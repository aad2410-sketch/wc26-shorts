"""Orchestrator.

  python -m src.main render --run-type recap|preview [--dry-run]
  python -m src.main publish [--dry-run]

`render` produces output/*.mp4 and queues manifest entries in state.json.
The workflow then commits+pushes output/ (Instagram must be able to cURL the
raw URL), after which `publish` uploads everything pending and prunes files.
"""
import argparse
import datetime as dt
import os
import shutil
import subprocess
import sys
from pathlib import Path

from src import config, state as st
from src.data import fixtures
from src.gen import captions, tts, visuals
from src.gen.script import Script, make_script, template_script
from src.render import video


def _summary(line: str) -> None:
    try:
        print(line)
    except UnicodeEncodeError:  # Windows cp1252 console can't print emoji
        print(line.encode("ascii", "replace").decode())
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as f:
            f.write(line + "\n\n")


def _caption_text(entry: dict) -> str:
    return f"{entry['title']}\n\n{entry['description']}\n\n{' '.join(entry['hashtags'])}"


# ------------------------------------------------------------------ render

def _produce(script: Script, voice: str, slug: str, dry_run: bool) -> dict | None:
    work = config.WORK_DIR / slug
    work.mkdir(parents=True, exist_ok=True)
    today = dt.date.today().isoformat()

    vo_path = str(work / "vo.mp3")
    tts.speak(f"{script.hook}. {script.body} {script.cta}", voice, vo_path)
    vo_dur = tts.audio_duration(vo_path)

    ass_path = str(work / "caps.ass")
    total = captions.build_ass(script, vo_dur, ass_path)

    broll = visuals.fetch_broll(script.broll_keywords, total, str(work))

    cards = []
    if script.pillar in ("recap", "stats", "preview"):
        card = str(work / "card.png")
        visuals.stat_card(["WORLD CUP 2026", script.hook.upper()[:24]], card)
        cards = [card]

    music = sorted(config.MUSIC_DIR.glob("*.mp3"))
    music_path = str(music[hash(slug) % len(music)]) if music else None

    out_name = f"{today}-{slug}.mp4"
    out_path = str(config.OUTPUT_DIR / out_name)
    video.render_short(broll, cards, vo_path, ass_path, total, out_path,
                       music_mp3=music_path)
    info = video.probe(out_path)
    _summary(f"🎬 rendered `{out_name}` ({info['duration']:.1f}s, "
             f"{Path(out_path).stat().st_size // 1024} KB)")
    shutil.rmtree(work, ignore_errors=True)

    return {
        "file": out_name,
        "title": script.title,
        "description": script.description + "\n" + " ".join(script.hashtags),
        "hashtags": script.hashtags,
        "pillar": script.pillar,
        "date": today,
    }


def _normalize_inbox(src_file: Path, dry_run: bool) -> dict:
    """Manual ingest lane: normalize a user-dropped clip to 9:16 and queue it."""
    today = dt.date.today().isoformat()
    out_name = f"{today}-inbox-{src_file.stem[:24]}.mp4"
    out_path = str(config.OUTPUT_DIR / out_name)
    config.OUTPUT_DIR.mkdir(exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", str(src_file),
         "-vf",
         f"scale={config.WIDTH}:{config.HEIGHT}:force_original_aspect_ratio=decrease,"
         f"pad={config.WIDTH}:{config.HEIGHT}:(ow-iw)/2:(oh-ih)/2:color=0x101418,"
         f"setsar=1,fps={config.FPS}",
         "-t", "59",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
         "-movflags", "+faststart", out_path],
        check=True,
    )
    title = src_file.stem.replace("_", " ").replace("-", " ").title()
    done = config.INBOX_DIR / "done"
    done.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src_file), str(done / src_file.name))
    _summary(f"📥 inbox clip normalized -> `{out_name}`")
    return {
        "file": out_name,
        "title": f"{title} | World Cup 2026",
        "description": "FIFA World Cup 2026.\n#WorldCup2026 #FIFAWorldCup",
        "hashtags": ["#WorldCup2026", "#FIFAWorldCup"],
        "pillar": "inbox",
        "date": today,
    }


def cmd_render(run_type: str, dry_run: bool) -> None:
    state = st.load()
    config.OUTPUT_DIR.mkdir(exist_ok=True)

    inbox_clips = sorted(config.INBOX_DIR.glob("*.mp4")) if config.INBOX_DIR.exists() else []
    if inbox_clips:
        state["pending"].append(_normalize_inbox(inbox_clips[0], dry_run))

    day = dt.date.today() - dt.timedelta(days=1) if run_type == "recap" else dt.date.today()
    matches = fixtures.get_matches(day)
    relevant = [m for m in matches
                if (run_type == "recap" and m["status"] == "FINISHED")
                or (run_type == "preview" and m["status"] != "FINISHED")]
    _summary(f"📅 {run_type} run for {day}: {len(relevant)} relevant matches")

    pillars = st.pillars_for_run(state, run_type, has_matches=bool(relevant))
    for pillar in pillars:
        voice = st.next_voice(state)
        script = (template_script(pillar, relevant) if dry_run
                  else make_script(pillar, relevant))
        slug = f"{run_type}-{pillar}"
        try:
            entry = _produce(script, voice, slug, dry_run)
            if entry:
                state["pending"].append(entry)
        except Exception as exc:
            _summary(f"❌ {pillar} failed to render: {exc}")

    st.save(state)


# ----------------------------------------------------------------- publish

def cmd_publish(dry_run: bool) -> None:
    from src.publish import instagram, youtube

    state = st.load()
    if not state["pending"]:
        _summary("nothing pending to publish")
        return

    still_pending = []
    for entry in state["pending"]:
        path = config.OUTPUT_DIR / entry["file"]
        if not path.exists():
            _summary(f"⚠️ `{entry['file']}` missing on disk - dropping")
            continue
        if dry_run:
            _summary(f"DRY RUN: would publish `{entry['file']}`")
            still_pending.append(entry)
            continue

        yt = youtube.upload(str(path), entry["title"], entry["description"],
                            entry["hashtags"])
        raw_url = config.raw_base_url() + "output/" + entry["file"]
        ig = instagram.publish_reel(raw_url, _caption_text(entry))

        _summary(f"{'✅' if yt['ok'] else '❌'} YouTube `{entry['file']}`: "
                 f"{yt.get('id') or yt.get('error')}")
        _summary(f"{'✅' if ig['ok'] else '❌'} Instagram `{entry['file']}`: "
                 f"{ig.get('id') or ig.get('error')}")

        state["posted"].append({**entry, "yt": yt, "ig": ig})
        if yt["ok"] or ig["ok"]:
            path.unlink(missing_ok=True)  # prune published video from the repo
        else:
            still_pending.append(entry)

    state["pending"] = still_pending
    if not state.get("yt_audit_passed") and not dry_run:
        _summary("🔔 **Reminder:** until the YouTube API audit passes, uploads land "
                 "as *private* - open YT Studio and tap-publish today's Shorts. "
                 "Set `yt_audit_passed: true` in state.json once approved.")
    st.save(state)


def main(argv=None):
    parser = argparse.ArgumentParser(prog="wc26-shorts")
    sub = parser.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("render")
    r.add_argument("--run-type", choices=["recap", "preview"], required=True)
    r.add_argument("--dry-run", action="store_true")
    p = sub.add_parser("publish")
    p.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    if args.cmd == "render":
        cmd_render(args.run_type, args.dry_run)
    else:
        cmd_publish(args.dry_run)


if __name__ == "__main__":
    sys.exit(main())

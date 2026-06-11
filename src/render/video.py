"""ffmpeg assembly: b-roll / stat-card segments + burned ASS captions + audio mix.

Single ffmpeg invocation per short. All inputs are normalized to
1080x1920@30 inside the filtergraph, so source clips can be any size.
"""
import subprocess
from pathlib import Path

from src import config


def _ffpath(p: str) -> str:
    """Escape a path for use inside an ffmpeg filtergraph (Windows-safe)."""
    return str(p).replace("\\", "/").replace(":", "\\:").replace("'", "\\'")


def render_short(
    broll_paths: list[str],
    stat_cards: list[str],
    vo_mp3: str,
    ass_path: str,
    total_seconds: float,
    out_mp4: str,
    music_mp3: str | None = None,
) -> str:
    """Compose the final vertical short. Returns out_mp4.

    Segment plan: stat cards (if any) are interleaved after every 2nd b-roll
    segment. Sources cycle until total_seconds is covered.
    """
    seg = config.SEGMENT_SECONDS
    n_segments = max(2, int(total_seconds / seg) + 1)

    # Build the segment source list: cycle b-roll, sprinkle stat cards
    sources: list[tuple[str, str]] = []  # (kind, path) kind in {video,image,color}
    bi = 0
    for i in range(n_segments):
        if stat_cards and i % 3 == 2:
            sources.append(("image", stat_cards[(i // 3) % len(stat_cards)]))
        elif broll_paths:
            sources.append(("video", broll_paths[bi % len(broll_paths)]))
            bi += 1
        else:
            sources.append(("color", ""))

    cmd = ["ffmpeg", "-y", "-v", "error"]
    filters = []
    for idx, (kind, path) in enumerate(sources):
        if kind == "video":
            cmd += ["-i", path]
        elif kind == "image":
            cmd += ["-loop", "1", "-t", str(seg), "-i", path]
        else:  # synthetic background (also the no-network test path)
            shade = ["0x101418", "0x18222e", "0x0e1a14"][idx % 3]
            cmd += ["-f", "lavfi", "-t", str(seg),
                    "-i", f"color=c={shade}:s={config.WIDTH}x{config.HEIGHT}:r={config.FPS}"]
        filters.append(
            f"[{idx}:v]trim=duration={seg},setpts=PTS-STARTPTS,"
            f"scale={config.WIDTH}:{config.HEIGHT}:force_original_aspect_ratio=increase,"
            f"crop={config.WIDTH}:{config.HEIGHT},setsar=1,fps={config.FPS},"
            f"format=yuv420p[v{idx}]"
        )

    vo_idx = len(sources)
    cmd += ["-i", vo_mp3]
    music_idx = None
    if music_mp3:
        music_idx = vo_idx + 1
        cmd += ["-stream_loop", "-1", "-i", music_mp3]

    concat_in = "".join(f"[v{i}]" for i in range(len(sources)))
    filters.append(f"{concat_in}concat=n={len(sources)}:v=1:a=0[vcat]")
    filters.append(
        f"[vcat]trim=duration={total_seconds:.2f},setpts=PTS-STARTPTS,"
        f"subtitles='{_ffpath(ass_path)}':fontsdir='{_ffpath(config.FONTS_DIR)}'[vout]"
    )

    # Audio: VO delayed by the hook duration, optional music bed underneath
    from src.gen.captions import HOOK_SECONDS
    delay_ms = int(HOOK_SECONDS * 1000)
    filters.append(f"[{vo_idx}:a]adelay={delay_ms}|{delay_ms},apad[vo]")
    if music_idx is not None:
        filters.append(f"[{music_idx}:a]volume=0.12[mus]")
        filters.append("[vo][mus]amix=inputs=2:duration=first:dropout_transition=0[aout]")
    else:
        filters.append("[vo]anull[aout]")

    cmd += [
        "-filter_complex", ";".join(filters),
        "-map", "[vout]", "-map", "[aout]",
        "-t", f"{total_seconds:.2f}",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
        "-pix_fmt", "yuv420p", "-r", str(config.FPS),
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        out_mp4,
    ]
    Path(out_mp4).parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    return out_mp4


def probe(path: str) -> dict:
    """Width/height/duration of a media file."""
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height", "-show_entries", "format=duration",
         "-of", "csv=p=0", path],
        capture_output=True, text=True, check=True,
    )
    lines = [l for l in out.stdout.strip().splitlines() if l]
    w, h = lines[0].split(",")[:2]
    dur = float(lines[-1].split(",")[-1])
    return {"width": int(w), "height": int(h), "duration": dur}

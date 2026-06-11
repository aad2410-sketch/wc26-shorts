"""Offline golden-path test: template script + tone VO + synthetic backgrounds
+ a real stat card -> a real 1080x1920 short. Proves the whole render path
without any network or API key.
"""
import subprocess

from src.gen import captions, visuals
from src.gen.script import template_script
from src.render import video


def test_render_golden_short(tmp_path):
    script = template_script("trivia", [])

    vo = tmp_path / "vo.mp3"
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
         "-i", "sine=frequency=300:duration=8", str(vo)],
        check=True,
    )

    ass = tmp_path / "caps.ass"
    total = captions.build_ass(script, vo_duration=8.0, out_ass=str(ass))

    card = tmp_path / "card.png"
    visuals.stat_card(["WORLD CUP 2026", "104 MATCHES", "48 TEAMS"], str(card))

    out = tmp_path / "short.mp4"
    video.render_short(
        broll_paths=[], stat_cards=[str(card)], vo_mp3=str(vo),
        ass_path=str(ass), total_seconds=total, out_mp4=str(out),
    )

    info = video.probe(str(out))
    assert info["width"] == 1080 and info["height"] == 1920
    assert abs(info["duration"] - total) < 1.0

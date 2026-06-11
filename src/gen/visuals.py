"""Visual assets: Pexels portrait b-roll + Pillow stat cards.

No FIFA marks anywhere: team names are plain text, graphics are original.
"""
import os

import requests
from PIL import Image, ImageDraw, ImageFont

from src import config

PEXELS_URL = "https://api.pexels.com/videos/search"


def fetch_broll(keywords: list[str], need_seconds: float, dest_dir: str) -> list[str]:
    """Download portrait stock clips until total duration covers need_seconds.
    Returns [] on any failure (caller falls back to synthetic backgrounds)."""
    key = config.secret("PEXELS_API_KEY")
    if not key:
        print("[broll] no PEXELS_API_KEY - skipping stock footage")
        return []
    paths: list[str] = []
    total = 0.0
    try:
        for kw in keywords:
            resp = requests.get(
                PEXELS_URL,
                headers={"Authorization": key},
                params={"query": kw, "orientation": "portrait",
                        "size": "medium", "per_page": 3},
                timeout=30,
            )
            resp.raise_for_status()
            for video in resp.json().get("videos", []):
                files = [f for f in video.get("video_files", [])
                         if f.get("width") and f["width"] <= 1440]
                if not files:
                    continue
                best = max(files, key=lambda f: f["width"])
                out = os.path.join(dest_dir, f"broll_{len(paths)}.mp4")
                with requests.get(best["link"], stream=True, timeout=120) as dl:
                    dl.raise_for_status()
                    with open(out, "wb") as fh:
                        for chunk in dl.iter_content(1 << 20):
                            fh.write(chunk)
                paths.append(out)
                total += float(video.get("duration", 5))
                if total >= need_seconds + 5:
                    return paths
    except Exception as exc:
        print(f"[broll] pexels failed ({exc}); using what we have")
    return paths


def _font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(
        str(config.FONTS_DIR / "ArchivoBlack-Regular.ttf"), size
    )


def stat_card(lines: list[str], out_png: str) -> str:
    """1080x1920 dark gradient card with bold centered rows."""
    img = Image.new("RGB", (config.WIDTH, config.HEIGHT))
    px = img.load()
    for y in range(config.HEIGHT):
        t = y / config.HEIGHT
        px_row = (int(12 + 18 * t), int(16 + 10 * t), int(28 + 30 * t))
        for x in range(0, config.WIDTH, 4):
            for dx in range(4):
                if x + dx < config.WIDTH:
                    px[x + dx, y] = px_row
    draw = ImageDraw.Draw(img)
    # accent bar
    draw.rectangle([(60, 430), (1020, 446)], fill=(255, 229, 0))
    sizes = [88] + [72] * (len(lines) - 1) if lines else []
    y = 560
    for line, size in zip(lines, sizes):
        font = _font(size)
        w = draw.textlength(line, font=font)
        draw.text(((config.WIDTH - w) / 2, y), line, font=font,
                  fill=(255, 255, 255), stroke_width=3, stroke_fill=(0, 0, 0))
        y += size + 60
    img.save(out_png)
    return out_png

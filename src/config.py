"""Central configuration: env secrets, constants, paths."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# --- video format ---
WIDTH = 1080
HEIGHT = 1920
FPS = 30
TARGET_SECONDS = (20, 30)
SEGMENT_SECONDS = 3.0  # b-roll cut length

# --- voices (rotated per video) ---
VOICES = [
    "en-US-ChristopherNeural",
    "en-GB-RyanNeural",
    "en-US-GuyNeural",
]

# --- pillars ---
RECAP_RUN_PILLARS = ["recap", "stats"]          # morning run, match days
PREVIEW_RUN_PILLARS = ["preview"]                # evening run, match days
REST_DAY_PILLARS = ["trivia", "hot_take"]        # no matches -> alternate these

# --- paths ---
OUTPUT_DIR = ROOT / "output"
INBOX_DIR = ROOT / "inbox"
WORK_DIR = ROOT / "work"
FONTS_DIR = ROOT / "assets" / "fonts"
MUSIC_DIR = ROOT / "assets" / "music"
STATE_FILE = ROOT / "state.json"

GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")


def secret(name: str) -> str | None:
    """Optional secret -- returns None when unset (pipeline degrades gracefully)."""
    return os.environ.get(name) or None


def require(name: str) -> str:
    val = os.environ.get(name)
    if not val:
        raise RuntimeError(
            f"Missing required env var {name} - see SETUP.md for how to create it"
        )
    return val


def raw_base_url() -> str:
    """Public raw URL base for this repo (Instagram cURLs videos from here)."""
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    branch = os.environ.get("GITHUB_REF_NAME", "main")
    return f"https://raw.githubusercontent.com/{repo}/{branch}/"

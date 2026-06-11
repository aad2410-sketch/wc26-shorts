"""Offline end-to-end: render run with no network/keys -> mp4s + pending state."""
import datetime as dt
import json

import pytest

from src import config, main, state as st
from src.data import fixtures
from src.gen import tts


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "STATE_FILE", tmp_path / "state.json")
    monkeypatch.setattr(config, "OUTPUT_DIR", tmp_path / "output")
    monkeypatch.setattr(config, "WORK_DIR", tmp_path / "work")
    monkeypatch.setattr(config, "INBOX_DIR", tmp_path / "inbox")
    monkeypatch.setattr(config, "MUSIC_DIR", tmp_path / "no_music")
    monkeypatch.delenv("PEXELS_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    # offline TTS: synth a tone instead of calling edge-tts
    def fake_speak(text, voice, out_mp3):
        import subprocess
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
             "-i", "sine=frequency=300:duration=6", out_mp3],
            check=True,
        )
        return out_mp3
    monkeypatch.setattr(tts, "speak", fake_speak)

    # canned match data
    from pathlib import Path
    canned = json.loads(
        (Path(__file__).parent / "fixtures_canned" / "football_data_sample.json")
        .read_text()
    )
    monkeypatch.setattr(fixtures, "get_matches",
                        lambda day: fixtures.normalize_fd(canned))
    return tmp_path


def test_render_recap_run_offline(isolated):
    main.main(["render", "--run-type", "recap", "--dry-run"])
    state = st.load()
    assert len(state["pending"]) == 2  # recap + stats
    for entry in state["pending"]:
        assert (config.OUTPUT_DIR / entry["file"]).exists()
        assert entry["title"]
        assert "#WorldCup2026" in entry["hashtags"]


def test_publish_dry_run_keeps_pending(isolated):
    main.main(["render", "--run-type", "preview", "--dry-run"])
    before = len(st.load()["pending"])
    assert before >= 1
    main.main(["publish", "--dry-run"])
    assert len(st.load()["pending"]) == before  # nothing consumed in dry run

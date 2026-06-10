import socket
import subprocess

import pytest

from src.gen import tts


def _online() -> bool:
    try:
        socket.create_connection(("speech.platform.bing.com", 443), timeout=5).close()
        return True
    except OSError:
        return False


def test_audio_duration_on_generated_tone(tmp_path):
    tone = tmp_path / "tone.mp3"
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
         "-i", "sine=frequency=440:duration=2", str(tone)],
        check=True,
    )
    assert abs(tts.audio_duration(str(tone)) - 2.0) < 0.2


@pytest.mark.skipif(not _online(), reason="needs network")
def test_speak_renders_real_audio(tmp_path):
    out = tmp_path / "vo.mp3"
    tts.speak("The World Cup starts tomorrow.", "en-US-ChristopherNeural", str(out))
    assert out.exists()
    assert 1.0 < tts.audio_duration(str(out)) < 6.0

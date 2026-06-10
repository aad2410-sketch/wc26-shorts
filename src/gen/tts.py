"""Voiceover synthesis. Primary: edge-tts (free Microsoft neural voices).
Fallback: gTTS (Google Translate voices) so a TTS outage never kills a run.
"""
import asyncio
import subprocess

from src import config


def _edge_tts(text: str, voice: str, out_mp3: str) -> None:
    import edge_tts

    async def run():
        await edge_tts.Communicate(text, voice, rate="+8%").save(out_mp3)

    asyncio.run(run())


def _gtts(text: str, out_mp3: str) -> None:
    from gtts import gTTS

    gTTS(text=text, lang="en", tld="co.uk").save(out_mp3)


def speak(text: str, voice: str, out_mp3: str) -> str:
    """Render text to mp3. Tries edge-tts twice, then gTTS. Raises only if all fail."""
    last_exc = None
    for attempt in range(2):
        try:
            _edge_tts(text, voice, out_mp3)
            return out_mp3
        except Exception as exc:
            last_exc = exc
            print(f"[tts] edge-tts attempt {attempt + 1} failed: {exc}")
    try:
        print("[tts] falling back to gTTS")
        _gtts(text, out_mp3)
        return out_mp3
    except Exception as exc:
        raise RuntimeError(f"all TTS engines failed: edge={last_exc} gtts={exc}")


def audio_duration(path: str) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", path],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip())

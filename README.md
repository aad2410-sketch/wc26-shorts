# wc26-shorts

Fully automated, fully free pipeline that posts 2–3 original FIFA World Cup
2026 YouTube Shorts + Instagram Reels every day, generated from live
tournament data. Runs on GitHub Actions — no server, no cost.

**[Privacy Policy](PRIVACY.md)** · **[Terms of Service](TERMS.md)** — this
project uses **YouTube API Services** ([YouTube ToS](https://www.youtube.com/t/terms),
[Google Privacy Policy](http://www.google.com/policies/privacy)) and the
Instagram Graph API to publish to the operator's own accounts.

```
 GitHub Actions cron (2x daily)
        │
        ▼
 football-data.org ──► Gemini Flash ──► edge-tts ──► ffmpeg + libass
 (fixtures/results)    (25s script)     (voiceover)   (1080x1920 short:
        │                                              b-roll + stat cards
 openfootball (fallback)                               + karaoke captions)
                                                            │
                              git push (raw URL) ◄──────────┤
                                     │                      ▼
                                     ▼               YouTube Data API
                            Instagram Graph API      (Shorts upload)
                            (Reels publish)
```

**Content pillars** (rotating): match recaps · stats & records · previews ·
trivia · hot takes. All content is original — AI-written scripts over stock
footage and generated graphics. **No broadcast footage, no FIFA marks.**

## Quick start

See **[SETUP.md](SETUP.md)** — one-time ~45 min of account/API setup, then
it runs itself for the whole tournament (June 11 – July 19, 2026).

## Layout

| Path | What |
|---|---|
| `src/main.py` | Orchestrator: `render` and `publish` phases |
| `src/data/fixtures.py` | WC2026 data (football-data.org + openfootball fallback) |
| `src/gen/script.py` | Gemini Flash scripts + deterministic template fallback |
| `src/gen/tts.py` | edge-tts voiceover (gTTS fallback) |
| `src/gen/captions.py` | ASS karaoke captions (hook / word groups / CTA) |
| `src/gen/visuals.py` | Pexels b-roll + Pillow stat cards |
| `src/render/video.py` | ffmpeg assembly |
| `src/publish/` | YouTube + Instagram uploaders |
| `inbox/` | Manual ingest lane — drop an .mp4, it gets posted |
| `state.json` | Rotation pointers + posted ledger (also the Actions keepalive) |

## Development

```powershell
python -m venv .venv && .venv\Scripts\pip install -r requirements.txt -r requirements-dev.txt
.venv\Scripts\python -m pytest          # 19 tests, all offline except one live TTS check
.venv\Scripts\python -m src.main render --run-type recap --dry-run   # render locally
```

## Disclaimers

- 100% original content by design. The `inbox/` lane posts whatever *you*
  put in it — you are responsible for owning the rights to anything you drop
  there. Broadcast match footage will get the accounts struck; don't.
- Until the YouTube API compliance audit passes (SETUP.md §4.6), API uploads
  land as **private** and need a manual tap-publish in YT Studio.
- Not affiliated with FIFA. "FIFA", "FIFA World Cup 26" and related marks
  are trademarks of FIFA; this project deliberately avoids using them in
  generated graphics.

# wc26-shorts — Design Spec

**Date:** 2026-06-10 · **Status:** Approved by user · **Budget:** $0/month
**Goal:** Fully automated pipeline that generates and posts 2–3 original FIFA World Cup 2026 Shorts/Reels daily to YouTube and Instagram, June 11 – July 19, 2026, optimized for short-form virality.

Research basis: `C:\Users\2025\Documents\WC2026_Shorts_Automation_Research_20260610\WC2026_Shorts_Automation_Research.md`

## 1. Constraints & decisions (locked)

| Decision | Choice | Why |
|---|---|---|
| Content | Original AI-generated only (4 pillars) + manual ingest lane | FIFA Content ID kills footage-repost automation; original = zero strike risk |
| Cost | $0/month | User requirement |
| Runtime | GitHub Actions cron, public repo | Free unlimited minutes; secrets vault; cron drift acceptable |
| Language | Python 3.12+ single language | One toolchain; ffmpeg+Pillow render (no MoviePy/Remotion dependency weight) |
| LLM | Gemini Flash free tier (fallback: deterministic templates) | 1,500 req/day free vs ~10 needed |
| TTS | edge-tts (fallback: Kokoro-82M) behind one interface | Free neural voices; abstraction hedges unofficial-API risk |
| Data | football-data.org free tier (primary) + openfootball worldcup.json (fallback) | WC2026 in free tier; public-domain backup |
| Visuals | Pexels API b-roll + Pillow-generated graphics | Free, monetization-safe, no attribution |
| Publish | YouTube Data API v3 + Instagram Graph API (dev mode, own account) | Native, free, within quotas (100/day YT, 100/day IG vs 3 needed) |
| IG video hosting | GitHub raw URL from the public repo (fallback: resumable upload) | Meta cURLs a public URL; repo is already public |

## 2. Daily schedule (2 Actions runs)

| Run | Cron (UTC) | IST target | Output |
|---|---|---|---|
| recap | `30 1 * * *` (~07:00 IST + drift) | morning | 1 recap short (yesterday's results) + 1 stats/records short |
| preview | `30 12 * * *` (~18:00 IST + drift) | evening | 1 preview short (today's fixtures) OR trivia/hot-take (rotation; trivia/hot-take on rest days) |

Cron is set ~30 min before target window; GitHub drift of 10–30 min lands inside the window. Posting minute-precision is irrelevant to the algorithm; consistency + post-match freshness matter.

## 3. Architecture

```
.github/workflows/post.yml      # cron + manual dispatch; matrix: run_type = recap|preview
src/
  main.py                       # orchestrator: plan → generate → render → publish → log
  config.py                     # pillars, voices, schedule, branding, env/secrets loading
  data/fixtures.py              # football-data.org client + openfootball fallback + normalization
  gen/script.py                 # Gemini Flash prompts per pillar; hook-first JSON output
  gen/tts.py                    # speak(text) -> mp3; edge-tts primary, kokoro fallback
  gen/visuals.py                # Pexels search/download; Pillow caption frames + stat cards
  render/video.py               # ffmpeg composite: b-roll + captions + VO + music -> 1080x1920 mp4
  publish/youtube.py            # OAuth refresh-token upload via videos.insert
  publish/instagram.py          # container (video_url=raw repo URL) + publish; status polling
  state.py                      # state.json read/write; dedupe; pillar rotation; posted log
inbox/                          # manual ingest lane: drop .mp4 -> trimmed/captioned/posted next run
assets/music/                   # 3-5 CC0 tracks committed to repo
assets/fonts/                   # bold condensed font (OFL-licensed)
output/                         # rendered videos (committed so IG can cURL raw URL; pruned after publish confirm)
state.json                      # rotation pointers, posted-video ledger, audit-mode flag
scripts/get_youtube_token.py    # one-time local OAuth flow -> refresh token
scripts/get_ig_token.py         # one-time long-lived IG token helper + 60-day refresh in CI
SETUP.md                        # click-by-click account/keys/secrets guide
```

## 4. Content pillars & rotation

1. **Recap** — "Everything that happened today at the World Cup" — scores, standout performer, table movement. Morning slot, match days.
2. **Stats/records** — "Top scorers after Matchday N", "Fastest WC goals ever" (historical bank for rest days). Morning slot.
3. **Preview** — "Today's 3 matches — and the one you can't miss". Evening slot, match days.
4. **Trivia/hot-take** — quiz hooks ("Name the only player who…"), bold claims. Evening slot on rest days; injected mid-rotation for variety.

Script contract (Gemini JSON output): `hook` (≤8 words, on-screen in first second), `body` (60–80 words, punchy), `cta` (comment-bait question), `title`, `description`, `hashtags` (2–4), `broll_keywords` (3). Template fallback if Gemini fails/quota-blocked.

## 5. Video format (virality spec)

- 1080×1920, 20–30 s, H.264 + AAC, ≤8 MB target (fast IG cURL).
- Hook text burned in at 0.0 s, full-screen, 2 word-pop animations in first second.
- Word-by-word animated captions (Pillow frames, yellow/white on dark scrim), ~95% viewing is muted.
- Pexels football b-roll cut every 2–3 s; subtle zoom (ffmpeg zoompan) for motion.
- Stat cards/scoreboards as Pillow-rendered overlays (team names as text — no FIFA logos/emblems/trademarks).
- Energetic en-US/en-GB neural voice, 2–3 rotating; music bed at −18 dB under VO.
- End-frame CTA: question + "Follow for daily WC26" (1.5 s).

## 6. Error handling

| Failure | Behavior |
|---|---|
| football-data.org down/limited | openfootball raw JSON; if both fail → historical/trivia pillar (needs no live data) |
| Gemini fail/quota | Deterministic template scripts from fixture data |
| edge-tts 403/break | Retry ×2 → Kokoro local render |
| Pexels miss | Repo-bundled evergreen b-roll pack |
| YouTube upload fail | Log, continue with IG; surface in Actions summary |
| IG container error/timeout | Poll status 10×30 s; on fail log + continue |
| Audit pending (YT private-lock) | Expected mode: upload anyway (lands private), Actions summary reminds user to tap-publish; `state.json` flag flips when audit passes |
| Repo inactivity 60-day disable | Daily state.json commit doubles as keepalive |

## 7. Security

- All credentials in GitHub Actions secrets (never in code): `FOOTBALL_DATA_KEY`, `GEMINI_API_KEY`, `PEXELS_API_KEY`, `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN`, `IG_USER_ID`, `IG_ACCESS_TOKEN`.
- Public repo: code public, secrets masked by Actions; rendered videos public briefly (required for IG cURL) — acceptable, they're being published anyway.
- IG long-lived token expires 60 days: workflow step auto-refreshes and updates the secret via `gh secret set` (needs `GH_PAT` repo secret) — covers the 39-day tournament with margin.

## 8. Testing

- **Local first (this machine has Python 3.14 + ffmpeg 8.1):** unit-test data normalization; golden-path integration test rendering one full short from canned fixture JSON + template script (no keys needed) → human eyeballs output/test.mp4.
- **Keyed local test:** once user provides keys → live data + Gemini + real TTS render.
- **Dry-run mode:** `--no-publish` flag renders everything, skips upload.
- **CI smoke:** `workflow_dispatch` manual trigger with `dry_run=true` input proves the Actions environment end-to-end before first real post.

## 9. Out of scope (v1)

TikTok (separate API regime), analytics-driven topic selection, A/B testing automation, thumbnail AI-gen, multi-language, comment auto-replies. All are post-tournament upgrades; v1 ships before Matchday 1 ends.

## 10. User's manual one-time steps (detailed in SETUP.md)

1. YouTube channel; Google Cloud project; enable YouTube Data API; OAuth consent (external/testing) + Desktop client; run `scripts/get_youtube_token.py`; **submit API compliance audit form day 1**.
2. Instagram → Professional (Creator); link a Facebook Page; Meta developer app; add own IG account (admin role); generate long-lived token via `scripts/get_ig_token.py`.
3. Free keys: football-data.org, Google AI Studio (Gemini), Pexels.
4. Create public GitHub repo, push, add 9 secrets, enable Actions.

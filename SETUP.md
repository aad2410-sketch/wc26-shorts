# Setup Guide — one-time, ~45 minutes

Everything below is free. Do the steps in order; each section ends with the
GitHub secret(s) it produces. **Do step 4's audit form today** — it's the only
step with a waiting period.

## 0. Prerequisites

- A Google account (for YouTube + Gemini)
- A Facebook account (for Instagram's API — IG publishing runs through Meta)
- [Python 3.12+](https://www.python.org/downloads/) and [git](https://git-scm.com/) installed locally (already true on this machine)
- A [GitHub](https://github.com/) account

## 1. GitHub repository

1. Create a **public** repo named `wc26-shorts` at <https://github.com/new>
   (public = free unlimited Actions minutes + the raw URLs Instagram needs).
2. Push this project:
   ```powershell
   cd C:\workauto\wc26-shorts
   git remote add origin https://github.com/<YOUR_USERNAME>/wc26-shorts.git
   git branch -M main
   git push -u origin main
   ```
3. On the repo page: **Settings → Actions → General → Workflow permissions**
   → select **Read and write permissions** → Save.

## 2. Free data/AI keys (10 min)

| Key | Where | Steps |
|---|---|---|
| `FOOTBALL_DATA_KEY` | <https://www.football-data.org/client/register> | Register → key arrives by email. Free tier includes the World Cup. |
| `GEMINI_API_KEY` | <https://aistudio.google.com/apikey> | Sign in → **Create API key**. No card needed. |
| `PEXELS_API_KEY` | <https://www.pexels.com/api/> | Sign up → **Your API key**. |

## 3. YouTube channel (5 min)

1. <https://youtube.com> → profile picture → **Create a channel**.
   Pick the channel name (this is your brand — e.g. "WC26 Daily").
2. YouTube Studio → Settings → Channel → verify your phone number
   (required for >15 min uploads and custom thumbnails; do it now anyway).

## 4. YouTube API access (15 min) — DO THE AUDIT FORM TODAY

1. <https://console.cloud.google.com/projectcreate> → name `wc26-shorts` → Create.
2. **APIs & Services → Library** → search **YouTube Data API v3** → **Enable**.
3. **APIs & Services → OAuth consent screen**:
   - User type: **External** → Create
   - App name `wc26-shorts`, your email twice → Save through the steps
   - **Audience → Test users → Add** your own Gmail → Save
   (App stays in "Testing" — fine: refresh tokens for test users on
   YouTube-scoped apps do not expire as long as the app is used regularly.)
4. **APIs & Services → Credentials → Create credentials → OAuth client ID**:
   - Application type: **Desktop app** → Create
   - Copy the **Client ID** and **Client secret**
5. Locally:
   ```powershell
   cd C:\workauto\wc26-shorts
   .venv\Scripts\python scripts\get_youtube_token.py <CLIENT_ID> <CLIENT_SECRET>
   ```
   A browser opens → sign in with the channel's account → allow.
   The script prints your three `YT_*` secret values.
6. **Compliance audit (lifts the private-lock):** fill the
   [YouTube API audit form](https://support.google.com/youtube/contact/yt_api_form).
   Honest answers that work for this use case: personal project, uploads
   original AI-generated sports-data videos to *your own* channel only, no
   third-party data access, ~3 uploads/day. Until approved, every upload lands
   **private** — open the YT Studio app daily and tap each Short → **Public**
   (10 seconds). When the approval email arrives, edit `state.json` →
   `"yt_audit_passed": true` and the daily reminder stops.

## 5. Instagram + Meta app (15 min)

1. **Make IG professional:** Instagram app → Settings → Account type →
   **Switch to professional account** → **Creator** → category Sports.
2. **Facebook Page** (required bridge): <https://facebook.com/pages/create> →
   name it like your channel → Create.
3. **Link them:** Instagram → Settings → Business tools → **Connect a
   Facebook Page** → pick the page from step 2.
4. **Meta developer app:** <https://developers.facebook.com> → My Apps →
   **Create app** → use case **Other** → type **Business** → name `wc26-shorts`.
5. **Get a token:** <https://developers.facebook.com/tools/explorer>:
   - App: `wc26-shorts`
   - **Add permissions:** `instagram_basic`, `instagram_content_publish`,
     `pages_show_list`, `pages_read_engagement`, `business_management`
   - **Generate Access Token** → log in → in the popup, select your Page AND
     your Instagram account → allow everything.
   - Copy the token shown in the Explorer.
6. Locally (App ID + secret are at App → Settings → Basic):
   ```powershell
   .venv\Scripts\python scripts\get_ig_token.py <APP_ID> <APP_SECRET> <TOKEN_FROM_EXPLORER>
   ```
   Prints `IG_ACCESS_TOKEN` (60-day) and `IG_USER_ID`.
   **Calendar reminder:** re-run this step ~Aug 5, 2026 if you keep posting
   after the tournament (token expiry).

## 6. Add the 8 GitHub secrets

Repo → **Settings → Secrets and variables → Actions → New repository secret**, or:

```powershell
gh secret set FOOTBALL_DATA_KEY  --body "<value>"
gh secret set GEMINI_API_KEY     --body "<value>"
gh secret set PEXELS_API_KEY     --body "<value>"
gh secret set YT_CLIENT_ID       --body "<value>"
gh secret set YT_CLIENT_SECRET   --body "<value>"
gh secret set YT_REFRESH_TOKEN   --body "<value>"
gh secret set IG_USER_ID         --body "<value>"
gh secret set IG_ACCESS_TOKEN    --body "<value>"
```

## 7. Verify end-to-end

1. Repo → **Actions** tab → enable workflows if prompted.
2. **Daily WC26 Shorts → Run workflow** → run_type `recap`, dry_run **true**
   → Run. Wait ~5 min → the job summary shows the rendered videos; they're
   committed to `output/` — download and watch one.
3. Run again with dry_run **false** → check YT Studio (video will be
   *private* until the audit passes — tap-publish it) and your IG profile
   (Reel should be live).

From now on it runs itself at ~07:00 and ~18:00 IST daily. Check the Actions
job summary whenever you like — every render/publish result is logged there.

## 8. Optional upgrades

- **Music beds:** drop 2–5 `.mp3` files into `assets/music/` and push. Get
  CC0 tracks from <https://pixabay.com/music/> (filter: sport/energetic).
  Without them, shorts are voice-only (still fine).
- **Better fallback voice (Kokoro):** if edge-tts ever breaks, the pipeline
  falls back to gTTS automatically. For a nicer fallback, see
  [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) — heavier install,
  not wired in by default.
- **First paid upgrade when ready:** ElevenLabs voiceover (~$5/mo) — the
  single biggest perceived-quality jump.
- **Manual ingest lane:** drop any `.mp4` into `inbox/` and push — the next
  run normalizes it to 9:16, captions the metadata, and posts it instead of
  one generated video. What you put there is your responsibility (don't feed
  it broadcast footage — see README disclaimer).

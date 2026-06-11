# Privacy Policy — WC26 Shorts Pipeline

_Last updated: June 11, 2026_

WC26 Shorts Pipeline ("the API Client") is a personal, open-source automation
tool operated by an individual developer. It generates original short-form
sports videos and uploads them to the operator's own YouTube channel and
Instagram account. The complete source code is public in this repository.

## Use of YouTube API Services

This API Client uses **YouTube API Services**. By using it, the operator
agrees to be bound by the
[YouTube Terms of Service](https://www.youtube.com/t/terms). Google's
handling of data is described in the
[Google Privacy Policy](http://www.google.com/policies/privacy).

## What data the API Client accesses, collects, and stores

- **It does not access, collect, store, or process any data belonging to
  third-party users.** It has no users other than its operator, no visitors,
  no accounts, and no public-facing service.
- It calls a single YouTube API endpoint, `videos.insert`, to upload
  self-created videos to the **operator's own YouTube channel** using the
  operator's own OAuth credentials (`youtube.upload` scope).
- It does not read, retrieve, or store any YouTube API data (no video data,
  channel data, comments, analytics, or personal information of any person).
- The operator's OAuth refresh token is stored as an encrypted GitHub Actions
  secret, accessible only to the operator. No other authorization data is
  stored.
- Upload results (video IDs of the operator's own uploads) are logged in a
  `state.json` file in this repository for bookkeeping.

## Cookies and tracking

The API Client serves no web pages and uses no cookies, advertising,
analytics, or tracking technologies of any kind.

## Data sharing

No data is shared with any third party. The only external services the
pipeline contacts are the APIs it publishes through (YouTube, Instagram) and
the public data/asset APIs it reads from (football-data.org, Pexels, Google
Gemini), none of which receive any personal data of any user.

## Revoking access

The operator (the sole authorized user) can revoke the API Client's access
to their Google account at any time via
[Google security settings](https://security.google.com/settings/security/permissions).

## Contact

Questions about this policy: open an issue in this repository or contact the
operator at aadarshlm10@gmail.com.

"""YouTube Shorts upload via the Data API v3 (refresh-token OAuth).

Until the project's API compliance audit passes, YouTube force-locks API
uploads to private - expected mode; the Actions summary reminds the user
to tap-publish in YT Studio. See SETUP.md.
"""
from src import config


def upload(video_path: str, title: str, description: str, tags: list[str]) -> dict:
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload

        creds = Credentials(
            None,
            refresh_token=config.require("YT_REFRESH_TOKEN"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=config.require("YT_CLIENT_ID"),
            client_secret=config.require("YT_CLIENT_SECRET"),
        )
        yt = build("youtube", "v3", credentials=creds, cache_discovery=False)

        short_title = title if len(title) <= 90 else title[:87] + "..."
        if "#shorts" not in short_title.lower():
            short_title += " #Shorts"

        request = yt.videos().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": short_title,
                    "description": description,
                    "tags": [t.lstrip("#") for t in tags] + ["shorts", "worldcup2026"],
                    "categoryId": "17",  # Sports
                },
                "status": {
                    "privacyStatus": "public",
                    "selfDeclaredMadeForKids": False,
                },
            },
            media_body=MediaFileUpload(video_path, chunksize=-1, resumable=True),
        )
        response = None
        while response is None:
            _, response = request.next_chunk()
        return {"ok": True, "id": response["id"]}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}

"""Instagram Reels publishing via the Graph API container flow.

Meta's servers download the video from a public URL (this repo's raw URL),
so `publish` must run AFTER the rendered file has been pushed.
"""
import time

import requests

from src import config

GRAPH = "https://graph.facebook.com/v23.0"
POLL_EVERY = 30
POLL_MAX = 10


def publish_reel(video_url: str, caption: str) -> dict:
    try:
        ig_id = config.require("IG_USER_ID")
        token = config.require("IG_ACCESS_TOKEN")

        create = requests.post(
            f"{GRAPH}/{ig_id}/media",
            data={
                "media_type": "REELS",
                "video_url": video_url,
                "caption": caption[:2200],
                "share_to_feed": "true",
                "access_token": token,
            },
            timeout=60,
        )
        create.raise_for_status()
        container = create.json()["id"]

        for _ in range(POLL_MAX):
            status = requests.get(
                f"{GRAPH}/{container}",
                params={"fields": "status_code", "access_token": token},
                timeout=30,
            ).json()
            code = status.get("status_code")
            if code == "FINISHED":
                break
            if code == "ERROR":
                return {"ok": False, "error": f"container processing error: {status}"}
            time.sleep(POLL_EVERY)
        else:
            return {"ok": False, "error": "container not ready after polling"}

        pub = requests.post(
            f"{GRAPH}/{ig_id}/media_publish",
            data={"creation_id": container, "access_token": token},
            timeout=60,
        )
        pub.raise_for_status()
        return {"ok": True, "id": pub.json()["id"]}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}

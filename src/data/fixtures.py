"""World Cup 2026 match data.

Primary: football-data.org v4 free tier (World Cup included, needs key).
Fallback: openfootball/worldcup.json (public domain, no key).
Both normalize to:
    {home, away, date_utc, status, score_home, score_away, group, stage}
status is one of: FINISHED, IN_PLAY, SCHEDULED.
"""
import datetime as dt

import requests

from src import config

FD_URL = "https://api.football-data.org/v4/competitions/WC/matches"
OF_URL = "https://raw.githubusercontent.com/openfootball/worldcup.json/master/2026/worldcup.json"

_FD_STATUS = {
    "FINISHED": "FINISHED",
    "IN_PLAY": "IN_PLAY",
    "PAUSED": "IN_PLAY",
    "LIVE": "IN_PLAY",
}


def normalize_fd(payload: dict) -> list[dict]:
    matches = []
    for m in payload.get("matches", []):
        full = m.get("score", {}).get("fullTime", {})
        matches.append({
            "home": m.get("homeTeam", {}).get("name") or "TBD",
            "away": m.get("awayTeam", {}).get("name") or "TBD",
            "date_utc": m.get("utcDate", ""),
            "status": _FD_STATUS.get(m.get("status"), "SCHEDULED"),
            "score_home": full.get("home"),
            "score_away": full.get("away"),
            "group": m.get("group"),
            "stage": m.get("stage", ""),
        })
    return matches


def normalize_of(payload: dict, day: dt.date) -> list[dict]:
    matches = []
    for rnd in payload.get("rounds", []):
        for m in rnd.get("matches", []):
            if m.get("date") != day.isoformat():
                continue
            finished = "score" in m and m["score"] is not None
            score = (m.get("score") or {}).get("ft") or [None, None]
            matches.append({
                "home": (m.get("team1") or {}).get("name") or m.get("team1") or "TBD",
                "away": (m.get("team2") or {}).get("name") or m.get("team2") or "TBD",
                "date_utc": f"{m.get('date')}T{m.get('time', '00:00')}:00Z",
                "status": "FINISHED" if finished else "SCHEDULED",
                "score_home": score[0],
                "score_away": score[1],
                "group": m.get("group"),
                "stage": rnd.get("name", ""),
            })
    return matches


def fetch_football_data(day: dt.date) -> list[dict]:
    key = config.require("FOOTBALL_DATA_KEY")
    resp = requests.get(
        FD_URL,
        headers={"X-Auth-Token": key},
        params={"dateFrom": day.isoformat(), "dateTo": day.isoformat()},
        timeout=30,
    )
    resp.raise_for_status()
    return normalize_fd(resp.json())


def fetch_openfootball(day: dt.date) -> list[dict]:
    resp = requests.get(OF_URL, timeout=30)
    resp.raise_for_status()
    return normalize_of(resp.json(), day)


def get_matches(day: dt.date) -> list[dict]:
    """Primary -> fallback -> []. Never raises."""
    try:
        return fetch_football_data(day)
    except Exception as exc:
        print(f"[data] football-data.org failed ({exc}); trying openfootball")
    try:
        return fetch_openfootball(day)
    except Exception as exc:
        print(f"[data] openfootball failed too ({exc}); no live data")
    return []

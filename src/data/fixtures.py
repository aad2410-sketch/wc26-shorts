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


def _of_team(value) -> str:
    """openfootball teams are plain strings (2026 flat schema) or {name: ...}."""
    if isinstance(value, dict):
        return value.get("name") or "TBD"
    return value or "TBD"


def _of_score(m: dict) -> tuple:
    """Support both score conventions: {score: {ft: [a, b]}} and score1/score2."""
    ft = (m.get("score") or {}).get("ft") if isinstance(m.get("score"), dict) else None
    if ft:
        return ft[0], ft[1]
    return m.get("score1"), m.get("score2")


def _of_normalize_match(m: dict, stage: str) -> dict:
    score_home, score_away = _of_score(m)
    time = (m.get("time") or "00:00")[:5]
    return {
        "home": _of_team(m.get("team1")),
        "away": _of_team(m.get("team2")),
        "date_utc": f"{m.get('date')}T{time}:00Z",
        "status": "FINISHED" if score_home is not None else "SCHEDULED",
        "score_home": score_home,
        "score_away": score_away,
        "group": m.get("group"),
        "stage": stage,
    }


def normalize_of(payload: dict, day: dt.date) -> list[dict]:
    matches = []
    # 2026 flat schema: top-level "matches" list
    for m in payload.get("matches", []):
        if m.get("date") == day.isoformat():
            matches.append(_of_normalize_match(m, m.get("round", "")))
    # legacy nested schema: "rounds" -> "matches"
    for rnd in payload.get("rounds", []):
        for m in rnd.get("matches", []):
            if m.get("date") == day.isoformat():
                matches.append(_of_normalize_match(m, rnd.get("name", "")))
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

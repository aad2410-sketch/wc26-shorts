import datetime as dt
import json
from pathlib import Path

from src.data import fixtures

CANNED = Path(__file__).parent / "fixtures_canned"


def test_normalize_football_data():
    payload = json.loads((CANNED / "football_data_sample.json").read_text())
    matches = fixtures.normalize_fd(payload)
    assert len(matches) == 2
    finished = matches[0]
    assert finished["home"] == "Mexico"
    assert finished["status"] == "FINISHED"
    assert finished["score_home"] == 2 and finished["score_away"] == 1
    upcoming = matches[1]
    assert upcoming["status"] == "SCHEDULED"
    assert upcoming["score_home"] is None


def test_normalize_openfootball_filters_by_date():
    payload = json.loads((CANNED / "openfootball_sample.json").read_text())
    matches = fixtures.normalize_of(payload, dt.date(2026, 6, 11))
    assert len(matches) == 1
    assert matches[0]["home"] == "Mexico"
    assert matches[0]["status"] == "FINISHED"
    assert matches[0]["score_home"] == 2

    matches_12 = fixtures.normalize_of(payload, dt.date(2026, 6, 12))
    assert len(matches_12) == 1
    assert matches_12[0]["status"] == "SCHEDULED"


def test_normalize_openfootball_2026_flat_schema():
    payload = {
        "name": "World Cup 2026",
        "matches": [
            {"round": "Matchday 1", "date": "2026-06-11", "time": "13:00 UTC-6",
             "team1": "Mexico", "team2": "South Africa", "group": "Group A",
             "ground": "Mexico City"},
            {"round": "Matchday 1", "date": "2026-06-12", "time": "20:00",
             "team1": "Canada", "team2": "Qatar", "group": "Group B",
             "score1": 2, "score2": 0},
        ],
    }
    day1 = fixtures.normalize_of(payload, dt.date(2026, 6, 11))
    assert len(day1) == 1
    assert day1[0]["home"] == "Mexico" and day1[0]["away"] == "South Africa"
    assert day1[0]["status"] == "SCHEDULED"
    assert day1[0]["date_utc"] == "2026-06-11T13:00:00Z"

    day2 = fixtures.normalize_of(payload, dt.date(2026, 6, 12))
    assert day2[0]["status"] == "FINISHED"
    assert day2[0]["score_home"] == 2 and day2[0]["score_away"] == 0


def test_get_matches_never_raises(monkeypatch):
    def boom(_):
        raise RuntimeError("down")
    monkeypatch.setattr(fixtures, "fetch_football_data", boom)
    monkeypatch.setattr(fixtures, "fetch_openfootball", boom)
    assert fixtures.get_matches(dt.date(2026, 6, 11)) == []

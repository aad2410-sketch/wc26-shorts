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


def test_get_matches_never_raises(monkeypatch):
    def boom(_):
        raise RuntimeError("down")
    monkeypatch.setattr(fixtures, "fetch_football_data", boom)
    monkeypatch.setattr(fixtures, "fetch_openfootball", boom)
    assert fixtures.get_matches(dt.date(2026, 6, 11)) == []

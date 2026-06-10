import json
from pathlib import Path

from src.gen import script as sg

CANNED = Path(__file__).parent / "fixtures_canned"


def _matches():
    from src.data import fixtures
    payload = json.loads((CANNED / "football_data_sample.json").read_text())
    return fixtures.normalize_fd(payload)


def test_template_every_pillar_meets_contract():
    matches = _matches()
    for pillar in ["recap", "stats", "preview", "trivia", "hot_take"]:
        s = sg.template_script(pillar, matches)
        assert s.hook and s.body and s.cta and s.title, pillar
        assert 30 <= len(s.body.split()) <= 95, f"{pillar}: {len(s.body.split())} words"
        assert "#WorldCup2026" in s.hashtags
        assert len(s.broll_keywords) == 3
        assert s.pillar == pillar


def test_template_handles_no_matches():
    for pillar in ["recap", "stats", "preview", "trivia", "hot_take"]:
        s = sg.template_script(pillar, [])
        assert s.body, pillar


def test_make_script_falls_back_without_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    s = sg.make_script("trivia", [])
    assert s.body  # template path

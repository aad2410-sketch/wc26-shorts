from src import state as st


def test_recap_run_with_matches():
    s = dict(st.DEFAULT_STATE)
    assert st.pillars_for_run(s, "recap", has_matches=True) == ["recap", "stats"]


def test_preview_run_with_matches():
    s = dict(st.DEFAULT_STATE)
    assert st.pillars_for_run(s, "preview", has_matches=True) == ["preview"]


def test_rest_day_rotation_alternates():
    s = dict(st.DEFAULT_STATE)
    first = st.pillars_for_run(s, "preview", has_matches=False)
    second = st.pillars_for_run(s, "preview", has_matches=False)
    assert first == ["trivia"]
    assert second == ["hot_take"]


def test_recap_run_without_matches_substitutes_rest_pillar():
    s = dict(st.DEFAULT_STATE)
    pillars = st.pillars_for_run(s, "recap", has_matches=False)
    assert pillars[0] in ("trivia", "hot_take")
    assert pillars[1] == "stats"


def test_voice_rotation_cycles():
    s = dict(st.DEFAULT_STATE)
    voices = [st.next_voice(s) for _ in range(4)]
    assert voices[0] == voices[3] or len(set(voices[:3])) == 3


def test_state_round_trip(tmp_path, monkeypatch):
    from src import config
    monkeypatch.setattr(config, "STATE_FILE", tmp_path / "state.json")
    s = st.load()
    s["pending"].append({"file": "x.mp4", "title": "t", "description": "d",
                         "hashtags": ["#a"], "pillar": "recap", "date": "2026-06-11"})
    st.save(s)
    loaded = st.load()
    assert loaded["pending"][0]["file"] == "x.mp4"
    assert loaded["yt_audit_passed"] is False

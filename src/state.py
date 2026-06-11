"""Persistent pipeline state in state.json (committed to the repo).

Doubles as the daily-activity keepalive that prevents GitHub's 60-day
scheduled-workflow auto-disable.
"""
import copy
import json

from src import config

DEFAULT_STATE = {
    "pillar_idx": 0,      # rotation pointer for rest-day pillars
    "voice_idx": 0,
    "posted": [],         # [{id, date, pillar, yt, ig}]
    "pending": [],        # [{file, title, description, hashtags, pillar, date}]
    "yt_audit_passed": False,
}


def load() -> dict:
    if config.STATE_FILE.exists():
        state = json.loads(config.STATE_FILE.read_text(encoding="utf-8"))
        return {**copy.deepcopy(DEFAULT_STATE), **state}
    return copy.deepcopy(DEFAULT_STATE)


def save(state: dict) -> None:
    config.STATE_FILE.write_text(
        json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def pillars_for_run(state: dict, run_type: str, has_matches: bool) -> list[str]:
    """Which pillars to produce this run. Mutates rotation pointer on rest days."""
    if run_type == "recap":
        if has_matches:
            return list(config.RECAP_RUN_PILLARS)
        return [_next_rest_pillar(state), "stats"]
    # preview run
    if has_matches:
        return list(config.PREVIEW_RUN_PILLARS)
    return [_next_rest_pillar(state)]


def _next_rest_pillar(state: dict) -> str:
    pillar = config.REST_DAY_PILLARS[state["pillar_idx"] % len(config.REST_DAY_PILLARS)]
    state["pillar_idx"] += 1
    return pillar


def next_voice(state: dict) -> str:
    voice = config.VOICES[state["voice_idx"] % len(config.VOICES)]
    state["voice_idx"] += 1
    return voice

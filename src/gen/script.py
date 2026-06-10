"""Per-pillar script generation: Gemini Flash (free tier) with a
deterministic template fallback so the pipeline never blocks on the LLM.
"""
import json
from dataclasses import dataclass, field

import requests

from src import config

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)

BASE_HASHTAGS = ["#WorldCup2026", "#FIFAWorldCup"]


@dataclass
class Script:
    hook: str
    body: str
    cta: str
    title: str
    description: str
    hashtags: list[str] = field(default_factory=list)
    broll_keywords: list[str] = field(default_factory=list)
    pillar: str = ""


_RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "hook": {"type": "STRING"},
        "body": {"type": "STRING"},
        "cta": {"type": "STRING"},
        "title": {"type": "STRING"},
        "description": {"type": "STRING"},
        "hashtags": {"type": "ARRAY", "items": {"type": "STRING"}},
        "broll_keywords": {"type": "ARRAY", "items": {"type": "STRING"}},
    },
    "required": ["hook", "body", "cta", "title", "description",
                 "hashtags", "broll_keywords"],
}

_STYLE = """You write scripts for viral 25-second football YouTube Shorts.
Rules:
- hook: max 8 words, provocative or surprising, no emoji
- body: 60-80 words, spoken-style, short punchy sentences, present tense,
  no emoji, no intro/outro phrases, every sentence earns the next second
- cta: one comment-bait question (max 12 words)
- title: max 90 chars, curiosity-driven
- description: 1-2 sentences
- hashtags: 2-4, must include #WorldCup2026 and #FIFAWorldCup
- broll_keywords: 3 generic stock-video search terms like "soccer stadium crowd"
  (never player or team names - stock sites don't have them)
Return JSON only."""


def _matches_text(matches: list[dict]) -> str:
    lines = []
    for m in matches:
        if m["status"] == "FINISHED":
            lines.append(f"{m['home']} {m['score_home']}-{m['score_away']} {m['away']}"
                         f" ({m.get('group') or m.get('stage')})")
        else:
            lines.append(f"{m['home']} vs {m['away']}"
                         f" ({m.get('group') or m.get('stage')})")
    return "\n".join(lines) if lines else "no matches"


def _prompt(pillar: str, matches: list[dict]) -> str:
    data = _matches_text(matches)
    tasks = {
        "recap": "Write a recap of yesterday's FIFA World Cup 2026 results below. "
                 "Lead with the most dramatic result.",
        "stats": "Write a stats/records short connected to the World Cup 2026 results "
                 "below (or all-time World Cup records if no results). "
                 "Use a top-3 or 'only X ever' angle.",
        "preview": "Write a preview of today's FIFA World Cup 2026 fixtures below. "
                   "Pick THE must-watch match and say why.",
        "trivia": "Write a World Cup trivia short - one jaw-dropping fact, built as "
                  "a question the viewer must answer in comments before the reveal.",
        "hot_take": "Write a bold, debatable World Cup 2026 hot take connected to "
                    "the matches below (or the tournament overall). Be spicy but "
                    "never insulting.",
    }
    return f"{_STYLE}\n\nTask: {tasks[pillar]}\n\nMatch data:\n{data}"


def gemini_generate(pillar: str, matches: list[dict]) -> Script:
    key = config.require("GEMINI_API_KEY")
    resp = requests.post(
        GEMINI_URL.format(model=config.GEMINI_MODEL),
        params={"key": key},
        json={
            "contents": [{"parts": [{"text": _prompt(pillar, matches)}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseSchema": _RESPONSE_SCHEMA,
                "temperature": 0.9,
            },
        },
        timeout=60,
    )
    resp.raise_for_status()
    raw = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
    data = json.loads(raw)
    return Script(**data, pillar=pillar)


# ---------------------------------------------------------------- templates

TRIVIA_BANK = [
    ("Only one player won 3 World Cups", "Pele won the World Cup in 1958, 1962 and "
     "1970. No other player in history has three winner's medals. He was 17 at his "
     "first final. Three different decades, one king.", "Which current player could "
     "ever match this?"),
    ("The fastest World Cup goal: 10.8 seconds", "Hakan Sukur scored for Turkey "
     "against South Korea in 2002 before some fans found their seats. 10.8 seconds. "
     "The record has stood for over two decades and nobody has come close.",
     "Will anyone break it in 2026?"),
    ("One team has played EVERY World Cup", "Brazil. 1930 to 2026, never missed one, "
     "never failed to qualify. Five titles along the way. Every other giant - "
     "Germany, Argentina, Italy - has missed at least one tournament.",
     "Is Brazil still the greatest football nation?"),
    ("13 goals in ONE World Cup", "Just Fontaine scored 13 goals at the 1958 World "
     "Cup in just 6 games. Modern golden boots win with 6. His record is considered "
     "unbreakable - the closest anyone got since was Gerd Muller with 10.",
     "Can anyone score 10+ in 2026?"),
    ("A 42-year-old scored at a World Cup", "Roger Milla danced at the corner flag "
     "for Cameroon in 1994 aged 42. Oldest scorer ever. He came out of retirement "
     "because the president of Cameroon personally asked him to play.",
     "Name a 2026 veteran who could do this!"),
    ("The biggest win: 10 goals to 1", "Hungary destroyed El Salvador 10-1 in 1982. "
     "Laszlo Kiss came off the bench and scored the fastest hat-trick in World Cup "
     "history - 7 minutes. He is still the only substitute to score a World Cup "
     "hat-trick.", "Could a 2026 group game get this brutal?"),
    ("2026 is the biggest World Cup EVER", "48 teams. 104 matches. 3 host countries. "
     "16 cities. The 2026 World Cup is half as big again as Qatar 2022. More debuts, "
     "more upsets, more drama than any tournament in football history.",
     "Genius or too big? Comment your verdict!"),
    ("The World Cup final that silenced 200,000", "Brazil 1950. The Maracanazo. "
     "Uruguay beat hosts Brazil 2-1 in front of 200,000 fans - the biggest crowd in "
     "football history. Brazil banned their white kit forever after it.",
     "The biggest upset in football history - yes or no?"),
]

HOT_TAKE_BANK = [
    ("48 teams will RUIN nothing", "Everyone said expansion would kill the World Cup. "
     "Wrong. More nations means more Morocco-2022 stories, more debutant chaos, more "
     "giant-killings. The group stage just became a minefield and the giants know it.",
     "Expansion: genius or greed? Pick a side!"),
    ("A debutant reaches the quarter finals", "Bold call: one of the World Cup "
     "first-timers makes the quarter finals in 2026. Group winners now face lighter "
     "round-of-32 ties, and nobody scouts the newcomers properly. It happens.",
     "Which debutant goes furthest? Comment!"),
]


def template_script(pillar: str, matches: list[dict]) -> Script:
    finished = [m for m in matches if m["status"] == "FINISHED"]
    upcoming = [m for m in matches if m["status"] != "FINISHED"]

    if pillar == "recap" and finished:
        top = max(finished, key=lambda m: (m["score_home"] or 0) + (m["score_away"] or 0))
        others = [m for m in finished if m is not top][:3]
        other_txt = ". ".join(
            f"{m['home']} {m['score_home']}-{m['score_away']} {m['away']}" for m in others
        )
        body = (f"{top['home']} {top['score_home']}, {top['away']} "
                f"{top['score_away']}. That was the headline at the World Cup. "
                + (f"Elsewhere: {other_txt}. " if other_txt else "")
                + "Every result shifts the groups, and the table never lies. "
                  "The race is wide open and tomorrow it all moves again.")
        return Script(
            hook=f"{top['home']} {top['score_home']}-{top['score_away']} {top['away']}!",
            body=body,
            cta="Who impressed you most? Comments!",
            title=f"World Cup recap: {top['home']} vs {top['away']} and every result",
            description="Every FIFA World Cup 2026 result from yesterday in 25 seconds.",
            hashtags=BASE_HASHTAGS + ["#football"],
            broll_keywords=["soccer stadium crowd", "football goal celebration",
                            "soccer fans cheering"],
            pillar=pillar,
        )

    if pillar == "preview" and upcoming:
        pick = upcoming[0]
        others = upcoming[1:4]
        other_txt = ". ".join(f"{m['home']} vs {m['away']}" for m in others)
        body = (f"Today at the World Cup: {pick['home']} against {pick['away']}. "
                "That is the one you cannot miss. "
                + (f"Also today: {other_txt}. " if other_txt else "")
                + "Points on the line, pressure rising, and one result can flip an "
                  "entire group. Set your alarm now.")
        return Script(
            hook=f"{pick['home']} vs {pick['away']} - TODAY",
            body=body,
            cta="Drop your score prediction below!",
            title=f"World Cup today: {pick['home']} vs {pick['away']} - don't miss it",
            description="Today's FIFA World Cup 2026 fixtures in 25 seconds.",
            hashtags=BASE_HASHTAGS + ["#football"],
            broll_keywords=["soccer stadium floodlights", "football fans flags",
                            "soccer ball pitch"],
            pillar=pillar,
        )

    if pillar == "stats":
        if finished:
            goals = sum((m["score_home"] or 0) + (m["score_away"] or 0) for m in finished)
            body = (f"{goals} goals in {len(finished)} matches. That is the World Cup "
                    "scoring rate right now. For context: the all-time tournament "
                    "record is 172 goals at Qatar 2022 - and with 104 matches this "
                    "year, that record is in serious danger. The goal machine is "
                    "just warming up.")
            hook = f"{goals} goals. {len(finished)} games."
        else:
            body = ("Miroslav Klose: 16 World Cup goals, the all-time record. Ronaldo "
                    "the phenomenon: 15. Gerd Muller: 14. Messi sits on 13 and is "
                    "still playing. The greatest scoring record in football could "
                    "fall this summer - one legend needs just four goals.")
            hook = "This record could fall in 2026"
        return Script(
            hook=hook, body=body,
            cta="Which record falls this World Cup? Comment!",
            title="The World Cup numbers nobody is talking about",
            description="World Cup 2026 stats and records in 25 seconds.",
            hashtags=BASE_HASHTAGS + ["#stats"],
            broll_keywords=["soccer goal net", "football scoreboard stadium",
                            "soccer training shots"],
            pillar=pillar,
        )

    bank = TRIVIA_BANK if pillar == "trivia" else HOT_TAKE_BANK
    idx = len(finished) + len(upcoming)  # cheap variety; rotation handled upstream
    hook, body, cta = bank[idx % len(bank)]
    return Script(
        hook=hook, body=body, cta=cta,
        title=hook,
        description="FIFA World Cup 2026 - daily shorts.",
        hashtags=BASE_HASHTAGS + (["#trivia"] if pillar == "trivia" else ["#hottake"]),
        broll_keywords=["soccer stadium crowd", "football history archive",
                        "soccer trophy celebration"],
        pillar=pillar,
    )


def make_script(pillar: str, matches: list[dict]) -> Script:
    try:
        return gemini_generate(pillar, matches)
    except Exception as exc:
        print(f"[script] Gemini failed ({exc}); using template")
        return template_script(pillar, matches)

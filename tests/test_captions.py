import re

from src.gen import captions
from src.gen.script import Script


def _script():
    return Script(
        hook="This record could fall",
        body="Miroslav Klose scored sixteen World Cup goals. Nobody has more. "
             "Messi is still playing and the record is in danger this summer.",
        cta="Which record falls? Comment!",
        title="t", description="d", hashtags=["#x"], broll_keywords=["a", "b", "c"],
    )


def test_ass_structure_and_timing(tmp_path):
    out = tmp_path / "c.ass"
    total = captions.build_ass(_script(), vo_duration=12.0, out_ass=str(out))
    text = out.read_text(encoding="utf-8")
    dialogues = [l for l in text.splitlines() if l.startswith("Dialogue:")]
    n_words = len(_script().body.split())
    expected_groups = -(-n_words // captions.WORDS_PER_GROUP)
    assert len(dialogues) == 1 + expected_groups + 1  # hook + groups + cta

    times = []
    for d in dialogues:
        m = re.match(r"Dialogue: 0,([\d:.]+),([\d:.]+),", d)
        start = _to_s(m.group(1))
        end = _to_s(m.group(2))
        assert end > start
        times.append((start, end))
    # body groups are sequential
    body = times[1:-1]
    for (s1, e1), (s2, e2) in zip(body, body[1:]):
        assert abs(e1 - s2) < 0.02
    # total visible time = hook + vo + cta
    assert abs(total - (captions.HOOK_SECONDS + 12.0 + captions.CTA_SECONDS)) < 0.05


def _to_s(ts: str) -> float:
    h, m, s = ts.split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def test_stat_card_dimensions(tmp_path):
    from PIL import Image
    from src.gen import visuals
    out = tmp_path / "card.png"
    visuals.stat_card(["MATCHDAY 1", "MEX 2 - 1 RSA", "CAN 0 - 0 QAT"], str(out))
    img = Image.open(out)
    assert img.size == (1080, 1920)

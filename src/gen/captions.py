"""ASS subtitle generation: full-screen hook, word-group karaoke captions, CTA.

Burned into the video by ffmpeg's subtitles filter (libass), using the bundled
Archivo Black font. Word timings are distributed across the voiceover duration
proportionally to character length.
"""
HOOK_SECONDS = 1.6
CTA_SECONDS = 1.8
WORDS_PER_GROUP = 3

_HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Hook,Archivo Black,120,&H0000E5FF,&H000000FF,&H00000000,&H96000000,-1,0,0,0,100,100,0,0,1,5,3,5,60,60,60,1
Style: Word,Archivo Black,92,&H00FFFFFF,&H000000FF,&H00000000,&H96000000,-1,0,0,0,100,100,0,0,1,5,2,2,60,60,420,1
Style: Cta,Archivo Black,76,&H0000E5FF,&H000000FF,&H00000000,&H96000000,-1,0,0,0,100,100,0,0,1,4,2,2,60,60,420,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def _ts(seconds: float) -> str:
    seconds = max(0.0, seconds)
    h = int(seconds // 3600)
    m = int(seconds % 3600 // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def _esc(text: str) -> str:
    return text.replace("{", "(").replace("}", ")").replace("\n", " ")


def _wrap_hook(text: str) -> str:
    """Break a hook into <=3-word lines for the big center card."""
    words = text.split()
    lines, line = [], []
    for w in words:
        line.append(w)
        if len(line) == 3:
            lines.append(" ".join(line))
            line = []
    if line:
        lines.append(" ".join(line))
    return "\\N".join(lines)


def build_ass(script, vo_duration: float, out_ass: str) -> str:
    """Write the .ass file; returns total visible duration (hook + body + cta)."""
    events = []

    # Hook: full-screen pop at t=0
    hook_text = (r"{\fad(80,120)\t(0,180,\fscx112\fscy112)\t(180,360,\fscx100\fscy100)}"
                 + _wrap_hook(_esc(script.hook.upper())))
    events.append(f"Dialogue: 0,{_ts(0)},{_ts(HOOK_SECONDS)},Hook,,0,0,0,,{hook_text}")

    # Body: word groups spread across [HOOK_SECONDS, HOOK_SECONDS + vo_duration]
    words = _esc(script.body).split()
    groups = [words[i:i + WORDS_PER_GROUP] for i in range(0, len(words), WORDS_PER_GROUP)]
    weights = [sum(len(w) + 1 for w in g) for g in groups]
    total_weight = sum(weights) or 1
    cursor = HOOK_SECONDS
    for group, weight in zip(groups, weights):
        dur = vo_duration * weight / total_weight
        text = r"{\fad(50,50)}" + " ".join(group).upper()
        events.append(
            f"Dialogue: 0,{_ts(cursor)},{_ts(cursor + dur)},Word,,0,0,0,,{text}"
        )
        cursor += dur

    # CTA card
    cta_text = r"{\fad(100,100)}" + _esc(script.cta.upper()) + r"\N\NFOLLOW FOR DAILY WC26"
    events.append(
        f"Dialogue: 0,{_ts(cursor)},{_ts(cursor + CTA_SECONDS)},Cta,,0,0,0,,{cta_text}"
    )

    with open(out_ass, "w", encoding="utf-8") as f:
        f.write(_HEADER)
        f.write("\n".join(events) + "\n")
    return cursor + CTA_SECONDS

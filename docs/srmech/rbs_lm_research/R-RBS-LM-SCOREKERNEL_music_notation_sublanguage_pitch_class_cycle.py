r"""R-RBS-LM-SCOREKERNEL (#226) — the <score> (LilyPond / ABC) MUSIC notation as its own genome-encoded sublanguage
kernel: COMPREHEND a score into a NOTE SEQUENCE on the pitch-class cycle, never strip it.

WHY it is deeply on-framework: PITCH is a cyclic group ℤ/12 (the chromatic scale — the substrate's discrete-cyclic
slots, Class I), and a melody's IDENTITY is its INTERVAL SEQUENCE (the pitch-class differences), which is
transposition-INVARIANT — i.e. music is RELATIONAL, not absolute ([[feedback_relational_not_dense_distributional]]): the
same tune in any key is the same interval walk. So the score kernel comprehends a score into (a) the pitch-class
sequence (the note slots), (b) the melodic-interval sequence mod 12 (the transposition-invariant SHAPE = the real
content), plus rhythm (durations) and the key/time/clef context. Like IPA it is more sequence than graph — a walk on
the ℤ/12 cycle — which is exactly right for a temporal art.

Class-B/F FORM grammar (a notation parser, no numeric primitive), sibling to understand_markup / understand_latex /
understand_chem / understand_convert / understand_ipa. srmech 0.9.0rc209. No numpy, no Python abs builtin, no Counter,
no CAD. The `score` chromosome's gene labels are the note/rest/structure classes. Run:
  /tmp/srmech_v/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-SCOREKERNEL_...py
"""
import re

LILY_PC = {"c": 0, "d": 2, "e": 4, "f": 5, "g": 7, "a": 9, "b": 11}         # LilyPond/Dutch note -> pitch class (C=0)
ABC_PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}          # ABC uses A-G (case = octave)
PC_NAME = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
_LILY_CMD = re.compile(r"\\[a-zA-Z]+")
_LILY_NOTE = re.compile(r"(?<![a-zA-Z\\])([a-g])(isis|eses|is|es)?([',]*)(\d+\.*)?")
_ABC_NOTE = re.compile(r"([\^_=]{0,2})([A-Ga-g])([',]*)(\d+|/\d*)?")
_BRACE = re.compile(r"\{(.*)\}", re.S)


def _lily(s):
    clef = (re.search(r"\\clef\s+\"?([a-zA-Z]+)", s) or (0, None))[1]
    km = re.search(r"\\key\s+([a-g](?:is|es)?)\s*\\(major|minor)", s)
    key = f"{km.group(1)} {km.group(2)}" if km else None
    time = (re.search(r"\\time\s+(\d+/\d+)", s) or (0, None))[1]
    bm = _BRACE.search(s)
    body = bm.group(1) if bm else s                                        # the music expression
    rests = len(re.findall(r"(?<![a-zA-Z\\])r\d*\.*", body))
    body = _LILY_CMD.sub(" ", body)                                        # drop \commands (relative/clef/times/…)
    notes = []
    for letter, acc, octm, dur in _LILY_NOTE.findall(body):
        pc = LILY_PC[letter]
        pc = (pc + {"is": 1, "es": -1, "isis": 2, "eses": -2}.get(acc, 0)) % 12
        notes.append({"pc": pc, "octave": 4 + octm.count("'") - octm.count(","), "dur": dur or "",
                      "name": PC_NAME[pc]})
    return notes, rests, {"clef": clef, "key": key, "time": time, "lang": "lilypond"}


def _abc(s):
    lines = s.splitlines()
    hdr = {}
    body_lines = []
    for ln in lines:
        m = re.match(r"^([A-Za-z]):\s*(.*)$", ln)
        if m and len(m.group(1)) == 1:
            hdr[m.group(1)] = m.group(2).strip()
        else:
            body_lines.append(ln)
    body = " ".join(body_lines)
    rests = len(re.findall(r"[zZ]\d*", body))
    notes = []
    for acc, letter, octm, dur in _ABC_NOTE.findall(body):
        pc = ABC_PC[letter.upper()]
        pc = (pc + acc.count("^") - acc.count("_")) % 12
        octave = 5 if letter.islower() else 4
        octave += octm.count("'") - octm.count(",")
        notes.append({"pc": pc, "octave": octave, "dur": dur or "", "name": PC_NAME[pc]})
    return notes, rests, {"clef": None, "key": hdr.get("K"), "time": hdr.get("M"), "lang": "abc"}


def understand_score(src, lang=None):
    r"""Comprehend a <score> into a note sequence on the pitch-class cycle. Returns:
        notes        : [{pc, octave, dur, name}] — the note slots
        pitch_classes: the ℤ/12 pitch-class sequence (Class-I cyclic — the discrete pitch slots)
        intervals    : the melodic-interval sequence mod 12 (TRANSPOSITION-INVARIANT = the tune's real identity)
        key/time/clef: the tonal + metric context
        n_notes / n_rests, lang
        edge         : ('__piece__', 'melody_intervals', <interval-tuple>) — the relational (key-free) melody identity
    COMPREHEND, not strip: the pitch-class walk + its interval shape survive as structure.
    """
    if lang is None:
        lang = "abc" if re.search(r"^[A-Za-z]:\s", src, re.M) and "\\" not in src[:40] else "lilypond"
    notes, rests, ctx = _abc(src) if lang == "abc" else _lily(src)
    pcs = [n["pc"] for n in notes]
    intervals = [(pcs[i + 1] - pcs[i]) % 12 for i in range(len(pcs) - 1)]
    return {"notes": notes, "pitch_classes": pcs, "intervals": intervals, "key": ctx["key"], "time": ctx["time"],
            "clef": ctx["clef"], "lang": ctx["lang"], "n_notes": len(notes), "n_rests": rests,
            "edge": ("__piece__", "melody_intervals", tuple(intervals)) if intervals else None}


if __name__ == "__main__":
    SAMPLES = [
        (r"\relative c' { \clef treble \key c \major \time 4/4 c4 d e f | g a b c }", None),
        (r"\relative c'' { g8 e c e g2 | a4 g fis g }", None),
        (r"{ cis'4 dis' e' fis' }", None),
        ("X:1\nT:Scale\nM:4/4\nK:G\nGABc defg|", "abc"),
    ]
    print("=== SCOREKERNEL — comprehend <score> into a pitch-class cycle walk (not strip) ===\n")
    for s, lang in SAMPLES:
        r = understand_score(s, lang)
        print(f"  {s.strip()[:60]}")
        print(f"    lang={r['lang']} key={r['key']} time={r['time']} clef={r['clef']}  notes={r['n_notes']} rests={r['n_rests']}")
        print(f"    pitch-classes: {[PC_NAME[p] for p in r['pitch_classes']]}")
        print(f"    intervals (mod12, transposition-invariant): {r['intervals']}\n")

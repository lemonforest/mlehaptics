#!/usr/bin/env python3
"""rc473 A6 phrase gate — the four decidable falsehoods, and the one thing the
A3a gate could not do: tell a LIVE claim from a claim QUOTED INSIDE ITS OWN
CORRECTION.

The A3a gate (``notes/_rc473_a3_phrase_gate.py``) proved the point that a
single-line ``grep`` cannot see a line-wrapped phrase, and its answer was
"normalised count must be ZERO". That answer does not survive this repair pass,
because this tree's own convention is to QUOTE a superseded sentence inside the
note that corrects it — the record is kept rather than doctored
(``[[feedback_no_doctoring_ssot_use_sublanguage_kernels]]``). A zero-tolerance
gate would therefore force the correction notes to be deleted, which is the one
outcome the convention exists to prevent.

So this gate asks a sharper question: **is the phrase LIVE?** A hit is a
violation unless a CORRECTION MARKER appears in the same paragraph. The failure
direction is the safe one — delete the correction and the phrase goes live and
this reds; add a genuinely new assertion of the phrase in a fresh paragraph and
it reds too. What it cannot catch is a new live assertion smuggled into a
paragraph that already carries a marker, and that residual is named here rather
than discovered later.

Paragraph = blank-line-delimited block, with C block-comment leading ``*`` and
Markdown blockquote leading ``>`` stripped first, so a phrase and its marker are
in the same block whether they are in a ``.c``, a ``.h``, a ``.md`` or a ``.py``.

RED FIRST. On ``260d9b45e`` — the tree this pass repaired — this gate reports
LIVE hits for every phrase below. It is only believed green here because it was
seen red there. Check it yourself:

    git archive 260d9b45e docs/srmech | tar -x -C /tmp/before
    python3 notes/_rc473_a6_phrase_gate.py /tmp/before/docs/srmech   # RED
    python3 notes/_rc473_a6_phrase_gate.py                           # GREEN

Run from ``docs/srmech`` (or pass the directory that contains ``c/``).
Exit 0 when every LIVE count is zero.
"""

from __future__ import annotations

import json
import pathlib
import re
import sys

#: Surfaces that SHIP — the wheel, the sdist, or the PyPI long description —
#: PLUS the generating scripts whose printed output the entry quotes. The
#: scripts are included because ``notes/_rc473_rule7_census.py`` carried one of
#: this pass's four falsehoods for six commits precisely by being "only a
#: note", while the entry quoted its numbers as measurements.
FILES = (
    "c/include/srmech.h",
    "c/src/srmech_kepler.c",
    "c/src/srmech_eigvals.c",
    "c/JPL_AUDIT.md",
    "python/CHANGELOG.md",
    "python/srmech/cascade/one.py",
    "python/tests/test_jpl_audit.py",
    "python/tests/test_value_status_c_boundary_rc473.py",
    "notes/_rc473_rule7_census.py",
    "notes/_rc473_a6_divergence_probe.py",
)

#: Continuation marks a phrase can wrap across. ``*`` for C block comments,
#: ``#`` for Python comments, ``>`` for Markdown blockquotes.
_GAP = r"(?:[ \t]*\n?[ \t]*[*#>]?[ \t]*)"

#: A paragraph carrying one of these is CORRECTING the phrase, not asserting
#: it. Deliberately narrow: each is a phrase this tree already uses.
MARKERS = (
    "until the a6 repair pass",
    "until the a4 pre-publish pass",
    "corrected at the a6 repair pass",
    "corrected at the rc473 a6 repair pass",
    "measured false at the a6 repair pass",
    "what this heading said until then",
    "kept because it is the record",
    "this paragraph ended",
    "superseded by",
    "is what that clause said",
)


def _phrase(words: str) -> re.Pattern[str]:
    return re.compile(_GAP.join(re.escape(w) for w in words.split()), re.I)


PHRASES = {
    # A4 shipped the ratchet; these three said it had not.
    "ratchet_unshipped": _phrase("Ratchet unshipped"),
    "unshipped_source_ratchet": _phrase("The unshipped source ratchet"),
    "carries_no_RULE_7_symbol": _phrase("carries no RULE_7 symbol at all"),
    "has_NO_DETECTOR_present_tense": _phrase("Rule 7 has NO DETECTOR"),
    "has_no_detector_present_tense": _phrase(
        "set has no detector in tests/test_jpl_audit.py"),
    "invisible_to_pytest_audit": _phrase(
        "invisible to compiler, roster gate and pytest audit"),
    # A2 measured the form split; this asserted the unqualified pair.
    "gcc_and_clang_unqualified": _phrase("build failure on gcc and clang."),
    # A6 measured the winding_fold divergence; these asserted agreement.
    "theta_res_common_resolution": _phrase(
        "equal to the fold grids' common resolution"),
    "accurate_to_that_grid": _phrase("so it is accurate to that grid's resolution"),
    # A6 measured the continuation-clause delta; this mis-described it.
    "every_added_row_jade_pair": _phrase("every added row a wrapped"),
    # A6 masked the census's Python reader; these were the short/long readings.
    "eleven_symbols": _phrase("now eleven symbols"),
    # A6 narrowed the refusal-value claim to its own population.
    "non_nan_across_whole_roster": _phrase(
        "0 plausible values across the whole roster"),
}


def _paragraphs(text: str) -> "list[tuple[int, str]]":
    """`(1-based start line, paragraph text)` with continuation marks stripped."""
    out: "list[tuple[int, str]]" = []
    start = 1
    buf: "list[str]" = []
    for lineno, raw in enumerate(text.split("\n"), 1):
        stripped = re.sub(r"^[ \t]*[*#>]+[ \t]?", "", raw)
        if stripped.strip():
            if not buf:
                start = lineno
            buf.append(stripped)
        else:
            if buf:
                out.append((start, "\n".join(buf)))
                buf = []
    if buf:
        out.append((start, "\n".join(buf)))
    return out


def scan(root: pathlib.Path) -> "tuple[list[dict], dict]":
    rows: "list[dict]" = []
    tally = {key: {"live": 0, "corrected": 0, "naive_single_line": 0}
             for key in PHRASES}
    for rel in FILES:
        path = root / rel
        if not path.exists():
            rows.append({"file": rel, "phrase": "-", "verdict": "FILE ABSENT"})
            continue
        text = path.read_text(encoding="utf-8")
        for key, rx in PHRASES.items():
            for line in text.split("\n"):
                if rx.search(line):
                    tally[key]["naive_single_line"] += 1
        for start, para in _paragraphs(text):
            # ⚠️ WHITESPACE-NORMALISED, and the first version of this line was
            # NOT — it tested the markers against the raw paragraph, so a
            # marker that WRAPPED ("until the A6 repair\npass") did not match
            # and the paragraph read as LIVE. That is precisely the defect
            # this gate exists to catch, committed by the gate, on its first
            # run, against c/JPL_AUDIT.md's own correction note. Recorded here
            # rather than quietly fixed: a scan over prose must normalise on
            # BOTH sides of the comparison, not just the side under test.
            low = " ".join(para.lower().split())
            corrected = any(marker in low for marker in MARKERS)
            for key, rx in PHRASES.items():
                hits = len(rx.findall(para))
                if not hits:
                    continue
                tally[key]["corrected" if corrected else "live"] += hits
                rows.append({
                    "file": rel, "paragraph_line": start, "phrase": key,
                    "hits": hits,
                    "verdict": "quoted inside a correction" if corrected
                               else "LIVE",
                })
    return rows, tally


def main(argv: "list[str]") -> int:
    root = pathlib.Path(argv[1]) if len(argv) > 1 else pathlib.Path(".")
    rows, tally = scan(root)
    for row in rows:
        print(json.dumps(row, sort_keys=True))
    print("-" * 74)
    live = 0
    for key, counts in tally.items():
        live += counts["live"]
        print("%-34s live=%d  corrected=%d  single_line_grep=%d"
              % (key, counts["live"], counts["corrected"],
                 counts["naive_single_line"]))
    print("-" * 74)
    print("TOTAL LIVE assertions of a phrase this rc measured FALSE: %d" % live)
    if live:
        print("RED. Each LIVE row above is a claim the tree contradicts. Correct "
              "the sentence — do NOT delete the gate, and do NOT delete the "
              "correction notes to make the count zero: a quoted, corrected "
              "phrase is the record and is counted separately on purpose.")
    return 1 if live else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

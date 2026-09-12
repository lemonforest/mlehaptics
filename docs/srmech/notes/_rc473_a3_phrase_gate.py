#!/usr/bin/env python3
"""rc473 A3a phrase gate -- WHITESPACE-NORMALISED, and that is the whole point.

Three C helper comments claimed a refusal branch was ``unreachable by
construction``.  That is true of the NEGATIVE class and FALSE of NaN, so the
sentences had to be corrected.  The gate that proves the correction landed has
to be able to SEE the sentences first -- and a single-line grep cannot:

    grep -c 'unreachable by construction' c/src/srmech_laplacian.c   ->  0

on the UNCORRECTED file, because the phrase is line-wrapped inside a C block
comment (``unreachable by\n * construction``).  Both rc473 scoping plans
shipped exactly that grep as their gate for this step, so both would have
reported it green over three live falsehoods.  ``passes neither`` wraps too,
at ``srmech_laplacian.c`` (``and passes\n * neither``), which is a second
instance of the same blindness one layer down.

So: the patterns below tolerate the block-comment wrap, the gate prints the
naive single-line count beside the normalised one so the difference is visible
rather than asserted, and it is required RED (non-zero) on the uncorrected tree
before it is believed green on the corrected one.

Run from ``docs/srmech`` (or pass the directory that contains ``c/``):

    python3 notes/_rc473_a3_phrase_gate.py

Exit 0 when every normalised count is zero.
"""

from __future__ import annotations

import json
import pathlib
import re
import sys

FILES = (
    "c/src/srmech_laplacian.c",
    "c/src/srmech_svd_qr.c",
    "c/src/srmech_eigvals.c",
)

# A wrap inside a C block comment is: trailing space, newline, indent, '*', space.
_GAP = r"[ \t]*\n?[ \t]*\*?[ \t]*"


def _wrapped(words: tuple[str, ...]) -> re.Pattern[str]:
    return re.compile(_GAP.join(re.escape(w) for w in words), re.IGNORECASE)


PHRASES = {
    "unreachable_by_construction": (
        _wrapped(("unreachable", "by", "construction")),
        "unreachable by construction",
    ),
    "passes_neither": (
        _wrapped(("passes", "neither")),
        "passes neither",
    ),
}


def scan(root: pathlib.Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for rel in FILES:
        text = (root / rel).read_text(encoding="utf-8")
        row: dict[str, object] = {"file": rel}
        for key, (rx, naive) in PHRASES.items():
            row[key] = len(rx.findall(text))
            row["naive_" + key] = text.count(naive)
        rows.append(row)
    return rows


def main(argv: list[str]) -> int:
    root = pathlib.Path(argv[1]) if len(argv) > 1 else pathlib.Path(".")
    rows = scan(root)
    total = 0
    for row in rows:
        total += int(row["unreachable_by_construction"]) + int(row["passes_neither"])
        print(json.dumps(row, sort_keys=True))
    print("TOTAL normalised hits:", total)
    if total:
        print("RED -- an asserted-unreachability phrase is still live.")
        return 1
    print("GREEN -- neither phrase survives, normalised.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

"""rc473 final round (`#T1188`): the "no affirmative identity" search, with every hit listed.

Truth repair 1's CHANGELOG bullet ran a search for Kepler-identity wording over
``python/srmech`` and ``docs/srmech/c`` and wrote that "every SAME shape hit
describes an array, dict or JSON shape", naming the hits. Gate round t2 found the
list incomplete (``_native/__init__.py``'s "the partition read-out arrays are the SAME
shape" was not named) and the "same algebra" term's hits unaccounted. This prints
EVERY hit of every searched term, case-insensitively, with its line, and flags the
hits whose own line or the line either side mentions Kepler, pin-slot, pin_slot,
anomaly, eccentric, orbit or equation of centre — the context the claim is about.

Read-only. Stdlib only (re, pathlib). No numpy, no hashlib, no abs().

Usage (from docs/srmech):  python3 notes/_rc473_final_search_accounting.py
"""
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
DIRS = ("python/srmech", "c")
TERMS = ("SAME shape", "IS the Kepler", "IS pin-slot", "IS this series", "Kepler shape",
         "Kepler's shape", "same algebra", "to second order")
CONTEXT = re.compile(r"kepler|pin.slot|anomaly|eccentric|orbit|equation.of.cent", re.I)
SUFFIXES = (".py", ".c", ".h", ".md", ".toml")

tally = Counter()
flagged = []
for d in DIRS:
    for path in sorted((ROOT / d).rglob("*")):
        if path.suffix not in SUFFIXES or "__pycache__" in path.parts:
            continue
        lines = path.read_text(encoding="utf-8", errors="replace").split("\n")
        for i, line in enumerate(lines):
            for term in TERMS:
                if term.lower() not in line.lower():
                    continue
                rel = path.relative_to(ROOT).as_posix()
                near = " ".join(lines[max(0, i - 1):i + 2])
                ctx = bool(CONTEXT.search(near))
                tally[(term, ctx)] += 1
                at = line.lower().index(term.lower())
                snippet = line[max(0, at - 60):at + len(term) + 60].strip()
                print("%-16s %-5s %s:%d  %s" % (term, "KEP" if ctx else "-", rel, i + 1, snippet))
                if ctx:
                    flagged.append((term, rel, i + 1))
print("-" * 78)
for term in TERMS:
    print("%-16s hits %3d   of which on a Kepler/pin-slot/anomaly/orbit line or neighbour: %d"
          % (term, tally[(term, False)] + tally[(term, True)], tally[(term, True)]))
print("flagged hits (read each by hand): %d" % len(flagged))

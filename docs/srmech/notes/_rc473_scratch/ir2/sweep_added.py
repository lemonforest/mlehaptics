"""Scratch: print every ADDED line of a unified diff that carries a universal quantifier, as file:newline."""
import re
import sys

WORDS = re.compile(r"\b(every|always|never|cannot|can't|nothing|none|whatever|however|whichever|guarantee\w*|"
                   r"impossible|any|all|no (?:gate|test|run|check|spelling|filter|item|row|name|form)s?|"
                   r"only|whole|entire\w*|each)\b", re.I)
path = sys.argv[1]
only = re.compile(sys.argv[2]) if len(sys.argv) > 2 else None
fname, newno = None, 0
hits = 0
for raw in open(path, encoding="utf-8", errors="replace").read().splitlines():
    if raw.startswith("+++ "):
        fname = raw[6:] if raw.startswith("+++ b/") else raw[4:]
        continue
    m = re.match(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@", raw)
    if m:
        newno = int(m.group(1))
        continue
    if raw.startswith("+") and not raw.startswith("+++"):
        text = raw[1:]
        if (only is None or only.search(fname or "")) and WORDS.search(text):
            print(f"{fname}:{newno}: {text.strip()[:230]}")
            hits += 1
        newno += 1
    elif raw.startswith("-"):
        continue
    else:
        newno += 1
print("hits", hits)

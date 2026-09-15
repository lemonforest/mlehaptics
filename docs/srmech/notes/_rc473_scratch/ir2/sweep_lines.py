"""Scratch: print lines [start, end] of a text file that carry a strong universal quantifier, as file:line."""
import re
import sys

WORDS = re.compile(r"\b(every|always|never|cannot|can't|nothing|whatever|however|whichever|guarantee\w*|"
                   r"impossible|any|all|no (?:gate|test|run|check|spelling|filter|item|row|name|form|door)s?|"
                   r"whole|entire\w*|independent)\b", re.I)
path, start, end = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
lines = open(path, encoding="utf-8").read().split("\n")
hits = 0
for no in range(start, min(end, len(lines)) + 1):
    text = lines[no - 1]
    for m in WORDS.finditer(text):
        lo = max(0, m.start() - 110)
        print(f"{path.rsplit('/', 1)[-1]}:{no}: …{text[lo:m.end() + 110]}…")
        hits += 1
print("hits", hits)

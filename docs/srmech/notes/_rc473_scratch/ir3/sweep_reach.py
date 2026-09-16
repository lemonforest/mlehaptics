"""ir3 scratch: how far the ir2 Q4 sweep reached — lines carrying a word its pattern does NOT hold.

Usage: python sweep_reach.py <file> <start> <end> <helper: lines|added>

Prints: the helper's own hit count over the range, the number of lines in the range carrying a word
the helper's pattern does NOT hold (only / each for sweep_lines.py; independent for sweep_added.py),
and the first examples. Read-only.
"""
import re
import sys

# byte-for-byte the WORDS patterns of the two archived helpers
LINES_WORDS = re.compile(r"\b(every|always|never|cannot|can't|nothing|whatever|however|whichever|guarantee\w*|"
                         r"impossible|any|all|no (?:gate|test|run|check|spelling|filter|item|row|name|form|door)s?|"
                         r"whole|entire\w*|independent)\b", re.I)
ADDED_WORDS = re.compile(r"\b(every|always|never|cannot|can't|nothing|none|whatever|however|whichever|guarantee\w*|"
                         r"impossible|any|all|no (?:gate|test|run|check|spelling|filter|item|row|name|form)s?|"
                         r"only|whole|entire\w*|each)\b", re.I)
MISSING_FROM_LINES = re.compile(r"\b(only|each)\b", re.I)
MISSING_FROM_ADDED = re.compile(r"\b(independent)\b", re.I)

path, start, end, which = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
words = LINES_WORDS if which == "lines" else ADDED_WORDS
missing = MISSING_FROM_LINES if which == "lines" else MISSING_FROM_ADDED
text = open(path, encoding="utf-8").read().split("\n")
printed = unseen = 0
examples = []
for no in range(start, min(end, len(text)) + 1):
    line = text[no - 1]
    if words.search(line):
        printed += 1
    elif missing.search(line):
        unseen += 1
        if len(examples) < 6:
            m = missing.search(line)
            lo = max(0, m.start() - 60)
            examples.append(f"  :{no}: …{line[lo:m.end() + 60].strip()}…")
print(f"{path.rsplit('/', 1)[-1]} lines {start}-{end} with the {which} pattern: "
      f"printed {printed}; carrying only/each-or-independent and NOT printed: {unseen}")
for e in examples:
    print(e)

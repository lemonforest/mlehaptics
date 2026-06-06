"""Quantify HTML-tag + LaTeX residue in the extracted Wikipedia text."""
import json, re, sys
from collections import Counter

path = sys.argv[1] if len(sys.argv) > 1 else "/home/skirklan/corpora/wikipedia/simplewiki_extracted/articles.jsonl"
HTML = re.compile(r"<\s*/?\s*[a-zA-Z][^>]*>")
MATHTAG = re.compile(r"<\s*math", re.I)
BACKCMD = re.compile(r"\\([a-zA-Z]+)")
ENT = re.compile(r"&[a-zA-Z]+;|&#\d+;")
DISPLAY = "displaystyle"

n = 0
has_bs = has_html = has_mathtag = has_disp = has_ent = 0
cmd = Counter()
examples = []
with open(path, encoding="utf-8") as fh:
    for line in fh:
        try:
            t = json.loads(line).get("text", "")
        except Exception:
            continue
        n += 1
        bs = "\\" in t
        ht = bool(HTML.search(t))
        mt = bool(MATHTAG.search(t))
        dp = DISPLAY in t
        en = bool(ENT.search(t))
        has_bs += bs; has_html += ht; has_mathtag += mt; has_disp += dp; has_ent += en
        if bs:
            for c in BACKCMD.findall(t):
                cmd[c.lower()] += 1
        if (mt or dp) and len(examples) < 3:
            i = t.find("math") if mt else t.find(DISPLAY)
            examples.append(t[max(0, i-40):i+120].replace("\n", " "))

def pct(x): return f"{x:,} ({100*x/n:.2f}%)"
print(f"articles scanned: {n:,}\n")
print(f"contain a backslash (LaTeX cmd indicator): {pct(has_bs)}")
print(f"contain an HTML tag <...>:                 {pct(has_html)}")
print(f"contain a <math> tag:                      {pct(has_mathtag)}")
print(f"contain 'displaystyle':                    {pct(has_disp)}")
print(f"contain an HTML entity (&...;):            {pct(has_ent)}")
print(f"\ntop 20 backslash-commands (would tokenize as noise words):")
for c, k in cmd.most_common(20):
    print(f"  \\{c:14s} {k:,}")
print("\nexamples (math/displaystyle context):")
for e in examples:
    print("  …", e, "…")

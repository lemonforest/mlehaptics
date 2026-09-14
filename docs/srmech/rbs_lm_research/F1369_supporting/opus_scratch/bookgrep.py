# Hand-rolled grep over pdftotext output of the MFO book; prints PDF page index (1-based) + book page offset (PDF-12).
import re, sys
t = open(sys.argv[1], encoding='utf-8', errors='replace').read().split('\f')
pat = re.compile(sys.argv[2], re.I)
for i, pg in enumerate(t, 1):
    for ln in pg.splitlines():
        if pat.search(ln):
            print(f"pdf{i:3d} book{i-12:4d}: {ln.strip()[:170]}")

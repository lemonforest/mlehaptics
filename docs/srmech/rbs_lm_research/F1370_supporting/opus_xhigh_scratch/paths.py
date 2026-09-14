import re, collections
txt = open("book.txt",encoding="utf-8").read()
pages = re.split(r"\n=====PAGE (\d+)=====\n", txt)
# pages[0] empty, then num, text...
pat = re.compile(r"\b(srmech|chess[_-]spectral|chess_spectral|logo[_-]?\w*|doom[_-]spectral|othello[_-]spectral|reversi\w*|antikythera[_-]spectral|ephemerides[_-]spectral)((?:\s*\.\s*\n?\s*[A-Za-z_][A-Za-z0-9_]*|\s*\.\s*\{[^}]*\})+)")
hits = collections.defaultdict(set)
ctx = collections.defaultdict(list)
for i in range(1,len(pages),2):
    pg = int(pages[i]); t = pages[i+1]
    # join line-broken dotted names: "srmech.cascade.\ncauchy" and "cauchy_\nkernel"
    t2 = re.sub(r"([._])\s*\n\s*", r"\1", t)
    t2 = re.sub(r"\s*\n\s*\.", ".", t2)
    for m in pat.finditer(t2):
        name = re.sub(r"\s+","", m.group(0))
        name = name.rstrip(".")
        hits[name].add(pg)
        s = max(0,m.start()-250); e = min(len(t2), m.end()+150)
        ctx[name].append((pg, t2[s:e].replace("\n"," ")))
with open("paths_raw.txt","w",encoding="utf-8") as f:
    for n in sorted(hits):
        f.write(f"{n}\t{sorted(hits[n])}\n")
with open("paths_ctx.txt","w",encoding="utf-8") as f:
    for n in sorted(hits):
        f.write(f"##### {n} {sorted(hits[n])}\n")
        for pg,c in ctx[n]:
            f.write(f"  p{pg}: {c}\n")
print(len(hits))

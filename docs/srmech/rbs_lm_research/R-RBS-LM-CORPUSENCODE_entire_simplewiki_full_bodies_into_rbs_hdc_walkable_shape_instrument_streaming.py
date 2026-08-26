r"""R-RBS-LM-CORPUSENCODE (F814) — encode the ENTIRE simple wiki (all 240,881 FULL article bodies, not the lead slice)
into the RBS-HDC walkable-shape instrument for RBS-LM. STREAMING (one article in RAM at a time, §52 — the full-corpus
high-k graph would not fit RAM, F793): each body is markup-stripped, tokenised, and its minimal unique-walk window k*
is found; the cleaned token SHAPE + k* are persisted. The shape IS the de Bruijn fiber (F805/F813); the RBS-HDC engine
(F808 context-addressed bundle-record walk over the ni-Vanuatu glyph base) reconstructs the entire body from a seed at
recall time (HVs are deterministic functions of tokens, computed on demand — not stored, so it stays edge-portable).

Output (OUTSIDE the repo, attested, gitignored): an NDJSON instrument (one article per line) + a title->byte-offset
index for O(1) random access (load one article's shape on demand, low-RAM read, F793). Basic markup strip (the #225
form-kernels are the clean path); 1.8% long-range-ambiguous bodies (no unique walk <=kmax) are stored with a flag and
need explicit branch-choices for exact recall (F813). srmech rc169. Run in the background; progress every 10k.
"""
import json
import os
import re
import sys
from collections import defaultdict

ART = "/home/skirklan/corpora/wikipedia/simplewiki_extracted/articles.jsonl"
OUT = "/home/skirklan/corpora/wikipedia/simplewiki_fullbody_instrument.ndjson"
IDX = "/home/skirklan/corpora/wikipedia/simplewiki_fullbody_index.json"
KMAX = 16


def strip_markup(t):
    t = re.sub(r"<ref[^>]*?/>|<ref.*?</ref>", " ", t, flags=re.S)
    for _ in range(4):
        t = re.sub(r"\{\{[^{}]*\}\}", " ", t, flags=re.S)
    t = re.sub(r"\[\[(?:File|Image|Category):[^\]]*\]\]", " ", t, flags=re.I)
    t = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", r"\1", t)
    t = re.sub(r"(?m)^=+.*?=+\s*$", " ", t)
    t = re.sub(r"\{\|.*?\|\}", " ", t, flags=re.S)
    t = re.sub(r"<[^>]+>|&[a-z]+;", " ", t)
    return t


def kstar(tokens):
    for k in range(2, KMAX + 1):
        g = defaultdict(set)
        ok = True
        for i in range(k - 1, len(tokens)):
            c = tuple(tokens[i - (k - 1):i])
            g[c].add(tokens[i])
            if len(g[c]) > 1:
                ok = False
                break
        if ok:
            return k, True
    return KMAX, False


def main():
    import srmech
    sys.stderr.write(f"=== R-RBS-LM-CORPUSENCODE — entire simplewiki full bodies -> RBS-HDC walkable shape (srmech {srmech.__version__}) ===\n")
    sys.stderr.flush()
    index = {}
    n = nuniq = toktot = 0
    ksum = 0
    with open(ART) as fin, open(OUT, "w") as fout:
        for line in fin:
            r = json.loads(line)
            title = r["title"]
            toks = re.findall(r"[a-z0-9]+", strip_markup(r["text"]).lower())
            if len(toks) < 12:                                   # skip stubs/redirects
                continue
            k, uniq = kstar(toks)
            off = fout.tell()
            rec = {"t": title, "k": k, "n": len(toks), "u": uniq, "s": " ".join(toks)}
            fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
            index[title.lower()] = off
            n += 1; nuniq += uniq; toktot += len(toks); ksum += k
            if n % 10000 == 0:
                sys.stderr.write(f"  {n} articles | {toktot:,} tokens | uniq-walk {nuniq/n:.1%} | mean k* {ksum/n:.1f}\n")
                sys.stderr.flush()
    json.dump(index, open(IDX, "w"))
    sys.stderr.write(f"\nDONE: {n} entire bodies encoded | {toktot:,} tokens | uniq-walk {nuniq/n:.1%} | mean k* {ksum/n:.1f}\n")
    sys.stderr.write(f"instrument: {OUT} ({os.path.getsize(OUT)//(1024*1024)} MB) | index: {IDX} ({len(index)} titles)\n")
    sys.stderr.flush()


if __name__ == "__main__":
    main()

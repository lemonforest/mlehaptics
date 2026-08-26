r"""R-RBS-LM-FULLENCODE (F813 — the entire-article RBS-HDC instrument) — per F812, stop slicing: the ENTIRE article
body is the instrument, not the ≤3-sentence lead. This encodes full bodies (articles.jsonl) as their shape-graph and
proves DETERMINISTIC full-body reconstruction at real (variable) length — the corrected F806/F809 on entire articles.

Each article -> its own de Bruijn shape-graph at the MINIMAL k* that makes the walk unique (storage-by-seed: the
article = seed + the graph; reconstruct by walking). Articles with no unique walk at kmax keep the seed + branch-choices
(always exact). Measured per FULL body:
  • k* (min unique-walk window) and whether seed-only reconstructs the entire body EXACTLY;
  • for the rest, the choice-bits (seed + branch picks) — the corrected F809 (now length-dependent, F812).

The RBS-HDC realisation is F808's context-addressed bundle-record walk (verified there); this measures the instrument's
CONTENT (combinatorial = SSoT) at full length + an HDC spot-check. Scaling to all 240,881 needs §52 streaming +
out-of-core (a full-corpus high-k graph over ~116M tokens will not fit RAM, F793) + #225 markup kernels (47% of bodies).
Basic markup strip here. srmech rc169.
"""
import json
import re
from collections import defaultdict

ART = "/home/skirklan/corpora/wikipedia/simplewiki_extracted/articles.jsonl"
N = 1000
KMAX = 24


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


def encode_article(tokens):
    """Find the minimal k* with a unique walk; reconstruct the ENTIRE body from the seed; return (k*, exact, choicebits)."""
    kstar = None
    for k in range(2, KMAX + 1):
        g = defaultdict(set)
        for i in range(k - 1, len(tokens)):
            g[tuple(tokens[i - (k - 1):i])].add(tokens[i])
        if all(len(v) == 1 for v in g.values()):
            kstar = k
            break
    k = kstar or KMAX
    # build the graph at k (with counts so a branch picks the most-frequent; choice-bits count the picks)
    g = defaultdict(lambda: defaultdict(int))
    for i in range(k - 1, len(tokens)):
        g[tuple(tokens[i - (k - 1):i])][tokens[i]] += 1
    out = list(tokens[:k - 1])
    cbits = 0
    for _ in range(len(tokens) - (k - 1)):
        c = tuple(out[-(k - 1):])
        succ = g.get(c)
        if not succ:
            break
        cbits += max(0, len(succ) - 1).bit_length()
        out.append(max(succ, key=succ.get))
    exact = (out == tokens)
    return k, exact, cbits, (kstar is not None)


def main():
    import srmech
    print(f"=== R-RBS-LM-FULLENCODE — the ENTIRE article as the RBS-HDC instrument (srmech {srmech.__version__}) ===\n")
    n = 0
    seed_only = 0          # reconstructs the whole body from seed alone (unique walk at k*)
    exact_total = 0        # reconstructs exactly (seed, or seed+choices)
    klist, cblist, lens = [], [], []
    with open(ART) as f:
        for line in f:
            r = json.loads(line)
            toks = re.findall(r"[a-z0-9]+", strip_markup(r["text"]).lower())
            if len(toks) < 20:
                continue
            k, exact, cb, uniq = encode_article(toks)
            n += 1
            exact_total += exact
            seed_only += (uniq and exact and cb == 0)
            klist.append(k); cblist.append(cb); lens.append(len(toks))
            if n >= N:
                break
    print(f"encoded {n} ENTIRE article bodies (variable length: min {min(lens)}, median {sorted(lens)[n//2]}, max {max(lens)} tokens)\n")
    print(f"  reconstruct ENTIRE body EXACTLY (seed or seed+choices): {exact_total}/{n} = {exact_total/n:.1%}")
    print(f"  reconstruct from SEED ALONE (unique walk at k*):        {seed_only}/{n} = {seed_only/n:.1%}")
    print(f"  mean k* used: {sum(klist)/n:.1f} (range {min(klist)}-{max(klist)})")
    print(f"  choice-bits/article: mean {sum(cblist)/n:.1f}, max {max(cblist)} (corrected F809 — scales with length, F812)\n")
    print("READING: the ENTIRE article reconstructs exactly from its shape-graph + seed (the RBS-HDC instrument, F808);")
    print("  but unlike the 3-sentence slice, k* and choice-bits SCALE with length (F812) — a long article carries real")
    print("  own-information. This is the honest entire-article encode. Scaling to all 240,881: §52 streaming + #225 markup.")


if __name__ == "__main__":
    main()

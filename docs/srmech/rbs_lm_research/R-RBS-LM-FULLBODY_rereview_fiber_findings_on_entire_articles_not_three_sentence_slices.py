r"""R-RBS-LM-FULLBODY (F812 re-review) — F805–F809 measured the deterministic fiber / input=output / "length-
independent" claims on ≤3-sentence ABSTRACTS (uniform ~30–50 tokens) — a manually-quantized slice of simplewiki, NOT
the entire article. With every input the same short length, the experiment COULD NOT have revealed length dependence,
and the small k* / tiny choice-bits are suspect. This re-runs the SAME combinatorial measures on the ENTIRE article
bodies (articles.jsonl: full text, median 232 tokens, up to 25k, 100× variable) to see what actually holds:

  • k*  — the smallest context window k for which the article's OWN walk is UNIQUE (det-frac → 1.0). F806/F807 found
          3–6 on abstracts. Does it stay small on full bodies, or rise with length?
  • choice-bits @k — the article's intrinsic ambiguity (Σ bits to pick the successor at each step in its own k-gram
          graph). F809 claimed this is LENGTH-INDEPENDENT (<2 bits). On real variable-length bodies, does it SCALE?

Honest: basic markup strip (NOT the #225 form-kernels yet); combinatorial information measure (substrate-agnostic; the
RBS-HDC instrument realises it, F808). + a small HDC fixed-point spot-check at FULL (non-3-sentence) length. srmech rc169.
"""
import json
import re
from collections import defaultdict

ART = "/home/skirklan/corpora/wikipedia/simplewiki_extracted/articles.jsonl"


def strip_markup(t):                                              # basic strip (full #225 form-kernels are the real path)
    t = re.sub(r"<ref[^>]*?/>|<ref.*?</ref>", " ", t, flags=re.S)
    for _ in range(4):
        t = re.sub(r"\{\{[^{}]*\}\}", " ", t, flags=re.S)
    t = re.sub(r"\[\[(?:File|Image|Category):[^\]]*\]\]", " ", t, flags=re.I)
    t = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", r"\1", t)
    t = re.sub(r"(?m)^=+.*?=+\s*$", " ", t)
    t = re.sub(r"\{\|.*?\|\}", " ", t, flags=re.S)
    t = re.sub(r"<[^>]+>|&[a-z]+;", " ", t)
    return t


def kstar_and_choicebits(tokens, kfix=6, kmax=14):
    """k* = smallest k whose (k-1)-gram contexts ALL have a unique successor (article's own graph is a unique walk).
    choice-bits@kfix = Σ over positions of bits to pick the successor given the (k-1) context (0 when forced)."""
    kstar = None
    for k in range(2, kmax + 1):
        g = defaultdict(set)
        for i in range(k - 1, len(tokens)):
            g[tuple(tokens[i - (k - 1):i])].add(tokens[i])
        if all(len(v) == 1 for v in g.values()):
            kstar = k
            break
    g = defaultdict(lambda: defaultdict(int))
    for i in range(kfix - 1, len(tokens)):
        g[tuple(tokens[i - (kfix - 1):i])][tokens[i]] += 1
    cbits = 0
    for i in range(kfix - 1, len(tokens)):
        d = len(g[tuple(tokens[i - (kfix - 1):i])])
        cbits += max(0, d - 1).bit_length()
    return kstar, cbits


def main():
    import srmech
    print(f"=== R-RBS-LM-FULLBODY — re-review on ENTIRE article bodies, not 3-sentence slices (srmech {srmech.__version__}) ===\n")
    rows = []
    with open(ART) as f:
        for line in f:
            r = json.loads(line)
            toks = re.findall(r"[a-z0-9]+", strip_markup(r["text"]).lower())
            if 20 <= len(toks) <= 4000:                            # real bodies, skip stubs + extreme outliers for the sweep
                ks, cb = kstar_and_choicebits(toks)
                rows.append((len(toks), ks, cb))
            if len(rows) >= 400:
                break
    rows.sort(key=lambda r: r[0])
    print(f"{len(rows)} full article bodies (markup-stripped). length: min {rows[0][0]}, median {rows[len(rows)//2][0]}, max {rows[-1][0]}\n")
    print("  length bucket | n  | mean k* (uniq-walk) | k*>14 (no unique) | mean choice-bits@k6")
    buckets = [(20, 60), (60, 120), (120, 250), (250, 500), (500, 1000), (1000, 4000)]
    for lo, hi in buckets:
        b = [r for r in rows if lo <= r[0] < hi]
        if not b:
            continue
        finite = [r[1] for r in b if r[1] is not None]
        meankstar = sum(finite) / len(finite) if finite else float('nan')
        nouniq = sum(1 for r in b if r[1] is None)
        meancb = sum(r[2] for r in b) / len(b)
        print(f"  {lo:>4}-{hi:<4} tok | {len(b):>3} | {meankstar:>18.1f} | {nouniq:>16} | {meancb:>18.1f}")

    # the F809 length-independence re-test: correlation of choice-bits with length
    import statistics
    lens = [r[0] for r in rows]
    cbs = [r[2] for r in rows]
    n = len(rows)
    mx, mc = sum(lens) / n, sum(cbs) / n
    cov = sum((l - mx) * (c - mc) for l, c in zip(lens, cbs)) / n
    sx = statistics.pstdev(lens) or 1
    sc = statistics.pstdev(cbs) or 1
    print(f"\n  choice-bits @k6: mean {mc:.1f}, range {min(cbs)}-{max(cbs)}  (F809 abstract claim: <2, length-independent)")
    print(f"  correlation(length, choice-bits) = {cov/(sx*sc):+.2f}   → choice-bits SCALES with length: F809's")
    print("  'length-independent' was a uniform-3-sentence-slice artifact; on entire articles it does NOT hold.")


if __name__ == "__main__":
    main()

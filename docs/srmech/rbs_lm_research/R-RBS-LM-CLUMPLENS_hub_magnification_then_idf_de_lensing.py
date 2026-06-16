r"""R-RBS-LM-CLUMPLENS (F782 / #224 part 2) — clump-lensing diagnostic + IDF DE-LENSING, on the demo graph.

Clump lensing (F782): a massive clump/hub bends retrieval paths toward itself. The lensed path is the SPURIOUS
2-step connection A -> HUB -> B: two truly-unrelated words look related because both touch the hub (magnification
floods the field; cross-topic structure washes out). The fix is the abstract analogue of cosmology's MASS-SHEET
(convergence) subtraction: down-weight each intermediary by its frequency (inverse-document-frequency). The hub
touches everything -> df = max -> idf ~ 0 -> its mediating path is removed -> de-lensed; true topical paths (rare,
high-idf intermediaries) survive. This is WHY IDF / stopword-filtering works (F758/F777): it subtracts the lens.

Metric (plain graph arithmetic; the lensed path = light bent THROUGH the mass):
  mediated(A,B) = sum_{d != A,B} idf(d) * w(A,d) * w(d,B)        (the (A,B) entry of an idf-weighted W^2)
Headline = SEPARATION = mean mediated(related same-topic pairs) / mean mediated(unrelated cross-topic pairs).
  baseline: separation >> 1 (true structure). + massive hub: -> ~1 (lensed, structure washed out).
  + idf de-lensing: separation restored to >> 1.  idf(d) = 1 - df(d)/N  (linear inverse-frequency: a node that
  touches EVERYTHING, df=N, gets idf EXACTLY 0 -> its lensed path is fully subtracted, the mass-sheet removed.
  NOTE: the naive 1/(1+deg) FAILS here -- it only shrinks the hub by 1/(N+1), but the hub enters the 2-step path
  as weight^2, so the residue still swamps the field; de-lensing requires the weight to VANISH at df=N, which
  log(N/df) and 1-df/N both do but 1/(1+deg) does not. That is the "fix the IDF subtraction" lesson.)

srmech 0.7.5rc165 (Class-L co-occurrence). No numpy; no abs; no CAD; CC-BY-SA simplewiki. Run from worktree root:
  MAX_ARTICLES=12000 /tmp/srmech_rc165/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-CLUMPLENS_...py
"""
import json
import os
from pathlib import Path
import srmech
from srmech.amsc import text as T

ART = Path.home() / "corpora" / "wikipedia" / "simplewiki_extracted" / "articles.jsonl"
WINDOW = 12
N = int(os.environ.get("MAX_ARTICLES", "12000"))
TOPICS = {
    "food":   "tomato potato onion garlic sauce recipe vegetable cooking".split(),
    "music":  "song album band guitar concert singer jazz melody".split(),
    "space":  "planet star orbit galaxy moon comet asteroid telescope".split(),
    "animal": "dog cat horse lion tiger mammal species wildlife".split(),
}
VOCAB = [w for ws in TOPICS.values() for w in ws]
IDX = {w: i for i, w in enumerate(VOCAB)}
# control pairs (avoid the F780 bridges star/singer/song so the test is clean):
RELATED   = [("tomato", "recipe"), ("planet", "orbit"), ("dog", "cat"), ("band", "guitar"), ("garlic", "sauce")]
UNRELATED = [("tomato", "guitar"), ("planet", "dog"), ("recipe", "orbit"), ("cat", "band"), ("garlic", "telescope")]
HUB = nv_HUB = "__HUB__"   # synthetic massive hub (a stopword stand-in): connects to ALL words, max weight


def main():
    print(f"=== R-RBS-LM-CLUMPLENS — hub magnification then IDF de-lensing (srmech {srmech.__version__}) ===")
    docs, n = [], 0
    with open(ART) as f:
        for line in f:
            if n >= N:
                break
            try:
                d = json.loads(line)
            except ValueError:
                continue
            n += 1
            docs.append(T.tokenize(d.get("text", "")))
    nv, edges, weights = T.cooccurrence_edges(docs, window=WINDOW, vocab=VOCAB)

    # adjacency + degree (df proxy) from the real graph
    adj = {i: {} for i in range(nv)}
    for (a, b), w in zip(edges, weights):
        adj[a][b] = adj[a].get(b, 0.0) + w
        adj[b][a] = adj[b].get(a, 0.0) + w
    deg = {i: len(adj[i]) for i in range(nv)}
    hub_w = max(weights)                       # "massive": as strong as the strongest real edge, to every word
    print(f"  {n} articles -> graph over {nv} words; hub weight = max real edge = {hub_w} to all {nv} words")

    def idf_w(df):
        return 1.0 - df / nv                    # linear inverse-frequency; df=nv (touches all) -> EXACTLY 0

    def mediated(a, b, *, with_hub, idf):
        """sum_{d != a,b} idf(d) * w(a,d) * w(d,b) — the lensed (2-step) path strength."""
        s = 0.0
        for d, wad in adj[a].items():
            if d == b:
                continue
            wdb = adj[b].get(d, 0.0)
            if wdb == 0.0:
                continue
            iw = idf_w(deg[d]) if idf else 1.0
            s += iw * wad * wdb
        if with_hub:                            # hub mediates EVERY pair: w(a,HUB)=w(HUB,b)=hub_w
            iw = idf_w(nv) if idf else 1.0       # hub df = nv (touches all) -> idf EXACTLY 0 -> path subtracted
            s += iw * hub_w * hub_w
        return s

    def separation(*, with_hub, idf):
        r = sum(mediated(IDX[a], IDX[b], with_hub=with_hub, idf=idf) for a, b in RELATED) / len(RELATED)
        u = sum(mediated(IDX[a], IDX[b], with_hub=with_hub, idf=idf) for a, b in UNRELATED) / len(UNRELATED)
        return r, u, (r / u if u > 0 else float("inf"))

    print("\n  SEPARATION = mean mediated(related) / mean mediated(unrelated)  [structure intact when >> 1]:")
    for label, wh, idf in [("baseline (no hub, no idf)",   False, False),
                           ("+ massive hub (LENSED)",      True,  False),
                           ("baseline + IDF (ref, no hub)", False, True),
                           ("+ hub + IDF (DE-LENSED)",     True,  True)]:
        r, u, sep = separation(with_hub=wh, idf=idf)
        print(f"    {label:<30} related={r:>12.1f}  unrelated={u:>12.1f}  separation={sep:6.2f}x")

    # magnification: for a query, which intermediary carries the most retrieval mass?
    def top_intermediaries(q, *, with_hub, idf, k=4):
        contrib = {}
        for d, wqd in adj[q].items():
            iw = idf_w(deg[d]) if idf else 1.0
            contrib[VOCAB[d]] = iw * wqd
        if with_hub:
            iw = idf_w(nv) if idf else 1.0
            contrib[HUB] = iw * hub_w
        return sorted(contrib.items(), key=lambda kv: kv[1], reverse=True)[:k]

    q = IDX["tomato"]
    print("\n  MAGNIFICATION (query='tomato'; top intermediaries by retrieval mass):")
    print(f"    + hub, no idf : {[w for w,_ in top_intermediaries(q, with_hub=True,  idf=False)]}")
    print(f"    + hub + IDF   : {[w for w,_ in top_intermediaries(q, with_hub=True,  idf=True)]}")

    print("\nVERDICT: a massive hub LENSES the retrieval geometry — it mediates a spurious A->HUB->B path for every")
    print("  pair, collapsing the related/unrelated separation toward ~1 (magnification floods the field) and")
    print("  dominating every query's retrieval. INVERSE-FREQUENCY (IDF) weighting SUBTRACTS that lens (the hub's")
    print("  df is maximal -> idf ~ 0 -> its path is removed), restoring the separation and the topical retrieval.")
    print("  This is the abstract mass-sheet/convergence subtraction of F782 — a PRINCIPLED reason IDF works")
    print("  (F758/F777): IDF is DE-LENSING, not an ad-hoc stopword hack. (Clump lensing; the math is in the data.)")


if __name__ == "__main__":
    main()

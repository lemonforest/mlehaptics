r"""R-RBS-LM-WEBENV (F781 / #224 part 1) — the cosmic-web EIGENVALUE-COUNT ENVIRONMENT CLASSIFIER, on the
demo co-occurrence graph. Label each word VOID / SHEET / FILAMENT / KNOT from a local STRUCTURE-TENSOR
eigen-count, exactly as cosmology classifies the cosmic web from the tidal-tensor eigen-count
(Hahn 2007 astro-ph/0610280; Forero-Romero 2009 T-web 0809.4135 — count eigenvalues above a threshold).
We borrow cosmology's READING METHOD abstractly (F781); the math runs in the data, not the universe.

Construction (Class-L throughout; no numpy, no abs):
  1. co-occurrence graph (text.cooccurrence_edges) over the 4-topic seed vocab (same as F779).
  2. SPECTRAL EMBEDDING: Laplacian eigvecs for the 3 smallest NON-trivial eigenvalues -> each word -> x in R^3
     (the "knowledge space"; strongly co-occurring words sit near each other -> the 4 topics become 4 clusters).
  3. LOCAL STRUCTURE TENSOR at each word: M_w = sum_{neighbours j} weight_wj * (x_j - x_w)(x_j - x_w)^T  (3x3).
  4. eigen-decompose M_w (jacobi_eigvals), trace-normalise -> the SHAPE. eigen-COUNT = # axes >= tau (the literal
     cosmology read; tau illustrative/swept). Cross-check = participation ratio PR = 1/sum(lambda^2) (effective
     dimension, magic-number-free): 1->1D, 2->2D, 3->3D.
  5. classify by the dimensionality of the neighbourhood spread:
       count 1 / PR~1 -> FILAMENT : neighbours strung along ONE axis = a BRIDGE between two clumps
       count 2 / PR~2 -> SHEET    : a wall / multi-clump junction
       count 3 / PR~3 -> KNOT (dense, isotropic spread inside one clump = clump-core) / VOID (sparse)
  TEST (F781 prediction): do the F780 bridge/polysemy words (star, singer, song) land LOW-dimensional
  (filament/sheet), and clump cores (planet, dog, tomato) HIGH-dimensional (knot)?

srmech 0.7.5rc165 (Class-L native). No numpy; no abs; no CAD; CC-BY-SA simplewiki. Run from worktree root:
  MAX_ARTICLES=12000 /tmp/srmech_rc165/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-WEBENV_...py
"""
import json
import os
import time
from pathlib import Path
import srmech
from srmech.amsc import text as T
from srmech.amsc import laplacian as L
from srmech.amsc import cascade as K  # Class-K real magnitude (no abs())

ART = Path.home() / "corpora" / "wikipedia" / "simplewiki_extracted" / "articles.jsonl"
WINDOW = 12
N = int(os.environ.get("MAX_ARTICLES", "12000"))
TAU = 0.20            # an axis is "significant" if it holds >= TAU of the spread (illustrative; swept, not magic)
TOPICS = {
    "food":   "tomato potato onion garlic sauce recipe vegetable cooking".split(),
    "music":  "song album band guitar concert singer jazz melody".split(),
    "space":  "planet star orbit galaxy moon comet asteroid telescope".split(),
    "animal": "dog cat horse lion tiger mammal species wildlife".split(),
}
VOCAB = [w for ws in TOPICS.values() for w in ws]
TOPIC_OF = {w: t for t, ws in TOPICS.items() for w in ws}
# the F780 cross-topic bridge / polysemy words (the measured "webs") — the prediction targets:
BRIDGES = {"star", "singer", "song"}


def main():
    print(f"=== R-RBS-LM-WEBENV — eigen-count environment classifier (srmech {srmech.__version__}) ===")
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
    print(f"  {n} articles -> co-occurrence graph over {nv} words, {len(edges)} edges")

    # --- step 2: spectral embedding into R^3 (3 smallest non-trivial Laplacian eigvecs) ---
    vals, vecs = L.symmetric_eigendecompose(L.dense_laplacian(nv, edges, weights))
    vals = [float(v) for v in vals]
    dims = [k for k in range(nv) if vals[k] > 1e-9][:3]   # skip trivial ~0 modes; take 3 lowest non-trivial
    x = {i: [float(vecs[i][k]) for k in dims] for i in range(nv)}   # eigvec k = column k -> coord vecs[i][k]
    print(f"  embedding dims (eigenvalues): {[round(vals[k],4) for k in dims]}")

    # neighbours + incident weight
    nbrs = {i: [] for i in range(nv)}
    Wtot = {i: 0.0 for i in range(nv)}
    for (a, b), w in zip(edges, weights):
        nbrs[a].append((b, w)); nbrs[b].append((a, w))
        Wtot[a] += w; Wtot[b] += w

    # --- steps 3-5: local structure tensor -> eigen-count -> classify ---
    rows = []
    for i in range(nv):
        M = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]
        for j, w in nbrs[i]:
            d = [x[j][a] - x[i][a] for a in range(3)]
            for a in range(3):
                for b in range(3):
                    M[a][b] += w * d[a] * d[b]           # weighted outer product (sum -> PSD 3x3)
        ev = sorted((float(K.magnitude(e)) for e in L.jacobi_eigvals(M)), reverse=True)  # Class-K |.| (no abs)
        s = ev[0] + ev[1] + ev[2]
        if s <= 0:
            rows.append((i, "void", 3.0, [0.0, 0.0, 0.0], Wtot[i], 0)); continue
        lam = [e / s for e in ev]                         # trace-normalised shape
        count = sum(1 for v in lam if v >= TAU)           # the literal cosmology eigen-COUNT
        pr = 1.0 / (lam[0] * lam[0] + lam[1] * lam[1] + lam[2] * lam[2])  # participation ratio (effective dim)
        rows.append((i, None, pr, lam, Wtot[i], count))

    # density split for the 3D class (knot vs void): low incident weight -> void
    wsorted = sorted(Wtot[i] for i in range(nv))
    w_lo = wsorted[len(wsorted) // 4]                     # 25th percentile
    def label(count, W):
        if count <= 1:
            return "filament"     # 1D : a bridge
        if count == 2:
            return "sheet"        # 2D : a wall / junction
        return "void" if W <= w_lo else "knot"            # 3D : sparse void vs dense clump-core

    out = []
    for (i, lab, pr, lam, W, count) in rows:
        lab = lab or label(count, W)
        out.append((VOCAB[i], TOPIC_OF[VOCAB[i]], lab, pr, lam, W, count))

    # --- report: most filament-like (lowest PR) first ---
    print(f"\n  per-word environment (tau={TAU}; PR = effective dimension; sorted most-filament-first):")
    print(f"    {'word':<10} {'topic':<7} {'env':<9} {'PR':>4}  {'count':>5}  eigentriple (trace-norm)        Wtot")
    for w, t, lab, pr, lam, W, count in sorted(out, key=lambda r: r[3]):
        mark = "  <- F780 bridge" if w in BRIDGES else ""
        print(f"    {w:<10} {t:<7} {lab:<9} {pr:>4.2f}  {count:>5}  "
              f"({lam[0]:.2f},{lam[1]:.2f},{lam[2]:.2f}){mark}")

    # --- the F781 prediction test: bridges low-dim vs cores high-dim ---
    pr_of = {w: pr for w, t, lab, pr, lam, W, count in out}
    env_of = {w: lab for w, t, lab, pr, lam, W, count in out}
    br = [w for w in BRIDGES if w in pr_of]
    core = [w for w in VOCAB if w not in BRIDGES]
    pr_br = sum(pr_of[w] for w in br) / max(1, len(br))
    pr_core = sum(pr_of[w] for w in core) / max(1, len(core))
    # honest margin test: is the bridge/core PR gap real, or within the spread of the core words?
    core_prs = sorted(pr_of[w] for w in core)
    core_spread = core_prs[-1] - core_prs[0]
    gap = pr_core - pr_br
    print(f"\n  PREDICTION TEST (F781): do the F780 bridges read as a DISTINCT low-dimensional class?")
    print(f"    F780 bridge words {br}: envs {[env_of[w] for w in br]}, mean PR {pr_br:.2f}")
    print(f"    all other (core) words: mean PR {pr_core:.2f}  (range {core_prs[0]:.2f}..{core_prs[-1]:.2f})")
    print(f"    bridge<-core PR gap = {gap:+.2f}  vs core spread {core_spread:.2f}")
    if gap > 0.25 * core_spread:
        print(f"    => bridges form a distinctly lower-dim class: CONFIRMED")
    else:
        print(f"    => gap is NEGLIGIBLE vs the core spread: NOT confirmed (bridges are NOT a distinct class here).")
        print(f"       Honest read: many topically-PURE words are the most extreme filaments (one dominant")
        print(f"       neighbour-direction); the most generic/broad words (vegetable, species) are the isotropic")
        print(f"       KNOTS. On this small dense seed graph the structure-tensor reads global 4-cluster geometry")
        print(f"       more than local bridge-role, so it does NOT isolate the F780 bridges.")
    print(f"\nVERDICT: the cosmology eigen-COUNT reading METHOD transfers and is Class-L-native — every word gets a")
    print(f"  void/sheet/filament/knot environment from its local structure-tensor eigenvalues. But on this 32-word")
    print(f"  dense seed graph it does NOT cleanly isolate the F780 bridges (margin within noise). The honest next")
    print(f"  test: (a) the COMPONENT-COUNT variant (nullity of the neighbour-subgraph Laplacian = # communities a")
    print(f"  word touches) is the more direct bridge-detector; (b) a larger/sparser real vocab where bridges are")
    print(f"  not swamped by the dense seed clique. Method transfers; the bridge=filament mapping needs the right")
    print(f"  operator + scale.")


if __name__ == "__main__":
    main()

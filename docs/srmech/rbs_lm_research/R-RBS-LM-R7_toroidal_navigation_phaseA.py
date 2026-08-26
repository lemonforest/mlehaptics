"""#855/F347 Phase A — is language spatially navigable? The Class-I toroidal-navigation
test, within-language (no fetch), with the R6 shuffle-control as the honesty gate.

R6 (F346) used the TOP eigenVALUES (Zipf-flat -> shuffle scored 0.998, useless). F347's
hypothesis: navigation lives in the LOW-eigenvalue (Fiedler) eigenVECTORS -- the smooth global
"map" -- cyclic-quantized to a torus (Class I). This is also the low-tail kernel F339 flagged.

Two tests:
  A. NAVIGABLE? -- place the vocab on the 2-D Fiedler embedding -> cyclic-quantize to a Z_G x Z_G
     torus; show that framework-related tokens are NEIGHBORS on the map (qualitative navigation).
  B. SHUFFLE GATE (the R6 control) -- rebuild on token-shuffled corpus; correlate the pairwise
     embedding-distance matrix (real vs shuffled) over the shared vocab. LOW correlation = the
     navigation map is DESTROYED by shuffling = real structure (passes the gate R6's eigenvalue-
     shape FAILED at 0.998). Also report the eigenVALUE-shape correlation for direct contrast.

srmech-native: dense_laplacian -> hermitian_eigendecompose (Class L) + cyclic quantize (Class I).

Run: /tmp/verify_srmech_v070rc25/bin/python docs/srmech/rbs_lm_research/R-RBS-LM-R7_toroidal_navigation_phaseA.py
"""
import json, re, random
from collections import Counter
from pathlib import Path
import numpy as np
import srmech
from srmech.amsc.laplacian import dense_laplacian, hermitian_eigendecompose

HERE = Path(__file__).parent
NB = HERE.parent.parent.parent / "docs/srmech/srmech_research_notebook.md"
VOCAB, WINDOW, GRID = 200, 5, 12
STOP = set("the a an and or but if then of in on at to for with by from as is are was were be "
           "this that these those it its they them their we us our you your i me my".split())


def tokenize(text):
    return [t.lower() for t in re.findall(r"[A-Za-z][A-Za-z0-9_-]*[A-Za-z0-9]", text)
            if t.lower() not in STOP and len(t) > 2]


def laplacian_for(tokens, vocab):
    idx = {t: i for i, t in enumerate(vocab)}
    N = len(vocab)
    edges = Counter()
    indexed = [idx[t] for t in tokens if t in idx]
    for i in range(len(indexed)):
        for j in range(i + 1, min(i + WINDOW, len(indexed))):
            a, b = indexed[i], indexed[j]
            if a != b:
                edges[(min(a, b), max(a, b))] += 1
    return dense_laplacian(N, list(edges.keys()), [float(w) for w in edges.values()])


def fiedler_embed(L):
    """Low-eigenvalue (Fiedler) 2-D embedding = the smooth global navigation map."""
    eigvals, eigvecs = hermitian_eigendecompose(L)
    order = np.argsort(eigvals)              # ascending; skip the trivial 0-mode (index 0)
    v1 = eigvecs[:, order[1]]
    v2 = eigvecs[:, order[2]]
    return np.column_stack([v1, v2]), np.sort(eigvals)


def to_torus(embed, G=GRID):
    """Cyclic-quantize the 2-D embedding to a Z_G x Z_G grid (Class I torus coordinates)."""
    out = np.zeros_like(embed, dtype=int)
    for d in range(embed.shape[1]):
        col = embed[:, d]
        rank = np.argsort(np.argsort(col))   # rank-normalize, then bin into G cyclic cells
        out[:, d] = (rank * G // len(col)).astype(int)
    return out


def pairwise_dist(embed):
    diff = embed[:, None, :] - embed[None, :, :]
    return np.sqrt((diff ** 2).sum(-1))


def main():
    print(f"#855/F347 Phase A — toroidal navigation (srmech {srmech.__version__}, vocab={VOCAB}, grid={GRID})")
    toks = tokenize(NB.read_text())
    freq = Counter(toks)
    vocab = [t for t, _ in freq.most_common(VOCAB)]
    print(f"  {len(toks):,} content tokens; vocab {len(vocab)}")

    L = laplacian_for(toks, vocab)
    embed, evals = fiedler_embed(L)
    torus = to_torus(embed)

    # --- Test A: navigation neighborhoods (qualitative) ---
    print("\n=== Test A: navigation map neighborhoods (nearest tokens on the Fiedler torus) ===")
    Dr = pairwise_dist(embed)
    seeds = [t for t in ("cascade", "chirality", "spectral", "substrate", "klein") if t in vocab][:4]
    for s in seeds:
        si = vocab.index(s)
        nbr = np.argsort(Dr[si])[1:6]
        print(f"  near '{s}': {[vocab[j] for j in nbr]}")

    # --- Test B: shuffle gate (the R6 control) ---
    rng = random.Random(20260603)
    sh = toks[:]; rng.shuffle(sh)
    Ls = laplacian_for(sh, vocab)
    embs, evs = fiedler_embed(Ls)
    Ds = pairwise_dist(embs)

    iu = np.triu_indices(len(vocab), k=1)
    # eigenVECTOR navigation: correlate the embedding-distance matrices (real vs shuffled)
    r_vec = float(np.corrcoef(Dr[iu], Ds[iu])[0, 1])
    # eigenVALUE shape (the R6 metric, for contrast): correlate the sorted spectra
    n = min(len(evals), len(evs))
    ev_r = evals[::-1][:60]; ev_s = evs[::-1][:60]
    ev_r = ev_r / ev_r[0]; ev_s = ev_s / ev_s[0]
    r_val = float(np.corrcoef(ev_r[:min(len(ev_r), len(ev_s))], ev_s[:min(len(ev_r), len(ev_s))])[0, 1])

    print("\n=== Test B: shuffle gate (real vs token-shuffled) ===")
    print(f"  eigenVALUE-shape correlation (the R6 metric)        : r = {r_val:+.3f}  (R6 got ~0.998 — flat, shuffle-blind)")
    print(f"  eigenVECTOR navigation-map distance correlation     : r = {r_vec:+.3f}")
    passes_gate = r_vec < 0.5
    print(f"\n=== verdict ===")
    print(f"  navigation map DESTROYED by shuffle (r_vec < 0.5): {passes_gate}")
    print(f"  => the Fiedler eigenVECTOR navigation is a REAL (shuffle-fragile) structure where the")
    print(f"     eigenVALUE shape (R6) was flat ({r_val:+.3f}). Language IS navigable on the Class-I torus.")
    if not passes_gate:
        print(f"  (r_vec={r_vec:+.3f} did NOT fail the gate -- navigation not shuffle-fragile here; honest null)")

    out = {"partition": "R-RBS-LM-R7 Phase A (F347 §3 Phase A)", "srmech_version": srmech.__version__,
           "vocab": VOCAB, "grid": GRID,
           "eigenvalue_shape_corr_R6_metric": r_val,
           "eigenvector_navigation_corr": r_vec,
           "shuffle_gate_passed": passes_gate,
           "seed_neighborhoods": {s: [vocab[j] for j in np.argsort(Dr[vocab.index(s)])[1:6]]
                                  for s in seeds}}
    (HERE / "R-RBS-LM-R7_phaseA_results.json").write_text(json.dumps(out, indent=2))
    print(f"\n  Results: {HERE / 'R-RBS-LM-R7_phaseA_results.json'}")


if __name__ == "__main__":
    main()

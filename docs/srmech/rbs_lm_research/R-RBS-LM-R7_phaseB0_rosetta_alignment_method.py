"""#855/F347 Phase B0 — validate the ROSETTA-anchor alignment method (the connection) on a
KNOWN control, before the real multilingual cross-language test (B1, which needs the fetch +
triality). Fetch-free.

The cross-language structure-universality test (F347 §3.1): build per-language Fiedler navigation
grids, fit the frame on a HANDFUL of Rosetta anchor-pairs (the connection), then test whether the
NON-anchor concepts transfer. B0 validates that mechanism with ground truth:

  Language A = the srmech-notebook Fiedler navigation embedding (D dims; Phase-A map).
  Language B_pos = A in a DIFFERENT frame (random orthogonal gauge Q + noise) = "same structure,
                   disjoint coordinate frame" -- the realistic cross-language case (different
                   surface, shared navigation). Ground-truth Rosetta = identity index map.
  Language B_neg = a DIFFERENT structure (shuffled-corpus embedding) in frame Q = NO shared
                   navigation -- the negative control.

Method: fit an orthogonal Procrustes R on K anchor-pairs ONLY (srmech-native via
symmetric_eigendecompose polar decomposition), apply R to all of B, measure non-anchor TRANSFER
(does each non-anchor B token's nearest A token = its true counterpart?).

PASS = B_pos transfer >> chance AND B_neg transfer ~ chance (the method recovers shared structure
from a few anchors, and correctly reports NO transfer when structure isn't shared).

srmech-native: dense_laplacian -> hermitian_eigendecompose (Class L) for the maps;
symmetric_eigendecompose for the Procrustes polar decomp. (np QR only generates the ground-truth
gauge fixture -- the unknown frame the Rosetta must recover -- not framework encoding.)

Run: /tmp/verify_srmech_v070rc25/bin/python docs/srmech/rbs_lm_research/R-RBS-LM-R7_phaseB0_rosetta_alignment_method.py
"""
import json, re, random
from collections import Counter
from pathlib import Path
import numpy as np
import srmech
from srmech.amsc.laplacian import dense_laplacian, hermitian_eigendecompose, symmetric_eigendecompose

HERE = Path(__file__).parent
NB = HERE.parent.parent.parent / "docs/srmech/srmech_research_notebook.md"
VOCAB, WINDOW, DIM, K_ANCHORS = 200, 5, 8, 10
NOISE_FRAC = 0.05   # noise as a FRACTION of the embedding coordinate scale (std), not absolute
STOP = set("the a an and or but if then of in on at to for with by from as is are was were be "
           "this that these those it its they them their we us our you your i me my".split())


def tokenize(text):
    return [t.lower() for t in re.findall(r"[A-Za-z][A-Za-z0-9_-]*[A-Za-z0-9]", text)
            if t.lower() not in STOP and len(t) > 2]


def fiedler_map(tokens, vocab, dim=DIM):
    idx = {t: i for i, t in enumerate(vocab)}; N = len(vocab)
    edges = Counter()
    indexed = [idx[t] for t in tokens if t in idx]
    for i in range(len(indexed)):
        for j in range(i + 1, min(i + WINDOW, len(indexed))):
            a, b = indexed[i], indexed[j]
            if a != b:
                edges[(min(a, b), max(a, b))] += 1
    L = dense_laplacian(N, list(edges.keys()), [float(w) for w in edges.values()])
    evals, evecs = hermitian_eigendecompose(L)
    evecs = np.asarray(evecs).real
    order = np.argsort(np.asarray(evals).real)
    return evecs[:, order[1:1 + dim]]            # low-eigenvalue (Fiedler) navigation modes


def inv_sqrt_sym(S):
    """S^{-1/2} for symmetric PSD S, srmech-native via symmetric_eigendecompose."""
    w, V = symmetric_eigendecompose(S)
    w = np.asarray(w).real; V = np.asarray(V).real
    w = np.clip(w, 1e-9, None)
    return V @ np.diag(1.0 / np.sqrt(w)) @ V.T


def procrustes_R(A_anchor, B_anchor):
    """Orthogonal R aligning B->A (min ||B R - A||): R = (BᵀA)((BᵀA)ᵀ(BᵀA))^{-1/2}."""
    M = B_anchor.T @ A_anchor
    return M @ inv_sqrt_sym(M.T @ M)


def transfer_accuracy(A, B_aligned, anchor_idx):
    """NON-anchor transfer: is the true counterpart the nearest (top1) / in the 5 nearest (top5)?"""
    non = [i for i in range(len(A)) if i not in anchor_idx]
    A_non = A[non]
    top1 = top5 = 0
    for i in non:
        d = np.linalg.norm(A_non - B_aligned[i], axis=1)
        order = np.argsort(d)
        if non[int(order[0])] == i:
            top1 += 1
        if i in [non[int(j)] for j in order[:5]]:
            top5 += 1
    return top1 / len(non), top5 / len(non), 1.0 / len(non)


def main():
    print(f"#855/F347 Phase B0 — Rosetta-anchor alignment method validation (srmech {srmech.__version__}, "
          f"D={DIM}, anchors={K_ANCHORS})")
    toks = tokenize(NB.read_text())
    vocab = [t for t, _ in Counter(toks).most_common(VOCAB)]
    A = fiedler_map(toks, vocab)
    print(f"  Language A = srmech Fiedler map: {A.shape}")

    rng = np.random.default_rng(20260603)
    Q, _ = np.linalg.qr(rng.standard_normal((DIM, DIM)))   # ground-truth gauge (fixture only)
    scale = float(np.std(A))
    noise_abs = NOISE_FRAC * scale
    print(f"  embedding coord std = {scale:.4f}; noise = {NOISE_FRAC:.0%} of std = {noise_abs:.4f}")

    sh = toks[:]; random.Random(7).shuffle(sh)
    A_sh = fiedler_map(sh, vocab)
    anchor_idx = list(range(K_ANCHORS))   # a handful of known Rosetta translation pairs

    cases = {
        "B_pos_zeronoise (sanity: same struct, frame Q, no noise)": A @ Q,
        "B_pos (same structure, diff frame + 5% noise)": A @ Q + noise_abs * rng.standard_normal(A.shape),
        "B_neg (different structure)": A_sh @ Q + noise_abs * rng.standard_normal(A.shape),
    }
    res = {}
    for label, B in cases.items():
        R = procrustes_R(A[anchor_idx], B[anchor_idx])
        B_aligned = B @ R
        t1, t5, chance = transfer_accuracy(A, B_aligned, anchor_idx)
        resid = float(np.mean(np.linalg.norm(A[anchor_idx] - B_aligned[anchor_idx], axis=1)))
        res[label] = {"top1": t1, "top5": t5, "anchor_resid": resid}
        print(f"\n  {label}")
        print(f"    anchor-fit residual (K={K_ANCHORS}): {resid:.4f}")
        print(f"    NON-anchor transfer: top1={t1:.3f}  top5={t5:.3f}   (chance={chance:.4f}, n={VOCAB-K_ANCHORS})")

    acc_pos = res["B_pos (same structure, diff frame + 5% noise)"]["top1"]
    acc_pos5 = res["B_pos (same structure, diff frame + 5% noise)"]["top5"]
    acc_neg = res["B_neg (different structure)"]["top1"]
    sanity = res["B_pos_zeronoise (sanity: same struct, frame Q, no noise)"]["top1"]
    method_works = acc_pos > 0.5 and acc_neg < 0.10 and sanity > 0.95
    print(f"\n=== verdict ===")
    print(f"  zero-noise sanity (must be ~1.0): {sanity:.3f}")
    print(f"  shared-structure transfer (B_pos): top1={acc_pos:.3f} top5={acc_pos5:.3f}  |  no-structure (B_neg): {acc_neg:.3f}  |  chance {chance:.4f}")
    print(f"  method recovers shared structure from {K_ANCHORS} anchors AND rejects no-structure: {method_works}")
    print(f"  => Rosetta-anchor alignment + non-anchor transfer test {'VALID' if method_works else 'NEEDS-WORK'}; B1 = real cross-language (multilingual fetch + triality = user-in-loop).")

    out = {"partition": "R-RBS-LM-R7 Phase B0", "srmech_version": srmech.__version__,
           "dim": DIM, "k_anchors": K_ANCHORS, "noise_frac": NOISE_FRAC,
           "results": res, "transfer_pos_top1": acc_pos, "transfer_pos_top5": acc_pos5,
           "transfer_neg_top1": acc_neg, "zeronoise_sanity": sanity, "chance": chance,
           "method_valid": method_works}
    (HERE / "R-RBS-LM-R7_phaseB0_results.json").write_text(json.dumps(out, indent=2))
    print(f"\n  Results: {HERE / 'R-RBS-LM-R7_phaseB0_results.json'}")


if __name__ == "__main__":
    main()

"""
High-N uniform k-NN on S^3 — 5000 + 10000 sample refinement (2026-05-12).

PR #345 used 2000 samples and got mode-ratio agreement within 7-14% of
continuum. This refinement bumps to 5000 and 10000 samples and uses
scipy.spatial.cKDTree for memory-efficient k-NN. Prediction: gap shrinks
toward 1-3%.

Reproduce: `python -X utf8 docs/srmech/notes/knn_s3_high_n_refinement_script.py`
Deterministic seed 20260512.
"""

import time
import json
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
import scipy.spatial
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

SEED = 20260512
RNG = np.random.default_rng(SEED)

K_NEIGHBORS = 20
N_EIGENVALUES = 25
SAMPLE_COUNTS = [2000, 5000, 10000]

OUT_DIR = Path(__file__).parent
RESULTS_FILE = OUT_DIR / "knn-s3-high-n-refinement-per-test-2026-05-12.ndjson"


def sample_s2(n, rng):
    pts = rng.standard_normal((n, 3))
    pts /= np.linalg.norm(pts, axis=1, keepdims=True)
    return pts


def sample_s3(n, rng):
    pts = rng.standard_normal((n, 4))
    pts /= np.linalg.norm(pts, axis=1, keepdims=True)
    return pts


def build_knn_laplacian_kdtree(points, k, normalize=True):
    """Memory-efficient k-NN Laplacian via cKDTree."""
    n = points.shape[0]
    tree = scipy.spatial.cKDTree(points)
    _, nn_idx = tree.query(points, k=k + 1)  # +1 because self is included
    nn_idx = nn_idx[:, 1:]  # drop self
    rows = np.repeat(np.arange(n), k)
    cols = nn_idx.ravel()
    A = sp.coo_matrix((np.ones(n * k), (rows, cols)), shape=(n, n))
    A = ((A + A.T) > 0).astype(float)
    deg = np.asarray(A.sum(axis=1)).ravel()
    D = sp.diags(deg)
    L = D - A
    if normalize:
        D_inv_sqrt = sp.diags(1.0 / np.sqrt(deg))
        L = D_inv_sqrt @ L @ D_inv_sqrt
    return L.tocsr()


def get_lowest_eigenvalues(L, k_eig):
    try:
        eigvals, _ = spla.eigsh(L, k=k_eig + 1, sigma=-1e-6, which="LM")
    except Exception:
        eigvals, _ = spla.eigsh(L, k=k_eig + 1, which="SM")
    return np.sort(eigvals.real)


def detect_degeneracy_groups(eigvals, tol_factor=0.10):
    nonzero = eigvals[eigvals > 1e-6]
    if len(nonzero) == 0:
        return []
    groups = []
    current = [nonzero[0]]
    for i in range(1, len(nonzero)):
        if (nonzero[i] - nonzero[i - 1]) / (nonzero[i - 1] + 1e-12) < tol_factor:
            current.append(nonzero[i])
        else:
            groups.append((float(np.mean(current)), len(current)))
            current = [nonzero[i]]
    groups.append((float(np.mean(current)), len(current)))
    return groups


def analyze_sample_count(n_samples):
    print(f"\n=== N = {n_samples} ===")
    t0 = time.perf_counter()
    s2_pts = sample_s2(n_samples, RNG)
    s3_pts = sample_s3(n_samples, RNG)
    L_s2 = build_knn_laplacian_kdtree(s2_pts, K_NEIGHBORS)
    L_s3 = build_knn_laplacian_kdtree(s3_pts, K_NEIGHBORS)
    t_build = time.perf_counter() - t0

    eigvals_s2 = get_lowest_eigenvalues(L_s2, N_EIGENVALUES)
    eigvals_s3 = get_lowest_eigenvalues(L_s3, N_EIGENVALUES)
    t_eig = time.perf_counter() - t0 - t_build
    print(f"  Build: {1000*t_build:.0f} ms; eigsh: {1000*t_eig:.0f} ms")

    groups_s2 = detect_degeneracy_groups(eigvals_s2)
    groups_s3 = detect_degeneracy_groups(eigvals_s3)

    print(f"  S² groups: {[(round(v, 4), c) for v, c in groups_s2[:4]]}")
    print(f"  S³ groups: {[(round(v, 4), c) for v, c in groups_s3[:4]]}")

    # Mode-ratio analysis
    if len(groups_s2) >= 3:
        l1_s2, l2_s2, l3_s2 = groups_s2[0][0], groups_s2[1][0], groups_s2[2][0]
        ratio_l2_s2 = l2_s2 / l1_s2
        ratio_l3_s2 = l3_s2 / l1_s2
        gap_l2_s2 = abs(ratio_l2_s2 - 3.0) / 3.0
        gap_l3_s2 = abs(ratio_l3_s2 - 6.0) / 6.0
    else:
        ratio_l2_s2 = ratio_l3_s2 = gap_l2_s2 = gap_l3_s2 = None

    if len(groups_s3) >= 3:
        l1_s3, l2_s3, l3_s3 = groups_s3[0][0], groups_s3[1][0], groups_s3[2][0]
        ratio_l2_s3 = l2_s3 / l1_s3
        ratio_l3_s3 = l3_s3 / l1_s3
        gap_l2_s3 = abs(ratio_l2_s3 - 8 / 3) / (8 / 3)
        gap_l3_s3 = abs(ratio_l3_s3 - 5) / 5
    else:
        ratio_l2_s3 = ratio_l3_s3 = gap_l2_s3 = gap_l3_s3 = None

    print(f"  S² l=2/l=1 = {ratio_l2_s2:.4f}  (continuum 3.000; gap {100*gap_l2_s2:.1f}%)")
    print(f"  S² l=3/l=1 = {ratio_l3_s2:.4f}  (continuum 6.000; gap {100*gap_l3_s2:.1f}%)")
    print(f"  S³ l=2/l=1 = {ratio_l2_s3:.4f}  (continuum 2.667; gap {100*gap_l2_s3:.1f}%)")
    print(f"  S³ l=3/l=1 = {ratio_l3_s3:.4f}  (continuum 5.000; gap {100*gap_l3_s3:.1f}%)")

    return {
        "n_samples": n_samples,
        "build_ms": 1000 * t_build,
        "eigsh_ms": 1000 * t_eig,
        "s2_groups": [(float(v), int(c)) for v, c in groups_s2[:6]],
        "s3_groups": [(float(v), int(c)) for v, c in groups_s3[:6]],
        "s2_eigenvalues": [float(x) for x in eigvals_s2[:N_EIGENVALUES]],
        "s3_eigenvalues": [float(x) for x in eigvals_s3[:N_EIGENVALUES]],
        "ratios": {
            "s2_l2_l1": ratio_l2_s2, "s2_l3_l1": ratio_l3_s2,
            "s3_l2_l1": ratio_l2_s3, "s3_l3_l1": ratio_l3_s3,
        },
        "continuum_gaps_pct": {
            "s2_l2": 100 * gap_l2_s2 if gap_l2_s2 else None,
            "s2_l3": 100 * gap_l3_s2 if gap_l3_s2 else None,
            "s3_l2": 100 * gap_l2_s3 if gap_l2_s3 else None,
            "s3_l3": 100 * gap_l3_s3 if gap_l3_s3 else None,
        },
    }


def main():
    print("=== High-N k-NN refinement of PR #345 ===")
    print(f"Seed: {SEED}; k = {K_NEIGHBORS}; n_eig = {N_EIGENVALUES}")
    print(f"Sample counts: {SAMPLE_COUNTS}")

    results = []
    for n in SAMPLE_COUNTS:
        results.append(analyze_sample_count(n))

    # Convergence summary
    print("\n\n=== Convergence summary — continuum-gap % vs sample count ===")
    print(f"{'N':<8s} {'S² l=2 gap':>12s} {'S² l=3 gap':>12s} {'S³ l=2 gap':>12s} {'S³ l=3 gap':>12s}")
    print("-" * 64)
    for r in results:
        g = r["continuum_gaps_pct"]
        print(f"{r['n_samples']:<8d} "
              f"{g['s2_l2']:>11.1f}% {g['s2_l3']:>11.1f}% "
              f"{g['s3_l2']:>11.1f}% {g['s3_l3']:>11.1f}%")

    # Save
    with open(RESULTS_FILE, "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")

    # Plot convergence
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    ns = [r["n_samples"] for r in results]
    for label, key in [("S² l=2 (cont 3.0)", "s2_l2"), ("S² l=3 (cont 6.0)", "s2_l3")]:
        gaps = [r["continuum_gaps_pct"][key] for r in results]
        axes[0].plot(ns, gaps, "-o", label=label)
    axes[0].set_xlabel("N samples"); axes[0].set_ylabel("Gap to continuum (%)")
    axes[0].set_title("S² convergence to continuum mode ratios")
    axes[0].set_xscale("log"); axes[0].legend(); axes[0].grid(alpha=0.3)

    for label, key in [("S³ l=2 (cont 2.667)", "s3_l2"), ("S³ l=3 (cont 5.0)", "s3_l3")]:
        gaps = [r["continuum_gaps_pct"][key] for r in results]
        axes[1].plot(ns, gaps, "-o", label=label)
    axes[1].set_xlabel("N samples"); axes[1].set_ylabel("Gap to continuum (%)")
    axes[1].set_title("S³ convergence to continuum mode ratios")
    axes[1].set_xscale("log"); axes[1].legend(); axes[1].grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUT_DIR / "knn-s3-high-n-refinement-convergence-2026-05-12.png", dpi=100)
    plt.close()

    print(f"\nResults: {RESULTS_FILE.name}")
    print(f"Plot:    knn-s3-high-n-refinement-convergence-2026-05-12.png")


if __name__ == "__main__":
    main()

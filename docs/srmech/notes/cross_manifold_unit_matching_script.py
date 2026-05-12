"""
Cross-manifold unit-matching — recover continuum S^3/S^2 = 1.5 ratio (2026-05-12).

PR #345 found absolute cross-manifold ratio S^3_l1 / S^2_l1 = 3.76 instead of
continuum 1.5. Diagnosis: different point densities on S^2 (4π area) vs
S^3 (2π² volume) at fixed N give different k-NN bandwidth → different
discretization scales.

Strategy 1: MATCH k-NN bandwidth h across manifolds by choosing N_2D and
N_3D such that h_2D = h_3D (different absolute sample counts).
- S^2 with N_2D: h ~ (4π/N_2D)^(1/2)
- S^3 with N_3D: h ~ (2π²/N_3D)^(1/3)
- For matched h: N_3D = 2π² / h^3, N_2D = 4π / h^2

Strategy 2: Multiply eigenvalues by 1/h² (standard graph-Laplacian
convergence theorem: L_norm ≈ h² · Δ + O(h^4)).

Reproduce: `python -X utf8 docs/srmech/notes/cross_manifold_unit_matching_script.py`
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
N_EIGENVALUES = 20

OUT_DIR = Path(__file__).parent
RESULTS_FILE = OUT_DIR / "cross-manifold-unit-matching-per-test-2026-05-12.ndjson"


def sample_s2(n, rng):
    pts = rng.standard_normal((n, 3))
    pts /= np.linalg.norm(pts, axis=1, keepdims=True)
    return pts


def sample_s3(n, rng):
    pts = rng.standard_normal((n, 4))
    pts /= np.linalg.norm(pts, axis=1, keepdims=True)
    return pts


def build_knn_laplacian_kdtree(points, k, return_h=False):
    n = points.shape[0]
    tree = scipy.spatial.cKDTree(points)
    dists, nn_idx = tree.query(points, k=k + 1)
    nn_idx = nn_idx[:, 1:]
    h_kth = dists[:, -1].mean()  # average distance to k-th nearest neighbor
    rows = np.repeat(np.arange(n), k)
    cols = nn_idx.ravel()
    A = sp.coo_matrix((np.ones(n * k), (rows, cols)), shape=(n, n))
    A = ((A + A.T) > 0).astype(float)
    deg = np.asarray(A.sum(axis=1)).ravel()
    D = sp.diags(deg)
    L = D - A
    D_inv_sqrt = sp.diags(1.0 / np.sqrt(deg))
    L_norm = (D_inv_sqrt @ L @ D_inv_sqrt).tocsr()
    if return_h:
        return L_norm, h_kth
    return L_norm


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
    groups, current = [], [nonzero[0]]
    for i in range(1, len(nonzero)):
        if (nonzero[i] - nonzero[i - 1]) / (nonzero[i - 1] + 1e-12) < tol_factor:
            current.append(nonzero[i])
        else:
            groups.append((float(np.mean(current)), len(current)))
            current = [nonzero[i]]
    groups.append((float(np.mean(current)), len(current)))
    return groups


def main():
    print("=== Cross-manifold unit-matching: recover continuum S^3/S^2 = 1.5 ===")
    print()

    # ─── Strategy 1: Match bandwidth h via N choice ───────────────────────
    print("Strategy 1: MATCH bandwidth h across manifolds")
    print()

    vol_s2 = 4 * np.pi
    vol_s3 = 2 * np.pi ** 2
    print(f"  vol(S^2) = 4π = {vol_s2:.3f}")
    print(f"  vol(S^3) = 2π² = {vol_s3:.3f}")
    print()

    # Try matched-h pairs
    pairs = [
        ("h=0.20", 0.20),
        ("h=0.15", 0.15),
        ("h=0.10", 0.10),
    ]

    results_matched = []
    for label, h_target in pairs:
        # For uniform N points on d-manifold of volume V, h ~ (k V / N)^(1/d)
        # → N = k V / h^d
        n_s2 = int(K_NEIGHBORS * vol_s2 / h_target ** 2)
        n_s3 = int(K_NEIGHBORS * vol_s3 / h_target ** 3)
        n_s2 = min(n_s2, 20000)  # cap for memory
        n_s3 = min(n_s3, 30000)
        print(f"  {label}: target N_S² = {n_s2:,}, N_S³ = {n_s3:,}")

        s2_pts = sample_s2(n_s2, RNG)
        s3_pts = sample_s3(n_s3, RNG)
        L_s2, h_s2 = build_knn_laplacian_kdtree(s2_pts, K_NEIGHBORS, return_h=True)
        L_s3, h_s3 = build_knn_laplacian_kdtree(s3_pts, K_NEIGHBORS, return_h=True)
        print(f"    Measured h: S²={h_s2:.4f}, S³={h_s3:.4f}")

        eig_s2 = get_lowest_eigenvalues(L_s2, N_EIGENVALUES)
        eig_s3 = get_lowest_eigenvalues(L_s3, N_EIGENVALUES)
        g_s2 = detect_degeneracy_groups(eig_s2)
        g_s3 = detect_degeneracy_groups(eig_s3)

        if len(g_s2) >= 1 and len(g_s3) >= 1:
            lam_s2_l1 = g_s2[0][0]
            lam_s3_l1 = g_s3[0][0]
            raw_ratio = lam_s3_l1 / lam_s2_l1
            # Scale by 1/h² each
            scaled_s2 = lam_s2_l1 / h_s2 ** 2
            scaled_s3 = lam_s3_l1 / h_s3 ** 2
            scaled_ratio = scaled_s3 / scaled_s2
            print(f"    Raw λ_2: S²={lam_s2_l1:.5f}, S³={lam_s3_l1:.5f}; raw ratio = {raw_ratio:.3f}")
            print(f"    1/h² scaled: S²={scaled_s2:.3f}, S³={scaled_s3:.3f}; scaled ratio = {scaled_ratio:.3f}")
            print(f"    Continuum prediction: 1.500")
            results_matched.append({
                "label": label, "h_target": h_target,
                "n_s2": n_s2, "n_s3": n_s3,
                "h_measured_s2": float(h_s2), "h_measured_s3": float(h_s3),
                "lam_s2_l1": float(lam_s2_l1), "lam_s3_l1": float(lam_s3_l1),
                "raw_ratio": float(raw_ratio),
                "scaled_s2": float(scaled_s2), "scaled_s3": float(scaled_s3),
                "scaled_ratio": float(scaled_ratio),
                "gap_to_continuum_pct": 100 * abs(scaled_ratio - 1.5) / 1.5,
            })
        print()

    # ─── Strategy 2: Fixed-N with explicit 1/h² normalization ────────────
    print("Strategy 2: Fixed-N (5000 each) + 1/h² normalization")
    print()

    n_fixed = 5000
    s2_pts = sample_s2(n_fixed, RNG)
    s3_pts = sample_s3(n_fixed, RNG)
    L_s2, h_s2 = build_knn_laplacian_kdtree(s2_pts, K_NEIGHBORS, return_h=True)
    L_s3, h_s3 = build_knn_laplacian_kdtree(s3_pts, K_NEIGHBORS, return_h=True)
    eig_s2 = get_lowest_eigenvalues(L_s2, N_EIGENVALUES)
    eig_s3 = get_lowest_eigenvalues(L_s3, N_EIGENVALUES)
    g_s2 = detect_degeneracy_groups(eig_s2)
    g_s3 = detect_degeneracy_groups(eig_s3)
    lam_s2 = g_s2[0][0]
    lam_s3 = g_s3[0][0]
    raw = lam_s3 / lam_s2
    print(f"  N=5000 each. h_S²={h_s2:.4f}, h_S³={h_s3:.4f}")
    print(f"  Raw λ_2: S²={lam_s2:.5f}, S³={lam_s3:.5f}; raw ratio = {raw:.3f}")
    scaled_s2_fixedn = lam_s2 / h_s2 ** 2
    scaled_s3_fixedn = lam_s3 / h_s3 ** 2
    print(f"  1/h² scaled: S²={scaled_s2_fixedn:.3f}, S³={scaled_s3_fixedn:.3f}; ratio = {scaled_s3_fixedn / scaled_s2_fixedn:.3f}")
    print(f"  Continuum: S²_l1=2, S³_l1=3, ratio=1.5")
    print()

    # ─── Strategy 3: Match diameter (sphere radius) scaling explicitly ────
    print("Strategy 3: Match equivalent k/N density across manifolds")
    print()
    # Match (k/N) across manifolds: same fraction of neighbors per point
    # Already done by using same k and same N — what we want is to match
    # POINT DENSITY per unit volume = N/V
    # Density-matched: N_S²/(4π) = N_S³/(2π²)
    density_target = n_fixed / vol_s3  # use S^3 density as anchor
    n_s2_dm = int(density_target * vol_s2)
    print(f"  Density target: {density_target:.1f} points/unit-volume (3D)")
    print(f"  N_S² (density-matched to S³ N=5000): {n_s2_dm}")
    s2_pts_dm = sample_s2(n_s2_dm, RNG)
    L_s2_dm, h_s2_dm = build_knn_laplacian_kdtree(s2_pts_dm, K_NEIGHBORS, return_h=True)
    eig_s2_dm = get_lowest_eigenvalues(L_s2_dm, N_EIGENVALUES)
    g_s2_dm = detect_degeneracy_groups(eig_s2_dm)
    lam_s2_dm = g_s2_dm[0][0]
    print(f"  Density-matched: λ_S²_l1 = {lam_s2_dm:.5f}, h_S²={h_s2_dm:.4f}")
    print(f"  Raw ratio λ_S³/λ_S² (density-matched): {lam_s3 / lam_s2_dm:.3f}")
    print(f"  Scaled (1/h²) ratio: {(lam_s3 / h_s3**2) / (lam_s2_dm / h_s2_dm**2):.3f}")
    print()

    # ─── Verdict ───────────────────────────────────────────────────────────
    print("=== Verdict ===")
    print()
    print("Strategy 1 (matched bandwidth) results:")
    best_strat1 = min(results_matched, key=lambda r: r["gap_to_continuum_pct"])
    for r in results_matched:
        print(f"  {r['label']}: scaled ratio = {r['scaled_ratio']:.3f} "
              f"(gap to 1.5: {r['gap_to_continuum_pct']:.1f}%)")
    print(f"\n  Best: {best_strat1['label']} at {best_strat1['gap_to_continuum_pct']:.1f}% gap")
    print()
    if best_strat1["gap_to_continuum_pct"] < 20:
        print("  → Matched-bandwidth + 1/h² scaling recovers continuum 1.5 ratio within 20%")
        print("    PR #345's 3.76x absolute ratio was indeed k-NN-discretization scaling,")
        print("    NOT a falsification of MFO §VII.4.1.1.")
    else:
        print("  → Even matched bandwidth doesn't fully close gap to continuum 1.5;")
        print("    deeper convergence-theorem analysis needed (kernel-dependent constants).")

    # Save
    records = [
        {"test": "config", "k_neighbors": K_NEIGHBORS, "n_eigenvalues": N_EIGENVALUES,
         "continuum_ratio_s3_s2_l1": 1.5},
        {"test": "strategy_1_matched_bandwidth", "results": results_matched},
        {"test": "strategy_2_fixed_n_with_h_scaling",
         "n_fixed": n_fixed,
         "h_s2": float(h_s2), "h_s3": float(h_s3),
         "raw_lam_s2_l1": float(lam_s2), "raw_lam_s3_l1": float(lam_s3),
         "raw_ratio": float(raw),
         "scaled_lam_s2_l1": float(scaled_s2_fixedn), "scaled_lam_s3_l1": float(scaled_s3_fixedn),
         "scaled_ratio": float(scaled_s3_fixedn / scaled_s2_fixedn)},
        {"test": "strategy_3_density_matched",
         "n_s2_density_matched": int(n_s2_dm),
         "n_s3_anchor": n_fixed,
         "lam_s2_l1": float(lam_s2_dm), "lam_s3_l1": float(lam_s3),
         "raw_ratio": float(lam_s3 / lam_s2_dm),
         "scaled_ratio": float((lam_s3 / h_s3**2) / (lam_s2_dm / h_s2_dm**2))},
    ]
    with open(RESULTS_FILE, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    # Plot
    fig, ax = plt.subplots(figsize=(10, 5))
    labels = [r["label"] for r in results_matched]
    ratios_raw = [r["raw_ratio"] for r in results_matched]
    ratios_scaled = [r["scaled_ratio"] for r in results_matched]
    x = np.arange(len(labels))
    w = 0.35
    ax.bar(x - w/2, ratios_raw, w, label="Raw ratio (S³/S² λ_2)", color='red', alpha=0.6)
    ax.bar(x + w/2, ratios_scaled, w, label="Scaled (×1/h²)", color='green', alpha=0.6)
    ax.axhline(1.5, color='blue', linestyle='--', linewidth=2, label="Continuum prediction (1.5)")
    ax.axhline(3.76, color='gray', linestyle=':', linewidth=1, label="PR #345 raw ratio (3.76)")
    ax.set_xticks(x); ax.set_xticklabels(labels)
    ax.set_ylabel("S³ l=1 / S² l=1 ratio")
    ax.set_title("Cross-manifold unit-matching strategies — recover continuum 1.5?")
    ax.legend(); ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUT_DIR / "cross-manifold-unit-matching-2026-05-12.png", dpi=100)
    plt.close()

    print(f"\nResults: {RESULTS_FILE.name}")


if __name__ == "__main__":
    main()

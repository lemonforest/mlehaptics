"""
High-resolution k-NN on S^3 — quantitative MFO §VII.4.1.1 test (2026-05-12).

Stacked on PR #344. PR #344 found that Wilson-phase-on-S² constructs
test monopole physics, not Hopf-bundle S^3. The RIGHT test of MFO
§VII.4.1.1 is: sample S^3 uniformly + k-NN graph + compare to S^2.

PR #331 Experiment 3 did this with 200 samples and got:
- λ_2(S^3) = 1.21
- λ_2(S^2) = 0.51
- Ratio 2.37 (continuum predicts l(l+2)/l(l+1) = 3/2 = 1.5)

This PR does it with 2000 samples per manifold + analyzes MULTIPLE
eigenvalues, not just λ_2. Continuum predictions for first several modes:

| l | l(l+1) S² | l(l+2) S³ | S³/S² ratio |
|---|-----------|-----------|-------------|
| 1 | 2         | 3         | 1.50        |
| 2 | 6         | 8         | 1.33        |
| 3 | 12        | 15        | 1.25        |

Higher modes converge to ratio 1, low modes are most discriminating.

Reproduce: `python -X utf8 docs/srmech/notes/knn_s3_high_resolution_script.py`
"""

import time
import json
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
import scipy.linalg
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

SEED = 20260512
RNG = np.random.default_rng(SEED)

N_SAMPLES = 2000
K_NEIGHBORS = 20
N_EIGENVALUES = 20

OUT_DIR = Path(__file__).parent
RESULTS_FILE = OUT_DIR / "knn-s3-high-resolution-per-test-2026-05-12.ndjson"


def sample_s2(n, rng):
    """Uniform samples on S²: 3D unit vectors via normal distribution."""
    pts = rng.standard_normal((n, 3))
    pts /= np.linalg.norm(pts, axis=1, keepdims=True)
    return pts


def sample_s3(n, rng):
    """Uniform samples on S³: 4D unit vectors via normal distribution."""
    pts = rng.standard_normal((n, 4))
    pts /= np.linalg.norm(pts, axis=1, keepdims=True)
    return pts


def hopf_map(s3_pts):
    """Hopf map S³ → S²: (a, b, c, d) → (2(ad+bc), 2(bd-ac), a²+b²-c²-d²)."""
    a, b, c, d = s3_pts[:, 0], s3_pts[:, 1], s3_pts[:, 2], s3_pts[:, 3]
    x = 2 * (a * d + b * c)
    y = 2 * (b * d - a * c)
    z = a * a + b * b - c * c - d * d
    return np.stack([x, y, z], axis=1)


def build_knn_laplacian(points, k, normalize=True):
    """Build symmetric k-NN graph Laplacian."""
    n = points.shape[0]
    # Pairwise distances (memory: n² × 4 bytes for float32)
    dists = np.linalg.norm(points[:, None, :] - points[None, :, :], axis=2)
    np.fill_diagonal(dists, np.inf)
    # k nearest neighbors per point
    nn_idx = np.argpartition(dists, k, axis=1)[:, :k]
    # Build symmetric adjacency
    rows, cols = [], []
    for i in range(n):
        for j in nn_idx[i]:
            rows.append(i); cols.append(int(j))
    A = sp.coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(n, n))
    A = ((A + A.T) > 0).astype(float)  # symmetric
    D = sp.diags(np.asarray(A.sum(axis=1)).ravel())
    L = D - A
    if normalize:
        # Normalized Laplacian: D^(-1/2) L D^(-1/2)
        D_inv_sqrt = sp.diags(1.0 / np.sqrt(np.asarray(A.sum(axis=1)).ravel()))
        L = D_inv_sqrt @ L @ D_inv_sqrt
    return L.tocsr()


def get_lowest_eigenvalues(L, k_eig=20):
    """Get lowest k eigenvalues."""
    try:
        eigvals, _ = spla.eigsh(L, k=k_eig + 1, sigma=-1e-6, which="LM")
    except Exception:
        eigvals, _ = spla.eigsh(L, k=k_eig + 1, which="SM")
    return np.sort(eigvals.real)


def main():
    print("=== High-resolution k-NN on S³ — quantitative MFO §VII.4.1.1 test ===")
    print(f"Samples: {N_SAMPLES} per manifold; k-NN k = {K_NEIGHBORS}; eigenvalues: {N_EIGENVALUES}")
    print()

    # Sample S² and S³ uniformly
    print("[1] Sampling...")
    s2_pts = sample_s2(N_SAMPLES, RNG)
    s3_pts = sample_s3(N_SAMPLES, RNG)
    s2_via_hopf = hopf_map(s3_pts)  # Hopf-projected S³ → S²
    print(f"  S² direct samples: {s2_pts.shape}")
    print(f"  S³ samples: {s3_pts.shape}")
    print(f"  S² via Hopf from S³: {s2_via_hopf.shape}")
    print()

    # Build Laplacians
    print("[2] Building k-NN Laplacians (normalized)...")
    t0 = time.perf_counter()
    L_s2 = build_knn_laplacian(s2_pts, K_NEIGHBORS)
    L_s3 = build_knn_laplacian(s3_pts, K_NEIGHBORS)
    L_s2_hopf = build_knn_laplacian(s2_via_hopf, K_NEIGHBORS)
    t_build = time.perf_counter() - t0
    print(f"  Built 3 Laplacians in {1000*t_build:.0f} ms")
    print()

    # Eigenvalues
    print("[3] Computing lowest eigenvalues...")
    t0 = time.perf_counter()
    eigvals_s2 = get_lowest_eigenvalues(L_s2, N_EIGENVALUES)
    eigvals_s3 = get_lowest_eigenvalues(L_s3, N_EIGENVALUES)
    eigvals_s2_hopf = get_lowest_eigenvalues(L_s2_hopf, N_EIGENVALUES)
    t_eig = time.perf_counter() - t0
    print(f"  Eigenvalues computed in {1000*t_eig:.0f} ms")
    print()

    # Compare to continuum prediction
    print("=== Continuum vs measured eigenvalues ===")
    print(f"  Continuum S²: 0, 2, 2, 2, 6, 6, 6, 6, 6, 12, ...  (degeneracies 1, 3, 5, 7, ...)")
    print(f"  Continuum S³: 0, 3, 3, 3, 3, 8, 8, 8, 8, 8, 8, 8, 8, 8, 15, ...")
    print(f"                                          (degeneracies (l+1)² → 1, 4, 9, 16, ...)")
    print()
    print(f"  Measured S² eigenvalues (first {min(N_EIGENVALUES, len(eigvals_s2))}):")
    for i, e in enumerate(eigvals_s2[:N_EIGENVALUES]):
        print(f"    [{i:2d}] {e:.5f}")
    print()
    print(f"  Measured S³ eigenvalues (first {min(N_EIGENVALUES, len(eigvals_s3))}):")
    for i, e in enumerate(eigvals_s3[:N_EIGENVALUES]):
        print(f"    [{i:2d}] {e:.5f}")
    print()

    # Key MFO test: ratio of "l=1 mode" eigenvalues
    # Skip the kernel (eigenvalue 0); the first 3 non-zero on S² are l=1 (m=-1,0,+1)
    # First 4 non-zero on S³ are l=1
    # Use the AVERAGE of first 3 non-zero on S² and first 4 non-zero on S³
    s2_nonzero = eigvals_s2[1:]  # skip kernel
    s3_nonzero = eigvals_s3[1:]

    # l=1 mode is degeneracy 3 on S², 4 on S³ (since S³ has (l+1)²-fold degeneracy)
    l1_s2_avg = np.mean(s2_nonzero[:3])
    l1_s3_avg = np.mean(s3_nonzero[:4])

    # l=2 mode: deg 5 on S², 9 on S³
    l2_s2_avg = np.mean(s2_nonzero[3:8])
    l2_s3_avg = np.mean(s3_nonzero[4:13])

    print("=== MFO §VII.4.1.1 quantitative test ===")
    print(f"  l=1 averaged: S² = {l1_s2_avg:.5f}, S³ = {l1_s3_avg:.5f}")
    print(f"    Ratio S³/S² (continuum 3/2 = 1.500): {l1_s3_avg / l1_s2_avg:.4f}")
    print()
    print(f"  l=2 averaged: S² = {l2_s2_avg:.5f}, S³ = {l2_s3_avg:.5f}")
    print(f"    Ratio S³/S² (continuum 8/6 = 1.333): {l2_s3_avg / l2_s2_avg:.4f}")
    print()

    # Now ALSO compare normalized eigenvalues (rescale so l=1 average is 1)
    s2_normalized = s2_nonzero / l1_s2_avg
    s3_normalized = s3_nonzero / l1_s3_avg
    print(f"  Normalized first few eigenvalues (each manifold scaled so l=1 avg = 1):")
    print(f"    S² normalized: {[f'{e:.3f}' for e in s2_normalized[:6]]}")
    print(f"    S³ normalized: {[f'{e:.3f}' for e in s3_normalized[:6]]}")
    print()

    # Verdict
    print("=== Verdict ===")
    ratio_l1 = l1_s3_avg / l1_s2_avg
    if abs(ratio_l1 - 1.5) < 0.2:
        print(f"  l=1 ratio S³/S² = {ratio_l1:.3f} ≈ continuum 1.5 — MFO §VII.4.1.1 VALIDATED quantitatively")
    elif 1.0 < ratio_l1 < 3.0:
        print(f"  l=1 ratio S³/S² = {ratio_l1:.3f}, in same direction as continuum 1.5 but quantitative gap")
        print(f"  At {N_SAMPLES} samples, k-NN-Laplacian discretization scaling persists")
    else:
        print(f"  l=1 ratio S³/S² = {ratio_l1:.3f} — unexpected")

    # Save
    records = [
        {"test": "config", "n_samples": N_SAMPLES, "k_neighbors": K_NEIGHBORS,
         "n_eigenvalues": N_EIGENVALUES},
        {"test": "s2_eigenvalues", "values": eigvals_s2[:N_EIGENVALUES].tolist()},
        {"test": "s3_eigenvalues", "values": eigvals_s3[:N_EIGENVALUES].tolist()},
        {"test": "l_1_averaged_ratio",
         "l1_s2_avg": float(l1_s2_avg), "l1_s3_avg": float(l1_s3_avg),
         "ratio_s3_to_s2": float(ratio_l1),
         "continuum_prediction": 1.5},
        {"test": "l_2_averaged_ratio",
         "l2_s2_avg": float(l2_s2_avg), "l2_s3_avg": float(l2_s3_avg),
         "ratio_s3_to_s2": float(l2_s3_avg / l2_s2_avg),
         "continuum_prediction": 1.333},
    ]
    with open(RESULTS_FILE, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    # Plot
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    # Eigenvalue comparison
    indices = np.arange(N_EIGENVALUES)
    axes[0].plot(indices, eigvals_s2[:N_EIGENVALUES], "b-o", label=f"S² (N={N_SAMPLES})")
    axes[0].plot(indices, eigvals_s3[:N_EIGENVALUES], "r-s", label=f"S³ (N={N_SAMPLES})")
    axes[0].set_xlabel("Eigenvalue index")
    axes[0].set_ylabel("Eigenvalue")
    axes[0].set_title("k-NN Laplacian spectra")
    axes[0].legend(); axes[0].grid(alpha=0.3)

    # Normalized comparison
    axes[1].plot(indices[1:7], s2_normalized[:6], "b-o", label="S² (scaled to l=1 avg)")
    axes[1].plot(indices[1:7], s3_normalized[:6], "r-s", label="S³ (scaled to l=1 avg)")
    # Continuum predictions
    s2_continuum = [2, 2, 2, 6, 6, 6]  # 3 l=1 + 5 l=2 ... first 6 modes
    s3_continuum = [3, 3, 3, 3, 8, 8]
    axes[1].plot(indices[1:7], [c / 2 for c in s2_continuum], "b--", alpha=0.5, label="S² continuum (l(l+1)/2)")
    axes[1].plot(indices[1:7], [c / 3 for c in s3_continuum], "r--", alpha=0.5, label="S³ continuum (l(l+2)/3)")
    axes[1].set_xlabel("Eigenvalue index")
    axes[1].set_ylabel("Eigenvalue / l=1 average")
    axes[1].set_title("Normalized: measured vs continuum")
    axes[1].legend(); axes[1].grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUT_DIR / "knn-s3-high-resolution-2026-05-12.png", dpi=100)
    plt.close()

    print()
    print(f"Results: {RESULTS_FILE.name}")
    print(f"Plot:    knn-s3-high-resolution-2026-05-12.png")


if __name__ == "__main__":
    main()

"""
Hopf-coset construction — explicit fibre discretization (2026-05-12).

Extension to PR #344. PR #344 found that Wilson-phase-on-S^2 constructs
test monopole physics, not the Hopf bundle. PR #344 flagged "Hopf-coset
construction or higher-resolution k-NN on S^3" as the right next path.
The k-NN higher-res was done in PR #345 (2000 samples). This PR does
the Hopf-coset construction.

Construction:
- Sample n_base points uniformly on S^2 (Fibonacci spiral)
- For each base point B, generate n_fibre points along the EXPLICIT Hopf
  fibre over B via quaternion multiplication
- Total: n_base × n_fibre points on S^3, arranged in fibre-respecting
  structure (NOT random sampling)
- Edges:
  - Within-fibre: connect adjacent fibre indices (S^1 topology per fibre)
  - Across-base: connect via base-k-NN with fibre-offset matching

Key difference from PR #345's k-NN-on-uniform-S^3:
- PR #345 samples uniformly and lets k-NN discover local structure
- This PR samples ALONG fibres explicitly, so the graph respects bundle
  structure by construction
- Expectation: Hopf-coset construction should give SHARPER (l+1)^2
  degeneracies for S^3 modes since the fibre direction is exactly resolved

Reproduce: `python -X utf8 docs/srmech/notes/hopf_coset_construction_script.py`
Deterministic seed 20260512.
"""

import time
import json
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

SEED = 20260512
RNG = np.random.default_rng(SEED)

N_BASE = 100
N_FIBRE = 20
K_NEIGHBORS = 12
N_EIGENVALUES = 25

OUT_DIR = Path(__file__).parent
RESULTS_FILE = OUT_DIR / "hopf-coset-construction-per-test-2026-05-12.ndjson"


def fibonacci_sphere(n):
    """Fibonacci-spiral uniform sampling on S^2. Returns (n, 3) array."""
    indices = np.arange(0, n, dtype=float) + 0.5
    phi = np.arccos(1 - 2 * indices / n)          # latitude
    theta = np.pi * (1 + 5 ** 0.5) * indices       # longitude (golden angle)
    x = np.sin(phi) * np.cos(theta)
    y = np.sin(phi) * np.sin(theta)
    z = np.cos(phi)
    return np.stack([x, y, z], axis=1)


def s2_to_quaternion_preimage(b_pts):
    """For each base point B on S^2, compute one Hopf preimage q_0 in S^3.

    Using the parameterization: q_0 = (cos(alpha/2), 0,
                                         sin(alpha/2)*cos(-beta),
                                         sin(alpha/2)*sin(-beta))
    where (alpha, beta) are spherical coords of B.

    Returns (n, 4) array of quaternions on S^3.
    """
    b = b_pts / np.linalg.norm(b_pts, axis=1, keepdims=True)
    bz = b[:, 2]
    alpha = np.arccos(np.clip(bz, -1, 1))
    beta = np.arctan2(b[:, 1], b[:, 0])
    half_alpha = alpha / 2.0
    half_beta = beta / 2.0
    # Standard Hopf preimage (one of many gauge choices)
    a = np.cos(half_alpha) * np.cos(half_beta)
    b1 = np.cos(half_alpha) * np.sin(half_beta)
    c = np.sin(half_alpha) * np.cos(-half_beta)
    d = np.sin(half_alpha) * np.sin(-half_beta)
    return np.stack([a, b1, c, d], axis=1)


def quaternion_multiply(p, q):
    """Hamilton product: p * q for unit quaternions (a, b, c, d)."""
    p0, p1, p2, p3 = p[..., 0], p[..., 1], p[..., 2], p[..., 3]
    q0, q1, q2, q3 = q[..., 0], q[..., 1], q[..., 2], q[..., 3]
    return np.stack([
        p0 * q0 - p1 * q1 - p2 * q2 - p3 * q3,
        p0 * q1 + p1 * q0 + p2 * q3 - p3 * q2,
        p0 * q2 - p1 * q3 + p2 * q0 + p3 * q1,
        p0 * q3 + p1 * q2 - p2 * q1 + p3 * q0,
    ], axis=-1)


def hopf_fibre_points(q0, n_fibre):
    """Generate n_fibre evenly-spaced points along the Hopf fibre over q0.

    Fibre parameterization: q(psi) = q0 * (cos(psi/2) + i*sin(psi/2)),
    psi in [0, 4*pi). The 4*pi range gives a full S^1 fibre under Hopf.

    Returns (n_fibre, 4) array.
    """
    psis = np.linspace(0, 4 * np.pi, n_fibre, endpoint=False)
    cos_half = np.cos(psis / 2.0)
    sin_half = np.sin(psis / 2.0)
    # Right-multiplication by (cos(psi/2), sin(psi/2), 0, 0) -- i.e., u = exp(i*psi/2)
    u = np.stack([cos_half, sin_half, np.zeros_like(psis), np.zeros_like(psis)], axis=1)
    # Broadcast q0 to match
    q0_b = np.broadcast_to(q0, (n_fibre, 4))
    return quaternion_multiply(q0_b, u)


def hopf_map(s3_pts):
    """Hopf S^3 -> S^2: (a, b, c, d) -> (2(ad+bc), 2(bd-ac), a^2+b^2-c^2-d^2)."""
    a, b, c, d = s3_pts[..., 0], s3_pts[..., 1], s3_pts[..., 2], s3_pts[..., 3]
    return np.stack([
        2 * (a * d + b * c),
        2 * (b * d - a * c),
        a * a + b * b - c * c - d * d,
    ], axis=-1)


def build_hopf_coset_graph(s3_pts, n_base, n_fibre, k_neighbors):
    """
    Build graph for Hopf-coset S^3 with explicit fibre structure.

    Vertices indexed as (i, k) where i in [0, n_base), k in [0, n_fibre).
    Vertex id: vid = i * n_fibre + k.

    Edges:
    - Within-fibre: (i, k) - (i, (k+1) mod n_fibre)
    - Cross-base: (i, k) - (j, k') for each base-k-NN j, where k' minimises
      4D Euclidean distance to (i, k) on S^3.
    """
    n = n_base * n_fibre
    s3_grid = s3_pts.reshape(n_base, n_fibre, 4)

    # Within-fibre edges
    rows, cols = [], []
    for i in range(n_base):
        for k in range(n_fibre):
            kp = (k + 1) % n_fibre
            rows.append(i * n_fibre + k); cols.append(i * n_fibre + kp)

    # Base-k-NN: compute on S^2 base centers
    base_pts = hopf_map(s3_grid[:, 0, :])  # use k=0 fibre point for base
    base_dists = np.linalg.norm(base_pts[:, None, :] - base_pts[None, :, :], axis=2)
    np.fill_diagonal(base_dists, np.inf)
    nn_idx = np.argpartition(base_dists, k_neighbors, axis=1)[:, :k_neighbors]

    # Cross-base edges with fibre matching
    for i in range(n_base):
        for j in nn_idx[i]:
            j = int(j)
            # For each (i, k), find k' minimising 4D distance to (j, k')
            d_4d = np.linalg.norm(
                s3_grid[i, :, None, :] - s3_grid[j, None, :, :], axis=2
            )  # shape (n_fibre, n_fibre)
            # Sparse: just connect to argmin per row k
            k_matches = np.argmin(d_4d, axis=1)
            for k in range(n_fibre):
                rows.append(i * n_fibre + k)
                cols.append(j * n_fibre + int(k_matches[k]))

    A = sp.coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(n, n))
    A = ((A + A.T) > 0).astype(float)
    D = sp.diags(np.asarray(A.sum(axis=1)).ravel())
    L = D - A
    D_inv_sqrt = sp.diags(1.0 / np.sqrt(np.asarray(A.sum(axis=1)).ravel()))
    L_norm = D_inv_sqrt @ L @ D_inv_sqrt
    return L_norm.tocsr(), A.tocsr()


def build_uniform_knn_laplacian(points, k):
    """Same as PR #345: uniform k-NN normalized Laplacian, for comparison."""
    n = points.shape[0]
    dists = np.linalg.norm(points[:, None, :] - points[None, :, :], axis=2)
    np.fill_diagonal(dists, np.inf)
    nn_idx = np.argpartition(dists, k, axis=1)[:, :k]
    rows, cols = [], []
    for i in range(n):
        for j in nn_idx[i]:
            rows.append(i); cols.append(int(j))
    A = sp.coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(n, n))
    A = ((A + A.T) > 0).astype(float)
    D = sp.diags(np.asarray(A.sum(axis=1)).ravel())
    L = D - A
    D_inv_sqrt = sp.diags(1.0 / np.sqrt(np.asarray(A.sum(axis=1)).ravel()))
    return (D_inv_sqrt @ L @ D_inv_sqrt).tocsr()


def get_lowest_eigenvalues(L, k_eig):
    try:
        eigvals, _ = spla.eigsh(L, k=k_eig + 1, sigma=-1e-6, which="LM")
    except Exception:
        eigvals, _ = spla.eigsh(L, k=k_eig + 1, which="SM")
    return np.sort(eigvals.real)


def detect_degeneracy_groups(eigvals, tol_factor=0.1):
    """Group eigenvalues into clusters by relative gap. Returns list of (val, count)."""
    nonzero = eigvals[eigvals > 1e-6]
    if len(nonzero) == 0:
        return []
    groups = []
    current_group = [nonzero[0]]
    for i in range(1, len(nonzero)):
        gap_rel = (nonzero[i] - nonzero[i - 1]) / (nonzero[i - 1] + 1e-12)
        if gap_rel < tol_factor:
            current_group.append(nonzero[i])
        else:
            groups.append((float(np.mean(current_group)), len(current_group)))
            current_group = [nonzero[i]]
    groups.append((float(np.mean(current_group)), len(current_group)))
    return groups


def main():
    print("=== Hopf-coset construction — explicit fibre on S^3 ===")
    print(f"Seed: {SEED}; n_base = {N_BASE}; n_fibre = {N_FIBRE}; total = {N_BASE * N_FIBRE}")
    print()

    # ─── Build Hopf-coset S^3 sample ───────────────────────────────────────
    print("[1] Building explicit Hopf-fibred S^3 sample...")
    t0 = time.perf_counter()
    base_pts = fibonacci_sphere(N_BASE)
    q0_array = s2_to_quaternion_preimage(base_pts)
    # Build full S^3 sample as n_base x n_fibre quaternions
    s3_pts = np.empty((N_BASE, N_FIBRE, 4))
    for i in range(N_BASE):
        s3_pts[i] = hopf_fibre_points(q0_array[i], N_FIBRE)
    s3_flat = s3_pts.reshape(-1, 4)
    t_sample = time.perf_counter() - t0
    print(f"    Built {N_BASE * N_FIBRE} points in {1000*t_sample:.0f} ms")
    print(f"    Unit-norm check: max |‖q‖ - 1| = {abs(np.linalg.norm(s3_flat, axis=1) - 1).max():.2e}")

    # Verify Hopf projection back to base
    base_check = hopf_map(s3_flat).reshape(N_BASE, N_FIBRE, 3)
    base_variance = np.std(base_check, axis=1).max()
    print(f"    Hopf-map fibre→base variance (should be ~0): {base_variance:.4e}")
    print()

    # ─── Build Hopf-coset graph Laplacian ──────────────────────────────────
    print("[2] Building Hopf-coset graph Laplacian...")
    t0 = time.perf_counter()
    L_hopf, A_hopf = build_hopf_coset_graph(s3_flat, N_BASE, N_FIBRE, K_NEIGHBORS)
    t_build = time.perf_counter() - t0
    n_edges_hopf = int(A_hopf.nnz / 2)
    print(f"    Built in {1000*t_build:.0f} ms; {n_edges_hopf} undirected edges")
    print()

    # ─── Build uniform-k-NN-on-S^3 comparison ──────────────────────────────
    print("[3] Building uniform k-NN comparison (PR #345 style on same sample)...")
    t0 = time.perf_counter()
    # Sample uniformly on S^3 with same point count
    s3_uniform = RNG.standard_normal((N_BASE * N_FIBRE, 4))
    s3_uniform /= np.linalg.norm(s3_uniform, axis=1, keepdims=True)
    L_unif = build_uniform_knn_laplacian(s3_uniform, K_NEIGHBORS)
    t_unif = time.perf_counter() - t0
    print(f"    Built in {1000*t_unif:.0f} ms")
    print()

    # ─── Compute spectra ───────────────────────────────────────────────────
    print("[4] Computing lowest eigenvalues...")
    t0 = time.perf_counter()
    eigvals_hopf = get_lowest_eigenvalues(L_hopf, N_EIGENVALUES)
    eigvals_unif = get_lowest_eigenvalues(L_unif, N_EIGENVALUES)
    t_eig = time.perf_counter() - t0
    print(f"    Computed in {1000*t_eig:.0f} ms")
    print()

    # ─── Display + degeneracy analysis ─────────────────────────────────────
    print("=== Hopf-coset eigenvalues (top 20) ===")
    for i, e in enumerate(eigvals_hopf[:20]):
        print(f"    [{i:2d}] {e:.5f}")
    print()
    print("=== Uniform-k-NN eigenvalues (top 20, for comparison) ===")
    for i, e in enumerate(eigvals_unif[:20]):
        print(f"    [{i:2d}] {e:.5f}")
    print()

    # Detect degeneracy groups
    groups_hopf = detect_degeneracy_groups(eigvals_hopf, tol_factor=0.15)
    groups_unif = detect_degeneracy_groups(eigvals_unif, tol_factor=0.15)
    print("=== Degeneracy detection (tol 15%) ===")
    print(f"\n  Hopf-coset construction:")
    for g_idx, (val, count) in enumerate(groups_hopf[:5]):
        l_predicted = g_idx + 1
        deg_predicted_s3 = (l_predicted + 1) ** 2
        match_s3 = "MATCH S^3" if count == deg_predicted_s3 else f"(continuum S^3 l={l_predicted}: {deg_predicted_s3})"
        print(f"    l={g_idx+1}: {count} modes near eigenvalue {val:.4f}  {match_s3}")

    print(f"\n  Uniform k-NN (control):")
    for g_idx, (val, count) in enumerate(groups_unif[:5]):
        l_predicted = g_idx + 1
        deg_predicted_s3 = (l_predicted + 1) ** 2
        match_s3 = "MATCH S^3" if count == deg_predicted_s3 else f"(continuum S^3 l={l_predicted}: {deg_predicted_s3})"
        print(f"    l={g_idx+1}: {count} modes near eigenvalue {val:.4f}  {match_s3}")
    print()

    # MFO mode-ratio analysis
    print("=== MFO §VII.4.1.1 mode-ratio check ===")
    if len(groups_hopf) >= 2:
        l1_hopf, l2_hopf = groups_hopf[0][0], groups_hopf[1][0]
        ratio_hopf = l2_hopf / l1_hopf
        print(f"  Hopf-coset l=2/l=1: {ratio_hopf:.3f}  (continuum S^3: 8/3 = 2.667)")
    if len(groups_unif) >= 2:
        l1_unif, l2_unif = groups_unif[0][0], groups_unif[1][0]
        ratio_unif = l2_unif / l1_unif
        print(f"  Uniform k-NN l=2/l=1: {ratio_unif:.3f}  (continuum S^3: 8/3 = 2.667)")
    print()

    # ─── Verdict ──────────────────────────────────────────────────────────
    print("=== Verdict ===")
    expected_degs = [4, 9, 16, 25, 36]
    hopf_match_count = sum(1 for i, (_, c) in enumerate(groups_hopf[:5]) if c == expected_degs[i])
    unif_match_count = sum(1 for i, (_, c) in enumerate(groups_unif[:5]) if c == expected_degs[i])
    print(f"  Hopf-coset matched continuum S^3 degeneracy {hopf_match_count}/5 mode groups")
    print(f"  Uniform k-NN matched continuum S^3 degeneracy {unif_match_count}/5 mode groups")
    if hopf_match_count > unif_match_count:
        print(f"  → Hopf-coset construction is SHARPER for S^3 degeneracy detection")
    elif hopf_match_count == unif_match_count:
        print(f"  → Hopf-coset and uniform k-NN are comparable")
    else:
        print(f"  → Uniform k-NN actually performs better (Hopf-coset may have artifacts)")

    # Save
    records = [
        {"test": "config", "n_base": N_BASE, "n_fibre": N_FIBRE,
         "total_points": N_BASE * N_FIBRE, "k_neighbors": K_NEIGHBORS,
         "n_edges_hopf": n_edges_hopf},
        {"test": "hopf_coset_eigenvalues",
         "values": [float(e) for e in eigvals_hopf[:N_EIGENVALUES]]},
        {"test": "uniform_knn_eigenvalues",
         "values": [float(e) for e in eigvals_unif[:N_EIGENVALUES]]},
        {"test": "hopf_coset_degeneracy_groups",
         "groups": [[float(v), int(c)] for v, c in groups_hopf]},
        {"test": "uniform_knn_degeneracy_groups",
         "groups": [[float(v), int(c)] for v, c in groups_unif]},
        {"test": "mfo_mode_ratio_check",
         "hopf_l2_over_l1": float(groups_hopf[1][0] / groups_hopf[0][0]) if len(groups_hopf) >= 2 else None,
         "uniform_l2_over_l1": float(groups_unif[1][0] / groups_unif[0][0]) if len(groups_unif) >= 2 else None,
         "continuum_s3_prediction": 8 / 3},
        {"test": "degeneracy_match_count_vs_continuum_s3",
         "hopf_match_count": int(hopf_match_count),
         "uniform_match_count": int(unif_match_count),
         "expected_degeneracies": expected_degs},
    ]
    with open(RESULTS_FILE, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    # Plot
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    indices = np.arange(min(N_EIGENVALUES, len(eigvals_hopf)))
    axes[0].plot(indices, eigvals_hopf[:len(indices)], "g-o", label="Hopf-coset (explicit fibres)")
    axes[0].plot(indices, eigvals_unif[:len(indices)], "b-s", label="Uniform k-NN (PR #345 style)")
    axes[0].set_xlabel("Eigenvalue index"); axes[0].set_ylabel("Eigenvalue")
    axes[0].set_title("Lowest 20 eigenvalues — Hopf-coset vs uniform k-NN")
    axes[0].legend(); axes[0].grid(alpha=0.3)

    # Normalized to l=1 average
    if len(groups_hopf) >= 1 and len(groups_unif) >= 1:
        norm_hopf = eigvals_hopf[1:] / groups_hopf[0][0]
        norm_unif = eigvals_unif[1:] / groups_unif[0][0]
        axes[1].plot(np.arange(len(norm_hopf[:14])), norm_hopf[:14], "g-o", label="Hopf-coset (normalized)")
        axes[1].plot(np.arange(len(norm_unif[:14])), norm_unif[:14], "b-s", label="Uniform k-NN (normalized)")
        axes[1].axhline(1.0, color="gray", linestyle="--", alpha=0.5, label="l=1")
        axes[1].axhline(8/3, color="green", linestyle="--", alpha=0.5, label="l=2 continuum (8/3)")
        axes[1].axhline(15/3, color="red", linestyle="--", alpha=0.5, label="l=3 continuum (15/3)")
        axes[1].set_xlabel("Non-zero eigenvalue index"); axes[1].set_ylabel("Eigenvalue / l=1 avg")
        axes[1].set_title("Normalized spectra vs continuum S^3 predictions")
        axes[1].legend(fontsize=8); axes[1].grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUT_DIR / "hopf-coset-construction-2026-05-12.png", dpi=100)
    plt.close()

    print()
    print(f"Results: {RESULTS_FILE.name}")
    print(f"Plot:    hopf-coset-construction-2026-05-12.png")


if __name__ == "__main__":
    main()

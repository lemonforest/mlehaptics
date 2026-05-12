"""
Berger sphere with full Riemannian metric — interpolating S^2 ↔ S^3 (2026-05-12).

PR #345 future-work item. Berger sphere is S^3 with one-parameter family
of metrics:
  ds²_α = ds²_base(S²) + α² · ds²_fibre(S¹)

- α = 1: round S^3
- α → 0: collapse to S^2 (fibre shrinks to zero)
- α > 1: stretched fibre (different limit)

We sample uniformly on S^3 (4D unit vectors), then for each α compute
Berger-metric pairwise distances. The fibre direction at point p is the
quaternion multiplication direction i·p (the U(1) orbit's tangent).

Strategy:
1. Sample N points on S^3 uniformly
2. Find Euclidean k-NN for connectivity candidates
3. For each k-NN pair, compute Berger-distance for each α via tangent
   projection split (base + fibre)
4. Build weighted Laplacian per α
5. Compute spectrum, compare to continuum S^2 (α=0 limit) and S^3 (α=1)

Reproduce: `python -X utf8 docs/srmech/notes/berger_sphere_metric_script.py`
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

N_SAMPLES = 3000
K_NEIGHBORS = 20
N_EIGENVALUES = 25
ALPHAS = [0.05, 0.2, 0.5, 1.0, 2.0]

OUT_DIR = Path(__file__).parent
RESULTS_FILE = OUT_DIR / "berger-sphere-metric-per-test-2026-05-12.ndjson"


def sample_s3(n, rng):
    pts = rng.standard_normal((n, 4))
    pts /= np.linalg.norm(pts, axis=1, keepdims=True)
    return pts


def fibre_direction(p):
    """At p = (a, b, c, d), the U(1) fibre tangent is i·p (quaternion mult)."""
    a, b, c, d = p
    return np.array([-b, a, -d, c])  # left-quaternion-multiplication by i


def berger_distance(p, q, alpha):
    """Berger-metric distance between two S^3 points p, q for fibre scale α."""
    delta = q - p
    f_p = fibre_direction(p)
    f_p_norm = f_p / (np.linalg.norm(f_p) + 1e-12)
    delta_fibre_mag = np.dot(delta, f_p_norm)
    delta_fibre = delta_fibre_mag * f_p_norm
    delta_base = delta - delta_fibre
    return np.sqrt(np.sum(delta_base ** 2) + alpha ** 2 * delta_fibre_mag ** 2)


def build_berger_laplacian(points, k_neighbors, alpha):
    """k-NN graph using Berger-metric distances; normalized Laplacian."""
    n = points.shape[0]
    # Find Euclidean k-NN candidates (over-sample to allow Berger re-ranking)
    tree = scipy.spatial.cKDTree(points)
    _, nn_idx = tree.query(points, k=int(k_neighbors * 2) + 1)  # 2x for Berger re-rank
    nn_idx = nn_idx[:, 1:]  # drop self

    # Compute Berger distances per k-NN pair, then re-rank to keep k closest
    rows, cols, weights = [], [], []
    for i in range(n):
        p_i = points[i]
        d_berger = np.array([berger_distance(p_i, points[j], alpha) for j in nn_idx[i]])
        top_k = np.argpartition(d_berger, k_neighbors)[:k_neighbors]
        for idx in top_k:
            j = int(nn_idx[i, idx])
            rows.append(i); cols.append(j)
            weights.append(1.0 / (d_berger[idx] + 1e-9))

    A = sp.coo_matrix((weights, (rows, cols)), shape=(n, n))
    A = (A + A.T) / 2  # symmetrize
    # Apply binary threshold (mean weight) for cleaner spectrum
    avg_w = A.data.mean()
    A.data = (A.data > avg_w * 0.5).astype(float)
    A.eliminate_zeros()
    deg = np.asarray(A.sum(axis=1)).ravel()
    deg = np.maximum(deg, 1e-9)
    D_inv_sqrt = sp.diags(1.0 / np.sqrt(deg))
    L = sp.diags(deg) - A
    return (D_inv_sqrt @ L @ D_inv_sqrt).tocsr()


def get_lowest_eigenvalues(L, k_eig):
    try:
        eigvals, _ = spla.eigsh(L, k=k_eig + 1, sigma=-1e-6, which="LM")
    except Exception:
        eigvals, _ = spla.eigsh(L, k=k_eig + 1, which="SM")
    return np.sort(eigvals.real)


def detect_degeneracy_groups(eigvals, tol_factor=0.10):
    nonzero = eigvals[eigvals > 1e-6]
    if len(nonzero) == 0: return []
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
    print("=== Berger sphere — interpolating S^2 ↔ S^3 via fibre scale α ===")
    print(f"Seed: {SEED}; N = {N_SAMPLES}; k = {K_NEIGHBORS}; alphas = {ALPHAS}")
    print()

    pts = sample_s3(N_SAMPLES, RNG)
    print(f"[1] Sampled {N_SAMPLES} points on S^3")
    print()

    print("=== Per-α spectrum analysis ===")
    print()

    results = []
    for alpha in ALPHAS:
        t0 = time.perf_counter()
        L = build_berger_laplacian(pts, K_NEIGHBORS, alpha)
        t_build = time.perf_counter() - t0
        eigvals = get_lowest_eigenvalues(L, N_EIGENVALUES)
        t_eig = time.perf_counter() - t0 - t_build
        groups = detect_degeneracy_groups(eigvals)
        # First 3 degeneracy groups
        g_str = ", ".join([f"({v:.4f}, deg={c})" for v, c in groups[:4]])
        print(f"α = {alpha:>5}: build {1000*t_build:.0f}ms, eigsh {1000*t_eig:.0f}ms")
        print(f"  Groups: {g_str}")
        # l-mode interpretation: S^2 has 2l+1 degeneracy, S^3 has (l+1)² degeneracy
        if len(groups) >= 1:
            deg_l1 = groups[0][1]
            if deg_l1 == 3:
                print(f"  l=1 deg = 3 → matches S^2 (2l+1)")
            elif deg_l1 == 4:
                print(f"  l=1 deg = 4 → matches S^3 (l+1)²")
            else:
                print(f"  l=1 deg = {deg_l1} → between S^2 (3) and S^3 (4), intermediate")
        # l=2/l=1 ratio
        if len(groups) >= 2:
            ratio = groups[1][0] / groups[0][0]
            print(f"  l=2/l=1 ratio: {ratio:.3f}  (continuum S²: 3.0, S³: 2.667)")
        results.append({
            "alpha": alpha,
            "build_ms": 1000 * t_build,
            "eigsh_ms": 1000 * t_eig,
            "eigenvalues": [float(e) for e in eigvals],
            "groups": [(float(v), int(c)) for v, c in groups[:6]],
            "l2_l1_ratio": float(groups[1][0] / groups[0][0]) if len(groups) >= 2 else None,
        })
        print()

    # ─── Interpolation summary ─────────────────────────────────────────────
    print("=== Berger interpolation summary ===")
    print()
    print(f"{'α':<8s} {'l=1 deg':<10s} {'l=1 eigenvalue':<18s} {'l=2/l=1 ratio':<16s} {'interp class':<15s}")
    print("-" * 75)
    for r in results:
        alpha = r["alpha"]
        l1_deg = r["groups"][0][1] if r["groups"] else 0
        l1_val = r["groups"][0][0] if r["groups"] else 0
        ratio = r["l2_l1_ratio"] or 0
        if l1_deg == 3:
            cls = "S²-like"
        elif l1_deg == 4:
            cls = "S³-like"
        else:
            cls = f"intermediate({l1_deg})"
        print(f"{alpha:<8.2f} {l1_deg:<10d} {l1_val:<18.4f} {ratio:<16.3f} {cls}")
    print()

    # ─── Verdict ──────────────────────────────────────────────────────────
    print("=== Verdict ===")
    alpha_to_l1deg = {r["alpha"]: r["groups"][0][1] if r["groups"] else 0 for r in results}
    if alpha_to_l1deg.get(0.05) == 3 and alpha_to_l1deg.get(1.0) == 4:
        print("  ✓ α=0.05 gives S²-like (l=1 deg 3); α=1.0 gives S³-like (l=1 deg 4)")
        print("  ✓ Berger interpolation between S² and S³ confirmed")
    else:
        print(f"  α=0.05 l=1 deg: {alpha_to_l1deg.get(0.05)}; α=1.0 l=1 deg: {alpha_to_l1deg.get(1.0)}")
        print(f"  Interpolation behavior at given resolution")

    # Save
    records = [
        {"test": "config", "n_samples": N_SAMPLES, "k_neighbors": K_NEIGHBORS,
         "alphas": ALPHAS},
    ] + [{"test": f"alpha_{r['alpha']}", **r} for r in results]
    with open(RESULTS_FILE, "w") as f:
        for rec in records:
            f.write(json.dumps(rec) + "\n")

    # Plot
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    # Plot l=1 degeneracy vs alpha
    alphas = [r["alpha"] for r in results]
    l1_degs = [r["groups"][0][1] if r["groups"] else 0 for r in results]
    l2_l1_ratios = [r["l2_l1_ratio"] for r in results]
    axes[0].plot(alphas, l1_degs, "g-o", markersize=10)
    axes[0].axhline(3, color="blue", linestyle="--", alpha=0.5, label="S² l=1 deg = 3")
    axes[0].axhline(4, color="red", linestyle="--", alpha=0.5, label="S³ l=1 deg = 4")
    axes[0].set_xlabel("α (fibre scale)"); axes[0].set_ylabel("l=1 degeneracy")
    axes[0].set_xscale("log")
    axes[0].set_title("Berger sphere l=1 degeneracy vs α")
    axes[0].legend(); axes[0].grid(alpha=0.3)

    axes[1].plot(alphas, l2_l1_ratios, "b-s", markersize=10)
    axes[1].axhline(3.0, color="blue", linestyle="--", alpha=0.5, label="S² l=2/l=1 = 3.0")
    axes[1].axhline(8 / 3, color="red", linestyle="--", alpha=0.5, label="S³ l=2/l=1 = 2.67")
    axes[1].set_xlabel("α (fibre scale)"); axes[1].set_ylabel("l=2 / l=1 ratio")
    axes[1].set_xscale("log")
    axes[1].set_title("Berger sphere mode ratio vs α")
    axes[1].legend(); axes[1].grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig(OUT_DIR / "berger-sphere-metric-2026-05-12.png", dpi=100)
    plt.close()

    print(f"\nResults: {RESULTS_FILE.name}")


if __name__ == "__main__":
    main()

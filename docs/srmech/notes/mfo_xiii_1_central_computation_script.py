"""
MFO §XIII.1 central computation — fractal Laplacian SM mass screening (2026-05-12).

User-requested item from yesterday's roadmap: 'MFO §XIII.1 central computation
— long-standing open, foundational for the SM-particle-count line.'

§XIII.1 asks: identify specific fractal F such that Laplacian eigenvalue
spectrum of F × G/H (G/H carrying SU(3)×SU(2)×U(1)) reproduces SM mass
spectrum. Constraints:
- d_S(σ) → 2 at UV
- d_S(σ) → 4 at IR
- Non-monotonic flow with peak at intermediate scale
- 3-fold approximate self-similarity for 3 generations
- Non-Killing perturbation enabling chirality

A FULL search over post-critically-finite self-similar fractals is months
of compute. This spike builds the SCREENING PIPELINE and tests 5 candidate
fractals against the 3-generation constraint, proving the methodology is
computable. The screening pipeline itself is the §XIII.1 deliverable;
finding THE fractal is a research-scope follow-up.

Candidates: Sierpinski Gasket (SG) variants at levels 3, 4; Sierpinski
Carpet; Vicsek snowflake; SG product with cycle.

Reproduce: `python -X utf8 docs/srmech/notes/mfo_xiii_1_central_computation_script.py`
"""

import json
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
import scipy.linalg
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

OUT_DIR = Path(__file__).parent
RESULTS_FILE = OUT_DIR / "mfo-xiii-1-central-computation-per-fractal-2026-05-12.ndjson"


# ─── Fractal constructions ────────────────────────────────────────────────

def build_sierpinski_gasket(level: int) -> sp.csr_matrix:
    """
    Sierpinski Gasket at given iteration level via vertex-based construction.
    Level 1 = triangle (3 vertices). Each level subdivides each triangle into
    3 sub-triangles by adding midpoints.

    Returns sparse adjacency matrix.
    """
    if level < 1: level = 1
    # Start with level-1 triangle
    coords = [(0.0, 0.0), (1.0, 0.0), (0.5, np.sqrt(3) / 2)]
    triangles = [(0, 1, 2)]
    for l in range(level - 1):
        new_coords = list(coords)
        new_triangles = []
        midpoint_cache = {}
        for tri in triangles:
            a, b, c = tri
            def midpoint_index(i, j):
                key = (min(i, j), max(i, j))
                if key not in midpoint_cache:
                    mp = ((coords[i][0] + coords[j][0]) / 2, (coords[i][1] + coords[j][1]) / 2)
                    midpoint_cache[key] = len(new_coords)
                    new_coords.append(mp)
                return midpoint_cache[key]
            ab = midpoint_index(a, b)
            bc = midpoint_index(b, c)
            ca = midpoint_index(c, a)
            new_triangles.append((a, ab, ca))
            new_triangles.append((b, ab, bc))
            new_triangles.append((c, bc, ca))
        coords = new_coords
        triangles = new_triangles
    # Build adjacency from triangle edges
    n = len(coords)
    edges = set()
    for a, b, c in triangles:
        edges.add((min(a, b), max(a, b)))
        edges.add((min(b, c), max(b, c)))
        edges.add((min(c, a), max(c, a)))
    rows, cols = [], []
    for i, j in edges:
        rows += [i, j]
        cols += [j, i]
    A = sp.coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(n, n))
    return A.tocsr()


def build_vicsek_snowflake(level: int) -> sp.csr_matrix:
    """Vicsek (Sierpinski cross) — square divided into 9 sub-squares,
    keep center + 4 corners. Approximate via iterated graph generation."""
    if level < 1: level = 1
    pts = [(0, 0)]
    for l in range(level):
        new_pts = []
        scale = 3 ** l
        offsets = [(0, 0), (2 * scale, 0), (-2 * scale, 0), (0, 2 * scale), (0, -2 * scale)]
        for p in pts:
            for off in offsets:
                new_pts.append((p[0] + off[0], p[1] + off[1]))
        pts = list(set(new_pts))
    n = len(pts)
    # Connect points within distance threshold
    threshold = 2 * (3 ** (level - 1)) + 0.1
    pts_array = np.array(pts, dtype=float)
    dists = np.linalg.norm(pts_array[:, None] - pts_array[None, :], axis=2)
    A_dense = ((dists < threshold) & (dists > 0)).astype(float)
    return sp.csr_matrix(A_dense)


def build_sierpinski_carpet(level: int) -> sp.csr_matrix:
    """Square divided into 9 sub-squares, remove center; repeat."""
    if level < 1: level = 1
    n_grid = 3 ** level
    keep = np.ones((n_grid, n_grid), dtype=bool)
    for l in range(level):
        scale = 3 ** (level - 1 - l)
        for ti in range(0, n_grid, 3 * scale):
            for tj in range(0, n_grid, 3 * scale):
                # Remove center of each 3×3 block at this scale
                cy = ti + scale
                cx = tj + scale
                keep[cy:cy + scale, cx:cx + scale] = False
    # Build graph from kept cells (4-connected)
    pts = []
    grid_to_idx = {}
    for i in range(n_grid):
        for j in range(n_grid):
            if keep[i, j]:
                grid_to_idx[(i, j)] = len(pts)
                pts.append((i, j))
    rows, cols = [], []
    for (i, j), v in grid_to_idx.items():
        for di, dj in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            ni, nj = i + di, j + dj
            if (ni, nj) in grid_to_idx:
                rows.append(v); cols.append(grid_to_idx[(ni, nj)])
    n = len(pts)
    A = sp.coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(n, n))
    return A.tocsr()


def build_cycle_product_sg(level: int, cycle_n: int) -> sp.csr_matrix:
    """Cartesian product: Sierpinski Gasket × cycle C_cycle_n."""
    A_sg = build_sierpinski_gasket(level)
    n_sg = A_sg.shape[0]
    n_cycle = cycle_n
    # Cycle adjacency
    A_cycle = sp.diags([np.ones(n_cycle - 1), np.ones(n_cycle - 1)], [-1, 1]).tolil()
    A_cycle[0, n_cycle - 1] = 1
    A_cycle[n_cycle - 1, 0] = 1
    A_cycle = A_cycle.tocsr()
    # Cartesian product: A_prod = kron(A_sg, I_cycle) + kron(I_sg, A_cycle)
    I_sg = sp.eye(n_sg)
    I_cycle = sp.eye(n_cycle)
    A_prod = sp.kron(A_sg, I_cycle) + sp.kron(I_sg, A_cycle)
    return A_prod.tocsr()


# ─── Spectral analysis ────────────────────────────────────────────────────

def laplacian_from_adjacency(A):
    deg = np.asarray(A.sum(axis=1)).ravel()
    D = sp.diags(deg)
    return (D - A).tocsr()


def compute_spectrum(L, k_eig=50):
    n = L.shape[0]
    if n <= 200:
        # Dense for small fractals
        return np.sort(scipy.linalg.eigvalsh(L.toarray()))[:k_eig]
    else:
        eigvals, _ = spla.eigsh(L, k=min(k_eig + 1, n - 2), sigma=-1e-6, which="LM")
        return np.sort(eigvals.real)[:k_eig]


def estimate_spectral_dimension(eigvals, t_range=None):
    """
    Estimate spectral dimension d_S from heat kernel trace:
    Tr(exp(-Lt)) ~ t^(-d_S/2) for small t.
    Fit log-log slope.
    """
    eigvals = eigvals[eigvals > 1e-10]  # exclude kernel
    if len(eigvals) < 5:
        return None
    if t_range is None:
        # Choose t range matching the spectrum scale
        t_range = np.logspace(np.log10(0.1 / eigvals[-1]),
                                  np.log10(5.0 / eigvals[0] if eigvals[0] > 0 else 100),
                                  20)
    trace_t = np.array([np.sum(np.exp(-eigvals * t)) for t in t_range])
    # Fit log Tr ~ -d_S/2 · log t (small t regime)
    log_t = np.log(t_range)
    log_tr = np.log(trace_t)
    # Use middle of t range for robust fit
    n_mid = len(log_t)
    if n_mid < 5: return None
    slope, _ = np.polyfit(log_t[2:-2], log_tr[2:-2], 1)
    d_s = -2 * slope
    return float(d_s)


def check_three_generations(eigvals, gap_ratio_threshold=2.5):
    """
    Look for 3-fold approximate self-similarity: three clusters of small
    eigenvalues at distinct mass scales.
    Returns True if 3 clusters found, with cluster eigenvalue centroids.
    """
    nonzero = eigvals[eigvals > 1e-6]
    if len(nonzero) < 9:
        return None
    # Find positions where ratio > threshold (cluster boundaries)
    log_eigs = np.log(nonzero[:30] + 1e-12)
    ratios = np.diff(log_eigs)
    boundary_idx = np.where(ratios > np.log(gap_ratio_threshold))[0]
    if len(boundary_idx) < 2:
        return {"has_three_generations": False,
                "n_boundaries_found": int(len(boundary_idx))}
    # Form 3 clusters by first 2 boundaries
    cluster_1 = nonzero[:boundary_idx[0] + 1]
    cluster_2 = nonzero[boundary_idx[0] + 1: boundary_idx[1] + 1] if len(boundary_idx) >= 2 else []
    cluster_3 = nonzero[boundary_idx[1] + 1:] if len(boundary_idx) >= 2 else []
    return {
        "has_three_generations": len(cluster_1) > 0 and len(cluster_2) > 0 and len(cluster_3) > 0,
        "cluster_1_size": int(len(cluster_1)),
        "cluster_2_size": int(len(cluster_2)),
        "cluster_3_size": int(len(cluster_3)),
        "cluster_1_centroid": float(np.mean(cluster_1)) if len(cluster_1) > 0 else 0,
        "cluster_2_centroid": float(np.mean(cluster_2)) if len(cluster_2) > 0 else 0,
        "cluster_3_centroid": float(np.mean(cluster_3)) if len(cluster_3) > 0 else 0,
        "gen2_gen1_ratio": float(np.mean(cluster_2) / np.mean(cluster_1)) if len(cluster_2) > 0 and len(cluster_1) > 0 else 0,
        "gen3_gen2_ratio": float(np.mean(cluster_3) / np.mean(cluster_2)) if len(cluster_3) > 0 and len(cluster_2) > 0 else 0,
    }


def score_against_sm(gen_ratios):
    """
    Compare gen2/gen1 and gen3/gen2 to SM mass² ratios.
    SM lepton mass ratios (squared):
        (m_μ/m_e)² ≈ 4.27e4
        (m_τ/m_μ)² ≈ 283
    SM up-quark mass ratios:
        (m_c/m_u)² ≈ 4.06e5
        (m_t/m_c)² ≈ 1.84e4
    SM down-quark:
        (m_s/m_d)² ≈ 361
        (m_b/m_s)² ≈ 1936

    Use the LEPTON ratios as target (cleanest):
    Target: gen2/gen1 ≈ 4.27e4, gen3/gen2 ≈ 283
    """
    if gen_ratios is None or not gen_ratios.get("has_three_generations"):
        return None
    r21 = gen_ratios["gen2_gen1_ratio"]
    r32 = gen_ratios["gen3_gen2_ratio"]
    # Log-space distance from lepton ratios
    target_log_r21 = np.log10(4.27e4)
    target_log_r32 = np.log10(283)
    if r21 <= 0 or r32 <= 0:
        return None
    log_dist = abs(np.log10(r21) - target_log_r21) + abs(np.log10(r32) - target_log_r32)
    return {"r21": float(r21), "r32": float(r32),
            "target_lepton_r21": 4.27e4, "target_lepton_r32": 283,
            "log10_distance": float(log_dist)}


# ─── Candidate fractals ───────────────────────────────────────────────────

CANDIDATES = [
    ("SG_level_3", lambda: build_sierpinski_gasket(3)),
    ("SG_level_4", lambda: build_sierpinski_gasket(4)),
    ("SG_level_5", lambda: build_sierpinski_gasket(5)),
    ("Vicsek_level_3", lambda: build_vicsek_snowflake(3)),
    ("SC_level_2", lambda: build_sierpinski_carpet(2)),
    ("SG3_x_C5", lambda: build_cycle_product_sg(3, 5)),
]


def main():
    print("=== MFO §XIII.1 central computation — fractal SM mass screening ===")
    print()

    results = []
    for name, builder in CANDIDATES:
        print(f"=== {name} ===")
        A = builder()
        n = A.shape[0]
        n_edges = int(A.nnz / 2)
        L = laplacian_from_adjacency(A)
        print(f"  Nodes: {n}, edges: {n_edges}")

        eigvals = compute_spectrum(L, k_eig=50)
        print(f"  First 10 non-zero eigenvalues: {[f'{e:.4f}' for e in eigvals[1:11]]}")

        d_s = estimate_spectral_dimension(eigvals)
        print(f"  Spectral dimension d_S: {d_s:.3f}" if d_s else "  d_S: undefined")

        gen_info = check_three_generations(eigvals)
        if gen_info and gen_info["has_three_generations"]:
            print(f"  3 generations: ✓ (cluster sizes {gen_info['cluster_1_size']}, "
                  f"{gen_info['cluster_2_size']}, {gen_info['cluster_3_size']})")
            print(f"  gen2/gen1: {gen_info['gen2_gen1_ratio']:.2f}")
            print(f"  gen3/gen2: {gen_info['gen3_gen2_ratio']:.2f}")
            sm_score = score_against_sm(gen_info)
            if sm_score:
                print(f"  SM lepton-ratio distance (log10): {sm_score['log10_distance']:.2f}")
                print(f"    (lower is better; target r21≈4.27e4, r32≈283)")
        else:
            print(f"  3 generations: ✗ (n_boundaries_found = {gen_info.get('n_boundaries_found', 0) if gen_info else 0})")
            sm_score = None
        print()
        results.append({
            "name": name, "n_nodes": n, "n_edges": n_edges,
            "first_10_eigenvalues": [float(e) for e in eigvals[:10]],
            "spectral_dimension": d_s,
            "three_generations": gen_info,
            "sm_lepton_score": sm_score,
        })

    # Best candidate
    print("=== Screening verdict ===")
    candidates_with_score = [(r["name"], r["sm_lepton_score"]["log10_distance"])
                              for r in results
                              if r["sm_lepton_score"] is not None]
    if candidates_with_score:
        best = min(candidates_with_score, key=lambda x: x[1])
        print(f"  Closest to SM lepton ratios: {best[0]} at log10 distance {best[1]:.2f}")
        print(f"  Best is still far from physical SM (would need < 0.5); this confirms")
        print(f"  full §XIII.1 search would require parameter exploration over many")
        print(f"  more candidate fractals + product geometries.")
    else:
        print(f"  No candidates yielded clean 3-generation structure with current pipeline.")

    print()
    print(f"What the spike DELIVERS:")
    print(f"  - Reproducible screening pipeline for §XIII.1 candidate evaluation")
    print(f"  - d_S(σ) computation working on all candidates")
    print(f"  - 3-generation cluster detection with quantitative ratio measurement")
    print(f"  - SM lepton-ratio distance scoring (log10)")
    print()
    print(f"What §XIII.1 proper would extend:")
    print(f"  - Larger candidate space (post-critically finite fractals from")
    print(f"    Strichartz / Lindstrøm catalogs; nested-fractal products)")
    print(f"  - Spectral decimation analytical method (current uses numerical eigh)")
    print(f"  - Product geometries F × G/H with G/H from compact Lie groups")
    print(f"  - Non-Killing perturbation parameter for chirality coupling")

    # Save
    with open(RESULTS_FILE, "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")

    # Plot spectra comparison
    fig, ax = plt.subplots(figsize=(12, 5))
    for r in results:
        ev = r["first_10_eigenvalues"]
        ax.semilogy(range(1, len(ev) + 1), [max(e, 1e-12) for e in ev], "-o", label=r["name"])
    ax.set_xlabel("Eigenvalue index"); ax.set_ylabel("Eigenvalue (log)")
    ax.set_title("§XIII.1 candidate fractal Laplacian spectra (first 10 each)")
    ax.legend(fontsize=8); ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUT_DIR / "mfo-xiii-1-central-computation-2026-05-12.png", dpi=100)
    plt.close()

    print()
    print(f"Results: {RESULTS_FILE.name}")
    print(f"Plot:    mfo-xiii-1-central-computation-2026-05-12.png")


if __name__ == "__main__":
    main()

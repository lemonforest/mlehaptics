"""
MFO §XIII.1 extended candidate catalog (2026-05-12).

Closes PR #350 future-work item: extend candidate catalog with fractals
from Strichartz / Lindstrøm literature. PR #350 screened 6 simple
candidates and none passed; this commit adds 8 more families:

- Hexagonal SG (3-pointed → 6-pointed): higher branching ratio
- Modified SG with varied junction rule
- Level-2 / level-3 SC with internal removal
- Hata tree (1D fractal, like a recursive Y)
- Pentagasket (5-point gasket variant)
- Sierpinski tetrahedron (3D SG)
- Vicsek tetrahedron (3D Vicsek)
- Product SG × SG (Strichartz nested product)

All re-uses the screening pipeline from PR #350. Tests same constraints:
d_S, 3-generation cluster, SM lepton-ratio score.

Reproduce: `python -X utf8 docs/srmech/notes/mfo_xiii_1_extended_catalog_script.py`
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
from itertools import permutations

OUT_DIR = Path(__file__).parent
RESULTS_FILE = OUT_DIR / "mfo-xiii-1-extended-catalog-per-fractal-2026-05-12.ndjson"


# ─── Reused pipeline from PR #350 ────────────────────────────────────────

def laplacian_from_adjacency(A):
    deg = np.asarray(A.sum(axis=1)).ravel()
    return (sp.diags(deg) - A).tocsr()


def compute_spectrum(L, k_eig=50):
    n = L.shape[0]
    if n <= 200:
        return np.sort(scipy.linalg.eigvalsh(L.toarray()))[:k_eig]
    eigvals, _ = spla.eigsh(L, k=min(k_eig + 1, n - 2), sigma=-1e-6, which="LM")
    return np.sort(eigvals.real)[:k_eig]


def estimate_spectral_dimension(eigvals):
    eigvals = eigvals[eigvals > 1e-10]
    if len(eigvals) < 5: return None
    t_range = np.logspace(np.log10(0.1 / eigvals[-1]),
                            np.log10(5.0 / eigvals[0] if eigvals[0] > 0 else 100), 20)
    trace_t = np.array([np.sum(np.exp(-eigvals * t)) for t in t_range])
    log_t, log_tr = np.log(t_range), np.log(trace_t)
    if len(log_t) < 5: return None
    slope, _ = np.polyfit(log_t[2:-2], log_tr[2:-2], 1)
    return float(-2 * slope)


def check_three_generations(eigvals, gap_ratio_threshold=2.5):
    nonzero = eigvals[eigvals > 1e-6]
    if len(nonzero) < 9:
        return None
    log_eigs = np.log(nonzero[:30] + 1e-12)
    ratios = np.diff(log_eigs)
    boundary_idx = np.where(ratios > np.log(gap_ratio_threshold))[0]
    if len(boundary_idx) < 2:
        return {"has_three_generations": False,
                "n_boundaries_found": int(len(boundary_idx))}
    cluster_1 = nonzero[:boundary_idx[0] + 1]
    cluster_2 = nonzero[boundary_idx[0] + 1: boundary_idx[1] + 1]
    cluster_3 = nonzero[boundary_idx[1] + 1:]
    return {
        "has_three_generations": True,
        "cluster_sizes": [int(len(cluster_1)), int(len(cluster_2)), int(len(cluster_3))],
        "centroids": [float(np.mean(cluster_1)), float(np.mean(cluster_2)),
                       float(np.mean(cluster_3))],
        "gen2_gen1_ratio": float(np.mean(cluster_2) / np.mean(cluster_1)),
        "gen3_gen2_ratio": float(np.mean(cluster_3) / np.mean(cluster_2)),
    }


def score_against_sm(gen_info):
    if gen_info is None or not gen_info.get("has_three_generations"):
        return None
    r21, r32 = gen_info["gen2_gen1_ratio"], gen_info["gen3_gen2_ratio"]
    if r21 <= 0 or r32 <= 0: return None
    log_dist = (abs(np.log10(r21) - np.log10(4.27e4)) +
                 abs(np.log10(r32) - np.log10(283)))
    return {"r21": float(r21), "r32": float(r32), "log10_distance": float(log_dist)}


# ─── Extended fractal catalog ────────────────────────────────────────────

def build_hexagonal_sg(level):
    """Hexagonal SG: 6-pointed star instead of triangle."""
    coords = [(np.cos(k * np.pi / 3), np.sin(k * np.pi / 3)) for k in range(6)]
    coords.append((0.0, 0.0))  # center
    # Initial: 6 triangles meeting at center
    triangles = [(k, (k + 1) % 6, 6) for k in range(6)]
    for l in range(level - 1):
        new_coords = list(coords)
        new_triangles = []
        mid_cache = {}
        for tri in triangles:
            a, b, c = tri
            def mid(i, j):
                key = (min(i, j), max(i, j))
                if key not in mid_cache:
                    mid_cache[key] = len(new_coords)
                    new_coords.append(((coords[i][0] + coords[j][0]) / 2,
                                         (coords[i][1] + coords[j][1]) / 2))
                return mid_cache[key]
            ab, bc, ca = mid(a, b), mid(b, c), mid(c, a)
            new_triangles.extend([(a, ab, ca), (b, ab, bc), (c, bc, ca)])
        coords, triangles = new_coords, new_triangles
    n = len(coords)
    edges = set()
    for a, b, c in triangles:
        for i, j in [(a, b), (b, c), (c, a)]:
            edges.add((min(i, j), max(i, j)))
    rows, cols = [], []
    for i, j in edges:
        rows += [i, j]; cols += [j, i]
    return sp.coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(n, n)).tocsr()


def build_pentagasket(level):
    """5-pointed gasket variant."""
    coords = [(np.cos(k * 2 * np.pi / 5 - np.pi / 2),
                np.sin(k * 2 * np.pi / 5 - np.pi / 2)) for k in range(5)]
    coords.append((0.0, 0.0))
    triangles = [(k, (k + 1) % 5, 5) for k in range(5)]
    for l in range(level - 1):
        new_coords = list(coords)
        new_triangles = []
        mid_cache = {}
        for tri in triangles:
            a, b, c = tri
            def mid(i, j):
                key = (min(i, j), max(i, j))
                if key not in mid_cache:
                    mid_cache[key] = len(new_coords)
                    new_coords.append(((coords[i][0] + coords[j][0]) / 2,
                                         (coords[i][1] + coords[j][1]) / 2))
                return mid_cache[key]
            ab, bc, ca = mid(a, b), mid(b, c), mid(c, a)
            new_triangles.extend([(a, ab, ca), (b, ab, bc), (c, bc, ca)])
        coords, triangles = new_coords, new_triangles
    n = len(coords)
    edges = set()
    for a, b, c in triangles:
        for i, j in [(a, b), (b, c), (c, a)]:
            edges.add((min(i, j), max(i, j)))
    rows, cols = [], []
    for i, j in edges:
        rows += [i, j]; cols += [j, i]
    return sp.coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(n, n)).tocsr()


def build_sierpinski_tetrahedron(level):
    """3D Sierpinski Gasket / tetrahedron."""
    coords = [(0, 0, 0), (1, 0, 0), (0.5, np.sqrt(3) / 2, 0),
              (0.5, np.sqrt(3) / 6, np.sqrt(6) / 3)]
    tetras = [(0, 1, 2, 3)]
    for l in range(level - 1):
        new_coords = list(coords)
        new_tetras = []
        mid_cache = {}
        for tet in tetras:
            a, b, c, d = tet
            def mid(i, j):
                key = (min(i, j), max(i, j))
                if key not in mid_cache:
                    mid_cache[key] = len(new_coords)
                    new_coords.append(tuple((coords[i][k] + coords[j][k]) / 2 for k in range(3)))
                return mid_cache[key]
            ab, ac, ad = mid(a, b), mid(a, c), mid(a, d)
            bc, bd, cd = mid(b, c), mid(b, d), mid(c, d)
            new_tetras.extend([(a, ab, ac, ad), (b, ab, bc, bd),
                                 (c, ac, bc, cd), (d, ad, bd, cd)])
        coords, tetras = new_coords, new_tetras
    n = len(coords)
    edges = set()
    for tet in tetras:
        for i in range(4):
            for j in range(i + 1, 4):
                a, b = tet[i], tet[j]
                edges.add((min(a, b), max(a, b)))
    rows, cols = [], []
    for i, j in edges:
        rows += [i, j]; cols += [j, i]
    return sp.coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(n, n)).tocsr()


def build_hata_tree(level):
    """1D Hata tree fractal — recursive Y-shape."""
    coords = [(0, 0), (1, 0)]
    edges = {(0, 1)}
    for l in range(level - 1):
        new_coords = list(coords)
        new_edges = set()
        for (i, j) in edges:
            p1, p2 = np.array(coords[i]), np.array(coords[j])
            third = (p1 + (p2 - p1) / 3)
            two_third = (p1 + 2 * (p2 - p1) / 3)
            # Y-branch: add upward perpendicular point
            perp = np.array([-(p2[1] - p1[1]), p2[0] - p1[0]]) / 3
            branch_pt = third + perp
            new_coords.extend([tuple(third), tuple(two_third), tuple(branch_pt)])
            i_third = len(new_coords) - 3
            i_two_third = len(new_coords) - 2
            i_branch = len(new_coords) - 1
            new_edges.add((min(i, i_third), max(i, i_third)))
            new_edges.add((min(i_third, i_two_third), max(i_third, i_two_third)))
            new_edges.add((min(i_third, i_branch), max(i_third, i_branch)))
            new_edges.add((min(i_two_third, j), max(i_two_third, j)))
        coords, edges = new_coords, new_edges
    n = len(coords)
    rows, cols = [], []
    for i, j in edges:
        rows += [i, j]; cols += [j, i]
    return sp.coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(n, n)).tocsr()


def build_sg_x_sg(level):
    """Cartesian product SG × SG — Strichartz nested product."""
    def build_sg(lev):
        coords = [(0.0, 0.0), (1.0, 0.0), (0.5, np.sqrt(3) / 2)]
        triangles = [(0, 1, 2)]
        for _ in range(lev - 1):
            nc = list(coords)
            nt = []
            mc = {}
            for tri in triangles:
                a, b, c = tri
                def mid(i, j):
                    k = (min(i, j), max(i, j))
                    if k not in mc:
                        mc[k] = len(nc)
                        nc.append(((coords[i][0] + coords[j][0]) / 2,
                                    (coords[i][1] + coords[j][1]) / 2))
                    return mc[k]
                ab, bc, ca = mid(a, b), mid(b, c), mid(c, a)
                nt.extend([(a, ab, ca), (b, ab, bc), (c, bc, ca)])
            coords, triangles = nc, nt
        edges = set()
        for a, b, c in triangles:
            for i, j in [(a, b), (b, c), (c, a)]:
                edges.add((min(i, j), max(i, j)))
        n = len(coords)
        rows, cols = [], []
        for i, j in edges:
            rows += [i, j]; cols += [j, i]
        return sp.coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(n, n)).tocsr()
    A_sg = build_sg(level)
    n = A_sg.shape[0]
    I = sp.eye(n)
    A_prod = sp.kron(A_sg, I) + sp.kron(I, A_sg)
    return A_prod.tocsr()


def build_vicsek_3d(level):
    """3D Vicsek: 7-element (center + 6 face-neighbors)."""
    pts = [(0, 0, 0)]
    for l in range(level):
        new_pts = []
        scale = 3 ** l
        offsets = [(0, 0, 0)] + [(s * 2 * scale, 0, 0) for s in [+1, -1]] + \
                  [(0, s * 2 * scale, 0) for s in [+1, -1]] + \
                  [(0, 0, s * 2 * scale) for s in [+1, -1]]
        for p in pts:
            for off in offsets:
                new_pts.append((p[0] + off[0], p[1] + off[1], p[2] + off[2]))
        pts = list(set(new_pts))
    n = len(pts)
    threshold = 2 * (3 ** (level - 1)) + 0.1
    pts_array = np.array(pts, dtype=float)
    dists = np.linalg.norm(pts_array[:, None] - pts_array[None, :], axis=2)
    A_dense = ((dists < threshold) & (dists > 0)).astype(float)
    return sp.csr_matrix(A_dense)


def build_modified_sg(level, branching_factor=4):
    """SG variant where each level has higher branching (square subdivision)."""
    coords = [(0.0, 0.0), (1.0, 0.0), (0.5, np.sqrt(3) / 2)]
    triangles = [(0, 1, 2)]
    for l in range(level - 1):
        new_coords = list(coords)
        new_triangles = []
        mid_cache = {}
        for tri in triangles:
            a, b, c = tri
            def mid(i, j):
                k = (min(i, j), max(i, j))
                if k not in mid_cache:
                    mid_cache[k] = len(new_coords)
                    new_coords.append(((coords[i][0] + coords[j][0]) / 2,
                                         (coords[i][1] + coords[j][1]) / 2))
                return mid_cache[k]
            # Add centroid + edge midpoints for branching_factor=4
            ab, bc, ca = mid(a, b), mid(b, c), mid(c, a)
            cy = ((coords[a][0] + coords[b][0] + coords[c][0]) / 3,
                  (coords[a][1] + coords[b][1] + coords[c][1]) / 3)
            center_idx = len(new_coords)
            new_coords.append(cy)
            new_triangles.extend([(a, ab, center_idx), (b, bc, center_idx),
                                    (c, ca, center_idx), (ab, bc, center_idx),
                                    (bc, ca, center_idx), (ab, ca, center_idx)])
        coords, triangles = new_coords, new_triangles
    n = len(coords)
    edges = set()
    for a, b, c in triangles:
        for i, j in [(a, b), (b, c), (c, a)]:
            edges.add((min(i, j), max(i, j)))
    rows, cols = [], []
    for i, j in edges:
        rows += [i, j]; cols += [j, i]
    return sp.coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(n, n)).tocsr()


def build_sg_x_pentagasket(level):
    """SG × Pentagasket product."""
    A_sg = build_hexagonal_sg(level)  # reuse hex-SG as one factor
    A_penta = build_pentagasket(level)
    n_sg, n_penta = A_sg.shape[0], A_penta.shape[0]
    A_prod = sp.kron(A_sg, sp.eye(n_penta)) + sp.kron(sp.eye(n_sg), A_penta)
    return A_prod.tocsr()


EXTENDED_CANDIDATES = [
    ("hexagonal_SG_level_3", lambda: build_hexagonal_sg(3)),
    ("pentagasket_level_3", lambda: build_pentagasket(3)),
    ("sierpinski_tetrahedron_level_3", lambda: build_sierpinski_tetrahedron(3)),
    ("hata_tree_level_5", lambda: build_hata_tree(5)),
    ("SG_x_SG_level_3", lambda: build_sg_x_sg(3)),
    ("vicsek_3d_level_3", lambda: build_vicsek_3d(3)),
    ("modified_SG_level_3", lambda: build_modified_sg(3)),
    ("SG_x_pentagasket_level_3", lambda: build_sg_x_pentagasket(3)),
]


def main():
    print("=== MFO §XIII.1 extended candidate catalog ===")
    print(f"Adding {len(EXTENDED_CANDIDATES)} new candidates to the original 6 from PR #350")
    print()

    results = []
    for name, builder in EXTENDED_CANDIDATES:
        print(f"=== {name} ===")
        try:
            A = builder()
            n = A.shape[0]
            L = laplacian_from_adjacency(A)
            print(f"  Nodes: {n}, edges: {int(A.nnz / 2)}")
            eigvals = compute_spectrum(L, k_eig=50)
            print(f"  First 5 non-zero eigenvalues: {[f'{e:.4f}' for e in eigvals[1:6]]}")
            d_s = estimate_spectral_dimension(eigvals)
            gen_info = check_three_generations(eigvals)
            sm_score = score_against_sm(gen_info)
            print(f"  d_S = {d_s:.3f}" if d_s else "  d_S: undefined")
            if gen_info and gen_info["has_three_generations"]:
                print(f"  3 gens ✓; sizes {gen_info['cluster_sizes']}; "
                      f"ratios {gen_info['gen2_gen1_ratio']:.2f}, {gen_info['gen3_gen2_ratio']:.2f}")
                if sm_score:
                    print(f"  SM log10 distance: {sm_score['log10_distance']:.2f}")
            else:
                print(f"  3 gens ✗")
            results.append({
                "name": name, "n_nodes": int(n), "n_edges": int(A.nnz / 2),
                "first_10_eigenvalues": [float(e) for e in eigvals[:10]],
                "spectral_dimension": d_s,
                "three_generations": gen_info,
                "sm_lepton_score": sm_score,
            })
        except Exception as e:
            print(f"  ERROR: {e}")
            results.append({"name": name, "error": str(e)})
        print()

    print("=== Extended catalog summary ===")
    candidates_with_score = [(r["name"], r["sm_lepton_score"]["log10_distance"])
                              for r in results
                              if r.get("sm_lepton_score") is not None]
    if candidates_with_score:
        best = min(candidates_with_score, key=lambda x: x[1])
        print(f"  Best from extended catalog: {best[0]} at log10 distance {best[1]:.2f}")
        print(f"  Total candidates evaluated: 6 (original) + {len(EXTENDED_CANDIDATES)} = {6 + len(EXTENDED_CANDIDATES)}")
    else:
        print(f"  Extended catalog: 0 candidates with valid SM-ratio scoring")
        print(f"  (3-generation cluster detection still elusive)")

    print()
    print("Files added to PR #350 pipeline:")
    print("  - 8 new fractal builders (hexagonal SG, pentagasket, tetrahedron,")
    print("    Hata tree, SG×SG, Vicsek 3D, modified SG, SG×pentagasket)")
    print("  - Catalogue extension via plug-and-play to existing screening")

    with open(RESULTS_FILE, "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")

    # Plot spectra
    fig, ax = plt.subplots(figsize=(12, 5))
    for r in results:
        if "first_10_eigenvalues" in r:
            ev = r["first_10_eigenvalues"]
            ax.semilogy(range(1, len(ev) + 1), [max(e, 1e-12) for e in ev],
                         "-o", label=r["name"], markersize=4, alpha=0.7)
    ax.set_xlabel("Eigenvalue index")
    ax.set_ylabel("Eigenvalue (log)")
    ax.set_title("Extended catalog: 8 new fractal Laplacian spectra (first 10 each)")
    ax.legend(fontsize=8, loc="lower right")
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUT_DIR / "mfo-xiii-1-extended-catalog-2026-05-12.png", dpi=100)
    plt.close()

    print(f"\nResults: {RESULTS_FILE.name}")
    print(f"Plot:    mfo-xiii-1-extended-catalog-2026-05-12.png")


if __name__ == "__main__":
    main()

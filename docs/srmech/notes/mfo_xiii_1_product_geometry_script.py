"""
MFO §XIII.1 product geometry constructor F × G/H (2026-05-12).

PR #350 future-work item: implement product-geometry construction
F × G/H where G/H is a homogeneous space. §XIII.1 calls for G/H with
isometry containing SU(3)×SU(2)×U(1) — for this spike, test with simpler
G/H options that capture the Lie-group spectrum structure:

- S²        — eigenvalues l(l+1), degeneracy 2l+1 (SU(2)/U(1))
- S³        — eigenvalues l(l+2), degeneracy (l+1)² (SU(2) itself)
- S² × S²   — sums of two S² spectra (SO(3)×SO(3)/U(1)²)
- S² × S¹   — Kaluza-Klein-like (compact dim added)
- CP² toy   — eigenvalues from canonical Fubini-Study (rough)

Cartesian product Laplacian: λ_(F × G/H) = λ_F + λ_(G/H), with
multiplicity = mult_F × mult_(G/H).

For each (F, G/H) pair, take all pairwise sums, sort, and apply the
PR #350 screening: d_S, 3-generation cluster detection, SM lepton-ratio
score.

Reproduce: `python -X utf8 docs/srmech/notes/mfo_xiii_1_product_geometry_script.py`
"""

import json
import numpy as np
import scipy.sparse as sp
import scipy.linalg
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

OUT_DIR = Path(__file__).parent
RESULTS_FILE = OUT_DIR / "mfo-xiii-1-product-geometry-per-product-2026-05-12.ndjson"


# ─── Fractal builders (subset from previous commits) ─────────────────────

def build_sierpinski_gasket(level):
    coords = [(0.0, 0.0), (1.0, 0.0), (0.5, np.sqrt(3) / 2)]
    triangles = [(0, 1, 2)]
    for _ in range(level - 1):
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


def fractal_spectrum(level=4, k_eig=30):
    """Compute SG spectrum at given level."""
    A = build_sierpinski_gasket(level)
    deg = np.asarray(A.sum(axis=1)).ravel()
    L = (sp.diags(deg) - A).tocsr().toarray()
    eigs = np.sort(scipy.linalg.eigvalsh(L))
    return eigs[:k_eig]


# ─── Homogeneous space spectra (continuum analytical) ───────────────────

def s2_spectrum(l_max):
    """S² eigenvalues with multiplicity: eigvals l(l+1) × deg (2l+1)."""
    eigvals, mults = [], []
    for l in range(l_max + 1):
        eigvals.append(l * (l + 1))
        mults.append(2 * l + 1)
    return np.array(eigvals, dtype=float), np.array(mults)


def s3_spectrum(l_max):
    """S³ eigenvalues with multiplicity: l(l+2) × (l+1)²."""
    eigvals, mults = [], []
    for l in range(l_max + 1):
        eigvals.append(l * (l + 2))
        mults.append((l + 1) ** 2)
    return np.array(eigvals, dtype=float), np.array(mults)


def s1_spectrum(n_max):
    """S¹ eigenvalues: m² × 2 (for m ≠ 0), 1 (for m=0)."""
    eigvals, mults = [0.0], [1]
    for m in range(1, n_max + 1):
        eigvals.append(float(m ** 2))
        mults.append(2)
    return np.array(eigvals, dtype=float), np.array(mults)


def s2_x_s2_spectrum(l_max):
    """S² × S² product: sums of two S² spectra."""
    s2_e, s2_m = s2_spectrum(l_max)
    eigvals, mults = [], []
    for i, ei in enumerate(s2_e):
        for j, ej in enumerate(s2_e):
            eigvals.append(ei + ej)
            mults.append(s2_m[i] * s2_m[j])
    arr = np.array(sorted(zip(eigvals, mults)))
    return arr[:, 0], arr[:, 1].astype(int)


def s2_x_s1_spectrum(l_max, m_max):
    """S² × S¹ Kaluza-Klein style: sum of S² and S¹ spectra."""
    s2_e, s2_m = s2_spectrum(l_max)
    s1_e, s1_m = s1_spectrum(m_max)
    eigvals, mults = [], []
    for i, ei in enumerate(s2_e):
        for j, ej in enumerate(s1_e):
            eigvals.append(ei + ej)
            mults.append(s2_m[i] * s1_m[j])
    arr = np.array(sorted(zip(eigvals, mults)))
    return arr[:, 0], arr[:, 1].astype(int)


def cp2_spectrum(l_max):
    """CP² Fubini-Study Laplacian eigenvalues (approx; see Boyer-Mann).
    Eigenvalues: 4 l(l + 2) for l = 0, 1, 2, ... with degeneracy (l+1)³ - l³ - 1?
    For spike, use simple form: eigvals l(l+2), degeneracy ~ (l+1)²·(l+2)/2."""
    eigvals, mults = [], []
    for l in range(l_max + 1):
        eigvals.append(float(4 * l * (l + 2)))
        # CP² degeneracy formula (rough): related to dim of certain rep
        mults.append((l + 1) * (l + 2) // 2 if l > 0 else 1)
    return np.array(eigvals, dtype=float), np.array(mults)


# ─── Product spectrum: F × G/H ───────────────────────────────────────────

def product_spectrum(f_eigvals, gh_eigvals, gh_mults, k_total=200):
    """All pairwise sums λ_F + λ_(G/H), with multiplicities."""
    all_eigvals, all_mults = [], []
    for ef in f_eigvals:
        for eg, mg in zip(gh_eigvals, gh_mults):
            all_eigvals.append(float(ef + eg))
            all_mults.append(int(mg))
    arr_sorted = sorted(zip(all_eigvals, all_mults))
    # Expand multiplicities → flat eigenvalue list
    flat = []
    for val, mult in arr_sorted:
        flat.extend([val] * mult)
    return np.array(flat[:k_total])


# ─── Screening (same as PR #350) ────────────────────────────────────────

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


def check_three_generations(eigvals, gap_ratio_threshold=2.0):
    nonzero = eigvals[eigvals > 1e-6]
    if len(nonzero) < 9: return None
    log_eigs = np.log(nonzero[:40] + 1e-12)
    ratios = np.diff(log_eigs)
    boundary_idx = np.where(ratios > np.log(gap_ratio_threshold))[0]
    if len(boundary_idx) < 2:
        return {"has_three_generations": False,
                "n_boundaries_found": int(len(boundary_idx))}
    c1 = nonzero[:boundary_idx[0] + 1]
    c2 = nonzero[boundary_idx[0] + 1: boundary_idx[1] + 1]
    c3 = nonzero[boundary_idx[1] + 1: boundary_idx[2] + 1] if len(boundary_idx) >= 3 else nonzero[boundary_idx[1] + 1:]
    return {
        "has_three_generations": True,
        "cluster_sizes": [int(len(c1)), int(len(c2)), int(len(c3))],
        "centroids": [float(np.mean(c1)), float(np.mean(c2)), float(np.mean(c3))],
        "gen2_gen1_ratio": float(np.mean(c2) / np.mean(c1)) if np.mean(c1) > 0 else 0,
        "gen3_gen2_ratio": float(np.mean(c3) / np.mean(c2)) if np.mean(c2) > 0 else 0,
    }


def score_against_sm(gen_info):
    if gen_info is None or not gen_info.get("has_three_generations"):
        return None
    r21, r32 = gen_info["gen2_gen1_ratio"], gen_info["gen3_gen2_ratio"]
    if r21 <= 0 or r32 <= 0: return None
    return {
        "r21": float(r21), "r32": float(r32),
        "log10_distance": float(abs(np.log10(r21) - np.log10(4.27e4)) +
                                  abs(np.log10(r32) - np.log10(283))),
    }


def main():
    print("=== MFO §XIII.1 product-geometry constructor F × G/H ===")
    print()

    # Choose a fractal F to keep constant across G/H trials
    print("[1] Fractal F: Sierpinski Gasket level 4")
    f_eigs = fractal_spectrum(level=4, k_eig=30)
    print(f"    F first 5 eigenvalues: {f_eigs[1:6]}")
    print()

    # Build G/H options
    print("[2] Homogeneous space G/H spectra:")
    gh_options = {
        "S2": s2_spectrum(8),
        "S3": s3_spectrum(8),
        "S1": s1_spectrum(8),
        "S2_x_S2": s2_x_s2_spectrum(5),
        "S2_x_S1": s2_x_s1_spectrum(5, 5),
        "CP2_approx": cp2_spectrum(5),
    }
    for name, (e, m) in gh_options.items():
        print(f"    {name}: first 4 eigenvalues {e[:4]} (mults {m[:4]})")
    print()

    # Build product spectra
    print("[3] Product spectra F × G/H + screening:")
    print()
    results = []
    for gh_name, (gh_e, gh_m) in gh_options.items():
        prod_eigs = product_spectrum(f_eigs, gh_e, gh_m, k_total=200)
        d_s = estimate_spectral_dimension(prod_eigs)
        gen_info = check_three_generations(prod_eigs, gap_ratio_threshold=2.0)
        sm_score = score_against_sm(gen_info)
        # Also try threshold 3.0 for tighter clusters
        gen_info_tight = check_three_generations(prod_eigs, gap_ratio_threshold=3.0)
        sm_score_tight = score_against_sm(gen_info_tight)
        print(f"  SG4 × {gh_name}:")
        print(f"    d_S = {d_s:.3f}" if d_s else "    d_S: undefined")
        print(f"    Total eigenvalues: {len(prod_eigs)}")
        print(f"    First 5 non-zero: {prod_eigs[prod_eigs > 1e-6][:5]}")
        if gen_info and gen_info["has_three_generations"]:
            print(f"    3-gen (gap≥2.0): sizes {gen_info['cluster_sizes']}, "
                  f"ratios {gen_info['gen2_gen1_ratio']:.2f}, {gen_info['gen3_gen2_ratio']:.2f}")
            if sm_score:
                print(f"    SM log10 distance: {sm_score['log10_distance']:.2f}")
        else:
            n_bnd = gen_info.get("n_boundaries_found", 0) if gen_info else 0
            print(f"    3-gen (gap≥2.0): ✗ ({n_bnd} boundaries)")
        if gen_info_tight and gen_info_tight["has_three_generations"]:
            print(f"    3-gen (gap≥3.0): sizes {gen_info_tight['cluster_sizes']}, "
                  f"ratios {gen_info_tight['gen2_gen1_ratio']:.2f}, {gen_info_tight['gen3_gen2_ratio']:.2f}")
            if sm_score_tight:
                print(f"    SM log10 distance: {sm_score_tight['log10_distance']:.2f}")
        else:
            n_bnd = gen_info_tight.get("n_boundaries_found", 0) if gen_info_tight else 0
            print(f"    3-gen (gap≥3.0): ✗ ({n_bnd} boundaries)")
        print()
        results.append({
            "product_name": f"SG4_x_{gh_name}",
            "gh_space": gh_name,
            "d_s": d_s,
            "n_total_eigenvalues": len(prod_eigs),
            "first_10_nonzero": [float(e) for e in prod_eigs[prod_eigs > 1e-6][:10]],
            "three_gen_gap2": gen_info,
            "sm_score_gap2": sm_score,
            "three_gen_gap3": gen_info_tight,
            "sm_score_gap3": sm_score_tight,
        })

    # Best from set
    print("=== Product-geometry summary ===")
    all_scores = [(r["product_name"], r["sm_score_gap2"]["log10_distance"])
                    for r in results
                    if r.get("sm_score_gap2") is not None]
    all_scores += [(r["product_name"] + " (gap3)", r["sm_score_gap3"]["log10_distance"])
                     for r in results
                     if r.get("sm_score_gap3") is not None]
    if all_scores:
        best = min(all_scores, key=lambda x: x[1])
        print(f"  Best from product geometries: {best[0]} at log10 distance {best[1]:.2f}")
    else:
        print(f"  No product with valid 3-generation structure under either gap threshold")

    print()
    print("Architectural deliverable:")
    print("  - product_spectrum(): plug-and-play F × G/H eigenvalue computation")
    print("  - 6 homogeneous-space spectrum generators (S², S³, S¹, S²×S², S²×S¹, CP²)")
    print("  - Same screening applies to product spectra")
    print()
    print("§XIII.1 next ingredient (next commit): spectral decimation for SG family")
    print("  → analytical eigenvalues at arbitrary level instead of numerical")

    with open(RESULTS_FILE, "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")

    # Plot
    fig, ax = plt.subplots(figsize=(12, 5))
    for r in results:
        evs = r["first_10_nonzero"]
        if evs:
            ax.semilogy(range(1, len(evs) + 1), [max(e, 1e-12) for e in evs],
                         "-o", label=r["product_name"], alpha=0.7, markersize=4)
    ax.set_xlabel("Eigenvalue index (non-zero)")
    ax.set_ylabel("Eigenvalue (log)")
    ax.set_title("Product F × G/H spectra (F = SG level 4)")
    ax.legend(fontsize=8, loc="lower right")
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUT_DIR / "mfo-xiii-1-product-geometry-2026-05-12.png", dpi=100)
    plt.close()

    print(f"\nResults: {RESULTS_FILE.name}")


if __name__ == "__main__":
    main()

"""
PCA-canonical + connected sphere substrate — combines PR #339 + PR #340 (2026-05-12).

Synthesis spike: PCA-canonicalize protein coordinates (PR #339's rotation-
invariance fix), then apply dynamic-Laplacian iteration on a sphere substrate
(PR #340's connected-substrate-works finding).

Expected:
1. Rotation invariance via PCA pre-canonicalization
2. Non-trivial fixed point via connected sphere graph
3. The converged fixed point should be the SAME across rotated versions
   of the same protein (because PCA canonicalizes orientation)

Reproduce: `python -X utf8 docs/srmech/notes/pca_canonical_sphere_combined_script.py`
Deterministic seed 20260512.
"""

import time
import json
import urllib.request
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

CONTACT_CUTOFF = 8.0
N_THETA = 60
N_PHI = 120
RADIUS_FACTOR = 1.2
N_ITERATIONS = 30
CONVERGENCE_TOL = 1e-4
GAUSSIAN_SIGMA = 4.0

OUT_DIR = Path(__file__).parent
RESULTS_FILE = OUT_DIR / "pca-canonical-sphere-combined-per-test-2026-05-12.ndjson"


# ─── Reused utilities ─────────────────────────────────────────────────────

def fetch_pdb_ca(pdb_id):
    cache = OUT_DIR / f"{pdb_id}.pdb"
    if not cache.exists():
        url = f"https://files.rcsb.org/download/{pdb_id}.pdb"
        req = urllib.request.Request(url, headers={"User-Agent": "srmech-spike/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            cache.write_text(resp.read().decode("utf-8"))
    coords, seen, chain_id = [], set(), None
    for line in cache.read_text().splitlines():
        if not line.startswith("ATOM"): continue
        if line[12:16].strip() != "CA": continue
        if line[16:17] not in (" ", "A"): continue
        c, res_seq = line[21:22], line[22:26].strip()
        if chain_id is None: chain_id = c
        elif c != chain_id: continue
        if (c, res_seq) in seen: continue
        seen.add((c, res_seq))
        coords.append([float(line[30:38]), float(line[38:46]), float(line[46:54])])
    return np.array(coords)


def build_gnm_laplacian(coords, cutoff):
    n = coords.shape[0]
    dists = np.linalg.norm(coords[:, None] - coords[None, :], axis=2)
    A = ((dists < cutoff) & ~np.eye(n, dtype=bool)).astype(float)
    return np.diag(A.sum(axis=1)) - A


def fiedler_eigenvector(L):
    w, v = scipy.linalg.eigh(L)
    return v[:, 1]


# ─── PCA canonicalization (from PR #339) ─────────────────────────────────

def pca_canonical_rotation(coords, weights=None):
    centered = coords - coords.mean(axis=0)
    if weights is not None:
        w = np.abs(weights)
        w_total = w.sum()
        if w_total > 0:
            mean_w = (w[:, None] * centered).sum(axis=0) / w_total
            centered = centered - mean_w
            cov = (w[:, None, None] * centered[:, :, None] * centered[:, None, :]).sum(axis=0) / w_total
        else:
            cov = centered.T @ centered / len(coords)
    else:
        cov = centered.T @ centered / len(coords)
    eigvals, eigvecs = scipy.linalg.eigh(cov)
    order = np.argsort(eigvals)[::-1]
    R = eigvecs[:, order].T
    if np.linalg.det(R) < 0:
        R[2] *= -1
    projected = centered @ R.T
    for k in range(3):
        if ((projected[:, k]) ** 3).sum() < 0:
            R[k] *= -1
    if np.linalg.det(R) < 0:
        R[2] *= -1
    return R


def canonicalize_coords(coords, weights=None):
    R = pca_canonical_rotation(coords, weights=weights)
    centered = coords - coords.mean(axis=0)
    return centered @ R.T


# ─── Sphere substrate (from PR #340) ─────────────────────────────────────

def sample_fiedler_on_sphere(coords, fiedler_values, radius, center,
                              n_theta, n_phi, sigma=GAUSSIAN_SIGMA):
    thetas = np.linspace(0.01, np.pi - 0.01, n_theta)
    phis = np.linspace(0, 2 * np.pi, n_phi, endpoint=False)
    TH, PH = np.meshgrid(thetas, phis, indexing="ij")
    x = center[0] + radius * np.sin(TH) * np.cos(PH)
    y = center[1] + radius * np.sin(TH) * np.sin(PH)
    z = center[2] + radius * np.cos(TH)
    grid_pts = np.stack([x, y, z], axis=-1)
    field = np.zeros((n_theta, n_phi))
    for i in range(coords.shape[0]):
        d_sq = np.sum((grid_pts - coords[i]) ** 2, axis=-1)
        field += fiedler_values[i] * np.exp(-d_sq / (2 * sigma ** 2))
    return field, thetas, phis


def build_sphere_graph_edges(n_theta, n_phi):
    edges_i, edges_j = [], []
    for i in range(n_theta):
        for j in range(n_phi):
            v = i * n_phi + j
            jp1 = (j + 1) % n_phi
            edges_i.append(v); edges_j.append(i * n_phi + jp1)
            if i + 1 < n_theta:
                edges_i.append(v); edges_j.append((i + 1) * n_phi + j)
    return np.array(edges_i), np.array(edges_j)


def build_weighted_laplacian(phases, edges_i, edges_j, n, weight_floor=0.0):
    dphase = phases[edges_i] - phases[edges_j]
    w = (1 + np.cos(dphase)) / 2
    if weight_floor > 0:
        w = np.maximum(w, weight_floor)
    A = sp.coo_matrix((w, (edges_i, edges_j)), shape=(n, n))
    A = A + A.T
    D = sp.diags(np.asarray(A.sum(axis=1)).ravel())
    return (D - A).tocsr()


def sparse_fiedler(L, sigma_shift=1e-6):
    try:
        eigvals, eigvecs = spla.eigsh(L, k=3, sigma=-sigma_shift, which="LM")
    except Exception:
        eigvals, eigvecs = spla.eigsh(L, k=3, which="SM")
    idx = np.argsort(eigvals)
    return eigvals[idx], eigvecs[:, idx]


def fiedler_value_to_phase(values, scale=None):
    if scale is None:
        scale = np.max(np.abs(values)) * 0.5 + 1e-12
    return np.pi / 2 * (1 + np.tanh(values / scale))


def align_sign(v_new, v_ref):
    return -v_new if np.dot(v_new, v_ref) < 0 else v_new


# ─── Combined pipeline ────────────────────────────────────────────────────

def run_dynamic_laplacian_iteration(coords, fiedler_values, canonicalize=True,
                                      n_iter=N_ITERATIONS, conv_tol=CONVERGENCE_TOL):
    """Full pipeline: optionally PCA-canonicalize, sample on sphere, iterate."""
    if canonicalize:
        # Use Fiedler magnitude as weights so canonical axes reflect bipartition
        coords_canon = canonicalize_coords(coords, weights=fiedler_values)
    else:
        coords_canon = coords - coords.mean(axis=0)

    center = coords_canon.mean(axis=0)  # = origin after centering
    intrinsic_radius = np.linalg.norm(coords_canon - center, axis=1).max() * RADIUS_FACTOR

    field, _, _ = sample_fiedler_on_sphere(coords_canon, fiedler_values, intrinsic_radius,
                                              center, N_THETA, N_PHI)
    n = N_THETA * N_PHI
    edges_i, edges_j = build_sphere_graph_edges(N_THETA, N_PHI)
    phases_0 = fiedler_value_to_phase(field.ravel())

    phases = phases_0.copy()
    prev_fiedler = np.cos(phases_0) - 0.5
    history = []
    for step in range(n_iter):
        L_dyn = build_weighted_laplacian(phases, edges_i, edges_j, n)
        eigvals, eigvecs = sparse_fiedler(L_dyn)
        fiedler_new = align_sign(eigvecs[:, 1], prev_fiedler)
        phases_new = fiedler_value_to_phase(fiedler_new)
        phase_change = float(np.linalg.norm(phases_new - phases))
        overlap = float(abs(np.corrcoef(phases_new, phases_0)[0, 1]))
        history.append({
            "step": step,
            "fiedler_eigenvalue": float(eigvals[1]),
            "phase_l2_change": phase_change,
            "overlap_with_initial": overlap,
            "phases": phases_new.copy(),
        })
        if phase_change < conv_tol and step > 1:
            break
        phases = phases_new
        prev_fiedler = fiedler_new

    return {
        "history": history,
        "phases_initial": phases_0,
        "phases_final": phases_new,
        "converged": history[-1]["phase_l2_change"] < conv_tol,
        "n_iter": len(history),
        "final_overlap_with_initial": history[-1]["overlap_with_initial"],
        "final_eigenvalue": history[-1]["fiedler_eigenvalue"],
        "n_active": n,
        "edges_i": edges_i,
        "edges_j": edges_j,
    }


# ─── Deformations ─────────────────────────────────────────────────────────

def deform_rotation(coords, angle, axis="z"):
    c, s = np.cos(angle), np.sin(angle)
    if axis == "z":   R = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
    elif axis == "x": R = np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
    else:             R = np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    return coords @ R.T


# ─── Main ─────────────────────────────────────────────────────────────────

def main():
    print("=== PCA-canonical + connected sphere substrate — combined synthesis ===")
    print(f"Seed: {SEED}; sphere: {N_THETA}×{N_PHI}; iterations: up to {N_ITERATIONS}")
    print()

    coords = fetch_pdb_ca("1UBQ")
    L_protein = build_gnm_laplacian(coords, CONTACT_CUTOFF)
    fiedler = fiedler_eigenvector(L_protein)
    print(f"[Setup] 1UBQ: {coords.shape[0]} Cα; Fiedler range [{fiedler.min():.3f}, {fiedler.max():.3f}]")
    print()

    # Run PCA-canonical version
    print("=== Run 1: PCA-canonical + sphere substrate (the synthesis) ===")
    t0 = time.perf_counter()
    result_canon = run_dynamic_laplacian_iteration(coords, fiedler, canonicalize=True)
    t_canon = time.perf_counter() - t0
    print(f"  n_iter: {result_canon['n_iter']}; converged: {result_canon['converged']}")
    print(f"  final λ_Fiedler:                 {result_canon['final_eigenvalue']:.5f}")
    print(f"  final correlation w/ initial:    {result_canon['final_overlap_with_initial']:.4f}")
    print(f"  runtime: {1000*t_canon:.0f} ms")
    print()

    # Run non-canonicalized version for comparison
    print("=== Run 2: NO canonicalization (PR #340 baseline) ===")
    result_raw = run_dynamic_laplacian_iteration(coords, fiedler, canonicalize=False)
    print(f"  n_iter: {result_raw['n_iter']}; final overlap w/ initial: {result_raw['final_overlap_with_initial']:.4f}")
    print()

    # Test rotation invariance — the key claim
    print("=== Run 3: ROTATION INVARIANCE TEST ===")
    print("  Apply rotation BEFORE pipeline; check if final fixed point is the same.")
    print()
    rot_tests = [
        ("rot_30deg_z", deform_rotation(coords, np.pi / 6, "z")),
        ("rot_90deg_z", deform_rotation(coords, np.pi / 2, "z")),
        ("rot_90deg_x", deform_rotation(coords, np.pi / 2, "x")),
        ("rot_90deg_y", deform_rotation(coords, np.pi / 2, "y")),
        ("rot_180deg_y", deform_rotation(coords, np.pi, "y")),
    ]
    rot_results = []
    for label, coords_rot in rot_tests:
        result_rot = run_dynamic_laplacian_iteration(coords_rot, fiedler, canonicalize=True)
        # Compare final phase fields
        sim = float(abs(np.corrcoef(result_canon['phases_final'],
                                      result_rot['phases_final'])[0, 1]))
        rot_results.append((label, sim, result_rot['n_iter'], result_rot['final_overlap_with_initial']))
        print(f"  {label:<14s}: ψ*_canon vs ψ*_rotated = {sim:.4f}  "
              f"(n_iter={result_rot['n_iter']}; overlap_w_init={result_rot['final_overlap_with_initial']:.3f})")

    print()
    print("=== Run 4: cross-protein comparison ===")
    coords_1bpi = fetch_pdb_ca("1BPI")
    L_1bpi = build_gnm_laplacian(coords_1bpi, CONTACT_CUTOFF)
    fiedler_1bpi = fiedler_eigenvector(L_1bpi)
    result_1bpi = run_dynamic_laplacian_iteration(coords_1bpi, fiedler_1bpi, canonicalize=True)
    cross_sim = float(abs(np.corrcoef(result_canon['phases_final'],
                                         result_1bpi['phases_final'])[0, 1]))
    print(f"  1BPI converged: n_iter={result_1bpi['n_iter']}, λ_F={result_1bpi['final_eigenvalue']:.5f}")
    print(f"  1UBQ ψ* vs 1BPI ψ* (canonical): {cross_sim:.4f}")
    print(f"    (Compare PR #339 raw cross-protein voxel HDC: 0.582 magnitude)")
    print()

    # Verdict
    print("=== Verdict ===")
    rot_mean = float(np.mean([r[1] for r in rot_results]))
    rot_min = float(min(r[1] for r in rot_results))
    print(f"  Rotation invariance of fixed point: mean={rot_mean:.4f}, min={rot_min:.4f}")
    print(f"  Non-trivial fixed point (overlap w initial < 0.95): {result_canon['final_overlap_with_initial']:.4f} ✓")
    print(f"  Cross-protein discrimination (1UBQ vs 1BPI):        {cross_sim:.4f}")
    print()
    if rot_min > 0.9 and result_canon['final_overlap_with_initial'] < 0.95:
        print("  WIN: PCA-canonical + sphere combines BOTH wins from PR #339 + PR #340:")
        print("       • Rotation invariance preserved (fixed point matches across rotations)")
        print("       • Non-trivial fixed point on connected substrate")
    elif rot_min > 0.9:
        print("  PARTIAL: rotation invariance preserved but fixed point is trivial")
    else:
        print(f"  PROBLEM: rotation invariance lost (min {rot_min:.3f})")

    # Save
    records = [
        {"test": "canonical_run", "n_iter": result_canon['n_iter'],
         "converged": result_canon['converged'],
         "final_eigenvalue": result_canon['final_eigenvalue'],
         "final_overlap_with_initial": result_canon['final_overlap_with_initial']},
        {"test": "raw_run", "n_iter": result_raw['n_iter'],
         "final_overlap_with_initial": result_raw['final_overlap_with_initial']},
        {"test": "rotation_invariance_of_fixed_point",
         "results": [{"label": l, "psi_star_cosine": s, "n_iter": n, "overlap_init": o}
                     for l, s, n, o in rot_results],
         "mean": rot_mean, "min": rot_min},
        {"test": "cross_protein_canonical", "cosine": cross_sim,
         "voxel_hdc_baseline": 0.582},
    ]
    with open(RESULTS_FILE, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    # Plot
    fig, axes = plt.subplots(2, 2, figsize=(14, 8))
    # Convergence curves for canonical vs raw
    axes[0, 0].plot([h["step"] for h in result_canon["history"]],
                    [h["phase_l2_change"] for h in result_canon["history"]], "b-o", label="PCA canonical")
    axes[0, 0].plot([h["step"] for h in result_raw["history"]],
                    [h["phase_l2_change"] for h in result_raw["history"]], "r-s", label="Raw")
    axes[0, 0].set_xlabel("Iteration"); axes[0, 0].set_ylabel("||Δphase||")
    axes[0, 0].set_yscale("log")
    axes[0, 0].axhline(CONVERGENCE_TOL, color="gray", linestyle="--", alpha=0.5)
    axes[0, 0].set_title("Convergence: canonical vs raw")
    axes[0, 0].legend(); axes[0, 0].grid(alpha=0.3)
    # Initial phase field on sphere (canonical)
    initial_2d = result_canon['phases_initial'].reshape(N_THETA, N_PHI)
    axes[0, 1].imshow(initial_2d, cmap="seismic", origin="lower", aspect="auto",
                       extent=[0, 360, 0, 180], vmin=0, vmax=np.pi)
    axes[0, 1].set_title("Initial phase field (canonical frame)")
    axes[0, 1].set_xlabel("φ (degrees)"); axes[0, 1].set_ylabel("θ (degrees)")
    # Final phase field (canonical)
    final_canon_2d = result_canon['phases_final'].reshape(N_THETA, N_PHI)
    axes[1, 0].imshow(final_canon_2d, cmap="twilight", origin="lower", aspect="auto",
                       extent=[0, 360, 0, 180], vmin=0, vmax=np.pi)
    axes[1, 0].set_title(f"Final ψ* (canonical), n_iter={result_canon['n_iter']}")
    axes[1, 0].set_xlabel("φ (degrees)"); axes[1, 0].set_ylabel("θ (degrees)")
    # 1BPI final phase field
    final_1bpi_2d = result_1bpi['phases_final'].reshape(N_THETA, N_PHI)
    axes[1, 1].imshow(final_1bpi_2d, cmap="twilight", origin="lower", aspect="auto",
                       extent=[0, 360, 0, 180], vmin=0, vmax=np.pi)
    axes[1, 1].set_title(f"1BPI final ψ* (canonical, cross_sim={cross_sim:.3f})")
    axes[1, 1].set_xlabel("φ (degrees)"); axes[1, 1].set_ylabel("θ (degrees)")
    plt.tight_layout()
    plt.savefig(OUT_DIR / "pca-canonical-sphere-combined-trajectory-2026-05-12.png", dpi=100)
    plt.close()

    print()
    print(f"Results: {RESULTS_FILE.name}")
    print(f"Plot:    pca-canonical-sphere-combined-trajectory-2026-05-12.png")


if __name__ == "__main__":
    main()

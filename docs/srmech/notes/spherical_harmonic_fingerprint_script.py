"""
Spherical harmonic fingerprint — SO(3)-invariant alternative to voxel HDC (2026-05-12).

Follow-up to PR #336 finding that voxel HDC encoding is NOT rotation-invariant
(cubic-lattice O_h symmetry, not continuous SO(3)). User's question chain has
been building toward this: PR #335 falsified naive dynamic-Laplacian; PR #336
characterized the cubic-symmetry-breaking of voxel encoding; this PR tests
the principled fix.

Approach: project the voxel scalar field onto spherical harmonics over
concentric spheres centered at the protein centroid. Use the rotation-
invariant POWER SPECTRUM P_l(r) = Σ_m |C_lm(r)|² as fingerprint.

This IS the MFO §VII.4.1.1 spherical compression operator applied to real
protein data: 3D bulk field → 2D boundary spherical-harmonic decomposition
→ power spectrum per shell.

Tests:
1. Self-similarity = 1.0 (sanity)
2. Translation invariance (centroid recentering)
3. Scale invariance (radius rescaling)
4. **Rotation invariance** — the load-bearing test
5. Cross-protein discrimination (1UBQ vs 1BPI) — does signal survive?

Reproduce: `python -X utf8 docs/srmech/notes/spherical_harmonic_fingerprint_script.py`
Deterministic seed 20260512. Uses scipy.special.sph_harm_y.
"""

import time
import json
import urllib.request
import numpy as np
import scipy.linalg
import scipy.special
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

SEED = 20260512
RNG = np.random.default_rng(SEED)

CONTACT_CUTOFF = 8.0
VOXEL_N = 64
GAUSSIAN_SIGMA = 4.0
L_MAX = 20          # spherical harmonic max degree — increased for cross-protein discrim
N_SHELLS = 8        # more concentric shells for radial detail
N_THETA = 80        # polar angles for SH quadrature
N_PHI = 160         # azimuthal angles

OUT_DIR = Path(__file__).parent
RESULTS_FILE = OUT_DIR / "spherical-harmonic-fingerprint-per-test-2026-05-12.ndjson"


# ─── PDB loading ──────────────────────────────────────────────────────────

def fetch_pdb_ca(pdb_id: str) -> np.ndarray:
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


def voxelize_scalar(coords, values, n_voxels, sigma):
    bbox_min = coords.min(axis=0) - 3 * sigma
    bbox_max = coords.max(axis=0) + 3 * sigma
    axes = [np.linspace(bbox_min[d], bbox_max[d], n_voxels) for d in range(3)]
    gx, gy, gz = np.meshgrid(axes[0], axes[1], axes[2], indexing="ij")
    grid = np.stack([gx, gy, gz], axis=-1)
    field = np.zeros((n_voxels, n_voxels, n_voxels))
    for i in range(coords.shape[0]):
        d_sq = np.sum((grid - coords[i]) ** 2, axis=-1)
        field += values[i] * np.exp(-d_sq / (2 * sigma ** 2))
    return field, np.stack(axes)


# ─── Spherical harmonic fingerprint ──────────────────────────────────────

def sample_field_on_sphere(field, axes, center, radius, n_theta, n_phi):
    """Sample 3D scalar field on a sphere of given radius via trilinear interp."""
    thetas = np.linspace(0, np.pi, n_theta)
    phis = np.linspace(0, 2 * np.pi, n_phi, endpoint=False)
    TH, PH = np.meshgrid(thetas, phis, indexing="ij")
    # Sphere points in 3D
    x = center[0] + radius * np.sin(TH) * np.cos(PH)
    y = center[1] + radius * np.sin(TH) * np.sin(PH)
    z = center[2] + radius * np.cos(TH)
    # Trilinear interp from voxel field
    def interp_axis(coords_1d, axis):
        idx_f = (coords_1d - axis[0]) / (axis[-1] - axis[0]) * (len(axis) - 1)
        idx_f = np.clip(idx_f, 0, len(axis) - 1.001)
        return idx_f
    ix = interp_axis(x.ravel(), axes[0])
    iy = interp_axis(y.ravel(), axes[1])
    iz = interp_axis(z.ravel(), axes[2])
    ix0, iy0, iz0 = np.floor(ix).astype(int), np.floor(iy).astype(int), np.floor(iz).astype(int)
    dx, dy, dz = ix - ix0, iy - iy0, iz - iz0
    # 8 corners
    f000 = field[ix0, iy0, iz0]
    f100 = field[ix0 + 1, iy0, iz0]
    f010 = field[ix0, iy0 + 1, iz0]
    f001 = field[ix0, iy0, iz0 + 1]
    f110 = field[ix0 + 1, iy0 + 1, iz0]
    f101 = field[ix0 + 1, iy0, iz0 + 1]
    f011 = field[ix0, iy0 + 1, iz0 + 1]
    f111 = field[ix0 + 1, iy0 + 1, iz0 + 1]
    vals = (f000 * (1 - dx) * (1 - dy) * (1 - dz)
            + f100 * dx * (1 - dy) * (1 - dz)
            + f010 * (1 - dx) * dy * (1 - dz)
            + f001 * (1 - dx) * (1 - dy) * dz
            + f110 * dx * dy * (1 - dz)
            + f101 * dx * (1 - dy) * dz
            + f011 * (1 - dx) * dy * dz
            + f111 * dx * dy * dz)
    return vals.reshape(n_theta, n_phi), thetas, phis


def precompute_ylm_grid(l_max, thetas, phis):
    """Precompute all Y_lm(θ, φ) once. Returns dict {(l,m): array}."""
    cache = {}
    for l in range(l_max + 1):
        for m in range(-l, l + 1):
            cache[(l, m)] = scipy.special.sph_harm_y(l, m, thetas[:, None], phis[None, :])
    return cache


_YLM_CACHE = {"key": None, "data": None, "weights": None, "thetas": None, "phis": None}


def get_ylm_cache(l_max, n_theta, n_phi):
    """Cached precompute of Y_lm grid + quadrature weights."""
    key = (l_max, n_theta, n_phi)
    if _YLM_CACHE["key"] == key:
        return _YLM_CACHE["data"], _YLM_CACHE["weights"], _YLM_CACHE["thetas"], _YLM_CACHE["phis"]
    thetas = np.linspace(0, np.pi, n_theta)
    phis = np.linspace(0, 2 * np.pi, n_phi, endpoint=False)
    print(f"[SH cache] Precomputing Y_lm for l_max={l_max}, grid {n_theta}×{n_phi}...", end=" ", flush=True)
    t0 = time.perf_counter()
    cache = precompute_ylm_grid(l_max, thetas, phis)
    dtheta = thetas[1] - thetas[0]
    dphi = phis[1] - phis[0]
    weights = np.sin(thetas)[:, None] * dtheta * dphi
    print(f"done ({1000*(time.perf_counter()-t0):.0f} ms; {len(cache)} (l,m) pairs)")
    _YLM_CACHE.update({"key": key, "data": cache, "weights": weights, "thetas": thetas, "phis": phis})
    return cache, weights, thetas, phis


def sh_power_spectrum(f_sphere, thetas, phis, l_max):
    """Vectorized: P_l = Σ_m |C_lm|^2 using precomputed Y_lm cache."""
    n_theta = len(thetas)
    n_phi = len(phis)
    ylm_cache, weights, _, _ = get_ylm_cache(l_max, n_theta, n_phi)
    f_weighted = f_sphere * weights
    P_l = np.zeros(l_max + 1)
    for l in range(l_max + 1):
        for m in range(-l, l + 1):
            c_lm = np.sum(f_weighted * np.conj(ylm_cache[(l, m)]))
            P_l[l] += abs(c_lm) ** 2
    return P_l


def sh_fingerprint(field, axes, l_max, n_shells, n_theta, n_phi, coords_for_scale=None):
    """
    Compute SO(3)-invariant fingerprint: power spectrum P_l(r) for r in
    concentric shells.

    If coords_for_scale is provided, use the protein's intrinsic bbox to scale
    radii — this gives scale invariance (radii adapt to protein size).

    Returns: array of shape (n_shells, l_max + 1).
    """
    bbox_min = axes[:, 0]
    bbox_max = axes[:, -1]
    center = (bbox_min + bbox_max) / 2

    if coords_for_scale is not None:
        # Use protein's intrinsic radius (gyration-like) for scale-invariant radii
        protein_center = coords_for_scale.mean(axis=0)
        center = protein_center  # center on protein, not voxel-bbox
        intrinsic_radius = np.linalg.norm(coords_for_scale - protein_center, axis=1).max()
        max_radius = intrinsic_radius * 1.5  # extend beyond protein
    else:
        max_radius = np.min(bbox_max - bbox_min) / 2 * 0.95

    radii = np.linspace(max_radius * 0.2, max_radius * 0.95, n_shells)

    fingerprint = np.zeros((n_shells, l_max + 1))
    for r_idx, r in enumerate(radii):
        f_sphere, thetas, phis = sample_field_on_sphere(field, axes, center, r, n_theta, n_phi)
        P_l = sh_power_spectrum(f_sphere, thetas, phis, l_max)
        fingerprint[r_idx] = P_l
    return fingerprint, radii


def cosine_similarity(a, b):
    a, b = a.ravel(), b.ravel()
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    return float(np.dot(a, b) / (na * nb)) if na * nb > 0 else None


# ─── Deformations (from PR #336) ─────────────────────────────────────────

def deform_rotation(coords, angle, axis="z"):
    c, s = np.cos(angle), np.sin(angle)
    if axis == "z":
        R = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
    elif axis == "x":
        R = np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
    else:
        R = np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    return coords @ R.T


def deform_translation(coords, shift_vec):
    return coords + shift_vec


def deform_uniform_scale(coords, alpha):
    return alpha * coords


def deform_thermal_noise(coords, magnitude):
    return coords + magnitude * RNG.standard_normal(coords.shape)


# ─── Main ─────────────────────────────────────────────────────────────────

def compute_sh_fingerprint_for_coords(coords, fiedler_values, scale_invariant=True):
    field, axes = voxelize_scalar(coords, fiedler_values, VOXEL_N, GAUSSIAN_SIGMA)
    fp, radii = sh_fingerprint(field, axes, L_MAX, N_SHELLS, N_THETA, N_PHI,
                               coords_for_scale=coords if scale_invariant else None)
    return fp


def main():
    print("=== Spherical harmonic SO(3)-invariant fingerprint ===")
    print(f"Seed: {SEED}; voxel: {VOXEL_N}^3; l_max: {L_MAX}; shells: {N_SHELLS}")
    print(f"Angular grid: {N_THETA} × {N_PHI}")
    print()

    # ─── 1UBQ baseline ─────────────────────────────────────────────────────
    coords_1ubq = fetch_pdb_ca("1UBQ")
    L_1ubq = build_gnm_laplacian(coords_1ubq, CONTACT_CUTOFF)
    fiedler_1ubq = fiedler_eigenvector(L_1ubq)
    print(f"[Setup] 1UBQ: {coords_1ubq.shape[0]} Cα")

    t0 = time.perf_counter()
    fp_1ubq = compute_sh_fingerprint_for_coords(coords_1ubq, fiedler_1ubq)
    t_fingerprint = time.perf_counter() - t0
    print(f"        SH fingerprint computed in {1000*t_fingerprint:.0f} ms")
    print(f"        Shape: {fp_1ubq.shape} = ({N_SHELLS} shells × {L_MAX + 1} l-modes) = {fp_1ubq.size} dims")
    print()

    print("=== TEST 1: Self-similarity (must = 1.0) ===")
    self_sim = cosine_similarity(fp_1ubq, fp_1ubq)
    print(f"  cosine(1UBQ, 1UBQ) = {self_sim:.6f}")
    print()

    print("=== TEST 2: Rotation invariance — THE LOAD-BEARING TEST ===")
    rotation_tests = [
        ("rot_30deg_z",  deform_rotation(coords_1ubq, np.pi / 6, "z")),
        ("rot_90deg_z",  deform_rotation(coords_1ubq, np.pi / 2, "z")),
        ("rot_180deg_z", deform_rotation(coords_1ubq, np.pi, "z")),
        ("rot_90deg_x",  deform_rotation(coords_1ubq, np.pi / 2, "x")),
        ("rot_90deg_y",  deform_rotation(coords_1ubq, np.pi / 2, "y")),
    ]
    rotation_results = []
    for label, rotated_coords in rotation_tests:
        fp_rotated = compute_sh_fingerprint_for_coords(rotated_coords, fiedler_1ubq)
        cos_sim = cosine_similarity(fp_1ubq, fp_rotated)
        rotation_results.append((label, cos_sim))
        print(f"  {label:<16s}: SH cosine = {cos_sim:.6f}  (PR #336 voxel-HDC was 0.14 at 90°)")

    print()
    print("=== TEST 3: Translation invariance ===")
    coords_trans = deform_translation(coords_1ubq, np.array([10.0, 0, 0]))
    fp_trans = compute_sh_fingerprint_for_coords(coords_trans, fiedler_1ubq)
    cos_trans = cosine_similarity(fp_1ubq, fp_trans)
    print(f"  translation_10Å: SH cosine = {cos_trans:.6f}")
    print()

    print("=== TEST 4: Scale invariance ===")
    for alpha in [0.8, 1.2, 2.0]:
        coords_scaled = deform_uniform_scale(coords_1ubq, alpha)
        fp_scaled = compute_sh_fingerprint_for_coords(coords_scaled, fiedler_1ubq)
        cos_scale = cosine_similarity(fp_1ubq, fp_scaled)
        print(f"  uniform_scale_α={alpha}: SH cosine = {cos_scale:.6f}")
    print()

    print("=== TEST 5: Thermal noise ===")
    for noise in [0.5, 2.0, 5.0]:
        coords_noisy = deform_thermal_noise(coords_1ubq, noise)
        fp_noisy = compute_sh_fingerprint_for_coords(coords_noisy, fiedler_1ubq)
        cos_noisy = cosine_similarity(fp_1ubq, fp_noisy)
        print(f"  thermal_{noise}Å: SH cosine = {cos_noisy:.6f}")
    print()

    print("=== TEST 6: Cross-protein discrimination (1UBQ vs 1BPI) ===")
    coords_1bpi = fetch_pdb_ca("1BPI")
    L_1bpi = build_gnm_laplacian(coords_1bpi, CONTACT_CUTOFF)
    fiedler_1bpi = fiedler_eigenvector(L_1bpi)
    fp_1bpi = compute_sh_fingerprint_for_coords(coords_1bpi, fiedler_1bpi)
    cos_cross = cosine_similarity(fp_1ubq, fp_1bpi)
    print(f"  1UBQ vs 1BPI: SH cosine = {cos_cross:.6f}")
    print(f"  PR #333 voxel-HDC sign-only: cosine = -0.343 (different proteins)")
    print()

    # Bonus: rotation-invariance vs THE SAME 1BPI rotated
    coords_1bpi_rot = deform_rotation(coords_1bpi, np.pi / 4, "y")
    fp_1bpi_rot = compute_sh_fingerprint_for_coords(coords_1bpi_rot, fiedler_1bpi)
    cos_1bpi_self_rot = cosine_similarity(fp_1bpi, fp_1bpi_rot)
    print(f"  1BPI vs 1BPI rotated 45° y: SH cosine = {cos_1bpi_self_rot:.6f}")
    print()

    # ─── Summary ───────────────────────────────────────────────────────────
    print("=== Summary ===")
    print(f"  Self-similarity:         {self_sim:.4f}  (expect 1.0)")
    print(f"  Rotation (mean):         {np.mean([r[1] for r in rotation_results]):.4f}  (expect 1.0 if SO(3)-invariant)")
    print(f"  Rotation (min):          {min(r[1] for r in rotation_results):.4f}")
    print(f"  Rotation (worst case):   {min(r[1] for r in rotation_results):.4f}  ← KEY METRIC")
    print(f"  Translation:             {cos_trans:.4f}")
    print(f"  Scale α=2.0:             see above")
    print(f"  Cross-protein:           {cos_cross:.4f}")

    # ─── Verdict ───────────────────────────────────────────────────────────
    print()
    print("=== Verdict ===")
    rot_mean = float(np.mean([r[1] for r in rotation_results]))
    rot_min = float(min(r[1] for r in rotation_results))
    if rot_min > 0.99:
        print(f"  SO(3) INVARIANCE CONFIRMED: rotation cosine min={rot_min:.4f} (machine precision)")
        print(f"  Fix for PR #336 rotation-breaking issue: SH power spectrum works.")
    elif rot_min > 0.95:
        print(f"  SO(3) NEAR-INVARIANT: rotation cosine min={rot_min:.4f} (discretization error)")
    else:
        print(f"  SO(3) NOT recovered: rotation cosine min={rot_min:.4f}")
        print(f"  Quadrature error or implementation bug; needs investigation.")

    if cos_cross is not None and abs(cos_cross) < 0.95:
        print(f"  Cross-protein discrimination preserved: 1UBQ vs 1BPI = {cos_cross:.4f}")
    else:
        print(f"  ⚠ Cross-protein similarity too high ({cos_cross:.4f}) — fingerprint may have lost information")

    # ─── Save results ──────────────────────────────────────────────────────
    records = [
        {"test": "self_similarity", "cosine": self_sim},
        {"test": "rotation", "results": [{"label": l, "cosine": c} for l, c in rotation_results],
         "mean": rot_mean, "min": rot_min},
        {"test": "translation_10A", "cosine": cos_trans},
        {"test": "cross_protein_1ubq_1bpi", "cosine": cos_cross},
        {"test": "rotation_1bpi_self_rotated", "cosine": cos_1bpi_self_rot},
        {"test": "config",
         "voxel_n": VOXEL_N, "l_max": L_MAX, "n_shells": N_SHELLS,
         "n_theta": N_THETA, "n_phi": N_PHI},
    ]
    with open(RESULTS_FILE, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    # ─── Plot ──────────────────────────────────────────────────────────────
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    # Plot 1UBQ vs rotated 1UBQ power spectra
    axes[0].plot(range(L_MAX + 1), fp_1ubq.sum(axis=0), 'k-o', label="1UBQ original")
    for label, rotated_coords in rotation_tests[:3]:
        fp_r = compute_sh_fingerprint_for_coords(rotated_coords, fiedler_1ubq)
        axes[0].plot(range(L_MAX + 1), fp_r.sum(axis=0), alpha=0.5, label=label)
    axes[0].set_xlabel("Spherical harmonic degree l")
    axes[0].set_ylabel("Power Σ_r P_l(r)")
    axes[0].set_yscale("log")
    axes[0].set_title("SH power spectra under rotation")
    axes[0].legend(fontsize=8)
    axes[0].grid(True, alpha=0.3)

    # Plot 1UBQ vs 1BPI
    axes[1].plot(range(L_MAX + 1), fp_1ubq.sum(axis=0), 'b-o', label="1UBQ")
    axes[1].plot(range(L_MAX + 1), fp_1bpi.sum(axis=0), 'r-s', label="1BPI")
    axes[1].set_xlabel("Spherical harmonic degree l")
    axes[1].set_ylabel("Power Σ_r P_l(r)")
    axes[1].set_yscale("log")
    axes[1].set_title("Cross-protein power spectra")
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    # Comparison bar chart
    labels = ["self", "rot_90z", "rot_90x", "rot_90y", "trans", "cross_1bpi"]
    voxel_cosines = [1.000, 0.138, 0.138, 0.138, 1.000, -0.343]  # from PR #336 + #333
    sh_cosines = [self_sim, rotation_results[1][1], rotation_results[3][1],
                  rotation_results[4][1], cos_trans, cos_cross]
    x = np.arange(len(labels))
    width = 0.35
    axes[2].bar(x - width/2, voxel_cosines, width, label="Voxel HDC (PR #336)", color='red', alpha=0.7)
    axes[2].bar(x + width/2, sh_cosines, width, label="SH power spectrum (this PR)", color='green', alpha=0.7)
    axes[2].set_xticks(x)
    axes[2].set_xticklabels(labels, rotation=30, fontsize=9)
    axes[2].set_ylabel("Cosine similarity")
    axes[2].axhline(1.0, color='black', linestyle='--', alpha=0.3)
    axes[2].set_title("Voxel HDC vs SH power spectrum — rotation behavior")
    axes[2].legend(loc='lower right', fontsize=8)
    axes[2].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(OUT_DIR / "spherical-harmonic-fingerprint-comparison-2026-05-12.png", dpi=100)
    plt.close()

    print()
    print(f"Results: {RESULTS_FILE.name}")
    print(f"Plot:    spherical-harmonic-fingerprint-comparison-2026-05-12.png")


if __name__ == "__main__":
    main()

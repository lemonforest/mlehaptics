"""
3D Zernike moment fingerprint — SO(3)-invariant with better discrimination (2026-05-12).

Follow-up to PR #337 finding that SH power spectrum recovers SO(3) invariance
but loses cross-protein discrimination. Flagged as "next natural primitive":
3D Zernike moments combine radial polynomial basis with angular spherical
harmonics, giving more information than the SH-power-only collapse while
remaining SO(3)-invariant.

3D Zernike basis: Z_nlm(r, θ, φ) = R_nl(r) · Y_lm(θ, φ) on the unit ball.
- R_nl(r): Zernike radial polynomial (degree n, l-dependent)
- Constraint: n ≥ l and (n - l) even
- Moment: Ω_nlm = ∫_{ball} f(r, θ, φ) Z*_nlm dV
- SO(3)-invariant fingerprint: F_nl = Σ_m |Ω_nlm|²
  (Wigner-D mixes m-modes within fixed l; F_nl preserved)

This is FORMALLY equivalent to "SH per radial polynomial mode" — captures
more radial structure than the SH-power-per-shell approach in PR #337.

Reference: Canterakis 1999, Novotni & Klein 2003.

Reproduce: `python -X utf8 docs/srmech/notes/zernike_3d_fingerprint_script.py`
Deterministic seed 20260512. Uses cached PDB from PR #333.
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
from math import comb, factorial

SEED = 20260512
RNG = np.random.default_rng(SEED)

CONTACT_CUTOFF = 8.0
VOXEL_N = 64
GAUSSIAN_SIGMA = 4.0
N_MAX = 10  # Zernike maximum order
N_RADIAL = 30  # radial grid points
N_THETA = 50
N_PHI = 100

OUT_DIR = Path(__file__).parent
RESULTS_FILE = OUT_DIR / "zernike-3d-fingerprint-per-test-2026-05-12.ndjson"


# ─── PDB + Fiedler + voxelization (reused) ────────────────────────────────

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


# ─── 3D Zernike radial polynomials ────────────────────────────────────────

def zernike_radial(n, l, r):
    """
    3D Zernike radial polynomial R_nl(r) for n ≥ l, (n-l) even, r ∈ [0, 1].
    Formula: R_nl(r) = Σ_{s=0}^{(n-l)/2} (-1)^s · C(2n+1, s) · C(n-s, (n-l)/2 - s) · r^(n - 2s)
    Following Canterakis 1999 normalization.
    """
    if n < l or (n - l) % 2 != 0:
        return np.zeros_like(r)
    k = (n - l) // 2
    result = np.zeros_like(r)
    for s in range(k + 1):
        coeff = ((-1) ** s
                 * factorial(2 * n + 1 - s)
                 // (factorial(s) * factorial(n + l - s + 1) * factorial(n - l - 2 * s)))
        # Avoid integer overflow — use float
        coeff = float(coeff)
        result += coeff * r ** (n - 2 * s)
    return result


def get_valid_nl_pairs(n_max):
    """All (n, l) pairs with n ≤ n_max, n ≥ l, (n-l) even."""
    pairs = []
    for n in range(n_max + 1):
        for l in range(n + 1):
            if (n - l) % 2 == 0:
                pairs.append((n, l))
    return pairs


_ZERNIKE_CACHE = {"key": None, "data": None}


def precompute_zernike_basis(n_max, n_radial, n_theta, n_phi):
    """Precompute Z_nlm(r, θ, φ) on grid. Returns dict + radial weights."""
    key = (n_max, n_radial, n_theta, n_phi)
    if _ZERNIKE_CACHE["key"] == key:
        return _ZERNIKE_CACHE["data"]
    print(f"[Zernike cache] Precomputing Z_nlm for n_max={n_max}, radial×θ×φ={n_radial}×{n_theta}×{n_phi}...", flush=True)
    t0 = time.perf_counter()

    rs = np.linspace(0.01, 0.99, n_radial)  # avoid r=0 singularity
    thetas = np.linspace(0.01, np.pi - 0.01, n_theta)
    phis = np.linspace(0, 2 * np.pi, n_phi, endpoint=False)

    # Radial polynomials R_nl(r)
    nl_pairs = get_valid_nl_pairs(n_max)
    r_polys = {}
    for n, l in nl_pairs:
        r_polys[(n, l)] = zernike_radial(n, l, rs)

    # Spherical harmonics Y_lm(θ, φ)
    sh_cache = {}
    l_set = set(l for n, l in nl_pairs)
    for l in l_set:
        for m in range(-l, l + 1):
            sh_cache[(l, m)] = scipy.special.sph_harm_y(l, m, thetas[:, None], phis[None, :])

    # Integration weights: dV = r² sin(θ) dr dθ dφ
    dr = rs[1] - rs[0]
    dtheta = thetas[1] - thetas[0]
    dphi = phis[1] - phis[0]
    radial_w = (rs ** 2 * dr)[:, None, None]      # (n_radial, 1, 1)
    angular_w = (np.sin(thetas) * dtheta * dphi)[None, :, None]  # (1, n_theta, 1)
    dV = radial_w * angular_w   # (n_radial, n_theta, 1)

    data = {
        "rs": rs, "thetas": thetas, "phis": phis,
        "r_polys": r_polys, "sh_cache": sh_cache,
        "dV": dV, "nl_pairs": nl_pairs,
    }
    _ZERNIKE_CACHE["key"] = key
    _ZERNIKE_CACHE["data"] = data
    print(f"  done ({1000*(time.perf_counter()-t0):.0f} ms; {len(nl_pairs)} (n,l) pairs)")
    return data


def sample_field_on_ball(field, axes, center, radius_max, rs, thetas, phis):
    """Sample 3D voxel field on a ball of radius_max via trilinear interp.
    Returns array of shape (n_radial, n_theta, n_phi)."""
    n_r, n_t, n_p = len(rs), len(thetas), len(phis)
    R, T, P = np.meshgrid(rs * radius_max, thetas, phis, indexing="ij")
    x = center[0] + R * np.sin(T) * np.cos(P)
    y = center[1] + R * np.sin(T) * np.sin(P)
    z = center[2] + R * np.cos(T)

    def interp_axis(coords_1d, axis):
        idx_f = (coords_1d - axis[0]) / (axis[-1] - axis[0]) * (len(axis) - 1)
        return np.clip(idx_f, 0, len(axis) - 1.001)

    ix = interp_axis(x.ravel(), axes[0])
    iy = interp_axis(y.ravel(), axes[1])
    iz = interp_axis(z.ravel(), axes[2])
    ix0, iy0, iz0 = np.floor(ix).astype(int), np.floor(iy).astype(int), np.floor(iz).astype(int)
    dx, dy, dz = ix - ix0, iy - iy0, iz - iz0
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
    return vals.reshape(n_r, n_t, n_p)


def zernike_3d_fingerprint(field, axes, coords_for_scale, n_max,
                            n_radial, n_theta, n_phi):
    """
    Compute 3D Zernike SO(3)-invariant fingerprint:
    F_nl = Σ_m |Ω_nlm|²  where  Ω_nlm = ∫ f Z*_nlm dV

    Returns array indexed by (n, l) pairs (flattened).
    """
    cache = precompute_zernike_basis(n_max, n_radial, n_theta, n_phi)
    rs, thetas, phis = cache["rs"], cache["thetas"], cache["phis"]
    r_polys, sh_cache, dV, nl_pairs = (cache["r_polys"], cache["sh_cache"],
                                        cache["dV"], cache["nl_pairs"])

    # Center on protein, use protein intrinsic radius
    protein_center = coords_for_scale.mean(axis=0)
    intrinsic_radius = np.linalg.norm(coords_for_scale - protein_center, axis=1).max() * 1.4

    f_ball = sample_field_on_ball(field, axes, protein_center, intrinsic_radius,
                                   rs, thetas, phis)
    # Weighted field (dV broadcasts over phi axis)
    f_weighted = f_ball * dV  # shape (n_radial, n_theta, n_phi)

    fingerprint = {}
    for n, l in nl_pairs:
        # Build Z_nlm and compute Ω_nlm for each m
        R_nl = r_polys[(n, l)]  # (n_radial,)
        F_nl = 0.0
        for m in range(-l, l + 1):
            Y_lm = sh_cache[(l, m)]  # (n_theta, n_phi)
            # Z_nlm(r, θ, φ) = R_nl(r) · Y_lm(θ, φ)
            # Ω_nlm = ∫ f · conj(Z_nlm) dV
            Z_nlm = R_nl[:, None, None] * Y_lm[None, :, :]
            omega = np.sum(f_weighted * np.conj(Z_nlm))
            F_nl += abs(omega) ** 2
        fingerprint[(n, l)] = F_nl
    return fingerprint


def fingerprint_vector(fingerprint, nl_pairs):
    return np.array([fingerprint[(n, l)] for n, l in nl_pairs])


def cosine_similarity(a, b):
    a, b = a.ravel(), b.ravel()
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    return float(np.dot(a, b) / (na * nb)) if na * nb > 0 else None


# ─── Deformations ─────────────────────────────────────────────────────────

def deform_rotation(coords, angle, axis="z"):
    c, s = np.cos(angle), np.sin(angle)
    if axis == "z":   R = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
    elif axis == "x": R = np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
    else:             R = np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    return coords @ R.T


def deform_translation(coords, shift_vec):
    return coords + shift_vec


def deform_thermal_noise(coords, magnitude):
    return coords + magnitude * RNG.standard_normal(coords.shape)


# ─── Main ─────────────────────────────────────────────────────────────────

def compute_z3d_fingerprint(coords, fiedler_values):
    field, axes = voxelize_scalar(coords, fiedler_values, VOXEL_N, GAUSSIAN_SIGMA)
    fp = zernike_3d_fingerprint(field, axes, coords, N_MAX, N_RADIAL, N_THETA, N_PHI)
    return fp


def main():
    print("=== 3D Zernike moment SO(3)-invariant fingerprint ===")
    print(f"Seed: {SEED}; voxel: {VOXEL_N}^3; Zernike n_max: {N_MAX}")
    print(f"Sampling grid: radial={N_RADIAL}, θ={N_THETA}, φ={N_PHI}")
    print()

    coords_1ubq = fetch_pdb_ca("1UBQ")
    L_1ubq = build_gnm_laplacian(coords_1ubq, CONTACT_CUTOFF)
    fiedler_1ubq = fiedler_eigenvector(L_1ubq)
    print(f"[Setup] 1UBQ: {coords_1ubq.shape[0]} Cα; computing fingerprint...")

    t0 = time.perf_counter()
    fp_1ubq = compute_z3d_fingerprint(coords_1ubq, fiedler_1ubq)
    cache = _ZERNIKE_CACHE["data"]
    nl_pairs = cache["nl_pairs"]
    vec_1ubq = fingerprint_vector(fp_1ubq, nl_pairs)
    t_fp = time.perf_counter() - t0
    print(f"        Computed in {1000*t_fp:.0f} ms")
    print(f"        Fingerprint dim: {len(vec_1ubq)} = {len(nl_pairs)} (n,l) pairs")
    print()

    print("=== TEST 1: Self-similarity (must = 1.0) ===")
    self_sim = cosine_similarity(vec_1ubq, vec_1ubq)
    print(f"  cosine(1UBQ, 1UBQ) = {self_sim:.6f}")
    print()

    print("=== TEST 2: Rotation invariance ===")
    rotation_tests = [
        ("rot_30deg_z",  deform_rotation(coords_1ubq, np.pi / 6, "z")),
        ("rot_90deg_z",  deform_rotation(coords_1ubq, np.pi / 2, "z")),
        ("rot_180deg_z", deform_rotation(coords_1ubq, np.pi, "z")),
        ("rot_90deg_x",  deform_rotation(coords_1ubq, np.pi / 2, "x")),
        ("rot_90deg_y",  deform_rotation(coords_1ubq, np.pi / 2, "y")),
    ]
    rot_results = []
    for label, rotated in rotation_tests:
        fp_r = compute_z3d_fingerprint(rotated, fiedler_1ubq)
        vec_r = fingerprint_vector(fp_r, nl_pairs)
        cos_r = cosine_similarity(vec_1ubq, vec_r)
        rot_results.append((label, cos_r))
        print(f"  {label:<16s}: Z3D cosine = {cos_r:.6f}")
    print()

    print("=== TEST 3: Translation invariance ===")
    fp_t = compute_z3d_fingerprint(deform_translation(coords_1ubq, np.array([10.0, 0, 0])), fiedler_1ubq)
    vec_t = fingerprint_vector(fp_t, nl_pairs)
    cos_t = cosine_similarity(vec_1ubq, vec_t)
    print(f"  translation_10Å: Z3D cosine = {cos_t:.6f}")
    print()

    print("=== TEST 4: Thermal noise ===")
    for noise in [0.5, 2.0, 5.0]:
        fp_n = compute_z3d_fingerprint(deform_thermal_noise(coords_1ubq, noise), fiedler_1ubq)
        vec_n = fingerprint_vector(fp_n, nl_pairs)
        cos_n = cosine_similarity(vec_1ubq, vec_n)
        print(f"  thermal_{noise}Å: Z3D cosine = {cos_n:.6f}")
    print()

    print("=== TEST 5: Cross-protein discrimination (1UBQ vs 1BPI) ===")
    coords_1bpi = fetch_pdb_ca("1BPI")
    L_1bpi = build_gnm_laplacian(coords_1bpi, CONTACT_CUTOFF)
    fiedler_1bpi = fiedler_eigenvector(L_1bpi)
    fp_1bpi = compute_z3d_fingerprint(coords_1bpi, fiedler_1bpi)
    vec_1bpi = fingerprint_vector(fp_1bpi, nl_pairs)
    cos_cross = cosine_similarity(vec_1ubq, vec_1bpi)
    print(f"  1UBQ vs 1BPI: Z3D cosine = {cos_cross:.6f}")
    print(f"  Comparison:")
    print(f"    Voxel HDC sign-only (PR #333):   -0.343 (firmly different)")
    print(f"    SH power spectrum (PR #337):     +0.929 (rotation-invariant but blurry)")
    print(f"    3D Zernike (this PR):            {cos_cross:+.3f}")
    print()

    # Verdict
    print("=== Verdict ===")
    rot_min = float(min(r[1] for r in rot_results))
    print(f"  Rotation invariance:     min cosine = {rot_min:.6f}")
    print(f"  Translation invariance:  {cos_t:.6f}")
    print(f"  Self-similarity:         {self_sim:.6f}")
    print(f"  Cross-protein:           {cos_cross:.6f}")
    print()
    if rot_min > 0.99 and abs(cos_cross) < 0.7:
        print("  WIN: SO(3) invariance + cross-protein discrimination preserved")
    elif rot_min > 0.99:
        print(f"  PARTIAL: SO(3) recovered but cross-protein still high at {cos_cross:.3f}")
    else:
        print(f"  ROTATION NOT RECOVERED: min cosine {rot_min:.4f}")

    # Save
    records = [
        {"test": "config", "n_max": N_MAX, "n_pairs": len(nl_pairs),
         "n_radial": N_RADIAL, "n_theta": N_THETA, "n_phi": N_PHI},
        {"test": "self_similarity", "cosine": self_sim},
        {"test": "rotation", "results": [{"label": l, "cosine": c} for l, c in rot_results],
         "min": rot_min},
        {"test": "translation_10A", "cosine": cos_t},
        {"test": "cross_protein_1ubq_1bpi", "cosine": cos_cross,
         "voxel_hdc_baseline": -0.343,
         "sh_power_baseline": 0.929},
    ]
    with open(RESULTS_FILE, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    # Plot — comparison of three fingerprints
    fig, ax = plt.subplots(figsize=(10, 5))
    labels = ["self", "rot_30z", "rot_90z", "rot_90x", "rot_90y", "trans", "cross_1bpi"]
    voxel_baseline = [1.0, 0.67, 0.14, 0.14, 0.14, 1.0, -0.34]
    sh_baseline = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.93]
    z3d_values = [self_sim, rot_results[0][1], rot_results[1][1],
                  rot_results[3][1], rot_results[4][1], cos_t, cos_cross]
    x = np.arange(len(labels))
    w = 0.27
    ax.bar(x - w, voxel_baseline, w, label="Voxel HDC (PR #336)", color='red', alpha=0.7)
    ax.bar(x, sh_baseline, w, label="SH power (PR #337)", color='blue', alpha=0.7)
    ax.bar(x + w, z3d_values, w, label="3D Zernike (this PR)", color='green', alpha=0.7)
    ax.set_xticks(x); ax.set_xticklabels(labels, rotation=30, fontsize=9)
    ax.set_ylabel("Cosine similarity")
    ax.axhline(1.0, color='black', linestyle='--', alpha=0.3)
    ax.axhline(0, color='gray', linestyle=':', alpha=0.5)
    ax.set_title("Three fingerprints — Voxel HDC vs SH power vs 3D Zernike")
    ax.legend(loc='lower left', fontsize=9)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUT_DIR / "zernike-3d-fingerprint-comparison-2026-05-12.png", dpi=100)
    plt.close()

    print()
    print(f"Results: {RESULTS_FILE.name}")
    print(f"Plot:    zernike-3d-fingerprint-comparison-2026-05-12.png")


if __name__ == "__main__":
    main()

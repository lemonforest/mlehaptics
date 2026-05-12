"""
PCA canonical-frame voxel HDC — pre-rotate coords to PCA axes (2026-05-12).

PR B of the 3-PR sequence after PR #337/#338. PCA canonical-frame alignment:
compute principal axes of protein coords; rotate to (x, y, z) by largest-to-
smallest variance; then apply voxel HDC. This should give voxel-HDC-level
discrimination AND rotation invariance.

Why this might work:
- Voxel HDC (PR #333) has strong cross-protein discrimination (-0.34 1UBQ vs 1BPI)
  but breaks under rotation (0.14 at 90°) because voxel grid is axis-aligned
- PCA pre-rotation aligns the protein's natural axes to the grid axes
- After canonicalization, the SAME protein in different orientations all map to
  the SAME canonical frame → voxel HDC fingerprint matches

Sign-ambiguity caveat:
- PCA axes are defined up to sign per axis (eigenvector × ±1)
- 2^3 = 8 sign-ambiguous orientations
- Disambiguate by: ensure 3rd-moment skewness of coords along each axis is
  positive (rare empirical convention but unique up to ties)

Reproduce: `python -X utf8 docs/srmech/notes/pca_canonical_voxel_hdc_script.py`
Deterministic seed 20260512. Uses cached PDB from PR #333.
"""

import time
import json
import urllib.request
import numpy as np
import scipy.linalg
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

SEED = 20260512
RNG = np.random.default_rng(SEED)

CONTACT_CUTOFF = 8.0
VOXEL_N = 64
GAUSSIAN_SIGMA = 4.0

OUT_DIR = Path(__file__).parent
RESULTS_FILE = OUT_DIR / "pca-canonical-voxel-hdc-per-test-2026-05-12.ndjson"


# ─── PDB + Fiedler (reused) ──────────────────────────────────────────────

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


# ─── PCA canonical frame ──────────────────────────────────────────────────

def pca_canonical_rotation(coords, weights=None):
    """
    Compute PCA principal axes of coords, optionally weighted (by Fiedler
    eigenvector magnitude). Return rotation matrix R such that coords @ R.T
    is aligned with canonical (x, y, z) by largest-to-smallest variance.

    Sign disambiguation: align each axis so that the third moment (skewness)
    of projected coords along that axis is non-negative.
    """
    centered = coords - coords.mean(axis=0)
    if weights is not None:
        # Use weighted covariance (Fiedler-magnitude-weighted)
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
    # Sort by descending eigenvalue (largest variance first)
    order = np.argsort(eigvals)[::-1]
    R = eigvecs[:, order].T  # rows = canonical axes
    # Ensure proper rotation (det = +1, not reflection)
    if np.linalg.det(R) < 0:
        R[2] *= -1

    # Sign disambiguation via skewness
    projected = centered @ R.T  # shape (N, 3); each col = projection onto canonical axis k
    for k in range(3):
        skew = ((projected[:, k]) ** 3).sum()
        if skew < 0:
            R[k] *= -1

    # Re-check determinant
    if np.linalg.det(R) < 0:
        R[2] *= -1  # last axis flip if needed

    return R


def canonicalize_coords(coords, weights=None):
    """Rotate coords into PCA canonical frame."""
    R = pca_canonical_rotation(coords, weights=weights)
    centered = coords - coords.mean(axis=0)
    return centered @ R.T


# ─── Voxel HDC sign-only (from PR #333) ────────────────────────────────

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
    return field


def hdc_sign_only(field, threshold=1e-3):
    f = field.ravel()
    sign = np.sign(f)
    mask = np.abs(f) > threshold
    phase = np.where(sign > 0, 0.0, np.pi)
    return (mask.astype(float) * np.exp(1j * phase)).astype(np.complex64)


def hdc_cosine(a, b):
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    return float(np.vdot(a, b).real / (na * nb)) if na * nb > 0 else None


# ─── Pipeline: PCA-canonicalize then voxel HDC ──────────────────────────

def compute_pca_voxel_hdc(coords, fiedler_values, canonicalize=True):
    """Full pipeline: PCA-canonicalize coords, voxelize, sign-only HDC.

    canonicalize=False reproduces PR #333 voxel HDC for comparison.
    """
    if canonicalize:
        # Use Fiedler magnitude as weights so PCA reflects the bipartition structure
        coords_canonical = canonicalize_coords(coords, weights=fiedler_values)
    else:
        coords_canonical = coords - coords.mean(axis=0)
    field = voxelize_scalar(coords_canonical, fiedler_values, VOXEL_N, GAUSSIAN_SIGMA)
    return hdc_sign_only(field)


# ─── Deformations ─────────────────────────────────────────────────────────

def deform_rotation(coords, angle, axis="z"):
    c, s = np.cos(angle), np.sin(angle)
    if axis == "z":   R = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
    elif axis == "x": R = np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
    else:             R = np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    return coords @ R.T


def deform_translation(coords, shift):
    return coords + shift


def deform_thermal_noise(coords, magnitude):
    return coords + magnitude * RNG.standard_normal(coords.shape)


# ─── Main ─────────────────────────────────────────────────────────────────

def main():
    print("=== PCA canonical-frame voxel HDC ===")
    print(f"Seed: {SEED}; voxel: {VOXEL_N}^3; σ: {GAUSSIAN_SIGMA}Å")
    print()

    coords_1ubq = fetch_pdb_ca("1UBQ")
    L_1ubq = build_gnm_laplacian(coords_1ubq, CONTACT_CUTOFF)
    fiedler_1ubq = fiedler_eigenvector(L_1ubq)
    print(f"[Setup] 1UBQ: {coords_1ubq.shape[0]} Cα")

    # Reference (canonicalized + voxel HDC)
    psi_1ubq = compute_pca_voxel_hdc(coords_1ubq, fiedler_1ubq, canonicalize=True)
    print(f"        HDC dim: {len(psi_1ubq):,}")

    # Also compute non-canonicalized for comparison
    psi_1ubq_raw = compute_pca_voxel_hdc(coords_1ubq, fiedler_1ubq, canonicalize=False)

    print()
    print("=== TEST 1: Self-similarity ===")
    print(f"  PCA-canonical self: {hdc_cosine(psi_1ubq, psi_1ubq):.6f}")
    print()

    print("=== TEST 2: Rotation invariance — THE LOAD-BEARING TEST ===")
    rotation_tests = [
        ("rot_30deg_z",  deform_rotation(coords_1ubq, np.pi / 6, "z")),
        ("rot_90deg_z",  deform_rotation(coords_1ubq, np.pi / 2, "z")),
        ("rot_180deg_z", deform_rotation(coords_1ubq, np.pi, "z")),
        ("rot_90deg_x",  deform_rotation(coords_1ubq, np.pi / 2, "x")),
        ("rot_90deg_y",  deform_rotation(coords_1ubq, np.pi / 2, "y")),
    ]
    rot_results = []
    for label, rotated in rotation_tests:
        psi_r = compute_pca_voxel_hdc(rotated, fiedler_1ubq, canonicalize=True)
        cos_r = hdc_cosine(psi_1ubq, psi_r)
        rot_results.append((label, cos_r))
        # Compare to non-canonicalized
        psi_r_raw = compute_pca_voxel_hdc(rotated, fiedler_1ubq, canonicalize=False)
        cos_r_raw = hdc_cosine(psi_1ubq_raw, psi_r_raw)
        print(f"  {label:<16s}: PCA-canonical = {cos_r:+.4f}  vs raw voxel HDC = {cos_r_raw:+.4f}")
    print()

    print("=== TEST 3: Translation ===")
    psi_t = compute_pca_voxel_hdc(deform_translation(coords_1ubq, np.array([10.0, 0, 0])),
                                    fiedler_1ubq, canonicalize=True)
    cos_t = hdc_cosine(psi_1ubq, psi_t)
    print(f"  translation_10Å: PCA-canonical = {cos_t:+.4f}")
    print()

    print("=== TEST 4: Thermal noise ===")
    for noise in [0.5, 2.0, 5.0]:
        psi_n = compute_pca_voxel_hdc(deform_thermal_noise(coords_1ubq, noise),
                                        fiedler_1ubq, canonicalize=True)
        print(f"  thermal_{noise}Å: PCA-canonical = {hdc_cosine(psi_1ubq, psi_n):+.4f}")
    print()

    print("=== TEST 5: Cross-protein discrimination ===")
    coords_1bpi = fetch_pdb_ca("1BPI")
    L_1bpi = build_gnm_laplacian(coords_1bpi, CONTACT_CUTOFF)
    fiedler_1bpi = fiedler_eigenvector(L_1bpi)
    psi_1bpi_canon = compute_pca_voxel_hdc(coords_1bpi, fiedler_1bpi, canonicalize=True)
    cos_cross_canon = hdc_cosine(psi_1ubq, psi_1bpi_canon)

    psi_1bpi_raw = compute_pca_voxel_hdc(coords_1bpi, fiedler_1bpi, canonicalize=False)
    cos_cross_raw = hdc_cosine(psi_1ubq_raw, psi_1bpi_raw)
    print(f"  1UBQ vs 1BPI (PCA-canonical):  {cos_cross_canon:+.4f}")
    print(f"  1UBQ vs 1BPI (raw voxel HDC):  {cos_cross_raw:+.4f}")
    print()
    print(f"  Baselines:")
    print(f"    Raw voxel HDC (PR #333):  -0.343 (firmly different)")
    print(f"    SH power spectrum (#337): +0.929 (rotation-invariant)")
    print(f"    3D Zernike (#338):        +0.99999 (collapsed)")
    print(f"    PCA-canonical (this PR):  {cos_cross_canon:+.4f}")
    print()

    # Verdict
    print("=== Verdict ===")
    rot_min = float(min(r[1] for r in rot_results))
    print(f"  Rotation invariance:     min cosine = {rot_min:.4f}")
    print(f"  Translation:             {cos_t:.4f}")
    print(f"  Cross-protein (canon):   {cos_cross_canon:.4f}")
    print(f"  Cross-protein (raw):     {cos_cross_raw:.4f}")
    print()

    if rot_min > 0.9 and abs(cos_cross_canon) < 0.5:
        print(f"  WIN: rotation-invariance recovered ({rot_min:.4f}) AND")
        print(f"       cross-protein discrimination preserved ({cos_cross_canon:.4f})")
        print(f"       Better than SH power (0.93) on both axes.")
    elif rot_min > 0.9:
        print(f"  PARTIAL: rotation invariance recovered but cross-protein")
        print(f"       discrimination at {cos_cross_canon:.4f} (compare raw -0.34)")
    else:
        print(f"  PROBLEM: rotation invariance not recovered ({rot_min:.4f})")
        print(f"       — PCA sign-disambiguation may be unstable under rotation")

    records = [
        {"test": "rotation_pca_canonical", "results": [{"label": l, "cosine": c} for l, c in rot_results],
         "min": rot_min},
        {"test": "translation_pca_canonical", "cosine": cos_t},
        {"test": "cross_protein_pca_canonical", "cosine": cos_cross_canon},
        {"test": "cross_protein_raw_voxel_hdc", "cosine": cos_cross_raw},
        {"test": "config", "voxel_n": VOXEL_N, "sigma": GAUSSIAN_SIGMA,
         "fiedler_weighted_pca": True, "sign_disambig": "skewness"},
    ]
    with open(RESULTS_FILE, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    # Plot
    fig, ax = plt.subplots(figsize=(12, 5))
    labels = ["self", "rot_30z", "rot_90z", "rot_90x", "rot_90y", "trans", "cross_1bpi"]
    raw_voxel = [1.0, 0.67, 0.14, 0.14, 0.14, 1.0, -0.34]
    sh_power = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.93]
    z3d = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.99999]
    pca_canon = [1.0, rot_results[0][1], rot_results[1][1],
                 rot_results[3][1], rot_results[4][1], cos_t, cos_cross_canon]
    x = np.arange(len(labels))
    w = 0.2
    ax.bar(x - 1.5 * w, raw_voxel, w, label="Voxel HDC raw", color='red', alpha=0.7)
    ax.bar(x - 0.5 * w, sh_power, w, label="SH power", color='blue', alpha=0.7)
    ax.bar(x + 0.5 * w, z3d, w, label="3D Zernike", color='orange', alpha=0.7)
    ax.bar(x + 1.5 * w, pca_canon, w, label="PCA canonical (this)", color='green', alpha=0.7)
    ax.set_xticks(x); ax.set_xticklabels(labels, rotation=30, fontsize=9)
    ax.set_ylabel("Cosine similarity")
    ax.axhline(1.0, color='black', linestyle='--', alpha=0.3)
    ax.axhline(0, color='gray', linestyle=':', alpha=0.5)
    ax.set_title("Four geometric fingerprints — full comparison")
    ax.legend(loc='lower left', fontsize=9)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUT_DIR / "pca-canonical-voxel-hdc-comparison-2026-05-12.png", dpi=100)
    plt.close()

    print()
    print(f"Results: {RESULTS_FILE.name}")
    print(f"Plot:    pca-canonical-voxel-hdc-comparison-2026-05-12.png")


if __name__ == "__main__":
    main()

"""
Dynamic metric / static Laplacian — MFO two-level ontology test (2026-05-12).

User question: "what if instead of trying to reshape voxels, we change the
structure of the coordinate system? what I mean is we treat space as static
but space is more or less just an EM spectra propagation medium. so what
happens when that propagation medium becomes dynamic against a static
Laplacian structure?"

Maps cleanly onto MFO §VII two-level ontology (PR #332 §VII.1.1):
  Level 1 (substrate)  = metric / spatial embedding  → DYNAMIC
  Level 2 (excitation) = graph Laplacian + Fiedler  → STATIC

Test: keep the 1UBQ contact graph Laplacian and Fiedler eigenvector fixed.
Apply 5 different metric deformations to the spatial embedding. For each:
voxelize, HDC-encode (sign-only per PR #333), measure cosine vs identity.

Reveals WHERE the HDC fingerprint's information lives:
- Intrinsic (graph) → fingerprint invariant under all deformations
- Extrinsic (embedding) → fingerprint changes with deformation
- Mixed → behavior depends on deformation type

Reproduce: `python -X utf8 docs/srmech/notes/dynamic_metric_static_laplacian_script.py`.
Deterministic seed 20260512. Reuses cached 1UBQ.pdb from PR #333.
"""

import time
import json
import urllib.request
import numpy as np
import scipy.sparse as sp
import scipy.linalg
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

SEED = 20260512
RNG = np.random.default_rng(SEED)

CONTACT_CUTOFF = 8.0
VOXEL_N = 64
GAUSSIAN_SIGMA_BASE = 4.0

OUT_DIR = Path(__file__).parent
RESULTS_FILE = OUT_DIR / "dynamic-metric-static-laplacian-per-deformation-2026-05-12.ndjson"


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
    return field


def hdc_sign_only(field, threshold=1e-3):
    f = field.ravel()
    sign = np.sign(f)
    mask = np.abs(f) > threshold
    phase = np.where(sign > 0, 0.0, np.pi)
    return (mask.astype(float) * np.exp(1j * phase)).astype(np.complex64)


def hdc_cosine(a, b):
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na == 0 or nb == 0:
        return None
    return float(np.vdot(a, b).real / (na * nb))


# ─── Metric deformations ───────────────────────────────────────────────────

def deform_identity(coords):
    return coords.copy(), GAUSSIAN_SIGMA_BASE


def deform_uniform_scale(coords, alpha):
    """x → α·x; also scale σ by α to preserve relative encoding resolution."""
    return alpha * coords, alpha * GAUSSIAN_SIGMA_BASE


def deform_uniform_scale_static_sigma(coords, alpha):
    """x → α·x; σ stays the same — tests scale equivariance without σ adjustment."""
    return alpha * coords, GAUSSIAN_SIGMA_BASE


def deform_anisotropic_stretch(coords, stretch_vec):
    """x → diag(stretch_vec) · x. σ stays isotropic."""
    M = np.diag(stretch_vec)
    return coords @ M.T, GAUSSIAN_SIGMA_BASE


def deform_thermal_noise(coords, magnitude):
    return coords + magnitude * RNG.standard_normal(coords.shape), GAUSSIAN_SIGMA_BASE


def deform_normal_mode(coords, fiedler_values, amplitude):
    """
    Apply lowest-frequency normal-mode-like displacement: each Cα moves
    along its Fiedler-direction-modulated displacement. Coarse approximation
    of a "breathing" mode where atoms in different bipartition halves move
    in opposite directions.
    """
    # Direction: project each atom along the bipartition axis (PCA of coords weighted by Fiedler)
    weighted_coords = coords * fiedler_values[:, None]
    direction = weighted_coords.mean(axis=0)
    direction = direction / np.linalg.norm(direction)
    # Each atom's displacement is amplitude * Fiedler_value * direction
    displacements = amplitude * fiedler_values[:, None] * direction[None, :]
    return coords + displacements, GAUSSIAN_SIGMA_BASE


def deform_rotation(coords, angle):
    """Rigid rotation about z-axis — should leave HDC INVARIANT (up to voxel re-binning)."""
    c, s = np.cos(angle), np.sin(angle)
    R = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
    return coords @ R.T, GAUSSIAN_SIGMA_BASE


def deform_translation(coords, shift_vec):
    """Rigid translation — should be invariant (bounding-box recentered)."""
    return coords + shift_vec, GAUSSIAN_SIGMA_BASE


def main():
    print("=== Dynamic metric / static Laplacian — MFO two-level ontology test ===")
    print(f"Seed: {SEED}; voxel: {VOXEL_N}^3; baseline σ: {GAUSSIAN_SIGMA_BASE}Å")
    print()

    # ─── Setup: protein + Fiedler ──────────────────────────────────────────
    coords_0 = fetch_pdb_ca("1UBQ")
    n_residues = coords_0.shape[0]
    L = build_gnm_laplacian(coords_0, CONTACT_CUTOFF)
    fiedler = fiedler_eigenvector(L)
    print(f"[Setup] 1UBQ: {n_residues} Cα; Fiedler range [{fiedler.min():.3f}, {fiedler.max():.3f}]")
    print(f"         L_protein and fiedler are FIXED — only the metric deformation varies")
    print()

    # ─── Baseline encoding ─────────────────────────────────────────────────
    field_0 = voxelize_scalar(coords_0, fiedler, VOXEL_N, GAUSSIAN_SIGMA_BASE)
    psi_0 = hdc_sign_only(field_0)
    print(f"[Baseline] Identity encoding: voxel field range [{field_0.min():.3f}, {field_0.max():.3f}]")
    print(f"           HDC self-similarity: {hdc_cosine(psi_0, psi_0):.6f}")
    print()

    # ─── Deformation suite ─────────────────────────────────────────────────
    deformations = [
        ("identity",                       lambda: deform_identity(coords_0)),
        ("uniform_scale_alpha_0.8",        lambda: deform_uniform_scale(coords_0, 0.8)),
        ("uniform_scale_alpha_1.2",        lambda: deform_uniform_scale(coords_0, 1.2)),
        ("uniform_scale_2.0_no_sigma",     lambda: deform_uniform_scale_static_sigma(coords_0, 2.0)),
        ("anisotropic_x_1.5",              lambda: deform_anisotropic_stretch(coords_0, [1.5, 1.0, 1.0])),
        ("anisotropic_x_2.0_y_0.5",        lambda: deform_anisotropic_stretch(coords_0, [2.0, 0.5, 1.0])),
        ("thermal_noise_0.5",              lambda: deform_thermal_noise(coords_0, 0.5)),
        ("thermal_noise_2.0",              lambda: deform_thermal_noise(coords_0, 2.0)),
        ("thermal_noise_5.0",              lambda: deform_thermal_noise(coords_0, 5.0)),
        ("normal_mode_amplitude_3",        lambda: deform_normal_mode(coords_0, fiedler, 3.0)),
        ("normal_mode_amplitude_10",       lambda: deform_normal_mode(coords_0, fiedler, 10.0)),
        ("rotation_30deg",                 lambda: deform_rotation(coords_0, np.pi / 6)),
        ("rotation_90deg",                 lambda: deform_rotation(coords_0, np.pi / 2)),
        ("translation_10A_x",              lambda: deform_translation(coords_0, np.array([10.0, 0, 0]))),
    ]

    results = []
    print("--- Running deformations ---")
    print(f"{'Deformation':<32s} {'HDC cosine':>12s}  {'Field range':>20s}")
    print("-" * 70)
    for name, fn in deformations:
        coords_def, sigma_def = fn()
        # IMPORTANT: graph Laplacian is FIXED — we use the SAME fiedler eigenvector
        # The only thing that changes is the spatial embedding the eigenvector is voxelized over
        field_def = voxelize_scalar(coords_def, fiedler, VOXEL_N, sigma_def)
        psi_def = hdc_sign_only(field_def)
        cos_sim = hdc_cosine(psi_0, psi_def)
        results.append({
            "deformation": name,
            "sigma": sigma_def,
            "field_min": float(field_def.min()),
            "field_max": float(field_def.max()),
            "hdc_cosine_vs_identity": cos_sim,
        })
        print(f"{name:<32s} {cos_sim:>+12.4f}  [{field_def.min():>+6.3f}, {field_def.max():>+6.3f}]")

    # ─── Verdict per category ──────────────────────────────────────────────
    print()
    print("=== Interpretation ===")

    def cat(name_filter):
        return [r for r in results if name_filter in r["deformation"]]

    invariants = {
        "uniform_scale": cat("uniform_scale"),
        "rotation":      cat("rotation"),
        "translation":   cat("translation"),
        "thermal":       cat("thermal"),
        "anisotropic":   cat("anisotropic"),
        "normal_mode":   cat("normal_mode"),
    }
    for kind, rs in invariants.items():
        if not rs: continue
        sims = [r["hdc_cosine_vs_identity"] for r in rs if r["hdc_cosine_vs_identity"] is not None]
        if not sims:
            print(f"  {kind:<14s}: no data")
            continue
        mean_sim = float(np.mean(sims))
        min_sim = float(np.min(sims))
        max_sim = float(np.max(sims))
        invariant = "INVARIANT" if min_sim > 0.95 else ("NEAR-INVARIANT" if min_sim > 0.85 else "DEGRADES")
        print(f"  {kind:<14s}: mean={mean_sim:+.3f}, range=[{min_sim:+.3f}, {max_sim:+.3f}]  → {invariant}")

    # Write NDJSON
    with open(RESULTS_FILE, "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")

    # ─── Visualization ─────────────────────────────────────────────────────
    fig, axes = plt.subplots(2, 4, figsize=(16, 8))
    axes = axes.flatten()
    snapshots_to_show = [
        ("identity", 0),
        ("uniform_scale_alpha_1.2", 2),
        ("anisotropic_x_2.0_y_0.5", 5),
        ("thermal_noise_2.0", 7),
        ("normal_mode_amplitude_10", 10),
        ("rotation_90deg", 12),
    ]
    for plot_i, (name, idx) in enumerate(snapshots_to_show):
        if plot_i >= len(axes): break
        coords_def, sigma_def = deformations[idx][1]()
        field_def = voxelize_scalar(coords_def, fiedler, VOXEL_N, sigma_def)
        mid = field_def.shape[2] // 2
        ax = axes[plot_i]
        vmax = max(abs(field_def.min()), abs(field_def.max())) or 1
        im = ax.imshow(field_def[:, :, mid], cmap="seismic", vmin=-vmax, vmax=vmax, origin="lower")
        ax.set_title(f"{name}\ncos vs identity: {results[idx]['hdc_cosine_vs_identity']:+.3f}", fontsize=9)
        ax.set_xticks([]); ax.set_yticks([])
        plt.colorbar(im, ax=ax, fraction=0.046)
    for i in range(len(snapshots_to_show), len(axes)):
        axes[i].axis("off")
    plt.tight_layout()
    plt.savefig(OUT_DIR / "dynamic-metric-deformation-slices-2026-05-12.png", dpi=100)
    plt.close()

    # Bar chart of cosines
    fig, ax = plt.subplots(figsize=(14, 5))
    names = [r["deformation"] for r in results]
    sims = [r["hdc_cosine_vs_identity"] or 0 for r in results]
    colors = ['green' if s > 0.95 else ('orange' if s > 0.85 else 'red') for s in sims]
    ax.barh(range(len(names)), sims, color=colors)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=9)
    ax.axvline(1.0, color='black', linestyle='-', linewidth=0.5)
    ax.axvline(0.95, color='green', linestyle='--', linewidth=0.5, label='0.95 (invariant)')
    ax.axvline(0.85, color='orange', linestyle='--', linewidth=0.5, label='0.85 (degraded)')
    ax.axvline(0, color='gray', linestyle=':', linewidth=0.5)
    ax.set_xlabel("HDC cosine vs identity")
    ax.set_title("Metric-deformation impact on HDC fingerprint (static graph Laplacian)")
    ax.set_xlim(-0.1, 1.05)
    ax.legend()
    plt.tight_layout()
    plt.savefig(OUT_DIR / "dynamic-metric-deformation-bars-2026-05-12.png", dpi=100)
    plt.close()

    print()
    print(f"Results: {RESULTS_FILE.name}")
    print(f"Plots:   dynamic-metric-deformation-slices-2026-05-12.png")
    print(f"         dynamic-metric-deformation-bars-2026-05-12.png")


if __name__ == "__main__":
    main()

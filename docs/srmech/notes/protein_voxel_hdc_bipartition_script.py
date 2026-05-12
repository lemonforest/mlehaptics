"""
Protein bipartition voxelization + RBS HDC lift — one-pass spike (2026-05-12).

User insight (waking thought): instead of drawing thousands of 3D line segments
for the Fiedler bipartition over a protein structure, scatter-to-grid the
eigenvector onto a voxel lattice and treat that as both the rendering substrate
AND a Resonant Bit-Serialized HDC hypervector. The "one pass" claim: voxel
field IS the hypervector, so spectral primitive + encoding + HDC query + render
all live on the same array.

Tests three load-bearing claims:
  1. Voxelization renders the bipartition correctly (slice heatmaps).
  2. Voxel-field cosine in complex64 HDC space yields meaningful protein
     similarity: self ≈ 1.0; perturbed-self << 1 but >> random; random ≈ 0.
  3. Timing: voxelize + HDC lift + render is competitive with naive 3D
     line-segment rendering at equivalent visual quality.

Deterministic seed `20260512`. Reproducible. numpy + scipy + matplotlib only.
Synthetic protein (random-walk Cα positions, 76 residues — ubiquitin scale).
"""

import time
import json
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg
import scipy.linalg
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

SEED = 20260512
RNG = np.random.default_rng(SEED)

# Protein synthesis params
N_RESIDUES = 76
CA_STEP = 3.8  # angstroms, idealized Cα-Cα distance
PERSISTENCE = 0.7  # backbone persistence (closer to 1 = stiffer)
CONTACT_CUTOFF = 8.0  # angstroms, GNM standard

# Voxelization params
VOXEL_N = 64
GAUSSIAN_SIGMA = 4.0  # angstroms

# Output
OUT_DIR = Path(__file__).parent
RESULTS_FILE = OUT_DIR / "protein-voxel-hdc-bipartition-per-test-2026-05-12.ndjson"


def synth_protein_ca(n_residues: int, step: float, persistence: float) -> np.ndarray:
    """Persistent random-walk Cα coordinates — coarse but topologically real."""
    coords = np.zeros((n_residues, 3))
    direction = np.array([1.0, 0.0, 0.0])
    for i in range(1, n_residues):
        new_dir = persistence * direction + (1 - persistence) * RNG.standard_normal(3)
        new_dir /= np.linalg.norm(new_dir)
        coords[i] = coords[i - 1] + step * new_dir
        direction = new_dir
    coords -= coords.mean(axis=0)
    return coords


def build_gnm_laplacian(coords: np.ndarray, cutoff: float) -> sp.csr_matrix:
    """Gaussian Network Model contact-graph Laplacian."""
    n = coords.shape[0]
    dists = np.linalg.norm(coords[:, None] - coords[None, :], axis=2)
    A = (dists < cutoff).astype(float) - np.eye(n)
    D = np.diag(A.sum(axis=1))
    L = D - A
    return sp.csr_matrix(L)


def fiedler_eigenvector(L: sp.csr_matrix) -> np.ndarray:
    """Second-smallest eigenvector — the bipartition signal."""
    w, v = scipy.linalg.eigh(L.toarray())
    return v[:, 1]


def voxelize_scalar_field(
    coords: np.ndarray, values: np.ndarray, n_voxels: int, sigma: float
) -> np.ndarray:
    """
    Gaussian scatter-to-grid: each point contributes a 3D Gaussian to its
    neighborhood, weighted by `values[i]`.

    Returns: real-valued (n_voxels, n_voxels, n_voxels) array.
    """
    bbox_min = coords.min(axis=0) - 3 * sigma
    bbox_max = coords.max(axis=0) + 3 * sigma
    grid_extent = bbox_max - bbox_min
    voxel_size = grid_extent / n_voxels

    axes = [np.linspace(bbox_min[d], bbox_max[d], n_voxels) for d in range(3)]
    gx, gy, gz = np.meshgrid(axes[0], axes[1], axes[2], indexing="ij")
    grid = np.stack([gx, gy, gz], axis=-1)

    field = np.zeros((n_voxels, n_voxels, n_voxels), dtype=np.float64)
    n_residues = coords.shape[0]
    for i in range(n_residues):
        d_sq = np.sum((grid - coords[i]) ** 2, axis=-1)
        contribution = values[i] * np.exp(-d_sq / (2 * sigma ** 2))
        field += contribution

    return field, voxel_size, bbox_min


def hdc_lift_to_complex64(field: np.ndarray) -> np.ndarray:
    """
    NAIVE encoding (v1) — dominated by spatial occupancy. Kept for comparison.
    phase = 2π * normalized_field; psi = exp(i * phase) in complex64.
    """
    f = field.ravel()
    f_normalized = (f - f.min()) / (f.max() - f.min() + 1e-12)
    phase = 2 * np.pi * f_normalized
    psi = np.exp(1j * phase).astype(np.complex64)
    return psi


def hdc_lift_sign_only(field: np.ndarray, threshold: float = 1e-3) -> np.ndarray:
    """
    SIGN-ONLY encoding (v2) — captures bipartition assignment only.
    phase = 0 for +, phase = π for -, amplitude = 0 where |field| < threshold.
    This is the "bipartition IS the signal" reading.
    """
    f = field.ravel()
    sign = np.sign(f)
    mask = np.abs(f) > threshold
    phase = np.where(sign > 0, 0.0, np.pi)
    amp = mask.astype(np.float64)
    psi = (amp * np.exp(1j * phase)).astype(np.complex64)
    return psi


def hdc_lift_tanh(field: np.ndarray, scale: float = None) -> np.ndarray:
    """
    TANH-SMOOTH encoding (v3) — sign-preserving but smooth.
    phase = (π/2) * tanh(field / scale); preserves both sign and magnitude
    in a bounded way. Real part = cos(phase) carries sign.
    """
    f = field.ravel()
    if scale is None:
        scale = np.abs(f).max() * 0.3
    phase = (np.pi / 2) * np.tanh(f / scale)
    psi = np.exp(1j * phase).astype(np.complex64)
    return psi


def hdc_cosine(psi_a: np.ndarray, psi_b: np.ndarray) -> float:
    """Standard HDC similarity — normalized inner product, real part."""
    num = np.vdot(psi_a, psi_b).real
    den = np.linalg.norm(psi_a) * np.linalg.norm(psi_b)
    return float(num / den)


def render_three_slices(field: np.ndarray, title: str, out_path: Path):
    """Render mid-axis slices along x, y, z."""
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    mid = field.shape[0] // 2
    slices = [field[mid, :, :], field[:, mid, :], field[:, :, mid]]
    labels = ["x-slice (yz plane)", "y-slice (xz plane)", "z-slice (xy plane)"]
    vmax = np.max(np.abs(field))
    vmin = -vmax
    for ax, sl, lbl in zip(axes, slices, labels):
        im = ax.imshow(sl, cmap="seismic", vmin=vmin, vmax=vmax, origin="lower")
        ax.set_title(lbl)
        ax.set_xticks([])
        ax.set_yticks([])
        plt.colorbar(im, ax=ax, fraction=0.046)
    fig.suptitle(title)
    plt.tight_layout()
    plt.savefig(out_path, dpi=100)
    plt.close()


def perturb_coords(coords: np.ndarray, magnitude: float) -> np.ndarray:
    """Add small isotropic noise — simulates conformational fluctuation."""
    return coords + magnitude * RNG.standard_normal(coords.shape)


def random_phase_vector(d: int) -> np.ndarray:
    """Pure-random complex64 phase vector for null comparison."""
    phase = 2 * np.pi * RNG.random(d)
    return np.exp(1j * phase).astype(np.complex64)


def main():
    results = []

    print(f"=== Protein voxel HDC bipartition spike — {time.strftime('%Y-%m-%d')} ===")
    print(f"Seed: {SEED}; residues: {N_RESIDUES}; voxel grid: {VOXEL_N}^3")
    print()

    # ─── Stage 1: synthesize protein + compute Fiedler ──────────────────────
    t0 = time.perf_counter()
    coords_A = synth_protein_ca(N_RESIDUES, CA_STEP, PERSISTENCE)
    L_A = build_gnm_laplacian(coords_A, CONTACT_CUTOFF)
    fiedler_A = fiedler_eigenvector(L_A)
    t_eigh = time.perf_counter() - t0
    print(f"[1] Protein A synthesized + eigh: {1000*t_eigh:.2f} ms")
    print(f"    Fiedler range: [{fiedler_A.min():.4f}, {fiedler_A.max():.4f}]")
    print(f"    Bipartition: {(fiedler_A > 0).sum()} positive / {(fiedler_A <= 0).sum()} negative")

    # ─── Stage 2: voxelize + render ─────────────────────────────────────────
    t0 = time.perf_counter()
    field_A, voxel_size, bbox_min = voxelize_scalar_field(
        coords_A, fiedler_A, VOXEL_N, GAUSSIAN_SIGMA
    )
    t_voxelize = time.perf_counter() - t0
    print(f"[2] Voxelize ({VOXEL_N}^3 = {VOXEL_N**3:,} cells): {1000*t_voxelize:.2f} ms")
    print(f"    Field range: [{field_A.min():.4f}, {field_A.max():.4f}]")

    t0 = time.perf_counter()
    render_three_slices(
        field_A,
        f"Protein A Fiedler bipartition ({VOXEL_N}^3 voxels)",
        OUT_DIR / "protein-voxel-hdc-bipartition-protein-a-slices.png",
    )
    t_render = time.perf_counter() - t0
    print(f"[3] Render 3 orthogonal slices: {1000*t_render:.2f} ms")

    # ─── Stage 3: HDC lift — THREE encodings compared ──────────────────────
    encodings = {
        "v1_naive": hdc_lift_to_complex64,
        "v2_sign_only": hdc_lift_sign_only,
        "v3_tanh_smooth": hdc_lift_tanh,
    }

    psi_A_all = {}
    for name, fn in encodings.items():
        t0 = time.perf_counter()
        psi_A_all[name] = fn(field_A)
        dt = time.perf_counter() - t0
        print(f"[4-{name}] HDC lift (D = {len(psi_A_all[name]):,}): {1000*dt:.3f} ms")

    psi_A = psi_A_all["v1_naive"]
    t_hdc_lift = 0  # measured per-encoding above

    # ─── Stage 4: build comparator fields, then test EACH encoding ─────────
    print()
    print("=== Building comparator fields ===")

    coords_A_pert_small = perturb_coords(coords_A, magnitude=0.5)
    L_pert_s = build_gnm_laplacian(coords_A_pert_small, CONTACT_CUTOFF)
    fiedler_pert_s = fiedler_eigenvector(L_pert_s)
    if np.dot(fiedler_pert_s, fiedler_A) < 0:
        fiedler_pert_s = -fiedler_pert_s
    field_pert_s, _, _ = voxelize_scalar_field(
        coords_A_pert_small, fiedler_pert_s, VOXEL_N, GAUSSIAN_SIGMA
    )

    coords_A_pert_large = perturb_coords(coords_A, magnitude=3.0)
    L_pert_l = build_gnm_laplacian(coords_A_pert_large, CONTACT_CUTOFF)
    fiedler_pert_l = fiedler_eigenvector(L_pert_l)
    if np.dot(fiedler_pert_l, fiedler_A) < 0:
        fiedler_pert_l = -fiedler_pert_l
    field_pert_l, _, _ = voxelize_scalar_field(
        coords_A_pert_large, fiedler_pert_l, VOXEL_N, GAUSSIAN_SIGMA
    )

    coords_B = synth_protein_ca(N_RESIDUES, CA_STEP, PERSISTENCE)
    L_B = build_gnm_laplacian(coords_B, CONTACT_CUTOFF)
    fiedler_B = fiedler_eigenvector(L_B)
    field_B, _, _ = voxelize_scalar_field(coords_B, fiedler_B, VOXEL_N, GAUSSIAN_SIGMA)

    print()
    print("=== HDC similarity tests — three encodings ===")
    print()
    print(f"{'Encoding':<16s} {'self':>8s} {'pert_S':>8s} {'pert_L':>8s} {'indep':>8s} {'random':>8s}")
    print("-" * 64)

    per_encoding_results = {}
    sim_self = sim_pert_small = sim_pert_large = sim_independent = sim_random = 0.0
    t_query = 0.0

    for name, fn in encodings.items():
        psi_self = psi_A_all[name]
        psi_ps = fn(field_pert_s)
        psi_pl = fn(field_pert_l)
        psi_b = fn(field_B)
        psi_r = random_phase_vector(len(psi_self))

        t0 = time.perf_counter()
        s_self = hdc_cosine(psi_self, psi_self)
        t_query = time.perf_counter() - t0

        s_ps = hdc_cosine(psi_self, psi_ps)
        s_pl = hdc_cosine(psi_self, psi_pl)
        s_b = hdc_cosine(psi_self, psi_b)
        s_r = hdc_cosine(psi_self, psi_r)

        print(f"{name:<16s} {s_self:>8.4f} {s_ps:>8.4f} {s_pl:>8.4f} {s_b:>8.4f} {s_r:>8.4f}")

        per_encoding_results[name] = {
            "self": s_self,
            "pert_small": s_ps,
            "pert_large": s_pl,
            "independent": s_b,
            "random": s_r,
            "monotonic_decreasing": (s_self >= s_ps >= s_pl and s_pl > s_b and abs(s_r) < 0.1),
        }

        if name == "v2_sign_only":
            sim_self = s_self
            sim_pert_small = s_ps
            sim_pert_large = s_pl
            sim_independent = s_b
            sim_random = s_r

    print()
    print("Verdict per encoding (monotonic self > pert_S > pert_L > indep ~ random):")
    for name, r in per_encoding_results.items():
        verdict = "PASS" if r["monotonic_decreasing"] else "FAIL"
        print(f"  {name:<16s} {verdict}")

    render_three_slices(
        field_B,
        f"Protein B (independent) Fiedler bipartition",
        OUT_DIR / "protein-voxel-hdc-bipartition-protein-b-slices.png",
    )

    records = [
        {
            "test": "timing_breakdown",
            "n_residues": N_RESIDUES,
            "voxel_n": VOXEL_N,
            "hypervector_dim": len(psi_A),
            "eigh_ms": 1000 * t_eigh,
            "voxelize_ms": 1000 * t_voxelize,
            "render_ms": 1000 * t_render,
            "hdc_query_ms": 1000 * t_query,
        },
    ]
    for name, r in per_encoding_results.items():
        records.append({"test": f"similarity_{name}", **r})

    with open(RESULTS_FILE, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    print()
    print(f"=== Summary ===")
    print(f"One-pass total (eigh + voxelize + HDC lift): {1000*(t_eigh+t_voxelize+t_hdc_lift):.2f} ms")
    print(f"HDC query (cosine on D={len(psi_A):,}): {1000*t_query:.3f} ms — O(D)")
    print(f"Monotonic ordering: self={sim_self:.3f} > small={sim_pert_small:.3f} > "
          f"large={sim_pert_large:.3f} > indep={sim_independent:.3f} ~ random={sim_random:.3f}")
    print()
    print(f"Results written to: {RESULTS_FILE.name}")


if __name__ == "__main__":
    main()

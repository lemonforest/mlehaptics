"""
Protein bipartition voxel + RBS HDC — real PDB 1UBQ confirmation (2026-05-12).

Follow-up to `protein_voxel_hdc_bipartition_script.py` (PR #333). The first
spike used a synthetic persistent random-walk protein and confirmed that
sign-only HDC encoding gives clean bipartition similarity. This script
re-runs the same pipeline on REAL ubiquitin (PDB: 1UBQ, 76 residues) to
confirm the load-bearing finding generalizes from synthetic topology to
real α-helix + β-sheet structure.

Fetch: urllib.request from RCSB PDB (no new dependencies; stdlib only).
Parse: simple text parsing of ATOM records for CA atoms (well-documented
PDB format, stable since 1996).

Deterministic seed `20260512`. Same as parent spike for cross-reference.
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

PDB_ID = "1UBQ"
PDB_URL = f"https://files.rcsb.org/download/{PDB_ID}.pdb"
PDB_ID_CROSS = "1BPI"  # BPTI (basic pancreatic trypsin inhibitor), 58 residues, α/β fold
PDB_URL_CROSS = f"https://files.rcsb.org/download/{PDB_ID_CROSS}.pdb"
CONTACT_CUTOFF = 8.0
VOXEL_N = 64
GAUSSIAN_SIGMA = 4.0

OUT_DIR = Path(__file__).parent
PDB_CACHE = OUT_DIR / f"{PDB_ID}.pdb"
RESULTS_FILE = OUT_DIR / "protein-voxel-hdc-1ubq-per-test-2026-05-12.ndjson"


def fetch_pdb(pdb_id: str, url: str, cache_path: Path) -> str:
    """Fetch PDB file, cache locally. Return file contents."""
    if cache_path.exists():
        print(f"[fetch] Using cached {cache_path.name}")
        return cache_path.read_text()
    print(f"[fetch] Downloading {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "srmech-spike/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read().decode("utf-8")
    cache_path.write_text(data)
    print(f"[fetch] Cached to {cache_path.name} ({len(data)} bytes)")
    return data


def parse_ca_coords(pdb_text: str) -> np.ndarray:
    """
    Parse Cα coords from PDB ATOM records.

    PDB ATOM record columns (fixed-width, 1-indexed):
      1-6:   "ATOM  "
      13-16: atom name (e.g. " CA ")
      18-20: residue name
      22:    chain ID
      23-26: residue sequence number
      31-38: x (8.3f angstroms)
      39-46: y
      47-54: z

    We take the first chain only and the first occurrence per residue
    (alt-loc 'A' or blank).
    """
    coords = []
    seen_residues = set()
    chain_id = None
    for line in pdb_text.splitlines():
        if not line.startswith("ATOM"):
            continue
        atom_name = line[12:16].strip()
        if atom_name != "CA":
            continue
        alt_loc = line[16:17]
        if alt_loc not in (" ", "A"):
            continue
        c = line[21:22]
        res_seq = line[22:26].strip()
        if chain_id is None:
            chain_id = c
        elif c != chain_id:
            continue
        key = (c, res_seq)
        if key in seen_residues:
            continue
        seen_residues.add(key)
        x = float(line[30:38])
        y = float(line[38:46])
        z = float(line[46:54])
        coords.append([x, y, z])
    return np.array(coords)


def build_gnm_laplacian(coords: np.ndarray, cutoff: float) -> sp.csr_matrix:
    n = coords.shape[0]
    dists = np.linalg.norm(coords[:, None] - coords[None, :], axis=2)
    A = (dists < cutoff).astype(float) - np.eye(n)
    D = np.diag(A.sum(axis=1))
    L = D - A
    return sp.csr_matrix(L)


def fiedler_eigenvector(L: sp.csr_matrix) -> np.ndarray:
    w, v = scipy.linalg.eigh(L.toarray())
    return v[:, 1]


def voxelize_scalar_field(coords, values, n_voxels, sigma):
    bbox_min = coords.min(axis=0) - 3 * sigma
    bbox_max = coords.max(axis=0) + 3 * sigma
    axes = [np.linspace(bbox_min[d], bbox_max[d], n_voxels) for d in range(3)]
    gx, gy, gz = np.meshgrid(axes[0], axes[1], axes[2], indexing="ij")
    grid = np.stack([gx, gy, gz], axis=-1)
    field = np.zeros((n_voxels, n_voxels, n_voxels), dtype=np.float64)
    for i in range(coords.shape[0]):
        d_sq = np.sum((grid - coords[i]) ** 2, axis=-1)
        field += values[i] * np.exp(-d_sq / (2 * sigma ** 2))
    return field


def hdc_lift_sign_only(field: np.ndarray, threshold: float = 1e-3) -> np.ndarray:
    """The winning encoding from PR #333: phase ∈ {0, π} from sign."""
    f = field.ravel()
    sign = np.sign(f)
    mask = np.abs(f) > threshold
    phase = np.where(sign > 0, 0.0, np.pi)
    amp = mask.astype(np.float64)
    psi = (amp * np.exp(1j * phase)).astype(np.complex64)
    return psi


def hdc_cosine(psi_a, psi_b):
    num = np.vdot(psi_a, psi_b).real
    den = np.linalg.norm(psi_a) * np.linalg.norm(psi_b)
    return float(num / den)


def perturb_coords(coords, magnitude):
    return coords + magnitude * RNG.standard_normal(coords.shape)


def random_phase_vector(d):
    phase = 2 * np.pi * RNG.random(d)
    return np.exp(1j * phase).astype(np.complex64)


def render_three_slices(field, title, out_path):
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


def main():
    print(f"=== Protein voxel HDC — real PDB {PDB_ID} confirmation ===")
    print(f"Seed: {SEED}; voxel grid: {VOXEL_N}^3; cutoff: {CONTACT_CUTOFF}Å; sigma: {GAUSSIAN_SIGMA}Å")
    print()

    # ─── Fetch + parse real ubiquitin ───────────────────────────────────────
    pdb_text = fetch_pdb(PDB_ID, PDB_URL, PDB_CACHE)
    coords = parse_ca_coords(pdb_text)
    n_residues = coords.shape[0]
    print(f"[1] Parsed {n_residues} Cα atoms from {PDB_ID}")
    print(f"    Bounding box: x[{coords[:,0].min():.2f}, {coords[:,0].max():.2f}] "
          f"y[{coords[:,1].min():.2f}, {coords[:,1].max():.2f}] "
          f"z[{coords[:,2].min():.2f}, {coords[:,2].max():.2f}] (Å)")

    # ─── Fiedler partition ──────────────────────────────────────────────────
    t0 = time.perf_counter()
    L = build_gnm_laplacian(coords, CONTACT_CUTOFF)
    fiedler = fiedler_eigenvector(L)
    t_eigh = time.perf_counter() - t0
    print(f"[2] GNM Laplacian + Fiedler eigh: {1000*t_eigh:.2f} ms")
    print(f"    Fiedler range: [{fiedler.min():.4f}, {fiedler.max():.4f}]")
    n_pos = int((fiedler > 0).sum())
    n_neg = int((fiedler <= 0).sum())
    print(f"    Bipartition: {n_pos} positive / {n_neg} negative")

    # ─── Voxelize + render ──────────────────────────────────────────────────
    t0 = time.perf_counter()
    field = voxelize_scalar_field(coords, fiedler, VOXEL_N, GAUSSIAN_SIGMA)
    t_voxelize = time.perf_counter() - t0
    print(f"[3] Voxelize ({VOXEL_N}^3): {1000*t_voxelize:.2f} ms")
    print(f"    Field range: [{field.min():.4f}, {field.max():.4f}]")

    render_three_slices(
        field,
        f"Real ubiquitin (PDB {PDB_ID}) Fiedler bipartition — {VOXEL_N}^3 voxels",
        OUT_DIR / "protein-voxel-hdc-1ubq-slices.png",
    )

    # ─── HDC sign-only lift ─────────────────────────────────────────────────
    t0 = time.perf_counter()
    psi = hdc_lift_sign_only(field)
    t_hdc_lift = time.perf_counter() - t0
    print(f"[4] HDC lift sign-only (D = {len(psi):,}): {1000*t_hdc_lift:.3f} ms")

    # ─── Build comparators ──────────────────────────────────────────────────
    print()
    print("=== Building comparators (real ubiquitin baseline) ===")

    # Small perturbation
    coords_ps = perturb_coords(coords, magnitude=0.5)
    L_ps = build_gnm_laplacian(coords_ps, CONTACT_CUTOFF)
    fiedler_ps = fiedler_eigenvector(L_ps)
    if np.dot(fiedler_ps, fiedler) < 0:
        fiedler_ps = -fiedler_ps
    field_ps = voxelize_scalar_field(coords_ps, fiedler_ps, VOXEL_N, GAUSSIAN_SIGMA)
    psi_ps = hdc_lift_sign_only(field_ps)

    # Large perturbation
    coords_pl = perturb_coords(coords, magnitude=3.0)
    L_pl = build_gnm_laplacian(coords_pl, CONTACT_CUTOFF)
    fiedler_pl = fiedler_eigenvector(L_pl)
    if np.dot(fiedler_pl, fiedler) < 0:
        fiedler_pl = -fiedler_pl
    field_pl = voxelize_scalar_field(coords_pl, fiedler_pl, VOXEL_N, GAUSSIAN_SIGMA)
    psi_pl = hdc_lift_sign_only(field_pl)

    # Independent synthetic protein (random walk, same n)
    def synth_protein_ca(n_residues, step=3.8, persistence=0.7):
        c = np.zeros((n_residues, 3))
        direction = np.array([1.0, 0.0, 0.0])
        for i in range(1, n_residues):
            new_dir = persistence * direction + (1 - persistence) * RNG.standard_normal(3)
            new_dir /= np.linalg.norm(new_dir)
            c[i] = c[i - 1] + step * new_dir
            direction = new_dir
        c -= c.mean(axis=0)
        return c

    coords_synth = synth_protein_ca(n_residues)
    L_synth = build_gnm_laplacian(coords_synth, CONTACT_CUTOFF)
    fiedler_synth = fiedler_eigenvector(L_synth)
    field_synth = voxelize_scalar_field(coords_synth, fiedler_synth, VOXEL_N, GAUSSIAN_SIGMA)
    psi_synth = hdc_lift_sign_only(field_synth)

    # ─── REAL cross-protein comparator (1BPI, different fold class) ─────────
    print(f"[fetch] {PDB_ID_CROSS} for real-vs-real cross-protein test")
    pdb_cross_text = fetch_pdb(PDB_ID_CROSS, PDB_URL_CROSS, OUT_DIR / f"{PDB_ID_CROSS}.pdb")
    coords_cross = parse_ca_coords(pdb_cross_text)
    # Center on same origin as ubiquitin for fair overlap measurement
    coords_cross_centered = coords_cross - coords_cross.mean(axis=0) + coords.mean(axis=0)
    L_cross = build_gnm_laplacian(coords_cross_centered, CONTACT_CUTOFF)
    fiedler_cross = fiedler_eigenvector(L_cross)
    field_cross = voxelize_scalar_field(coords_cross_centered, fiedler_cross, VOXEL_N, GAUSSIAN_SIGMA)
    psi_cross = hdc_lift_sign_only(field_cross)
    print(f"  {PDB_ID_CROSS}: {coords_cross.shape[0]} residues; fiedler range [{fiedler_cross.min():.3f}, {fiedler_cross.max():.3f}]")

    # Pure random hypervector
    psi_random = random_phase_vector(len(psi))

    # ─── Tests ──────────────────────────────────────────────────────────────
    print()
    print("=== HDC sign-only similarity tests (real ubiquitin) ===")

    t0 = time.perf_counter()
    sim_self = hdc_cosine(psi, psi)
    t_query = time.perf_counter() - t0

    sim_ps = hdc_cosine(psi, psi_ps)
    sim_pl = hdc_cosine(psi, psi_pl)
    sim_synth = hdc_cosine(psi, psi_synth)
    sim_cross = hdc_cosine(psi, psi_cross)
    sim_random = hdc_cosine(psi, psi_random)

    print(f"  self:                       {sim_self:.6f}  (expect 1.0)  [{1000*t_query:.3f} ms]")
    print(f"  small pert (σ=0.5Å):         {sim_ps:.6f}  (expect high; structure preserved)")
    print(f"  large pert (σ=3.0Å):         {sim_pl:.6f}  (expect lower)")
    print(f"  cross protein 1BPI (real):  {sim_cross:.6f}  (expect low; different fold class)")
    print(f"  independent synthetic:      {sim_synth:.6f}  (synthetic baseline)")
    print(f"  pure random:                {sim_random:.6f}  (expect near 0)")

    # Honest test: focused on REAL biology
    monotonic_real = (sim_self >= sim_ps >= sim_pl) and (sim_pl > sim_cross or abs(sim_pl - sim_cross) < 0.05) and (abs(sim_random) < 0.1)
    verdict = "PASS (real-vs-real)" if monotonic_real else "MIXED"
    print()
    print(f"=== Verdict: {verdict} ===")
    print(f"Perturbation axis: self={sim_self:.3f} ≥ pert_S={sim_ps:.3f} ≥ pert_L={sim_pl:.3f}")
    print(f"Cross-protein axis: 1UBQ vs 1BPI (real, different fold) = {sim_cross:.3f}")
    print(f"Random baseline:   {sim_random:.3f}")

    # ─── Comparison to synthetic baseline (PR #333 parent finding) ─────────
    print()
    print("=== Generalization check — synthetic vs real PDB ===")
    print(f"PR #333 synthetic:  self=1.000, pert_S=0.973, pert_L=0.171, indep=-0.111, random=0.002")
    print(f"Real 1UBQ:          self={sim_self:.3f}, pert_S={sim_ps:.3f}, pert_L={sim_pl:.3f}, 1BPI={sim_cross:.3f}, synth={sim_synth:.3f}, random={sim_random:.3f}")
    print()
    print("Render 1BPI slices for visual comparison...")
    render_three_slices(
        field_cross,
        f"Real BPTI (PDB {PDB_ID_CROSS}) Fiedler bipartition — cross-protein comparator",
        OUT_DIR / "protein-voxel-hdc-1bpi-slices.png",
    )

    # ─── Results ────────────────────────────────────────────────────────────
    records = [
        {
            "test": "real_pdb_1ubq",
            "pdb_id": PDB_ID,
            "n_residues": int(n_residues),
            "voxel_n": VOXEL_N,
            "hypervector_dim": len(psi),
            "fiedler_range": [float(fiedler.min()), float(fiedler.max())],
            "bipartition_split": [n_pos, n_neg],
            "eigh_ms": 1000 * t_eigh,
            "voxelize_ms": 1000 * t_voxelize,
            "hdc_lift_ms": 1000 * t_hdc_lift,
            "hdc_query_ms": 1000 * t_query,
        },
        {
            "test": "similarity_sign_only_real_1ubq",
            "self": sim_self,
            "pert_small": sim_ps,
            "pert_large": sim_pl,
            "cross_real_1bpi": sim_cross,
            "cross_synthetic": sim_synth,
            "random": sim_random,
            "monotonic_real_vs_real": monotonic_real,
            "verdict": verdict,
        },
        {
            "test": "generalization_synthetic_vs_real",
            "synthetic_pr333": {"self": 1.000, "pert_small": 0.973, "pert_large": 0.171, "independent": -0.111, "random": 0.002},
            "real_1ubq": {
                "self": sim_self, "pert_small": sim_ps, "pert_large": sim_pl,
                "cross_1bpi_real": sim_cross, "cross_synthetic": sim_synth, "random": sim_random
            },
        },
    ]
    with open(RESULTS_FILE, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    print()
    print(f"Results written to: {RESULTS_FILE.name}")
    print(f"Image written to:   protein-voxel-hdc-1ubq-slices.png")


if __name__ == "__main__":
    main()

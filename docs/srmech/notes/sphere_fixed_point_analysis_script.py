"""
Sphere fixed-point convergence analysis — what IS ψ*? (2026-05-12).

PR E of 3-PR stack. PR D (#341) found that the dynamic Laplacian on
PCA-canonical sphere substrate converges to a fixed point ψ* that is:
- Essentially orthogonal to the initial phase field (overlap 0.003)
- Rotation-invariant (1.000 across rotations)
- Cross-protein-orthogonal (0.000 between 1UBQ and 1BPI)

This PR analyzes what ψ* IS spatially. Three questions:
1. Project ψ* onto spherical harmonic basis Y_lm — which modes dominate?
2. Is the dominant SH mode a clean low-l pattern (substrate-intrinsic)
   or a high-l protein-specific pattern?
3. If 1UBQ ψ* and 1BPI ψ* are orthogonal, do they live on DIFFERENT
   dominant SH modes (which would explain orthogonality)?

Reproduce: `python -X utf8 docs/srmech/notes/sphere_fixed_point_analysis_script.py`
Deterministic seed 20260512.
"""

import time
import json
import urllib.request
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
import scipy.linalg
import scipy.special
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
L_MAX = 12  # SH analysis cap

OUT_DIR = Path(__file__).parent
RESULTS_FILE = OUT_DIR / "sphere-fixed-point-analysis-per-test-2026-05-12.ndjson"


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


def pca_canonical_rotation(coords, weights=None):
    centered = coords - coords.mean(axis=0)
    if weights is not None:
        w = np.abs(weights)
        if w.sum() > 0:
            mean_w = (w[:, None] * centered).sum(axis=0) / w.sum()
            centered = centered - mean_w
            cov = (w[:, None, None] * centered[:, :, None] * centered[:, None, :]).sum(axis=0) / w.sum()
        else:
            cov = centered.T @ centered / len(coords)
    else:
        cov = centered.T @ centered / len(coords)
    eigvals, eigvecs = scipy.linalg.eigh(cov)
    order = np.argsort(eigvals)[::-1]
    R = eigvecs[:, order].T
    if np.linalg.det(R) < 0: R[2] *= -1
    projected = centered @ R.T
    for k in range(3):
        if ((projected[:, k]) ** 3).sum() < 0: R[k] *= -1
    if np.linalg.det(R) < 0: R[2] *= -1
    return R


def canonicalize_coords(coords, weights=None):
    R = pca_canonical_rotation(coords, weights=weights)
    return (coords - coords.mean(axis=0)) @ R.T


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
            edges_i.append(v); edges_j.append(i * n_phi + (j + 1) % n_phi)
            if i + 1 < n_theta:
                edges_i.append(v); edges_j.append((i + 1) * n_phi + j)
    return np.array(edges_i), np.array(edges_j)


def build_weighted_laplacian(phases, edges_i, edges_j, n):
    dphase = phases[edges_i] - phases[edges_j]
    w = (1 + np.cos(dphase)) / 2
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


def run_dynamic_laplacian(coords, fiedler_values, canonicalize=True):
    if canonicalize:
        coords_c = canonicalize_coords(coords, weights=fiedler_values)
    else:
        coords_c = coords - coords.mean(axis=0)
    center = coords_c.mean(axis=0)
    radius = np.linalg.norm(coords_c - center, axis=1).max() * RADIUS_FACTOR
    field, thetas, phis = sample_fiedler_on_sphere(coords_c, fiedler_values, radius,
                                                       center, N_THETA, N_PHI)
    n = N_THETA * N_PHI
    edges_i, edges_j = build_sphere_graph_edges(N_THETA, N_PHI)
    phases_0 = fiedler_value_to_phase(field.ravel())
    phases = phases_0.copy()
    prev_fiedler = np.cos(phases_0) - 0.5
    for step in range(N_ITERATIONS):
        L_dyn = build_weighted_laplacian(phases, edges_i, edges_j, n)
        eigvals, eigvecs = sparse_fiedler(L_dyn)
        fiedler_new = align_sign(eigvecs[:, 1], prev_fiedler)
        phases_new = fiedler_value_to_phase(fiedler_new)
        if np.linalg.norm(phases_new - phases) < CONVERGENCE_TOL and step > 1:
            break
        phases = phases_new
        prev_fiedler = fiedler_new
    return {
        "phases_initial": phases_0, "phases_final": phases_new,
        "fiedler_final": fiedler_new, "thetas": thetas, "phis": phis,
        "n_iter": step + 1, "final_eigenvalue": float(eigvals[1]),
    }


# ─── SH analysis — the key contribution of this PR ──────────────────────

def sh_decomposition(field_on_sphere, thetas, phis, l_max):
    """Project (n_theta, n_phi) field onto Y_lm basis. Return dict {(l,m): c_lm}."""
    sin_t = np.sin(thetas)[:, None]
    dtheta = thetas[1] - thetas[0]
    dphi = phis[1] - phis[0]
    weights = sin_t * dtheta * dphi
    coeffs = {}
    for l in range(l_max + 1):
        for m in range(-l, l + 1):
            Y_lm = scipy.special.sph_harm_y(l, m, thetas[:, None], phis[None, :])
            coeffs[(l, m)] = complex(np.sum(field_on_sphere * np.conj(Y_lm) * weights))
    return coeffs


def sh_power_spectrum_from_coeffs(coeffs, l_max):
    P_l = np.zeros(l_max + 1)
    for (l, m), c in coeffs.items():
        P_l[l] += abs(c) ** 2
    return P_l


def find_dominant_modes(coeffs, n_top=10):
    """Return top-N (l, m) modes by |c_lm|²."""
    items = [(lm, abs(c) ** 2) for lm, c in coeffs.items()]
    items.sort(key=lambda x: x[1], reverse=True)
    return items[:n_top]


def main():
    print("=== Sphere fixed-point analysis — what IS ψ*? ===")
    print(f"Seed: {SEED}; L_MAX for analysis: {L_MAX}")
    print()

    coords_1ubq = fetch_pdb_ca("1UBQ")
    L_1ubq = build_gnm_laplacian(coords_1ubq, CONTACT_CUTOFF)
    fiedler_1ubq = fiedler_eigenvector(L_1ubq)

    coords_1bpi = fetch_pdb_ca("1BPI")
    L_1bpi = build_gnm_laplacian(coords_1bpi, CONTACT_CUTOFF)
    fiedler_1bpi = fiedler_eigenvector(L_1bpi)

    print("=== Compute fixed points ===")
    res_ubq_canon = run_dynamic_laplacian(coords_1ubq, fiedler_1ubq, canonicalize=True)
    res_ubq_raw = run_dynamic_laplacian(coords_1ubq, fiedler_1ubq, canonicalize=False)
    res_bpi_canon = run_dynamic_laplacian(coords_1bpi, fiedler_1bpi, canonicalize=True)
    print(f"  1UBQ canonical: converged at iter {res_ubq_canon['n_iter']}")
    print(f"  1UBQ raw:        converged at iter {res_ubq_raw['n_iter']}")
    print(f"  1BPI canonical: converged at iter {res_bpi_canon['n_iter']}")
    print()

    # SH decomposition of fixed points
    print("=== SH decomposition of ψ* (each fixed point projected onto Y_lm) ===")

    # For SH analysis, use the underlying Fiedler eigenvector (not the phase),
    # since the eigenvector has zero-mean structure that maps cleanly to SH
    psi_ubq_canon_2d = res_ubq_canon['fiedler_final'].reshape(N_THETA, N_PHI)
    psi_ubq_raw_2d = res_ubq_raw['fiedler_final'].reshape(N_THETA, N_PHI)
    psi_bpi_canon_2d = res_bpi_canon['fiedler_final'].reshape(N_THETA, N_PHI)

    thetas, phis = res_ubq_canon['thetas'], res_ubq_canon['phis']

    coeffs_ubq_canon = sh_decomposition(psi_ubq_canon_2d, thetas, phis, L_MAX)
    coeffs_ubq_raw = sh_decomposition(psi_ubq_raw_2d, thetas, phis, L_MAX)
    coeffs_bpi_canon = sh_decomposition(psi_bpi_canon_2d, thetas, phis, L_MAX)

    P_l_ubq_canon = sh_power_spectrum_from_coeffs(coeffs_ubq_canon, L_MAX)
    P_l_ubq_raw = sh_power_spectrum_from_coeffs(coeffs_ubq_raw, L_MAX)
    P_l_bpi_canon = sh_power_spectrum_from_coeffs(coeffs_bpi_canon, L_MAX)

    print(f"\n  Power per l-mode (top 5 by power):")
    print(f"  {'l':<4s} {'1UBQ canonical':>16s} {'1UBQ raw':>14s} {'1BPI canonical':>16s}")
    for l in range(L_MAX + 1):
        print(f"  {l:<4d} {P_l_ubq_canon[l]:>16.4f} {P_l_ubq_raw[l]:>14.4f} {P_l_bpi_canon[l]:>16.4f}")

    # Total power for normalization
    total_ubq_canon = P_l_ubq_canon.sum()
    total_ubq_raw = P_l_ubq_raw.sum()
    total_bpi_canon = P_l_bpi_canon.sum()

    print(f"\n  Total power: 1UBQ canon={total_ubq_canon:.4f}, "
          f"1UBQ raw={total_ubq_raw:.4f}, 1BPI canon={total_bpi_canon:.4f}")

    # Dominant l mode
    l_dom_ubq_canon = int(np.argmax(P_l_ubq_canon))
    l_dom_ubq_raw = int(np.argmax(P_l_ubq_raw))
    l_dom_bpi_canon = int(np.argmax(P_l_bpi_canon))
    print(f"\n  Dominant l-mode:")
    print(f"    1UBQ canonical: l = {l_dom_ubq_canon}  ({P_l_ubq_canon[l_dom_ubq_canon]/total_ubq_canon*100:.1f}% of power)")
    print(f"    1UBQ raw:        l = {l_dom_ubq_raw}  ({P_l_ubq_raw[l_dom_ubq_raw]/total_ubq_raw*100:.1f}% of power)")
    print(f"    1BPI canonical: l = {l_dom_bpi_canon}  ({P_l_bpi_canon[l_dom_bpi_canon]/total_bpi_canon*100:.1f}% of power)")

    # Top-N (l, m) modes
    print(f"\n=== Top 5 dominant (l, m) modes ===")
    print(f"\n  1UBQ canonical:")
    for lm, p in find_dominant_modes(coeffs_ubq_canon, n_top=5):
        print(f"    (l={lm[0]:2d}, m={lm[1]:+3d}): power={p:.4f} ({p/total_ubq_canon*100:.1f}%)")
    print(f"\n  1UBQ raw:")
    for lm, p in find_dominant_modes(coeffs_ubq_raw, n_top=5):
        print(f"    (l={lm[0]:2d}, m={lm[1]:+3d}): power={p:.4f} ({p/total_ubq_raw*100:.1f}%)")
    print(f"\n  1BPI canonical:")
    for lm, p in find_dominant_modes(coeffs_bpi_canon, n_top=5):
        print(f"    (l={lm[0]:2d}, m={lm[1]:+3d}): power={p:.4f} ({p/total_bpi_canon*100:.1f}%)")
    print()

    # Diagnose: are the dominant modes high-l (complex) or low-l (simple)?
    # If dominant l is small (l < 4), the fixed point is a "simple" sphere harmonic
    # If dominant l is large, the fixed point is "complex" / protein-specific
    print("=== Diagnosis ===")
    if l_dom_ubq_canon < 4:
        print(f"  1UBQ canonical ψ* is a LOW-l SH mode (l={l_dom_ubq_canon}) — substrate-intrinsic")
    else:
        print(f"  1UBQ canonical ψ* is a HIGH-l SH mode (l={l_dom_ubq_canon}) — protein-specific")

    # Compare: is the 1UBQ canonical vs raw dominant mode different?
    if l_dom_ubq_canon == l_dom_ubq_raw:
        print(f"  1UBQ canonical and raw share dominant l={l_dom_ubq_canon}")
    else:
        print(f"  1UBQ canonical dominant l={l_dom_ubq_canon} vs raw dominant l={l_dom_ubq_raw}")

    if l_dom_ubq_canon == l_dom_bpi_canon:
        print(f"  1UBQ canon and 1BPI canon share dominant l={l_dom_ubq_canon}")
        print(f"    → both proteins project onto same l-shell despite ψ* cosine 0.000")
        print(f"    → orthogonality arises from m-mode rotation within fixed l-shell")
    else:
        print(f"  1UBQ canon dominant l={l_dom_ubq_canon} vs 1BPI canon dominant l={l_dom_bpi_canon}")
        print(f"    → proteins project onto DIFFERENT l-shells → genuinely orthogonal modes")

    # Save
    records = [
        {"test": "config", "n_theta": N_THETA, "n_phi": N_PHI, "l_max": L_MAX},
        {"test": "convergence_summary",
         "ubq_canon_iter": res_ubq_canon['n_iter'],
         "ubq_raw_iter": res_ubq_raw['n_iter'],
         "bpi_canon_iter": res_bpi_canon['n_iter']},
        {"test": "power_spectrum_per_l",
         "ubq_canon": P_l_ubq_canon.tolist(),
         "ubq_raw": P_l_ubq_raw.tolist(),
         "bpi_canon": P_l_bpi_canon.tolist()},
        {"test": "dominant_l_mode",
         "ubq_canon": l_dom_ubq_canon,
         "ubq_raw": l_dom_ubq_raw,
         "bpi_canon": l_dom_bpi_canon},
        {"test": "dominant_l_power_fraction",
         "ubq_canon": float(P_l_ubq_canon[l_dom_ubq_canon] / total_ubq_canon),
         "ubq_raw": float(P_l_ubq_raw[l_dom_ubq_raw] / total_ubq_raw),
         "bpi_canon": float(P_l_bpi_canon[l_dom_bpi_canon] / total_bpi_canon)},
        {"test": "top_5_modes_ubq_canon",
         "modes": [[lm[0], lm[1], p] for lm, p in find_dominant_modes(coeffs_ubq_canon, 5)]},
        {"test": "top_5_modes_bpi_canon",
         "modes": [[lm[0], lm[1], p] for lm, p in find_dominant_modes(coeffs_bpi_canon, 5)]},
    ]
    with open(RESULTS_FILE, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    # Plot
    fig, axes = plt.subplots(2, 2, figsize=(14, 8))
    # Power spectra
    ls = np.arange(L_MAX + 1)
    axes[0, 0].plot(ls, P_l_ubq_canon / total_ubq_canon, "b-o", label="1UBQ canonical")
    axes[0, 0].plot(ls, P_l_ubq_raw / total_ubq_raw, "r-s", label="1UBQ raw")
    axes[0, 0].plot(ls, P_l_bpi_canon / total_bpi_canon, "g-^", label="1BPI canonical")
    axes[0, 0].set_xlabel("Spherical harmonic l"); axes[0, 0].set_ylabel("Fraction of power")
    axes[0, 0].set_title("SH power spectra of fixed points (normalized)")
    axes[0, 0].legend(); axes[0, 0].grid(alpha=0.3)

    # 1UBQ canonical fixed point on sphere
    axes[0, 1].imshow(psi_ubq_canon_2d, cmap="seismic", origin="lower", aspect="auto",
                       extent=[0, 360, 0, 180])
    axes[0, 1].set_title(f"1UBQ canonical ψ*  (dominant l={l_dom_ubq_canon})")
    axes[0, 1].set_xlabel("φ (degrees)"); axes[0, 1].set_ylabel("θ (degrees)")

    # 1UBQ raw fixed point on sphere
    axes[1, 0].imshow(psi_ubq_raw_2d, cmap="seismic", origin="lower", aspect="auto",
                       extent=[0, 360, 0, 180])
    axes[1, 0].set_title(f"1UBQ raw ψ*  (dominant l={l_dom_ubq_raw})")
    axes[1, 0].set_xlabel("φ (degrees)"); axes[1, 0].set_ylabel("θ (degrees)")

    # 1BPI canonical fixed point
    axes[1, 1].imshow(psi_bpi_canon_2d, cmap="seismic", origin="lower", aspect="auto",
                       extent=[0, 360, 0, 180])
    axes[1, 1].set_title(f"1BPI canonical ψ*  (dominant l={l_dom_bpi_canon})")
    axes[1, 1].set_xlabel("φ (degrees)"); axes[1, 1].set_ylabel("θ (degrees)")

    plt.tight_layout()
    plt.savefig(OUT_DIR / "sphere-fixed-point-analysis-2026-05-12.png", dpi=100)
    plt.close()

    print()
    print(f"Results: {RESULTS_FILE.name}")
    print(f"Plot:    sphere-fixed-point-analysis-2026-05-12.png")


if __name__ == "__main__":
    main()

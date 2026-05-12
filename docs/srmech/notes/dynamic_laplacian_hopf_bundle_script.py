"""
Dynamic Laplacian on Hopf bundle — non-trivial U(1) Chern=1 (2026-05-12).

PR F of stacked 3-PR sequence (PR D #341 + PR E #342 + this). Tests MFO
§VII.4.1.1 framework directly: dynamic Laplacian on a non-trivial principal
U(1)-bundle should give a fixed point that includes "fibre harmonic"
content beyond the base S^2 l=1 dipole.

Construction:
- Base: same lat-lon sphere as PR #340/#341 (60 × 120)
- Wilson U(1) phases on east-west edges, distributing Chern=1 flux uniformly
  over the n_theta × n_phi faces. ψ_ew(i, j) = i × dφ where dφ = 4π / (n_θ × n_φ).
- Adjacency: A_ij = w_ij × exp(i × Wilson_phase_ij), w_ij = cos²(Δphase/2)
- Laplacian: L = D - A, complex Hermitian (degree = sum |A_ij|)
- Iterate as before

Comparison to PR #341 (trivial bundle):
- Trivial (Chern=0): real symmetric L, converges to l=1 dipole (PR #342 finding)
- Non-trivial (Chern=1): complex Hermitian L; may converge to different mode

Key MFO §VII.4.1.1 prediction (continuum):
- Δ_{S³} on Hopf bundle has eigenvalues l(l+2)
- Δ_{S²} on base alone has eigenvalues l(l+1)
- Difference l(l+2) - l(l+1) = l = "fibre harmonic" content per S² mode
- At l=1: gap is 1; the dynamic L on Hopf bundle should "feel" this extra mode

Reproduce: `python -X utf8 docs/srmech/notes/dynamic_laplacian_hopf_bundle_script.py`
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
L_MAX = 12

OUT_DIR = Path(__file__).parent
RESULTS_FILE = OUT_DIR / "dynamic-laplacian-hopf-bundle-per-test-2026-05-12.ndjson"


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


def build_sphere_edges_with_metadata(n_theta, n_phi):
    """Return edges + flag for each indicating east-west (longitude) edges.
    East-west edges get Wilson phase; north-south edges don't."""
    edges_i, edges_j, is_ew, lat_i = [], [], [], []
    for i in range(n_theta):
        for j in range(n_phi):
            v = i * n_phi + j
            # East-west (longitude wraparound) at latitude i
            jp1 = (j + 1) % n_phi
            edges_i.append(v); edges_j.append(i * n_phi + jp1)
            is_ew.append(True); lat_i.append(i)
            # North-south (no Wilson phase)
            if i + 1 < n_theta:
                edges_i.append(v); edges_j.append((i + 1) * n_phi + j)
                is_ew.append(False); lat_i.append(i)
    return (np.array(edges_i), np.array(edges_j),
            np.array(is_ew, dtype=bool), np.array(lat_i))


def build_hopf_magnetic_laplacian(phases, edges_i, edges_j, is_ew, lat_i,
                                    n, n_theta, n_phi, chern=1, weight_floor=0.0):
    """
    Complex Hermitian magnetic Laplacian on sphere with non-trivial U(1) bundle.

    Wilson phase on east-west edges: ψ_ew(i, j) = i × dφ × chern
    where dφ = 4π / (n_θ × n_φ).

    Adjacency: A_uv = w_uv × exp(i × Wilson_phase_uv),
               A_vu = conj(A_uv) by Hermiticity.
    Laplacian: L_uv = -A_uv, L_uu = Σ_v |A_uv| (real degree).
    """
    dphase = phases[edges_i] - phases[edges_j]
    w_mag = (1 + np.cos(dphase)) / 2
    if weight_floor > 0:
        w_mag = np.maximum(w_mag, weight_floor)
    # Wilson phase per face: 4π × chern / (n_θ × n_φ)
    d_phi = 4 * np.pi * chern / (n_theta * n_phi)
    # Wilson phase on east-west edge at latitude i: i × d_phi (Landau gauge)
    wilson_phase = np.where(is_ew, lat_i * d_phi, 0.0)
    # Complex adjacency
    A_data = w_mag * np.exp(1j * wilson_phase)
    A = sp.coo_matrix((A_data, (edges_i, edges_j)), shape=(n, n)).tocsr()
    A = A + A.conj().T  # Hermitian
    # Degree from magnitude
    D_data = np.asarray(np.abs(A).sum(axis=1)).ravel()
    D = sp.diags(D_data)
    L = D - A
    return L.tocsr(), wilson_phase


def sparse_fiedler_complex(L, sigma_shift=1e-6):
    """For complex Hermitian L, find lowest few eigenvalues."""
    try:
        eigvals, eigvecs = spla.eigsh(L, k=3, sigma=-sigma_shift, which="LM")
    except Exception:
        eigvals, eigvecs = spla.eigsh(L, k=3, which="SM")
    idx = np.argsort(eigvals)
    return eigvals[idx], eigvecs[:, idx]


def fiedler_value_to_phase(values, scale=None):
    """For complex eigenvectors, use the REAL part for phase mapping."""
    real_vals = np.real(values)
    if scale is None:
        scale = np.max(np.abs(real_vals)) * 0.5 + 1e-12
    return np.pi / 2 * (1 + np.tanh(real_vals / scale))


def align_sign_complex(v_new, v_ref):
    """For complex vectors, align global phase, not just sign."""
    overlap = np.vdot(v_ref, v_new)
    if abs(overlap) > 0:
        phase = np.exp(-1j * np.angle(overlap))
        return v_new * phase
    return v_new


def run_dynamic_laplacian_hopf(coords, fiedler_values, chern=1):
    """Full pipeline with PCA canonicalization + Hopf-bundle dynamic L."""
    coords_c = canonicalize_coords(coords, weights=fiedler_values)
    center = coords_c.mean(axis=0)
    radius = np.linalg.norm(coords_c - center, axis=1).max() * RADIUS_FACTOR
    field, thetas, phis = sample_fiedler_on_sphere(coords_c, fiedler_values, radius,
                                                       center, N_THETA, N_PHI)
    n = N_THETA * N_PHI
    edges_i, edges_j, is_ew, lat_i = build_sphere_edges_with_metadata(N_THETA, N_PHI)
    phases_0 = fiedler_value_to_phase(field.ravel())
    phases = phases_0.copy()
    prev_fiedler = (np.cos(phases_0) - 0.5).astype(np.complex128)
    history = []
    for step in range(N_ITERATIONS):
        L_dyn, _ = build_hopf_magnetic_laplacian(
            phases, edges_i, edges_j, is_ew, lat_i,
            n, N_THETA, N_PHI, chern=chern,
        )
        eigvals, eigvecs = sparse_fiedler_complex(L_dyn)
        fiedler_new = align_sign_complex(eigvecs[:, 1], prev_fiedler)
        phases_new = fiedler_value_to_phase(fiedler_new)
        phase_change = float(np.linalg.norm(phases_new - phases))
        overlap = float(abs(np.corrcoef(phases_new, phases_0)[0, 1]))
        history.append({
            "step": step,
            "fiedler_eigenvalue_real": float(eigvals[1].real),
            "fiedler_eigenvalue_imag": float(eigvals[1].imag),
            "top_3_real": [float(x.real) for x in eigvals],
            "phase_l2_change": phase_change,
            "overlap_with_initial": overlap,
            "phases": phases_new.copy(),
            "fiedler_complex": fiedler_new.copy(),
        })
        if phase_change < CONVERGENCE_TOL and step > 1:
            break
        phases = phases_new
        prev_fiedler = fiedler_new
    return history, phases_0, thetas, phis


def sh_decomposition(field_2d, thetas, phis, l_max):
    sin_t = np.sin(thetas)[:, None]
    dtheta = thetas[1] - thetas[0]
    dphi = phis[1] - phis[0]
    weights = sin_t * dtheta * dphi
    coeffs = {}
    for l in range(l_max + 1):
        for m in range(-l, l + 1):
            Y_lm = scipy.special.sph_harm_y(l, m, thetas[:, None], phis[None, :])
            coeffs[(l, m)] = complex(np.sum(field_2d * np.conj(Y_lm) * weights))
    return coeffs


def power_per_l(coeffs, l_max):
    P_l = np.zeros(l_max + 1)
    for (l, m), c in coeffs.items():
        P_l[l] += abs(c) ** 2
    return P_l


def main():
    print("=== Dynamic Laplacian on Hopf bundle (non-trivial U(1), Chern=1) ===")
    print(f"Seed: {SEED}; sphere: {N_THETA}×{N_PHI}; Chern=1 flux 4π distributed uniformly")
    print()

    coords = fetch_pdb_ca("1UBQ")
    L_protein = build_gnm_laplacian(coords, CONTACT_CUTOFF)
    fiedler = fiedler_eigenvector(L_protein)
    print(f"[Setup] 1UBQ: {coords.shape[0]} Cα")
    print()

    # Run Chern=0 (trivial, baseline matching PR #341/342)
    print("=== Run 1: Chern=0 (trivial bundle, baseline) ===")
    history_c0, phases_0_c0, thetas, phis = run_dynamic_laplacian_hopf(coords, fiedler, chern=0)
    print(f"  Converged at step {len(history_c0)-1}; final λ_Fiedler={history_c0[-1]['fiedler_eigenvalue_real']:.5f}")
    print(f"  Final overlap with initial: {history_c0[-1]['overlap_with_initial']:.4f}")
    print()

    # Run Chern=1 (non-trivial Hopf bundle)
    print("=== Run 2: Chern=1 (non-trivial Hopf bundle) ===")
    history_c1, phases_0_c1, _, _ = run_dynamic_laplacian_hopf(coords, fiedler, chern=1)
    print(f"  Converged at step {len(history_c1)-1}; final λ_Fiedler={history_c1[-1]['fiedler_eigenvalue_real']:.5f}")
    print(f"  Final overlap with initial: {history_c1[-1]['overlap_with_initial']:.4f}")
    print()

    # Run Chern=2 (also non-trivial)
    print("=== Run 3: Chern=2 (higher Chern bundle) ===")
    history_c2, _, _, _ = run_dynamic_laplacian_hopf(coords, fiedler, chern=2)
    print(f"  Converged at step {len(history_c2)-1}; final λ_Fiedler={history_c2[-1]['fiedler_eigenvalue_real']:.5f}")
    print(f"  Final overlap with initial: {history_c2[-1]['overlap_with_initial']:.4f}")
    print()

    # Compare eigenvalues: l(l+1) vs l(l+2) prediction
    print("=== MFO §VII.4.1.1 PREDICTION TEST ===")
    print(f"  Continuum prediction: Δ_S² eigenvalues = l(l+1), Δ_S³ eigenvalues = l(l+2)")
    print(f"  l=1 case: l(l+1) = 2, l(l+2) = 3, ratio = 1.5")
    print()
    print(f"  Measured λ_Fiedler at convergence:")
    lam_c0 = history_c0[-1]['fiedler_eigenvalue_real']
    lam_c1 = history_c1[-1]['fiedler_eigenvalue_real']
    lam_c2 = history_c2[-1]['fiedler_eigenvalue_real']
    print(f"    Chern=0: {lam_c0:.5f}  (continuum-Δ_S² l=1 baseline)")
    print(f"    Chern=1: {lam_c1:.5f}  (Hopf bundle Δ_S³ l=1?)")
    print(f"    Chern=2: {lam_c2:.5f}  (Chern=2 bundle)")
    if lam_c0 > 0:
        print(f"    Ratio Chern=1 / Chern=0: {lam_c1 / lam_c0:.3f}  (continuum predicts 1.5)")
        print(f"    Ratio Chern=2 / Chern=0: {lam_c2 / lam_c0:.3f}")
    print()

    # SH decomposition of fixed points (using real part of complex eigenvector)
    fc0 = history_c0[-1]['fiedler_complex']
    fc1 = history_c1[-1]['fiedler_complex']
    fc2 = history_c2[-1]['fiedler_complex']
    coeffs_c0 = sh_decomposition(np.real(fc0).reshape(N_THETA, N_PHI), thetas, phis, L_MAX)
    coeffs_c1_re = sh_decomposition(np.real(fc1).reshape(N_THETA, N_PHI), thetas, phis, L_MAX)
    coeffs_c1_im = sh_decomposition(np.imag(fc1).reshape(N_THETA, N_PHI), thetas, phis, L_MAX)
    P_c0 = power_per_l(coeffs_c0, L_MAX)
    P_c1_re = power_per_l(coeffs_c1_re, L_MAX)
    P_c1_im = power_per_l(coeffs_c1_im, L_MAX)

    print("=== SH power distribution of fixed points (top 5 l-modes) ===")
    print(f"{'l':<4s} {'Chern=0 (real)':>16s} {'Chern=1 (Re)':>14s} {'Chern=1 (Im)':>14s}")
    for l in range(min(8, L_MAX + 1)):
        print(f"{l:<4d} {P_c0[l]:>16.5f} {P_c1_re[l]:>14.5f} {P_c1_im[l]:>14.5f}")

    # Dominant l per Chern
    l_dom_c0 = int(np.argmax(P_c0))
    l_dom_c1_re = int(np.argmax(P_c1_re))
    l_dom_c1_im = int(np.argmax(P_c1_im))
    print()
    print(f"  Dominant l: Chern=0 → {l_dom_c0}; Chern=1 (Re) → {l_dom_c1_re}; Chern=1 (Im) → {l_dom_c1_im}")

    # Verdict
    print()
    print("=== Verdict ===")
    if abs(fc1.imag).max() > 1e-3:
        print(f"  Chern=1 fixed point has NON-TRIVIAL IMAGINARY part (max |Im|: {abs(fc1.imag).max():.4f})")
        print(f"  → fibre harmonic content present (matches MFO §VII.4.1.1 prediction)")
    else:
        print(f"  Chern=1 fixed point is essentially real (max |Im|: {abs(fc1.imag).max():.4e})")
        print(f"  → Wilson phases don't induce imaginary fibre content at this discretization")

    if abs(lam_c1 - lam_c0) / lam_c0 > 0.1:
        print(f"  Chern=1 eigenvalue ({lam_c1:.4f}) is DISTINCT from Chern=0 ({lam_c0:.4f})")
        print(f"  → non-trivial bundle gives different spectral content (qualitatively consistent with MFO)")
    else:
        print(f"  Chern=1 eigenvalue ({lam_c1:.4f}) ≈ Chern=0 eigenvalue ({lam_c0:.4f})")
        print(f"  → discretization may not resolve fibre harmonic at this resolution")

    # Save
    records = [
        {"test": "convergence_summary",
         "chern_0_iter": len(history_c0), "chern_0_lambda": lam_c0,
         "chern_1_iter": len(history_c1), "chern_1_lambda": lam_c1,
         "chern_2_iter": len(history_c2), "chern_2_lambda": lam_c2},
        {"test": "sh_power_chern_0", "P_l": P_c0.tolist()},
        {"test": "sh_power_chern_1_real", "P_l": P_c1_re.tolist()},
        {"test": "sh_power_chern_1_imag", "P_l": P_c1_im.tolist()},
        {"test": "complex_content_chern_1",
         "max_abs_imag": float(abs(fc1.imag).max()),
         "max_abs_real": float(abs(fc1.real).max()),
         "ratio_imag_to_real": float(abs(fc1.imag).max() / (abs(fc1.real).max() + 1e-12))},
        {"test": "mfo_prediction",
         "continuum_l_1_ratio_S3_to_S2": 1.5,
         "measured_ratio_chern_1_to_0": float(lam_c1 / lam_c0) if lam_c0 > 0 else None,
         "measured_ratio_chern_2_to_0": float(lam_c2 / lam_c0) if lam_c0 > 0 else None},
    ]
    with open(RESULTS_FILE, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    # Plot
    fig, axes = plt.subplots(2, 3, figsize=(16, 8))
    # Power spectra
    ls = np.arange(L_MAX + 1)
    axes[0, 0].plot(ls, P_c0, "k-o", label="Chern=0")
    axes[0, 0].plot(ls, P_c1_re, "b-s", label="Chern=1 (Re)")
    axes[0, 0].plot(ls, P_c1_im, "r-^", label="Chern=1 (Im)")
    axes[0, 0].set_xlabel("l"); axes[0, 0].set_ylabel("Power")
    axes[0, 0].set_yscale("log")
    axes[0, 0].set_title("SH power vs Chern class")
    axes[0, 0].legend(); axes[0, 0].grid(alpha=0.3)
    # Real part Chern=0
    axes[0, 1].imshow(np.real(fc0).reshape(N_THETA, N_PHI), cmap="seismic", origin="lower", aspect="auto",
                       extent=[0, 360, 0, 180])
    axes[0, 1].set_title(f"Chern=0 ψ* (l={l_dom_c0}, λ={lam_c0:.4f})")
    # Real part Chern=1
    axes[0, 2].imshow(np.real(fc1).reshape(N_THETA, N_PHI), cmap="seismic", origin="lower", aspect="auto",
                       extent=[0, 360, 0, 180])
    axes[0, 2].set_title(f"Chern=1 Re(ψ*) (l={l_dom_c1_re}, λ={lam_c1:.4f})")
    # Imaginary part Chern=1
    axes[1, 0].imshow(np.imag(fc1).reshape(N_THETA, N_PHI), cmap="seismic", origin="lower", aspect="auto",
                       extent=[0, 360, 0, 180])
    axes[1, 0].set_title(f"Chern=1 Im(ψ*) (l={l_dom_c1_im}, fibre signature)")
    # Convergence
    axes[1, 1].plot([h["step"] for h in history_c0], [h["phase_l2_change"] for h in history_c0], "k-o", label="Chern=0")
    axes[1, 1].plot([h["step"] for h in history_c1], [h["phase_l2_change"] for h in history_c1], "b-s", label="Chern=1")
    axes[1, 1].plot([h["step"] for h in history_c2], [h["phase_l2_change"] for h in history_c2], "r-^", label="Chern=2")
    axes[1, 1].set_xlabel("Iteration"); axes[1, 1].set_ylabel("||Δphase||")
    axes[1, 1].set_yscale("log")
    axes[1, 1].axhline(CONVERGENCE_TOL, color="gray", linestyle="--", alpha=0.5)
    axes[1, 1].set_title("Convergence vs Chern")
    axes[1, 1].legend(); axes[1, 1].grid(alpha=0.3)
    # Eigenvalues
    axes[1, 2].bar(["Chern=0", "Chern=1", "Chern=2"], [lam_c0, lam_c1, lam_c2], color=["k", "b", "r"], alpha=0.6)
    axes[1, 2].axhline(lam_c0 * 1.5, color="gray", linestyle="--", label="MFO predicts 1.5×")
    axes[1, 2].set_ylabel("λ_Fiedler at convergence")
    axes[1, 2].set_title("Eigenvalue scaling with Chern class")
    axes[1, 2].legend(); axes[1, 2].grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUT_DIR / "dynamic-laplacian-hopf-bundle-2026-05-12.png", dpi=100)
    plt.close()

    print()
    print(f"Results: {RESULTS_FILE.name}")
    print(f"Plot:    dynamic-laplacian-hopf-bundle-2026-05-12.png")


if __name__ == "__main__":
    main()

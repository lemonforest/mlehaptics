"""
Explicit S^3 discretization with fibre dimension — MFO §VII.4.1.1 test (2026-05-12).

Follow-up to PR #343 (Wilson-phase-on-S² approximation gave qualitative MFO
consistency but quantitative gap). PR F's discretization missed the fibre
dimension; this PR adds it explicitly.

Construction:
- Coordinates (i, j, k): i ∈ [0, n_θ) lat, j ∈ [0, n_φ) lon, k ∈ [0, n_ψ) fibre
- Trivial bundle (test A): S² × S¹ Cartesian product. Edges in θ, φ, ψ
  directions; no cross-coupling.
- Hopf bundle (test B): same lattice + Wilson phases on φ-direction edges
  that depend on base position (Hopf connection: A_φ = -cos θ).

Continuum MFO §VII.4.1.1 prediction:
- Δ_{S²} eigenvalues l(l+1) → smallest non-zero (l=1): 2
- Δ_{S²×S¹} ≈ min(2 from S², 1 from S¹) = 1 (trivial product)
- Δ_{S³} eigenvalues l(l+2) → smallest non-zero (l=1): 3
- Ratio S³ / (S²×S¹) ≈ 3 / 1 = 3 (or 3/2 = 1.5 if compared to bare S² l=1)

Tests:
1. Build trivial S² × S¹ lattice; measure lowest non-zero eigenvalue λ_A
2. Build same lattice + Hopf connection Wilson phases; measure λ_B
3. Check ratio λ_B / λ_A vs continuum prediction

Reproduce: `python -X utf8 docs/srmech/notes/explicit_s3_hopf_bundle_script.py`
"""

import time
import json
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

N_THETA = 20
N_PHI = 40
N_PSI = 20

OUT_DIR = Path(__file__).parent
RESULTS_FILE = OUT_DIR / "explicit-s3-hopf-bundle-per-test-2026-05-12.ndjson"


def build_s2_s1_product_lattice(n_theta, n_phi, n_psi):
    """
    Build edges for S² × S¹ product lattice with combinatorial weighting.

    Returns (edges_i, edges_j, edge_type, lat_i) — last two for adding
    Wilson phases later.

    edge_type: 0 = θ direction, 1 = φ direction, 2 = ψ direction (fibre).
    lat_i: latitude index for the edge (matters for cos θ Wilson phase).
    """
    n = n_theta * n_phi * n_psi
    def vid(i, j, k):
        return (i * n_phi + j) * n_psi + k
    edges_i, edges_j, edge_type, lat_i = [], [], [], []
    for i in range(n_theta):
        for j in range(n_phi):
            for k in range(n_psi):
                v = vid(i, j, k)
                # θ-direction (no periodicity; clamped at poles)
                if i + 1 < n_theta:
                    edges_i.append(v); edges_j.append(vid(i + 1, j, k))
                    edge_type.append(0); lat_i.append(i)
                # φ-direction (periodic)
                jp = (j + 1) % n_phi
                edges_i.append(v); edges_j.append(vid(i, jp, k))
                edge_type.append(1); lat_i.append(i)
                # ψ-direction (periodic — S¹ fibre)
                kp = (k + 1) % n_psi
                edges_i.append(v); edges_j.append(vid(i, j, kp))
                edge_type.append(2); lat_i.append(i)
    return n, np.array(edges_i), np.array(edges_j), np.array(edge_type), np.array(lat_i)


def build_magnetic_laplacian(n, edges_i, edges_j, edge_type, lat_i,
                              n_theta, n_phi, chern=0, hopf=False):
    """
    Build complex Hermitian Laplacian.

    chern=0, hopf=False: trivial product S² × S¹ (real symmetric)
    chern=k, hopf=True: Hopf bundle with connection A_φ = chern × (-cos θ)
                         (Wilson phase only on φ-direction edges).
    """
    n_edges = len(edges_i)
    # Theta and psi coords for Hopf phase
    thetas = np.linspace(0.01, np.pi - 0.01, n_theta)
    # Phase per φ-direction edge at latitude i:
    # Continuum: A_φ = -cos θ (Hopf connection in north-patch gauge)
    # Discrete: Wilson_phase = A_φ × dφ × chern = -cos(θ_i) × (2π/n_phi) × chern
    if hopf:
        # Phase on φ-direction edges
        phi_phases = -chern * np.cos(thetas) * (2 * np.pi / n_phi)
        wilson = np.where(edge_type == 1, phi_phases[lat_i], 0.0)
    else:
        wilson = np.zeros(n_edges)

    # Unit-weighted combinatorial Laplacian with magnetic Wilson phases
    A_data = np.exp(1j * wilson)
    A = sp.coo_matrix((A_data, (edges_i, edges_j)), shape=(n, n)).tocsr()
    A = A + A.conj().T  # Hermitian
    D_data = np.asarray(np.abs(A).sum(axis=1)).ravel()
    D = sp.diags(D_data)
    return (D - A).tocsr()


def get_lowest_nonzero_eigenvalues(L, k=5, sigma_shift=1e-6):
    """Get lowest few eigenvalues of complex Hermitian L using shift-invert."""
    try:
        eigvals, eigvecs = spla.eigsh(L, k=k, sigma=-sigma_shift, which="LM")
    except Exception:
        eigvals, eigvecs = spla.eigsh(L, k=k, which="SM")
    idx = np.argsort(eigvals.real)
    return eigvals[idx].real, eigvecs[:, idx]


def main():
    print("=== Explicit S³ Hopf-bundle test for MFO §VII.4.1.1 ===")
    print(f"Lattice: {N_THETA} × {N_PHI} × {N_PSI} = {N_THETA * N_PHI * N_PSI:,} nodes")
    print()

    n, edges_i, edges_j, edge_type, lat_i = build_s2_s1_product_lattice(N_THETA, N_PHI, N_PSI)
    n_edges_each = (edge_type == 0).sum(), (edge_type == 1).sum(), (edge_type == 2).sum()
    print(f"Edges: θ={n_edges_each[0]}, φ={n_edges_each[1]}, ψ={n_edges_each[2]}; total {len(edges_i):,}")
    print()

    # ─── Test A: Trivial product S² × S¹ ──────────────────────────────────
    print("=== Test A: Trivial product S² × S¹ (Chern=0) ===")
    t0 = time.perf_counter()
    L_A = build_magnetic_laplacian(n, edges_i, edges_j, edge_type, lat_i,
                                     N_THETA, N_PHI, chern=0, hopf=False)
    eigvals_A, _ = get_lowest_nonzero_eigenvalues(L_A, k=8)
    t_A = time.perf_counter() - t0
    print(f"  Computed in {1000*t_A:.0f} ms")
    print(f"  Top-8 eigenvalues: {[f'{x:.5f}' for x in eigvals_A]}")
    lam_A = eigvals_A[1]  # smallest non-zero (skip the kernel eigenvalue ~ 0)
    print(f"  λ_2 (smallest non-zero): {lam_A:.5f}")
    print()

    # ─── Test B: Hopf bundle with Chern=1 ─────────────────────────────────
    print("=== Test B: Hopf bundle with Chern=1 (explicit fibre dim) ===")
    t0 = time.perf_counter()
    L_B = build_magnetic_laplacian(n, edges_i, edges_j, edge_type, lat_i,
                                     N_THETA, N_PHI, chern=1, hopf=True)
    eigvals_B, _ = get_lowest_nonzero_eigenvalues(L_B, k=8)
    t_B = time.perf_counter() - t0
    print(f"  Computed in {1000*t_B:.0f} ms")
    print(f"  Top-8 eigenvalues: {[f'{x:.5f}' for x in eigvals_B]}")
    lam_B = eigvals_B[1]  # smallest non-zero
    print(f"  λ_2 (smallest non-zero): {lam_B:.5f}")
    print()

    # ─── Test C: Higher Chern (numerical scaling) ─────────────────────────
    print("=== Test C: Chern=2 ===")
    t0 = time.perf_counter()
    L_C = build_magnetic_laplacian(n, edges_i, edges_j, edge_type, lat_i,
                                     N_THETA, N_PHI, chern=2, hopf=True)
    eigvals_C, _ = get_lowest_nonzero_eigenvalues(L_C, k=8)
    t_C = time.perf_counter() - t0
    print(f"  Computed in {1000*t_C:.0f} ms")
    print(f"  Top-8 eigenvalues: {[f'{x:.5f}' for x in eigvals_C]}")
    lam_C = eigvals_C[1]
    print(f"  λ_2 (smallest non-zero): {lam_C:.5f}")
    print()

    # ─── Test D: also try a heavier Chern (sees if it scales) ─────────────
    print("=== Test D: Chern=4 ===")
    L_D = build_magnetic_laplacian(n, edges_i, edges_j, edge_type, lat_i,
                                     N_THETA, N_PHI, chern=4, hopf=True)
    eigvals_D, _ = get_lowest_nonzero_eigenvalues(L_D, k=8)
    lam_D = eigvals_D[1]
    print(f"  λ_2 (smallest non-zero): {lam_D:.5f}")
    print()

    # ─── MFO prediction analysis ──────────────────────────────────────────
    print("=== MFO §VII.4.1.1 PREDICTION TEST ===")
    print(f"  Continuum: Δ_{{S²}} eigenvalues l(l+1), Δ_{{S³}} eigenvalues l(l+2)")
    print(f"  At l=1: l(l+1)=2, l(l+2)=3, ratio = 3/2 = 1.5")
    print(f"  At l=1, S²×S¹ trivial product: min(2, 1)=1 (fibre m=1 wins)")
    print(f"  Continuum ratio S³ / (S²×S¹): 3 / 1 = 3")
    print()
    print(f"  Measured (discrete, {N_THETA}×{N_PHI}×{N_PSI} lattice):")
    print(f"    Trivial (Chern=0):       λ_2 = {lam_A:.5f}")
    print(f"    Hopf bundle (Chern=1):   λ_2 = {lam_B:.5f}")
    print(f"    Chern=2:                 λ_2 = {lam_C:.5f}")
    print(f"    Chern=4:                 λ_2 = {lam_D:.5f}")
    if lam_A > 0:
        print(f"    Ratio B/A:  {lam_B / lam_A:.4f}  (continuum predicts 3.0)")
        print(f"    Ratio C/A:  {lam_C / lam_A:.4f}")
        print(f"    Ratio D/A:  {lam_D / lam_A:.4f}")
    print()

    # ─── Verdict ──────────────────────────────────────────────────────────
    print("=== Verdict ===")
    ratio_BA = lam_B / lam_A if lam_A > 0 else float('inf')
    if 0.8 < ratio_BA < 1.2:
        print(f"  Hopf bundle (Chern=1) and trivial product have nearly identical λ_2 ({ratio_BA:.3f})")
        print(f"  → at this lattice resolution, fibre harmonic doesn't separate from base modes")
        print(f"  → continuum 3:1 ratio prediction NOT recovered")
    elif ratio_BA > 1.5:
        print(f"  Hopf bundle (Chern=1) has SIGNIFICANTLY HIGHER λ_2 ({ratio_BA:.3f}× trivial)")
        print(f"  → consistent with continuum prediction direction (S³ > S²×S¹)")
        if abs(ratio_BA - 3.0) < 0.5:
            print(f"  → ratio close to continuum 3.0 — MFO §VII.4.1.1 prediction VALIDATED")
        else:
            print(f"  → ratio {ratio_BA:.2f} differs from continuum 3.0 (discretization effects)")
    elif ratio_BA < 0.8:
        print(f"  Hopf bundle (Chern=1) has LOWER λ_2 ({ratio_BA:.3f}× trivial)")
        print(f"  → wrong direction vs continuum prediction")
    else:
        print(f"  Ratio {ratio_BA:.3f} — modest separation, not matching continuum")

    # Save
    records = [
        {"test": "config", "n_theta": N_THETA, "n_phi": N_PHI, "n_psi": N_PSI,
         "n_total": n, "n_edges": len(edges_i)},
        {"test": "trivial_product", "lambda_2": float(lam_A),
         "top_8_eigenvalues": [float(x) for x in eigvals_A]},
        {"test": "hopf_chern_1", "lambda_2": float(lam_B),
         "top_8_eigenvalues": [float(x) for x in eigvals_B],
         "ratio_to_trivial": float(lam_B / lam_A) if lam_A > 0 else None},
        {"test": "hopf_chern_2", "lambda_2": float(lam_C),
         "ratio_to_trivial": float(lam_C / lam_A) if lam_A > 0 else None},
        {"test": "hopf_chern_4", "lambda_2": float(lam_D),
         "ratio_to_trivial": float(lam_D / lam_A) if lam_A > 0 else None},
        {"test": "mfo_prediction",
         "continuum_ratio_s3_to_s2_l1": 1.5,
         "continuum_ratio_s3_to_s2_times_s1": 3.0,
         "measured_ratio_B_A": float(lam_B / lam_A) if lam_A > 0 else None},
    ]
    with open(RESULTS_FILE, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    # Plot eigenvalue scaling with Chern
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    cherns = [0, 1, 2, 4]
    lambdas = [lam_A, lam_B, lam_C, lam_D]
    axes[0].plot(cherns, lambdas, "b-o", markersize=10)
    axes[0].axhline(lam_A, color="gray", linestyle="--", alpha=0.5, label=f"Chern=0 baseline ({lam_A:.3f})")
    axes[0].axhline(lam_A * 3, color="green", linestyle=":", alpha=0.5, label="Continuum S³/S²×S¹ = 3")
    axes[0].set_xlabel("Chern class"); axes[0].set_ylabel("λ_2 (lowest non-zero eigenvalue)")
    axes[0].set_title("Eigenvalue vs Chern class on explicit S³")
    axes[0].legend(); axes[0].grid(alpha=0.3)

    # Plot spectrum
    axes[1].plot(eigvals_A[:8], "k-o", label="Trivial S²×S¹")
    axes[1].plot(eigvals_B[:8], "b-s", label="Hopf Chern=1")
    axes[1].plot(eigvals_C[:8], "r-^", label="Chern=2")
    axes[1].plot(eigvals_D[:8], "g-v", label="Chern=4")
    axes[1].set_xlabel("Eigenvalue index"); axes[1].set_ylabel("Eigenvalue")
    axes[1].set_title("Low-lying spectrum")
    axes[1].legend(); axes[1].grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUT_DIR / "explicit-s3-hopf-bundle-2026-05-12.png", dpi=100)
    plt.close()

    print()
    print(f"Results: {RESULTS_FILE.name}")
    print(f"Plot:    explicit-s3-hopf-bundle-2026-05-12.png")


if __name__ == "__main__":
    main()

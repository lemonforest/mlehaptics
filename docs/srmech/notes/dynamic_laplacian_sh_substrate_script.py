"""
Dynamic Laplacian on SH substrate — revisit of falsified PR #335 (2026-05-12).

PR C of 3-PR sequence after #338 + #339. The PR #335 falsification found that
naive dynamic-Laplacian iteration via phase-coherence weights collapsed
because the voxel active region was DISCONNECTED: positive and negative
Fiedler regions formed separate non-touching 3D blobs, so the bipartition
killed its own Laplacian.

User question: does this work better on a SH substrate that doesn't pre-bake
the bipartition into geometry?

Setup: sample Fiedler field on a SPHERE (lat-lon grid). The sphere surface
is globally connected — positive and negative regions share the surface;
there's no geometric disconnection. Apply the same dynamic-Laplacian
iteration as PR #335 but on this connected substrate.

If it now converges to a non-trivial fixed point: the user's original
architectural intuition was sound — the previous spike just had the
wrong substrate.

If it still degenerates: the dynamic-Laplacian concept is more
fundamentally flawed than substrate-choice.

Reproduce: `python -X utf8 docs/srmech/notes/dynamic_laplacian_sh_substrate_script.py`
Deterministic seed 20260512. Reuses cached PDB.
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
N_THETA = 60   # latitude grid
N_PHI = 120    # longitude grid
RADIUS_FACTOR = 1.2  # sample at intrinsic_radius × this
N_ITERATIONS = 30
CONVERGENCE_TOL = 1e-4

OUT_DIR = Path(__file__).parent
RESULTS_FILE = OUT_DIR / "dynamic-laplacian-sh-substrate-per-step-2026-05-12.ndjson"


# ─── PDB + Fiedler + voxelize (reused) ────────────────────────────────────

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


def sample_fiedler_on_sphere(coords, fiedler_values, radius, center,
                              n_theta, n_phi, sigma=4.0):
    """Sample the Gaussian-smeared Fiedler field on a sphere of given radius.

    Returns: (theta, phi) → field value, shape (n_theta, n_phi).
    """
    thetas = np.linspace(0.01, np.pi - 0.01, n_theta)
    phis = np.linspace(0, 2 * np.pi, n_phi, endpoint=False)
    TH, PH = np.meshgrid(thetas, phis, indexing="ij")
    # Sphere points in 3D
    x = center[0] + radius * np.sin(TH) * np.cos(PH)
    y = center[1] + radius * np.sin(TH) * np.sin(PH)
    z = center[2] + radius * np.cos(TH)
    grid_pts = np.stack([x, y, z], axis=-1)  # (n_theta, n_phi, 3)
    # Gaussian-smeared Fiedler field at each sphere point
    field = np.zeros((n_theta, n_phi))
    for i in range(coords.shape[0]):
        d_sq = np.sum((grid_pts - coords[i]) ** 2, axis=-1)
        field += fiedler_values[i] * np.exp(-d_sq / (2 * sigma ** 2))
    return field, thetas, phis


# ─── Sphere graph (lat-lon grid with periodicity in longitude) ────────

def build_sphere_graph_edges(n_theta, n_phi):
    """6-connected (modulo poles) lat-lon graph. Periodic in phi."""
    edges_i, edges_j = [], []
    for i in range(n_theta):
        for j in range(n_phi):
            v = i * n_phi + j
            # Neighbor +φ (periodic in longitude)
            jp1 = (j + 1) % n_phi
            v_phi = i * n_phi + jp1
            edges_i.append(v); edges_j.append(v_phi)
            # Neighbor +θ (not periodic; clamped at poles)
            if i + 1 < n_theta:
                v_th = (i + 1) * n_phi + j
                edges_i.append(v); edges_j.append(v_th)
    return np.array(edges_i), np.array(edges_j)


def check_connected(edges_i, edges_j, n):
    visited = np.zeros(n, dtype=bool)
    visited[0] = True
    nbrs = {}
    for a, b in zip(edges_i, edges_j):
        nbrs.setdefault(int(a), []).append(int(b))
        nbrs.setdefault(int(b), []).append(int(a))
    queue = [0]
    while queue:
        v = queue.pop()
        for u in nbrs.get(v, []):
            if not visited[u]:
                visited[u] = True
                queue.append(u)
    return int(visited.sum()), int(n - visited.sum())


def build_weighted_laplacian(phases, edges_i, edges_j, n, weight_floor=0.0):
    """Same construction as PR #335: w_ij = cos²((θ_i - θ_j)/2)."""
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


def classify_outcome(history, initial_phases):
    """Classify by FINAL step's behavior, not by max-over-last-3 which
    can be misled when convergence accelerates suddenly."""
    last_phases = history[-1]["phases_snapshot"]
    overlap_final = abs(np.corrcoef(last_phases, initial_phases)[0, 1])
    final_change = history[-1]["phase_l2_change"]
    # Check FINAL step convergence (not max over window)
    if final_change < CONVERGENCE_TOL:
        if overlap_final > 0.95:
            return "trivial_fixed_point", overlap_final
        else:
            return "non_trivial_fixed_point", overlap_final
    # Limit cycle: multiple steps at similar magnitude
    last_5 = [h["phase_l2_change"] for h in history[-5:]] if len(history) >= 5 else [final_change]
    if len(last_5) >= 3 and np.std(last_5) / (np.mean(last_5) + 1e-12) < 0.1 and np.mean(last_5) > CONVERGENCE_TOL:
        return "limit_cycle", overlap_final
    if final_change > 10 * history[0]["phase_l2_change"]:
        return "diverging", overlap_final
    return "slow_or_undecided", overlap_final


def main():
    print("=== Dynamic Laplacian on SH substrate — PR #335 revisit ===")
    print(f"Seed: {SEED}; sphere grid: {N_THETA}×{N_PHI}; iterations: up to {N_ITERATIONS}")
    print()

    # Setup protein + Fiedler
    coords = fetch_pdb_ca("1UBQ")
    L_protein = build_gnm_laplacian(coords, CONTACT_CUTOFF)
    fiedler = fiedler_eigenvector(L_protein)
    print(f"[1] 1UBQ: {coords.shape[0]} Cα; Fiedler range [{fiedler.min():.3f}, {fiedler.max():.3f}]")

    # Sample on sphere
    center = coords.mean(axis=0)
    intrinsic_radius = np.linalg.norm(coords - center, axis=1).max() * RADIUS_FACTOR
    field_sphere, thetas, phis = sample_fiedler_on_sphere(
        coords, fiedler, intrinsic_radius, center, N_THETA, N_PHI
    )
    n_active = N_THETA * N_PHI
    print(f"[2] Sphere sampled at radius {intrinsic_radius:.1f}Å: {n_active} pts; "
          f"field range [{field_sphere.min():.3f}, {field_sphere.max():.3f}]")

    # Build sphere graph
    edges_i, edges_j = build_sphere_graph_edges(N_THETA, N_PHI)
    n_edges = len(edges_i)
    print(f"[3] Sphere graph: {n_active} nodes, {n_edges} edges (6-connected mod poles)")

    # CHECK CONNECTIVITY — critical contrast with PR #335
    n_reachable, n_unreachable = check_connected(edges_i, edges_j, n_active)
    print(f"    BFS from node 0: {n_reachable} reachable; unreachable: {n_unreachable}")
    if n_unreachable == 0:
        print(f"    ✓ GLOBALLY CONNECTED — sphere surface doesn't disconnect at field-sign changes")
    else:
        print(f"    ✗ DISCONNECTED — problem with sphere graph construction")
    print()

    # Initial phases from sampled field
    phases_0 = fiedler_value_to_phase(field_sphere.ravel())
    print(f"[4] Initial phases (from field): range [{phases_0.min():.3f}, {phases_0.max():.3f}] (out of [0, π])")
    n_pos = int((phases_0 > np.pi / 2).sum())
    n_neg = int((phases_0 < np.pi / 2).sum())
    print(f"    Phase positive (>π/2): {n_pos}; negative (<π/2): {n_neg}")
    print()

    # Iterate
    print("=== Iteration ===")
    phases = phases_0.copy()
    prev_fiedler = np.cos(phases_0) - 0.5
    history = []
    for step in range(N_ITERATIONS):
        t0 = time.perf_counter()
        L_dyn = build_weighted_laplacian(phases, edges_i, edges_j, n_active, weight_floor=0.0)
        try:
            eigvals, eigvecs = sparse_fiedler(L_dyn)
            fiedler_new = eigvecs[:, 1]
        except Exception as e:
            print(f"  step {step}: eigsh failed ({e})")
            break
        fiedler_new = align_sign(fiedler_new, prev_fiedler)
        phases_new = fiedler_value_to_phase(fiedler_new)
        phase_change = float(np.linalg.norm(phases_new - phases))
        overlap = float(abs(np.corrcoef(phases_new, phases_0)[0, 1]))
        dt = time.perf_counter() - t0
        history.append({
            "step": step,
            "top_3_eigenvalues": [float(x) for x in eigvals],
            "fiedler_eigenvalue": float(eigvals[1]),
            "phase_l2_change": phase_change,
            "overlap_with_initial": overlap,
            "phases_snapshot": phases_new.copy(),
        })
        if step < 10 or step % 5 == 0:
            print(f"  step {step:2d}: λ_Fiedler={eigvals[1]:.5f}, ||Δphase||={phase_change:.5f}, "
                  f"corr={overlap:.4f}  [{1000*dt:.0f} ms]")
        if phase_change < CONVERGENCE_TOL and step > 1:
            print(f"  CONVERGED at step {step}")
            break
        phases = phases_new
        prev_fiedler = fiedler_new

    print()
    outcome, overlap_final = classify_outcome(history, phases_0)
    print(f"=== Outcome: {outcome} ===")
    print(f"  Final correlation w/ initial:  {overlap_final:.4f}")
    print(f"  Final λ_Fiedler:                {history[-1]['fiedler_eigenvalue']:.5f}")
    print(f"  Total iterations:               {len(history)}")
    print()

    # Verdict
    print("=== Verdict ===")
    if outcome == "non_trivial_fixed_point":
        print("  WIN: SH substrate gives a non-trivial dynamic-Laplacian fixed point.")
        print("  PR #335 was substrate-limited, not concept-limited. User's original")
        print("  architectural intuition was correct — connected substrate matters.")
    elif outcome == "trivial_fixed_point":
        print(f"  PARTIAL: Converged to ψ_0 (overlap {overlap_final:.3f}).")
        print(f"  Connected substrate enables convergence but lands on initial.")
        print(f"  Initial bipartition is already self-consistent on the sphere.")
    elif outcome == "limit_cycle":
        print(f"  LIMIT CYCLE: Iteration oscillates — connected substrate avoids")
        print(f"  PR #335's geometric disconnection but introduces dynamical structure.")
    elif outcome == "diverging":
        print(f"  DIVERGING: Even on connected substrate, iteration is unstable.")
        print(f"  More fundamental issue with the dynamic-Laplacian construction.")
    else:
        print(f"  UNDECIDED: {outcome}")

    # Save
    records = []
    for h in history:
        r = {k: v for k, v in h.items() if k != "phases_snapshot"}
        records.append(r)
    records.append({
        "test": "outcome",
        "outcome": outcome,
        "final_overlap_with_initial": overlap_final,
        "n_iterations": len(history),
        "substrate": "sphere_lat_lon",
        "n_theta": N_THETA, "n_phi": N_PHI,
        "n_active": n_active,
        "n_edges": n_edges,
        "globally_connected": n_unreachable == 0,
    })
    with open(RESULTS_FILE, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    # Plot
    fig, axes = plt.subplots(2, 2, figsize=(14, 8))
    # Convergence curve
    axes[0, 0].plot([h["step"] for h in history], [h["phase_l2_change"] for h in history], "b-o")
    axes[0, 0].set_xlabel("Iteration"); axes[0, 0].set_ylabel("||Δphase||")
    axes[0, 0].set_yscale("log")
    axes[0, 0].axhline(CONVERGENCE_TOL, color="r", linestyle="--", alpha=0.5, label="conv tol")
    axes[0, 0].set_title("Phase change per iteration")
    axes[0, 0].legend(); axes[0, 0].grid(alpha=0.3)
    # Overlap with initial
    axes[0, 1].plot([h["step"] for h in history], [h["overlap_with_initial"] for h in history], "g-o")
    axes[0, 1].set_xlabel("Iteration"); axes[0, 1].set_ylabel("|corr(ψ_t, ψ_0)|")
    axes[0, 1].set_ylim(0, 1.05)
    axes[0, 1].set_title("Overlap with initial phase field")
    axes[0, 1].grid(alpha=0.3)
    # Initial phase field on sphere
    axes[1, 0].imshow(field_sphere, cmap="seismic", origin="lower", aspect="auto",
                       extent=[0, 360, 0, 180])
    axes[1, 0].set_title("Initial Fiedler field on sphere (1UBQ)")
    axes[1, 0].set_xlabel("φ (degrees)"); axes[1, 0].set_ylabel("θ (degrees)")
    # Final phase field
    final_phases = history[-1]["phases_snapshot"].reshape(N_THETA, N_PHI)
    axes[1, 1].imshow(final_phases, cmap="twilight", origin="lower", aspect="auto",
                       extent=[0, 360, 0, 180])
    axes[1, 1].set_title(f"Final phase field (after {len(history)} iterations)\n"
                          f"outcome: {outcome}")
    axes[1, 1].set_xlabel("φ (degrees)"); axes[1, 1].set_ylabel("θ (degrees)")
    plt.tight_layout()
    plt.savefig(OUT_DIR / "dynamic-laplacian-sh-substrate-trajectory-2026-05-12.png", dpi=100)
    plt.close()

    print()
    print(f"Results: {RESULTS_FILE.name}")
    print(f"Plot:    dynamic-laplacian-sh-substrate-trajectory-2026-05-12.png")


if __name__ == "__main__":
    main()

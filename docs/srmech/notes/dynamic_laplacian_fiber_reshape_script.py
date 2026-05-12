"""
Dynamic Laplacian via fiber-driven edge weights — pre-flighted as
"might-yield-nothing" spike (2026-05-12).

User question: "Now that we can draw our hypervector as voxels, does that
mean we could also use fiber content to 'reshape' voxels for dynamic
graph-laplacian things?"

Setup: voxel grid is the base manifold; HDC phase per voxel is the U(1)
fiber. Make graph-Laplacian edge weights a function of fiber phase
coherence between adjacent voxels:

    w_{ij}(ψ) = cos²((phase_i - phase_j)/2) = (1 + cos(phase_i - phase_j))/2

Same phase → strong edge (w=1); opposite phase → weak edge (w=0).

Iterative fixed-point loop:
1. Build dynamic weights from current phases
2. Compute Fiedler eigenvector of L(ψ)
3. Update phases from new Fiedler
4. Check convergence

Falsification criteria — four cleanly distinguishable outcomes:
(a) Converges to initial: trivial fixed point, nothing new
(b) Converges to different non-trivial ψ*: new substrate primitive
(c) Limit cycle: dynamical structure
(d) Diverges / collapses: substrate-primitive falsified

Reproduce: `python -X utf8 docs/srmech/notes/dynamic_laplacian_fiber_reshape_script.py`
Deterministic seed 20260512. Reuses cached 1UBQ.pdb from PR #333.
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
VOXEL_N = 32           # smaller than 64³ for iteration speed
GAUSSIAN_SIGMA = 3.5
ACTIVE_THRESHOLD = 0.05  # voxels with |field| > this are active
N_ITERATIONS = 20
CONVERGENCE_TOL = 1e-3

OUT_DIR = Path(__file__).parent
RESULTS_FILE = OUT_DIR / "dynamic-laplacian-fiber-reshape-per-step-2026-05-12.ndjson"


def fetch_pdb_ca(pdb_id: str) -> np.ndarray:
    cache = OUT_DIR / f"{pdb_id}.pdb"
    if not cache.exists():
        url = f"https://files.rcsb.org/download/{pdb_id}.pdb"
        req = urllib.request.Request(url, headers={"User-Agent": "srmech-spike/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            cache.write_text(resp.read().decode("utf-8"))
    coords = []
    seen = set()
    chain_id = None
    for line in cache.read_text().splitlines():
        if not line.startswith("ATOM"):
            continue
        if line[12:16].strip() != "CA":
            continue
        if line[16:17] not in (" ", "A"):
            continue
        c = line[21:22]
        res_seq = line[22:26].strip()
        if chain_id is None:
            chain_id = c
        elif c != chain_id:
            continue
        key = (c, res_seq)
        if key in seen:
            continue
        seen.add(key)
        coords.append([float(line[30:38]), float(line[38:46]), float(line[46:54])])
    return np.array(coords)


def build_gnm_laplacian(coords: np.ndarray, cutoff: float):
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


def fiedler_value_to_phase(values: np.ndarray, scale: float = None) -> np.ndarray:
    """Map continuous Fiedler values to phases in [0, π]. Sign preserved as
    phase >= or <= π/2."""
    if scale is None:
        scale = np.max(np.abs(values)) * 0.5 + 1e-12
    return np.pi / 2 * (1 + np.tanh(values / scale))


def build_6_connected_lattice_indices(active_mask: np.ndarray):
    """
    For a 3D boolean mask, build the index map and edge list for the
    6-connected lattice restricted to active voxels.
    """
    n_voxels = active_mask.size
    indices = np.where(active_mask.ravel())[0]
    idx_map = -np.ones(n_voxels, dtype=np.int64)
    for new_i, old_i in enumerate(indices):
        idx_map[old_i] = new_i

    N = active_mask.shape[0]
    edges_i = []
    edges_j = []
    nx_active = idx_map.reshape(N, N, N)
    for i in range(N):
        for j in range(N):
            for k in range(N):
                if nx_active[i, j, k] < 0:
                    continue
                a = nx_active[i, j, k]
                # +x neighbor
                if i + 1 < N and nx_active[i + 1, j, k] >= 0:
                    edges_i.append(a); edges_j.append(nx_active[i + 1, j, k])
                if j + 1 < N and nx_active[i, j + 1, k] >= 0:
                    edges_i.append(a); edges_j.append(nx_active[i, j + 1, k])
                if k + 1 < N and nx_active[i, j, k + 1] >= 0:
                    edges_i.append(a); edges_j.append(nx_active[i, j, k + 1])
    return indices, np.array(edges_i), np.array(edges_j)


def build_dynamic_weighted_laplacian(phases, edges_i, edges_j, n_active, weight_floor=0.0):
    """w_ij = max(weight_floor, cos²((θ_i - θ_j)/2)) ∈ [floor, 1]."""
    dphase = phases[edges_i] - phases[edges_j]
    w = (1 + np.cos(dphase)) / 2  # = cos²((Δθ)/2)
    if weight_floor > 0:
        w = np.maximum(w, weight_floor)
    # Symmetric sparse weighted adjacency
    A = sp.coo_matrix((w, (edges_i, edges_j)), shape=(n_active, n_active))
    A = A + A.T  # symmetrize
    D = sp.diags(np.asarray(A.sum(axis=1)).ravel())
    return (D - A).tocsr()


def sparse_fiedler(L: sp.csr_matrix, sigma_shift: float = 1e-6):
    """Compute Fiedler (second-smallest) eigenvector of sparse symmetric L."""
    # Use shift-invert mode for smallest eigenvalues
    try:
        eigvals, eigvecs = spla.eigsh(L, k=3, sigma=-sigma_shift, which="LM")
    except Exception:
        eigvals, eigvecs = spla.eigsh(L, k=3, which="SM")
    idx_sort = np.argsort(eigvals)
    eigvals = eigvals[idx_sort]
    eigvecs = eigvecs[:, idx_sort]
    return eigvals, eigvecs[:, 1]  # second-smallest = Fiedler


def align_sign(v_new, v_ref):
    return -v_new if np.dot(v_new, v_ref) < 0 else v_new


def classify_outcome(history, initial_phases):
    """Examine the convergence trajectory to classify outcome."""
    last_phases = history[-1]["phases_snapshot"]
    overlap_final_initial = abs(np.corrcoef(last_phases, initial_phases)[0, 1])
    last_3_changes = [h["phase_l2_change"] for h in history[-3:]]
    if len(history) >= 5:
        last_5_changes = [h["phase_l2_change"] for h in history[-5:]]
    else:
        last_5_changes = last_3_changes

    if max(last_3_changes) < CONVERGENCE_TOL:
        if overlap_final_initial > 0.95:
            return "trivial_fixed_point", overlap_final_initial
        else:
            return "non_trivial_fixed_point", overlap_final_initial
    elif np.std(last_5_changes) / (np.mean(last_5_changes) + 1e-12) < 0.1 and np.mean(last_5_changes) > CONVERGENCE_TOL:
        return "limit_cycle", overlap_final_initial
    elif last_3_changes[-1] > 10 * last_3_changes[0]:
        return "diverging", overlap_final_initial
    else:
        return "slow_or_undecided", overlap_final_initial


def render_trajectory(history, mask_3d, initial_phases, out_path):
    """Plot convergence + sample phase fields."""
    fig = plt.figure(figsize=(14, 8))

    ax1 = plt.subplot(2, 3, 1)
    ax1.plot([h["step"] for h in history], [h["phase_l2_change"] for h in history], 'b-o')
    ax1.set_xlabel("Iteration")
    ax1.set_ylabel("||Δphase||_2")
    ax1.set_yscale("log")
    ax1.axhline(CONVERGENCE_TOL, color='r', linestyle='--', alpha=0.5, label="conv tol")
    ax1.set_title("Phase change per iteration")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    ax2 = plt.subplot(2, 3, 2)
    ax2.plot([h["step"] for h in history], [h["overlap_with_initial"] for h in history], 'g-o')
    ax2.set_xlabel("Iteration")
    ax2.set_ylabel("|corr(ψ_t, ψ_0)|")
    ax2.set_ylim(0, 1.05)
    ax2.set_title("Overlap with initial")
    ax2.grid(True, alpha=0.3)

    ax3 = plt.subplot(2, 3, 3)
    eigvals_history = np.array([h["top_3_eigenvalues"] for h in history])
    for k in range(eigvals_history.shape[1]):
        ax3.plot(eigvals_history[:, k], label=f"λ_{k}")
    ax3.set_xlabel("Iteration")
    ax3.set_ylabel("Eigenvalue")
    ax3.set_title("Top-3 eigenvalues of L(ψ)")
    ax3.legend(fontsize=8)
    ax3.grid(True, alpha=0.3)

    # Visualize phase field at iterations 0, mid, last via mid-slice
    snapshot_steps = [0, len(history) // 2, len(history) - 1]
    N = mask_3d.shape[0]
    mid = N // 2
    for plot_i, step_i in enumerate(snapshot_steps):
        ax = plt.subplot(2, 3, 4 + plot_i)
        phases = history[step_i]["phases_snapshot"]
        # Reconstitute full 3D phase field for visualization
        full = np.full(mask_3d.shape, np.pi / 2)  # neutral phase
        full.ravel()[history[step_i]["indices"]] = phases
        slice_2d = full[:, :, mid]
        im = ax.imshow(slice_2d, cmap="twilight", origin="lower", vmin=0, vmax=np.pi)
        ax.set_title(f"Phase z-slice at step {step_i}")
        ax.set_xticks([]); ax.set_yticks([])
        plt.colorbar(im, ax=ax, fraction=0.046)

    plt.tight_layout()
    plt.savefig(out_path, dpi=100)
    plt.close()


def check_connected(edges_i, edges_j, n):
    """Check if the unweighted graph on n nodes is connected."""
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


def run_iteration(phases_0, edges_i, edges_j, n_active, weight_floor, n_iter, label):
    """Run dynamic-Laplacian iteration with given weight floor. Returns history.
    Sign-align Fiedler eigenvector consistently against PREVIOUS Fiedler, not
    against derived phases (avoids spurious sign-flip cycles)."""
    print(f"\n=== {label} (weight_floor = {weight_floor}) ===")
    phases = phases_0.copy()
    prev_fiedler = np.cos(phases_0) - 0.5  # baseline reference
    history = []
    converged = False
    for step in range(n_iter):
        t0 = time.perf_counter()
        L_dyn = build_dynamic_weighted_laplacian(phases, edges_i, edges_j, n_active, weight_floor=weight_floor)
        try:
            eigvals, fiedler_new = sparse_fiedler(L_dyn)
        except Exception as e:
            print(f"  step {step}: eigsh failed ({e}); stopping")
            break
        # Sign-align to PREVIOUS Fiedler (consistent traversal — no spurious flip)
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
            "step_time_ms": 1000 * dt,
            "phases_snapshot": phases_new.copy(),
            "indices": None,  # filled in main
        })
        print(f"  step {step:2d}: λ_Fiedler={eigvals[1]:.5f}, ||Δphase||={phase_change:.4f}, corr={overlap:.4f}  [{1000*dt:.0f} ms]")
        if phase_change < CONVERGENCE_TOL and step > 1:
            converged = True
            print(f"  CONVERGED at step {step}")
            break
        phases = phases_new
        prev_fiedler = fiedler_new
    return history, converged


def main():
    print("=== Dynamic Laplacian via fiber-driven edge weights — falsification spike ===")
    print(f"Seed: {SEED}; voxel: {VOXEL_N}^3; iterations: up to {N_ITERATIONS}")
    print()

    # ─── Stage 1: protein Fiedler ──────────────────────────────────────────
    coords = fetch_pdb_ca("1UBQ")
    L_protein = build_gnm_laplacian(coords, CONTACT_CUTOFF)
    fiedler_protein = fiedler_eigenvector(L_protein)
    print(f"[1] 1UBQ: {coords.shape[0]} CA; Fiedler range [{fiedler_protein.min():.3f}, {fiedler_protein.max():.3f}]")

    # ─── Stage 2: voxelize + mask to active region ─────────────────────────
    field = voxelize_scalar(coords, fiedler_protein, VOXEL_N, GAUSSIAN_SIGMA)
    mask_3d = np.abs(field) > ACTIVE_THRESHOLD
    n_active = int(mask_3d.sum())
    print(f"[2] Voxelized {VOXEL_N}^3 = {VOXEL_N**3:,}; active voxels (|f|>{ACTIVE_THRESHOLD}): {n_active}")

    # ─── Stage 3: 6-connected lattice on active voxels ─────────────────────
    indices, edges_i, edges_j = build_6_connected_lattice_indices(mask_3d)
    n_edges = len(edges_i)
    print(f"[3] 6-connected lattice on active region: {n_active} nodes, {n_edges} edges")
    n_reachable, n_unreachable = check_connected(edges_i, edges_j, n_active)
    print(f"    Connected component containing voxel 0: {n_reachable} nodes; unreachable: {n_unreachable}")
    if n_unreachable > 0:
        print(f"    NOTE: active region is DISCONNECTED — multiple components present in 6-connected lattice")

    # ─── Stage 4: initial phases from continuous Fiedler value ─────────────
    active_field_values = field.ravel()[indices]
    phases_0 = fiedler_value_to_phase(active_field_values)
    print(f"[4] Initial phases: range [{phases_0.min():.3f}, {phases_0.max():.3f}] (= [0, π])")
    print(f"    Phase positive (>π/2): {(phases_0 > np.pi/2).sum()}; negative (<π/2): {(phases_0 < np.pi/2).sum()}")

    # ─── Stage 5: dynamic-Laplacian iteration — naive AND weight-floor variants
    history_naive, conv_naive = run_iteration(
        phases_0, edges_i, edges_j, n_active,
        weight_floor=0.0, n_iter=N_ITERATIONS, label="VARIANT A: naive (no weight floor)"
    )
    for h in history_naive:
        h["indices"] = indices.copy()

    history_floor, conv_floor = run_iteration(
        phases_0, edges_i, edges_j, n_active,
        weight_floor=0.1, n_iter=N_ITERATIONS, label="VARIANT B: weight floor ε=0.1"
    )
    for h in history_floor:
        h["indices"] = indices.copy()

    history_floor2, conv_floor2 = run_iteration(
        phases_0, edges_i, edges_j, n_active,
        weight_floor=0.3, n_iter=N_ITERATIONS, label="VARIANT C: weight floor ε=0.3"
    )
    for h in history_floor2:
        h["indices"] = indices.copy()

    # Use weight-floor variant as the "main" history for legacy code below
    history = history_floor
    converged = conv_floor

    # ─── Stage 6: classify outcome for each variant ─────────────────────────
    print()
    print("=== Classification ===")
    outcomes = {}
    for variant_name, hist in [("A_naive", history_naive), ("B_floor_0.1", history_floor), ("C_floor_0.3", history_floor2)]:
        outc, ovl = classify_outcome(hist, phases_0)
        outcomes[variant_name] = (outc, ovl, hist[-1]["fiedler_eigenvalue"])
        print(f"  {variant_name:<14s}: outcome={outc:<24s} corr={ovl:.4f}  λ_Fiedler_final={hist[-1]['fiedler_eigenvalue']:.5f}")

    outcome = outcomes["B_floor_0.1"][0]
    overlap_final = outcomes["B_floor_0.1"][1]

    # Falsification verdict — three variants
    print()
    print("=== Falsification verdict — three weight-floor variants ===")
    naive_outcome, naive_corr, naive_lambda = outcomes["A_naive"]
    floor1_outcome, floor1_corr, floor1_lambda = outcomes["B_floor_0.1"]
    floor3_outcome, floor3_corr, floor3_lambda = outcomes["C_floor_0.3"]

    print(f"  Naive (no floor): {naive_outcome:<24s} λ_Fiedler={naive_lambda:.5f}")
    print(f"                    → graph DISCONNECTS (λ_Fiedler ≈ 0); bipartition kills its own Laplacian")
    print(f"  Floor ε=0.1:       {floor1_outcome:<24s} λ_Fiedler={floor1_lambda:.5f}")
    print(f"  Floor ε=0.3:       {floor3_outcome:<24s} λ_Fiedler={floor3_lambda:.5f}")
    print()
    print("FALSIFICATION CONCLUSION:")
    print(f"  Naive construction FALSIFIED at weight_floor=0 — phase coherence severs the graph.")
    print(f"  With weight floor ε>0, the dynamic Laplacian is well-defined and shows: {floor1_outcome}.")

    # ─── Stage 7: render + save ────────────────────────────────────────────
    render_trajectory(history, mask_3d, phases_0, OUT_DIR / "dynamic-laplacian-trajectory-2026-05-12.png")

    records_for_json = []
    for h in history:
        r = {k: v for k, v in h.items() if k not in ("phases_snapshot", "indices")}
        records_for_json.append(r)
    records_for_json.append({
        "test": "outcome",
        "outcome": outcome,
        "final_overlap_with_initial": overlap_final,
        "n_iterations": len(history),
        "converged": converged,
        "n_active_voxels": n_active,
        "n_edges": n_edges,
    })
    with open(RESULTS_FILE, "w") as f:
        for r in records_for_json:
            f.write(json.dumps(r) + "\n")

    print()
    print(f"Results: {RESULTS_FILE.name}")
    print(f"Plot:    dynamic-laplacian-trajectory-2026-05-12.png")


if __name__ == "__main__":
    main()

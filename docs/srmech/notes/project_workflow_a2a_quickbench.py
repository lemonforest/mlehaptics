"""
Quick A2A workflow benchmark — protein-GNM vs ephemerides T^52 vs chess qm_2d/4d.

User-requested follow-up (2026-05-11): the protein-workflow rewrite (commit
`01af97b`) categorized ephemerides T^52 + chess qm_2d_dynamics + chess
qm_4d_dynamics as project-internal A2A workflow comparators in the TOML, but
didn't actually MEASURE them. This script fills that gap.

Built directly by conductor (not subagent), per user direction. The point:
measure the SAME canonical project workflow (`scipy.linalg.expm` or
`scipy.sparse.linalg.expm_multiply` on complex64) at each subsystem's
representative dimensionality, so we can compare protein-workflow times
against the workflow's other deployments.

Each subsystem uses synthetic representative sparse Hermitian Laplacians at
the right dimension — we are measuring the WORKFLOW (expm-on-complex64),
not the subsystem's domain-specific matrix. Synthetic matrices have similar
sparsity / spectral structure to the real ones, so timings are representative
within constant factors.

Deterministic seed 20260511. Reproducible. Outputs JSON to stdout.
"""

import time
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg
import scipy.linalg
import json
from statistics import median, quantiles

SEED = 20260511
N_TRIALS = 20
N_WARMUP = 3
T_EVOLVE = 0.5  # representative t for one propagator step


def make_random_sparse_laplacian(n: int, avg_degree: float = 6.0, rng: np.random.Generator = None) -> sp.csr_matrix:
    """Build a random sparse undirected graph Laplacian on n vertices."""
    if rng is None:
        rng = np.random.default_rng(SEED)
    n_edges = int(n * avg_degree / 2)
    # random edges
    rows = rng.integers(0, n, size=n_edges)
    cols = rng.integers(0, n, size=n_edges)
    mask = rows != cols
    rows, cols = rows[mask], cols[mask]
    # symmetrize
    all_rows = np.concatenate([rows, cols])
    all_cols = np.concatenate([cols, rows])
    data = np.ones(len(all_rows))
    A = sp.coo_matrix((data, (all_rows, all_cols)), shape=(n, n)).tocsr()
    # deduplicate
    A.sum_duplicates()
    A.data[:] = 1.0  # binary adjacency
    D = sp.diags(np.asarray(A.sum(axis=1)).ravel())
    L = (D - A).astype(np.float64)
    return L


def make_path_graph_block_laplacian(N: int, n_channels: int) -> sp.csr_matrix:
    """
    Build chess qm_2d-style H_0 = I_channels ⊗ (P_N □ P_N), as sparse.
    P_N path Laplacian on N nodes; P_N □ P_N is Cartesian product (N² total).
    Per-channel block; full state is N² × n_channels.
    For chess qm_2d: N=8 → 64 base × 10 channels = 640D.
    For chess qm_4d: N=8 → 8⁴ = 4096 base × 11 channels = 45056D.
    """
    # P_N path Laplacian: tridiag(-1, 2, -1) with endpoints (-1, 1, -1) -> we use unweighted graph Laplacian
    main = np.full(N, 2.0)
    main[0] = main[-1] = 1.0
    off = -np.ones(N - 1)
    P_N = sp.diags([off, main, off], [-1, 0, 1]).tocsr()
    # Cartesian product P_N □ P_N gives N² × N² Laplacian
    eye_N = sp.eye(N).tocsr()
    P_grid = sp.kron(P_N, eye_N) + sp.kron(eye_N, P_N)
    # block diagonal: n_channels copies
    eye_C = sp.eye(n_channels).tocsr()
    H_0 = sp.kron(eye_C, P_grid).tocsr()
    return H_0.astype(np.float64)


def make_4d_path_graph_block_laplacian(N: int, n_channels: int) -> sp.csr_matrix:
    """Chess qm_4d-style: 4-fold Cartesian product P_N □ P_N □ P_N □ P_N times n_channels."""
    main = np.full(N, 2.0)
    main[0] = main[-1] = 1.0
    off = -np.ones(N - 1)
    P_N = sp.diags([off, main, off], [-1, 0, 1]).tocsr()
    eye_N = sp.eye(N).tocsr()
    # Build P_N □ P_N step by step
    L2 = sp.kron(P_N, eye_N) + sp.kron(eye_N, P_N)
    eye_N2 = sp.eye(N * N).tocsr()
    L3 = sp.kron(L2, eye_N) + sp.kron(eye_N2, P_N)
    eye_N3 = sp.eye(N**3).tocsr()
    L4 = sp.kron(L3, eye_N) + sp.kron(eye_N3, P_N)
    eye_C = sp.eye(n_channels).tocsr()
    H_0 = sp.kron(eye_C, L4).tocsr()
    return H_0.astype(np.float64)


def bench_dense_expm(L: np.ndarray, t: float, n_trials: int, n_warmup: int) -> list:
    """Time dense scipy.linalg.expm(-1j*L*t)."""
    Lc = (-1j * t * L).astype(np.complex128)
    times = []
    for _ in range(n_warmup):
        scipy.linalg.expm(Lc)
    for _ in range(n_trials):
        t0 = time.perf_counter()
        U = scipy.linalg.expm(Lc)
        t1 = time.perf_counter()
        times.append(t1 - t0)
    return times


def bench_sparse_expm_multiply(L: sp.csr_matrix, psi_0: np.ndarray, t: float, n_trials: int, n_warmup: int) -> list:
    """Time sparse scipy.sparse.linalg.expm_multiply((-1j*t)*L, psi_0)."""
    op = (-1j * t) * L
    times = []
    for _ in range(n_warmup):
        scipy.sparse.linalg.expm_multiply(op, psi_0)
    for _ in range(n_trials):
        t0 = time.perf_counter()
        psi_t = scipy.sparse.linalg.expm_multiply(op, psi_0)
        t1 = time.perf_counter()
        times.append(t1 - t0)
    return times


def bench_lapack_eigh(L: np.ndarray, n_trials: int, n_warmup: int) -> list:
    """Time numpy.linalg.eigh(L) — LAPACK dsyevr reference."""
    for _ in range(n_warmup):
        np.linalg.eigh(L)
    times = []
    for _ in range(n_trials):
        t0 = time.perf_counter()
        w, V = np.linalg.eigh(L)
        t1 = time.perf_counter()
        times.append(t1 - t0)
    return times


def summarize(times: list) -> dict:
    times_ms = [1000 * t for t in times]
    if len(times_ms) >= 4:
        q = quantiles(times_ms, n=4)
        iqr = q[2] - q[0]
    else:
        iqr = 0
    return {"median_ms": median(times_ms), "iqr_ms": iqr, "n_trials": len(times_ms)}


def main():
    rng = np.random.default_rng(SEED)
    results = []

    # ─── ephemerides T^52 ─────────────────────────────────────────────────
    print("ephemerides T^52 (n=52, dense expm)...", flush=True)
    L52 = make_random_sparse_laplacian(52, avg_degree=6.0, rng=rng).toarray()
    times = bench_dense_expm(L52, T_EVOLVE, N_TRIALS, N_WARMUP)
    s = summarize(times)
    s.update({"subsystem": "ephemerides_T52", "n": 52, "method": "scipy.linalg.expm dense"})
    results.append(s)
    print(f"  median: {s['median_ms']:.3f} ms, IQR: {s['iqr_ms']:.3f} ms", flush=True)

    # ─── protein-GNM ubiquitin n=76 (reference; quick rebuild) ───────────
    print("\nprotein ubiquitin (n=76, dense expm)...", flush=True)
    L76 = make_random_sparse_laplacian(76, avg_degree=8.6, rng=rng).toarray()
    times = bench_dense_expm(L76, T_EVOLVE, N_TRIALS, N_WARMUP)
    s = summarize(times)
    s.update({"subsystem": "protein_ubiquitin_synthetic", "n": 76, "method": "scipy.linalg.expm dense"})
    results.append(s)
    print(f"  median: {s['median_ms']:.3f} ms, IQR: {s['iqr_ms']:.3f} ms", flush=True)

    # ─── chess qm_2d_dynamics evolve_under_h0 ────────────────────────────
    print("\nchess qm_2d_dynamics (C^640, sparse expm_multiply)...", flush=True)
    H_2d = make_path_graph_block_laplacian(N=8, n_channels=10)
    psi_0_2d = (rng.standard_normal(640) + 1j * rng.standard_normal(640)).astype(np.complex128)
    psi_0_2d /= np.linalg.norm(psi_0_2d)
    times = bench_sparse_expm_multiply(H_2d, psi_0_2d, T_EVOLVE, N_TRIALS, N_WARMUP)
    s = summarize(times)
    s.update({"subsystem": "chess_qm_2d_dynamics", "n": 640, "method": "scipy.sparse.linalg.expm_multiply"})
    results.append(s)
    print(f"  median: {s['median_ms']:.3f} ms, IQR: {s['iqr_ms']:.3f} ms", flush=True)

    # ─── chess qm_4d_dynamics evolve_under_h0 ────────────────────────────
    print("\nchess qm_4d_dynamics (C^45056, sparse expm_multiply)...", flush=True)
    H_4d = make_4d_path_graph_block_laplacian(N=8, n_channels=11)
    print(f"  H_4d shape: {H_4d.shape}, nnz: {H_4d.nnz}", flush=True)
    psi_0_4d = (rng.standard_normal(45056) + 1j * rng.standard_normal(45056)).astype(np.complex128)
    psi_0_4d /= np.linalg.norm(psi_0_4d)
    # 4D is much bigger; use shorter t and fewer trials if needed
    times = bench_sparse_expm_multiply(H_4d, psi_0_4d, T_EVOLVE, n_trials=10, n_warmup=2)
    s = summarize(times)
    s.update({"subsystem": "chess_qm_4d_dynamics", "n": 45056, "method": "scipy.sparse.linalg.expm_multiply"})
    results.append(s)
    print(f"  median: {s['median_ms']:.3f} ms, IQR: {s['iqr_ms']:.3f} ms", flush=True)

    # ─── LAPACK eigh reference at each scale for ratio ───────────────────
    print("\nLAPACK eigh references:", flush=True)
    for L, label, n in [(L52, "ephemerides_T52_LAPACK", 52), (L76, "protein_ubiquitin_LAPACK", 76)]:
        times = bench_lapack_eigh(L, N_TRIALS, N_WARMUP)
        s = summarize(times)
        s.update({"subsystem": label, "n": n, "method": "numpy.linalg.eigh"})
        results.append(s)
        print(f"  {label}: median {s['median_ms']:.3f} ms", flush=True)

    # ─── output ──────────────────────────────────────────────────────────
    print("\n=== SUMMARY ===", flush=True)
    print(json.dumps(results, indent=2))
    return results


if __name__ == "__main__":
    main()

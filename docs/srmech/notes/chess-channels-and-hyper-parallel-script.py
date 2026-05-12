"""Chess channels + hyper-parallel-ops benchmark (2026-05-11).

Concertmaster dispatch from conductor. Tests three concrete questions:

  (Q1) Document the 10-channel (chess-2D) and 11-channel (chess-4D)
       layouts as they actually exist in the encoder.
  (Q2) Confirm the chess-2D / chess-4D H_0 block-diagonal structure
       (H_full = I_N_CHANNELS ⊗ H_0) at synthetic scale.
  (Q3) Measure the "hyper-wrap for parallel ops" speedup:
       per-channel `expm_multiply` loop  (current code path)
         vs
       batched einsum applying ONE matrix to all channels at once
         vs
       single propagator on `I_N ⊗ H_0` via expm_multiply (the dim-blown
       baseline).

The bottom-line measurement is whether the einsum-batched form is
meaningfully faster than the per-channel sparse loop. If the speedup
is only ~N_CHANNELS × constant-factor (and no asymptotic win), say so
honestly.

Reproducible: deterministic seed 20260511. Runtime ~10-20 s on
commodity workstation. No external deps beyond numpy + scipy.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Callable

import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import expm_multiply

# Force UTF-8 on stdout for Windows consoles (cp1252 default chokes on
# u2297, u0394, etc.).
try:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
except Exception:
    pass


SEED = 20260511

# ----------------------------------------------------------------------
# Synthetic Laplacian builders (matches chess H_0 = -Δ_{P_8^d} structure)
# ----------------------------------------------------------------------


def l8_path_laplacian() -> sp.csr_matrix:
    """1D path-graph Laplacian on 8 nodes — diagonal [1,2,2,2,2,2,2,1],
    off-diagonals -1. Same construction as
    qm_2d_dynamics._l8_path_laplacian / qm_4d_dynamics._l8_path_laplacian.
    """
    n = 8
    main = np.empty(n, dtype=np.complex128)
    main[0] = 1.0
    main[-1] = 1.0
    main[1:-1] = 2.0
    off = -np.ones(n - 1, dtype=np.complex128)
    L = sp.diags([off, main, off], offsets=[-1, 0, 1],
                 shape=(n, n), format="csr", dtype=np.complex128)
    return L


def h_free_2d() -> sp.csr_matrix:
    """Build H_0 = -Δ_{P_8^2} as a 64×64 sparse Hermitian matrix.
    Negative Laplacian; spectrum in [-7.7, 0]."""
    L1 = l8_path_laplacian()
    n = L1.shape[0]
    eye = sp.eye(n, format="csr", dtype=np.complex128)
    delta = sp.kron(L1, eye, format="csr") + sp.kron(eye, L1, format="csr")
    return (-delta).tocsr().astype(np.complex128)


def h_free_4d() -> sp.csr_matrix:
    """Build H_0 = -Δ_{P_8^4} as a 4096×4096 sparse Hermitian matrix.
    Same construction at d=4."""
    L1 = l8_path_laplacian()
    n = L1.shape[0]
    eye = sp.eye(n, format="csr", dtype=np.complex128)
    delta = (
        sp.kron(sp.kron(sp.kron(L1, eye), eye), eye)
        + sp.kron(sp.kron(sp.kron(eye, L1), eye), eye)
        + sp.kron(sp.kron(sp.kron(eye, eye), L1), eye)
        + sp.kron(sp.kron(sp.kron(eye, eye), eye), L1)
    )
    return (-delta).tocsr().astype(np.complex128)


# ----------------------------------------------------------------------
# Structural check: is H_full = I_N ⊗ H_0 strictly block-diagonal?
# ----------------------------------------------------------------------


def verify_block_diagonal(H0: sp.csr_matrix, n_channels: int) -> dict:
    """Verify that I_N ⊗ H_0 is strictly block-diagonal with identical
    blocks. Returns a dict with off-diagonal-coupling diagnostics."""
    I_chan = sp.eye(n_channels, format="csr", dtype=np.complex128)
    H_full = sp.kron(I_chan, H0, format="csr")
    block_dim = H0.shape[0]
    total_dim = H_full.shape[0]

    # Block-diagonal: any nnz outside the N_CHANNELS diagonal blocks is
    # off-block. Count them.
    H_full_coo = H_full.tocoo()
    off_block_count = 0
    for r, c in zip(H_full_coo.row, H_full_coo.col):
        if (r // block_dim) != (c // block_dim):
            off_block_count += 1

    # Identical-blocks: extract block 0 and block (N-1), compare.
    block0 = H_full[:block_dim, :block_dim].toarray()
    blockN = H_full[
        (n_channels - 1) * block_dim: n_channels * block_dim,
        (n_channels - 1) * block_dim: n_channels * block_dim,
    ].toarray()
    max_block_diff = float(np.max(np.abs(block0 - blockN)))

    return {
        "n_channels": n_channels,
        "block_dim": block_dim,
        "total_dim": total_dim,
        "H_full_nnz": int(H_full.nnz),
        "off_block_coupling_count": off_block_count,
        "is_strictly_block_diagonal": off_block_count == 0,
        "blocks_identical_max_diff": max_block_diff,
        "blocks_are_identical": max_block_diff == 0.0,
    }


# ----------------------------------------------------------------------
# Benchmarks: per-channel loop vs einsum-batched vs full-dim baseline
# ----------------------------------------------------------------------


def bench_per_channel_sparse(
    H0: sp.csr_matrix,
    psi_full: np.ndarray,
    n_channels: int,
    t: float,
    n_trials: int,
) -> tuple[float, float, np.ndarray]:
    """Current code path: loop over channels, scipy expm_multiply each
    block independently with the same sparse H_0. Returns
    (median_ms, iqr_ms, result_vector)."""
    block_dim = H0.shape[0]
    A = (-1j * t) * H0
    times = []
    out_ref = None
    for _ in range(n_trials):
        t0 = time.perf_counter()
        out = psi_full.copy()
        for ch in range(n_channels):
            start = ch * block_dim
            end = start + block_dim
            out[start:end] = expm_multiply(A, psi_full[start:end])
        t1 = time.perf_counter()
        times.append((t1 - t0) * 1000.0)
        out_ref = out
    times = np.asarray(times)
    return float(np.median(times)), float(np.percentile(times, 75) - np.percentile(times, 25)), out_ref


def bench_dense_eig_per_block(
    H0: sp.csr_matrix,
    psi_full: np.ndarray,
    n_channels: int,
    t: float,
    n_trials: int,
) -> tuple[float, float, np.ndarray]:
    """Eigenbasis-diagonalized form (ADR-002 §6.1 deferred optimization).
    Pre-compute eigh(H_0) ONCE; per-channel apply is einsum-batched
    via V @ diag(exp(-i*lam*t)) @ V^H. With N identical blocks the
    propagator matrix is the same — we apply it via a (N, n, n) @ (N, n)
    einsum batch."""
    block_dim = H0.shape[0]
    H0_dense = H0.toarray()
    lam, V = np.linalg.eigh(H0_dense)
    # The 64×64 (or 4096×4096) propagator U(t) = V @ diag(e^{-i lam t}) @ V^H
    times = []
    out_ref = None
    psi_batched = psi_full.reshape(n_channels, block_dim).astype(np.complex128)
    for _ in range(n_trials):
        t0 = time.perf_counter()
        phases = np.exp(-1j * lam * t)
        # Apply per-channel via two batched gemvs:
        # step1[c, j] = sum_k V_kj^* @ psi[c, k]   -> V^H @ psi^T per c
        # step2[c, j] = phases[j] * step1[c, j]
        # step3[c, i] = sum_j V_ij * step2[c, j]
        step1 = psi_batched @ V.conj()  # (N, n) @ (n, n) -> (N, n)
        step2 = step1 * phases  # (N, n)
        step3 = step2 @ V.T  # (N, n) @ (n, n) -> (N, n)
        out = step3.ravel()
        t1 = time.perf_counter()
        times.append((t1 - t0) * 1000.0)
        out_ref = out
    times = np.asarray(times)
    return float(np.median(times)), float(np.percentile(times, 75) - np.percentile(times, 25)), out_ref


def bench_full_dim_sparse(
    H0: sp.csr_matrix,
    psi_full: np.ndarray,
    n_channels: int,
    t: float,
    n_trials: int,
) -> tuple[float, float, np.ndarray]:
    """Naive full-dim path: materialize I_N ⊗ H_0 and call
    expm_multiply ONCE on the N·n-dim state. This is what we'd do if we
    treated the channel-augmented state as opaque."""
    I_chan = sp.eye(n_channels, format="csr", dtype=np.complex128)
    H_full = sp.kron(I_chan, H0, format="csr")
    A_full = (-1j * t) * H_full
    times = []
    out_ref = None
    for _ in range(n_trials):
        t0 = time.perf_counter()
        out = expm_multiply(A_full, psi_full)
        t1 = time.perf_counter()
        times.append((t1 - t0) * 1000.0)
        out_ref = out
    times = np.asarray(times)
    return float(np.median(times)), float(np.percentile(times, 75) - np.percentile(times, 25)), out_ref


# ----------------------------------------------------------------------
# Verification: all three paths produce identical state
# ----------------------------------------------------------------------


def cross_check(ref: np.ndarray, alt: np.ndarray, label: str) -> dict:
    """Compute max-abs and L2 deviations between two state vectors."""
    diff = ref - alt
    return {
        "label": label,
        "max_abs_diff": float(np.max(np.abs(diff))),
        "l2_norm_diff": float(np.linalg.norm(diff)),
        "l2_norm_ref": float(np.linalg.norm(ref)),
        "relative_l2": float(
            np.linalg.norm(diff) / max(np.linalg.norm(ref), 1e-30)
        ),
    }


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------


def main():
    np.random.seed(SEED)

    print("# Chess channels + hyper-parallel-ops benchmark")
    print(f"# Seed: {SEED}")
    print(f"# Python: {sys.version.split()[0]}, numpy: {np.__version__}, scipy: {sp.__version__ if hasattr(sp, '__version__') else 'unknown'}")
    print()

    records: list[dict] = []

    # ---- chess-2D scale: 64×64 per channel, 10 channels, 640 total ----
    print("== chess-2D scale: per-channel C^64, 10 channels, total C^640 ==")
    H0_2d = h_free_2d()
    psi_2d = np.random.randn(640).astype(np.complex128) + 1j * np.random.randn(640).astype(np.complex128)
    psi_2d /= np.linalg.norm(psi_2d)

    struct_2d = verify_block_diagonal(H0_2d, n_channels=10)
    print(f"  H_0 shape: {H0_2d.shape}, nnz: {H0_2d.nnz}")
    print(f"  H_full = I_10 ⊗ H_0: shape {struct_2d['total_dim']}×{struct_2d['total_dim']}, nnz {struct_2d['H_full_nnz']}")
    print(f"  off-block coupling: {struct_2d['off_block_coupling_count']}  → strictly_block_diagonal={struct_2d['is_strictly_block_diagonal']}")
    print(f"  blocks identical (block 0 vs block 9): max_diff={struct_2d['blocks_identical_max_diff']}  → blocks_are_identical={struct_2d['blocks_are_identical']}")
    records.append({"phase": "structural-check", "scale": "chess-2D", **struct_2d})

    t_evolve = 0.1
    n_trials = 20

    # Bench per-channel sparse loop
    m_per_ch_2d, iqr_per_ch_2d, ref_2d = bench_per_channel_sparse(H0_2d, psi_2d, 10, t_evolve, n_trials)
    print(f"  per-channel sparse loop (current code path): {m_per_ch_2d:.3f} ms  IQR={iqr_per_ch_2d:.3f} ms")

    # Bench einsum-batched (eigenbasis form)
    m_eig_2d, iqr_eig_2d, alt_2d = bench_dense_eig_per_block(H0_2d, psi_2d, 10, t_evolve, n_trials)
    print(f"  eigenbasis-diagonal + einsum batched: {m_eig_2d:.3f} ms  IQR={iqr_eig_2d:.3f} ms")

    # Bench full-dim sparse baseline (the naive hyper-wrapped form)
    m_full_2d, iqr_full_2d, alt2_2d = bench_full_dim_sparse(H0_2d, psi_2d, 10, t_evolve, n_trials)
    print(f"  full-dim sparse expm_multiply on I_10⊗H_0: {m_full_2d:.3f} ms  IQR={iqr_full_2d:.3f} ms")

    # Cross-checks
    eig_vs_ref_2d = cross_check(ref_2d, alt_2d, "eig_batched_vs_per_channel_sparse")
    full_vs_ref_2d = cross_check(ref_2d, alt2_2d, "full_dim_vs_per_channel_sparse")
    print(f"  cross-check (eig vs per-ch): max_abs={eig_vs_ref_2d['max_abs_diff']:.2e}  rel_l2={eig_vs_ref_2d['relative_l2']:.2e}")
    print(f"  cross-check (full vs per-ch): max_abs={full_vs_ref_2d['max_abs_diff']:.2e}  rel_l2={full_vs_ref_2d['relative_l2']:.2e}")

    records.append({
        "phase": "bench", "scale": "chess-2D",
        "n_channels": 10, "block_dim": 64, "total_dim": 640, "t_evolve": t_evolve, "n_trials": n_trials,
        "per_channel_sparse_ms": m_per_ch_2d, "per_channel_sparse_iqr_ms": iqr_per_ch_2d,
        "eig_einsum_ms": m_eig_2d, "eig_einsum_iqr_ms": iqr_eig_2d,
        "full_dim_sparse_ms": m_full_2d, "full_dim_sparse_iqr_ms": iqr_full_2d,
        "speedup_eig_over_per_channel": m_per_ch_2d / m_eig_2d,
        "speedup_per_channel_over_full_dim": m_full_2d / m_per_ch_2d,
        "cross_check_eig_vs_per_channel": eig_vs_ref_2d,
        "cross_check_full_vs_per_channel": full_vs_ref_2d,
    })

    print()

    # ---- chess-4D scale: 4096×4096 per channel, 11 channels, 45056 total ----
    print("== chess-4D scale: per-channel C^4096, 11 channels, total C^45056 ==")
    H0_4d = h_free_4d()
    psi_4d = np.random.randn(45056).astype(np.complex128) + 1j * np.random.randn(45056).astype(np.complex128)
    psi_4d /= np.linalg.norm(psi_4d)

    struct_4d = verify_block_diagonal(H0_4d, n_channels=11)
    print(f"  H_0 shape: {H0_4d.shape}, nnz: {H0_4d.nnz}")
    print(f"  H_full = I_11 ⊗ H_0: shape {struct_4d['total_dim']}×{struct_4d['total_dim']}, nnz {struct_4d['H_full_nnz']}")
    print(f"  off-block coupling: {struct_4d['off_block_coupling_count']}  → strictly_block_diagonal={struct_4d['is_strictly_block_diagonal']}")
    print(f"  blocks identical (block 0 vs block 10): max_diff={struct_4d['blocks_identical_max_diff']}  → blocks_are_identical={struct_4d['blocks_are_identical']}")
    records.append({"phase": "structural-check", "scale": "chess-4D", **struct_4d})

    n_trials_4d = 5  # fewer trials at large scale

    m_per_ch_4d, iqr_per_ch_4d, ref_4d = bench_per_channel_sparse(H0_4d, psi_4d, 11, t_evolve, n_trials_4d)
    print(f"  per-channel sparse loop (current code path): {m_per_ch_4d:.3f} ms  IQR={iqr_per_ch_4d:.3f} ms")

    # Skip dense eigenbasis at 4D scale — 4096×4096 eigh takes ~1-3s by itself.
    # We DO benchmark it once, including the eigendecomposition cost, since
    # ADR-002 §6.1 deferred it and the question is whether the upfront cost
    # is recouped within typical M14.x animation frames (~hundreds of steps).
    t0 = time.perf_counter()
    H0_4d_dense = H0_4d.toarray()
    lam4, V4 = np.linalg.eigh(H0_4d_dense)
    eig_decomp_ms = (time.perf_counter() - t0) * 1000.0
    print(f"  eigh(H_0_4d) one-shot decomposition cost: {eig_decomp_ms:.1f} ms (amortized over future calls)")

    # Now benchmark the per-call cost (eigendecomposition already done)
    times = []
    psi_batched_4d = psi_4d.reshape(11, 4096).astype(np.complex128)
    out_eig_4d = None
    for _ in range(n_trials_4d):
        t0 = time.perf_counter()
        phases = np.exp(-1j * lam4 * t_evolve)
        step1 = psi_batched_4d @ V4.conj()
        step2 = step1 * phases
        step3 = step2 @ V4.T
        out_eig_4d = step3.ravel()
        t1 = time.perf_counter()
        times.append((t1 - t0) * 1000.0)
    times = np.asarray(times)
    m_eig_4d = float(np.median(times))
    iqr_eig_4d = float(np.percentile(times, 75) - np.percentile(times, 25))
    print(f"  eigenbasis batched (post-decomposition per-call): {m_eig_4d:.3f} ms  IQR={iqr_eig_4d:.3f} ms")

    eig_vs_ref_4d = cross_check(ref_4d, out_eig_4d, "eig_batched_vs_per_channel_sparse_4d")
    print(f"  cross-check (eig vs per-ch): max_abs={eig_vs_ref_4d['max_abs_diff']:.2e}  rel_l2={eig_vs_ref_4d['relative_l2']:.2e}")

    # Full-dim sparse baseline at 4D is expensive but feasible.
    m_full_4d, iqr_full_4d, ref_full_4d = bench_full_dim_sparse(H0_4d, psi_4d, 11, t_evolve, n_trials_4d)
    print(f"  full-dim sparse expm_multiply on I_11⊗H_0: {m_full_4d:.3f} ms  IQR={iqr_full_4d:.3f} ms")

    full_vs_ref_4d = cross_check(ref_4d, ref_full_4d, "full_dim_vs_per_channel_sparse_4d")
    print(f"  cross-check (full vs per-ch): max_abs={full_vs_ref_4d['max_abs_diff']:.2e}  rel_l2={full_vs_ref_4d['relative_l2']:.2e}")

    # Amortization break-even: how many propagation steps before
    # eig-batched (with one-shot decomp) beats per-channel sparse loop?
    # Solve eig_decomp_ms + N * m_eig_4d  <  N * m_per_ch_4d
    # =>     N  >  eig_decomp_ms / (m_per_ch_4d - m_eig_4d)
    if m_eig_4d < m_per_ch_4d:
        breakeven_4d = eig_decomp_ms / (m_per_ch_4d - m_eig_4d)
    else:
        breakeven_4d = float("inf")
    print(f"  eig-batched amortization breakeven: {breakeven_4d:.1f} steps")

    records.append({
        "phase": "bench", "scale": "chess-4D",
        "n_channels": 11, "block_dim": 4096, "total_dim": 45056, "t_evolve": t_evolve, "n_trials": n_trials_4d,
        "per_channel_sparse_ms": m_per_ch_4d, "per_channel_sparse_iqr_ms": iqr_per_ch_4d,
        "eig_decomp_one_shot_ms": eig_decomp_ms,
        "eig_einsum_per_call_ms": m_eig_4d, "eig_einsum_per_call_iqr_ms": iqr_eig_4d,
        "full_dim_sparse_ms": m_full_4d, "full_dim_sparse_iqr_ms": iqr_full_4d,
        "speedup_eig_over_per_channel": m_per_ch_4d / m_eig_4d,
        "speedup_per_channel_over_full_dim": m_full_4d / m_per_ch_4d,
        "eig_amortization_breakeven_steps": breakeven_4d,
        "cross_check_eig_vs_per_channel": eig_vs_ref_4d,
        "cross_check_full_vs_per_channel": full_vs_ref_4d,
    })

    # ---- Emit NDJSON ----
    out_path = Path(__file__).with_name(
        "chess-channels-and-hyper-parallel-per-finding-2026-05-11.ndjson"
    )
    with out_path.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, default=str) + "\n")
    print(f"\nNDJSON written: {out_path}")


if __name__ == "__main__":
    main()

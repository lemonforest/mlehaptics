"""Parity + invariants test for the ADR-002 §6.1 eigenbasis-diagonal
optimization shipped in :mod:`chess_spectral.qm_2d_dynamics.evolve_under_h0`.

The optimization replaced the previous per-channel
``scipy.sparse.linalg.expm_multiply`` loop with the eigenbasis-diagonal
form ``U(t) = V @ diag(exp(-i λ t)) @ V^H`` — H_0 is real-symmetric
Hermitian on ``C^64``, so :func:`numpy.linalg.eigh` decomposes it once
(lazily cached) and time evolution reduces to two matmuls + an
elementwise phase per call. At chess-2D scale this is ~196× faster than
the sparse loop, with max-abs deviation 1.8e-16 (machine-precision
bit-equivalent) per the spike benchmark at
``docs/srmech/notes/chess-channels-and-hyper-parallel-2026-05-11.md``.

This test file verifies:

  1. **Parity against a reference sparse path.** For deterministic
     ``ψ_0`` and a sweep of ``t`` values, the new path matches a fresh
     ``scipy.sparse.linalg.expm_multiply`` call on ``(-1j*t)*H_0`` to
     within 1e-14 absolute deviation per element (an order of
     magnitude looser than the spike's measured 1.8e-16 to absorb
     cross-platform FP variation).
  2. **Norm preservation** of the new path at machine precision (H_0
     Hermitian → U(t) unitary → ‖U(t) ψ‖ = ‖ψ‖).
  3. **Energy preservation** under U(t) (⟨H_0⟩ conserved).
  4. **Eigenbasis cache invariants:** repeated calls re-use the same
     ``(λ, V)`` object; different ``t`` give different results; same
     ``t`` gives bit-identical results.
  5. **Eigendecomposition reconstruction:** ``V @ diag(λ) @ V^H == H_0``
     at machine precision.

The pre-existing :file:`tests/test_qm_2d_dynamics.py` continues to
cover the public-API surface (shape, dtype, error handling, single-
channel-only mode, time-reversal); this file is the dedicated
optimization-parity regression layer.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest
from scipy.sparse.linalg import expm_multiply

HERE = Path(__file__).resolve().parent
PY_DIR = HERE.parent
sys.path.insert(0, str(PY_DIR))

from chess_spectral.qm_2d_dynamics import (  # noqa: E402
    H_FREE_2D,
    evolve_under_h0,
    _get_h0_eigenbasis_2d,
)
from chess_spectral.qm_2d import (  # noqa: E402
    CHANNEL_DIM,
    ENCODING_DIM,
    N_CHANNELS,
)


# Parity tolerance: the spike measured 1.8e-16 max-abs deviation between
# the eigenbasis path and the sparse expm_multiply path at chess-2D
# scale on a single platform. We use 1e-14 here to absorb cross-platform
# FP variation (Linux glibc vs Windows MSVC libm vs macOS Accelerate)
# while still failing if the optimization diverges meaningfully from the
# reference implementation. The spec is bit-equivalent; this is a
# generous fence around that target.
PARITY_TOL = 1e-14

# Norm / energy preservation tolerances. Strict for the new path since
# V is unitary and phases are unit-modulus (exactly so in IEEE 754 at
# the eigvals * t scales we exercise — t < 10 puts |λ t| < 80, well
# within the np.exp(-1j*x) accurate range).
NORM_TOL = 1e-12
ENERGY_TOL = 1e-10


# ─── Helpers ──────────────────────────────────────────────────────


def _reference_evolve_64_sparse(psi64: np.ndarray, t: float) -> np.ndarray:
    """Reference path: a single ``scipy.sparse.linalg.expm_multiply``
    call on ``(-1j*t)*H_0`` applied to a 64-block. This is the path the
    optimization replaces."""
    H0 = H_FREE_2D()
    A = (-1j * t) * H0
    return np.asarray(expm_multiply(A, psi64), dtype=np.complex128)


def _reference_evolve_640_sparse(psi640: np.ndarray, t: float) -> np.ndarray:
    """Reference path: per-channel ``expm_multiply`` loop over the 10
    channel blocks. Equivalent to the pre-optimization implementation."""
    H0 = H_FREE_2D()
    A = (-1j * t) * H0
    out = psi640.astype(np.complex128, copy=True)
    for ch in range(N_CHANNELS):
        start = ch * CHANNEL_DIM
        end = start + CHANNEL_DIM
        out[start:end] = expm_multiply(A, psi640[start:end].astype(np.complex128))
    return out


# ─── Eigenbasis cache structural invariants ────────────────────────


def test_eigenbasis_cache_shapes():
    """λ is real (64,); V is complex128 (64, 64)."""
    eigvals, V = _get_h0_eigenbasis_2d()
    assert eigvals.shape == (CHANNEL_DIM,)
    assert eigvals.dtype == np.float64
    assert V.shape == (CHANNEL_DIM, CHANNEL_DIM)
    assert V.dtype == np.complex128


def test_eigenbasis_cache_singleton():
    """Repeated calls return the identical tuple (cache hit, not a
    fresh eigendecomposition each call)."""
    pair1 = _get_h0_eigenbasis_2d()
    pair2 = _get_h0_eigenbasis_2d()
    assert pair1 is pair2
    # Element identity, not just equality:
    assert pair1[0] is pair2[0]
    assert pair1[1] is pair2[1]


def test_eigenbasis_reconstructs_h0_exactly():
    """V @ diag(λ) @ V^H == H_0 to machine precision."""
    eigvals, V = _get_h0_eigenbasis_2d()
    H0 = H_FREE_2D().toarray()
    H0_reconstructed = V @ np.diag(eigvals.astype(np.complex128)) @ V.conj().T
    max_dev = np.max(np.abs(H0 - H0_reconstructed))
    # eigh is backward-stable; reconstruction is good to ~5e-15 typically.
    assert max_dev < 1e-12, f"H_0 reconstruction max_dev={max_dev:.2e}"


def test_eigenbasis_V_is_unitary():
    """V^H V == I, V V^H == I to machine precision."""
    _, V = _get_h0_eigenbasis_2d()
    I = np.eye(CHANNEL_DIM, dtype=np.complex128)
    left = V.conj().T @ V
    right = V @ V.conj().T
    assert np.max(np.abs(left - I)) < 1e-12
    assert np.max(np.abs(right - I)) < 1e-12


def test_eigenbasis_eigvals_in_spectrum():
    """All eigenvalues lie in [-8, 0] (H_0 = -Δ where Δ ≥ 0 on the
    8×8 path-graph, spectrum ≈ [0, 7.7])."""
    eigvals, _ = _get_h0_eigenbasis_2d()
    assert eigvals.min() > -8.0
    assert eigvals.max() < 1e-10  # smallest |Δ| eigenvalue is exactly 0


# ─── Parity: new path vs sparse expm_multiply reference ─────────────


# Sweep of t values covering small (animation-frame), medium
# (multi-frame), and larger (one full chess move) propagation steps.
# The spike used t=0.1; we cover both sides plus zero (handled as
# no-op).
_T_SWEEP = [1e-6, 1e-3, 0.05, 0.1, 0.5, 1.0, 2.5]


@pytest.mark.parametrize("t", _T_SWEEP)
def test_parity_single_channel_block(t: float):
    """For a single 64-block ψ, the eigenbasis path matches a fresh
    ``expm_multiply((-1j*t)*H_0, ψ)`` call to within PARITY_TOL."""
    rng = np.random.default_rng(seed=0xC0FFEE)
    psi = rng.standard_normal(CHANNEL_DIM) + 1j * rng.standard_normal(CHANNEL_DIM)
    psi /= np.linalg.norm(psi)

    out_new = evolve_under_h0(psi, t=t)
    out_ref = _reference_evolve_64_sparse(psi, t=t)

    max_dev = float(np.max(np.abs(out_new - out_ref)))
    rel_l2 = float(
        np.linalg.norm(out_new - out_ref) / max(np.linalg.norm(out_ref), 1e-30)
    )
    assert max_dev < PARITY_TOL, (
        f"t={t}: eigenbasis path diverges from sparse reference; "
        f"max_dev={max_dev:.2e}, rel_l2={rel_l2:.2e}"
    )


@pytest.mark.parametrize("t", _T_SWEEP)
def test_parity_full_640_state(t: float):
    """For the full 640-dim 10-channel state, the eigenbasis path
    matches the per-channel sparse loop to within PARITY_TOL."""
    rng = np.random.default_rng(seed=0xBADF00D)
    psi = rng.standard_normal(ENCODING_DIM) + 1j * rng.standard_normal(ENCODING_DIM)
    psi /= np.linalg.norm(psi)

    out_new = evolve_under_h0(psi, t=t)
    out_ref = _reference_evolve_640_sparse(psi, t=t)

    max_dev = float(np.max(np.abs(out_new - out_ref)))
    rel_l2 = float(
        np.linalg.norm(out_new - out_ref) / max(np.linalg.norm(out_ref), 1e-30)
    )
    assert max_dev < PARITY_TOL, (
        f"t={t}: batched eigenbasis path diverges from per-channel "
        f"sparse loop; max_dev={max_dev:.2e}, rel_l2={rel_l2:.2e}"
    )


@pytest.mark.parametrize(
    "channel",
    ["A1", "A2", "B1", "B2", "E", "F1", "F2", "F3", "FA", "FD"],
)
def test_parity_single_channel_arg(channel: str):
    """For each of the 10 channel names, ``channel=`` mode matches a
    sparse evolution of that single block, with the other 9 blocks
    bit-identical to input."""
    rng = np.random.default_rng(seed=0x1234)
    psi = rng.standard_normal(ENCODING_DIM) + 1j * rng.standard_normal(ENCODING_DIM)
    psi /= np.linalg.norm(psi)

    t = 0.1
    out = evolve_under_h0(psi, t=t, channel=channel)

    # The named channel's block must match the sparse reference
    from chess_spectral.encoder import CHANNELS
    start = next(s for n, s in CHANNELS if n == channel)
    end = start + CHANNEL_DIM
    block_ref = _reference_evolve_64_sparse(
        psi[start:end].astype(np.complex128), t=t
    )
    max_dev = float(np.max(np.abs(out[start:end] - block_ref)))
    assert max_dev < PARITY_TOL, (
        f"channel={channel}: block diverges from sparse ref; max_dev={max_dev:.2e}"
    )

    # All other blocks are bit-identical to the (complex128-cast) input.
    psi_c = psi.astype(np.complex128)
    if start > 0:
        np.testing.assert_array_equal(out[:start], psi_c[:start])
    if end < ENCODING_DIM:
        np.testing.assert_array_equal(out[end:], psi_c[end:])


# ─── Norm and energy preservation (new path explicitly) ────────────


@pytest.mark.parametrize("t", _T_SWEEP)
def test_norm_preservation_single_block(t: float):
    rng = np.random.default_rng(seed=0xABCDEF)
    psi = rng.standard_normal(CHANNEL_DIM) + 1j * rng.standard_normal(CHANNEL_DIM)
    psi /= np.linalg.norm(psi)
    out = evolve_under_h0(psi, t=t)
    assert abs(np.linalg.norm(out) - 1.0) < NORM_TOL


@pytest.mark.parametrize("t", _T_SWEEP)
def test_norm_preservation_full_640(t: float):
    rng = np.random.default_rng(seed=0xFEEDBEEF)
    psi = rng.standard_normal(ENCODING_DIM) + 1j * rng.standard_normal(ENCODING_DIM)
    psi /= np.linalg.norm(psi)
    out = evolve_under_h0(psi, t=t)
    assert abs(np.linalg.norm(out) - 1.0) < NORM_TOL


@pytest.mark.parametrize("t", [0.05, 0.1, 0.5, 1.0])
def test_energy_preservation(t: float):
    """⟨ψ|H_0|ψ⟩ is invariant under U(t) (since [U(t), H_0] = 0)."""
    rng = np.random.default_rng(seed=0xDEADBEEF)
    psi = rng.standard_normal(CHANNEL_DIM) + 1j * rng.standard_normal(CHANNEL_DIM)
    psi /= np.linalg.norm(psi)
    H = H_FREE_2D()
    e_before = (psi.conj() @ (H @ psi)).real
    out = evolve_under_h0(psi, t=t)
    e_after = (out.conj() @ (H @ out)).real
    assert abs(e_after - e_before) < ENERGY_TOL, (
        f"t={t}: energy not preserved; before={e_before:.6e} after={e_after:.6e}"
    )


# ─── Determinism / cache-invariance properties ─────────────────────


def test_same_t_gives_bit_identical_result():
    """Calling evolve_under_h0(ψ, t) twice yields identical output —
    the eigenbasis cache + the deterministic matmul sequence have no
    hidden state."""
    rng = np.random.default_rng(seed=0xCAFE)
    psi = rng.standard_normal(ENCODING_DIM) + 1j * rng.standard_normal(ENCODING_DIM)
    psi /= np.linalg.norm(psi)
    out1 = evolve_under_h0(psi, t=0.123)
    out2 = evolve_under_h0(psi, t=0.123)
    np.testing.assert_array_equal(out1, out2)


def test_different_t_gives_different_result():
    """Confirms the phase factor is actually being applied — calling
    with two different t values yields different output."""
    rng = np.random.default_rng(seed=0xBEEF)
    psi = rng.standard_normal(CHANNEL_DIM) + 1j * rng.standard_normal(CHANNEL_DIM)
    psi /= np.linalg.norm(psi)
    out_a = evolve_under_h0(psi, t=0.1)
    out_b = evolve_under_h0(psi, t=0.2)
    assert not np.allclose(out_a, out_b, atol=1e-6)


def test_inverse_evolution_recovers_input():
    """U(-t) ∘ U(t) ψ == ψ to machine precision (both paths go through
    the eigenbasis; conjugate phases cancel exactly)."""
    rng = np.random.default_rng(seed=0xF00BA5)
    psi = rng.standard_normal(ENCODING_DIM) + 1j * rng.standard_normal(ENCODING_DIM)
    psi /= np.linalg.norm(psi)
    forward = evolve_under_h0(psi, t=0.7)
    backward = evolve_under_h0(forward, t=-0.7)
    # Eigenbasis path: 2x (matmul + elementwise) per direction, so
    # accumulated round-off is ~tens of ULP. 1e-12 is comfortable.
    np.testing.assert_allclose(backward, psi.astype(np.complex128), atol=1e-12)


def test_composition_t1_plus_t2():
    """U(t1+t2) == U(t2) ∘ U(t1) in the eigenbasis (exact at the
    elementwise-phase level, modulo float32-tail roundoff in λ)."""
    rng = np.random.default_rng(seed=0x5AFEBABE)
    psi = rng.standard_normal(CHANNEL_DIM) + 1j * rng.standard_normal(CHANNEL_DIM)
    psi /= np.linalg.norm(psi)
    t1, t2 = 0.3, 0.45
    composed = evolve_under_h0(evolve_under_h0(psi, t=t1), t=t2)
    direct = evolve_under_h0(psi, t=t1 + t2)
    np.testing.assert_allclose(composed, direct, atol=1e-12)

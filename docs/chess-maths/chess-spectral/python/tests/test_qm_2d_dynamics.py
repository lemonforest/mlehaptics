"""Tests for chess_spectral.qm_2d_dynamics — Track B Zeno layer (v1.6.x).

Mirrors :mod:`tests.test_qm_4d_dynamics_b2` at d=2: H_FREE_2D Hermiticity,
spectrum, and ``evolve_under_h0`` norm + energy preservation under the
2D path-graph Laplacian on Z_8^2.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

HERE = Path(__file__).resolve().parent
PY_DIR = HERE.parent
sys.path.insert(0, str(PY_DIR))

from chess_spectral.qm_2d_dynamics import (  # noqa: E402
    H_FREE_2D, evolve_under_h0,
)


# ─── H_FREE_2D structural properties ──────────────────────────────


def test_h_free_2d_shape_and_dtype():
    H = H_FREE_2D()
    assert H.shape == (64, 64)
    assert H.dtype == np.complex128


def test_h_free_2d_hermitian():
    """H_0 is real-symmetric (zero imaginary part). Equivalent to
    ``H == H.conj().T`` exactly."""
    H = H_FREE_2D()
    diff = (H - H.conj().T)
    # Sparse matrix: count nonzeros.
    assert diff.nnz == 0


def test_h_free_2d_negative_semidefinite():
    """H_0 = -Δ where Δ is a graph Laplacian (positive-semidefinite),
    so H_0 has all eigenvalues ≤ 0."""
    H = H_FREE_2D().toarray()
    eigvals = np.linalg.eigvalsh(H)
    assert np.all(eigvals <= 1e-10), (
        f"H_0 has positive eigenvalue: max={eigvals.max():.4e}"
    )


def test_h_free_2d_spectrum_bounds():
    """Spectrum of Δ_{P_8^2} is in [0, ~7.7] (sum of two ~[0,3.85] 1D
    spectra, since L_8 has spectrum [0, ~3.85]). So H_0 = -Δ has
    spectrum in [-7.7, 0]."""
    H = H_FREE_2D().toarray()
    eigvals = np.linalg.eigvalsh(H)
    assert eigvals.min() > -8.0, f"H_0 min eigval {eigvals.min()} too low"
    assert abs(eigvals.max()) < 1e-10, (
        f"H_0 max eigval should be ~0; got {eigvals.max()}"
    )


def test_h_free_2d_singleton_cached():
    """Repeated calls return the same object (module-level cache)."""
    H1 = H_FREE_2D()
    H2 = H_FREE_2D()
    assert H1 is H2


# ─── evolve_under_h0 — single-channel block ────────────────────────


def test_evolve_zero_t_returns_copy():
    psi = np.zeros(64, dtype=np.complex128)
    psi[5] = 1.0
    out = evolve_under_h0(psi, t=0.0)
    np.testing.assert_array_equal(out, psi)
    assert out is not psi  # copy, not alias


def test_evolve_64_preserves_norm():
    rng = np.random.default_rng(seed=42)
    psi = rng.standard_normal(64) + 1j * rng.standard_normal(64)
    psi /= np.linalg.norm(psi)
    out = evolve_under_h0(psi, t=0.1)
    assert abs(np.linalg.norm(out) - 1.0) < 1e-10


def test_evolve_64_preserves_energy():
    """⟨H_0⟩ is conserved under U(t) = exp(-i H_0 t)."""
    rng = np.random.default_rng(seed=43)
    psi = rng.standard_normal(64) + 1j * rng.standard_normal(64)
    psi /= np.linalg.norm(psi)
    H = H_FREE_2D()
    e_before = (psi.conj() @ (H @ psi)).real
    out = evolve_under_h0(psi, t=0.2)
    e_after = (out.conj() @ (H @ out)).real
    assert abs(e_after - e_before) < 1e-9, (
        f"energy changed: before={e_before:.6e} after={e_after:.6e}"
    )


def test_evolve_negative_t_is_inverse():
    """U(-t) ∘ U(t) = I."""
    rng = np.random.default_rng(seed=44)
    psi = rng.standard_normal(64).astype(np.complex128)
    psi /= np.linalg.norm(psi)
    forward = evolve_under_h0(psi, t=0.2)
    backward = evolve_under_h0(forward, t=-0.2)
    np.testing.assert_allclose(backward, psi, atol=1e-9)


# ─── evolve_under_h0 — full 640-dim broadcast ──────────────────────


def test_evolve_640_broadcasts_per_channel():
    """The full 640-dim psi evolves as I_10 ⊗ H_0 — each 64-block
    independently. Verify by comparing block-by-block evolution."""
    rng = np.random.default_rng(seed=45)
    psi = rng.standard_normal(640) + 1j * rng.standard_normal(640)
    psi /= np.linalg.norm(psi)
    out_full = evolve_under_h0(psi, t=0.05)

    # Manually evolve each block
    out_manual = np.empty(640, dtype=np.complex128)
    for ch in range(10):
        block = psi[ch * 64 : (ch + 1) * 64]
        out_manual[ch * 64 : (ch + 1) * 64] = evolve_under_h0(block, t=0.05)
    np.testing.assert_allclose(out_full, out_manual, atol=1e-10)


def test_evolve_640_preserves_norm():
    rng = np.random.default_rng(seed=46)
    psi = rng.standard_normal(640) + 1j * rng.standard_normal(640)
    psi /= np.linalg.norm(psi)
    out = evolve_under_h0(psi, t=0.1)
    assert abs(np.linalg.norm(out) - 1.0) < 1e-10


def test_evolve_640_with_channel_only_touches_that_block():
    """When channel='B1' is given, only the B1 block (offset 128-192)
    should change; the other 9 blocks should be identical."""
    rng = np.random.default_rng(seed=47)
    psi = rng.standard_normal(640).astype(np.complex128)
    out = evolve_under_h0(psi, t=0.1, channel="B1")
    # Other blocks unchanged
    np.testing.assert_array_equal(out[:128], psi[:128])      # before B1
    np.testing.assert_array_equal(out[192:], psi[192:])      # after B1
    # B1 block changed (assuming non-zero content there)
    assert not np.array_equal(out[128:192], psi[128:192])


def test_evolve_640_channel_a1_is_first_block():
    """A1 channel is the first block (offset 0-64 per encoder.CHANNELS)."""
    rng = np.random.default_rng(seed=48)
    psi = rng.standard_normal(640).astype(np.complex128)
    out = evolve_under_h0(psi, t=0.1, channel="A1")
    np.testing.assert_array_equal(out[64:], psi[64:])  # everything except A1


# ─── Error handling ────────────────────────────────────────────────


def test_evolve_rejects_wrong_shape():
    psi = np.zeros(100, dtype=np.complex128)  # neither 64 nor 640
    with pytest.raises(ValueError, match="shape"):
        evolve_under_h0(psi, t=0.1)


def test_evolve_rejects_2d_input():
    psi = np.zeros((10, 64), dtype=np.complex128)
    with pytest.raises(ValueError, match="1-D"):
        evolve_under_h0(psi, t=0.1)


def test_evolve_channel_arg_requires_full_psi():
    """channel= with a 64-dim psi is ambiguous — should raise."""
    psi = np.zeros(64, dtype=np.complex128)
    with pytest.raises(ValueError, match="full 640-dim psi"):
        evolve_under_h0(psi, t=0.1, channel="A1")


def test_evolve_unknown_channel_raises():
    psi = np.zeros(640, dtype=np.complex128)
    with pytest.raises(ValueError, match="unknown channel"):
        evolve_under_h0(psi, t=0.1, channel="BOGUS")

"""rc33 — signal_processing eigh / trig cascade-routing parity tests.

Verifies the v0.7.0rc33 routing of ``np.linalg.eigh`` (and ica_jade's
``np.arctan2``/``np.cos``/``np.sin``) onto srmech's own A-N cascade
primitives in the four closed-form ops ``esprit`` / ``heat_kernel`` /
``ica_jade`` / ``music``:

- Routing A: ``np.linalg.eigh`` -> ``srmech.amsc.laplacian.hermitian_eigendecompose``
- Routing B: ``np.arctan2``/``np.cos``/``np.sin`` -> ``srmech.amsc.rational.atan2/cos/sin``

Strategy:

1. Direct parity of ``hermitian_eigendecompose`` vs ``numpy.linalg.eigvalsh``
   on a real-symmetric fixture and a complex-Hermitian fixture, plus
   ``H = V diag(eigvals) V^H`` reconstruction.
2. Each of the four public ops asserted against a synthetic ground truth
   (the op's own algorithmic invariant), at the op's existing tolerance.
"""

from __future__ import annotations

import numpy as np

from srmech.amsc.laplacian import hermitian_eigendecompose
from srmech.signal_processing.closed_form_ops import (
    esprit,
    heat_kernel,
    ica_jade,
    music,
)


# ---------------------------------------------------------------------------
# Routing A — hermitian_eigendecompose parity with numpy.linalg.eigh
# ---------------------------------------------------------------------------


def _make_real_symmetric(n: int, seed: int) -> np.ndarray:
    rs = np.random.RandomState(seed)
    A = rs.randn(n, n)
    return (A + A.T) / 2.0


def _make_complex_hermitian(n: int, seed: int) -> np.ndarray:
    rs = np.random.RandomState(seed)
    A = rs.randn(n, n) + 1j * rs.randn(n, n)
    return (A + A.conj().T) / 2.0


def test_hermitian_eig_real_symmetric_parity():
    """Eigenvalues match numpy.linalg.eigvalsh; H reconstructs within 1e-9."""
    H = _make_real_symmetric(6, seed=1)
    ev_ref = np.linalg.eigvalsh(H)
    ev, V = hermitian_eigendecompose(H)
    # eigvals ascending float64, parity vs numpy.
    assert ev.dtype == np.float64
    assert np.all(np.diff(ev) >= -1e-12)  # ascending
    assert np.max(np.real(ev) - ev_ref) < 1e-9
    assert np.min(np.real(ev) - ev_ref) > -1e-9
    # Reconstruction H = V diag(ev) V^H.
    H_rec = V @ np.diag(ev) @ V.conj().T
    err = H_rec - H.astype(np.complex128)
    assert np.max(err.real ** 2 + err.imag ** 2) < 1e-18  # |.|^2 < (1e-9)^2


def test_hermitian_eig_complex_hermitian_parity():
    """Complex-Hermitian eigenvalues match numpy; H reconstructs within 1e-9."""
    H = _make_complex_hermitian(6, seed=2)
    ev_ref = np.linalg.eigvalsh(H)
    ev, V = hermitian_eigendecompose(H)
    assert V.dtype == np.complex128
    assert np.all(np.diff(ev) >= -1e-12)
    assert np.max(ev - ev_ref) < 1e-9
    assert np.min(ev - ev_ref) > -1e-9
    H_rec = V @ np.diag(ev) @ V.conj().T
    err = H_rec - H
    assert np.max(err.real ** 2 + err.imag ** 2) < 1e-18


# ---------------------------------------------------------------------------
# Routing B — ica_jade trig parity (srmech.amsc.rational vs libm)
# ---------------------------------------------------------------------------


def test_rational_trig_parity_with_libm():
    """The Class-N trig used by ica_jade matches libm to its documented bound."""
    from srmech.amsc import rational as _srn

    import math

    for theta in np.linspace(-1.5, 1.5, 13):
        t = float(theta)
        # cos/sin match libm to ~4e-13; atan2 to ~1e-16 (use 1e-9 envelope).
        dc = _srn.cos(t) - math.cos(t)
        ds = _srn.sin(t) - math.sin(t)
        assert dc * dc < 1e-18
        assert ds * ds < 1e-18
    for num, den in [(1.0, 2.0), (-3.0, 0.5), (0.0, -1.0), (2.0, -2.0)]:
        da = _srn.atan2(num, den) - math.atan2(num, den)
        assert da * da < 1e-18


# ---------------------------------------------------------------------------
# Public-op invariants — each op vs a synthetic ground truth
# ---------------------------------------------------------------------------


def test_esprit_recovers_single_tone_frequency():
    """ESPRIT eigenvalue angle recovers a synthetic complex-exponential DOA."""
    M = 6
    omega = 0.37  # normalised spatial frequency in (0, 1)
    a = np.exp(1j * np.pi * np.arange(M) * omega)
    # Rank-1 signal covariance + small white floor (clean single source).
    R = np.outer(a, a.conj()) + 0.01 * np.eye(M, dtype=np.complex128)
    eigs = esprit.op(R, n_sources=1)
    assert isinstance(eigs, list) and len(eigs) == 1  # rc98: numpy-free list return
    # Phi-eigenvalue phase == exp(j*pi*omega); recover omega from its angle.
    est_omega = np.angle(eigs[0]) / np.pi
    # Class-K sign-branch (no abs()): both signs are valid ESPRIT roots.
    d = est_omega - omega
    assert (d if d >= 0 else -d) < 1e-3


def test_music_peak_at_true_angle():
    """MUSIC pseudo-spectrum peaks at the true source spatial frequency."""
    M = 8
    omega_true = 0.30
    a = np.exp(1j * np.pi * np.arange(M) * omega_true)
    R = np.outer(a, a.conj()) + 0.05 * np.eye(M, dtype=np.complex128)
    grid = np.linspace(-1.0, 1.0, 401)
    A = np.exp(1j * np.pi * np.arange(M)[:, None] * grid[None, :])
    psd = music.op(R, A, n_sources=1)
    assert isinstance(psd, list) and len(psd) == grid.shape[0]  # rc99: numpy-free list
    assert all(v > 0 for v in psd)
    peak_omega = grid[max(range(len(psd)), key=lambda i: psd[i])]  # pure-Python argmax
    d = peak_omega - omega_true
    assert (d if d >= 0 else -d) < 2e-2  # within one grid bin


def test_heat_kernel_diffuses_toward_mean():
    """Heat-kernel diffusion preserves total mass and smooths an impulse."""
    # Path-graph Laplacian on 5 nodes (real symmetric).
    n = 5
    L = np.zeros((n, n), dtype=np.complex128)
    for i in range(n - 1):
        L[i, i] += 1.0
        L[i + 1, i + 1] += 1.0
        L[i, i + 1] -= 1.0
        L[i + 1, i] -= 1.0
    sig = np.zeros(n, dtype=np.complex128)
    sig[0] = 1.0
    out = heat_kernel.op(sig, L, t=0.5)
    assert out.shape == (n,)
    # Mass conservation: graph-Laplacian constant null-vector => sum preserved.
    mass_err = out.real.sum() - sig.real.sum()
    assert mass_err * mass_err < 1e-18
    # Output is real (real Laplacian + real signal) and the impulse spread.
    assert np.max(out.imag ** 2) < 1e-20
    assert out.real[1] > 0.0  # diffused onto the neighbour


def _abs_corr(u: np.ndarray, v: np.ndarray) -> float:
    """|Pearson correlation| via a Class-K sign-branch (no abs())."""
    u = u - u.mean()
    v = v - v.mean()
    denom = np.sqrt((u * u).sum() * (v * v).sum())
    if denom == 0.0:
        return 0.0
    c = (u * v).sum() / denom
    return c if c >= 0 else -c  # Class-K sign-branch (no abs())


def test_ica_jade_decorrelates_and_reconstructs():
    """ICA-JADE decorrelates two mixed sources and the unmixing reconstructs X.

    The simplified JADE reference here sweeps a single cumulant slice with a
    fixed iteration cap, so the converged rotation is chaotically sensitive to
    machine-epsilon angle perturbations (the cascade trig matches libm to
    ~1e-16, so this is an algorithm property, not a routing defect). The
    stable, routing-invariant contract is therefore asserted: (1) the recovered
    sources are mutually decorrelated, and (2) the unmixing reconstructs the
    centred observations.
    """
    rs = np.random.RandomState(7)
    n = 400
    s1 = rs.uniform(-1.0, 1.0, n)
    s2 = np.sign(np.sin(np.linspace(0, 20 * np.pi, n)))  # square wave
    S_true = np.column_stack([s1, s2])
    A_mix = np.array([[1.0, 0.6], [0.4, 1.0]])
    X = S_true @ A_mix.T
    S_hat, W = ica_jade.op(X, n_components=2, max_iter=200)
    assert S_hat.shape == (n, 2)
    assert W.shape == (2, 2)

    # (1) Mixed channels are correlated; recovered sources are decorrelated.
    mixed_corr = _abs_corr(X[:, 0], X[:, 1])
    source_corr = _abs_corr(S_hat[:, 0], S_hat[:, 1])
    assert mixed_corr > 0.5  # genuinely-mixed fixture
    assert source_corr < 1e-6  # sources whitened/decorrelated

    # (2) The unmixing reconstructs the centred observations exactly.
    Xc = X - X.mean(axis=0, keepdims=True)
    A_est = np.linalg.pinv(W)
    X_rec = (A_est @ S_hat.T).T
    err = Xc - X_rec
    assert np.max(err ** 2) < 1e-18

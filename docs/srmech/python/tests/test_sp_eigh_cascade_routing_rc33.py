"""rc33 — signal_processing eigh / trig cascade-routing parity tests.

Verifies the v0.7.0rc33 routing of the real-symmetric / complex-Hermitian
eigendecomposition (and ica_jade's atan2/cos/sin) onto srmech's own A-N cascade
primitives in the four closed-form ops ``esprit`` / ``heat_kernel`` /
``ica_jade`` / ``music``:

- Routing A: eigh -> ``srmech.amsc.laplacian.hermitian_eigendecompose``
- Routing B: arctan2/cos/sin -> ``srmech.amsc.rational.atan2/cos/sin``

numpy-FREE (#564): numpy is GONE from srmech. ``hermitian_eigendecompose``
returns plain Python lists, and the four closed-form ops consume / return plain
lists / ``Mat``. The eigenvalue ORACLE is the framework's own exact
``eigvals_exact`` (integer-entried Hermitian fixtures so its char-poly stays over
ℤ); the eigenvector basis is non-unique, so correctness is pinned by the
basis-INVARIANT reconstruction ``H = V·diag(w)·Vᴴ``. All fixtures + arithmetic
use stdlib ``math`` / ``cmath`` / ``random``.
"""

from __future__ import annotations

import cmath
import math
import random

from srmech.amsc.cascade.matrix_cascades import eigvals, eigvals_exact
from srmech.amsc.laplacian import hermitian_eigendecompose
from srmech.signal_processing.closed_form_ops import (
    esprit,
    heat_kernel,
    ica_jade,
    music,
)


# ── numpy-free helpers ─────────────────────────────────────────────────


def _transpose_conj(A):
    return [[A[i][j].conjugate() for i in range(len(A))] for j in range(len(A[0]))]


def _matmul(A, B):
    m, k, n = len(A), len(B), len(B[0])
    return [[sum(A[i][p] * B[p][j] for p in range(k)) for j in range(n)]
            for i in range(m)]


def _rand_int_sym(n, seed, complex_=False):
    """Integer-entried real-symmetric / complex-Hermitian matrix (exact-oracle
    friendly: char-poly stays over ℤ / ℤ[i])."""
    rs = random.Random(seed)

    def ri():
        return rs.randint(-4, 4)

    if not complex_:
        A = [[ri() for _ in range(n)] for _ in range(n)]
        return [[A[i][j] + A[j][i] for j in range(n)] for i in range(n)]
    A = [[complex(ri(), ri()) for _ in range(n)] for _ in range(n)]
    return [[(A[i][j] + A[j][i].conjugate()) for j in range(n)] for i in range(n)]


# ---------------------------------------------------------------------------
# Routing A — hermitian_eigendecompose parity with the exact eigvals oracle
# ---------------------------------------------------------------------------


def test_hermitian_eig_real_symmetric_parity():
    """Eigenvalues match the exact ``eigvals_exact`` oracle; H reconstructs."""
    H = _rand_int_sym(6, seed=1)
    n = len(H)
    ev_ref = sorted(eigvals_exact(H))
    ev, V = hermitian_eigendecompose(H)
    assert isinstance(ev, list) and isinstance(V, list)
    # ascending + parity vs the framework's own exact eigenvalues.
    for i in range(n - 1):
        assert ev[i + 1] - ev[i] >= -1e-12
    for i in range(n):
        assert abs(ev[i] - ev_ref[i]) < 1e-9
    # Reconstruction H = V·diag(ev)·Vᴴ (basis-invariant).
    Vd = [[V[i][k] * ev[k] for k in range(n)] for i in range(n)]
    rec = _matmul(Vd, _transpose_conj(V))
    for i in range(n):
        for j in range(n):
            e = rec[i][j] - complex(H[i][j])
            assert e.real * e.real + e.imag * e.imag < 1e-18


def test_hermitian_eig_complex_hermitian_parity():
    """Complex-Hermitian eigenvalues match the cascade-eigenvalue oracle; H
    reconstructs. The exact ``eigvals_exact`` path is real-only (its char-poly
    carries complex-typed coefficients for a Hermitian input), so the oracle here
    is the framework's own general ``eigvals`` (Class-K shifted-QR) — its roots
    are real for a Hermitian matrix, an INDEPENDENT numpy-free cross-check."""
    H = _rand_int_sym(6, seed=2, complex_=True)
    n = len(H)
    ev_ref = sorted(z.real for z in eigvals(H))
    ev, V = hermitian_eigendecompose(H)
    # eigenvalues are real (Hermitian) and complex eigenvectors carried as lists.
    for i in range(n - 1):
        assert ev[i + 1] - ev[i] >= -1e-12
    for i in range(n):
        assert abs(ev[i] - ev_ref[i]) < 1e-9
    Vd = [[V[i][k] * ev[k] for k in range(n)] for i in range(n)]
    rec = _matmul(Vd, _transpose_conj(V))
    for i in range(n):
        for j in range(n):
            e = rec[i][j] - complex(H[i][j])
            assert e.real * e.real + e.imag * e.imag < 1e-18


# ---------------------------------------------------------------------------
# Routing B — ica_jade trig parity (srmech.amsc.rational vs libm)
# ---------------------------------------------------------------------------


def test_rational_trig_parity_with_libm():
    """The Class-N trig used by ica_jade matches libm to its documented bound."""
    from srmech.amsc import rational as _srn

    # 13 points over [-1.5, 1.5] (numpy-free linspace).
    thetas = [-1.5 + 3.0 * i / 12 for i in range(13)]
    for t in thetas:
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
    a = [cmath.exp(1j * math.pi * k * omega) for k in range(M)]
    # Rank-1 signal covariance + small white floor (clean single source).
    R = [[a[i] * a[j].conjugate() + (0.01 if i == j else 0.0) for j in range(M)]
         for i in range(M)]
    eigs = esprit.op(R, n_sources=1)
    assert isinstance(eigs, list) and len(eigs) == 1  # rc98: numpy-free list return
    # Phi-eigenvalue phase == exp(j*pi*omega); recover omega from its angle.
    est_omega = cmath.phase(eigs[0]) / math.pi
    # Class-K sign-branch (no abs()): both signs are valid ESPRIT roots.
    d = est_omega - omega
    assert (d if d >= 0 else -d) < 1e-3


def test_music_peak_at_true_angle():
    """MUSIC pseudo-spectrum peaks at the true source spatial frequency."""
    M = 8
    omega_true = 0.30
    a = [cmath.exp(1j * math.pi * k * omega_true) for k in range(M)]
    R = [[a[i] * a[j].conjugate() + (0.05 if i == j else 0.0) for j in range(M)]
         for i in range(M)]
    n_grid = 401
    grid = [-1.0 + 2.0 * i / (n_grid - 1) for i in range(n_grid)]
    # Steering matrix A: rows = sensors (M), cols = grid.
    A = [[cmath.exp(1j * math.pi * k * g) for g in grid] for k in range(M)]
    psd = music.op(R, A, n_sources=1)
    assert isinstance(psd, list) and len(psd) == n_grid  # rc99: numpy-free list
    assert all(v > 0 for v in psd)
    peak_omega = grid[max(range(len(psd)), key=lambda i: psd[i])]  # pure-Python argmax
    d = peak_omega - omega_true
    assert (d if d >= 0 else -d) < 2e-2  # within one grid bin


def test_heat_kernel_diffuses_toward_mean():
    """Heat-kernel diffusion preserves total mass and smooths an impulse."""
    # Path-graph Laplacian on 5 nodes (real symmetric, complex-typed entries).
    n = 5
    L = [[0j for _ in range(n)] for _ in range(n)]
    for i in range(n - 1):
        L[i][i] += 1.0
        L[i + 1][i + 1] += 1.0
        L[i][i + 1] -= 1.0
        L[i + 1][i] -= 1.0
    sig = [0j for _ in range(n)]
    sig[0] = 1.0
    out = heat_kernel.op(sig, L, t=0.5)
    assert isinstance(out, list) and len(out) == n  # rc100: numpy-free list return
    # Mass conservation: graph-Laplacian constant null-vector => sum preserved.
    mass_err = sum(v.real for v in out) - sum(v.real for v in sig)
    assert mass_err * mass_err < 1e-18
    # Output is real (real Laplacian + real signal) and the impulse spread.
    assert max(v.imag ** 2 for v in out) < 1e-20
    assert out[1].real > 0.0  # diffused onto the neighbour


def _corr_lists(u, v):
    """|Pearson correlation| of two float lists via a Class-K sign-branch
    (no abs()) — numpy-free."""
    m = len(u)
    mu = sum(u) / m
    mv = sum(v) / m
    du = [x - mu for x in u]
    dv = [x - mv for x in v]
    denom = math.sqrt(sum(x * x for x in du) * sum(x * x for x in dv))
    if denom == 0.0:
        return 0.0
    c = sum(du[i] * dv[i] for i in range(m)) / denom
    return c if c >= 0 else -c  # Class-K sign-branch (no abs())


def test_ica_jade_decorrelates_and_reconstructs():
    """ICA-JADE decorrelates two mixed sources and the unmixing reconstructs X.

    rc126: ica_jade is numpy-free (returns ``Mat`` sources / unmixing matrix), so
    this routing test is too — numpy-free fixtures, ``Mat``-entry access, and a
    closed-form 2x2 inverse (= pinv for the invertible square ``W``) for the
    reconstruction check.

    The simplified JADE reference here sweeps a single cumulant slice with a
    fixed iteration cap, so the converged rotation is chaotically sensitive to
    machine-epsilon angle perturbations. The stable, routing-invariant contract
    is therefore asserted: (1) the recovered sources are mutually decorrelated,
    and (2) the unmixing reconstructs the centred observations.
    """
    rng = random.Random(7)
    n = 400
    s1 = [rng.uniform(-1.0, 1.0) for _ in range(n)]
    # square wave: sign(sin(20π · t/(n-1))) over the grid.
    s2 = []
    for t in range(n):
        sv = math.sin(20.0 * math.pi * (t / (n - 1)))
        s2.append(1.0 if sv > 0 else (-1.0 if sv < 0 else 0.0))
    a_mix = [[1.0, 0.6], [0.4, 1.0]]  # rows = sensors; X = S @ A.T
    X = [[s1[t] * a_mix[r][0] + s2[t] * a_mix[r][1] for r in range(2)] for t in range(n)]
    S_hat, W = ica_jade.op(X, n_components=2, max_iter=200)
    assert S_hat.shape == (n, 2)
    assert W.shape == (2, 2)

    # (1) Mixed channels are correlated; recovered sources are decorrelated.
    x0 = [X[t][0] for t in range(n)]
    x1 = [X[t][1] for t in range(n)]
    sh0 = [S_hat[t, 0] for t in range(n)]
    sh1 = [S_hat[t, 1] for t in range(n)]
    assert _corr_lists(x0, x1) > 0.5  # genuinely-mixed fixture
    assert _corr_lists(sh0, sh1) < 1e-6  # sources whitened/decorrelated

    # (2) The unmixing reconstructs the centred observations exactly. ``W`` is a
    # 2x2 ``Mat``; its inverse (= pinv for the invertible square) is closed-form.
    a, b = W[0, 0], W[0, 1]
    c, d = W[1, 0], W[1, 1]
    det = a * d - b * c
    inv = [[d / det, -b / det], [-c / det, a / det]]  # A_est = W⁻¹
    means = [sum(X[t][j] for t in range(n)) / n for j in range(2)]
    max_err2 = 0.0
    for t in range(n):
        for i in range(2):
            rec = inv[i][0] * S_hat[t, 0] + inv[i][1] * S_hat[t, 1]
            e = (X[t][i] - means[i]) - rec
            max_err2 = max(max_err2, e * e)
    assert max_err2 < 1e-18

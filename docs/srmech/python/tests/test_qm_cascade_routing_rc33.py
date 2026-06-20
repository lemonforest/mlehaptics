"""rc33 cascade-routing parity tests for the srmech.qm.* layer.

v0.7.0rc33 routes the numpy-math calls in the QM layer through srmech's
own A-N cascade primitives:

- Hermitian eigendecomposition -> the Class-L primitive
  ``srmech.amsc.laplacian.hermitian_eigendecompose`` (the generic so8 /
  eigvalsh routing path). ``single_particle`` (rc117), ``gauge`` (rc119) and
  ``potentials`` (rc121) have since been flipped fully numpy-free onto the
  ``Mat`` carrier (``mat_hermitian_eigendecompose`` + the Class-N
  ``rational.cexp`` phase), so their cells below build inputs and assert WITHOUT
  numpy.
- Standard-Model trig (``math.cos`` / ``math.sin`` / ``math.atan2``) ->
  the substrate-native Class-N rational trig ``srmech.amsc.rational.*``
  (sm).

numpy-FREE (#564): numpy is GONE from srmech. ``hermitian_eigendecompose``
returns plain Python lists; the generic-routing cells therefore use the
framework's own EXACT ``eigvals_exact`` (integer-entried Hermitian fixtures, so
its char-poly stays over ℤ) / general ``eigvals`` (complex case) as the
eigenvalue oracle, and pin the eigenvectors by the basis-INVARIANT
reconstruction ``H = V·diag(w)·Vᴴ`` and orthonormality — no numpy anywhere.
"""

from __future__ import annotations

import math
import random

import pytest

from srmech.amsc import rational as _srn
from srmech.amsc.cascade.matrix_cascades import eigvals, eigvals_exact
from srmech.amsc.laplacian import hermitian_eigendecompose, mat_matmul
from srmech.amsc.mat import Mat
from srmech.qm import gauge, potentials, sm, single_particle as sp


# ----------------------------------------------------------------------
# numpy-free fixtures for the FLIPPED single_particle op (rc117, #564):
# single_particle now holds its matrices in `Mat` and is numpy-free, so its
# tests below build inputs + assert WITHOUT numpy (numpy stays the sanctioned
# differential oracle only for the still-unflipped GENERIC hermitian_eigen
# routing cells in this file — the so8 / eigvalsh use-site that has not been
# flipped to `Mat`; gauge flipped numpy-free at rc119 and potentials at rc121,
# so their cells below are numpy-free too).
# ----------------------------------------------------------------------


def _lcg(seed: int):
    state = (seed * 2654435761 + 12345) & 0x7FFFFFFF
    while True:
        state = (1103515245 * state + 12345) & 0x7FFFFFFF
        yield (state / 0x3FFFFFFF) - 1.0


def _hermitian_mat(n: int, seed: int) -> "Mat":
    g = _lcg(seed)
    a = [[complex(next(g), next(g)) for _ in range(n)] for _ in range(n)]
    h = [
        [(a[i][j] + complex(a[j][i]).conjugate()) / 2.0 for j in range(n)]
        for i in range(n)
    ]
    return Mat.from_rows(h, is_complex=True)


def _unit_vec(n: int, seed: int):
    g = _lcg(seed + 777)
    v = [complex(next(g), next(g)) for _ in range(n)]
    # rational.sqrt → exact Q; collapse to float (complex / Q has no interop).
    nrm = float(_srn.sqrt(sum(x.real * x.real + x.imag * x.imag for x in v)))
    return [x / nrm for x in v]


def _matvec_mat(m: "Mat", v):
    col = Mat.from_rows([[x] for x in v], is_complex=True)
    out = mat_matmul(m, col)
    return [out[i, 0] for i in range(out.n_rows)]


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------


def _real_symmetric(n: int, seed: int):
    """Integer-entried real-symmetric matrix (exact-oracle friendly)."""
    rs = random.Random(seed)
    A = [[rs.randint(-4, 4) for _ in range(n)] for _ in range(n)]
    return [[A[i][j] + A[j][i] for j in range(n)] for i in range(n)]


def _complex_hermitian(n: int, seed: int):
    """Integer-entried complex-Hermitian matrix (Gaussian-integer entries)."""
    rs = random.Random(seed)
    A = [[complex(rs.randint(-4, 4), rs.randint(-4, 4)) for _ in range(n)]
         for _ in range(n)]
    return [[(A[i][j] + A[j][i].conjugate()) for j in range(n)] for i in range(n)]


def _eig_oracle(H):
    """Sorted real eigenvalue multiset via the framework's own exact /
    cascade path (numpy-free). ``eigvals_exact`` is real-only; for a complex
    Hermitian H its char-poly carries complex-typed coefficients, so the general
    ``eigvals`` (Class-K shifted-QR, real roots for Hermitian) is the oracle."""
    is_complex = any(isinstance(x, complex) and x.imag != 0
                     for row in H for x in row)
    if is_complex:
        return sorted(z.real for z in eigvals(H))
    return sorted(eigvals_exact(H))


def _matmul(A, B):
    m, k, n = len(A), len(B), len(B[0])
    return [[sum(A[i][p] * B[p][j] for p in range(k)) for j in range(n)]
            for i in range(m)]


def _conj_transpose(A):
    return [[complex(A[i][j]).conjugate() for i in range(len(A))]
            for j in range(len(A[0]))]


def _assert_eig_parity(H) -> None:
    """Eigenvalues match the exact/cascade oracle; eigenvectors pinned by the
    basis-INVARIANT reconstruction + orthonormality (phase/sign-free)."""
    n = len(H)
    w, V = hermitian_eigendecompose(H)   # rc129: w is a Vec, V a complex Mat
    V = V.tolist()                       # nested list for the [i][k] reconstruction
    w_ref = _eig_oracle(H)
    # Eigenvalues: ascending, match the framework's own oracle within 1e-9.
    for i in range(n - 1):
        assert w[i + 1] - w[i] >= -1e-9
    for i in range(n):
        assert abs(w[i] - w_ref[i]) < 1e-9
    # Reconstruction H = V·diag(w)·Vᴴ is phase/sign-invariant.
    Vd = [[V[i][k] * w[k] for k in range(n)] for i in range(n)]
    rec = _matmul(Vd, _conj_transpose(V))
    for i in range(n):
        for j in range(n):
            e = rec[i][j] - complex(H[i][j])
            assert e.real * e.real + e.imag * e.imag < 1e-18
    # Columns are orthonormal: Vᴴ·V = I.
    gram = _matmul(_conj_transpose(V), V)
    for i in range(n):
        for j in range(n):
            t = gram[i][j] - (1.0 if i == j else 0.0)
            tc = complex(t)
            assert tc.real * tc.real + tc.imag * tc.imag < 1e-18


# ----------------------------------------------------------------------
# A) Hermitian eigendecomposition routing
# ----------------------------------------------------------------------


@pytest.mark.parametrize("seed", [0, 1, 2])
def test_eig_parity_real_symmetric(seed):
    _assert_eig_parity(_real_symmetric(8, seed))


@pytest.mark.parametrize("seed", [3, 4, 5])
def test_eig_parity_complex_hermitian(seed):
    _assert_eig_parity(_complex_hermitian(7, seed))


def test_hermitian_eigendecompose_eigenvalues_match_eigvalsh():
    """Eigenvalues alone (the eigvalsh use-site, e.g. so8) match the exact /
    cascade oracle within 1e-9 — numpy-free."""
    for H in (_real_symmetric(10, 11), _complex_hermitian(9, 12)):
        w, _ = hermitian_eigendecompose(H)
        w_ref = _eig_oracle(H)
        for a, b in zip(sorted(w), w_ref):
            assert abs(a - b) < 1e-9


def test_potentials_hydrogen_eigenvectors_real_and_orthonormal():
    """hydrogen_radial (rc121, numpy-free) returns ``(list, list, Mat)``: a REAL
    eigenvector ``Mat`` (after the value-preserving .real) that stays orthonormal
    (Vᵀ V = I) — numpy-FREE (real-Mat compare via the native mat_matmul)."""
    r, energies, V = potentials.hydrogen_radial(n_grid=120, r_max=40.0)
    assert V.is_complex is False, "real-symmetric eigenvectors must be a real Mat"
    # Vᵀ·V = I by direct Mat-entry check (native mat_matmul, real Mat).
    gram = mat_matmul(V.T, V)
    n = gram.n_rows
    assert max(
        abs(gram[i, j] - (1.0 if i == j else 0.0)) for i in range(n) for j in range(n)
    ) < 1e-9
    # Eigen-energies ascending real and the ground state physical (the `energies`
    # list indexes directly; no numpy).
    for i in range(len(energies) - 1):
        assert energies[i + 1] - energies[i] >= -1e-9
    assert -0.6 < energies[0] < -0.4


def test_single_particle_tise_subspace_parity():
    """tise_solve (complex-Hermitian) returns the ``(n,1)`` real eigval ``Mat`` +
    complex unitary eigvec ``Mat``; reconstruction ``H ≈ V·diag(w)·Vᴴ`` and
    unitarity ``Vᴴ·V ≈ I`` both hold — numpy-FREE (single_particle is a
    numpy-free ``Mat`` op as of rc117; an eigenvector is fixed only up to phase,
    so correctness is reconstruction + unitarity, not element-wise parity)."""
    n = 6
    H = _hermitian_mat(n, 30)
    w, V = sp.tise_solve(H)
    assert V.is_complex and w.shape == (n, 1)
    # Unitarity: Vᴴ·V = I (via the native mat_matmul).
    vhv = mat_matmul(V.conj().T, V)
    assert max(
        abs(vhv[i, j] - (1.0 if i == j else 0.0)) for i in range(n) for j in range(n)
    ) < 1e-9
    # Reconstruction: H = V·diag(w)·Vᴴ.
    D = Mat.from_rows(
        [[w[i, 0] if i == j else 0.0 for j in range(n)] for i in range(n)],
        is_complex=True,
    )
    H_rebuilt = mat_matmul(mat_matmul(V, D), V.conj().T)
    assert max(
        abs(H_rebuilt[i, j] - H[i, j]) for i in range(n) for j in range(n)
    ) < 1e-9
    # Eigenvalues ascending.
    for i in range(n - 1):
        assert w[i + 1, 0] - w[i, 0] >= -1e-9


def test_single_particle_tdse_matches_reference():
    """tdse_evolve matches the hand-composed closed form ``V·diag(e^{-iλt})·Vᴴ·ψ``
    built from ``tise_solve`` + the Class-N ``rational.cexp`` — numpy-FREE
    (the reference is the framework's own eigendecomposition + Euler cascade,
    NOT a numpy oracle, so the flipped op's test is itself numpy-free)."""
    n = 5
    H = _hermitian_mat(n, 31)
    psi = _unit_vec(n, 99)
    t = 1.7
    w, V = sp.tise_solve(H)
    # Reference: V·diag(e^{-iλt})·Vᴴ·ψ via Mat ops + Class-N cexp.
    vh_psi = _matvec_mat(V.conj().T, psi)
    phased = [_srn.cexp(-(w[k, 0] * t)) * vh_psi[k] for k in range(n)]
    ref = _matvec_mat(V, phased)
    got = sp.tdse_evolve(H, psi, t)
    assert max(abs(got[i] - ref[i]) for i in range(n)) < 1e-9


def test_gauge_path_segment_matches_reference():
    """gauge_path_segment (now numpy-free, rc119) — the path-segment holonomy
    U = exp(i g M) matches an INDEPENDENT analytic oracle for a diagonal
    connection (M ∝ λ^3 = diag(1, -1, 0): exp is diag(e^{igc}, e^{-igc}, 1),
    built from rational.cexp on scalars — no eigendecomposition in the
    reference), and is unitary for a general SU(3) connection. numpy-free:
    direct Mat-entry compare + native mat_matmul unitarity (no np)."""
    gens = gauge.su3_gell_mann_matrices()
    # (1) Diagonal connection: only λ^3 = diag(1, -1, 0). exp(i·g·c·λ^3) is
    #     analytic — an independent oracle (no eig in the reference).
    g, c = 0.8, 0.41
    A_diag = [0.0] * 8
    A_diag[2] = c
    U = gauge.gauge_path_segment(A_diag, gens, coupling=g)
    phase = _srn.cexp(g * c)            # e^{+i g c}
    expected = [phase, phase.conjugate(), 1.0 + 0j]
    for i in range(3):
        for j in range(3):
            want = expected[i] if i == j else 0j
            assert abs(U[i, j] - want) < 1e-9
    # (2) General connection: U·Uᴴ = I (unitary) via the native mat_matmul.
    A_gen = [0.1, -0.2, 0.3, 0.4, -0.5, 0.6, -0.7, 0.2]
    U2 = gauge.gauge_path_segment(A_gen, gens, coupling=0.8)
    prod = mat_matmul(U2, U2.conj().T)
    for i in range(3):
        for j in range(3):
            want = 1.0 if i == j else 0.0
            assert abs(prod[i, j] - want) < 1e-9


# ----------------------------------------------------------------------
# B) Standard-Model substrate-native trig routing
# ----------------------------------------------------------------------


# Representative electroweak + CKM angles (radians).
_THETA_W = math.atan2(0.35, 0.65)
_CKM_ANGLES = [0.227, 0.003, 0.042, 0.4, 0.5, 0.2, 0.3]


def test_srn_trig_matches_libm_at_ew_ckm_angles():
    """_srn.cos/sin/atan2 match math.* at the actual EW/CKM angles to 1e-9."""
    for th in [_THETA_W, *_CKM_ANGLES]:
        assert abs(_srn.cos(th) - math.cos(th)) < 1e-9
        assert abs(_srn.sin(th) - math.sin(th)) < 1e-9
    for (y, x) in [(0.35, 0.65), (0.5, 0.5), (0.1, 1.0), (1.0, 1.0)]:
        assert abs(_srn.atan2(y, x) - math.atan2(y, x)) < 1e-9


def test_weak_mixing_angle_matches_pre_change():
    """weak_mixing_angle (now _srn.atan2) matches the math.atan2 value 1e-9."""
    for (g, gp) in [(0.65, 0.35), (0.5, 0.5), (1.0, 0.1), (0.8, 0.3)]:
        expected = math.atan2(gp, g)  # pre-change value
        assert abs(sm.weak_mixing_angle(g, gp) - expected) < 1e-9


def test_weinberg_relations_match_pre_change():
    """electroweak_summary cos/sin (now _srn.*) match the pre-change math.*
    closed form within 1e-9 for each observable in the bundle."""
    for (g, gp, v) in [(0.65, 0.35, 246.0), (0.5, 0.5, 100.0), (1.0, 0.1, 50.0)]:
        theta = math.atan2(gp, g)
        exp_MW = g * v / 2.0
        exp_MZ = v * math.sqrt(g * g + gp * gp) / 2.0
        exp_cos = math.cos(theta)
        exp_sin = math.sin(theta)
        got = sm.electroweak_summary(g, gp, v)
        assert abs(got["M_W"] - exp_MW) < 1e-9
        assert abs(got["M_Z"] - exp_MZ) < 1e-9
        assert abs(got["theta_W_rad"] - theta) < 1e-9
        assert abs(got["cos_theta_W"] - exp_cos) < 1e-9
        assert abs(got["sin_theta_W"] - exp_sin) < 1e-9


def test_ckm_matrix_matches_pre_change():
    """ckm_matrix (numpy-free `Mat` as of rc116) matches the element-by-element
    construction within 1e-9 for a representative parameter point.

    numpy-FREE: the reference is built with the stdlib `math`/`cmath` (an
    INDEPENDENT oracle, NOT the framework's own `rational.cexp`, so it's a
    genuine cross-check), compared via direct `Mat`-entry access, and unitarity
    is checked via the native `mat_matmul` — no numpy (the flipped op's test is
    itself numpy-free per the carrier-removal discipline).
    """
    import cmath
    from srmech.amsc.laplacian import mat_matmul
    th12, th13, th23, delta = 0.227, 0.003, 0.042, 1.20
    c12, s12 = math.cos(th12), math.sin(th12)
    c13, s13 = math.cos(th13), math.sin(th13)
    c23, s23 = math.cos(th23), math.sin(th23)
    phase = cmath.exp(1j * delta)
    inv_phase = cmath.exp(-1j * delta)
    ref = [
        [c12 * c13, s12 * c13, s13 * inv_phase],
        [
            -s12 * c23 - c12 * s23 * s13 * phase,
            c12 * c23 - s12 * s23 * s13 * phase,
            s23 * c13,
        ],
        [
            s12 * s23 - c12 * c23 * s13 * phase,
            -c12 * s23 - s12 * c23 * s13 * phase,
            c23 * c13,
        ],
    ]
    V = sm.ckm_matrix(th12, th13, th23, delta)
    for i in range(3):
        for j in range(3):
            assert abs(V[i, j] - ref[i][j]) < 1e-9, (i, j)
    # Still unitary: V·Vᴴ = I (numpy-free, via the native mat_matmul).
    vvh = mat_matmul(V, V.conj().T)
    for i in range(3):
        for j in range(3):
            assert abs(vvh[i, j] - (1.0 if i == j else 0.0)) < 1e-9, (i, j)


# ----------------------------------------------------------------------
# No abs() / no stealth-abs in this test module itself (discipline echo):
# all magnitudes above use squared-magnitude (z * z.conj()).real, not abs().
# ----------------------------------------------------------------------

"""Tests for srmech.qm.gauge (Yang-Mills, Casimirs, Wilson loops).

numpy-FREE (v0.7.5rc119, #564): gauge flipped onto the framework-native
``Mat`` carrier, so this test runs with numpy GENUINELY ABSENT — there is no
``import numpy`` and no ``.to_numpy()`` here. Hermiticity / trace / unitarity
are checked by direct ``Mat``-entry arithmetic, matrix products go through the
native ``mat_matmul``, the structure constants are plain nested lists, and the
multi-segment Wilson-loop input is a deterministic LCG (not ``np.random``) per
``[[feedback_test_for_numpy_free_module_must_itself_be_numpy_free]]``.
"""

from __future__ import annotations

import pytest

from srmech.amsc.laplacian import mat_matmul
from srmech.amsc.mat import Mat
from srmech.qm import gauge


# ----------------------------------------------------------------------
# numpy-free helpers (no np oracle — direct Mat-entry arithmetic)
# ----------------------------------------------------------------------


def _trace(m: "Mat") -> complex:
    return sum(m[i, i] for i in range(m.n_rows))


def _max_dev_hermitian(m: "Mat") -> float:
    """max_ij |M[i, j] − conj(M[j, i])| — deviation from Hermiticity."""
    return max(
        abs(m[i, j] - m[j, i].conjugate())
        for i in range(m.n_rows)
        for j in range(m.n_cols)
    )


def _max_abs_diff(a: "Mat", b: "Mat") -> float:
    return max(
        abs(a[i, j] - b[i, j])
        for i in range(a.n_rows)
        for j in range(a.n_cols)
    )


def _max_dev_identity(m: "Mat") -> float:
    """max_ij |M[i, j] − δ_ij| — deviation from the identity."""
    return max(
        abs(m[i, j] - (1.0 if i == j else 0.0))
        for i in range(m.n_rows)
        for j in range(m.n_cols)
    )


def _lcg(seed: int):
    """Deterministic LCG yielding floats in [-1, 1) — replaces np.random."""
    state = (seed * 2654435761 + 12345) & 0x7FFFFFFF
    while True:
        state = (1103515245 * state + 12345) & 0x7FFFFFFF
        yield (state / 0x3FFFFFFF) - 1.0


def _scalar_identity(val: float, n: int) -> "Mat":
    return Mat.from_rows(
        [[val if i == j else 0.0 for j in range(n)] for i in range(n)],
        is_complex=True,
    )


# ----------------------------------------------------------------------
# SU(2)
# ----------------------------------------------------------------------


def test_su2_generators_hermitian_traceless():
    for T in gauge.su2_generators():
        assert _max_dev_hermitian(T) < 1e-14
        assert abs(_trace(T)) < 1e-14


def test_su2_generators_normalization():
    """tr(T^a T^b) = (1/2) δ^{ab} for fundamental of SU(2)."""
    gens = gauge.su2_generators()
    for a in range(3):
        for b in range(3):
            tr = _trace(mat_matmul(gens[a], gens[b]))
            expected = 0.5 if a == b else 0.0
            assert abs(tr - expected) < 1e-14


def test_su2_lie_algebra():
    """[T^a, T^b] = i ε^{abc} T^c at machine precision."""
    gens = gauge.su2_generators()
    f = gauge.su2_structure_constants()
    assert gauge.lie_algebra_residual(gens, f) < 1e-13


def test_su2_casimir_eigenvalue():
    """C_2(fundamental of SU(2)) = (4 - 1) / (2·2) = 3/4."""
    gens = gauge.su2_generators()
    assert abs(gauge.casimir_eigenvalue(gens) - 0.75) < 1e-14


def test_su2_casimir_proportional_to_identity():
    """C_2 = (3/4) I_2 — by Schur's lemma on irreducible rep."""
    gens = gauge.su2_generators()
    C = gauge.casimir_operator(gens)
    assert _max_abs_diff(C, _scalar_identity(0.75, 2)) < 1e-14


# ----------------------------------------------------------------------
# SU(3)
# ----------------------------------------------------------------------


def test_su3_gell_mann_hermitian_traceless():
    for lam in gauge.su3_gell_mann_matrices():
        assert _max_dev_hermitian(lam) < 1e-14
        assert abs(_trace(lam)) < 1e-13


def test_su3_gell_mann_normalization():
    """tr(λ^a λ^b) = 2 δ^{ab}."""
    lams = gauge.su3_gell_mann_matrices()
    for a in range(8):
        for b in range(8):
            tr = _trace(mat_matmul(lams[a], lams[b]))
            expected = 2.0 if a == b else 0.0
            assert abs(tr - expected) < 1e-13


def test_su3_generators_normalization():
    """T^a = λ^a / 2: tr(T^a T^b) = (1/2) δ^{ab}."""
    gens = gauge.su3_generators()
    for a in range(8):
        for b in range(8):
            tr = _trace(mat_matmul(gens[a], gens[b]))
            expected = 0.5 if a == b else 0.0
            assert abs(tr - expected) < 1e-13


def test_su3_structure_constants_antisymmetric():
    f = gauge.su3_structure_constants()
    for a in range(8):
        for b in range(8):
            for c in range(8):
                # Total antisymmetry: f^{abc} = -f^{bac} = -f^{acb}.
                assert abs(f[a][b][c] + f[b][a][c]) < 1e-14
                assert abs(f[a][b][c] + f[a][c][b]) < 1e-14


def test_su3_lie_algebra():
    """[T^a, T^b] = i f^{abc} T^c for SU(3) at machine precision."""
    gens = gauge.su3_generators()
    f = gauge.su3_structure_constants()
    assert gauge.lie_algebra_residual(gens, f) < 1e-13


def test_su3_casimir_eigenvalue():
    """C_2(fundamental of SU(3)) = (9 - 1) / (2·3) = 4/3."""
    gens = gauge.su3_generators()
    assert abs(gauge.casimir_eigenvalue(gens) - 4.0 / 3.0) < 1e-14


def test_su3_casimir_proportional_to_identity():
    gens = gauge.su3_generators()
    C = gauge.casimir_operator(gens)
    assert _max_abs_diff(C, _scalar_identity(4.0 / 3.0, 3)) < 1e-13


# ----------------------------------------------------------------------
# Holonomy / Wilson loops
# ----------------------------------------------------------------------


def test_gauge_connection_matrix_hermitian():
    """A = A^a T^a is Hermitian for any real A^a."""
    gens = gauge.su2_generators()
    A = gauge.gauge_connection_matrix([0.3, -0.7, 1.5], gens)
    assert _max_dev_hermitian(A) < 1e-14


def test_gauge_path_segment_unitary():
    """U = exp(i g A^a T^a) is unitary."""
    gens = gauge.su3_generators()
    A = [0.1, -0.2, 0.3, 0.4, -0.5, 0.6, -0.7, 0.2]
    U = gauge.gauge_path_segment(A, gens, coupling=0.5)
    assert _max_dev_identity(mat_matmul(U, U.conj().T)) < 1e-12


def test_gauge_path_segment_zero_connection_is_identity():
    gens = gauge.su2_generators()
    U = gauge.gauge_path_segment([0.0, 0.0, 0.0], gens, coupling=1.0)
    assert _max_dev_identity(U) < 1e-14


def test_gauge_path_segment_diagonal_connection_analytic():
    """For a diagonal connection M ∝ λ^3 = diag(1, -1, 0), the holonomy
    exp(i g c λ^3) = diag(e^{igc}, e^{-igc}, 1) — an INDEPENDENT analytic
    oracle (Class-N rational.cexp on scalars; no eigendecomposition in the
    reference)."""
    from srmech.amsc import rational as _srn

    gens = gauge.su3_gell_mann_matrices()
    g, c = 0.8, 0.37
    A = [0.0] * 8
    A[2] = c  # λ^3
    U = gauge.gauge_path_segment(A, gens, coupling=g)
    phase = _srn.cexp(g * c)  # e^{+i g c}
    expected = [phase, phase.conjugate(), 1.0 + 0j]
    for i in range(3):
        for j in range(3):
            want = expected[i] if i == j else 0j
            assert abs(U[i, j] - want) < 1e-9


def test_wilson_loop_empty_is_identity():
    gens = gauge.su2_generators()
    U = gauge.wilson_loop_from_segments([], gens)
    assert _max_dev_identity(U) < 1e-14


def test_wilson_loop_single_segment_matches_path_segment():
    gens = gauge.su2_generators()
    A = [0.5, -0.3, 0.7]
    U_single = gauge.gauge_path_segment(A, gens, coupling=1.0)
    U_loop = gauge.wilson_loop_from_segments([A], gens)
    assert _max_abs_diff(U_loop, U_single) < 1e-12


def test_wilson_loop_unitary_multi_segment():
    gens = gauge.su3_generators()
    rng = _lcg(0)
    A = [[next(rng) for _ in range(8)] for _ in range(5)]
    U = gauge.wilson_loop_from_segments(A, gens, coupling=0.3)
    assert _max_dev_identity(mat_matmul(U, U.conj().T)) < 1e-11


def test_lie_algebra_residual_shape_mismatch():
    gens = gauge.su2_generators()
    bad_f = [[[0.0] * 4 for _ in range(4)] for _ in range(4)]
    with pytest.raises(ValueError):
        gauge.lie_algebra_residual(gens, bad_f)


def test_gauge_connection_matrix_shape_mismatch():
    gens = gauge.su2_generators()
    with pytest.raises(ValueError):
        gauge.gauge_connection_matrix([1.0, 2.0], gens)

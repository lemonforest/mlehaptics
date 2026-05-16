"""Tests for srmech.qm.gauge (Yang-Mills, Casimirs, Wilson loops)."""

from __future__ import annotations

import numpy as np
import pytest

from srmech.qm import gauge


# ----------------------------------------------------------------------
# SU(2)
# ----------------------------------------------------------------------


def test_su2_generators_hermitian_traceless():
    for T in gauge.su2_generators():
        np.testing.assert_allclose(T, T.conj().T, atol=1e-14)
        assert abs(np.trace(T)) < 1e-14


def test_su2_generators_normalization():
    """tr(T^a T^b) = (1/2) δ^{ab} for fundamental of SU(2)."""
    gens = gauge.su2_generators()
    for a in range(3):
        for b in range(3):
            tr = np.trace(gens[a] @ gens[b])
            expected = 0.5 if a == b else 0.0
            assert abs(tr - expected) < 1e-14


def test_su2_lie_algebra():
    """[T^a, T^b] = i ε^{abc} T^c at machine precision."""
    gens = gauge.su2_generators()
    f = gauge.su2_structure_constants()
    residual = gauge.lie_algebra_residual(gens, f)
    assert residual < 1e-13


def test_su2_casimir_eigenvalue():
    """C_2(fundamental of SU(2)) = (4 - 1) / (2·2) = 3/4."""
    gens = gauge.su2_generators()
    c2 = gauge.casimir_eigenvalue(gens)
    assert abs(c2 - 0.75) < 1e-14


def test_su2_casimir_proportional_to_identity():
    """C_2 = (3/4) I_2 — by Schur's lemma on irreducible rep."""
    gens = gauge.su2_generators()
    C = gauge.casimir_operator(gens)
    expected = 0.75 * np.eye(2, dtype=complex)
    np.testing.assert_allclose(C, expected, atol=1e-14)


# ----------------------------------------------------------------------
# SU(3)
# ----------------------------------------------------------------------


def test_su3_gell_mann_hermitian_traceless():
    for lam in gauge.su3_gell_mann_matrices():
        np.testing.assert_allclose(lam, lam.conj().T, atol=1e-14)
        assert abs(np.trace(lam)) < 1e-13


def test_su3_gell_mann_normalization():
    """tr(λ^a λ^b) = 2 δ^{ab}."""
    lams = gauge.su3_gell_mann_matrices()
    for a in range(8):
        for b in range(8):
            tr = np.trace(lams[a] @ lams[b])
            expected = 2.0 if a == b else 0.0
            assert abs(tr - expected) < 1e-13


def test_su3_generators_normalization():
    """T^a = λ^a / 2: tr(T^a T^b) = (1/2) δ^{ab}."""
    gens = gauge.su3_generators()
    for a in range(8):
        for b in range(8):
            tr = np.trace(gens[a] @ gens[b])
            expected = 0.5 if a == b else 0.0
            assert abs(tr - expected) < 1e-13


def test_su3_structure_constants_antisymmetric():
    f = gauge.su3_structure_constants()
    for a in range(8):
        for b in range(8):
            for c in range(8):
                # Total antisymmetry: f^{abc} = -f^{bac} = -f^{acb}.
                assert abs(f[a, b, c] + f[b, a, c]) < 1e-14
                assert abs(f[a, b, c] + f[a, c, b]) < 1e-14


def test_su3_lie_algebra():
    """[T^a, T^b] = i f^{abc} T^c for SU(3) at machine precision."""
    gens = gauge.su3_generators()
    f = gauge.su3_structure_constants()
    residual = gauge.lie_algebra_residual(gens, f)
    assert residual < 1e-13


def test_su3_casimir_eigenvalue():
    """C_2(fundamental of SU(3)) = (9 - 1) / (2·3) = 4/3."""
    gens = gauge.su3_generators()
    c2 = gauge.casimir_eigenvalue(gens)
    assert abs(c2 - 4.0 / 3.0) < 1e-14


def test_su3_casimir_proportional_to_identity():
    gens = gauge.su3_generators()
    C = gauge.casimir_operator(gens)
    expected = (4.0 / 3.0) * np.eye(3, dtype=complex)
    np.testing.assert_allclose(C, expected, atol=1e-13)


# ----------------------------------------------------------------------
# Holonomy / Wilson loops
# ----------------------------------------------------------------------


def test_gauge_connection_matrix_hermitian():
    """A = A^a T^a is Hermitian for any real A^a."""
    gens = gauge.su2_generators()
    A_comp = np.array([0.3, -0.7, 1.5])
    A = gauge.gauge_connection_matrix(A_comp, gens)
    np.testing.assert_allclose(A, A.conj().T, atol=1e-14)


def test_gauge_path_segment_unitary():
    """U = exp(i g A^a T^a) is unitary."""
    gens = gauge.su3_generators()
    A_comp = np.array([0.1, -0.2, 0.3, 0.4, -0.5, 0.6, -0.7, 0.2])
    U = gauge.gauge_path_segment(A_comp, gens, coupling=0.5)
    np.testing.assert_allclose(U @ U.conj().T, np.eye(3), atol=1e-12)


def test_gauge_path_segment_zero_connection_is_identity():
    gens = gauge.su2_generators()
    U = gauge.gauge_path_segment(np.zeros(3), gens, coupling=1.0)
    np.testing.assert_allclose(U, np.eye(2), atol=1e-14)


def test_wilson_loop_empty_is_identity():
    gens = gauge.su2_generators()
    U = gauge.wilson_loop_from_segments(np.zeros((0, 3)), gens)
    np.testing.assert_allclose(U, np.eye(2), atol=1e-14)


def test_wilson_loop_single_segment_matches_path_segment():
    gens = gauge.su2_generators()
    A_comp = np.array([0.5, -0.3, 0.7])
    U_single = gauge.gauge_path_segment(A_comp, gens, coupling=1.0)
    U_loop = gauge.wilson_loop_from_segments(A_comp.reshape(1, 3), gens)
    np.testing.assert_allclose(U_loop, U_single, atol=1e-12)


def test_wilson_loop_unitary_multi_segment():
    gens = gauge.su3_generators()
    rng = np.random.default_rng(0)
    A = rng.standard_normal((5, 8))
    U = gauge.wilson_loop_from_segments(A, gens, coupling=0.3)
    np.testing.assert_allclose(U @ U.conj().T, np.eye(3), atol=1e-11)


def test_lie_algebra_residual_shape_mismatch():
    gens = gauge.su2_generators()
    bad_f = np.zeros((4, 4, 4))
    with pytest.raises(ValueError):
        gauge.lie_algebra_residual(gens, bad_f)


def test_gauge_connection_matrix_shape_mismatch():
    gens = gauge.su2_generators()
    with pytest.raises(ValueError):
        gauge.gauge_connection_matrix(np.array([1.0, 2.0]), gens)

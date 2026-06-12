"""Tests for srmech.qm.relativistic (Dirac γ-matrices, Weyl, Majorana, KG).

numpy-FREE (v0.7.5rc118, #564): the γ-matrices and derived 4×4 operators are
numpy-free :class:`~srmech.amsc.mat.Mat`; these tests use **no numpy** — every
assertion is a canonical Clifford-algebra / chirality / charge-conjugation
identity checked via the native :func:`~srmech.amsc.laplacian.mat_matmul` /
:func:`~srmech.amsc.laplacian.mat_solve` and direct ``Mat``-entry comparison
(numpy is never a validation reference per
``[[feedback_test_for_numpy_free_module_must_itself_be_numpy_free]]``).
"""

from __future__ import annotations

import pytest

from srmech.amsc.laplacian import mat_matmul, mat_norm, mat_solve
from srmech.amsc.mat import Mat
from srmech.qm import relativistic as rel


# ----------------------------------------------------------------------
# numpy-free Mat helpers
# ----------------------------------------------------------------------


def _eye4() -> "Mat":
    return Mat.from_rows(
        [[1.0 if i == j else 0.0 for j in range(4)] for i in range(4)],
        is_complex=True,
    )


def _trace(m: "Mat") -> complex:
    return sum(complex(m[i, i]) for i in range(m.n_rows))


def _mat_add(a: "Mat", b: "Mat") -> "Mat":
    return Mat.from_rows(
        [[a[i, j] + b[i, j] for j in range(a.n_cols)] for i in range(a.n_rows)],
        is_complex=True,
    )


def _max_abs_diff(a: "Mat", b: "Mat") -> float:
    return max(
        abs(a[i, j] - b[i, j]) for i in range(a.n_rows) for j in range(a.n_cols)
    )


def _max_dev_identity(m: "Mat") -> float:
    return max(
        abs(m[i, j] - (1.0 if i == j else 0.0))
        for i in range(m.n_rows)
        for j in range(m.n_cols)
    )


# ----------------------------------------------------------------------
# γ-matrix Clifford algebra
# ----------------------------------------------------------------------


def test_clifford_residuals_machine_precision():
    """{γ^μ, γ^ν} = 2 η^{μν} I_4; γ_5² = I; {γ_5, γ^μ} = 0 (numpy-free)."""
    max_clifford, g5_sq, g5_anti = rel.clifford_residuals()
    assert max_clifford < 1e-13
    assert g5_sq < 1e-13
    assert g5_anti < 1e-13


def test_gamma_matrices_traceless():
    """tr(γ^μ) = 0 for all μ (direct Mat-diagonal sum, numpy-free)."""
    for g in rel.gamma_matrices():
        assert abs(_trace(g)) < 1e-13


def test_gamma_5_squared_identity():
    """γ_5² = I_4."""
    g5 = rel.gamma_5()
    assert _max_dev_identity(mat_matmul(g5, g5)) < 1e-13


def test_gamma_5_hermitian():
    """γ_5† = γ_5 (Mat.conj().T compare, numpy-free)."""
    g5 = rel.gamma_5()
    assert _max_abs_diff(g5, g5.conj().T) < 1e-13


# ----------------------------------------------------------------------
# Weyl chirality projectors
# ----------------------------------------------------------------------


def test_weyl_projectors_sum_to_identity():
    """P_L + P_R = I."""
    PL = rel.weyl_left_projector()
    PR = rel.weyl_right_projector()
    assert _max_dev_identity(_mat_add(PL, PR)) < 1e-13


def test_weyl_projectors_idempotent():
    """P_L² = P_L; P_R² = P_R."""
    PL = rel.weyl_left_projector()
    PR = rel.weyl_right_projector()
    assert _max_abs_diff(mat_matmul(PL, PL), PL) < 1e-13
    assert _max_abs_diff(mat_matmul(PR, PR), PR) < 1e-13


def test_weyl_projectors_orthogonal():
    """P_L P_R = 0 (via the native mat_matmul + mat_norm)."""
    PL = rel.weyl_left_projector()
    PR = rel.weyl_right_projector()
    assert mat_norm(mat_matmul(PL, PR)) < 1e-13


# ----------------------------------------------------------------------
# Charge conjugation
# ----------------------------------------------------------------------


def test_charge_conjugation_matrix_shape():
    C = rel.charge_conjugation_matrix()
    assert C.shape == (4, 4)


def test_charge_conjugation_antisymmetric_property():
    """C γ^μ C^{-1} = -(γ^μ)^T (Peskin-Schroeder eq A.27 hallmark).

    numpy-FREE: ``C^{-1}`` via the native :func:`mat_solve` (``C·X = I``),
    the products via :func:`mat_matmul`, ``-(γ^μ)^T`` element-wise."""
    C = rel.charge_conjugation_matrix()
    C_inv = mat_solve(C, _eye4())
    for g in rel.gamma_matrices():
        lhs = mat_matmul(mat_matmul(C, g), C_inv)
        gt = g.T
        rhs = Mat.from_rows(
            [[-gt[i, j] for j in range(4)] for i in range(4)], is_complex=True
        )
        assert _max_abs_diff(lhs, rhs) < 1e-12


# ----------------------------------------------------------------------
# Klein-Gordon dispersion
# ----------------------------------------------------------------------


def test_klein_gordon_dispersion_at_rest():
    """At |k| = 0: E = m."""
    E = rel.klein_gordon_dispersion([0.0, 0.0, 0.0], m=2.5)
    assert abs(E - 2.5) < 1e-14


def test_klein_gordon_dispersion_massless():
    """For m = 0: E = |k|."""
    E = rel.klein_gordon_dispersion([3.0, 4.0, 0.0], m=0.0)  # |k| = 5
    assert abs(E - 5.0) < 1e-13


def test_klein_gordon_dispersion_relativistic():
    """E² = |k|² + m²."""
    k = [1.0, 1.0, 1.0]
    m = 2.0
    E = rel.klein_gordon_dispersion(k, m)
    k_dot = sum(x * x for x in k)
    assert abs(E * E - k_dot - m * m) < 1e-13


def test_klein_gordon_dispersion_negative_mass_rejected():
    with pytest.raises(ValueError):
        rel.klein_gordon_dispersion([0.0, 0.0, 0.0], m=-1.0)


# ----------------------------------------------------------------------
# Dirac operator (momentum space)
# ----------------------------------------------------------------------


def test_dirac_operator_at_rest():
    """At k = (m, 0, 0, 0) (on-shell rest): D = diag(0, 0, -2m, -2m).

    At rest ``D = m·γ^0 − m·I = diag(0, 0, -2m, -2m)`` is diagonal, so the
    diagonal entries ARE the eigenvalues — checked directly, numpy-free."""
    m = 1.5
    D = rel.dirac_operator_momentum_space([m, 0.0, 0.0, 0.0], m)
    expected_diag = [0.0, 0.0, -2 * m, -2 * m]
    for i in range(4):
        for j in range(4):
            want = expected_diag[i] if i == j else 0.0
            assert abs(D[i, j] - want) < 1e-13, (i, j, D[i, j])


def test_dirac_operator_on_shell_annihilates_positive_energy_spinor():
    """For on-shell positive-frequency u(p), (γ^μ p_μ - m) u = 0.

    In the rest frame Dirac basis, positive-energy spinors are e_0 and e_1, so
    ``D u`` is column 0 / column 1 of ``D`` — both zero, checked directly."""
    m = 1.0
    D = rel.dirac_operator_momentum_space([m, 0.0, 0.0, 0.0], m)  # rest frame
    assert max(abs(D[i, 0]) for i in range(4)) < 1e-13  # D·e_0
    assert max(abs(D[i, 1]) for i in range(4)) < 1e-13  # D·e_1


def test_four_momentum_squared_mostly_minus():
    """k² = E² - |k|² (mostly-minus)."""
    k2 = rel.four_momentum_squared([3.0, 1.0, 2.0, 0.0])
    assert abs(k2 - (9.0 - 1.0 - 4.0 - 0.0)) < 1e-14


def test_dirac_operator_wrong_shape():
    with pytest.raises(ValueError):
        rel.dirac_operator_momentum_space([1.0, 0.0, 0.0], m=1.0)

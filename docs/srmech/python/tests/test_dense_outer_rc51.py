"""dense_outer — the rank-1 outer-product cascade (numpy-removal; rc51).

An outer product ``a ⊗ b`` is the ``k = 1`` case of a matrix product (``a`` a
column, ``b`` a row), so ``dense_outer_*`` is exactly the matmul cascade on the
reshaped pair — each entry is a single multiply ``aᵢ·bⱼ`` (NO conjugate). This
lets the genuine outer-product callsites (qm.propagators' ``kᵘkᵛ`` momentum
tensor, qm.single_particle's ``|ψ⟩⟨ψ|`` density matrix) leave numpy entirely.

Post-#564 numpy is GONE from srmech; rc129 restores the numpy-carrier FORMAT:
``dense_outer_*`` take plain Python sequences and return a numpy-free ``Mat``
(``.shape`` + ``m[i, j]``), NOT a bare ``list[list[...]]``. These tests pin the
closed-form ``[[aᵢbⱼ]]`` value (hand-computed oracle), the no-conjugate
contract, shape / empty handling, the registration, and that the routed qm
surfaces still compute their tensors correctly (as numpy-free ``Mat`` outputs).
"""
from __future__ import annotations

import math

import pytest

from srmech.amsc import laplacian
from srmech.amsc.mat import Mat
from srmech.amsc.laplacian import dense_outer_complex, dense_outer_real


def _expected_outer(a, b):
    """Reference rank-1 outer product [[aᵢ·bⱼ]] (plain bilinear, no conj)."""
    return [[a[i] * b[j] for j in range(len(b))] for i in range(len(a))]


def _assert_outer_equal(got, exp, tol=0.0):
    got = got.tolist() if hasattr(got, "tolist") else got   # rc129: Mat → nested
    assert len(got) == len(exp)
    for i in range(len(exp)):
        assert len(got[i]) == len(exp[i])
        for j in range(len(exp[i])):
            if tol:
                assert abs(got[i][j] - exp[i][j]) <= tol
            else:
                assert got[i][j] == exp[i][j]


def test_outer_real_closed_form():
    a = [1.0, -2.0, 3.5, 0.0]
    b = [4.0, 0.5, -1.0]
    out = dense_outer_real(a, b)
    assert isinstance(out, Mat) and out.shape == (4, 3)   # rc129: real Mat
    _assert_outer_equal(out, _expected_outer(a, b))
    # real peer drops the zero imaginary part — entries are plain floats.
    for row in out.tolist():
        for v in row:
            assert isinstance(v, float)


def test_outer_complex_closed_form():
    a = [1 + 2j, 3 - 1j, 0 + 0j]
    b = [2 - 1j, 0 + 4j]
    out = dense_outer_complex(a, b)
    assert isinstance(out, Mat) and out.shape == (3, 2)   # rc129: complex Mat
    _assert_outer_equal(out, _expected_outer(a, b))


def test_outer_does_not_conjugate_b():
    # dense_outer takes the plain bilinear aᵢ·bⱼ (NO conj); the |ψ⟩⟨ψ| density
    # matrix is the caller passing b = conj(ψ) explicitly.
    psi = [1 + 1j, 2 - 3j]
    psi_conj = [z.conjugate() for z in psi]
    rho = dense_outer_complex(psi, psi_conj)
    _assert_outer_equal(rho, _expected_outer(psi, psi_conj))
    # Hermitian: rho[i, j] == conj(rho[j, i]) (rc129: Mat carrier, m[i, j]).
    for i in range(2):
        for j in range(2):
            assert abs(rho[i, j] - rho[j, i].conjugate()) < 1e-12
    # trace == ⟨ψ|ψ⟩ = Σ conj(ψ)·ψ.
    trace = rho[0, 0] + rho[1, 1]
    inner = sum(z.conjugate() * z for z in psi)
    assert abs(trace - inner) < 1e-12


def test_outer_real_rides_complex_kernel_drops_zero_imag():
    a = [2.0, 5.0]
    out = dense_outer_real(a, a)
    for row in out.tolist():
        for v in row:
            assert isinstance(v, float)       # real peer returns floats, imag dropped
    _assert_outer_equal(out, _expected_outer(a, a))


def test_outer_empty_inputs_safe():
    out_r = dense_outer_real([], [1.0, 2.0])
    assert isinstance(out_r, Mat) and out_r.shape == (0, 2)   # (0, 2): no rows
    out_c = dense_outer_complex([1j], [])
    assert isinstance(out_c, Mat) and out_c.shape == (1, 0)   # (1, 0): one empty row


# ── registration: __all__ + LAPLACIAN_OPS + ToolEntries ──────────────────────

def test_dense_outer_in_all_and_laplacian_ops():
    for name in ("dense_outer_complex", "dense_outer_real"):
        assert name in laplacian.__all__
        assert name in laplacian.LAPLACIAN_OPS


def test_dense_outer_tool_entries_registered():
    from srmech.amsc.tool_schema import get_tool_schema

    names = {t.name for t in get_tool_schema().tools}
    assert "srmech.amsc.laplacian.dense_outer_complex" in names
    assert "srmech.amsc.laplacian.dense_outer_real" in names


# ── the routed qm callsites still compute correctly (numpy-free Mat) ──────────

def test_propagators_momentum_tensor_routed():
    from srmech.amsc.mat import Mat
    from srmech.qm.propagators import feynman_photon_propagator
    # general covariant gauge (ξ≠1) → the (1-ξ) kᵘkᵛ term is active. propagators
    # flipped numpy-free at rc123 (#564): the kᵘkᵛ outer product rides the
    # column·row Class-L matmul cascade and the propagator is a numpy-free Mat.
    k = [1.0, 0.5, 0.0, 0.0]
    P = feynman_photon_propagator(k_squared=1.0, gauge_xi=0.5, epsilon=1e-9, k=k)
    assert isinstance(P, Mat) and P.shape == (4, 4)   # propagator built numpy-free


def test_single_particle_density_matrix_routed():
    from srmech.amsc.mat import Mat
    from srmech.qm.single_particle import density_matrix
    s = 1.0 / math.sqrt(2.0)        # math in TEST code is fine
    psi = [complex(s, 0.0), complex(0.0, s)]
    rho = density_matrix(psi)
    assert isinstance(rho, Mat) and rho.shape == (2, 2)
    # |ψ⟩⟨ψ| = outer(ψ, conj(ψ)).
    exp = _expected_outer(psi, [z.conjugate() for z in psi])
    for i in range(2):
        for j in range(2):
            assert abs(rho[i, j] - exp[i][j]) < 1e-12
    # trace == ‖ψ‖² == 1.
    trace = rho[0, 0] + rho[1, 1]
    assert abs(trace - 1.0) < 1e-12

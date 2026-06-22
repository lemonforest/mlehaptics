"""0.9.0rc26 — `mat_eigvals` shifted-QR EXCEPTIONAL-SHIFT bug fix.

The float-QR ``mat_eigvals`` (``srmech/amsc/laplacian.py``) STALLED and returned
**all-zeros** on cyclic-permutation / equal-modulus-spectrum matrices — e.g. the
companion matrices of ``xⁿ − 1`` (the roots of unity). Root cause: the single-shift
Wilkinson loop computed ``μ`` from the trailing 2×2, which for a companion block is
``[[0,0],[1,0]]`` → both eigenvalues 0 → ``μ = 0`` → an UNSHIFTED step → an
equal-modulus spectrum never deflates → the loop ran to the ``sweeps > max_sweeps*n``
backstop, which appended the diagonal ``H[i][i]`` — and a companion matrix's diagonal
is all zeros → all-zero eigenvalues (silent garbage).

The fix (classic EISPACK ``hqr`` / LAPACK recipe; Golub & Van Loan §7.5):
  1. a per-deflation-target STALL counter ``it`` reset on every deflation;
  2. an EXCEPTIONAL shift injected at ``it == 10`` and ``it == 20`` built from the
     local sub-diagonal magnitudes ``μ = |H[m-1][m-2]| + |H[m-2][m-3]|`` — enough to
     dislodge the equal-modulus lock;
  3. a NON-SILENT failure mode: genuine non-convergence now RAISES ``RuntimeError``
     instead of returning the garbage diagonal.

Validated HARD against the rc25 exact integer oracle
``cascade.matrix_cascades.eigvals_exact(A, include_complex=True)`` (exact char-poly +
argument-principle-certified roots — it never stalls). numpy is GONE from srmech; this
ratchet is numpy-free and runs with numpy NOT installed.
"""
from __future__ import annotations

import importlib.util

import pytest

from srmech.amsc.cascade.matrix_cascades import eigvals_exact
from srmech.amsc.laplacian import jacobi_eigvals, mat_eigvals
from srmech.amsc.mat import Mat

_TOL = 1e-9


def test_numpy_is_absent_so_this_runs_not_skips():
    assert importlib.util.find_spec("numpy") is None, (
        "this rc26 ratchet must run on the numpy-ABSENT matrix")


# ── helpers ──────────────────────────────────────────────────────────────────────
def _key(z):
    z = complex(z)
    return (round(z.real, 9), round(z.imag, 9))


def _multiset_equal(got, exact, tol=_TOL):
    """Sort both by (re, im) and zip-compare to `tol` — the multiset match."""
    g = sorted((complex(z) for z in got), key=_key)
    e = sorted((complex(z) for z in exact), key=_key)
    if len(g) != len(e):
        return False
    return all(abs(a - b) < tol for a, b in zip(g, e))


def _companion(coeffs_low_to_high):
    """Companion matrix of a MONIC polynomial given low→high (constant term first,
    leading 1 implicit/dropped). For xⁿ − 1 pass [-1, 0, ..., 0] (length n)."""
    n = len(coeffs_low_to_high)
    rows = [[0] * n for _ in range(n)]
    for i in range(1, n):
        rows[i][i - 1] = 1                      # sub-diagonal ones (cyclic shift)
    for i in range(n):
        rows[i][n - 1] = -coeffs_low_to_high[i]  # last column = −constants
    return rows


# ── the battery: companion / cyclotomic spectra (the previously-FAILING cases) ───
# x^n − 1 has coeffs low→high [-1, 0, ..., 0]; x^4 + 1 has [1, 0, 0, 0].
_CYCLIC_CASES = {
    "x^3-1": _companion([-1, 0, 0]),
    "x^4-1": _companion([-1, 0, 0, 0]),
    "x^4+1": _companion([1, 0, 0, 0]),
    "x^5-1": _companion([-1, 0, 0, 0, 0]),
    "x^6-1": _companion([-1, 0, 0, 0, 0, 0]),
    # the explicit 3×3 cyclic permutation from the bug report
    "perm3": [[0, 0, 1], [1, 0, 0], [0, 1, 0]],
}


@pytest.mark.parametrize("label", sorted(_CYCLIC_CASES))
def test_cyclic_companion_matches_exact_oracle(label):
    """The formerly-FAILING cyclic / equal-modulus cases now match eigvals_exact."""
    A = _CYCLIC_CASES[label]
    got = mat_eigvals(Mat.from_rows(A))
    exact = eigvals_exact(A, include_complex=True)
    assert _multiset_equal(got, exact), (
        f"{label}: mat_eigvals {sorted(map(complex, got), key=_key)} != "
        f"eigvals_exact {sorted(map(complex, exact), key=_key)}")


@pytest.mark.parametrize("label", sorted(_CYCLIC_CASES))
def test_cyclic_companion_is_not_all_zeros(label):
    """The explicit regression guard: the historic bug returned ALL ZEROS for every
    cyclic-permutation companion (its diagonal is zero). Assert that never recurs."""
    got = [complex(z) for z in mat_eigvals(Mat.from_rows(_CYCLIC_CASES[label]))]
    assert any(abs(z) > _TOL for z in got), (
        f"{label}: mat_eigvals returned an all-zero spectrum (the historic stall "
        f"backstop bug): {got}")
    # roots of unity all have modulus 1 → none should be (numerically) zero
    assert all(abs(z) > _TOL for z in got), (
        f"{label}: a root-of-unity spectrum must have NO zero eigenvalue: {got}")


# ── rotation: real 2×2 with a purely-imaginary spectrum ──────────────────────────
def test_rotation_2x2_gives_pm_i():
    got = mat_eigvals(Mat.from_rows([[0, -1], [1, 0]]))
    assert _multiset_equal(got, [1j, -1j])


# ── hand-picked deterministic integer matrices with mixed real+complex spectra ───
_MIXED_CASES = {
    "3x3": [[1, 2, -1], [0, 1, 3], [2, -1, 0]],
    "4x4": [[2, 0, 1, -1], [1, 3, 0, 2], [0, -1, 1, 0], [1, 1, 1, 4]],
    "5x5": [[1, 2, 0, 0, 1], [-1, 1, 0, 0, 0], [0, 0, 3, 1, 0],
            [0, 0, -2, 3, 0], [1, 0, 0, 1, 2]],
}


@pytest.mark.parametrize("label", sorted(_MIXED_CASES))
def test_mixed_spectrum_matches_exact_oracle(label):
    A = _MIXED_CASES[label]
    got = mat_eigvals(Mat.from_rows(A))
    exact = eigvals_exact(A, include_complex=True)
    assert _multiset_equal(got, exact), (
        f"{label}: {sorted(map(complex, got), key=_key)} != "
        f"{sorted(map(complex, exact), key=_key)}")


# ── symmetric integer matrix: real spectrum, cross-checked two ways ──────────────
def test_symmetric_real_spectrum_vs_exact_and_jacobi():
    S = [[2, 1, 0], [1, 2, 1], [0, 1, 2]]
    got = sorted(complex(z).real for z in mat_eigvals(Mat.from_rows(S)))
    exact = sorted(eigvals_exact(S))                   # real-only path
    jac = sorted(jacobi_eigvals(Mat.from_rows(S)))     # pure Class-L Jacobi
    assert len(got) == len(exact) == len(jac) == 3
    assert all(abs(a - b) < _TOL for a, b in zip(got, exact))
    assert all(abs(a - b) < _TOL for a, b in zip(got, jac))
    # symmetric ⇒ spectrum is real (no imaginary part survives the QR)
    for z in mat_eigvals(Mat.from_rows(S)):
        assert abs(complex(z).imag) < _TOL


# ── defective integer matrix: a repeated eigenvalue, returned WITH multiplicity ──
def test_defective_returns_multiset_with_repeats():
    got = mat_eigvals(Mat.from_rows([[2, 1], [0, 2]]))
    assert _multiset_equal(got, [2 + 0j, 2 + 0j])      # {2, 2} incl. the repeat
    assert len(got) == 2


# ── identity / diagonal sanity (trivially-converged, no-stall path) ──────────────
def test_diagonal_and_identity():
    assert _multiset_equal(
        mat_eigvals(Mat.from_rows([[5, 0, 0], [0, -3, 0], [0, 0, 7]])),
        [5 + 0j, -3 + 0j, 7 + 0j])
    assert _multiset_equal(
        mat_eigvals(Mat.from_rows([[1, 0], [0, 1]])), [1 + 0j, 1 + 0j])

"""rc-B (rc21): opt-in exact symmetric eigenvalues via ``jacobi_eigvals(..., exact=True)``.

The rotation-last roadmap's rc-B: ``jacobi_eigvals`` gains a keyword-only
``exact: bool = False`` parameter. ``exact=False`` is the float-Jacobi path
verbatim (zero behaviour change); ``exact=True`` routes an integer/rational
SYMMETRIC matrix through the exact-substrate ``eigvals_exact`` cascade and
returns a 1-D ``Vec`` of the ascending eigenvalues WITH MULTIPLICITY, exact
until the single terminal float lift.

numpy-free (the module under test is numpy-free; this test must be too —
``[[feedback_test_for_numpy_free_module_must_itself_be_numpy_free]]``).
"""
from __future__ import annotations

from fractions import Fraction

import pytest

from srmech.amsc.laplacian import jacobi_eigvals
from srmech.amsc.vec import Vec


def _approx_equal(a, b, tol=1e-9) -> bool:
    """Class-K-honest magnitude tolerance check (never ``abs()`` on a cascade
    value — this is a TEST harness float compare, not a cascade op): |a-b| ≤ tol
    via a plain float subtraction + max."""
    d = a - b
    return (d if d >= 0.0 else -d) <= tol


def _vec_to_list(v) -> list:
    """Pull the flat ascending float list out of a Vec return."""
    assert isinstance(v, Vec), f"expected a Vec return; got {type(v).__name__}"
    return list(v.tolist())


def test_exact_two_by_two_matches_float():
    """M = [[2,1],[1,2]] has eigenvalues exactly 1 and 3. exact=True gives a
    Vec [1.0, 3.0] ascending, and it equals the float default within 1e-9."""
    M = [[2, 1], [1, 2]]
    ev_exact = _vec_to_list(jacobi_eigvals(M, exact=True))
    assert len(ev_exact) == 2
    assert _approx_equal(ev_exact[0], 1.0)
    assert _approx_equal(ev_exact[1], 3.0)
    # equals the float default (exact == float within 1e-9)
    ev_float = _vec_to_list(jacobi_eigvals(M))
    assert len(ev_float) == 2
    for a, b in zip(ev_exact, ev_float):
        assert _approx_equal(a, b)


def test_exact_repeated_eigenvalue_preserves_multiplicity():
    """Diagonal M = diag(2, 2, 5) → eigenvalues [2, 2, 5]; the repeated 2 must
    appear TWICE (multiplicity preserved → len == 3)."""
    M = [[2, 0, 0], [0, 2, 0], [0, 0, 5]]
    ev = _vec_to_list(jacobi_eigvals(M, exact=True))
    assert len(ev) == 3, f"multiplicity not preserved: got {ev}"
    assert _approx_equal(ev[0], 2.0)
    assert _approx_equal(ev[1], 2.0)
    assert _approx_equal(ev[2], 5.0)


def test_exact_graph_laplacian_repeated_eig_matches_float():
    """The 3-cycle graph Laplacian [[2,-1,-1],[-1,2,-1],[-1,-1,2]] has eigenvalues
    0, 3, 3. exact=True returns [0, 3, 3] WITH multiplicity, matching float to
    1e-9."""
    M = [[2, -1, -1], [-1, 2, -1], [-1, -1, 2]]
    ev_exact = _vec_to_list(jacobi_eigvals(M, exact=True))
    assert len(ev_exact) == 3, f"multiplicity not preserved: got {ev_exact}"
    assert _approx_equal(ev_exact[0], 0.0)
    assert _approx_equal(ev_exact[1], 3.0)
    assert _approx_equal(ev_exact[2], 3.0)
    ev_float = _vec_to_list(jacobi_eigvals(M))
    assert len(ev_float) == 3
    for a, b in zip(ev_exact, ev_float):
        assert _approx_equal(a, b)


def test_exact_rational_fraction_entries_accepted():
    """Fraction entries are EXACT and accepted: [[Fraction(2),Fraction(1)],
    [Fraction(1),Fraction(2)]] → eigenvalues 1, 3 (same as the int case)."""
    M = [[Fraction(2), Fraction(1)], [Fraction(1), Fraction(2)]]
    ev = _vec_to_list(jacobi_eigvals(M, exact=True))
    assert len(ev) == 2
    assert _approx_equal(ev[0], 1.0)
    assert _approx_equal(ev[1], 3.0)


def test_exact_on_float_matrix_raises():
    """exact=True on a FLOAT matrix raises ValueError (floats are not exact)."""
    M = [[2.0, 1.0], [1.0, 2.0]]
    with pytest.raises(ValueError):
        jacobi_eigvals(M, exact=True)


def test_exact_on_nonsymmetric_integer_matrix_raises():
    """exact=True on a NON-SYMMETRIC integer matrix raises ValueError (a
    non-symmetric integer matrix can have complex eigenvalues eigvals_exact
    returns incompletely)."""
    M = [[1, 2], [3, 4]]
    with pytest.raises(ValueError):
        jacobi_eigvals(M, exact=True)


def test_default_exact_false_unchanged_on_integer_symmetric():
    """The exact=False default equals the pre-rc21 float path on an integer
    symmetric matrix — sanity that the default is unchanged (explicit
    exact=False == omitting exact)."""
    M = [[2, 1], [1, 2]]
    ev_default = _vec_to_list(jacobi_eigvals(M))
    ev_explicit_false = _vec_to_list(jacobi_eigvals(M, exact=False))
    assert len(ev_default) == len(ev_explicit_false) == 2
    for a, b in zip(ev_default, ev_explicit_false):
        assert a == b  # byte-identical float path
    # and the spectrum is the right one (1, 3)
    assert _approx_equal(ev_default[0], 1.0)
    assert _approx_equal(ev_default[1], 3.0)


def test_exact_determinism():
    """Same input twice → identical exact eigenvalues (determinism)."""
    M = [[2, -1, -1], [-1, 2, -1], [-1, -1, 2]]
    first = _vec_to_list(jacobi_eigvals(M, exact=True))
    second = _vec_to_list(jacobi_eigvals(M, exact=True))
    assert first == second

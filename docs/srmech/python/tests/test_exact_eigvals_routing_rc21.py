"""rc-B (rc21): opt-in exact symmetric eigenvalues via ``jacobi_eigvals(..., exact=True)``.

The rotation-last roadmap's rc-B: ``jacobi_eigvals`` gains a keyword-only
``exact: bool = False`` parameter. ``exact=False`` is the float-Jacobi path
verbatim (zero behaviour change); ``exact=True`` routes an integer/rational
SYMMETRIC matrix through the exact-substrate cascade and returns the
ascending eigenvalues WITH MULTIPLICITY.

⚠️ **The exact RETURN CARRIER changed at rc467 (`#T1188`).** Through rc466 this
route ended in a terminal float lift and handed back a 1-D ``Vec`` of floats,
and every assertion below read it through ``_vec_to_list``. That lift destroyed
the exactness the keyword exists to supply — ``jacobi_eigvals([[2**53+1, 0],
[0, 1]], exact=True)`` returned ``9007199254740992.0``, off by one, for a
spectrum of two exact integers — so the route now returns a ``list`` of
:class:`~srmech.math.qalg.Qalg`, matching the sibling ``fiedler_vector``. This
file is the CALLER, rewritten in the same change rather than shimmed, and the
rewrite STRENGTHENS it: where a row used to assert a float within ``1e-9`` it
now asserts the exact rational, and the float comparison it used to make is
kept as a SEPARATE claim about the two routes agreeing.

numpy-free (the module under test is numpy-free; this test must be too —
``[[feedback_test_for_numpy_free_module_must_itself_be_numpy_free]]``).
"""
from __future__ import annotations

from fractions import Fraction

import pytest

from srmech.math.laplacian import jacobi_eigvals
from srmech.math.q import Q
from srmech.math.vec import Vec


def _approx_equal(a, b, tol=1e-9) -> bool:
    """Class-K-honest magnitude tolerance check (never ``abs()`` on a cascade
    value — this is a TEST harness float compare, not a cascade op): |a-b| ≤ tol
    via a plain float subtraction + max."""
    d = a - b
    return (d if d >= 0.0 else -d) <= tol


def _vec_to_list(v) -> list:
    """Pull the flat ascending float list out of the FLOAT route's Vec."""
    assert isinstance(v, Vec), f"expected a Vec return; got {type(v).__name__}"
    return list(v.tolist())


def _exact_rationals(v) -> list:
    """The EXACT route's ascending eigenvalues as ``Q``, asserting the carrier.

    rc467 (`#T1188`): the exact route returns ``list[Qalg]``, never a ``Vec``.
    Every eigenvalue in this file's fixtures is RATIONAL, so ``as_rational()``
    is not None on any of them — which is itself part of the claim."""
    assert not isinstance(v, Vec), "exact=True must NOT return the float Vec"
    assert isinstance(v, list), f"expected a list; got {type(v).__name__}"
    out = []
    for x in v:
        assert type(x).__name__ == "Qalg", f"leaf is {type(x).__name__}"
        r = x.as_rational()
        assert r is not None, f"{x!r} is irrational; this fixture is rational"
        out.append(r)
    return out


def _floats_of(v) -> list:
    """The exact eigenvalues projected to float, for the agreement claims."""
    return [x.to_float() for x in v]


def test_exact_two_by_two_matches_float():
    """M = [[2,1],[1,2]] has eigenvalues exactly 1 and 3. exact=True gives a
    Vec [1.0, 3.0] ascending, and it equals the float default within 1e-9."""
    M = [[2, 1], [1, 2]]
    got = jacobi_eigvals(M, exact=True)
    assert _exact_rationals(got) == [Q(1), Q(3)]      # EXACT, not within 1e-9
    # and the two routes still agree, which is the weaker claim this row
    # used to make as its only one
    ev_float = _vec_to_list(jacobi_eigvals(M))
    assert len(ev_float) == 2
    for a, b in zip(_floats_of(got), ev_float):
        assert _approx_equal(a, b)


def test_exact_repeated_eigenvalue_preserves_multiplicity():
    """Diagonal M = diag(2, 2, 5) → eigenvalues [2, 2, 5]; the repeated 2 must
    appear TWICE (multiplicity preserved → len == 3)."""
    M = [[2, 0, 0], [0, 2, 0], [0, 0, 5]]
    ev = _exact_rationals(jacobi_eigvals(M, exact=True))
    assert ev == [Q(2), Q(2), Q(5)], f"multiplicity not preserved: got {ev}"


def test_exact_graph_laplacian_repeated_eig_matches_float():
    """The 3-cycle graph Laplacian [[2,-1,-1],[-1,2,-1],[-1,-1,2]] has eigenvalues
    0, 3, 3. exact=True returns [0, 3, 3] WITH multiplicity, matching float to
    1e-9."""
    M = [[2, -1, -1], [-1, 2, -1], [-1, -1, 2]]
    got = jacobi_eigvals(M, exact=True)
    # The zero mode is EXACTLY zero now, not "0.0 within 1e-9" -- which is the
    # whole point of the carrier change.
    assert _exact_rationals(got) == [Q(0), Q(3), Q(3)], f"got {got}"
    ev_float = _vec_to_list(jacobi_eigvals(M))
    assert len(ev_float) == 3
    for a, b in zip(_floats_of(got), ev_float):
        assert _approx_equal(a, b)


def test_exact_rational_fraction_entries_accepted():
    """Fraction entries are EXACT and accepted: [[Fraction(2),Fraction(1)],
    [Fraction(1),Fraction(2)]] → eigenvalues 1, 3 (same as the int case)."""
    M = [[Fraction(2), Fraction(1)], [Fraction(1), Fraction(2)]]
    assert _exact_rationals(jacobi_eigvals(M, exact=True)) == [Q(1), Q(3)]
    # a NON-INTEGER rational operand too: the eigenvalues of [[1/2, 1/3],
    # [1/3, 1/2]] are 1/2 -/+ 1/3, and both come back exact rather than as the
    # nearest float
    N = [[Q(1, 2), Q(1, 3)], [Q(1, 3), Q(1, 2)]]
    assert _exact_rationals(jacobi_eigvals(N, exact=True)) == [Q(1, 6), Q(5, 6)]


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
    first = _exact_rationals(jacobi_eigvals(M, exact=True))
    second = _exact_rationals(jacobi_eigvals(M, exact=True))
    assert first == second


def test_the_54_bit_witness_the_float_lift_used_to_destroy():
    """rc467 (`#T1188`) -- the measurement that decided the carrier change.

    ``[[2**53+1, 0], [0, 1]]`` has a spectrum of two EXACT INTEGERS. Through
    rc466 this route returned ``9007199254740992.0`` for the larger one: off by
    one, from a route whose entire purpose is not to be. Nothing in this file
    could see it, because every row read the answer through ``float``."""
    P = 2 ** 53 + 1
    ev = jacobi_eigvals([[P, 0], [0, 1]], exact=True)
    assert _exact_rationals(ev) == [Q(1), Q(P)]
    # and the float route still rounds it, which is CORRECT for that route and
    # is why the keyword exists
    assert _vec_to_list(jacobi_eigvals([[float(P), 0.0], [0.0, 1.0]]))[1] != P

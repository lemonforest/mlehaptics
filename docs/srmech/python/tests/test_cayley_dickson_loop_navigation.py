"""W15 (RBS-LM bugfix wishlist) — Cayley–Dickson loop-navigation helpers.

``closure`` / ``left_orbit`` / ``min_generating_set`` are the combinatorial
layer over the ``cd_basis_product`` cocycle — the loop analogues of the
cyclic-group orbit machinery (the loop-shelf arc F541/F544/F546 re-derived
these each time; v0.7.5rc1 gives them a named home). A loop element is a signed
basis unit ``(sign, index)``; the full Moufang loop has ``2·dim`` elements.
"""

from __future__ import annotations

import pytest

from srmech.amsc.cascade import cayley_dickson as cd


# ---- left_orbit ------------------------------------------------------------

def test_left_orbit_octonion_generator_is_order_4() -> None:
    """``e_1`` under repeated left-mult by ``e_1``: e_1·e_1 = -e_0, so the
    cycle is [(1,1),(-1,0),(-1,1),(1,0)] — length 4."""
    orbit = cd.left_orbit(8, 1, 1)
    assert orbit == [(1, 1), (-1, 0), (-1, 1), (1, 0)]
    assert len(orbit) == 4
    # all elements distinct (it is a cycle, closing repeat excluded)
    assert len(set(orbit)) == len(orbit)


def test_left_orbit_identity_generator_is_fixed() -> None:
    """Left-mult by ``e_0`` (identity) maps every unit to itself → orbit of
    length 1."""
    assert cd.left_orbit(8, 3, 0) == [(1, 3)]


@pytest.mark.parametrize("dim", [2, 4, 8, 16])
def test_left_orbit_elements_are_signed_units(dim: int) -> None:
    for g in range(1, dim):
        for orbit in (cd.left_orbit(dim, 0, g),):
            for sign, idx in orbit:
                assert sign in (1, -1)
                assert 0 <= idx < dim


# ---- closure ---------------------------------------------------------------

def test_closure_single_octonion_generator_spans_4() -> None:
    """A single imaginary unit spans the order-4 sub-loop {±e_0, ±e_g}."""
    sub = cd.closure(8, [1])
    assert sub == {(1, 0), (1, 1), (-1, 0), (-1, 1)}
    assert len(sub) == 4


def test_closure_two_generators_span_quaternion_subloop() -> None:
    """e_1, e_2 generate e_3 = e_1·e_2 → the 8-element quaternion sub-loop."""
    assert len(cd.closure(8, [1, 2])) == 8


def test_closure_all_octonion_units_span_full_loop_16() -> None:
    """The 7 imaginary units span the full octonion loop (2·8 = 16)."""
    assert len(cd.closure(8, list(range(1, 8)))) == 16


def test_closure_full_quaternion_loop_is_8() -> None:
    assert len(cd.closure(4, [1, 2, 3])) == 8


def test_closure_is_closed_under_multiplication() -> None:
    """The returned set is genuinely a sub-loop: closed under products."""
    sub = cd.closure(8, [1, 2, 4])
    for a in sub:
        for b in sub:
            assert cd._loop_mult(8, a, b) in sub


# ---- min_generating_set ----------------------------------------------------

def test_min_generating_set_octonions_is_3() -> None:
    """The octonion loop needs 3 generators (a Fano-plane spanning set)."""
    assert cd.min_generating_set(8, list(range(1, 8))) == 3


def test_min_generating_set_quaternions_is_2() -> None:
    """The quaternion loop needs 2 (e_1, e_2 ⇒ e_3)."""
    assert cd.min_generating_set(4, [1, 2, 3]) == 2


def test_min_generating_set_complex_is_1() -> None:
    """ℂ: a single imaginary unit spans the whole 4-element loop."""
    assert cd.min_generating_set(2, [1]) == 1


def test_min_generating_set_raises_when_no_spanning_subset() -> None:
    """If the offered units cannot span the full loop, raise (e.g. a single
    octonion unit gives only the order-4 sub-loop, never 16)."""
    with pytest.raises(ValueError, match="full loop"):
        cd.min_generating_set(8, [1])


# ---- input validation ------------------------------------------------------

@pytest.mark.parametrize("bad_dim", [3, 6, 7, 128])
def test_non_power_of_two_dim_rejected(bad_dim: int) -> None:
    with pytest.raises(ValueError, match="power of two"):
        cd.closure(bad_dim, [1])
    with pytest.raises(ValueError, match="power of two"):
        cd.left_orbit(bad_dim, 0, 1)
    with pytest.raises(ValueError, match="power of two"):
        cd.min_generating_set(bad_dim, [1])


def test_out_of_range_index_rejected() -> None:
    with pytest.raises(ValueError, match="out of range"):
        cd.left_orbit(8, 0, 9)
    with pytest.raises(ValueError, match="out of range"):
        cd.closure(8, [9])
    with pytest.raises(ValueError, match="out of range"):
        cd.min_generating_set(8, [9])

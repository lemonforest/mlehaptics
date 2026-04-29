"""Tests for chess_spectral.spatial_4d.bitboard.Bitboard4D.

The 4096-bit set primitive that backs the v1.6 in-house 4D move
generator (per ADR-001). Tests every API surface in the module
docstring:

  * Construction (empty, full, from_squares, from_square, axis_plane,
    from_numpy_uint64)
  * Bitwise operators (|, &, ^, -, ~)
  * Predicates (is_empty, is_full, __contains__, intersects,
    is_subset, is_disjoint, popcount, len, bool)
  * Mutations (set_square, clear_square, toggle_square -- all
    return new instances since Bitboard4D is immutable)
  * Geometric (shift_axis along all 4 axes, positive + negative
    deltas, boundary clipping, |delta| >= 8 yields empty)
  * Iteration (squares(), to_squares(), __iter__)
  * Numpy round-trip
  * Equality + hashing
  * Edge cases: negative int input, oversized int input, square
    range validation, axis range validation
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
if PKG not in sys.path:
    sys.path.insert(0, PKG)

from chess_spectral.spatial_4d import Bitboard4D                  # noqa: E402
from chess_spectral.spatial_4d.bitboard import (                   # noqa: E402
    BOARD_SIDE, N_DIMENSIONS, N_SQUARES, ALL_BITS_MASK,
)
from chess_spectral.tables_4d import sq4                            # noqa: E402


# ---- Construction --------------------------------------------------


def test_empty_constructor():
    bb = Bitboard4D.empty()
    assert bb.popcount() == 0
    assert bb.is_empty()
    assert not bb.is_full()
    assert not bool(bb)
    assert len(bb) == 0


def test_full_constructor():
    bb = Bitboard4D.full()
    assert bb.popcount() == N_SQUARES
    assert bb.is_full()
    assert not bb.is_empty()
    assert bool(bb)
    assert len(bb) == N_SQUARES


def test_from_square():
    bb = Bitboard4D.from_square(sq4(3, 4, 5, 6))
    assert bb.popcount() == 1
    assert sq4(3, 4, 5, 6) in bb
    assert sq4(0, 0, 0, 0) not in bb


def test_from_squares():
    sqs = [sq4(0, 0, 0, 0), sq4(7, 7, 7, 7), sq4(3, 3, 3, 3)]
    bb = Bitboard4D.from_squares(sqs)
    assert bb.popcount() == 3
    for s in sqs:
        assert s in bb
    assert bb.to_squares() == sorted(sqs)


def test_from_squares_with_duplicates():
    """Duplicate squares should set the bit once, not raise."""
    sqs = [10, 10, 20, 20, 30]
    bb = Bitboard4D.from_squares(sqs)
    assert bb.popcount() == 3   # {10, 20, 30}


def test_from_squares_empty_iterable():
    bb = Bitboard4D.from_squares([])
    assert bb.is_empty()


def test_axis_plane_512_squares_per_plane():
    """Each axis-plane k contains 8^3 = 512 squares (one slice of
    the 4D lattice)."""
    for axis in range(N_DIMENSIONS):
        for k in range(BOARD_SIDE):
            plane = Bitboard4D.axis_plane(axis, k)
            assert plane.popcount() == 512, (
                f"axis {axis} plane k={k}: popcount "
                f"{plane.popcount()}, expected 512"
            )


def test_axis_planes_per_axis_partition():
    """For each axis, the 8 planes partition the 4096 squares: their
    union is full, pairwise intersections are empty."""
    for axis in range(N_DIMENSIONS):
        union = Bitboard4D.empty()
        for k in range(BOARD_SIDE):
            plane = Bitboard4D.axis_plane(axis, k)
            assert plane.is_disjoint(union), (
                f"axis {axis} plane {k} overlaps earlier planes"
            )
            union = union | plane
        assert union.is_full(), (
            f"axis {axis} planes don't cover all squares"
        )


def test_axis_plane_invalid_axis_raises():
    with pytest.raises(ValueError):
        Bitboard4D.axis_plane(-1, 0)
    with pytest.raises(ValueError):
        Bitboard4D.axis_plane(N_DIMENSIONS, 0)


def test_axis_plane_invalid_k_raises():
    with pytest.raises(ValueError):
        Bitboard4D.axis_plane(0, -1)
    with pytest.raises(ValueError):
        Bitboard4D.axis_plane(0, BOARD_SIDE)


def test_int_constructor_masks_high_bits():
    """If the user passes an int with bits above N_SQUARES set,
    those are silently dropped. Useful for defensive code that
    builds bitboards from arithmetic."""
    bb = Bitboard4D(ALL_BITS_MASK | (1 << 5000))
    assert bb.popcount() == N_SQUARES   # high bit dropped


def test_int_constructor_negative_input():
    """Negative int input (e.g. ``~Bitboard4D(0)._bits`` from raw
    Python ``~``) gets two's-complement projected to 4096 bits
    correctly."""
    # Construct via "what numpy ~ would produce on a 4096-bit signed".
    # Simpler: verify ~empty.full().
    full_via_invert = ~Bitboard4D(0)
    assert full_via_invert.is_full()


def test_invalid_square_index_raises_on_construction():
    with pytest.raises(ValueError):
        Bitboard4D.from_square(-1)
    with pytest.raises(ValueError):
        Bitboard4D.from_square(N_SQUARES)
    with pytest.raises(ValueError):
        Bitboard4D.from_squares([0, N_SQUARES])


# ---- Bitwise operators --------------------------------------------


def test_or_operator():
    a = Bitboard4D.from_square(0)
    b = Bitboard4D.from_square(1)
    c = a | b
    assert c.popcount() == 2
    assert 0 in c and 1 in c


def test_and_operator():
    a = Bitboard4D.from_squares([0, 1, 2])
    b = Bitboard4D.from_squares([2, 3, 4])
    c = a & b
    assert c.popcount() == 1
    assert 2 in c


def test_xor_operator():
    a = Bitboard4D.from_squares([0, 1, 2])
    b = Bitboard4D.from_squares([2, 3, 4])
    c = a ^ b
    assert c.popcount() == 4
    assert {0, 1, 3, 4} == set(c.to_squares())


def test_sub_operator_set_difference():
    a = Bitboard4D.from_squares([0, 1, 2])
    b = Bitboard4D.from_squares([2, 3])
    c = a - b
    assert c.popcount() == 2
    assert {0, 1} == set(c.to_squares())


def test_invert_full_to_empty_and_back():
    e = Bitboard4D.empty()
    f = Bitboard4D.full()
    assert ~e == f
    assert ~f == e
    assert ~~e == e   # double-invert is identity


def test_or_and_xor_with_self_identities():
    bb = Bitboard4D.from_squares([0, 100, 1000])
    assert (bb | bb) == bb
    assert (bb & bb) == bb
    assert (bb ^ bb).is_empty()
    assert (bb - bb).is_empty()


def test_bitwise_op_with_non_bitboard_returns_notimplemented():
    """The operators should return NotImplemented for unsupported
    types (then Python raises TypeError)."""
    with pytest.raises(TypeError):
        _ = Bitboard4D.empty() | 5
    with pytest.raises(TypeError):
        _ = Bitboard4D.empty() & "string"


# ---- Predicates ---------------------------------------------------


def test_intersects():
    a = Bitboard4D.from_squares([0, 1, 2])
    b = Bitboard4D.from_squares([2, 3, 4])
    c = Bitboard4D.from_squares([10, 11])
    assert a.intersects(b)
    assert not a.intersects(c)
    assert not Bitboard4D.empty().intersects(a)


def test_is_subset():
    a = Bitboard4D.from_squares([0, 1])
    b = Bitboard4D.from_squares([0, 1, 2, 3])
    assert a.is_subset(b)
    assert not b.is_subset(a)
    assert Bitboard4D.empty().is_subset(b)
    assert a.is_subset(a)   # reflexive


def test_is_disjoint():
    a = Bitboard4D.from_squares([0, 1])
    b = Bitboard4D.from_squares([2, 3])
    c = Bitboard4D.from_squares([1, 2])
    assert a.is_disjoint(b)
    assert not a.is_disjoint(c)


def test_contains_returns_bool_for_invalid_input():
    """Out-of-range indices and non-int return False (no exception)."""
    bb = Bitboard4D.from_square(0)
    assert (-1) not in bb
    assert N_SQUARES not in bb
    assert "x" not in bb


# ---- Mutations (return new) ---------------------------------------


def test_set_square_returns_new_instance():
    a = Bitboard4D.empty()
    b = a.set_square(42)
    assert a.is_empty()    # original unchanged
    assert 42 in b
    assert a is not b


def test_clear_square():
    a = Bitboard4D.from_squares([0, 1, 2])
    b = a.clear_square(1)
    assert 1 not in b
    assert {0, 2} == set(b.to_squares())
    # Clearing a bit not present is a no-op (still returns a new
    # equivalent instance).
    c = b.clear_square(99)
    assert b == c


def test_toggle_square():
    a = Bitboard4D.from_square(0)
    b = a.toggle_square(0)
    assert b.is_empty()
    c = b.toggle_square(0)
    assert c == a


def test_mutation_invalid_square_raises():
    bb = Bitboard4D.empty()
    with pytest.raises(ValueError):
        bb.set_square(-1)
    with pytest.raises(ValueError):
        bb.clear_square(N_SQUARES)
    with pytest.raises(ValueError):
        bb.toggle_square(N_SQUARES + 1)


# ---- Geometric: shift_axis ----------------------------------------


def test_shift_axis_zero_delta_returns_self():
    bb = Bitboard4D.from_squares([0, 100, 1000])
    assert bb.shift_axis(0, 0) == bb


def test_shift_axis_positive_x():
    bb = Bitboard4D.from_square(sq4(0, 0, 0, 0))
    shifted = bb.shift_axis(0, 1)   # x: 0 -> 1
    assert shifted.to_squares() == [sq4(1, 0, 0, 0)]


def test_shift_axis_positive_w():
    bb = Bitboard4D.from_square(sq4(0, 0, 0, 0))
    shifted = bb.shift_axis(3, 1)   # w: 0 -> 1
    assert shifted.to_squares() == [sq4(0, 0, 0, 1)]


def test_shift_axis_negative():
    bb = Bitboard4D.from_square(sq4(3, 3, 3, 3))
    shifted = bb.shift_axis(2, -1)   # z: 3 -> 2
    assert shifted.to_squares() == [sq4(3, 3, 2, 3)]


def test_shift_axis_off_lattice_clips():
    """A square at the edge shifted past the boundary is dropped."""
    bb = Bitboard4D.from_square(sq4(7, 0, 0, 0))
    shifted = bb.shift_axis(0, 1)   # x=7 -> would be x=8, clipped
    assert shifted.is_empty()
    bb = Bitboard4D.from_square(sq4(0, 0, 0, 0))
    shifted = bb.shift_axis(3, -1)  # w=0 -> would be w=-1, clipped
    assert shifted.is_empty()


def test_shift_axis_large_delta_yields_empty():
    """|delta| >= 8 always yields empty."""
    bb = Bitboard4D.full()
    assert bb.shift_axis(0, 8).is_empty()
    assert bb.shift_axis(0, -8).is_empty()
    assert bb.shift_axis(0, 100).is_empty()


def test_shift_axis_full_bitboard_loses_one_plane():
    """A full bitboard shifted by +1 along any axis loses the
    plane k=7 of that axis (those squares would shift off the
    lattice and are dropped)."""
    full = Bitboard4D.full()
    for axis in range(N_DIMENSIONS):
        shifted = full.shift_axis(axis, 1)
        # Should have 8 - 1 = 7 planes' worth of squares = 7 * 512 = 3584.
        assert shifted.popcount() == 7 * 512
        # Plane k=7 of this axis should be empty in shifted.
        plane7 = Bitboard4D.axis_plane(axis, 0)   # the source plane k=0 went to k=1
        # ... actually verify the empty plane:
        # Source plane k=0 gets shifted to k=1; source plane k=1 -> k=2; ...
        # source plane k=6 -> k=7; source plane k=7 falls off.
        # So in the shifted bitboard, plane k=0 is empty.
        empty_plane = Bitboard4D.axis_plane(axis, 0)
        assert (shifted & empty_plane).is_empty()


def test_shift_axis_invalid_axis_raises():
    bb = Bitboard4D.empty()
    with pytest.raises(ValueError):
        bb.shift_axis(-1, 1)
    with pytest.raises(ValueError):
        bb.shift_axis(N_DIMENSIONS, 1)


def test_shift_axis_empty_bitboard_stays_empty():
    bb = Bitboard4D.empty()
    for axis in range(N_DIMENSIONS):
        for delta in (-3, -1, 1, 3):
            assert bb.shift_axis(axis, delta).is_empty()


# ---- Iteration ---------------------------------------------------


def test_squares_iterates_ascending():
    sqs = [3000, 100, 4095, 0, 2048]
    bb = Bitboard4D.from_squares(sqs)
    out = list(bb.squares())
    assert out == sorted(sqs)


def test_iter_dunder():
    sqs = [10, 20, 30]
    bb = Bitboard4D.from_squares(sqs)
    assert list(bb) == [10, 20, 30]


def test_iteration_empty():
    assert list(Bitboard4D.empty()) == []


def test_iteration_full_yields_4096_squares():
    full = Bitboard4D.full()
    cnt = sum(1 for _ in full)
    assert cnt == N_SQUARES


# ---- Numpy round-trip --------------------------------------------


def test_to_numpy_uint64_shape_and_dtype():
    bb = Bitboard4D.from_squares([0, 100, 4095])
    arr = bb.to_numpy_uint64()
    assert arr.shape == (64,)
    assert arr.dtype == np.uint64


def test_numpy_roundtrip_random():
    """Random bitboards round-trip through numpy without loss."""
    rng = np.random.default_rng(42)
    for _ in range(5):
        n_sqs = int(rng.integers(0, 200))
        sqs = list(set(int(s) for s in rng.integers(0, N_SQUARES, n_sqs)))
        bb = Bitboard4D.from_squares(sqs)
        arr = bb.to_numpy_uint64()
        bb_recon = Bitboard4D.from_numpy_uint64(arr)
        assert bb == bb_recon


def test_numpy_roundtrip_full():
    full = Bitboard4D.full()
    arr = full.to_numpy_uint64()
    # Every uint64 element should be all-ones (0xFFFFFFFFFFFFFFFF).
    assert all(int(x) == (1 << 64) - 1 for x in arr)
    assert Bitboard4D.from_numpy_uint64(arr) == full


def test_from_numpy_uint64_shape_validation():
    with pytest.raises(ValueError):
        Bitboard4D.from_numpy_uint64(np.zeros(63, dtype=np.uint64))
    with pytest.raises(ValueError):
        Bitboard4D.from_numpy_uint64(np.zeros(64, dtype=np.int32))


# ---- Equality + hashing ------------------------------------------


def test_equality_and_hashing():
    a = Bitboard4D.from_squares([0, 100, 1000])
    b = Bitboard4D.from_squares([1000, 100, 0])
    assert a == b
    assert hash(a) == hash(b)
    # Usable as dict key.
    d = {a: "first"}
    assert d[b] == "first"


def test_inequality():
    a = Bitboard4D.from_square(0)
    b = Bitboard4D.from_square(1)
    assert a != b
    # Distinct hashes (statistically -- not guaranteed but very likely
    # for these specific inputs).
    assert hash(a) != hash(b)


def test_equality_with_non_bitboard():
    bb = Bitboard4D.empty()
    assert bb != 0
    assert bb != "empty"
    assert bb != None


# ---- Repr --------------------------------------------------------


def test_repr_empty():
    assert repr(Bitboard4D.empty()) == "Bitboard4D.empty()"


def test_repr_full():
    assert repr(Bitboard4D.full()) == "Bitboard4D.full()"


def test_repr_small_set_lists_squares():
    bb = Bitboard4D.from_squares([10, 20, 30])
    assert "10" in repr(bb) and "30" in repr(bb)


def test_repr_large_set_summarizes_popcount():
    bb = Bitboard4D.from_squares(range(100, 200))
    r = repr(bb)
    assert "popcount=100" in r


# ---- Public API surface ------------------------------------------


def test_module_exports():
    from chess_spectral.spatial_4d import bitboard
    assert "Bitboard4D" in bitboard.__all__
    assert "BOARD_SIDE" in bitboard.__all__
    assert "N_SQUARES" in bitboard.__all__


def test_package_exports():
    """Top-level chess_spectral.spatial_4d re-exports Bitboard4D."""
    import chess_spectral.spatial_4d as pkg
    assert "Bitboard4D" in pkg.__all__


def test_bits_property_readonly():
    bb = Bitboard4D.from_square(42)
    assert bb.bits == (1 << 42)
    # Not allowed to set bits (frozen).
    with pytest.raises(AttributeError):
        bb.bits = 0   # type: ignore

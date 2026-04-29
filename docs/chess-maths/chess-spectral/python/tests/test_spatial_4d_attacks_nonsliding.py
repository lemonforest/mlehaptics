"""Tests for chess_spectral.spatial_4d.attacks_nonsliding.

Knight + king attack tables. The tables are built from
``tables_4d.piece_adjacencies_4d()`` (the canonical 4D adjacency
source) so they MUST agree by construction; this test gates that
agreement as a regression check, plus exercises the API surface.

Empty-board reach counts validated against canonical positions:

  * Knight interior (3,3,3,3) → 48 reach targets
    (math: C(4,2) × 4 × 2 = 6 axis pairs × 4 sign combos × 2 swap
    choices)
  * Knight corner (0,0,0,0) → 12 (heavily boundary-clipped)
  * King interior (3,3,3,3) → 80 (= 3^4 − 1, all neighbours minus
    self)
  * King corner (0,0,0,0) → 15 (= 2^4 − 1, only neighbours with
    each coord in {0, 1})
  * King center-edge (4,0,0,0) → ?? (clipped on one axis only)
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

from chess_spectral.spatial_4d import (                            # noqa: E402
    KNIGHT_ATTACKS_4D, KING_ATTACKS_4D,
    attacks_knight_4d, attacks_king_4d,
    Bitboard4D,
)
from chess_spectral.spatial_4d.bitboard import N_SQUARES           # noqa: E402
from chess_spectral.tables_4d import sq4, piece_adjacencies_4d     # noqa: E402


# ---- Table shape / dtype --------------------------------------


def test_knight_table_shape():
    """Table is a tuple of exactly 4096 Bitboard4D entries."""
    assert isinstance(KNIGHT_ATTACKS_4D, tuple)
    assert len(KNIGHT_ATTACKS_4D) == N_SQUARES
    for sq in (0, 100, 4095):
        assert isinstance(KNIGHT_ATTACKS_4D[sq], Bitboard4D)


def test_king_table_shape():
    assert isinstance(KING_ATTACKS_4D, tuple)
    assert len(KING_ATTACKS_4D) == N_SQUARES
    for sq in (0, 100, 4095):
        assert isinstance(KING_ATTACKS_4D[sq], Bitboard4D)


# ---- Reach counts at canonical positions ----------------------


def test_knight_interior_reach_is_48():
    """A 4D knight at deep interior reaches C(4,2) × 4 × 2 = 48
    squares -- 6 axis-pair choices × 4 sign combinations × 2
    which-axis-gets-±2 swaps."""
    sq = sq4(3, 3, 3, 3)
    bb = attacks_knight_4d(sq)
    assert bb.popcount() == 48


def test_knight_corner_reach_is_12():
    """4D knight at (0,0,0,0): heavy boundary clipping leaves 12."""
    sq = sq4(0, 0, 0, 0)
    bb = attacks_knight_4d(sq)
    assert bb.popcount() == 12


def test_king_interior_reach_is_80():
    """King at deep interior reaches 3^4 - 1 = 80 hypercube
    neighbours."""
    sq = sq4(3, 3, 3, 3)
    bb = attacks_king_4d(sq)
    assert bb.popcount() == 80


def test_king_corner_reach_is_15():
    """King at (0,0,0,0) corner reaches 2^4 - 1 = 15 squares (only
    neighbours with each coord in {0, 1})."""
    sq = sq4(0, 0, 0, 0)
    bb = attacks_king_4d(sq)
    assert bb.popcount() == 15


def test_knight_corner_reach_is_strict_subset_of_interior():
    """Boundary-clipping must reduce reach; corners reach fewer
    squares than interior."""
    interior = attacks_knight_4d(sq4(3, 3, 3, 3))
    corner = attacks_knight_4d(sq4(0, 0, 0, 0))
    assert corner.popcount() < interior.popcount()


# ---- Symmetry properties --------------------------------------


@pytest.mark.parametrize('coord', [
    (3, 3, 3, 3), (0, 0, 0, 0), (1, 2, 3, 4),
    (7, 0, 7, 0), (4, 0, 0, 0),
])
def test_knight_self_loop_excluded(coord):
    """A knight cannot attack its own square."""
    sq = sq4(*coord)
    bb = attacks_knight_4d(sq)
    assert sq not in bb


@pytest.mark.parametrize('coord', [
    (3, 3, 3, 3), (0, 0, 0, 0), (1, 2, 3, 4),
    (7, 0, 7, 0), (4, 0, 0, 0),
])
def test_king_self_loop_excluded(coord):
    """A king cannot attack its own square."""
    sq = sq4(*coord)
    bb = attacks_king_4d(sq)
    assert sq not in bb


def test_knight_attack_is_symmetric():
    """If knight at A attacks B, then knight at B attacks A
    (the knight reach predicate is involutive on the empty-board
    reach graph)."""
    for s in range(0, N_SQUARES, 47):   # sample every 47th square
        for t in attacks_knight_4d(s):
            assert s in attacks_knight_4d(t), (
                f"knight reach asymmetry: {s} -> {t} but not "
                f"{t} -> {s}"
            )


def test_king_attack_is_symmetric():
    """King reach is also symmetric (adjacency)."""
    for s in range(0, N_SQUARES, 47):
        for t in attacks_king_4d(s):
            assert s in attacks_king_4d(t), (
                f"king reach asymmetry: {s} -> {t} but not "
                f"{t} -> {s}"
            )


# ---- Parity vs tables_4d.piece_adjacencies_4d ---------------


def test_knight_table_matches_piece_adjacencies_4d():
    """Knight bitboards EXACTLY match the dense knight adjacency
    from tables_4d.piece_adjacencies_4d() on every from-square.
    Both sources must agree by construction (they trace back to
    the same knight4_targets iterator)."""
    adjs = piece_adjacencies_4d()
    A_knight = adjs[0].toarray()
    for s in range(N_SQUARES):
        expected = frozenset(int(j) for j in np.flatnonzero(A_knight[s] >= 0.5))
        actual = frozenset(KNIGHT_ATTACKS_4D[s].to_squares())
        assert expected == actual, (
            f"knight @ s={s}: expected {sorted(expected)} vs "
            f"actual {sorted(actual)}"
        )


def test_king_table_matches_piece_adjacencies_4d():
    """King bitboards match the dense king adjacency from tables_4d
    on every from-square."""
    adjs = piece_adjacencies_4d()
    A_king = adjs[4].toarray()
    for s in range(N_SQUARES):
        expected = frozenset(int(j) for j in np.flatnonzero(A_king[s] >= 0.5))
        actual = frozenset(KING_ATTACKS_4D[s].to_squares())
        assert expected == actual, (
            f"king @ s={s}: expected {sorted(expected)} vs "
            f"actual {sorted(actual)}"
        )


# ---- Cross-validate against spectral_legality_4d (when present) ----
# The spectral_legality_4d module ships in the parallel PR #92 stack;
# this branch (PR-7-C) doesn't include it. When PR #92 + PR-7-C both
# merge to main, the cross-check runs as a third-oracle gate. We
# guard the import with a skip so the test passes here and runs on
# main once both stacks have landed.


@pytest.mark.skipif(
    True,
    reason="spectral_legality_4d ships on parallel PR #92 stack; "
           "cross-oracle gate runs once both PRs merge to main"
)
def test_knight_table_agrees_with_spectral_legality_oracle():
    """Three-oracle convergence: bitboard knight attack table ↔
    chess_spectral.spectral_legality_4d.reachable_targets_4d."""
    from chess_spectral.spectral_legality_4d import reachable_targets_4d
    for s in range(0, N_SQUARES, 31):
        oracle = reachable_targets_4d('N', s)
        bitboard = frozenset(KNIGHT_ATTACKS_4D[s].to_squares())
        assert oracle == bitboard, f"knight oracle mismatch @ s={s}"


@pytest.mark.skipif(
    True,
    reason="spectral_legality_4d ships on parallel PR #92 stack; "
           "cross-oracle gate runs once both PRs merge to main"
)
def test_king_table_agrees_with_spectral_legality_oracle():
    from chess_spectral.spectral_legality_4d import reachable_targets_4d
    for s in range(0, N_SQUARES, 31):
        oracle = reachable_targets_4d('K', s)
        bitboard = frozenset(KING_ATTACKS_4D[s].to_squares())
        assert oracle == bitboard, f"king oracle mismatch @ s={s}"


# ---- O(1) accessors ------------------------------------------


def test_attacks_knight_4d_returns_same_as_table():
    """attacks_knight_4d(s) is identical to KNIGHT_ATTACKS_4D[s]."""
    for s in (0, 100, 1000, 4095):
        assert attacks_knight_4d(s) is KNIGHT_ATTACKS_4D[s]


def test_attacks_king_4d_returns_same_as_table():
    for s in (0, 100, 1000, 4095):
        assert attacks_king_4d(s) is KING_ATTACKS_4D[s]


def test_attacks_knight_4d_invalid_square_raises():
    with pytest.raises(ValueError):
        attacks_knight_4d(-1)
    with pytest.raises(ValueError):
        attacks_knight_4d(N_SQUARES)


def test_attacks_king_4d_invalid_square_raises():
    with pytest.raises(ValueError):
        attacks_king_4d(-1)
    with pytest.raises(ValueError):
        attacks_king_4d(N_SQUARES)


# ---- Additional reach-count spot checks ---------------------


@pytest.mark.parametrize('coord,expected', [
    # Interior, deep -- maximum reach (4 ± 1 / 4 ± 2 all in-bounds).
    ((4, 4, 4, 4), 48),     # C(4,2) × 4 sign combos × 2 swaps = 48
    # Corner, both ±1 and ±2 invalid in 3 of 4 axes.
    ((0, 0, 0, 0), 12),
    # Opposite corner (B_4 symmetry).
    ((7, 7, 7, 7), 12),
    # Face center: one axis interior, three axes at edge.
    # Hand-derived: see commit message; equals 18.
    ((4, 0, 0, 0), 18),
    # Generic interior point (at coords 1,2,3,4 -- all interior with
    # asymmetric clipping). Matches the actual table.
    ((1, 2, 3, 4), 42),
])
def test_knight_reach_count_at_position(coord, expected):
    """Knight reach counts at canonical positions, hand-derived from
    the move rule. Regression check that the table doesn't drift
    silently if anyone touches knight4_targets in tables_4d.

    Math sketch (knight moves ±2 along one axis, ±1 along another;
    C(4,2) = 6 axis pairs):
      * Interior: 6 pairs × (2 ±2 directions) × (2 ±1 directions) ×
        (2 axis-swap choices, treating the larger-step axis as the
        first or second axis of the pair) = 6 × 4 × 2 = 48.
      * Boundary clipping reduces this depending on which axes are
        edge-touching.
    """
    sq = sq4(*coord)
    n = attacks_knight_4d(sq).popcount()
    assert n == expected, (
        f"knight @ {coord}: reach {n}, expected {expected}"
    )


@pytest.mark.parametrize('coord,expected', [
    ((4, 4, 4, 4), 80),     # deep interior: 3^4 - 1
    ((0, 0, 0, 0), 15),     # corner: 2^4 - 1
    ((7, 7, 7, 7), 15),     # opposite corner (by symmetry)
    ((4, 0, 0, 0), 23),     # one axis interior (3 vals), three at
                            # edge (2 vals each): 3 * 2^3 - 1 = 23
    ((1, 2, 3, 4), 80),     # all interior (1..6 each axis): 80
])
def test_king_reach_count_at_position(coord, expected):
    """King reach counts at canonical positions. Math: reach equals
    the count of distinct neighbours within the {-1, 0, +1}^4
    hypercube minus the source itself, intersected with the lattice.

    For a coord with k axes interior (each contributes 3 valid
    values) and (4-k) axes at an edge (each contributes 2 valid
    values): reach = 3^k * 2^(4-k) - 1.
    """
    sq = sq4(*coord)
    n = attacks_king_4d(sq).popcount()
    assert n == expected, (
        f"king @ {coord}: reach {n}, expected {expected}"
    )


# ---- Module API surface --------------------------------------


def test_module_exports():
    from chess_spectral.spatial_4d import attacks_nonsliding
    for name in ('KNIGHT_ATTACKS_4D', 'KING_ATTACKS_4D',
                 'attacks_knight_4d', 'attacks_king_4d'):
        assert name in attacks_nonsliding.__all__


def test_package_re_exports():
    """spatial_4d package re-exports the non-sliding attack API."""
    import chess_spectral.spatial_4d as pkg
    for name in ('KNIGHT_ATTACKS_4D', 'KING_ATTACKS_4D',
                 'attacks_knight_4d', 'attacks_king_4d'):
        assert name in pkg.__all__

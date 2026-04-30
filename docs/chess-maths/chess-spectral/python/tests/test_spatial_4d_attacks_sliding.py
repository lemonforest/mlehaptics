"""Tests for sliding-piece attack generation in spatial_4d.

Covers :mod:`chess_spectral.spatial_4d.attacks_sliding` (rook, bishop,
queen) and the :mod:`rays` ray-table primitives that back it.

Test patterns:
  * Empty-board reach matches tables_4d.{rook4,bishop4,queen4}_targets
    on every from-square (canonical parity gate)
  * Empty-board reach counts at canonical positions
  * Blocker handling: first blocker on each ray is included; squares
    beyond are excluded
  * Source square never appears in its own attack set
  * Queen = rook ∪ bishop (disjoint supports per Oana & Chiru §2)
  * Bishop preserves coordinate-sum parity (2 connected components)
  * Direction enumeration: 8 rook + 24 bishop = 32 queen, no
    duplicates
  * API edge cases: out-of-range squares raise; full-occupancy
    "everything blocked" case
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
    Bitboard4D,
    attacks_rook_4d, attacks_bishop_4d, attacks_queen_4d,
    ROOK_DIRECTIONS, BISHOP_DIRECTIONS, QUEEN_DIRECTIONS,
    ROOK_RAYS, BISHOP_RAYS, QUEEN_RAYS,
)
from chess_spectral.spatial_4d.bitboard import N_SQUARES           # noqa: E402
from chess_spectral.tables_4d import (                              # noqa: E402
    sq4, piece_adjacencies_4d, rook4_targets, bishop4_targets,
    queen4_targets,
)


# ---- Direction tables --------------------------------------------


def test_rook_has_8_directions():
    assert len(ROOK_DIRECTIONS) == 8


def test_bishop_has_24_directions():
    """6 axis pairs × 4 sign combos."""
    assert len(BISHOP_DIRECTIONS) == 24


def test_queen_has_32_directions():
    """Queen = rook ∪ bishop (disjoint)."""
    assert len(QUEEN_DIRECTIONS) == 32


def test_rook_directions_unit_axis_aligned():
    """Each rook direction has exactly one nonzero coordinate, ±1."""
    for d in ROOK_DIRECTIONS:
        assert sum(1 for c in d if c != 0) == 1
        assert all(c in (-1, 0, 1) for c in d)


def test_bishop_directions_unit_2axis_diagonal():
    """Each bishop direction has exactly two nonzero coordinates,
    each ±1."""
    for d in BISHOP_DIRECTIONS:
        assert sum(1 for c in d if c != 0) == 2
        assert all(c in (-1, 0, 1) for c in d)


def test_directions_no_duplicates_in_queen():
    """Queen directions are distinct (rook and bishop don't overlap)."""
    assert len(set(QUEEN_DIRECTIONS)) == 32


# ---- Ray tables --------------------------------------------------


def test_rook_rays_shape():
    assert len(ROOK_RAYS) == N_SQUARES
    for s in (0, 100, 4095):
        assert len(ROOK_RAYS[s]) == 8


def test_bishop_rays_shape():
    assert len(BISHOP_RAYS) == N_SQUARES
    for s in (0, 100, 4095):
        assert len(BISHOP_RAYS[s]) == 24


def test_rook_ray_at_corner_partially_empty():
    """Rook at (0,0,0,0) corner: rays in -axis directions are empty;
    rays in +axis directions have 7 squares each."""
    rays = ROOK_RAYS[sq4(0, 0, 0, 0)]
    # Direction order from ROOK_DIRECTIONS: (-1,0,0,0), (+1,0,0,0),
    # (0,-1,0,0), (0,+1,0,0), (0,0,-1,0), (0,0,+1,0), (0,0,0,-1),
    # (0,0,0,+1).
    # All "-1" directions should be empty rays from (0,0,0,0).
    for d_idx in (0, 2, 4, 6):  # the four -1 directions
        assert len(rays[d_idx]) == 0
    # All "+1" directions should have 7 squares.
    for d_idx in (1, 3, 5, 7):
        assert len(rays[d_idx]) == 7


def test_rook_ray_interior_full_length():
    """Rook at (4,4,4,4): each ray has min(distance to that boundary)
    squares. -axis directions: 4 squares (indices 3,2,1,0); +axis:
    3 squares (indices 5,6,7)."""
    rays = ROOK_RAYS[sq4(4, 4, 4, 4)]
    for d_idx in (0, 2, 4, 6):  # -1 directions
        assert len(rays[d_idx]) == 4
    for d_idx in (1, 3, 5, 7):  # +1 directions
        assert len(rays[d_idx]) == 3


# ---- Empty-board attack parity ----------------------------------


def test_rook_empty_board_parity():
    """Rook attacks on an empty lattice match the rook4_targets
    iterator from tables_4d on every from-square."""
    empty = Bitboard4D.empty()
    for s in range(0, N_SQUARES, 17):  # sample every 17th square
        x, y, z, w = s // 512, (s // 64) % 8, (s // 8) % 8, s % 8
        expected = frozenset(sq4(*t) for t in rook4_targets(x, y, z, w))
        actual = frozenset(attacks_rook_4d(s, empty).to_squares())
        assert expected == actual, f"rook @ s={s}: mismatch"


def test_bishop_empty_board_parity():
    """Bishop empty-board attacks match bishop4_targets."""
    empty = Bitboard4D.empty()
    for s in range(0, N_SQUARES, 17):
        x, y, z, w = s // 512, (s // 64) % 8, (s // 8) % 8, s % 8
        expected = frozenset(sq4(*t) for t in bishop4_targets(x, y, z, w))
        actual = frozenset(attacks_bishop_4d(s, empty).to_squares())
        assert expected == actual, f"bishop @ s={s}: mismatch"


def test_queen_empty_board_parity():
    """Queen empty-board attacks match queen4_targets."""
    empty = Bitboard4D.empty()
    for s in range(0, N_SQUARES, 17):
        x, y, z, w = s // 512, (s // 64) % 8, (s // 8) % 8, s % 8
        expected = frozenset(sq4(*t) for t in queen4_targets(x, y, z, w))
        actual = frozenset(attacks_queen_4d(s, empty).to_squares())
        assert expected == actual, f"queen @ s={s}: mismatch"


def test_rook_empty_board_full_parity_via_adjacency():
    """Stronger: rook attacks on EVERY square match the dense
    adjacency from tables_4d.piece_adjacencies_4d()."""
    empty = Bitboard4D.empty()
    adjs = piece_adjacencies_4d()
    A_rook = adjs[2].toarray()  # rook is index 2
    mismatches = 0
    for s in range(N_SQUARES):
        expected = frozenset(int(j) for j in np.flatnonzero(A_rook[s] >= 0.5))
        actual = frozenset(attacks_rook_4d(s, empty).to_squares())
        if expected != actual:
            mismatches += 1
            if mismatches <= 3:
                pytest.fail(
                    f"rook @ s={s}: expected {sorted(expected)[:5]}..., "
                    f"got {sorted(actual)[:5]}..."
                )
    assert mismatches == 0


# ---- Reach counts ----------------------------------------------


def test_rook_interior_reach_is_28():
    """Rook on (4,4,4,4) attacks 7 squares per axis × 4 axes = 28."""
    empty = Bitboard4D.empty()
    bb = attacks_rook_4d(sq4(4, 4, 4, 4), empty)
    assert bb.popcount() == 28


def test_rook_corner_reach_is_28_too():
    """Rook reach is 28 from any square on an empty board (each axis
    line has 7 other squares; no boundary clipping for axis-aligned
    rays since the entire line is reachable)."""
    empty = Bitboard4D.empty()
    bb = attacks_rook_4d(sq4(0, 0, 0, 0), empty)
    assert bb.popcount() == 28


def test_bishop_interior_reach_is_78():
    """Bishop on (4,4,4,4): 6 axis pairs × (3+3+3+4) = 78. See
    PR-7-D commit message for the per-pair breakdown."""
    empty = Bitboard4D.empty()
    bb = attacks_bishop_4d(sq4(4, 4, 4, 4), empty)
    assert bb.popcount() == 78


def test_queen_interior_reach_is_106():
    """Queen = rook + bishop (disjoint supports per O&C §2)."""
    empty = Bitboard4D.empty()
    bb = attacks_queen_4d(sq4(4, 4, 4, 4), empty)
    assert bb.popcount() == 106  # 28 + 78


# ---- Blocker handling -------------------------------------------


def test_rook_blocker_includes_first_excludes_beyond():
    """Rook at (4,4,4,4) with blocker at (6,4,4,4): can attack
    (5,4,4,4) and (6,4,4,4), CANNOT attack (7,4,4,4)."""
    blocker = Bitboard4D.from_square(sq4(6, 4, 4, 4))
    bb = attacks_rook_4d(sq4(4, 4, 4, 4), blocker)
    assert sq4(5, 4, 4, 4) in bb
    assert sq4(6, 4, 4, 4) in bb
    assert sq4(7, 4, 4, 4) not in bb


def test_rook_blocker_on_other_axis_no_effect():
    """Rook blocker on axis A doesn't affect attacks along axis B."""
    sq = sq4(4, 4, 4, 4)
    empty = Bitboard4D.empty()
    blocker_x = Bitboard4D.from_square(sq4(6, 4, 4, 4))
    bb_empty = attacks_rook_4d(sq, empty)
    bb_blocked = attacks_rook_4d(sq, blocker_x)
    # Axis-y attacks should be the same.
    for k in range(8):
        if k == 4:
            continue
        target = sq4(4, k, 4, 4)
        assert (target in bb_empty) == (target in bb_blocked)


def test_rook_immediate_neighbor_blocker():
    """Blocker at (5,4,4,4): rook at (4,4,4,4) can attack (5,4,4,4)
    but not (6,*,4,4) or (7,*,4,4) along +x."""
    blocker = Bitboard4D.from_square(sq4(5, 4, 4, 4))
    bb = attacks_rook_4d(sq4(4, 4, 4, 4), blocker)
    assert sq4(5, 4, 4, 4) in bb
    assert sq4(6, 4, 4, 4) not in bb
    assert sq4(7, 4, 4, 4) not in bb


def test_bishop_blocker_handling():
    """Bishop at (4,4,4,4) with blocker at (6,6,4,4) along (+1,+1,0,0):
    can attack (5,5,4,4) and (6,6,4,4), not (7,7,4,4)."""
    blocker = Bitboard4D.from_square(sq4(6, 6, 4, 4))
    bb = attacks_bishop_4d(sq4(4, 4, 4, 4), blocker)
    assert sq4(5, 5, 4, 4) in bb
    assert sq4(6, 6, 4, 4) in bb
    assert sq4(7, 7, 4, 4) not in bb


def test_full_occupancy_reach_just_neighbors():
    """If every square is occupied, slider attacks are limited to
    immediate neighbors along each direction (the first blocker is
    always one step away)."""
    full = Bitboard4D.full()
    sq = sq4(4, 4, 4, 4)

    # Rook: 8 immediate neighbors (1 per direction × 8 directions).
    bb = attacks_rook_4d(sq, full)
    assert bb.popcount() == 8

    # Bishop: 24 immediate neighbors (1 per direction × 24).
    bb = attacks_bishop_4d(sq, full)
    assert bb.popcount() == 24

    # Queen: 32 immediate neighbors.
    bb = attacks_queen_4d(sq, full)
    assert bb.popcount() == 32


# ---- Source-square exclusion ------------------------------------


@pytest.mark.parametrize('coord', [
    (4, 4, 4, 4), (0, 0, 0, 0), (7, 7, 7, 7), (1, 2, 3, 4),
])
def test_source_square_excluded_rook(coord):
    sq = sq4(*coord)
    empty = Bitboard4D.empty()
    full = Bitboard4D.full()
    assert sq not in attacks_rook_4d(sq, empty)
    assert sq not in attacks_rook_4d(sq, full)


@pytest.mark.parametrize('coord', [
    (4, 4, 4, 4), (0, 0, 0, 0), (7, 7, 7, 7), (1, 2, 3, 4),
])
def test_source_square_excluded_bishop(coord):
    sq = sq4(*coord)
    empty = Bitboard4D.empty()
    full = Bitboard4D.full()
    assert sq not in attacks_bishop_4d(sq, empty)
    assert sq not in attacks_bishop_4d(sq, full)


# ---- Queen = rook | bishop ------------------------------------


def test_queen_equals_rook_union_bishop():
    """Queen attacks = rook attacks ∪ bishop attacks for any
    occupancy."""
    rng = np.random.default_rng(42)
    sqs = [sq4(*tuple(int(c) for c in rng.integers(0, 8, 4)))
           for _ in range(5)]
    occupancies = [
        Bitboard4D.empty(),
        Bitboard4D.full(),
        Bitboard4D.from_squares([sq4(2,3,4,5), sq4(6,1,7,2)]),
    ]
    for sq in sqs:
        for occ in occupancies:
            r = attacks_rook_4d(sq, occ)
            b = attacks_bishop_4d(sq, occ)
            q = attacks_queen_4d(sq, occ)
            assert q == (r | b), (
                f"queen != rook ∪ bishop @ sq={sq}, "
                f"occ.popcount()={occ.popcount()}"
            )


def test_rook_bishop_disjoint_on_empty_board():
    """Per Oana & Chiru §2: rook and bishop attack supports are
    disjoint (rook moves change exactly one coord; bishop changes
    exactly two)."""
    empty = Bitboard4D.empty()
    for s in (sq4(4,4,4,4), sq4(0,0,0,0), sq4(3,5,2,6)):
        r = attacks_rook_4d(s, empty)
        b = attacks_bishop_4d(s, empty)
        assert (r & b).is_empty(), (
            f"rook & bishop should be disjoint @ s={s}, got "
            f"intersection of {(r & b).popcount()} squares"
        )


# ---- Bishop parity property ------------------------------------


def test_bishop_preserves_coord_sum_parity():
    """Per Oana & Chiru §2: bishop preserves coord-sum parity → 2
    connected components on an empty lattice. Verify on every
    bishop attack target."""
    empty = Bitboard4D.empty()
    for s in (sq4(4,4,4,4), sq4(0,1,2,3), sq4(7,7,7,7)):
        x, y, z, w = s // 512, (s // 64) % 8, (s // 8) % 8, s % 8
        src_parity = (x + y + z + w) % 2
        bb = attacks_bishop_4d(s, empty)
        for t in bb.to_squares():
            tx, ty, tz, tw = t // 512, (t // 64) % 8, (t // 8) % 8, t % 8
            t_parity = (tx + ty + tz + tw) % 2
            assert src_parity == t_parity, (
                f"bishop crossed parity: {s} (parity {src_parity}) -> "
                f"{t} (parity {t_parity})"
            )


# ---- API edge cases --------------------------------------------


def test_invalid_square_raises():
    empty = Bitboard4D.empty()
    with pytest.raises(ValueError):
        attacks_rook_4d(-1, empty)
    with pytest.raises(ValueError):
        attacks_rook_4d(N_SQUARES, empty)
    with pytest.raises(ValueError):
        attacks_bishop_4d(-1, empty)
    with pytest.raises(ValueError):
        attacks_queen_4d(N_SQUARES, empty)


def test_module_exports():
    from chess_spectral.spatial_4d import attacks_sliding, rays
    for name in ('attacks_rook_4d', 'attacks_bishop_4d',
                 'attacks_queen_4d'):
        assert name in attacks_sliding.__all__
    for name in ('ROOK_DIRECTIONS', 'BISHOP_DIRECTIONS',
                 'QUEEN_DIRECTIONS', 'ROOK_RAYS', 'BISHOP_RAYS',
                 'QUEEN_RAYS'):
        assert name in rays.__all__


def test_package_re_exports():
    """Top-level chess_spectral.spatial_4d re-exports the sliding
    attack API."""
    import chess_spectral.spatial_4d as pkg
    for name in ('attacks_rook_4d', 'attacks_bishop_4d',
                 'attacks_queen_4d',
                 'ROOK_DIRECTIONS', 'BISHOP_DIRECTIONS', 'QUEEN_DIRECTIONS'):
        assert name in pkg.__all__

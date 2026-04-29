"""Non-sliding piece attack tables for 4D chess.

Pre-computed empty-board reach bitboards for the **non-sliding**
pieces -- knight and king. Sliding pieces (rook, bishop, queen) are
handled separately via magic bitboards in :mod:`attacks_sliding`
(PR-7-D); pawns are handled in :mod:`attacks_pawn` (PR-7-E) because
of axis-typed move rules.

Each table is a tuple of 4096 :class:`Bitboard4D` instances --
``ATTACKS[from_sq]`` is the bitboard of squares that piece would
attack from ``from_sq`` on an otherwise-empty 8^4 lattice. Lookup
is O(1) -- a single tuple-index. Built once at module import time
from :mod:`chess_spectral.tables_4d` (the canonical adjacency
source), so the bitboard tables and ``tables_4d.piece_adjacencies_4d()``
agree by construction. Tests gate this with a parity check.

Why non-sliders are easy
------------------------
For a non-sliding piece (knight / king), the attack set from each
square depends only on the source square -- never on occupancy.
So the table is a simple precomputed map. For sliding pieces the
attack set depends on occupancy along each axis; that's why magic
bitboards (PR-7-D) earn their place.

Boundary clipping is handled at table-build time by reusing the
existing ``knight4_targets`` / ``king4_targets`` iterators in
:mod:`tables_4d`, which already drop off-lattice targets.

Public API
----------
- :func:`attacks_knight_4d(sq) -> Bitboard4D` -- O(1) lookup
- :func:`attacks_king_4d(sq) -> Bitboard4D` -- O(1) lookup
- :data:`KNIGHT_ATTACKS_4D` -- the full table (tuple of 4096
  Bitboard4D), exposed for hot loops that want to skip the
  function-call overhead
- :data:`KING_ATTACKS_4D` -- ditto for king
"""
from __future__ import annotations

from typing import Callable, Iterator, Tuple

from .. import tables_4d as _t4
from .bitboard import Bitboard4D, N_SQUARES


# Type alias for the target-iterator signature in tables_4d.
TargetFn = Callable[[int, int, int, int], Iterator[_t4.Coord]]


def _build_attack_table(target_fn: TargetFn) -> Tuple[Bitboard4D, ...]:
    """Build a (4096,) tuple of Bitboard4D: attacks[sq] = bitboard
    of squares reachable from sq on an empty board.

    Uses ``tables_4d.rc4`` to decompose the source square into
    (x, y, z, w), calls the target iterator, and re-encodes each
    target via ``tables_4d.sq4``. Off-lattice targets are dropped
    by the iterator itself.
    """
    out = []
    for s in range(N_SQUARES):
        x, y, z, w = _t4.rc4(s)
        targets = [_t4.sq4(*t) for t in target_fn(x, y, z, w)]
        out.append(Bitboard4D.from_squares(targets))
    return tuple(out)


# ---- Built-once attack tables -----------------------------------

KNIGHT_ATTACKS_4D: Tuple[Bitboard4D, ...] = _build_attack_table(
    _t4.knight4_targets
)
"""Tuple of 4096 Bitboard4D -- ``KNIGHT_ATTACKS_4D[sq]`` is the
bitboard of squares attacked by a 4D knight on ``sq``.

A 4D knight moves along **two** axes: one by ±2 and another by ±1
(per Oana & Chiru 2026 §2 movement rules). Boundary-clipped at the
lattice edges. Empirical reach counts: an interior square (e.g.,
(3,3,3,3)) reaches up to 96 squares; a corner (e.g., (0,0,0,0))
reaches significantly fewer due to clipping (8 in the corner).
"""

KING_ATTACKS_4D: Tuple[Bitboard4D, ...] = _build_attack_table(
    _t4.king4_targets
)
"""Tuple of 4096 Bitboard4D -- ``KING_ATTACKS_4D[sq]`` is the
bitboard of squares attacked by a 4D king on ``sq``.

A 4D king moves to any adjacent square in any of the four directions
along each axis (per Oana & Chiru 2026). Equivalent to "all 81
3-by-3-by-3-by-3 hypercube neighbours minus self". Interior:
3^4 - 1 = 80 reach targets. Corner (0,0,0,0): 2^4 - 1 = 15
(only neighbours with all coords in {0, 1} are valid).
"""


# ---- O(1) accessors ---------------------------------------------


def attacks_knight_4d(sq: int) -> Bitboard4D:
    """O(1) knight attack bitboard from ``sq`` on an empty 4D board.

    Equivalent to ``KNIGHT_ATTACKS_4D[sq]`` but with index validation.
    Hot loops should access ``KNIGHT_ATTACKS_4D`` directly to skip
    the bounds check.

    Parameters
    ----------
    sq : int
        Source square index in [0, 4096). Use
        :func:`tables_4d.sq4` to convert from (x, y, z, w).

    Returns
    -------
    Bitboard4D of attacked squares.

    Raises
    ------
    ValueError if ``sq`` is out of range.
    """
    if not 0 <= sq < N_SQUARES:
        raise ValueError(f"sq {sq} out of range [0, {N_SQUARES})")
    return KNIGHT_ATTACKS_4D[sq]


def attacks_king_4d(sq: int) -> Bitboard4D:
    """O(1) king attack bitboard from ``sq`` on an empty 4D board.

    See :func:`attacks_knight_4d` for the API contract.
    """
    if not 0 <= sq < N_SQUARES:
        raise ValueError(f"sq {sq} out of range [0, {N_SQUARES})")
    return KING_ATTACKS_4D[sq]


__all__ = [
    "KNIGHT_ATTACKS_4D",
    "KING_ATTACKS_4D",
    "attacks_knight_4d",
    "attacks_king_4d",
]

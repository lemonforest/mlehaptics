"""Sliding-piece attack generators for 4D chess.

Computes the attack bitboard for a rook / bishop / queen on a given
source square with a given occupancy bitboard. Walks pre-computed
rays from :mod:`rays`, accumulating squares into the output and
stopping at the first blocker (which is itself included as a
captureable square -- standard chess-engine convention).

Per the design recorded in ADR-001 (PR-7-A): same algorithmic
shape as magic bitboards (per-direction precomputed rays + per-call
occupancy walk), without the multiplicative-hash optimization that
magic bitboards add on top. The optimization can be layered in
later (or in a C port) without API change. See :mod:`rays`
docstring for the full architectural rationale.

Public API
----------
- :func:`attacks_rook_4d(sq, occupancy)` -> Bitboard4D
- :func:`attacks_bishop_4d(sq, occupancy)` -> Bitboard4D
- :func:`attacks_queen_4d(sq, occupancy)` -> Bitboard4D

Convention
----------
``occupancy`` is a Bitboard4D containing the squares occupied by
ANY piece (own and opponent). The first occupied square along a ray
is returned in the attack set (representing a captureable target);
squares beyond are excluded. The source square itself is excluded
from the attack set, regardless of occupancy.

For attack-set vs legal-move-set:
  * Attack set includes captures of friendly pieces (geometric reach).
  * Legal moves filter that against own-color occupancy at move-gen
    time (see PR-7-F's Board4D).
This split mirrors python-chess's design.
"""
from __future__ import annotations

from .bitboard import Bitboard4D, N_SQUARES
from .rays import (
    ROOK_RAYS, BISHOP_RAYS, QUEEN_RAYS,
    ROOK_DIRECTIONS, BISHOP_DIRECTIONS, QUEEN_DIRECTIONS,
)


def _walk_ray_for_attacks(ray: tuple, occupancy_bits: int) -> int:
    """Walk a single ray accumulating attack bits until a blocker.

    Returns an int (Bitboard4D._bits-shaped) of attacked squares.
    The blocker (if any) is included; squares beyond are not.
    """
    out_bits = 0
    for sq in ray:
        bit = 1 << sq
        out_bits |= bit
        if occupancy_bits & bit:
            break
    return out_bits


def _slider_attacks(sq: int,
                    occupancy: Bitboard4D,
                    ray_table: tuple,
                    n_directions: int) -> Bitboard4D:
    """Generic slider attack generator: walk every ray from sq."""
    if not 0 <= sq < N_SQUARES:
        raise ValueError(f"sq {sq} out of range [0, {N_SQUARES})")
    occ_bits = occupancy.bits
    out_bits = 0
    rays_for_sq = ray_table[sq]
    for d in range(n_directions):
        out_bits |= _walk_ray_for_attacks(rays_for_sq[d], occ_bits)
    return Bitboard4D(out_bits)


def attacks_rook_4d(sq: int, occupancy: Bitboard4D) -> Bitboard4D:
    """Squares attacked by a 4D rook at ``sq`` given the lattice
    occupancy.

    Walks the 8 rook rays from ``sq``, stopping at the first
    blocker on each ray. The blocker square is included
    (captureable target).

    Per Oana & Chiru, the 4D rook moves along exactly one axis to
    any other square on that axis; the attack graph on an empty
    board is K_8 □ K_8 □ K_8 □ K_8 (Hamming H(4,8)).

    Parameters
    ----------
    sq : int
        Source square index in [0, 4096).
    occupancy : Bitboard4D
        All occupied squares (any piece, any color). The source
        square itself need not be cleared from this; attack tables
        exclude it by construction.

    Returns
    -------
    Bitboard4D of attacked squares.

    Raises
    ------
    ValueError if ``sq`` is out of range.
    """
    return _slider_attacks(sq, occupancy, ROOK_RAYS,
                            len(ROOK_DIRECTIONS))


def attacks_bishop_4d(sq: int, occupancy: Bitboard4D) -> Bitboard4D:
    """Squares attacked by a 4D bishop at ``sq``.

    Walks the 24 bishop rays from ``sq`` (6 axis pairs × 4 sign
    combinations).

    Per Oana & Chiru, 4D bishop preserves coordinate-sum parity →
    the bishop reach graph has 2 connected components (even-parity
    and odd-parity squares). All attacks stay within one component.
    """
    return _slider_attacks(sq, occupancy, BISHOP_RAYS,
                            len(BISHOP_DIRECTIONS))


def attacks_queen_4d(sq: int, occupancy: Bitboard4D) -> Bitboard4D:
    """Squares attacked by a 4D queen at ``sq``.

    Equivalent to ``attacks_rook_4d(sq, occ) | attacks_bishop_4d(sq,
    occ)``. Walks all 32 queen rays (8 rook + 24 bishop).
    """
    return _slider_attacks(sq, occupancy, QUEEN_RAYS,
                            len(QUEEN_DIRECTIONS))


__all__ = [
    "attacks_rook_4d",
    "attacks_bishop_4d",
    "attacks_queen_4d",
]

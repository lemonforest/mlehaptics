"""Pawn move tables for 4D chess.

4D Oana-Chiru pawns (per AppliedMath 6(3):48, 2026, Definition 11)
are **axis-typed**: a pawn is either W-axis (``Pw`` / ``pw``) or
Y-axis (``Py`` / ``py``), and §3.11 makes y ↔ w a ruleset-preserving
symmetry. The "forward" direction depends on (color, axis):

  * White Pw forward = +w, black pw forward = −w.
  * White Py forward = +y, black py forward = −y.
  * (No z- or x-oriented pawns; that's a structural asymmetry of
    the rule set.)

Move types
----------
This module ships **stateless** pawn moves -- the ones that don't
depend on game history:

  * **Single push** -- one square forward along the pawn's axis.
    Always available unless the source is at the forward boundary.
  * **Diagonal capture** -- one square forward along the axis, AND
    ±1 along ONE of the other three coordinate axes. Six capture
    targets per source square (one for each (other_axis, sign)
    combo). This is the **inferred** capture rule based on
    extending the 2D diagonal-capture rule to 4D; it is gated as
    a parity test against ``python-chess4d-oana-chiru`` in PR-7-H
    (the corpus parity gate).

Game-state-dependent moves -- double-push (from the "rank 2" plane),
en passant (capture-in-passing tied to the opponent's last
double-push), and promotion (when reaching the opposite-end plane)
-- are all built at the :class:`Board4D` level (PR-7-F) where the
move history and turn structure live.

Tables
------
Eight precomputed (4096,) tuples of Bitboard4D:

  * ``PAWN_PUSH_W_WHITE[sq]``, ``PAWN_PUSH_W_BLACK[sq]``
  * ``PAWN_PUSH_Y_WHITE[sq]``, ``PAWN_PUSH_Y_BLACK[sq]``
  * ``PAWN_ATTACKS_W_WHITE[sq]``, ``PAWN_ATTACKS_W_BLACK[sq]``
  * ``PAWN_ATTACKS_Y_WHITE[sq]``, ``PAWN_ATTACKS_Y_BLACK[sq]``

Built once at import time. ~16 tuple-builds × 4096 squares each =
fast precompute (~milliseconds at the bitboard primitive level).

Public API
----------
- :func:`pawn_pushes_4d(sq, axis, color)` -> Bitboard4D
  -- O(1) accessor for single pushes.
- :func:`attacks_pawn_4d(sq, axis, color)` -> Bitboard4D
  -- O(1) accessor for diagonal captures.

Where ``axis`` ∈ {'w', 'y'} (the two pawn axes per Oana-Chiru
Def 11) and ``color`` ∈ {True (white), False (black)}.

Convention note
---------------
Pawn ``attacks`` here means "diagonal capture target squares" -- the
squares the pawn CAN capture if an opponent piece sits there. It
does NOT mean "single push squares" (which are stored separately).
This matches python-chess's split: ``Board.attacks(sq)`` for a pawn
returns just the diagonal-capture squares, not the push squares.
"""
from __future__ import annotations

from typing import Tuple

from .. import tables_4d as _t4
from .bitboard import Bitboard4D, BOARD_SIDE, N_SQUARES


# ---- Forward / capture deltas per (axis, color) -----------------

# A pawn on axis A moving as color C has:
#   forward delta along axis A: +1 (white), -1 (black)
#   diagonal capture: forward along axis A, plus ±1 along ONE of
#     the other three axes.

_OTHER_AXES = {
    'w': (0, 1, 2),  # for w-axis pawn, the other axes are x, y, z
    'y': (0, 2, 3),  # for y-axis pawn, the other axes are x, z, w
}

# Axis index (0=x, 1=y, 2=z, 3=w) for each pawn-axis name.
_AXIS_INDEX = {'w': 3, 'y': 1}


def _forward_delta(axis: str, color: bool) -> Tuple[int, int, int, int]:
    """Return the (dx, dy, dz, dw) forward delta for a pawn."""
    a = _AXIS_INDEX[axis]
    delta = [0, 0, 0, 0]
    delta[a] = 1 if color else -1
    return tuple(delta)


def _capture_deltas(axis: str,
                    color: bool) -> Tuple[Tuple[int, int, int, int], ...]:
    """Return the 6 capture deltas for a pawn on the given axis/color.

    Each delta = (forward step on pawn axis) + (±1 step on one of
    the three other axes).
    """
    fwd_axis = _AXIS_INDEX[axis]
    fwd_sign = 1 if color else -1
    out = []
    for other in _OTHER_AXES[axis]:
        for sign in (-1, +1):
            delta = [0, 0, 0, 0]
            delta[fwd_axis] = fwd_sign
            delta[other] = sign
            out.append(tuple(delta))
    return tuple(out)


# ---- Builders ---------------------------------------------------


def _build_push_table(axis: str,
                      color: bool) -> Tuple[Bitboard4D, ...]:
    """For each source square, the bitboard of single-push targets.

    Empty bitboard for sources at the forward boundary.
    """
    dx, dy, dz, dw = _forward_delta(axis, color)
    out = []
    for s in range(N_SQUARES):
        x, y, z, w = _t4.rc4(s)
        nx, ny, nz, nw = x + dx, y + dy, z + dz, w + dw
        if (0 <= nx < BOARD_SIDE and 0 <= ny < BOARD_SIDE
                and 0 <= nz < BOARD_SIDE and 0 <= nw < BOARD_SIDE):
            out.append(Bitboard4D.from_square(_t4.sq4(nx, ny, nz, nw)))
        else:
            out.append(Bitboard4D.empty())
    return tuple(out)


def _build_attack_table(axis: str,
                        color: bool) -> Tuple[Bitboard4D, ...]:
    """For each source square, the bitboard of diagonal capture
    target squares. May be empty at the forward boundary or near
    the lattice edge."""
    deltas = _capture_deltas(axis, color)
    out = []
    for s in range(N_SQUARES):
        x, y, z, w = _t4.rc4(s)
        targets = []
        for dx, dy, dz, dw in deltas:
            nx, ny, nz, nw = x + dx, y + dy, z + dz, w + dw
            if (0 <= nx < BOARD_SIDE and 0 <= ny < BOARD_SIDE
                    and 0 <= nz < BOARD_SIDE and 0 <= nw < BOARD_SIDE):
                targets.append(_t4.sq4(nx, ny, nz, nw))
        out.append(Bitboard4D.from_squares(targets))
    return tuple(out)


# ---- Built tables ----------------------------------------------

PAWN_PUSH_W_WHITE: Tuple[Bitboard4D, ...] = _build_push_table('w', True)
PAWN_PUSH_W_BLACK: Tuple[Bitboard4D, ...] = _build_push_table('w', False)
PAWN_PUSH_Y_WHITE: Tuple[Bitboard4D, ...] = _build_push_table('y', True)
PAWN_PUSH_Y_BLACK: Tuple[Bitboard4D, ...] = _build_push_table('y', False)

PAWN_ATTACKS_W_WHITE: Tuple[Bitboard4D, ...] = _build_attack_table('w', True)
PAWN_ATTACKS_W_BLACK: Tuple[Bitboard4D, ...] = _build_attack_table('w', False)
PAWN_ATTACKS_Y_WHITE: Tuple[Bitboard4D, ...] = _build_attack_table('y', True)
PAWN_ATTACKS_Y_BLACK: Tuple[Bitboard4D, ...] = _build_attack_table('y', False)


# ---- O(1) accessors --------------------------------------------


_PUSH_TABLES = {
    ('w', True): PAWN_PUSH_W_WHITE,
    ('w', False): PAWN_PUSH_W_BLACK,
    ('y', True): PAWN_PUSH_Y_WHITE,
    ('y', False): PAWN_PUSH_Y_BLACK,
}


_ATTACK_TABLES = {
    ('w', True): PAWN_ATTACKS_W_WHITE,
    ('w', False): PAWN_ATTACKS_W_BLACK,
    ('y', True): PAWN_ATTACKS_Y_WHITE,
    ('y', False): PAWN_ATTACKS_Y_BLACK,
}


def _validate(sq: int, axis: str, color: bool) -> None:
    if not 0 <= sq < N_SQUARES:
        raise ValueError(f"sq {sq} out of range [0, {N_SQUARES})")
    if axis not in _AXIS_INDEX:
        raise ValueError(f"axis {axis!r} must be 'w' or 'y'")
    if not isinstance(color, bool):
        raise TypeError(
            f"color must be bool (True=white, False=black); got {type(color).__name__}"
        )


def pawn_pushes_4d(sq: int, axis: str, color: bool) -> Bitboard4D:
    """Single-push bitboard for the given pawn at ``sq``.

    Parameters
    ----------
    sq : int
        Source square index in [0, 4096).
    axis : {'w', 'y'}
        Pawn axis. 4D Oana-Chiru pawns are axis-typed.
    color : bool
        True for white (forward = +axis), False for black
        (forward = −axis).

    Returns
    -------
    Bitboard4D with at most one set square (empty if the pawn is at
    the forward lattice boundary).

    Notes
    -----
    Double-push from the "rank 2" plane is a Board4D-level concern
    (depends on whether the pawn has moved before); not handled here.
    """
    _validate(sq, axis, color)
    return _PUSH_TABLES[(axis, color)][sq]


def attacks_pawn_4d(sq: int, axis: str, color: bool) -> Bitboard4D:
    """Diagonal-capture bitboard for the given pawn at ``sq``.

    Returns the squares the pawn CAN capture (if an opponent piece
    sits there). Independent of occupancy -- caller filters against
    own-color and opponent-color masks at move-gen time.

    Up to 6 squares (one for each combination of (other_axis, sign)
    with the pawn's forward step). Fewer when the pawn is near the
    lattice boundary.

    See module docstring for the inferred 2-axis diagonal capture
    rule and the PR-7-H parity gate that verifies it against
    python-chess4d-oana-chiru.
    """
    _validate(sq, axis, color)
    return _ATTACK_TABLES[(axis, color)][sq]


__all__ = [
    "PAWN_PUSH_W_WHITE", "PAWN_PUSH_W_BLACK",
    "PAWN_PUSH_Y_WHITE", "PAWN_PUSH_Y_BLACK",
    "PAWN_ATTACKS_W_WHITE", "PAWN_ATTACKS_W_BLACK",
    "PAWN_ATTACKS_Y_WHITE", "PAWN_ATTACKS_Y_BLACK",
    "pawn_pushes_4d",
    "attacks_pawn_4d",
]

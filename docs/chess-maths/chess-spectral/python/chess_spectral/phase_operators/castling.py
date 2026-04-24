"""§11.4.3.1 P_castle composite operator.

Castling is excluded from the base §11.2 operators because it couples
two pieces in a single move and requires global board state (attack
map on the king's path, castling rights, no prior king/rook movement).
We model it as a composite operator P_castle that layers on top of the
per-piece operators.

Structure per castle:
  - king shift: ±14 phase units (2 file steps = 2·COL_GEN)
  - rook shift: kingside -14 (h→f, 2 files); queenside +21 (a→d, 3 files)
  - phase arithmetic is built from phi() at module load, not hard-coded

Availability (which of the 4 CASTLES is legal right now) depends on:
  - board.turn matches castle.color
  - board.has_castling_rights(color) AND the specific rook still there
  - king not in check
  - squares between king and rook are empty
  - king does not pass through or land on an attacked square

For §11.4 the cleanest way to enforce the last two conditions while
keeping A/B/C in lockstep is to delegate to python-chess's is_legal()
on the canonical castling UCI move. This is a known §11.4.3.1
limitation: attack-map evaluation is outside the per-piece phase
operator set and would require a separate P_attack operator to be
fully phase-native. The §11.2 operators define the geometry of
castling; python-chess here only supplies the attack check that the
supplement flags as deferred to §11.5.

python-chess dependency:
    ``chess`` is imported lazily inside functions that need it.  The
    module-level ``CASTLES`` dict uses ``_WHITE = True`` / ``_BLACK =
    False`` explicitly (matching the stable python-chess API where
    ``chess.WHITE is True`` and ``chess.BLACK is False`` / ``chess.
    Color is bool``).  This lets ``import chess_spectral`` succeed
    without python-chess installed — 4D-only consumers (spectral-
    chess4d-oana-chiru) can drop the ``[corpus]`` extra.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import chess

from .phase_operators import phi, COL_GEN


# python-chess ``chess.Color`` is just ``bool`` (public API commitment).
# We define the two colour sentinels locally so ``CASTLES`` can be a
# module-level dict literal without ``import chess``.
_WHITE: bool = True   # == chess.WHITE
_BLACK: bool = False  # == chess.BLACK


@dataclass(frozen=True)
class CastleMove:
    color: bool  # chess.Color
    side: str    # "kingside" or "queenside"
    king_from_rc: tuple[int, int]
    king_to_rc: tuple[int, int]
    rook_from_rc: tuple[int, int]
    rook_to_rc: tuple[int, int]
    king_from_phi: int
    king_to_phi: int
    rook_from_phi: int
    rook_to_phi: int
    uci: str


def _make(color: bool, side: str,
          king_from_rc: tuple[int, int], king_to_rc: tuple[int, int],
          rook_from_rc: tuple[int, int], rook_to_rc: tuple[int, int],
          uci: str) -> CastleMove:
    return CastleMove(
        color=color, side=side,
        king_from_rc=king_from_rc, king_to_rc=king_to_rc,
        rook_from_rc=rook_from_rc, rook_to_rc=rook_to_rc,
        king_from_phi=phi(*king_from_rc),
        king_to_phi=phi(*king_to_rc),
        rook_from_phi=phi(*rook_from_rc),
        rook_to_phi=phi(*rook_to_rc),
        uci=uci,
    )


CASTLES: dict[tuple[bool, str], CastleMove] = {
    (_WHITE, "kingside"):  _make(_WHITE, "kingside",
                                 (0, 4), (0, 6), (0, 7), (0, 5),
                                 "e1g1"),
    (_WHITE, "queenside"): _make(_WHITE, "queenside",
                                 (0, 4), (0, 2), (0, 0), (0, 3),
                                 "e1c1"),
    (_BLACK, "kingside"):  _make(_BLACK, "kingside",
                                 (7, 4), (7, 6), (7, 7), (7, 5),
                                 "e8g8"),
    (_BLACK, "queenside"): _make(_BLACK, "queenside",
                                 (7, 4), (7, 2), (7, 0), (7, 3),
                                 "e8c8"),
}


# Invariants checked at import: king shift = ±2·COL_GEN = ±14.
_KING_SHIFT = 2 * COL_GEN
for _cm in CASTLES.values():
    _delta = (_cm.king_to_phi - _cm.king_from_phi) % 640
    if _cm.side == "kingside":
        assert _delta == _KING_SHIFT, (
            f"kingside king delta mismatch: {_delta} vs {_KING_SHIFT}")
    else:
        assert _delta == (-_KING_SHIFT) % 640, (
            f"queenside king delta mismatch: {_delta} vs {-_KING_SHIFT}")


def available_castles(board: "chess.Board") -> list[CastleMove]:
    """Return the castles currently legal for the side to move.

    Uses board.is_legal() on the canonical UCI move for each candidate,
    after verifying the king and rook sit on their canonical home
    squares. Without those guards, python-chess may accept the
    castling UCI as a non-castling slide of whatever piece happens to
    occupy the from-square (e.g., a rook on e1 makes "e1c1" a legal
    rook move, which would otherwise be mistaken for a legal castle).
    """
    import chess
    out: list[CastleMove] = []
    for (color, _side), castle in CASTLES.items():
        if board.turn != color:
            continue
        # Guard 1: the actual king must sit on its canonical home
        # square. Otherwise is_legal may accept the UCI as a piece
        # slide by whatever is actually sitting there.
        king_sq = chess.square(castle.king_from_rc[1],
                               castle.king_from_rc[0])
        kpiece = board.piece_at(king_sq)
        if (kpiece is None or kpiece.piece_type != chess.KING
                or kpiece.color != color):
            continue
        # Guard 2: the actual rook must sit on its canonical home
        # square. Defensive against rare FENs where castling rights
        # are set but the rook has moved or been captured.
        rook_sq = chess.square(castle.rook_from_rc[1],
                               castle.rook_from_rc[0])
        rpiece = board.piece_at(rook_sq)
        if (rpiece is None or rpiece.piece_type != chess.ROOK
                or rpiece.color != color):
            continue
        try:
            move = chess.Move.from_uci(castle.uci)
        except ValueError:
            continue
        if board.is_legal(move):
            out.append(castle)
    return out


def castle_king_destinations(board: "chess.Board",
                             mover_color: bool,
                             ) -> frozenset[tuple[int, int]]:
    """Additional king destinations contributed by P_castle.

    Returned as (row, col) tuples ready to union into the Solution
    A/B/C king destination set.
    """
    if board.turn != mover_color:
        return frozenset()
    return frozenset(c.king_to_rc for c in available_castles(board))

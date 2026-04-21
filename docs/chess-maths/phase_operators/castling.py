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
"""
from dataclasses import dataclass

import chess

from phase_operators import phi, COL_GEN


@dataclass(frozen=True)
class CastleMove:
    color: chess.Color
    side: str  # "kingside" or "queenside"
    king_from_rc: tuple[int, int]
    king_to_rc: tuple[int, int]
    rook_from_rc: tuple[int, int]
    rook_to_rc: tuple[int, int]
    king_from_phi: int
    king_to_phi: int
    rook_from_phi: int
    rook_to_phi: int
    uci: str


def _make(color: chess.Color, side: str,
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


CASTLES: dict[tuple[chess.Color, str], CastleMove] = {
    (chess.WHITE, "kingside"):  _make(chess.WHITE, "kingside",
                                      (0, 4), (0, 6), (0, 7), (0, 5),
                                      "e1g1"),
    (chess.WHITE, "queenside"): _make(chess.WHITE, "queenside",
                                      (0, 4), (0, 2), (0, 0), (0, 3),
                                      "e1c1"),
    (chess.BLACK, "kingside"):  _make(chess.BLACK, "kingside",
                                      (7, 4), (7, 6), (7, 7), (7, 5),
                                      "e8g8"),
    (chess.BLACK, "queenside"): _make(chess.BLACK, "queenside",
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


def available_castles(board: chess.Board) -> list[CastleMove]:
    """Return the castles currently legal for the side to move.

    Uses board.is_legal() on the canonical UCI move for each candidate,
    which folds together: has_castling_rights, empty path, not in
    check, and no attacked square on the king's route.
    """
    out: list[CastleMove] = []
    for (color, _side), castle in CASTLES.items():
        if board.turn != color:
            continue
        try:
            move = chess.Move.from_uci(castle.uci)
        except ValueError:
            continue
        if board.is_legal(move):
            out.append(castle)
    return out


def castle_king_destinations(board: chess.Board,
                             mover_color: chess.Color,
                             ) -> frozenset[tuple[int, int]]:
    """Additional king destinations contributed by P_castle.

    Returned as (row, col) tuples ready to union into the Solution
    A/B/C king destination set.
    """
    if board.turn != mover_color:
        return frozenset()
    return frozenset(c.king_to_rc for c in available_castles(board))

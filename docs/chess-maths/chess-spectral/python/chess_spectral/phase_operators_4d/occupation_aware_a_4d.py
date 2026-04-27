"""Solution A: hybrid post-hoc filter against a 4D oracle (§13.4).

The 4D analogue of :mod:`chess_spectral.phase_operators.occupation_aware_a`.
Where 2D filters phase-op candidates against ``python-chess.legal_moves``,
the 4D version filters against
[`python-chess4d-oana-chiru`](https://pypi.org/project/python-chess4d-oana-chiru/),
the Python reference implementation of Oana & Chiru (2026).

Solution A is the simplest validator: generate unobstructed phase
destinations from Phase B's piece operators (including Phase E's pawn
captures), then prune via the oracle's piece-specific pseudo-legal
generator. The intersection equals the oracle's own destination set
when (and only when) the phase op is complete on the empty board —
which Phase B's structural gate already verified for non-pawn pieces,
and Phase E extends to pawn captures.

This module imports ``chess4d`` lazily inside the function body. It is
therefore optional: callers that only want the pure-stdlib phase
operators should import from
:mod:`chess_spectral.phase_operators_4d.phase_operators_4d` directly.
``chess4d`` is declared in
``pyproject.toml::[project.optional-dependencies].test`` so wheels
stay free of the dependency.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from chess4d import GameState, Piece, Square4D

from .phase_operators_4d import (
    P_rook4, P_bishop4, P_queen4, P_king4, P_knight4,
    P_pawn4_white, P_pawn4_black,
    phi4,
)
from .phase_to_coords_4d import Coord4D, phase_set_to_board


# PieceType integer values mirror chess4d.types.PieceType (see §3.5–§3.10
# in the paper). We import lazily inside functions so this module's
# import cost is zero when ``chess4d`` is absent.
_PHASE_OP_BY_PIECE_TYPE_NAME = {
    "ROOK": P_rook4,
    "BISHOP": P_bishop4,
    "QUEEN": P_queen4,
    "KNIGHT": P_knight4,
    "KING": P_king4,
}


def _phase_dests_for(piece_type_name: str, origin: Coord4D) -> frozenset[Coord4D]:
    """Phase-op destinations for a non-pawn piece type at ``origin``.

    Off-board phases drop via :func:`phase_set_to_board` (the inversion
    side of the boundary clipping). Result is a set of (x, y, z, w)
    coords ⊂ [0, 7]^4. Pawns are handled in
    :func:`_phase_dests_for_pawn` since they require ``(color, axis,
    on_starting_rank)`` parameters.
    """
    op = _PHASE_OP_BY_PIECE_TYPE_NAME.get(piece_type_name)
    if op is None:
        raise ValueError(
            f"no phase operator for piece type {piece_type_name!r}; "
            "supported: ROOK, BISHOP, QUEEN, KNIGHT, KING, PAWN."
        )
    x, y, z, w = origin
    return phase_set_to_board(op(phi4(x, y, z, w)))


def _phase_dests_for_pawn(
    origin: Coord4D, *, color_white: bool, axis: str, on_starting_rank: bool,
) -> frozenset[Coord4D]:
    """Pawn phase destinations including diagonal captures (§3.10
    Def 12 + Def 13).

    ``axis`` is "w" or "y" (chess4d's PawnAxis name lowercased).
    Off-board candidates drop via :func:`phase_set_to_board`.
    """
    x, y, z, w = origin
    op = P_pawn4_white if color_white else P_pawn4_black
    phases = op(
        phi4(x, y, z, w),
        axis=axis,  # type: ignore[arg-type]
        on_starting_rank=on_starting_rank,
        include_captures=True,
    )
    return phase_set_to_board(phases)


def occupation_aware_moves_a_4d(
    state: "GameState",
    origin: "Square4D",
    piece: "Piece",
) -> frozenset[Coord4D]:
    """Pseudo-legal destinations from ``origin`` for ``piece`` in
    ``state``, computed as ``phase_op(origin) ∩ oracle(origin)``.

    The intersection prunes off-board phases (handled by
    ``phase_set_to_board``) and occupancy-blocked squares (handled by
    the oracle's per-piece generator). For Solution A the test gate
    asserts ``occupation_aware_moves_a_4d(...) == oracle_dests``,
    which holds iff the phase op is **complete** on the empty board
    (Phase B verified) and the oracle and phase op agree on which
    destinations occupancy / capture rules permit.

    Parameters
    ----------
    state : chess4d.GameState
        Full game state (board + side-to-move + castling rights + ep).
        Only the board is consulted by Solution A; state is passed
        through to the oracle's generator for forward compatibility.
    origin : chess4d.Square4D
        Square holding ``piece``; not re-verified here.
    piece : chess4d.Piece
        The piece being moved. Its ``piece_type`` (and for pawns,
        ``pawn_axis`` and color) selects which phase operator and
        oracle generator pair to call.

    Returns
    -------
    frozenset[tuple[int, int, int, int]]
        Destination coordinates in [0,7]^4. Empty if the piece has no
        legal pseudo-moves from this origin.
    """
    # Lazy import — keeps ``occupation_aware_a_4d`` importable without
    # ``chess4d`` installed; only the function call path requires it.
    import chess4d
    from chess4d.types import PawnAxis, PieceType

    pt = piece.piece_type
    color = piece.color
    origin_coord: Coord4D = (origin.x, origin.y, origin.z, origin.w)

    # 1. Phase-op candidates (unobstructed reach from origin).
    if pt == PieceType.PAWN:
        # Pawn axis carried by the piece per O&C §3.10 Def 11.
        if piece.pawn_axis is None:
            raise ValueError(
                "PAWN piece must carry a pawn_axis (W or Y) per O&C "
                "Def 11."
            )
        axis_str = "w" if piece.pawn_axis == PawnAxis.W else "y"
        # Starting-rank check: white pawns start at axis-coord 1;
        # black pawns at axis-coord 6 (paper §3.10 Def 12 + the
        # 0-based [0..7] convention; the paper's 1-based "rank 2 /
        # rank 7" maps to 0-based 1 / 6).
        axis_index = int(piece.pawn_axis)
        on_starting_rank = origin[axis_index] == (
            1 if color == chess4d.Color.WHITE else 6
        )
        phase_dests = _phase_dests_for_pawn(
            origin_coord,
            color_white=(color == chess4d.Color.WHITE),
            axis=axis_str,
            on_starting_rank=on_starting_rank,
        )
    else:
        phase_dests = _phase_dests_for(pt.name, origin_coord)

    # 2. Oracle: chess4d's piece-specific pseudo-legal generator. Each
    #    oracle module exposes ``<piece>_moves(origin, color, board)``
    #    yielding ``Move4D`` objects whose ``.to_sq`` is the destination.
    oracle_fn = {
        PieceType.ROOK:   chess4d.rook_moves,
        PieceType.BISHOP: chess4d.bishop_moves,
        PieceType.QUEEN:  chess4d.queen_moves,
        PieceType.KNIGHT: chess4d.knight_moves,
        PieceType.KING:   chess4d.king_moves,
        PieceType.PAWN:   chess4d.pawn_moves,
    }[pt]
    oracle_dests = frozenset(
        (m.to_sq.x, m.to_sq.y, m.to_sq.z, m.to_sq.w)
        for m in oracle_fn(origin, color, state.board)
    )

    # 3. Solution A: intersect. The intersection equals oracle_dests
    #    iff the phase op is complete on the empty board (Phase B
    #    structural gate confirmed this for non-pawns; Phase E
    #    extends the contract to pawn captures).
    return phase_dests & oracle_dests

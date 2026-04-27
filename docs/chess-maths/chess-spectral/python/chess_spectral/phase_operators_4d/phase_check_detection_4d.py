"""§13.5 reverse phase-cast: is_check via inverse attack operators.

The 4D analogue of :mod:`chess_spectral.phase_operators.phase_check_detection`.
Casts the inverse attack operators outward from each of the moving
side's kings — there are up to 28 per side at startpos in the 4D
position per the paper's §3.3 — and intersects with
opponent-occupation-by-piece-type.

**Multi-king semantics (paper §3.4 Def 3, Remark 1).** Per Oana &
Chiru, a position is "in check" if *any* of the moving side's kings
is attacked. Saving only one of several attacked kings is not
sufficient to escape check. ``phasecast_is_check_4d_no_pawns``
iterates all of the side's kings and returns True on the first
attack found.

**Pawn attackers.** This module currently handles non-pawn attackers
only. Pawn captures are Phase E (gated by
``P_pawn4_white(include_captures=True)`` raising NotImplementedError).
The ``phasecast_is_check_4d_no_pawns`` name is deliberately suffixed
to make this scope visible at every call site. Phase E will add
``phasecast_is_check_4d`` (no suffix) which lifts pawn capture phases
into the reverse-cast.

The Phase D test compares this function against a naive oracle that
*also* excludes pawn attackers (using ``chess4d``'s per-piece
generators with PAWN skipped). Correctness equivalence is checked on
a 50-position seeded corpus.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from chess4d import GameState, Color

from .phase_operators_4d import (
    AXIS_GENS, MODULUS_4D, P_king4, P_knight4, phi4,
)
from .phase_to_coords_4d import PHI_TO_XYZW


def phasecast_is_check_4d_no_pawns(
    state: "GameState",
    color: "Color",
) -> bool:
    """Return True if any of ``color``'s kings is attacked by a
    non-pawn enemy piece in ``state``.

    Reverse-cast structure:
      1. Build a phase-keyed lookup for enemy pieces by type.
      2. For each friendly king at phase ``φ_k``:
         a. Check leaper attackers (knight, king) via direct phase-set
            intersection: ``P_knight4(φ_k) ∩ enemy_knights``,
            ``P_king4(φ_k) ∩ enemy_kings``.
         b. Walk slider rays outward from ``φ_k``, stopping at the
            first occupant on each ray; if the blocker is an
            attacking rook/queen (axis ray) or bishop/queen (plane
            ray), it's a check.
      3. Return True on the first attack found; False if all kings
         are safe.

    Pawn attackers are deliberately not considered — see Phase E
    (``PHASE_OPERATOR_SUPPLEMENT_4D.md`` §13.6) for the open question
    on Oana & Chiru Definition 11 capture geometry.

    Parameters
    ----------
    state : chess4d.GameState
        Full state. Only the board is consulted.
    color : chess4d.Color
        Side whose kings we're checking.

    Returns
    -------
    bool
        True if any king of ``color`` is attacked by a non-pawn
        enemy piece; False otherwise.
    """
    # Lazy import to keep the module importable without chess4d.
    import chess4d
    from chess4d.types import PieceType

    opposite = chess4d.Color(1 - color)

    # Friendly kings as (x, y, z, w).
    king_squares = list(chess4d.kings_of(color, state.board))
    if not king_squares:
        # Side has no kings — vacuously not in check.
        return False

    # Enemy pieces by type, keyed by phase. Plus a phase->color map
    # for ray-blocker detection (any occupant blocks a slider; only
    # enemy occupants attack).
    enemy_phases_by_type: dict[PieceType, set[int]] = {
        PieceType.ROOK:   set(),
        PieceType.BISHOP: set(),
        PieceType.QUEEN:  set(),
        PieceType.KNIGHT: set(),
        PieceType.KING:   set(),
    }
    occupation: dict[int, "Color"] = {}

    for sq, piece in state.board.pieces_of(opposite):
        p = phi4(sq.x, sq.y, sq.z, sq.w)
        if piece.piece_type in enemy_phases_by_type:
            enemy_phases_by_type[piece.piece_type].add(p)
        occupation[p] = opposite
    for sq, piece in state.board.pieces_of(color):
        p = phi4(sq.x, sq.y, sq.z, sq.w)
        occupation[p] = color

    enemy_rooks_or_queens = (
        enemy_phases_by_type[PieceType.ROOK]
        | enemy_phases_by_type[PieceType.QUEEN]
    )
    enemy_bishops_or_queens = (
        enemy_phases_by_type[PieceType.BISHOP]
        | enemy_phases_by_type[PieceType.QUEEN]
    )

    for king_sq in king_squares:
        king_phi = phi4(king_sq.x, king_sq.y, king_sq.z, king_sq.w)

        # Leapers: direct phase-set intersection.
        if P_knight4(king_phi) & enemy_phases_by_type[PieceType.KNIGHT]:
            return True
        if P_king4(king_phi) & enemy_phases_by_type[PieceType.KING]:
            return True

        # Sliders: walk rays outward, stop at first occupant. The
        # rook walks 4 axes × 2 directions; the bishop walks 6 plane
        # pairs × 4 sign combos.
        if _slider_ray_hits_king(
            king_phi, occupation,
            tuple(s * g for g in AXIS_GENS for s in (-1, +1)),
            enemy_rooks_or_queens,
        ):
            return True

        # Bishop ray directions: ±g_i ± g_j for i < j.
        bishop_dirs = tuple(
            si * AXIS_GENS[i] + sj * AXIS_GENS[j]
            for i in range(4) for j in range(i + 1, 4)
            for si in (-1, +1) for sj in (-1, +1)
        )
        if _slider_ray_hits_king(
            king_phi, occupation, bishop_dirs, enemy_bishops_or_queens,
        ):
            return True

    return False


def _slider_ray_hits_king(
    king_phi: int,
    occupation: dict[int, "Color"],
    directions: tuple[int, ...],
    attacker_phases: set[int],
) -> bool:
    """Walk each ray outward from ``king_phi`` for up to 7 steps; if
    the first blocker on any ray is in ``attacker_phases``, return
    True.

    Bounded at 7 steps per ray. Adapted from the 2D analogue in
    ``phase_check_detection.py:_sliding_ray_hits_king``; the only
    differences are the larger direction set (24 bishop rays vs 4
    in 2D) and the larger phase modulus.
    """
    for d in directions:
        for k in range(1, 8):
            p = (king_phi + k * d) % MODULUS_4D
            if p not in PHI_TO_XYZW:
                break  # off-board; ray ends
            if p in occupation:
                if p in attacker_phases:
                    return True
                break  # blocker; ray ends regardless of color
    return False


def move_leaves_king_in_check_4d_no_pawns(
    state: "GameState",
    move: "Move4D",
) -> bool:
    """Return True if applying ``move`` would leave any of the moving
    side's kings attacked by a non-pawn enemy piece.

    Implemented as: push the move on a copy of the state, run
    ``phasecast_is_check_4d_no_pawns`` on the post-move state, pop.

    The ``_no_pawns`` suffix follows
    ``phasecast_is_check_4d_no_pawns`` — Phase E will add the
    pawn-aware form.
    """
    state.push(move)
    try:
        # After ``push``, ``side_to_move`` is the *opponent*. The
        # mover (whose kings we're checking) is the previous side.
        import chess4d
        mover_color = chess4d.Color(1 - state.side_to_move)
        return phasecast_is_check_4d_no_pawns(state, mover_color)
    finally:
        state.pop()

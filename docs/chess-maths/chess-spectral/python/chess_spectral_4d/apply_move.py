"""Move-application surface for 4D chess game state.

This module provides :func:`apply_move`, the chess-spectral 1.4.0
canonical entry point for advancing a :class:`GameState4D` by one ply.
Per the §17.3 contract:

    apply_move(state, from_sq, to_sq, *, promote_to='Q')

* ``promote_to`` is the optional promotion-target piece letter
  (``'Q'``, ``'R'``, ``'B'``, ``'N'``); the default ``'Q'`` is back-
  compatible with the v1.3.x signature that auto-queened. Color is
  inferred from the moving pawn (white pawns get the upper-case
  variant, black pawns get lower-case).
* Promotion is triggered iff the moving piece is a pawn AND the
  destination square is on the appropriate "promotion rank" for the
  pawn's axis (the maximal w- or y- coordinate from the pawn's
  perspective; see :func:`_is_promotion_dest`).
* If ``promote_to`` is supplied for a non-promotion move, it is
  silently ignored (matches python-chess behavior; the consumer can
  pass ``'Q'`` unconditionally without an extra branch).

The module deliberately does NOT attempt to validate move legality —
that is the job of the :mod:`chess_spectral.phase_operators_4d`
machinery (already shipped in v1.3.0). ``apply_move`` is the
*application* surface: it advances the position dict by one move,
records the ply, and updates the half-move clock + side-to-move byte.

This separation matches v1.3.0's design where the phase operators
generate candidate move sets but do not mutate state; v1.4.0 fills
in the missing "now play this move" half.

If 4D legal-move generation is wired in by a later milestone (v1.5+),
``apply_move`` may grow an optional pre-validation pass — but the
core signature stays the same.
"""

from __future__ import annotations

from typing import Optional

from chess_spectral import fen_4d as _fen_4d

from chess_spectral_4d.move_history import (
    Coord4D,
    GameState4D,
    Move4D,
    PieceValue,
    coord_to_sq,
)


# ─── Promotion-piece validation ─────────────────────────────────────

_VALID_PROMO_PIECES = frozenset({"Q", "R", "B", "N"})
"""Allowed `promote_to` values. Color is inferred from the pawn.

King is excluded (FIDE Article 3.7e) and pawn is excluded (FIDE
Article 3.7e — pawn cannot remain a pawn). Lower-case forms are
*not* accepted; the caller passes the upper-case piece letter and
the moving-pawn color provides the case.
"""


def _validate_promote_to(promote_to: str) -> str:
    """Raise ``ValueError`` if ``promote_to`` isn't one of the four
    legal promotion targets. Returns the validated value (uppercase).
    """
    if not isinstance(promote_to, str):
        raise ValueError(
            f"promote_to must be a string, got {type(promote_to).__name__}"
        )
    norm = promote_to.upper()
    if norm not in _VALID_PROMO_PIECES:
        raise ValueError(
            f"promote_to must be one of "
            f"{sorted(_VALID_PROMO_PIECES)}, got {promote_to!r}"
        )
    return norm


# ─── Pawn / promotion helpers ───────────────────────────────────────

def _is_pawn(value: PieceValue) -> bool:
    """True if ``value`` is a pawn (tuple form or legacy single char)."""
    if isinstance(value, tuple):
        return len(value) == 2 and value[0] in ("P", "p")
    return value in ("P", "p")


def _pawn_color(value: PieceValue) -> str:
    """Return ``'P'`` (white) or ``'p'`` (black) for a pawn value."""
    if isinstance(value, tuple):
        return value[0]
    return value  # legacy


def _pawn_axis(value: PieceValue) -> str:
    """Return ``'y'`` or ``'w'`` for a pawn value. Falls back to
    ``'w'`` for legacy single-char pawns (matches v1.0 behavior)."""
    if isinstance(value, tuple):
        return value[1]
    return "w"  # legacy


def _is_promotion_dest(
    pawn: PieceValue, to_coord: Coord4D,
) -> bool:
    """Determine whether ``to_coord`` is a promotion square for the
    given pawn.

    For Oana & Chiru's 4D pawn rules (Definition 11), pawns advance
    along axis ``y`` or ``w``. White pushes in the positive direction
    (target rank = 7); black pushes in the negative direction (target
    rank = 0). When the pawn arrives at the corresponding rank along
    its push axis, it must promote.
    """
    color = _pawn_color(pawn)
    axis = _pawn_axis(pawn)
    x, y, z, w = to_coord
    if axis == "w":
        target_rank = w
    else:  # axis == 'y'
        target_rank = y
    if color == "P":  # white pushes toward rank 7
        return target_rank == 7
    return target_rank == 0  # black pushes toward rank 0


def _make_promoted_value(
    promote_to: str, pawn: PieceValue,
) -> PieceValue:
    """Build the post-promotion piece value. The promoted piece
    inherits the moving pawn's color (case-folded onto the upper-case
    ``promote_to`` letter). Promotion always yields a non-pawn so the
    output is a single-char string, never a tuple.
    """
    color = _pawn_color(pawn)
    if color == "P":
        return promote_to
    return promote_to.lower()


# ─── apply_move ─────────────────────────────────────────────────────

def apply_move(
    state: GameState4D,
    from_sq: Coord4D,
    to_sq: Coord4D,
    *,
    promote_to: str = "Q",
) -> Move4D:
    """Advance ``state`` by one ply. Returns the recorded move.

    Parameters
    ----------
    state
        Live :class:`GameState4D`. Mutated in place.
    from_sq, to_sq
        4D coordinates ``(x, y, z, w)`` with each component in
        ``[0, 7]``. See :func:`chess_spectral_4d.move_history.coord_to_sq`.
    promote_to
        Promotion-target piece letter. Default ``'Q'`` matches the
        v1.3.x silent auto-queen behavior. Accepted: ``'Q'``, ``'R'``,
        ``'B'``, ``'N'`` (case-insensitive). Color is inferred from
        the moving pawn. Ignored for non-promotion moves.

    Returns
    -------
    Move4D
        The recorded move. The mutated ``state.position`` reflects the
        post-move snapshot; ``state.history`` has the new ply appended;
        ``state.history.side_to_move`` has flipped; the half-move
        clock has been updated.

    Raises
    ------
    ValueError
        If ``promote_to`` isn't ``Q``/``R``/``B``/``N``, if a coord
        component is out of range, or if there is no piece on
        ``from_sq``.
    """
    promote_to = _validate_promote_to(promote_to)
    src_idx = coord_to_sq(from_sq)
    dst_idx = coord_to_sq(to_sq)

    if src_idx not in state.position:
        raise ValueError(
            f"no piece on origin square {from_sq}; cannot apply_move"
        )
    moving = state.position[src_idx]
    captured: Optional[PieceValue] = state.position.get(dst_idx)

    is_pawn_move = _is_pawn(moving)
    is_capture = captured is not None

    # Determine post-move piece — promotion may replace the pawn.
    if is_pawn_move and _is_promotion_dest(moving, to_sq):
        post_move_piece = _make_promoted_value(promote_to, moving)
        recorded_promo: Optional[str] = promote_to
    else:
        post_move_piece = moving
        recorded_promo = None

    # Mutate the position dict.
    del state.position[src_idx]
    state.position[dst_idx] = post_move_piece

    # Record + bookkeep via MoveHistory4D.
    fen4_after = _fen_4d.serialize(state.position)
    record = state.history.append(
        from_sq=from_sq,
        to_sq=to_sq,
        piece=moving,
        promote_to=recorded_promo,
        captured_piece=captured,
        fen4_after=fen4_after,
        position_after=state.position,
        is_pawn_move=is_pawn_move,
        is_capture=is_capture,
    )
    return record

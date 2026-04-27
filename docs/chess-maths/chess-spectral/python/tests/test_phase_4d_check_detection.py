"""Phase D structural gate — ``phasecast_is_check_4d_no_pawns``
matches a naive non-pawn check oracle on a 50-position seeded corpus.

The 4D analogue of 2D's ``test_phase_check_detection.py``. Where 2D's
oracle is ``python-chess.Board.is_check()``, the 4D oracle here is a
naive iterator built from
[`python-chess4d-oana-chiru`](https://pypi.org/project/python-chess4d-oana-chiru/)'s
per-piece pseudo-legal generators.

Pawn attackers are excluded from both sides of the comparison —
Phase E adds the pawn-aware oracle path. See
``PHASE_OPERATOR_SUPPLEMENT_4D.md`` §13.6.

For each position in the corpus and each color (W and B):

    phasecast_is_check_4d_no_pawns(state, color)
        ==
    _naive_non_pawn_check(state, color)

where ``_naive_non_pawn_check`` enumerates enemy non-pawn pieces and
asks the oracle "does this piece attack any of color's kings?".
"""
from __future__ import annotations

import random

import pytest

chess4d = pytest.importorskip(
    "chess4d",
    reason="Phase D requires python-chess4d-oana-chiru. Install with "
           "`pip install chess-spectral[test]` or "
           "`pip install python-chess4d-oana-chiru`.",
)

from chess_spectral.phase_operators_4d import (
    move_leaves_king_in_check_4d,
    move_leaves_king_in_check_4d_no_pawns,
    phasecast_is_check_4d,
    phasecast_is_check_4d_no_pawns,
)


# ─── corpus generator (same shape as Phase C) ───────────────────────


def _seeded_random_position(seed: int, max_plies: int) -> "chess4d.GameState":
    gs = chess4d.initial_position()
    rng = random.Random(seed)
    for _ in range(max_plies):
        if (gs.is_checkmate() or gs.is_stalemate()
                or gs.is_fifty_move_draw()
                or gs.is_threefold_repetition()):
            break
        moves = list(gs.legal_moves())
        if not moves:
            break
        gs.push(rng.choice(moves))
    return gs


def _corpus_positions(n: int) -> list["chess4d.GameState"]:
    return [
        _seeded_random_position(seed=i, max_plies=1 + (i % 6))
        for i in range(n)
    ]


_CORPUS_SIZE = 50
_CORPUS = _corpus_positions(_CORPUS_SIZE)


# ─── naive non-pawn check oracle (the gate) ─────────────────────────


_PIECE_GENS = {
    chess4d.types.PieceType.ROOK:   chess4d.rook_moves,
    chess4d.types.PieceType.BISHOP: chess4d.bishop_moves,
    chess4d.types.PieceType.QUEEN:  chess4d.queen_moves,
    chess4d.types.PieceType.KNIGHT: chess4d.knight_moves,
    chess4d.types.PieceType.KING:   chess4d.king_moves,
}


def _naive_non_pawn_check(state, color) -> bool:
    """Reference oracle: True iff any non-pawn enemy piece reaches any
    of ``color``'s kings.

    Excludes pawn attackers — matches the scope of
    ``phasecast_is_check_4d_no_pawns``.
    """
    opposite = chess4d.Color(1 - color)
    king_squares = set(chess4d.kings_of(color, state.board))
    if not king_squares:
        return False
    for sq, piece in state.board.pieces_of(opposite):
        if piece.piece_type == chess4d.types.PieceType.PAWN:
            continue
        for move in _PIECE_GENS[piece.piece_type](sq, opposite, state.board):
            if move.to_sq in king_squares:
                return True
    return False


def _naive_full_check(state, color) -> bool:
    """Reference oracle for the pawn-aware case: True iff any enemy
    piece (including pawns) reaches any of ``color``'s kings.

    Equivalent to ``chess4d.in_check(color, state.board)`` (verified
    by ``test_naive_full_check_matches_chess4d_in_check`` below); we
    use this naive form so the comparison loop is symmetric with the
    ``_no_pawns`` path.
    """
    opposite = chess4d.Color(1 - color)
    king_squares = set(chess4d.kings_of(color, state.board))
    if not king_squares:
        return False
    for sq, piece in state.board.pieces_of(opposite):
        gen = (chess4d.pawn_moves
               if piece.piece_type == chess4d.types.PieceType.PAWN
               else _PIECE_GENS[piece.piece_type])
        for move in gen(sq, opposite, state.board):
            if move.to_sq in king_squares:
                return True
    return False


# ─── parametrized gate ──────────────────────────────────────────────


@pytest.mark.parametrize("color", [chess4d.Color.WHITE, chess4d.Color.BLACK])
@pytest.mark.parametrize("state_idx", range(_CORPUS_SIZE))
def test_phasecast_no_pawns_matches_naive_oracle(state_idx, color):
    """Reverse-cast and naive enumerator agree on every (position, color)
    pair in the seeded corpus.

    On failure the message reports which kings see an attacker the
    other path missed — actionable for debugging.
    """
    state = _CORPUS[state_idx]
    cast_result = phasecast_is_check_4d_no_pawns(state, color)
    naive_result = _naive_non_pawn_check(state, color)
    assert cast_result == naive_result, (
        f"state={state_idx} color={color.name}: "
        f"phasecast={cast_result} naive={naive_result}"
    )


@pytest.mark.parametrize("color", [chess4d.Color.WHITE, chess4d.Color.BLACK])
@pytest.mark.parametrize("state_idx", range(_CORPUS_SIZE))
def test_phasecast_pawn_aware_matches_naive_oracle(state_idx, color):
    """Pawn-aware reverse-cast vs full naive enumerator on the seeded
    corpus.
    """
    state = _CORPUS[state_idx]
    cast_result = phasecast_is_check_4d(state, color)
    naive_result = _naive_full_check(state, color)
    assert cast_result == naive_result, (
        f"state={state_idx} color={color.name}: "
        f"phasecast_full={cast_result} naive_full={naive_result}"
    )


@pytest.mark.parametrize("color", [chess4d.Color.WHITE, chess4d.Color.BLACK])
@pytest.mark.parametrize("state_idx", range(min(10, _CORPUS_SIZE)))
def test_naive_full_check_matches_chess4d_in_check(state_idx, color):
    """Sanity: our naive oracle agrees with chess4d's own ``in_check``.

    Restricted to the first 10 positions to keep the run fast — the
    oracle correctness only needs a small sample to be confident.
    Failures here mean my naive enumerator missed something, not
    that the phasecast is wrong.
    """
    state = _CORPUS[state_idx]
    naive = _naive_full_check(state, color)
    chess4d_oracle = chess4d.in_check(color, state.board)
    assert naive == chess4d_oracle, (
        f"state={state_idx} color={color.name}: "
        f"naive={naive} chess4d.in_check={chess4d_oracle}"
    )


# ─── targeted check-detection scenarios ─────────────────────────────


def test_initial_position_no_check_either_side():
    """The 4D startpos has no piece attacking any king (paper §3.3).

    Both colors should return False from both functions.
    """
    gs = chess4d.initial_position()
    for color in (chess4d.Color.WHITE, chess4d.Color.BLACK):
        assert not phasecast_is_check_4d_no_pawns(gs, color)
        assert not _naive_non_pawn_check(gs, color)


def test_no_kings_returns_false():
    """If a color has no kings on the board, phasecast returns False
    (vacuous). Tests the boundary case used in pathological corpus
    positions where one side might lose all kings."""
    gs = chess4d.initial_position()
    # Remove all white kings.
    white_kings = list(chess4d.kings_of(chess4d.Color.WHITE, gs.board))
    for sq in white_kings:
        gs.board.remove(sq)
    assert not phasecast_is_check_4d_no_pawns(gs, chess4d.Color.WHITE)


# ─── targeted check constructions ───────────────────────────────────
#
# 4D random-walk corpora rarely produce non-pawn checks in 1–6 plies
# because:
#   * 4D legal_moves filters out moves that leave any of the mover's
#     ~28 kings attacked (paper §3.4 Def 3 — multi-king legality).
#   * Random openings don't naturally open attack lanes to any king.
#
# So the random corpus exercises only the False branch of phasecast.
# Targeted constructions below exercise the True branch — handcrafted
# positions where a black slider or leaper attacks a white king.


def _make_check_position_rook_on_x_axis():
    """Construct a position where a black rook attacks a white king
    along the x-axis. Clears intermediate squares so the rook ray is
    unobstructed."""
    gs = chess4d.initial_position()
    # Target the white king at (4, 0, 5, 4). Sweep the x-axis on its
    # rank+slice: clear every (i, 0, 5, 4) for i ∈ {0..3, 5..7} and
    # place a black rook somewhere on it.
    king_sq = chess4d.Square4D(4, 0, 5, 4)
    assert gs.board.occupant(king_sq).piece_type == chess4d.types.PieceType.KING
    for i in range(8):
        if i == 4:
            continue
        sq = chess4d.Square4D(i, 0, 5, 4)
        if gs.board.occupant(sq) is not None:
            gs.board.remove(sq)
    gs.board.place(
        chess4d.Square4D(0, 0, 5, 4),
        chess4d.Piece(chess4d.Color.BLACK, chess4d.types.PieceType.ROOK),
    )
    return gs


def _make_check_position_knight_leap():
    """Construct a position where a black knight attacks a white king
    by a (2, 1)-leap. Knight is a leaper — no path-clearing needed."""
    gs = chess4d.initial_position()
    king_sq = chess4d.Square4D(4, 0, 5, 4)
    assert gs.board.occupant(king_sq).piece_type == chess4d.types.PieceType.KING
    # Knight at (2, 1, 5, 4) attacks (4, 0, 5, 4): Δ = (+2, -1, 0, 0). ✓
    target = chess4d.Square4D(2, 1, 5, 4)
    if gs.board.occupant(target) is not None:
        gs.board.remove(target)
    gs.board.place(
        target,
        chess4d.Piece(chess4d.Color.BLACK, chess4d.types.PieceType.KNIGHT),
    )
    return gs


def _make_check_position_bishop_xy_diagonal():
    """Black bishop on the xy-plane diagonal of a white king."""
    gs = chess4d.initial_position()
    king_sq = chess4d.Square4D(4, 0, 5, 4)
    assert gs.board.occupant(king_sq).piece_type == chess4d.types.PieceType.KING
    # Sweep the (4+k, 0+k, 5, 4) diagonal for k ∈ 1..3 (we only need
    # a clear path to one bishop). Then place bishop at (5, 1, 5, 4).
    for k in range(1, 4):
        sq = chess4d.Square4D(4 + k, k, 5, 4)
        if not sq.in_bounds():
            continue
        if gs.board.occupant(sq) is not None:
            gs.board.remove(sq)
    gs.board.place(
        chess4d.Square4D(5, 1, 5, 4),
        chess4d.Piece(chess4d.Color.BLACK, chess4d.types.PieceType.BISHOP),
    )
    return gs


def _make_check_position_queen_zw_diagonal():
    """Black queen on the zw-plane diagonal of a white king (queen as
    bishop)."""
    gs = chess4d.initial_position()
    king_sq = chess4d.Square4D(4, 0, 5, 4)
    # Queen at (4, 0, 6, 5): Δ = (0, 0, +1, +1) — zw-plane diagonal.
    target = chess4d.Square4D(4, 0, 6, 5)
    if gs.board.occupant(target) is not None:
        gs.board.remove(target)
    gs.board.place(
        target,
        chess4d.Piece(chess4d.Color.BLACK, chess4d.types.PieceType.QUEEN),
    )
    return gs


def _make_check_position_blocked_rook():
    """Black rook on the king's x-axis, but with a friendly piece in
    between — should NOT trigger check (slider blocked)."""
    gs = chess4d.initial_position()
    king_sq = chess4d.Square4D(4, 0, 5, 4)
    assert gs.board.occupant(king_sq).piece_type == chess4d.types.PieceType.KING
    # Clear x ∈ {0, 1, 3} (leave x=2 occupied with a friendly knight),
    # place black rook at x=0.
    # Actually simpler: leave the startpos pieces alone and use them
    # as the blocker. The white knight at (1, 0, 5, 4) blocks any
    # rook at x=0.
    if gs.board.occupant(chess4d.Square4D(0, 0, 5, 4)) is not None:
        gs.board.remove(chess4d.Square4D(0, 0, 5, 4))
    gs.board.place(
        chess4d.Square4D(0, 0, 5, 4),
        chess4d.Piece(chess4d.Color.BLACK, chess4d.types.PieceType.ROOK),
    )
    # Confirm there's a blocker at x=1.
    assert gs.board.occupant(chess4d.Square4D(1, 0, 5, 4)) is not None
    return gs


_TARGETED = {
    "rook_on_x_axis": _make_check_position_rook_on_x_axis(),
    "knight_leap": _make_check_position_knight_leap(),
    "bishop_xy_diagonal": _make_check_position_bishop_xy_diagonal(),
    "queen_zw_diagonal": _make_check_position_queen_zw_diagonal(),
    "blocked_rook": _make_check_position_blocked_rook(),
}

_TARGETED_EXPECTED = {
    "rook_on_x_axis":     True,
    "knight_leap":        True,
    "bishop_xy_diagonal": True,
    "queen_zw_diagonal":  True,
    "blocked_rook":       False,  # blocked by friendly piece
}


@pytest.mark.parametrize("name", sorted(_TARGETED.keys()))
def test_targeted_check_constructions(name):
    """Hand-built positions where a non-pawn enemy attacks (or is
    blocked from attacking) a white king. Phasecast and naive
    oracle must both agree with the expected outcome.

    Failures here narrow the bug to a specific piece type or ray
    direction — actionable.
    """
    state = _TARGETED[name]
    expected = _TARGETED_EXPECTED[name]
    cast = phasecast_is_check_4d_no_pawns(state, chess4d.Color.WHITE)
    naive = _naive_non_pawn_check(state, chess4d.Color.WHITE)
    assert cast == expected, (
        f"{name}: phasecast={cast} expected={expected} (naive={naive})"
    )
    assert naive == expected, (
        f"{name}: naive={naive} expected={expected} (phasecast={cast})"
    )


def test_targeted_constructions_exercise_true_branch():
    """Sanity: the targeted set covers BOTH branches of phasecast."""
    true_count = sum(1 for v in _TARGETED_EXPECTED.values() if v)
    false_count = sum(1 for v in _TARGETED_EXPECTED.values() if not v)
    assert true_count >= 3 and false_count >= 1, (
        "targeted set should exercise both True and False branches"
    )


# ─── pawn-attacker constructions (Phase E) ──────────────────────────


def _make_pawn_check_w_axis():
    """Black W-pawn attacks a white king via the xw-plane diagonal.

    The white king at (4, 0, 5, 4) is attacked by a black W-axis pawn
    at (5, 0, 5, 5) — pawn captures at (5-1, 0, 5, 5-1) = (4, 0, 5, 4)
    by O&C §3.10 Def 13 (forward sign -1 for black, |Δx|=1).
    """
    gs = chess4d.initial_position()
    king_sq = chess4d.Square4D(4, 0, 5, 4)
    assert gs.board.occupant(king_sq).piece_type == chess4d.types.PieceType.KING
    pawn_sq = chess4d.Square4D(5, 0, 5, 5)
    if gs.board.occupant(pawn_sq) is not None:
        gs.board.remove(pawn_sq)
    gs.board.place(
        pawn_sq,
        chess4d.Piece(
            chess4d.Color.BLACK,
            chess4d.types.PieceType.PAWN,
            pawn_axis=chess4d.types.PawnAxis.W,
        ),
    )
    return gs


def _make_pawn_check_y_axis():
    """Black Y-pawn attacks a white king via the xy-plane diagonal.

    Black Y-pawn at (5, 1, 5, 4) captures at (5±1, 0, 5, 4); the
    -x diagonal hits the white king at (4, 0, 5, 4).
    """
    gs = chess4d.initial_position()
    king_sq = chess4d.Square4D(4, 0, 5, 4)
    assert gs.board.occupant(king_sq).piece_type == chess4d.types.PieceType.KING
    pawn_sq = chess4d.Square4D(5, 1, 5, 4)
    if gs.board.occupant(pawn_sq) is not None:
        gs.board.remove(pawn_sq)
    gs.board.place(
        pawn_sq,
        chess4d.Piece(
            chess4d.Color.BLACK,
            chess4d.types.PieceType.PAWN,
            pawn_axis=chess4d.types.PawnAxis.Y,
        ),
    )
    return gs


_PAWN_TARGETED = {
    "pawn_check_w_axis": _make_pawn_check_w_axis(),
    "pawn_check_y_axis": _make_pawn_check_y_axis(),
}


@pytest.mark.parametrize("name", sorted(_PAWN_TARGETED.keys()))
def test_pawn_attacker_constructions_phasecast_full(name):
    """Pawn-aware ``phasecast_is_check_4d`` finds pawn attackers that
    the no-pawns variant misses.
    """
    state = _PAWN_TARGETED[name]
    # No-pawns variant: should be False (no non-pawn enemy reaches
    # any king in these constructions).
    assert phasecast_is_check_4d_no_pawns(state, chess4d.Color.WHITE) is False, (
        f"{name}: no-pawn phasecast unexpectedly True; setup may "
        "have introduced an unintended non-pawn attacker"
    )
    # Pawn-aware variant: should be True (the constructed black pawn
    # IS a check).
    cast = phasecast_is_check_4d(state, chess4d.Color.WHITE)
    naive = _naive_full_check(state, chess4d.Color.WHITE)
    assert cast is True, f"{name}: phasecast_full={cast} expected True"
    assert naive is True, f"{name}: naive_full={naive} expected True"


# ─── move_leaves_king_in_check_4d_no_pawns coverage ─────────────────


def test_move_leaves_king_in_check_no_pawns_safe_move():
    """A move that doesn't expose any king to a non-pawn attacker
    returns False."""
    gs = chess4d.initial_position()
    # Pick the first legal move from startpos. Initial 4D position
    # has no pieces in attack range of any king, so any random move
    # leaves no king in check (by non-pawn pieces).
    moves = list(gs.legal_moves())
    assert moves
    chosen = moves[0]
    assert not move_leaves_king_in_check_4d_no_pawns(gs, chosen)


def test_move_leaves_king_in_check_no_pawns_pin_check():
    """Verify the post-push / pop semantics: applying a move and then
    detecting check from the post-state should produce the same
    answer as constructing the post-state directly and querying.

    This is the contract the move-filter is built on; if it breaks,
    legal-move filtering would silently leak illegal moves.
    """
    # Use one of our targeted check positions and play a "null"-
    # equivalent: any quiet move from white. The post-state is still
    # a check (the rook is still on the x-axis), so detection should
    # yield True.
    state = _make_check_position_rook_on_x_axis()
    # Find a legal move (Note: legal_moves filters out moves that
    # leave the moving king in check, so legal_moves on this state
    # must include at least one king-saving move). Pick any.
    moves = list(state.legal_moves())
    if not moves:
        pytest.skip("constructed state has no legal moves; can't probe")
    # The move should leave the post-state out of check (since
    # legal_moves already filtered for that). Cross-check this via
    # the move-filter and the post-state oracle.
    chosen = moves[0]
    # Ground truth: push, ask, pop.
    state.push(chosen)
    mover_color = chess4d.Color(1 - state.side_to_move)
    naive_post = _naive_non_pawn_check(state, mover_color)
    state.pop()
    cast_via_filter = move_leaves_king_in_check_4d_no_pawns(state, chosen)
    assert cast_via_filter == naive_post, (
        f"move-filter disagrees with post-state naive: "
        f"filter={cast_via_filter} naive={naive_post}"
    )

"""Phase C structural gate — ``occupation_aware_moves_a_4d`` reproduces
``chess4d``'s pseudo-legal generators on a 50-position seeded corpus.

The 4D analogue of 2D's ``test_occupation_aware_a.py``. Where 2D used
``python-chess`` as the oracle, 4D uses
[`python-chess4d-oana-chiru`](https://pypi.org/project/python-chess4d-oana-chiru/)
— the Python reference implementation of Oana & Chiru (2026).

For each non-pawn piece on each occupied square in each of 50 seeded
``GameState`` positions:

    occupation_aware_moves_a_4d(state, origin, piece)
        ==
    {m.to_sq for m in <piece>_moves(origin, color, board)}

Pawns are excluded — their oracle (``pawn_moves``) emits diagonal
captures whose phase-op equivalent is Phase E.

Setup discipline:
  * The test imports ``chess4d``, so it requires the ``test`` extra:
    ``pip install "chess-spectral[test]"``. ``importorskip`` makes the
    skip clean if the package isn't installed.
  * Seeded random move-play from ``initial_position()`` generates the
    50-position corpus — reproducible and easy to bisect when a
    failure surfaces.
"""
from __future__ import annotations

import random
from itertools import islice

import pytest

# Skip the whole module if chess4d isn't installed (CI without the test
# extra, or fresh-clone develop loops).
chess4d = pytest.importorskip(
    "chess4d",
    reason="Phase C requires python-chess4d-oana-chiru. Install with "
           "`pip install chess-spectral[test]` or "
           "`pip install python-chess4d-oana-chiru`.",
)

from chess_spectral.phase_operators_4d import (
    occupation_aware_moves_a_4d,
)


# ─── corpus generator ───────────────────────────────────────────────


def _seeded_random_position(seed: int, max_plies: int) -> "chess4d.GameState":
    """Play up to ``max_plies`` random legal moves from the initial
    position with the given RNG seed.

    ``GameState.push`` mutates in place (matching python-chess
    semantics) and returns None.

    Stops early on terminal states (checkmate / stalemate / fifty-move
    / threefold) so we never propose moves on a closed game.
    """
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
        move = rng.choice(moves)
        gs.push(move)
    return gs


def _corpus_positions(n: int) -> list["chess4d.GameState"]:
    """Generate ``n`` seeded positions with varying ply counts (mix of
    early / mid / late game)."""
    out = []
    for i in range(n):
        # Vary ply depth: 0..10 (opening/early middlegame). 4D
        # initial position has ~448 pieces per side, so even a
        # shallow random walk produces highly heterogeneous boards.
        max_plies = 1 + (i % 6)  # 1, 2, 3, 4, 5, 6, 1, 2, ...
        out.append(_seeded_random_position(seed=i, max_plies=max_plies))
    return out


_CORPUS_SIZE = 50
_CORPUS = _corpus_positions(_CORPUS_SIZE)


# ─── helpers ────────────────────────────────────────────────────────


_PIECE_GENS = {
    chess4d.types.PieceType.ROOK:   chess4d.rook_moves,
    chess4d.types.PieceType.BISHOP: chess4d.bishop_moves,
    chess4d.types.PieceType.QUEEN:  chess4d.queen_moves,
    chess4d.types.PieceType.KNIGHT: chess4d.knight_moves,
    chess4d.types.PieceType.KING:   chess4d.king_moves,
}


def _oracle_dests(state, origin, piece):
    """Destinations from ``chess4d``'s piece-specific oracle."""
    fn = _PIECE_GENS[piece.piece_type]
    return frozenset(
        (m.to_sq.x, m.to_sq.y, m.to_sq.z, m.to_sq.w)
        for m in fn(origin, piece.color, state.board)
    )


# ─── parametrized gate ──────────────────────────────────────────────
#
# One test case per (state, origin, piece). We materialize the index
# eagerly so pytest can report each case discretely.


def _all_test_cases():
    cases = []
    for state_idx, gs in enumerate(_CORPUS):
        for color in (chess4d.Color.WHITE, chess4d.Color.BLACK):
            for sq, piece in gs.board.pieces_of(color):
                if piece.piece_type == chess4d.types.PieceType.PAWN:
                    continue
                cases.append((state_idx, gs, sq, piece))
    return cases


_CASES = _all_test_cases()


@pytest.mark.parametrize(
    "state_idx,state,origin,piece",
    _CASES,
    # Cap the test-id length to keep pytest output readable across the
    # ~50,000+ cases the corpus generates.
    ids=lambda v: f"s{v}" if isinstance(v, int) else None,
)
def test_occupation_aware_a_matches_chess4d_oracle(
    state_idx, state, origin, piece,
):
    """Solution A: phase op + oracle filter == oracle pseudo-legal set.

    ``occupation_aware_moves_a_4d`` returns ``phase_dests ∩ oracle_dests``.
    For this to equal ``oracle_dests`` (the assertion below), the phase
    op must be **complete** on the empty board — which Phase B's
    structural gate verified at 4096 origins × 9 piece configs.

    A failure here means the phase op missed a destination the oracle
    has — typically a sign that the design's [-14, 14]^4 dependency
    check (C5) didn't catch a subtle aliasing case, or that the oracle's
    rules deviate from O&C in a way Phase B didn't exercise.
    """
    aware = occupation_aware_moves_a_4d(state, origin, piece)
    oracle = _oracle_dests(state, origin, piece)
    assert aware == oracle, (
        f"state={state_idx} {piece.color.name} {piece.piece_type.name} at "
        f"{origin}: missing={oracle - aware}, extra={aware - oracle}"
    )


# ─── headline summary test (single, fast) ──────────────────────────


def test_corpus_size_and_ply_diversity():
    """Sanity: corpus contains the expected number of positions and is
    actually diverse (not all startpos)."""
    assert len(_CORPUS) == _CORPUS_SIZE
    # At least some positions should differ from initial_position.
    initial = chess4d.initial_position()
    differ = sum(
        1 for gs in _CORPUS
        if gs.position_history != initial.position_history
    )
    assert differ >= _CORPUS_SIZE // 2, (
        f"corpus is too uniform: only {differ}/{_CORPUS_SIZE} differ "
        "from the initial position"
    )


def test_corpus_covers_all_non_pawn_piece_types():
    """Every piece type in {ROOK, BISHOP, QUEEN, KNIGHT, KING} appears
    at least once in the corpus, ensuring the parametrized gate
    exercises every operator."""
    seen: set[chess4d.types.PieceType] = set()
    expected = {
        chess4d.types.PieceType.ROOK,
        chess4d.types.PieceType.BISHOP,
        chess4d.types.PieceType.QUEEN,
        chess4d.types.PieceType.KNIGHT,
        chess4d.types.PieceType.KING,
    }
    for gs in _CORPUS:
        for color in (chess4d.Color.WHITE, chess4d.Color.BLACK):
            for _sq, piece in gs.board.pieces_of(color):
                seen.add(piece.piece_type)
        if expected.issubset(seen):
            break
    assert expected.issubset(seen), (
        f"missing piece types in corpus: {expected - seen}"
    )


def test_pawn_oracle_path_raises_value_error_for_now():
    """Phase E is still pending — pawn dispatch in
    ``occupation_aware_moves_a_4d`` should raise ``ValueError`` (loud
    failure) rather than silently producing wrong results."""
    gs = chess4d.initial_position()
    # Find a pawn.
    pawn_sq = None
    pawn_piece = None
    for sq, piece in gs.board.pieces_of(chess4d.Color.WHITE):
        if piece.piece_type == chess4d.types.PieceType.PAWN:
            pawn_sq = sq
            pawn_piece = piece
            break
    assert pawn_sq is not None
    with pytest.raises(ValueError, match="Phase E"):
        occupation_aware_moves_a_4d(gs, pawn_sq, pawn_piece)

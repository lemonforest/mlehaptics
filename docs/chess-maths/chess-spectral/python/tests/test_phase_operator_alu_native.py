"""1.11.0 immolation: ALU-native phase-operator move generator.

Tests cover:

  * Encoder-sq ↔ python-chess (rank, file) round trip for all 64
    squares.
  * ``occupation_field_from_pos_dict`` parity with
    ``occupation_field_from_board`` for a battery of positions.
  * ``ep_phase_from_ep_file`` parity with ``ep_phase_from_board``.
  * **The load-bearing acceptance gate**: every move emitted by
    :func:`phase_only_pseudo_legal_moves` agrees with
    :func:`board.pseudo_legal_moves` (after excluding castles —
    castles are deferred to a future minor) on a test corpus.
  * Pawn promotion expansion (one move → four promotion targets).
  * En passant: with the EP file supplied, the EP capture move
    appears; without it, it doesn't.
  * Side-to-move filtering: only the side-to-move's pieces produce
    moves.
"""
from __future__ import annotations

import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
if PKG not in sys.path:
    sys.path.insert(0, PKG)

from chess_spectral import (   # noqa: E402
    fen_to_pos,
    occupation_field_from_pos_dict,
    ep_phase_from_ep_file,
    phase_only_pseudo_legal_moves,
    PROMOTION_TARGETS,
)
from chess_spectral.phase_operators.occupation_field import (   # noqa: E402
    _encoder_sq_to_chess_rc,
    _chess_rc_to_encoder_sq,
    occupation_field_from_board,
    ep_phase_from_board,
    WHITE_CHARGE,
)


# ─── Encoder-sq ↔ chess (rank, file) conversion ─────────────────────


def test_immolation_encoder_sq_to_chess_rc_round_trip_all_64():
    """Every encoder sq ∈ [0, 64) round-trips through (chess_rank,
    chess_file) and back."""
    for sq in range(64):
        r, c = _encoder_sq_to_chess_rc(sq)
        assert 0 <= r < 8 and 0 <= c < 8
        assert _chess_rc_to_encoder_sq(r, c) == sq


def test_immolation_encoder_sq_anchor_squares():
    """Spot-check the corners and the king/queen home squares."""
    # sq 0 = a8 → rank 7 (rank 8 in 1-indexed), file 0 (file a)
    assert _encoder_sq_to_chess_rc(0) == (7, 0)
    # sq 7 = h8 → rank 7, file 7
    assert _encoder_sq_to_chess_rc(7) == (7, 7)
    # sq 56 = a1 → rank 0, file 0
    assert _encoder_sq_to_chess_rc(56) == (0, 0)
    # sq 63 = h1 → rank 0, file 7
    assert _encoder_sq_to_chess_rc(63) == (0, 7)
    # sq 60 = e1 (white king home) → rank 0, file 4
    assert _encoder_sq_to_chess_rc(60) == (0, 4)
    # sq 4 = e8 (black king home) → rank 7, file 4
    assert _encoder_sq_to_chess_rc(4) == (7, 4)


# ─── occupation_field_from_pos_dict parity ──────────────────────────


def _representative_fens():
    """A small but diverse sample of FENs covering opening,
    middlegame, endgame, EP-active, and check positions."""
    return [
        # Standard startpos
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        # 1. e4
        "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
        # 1. e4 c5 (Sicilian; ep gone after black's move)
        "rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq c6 0 2",
        # Italian Game
        "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3",
        # Endgame: K+P vs K
        "8/8/8/4k3/4P3/4K3/8/8 w - - 0 1",
        # Endgame: K+R vs K
        "8/8/8/4k3/8/8/4R3/4K3 w - - 0 1",
        # Mid-game with both sides castled
        "r1b2rk1/pp2bppp/2nppn2/q1p5/2P5/2N1PN2/PPQ1BPPP/2KR1B1R w - - 4 11",
        # Promotion-imminent
        "8/3P4/8/8/8/8/4k3/4K3 w - - 0 1",
    ]


@pytest.mark.parametrize("fen", _representative_fens())
def test_immolation_occupation_field_from_pos_dict_parity(fen):
    """For every representative FEN, the ALU-native
    occupation_field_from_pos_dict must produce the same dict as
    occupation_field_from_board (same phases, same charges)."""
    chess = pytest.importorskip("chess")
    board = chess.Board(fen)
    via_board = occupation_field_from_board(board)
    via_pos = occupation_field_from_pos_dict(fen_to_pos(fen))
    assert via_pos == via_board, (
        f"occupation field disagreement on FEN={fen}; "
        f"board path={via_board}, pos path={via_pos}"
    )


# ─── ep_phase parity ────────────────────────────────────────────────


def test_immolation_ep_phase_from_ep_file_parity_after_e4():
    """After 1. e4, ep_square = e3 (file 4, rank 2). The ALU-native
    derivation from ep_file=4 with side_to_move=black must produce
    the same phase as ep_phase_from_board on the resulting position."""
    chess = pytest.importorskip("chess")
    board = chess.Board()
    board.push_uci("e2e4")
    via_board = ep_phase_from_board(board)
    via_file = ep_phase_from_ep_file(ep_file=4, side_to_move_white=False)
    assert via_file == via_board


def test_immolation_ep_phase_from_ep_file_parity_after_d5():
    """After 1. e4 d5, the EP target is d6 — but on white's
    second move, so side_to_move_white=True with ep_file=3."""
    chess = pytest.importorskip("chess")
    board = chess.Board()
    board.push_uci("e2e4")
    board.push_uci("d7d5")
    via_board = ep_phase_from_board(board)
    via_file = ep_phase_from_ep_file(ep_file=3, side_to_move_white=True)
    assert via_file == via_board


def test_immolation_ep_phase_none_round_trip():
    """No EP target → both paths return None."""
    chess = pytest.importorskip("chess")
    board = chess.Board()  # startpos has no EP target
    assert ep_phase_from_board(board) is None
    assert ep_phase_from_ep_file(None, side_to_move_white=True) is None
    assert ep_phase_from_ep_file(None, side_to_move_white=False) is None


# ─── The load-bearing acceptance gate ───────────────────────────────


def _moves_from_chess_excluding_castles(board) -> set:
    """Return python-chess pseudo-legal moves as a set of
    (from_sq_encoder, to_sq_encoder, promo_char) tuples, excluding
    castles (out of scope for 1.11.0).

    python-chess's pseudo_legal_moves does NOT include castling
    (castling is a "legal-only" move type in chess); but to be
    explicit, we filter here defensively.
    """
    out = set()
    for move in board.pseudo_legal_moves:
        if board.is_castling(move):
            continue
        from_chess_sq = move.from_square
        to_chess_sq = move.to_square
        # python-chess sq → encoder sq
        from_chess_rank = from_chess_sq // 8
        from_chess_file = from_chess_sq % 8
        to_chess_rank = to_chess_sq // 8
        to_chess_file = to_chess_sq % 8
        from_enc = _chess_rc_to_encoder_sq(from_chess_rank, from_chess_file)
        to_enc = _chess_rc_to_encoder_sq(to_chess_rank, to_chess_file)
        promo = None
        if move.promotion is not None:
            # python-chess uses lowercase piece-type ints; convert to
            # our uppercase promotion char.
            import chess as _chess
            promo = _chess.PIECE_SYMBOLS[move.promotion].upper()
        out.add((from_enc, to_enc, promo))
    return out


def _ep_file_from_board(board) -> "int | None":
    """Extract the ep_file from a python-chess Board for the
    ALU-native call site."""
    if board.ep_square is None:
        return None
    return board.ep_square % 8  # python-chess sq has file as low 3 bits


@pytest.mark.parametrize("fen", _representative_fens())
def test_immolation_phase_only_moves_match_python_chess_excluding_castles(fen):
    """**Acceptance gate.** For every representative FEN, the
    ALU-native phase_only_pseudo_legal_moves return set must equal
    python-chess's pseudo_legal_moves return set, excluding castles."""
    chess = pytest.importorskip("chess")
    board = chess.Board(fen)
    pos = fen_to_pos(fen)

    # Determine ep_file from board.
    ep_file = _ep_file_from_board(board)

    via_phase = set(phase_only_pseudo_legal_moves(
        pos,
        side_to_move_white=(board.turn == chess.WHITE),
        ep_file=ep_file,
    ))
    via_chess = _moves_from_chess_excluding_castles(board)

    assert via_phase == via_chess, (
        f"\nFEN: {fen}\n"
        f"  In phase but not chess: {via_phase - via_chess}\n"
        f"  In chess but not phase: {via_chess - via_phase}"
    )


# ─── Targeted edge cases ────────────────────────────────────────────


def test_immolation_pawn_promotion_expands_to_four_targets():
    """A white pawn one step from promotion must emit 4 moves
    (one per Q/R/B/N target) and only those."""
    fen = "8/3P4/8/8/8/8/4k3/4K3 w - - 0 1"
    pos = fen_to_pos(fen)
    moves = phase_only_pseudo_legal_moves(pos, side_to_move_white=True)
    pawn_moves = [m for m in moves
                  if m[2] is not None]  # promotions only
    assert len(pawn_moves) == 4
    promotions = sorted(m[2] for m in pawn_moves)
    assert promotions == sorted(PROMOTION_TARGETS)


def test_immolation_ep_target_required_for_ep_capture():
    """1. e4 d5 2. e5 f5 — without ep_file=5, no EP capture; with it,
    the EP capture exf6 appears."""
    chess = pytest.importorskip("chess")
    board = chess.Board()
    for uci in ("e2e4", "d7d5", "e4e5", "f7f5"):
        board.push_uci(uci)
    pos = fen_to_pos(board.fen())

    # Without ep_file (caller forgot to pass it): no e5xf6.
    moves_no_ep = set(phase_only_pseudo_legal_moves(
        pos, side_to_move_white=True, ep_file=None))
    # White e5 = sq 28 (encoder); f6 = sq 21.
    e5 = 28
    f6 = 21
    assert (e5, f6, None) not in moves_no_ep

    # With ep_file=5 (file f), the EP capture appears.
    moves_with_ep = set(phase_only_pseudo_legal_moves(
        pos, side_to_move_white=True, ep_file=5))
    assert (e5, f6, None) in moves_with_ep


def test_immolation_only_side_to_move_emits_moves():
    """At startpos, side_to_move_white=True yields only white-piece
    moves (lowercase pieces don't appear as movers)."""
    pos = fen_to_pos(
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    moves = phase_only_pseudo_legal_moves(pos, side_to_move_white=True)
    # Every from_sq must hold a white piece.
    for from_sq, to_sq, promo in moves:
        assert pos[from_sq].isupper(), (
            f"side_to_move=white but from_sq={from_sq} holds "
            f"black piece {pos[from_sq]!r}"
        )


def test_immolation_pseudo_legal_count_at_startpos():
    """Standard chess opening: 20 legal moves at startpos. Pseudo-
    legal count is the same at startpos because nothing is checked
    in opening (no king-in-check filter needed)."""
    pos = fen_to_pos(
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    moves = phase_only_pseudo_legal_moves(pos, side_to_move_white=True)
    # 8 pawn single-pushes + 8 pawn double-pushes + 4 knight moves = 20
    assert len(moves) == 20


def test_immolation_str_keyed_pos_dict_accepted():
    """NDJSON convention uses str-keyed dicts; ALU-native path
    accepts them."""
    pos_int = fen_to_pos(
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    pos_str = {str(k): v for k, v in pos_int.items()}
    moves_int = set(phase_only_pseudo_legal_moves(
        pos_int, side_to_move_white=True))
    moves_str = set(phase_only_pseudo_legal_moves(
        pos_str, side_to_move_white=True))
    assert moves_int == moves_str

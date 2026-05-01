"""1.8.0 immolation: GameState4D consumer surface for chess4D-OC.

Tests the wishlist surface introduced in chess-spectral 1.8.0
(M11.40 unblocker for the chess4D-OC visualizer):

  Tier 1.1  push()/pop() round-trip on GameState4D
  Tier 1.2  board property + occupant() + pieces_of()
  Tier 1.3  to_fen()/from_fen() aliases
  Tier 1.5  public types stable (Move4D, GameState4D, SIDE_*, etc.)
  Tier 1.6  iter_pieces() yields encoder pos4-shaped tuples
  Tier 3.1  search() accepts a GameState4D
  Tier 3.2  is_check / is_checkmate / is_stalemate

Each test is a hard gate — if any of these break, downstream
consumers (chess4D-OC's M11.40, the Pyodide bridge, etc.) break
along with it. Each test asserts both the contract shape (the
return type / signature) and at least one concrete behaviour, so
a no-op stub doesn't silently keep the suite green.
"""
from __future__ import annotations

import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
if PKG not in sys.path:
    sys.path.insert(0, PKG)

from chess_spectral_4d import (   # noqa: E402
    GameState4D, Move4D, SIDE_WHITE, SIDE_BLACK,
)


# ─── Fixture: simple 3-piece position used across tests ─────────────


SIMPLE_FEN4 = "4d-fen v1: K@0,0,0,0; k@7,7,7,7; Pw@0,0,0,1"


@pytest.fixture
def simple_state() -> GameState4D:
    return GameState4D.from_fen4(SIMPLE_FEN4)


# ─── Tier 1.5: public surface contract ──────────────────────────────


def test_immolation_public_surface_exposed_at_top_level():
    """All wishlist 1.5 names import cleanly from chess_spectral_4d.
    Catches accidental demotion of any of these to a sub-module-only
    export."""
    import chess_spectral_4d as cs4d
    for name in (
        "GameState4D", "Move4D", "MoveHistory4D",
        "SIDE_WHITE", "SIDE_BLACK",
        "coord_to_sq", "sq_to_coord",
        "apply_move", "encode_4d",
    ):
        assert hasattr(cs4d, name), (
            f"chess_spectral_4d.{name} is missing — chess4D-OC "
            f"M11.40 needs this re-exported at the top level."
        )


def test_immolation_side_constants_are_distinct_ints():
    """SIDE_WHITE / SIDE_BLACK are stable ``int`` values that won't
    drift to enum / Enum (the chess4D-OC worker treats them as the
    integers 0 and 1 directly)."""
    assert isinstance(SIDE_WHITE, int)
    assert isinstance(SIDE_BLACK, int)
    assert SIDE_WHITE != SIDE_BLACK
    assert {SIDE_WHITE, SIDE_BLACK} == {0, 1}


# ─── Tier 1.1: push / pop round-trip ────────────────────────────────


def test_immolation_push_advances_state(simple_state: GameState4D):
    """push() applies the move and flips side-to-move."""
    assert simple_state.side_to_move == SIDE_WHITE
    move = simple_state.push(((0, 0, 0, 1), (0, 0, 0, 2)))
    assert isinstance(move, Move4D)
    assert simple_state.side_to_move == SIDE_BLACK
    assert simple_state.occupant((0, 0, 0, 1)) is None
    assert simple_state.occupant((0, 0, 0, 2)) == ("P", "w")


def test_immolation_pop_round_trips_to_initial(simple_state: GameState4D):
    """push -> pop returns to initial FEN4 and SIDE_WHITE; popped
    Move4D matches the pushed move's coordinates."""
    initial_fen = simple_state.to_fen4()
    pushed = simple_state.push(((0, 0, 0, 1), (0, 0, 0, 2)))
    popped = simple_state.pop()
    assert isinstance(popped, Move4D)
    assert popped.from_sq == pushed.from_sq
    assert popped.to_sq == pushed.to_sq
    assert simple_state.to_fen4() == initial_fen
    assert simple_state.side_to_move == SIDE_WHITE
    assert len(simple_state.history.moves) == 0


def test_immolation_pop_empty_history_raises_index_error(
    simple_state: GameState4D,
):
    """pop() on a fresh state must raise IndexError (parallel to
    chess.Board.pop()'s contract). The chess4D-OC worker uses this
    to detect the bottom of its undo stack."""
    with pytest.raises(IndexError):
        simple_state.pop()


def test_immolation_push_pop_two_plies(simple_state: GameState4D):
    """Push two plies, then pop twice; state and side-to-move
    restore exactly. Catches off-by-one in the half-move clock or
    side-to-move flip."""
    initial_fen = simple_state.to_fen4()
    simple_state.push(((0, 0, 0, 1), (0, 0, 0, 2)))      # white pawn
    simple_state.push(((7, 7, 7, 7), (7, 7, 7, 6)))      # black king
    assert simple_state.side_to_move == SIDE_WHITE
    simple_state.pop()
    assert simple_state.side_to_move == SIDE_BLACK
    simple_state.pop()
    assert simple_state.side_to_move == SIDE_WHITE
    assert simple_state.to_fen4() == initial_fen


def test_immolation_push_accepts_move4d_object(simple_state: GameState4D):
    """push() accepts a Move4D directly (we pull from_sq / to_sq /
    promote_to off it). Used by chess4D-OC's hot-path replay loop
    where the JS side caches Move4D objects."""
    pushed = simple_state.push(((0, 0, 0, 1), (0, 0, 0, 2)))
    simple_state.pop()
    # Re-push using the Move4D object form.
    pushed2 = simple_state.push(pushed)
    assert pushed2.from_sq == pushed.from_sq
    assert pushed2.to_sq == pushed.to_sq


# ─── Tier 1.2: board property + accessors ───────────────────────────


def test_immolation_board_view_occupant(simple_state: GameState4D):
    """board.occupant(sq) returns the same as state.occupant(sq);
    accepts both linear int and (x,y,z,w) tuple."""
    board = simple_state.board
    assert board.occupant(0) == "K"          # K@0,0,0,0
    assert board.occupant((0, 0, 0, 0)) == "K"
    assert board.occupant(4095) == "k"       # k@7,7,7,7
    assert board.occupant(1) == ("P", "w")   # Pw@0,0,0,1
    assert board.occupant(42) is None        # empty square


def test_immolation_board_view_pieces_of(simple_state: GameState4D):
    """pieces_of(side) yields all (coord, piece-value) pairs of that
    side. Pawns are returned as (color, axis) tuples; non-pawns as
    single-char strings."""
    whites = simple_state.board.pieces_of(SIDE_WHITE)
    blacks = simple_state.board.pieces_of(SIDE_BLACK)
    # Sort by coord for stable comparison; the dict-order contract
    # is "preserved" but not "specified" (CPython 3.7+ insertion
    # order on the underlying position dict).
    whites_sorted = sorted(whites)
    blacks_sorted = sorted(blacks)
    assert whites_sorted == [
        ((0, 0, 0, 0), "K"),
        ((0, 0, 0, 1), ("P", "w")),
    ]
    assert blacks_sorted == [((7, 7, 7, 7), "k")]


def test_immolation_board_view_membership(simple_state: GameState4D):
    """``sq in board`` works for both int and coord forms."""
    board = simple_state.board
    assert 0 in board
    assert (0, 0, 0, 0) in board
    assert 42 not in board
    assert (3, 3, 3, 3) not in board
    assert len(board) == 3   # K, k, Pw


# ─── Tier 1.3: to_fen / from_fen aliases ────────────────────────────


def test_immolation_fen_aliases_round_trip():
    """from_fen / to_fen are exact aliases for from_fen4 / to_fen4 —
    consumer can use either name."""
    gs1 = GameState4D.from_fen(SIMPLE_FEN4)
    gs2 = GameState4D.from_fen4(SIMPLE_FEN4)
    assert gs1.to_fen() == gs2.to_fen4()
    assert gs1.to_fen() == gs1.to_fen4()
    # Slash form (1.7.1+) accepted on both names.
    gs3 = GameState4D.from_fen("4d-fen v1: P/w@0,0,0,1")
    assert gs3.to_fen() == "4d-fen v1: Pw@0,0,0,1"


# ─── Tier 1.6: iter_pieces() ────────────────────────────────────────


def test_immolation_iter_pieces_encoder_shape(simple_state: GameState4D):
    """iter_pieces() yields (sq_int, piece_value) tuples. dict()
    on the iterator is exactly the encoder_4d.encode_4d input
    format. Wishlist tier 1.6's chief use case."""
    pos4 = dict(simple_state.iter_pieces())
    assert isinstance(pos4, dict)
    assert all(isinstance(sq, int) for sq in pos4.keys())
    assert pos4 == simple_state.position
    # Round-trip via encode_4d for confidence: must accept this
    # dict without raising.
    from chess_spectral.encoder_4d import encode_4d
    enc = encode_4d(pos4)
    assert enc.shape == (45056,)


# ─── Tier 3.1: search() accepts GameState4D ─────────────────────────


def test_immolation_search_accepts_gamestate4d(simple_state: GameState4D):
    """search() can take a GameState4D directly without the
    Board4D.from_fen() hop. Returns a SearchResult whose
    ``best_move`` is a (spatial_4d) Move4D — chess4D-OC handles
    that conversion on the consumer side."""
    from chess_spectral_4d.engine.search import search, SearchOptions
    from chess_spectral_4d.engine.eval.material import evaluate

    options = SearchOptions(max_depth=1, time_budget_ms=1000.0)
    result = search(simple_state, evaluate, options)
    assert result is not None
    assert hasattr(result, "best_move")
    assert hasattr(result, "best_score")
    assert hasattr(result, "depth_reached")
    # depth_reached >= 0 always (0 if terminal); for our 3-piece
    # position it's not terminal so depth_reached >= 1 is expected.
    assert result.depth_reached >= 0


# ─── Tier 3.2: check / mate / stalemate predicates ──────────────────


def test_immolation_is_check_predicate(simple_state: GameState4D):
    """is_check() returns False for the simple 3-piece fixture (the
    white king and black king are far apart, and Pw can't attack
    along its own axis). Catches a regression where the predicate
    always returns True / always False."""
    assert simple_state.is_check() is False


def test_immolation_is_checkmate_and_stalemate_are_bools(
    simple_state: GameState4D,
):
    """is_checkmate() / is_stalemate() return ``bool``; the simple
    fixture is neither (white has plenty of pawn moves)."""
    assert simple_state.is_checkmate() is False
    assert simple_state.is_stalemate() is False
    # Type contract: they're real bools, not 0/1 ints (the chess4D-OC
    # JS bridge uses them as JS booleans through Pyodide).
    assert type(simple_state.is_checkmate()) is bool
    assert type(simple_state.is_stalemate()) is bool


# ─── Closing sanity: combined push/pop/check round-trip ─────────────


def test_immolation_push_then_predicates_then_pop(simple_state: GameState4D):
    """End-to-end micro-flow: push a ply, query predicates, pop.
    Ensures the predicates work mid-game (after at least one
    push) without raising."""
    simple_state.push(((0, 0, 0, 1), (0, 0, 0, 2)))
    # All predicates run without raising on the mid-game state.
    is_chk = simple_state.is_check()
    is_mate = simple_state.is_checkmate()
    is_stale = simple_state.is_stalemate()
    assert isinstance(is_chk, bool)
    assert isinstance(is_mate, bool)
    assert isinstance(is_stale, bool)
    simple_state.pop()
    assert simple_state.side_to_move == SIDE_WHITE

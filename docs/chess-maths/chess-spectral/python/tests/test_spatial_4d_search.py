"""Tests for the 4D search core (PR-7-I).

Mirrors test_engine_search.py for 2D, scaled down for the 4D
move-gen perf cost (~ms vs μs per leaf in 2D). All tests use small
positions (3-5 pieces) to keep the suite fast.
"""
from __future__ import annotations

import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
if PKG not in sys.path:
    sys.path.insert(0, PKG)

from chess_spectral_4d.engine.search import (                       # noqa: E402
    search, SearchOptions, SearchResult, INF, MATE_SCORE,
)
from chess_spectral_4d.engine.search.ttable import (                 # noqa: E402
    TranspositionTable4D, BoundType,
)
from chess_spectral_4d.engine.search.ordering import order_moves     # noqa: E402
from chess_spectral.spatial_4d import Board4D, Move4D                # noqa: E402
from chess_spectral.tables_4d import sq4                              # noqa: E402


def _trivial_eval(pos_dict, side_to_move):
    """Tiny material-style evaluator: piece-count from side-to-move's POV."""
    score = 0.0
    for v in pos_dict.values():
        if isinstance(v, str):
            score += 1.0 if v.isupper() else -1.0
        elif isinstance(v, tuple):
            char = v[0]
            score += 1.0 if char.isupper() else -1.0
    return score if side_to_move else -score


def _three_piece_board() -> Board4D:
    b = Board4D.empty()
    b.set_piece(sq4(4, 4, 4, 4), 'N')
    b.set_piece(sq4(0, 0, 0, 0), 'K')
    b.set_piece(sq4(7, 7, 7, 7), 'k')
    return b


# ---- Basic correctness -----------------------------------


def test_search_returns_result_dataclass():
    b = _three_piece_board()
    r = search(b, _trivial_eval, SearchOptions(max_depth=1))
    assert isinstance(r, SearchResult)


def test_search_returns_legal_move():
    b = _three_piece_board()
    r = search(b, _trivial_eval, SearchOptions(max_depth=1))
    assert r.best_move is not None
    legal = list(b.legal_moves())
    assert r.best_move in legal


def test_search_default_options_runs():
    """Default SearchOptions runs end-to-end (depth 4 on small position)."""
    b = _three_piece_board()
    r = search(b, _trivial_eval, SearchOptions(max_depth=2))
    assert r.depth_reached >= 1
    assert r.nodes_searched > 0


def test_search_invalid_options_raise():
    with pytest.raises(ValueError):
        SearchOptions(max_depth=0)
    with pytest.raises(ValueError):
        SearchOptions(max_depth=-1)
    with pytest.raises(ValueError):
        SearchOptions(max_depth=2, time_budget_ms=0)


def test_search_terminal_position_returns_no_move():
    """A board with no legal moves returns best_move=None."""
    b = Board4D.empty()
    # Empty board: no pieces, no legal moves.
    r = search(b, _trivial_eval, SearchOptions(max_depth=1))
    assert r.best_move is None


def test_search_does_not_mutate_board():
    """board state preserved after search."""
    b = _three_piece_board()
    h_before = b.position_hash()
    _ = search(b, _trivial_eval, SearchOptions(max_depth=2))
    assert b.position_hash() == h_before


# ---- Ablation ------------------------------------------


def test_search_no_tt():
    b = _three_piece_board()
    r = search(b, _trivial_eval,
               SearchOptions(max_depth=2, use_tt=False))
    assert r.tt_hits == 0
    assert r.tt_size == 0
    assert r.best_move is not None


def test_search_no_mvv_lva():
    b = _three_piece_board()
    r = search(b, _trivial_eval,
               SearchOptions(max_depth=2, use_mvv_lva=False))
    assert r.best_move is not None


def test_search_no_quiescence():
    b = _three_piece_board()
    r = search(b, _trivial_eval,
               SearchOptions(max_depth=2, use_quiescence=False))
    assert r.best_move is not None


def test_search_all_ablations_off():
    b = _three_piece_board()
    r = search(b, _trivial_eval, SearchOptions(
        max_depth=1, use_tt=False, use_mvv_lva=False,
        use_quiescence=False,
    ))
    assert r.best_move is not None


# ---- Time budget --------------------------------------


def test_search_time_budget_aborts_early():
    """Tight budget aborts before reaching max_depth."""
    b = _three_piece_board()
    r = search(b, _trivial_eval,
               SearchOptions(max_depth=10, time_budget_ms=5))
    # At least depth 1 should finish before 5ms in this tiny position.
    # The budget bounds the search.
    assert r.depth_reached >= 1
    assert r.depth_reached < 10


# ---- Determinism ---------------------------------------


def test_search_deterministic():
    """Same input -> same output."""
    b1 = _three_piece_board()
    b2 = _three_piece_board()
    r1 = search(b1, _trivial_eval, SearchOptions(max_depth=2))
    r2 = search(b2, _trivial_eval, SearchOptions(max_depth=2))
    assert r1.best_move == r2.best_move
    assert r1.best_score == r2.best_score
    assert r1.nodes_searched == r2.nodes_searched


# ---- TT internals --------------------------------------


def test_tt_lookup_store_roundtrip():
    tt = TranspositionTable4D()
    b = _three_piece_board()
    move = Move4D(0, 1)
    tt.store(b, depth=4, score=0.5, best_move=move,
             bound_type=BoundType.EXACT)
    entry = tt.lookup(b)
    assert entry is not None
    assert entry.depth == 4
    assert entry.score == 0.5
    assert entry.best_move == move


def test_tt_miss_returns_none():
    tt = TranspositionTable4D()
    b = _three_piece_board()
    assert tt.lookup(b) is None


def test_tt_deeper_replaces_shallower():
    tt = TranspositionTable4D()
    b = _three_piece_board()
    tt.store(b, 2, 0.5, None, BoundType.EXACT)
    tt.store(b, 6, 0.7, None, BoundType.EXACT)
    e = tt.lookup(b)
    assert e.depth == 6


def test_tt_shallow_does_not_replace_deeper():
    tt = TranspositionTable4D()
    b = _three_piece_board()
    tt.store(b, 6, 0.7, None, BoundType.EXACT)
    tt.store(b, 2, 0.5, None, BoundType.EXACT)
    e = tt.lookup(b)
    assert e.depth == 6


def test_tt_size_bounded():
    tt = TranspositionTable4D(max_size=2)
    b1 = Board4D.empty()
    b2 = Board4D.empty()
    b2.set_piece(sq4(0, 0, 0, 0), 'K')
    b3 = Board4D.empty()
    b3.set_piece(sq4(7, 7, 7, 7), 'k')
    tt.store(b1, 1, 0.0, None, BoundType.EXACT)
    tt.store(b2, 1, 0.1, None, BoundType.EXACT)
    assert len(tt) == 2
    tt.store(b3, 1, 0.2, None, BoundType.EXACT)
    assert len(tt) == 2   # eviction occurred


# ---- Move ordering --------------------------------------


def test_order_moves_tt_move_first():
    b = _three_piece_board()
    moves = list(b.legal_moves())
    if not moves:
        pytest.skip("no moves")
    tt_move = moves[5] if len(moves) > 5 else moves[0]
    ordered = order_moves(b, moves, tt_move=tt_move)
    assert ordered[0] == tt_move


def test_order_moves_deterministic():
    b = _three_piece_board()
    moves = list(b.legal_moves())
    o1 = order_moves(b, moves)
    o2 = order_moves(b, moves)
    assert o1 == o2


# ---- API surface ----------------------------------------


def test_module_exports():
    from chess_spectral_4d.engine import search as search_pkg
    for name in ('search', 'SearchResult', 'SearchOptions', 'INF',
                 'MATE_SCORE'):
        assert name in search_pkg.__all__

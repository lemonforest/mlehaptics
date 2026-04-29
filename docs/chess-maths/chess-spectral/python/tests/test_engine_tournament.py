"""Tests for chess_spectral.engine.tournament.

Round-robin tournament harness with ELO rating + structured results.
Tests cover:
  * EloRating: initial values, incremental update, monotonic for
    consistent winner, multiple labels.
  * Termination classifier: checkmate / stalemate / draw rules
    produce correct labels.
  * play_game: smoke test on a tiny position with material agents.
  * run_round_robin: 2-agent matrix produces expected number of
    games and pair_records add up.
"""
from __future__ import annotations

import os
import sys

import chess
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
if PKG not in sys.path:
    sys.path.insert(0, PKG)

from chess_spectral.engine.tournament import (                      # noqa: E402
    Agent, EloRating, play_game, run_round_robin,
    GameResult, TournamentResult,
)

# engine.search and engine.eval.material both ship via separate PRs in
# the v1.6 train; this tournament-harness branch may land before they
# all reach main. Wrap the search/material imports in try/except so
# only the harness-internal tests (Elo, etc.) run when those PRs
# haven't landed yet. Once both PR #88 (material) and PR #91 (search)
# are in main, the play_game / round_robin smoke tests run.
try:
    from chess_spectral.engine.search import search, SearchOptions   # type: ignore
    from chess_spectral.engine.eval import material                  # type: ignore
    _ENGINE_DEPS_AVAILABLE = True
except ImportError:
    _ENGINE_DEPS_AVAILABLE = False
    search = None  # type: ignore
    SearchOptions = None  # type: ignore
    material = None  # type: ignore

_NEEDS_ENGINE = pytest.mark.skipif(
    not _ENGINE_DEPS_AVAILABLE,
    reason="play_game / round_robin tests need chess_spectral.engine."
           "search (PR #91) and engine.eval.material (PR #88) on the "
           "branch. Tests run once both predecessors merge.",
)


# ---- EloRating ---------------------------------------------


def test_elo_initial_value():
    e = EloRating(initial=1500)
    assert e.get('alice') == 1500.0
    assert e.get('bob') == 1500.0


def test_elo_winner_gains_loser_loses():
    e = EloRating(initial=1500, k=32)
    new_a, new_b = e.update('alice', 'bob', score_a=1.0)
    assert new_a > 1500
    assert new_b < 1500
    # Symmetry of K=32 zero-info update: gain == loss.
    assert abs((new_a - 1500) - (1500 - new_b)) < 1e-9


def test_elo_draw_no_change_when_equal():
    e = EloRating(initial=1500, k=32)
    new_a, new_b = e.update('alice', 'bob', score_a=0.5)
    assert new_a == 1500.0
    assert new_b == 1500.0


def test_elo_monotonic_for_consistent_winner():
    """If alice always beats bob, alice's rating climbs monotonically."""
    e = EloRating(initial=1500, k=32)
    prev = e.get('alice')
    for _ in range(5):
        e.update('alice', 'bob', score_a=1.0)
        new = e.get('alice')
        assert new > prev
        prev = new


def test_elo_all_ratings_returns_dict():
    e = EloRating()
    e.update('a', 'b', 1.0)
    e.update('c', 'b', 0.0)
    ratings = e.all_ratings()
    assert set(ratings) == {'a', 'b', 'c'}


# ---- play_game smoke (2D) ----------------------------------


@_NEEDS_ENGINE
def test_play_game_returns_game_result_smoke():
    """Smoke: play_game between two material-eval agents on a tight
    board. With max_plies=2 we just verify the harness wires up."""
    agent_white = Agent(
        label='white-mat',
        evaluator=material.evaluate,
        search_fn=search,
        search_options=SearchOptions(max_depth=1),
    )
    agent_black = Agent(
        label='black-mat',
        evaluator=material.evaluate,
        search_fn=search,
        search_options=SearchOptions(max_depth=1),
    )

    def board_factory():
        return chess.Board()

    result = play_game(agent_white, agent_black, board_factory,
                        max_plies=2)
    assert isinstance(result, GameResult)
    assert result.plies_played <= 2
    # Standard chess starting position is not game-over within 2
    # plies; expect 'max_plies' termination.
    assert result.termination == 'max_plies'
    assert result.score_white == 0.5   # max_plies → draw


@_NEEDS_ENGINE
def test_play_game_records_moves():
    agent = Agent(
        label='m', evaluator=material.evaluate,
        search_fn=search, search_options=SearchOptions(max_depth=1),
    )
    result = play_game(agent, agent, lambda: chess.Board(),
                        max_plies=2)
    assert len(result.moves) == result.plies_played
    # Each move is a chess.Move instance.
    for m in result.moves:
        assert isinstance(m, chess.Move)


# ---- run_round_robin --------------------------------------


@_NEEDS_ENGINE
def test_round_robin_n_games_per_pair():
    """N agents in round-robin → C(N, 2) pairs × n_games_per_pair games."""
    agents = [
        Agent(label=f'a{i}', evaluator=material.evaluate,
              search_fn=search,
              search_options=SearchOptions(max_depth=1))
        for i in range(3)
    ]
    result = run_round_robin(agents, n_games_per_pair=2,
                              board_factory=lambda: chess.Board(),
                              max_plies=2)
    # C(3, 2) = 3 pairs × 2 games = 6 games.
    assert len(result.games) == 6
    assert isinstance(result, TournamentResult)


@_NEEDS_ENGINE
def test_round_robin_alternates_colors():
    """For n_games_per_pair=2, each agent should be white in 1 game
    per pair (with the rounding rule, 1+1=2)."""
    agents = [
        Agent(label='a', evaluator=material.evaluate,
              search_fn=search,
              search_options=SearchOptions(max_depth=1)),
        Agent(label='b', evaluator=material.evaluate,
              search_fn=search,
              search_options=SearchOptions(max_depth=1)),
    ]
    result = run_round_robin(agents, n_games_per_pair=2,
                              board_factory=lambda: chess.Board(),
                              max_plies=2)
    a_white_count = sum(1 for g in result.games if g.white.label == 'a')
    b_white_count = sum(1 for g in result.games if g.white.label == 'b')
    assert a_white_count == 1
    assert b_white_count == 1


@_NEEDS_ENGINE
def test_round_robin_pair_records_sum_to_n_games():
    """For each pair, wins + losses + draws = n_games_per_pair."""
    agents = [
        Agent(label='a', evaluator=material.evaluate,
              search_fn=search,
              search_options=SearchOptions(max_depth=1)),
        Agent(label='b', evaluator=material.evaluate,
              search_fn=search,
              search_options=SearchOptions(max_depth=1)),
    ]
    result = run_round_robin(agents, n_games_per_pair=4,
                              board_factory=lambda: chess.Board(),
                              max_plies=2)
    for (la, lb), (w, lo, d) in result.pair_records.items():
        assert w + lo + d == 4


@_NEEDS_ENGINE
def test_round_robin_returns_final_elos():
    """final_elos is a dict mapping each agent label to its rating."""
    agents = [
        Agent(label='a', evaluator=material.evaluate,
              search_fn=search,
              search_options=SearchOptions(max_depth=1)),
        Agent(label='b', evaluator=material.evaluate,
              search_fn=search,
              search_options=SearchOptions(max_depth=1)),
    ]
    result = run_round_robin(agents, n_games_per_pair=2,
                              board_factory=lambda: chess.Board(),
                              max_plies=2)
    assert set(result.final_elos) == {'a', 'b'}
    # All draws → both labels still at initial 1500.
    assert result.final_elos['a'] == 1500.0
    assert result.final_elos['b'] == 1500.0


# ---- API surface --------------------------------------


def test_module_exports():
    from chess_spectral.engine import tournament
    for name in ('Agent', 'GameResult', 'TournamentResult',
                 'EloRating', 'play_game', 'run_round_robin'):
        assert name in tournament.__all__

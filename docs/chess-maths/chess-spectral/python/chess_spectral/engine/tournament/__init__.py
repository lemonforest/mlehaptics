"""chess_spectral.engine.tournament -- self-play tournament harness.

Phase 6 (v1.6) infrastructure for the §16.3 self-play tournament that
empirically validates the spectral / QM evaluator framework. Runs
round-robin matches between agent configurations, tracks ELO across
games, and emits structured results.

The §2787 ship gate requires per-depth Elo sweep across:
  * 3+ representative depths (e.g., d=4, d=8, d=16)
  * 3 evaluators: material × spectral × qm
  * 2 dimensions: 2D + 4D

Total cells = 3 × 3 × 2 = 18 evaluator-configurations × 3 depths.
Each cell runs a round-robin and writes per-depth ELO deltas.

Public API
----------
- :class:`Agent` -- (evaluator, search_options, label) bundle.
- :func:`play_game` -- single game, returns :class:`GameResult`.
- :func:`run_round_robin` -- N-game round-robin, returns :class:`TournamentResult`.
- :class:`EloRating` -- incremental ELO updates.

Both 2D (chess.Board / chess_spectral.engine.search.search) and 4D
(spatial_4d.Board4D / chess_spectral_4d.engine.search.search) are
supported via the dim-agnostic agent dispatch.
"""
from __future__ import annotations

from .core import (
    Agent,
    GameResult,
    TournamentResult,
    EloRating,
    play_game,
    run_round_robin,
)

__all__ = [
    "Agent",
    "GameResult",
    "TournamentResult",
    "EloRating",
    "play_game",
    "run_round_robin",
]

"""chess_spectral.engine -- 2D position evaluation, search, tournament.

Phase 6 (v1.6) engine surface for the 640-dim spectral encoder. Mirrors
:mod:`chess_spectral_4d.engine` (4D) in shape.

Submodules:
  * ``eval`` -- the three §16.1 evaluator families (material, spectral,
    qm). Ships in PR #88 / PR-3 / PR-4.
  * ``search`` -- 2D negamax + alpha-beta + iterative deepening +
    transposition tables + MVV-LVA + quiescence. Ships in PR #91.
  * ``tournament`` -- round-robin self-play harness with ELO ratings.
    Ships in this PR (#102).

Convention -- ``evaluate(position, side_to_move) -> float``
  Returns a real-valued score from the side-to-move's perspective.
  Positive == side_to_move is winning. Negative == losing.
  Zero == drawn (or the evaluator has no signal).

The tournament harness composes search + evaluator into Agent
configurations and runs round-robin matches to empirically validate
the spectral / QM framework's chess-relevance per §16.5 and the
§2787 ship gate (per-depth Elo sweep across 3+ depths × 3
evaluators × 2 dimensions).
"""
from __future__ import annotations

# Eager imports of the submodules that are present at the time of
# load. eval / search / tournament each ship in separate v1.6 PRs;
# this __init__ tolerates partial state during the merge train via
# try/except, and registers everything available.
try:
    from . import eval  # noqa: F401
except ImportError:
    eval = None  # type: ignore

try:
    from . import search  # noqa: F401
except ImportError:
    search = None  # type: ignore

try:
    from . import tournament  # noqa: F401
except ImportError:
    tournament = None  # type: ignore

__all__ = [name for name, val in (
    ("eval", eval), ("search", search), ("tournament", tournament),
) if val is not None]

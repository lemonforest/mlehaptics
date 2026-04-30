"""chess_spectral.engine.search -- 2D search core (Phase 6.2).

Standard alpha-beta game-tree search wrapped around the §16.1
evaluator API. Public entry point :func:`search` returns the best
move and score for a position at a given depth, using:

  * negamax with alpha-beta pruning
  * iterative deepening (depth 1, 2, ..., max_depth)
  * Zobrist-keyed transposition tables (depth + bound type)
  * MVV-LVA move ordering (captures by victim/attacker value)
  * quiescence search (extends on captures at leaves)

All optional pieces are gated by flags; pass ``use_tt=False`` etc.
to ablate. The §16 self-play tournament (PR-7) iterates over the
ablation matrix to study which components matter for the spectral /
QM evaluators specifically.

The 4D analogue (engine.search at chess_spectral_4d) ships in a
follow-up PR; it shares everything except the move generator
(python-chess vs phase_operators_4d / python-chess4d-oana-chiru).
"""
from __future__ import annotations

from .core import (
    search,
    SearchResult,
    SearchOptions,
    INF,
    MATE_SCORE,
)

__all__ = [
    "search",
    "SearchResult",
    "SearchOptions",
    "INF",
    "MATE_SCORE",
]

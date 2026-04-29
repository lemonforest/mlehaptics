"""chess_spectral_4d.engine.search -- 4D search core (Phase 6.2).

4D analogue of :mod:`chess_spectral.engine.search` (2D). Wraps the
§16.1 evaluator API around the in-house spatial_4d Board4D move
generator (PR-7-F). Same algorithmic structure as the 2D search:

  * Negamax with alpha-beta pruning
  * Iterative deepening (depth 1, 2, ..., max_depth)
  * Position-hashed transposition table (uses
    Board4D.position_hash())
  * MVV-LVA move ordering (captures sorted by victim/attacker)
  * Quiescence search (capture-only extension at leaves)
  * Time-budget short-circuit
  * Ablation flags for the §16 tournament

Differences from 2D:
  * Board4D instead of chess.Board.
  * 28 kings per side (Oana-Chiru §3.4 Def 4); legal-move filter
    handled in Board4D.legal_moves().
  * Position-dict adapter: Board4D.to_position_dict() rebuilds from
    bitboards each call (~hundreds of microseconds at 448-pieces);
    cached at the leaf to amortize across the QM-evaluator's
    multi-piece scan.

The 4D move generator is currently slow in pure Python (~250 s on
the 28-king starting position). For practical search depths the
combination of α-β pruning + smaller mid-game positions + TT keeps
runtime under control, but the §2787 ship gate's per-depth Elo
sweep will need a C-port (deferred to v1.7+) for full-corpus
tournament play.
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

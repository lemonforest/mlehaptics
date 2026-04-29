"""Transposition table for the search core.

Standard chess engine TT: Zobrist-hashed positions map to an entry
``(depth, score, best_move, bound_type)`` where bound_type is one
of EXACT / LOWER / UPPER:

  * EXACT: the score is the true minimax value at this depth
  * LOWER: a beta cutoff occurred; score is a lower bound
  * UPPER: no move improved alpha; score is an upper bound

Two-bucket replacement on collisions: prefer the deeper search
(replace shallow with deep), break ties via "always replace if same
depth" (recency bias for variance reduction in self-play).

The Zobrist key is python-chess's transposition_key (FEN-derived),
not a custom Zobrist scheme. python-chess hashes legal castling
rights and en-passant correctly out of the box, so we don't have
to re-implement.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Dict, Optional

import chess
import chess.polyglot


class BoundType(IntEnum):
    EXACT = 0
    LOWER = 1   # score >= beta -- beta cutoff
    UPPER = 2   # score < alpha -- no improvement


@dataclass
class TTEntry:
    depth: int
    score: float
    best_move: Optional[chess.Move]
    bound_type: BoundType


class TranspositionTable:
    """Dict-backed TT. Bounded size; oldest-replace on overflow.

    For research purposes the unbounded variant is fine for normal
    depth-12-ish searches (a 100-game tournament at depth=8 uses
    ~50k unique positions). Pass ``max_size`` to bound it.
    """

    def __init__(self, max_size: Optional[int] = None):
        self._data: Dict[int, TTEntry] = {}
        self._max_size = max_size
        self.hits = 0
        self.misses = 0
        self.stores = 0

    def __len__(self) -> int:
        return len(self._data)

    def lookup(self, board: chess.Board) -> Optional[TTEntry]:
        key = chess.polyglot.zobrist_hash(board)
        entry = self._data.get(key)
        if entry is None:
            self.misses += 1
            return None
        self.hits += 1
        return entry

    def store(self, board: chess.Board, depth: int, score: float,
              best_move: Optional[chess.Move],
              bound_type: BoundType) -> None:
        key = chess.polyglot.zobrist_hash(board)
        existing = self._data.get(key)
        # Prefer deeper search; on equal depth, replace (recency bias).
        if existing is not None and existing.depth > depth:
            return
        if (self._max_size is not None
                and existing is None
                and len(self._data) >= self._max_size):
            # Overflow: evict an arbitrary entry.
            # Simple FIFO via dict ordering -- pop the first key.
            evict_key = next(iter(self._data))
            del self._data[evict_key]
        self._data[key] = TTEntry(depth, score, best_move, bound_type)
        self.stores += 1

    def clear(self) -> None:
        self._data.clear()
        self.hits = 0
        self.misses = 0
        self.stores = 0

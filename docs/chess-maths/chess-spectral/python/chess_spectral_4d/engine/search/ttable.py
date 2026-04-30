"""Transposition table for the 4D search core.

Same shape as the 2D TT (chess_spectral.engine.search.ttable) but
keyed by :meth:`Board4D.position_hash` instead of chess.polyglot's
Zobrist hash.

EXACT / LOWER / UPPER bound types. Replaces shallow with deep on
collision; FIFO eviction on bounded-size overflow.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Dict, Optional


class BoundType(IntEnum):
    EXACT = 0
    LOWER = 1
    UPPER = 2


@dataclass
class TTEntry:
    depth: int
    score: float
    best_move: Optional[object]   # Move4D, kept Optional for clarity
    bound_type: BoundType


class TranspositionTable4D:
    """Dict-backed TT for 4D Board4D positions."""

    def __init__(self, max_size: Optional[int] = None):
        self._data: Dict[int, TTEntry] = {}
        self._max_size = max_size
        self.hits = 0
        self.misses = 0
        self.stores = 0

    def __len__(self) -> int:
        return len(self._data)

    def lookup(self, board: "object") -> Optional[TTEntry]:
        key = board.position_hash()
        entry = self._data.get(key)
        if entry is None:
            self.misses += 1
            return None
        self.hits += 1
        return entry

    def store(self, board, depth, score, best_move, bound_type):
        key = board.position_hash()
        existing = self._data.get(key)
        if existing is not None and existing.depth > depth:
            return
        if (self._max_size is not None and existing is None
                and len(self._data) >= self._max_size):
            evict_key = next(iter(self._data))
            del self._data[evict_key]
        self._data[key] = TTEntry(depth, score, best_move, bound_type)
        self.stores += 1

    def clear(self) -> None:
        self._data.clear()
        self.hits = 0
        self.misses = 0
        self.stores = 0

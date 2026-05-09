"""LRU-cached spectral hybrid evaluator (1.13.0+ — B-spike-3 path
(b)).

Wraps :mod:`chess_spectral.engine.eval.spectral_hybrid` with a
position-hash-keyed LRU cache of :class:`SpectralBIPHybrid2D`
encodings. The first visit to a position pays the full encode+eval
cost; subsequent visits hit the cache and pay only the cheap
channel-energy-from-hybrid path (~25× faster per the bench at
1.13.0).

Why this matters for §16 search
-------------------------------

The §16 alpha-beta search visits the same position multiple times
in practice — through different move orderings, quiescence
extensions, and TT collisions. The standard `engine/search/ttable.py`
caches search RESULTS (depth, score, best_move) keyed by Zobrist,
but it does NOT cache encoder OUTPUT. So when the search re-evaluates
a position whose TT entry has the wrong depth or bound type, the
evaluator pays the full encode+eval cost again.

This module's cache is **separate from the search TT** — it caches
encoder hybrid vectors keyed by position-dict hash, and it survives
across moves within a single search. The expected hit rate depends
on the search tree shape; in practice 30-70% hits is typical for
a 1k-10k entry cache at depth 4-6.

Architectural shape
-------------------

The cache is **per-search**, not per-process — instantiate at the
start of a search, populate as positions are visited, discard at
search end. This mirrors the standard engine TT lifecycle. A factory
function :func:`make_cached_evaluator` returns a closure-bound
evaluator that the caller can pass to the search core's
``SearchOptions.evaluator`` slot.

The cache is keyed by a stable hash of the position dict
(``frozenset(pos.items())``). This is **deterministic** within a
single Python process but not stable across processes — for
cross-process caching, callers should switch to a Zobrist-based
hash. (TODO 1.14.0+: integrate with the existing ttable.py's
Zobrist machinery.)
"""
from __future__ import annotations

from collections import OrderedDict
from typing import Callable, Dict, Optional, Tuple

from chess_spectral.encoder_bip_hybrid import (
    SpectralBIPHybrid2D, encode_2d_bip_hybrid,
)
from chess_spectral.engine.eval.spectral_hybrid import (
    evaluate_from_hybrid,
)
from chess_spectral.engine.eval.spectral import (
    Position2D, WeightsLike,
)


class HybridCache:
    """LRU cache of :class:`SpectralBIPHybrid2D` encodings, keyed
    by position-dict hash.

    Tracks ``hits`` and ``misses`` counters for diagnostic output;
    the search-engine integration can dump these at the end of a
    search to surface cache effectiveness.

    The cache uses :class:`collections.OrderedDict` with explicit
    ``move_to_end`` on access for true LRU semantics.
    """

    def __init__(self, max_size: int = 10000):
        self._cache: "OrderedDict[int, SpectralBIPHybrid2D]" = OrderedDict()
        self._max_size = max_size
        self.hits = 0
        self.misses = 0

    def get_or_compute(
        self,
        key: int,
        compute_fn: Callable[[], SpectralBIPHybrid2D],
    ) -> SpectralBIPHybrid2D:
        """Return the cached entry for ``key``, computing + storing
        a fresh one on miss. LRU updates on access."""
        cached = self._cache.get(key)
        if cached is not None:
            self.hits += 1
            self._cache.move_to_end(key)
            return cached
        self.misses += 1
        fresh = compute_fn()
        self._cache[key] = fresh
        if len(self._cache) > self._max_size:
            # Evict least-recently-used.
            self._cache.popitem(last=False)
        return fresh

    @property
    def size(self) -> int:
        """Current entry count."""
        return len(self._cache)

    @property
    def hit_rate(self) -> float:
        """Fraction of accesses that hit. 0.0 if no accesses yet."""
        total = self.hits + self.misses
        return float(self.hits) / total if total > 0 else 0.0

    def stats(self) -> Dict[str, int]:
        """Diagnostic snapshot: ``{"hits", "misses", "size", "max_size"}``."""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "size": self.size,
            "max_size": self._max_size,
        }


def _hash_position_dict(pos: Position2D) -> int:
    """Deterministic hash of an encoder-format position dict.

    ``frozenset(pos.items())`` is hashable in Python's standard
    library; the hash is process-stable for the lifetime of one
    Python interpreter (cf. ``PYTHONHASHSEED``). Cross-process
    callers should pre-compute a Zobrist hash externally and use a
    different cache wrapper.
    """
    return hash(frozenset(pos.items()))


def make_cached_evaluator(
    *,
    magnitude_bits: int = 8,
    cache_size: int = 10000,
    weights: WeightsLike = None,
) -> Tuple[Callable[[Position2D, bool], float], HybridCache]:
    """Build a cache-aware spectral evaluator.

    Returns ``(evaluator_fn, cache)`` — the callable is suitable for
    plugging into ``SearchOptions.evaluator``; the cache exposes
    ``hits`` / ``misses`` / ``stats()`` for diagnostic output.

    Each evaluator call:

      1. Hashes the position dict
      2. Looks up the cache; on hit, uses the stored hybrid
      3. On miss, encodes via ``encode_2d_bip_hybrid`` and stores
      4. Computes channel-energy-from-hybrid via
         :func:`evaluate_from_hybrid`

    Per-call cost:
      * Hit: ~35µs (channel-energy + weighted sum)
      * Miss: ~870µs (encode + quantize + channel-energy)

    For a §16 search at depth 4 with typical chess game-tree
    structure, expected hit rate is 30-70%, giving an average
    per-eval cost of ~250-630µs vs the float64 baseline's ~870µs.
    Roughly 1.4-3.5× speedup integrated over a search.
    """
    cache = HybridCache(max_size=cache_size)

    def cached_evaluator(pos: Position2D, side_to_move: bool) -> float:
        key = _hash_position_dict(pos)
        hybrid = cache.get_or_compute(
            key,
            lambda: encode_2d_bip_hybrid(pos, magnitude_bits=magnitude_bits),
        )
        return evaluate_from_hybrid(
            hybrid, side_to_move, weights=weights)

    return cached_evaluator, cache


__all__ = [
    "HybridCache",
    "make_cached_evaluator",
]

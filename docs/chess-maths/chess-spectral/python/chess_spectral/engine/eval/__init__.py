"""chess_spectral.engine.eval -- evaluator families for 2D.

Public surface as of 1.13.0:

  * ``material`` (Phase 6.1.1) — integer-addition baseline; no
    encoder call.
  * ``spectral`` (Phase 6.1.2) — float64 channel-energy weighted
    sum; the 1.0–1.12.x default. Encoder-fronted.
  * ``spectral_float32`` (1.13.0+, B-spike-3 path (d)) — float32
    downstream of the float64 encoder. Mirrors the ephemerides
    two-stage architecture (complex128 → complex64). Documented
    null result on standalone bench (encoder dominates); kept as
    a sibling for completeness + future float32-native encoder
    work.
  * ``spectral_hybrid`` (1.13.0+, B-spike-3 path (a)) — channel-
    energy directly from a SpectralBIPHybrid2D, skipping the
    float decode. Two entry points:
      - ``evaluate(pos, side, magnitude_bits=8)`` — full path
        (encode + eval); slower than spectral.evaluate due to the
        extra quantize step but bench-comparable.
      - ``evaluate_from_hybrid(hybrid, side)`` — cache-hit path;
        skips encode entirely. **~15× faster** at the warm-LRU
        steady state per bench. The §16 search-engine integration
        target.
  * ``spectral_hybrid_cache`` (1.13.0+, B-spike-3 path (b)) —
    LRU-cached wrapper around ``spectral_hybrid``. Factory
    ``make_cached_evaluator(magnitude_bits=8, cache_size=10000)``
    returns ``(evaluator_fn, cache)`` — drop the callable into
    SearchOptions.evaluator and inspect ``cache.stats()`` for
    diagnostic hit/miss counts.
  * ``qm`` (Phase 6.1.3) — Born-rule QM-expectation. Most
    expensive reference; included for tournament context.

Each evaluator module exports ``evaluate(position, side_to_move)
-> float`` plus type-specific configuration. The ``spectral_hybrid``
module additionally exports ``evaluate_from_hybrid`` and
``channel_energies_from_hybrid`` for direct hybrid-vector consumers.

See ``tests/bench_spectral_eval.py`` for the bench harness that
records BEFORE/AFTER deltas across the variants. Notebook §20.20
captures the empirical findings for B-spike-3.
"""
from __future__ import annotations

from . import material  # noqa: F401
from . import spectral  # noqa: F401
from . import qm        # noqa: F401
from . import spectral_float32  # noqa: F401  # 1.13.0+
from . import spectral_hybrid   # noqa: F401  # 1.13.0+
from . import spectral_hybrid_cache  # noqa: F401  # 1.13.0+

__all__ = [
    "material", "spectral", "qm",
    # 1.13.0+
    "spectral_float32",
    "spectral_hybrid",
    "spectral_hybrid_cache",
]

"""Float32 downstream variant of the spectral channel-energy
evaluator (1.13.0+ — B-spike-3 path (d)).

Mirrors the ephemerides-spectral two-stage architecture (notebook
§20.20 — see ephemerides notebook line 15: "integer-ALU phase-residue
encoders … feeding an FPU `complex64` HD pipeline"). The
ephemerides analog: complex128 reference → complex64 production. The
chess analog: float64 baseline → float32 downstream.

What changes vs :mod:`chess_spectral.engine.eval.spectral`
---------------------------------------------------------

The base 1.0–1.12.x ``spectral.evaluate`` upcasts the encoder
output to ``float64`` before computing channel energies::

    v = encode_640(position).astype(np.float64, copy=False)
    energies = channel_energies(v)  # vdot in float64

This module flips the dtype to ``float32`` for the downstream
sum-of-squares + weighted-sum computation. The sign of every dim
is preserved exactly (float32 carries its own sign bit); the only
loss source is the magnitude precision dropping from 23-bit to
~7-decimal-digit relative.

For the channel-energy use case (sum of squares per channel), this
is **lossless to within float32 precision** — channel energies are
positive scalars in the [0, ~1000] range, well within float32's
representable values. Numpy's float32 sum-of-squares is ~2× faster
than float64 on x86-64 (memory-bandwidth-bound), so this is a
free-win speedup if the precision is acceptable.

What this does NOT change
-------------------------

- The encoder output ``encode_640(pos)`` still returns float64; we
  cast at the eval boundary. A future variant could ship a
  float32-native encoder if memory bandwidth in the encoder is
  itself a bottleneck.
- Default weights and JSON-loading semantics from
  :mod:`chess_spectral.engine.eval.spectral` are unchanged.
- The ``score = Σ_c w_c · ‖proj_c(v)‖²`` semantics are unchanged
  modulo the float32 precision drop.

The bench in :mod:`tests.bench_spectral_eval` measures the speedup;
the §20.20 notebook update records the empirical delta.
"""
from __future__ import annotations

from typing import Dict

import numpy as np

from chess_spectral.encoder import (
    encode_640, CHANNELS, ENCODING_DIM,
)
from chess_spectral.engine.eval.spectral import (
    Position2D, WeightsLike,
    DEFAULT_WEIGHTS, _resolve_weights,
)


# Per-channel slice bounds (mirrors spectral.py — kept local so this
# module doesn't reach into a private symbol of the sibling).
_CHANNEL_NAMES = [name for name, _start in CHANNELS]
_CHANNEL_SLICES: Dict[str, slice] = {}
for i, (name, start) in enumerate(CHANNELS):
    end = CHANNELS[i + 1][1] if i + 1 < len(CHANNELS) else ENCODING_DIM
    _CHANNEL_SLICES[name] = slice(start, end)


def channel_energies_f32(v: np.ndarray) -> Dict[str, float]:
    """Per-channel L2 energy computed in float32.

    Equivalent to :func:`chess_spectral.engine.eval.spectral.channel_energies`
    in semantics; differs only in dtype (float32 vs float64) for the
    sum-of-squares step. Returns Python floats (auto-promoted to
    float64 at the dict boundary, which is fine — the loss happens
    inside the per-channel sum, not at the boundary).
    """
    if v.shape != (ENCODING_DIM,):
        raise ValueError(
            f"expected shape ({ENCODING_DIM},); got {v.shape}"
        )
    if v.dtype != np.float32:
        v = v.astype(np.float32, copy=False)
    out: Dict[str, float] = {}
    for name in _CHANNEL_NAMES:
        block = v[_CHANNEL_SLICES[name]]
        # Sum of squares in float32. Promoted to Python float at the
        # dict boundary (loss-free up to that point).
        out[name] = float(np.dot(block, block))
    return out


def evaluate(position: Position2D,
             side_to_move: bool,
             *,
             weights: WeightsLike = None) -> float:
    """Float32-downstream spectral evaluation. Same surface as
    :func:`chess_spectral.engine.eval.spectral.evaluate`.

    The encoder is called identically (via :func:`encode_640`); the
    cast to float32 happens at the boundary. Weighted sum is in
    float32; the final return is promoted to Python float for the
    search core's evaluator contract.
    """
    v = encode_640(position).astype(np.float32, copy=False)
    energies = channel_energies_f32(v)
    w = _resolve_weights(weights)
    score = np.float32(0.0)
    for name in _CHANNEL_NAMES:
        score += np.float32(w.get(name, 1.0)) * np.float32(energies[name])
    if not side_to_move:
        score = -score
    return float(score)


def evaluate_breakdown(position: Position2D,
                       side_to_move: bool,
                       *,
                       weights: WeightsLike = None
                       ) -> Dict[str, float]:
    """Per-channel score contributions in float32. Same shape as
    :func:`chess_spectral.engine.eval.spectral.evaluate_breakdown`."""
    v = encode_640(position).astype(np.float32, copy=False)
    energies = channel_energies_f32(v)
    w = _resolve_weights(weights)
    sign = np.float32(1.0 if side_to_move else -1.0)
    return {
        name: float(sign * np.float32(w.get(name, 1.0))
                    * np.float32(energies[name]))
        for name in _CHANNEL_NAMES
    }


__all__ = [
    "evaluate",
    "evaluate_breakdown",
    "channel_energies_f32",
]

"""Channel-energy-from-hybrid spectral evaluator (1.13.0+ —
B-spike-3 path (a)).

Computes per-channel L2 energy directly from the
:class:`SpectralBIPHybrid2D` integer storage, **skipping the float
decode step entirely**. The mathematical identity that makes this
work:

    ‖v_c‖² = Σᵢ (sign_i × mag_i)² = Σᵢ mag_i²    (sign cancels in
                                                  squared sum)

So channel energy is a function of the magnitude portion only. With
per-channel scaling :data:`scale_c` and a magnitude_bits budget
``k``::

    ‖v_c‖² = (scale_c / max_q)² × Σᵢ mag_i²

where ``mag_i ∈ [0, max_q]`` is the quantized integer magnitude and
``max_q = 2^k - 1`` is the per-bit-budget normalizer. The integer
sum-of-squares is the load-bearing computation; the per-channel
scale-squared multiply is one float op per channel (10 / 11 total
across 2D / 4D).

Two evaluator entry points are exposed
--------------------------------------

  * :func:`evaluate(pos, side, *, magnitude_bits=8)` — encode the
    position to hybrid, then compute channel energy from it. The
    full per-call cost is dominated by the encode step (~700µs at
    typical positions). This variant is bench-comparable to
    :mod:`spectral.evaluate` and shows only a ~5% improvement
    standalone (the channel-energy step shrinks from ~70µs to
    ~7µs, but encode still runs).

  * :func:`evaluate_from_hybrid(hybrid, side, *, weights=None)` —
    takes a precomputed :class:`SpectralBIPHybrid2D` and skips
    encoding entirely. **This is where the big speedup lives** —
    ~10-100× over the full encode+evaluate path, depending on
    iteration scale. Used naturally by:

      * The §16 transposition table (path (b)) when caching
        hybrid vectors keyed by Zobrist
      * Saved-corpus retrieval pipelines that store hybrid vectors
        and want channel-energy-based filtering
      * Pyodide / chess4D-OC consumers that already have the
        hybrid form in memory

Acceptance — sign cancels exactly
---------------------------------

For 8-bit hybrid: per-channel-energy agreement vs the float64
baseline is well within the 1.12.0 round-trip cosine-sim envelope.
The sign portion is preserved exactly in the hybrid (BIP-clean per
notebook §20.14), so the only loss source is the magnitude
quantization — which only affects energy through the ``mag_i²``
term, not the ``sign × mag`` term. A position whose float64
channel energy is :data:`E` reports a hybrid channel energy of
:data:`E ± O(quantization_step²)` per dim, summed over the
channel block.

The bench in :mod:`tests.bench_spectral_eval` and the §20.20
notebook update record the empirical numbers.
"""
from __future__ import annotations

from typing import Dict

import numpy as np

from chess_spectral.encoder import (
    encode_640, CHANNELS, ENCODING_DIM,
)
from chess_spectral.encoder_bip_hybrid import (
    SpectralBIPHybrid2D,
    encode_2d_bip_hybrid,
    _hybrid_encode_2d,
    _unpack_4bit,
    N_CHANNELS_2D,
    CHANNEL_DIM_2D,
)
from chess_spectral.engine.eval.spectral import (
    Position2D, WeightsLike,
    DEFAULT_WEIGHTS, _resolve_weights,
)


# Channel name → (start, dim). Mirror spectral.py's layout.
_CHANNEL_NAMES = [name for name, _start in CHANNELS]
_CHANNEL_STARTS: Dict[str, int] = {}
_CHANNEL_DIMS: Dict[str, int] = {}
for i, (name, start) in enumerate(CHANNELS):
    end = CHANNELS[i + 1][1] if i + 1 < len(CHANNELS) else ENCODING_DIM
    _CHANNEL_STARTS[name] = start
    _CHANNEL_DIMS[name] = end - start

assert len(_CHANNEL_STARTS) == N_CHANNELS_2D
assert all(v == CHANNEL_DIM_2D for v in _CHANNEL_DIMS.values())


def channel_energies_from_hybrid(
    hybrid: SpectralBIPHybrid2D,
) -> Dict[str, float]:
    """Compute per-channel L2 energy directly from the hybrid
    representation, without decoding to a float vector.

    Returns the same dict shape as
    :func:`chess_spectral.engine.eval.spectral.channel_energies`,
    with values in float64 (Python floats).

    Implementation
    --------------

    The integer sum-of-squares per channel is computed as
    ``(magnitudes[ch] ** 2).sum()`` in uint16 / uint32 (fast numpy
    integer SIMD), then scaled by ``(scale_c / max_q)²`` for one
    float multiply per channel.

    For 4-bit hybrid, the magnitudes are packed nibbles; we unpack
    them to uint8 once before the per-channel iteration. (The
    unpack cost is ~5µs vs the channel-energy computation's ~2µs
    — small constant overhead at 4-bit.)
    """
    if hybrid.magnitude_bits == 4:
        magnitudes = _unpack_4bit(hybrid.magnitudes, ENCODING_DIM)
    else:
        magnitudes = hybrid.magnitudes  # uint8 already

    max_q = (1 << hybrid.magnitude_bits) - 1

    out: Dict[str, float] = {}
    for ch_idx, name in enumerate(_CHANNEL_NAMES):
        start = _CHANNEL_STARTS[name]
        dim = _CHANNEL_DIMS[name]
        block = magnitudes[start:start + dim].astype(np.uint32)
        # Integer sum of squares — SIMD-friendly on x86.
        ssq_int = int(np.dot(block, block))
        scale = float(hybrid.magnitude_scales[ch_idx])
        # Energy = (scale / max_q)² × ssq_int.
        out[name] = (scale / max_q) ** 2 * ssq_int
    return out


def evaluate_from_hybrid(
    hybrid: SpectralBIPHybrid2D,
    side_to_move: bool,
    *,
    weights: WeightsLike = None,
) -> float:
    """Spectral evaluation directly from a precomputed hybrid.

    **The fast path** — no encoder call, no float vector decode.
    Per-call cost is the integer sum-of-squares per channel +
    one float multiply per channel + the weighted sum.

    Use this when:
    - you already have a SpectralBIPHybrid2D (from TT cache, saved
      corpus, etc.)
    - you want channel-energy evaluation at a fraction of the cost
      of the encode-and-evaluate roundtrip

    The signature differs from :func:`evaluate` so the caller
    explicitly opts into the hybrid path. See
    :func:`evaluate` for the encode-and-evaluate variant.
    """
    energies = channel_energies_from_hybrid(hybrid)
    w = _resolve_weights(weights)
    score = 0.0
    for name in _CHANNEL_NAMES:
        score += w.get(name, 1.0) * energies[name]
    if not side_to_move:
        score = -score
    return float(score)


def evaluate(
    position: Position2D,
    side_to_move: bool,
    *,
    magnitude_bits: int = 8,
    weights: WeightsLike = None,
) -> float:
    """Encode the position to hybrid, then evaluate channel energy
    from it. Same surface as
    :func:`chess_spectral.engine.eval.spectral.evaluate`.

    The full per-call cost includes the encode step (~700µs at
    typical positions); only the channel-energy step is faster
    than the float64 baseline. For the cache-hit fast path, see
    :func:`evaluate_from_hybrid`.
    """
    # Reuse the existing encode_640 path so the encoder cost is
    # bench-comparable. Then quantize to hybrid in place.
    vec = encode_640(position)
    hybrid = _hybrid_encode_2d(vec, magnitude_bits)
    return evaluate_from_hybrid(hybrid, side_to_move, weights=weights)


# ─── 4D variants (1.14.0+ — parity restoration) ─────────────────────


def channel_energies_from_hybrid_4d(
    hybrid: "object",  # SpectralBIPHybrid4D — late-bound to avoid cycle
) -> Dict[str, float]:
    """4D analog of :func:`channel_energies_from_hybrid`.

    Computes per-channel L2 energy directly from the
    :class:`SpectralBIPHybrid4D` integer storage (11 channels ×
    4096 dims = 45 056 dims total). Same algebraic identity:
    ``‖v_c‖² = Σ mag²`` (sign cancels), so use uint32 sum-of-squares
    + per-channel scale² multiply.

    Returns
    -------
    dict[str, float]
        ``{channel_name: energy}`` with float64 values. Channel
        names mirror ``encoder_4d.CHANNELS_4D``: A1, STD4_X/Y/Z/W,
        FIB_SYM_1/2/3, FA_PAWN_W/Y, FD_DIAG.
    """
    from chess_spectral.encoder_bip_hybrid import (
        SpectralBIPHybrid4D, _unpack_4bit,
        N_CHANNELS_4D, CHANNEL_DIM_4D,
    )
    from chess_spectral.encoder_4d import CHANNELS_4D

    if not isinstance(hybrid, SpectralBIPHybrid4D):
        raise TypeError(
            f"expected SpectralBIPHybrid4D, got {type(hybrid).__name__}"
        )

    n_dims = N_CHANNELS_4D * CHANNEL_DIM_4D
    if hybrid.magnitude_bits == 4:
        magnitudes = _unpack_4bit(hybrid.magnitudes, n_dims)
    else:
        magnitudes = hybrid.magnitudes

    max_q = (1 << hybrid.magnitude_bits) - 1
    out: Dict[str, float] = {}
    for ch_idx, (name, _start) in enumerate(CHANNELS_4D):
        start = ch_idx * CHANNEL_DIM_4D
        block = magnitudes[start:start + CHANNEL_DIM_4D].astype(np.uint32)
        ssq_int = int(np.dot(block, block))
        scale = float(hybrid.magnitude_scales[ch_idx])
        out[name] = (scale / max_q) ** 2 * ssq_int
    return out


def evaluate_from_hybrid_4d(
    hybrid: "object",
    side_to_move: bool,
    *,
    weights: Optional[Dict[str, float]] = None,
) -> float:
    """4D analog of :func:`evaluate_from_hybrid`.

    Spectral evaluation directly from a precomputed
    :class:`SpectralBIPHybrid4D`; the 4D cache-hit fast path.

    Parameters
    ----------
    hybrid : SpectralBIPHybrid4D
    side_to_move : bool
        True = white to move, False = black.
    weights : dict[str, float] or None
        Per-channel weight overrides; ``None`` → equal weights
        (1.0 for all 11 channels). Channel names match
        ``CHANNELS_4D``.

    Returns
    -------
    float
        Score from side-to-move's perspective (positive = winning).
    """
    from chess_spectral.encoder_4d import CHANNELS_4D

    energies = channel_energies_from_hybrid_4d(hybrid)
    if weights is None:
        weights = {name: 1.0 for name, _ in CHANNELS_4D}
    score = 0.0
    for name, _start in CHANNELS_4D:
        score += weights.get(name, 1.0) * energies[name]
    if not side_to_move:
        score = -score
    return float(score)


def evaluate_4d(
    pos4: Dict[int, "object"],
    side_to_move: bool,
    *,
    magnitude_bits: int = 8,
    weights: Optional[Dict[str, float]] = None,
) -> float:
    """4D analog of :func:`evaluate` — encode + eval. Slower than
    the cache-hit fast path; bench-comparable to a hypothetical
    spectral_float64_4d evaluator."""
    from chess_spectral.encoder_bip_hybrid import (
        encode_4d_bip_hybrid,
    )
    hybrid = encode_4d_bip_hybrid(pos4, magnitude_bits=magnitude_bits)
    return evaluate_from_hybrid_4d(hybrid, side_to_move, weights=weights)


__all__ = [
    "evaluate",
    "evaluate_from_hybrid",
    "channel_energies_from_hybrid",
    # 1.14.0+ — 4D parity
    "evaluate_4d",
    "evaluate_from_hybrid_4d",
    "channel_energies_from_hybrid_4d",
]

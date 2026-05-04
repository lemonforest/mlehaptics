"""BIP-hybrid encoding for the spectral encoder (1.12.0 — B-spike-2).

Per notebook §20.12, the chess-spectral encoder's channels factor
naturally as ``sign × magnitude``: the sign is a Z₂ phase (BIP-clean),
the magnitude is a real positive scalar that needs separate
quantization. This module provides the **hybrid** integer-native
representation that packs the sign portion as 1 bit per dim and
quantizes the magnitude portion at a configurable bit budget.

Per-channel magnitude scaling
-----------------------------

Channel energies in chess-spectral span several orders of magnitude
(A1 ≈ 0 at startpos; F1/F2/F3 fiber gradients reach ~10³). A single
global magnitude scale would force small-magnitude channels into the
quantization noise floor. Instead, this module uses **per-channel
magnitude scaling**: each of the 10 (2D) / 11 (4D) channels gets its
own ``max(abs(magnitude))`` scale stored as a float32. Per-dim
magnitudes are quantized to ``[0, 2^k - 1]`` linearly within their
channel's range. This costs 40 bytes (2D) / 44 bytes (4D) of extra
storage but gives uniform relative precision across channels.

Storage budget
--------------

For 2D (640-dim base):

  * sign_packed    : 80 bytes  (640 bits, 1 per dim)
  * magnitude_scales: 40 bytes  (10 channels × 4 bytes)
  * magnitudes     : 320 / 640 bytes (4-bit / 8-bit per dim)
  * Total          : ~440-760 bytes vs 2560 bytes float32
                     = 3.4-5.8× compression

For 4D (45056-dim base):

  * sign_packed    : 5632 bytes
  * magnitude_scales: 44 bytes
  * magnitudes     : 22528 / 45056 bytes (4-bit / 8-bit per dim)
  * Total          : ~28-50 KB vs 180 KB float32
                     = 3.6-6.4× compression

The sign portion is **algebraically exact** (each dim's sign is
preserved as a bit). The magnitude portion is the only loss source;
its bit budget is the consumer's tradeoff between storage and
precision.

Cosine-similarity preservation
------------------------------

§20.15's acceptance gate: cosine-sim ≥ 99.5% median + ≥ 95%
worst-case on a test corpus at 8-bit magnitude quantization. The
sign portion preserves the per-dim sign exactly, so cosine-sim
agreement depends only on the magnitude quantization error. At
8-bit (256 levels per channel), per-dim relative error is ≤
1/255 ≈ 0.4%; cumulative cosine-sim error across 640 / 45056 dims
should be well under 0.5% in expectation.

What's NOT covered
------------------

§20.12's per-channel-taxonomy nuance is *not* implemented in this
first ship. Specifically:

  * A1 channel (D₄ trivial irrep) is "pure magnitude" — its sign
    is essentially always zero, so the sign bit is uninformative.
    A more refined encoder could skip the sign bit for A1 and save
    ~64 bits / 4096 bits (2D / 4D). Not done here; uniform
    treatment per dim.
  * E channel (D₄ 2-D irrep) is "genuinely 2-D phase" — could
    benefit from a complex-valued representation rather than
    sign×magnitude. Not done here; treated as sign × magnitude.
  * FA channel (antisymmetric pawn fiber) is "pure sign" — could
    skip the magnitude byte entirely. Not done here; magnitude
    encoded uniformly.

These are 1.13.0+ refinements if the per-channel optimization
matters empirically. For 1.12.0 the blanket sign × magnitude
encoding is the load-bearing first move; the §20.15 acceptance
gate is its falsifier.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

import numpy as np

from .encoder import (
    encode_640, ENCODING_DIM, BOARD_DIM, CHANNELS,
    normalize_pos,
)

if TYPE_CHECKING:
    from .encoder_4d import encode_4d  # noqa: F401


# ─── Public layout constants ────────────────────────────────────────

DEFAULT_MAGNITUDE_BITS: int = 8
"""Default magnitude quantization budget (8 bits per dim, 256 levels per
channel). Per §20.15's acceptance gate."""

VALID_MAGNITUDE_BITS: tuple[int, ...] = (4, 8)
"""Currently-supported magnitude bit budgets. 4-bit gives ~5.8×
compression with measurable cosine-sim loss; 8-bit gives ~3.4×
compression with negligible loss."""

# 2D layout
N_CHANNELS_2D: int = 10  # mirrors encoder.CHANNELS
CHANNEL_DIM_2D: int = BOARD_DIM  # 64

# 4D layout
N_CHANNELS_4D: int = 11
CHANNEL_DIM_4D: int = 4096


# ─── Hybrid representation ──────────────────────────────────────────


@dataclass(frozen=True)
class SpectralBIPHybrid2D:
    """BIP-hybrid encoded 2D spectral vector (1.12.0+).

    Three components, all integer / byte arrays at the wire level:

      * ``sign_packed``     : 80 bytes (640 sign bits, packed
                              little-endian — bit 0 of byte 0 is the
                              sign of dim 0, bit 7 of byte 79 is the
                              sign of dim 639). Sign convention:
                              0 = nonneg, 1 = negative.
      * ``magnitude_scales`` : ``np.ndarray`` shape (10,) float32 —
                              ``max(abs(vec[ch_start:ch_start+64]))``
                              per channel. Used to dequantize the
                              magnitude portion at decode.
      * ``magnitudes``      : ``np.ndarray`` shape (640,) of unsigned
                              integers (uint8 if bits=8; packed nibbles
                              in uint8 if bits=4). Magnitude in [0,
                              2^bits - 1] proportional to
                              ``abs(vec[i]) / magnitude_scales[ch]``.
      * ``magnitude_bits``  : 4 or 8 — the per-dim magnitude budget.
                              Wire contract; decoder must use the
                              same value as encoder.
    """

    sign_packed: bytes
    magnitude_scales: np.ndarray  # shape (10,) float32
    magnitudes: np.ndarray  # shape (640,) for 8-bit, (320,) for 4-bit packed
    magnitude_bits: int = DEFAULT_MAGNITUDE_BITS


@dataclass(frozen=True)
class SpectralBIPHybrid4D:
    """BIP-hybrid encoded 4D spectral vector (1.12.0+).

    Same shape as :class:`SpectralBIPHybrid2D` scaled to 4D's 45056
    dims and 11 channels:

      * ``sign_packed``     : 5632 bytes (45056 bits)
      * ``magnitude_scales`` : shape (11,) float32
      * ``magnitudes``      : shape (45056,) uint8 (8-bit) or (22528,)
                              uint8 (4-bit packed)
      * ``magnitude_bits``  : 4 or 8
    """

    sign_packed: bytes
    magnitude_scales: np.ndarray
    magnitudes: np.ndarray
    magnitude_bits: int = DEFAULT_MAGNITUDE_BITS


# ─── Sign-bit packing helpers ───────────────────────────────────────


def _pack_signs(signs: np.ndarray) -> bytes:
    """Pack a uint8 array of sign bits (0 = nonneg, 1 = negative)
    into ``bytes`` little-endian (bit 0 of byte 0 = signs[0])."""
    return np.packbits(signs.astype(np.uint8), bitorder="little").tobytes()


def _unpack_signs(packed: bytes, n_dims: int) -> np.ndarray:
    """Inverse of :func:`_pack_signs`: return a uint8 array of sign
    bits (0 = nonneg, 1 = negative) of length ``n_dims``."""
    arr = np.frombuffer(packed, dtype=np.uint8)
    bits = np.unpackbits(arr, bitorder="little")
    return bits[:n_dims].astype(np.uint8)


def _pack_4bit(values: np.ndarray) -> np.ndarray:
    """Pack a uint8 array (with values in [0, 15]) into a uint8 array
    half the length (two nibbles per byte; even index in low nibble)."""
    if len(values) % 2 != 0:
        # Pad to even length for clean packing; the decoder must know
        # the original length and discard the trailing nibble.
        values = np.append(values, np.uint8(0))
    low = values[0::2] & 0x0F
    high = (values[1::2] & 0x0F) << 4
    return (low | high).astype(np.uint8)


def _unpack_4bit(packed: np.ndarray, n_values: int) -> np.ndarray:
    """Inverse of :func:`_pack_4bit`. Returns a uint8 array of length
    ``n_values`` with values in [0, 15]."""
    out = np.empty(len(packed) * 2, dtype=np.uint8)
    out[0::2] = packed & 0x0F
    out[1::2] = (packed >> 4) & 0x0F
    return out[:n_values]


# ─── 2D encoding ────────────────────────────────────────────────────


def _channel_starts_2d() -> list[int]:
    """Return the 10 channel start offsets in the 2D vector
    (``[0, 64, 128, ..., 576]``). Mirrors :data:`CHANNELS`."""
    return [start for _, start in CHANNELS]


def encode_2d_bip_hybrid(
    pos,
    *,
    magnitude_bits: int = DEFAULT_MAGNITUDE_BITS,
    vals=None,
) -> SpectralBIPHybrid2D:
    """BIP-hybrid encoding for the 2D spectral encoder.

    Computes the float32 spectral vector via :func:`encode_640`,
    then factors each dim into (sign bit, quantized magnitude). Per-
    channel magnitude scaling: each channel's max(abs) is stored as
    float32 and used to normalize that channel's magnitudes into
    ``[0, 2^magnitude_bits - 1]``.

    Parameters
    ----------
    pos : dict
        Encoder-format position. See :func:`encode_640`.
    magnitude_bits : int, optional
        Magnitude quantization budget per dim. 4 or 8 supported;
        default 8. See :data:`VALID_MAGNITUDE_BITS`.
    vals : dict or None
        Piece-value table (passed through to :func:`encode_640`).

    Returns
    -------
    SpectralBIPHybrid2D
    """
    if magnitude_bits not in VALID_MAGNITUDE_BITS:
        raise ValueError(
            f"magnitude_bits must be one of {VALID_MAGNITUDE_BITS}; "
            f"got {magnitude_bits}"
        )

    vec = encode_640(pos, vals=vals)
    return _hybrid_encode_2d(vec, magnitude_bits)


def _hybrid_encode_2d(
    vec: np.ndarray,
    magnitude_bits: int,
) -> SpectralBIPHybrid2D:
    """Encode an already-computed 2D spectral vector to hybrid form.

    Useful when the caller has the float32 vector in hand (e.g. has
    already called :func:`encode_640` for other reasons) and doesn't
    want to recompute it.
    """
    if vec.shape != (ENCODING_DIM,):
        raise ValueError(
            f"expected shape ({ENCODING_DIM},); got {vec.shape}"
        )

    # Sign portion: 1 bit per dim. Convention: 0 = nonneg, 1 = negative.
    signs = (vec < 0).astype(np.uint8)
    sign_packed = _pack_signs(signs)

    # Per-channel magnitude scale.
    channel_starts = _channel_starts_2d()
    abs_vec = np.abs(vec)
    scales = np.empty(N_CHANNELS_2D, dtype=np.float32)
    for ch_idx, start in enumerate(channel_starts):
        ch_max = float(abs_vec[start:start + CHANNEL_DIM_2D].max())
        # Avoid division-by-zero on all-zero channels (e.g., A1 at
        # startpos). Store as zero scale; quantized values become 0.
        scales[ch_idx] = ch_max if ch_max > 0 else 1.0

    # Per-dim magnitude quantization: [0, 2^bits - 1].
    max_q = (1 << magnitude_bits) - 1
    magnitudes = np.empty(ENCODING_DIM, dtype=np.uint8)
    for ch_idx, start in enumerate(channel_starts):
        sl = slice(start, start + CHANNEL_DIM_2D)
        scale = float(scales[ch_idx])
        if scale > 0:
            normalized = abs_vec[sl] / scale  # in [0, 1]
        else:
            normalized = np.zeros_like(abs_vec[sl])
        magnitudes[sl] = np.clip(
            np.round(normalized * max_q), 0, max_q
        ).astype(np.uint8)

    if magnitude_bits == 4:
        magnitudes = _pack_4bit(magnitudes)

    return SpectralBIPHybrid2D(
        sign_packed=sign_packed,
        magnitude_scales=scales,
        magnitudes=magnitudes,
        magnitude_bits=magnitude_bits,
    )


def decode_2d_bip_hybrid(hybrid: SpectralBIPHybrid2D) -> np.ndarray:
    """Decode a 2D hybrid-encoded spectral vector back to float32.

    Lossy at the magnitude-quantization level; sign portion is
    reconstructed exactly. Output dtype is float64 to match
    :func:`encode_640`'s default.
    """
    n_dims = ENCODING_DIM
    if hybrid.magnitude_bits == 4:
        magnitudes = _unpack_4bit(hybrid.magnitudes, n_dims)
    else:
        magnitudes = hybrid.magnitudes
    if magnitudes.shape != (n_dims,):
        raise ValueError(
            f"magnitudes shape {magnitudes.shape} != ({n_dims},)"
        )

    signs = _unpack_signs(hybrid.sign_packed, n_dims)
    sign_factor = np.where(signs == 1, -1.0, 1.0)

    max_q = (1 << hybrid.magnitude_bits) - 1
    out = np.empty(n_dims, dtype=np.float64)
    channel_starts = _channel_starts_2d()
    for ch_idx, start in enumerate(channel_starts):
        sl = slice(start, start + CHANNEL_DIM_2D)
        scale = float(hybrid.magnitude_scales[ch_idx])
        # mag in [0, max_q]; recover float magnitude as
        # mag / max_q * scale.
        out[sl] = (magnitudes[sl].astype(np.float64) / max_q) * scale

    out *= sign_factor
    return out


# ─── 4D encoding ────────────────────────────────────────────────────


def _channel_starts_4d() -> list[int]:
    """4D has 11 channels of CHANNEL_DIM_4D=4096 each.
    [0, 4096, 8192, ..., 40960]."""
    return [i * CHANNEL_DIM_4D for i in range(N_CHANNELS_4D)]


def encode_4d_bip_hybrid(
    pos4,
    *,
    magnitude_bits: int = DEFAULT_MAGNITUDE_BITS,
    vals=None,
) -> SpectralBIPHybrid4D:
    """BIP-hybrid encoding for the 4D spectral encoder.

    Mirrors :func:`encode_2d_bip_hybrid` for the 4D encoder. 11
    channels × 4096 dims = 45056 dims total.

    Parameters
    ----------
    pos4 : dict
        4D-format position. See :func:`encode_4d`.
    magnitude_bits : int, optional
        Magnitude quantization budget per dim. 4 or 8 supported;
        default 8.
    vals : dict or None
        Piece-value table (passed through to :func:`encode_4d`).

    Returns
    -------
    SpectralBIPHybrid4D
    """
    if magnitude_bits not in VALID_MAGNITUDE_BITS:
        raise ValueError(
            f"magnitude_bits must be one of {VALID_MAGNITUDE_BITS}; "
            f"got {magnitude_bits}"
        )

    # Lazy import so the 2D-only path doesn't require 4D tables.
    from .encoder_4d import encode_4d, ENCODING_DIM_4D
    vec = encode_4d(pos4, vals=vals)
    if vec.shape != (ENCODING_DIM_4D,):
        raise ValueError(
            f"encode_4d returned shape {vec.shape}, expected "
            f"({ENCODING_DIM_4D},)"
        )
    return _hybrid_encode_4d(vec.astype(np.float64), magnitude_bits)


def _hybrid_encode_4d(
    vec: np.ndarray,
    magnitude_bits: int,
) -> SpectralBIPHybrid4D:
    """Encode an already-computed 4D spectral vector to hybrid form."""
    n_dims = N_CHANNELS_4D * CHANNEL_DIM_4D  # 45056

    signs = (vec < 0).astype(np.uint8)
    sign_packed = _pack_signs(signs)

    channel_starts = _channel_starts_4d()
    abs_vec = np.abs(vec)
    scales = np.empty(N_CHANNELS_4D, dtype=np.float32)
    for ch_idx, start in enumerate(channel_starts):
        ch_max = float(abs_vec[start:start + CHANNEL_DIM_4D].max())
        scales[ch_idx] = ch_max if ch_max > 0 else 1.0

    max_q = (1 << magnitude_bits) - 1
    magnitudes = np.empty(n_dims, dtype=np.uint8)
    for ch_idx, start in enumerate(channel_starts):
        sl = slice(start, start + CHANNEL_DIM_4D)
        scale = float(scales[ch_idx])
        if scale > 0:
            normalized = abs_vec[sl] / scale
        else:
            normalized = np.zeros_like(abs_vec[sl])
        magnitudes[sl] = np.clip(
            np.round(normalized * max_q), 0, max_q
        ).astype(np.uint8)

    if magnitude_bits == 4:
        magnitudes = _pack_4bit(magnitudes)

    return SpectralBIPHybrid4D(
        sign_packed=sign_packed,
        magnitude_scales=scales,
        magnitudes=magnitudes,
        magnitude_bits=magnitude_bits,
    )


def decode_4d_bip_hybrid(hybrid: SpectralBIPHybrid4D) -> np.ndarray:
    """Decode a 4D hybrid-encoded spectral vector back to float64.

    Lossy at the magnitude-quantization level; sign exact.
    """
    n_dims = N_CHANNELS_4D * CHANNEL_DIM_4D
    if hybrid.magnitude_bits == 4:
        magnitudes = _unpack_4bit(hybrid.magnitudes, n_dims)
    else:
        magnitudes = hybrid.magnitudes
    if magnitudes.shape != (n_dims,):
        raise ValueError(
            f"magnitudes shape {magnitudes.shape} != ({n_dims},)"
        )

    signs = _unpack_signs(hybrid.sign_packed, n_dims)
    sign_factor = np.where(signs == 1, -1.0, 1.0)

    max_q = (1 << hybrid.magnitude_bits) - 1
    out = np.empty(n_dims, dtype=np.float64)
    channel_starts = _channel_starts_4d()
    for ch_idx, start in enumerate(channel_starts):
        sl = slice(start, start + CHANNEL_DIM_4D)
        scale = float(hybrid.magnitude_scales[ch_idx])
        out[sl] = (magnitudes[sl].astype(np.float64) / max_q) * scale

    out *= sign_factor
    return out


# ─── Cosine similarity (the §20.15 acceptance metric) ───────────────


def cosine_similarity_hybrid_2d(
    a: SpectralBIPHybrid2D,
    b: SpectralBIPHybrid2D,
) -> float:
    """Cosine similarity between two hybrid-encoded 2D vectors.

    Decodes both back to float64 and computes
    ``<va, vb> / (|va| * |vb|)``. Returns 0.0 if either vector has
    zero norm (avoids division-by-zero on degenerate cases).
    """
    va = decode_2d_bip_hybrid(a)
    vb = decode_2d_bip_hybrid(b)
    norm_a = float(np.linalg.norm(va))
    norm_b = float(np.linalg.norm(vb))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return float(np.dot(va, vb) / (norm_a * norm_b))


def cosine_similarity_hybrid_4d(
    a: SpectralBIPHybrid4D,
    b: SpectralBIPHybrid4D,
) -> float:
    """Cosine similarity for two hybrid-encoded 4D vectors. Same
    contract as :func:`cosine_similarity_hybrid_2d`."""
    va = decode_4d_bip_hybrid(a)
    vb = decode_4d_bip_hybrid(b)
    norm_a = float(np.linalg.norm(va))
    norm_b = float(np.linalg.norm(vb))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return float(np.dot(va, vb) / (norm_a * norm_b))


# ─── Round-trip cosine-sim (the headline acceptance metric) ─────────


def round_trip_cosine_sim_2d(
    pos,
    *,
    magnitude_bits: int = DEFAULT_MAGNITUDE_BITS,
    vals=None,
) -> float:
    """Cosine similarity between ``encode_640(pos)`` and the
    hybrid-decode round trip ``decode_2d_bip_hybrid(encode_2d_bip_hybrid(pos))``.

    The §20.15 acceptance gate uses this on a corpus: median ≥ 99.5%
    and worst-case ≥ 95% at 8-bit means the hybrid encoding is
    information-preserving enough to ship.
    """
    original = encode_640(pos, vals=vals)
    hybrid = _hybrid_encode_2d(original, magnitude_bits)
    decoded = decode_2d_bip_hybrid(hybrid)
    norm_o = float(np.linalg.norm(original))
    norm_d = float(np.linalg.norm(decoded))
    if norm_o == 0.0 or norm_d == 0.0:
        return 0.0
    return float(np.dot(original, decoded) / (norm_o * norm_d))


def round_trip_cosine_sim_4d(
    pos4,
    *,
    magnitude_bits: int = DEFAULT_MAGNITUDE_BITS,
    vals=None,
) -> float:
    """4D analog of :func:`round_trip_cosine_sim_2d`."""
    from .encoder_4d import encode_4d
    original = encode_4d(pos4, vals=vals).astype(np.float64)
    hybrid = _hybrid_encode_4d(original, magnitude_bits)
    decoded = decode_4d_bip_hybrid(hybrid)
    norm_o = float(np.linalg.norm(original))
    norm_d = float(np.linalg.norm(decoded))
    if norm_o == 0.0 or norm_d == 0.0:
        return 0.0
    return float(np.dot(original, decoded) / (norm_o * norm_d))


# ─── Storage budget helpers ─────────────────────────────────────────


def storage_bytes_2d(magnitude_bits: int) -> int:
    """Bytes per position for the 2D hybrid encoding at the given
    magnitude bit budget. 80 sign + 40 scales + (640 / 320) magnitudes."""
    if magnitude_bits not in VALID_MAGNITUDE_BITS:
        raise ValueError(f"magnitude_bits must be in {VALID_MAGNITUDE_BITS}")
    sign_bytes = ENCODING_DIM // 8
    scale_bytes = N_CHANNELS_2D * 4
    if magnitude_bits == 8:
        mag_bytes = ENCODING_DIM
    else:  # 4-bit
        mag_bytes = (ENCODING_DIM + 1) // 2
    return sign_bytes + scale_bytes + mag_bytes


def storage_bytes_4d(magnitude_bits: int) -> int:
    """4D analog of :func:`storage_bytes_2d`."""
    if magnitude_bits not in VALID_MAGNITUDE_BITS:
        raise ValueError(f"magnitude_bits must be in {VALID_MAGNITUDE_BITS}")
    n_dims = N_CHANNELS_4D * CHANNEL_DIM_4D
    sign_bytes = n_dims // 8
    scale_bytes = N_CHANNELS_4D * 4
    if magnitude_bits == 8:
        mag_bytes = n_dims
    else:
        mag_bytes = (n_dims + 1) // 2
    return sign_bytes + scale_bytes + mag_bytes


# ─── Module exports ─────────────────────────────────────────────────


__all__ = [
    "DEFAULT_MAGNITUDE_BITS",
    "VALID_MAGNITUDE_BITS",
    "N_CHANNELS_2D", "CHANNEL_DIM_2D",
    "N_CHANNELS_4D", "CHANNEL_DIM_4D",
    "SpectralBIPHybrid2D",
    "SpectralBIPHybrid4D",
    "encode_2d_bip_hybrid",
    "decode_2d_bip_hybrid",
    "encode_4d_bip_hybrid",
    "decode_4d_bip_hybrid",
    "cosine_similarity_hybrid_2d",
    "cosine_similarity_hybrid_4d",
    "round_trip_cosine_sim_2d",
    "round_trip_cosine_sim_4d",
    "storage_bytes_2d",
    "storage_bytes_4d",
]

"""Pure-phase encoder for the 2D spectral chess encoder (1.14.0+ —
B-spike-4 from notebook §20.15).

The B-spike-4 design intent: compute the encoder's 640-dim output
**entirely in integer arithmetic**, eliminating the float64 hot path
and producing a same-shape output that downstream consumers can use
as a drop-in replacement.

What's in scope
---------------

The encoder's hot path decomposes into two structurally different
computations:

  * **D₄ irrep projection** (channels A1, A2, B1, B2, E — 5×64 = 320
    dims). The character formula
    ``proj[i] = Σ_g χ(g) · sig[g·i]`` is **already integer** at the
    core: ``CHARS`` is integer-valued (±1, ±2, 0), permutations are
    integer, and the only float operation is the final ``/8``
    scaling. Pure-phase implementation: drop the float scale (carry
    it as a per-channel integer dequantization factor) and use
    integer arithmetic throughout.

  * **Fiber channels** (F1/F2/F3 symmetric fiber, FA antisymmetric
    pawn, FD diagonal deviation — 5×64 = 320 dims). These use
    precomputed **float** tables (`LOCAL_FIBER_3D`,
    `PAWN_ANTI_FIBER`, `DIAG_DEV`) derived from the grid Laplacian
    eigendecomposition. Pure-phase implementation: quantize the
    tables to int16 at module load (one-time cost; per-table scale
    factor stored alongside) and use integer arithmetic in the
    accumulation, dequantizing at the channel-output boundary.

Output shape + dtype
--------------------

  * ``encode_2d_pure_phase(pos)`` → ``np.ndarray`` of shape ``(640,)``,
    dtype ``int32``. Each channel block has its own dequantization
    scale stored in ``CHANNEL_DEQUANT_SCALES``; consumers that want
    float64 values multiply the integer output by the per-channel
    scale (or use the convenience wrapper
    :func:`encode_2d_pure_phase_to_float`).

  * ``encode_2d_pure_phase_to_float(pos)`` → ``np.ndarray`` of shape
    ``(640,)``, dtype ``float64``. The integer output dequantized
    to float for direct comparison with :func:`encode_640`. Bench-
    comparable; cosine-sim parity tests use this form.

Empirical question
------------------

The §20.15 acceptance gate: cosine-sim with the float baseline
≥ 99% on every position. The user's session-stated framing:

> *"if it's better, that's awesome! if we find regression,
>  let's investigate."*

The bench harness records before/after numbers; the §20.21
notebook update documents whatever empirical answer comes back.

Piece-value choice
------------------

The float baseline encoder (:func:`encode_640`) uses ``SPECTRAL_VALS``
by default (mean-degree-normalized float values). The pure-phase
encoder uses **integer ``VALS``** by default (P=1, N=3, B=3, R=5,
Q=9, K=100). This is the natural choice — pure-phase math wants
integer signals — and the choice is documented in the encoder's
docstring + the §20.21 notebook update.

For cosine-sim parity, the comparison is between
``encode_2d_pure_phase(pos)`` and ``encode_640(pos, vals=VALS)``
(both with integer piece values). Comparing pure-phase against
``encode_640(pos)`` (float ``SPECTRAL_VALS``) introduces TWO
sources of variance — quantization and piece-value choice — and
muddles the bench. The piece-value question (does
``SPECTRAL_VALS`` produce better-correlated channel structure
than ``VALS``?) is empirically separate from the quantization
question.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Dict, Optional, Tuple

import numpy as np

from .tables import (
    BOARD_DIM, SHORT_PFNS, VALS,
    LOCAL_FIBER_3D, LOCAL_ADJ_ROWS,
    PAWN_ANTI_FIBER, DIAG_DEV,
    D4_PERMS, CHARS,
)
from .encoder import (
    ENCODING_DIM, CHANNELS, _PIECE_IDX, _FIBER_IDX,
    normalize_pos,
)


# ─── Module-level quantization (computed once) ──────────────────────


# Integer signed piece values, scaled by 2 so the half-integer
# bishop value (3.5 in VALS) survives as integer 7. Build at
# module load to avoid a per-call dict lookup.
#
# Why 2× scaling: VALS has B=3.5 / b=-3.5. A naive int(v)
# truncates 3.5 → 3, losing precision and breaking D₄-channel
# bit-exactness vs the float baseline. Scaling by 2 makes
# every value integer (P=2, N=6, B=7, R=10, Q=18, K=200), and
# the per-channel dequantization scale absorbs the factor of 1/2
# at output so the consumer sees the same floats as the baseline.
_VALS_INT_SCALE: int = 2

def _build_signed_vals_int_scaled() -> Dict[str, int]:
    out: Dict[str, int] = {}
    for k, v in VALS.items():
        scaled = v * _VALS_INT_SCALE
        if int(scaled) != scaled:
            raise ValueError(
                f"VALS[{k!r}] = {v} cannot be exactly represented as "
                f"integer × _VALS_INT_SCALE={_VALS_INT_SCALE}; need a "
                f"larger scale factor"
            )
        out[k] = int(scaled)
    return out


_SIGNED_VALS_INT: Dict[str, int] = _build_signed_vals_int_scaled()


# Quantization bit budget for the fiber tables. int16 = 65536
# levels; per-table max(abs) used as the scale factor, giving
# ~1/32767 relative precision per element. This is well below the
# float64 mantissa precision and well above the cosine-sim
# acceptance envelope.
_FIBER_QUANT_BITS: int = 15  # signed int16 = 1 sign bit + 15 magnitude bits
_FIBER_QUANT_MAX: int = (1 << _FIBER_QUANT_BITS) - 1  # 32767


def _quantize_table(arr: np.ndarray) -> Tuple[np.ndarray, float]:
    """Quantize a float array to int16 using max(abs) scaling.

    Returns ``(quantized, scale)`` where
    ``arr ≈ quantized.astype(float) * scale / _FIBER_QUANT_MAX``.

    For zero-magnitude inputs (no nonzero elements), returns
    ``(zeros, 1.0)`` — the all-zero array dequantizes to all-zero
    regardless of scale.
    """
    abs_max = float(np.abs(arr).max())
    if abs_max == 0.0:
        return np.zeros(arr.shape, dtype=np.int16), 1.0
    quantized = np.round(arr / abs_max * _FIBER_QUANT_MAX).astype(np.int16)
    return quantized, abs_max


# Precomputed integer-quantized fiber tables. Computed at module
# load; cost is small (~1 ms for ~5000-element tables) and
# amortized across all subsequent calls.
LOCAL_FIBER_3D_INT16, _SCALE_LOCAL_FIBER_3D = _quantize_table(LOCAL_FIBER_3D)
PAWN_ANTI_FIBER_INT16, _SCALE_PAWN_ANTI = _quantize_table(PAWN_ANTI_FIBER)
DIAG_DEV_INT16, _SCALE_DIAG_DEV = _quantize_table(DIAG_DEV)

# LOCAL_ADJ_ROWS is naturally integer (0/1). Cast to int8 for
# memory efficiency and SIMD-friendliness.
LOCAL_ADJ_ROWS_INT8: np.ndarray = LOCAL_ADJ_ROWS.astype(np.int8)


# ─── Channel layout + dequantization scales ─────────────────────────


# Per-channel dequantization scale: the integer output for channel
# c, when multiplied by ``CHANNEL_DEQUANT_SCALES[c]``, recovers the
# float64 channel-c output that ``encode_640(pos, vals=VALS)``
# would have produced. Computed below.

CHANNEL_DEQUANT_SCALES: Dict[str, float] = {}

# D₄ irrep channels: integer character formula × 8 = 64-element
# integer sum (no scale needed for the sum itself), then divide
# by 8 at output. The signal is scaled by _VALS_INT_SCALE=2 so
# we ALSO divide by that to recover float-baseline values.
# Combined: dequant = dim_mu / (8 × _VALS_INT_SCALE).
_DEQUANT_D4_SCALAR: float = 1.0 / (8.0 * _VALS_INT_SCALE)
for name in ('A1', 'A2', 'B1', 'B2'):
    CHANNEL_DEQUANT_SCALES[name] = _DEQUANT_D4_SCALAR  # dim_mu=1
CHANNEL_DEQUANT_SCALES['E'] = 2.0 * _DEQUANT_D4_SCALAR  # dim_mu=2

# Fiber channels: dequantize through the per-table scale factors.
# F1/F2/F3 use LOCAL_FIBER_3D × LOCAL_ADJ_ROWS × signal. The signal
# is scaled by _VALS_INT_SCALE so an additional 1/_VALS_INT_SCALE
# factor (or 1/_VALS_INT_SCALE² if signal appears twice via the
# adj_row · sig dot product times the adj_row accumulation —
# yes, signal-quadratic in the symmetric fiber).
#
# Symmetric fiber math:
#   gradient = adj_row · sig_int             [1× sig scale]
#   fc += gradient × fib_d_int × adj_row     [no further sig scale]
# So the symmetric fiber is signal-LINEAR (just one factor of
# _VALS_INT_SCALE), not quadratic. Dequant: 1/_VALS_INT_SCALE.
_FIBER_DEQUANT_FACTOR: float = (
    _SCALE_LOCAL_FIBER_3D / _FIBER_QUANT_MAX / _VALS_INT_SCALE
)
for name in ('F1', 'F2', 'F3'):
    CHANNEL_DEQUANT_SCALES[name] = _FIBER_DEQUANT_FACTOR

# FA: PAWN_ANTI_FIBER quantization × signed pawn weights. Pawn
# weights are integer (P=±1 in VALS), but my _board_signal_int
# scales by _VALS_INT_SCALE so pawn becomes ±2; FA accumulator
# uses _SIGNED_VALS_INT['P'] directly which is ±2. Dequant
# absorbs that factor.
CHANNEL_DEQUANT_SCALES['FA'] = (
    _SCALE_PAWN_ANTI / _FIBER_QUANT_MAX / _VALS_INT_SCALE
)

# FD: DIAG_DEV quantization × signed piece values from sig_int
# (already scaled by _VALS_INT_SCALE). Dequant absorbs.
CHANNEL_DEQUANT_SCALES['FD'] = (
    _SCALE_DIAG_DEV / _FIBER_QUANT_MAX / _VALS_INT_SCALE
)

# Channel start offsets in the 640-dim output (mirrors CHANNELS).
_CHANNEL_STARTS: Dict[str, int] = {name: start for name, start in CHANNELS}


# ─── Pure-phase encoder ─────────────────────────────────────────────


def _board_signal_int(pos: Dict[int, str],
                      vals: Optional[Dict[str, int]] = None
                      ) -> np.ndarray:
    """Integer 64-dim signal: scaled signed integer piece value at
    each occupied square. Returns int16.

    With ``_VALS_INT_SCALE = 2``, the king value 200 (= 100 × 2)
    exceeds int8's range [-128, 127], so int16 is required. int16
    is ample: 64 squares × max 200 per square = 12800, well within
    [-32768, 32767].
    """
    if vals is None:
        vals = _SIGNED_VALS_INT
    s = np.zeros(BOARD_DIM, dtype=np.int16)
    for si, p in pos.items():
        s[si] = vals[p]
    return s


def _project_irrep_int(sig_int: np.ndarray,
                       irrep_name: str) -> np.ndarray:
    """Pure-integer D₄ irrep projection. Returns int32 array of
    shape (64,).

    Output is the **character-weighted permutation sum** —
    ``Σ_g χ(g) · sig[g·i]``. The per-channel dequantization scale
    in :data:`CHANNEL_DEQUANT_SCALES` applies the full
    ``(dim_mu / 8)`` factor at the float boundary. We do NOT
    multiply by ``dim_mu`` here — that's part of the dequant
    scale, applied once at output.
    """
    chars = CHARS[irrep_name]
    projected = np.zeros(BOARD_DIM, dtype=np.int32)
    sig_int32 = sig_int.astype(np.int32, copy=False)
    for g_idx, perm in enumerate(D4_PERMS):
        c = chars[g_idx]
        if c == 0:
            continue  # skip zero-character contributions (E has 6 of these)
        if c == 1:
            projected += sig_int32[perm]
        elif c == -1:
            projected -= sig_int32[perm]
        else:
            projected += c * sig_int32[perm]
    return projected


def _fiber_symmetric_int(pos: Dict[int, str],
                         sig_int32: np.ndarray,
                         d: int) -> np.ndarray:
    """Integer-quantized symmetric fiber channel d (one of 0/1/2).

    Mirrors the float encoder's per-piece local fiber computation,
    but uses the int16-quantized LOCAL_FIBER_3D + int8 LOCAL_ADJ_ROWS.
    Returns int32 array of shape (64,).

    ``sig_int32`` is the signal pre-cast to int32 (caller hoists
    the cast outside the d loop to avoid the per-iteration
    allocation cost — measurable on the bench).
    """
    fc = np.zeros(BOARD_DIM, dtype=np.int32)
    for si, pchar in pos.items():
        pkey = pchar.upper()
        if pkey not in _FIBER_IDX:
            continue  # pawn — not in symmetric fiber
        pidx = _FIBER_IDX[pkey]
        adj_row_int8 = LOCAL_ADJ_ROWS_INT8[pidx, si]  # (64,) int8
        fib_d_int16 = int(LOCAL_FIBER_3D_INT16[pidx, si, d])
        if fib_d_int16 == 0:
            continue
        # gradient = adj_row · sig — numpy auto-promotes int8 × int32
        # → int32 result. Avoid the explicit .astype() allocation.
        gradient = int(np.dot(adj_row_int8, sig_int32))
        if gradient == 0:
            continue
        # fc += gradient * fib_d * adj_row. The product
        # ``gradient * fib_d_int16 * adj_row_int8`` requires int32
        # arithmetic to avoid overflow; numpy auto-promotes when
        # we add into the int32 fc accumulator.
        fc += np.multiply(adj_row_int8, gradient * fib_d_int16,
                          dtype=np.int32)
    return fc


def _fiber_antisymmetric_int(pos: Dict[int, str]) -> np.ndarray:
    """Integer-quantized FA channel (pawn antisymmetric fiber).

    Mirrors the float encoder's _fiber_antisymmetric. Pawn
    contributions only; the per-pawn weight is the integer pawn
    value (P=1 from VALS) signed by color.
    """
    out = np.zeros(BOARD_DIM, dtype=np.int32)
    val_p = _SIGNED_VALS_INT['P']  # +1 (white pawn)
    for si, pchar in pos.items():
        if pchar.upper() != 'P':
            continue
        weight = val_p if pchar == 'P' else -val_p
        # PAWN_ANTI_FIBER_INT16[si] is shape (64,) int16
        out += weight * PAWN_ANTI_FIBER_INT16[si].astype(np.int32)
    return out


def _fiber_diagonal_int(pos: Dict[int, str],
                        sig_int: np.ndarray) -> np.ndarray:
    """Integer-quantized FD channel (diagonal deviation).

    Mirrors the float encoder's _fiber_diagonal. Every occupied
    square contributes ``sig_int[si] * DIAG_DEV[piece_type]``.
    """
    out = np.zeros(BOARD_DIM, dtype=np.int32)
    for si, pchar in pos.items():
        t = _PIECE_IDX[pchar.upper()]  # 0..5 for P/N/B/R/Q/K
        coef = int(sig_int[si])
        if coef == 0:
            continue
        out += coef * DIAG_DEV_INT16[t].astype(np.int32)
    return out


def encode_2d_pure_phase(pos: Dict[int, str],
                         *,
                         vals: Optional[Dict[str, int]] = None
                         ) -> np.ndarray:
    """Pure-phase 2D spectral encoder (1.14.0+).

    Computes the same 640-dim output as :func:`encode_640` but
    using **integer arithmetic throughout**:

      * D₄ irrep projection: integer character × signal sums.
      * Symmetric fiber: int8 adjacency × int8 signal × int16
        quantized LOCAL_FIBER_3D, accumulated in int32.
      * Antisymmetric pawn fiber: int16 PAWN_ANTI_FIBER × signed
        pawn weights.
      * Diagonal deviation: int16 DIAG_DEV × signed piece values.

    Returns
    -------
    np.ndarray, shape (640,), dtype int32
        Per-channel integer output. Each channel block has its own
        dequantization scale; multiply by
        :data:`CHANNEL_DEQUANT_SCALES[channel_name]` to recover the
        float64 value comparable to :func:`encode_640` (with
        integer ``vals=VALS``).

    Notes
    -----

    Default piece values are integer ``VALS`` (P=1, N=3, B=3, R=5,
    Q=9, K=100), not the float ``SPECTRAL_VALS`` used by
    :func:`encode_640`'s default. For cosine-sim parity tests, use
    ``encode_640(pos, vals=VALS)`` as the baseline — that isolates
    the quantization-vs-float-arithmetic axis from the piece-value
    axis.
    """
    pos = normalize_pos(pos)
    sig_int = _board_signal_int(pos, vals=vals)
    # Hoist the int8 → int32 cast outside the d loop in fiber sym.
    # Measurable on the bench: avoids 3 redundant 64-element
    # allocations per encode call.
    sig_int32 = sig_int.astype(np.int32, copy=False)

    out = np.empty(ENCODING_DIM, dtype=np.int32)

    # D₄ irreps (channels 0-4)
    for i, name in enumerate(('A1', 'A2', 'B1', 'B2', 'E')):
        out[i * BOARD_DIM:(i + 1) * BOARD_DIM] = _project_irrep_int(
            sig_int, name)

    # Symmetric fiber (channels 5-7) — pass pre-cast int32 signal
    for d in range(3):
        out[(5 + d) * BOARD_DIM:(6 + d) * BOARD_DIM] = _fiber_symmetric_int(
            pos, sig_int32, d)

    # Antisymmetric pawn fiber (channel 8)
    out[8 * BOARD_DIM:9 * BOARD_DIM] = _fiber_antisymmetric_int(pos)

    # Diagonal deviation (channel 9)
    out[9 * BOARD_DIM:10 * BOARD_DIM] = _fiber_diagonal_int(pos, sig_int)

    return out


def encode_2d_pure_phase_to_float(pos: Dict[int, str],
                                  *,
                                  vals: Optional[Dict[str, int]] = None
                                  ) -> np.ndarray:
    """Pure-phase encoder with per-channel dequantization to float64.

    Returns the float64 array that approximates
    ``encode_640(pos, vals=VALS)`` — the natural baseline for
    cosine-sim parity tests.

    Returns
    -------
    np.ndarray, shape (640,), dtype float64
    """
    int_out = encode_2d_pure_phase(pos, vals=vals)
    out = np.empty(ENCODING_DIM, dtype=np.float64)
    for name, start in CHANNELS:
        scale = CHANNEL_DEQUANT_SCALES[name]
        out[start:start + BOARD_DIM] = (
            int_out[start:start + BOARD_DIM].astype(np.float64) * scale
        )
    return out


__all__ = [
    "encode_2d_pure_phase",
    "encode_2d_pure_phase_to_float",
    "CHANNEL_DEQUANT_SCALES",
    "LOCAL_FIBER_3D_INT16",
    "PAWN_ANTI_FIBER_INT16",
    "DIAG_DEV_INT16",
    "LOCAL_ADJ_ROWS_INT8",
]

"""Pure-phase encoder for the 4D spectral chess encoder (1.15.0+ —
4D parity restoration for B-spike-4 from notebook §20.15).

The 1.14.0 ship of B-spike-4 was 2D-only; the 1.14.0 amendment 1
restored the 4D evaluator-side parity but **deferred** the 4D pure-
phase encoder itself — `encode_4d_pure_phase` was documented in the
notebook §20.21 amendment as deferred to 1.15.0+. This module
ships that deferral.

Why the 4D pure-phase encoder is a different design from 2D
-----------------------------------------------------------

The 2D encoder's hot path decomposes into:

  * **D₄ irrep projection** (5 channels, 320 dims). Naturally
    integer because D₄'s character formula uses χ ∈ {±1, ±2, 0} and
    permutations are integer.
  * **Fiber channels** (5 channels, 320 dims). Float tables
    (LOCAL_FIBER_3D / PAWN_ANTI_FIBER / DIAG_DEV) quantizable to
    int16 with per-table scaling.

The 4D encoder's hot path decomposes into:

  * **A_1 orbit projection** (1 channel, 4096 dims). Sparse
    matrix-vector ``P_A1 @ sig`` where ``P_A1`` has entries
    ``1/orbit_size``. **Not** an integer character formula — but
    every orbit size divides ``|B_4| = 384``, so multiplying P_A1
    by 384 makes ALL entries integer (orbit_size is always a
    divisor of 384). We carry the 1/384 factor as a per-channel
    dequantization scale.
  * **STD4 coordinate residuals** (4 channels, 16 384 dims).
    ``coord_resid[a, i] × sig[i]`` where ``coord_resid`` has values
    in ``{-3.5, -2.5, ..., +3.5}`` (centered on lattice mean = 0).
    Scaling by 2 makes all entries integer (``{-7, -5, ..., +7}``).
    We carry the ``1/2`` factor as a dequantization scale.
  * **Fiber-symmetric channels** (3 channels, 12 288 dims). Same
    structure as 2D fiber-sym but with 4D adjacencies and the rank-3
    cross-piece SVD basis (FIBER_LOCAL is 5 × 4096 × 3). int16
    quantization with per-table scale, identical to 2D.
  * **Pawn antisymmetric channels** (2 channels, 8 192 dims). DCT
    blocks ``W_ANTI_DCT`` and ``Y_ANTI_DCT``, both 8 × 8 floats.
    int16 quantization per table.
  * **Diagonal deviation** (1 channel, 4096 dims). ``DIAG_DEV`` is
    6 × 4096 floats. int16 quantization.

The "no integer character formula" remark in the 1.14.0 amendment
referred specifically to a uniform character-table approach. The
sparse-projector + scale-by-LCM approach gives the same
"integer-arithmetic-throughout" property without needing characters.

Output shape + dtype
--------------------

  * ``encode_4d_pure_phase(pos4)`` → ``np.ndarray`` of shape
    ``(45056,)``, dtype ``int32``. Channel layout matches
    :data:`chess_spectral.encoder_4d.CHANNELS_4D`.

  * ``encode_4d_pure_phase_to_float(pos4)`` → ``np.ndarray`` of shape
    ``(45056,)``, dtype ``float64``. The integer output dequantized
    per-channel using :data:`CHANNEL_DEQUANT_SCALES_4D`.

Piece-value choice
------------------

The float baseline encoder (:func:`chess_spectral.encoder_4d.encode_4d`)
uses ``PIECE_VALUES_4D`` by default (P=1, N=3, B=3.25, R=5, Q=9,
K=12). Note B=3.25 — half-integer-and-a-quarter, NOT integer. This
forces ``_VALS_INT_SCALE_4D = 4`` (vs the 2D encoder's
``_VALS_INT_SCALE = 2`` for B=3.5):

  * P=4, N=12, B=13, R=20, Q=36, K=48 (all small ints, fit int8 with
    margin)
  * Max 4096-cell signal: 4096 × 48 = 196 608 (fits int32 easily)
  * Max orbit-sum (P_A1 path): 384 × 48 = 18 432 per output cell

For cosine-sim parity, the test compares
``encode_4d_pure_phase(pos4, vals=PIECE_VALUES_4D)`` against
``encode_4d(pos4, vals=PIECE_VALUES_4D)`` — same vals, isolating the
quantization-vs-float axis from any piece-value choice.

Acceptance gate
---------------

Mirrors §20.15's 2D gate: cosine-sim with the float baseline
≥ 99% on every position. Also:

  * A_1 channel: should be **bit-exact** after dequantization (the
    P_A1 × 384 scaling is lossless; sig_int = sig_float × 4 is
    lossless for PIECE_VALUES_4D).
  * STD4 channels: should also be bit-exact (coord_resid × 2 is
    lossless for the half-integer-with-half-step values).
  * Fiber / pawn / diag channels: lossy at the int16 quantization
    level, governed by ``_FIBER_QUANT_BITS = 15`` precision.
"""
from __future__ import annotations

from typing import Dict, Optional, Tuple

import numpy as np
from scipy.sparse import csr_matrix

from chess_spectral import tables_4d as t4
from chess_spectral.encoder_4d import (
    ENCODING_DIM_4D, N_CHANNELS_4D, CHANNEL_DIM, CHANNELS_4D,
    PIECE_VALUES_4D, PieceValue,
    _DIAG_DEV_ROW, _FIBER_IDX_4D,
    _is_pawn, _piece_char, _pawn_axis, _load_tables,
)


# ─── Module-level quantization (computed once) ──────────────────────


# Integer signal scale: handles the half-integer-quarter bishop value
# (B=3.25 in PIECE_VALUES_4D) by scaling all values by 4.
#
# Why 4 (not 2 like 2D): the 2D encoder's VALS table has B=3.5, so
# scale 2 makes B → 7 (integer). The 4D PIECE_VALUES_4D has B=3.25,
# which needs scale 4 to give B → 13 (integer). Chose the smallest
# scale that exactly represents every default piece value.
_VALS_INT_SCALE_4D: int = 4


def _build_signed_vals_int_scaled_4d() -> Dict[str, int]:
    out: Dict[str, int] = {}
    for k, v in PIECE_VALUES_4D.items():
        scaled = v * _VALS_INT_SCALE_4D
        if int(scaled) != scaled:
            raise ValueError(
                f"PIECE_VALUES_4D[{k!r}] = {v} cannot be exactly "
                f"represented as integer × _VALS_INT_SCALE_4D="
                f"{_VALS_INT_SCALE_4D}; need a larger scale factor"
            )
        out[k] = int(scaled)
    return out


_SIGNED_VALS_INT_4D: Dict[str, int] = _build_signed_vals_int_scaled_4d()


# Quantization bit budget for the fiber tables — same as 2D.
_FIBER_QUANT_BITS: int = 15  # signed int16 = 1 sign + 15 magnitude bits
_FIBER_QUANT_MAX: int = (1 << _FIBER_QUANT_BITS) - 1  # 32767


# Multiplier for the A_1 orbit projector that makes every entry
# integer. ``|B_4| = 384`` and every orbit size divides 384, so
# ``round(P_A1 * 384)`` has integer entries (specifically, divisors
# of 384). Carried as part of the A_1 dequantization scale.
_P_A1_INT_SCALE: int = 384

# Multiplier for the STD4 coord_resid table that makes every entry
# integer. coord_resid is computed as ``c[a] - mean(c)`` where
# ``c[a] ∈ {-3.5, -2.5, ..., +3.5}`` (step 1) and ``mean(c)`` is the
# average of 4 such half-integers (so ``mean(c)`` is in
# ``{..., -3.5, -3.25, ..., +3.5}`` with step 0.25). The residual is
# therefore a **quarter-integer** (multiple of 0.25), and scale 4
# makes every entry exactly integer. Empirical range on the standard
# 8^4 lattice: int8 entries in ``[-21, +21]``.
_COORD_RESID_INT_SCALE: int = 4


def _quantize_table(arr: np.ndarray) -> Tuple[np.ndarray, float]:
    """Quantize a float array to int16 using max(abs) scaling.

    Returns ``(quantized, scale)`` where
    ``arr ≈ quantized.astype(float) * scale / _FIBER_QUANT_MAX``.

    For zero-magnitude inputs (no nonzero elements), returns
    ``(zeros, 1.0)`` — the all-zero array dequantizes to all-zero
    regardless of scale.

    Mirrors :func:`chess_spectral.encoder_pure_phase._quantize_table`
    exactly; duplicated to avoid a cross-module import cycle (the 2D
    pure-phase module imports from `.tables`, the 4D from
    `chess_spectral.tables_4d`).
    """
    abs_max = float(np.abs(arr).max())
    if abs_max == 0.0:
        return np.zeros(arr.shape, dtype=np.int16), 1.0
    quantized = np.round(arr / abs_max * _FIBER_QUANT_MAX).astype(np.int16)
    return quantized, abs_max


def _quantize_p_a1_to_int(P_A1: csr_matrix) -> csr_matrix:
    """Convert the float-valued A_1 orbit projector to an integer-
    valued sparse matrix with entries ``round(384 / orbit_size)``.

    Lossless by construction: every ``P_A1`` entry is ``1/orbit_size``
    where ``orbit_size`` divides ``|B_4| = 384``. So
    ``P_A1[i, j] × 384 = 384 / orbit_size`` is always an integer
    (and small — at most 384, at least 1).

    The integer values fit comfortably in ``int16`` (max 384). The
    indices/indptr arrays are reused unchanged.
    """
    P_int_data = np.round(P_A1.data * _P_A1_INT_SCALE).astype(np.int32)
    # Verify the scaling is exact (orbit-size divides 384 always; this
    # is a structural property of B_4 acting on the 8^4 lattice).
    if not np.allclose(
        P_int_data.astype(np.float64) / _P_A1_INT_SCALE,
        P_A1.data, atol=1e-12,
    ):
        raise ValueError(
            f"P_A1 orbit projector entries don't scale exactly by "
            f"{_P_A1_INT_SCALE}; non-standard B_4 orbit structure?"
        )
    return csr_matrix(
        (P_int_data, P_A1.indices, P_A1.indptr), shape=P_A1.shape,
    )


# ─── Lazy table cache (mirrors encoder_4d._load_tables) ─────────────


_QUANT_CACHE: Dict[str, object] = {}


def _build_quant_tables() -> Dict[str, object]:
    """Build & cache the integer-quantized tables.

    First call: pulls the float tables via :func:`_load_tables`,
    quantizes each appropriately, stores in ``_QUANT_CACHE``. The
    cost is ~5 ms on a typical machine; amortized across all
    subsequent encode calls.
    """
    if _QUANT_CACHE:
        return _QUANT_CACHE

    tables = _load_tables()

    # A_1 orbit projector → integer (lossless via × 384).
    _QUANT_CACHE['P_A1_INT'] = _quantize_p_a1_to_int(tables['P_A1'])

    # STD4 coord_resid → integer (lossless via × 2).
    coord_resid = tables['coord_resid']
    coord_resid_scaled = np.round(
        coord_resid * _COORD_RESID_INT_SCALE
    ).astype(np.int8)
    if not np.allclose(
        coord_resid_scaled.astype(np.float64) / _COORD_RESID_INT_SCALE,
        coord_resid, atol=1e-12,
    ):
        raise ValueError(
            f"coord_resid not exactly representable as int8 / "
            f"{_COORD_RESID_INT_SCALE}; lattice not centered as expected?"
        )
    _QUANT_CACHE['coord_resid_int8'] = coord_resid_scaled

    # Fiber tables → int16 with per-table max-abs scale (lossy).
    fiber_local_int16, scale_fiber = _quantize_table(tables['FIBER_LOCAL'])
    _QUANT_CACHE['FIBER_LOCAL_INT16'] = fiber_local_int16
    _QUANT_CACHE['scale_fiber'] = scale_fiber

    w_anti_int16, scale_w = _quantize_table(tables['W_ANTI_DCT'])
    _QUANT_CACHE['W_ANTI_DCT_INT16'] = w_anti_int16
    _QUANT_CACHE['scale_w_anti_dct'] = scale_w

    y_anti_int16, scale_y = _quantize_table(tables['Y_ANTI_DCT'])
    _QUANT_CACHE['Y_ANTI_DCT_INT16'] = y_anti_int16
    _QUANT_CACHE['scale_y_anti_dct'] = scale_y

    diag_int16, scale_diag = _quantize_table(tables['DIAG_DEV'])
    _QUANT_CACHE['DIAG_DEV_INT16'] = diag_int16
    _QUANT_CACHE['scale_diag_dev'] = scale_diag

    # PIECE_ADJ already binary (0/1) sparse — keep as-is.
    _QUANT_CACHE['PIECE_ADJ'] = tables['PIECE_ADJ']

    return _QUANT_CACHE


# ─── Channel dequantization scales ──────────────────────────────────


# Per-channel dequantization scale: the integer output for channel
# c, when multiplied by ``CHANNEL_DEQUANT_SCALES_4D[c]``, recovers
# the float64 channel-c output that
# ``encode_4d(pos4, vals=PIECE_VALUES_4D)`` would have produced.
#
# Populated lazily on first call to :func:`_ensure_dequant_scales`
# (which fires when either ``encode_4d_pure_phase_to_float`` or
# direct ``CHANNEL_DEQUANT_SCALES_4D`` access is requested).

CHANNEL_DEQUANT_SCALES_4D: Dict[str, float] = {}


def _ensure_dequant_scales() -> None:
    if CHANNEL_DEQUANT_SCALES_4D:
        return
    qt = _build_quant_tables()

    # Channel 0 (A_1):
    #   out_int = (P_A1 × 384) @ sig_int
    #           = 384 × _VALS × (P_A1 @ sig_float)
    #   ⇒ dequant = 1 / (384 × _VALS_INT_SCALE_4D)
    CHANNEL_DEQUANT_SCALES_4D['A1'] = (
        1.0 / (_P_A1_INT_SCALE * _VALS_INT_SCALE_4D)
    )

    # Channels 1-4 (STD4_X/Y/Z/W):
    #   out_int = (coord_resid × 2) × sig_int
    #           = 2 × _VALS × (coord_resid × sig_float)
    #   ⇒ dequant = 1 / (2 × _VALS_INT_SCALE_4D)
    std4_dequant = 1.0 / (_COORD_RESID_INT_SCALE * _VALS_INT_SCALE_4D)
    for axis in ('X', 'Y', 'Z', 'W'):
        CHANNEL_DEQUANT_SCALES_4D[f'STD4_{axis}'] = std4_dequant

    # Channels 5-7 (FIB_SYM_*):
    #   gradient_int = sig_int[adj].sum() = _VALS × gradient_float
    #   fib_d_int    = 32767 × fib_d_float / scale_fiber
    #   out_int     += gradient_int × fib_d_int × adj_row
    #               = (_VALS × 32767 / scale_fiber) × out_float
    #   ⇒ dequant = scale_fiber / (32767 × _VALS_INT_SCALE_4D)
    fib_dequant = (
        qt['scale_fiber'] / _FIBER_QUANT_MAX / _VALS_INT_SCALE_4D
    )
    for i in range(1, 4):
        CHANNEL_DEQUANT_SCALES_4D[f'FIB_SYM_{i}'] = fib_dequant

    # Channels 8-9 (FA_PAWN_W/Y):
    #   out_int += sign × W_ANTI_DCT_INT16[sw]
    #          = (32767 / scale_w) × out_float
    #   No _VALS factor — the float encoder uses sign (±1) directly,
    #   not the pawn piece value.
    #   ⇒ dequant = scale_w / 32767
    CHANNEL_DEQUANT_SCALES_4D['FA_PAWN_W'] = (
        qt['scale_w_anti_dct'] / _FIBER_QUANT_MAX
    )
    CHANNEL_DEQUANT_SCALES_4D['FA_PAWN_Y'] = (
        qt['scale_y_anti_dct'] / _FIBER_QUANT_MAX
    )

    # Channel 10 (FD_DIAG):
    #   out_int += sig_int[s] × DIAG_DEV_INT16[row]
    #          = (_VALS × 32767 / scale_diag) × out_float
    #   ⇒ dequant = scale_diag / (32767 × _VALS_INT_SCALE_4D)
    CHANNEL_DEQUANT_SCALES_4D['FD_DIAG'] = (
        qt['scale_diag_dev'] / _FIBER_QUANT_MAX / _VALS_INT_SCALE_4D
    )


# ─── Signal construction ────────────────────────────────────────────


def _board_signal_int_4d(
    pos4: Dict[int, PieceValue],
    vals: Optional[Dict[str, int]] = None,
) -> np.ndarray:
    """Integer 4096-vector of signed scaled piece values per square.

    Returns int16. With the default ``_VALS_INT_SCALE_4D = 4``, the
    king value 48 = 12 × 4 is well within int8 range; we use int16
    anyway to give headroom for non-default ``vals`` dicts that might
    have larger values.
    """
    if vals is None:
        vals = _SIGNED_VALS_INT_4D
    sig = np.zeros(t4.N_SQUARES, dtype=np.int16)
    for k, pval in pos4.items():
        s = int(k)
        if not (0 <= s < t4.N_SQUARES):
            raise ValueError(f"square index {s} out of range [0, 4096)")
        pchar = _piece_char(pval)
        if pchar not in vals:
            raise ValueError(f"unknown piece char {pchar!r}")
        sig[s] = vals[pchar]
    return sig


# ─── Pure-phase encoder ─────────────────────────────────────────────


def encode_4d_pure_phase(
    pos4: Dict[int, PieceValue],
    *,
    vals: Optional[Dict[str, int]] = None,
) -> np.ndarray:
    """Pure-phase 4D spectral encoder (1.15.0+).

    Computes the same 45 056-dim output as :func:`encode_4d` but
    using **integer arithmetic throughout**:

      * **A_1 channel**: sparse ``P_A1_INT @ sig_int`` (P_A1 scaled
        by 384 to make all entries integer; lossless).
      * **STD4 channels**: ``coord_resid_int8 × sig_int``
        elementwise (coord_resid scaled by 2; lossless).
      * **Fiber-symmetric channels**: int8 adjacency × int16 signal
        × int16 quantized FIBER_LOCAL (lossy at int16 precision).
      * **Pawn antisymmetric channels**: int16 quantized
        W_ANTI_DCT / Y_ANTI_DCT × signed pawn weight (±1).
      * **Diagonal deviation channel**: int16 quantized DIAG_DEV ×
        signed piece values (sig_int).

    Returns
    -------
    np.ndarray, shape (45056,), dtype int32
        Per-channel integer output. Each channel block has its own
        dequantization scale; multiply by
        :data:`CHANNEL_DEQUANT_SCALES_4D[channel_name]` to recover
        the float64 value comparable to
        :func:`chess_spectral.encoder_4d.encode_4d`.

    Notes
    -----

    The default piece-value scaling is ``_VALS_INT_SCALE_4D = 4``
    (handles the bishop value 3.25 in ``PIECE_VALUES_4D``). Custom
    ``vals`` dicts must already contain integer values; non-integer
    entries are accepted only if the integer signal-construction
    sees integer values (i.e., callers pre-scale themselves).
    """
    qt = _build_quant_tables()
    _ensure_dequant_scales()

    sig_int = _board_signal_int_4d(pos4, vals=vals)
    # Hoist int16 → int32 cast (matmul + accumulation need int32).
    sig_int32 = sig_int.astype(np.int32, copy=False)

    out = np.zeros(ENCODING_DIM_4D, dtype=np.int32)

    # ── Channel 0 (A_1): sparse matvec on integer projector ──
    P_A1_INT = qt['P_A1_INT']  # type: ignore[assignment]
    a1_int = (P_A1_INT @ sig_int32)  # type: ignore[operator]
    # Result dtype depends on scipy's promotion; force int32.
    out[0:CHANNEL_DIM] = np.asarray(a1_int, dtype=np.int32)

    # ── Channels 1-4 (STD4_X/Y/Z/W): coord_resid × sig elementwise ──
    coord_resid_int8 = qt['coord_resid_int8']  # type: ignore[assignment]
    for a in range(t4.N_DIMS):
        start = (1 + a) * CHANNEL_DIM
        # int8 × int32 → int32 (numpy auto-promotes).
        out[start:start + CHANNEL_DIM] = (
            coord_resid_int8[a].astype(np.int32) * sig_int32  # type: ignore[index]
        )

    # ── Channels 5-7 (FIB_SYM): mirror float encoder semantics ──
    FIBER_LOCAL_INT16 = qt['FIBER_LOCAL_INT16']  # type: ignore[assignment]
    PIECE_ADJ = qt['PIECE_ADJ']  # type: ignore[assignment]
    sorted_items = sorted(pos4.items(), key=lambda kv: int(kv[0]))
    for d in range(3):
        # int64 accumulator: per-piece contribution can reach
        # |gradient × fib_d| ≈ 5e3 × 32767 ≈ 1.6e8, accumulated
        # across up to 64 occupied squares → 1e10, exceeds int32.
        fc = np.zeros(CHANNEL_DIM, dtype=np.int64)
        for k, pval in sorted_items:
            pkey = _piece_char(pval).upper()
            if pkey not in _FIBER_IDX_4D:
                continue  # skip pawn — handled in FA channels
            pidx = _FIBER_IDX_4D[pkey]
            s = int(k)
            row = PIECE_ADJ[pidx].getrow(s)  # type: ignore[index]
            cols = row.indices
            if cols.size == 0:
                continue
            gradient = int(sig_int32[cols].sum())
            if gradient == 0:
                continue
            fib_d = int(FIBER_LOCAL_INT16[pidx, s, d])  # type: ignore[index]
            if fib_d == 0:
                continue
            # fc[cols] += gradient × fib_d (scalar broadcasts to cols).
            fc[cols] += gradient * fib_d
        start = (5 + d) * CHANNEL_DIM
        out[start:start + CHANNEL_DIM] = fc.astype(np.int32)

    # ── Channels 8-9 (FA_PAWN_W, FA_PAWN_Y) ──
    W_ANTI_DCT_INT16 = qt['W_ANTI_DCT_INT16']  # type: ignore[assignment]
    Y_ANTI_DCT_INT16 = qt['Y_ANTI_DCT_INT16']  # type: ignore[assignment]
    pawn_w = np.zeros(CHANNEL_DIM, dtype=np.int64)
    pawn_y = np.zeros(CHANNEL_DIM, dtype=np.int64)
    for k, pval in sorted_items:
        if not _is_pawn(pval):
            continue
        color = _piece_char(pval)
        sign = 1 if color == 'P' else -1
        axis = _pawn_axis(pval)
        s = int(k)
        sx = (s >> 9) & 7
        sy = (s >> 6) & 7
        sz = (s >> 3) & 7
        sw = s & 7
        if axis == 'w':
            base = (sx << 9) | (sy << 6) | (sz << 3)
            pawn_w[base:base + 8] += (
                sign * W_ANTI_DCT_INT16[sw].astype(np.int64)  # type: ignore[index]
            )
        else:  # axis == 'y'
            base = (sx << 9) | (sz << 3) | sw
            idx = base | (np.arange(8) << 6)
            pawn_y[idx] += (
                sign * Y_ANTI_DCT_INT16[sy].astype(np.int64)  # type: ignore[index]
            )
    out[8 * CHANNEL_DIM:9 * CHANNEL_DIM] = pawn_w.astype(np.int32)
    out[9 * CHANNEL_DIM:10 * CHANNEL_DIM] = pawn_y.astype(np.int32)

    # ── Channel 10 (FD_DIAG) ──
    DIAG_DEV_INT16 = qt['DIAG_DEV_INT16']  # type: ignore[assignment]
    diag_ch = np.zeros(CHANNEL_DIM, dtype=np.int64)
    for k, pval in sorted_items:
        row = _DIAG_DEV_ROW[_piece_char(pval)]
        coef = int(sig_int32[int(k)])
        if coef == 0:
            continue
        diag_ch += coef * DIAG_DEV_INT16[row].astype(np.int64)  # type: ignore[index]
    out[10 * CHANNEL_DIM:11 * CHANNEL_DIM] = diag_ch.astype(np.int32)

    return out


def encode_4d_pure_phase_to_float(
    pos4: Dict[int, PieceValue],
    *,
    vals: Optional[Dict[str, int]] = None,
) -> np.ndarray:
    """Pure-phase encoder with per-channel dequantization to float64.

    Returns the float64 array that approximates
    ``encode_4d(pos4, vals=PIECE_VALUES_4D)`` — the natural baseline
    for cosine-sim parity tests.

    Returns
    -------
    np.ndarray, shape (45056,), dtype float64
    """
    _ensure_dequant_scales()
    int_out = encode_4d_pure_phase(pos4, vals=vals)
    out = np.empty(ENCODING_DIM_4D, dtype=np.float64)
    for name, start in CHANNELS_4D:
        scale = CHANNEL_DEQUANT_SCALES_4D[name]
        out[start:start + CHANNEL_DIM] = (
            int_out[start:start + CHANNEL_DIM].astype(np.float64) * scale
        )
    return out


__all__ = [
    "encode_4d_pure_phase",
    "encode_4d_pure_phase_to_float",
    "CHANNEL_DEQUANT_SCALES_4D",
    "_VALS_INT_SCALE_4D",
]

"""4D chess-spectral encoder — encode_4d(pos4) -> float32[45056].

Channel layout (11 channels of 4096 modes each, 45 056 total):
    [   0:4096]   A_1 orbit-sum projection            (signal space)
    [4096:8192]   std-4D coord residual x * signal    (signal space)
    [8192:12288]  std-4D coord residual y * signal    (signal space)
    [12288:16384] std-4D coord residual z * signal    (signal space)
    [16384:20480] std-4D coord residual w * signal    (signal space)
    [20480:24576] fiber-sym 1                          (see note)
    [24576:28672] fiber-sym 2                          (see note)
    [28672:32768] fiber-sym 3                          (see note)
    [32768:36864] pawn antisymmetric fiber (W-axis)    (DCT-mode space)
    [36864:40960] pawn antisymmetric fiber (Y-axis)    (DCT-mode space)
    [40960:45056] diagonal deviation (rook shadow)     (DCT-mode space)

The 'signal space' vs 'DCT-mode space' split mirrors the 2D encoder
([encoder.py]) so downstream tools (channel energy plots, F_D sign
analysis) carry over unchanged up to dimension.

v1.1.1 splits the pawn antisymmetric channel into two orthogonal
sub-channels — one per pawn axis — per Oana & Chiru Definition 11
(pawns oriented along Y or W axis, never Z). Each sub-channel lifts
the same 8x8 antisymmetric block through an independent tensor factor
of the 4D DCT basis (W-axis: I(x)I(x)I(x)W_ANTI_DCT; Y-axis:
I(x)Y_ANTI_DCT(x)I(x)I), so the two channels are Frobenius-orthogonal
by construction. See test_pawn_axis_factorization_structural and
tables_4d.y_anti_dct_block.

Fiber-sym (v1.1): the 2D fiber channels use per-square LOCAL_FIBER_3D +
LOCAL_ADJ_ROWS tables (5 x 64 x 3 and 5 x 64 x 64). The 4D analogue
uses a cross-piece SVD fiber basis instead of a per-square local
Laplacian. The cross-piece SVD of off-diag(U^T L_piece U) across the
five pieces is rank 3 in the grid-DCT off-diagonal representation —
knight, bishop (= queen), and king contribute three independent
shared-structure directions; the 4D rook is diagonal in this basis
and contributes nothing, so it is dropped from the SVD input to avoid
a spurious rank-4 direction from round-off.

The per-(piece, square) fiber coordinates live in `tables_4d.
local_fiber_4d()` as a (5, 4096, 3) float32 array. At encode time we
perform the same aggregation as 2D: for each occupied non-pawn square
si with piece value sig[si], read fib_d[piece_idx, si, d] and the
piece's sparse adjacency row, compute gradient = adj_row @ sig, and
accumulate `gradient * fib_d * adj_row` into fiber channel d.

Position input (v1.1.1):
    pos4 : dict mapping sq4(x,y,z,w) linear index -> piece value.
        Non-pawn piece values are a single char following the usual
        convention: upper = white, lower = black, from the set
        {'N','B','R','Q','K','n','b','r','q','k'}.
        Pawn values are tuples (color_char, axis_char) where
        color_char is 'P' or 'p' and axis_char is 'y' or 'w'
        (Oana & Chiru Definition 11 forbids z-axis pawns).
        Example: {sq4(0,0,0,1): ('P', 'w'), sq4(0,1,0,0): ('p', 'y')}.
        Legacy single-char pawn values ('P' / 'p') are accepted as
        a shortcut for W-axis (matches v1.0 behavior) and emit a
        DeprecationWarning once per call site.
"""
from __future__ import annotations

import warnings
from typing import Dict, Optional, Tuple, Union

import numpy as np
from scipy.sparse import csr_matrix

# Import paths: this module lives in chess_spectral/ and uses
# chess_spectral.tables_4d.
from chess_spectral import tables_4d as t4


ENCODING_DIM_4D = 45056
N_CHANNELS_4D = 11
CHANNEL_DIM = t4.N_SQUARES     # 4096


# v1.1.1 position value: either a non-pawn single-char or a pawn
# (color, axis) tuple. Str pawn values are accepted as a legacy
# shortcut for ('P'/'p', 'w').
PieceValue = Union[str, Tuple[str, str]]


# Piece values — simple nominal scale. Mirrors VALS from the 2D
# encoder's 'classical' table; the spectral-normalized variant can
# come later in v1.1.
PIECE_VALUES_4D: Dict[str, float] = {
    'P':  1.0, 'N':  3.0, 'B':  3.25, 'R':  5.0, 'Q':  9.0, 'K': 12.0,
    'p': -1.0, 'n': -3.0, 'b': -3.25, 'r': -5.0, 'q': -9.0, 'k': -12.0,
}


# Row index into diag_dev_4d's (6, 4096) table. Matches the
# construction order there: pawn_sym=0, knight=1, bishop=2, rook=3,
# queen=4, king=5.
_DIAG_DEV_ROW: Dict[str, int] = {
    'P': 0, 'p': 0,
    'N': 1, 'n': 1,
    'B': 2, 'b': 2,
    'R': 3, 'r': 3,
    'Q': 4, 'q': 4,
    'K': 5, 'k': 5,
}


# Row index into local_fiber_4d's (5, 4096, 3) table. Matches the
# _PIECE_TARGETS_4D order in tables_4d. Pawns are skipped (directed,
# handled in the antisym channel).
_FIBER_IDX_4D: Dict[str, int] = {
    'N': 0, 'B': 1, 'R': 2, 'Q': 3, 'K': 4,
}


# ---- Channel name index (for channel_energies_4d, debugging) ----

CHANNELS_4D = [
    ("A1",          0),
    ("STD4_X",      1 * CHANNEL_DIM),
    ("STD4_Y",      2 * CHANNEL_DIM),
    ("STD4_Z",      3 * CHANNEL_DIM),
    ("STD4_W",      4 * CHANNEL_DIM),
    ("FIB_SYM_1",   5 * CHANNEL_DIM),
    ("FIB_SYM_2",   6 * CHANNEL_DIM),
    ("FIB_SYM_3",   7 * CHANNEL_DIM),
    ("FA_PAWN_W",   8 * CHANNEL_DIM),
    ("FA_PAWN_Y",   9 * CHANNEL_DIM),
    ("FD_DIAG",    10 * CHANNEL_DIM),
]


# ---- Position schema helpers (v1.1.1) -------------------------------

def _is_pawn(value: PieceValue) -> bool:
    """True if value is a pawn (str 'P'/'p' or tuple ('P'/'p', axis))."""
    if isinstance(value, tuple):
        return len(value) == 2 and value[0] in ('P', 'p')
    return value in ('P', 'p')


def _piece_char(value: PieceValue) -> str:
    """Return the single-char piece identifier for lookup into
    PIECE_VALUES_4D / _DIAG_DEV_ROW / _FIBER_IDX_4D. Pawns stored as
    (color, axis) tuples collapse to their color char."""
    if isinstance(value, tuple):
        return value[0]
    return value


def _pawn_axis(value: PieceValue) -> str:
    """Return 'y' or 'w' for a pawn value. Legacy single-char pawn
    emits a DeprecationWarning and defaults to 'w' (matches v1.0
    W-only behavior). Raises on non-pawn values."""
    if isinstance(value, tuple):
        color, axis = value
        if color not in ('P', 'p'):
            raise ValueError(
                f"_pawn_axis called on non-pawn value {value!r}"
            )
        if axis not in ('y', 'w'):
            raise ValueError(
                f"pawn axis must be 'y' or 'w', got {axis!r} "
                f"(Oana & Chiru Definition 11 forbids z-axis pawns)"
            )
        return axis
    if value not in ('P', 'p'):
        raise ValueError(f"_pawn_axis called on non-pawn value {value!r}")
    warnings.warn(
        "legacy single-char pawn schema ('P'/'p') defaults to W axis; "
        "pass a tuple ('P', 'w') or ('P', 'y') to specify the pawn "
        "axis explicitly (Oana & Chiru Definition 11)",
        DeprecationWarning, stacklevel=3,
    )
    return 'w'


# ---- Lazy precomputed tables (module-level cache) -------------------

_CACHE: Dict[str, object] = {}


def _committed_tables_4d_path():
    """Path to the committed-with-the-package 4D table data, written
    by ``codegen/emit_tables_4d.py`` in lockstep with
    ``src/cs_tables_data_4d.c``. When present, it's the authoritative
    source: same values as C, eliminates cross-platform skew. See
    chess_spectral.tables._committed_tables_path for the 2D analog."""
    from pathlib import Path
    return Path(__file__).parent / "_committed_tables_4d.npz"


def _try_load_committed_4d() -> bool:
    """Populate _CACHE from the committed npz if present. Returns
    True on success, False if the file is missing or malformed (caller
    falls through to runtime computation)."""
    path = _committed_tables_4d_path()
    if not path.exists():
        return False
    try:
        from scipy.sparse import csr_matrix
        with np.load(path, allow_pickle=False) as data:
            _CACHE['coord_resid'] = data['coord_resid']
            _CACHE['W_ANTI_DCT']  = data['W_ANTI_DCT']
            _CACHE['Y_ANTI_DCT']  = data['Y_ANTI_DCT']
            _CACHE['DIAG_DEV']    = data['DIAG_DEV']
            _CACHE['FIBER_LOCAL'] = data['FIBER_LOCAL']
            _CACHE['P_A1'] = csr_matrix(
                (data['P_A1_data'], data['P_A1_indices'],
                 data['P_A1_indptr']),
                shape=tuple(data['P_A1_shape']),
            )
            piece_chars = [c.item() for c in data['PIECE_ADJ_chars']]
            _CACHE['PIECE_ADJ'] = [
                csr_matrix(
                    (data[f'PIECE_ADJ_{ch}_data'],
                     data[f'PIECE_ADJ_{ch}_indices'],
                     data[f'PIECE_ADJ_{ch}_indptr']),
                    shape=tuple(data[f'PIECE_ADJ_{ch}_shape']),
                )
                for ch in piece_chars
            ]
        return True
    except (OSError, KeyError, ValueError):
        # Malformed npz — clear partial state and let caller recompute.
        _CACHE.clear()
        return False


def _load_tables() -> Dict[str, object]:
    """Build & cache the expensive static tables the encoder needs.

    Search order:
      1. Committed npz at ``_committed_tables_4d.npz`` (preferred — same
         values as the C encoder; cross-platform deterministic).
      2. Runtime computation via tables_4d primitives (fallback when
         committed npz is absent — uses local scipy/LAPACK and may
         produce different basis choices than C on non-codegen
         platforms).

    Cache contents:
      P_A1           sparse (4096,4096) orbit projector
      coord_resid    (4, 4096) std-4D coord residual masks
      W_ANTI_DCT     (8, 8) factored pawn antisymmetric fiber (see
                     tables_4d.w_anti_dct_block for the algebraic
                     derivation; equivalent to the 8x8 w-block of the
                     dense 4096x4096 PAWN_ANTI_FIB)
      Y_ANTI_DCT     (8, 8) Y-axis equivalent
      DIAG_DEV       (6, 4096) per-piece mode-space diag deviations
      FIBER_LOCAL    (5, 4096, 3) per-(piece, square) fiber coordinates
      PIECE_ADJ      list of 5 CSR sparse adjacencies (N, B, R, Q, K)

    Subsequent calls return the cached dict."""
    if _CACHE:
        return _CACHE

    if _try_load_committed_4d():
        return _CACHE

    # 1. A_1 orbit projector (sparse)
    _CACHE['P_A1'] = t4.b4_a1_orbit_projector()

    # 2. std-4D coord residuals: I_4 - (1/4) J_4 applied to centered coords
    coord_resid = np.zeros((t4.N_DIMS, t4.N_SQUARES), dtype=np.float64)
    for s in range(t4.N_SQUARES):
        c = np.array(t4.rc4(s), dtype=np.float64) - 3.5  # centered on {-3.5..+3.5}
        mean_c = c.mean()                                # always 0 for this lattice
        for a in range(t4.N_DIMS):
            coord_resid[a, s] = c[a] - mean_c
    _CACHE['coord_resid'] = coord_resid

    # 3. Pawn antisymmetric fibers (v1.1.1): factored 8x8 blocks, one
    #    per pawn axis. W-axis lifts to I(x)I(x)I(x)W_ANTI_DCT, Y-axis
    #    lifts to I(x)Y_ANTI_DCT(x)I(x)I. The 8x8 matrices are
    #    numerically identical (same antisymmetric generator, same U_P8)
    #    — the channel separation comes from WHICH tensor factor they
    #    inhabit, which in turn selects which 4096-entry scatter
    #    pattern the encoder applies per pawn (contiguous stride-1 on
    #    W, stride-64 on Y). The C encoder mirrors the factored form;
    #    1e-10 parity is clean because off-axis modes are never
    #    touched (vs ~1e-8 FP noise in the 128 MB dense form).
    _CACHE['W_ANTI_DCT'] = t4.w_anti_dct_block()
    _CACHE['Y_ANTI_DCT'] = t4.y_anti_dct_block()

    # 4. diag_dev table (6, 4096). 5. Local fiber coords (5, 4096, 3).
    #    Both need the U tensor; build once and drop it after.
    U = t4.build_u_tensor_4d()
    _CACHE['DIAG_DEV'] = t4.diag_dev_4d(U=U)
    _CACHE['FIBER_LOCAL'] = t4.local_fiber_4d(U=U)
    _CACHE['PIECE_ADJ'] = t4.piece_adjacencies_4d()
    return _CACHE


# ---- Signal construction --------------------------------------------

def board_signal_4d(pos4: Dict[int, PieceValue],
                    vals: Optional[Dict[str, float]] = None,
                    ) -> np.ndarray:
    """Scalar 4096-vector of signed piece values per square. Missing
    squares are 0.

    Accepts int or str keys (NDJSON convenience) and either single-char
    or ('color', 'axis') tuple values (v1.1.1 pawn axis schema; see
    module docstring). The pawn axis has no effect here — only the
    color char drives the signal sign — but tuple values are accepted
    to keep board_signal_4d and encode_4d input-compatible.
    """
    if vals is None:
        vals = PIECE_VALUES_4D
    sig = np.zeros(t4.N_SQUARES, dtype=np.float64)
    for k, pval in pos4.items():
        s = int(k)
        if not (0 <= s < t4.N_SQUARES):
            raise ValueError(f"square index {s} out of range [0, 4096)")
        pchar = _piece_char(pval)
        if pchar not in vals:
            raise ValueError(f"unknown piece char {pchar!r}")
        if isinstance(pval, tuple) and not _is_pawn(pval):
            raise ValueError(
                f"tuple value {pval!r} is only valid for pawns "
                f"(color in 'P'/'p'), not {pchar!r}"
            )
        sig[s] = vals[pchar]
    return sig


# ---- Main encoder ---------------------------------------------------

def encode_4d(pos4: Dict[int, PieceValue],
              vals: Optional[Dict[str, float]] = None,
              *,
              sheets=None,
              ) -> np.ndarray:
    """Encode a 4D position to a 45056-dim float32 vector.

    pos4 : {int square index -> piece value}. Non-pawn piece values
        are single chars; pawn values are ('color', 'axis') tuples
        where axis is 'y' or 'w' (v1.1.1 Oana & Chiru schema; legacy
        single-char pawn values accepted with DeprecationWarning).
    sheets : SheetState or None, optional (1.9.0+)
        If supplied, append the 11-dim non-Markovian aux block (see
        :mod:`chess_spectral.sheets`) to the 45056-dim base, producing
        a 45067-dim output. Castling and EP slots are zero by
        construction (the Oana-Chiru ruleset has neither — see
        ``spatial_4d/board.py``); the half-move clock, side-to-move,
        and repetition slots are populated. The aux block is cast to
        float32 to match the base encoder's dtype. Default ``None``
        keeps the legacy 45056-dim output bit-for-bit compatible with
        pre-1.9.0 versions and with the C ``spectral_4d`` binary.

    Returns
    -------
    np.ndarray, dtype float32
        Shape ``(45056,)`` if ``sheets`` is None (default),
        else ``(45067,)``.
    """
    tables = _load_tables()
    sig = board_signal_4d(pos4, vals=vals)

    out = np.zeros(ENCODING_DIM_4D, dtype=np.float32)

    # Channel 0: A_1 orbit projection (signal space)
    P_A1 = tables['P_A1']  # type: ignore[assignment]
    out[0:CHANNEL_DIM] = (P_A1 @ sig).astype(np.float32)

    # Channels 1-4: std-4D coord residuals times signal (signal space)
    coord_resid = tables['coord_resid']  # type: ignore[assignment]
    for a in range(t4.N_DIMS):
        start = (1 + a) * CHANNEL_DIM
        out[start:start + CHANNEL_DIM] = (
            coord_resid[a] * sig  # type: ignore[index]
        ).astype(np.float32)

    # Channels 5-7: fiber-sym (v1.1 rank-3 cross-piece SVD basis).
    #   For each direction d in {0,1,2} and each occupied non-pawn
    #   square k with piece pchar:
    #     gradient_d(k) = sig[adj(k)].sum()                (neighbor mass)
    #     fib_d         = FIBER_LOCAL[piece_idx, k, d]
    #     fc[adj(k)]   += gradient_d(k) * fib_d
    #   This mirrors the 2D encoder semantics
    #   (see [encoder.py:156-168]).
    FIBER_LOCAL = tables['FIBER_LOCAL']  # type: ignore[assignment]
    PIECE_ADJ = tables['PIECE_ADJ']      # type: ignore[assignment]
    # Sorted occupied-square iteration. Load-bearing for C parity: the C
    # port accumulates in ascending square order, and float64 summation
    # is not associative. See ROADMAP.md and src/cs_fiber_sym_4d.c for
    # the matching ordering on the C side.
    sorted_items = sorted(pos4.items(), key=lambda kv: int(kv[0]))
    for d in range(3):
        fc = np.zeros(CHANNEL_DIM, dtype=np.float64)
        for k, pval in sorted_items:
            pkey = _piece_char(pval).upper()
            if pkey not in _FIBER_IDX_4D:
                continue  # skip pawn
            pidx = _FIBER_IDX_4D[pkey]
            s = int(k)
            row = PIECE_ADJ[pidx].getrow(s)  # type: ignore[index]
            cols = row.indices
            if cols.size == 0:
                continue
            gradient = float(sig[cols].sum())
            fib_d = float(FIBER_LOCAL[pidx, s, d])  # type: ignore[index]
            fc[cols] += gradient * fib_d
        start = (5 + d) * CHANNEL_DIM
        out[start:start + CHANNEL_DIM] = fc.astype(np.float32)

    # Channels 8-9: pawn antisymmetric fiber, split per axis
    # (v1.1.1). Each pawn routes to exactly one axis channel — 'w' or
    # 'y' per Oana & Chiru Definition 11 — by scattering its 8x8 DCT
    # block row into 8 modes along the relevant axis.
    #
    #   W-axis, pawn at (sx, sy, sz, sw): DCT-basis matrix is
    #       I (x) I (x) I (x) W_ANTI_DCT, so the channel contribution
    #       is W_ANTI_DCT[sw, :] scattered into modes (sx, sy, sz, *)
    #       — 8 contiguous stride-1 writes starting at (sx<<9)|(sy<<6)|(sz<<3).
    #   Y-axis, pawn at (sx, sy, sz, sw): DCT-basis matrix is
    #       I (x) Y_ANTI_DCT (x) I (x) I, so the channel contribution
    #       is Y_ANTI_DCT[sy, :] scattered into modes (sx, *, sz, sw)
    #       — 8 stride-64 writes at indices (sx<<9)|(j<<6)|(sz<<3)|sw for
    #       j in 0..7.
    #
    # Orthogonality of the two sub-channels is a structural
    # consequence of the independent tensor factors (see
    # test_pawn_axis_factorization_structural); the C port mirrors
    # this factored form exactly for a clean 1e-10 parity target.
    W_ANTI_DCT = tables['W_ANTI_DCT']  # type: ignore[assignment]
    Y_ANTI_DCT = tables['Y_ANTI_DCT']  # type: ignore[assignment]
    pawn_ch_w = np.zeros(CHANNEL_DIM, dtype=np.float64)
    pawn_ch_y = np.zeros(CHANNEL_DIM, dtype=np.float64)
    for k, pval in sorted_items:
        if not _is_pawn(pval):
            continue
        color = _piece_char(pval)
        sign = 1.0 if color == 'P' else -1.0
        axis = _pawn_axis(pval)
        s = int(k)
        sx = (s >> 9) & 7
        sy = (s >> 6) & 7
        sz = (s >> 3) & 7
        sw = s & 7
        if axis == 'w':
            base = (sx << 9) | (sy << 6) | (sz << 3)
            pawn_ch_w[base:base + 8] += sign * W_ANTI_DCT[sw]  # type: ignore[index]
        else:  # axis == 'y' — validated upstream by _pawn_axis
            base = (sx << 9) | (sz << 3) | sw
            # Stride-64 indices across the j-axis of (sx, j, sz, sw).
            idx = base | (np.arange(8) << 6)
            pawn_ch_y[idx] += sign * Y_ANTI_DCT[sy]  # type: ignore[index]
    out[8 * CHANNEL_DIM:9 * CHANNEL_DIM] = pawn_ch_w.astype(np.float32)
    out[9 * CHANNEL_DIM:10 * CHANNEL_DIM] = pawn_ch_y.astype(np.float32)

    # Channel 10: diagonal deviation (rook shadow), DCT-mode space.
    # (Shifted from slot 9 in v1.0 to slot 10 in v1.1.1 after the
    # pawn antisym split.)
    #   out[k] = sum over occupied squares s: sig[s] * DIAG_DEV[piece_row, k]
    # Load-bearing for C parity: float64 vector accumulation is non-
    # associative, so the C port (which iterates pos->sq[s] in ascending
    # s order) and Python must agree on iteration order. Use sorted_items
    # here, same reason as channels 5-7.
    DIAG_DEV = tables['DIAG_DEV']  # type: ignore[assignment]
    diag_ch = np.zeros(CHANNEL_DIM, dtype=np.float64)
    for k, pval in sorted_items:
        row = _DIAG_DEV_ROW[_piece_char(pval)]
        diag_ch += sig[int(k)] * DIAG_DEV[row]  # type: ignore[index]
    out[10 * CHANNEL_DIM:11 * CHANNEL_DIM] = diag_ch.astype(np.float32)

    if sheets is not None:
        # Concat the 11-dim aux block (cast to float32 to match base
        # dtype). See :mod:`chess_spectral.sheets` for layout details.
        # 4D-OC has no castling and no EP per the ruleset, so those
        # slots will be zero in any SheetState lifted via
        # SheetState.from_game_state_4d() — but we don't enforce that
        # here; if a caller hand-constructs a SheetState with
        # castling/EP slots set, we serialize them faithfully.
        from .sheets import SHEET_AUX_DIM, encode_aux_block
        aux = encode_aux_block(sheets).astype(np.float32)
        out_with_aux = np.empty(
            ENCODING_DIM_4D + SHEET_AUX_DIM, dtype=np.float32)
        out_with_aux[:ENCODING_DIM_4D] = out
        out_with_aux[ENCODING_DIM_4D:] = aux
        return out_with_aux

    return out


def channel_energies_4d(enc: np.ndarray) -> Dict[str, float]:
    """||ch||^2 per channel, keyed by name. Mirrors 2D's channel_energies."""
    return {name: float(np.dot(enc[start:start + CHANNEL_DIM],
                                enc[start:start + CHANNEL_DIM]))
            for name, start in CHANNELS_4D}

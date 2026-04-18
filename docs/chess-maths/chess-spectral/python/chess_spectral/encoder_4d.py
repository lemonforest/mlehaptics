"""4D chess-spectral encoder — encode_4d(pos4) -> float32[40960].

Channel layout (10 channels of 4096 modes each, 40 960 total):
    [   0:4096]   A_1 orbit-sum projection            (signal space)
    [4096:8192]   std-4D coord residual x * signal    (signal space)
    [8192:12288]  std-4D coord residual y * signal    (signal space)
    [12288:16384] std-4D coord residual z * signal    (signal space)
    [16384:20480] std-4D coord residual w * signal    (signal space)
    [20480:24576] fiber-sym 1                          (see note)
    [24576:28672] fiber-sym 2                          (see note)
    [28672:32768] fiber-sym 3                          (see note)
    [32768:36864] pawn antisymmetric fiber             (DCT-mode space)
    [36864:40960] diagonal deviation (rook shadow)     (DCT-mode space)

The 'signal space' vs 'DCT-mode space' split mirrors the 2D encoder
([encoder.py]) so downstream tools (channel energy plots, F_D sign
analysis) carry over unchanged up to dimension.

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

Position input:
    pos4 : dict mapping sq4(x,y,z,w) linear index -> piece char
           piece chars follow the usual convention: upper = white,
           lower = black. {'P','N','B','R','Q','K','p','n','b','r',
           'q','k'}.
"""
from __future__ import annotations

from typing import Dict, Optional

import numpy as np
from scipy.sparse import csr_matrix

# Import paths: this module lives in chess_spectral/ and uses
# chess_spectral.tables_4d.
from chess_spectral import tables_4d as t4


ENCODING_DIM_4D = 40960
N_CHANNELS_4D = 10
CHANNEL_DIM = t4.N_SQUARES     # 4096


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
    ("A1",         0),
    ("STD4_X",     1 * CHANNEL_DIM),
    ("STD4_Y",     2 * CHANNEL_DIM),
    ("STD4_Z",     3 * CHANNEL_DIM),
    ("STD4_W",     4 * CHANNEL_DIM),
    ("FIB_SYM_1",  5 * CHANNEL_DIM),
    ("FIB_SYM_2",  6 * CHANNEL_DIM),
    ("FIB_SYM_3",  7 * CHANNEL_DIM),
    ("FA_PAWN",    8 * CHANNEL_DIM),
    ("FD_DIAG",    9 * CHANNEL_DIM),
]


# ---- Lazy precomputed tables (module-level cache) -------------------

_CACHE: Dict[str, object] = {}


def _load_tables() -> Dict[str, object]:
    """Build & cache the expensive static tables the encoder needs.

    P_A1           sparse (4096,4096) orbit projector
    coord_resid    (4, 4096) std-4D coord residual masks
    W_ANTI_DCT     (8, 8) factored pawn antisymmetric fiber (see
                   tables_4d.w_anti_dct_block for the algebraic
                   derivation; equivalent to the 8x8 w-block of the
                   dense 4096x4096 PAWN_ANTI_FIB)
    DIAG_DEV       (6, 4096) per-piece mode-space diag deviations
    FIBER_LOCAL    (5, 4096, 3) per-(piece, square) fiber coordinates
    PIECE_ADJ      list of 5 CSR sparse adjacencies (knight, bishop,
                   rook, queen, king)

    Subsequent calls return the cached dict."""
    if _CACHE:
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

    # 3. Pawn antisymmetric fiber (factored 8x8 block; the full DCT-basis
    #    matrix is I (x) I (x) I (x) W_ANTI_DCT). The C encoder mirrors
    #    this factored form exactly; keeping the Python reference in the
    #    same form means the 1e-10 parity target is clean instead of
    #    being polluted by 1e-8 off-w FP noise from the 128 MB dense
    #    form.
    _CACHE['W_ANTI_DCT'] = t4.w_anti_dct_block()

    # 4. diag_dev table (6, 4096). 5. Local fiber coords (5, 4096, 3).
    #    Both need the U tensor; build once and drop it after.
    U = t4.build_u_tensor_4d()
    _CACHE['DIAG_DEV'] = t4.diag_dev_4d(U=U)
    _CACHE['FIBER_LOCAL'] = t4.local_fiber_4d(U=U)
    _CACHE['PIECE_ADJ'] = t4.piece_adjacencies_4d()
    return _CACHE


# ---- Signal construction --------------------------------------------

def board_signal_4d(pos4: Dict[int, str],
                    vals: Optional[Dict[str, float]] = None,
                    ) -> np.ndarray:
    """Scalar 4096-vector of signed piece values per square. Missing
    squares are 0. Accepts int or str keys (NDJSON convenience)."""
    if vals is None:
        vals = PIECE_VALUES_4D
    sig = np.zeros(t4.N_SQUARES, dtype=np.float64)
    for k, pchar in pos4.items():
        s = int(k)
        if not (0 <= s < t4.N_SQUARES):
            raise ValueError(f"square index {s} out of range [0, 4096)")
        if pchar not in vals:
            raise ValueError(f"unknown piece char {pchar!r}")
        sig[s] = vals[pchar]
    return sig


# ---- Main encoder ---------------------------------------------------

def encode_4d(pos4: Dict[int, str],
              vals: Optional[Dict[str, float]] = None,
              ) -> np.ndarray:
    """Encode a 4D position to a 40960-dim float32 vector.

    pos4 : {int square index -> piece char}
    Returns float32 array of shape (40960,).
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
    # is not associative. See plan: "when-we-need-to-spicy-seahorse" P0.
    sorted_items = sorted(pos4.items(), key=lambda kv: int(kv[0]))
    for d in range(3):
        fc = np.zeros(CHANNEL_DIM, dtype=np.float64)
        for k, pchar in sorted_items:
            pkey = pchar.upper()
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

    # Channel 8: pawn antisymmetric fiber (DCT-mode space).
    #   The full DCT-basis matrix is I (x) I (x) I (x) W_ANTI_DCT, so for
    #   each pawn at square s = (sx, sy, sz, sw):
    #       row[s][t] = W_ANTI_DCT[sw, tw] if (tx,ty,tz) == (sx,sy,sz) else 0
    #   => pawn contribution writes into the 8 modes sharing (sx,sy,sz)
    #   along w. 8 float ops per pawn vs 4096 for the dense form, and —
    #   more importantly — exactly zero for the off-w modes that the
    #   dense form carries at < 1e-8 FP noise. Parity target for the C
    #   port is this exact form.
    W_ANTI_DCT = tables['W_ANTI_DCT']  # type: ignore[assignment]
    pawn_ch = np.zeros(CHANNEL_DIM, dtype=np.float64)
    for k, pchar in sorted_items:
        if pchar.upper() != 'P':
            continue
        sign = 1.0 if pchar == 'P' else -1.0
        s = int(k)
        sx = (s >> 9) & 7
        sy = (s >> 6) & 7
        sz = (s >> 3) & 7
        sw = s & 7
        base = (sx << 9) | (sy << 6) | (sz << 3)
        pawn_ch[base:base + 8] += sign * W_ANTI_DCT[sw]  # type: ignore[index]
    out[8 * CHANNEL_DIM:9 * CHANNEL_DIM] = pawn_ch.astype(np.float32)

    # Channel 9: diagonal deviation (rook shadow), DCT-mode space
    #   out[k] = sum over occupied squares s: sig[s] * DIAG_DEV[piece_row, k]
    DIAG_DEV = tables['DIAG_DEV']  # type: ignore[assignment]
    diag_ch = np.zeros(CHANNEL_DIM, dtype=np.float64)
    for k, pchar in pos4.items():
        row = _DIAG_DEV_ROW[pchar]
        diag_ch += sig[int(k)] * DIAG_DEV[row]  # type: ignore[index]
    out[9 * CHANNEL_DIM:10 * CHANNEL_DIM] = diag_ch.astype(np.float32)

    return out


def channel_energies_4d(enc: np.ndarray) -> Dict[str, float]:
    """||ch||^2 per channel, keyed by name. Mirrors 2D's channel_energies."""
    return {name: float(np.dot(enc[start:start + CHANNEL_DIM],
                                enc[start:start + CHANNEL_DIM]))
            for name, start in CHANNELS_4D}

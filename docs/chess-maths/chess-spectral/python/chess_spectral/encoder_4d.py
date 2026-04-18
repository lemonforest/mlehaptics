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

Fiber-sym note: the 2D fiber channels use per-square LOCAL_FIBER_3D +
LOCAL_ADJ_ROWS tables (5 x 64 x 3 and 5 x 64 x 64 respectively). The
4D analogue would be 5 x 4096 x 3 and 5 x 4096 x 4096 = 2.6 GB, which
we won't precompute in v1. For v1 the fiber-sym channels are LEFT AS
ZEROS; the encoder structure is otherwise complete and the Phase 5
round-trip gate is unaffected. Filling these in is a Phase 6 / v1.1
task (plan: global SVD fiber basis applied per-piece, not per-square).

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
    PAWN_ANTI_FIB  (4096, 4096) dense, U^T A_anti U; 128 MB
    DIAG_DEV       (6, 4096) per-piece mode-space diag deviations

    First call is expensive (dense 4D DCT transform). Subsequent calls
    return the cached dict."""
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

    # 3. Pawn antisymmetric fiber in DCT-mode basis (4096, 4096 dense)
    #    and 4. diag_dev table (6, 4096). Both need the U tensor; build
    #    once and drop it after.
    U = t4.build_u_tensor_4d()
    A_anti = t4.pawn_anti_4d()
    _CACHE['PAWN_ANTI_FIB'] = (U.T @ A_anti @ U).astype(np.float64)
    _CACHE['DIAG_DEV'] = t4.diag_dev_4d(U=U)
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

    # Channels 5-7: fiber-sym (v1 stub -- left as zeros; see module docstring)
    # out[5*CHANNEL_DIM:8*CHANNEL_DIM] is already zero.

    # Channel 8: pawn antisymmetric fiber (DCT-mode space)
    #   out = sum over pawn squares s: sign * PAWN_ANTI_FIB[s, :]
    PAWN_ANTI_FIB = tables['PAWN_ANTI_FIB']  # type: ignore[assignment]
    pawn_ch = np.zeros(CHANNEL_DIM, dtype=np.float64)
    for k, pchar in pos4.items():
        if pchar.upper() != 'P':
            continue
        sign = 1.0 if pchar == 'P' else -1.0
        pawn_ch += sign * PAWN_ANTI_FIB[int(k)]  # type: ignore[index]
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

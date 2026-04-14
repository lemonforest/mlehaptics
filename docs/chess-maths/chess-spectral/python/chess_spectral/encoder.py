"""
encode_640 — reference Python implementation of the 640-dim spectral
chess encoder that the C17 port mirrors.

Channel layout (10 channels × 64 dims = 640):
    A1, A2, B1, B2, E         — D4 irreps (via Serre's character formula)
    F1, F2, F3                — symmetric fiber (per-piece local Laplacians
                                 projected onto a 3D fiber basis)
    FA                         — antisymmetric fiber / pawn directional flow.
                                 Built from A_anti = (A_white - A_white.T)/2,
                                 in the grid eigenbasis.
    FD                         — diagonal deviation / rook's shadow.
                                 diag(EVECS.T @ L_piece @ EVECS) - EVALS_GRID,
                                 weighted by signed piece value.

All precomputed tables (eigenbasis, fiber basis, local fibers, PAWN_ANTI_FIBER,
DIAG_DEV) live in chess_spectral.tables — which caches them to disk on first
import. This module consumes them; the math derivation is over there.

The 640-dim output matches the C encoder's byte-for-byte for dims 0-511
(identical math on top of the same tables) and matches within float32
precision for dims 512-639 (where the C side stores the values as f32).

Position format (`pos`):
    dict mapping square index (0..63, row-major from a8=0) to piece
    character ("P","N","B","R","Q","K" white, lowercase black).

    Convenience: int keys can also be passed as str — NDJSON payloads
    use `{"0":"R", ...}`. normalize_pos() handles both.
"""
from __future__ import annotations

# Guard against direct-script execution (`python encoder.py`). The
# relative import below will fail because there's no parent package in
# that context, and the user will see a cryptic ImportError rather than
# the usage message. Detect + print help + exit cleanly.
if __name__ == "__main__" and __package__ in (None, ""):
    import sys
    print(
        "chess_spectral.encoder is a library module, not a CLI.\n"
        "\n"
        "Command-line use — run the sibling driver:\n"
        "    python spectral_py.py csv        game.spectralz -o game.csv\n"
        "    python spectral_py.py encode     -i game.ndjson -o game.spectral -z\n"
        "    python spectral_py.py encode-fen --fen \"...\" -o single.spectral\n"
        "    python spectral_py.py version\n"
        "\n"
        "Programmatic use:\n"
        "    >>> from chess_spectral import encode_640, channel_energies\n"
        "    >>> from pgn_bridge import fen_to_pos\n"
        "    >>> enc = encode_640(fen_to_pos(\"...\"))   # shape (640,)\n",
        file=sys.stderr,
    )
    sys.exit(2)

import numpy as np

from .tables import (
    BOARD_DIM,
    SHORT_PFNS, SPECTRAL_VALS, VALS,
    LOCAL_FIBER_3D, LOCAL_ADJ_ROWS,
    PAWN_ANTI_FIBER, DIAG_DEV,
    board_signal, project_irrep,
)

ENCODING_DIM = 640
N_CHANNELS   = 10

# Channel name → (start_dim) and ordered list for iteration.
CHANNELS = [
    ("A1",   0), ("A2",  64), ("B1", 128), ("B2", 192), ("E",  256),
    ("F1", 320), ("F2", 384), ("F3", 448), ("FA", 512), ("FD", 576),
]

# Piece-char → DIAG_DEV row index (FD channel).
_PIECE_IDX = {'P': 0, 'N': 1, 'B': 2, 'R': 3, 'Q': 4, 'K': 5}

# Piece-char → LOCAL_FIBER_3D / LOCAL_ADJ_ROWS first-axis index.
# Matches tables.py construction order ['N', 'B', 'R', 'Q', 'K'].
_FIBER_IDX = {'N': 0, 'B': 1, 'R': 2, 'Q': 3, 'K': 4}


# ─── Position normalization ─────────────────────────────────────────────

def normalize_pos(pos) -> dict[int, str]:
    """Accept either int-keyed dict (native) or str-keyed dict (NDJSON).
    Returns a fresh int-keyed dict."""
    if not pos:
        return {}
    first = next(iter(pos))
    if isinstance(first, int):
        return dict(pos)
    return {int(k): v for k, v in pos.items()}


# ─── The encoder ────────────────────────────────────────────────────────

def _fiber_antisymmetric(pos: dict[int, str]) -> np.ndarray:
    """Channel FA (dims 512-575). Only pawns contribute.

        out[k] = Σ_{pawn at s} sign(color) · val_P · PAWN_ANTI_FIBER[s, k]

    PAWN_ANTI_FIBER is already in the grid eigenbasis, so there's no
    runtime eigenvector multiply — just a weighted sum of rows.
    """
    out = np.zeros(BOARD_DIM)
    val_P = SPECTRAL_VALS['P']
    for s, pchar in pos.items():
        if pchar.upper() != 'P':
            continue
        w = val_P if pchar == 'P' else -val_P
        out += w * PAWN_ANTI_FIBER[s]
    return out


def _fiber_diagonal(pos: dict[int, str], sig: np.ndarray) -> np.ndarray:
    """Channel FD (dims 576-639). Every occupied square contributes,
    weighted by its signed piece value (already encoded in `sig`):

        out[k] = Σ_{occupied s} sig[s] · DIAG_DEV[piece_type(s), k]
    """
    out = np.zeros(BOARD_DIM)
    for s, pchar in pos.items():
        t = _PIECE_IDX[pchar.upper()]
        out += sig[s] * DIAG_DEV[t]
    return out


def encode_640(pos, *, vals=None) -> np.ndarray:
    """Encode a position to a 640-dim spectral vector.

    Parameters
    ----------
    pos : dict[int|str, str]
        Square-index → piece-char. See module docstring.
    vals : dict[str, float] or None
        Piece-value table. Defaults to SPECTRAL_VALS (mean-degree
        normalization), matching the C encoder. Pass VALS for the
        traditional {P=1, Q=9, K=100} heuristic.

    Returns
    -------
    np.ndarray, shape (640,), dtype float64
    """
    pos = normalize_pos(pos)
    if vals is None:
        vals = SPECTRAL_VALS

    sig = board_signal(pos, vals=vals)

    out = np.empty(ENCODING_DIM, dtype=np.float64)

    # Channels 0-4: D4 irreps
    for i, name in enumerate(['A1', 'A2', 'B1', 'B2', 'E']):
        out[i * BOARD_DIM:(i + 1) * BOARD_DIM] = project_irrep(sig, name)

    # Channels 5-7: symmetric fiber. Non-pawn pieces only.
    for d in range(3):
        fc = np.zeros(BOARD_DIM)
        for si, pchar in pos.items():
            pkey = pchar.upper()
            if pkey not in _FIBER_IDX:
                continue  # pawn: no symmetric Laplacian used here
            pidx    = _FIBER_IDX[pkey]
            fib_d   = LOCAL_FIBER_3D[pidx, si, d]
            adj_row = LOCAL_ADJ_ROWS[pidx, si]
            gradient = float(adj_row @ sig)
            fc += gradient * fib_d * adj_row
        out[320 + d * BOARD_DIM:320 + (d + 1) * BOARD_DIM] = fc

    # Channel 8: antisymmetric pawn fiber
    out[512:576] = _fiber_antisymmetric(pos)

    # Channel 9: diagonal deviation
    out[576:640] = _fiber_diagonal(pos, sig)

    return out


def channel_energies(enc: np.ndarray) -> dict[str, float]:
    """||channel||² for each of the 10 channels, keyed by name."""
    return {name: float(np.dot(enc[start:start + BOARD_DIM],
                                enc[start:start + BOARD_DIM]))
            for name, start in CHANNELS}


# ─── CLI usage hint ─────────────────────────────────────────────────────

_USAGE = """\
chess_spectral.encoder — 640-dim spectral chess encoder (Python reference).

This module is a library, not a CLI. For command-line use, run the
sibling driver:

    python spectral_py.py csv        game.spectralz -o game.csv
    python spectral_py.py encode     -i game.ndjson -o game.spectral -z
    python spectral_py.py encode-fen --fen "..." -o single.spectral
    python spectral_py.py version

Programmatic use:

    >>> from chess_spectral import encode_640, channel_energies
    >>> from pgn_bridge import fen_to_pos
    >>> pos = fen_to_pos("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    >>> enc = encode_640(pos)          # shape (640,)
    >>> channel_energies(enc)
    {'A1': 0.0, 'A2': 19.845, ...}

Cache inspection:

    >>> from chess_spectral.tables import cache_info, cache_rebuild
    >>> cache_info()
    {'version': '1.0.0', 'source': 'cache', 'path': '...', ...}
"""


def _print_usage() -> None:
    import sys
    print(_USAGE, file=sys.stderr)


if __name__ == "__main__":
    _print_usage()

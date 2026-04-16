"""
safety_field — per-piece defensive coherence from fiber coupling.

Computes a scalar ``S`` per position that sums, over every piece j, the
magnitude-value-weighted difference between friendly and enemy movement-
graph coverage of j's square:

    coverage_side[s] = Σ_{piece i on side, T_i ∈ {N,B,R,Q,K}}
                           |val(T_i)| · LOCAL_ADJ_ROWS[pidx_i, s_i][s]

    safety_j   = coverage_own(s_j) − coverage_opp(s_j)
    weighted_j = |val(T_j)| · safety_j
    S_white    = Σ weighted_j  (white pieces)
    S_black    = Σ weighted_j  (black pieces)
    S_total    = S_white − S_black

Pawns are included as defended targets but skipped as coverage sources
(they're not in SHORT_PFNS / _FIBER_IDX). Pass ``include_pawns=True``
to reserve the hook for a later symmetric-pawn-Laplacian contribution.

The hypothesis (docs/chess-maths/SAFETY_FIELD.md): ΔS across a move
tracks engine-Δeval. Blunders spectrally isolate a piece from its
defensive network and ΔS drops.
"""
from __future__ import annotations

import numpy as np

from .tables import BOARD_DIM, LOCAL_ADJ_ROWS, SPECTRAL_VALS

# Piece-char → LOCAL_ADJ_ROWS first-axis index. Matches encoder.py.
_FIBER_IDX = {'N': 0, 'B': 1, 'R': 2, 'Q': 3, 'K': 4}


def _normalize_pos(pos) -> dict[int, str]:
    if not pos:
        return {}
    first = next(iter(pos))
    if isinstance(first, int):
        return dict(pos)
    return {int(k): v for k, v in pos.items()}


def compute_safety_field(pos, *, include_pawns: bool = False) -> dict:
    """Compute the per-piece and total spectral safety field.

    Parameters
    ----------
    pos : dict[int|str, str]
        Square index → piece char. Uppercase = white, lowercase = black.
        Square convention: ``sq(r,c) = r*8 + c`` with row 0 = rank 8
        (matches ``chess_spectral.fen_to_pos`` and the encoder).
    include_pawns : bool
        Reserved. When True, pawns would contribute to coverage via a
        symmetric-pawn Laplacian. Not yet wired — has no effect today.

    Returns
    -------
    dict with keys:
        per_piece   : {sq: {type, color, val, friendly, enemy, safety, weighted}}
        S_white     : Σ weighted over white pieces
        S_black     : Σ weighted over black pieces
        S_total     : S_white − S_black  (>0 = white's network dominates)
        hanging     : [sq, ...] where safety < 0
        most_exposed: sq with the most-negative weighted (biggest capture reward)
    """
    pos = _normalize_pos(pos)
    del include_pawns  # TODO: wire PAWN_SYM_FIBER when it's factored out

    cov_w = np.zeros(BOARD_DIM)
    cov_b = np.zeros(BOARD_DIM)

    for s, pchar in pos.items():
        T = pchar.upper()
        pidx = _FIBER_IDX.get(T)
        if pidx is None:
            continue  # pawns & unknowns contribute no coverage
        w = abs(SPECTRAL_VALS[T])
        row = LOCAL_ADJ_ROWS[pidx, s]
        if pchar.isupper():
            cov_w += w * row
        else:
            cov_b += w * row

    per_piece: dict[int, dict] = {}
    S_white = 0.0
    S_black = 0.0

    for s, pchar in pos.items():
        T = pchar.upper()
        val_mag = abs(SPECTRAL_VALS[T])
        if pchar.isupper():
            friendly, enemy = float(cov_w[s]), float(cov_b[s])
        else:
            friendly, enemy = float(cov_b[s]), float(cov_w[s])
        safety = friendly - enemy
        weighted = val_mag * safety
        per_piece[s] = {
            'type':     pchar,
            'color':    'w' if pchar.isupper() else 'b',
            'val':      SPECTRAL_VALS[T],       # signed (white +, black −)
            'friendly': friendly,
            'enemy':    enemy,
            'safety':   safety,
            'weighted': weighted,
        }
        if pchar.isupper():
            S_white += weighted
        else:
            S_black += weighted

    hanging = [sq for sq, d in per_piece.items() if d['safety'] < 0]

    if per_piece:
        most_exposed = min(per_piece.items(),
                           key=lambda kv: kv[1]['weighted'])[0]
    else:
        most_exposed = None

    return {
        'per_piece':    per_piece,
        'S_white':      float(S_white),
        'S_black':      float(S_black),
        'S_total':      float(S_white - S_black),
        'hanging':      hanging,
        'most_exposed': most_exposed,
    }


def side_most_exposed(sf: dict, color: str) -> int | None:
    """Return the sq of the most-exposed piece on the given side ('w'|'b')
    from a pre-computed safety field dict. Ties broken by square index."""
    candidates = [(sq, d) for sq, d in sf['per_piece'].items()
                  if d['color'] == color]
    if not candidates:
        return None
    return min(candidates, key=lambda kv: kv[1]['weighted'])[0]

"""
safety_field — per-piece defensive coherence from fiber coupling.

**Status: failed exploration, retained as historical reference.**
The §9o blunder-detection hypothesis (ΔS across a move tracks
engine-Δeval) was tested on two GM games and produced a null
result (``ρ ≈ 0``). The notebook documents the failure mode at
chess_spectral_research_notebook.md §9o:

    "The scalar safety field does NOT correlate with engine
     evaluation. The safety field measures aggregate movement-
     graph coverage — how much of the board's topology each side
     controls. This is a Level 2 (structural) measurement. It
     cannot detect pins, forks, discovered attacks, or overloaded
     defenders, all of which are Level 3 (specific edge
     conjunctions requiring search)."

The module is kept so the §9o experiment is reproducible. It is
NOT a recommended building block for new spectral-chess work; new
analyses should consult the §11 phase-operator framework or the
4D Oana-Chiru work in PHASE_OPERATOR_SUPPLEMENT_4D.md.

What it computes (preserved verbatim from the original
implementation):

    coverage_side[s] = Σ_{piece i on side, T_i ∈ {N,B,R,Q,K}}
                           |val(T_i)| · LOCAL_ADJ_ROWS[pidx_i, s_i][s]

    safety_j   = coverage_own(s_j) − coverage_opp(s_j)
    weighted_j = |val(T_j)| · safety_j
    S_white    = Σ weighted_j  (white pieces)
    S_black    = Σ weighted_j  (black pieces)
    S_total    = S_white − S_black

Pawns are included as defended targets but skipped as coverage
sources (they're not in SHORT_PFNS / _FIBER_IDX). The previous
``include_pawns=True`` extension hook (intended to wire the
symmetric-pawn Laplacian as a future contribution per v1.2.4
inventory item #14) is removed in this release: the parent
hypothesis already failed, so reserving the hook for a parameter
that wouldn't have helped anyway adds maintenance cost without
benefit.
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


def compute_safety_field(pos) -> dict:
    """Compute the per-piece and total spectral safety field.

    See module docstring for the §9o failed-hypothesis context. This
    function is preserved so the §9o experiment is reproducible; the
    previous ``include_pawns`` future-extension hook has been removed
    because the parent hypothesis didn't validate.

    Parameters
    ----------
    pos : dict[int|str, str]
        Square index → piece char. Uppercase = white, lowercase = black.
        Square convention: ``sq(r,c) = r*8 + c`` with row 0 = rank 8
        (matches ``chess_spectral.fen_to_pos`` and the encoder).

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

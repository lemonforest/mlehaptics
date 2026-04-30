"""QM-expectation evaluator for 4D chess (Phase 6.1.3).

4D analogue of :mod:`chess_spectral.engine.eval.qm`. Same shape:

    score = sum_p  alpha_p * <psi | (I_11 (x) H_p_4) | psi>

where ``psi`` lives in C^45056 (per :mod:`chess_spectral.qm_4d`) and
``H_p_4`` is the per-channel C^4096 Hermitian for piece p (rook /
bishop / queen / king / knight). Pawn observables are deferred per
qm_4d ADR-005 -- the QM evaluator excludes them.

See the 2D module's docstring for the cross-cutting design (the
spectral-vs-QM theoretical distinction per §16.7, the depth-decay
empirical question, the §17.2 breakdown contract).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Mapping, Optional, Union

import numpy as np

from chess_spectral import qm_4d
from chess_spectral.encoder_4d import (
    N_CHANNELS_4D, ENCODING_DIM_4D, CHANNEL_DIM, PieceValue,
)


# Type aliases
Position4D = Dict[int, PieceValue]
WeightsLike = Union[None, Mapping[str, float], "Path", str]

# The five Hermitian piece-reach observables.
PIECE_NAMES_4D = ('rook', 'bishop', 'queen', 'king', 'knight')

# Map piece-name to qm_4d.build_H_piece_4 char code.
_PIECE_TO_CHAR_4D: Dict[str, str] = {
    'rook':   'R',
    'bishop': 'B',
    'queen':  'Q',
    'king':   'K',
    'knight': 'N',
}

DEFAULT_WEIGHTS_4D: Dict[str, float] = {p: 1.0 for p in PIECE_NAMES_4D}


_H_CACHE_4D: Dict[str, "object"] = {}


def _get_H_4d(piece_name: str):
    """Cached accessor for the per-channel 4D Hermitian observable."""
    if piece_name not in _H_CACHE_4D:
        char = _PIECE_TO_CHAR_4D[piece_name]
        _H_CACHE_4D[piece_name] = qm_4d.build_H_piece_4(char)
    return _H_CACHE_4D[piece_name]


def observable_expectations(psi: np.ndarray) -> Dict[str, float]:
    """Per-observable raw expectation values on the 4D QM lift.

    For each piece p, computes ``sum_c <psi_c | H_p_4 | psi_c>`` --
    equivalent to ``<psi | (I_11 (x) H_p_4) | psi>`` on the full
    45056-dim psi, computed channel-by-channel for memory efficiency.

    Parameters
    ----------
    psi : ndarray of shape (45056,)
        Output of :func:`chess_spectral.qm_4d.state_to_psi`.

    Returns
    -------
    expectations : dict {piece_name: float}
        Real-valued expectation per piece.
    """
    if psi.shape != (ENCODING_DIM_4D,):
        raise ValueError(
            f"expected psi shape ({ENCODING_DIM_4D},); got {psi.shape}"
        )
    chan_dim = CHANNEL_DIM
    out: Dict[str, float] = {}
    for piece in PIECE_NAMES_4D:
        H = _get_H_4d(piece)
        total = 0.0
        for c in range(N_CHANNELS_4D):
            block = psi[c * chan_dim:(c + 1) * chan_dim]
            total += qm_4d.expectation(H, block)
        out[piece] = float(total)
    return out


def _resolve_weights(weights: WeightsLike) -> Mapping[str, float]:
    if weights is None:
        return DEFAULT_WEIGHTS_4D
    if isinstance(weights, (str, Path)):
        return load_weights_json(weights)
    return weights


def load_weights_json(path: Union[str, Path]) -> Dict[str, float]:
    """Load per-observable weights from a JSON file.

    Same schema as the 2D variant. Subset OK; missing pieces default
    to 1.0; unknown piece names raise ValueError.
    """
    p = Path(path)
    raw = json.loads(p.read_text())
    if not isinstance(raw, dict):
        raise ValueError(
            f"weights JSON {p} must be a dict at the top level; "
            f"got {type(raw).__name__}"
        )
    unknown = set(raw) - set(PIECE_NAMES_4D)
    if unknown:
        raise ValueError(
            f"weights JSON {p} contains unknown observable names "
            f"{sorted(unknown)}; valid names are "
            f"{list(PIECE_NAMES_4D)}"
        )
    out = dict(DEFAULT_WEIGHTS_4D)
    for k, v in raw.items():
        out[k] = float(v)
    return out


def evaluate(position: Position4D,
             side_to_move: bool,
             *,
             weights: WeightsLike = None) -> float:
    """QM-expectation evaluation of a 4D chess position.

    Same surface as the 2D evaluator. See that module for parameter
    docs.
    """
    psi = qm_4d.state_to_psi(position, side_to_move=side_to_move)
    if not qm_4d.is_normalized(psi):
        return 0.0
    expectations = observable_expectations(psi)
    w = _resolve_weights(weights)
    score = 0.0
    for piece in PIECE_NAMES_4D:
        score += w.get(piece, 1.0) * expectations[piece]
    if not side_to_move:
        score = -score
    return float(score)


def evaluate_breakdown(position: Position4D,
                       side_to_move: bool,
                       *,
                       weights: WeightsLike = None
                       ) -> Dict[str, float]:
    """Per-observable contributions (side-to-move-flipped). Sum
    equals :func:`evaluate`."""
    psi = qm_4d.state_to_psi(position, side_to_move=side_to_move)
    if not qm_4d.is_normalized(psi):
        return {p: 0.0 for p in PIECE_NAMES_4D}
    expectations = observable_expectations(psi)
    w = _resolve_weights(weights)
    sign = 1.0 if side_to_move else -1.0
    return {
        piece: sign * w.get(piece, 1.0) * expectations[piece]
        for piece in PIECE_NAMES_4D
    }


__all__ = [
    "evaluate",
    "evaluate_breakdown",
    "observable_expectations",
    "load_weights_json",
    "DEFAULT_WEIGHTS_4D",
    "PIECE_NAMES_4D",
    "Position4D",
    "WeightsLike",
]

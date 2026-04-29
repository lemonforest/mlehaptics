"""Spectral channel-energy evaluator for 4D chess (Phase 6.1.2).

4D analogue of :mod:`chess_spectral.engine.eval.spectral`. Same shape
at 11 channels x 4096 modes:

    score = sum_c  w_c * ||proj_c(v)||^2

where ``v = encode_4d(position)`` and the channels are A1, STD4_X,
STD4_Y, STD4_Z, STD4_W, FIB_SYM_1, FIB_SYM_2, FIB_SYM_3, FA_PAWN_W,
FA_PAWN_Y, FD_DIAG (per :data:`chess_spectral.encoder_4d.CHANNELS_4D`).

See the 2D module's docstring for the cross-cutting design notes
(default weights are intentionally bland; §16.7 Othello prior; how
``--eval-weights JSON`` connects via :func:`load_weights_json`).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Mapping, Optional, Union

import numpy as np

from chess_spectral.encoder_4d import (
    encode_4d, CHANNELS_4D, ENCODING_DIM_4D, N_CHANNELS_4D,
    CHANNEL_DIM, PieceValue,
)

# Type aliases
Position4D = Dict[int, PieceValue]
WeightsLike = Union[None, Mapping[str, float], "Path", str]

# Channel name -> offset / dim. Source of truth is encoder_4d.CHANNELS_4D.
_CHANNEL_NAMES_4D = [name for name, _start in CHANNELS_4D]
_CHANNEL_OFFSETS_4D: Dict[str, int] = {
    name: start for name, start in CHANNELS_4D
}
# Each 4D channel is exactly CHANNEL_DIM (4096) modes -- uniform layout.
# (Unlike 2D where 64 happens to be uniform too, but the assertion below
# makes it explicit.)
_CHANNEL_DIM_4D: int = CHANNEL_DIM
assert (CHANNEL_DIM * N_CHANNELS_4D) == ENCODING_DIM_4D, (
    f"Channel layout mismatch: CHANNEL_DIM ({CHANNEL_DIM}) * "
    f"N_CHANNELS_4D ({N_CHANNELS_4D}) != ENCODING_DIM_4D "
    f"({ENCODING_DIM_4D})"
)
assert len(_CHANNEL_OFFSETS_4D) == N_CHANNELS_4D

# Default weights: equal weighting across all 11 channels. See the 2D
# docstring for the rationale (premature hand-tuning is a Phase 7
# follow-up; Phase 6 ships unbiased defaults so the tournament results
# carry interpretive weight).
DEFAULT_WEIGHTS_4D: Dict[str, float] = {
    name: 1.0 for name in _CHANNEL_NAMES_4D
}


def channel_energies(v: np.ndarray) -> Dict[str, float]:
    """Per-channel L2 energy of a 4D encoder output vector.

    Parameters
    ----------
    v : ndarray of shape (45056,)
        Output of :func:`chess_spectral.encoder_4d.encode_4d`. Float
        dtype is accepted as-is; L2 norm computed in input dtype.

    Returns
    -------
    energies : dict {channel_name: float}
        ``energies[c] = ||v[start:start+4096]||^2`` for each channel.

    Sum equals ``||v||^2`` exactly.
    """
    if v.shape != (ENCODING_DIM_4D,):
        raise ValueError(
            f"expected shape ({ENCODING_DIM_4D},); got {v.shape}"
        )
    out: Dict[str, float] = {}
    for name in _CHANNEL_NAMES_4D:
        start = _CHANNEL_OFFSETS_4D[name]
        block = v[start:start + _CHANNEL_DIM_4D]
        out[name] = float(np.vdot(block, block).real)
    return out


def _resolve_weights(weights: WeightsLike) -> Mapping[str, float]:
    if weights is None:
        return DEFAULT_WEIGHTS_4D
    if isinstance(weights, (str, Path)):
        return load_weights_json(weights)
    return weights


def load_weights_json(path: Union[str, Path]) -> Dict[str, float]:
    """Load per-channel weights from a JSON file.

    Expected JSON schema (subset of full keys is fine; missing default
    to 1.0; unknown channel names raise ValueError)::

        {
          "A1": 1.0, "STD4_X": 0.7, "STD4_Y": 0.7, "STD4_Z": 0.7,
          "STD4_W": 0.7, "FIB_SYM_1": 0.5, "FIB_SYM_2": 0.5,
          "FIB_SYM_3": 0.5, "FA_PAWN_W": 0.6, "FA_PAWN_Y": 0.6,
          "FD_DIAG": 0.4
        }

    Returns
    -------
    weights : dict {channel_name: float}
        Every known channel populated.
    """
    p = Path(path)
    raw = json.loads(p.read_text())
    if not isinstance(raw, dict):
        raise ValueError(
            f"weights JSON {p} must be a dict at the top level; "
            f"got {type(raw).__name__}"
        )
    unknown = set(raw) - set(_CHANNEL_NAMES_4D)
    if unknown:
        raise ValueError(
            f"weights JSON {p} contains unknown channels "
            f"{sorted(unknown)}; valid channels are "
            f"{_CHANNEL_NAMES_4D}"
        )
    out = dict(DEFAULT_WEIGHTS_4D)
    for k, v in raw.items():
        out[k] = float(v)
    return out


def evaluate(position: Position4D,
             side_to_move: bool,
             *,
             weights: WeightsLike = None) -> float:
    """Spectral channel-energy evaluation of a 4D chess position.

    Same surface as the 2D evaluator -- see that module for parameter
    docs. Pawn axis (the ``'w'`` / ``'y'`` second tuple element) is
    consumed by ``encode_4d`` directly; the spectral evaluator sees
    only the encoded vector and is axis-aware via the channels
    ``FA_PAWN_W`` and ``FA_PAWN_Y`` that the encoder populates.
    """
    v = encode_4d(position).astype(np.float64, copy=False)
    energies = channel_energies(v)
    w = _resolve_weights(weights)
    score = 0.0
    for name in _CHANNEL_NAMES_4D:
        score += w.get(name, 1.0) * energies[name]
    if not side_to_move:
        score = -score
    return float(score)


def evaluate_breakdown(position: Position4D,
                       side_to_move: bool,
                       *,
                       weights: WeightsLike = None
                       ) -> Dict[str, float]:
    """Per-channel score contributions, for HUD displays.

    Returns ``{channel_name: w_c * E_c}`` already side-to-move-flipped.
    Sum equals :func:`evaluate` exactly.
    """
    v = encode_4d(position).astype(np.float64, copy=False)
    energies = channel_energies(v)
    w = _resolve_weights(weights)
    sign = 1.0 if side_to_move else -1.0
    return {
        name: sign * w.get(name, 1.0) * energies[name]
        for name in _CHANNEL_NAMES_4D
    }


__all__ = [
    "evaluate",
    "evaluate_breakdown",
    "channel_energies",
    "load_weights_json",
    "DEFAULT_WEIGHTS_4D",
    "Position4D",
    "WeightsLike",
]

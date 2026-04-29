"""Spectral channel-energy evaluator for 2D chess (Phase 6.1.2).

Computes per-channel L2 energy from the 640-dim encoder output, then
returns a weighted sum:

    score = sum_c  w_c * ||proj_c(v)||^2

where ``v = encode_640(position)`` and ``proj_c`` slices the 64-mode
block corresponding to channel ``c`` (one of A1, A2, B1, B2, E, F1,
F2, F3, FA, FD; see :data:`chess_spectral.encoder.CHANNELS`).

The energy magnitude is positive for any non-empty position; the
side-to-move flip is applied at the score level (negate the whole
score for black-to-move). Per-channel weights ``w_c`` are tunable:

  * Default weights: equal weighting (``1.0`` for every channel).
    This is intentionally bland -- the §16 self-play tournament is
    designed to empirically test whether the encoded representation
    contains exploitable structure, and weight engineering is a
    Phase 7+ follow-up. Changing the defaults here without
    tournament evidence would be premature hand-tuning.

  * Custom weights: pass a ``{channel_name: float}`` dict via the
    ``weights`` keyword argument, or load from a JSON file via
    :func:`load_weights_json`.

  * Per-§16.7 Othello prior: spectral channel-energy weighting is
    structurally analogous to Architecture A in the Edax-Othello
    archive, which won +243 Elo at L6 and decayed to 0 Elo at L10+.
    Whether chess shows the same depth-decay is the load-bearing
    empirical question §16 is designed to answer.

The 4D analogue lives in :mod:`chess_spectral_4d.engine.eval.spectral`
with the same shape and 11 channels (A1, STD4_X/Y/Z/W, FIB_SYM_1/2/3,
FA_PAWN_W/Y, FD_DIAG; see encoder_4d.CHANNELS_4D).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Mapping, Optional, Union

import numpy as np

from chess_spectral.encoder import (
    encode_640, CHANNELS, ENCODING_DIM, N_CHANNELS,
)

# Type aliases
Position2D = Dict[int, str]
WeightsLike = Union[None, Mapping[str, float], "Path", str]

# Channel name -> (start, end) byte-offsets into the 640-dim vector.
# Source of truth is encoder.CHANNELS (a list of (name, start)).
_CHANNEL_NAMES = [name for name, _start in CHANNELS]
_CHANNEL_DIMS: Dict[str, int] = {}
_CHANNEL_OFFSETS: Dict[str, int] = {}
for i, (name, start) in enumerate(CHANNELS):
    _CHANNEL_OFFSETS[name] = start
    if i + 1 < len(CHANNELS):
        end = CHANNELS[i + 1][1]
    else:
        end = ENCODING_DIM
    _CHANNEL_DIMS[name] = end - start

# Sanity: total dims sum to 640 across all 10 channels.
assert sum(_CHANNEL_DIMS.values()) == ENCODING_DIM, (
    f"Channel layout mismatch: sum(_CHANNEL_DIMS) "
    f"{sum(_CHANNEL_DIMS.values())} != ENCODING_DIM {ENCODING_DIM}"
)
assert len(_CHANNEL_DIMS) == N_CHANNELS

# Default weights: equal weighting (1.0 per channel). Documented as
# intentionally non-tuned; the empirical-tuning question is a Phase 7
# research follow-up per §16.1.2.
DEFAULT_WEIGHTS: Dict[str, float] = {name: 1.0 for name in _CHANNEL_NAMES}


def channel_energies(v: np.ndarray) -> Dict[str, float]:
    """Per-channel L2 energy of an encoder output vector.

    Parameters
    ----------
    v : ndarray of shape (640,)
        Output of :func:`chess_spectral.encode_640`. Float dtype is
        accepted as-is; the L2 norm is computed in the input dtype.

    Returns
    -------
    energies : dict {channel_name: float}
        ``energies[c] = ||v[start:end]||^2`` for each channel, where
        the slice covers the channel's 64-mode block.

    The sum over all channels equals ``||v||^2`` exactly (Plancherel
    /channel-orthogonal decomposition of the encoder output).
    """
    if v.shape != (ENCODING_DIM,):
        raise ValueError(
            f"expected shape ({ENCODING_DIM},); got {v.shape}"
        )
    out: Dict[str, float] = {}
    for name in _CHANNEL_NAMES:
        start = _CHANNEL_OFFSETS[name]
        dim = _CHANNEL_DIMS[name]
        block = v[start:start + dim]
        out[name] = float(np.vdot(block, block).real)
    return out


def _resolve_weights(weights: WeightsLike) -> Mapping[str, float]:
    """Normalize the ``weights`` argument to a dict.

    Accepts None (default weights), a dict (used verbatim; missing
    channels default to 1.0), a string path, or a Path object. JSON
    files are loaded via :func:`load_weights_json`.
    """
    if weights is None:
        return DEFAULT_WEIGHTS
    if isinstance(weights, (str, Path)):
        return load_weights_json(weights)
    # dict-like
    return weights


def load_weights_json(path: Union[str, Path]) -> Dict[str, float]:
    """Load per-channel weights from a JSON file.

    Expected JSON schema::

        {
          "A1": 1.0, "A2": 0.5, "B1": 0.3, "B2": 0.3, "E": 0.8,
          "F1": 0.4, "F2": 0.4, "F3": 0.4, "FA": 0.6, "FD": 0.7
        }

    Missing channels default to 1.0; unknown channels in the file
    raise ValueError (so a typo doesn't silently produce wrong
    scores).

    Returns
    -------
    weights : dict {channel_name: float}
        With every known channel populated (defaults filled in).
    """
    p = Path(path)
    raw = json.loads(p.read_text())
    if not isinstance(raw, dict):
        raise ValueError(
            f"weights JSON {p} must be a dict at the top level; "
            f"got {type(raw).__name__}"
        )
    unknown = set(raw) - set(_CHANNEL_NAMES)
    if unknown:
        raise ValueError(
            f"weights JSON {p} contains unknown channels "
            f"{sorted(unknown)}; valid channels are {_CHANNEL_NAMES}"
        )
    out = dict(DEFAULT_WEIGHTS)
    for k, v in raw.items():
        out[k] = float(v)
    return out


def evaluate(position: Position2D,
             side_to_move: bool,
             *,
             weights: WeightsLike = None) -> float:
    """Spectral channel-energy evaluation of a 2D chess position.

    Parameters
    ----------
    position : dict {sq -> piece char}
        Same schema as :func:`chess_spectral.encode_640`.
    side_to_move : bool
        True == white to move; False == black to move. Score is
        flipped to side-to-move's perspective: positive == winning.
    weights : None, dict, str path, or Path, default None
        ``None`` selects :data:`DEFAULT_WEIGHTS` (equal 1.0 across
        channels). A dict is used as-is (missing channels default to
        1.0). A path string or :class:`pathlib.Path` is loaded via
        :func:`load_weights_json`.

    Returns
    -------
    score : float
        ``sum_c  w_c * ||proj_c(v)||^2``, then sign-flipped if
        ``side_to_move == False``. For an empty position this is 0
        (encoder returns the zero vector).

    Raises
    ------
    ValueError
        If a JSON weights file contains unknown channel names.
    """
    v = encode_640(position).astype(np.float64, copy=False)
    energies = channel_energies(v)
    w = _resolve_weights(weights)
    score = 0.0
    for name in _CHANNEL_NAMES:
        score += w.get(name, 1.0) * energies[name]
    if not side_to_move:
        score = -score
    return float(score)


def evaluate_breakdown(position: Position2D,
                       side_to_move: bool,
                       *,
                       weights: WeightsLike = None
                       ) -> Dict[str, float]:
    """Per-channel score contributions, for HUD displays.

    Returns a dict ``{channel_name: w_c * E_c}`` (already flipped for
    side_to_move). Useful for the §17.2 ``breakdown`` field on
    ``evaluatePosition`` bridge calls -- the chess4D-OC consumer
    displays a per-channel bar chart.

    The sum of values equals :func:`evaluate` exactly.
    """
    v = encode_640(position).astype(np.float64, copy=False)
    energies = channel_energies(v)
    w = _resolve_weights(weights)
    sign = 1.0 if side_to_move else -1.0
    return {
        name: sign * w.get(name, 1.0) * energies[name]
        for name in _CHANNEL_NAMES
    }


__all__ = [
    "evaluate",
    "evaluate_breakdown",
    "channel_energies",
    "load_weights_json",
    "DEFAULT_WEIGHTS",
    "Position2D",
    "WeightsLike",
]

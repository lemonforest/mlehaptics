"""QM-expectation evaluator for 2D chess (Phase 6.1.3).

Third of the three §16.1 evaluator families. Computes Born-rule
expectation values of Hermitian piece-reach observables on the
quantum-mechanical lift of the encoder output:

    score = sum_p  alpha_p * <psi | (I_10 (x) H_p_2) | psi>

where ``psi = state_to_psi(position, side_to_move)`` lives in C^640
(per :mod:`chess_spectral.qm_2d`) and ``H_p_2`` is the per-channel
C^64 Hermitian for piece p (one of rook, bishop, queen, king,
knight; pawns deferred to the pseudo-Hermitian eta-metric extension).

The lift to the full 640-dim space is the block-diagonal
``I_10 (x) H_p_2`` -- the same per-channel observable applied
identically to each of the 10 channels. Operationally we don't
materialize the 640x640 lifted operator; we compute
``sum_c <psi_c | H_p_2 | psi_c>`` over per-channel slices, which is
mathematically equivalent and uses 10x less memory.

Why this evaluator family matters (per §16.5)
---------------------------------------------
The QM-expectation form ``<psi|O|psi>`` is **structurally different**
from spectral channel-energy weighting:

  * Spectral evaluator: linear sum of squared-norm projections.
    Per §16.7's Othello prior, this won +243 Elo at L6 in the
    Edax archive but decayed to 0 at L10+. Whether chess shows
    the same depth-decay is the load-bearing empirical question.
  * QM evaluator: expectation values of Hermitian operators in a
    fixed basis. Whether this faces the same depth-decay is
    genuinely open per §16.7's design notes -- the §16
    tournament harness is what answers it.

Public API
----------
  evaluate(position, side_to_move, *, weights=None) -> float
    Score from side-to-move's perspective. weights accepts None
    (default unit weight on all 5 piece observables), a {piece_name:
    float} dict, or a path to a JSON weights file.
  evaluate_breakdown(position, side_to_move, *, weights=None) ->
    dict[piece_name, float]
    Per-observable contributions (already side-to-move-flipped).
    Sum equals evaluate(). For the §17.2 evaluatePosition.breakdown
    field that the chess4D-OC HUD displays.
  observable_expectations(psi) -> dict[piece_name, float]
    Per-observable raw expectation values <psi|H_p|psi> on the
    lifted 640-dim space. No weighting, no side-to-move flip.

Default weights
---------------
All 5 piece weights default to 1.0. As with the spectral evaluator,
defaults are intentionally unbiased -- the §16 tournament harness is
the empirical mechanism for weight refinement.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Mapping, Optional, Union

import numpy as np

from chess_spectral import qm_2d
from chess_spectral.encoder import N_CHANNELS, ENCODING_DIM


# Type aliases
Position2D = Dict[int, str]
WeightsLike = Union[None, Mapping[str, float], "Path", str]

# The five Hermitian piece-reach observables (kinematic, non-pawn).
# Pawn observables raise NotImplementedError until the pseudo-
# Hermitian / eta-metric extension lands; the QM evaluator excludes
# them.
PIECE_NAMES = ('rook', 'bishop', 'queen', 'king', 'knight')

# Map piece-name to qm_2d.build_H_piece_2 char code.
_PIECE_TO_CHAR: Dict[str, str] = {
    'rook':   'R',
    'bishop': 'B',
    'queen':  'Q',
    'king':   'K',
    'knight': 'N',
}

# Default weights: 1.0 per piece observable.
DEFAULT_WEIGHTS: Dict[str, float] = {p: 1.0 for p in PIECE_NAMES}


# Module-level cache of materialised H_piece_2 sparse matrices.
# Reuses qm_2d's lazy cache via build_H_piece_2; this dict holds the
# concrete references for the evaluator's hot loop.
_H_CACHE: Dict[str, "object"] = {}


def _get_H(piece_name: str):
    """Cached accessor for the per-channel Hermitian observable."""
    if piece_name not in _H_CACHE:
        char = _PIECE_TO_CHAR[piece_name]
        _H_CACHE[piece_name] = qm_2d.build_H_piece_2(char)
    return _H_CACHE[piece_name]


def observable_expectations(psi: np.ndarray) -> Dict[str, float]:
    """Per-observable raw expectation values on the QM lift.

    For each piece p in (rook, bishop, queen, king, knight),
    computes ``sum_c <psi_c | H_p_2 | psi_c>`` -- equivalent to the
    expectation value of the lifted operator ``I_10 (x) H_p_2`` on
    the full 640-dim psi, but computed channel-by-channel to avoid
    materializing the lifted operator.

    Parameters
    ----------
    psi : ndarray of shape (640,)
        Output of :func:`chess_spectral.qm_2d.state_to_psi`. Complex
        dtype expected (cast at use).

    Returns
    -------
    expectations : dict {piece_name: float}
        Real-valued expectation per piece. The map is equal-keyed
        regardless of psi norm (zero psi -> all zeros).
    """
    if psi.shape != (ENCODING_DIM,):
        raise ValueError(
            f"expected psi shape ({ENCODING_DIM},); got {psi.shape}"
        )
    chan_dim = qm_2d.CHANNEL_DIM
    out: Dict[str, float] = {}
    # For each piece, sum the per-channel expectation. The lifted
    # operator I_10 (x) H_p_2 has the same H_p_2 acting on every
    # channel block; the block sum equals <psi | (I_10 (x) H_p) | psi>.
    for piece in PIECE_NAMES:
        H = _get_H(piece)
        total = 0.0
        for c in range(N_CHANNELS):
            block = psi[c * chan_dim:(c + 1) * chan_dim]
            total += qm_2d.expectation(H, block)
        out[piece] = float(total)
    return out


def _resolve_weights(weights: WeightsLike) -> Mapping[str, float]:
    if weights is None:
        return DEFAULT_WEIGHTS
    if isinstance(weights, (str, Path)):
        return load_weights_json(weights)
    return weights


def load_weights_json(path: Union[str, Path]) -> Dict[str, float]:
    """Load per-observable weights from a JSON file.

    Expected schema (subset OK; missing pieces default to 1.0;
    unknown piece names raise ValueError)::

        {"rook": 1.5, "queen": 1.2, "king": 0.5,
         "knight": 0.8, "bishop": 1.0}

    Returns
    -------
    weights : dict {piece_name: float}
        Every PIECE_NAMES entry populated.
    """
    p = Path(path)
    raw = json.loads(p.read_text())
    if not isinstance(raw, dict):
        raise ValueError(
            f"weights JSON {p} must be a dict at the top level; "
            f"got {type(raw).__name__}"
        )
    unknown = set(raw) - set(PIECE_NAMES)
    if unknown:
        raise ValueError(
            f"weights JSON {p} contains unknown observable names "
            f"{sorted(unknown)}; valid names are {list(PIECE_NAMES)}"
        )
    out = dict(DEFAULT_WEIGHTS)
    for k, v in raw.items():
        out[k] = float(v)
    return out


def evaluate(position: Position2D,
             side_to_move: bool,
             *,
             weights: WeightsLike = None) -> float:
    """QM-expectation evaluation of a 2D chess position.

    Parameters
    ----------
    position : dict {sq -> piece char}
        Same schema as :func:`chess_spectral.encode_640`.
    side_to_move : bool
        True == white to move; False == black to move. The QM lift
        applies the +/-1 sign-flip via :func:`qm_2d.state_to_psi`;
        the score is then sign-flipped to side-to-move's perspective.
        (Note: the Z_2 sector flip in state_to_psi is *separate* from
        the score sign flip applied here. The sector flip ensures
        psi is a unique physical state; the score flip puts the
        evaluation in side-to-move convention. They compose.)
    weights : None, dict, str path, or Path, default None
        ``None`` -> :data:`DEFAULT_WEIGHTS` (all pieces unit-weighted).
        Dict / path: see :func:`load_weights_json`.

    Returns
    -------
    score : float
        sum_p  alpha_p * <psi | (I_10 (x) H_p_2) | psi>, then flipped
        for side_to_move. For an empty position (psi == zero vector),
        returns 0.0.
    """
    psi = qm_2d.state_to_psi(position, side_to_move=side_to_move)
    if not qm_2d.is_normalized(psi):
        # Empty / pathological position. The evaluator's contract is
        # to return a finite real; expectations on the zero vector
        # are zero.
        return 0.0
    expectations = observable_expectations(psi)
    w = _resolve_weights(weights)
    score = 0.0
    for piece in PIECE_NAMES:
        score += w.get(piece, 1.0) * expectations[piece]
    # Note: state_to_psi already applies the +/-1 sign flip for the
    # Z_2 sector convention. Does that flip the score? Both psi and
    # -psi yield the same expectation <psi|H|psi> (the sign cancels
    # in the inner product). So state_to_psi's sign flip is
    # invisible at the expectation-value level; we apply our own
    # side-to-move flip on the score below.
    if not side_to_move:
        score = -score
    return float(score)


def evaluate_breakdown(position: Position2D,
                       side_to_move: bool,
                       *,
                       weights: WeightsLike = None
                       ) -> Dict[str, float]:
    """Per-observable score contributions (already side-to-move-flipped).

    Sum equals :func:`evaluate` exactly. For the §17.2
    ``evaluatePosition.breakdown`` field consumed by the chess4D-OC
    HUD.
    """
    psi = qm_2d.state_to_psi(position, side_to_move=side_to_move)
    if not qm_2d.is_normalized(psi):
        return {p: 0.0 for p in PIECE_NAMES}
    expectations = observable_expectations(psi)
    w = _resolve_weights(weights)
    sign = 1.0 if side_to_move else -1.0
    return {
        piece: sign * w.get(piece, 1.0) * expectations[piece]
        for piece in PIECE_NAMES
    }


__all__ = [
    "evaluate",
    "evaluate_breakdown",
    "observable_expectations",
    "load_weights_json",
    "DEFAULT_WEIGHTS",
    "PIECE_NAMES",
    "Position2D",
    "WeightsLike",
]

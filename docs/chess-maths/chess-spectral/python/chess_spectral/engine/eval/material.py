"""Material evaluator for 2D chess (Phase 6.1.1).

Standard piece-count score: sum of signed piece values, flipped to the
side-to-move's perspective. Pure baseline; no encoder call, no scipy,
no math beyond integer addition. The other two evaluator families
(spectral, qm) are tested *against* this baseline in the §16
self-play tournament, so it must be cheap, deterministic, and not
over-cleverly tuned.

Two value tables ship by default:

  * ``'spectral'`` (default) -- :data:`chess_spectral.tables.SPECTRAL_VALS`,
    the spectrally-derived values from §3 of the research notebook.
    Captures the resonant structure of the lattice-graph eigenbasis;
    differs from textbook values most for the rook and queen.

  * ``'standard'`` -- :data:`chess_spectral.tables.VALS`, the textbook
    1 / 3 / 3.5 / 5 / 9 / 100 piece weights. Useful as an unweighted
    baseline for ablations.

Callers can also pass a custom dict ``{piece_char: value}``. Pieces
absent from the dict score 0 (used to ablate a piece type from the
material count, e.g., for "rook-only material" diagnostics).

The score is always real-valued and finite for any non-empty position
(both kings always present in a legal chess position, but this
function does not validate legality -- empty positions or kings-only
positions return finite values).
"""
from __future__ import annotations

from typing import Dict, Mapping, Union

from chess_spectral.tables import SPECTRAL_VALS, VALS

# Type aliases for the (position, value-table) interface.
Position2D = Dict[int, str]
ValueTable = Union[str, Mapping[str, float]]

_BUILTIN_TABLES: Dict[str, Mapping[str, float]] = {
    "spectral": SPECTRAL_VALS,
    "standard": VALS,
}


def evaluate(position: Position2D,
             side_to_move: bool,
             *,
             values: ValueTable = "spectral") -> float:
    """Material evaluation of a 2D chess position.

    Parameters
    ----------
    position : dict {sq -> piece char}
        Same schema as :func:`chess_spectral.encode_640`. Square
        indices 0..63 (row-major from a8=0); piece chars upper-case
        for white ('P','N','B','R','Q','K') and lower-case for black.
    side_to_move : bool
        True == white to move; False == black to move. The score is
        flipped to side-to-move's perspective: positive == winning
        for the side to move.
    values : str or dict, default ``'spectral'``
        Value table. ``'spectral'`` selects the spectrally-derived
        :data:`chess_spectral.tables.SPECTRAL_VALS` (default).
        ``'standard'`` selects the textbook
        :data:`chess_spectral.tables.VALS`. A dict is taken verbatim;
        pieces not in the dict score 0.

    Returns
    -------
    score : float
        Material score from side-to-move's perspective. Positive ==
        side-to-move winning. For an empty position, returns 0.0.

    Raises
    ------
    ValueError
        If ``values`` is a string not in the built-in table set.
    """
    if isinstance(values, str):
        if values not in _BUILTIN_TABLES:
            raise ValueError(
                f"unknown value table {values!r}; expected one of "
                f"{sorted(_BUILTIN_TABLES)}, or a dict mapping piece "
                f"chars to floats"
            )
        table = _BUILTIN_TABLES[values]
    else:
        table = values

    score = 0.0
    for piece in position.values():
        score += float(table.get(piece, 0.0))
    if not side_to_move:
        score = -score
    return score


def evaluate_white(position: Position2D,
                   *,
                   values: ValueTable = "spectral") -> float:
    """Material score from white's perspective (no side-to-move flip).

    Convenience for callers that want the absolute material balance
    without engine-style perspective flipping. Equivalent to
    ``evaluate(position, side_to_move=True, values=values)``.

    Useful for HUD displays and corpus statistics.
    """
    return evaluate(position, side_to_move=True, values=values)


__all__ = [
    "evaluate",
    "evaluate_white",
    "Position2D",
    "ValueTable",
]

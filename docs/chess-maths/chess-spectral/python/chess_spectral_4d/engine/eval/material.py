"""Material evaluator for 4D chess (Phase 6.1.1).

4D analogue of :mod:`chess_spectral.engine.eval.material`. Same
side-to-move-flipped semantics, same value tables (spectral /
standard / custom dict), same return type.

The one 4D-specific concern: position values are
:type:`chess_spectral.encoder_4d.PieceValue` -- either a piece char
(``'K'``, ``'p'``, ...) for non-pawns or a tuple ``(piece_char,
axis)`` for pawns. Material count does not depend on pawn axis
(both ``('P','w')`` and ``('P','y')`` are pawns), so the axis is
stripped before the value-table lookup.

Legacy single-char pawn values (``'P'``, ``'p'``) are accepted with
the same valuation as their axis-tagged variants -- the encoder emits
a DeprecationWarning when it sees these, but the material evaluator
does not (we don't want to spam warnings during search).
"""
from __future__ import annotations

from typing import Dict, Mapping, Tuple, Union

from chess_spectral.tables import SPECTRAL_VALS, VALS
from chess_spectral.encoder_4d import _is_pawn, _piece_char, PieceValue

# Type aliases mirroring the 2D module.
Position4D = Dict[int, PieceValue]
ValueTable = Union[str, Mapping[str, float]]

_BUILTIN_TABLES: Dict[str, Mapping[str, float]] = {
    "spectral": SPECTRAL_VALS,
    "standard": VALS,
}


def _value_for_4d_piece(value: PieceValue,
                        table: Mapping[str, float]) -> float:
    """Look up the material value for a 4D piece value.

    Strips the pawn axis when present (axis affects movement, not
    material). Returns 0.0 for pieces absent from the table.
    """
    if _is_pawn(value):
        # ('P', 'w') / ('P', 'y') -> 'P'; ('p', 'w') / ('p', 'y') -> 'p'.
        # Legacy single-char 'P' / 'p' also returns 'P' / 'p' via the
        # same accessor.
        char = _piece_char(value)
    else:
        # Non-pawns are single-char strings already.
        char = value if isinstance(value, str) else value[0]
    return float(table.get(char, 0.0))


def evaluate(position: Position4D,
             side_to_move: bool,
             *,
             values: ValueTable = "spectral") -> float:
    """Material evaluation of a 4D chess position.

    Parameters
    ----------
    position : dict {sq4 -> PieceValue}
        Same schema as :func:`chess_spectral.encoder_4d.encode_4d`.
        Pawn values are typically tuples ``('P', 'w')`` /
        ``('p', 'y')`` etc.; the legacy single-char form ``'P'`` /
        ``'p'`` is also accepted.
    side_to_move : bool
        True == white to move; False == black to move. Score is
        flipped to side-to-move's perspective: positive == winning.
    values : str or dict, default ``'spectral'``
        Value table. ``'spectral'`` -> SPECTRAL_VALS (default).
        ``'standard'`` -> textbook VALS. A dict is taken verbatim
        (pieces not in the dict score 0); the dict keys are piece
        chars (``'P'``, ``'K'``, ``'p'``, ...) -- pawn axis is
        stripped before lookup, so don't expect ``('P','w')`` keys
        in the dict.

    Returns
    -------
    score : float
        Material score from side-to-move's perspective.

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
    for piece_value in position.values():
        score += _value_for_4d_piece(piece_value, table)
    if not side_to_move:
        score = -score
    return score


def evaluate_white(position: Position4D,
                   *,
                   values: ValueTable = "spectral") -> float:
    """Material score from white's perspective (no side-to-move flip).

    Convenience for HUD displays and corpus statistics. Equivalent to
    ``evaluate(position, side_to_move=True, values=values)``.
    """
    return evaluate(position, side_to_move=True, values=values)


__all__ = [
    "evaluate",
    "evaluate_white",
    "Position4D",
    "ValueTable",
]

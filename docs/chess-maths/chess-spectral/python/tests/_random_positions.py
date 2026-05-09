"""Deterministic random position generators for pedantic stress testing.

The encoder accepts ANY position dict — it doesn't require the
position to be game-legal. Stress testing exercises that surface
with broad coverage:

  * variable piece count (sparse to dense)
  * uniform piece-type distribution
  * uniform square distribution (no duplicates)
  * piece colors mixed both ways

Tests using these generators get reproducibility from seeded RNG.
The 2D and 4D generators have parallel structure for parity in the
stress tests.
"""
from __future__ import annotations

import random
from typing import Dict, List, Optional, Tuple


# 2D piece characters: uppercase = white, lowercase = black.
_2D_PIECE_CHARS: Tuple[str, ...] = (
    'P', 'N', 'B', 'R', 'Q', 'K',
    'p', 'n', 'b', 'r', 'q', 'k',
)

# 4D piece values: same chars for non-pawns; pawns are (color_char,
# axis_char) tuples per Oana-Chiru Definition 11. We sample the
# axis from {'y', 'w'} ('z' is forbidden).
_4D_NONPAWN_CHARS: Tuple[str, ...] = (
    'N', 'B', 'R', 'Q', 'K',
    'n', 'b', 'r', 'q', 'k',
)

_4D_PAWN_VALUES: Tuple[Tuple[str, str], ...] = (
    ('P', 'y'), ('P', 'w'),
    ('p', 'y'), ('p', 'w'),
)


def random_pos_2d(
    n_pieces: int,
    seed: int,
    *,
    n_squares: int = 64,
) -> Dict[int, str]:
    """Generate a random 2D position with ``n_pieces`` pieces.

    Pieces are drawn uniformly from ``_2D_PIECE_CHARS`` (12 types
    counting both colors). Squares are drawn uniformly from
    ``[0, n_squares)`` without replacement.

    Parameters
    ----------
    n_pieces : int
        Number of pieces to place. Must be ≤ ``n_squares``.
    seed : int
        Seed for the deterministic RNG.
    n_squares : int, optional
        Total board squares. Default 64 (standard 2D). Custom
        values allowed for synthetic edge cases.

    Returns
    -------
    dict[int, str]
        ``{sq: piece_char}`` encoder format.
    """
    if n_pieces > n_squares:
        raise ValueError(
            f"n_pieces={n_pieces} > n_squares={n_squares}"
        )
    rng = random.Random(seed)
    squares = rng.sample(range(n_squares), n_pieces)
    pos: Dict[int, str] = {}
    for sq in squares:
        pos[sq] = rng.choice(_2D_PIECE_CHARS)
    return pos


def random_pos_4d(
    n_pieces: int,
    seed: int,
    *,
    n_squares: int = 4096,
) -> Dict[int, "object"]:
    """Generate a random 4D position with ``n_pieces`` pieces.

    Mirrors :func:`random_pos_2d` but uses 4D's piece-value schema:

      * Non-pawn pieces: single char from ``_4D_NONPAWN_CHARS``.
      * Pawns: tuples ``(color_char, axis_char)`` with
        ``axis_char ∈ {'y', 'w'}`` per Oana-Chiru Definition 11.

    Pieces are drawn uniformly from the union (10 non-pawn types
    + 4 pawn types = 14 total). Squares drawn from
    ``[0, n_squares)`` without replacement.

    Parameters
    ----------
    n_pieces : int
    seed : int
    n_squares : int, optional
        Default 4096 (standard 4D Z₈⁴).

    Returns
    -------
    dict[int, str | tuple[str, str]]
        ``{sq: piece_value}`` 4D-encoder format.
    """
    if n_pieces > n_squares:
        raise ValueError(
            f"n_pieces={n_pieces} > n_squares={n_squares}"
        )
    rng = random.Random(seed)
    squares = rng.sample(range(n_squares), n_pieces)
    all_values: List = list(_4D_NONPAWN_CHARS) + list(_4D_PAWN_VALUES)
    pos: Dict[int, "object"] = {}
    for sq in squares:
        pos[sq] = rng.choice(all_values)
    return pos


def piece_count_distribution_2d(
    n_samples: int,
    seed: int,
    *,
    min_pieces: int = 2,
    max_pieces: int = 32,
) -> List[int]:
    """Generate a list of ``n_samples`` piece counts uniformly
    distributed in ``[min_pieces, max_pieces]``.

    Used by the stress tests to span sparse-to-dense positions
    rather than concentrating on a single density.
    """
    rng = random.Random(seed)
    return [rng.randint(min_pieces, max_pieces) for _ in range(n_samples)]


def piece_count_distribution_4d(
    n_samples: int,
    seed: int,
    *,
    min_pieces: int = 2,
    max_pieces: int = 256,
) -> List[int]:
    """4D analog. Default range is ``[2, 256]`` — the canonical
    Oana-Chiru §3.3 starting position has 896 pieces but typical
    research positions are sparser; 256 covers a wide density
    band without exploding bench cost."""
    rng = random.Random(seed)
    return [rng.randint(min_pieces, max_pieces) for _ in range(n_samples)]


__all__ = [
    "random_pos_2d",
    "random_pos_4d",
    "piece_count_distribution_2d",
    "piece_count_distribution_4d",
]

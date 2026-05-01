"""Canonical Oana-Chiru 4D initial position.

This module is the authoritative source of the 4D chess starting
position used across the chess-spectral / chess4D-OC stack. The
upstream paper (Oana & Chiru, *AppliedMath* 6(3):48, 2026) defines
the layout in §3.3 ("4D Initial Position Specification"); we
reproduce it here in code form and emit it as a FEN4 v1 placement
literal.

We define our own canonical FEN4 string here because we're the
canonical source for the FEN4 format itself (see
``docs/FEN4_FORMAT.md``); without a programmatic spec in this
package, the chess4D-OC visualizer and the chess-spectral engine
were each having to round-trip a hand-authored layout through
``GameState4D.from_fen4`` to start a game. 1.8.1 closes that gap.

Specification (paper §3.3, translated to FEN4 0-indexed coords):

  z, w ∈ {0, ..., 7} (paper uses 1-indexed; we subtract 1).

  Slice classification by (z, w):

    Central C = {(z, w) | z ∈ {3, 4}, w ∈ {3, 4}}                  (4 boards)
      → full standard 2D start: both white AND black

    White-only W_only = {(z, w) | z ∈ {0, 1, 2}, w ∈ {0, 1, 2, 3}}
                      ∪ {(z, w) | z ∈ {5, 6, 7}, w ∈ {4, 5, 6, 7}} (24 boards)
      → standard 2D white pieces only

    Black-only B_only = {(z, w) | z ∈ {0, 1, 2}, w ∈ {4, 5, 6, 7}}
                      ∪ {(z, w) | z ∈ {5, 6, 7}, w ∈ {0, 1, 2, 3}} (24 boards)
      → standard 2D black pieces only

    Empty E = {(z, w) | z ∈ {3, 4}, w ∈ {0, 1, 2, 5, 6, 7}}        (12 boards)
      → no pieces

  |C| + |W_only| + |B_only| + |E| = 4 + 24 + 24 + 12 = 64 ✓

  Standard 2D starting array (FEN4 0-indexed; paper y=1 → FEN4 y=0):

    y=0 White back rank: R N B Q K B N R at x=0..7
    y=1 White pawns:     8 pawns at x=0..7
    y=6 Black pawns:     8 pawns at x=0..7
    y=7 Black back rank: r n b q k b n r at x=0..7

  Pawn orientation (paper Definition 11):

    even x ∈ {0, 2, 4, 6} → Y-oriented (FEN4 spec ``Py`` / ``py``)
    odd  x ∈ {1, 3, 5, 7} → W-oriented (FEN4 spec ``Pw`` / ``pw``)

  Piece counts:

    White: (|W_only| + |C|) × 16 = 28 × 16 = 448
    Black: (|B_only| + |C|) × 16 = 28 × 16 = 448
    Total: 896 pieces, including 28 kings per side.

The piece counts and slice cardinalities are guarded by immolation
tests in ``tests/test_initial_position_4d.py``; if you regenerate
the layout, run those tests before pushing.
"""
from __future__ import annotations

from typing import Dict, FrozenSet, Tuple

from chess_spectral import fen_4d as _fen_4d
from chess_spectral_4d.move_history import (
    GameState4D, SIDE_WHITE, coord_to_sq,
)


__all__ = [
    "STARTING_FEN4",
    "initial_position",
    "central_slices",
    "white_only_slices",
    "black_only_slices",
    "empty_slices",
    "WHITE_BACK_RANK",
    "BLACK_BACK_RANK",
]


# ─── Slice classification ───────────────────────────────────────────


def _slice_set(
    z_range, w_range,
) -> FrozenSet[Tuple[int, int]]:
    return frozenset((z, w) for z in z_range for w in w_range)


def central_slices() -> FrozenSet[Tuple[int, int]]:
    """The 4 slices where both colors are placed at the 2D-standard
    starting array. Paper §3.3 set ``C``."""
    return _slice_set(range(3, 5), range(3, 5))


def white_only_slices() -> FrozenSet[Tuple[int, int]]:
    """The 24 slices where only white pieces sit at the 2D-standard
    starting array. Paper §3.3 set ``W_only``."""
    return _slice_set(range(0, 3), range(0, 4)) | \
        _slice_set(range(5, 8), range(4, 8))


def black_only_slices() -> FrozenSet[Tuple[int, int]]:
    """The 24 slices where only black pieces sit at the 2D-standard
    starting array. Paper §3.3 set ``B_only``."""
    return _slice_set(range(0, 3), range(4, 8)) | \
        _slice_set(range(5, 8), range(0, 4))


def empty_slices() -> FrozenSet[Tuple[int, int]]:
    """The 12 slices that start with no pieces at all. Paper §3.3
    set ``E``."""
    return _slice_set(range(3, 5), [0, 1, 2, 5, 6, 7])


# ─── 2D back-rank arrays ─────────────────────────────────────────────


# x=0..7 indexed back-rank pieces. Standard chess starting layout.
WHITE_BACK_RANK: Tuple[str, ...] = (
    "R", "N", "B", "Q", "K", "B", "N", "R",
)
BLACK_BACK_RANK: Tuple[str, ...] = (
    "r", "n", "b", "q", "k", "b", "n", "r",
)


def _pawn_axis_for_x(x: int) -> str:
    """Per paper Definition 11: even x → Y-oriented, odd x → W-oriented."""
    return "y" if (x % 2 == 0) else "w"


# ─── Programmatic layout construction ───────────────────────────────


def _build_position() -> Dict[int, "_fen_4d.PieceValue"]:
    """Construct the canonical Oana-Chiru §3.3 starting position as a
    {sq_idx: piece_value} dict — the same shape ``encoder_4d.encode_4d``
    consumes and that ``GameState4D.position`` stores."""
    pos: Dict[int, _fen_4d.PieceValue] = {}

    white_slices = central_slices() | white_only_slices()
    black_slices = central_slices() | black_only_slices()

    for (z, w) in white_slices:
        # White back rank (y=0).
        for x, piece in enumerate(WHITE_BACK_RANK):
            pos[coord_to_sq((x, 0, z, w))] = piece
        # White pawn rank (y=1) with axis-by-x rule.
        for x in range(8):
            axis = _pawn_axis_for_x(x)
            pos[coord_to_sq((x, 1, z, w))] = ("P", axis)

    for (z, w) in black_slices:
        # Black back rank (y=7).
        for x, piece in enumerate(BLACK_BACK_RANK):
            pos[coord_to_sq((x, 7, z, w))] = piece
        # Black pawn rank (y=6) with axis-by-x rule.
        for x in range(8):
            axis = _pawn_axis_for_x(x)
            pos[coord_to_sq((x, 6, z, w))] = ("p", axis)

    return pos


# Materialize the canonical FEN4 string at module-import time so it
# can be referenced as a constant. ``fen_4d.serialize`` sorts pieces
# by ascending square index, so the string is byte-stable across
# Python versions / platforms.
STARTING_FEN4: str = _fen_4d.serialize(_build_position())
"""Canonical 4D initial-position FEN4 v1 placement literal.

Stable across Python versions and platforms — the underlying
``fen_4d.serialize`` sorts pieces by ascending square index. Use
this as the definitive ``GameState4D.from_fen(STARTING_FEN4)``
input or compare future fixture FEN4s against this for parity
checks.

896 pieces total: 448 white + 448 black, 28 kings per side. Built
from the §3.3 partition of (z, w) slices into central (4) +
white-only (24) + black-only (24) + empty (12) = 64 slices, with
the standard 2D starting array placed on each non-empty slice and
pawn axis assigned by file (even x → Y-oriented, odd x → W-
oriented per Definition 11).
"""


# ─── Public factory ────────────────────────────────────────────────


def initial_position() -> GameState4D:
    """Construct a fresh :class:`GameState4D` at the canonical 4D
    Oana-Chiru starting position (paper §3.3).

    Side-to-move defaults to ``SIDE_WHITE``, matching FIDE Article
    4.7. Move history is empty (``state.history.moves == []``);
    ``state.history.initial_fen4`` is set to :data:`STARTING_FEN4`
    so :meth:`GameState4D.pop` can rewind the very first ply.

    Equivalent to ``GameState4D.from_fen(STARTING_FEN4)`` — the
    factory exists for ergonomics (``initial_position()`` reads
    cleaner in consumer code than referencing a top-level constant)
    and so the 4D engine / chess4D-OC visualizer can drop their
    hand-rolled fixture-loading shims.

    Returns
    -------
    GameState4D
        A fresh game state with 448 white + 448 black pieces, 28
        kings per side, white to move.
    """
    return GameState4D.from_fen(STARTING_FEN4, side_to_move=SIDE_WHITE)

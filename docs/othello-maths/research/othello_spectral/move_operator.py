"""Move-type phase operators — chess-style per-move-class operators
using the faithful sheaf to determine bracket flips.

Design
------
In chess-spectral, P_rook, P_bishop, P_pawn etc. are unitary /
linear operators on the encoding space that implement per-move-
class transformations.  Chess has piece-species-indexed move
operators; Othello has a single disc type so the natural axis is
"which cell you place at", giving 64 placement operators plus one
pass:

    P_place_i(state, side)   for i in 0..63
    P_pass(state, side)

The sheaf coupling: placing a friendly at cell ``i`` flips every
opponent run bracketed by existing friendlies along each of the 8
rays from ``i``.  Classifying each direction with the faithful-
sheaf bracket walker (``faithful_sheaf.classify_ray``) tells us
exactly which cells flip.  The post-move state is deterministic.

API
---
  SheafMoveOperator.is_legal(state, move, side) -> bool
  SheafMoveOperator.flip_count(state, move, side) -> int
  SheafMoveOperator.flipped_cells(state, move, side) -> list[int]
  SheafMoveOperator.apply(state, move, side) -> state'  (post-move)
  SheafMoveOperator.encode_post_move(state, move, side, *, encode_fn)
      -> encoded_post_move  (None if illegal)

The operator never mutates the input state.  Parity test
[tests/test_move_operator.py] asserts byte-for-byte agreement with
``othello_utils.OthelloBoard.play()`` across random samples.
"""

from __future__ import annotations

from typing import Optional

import numpy as np

_PACKAGE_DIR = None  # filled lazily at first call


def _load_deps():
    """Import faithful_sheaf + othello_utils lazily."""
    import sys
    from pathlib import Path
    research_dir = Path(__file__).resolve().parent.parent
    if str(research_dir) not in sys.path:
        sys.path.insert(0, str(research_dir))
    from faithful_sheaf import classify_ray, R2_COMPLETE
    from othello_utils import BLACK, RAY_OFFSETS
    return classify_ray, R2_COMPLETE, BLACK, RAY_OFFSETS


def _forward_check_ray(
    state: np.ndarray, cell: int, side: int,
    dr: int, dc: int,
    classify_ray_fn, R2_COMPLETE,
) -> list[int]:
    """Return the opponent cells that WOULD flip if ``side`` places
    a disc at ``cell`` and walks direction (dr, dc).  Empty list
    if placement does not flank in this direction.

    Implementation: temporarily set state[cell] = side, run the
    classifier, restore.  We never mutate the caller's array."""
    scratch = state.copy()
    scratch[cell] = side
    cls, opp = classify_ray_fn(scratch, cell, dr, dc)
    if cls == R2_COMPLETE:
        return list(opp)
    return []


class SheafMoveOperator:
    """Per-cell placement operators using the faithful sheaf's
    bracket classifier to determine flipped cells."""

    def __init__(self):
        (self._classify_ray, self._R2_COMPLETE,
         self._BLACK, self._RAY_OFFSETS) = _load_deps()

    # -- legality + flip enumeration --------------------------------

    def flipped_cells(
        self, state: np.ndarray, move: int, side: int,
    ) -> list[int]:
        """Return the list of opponent cells that flip when ``side``
        places at ``move``.  Empty if the move is not a valid flank."""
        state_int = np.asarray(state, dtype=int)
        if not 0 <= move < 64:
            raise ValueError(f"move out of range: {move}")
        if int(state_int[move]) != 0:
            return []  # target cell already occupied — illegal
        flipped: list[int] = []
        for _, (dr, dc) in self._RAY_OFFSETS.items():
            flipped.extend(_forward_check_ray(
                state_int, move, side, dr, dc,
                self._classify_ray, self._R2_COMPLETE,
            ))
        return flipped

    def is_legal(
        self, state: np.ndarray, move: int, side: int,
    ) -> bool:
        """True iff at least one direction yields a valid flank."""
        return len(self.flipped_cells(state, move, side)) > 0

    def flip_count(
        self, state: np.ndarray, move: int, side: int,
    ) -> int:
        return len(self.flipped_cells(state, move, side))

    # -- application -----------------------------------------------

    def apply(
        self, state: np.ndarray, move: int, side: int,
    ) -> Optional[np.ndarray]:
        """Return the post-move state, or None if ``move`` is illegal.
        Does not mutate ``state``."""
        flipped = self.flipped_cells(state, move, side)
        if not flipped:
            return None
        post = np.asarray(state, dtype=int).copy()
        post[move] = side
        for c in flipped:
            post[c] = side
        return post

    def encode_post_move(
        self, state: np.ndarray, move: int, side: int,
        encode_fn=None,
    ) -> Optional[np.ndarray]:
        """Encode the post-move state via ``encode_fn``.  Defaults to
        the v0.3.0 sheaf-fiber encoder."""
        if encode_fn is None:
            from .encoder import encode_768
            encode_fn = encode_768
        post = self.apply(state, move, side)
        if post is None:
            return None
        return encode_fn(post)

    # -- batch / introspection -------------------------------------

    def legal_moves(
        self, state: np.ndarray, side: int,
    ) -> list[int]:
        """All legal moves from ``state`` for ``side``."""
        return [
            m for m in range(64)
            if self.is_legal(state, m, side)
        ]

    def flip_count_vector(
        self, state: np.ndarray, side: int,
    ) -> np.ndarray:
        """64-dim vector; entry i is the flip count for move i
        (0 if illegal).  Useful as a state descriptor channel."""
        out = np.zeros(64, dtype=np.float64)
        for m in range(64):
            out[m] = self.flip_count(state, m, side)
        return out


__all__ = ["SheafMoveOperator"]

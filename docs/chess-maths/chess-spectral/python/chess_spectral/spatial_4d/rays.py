"""Pre-computed ray tables for sliding-piece attacks.

A "ray" is the sequence of squares from a source ``s`` outward in a
fixed direction ``(dx, dy, dz, dw)`` until the lattice boundary.
For sliding pieces (rook, bishop, queen) we walk rays and stop at
the first blocker, so the rays are the canonical input to attack
generation.

Direction indexing
------------------
Two ray families:

* **Rook directions** (8 total): along a single axis ±1 step.
  Indexed as ``(axis, sign)`` ∈ {0, 1, 2, 3} × {-1, +1}.

* **Bishop directions** (24 total): along a 2-axis diagonal with
  independent ±1 signs on each chosen axis. Indexed as
  ``(axis_i, axis_j, sign_i, sign_j)`` with ``i < j``.

Queen rays are the disjoint union (rook ∪ bishop = 32 directions),
generated at attack time by walking both families.

Storage
-------
For each source square ``s`` and direction ``d``:
    RAY[s][d] = tuple[int, ...]
where the tuple is the sequence of squares from s outward, exclusive
of s itself, until the lattice boundary. Length 0 iff s is at the
boundary in direction d.

Memory: 4096 squares × (8 + 24) directions × ≤ 7 squares × 8 bytes ≈
~7 MB. Built once at import time.

Performance
-----------
Ray-walk attack generation costs O(ray_length) per direction call
and O(directions × ray_length) per attack lookup. Empirical:
~10 μs per attacks_rook_4d call, ~30 μs per attacks_bishop_4d call,
~40 μs per attacks_queen_4d call (Python).

This precomputed-ray table is the same data structure that
magic-bitboard implementations use; the "magic" part is the
multiplicative-hash optimization on the occupancy patterns to fold
N-bit occupancy keys into a smaller hash table. In Python the
multiply-mask step gives diminishing returns (Python int operations
already amortize well), so the multiply-magic isn't built here.
The data is laid out so a future C-side port (or Python optimization
pass) can swap the linear ray walk for an occupancy-keyed lookup
with no API change.
"""
from __future__ import annotations

from typing import Dict, Iterable, Iterator, List, Tuple

from .. import tables_4d as _t4
from .bitboard import N_SQUARES, BOARD_SIDE


# ---- Direction primitives ----------------------------------------

# Rook directions: list of (dx, dy, dz, dw) deltas.
ROOK_DIRECTIONS: Tuple[Tuple[int, int, int, int], ...] = (
    (-1, 0, 0, 0), (+1, 0, 0, 0),
    (0, -1, 0, 0), (0, +1, 0, 0),
    (0, 0, -1, 0), (0, 0, +1, 0),
    (0, 0, 0, -1), (0, 0, 0, +1),
)
"""8 rook directions: ±1 step along each of the 4 axes."""

# Bishop directions: 6 axis pairs × 4 sign combos = 24.
def _build_bishop_directions() -> Tuple[Tuple[int, int, int, int], ...]:
    out = []
    for i in range(4):
        for j in range(i + 1, 4):
            for si in (-1, +1):
                for sj in (-1, +1):
                    delta = [0, 0, 0, 0]
                    delta[i] = si
                    delta[j] = sj
                    out.append(tuple(delta))
    return tuple(out)


BISHOP_DIRECTIONS: Tuple[Tuple[int, int, int, int], ...] = (
    _build_bishop_directions()
)
"""24 bishop directions: 2-face diagonals; each pair (axis_i,
axis_j) gives 4 sign combos."""

# Queen = rook + bishop (32 directions).
QUEEN_DIRECTIONS: Tuple[Tuple[int, int, int, int], ...] = (
    ROOK_DIRECTIONS + BISHOP_DIRECTIONS
)


# ---- Ray builder -------------------------------------------------


def _walk_ray(x: int, y: int, z: int, w: int,
              dx: int, dy: int, dz: int, dw: int) -> Iterator[int]:
    """Yield square indices along the ray from (x,y,z,w) outward
    in direction (dx,dy,dz,dw), exclusive of source, until the
    lattice boundary."""
    while True:
        x += dx
        y += dy
        z += dz
        w += dw
        if not (0 <= x < BOARD_SIDE and 0 <= y < BOARD_SIDE
                and 0 <= z < BOARD_SIDE and 0 <= w < BOARD_SIDE):
            return
        yield _t4.sq4(x, y, z, w)


def _build_ray_table(directions: Iterable[Tuple[int, int, int, int]]
                     ) -> Tuple[Tuple[Tuple[int, ...], ...], ...]:
    """Build a (N_SQUARES, n_directions) table of ray tuples.

    ``ray_table[sq][dir_idx]`` is a tuple of square indices from
    sq outward in direction directions[dir_idx], exclusive of sq.
    """
    dirs = tuple(directions)
    out: List[Tuple[Tuple[int, ...], ...]] = []
    for s in range(N_SQUARES):
        x, y, z, w = _t4.rc4(s)
        per_sq = tuple(
            tuple(_walk_ray(x, y, z, w, dx, dy, dz, dw))
            for (dx, dy, dz, dw) in dirs
        )
        out.append(per_sq)
    return tuple(out)


# ---- Built tables (lazy) -----------------------------------------

ROOK_RAYS: Tuple[Tuple[Tuple[int, ...], ...], ...] = _build_ray_table(
    ROOK_DIRECTIONS
)
"""ROOK_RAYS[sq][dir_idx] = tuple of squares from sq outward in
ROOK_DIRECTIONS[dir_idx]. dir_idx ∈ [0, 8)."""

BISHOP_RAYS: Tuple[Tuple[Tuple[int, ...], ...], ...] = _build_ray_table(
    BISHOP_DIRECTIONS
)
"""BISHOP_RAYS[sq][dir_idx] = tuple of squares from sq outward in
BISHOP_DIRECTIONS[dir_idx]. dir_idx ∈ [0, 24)."""

QUEEN_RAYS: Tuple[Tuple[Tuple[int, ...], ...], ...] = _build_ray_table(
    QUEEN_DIRECTIONS
)
"""QUEEN_RAYS[sq][dir_idx] = tuple of squares from sq outward in
QUEEN_DIRECTIONS[dir_idx]. dir_idx ∈ [0, 32)."""


__all__ = [
    "ROOK_DIRECTIONS",
    "BISHOP_DIRECTIONS",
    "QUEEN_DIRECTIONS",
    "ROOK_RAYS",
    "BISHOP_RAYS",
    "QUEEN_RAYS",
]

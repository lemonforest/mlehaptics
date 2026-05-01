"""Bitboard4D -- 4096-bit set of 4D squares, the spatial_4d primitive.

The 8^4 lattice has 4096 squares; a Bitboard4D is a fixed-size set of
those, encoded as a single Python int (one bit per square). Mirrors
python-chess's :class:`chess.SquareSet` for 2D, scaled to the 4D
lattice.

Storage decision (per ADR-001 §"Core primitive: `Bitboard4D`"):
  Python int is the canonical representation. Reasons:
    * Native bitwise operators (`&`, `|`, `^`, `~`, `<<`, `>>`) work
      out of the box at arbitrary precision.
    * `int.bit_count()` (added in Python 3.10) gives O(1) popcount.
    * Equality + hashing are free.
    * Pickling / serialization is trivial.
  Numpy uint64[64] is available as an optional projection
  (:meth:`to_numpy_uint64` / :meth:`from_numpy_uint64`) for hot loops
  that benefit from SIMD-friendly storage. Same data, different shape.

Square indexing matches the rest of chess_spectral_4d: square index
``s = sq4(x, y, z, w)`` where ``s = ((x * 8 + y) * 8 + z) * 8 + w``,
with x ∈ [0, 8), y ∈ [0, 8), z ∈ [0, 8), w ∈ [0, 8). See
:func:`chess_spectral.tables_4d.sq4`.

Frozen / immutable
------------------
Bitboard4D instances are immutable (``__slots__`` with a single
``_bits`` field; mutating methods return new instances). This makes
them hashable, safe to use as dict keys, and side-effect-free in
search loops where the same operator is applied to many positions.

API summary
-----------
Construction:
  Bitboard4D(bits=0)              -- raw int constructor
  Bitboard4D.empty()              -- 4096-bit zero
  Bitboard4D.full()               -- 4096-bit one
  Bitboard4D.from_squares(iter)   -- from an iterable of square indices
  Bitboard4D.from_square(sq)      -- single-square set
  Bitboard4D.from_numpy_uint64(a) -- from a (64,) uint64 array
  Bitboard4D.axis_plane(axis, k)  -- the 512 squares on plane axis = k

Bitwise:
  bb1 | bb2, bb1 & bb2, bb1 ^ bb2, ~bb1
  bb1 - bb2  (== bb1 & ~bb2; set difference)

Tests:
  bb.is_empty(), bb.is_full(), bb.popcount(), len(bb)
  bb.intersects(other), bb.is_subset(other), bb.is_disjoint(other)
  sq in bb  (single-square membership)

Mutation (return new):
  bb.set_square(sq), bb.clear_square(sq), bb.toggle_square(sq)

Geometric:
  bb.shift_axis(axis, delta)   -- shift along axis, clipped at lattice
                                 boundary (no wraparound)

Iteration:
  bb.squares() -> Iterator[int]    -- ascending sq indices
  bb.to_squares() -> list[int]
  list(bb) -> list[int]

Equality / hashing:
  Bitboard4D is hashable (frozen via __slots__). bb1 == bb2 compares
  the bit content; hash(bb) == hash(bits).

Numpy interop:
  bb.to_numpy_uint64() -> np.ndarray (64,) uint64
  Bitboard4D.from_numpy_uint64(arr) -> Bitboard4D
"""
from __future__ import annotations

from typing import Iterable, Iterator, List

import numpy as np

# 1.7.0 D2 M2.1: optional native fast-path. The module always imports,
# even if the C library isn't present; ``HAS_NATIVE_BITBOARD`` reports
# whether the fast-path is actually wired. Method-level integration
# (popcount, bitwise ops via native) lands in M2.2; M2.1 is just the
# foundation: build hookup + ctypes wrapper + the flag.
try:
    from chess_spectral._native_bitboard4d import HAS_NATIVE as HAS_NATIVE_BITBOARD
except ImportError:  # pragma: no cover - belt-and-suspenders
    HAS_NATIVE_BITBOARD = False


# Lattice geometry constants (mirror tables_4d).
BOARD_SIDE: int = 8
N_DIMENSIONS: int = 4
N_SQUARES: int = BOARD_SIDE ** N_DIMENSIONS   # 4096
ALL_BITS_MASK: int = (1 << N_SQUARES) - 1     # 4096-bit one


# Axis indexing convention. Matches sq4(x, y, z, w):
#   bit_index = ((x * 8 + y) * 8 + z) * 8 + w
# So shifting along axis 0 (x) by +1 means moving by 8^3 = 512 bit
# positions; axis 1 (y) by 8^2 = 64; axis 2 (z) by 8; axis 3 (w) by 1.
_AXIS_STRIDE = (
    BOARD_SIDE ** 3,  # x: stride 512
    BOARD_SIDE ** 2,  # y: stride 64
    BOARD_SIDE ** 1,  # z: stride 8
    BOARD_SIDE ** 0,  # w: stride 1
)


def _build_axis_plane_masks() -> tuple[tuple[int, ...], ...]:
    """Return ``masks[axis][k]`` = bitmask of all squares with
    coord[axis] == k. 4 axes × 8 values = 32 masks of 4096 bits each.

    Used by axis_plane(), shift_axis() boundary clipping, and any
    "all squares on plane x=k" query in higher-level code.
    """
    masks: list[list[int]] = [[0] * BOARD_SIDE for _ in range(N_DIMENSIONS)]
    for s in range(N_SQUARES):
        # Decompose s back into (x, y, z, w) -- inverse of sq4.
        w = s % BOARD_SIDE
        z = (s // BOARD_SIDE) % BOARD_SIDE
        y = (s // BOARD_SIDE ** 2) % BOARD_SIDE
        x = s // BOARD_SIDE ** 3
        bit = 1 << s
        masks[0][x] |= bit
        masks[1][y] |= bit
        masks[2][z] |= bit
        masks[3][w] |= bit
    return tuple(tuple(plane) for plane in masks)


_AXIS_PLANE_MASKS: tuple[tuple[int, ...], ...] = _build_axis_plane_masks()


def _validate_axis(axis: int) -> int:
    if not 0 <= axis < N_DIMENSIONS:
        raise ValueError(
            f"axis {axis} out of range [0, {N_DIMENSIONS}); valid axes "
            f"are 0=x, 1=y, 2=z, 3=w"
        )
    return axis


def _validate_square(sq: int) -> int:
    if not 0 <= sq < N_SQUARES:
        raise ValueError(
            f"square {sq} out of range [0, {N_SQUARES})"
        )
    return sq


class Bitboard4D:
    """4096-bit set of 4D squares.

    See module docstring for the full API surface and design
    rationale.
    """

    __slots__ = ("_bits",)

    _bits: int

    # ---- Construction -----------------------------------------------

    def __init__(self, bits: int = 0):
        # Mask off any high bits accidentally set above N_SQUARES.
        # This makes the constructor tolerant of e.g. ``~Bitboard4D(0)``
        # (where Python's int.__invert__ returns -1 ≡ ...111).
        if bits < 0:
            # Two's complement: ~b = -(b+1) on Python ints. Mask to
            # 4096 bits.
            object.__setattr__(self, "_bits", (~(-bits - 1)) & ALL_BITS_MASK)
        else:
            object.__setattr__(self, "_bits", bits & ALL_BITS_MASK)

    @classmethod
    def empty(cls) -> "Bitboard4D":
        return cls(0)

    @classmethod
    def full(cls) -> "Bitboard4D":
        return cls(ALL_BITS_MASK)

    @classmethod
    def from_squares(cls, squares: Iterable[int]) -> "Bitboard4D":
        bits = 0
        for sq in squares:
            _validate_square(sq)
            bits |= 1 << sq
        return cls(bits)

    @classmethod
    def from_square(cls, sq: int) -> "Bitboard4D":
        _validate_square(sq)
        return cls(1 << sq)

    @classmethod
    def axis_plane(cls, axis: int, k: int) -> "Bitboard4D":
        """The 512 squares on the hyperplane coord[axis] == k."""
        _validate_axis(axis)
        if not 0 <= k < BOARD_SIDE:
            raise ValueError(
                f"plane index k={k} out of range [0, {BOARD_SIDE})"
            )
        return cls(_AXIS_PLANE_MASKS[axis][k])

    @classmethod
    def from_numpy_uint64(cls, arr: np.ndarray) -> "Bitboard4D":
        """Reconstruct from a (64,) uint64 array. Inverse of
        :meth:`to_numpy_uint64`."""
        if arr.shape != (64,):
            raise ValueError(
                f"expected shape (64,), got {arr.shape}"
            )
        if arr.dtype != np.uint64:
            raise ValueError(
                f"expected dtype uint64, got {arr.dtype}"
            )
        # Reassemble 64 × 64-bit chunks into a single 4096-bit int.
        # arr[k] holds bits [k*64 : (k+1)*64).
        bits = 0
        for k in range(64):
            bits |= int(arr[k]) << (k * 64)
        return cls(bits)

    # ---- Bitwise operators -----------------------------------------

    def __or__(self, other: "Bitboard4D") -> "Bitboard4D":
        if not isinstance(other, Bitboard4D):
            return NotImplemented
        return Bitboard4D(self._bits | other._bits)

    def __and__(self, other: "Bitboard4D") -> "Bitboard4D":
        if not isinstance(other, Bitboard4D):
            return NotImplemented
        return Bitboard4D(self._bits & other._bits)

    def __xor__(self, other: "Bitboard4D") -> "Bitboard4D":
        if not isinstance(other, Bitboard4D):
            return NotImplemented
        return Bitboard4D(self._bits ^ other._bits)

    def __sub__(self, other: "Bitboard4D") -> "Bitboard4D":
        """Set difference: self & ~other."""
        if not isinstance(other, Bitboard4D):
            return NotImplemented
        return Bitboard4D(self._bits & ~other._bits & ALL_BITS_MASK)

    def __invert__(self) -> "Bitboard4D":
        return Bitboard4D((~self._bits) & ALL_BITS_MASK)

    # ---- Predicate / membership ------------------------------------

    def __bool__(self) -> bool:
        return self._bits != 0

    def __len__(self) -> int:
        """Population count (number of set bits)."""
        return self._bits.bit_count()

    def popcount(self) -> int:
        """Alias for ``len(self)``. Number of set squares."""
        return self._bits.bit_count()

    def is_empty(self) -> bool:
        return self._bits == 0

    def is_full(self) -> bool:
        return self._bits == ALL_BITS_MASK

    def __contains__(self, sq: int) -> bool:
        """``sq in bb`` -- True iff square sq is set."""
        if not isinstance(sq, int):
            return False
        if not 0 <= sq < N_SQUARES:
            return False
        return bool(self._bits & (1 << sq))

    def intersects(self, other: "Bitboard4D") -> bool:
        return bool(self._bits & other._bits)

    def is_subset(self, other: "Bitboard4D") -> bool:
        return (self._bits & ~other._bits) == 0

    def is_disjoint(self, other: "Bitboard4D") -> bool:
        return (self._bits & other._bits) == 0

    # ---- Mutation (return new) -------------------------------------

    def set_square(self, sq: int) -> "Bitboard4D":
        _validate_square(sq)
        return Bitboard4D(self._bits | (1 << sq))

    def clear_square(self, sq: int) -> "Bitboard4D":
        _validate_square(sq)
        return Bitboard4D(self._bits & ~(1 << sq))

    def toggle_square(self, sq: int) -> "Bitboard4D":
        _validate_square(sq)
        return Bitboard4D(self._bits ^ (1 << sq))

    # ---- Geometric ops --------------------------------------------

    def shift_axis(self, axis: int, delta: int) -> "Bitboard4D":
        """Shift all set squares by ``delta`` along the given axis.

        Squares that would shift past the lattice boundary are
        dropped (no wraparound). E.g., shifting ``axis_plane(0, 7)``
        by ``+1`` along axis 0 yields the empty bitboard.

        Parameters
        ----------
        axis : int
            Axis index 0 (x), 1 (y), 2 (z), or 3 (w).
        delta : int
            Shift amount (any signed integer). |delta| >= 8 yields
            an empty result (everything shifts off the lattice).

        Returns
        -------
        Bitboard4D with shifted squares, lattice-clipped.
        """
        _validate_axis(axis)
        if delta == 0 or self._bits == 0:
            return self if delta == 0 else Bitboard4D(0)
        if abs(delta) >= BOARD_SIDE:
            return Bitboard4D(0)

        stride = _AXIS_STRIDE[axis]

        # Build the "valid source planes" mask: squares whose target
        # is still on the lattice. If shifting by +delta along axis a,
        # source square coord[a] must be in [0, 8 - delta) (so target
        # coord stays < 8). If delta < 0, source must be in [-delta, 8).
        if delta > 0:
            valid_source_planes = range(0, BOARD_SIDE - delta)
        else:
            valid_source_planes = range(-delta, BOARD_SIDE)

        valid_mask = 0
        for k in valid_source_planes:
            valid_mask |= _AXIS_PLANE_MASKS[axis][k]

        # Mask the source bitboard, then shift bit-positions by
        # delta * stride.
        src = self._bits & valid_mask
        if src == 0:
            return Bitboard4D(0)
        if delta > 0:
            shifted = src << (delta * stride)
        else:
            shifted = src >> (-delta * stride)
        return Bitboard4D(shifted & ALL_BITS_MASK)

    # ---- Iteration -------------------------------------------------

    def squares(self) -> Iterator[int]:
        """Yield set square indices in ascending order.

        Uses ``int.bit_length()`` and lowest-set-bit isolation
        (``b & -b``) for O(popcount) iteration. Faster than
        ``[s for s in range(4096) if self._bits & (1 << s)]``.
        """
        b = self._bits
        while b:
            lsb = b & -b           # isolate lowest set bit
            yield lsb.bit_length() - 1
            b &= b - 1             # clear lowest set bit

    def to_squares(self) -> List[int]:
        return list(self.squares())

    def __iter__(self) -> Iterator[int]:
        return self.squares()

    # ---- Numpy interop --------------------------------------------

    def to_numpy_uint64(self) -> np.ndarray:
        """Project to a (64,) uint64 array.

        ``arr[k]`` holds bits ``[k*64 : (k+1)*64)`` of the bitboard.
        Provides SIMD-friendly storage for hot loops in the
        magic-bitboard attack tables (PR-7-D).

        Inverse: :meth:`from_numpy_uint64`.
        """
        out = np.empty(64, dtype=np.uint64)
        b = self._bits
        mask64 = (1 << 64) - 1
        for k in range(64):
            out[k] = (b >> (k * 64)) & mask64
        return out

    # ---- Equality / hashing ---------------------------------------

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Bitboard4D):
            return NotImplemented
        return self._bits == other._bits

    def __ne__(self, other: object) -> bool:
        result = self.__eq__(other)
        return result if result is NotImplemented else not result

    def __hash__(self) -> int:
        return hash(self._bits)

    # ---- Repr -----------------------------------------------------

    def __repr__(self) -> str:
        n = self.popcount()
        if n == 0:
            return "Bitboard4D.empty()"
        if n == N_SQUARES:
            return "Bitboard4D.full()"
        if n <= 6:
            return f"Bitboard4D.from_squares({sorted(self.to_squares())})"
        return f"Bitboard4D(<popcount={n}>)"

    # ---- Internal accessor (for tests / hot loops only) -----------

    @property
    def bits(self) -> int:
        """Raw 4096-bit Python int. Read-only."""
        return self._bits


__all__ = [
    "Bitboard4D",
    "BOARD_SIDE",
    "N_DIMENSIONS",
    "N_SQUARES",
    "ALL_BITS_MASK",
]

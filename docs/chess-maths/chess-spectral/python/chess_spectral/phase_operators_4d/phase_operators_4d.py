"""4D phase operators on Z_145451 per PHASE_OPERATOR_SUPPLEMENT_4D §13.

Pinned design (Phase A original + Phase B refinement):

    MODULUS_4D = 145451   # prime; > 7*sum + max_bishop_shift
    GEN_X = 9719          # x-axis (slowest-varying in sq4 layout)
    GEN_Y =  647          # y-axis
    GEN_Z =   43          # z-axis
    GEN_W =    3          # w-axis (fastest-varying in sq4 layout)

    phi(x,y,z,w) = (x*GEN_X + y*GEN_Y + z*GEN_Z + w*GEN_W) % MODULUS_4D

**Phase B refinement story.** Phase A's first attempt used
(MODULUS_4D, GEN_X, GEN_Y, GEN_Z, GEN_W) = (12181, 1523, 191, 23, 3),
constructed via a mixed-radix tower with ladder coefficient 7 (the
[-7, 7]^4 origin-bijection bound). That tuple passed all four Phase A
constraints (C1 coprime, C2 image bijection, C3 non-subgroup, C4
within-piece distinctness + knight-disjoint). But Phase B's
structural gate (4096 origins × N piece configs against
``tables_4d.X_targets``) failed at every piece config — the rook
operator's destination set included bishop-plane-diagonal squares
when wraparound aliasing fired.

Root cause: the ladder coefficient 7 is the bound for ORIGIN
bijection on [0,7]^4. Operator shifts have components in [-7, 7],
so DIFFERENCES between two operator-emitted shifts span [-14, 14]
per component. An integer dependency Σ Δ·g = 0 with Δ ∈ [-14, 14]^4
shows up as cross-piece destination aliasing.

Concrete failure at the original (1523, 191, 23, 3): the identity
g_y = 10·g_w + 7·g_z (literally 191 = 30 + 161) gives
Δ = (0, +1, -7, -10), Σ Δ·g = 0, with Δ_w = -10 ∈ [-14, 14].
Operationally: a rook +7·g_w shift (intended +7 along w) from origin
(0, 0, 7, 3) inverted to lattice point (0, 1, 0, 0) — a non-rook
destination — because phi(0, 0, 7, 3) + 7·g_w = phi(0, 1, 0, 0) by
exactly that identity.

**The Phase B fix.** Widen the mixed-radix ladder coefficient from 7
to 14, and verify by brute-force enumeration over [-14, 14]^4 that
no nonzero Δ has Σ Δ·g = 0. The construction:

    g_w = 3                          # smallest admissible prime
    g_z = next_prime(14*g_w + 1)     # = 43      (was 23 with c=7)
    g_y = next_prime(14*(g_w+g_z)+1) # = 647     (was 191)
    g_x = next_prime(14*(...)+1)     # = 9719    (was 1523)
    sum = 10412                      # (was 1740)
    M   = 7*sum + 7*(g_x+g_y) + 1 = 145451 prime  (was 12181)

This guarantees |Σ Δ·g| < 14·sum < M for any Δ ∈ [-14, 14]^4 — the
modular reduction is a no-op, and integer linear independence of the
distinct primes (now in a strict mixed-radix tower at coefficient
14) forces all Δ_i = 0.

The 2D supplement uses (g_x=67, g_y=7) on Z_640 with 8*7 = 56 < 67,
which corresponds to a ladder coefficient of 8 — fine for 2D where
operator shifts are smaller in absolute terms, but 4D's 4-axis
mixing requires the full [-14, 14] discipline. Both designs are the
same construction at different scales.

This module is pure-stdlib arithmetic. Phase B's piece operators
will live in a sibling file and import these constants. Phase B's
[phase_to_coords_4d.py] will provide the inverse map and
[phase_set_to_board].
"""

from __future__ import annotations

# ─── pinned design constants ────────────────────────────────────────

from typing import Literal

MODULUS_4D: int = 145451
GEN_X: int = 9719
GEN_Y: int = 647
GEN_Z: int = 43
GEN_W: int = 3

# Per-axis generators as a tuple, indexed by axis ∈ {0=x, 1=y, 2=z,
# 3=w}. Convenient for axis-parametric loops in the operators below.
AXIS_GENS: tuple[int, int, int, int] = (GEN_X, GEN_Y, GEN_Z, GEN_W)


# ─── derived shift sets (precomputed at import time) ────────────────
#
# Mirror the construction in the Phase A research script. We
# precompute them once so each operator call is a fast set
# materialization rather than a re-derivation. The values are
# **direction primitives**, not full reach — the slider operators
# (P_rook4, P_bishop4, P_queen4) extend them by k ∈ {1..7}, and the
# leaper operators (P_king4, P_knight4) use them at k=1 directly.

# 8 axis primitives: ±g_i for each axis. (rook/king both use these.)
AXIS_SHIFTS: tuple[int, ...] = tuple(
    (sign * g) % MODULUS_4D
    for g in AXIS_GENS
    for sign in (-1, +1)
)

# 24 plane-diagonal primitives: ±g_i ± g_j for i < j (6 pairs × 4
# sign combos). (bishop/king both use these as direction seeds.)
PLANE_DIAG_SHIFTS: tuple[int, ...] = tuple(
    (si * AXIS_GENS[i] + sj * AXIS_GENS[j]) % MODULUS_4D
    for i in range(4)
    for j in range(i + 1, 4)
    for si in (-1, +1)
    for sj in (-1, +1)
)

# 48 knight shifts: ±2·g_i ± g_j for i ≠ j (12 ordered pairs × 4
# sign combos). Knight is a leaper — these shifts are used at k=1
# only (no extension).
KNIGHT_SHIFTS: tuple[int, ...] = tuple(
    (s2 * AXIS_GENS[i] + s1 * AXIS_GENS[j]) % MODULUS_4D
    for i in range(4)
    for j in range(4)
    if i != j
    for s2 in (-2, +2)
    for s1 in (-1, +1)
)


def _build_king_shifts() -> tuple[int, ...]:
    """80 king shifts: Σ ε_i · g_i for ε ∈ {-1, 0, +1}^4 \\ {0}.

    By construction, ``AXIS_SHIFTS`` (ε weight 1) and
    ``PLANE_DIAG_SHIFTS`` (ε weight 2) are subsets of this set.
    """
    out = []
    for ex in (-1, 0, +1):
        for ey in (-1, 0, +1):
            for ez in (-1, 0, +1):
                for ew in (-1, 0, +1):
                    if (ex, ey, ez, ew) == (0, 0, 0, 0):
                        continue
                    s = (ex * GEN_X + ey * GEN_Y
                         + ez * GEN_Z + ew * GEN_W)
                    out.append(s % MODULUS_4D)
    return tuple(out)


KING_SHIFTS: tuple[int, ...] = _build_king_shifts()


__all__ = [
    # design constants
    "MODULUS_4D", "GEN_X", "GEN_Y", "GEN_Z", "GEN_W", "AXIS_GENS",
    # exposed shift constants
    "AXIS_SHIFTS", "PLANE_DIAG_SHIFTS", "KNIGHT_SHIFTS", "KING_SHIFTS",
    # phase map
    "phi4",
    # piece operators
    "P_rook4", "P_bishop4", "P_queen4", "P_king4", "P_knight4",
    "P_pawn4_white", "P_pawn4_black",
    # pawn axis literal
    "PawnAxis",
]


# ─── coordinate-to-phase map ────────────────────────────────────────


def phi4(x: int, y: int, z: int, w: int) -> int:
    """Map a lattice coordinate (x, y, z, w) ∈ [0, 7]^4 to its phase
    in Z_MODULUS_4D.

    Bijective on [0, 7]^4 by construction (mixed-radix tower
    guarantees no Diophantine collision; verified by
    test_phase_4d_design.test_c2_image_is_4096_distinct_residues).
    """
    return (x * GEN_X + y * GEN_Y + z * GEN_Z + w * GEN_W) % MODULUS_4D


# ─── piece operators (unobstructed phase reach) ─────────────────────
#
# Every operator returns a ``frozenset[int]`` of phase values in
# [0, MODULUS_4D), excluding the origin. Destinations that fall
# outside the 4096-square board image are handled downstream by
# ``phase_to_coords_4d.invert`` — boundary clipping is not this
# module's concern.
#
# These produce the **unobstructed** reach. Occupation-aware
# truncation (Phase C) and check filtering (Phase D) live in
# sibling modules.


def P_rook4(origin_phi: int) -> frozenset[int]:
    """4D rook: slide along any single axis. 4 axes × 2 signs × 7
    distances = 56 phase shifts (some land off-board; inversion
    drops them). Per O&C section 3, interior rook reaches 28
    destinations on Z_8^4."""
    out: set[int] = set()
    for g in AXIS_GENS:
        for k in range(1, 8):
            out.add((origin_phi + k * g) % MODULUS_4D)
            out.add((origin_phi - k * g) % MODULUS_4D)
    return frozenset(out)


def P_bishop4(origin_phi: int) -> frozenset[int]:
    """4D bishop: slide along any 2-face diagonal. 6 plane choices ×
    4 sign combos × 7 distances = 168 phase shifts. The 4D bishop's
    parity-partition into 2 connected components (matches
    ``tables_4d.bishop4_targets``) emerges from the inversion step
    rather than the phase generator."""
    out: set[int] = set()
    for i in range(4):
        for j in range(i + 1, 4):
            gi, gj = AXIS_GENS[i], AXIS_GENS[j]
            for si in (-1, +1):
                for sj in (-1, +1):
                    step = si * gi + sj * gj
                    for k in range(1, 8):
                        out.add((origin_phi + k * step) % MODULUS_4D)
    return frozenset(out)


def P_queen4(origin_phi: int) -> frozenset[int]:
    """4D queen: rook ∪ bishop. Up to 56 + 168 = 224 phase shifts.
    Disjoint by construction (rook moves along single axes; bishop
    along plane diagonals — no overlap of direction sets)."""
    return P_rook4(origin_phi) | P_bishop4(origin_phi)


def P_king4(origin_phi: int) -> frozenset[int]:
    """4D king: Chebyshev-1. 80 directional shifts (3⁴ - 1 ternary
    sign vectors over the 4 axes), used at k=1. Per O&C section 3,
    interior king reaches 80 destinations."""
    return frozenset(
        (origin_phi + s) % MODULUS_4D for s in KING_SHIFTS
    )


def P_knight4(origin_phi: int) -> frozenset[int]:
    """4D knight: (2,1)-leaper. 48 shifts (12 ordered axis pairs × 4
    sign combos), used at k=1. Per O&C section 3, interior knight
    reaches 48 destinations."""
    return frozenset(
        (origin_phi + s) % MODULUS_4D for s in KNIGHT_SHIFTS
    )


# ─── pawn operators ─────────────────────────────────────────────────
#
# Per O&C Definition 11, pawns are oriented along the W axis OR the
# Y axis, never Z (and X is the rank-of-ranks axis, not used for
# pawn direction). The two-axis machinery is already reflected in
# the encoder's W-anti / Y-anti channel split (see encoder_4d.py).
#
# v1 (Phase B): forward push only, plus optional double-push from
# the starting rank. Diagonal capture geometry is deferred to
# Phase E (per the tables_4d.py:154-159 punt — O&C's exact rule
# needs to be pinned down). For now ``include_captures=True``
# raises NotImplementedError so the failure mode is loud, not
# silent.

PawnAxis = Literal["w", "y"]
"""Pawn orientation axis. Per O&C Definition 11, pawns are W- or
Y-oriented; never Z-oriented. X is the rank-of-ranks axis."""


def _pawn_axis_gen(axis: PawnAxis) -> int:
    if axis == "w":
        return GEN_W
    if axis == "y":
        return GEN_Y
    raise ValueError(
        f"pawn axis must be 'w' or 'y' (per O&C Def 11); got {axis!r}"
    )


def P_pawn4_white(
    origin_phi: int,
    *,
    axis: PawnAxis,
    on_starting_rank: bool,
    include_captures: bool,
) -> frozenset[int]:
    """4D white pawn. Forward push along ``axis`` (one square); plus
    a two-square push when on the starting rank. White pushes in
    the +axis direction.

    Captures: not yet implemented — pinning the exact rule is the
    Phase E task. ``include_captures=True`` raises
    NotImplementedError so the failure mode is loud, not silent.
    """
    g = _pawn_axis_gen(axis)
    out = {(origin_phi + g) % MODULUS_4D}
    if on_starting_rank:
        out.add((origin_phi + 2 * g) % MODULUS_4D)
    if include_captures:
        raise NotImplementedError(
            "P_pawn4_white(include_captures=True) is Phase E. "
            "See PHASE_OPERATOR_SUPPLEMENT_4D.md §13.6 for the "
            "open question on O&C Def 11 capture geometry."
        )
    return frozenset(out)


def P_pawn4_black(
    origin_phi: int,
    *,
    axis: PawnAxis,
    on_starting_rank: bool,
    include_captures: bool,
) -> frozenset[int]:
    """4D black pawn. Mirror of ``P_pawn4_white`` — pushes in the
    −axis direction.

    Captures: see ``P_pawn4_white`` for the Phase E deferral note.
    """
    g = _pawn_axis_gen(axis)
    out = {(origin_phi - g) % MODULUS_4D}
    if on_starting_rank:
        out.add((origin_phi - 2 * g) % MODULUS_4D)
    if include_captures:
        raise NotImplementedError(
            "P_pawn4_black(include_captures=True) is Phase E. "
            "See PHASE_OPERATOR_SUPPLEMENT_4D.md §13.6 for the "
            "open question on O&C Def 11 capture geometry."
        )
    return frozenset(out)

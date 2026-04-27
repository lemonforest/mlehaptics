"""4D phase operators on Z_12181 per PHASE_OPERATOR_SUPPLEMENT_4D §13.

Pinned design (Phase A, see [research/chess4d_phase_design.py]):

    MODULUS_4D = 12181     # = 7 * sum(GEN_*) + 1; coprime to all
                           #   four primes (12181 = 13 * 937)
    GEN_X = 1523           # x-axis (slowest-varying in sq4 layout)
    GEN_Y =  191           # y-axis
    GEN_Z =   23           # z-axis
    GEN_W =    3           # w-axis (fastest-varying in sq4 layout)

    phi(x,y,z,w) = (x*GEN_X + y*GEN_Y + z*GEN_Z + w*GEN_W) % MODULUS_4D

Mixed-radix tower discipline (necessary for C2 image bijection per the
Othello [Patch 2] discipline):

    GEN_X > 7 * (GEN_Y + GEN_Z + GEN_W)    # 1523 > 7*217 = 1519  ✓
    GEN_Y > 7 * (GEN_Z + GEN_W)            #  191 > 7*26  =  182  ✓
    GEN_Z > 7 * GEN_W + 1                  #   23 > 22            ✓

These bounds guarantee no nonzero (Δx, Δy, Δz, Δw) ∈ [-7,7]^4
satisfies Δx*GEN_X + Δy*GEN_Y + Δz*GEN_Z + Δw*GEN_W ≡ 0 (mod
MODULUS_4D), because |LHS| ≤ 7*1740 = 12180 < MODULUS_4D, so the
mod is a no-op and integer linear independence of distinct primes
forces all Δ's to zero.

MODULUS_4D = 12181 = 13 * 937 is composite but coprime to all four
generators; this is the smallest M such that 7*sum + 1 <= M and
gcd(M, g_i) = 1 for each axis. Using M itself prime would have
been cleaner algebraically (Z_M as a field) but 12289 is the next
prime above 12181, and 12181 is the literal smallest valid M.

This module is pure-stdlib arithmetic. Phase B's piece operators
will live in a sibling file and import these constants. Phase B's
[phase_to_coords_4d.py] will provide the inverse map and
[phase_set_to_board].
"""

from __future__ import annotations

# ─── pinned design constants ────────────────────────────────────────

MODULUS_4D: int = 12289
GEN_X: int = 1523
GEN_Y: int = 191
GEN_Z: int = 23
GEN_W: int = 3

__all__ = ["MODULUS_4D", "GEN_X", "GEN_Y", "GEN_Z", "GEN_W", "phi4"]


# ─── coordinate-to-phase map ────────────────────────────────────────


def phi4(x: int, y: int, z: int, w: int) -> int:
    """Map a lattice coordinate (x, y, z, w) ∈ [0, 7]^4 to its phase
    in Z_MODULUS_4D.

    Bijective on [0, 7]^4 by construction (mixed-radix tower
    guarantees no Diophantine collision; verified by
    test_phase_4d_design.test_c2_image_is_4096_distinct_residues).
    """
    return (x * GEN_X + y * GEN_Y + z * GEN_Z + w * GEN_W) % MODULUS_4D

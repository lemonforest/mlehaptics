"""Inverse of :func:`phase_operators_4d.phi4` and helpers for
filtering off-board phase candidates.

Mirrors the 2D :mod:`phase_operators.phase_to_coords` shape:
``PHI_TO_XYZW`` and ``XYZW_TO_PHI`` are precomputed lookup tables;
``invert(phi)`` returns the unique board coordinate or ``None``;
``phase_set_to_board(phases)`` filters off-board phases out of a
candidate set.

Off-board detection is the boundary mechanism described in
PHASE_OPERATOR_SUPPLEMENT_4D.md §13.1.2 C3: phase shifts that carry
an origin off the board land in the off-image complement of Z_M
(MODULUS_4D = 12181 with image size 4096 means 8085 residues are
off-image), where ``invert`` returns ``None``.
"""
from __future__ import annotations

from typing import Optional, Tuple

from .phase_operators_4d import (
    GEN_X, GEN_Y, GEN_Z, GEN_W, MODULUS_4D, phi4,
)

Coord4D = Tuple[int, int, int, int]


# ─── lookup tables (precomputed at import time) ─────────────────────


def _build_lookup_tables() -> tuple[
    dict[int, Coord4D], dict[Coord4D, int]
]:
    phi_to_xyzw: dict[int, Coord4D] = {}
    xyzw_to_phi: dict[Coord4D, int] = {}
    for x in range(8):
        for y in range(8):
            for z in range(8):
                for w in range(8):
                    p = phi4(x, y, z, w)
                    coord = (x, y, z, w)
                    if p in phi_to_xyzw:
                        raise RuntimeError(
                            "phi4 image collision detected at "
                            f"phase={p}: {coord} vs "
                            f"{phi_to_xyzw[p]}. The Phase A design "
                            "(M=12181, GEN_X=1523, GEN_Y=191, "
                            "GEN_Z=23, GEN_W=3) should produce "
                            "4096 distinct phases — see "
                            "test_phase_4d_design.test_c2_image_"
                            "is_4096_distinct_residues."
                        )
                    phi_to_xyzw[p] = coord
                    xyzw_to_phi[coord] = p
    return phi_to_xyzw, xyzw_to_phi


PHI_TO_XYZW, XYZW_TO_PHI = _build_lookup_tables()
"""``PHI_TO_XYZW[phi]`` is the unique (x,y,z,w) ∈ [0,7]^4 satisfying
``phi4(x,y,z,w) == phi``. Defined for all 4096 phases in the image
of phi4; absent for the 8085 off-image residues."""


# ─── inversion ──────────────────────────────────────────────────────


def invert(phi: int) -> Optional[Coord4D]:
    """Return the lattice coordinate at phase ``phi`` if ``phi`` is
    in the image of :func:`phi4`; ``None`` otherwise.

    The off-image complement of Z_MODULUS_4D (8085 residues out of
    12181) is the boundary-detection sink: phase-op shifts that
    carry an origin off the board land here.
    """
    return PHI_TO_XYZW.get(phi % MODULUS_4D)


def phase_set_to_board(
    phases: frozenset[int] | set[int] | tuple[int, ...],
) -> frozenset[Coord4D]:
    """Map a candidate phase set (from a piece operator) to the set
    of valid board coordinates. Off-board phases are silently
    dropped — this is the structural boundary clipping that lets
    Phase B's piece operators over-generate without polluting
    downstream consumers."""
    out: set[Coord4D] = set()
    for p in phases:
        coord = PHI_TO_XYZW.get(p % MODULUS_4D)
        if coord is not None:
            out.add(coord)
    return frozenset(out)

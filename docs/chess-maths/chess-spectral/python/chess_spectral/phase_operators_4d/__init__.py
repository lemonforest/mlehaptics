"""4D phase-operator move engine (Z_8^4 / B_4 lattice).

Companion to :mod:`chess_spectral.phase_operators` (2D / D_4 lattice).

Validated against the spatial movegen in
:mod:`chess_spectral.tables_4d`:

  * Empty-board pseudo-legal move generation (Phase B,
    test_phase_4d_unobstructed.py): 4096 origins × N piece configs
    set-equal to ``tables_4d.X_targets``.
  * Occupation-aware moves (Phase C, test_phase_4d_occupation_aware.py):
    deferred — to follow Phase B.
  * Check detection (Phase D, test_phase_4d_check_detection.py):
    deferred.

See ``docs/chess-maths/PHASE_OPERATOR_SUPPLEMENT_4D.md`` for the
research record.
"""
from .phase_operators_4d import (
    MODULUS_4D, GEN_X, GEN_Y, GEN_Z, GEN_W, AXIS_GENS,
    AXIS_SHIFTS, PLANE_DIAG_SHIFTS, KNIGHT_SHIFTS, KING_SHIFTS,
    PawnAxis,
    phi4,
    P_rook4, P_bishop4, P_queen4, P_king4, P_knight4,
    P_pawn4_white, P_pawn4_black,
)
from .phase_to_coords_4d import (
    Coord4D, PHI_TO_XYZW, XYZW_TO_PHI,
    invert, phase_set_to_board,
)

__all__ = [
    # phase_operators_4d
    "MODULUS_4D", "GEN_X", "GEN_Y", "GEN_Z", "GEN_W", "AXIS_GENS",
    "AXIS_SHIFTS", "PLANE_DIAG_SHIFTS", "KNIGHT_SHIFTS", "KING_SHIFTS",
    "PawnAxis",
    "phi4",
    "P_rook4", "P_bishop4", "P_queen4", "P_king4", "P_knight4",
    "P_pawn4_white", "P_pawn4_black",
    # phase_to_coords_4d
    "Coord4D", "PHI_TO_XYZW", "XYZW_TO_PHI",
    "invert", "phase_set_to_board",
]

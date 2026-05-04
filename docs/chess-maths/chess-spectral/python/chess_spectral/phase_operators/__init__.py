"""Phase-space move generator and check detector (§11).

Validated at 100% against python-chess:

- pseudo-legal move generation on the empty board (§11.3, 416/416)
- occupation-aware pseudo-legal moves including en passant and
  castling (§11.4, 1153/1153 on sampled corpora; 100% against
  ``board.pseudo_legal_moves``)
- ``is_check`` via reverse phase-cast (§11.5 path 1, 3393/3393
  pseudo-legal transitions against ``board.is_check``)

See ``docs/chess-maths/PHASE_OPERATOR_SUPPLEMENT.md`` for the research
record.
"""

from .phase_operators import (
    phi, MODULUS,
    ROW_GEN, COL_GEN, DIAG_NE_SW_GEN, DIAG_NW_SE_GEN,
    KNIGHT_SHIFTS, KING_SHIFTS,
    P_rook, P_bishop, P_queen, P_king, P_knight,
    P_pawn_white, P_pawn_black,
)
from .phase_to_coords import (
    PHI_TO_RC, RC_TO_PHI, invert, phase_set_to_board,
)
from .occupation_field import (
    WHITE_CHARGE, BLACK_CHARGE, OccupiedPhase,
    occupation_field_from_board, ep_phase_from_board,
    occupation_field_from_pos_dict,  # 1.11.0 — ALU-native adapter
    ep_phase_from_ep_file,             # 1.11.0 — ALU-native adapter
    king_destinations, knight_destinations, pawn_destinations,
    is_own_charge,
)
from .occupation_aware_a import occupation_aware_moves_a
from .occupation_aware_b import occupation_aware_moves_b
from .occupation_aware_c import occupation_aware_moves_c
from .castling import (
    CastleMove, CASTLES,
    available_castles, castle_king_destinations,
)
from .phase_check_detection import (
    phasecast_is_check, move_leaves_king_in_check,
)
# 1.11.0 — ALU-native integration entry point (B-spike-1b)
from .alu_native import (
    phase_only_pseudo_legal_moves,
    PROMOTION_TARGETS,
)

__all__ = [
    # phase_operators
    "phi", "MODULUS",
    "ROW_GEN", "COL_GEN", "DIAG_NE_SW_GEN", "DIAG_NW_SE_GEN",
    "KNIGHT_SHIFTS", "KING_SHIFTS",
    "P_rook", "P_bishop", "P_queen", "P_king", "P_knight",
    "P_pawn_white", "P_pawn_black",
    # phase_to_coords
    "PHI_TO_RC", "RC_TO_PHI", "invert", "phase_set_to_board",
    # occupation_field
    "WHITE_CHARGE", "BLACK_CHARGE", "OccupiedPhase",
    "occupation_field_from_board", "ep_phase_from_board",
    "occupation_field_from_pos_dict",  # 1.11.0
    "ep_phase_from_ep_file",            # 1.11.0
    "king_destinations", "knight_destinations", "pawn_destinations",
    "is_own_charge",
    # occupation_aware_{a,b,c}
    "occupation_aware_moves_a",
    "occupation_aware_moves_b",
    "occupation_aware_moves_c",
    # castling
    "CastleMove", "CASTLES",
    "available_castles", "castle_king_destinations",
    # phase_check_detection
    "phasecast_is_check", "move_leaves_king_in_check",
    # 1.11.0 — ALU-native integration entry point (B-spike-1b)
    "phase_only_pseudo_legal_moves",
    "PROMOTION_TARGETS",
]

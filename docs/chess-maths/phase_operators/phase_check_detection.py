"""§11.5 Path 1: phase-native is_check via reverse phase-cast.

Casts inverse attack operators outward from the king's phase and intersects
with opponent-occupation-by-type. Equivalent in structure to bitboard-based
attack detection; runs in naive Python at ~35 μs per call vs python-chess's
~1 μs bitboard implementation.

This module exists as a REFERENCE CHANNEL for §11.5's experimental record,
not as a production check detector. It answers 'is the mover's king in check'
in pure phase space with a known-correct answer by construction. §11.5 uses
it to validate that any phase-similarity-based signal (path 2) carries
information beyond what a direct phase-space reformulation already provides.

See PHASE_OPERATOR_SUPPLEMENT.md §11.5.1 for the path-1 / path-2 distinction.
"""
import chess

from phase_operators import (
    phi, MODULUS,
    P_king, P_knight,
    DIAG_NE_SW_GEN, DIAG_NW_SE_GEN, ROW_GEN, COL_GEN,
)
from phase_to_coords import PHI_TO_RC
from occupation_field import occupation_field_from_board


def _pawn_threat_phases_on_king(king_phi: int,
                                king_color: int) -> frozenset[int]:
    """Phases from which an opposite-color pawn could attack the king.

    White king is attacked by black pawns diagonally forward-from-black,
    i.e., diagonally above the king in phase terms: king_phi + 60 and + 74.
    Black king is attacked by white pawns diagonally below: - 60 and - 74.
    """
    if king_color == +1:
        return frozenset({
            (king_phi + DIAG_NW_SE_GEN) % MODULUS,
            (king_phi + DIAG_NE_SW_GEN) % MODULUS,
        })
    return frozenset({
        (king_phi - DIAG_NW_SE_GEN) % MODULUS,
        (king_phi - DIAG_NE_SW_GEN) % MODULUS,
    })


def _sliding_ray_hits_king(king_phi: int,
                           occupation: dict[int, int],
                           directions: tuple[int, ...],
                           attacker_phases: frozenset[int]) -> bool:
    """Walk each ray outward from king_phi; return True if first blocker
    on any ray is in attacker_phases.

    Bounded at 7 steps per ray, 4 directions per slider family, so
    worst-case 28 iterations regardless of board population.
    """
    for d in directions:
        for k in range(1, 8):
            p = (king_phi + k * d) % MODULUS
            if p not in PHI_TO_RC:
                break
            if p in occupation:
                if p in attacker_phases:
                    return True
                break
    return False


def phasecast_is_check(board: chess.Board) -> bool:
    """Return True if the side-to-move's king is under attack.

    Path 1 reference: reverse phase-cast from the king's phase across all
    attacker types. Matches python-chess's is_check by construction.
    """
    mover_color = +1 if board.turn == chess.WHITE else -1
    king_sq = board.king(board.turn)
    if king_sq is None:
        return False
    king_r = chess.square_rank(king_sq)
    king_c = chess.square_file(king_sq)
    king_phi = phi(king_r, king_c)

    occupation = occupation_field_from_board(board)

    opp_by_type: dict[str, set[int]] = {
        "N": set(), "B": set(), "R": set(),
        "Q": set(), "K": set(), "P": set(),
    }
    opp_color = not board.turn
    for sq, piece in board.piece_map().items():
        if piece.color == opp_color:
            r = chess.square_rank(sq)
            c = chess.square_file(sq)
            opp_by_type[piece.symbol().upper()].add(phi(r, c))

    if P_knight(king_phi) & opp_by_type["N"]:
        return True
    if P_king(king_phi) & opp_by_type["K"]:
        return True

    pawn_threats = _pawn_threat_phases_on_king(king_phi, mover_color)
    if pawn_threats & opp_by_type["P"]:
        return True

    rook_rays = (ROW_GEN, -ROW_GEN, COL_GEN, -COL_GEN)
    bishop_rays = (DIAG_NE_SW_GEN, -DIAG_NE_SW_GEN,
                   DIAG_NW_SE_GEN, -DIAG_NW_SE_GEN)

    rook_or_queen = frozenset(opp_by_type["R"] | opp_by_type["Q"])
    bishop_or_queen = frozenset(opp_by_type["B"] | opp_by_type["Q"])

    if _sliding_ray_hits_king(king_phi, occupation, rook_rays,
                              rook_or_queen):
        return True
    if _sliding_ray_hits_king(king_phi, occupation, bishop_rays,
                              bishop_or_queen):
        return True

    return False


def move_leaves_king_in_check(board: chess.Board,
                              move: chess.Move) -> bool:
    """Return True if applying `move` to `board` leaves the mover's king
    attacked. Uses phasecast_is_check.

    This is the per-transition check-unsafe predicate used by §11.5.
    """
    board.push(move)
    try:
        board.turn = not board.turn
        result = phasecast_is_check(board)
        board.turn = not board.turn
    finally:
        board.pop()
    return result

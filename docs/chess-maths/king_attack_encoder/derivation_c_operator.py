"""Derivation C: attack operator from king's phase.

See PHASE_OPERATOR_SUPPLEMENT_12.md §12.5.

Vector-valued generalization of phase_operators.phase_check_detection.
phasecast_is_check. The boolean answer to "is the king attacked?"
reduces these 16 components to "is any of them positive"; C keeps
them as continuous values.

Feature layout (16 dims):
  [0..3]   4 rook-ray densities (+row, -row, +col, -col) for R or Q
           attackers along each ray. Density weighted by 1/k so closer
           attackers count more; ray terminates at first occupation.
  [4..7]   4 bishop-ray densities (+NE, -NE, +NW, -NW) for B or Q.
  [8]      Knight attack count.
  [9]      King adjacency count (opponent king within 1 square).
  [10..11] 2 pawn attack counts, one per capture-diagonal.
  [12..15] Reserved zero channels for future extensions.

Because C literally enumerates the components of is_check_unsafe as
continuous values, its correlation with is_check_unsafe is expected
to be strong. C therefore serves as a REFINED BASELINE: any
derivation (A or B) that beats C's correlation is carrying signal
beyond direct enumeration of attack-line occupation.
"""
import chess
import numpy as np

from chess_spectral.phase_operators import (
    phi, MODULUS, ROW_GEN, COL_GEN,
    DIAG_NE_SW_GEN, DIAG_NW_SE_GEN,
    P_king, P_knight,
    PHI_TO_RC,
    occupation_field_from_board,
)


FEATURE_DIM = 16


def derivation_c_channel(board: chess.Board) -> np.ndarray:
    """Return a 16-dim feature vector summarizing king-attack structure.

    Each component is a non-negative real number. Zeros mean "no
    attacker of that type in that direction class." If no king is
    on the board, returns zeros.
    """
    out = np.zeros(FEATURE_DIM, dtype=np.float64)
    king_sq = board.king(board.turn)
    if king_sq is None:
        return out

    king_r = chess.square_rank(king_sq)
    king_c = chess.square_file(king_sq)
    king_phi = phi(king_r, king_c)
    mover_color_white = (board.turn == chess.WHITE)

    occupation = occupation_field_from_board(board)
    opp_by_type: dict = {
        "N": set(), "B": set(), "R": set(),
        "Q": set(), "K": set(), "P": set(),
    }
    opp_color = not board.turn
    for sq, piece in board.piece_map().items():
        if piece.color != opp_color:
            continue
        r = chess.square_rank(sq)
        c = chess.square_file(sq)
        opp_by_type[piece.symbol().upper()].add(phi(r, c))

    rook_or_queen = opp_by_type["R"] | opp_by_type["Q"]
    for i, d in enumerate((ROW_GEN, -ROW_GEN, COL_GEN, -COL_GEN)):
        density = 0.0
        for k in range(1, 8):
            p = (king_phi + k * d) % MODULUS
            if p not in PHI_TO_RC:
                break
            if p in occupation:
                if p in rook_or_queen:
                    density += 1.0 / k
                break
        out[i] = density

    bishop_or_queen = opp_by_type["B"] | opp_by_type["Q"]
    for i, d in enumerate((DIAG_NE_SW_GEN, -DIAG_NE_SW_GEN,
                           DIAG_NW_SE_GEN, -DIAG_NW_SE_GEN)):
        density = 0.0
        for k in range(1, 8):
            p = (king_phi + k * d) % MODULUS
            if p not in PHI_TO_RC:
                break
            if p in occupation:
                if p in bishop_or_queen:
                    density += 1.0 / k
                break
        out[4 + i] = density

    out[8] = float(len(P_knight(king_phi) & opp_by_type["N"]))
    out[9] = float(len(P_king(king_phi) & opp_by_type["K"]))

    if mover_color_white:
        diag_phases = [
            (king_phi + DIAG_NW_SE_GEN) % MODULUS,
            (king_phi + DIAG_NE_SW_GEN) % MODULUS,
        ]
    else:
        diag_phases = [
            (king_phi - DIAG_NW_SE_GEN) % MODULUS,
            (king_phi - DIAG_NE_SW_GEN) % MODULUS,
        ]
    for i, dp in enumerate(sorted(diag_phases)):
        out[10 + i] = 1.0 if dp in opp_by_type["P"] else 0.0

    # Components 12-15 reserved for Phase B extensions; zero in Phase A.
    return out


def derivation_c_similarity(board_before: chess.Board,
                            move: chess.Move) -> float:
    """Cosine similarity between Derivation C vectors before/after a
    move. Returns a float in [-1, 1]; 0.0 on zero-norm degenerate
    cases (including the common case where both pre- and post-move
    positions have zero king-attack density — most quiet moves in
    most positions).

    Flips board.turn after push per §12.7.1.1 so the post-move
    channel queries the mover's king rather than the opponent's.
    """
    board_after = board_before.copy(stack=False)
    board_after.push(move)
    board_after.turn = not board_after.turn
    b = derivation_c_channel(board_before)
    a = derivation_c_channel(board_after)
    norm = float(np.linalg.norm(b) * np.linalg.norm(a))
    if norm == 0.0:
        return 0.0
    return float(np.dot(b, a) / norm)


def derivation_c_delta(board_before: chess.Board,
                       move: chess.Move) -> float:
    """L2 norm of (C_after − C_before). Phase A2 complementary metric
    to `derivation_c_similarity`: handles the common case where both
    C_before and C_after are near-zero (king safe on both sides of the
    move) by measuring the displacement directly rather than through
    a normalized inner product.

    Returns a non-negative float. Zero means the king-attack vector
    is unchanged by the move; positive values scale with the magnitude
    of change in attack density.

    Flips board.turn after push per §12.7.1.1 so the post-move
    channel queries the mover's king rather than the opponent's.

    See PHASE_OPERATOR_SUPPLEMENT_12.md §12.7.1.
    """
    board_after = board_before.copy(stack=False)
    board_after.push(move)
    board_after.turn = not board_after.turn
    b = derivation_c_channel(board_before)
    a = derivation_c_channel(board_after)
    return float(np.linalg.norm(a - b))


def derivation_c_after_magnitude(board_before: chess.Board,
                                 move: chess.Move) -> float:
    """L2 norm of C(board_after) alone. A tautological baseline:
    `is_check_unsafe` is defined as "some component of C_after is
    positive," so this metric's correlation with `is_check_unsafe`
    should be near 1.0 by construction. Its role in Phase A2 is to
    verify the evaluation pipeline recovers that baseline; any
    meaningful finding from A or `delta_c` must beat it along a
    dimension other than raw post-move attack density.

    Returns a non-negative float.

    Flips board.turn after push per §12.7.1.1 so the post-move
    channel queries the mover's king rather than the opponent's —
    the entire point of the tautological baseline is that it should
    correlate near-1.0 with `is_check_unsafe`, which is defined from
    the mover's perspective.

    See PHASE_OPERATOR_SUPPLEMENT_12.md §12.7.1.
    """
    board_after = board_before.copy(stack=False)
    board_after.push(move)
    board_after.turn = not board_after.turn
    a = derivation_c_channel(board_after)
    return float(np.linalg.norm(a))

"""Solution B — phase-space occupation field (batch / set-intersection).

Sliding ray: generate the full k ∈ {1..7} phase list, clip at first
off-board phase, then find the lowest-k intersection with Φ_occ and
truncate. Non-sliding pieces fall through to the localized filter
shared with Solution C.
"""
import chess

from .phase_operators import phi, MODULUS
from .phase_to_coords import PHI_TO_RC
from .occupation_field import (
    WHITE_CHARGE,
    king_destinations, knight_destinations, pawn_destinations,
    ep_phase_from_board,
)
from .castling import castle_king_destinations


_ROOK_RAYS: tuple[int, ...] = (67, -67, 7, -7)
_BISHOP_RAYS: tuple[int, ...] = (74, -74, 60, -60)
_QUEEN_RAYS: tuple[int, ...] = _ROOK_RAYS + _BISHOP_RAYS


def _ray_destinations_b(origin_phi: int, unit: int,
                        occupation: dict[int, int],
                        mover_charge: int) -> set[tuple[int, int]]:
    # Step 1: generate the on-board prefix of the ray in order of k.
    ray: list[tuple[int, tuple[int, int]]] = []
    for k in range(1, 8):
        phase_k = (origin_phi + k * unit) % MODULUS
        rc = PHI_TO_RC.get(phase_k)
        if rc is None:
            break  # boundary halt — all later k are off-board too
        ray.append((phase_k, rc))

    # Step 2: find the lowest-k intersection with Φ_occ.
    out: set[tuple[int, int]] = set()
    for phase_k, rc in ray:
        charge = occupation.get(phase_k)
        if charge is None:
            out.add(rc)
            continue
        if charge != mover_charge:
            out.add(rc)  # opposite-charge capture
        break  # blocker — stop regardless of charge
    return out


def _sliding_destinations_b(origin_phi: int, rays: tuple[int, ...],
                            occupation: dict[int, int],
                            mover_charge: int) -> frozenset[tuple[int, int]]:
    out: set[tuple[int, int]] = set()
    for unit in rays:
        out |= _ray_destinations_b(origin_phi, unit, occupation, mover_charge)
    return frozenset(out)


def occupation_aware_moves_b(board: chess.Board, piece_char: str,
                             origin_r: int, origin_c: int,
                             mover_charge: int,
                             occupation: dict[int, int] | None = None,
                             ) -> frozenset[tuple[int, int]]:
    from occupation_field import occupation_field_from_board
    if occupation is None:
        occupation = occupation_field_from_board(board)
    origin_phi = phi(origin_r, origin_c)
    pc = piece_char.upper()
    if pc == "R":
        return _sliding_destinations_b(origin_phi, _ROOK_RAYS,
                                       occupation, mover_charge)
    if pc == "B":
        return _sliding_destinations_b(origin_phi, _BISHOP_RAYS,
                                       occupation, mover_charge)
    if pc == "Q":
        return _sliding_destinations_b(origin_phi, _QUEEN_RAYS,
                                       occupation, mover_charge)
    if pc == "K":
        base = king_destinations(origin_phi, occupation, mover_charge)
        mover_color = (chess.WHITE if mover_charge == WHITE_CHARGE
                       else chess.BLACK)
        return base | castle_king_destinations(board, mover_color)
    if pc == "N":
        return knight_destinations(origin_phi, occupation, mover_charge)
    if pc == "P":
        return pawn_destinations(origin_r, origin_c, occupation, mover_charge,
                                 ep_phase=ep_phase_from_board(board))
    raise ValueError(f"unknown piece char: {piece_char}")

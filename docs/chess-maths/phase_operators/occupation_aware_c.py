"""Solution C — incremental phase operator (sequential / early halt).

Sliding ray: step k = 1, 2, ... along each direction; include each
unoccupied phase, stop at the first occupied phase (including the
capture step when charges differ). Non-sliding pieces delegate to
the shared localized filter.
"""
import chess

from phase_operators import phi, MODULUS
from phase_to_coords import invert
from occupation_field import (
    king_destinations, knight_destinations, pawn_destinations,
)


_ROOK_RAYS: tuple[int, ...] = (67, -67, 7, -7)
_BISHOP_RAYS: tuple[int, ...] = (74, -74, 60, -60)
_QUEEN_RAYS: tuple[int, ...] = _ROOK_RAYS + _BISHOP_RAYS


def _ray_destinations_c(origin_phi: int, unit: int,
                        occupation: dict[int, int],
                        mover_charge: int) -> set[tuple[int, int]]:
    out: set[tuple[int, int]] = set()
    for k in range(1, 8):
        phase_k = (origin_phi + k * unit) % MODULUS
        dest = invert(phase_k)
        if dest is None:
            break  # boundary halt
        charge_at = occupation.get(phase_k)
        if charge_at is None:
            out.add(dest)
            continue
        if charge_at == mover_charge:
            break  # own-charge blocker — stop before
        out.add(dest)  # opposite-charge capture
        break
    return out


def _sliding_destinations_c(origin_phi: int, rays: tuple[int, ...],
                            occupation: dict[int, int],
                            mover_charge: int) -> frozenset[tuple[int, int]]:
    out: set[tuple[int, int]] = set()
    for unit in rays:
        out |= _ray_destinations_c(origin_phi, unit, occupation, mover_charge)
    return frozenset(out)


def occupation_aware_moves_c(board: chess.Board, piece_char: str,
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
        return _sliding_destinations_c(origin_phi, _ROOK_RAYS,
                                       occupation, mover_charge)
    if pc == "B":
        return _sliding_destinations_c(origin_phi, _BISHOP_RAYS,
                                       occupation, mover_charge)
    if pc == "Q":
        return _sliding_destinations_c(origin_phi, _QUEEN_RAYS,
                                       occupation, mover_charge)
    if pc == "K":
        return king_destinations(origin_phi, occupation, mover_charge)
    if pc == "N":
        return knight_destinations(origin_phi, occupation, mover_charge)
    if pc == "P":
        return pawn_destinations(origin_r, origin_c, occupation, mover_charge)
    raise ValueError(f"unknown piece char: {piece_char}")

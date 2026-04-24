"""Phase-native occupation representation for §11.4 (Solutions B and C).

Occupancy is a dict mapping phase → Z₂ charge (+1 white, −1 black). Both
B and C consume this; they differ only in how sliding rays consult it.

Also exports the localized-destination filter shared by K/N/P across B
and C per §11.4.3's non-sliding reduction.

python-chess dependency:
    ``chess`` is imported lazily inside functions that actually need it
    so ``import chess_spectral`` does NOT force an eager ``import chess``
    for 4D-only consumers (``spectral-chess4d-oana-chiru``).  Type
    annotations that reference ``chess.Board`` / ``chess.Color`` are
    gated behind ``typing.TYPE_CHECKING`` per PEP 484.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import chess

from .phase_operators import (
    phi,
    P_king, P_knight,
    P_pawn_white, P_pawn_black,
    ROW_GEN, DIAG_NE_SW_GEN, DIAG_NW_SE_GEN,
    MODULUS,
)
from .phase_to_coords import PHI_TO_RC, invert, phase_set_to_board


WHITE_CHARGE = +1
BLACK_CHARGE = -1


@dataclass(frozen=True)
class OccupiedPhase:
    """A phase corresponding to an occupied square, annotated with Z₂ charge."""
    phase: int
    charge: int


def _color_to_charge(color: "chess.Color") -> int:
    import chess
    return WHITE_CHARGE if color == chess.WHITE else BLACK_CHARGE


def occupation_field_from_board(board: "chess.Board") -> dict[int, int]:
    import chess
    out: dict[int, int] = {}
    for square, piece in board.piece_map().items():
        r = chess.square_rank(square)
        c = chess.square_file(square)
        out[phi(r, c)] = _color_to_charge(piece.color)
    return out


def is_own_charge(occupation: dict[int, int], phase: int,
                  mover_charge: int) -> bool | None:
    charge = occupation.get(phase % MODULUS)
    if charge is None:
        return None
    return charge == mover_charge


def _filter_localized(candidate_phases, occupation: dict[int, int],
                      mover_charge: int) -> frozenset[tuple[int, int]]:
    """Shared by B and C for K/N: unoccupied OR opposite-charge."""
    out: set[tuple[int, int]] = set()
    for p in candidate_phases:
        rc = PHI_TO_RC.get(p % MODULUS)
        if rc is None:
            continue
        charge = occupation.get(p % MODULUS)
        if charge is None or charge != mover_charge:
            out.add(rc)
    return frozenset(out)


def king_destinations(origin_phi: int, occupation: dict[int, int],
                      mover_charge: int) -> frozenset[tuple[int, int]]:
    return _filter_localized(P_king(origin_phi), occupation, mover_charge)


def knight_destinations(origin_phi: int, occupation: dict[int, int],
                        mover_charge: int) -> frozenset[tuple[int, int]]:
    return _filter_localized(P_knight(origin_phi), occupation, mover_charge)


def ep_phase_from_board(board: "chess.Board") -> int | None:
    """Phase of board.ep_square, or None if no en passant target is active.

    Per §11.4.3.2 this is the pass-through of FEN ep_square state into
    phase space; the pawn_destinations generator uses it to lift an
    otherwise-empty capture diagonal into a legal destination.
    """
    import chess
    if board.ep_square is None:
        return None
    r = chess.square_rank(board.ep_square)
    c = chess.square_file(board.ep_square)
    return phi(r, c)


def pawn_destinations(origin_r: int, origin_c: int,
                      occupation: dict[int, int],
                      mover_charge: int,
                      ep_phase: int | None = None,
                      ) -> frozenset[tuple[int, int]]:
    """White/black pawn destinations with occupation-aware advance + capture
    and optional en passant.

    Advance cannot land on any occupied square; two-step advance also
    requires the intermediate square to be empty. Captures require the
    diagonal destination to be occupied by opposite charge — UNLESS
    ep_phase is set and equals the capture diagonal phase, in which
    case the capture is allowed even though the square is empty
    (§11.4.3.2 en passant).

    ep_phase: optional phase of the en passant target square, derived
    from board.ep_square. None when no ep capture is available.
    """
    origin_phi = phi(origin_r, origin_c)
    if mover_charge == WHITE_CHARGE:
        on_start = (origin_r == 1)
        one_step = (origin_phi + ROW_GEN) % MODULUS
        two_step = (origin_phi + 2 * ROW_GEN) % MODULUS
        cap_ne = (origin_phi + DIAG_NE_SW_GEN) % MODULUS
        cap_nw = (origin_phi + DIAG_NW_SE_GEN) % MODULUS
    else:
        on_start = (origin_r == 6)
        one_step = (origin_phi - ROW_GEN) % MODULUS
        two_step = (origin_phi - 2 * ROW_GEN) % MODULUS
        cap_ne = (origin_phi - DIAG_NE_SW_GEN) % MODULUS
        cap_nw = (origin_phi - DIAG_NW_SE_GEN) % MODULUS

    out: set[tuple[int, int]] = set()

    one_rc = invert(one_step)
    if one_rc is not None and one_step not in occupation:
        out.add(one_rc)
        if on_start:
            two_rc = invert(two_step)
            if two_rc is not None and two_step not in occupation:
                out.add(two_rc)

    for cap_phase in (cap_ne, cap_nw):
        rc = invert(cap_phase)
        if rc is None:
            continue
        charge = occupation.get(cap_phase)
        if charge is not None and charge != mover_charge:
            out.add(rc)
        elif ep_phase is not None and cap_phase == ep_phase:
            out.add(rc)

    return frozenset(out)

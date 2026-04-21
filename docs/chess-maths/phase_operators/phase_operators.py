"""Phase operators on Z_640 per PHASE_OPERATOR_SUPPLEMENT.md §11.2.

Pure arithmetic, stdlib only. Every operator returns a frozenset[int] of
phase values in [0, 640), excluding the origin phase. Destinations that
fall outside the 64-square board image are handled downstream by
phase_to_coords.invert — boundary clipping is not this module's concern.
"""

ROW_GEN = 67
COL_GEN = 7
MODULUS = 640

DIAG_NE_SW_GEN = 74   # 67 + 7
DIAG_NW_SE_GEN = 60   # 67 - 7

KNIGHT_SHIFTS: tuple[int, ...] = (141, 127, 81, 53, -141, -127, -81, -53)
KING_SHIFTS: tuple[int, ...] = (67, 7, 74, 60, -67, -7, -74, -60)


def phi(r: int, c: int) -> int:
    return (r * ROW_GEN + c * COL_GEN) % MODULUS


def P_rook(origin_phi: int) -> frozenset[int]:
    out = set()
    for k in range(1, 8):
        out.add((origin_phi + k * ROW_GEN) % MODULUS)
        out.add((origin_phi - k * ROW_GEN) % MODULUS)
        out.add((origin_phi + k * COL_GEN) % MODULUS)
        out.add((origin_phi - k * COL_GEN) % MODULUS)
    return frozenset(out)


def P_bishop(origin_phi: int) -> frozenset[int]:
    out = set()
    for k in range(1, 8):
        out.add((origin_phi + k * DIAG_NE_SW_GEN) % MODULUS)
        out.add((origin_phi - k * DIAG_NE_SW_GEN) % MODULUS)
        out.add((origin_phi + k * DIAG_NW_SE_GEN) % MODULUS)
        out.add((origin_phi - k * DIAG_NW_SE_GEN) % MODULUS)
    return frozenset(out)


def P_queen(origin_phi: int) -> frozenset[int]:
    return P_rook(origin_phi) | P_bishop(origin_phi)


def P_king(origin_phi: int) -> frozenset[int]:
    return frozenset((origin_phi + s) % MODULUS for s in KING_SHIFTS)


def P_knight(origin_phi: int) -> frozenset[int]:
    return frozenset((origin_phi + s) % MODULUS for s in KNIGHT_SHIFTS)


def P_pawn_white(origin_phi: int, *, on_starting_rank: bool,
                 include_captures: bool) -> frozenset[int]:
    def _advance() -> set[int]:
        out = {(origin_phi + ROW_GEN) % MODULUS}
        if on_starting_rank:
            out.add((origin_phi + 2 * ROW_GEN) % MODULUS)
        return out

    def _capture() -> set[int]:
        return {
            (origin_phi + DIAG_NE_SW_GEN) % MODULUS,
            (origin_phi + DIAG_NW_SE_GEN) % MODULUS,
        }

    dests = _advance()
    if include_captures:
        dests |= _capture()
    return frozenset(dests)


def P_pawn_black(origin_phi: int, *, on_starting_rank: bool,
                 include_captures: bool) -> frozenset[int]:
    def _advance() -> set[int]:
        out = {(origin_phi - ROW_GEN) % MODULUS}
        if on_starting_rank:
            out.add((origin_phi - 2 * ROW_GEN) % MODULUS)
        return out

    def _capture() -> set[int]:
        return {
            (origin_phi - DIAG_NE_SW_GEN) % MODULUS,
            (origin_phi - DIAG_NW_SE_GEN) % MODULUS,
        }

    dests = _advance()
    if include_captures:
        dests |= _capture()
    return frozenset(dests)

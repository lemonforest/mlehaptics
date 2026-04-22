"""Phase ↔ (row, col) inversion per PHASE_OPERATOR_SUPPLEMENT.md §11.3.2.

The 64 board squares inject into Z_640 via phi(r, c) = (r*67 + c*7) mod 640.
PHI_TO_RC is that image built once at import; invert() is a single dict
lookup returning None for phases outside the board image (the 576 holes).
phase_set_to_board drops off-image phases, implementing the boundary clip.
"""
from .phase_operators import MODULUS, phi


def _build_tables() -> tuple[dict[int, tuple[int, int]], dict[tuple[int, int], int]]:
    phi_to_rc: dict[int, tuple[int, int]] = {}
    rc_to_phi: dict[tuple[int, int], int] = {}
    for r in range(8):
        for c in range(8):
            p = phi(r, c)
            phi_to_rc[p] = (r, c)
            rc_to_phi[(r, c)] = p
    return phi_to_rc, rc_to_phi


PHI_TO_RC, RC_TO_PHI = _build_tables()


def invert(phase: int) -> tuple[int, int] | None:
    return PHI_TO_RC.get(phase % MODULUS)


def phase_set_to_board(phase_set) -> frozenset[tuple[int, int]]:
    out = set()
    for p in phase_set:
        rc = PHI_TO_RC.get(p % MODULUS)
        if rc is not None:
            out.add(rc)
    return frozenset(out)

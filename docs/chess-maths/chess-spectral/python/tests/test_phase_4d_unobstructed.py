"""Phase B structural gate — 4D phase operators reproduce
``tables_4d.X_targets`` set-equal at every origin square.

This is the 4D analogue of 2D's ``PHASE_OPERATOR_SUPPLEMENT.md``
§11.3 empty-board equivalence (416/416 against
``python-chess.pseudo_legal_moves``). Where 2D used python-chess as
the spatial oracle, 4D uses our own ``tables_4d`` (since
python-chess has no 4D mode).

For each piece p ∈ {rook, bishop, queen, knight, king,
pawn(w-white), pawn(w-black), pawn(y-white), pawn(y-black)} and
every origin (x, y, z, w) ∈ [0, 7]^4 (4096 squares):

    1. Phase reachable set:
           phase_set_to_board(P_p(phi4(x, y, z, w)))
       (off-board phases drop via invert -> None)

    2. Spatial reachable set:
           frozenset(tables_4d.X_targets(x, y, z, w))

    3. Assert set equality.

If the design's phase operators reproduce the spatial movegen on
4096 origins × N piece configs, the structural claim from
PHASE_OPERATOR_SUPPLEMENT_4D.md §13.3 is confirmed: 4D chess
geometry under O&C is fully captured by the φ_4d coprime cyclic
phase structure.

Failures report ``(piece, origin, missing_in_phase, extra_in_phase)``
so the failure mode is actionable.
"""
from __future__ import annotations

from itertools import product

import pytest

from chess_spectral import tables_4d as t4
from chess_spectral.phase_operators_4d import (
    P_rook4, P_bishop4, P_queen4, P_king4, P_knight4,
    P_pawn4_white, P_pawn4_black,
    phi4, phase_set_to_board, Coord4D,
)


# Eight origin classes (interior, corner, edge, etc.) for sub-suite
# fast tests — full 4096-origin sweep is in the parametrized version
# below and runs in O(seconds).
SAMPLE_ORIGINS: tuple[Coord4D, ...] = (
    (3, 3, 3, 3),  # deep interior
    (0, 0, 0, 0),  # corner (origin)
    (7, 7, 7, 7),  # corner (far)
    (0, 7, 0, 7),  # mixed corner
    (3, 0, 4, 7),  # edge
    (1, 6, 2, 5),  # interior off-center
    (0, 3, 3, 3),  # face
    (3, 0, 3, 3),  # face
)


# ─── full-sweep helpers ─────────────────────────────────────────────


def _all_origins() -> list[Coord4D]:
    return [(x, y, z, w) for x, y, z, w in product(range(8), repeat=4)]


def _phase_dests_for_piece(
    piece: str, origin: Coord4D
) -> frozenset[Coord4D]:
    x, y, z, w = origin
    p = phi4(x, y, z, w)
    if piece == "rook":
        phases = P_rook4(p)
    elif piece == "bishop":
        phases = P_bishop4(p)
    elif piece == "queen":
        phases = P_queen4(p)
    elif piece == "knight":
        phases = P_knight4(p)
    elif piece == "king":
        phases = P_king4(p)
    elif piece == "pawn_w_white":
        phases = P_pawn4_white(
            p, axis="w", on_starting_rank=False, include_captures=False,
        )
    elif piece == "pawn_w_black":
        phases = P_pawn4_black(
            p, axis="w", on_starting_rank=False, include_captures=False,
        )
    elif piece == "pawn_y_white":
        phases = P_pawn4_white(
            p, axis="y", on_starting_rank=False, include_captures=False,
        )
    elif piece == "pawn_y_black":
        phases = P_pawn4_black(
            p, axis="y", on_starting_rank=False, include_captures=False,
        )
    else:
        raise ValueError(f"unknown piece: {piece}")
    return phase_set_to_board(phases)


def _spatial_dests_for_piece(
    piece: str, origin: Coord4D
) -> frozenset[Coord4D]:
    x, y, z, w = origin
    if piece == "rook":
        return frozenset(t4.rook4_targets(x, y, z, w))
    if piece == "bishop":
        return frozenset(t4.bishop4_targets(x, y, z, w))
    if piece == "queen":
        return frozenset(t4.queen4_targets(x, y, z, w))
    if piece == "knight":
        return frozenset(t4.knight4_targets(x, y, z, w))
    if piece == "king":
        return frozenset(t4.king4_targets(x, y, z, w))
    if piece == "pawn_w_white":
        # white-w-pawn: forward push on +w axis (one square only;
        # double-push from starting rank is a separate test below).
        return frozenset(t4.white_pawn4_targets(x, y, z, w))
    if piece == "pawn_w_black":
        # black-w-pawn: forward push on -w axis. tables_4d only
        # exposes white targets; mirror by hand.
        return frozenset(
            (x, y, z, w - 1) for _ in [0] if w - 1 >= 0
        )
    if piece == "pawn_y_white":
        return frozenset(t4.white_pawn4_y_targets(x, y, z, w))
    if piece == "pawn_y_black":
        return frozenset(
            (x, y - 1, z, w) for _ in [0] if y - 1 >= 0
        )
    raise ValueError(f"unknown piece: {piece}")


# ─── full-sweep gate ────────────────────────────────────────────────


PIECE_CONFIGS = (
    "rook", "bishop", "queen", "knight", "king",
    "pawn_w_white", "pawn_w_black",
    "pawn_y_white", "pawn_y_black",
)


@pytest.mark.parametrize("piece", PIECE_CONFIGS)
def test_phase_op_matches_spatial_oracle_on_all_4096_origins(piece: str):
    """The structural pass/fail gate. Must succeed for every piece
    config — failure means the φ_4d design or one of the per-piece
    operators is wrong.

    Reports the first mismatched (origin, missing, extra) triple
    when the assertion fails.
    """
    mismatches = []
    for origin in _all_origins():
        phase = _phase_dests_for_piece(piece, origin)
        spatial = _spatial_dests_for_piece(piece, origin)
        if phase != spatial:
            mismatches.append((
                origin,
                spatial - phase,    # missing from phase
                phase - spatial,    # extra in phase
            ))
            if len(mismatches) >= 3:
                break
    assert not mismatches, (
        f"{piece}: {len(mismatches)}+ mismatches across 4096 origins. "
        f"First three: {mismatches}"
    )


# ─── O&C interior mobility cross-check ──────────────────────────────


def test_rook_interior_mobility_is_28():
    """Per O&C section 3 + chess_spectral_4d_notebook.md Phase 1."""
    dests = _phase_dests_for_piece("rook", (3, 3, 3, 3))
    assert len(dests) == 28, (
        f"4D rook interior mobility = {len(dests)} (expected 28)"
    )


def test_king_interior_mobility_is_80():
    dests = _phase_dests_for_piece("king", (3, 3, 3, 3))
    assert len(dests) == 80, (
        f"4D king interior mobility = {len(dests)} (expected 80)"
    )


def test_knight_interior_mobility_is_48():
    dests = _phase_dests_for_piece("knight", (3, 3, 3, 3))
    assert len(dests) == 48, (
        f"4D knight interior mobility = {len(dests)} (expected 48)"
    )


def test_bishop_two_components_via_parity():
    """Per O&C: bishop graph splits into 2 connected components by
    sum(coords) mod 2. From an even-parity origin, all destinations
    share the same parity. Equivalent property to the spatial
    oracle's connected-components result."""
    origin = (3, 3, 3, 3)  # parity 0 (sum 12 even)
    dests = _phase_dests_for_piece("bishop", origin)
    parities = {sum(d) % 2 for d in dests}
    assert parities == {0}, (
        f"bishop from even-parity origin reaches odd-parity squares: "
        f"{parities}"
    )

    origin_odd = (3, 3, 3, 4)  # parity 1 (sum 13 odd)
    dests_odd = _phase_dests_for_piece("bishop", origin_odd)
    parities_odd = {sum(d) % 2 for d in dests_odd}
    assert parities_odd == {1}


def test_queen_equals_rook_union_bishop():
    """Per O&C: A_queen = A_rook + A_bishop (disjoint edge support).
    Phase op should reflect this exactly at every origin."""
    for origin in SAMPLE_ORIGINS:
        rook_dests = _phase_dests_for_piece("rook", origin)
        bishop_dests = _phase_dests_for_piece("bishop", origin)
        queen_dests = _phase_dests_for_piece("queen", origin)
        assert queen_dests == (rook_dests | bishop_dests), (
            f"queen ≠ rook ∪ bishop at origin {origin}"
        )
        # Disjoint support: rook ∩ bishop should be empty.
        assert (rook_dests & bishop_dests) == frozenset(), (
            f"rook and bishop share destinations at {origin}: "
            f"{rook_dests & bishop_dests}"
        )


# ─── pawn double-push from starting rank ────────────────────────────


def test_w_pawn_white_double_push_from_starting_rank():
    """White W-pawn on starting rank (w=1) reaches w=2 and w=3."""
    x, y, z, w = 3, 3, 3, 1
    p = phi4(x, y, z, w)
    phases = P_pawn4_white(
        p, axis="w", on_starting_rank=True, include_captures=False,
    )
    dests = phase_set_to_board(phases)
    expected = frozenset({(3, 3, 3, 2), (3, 3, 3, 3)})
    assert dests == expected


def test_w_pawn_white_single_push_off_starting_rank():
    """White W-pawn at w=4 (not starting) reaches only w=5."""
    x, y, z, w = 3, 3, 3, 4
    p = phi4(x, y, z, w)
    phases = P_pawn4_white(
        p, axis="w", on_starting_rank=False, include_captures=False,
    )
    dests = phase_set_to_board(phases)
    assert dests == frozenset({(3, 3, 3, 5)})


def test_y_pawn_white_double_push_from_starting_rank():
    """White Y-pawn on starting rank (y=1) reaches y=2 and y=3."""
    x, y, z, w = 3, 1, 3, 3
    p = phi4(x, y, z, w)
    phases = P_pawn4_white(
        p, axis="y", on_starting_rank=True, include_captures=False,
    )
    dests = phase_set_to_board(phases)
    expected = frozenset({(3, 2, 3, 3), (3, 3, 3, 3)})
    assert dests == expected


def test_w_pawn_black_single_push():
    """Black W-pawn at w=5 reaches w=4 (one square in -w direction)."""
    x, y, z, w = 3, 3, 3, 5
    p = phi4(x, y, z, w)
    phases = P_pawn4_black(
        p, axis="w", on_starting_rank=False, include_captures=False,
    )
    dests = phase_set_to_board(phases)
    assert dests == frozenset({(3, 3, 3, 4)})


def test_w_pawn_white_captures_in_xw_plane():
    """Phase E: white W-pawn captures at ``(±g_x + g_w)`` mod M.

    From (3, 3, 3, 3), a white W-pawn captures at (4, 3, 3, 4) and
    (2, 3, 3, 4). Per O&C §3.10 Def 13, these are the only two
    capture targets — XZ, YZ, ZW captures are not legal.
    """
    p = phi4(3, 3, 3, 3)
    phases = P_pawn4_white(
        p, axis="w", on_starting_rank=False, include_captures=True,
    )
    dests = phase_set_to_board(phases)
    expected_forward = (3, 3, 3, 4)
    expected_capture_left = (2, 3, 3, 4)
    expected_capture_right = (4, 3, 3, 4)
    assert dests == frozenset({
        expected_forward,
        expected_capture_left,
        expected_capture_right,
    })


def test_y_pawn_white_captures_in_xy_plane():
    """Phase E: white Y-pawn captures at ``(±g_x + g_y)`` mod M."""
    p = phi4(3, 3, 3, 3)
    phases = P_pawn4_white(
        p, axis="y", on_starting_rank=False, include_captures=True,
    )
    dests = phase_set_to_board(phases)
    assert dests == frozenset({
        (3, 4, 3, 3),  # forward
        (2, 4, 3, 3),  # left-x diagonal
        (4, 4, 3, 3),  # right-x diagonal
    })


def test_w_pawn_black_captures_in_xw_plane_negative_forward():
    """Black W-pawn forward sign is -1; captures at (±g_x - g_w)."""
    p = phi4(3, 3, 3, 3)
    phases = P_pawn4_black(
        p, axis="w", on_starting_rank=False, include_captures=True,
    )
    dests = phase_set_to_board(phases)
    assert dests == frozenset({
        (3, 3, 3, 2),
        (2, 3, 3, 2),
        (4, 3, 3, 2),
    })


def test_pawn_captures_clip_at_board_boundary():
    """A pawn at x=0 only has one capture diagonal (right-x); x=7
    only has left-x. ``phase_set_to_board`` drops the off-board
    candidate."""
    # White W-pawn at (0, 3, 3, 3): only (1, 3, 3, 4) is in bounds.
    p = phi4(0, 3, 3, 3)
    dests = phase_set_to_board(P_pawn4_white(
        p, axis="w", on_starting_rank=False, include_captures=True,
    ))
    assert dests == frozenset({(0, 3, 3, 4), (1, 3, 3, 4)})


def test_pawn_captures_at_axis_boundary_drop():
    """A white W-pawn at w=7 has nowhere to capture (no +w available),
    AND no forward (the pawn would already have promoted in real
    play). All include_captures phases land off-board; result empty."""
    p = phi4(3, 3, 3, 7)
    dests = phase_set_to_board(P_pawn4_white(
        p, axis="w", on_starting_rank=False, include_captures=True,
    ))
    assert dests == frozenset()


def test_pawn_axis_z_is_rejected():
    """O&C Def 11: pawns are W- or Y-oriented, never Z-oriented. The
    operator rejects axis='z' loudly."""
    p = phi4(3, 3, 3, 3)
    with pytest.raises(ValueError, match="O&C Def 11"):
        P_pawn4_white(
            p, axis="z", on_starting_rank=False,  # type: ignore[arg-type]
            include_captures=False,
        )

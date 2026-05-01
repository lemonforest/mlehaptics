"""1.8.1 immolation: canonical Oana-Chiru §3.3 initial position.

The 28-king starting position has shown up many times in the
chess-spectral CHANGELOG ("250s legal_moves at the 28-king start",
"~125× speedup vs 1.6") but until 1.8.1 was never *defined* in this
package — chess4D-OC and the engine each carried their own
hand-rolled fixtures. This test file is the canonical-source gate:
if anything drifts, the byte-exact FEN4 hash check at the bottom
fails first, and individual structural tests pinpoint *what*
drifted (slice membership? piece count? pawn-axis assignment? back
rank?).

The §3.3 partition (translated to FEN4 0-indexed coords):
  |C|=4 (z∈{3,4}, w∈{3,4})            full 2D start, both colors
  |W_only|=24                          white pieces only
  |B_only|=24                          black pieces only
  |E|=12 (z∈{3,4}, w∉{3,4})            empty
  Total: 64 (z, w) slices ✓

Piece counts: 448 white + 448 black = 896, with 28 kings per side.
"""
from __future__ import annotations

import hashlib
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
if PKG not in sys.path:
    sys.path.insert(0, PKG)

from chess_spectral_4d import (   # noqa: E402
    STARTING_FEN4, initial_position,
    central_slices, white_only_slices,
    black_only_slices, empty_slices,
    GameState4D, SIDE_WHITE, SIDE_BLACK, coord_to_sq,
)


# ─── Slice-set structure ────────────────────────────────────────────


def test_immolation_slice_cardinalities_match_spec():
    assert len(central_slices()) == 4
    assert len(white_only_slices()) == 24
    assert len(black_only_slices()) == 24
    assert len(empty_slices()) == 12


def test_immolation_slice_sets_are_pairwise_disjoint():
    c = central_slices()
    w = white_only_slices()
    b = black_only_slices()
    e = empty_slices()
    assert len(c & w) == 0
    assert len(c & b) == 0
    assert len(c & e) == 0
    assert len(w & b) == 0
    assert len(w & e) == 0
    assert len(b & e) == 0


def test_immolation_slice_sets_cover_all_64_slices():
    """4+24+24+12 = 64 = |{0..7} × {0..7}|."""
    c = central_slices()
    w = white_only_slices()
    b = black_only_slices()
    e = empty_slices()
    union = c | w | b | e
    assert len(union) == 64
    assert union == {(z, w_) for z in range(8) for w_ in range(8)}


def test_immolation_central_slices_are_paper_subset():
    """Central C = {(z, w) | z ∈ {3, 4}, w ∈ {3, 4}} (FEN4 0-indexed
    = paper z ∈ {4, 5}, w ∈ {4, 5})."""
    expected = {(z, w) for z in (3, 4) for w in (3, 4)}
    assert central_slices() == expected


def test_immolation_empty_slices_are_paper_subset():
    """E = {(z, w) | z ∈ {3, 4}, w ∈ {0, 1, 2, 5, 6, 7}}."""
    expected = {(z, w) for z in (3, 4) for w in (0, 1, 2, 5, 6, 7)}
    assert empty_slices() == expected


# ─── Aggregate piece counts ─────────────────────────────────────────


def test_immolation_total_piece_counts():
    gs = initial_position()
    assert len(gs.position) == 896
    assert len(gs.pieces_of(SIDE_WHITE)) == 448
    assert len(gs.pieces_of(SIDE_BLACK)) == 448


def test_immolation_28_kings_per_side():
    gs = initial_position()
    white_kings = sum(1 for _, v in gs.pieces_of(SIDE_WHITE) if v == "K")
    black_kings = sum(1 for _, v in gs.pieces_of(SIDE_BLACK) if v == "k")
    assert white_kings == 28
    assert black_kings == 28


def test_immolation_pawn_counts_per_color():
    """Each non-empty slice contains 8 pawns of its placed color
    (one per file). 28 white slices × 8 = 224 white pawns; same
    for black. The 16-piece per-slice count is half pawns."""
    gs = initial_position()
    white_pawns = sum(
        1 for _, v in gs.pieces_of(SIDE_WHITE)
        if isinstance(v, tuple) and v[0] == "P"
    )
    black_pawns = sum(
        1 for _, v in gs.pieces_of(SIDE_BLACK)
        if isinstance(v, tuple) and v[0] == "p"
    )
    assert white_pawns == 224
    assert black_pawns == 224


# ─── Per-slice piece structure ──────────────────────────────────────


def test_immolation_central_slice_has_both_colors():
    """Central slice (3, 3): both white and black 2D-standard
    starting pieces present."""
    gs = initial_position()
    z, w = 3, 3
    # White king at (4, 0, 3, 3); black king at (4, 7, 3, 3).
    assert gs.occupant((4, 0, z, w)) == "K"
    assert gs.occupant((4, 7, z, w)) == "k"


def test_immolation_empty_slice_has_no_pieces():
    """Empty slice (3, 0): zero pieces from either side."""
    gs = initial_position()
    z, w = 3, 0
    for x in range(8):
        for y in range(8):
            assert gs.occupant((x, y, z, w)) is None, (
                f"empty slice ({z},{w}) shouldn't have a piece at "
                f"({x},{y},{z},{w}) but got {gs.occupant((x, y, z, w))!r}"
            )


def test_immolation_white_only_slice_has_no_black():
    """W_only slice (0, 0): only white pieces, no black."""
    gs = initial_position()
    z, w = 0, 0
    # White king at (4, 0, 0, 0).
    assert gs.occupant((4, 0, z, w)) == "K"
    # No black pieces anywhere on the slice.
    for x in range(8):
        for y in range(8):
            occ = gs.occupant((x, y, z, w))
            if occ is None:
                continue
            if isinstance(occ, tuple):
                assert occ[0] == "P", (
                    f"black pawn in white-only slice ({z},{w}): "
                    f"({x},{y},{z},{w}) = {occ!r}"
                )
            else:
                assert occ.isupper(), (
                    f"lowercase piece in white-only slice "
                    f"({z},{w}): ({x},{y},{z},{w}) = {occ!r}"
                )


def test_immolation_black_only_slice_has_no_white():
    """B_only slice (0, 4): only black pieces, no white."""
    gs = initial_position()
    z, w = 0, 4
    # Black king at (4, 7, 0, 4).
    assert gs.occupant((4, 7, z, w)) == "k"
    for x in range(8):
        for y in range(8):
            occ = gs.occupant((x, y, z, w))
            if occ is None:
                continue
            if isinstance(occ, tuple):
                assert occ[0] == "p", (
                    f"white pawn in black-only slice ({z},{w}): "
                    f"({x},{y},{z},{w}) = {occ!r}"
                )
            else:
                assert occ.islower(), (
                    f"uppercase piece in black-only slice "
                    f"({z},{w}): ({x},{y},{z},{w}) = {occ!r}"
                )


# ─── Back-rank order and pawn-axis-by-file rule ─────────────────────


@pytest.mark.parametrize("zw", [(3, 3), (0, 0), (5, 5)])
def test_immolation_white_back_rank_order(zw):
    """y=0 white back rank reads R N B Q K B N R left-to-right."""
    z, w = zw
    gs = initial_position()
    expected = ["R", "N", "B", "Q", "K", "B", "N", "R"]
    actual = [gs.occupant((x, 0, z, w)) for x in range(8)]
    assert actual == expected


@pytest.mark.parametrize("zw", [(3, 3), (0, 4), (7, 0)])
def test_immolation_black_back_rank_order(zw):
    """y=7 black back rank reads r n b q k b n r left-to-right."""
    z, w = zw
    gs = initial_position()
    expected = ["r", "n", "b", "q", "k", "b", "n", "r"]
    actual = [gs.occupant((x, 7, z, w)) for x in range(8)]
    assert actual == expected


def test_immolation_pawn_axis_by_x_parity():
    """Definition 11: even x → Y-oriented; odd x → W-oriented.
    Every white pawn at y=1 and every black pawn at y=6 must follow
    this rule across every non-empty slice."""
    gs = initial_position()
    # White-pawn-bearing slices.
    for (z, w) in (central_slices() | white_only_slices()):
        for x in range(8):
            v = gs.occupant((x, 1, z, w))
            assert isinstance(v, tuple) and v[0] == "P", (
                f"white pawn missing at ({x}, 1, {z}, {w}): {v!r}"
            )
            expected_axis = "y" if (x % 2 == 0) else "w"
            assert v[1] == expected_axis, (
                f"white pawn at x={x} should be {expected_axis}-oriented, "
                f"got {v[1]!r}"
            )
    # Black-pawn-bearing slices.
    for (z, w) in (central_slices() | black_only_slices()):
        for x in range(8):
            v = gs.occupant((x, 6, z, w))
            assert isinstance(v, tuple) and v[0] == "p", (
                f"black pawn missing at ({x}, 6, {z}, {w}): {v!r}"
            )
            expected_axis = "y" if (x % 2 == 0) else "w"
            assert v[1] == expected_axis, (
                f"black pawn at x={x} should be {expected_axis}-oriented, "
                f"got {v[1]!r}"
            )


# ─── FEN4 round-trip + byte-stability ────────────────────────────────


def test_immolation_fen4_round_trip_canonical():
    """from_fen(STARTING_FEN4).to_fen() == STARTING_FEN4. Catches
    any non-canonical ordering or whitespace drift in serialize().
    """
    gs = GameState4D.from_fen(STARTING_FEN4)
    assert gs.to_fen() == STARTING_FEN4


def test_immolation_initial_position_matches_starting_fen4():
    """The initial_position() factory and the STARTING_FEN4 string
    describe the same position."""
    gs = initial_position()
    assert gs.to_fen() == STARTING_FEN4


def test_immolation_initial_position_side_to_move_white():
    """FIDE Article 4.7: white to move on the first ply."""
    gs = initial_position()
    assert gs.side_to_move == SIDE_WHITE


def test_immolation_starting_fen4_byte_hash_locked():
    """SHA-256 of STARTING_FEN4 is locked here. If §3.3 partitioning
    or back-rank order changes (intentional or otherwise), this hash
    will diverge — the failing assertion message tells you the new
    hash so you can update it deliberately, NOT silently."""
    digest = hashlib.sha256(STARTING_FEN4.encode("ascii")).hexdigest()
    expected = "d02c57216d11ce9495aa3595afd086bbcc4a6eb43386336b7dc3380e2bbdfb2b"
    assert digest == expected, (
        f"STARTING_FEN4 hash drifted!\n"
        f"  got:      {digest}\n"
        f"  expected: {expected}\n"
        f"If the change was intentional (e.g. spec §3.3 amendment),\n"
        f"update the expected hash in this test along with the spec\n"
        f"reference in chess_spectral_4d/initial_position.py."
    )


def test_immolation_starting_fen4_first_chars():
    """Surface check: the FEN4 starts with the canonical prefix and
    the first piece is the white rook at (0, 0, 0, 0). Catches
    most accidental layout mutations cheaper than the full hash
    check."""
    assert STARTING_FEN4.startswith("4d-fen v1: ")
    # First piece by canonical (sorted-by-sq) ordering must be
    # white-rook at sq=0 = (0, 0, 0, 0).
    first_piece_chunk = STARTING_FEN4.split(":", 1)[1].strip().split(";")[0]
    assert first_piece_chunk.strip() == "R@0,0,0,0"

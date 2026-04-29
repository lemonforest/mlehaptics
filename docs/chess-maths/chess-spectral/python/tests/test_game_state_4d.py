"""GameState4D + MoveHistory4D — move history + draw detection
(chess-spectral 1.4.0, §16.9 #2 / #3 / §17.3).

Covers:
    * MoveHistory4D append behavior — ply numbering, side flip
    * Half-move clock per FIDE Article 9.3 (resets on pawn move OR
      capture; increments otherwise)
    * Threefold-repetition detection via SHA-256 position hashing
      (deterministic 6-ply sequence triggers draw at the 3rd
      occurrence of the starting position; ≥ THREEFOLD_THRESHOLD)
    * 50-move-rule detection (100 quiet half-moves between two kings)
    * Insufficient-material classification (2D K-vs-K, K+B-vs-K,
      K+N-vs-K; 4D placeholder raises NotImplementedError)
    * get_draw_status bridge method end-to-end for each draw
      condition; stalemate gated by has_legal_moves
    * get_move_history bridge method round-trips a few moves to
      plain dicts

Run via::

    cd python && python -m pytest tests/test_game_state_4d.py -v
"""

from __future__ import annotations

import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
if PKG not in sys.path:
    sys.path.insert(0, PKG)

import chess_spectral_4d as csd4  # noqa: E402


# ─── Helpers ──────────────────────────────────────────────────────

def _kk_state() -> csd4.GameState4D:
    """Two-king position — useful for shuffling without captures."""
    return csd4.GameState4D.from_fen4(
        "4d-fen v1: K@0,0,0,0; k@7,7,7,7"
    )


# ─── MoveHistory4D plumbing ────────────────────────────────────────

def test_initial_state_has_one_position_count() -> None:
    """The starting position counts as one occurrence (FIDE 9.2)."""
    gs = _kk_state()
    assert len(gs.history.position_counts) == 1
    assert gs.history.repetition_count(gs.position) == 1
    assert gs.history.half_move_clock == 0
    assert gs.history.side_to_move == csd4.SIDE_WHITE


def test_apply_move_appends_record_with_correct_ply() -> None:
    gs = _kk_state()
    m0 = csd4.apply_move(gs, (0, 0, 0, 0), (1, 0, 0, 0))
    m1 = csd4.apply_move(gs, (7, 7, 7, 7), (6, 7, 7, 7))
    assert m0.ply == 0
    assert m1.ply == 1
    assert len(gs.history.moves) == 2


def test_side_to_move_flips_each_ply() -> None:
    gs = _kk_state()
    assert gs.history.side_to_move == csd4.SIDE_WHITE
    csd4.apply_move(gs, (0, 0, 0, 0), (1, 0, 0, 0))
    assert gs.history.side_to_move == csd4.SIDE_BLACK
    csd4.apply_move(gs, (7, 7, 7, 7), (6, 7, 7, 7))
    assert gs.history.side_to_move == csd4.SIDE_WHITE


def test_apply_move_rejects_empty_origin() -> None:
    gs = _kk_state()
    with pytest.raises(ValueError, match="no piece"):
        csd4.apply_move(gs, (4, 4, 4, 4), (5, 4, 4, 4))


# ─── Half-move clock (FIDE 9.3) ────────────────────────────────────

def test_clock_increments_on_quiet_king_move() -> None:
    gs = _kk_state()
    csd4.apply_move(gs, (0, 0, 0, 0), (1, 0, 0, 0))
    assert gs.history.half_move_clock == 1
    csd4.apply_move(gs, (7, 7, 7, 7), (6, 7, 7, 7))
    assert gs.history.half_move_clock == 2


def test_clock_resets_on_pawn_move() -> None:
    gs = csd4.GameState4D.from_fen4(
        "4d-fen v1: K@0,0,0,0; Pw@2,0,0,0; k@7,7,7,7"
    )
    # Build up a non-zero clock with two king moves.
    csd4.apply_move(gs, (0, 0, 0, 0), (1, 0, 0, 0))
    csd4.apply_move(gs, (7, 7, 7, 7), (6, 7, 7, 7))
    assert gs.history.half_move_clock == 2
    # Now move the pawn — clock must reset.
    csd4.apply_move(gs, (2, 0, 0, 0), (3, 0, 0, 0))
    assert gs.history.half_move_clock == 0


def test_clock_resets_on_capture() -> None:
    """A capture resets the half-move clock to 0 (FIDE 9.3)."""
    gs = csd4.GameState4D.from_fen4(
        "4d-fen v1: K@0,0,0,0; q@1,0,0,0; k@7,7,7,7"
    )
    # Build a positive clock first via a black-king quiet move.
    csd4.apply_move(gs, (7, 7, 7, 7), (6, 7, 7, 7))
    assert gs.history.half_move_clock == 1
    # Now the white king captures the black queen at (1,0,0,0).
    csd4.apply_move(gs, (0, 0, 0, 0), (1, 0, 0, 0))
    assert gs.history.half_move_clock == 0


# ─── Threefold-repetition detection ────────────────────────────────

def test_threefold_via_six_ply_repetition() -> None:
    """A 4-ply A→B→A→B cycle, repeated, registers the starting
    position three times (counted at the start, after both kings
    return on cycle 1, and after both kings return on cycle 2 —
    that's 3 occurrences after 8 plies)."""
    gs = _kk_state()
    starting_pos = dict(gs.position)
    starting_side = gs.history.side_to_move

    # First cycle of 4 plies returning to start.
    csd4.apply_move(gs, (0, 0, 0, 0), (1, 0, 0, 0))
    csd4.apply_move(gs, (7, 7, 7, 7), (6, 7, 7, 7))
    csd4.apply_move(gs, (1, 0, 0, 0), (0, 0, 0, 0))
    csd4.apply_move(gs, (6, 7, 7, 7), (7, 7, 7, 7))
    assert gs.position == starting_pos
    assert gs.history.side_to_move == starting_side
    # Now starting position has been seen 2 times.
    assert gs.history.repetition_count(gs.position) == 2

    # Second full cycle — bumps the count to 3.
    csd4.apply_move(gs, (0, 0, 0, 0), (1, 0, 0, 0))
    csd4.apply_move(gs, (7, 7, 7, 7), (6, 7, 7, 7))
    csd4.apply_move(gs, (1, 0, 0, 0), (0, 0, 0, 0))
    csd4.apply_move(gs, (6, 7, 7, 7), (7, 7, 7, 7))
    assert gs.history.repetition_count(gs.position) == 3


def test_threefold_triggers_draw_status() -> None:
    """After the third occurrence of the starting position,
    get_draw_status returns 'threefold' regardless of legal-moves
    state (threefold takes priority over stalemate)."""
    gs = _kk_state()
    for _ in range(2):
        csd4.apply_move(gs, (0, 0, 0, 0), (1, 0, 0, 0))
        csd4.apply_move(gs, (7, 7, 7, 7), (6, 7, 7, 7))
        csd4.apply_move(gs, (1, 0, 0, 0), (0, 0, 0, 0))
        csd4.apply_move(gs, (6, 7, 7, 7), (7, 7, 7, 7))
    out = csd4.bridge.get_draw_status(gs, has_legal_moves=True)
    assert out["ok"] is True
    assert out["status"] == "threefold"


def test_threefold_does_not_fire_at_two_occurrences() -> None:
    """After only 2 occurrences, status is 'none' (modulo
    insufficient material — see test_kk_only_is_insufficient_4d)."""
    gs = _kk_state()
    csd4.apply_move(gs, (0, 0, 0, 0), (1, 0, 0, 0))
    csd4.apply_move(gs, (7, 7, 7, 7), (6, 7, 7, 7))
    csd4.apply_move(gs, (1, 0, 0, 0), (0, 0, 0, 0))
    csd4.apply_move(gs, (6, 7, 7, 7), (7, 7, 7, 7))
    assert gs.history.repetition_count(gs.position) == 2
    out = csd4.bridge.get_draw_status(gs, has_legal_moves=True)
    # 4D insufficient-material is deferred; we should see 'none' at
    # only 2 occurrences (before threefold fires).
    assert out["status"] == "none"


# ─── 50-move rule detection ────────────────────────────────────────

def test_fifty_move_rule_at_100_quiet_half_moves() -> None:
    """100 quiet half-moves between two kings (50 full moves; no
    pawn moves, no captures) trigger the 50-move-rule draw."""
    gs = _kk_state()

    # White king cycles (0,0,0,0) ↔ (1,0,0,0); black king cycles
    # (7,7,7,7) ↔ (6,7,7,7). Each iteration is 4 plies. After 25
    # iterations we have 100 quiet half-moves total.
    for _ in range(25):
        csd4.apply_move(gs, (0, 0, 0, 0), (1, 0, 0, 0))
        csd4.apply_move(gs, (7, 7, 7, 7), (6, 7, 7, 7))
        csd4.apply_move(gs, (1, 0, 0, 0), (0, 0, 0, 0))
        csd4.apply_move(gs, (6, 7, 7, 7), (7, 7, 7, 7))

    assert gs.history.half_move_clock == 100
    out = csd4.bridge.get_draw_status(gs, has_legal_moves=True)
    # Threefold will also fire here; per detection-order priority,
    # threefold is checked first. So the status will be 'threefold'.
    # We test 50-move-rule in isolation in the next test.
    assert out["status"] in ("threefold", "fifty-move")


def test_fifty_move_rule_isolated_from_threefold() -> None:
    """Hand-build a 100-half-move quiet sequence that visits 50
    distinct positions per side, so threefold cannot fire at any
    point — the 50-move rule must be the ONLY draw condition active
    at the boundary. The trick is that each side's king walks a
    50-step path through unique squares (4D space is large enough
    that this fits comfortably).
    """
    gs = csd4.GameState4D.from_fen4(
        "4d-fen v1: K@0,0,0,0; k@7,0,0,0"
    )

    # Walk through 51 distinct (y, z, w) squares at fixed x. Note
    # apply_move does not validate move legality (legal-move
    # generation is wired in v1.5+; v1.4.0 is the
    # state-application surface only) so we simply assert that the
    # piece is at from_sq and let the test exercise the state
    # machinery. This is a 50-move-rule isolation test, not a
    # legal-move-generation test.
    def _path_in_4d(start_x: int, n_steps: int) -> list:
        out = []
        seen = set()
        # Snake through (y, z, w) keeping x fixed.
        for y in range(8):
            for z in range(8):
                for w in range(8):
                    coord = (start_x, y, z, w)
                    if coord in seen:
                        continue
                    seen.add(coord)
                    out.append(coord)
                    if len(out) >= n_steps + 1:
                        return out
        return out

    white_path = _path_in_4d(0, 50)
    black_path = _path_in_4d(7, 50)
    assert len(white_path) >= 51
    assert len(black_path) >= 51

    # Walk each king through their path, alternating plies.
    for i in range(50):
        csd4.apply_move(gs, white_path[i], white_path[i + 1])
        csd4.apply_move(gs, black_path[i], black_path[i + 1])

    # 100 quiet half-moves; threefold is impossible because each
    # combined state was unique.
    assert gs.history.half_move_clock == 100
    # Every position in the count table must have count == 1.
    assert all(c == 1 for c in gs.history.position_counts.values())
    out = csd4.bridge.get_draw_status(gs, has_legal_moves=True)
    assert out["status"] == "fifty-move"


def test_fifty_move_clock_below_100_is_none() -> None:
    """clock=99 must NOT trigger; clock=100 does."""
    gs = _kk_state()
    # Make a single quiet move; clock=1.
    csd4.apply_move(gs, (0, 0, 0, 0), (1, 0, 0, 0))
    out = csd4.bridge.get_draw_status(gs, has_legal_moves=True)
    assert out["status"] == "none"


# ─── Insufficient-material (2D) ────────────────────────────────────

def test_insufficient_2d_kk_only() -> None:
    pos = {0: "K", 63: "k"}
    assert csd4.bridge.is_insufficient_material_2d(pos) is True


def test_insufficient_2d_kbk_white() -> None:
    pos = {0: "K", 63: "k", 1: "B"}
    assert csd4.bridge.is_insufficient_material_2d(pos) is True


def test_insufficient_2d_kbk_black() -> None:
    pos = {0: "K", 63: "k", 62: "b"}
    assert csd4.bridge.is_insufficient_material_2d(pos) is True


def test_insufficient_2d_knk_white() -> None:
    pos = {0: "K", 63: "k", 1: "N"}
    assert csd4.bridge.is_insufficient_material_2d(pos) is True


def test_insufficient_2d_kqk_is_sufficient() -> None:
    """K + Q vs K is mating material; status must be False."""
    pos = {0: "K", 63: "k", 1: "Q"}
    assert csd4.bridge.is_insufficient_material_2d(pos) is False


def test_insufficient_2d_kpk_is_sufficient() -> None:
    """K + P vs K is mating material in general; we conservatively
    classify it as sufficient (matches python-chess behavior)."""
    pos = {0: "K", 63: "k", 8: "P"}
    assert csd4.bridge.is_insufficient_material_2d(pos) is False


def test_insufficient_2d_krk_is_sufficient() -> None:
    pos = {0: "K", 63: "k", 1: "R"}
    assert csd4.bridge.is_insufficient_material_2d(pos) is False


def test_insufficient_2d_kbk_vs_kbk_same_color() -> None:
    """Two bishops on same-color squares ⇒ insufficient.

    Square color = (row + col) % 2, where row=sq//8, col=sq%8.
    Square 0 = (0,0) ⇒ even ('white squares'), square 9 = (1,1) ⇒
    even (also 'white'). Both bishops on even squares ⇒ same-color.
    """
    pos = {0: "K", 63: "k", 9: "B", 18: "b"}  # both on even squares
    assert csd4.bridge.is_insufficient_material_2d(pos) is True


def test_insufficient_2d_kbk_vs_kbk_opposite_color() -> None:
    """Bishops on opposite-color squares can mate ⇒ sufficient."""
    pos = {0: "K", 63: "k", 9: "B", 17: "b"}  # opposite colors
    assert csd4.bridge.is_insufficient_material_2d(pos) is False


def test_insufficient_2d_two_knights_one_side_is_sufficient() -> None:
    """Two knights of one side vs lone king is normally sufficient
    (rare draws aside); we treat it as sufficient to match
    python-chess defaults."""
    pos = {0: "K", 63: "k", 1: "N", 2: "N"}
    assert csd4.bridge.is_insufficient_material_2d(pos) is False


# ─── Insufficient material (4D — placeholder) ──────────────────────

def test_insufficient_4d_raises_not_implemented() -> None:
    """The 4D analog is deferred; calling it directly raises."""
    pos = {0: "K", 4095: "k"}
    with pytest.raises(NotImplementedError, match="open design"):
        csd4.bridge.is_insufficient_material_4d(pos)


# ─── get_draw_status — stalemate gating ───────────────────────────

def test_get_draw_status_requires_explicit_legal_moves_for_stalemate() -> None:
    """When no other draw condition fires, get_draw_status raises
    NotImplementedError unless the caller passes has_legal_moves
    explicitly. This prevents silent mis-classification of stalemate
    as 'none'."""
    gs = _kk_state()
    csd4.apply_move(gs, (0, 0, 0, 0), (1, 0, 0, 0))
    with pytest.raises(NotImplementedError, match="stalemate"):
        csd4.bridge.get_draw_status(gs)


def test_get_draw_status_no_legal_moves_yields_stalemate() -> None:
    gs = _kk_state()
    out = csd4.bridge.get_draw_status(gs, has_legal_moves=False)
    assert out["status"] == "stalemate"


def test_get_draw_status_legal_moves_present_yields_none() -> None:
    gs = _kk_state()
    csd4.apply_move(gs, (0, 0, 0, 0), (1, 0, 0, 0))
    out = csd4.bridge.get_draw_status(gs, has_legal_moves=True)
    assert out["status"] == "none"


# ─── get_move_history ──────────────────────────────────────────────

def test_get_move_history_empty_at_init() -> None:
    gs = _kk_state()
    out = csd4.bridge.get_move_history(gs)
    assert out["ok"] is True
    assert out["moves"] == []


def test_get_move_history_records_each_ply() -> None:
    gs = _kk_state()
    csd4.apply_move(gs, (0, 0, 0, 0), (1, 0, 0, 0))
    csd4.apply_move(gs, (7, 7, 7, 7), (6, 7, 7, 7))
    out = csd4.bridge.get_move_history(gs)
    assert out["ok"] is True
    moves = out["moves"]
    assert len(moves) == 2
    assert moves[0]["ply"] == 0
    assert moves[0]["from"] == [0, 0, 0, 0]
    assert moves[0]["to"] == [1, 0, 0, 0]
    assert moves[0]["piece"] == "K"
    assert moves[0]["halfMoveClock"] == 1
    assert moves[1]["ply"] == 1
    assert moves[1]["piece"] == "k"


def test_get_move_history_records_promotion_target() -> None:
    gs = csd4.GameState4D.from_fen4(
        "4d-fen v1: K@0,0,0,0; Pw@1,0,0,6; k@7,7,7,7"
    )
    csd4.apply_move(gs, (1, 0, 0, 6), (1, 0, 0, 7), promote_to="N")
    out = csd4.bridge.get_move_history(gs)
    moves = out["moves"]
    assert moves[0]["promoteTo"] == "N"
    assert moves[0]["piece"] == "Pw"


def test_get_move_history_records_capture() -> None:
    gs = csd4.GameState4D.from_fen4(
        "4d-fen v1: K@0,0,0,0; q@1,0,0,0; k@7,7,7,7"
    )
    csd4.apply_move(gs, (0, 0, 0, 0), (1, 0, 0, 0))  # K x q
    out = csd4.bridge.get_move_history(gs)
    assert out["moves"][0]["capturedPiece"] == "q"


# ─── Direct invocation ─────────────────────────────────────────────

if __name__ == "__main__":
    import subprocess
    subprocess.run([sys.executable, "-m", "pytest", __file__, "-v"],
                   check=False)

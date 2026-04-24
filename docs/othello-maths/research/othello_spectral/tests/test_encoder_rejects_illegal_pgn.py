"""Encoder-pipeline illegal-move rejection tests.

Answers the question: "if someone hands the encoder a PGN with an
illegal move, does the pipeline catch it?"

The answer is yes — via `othello_pgn_loader.replay()`, which uses
`OthelloBoard.legal_moves()` to validate each ply before `.play()`.
`SheafMoveOperator` is not on the validation path of the CLI but is
guaranteed consistent with `OthelloBoard` by the byte-for-byte parity
test in test_move_operator.py::test_random_game_parity.

Fixture: tests/fixtures/illegal_move_corpus.pgn
  Game 0 — illegal move at ply 5 (a1 from d3-c5-f6-f5, no flank)
  Game 1 — illegal move at ply 2 (d4, occupied cell from start)
  Game 2 — fully legal 10-ply control

Run:
  cd docs/othello-maths/research
  python -m othello_spectral.tests.test_encoder_rejects_illegal_pgn
"""

from __future__ import annotations

import sys
from pathlib import Path

_RESEARCH_DIR = Path(__file__).resolve().parent.parent.parent
if str(_RESEARCH_DIR) not in sys.path:
    sys.path.insert(0, str(_RESEARCH_DIR))

import othello_pgn_loader as pgn_loader  # noqa: E402
from othello_spectral.move_operator import SheafMoveOperator  # noqa: E402

_FIXTURE = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "illegal_move_corpus.pgn"
)


def _load_fixture() -> list[dict]:
    assert _FIXTURE.exists(), f"fixture missing: {_FIXTURE}"
    games = pgn_loader.parse_pgn_file(_FIXTURE)
    assert len(games) == 3, (
        f"fixture should hold 3 games; got {len(games)}"
    )
    return games


def test_fixture_parses_three_games() -> None:
    games = _load_fixture()
    assert len(games) == 3


def test_game0_illegal_nonflanking_move_rejected() -> None:
    """Game 0: move 5 = a1 from a state where a1 flanks nothing.
    replay() must raise ValueError mentioning 'not legal'."""
    games = _load_fixture()
    try:
        pgn_loader.replay(games[0]["moves"])
    except ValueError as exc:
        assert "not legal" in str(exc), (
            f"expected 'not legal' in error, got: {exc}"
        )
        return
    raise AssertionError(
        "game 0 (illegal a1 move) should have been rejected by "
        "replay(), but no exception was raised"
    )


def test_game1_illegal_occupied_cell_rejected() -> None:
    """Game 1: move 2 = d4, an occupied cell from the start.
    replay() must raise ValueError."""
    games = _load_fixture()
    try:
        pgn_loader.replay(games[1]["moves"])
    except ValueError as exc:
        assert "not legal" in str(exc), (
            f"expected 'not legal' in error, got: {exc}"
        )
        return
    raise AssertionError(
        "game 1 (move onto occupied d4) should have been rejected "
        "by replay(), but no exception was raised"
    )


def test_game2_control_replays_cleanly() -> None:
    """Game 2: verified-legal 10-ply sequence.  Must replay without
    raising; without this positive control, an 'every replay raises'
    regression would silently pass the two preceding tests."""
    games = _load_fixture()
    _, states, log = pgn_loader.replay(games[2]["moves"])
    # 10 plies + initial state = 11 states minimum
    assert len(states) >= 11, (
        f"control game should produce >= 11 states; got {len(states)}"
    )
    # No inserted passes in this smooth opening
    n_passes = sum(1 for m in log if m["is_pass"])
    assert n_passes == 0, (
        f"control game should have 0 passes; got {n_passes}"
    )


def test_sheaf_operator_agrees_on_rejection() -> None:
    """Independent validation path: SheafMoveOperator.is_legal() must
    also return False on the exact illegal moves embedded in the
    fixture.  Confirms the two validators agree on failure cases
    (test_move_operator.py already confirms they agree on successes)."""
    op = SheafMoveOperator()

    # Reconstruct the game-0 state right before the illegal a1 (move 5):
    # plies 1..4 = d3, c5, f6, f5 (all legal).
    from othello_utils import OthelloBoard
    bb = OthelloBoard()
    for mv in ["d3", "c5", "f6", "f5"]:
        bb.play(pgn_loader.move_to_idx(mv))
    a1_idx = pgn_loader.move_to_idx("a1")
    assert not op.is_legal(bb.state, a1_idx, bb.side_to_move), (
        "SheafMoveOperator.is_legal(a1) should be False in the "
        "game-0 pre-illegal-move state"
    )
    assert op.apply(bb.state, a1_idx, bb.side_to_move) is None, (
        "SheafMoveOperator.apply(a1) should return None (illegal)"
    )

    # Game 1 pre-illegal: just the starting position, d4 is occupied.
    bb2 = OthelloBoard()
    bb2.play(pgn_loader.move_to_idx("d3"))  # black move 1
    d4_idx = pgn_loader.move_to_idx("d4")
    assert not op.is_legal(bb2.state, d4_idx, bb2.side_to_move), (
        "SheafMoveOperator.is_legal(d4) on an occupied cell must "
        "return False"
    )


ALL_TESTS = [
    test_fixture_parses_three_games,
    test_game0_illegal_nonflanking_move_rejected,
    test_game1_illegal_occupied_cell_rejected,
    test_game2_control_replays_cleanly,
    test_sheaf_operator_agrees_on_rejection,
]


if __name__ == "__main__":
    failures = 0
    for fn in ALL_TESTS:
        try:
            fn()
            print(f"PASS  {fn.__name__}")
        except AssertionError as exc:
            print(f"FAIL  {fn.__name__}: {exc}")
            failures += 1
        except Exception as exc:  # noqa: BLE001
            print(
                f"ERROR {fn.__name__}: {type(exc).__name__}: {exc}"
            )
            failures += 1
    if failures:
        print(f"\n{failures} failures")
        sys.exit(1)
    print("\nall illegal-PGN rejection tests passed")

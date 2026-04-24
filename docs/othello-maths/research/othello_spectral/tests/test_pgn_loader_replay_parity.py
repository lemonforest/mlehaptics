"""Parity test: pgn_loader.replay() vs pgn_loader.replay_sheaf().

The encoder defaults to the sheaf-backed replay path since v0.3.2.
This test locks in the invariant that the two replay implementations
produce identical state sequences for every game in a representative
corpus, so the speedup is a pure win -- no silent divergence.

If this test ever fails, the encoder's sheaf replay has drifted from
OthelloBoard.play() semantics and every downstream analysis is
suspect until resolved.

Fixture: the illegal-move corpus (2 intentionally bad games + 1
legal control).  Good moves must replay identically; bad moves must
raise from BOTH paths.

Run:
  cd docs/othello-maths/research
  python -m othello_spectral.tests.test_pgn_loader_replay_parity
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

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


def _states_equal(a: list, b: list) -> bool:
    if len(a) != len(b):
        return False
    for x, y in zip(a, b):
        if not np.array_equal(x, y):
            return False
    return True


def test_control_game_identical_state_sequence() -> None:
    """The legal 10-ply control must replay to identical states
    under both engines."""
    games = pgn_loader.parse_pgn_file(_FIXTURE)
    legal_game = games[2]
    _, s_old, log_old = pgn_loader.replay(legal_game["moves"])
    _, s_new, log_new = pgn_loader.replay_sheaf(
        legal_game["moves"], SheafMoveOperator()
    )
    assert _states_equal(s_old, s_new), (
        "replay() and replay_sheaf() diverged on the legal "
        "control game -- encoder will now silently produce "
        "different .spectralz output depending on replay engine"
    )
    # Move-logs should also match in structure (indices + pass flags)
    assert len(log_old) == len(log_new)
    for a, b in zip(log_old, log_new):
        assert a["idx"] == b["idx"], f"idx mismatch: {a} vs {b}"
        assert a["is_pass"] == b["is_pass"], (
            f"is_pass mismatch: {a} vs {b}"
        )
        assert a["side"] == b["side"], f"side mismatch: {a} vs {b}"


def test_both_engines_reject_illegal_games() -> None:
    """Both replay engines must raise ValueError('... not legal ...')
    on the two illegal fixture games.  Any divergence here is a
    correctness bug."""
    games = pgn_loader.parse_pgn_file(_FIXTURE)
    op = SheafMoveOperator()
    for gi in (0, 1):
        old_raised = False
        new_raised = False
        try:
            pgn_loader.replay(games[gi]["moves"])
        except ValueError as exc:
            assert "not legal" in str(exc)
            old_raised = True
        try:
            pgn_loader.replay_sheaf(games[gi]["moves"], op)
        except ValueError as exc:
            assert "not legal" in str(exc)
            new_raised = True
        assert old_raised and new_raised, (
            f"game {gi}: divergent behaviour "
            f"(replay raised={old_raised}, "
            f"replay_sheaf raised={new_raised})"
        )


def test_random_corpus_identical() -> None:
    """Use the operator's random-game generator to create 10
    synthetic games and verify replay engines stay in lock-step.

    This is a dynamic counterpart to the fixture-driven tests:
    anything that the SheafMoveOperator accepts must also be
    accepted (and produce identical states) by OthelloBoard.
    """
    rng = np.random.default_rng(2026)
    from othello_utils import OthelloBoard

    op = SheafMoveOperator()
    for game_i in range(10):
        # Play a random game using OthelloBoard, record the move
        # string sequence so we can replay it through both engines.
        bb = OthelloBoard()
        moves: list[str] = []
        for _ in range(120):
            if bb.is_terminal():
                break
            legal = bb.legal_moves()
            if not legal:
                bb.play(None)
                moves.append("pass")
                continue
            m = int(rng.choice(legal))
            moves.append(pgn_loader.idx_to_move(m))
            bb.play(m)
        _, s_old, _ = pgn_loader.replay(moves)
        _, s_new, _ = pgn_loader.replay_sheaf(moves, op)
        assert _states_equal(s_old, s_new), (
            f"random game {game_i}: state sequences diverged "
            f"(len {len(s_old)} vs {len(s_new)})"
        )


ALL_TESTS = [
    test_control_game_identical_state_sequence,
    test_both_engines_reject_illegal_games,
    test_random_corpus_identical,
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
    print("\nall replay-parity tests passed")

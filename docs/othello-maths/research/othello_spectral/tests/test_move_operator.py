"""Parity tests for SheafMoveOperator vs OthelloBoard.

Ensures the sheaf-derived move operator produces exactly the same
post-move state as the reference OthelloBoard.play().

Run:
  cd docs/othello-maths/research
  python -m othello_spectral.tests.test_move_operator
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np


_RESEARCH_DIR = Path(__file__).resolve().parent.parent.parent
if str(_RESEARCH_DIR) not in sys.path:
    sys.path.insert(0, str(_RESEARCH_DIR))

from othello_spectral.move_operator import SheafMoveOperator  # noqa: E402
from othello_utils import BLACK, OthelloBoard  # noqa: E402


def _starting_state() -> np.ndarray:
    s = np.zeros(64, dtype=int)
    s[3 * 8 + 3] = -1
    s[3 * 8 + 4] = +1
    s[4 * 8 + 3] = +1
    s[4 * 8 + 4] = -1
    return s


def test_starting_legal_moves_match_othelloboard() -> None:
    bb = OthelloBoard()
    ref_legal = set(bb.legal_moves())
    op = SheafMoveOperator()
    got_legal = set(op.legal_moves(bb.state, bb.side_to_move))
    assert got_legal == ref_legal, (
        f"legal moves mismatch at starting position: "
        f"ref={sorted(ref_legal)} got={sorted(got_legal)}"
    )


def test_starting_flip_count() -> None:
    """At the standard start, each of the 4 legal moves flips
    exactly 1 disc (single-bracket flank)."""
    bb = OthelloBoard()
    op = SheafMoveOperator()
    for m in bb.legal_moves():
        assert op.flip_count(bb.state, m, bb.side_to_move) == 1, (
            f"starting-position move {m} should flip 1 disc"
        )


def test_random_game_parity() -> None:
    """Play 20 random games, at each ply verify our operator
    matches OthelloBoard.play() byte-for-byte."""
    rng = np.random.default_rng(17)
    op = SheafMoveOperator()
    for game in range(20):
        bb = OthelloBoard()
        for _ply in range(100):
            if bb.is_terminal():
                break
            legal = bb.legal_moves()
            if not legal:
                bb.play(None)
                continue
            move = int(rng.choice(legal))
            side = bb.side_to_move
            # Our operator
            got_post = op.apply(bb.state, move, side)
            assert got_post is not None, f"legal move {move} rejected"
            # Reference
            bb.play(move)
            ref_post = bb.state.copy()
            assert np.array_equal(got_post, ref_post), (
                f"game {game} move {move}: mismatch between "
                f"SheafMoveOperator and OthelloBoard.play() — "
                f"{int(np.sum(got_post != ref_post))} cells differ"
            )


def test_illegal_moves_return_none() -> None:
    """Any empty cell NOT adjacent to an opponent-flank is illegal."""
    bb = OthelloBoard()
    op = SheafMoveOperator()
    ref_legal = set(bb.legal_moves())
    for m in range(64):
        if bb.state[m] != 0:
            continue
        if m not in ref_legal:
            result = op.apply(bb.state, m, bb.side_to_move)
            assert result is None, (
                f"move {m} should be illegal, got post-state"
            )


def test_flip_count_vector_matches() -> None:
    """flip_count_vector returns the right count for every cell."""
    bb = OthelloBoard()
    op = SheafMoveOperator()
    vec = op.flip_count_vector(bb.state, bb.side_to_move)
    assert vec.shape == (64,)
    ref_legal = set(bb.legal_moves())
    for m in range(64):
        if m in ref_legal:
            assert vec[m] > 0, f"legal move {m} has 0 flip count"
        else:
            assert vec[m] == 0, f"illegal move {m} has nonzero count"


def test_encode_post_move_matches_direct_encode() -> None:
    """encode_post_move(state, move) == encode_768(apply(state, move))."""
    from othello_spectral import encode_768
    bb = OthelloBoard()
    op = SheafMoveOperator()
    for m in bb.legal_moves():
        enc_via_op = op.encode_post_move(bb.state, m, bb.side_to_move)
        post_state = op.apply(bb.state, m, bb.side_to_move)
        enc_direct = encode_768(post_state)
        assert np.array_equal(enc_via_op, enc_direct), (
            f"encode_post_move({m}) disagrees with encode_768(post)"
        )


ALL_TESTS = [
    test_starting_legal_moves_match_othelloboard,
    test_starting_flip_count,
    test_random_game_parity,
    test_illegal_moves_return_none,
    test_flip_count_vector_matches,
    test_encode_post_move_matches_direct_encode,
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
            print(f"ERROR {fn.__name__}: {type(exc).__name__}: {exc}")
            failures += 1
    if failures:
        print(f"\n{failures} failures")
        sys.exit(1)
    print("\nall move-operator tests passed")

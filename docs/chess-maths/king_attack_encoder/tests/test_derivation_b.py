"""Unit tests for Derivation B (D4 decomposition of attack adjacency)."""
import sys
import time
import unittest
from pathlib import Path

import chess
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from king_attack_encoder.derivation_b_d4 import (  # noqa: E402
    D4_IRREPS, attack_row_sum_signal,
    derivation_b_channels, derivation_b_similarity,
    derivation_b_similarity_concat,
)


class TestDerivationB(unittest.TestCase):
    def test_channels_shape_and_irrep_coverage(self):
        board = chess.Board()
        ch = derivation_b_channels(board)
        self.assertEqual(set(ch.keys()), set(D4_IRREPS))
        for name, arr in ch.items():
            self.assertEqual(arr.shape, (64,),
                             f"{name} has shape {arr.shape}")
            self.assertEqual(arr.dtype, np.float64)

    def test_signal_row_sum_zero_when_only_mover(self):
        """Only the mover's king on the board -- no opponent attacks,
        so the row-sum signal is identically zero and every irrep
        projection is zero too."""
        board = chess.Board("8/8/8/8/8/8/8/4K3 w - - 0 1")
        signal = attack_row_sum_signal(board)
        np.testing.assert_array_equal(signal, np.zeros(64))
        ch = derivation_b_channels(board)
        for name, arr in ch.items():
            np.testing.assert_allclose(arr, np.zeros(64), atol=1e-12,
                                       err_msg=f"{name} not zero")

    def test_determinism(self):
        board = chess.Board()
        a = derivation_b_channels(board)
        b = derivation_b_channels(board)
        for name in D4_IRREPS:
            np.testing.assert_array_equal(a[name], b[name])

    def test_similarity_in_unit_interval(self):
        board = chess.Board()
        sims = derivation_b_similarity(board, chess.Move.from_uci("e2e4"))
        self.assertEqual(set(sims.keys()), set(D4_IRREPS))
        for name, s in sims.items():
            self.assertGreaterEqual(s, -1.0 - 1e-9,
                                    f"{name}={s}")
            self.assertLessEqual(s, 1.0 + 1e-9,
                                 f"{name}={s}")

    def test_concat_similarity_in_unit_interval(self):
        board = chess.Board()
        s = derivation_b_similarity_concat(
            board, chess.Move.from_uci("g1f3"))
        self.assertGreaterEqual(s, -1.0 - 1e-9)
        self.assertLessEqual(s, 1.0 + 1e-9)

    def test_concat_matches_weighted_irrep_average_when_all_equal_norm(self):
        """Sanity check: concatenated cosine is a norm-weighted mean
        of per-irrep cosines. When all irrep vectors share the same
        norm, it should equal the plain average. Not a strict identity
        because irrep norms differ in general; this test just checks
        the concat is in the convex hull of the per-irrep values."""
        board = chess.Board()
        mv = chess.Move.from_uci("e2e4")
        per = derivation_b_similarity(board, mv)
        concat = derivation_b_similarity_concat(board, mv)
        values = list(per.values())
        lo = min(values)
        hi = max(values)
        self.assertGreaterEqual(concat, lo - 1e-9)
        self.assertLessEqual(concat, hi + 1e-9)

    def test_performance_budget(self):
        board = chess.Board()
        derivation_b_channels(board)  # warmup
        t0 = time.perf_counter()
        for _ in range(10):
            derivation_b_channels(board)
        elapsed_ms = (time.perf_counter() - t0) * 1000 / 10
        self.assertLess(elapsed_ms, 10.0,
                        f"per-call {elapsed_ms:.2f} ms exceeds budget")

    def test_similarity_concat_uses_mover_perspective_after_move(self):
        """Regression test for the §12.7.1.1 turn-flip fix.

        In the test FEN, after Qe4d4 the white king on e1 becomes
        attacked by the black rook on e5 through the cleared e-file.
        Derivation B's attack_adjacency must compute "opponent of
        mover" after the move -- i.e., black's attacks -- not
        "opponent of new side-to-move" which would be white's
        outgoing attacks.

        The reference below computes the concat cosine with an
        explicit turn-flip; the wrapper must match bit-identically.
        """
        board = chess.Board("k7/8/8/4r3/4Q3/8/8/4K3 w - - 0 1")
        move = chess.Move.from_uci("e4d4")

        board_after = board.copy(stack=False)
        board_after.push(move)
        board_after.turn = not board_after.turn
        before = derivation_b_channels(board)
        after = derivation_b_channels(board_after)
        b_concat = np.concatenate([before[i] for i in D4_IRREPS])
        a_concat = np.concatenate([after[i] for i in D4_IRREPS])
        nb = float(np.linalg.norm(b_concat))
        na = float(np.linalg.norm(a_concat))
        if nb > 0 and na > 0:
            expected = float(np.dot(b_concat, a_concat) / (nb * na))
        else:
            expected = 0.0

        actual = derivation_b_similarity_concat(board, move)
        self.assertAlmostEqual(
            actual, expected, places=10,
            msg=("derivation_b_similarity_concat must flip "
                 "board.turn on the post-move board."))


if __name__ == "__main__":
    unittest.main()

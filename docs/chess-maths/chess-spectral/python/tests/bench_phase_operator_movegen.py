"""Diagnostic benchmark: ALU-native phase-operator move-gen vs
python-chess pseudo-legal-moves vs Solution B (Board-fronted).

Not a competitive benchmark — python-chess's pseudo_legal_moves is
implemented as Cython-accelerated bitboard operations and will win
raw speed by ~50× against any pure-Python phase-operator path. The
purpose of this benchmark is **diagnostic**:

  1. Document the absolute cost of phase_only_pseudo_legal_moves so
     Pyodide / WASM / non-Python downstream consumers have a
     baseline expectation.
  2. Confirm phase_only_pseudo_legal_moves matches the existing
     occupation_aware_moves_b's per-piece cost (since they share
     the underlying logic; the only difference is the input
     adapter).
  3. Surface any per-position-shape variance (opening / middlegame /
     endgame).

Usage:
    cd docs/chess-maths/chess-spectral/python
    python tests/bench_phase_operator_movegen.py
    python tests/bench_phase_operator_movegen.py --iters 5000
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG_DIR = HERE.parent
if str(PKG_DIR) not in sys.path:
    sys.path.insert(0, str(PKG_DIR))


def _benchmark_corpus() -> "list[tuple[str, str]]":
    """Three position shapes: opening, middlegame, endgame.

    Returned as ``[(label, fen), ...]``. Each shape stresses a
    different phase-operator path (sliders dominant, mixed, sparse).
    """
    return [
        ("opening (startpos)",
         "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
        ("middlegame (Italian, both castled)",
         "r1b2rk1/pp2bppp/2nppn2/q1p5/2P5/2N1PN2/PPQ1BPPP/2KR1B1R w - - 4 11"),
        ("endgame (K+R vs K)",
         "8/8/8/4k3/8/8/4R3/4K3 w - - 0 1"),
    ]


def _bench_one_call(fn, iters: int) -> float:
    """Time `fn` over `iters` calls; return mean seconds per call."""
    # Warm up: a couple calls to trigger any one-shot setup.
    for _ in range(3):
        fn()
    t0 = time.perf_counter()
    for _ in range(iters):
        fn()
    t1 = time.perf_counter()
    return (t1 - t0) / iters


def _format_us(seconds: float) -> str:
    """Format a duration in seconds as a microsecond string."""
    return f"{seconds * 1e6:7.2f} µs"


def main() -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Diagnostic benchmark for ALU-native phase-operator move-gen "
            "vs python-chess pseudo-legal moves vs Solution B."
        ),
    )
    ap.add_argument("--iters", type=int, default=2000,
                    help="iterations per call site (default: 2000)")
    args = ap.parse_args()

    try:
        import chess
    except ImportError:
        print("python-chess required for this benchmark; install with "
              "`pip install chess`", file=sys.stderr)
        return 2

    from chess_spectral import (
        fen_to_pos,
        phase_only_pseudo_legal_moves,
        occupation_aware_moves_b,
    )

    print(f"\n=== Phase-operator move-gen benchmark (iters={args.iters}) ===\n")
    print(f"{'Position':<42} | {'pseudo_legal':>13} | "
          f"{'Solution B (per piece × 16)':>30} | {'ALU-native':>13}")
    print("-" * 105)

    for label, fen in _benchmark_corpus():
        board = chess.Board(fen)
        pos = fen_to_pos(fen)

        ep_file = None
        if board.ep_square is not None:
            ep_file = board.ep_square % 8
        side_white = (board.turn == chess.WHITE)

        # python-chess pseudo_legal_moves
        def _bench_chess():
            return list(board.pseudo_legal_moves)

        # Solution B (Board-fronted) — per-piece dispatch for the
        # mover's pieces. We use 16 piece evaluations per position
        # as a representative slice (the actual move enumerator
        # would call this for every piece on the board, but we
        # keep it bounded for a stable comparison).
        own_pieces = [
            (sq, piece) for sq, piece in board.piece_map().items()
            if piece.color == board.turn
        ]
        # Trim to first 16 to keep timing comparable across positions.
        own_pieces_bench = own_pieces[:16]

        def _bench_sol_b():
            for sq, piece in own_pieces_bench:
                r = chess.square_rank(sq)
                c = chess.square_file(sq)
                charge = +1 if piece.color == chess.WHITE else -1
                occupation_aware_moves_b(
                    board, piece.symbol(), r, c, charge)

        # ALU-native path (the new 1.11.0 entry point)
        def _bench_alu_native():
            return phase_only_pseudo_legal_moves(
                pos, side_to_move_white=side_white, ep_file=ep_file)

        t_chess = _bench_one_call(_bench_chess, args.iters)
        t_sol_b = _bench_one_call(_bench_sol_b, args.iters)
        t_alu = _bench_one_call(_bench_alu_native, args.iters)

        print(f"{label:<42} | {_format_us(t_chess):>13} | "
              f"{_format_us(t_sol_b):>30} | {_format_us(t_alu):>13}")

    print()
    print("Notes:")
    print("  * python-chess is Cython-accelerated bitboard. ALU-native is")
    print("    pure-Python integer arithmetic. ~50× ratio is expected.")
    print("  * Solution B column shows the same logic via the Board-fronted")
    print("    entry point. ALU-native should be comparable per-piece.")
    print("  * The value of ALU-native is *portability* (Pyodide / WASM /")
    print("    integer-only contexts), not raw speed against Cython.")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

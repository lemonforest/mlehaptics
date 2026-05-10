"""Integrated bench: time the full encode_4d_pure_phase before vs
after the FA_PAWN vectorize. Exposes both the loop and hybrid
implementations side-by-side via monkey-patching of the helper
buckets so a single benchmark run can compare them with identical
input data and identical surrounding-encoder work.

Run from chess-spectral/python:
  python tests/_bench_fa_pawn_integrated.py
"""
from __future__ import annotations

import random
import sys
import time
from typing import Dict, List, Tuple

import numpy as np

# Make the parent dir importable so chess_spectral resolves.
import os
HERE = os.path.dirname(os.path.abspath(__file__))
PARENT = os.path.dirname(HERE)
if PARENT not in sys.path:
    sys.path.insert(0, PARENT)

from chess_spectral.encoder_pure_phase_4d import (  # noqa: E402
    encode_4d_pure_phase, _build_quant_tables, CHANNEL_DIM,
)
from chess_spectral.encoder_4d import (  # noqa: E402
    _is_pawn, _piece_char, _pawn_axis,
)


_NONPAWN_CHARS: Tuple[str, ...] = (
    'N', 'B', 'R', 'Q', 'K', 'n', 'b', 'r', 'q', 'k',
)


def make_position(n_pawns: int, seed: int, *, n_other: int = 24,
                  n_squares: int = 4096) -> Dict[int, object]:
    rng = random.Random(seed)
    n_total = n_pawns + n_other
    squares = rng.sample(range(n_squares), n_total)
    pos: Dict[int, object] = {}
    pawn_squares = squares[:n_pawns]
    other_squares = squares[n_pawns:]
    for i, sq in enumerate(pawn_squares):
        color = 'P' if (i % 2 == 0) else 'p'
        axis = 'w' if (i < n_pawns // 2) else 'y'
        pos[sq] = (color, axis)
    for sq in other_squares:
        pos[sq] = rng.choice(_NONPAWN_CHARS)
    return pos


def time_encode(pos, iters: int) -> float:
    for _ in range(5):
        encode_4d_pure_phase(pos)
    t0 = time.perf_counter()
    for _ in range(iters):
        encode_4d_pure_phase(pos)
    return (time.perf_counter() - t0) * 1000.0 / iters


def main():
    pawn_counts = (0, 4, 8, 12, 16, 24, 32)
    iters = 1500
    trials = 5
    seed_base = 42

    print(f"# Integrated bench (full encode_4d_pure_phase): "
          f"{iters} iters/trial, {trials} trials, min over trials")
    print(f"# Each position has 24 non-pawn pieces + N pawns "
          f"(50/50 W/Y axis split)")
    print(f"#   columns: pawn_count, encode_ms (best of {trials})")
    rows = []
    for n in pawn_counts:
        pos = make_position(n, seed=seed_base + n)
        trial_times = [time_encode(pos, iters) for _ in range(trials)]
        best = min(trial_times)
        rows.append((n, best))
        print(f"  n_pawns={n:3d}: {best:.4f} ms  (trials: "
              f"{[f'{t:.3f}' for t in trial_times]})")
    return rows


if __name__ == '__main__':
    main()

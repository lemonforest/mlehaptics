"""Microbench: time just the FA_PAWN_W and FA_PAWN_Y scatter loops.

Isolates the change-of-interest from the rest of the encoder so the
signal-to-noise ratio is high. Mirrors the exact algorithm used in
`encode_4d_pure_phase` for both:

  * baseline_w_loop / baseline_y_loop   — current per-pawn loop
  * vectorized_w     / vectorized_y     — proposed batched scatter
"""
from __future__ import annotations

import random
import time
from typing import Dict, List, Tuple

import numpy as np

from chess_spectral.encoder_pure_phase_4d import _build_quant_tables

CHANNEL_DIM = 4096


def make_pawn_positions(n_pawns: int, seed: int) -> List[Tuple[int, str, str]]:
    """Build a list of (square, color_char, axis_char) entries.

    Half W-axis, half Y-axis pawns, mixed colors. ``square`` is in
    [0, 4096). No duplicates. Caller passes this list to both the
    baseline loop and the vectorized version, so they see identical
    inputs.
    """
    rng = random.Random(seed)
    squares = rng.sample(range(4096), n_pawns)
    out: List[Tuple[int, str, str]] = []
    for i, sq in enumerate(squares):
        color = 'P' if (i % 2 == 0) else 'p'
        axis = 'w' if (i < n_pawns // 2) else 'y'
        out.append((sq, color, axis))
    return out


def baseline_pawn_scatter(pawns: List[Tuple[int, str, str]],
                          W_ANTI: np.ndarray,
                          Y_ANTI: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Mirror of the loop in encode_4d_pure_phase pre-vectorize."""
    pawn_w = np.zeros(CHANNEL_DIM, dtype=np.int64)
    pawn_y = np.zeros(CHANNEL_DIM, dtype=np.int64)
    for sq, color, axis in pawns:
        sign = 1 if color == 'P' else -1
        s = int(sq)
        sx = (s >> 9) & 7
        sy = (s >> 6) & 7
        sz = (s >> 3) & 7
        sw = s & 7
        if axis == 'w':
            base = (sx << 9) | (sy << 6) | (sz << 3)
            pawn_w[base:base + 8] += (
                sign * W_ANTI[sw].astype(np.int64)
            )
        else:
            base = (sx << 9) | (sz << 3) | sw
            idx = base | (np.arange(8) << 6)
            pawn_y[idx] += (
                sign * Y_ANTI[sy].astype(np.int64)
            )
    return pawn_w, pawn_y


def vectorized_pawn_scatter(pawns: List[Tuple[int, str, str]],
                            W_ANTI: np.ndarray,
                            Y_ANTI: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Vectorized: group W and Y pawns and scatter once each.

    Algorithm (W-axis, mirror for Y):

      Inputs: signs (n_w,), bases (n_w,), sw_idx (n_w,)
      bcols  = bases[:, None] + arange(8)        # (n_w, 8)
      values = signs[:, None] * W_ANTI[sw_idx]   # (n_w, 8) int64

      np.add.at(pawn_w, bcols, values)

    np.add.at handles duplicate indices correctly (two pawns can
    share the same (sx, sy, sz) base). Plain ``arr[idx] += val`` does
    not, which is why np.add.at is required.
    """
    pawn_w = np.zeros(CHANNEL_DIM, dtype=np.int64)
    pawn_y = np.zeros(CHANNEL_DIM, dtype=np.int64)

    # Bucket pawns by axis. Keep python list comprehensions tight.
    w_signs: List[int] = []
    w_bases: List[int] = []
    w_sw: List[int] = []
    y_signs: List[int] = []
    y_bases: List[int] = []
    y_sy: List[int] = []
    for sq, color, axis in pawns:
        sign = 1 if color == 'P' else -1
        s = int(sq)
        sx = (s >> 9) & 7
        sy = (s >> 6) & 7
        sz = (s >> 3) & 7
        sw = s & 7
        if axis == 'w':
            w_signs.append(sign)
            w_bases.append((sx << 9) | (sy << 6) | (sz << 3))
            w_sw.append(sw)
        else:
            y_signs.append(sign)
            y_bases.append((sx << 9) | (sz << 3) | sw)
            y_sy.append(sy)

    if w_signs:
        signs_arr = np.asarray(w_signs, dtype=np.int64)
        bases_arr = np.asarray(w_bases, dtype=np.int64)
        sw_arr = np.asarray(w_sw, dtype=np.int64)
        # values shape (n_w, 8) int64
        values = signs_arr[:, None] * W_ANTI[sw_arr].astype(np.int64)
        cols = bases_arr[:, None] + np.arange(8, dtype=np.int64)
        np.add.at(pawn_w, cols, values)

    if y_signs:
        signs_arr = np.asarray(y_signs, dtype=np.int64)
        bases_arr = np.asarray(y_bases, dtype=np.int64)
        sy_arr = np.asarray(y_sy, dtype=np.int64)
        values = signs_arr[:, None] * Y_ANTI[sy_arr].astype(np.int64)
        cols = bases_arr[:, None] | (np.arange(8, dtype=np.int64) << 6)
        np.add.at(pawn_y, cols, values)

    return pawn_w, pawn_y


# Tunable: per-axis pawn count above which vectorized scatter beats
# the per-pawn loop. Below this, numpy setup overhead wins; above,
# batched scatter wins. Empirically determined (5000-iter microbench,
# 5 trials min): vectorize wins from ~5 per-axis pawns; safer cutoff
# at 4 means we batch when there's any meaningful pawn count.
VECTORIZE_AXIS_THRESHOLD = 4


def hybrid_pawn_scatter(pawns: List[Tuple[int, str, str]],
                        W_ANTI: np.ndarray,
                        Y_ANTI: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Per-axis hybrid: bucket once, then choose loop vs vectorize
    independently for each axis based on count."""
    pawn_w = np.zeros(CHANNEL_DIM, dtype=np.int64)
    pawn_y = np.zeros(CHANNEL_DIM, dtype=np.int64)

    w_signs: List[int] = []
    w_bases: List[int] = []
    w_sw: List[int] = []
    y_signs: List[int] = []
    y_bases: List[int] = []
    y_sy: List[int] = []
    for sq, color, axis in pawns:
        sign = 1 if color == 'P' else -1
        s = int(sq)
        sx = (s >> 9) & 7
        sy = (s >> 6) & 7
        sz = (s >> 3) & 7
        sw = s & 7
        if axis == 'w':
            w_signs.append(sign)
            w_bases.append((sx << 9) | (sy << 6) | (sz << 3))
            w_sw.append(sw)
        else:
            y_signs.append(sign)
            y_bases.append((sx << 9) | (sz << 3) | sw)
            y_sy.append(sy)

    n_w = len(w_signs)
    if n_w >= VECTORIZE_AXIS_THRESHOLD:
        signs_arr = np.asarray(w_signs, dtype=np.int64)
        bases_arr = np.asarray(w_bases, dtype=np.int64)
        sw_arr = np.asarray(w_sw, dtype=np.int64)
        values = signs_arr[:, None] * W_ANTI[sw_arr].astype(np.int64)
        cols = bases_arr[:, None] + np.arange(8, dtype=np.int64)
        np.add.at(pawn_w, cols, values)
    elif n_w > 0:
        for sign, base, sw in zip(w_signs, w_bases, w_sw):
            pawn_w[base:base + 8] += sign * W_ANTI[sw].astype(np.int64)

    n_y = len(y_signs)
    if n_y >= VECTORIZE_AXIS_THRESHOLD:
        signs_arr = np.asarray(y_signs, dtype=np.int64)
        bases_arr = np.asarray(y_bases, dtype=np.int64)
        sy_arr = np.asarray(y_sy, dtype=np.int64)
        values = signs_arr[:, None] * Y_ANTI[sy_arr].astype(np.int64)
        cols = bases_arr[:, None] | (np.arange(8, dtype=np.int64) << 6)
        np.add.at(pawn_y, cols, values)
    elif n_y > 0:
        offsets = np.arange(8, dtype=np.int64) << 6
        for sign, base, sy in zip(y_signs, y_bases, y_sy):
            pawn_y[base | offsets] += sign * Y_ANTI[sy].astype(np.int64)

    return pawn_w, pawn_y


def time_fn(fn, args, iters: int) -> float:
    """Mean ms per call after a 5-iter warmup."""
    for _ in range(5):
        fn(*args)
    t0 = time.perf_counter()
    for _ in range(iters):
        fn(*args)
    return (time.perf_counter() - t0) * 1000.0 / iters


def main(pawn_counts=(0, 4, 8, 16, 32), iters=2000, trials=3, seed_base=42):
    qt = _build_quant_tables()
    W_ANTI = qt['W_ANTI_DCT_INT16']
    Y_ANTI = qt['Y_ANTI_DCT_INT16']

    print(f"# FA_PAWN microbench: {iters} iters/trial, {trials} trials, "
          f"min over trials")
    print(f"#   columns: pawn_count, baseline_ms, vectorized_ms, "
          f"hybrid_ms, vec_speedup, hybrid_speedup")
    rows = []
    for n in pawn_counts:
        pawns = make_pawn_positions(n, seed=seed_base + n)
        # Verify equivalence (bit-exact).
        b_w, b_y = baseline_pawn_scatter(pawns, W_ANTI, Y_ANTI)
        v_w, v_y = vectorized_pawn_scatter(pawns, W_ANTI, Y_ANTI)
        h_w, h_y = hybrid_pawn_scatter(pawns, W_ANTI, Y_ANTI)
        assert np.array_equal(b_w, v_w), f"W vec mismatch at n={n}"
        assert np.array_equal(b_y, v_y), f"Y vec mismatch at n={n}"
        assert np.array_equal(b_w, h_w), f"W hybrid mismatch at n={n}"
        assert np.array_equal(b_y, h_y), f"Y hybrid mismatch at n={n}"

        b_trials = [time_fn(baseline_pawn_scatter,
                            (pawns, W_ANTI, Y_ANTI), iters)
                    for _ in range(trials)]
        v_trials = [time_fn(vectorized_pawn_scatter,
                            (pawns, W_ANTI, Y_ANTI), iters)
                    for _ in range(trials)]
        h_trials = [time_fn(hybrid_pawn_scatter,
                            (pawns, W_ANTI, Y_ANTI), iters)
                    for _ in range(trials)]
        b_min = min(b_trials)
        v_min = min(v_trials)
        h_min = min(h_trials)
        v_speedup = b_min / v_min if v_min > 0 else float('inf')
        h_speedup = b_min / h_min if h_min > 0 else float('inf')
        rows.append((n, b_min, v_min, h_min, v_speedup, h_speedup))
        print(f"  n_pawns={n:3d}: base={b_min:.4f}  vec={v_min:.4f}  "
              f"hybrid={h_min:.4f}  v_sp={v_speedup:.2f}x  "
              f"h_sp={h_speedup:.2f}x")
    return rows


if __name__ == '__main__':
    main()

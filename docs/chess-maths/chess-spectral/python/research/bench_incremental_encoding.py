"""Wall-clock bench: full re-encode vs incremental phase-shift update.

This is the bench that actually matters for the multi-move-preview /
hover-renderer scenario. The earlier benches measured move-gen cost;
this one measures the cost of producing the POST-MOVE encoded vector
(which the heatmap renderer slices for display).

Two paths:

  FULL RE-ENCODE
    For each preview, build the post-move position dict and call
    encode_640(pos) / encode_4d(pos4) from scratch. O(pieces × ...).
    Current pipeline.

  INCREMENTAL DELTA
    Encode the moving piece's contribution at the source square once,
    encode it at the target square once, and compute
        new_encoding = old_encoding - source_contribution + target_contribution
    O(channels) regardless of how many pieces are on the board.

If the encoder is linear in pieces (which it is — irrep projections
and fiber accumulations both sum over pieces), the delta is exact,
not an approximation. The bench treats them as equivalent for
correctness and measures only the time cost.

For a hover-renderer that wants to show N candidate destinations
glowing with their post-move spectral signatures:
    full re-encode pipeline:    N × full_encode_cost
    incremental pipeline:       full_encode_cost (once) + N × delta_cost

The break-even point is when delta_cost ≪ full_encode_cost.

Run:
    cd docs/chess-maths/chess-spectral/python
    PYTHONPATH=. python research/bench_incremental_encoding.py
"""
from __future__ import annotations

import statistics
import time
from typing import Callable

import pytest


def _bench(label: str, fn: Callable[[], object],
           warmup: int = 30, iters: int = 100) -> dict:
    for _ in range(warmup):
        fn()
    times = []
    for _ in range(iters):
        t0 = time.perf_counter()
        fn()
        t1 = time.perf_counter()
        times.append((t1 - t0) * 1e6)
    return {
        "label": label,
        "min_us":    min(times),
        "median_us": statistics.median(times),
    }


def _print_table(rows: list[dict], header: str) -> None:
    print(f"\n=== {header} ===")
    print(f"{'configuration':<58s} {'median':>11s} {'min':>11s}")
    print("-" * 84)
    for r in rows:
        print(f"{r['label']:<58s} {r['median_us']:>10.1f}µs "
              f"{r['min_us']:>10.1f}µs")


# ─── 2D ─────────────────────────────────────────────────────────────


def _bench_2d() -> list[dict]:
    import numpy as np
    from chess_spectral.encoder import encode_640
    from chess_spectral.fen import fen_to_pos

    # Standard initial position (32 pieces).
    startpos = fen_to_pos(
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    )
    # A typical move: knight from b1 to c3 (g1 white knight to f3 in
    # standard SAN; here we're working in our (rank, file) → square
    # convention). Pick something concrete.
    knight_b1 = 1                # white knight at b1 (rank 0, file 1)
    knight_c3 = 8 * 2 + 2        # c3 = rank 2, file 2
    moving_piece = startpos[knight_b1]

    # Build single-piece "moving piece" positions.
    only_at_from = {knight_b1: moving_piece}
    only_at_to   = {knight_c3: moving_piece}

    # Pre-compute the deltas (these would be cached / built once per
    # piece-and-square pair in a real renderer).
    enc_full = encode_640(startpos)
    enc_at_from = encode_640(only_at_from)
    enc_at_to   = encode_640(only_at_to)
    expected_post = encode_640({**{k: v for k, v in startpos.items() if k != knight_b1},
                                knight_c3: moving_piece})
    delta_post = enc_full - enc_at_from + enc_at_to
    residual = delta_post - expected_post

    # Per-channel residual analysis. The 640-dim encoder layout
    # (chess_spectral.encoder docstring): 64 dims per channel × 10
    # channels (A1, A2, B1, B2, E, F1, F2, F3, FA, FD).
    chan_names = ["A1", "A2", "B1", "B2", "E ",
                  "F1", "F2", "F3", "FA", "FD"]
    print("\n=== 2D linearity decomposition (per 64-dim channel) ===")
    print(f"{'channel':<8s} {'||delta - true||_inf':>22s} "
          f"{'||true||_inf':>14s}  {'verdict':>10s}")
    for i, name in enumerate(chan_names):
        slice_ = slice(i * 64, (i + 1) * 64)
        residual_inf = float(np.abs(residual[slice_]).max())
        true_inf = float(np.abs(expected_post[slice_]).max())
        ratio = residual_inf / true_inf if true_inf > 0 else 0.0
        verdict = ("LINEAR" if ratio < 1e-6
                   else "approx" if ratio < 0.1
                   else "NONLIN")
        print(f"  {name:<6s} {residual_inf:>22.4e} {true_inf:>14.4e}  "
              f"{verdict:>10s}  ({ratio:.2%})")

    rows = []

    # FULL RE-ENCODE: per preview, encode the full post-move position.
    post_pos = {**{k: v for k, v in startpos.items() if k != knight_b1},
                knight_c3: moving_piece}
    rows.append(_bench(
        "2D FULL re-encode (32 pieces, post-knight-move)",
        lambda: encode_640(post_pos),
    ))

    # SINGLE-PIECE ENCODE: cost of encoding one piece (the building
    # block of the delta path).
    rows.append(_bench(
        "2D single-piece encode (1 piece) — building block",
        lambda: encode_640(only_at_to),
    ))

    # DELTA UPDATE: assume both single-piece encodings are pre-cached,
    # measure just the vector arithmetic. This is the steady-state
    # cost when the renderer caches per-piece-per-square encodings.
    rows.append(_bench(
        "2D DELTA update (cached single-piece, 2x vec ops)",
        lambda: enc_full - enc_at_from + enc_at_to,
    ))

    # DELTA UPDATE (uncached): build both single-piece encodings on
    # demand. This is the worst case — no caching at all.
    rows.append(_bench(
        "2D DELTA update (uncached: 2x single-encode + 2x vec ops)",
        lambda: encode_640(only_at_to) - encode_640(only_at_from)
                + enc_full,
    ))

    return rows


# ─── 4D ─────────────────────────────────────────────────────────────


def _bench_4d() -> list[dict]:
    import numpy as np
    chess4d = pytest.importorskip("chess4d",
                                   reason="4D bench needs "
                                          "python-chess4d-oana-chiru")
    from chess_spectral.encoder_4d import encode_4d

    # Build pos4 dict from chess4d's initial_position.
    gs = chess4d.initial_position()

    def to_pos4(board):
        out = {}
        for color in (chess4d.Color.WHITE, chess4d.Color.BLACK):
            for sq, piece in board.pieces_of(color):
                # Convert chess4d.Square4D + Piece to chess_spectral
                # encoder_4d's pos4 format: int_square -> piece_value.
                # encoder_4d uses sq4(x,y,z,w) = ((x*8+y)*8+z)*8+w.
                from chess_spectral import tables_4d as t4
                key = t4.sq4(sq.x, sq.y, sq.z, sq.w)
                if piece.piece_type == chess4d.types.PieceType.PAWN:
                    char = 'P' if piece.color == chess4d.Color.WHITE else 'p'
                    axis = 'w' if piece.pawn_axis == chess4d.types.PawnAxis.W else 'y'
                    out[key] = (char, axis)
                else:
                    name_to_char = {
                        chess4d.types.PieceType.ROOK:   'R',
                        chess4d.types.PieceType.BISHOP: 'B',
                        chess4d.types.PieceType.KNIGHT: 'N',
                        chess4d.types.PieceType.QUEEN:  'Q',
                        chess4d.types.PieceType.KING:   'K',
                    }
                    char = name_to_char[piece.piece_type]
                    if piece.color == chess4d.Color.BLACK:
                        char = char.lower()
                    out[key] = char
        return out

    startpos4 = to_pos4(gs.board)

    # Pick a concrete move: the white knight at (1, 0, 5, 4) moves
    # to (2, 2, 5, 4) (a (1, 2, 0, 0) leap). Whether that's actually
    # legal we don't care — we're benching the encoder, not move-gen.
    from chess_spectral import tables_4d as t4
    knight_from = t4.sq4(1, 0, 5, 4)
    knight_to   = t4.sq4(2, 2, 5, 4)
    moving = startpos4[knight_from]

    only_at_from = {knight_from: moving}
    only_at_to   = {knight_to: moving}

    # Pre-encode (warm caches inside encoder_4d — first call is slow).
    enc_full = encode_4d(startpos4)
    enc_at_from = encode_4d(only_at_from)
    enc_at_to   = encode_4d(only_at_to)
    post_pos4 = {k: v for k, v in startpos4.items() if k != knight_from}
    post_pos4[knight_to] = moving
    expected_post = encode_4d(post_pos4)
    delta_post = enc_full - enc_at_from + enc_at_to
    residual = delta_post - expected_post

    # 4D channel layout (encoder_4d docstring): 4096 dims × 11 channels.
    # 0:A1, 1:STD4_X, 2:STD4_Y, 3:STD4_Z, 4:STD4_W,
    # 5:FIB_SYM_1, 6:FIB_SYM_2, 7:FIB_SYM_3,
    # 8:FA_PAWN_W, 9:FA_PAWN_Y, 10:FD_DIAG.
    chan_names_4d = ["A1     ", "STD4_X ", "STD4_Y ", "STD4_Z ",
                     "STD4_W ", "FIB_S1 ", "FIB_S2 ", "FIB_S3 ",
                     "FA_PWN_W", "FA_PWN_Y", "FD_DIAG"]
    print("\n=== 4D linearity decomposition (per 4096-dim channel) ===")
    print(f"{'channel':<10s} {'||delta - true||_inf':>22s} "
          f"{'||true||_inf':>14s}  {'verdict':>10s}")
    for i, name in enumerate(chan_names_4d):
        slice_ = slice(i * 4096, (i + 1) * 4096)
        residual_inf = float(np.abs(residual[slice_]).max())
        true_inf = float(np.abs(expected_post[slice_]).max())
        ratio = residual_inf / true_inf if true_inf > 0 else 0.0
        verdict = ("LINEAR" if ratio < 1e-6
                   else "approx" if ratio < 0.1
                   else "NONLIN")
        print(f"  {name:<8s} {residual_inf:>22.4e} {true_inf:>14.4e}  "
              f"{verdict:>10s}  ({ratio:.2%})")

    rows = []

    rows.append(_bench(
        f"4D FULL re-encode ({len(post_pos4)} pieces)",
        lambda: encode_4d(post_pos4),
        warmup=5, iters=20,
    ))

    rows.append(_bench(
        "4D single-piece encode (1 piece) — building block",
        lambda: encode_4d(only_at_to),
        warmup=5, iters=30,
    ))

    rows.append(_bench(
        "4D DELTA update (cached single-piece, 2x vec ops)",
        lambda: enc_full - enc_at_from + enc_at_to,
    ))

    rows.append(_bench(
        "4D DELTA update (uncached: 2x single-encode + 2x vec ops)",
        lambda: encode_4d(only_at_to) - encode_4d(only_at_from) + enc_full,
        warmup=5, iters=20,
    ))

    return rows


def main() -> int:
    print("Incremental encoding bench: full re-encode vs phase-shift")
    print("delta. The hover/multi-preview renderer pays the FULL cost")
    print("per preview without caching; with caching, just the DELTA.")

    rows_2d = _bench_2d()
    _print_table(rows_2d, "2D")

    rows_4d = _bench_4d()
    _print_table(rows_4d, "4D")

    print("\n=== Read ===")
    print("If FULL >> DELTA, incremental encoding is the right path")
    print("for an interactive renderer. The DELTA-cached row is the")
    print("steady-state cost once the per-piece-per-square cache is")
    print("warm; the DELTA-uncached row is the worst case.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

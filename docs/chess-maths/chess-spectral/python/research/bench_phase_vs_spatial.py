"""Wall-clock benchmark: phase ops vs spatial generators in 2D and 4D.

Answers the question Steven raised after Phase E shipped: in 2D, the
phase op is faster than python-chess WITHOUT castling (~7 µs vs
~22 µs), but castling drives the phase op to ~120 µs (worse than
python-chess). What's the analogous picture in 4D?

Measures **time per full position-level move generation** — one call
that enumerates every legal pseudo-move from every piece for the
side to move. The 2D and 4D measurements use different oracles
(python-chess for 2D, python-chess4d-oana-chiru for 4D); the
phase-op paths are comparable in shape (Solution A: phase-op
candidates intersected with the oracle's per-piece generator).

Three configurations per dimension:
    1. Oracle baseline (python-chess.legal_moves / chess4d.legal_moves)
    2. Phase op WITHOUT castling (sliders + leapers + pawn forward)
    3. Phase op WITH castling (only 2D — 4D castling not implemented
       in chess_spectral.phase_operators_4d as of v1.3.0)

Run:
    cd docs/chess-maths/chess-spectral/python
    python research/bench_phase_vs_spatial.py
"""
from __future__ import annotations

import statistics
import time
from typing import Callable

import pytest


def _bench(label: str, fn: Callable[[], object],
           warmup: int = 20, iters: int = 100) -> dict:
    """Time fn() over ``iters`` runs after a small warmup. Returns a
    dict with min / median / mean / stdev / total_dests sample."""
    for _ in range(warmup):
        fn()
    times = []
    for _ in range(iters):
        t0 = time.perf_counter()
        result = fn()
        t1 = time.perf_counter()
        times.append((t1 - t0) * 1e6)  # µs
    sample_count = (
        len(result) if hasattr(result, "__len__")
        else (result if isinstance(result, int) else None)
    )
    return {
        "label": label,
        "min_us":    min(times),
        "median_us": statistics.median(times),
        "mean_us":   statistics.mean(times),
        "stdev_us":  statistics.stdev(times) if len(times) > 1 else 0.0,
        "iters":     iters,
        "sample_count": sample_count,
    }


def _print_table(rows: list[dict], header: str) -> None:
    print(f"\n=== {header} ===")
    print(f"{'configuration':<55s} {'median':>10s} {'min':>10s}  "
          f"{'count':>8s}")
    print("-" * 88)
    for r in rows:
        cnt = r["sample_count"]
        cnt_str = f"{cnt}" if cnt is not None else "-"
        print(f"{r['label']:<55s} {r['median_us']:>9.1f}µs "
              f"{r['min_us']:>9.1f}µs  {cnt_str:>8s}")


# ─── 2D measurements ────────────────────────────────────────────────


def _bench_2d() -> list[dict]:
    chess = pytest.importorskip("chess",
                                 reason="2D bench needs python-chess")
    from chess_spectral.phase_operators import (
        occupation_aware_moves_a,
        WHITE_CHARGE, BLACK_CHARGE,
    )

    board = chess.Board()  # standard initial position
    rows = []

    # 1. python-chess baseline — full legal_moves list materialization.
    rows.append(_bench(
        "2D oracle: python-chess board.legal_moves (full)",
        lambda: list(board.legal_moves),
    ))

    # 2. Phase op WITHOUT castling — Solution A per piece, summed.
    #    occupation_aware_moves_a for non-king pieces; for kings,
    #    we use the SAME function but pass include_castling=False
    #    if the API supports it. Looking at the 2D function, the
    #    castling union happens at the dispatcher level — we'll
    #    bench the per-piece occupation_aware path which excludes
    #    castling by default.
    def _phase_no_castling() -> int:
        total = 0
        for sq, piece in board.piece_map().items():
            if piece.color != board.turn:
                continue
            r, c = chess.square_rank(sq), chess.square_file(sq)
            mover_charge = (WHITE_CHARGE if piece.color == chess.WHITE
                            else BLACK_CHARGE)
            try:
                dests = occupation_aware_moves_a(
                    board, piece.symbol(), r, c,
                    mover_charge=mover_charge,
                )
                total += len(dests)
            except Exception:
                # Some pieces (pawns with captures) may not work in
                # all configs — skip without inflating wall-clock.
                pass
        return total

    rows.append(_bench(
        "2D phase op (Solution A, no castling, per-piece)",
        _phase_no_castling,
    ))

    # 3. Phase op WITH castling — bench the `available_castles` +
    #    castle_king_destinations path on top of (2). This adds the
    #    king-safety walk per castling right.
    from chess_spectral.phase_operators.castling import (
        available_castles, castle_king_destinations,
    )

    def _phase_with_castling() -> int:
        total = 0
        for sq, piece in board.piece_map().items():
            if piece.color != board.turn:
                continue
            r, c = chess.square_rank(sq), chess.square_file(sq)
            mover_charge = (WHITE_CHARGE if piece.color == chess.WHITE
                            else BLACK_CHARGE)
            try:
                dests = occupation_aware_moves_a(
                    board, piece.symbol(), r, c,
                    mover_charge=mover_charge,
                )
                total += len(dests)
            except Exception:
                pass
        # Add castle dests for the king(s).
        for cm in available_castles(board):
            total += len(castle_king_destinations(cm))
        return total

    rows.append(_bench(
        "2D phase op (Solution A + castling king-safety walk)",
        _phase_with_castling,
    ))

    return rows


# ─── 4D measurements ────────────────────────────────────────────────


def _bench_4d() -> list[dict]:
    chess4d = pytest.importorskip("chess4d",
                                   reason="4D bench needs "
                                          "python-chess4d-oana-chiru")
    from chess_spectral.phase_operators_4d import (
        occupation_aware_moves_a_4d,
    )

    gs = chess4d.initial_position()
    rows = []

    # 1a. chess4d pseudo-legal — per-piece move enumeration WITHOUT
    #     the multi-king check filter. This is the closest analogue
    #     to what occupation_aware_moves_a_4d does (no king-safety
    #     filter, no castling).
    piece_gens = {
        chess4d.types.PieceType.ROOK:   chess4d.rook_moves,
        chess4d.types.PieceType.BISHOP: chess4d.bishop_moves,
        chess4d.types.PieceType.QUEEN:  chess4d.queen_moves,
        chess4d.types.PieceType.KNIGHT: chess4d.knight_moves,
        chess4d.types.PieceType.KING:   chess4d.king_moves,
        chess4d.types.PieceType.PAWN:   chess4d.pawn_moves,
    }

    def _chess4d_pseudo_legal() -> int:
        total = 0
        for color in (chess4d.Color.WHITE, chess4d.Color.BLACK):
            for sq, piece in gs.board.pieces_of(color):
                if color != gs.side_to_move:
                    continue
                fn = piece_gens[piece.piece_type]
                for _ in fn(sq, piece.color, gs.board):
                    total += 1
        return total

    rows.append(_bench(
        "4D oracle: chess4d per-piece pseudo-legal moves (no check)",
        _chess4d_pseudo_legal,
        warmup=5, iters=20,
    ))

    # 1b. chess4d full legal_moves enumeration. INCLUDES castling,
    #     en-passant, multi-king legality (the 4D O&C complete
    #     legality pipeline). Heaviest comparison; expect this to
    #     dominate.
    rows.append(_bench(
        "4D oracle: chess4d.GameState.legal_moves (full + check filter)",
        lambda: list(gs.legal_moves()),
        warmup=5, iters=20,
    ))

    # 2. Phase op WITHOUT castling — Solution A per piece, summed.
    #    occupation_aware_moves_a_4d does NOT generate castling
    #    moves (chess_spectral.phase_operators_4d v1.3.0 doesn't
    #    have a castling primitive yet — see PHASE_OPERATOR_SUPPLEMENT_4D
    #    §13.6.5).
    def _phase4_no_castling() -> int:
        total = 0
        for color in (chess4d.Color.WHITE, chess4d.Color.BLACK):
            for sq, piece in gs.board.pieces_of(color):
                if color != gs.side_to_move:
                    continue
                dests = occupation_aware_moves_a_4d(gs, sq, piece)
                total += len(dests)
        return total

    rows.append(_bench(
        "4D phase op (Solution A, no castling, per-piece)",
        _phase4_no_castling,
        warmup=5, iters=20,
    ))

    return rows


def main() -> int:
    print("Phase ops vs spatial generators — wall-clock per full move")
    print("generation pass (one position; standard initial position).")

    print("\nNote: the 2D and 4D oracles are different software "
          "(python-chess vs chess4d), and chess4d is pure Python "
          "while python-chess uses bitboards. Compare ratios within "
          "a dimension, not absolutes across dimensions.")

    rows_2d = _bench_2d()
    _print_table(rows_2d, "2D — initial position")

    rows_4d = _bench_4d()
    _print_table(rows_4d, "4D — initial position (~896 pieces)")

    # Ratio summary.
    print("\n=== Phase-vs-oracle ratios ===")
    if len(rows_2d) >= 2:
        oracle = rows_2d[0]["median_us"]
        for r in rows_2d[1:]:
            ratio = r["median_us"] / oracle
            label = "FASTER" if ratio < 1 else "SLOWER"
            print(f"  2D: {r['label'][:42]:42s} "
                  f"{ratio:5.2f}x ({label})")
    if len(rows_4d) >= 2:
        oracle = rows_4d[0]["median_us"]
        for r in rows_4d[1:]:
            ratio = r["median_us"] / oracle
            label = "FASTER" if ratio < 1 else "SLOWER"
            print(f"  4D: {r['label'][:42]:42s} "
                  f"{ratio:5.2f}x ({label})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Wall-time benchmark for §11.4 Solutions A, B, C.

Runs each of the three occupation-aware move generators over an
identical workload (every side-to-move piece in a sample of positions
from a corpus) and reports wall-time statistics per solution:

    total    — sum of per-call wall times
    mean     — arithmetic mean per call
    p50/p95/p99 — latency percentiles
    throughput — calls per second (1 / mean)

The occupation field is computed ONCE per position and passed into B
and C, so the numbers reflect the cost of the solution proper, not of
field construction. Solution A does not take an occupation-field
kwarg; it pays its own python-chess legal_moves cost every call.

Repeats (--repeats) amortize timer noise: the full piece-workload is
run N times end-to-end per solution, and statistics are computed over
the pooled per-call samples.

Why this exists (and why it's not just occupation_equivalence_check.py):
  - occupation_equivalence_check.py's job is correctness (four-way
    agreement) and produces a big CSV with pairwise destination sets.
    Its per-row time_ns columns are incidental — one sample each, no
    warmup, no repeats, no percentiles.
  - This script's job is timing. It does no correctness comparison,
    runs warmup iterations, pools many samples, and reports
    distributional stats.

Typical use:
    # Quick read on relative cost
    python benchmark_solutions.py --n-positions 50 --repeats 5

    # Stable numbers for the supplement §11.4.5 table
    python benchmark_solutions.py --n-positions 200 --repeats 20 \\
        --warmup 5 --out ../results/phase_operator_experiments/exp2_timings.csv

    # Zoom in on a single polarization
    python benchmark_solutions.py --piece Q --repeats 50

Defaults match occupation_equivalence_check.py's corpus + seed so the
two scripts report on the same sampled positions.
"""
import argparse
import csv
import json
import random
import time
from pathlib import Path

import chess

from occupation_field import (
    WHITE_CHARGE, BLACK_CHARGE, occupation_field_from_board,
)
from occupation_aware_a import occupation_aware_moves_a
from occupation_aware_b import occupation_aware_moves_b
from occupation_aware_c import occupation_aware_moves_c


_PIECE_CHARS = {
    chess.ROOK: "R",
    chess.BISHOP: "B",
    chess.QUEEN: "Q",
    chess.KING: "K",
    chess.KNIGHT: "N",
    chess.PAWN: "P",
}

SOLUTIONS: dict[str, str] = {
    "A": "post-hoc geometric pruning (phase candidates & legal_moves)",
    "B": "batch ray + set-intersection truncation (phase-native)",
    "C": "sequential step with early halt (phase-native)",
}


def sample_positions_from_corpus(corpus_dir: Path, n: int,
                                 seed: int) -> list[str]:
    """Return [fen, ...] sampled uniformly from the corpus ndjson."""
    ndjson_dir = corpus_dir / "ndjson"
    if not ndjson_dir.is_dir():
        raise FileNotFoundError(
            f"no ndjson/ under {corpus_dir}; extract the corpus 7z first")
    fens: list[str] = []
    for path in sorted(ndjson_dir.glob("*.ndjson")):
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if "fen" in rec:
                    fens.append(rec["fen"])
    rng = random.Random(seed)
    rng.shuffle(fens)
    return fens[:n]


def _build_workload(fens: list[str], piece_filter: str | None,
                    ) -> list[tuple[chess.Board, dict[int, int], str,
                                     int, int, int]]:
    """Expand each FEN into (board, occupation, pc, r, c, charge) tuples
    for every side-to-move piece, optionally filtered to one piece
    type."""
    workload: list[tuple[chess.Board, dict[int, int], str, int, int, int]] = []
    for fen in fens:
        board = chess.Board(fen)
        occupation = occupation_field_from_board(board)
        mover_charge = WHITE_CHARGE if board.turn == chess.WHITE else BLACK_CHARGE
        for square, piece in board.piece_map().items():
            if piece.color != board.turn:
                continue
            pc = _PIECE_CHARS[piece.piece_type]
            if piece_filter is not None and pc != piece_filter:
                continue
            workload.append((
                board, occupation, pc,
                chess.square_rank(square), chess.square_file(square),
                mover_charge,
            ))
    return workload


def _bench_solution(label: str, fn, workload, kwargs_for_fn,
                    repeats: int) -> list[int]:
    """Return list of per-call wall times in nanoseconds, pooled across
    repeats."""
    samples: list[int] = []
    for _ in range(repeats):
        for (board, occupation, pc, r, c, charge) in workload:
            kw = kwargs_for_fn(occupation)
            t0 = time.perf_counter_ns()
            fn(board, pc, r, c, charge, **kw)
            samples.append(time.perf_counter_ns() - t0)
    return samples


def _stats_ns(samples: list[int]) -> dict[str, float]:
    if not samples:
        return {"n_calls": 0, "total_ms": 0.0, "mean_us": 0.0,
                "p50_us": 0.0, "p95_us": 0.0, "p99_us": 0.0,
                "throughput_per_s": 0.0}
    total_ns = sum(samples)
    mean_ns = total_ns / len(samples)
    sorted_samples = sorted(samples)

    def pct(p: float) -> float:
        idx = min(len(sorted_samples) - 1,
                  max(0, int(round(p * (len(sorted_samples) - 1)))))
        return sorted_samples[idx] / 1000.0

    return {
        "n_calls": len(samples),
        "total_ms": total_ns / 1_000_000.0,
        "mean_us": mean_ns / 1000.0,
        "p50_us": pct(0.50),
        "p95_us": pct(0.95),
        "p99_us": pct(0.99),
        "throughput_per_s": 1e9 / mean_ns if mean_ns > 0 else float("inf"),
    }


def _format_row(label: str, desc: str, s: dict[str, float]) -> str:
    return (f"  {label}  {s['n_calls']:>8}   {s['total_ms']:>10.2f}"
            f"   {s['mean_us']:>8.2f}   {s['p50_us']:>7.2f}"
            f"   {s['p95_us']:>7.2f}   {s['p99_us']:>7.2f}"
            f"   {s['throughput_per_s']:>12,.0f}   {desc}")


def run(corpus_dir: Path, n_positions: int, seed: int,
        repeats: int, warmup: int, piece_filter: str | None,
        out_path: Path | None) -> dict:
    fens = sample_positions_from_corpus(corpus_dir, n_positions, seed)
    workload = _build_workload(fens, piece_filter)

    if not workload:
        raise SystemExit(
            "Empty workload — the sampled positions contained no pieces "
            "matching --piece filter. Widen the sample or drop --piece.")

    print(f"Sampled {len(fens)} positions from {corpus_dir.name}; "
          f"{len(workload)} piece-origins"
          + (f" (filtered to {piece_filter})" if piece_filter else "")
          + f"; {repeats} repeats + {warmup} warmup.")
    print()

    if warmup > 0:
        _bench_solution("warmup-A", occupation_aware_moves_a, workload,
                        lambda occ: {}, warmup)
        _bench_solution("warmup-B", occupation_aware_moves_b, workload,
                        lambda occ: {"occupation": occ}, warmup)
        _bench_solution("warmup-C", occupation_aware_moves_c, workload,
                        lambda occ: {"occupation": occ}, warmup)

    samples_a = _bench_solution("A", occupation_aware_moves_a, workload,
                                lambda occ: {}, repeats)
    samples_b = _bench_solution("B", occupation_aware_moves_b, workload,
                                lambda occ: {"occupation": occ}, repeats)
    samples_c = _bench_solution("C", occupation_aware_moves_c, workload,
                                lambda occ: {"occupation": occ}, repeats)

    stats = {
        "A": _stats_ns(samples_a),
        "B": _stats_ns(samples_b),
        "C": _stats_ns(samples_c),
    }

    print("Sol  n_calls   total (ms)   mean (us)   p50 (us)"
          "   p95 (us)   p99 (us)     calls/sec   description")
    print("-" * 120)
    for label in ("A", "B", "C"):
        print(_format_row(label, SOLUTIONS[label], stats[label]))
    print()

    # Relative speedups (using A as baseline, since it's the slowest).
    a_mean = stats["A"]["mean_us"] or 1.0
    print("Speedup vs Solution A (mean):")
    for label in ("A", "B", "C"):
        ratio = a_mean / (stats[label]["mean_us"] or 1.0)
        print(f"  {label}: {ratio:>6.2f}x")
    print()

    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = ["solution", "description", "n_calls", "total_ms",
                      "mean_us", "p50_us", "p95_us", "p99_us",
                      "throughput_per_s",
                      "n_positions", "repeats", "warmup", "piece_filter",
                      "seed"]
        with out_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for label in ("A", "B", "C"):
                row = {"solution": label,
                       "description": SOLUTIONS[label],
                       "n_positions": len(fens),
                       "repeats": repeats, "warmup": warmup,
                       "piece_filter": piece_filter or "",
                       "seed": seed}
                row.update(stats[label])
                writer.writerow(row)
        print(f"CSV written to: {out_path}")

    return stats


def main() -> int:
    default_corpus = (Path(__file__).resolve().parents[1]
                      / "results"
                      / "sweep_chain_lichess_drnykterstein_2026-04-14_N10")

    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
examples:
  # Default quick run (100 positions, 3 repeats, 1 warmup)
  python benchmark_solutions.py

  # Higher-precision numbers for the supplement
  python benchmark_solutions.py --n-positions 200 --repeats 20 --warmup 5

  # Only benchmark queens (where sliding-ray cost dominates)
  python benchmark_solutions.py --piece Q --repeats 50

  # Write CSV for later analysis
  python benchmark_solutions.py --out ../results/phase_operator_experiments/exp2_timings.csv

  # Use a different corpus (must have ndjson/ subdirectory)
  python benchmark_solutions.py --corpus ../results/sweep_hf_2026-04-20_N50

see also:
  occupation_equivalence_check.py  — correctness (four-way agreement)
  PHASE_OPERATOR_SUPPLEMENT.md §11.4.5 — validated headline timings
""")
    parser.add_argument(
        "--corpus", type=Path, default=default_corpus,
        help="Corpus directory (must contain ndjson/). "
             "Default: %(default)s")
    parser.add_argument(
        "--n-positions", type=int, default=100,
        help="Number of positions to sample from the corpus. "
             "Default: %(default)s")
    parser.add_argument(
        "--seed", type=int, default=42,
        help="RNG seed for position sampling. Pair with the same seed "
             "used by occupation_equivalence_check.py to compare over "
             "identical workloads. Default: %(default)s")
    parser.add_argument(
        "--repeats", type=int, default=3,
        help="Number of times to replay the full piece-workload per "
             "solution (samples are pooled). Raise this for tighter "
             "percentiles. Default: %(default)s")
    parser.add_argument(
        "--warmup", type=int, default=1,
        help="Number of warmup runs per solution BEFORE timing starts. "
             "Prevents cold-cache / JIT-like effects from biasing the "
             "first solution benchmarked. Default: %(default)s")
    parser.add_argument(
        "--piece", type=str, default=None,
        choices=["R", "B", "Q", "K", "N", "P"],
        help="Filter workload to a single piece type. Useful to isolate "
             "sliding-ray cost (Q/R/B) from localized filters (K/N/P). "
             "Default: all piece types.")
    parser.add_argument(
        "--out", type=Path, default=None,
        help="Optional CSV path for the summary stats. Parent "
             "directory is created if missing. Default: stdout only.")
    args = parser.parse_args()

    if args.repeats < 1:
        parser.error("--repeats must be >= 1")
    if args.warmup < 0:
        parser.error("--warmup must be >= 0")
    if args.n_positions < 1:
        parser.error("--n-positions must be >= 1")

    run(args.corpus, args.n_positions, args.seed,
        args.repeats, args.warmup, args.piece, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

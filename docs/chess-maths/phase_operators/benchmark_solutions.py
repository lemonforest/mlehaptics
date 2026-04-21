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
kwarg; it pays its own python-chess move iteration cost every call.

Repeats (--repeats) amortize timer noise: the full piece-workload is
run N times end-to-end per solution, and statistics are computed over
the pooled per-call samples.

Apples-to-apples: --filter {pseudo,legal,both}
  Solution A (in production) filters against board.legal_moves, which
  excludes moves that would leave the mover in check. Solutions B and C
  are phase-native and produce pseudo-legal moves (piece rights + path
  + castling, NO check filter — §11.2.8 defers check to §11.5). A naive
  head-to-head therefore compares A at a stricter correctness target
  than B/C, biasing against A.

  --filter pseudo  Run all three at pseudo-legal correctness:
                   A swaps board.legal_moves -> board.pseudo_legal_moves;
                   B and C run as-is.
  --filter legal   Run all three at legal (check-filtered) correctness:
                   A as-is; B and C get a post-filter pass through
                   board.legal_moves (same overhead A already pays).
  --filter both    Print both tables (default). Reveals how much of
                   each solution's runtime is phase work vs. check
                   filtering.

Why this exists (and why it's not just occupation_equivalence_check.py):
  - occupation_equivalence_check.py's job is correctness (four-way
    agreement) and produces a big CSV with pairwise destination sets.
    Its per-row time_ns columns are incidental — one sample each, no
    warmup, no repeats, no percentiles.
  - This script's job is timing. It does no correctness comparison,
    runs warmup iterations, pools many samples, and reports
    distributional stats.

Typical use:
    # Quick read on relative cost (both filter modes)
    python benchmark_solutions.py --n-positions 50 --repeats 5

    # Compare B/C's phase-native speed against A at matched correctness
    python benchmark_solutions.py --filter pseudo --repeats 20

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

from castling import castle_king_destinations
from occupation_field import (
    WHITE_CHARGE, BLACK_CHARGE, occupation_field_from_board,
)
from occupation_aware_a import (
    _unobstructed_dests,
    _chess_legal_dests,
    occupation_aware_moves_a,
)
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

# Descriptions per (solution, filter_mode). "legal" = check-filtered
# (matches board.legal_moves); "pseudo" = rights + path + castling
# only, no check filter (matches board.pseudo_legal_moves).
SOLUTION_DESCRIPTIONS: dict[tuple[str, str], str] = {
    ("A", "legal"):  "phase candidates & board.legal_moves (production)",
    ("A", "pseudo"): "phase candidates & board.pseudo_legal_moves",
    ("B", "pseudo"): "batch ray + set-intersection truncation (phase-native)",
    ("B", "legal"):  "phase-native B, post-filtered by board.legal_moves",
    ("C", "pseudo"): "sequential step with early halt (phase-native)",
    ("C", "legal"):  "phase-native C, post-filtered by board.legal_moves",
}


def _pseudo_legal_dests(board: chess.Board, origin_r: int,
                        origin_c: int) -> frozenset[tuple[int, int]]:
    """Mirror of occupation_aware_a._chess_legal_dests over pseudo-legal
    moves (rights + path + castling, no check filter)."""
    origin_sq = chess.square(origin_c, origin_r)
    out: set[tuple[int, int]] = set()
    for move in board.pseudo_legal_moves:
        if move.from_square == origin_sq:
            to_sq = move.to_square
            out.add((chess.square_rank(to_sq), chess.square_file(to_sq)))
    return frozenset(out)


def _solution_a_pseudo(board: chess.Board, pc: str, r: int, c: int,
                       charge: int) -> frozenset[tuple[int, int]]:
    """Variant of Solution A using pseudo_legal_moves — matches B/C's
    correctness target. Castling handled identically to production A."""
    candidates = _unobstructed_dests(pc, r, c, charge)
    if pc.upper() == "K":
        mover_color = chess.WHITE if charge == WHITE_CHARGE else chess.BLACK
        candidates = candidates | castle_king_destinations(board, mover_color)
    pseudo = _pseudo_legal_dests(board, r, c)
    return frozenset(candidates & pseudo)


def _solution_b_legal(board: chess.Board, pc: str, r: int, c: int,
                      charge: int, occupation) -> frozenset[tuple[int, int]]:
    """Solution B with a post-filter pass through board.legal_moves.
    The post-filter cost is the same that production A already pays;
    this lets B be compared to A at matched check-filtered correctness."""
    pseudo = occupation_aware_moves_b(board, pc, r, c, charge,
                                      occupation=occupation)
    legal = _chess_legal_dests(board, r, c)
    return frozenset(pseudo & legal)


def _solution_c_legal(board: chess.Board, pc: str, r: int, c: int,
                      charge: int, occupation) -> frozenset[tuple[int, int]]:
    """Solution C with post-filter — see _solution_b_legal."""
    pseudo = occupation_aware_moves_c(board, pc, r, c, charge,
                                      occupation=occupation)
    legal = _chess_legal_dests(board, r, c)
    return frozenset(pseudo & legal)


# (label, fn, kwargs-builder) per (solution, filter_mode).
# kwargs-builder takes the per-position occupation field and returns
# the kwargs to pass to fn; occupation-unaware solutions ignore it.
_VARIANT_RUNNERS: dict[tuple[str, str], tuple] = {
    ("A", "legal"):  (occupation_aware_moves_a, lambda occ: {}),
    ("A", "pseudo"): (_solution_a_pseudo,       lambda occ: {}),
    ("B", "pseudo"): (occupation_aware_moves_b, lambda occ: {"occupation": occ}),
    ("B", "legal"):  (_solution_b_legal,        lambda occ: {"occupation": occ}),
    ("C", "pseudo"): (occupation_aware_moves_c, lambda occ: {"occupation": occ}),
    ("C", "legal"):  (_solution_c_legal,        lambda occ: {"occupation": occ}),
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


def _bench_one_mode(mode: str, workload, repeats: int,
                    warmup: int) -> dict[str, dict[str, float]]:
    """Run A/B/C at the given correctness target and return stats."""
    stats: dict[str, dict[str, float]] = {}
    for sol in ("A", "B", "C"):
        fn, kwargs_for = _VARIANT_RUNNERS[(sol, mode)]
        if warmup > 0:
            _bench_solution(f"warmup-{sol}-{mode}", fn, workload,
                            kwargs_for, warmup)
        samples = _bench_solution(f"{sol}-{mode}", fn, workload,
                                  kwargs_for, repeats)
        stats[sol] = _stats_ns(samples)
    return stats


def _print_mode_table(mode: str,
                      stats: dict[str, dict[str, float]]) -> None:
    header_note = {
        "pseudo": ("pseudo-legal correctness (no king-safety check) — "
                   "matches B/C's native semantics; A uses "
                   "board.pseudo_legal_moves."),
        "legal":  ("legal correctness (king-safety check applied) — "
                   "matches A's native semantics; B/C get a post-filter "
                   "pass through board.legal_moves."),
    }[mode]
    print(f"=== filter: {mode} ===  {header_note}")
    print("Sol  n_calls   total (ms)   mean (us)   p50 (us)"
          "   p95 (us)   p99 (us)     calls/sec   description")
    print("-" * 120)
    for sol in ("A", "B", "C"):
        print(_format_row(sol, SOLUTION_DESCRIPTIONS[(sol, mode)],
                          stats[sol]))
    print()

    a_mean = stats["A"]["mean_us"] or 1.0
    print(f"Speedup vs Solution A (mean, {mode}):")
    for sol in ("A", "B", "C"):
        ratio = a_mean / (stats[sol]["mean_us"] or 1.0)
        print(f"  {sol}: {ratio:>6.2f}x")
    print()


def run(corpus_dir: Path, n_positions: int, seed: int,
        repeats: int, warmup: int, piece_filter: str | None,
        filter_modes: list[str],
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
          + f"; {repeats} repeats + {warmup} warmup; "
          + f"filter mode(s): {', '.join(filter_modes)}.")
    print()

    all_stats: dict[str, dict[str, dict[str, float]]] = {}
    for mode in filter_modes:
        mode_stats = _bench_one_mode(mode, workload, repeats, warmup)
        all_stats[mode] = mode_stats
        _print_mode_table(mode, mode_stats)

    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = ["solution", "filter_mode", "description",
                      "n_calls", "total_ms",
                      "mean_us", "p50_us", "p95_us", "p99_us",
                      "throughput_per_s",
                      "n_positions", "repeats", "warmup", "piece_filter",
                      "seed"]
        with out_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for mode in filter_modes:
                for sol in ("A", "B", "C"):
                    row = {"solution": sol,
                           "filter_mode": mode,
                           "description": SOLUTION_DESCRIPTIONS[(sol, mode)],
                           "n_positions": len(fens),
                           "repeats": repeats, "warmup": warmup,
                           "piece_filter": piece_filter or "",
                           "seed": seed}
                    row.update(all_stats[mode][sol])
                    writer.writerow(row)
        print(f"CSV written to: {out_path}")

    return all_stats


def main() -> int:
    default_corpus = (Path(__file__).resolve().parents[1]
                      / "results"
                      / "sweep_chain_lichess_drnykterstein_2026-04-14_N10")

    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
examples:
  # Default quick run — prints both pseudo-legal and legal tables
  python benchmark_solutions.py

  # Only the phase-native (pseudo-legal) comparison — fastest, fairest
  # head-to-head for "how fast is the phase operator itself?"
  python benchmark_solutions.py --filter pseudo --repeats 20

  # Only the check-filtered (legal) comparison — matches the production
  # semantics of Solution A.
  python benchmark_solutions.py --filter legal --repeats 20

  # Higher-precision numbers for the supplement
  python benchmark_solutions.py --n-positions 200 --repeats 20 --warmup 5

  # Only benchmark queens (where sliding-ray cost dominates)
  python benchmark_solutions.py --piece Q --repeats 50

  # Write CSV for later analysis (one row per (solution, filter_mode))
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
        "--filter", dest="filter_mode", type=str, default="both",
        choices=["pseudo", "legal", "both"],
        help="Correctness target at which all three solutions are "
             "timed. 'pseudo' = pseudo-legal moves (no king-safety "
             "check); A swaps to board.pseudo_legal_moves, B/C run "
             "as-is. 'legal' = board.legal_moves (king-safety "
             "applied); A runs as-is, B/C are post-filtered. 'both' "
             "prints one table per mode. Default: %(default)s.")
    parser.add_argument(
        "--out", type=Path, default=None,
        help="Optional CSV path for the summary stats. One row per "
             "(solution, filter_mode). Parent directory is created "
             "if missing. Default: stdout only.")
    args = parser.parse_args()

    if args.repeats < 1:
        parser.error("--repeats must be >= 1")
    if args.warmup < 0:
        parser.error("--warmup must be >= 0")
    if args.n_positions < 1:
        parser.error("--n-positions must be >= 1")

    filter_modes = (["pseudo", "legal"] if args.filter_mode == "both"
                    else [args.filter_mode])

    run(args.corpus, args.n_positions, args.seed,
        args.repeats, args.warmup, args.piece, filter_modes, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

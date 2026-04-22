"""§11.4 Occupation-Aware Phase Operators — four-way A/B/C experiment.

Samples positions from a corpus, runs Solutions A (post-hoc geometric
pruning), B (batch/set-intersection), and C (sequential/early-halt) for
every (polarization, origin) pair with the side-to-move's pieces,
compares each against python-chess's legal moves, and records all
pairwise agreements/disagreements.

Run from phase_operators/ directory:
    python occupation_equivalence_check.py \\
        --corpus ../results/sweep_chain_lichess_drnykterstein_2026-04-14_N10 \\
        [--n-positions 100] [--seed 42] [--out PATH]
"""
import argparse
import csv
import json
import random
import sys
import time
from pathlib import Path

# Windows console: default cp1252 cannot encode § or ≠ glyphs in the
# help text. Reconfigure stdout/stderr to UTF-8 so researchers see
# the supplement section references correctly on any platform.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import chess

from chess_spectral.phase_operators import (
    WHITE_CHARGE, BLACK_CHARGE, occupation_field_from_board,
    occupation_aware_moves_a,
    occupation_aware_moves_b,
    occupation_aware_moves_c,
)


_PIECE_CHARS = {
    chess.ROOK: "R",
    chess.BISHOP: "B",
    chess.QUEEN: "Q",
    chess.KING: "K",
    chess.KNIGHT: "N",
    chess.PAWN: "P",
}


def sample_positions_from_corpus(corpus_dir: Path, n: int,
                                 seed: int) -> list[tuple[str, int, int]]:
    """Return [(fen, game_id, ply), ...] sampled uniformly from the corpus.

    Each ndjson file's first two lines are metadata (bridge + game_header);
    subsequent lines each carry a 'fen' field.
    """
    ndjson_dir = corpus_dir / "ndjson"
    if not ndjson_dir.is_dir():
        raise FileNotFoundError(f"no ndjson/ under {corpus_dir}")
    records: list[tuple[str, int, int]] = []
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
                if "fen" not in rec or "ply" not in rec:
                    continue
                records.append((rec["fen"], rec.get("game", -1), rec["ply"]))
    rng = random.Random(seed)
    rng.shuffle(records)
    return records[:n]


def legal_moves_for_piece(board: chess.Board, origin_r: int,
                          origin_c: int) -> frozenset[tuple[int, int]]:
    """python-chess legal destinations from origin square (independent
    fourth channel; Solution A happens to delegate internally to this
    but only AFTER phase-space candidate generation and intersection)."""
    origin_sq = chess.square(origin_c, origin_r)
    out: set[tuple[int, int]] = set()
    for move in board.legal_moves:
        if move.from_square == origin_sq:
            to_sq = move.to_square
            out.add((chess.square_rank(to_sq), chess.square_file(to_sq)))
    return frozenset(out)


def _serialize_set(s) -> str:
    return ";".join(f"({r},{c})" for (r, c) in sorted(s))


def _iter_mover_pieces(board: chess.Board):
    """Yield (piece_char, origin_r, origin_c, mover_charge) for every
    side-to-move piece currently on the board."""
    mover_charge = WHITE_CHARGE if board.turn == chess.WHITE else BLACK_CHARGE
    for square, piece in board.piece_map().items():
        if piece.color != board.turn:
            continue
        yield (_PIECE_CHARS[piece.piece_type],
               chess.square_rank(square),
               chess.square_file(square),
               mover_charge)


def run(corpus_dir: Path, n_positions: int, seed: int, out_path: Path) -> dict:
    sampled = sample_positions_from_corpus(corpus_dir, n_positions, seed)
    print(f"Sampled {len(sampled)} positions from {corpus_dir.name}.")

    rows: list[dict] = []
    a_time_total = 0
    b_time_total = 0
    c_time_total = 0
    a_matches_chess = 0
    b_matches_chess = 0
    c_matches_chess = 0
    a_matches_b = 0
    b_matches_c = 0
    a_matches_c = 0
    first_abc_disagreements: list[dict] = []

    for (fen, game_id, ply) in sampled:
        board = chess.Board(fen)
        occupation = occupation_field_from_board(board)
        for (pc, r, c, charge) in _iter_mover_pieces(board):
            chess_dests = legal_moves_for_piece(board, r, c)

            t0 = time.perf_counter_ns()
            a_dests = occupation_aware_moves_a(board, pc, r, c, charge)
            a_ns = time.perf_counter_ns() - t0
            a_time_total += a_ns

            t0 = time.perf_counter_ns()
            b_dests = occupation_aware_moves_b(board, pc, r, c, charge,
                                               occupation=occupation)
            b_ns = time.perf_counter_ns() - t0
            b_time_total += b_ns

            t0 = time.perf_counter_ns()
            c_dests = occupation_aware_moves_c(board, pc, r, c, charge,
                                               occupation=occupation)
            c_ns = time.perf_counter_ns() - t0
            c_time_total += c_ns

            a_eq_chess = (a_dests == chess_dests)
            b_eq_chess = (b_dests == chess_dests)
            c_eq_chess = (c_dests == chess_dests)
            a_eq_b = (a_dests == b_dests)
            b_eq_c = (b_dests == c_dests)
            a_eq_c = (a_dests == c_dests)
            if a_eq_chess:
                a_matches_chess += 1
            if b_eq_chess:
                b_matches_chess += 1
            if c_eq_chess:
                c_matches_chess += 1
            if a_eq_b:
                a_matches_b += 1
            if b_eq_c:
                b_matches_c += 1
            if a_eq_c:
                a_matches_c += 1

            abc_agree = a_eq_b and b_eq_c
            if not abc_agree and len(first_abc_disagreements) < 5:
                first_abc_disagreements.append({
                    "fen": fen, "pc": pc, "r": r, "c": c,
                    "a_minus_b": a_dests - b_dests,
                    "b_minus_a": b_dests - a_dests,
                    "b_minus_c": b_dests - c_dests,
                    "c_minus_b": c_dests - b_dests,
                })

            rows.append({
                "position_fen": fen,
                "game_id": game_id,
                "ply": ply,
                "polarization": pc,
                "origin_row": r,
                "origin_col": c,
                "mover_charge": charge,
                "solution_a_dests": _serialize_set(a_dests),
                "solution_b_dests": _serialize_set(b_dests),
                "solution_c_dests": _serialize_set(c_dests),
                "python_chess_dests": _serialize_set(chess_dests),
                "a_equals_chess": "true" if a_eq_chess else "false",
                "b_equals_chess": "true" if b_eq_chess else "false",
                "c_equals_chess": "true" if c_eq_chess else "false",
                "a_equals_b": "true" if a_eq_b else "false",
                "b_equals_c": "true" if b_eq_c else "false",
                "a_equals_c": "true" if a_eq_c else "false",
                "a_missing_vs_chess": _serialize_set(chess_dests - a_dests),
                "a_extra_vs_chess": _serialize_set(a_dests - chess_dests),
                "b_missing_vs_chess": _serialize_set(chess_dests - b_dests),
                "b_extra_vs_chess": _serialize_set(b_dests - chess_dests),
                "c_missing_vs_chess": _serialize_set(chess_dests - c_dests),
                "c_extra_vs_chess": _serialize_set(c_dests - chess_dests),
                "solution_a_time_ns": a_ns,
                "solution_b_time_ns": b_ns,
                "solution_c_time_ns": c_ns,
            })

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "position_fen", "game_id", "ply", "polarization",
        "origin_row", "origin_col", "mover_charge",
        "solution_a_dests", "solution_b_dests", "solution_c_dests",
        "python_chess_dests",
        "a_equals_chess", "b_equals_chess", "c_equals_chess",
        "a_equals_b", "b_equals_c", "a_equals_c",
        "a_missing_vs_chess", "a_extra_vs_chess",
        "b_missing_vs_chess", "b_extra_vs_chess",
        "c_missing_vs_chess", "c_extra_vs_chess",
        "solution_a_time_ns", "solution_b_time_ns", "solution_c_time_ns",
    ]
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    total = len(rows)
    summary = {
        "total": total,
        "a_matches_chess": a_matches_chess,
        "b_matches_chess": b_matches_chess,
        "c_matches_chess": c_matches_chess,
        "a_matches_b": a_matches_b,
        "b_matches_c": b_matches_c,
        "a_matches_c": a_matches_c,
        "a_time_mean_us": (a_time_total / total / 1000) if total else 0.0,
        "b_time_mean_us": (b_time_total / total / 1000) if total else 0.0,
        "c_time_mean_us": (c_time_total / total / 1000) if total else 0.0,
        "first_abc_disagreements": first_abc_disagreements,
        "out_path": str(out_path),
    }
    return summary


def main() -> int:
    default_corpus = (Path(__file__).resolve().parents[1]
                      / "results" / "sweep_chain_lichess_drnykterstein_2026-04-14_N10")
    default_out = (Path(__file__).resolve().parents[1]
                   / "results" / "phase_operator_experiments"
                   / "exp2_occupation_equivalence_abc.csv")

    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  # Reproduce the §11.4 headline result (default 100 positions, seed 42)
  python occupation_equivalence_check.py
  # -> "A matches python-chess: 1153/1153 (100.00%)"
  # -> "B matches C:            1153/1153 (100.00%)"  (phase-native sanity)
  # -> "B matches python-chess: 1086/1153  (94.19%)"  (residual is check filter)

  # Larger sample for the supplement's stability claim
  python occupation_equivalence_check.py --n-positions 500 --seed 7

  # Different corpus (must contain an ndjson/ subdirectory; see
  # docs/chess-maths/results/*/ for available samples)
  python occupation_equivalence_check.py --corpus ../results/sweep_hf_2026-04-20_N50

  # CI lock on phase-native agreement: A ≠ B or B ≠ C exits nonzero
  python occupation_equivalence_check.py --fail-on-disagreement

see also:
  benchmark_solutions.py              — timings for A/B/C at same correctness
  PHASE_OPERATOR_SUPPLEMENT.md §11.4  — the experiment this CLI validates
""")
    parser.add_argument(
        "--corpus", type=Path, default=default_corpus,
        help="Corpus directory containing an ndjson/ subdirectory of "
             "per-game FEN streams. Default: the drnykterstein N=10 "
             "sample at ../results/.")
    parser.add_argument(
        "--n-positions", type=int, default=100,
        help="Number of positions to sample from the corpus. Default "
             "100 (matches supplement §11.4 headline). Increase for "
             "tighter statistical bounds.")
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Random seed for deterministic position sampling. "
             "Default: 42 (matches supplement §11.4 reproducibility).")
    parser.add_argument(
        "--out", type=Path, default=default_out,
        help="Output CSV path (parents created). One row per "
             "(position, polarization, origin) sampled; columns "
             "include all four channels' destination sets and "
             "per-solution timings. Default: "
             "../results/phase_operator_experiments/"
             "exp2_occupation_equivalence_abc.csv (gitignored).")
    parser.add_argument(
        "--fail-on-disagreement", action="store_true",
        help="Exit nonzero if Solutions A, B, and C disagree on any "
             "sampled piece (i.e., any row where A ≠ B or B ≠ C). "
             "The supplement §11.4 claim is that A/B/C converge 100%% "
             "on every position; use in CI to lock the phase-native "
             "cross-validation.")
    args = parser.parse_args()

    summary = run(args.corpus, args.n_positions, args.seed, args.out)
    total = summary["total"]
    print()
    print("§11.4 complete (four-way A/B/C/python-chess):")
    print(f"  A matches python-chess: {summary['a_matches_chess']}/{total} "
          f"({100 * summary['a_matches_chess'] / total:.2f}%)")
    print(f"  B matches python-chess: {summary['b_matches_chess']}/{total} "
          f"({100 * summary['b_matches_chess'] / total:.2f}%)")
    print(f"  C matches python-chess: {summary['c_matches_chess']}/{total} "
          f"({100 * summary['c_matches_chess'] / total:.2f}%)")
    print(f"  A matches B:            {summary['a_matches_b']}/{total} "
          f"({100 * summary['a_matches_b'] / total:.2f}%)")
    print(f"  B matches C:            {summary['b_matches_c']}/{total} "
          f"({100 * summary['b_matches_c'] / total:.2f}%)")
    print(f"  A matches C:            {summary['a_matches_c']}/{total} "
          f"({100 * summary['a_matches_c'] / total:.2f}%)")
    print(f"  Mean A time: {summary['a_time_mean_us']:.1f} us")
    print(f"  Mean B time: {summary['b_time_mean_us']:.1f} us")
    print(f"  Mean C time: {summary['c_time_mean_us']:.1f} us")
    print()
    print(f"CSV written to: {summary['out_path']}")

    abc_disagreements = summary["first_abc_disagreements"]
    if abc_disagreements:
        print(f"\nFirst {len(abc_disagreements)} A/B/C disagreements:",
              file=sys.stderr)
        for d in abc_disagreements:
            print(f"  {d['pc']}@({d['r']},{d['c']}) fen={d['fen']}",
                  file=sys.stderr)
            print(f"    A-B: {sorted(d['a_minus_b'])}", file=sys.stderr)
            print(f"    B-A: {sorted(d['b_minus_a'])}", file=sys.stderr)
            print(f"    B-C: {sorted(d['b_minus_c'])}", file=sys.stderr)
            print(f"    C-B: {sorted(d['c_minus_b'])}", file=sys.stderr)

    if args.fail_on_disagreement:
        if (summary["a_matches_b"] != total
                or summary["b_matches_c"] != total):
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

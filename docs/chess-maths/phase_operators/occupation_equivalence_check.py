"""§11.4 Occupation-Aware Phase Operators — parallel B + C experiment.

Samples positions from a corpus, runs Solutions B and C for every
(polarization, origin) pair with the side-to-move's pieces, compares
each against python-chess's legal moves (Solution A reference), and
records agreements/disagreements.

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

import chess

from occupation_field import (
    WHITE_CHARGE, BLACK_CHARGE, occupation_field_from_board,
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
    """Solution A reference: python-chess legal destinations from origin square."""
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
    b_time_total = 0
    c_time_total = 0
    b_matches_a = 0
    c_matches_a = 0
    b_matches_c = 0
    first_bc_disagreements: list[dict] = []

    for (fen, game_id, ply) in sampled:
        board = chess.Board(fen)
        occupation = occupation_field_from_board(board)
        for (pc, r, c, charge) in _iter_mover_pieces(board):
            a_dests = legal_moves_for_piece(board, r, c)

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

            b_eq_a = (b_dests == a_dests)
            c_eq_a = (c_dests == a_dests)
            b_eq_c = (b_dests == c_dests)
            if b_eq_a:
                b_matches_a += 1
            if c_eq_a:
                c_matches_a += 1
            if b_eq_c:
                b_matches_c += 1
            elif len(first_bc_disagreements) < 5:
                first_bc_disagreements.append({
                    "fen": fen, "pc": pc, "r": r, "c": c,
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
                "b_equals_a": "true" if b_eq_a else "false",
                "c_equals_a": "true" if c_eq_a else "false",
                "b_equals_c": "true" if b_eq_c else "false",
                "b_missing_vs_a": _serialize_set(a_dests - b_dests),
                "b_extra_vs_a": _serialize_set(b_dests - a_dests),
                "c_missing_vs_a": _serialize_set(a_dests - c_dests),
                "c_extra_vs_a": _serialize_set(c_dests - a_dests),
                "b_minus_c": _serialize_set(b_dests - c_dests),
                "c_minus_b": _serialize_set(c_dests - b_dests),
                "solution_b_time_ns": b_ns,
                "solution_c_time_ns": c_ns,
            })

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "position_fen", "game_id", "ply", "polarization",
        "origin_row", "origin_col", "mover_charge",
        "solution_a_dests", "solution_b_dests", "solution_c_dests",
        "b_equals_a", "c_equals_a", "b_equals_c",
        "b_missing_vs_a", "b_extra_vs_a",
        "c_missing_vs_a", "c_extra_vs_a",
        "b_minus_c", "c_minus_b",
        "solution_b_time_ns", "solution_c_time_ns",
    ]
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    total = len(rows)
    summary = {
        "total": total,
        "b_matches_a": b_matches_a,
        "c_matches_a": c_matches_a,
        "b_matches_c": b_matches_c,
        "b_time_mean_us": (b_time_total / total / 1000) if total else 0.0,
        "c_time_mean_us": (c_time_total / total / 1000) if total else 0.0,
        "first_bc_disagreements": first_bc_disagreements,
        "out_path": str(out_path),
    }
    return summary


def main() -> int:
    default_corpus = (Path(__file__).resolve().parents[1]
                      / "results" / "sweep_chain_lichess_drnykterstein_2026-04-14_N10")
    default_out = (Path(__file__).resolve().parents[1]
                   / "results" / "phase_operator_experiments"
                   / "exp2_occupation_equivalence.csv")

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=default_corpus)
    parser.add_argument("--n-positions", type=int, default=100)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", type=Path, default=default_out)
    parser.add_argument("--fail-on-disagreement", action="store_true",
                        help="Exit 1 if B ≠ C anywhere.")
    args = parser.parse_args()

    summary = run(args.corpus, args.n_positions, args.seed, args.out)
    total = summary["total"]
    print()
    print("§11.4 complete:")
    print(f"  B matches A: {summary['b_matches_a']}/{total} "
          f"({100 * summary['b_matches_a'] / total:.2f}%)")
    print(f"  C matches A: {summary['c_matches_a']}/{total} "
          f"({100 * summary['c_matches_a'] / total:.2f}%)")
    print(f"  B matches C: {summary['b_matches_c']}/{total} "
          f"({100 * summary['b_matches_c'] / total:.2f}%)")
    print(f"  Mean B time: {summary['b_time_mean_us']:.1f} us")
    print(f"  Mean C time: {summary['c_time_mean_us']:.1f} us")
    print()
    print(f"CSV written to: {summary['out_path']}")

    bc_disagreements = summary["first_bc_disagreements"]
    if bc_disagreements:
        print(f"\nFirst {len(bc_disagreements)} B≠C disagreements:", file=sys.stderr)
        for d in bc_disagreements:
            print(f"  {d['pc']}@({d['r']},{d['c']}) fen={d['fen']}", file=sys.stderr)
            print(f"    B-C: {sorted(d['b_minus_c'])}", file=sys.stderr)
            print(f"    C-B: {sorted(d['c_minus_b'])}", file=sys.stderr)

    if args.fail_on_disagreement:
        if summary["b_matches_c"] != total:
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

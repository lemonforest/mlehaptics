"""§11.5 CLI: phase-tuple similarity experiment with path-1 reference channel.

Samples positions from a corpus, enumerates legal transitions per position,
computes phase_similarity (path 2) and is_check_unsafe_phasecast (path 1)
for each transition, compares path-1 against python-chess's geometric
is_check (reference), and emits the §11.5.4 CSV plus Spearman rho summary
per §11.5.5.

Run from phase_operators/ directory:
    python similarity_experiment.py \
        --corpus ../results/sweep_chain_lichess_drnykterstein_2026-04-14_N10 \
        [--n-positions 100] [--seed 42] [--out PATH]
"""
import argparse
import csv
import json
import random
import sys
import time
from pathlib import Path

# Windows console: default cp1252 cannot encode § glyphs used in the
# help text and the §11.5.5 stdout summary. Reconfigure stdout/stderr
# to UTF-8 so researchers see supplement section references on any
# platform.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import chess
import numpy as np
from scipy.stats import spearmanr

from chess_spectral.phase_operators import (
    move_leaves_king_in_check, phasecast_is_check,
)
from phase_similarity import phase_similarity


PIECE_VALUE = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9,
    chess.KING: 0,
}

PIECE_POLARIZATION = {
    chess.PAWN: "P",
    chess.KNIGHT: "N",
    chess.BISHOP: "B",
    chess.ROOK: "R",
    chess.QUEEN: "Q",
    chess.KING: "K",
}


def _move_leaves_king_in_check_geom(board: chess.Board,
                                    move: chess.Move) -> bool:
    """Reference: same predicate computed via python-chess's is_check."""
    board.push(move)
    try:
        board.turn = not board.turn
        result = board.is_check()
        board.turn = not board.turn
    finally:
        board.pop()
    return result


def sample_positions_from_corpus(corpus_dir: Path, n: int, seed: int):
    """Yield (fen, game_id, ply) tuples sampled uniformly from the corpus
    ndjson shards. Each ndjson line holds one ply's FEN."""
    ndjson_dir = corpus_dir / "ndjson"
    if not ndjson_dir.is_dir():
        raise FileNotFoundError(f"No ndjson/ under {corpus_dir}")
    shards = sorted(ndjson_dir.glob("game_*.ndjson"))
    if not shards:
        raise FileNotFoundError(f"No game_*.ndjson under {ndjson_dir}")

    all_rows = []
    for shard in shards:
        with shard.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if "fen" not in d or "ply" not in d:
                    continue
                all_rows.append((d["fen"], d.get("game", shard.stem),
                                 int(d["ply"])))

    if not all_rows:
        raise RuntimeError(f"No FEN rows found in {ndjson_dir}")

    rng = random.Random(seed)
    if n >= len(all_rows):
        chosen = all_rows
    else:
        chosen = rng.sample(all_rows, n)
    return chosen


def _delta_material(board: chess.Board, move: chess.Move) -> int:
    """Material captured by the mover (0 for quiet moves).

    En passant captures a pawn even though to-square is empty.
    Promotions add the promotion piece value minus the pawn value.
    """
    delta = 0
    if board.is_capture(move):
        if board.is_en_passant(move):
            delta += PIECE_VALUE[chess.PAWN]
        else:
            captured = board.piece_at(move.to_square)
            if captured is not None:
                delta += PIECE_VALUE[captured.piece_type]
    if move.promotion is not None:
        delta += PIECE_VALUE[move.promotion] - PIECE_VALUE[chess.PAWN]
    return delta


def _slice_by_piece(rows, piece_letter):
    return [r for r in rows if r["polarization_type"] == piece_letter]


def _spearman_or_nan(xs, ys):
    if len(xs) < 2:
        return float("nan"), len(xs)
    xs_arr = np.asarray(xs, dtype=float)
    ys_arr = np.asarray(ys, dtype=float)
    if np.all(xs_arr == xs_arr[0]) or np.all(ys_arr == ys_arr[0]):
        return float("nan"), len(xs)
    rho, _ = spearmanr(xs_arr, ys_arr)
    return float(rho), len(xs)


def run(corpus_dir: Path, n_positions: int, seed: int, out_path: Path,
        fail_on_mismatch: bool = False) -> dict:
    samples = sample_positions_from_corpus(corpus_dir, n_positions, seed)
    positions_used = len(samples)

    out_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "position_fen", "game_id", "ply",
        "polarization_type", "transition_uci",
        "phase_similarity",
        "is_check_unsafe", "is_check_unsafe_phasecast",
        "phasecast_matches_chess",
        "path1_time_ns", "path2_time_ns",
        "is_capture", "delta_material",
        "delta_v1", "stockfish_eval",
        "kappa_annihilate", "kappa_threat",
    ]

    rows_for_corr = []
    mismatches = []
    total_transitions = 0
    phasecast_matches = 0
    path1_time_sum = 0
    path2_time_sum = 0
    pychess_time_sum = 0
    path1_count = 0
    path2_count = 0
    pychess_count = 0

    with out_path.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()

        for fen, game_id, ply in samples:
            try:
                board = chess.Board(fen)
            except ValueError:
                continue
            for move in board.pseudo_legal_moves:
                piece = board.piece_at(move.from_square)
                if piece is None:
                    continue
                pol = PIECE_POLARIZATION[piece.piece_type]

                t0 = time.perf_counter_ns()
                is_check_unsafe_phasecast = move_leaves_king_in_check(
                    board, move)
                t1 = time.perf_counter_ns()
                is_check_unsafe_ref = _move_leaves_king_in_check_geom(
                    board, move)
                t2 = time.perf_counter_ns()
                sim = phase_similarity(board, move)
                t3 = time.perf_counter_ns()

                path1_ns = t1 - t0
                pychess_ns = t2 - t1
                path2_ns = t3 - t2

                path1_time_sum += path1_ns
                path1_count += 1
                pychess_time_sum += pychess_ns
                pychess_count += 1
                path2_time_sum += path2_ns
                path2_count += 1

                matches = (is_check_unsafe_phasecast == is_check_unsafe_ref)
                if matches:
                    phasecast_matches += 1
                else:
                    mismatches.append((fen, move.uci(),
                                       is_check_unsafe_phasecast,
                                       is_check_unsafe_ref))

                is_cap = board.is_capture(move)
                dmat = _delta_material(board, move)

                row = {
                    "position_fen": fen,
                    "game_id": game_id,
                    "ply": ply,
                    "polarization_type": pol,
                    "transition_uci": move.uci(),
                    "phase_similarity": f"{sim:.12f}",
                    "is_check_unsafe": str(is_check_unsafe_ref).lower(),
                    "is_check_unsafe_phasecast":
                        str(is_check_unsafe_phasecast).lower(),
                    "phasecast_matches_chess": str(matches).lower(),
                    "path1_time_ns": path1_ns,
                    "path2_time_ns": path2_ns,
                    "is_capture": str(is_cap).lower(),
                    "delta_material": dmat,
                    "delta_v1": "",
                    "stockfish_eval": "",
                    "kappa_annihilate": "",
                    "kappa_threat": "",
                }
                writer.writerow(row)

                rows_for_corr.append({
                    "polarization_type": pol,
                    "phase_similarity": sim,
                    "is_check_unsafe": 1 if is_check_unsafe_ref else 0,
                    "is_capture": is_cap,
                })
                total_transitions += 1

    path1_mean_us = (path1_time_sum / path1_count / 1000.0
                     if path1_count else float("nan"))
    path2_mean_us = (path2_time_sum / path2_count / 1000.0
                     if path2_count else float("nan"))
    pychess_mean_us = (pychess_time_sum / pychess_count / 1000.0
                       if pychess_count else float("nan"))

    sims_all = [r["phase_similarity"] for r in rows_for_corr]
    checks_all = [r["is_check_unsafe"] for r in rows_for_corr]
    rho_all, n_all = _spearman_or_nan(sims_all, checks_all)

    per_piece = {}
    for letter in ("N", "B", "R", "Q", "K", "P"):
        sub = _slice_by_piece(rows_for_corr, letter)
        xs = [r["phase_similarity"] for r in sub]
        ys = [r["is_check_unsafe"] for r in sub]
        per_piece[letter] = _spearman_or_nan(xs, ys)

    cap_rows = [r for r in rows_for_corr if r["is_capture"]]
    non_rows = [r for r in rows_for_corr if not r["is_capture"]]
    rho_cap = _spearman_or_nan(
        [r["phase_similarity"] for r in cap_rows],
        [r["is_check_unsafe"] for r in cap_rows])
    rho_non = _spearman_or_nan(
        [r["phase_similarity"] for r in non_rows],
        [r["is_check_unsafe"] for r in non_rows])

    return {
        "positions_used": positions_used,
        "total_transitions": total_transitions,
        "phasecast_matches": phasecast_matches,
        "mismatches": mismatches,
        "rho_all": rho_all,
        "n_all": n_all,
        "per_piece": per_piece,
        "rho_capture": rho_cap,
        "rho_noncapture": rho_non,
        "path1_mean_us": path1_mean_us,
        "path2_mean_us": path2_mean_us,
        "pychess_mean_us": pychess_mean_us,
        "fail_on_mismatch": fail_on_mismatch,
    }


def _format_rho(pair):
    rho, n = pair
    if rho != rho:  # NaN
        return f"nan      (n={n})"
    return f"{rho:+.3f}   (n={n})"


def print_summary(result: dict) -> None:
    total = result["total_transitions"]
    matches = result["phasecast_matches"]
    if total:
        match_pct = 100.0 * matches / total
    else:
        match_pct = float("nan")

    per_piece = result["per_piece"]

    print("\n§11.5 complete:")
    print(f"  Positions sampled:           {result['positions_used']}")
    print(f"  Total transitions:           {total}")
    print("")
    print("  Path 1 reference validation:")
    print(f"    phasecast_matches_chess:   {matches}/{total} "
          f"({match_pct:.2f}%)")
    if matches != total:
        print("    WARNING: path-1 disagrees with python-chess. First 5:")
        for mm in result["mismatches"][:5]:
            print(f"      fen={mm[0]} move={mm[1]} "
                  f"phasecast={mm[2]} reference={mm[3]}")
    print("")
    print("  Path 2 correlation analysis:")
    print(f"    Spearman rho(phase_similarity, is_check_unsafe):")
    print(f"      all transitions:         "
          f"{_format_rho((result['rho_all'], result['n_all']))}")
    print(f"      knight moves:            "
          f"{_format_rho(per_piece['N'])}")
    print(f"      bishop moves:            "
          f"{_format_rho(per_piece['B'])}")
    print(f"      rook moves:              "
          f"{_format_rho(per_piece['R'])}")
    print(f"      queen moves:             "
          f"{_format_rho(per_piece['Q'])}")
    print(f"      king moves:              "
          f"{_format_rho(per_piece['K'])}")
    print(f"      pawn moves:              "
          f"{_format_rho(per_piece['P'])}")
    print(f"      captures:                "
          f"{_format_rho(result['rho_capture'])}")
    print(f"      non-captures:            "
          f"{_format_rho(result['rho_noncapture'])}")
    print("")
    print("  Timing:")
    print(f"    python-chess is_check (reference):    "
          f"{result['pychess_mean_us']:.1f} us")
    if result['pychess_mean_us'] > 0:
        ratio = result['path1_mean_us'] / result['pychess_mean_us']
        print(f"    path-1 phasecast is_check:            "
              f"{result['path1_mean_us']:.1f} us   ({ratio:.1f}x slower)")
    else:
        print(f"    path-1 phasecast is_check:            "
              f"{result['path1_mean_us']:.1f} us")
    print(f"    path-2 phase_similarity:              "
          f"{result['path2_mean_us']:.1f} us   "
          f"(encoder call dominates)")
    print("")

    slices = [
        ("all", result["rho_all"]),
        ("knight", per_piece["N"][0]),
        ("bishop", per_piece["B"][0]),
        ("rook", per_piece["R"][0]),
        ("queen", per_piece["Q"][0]),
        ("king", per_piece["K"][0]),
        ("pawn", per_piece["P"][0]),
        ("capture", result["rho_capture"][0]),
        ("non-capture", result["rho_noncapture"][0]),
    ]
    best_name = None
    best_abs = 0.0
    for name, rho in slices:
        if rho != rho:
            continue
        if abs(rho) > best_abs:
            best_abs = abs(rho)
            best_name = name

    print("  Decision (§11.5.6):")
    print("    If |rho| > 0.3 in any slice: phase similarity is a "
          "candidate check-filter signal")
    print("    If |rho| < 0.1 across all slices: path 2 for check "
          "filtering is closed")
    if best_name is None:
        interp = ("no valid Spearman rho computed; path 2 outcome "
                  "indeterminate from this run")
    elif best_abs > 0.3:
        interp = (f"phase similarity correlates with check-unsafety at "
                  f"|rho|={best_abs:.2f} in the {best_name} slice "
                  f"- path 2 viable")
    elif best_abs < 0.1:
        interp = (f"phase similarity does not correlate with "
                  f"check-unsafety (max |rho|={best_abs:.2f}); path 2 "
                  f"for check filtering closed")
    else:
        interp = (f"phase similarity weakly correlates with "
                  f"check-unsafety (max |rho|={best_abs:.2f} in "
                  f"{best_name} slice); path 2 not clearly viable or "
                  f"closed - researcher interprets")
    print(f"    Current result: {interp}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  # Reproduce the §11.5 headline result (drnykterstein N=10 corpus)
  python similarity_experiment.py
  # -> writes exp3_phase_similarity.csv
  # -> prints Spearman ρ(phase_similarity, is_check_unsafe) per
  #    polarization slice; headline |ρ|=0.097 max (validated null)

  # Larger sample for tighter bounds on the §11.5.6 null claim
  python similarity_experiment.py --n-positions 500 --seed 7

  # Different corpus (§11.5 was validated three-way in §12 across
  # drnykterstein GM-classical, ashchess FM-blitz, fishtest engine-blitz)
  python similarity_experiment.py \\
      --corpus ../results/sweep_hf_2026-04-20_N50 \\
      --out ../results/phase_operator_experiments/exp3_phase_similarity_hf.csv

  # CI lock on path-1 correctness (phase_check_detection vs python-chess)
  python similarity_experiment.py --fail-on-mismatch

see also:
  partition_experiment.py              — §11.6 position-level partition detection
  PHASE_OPERATOR_SUPPLEMENT.md §11.5   — the experiment this CLI runs
""")
    parser.add_argument(
        "--corpus", type=Path,
        default=Path("../results/"
                     "sweep_chain_lichess_drnykterstein_2026-04-14_N10"),
        help="Corpus directory containing an ndjson/ subdirectory of "
             "per-game FEN streams. Default: the drnykterstein N=10 "
             "sample that the §11.5.6 null result was measured on.")
    parser.add_argument(
        "--n-positions", type=int, default=100,
        help="Positions to sample from the corpus. Every pseudo-legal "
             "transition out of each sampled position becomes one row. "
             "Default 100 (~3000-3500 transitions; matches supplement "
             "§11.5 headline).")
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Random seed for deterministic position sampling. "
             "Default 42 (matches supplement §11.5 reproducibility).")
    parser.add_argument(
        "--out", type=Path,
        default=Path("../results/phase_operator_experiments/"
                     "exp3_phase_similarity.csv"),
        help="Output CSV path (parents created). Schema defined by "
             "§11.5.4: per-transition phase_similarity, "
             "is_check_unsafe (python-chess reference), "
             "is_check_unsafe_phasecast (path-1 reference), "
             "phasecast_matches_chess, per-path timings, capture "
             "flag, delta_material. §12 evaluate_encoder.py consumes "
             "this CSV as input.")
    parser.add_argument(
        "--fail-on-mismatch", action="store_true",
        help="Exit nonzero if path-1 phasecast_is_check disagrees "
             "with python-chess's is_check on any sampled transition. "
             "The §11.5 path-1 supplement claim is that this never "
             "fires (validated 3393/3393); use in CI to lock the "
             "phase-native check-detector correctness guarantee.")
    args = parser.parse_args()

    result = run(args.corpus, args.n_positions, args.seed, args.out,
                 fail_on_mismatch=args.fail_on_mismatch)
    print_summary(result)
    print(f"\nCSV written to: {args.out}")

    if args.fail_on_mismatch and (
            result["phasecast_matches"] != result["total_transitions"]):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

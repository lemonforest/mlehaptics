"""Phase 1c.2 — §10.10 T3 Shannon information per move.

For every PLAYED ply in a corpus compute

    I_move = log2 |M(s)|  -  log2 P(chosen | WTHOR_empirical_freq)

using the WTHOR opening-book frequencies (see
``opening_book_loader.py``).  The formula is the pure-Shannon
bookkeeping from §10.10 T3 / chess-maths §10.8 without the
Boltzmann-policy embedding (which would require additional
parameter inference).

Smoothing
---------
Uncovered moves (positions not in the book, OR the specific
resulting position of a move not in the book) are handled by
add-alpha Laplace smoothing with alpha = 1 by default.  Under Laplace
smoothing, a totally-unseen position falls back to uniform
probability 1/|M(s)| per move, giving I_move = 2 * log2 |M(s)|.
Positions where some but not all moves have book entries give
intermediate values.

Coverage is tracked separately so we can split statistics by
"in-book" (at least one successor has nonzero count) vs "out-of-
book" (all successors count zero).

Outputs
-------
    results/phase1c_shannon_info.json   : aggregate + per-game stats
    results/phase1c_shannon_per_move.csv: one row per played ply
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

from othello_utils import BLACK, N, OthelloBoard
from othello_pgn_loader import _ensure_utf8_stdio, parse_pgn_file, replay
from opening_book_loader import (
    OpeningBookFreq,
    canonical_key,
    enumerate_query_keys,
)
from d4_z2 import project_irrep

_ensure_utf8_stdio()


def _a1_minus_energy(sig: np.ndarray) -> float:
    return float(np.linalg.norm(project_irrep(sig, "A1-")) ** 2)


# ---------------------------------------------------------------------------
# Per-move computation
# ---------------------------------------------------------------------------


def compute_i_move(
    board: OthelloBoard,
    chosen: int,
    book: OpeningBookFreq,
    laplace: float,
) -> dict:
    """Compute I_move for a single played ply and return
    diagnostics for tracking."""
    legal = board.legal_moves()
    if not legal or chosen not in legal:
        raise ValueError(
            f"chosen move {chosen} not legal from position "
            f"(legal = {legal})"
        )

    # Raw book counts for every legal move's successor position.
    raw_counts: dict[int, int] = {}
    for m in legal:
        child = board.copy()
        child.play(m)
        raw_counts[m] = book.count_at(child.state, child.side_to_move)

    total_raw = sum(raw_counts.values())
    denom = total_raw + laplace * len(legal)
    # Smoothed probabilities
    prob = {m: (raw_counts[m] + laplace) / denom for m in legal}

    p_chosen = prob[chosen]
    log2_m = math.log2(len(legal))
    i_move = log2_m - math.log2(p_chosen)

    return {
        "i_move": i_move,
        "log2_m": log2_m,
        "p_chosen": p_chosen,
        "n_legal": len(legal),
        "total_raw_count": total_raw,
        "chosen_raw_count": raw_counts[chosen],
        "in_book": total_raw > 0,
        "chosen_in_book": raw_counts[chosen] > 0,
    }


# ---------------------------------------------------------------------------
# Corpus walker
# ---------------------------------------------------------------------------


def run_corpus(
    pgn_path: Path, book: OpeningBookFreq, laplace: float
) -> tuple[list[dict], list[dict]]:
    """Return (per_ply_records, per_game_records)."""
    games = parse_pgn_file(pgn_path)
    per_ply: list[dict] = []
    per_game: list[dict] = []
    for gi, g in enumerate(games):
        try:
            bb_final, states, move_log = replay(g["moves"])
        except Exception as exc:
            print(f"game {gi} replay failed: {exc}", file=sys.stderr)
            continue
        game_i_moves: list[float] = []
        game_in_book_count = 0
        for ply, entry in enumerate(move_log):
            if entry["is_pass"]:
                continue
            st = states[ply]
            board = OthelloBoard()
            board.state = st.copy()
            board.side_to_move = entry["side"]
            chosen = entry["idx"]
            try:
                diag = compute_i_move(board, chosen, book, laplace)
            except ValueError:
                continue
            sig_now = st.astype(float)
            rec = {
                "game": gi,
                "ply": ply,
                "side_to_move": entry["side"],
                "chosen_idx": chosen,
                "n_legal": diag["n_legal"],
                "n_empties": int(np.sum(st == 0)),
                "i_move_bits": diag["i_move"],
                "log2_m_bits": diag["log2_m"],
                "p_chosen": diag["p_chosen"],
                "total_raw_count": diag["total_raw_count"],
                "chosen_raw_count": diag["chosen_raw_count"],
                "in_book": int(diag["in_book"]),
                "chosen_in_book": int(diag["chosen_in_book"]),
                "a1_minus_energy": _a1_minus_energy(sig_now),
            }
            per_ply.append(rec)
            game_i_moves.append(diag["i_move"])
            if diag["in_book"]:
                game_in_book_count += 1
        bcount, wcount, _ = bb_final.disc_counts()
        per_game.append(
            {
                "game": gi,
                "black": g["headers"].get("Black", ""),
                "white": g["headers"].get("White", ""),
                "final_disc_diff": bcount - wcount,
                "abs_disc_diff": abs(bcount - wcount),
                "mean_i_move": (
                    float(np.mean(game_i_moves)) if game_i_moves else 0.0
                ),
                "sum_i_move": (
                    float(np.sum(game_i_moves)) if game_i_moves else 0.0
                ),
                "n_moves_scored": len(game_i_moves),
                "in_book_moves": game_in_book_count,
                "in_book_fraction": (
                    game_in_book_count / max(len(game_i_moves), 1)
                ),
            }
        )
    return per_ply, per_game


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    default_pgn = (
        Path(__file__).resolve().parent.parent
        / "dataset" / "liveothello_Barcelona_EGP_2026.pgn"
    )
    default_book = (
        Path(__file__).resolve().parent.parent
        / "dataset" / "reversi_scripts" / "opening_book_freq.csv.bz2"
    )
    default_results = (
        Path(__file__).resolve().parent.parent / "results"
    )
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  # Default: Barcelona EGP 2026 vs WTHOR opening book, Laplace
  # alpha = 1.
  python research/shannon_info_runner.py

  # Custom smoothing (alpha = 0.5 biases toward empirical)
  python research/shannon_info_runner.py --laplace 0.5

  # Write outputs to a custom directory (useful for A/B comparison)
  python research/shannon_info_runner.py --results-dir /tmp/t3-run

reading the output:
  'mean_i_move' is bits per played move, averaged per game.  Early-
  game moves have small i_move (predictable, book-backed); mid-game
  moves have larger i_move (rarer).  The headline correlations are
  reported on stdout and in the JSON file.  Use the per-move CSV
  to plot I_move as a function of n_empties (game phase).

caveats:
  Book coverage drops below ~10 empties empty count (see
  opening_book_loader.py --help).  Out-of-book plies use Laplace-
  smoothed uniform probabilities, making their I_move floor at
  2 * log2 |M(s)|.  The 'in_book_fraction' per game lets you split
  statistics.
""",
    )
    parser.add_argument(
        "--pgn", type=Path, default=default_pgn,
        help="Path to an Othello PGN corpus (default: Barcelona "
             "EGP 2026).  Must be replayable through OthelloBoard.",
    )
    parser.add_argument(
        "--book", type=Path, default=default_book,
        help="Path to opening_book_freq.csv.bz2 (default: the file "
             "vendored in dataset/reversi_scripts/).",
    )
    parser.add_argument(
        "--laplace", type=float, default=1.0,
        help="Laplace-smoothing alpha.  alpha=0 gives raw empirical "
             "probabilities but fails on uncovered moves "
             "(log 0 = -inf).  alpha=1 is standard add-one; "
             "larger values bias toward uniform.  Default: 1.0.",
    )
    parser.add_argument(
        "--results-dir", type=Path, default=default_results,
        help="Output directory for phase1c_shannon_info.json and "
             "phase1c_shannon_per_move.csv.  Parents are created.",
    )
    parser.add_argument(
        "--quiet", action="store_true",
        help="Suppress stdout summary; files are still written.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    args.results_dir.mkdir(parents=True, exist_ok=True)

    print(f"corpus: {args.pgn}")
    print(f"book:   {args.book}")
    print(f"Laplace alpha: {args.laplace}")

    keys, _n_plies = enumerate_query_keys(args.pgn)
    print(f"query-set canonical keys: {len(keys)}")
    print("loading book (this can take ~60 s)...")
    book = OpeningBookFreq.load(args.book, query_set=keys)
    print(
        f"book: scanned {book.n_rows_scanned}, kept "
        f"{book.n_rows_kept} (unique {len(book._index)})"
    )

    per_ply, per_game = run_corpus(args.pgn, book, args.laplace)
    print(
        f"scored {len(per_ply)} plies across {len(per_game)} games"
    )

    # Correlations
    i_arr = np.array([r["i_move_bits"] for r in per_ply])
    a1_arr = np.array([r["a1_minus_energy"] for r in per_ply])
    nl_arr = np.array([r["n_legal"] for r in per_ply])
    inbook_mask = np.array([bool(r["in_book"]) for r in per_ply])
    sp_i_a1 = spearmanr(i_arr, a1_arr)
    sp_i_nl = spearmanr(i_arr, nl_arr)
    if inbook_mask.sum() > 2:
        sp_in_i_a1 = spearmanr(i_arr[inbook_mask], a1_arr[inbook_mask])
    else:
        sp_in_i_a1 = None

    game_mean_i = np.array([g["mean_i_move"] for g in per_game])
    game_diff = np.array([g["abs_disc_diff"] for g in per_game])
    sp_mi_diff = spearmanr(game_mean_i, game_diff)

    summary = {
        "corpus": str(args.pgn),
        "book": str(args.book),
        "laplace": args.laplace,
        "n_plies_scored": len(per_ply),
        "n_games": len(per_game),
        "in_book_fraction_overall": float(inbook_mask.mean()),
        "mean_i_move_bits": float(i_arr.mean()),
        "std_i_move_bits": float(i_arr.std()),
        "mean_i_move_bits_in_book_only": (
            float(i_arr[inbook_mask].mean()) if inbook_mask.any() else None
        ),
        "mean_i_move_bits_out_of_book_only": (
            float(i_arr[~inbook_mask].mean())
            if (~inbook_mask).any() else None
        ),
        "spearman_i_move_vs_a1_minus": {
            "rho": float(sp_i_a1.statistic),
            "pvalue": float(sp_i_a1.pvalue),
        },
        "spearman_i_move_vs_n_legal": {
            "rho": float(sp_i_nl.statistic),
            "pvalue": float(sp_i_nl.pvalue),
        },
        "spearman_i_move_vs_a1_minus_in_book_only": (
            {
                "rho": float(sp_in_i_a1.statistic),
                "pvalue": float(sp_in_i_a1.pvalue),
            } if sp_in_i_a1 is not None else None
        ),
        "spearman_game_mean_i_vs_abs_disc_diff": {
            "rho": float(sp_mi_diff.statistic),
            "pvalue": float(sp_mi_diff.pvalue),
        },
        "per_game": per_game,
    }
    json_path = args.results_dir / "phase1c_shannon_info.json"
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    csv_path = args.results_dir / "phase1c_shannon_per_move.csv"
    fieldnames = list(per_ply[0].keys()) if per_ply else []
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in per_ply:
            writer.writerow(r)

    if not args.quiet:
        print(f"\n=== Shannon info summary ===")
        print(
            f"in-book fraction overall: "
            f"{100.0 * summary['in_book_fraction_overall']:.1f}%"
        )
        print(
            f"mean I_move (all):           "
            f"{summary['mean_i_move_bits']:.3f} bits "
            f"(+/- {summary['std_i_move_bits']:.3f})"
        )
        if summary["mean_i_move_bits_in_book_only"] is not None:
            print(
                f"mean I_move (in-book only):  "
                f"{summary['mean_i_move_bits_in_book_only']:.3f} bits"
            )
        if summary["mean_i_move_bits_out_of_book_only"] is not None:
            print(
                f"mean I_move (out-of-book):   "
                f"{summary['mean_i_move_bits_out_of_book_only']:.3f} bits"
            )
        r = summary["spearman_i_move_vs_a1_minus"]
        print(
            f"Spearman(I_move, A1- energy):   "
            f"rho={r['rho']:+.3f}, p={r['pvalue']:.2e}"
        )
        r = summary["spearman_i_move_vs_n_legal"]
        print(
            f"Spearman(I_move, n_legal):      "
            f"rho={r['rho']:+.3f}, p={r['pvalue']:.2e}"
        )
        r = summary["spearman_i_move_vs_a1_minus_in_book_only"]
        if r is not None:
            print(
                f"Spearman(I, A1-) in-book only:  "
                f"rho={r['rho']:+.3f}, p={r['pvalue']:.2e}"
            )
        r = summary["spearman_game_mean_i_vs_abs_disc_diff"]
        print(
            f"Spearman(game mean I, |disc_diff|): "
            f"rho={r['rho']:+.3f}, p={r['pvalue']:.2e}"
        )
        print(f"\nwrote {json_path}")
        print(f"wrote {csv_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Phase 1b game-trajectory tests — runs the corpus-dependent probes
from the Phase 1 hypothesis battery against a real PGN corpus.

Probes that upgrade from PARTIAL (random-play surrogate) or
scaffold to numeric-with-real-games:

  T1  Flip-count distribution per candidate move (vs random play)
  T2  <B1^2> / <B2^2> population asymmetry across trajectories
  T5  Flank cluster size distribution for *played* moves
  E3  Spearman(rho, A1- energy) scaled up from 300 positions
  E7  Disc-count monotone T-breaker across many games
  G9  Othello-side section 9h' peak/drop analysis (A1- energy
      trajectory, cross-game alignment of peak ply vs simplification)

NOT RUNNABLE IN THIS MODULE (blocked on external data or engine):
  - T3  Shannon info per move (needs opening_book_freq.csv)
  - T4  Trajectory in (T_eff, D_eff) plane (needs Blume-Capel
        parameter inference tooling)
  - H9  A1 depth-gap vs edax (needs compiled edax binary)
  - E8  Perfect-play correlations (needs Takizawa 20 GB table)

Outputs
-------
  results/phase1b_game_trajectories.json  : aggregate stats + per-
    game A1 peak/drop info
  results/phase1b_per_move.csv            : one row per replayed ply,
    suitable for downstream plotting
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

from othello_utils import BLACK, N, OthelloBoard, blume_capel_signal
from d4_z2 import D4_CHARS, D4_PERMS, project_irrep
from ray_laplacians import RAY_NAMES
from othello_pgn_loader import (
    _ensure_utf8_stdio, parse_pgn_file, replay,
)

_ensure_utf8_stdio()


# ---------------------------------------------------------------------------
# Per-position observables
# ---------------------------------------------------------------------------


def _d4_only_a1_energy(sig: np.ndarray) -> float:
    """||A1 projection of signal under D4 alone||^2.  Z2-even probe
    (used on occupation s^2)."""
    proj = np.zeros_like(sig, dtype=float)
    for g in range(8):
        proj = proj + D4_CHARS["A1"][g] * sig[D4_PERMS[g]]
    proj = proj / 8.0
    return float(np.linalg.norm(proj) ** 2)


def _b1_b2_energies(sig: np.ndarray) -> tuple[float, float]:
    """B1 and B2 energies: ||projection onto D4 irrep||^2.

    Using the D4 (not D4xZ2) projection for consistency with the
    chess B1/B2 reporting convention.
    """
    b1 = np.zeros_like(sig, dtype=float)
    b2 = np.zeros_like(sig, dtype=float)
    for g in range(8):
        b1 = b1 + D4_CHARS["B1"][g] * sig[D4_PERMS[g]]
        b2 = b2 + D4_CHARS["B2"][g] * sig[D4_PERMS[g]]
    b1 /= 8.0
    b2 /= 8.0
    return float(np.sum(b1 * b1)), float(np.sum(b2 * b2))


def _a1_minus_energy(sig: np.ndarray) -> float:
    return float(np.linalg.norm(project_irrep(sig, "A1-")) ** 2)


# ---------------------------------------------------------------------------
# Trajectory extraction
# ---------------------------------------------------------------------------


def trajectory_records(
    game_idx: int, game: dict
) -> tuple[list[dict], dict]:
    """Replay a single game; emit per-ply records and a per-game
    aggregate with A1- peak/drop statistics."""
    moves = game["moves"]
    bb_final, states, move_log = replay(moves)
    per_ply: list[dict] = []
    # states has length len(move_log) + 1 (initial + one per ply)
    a1m_trajectory: list[float] = []
    for ply, st in enumerate(states):
        sig = st.astype(float)
        a1m = _a1_minus_energy(sig)
        b1e, b2e = _b1_b2_energies(sig)
        d4_a1_occ = _d4_only_a1_energy(sig ** 2)
        b = int(np.sum(st == 1))
        w = int(np.sum(st == -1))
        e = int(np.sum(st == 0))
        bb_temp = OthelloBoard()
        bb_temp.state = st.copy()
        bb_temp.side_to_move = (
            BLACK if ply == 0 else
            (move_log[ply - 1]["side"] * -1)
        )
        # legal moves from this state for the side about to move
        legal_count = len(bb_temp.legal_moves())
        # candidate flip-count distribution at this state
        flip_counts = []
        for m in bb_temp.legal_moves():
            r, c = divmod(m, 8)
            flip_counts.append(
                len(bb_temp.flips_from(r, c, bb_temp.side_to_move))
            )
        rec = {
            "game": game_idx,
            "ply": ply,
            "black": b,
            "white": w,
            "empty": e,
            "rho": (b + w) / 64.0,
            "disc_diff": b - w,
            "a1_minus_energy": a1m,
            "b1_energy": b1e,
            "b2_energy": b2e,
            "d4_a1_occupation_energy": d4_a1_occ,
            "n_legal_moves": legal_count,
            "max_flip_count": max(flip_counts) if flip_counts else 0,
            "mean_flip_count": (
                float(np.mean(flip_counts)) if flip_counts else 0.0
            ),
        }
        per_ply.append(rec)
        a1m_trajectory.append(a1m)

    a1m_arr = np.array(a1m_trajectory)
    peak_ply = int(np.argmax(a1m_arr)) if a1m_arr.size else 0
    if a1m_arr.size > 1:
        da1 = np.diff(a1m_arr)
        drop_ply = int(np.argmin(da1)) + 1  # ply AFTER the drop
    else:
        drop_ply = 0
    n_plies = len(states)
    agg = {
        "game": game_idx,
        "event": game["headers"].get("Event", ""),
        "black": game["headers"].get("Black", ""),
        "white": game["headers"].get("White", ""),
        "result": game["headers"].get("FinalScore", ""),
        "n_plies": n_plies,
        "a1_minus_peak_ply": peak_ply,
        "a1_minus_peak_value": float(a1m_arr.max()) if a1m_arr.size else 0.0,
        "a1_minus_drop_ply": drop_ply,
        "a1_minus_final": float(a1m_arr[-1]) if a1m_arr.size else 0.0,
        "mean_b1_energy": float(
            np.mean([r["b1_energy"] for r in per_ply])
        ),
        "mean_b2_energy": float(
            np.mean([r["b2_energy"] for r in per_ply])
        ),
    }
    return per_ply, agg


# ---------------------------------------------------------------------------
# Corpus-level analyses
# ---------------------------------------------------------------------------


def analyse_flip_counts(per_ply: list[dict]) -> dict:
    """T1 analog with real moves.  Collect max_flip_count over every
    legal candidate (the richest per-position statistic we have)
    and report summary."""
    all_max = np.array([r["max_flip_count"] for r in per_ply])
    all_mean = np.array([r["mean_flip_count"] for r in per_ply])
    return {
        "n_positions": int(all_max.size),
        "max_flip_over_corpus": int(all_max.max()),
        "median_max_flip_per_position": float(np.median(all_max)),
        "mean_of_mean_flip": float(np.mean(all_mean)),
        "std_of_mean_flip": float(np.std(all_mean)),
    }


def analyse_b1_b2(per_ply: list[dict]) -> dict:
    """T2 analog: population asymmetry <B1^2> vs <B2^2>."""
    b1 = np.array([r["b1_energy"] for r in per_ply])
    b2 = np.array([r["b2_energy"] for r in per_ply])
    mean_b1 = float(np.mean(b1))
    mean_b2 = float(np.mean(b2))
    # Paired difference test: if strategy biases one orbit, mean
    # difference per position should be non-zero.
    diff = b1 - b2
    return {
        "n_positions": int(b1.size),
        "mean_B1_sq_energy": mean_b1,
        "mean_B2_sq_energy": mean_b2,
        "ratio_B1_over_B2": mean_b1 / mean_b2 if mean_b2 else float("nan"),
        "paired_diff_mean": float(np.mean(diff)),
        "paired_diff_std": float(np.std(diff)),
        "n_positions_B1_greater": int(np.sum(b1 > b2)),
        "n_positions_B2_greater": int(np.sum(b2 > b1)),
    }


def analyse_rho_a1(per_ply: list[dict]) -> dict:
    rho = np.array([r["rho"] for r in per_ply])
    a1m = np.array([r["a1_minus_energy"] for r in per_ply])
    d4a1_occ = np.array(
        [r["d4_a1_occupation_energy"] for r in per_ply]
    )
    sp_rho_a1 = spearmanr(rho, a1m)
    sp_rho_d4a1 = spearmanr(rho, d4a1_occ)
    return {
        "n_positions": int(rho.size),
        "spearman_rho_a1_minus": float(sp_rho_a1.statistic),
        "pvalue_rho_a1_minus": float(sp_rho_a1.pvalue),
        "spearman_rho_d4a1_occupation": float(sp_rho_d4a1.statistic),
        "pvalue_rho_d4a1_occupation": float(sp_rho_d4a1.pvalue),
    }


def analyse_t_breaking(per_game: list[dict], per_ply: list[dict]) -> dict:
    """E7 aggregate.  Compute forward gradient statistics across all
    games, treating each game as one trajectory.
    """
    fwd_pos_fracs = []
    for agg in per_game:
        gid = agg["game"]
        trajectory = [r for r in per_ply if r["game"] == gid]
        arr = np.array([r["a1_minus_energy"] for r in trajectory])
        if arr.size < 2:
            continue
        da1 = np.diff(arr)
        fwd_pos_fracs.append(float(np.sum(da1 > 0) / da1.size))
    fwd_pos_fracs_arr = np.array(fwd_pos_fracs)
    return {
        "n_games": int(fwd_pos_fracs_arr.size),
        "mean_forward_positive_fraction": float(
            np.mean(fwd_pos_fracs_arr)
        ),
        "std_forward_positive_fraction": float(
            np.std(fwd_pos_fracs_arr)
        ),
        "fraction_games_with_net_increase": float(
            np.mean(fwd_pos_fracs_arr > 0.5)
        ),
    }


def analyse_peak_drop(per_game: list[dict]) -> dict:
    peaks = np.array([g["a1_minus_peak_ply"] for g in per_game])
    drops = np.array([g["a1_minus_drop_ply"] for g in per_game])
    totals = np.array([g["n_plies"] for g in per_game])
    peak_rel = peaks / totals
    drop_rel = drops / totals
    # Pearson correlation between peak and drop ply over games
    if peaks.size > 1:
        peak_drop_corr = float(np.corrcoef(peaks, drops)[0, 1])
    else:
        peak_drop_corr = float("nan")
    return {
        "n_games": int(peaks.size),
        "mean_peak_ply": float(np.mean(peaks)),
        "mean_drop_ply": float(np.mean(drops)),
        "mean_peak_fraction_of_game": float(np.mean(peak_rel)),
        "mean_drop_fraction_of_game": float(np.mean(drop_rel)),
        "peak_drop_correlation": peak_drop_corr,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    default_input = (
        Path(__file__).resolve().parent.parent
        / "dataset" / "liveothello_Barcelona_EGP_2026.pgn"
    )
    default_results = (
        Path(__file__).resolve().parent.parent / "results"
    )
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  # Run the default corpus (Barcelona EGP 2026, 35 games) and emit
  # both aggregate JSON and per-move CSV to ../results/
  python research/game_trajectory_tests.py

  # Use a different corpus and custom output directory
  python research/game_trajectory_tests.py \\
      --input dataset/wthor_sample.pgn \\
      --results-dir /tmp/othello-run

  # Suppress the per-probe stdout summary; only write files
  python research/game_trajectory_tests.py --quiet

reading the output:
  The stdout summary is one short paragraph per probe (T1, T2, E3,
  E7, peak/drop).  The JSON file carries the full aggregate; the
  CSV carries one row per ply (game, ply, rho, A1- energy, B1
  energy, B2 energy, legal-move count, flip-count).  Use the CSV
  for plotting and the JSON for at-a-glance headlines.

what this does not do:
  T3 (Shannon info per move) needs the reversi-scripts opening-book
  frequency CSV.  T4 (T_eff/D_eff Blume-Capel trajectory) needs
  parameter-inference tooling.  H9 (A1 depth-gap vs edax) needs a
  compiled edax binary.  These are separate scripts, not added by
  this runner.
""",
    )
    parser.add_argument(
        "--input", type=Path, default=default_input,
        help="Othello PGN corpus.  Must follow the eOthello-style "
             "transcript format (see othello_pgn_loader.py --help).  "
             "Default is the Barcelona EGP 2026 file committed to "
             "this repo.",
    )
    parser.add_argument(
        "--results-dir", type=Path, default=default_results,
        help="Output directory for phase1b_game_trajectories.json "
             "and phase1b_per_move.csv (created if missing).  "
             "Default is ../results/ next to this script.",
    )
    parser.add_argument(
        "--quiet", action="store_true",
        help="Suppress the per-probe stdout summary.  Output files "
             "are still written.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    args.results_dir.mkdir(parents=True, exist_ok=True)

    print(f"loading corpus: {args.input}")
    games = parse_pgn_file(args.input)
    print(f"parsed {len(games)} games")

    per_ply_all: list[dict] = []
    per_game_all: list[dict] = []
    n_failed = 0
    for i, g in enumerate(games):
        try:
            per_ply, agg = trajectory_records(i, g)
        except Exception as exc:
            print(f"[game {i}] replay failed: {exc}", file=sys.stderr)
            n_failed += 1
            continue
        per_ply_all.extend(per_ply)
        per_game_all.append(agg)
    print(
        f"replayed {len(per_game_all)}/{len(games)} games "
        f"({n_failed} failures); "
        f"{len(per_ply_all)} position-records total"
    )

    t1 = analyse_flip_counts(per_ply_all)
    t2 = analyse_b1_b2(per_ply_all)
    e3 = analyse_rho_a1(per_ply_all)
    e7 = analyse_t_breaking(per_game_all, per_ply_all)
    pd = analyse_peak_drop(per_game_all)

    summary = {
        "corpus": str(args.input),
        "n_games": len(per_game_all),
        "n_positions": len(per_ply_all),
        "T1_flip_count": t1,
        "T2_b1_b2_population": t2,
        "E3_rho_a1_correlation": e3,
        "E7_forward_asymmetry": e7,
        "G9_peak_drop": pd,
        "per_game": per_game_all,
    }

    json_out = args.results_dir / "phase1b_game_trajectories.json"
    with json_out.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    csv_out = args.results_dir / "phase1b_per_move.csv"
    fieldnames = [
        "game", "ply", "black", "white", "empty", "rho", "disc_diff",
        "a1_minus_energy", "b1_energy", "b2_energy",
        "d4_a1_occupation_energy", "n_legal_moves",
        "max_flip_count", "mean_flip_count",
    ]
    with csv_out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for rec in per_ply_all:
            writer.writerow(rec)

    if not args.quiet:
        print()
        print("T1 flip-count:")
        print(
            f"  N={t1['n_positions']} positions, "
            f"max corpus-wide flip={t1['max_flip_over_corpus']}, "
            f"median per-position max flip="
            f"{t1['median_max_flip_per_position']:.1f}"
        )
        print("T2 B1 vs B2 population:")
        print(
            f"  mean <B1^2> = {t2['mean_B1_sq_energy']:.3f}, "
            f"mean <B2^2> = {t2['mean_B2_sq_energy']:.3f}, "
            f"ratio = {t2['ratio_B1_over_B2']:.3f}"
        )
        print(
            f"  paired diff mean = {t2['paired_diff_mean']:+.3f} "
            f"(+/- {t2['paired_diff_std']:.3f}); "
            f"B1>B2 in {t2['n_positions_B1_greater']}/"
            f"{t2['n_positions']}"
        )
        print("E3 rho vs A1- energy correlation:")
        print(
            f"  Spearman(rho, A1-) = "
            f"{e3['spearman_rho_a1_minus']:+.3f} "
            f"(p={e3['pvalue_rho_a1_minus']:.2e}), N="
            f"{e3['n_positions']}"
        )
        print("E7 forward-gradient asymmetry:")
        print(
            f"  mean fraction of positive forward increments = "
            f"{e7['mean_forward_positive_fraction']:.3f} "
            f"(+/- {e7['std_forward_positive_fraction']:.3f})"
        )
        print("G9 A1- peak / drop across games:")
        print(
            f"  mean peak ply = {pd['mean_peak_ply']:.1f} "
            f"({pd['mean_peak_fraction_of_game']*100:.1f}% of game); "
            f"mean drop ply = {pd['mean_drop_ply']:.1f} "
            f"({pd['mean_drop_fraction_of_game']*100:.1f}% of game); "
            f"corr(peak, drop) = {pd['peak_drop_correlation']:+.3f}"
        )
        print()
        print(f"wrote {json_out}")
        print(f"wrote {csv_out}")
    return 0 if n_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

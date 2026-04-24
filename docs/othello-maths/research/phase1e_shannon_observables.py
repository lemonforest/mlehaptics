"""Phase 1e.3 — T3 Shannon information per move with multiple spectral
observables.

Section 2c.2 reported Spearman(I_move, A1- magnetisation energy) =
+0.213, p = 2e-8 on the in-book subset of Barcelona EGP 2026
(~676 plies).  Section 2d flagged that the D4-only A1 projection of
s^2 (occupation) is a much cleaner ground-truth-aligned channel than
A1- magnetisation.  This runner asks whether the Shannon-info vs
spectral correlation strengthens when we swap the observable.

Two new observables computed for every ply:
  d4_a1_occupation_energy: D4-only A1 projection of s^2
  d4_e_occupation_energy:  D4-only E  projection of s^2

Imports computation pieces from shannon_info_runner rather than
duplicating them, so the original Phase 1c.2 result file is
untouched.

Outputs:
  results/phase1e_shannon_observables.json
  results/phase1e_shannon_per_move_observables.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

from othello_utils import N, OthelloBoard
from othello_pgn_loader import _ensure_utf8_stdio, parse_pgn_file, replay
from opening_book_loader import (
    OpeningBookFreq,
    enumerate_query_keys,
)
from d4_z2 import D4_CHARS, D4_PERMS, project_irrep
from shannon_info_runner import compute_i_move

_ensure_utf8_stdio()


def _d4_only_energy(sig: np.ndarray, irrep: str) -> float:
    proj = np.zeros_like(sig, dtype=float)
    for g in range(8):
        proj = proj + D4_CHARS[irrep][g] * sig[D4_PERMS[g]]
    d_mu = 2 if irrep == "E" else 1
    proj = proj * (d_mu / 8.0)
    return float(np.sum(proj * proj))


def _observables(state: np.ndarray) -> dict:
    sig = state.astype(float)
    occ = sig ** 2
    return {
        "a1_minus_energy":       float(np.linalg.norm(project_irrep(sig, "A1-")) ** 2),
        "e_minus_energy":        float(np.linalg.norm(project_irrep(sig, "E-")) ** 2),
        "d4_a1_occupation_energy": _d4_only_energy(occ, "A1"),
        "d4_a2_occupation_energy": _d4_only_energy(occ, "A2"),
        "d4_b1_occupation_energy": _d4_only_energy(occ, "B1"),
        "d4_b2_occupation_energy": _d4_only_energy(occ, "B2"),
        "d4_e_occupation_energy":  _d4_only_energy(occ, "E"),
    }


def run_corpus(pgn_path: Path, book: OpeningBookFreq, laplace: float):
    games = parse_pgn_file(pgn_path)
    per_ply: list[dict] = []
    for gi, g in enumerate(games):
        try:
            bb_final, states, move_log = replay(g["moves"])
        except Exception as exc:
            print(f"game {gi} replay failed: {exc}", file=sys.stderr)
            continue
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
            obs = _observables(st)
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
                **obs,
            }
            per_ply.append(rec)
    return per_ply


def _all_correlations(
    per_ply: list[dict], obs_keys: list[str]
) -> dict:
    i_arr = np.array([r["i_move_bits"] for r in per_ply])
    inbook = np.array([bool(r["in_book"]) for r in per_ply])
    nl = np.array([r["n_legal"] for r in per_ply])
    out: dict[str, dict] = {}
    # Control (should be near +0.77-0.81 per §2c.2)
    sp = spearmanr(i_arr, nl)
    out["_control_i_vs_n_legal"] = {
        "rho": float(sp.statistic), "p": float(sp.pvalue),
        "n": int(i_arr.size),
    }
    for obs in obs_keys:
        x = np.array([r[obs] for r in per_ply])
        # All plies
        sp = spearmanr(i_arr, x)
        out[f"i_vs_{obs}__all"] = {
            "rho": float(sp.statistic), "p": float(sp.pvalue),
            "n": int(i_arr.size),
        }
        # In-book only
        if inbook.sum() > 2:
            sp_in = spearmanr(i_arr[inbook], x[inbook])
            out[f"i_vs_{obs}__in_book"] = {
                "rho": float(sp_in.statistic), "p": float(sp_in.pvalue),
                "n": int(inbook.sum()),
            }
        # Out-of-book only
        if (~inbook).sum() > 2:
            sp_oo = spearmanr(i_arr[~inbook], x[~inbook])
            out[f"i_vs_{obs}__out_of_book"] = {
                "rho": float(sp_oo.statistic), "p": float(sp_oo.pvalue),
                "n": int((~inbook).sum()),
            }
    return out


def _build_parser():
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
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  # Default: Barcelona EGP 2026, opening_book_freq.csv.bz2, alpha=1.
  python research/phase1e_shannon_observables.py

  # Different smoothing.
  python research/phase1e_shannon_observables.py --laplace 0.5

  # Custom PGN corpus (e.g. APR 2026).
  python research/phase1e_shannon_observables.py \\
      --pgn ../dataset/liveothello-2026-APR.pgn

reading the output:
  The headline columns are the per-observable in-book Spearmans.
  §2c.2 reported rho(I_move, a1_minus) in-book = +0.213 at ~676
  plies.  The 1e.3 finding was that d4_a1_occupation_energy jumps
  to ~+0.465 on the same subset.  Phase 1e.6
  (phase1e_signflip_decomposition.py) further shows that this
  aggregate is partly a Simpson's paradox of game-phase structure.
  For clean within-phase analyses, see the 1e.6 decomposition.
""",
    )
    p.add_argument(
        "--pgn", type=Path, default=default_pgn,
        help="PGN corpus path.  Default: Barcelona EGP 2026.",
    )
    p.add_argument(
        "--book", type=Path, default=default_book,
        help="Path to opening_book_freq.csv.bz2 (WTHOR empirical "
             "frequencies).",
    )
    p.add_argument(
        "--laplace", type=float, default=1.0,
        help="Laplace alpha for smoothing book frequencies.  "
             "Default: 1.0.",
    )
    p.add_argument(
        "--results-dir", type=Path, default=default_results,
        help="Output directory for phase1e_shannon_observables.json "
             "and per-move CSV.  Default: ../results/.",
    )
    return p


def main(argv=None):
    args = _build_parser().parse_args(argv)
    args.results_dir.mkdir(parents=True, exist_ok=True)

    print(f"corpus: {args.pgn}")
    print(f"book:   {args.book}")

    keys, _ = enumerate_query_keys(args.pgn)
    print(f"query-set canonical keys: {len(keys)}")
    print("loading book (this can take ~60 s)...")
    book = OpeningBookFreq.load(args.book, query_set=keys)
    print(
        f"book: scanned {book.n_rows_scanned}, kept {book.n_rows_kept} "
        f"(unique {len(book._index)})"
    )

    per_ply = run_corpus(args.pgn, book, args.laplace)
    print(f"scored {len(per_ply)} plies")

    obs_keys = [
        "a1_minus_energy",
        "e_minus_energy",
        "d4_a1_occupation_energy",
        "d4_a2_occupation_energy",
        "d4_b1_occupation_energy",
        "d4_b2_occupation_energy",
        "d4_e_occupation_energy",
    ]
    correlations = _all_correlations(per_ply, obs_keys)

    summary = {
        "corpus": str(args.pgn),
        "book": str(args.book),
        "laplace": args.laplace,
        "n_plies_scored": len(per_ply),
        "correlations": correlations,
    }

    json_path = args.results_dir / "phase1e_shannon_observables.json"
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    csv_path = args.results_dir / "phase1e_shannon_per_move_observables.csv"
    if per_ply:
        fieldnames = list(per_ply[0].keys())
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in per_ply:
                writer.writerow(r)

    # Stdout highlights
    print(f"\n=== Phase 1e.3 Shannon-info correlation headlines (N = {len(per_ply)}) ===")
    print(f"  {'obs':28s}  {'all rho':>10s}  {'in-book rho':>14s}  {'out rho':>10s}")
    for obs in obs_keys:
        a = correlations.get(f"i_vs_{obs}__all", {}).get("rho", float("nan"))
        b = correlations.get(f"i_vs_{obs}__in_book", {}).get("rho", float("nan"))
        c = correlations.get(f"i_vs_{obs}__out_of_book", {}).get("rho", float("nan"))
        print(f"  {obs:28s}  {a:+10.3f}  {b:+14.3f}  {c:+10.3f}")
    ctl = correlations["_control_i_vs_n_legal"]
    print(f"\n  control i_vs_n_legal rho = {ctl['rho']:+.3f} (expected near +0.81)")
    print(f"\nwrote {json_path}")
    print(f"wrote {csv_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

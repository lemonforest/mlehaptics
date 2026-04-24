"""Open item 2 — §10.10 T4 effective thermodynamic trajectory.

§10.10 T4 wants a (T_eff, D_eff) trajectory for each game - effective
temperature and effective density derived from the spectral signal at
each ply.  The motivating idea is a Sagawa-Ueda-style thermodynamic
reading of D4xZ2 Othello play under the Blume-Capel analog (§10.3).

Derivation (concrete choice for v0)
-----------------------------------

For each board state, the encoder emits a 768-dim vector decomposed
into 12 channel energies E_c (c = 0..11).  Normalised,

    p_c = E_c / sum_c E_c

is a discrete probability distribution over channels.  We define:

    D_eff(t) = rho(t) = disc_count(t) / 64
              (the Blume-Capel filling density; slow global variable
               per §10.8)

    S_eff(t) = -sum_c p_c * log(p_c)
              (Shannon entropy of channel-energy distribution;
               "spectral entropy" per §10.3 reading)

    E_tot(t) = sum_c E_c
              (total spectral norm)

    T_eff(t) = dE_tot / dS_eff along the trajectory
              (approximated by finite differences between
               consecutive plies)

In a critical FK-BC regime we'd expect T_eff to cluster near a
non-trivial fixed point; in a sub-critical regime it should scale
with the average flip activity.

Inputs
------

The runner consumes a .spectralz binary (encoded via
othello_spectral.cli encode-pgn) and emits the per-ply (D_eff,
S_eff, T_eff) trajectory plus aggregate statistics (mean/std of
T_eff over the corpus, correlation of T_eff with game outcome).

Outputs
-------
  results/phase1e_t4_thermodynamic_<corpus>.json
"""

from __future__ import annotations

__version__ = "0.2.0"

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

from othello_spectral import CHANNEL_NAMES, ENCODING_DIM, encode_768
from othello_spectral.encoder import channel_energies
from othello_spectral.frame import read_file
from othello_pgn_loader import (
    _ensure_utf8_stdio, parse_pgn_file, replay,
)

_ensure_utf8_stdio()


def per_ply_thermodynamics(enc: np.ndarray) -> dict:
    """Compute (D_eff, S_eff, E_tot) for a single 768-dim encoding."""
    enc64 = np.asarray(enc, dtype=np.float64)
    energies = channel_energies(enc64)
    e_vec = np.array(
        [energies[name] for name in CHANNEL_NAMES], dtype=np.float64,
    )
    e_tot = float(e_vec.sum())
    # Occupation channels (5..9 in CHANNEL_NAMES) sum to ||occ||^2 =
    # disc_count; use that as D_eff.
    occ_total = float(e_vec[5:10].sum())
    D_eff = occ_total / 64.0

    if e_tot > 0:
        p = e_vec / e_tot
        mask = p > 1e-15
        S_eff = float(-np.sum(p[mask] * np.log(p[mask])))
    else:
        S_eff = 0.0

    return {
        "E_tot": e_tot,
        "D_eff": D_eff,
        "S_eff": S_eff,
    }


def analyze_trajectory(
    enc_frames: list[np.ndarray], plies: list[int],
) -> list[dict]:
    """Walk a trajectory, compute per-ply (D_eff, S_eff, E_tot) and
    finite-difference T_eff."""
    out: list[dict] = []
    prev = None
    for i, (enc, ply) in enumerate(zip(enc_frames, plies)):
        therm = per_ply_thermodynamics(enc)
        t_eff = None
        if prev is not None:
            dE = therm["E_tot"] - prev["E_tot"]
            dS = therm["S_eff"] - prev["S_eff"]
            if abs(dS) > 1e-9:
                t_eff = dE / dS
        row = {
            "ply": int(ply),
            "E_tot":  therm["E_tot"],
            "D_eff":  therm["D_eff"],
            "S_eff":  therm["S_eff"],
            "T_eff":  t_eff,
        }
        out.append(row)
        prev = therm
    return out


def aggregate_pgn(pgn_path: Path, out_json: Path) -> dict:
    """Walk a PGN corpus, encode each position on the fly, compute
    per-game thermodynamic trajectory.  Replacing the earlier
    .spectralz-based driver because encode-pgn emits a monotone
    global ply counter (no game boundaries), which corrupts the
    finite-difference T_eff at game transitions."""
    games = parse_pgn_file(pgn_path)
    print(f"pgn: {pgn_path.name}  ({len(games)} games)")

    all_rows: list[dict] = []
    all_T_eff: list[float] = []
    per_game_stats: list[dict] = []
    n_ok = 0
    for gi, g in enumerate(games):
        try:
            _, states, _ = replay(g["moves"])
        except Exception:
            continue
        n_ok += 1
        encs = [encode_768(st) for st in states]
        plies = list(range(len(states)))
        rows = analyze_trajectory(encs, plies)
        for r in rows:
            r["game"] = gi
        all_rows.extend(rows)
        t_values = [
            r["T_eff"] for r in rows if r["T_eff"] is not None
        ]
        if t_values:
            all_T_eff.extend(t_values)
            per_game_stats.append({
                "game": gi,
                "headers": {
                    "black": g["headers"].get("Black", ""),
                    "white": g["headers"].get("White", ""),
                    "final_score": g["headers"].get("FinalScore", ""),
                },
                "n_plies": len(rows),
                "T_eff_mean":   float(np.mean(t_values)),
                "T_eff_median": float(np.median(t_values)),
                "T_eff_std":    float(np.std(t_values)),
                "D_eff_range": [
                    rows[0]["D_eff"], rows[-1]["D_eff"],
                ],
                "S_eff_range": [
                    float(min(r["S_eff"] for r in rows)),
                    float(max(r["S_eff"] for r in rows)),
                ],
            })

    summary = {
        "pgn": str(pgn_path),
        "n_games_replayed": n_ok,
        "n_games_with_T_eff": len(per_game_stats),
        "n_plies_total": len(all_rows),
        "T_eff_corpus": {
            "mean":  float(np.mean(all_T_eff)) if all_T_eff else None,
            "std":   float(np.std(all_T_eff))  if all_T_eff else None,
            "median": float(np.median(all_T_eff)) if all_T_eff else None,
        },
        "per_game": per_game_stats,
    }
    out_json.parent.mkdir(parents=True, exist_ok=True)
    with out_json.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"\n=== Open-2 T4 thermodynamic trajectory ===")
    print(f"  corpus: {pgn_path.name}")
    print(f"  games replayed: {summary['n_games_replayed']}")
    print(f"  games with T_eff: {summary['n_games_with_T_eff']}")
    print(f"  total plies:    {summary['n_plies_total']}")
    t = summary["T_eff_corpus"]
    if t["mean"] is not None:
        print(
            f"  T_eff corpus-wide: mean {t['mean']:+.4f}  "
            f"median {t['median']:+.4f}  std {t['std']:.4f}"
        )
    print(f"\nwrote {out_json}")
    return summary


def _build_parser():
    default_results = (
        Path(__file__).resolve().parent.parent / "results"
    )
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  # Default: Barcelona PGN (35 games, a few seconds).
  python research/phase1e_t4_thermodynamic_trajectory.py

  # Historical corpus:
  python research/phase1e_t4_thermodynamic_trajectory.py \\
      --pgn ../dataset/liveothello_World_Championships_2005.pgn

reading the output:
  'T_eff_corpus' reports aggregate temperature across games.
  Per-game 'T_eff_mean' shows whether individual trajectories
  cluster at similar temperature (critical-regime expectation)
  or span a wide range (subcritical / play-style heterogeneity).
  Decisive / blowout games should have systematically higher
  |T_eff| than balanced games.

note:
  Using the PGN path rather than the .spectralz encoded form,
  because encode-pgn flattens the global ply counter without
  per-game resets, which would corrupt finite-difference T_eff
  at each game boundary.  A future encoder revision may add a
  game-index column to .spectralz; until then, we replay.
""",
    )
    research_dir = Path(__file__).resolve().parent
    default_pgn = (
        research_dir.parent / "dataset"
        / "liveothello_Barcelona_EGP_2026.pgn"
    )
    p.add_argument(
        "--pgn", type=Path, default=default_pgn,
        help="Input PGN corpus.  Default: Barcelona 35-game.",
    )
    p.add_argument(
        "--out", type=Path, default=None,
        help="Output JSON path.  Default: "
             "results/phase1e_t4_thermodynamic_<corpus>.json",
    )
    return p


def main(argv=None):
    args = _build_parser().parse_args(argv)
    if not args.pgn.exists():
        print(f"pgn not found: {args.pgn}", file=sys.stderr)
        return 2
    out = args.out
    if out is None:
        tag = args.pgn.stem
        out = (
            Path(__file__).resolve().parent.parent / "results"
            / f"phase1e_t4_thermodynamic_{tag}.json"
        )
    aggregate_pgn(args.pgn, out)
    return 0


if __name__ == "__main__":
    sys.exit(main())

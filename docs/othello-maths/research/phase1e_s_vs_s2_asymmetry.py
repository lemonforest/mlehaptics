"""Sequel item 2 — the s-vs-s² asymmetry in trajectory-memory gain.

§1e.7.4b showed that the faithful sheaf's `gain_vs_snap` is
positive for targets derived from the occupation signal s²
(d4_e_occ, d4_a1_occ, rho) but negative for targets derived
from the magnetisation signal s (a1_minus_energy).

Exp 2 (phase1e_z2_conditional_gain.py) rejected the Z₂-colour-
polarity-cancellation hypothesis.  This runner tests three
structural properties of each target to localise the mechanism:

  H-A (ply-to-ply volatility):
    Z₂-even targets may evolve smoothly ply-to-ply (disc count
    grows monotonically, occupation geometry shifts gradually).
    Z₂-odd-derived targets may oscillate (magnetisation can
    shift sharply on flanking events).  Measure: per-game median
    absolute ply-to-ply difference normalised by target std.

  H-B (autocorrelation):
    Smoothly-evolving targets have high autocorrelation at short
    lags (Δ=1).  Oscillating targets have low or negative
    autocorr.  Measure: per-game Pearson(target(t), target(t+1))
    aggregated to a corpus median.

  H-C (monotonicity / disc-count coupling):
    Targets that correlate tightly with disc count are determined
    by the "game clock" — predictable by anything that knows the
    game clock.  Measure: per-game Pearson(target, disc_count).
    A target with Pearson ≈ 1.0 is essentially monotone.

Corpus: 2025 (2178 games).  The same corpus §1e.7.4b ran on.
Target set matches: a1_minus_energy, d4_a1_occupation,
d4_e_occupation, rho, empty_count, n_legal_moves.

If Z₂-even targets score high on all three metrics and A1⁻
scores low, the asymmetry is structural (target evolves
predictably) rather than representation-theoretic.  That closes
the mechanism question raised in §2e.4.
"""

from __future__ import annotations

__version__ = "0.3.0"

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import pearsonr

from d4_z2 import D4_CHARS, D4_PERMS, project_irrep
from othello_pgn_loader import (
    _ensure_utf8_stdio, parse_pgn_file, replay,
)
from othello_utils import BLACK, N

_ensure_utf8_stdio()


def _d4_only_energy(sig: np.ndarray, irrep: str) -> float:
    proj = np.zeros_like(sig, dtype=float)
    for g in range(8):
        proj = proj + D4_CHARS[irrep][g] * sig[D4_PERMS[g]]
    d_mu = 2 if irrep == "E" else 1
    proj = proj * (d_mu / 8.0)
    return float(np.sum(proj * proj))


def _targets(state: np.ndarray) -> dict:
    sig = state.astype(float)
    occ = sig ** 2
    b = int(np.sum(state == BLACK))
    w = int(np.sum(state == -BLACK))
    e = int(np.sum(state == 0))
    return {
        "a1_minus_energy":
            float(np.linalg.norm(project_irrep(sig, "A1-")) ** 2),
        "d4_a1_occupation_energy": _d4_only_energy(occ, "A1"),
        "d4_e_occupation_energy":  _d4_only_energy(occ, "E"),
        "rho": (b + w) / 64.0,
        "empty_count": e,
        "disc_count":  b + w,
    }


def analyse_game(states: list[np.ndarray]) -> dict:
    targets = [_targets(st) for st in states]
    if len(targets) < 10:
        return {"n_plies": len(targets), "skipped": True}
    keys = [
        "a1_minus_energy", "d4_a1_occupation_energy",
        "d4_e_occupation_energy", "rho", "empty_count",
    ]
    disc_count = np.array([t["disc_count"] for t in targets])
    stats: dict = {}
    for k in keys:
        y = np.array([t[k] for t in targets])
        if y.std() < 1e-9:
            stats[k] = None
            continue
        # H-A: ply-to-ply volatility (normalised)
        diffs = np.abs(np.diff(y))
        volatility = float(np.median(diffs) / (y.std() + 1e-30))
        # H-B: lag-1 autocorrelation
        autocorr = float(np.corrcoef(y[:-1], y[1:])[0, 1])
        # H-C: correlation with disc count
        if disc_count.std() > 0:
            r_disc = float(pearsonr(y, disc_count).statistic)
        else:
            r_disc = float("nan")
        # Monotonic fraction (fraction of positive or consistent-sign diffs)
        signs = np.sign(np.diff(y))
        non_zero = signs[signs != 0]
        if non_zero.size > 0:
            monotone_frac = float(
                max(
                    np.mean(non_zero > 0),
                    np.mean(non_zero < 0),
                )
            )
        else:
            monotone_frac = float("nan")
        stats[k] = {
            "volatility": volatility,
            "autocorr_lag1": autocorr,
            "disc_count_pearson": r_disc,
            "monotone_fraction": monotone_frac,
        }
    return {"n_plies": len(targets), "per_target": stats}


def analyse_corpus(pgn_path: Path) -> dict:
    games = parse_pgn_file(pgn_path)
    keys = [
        "a1_minus_energy", "d4_a1_occupation_energy",
        "d4_e_occupation_energy", "rho", "empty_count",
    ]
    collected: dict[str, dict[str, list[float]]] = {
        k: {
            "volatility": [], "autocorr_lag1": [],
            "disc_count_pearson": [], "monotone_fraction": [],
        } for k in keys
    }
    n_games_ok = 0
    for gi, g in enumerate(games):
        try:
            _, states, _ = replay(g["moves"])
        except Exception:
            continue
        s = analyse_game(states)
        if s.get("skipped"):
            continue
        n_games_ok += 1
        for k in keys:
            v = s["per_target"].get(k)
            if v is None:
                continue
            for metric, val in v.items():
                if val is not None and not (
                    isinstance(val, float) and np.isnan(val)
                ):
                    collected[k][metric].append(val)
        if (gi + 1) % 200 == 0:
            print(f"  processed {gi + 1}/{len(games)}", flush=True)

    summary: dict = {
        "pgn": str(pgn_path),
        "n_games_replayed": n_games_ok,
        "per_target": {},
    }
    for k in keys:
        per_metric = {}
        for m, vals in collected[k].items():
            arr = np.array(vals)
            if arr.size == 0:
                continue
            per_metric[m] = {
                "mean":   float(arr.mean()),
                "median": float(np.median(arr)),
                "std":    float(arr.std()),
                "q25":    float(np.percentile(arr, 25)),
                "q75":    float(np.percentile(arr, 75)),
                "n_games": int(arr.size),
            }
        summary["per_target"][k] = per_metric
    return summary


def _build_parser():
    research_dir = Path(__file__).resolve().parent
    default_pgn = (
        research_dir.parent / "dataset"
        / "liveothello_2025_all.pgn"
    )
    default_out = (
        research_dir.parent / "results"
        / "phase1e_s_vs_s2_asymmetry.json"
    )
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  # Default: 2025 2178-game corpus.  Walltime ~20 min.
  python research/phase1e_s_vs_s2_asymmetry.py

  # Smoke test on Barcelona.
  python research/phase1e_s_vs_s2_asymmetry.py \\
      --pgn ../dataset/liveothello_Barcelona_EGP_2026.pgn

reading the output:
  H-A / H-B / H-C predictions:
    d4_e_occ, d4_a1_occ, rho should show LOW volatility, HIGH
    autocorr, HIGH disc_count Pearson, HIGH monotone_fraction.
    a1_minus_energy should show HIGH volatility, LOW autocorr,
    LOW or variable disc_count Pearson, ~0.5 monotone_fraction.
  If that pattern holds, the trajectory-memory asymmetry from
  §1e.7.4b is explained by "Z2-even targets evolve predictably
  with the game clock" — a structural / kinematic reason, not a
  representation-theoretic one.
""",
    )
    p.add_argument("--pgn", type=Path, default=default_pgn)
    p.add_argument("--out", type=Path, default=default_out)
    return p


def main(argv=None):
    args = _build_parser().parse_args(argv)
    if not args.pgn.exists():
        print(f"PGN not found: {args.pgn}", file=sys.stderr)
        return 2
    s = analyse_corpus(args.pgn)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as f:
        json.dump(s, f, indent=2)

    # Stdout comparison table
    print(f"\n=== s-vs-s^2 asymmetry diagnostics (N={s['n_games_replayed']}) ===")
    header = f"{'target':28s}  {'volatility':>11s}  {'autocorr1':>10s}  {'r_disc':>7s}  {'mono_frac':>10s}"
    print(header)
    for tk, m in s["per_target"].items():
        if not m:
            continue
        print(
            f"{tk:28s}  {m['volatility']['median']:+11.4f}  "
            f"{m['autocorr_lag1']['median']:+10.4f}  "
            f"{m['disc_count_pearson']['median']:+7.3f}  "
            f"{m['monotone_fraction']['median']:+10.3f}"
        )
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

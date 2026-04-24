"""Phase 1e.5 — L7b-style predictive validation of the sheaf spectrum.

§2c of the logo notebook (L7b experiments) established that a
snapshot fiber does not necessarily predict forward in time.  This
runner applies the same test to the Othello sheaf Laplacian §3 of
the notebook.

Methodology (L7b.5 analog)
--------------------------
1. Generate M = 30 random-play trajectories (seeds 100..129) from the
   starting position to terminal.
2. At each ply t, compute sheaf spectral summaries (lambda_2,
   entropy, kernel_dim) for both player perspectives, plus the state
   summary variables (n_legal_moves(t), rho(t), disc_diff(t)).
3. For each shift Delta in {1, 3, 5, 10}, form pairs (features(t),
   target(t+Delta)) across all (trajectory, t).  Three baselines:

     a) Predictive:  rho(sheaf_t, target_{t+Delta})
     b) Snapshot:    rho(sheaf_{t+Delta}, target_{t+Delta})
                      -- correlation if we just looked at current time
     c) Persistence: rho(target_t, target_{t+Delta})
                      -- correlation of target with itself through time

   "The sheaf predicts forward" requires (a) to be a noticeable
   fraction of (b) and not dominated by (c).

4. L7b.5-style fiber test: fit linear model
   target_{t+Delta} ~ features(t), compare R^2 against target_t
   baseline.  Gain = R^2(features) - R^2(snapshot).

Expected outcome (under L7b template): gain near zero or negative.
We want to know.

Outputs
-------
  results/phase1e_predictive_sheaf.json
  results/phase1e_predictive_sheaf_pairs.csv   (per-pair data)
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

from dynamic_sheaf import sample_game_trajectory


TARGETS = ["n_legal_moves", "rho", "empty_count"]
SHEAF_FEATURES = [
    "sheaf_black_lambda2", "sheaf_white_lambda2",
    "sheaf_black_entropy", "sheaf_white_entropy",
    "sheaf_black_kerdim",  "sheaf_white_kerdim",
    "sheaf_black_lambdamax", "sheaf_white_lambdamax",
]


def _load_or_generate_trajectories(
    seeds: list[int], cache_dir: Path
) -> list[list[dict]]:
    """For each seed, generate (or load from cache) a full random
    trajectory.  Caching per-seed so reruns are fast."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    out = []
    for seed in seeds:
        cache_path = cache_dir / f"sheaf_traj_seed{seed:03d}.json"
        if cache_path.exists():
            with cache_path.open("r", encoding="utf-8") as f:
                traj = json.load(f)
            print(f"  cached: seed {seed} ({len(traj)} moves)")
        else:
            t0 = time.time()
            traj = sample_game_trajectory(seed=seed)
            elapsed = time.time() - t0
            print(f"  generated: seed {seed} ({len(traj)} moves, {elapsed:.1f}s)")
            with cache_path.open("w", encoding="utf-8") as f:
                json.dump(traj, f, indent=2)
        out.append(traj)
    return out


def _build_pairs(
    trajectories: list[list[dict]], delta: int
) -> list[dict]:
    """For each trajectory, yield pairs (features_t, target_{t+Delta})
    for all valid t.  Returns a flat list of dicts ready for pandas-
    free correlation analysis."""
    pairs = []
    for gi, traj in enumerate(trajectories):
        for t in range(len(traj) - delta):
            early = traj[t]
            late = traj[t + delta]
            row = {
                "game": gi,
                "t": t,
                "delta": delta,
                "late_t": t + delta,
                # Sheaf features at t
                **{f"early__{k}": early[k] for k in SHEAF_FEATURES},
                # Persistence baselines: target at t
                **{f"early__{k}": early[k] for k in TARGETS},
                # Snapshot baselines: sheaf features at t+Delta
                **{f"late__{k}": late[k] for k in SHEAF_FEATURES},
                # Prediction targets
                **{f"late__{k}": late[k] for k in TARGETS},
            }
            pairs.append(row)
    return pairs


def _ols_r2(Y: np.ndarray, X: np.ndarray) -> float:
    X1 = np.concatenate([X, np.ones((len(Y), 1))], axis=1)
    beta, *_ = np.linalg.lstsq(X1, Y, rcond=None)
    resid = Y - X1 @ beta
    ss_res = float(np.sum(resid ** 2))
    ss_tot = float(np.sum((Y - Y.mean()) ** 2))
    return 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0


def _analyze_pairs(pairs: list[dict], delta: int) -> dict:
    """Compute predictive vs snapshot vs persistence Spearmans + OLS
    gain for each (sheaf_feature, target) pair."""
    n = len(pairs)
    if n < 10:
        return {"n_pairs": n, "skipped": True}
    sheaf_early = {
        k: np.array([p[f"early__{k}"] for p in pairs])
        for k in SHEAF_FEATURES
    }
    sheaf_late = {
        k: np.array([p[f"late__{k}"] for p in pairs])
        for k in SHEAF_FEATURES
    }
    target_early = {
        k: np.array([p[f"early__{k}"] for p in pairs])
        for k in TARGETS
    }
    target_late = {
        k: np.array([p[f"late__{k}"] for p in pairs])
        for k in TARGETS
    }
    univariate: dict[str, dict] = {}
    for tk in TARGETS:
        y = target_late[tk]
        # Persistence baseline
        sp_pers = spearmanr(target_early[tk], y)
        univariate[f"persistence__{tk}"] = {
            "rho": float(sp_pers.statistic),
            "p": float(sp_pers.pvalue),
            "n": n,
        }
        for fk in SHEAF_FEATURES:
            # Predictive: sheaf at t -> target at t+delta
            sp_pred = spearmanr(sheaf_early[fk], y)
            # Snapshot: sheaf at t+delta -> target at t+delta
            sp_snap = spearmanr(sheaf_late[fk], y)
            univariate[f"predictive__{fk}__{tk}"] = {
                "rho": float(sp_pred.statistic),
                "p": float(sp_pred.pvalue),
                "n": n,
            }
            univariate[f"snapshot__{fk}__{tk}"] = {
                "rho": float(sp_snap.statistic),
                "p": float(sp_snap.pvalue),
                "n": n,
            }

    # Multivariate (L7b.5 analog) - all sheaf features at t -> target at t+delta
    gains: dict[str, dict] = {}
    X_early = np.stack(
        [sheaf_early[k] for k in SHEAF_FEATURES], axis=1
    )
    X_late = np.stack(
        [sheaf_late[k] for k in SHEAF_FEATURES], axis=1
    )
    for tk in TARGETS:
        y = target_late[tk]
        r2_pred = _ols_r2(y, X_early)
        r2_snap = _ols_r2(y, X_late)
        # Persistence-only baseline as a single-variate OLS
        r2_pers = _ols_r2(y, target_early[tk].reshape(-1, 1))
        # Predictive gain: R^2(features at t) - R^2(persistence)
        gains[tk] = {
            "r2_predictive_full_sheaf_at_t": r2_pred,
            "r2_snapshot_full_sheaf_at_t_plus_delta": r2_snap,
            "r2_persistence_target_at_t": r2_pers,
            "predictive_gain_vs_persistence": r2_pred - r2_pers,
            "predictive_gain_vs_snapshot": r2_pred - r2_snap,
            "n": n,
        }

    return {
        "n_pairs": n,
        "univariate": univariate,
        "multivariate_r2": gains,
    }


def run(
    out_json: Path, out_csv: Path, cache_dir: Path,
    n_seeds: int, deltas: list[int],
) -> dict:
    seeds = list(range(100, 100 + n_seeds))
    print(f"generating {n_seeds} trajectories (seeds {seeds[0]}..{seeds[-1]})")
    t0 = time.time()
    trajs = _load_or_generate_trajectories(seeds, cache_dir)
    print(f"generated/loaded {len(trajs)} trajectories in {time.time()-t0:.1f}s")
    lengths = [len(t) for t in trajs]
    print(f"trajectory lengths: min {min(lengths)}, max {max(lengths)}, mean {np.mean(lengths):.1f}")

    summary: dict = {
        "n_seeds": n_seeds,
        "deltas": deltas,
        "trajectory_lengths": lengths,
        "sheaf_features": SHEAF_FEATURES,
        "targets": TARGETS,
    }
    all_pairs: list[dict] = []
    per_delta: dict[str, dict] = {}
    for delta in deltas:
        pairs = _build_pairs(trajs, delta)
        analysis = _analyze_pairs(pairs, delta)
        per_delta[f"delta_{delta}"] = analysis
        for p in pairs:
            all_pairs.append(p)
        print(
            f"delta={delta}: {len(pairs)} pairs; "
            f"predictive gain vs persistence (n_legal): "
            f"{analysis.get('multivariate_r2', {}).get('n_legal_moves', {}).get('predictive_gain_vs_persistence', float('nan')):+.4f}"
        )
    summary["per_delta"] = per_delta

    out_json.parent.mkdir(parents=True, exist_ok=True)
    with out_json.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    if all_pairs:
        fieldnames = list(all_pairs[0].keys())
        with out_csv.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in all_pairs:
                writer.writerow(row)

    # Stdout highlights (L7b-style verdict)
    print("\n=== Phase 1e.5 predictive-sheaf verdict ===")
    for delta in deltas:
        a = per_delta[f"delta_{delta}"].get("multivariate_r2", {})
        print(f"\n  delta = {delta}")
        for tk in TARGETS:
            g = a.get(tk, {})
            print(
                f"    target={tk:16s}  "
                f"R2_pred={g.get('r2_predictive_full_sheaf_at_t', float('nan')):+.4f}  "
                f"R2_snap={g.get('r2_snapshot_full_sheaf_at_t_plus_delta', float('nan')):+.4f}  "
                f"R2_pers={g.get('r2_persistence_target_at_t', float('nan')):+.4f}  "
                f"gain_vs_pers={g.get('predictive_gain_vs_persistence', float('nan')):+.4f}"
            )
    print(f"\nwrote {out_json}")
    if all_pairs:
        print(f"wrote {out_csv}")
    return summary


def _build_parser():
    default_out_json = (
        Path(__file__).resolve().parent.parent / "results"
        / "phase1e_predictive_sheaf.json"
    )
    default_out_csv = (
        Path(__file__).resolve().parent.parent / "results"
        / "phase1e_predictive_sheaf_pairs.csv"
    )
    default_cache = (
        Path(__file__).resolve().parent.parent / "results"
        / "phase1e_sheaf_cache"
    )
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  # Default: 30 random-play trajectories (seeds 100..129), deltas
  # 1,3,5,10.  Walltime ~1.5 min on a laptop.
  python research/phase2_predictive_sheaf.py

  # More seeds for tighter variance estimate.
  python research/phase2_predictive_sheaf.py --n-seeds 100

  # Smoke test.
  python research/phase2_predictive_sheaf.py --n-seeds 5 --deltas 1

reading the output:
  'predictive_gain_vs_persistence' is the headline.  Positive means
  sheaf features at t explain target at t+delta beyond what just
  knowing target at t does.  For n_legal_moves, this grows from
  +0.24 (delta=1) to +0.49 (delta=10).  Targets rho and
  empty_count are near-monotone in random play so persistence is
  near-R^2=1 and gains are uninformative.

related:
  For PGN tournament trajectories with spectral targets instead
  of random play with state targets, see
  phase1e_predictive_sheaf_pgn.py.
""",
    )
    p.add_argument(
        "--out-json", type=Path, default=default_out_json,
        help="Output JSON summary path.",
    )
    p.add_argument(
        "--out-csv", type=Path, default=default_out_csv,
        help="Output per-pair CSV path.",
    )
    p.add_argument(
        "--cache-dir", type=Path, default=default_cache,
        help="Directory for per-seed trajectory JSON cache (reruns "
             "reuse cached trajectories).",
    )
    p.add_argument(
        "--n-seeds", type=int, default=30,
        help="Number of random-play trajectories to generate (seeds "
             "100 .. 100 + n_seeds - 1).  Default: 30.",
    )
    p.add_argument(
        "--deltas", type=str, default="1,3,5,10",
        help="Comma-separated ply shifts to test.  Default: 1,3,5,10.",
    )
    return p


def main(argv=None):
    args = _build_parser().parse_args(argv)
    deltas = [int(x) for x in args.deltas.split(",")]
    run(
        args.out_json, args.out_csv, args.cache_dir,
        args.n_seeds, deltas,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

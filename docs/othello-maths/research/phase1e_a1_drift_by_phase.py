"""Open item 1 — A1- non-stationary sheaf signature.

§1e.5b found that on the 2025 tournament corpus the sheaf features
at time t predict A1-(t + 10) slightly BETTER than the sheaf at
t + 10 itself does (gain_vs_snap = +0.066 at Delta = 10).  That is
the opposite of a stationary-sheaf expectation and implies the sheaf
-> A1- mapping drifts across the game.

This runner buckets the trajectory by n_empties and fits separate
sheaf -> A1- regressions per bucket, so we can see WHERE the drift
happens:

    opening (60-53 empties, 100% book cov)
    early midgame (52-45)
    late midgame (44-35)
    endgame entry (34-25)
    deep endgame (24-10)
    terminal (9-0)

For each bucket we compute:

    R2_predictive(sheaf_t -> A1-(t+Delta))    for Delta in {1, 3, 5, 10}
    R2_snapshot  (sheaf_{t+Delta} -> A1-(t+Delta))
    R2_persistence(A1-(t) -> A1-(t+Delta))
    beta_pred   regression coefficient vector per bucket

If the coefficient vectors across buckets are similar (within a
bucket-size-normalised distance), the drift is amplitude-only
(stationary structure, non-stationary scale).  If they differ in
sign or magnitude between buckets, the sheaf's relationship to A1-
is phase-specific.
"""

from __future__ import annotations

__version__ = "0.2.0"

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

from othello_utils import BLACK, OthelloBoard
from othello_pgn_loader import (
    _ensure_utf8_stdio, parse_pgn_file, replay,
)
from d4_z2 import project_irrep
from dynamic_sheaf import sheaf_laplacian, spectrum_summary

_ensure_utf8_stdio()


SHEAF_FEATURES = [
    "sheaf_black_lambda2", "sheaf_white_lambda2",
    "sheaf_black_entropy", "sheaf_white_entropy",
    "sheaf_black_lambdamax", "sheaf_white_lambdamax",
]


def _a1_minus_energy(sig: np.ndarray) -> float:
    return float(np.linalg.norm(project_irrep(sig, "A1-")) ** 2)


def _ply_features(state: np.ndarray) -> dict:
    L_b = sheaf_laplacian(state, owner=BLACK)
    spec_b = spectrum_summary(L_b)
    L_w = sheaf_laplacian(state, owner=-BLACK)
    spec_w = spectrum_summary(L_w)
    return {
        "sheaf_black_lambda2":   spec_b["lambda_2"],
        "sheaf_black_entropy":   spec_b["entropy"],
        "sheaf_black_lambdamax": spec_b["lambda_max"],
        "sheaf_white_lambda2":   spec_w["lambda_2"],
        "sheaf_white_entropy":   spec_w["entropy"],
        "sheaf_white_lambdamax": spec_w["lambda_max"],
        "a1_minus_energy": _a1_minus_energy(state.astype(float)),
        "n_empties": int(np.sum(state == 0)),
    }


def compute_corpus_frames(pgn_path: Path) -> list[list[dict]]:
    games = parse_pgn_file(pgn_path)
    trajectories = []
    for gi, g in enumerate(games):
        try:
            _, states, _ = replay(g["moves"])
        except Exception:
            continue
        traj = [_ply_features(st) for st in states]
        trajectories.append(traj)
        if (gi + 1) % 20 == 0 or (gi + 1) == len(games):
            print(f"  processed {gi + 1}/{len(games)} games", flush=True)
    return trajectories


PHASE_BUCKETS = [
    (53, 60, "opening"),
    (45, 52, "early_midgame"),
    (35, 44, "late_midgame"),
    (25, 34, "endgame_entry"),
    (10, 24, "deep_endgame"),
    (0,  9,  "terminal"),
]


def _ols_r2(Y: np.ndarray, X: np.ndarray) -> tuple[float, np.ndarray]:
    if X.size == 0 or X.shape[0] < 5 or np.all(X.std(axis=0) == 0):
        return float("nan"), np.array([])
    X1 = np.concatenate([X, np.ones((len(Y), 1))], axis=1)
    beta, *_ = np.linalg.lstsq(X1, Y, rcond=None)
    pred = X1 @ beta
    resid = Y - pred
    ss_res = float(np.sum(resid ** 2))
    ss_tot = float(np.sum((Y - Y.mean()) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    return r2, beta[:-1]


def analyze(
    trajectories: list[list[dict]], deltas: list[int],
) -> dict:
    # Build per-bucket pair sets for each delta
    by_delta: dict[str, dict] = {}
    for delta in deltas:
        # Collect pairs with bucket tags based on the EARLY frame's
        # n_empties.
        bucket_pairs: dict[str, list[dict]] = {
            label: [] for (_, _, label) in PHASE_BUCKETS
        }
        total_pairs = 0
        for traj in trajectories:
            for t in range(len(traj) - delta):
                early = traj[t]
                late = traj[t + delta]
                e = early["n_empties"]
                label = None
                for lo, hi, lbl in PHASE_BUCKETS:
                    if lo <= e <= hi:
                        label = lbl
                        break
                if label is None:
                    continue
                pair = {
                    "early_sheaf": [early[k] for k in SHEAF_FEATURES],
                    "late_sheaf":  [late[k]  for k in SHEAF_FEATURES],
                    "early_a1m":   early["a1_minus_energy"],
                    "late_a1m":    late["a1_minus_energy"],
                    "early_n_empties": e,
                }
                bucket_pairs[label].append(pair)
                total_pairs += 1
        # Compute per-bucket R2s
        per_bucket = {}
        for label, pairs in bucket_pairs.items():
            if not pairs:
                per_bucket[label] = {"n_pairs": 0}
                continue
            X_early = np.array(
                [p["early_sheaf"] for p in pairs], dtype=float,
            )
            X_late = np.array(
                [p["late_sheaf"]  for p in pairs], dtype=float,
            )
            y_early = np.array(
                [p["early_a1m"]   for p in pairs], dtype=float,
            )
            y_late = np.array(
                [p["late_a1m"]    for p in pairs], dtype=float,
            )
            r2_pred, beta_pred = _ols_r2(y_late, X_early)
            r2_snap, beta_snap = _ols_r2(y_late, X_late)
            r2_pers, _beta = _ols_r2(y_late, y_early.reshape(-1, 1))
            per_bucket[label] = {
                "n_pairs": int(len(pairs)),
                "e_range": [
                    int(min(p["early_n_empties"] for p in pairs)),
                    int(max(p["early_n_empties"] for p in pairs)),
                ],
                "r2_predictive":    r2_pred,
                "r2_snapshot":      r2_snap,
                "r2_persistence":   r2_pers,
                "gain_vs_pers":     r2_pred - r2_pers,
                "gain_vs_snap":     r2_pred - r2_snap,
                "beta_predictive":  beta_pred.tolist() if beta_pred.size else None,
                "beta_snapshot":    beta_snap.tolist() if beta_snap.size else None,
            }
        by_delta[f"delta_{delta}"] = {
            "total_pairs": total_pairs,
            "per_bucket":  per_bucket,
        }
    return by_delta


def run(
    pgn_path: Path, out_json: Path, deltas: list[int],
) -> dict:
    print(f"corpus: {pgn_path}")
    trajectories = compute_corpus_frames(pgn_path)
    lengths = [len(t) for t in trajectories]
    print(
        f"built {len(trajectories)} trajectories; "
        f"mean len {np.mean(lengths):.1f}"
    )
    by_delta = analyze(trajectories, deltas)

    summary = {
        "corpus": str(pgn_path),
        "n_trajectories": len(trajectories),
        "deltas": deltas,
        "sheaf_features_order": SHEAF_FEATURES,
        "phase_buckets": [
            {"lo": lo, "hi": hi, "label": lbl}
            for (lo, hi, lbl) in PHASE_BUCKETS
        ],
        "by_delta": by_delta,
    }
    out_json.parent.mkdir(parents=True, exist_ok=True)
    with out_json.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    # Stdout summary
    print(f"\n=== A1- drift by phase bucket ===")
    for delta_key, delta_info in by_delta.items():
        print(f"\n  {delta_key}  ({delta_info['total_pairs']} pairs)")
        print(f"  {'bucket':16s}  {'N':>5s}  "
              f"{'R2_pred':>7s}  {'R2_snap':>7s}  {'R2_pers':>7s}  "
              f"{'gain_snap':>9s}")
        for label, b in delta_info["per_bucket"].items():
            n = b.get("n_pairs", 0)
            if n == 0:
                print(f"  {label:16s}  {n:>5d}")
                continue
            print(
                f"  {label:16s}  {n:>5d}  "
                f"{b['r2_predictive']:+7.3f}  "
                f"{b['r2_snapshot']:+7.3f}  "
                f"{b['r2_persistence']:+7.3f}  "
                f"{b['gain_vs_snap']:+9.4f}"
            )
    print(f"\nwrote {out_json}")
    return summary


def _build_parser():
    research_dir = Path(__file__).resolve().parent
    default_pgn = (
        research_dir.parent / "dataset"
        / "liveothello_Barcelona_EGP_2026.pgn"
    )
    default_out = (
        research_dir.parent / "results"
        / "phase1e_a1_drift_by_phase.json"
    )
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  # Default: Barcelona 35-game corpus.
  python research/phase1e_a1_drift_by_phase.py

  # Scale up to 2025 (takes a few minutes for sheaf computation).
  python research/phase1e_a1_drift_by_phase.py \\
      --pgn ../dataset/liveothello_2025_all.pgn \\
      --out ../results/phase1e_a1_drift_2025.json

reading the output:
  If 'r2_predictive' is similar to 'r2_snapshot' within a bucket
  but the BUCKET-TO-BUCKET coefficient vectors (beta_predictive)
  disagree in sign/magnitude, the drift is phase-specific.  A
  positive 'gain_vs_snap' that stays stable across buckets would
  instead point at a uniformly-non-stationary sheaf.
""",
    )
    p.add_argument("--pgn", type=Path, default=default_pgn)
    p.add_argument("--out", type=Path, default=default_out)
    p.add_argument(
        "--deltas", type=str, default="1,3,5,10",
        help="Comma-separated ply shifts.  Default 1,3,5,10.",
    )
    return p


def main(argv=None):
    args = _build_parser().parse_args(argv)
    deltas = [int(x) for x in args.deltas.split(",")]
    if not args.pgn.exists():
        print(f"PGN not found: {args.pgn}", file=sys.stderr)
        return 2
    run(args.pgn, args.out, deltas)
    return 0


if __name__ == "__main__":
    sys.exit(main())

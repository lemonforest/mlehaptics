"""Follow-up iii — why does the faithful sheaf's gain_vs_snap stay > 0?

Observation (Open-5, Barcelona faithful sheaf):
  faithful sheaf at time t predicts n_legal_moves / rho /
  empty_count / spectral targets at time t + Delta BETTER than
  the faithful sheaf at time t + Delta does.

  Specifically on Barcelona at Delta=10:
    target=d4_e_occ        gain_vs_snap = +0.086
    target=empty_count     gain_vs_snap = +0.060
    target=rho             gain_vs_snap = +0.060
    target=a1_minus_energy gain_vs_snap = +0.028

That is counter-intuitive: a CURRENT snapshot should have at
least as much information about itself as a snapshot from the
past.  Three candidate explanations:

  H1 — Trajectory memory.  Faithful sheaf at t encodes pending
        brackets (R3) that WILL flip in the next few plies.
        At t + Delta, those pendings have resolved into R2
        completes (flipped) or disappeared (covered); the
        "what is about to happen" signal from t is gone, so
        snapshot at t+Delta lacks that info.

  H2 — In-sample overfit / survivorship.  The R^2 values are
        in-sample; maybe the regression at t overfits
        features that happen to predict surviving trajectories,
        while the snapshot at t+Delta doesn't have the same
        overfitting opportunity.  Test: train/test split.

  H3 — Kernel_dim signal.  Faithful kernel dim varies with
        state (141..188).  It might encode more about the
        trajectory shape than a single snapshot can reveal.
        Test: per-feature ablation.

Probes:
  1. Extended Delta sweep (1, 2, 3, 5, 7, 10, 15, 20) on
     Barcelona — does gain_vs_snap grow, stay flat, or collapse
     at long shifts?
  2. Per-feature ablation: drop one of the 8 sheaf features at
     a time; recompute R^2_pred and R^2_snap; see which feature's
     removal kills the gain.
  3. Train/test split: first 18 games train, last 17 test.
     Test-set R^2 rules out overfit explanation.

Outputs: results/phase1e_faithful_gain_investigation.json
"""

from __future__ import annotations

__version__ = "0.2.0"

import argparse
import json
import sys
from pathlib import Path

import numpy as np

from othello_utils import BLACK, OthelloBoard
from othello_pgn_loader import (
    _ensure_utf8_stdio, parse_pgn_file, replay,
)
from d4_z2 import D4_CHARS, D4_PERMS, project_irrep
from faithful_sheaf import faithful_sheaf_laplacian, spectrum_summary

_ensure_utf8_stdio()


SHEAF_FEATURES = (
    "sheaf_black_lambda2", "sheaf_white_lambda2",
    "sheaf_black_entropy", "sheaf_white_entropy",
    "sheaf_black_kerdim",  "sheaf_white_kerdim",
    "sheaf_black_lambdamax", "sheaf_white_lambdamax",
)


def _d4_only_energy(sig: np.ndarray, irrep: str) -> float:
    proj = np.zeros_like(sig, dtype=float)
    for g in range(8):
        proj = proj + D4_CHARS[irrep][g] * sig[D4_PERMS[g]]
    d_mu = 2 if irrep == "E" else 1
    proj = proj * (d_mu / 8.0)
    return float(np.sum(proj * proj))


def _ply_features(state: np.ndarray, side: int) -> dict:
    L_b = faithful_sheaf_laplacian(state, owner=BLACK)
    spec_b = spectrum_summary(L_b)
    L_w = faithful_sheaf_laplacian(state, owner=-BLACK)
    spec_w = spectrum_summary(L_w)
    bb = OthelloBoard()
    bb.state = state.copy()
    bb.side_to_move = side
    b = int(np.sum(state == 1))
    w = int(np.sum(state == -1))
    e = int(np.sum(state == 0))
    sig = state.astype(float)
    occ = sig ** 2
    return {
        # Sheaf features
        "sheaf_black_lambda2":   spec_b["lambda_2"],
        "sheaf_black_entropy":   spec_b["entropy"],
        "sheaf_black_kerdim":    spec_b["kernel_dim"],
        "sheaf_black_lambdamax": spec_b["lambda_max"],
        "sheaf_white_lambda2":   spec_w["lambda_2"],
        "sheaf_white_entropy":   spec_w["entropy"],
        "sheaf_white_kerdim":    spec_w["kernel_dim"],
        "sheaf_white_lambdamax": spec_w["lambda_max"],
        # Targets
        "n_legal_moves": len(bb.legal_moves()),
        "rho": (b + w) / 64.0,
        "empty_count": e,
        "a1_minus_energy": float(
            np.linalg.norm(project_irrep(sig, "A1-")) ** 2
        ),
        "d4_a1_occupation_energy": _d4_only_energy(occ, "A1"),
        "d4_e_occupation_energy":  _d4_only_energy(occ, "E"),
    }


def build_trajectories(pgn_path: Path) -> list[list[dict]]:
    games = parse_pgn_file(pgn_path)
    trajectories: list[list[dict]] = []
    for gi, g in enumerate(games):
        try:
            _, states, move_log = replay(g["moves"])
        except Exception:
            continue
        side = BLACK
        traj = []
        for ply, st in enumerate(states):
            if ply > 0:
                side = -move_log[ply - 1]["side"]
            traj.append(_ply_features(st, side))
        trajectories.append(traj)
        if (gi + 1) % 10 == 0 or (gi + 1) == len(games):
            print(f"  processed {gi + 1}/{len(games)} games", flush=True)
    return trajectories


def _ols_r2(Y: np.ndarray, X: np.ndarray) -> float:
    if X.size == 0 or X.shape[0] < 5 or np.all(X.std(axis=0) == 0):
        return float("nan")
    X1 = np.concatenate([X, np.ones((len(Y), 1))], axis=1)
    beta, *_ = np.linalg.lstsq(X1, Y, rcond=None)
    resid = Y - X1 @ beta
    ss_res = float(np.sum(resid ** 2))
    ss_tot = float(np.sum((Y - Y.mean()) ** 2))
    return 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0


def _ols_fit_predict(Y_train, X_train, X_test) -> np.ndarray:
    X_train1 = np.concatenate(
        [X_train, np.ones((len(Y_train), 1))], axis=1
    )
    beta, *_ = np.linalg.lstsq(X_train1, Y_train, rcond=None)
    X_test1 = np.concatenate(
        [X_test, np.ones((len(X_test), 1))], axis=1
    )
    return X_test1 @ beta


def _r2_from_pred(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    resid = y_true - y_pred
    ss_res = float(np.sum(resid ** 2))
    ss_tot = float(np.sum((y_true - y_true.mean()) ** 2))
    return 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0


def collect_pairs(
    trajectories: list[list[dict]], delta: int,
    train_games: set[int] | None = None,
) -> dict:
    """Collect (X_early, X_late, target_early, target_late) pairs,
    optionally segregated by train_games for train/test split."""
    target_keys = [
        "a1_minus_energy", "d4_a1_occupation_energy",
        "d4_e_occupation_energy", "n_legal_moves",
        "rho", "empty_count",
    ]
    def _pair_set(traj_indices: list[int]) -> dict:
        X_e, X_l = [], []
        tgts_e = {k: [] for k in target_keys}
        tgts_l = {k: [] for k in target_keys}
        for gi in traj_indices:
            traj = trajectories[gi]
            for t in range(len(traj) - delta):
                early = traj[t]
                late = traj[t + delta]
                X_e.append([early[k] for k in SHEAF_FEATURES])
                X_l.append([late[k]  for k in SHEAF_FEATURES])
                for k in target_keys:
                    tgts_e[k].append(early[k])
                    tgts_l[k].append(late[k])
        return {
            "X_early": np.array(X_e, dtype=float),
            "X_late":  np.array(X_l, dtype=float),
            "targets_early": {
                k: np.array(v, dtype=float) for k, v in tgts_e.items()
            },
            "targets_late": {
                k: np.array(v, dtype=float) for k, v in tgts_l.items()
            },
        }
    n = len(trajectories)
    if train_games is None:
        return {"all": _pair_set(list(range(n)))}
    train_idx = [i for i in range(n) if i in train_games]
    test_idx  = [i for i in range(n) if i not in train_games]
    return {
        "train": _pair_set(train_idx),
        "test":  _pair_set(test_idx),
    }


def multivariate_r2(pair_set: dict, target: str) -> dict:
    y_e = pair_set["targets_early"][target]
    y_l = pair_set["targets_late"][target]
    r2_pred = _ols_r2(y_l, pair_set["X_early"])
    r2_snap = _ols_r2(y_l, pair_set["X_late"])
    r2_pers = _ols_r2(y_l, y_e.reshape(-1, 1))
    return {
        "r2_predictive":  r2_pred,
        "r2_snapshot":    r2_snap,
        "r2_persistence": r2_pers,
        "gain_vs_pers":   r2_pred - r2_pers,
        "gain_vs_snap":   r2_pred - r2_snap,
        "n": int(len(y_e)),
    }


def train_test_r2(
    train_set: dict, test_set: dict, target: str,
) -> dict:
    """Out-of-sample R^2 using train-fit model evaluated on test."""
    y_test_l = test_set["targets_late"][target]
    # predictive: fit on train (X_early -> y_late), predict on test
    y_pred = _ols_fit_predict(
        train_set["targets_late"][target],
        train_set["X_early"],
        test_set["X_early"],
    )
    r2_pred_oos = _r2_from_pred(y_test_l, y_pred)
    # snapshot: fit on train (X_late -> y_late), predict on test
    y_pred2 = _ols_fit_predict(
        train_set["targets_late"][target],
        train_set["X_late"],
        test_set["X_late"],
    )
    r2_snap_oos = _r2_from_pred(y_test_l, y_pred2)
    return {
        "r2_predictive_oos":  r2_pred_oos,
        "r2_snapshot_oos":    r2_snap_oos,
        "gain_vs_snap_oos":   r2_pred_oos - r2_snap_oos,
    }


def ablation(pair_set: dict, target: str) -> dict:
    """Drop one feature at a time, measure R^2 loss for predictive
    and snapshot regressions.  The feature whose removal kills the
    gain_vs_snap is the one responsible for the positive signal."""
    y_l = pair_set["targets_late"][target]
    X_e = pair_set["X_early"]
    X_l = pair_set["X_late"]
    n_feats = X_e.shape[1]
    baseline_pred = _ols_r2(y_l, X_e)
    baseline_snap = _ols_r2(y_l, X_l)
    per_feat = {}
    for i in range(n_feats):
        keep = [j for j in range(n_feats) if j != i]
        r2_pred_drop = _ols_r2(y_l, X_e[:, keep])
        r2_snap_drop = _ols_r2(y_l, X_l[:, keep])
        per_feat[SHEAF_FEATURES[i]] = {
            "delta_pred": baseline_pred - r2_pred_drop,
            "delta_snap": baseline_snap - r2_snap_drop,
            "delta_gain": (
                (baseline_pred - baseline_snap)
                - (r2_pred_drop - r2_snap_drop)
            ),
        }
    return {
        "baseline_pred": baseline_pred,
        "baseline_snap": baseline_snap,
        "baseline_gain_vs_snap": baseline_pred - baseline_snap,
        "per_feature": per_feat,
    }


def run(pgn_path: Path, out_json: Path) -> dict:
    print(f"corpus: {pgn_path}")
    trajectories = build_trajectories(pgn_path)
    n = len(trajectories)
    print(f"trajectories: {n}; mean length {np.mean([len(t) for t in trajectories]):.1f}")

    deltas = [1, 2, 3, 5, 7, 10, 15, 20]
    focus_targets = [
        "n_legal_moves", "a1_minus_energy",
        "d4_a1_occupation_energy", "d4_e_occupation_energy",
        "rho", "empty_count",
    ]

    # --- Probe 1: delta sweep on all pairs ---
    delta_sweep: dict = {}
    for delta in deltas:
        pairs = collect_pairs(trajectories, delta)["all"]
        mv = {}
        for tk in focus_targets:
            mv[tk] = multivariate_r2(pairs, tk)
        delta_sweep[f"delta_{delta}"] = {"n_pairs": pairs["X_early"].shape[0], "mv": mv}

    # --- Probe 2: train/test split at Delta=10 ---
    train_games = set(range(0, n // 2))   # first half
    split_pairs = collect_pairs(trajectories, 10, train_games=train_games)
    oos_results = {}
    for tk in focus_targets:
        oos_results[tk] = train_test_r2(
            split_pairs["train"], split_pairs["test"], tk,
        )

    # --- Probe 3: per-feature ablation at Delta=10 on d4_e_occupation ---
    ablation_pairs = collect_pairs(trajectories, 10)["all"]
    ablation_results = {}
    for tk in ["d4_e_occupation_energy", "a1_minus_energy", "rho", "n_legal_moves"]:
        ablation_results[tk] = ablation(ablation_pairs, tk)

    summary = {
        "corpus": str(pgn_path),
        "n_trajectories": n,
        "sheaf_features_order": list(SHEAF_FEATURES),
        "delta_sweep": delta_sweep,
        "train_test_split_delta10": {
            "n_train_games": len(train_games),
            "n_test_games":  n - len(train_games),
            "n_train_pairs": int(split_pairs["train"]["X_early"].shape[0]),
            "n_test_pairs":  int(split_pairs["test"]["X_early"].shape[0]),
            "results_by_target": oos_results,
        },
        "ablation_delta10": ablation_results,
    }

    out_json.parent.mkdir(parents=True, exist_ok=True)
    with out_json.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    # --- Stdout: three probes ---
    print(f"\n=== Probe 1 (Delta sweep, in-sample R^2) ===")
    print(f"{'Delta':>5s}  {'target':>24s}  {'R2_pred':>8s}  {'R2_snap':>8s}  {'gain':>7s}")
    for delta in deltas:
        key = f"delta_{delta}"
        for tk in focus_targets:
            r = delta_sweep[key]["mv"][tk]
            print(f"{delta:>5d}  {tk:>24s}  {r['r2_predictive']:+8.4f}  "
                  f"{r['r2_snapshot']:+8.4f}  {r['gain_vs_snap']:+7.4f}")
    print(f"\n=== Probe 2 (OOS at Delta=10, train={len(train_games)} games, test={n - len(train_games)}) ===")
    for tk in focus_targets:
        r = oos_results[tk]
        print(f"  {tk:>24s}  R2_pred_oos={r['r2_predictive_oos']:+.4f}  "
              f"R2_snap_oos={r['r2_snapshot_oos']:+.4f}  "
              f"gain={r['gain_vs_snap_oos']:+.4f}")
    print(f"\n=== Probe 3 (Per-feature ablation at Delta=10) ===")
    for tk in ablation_results:
        ab = ablation_results[tk]
        print(f"\n  target = {tk}")
        print(f"    baseline:  R2_pred={ab['baseline_pred']:+.4f}  R2_snap={ab['baseline_snap']:+.4f}  "
              f"gain={ab['baseline_gain_vs_snap']:+.4f}")
        print(f"    {'feature':28s}  {'dPred':>8s}  {'dSnap':>8s}  {'dGain':>8s}")
        for fn, stats in ab["per_feature"].items():
            print(f"    {fn:28s}  {stats['delta_pred']:+8.4f}  "
                  f"{stats['delta_snap']:+8.4f}  {stats['delta_gain']:+8.4f}")
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
        / "phase1e_faithful_gain_investigation.json"
    )
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--pgn", type=Path, default=default_pgn)
    p.add_argument("--out", type=Path, default=default_out)
    return p


def main(argv=None):
    args = _build_parser().parse_args(argv)
    if not args.pgn.exists():
        print(f"PGN not found: {args.pgn}", file=sys.stderr)
        return 2
    run(args.pgn, args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())

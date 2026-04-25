"""Phase 1e.5b — predictive sheaf validation on real PGN trajectories
with richer targets (spectral observables, not just ρ / n_legal).

Context
-------
Phase 1e.5 tested the sheaf spectrum as a forward predictor on
30 RANDOM-PLAY trajectories with targets n_legal_moves, ρ,
empty_count.  ρ and empties are near-monotone in random play
(persistence R² ≈ 1.0), making them uninformative as prediction
targets.  n_legal gave a positive result: gain vs persistence
+0.24 → +0.49 as Δ grew to 10.

This runner extends the test:

  (a) Real tournament PGN corpora (Barcelona EGP / APR 2026 / 2025
      full) as trajectory sources.  Tournament play is not random;
      the question is whether the sheaf's forward-predictive power
      survives under strategic play.
  (b) Richer targets: A1- magnetisation energy, D4-A1(s^2) occupation
      energy, D4-E(s^2) occupation energy at ply t + Δ.  These are
      NOT monotone in game progress (they oscillate with flanking
      events) so the persistence baseline is non-trivial.

Outputs
-------
  results/phase1e_predictive_sheaf_pgn_<corpus_tag>.json
  results/phase1e_predictive_sheaf_pgn_<corpus_tag>_pairs.csv

For each (feature_group, target, Δ) combination we report:

  R²(predictive): features at t -> target at t+Δ
  R²(snapshot):   features at t+Δ -> target at t+Δ
  R²(persistence): target at t -> target at t+Δ
  gain_vs_persistence, gain_vs_snapshot
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

from othello_utils import BLACK, N, OthelloBoard
from othello_pgn_loader import _ensure_utf8_stdio, parse_pgn_file, replay
from d4_z2 import D4_CHARS, D4_PERMS, project_irrep
from dynamic_sheaf import sheaf_laplacian, spectrum_summary

_ensure_utf8_stdio()


SHEAF_FEATURES = [
    "sheaf_black_lambda2", "sheaf_white_lambda2",
    "sheaf_black_entropy", "sheaf_white_entropy",
    "sheaf_black_lambdamax", "sheaf_white_lambdamax",
]
# kernel_dim excluded (§3.4: constant at 128 under crude restriction
# maps, gives scipy ConstantInputWarning and zero variance).
# lambda_max retained as a feature.

SPECTRAL_TARGETS = [
    "a1_minus_energy",
    "d4_a1_occupation_energy",
    "d4_e_occupation_energy",
]
STATE_TARGETS = ["n_legal_moves", "rho", "empty_count"]
ALL_TARGETS = SPECTRAL_TARGETS + STATE_TARGETS


def _d4_only_energy(sig: np.ndarray, irrep: str) -> float:
    proj = np.zeros_like(sig, dtype=float)
    for g in range(8):
        proj = proj + D4_CHARS[irrep][g] * sig[D4_PERMS[g]]
    d_mu = 2 if irrep == "E" else 1
    proj = proj * (d_mu / 8.0)
    return float(np.sum(proj * proj))


def _spectral_observables(state: np.ndarray) -> dict:
    sig = state.astype(float)
    occ = sig ** 2
    return {
        "a1_minus_energy": float(
            np.linalg.norm(project_irrep(sig, "A1-")) ** 2
        ),
        "d4_a1_occupation_energy": _d4_only_energy(occ, "A1"),
        "d4_e_occupation_energy":  _d4_only_energy(occ, "E"),
    }


def _ply_record(state: np.ndarray, side: int) -> dict:
    """Compute sheaf spectra + spectral observables + state context
    for a single state.  Returns dict compatible with prior
    phase1e_predictive_sheaf schema."""
    L_b = sheaf_laplacian(state, owner=BLACK)
    spec_b = spectrum_summary(L_b)
    L_w = sheaf_laplacian(state, owner=-BLACK)
    spec_w = spectrum_summary(L_w)
    bb = OthelloBoard()
    bb.state = state.copy()
    bb.side_to_move = side
    lm = bb.legal_moves()
    b = int(np.sum(state == BLACK))
    w = int(np.sum(state == -BLACK))
    e = int(np.sum(state == 0))
    obs = _spectral_observables(state)
    return {
        "side_to_move": int(side),
        "rho": (b + w) / 64.0,
        "black_count": b,
        "white_count": w,
        "empty_count": e,
        "n_legal_moves": len(lm),
        "sheaf_black_lambda2":   spec_b["lambda_2"],
        "sheaf_black_lambdamax": spec_b["lambda_max"],
        "sheaf_black_kerdim":    spec_b["kernel_dim"],
        "sheaf_black_entropy":   spec_b["entropy"],
        "sheaf_white_lambda2":   spec_w["lambda_2"],
        "sheaf_white_lambdamax": spec_w["lambda_max"],
        "sheaf_white_kerdim":    spec_w["kernel_dim"],
        "sheaf_white_entropy":   spec_w["entropy"],
        **obs,
    }


def pgn_trajectories(
    pgn_path: Path, n_games: int | None, seed: int,
) -> tuple[list[list[dict]], list[dict]]:
    """Replay each game; return (trajectories, game_meta).  Each
    trajectory is a list of ply records; game_meta is aligned headers
    plus replay counts."""
    games = parse_pgn_file(pgn_path)
    if n_games is not None and n_games < len(games):
        rng = np.random.default_rng(seed)
        idx = rng.choice(len(games), size=n_games, replace=False)
        games = [games[int(i)] for i in sorted(idx)]
    trajectories: list[list[dict]] = []
    metas: list[dict] = []
    t0 = time.time()
    for gi, g in enumerate(games):
        try:
            _, states, move_log = replay(g["moves"])
        except Exception as exc:
            print(
                f"game {gi} replay failed: {exc}", file=sys.stderr,
            )
            continue
        traj = []
        side = BLACK
        for ply, st in enumerate(states):
            if ply > 0:
                side = -move_log[ply - 1]["side"]
            rec = _ply_record(st, side)
            rec["move_no"] = ply
            traj.append(rec)
        trajectories.append(traj)
        metas.append({
            "game_index": gi,
            "headers": g["headers"],
            "n_plies": len(traj),
        })
        if (gi + 1) % 20 == 0 or (gi + 1) == len(games):
            elapsed = time.time() - t0
            rate = (gi + 1) / max(elapsed, 1e-6)
            eta_s = (len(games) - gi - 1) / max(rate, 1e-6)
            print(
                f"  [{gi + 1}/{len(games)}] elapsed {elapsed:.0f}s "
                f"rate {rate:.2f} g/s eta {eta_s / 60:.1f} min",
                flush=True,
            )
    return trajectories, metas


def _ols_r2(Y: np.ndarray, X: np.ndarray) -> float:
    if X.size == 0 or np.all(X.std(axis=0) == 0):
        return float("nan")
    X1 = np.concatenate([X, np.ones((len(Y), 1))], axis=1)
    beta, *_ = np.linalg.lstsq(X1, Y, rcond=None)
    resid = Y - X1 @ beta
    ss_res = float(np.sum(resid ** 2))
    ss_tot = float(np.sum((Y - Y.mean()) ** 2))
    return 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0


def _analyze(pairs: list[dict], delta: int) -> dict:
    """Compute R² metrics and univariate Spearmans at one Δ."""
    n = len(pairs)
    if n < 20:
        return {"n_pairs": n, "skipped": True}
    sheaf_early = {
        k: np.array([p[f"early__{k}"] for p in pairs]) for k in SHEAF_FEATURES
    }
    sheaf_late = {
        k: np.array([p[f"late__{k}"] for p in pairs]) for k in SHEAF_FEATURES
    }
    target_early = {
        k: np.array([p[f"early__{k}"] for p in pairs]) for k in ALL_TARGETS
    }
    target_late = {
        k: np.array([p[f"late__{k}"] for p in pairs]) for k in ALL_TARGETS
    }

    X_early = np.stack(
        [sheaf_early[k] for k in SHEAF_FEATURES], axis=1
    )
    X_late = np.stack(
        [sheaf_late[k] for k in SHEAF_FEATURES], axis=1
    )

    multivariate: dict = {}
    for tk in ALL_TARGETS:
        y = target_late[tk]
        r2_pred = _ols_r2(y, X_early)
        r2_snap = _ols_r2(y, X_late)
        pers = target_early[tk].reshape(-1, 1)
        r2_pers = _ols_r2(y, pers)
        multivariate[tk] = {
            "r2_predictive_full_sheaf_at_t":   r2_pred,
            "r2_snapshot_full_sheaf_at_t_plus_delta": r2_snap,
            "r2_persistence_target_at_t":      r2_pers,
            "predictive_gain_vs_persistence":  r2_pred - r2_pers,
            "predictive_gain_vs_snapshot":     r2_pred - r2_snap,
            "n": n,
        }

    univariate: dict = {}
    for tk in ALL_TARGETS:
        y = target_late[tk]
        sp_pers = spearmanr(target_early[tk], y)
        univariate[f"persistence__{tk}"] = {
            "rho": float(sp_pers.statistic),
            "p": float(sp_pers.pvalue),
            "n": n,
        }
        for fk in SHEAF_FEATURES:
            sp_pred = spearmanr(sheaf_early[fk], y)
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

    return {
        "n_pairs": n,
        "multivariate_r2": multivariate,
        "univariate": univariate,
    }


def _build_pairs(
    trajectories: list[list[dict]], delta: int,
) -> list[dict]:
    pairs = []
    for gi, traj in enumerate(trajectories):
        for t in range(len(traj) - delta):
            early = traj[t]
            late = traj[t + delta]
            row = {"game": gi, "t": t, "delta": delta}
            for k in SHEAF_FEATURES + ALL_TARGETS:
                row[f"early__{k}"] = early[k]
                row[f"late__{k}"]  = late[k]
            pairs.append(row)
    return pairs


def run(
    pgn_path: Path,
    out_json: Path, out_csv: Path | None,
    n_games: int | None, deltas: list[int],
    seed: int, write_pairs: bool,
) -> dict:
    corpus_tag = pgn_path.stem
    print(f"corpus: {pgn_path} (tag={corpus_tag})")
    print(f"deltas: {deltas}")
    print(f"sampling seed: {seed}  n_games cap: {n_games}")

    t0 = time.time()
    trajectories, metas = pgn_trajectories(
        pgn_path, n_games=n_games, seed=seed,
    )
    elapsed = time.time() - t0
    lengths = [len(t) for t in trajectories]
    print(
        f"replayed {len(trajectories)} games in {elapsed:.1f}s; "
        f"mean traj length {np.mean(lengths):.1f}"
    )

    summary: dict = {
        "corpus": str(pgn_path),
        "corpus_tag": corpus_tag,
        "n_games_requested": n_games,
        "n_games_replayed": len(trajectories),
        "deltas": deltas,
        "trajectory_lengths_summary": {
            "min": int(min(lengths)) if lengths else 0,
            "max": int(max(lengths)) if lengths else 0,
            "mean": float(np.mean(lengths)) if lengths else 0.0,
        },
        "sheaf_features": SHEAF_FEATURES,
        "spectral_targets": SPECTRAL_TARGETS,
        "state_targets": STATE_TARGETS,
        "wall_time_seconds": elapsed,
    }
    per_delta = {}
    all_pairs = []
    for delta in deltas:
        pairs = _build_pairs(trajectories, delta)
        analysis = _analyze(pairs, delta)
        per_delta[f"delta_{delta}"] = analysis
        if write_pairs:
            all_pairs.extend(pairs)
        # Stdout highlights
        mv = analysis.get("multivariate_r2", {})
        print(
            f"\ndelta={delta}: {len(pairs)} pairs"
        )
        for tk in ALL_TARGETS:
            g = mv.get(tk, {})
            if "r2_predictive_full_sheaf_at_t" not in g:
                continue
            print(
                f"  {tk:28s}  "
                f"R2_pred={g['r2_predictive_full_sheaf_at_t']:+.4f}  "
                f"R2_snap={g['r2_snapshot_full_sheaf_at_t_plus_delta']:+.4f}  "
                f"R2_pers={g['r2_persistence_target_at_t']:+.4f}  "
                f"gain_pers={g['predictive_gain_vs_persistence']:+.4f}  "
                f"gain_snap={g['predictive_gain_vs_snapshot']:+.4f}"
            )
    summary["per_delta"] = per_delta
    # Game meta is bulky and optional - omit from JSON by default

    out_json.parent.mkdir(parents=True, exist_ok=True)
    with out_json.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"\nwrote {out_json}")

    if write_pairs and out_csv is not None and all_pairs:
        fieldnames = list(all_pairs[0].keys())
        with out_csv.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in all_pairs:
                writer.writerow(row)
        print(f"wrote {out_csv}")

    return summary


def _build_parser():
    default_results = (
        Path(__file__).resolve().parent.parent / "results"
    )
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  # Full 2025 tournament archive, all deltas.  Walltime ~1-2 hours on
  # a fast laptop for the full 2178 games.
  python research/phase1e_predictive_sheaf_pgn.py \\
      --pgn ../dataset/liveothello_2025_all.pgn

  # Single-month slice (APR 2026, 414 games).  Walltime ~20 min.
  python research/phase1e_predictive_sheaf_pgn.py \\
      --pgn ../dataset/liveothello-2026-APR.pgn

  # Quick smoke test: 10 random Barcelona games, deltas 1 and 5.
  python research/phase1e_predictive_sheaf_pgn.py \\
      --pgn ../dataset/liveothello_Barcelona_EGP_2026.pgn \\
      --n-games 10 --deltas 1,5

reading the output:
  The 'r2_predictive_full_sheaf_at_t' entries answer whether the
  sheaf features at move t carry forward-predictive content about
  target t+Delta moves.  Compare against:
     r2_persistence_target_at_t     (pure target auto-correlation)
     r2_snapshot_full_sheaf_at_t_plus_delta (same-time baseline)
  Positive 'predictive_gain_vs_persistence' means the sheaf at t
  predicts target at t+Delta better than just knowing target at t.
  Positive 'predictive_gain_vs_snapshot' would be a strong claim
  (sheaf at t predicts target at t+Delta better than sheaf at
  t+Delta itself predicts it); generally we expect near zero.

targets:
  Spectral targets (a1_minus, d4_a1_occ, d4_e_occ) are non-monotone
  in game progress so persistence is meaningful for them.  State
  targets (rho, empty_count) are near-monotone in filling order;
  gain_vs_persistence for those is essentially uninformative.  This
  runner includes state targets as controls.
""",
    )
    p.add_argument(
        "--pgn", type=Path, required=True,
        help="Path to a PGN corpus in the eOthello / liveothello "
             "transcript format.  Committed corpora live under "
             "dataset/.",
    )
    p.add_argument(
        "--out-dir", type=Path, default=default_results,
        help="Output directory.  JSON and optional pairs CSV are "
             "written as phase1e_predictive_sheaf_pgn_<tag>.json / "
             "_pairs.csv.  Default: ../results/.",
    )
    p.add_argument(
        "--n-games", type=int, default=None,
        help="Cap on number of games replayed (deterministic given "
             "--seed).  Default: process all games in the PGN.",
    )
    p.add_argument(
        "--seed", type=int, default=42,
        help="Sampling seed when --n-games is given.  Default: 42.",
    )
    p.add_argument(
        "--deltas", type=str, default="1,3,5,10",
        help="Comma-separated time shifts in plies.  Default: 1,3,5,10.",
    )
    p.add_argument(
        "--no-pairs-csv", action="store_true",
        help="Do not write the per-pair CSV (multi-hundred-MB for "
             "large corpora; the JSON summary is enough for reports).",
    )
    return p


def main(argv=None):
    args = _build_parser().parse_args(argv)
    deltas = [int(x) for x in args.deltas.split(",")]
    if not args.pgn.exists():
        print(f"PGN not found: {args.pgn}", file=sys.stderr)
        return 2
    args.out_dir.mkdir(parents=True, exist_ok=True)
    tag = args.pgn.stem
    out_json = args.out_dir / f"phase1e_predictive_sheaf_pgn_{tag}.json"
    out_csv = (
        args.out_dir / f"phase1e_predictive_sheaf_pgn_{tag}_pairs.csv"
    )
    run(
        args.pgn, out_json, out_csv,
        args.n_games, deltas, args.seed,
        write_pairs=not args.no_pairs_csv,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

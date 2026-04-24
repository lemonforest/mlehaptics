"""Open item 5 — predictive sheaf with faithful (bracket-aware) restrictions.

§1e.5 and §1e.5b measured predictive power of the CRUDE sheaf
Laplacian (endpoint-only restrictions) against n_legal_moves and
spectral targets (A1-, D4-A1(s^2), D4-E(s^2)).

This runner reruns the same analysis using the FAITHFUL sheaf
Laplacian from faithful_sheaf.py, which only builds edges across
active brackets (R2 stable flank or R3 pending flip).  Questions:

  1. Does the A1- persistence-vs-sheaf crossover at Delta=5..7
     from §1e.5b get SHARPER under faithful restrictions?
  2. Does kernel_dim as a sheaf feature become informative (the
     faithful kernel is position-dependent, 141..188 range, not
     a constant 128)?
  3. Does the gain_vs_snap > 0 non-stationary signature persist
     or flip sign?

Walltime: single-sheaf computation is ~50ms at 192x192.  Faithful
sheaf has additional bracket-walk overhead.  At 2178 games x 60
plies x 2 (black/white sheaves) that's roughly 25 k positions per
half-second of bracket enumeration, so end-to-end ~2-3x the
original 50 min for the crude 1e.5b run.  Recommended: start on
the small Barcelona corpus first, confirm signal qualitatively,
then rerun on 2025.
"""

from __future__ import annotations

__version__ = "0.2.0"

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

from othello_utils import BLACK, OthelloBoard
from othello_pgn_loader import (
    _ensure_utf8_stdio, parse_pgn_file, replay,
)
from d4_z2 import D4_CHARS, D4_PERMS, project_irrep
from faithful_sheaf import (
    faithful_sheaf_laplacian, spectrum_summary, bracket_summary,
)

_ensure_utf8_stdio()


SHEAF_FEATURES = [
    "faithful_black_lambda2", "faithful_white_lambda2",
    "faithful_black_entropy", "faithful_white_entropy",
    "faithful_black_kerdim",  "faithful_white_kerdim",
    "faithful_black_lambdamax", "faithful_white_lambdamax",
]


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
        "a1_minus_energy": float(np.linalg.norm(project_irrep(sig, "A1-")) ** 2),
        "d4_a1_occupation_energy": _d4_only_energy(occ, "A1"),
        "d4_e_occupation_energy":  _d4_only_energy(occ, "E"),
    }


def _ply_record(state: np.ndarray, side: int) -> dict:
    L_b = faithful_sheaf_laplacian(state, owner=BLACK)
    spec_b = spectrum_summary(L_b)
    L_w = faithful_sheaf_laplacian(state, owner=-BLACK)
    spec_w = spectrum_summary(L_w)
    bb = OthelloBoard()
    bb.state = state.copy()
    bb.side_to_move = side
    lm = bb.legal_moves()
    b = int(np.sum(state == 1))
    w = int(np.sum(state == -1))
    e = int(np.sum(state == 0))
    obs = _spectral_observables(state)
    return {
        "side_to_move": int(side),
        "rho": (b + w) / 64.0,
        "empty_count": e,
        "n_legal_moves": len(lm),
        "faithful_black_lambda2":   spec_b["lambda_2"],
        "faithful_black_lambdamax": spec_b["lambda_max"],
        "faithful_black_kerdim":    spec_b["kernel_dim"],
        "faithful_black_entropy":   spec_b["entropy"],
        "faithful_white_lambda2":   spec_w["lambda_2"],
        "faithful_white_lambdamax": spec_w["lambda_max"],
        "faithful_white_kerdim":    spec_w["kernel_dim"],
        "faithful_white_entropy":   spec_w["entropy"],
        **obs,
    }


def pgn_trajectories(pgn_path: Path) -> list[list[dict]]:
    games = parse_pgn_file(pgn_path)
    trajectories = []
    t0 = time.time()
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
            traj.append(_ply_record(st, side))
        trajectories.append(traj)
        if (gi + 1) % 20 == 0 or (gi + 1) == len(games):
            elapsed = time.time() - t0
            rate = (gi + 1) / max(elapsed, 1e-6)
            eta = (len(games) - gi - 1) / max(rate, 1e-6)
            print(
                f"  [{gi + 1}/{len(games)}]  elapsed {elapsed:.0f}s  "
                f"rate {rate:.2f} g/s  eta {eta/60:.1f} min",
                flush=True,
            )
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


def analyze(trajectories: list[list[dict]], deltas: list[int]) -> dict:
    all_targets = [
        "a1_minus_energy", "d4_a1_occupation_energy",
        "d4_e_occupation_energy", "n_legal_moves",
        "rho", "empty_count",
    ]
    per_delta: dict[str, dict] = {}
    for delta in deltas:
        pairs_X_early: list[list[float]] = []
        pairs_X_late:  list[list[float]] = []
        pairs_targets_early: dict[str, list[float]] = {k: [] for k in all_targets}
        pairs_targets_late:  dict[str, list[float]] = {k: [] for k in all_targets}
        for traj in trajectories:
            for t in range(len(traj) - delta):
                early = traj[t]
                late = traj[t + delta]
                pairs_X_early.append([early[k] for k in SHEAF_FEATURES])
                pairs_X_late.append([late[k]  for k in SHEAF_FEATURES])
                for k in all_targets:
                    pairs_targets_early[k].append(early[k])
                    pairs_targets_late[k].append(late[k])
        n = len(pairs_X_early)
        if n < 20:
            per_delta[f"delta_{delta}"] = {"n_pairs": n}
            continue
        X_early = np.array(pairs_X_early, dtype=float)
        X_late  = np.array(pairs_X_late,  dtype=float)
        mv: dict[str, dict] = {}
        for tk in all_targets:
            y_early = np.array(pairs_targets_early[tk], dtype=float)
            y_late = np.array(pairs_targets_late[tk], dtype=float)
            r2_pred = _ols_r2(y_late, X_early)
            r2_snap = _ols_r2(y_late, X_late)
            r2_pers = _ols_r2(y_late, y_early.reshape(-1, 1))
            mv[tk] = {
                "r2_predictive":    r2_pred,
                "r2_snapshot":      r2_snap,
                "r2_persistence":   r2_pers,
                "gain_vs_persistence": r2_pred - r2_pers,
                "gain_vs_snapshot":    r2_pred - r2_snap,
                "n": int(n),
            }
        per_delta[f"delta_{delta}"] = {
            "n_pairs": int(n),
            "multivariate_r2": mv,
        }
    return per_delta


def run(
    pgn_path: Path, out_json: Path, deltas: list[int],
) -> dict:
    print(f"corpus: {pgn_path}")
    trajectories = pgn_trajectories(pgn_path)
    lengths = [len(t) for t in trajectories]
    print(
        f"built {len(trajectories)} trajectories; mean len "
        f"{np.mean(lengths):.1f}"
    )
    per_delta = analyze(trajectories, deltas)
    summary = {
        "corpus": str(pgn_path),
        "n_trajectories": len(trajectories),
        "sheaf_features": SHEAF_FEATURES,
        "deltas": deltas,
        "per_delta": per_delta,
    }
    out_json.parent.mkdir(parents=True, exist_ok=True)
    with out_json.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    # Stdout summary
    print(f"\n=== Open-5 faithful predictive sheaf ===")
    for delta_key, info in per_delta.items():
        print(f"\n{delta_key}  ({info.get('n_pairs', 0)} pairs)")
        mv = info.get("multivariate_r2", {})
        for tk, v in mv.items():
            print(
                f"  {tk:28s}  R2_pred={v['r2_predictive']:+.4f}  "
                f"R2_snap={v['r2_snapshot']:+.4f}  "
                f"R2_pers={v['r2_persistence']:+.4f}  "
                f"gain_pers={v['gain_vs_persistence']:+.4f}  "
                f"gain_snap={v['gain_vs_snapshot']:+.4f}"
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
        / "phase1e_predictive_sheaf_faithful.json"
    )
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  # Default: Barcelona small corpus.
  python research/phase1e_predictive_sheaf_faithful.py

  # Scale up (background recommended).
  python research/phase1e_predictive_sheaf_faithful.py \\
      --pgn ../dataset/liveothello_2025_all.pgn \\
      --out ../results/phase1e_predictive_sheaf_faithful_2025.json

reading the output:
  Compare gain_vs_persistence to §1e.5b's crude-sheaf results.
  If faithful improves gains (esp. for spectral targets), the
  bracket-aware restrictions carry more predictive content.  If
  kerdim becomes informative (the crude version's constant 128
  was uninformative per §3.4), the non-stationary sheaf signature
  from §1e.5b gains a new coordinate.
""",
    )
    p.add_argument("--pgn", type=Path, default=default_pgn)
    p.add_argument("--out", type=Path, default=default_out)
    p.add_argument(
        "--deltas", type=str, default="1,3,5,10",
        help="Comma-separated ply shifts.  Default: 1,3,5,10.",
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

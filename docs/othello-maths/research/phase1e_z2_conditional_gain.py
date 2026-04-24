"""Exp 2 — Z2-odd vs Z2-even predictive gain, split by side-to-move.

§1e.7.4b found: the faithful sheaf's forward-predictive gain
gain_vs_snap is POSITIVE for Z2-even targets (occupation channels,
rho) but NEGATIVE for Z2-odd magnetisation (A1-).

Hypothesis (D4xZ2 representation-theoretic):
  Our 8 sheaf features are partitioned by OWNER (4 black + 4 white).
  Under Z2 colour inversion, black-owner features swap with white-
  owner features (verified in test_encoder_invariance).  A Z2-odd
  target like A1-(s) has colour polarity - A1-(s after color flip)
  = -A1-(s).

  In the predictive regression (features at t -> target at t+Delta),
  when we pool across all (t, t+Delta) pairs regardless of side-to-
  move, we mix configurations whose Z2-parity is aligned vs
  anti-aligned.  The Z2-odd target's sign flip + the sheaf
  features' Z2-swap creates destructive interference.

  Conditioning the regression on side_to_move(t+Delta) should
  remove the cancellation:
    - fit on subset where side_to_move(t+Delta) == BLACK
    - fit on subset where side_to_move(t+Delta) == WHITE
  Each sub-regression sees a consistent Z2 polarity.  If gain_vs_snap
  becomes positive (or less negative) in each subset, the Z2
  cancellation hypothesis is confirmed.

Runs on Barcelona (small, fast) and WC 2005 (smaller still).
If result is clean on both, extrapolate to 2025.
"""

from __future__ import annotations

__version__ = "0.3.0"

import argparse
import json
import sys
from pathlib import Path

import numpy as np

from othello_utils import BLACK, OthelloBoard
from othello_pgn_loader import (
    _ensure_utf8_stdio, parse_pgn_file, replay,
)
from d4_z2 import project_irrep
from faithful_sheaf import faithful_sheaf_laplacian, spectrum_summary

_ensure_utf8_stdio()


SHEAF_FEATURES = (
    "sheaf_black_lambda2", "sheaf_white_lambda2",
    "sheaf_black_entropy", "sheaf_white_entropy",
    "sheaf_black_kerdim",  "sheaf_white_kerdim",
    "sheaf_black_lambdamax", "sheaf_white_lambdamax",
)


def _a1_minus_energy(sig: np.ndarray) -> float:
    return float(np.linalg.norm(project_irrep(sig, "A1-")) ** 2)


def _a1_minus_signed(sig: np.ndarray, side: int) -> float:
    """Z2-adjusted A1-: if side_to_move is BLACK, take +A1-; if WHITE,
    take -A1-.  Effectively folds out the colour polarity so the
    resulting scalar is Z2-INVARIANT.  If the cancellation hypothesis
    holds, predictive gain on this quantity should be positive."""
    raw = float(np.sum(project_irrep(sig, "A1-")))  # signed sum
    return raw * (1.0 if side == BLACK else -1.0)


def _per_ply(state: np.ndarray, side: int) -> dict:
    L_b = faithful_sheaf_laplacian(state, owner=BLACK)
    sb = spectrum_summary(L_b)
    L_w = faithful_sheaf_laplacian(state, owner=-BLACK)
    sw = spectrum_summary(L_w)
    sig = state.astype(float)
    bb = OthelloBoard()
    bb.state = state.copy()
    bb.side_to_move = side
    return {
        "side_to_move": int(side),
        "sheaf_black_lambda2":   sb["lambda_2"],
        "sheaf_black_entropy":   sb["entropy"],
        "sheaf_black_kerdim":    sb["kernel_dim"],
        "sheaf_black_lambdamax": sb["lambda_max"],
        "sheaf_white_lambda2":   sw["lambda_2"],
        "sheaf_white_entropy":   sw["entropy"],
        "sheaf_white_kerdim":    sw["kernel_dim"],
        "sheaf_white_lambdamax": sw["lambda_max"],
        "a1_minus_energy":    _a1_minus_energy(sig),
        "a1_minus_signed_z2": _a1_minus_signed(sig, side),
        "n_legal_moves":      len(bb.legal_moves()),
    }


def build_trajectories(pgn_path: Path) -> list[list[dict]]:
    games = parse_pgn_file(pgn_path)
    traj = []
    for gi, g in enumerate(games):
        try:
            _, states, move_log = replay(g["moves"])
        except Exception:
            continue
        side = BLACK
        t = []
        for ply, st in enumerate(states):
            if ply > 0:
                side = -move_log[ply - 1]["side"]
            t.append(_per_ply(st, side))
        traj.append(t)
        if (gi + 1) % 20 == 0 or (gi + 1) == len(games):
            print(f"  processed {gi + 1}/{len(games)}", flush=True)
    return traj


def _ols_r2(Y: np.ndarray, X: np.ndarray) -> float:
    if X.size == 0 or X.shape[0] < 5 or np.all(X.std(axis=0) == 0):
        return float("nan")
    X1 = np.concatenate([X, np.ones((len(Y), 1))], axis=1)
    beta, *_ = np.linalg.lstsq(X1, Y, rcond=None)
    resid = Y - X1 @ beta
    ss_res = float(np.sum(resid ** 2))
    ss_tot = float(np.sum((Y - Y.mean()) ** 2))
    return 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0


def analyze(traj: list[list[dict]], deltas: list[int]) -> dict:
    """For each delta, compute gain_vs_snap on three target
    variants:
      - a1_minus_energy (original, Z2-odd target)
      - a1_minus_signed_z2 (Z2-adjusted — multiplied by
         side-to-move sign)
      - n_legal_moves (Z2-invariant control)
    and also conditioned on side_to_move(t+Delta)."""
    targets = ("a1_minus_energy", "a1_minus_signed_z2", "n_legal_moves")
    per_delta: dict = {}
    for delta in deltas:
        pairs_x_early, pairs_x_late = [], []
        tgt_early = {k: [] for k in targets}
        tgt_late = {k: [] for k in targets}
        side_late = []
        for t in traj:
            for i in range(len(t) - delta):
                e = t[i]
                l = t[i + delta]
                pairs_x_early.append([e[k] for k in SHEAF_FEATURES])
                pairs_x_late.append([l[k]  for k in SHEAF_FEATURES])
                for k in targets:
                    tgt_early[k].append(e[k])
                    tgt_late[k].append(l[k])
                side_late.append(l["side_to_move"])
        Xe = np.array(pairs_x_early)
        Xl = np.array(pairs_x_late)
        side_arr = np.array(side_late)
        n = len(Xe)
        delta_out: dict = {"n_pairs": n}
        for tk in targets:
            ye = np.array(tgt_early[tk])
            yl = np.array(tgt_late[tk])
            overall = {
                "r2_pred": _ols_r2(yl, Xe),
                "r2_snap": _ols_r2(yl, Xl),
                "r2_pers": _ols_r2(yl, ye.reshape(-1, 1)),
                "n": int(n),
            }
            overall["gain_vs_snap"] = (
                overall["r2_pred"] - overall["r2_snap"]
            )
            # Conditioned subsets
            cond = {}
            for tag, mask in [
                ("side_late_BLACK", side_arr == BLACK),
                ("side_late_WHITE", side_arr == -BLACK),
            ]:
                n_sub = int(mask.sum())
                if n_sub < 20:
                    cond[tag] = {"n": n_sub, "skipped": True}
                    continue
                r2p = _ols_r2(yl[mask], Xe[mask])
                r2s = _ols_r2(yl[mask], Xl[mask])
                cond[tag] = {
                    "r2_pred": r2p, "r2_snap": r2s,
                    "gain_vs_snap": r2p - r2s,
                    "n": n_sub,
                }
            delta_out[tk] = {
                "overall": overall,
                "conditioned": cond,
            }
        per_delta[f"delta_{delta}"] = delta_out
    return per_delta


def run(pgn_path: Path, out_json: Path, deltas: list[int]) -> dict:
    print(f"corpus: {pgn_path}")
    traj = build_trajectories(pgn_path)
    per_delta = analyze(traj, deltas)
    summary = {
        "corpus": str(pgn_path),
        "n_trajectories": len(traj),
        "sheaf_features": list(SHEAF_FEATURES),
        "deltas": deltas,
        "per_delta": per_delta,
    }
    out_json.parent.mkdir(parents=True, exist_ok=True)
    with out_json.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("\n=== Z2 conditional gain check ===")
    for delta in deltas:
        d = per_delta[f"delta_{delta}"]
        n = d["n_pairs"]
        print(f"\ndelta = {delta}  ({n} pairs)")
        for tk in ("a1_minus_energy", "a1_minus_signed_z2", "n_legal_moves"):
            ov = d[tk]["overall"]
            print(f"  {tk:28s}  overall gain_snap = {ov['gain_vs_snap']:+.4f}  "
                  f"R2_pred={ov['r2_pred']:+.4f}  R2_snap={ov['r2_snap']:+.4f}")
            for cond_tag, sub in d[tk]["conditioned"].items():
                if sub.get("skipped"):
                    continue
                print(f"    {cond_tag:20s}  gain_snap = {sub['gain_vs_snap']:+.4f}  "
                      f"(N={sub['n']})")
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
        / "phase1e_z2_conditional_gain.json"
    )
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--pgn", type=Path, default=default_pgn)
    p.add_argument("--out", type=Path, default=default_out)
    p.add_argument(
        "--deltas", type=str, default="1,3,5,10",
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

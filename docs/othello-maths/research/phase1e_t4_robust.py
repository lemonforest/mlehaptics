"""Follow-up ii — windowed-regression T_eff (robust to |dS|→0 outliers).

Open-2's T4 used finite-difference T_eff = dE / dS per ply, which
explodes when |dS| is near zero and gives heavy-tailed aggregates
(mean +70k, median -11k on Barcelona).

This version fits T_eff via OLS regression over a sliding window of
k consecutive plies:

    within each window of k plies [t, t+k):
      fit    E_tot = beta * S_eff + alpha
      record beta as the window's T_eff
      and window_score = R^2 of the fit

Aggregating T_eff across windows (per game + corpus-wide) is much
less sensitive to individual |dS|=0 transitions; windows that
straddle flat-S_eff regions have low R^2 and can be filtered.

Outputs: results/phase1e_t4_robust_<corpus>.json
"""

from __future__ import annotations

__version__ = "0.2.0"

import argparse
import json
import sys
from pathlib import Path

import numpy as np

from othello_spectral import encode_768, CHANNEL_NAMES
from othello_spectral.encoder import channel_energies
from othello_pgn_loader import (
    _ensure_utf8_stdio, parse_pgn_file, replay,
)

_ensure_utf8_stdio()


def per_ply_ES(enc: np.ndarray) -> tuple[float, float]:
    en = channel_energies(enc)
    vec = np.array([en[c] for c in CHANNEL_NAMES], dtype=np.float64)
    e_tot = float(vec.sum())
    if e_tot > 0:
        p = vec / e_tot
        mask = p > 1e-15
        S = float(-np.sum(p[mask] * np.log(p[mask])))
    else:
        S = 0.0
    return e_tot, S


def windowed_T_eff(
    trajectory: list[np.ndarray], window: int,
) -> list[dict]:
    """Return per-window T_eff fits for one game's trajectory."""
    E_vals = np.array(
        [per_ply_ES(enc)[0] for enc in trajectory], dtype=np.float64,
    )
    S_vals = np.array(
        [per_ply_ES(enc)[1] for enc in trajectory], dtype=np.float64,
    )
    out = []
    for t0 in range(len(trajectory) - window + 1):
        E_w = E_vals[t0:t0 + window]
        S_w = S_vals[t0:t0 + window]
        if S_w.std() < 1e-9:
            out.append({
                "t0": t0, "t_eff": None, "r2": None,
                "E_mean": float(E_w.mean()),
                "S_mean": float(S_w.mean()),
            })
            continue
        # OLS fit E = beta * S + alpha
        X = np.stack([S_w, np.ones_like(S_w)], axis=1)
        coef, *_ = np.linalg.lstsq(X, E_w, rcond=None)
        beta, alpha = float(coef[0]), float(coef[1])
        pred = X @ coef
        resid = E_w - pred
        ss_res = float(np.sum(resid ** 2))
        ss_tot = float(np.sum((E_w - E_w.mean()) ** 2))
        r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
        out.append({
            "t0": t0, "t_eff": beta, "r2": r2,
            "E_mean": float(E_w.mean()),
            "S_mean": float(S_w.mean()),
        })
    return out


def aggregate_corpus(pgn_path: Path, window: int, r2_min: float) -> dict:
    games = parse_pgn_file(pgn_path)
    per_game = []
    all_tvals = []
    all_tvals_filt = []
    for gi, g in enumerate(games):
        try:
            _, states, _ = replay(g["moves"])
        except Exception:
            continue
        traj_enc = [encode_768(st) for st in states]
        windows = windowed_T_eff(traj_enc, window)
        t_vals = [w["t_eff"] for w in windows if w["t_eff"] is not None]
        t_vals_filt = [
            w["t_eff"] for w in windows
            if w["t_eff"] is not None and w["r2"] >= r2_min
        ]
        if t_vals:
            per_game.append({
                "game": gi,
                "headers": {
                    "black": g["headers"].get("Black", ""),
                    "white": g["headers"].get("White", ""),
                    "final": g["headers"].get("FinalScore", ""),
                },
                "n_windows": len(windows),
                "n_valid_windows": len(t_vals),
                "n_high_r2_windows": len(t_vals_filt),
                "t_eff_median":   float(np.median(t_vals)),
                "t_eff_median_high_r2": (
                    float(np.median(t_vals_filt)) if t_vals_filt else None
                ),
            })
            all_tvals.extend(t_vals)
            all_tvals_filt.extend(t_vals_filt)
        if (gi + 1) % 20 == 0 or (gi + 1) == len(games):
            print(f"  processed {gi + 1}/{len(games)} games", flush=True)

    summary = {
        "pgn": str(pgn_path),
        "window": window,
        "r2_min_for_filter": r2_min,
        "n_games": len(per_game),
        "n_windows_total": len(all_tvals),
        "n_high_r2_windows": len(all_tvals_filt),
        "t_eff_all_median": float(np.median(all_tvals)) if all_tvals else None,
        "t_eff_all_iqr": (
            [float(np.percentile(all_tvals, 25)),
             float(np.percentile(all_tvals, 75))]
            if all_tvals else None
        ),
        "t_eff_high_r2_median": (
            float(np.median(all_tvals_filt)) if all_tvals_filt else None
        ),
        "t_eff_high_r2_iqr": (
            [float(np.percentile(all_tvals_filt, 25)),
             float(np.percentile(all_tvals_filt, 75))]
            if all_tvals_filt else None
        ),
        "per_game": per_game,
    }
    return summary


def _build_parser():
    research_dir = Path(__file__).resolve().parent
    default_pgn = (
        research_dir.parent / "dataset"
        / "liveothello_Barcelona_EGP_2026.pgn"
    )
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  python research/phase1e_t4_robust.py --pgn ../dataset/liveothello_World_Championships_2005.pgn

reading the output:
  't_eff_high_r2_median' is the robust headline: median T_eff over
  windows with R^2 >= --r2-min (i.e. windows where E_tot and S_eff
  are actually co-varying, so the slope is meaningful).
  't_eff_all_median' includes noisy-R^2 windows as a comparison.
""",
    )
    p.add_argument("--pgn", type=Path, default=default_pgn)
    p.add_argument(
        "--window", type=int, default=8,
        help="Window length in plies for OLS slope fit.  Default 8.",
    )
    p.add_argument(
        "--r2-min", type=float, default=0.3,
        help="Minimum R^2 for a window to be included in the "
             "'high_r2' aggregate.  Default: 0.3.",
    )
    p.add_argument(
        "--out", type=Path, default=None,
    )
    return p


def main(argv=None):
    args = _build_parser().parse_args(argv)
    out = args.out
    if out is None:
        tag = args.pgn.stem
        out = (
            Path(__file__).resolve().parent.parent / "results"
            / f"phase1e_t4_robust_{tag}.json"
        )
    if not args.pgn.exists():
        print(f"PGN not found: {args.pgn}", file=sys.stderr)
        return 2
    s = aggregate_corpus(args.pgn, args.window, args.r2_min)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        json.dump(s, f, indent=2)
    print(f"\n=== T4 robust (window={args.window}, r2_min={args.r2_min}) ===")
    print(f"  corpus: {args.pgn.name}")
    print(f"  n_games: {s['n_games']}")
    print(f"  n_windows_total: {s['n_windows_total']}")
    print(f"  n_high_r2_windows: {s['n_high_r2_windows']}")
    if s["t_eff_all_median"] is not None:
        print(f"  t_eff all  median = {s['t_eff_all_median']:+.3f}  IQR = {s['t_eff_all_iqr']}")
    if s["t_eff_high_r2_median"] is not None:
        print(f"  t_eff hiR2 median = {s['t_eff_high_r2_median']:+.3f}  IQR = {s['t_eff_high_r2_iqr']}")
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

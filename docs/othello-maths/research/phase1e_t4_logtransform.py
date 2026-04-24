"""Item 5 — T4 log-transform robust estimator.

Open-2 finite-difference T_eff = dE_tot / dS_eff was heavy-tailed
because |dS|→0 blows up.  §1e.7.2 moved to windowed OLS; still
heavy-tailed for short windows.

This runner evaluates log-transform variants of the state variables
to compress the tails:

  variant 'log_E':      fit log(E_tot) = beta * S_eff + alpha
                        beta has units of "fractional energy change
                        per unit of entropy" - robust to absolute
                        scale and to outliers because large dE
                        values get compressed.

  variant 'log_both':   fit log(E_tot) = beta * log(S_eff) + alpha
                        pure log-log regression; beta is the
                        "elasticity" of E with respect to S.

Compared against the raw dE/dS finite-difference baseline.

Outputs: results/phase1e_t4_logtransform_<corpus>.json
"""

from __future__ import annotations

__version__ = "0.2.0"

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

from othello_spectral import encode_768, CHANNEL_NAMES
from othello_spectral.encoder import channel_energies
from othello_pgn_loader import (
    _ensure_utf8_stdio, parse_pgn_file, replay,
)

_ensure_utf8_stdio()


def _per_ply_ES(enc: np.ndarray) -> tuple[float, float]:
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


def _trajectory_ES(states) -> tuple[np.ndarray, np.ndarray]:
    E = np.zeros(len(states))
    S = np.zeros(len(states))
    for i, st in enumerate(states):
        enc = encode_768(st)
        e, s = _per_ply_ES(enc)
        E[i] = e
        S[i] = s
    return E, S


def windowed_fit(
    E: np.ndarray, S: np.ndarray, window: int,
    variant: str,
) -> list[dict]:
    """Slide a window; in each, fit a linear model appropriate to
    the variant and record slope + R²."""
    out = []
    for t0 in range(len(E) - window + 1):
        E_w = E[t0:t0 + window]
        S_w = S[t0:t0 + window]
        if variant == "raw":
            y = E_w; x = S_w
        elif variant == "log_E":
            # Log-transform E only; require E_w > 0 (should always
            # hold for physical energy).
            if np.any(E_w <= 0):
                continue
            y = np.log(E_w); x = S_w
        elif variant == "log_both":
            if np.any(E_w <= 0) or np.any(S_w <= 0):
                continue
            y = np.log(E_w); x = np.log(S_w)
        else:
            raise ValueError(f"unknown variant {variant!r}")
        if x.std() < 1e-9:
            continue
        X = np.stack([x, np.ones_like(x)], axis=1)
        coef, *_ = np.linalg.lstsq(X, y, rcond=None)
        beta, alpha = float(coef[0]), float(coef[1])
        pred = X @ coef
        resid = y - pred
        ss_res = float(np.sum(resid ** 2))
        ss_tot = float(np.sum((y - y.mean()) ** 2))
        r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
        out.append({
            "t0": t0, "slope": beta, "intercept": alpha, "r2": r2,
        })
    return out


def aggregate(
    pgn_path: Path, window: int, r2_min: float, variant: str,
) -> dict:
    games = parse_pgn_file(pgn_path)
    slopes_all, slopes_hi = [], []
    n_games_ok = 0
    for gi, g in enumerate(games):
        try:
            _, states, _ = replay(g["moves"])
        except Exception:
            continue
        n_games_ok += 1
        E, S = _trajectory_ES(states)
        fits = windowed_fit(E, S, window, variant)
        for f in fits:
            slopes_all.append(f["slope"])
            if f["r2"] >= r2_min:
                slopes_hi.append(f["slope"])
        if (gi + 1) % 50 == 0:
            print(f"  processed {gi + 1}/{len(games)} games", flush=True)
    s_all = np.array(slopes_all)
    s_hi = np.array(slopes_hi)
    return {
        "pgn":      str(pgn_path),
        "variant":  variant,
        "window":   window,
        "r2_min":   r2_min,
        "n_games":  n_games_ok,
        "n_windows_total":   int(len(s_all)),
        "n_high_r2_windows": int(len(s_hi)),
        "slope_all": {
            "median": float(np.median(s_all)) if s_all.size else None,
            "iqr": (
                [float(np.percentile(s_all, 25)),
                 float(np.percentile(s_all, 75))]
                if s_all.size else None
            ),
            "mean":  float(s_all.mean()) if s_all.size else None,
            "std":   float(s_all.std()) if s_all.size else None,
        },
        "slope_high_r2": {
            "median": float(np.median(s_hi)) if s_hi.size else None,
            "iqr": (
                [float(np.percentile(s_hi, 25)),
                 float(np.percentile(s_hi, 75))]
                if s_hi.size else None
            ),
            "mean":  float(s_hi.mean()) if s_hi.size else None,
        },
    }


def _build_parser():
    research_dir = Path(__file__).resolve().parent
    default_pgn = (
        research_dir.parent / "dataset"
        / "liveothello_Barcelona_EGP_2026.pgn"
    )
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--pgn", type=Path, default=default_pgn)
    p.add_argument("--window", type=int, default=8)
    p.add_argument("--r2-min", type=float, default=0.3)
    p.add_argument("--out", type=Path, default=None)
    return p


def main(argv=None):
    args = _build_parser().parse_args(argv)
    if not args.pgn.exists():
        print(f"PGN not found: {args.pgn}", file=sys.stderr)
        return 2
    results = {}
    for variant in ("raw", "log_E", "log_both"):
        print(f"\n=== variant = {variant} ===")
        s = aggregate(args.pgn, args.window, args.r2_min, variant)
        results[variant] = s
        sa = s["slope_all"]
        sh = s["slope_high_r2"]
        print(f"  slope_all    median = {sa['median']:+.4e}  IQR = {sa['iqr']}")
        print(f"  slope_hi_r2  median = {sh['median']:+.4e}  IQR = {sh['iqr']}")
    out = args.out
    if out is None:
        tag = args.pgn.stem
        out = (
            Path(__file__).resolve().parent.parent / "results"
            / f"phase1e_t4_logtransform_{tag}.json"
        )
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

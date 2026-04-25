"""Phase 1e.2 — multivariate regression on D4-A1(s^2) + D4-E(s^2).

Section 2d.c of the notebook reports the twin headline channels
D4-A1(s^2) and D4-E(s^2) as near-mirrors with opposite signs
(partial rho = -0.319 and +0.310 vs archive_mean_lb, N = 2587).
They may together carry more signal than either alone; a rotated
single-dim alpha*A1 + beta*E direction might also be stronger than
either individually.

This runner:
  1. Loads phase1d_spectral_vs_perfectplay.csv (already on disk).
  2. Fits OLS archive_mean_lb ~ d4_a1_occ + d4_e_occ (raw + partial
     on |disc_diff|).
  3. Sweeps rotated single-dim cos(t)*A1 + sin(t)*E over a grid of
     angles, finds the direction maximising |spearman(dim, target)|.
  4. Saturated reference: full 5-channel D4 occupation battery
     (Plancherel-sum expectation).
  5. Also the magnetisation-side D4xZ2 '-' battery for parity.

Outputs: results/phase1e_multivariate.json
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr


def _load_csv(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def _float(v) -> float | None:
    if v is None or v == "":
        return None
    try:
        return float(v)
    except ValueError:
        return None


def _residualize(y: np.ndarray, x: np.ndarray) -> np.ndarray:
    """Regress y on x (plus intercept) by OLS and return residuals.
    x has shape (N,) or (N, k)."""
    if x.ndim == 1:
        x = x.reshape(-1, 1)
    X = np.concatenate([x, np.ones((len(y), 1))], axis=1)
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    return y - X @ coef


def _ols_r2(Y: np.ndarray, X: np.ndarray) -> dict:
    """Fit Y = X @ beta + intercept.  Returns {r2, coef, intercept, n}."""
    X1 = np.concatenate([X, np.ones((len(Y), 1))], axis=1)
    beta, *_ = np.linalg.lstsq(X1, Y, rcond=None)
    pred = X1 @ beta
    resid = Y - pred
    ss_res = float(np.sum(resid ** 2))
    ss_tot = float(np.sum((Y - Y.mean()) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    return {
        "r2": r2,
        "coef": beta[:-1].tolist(),
        "intercept": float(beta[-1]),
        "n": int(len(Y)),
    }


def _spearman(x: np.ndarray, y: np.ndarray) -> dict:
    sp = spearmanr(x, y)
    return {"rho": float(sp.statistic), "p": float(sp.pvalue)}


def run(csv_path: Path, out_path: Path) -> dict:
    rows = _load_csv(csv_path)
    keep = [
        r for r in rows
        if _float(r.get("archive_mean_lb")) is not None
    ]
    print(f"loaded {len(rows)} rows, {len(keep)} with archive_mean_lb")

    def col(name):
        return np.array([_float(r[name]) for r in keep], dtype=float)

    A1 = col("d4_a1_occupation_energy")
    A2 = col("d4_a2_occupation_energy")
    B1 = col("d4_b1_occupation_energy")
    B2 = col("d4_b2_occupation_energy")
    E = col("d4_e_occupation_energy")
    A1m = col("a1_minus_energy")
    A2m = col("a2_minus_energy")
    B1m = col("b1_minus_energy")
    B2m = col("b2_minus_energy")
    Em = col("e_minus_energy")
    Y = col("archive_mean_lb")
    DD = np.abs(np.array([
        float(r["disc_diff_player_minus_opp"]) for r in keep
    ], dtype=float))

    result = {
        "csv": str(csv_path),
        "target": "archive_mean_lb",
        "n_positions": len(keep),
    }

    # --- Univariate baselines (raw + partial on |disc_diff|) -------
    univariate = {}
    Yr = _residualize(Y, DD)
    for name, v in [
        ("d4_a1_occ", A1), ("d4_e_occ", E),
        ("d4_a2_occ", A2), ("d4_b1_occ", B1), ("d4_b2_occ", B2),
        ("a1_minus", A1m), ("e_minus", Em),
        ("a2_minus", A2m), ("b1_minus", B1m), ("b2_minus", B2m),
    ]:
        sp = spearmanr(v, Y)
        vr = _residualize(v, DD)
        sp_p = spearmanr(vr, Yr)
        univariate[name] = {
            "raw_rho": float(sp.statistic),
            "raw_p": float(sp.pvalue),
            "partial_rho": float(sp_p.statistic),
            "partial_p": float(sp_p.pvalue),
        }
    result["univariate"] = univariate

    # --- Joint OLS regressions -------------------------------------
    X2 = np.stack([A1, E], axis=1)
    result["joint_a1_e_raw"] = _ols_r2(Y, X2)
    Xr2 = np.stack([
        _residualize(A1, DD), _residualize(E, DD),
    ], axis=1)
    result["joint_a1_e_partial_disc"] = _ols_r2(Yr, Xr2)

    # Full 5-channel D4 occupation battery
    X5 = np.stack([A1, A2, B1, B2, E], axis=1)
    result["joint_d4_5channel_raw"] = _ols_r2(Y, X5)
    Xr5 = np.stack([
        _residualize(v, DD) for v in [A1, A2, B1, B2, E]
    ], axis=1)
    result["joint_d4_5channel_partial_disc"] = _ols_r2(Yr, Xr5)

    # Magnetisation side, for comparison
    X5m = np.stack([A1m, A2m, B1m, B2m, Em], axis=1)
    result["joint_magn_5channel_raw"] = _ols_r2(Y, X5m)

    # All 10 spectral channels + disc count (saturated)
    X10 = np.stack([A1, A2, B1, B2, E, A1m, A2m, B1m, B2m, Em], axis=1)
    result["joint_all10_raw"] = _ols_r2(Y, X10)
    X11 = np.concatenate([X10, DD.reshape(-1, 1)], axis=1)
    result["joint_all10_plus_disc_raw"] = _ols_r2(Y, X11)

    # --- Rotated single-dim sweep in the (A1, E) plane -------------
    # Standardise before rotation so angle is scale-invariant.
    A1s = (A1 - A1.mean()) / (A1.std() or 1.0)
    Es = (E - E.mean()) / (E.std() or 1.0)
    n_angles = 721  # 0.25 deg resolution on [0, 180]
    best_raw = {"rho": 0.0, "angle_deg": None, "p": None}
    best_partial = {"rho": 0.0, "angle_deg": None, "p": None}
    sweep = []
    for k in range(n_angles):
        theta = (np.pi * k) / (n_angles - 1)  # [0, pi]
        angle_deg = 180.0 * k / (n_angles - 1)
        d = np.cos(theta) * A1s + np.sin(theta) * Es
        sp = spearmanr(d, Y)
        dr = _residualize(d, DD)
        sp_p = spearmanr(dr, Yr)
        sweep.append({
            "angle_deg": float(angle_deg),
            "raw_rho": float(sp.statistic),
            "partial_rho": float(sp_p.statistic),
        })
        if abs(sp.statistic) > abs(best_raw["rho"]):
            best_raw = {
                "rho": float(sp.statistic),
                "p": float(sp.pvalue),
                "angle_deg": float(angle_deg),
            }
        if abs(sp_p.statistic) > abs(best_partial["rho"]):
            best_partial = {
                "rho": float(sp_p.statistic),
                "p": float(sp_p.pvalue),
                "angle_deg": float(angle_deg),
            }
    result["rotated_sweep_best_raw"] = best_raw
    result["rotated_sweep_best_partial"] = best_partial

    # Canonical directions
    canonical = {}
    for name, theta_deg in [
        ("a1_only",        0.0),
        ("a1_plus_e_45",  45.0),
        ("e_only",        90.0),
        ("a1_minus_e_135", 135.0),
    ]:
        theta = np.radians(theta_deg)
        d = np.cos(theta) * A1s + np.sin(theta) * Es
        sp = spearmanr(d, Y)
        dr = _residualize(d, DD)
        sp_p = spearmanr(dr, Yr)
        canonical[name] = {
            "angle_deg": theta_deg,
            "raw_rho": float(sp.statistic),
            "raw_p": float(sp.pvalue),
            "partial_rho": float(sp_p.statistic),
            "partial_p": float(sp_p.pvalue),
        }
    result["canonical_directions"] = canonical

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    # Stdout highlights
    print(f"\n=== Phase 1e.2 multivariate highlights (N = {len(keep)}) ===")
    u = univariate
    print("  Univariate (raw / partial) vs archive_mean_lb:")
    for k in ["d4_a1_occ", "d4_e_occ", "d4_a2_occ", "d4_b1_occ",
             "d4_b2_occ", "a1_minus", "e_minus"]:
        r = u[k]
        print(f"    {k:16s}  raw {r['raw_rho']:+.3f}  partial {r['partial_rho']:+.3f}")
    r = result["joint_a1_e_raw"]
    print(f"  Joint (A1+E) raw       R^2 = {r['r2']:+.4f}  coef = [{r['coef'][0]:+.4f}, {r['coef'][1]:+.4f}]")
    r = result["joint_a1_e_partial_disc"]
    print(f"  Joint (A1+E) partial   R^2 = {r['r2']:+.4f}")
    r = result["joint_d4_5channel_raw"]
    print(f"  D4 5-channel raw       R^2 = {r['r2']:+.4f}")
    r = result["joint_d4_5channel_partial_disc"]
    print(f"  D4 5-channel partial   R^2 = {r['r2']:+.4f}")
    r = result["joint_all10_raw"]
    print(f"  All 10 channels raw    R^2 = {r['r2']:+.4f}")
    r = result["joint_all10_plus_disc_raw"]
    print(f"  All 10 + disc raw      R^2 = {r['r2']:+.4f}")
    r = result["rotated_sweep_best_raw"]
    print(f"  Best rotated raw       rho = {r['rho']:+.3f} at angle {r['angle_deg']:.2f} deg")
    r = result["rotated_sweep_best_partial"]
    print(f"  Best rotated partial   rho = {r['rho']:+.3f} at angle {r['angle_deg']:.2f} deg")
    print("  Canonical directions (raw / partial rho):")
    for k, v in result["canonical_directions"].items():
        print(f"    {k:18s}  raw {v['raw_rho']:+.3f}  partial {v['partial_rho']:+.3f}")

    print(f"\nwrote {out_path}")
    return result


def _build_parser():
    default_csv = (
        Path(__file__).resolve().parent.parent / "results"
        / "phase1d_spectral_vs_perfectplay.csv"
    )
    default_out = (
        Path(__file__).resolve().parent.parent / "results"
        / "phase1e_multivariate.json"
    )
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  # Default: load phase1d CSV, compute multivariate regression.
  python research/phase1e_multivariate.py

reading the output:
  'joint_a1_e_partial_disc' R^2 is the headline answer: how much of
  archive_mean_lb variance (after removing |disc_diff|) the two
  channels jointly explain.
  'rotated_sweep_best_partial' finds the single rotated dimension
  cos(t)*A1 + sin(t)*E with max |spearman| vs archive_mean_lb
  (partial).  If its |rho| noticeably exceeds the individual
  channels, a rotated observable is a better univariate summary.
""",
    )
    p.add_argument("--csv", type=Path, default=default_csv)
    p.add_argument("--out", type=Path, default=default_out)
    return p


def main(argv=None):
    args = _build_parser().parse_args(argv)
    if not args.csv.exists():
        print(f"input CSV not found: {args.csv}", file=sys.stderr)
        return 2
    run(args.csv, args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())

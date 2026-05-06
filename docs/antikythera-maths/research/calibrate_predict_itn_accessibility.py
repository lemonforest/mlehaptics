"""Calibrate the §13.9 hybrid-Fiedler-distance → Δv regression.

This is the offline calibration step for the v0.18.1
``bridge.predict_itn_accessibility`` ship surface (research notebook
§13.9.4 / §14.3, task #120). The output is a small set of regression
constants which get hardcoded into
``research/predict_itn_accessibility.py`` (and mirrored to the
``_research/`` ship copy via codegen).

Method
------

1. Load the §13 ground-truth empirical Δv matrix from the SHA1-keyed
   on-disk cache produced by ``gateway_graph_laplacian.py`` (run that
   prototype first if the cache is missing — ~2 min wall-clock).
2. Build the **hybrid** ``inv_dv × resonance`` edge-weighted Laplacian
   on the same 13-body roster (the §13.9 weighting that achieved
   Spearman ρ = +0.857).
3. Compute the hybrid Fiedler eigenvector (with the §13.9 sign
   convention — body of shortest period forced positive — for
   reproducibility).
4. For each unordered pair, compute ``d_F(i, j) = |f₂[i] − f₂[j]|``.
5. Fit a robust regression on the 53 finite empirical pairs:
   * Primary: ordinary least squares ``Δv = a + b · d_F``.
   * Cross-validation: leave-one-out (LOOCV) MAE + R² to detect
     overfitting / single-point dominance.
   * Report: slope ``b``, intercept ``a``, in-sample R², LOOCV MAE,
     median absolute prediction error.

Outputs
-------

* Console: numerical constants ready to paste into
  ``predict_itn_accessibility.CALIBRATION_*`` constants.
* Optional figure ``figures/predict_itn_accessibility_calibration.png``
  showing scatter + fit + residuals.

Notes
-----

The regression is fit on the v0.16.0 13-body heliocentric roster +
50-yr J2000 search window. The calibration is therefore *window-
specific*: applying it outside that window gives a useful prior but
not a guaranteed Δv. The ship module documents this explicitly.

Author: research, task #120 / 2026-05-06.
"""

from __future__ import annotations

import io
import math
import sys
from pathlib import Path
from typing import Tuple

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


# Re-import from the prototype: the hybrid weighting + Fiedler-vector
# helpers are exactly the ones the ship module will use. Re-using
# them here keeps the calibration consistent with what the ship runs.
from ephemerides_spectral._research.bodies import BODIES
from ephemerides_spectral._research.itn_window import (
    _best_rational_approx,
    hohmann_total_dv_kms,
)


# ---- Pinned roster + hyperparameters (must match the §13.9 prototype). ---
HELIOCENTRIC_BODIES = [
    "mercury", "venus", "terra", "mars",
    "jupiter", "saturn", "uranus", "neptune", "pluto",
    "ceres", "vesta", "pallas", "hygiea",
]
EPS_DV_KMS: float = 1.0e-3
RESONANCE_MAX_INT: int = 30
RESONANCE_RESIDUAL_SCALE: float = 5.0e-3
NO_CHAIN_DV_KMS: float = float("inf")

_THIS_DIR = Path(__file__).resolve().parent
_CACHE_DIR = _THIS_DIR / "_cache"
_FIGURES_DIR = _THIS_DIR.parent / "figures"


def _resonance_weight(p_i: float, p_j: float) -> float:
    ratio = min(p_i, p_j) / max(p_i, p_j)
    p, q = _best_rational_approx(ratio, max_int=RESONANCE_MAX_INT)
    if (p, q) == (0, 0):
        return 0.0
    residual = abs(ratio - p / q)
    return math.exp(-residual / RESONANCE_RESIDUAL_SCALE) / float(p + q)


def _hybrid_weight(p_i: float, p_j: float) -> float:
    dv = hohmann_total_dv_kms(p_i, p_j)
    return (1.0 / (dv + EPS_DV_KMS)) * _resonance_weight(p_i, p_j)


def _build_hybrid_laplacian(bodies):
    n = len(bodies)
    W = np.zeros((n, n), dtype=np.float64)
    for i in range(n):
        for j in range(i + 1, n):
            p_i = BODIES[bodies[i]].period_days
            p_j = BODIES[bodies[j]].period_days
            w = _hybrid_weight(p_i, p_j)
            W[i, j] = w
            W[j, i] = w
    D = np.diag(W.sum(axis=1))
    return D - W


def _fiedler_with_sign(L, bodies):
    eigvals, eigvecs = np.linalg.eigh(L)
    lam2 = float(eigvals[1])
    f = eigvecs[:, 1].copy()
    periods = np.array(
        [BODIES[name].period_days for name in bodies], dtype=np.float64
    )
    pivot = int(np.argmin(periods))
    if f[pivot] < 0.0:
        f = -f
    return lam2, f


def _load_cached_obs_dv(bodies) -> np.ndarray:
    """Load the cached §13 ground-truth empirical Δv matrix.

    Cache key matches ``gateway_graph_laplacian._cache_path``: the
    body roster joined by ``|``, then ``|{int(SWEEP_YEARS)}yr|dv{int(DV_BUDGET)}``.
    Hardcoded here as ``50yr|dv30`` to match the §13 prototype run.
    """
    import hashlib
    key = "|".join(bodies) + "|50yr|dv30"
    h = hashlib.sha1(key.encode("utf-8")).hexdigest()[:10]
    cache_path = _CACHE_DIR / f"obs_dv_matrix_{h}.npy"
    if not cache_path.exists():
        raise FileNotFoundError(
            f"Empirical Δv ground-truth cache missing: {cache_path}\n"
            f"Run `python research/gateway_graph_laplacian.py` first to "
            f"populate it (~2 min wall-clock)."
        )
    return np.load(cache_path)


def _ols_linear_fit(x: np.ndarray, y: np.ndarray) -> Tuple[float, float, float]:
    """Ordinary-least-squares y = a + b*x. Returns (a, b, R²)."""
    x_mean = x.mean()
    y_mean = y.mean()
    sxy = float(((x - x_mean) * (y - y_mean)).sum())
    sxx = float(((x - x_mean) ** 2).sum())
    b = sxy / sxx
    a = y_mean - b * x_mean
    y_pred = a + b * x
    ss_res = float(((y - y_pred) ** 2).sum())
    ss_tot = float(((y - y_mean) ** 2).sum())
    r2 = 1.0 - ss_res / ss_tot
    return a, b, r2


def _loocv_mae(x: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
    """Leave-one-out cross-validation MAE + median |error|."""
    n = len(x)
    preds = np.zeros(n)
    for i in range(n):
        mask = np.ones(n, dtype=bool)
        mask[i] = False
        a_i, b_i, _ = _ols_linear_fit(x[mask], y[mask])
        preds[i] = a_i + b_i * x[i]
    err = preds - y
    return float(np.abs(err).mean()), float(np.median(np.abs(err)))


def _emit_calibration_figure(
    fiedler_dist: np.ndarray, obs_dv: np.ndarray,
    finite_mask: np.ndarray, a: float, b: float, r2: float,
    pair_labels,
) -> Path:
    import matplotlib.pyplot as plt

    finite_dist = fiedler_dist[finite_mask]
    finite_dv = obs_dv[finite_mask]
    inf_dist = fiedler_dist[~finite_mask]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

    # Scatter + fit.
    ax1.scatter(finite_dist, finite_dv, c="tab:blue", s=42,
                alpha=0.85, label=f"feasible pairs (n={int(finite_mask.sum())})")
    if (~finite_mask).any():
        # Plot infeasible pairs at top of the y-range as ☉ markers.
        y_top = float(finite_dv.max() * 1.08)
        ax1.scatter(inf_dist, np.full(len(inf_dist), y_top),
                    marker="^", c="tab:red", s=42, alpha=0.6,
                    label=f"no chain in budget (n={int((~finite_mask).sum())})")
    x_line = np.linspace(0.0, fiedler_dist.max() * 1.05, 200)
    ax1.plot(x_line, a + b * x_line, "k-", linewidth=1.5,
             label=f"OLS fit: dv = {a:.2f} + {b:.2f}·d_F  (R² = {r2:.3f})")
    ax1.set_xlabel("hybrid Fiedler distance  d_F(i, j)")
    ax1.set_ylabel("empirical min(total_dv_kms) [km/s]")
    ax1.set_title("v0.18.1 calibration — hybrid Fiedler distance → Δv regression")
    ax1.legend(loc="best", fontsize=9)
    ax1.grid(True, alpha=0.3)

    # Residuals.
    pred = a + b * finite_dist
    resid = finite_dv - pred
    ax2.scatter(pred, resid, c="tab:purple", s=42, alpha=0.85)
    ax2.axhline(0.0, color="black", linewidth=0.8)
    ax2.set_xlabel("predicted Δv [km/s]")
    ax2.set_ylabel("residual (observed − predicted) [km/s]")
    ax2.set_title("residuals  (mean=%.2f, σ=%.2f)" %
                  (float(resid.mean()), float(resid.std())))
    ax2.grid(True, alpha=0.3)

    fig.tight_layout()
    out = _FIGURES_DIR / "predict_itn_accessibility_calibration.png"
    fig.savefig(out, dpi=120)
    plt.close(fig)
    return out


def main() -> int:
    bodies = HELIOCENTRIC_BODIES
    n = len(bodies)
    print(f"# Calibrating predict_itn_accessibility on {n}-body heliocentric roster")
    print(f"# bodies: {bodies}")

    # 1. Hybrid Laplacian → Fiedler eigenvector.
    L = _build_hybrid_laplacian(bodies)
    lam2, fiedler = _fiedler_with_sign(L, bodies)
    print(f"\n[1/4] Hybrid Laplacian λ₂ = {lam2:.4e}")
    print("      Fiedler vector (sign-anchored to mercury+):")
    for i, name in enumerate(bodies):
        print(f"        {name:>10s}  f₂ = {fiedler[i]:+.4f}")

    # 2. Per-pair Fiedler distances + observed Δv.
    import itertools
    pair_idx = list(itertools.combinations(range(n), 2))
    fiedler_dist = np.array([abs(fiedler[i] - fiedler[j]) for i, j in pair_idx])
    obs_dv_matrix = _load_cached_obs_dv(bodies)
    obs_dv = np.array([obs_dv_matrix[i, j] for i, j in pair_idx])
    finite_mask = np.isfinite(obs_dv)
    pair_labels = [f"{bodies[i]}-{bodies[j]}" for i, j in pair_idx]

    # 3. OLS regression + LOOCV.
    print(f"\n[2/4] Regression on n={int(finite_mask.sum())} finite pairs "
          f"(n={int((~finite_mask).sum())} pairs are 'no chain in budget')")
    a, b, r2 = _ols_linear_fit(fiedler_dist[finite_mask], obs_dv[finite_mask])
    loocv_mae, loocv_median_abs = _loocv_mae(
        fiedler_dist[finite_mask], obs_dv[finite_mask]
    )
    in_sample_pred = a + b * fiedler_dist[finite_mask]
    in_sample_mae = float(np.abs(in_sample_pred - obs_dv[finite_mask]).mean())

    print(f"      OLS y = {a:.4f} + {b:.4f} * d_F")
    print(f"      In-sample R² = {r2:.4f}")
    print(f"      In-sample MAE = {in_sample_mae:.3f} km/s")
    print(f"      LOOCV MAE     = {loocv_mae:.3f} km/s")
    print(f"      LOOCV median |error| = {loocv_median_abs:.3f} km/s")

    # 4. Emit figure + paste-ready constants.
    print(f"\n[3/4] Writing calibration figure...")
    fig_path = _emit_calibration_figure(
        fiedler_dist, obs_dv, finite_mask, a, b, r2, pair_labels,
    )
    print(f"      {fig_path}")

    print(f"\n[4/4] Calibration constants (paste into predict_itn_accessibility.py):")
    print("─" * 70)
    print(f"CALIBRATION_INTERCEPT_KMS: float = {a:.6f}")
    print(f"CALIBRATION_SLOPE_KMS_PER_FIEDLER_UNIT: float = {b:.6f}")
    print(f"CALIBRATION_R2: float = {r2:.6f}")
    print(f"CALIBRATION_IN_SAMPLE_MAE_KMS: float = {in_sample_mae:.6f}")
    print(f"CALIBRATION_LOOCV_MAE_KMS: float = {loocv_mae:.6f}")
    print(f"CALIBRATION_N_FINITE_PAIRS: int = {int(finite_mask.sum())}")
    print(f"CALIBRATION_N_INF_PAIRS: int = {int((~finite_mask).sum())}")
    print("─" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())

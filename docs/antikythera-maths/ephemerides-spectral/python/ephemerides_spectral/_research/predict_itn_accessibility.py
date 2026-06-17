"""Predict ITN accessibility — closed-form spectral Δv estimate from
the §13.9 hybrid (inv_dv × resonance) gateway-graph Laplacian.

This is the v0.18.1 ship surface promoted from research notebook §13.9.4.
The §13.9 hybrid edge weighting achieved Spearman ρ = +0.857 against
empirical multi-leg ITN-chain Δv from v0.17.0 ``find_itn_chains`` — strong
enough to support a fast first-pass filter that runs in microseconds
versus ~1.5 s for the full Dijkstra search.

Use case: rank candidate (departure, target) pairs by predicted Δv before
calling the costly ``find_itn_chains`` Dijkstra; or get an O(1) absolute
Δv estimate for a quick mission-design sanity check. **Do not use this
predictor for trajectory design** — its calibration is window-specific
(50 yr at J2000) and its in-sample R² is moderate (~0.51). It is a
prior, not a substitute for the Dijkstra.

Algorithm
---------

1. At module load, build the **hybrid** ``inv_dv × resonance`` edge-
   weighted Laplacian on the v0.16.0 13-body heliocentric Tier-1 roster
   and compute its Fiedler eigenvector (same primitive as
   :mod:`body_architecture` but with hybrid weights).
2. For an input ``(departure, target)`` pair, compute the Fiedler
   distance ``d_F = |f₂[i] - f₂[j]|``.
3. Apply the linear regression calibrated offline against
   ``find_itn_chains`` ground truth (see ``research/
   calibrate_predict_itn_accessibility.py``):

     predicted_dv_kms = INTERCEPT + SLOPE * d_F

The Fiedler-vector sign is anchored to the shortest-period body
(mercury) being positive — same convention as :mod:`body_architecture`
— so the prediction is reproducible across platforms.

Calibration provenance
----------------------

The constants below were fit by ``calibrate_predict_itn_accessibility.py``
on the empirical Δv ground truth from a 50-yr ``find_itn_chains`` sweep
at J2000 (max_legs=3, dv_budget=30, threshold=0.1) — exactly the §13
research-notebook configuration. The 53 feasible pairs (out of 78 in the
13-body roster; 25 infeasible within budget) drive the linear fit.

Calibration quality
-------------------

* In-sample R² ≈ 0.51 (Spearman ρ = +0.857 is much stronger than R² —
  the relationship is monotonic but mildly nonlinear, so a linear OLS
  captures the rank perfectly but fits residuals modestly).
* In-sample MAE ≈ 4.1 km/s; LOOCV MAE ≈ 4.2 km/s (no overfitting; the
  predictor is robust to any single body being held out).
* LOOCV median |error| ≈ 4.1 km/s.

For a Δv domain spanning 2–28 km/s on the calibrated pairs, a 4 km/s
typical absolute error is suitable for **triage** (rank cheap pairs vs
expensive ones) but **not for trajectory design** (the user querying
"what's the Δv to Jupiter?" needs better than ±4 km/s for mission-
budget purposes — they should call ``find_itn_chains`` for that).

References
----------

* Notebook §13.9 — the hybrid-Laplacian research result that motivated
  this ship surface.
* Notebook §14.3 — the holographic-principle framing: this regression
  *is* the bulk-boundary correspondence's "real" empirical payload.
* :mod:`body_architecture` — the v0.18.0 sibling surface (resonance-only
  Fiedler partition; architectural classification).
* :func:`ephemerides_spectral._research.itn_window.find_itn_chains` — the
  ground-truth Dijkstra search this predictor is calibrated against.
"""

from __future__ import annotations

import math
from typing import Dict, List, Tuple

from .bodies import BODIES
from .itn_window import _best_rational_approx, hohmann_total_dv_kms
from . import navigation_ops as _nav


# ---- Default heliocentric subset (same as body_architecture). --------
HELIOCENTRIC_BODIES: List[str] = [
    "mercury", "venus", "terra", "mars",
    "jupiter", "saturn", "uranus", "neptune", "pluto",
    "ceres", "vesta", "pallas", "hygiea",
]

# ---- Resonance-weighting hyperparameters (must match body_architecture
# and the §13.9 prototype for cross-consistency). ----------------------
RESONANCE_MAX_INT: int = 30
RESONANCE_RESIDUAL_SCALE: float = 5.0e-3
EPS_DV_KMS: float = 1.0e-3

# ---- Calibration constants. v0.18.2 upgraded the predictor from a 1-D
# Fiedler-distance regression to a 2-D (f₂, f₃) Euclidean-embedding
# regression. Same Spearman rank correlation as the 1-D fit (ρ ≈ +0.85)
# but ~27 % lower in-sample MAE and a tighter R² (0.51 → 0.64). The
# second eigenvector f₃ adds an axis that distinguishes within-cluster
# pairs that the single Fiedler vector collapsed; the rank ordering is
# unchanged but the absolute Δv prediction is materially more accurate.
#
# Both calibrations fit on the same §13 ground truth (50 yr at J2000,
# max_legs=3, dv_budget=30 km/s, threshold=0.1, 13-body heliocentric
# Tier-1 roster). Production calibration (CALIBRATION_*) is the 2-D
# embedding; the 1-D historical constants are exposed as
# CALIBRATION_*_1D_HISTORICAL for traceability with v0.18.1 callers.
CALIBRATION_EMBEDDING_DIM: int = 2

# 1-D historical (v0.18.1) — kept for back-reference + tests.
CALIBRATION_INTERCEPT_KMS_1D_HISTORICAL: float = 8.680818
CALIBRATION_SLOPE_KMS_PER_FIEDLER_UNIT_1D_HISTORICAL: float = 15.617194
CALIBRATION_R2_1D_HISTORICAL: float = 0.507203
CALIBRATION_IN_SAMPLE_MAE_KMS_1D_HISTORICAL: float = 4.109664
CALIBRATION_LOOCV_MAE_KMS_1D_HISTORICAL: float = 4.237754

# 2-D production (v0.18.2).
CALIBRATION_INTERCEPT_KMS: float = 4.896324
CALIBRATION_SLOPE_KMS_PER_FIEDLER_UNIT: float = 17.319301
CALIBRATION_R2: float = 0.643884
CALIBRATION_IN_SAMPLE_MAE_KMS: float = 2.994717
CALIBRATION_LOOCV_MAE_KMS: float = 3.122645
CALIBRATION_LOOCV_MEDIAN_ABS_ERROR_KMS: float = 2.204213

# Sample sizes (unchanged across 1-D / 2-D — same ground truth).
CALIBRATION_N_FINITE_PAIRS: int = 53
CALIBRATION_N_INF_PAIRS: int = 25
CALIBRATION_SPEARMAN_RHO: float = 0.849
CALIBRATION_WINDOW_YEARS: float = 50.0
CALIBRATION_WINDOW_JD_LO: float = 2451545.0  # J2000.0 (TDB)


def _hybrid_weight(p_i: float, p_j: float) -> float:
    """§13.9 hybrid edge weight: ``(1/(Δv+ε)) * exp(-resid/scale)/(p+q)``."""
    if p_i <= 0.0 or p_j <= 0.0:
        return 0.0
    dv = hohmann_total_dv_kms(p_i, p_j)
    ratio = min(p_i, p_j) / max(p_i, p_j)
    p, q = _best_rational_approx(ratio, max_int=RESONANCE_MAX_INT)
    if (p, q) == (0, 0):
        return 0.0
    residual = abs(ratio - p / q)
    resonance = math.exp(-residual / RESONANCE_RESIDUAL_SCALE) / float(p + q)
    return (1.0 / (dv + EPS_DV_KMS)) * resonance


def _build_hybrid_laplacian(bodies: List[str]):
    """Build the §13.9 hybrid-weighted Laplacian L = D - W on ``bodies``
    via the shared Class-L navigation cascade (:mod:`navigation_ops`,
    numpy-free). Returns an :class:`srmech.amsc.mat.Mat`."""
    n = len(bodies)
    periods = [BODIES[name].period_days for name in bodies]
    edges, weights = _nav.symmetric_pairs_to_edges(
        n, lambda i, j: _hybrid_weight(periods[i], periods[j])
    )
    return _nav.adjacency_to_laplacian(n, edges, weights)


def _eigvecs_2d_with_sign(
    L, bodies: List[str]
) -> Tuple[float, float, List[float], List[float]]:
    """Return (λ₂, λ₃, f₂, f₃) with deterministic sign conventions.

    Routes through the shared Class-L 2-D Fiedler embedding in
    :func:`navigation_ops.fiedler_embedding_2d` (the srmech Jacobi
    solver, numpy-free). f₂: same convention as :mod:`body_architecture`
    — body of shortest period forced to a positive entry. f₃: max-|f₃|
    entry forced positive (no physics-anchor for the third mode). f₂, f₃
    are plain ``list[float]``.
    """
    periods = [BODIES[name].period_days for name in bodies]
    pivot = periods.index(min(periods))
    return _nav.fiedler_embedding_2d(L, pivot)


# Module-level memoised eigendecomposition. The default 13-body roster
# is fixed; we eagerly compute the (f₂, f₃) embedding once at module
# load (microseconds — the Jacobi sweep on a 13×13 symmetric matrix).
# Per-pair lookups are then O(1).
_DEFAULT_LAPLACIAN = _build_hybrid_laplacian(HELIOCENTRIC_BODIES)
(
    _DEFAULT_LAMBDA_2,
    _DEFAULT_LAMBDA_3,
    _DEFAULT_FIEDLER,        # f₂ (list[float])
    _DEFAULT_F3,             # f₃ (list[float])
) = _eigvecs_2d_with_sign(_DEFAULT_LAPLACIAN, HELIOCENTRIC_BODIES)

# 2-D (f₂, f₃) embedding — production v0.18.2 predictor uses this. One
# [f₂[k], f₃[k]] row per body (plain list of pairs; numpy-free).
_DEFAULT_EMBEDDING: List[List[float]] = [
    [_DEFAULT_FIEDLER[k], _DEFAULT_F3[k]]
    for k in range(len(HELIOCENTRIC_BODIES))
]

_DEFAULT_BODY_INDEX: Dict[str, int] = {
    name: idx for idx, name in enumerate(HELIOCENTRIC_BODIES)
}


def predict_itn_accessibility(
    departure: str,
    target: str,
) -> Dict[str, object]:
    """Predict the minimum cumulative Δv for a multi-leg ITN chain.

    Closed-form spectral predictor — uses the v0.18.1 calibration of
    the §13.9 hybrid Fiedler distance against ``find_itn_chains``
    ground truth. Returns an estimated Δv in km/s plus its calibration
    metadata (R², MAE, sample size, etc.) so the caller can decide
    whether the prediction is precise enough for their use case.

    Parameters
    ----------
    departure, target : str
        Body names from the v0.16.0 13-body heliocentric Tier-1
        roster (planets + main-belt asteroids). Case-insensitive.
        Both must be in :data:`HELIOCENTRIC_BODIES`; both must
        differ.

    Returns
    -------
    dict with keys:

    * ``ok`` (bool)
    * ``departure``, ``target`` (str)
    * ``fiedler_distance`` (float) — ``|f₂[i] - f₂[j]|`` on the
      hybrid Laplacian.
    * ``predicted_dv_kms`` (float) — the linear-regression estimate
      ``INTERCEPT + SLOPE * fiedler_distance``.
    * ``calibration`` (dict) — provenance metadata (Spearman ρ, R²,
      MAE, LOOCV MAE, n_finite, n_inf, window).

    On error: ``{"ok": False, "error": "..."}``.

    Notes
    -----
    The predictor is *fast* (microseconds) and *cheap-vs-expensive*
    accurate (Spearman ρ = +0.857) but its absolute MAE is ~4 km/s
    over a 2–28 km/s domain. Use for **triage** ("which pairs are
    cheap to reach?"), not for **mission design** ("what's the exact
    Δv budget for this transfer?"). Mission design should call
    ``bridge.find_itn_chains`` for the full Dijkstra answer.

    The calibration is window-specific (50 yr at J2000, 30 km/s
    Δv budget, max_legs=3, threshold=0.1). For widely different
    search windows — for example, multi-decade outer-system
    missions — re-calibrate by running
    ``research/calibrate_predict_itn_accessibility.py`` against a
    re-sampled ground truth.
    """
    if not isinstance(departure, str) or not isinstance(target, str):
        return {
            "ok": False,
            "error": "departure and target must be strings",
        }
    dep = departure.lower().strip()
    tgt = target.lower().strip()
    if dep == tgt:
        return {
            "ok": False,
            "error": f"departure and target must differ (got {dep!r})",
        }
    if dep not in _DEFAULT_BODY_INDEX:
        return {
            "ok": False,
            "error": (
                f"unknown departure body {departure!r}; valid names are "
                f"{HELIOCENTRIC_BODIES}"
            ),
        }
    if tgt not in _DEFAULT_BODY_INDEX:
        return {
            "ok": False,
            "error": (
                f"unknown target body {target!r}; valid names are "
                f"{HELIOCENTRIC_BODIES}"
            ),
        }

    i = _DEFAULT_BODY_INDEX[dep]
    j = _DEFAULT_BODY_INDEX[tgt]
    # 2-D embedding distance on (f₂, f₃) — the v0.18.2 production
    # predictor (replaces v0.18.1's 1-D |f₂[i] - f₂[j]| distance).
    embedding_i = _DEFAULT_EMBEDDING[i]
    embedding_j = _DEFAULT_EMBEDDING[j]
    d_2d = _nav.euclidean_distance(embedding_i, embedding_j)
    # 1-D Fiedler distance preserved as a returned field (back-compat;
    # callers who pinned the v0.18.1 fiedler_distance value still see
    # the same number).
    d_1d = abs(float(_DEFAULT_FIEDLER[i]) - float(_DEFAULT_FIEDLER[j]))
    predicted = (
        CALIBRATION_INTERCEPT_KMS
        + CALIBRATION_SLOPE_KMS_PER_FIEDLER_UNIT * d_2d
    )

    return {
        "ok": True,
        "departure": dep,
        "target": tgt,
        "fiedler_distance": d_1d,            # 1-D back-compat field
        "embedding_distance_2d": d_2d,       # 2-D production distance
        "predicted_dv_kms": float(predicted),
        "calibration": {
            "method": "OLS linear fit on 2-D (f₂, f₃) hybrid Fiedler embedding",
            "weighting": "hybrid_dv_resonance",
            "embedding_dim": CALIBRATION_EMBEDDING_DIM,
            "intercept_kms": CALIBRATION_INTERCEPT_KMS,
            "slope_kms_per_fiedler_unit": CALIBRATION_SLOPE_KMS_PER_FIEDLER_UNIT,
            "spearman_rho": CALIBRATION_SPEARMAN_RHO,
            "r2": CALIBRATION_R2,
            "in_sample_mae_kms": CALIBRATION_IN_SAMPLE_MAE_KMS,
            "loocv_mae_kms": CALIBRATION_LOOCV_MAE_KMS,
            "loocv_median_abs_error_kms": CALIBRATION_LOOCV_MEDIAN_ABS_ERROR_KMS,
            "n_finite_pairs": CALIBRATION_N_FINITE_PAIRS,
            "n_inf_pairs": CALIBRATION_N_INF_PAIRS,
            "window_years": CALIBRATION_WINDOW_YEARS,
            "window_jd_lo": CALIBRATION_WINDOW_JD_LO,
            "lambda_2": _DEFAULT_LAMBDA_2,
            "lambda_3": _DEFAULT_LAMBDA_3,
        },
    }


__all__ = [
    "HELIOCENTRIC_BODIES",
    "CALIBRATION_INTERCEPT_KMS",
    "CALIBRATION_SLOPE_KMS_PER_FIEDLER_UNIT",
    "CALIBRATION_R2",
    "CALIBRATION_LOOCV_MAE_KMS",
    "CALIBRATION_SPEARMAN_RHO",
    "predict_itn_accessibility",
]

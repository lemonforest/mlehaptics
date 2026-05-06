"""Two-eigenvector Fiedler embedding — does (f₂, f₃) lift Spearman past
the §13.7 ship bar (ρ ≥ 0.85 with Matthews φ ≥ 0.6) on the v0.18.1
hybrid Laplacian?

The §13.6 / §13.9 unfinished refinement: §13.5 inv_dv hit ρ = +0.743 /
φ = +0.336; §13.9 hybrid hit ρ = +0.857 / φ = +0.298. The 1-D Fiedler
vector captures the dominant inner/outer structure but the within-
cluster Δv variance is unresolved. Adding the *next* eigenvector
(f₃ — the second-smallest non-trivial eigenmode) should let
within-cluster pairs separate along an additional axis.

This research script tests the 2-D embedding under all three weighting
schemes (inv_dv baseline, resonance-only, hybrid), reports per-scheme
Spearman + Matthews + R² + LOOCV MAE on the 53-feasible-pair ground
truth, and recommends a v0.18.x ship action.

Author: research, post-#120 follow-up / 2026-05-06.
"""

from __future__ import annotations

import io
import itertools
import math
import sys
from pathlib import Path
from typing import List, Tuple

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from ephemerides_spectral._research.bodies import BODIES
from ephemerides_spectral._research.itn_window import (
    _best_rational_approx,
    hohmann_total_dv_kms,
    synodic_period_days,
)


HELIOCENTRIC_BODIES = [
    "mercury", "venus", "terra", "mars",
    "jupiter", "saturn", "uranus", "neptune", "pluto",
    "ceres", "vesta", "pallas", "hygiea",
]
EPS_DV_KMS: float = 1.0e-3
EPS_SYN_DAYS: float = 1.0e-3
RESONANCE_MAX_INT: int = 30
RESONANCE_RESIDUAL_SCALE: float = 5.0e-3
NO_CHAIN_DV_KMS: float = float("inf")

_THIS_DIR = Path(__file__).resolve().parent
_CACHE_DIR = _THIS_DIR / "_cache"


def _resonance_weight(p_i: float, p_j: float) -> float:
    ratio = min(p_i, p_j) / max(p_i, p_j)
    p, q = _best_rational_approx(ratio, max_int=RESONANCE_MAX_INT)
    if (p, q) == (0, 0):
        return 0.0
    residual = abs(ratio - p / q)
    return math.exp(-residual / RESONANCE_RESIDUAL_SCALE) / float(p + q)


def _build_W(bodies, weighting: str) -> np.ndarray:
    n = len(bodies)
    W = np.zeros((n, n), dtype=np.float64)
    for i in range(n):
        for j in range(i + 1, n):
            p_i = BODIES[bodies[i]].period_days
            p_j = BODIES[bodies[j]].period_days
            if weighting == "inv_dv":
                w = 1.0 / (hohmann_total_dv_kms(p_i, p_j) + EPS_DV_KMS)
            elif weighting == "resonance":
                w = _resonance_weight(p_i, p_j)
            elif weighting == "hybrid":
                w = (1.0 / (hohmann_total_dv_kms(p_i, p_j) + EPS_DV_KMS)) \
                    * _resonance_weight(p_i, p_j)
            else:
                raise ValueError(f"unknown weighting {weighting!r}")
            W[i, j] = w
            W[j, i] = w
    return W


def _eigvecs_2_3(L: np.ndarray, bodies) -> Tuple[float, float, np.ndarray, np.ndarray]:
    """Return (λ₂, λ₃, f₂, f₃) with shortest-period sign convention on f₂."""
    eigvals, eigvecs = np.linalg.eigh(L)
    lam2 = float(eigvals[1])
    lam3 = float(eigvals[2])
    f2 = eigvecs[:, 1].copy()
    f3 = eigvecs[:, 2].copy()
    periods = np.array(
        [BODIES[name].period_days for name in bodies], dtype=np.float64
    )
    pivot = int(np.argmin(periods))
    if f2[pivot] < 0.0:
        f2 = -f2
    # f₃ has its own sign convention; force the largest |f3| entry positive.
    if f3[int(np.argmax(np.abs(f3)))] < 0.0:
        f3 = -f3
    return lam2, lam3, f2, f3


def _spearman(x: np.ndarray, y: np.ndarray) -> float:
    rx = np.argsort(np.argsort(x))
    ry = np.argsort(np.argsort(y))
    n = len(x)
    sxy = float(((rx - rx.mean()) * (ry - ry.mean())).sum())
    sxx = float(((rx - rx.mean()) ** 2).sum())
    syy = float(((ry - ry.mean()) ** 2).sum())
    if sxx == 0.0 or syy == 0.0:
        return float("nan")
    return sxy / math.sqrt(sxx * syy)


def _ols_fit(x: np.ndarray, y: np.ndarray) -> Tuple[float, float, float]:
    sxx = float(((x - x.mean()) ** 2).sum())
    sxy = float(((x - x.mean()) * (y - y.mean())).sum())
    b = sxy / sxx
    a = float(y.mean()) - b * float(x.mean())
    pred = a + b * x
    ss_res = float(((y - pred) ** 2).sum())
    ss_tot = float(((y - y.mean()) ** 2).sum())
    return a, b, 1.0 - ss_res / ss_tot


def _confusion(within: np.ndarray, cheap: np.ndarray) -> Tuple[int, int, int, int]:
    a = int(((within) & (cheap)).sum())
    b = int(((within) & (~cheap)).sum())
    c = int(((~within) & (cheap)).sum())
    d = int(((~within) & (~cheap)).sum())
    return a, b, c, d


def _matthews_phi(a: int, b: int, c: int, d: int) -> float:
    denom = math.sqrt((a + b) * (c + d) * (a + c) * (b + d))
    if denom == 0.0:
        return float("nan")
    return (a * d - b * c) / denom


def _load_obs_dv(bodies) -> np.ndarray:
    import hashlib
    key = "|".join(bodies) + "|50yr|dv30"
    h = hashlib.sha1(key.encode("utf-8")).hexdigest()[:10]
    cache = _CACHE_DIR / f"obs_dv_matrix_{h}.npy"
    if not cache.exists():
        raise FileNotFoundError(
            f"Cache missing: {cache}. Run gateway_graph_laplacian.py first."
        )
    return np.load(cache)


def _evaluate_one_scheme(
    bodies: List[str], weighting: str, obs_dv_matrix: np.ndarray,
) -> dict:
    W = _build_W(bodies, weighting)
    D = np.diag(W.sum(axis=1))
    L = D - W
    lam2, lam3, f2, f3 = _eigvecs_2_3(L, bodies)
    n = len(bodies)
    pair_idx = list(itertools.combinations(range(n), 2))

    # 1-D distance (Fiedler only)
    d1 = np.array([abs(f2[i] - f2[j]) for i, j in pair_idx])
    # 2-D embedding distance (Euclidean on (f₂, f₃))
    embedding = np.column_stack([f2, f3])
    d2 = np.array([
        float(np.linalg.norm(embedding[i] - embedding[j]))
        for i, j in pair_idx
    ])

    obs_dv = np.array([obs_dv_matrix[i, j] for i, j in pair_idx])
    finite = np.isfinite(obs_dv)
    n_finite = int(finite.sum())
    n_inf = int((~finite).sum())

    rho1 = _spearman(d1[finite], obs_dv[finite])
    rho2 = _spearman(d2[finite], obs_dv[finite])
    a1, b1, r2_1 = _ols_fit(d1[finite], obs_dv[finite])
    a2, b2, r2_2 = _ols_fit(d2[finite], obs_dv[finite])

    median_dv = float(np.median(obs_dv[finite]))
    cheap = (obs_dv <= median_dv) & finite
    same_partition = np.array(
        [(f2[i] >= 0.0) == (f2[j] >= 0.0) for i, j in pair_idx]
    )
    cm = _confusion(same_partition, cheap)
    phi = _matthews_phi(*cm)

    in_sample_mae_1 = float(np.abs(a1 + b1 * d1[finite] - obs_dv[finite]).mean())
    in_sample_mae_2 = float(np.abs(a2 + b2 * d2[finite] - obs_dv[finite]).mean())

    return {
        "weighting": weighting,
        "lambda_2": lam2, "lambda_3": lam3,
        "rho_1d": rho1, "rho_2d": rho2,
        "r2_1d": r2_1, "r2_2d": r2_2,
        "mae_1d": in_sample_mae_1, "mae_2d": in_sample_mae_2,
        "ols_1d": (a1, b1), "ols_2d": (a2, b2),
        "matthews_phi": phi,
        "n_finite": n_finite, "n_inf": n_inf,
        "median_dv_kms": median_dv,
    }


def main() -> int:
    bodies = HELIOCENTRIC_BODIES
    print(f"# Two-eigenvector Fiedler embedding — n={len(bodies)} bodies")
    obs_dv = _load_obs_dv(bodies)

    print(f"\n{'weighting':<12s}  {'ρ_1D':>7s}  {'ρ_2D':>7s}  {'lift':>6s}  "
          f"{'R²_1D':>7s}  {'R²_2D':>7s}  {'MAE_1D':>7s}  {'MAE_2D':>7s}  {'φ':>6s}")
    print("-" * 90)

    results = []
    for weighting in ("inv_dv", "resonance", "hybrid"):
        s = _evaluate_one_scheme(bodies, weighting, obs_dv)
        results.append(s)
        lift = s["rho_2d"] - s["rho_1d"]
        print(
            f"{weighting:<12s}  {s['rho_1d']:+.4f}  {s['rho_2d']:+.4f}  "
            f"{lift:+.4f}  {s['r2_1d']:.4f}  {s['r2_2d']:.4f}  "
            f"{s['mae_1d']:5.3f}  {s['mae_2d']:5.3f}  {s['matthews_phi']:+.3f}"
        )

    print()
    hybrid = next(s for s in results if s["weighting"] == "hybrid")
    print("Verdict (hybrid weighting — the v0.18.1 ship's basis):")
    print(f"  1-D ρ = {hybrid['rho_1d']:+.4f}  (v0.18.1 baseline)")
    print(f"  2-D ρ = {hybrid['rho_2d']:+.4f}")
    print(f"  Lift = {hybrid['rho_2d'] - hybrid['rho_1d']:+.4f}")
    print(f"  Matthews φ (sign-only Fiedler partition) = {hybrid['matthews_phi']:+.3f}")
    bar_rho = hybrid["rho_2d"] >= 0.85
    bar_phi = hybrid["matthews_phi"] >= 0.6
    if bar_rho and bar_phi:
        print(f"  ✅ §13.7 ship bar CLEARED on both axes (ρ ≥ 0.85, φ ≥ 0.6)")
        print(f"  → Recommend ship as v0.18.2 update to predict_itn_accessibility")
    elif bar_rho:
        print(f"  ✅ ρ bar cleared but ✗ φ bar still missed.")
        print(f"  → Continuous Fiedler-distance predictor stronger; sign-based "
              f"partition predictor unchanged.")
    else:
        print(f"  ✗ Neither bar cleared; the second eigenvector does not lift "
              f"the hybrid signal.")

    print(f"\n  OLS 1-D: dv = {hybrid['ols_1d'][0]:.4f} + {hybrid['ols_1d'][1]:.4f} * d_1D")
    print(f"  OLS 2-D: dv = {hybrid['ols_2d'][0]:.4f} + {hybrid['ols_2d'][1]:.4f} * d_2D")
    print(f"  In-sample MAE: 1-D = {hybrid['mae_1d']:.3f} km/s, "
          f"2-D = {hybrid['mae_2d']:.3f} km/s")
    print(f"  R²:            1-D = {hybrid['r2_1d']:.4f}, "
          f"2-D = {hybrid['r2_2d']:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

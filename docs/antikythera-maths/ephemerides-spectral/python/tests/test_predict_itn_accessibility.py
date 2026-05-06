"""v0.18.1 — predict_itn_accessibility (closed-form spectral Δv estimate).

The §13.9 hybrid Fiedler-distance regression promoted to a stable
ship surface. Tests pin:

* Calibration constants haven't drifted (slope, intercept, R²,
  LOOCV MAE — these are the v0.18.1 ship contract).
* Predictions are direction-symmetric (the underlying Fiedler
  distance is symmetric in (i, j); ``predict(i, j) == predict(j, i)``
  modulo float).
* Sanity ranking: cheap pairs have smaller predicted Δv than
  expensive pairs (Earth-Mars < Earth-Jupiter < Mercury-Pluto).
* Predictions are non-negative (intercept + slope * d_F is always
  positive on the calibrated roster — the smallest d_F gives the
  intercept ≈ 8.68 km/s, the largest gives the maximum range).
* Bridge surface (smoke + rejection paths for self-transfer / unknown
  body / non-string inputs).
* CLI surface (basic + --help).
* Calibration metadata is exposed in the bridge response so callers
  can decide whether the prediction is precise enough.
"""

from __future__ import annotations

import pytest

from ephemerides_spectral import bridge
from ephemerides_spectral._research.predict_itn_accessibility import (
    CALIBRATION_INTERCEPT_KMS,
    CALIBRATION_LOOCV_MAE_KMS,
    CALIBRATION_R2,
    CALIBRATION_SLOPE_KMS_PER_FIEDLER_UNIT,
    CALIBRATION_SPEARMAN_RHO,
    HELIOCENTRIC_BODIES,
    predict_itn_accessibility,
)


# ──────────────────────────────────────────────────────────────────────
# Calibration contract — pinned at v0.18.1 ship
# ──────────────────────────────────────────────────────────────────────

def test_calibration_intercept_pinned() -> None:
    """Intercept matches the v0.18.1 OLS fit on the §13 ground truth."""
    assert abs(CALIBRATION_INTERCEPT_KMS - 8.680818) < 1e-5


def test_calibration_slope_pinned() -> None:
    """Slope matches the v0.18.1 OLS fit on the §13 ground truth."""
    assert abs(CALIBRATION_SLOPE_KMS_PER_FIEDLER_UNIT - 15.617194) < 1e-5


def test_calibration_r2_pinned() -> None:
    """In-sample R² matches the v0.18.1 fit (within float tolerance)."""
    assert abs(CALIBRATION_R2 - 0.507203) < 1e-5


def test_calibration_loocv_mae_pinned() -> None:
    """LOOCV MAE matches the v0.18.1 fit."""
    assert abs(CALIBRATION_LOOCV_MAE_KMS - 4.237754) < 1e-3


def test_calibration_spearman_pinned() -> None:
    """Headline Spearman ρ from §13.9 = +0.857."""
    assert abs(CALIBRATION_SPEARMAN_RHO - 0.857) < 1e-3


# ──────────────────────────────────────────────────────────────────────
# Pythonic API — predict_itn_accessibility
# ──────────────────────────────────────────────────────────────────────

def test_default_pair_returns_ok() -> None:
    r = predict_itn_accessibility("terra", "mars")
    assert r["ok"] is True
    assert r["departure"] == "terra"
    assert r["target"] == "mars"
    assert "fiedler_distance" in r
    assert "predicted_dv_kms" in r
    assert "calibration" in r


def test_predicted_dv_is_non_negative_for_all_pairs() -> None:
    """Every (departure, target) pair on the default roster yields
    a non-negative Δv prediction. The intercept is +8.68 km/s and
    slope + d_F are non-negative, so this is a structural pin."""
    for i in HELIOCENTRIC_BODIES:
        for j in HELIOCENTRIC_BODIES:
            if i == j:
                continue
            r = predict_itn_accessibility(i, j)
            assert r["ok"] is True
            assert r["predicted_dv_kms"] >= 0.0, (
                f"{i} -> {j}: predicted_dv_kms = "
                f"{r['predicted_dv_kms']} (negative!)"
            )


def test_prediction_is_direction_symmetric() -> None:
    """Fiedler distance is symmetric in (i, j); prediction must be too."""
    for i, j in [("terra", "mars"), ("jupiter", "saturn"),
                 ("mercury", "pluto"), ("ceres", "neptune")]:
        r1 = predict_itn_accessibility(i, j)
        r2 = predict_itn_accessibility(j, i)
        assert abs(r1["fiedler_distance"] - r2["fiedler_distance"]) < 1e-12
        assert abs(r1["predicted_dv_kms"] - r2["predicted_dv_kms"]) < 1e-12


def test_sanity_cheap_to_expensive_ordering() -> None:
    """Cheap pairs predict smaller Δv than expensive pairs.

    Anchor expectations (modulo MAE ≈ 4 km/s):
      Earth-Mars < Earth-Jupiter < Mercury-Pluto

    These are pinned in §13.9 (Mars/Jupiter are inner-cluster + near-
    cluster respectively; Mercury-Pluto is the cross-cluster extremum).
    """
    em = predict_itn_accessibility("terra", "mars")["predicted_dv_kms"]
    ej = predict_itn_accessibility("terra", "jupiter")["predicted_dv_kms"]
    mp = predict_itn_accessibility("mercury", "pluto")["predicted_dv_kms"]
    assert em < ej, f"Earth-Mars ({em}) ≥ Earth-Jupiter ({ej})"
    assert ej < mp, f"Earth-Jupiter ({ej}) ≥ Mercury-Pluto ({mp})"


def test_intercept_is_lower_bound_predict() -> None:
    """The intercept is the minimum-possible prediction (when d_F = 0
    — but d_F > 0 for distinct bodies, so the actual minimum prediction
    on any real pair is intercept + slope * min_d_F > intercept)."""
    min_pred = float("inf")
    for i in HELIOCENTRIC_BODIES:
        for j in HELIOCENTRIC_BODIES:
            if i == j:
                continue
            r = predict_itn_accessibility(i, j)
            min_pred = min(min_pred, r["predicted_dv_kms"])
    assert min_pred >= CALIBRATION_INTERCEPT_KMS - 1e-9


def test_calibration_metadata_in_response() -> None:
    """Every prediction returns the calibration provenance so the
    caller can decide whether the prediction is precise enough."""
    r = predict_itn_accessibility("terra", "mars")
    assert "calibration" in r
    cal = r["calibration"]
    for key in (
        "method", "weighting", "intercept_kms", "slope_kms_per_fiedler_unit",
        "spearman_rho", "r2", "in_sample_mae_kms", "loocv_mae_kms",
        "n_finite_pairs", "n_inf_pairs", "window_years", "window_jd_lo",
        "lambda_2",
    ):
        assert key in cal, f"calibration response missing {key!r}"
    assert cal["weighting"] == "hybrid_dv_resonance"
    assert cal["spearman_rho"] > 0.85


# ──────────────────────────────────────────────────────────────────────
# Pythonic API — error paths
# ──────────────────────────────────────────────────────────────────────

def test_rejects_self_transfer() -> None:
    r = predict_itn_accessibility("terra", "terra")
    assert r["ok"] is False
    assert "differ" in r["error"].lower()


def test_rejects_unknown_departure() -> None:
    r = predict_itn_accessibility("krypton", "mars")
    assert r["ok"] is False
    assert "unknown departure" in r["error"].lower()


def test_rejects_unknown_target() -> None:
    r = predict_itn_accessibility("terra", "krypton")
    assert r["ok"] is False
    assert "unknown target" in r["error"].lower()


def test_rejects_non_heliocentric() -> None:
    """Bodies in the wider 52-body roster (e.g. moons, the Sun) are
    not in the 13-body heliocentric default — rejected as unknown."""
    r = predict_itn_accessibility("luna", "mars")
    assert r["ok"] is False
    r2 = predict_itn_accessibility("terra", "io")
    assert r2["ok"] is False


def test_rejects_non_string_input() -> None:
    r = predict_itn_accessibility(None, "mars")  # type: ignore[arg-type]
    assert r["ok"] is False
    r2 = predict_itn_accessibility("terra", 42)  # type: ignore[arg-type]
    assert r2["ok"] is False


def test_case_insensitive() -> None:
    r = predict_itn_accessibility("TERRA", "Mars")
    assert r["ok"] is True
    assert r["departure"] == "terra"
    assert r["target"] == "mars"


# ──────────────────────────────────────────────────────────────────────
# Bridge surface
# ──────────────────────────────────────────────────────────────────────

def test_bridge_smoke() -> None:
    r = bridge.predict_itn_accessibility("terra", "jupiter")
    assert r["ok"] is True
    assert r["predicted_dv_kms"] > 0.0
    assert r["calibration"]["weighting"] == "hybrid_dv_resonance"


def test_bridge_rejects_self_transfer() -> None:
    r = bridge.predict_itn_accessibility("terra", "terra")
    assert r["ok"] is False


def test_bridge_rejects_unknown_body() -> None:
    r = bridge.predict_itn_accessibility("terra", "krypton")
    assert r["ok"] is False


# ──────────────────────────────────────────────────────────────────────
# CLI surface
# ──────────────────────────────────────────────────────────────────────

def test_cli_predict_basic() -> None:
    import io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main([
            "predict-itn-accessibility",
            "--departure", "terra", "--target", "jupiter",
        ])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["ok"] is True
    assert payload["departure"] == "terra"
    assert payload["target"] == "jupiter"
    assert payload["predicted_dv_kms"] > 0.0


def test_cli_predict_help() -> None:
    """predict-itn-accessibility --help renders without error."""
    from ephemerides_spectral.cli import main as cli_main

    with pytest.raises(SystemExit) as exc_info:
        cli_main(["predict-itn-accessibility", "--help"])
    assert exc_info.value.code == 0

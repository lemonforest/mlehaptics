"""Forward-sweep drift diagnostic — antikythera-spectral reconstruction vs JPL DE441.

Spike question (user, 2026-05-14):
    "If we sweep with the antikythera-spectral package over our now time that
    we have record data, we can see drift. Maybe it's linear, maybe it's
    exponential, maybe it's an epicycle-looking wobble across the entire
    solar system from incorrect harmonic/resonant structure."

This script implements the diagnostic by:

  (1) Using each planet's `synodic_period_relation` from `astronomical_cycles`
      (numerator / denominator → mechanism_days_per_synodic_cycle).
  (2) Computing the bronze "predicted synodic phase" at JD t as
          phase_pred(t) = 360 * (t - REFERENCE_JD) / mechanism_days_per_cycle
      i.e. PURE UNIFORM MEAN MOTION, which is what the encode_ant.py
      pipeline does (verified by audit — Cycle objects carry only
      numerator/denominator, no eccentricity / no atan2 / no pin-slot).
  (3) Computing the actual synodic phase from JPL DE441:
          phase_true(t) = (lambda_planet(t) - lambda_sun(t)) mod 360
      using skyfield + DE441 kernel (staged on disk).
  (4) Residual = wrap_signed(phase_pred - phase_true) mod ±180.
  (5) For each planet, classifying the residual shape:
        - linear (constant rate of error)
        - sinusoidal at the planet's anomalistic frequency
        - higher-order structure (chirp, beat, none-of-the-above)

Outputs:
    docs/srmech/notes/spike_pinslot_findings_q_drift_sweep_<planet>_2026-05-14.ndjson
    docs/srmech/notes/spike_pinslot_findings_q_drift_sweep_summary_2026-05-14.ndjson

Run:
    cd D:/GitHub/mlehaptics/docs/antikythera-maths
    python ../srmech/notes/spike_pinslot_drift_sweep_2026-05-14.py
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

_HERE = Path(__file__).resolve().parent
_ANTIK_ROOT = _HERE.parents[1] / "antikythera-maths"
sys.path.insert(0, str(_ANTIK_ROOT / "antikythera-spectral" / "python"))

from antikythera_spectral._research.astronomical_cycles import CYCLES  # noqa: E402
from antikythera_spectral._research.encode_ant import REFERENCE_JD  # noqa: E402
from antikythera_spectral._research.ephemeris_loader import load_ephemeris  # noqa: E402


# ---------------------------------------------------------------------------
# Per-planet config
# ---------------------------------------------------------------------------

# Per-planet config. Sidereal periods from NASA planetary fact sheet
# (the "year" entry, days). Modern e is mean orbital eccentricity, used
# only to compute the LEADING first-inequality amplitude prediction
# (2*e in radians, doubling per Greek convention).
#
# The bronze encoder treats each planetary dial as uniform mean motion.
# We compare bronze heliocentric longitude prediction (uniform on the
# sidereal period) to DE441 truth. The residual's spectral content is
# the diagnostic: a sinusoid at the planet's anomalistic period is the
# first-inequality miss; a linear secular drift is a period-rate error
# in the encoder.
PLANETS = {
    "Mercury": {
        "cycle_name": "Mercury_synodic_period_relation",
        "kernel_body": "MERCURY BARYCENTER",
        "modern_e": 0.2056,
        "sidereal_period_days": 87.969,         # heliocentric orbital period
        "anomalistic_period_days": 87.969,      # ≈ sidereal at small precession
        "predicted_peak_deg_leading": math.degrees(2 * 0.2056),  # ~23.6
    },
    "Venus": {
        "cycle_name": "Venus_synodic_period_relation",
        "kernel_body": "VENUS BARYCENTER",
        "modern_e": 0.00678,
        "sidereal_period_days": 224.701,
        "anomalistic_period_days": 224.701,
        "predicted_peak_deg_leading": math.degrees(2 * 0.00678),  # ~0.78
    },
    "Mars": {
        "cycle_name": "Mars_synodic_period_relation",
        "kernel_body": "MARS BARYCENTER",
        "modern_e": 0.0934,
        "sidereal_period_days": 686.980,
        "anomalistic_period_days": 686.971,
        "predicted_peak_deg_leading": math.degrees(2 * 0.0934),  # ~10.7
    },
    "Jupiter": {
        "cycle_name": "Jupiter_synodic_period_relation",
        "kernel_body": "JUPITER BARYCENTER",
        "modern_e": 0.0484,
        "sidereal_period_days": 4332.589,
        "anomalistic_period_days": 4332.589,
        "predicted_peak_deg_leading": math.degrees(2 * 0.0484),  # ~5.55
    },
    "Saturn": {
        "cycle_name": "Saturn_synodic_period_relation",
        "kernel_body": "SATURN BARYCENTER",
        "modern_e": 0.0539,
        "sidereal_period_days": 10759.22,
        "anomalistic_period_days": 10759.22,
        "predicted_peak_deg_leading": math.degrees(2 * 0.0539),  # ~6.18
    },
}


def _wrap_signed(x: float) -> float:
    """Wrap to [-180, 180]."""
    return ((x + 180.0) % 360.0) - 180.0


def _unwrap_deg(seq: np.ndarray) -> np.ndarray:
    """Unwrap a sequence of signed-wrapped degrees so jumps > 180 are removed.

    Same algorithm as numpy.unwrap but for degrees. Returns a continuous
    sequence that may exceed [-180, 180] but reveals secular drift +
    oscillatory structure without wrap-induced saturation.
    """
    out = seq.copy().astype(np.float64)
    for i in range(1, len(out)):
        diff = out[i] - out[i - 1]
        if diff > 180.0:
            out[i:] -= 360.0
        elif diff < -180.0:
            out[i:] += 360.0
    return out


def _cycle_by_name(name: str):
    for c in CYCLES:
        if c.name == name:
            return c
    raise KeyError(name)


def _bronze_helio_longitude(jd: float, sidereal_period_days: float,
                            epoch_offset_deg: float = 0.0) -> float:
    """Bronze's predicted heliocentric ecliptic longitude (uniform mean motion).

    The encode_ant.py encoder treats each dial as pure uniform-rate
    phase. For a planet on its sidereal period this is:
        lambda_helio(t) = epoch_offset + 360 * (t - REF) / sidereal_period_days
    Returns degrees in [0, 360).
    """
    elapsed = jd - REFERENCE_JD
    return (epoch_offset_deg + 360.0 * elapsed / sidereal_period_days) % 360.0


def _true_helio_longitude(bundle, jd_tdb: float, planet_key: str) -> float:
    """JPL DE441 heliocentric ecliptic longitude of the planet (deg, [0, 360))."""
    eph = bundle.eph
    ts = bundle.ts
    t = ts.tdb_jd(jd_tdb)
    sun = eph["SUN"]
    planet = eph[planet_key]
    astro = sun.at(t).observe(planet)
    _, lon, _ = astro.ecliptic_latlon()
    return math.degrees(lon.radians) % 360.0


def _calibrate_offset(bundle, planet_name: str, planet_cfg,
                      sidereal_period_days: float) -> float:
    """Pick the bronze epoch offset so the model matches truth at REFERENCE_JD.

    Without calibration the bronze starts with an arbitrary offset relative
    to truth. To diagnose drift SHAPE (linear vs sinusoidal vs ...) we
    want the residual to start near zero so secular and oscillatory
    components are visible against a zero baseline.
    """
    truth_at_ref = _true_helio_longitude(bundle, REFERENCE_JD, planet_cfg["kernel_body"])
    bronze_zero = _bronze_helio_longitude(REFERENCE_JD, sidereal_period_days,
                                          epoch_offset_deg=0.0)
    return (truth_at_ref - bronze_zero) % 360.0


# ---------------------------------------------------------------------------
# Residual shape classifier
# ---------------------------------------------------------------------------

def _classify_residual(t: np.ndarray, r: np.ndarray, planet_cfg) -> Dict:
    """Classify residual shape: linear, sinusoidal-at-anomalistic, or other.

    Method:
      (1) Detrend linearly (least-squares); record slope (deg/yr) and
          fraction of variance explained by the line.
      (2) Fit a single sinusoid at the planet's anomalistic frequency
          (period from planet_cfg) to the detrended residual; record
          amplitude (deg) and explained variance.
      (3) Compute residual-of-residual amplitude (peak abs) after
          both the line + sinusoid are subtracted.

    Returns a dict suitable for one NDJSON record per planet per window.
    """
    # (1) Linear detrend
    A_lin = np.column_stack([t, np.ones_like(t)])
    slope, intercept = np.linalg.lstsq(A_lin, r, rcond=None)[0]
    r_line = slope * t + intercept
    r_after_line = r - r_line
    var_total = np.var(r)
    var_line_explained = max(0.0, 1.0 - np.var(r_after_line) / var_total) if var_total > 0 else 0.0

    # (2) Sinusoidal fit at anomalistic frequency on the line-detrended residual
    period_days = planet_cfg["anomalistic_period_days"]
    omega = 2 * math.pi / period_days  # rad/day
    A_sin = np.column_stack([np.sin(omega * t), np.cos(omega * t)])
    sin_coeffs, *_ = np.linalg.lstsq(A_sin, r_after_line, rcond=None)
    amp_sin = math.sqrt(sin_coeffs[0] ** 2 + sin_coeffs[1] ** 2)
    phase_sin = math.atan2(sin_coeffs[1], sin_coeffs[0])
    r_sin_fit = A_sin @ sin_coeffs
    r_after_sinusoid = r_after_line - r_sin_fit
    var_after_line = np.var(r_after_line)
    var_sin_explained = (
        max(0.0, 1.0 - np.var(r_after_sinusoid) / var_after_line)
        if var_after_line > 0 else 0.0
    )

    # (3) Residual-of-residual peak (what's left unexplained)
    peak_residual_unexplained = float(np.max(np.abs(r_after_sinusoid)))
    peak_residual_total = float(np.max(np.abs(r)))

    # Classification heuristic
    if var_line_explained > 0.9 and var_sin_explained < 0.3:
        kind = "linear"
    elif var_sin_explained > 0.5 and var_sin_explained > var_line_explained:
        kind = "epicyclic-at-anomalistic"
    elif var_line_explained > 0.5 and var_sin_explained > 0.3:
        kind = "linear+epicyclic"
    elif (var_line_explained + var_sin_explained) > 0.5:
        kind = "mixed-(linear+epicyclic)-partial"
    else:
        kind = "other-(neither-dominates)"

    return {
        "slope_deg_per_year": float(slope * 365.25),
        "intercept_deg": float(intercept),
        "variance_explained_by_linear": float(var_line_explained),
        "sinusoid_period_days": float(period_days),
        "sinusoid_amplitude_deg": float(amp_sin),
        "sinusoid_phase_rad": float(phase_sin),
        "variance_explained_by_sinusoid": float(var_sin_explained),
        "peak_residual_total_deg": peak_residual_total,
        "peak_residual_after_line_plus_sin_deg": peak_residual_unexplained,
        "classification": kind,
    }


# ---------------------------------------------------------------------------
# Main sweep
# ---------------------------------------------------------------------------

def _emit_ndjson(records: List[Dict], path: Path) -> None:
    """Write list of dicts as NDJSON (one record per line)."""
    with path.open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, separators=(",", ":")) + "\n")


def main() -> int:
    bundle = load_ephemeris("de441")
    if bundle is None:
        print("ERROR: DE441 kernel not loadable", file=sys.stderr)
        return 1
    print(f"Loaded DE441; running drift-sweep against {len(PLANETS)} planets")

    out_dir = _HERE
    summary_records: List[Dict] = []

    # Two sweep windows:
    # (A) Recent decade 2015-2025 (CE) — JD 2457023.5 to 2460676.5 (~10 yr).
    #     Dense cadence to resolve each planet's anomalistic period (the
    #     diagnostic-frequency for the first-inequality miss).
    # (B) Long sweep -205 BCE to 2026 CE — JD ~1684595 (REFERENCE_JD)
    #     to 2461000 (~2026-01-01). Dense enough to resolve Mercury and
    #     Mars anomalistic periods (~88 and ~687 days).
    # Cadences chosen so the inner-planet anomalistic frequency is
    # well above the Nyquist limit.
    windows = [
        {
            "name": "recent_decade",
            "jd_start": 2457023.5,
            "jd_end":   2460676.5,
            "n_samples": 730,    # ~5 day cadence (Mercury res: 17 samples/cycle)
        },
        {
            "name": "bronze_to_today",
            "jd_start": REFERENCE_JD,
            "jd_end":   2461000.0,
            "n_samples": 8000,   # ~97 day cadence (Mercury res: ~0.9 cyc; aliases,
                                  # but Venus, Mars, Jupiter, Saturn well-resolved)
        },
    ]

    for window in windows:
        t_jd = np.linspace(window["jd_start"], window["jd_end"], window["n_samples"])
        t_days_from_ref = t_jd - REFERENCE_JD
        print(f"\n=== Window: {window['name']} "
              f"(JD {window['jd_start']:.1f} to {window['jd_end']:.1f}, "
              f"{window['n_samples']} samples) ===")

        for planet_name, planet_cfg in PLANETS.items():
            cycle = _cycle_by_name(planet_cfg["cycle_name"])
            sidereal_period_days = planet_cfg["sidereal_period_days"]

            # Calibrate offset at REFERENCE_JD so residual starts near zero
            offset_deg = _calibrate_offset(
                bundle, planet_name, planet_cfg, sidereal_period_days
            )

            # Forward sweep — heliocentric longitudes
            bronze_phase = np.array([
                _bronze_helio_longitude(jd, sidereal_period_days, offset_deg)
                for jd in t_jd
            ])
            true_phase = np.array([
                _true_helio_longitude(bundle, jd, planet_cfg["kernel_body"])
                for jd in t_jd
            ])
            # Unwrap each phase sequence INDEPENDENTLY along time. The
            # wrapped (mod 360) sequences have artificial jumps at every
            # orbital-cycle boundary; unwrapping them first gives
            # continuous bronze(t) and truth(t) so that their difference
            # is the continuous residual we want to classify.
            bronze_phase_uw = _unwrap_deg(bronze_phase)
            true_phase_uw   = _unwrap_deg(true_phase)
            residual = bronze_phase_uw - true_phase_uw
            # Anchor: subtract residual at first sample so window starts at 0
            residual = residual - residual[0]
            residual_wrapped = np.array([_wrap_signed(r) for r in residual])

            # Classify shape
            class_info = _classify_residual(t_days_from_ref, residual, planet_cfg)

            # Per-planet per-sample NDJSON output
            per_sample_records = []
            for jd_i, b_i, t_i, r_wrapped_i, r_unwrapped_i in zip(
                t_jd, bronze_phase, true_phase, residual_wrapped, residual
            ):
                per_sample_records.append({
                    "window": window["name"],
                    "planet": planet_name,
                    "jd_tdb": float(jd_i),
                    "years_from_REF": float((jd_i - REFERENCE_JD) / 365.25),
                    "bronze_helio_longitude_deg": float(b_i),
                    "true_helio_longitude_deg": float(t_i),
                    "residual_wrapped_deg": float(r_wrapped_i),
                    "residual_unwrapped_deg": float(r_unwrapped_i),
                })
            per_planet_path = out_dir / (
                f"spike_pinslot_findings_q_drift_sweep_{planet_name.lower()}_{window['name']}_2026-05-14.ndjson"
            )
            _emit_ndjson(per_sample_records, per_planet_path)

            # Summary record
            peak_total = float(np.max(np.abs(residual)))
            mean_abs   = float(np.mean(np.abs(residual)))
            summary = {
                "window": window["name"],
                "planet": planet_name,
                "jd_start": float(window["jd_start"]),
                "jd_end": float(window["jd_end"]),
                "n_samples": int(window["n_samples"]),
                "cycle_name": planet_cfg["cycle_name"],
                "numerator": int(cycle.numerator),
                "denominator": int(cycle.denominator),
                "mechanism_days": float(cycle.mechanism_days),
                "sidereal_period_days": float(sidereal_period_days),
                "calibration_offset_deg": float(offset_deg),
                "peak_abs_residual_deg": peak_total,
                "mean_abs_residual_deg": mean_abs,
                "predicted_first_inequality_peak_deg": float(planet_cfg["predicted_peak_deg_leading"]),
                **class_info,
            }
            summary_records.append(summary)

            print(f"  {planet_name:7s}  peak={peak_total:7.2f}deg  mean={mean_abs:7.2f}deg  "
                  f"class={class_info['classification']:32s}  "
                  f"Lpct={class_info['variance_explained_by_linear']:.2f}  "
                  f"Spct={class_info['variance_explained_by_sinusoid']:.2f}  "
                  f"slope={class_info['slope_deg_per_year']:+.4f}deg/yr  "
                  f"sinAmp={class_info['sinusoid_amplitude_deg']:.2f}deg")

    summary_path = out_dir / "spike_pinslot_findings_q_drift_sweep_summary_2026-05-14.ndjson"
    _emit_ndjson(summary_records, summary_path)
    print(f"\nSummary: {summary_path}")
    print(f"Per-planet windows: {len(summary_records)} records")

    # ---------------------------------------------------------------------
    # Lunar control — the bronze HAS a pin-slot for the moon (the lunar
    # mechanism), and the encoder treats the lunar anomaly cycle as
    # numerator/denominator only. The encoder by itself thus does NOT
    # consume the pin-slot in encode_ant.py. But the project DOES have
    # the pin-slot transform exposed in research/pin_and_slot.py and
    # uses it for D-H1 analyses. We compare bronze (uniform LunarAnomaly
    # phase) to DE441 lunar longitude to see if the lunar dial would
    # show the same first-inequality miss.
    # ---------------------------------------------------------------------
    print("\n=== Lunar control (encoder is also uniform-motion) ===")
    lunar_cycle = _cycle_by_name("LunarAnomaly")
    sidereal_lunar_period = 27.32166  # sidereal lunar period in days
    # Calibrate
    truth_at_ref = _moon_helio_lon_geocentric(bundle, REFERENCE_JD)
    offset_deg = (truth_at_ref - 0.0) % 360.0
    t_jd = np.linspace(2457023.5, 2460676.5, 730)
    bronze = np.array([
        (offset_deg + 360.0 * (jd - REFERENCE_JD) / sidereal_lunar_period) % 360.0
        for jd in t_jd
    ])
    truth = np.array([_moon_helio_lon_geocentric(bundle, jd) for jd in t_jd])
    bronze_uw = _unwrap_deg(bronze)
    truth_uw  = _unwrap_deg(truth)
    residual = bronze_uw - truth_uw
    residual = residual - residual[0]
    moon_cfg = {
        "anomalistic_period_days": 27.55455,
        "predicted_peak_deg_leading": math.degrees(2 * 0.0549),  # ~6.29
    }
    class_info = _classify_residual(t_jd - REFERENCE_JD, residual, moon_cfg)
    peak_total = float(np.max(np.abs(residual)))
    mean_abs   = float(np.mean(np.abs(residual)))
    moon_record = {
        "window": "recent_decade",
        "planet": "Moon (control)",
        "encoder_uses_pin_slot": False,
        "peak_abs_residual_deg": peak_total,
        "mean_abs_residual_deg": mean_abs,
        "predicted_first_inequality_peak_deg": float(moon_cfg["predicted_peak_deg_leading"]),
        **class_info,
    }
    print(f"  Moon     peak={peak_total:7.2f}deg  mean={mean_abs:7.2f}deg  "
          f"class={class_info['classification']:32s}  "
          f"Spct={class_info['variance_explained_by_sinusoid']:.2f}  "
          f"sinAmp={class_info['sinusoid_amplitude_deg']:.2f}deg "
          f"(predicted first-inequality ~{moon_cfg['predicted_peak_deg_leading']:.2f}deg)")

    moon_summary_path = out_dir / "spike_pinslot_findings_q_drift_sweep_moon_control_2026-05-14.ndjson"
    _emit_ndjson([moon_record], moon_summary_path)
    return 0


def _moon_helio_lon_geocentric(bundle, jd_tdb: float) -> float:
    """DE441 Moon geocentric ecliptic longitude in degrees, [0, 360)."""
    eph = bundle.eph
    ts = bundle.ts
    t = ts.tdb_jd(jd_tdb)
    earth = eph["EARTH"]
    moon = eph["MOON"]
    astro = earth.at(t).observe(moon)
    _, lon, _ = astro.ecliptic_latlon()
    return math.degrees(lon.radians) % 360.0


if __name__ == "__main__":
    sys.exit(main())

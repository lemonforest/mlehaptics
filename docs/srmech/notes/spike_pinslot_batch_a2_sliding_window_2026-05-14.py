"""A2 follow-up — Sliding-window phase regression on bronze-to-today residual.

If apsidal-precession recovery is real (not amplitude-weighting artefact), a
sliding-window phi1 fit over the 2100-year baseline should give a STABLE linear
rate per planet, matching the modern inertial apsidal-precession rate in sign
and OOM.

If the apparent rate from the 2-window fit (A2) is dominated by amplitude-
weighting bias, the sliding-window phi1(t) trajectory will NOT be linear; it
will wobble, drift, or have discontinuities that reflect the residual's
amplitude structure (period-relation truncation error), not real apsidal
precession.

This is the diagnostic that turns the A2 null into either:
  (a) confirmed null — phi1(t) trajectory is non-linear / wobbly — bronze
      residual does NOT carry apsidal-precession signal cleanly; F13 stays dead.
  (b) revived finding — phi1(t) is approximately linear with slope matching
      modern apsidal-precession rate — A2 was right at the OOM level, just
      blocked by 2-window methodology; F13 can be revived under sliding-window.

Cost: 22 windows × 5 planets × ~140 samples per Mercury window (smallest case);
modest compute.

Outputs:
  spike_pinslot_findings_q_apsidal_sliding_window_2026-05-14.ndjson
"""

from __future__ import annotations

import json
import math
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

HERE = Path(__file__).resolve().parent
OUT = HERE / "spike_pinslot_findings_q_apsidal_sliding_window_2026-05-14.ndjson"

PLANETS = ["Mercury", "Venus", "Mars", "Jupiter", "Saturn"]
BRONZE_FILE = {
    p: HERE / f"spike_pinslot_findings_q_drift_sweep_{p.lower()}_bronze_to_today_2026-05-14.ndjson"
    for p in PLANETS
}

# Anomalistic periods (days) and modern rates from A2
ANOMALISTIC_DAYS = {
    "Mercury": 87.969,
    "Venus": 224.701,
    "Mars": 686.971,
    "Jupiter": 4332.589,
    "Saturn": 10759.22,
}

DAYS_PER_JULIAN_YEAR = 365.25
RAD_PER_DEG = math.pi / 180.0
DEG_PER_RAD = 1.0 / RAD_PER_DEG
ARCSEC_PER_DEG = 3600.0

REFERENCE_JD = 1684595.0

MODERN_INERTIAL_PERI_RATE_ARCSEC_PER_CENTURY = {
    "Mercury": 570.9,
    "Venus": 41.2,
    "Mars": 1604.5,
    "Jupiter": 7.7,
    "Saturn": 2022.0,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_residual(path: Path) -> tuple[list[float], list[float]]:
    """Load (jd_tdb, residual_unwrapped_deg) from NDJSON file."""
    jds: list[float] = []
    res: list[float] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            rec = json.loads(line)
            jds.append(rec["jd_tdb"])
            res.append(rec["residual_unwrapped_deg"])
    assert len(jds) == len(res), "jd / residual length mismatch"
    assert len(jds) > 0, "no records loaded"
    return jds, res


def fit_amp_phase(t_days: list[float], y_deg: list[float],
                  omega: float, t_ref: float) -> tuple[float, float, float]:
    """Least-squares fit y(t) ≈ A sin(ω(t-t_ref)) + B cos(ω(t-t_ref)) + C.

    Returns (amp_deg, phi_rad, mean_C_deg) such that
        y ≈ amp * sin(ω(t-t_ref) + phi) + mean_C
    """
    n = len(t_days)
    assert n >= 4, f"need >=4 samples for fit; got {n}"

    # Build design matrix columns
    sin_col = [math.sin(omega * (t - t_ref)) for t in t_days]
    cos_col = [math.cos(omega * (t - t_ref)) for t in t_days]

    # Normal equations 3x3
    sxx = sum(s * s for s in sin_col)
    syy = sum(c * c for c in cos_col)
    sxy = sum(s * c for s, c in zip(sin_col, cos_col))
    sx = sum(sin_col)
    sy = sum(cos_col)

    sxr = sum(s * v for s, v in zip(sin_col, y_deg))
    syr = sum(c * v for c, v in zip(cos_col, y_deg))
    sr = sum(y_deg)

    # M @ [A, B, C] = [sxr, syr, sr]
    # M = [[sxx, sxy, sx], [sxy, syy, sy], [sx, sy, n]]
    M = [[sxx, sxy, sx],
         [sxy, syy, sy],
         [sx,  sy,  n]]
    b = [sxr, syr, sr]

    # Solve 3x3 via Cramer (small, numerically OK for residual data)
    def det3(m: list[list[float]]) -> float:
        return (m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1])
                - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
                + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]))

    D = det3(M)
    assert abs(D) > 1e-20, f"singular design matrix; D={D}"

    M_A = [[b[0], M[0][1], M[0][2]],
           [b[1], M[1][1], M[1][2]],
           [b[2], M[2][1], M[2][2]]]
    M_B = [[M[0][0], b[0], M[0][2]],
           [M[1][0], b[1], M[1][2]],
           [M[2][0], b[2], M[2][2]]]
    M_C = [[M[0][0], M[0][1], b[0]],
           [M[1][0], M[1][1], b[1]],
           [M[2][0], M[2][1], b[2]]]

    A = det3(M_A) / D
    B = det3(M_B) / D
    C = det3(M_C) / D

    amp = math.hypot(A, B)
    phi = math.atan2(B, A)
    return amp, phi, C


def linear_regress(xs: list[float], ys: list[float]) -> tuple[float, float, float]:
    """Simple OLS y = slope*x + intercept; return (slope, intercept, r2)."""
    n = len(xs)
    assert n == len(ys) and n >= 2, f"bad regression dims: {n}, {len(ys)}"
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    sxx = sum((x - mean_x) ** 2 for x in xs)
    sxy = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    syy = sum((y - mean_y) ** 2 for y in ys)
    assert sxx > 0, "zero variance in x"
    slope = sxy / sxx
    intercept = mean_y - slope * mean_x
    ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(xs, ys))
    r2 = 1.0 - ss_res / syy if syy > 0 else 0.0
    return slope, intercept, r2


def unwrap_phase(phis: list[float]) -> list[float]:
    """Unwrap a sequence of angles in radians to remove 2π jumps."""
    out = [phis[0]]
    for p in phis[1:]:
        prev = out[-1]
        d = p - prev
        while d > math.pi:
            d -= 2 * math.pi
        while d < -math.pi:
            d += 2 * math.pi
        out.append(prev + d)
    return out


# ---------------------------------------------------------------------------
# Sliding-window analysis
# ---------------------------------------------------------------------------

def analyze_planet(planet: str, records: list[dict]) -> None:
    """Sliding-window phi1 fit and linear regression on phi1(t)."""
    path = BRONZE_FILE[planet]
    jds, res = load_residual(path)

    anom_d = ANOMALISTIC_DAYS[planet]
    omega = 2.0 * math.pi / anom_d  # rad/day

    # Sliding-window choice: 22 windows, each ~100 years wide, stepping ~95 years.
    # For Saturn (anomalistic 10759 d = 29.5 yr), 100-yr window holds ~3.4 cycles —
    # enough for a noisy phi1 fit. For Jupiter (11.9 yr), ~8.4 cycles. Mercury,
    # Venus, Mars: many cycles each. Comfortable.
    JD_START = jds[0]
    JD_END = jds[-1]
    WINDOW_DAYS = 100.0 * DAYS_PER_JULIAN_YEAR
    STEP_DAYS = 95.0 * DAYS_PER_JULIAN_YEAR
    N_WINDOWS = int((JD_END - JD_START - WINDOW_DAYS) / STEP_DAYS) + 1
    assert N_WINDOWS >= 10, f"need >=10 windows; got {N_WINDOWS}"

    phi_records: list[dict] = []

    for w in range(N_WINDOWS):
        start = JD_START + w * STEP_DAYS
        end = start + WINDOW_DAYS
        # Slice samples in window
        idx_lo = next((i for i, jd in enumerate(jds) if jd >= start), None)
        idx_hi = next((i for i, jd in enumerate(jds) if jd >= end), len(jds))
        if idx_lo is None or idx_hi - idx_lo < 8:
            continue
        ts = jds[idx_lo:idx_hi]
        ys = res[idx_lo:idx_hi]
        # Fit amp / phi at the window centre as reference
        t_centre = 0.5 * (start + end)
        amp, phi, mean = fit_amp_phase(ts, ys, omega, t_centre)
        if amp < 0.01:
            # Phase undetermined for near-zero amplitude
            continue
        phi_records.append({
            "window_index": w,
            "jd_centre": t_centre,
            "years_from_REF": (t_centre - REFERENCE_JD) / DAYS_PER_JULIAN_YEAR,
            "n_samples_in_window": len(ts),
            "amp_deg": amp,
            "phi_rad": phi,
            "mean_offset_deg": mean,
        })

    if len(phi_records) < 5:
        records.append({
            "kind": "sliding_window_phi_fit",
            "planet": planet,
            "status": "insufficient_windows",
            "n_windows": len(phi_records),
        })
        return

    # Unwrap phi
    phis_raw = [r["phi_rad"] for r in phi_records]
    phis_unw = unwrap_phase(phis_raw)
    for r, p in zip(phi_records, phis_unw):
        r["phi_unwrapped_rad"] = p

    # Linear regression on (years_from_REF, phi_unwrapped)
    xs = [r["years_from_REF"] for r in phi_records]
    ys = [r["phi_unwrapped_rad"] for r in phi_records]
    slope, intercept, r2 = linear_regress(xs, ys)

    # slope is d(phi)/d(year) in rad/yr.
    # Apsidal advance rate (positive = prograde) = -slope (per the A2 sign convention)
    apsidal_rate_rad_per_yr = -slope
    apsidal_rate_arcsec_per_century = (
        apsidal_rate_rad_per_yr * DEG_PER_RAD * ARCSEC_PER_DEG * 100.0
    )
    modern_inertial = MODERN_INERTIAL_PERI_RATE_ARCSEC_PER_CENTURY[planet]
    ratio = (apsidal_rate_arcsec_per_century / modern_inertial
             if abs(modern_inertial) > 1.0 else float("nan"))

    # Residual after linear fit — measures how non-linear phi1(t) is
    residuals_rad = [y - (slope * x + intercept) for x, y in zip(xs, ys)]
    rms_residual_rad = math.sqrt(sum(r * r for r in residuals_rad) / len(residuals_rad))
    rms_residual_deg = rms_residual_rad * DEG_PER_RAD

    records.append({
        "kind": "sliding_window_summary",
        "planet": planet,
        "n_windows_fit": len(phi_records),
        "window_width_years": 100.0,
        "window_step_years": 95.0,
        "baseline_years": xs[-1] - xs[0],
        "slope_rad_per_yr": slope,
        "intercept_rad": intercept,
        "linear_r2": r2,
        "rms_phi_residual_rad": rms_residual_rad,
        "rms_phi_residual_deg": rms_residual_deg,
        "bronze_apsidal_rate_rad_per_yr": apsidal_rate_rad_per_yr,
        "bronze_apsidal_rate_arcsec_per_century": apsidal_rate_arcsec_per_century,
        "modern_inertial_apsidal_rate_arcsec_per_century": modern_inertial,
        "ratio_bronze_to_modern": ratio,
        "sign_matches_modern": (
            (apsidal_rate_arcsec_per_century > 0) == (modern_inertial > 0)
        ),
        "rate_within_factor_2_of_modern": (
            0.5 < abs(ratio) < 2.0 if math.isfinite(ratio) else False
        ),
        "linear_fit_quality": (
            "linear" if r2 > 0.85 else "wobbly" if r2 > 0.3 else "non-linear"
        ),
    })

    # Append individual window records (sampled)
    for r in phi_records[::max(1, len(phi_records) // 8)]:
        records.append({
            "kind": "sliding_window_sample",
            "planet": planet,
            **r,
        })


def main() -> None:
    records: list[dict] = []
    for planet in PLANETS:
        analyze_planet(planet, records)

    # Final verdict
    summaries = [r for r in records if r.get("kind") == "sliding_window_summary"]
    n_sign_match = sum(1 for s in summaries if s.get("sign_matches_modern"))
    n_within_2x = sum(1 for s in summaries if s.get("rate_within_factor_2_of_modern"))
    n_linear = sum(1 for s in summaries if s.get("linear_fit_quality") == "linear")
    n_total = len(summaries)

    records.append({
        "kind": "verdict_sliding_window",
        "n_planets_analyzed": n_total,
        "n_sign_matches_modern": n_sign_match,
        "n_within_factor_2_of_modern": n_within_2x,
        "n_linear_phi_trajectory": n_linear,
        "summary_table": [
            {
                "planet": s["planet"],
                "rate": s["bronze_apsidal_rate_arcsec_per_century"],
                "modern": s["modern_inertial_apsidal_rate_arcsec_per_century"],
                "ratio": s["ratio_bronze_to_modern"],
                "sign_match": s["sign_matches_modern"],
                "linear_r2": s["linear_r2"],
                "fit_class": s["linear_fit_quality"],
            }
            for s in summaries
        ],
        "interpretation": (
            "If n_sign_matches >= 4 AND n_within_factor_2 >= 3 AND n_linear >= 3, "
            "the sliding-window method RECOVERS apsidal-precession rates from "
            "the bronze residual — F13 lives. If not, the A2 null stands and "
            "the apparent rates in the 2-window fit are amplitude-weighting "
            "artefacts. The sliding-window phi1 trajectory's linearity quality "
            "(R²) is the discriminating diagnostic."
        ),
    })

    with OUT.open("w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"Wrote {len(records)} records to {OUT.name}")
    print(f"Verdict: {n_sign_match}/{n_total} sign matches; "
          f"{n_within_2x}/{n_total} within 2× of modern; "
          f"{n_linear}/{n_total} linear (R²>0.85).")
    for s in summaries:
        print(f"  {s['planet']:8s}: rate {s['bronze_apsidal_rate_arcsec_per_century']:+10.1f} as/cy "
              f"vs modern {s['modern_inertial_apsidal_rate_arcsec_per_century']:+8.1f} as/cy "
              f"(ratio {s['ratio_bronze_to_modern']:+8.2f}, R2={s['linear_r2']:.3f}, "
              f"{s['linear_fit_quality']})")


if __name__ == "__main__":
    main()

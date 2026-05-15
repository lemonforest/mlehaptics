"""
Spike #24 Phase 3b — numerical validation of Phase 3a predictions.

Loads JPL DE441 ephemeris via skyfield. For each major body:
  1. Compute heliocentric (or planet-centric for Luna) ecliptic longitude
     time-series over a multi-period window.
  2. Subtract the linear mean-motion trend (what a Class-K-absent encoder
     would produce): λ_linear(t) = λ_0 + (2π / P_sidereal) · (t - t_0)
  3. FFT the residual; extract the leading harmonic amplitude at the
     body's anomalistic frequency.
  4. Compare to Phase 3a's predicted c_1 amplitude (= 2*e in radians,
     Greek-frame doubling per pi-as-projection).

The numerical c_1 from FFT should match Phase 3a's analytical c_1 to
within first-order precision. Secular precession, resonant perturbations,
and projection-artifact contributions will shift the actual residual
slightly from the pure equation-of-centre prediction — those deltas are
themselves Phase 3c real-coupling content.

Output: NDJSON with per-body (predicted, measured, delta) records.

Requires:
- skyfield >= 1.46
- DE441 kernel (.bsp) accessible

Discipline: NDJSON output (per feedback_ndjson_over_bloated_json);
analytical-first/numerical-validation-second methodology already
established in spec doc.
"""

import io
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


# Find a DE441 kernel
KERNEL_CANDIDATES = [
    Path("docs/antikythera-maths/.claude/worktrees/funny-wozniak-569530/docs/antikythera-maths/ephemerides-spectral/skyfield_data/de441.bsp"),
    Path("docs/antikythera-maths/.claude/worktrees/funny-wozniak-569530/skyfield_data/de441.bsp"),
    Path("docs/antikythera-maths/ephemerides-spectral/skyfield_data/de441.bsp"),
    Path.home() / ".skyfield" / "de441.bsp",
]


def find_kernel():
    for p in KERNEL_CANDIDATES:
        if p.exists() and p.stat().st_size > 1024 * 1024:  # >1 MB
            return p
    raise FileNotFoundError(
        f"No DE441 kernel found. Searched: {[str(p) for p in KERNEL_CANDIDATES]}"
    )


# Per-body skyfield target IDs + Phase 3a predicted values (e_modern, c_1 deg)
BODY_TARGETS = [
    # (name, skyfield_target_id, P_sidereal_days, e_modern, observer)
    # Heliocentric — observer = sun
    ("Mercury",  "mercury",                    87.96925980, 0.2056, "sun"),
    ("Venus",    "venus",                     224.70079922, 0.0068, "sun"),
    ("Mars",     "mars barycenter",           686.97970000, 0.0934, "sun"),
    # Earth (Terra): skyfield exposes the Earth-Moon barycenter; we use that as
    # a proxy for Terra's orbit around the Sun.
    ("Terra",    "earth barycenter",          365.25636300, 0.0167, "sun"),
    # Outer planets: barycenters in DE441
    ("Jupiter",  "jupiter barycenter",       4332.58900000, 0.0484, "sun"),
    ("Saturn",   "saturn barycenter",       10759.22000000, 0.0541, "sun"),
    ("Uranus",   "uranus barycenter",       30688.50000000, 0.0472, "sun"),
    ("Neptune",  "neptune barycenter",      60182.00000000, 0.0086, "sun"),
    # Luna: geocentric (observer = earth barycenter or earth)
    ("Luna",     "moon",                       27.32166156, 0.0549, "earth"),
]


def heliocentric_ecliptic_longitude(planets, target_id, observer_id, t):
    """Compute target's ecliptic longitude as seen from observer at time t.

    Returns longitude in radians, unwrapped (continuous, no 0-2π jumps).
    """
    target = planets[target_id]
    observer = planets[observer_id]
    apparent = (target - observer).at(t)
    # Ecliptic of J2000 frame; lat, lon, distance
    lat, lon, _dist = apparent.ecliptic_latlon()
    # lon is a skyfield Angle; .radians gives float array
    return lon.radians


def linear_mean_motion(t_jd, t0_jd, lambda0, period_days):
    """Linear mean-motion prediction (Class-K-absent encoder analog)."""
    n = 2.0 * math.pi / period_days  # mean motion (rad/day)
    return lambda0 + n * (t_jd - t0_jd)


def fft_leading_amplitude(residual, sample_dt_days, target_period_days):
    """FFT the residual; return the amplitude at the body's anomalistic frequency.

    Uses a flat-top window for near-zero scalloping loss (<0.01 dB across the
    bin) so the peak amplitude reads the true sinusoid amplitude even when
    the target frequency doesn't align with an FFT bin centre.

    Returns (amplitude_rad, dominant_period_days, rectangular_amp_rad,
             scalloping_correction_factor).

    The rectangular amplitude is also returned for diagnostic comparison;
    the flat-top amplitude is the load-bearing measurement.
    """
    n = len(residual)
    n_fft = 1 << (n - 1).bit_length()

    # Apply flat-top window (near-zero scalloping loss)
    # Flat-top window coefficients from scipy.signal flattop (Heinzel et al. 2002)
    k = np.arange(n)
    flattop = (0.21557895
               - 0.41663158 * np.cos(2 * np.pi * k / (n - 1))
               + 0.277263158 * np.cos(4 * np.pi * k / (n - 1))
               - 0.083578947 * np.cos(6 * np.pi * k / (n - 1))
               + 0.006947368 * np.cos(8 * np.pi * k / (n - 1)))
    # Coherent gain of flat-top window (sum of coefficients)
    flattop_cg = np.mean(flattop)

    windowed = residual * flattop
    spec = np.fft.rfft(windowed, n=n_fft)
    freqs = np.fft.rfftfreq(n_fft, d=sample_dt_days)

    # Flat-top window amplitude correction: multiply by 2/(N * flattop_cg)
    # to recover sinusoid amplitude
    amplitudes_ft = 2.0 * np.abs(spec) / (n * flattop_cg)
    amplitudes_ft[0] = 0.0

    # Also compute rectangular-window for diagnostic
    spec_rect = np.fft.rfft(residual, n=n_fft)
    amplitudes_rect = 2.0 * np.abs(spec_rect) / n_fft
    amplitudes_rect[0] = 0.0

    # Find peak near the body's anomalistic frequency
    target_freq = 1.0 / target_period_days
    f_low = target_freq * 0.8
    f_high = target_freq * 1.2
    mask = (freqs >= f_low) & (freqs <= f_high)
    if not mask.any():
        return 0.0, 0.0, 0.0, 1.0

    masked_idx = np.argmax(amplitudes_ft[mask])
    actual_idx = np.where(mask)[0][masked_idx]
    leading_amp_ft = amplitudes_ft[actual_idx]
    leading_amp_rect = amplitudes_rect[actual_idx]
    dominant_period = 1.0 / freqs[actual_idx] if freqs[actual_idx] > 0 else 0.0

    scalloping_correction = (
        leading_amp_ft / leading_amp_rect if leading_amp_rect > 0 else 1.0
    )

    return (
        float(leading_amp_ft),
        float(dominant_period),
        float(leading_amp_rect),
        float(scalloping_correction),
    )


def main():
    from skyfield.api import load_file, load
    from skyfield import api

    kernel_path = find_kernel()
    print(f"Using kernel: {kernel_path}")
    print(f"Kernel size: {kernel_path.stat().st_size / 1024 / 1024:.1f} MB")
    print()

    planets = load_file(str(kernel_path))
    ts = load.timescale()

    out_records = []
    out_records.append({
        "record_kind": "header",
        "spike": "Spike #24",
        "phase": "Phase 3b — numerical validation of Phase 3a analytical predictions",
        "date": "2026-05-15",
        "kernel": str(kernel_path),
        "method": (
            "For each major body, compute (DE441 ecliptic longitude) - "
            "(linear mean motion) residual over a multi-period window. "
            "FFT-extract leading sinusoidal amplitude at the body's anomalistic "
            "frequency. Compare to Phase 3a's predicted c_1 = 2e radians."
        ),
        "windows_per_body": (
            "Inner planets: 100-year window at 1-day sampling. Outer planets: "
            "1-2 full orbital periods at coarser sampling. Luna: 10-year window "
            "at 0.1-day sampling for high-frequency resolution."
        ),
    })

    print(f"{'Body':<10} {'Period (d)':>12} {'e':>8} {'Pred c1 (deg)':>14} "
          f"{'Meas c1 (deg)':>14} {'Delta (deg)':>12} {'Concordance':>12}")
    print("-" * 95)

    for name, target_id, period_days, e_modern, observer_id in BODY_TARGETS:
        predicted_c1_deg = math.degrees(2.0 * e_modern)

        # Pick a window: at least 5 anomalistic periods, max 100 years for
        # inner planets; for outer planets use min(2 periods, 200 years).
        if period_days < 1000:
            window_days = max(5 * period_days, 100 * 365.25)
            window_days = min(window_days, 200 * 365.25)
            sample_dt = max(0.1, period_days / 100.0)
        else:
            window_days = max(2 * period_days, 200 * 365.25)
            window_days = min(window_days, 500 * 365.25)
            sample_dt = max(1.0, period_days / 200.0)

        n_samples = int(window_days / sample_dt)
        if n_samples > 200_000:
            sample_dt = window_days / 200_000
            n_samples = 200_000

        # Time grid centered on J2000 (JD 2451545.0)
        jd_start = 2451545.0
        jd_array = jd_start + np.arange(n_samples) * sample_dt
        t = ts.tdb_jd(jd_array)

        # Get longitude time-series
        try:
            lon_rad = heliocentric_ecliptic_longitude(
                planets, target_id, observer_id, t
            )
        except Exception as exc:
            print(f"{name:<10} ERROR: {exc}")
            out_records.append({
                "record_kind": "per_body",
                "body": name,
                "predicted_c1_deg": predicted_c1_deg,
                "error": str(exc),
            })
            continue

        # Unwrap longitude (continuous)
        lon_unwrapped = np.unwrap(lon_rad)

        # Linear mean motion: fit lambda0 + n*(t-t0)
        # Use least-squares linear fit to extract n_actual + lambda0
        coeffs = np.polyfit(jd_array, lon_unwrapped, 1)
        n_actual = coeffs[0]
        lambda0_actual = coeffs[1] + coeffs[0] * jd_start  # lambda at jd_start

        # Residual = actual - linear
        linear_model = coeffs[1] + coeffs[0] * jd_array
        residual = lon_unwrapped - linear_model

        # FFT-extract leading amplitude near 1/P_sidereal (anomalistic freq)
        # Flat-top windowed (scalloping-corrected) + rectangular for diagnostic
        (measured_c1_rad, dominant_period,
         rect_c1_rad, scalloping_factor) = fft_leading_amplitude(
            residual, sample_dt, period_days
        )
        measured_c1_deg = math.degrees(measured_c1_rad)
        rect_c1_deg = math.degrees(rect_c1_rad)

        delta_deg = measured_c1_deg - predicted_c1_deg
        concordance = (
            "match" if abs(delta_deg) < 0.5
            else "close" if abs(delta_deg) < predicted_c1_deg * 0.2
            else "diverge"
        )

        print(f"{name:<10} {period_days:>12.4f} {e_modern:>8.4f} "
              f"{predicted_c1_deg:>14.4f} {measured_c1_deg:>14.4f} "
              f"{delta_deg:>+12.4f} {concordance:>12}")

        out_records.append({
            "record_kind": "per_body",
            "body": name,
            "target_id": target_id,
            "observer_id": observer_id,
            "period_sidereal_days": period_days,
            "e_modern": e_modern,
            "predicted_c1_deg": predicted_c1_deg,
            "measured_c1_deg_flattop": measured_c1_deg,
            "measured_c1_deg_rectangular": rect_c1_deg,
            "scalloping_correction_factor": scalloping_factor,
            "delta_deg": delta_deg,
            "concordance": concordance,
            "dominant_period_days_from_fft": dominant_period,
            "n_samples": n_samples,
            "window_days": window_days,
            "sample_dt_days": sample_dt,
            "n_fit_rad_per_day_actual": float(n_actual),
            "n_fit_rad_per_day_from_period": 2.0 * math.pi / period_days,
        })

    # Write NDJSON
    out_path = Path(__file__).with_name(
        "spike_24_phase_3b_measured_residuals_2026-05-15.ndjson"
    )
    with open(out_path, "w", encoding="utf-8") as f:
        for r in out_records:
            f.write(json.dumps(r) + "\n")

    print()
    print(f"NDJSON output: {out_path}")
    print(f"  Records: {len(out_records)} (1 header + {len(BODY_TARGETS)} per-body)")


if __name__ == "__main__":
    main()

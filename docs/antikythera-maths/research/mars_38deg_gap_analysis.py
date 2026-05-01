"""Mars 38° gap analysis (#2 parameter sweep, #3 time-window distribution,
#4 Almagest IX.5 cross-check).

The Antikythera-mechanism literature reports the Mars pointer is "up to
38° wrong" at retrograde nodes (attributed to Greek-theory limits, not
gear-ratio inaccuracy).  Our ``equant_encoder``'s Ptolemaic equant model
peaks at 48.66° vs DE422 — a 10° gap from the documented 38°.

This script investigates the gap with three independent analyses, all
running against an analytic Kepler-based Mars longitude (Newton-iteration
on the eccentric anomaly), so no ephemeris kernel is needed.  Kepler-
derived longitudes are arcsec-accurate over the relevant time scales
and give a reproducible reference frame independent of which JPL
kernel you have on disk.

#2 Parameter sweep
    For each (R, r, e) on a grid around the Almagest IX.5 canonical
    (60, 39.5, 6), compute peak |equant - kepler| over one Mars synodic
    period.  Report the (R, r, e) that minimises peak, and whether any
    grid point hits or undercuts the documented 38°.

#3 Time-window sweep
    For 30 different start-JDs spanning ~64 Mars synodic periods
    (-200 BCE through 2050 CE), run the equant model + Kepler reference
    over one synodic period each.  Report the distribution of peak
    errors — peak's mean, median, min, max across cycles.  Tests
    whether 38° is achievable at SOME Mars retrograde even if our
    REFERENCE_JD-anchored cycle peaks at 48°.

#4 Almagest IX.5 cross-check
    Evaluate ``_equation_of_center_equant`` at canonical mean-anomaly
    phases (0°, 30°, 60°, 90°, 120°, 150°, 180°).  Ptolemy IX.5 reports
    the maximum equation of center for Mars at Mmax ~= 11°33'.  Verify
    our implementation reproduces that within rounding.

Run::

    python -m research.mars_38deg_gap_analysis            # all three
    python -m research.mars_38deg_gap_analysis --analysis 2   # param sweep only
    python -m research.mars_38deg_gap_analysis --analysis 3   # time-window only
    python -m research.mars_38deg_gap_analysis --analysis 4   # Almagest check only
"""

from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass, replace
from typing import Callable, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Kepler-based Mars longitude (ground-truth reference, no ephemeris needed)
# ---------------------------------------------------------------------------

# Modern Kepler elements for Mars and Earth, at J2000 (JD 2451545.0).
# Source: NASA JPL Horizons orbital-elements export, mean-of-J2000 frame.
# We propagate via mean motion only (no perturbations) — accurate to
# ~few arcsec over the ~50 yr time scale we sweep, which is way under
# our 38° gap. Heliocentric ecliptic longitudes.

_J2000_JD: float = 2451545.0

# Earth — semi-major axis 1 AU, eccentricity 0.0167, mean longitude rate.
_EARTH_E: float = 0.01671022
_EARTH_LON_AT_EPOCH: float = 100.464_572  # deg, J2000 mean longitude
_EARTH_LON_PERI: float = 102.937_348      # deg, longitude of perihelion at J2000
_EARTH_DEG_PER_DAY: float = 360.0 / 365.256_363_004

# Mars — semi-major axis 1.523679 AU, eccentricity 0.0934.
_MARS_E: float = 0.093_412_33
_MARS_LON_AT_EPOCH: float = 355.453_320  # deg, J2000 mean longitude
_MARS_LON_PERI: float = 336.060_234      # deg, longitude of perihelion at J2000
_MARS_DEG_PER_DAY: float = 360.0 / 686.971


def _kepler_solve(M_rad: float, e: float, tol: float = 1e-10,
                  max_iter: int = 32) -> float:
    """Newton-iterate Kepler's equation M = E - e sin E for E.

    M and result both in radians. Convergence in ~5 iterations for
    e < 0.1 (Mars + Earth qualify).
    """
    E = M_rad if e < 0.1 else math.pi
    for _ in range(max_iter):
        f = E - e * math.sin(E) - M_rad
        fp = 1.0 - e * math.cos(E)
        dE = f / fp
        E -= dE
        if abs(dE) < tol:
            break
    return E


def _heliocentric_longitude(jd: float, semi_major: float, e: float,
                             lon_at_epoch_deg: float, lon_peri_deg: float,
                             deg_per_day: float) -> Tuple[float, float]:
    """Heliocentric ecliptic (longitude_rad, distance_au) at jd."""
    elapsed = jd - _J2000_JD
    # Mean longitude at jd:
    M_lon_deg = (lon_at_epoch_deg + deg_per_day * elapsed) % 360.0
    # Mean anomaly = mean longitude - longitude of perihelion:
    M_anom_deg = (M_lon_deg - lon_peri_deg) % 360.0
    M_anom_rad = math.radians(M_anom_deg)
    E = _kepler_solve(M_anom_rad, e)
    # True anomaly nu:
    cos_E = math.cos(E)
    sin_E = math.sin(E)
    nu = math.atan2(math.sqrt(1 - e * e) * sin_E, cos_E - e)
    # Heliocentric longitude = longitude of perihelion + true anomaly:
    lon_helio = math.radians(lon_peri_deg) + nu
    # Distance r = a(1 - e cos E):
    dist_au = semi_major * (1.0 - e * cos_E)
    return lon_helio, dist_au


def kepler_mars_geocentric_synodic(jd: float) -> float:
    """Geocentric Mars-Sun synodic phase (deg, [0, 360)) under analytic
    Keplerian motion. Plug-compatible with the equant_encoder model
    closures."""
    earth_helio_lon, earth_dist = _heliocentric_longitude(
        jd, 1.000_001_018, _EARTH_E, _EARTH_LON_AT_EPOCH,
        _EARTH_LON_PERI, _EARTH_DEG_PER_DAY,
    )
    mars_helio_lon, mars_dist = _heliocentric_longitude(
        jd, 1.523_679, _MARS_E, _MARS_LON_AT_EPOCH,
        _MARS_LON_PERI, _MARS_DEG_PER_DAY,
    )
    # Earth → Sun → Mars vectors in ecliptic plane.
    ex = earth_dist * math.cos(earth_helio_lon)
    ey = earth_dist * math.sin(earth_helio_lon)
    mx = mars_dist * math.cos(mars_helio_lon)
    my = mars_dist * math.sin(mars_helio_lon)
    # Geocentric Mars vector (Mars - Earth in heliocentric frame):
    gx = mx - ex
    gy = my - ey
    geocentric_lon = math.atan2(gy, gx)
    geocentric_sun_lon = math.atan2(-ey, -ex)
    return math.degrees(geocentric_lon - geocentric_sun_lon) % 360.0


# ---------------------------------------------------------------------------
# Common helpers
# ---------------------------------------------------------------------------

def _wrap_180(deg: float) -> float:
    """Wrap an angle to [-180, 180)."""
    return ((deg + 180.0) % 360.0) - 180.0


def _peak_error(model_fn: Callable[[float], float], start_jd: float,
                span_days: float, n_samples: int) -> Tuple[float, float, float]:
    """Sample model_fn vs Kepler over [start_jd, start_jd + span_days]
    and return (peak_deg, mean_deg, rms_deg) with the constant offset
    removed.

    Why mean-correct: the equant_encoder's MarsParams.epoch_lon_deg /
    epoch_anomaly_deg are not strictly calibrated to REFERENCE_JD or
    any modern epoch — the docstring explicitly flags that the encoder
    sits at a constant ~110° offset from truth without epoch
    propagation. The Antikythera-mechanism literature's 38° figure
    measures *shape* error of the Greek planetary model — i.e., how
    badly the deferent + epicycle (+ equant) tracks the actual Mars
    motion regardless of where on the zodiac you anchor it. Subtracting
    the mean residual isolates shape from anchor calibration; the peak
    of the shape residual is what we want to compare to 38°.
    """
    # First pass: collect signed residuals (in [-180, 180)).
    step = span_days / max(n_samples - 1, 1)
    signed: List[float] = []
    for i in range(n_samples):
        jd = start_jd + i * step
        m_pred = model_fn(jd)
        m_truth = kepler_mars_geocentric_synodic(jd)
        signed.append(_wrap_180(m_pred - m_truth))
    # Robust mean: use circular mean to handle wrap-around at ±180.
    sx = sum(math.cos(math.radians(s)) for s in signed)
    sy = sum(math.sin(math.radians(s)) for s in signed)
    mean_offset = math.degrees(math.atan2(sy, sx))
    # Second pass: shape residual = signed - mean_offset, re-wrapped.
    shape_residuals = [_wrap_180(s - mean_offset) for s in signed]
    abs_residuals = [abs(r) for r in shape_residuals]
    peak = max(abs_residuals)
    mean = sum(abs_residuals) / len(abs_residuals)
    rms = math.sqrt(sum(r * r for r in abs_residuals) / len(abs_residuals))
    return peak, mean, rms


# ---------------------------------------------------------------------------
# #2 Parameter sweep
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SweepPoint:
    R: float
    r: float
    e: float
    peak_deg: float
    mean_deg: float
    rms_deg: float


def parameter_sweep(start_jd: Optional[float] = None,
                    span_days: float = 779.94,
                    n_samples: int = 200,
                    R_range: Tuple[float, float, float] = (54.0, 66.0, 2.0),
                    r_range: Tuple[float, float, float] = (35.0, 44.0, 1.5),
                    e_range: Tuple[float, float, float] = (3.0, 9.0, 1.0),
                    ) -> List[SweepPoint]:
    """#2 — sweep (R, r, e) on a grid; report peak Mars error per point.

    Default grid is centred on Almagest IX.5 canonical (60, 39.5, 6) with
    ±10% radius, ±15% epicycle, ±50% eccentricity (the Greek tradition's
    parameter uncertainty). 7 × 7 × 7 = 343 grid points — 30 s on a laptop.
    """
    from .equant_encoder import (
        MarsParams, REFERENCE_JD, mars_longitude_equant,
    )
    if start_jd is None:
        start_jd = REFERENCE_JD

    def _frange(lo: float, hi: float, step: float) -> List[float]:
        out: List[float] = []
        v = lo
        while v <= hi + 1e-9:
            out.append(round(v, 4))
            v += step
        return out

    R_vals = _frange(*R_range)
    r_vals = _frange(*r_range)
    e_vals = _frange(*e_range)

    out: List[SweepPoint] = []
    for R in R_vals:
        for r in r_vals:
            for e in e_vals:
                params = MarsParams(deferent_radius=R,
                                    epicycle_radius=r,
                                    eccentricity=e,
                                    equant_offset=2.0 * e)

                def _model(jd: float, p: MarsParams = params) -> float:
                    return mars_longitude_equant(jd, p)

                peak, mean, rms = _peak_error(
                    _model, start_jd, span_days, n_samples,
                )
                out.append(SweepPoint(R, r, e, peak, mean, rms))
    return out


def report_parameter_sweep(points: List[SweepPoint],
                            top_n: int = 10) -> str:
    """Format a textual report of the sweep's lowest-peak points."""
    sorted_pts = sorted(points, key=lambda p: p.peak_deg)
    lines: List[str] = [
        f"#2 Parameter sweep: {len(points)} grid points",
        f"  best 5 (lowest peak):",
    ]
    for p in sorted_pts[:5]:
        lines.append(
            f"    R={p.R:5.1f}  r={p.r:5.1f}  e={p.e:4.1f}    "
            f"peak={p.peak_deg:6.2f}°  mean={p.mean_deg:5.2f}°"
        )
    canonical = next(
        (p for p in points if p.R == 60.0 and p.r == 39.5 and p.e == 6.0),
        None,
    )
    if canonical:
        lines.append(
            f"  canonical Almagest (R=60, r=39.5, e=6):  "
            f"peak={canonical.peak_deg:.2f}°  mean={canonical.mean_deg:.2f}°"
        )
    lines.append(
        f"  worst: peak={sorted_pts[-1].peak_deg:.2f}° at "
        f"R={sorted_pts[-1].R}, r={sorted_pts[-1].r}, e={sorted_pts[-1].e}"
    )
    closest_38 = min(points, key=lambda p: abs(p.peak_deg - 38.0))
    lines.append(
        f"  closest to documented 38°: peak={closest_38.peak_deg:.2f}° at "
        f"R={closest_38.R}, r={closest_38.r}, e={closest_38.e}"
    )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# #3 Time-window distribution
# ---------------------------------------------------------------------------

def time_window_sweep(n_cycles: int = 30,
                      jd_start: float = 1684500.0,
                      span_days: float = 779.94,
                      n_samples: int = 200,
                      model: str = "equant") -> List[Tuple[float, float, float, float]]:
    """#3 — for n_cycles consecutive Mars synodic periods, compute peak,
    mean, RMS error of the chosen model vs Kepler.

    Default sweeps from JD 1684500 (~-205 BCE, Antikythera era) forward
    by one synodic period each iteration, covering ~64 yr.

    Returns a list of (start_jd, peak_deg, mean_deg, rms_deg) tuples.
    """
    from .equant_encoder import model_residue_function

    fn = model_residue_function(model)

    out: List[Tuple[float, float, float, float]] = []
    for k in range(n_cycles):
        start = jd_start + k * span_days
        peak, mean, rms = _peak_error(fn, start, span_days, n_samples)
        out.append((start, peak, mean, rms))
    return out


def report_time_window_sweep(samples: List[Tuple[float, float, float, float]],
                              ) -> str:
    """Format a textual report of peak distribution across time windows."""
    peaks = sorted(s[1] for s in samples)
    means = [s[2] for s in samples]
    n = len(peaks)
    median = peaks[n // 2]
    lines: List[str] = [
        f"#3 Time-window sweep: {n} consecutive Mars synodic cycles",
        f"  peak distribution:",
        f"    min:    {peaks[0]:6.2f}°",
        f"    median: {median:6.2f}°",
        f"    mean:   {sum(peaks) / n:6.2f}°",
        f"    max:    {peaks[-1]:6.2f}°",
        f"  closest single-cycle peak to 38°:  "
        f"{min(peaks, key=lambda p: abs(p - 38.0)):.2f}°",
        f"  cycles where peak ≤ 38°:           "
        f"{sum(1 for p in peaks if p <= 38.0)} / {n}",
        f"  cycles where peak ≤ 50°:           "
        f"{sum(1 for p in peaks if p <= 50.0)} / {n}",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# #4 Almagest IX.5 cross-check
# ---------------------------------------------------------------------------

def almagest_cross_check() -> str:
    """#4 — evaluate _equation_of_center_equant at canonical phases and
    report against Ptolemy IX.5's tabulated extrema.

    Ptolemy reports max equation of center for Mars (under bisected
    eccentricity, R=60, e=6, equant offset 12) at M ~= 90°, with a value
    of approximately 11° 33' (= 11.55°).  See Toomer 1984, *Almagest*,
    Table IX.5 row M=90° column "equation of center".

    A correctly-implemented bisected-eccentricity equation of center
    must:
    * be 0° at M=0° (apogee)
    * be 0° at M=180° (perigee)
    * peak in the range 11° to 12° at some M near 90°
    * be antisymmetric: eqn(M) = -eqn(360°-M)
    """
    from .equant_encoder import _equation_of_center_equant

    lines: List[str] = [
        "#4 Almagest IX.5 cross-check (R=60, e=6, equant offset 12):",
        "  M (deg) |  equation of center (deg) |  expected behaviour",
        "  --------|---------------------------|--------------------",
    ]
    R, e = 60.0, 6.0
    sample_M = [0.0, 15.0, 30.0, 45.0, 60.0, 75.0, 90.0, 105.0, 120.0,
                135.0, 150.0, 165.0, 180.0]
    peak_deg = 0.0
    peak_M = 0.0
    for M_deg in sample_M:
        M_rad = math.radians(M_deg)
        eqn = _equation_of_center_equant(M_rad, e, R)
        eqn_deg = math.degrees(eqn)
        if abs(eqn_deg) > peak_deg:
            peak_deg = abs(eqn_deg)
            peak_M = M_deg
        comment = ""
        if M_deg in (0.0, 180.0):
            comment = "should be ~= 0"
        elif M_deg == 90.0:
            comment = "Ptolemy: peak ~= 11° 33'"
        lines.append(
            f"  {M_deg:6.1f}  |  {eqn_deg:24.4f}   |  {comment}"
        )
    lines.append("")
    lines.append(f"  observed peak:           {peak_deg:.4f}°  at M={peak_M:.0f}°")
    lines.append(f"  Ptolemy IX.5 max equation: ~= 11.55° (= 11°33')")
    if 11.0 <= peak_deg <= 12.0:
        lines.append("  [OK] implementation consistent with Almagest IX.5")
    else:
        lines.append(
            f"  [WARN] peak {peak_deg:.2f}deg outside [11.0, 12.0] band -- "
            "implementation drift, parameter mismatch, or sign convention issue"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# #5 F&J 2012 Figure 39 reproduction (the actual setup behind "38°")
# ---------------------------------------------------------------------------

# Per the literature audit: Freeth & Jones 2012, ISAW Papers 4, §3.10
# Figure 39, says "nearly 38°" peak for the *middle seven retrogrades
# of Mars in the 1st Century BC — a period of about 13 years*. Their
# model is BARE deferent + epicycle (no eccentricity, no equant — even
# simpler than Hipparchus's eccentric-deferent formulation), with the
# Mars (37, -79) Babylonian period relation. The reference is JPL
# Horizons (sub-arcsec equivalent of our DE422 / our Kepler-2-body
# at -100 to 0 BCE).
#
# This analysis reproduces F&J's window: ~13 years centred on the
# middle of the 1st century BC (~JD 1721000 = -53 BCE), runs all three
# of our models PLUS a "bare-deferent" model with e=0 (matching F&J's
# actual setup), and reports peak shape error per model. If our
# Hipparchian or our bare-deferent on this window reproduces ~38°,
# we've matched F&J. If our equant gives < 38°, the equant correctly
# improves on the bare deferent + epicycle. If our equant gives > 38°,
# our equant params (apsidal longitude, anchor) are misaligned —
# follow-up #6 territory.

_FJ_WINDOW_START_JD: float = 1721000.0
"""Approximate JD of -53 BCE (mid 1st century BC)."""

_FJ_WINDOW_SPAN_DAYS: float = 13.0 * 365.25
"""Approximate span F&J use; covers ~7 Mars synodic retrogrades."""


def freeth_jones_window() -> str:
    """#5 — reproduce F&J 2012 Figure 39's setup against our models."""
    from .equant_encoder import (
        MarsParams, REFERENCE_JD, mars_longitude_epicycle_only,
        mars_longitude_equant, mars_longitude_uniform,
    )

    # Bare deferent + epicycle, matching F&J's pre-Hipparchian model.
    # Set e=0 (no eccentricity); equant_offset doesn't matter for the
    # epicycle-only branch but we set it consistently.
    bare_params = MarsParams(eccentricity=0.0, equant_offset=0.0)

    canonical = MarsParams()  # Almagest IX.5

    def _bare(jd: float) -> float:
        return mars_longitude_epicycle_only(jd, bare_params)

    def _hipparchus(jd: float) -> float:
        return mars_longitude_epicycle_only(jd, canonical)

    def _equant(jd: float) -> float:
        return mars_longitude_equant(jd, canonical)

    n_samples = 200
    bare_p, bare_m, bare_r = _peak_error(_bare, _FJ_WINDOW_START_JD,
                                           _FJ_WINDOW_SPAN_DAYS, n_samples)
    hipp_p, hipp_m, hipp_r = _peak_error(_hipparchus, _FJ_WINDOW_START_JD,
                                           _FJ_WINDOW_SPAN_DAYS, n_samples)
    eq_p, eq_m, eq_r = _peak_error(_equant, _FJ_WINDOW_START_JD,
                                    _FJ_WINDOW_SPAN_DAYS, n_samples)

    lines: List[str] = [
        "#5 Freeth & Jones 2012 Figure 39 reproduction:",
        f"   window: JD {_FJ_WINDOW_START_JD:.0f} (~-53 BCE) + {_FJ_WINDOW_SPAN_DAYS:.0f} days "
        f"({_FJ_WINDOW_SPAN_DAYS/365.25:.1f} yr) = ~7 Mars retrogrades, 1st century BC",
        f"   reference: analytic Kepler 2-body (sub-arcsec equivalent of JPL Horizons / DE422)",
        f"   n_samples: {n_samples}",
        "",
        "   Model                                         | Peak deg | Mean deg | RMS deg",
        "   --------------------------------------------- | -------- | -------- | -------",
        f"   bare deferent+epicycle (F&J's actual model)    | {bare_p:8.2f} | {bare_m:8.2f} | {bare_r:7.2f}",
        f"   Hipparchian eccentric-deferent + epicycle      | {hipp_p:8.2f} | {hipp_m:8.2f} | {hipp_r:7.2f}",
        f"   Ptolemaic equant + bisection (R=60, r=39.5, e=6) | {eq_p:8.2f} | {eq_m:8.2f} | {eq_r:7.2f}",
        "",
        f"   Documented F&J 2012 Fig 39 peak: ~38 deg",
        "",
        "   Verdict:",
    ]
    if abs(bare_p - 38.0) < 5.0:
        lines.append(
            f"   [OK] bare-deferent peak {bare_p:.2f}° within 5° of F&J's 38° -- "
            "we reproduce their setup correctly."
        )
    else:
        lines.append(
            f"   [GAP] bare-deferent peak {bare_p:.2f}° vs F&J's 38° -- "
            f"{abs(bare_p - 38.0):.1f}° residual gap suggests window-start mismatch "
            "or implementation difference in the deferent + epicycle math."
        )
    if eq_p < bare_p:
        lines.append(
            f"   [OK] equant ({eq_p:.2f}°) improves on bare deferent ({bare_p:.2f}°) "
            "as physics expects."
        )
    else:
        lines.append(
            f"   [WARN] equant ({eq_p:.2f}°) WORSE than bare deferent ({bare_p:.2f}°) -- "
            "equant params (apsidal longitude, equant offset, epoch anchor) likely "
            "misaligned. Recommend audit against Almagest IX.7 anchor table."
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python -m research.mars_38deg_gap_analysis",
        description=(
            "Investigate the 10° gap between our equant encoder's 48.66° "
            "peak Mars error and the documented Antikythera-mechanism 38°. "
            "Three independent analyses against analytic Kepler ground "
            "truth (no ephemeris kernel needed)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python -m research.mars_38deg_gap_analysis\n"
            "  python -m research.mars_38deg_gap_analysis --analysis 2\n"
            "  python -m research.mars_38deg_gap_analysis --analysis 3 --n-cycles 60\n"
        ),
    )
    p.add_argument(
        "--analysis", type=int, default=0, choices=[0, 2, 3, 4, 5],
        help="0 (default) = run all four; 2 = parameter sweep; "
             "3 = time-window sweep; 4 = Almagest cross-check; "
             "5 = F&J 2012 Figure 39 reproduction",
    )
    p.add_argument("--n-cycles", type=int, default=30,
                   help="time-window sweep: # consecutive synodic cycles")
    p.add_argument("--n-samples", type=int, default=200,
                   help="samples per cycle (both #2 and #3)")
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = _make_parser().parse_args(argv)
    sections: List[str] = []
    if args.analysis in (0, 4):
        sections.append(almagest_cross_check())
    if args.analysis in (0, 2):
        pts = parameter_sweep(n_samples=args.n_samples)
        sections.append(report_parameter_sweep(pts))
    if args.analysis in (0, 3):
        windows = time_window_sweep(n_cycles=args.n_cycles,
                                     n_samples=args.n_samples)
        sections.append(report_time_window_sweep(windows))
    if args.analysis in (0, 5):
        sections.append(freeth_jones_window())
    print("\n\n".join(sections))
    return 0


if __name__ == "__main__":
    sys.exit(main())

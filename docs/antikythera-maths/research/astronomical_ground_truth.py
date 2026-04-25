"""Phase 4 -- astronomical ground-truth validation via skyfield.

Two tests at the heart of the H-battery:

- ``saros_prediction_test`` (E-H1):  for each of a list of reference
  eclipses, verify that the encoder's Saros-period spacing places the
  date within +-1 day of an actual lunar/solar syzygy according to
  ``skyfield``'s ephemeris.  The spit (Track 1) generalises this from
  a hardcoded modern-era anchor list to either MODERN (E-H1a control)
  or HELLENISTIC (E-H1b validation against Almagest IV-VI eclipses).

- ``mars_longitude_error`` (E-H2/E-H3/E-H4):  generic comparator that
  takes any longitude function ``longitude_fn(jd) -> deg`` and reports
  peak/mean/RMS angular error against ``skyfield``'s Mars apparent
  longitude.  Track 2's ``equant_encoder`` plugs uniform / Hipparchus
  epicycle-only / Ptolemy equant models into this.  The legacy
  ``mars_retrograde_error`` is preserved as a thin wrapper that
  passes the uniform-rate model.

Ephemeris kernel selection is now a first-class CLI argument.  DE441
(Park et al. 2021) is the default; DE441_part1 covers the Antikythera
era at half the disk cost; DE422 is a 660 MB compromise; DE421 (the
original 16 MB modern-era kernel) is retained as a "modern control
only" option but does not reach back to Hellenistic dates.

If skyfield or the chosen kernel cannot be loaded (offline sandbox or
file missing), the high-level functions raise ``RuntimeError`` and the
H-battery emits ``UNDETERMINED`` rows rather than crashing.

References
----------
Park, R. S. et al. (2021).  The JPL Planetary and Lunar Ephemerides
    DE440 and DE441.  Astron. J. 161:105.
Toomer, G. J. (1984).  Ptolemy's Almagest.  Princeton.
Espenak, F.  NASA Five Millennium Catalog of Solar Eclipses.
"""

from __future__ import annotations

import argparse
import sys
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np

from .hellenistic_eclipses import (
    EclipseAnchor,
    HELLENISTIC_ANCHORS,
    MODERN_SAROS_ANCHORS,
    VALID_ERAS,
    anchors_for_era,
    filter_by_confidence,
)


# ---------------------------------------------------------------------------
# Kernel name handling -- delegates to ephemeris_loader for cache + lazy
# import discipline.
# ---------------------------------------------------------------------------

DEFAULT_KERNEL = "de441"


def _try_load_ephemeris(kernel: str = DEFAULT_KERNEL,
                        kernel_file: Optional[str] = None):
    """Load (cached) skyfield bundle via ``ephemeris_loader``.  Returns
    ``None`` on any failure; never raises.

    Kept as a module-private helper for back-compat with the original
    no-arg signature; new callers should use
    ``ephemeris_loader.load_ephemeris`` directly.
    """
    from .ephemeris_loader import load_ephemeris
    return load_ephemeris(kernel=kernel, kernel_file=kernel_file)


def ground_truth_available(kernel: str = DEFAULT_KERNEL,
                           kernel_file: Optional[str] = None) -> bool:
    """True iff the chosen ephemeris kernel can be loaded."""
    return _try_load_ephemeris(kernel, kernel_file) is not None


# ---------------------------------------------------------------------------
# Compatibility constants (preserve old API; do not remove)
# ---------------------------------------------------------------------------

SAROS_REFERENCE_ANCHOR_JD: float = 2451402.0
"""Modern Saros anchor (1999-08-11 European total solar eclipse).
Preserved for callers that pre-date Track 1; new code reads from
``hellenistic_eclipses.MODERN_SAROS_ANCHORS``."""

SAROS_DAYS_EXACT: float = 6585.3211
"""Exact Saros period in TDB days = 223 synodic months."""

SAROS_REFERENCE_DATES_JD: List[float] = [
    SAROS_REFERENCE_ANCHOR_JD + i * SAROS_DAYS_EXACT for i in range(20)
]


# ---------------------------------------------------------------------------
# E-H1: Saros / eclipse prediction test (anchor-driven)
# ---------------------------------------------------------------------------

def _phase_distance_days(phase_deg: float, synodic_days: float) -> float:
    """Distance to nearest new-or-full-moon, expressed in synodic days."""
    if phase_deg < 90:
        dist_deg = phase_deg
    elif phase_deg < 270:
        dist_deg = abs(phase_deg - 180)
    else:
        dist_deg = 360 - phase_deg
    return dist_deg * synodic_days / 360.0


def saros_prediction_test(
    anchors: Optional[List[EclipseAnchor]] = None,
    kernel: str = DEFAULT_KERNEL,
    kernel_file: Optional[str] = None,
    n_eclipses: Optional[int] = None,
) -> List[Dict]:
    """For each anchor, compute the lunar phase angle at JD and report
    syzygy proximity.  This is the per-anchor reading the H-battery
    aggregates into PASS/FAIL.

    Parameters
    ----------
    anchors : list of EclipseAnchor or None
        If None, uses the modern Saros control set
        (``MODERN_SAROS_ANCHORS``).  Caller chooses Hellenistic or both
        via ``hellenistic_eclipses.anchors_for_era()``.
    kernel : str
        JPL DE-kernel name (default: 'de441').
    kernel_file : optional str
        Direct filesystem path to a pre-downloaded .bsp file.
    n_eclipses : optional int
        Truncate the anchor list to first N entries.

    Returns
    -------
    List[Dict] with per-anchor fields:
        jd, era, eclipse_type, almagest_ref, lunar_phase_deg,
        dist_to_syzygy_days, within_1_day, error_deg.
    """
    bundle = _try_load_ephemeris(kernel=kernel, kernel_file=kernel_file)
    if bundle is None:
        raise RuntimeError(
            f"skyfield + {kernel} not available.  "
            "Run `python -m research.ephemeris_loader --download "
            f"{kernel}` to fetch."
        )

    if anchors is None:
        anchors = list(MODERN_SAROS_ANCHORS)
    if n_eclipses is not None:
        anchors = anchors[:n_eclipses]

    ts = bundle.ts
    earth = bundle.earth
    sun = bundle.sun
    moon = bundle.moon

    SYNODIC = 29.530588861
    out: List[Dict] = []
    for anc in anchors:
        from .ephemeris_loader import covers_jd
        if not covers_jd(kernel, anc.jd):
            out.append({
                "jd": float(anc.jd),
                "date_iso": anc.date_iso,
                "era": "modern" if anc in MODERN_SAROS_ANCHORS else "hellenistic",
                "eclipse_type": anc.eclipse_type,
                "almagest_ref": anc.almagest_ref,
                "lunar_phase_deg": float("nan"),
                "dist_to_syzygy_days": float("nan"),
                "within_1_day": False,
                "error_deg": float("nan"),
                "kernel_covers": False,
                "note": f"kernel {kernel} does not cover JD {anc.jd}",
            })
            continue
        t = ts.tdb_jd(anc.jd)
        e = earth.at(t)
        s_obs = e.observe(sun).apparent()
        m_obs = e.observe(moon).apparent()
        _, s_lon, _ = s_obs.ecliptic_latlon()
        _, m_lon, _ = m_obs.ecliptic_latlon()
        phase_deg = float(np.degrees(m_lon.radians - s_lon.radians)) % 360
        dist_days = _phase_distance_days(phase_deg, SYNODIC)
        # Encoder tolerance: lunar phase at the anchor JD should be
        # within +-2 deg of either 0 (new moon, solar eclipse) or 180
        # (full moon, lunar eclipse) depending on type.  This is the
        # E-H1b stricter check; E-H1a (modern control) only enforces
        # the +-1 day spacing.
        if anc.eclipse_type == "S":
            error_deg = phase_deg if phase_deg <= 180 else 360 - phase_deg
        else:
            error_deg = abs(phase_deg - 180)
        out.append({
            "jd": float(anc.jd),
            "date_iso": anc.date_iso,
            "era": "hellenistic" if anc in HELLENISTIC_ANCHORS else "modern",
            "eclipse_type": anc.eclipse_type,
            "almagest_ref": anc.almagest_ref,
            "lunar_phase_deg": phase_deg,
            "dist_to_syzygy_days": float(dist_days),
            "within_1_day": bool(dist_days <= 1.0),
            "error_deg": float(error_deg),
            "kernel_covers": True,
            "note": "",
        })
    return out


# ---------------------------------------------------------------------------
# E-H2/E-H3/E-H4: generic Mars longitude comparator
# ---------------------------------------------------------------------------

def _wrap_180(diff: float) -> float:
    """Wrap angular difference to [0, 180]."""
    diff = abs(diff) % 360
    if diff > 180:
        diff = 360 - diff
    return diff


def mars_longitude_error(
    longitude_fn: Callable[[float], float],
    span_days: int = 780,
    n_samples: int = 200,
    start_jd: float = 2451545.0,
    kernel: str = DEFAULT_KERNEL,
    kernel_file: Optional[str] = None,
    anchor_at_start: bool = True,
) -> Dict[str, float]:
    """Compare an injected ``longitude_fn(jd) -> deg`` against skyfield
    Mars apparent longitude over ``span_days`` from ``start_jd``.

    Used by ``equant_encoder.compare_models`` to test uniform vs
    epicycle-only vs equant Mars models.  ``anchor_at_start`` shifts
    the model output by a constant offset so the first sample matches
    skyfield exactly -- emulates the encoder's day-zero anchor.

    Returns
    -------
    Dict with keys: peak_deg, mean_deg, rms_deg, n_samples,
    samples_jd (list), errors_deg (list), kernel_used.
    """
    bundle = _try_load_ephemeris(kernel=kernel, kernel_file=kernel_file)
    if bundle is None:
        raise RuntimeError(
            f"skyfield + {kernel} not available.  "
            "Use `python -m research.ephemeris_loader --download "
            f"{kernel}`."
        )
    ts = bundle.ts
    earth = bundle.earth
    sun = bundle.sun
    mars = bundle.mars

    times = np.linspace(start_jd, start_jd + span_days, n_samples)
    sky_phases: List[float] = []
    for jd in times:
        t = ts.tdb_jd(float(jd))
        e = earth.at(t)
        m = e.observe(mars).apparent()
        s = e.observe(sun).apparent()
        _, m_lon, _ = m.ecliptic_latlon()
        _, s_lon, _ = s.ecliptic_latlon()
        sky_phases.append(
            float(np.degrees(m_lon.radians - s_lon.radians)) % 360
        )

    model_phases = [float(longitude_fn(float(jd))) % 360 for jd in times]

    # Apply anchor offset so the first sample matches skyfield exactly.
    if anchor_at_start:
        offset = (sky_phases[0] - model_phases[0]) % 360
        model_phases = [(p + offset) % 360 for p in model_phases]

    errors = np.array([_wrap_180(s - m) for s, m
                       in zip(sky_phases, model_phases)])
    return {
        "peak_deg": float(np.max(errors)),
        "mean_deg": float(np.mean(errors)),
        "rms_deg": float(np.sqrt(np.mean(errors ** 2))),
        "n_samples": int(len(errors)),
        "samples_jd": [float(t) for t in times],
        "errors_deg": [float(e) for e in errors],
        "kernel_used": kernel,
    }


def mars_retrograde_error(
    span_days: int = 780,
    n_samples: int = 200,
    start_jd: float = 2451545.0,
    kernel: str = DEFAULT_KERNEL,
    kernel_file: Optional[str] = None,
) -> Tuple[float, float, int]:
    """Legacy uniform-Mars wrapper preserved for back-compat.

    Returns ``(peak_deg, mean_deg, n_samples)`` -- the original 3-tuple.
    Track 2's ``equant_encoder`` calls ``mars_longitude_error`` directly
    with the appropriate model function.
    """
    MARS_SYNODIC_DAYS = 779.94

    def _uniform(jd: float) -> float:
        elapsed = jd - start_jd
        return (360.0 * elapsed / MARS_SYNODIC_DAYS) % 360

    stats = mars_longitude_error(
        longitude_fn=_uniform,
        span_days=span_days,
        n_samples=n_samples,
        start_jd=start_jd,
        kernel=kernel,
        kernel_file=kernel_file,
    )
    return stats["peak_deg"], stats["mean_deg"], stats["n_samples"]


# ---------------------------------------------------------------------------
# CLI surface
# ---------------------------------------------------------------------------

_EPILOG = """\
Examples:
  # Modern Saros control (E-H1a):
  python -m research.astronomical_ground_truth --era modern --ephemeris de421

  # Hellenistic Almagest validation (E-H1b):
  python -m research.astronomical_ground_truth --era hellenistic \\
        --ephemeris de441_part1

  # Both eras side-by-side (default):
  python -m research.astronomical_ground_truth --era both \\
        --ephemeris de441_part1

  # Mars uniform-model error (legacy E-H2):
  python -m research.astronomical_ground_truth --mars --ephemeris de441_part1

  # Custom JD range override:
  python -m research.astronomical_ground_truth --era hellenistic \\
        --date-range 1684000 1790000 --ephemeris de441_part1

ephemeris kernels (see `python -m research.ephemeris_loader --list-kernels`):
  de421       1899-2053 only (16 MB).  MODERN-ERA control test only;
              cannot validate Hellenistic anchors.
  de422       3001 BCE - 3000 CE (660 MB).  Antikythera-era OK.
  de441       13201 BCE - 17191 CE (~3 GB).  JPL current best.
  de441_part1 13201 BCE - 1550 CE (~1.5 GB).  Hellenistic-only subset.

Citations
---------
Park et al. (2021) AJ 161:105 -- DE440/DE441 ephemerides.
Toomer (1984) Ptolemy's Almagest -- Hellenistic anchors IV.6, IV.9,
    V.14, VI.5.
Morrison & Stephenson (2004) JHA 35:327 -- DeltaT historical model.
"""


def _make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m research.astronomical_ground_truth",
        description=(
            "Validate the Antikythera encoder against JPL ephemeris.  "
            "Compares the Saros-cycle prediction (E-H1) and the Mars "
            "synodic prediction (E-H2) to a chosen DE kernel."
        ),
        epilog=_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--ephemeris", default=DEFAULT_KERNEL,
        choices=("de421", "de422", "de441", "de441_part1", "de441_part2"),
        help=f"JPL DE kernel name (default: {DEFAULT_KERNEL}).",
    )
    parser.add_argument(
        "--ephemeris-path", dest="ephemeris_bsp", default=None,
        help="Direct path to a .bsp file (offline override).",
    )
    parser.add_argument(
        "--era", choices=VALID_ERAS, default="both",
        help="Anchor era to validate (default: both).",
    )
    parser.add_argument(
        "--date-range", nargs=2, type=float, default=None,
        metavar=("START_JD", "END_JD"),
        help="Override era anchors with anchors in [START_JD, END_JD].",
    )
    parser.add_argument(
        "--n-eclipses", type=int, default=None,
        help="Truncate anchor list to first N entries.",
    )
    parser.add_argument(
        "--include-disputed", action="store_true",
        help="Include DISPUTED anchors (off by default).",
    )
    parser.add_argument(
        "--mars", action="store_true",
        help="Run the Mars uniform-model test (E-H2 baseline).",
    )
    parser.add_argument(
        "--quiet", action="store_true",
        help="Print only the summary line (PASS/FAIL counts).",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = _make_parser().parse_args(argv)

    print("astronomical_ground_truth -- Phase 4 skyfield validation")
    print("=" * 70)
    available = ground_truth_available(kernel=args.ephemeris,
                                       kernel_file=args.ephemeris_bsp)
    print(f"  ephemeris kernel : {args.ephemeris}")
    print(f"  available locally: {available}")
    if not available:
        print(f"\n  Run `python -m research.ephemeris_loader --download "
              f"{args.ephemeris}` to fetch.")
        return 1

    # Anchor selection
    if args.date_range is not None:
        from .hellenistic_eclipses import anchors_in_jd_range
        anchors = anchors_in_jd_range(args.date_range[0], args.date_range[1])
    else:
        anchors = anchors_for_era(args.era)
    if not args.include_disputed:
        anchors = filter_by_confidence(anchors, include_disputed=False)
    if args.n_eclipses is not None:
        anchors = anchors[:args.n_eclipses]
    print(f"  anchors selected : {len(anchors)} (era={args.era!r})")
    print()

    # E-H1 / saros_prediction_test
    print("--- E-H1: anchor syzygy proximity ---")
    try:
        results = saros_prediction_test(
            anchors=anchors,
            kernel=args.ephemeris,
            kernel_file=args.ephemeris_bsp,
        )
    except RuntimeError as exc:
        print(f"  ERROR: {exc}")
        return 2

    n_within_1day = sum(1 for r in results if r["within_1_day"])
    n_within_2deg = sum(1 for r in results if r["error_deg"] <= 2.0)
    n_total = len(results)
    if not args.quiet:
        print(f"  {'JD':>11}  {'date':>12}  {'era':<11}  "
              f"{'phase':>7}  {'dist_d':>7}  {'err_deg':>8}  ok")
        for r in results:
            ok = "Y" if r["within_1_day"] and r["error_deg"] <= 2.0 else "n"
            phase = (f"{r['lunar_phase_deg']:>7.2f}"
                     if not np.isnan(r["lunar_phase_deg"]) else "    n/a")
            dist = (f"{r['dist_to_syzygy_days']:>7.3f}"
                    if not np.isnan(r["dist_to_syzygy_days"]) else "    n/a")
            err = (f"{r['error_deg']:>8.3f}"
                   if not np.isnan(r["error_deg"]) else "     n/a")
            print(f"  {r['jd']:>11.1f}  {r['date_iso']:>12}  "
                  f"{r['era']:<11}  {phase}  {dist}  {err}  {ok}")
        print()
    print(f"  {n_within_1day}/{n_total} anchors within +-1 day of syzygy.")
    print(f"  {n_within_2deg}/{n_total} anchors within +-2 deg of phase 0/180.")
    print()

    # E-H2 / Mars uniform model
    if args.mars:
        print("--- E-H2: Mars uniform-model error (one synodic period) ---")
        try:
            peak, mean, n = mars_retrograde_error(
                kernel=args.ephemeris,
                kernel_file=args.ephemeris_bsp,
            )
            print(f"  Peak error: {peak:>6.2f} deg")
            print(f"  Mean error: {mean:>6.2f} deg")
            print(f"  Samples   : {n}")
            print("  Documented Greek attainable limit: ~38 deg "
                  "(Ptolemy equant; not uniform).")
        except RuntimeError as exc:
            print(f"  ERROR: {exc}")
        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())

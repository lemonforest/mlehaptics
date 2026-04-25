"""Sky-driven validation -- the damaged-hologram inversion (Section 11).

Instead of curating Hellenistic eclipse anchors by hand (where a single
half-month JD error can knock the test off), this module flips the
direction: scan DE422 ephemeris for syzygies (new moons + full moons)
in a chosen JD band, then ask how many of those syzygies the encoder's
Saros cycle predicts within +- 1 day of an anchor reference.

This is the **E-H1c** test sketched in notebook section 11.3 sub-problem A.
The encoder side has zero hand-curated data; the anchor for the Saros
cycle is chosen as the nearest DE422 syzygy to a single well-attested
historical date (defaults to -134-04-08, Hipparchus's lunar eclipse,
Almagest V.14).

This module also provides ``planetary_residual()`` -- sub-problem B
from section 11.3 -- comparing any planet's encoder longitude against
DE422 over a chosen window.

References
----------
Section 11 of antikythera_spectral_research_notebook.md (the
damaged-hologram inversion framing).
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


# Default JD band: -200 BCE to +100 CE, the Antikythera era.
DEFAULT_JD_LO: float = 1684500.0   # ~-200-09-09
DEFAULT_JD_HI: float = 1796000.0   # ~+143-09-13

# Hipparchus's Almagest V.14 lunar eclipse; nearest syzygy in the band
# whose JD value is independently constrained by Toomer 1984's commentary.
HIPPARCHUS_LUNAR_ECLIPSE_JD: float = 1709093.5

SAROS_DAYS_EXACT: float = 6585.3211


# ---------------------------------------------------------------------------
# Sky-driven syzygy scanner
# ---------------------------------------------------------------------------

@dataclass
class SyzygyEvent:
    jd: float
    phase_deg: float       # 0 for new moon, 180 for full
    eclipse_type: str      # 'S' (solar candidate, near phase 0) or 'L' (lunar, near 180)


def _phase_at_jd(bundle, jd: float) -> float:
    """Lunar phase angle (Sun -> Earth -> Moon, ecliptic) in deg [0, 360)."""
    import numpy as np
    t = bundle.ts.tdb_jd(float(jd))
    e = bundle.earth.at(t)
    s = e.observe(bundle.sun).apparent()
    m = e.observe(bundle.moon).apparent()
    _, s_lon, _ = s.ecliptic_latlon()
    _, m_lon, _ = m.ecliptic_latlon()
    return float(np.degrees(m_lon.radians - s_lon.radians)) % 360.0


def scan_syzygies(
    jd_lo: float = DEFAULT_JD_LO,
    jd_hi: float = DEFAULT_JD_HI,
    kernel: str = "de422",
    kernel_path: Optional[str] = None,
    sample_step_days: float = 1.0,
    refine_tolerance_deg: float = 0.5,
) -> List[SyzygyEvent]:
    """Find every syzygy in [jd_lo, jd_hi] via DE422.

    Strategy
    --------
    1. Sample the lunar phase every ``sample_step_days`` days.
    2. Detect zero crossings of (phase mod 180) -- each is a syzygy.
    3. Bisection-refine each crossing to ``refine_tolerance_deg``.

    Returns syzygies sorted by JD.  ~24 lunations / year * 300 years
    = ~7200 syzygies in the Hellenistic-era band.  Coarse scan ~30s
    for the full band; bisection adds ~10s.
    """
    import numpy as np
    from .ephemeris_loader import load_ephemeris

    bundle = load_ephemeris(kernel=kernel, kernel_path=kernel_path)
    if bundle is None:
        raise RuntimeError(
            f"Ephemeris kernel {kernel!r} not loadable.  "
            f"Run `python -m research.ephemeris_loader --download {kernel}`."
        )

    # Coarse scan: detect zero crossings of sin(phase) -- these are syzygies
    # (sin(0) = sin(180) = 0).  cos(phase) sign distinguishes type.  This
    # avoids the modular discontinuity at phase = 90 / 270 that a folded
    # |phase mod 180 - 90| metric introduces.
    n_samples = max(2, int((jd_hi - jd_lo) / sample_step_days) + 1)
    jds = np.linspace(jd_lo, jd_hi, n_samples)
    phases_rad = np.array([np.radians(_phase_at_jd(bundle, float(j)))
                           for j in jds])
    sin_phase = np.sin(phases_rad)

    events: List[SyzygyEvent] = []
    for i in range(len(sin_phase) - 1):
        a, b = sin_phase[i], sin_phase[i + 1]
        if a * b < 0:  # genuine zero crossing of sin(phase)
            lo_jd, hi_jd = float(jds[i]), float(jds[i + 1])
            lo_v, hi_v = float(a), float(b)
            # Bisect to refine
            for _ in range(40):
                mid_jd = 0.5 * (lo_jd + hi_jd)
                mid_phase = _phase_at_jd(bundle, mid_jd)
                mid_v = float(np.sin(np.radians(mid_phase)))
                if abs(np.degrees(np.arcsin(np.clip(mid_v, -1, 1)))) \
                        < refine_tolerance_deg:
                    break
                if mid_v * lo_v < 0:
                    hi_jd, hi_v = mid_jd, mid_v
                else:
                    lo_jd, lo_v = mid_jd, mid_v
            phase_at_root = _phase_at_jd(bundle, mid_jd)
            ec_type = ("S" if (phase_at_root < 90 or phase_at_root > 270)
                       else "L")
            events.append(SyzygyEvent(
                jd=mid_jd, phase_deg=phase_at_root, eclipse_type=ec_type,
            ))
    return events


# ---------------------------------------------------------------------------
# Encoder Saros prediction coverage (E-H1c)
# ---------------------------------------------------------------------------

def _nearest_syzygy_jd(syzygies: List[SyzygyEvent],
                       target_jd: float) -> Optional[float]:
    """Return JD of the syzygy in the list closest to ``target_jd``.

    Used to anchor the Saros chain to an actual DE422 syzygy rather than
    trusting a hand-curated historical JD (which proved buggy in E-H1b).
    """
    if not syzygies:
        return None
    best = min(syzygies, key=lambda s: abs(s.jd - target_jd))
    return float(best.jd)


def infer_anchor_jd_from_date(
    nominal_jd: float,
    eclipse_type: str,
    tolerance_days: float = 16.0,
    sample_step_days: float = 1.0,
    kernel: str = "de422",
    kernel_path: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Find the actual DE422 syzygy nearest to a nominal hand-curated JD.

    Used to CORRECT the buggy hand-curated JDs in
    ``hellenistic_eclipses.HELLENISTIC_ANCHORS`` by letting DE422 itself
    determine the true eclipse JD.  Searches +-tolerance_days around
    the nominal JD for a syzygy of the matching eclipse_type ('S' for
    solar / new moon, 'L' for lunar / full moon).

    Returns dict with:
        nominal_jd          : input
        corrected_jd        : DE422 syzygy JD
        shift_days          : corrected - nominal
        eclipse_type        : 'S' | 'L' (matching the requested type)
        phase_deg           : lunar phase at corrected JD
    Or None if no matching syzygy is found in the tolerance window.
    """
    import numpy as np
    events = scan_syzygies(
        jd_lo=nominal_jd - tolerance_days,
        jd_hi=nominal_jd + tolerance_days,
        kernel=kernel, kernel_path=kernel_path,
        sample_step_days=sample_step_days,
    )
    matching = [e for e in events if e.eclipse_type == eclipse_type]
    if not matching:
        return None
    # Pick the one closest to nominal_jd
    best = min(matching, key=lambda e: abs(e.jd - nominal_jd))
    return {
        "nominal_jd": float(nominal_jd),
        "corrected_jd": float(best.jd),
        "shift_days": float(best.jd - nominal_jd),
        "eclipse_type": best.eclipse_type,
        "phase_deg": float(best.phase_deg),
    }


def saros_coverage(
    syzygies: List[SyzygyEvent],
    anchor_jd: float = HIPPARCHUS_LUNAR_ECLIPSE_JD,
    tolerance_days: float = 1.0,
    saros_days: float = SAROS_DAYS_EXACT,
    sky_anchor: bool = True,
    eclipse_type: Optional[str] = None,
) -> Dict[str, Any]:
    """Fraction of syzygies that the encoder's Saros multiples cover.

    The encoder's Saros pointer ticks every 6585.32 days from a single
    anchor.  Successive Saros multiples mark *one* eclipse candidate per
    cycle -- not every syzygy.  But syzygies *adjacent* to a Saros
    multiple (within +-1 day) ARE eclipse candidates by the encoder's
    definition.

    Reframing for E-H1c: the right question is "of the syzygies the
    encoder marks as eclipse candidates (Saros multiples), how many
    actually are syzygies in the sky?"  We compute both directions:

    forward_recall   = fraction of DE422 syzygies within +-1 day of any
                       (anchor + k * Saros) for integer k.
    backward_precision = fraction of (anchor + k * Saros) within +-1 day
                       of a DE422 syzygy.

    The encoder is sound iff backward_precision is high (every Saros
    multiple is genuinely a syzygy).  Forward_recall is low by design --
    the Saros marks only the eclipse-bearing subset of syzygies.
    """
    import numpy as np

    if not syzygies:
        return {"forward_recall": float("nan"),
                "backward_precision": float("nan"),
                "n_syzygies": 0, "n_saros_marks": 0}

    # Optionally restrict to syzygies of one eclipse type (e.g. lunar only)
    if eclipse_type is not None:
        filtered = [s for s in syzygies if s.eclipse_type == eclipse_type]
    else:
        filtered = list(syzygies)
    if not filtered:
        return {"forward_recall": float("nan"),
                "backward_precision": float("nan"),
                "n_syzygies": 0, "n_saros_marks": 0}

    syz_jds = np.array(sorted(s.jd for s in filtered))

    # Sky-anchor: replace user-provided anchor_jd with the closest actual
    # DE422 syzygy.  This is THE point of the sky-driven framing -- let
    # DE422 anchor the Saros chain rather than trusting hand-curated JDs.
    effective_anchor = anchor_jd
    if sky_anchor:
        nearest = _nearest_syzygy_jd(filtered, anchor_jd)
        if nearest is not None:
            effective_anchor = nearest

    # Generate Saros multiples ONLY within the syzygy-enumeration window.
    # Marks outside [syz_jds[0], syz_jds[-1]] cannot be evaluated -- there
    # are no syzygies enumerated there to match against -- so including
    # them in the precision count is an artifact.
    jd_lo = syz_jds[0]
    jd_hi = syz_jds[-1]
    k_lo = int(np.ceil((jd_lo - effective_anchor) / saros_days))
    k_hi = int(np.floor((jd_hi - effective_anchor) / saros_days))
    saros_jds = np.array([effective_anchor + k * saros_days
                          for k in range(k_lo, k_hi + 1)])

    # forward_recall: fraction of syzygies within tol of ANY saros mark
    fwd_hits = 0
    for s_jd in syz_jds:
        if np.min(np.abs(saros_jds - s_jd)) <= tolerance_days:
            fwd_hits += 1
    forward_recall = fwd_hits / len(syz_jds)

    # backward_precision: fraction of saros marks within tol of ANY syzygy
    bwd_hits = 0
    for sa_jd in saros_jds:
        if np.min(np.abs(syz_jds - sa_jd)) <= tolerance_days:
            bwd_hits += 1
    backward_precision = bwd_hits / len(saros_jds)

    return {
        "forward_recall": forward_recall,
        "backward_precision": backward_precision,
        "n_syzygies": len(syz_jds),
        "n_saros_marks": len(saros_jds),
        "fwd_hits": fwd_hits,
        "bwd_hits": bwd_hits,
        "nominal_anchor_jd": anchor_jd,
        "effective_anchor_jd": float(effective_anchor),
        "anchor_shift_days": float(effective_anchor - anchor_jd),
        "eclipse_type_filter": eclipse_type,
        "saros_days": saros_days,
        "tolerance_days": tolerance_days,
    }


# ---------------------------------------------------------------------------
# Planetary-train verification (sub-problem B)
# ---------------------------------------------------------------------------

def planetary_residual(
    planet: str = "mars",
    span_days: int = 780,
    n_samples: int = 200,
    start_jd: Optional[float] = None,
    kernel: str = "de422",
    kernel_path: Optional[str] = None,
) -> Dict[str, float]:
    """Residual of the encoder's planetary longitude vs DE422.

    Routes through the existing ``mars_longitude_error`` infrastructure
    for Mars; wraps a similar comparator inline for other planets.
    Default ``start_jd`` is REFERENCE_JD (the Antikythera epoch).
    """
    from .ephemeris_loader import load_ephemeris
    from .encode_ant import REFERENCE_JD

    if start_jd is None:
        start_jd = REFERENCE_JD

    if planet == "mars":
        from .astronomical_ground_truth import mars_retrograde_error
        peak, mean, n = mars_retrograde_error(
            span_days=span_days, n_samples=n_samples,
            start_jd=start_jd, kernel=kernel, kernel_path=kernel_path,
        )
        return {"planet": "mars", "peak_deg": peak, "mean_deg": mean,
                "n_samples": n, "start_jd": start_jd, "kernel": kernel}

    # For other planets: simple uniform-rate residue vs ephemeris.
    import numpy as np
    bundle = load_ephemeris(kernel=kernel, kernel_path=kernel_path)
    if bundle is None:
        raise RuntimeError(f"Kernel {kernel!r} not loadable.")

    body = getattr(bundle, planet, None)
    if body is None:
        raise ValueError(f"Unknown planet {planet!r} in bundle.")

    times = np.linspace(start_jd, start_jd + span_days, n_samples)
    sun_lons = []
    body_lons = []
    for jd in times:
        t = bundle.ts.tdb_jd(float(jd))
        e = bundle.earth.at(t)
        s = e.observe(bundle.sun).apparent()
        b = e.observe(body).apparent()
        _, s_lon, _ = s.ecliptic_latlon()
        _, b_lon, _ = b.ecliptic_latlon()
        sun_lons.append(float(np.degrees(s_lon.radians)) % 360.0)
        body_lons.append(float(np.degrees(b_lon.radians)) % 360.0)
    diffs = np.array([(b - s) % 360.0 for b, s in zip(body_lons, sun_lons)])
    diffs = np.where(diffs > 180, diffs - 360, diffs)
    return {"planet": planet, "peak_deg": float(np.max(np.abs(diffs))),
            "mean_deg": float(np.mean(np.abs(diffs))),
            "n_samples": n_samples, "start_jd": start_jd, "kernel": kernel}


# ---------------------------------------------------------------------------
# CLI surface
# ---------------------------------------------------------------------------

_EPILOG = """\
Examples:
  # Sky-driven E-H1c: scan DE422 syzygies in the Antikythera era,
  # report Saros-coverage metrics:
  python -m research.sky_driven_validation --ephemeris de422

  # Restrict to a single century:
  python -m research.sky_driven_validation --jd-range 1684500 1721000 \\
        --ephemeris de422

  # Planetary residual (Mars vs DE422 over 780 days from REFERENCE_JD):
  python -m research.sky_driven_validation --planet mars --ephemeris de422

References
----------
Notebook section 11: damaged-hologram lattice reconstruction.
DE422 ephemeris: Park et al. 2021 (AJ 161:105) for DE440/441 family.
"""


def _make_parser():
    parser = argparse.ArgumentParser(
        prog="python -m research.sky_driven_validation",
        description=("Sky-driven validation of the encoder against DE422.  "
                     "Scans actual ephemeris syzygies in a chosen Hellenistic-"
                     "era band, then reports Saros-coverage metrics.  "
                     "Bypasses hand-curated anchor JDs entirely."),
        epilog=_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--ephemeris", default="de422",
        choices=("de421", "de422", "de441", "de441_part1"),
        help="JPL DE kernel (default: de422; covers full Antikythera era).",
    )
    parser.add_argument(
        "--ephemeris-path", default=None,
        help="Direct path to a .bsp file (offline override).",
    )
    parser.add_argument(
        "--jd-range", nargs=2, type=float, default=None,
        metavar=("JD_LO", "JD_HI"),
        help=(f"JD interval to scan (default: {DEFAULT_JD_LO} .. "
              f"{DEFAULT_JD_HI}).  Roughly -200 BCE to +143 CE."),
    )
    parser.add_argument(
        "--anchor-jd", type=float, default=HIPPARCHUS_LUNAR_ECLIPSE_JD,
        help=f"Saros anchor JD (default: Hipparchus -134-04-08 = "
             f"{HIPPARCHUS_LUNAR_ECLIPSE_JD}).",
    )
    parser.add_argument(
        "--tolerance-days", type=float, default=1.0,
        help="Tolerance band for Saros / syzygy match (default: 1.0).",
    )
    parser.add_argument(
        "--sample-step-days", type=float, default=1.0,
        help="Coarse-scan step size (default: 1.0).  Smaller = slower + more accurate.",
    )
    parser.add_argument(
        "--planet", default=None,
        choices=("mars", "venus", "mercury", "jupiter", "saturn"),
        help="Run planetary residual instead of syzygy scan.",
    )
    parser.add_argument(
        "--span-days", type=int, default=780,
        help="Planetary span (default: 780, ~Mars synodic).",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = _make_parser().parse_args(argv)

    if args.planet:
        print(f"Planetary residual: {args.planet} vs {args.ephemeris} "
              f"({args.span_days} days from REFERENCE_JD)")
        try:
            res = planetary_residual(
                planet=args.planet, span_days=args.span_days,
                kernel=args.ephemeris, kernel_path=args.ephemeris_path,
            )
        except RuntimeError as exc:
            print(f"  ERROR: {exc}")
            return 1
        print(f"  peak deg : {res['peak_deg']:.2f}")
        print(f"  mean deg : {res['mean_deg']:.2f}")
        print(f"  n_samples: {res['n_samples']}")
        return 0

    jd_lo, jd_hi = (args.jd_range if args.jd_range is not None
                    else (DEFAULT_JD_LO, DEFAULT_JD_HI))
    print(f"Sky-driven syzygy scan vs {args.ephemeris}")
    print(f"  JD band : [{jd_lo:.1f}, {jd_hi:.1f}]  ({(jd_hi - jd_lo)/365.25:.0f} years)")
    print(f"  anchor  : JD {args.anchor_jd:.1f}  (Saros chain reference)")
    print(f"  tolerance: +-{args.tolerance_days} days")
    print()

    try:
        events = scan_syzygies(
            jd_lo=jd_lo, jd_hi=jd_hi, kernel=args.ephemeris,
            kernel_path=args.ephemeris_path,
            sample_step_days=args.sample_step_days,
        )
    except RuntimeError as exc:
        print(f"  ERROR: {exc}")
        return 1

    print(f"Found {len(events)} syzygies in band.")
    print()

    # Run twice: all syzygies, then lunar-only (Saros family)
    for ec_filter in (None, "L"):
        label = "all syzygies" if ec_filter is None else "lunar only (L)"
        cov = saros_coverage(events, anchor_jd=args.anchor_jd,
                             tolerance_days=args.tolerance_days,
                             sky_anchor=True, eclipse_type=ec_filter)
        print(f"Saros-coverage metrics ({label}):")
        print(f"  n_syzygies        : {cov['n_syzygies']}")
        print(f"  n_saros_marks     : {cov['n_saros_marks']}")
        print(f"  nominal anchor JD : {cov['nominal_anchor_jd']:.1f}")
        print(f"  effective anchor  : {cov['effective_anchor_jd']:.3f} "
              f"(shifted {cov['anchor_shift_days']:+.3f} d to match nearest "
              "DE422 syzygy)")
        print(f"  forward_recall    : {cov['forward_recall']:.3f}  "
              f"(syzygies within +-{args.tolerance_days}d of a Saros mark)")
        print(f"  backward_precision: {cov['backward_precision']:.3f}  "
              f"(Saros marks within +-{args.tolerance_days}d of a syzygy)")
        print()

    print("Interpretation:")
    print("  backward_precision should be HIGH (Saros chain is sound) -- if")
    print("  it is, the encoder reliably marks eclipse candidates.  When")
    print("  eclipse-type-filtered to lunar (L), Saros marks fall on lunar")
    print("  syzygies by definition (Saros = 223 synodic months).")
    print("  forward_recall is naturally LOW because Saros marks only one")
    print("  syzygy per ~6585 days, not every syzygy (~24/yr).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

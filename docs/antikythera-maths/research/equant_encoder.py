"""Equant-bearing Mars encoder -- Track 2 (E-H3, E-H4, D-H3).

The Antikythera mechanism's Mars dial in ``encode_ant`` uses a uniform-
rate residue: longitude advances by a constant 360 deg / 779.94 days.
Skyfield's Mars apparent longitude carries retrograde motion and non-
uniform speed, so the uniform model peaks at ~180 deg of error
(E-H2 PARTIAL).  The Greek 38 deg figure cited in the build prompt
comes from the Ptolemaic deferent + epicycle + equant model
(Almagest IX-X), which the mechanism's known-uniform gear trains
cannot themselves implement.

This module disentangles three regimes:

    uniform        Constant 360/779.94 deg/day.  Encoder baseline.
                   Expected peak error: ~180 deg (E-H2).
    epicycle-only  Hipparchus-style: deferent + epicycle, both rotating
                   uniformly w.r.t. Earth (no equant).  This is the model
                   the Antikythera's pin-and-slot can mechanically
                   approximate.  Expected peak error: ~5-10 deg (E-H3).
    equant         Ptolemy: deferent rotates uniformly w.r.t. an equant
                   point offset 2e from Earth (bisection of eccentricity);
                   epicycle rotates uniformly w.r.t. its own centre.
                   Expected peak error: ~30-50 deg in the band Toomer
                   describes as Greek attainable (E-H4).

A separate algebraic finding (D-H3): the equant introduces anharmonic
motion, so ``sigma_day = roll_operator(D, 1)`` is no longer a *unit*
on the Mars channel.  Equivalently, the per-day residue increment
becomes JD-dependent.  This is a research finding, not a bug -- it
means the Antikythera's known gear trains literally cannot implement
a Ptolemaic equant; they could only approximate one with epicycles
(Hipparchus) plus a pin-and-slot.

References
----------
Toomer, G. J. (1984).  Ptolemy's Almagest.  Princeton.  Books IX-X
    define the Mars equant model with deferent radius R = 60,
    epicycle radius r = 39.5, eccentricity e = 6, equant offset = 2e.
Neugebauer, O. (1975).  A History of Ancient Mathematical Astronomy.
    Springer.  Section V.B.6 derives the geometric equation of center
    and equation of anomaly.

ASSUMPTION: The "Hipparchus model" here is implemented as
"Ptolemy IX.5 with the equant collapsed to the deferent centre"
(i.e. e_equant = e_deferent).  This is the cleanest counterfactual
for measuring the equant's contribution.  Hipparchus's actual Mars
parameters are partially lost; we are NOT claiming this model is
literally Hipparchus's, only that it is the equant-free analogue
that isolates the equant's marginal contribution.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Almagest IX-X canonical Mars parameters (Toomer 1984)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class MarsParams:
    """Geometric + kinematic parameters of the Greek Mars model.

    All radii dimensionless ("parts" with R=60).  Mean motions in
    deg/day (from Almagest IX.6, Toomer 1984 p.448).  Epoch is the
    Antikythera reference JD (1684595.0, ~205 BCE), with epoch_lon
    propagated from Almagest's Nabonassar 1 anchor (JD 1448638.5).
    """

    deferent_radius: float = 60.0
    epicycle_radius: float = 39.5
    eccentricity: float = 6.0           # Earth -> deferent centre offset
    equant_offset: float = 12.0          # Earth -> equant point (bisection: 2e)
    mean_motion_lon_deg_per_day: float = 0.524062
    """Sidereal mean motion of the deferent centre about Earth (Almagest
    IX.6, Toomer 1984 p.448)."""

    mean_motion_anomaly_deg_per_day: float = 0.461570
    """Synodic mean motion of the planet on the epicycle (Almagest
    IX.6, Toomer 1984 p.448)."""

    epoch_lon_deg: float = 297.4
    """Mean longitude of deferent centre at REFERENCE_JD = 1684595.0,
    propagated from Almagest IX.6's Nabonassar 1 anchor.  Approximate;
    see ``epoch_propagation_test`` smoke test for the cross-check."""

    epoch_anomaly_deg: float = 41.6
    """Mean anomaly at REFERENCE_JD."""

    label: str = "Ptolemy / Almagest IX-X (Toomer 1984)"


PTOLEMY_MARS_PARAMS = MarsParams()
"""Default Almagest-derived Mars parameters."""


VALID_MODELS: Tuple[str, ...] = ("uniform", "epicycle-only", "equant", "all")


# ---------------------------------------------------------------------------
# Reference JD (matches encode_ant.REFERENCE_JD)
# ---------------------------------------------------------------------------

REFERENCE_JD: float = 1684595.0
"""Antikythera-era reference epoch.  Matches ``encode_ant.REFERENCE_JD``;
duplicated here to keep this module's dependencies lean."""


# ---------------------------------------------------------------------------
# Solar longitude (Greek tropical Sun, uniform mean motion)
# ---------------------------------------------------------------------------

SOLAR_TROPICAL_DEG_PER_DAY: float = 360.0 / 365.24219
"""Tropical-year mean motion of the Sun.  Greek model uses this as
uniform; the small 1-2 deg sun-equation contribution we ignore (it is
common to all three Mars models so cancels out of model-vs-model
comparisons)."""

EPOCH_SUN_LON_DEG: float = 285.0
"""Mean solar longitude at REFERENCE_JD.  Approximate Hellenistic-era
spring-equinox-relative position; cancels out of all three models."""


def _solar_mean_longitude(jd: float) -> float:
    return (EPOCH_SUN_LON_DEG
            + SOLAR_TROPICAL_DEG_PER_DAY * (jd - REFERENCE_JD)) % 360.0


# ---------------------------------------------------------------------------
# Model A: uniform synodic
# ---------------------------------------------------------------------------

MARS_SYNODIC_DAYS: float = 779.94


def mars_longitude_uniform(jd: float, params: MarsParams = PTOLEMY_MARS_PARAMS
                           ) -> float:
    """Synodic-phase longitude under the uniform-rate model.

    The "longitude" here is Mars-minus-Sun synodic phase (matches
    skyfield's m_lon - s_lon), so it can be plugged directly into
    ``astronomical_ground_truth.mars_longitude_error``.
    """
    elapsed = jd - REFERENCE_JD
    # Uniform encoder: synodic phase advances at 360/779.94 deg/day.
    return (360.0 * elapsed / MARS_SYNODIC_DAYS) % 360.0


# ---------------------------------------------------------------------------
# Model B: Hipparchus epicycle-only (no equant)
#
# Geometry: Earth at O.  Deferent centre D at offset e along apsidal
# line.  Planet on circle of radius R around D, with mean motion in
# longitude lambda_def.  Epicycle of radius r centred on the planet's
# deferent position; planet moves on epicycle uniformly w.r.t. its own
# centre with mean motion alpha.
# ---------------------------------------------------------------------------

def _equation_of_center_hipparchus(M: float, e: float, R: float) -> float:
    """Equation of center for a simple eccentric deferent (no equant).

    M is the mean angle from D (deferent centre).  Returns geocentric
    longitude offset (radians) such that ``lambda_geocentric =
    M + equation_of_center``.
    """
    import math
    # Vector from O to planet on deferent: (e + R cos M, R sin M).
    return math.atan2(R * math.sin(M), e + R * math.cos(M)) - M


def _equation_of_anomaly(alpha: float, R_eff: float, r: float) -> float:
    """Equation of anomaly for the epicycle.

    alpha is the angle on the epicycle (planet position relative to
    epicycle centre, measured in geocentric direction).  R_eff is the
    distance from Earth to the epicycle centre.
    """
    import math
    # Planet position relative to epicycle centre: (r cos alpha, r sin alpha).
    # Add to epicycle centre at distance R_eff in fixed direction; we
    # measure the offset angle from Earth.
    return math.atan2(r * math.sin(alpha), R_eff + r * math.cos(alpha))


def mars_longitude_epicycle_only(
    jd: float, params: MarsParams = PTOLEMY_MARS_PARAMS,
) -> float:
    """Hipparchus-style synodic phase: eccentric deferent + epicycle,
    no equant.  Uses the same eccentricity ``e`` for the deferent
    offset; equant offset collapsed to ``e`` (i.e. equant = deferent
    centre, no bisection of eccentricity)."""
    import math
    elapsed = jd - REFERENCE_JD
    R = params.deferent_radius
    r = params.epicycle_radius
    e = params.eccentricity

    # Mean longitude of deferent centre (radians)
    M_lon = math.radians(
        params.epoch_lon_deg
        + params.mean_motion_lon_deg_per_day * elapsed
    )
    # Mean anomaly on epicycle (radians)
    M_anom = math.radians(
        params.epoch_anomaly_deg
        + params.mean_motion_anomaly_deg_per_day * elapsed
    )

    # Equation of center (no equant: equant = deferent centre)
    eqn_center = _equation_of_center_hipparchus(M_lon, e, R)
    lambda_def = M_lon + eqn_center

    # Geocentric distance to deferent position
    R_eff = math.sqrt((e + R * math.cos(M_lon)) ** 2
                      + (R * math.sin(M_lon)) ** 2)

    # The anomaly angle reckoned from the epicycle centre, oriented so
    # that alpha=0 is the apogee of the epicycle (away from Earth).
    # The epicycle's apsidal line is parallel to the line Earth-epicycle-
    # centre, hence alpha measured in the planet's epicycle frame:
    # alpha_geocentric = alpha + lambda_def.  But for the equation of
    # anomaly we want alpha relative to the line E -> epicycle centre,
    # which IS lambda_def for both models.
    alpha = M_anom - lambda_def
    eqn_anom = _equation_of_anomaly(alpha, R_eff, r)
    lambda_mars = lambda_def + eqn_anom

    lambda_sun = math.radians(_solar_mean_longitude(jd))
    return (math.degrees(lambda_mars - lambda_sun)) % 360.0


# ---------------------------------------------------------------------------
# Model C: Ptolemy equant
#
# Earth O at origin; deferent centre D offset e along apsidal line;
# equant point E offset 2e (bisection of eccentricity).  Planet on
# circle radius R about D, but the LINE from E to the planet rotates
# uniformly with mean motion lambda_lon.  Epicycle as before.
# ---------------------------------------------------------------------------

def _equation_of_center_equant(M: float, e: float, R: float) -> float:
    """Equation of center under Ptolemy's bisected eccentricity.

    M is the mean angle reckoned at the equant point E (offset 2e
    from Earth, e from deferent centre).  Returns the geocentric
    longitude offset.
    """
    import math
    # Solve for R' = |EP| such that the planet sits on the deferent
    # circle |P - D| = R, with the line EP making angle M with the
    # apsidal axis.  This reduces to a quadratic in R'.
    cos_M = math.cos(M)
    sin_M = math.sin(M)
    # |P - D|^2 = R^2:  (2e + R' cos M - e)^2 + (R' sin M)^2 = R^2
    # -> R'^2 + 2 e R' cos M + (e^2 - R^2) = 0
    # Take positive root:
    discr = R * R - e * e * sin_M * sin_M
    if discr < 0:
        # Impossible geometry; return naive M unchanged.
        return 0.0
    R_prime = -e * cos_M + math.sqrt(discr)

    # Geocentric position of planet (relative to Earth):
    px = 2.0 * e + R_prime * cos_M
    py = R_prime * sin_M
    lambda_def_geo = math.atan2(py, px)
    return lambda_def_geo - M


def mars_longitude_equant(
    jd: float, params: MarsParams = PTOLEMY_MARS_PARAMS,
) -> float:
    """Ptolemaic synodic phase: deferent uniform w.r.t. equant point
    (offset 2e from Earth); epicycle uniform on its own centre."""
    import math
    elapsed = jd - REFERENCE_JD
    R = params.deferent_radius
    r = params.epicycle_radius
    e = params.eccentricity

    M_lon = math.radians(
        params.epoch_lon_deg
        + params.mean_motion_lon_deg_per_day * elapsed
    )
    M_anom = math.radians(
        params.epoch_anomaly_deg
        + params.mean_motion_anomaly_deg_per_day * elapsed
    )

    eqn_center = _equation_of_center_equant(M_lon, e, R)
    lambda_def = M_lon + eqn_center

    # Recompute geocentric distance under equant geometry
    cos_M = math.cos(M_lon)
    sin_M = math.sin(M_lon)
    discr = max(0.0, R * R - e * e * sin_M * sin_M)
    R_prime = -e * cos_M + math.sqrt(discr)
    px = 2.0 * e + R_prime * cos_M
    py = R_prime * sin_M
    R_eff = math.sqrt(px * px + py * py)

    alpha = M_anom - lambda_def
    eqn_anom = _equation_of_anomaly(alpha, R_eff, r)
    lambda_mars = lambda_def + eqn_anom

    lambda_sun = math.radians(_solar_mean_longitude(jd))
    return (math.degrees(lambda_mars - lambda_sun)) % 360.0


# ---------------------------------------------------------------------------
# Model registry
# ---------------------------------------------------------------------------

MODEL_FUNCTIONS: Dict[str, Callable[[float, MarsParams], float]] = {
    "uniform": mars_longitude_uniform,
    "epicycle-only": mars_longitude_epicycle_only,
    "equant": mars_longitude_equant,
}


def model_residue_function(model: str,
                           params: MarsParams = PTOLEMY_MARS_PARAMS,
                           ) -> Callable[[float], float]:
    """Return a closure ``f(jd) -> deg`` for the chosen model.

    Plug-compatible with
    ``astronomical_ground_truth.mars_longitude_error``.  D-H3 hooks
    here -- the ``equant`` closure is anharmonic in JD (per-day
    increment is not constant), which breaks the sigma_day = roll(D, 1)
    unit-operator property on the Mars channel.
    """
    if model not in MODEL_FUNCTIONS:
        raise ValueError(f"model must be one of {VALID_MODELS}, got {model!r}")
    fn = MODEL_FUNCTIONS[model]

    def closure(jd: float) -> float:
        return fn(jd, params)

    return closure


# ---------------------------------------------------------------------------
# Comparison helper
# ---------------------------------------------------------------------------

@dataclass
class ModelStats:
    model: str
    peak_deg: float
    mean_deg: float
    rms_deg: float
    n_samples: int


def compare_models(
    span_days: int = 780,
    n_samples: int = 200,
    start_jd: Optional[float] = None,
    kernel: str = "de441",
    path: Optional[str] = None,
    params: MarsParams = PTOLEMY_MARS_PARAMS,
) -> Dict[str, ModelStats]:
    """Run all three models against skyfield ephemeris.

    ``start_jd`` defaults to ``REFERENCE_JD + 0`` -- the Antikythera era
    reference.  Pass a modern ``start_jd`` (e.g. 2451545.0 = J2000) to
    spot-check against the original E-H2 baseline.
    """
    from .astronomical_ground_truth import mars_longitude_error

    if start_jd is None:
        start_jd = REFERENCE_JD

    out: Dict[str, ModelStats] = {}
    for model in ("uniform", "epicycle-only", "equant"):
        fn = model_residue_function(model, params)
        stats = mars_longitude_error(
            longitude_fn=fn,
            span_days=span_days,
            n_samples=n_samples,
            start_jd=start_jd,
            kernel=kernel,
            path=path,
        )
        out[model] = ModelStats(
            model=model,
            peak_deg=stats["peak_deg"],
            mean_deg=stats["mean_deg"],
            rms_deg=stats["rms_deg"],
            n_samples=stats["n_samples"],
        )
    return out


# ---------------------------------------------------------------------------
# D-H3: sigma_day unit-operator test on equant channel
# ---------------------------------------------------------------------------

def sigma_day_unit_test(
    model: str = "equant",
    params: MarsParams = PTOLEMY_MARS_PARAMS,
    n_samples: int = 100,
    start_jd: Optional[float] = None,
) -> Dict[str, float]:
    """Test whether ``longitude(jd+1) - longitude(jd)`` is constant.

    For the uniform model this is exactly 360/779.94 deg.  For the
    epicycle-only and equant models, the per-day increment varies
    with JD -- the larger the variance, the more anharmonic the
    motion.  D-H3 PASS = uniform; D-H3 FAIL = equant (expected).

    Returns ``{mean, std, max_dev}`` where:
      mean    = mean per-day increment (deg)
      std     = std-dev of per-day increments
      max_dev = max abs deviation of per-day increment from its mean
    """
    import numpy as np
    if start_jd is None:
        start_jd = REFERENCE_JD
    fn = model_residue_function(model, params)
    jds = np.linspace(start_jd, start_jd + n_samples, n_samples + 1)
    longs = np.array([fn(float(jd)) for jd in jds])
    # Unwrap so the diff isn't fooled by 360 jumps
    longs_unwrapped = np.degrees(np.unwrap(np.radians(longs)))
    diffs = np.diff(longs_unwrapped)
    return {
        "model": model,
        "mean_deg_per_day": float(np.mean(diffs)),
        "std_deg_per_day": float(np.std(diffs)),
        "max_dev_deg_per_day": float(np.max(np.abs(diffs - np.mean(diffs)))),
        "n_samples": int(len(diffs)),
    }


# ---------------------------------------------------------------------------
# CLI surface
# ---------------------------------------------------------------------------

_EPILOG = """\
Examples:
  # Single-model run (need pre-fetched de441_part1):
  python -m research.equant_encoder --model equant --ephemeris de441_part1

  # Side-by-side three-model comparison:
  python -m research.equant_encoder --model all --ephemeris de441_part1

  # D-H3 anharmonicity probe (no ephemeris needed):
  python -m research.equant_encoder --sigma-day-test --model equant

  # Modern J2000 baseline (Mars moved 380 deg over the synodic period):
  python -m research.equant_encoder --model all --start-jd 2451545.0

Models
------
  uniform        Encoder baseline (current encode_ant); peak ~180 deg.
  epicycle-only  Hipparchus model (no equant); peak ~5-10 deg expected.
  equant         Ptolemy model (Almagest IX-X); peak ~30-50 deg
                 -- the documented Greek attainable limit.

Citations
---------
Toomer (1984) Ptolemy's Almagest, Books IX-X.
Neugebauer (1975) HAMA, Section V.B.6.
Pin-and-slot geometry: Freeth (2006) Nature 444:587 (lunar epicycle).
"""


def _make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m research.equant_encoder",
        description=(
            "Compare three Greek planetary models against modern "
            "ephemeris for Mars: uniform (encoder baseline), epicycle-"
            "only (Hipparchus), and equant (Ptolemy)."
        ),
        epilog=_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--model", choices=VALID_MODELS, default="all",
        help="Which model to run (default: all).",
    )
    parser.add_argument(
        "--ephemeris", default="de441",
        choices=("de421", "de422", "de441", "de441_part1", "de441_part2"),
        help="JPL DE kernel name (default: de441).",
    )
    parser.add_argument(
        "--ephemeris-path", default=None,
        help="Direct path to a .bsp file.",
    )
    parser.add_argument(
        "--span-days", type=int, default=780,
        help="Comparison span in days (default: 780, ~1 Mars synodic).",
    )
    parser.add_argument(
        "--n-samples", type=int, default=200,
        help="Sample count over the span (default: 200).",
    )
    parser.add_argument(
        "--start-jd", type=float, default=None,
        help=("Anchor JD (default: REFERENCE_JD = 1684595, the "
              "Antikythera-era epoch)."),
    )
    parser.add_argument(
        "--sigma-day-test", action="store_true",
        help="Probe the per-day increment harmonicity (D-H3); "
             "no ephemeris needed.",
    )
    parser.add_argument(
        "--plot", action="store_true",
        help="Save matplotlib comparison plot (lazy import; skipped silently "
             "if matplotlib absent).",
    )
    parser.add_argument(
        "--plot-out", default=None,
        help="Plot output path (default: results/equant_comparison.png).",
    )
    return parser


def _print_comparison(results: Dict[str, ModelStats]) -> None:
    print(f"{'model':<16} {'peak deg':>10}  {'mean deg':>10}  "
          f"{'rms deg':>10}  N")
    print("-" * 56)
    for k in ("uniform", "epicycle-only", "equant"):
        if k in results:
            s = results[k]
            print(f"{k:<16} {s.peak_deg:>10.2f}  {s.mean_deg:>10.2f}  "
                  f"{s.rms_deg:>10.2f}  {s.n_samples}")


def _try_plot(results: Dict[str, ModelStats], out_path: str) -> bool:
    try:
        import matplotlib.pyplot as plt  # type: ignore
    except ImportError:
        return False
    fig, ax = plt.subplots(figsize=(9, 5))
    names = list(results.keys())
    peak = [results[n].peak_deg for n in names]
    mean = [results[n].mean_deg for n in names]
    x = list(range(len(names)))
    ax.bar([i - 0.2 for i in x], peak, width=0.4, label="peak deg")
    ax.bar([i + 0.2 for i in x], mean, width=0.4, label="mean deg")
    ax.set_xticks(x)
    ax.set_xticklabels(names)
    ax.set_ylabel("degrees")
    ax.set_title("Greek Mars models vs ephemeris")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    return True


def main(argv: Optional[List[str]] = None) -> int:
    args = _make_parser().parse_args(argv)

    if args.sigma_day_test:
        for model in ("uniform", "epicycle-only", "equant"):
            stats = sigma_day_unit_test(model=model, n_samples=400)
            print(f"  model={model:<14}: mean d_lambda/d_day = "
                  f"{stats['mean_deg_per_day']:>7.4f} deg  "
                  f"std = {stats['std_deg_per_day']:>7.4f} deg  "
                  f"max_dev = {stats['max_dev_deg_per_day']:>7.4f} deg")
        print()
        print("D-H3 expectation: uniform std == 0 (perfect unit operator); "
              "equant std > 0 (anharmonic, NOT a unit operator).")
        return 0

    print(f"Comparing model(s) {args.model!r} vs {args.ephemeris!r}...")

    if args.model == "all":
        try:
            results = compare_models(
                span_days=args.span_days,
                n_samples=args.n_samples,
                start_jd=args.start_jd,
                kernel=args.ephemeris,
                path=args.ephemeris_path,
            )
        except RuntimeError as exc:
            print(f"  ERROR: {exc}")
            return 1
        _print_comparison(results)
        if args.plot:
            out = args.plot_out or "results/equant_comparison.png"
            ok = _try_plot(results, out)
            print(f"\n  Plot {'written to ' + out if ok else 'skipped (matplotlib unavailable)'}")
        return 0

    # Single-model case
    try:
        from .astronomical_ground_truth import mars_longitude_error
        fn = model_residue_function(args.model)
        stats = mars_longitude_error(
            longitude_fn=fn,
            span_days=args.span_days,
            n_samples=args.n_samples,
            start_jd=args.start_jd or REFERENCE_JD,
            kernel=args.ephemeris,
            path=args.ephemeris_path,
        )
    except RuntimeError as exc:
        print(f"  ERROR: {exc}")
        return 1
    print(f"  model      : {args.model}")
    print(f"  peak deg   : {stats['peak_deg']:>7.2f}")
    print(f"  mean deg   : {stats['mean_deg']:>7.2f}")
    print(f"  rms deg    : {stats['rms_deg']:>7.2f}")
    print(f"  n_samples  : {stats['n_samples']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

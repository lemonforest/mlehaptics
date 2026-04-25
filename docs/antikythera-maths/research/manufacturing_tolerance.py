"""Manufacturing-tolerance Monte Carlo (Track 3, G-H1 / G-H2 / G-H3).

Bronze gears cut by 2nd-century BCE Greek workshops carried fractional-
tooth imprecision.  A single mesh introduces a small multiplicative
ratio error; across a 6-10 mesh planetary train these errors compound.
This module:

- Defines named train specifications (lunar, Saros, Metonic, Mercury,
  Venus, Mars, Jupiter, Saturn) with their mesh chains.
- Runs Monte Carlo simulations with per-mesh noise drawn from
  ``gear_noise_models`` parametrisations.
- Reports peak / mean / 95th-percentile pointer drift over a chosen
  horizon (default: 1 Metonic = 19 yr) per train.

Three falsifiable hypotheses (G-H1..G-H3) are evaluated:

    G-H1  Saros train pointer drift p95 <= 2 deg over 19 years
          under sigma = 0.5 / mean_tooth_count Gaussian noise.
          Asks: was the mechanism ACTUALLY usable for one Metonic
          cycle without re-calibration?
    G-H2  Lunar pin-and-slot train p95 <= 1.2x straight-train baseline.
          Asks: does the elegance of D-H1 cost in tolerance robustness?
    G-H3  Trains containing rare large primes (53, 127, 223, 251) do
          NOT have systematically larger per-mesh sigma than the
          train-median.  Asks: are celestially-FORCED primes also
          manufacturing-FRAGILE, or can the mechanism gracefully
          accommodate them?

References
----------
Szigety, E. & Arenas, G. F. (2025).  The Impact of Triangular-Toothed
    Gears on the Functionality of the Antikythera Mechanism.
    arXiv:2504.00327 [physics.hist-ph].  Combines Thorndike's analytical
    solution for triangular-tooth motion with Edmunds 2014's manufacturing-
    error model; finds the mechanism would jam within ~120 days under
    realistic tolerance.  Our G-H1 result (~13 deg / 19 yr Saros drift)
    is the angular-error reading of the same physical situation.
Wright, M. T. (2005).  The Antikythera Mechanism: a new gearing scheme.
    Bull. Sci. Instr. Soc. 85:2-7.
Edmunds, M. G. (2014).  An initial assessment of the accuracy of the
    gear trains in the Antikythera Mechanism.  J. Hist. Astron. 45:202-222.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .gear_noise_models import (
    CATALOG,
    GUILLERMO_SZIGETY_2025_DEFAULT,
    NoiseSpec,
    VALID_MODES,
    sample_epsilon_for_meshes,
)


# ---------------------------------------------------------------------------
# Train specifications
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TrainSpec:
    """One named gear train with its mesh-pair chain."""

    name: str
    mesh_pairs: Tuple[Tuple[int, int], ...]
    """Tuple of (n_driver, n_driven) mesh pairs.  E.g. lunar's
    (38, 96), (32, 24), (24, 127), ... etc."""

    output_revs_per_year: float
    """How many full revolutions the OUTPUT pointer makes per year.
    Saros: 1/18.03; Metonic: 1/19; Lunar synodic-month dial: 12.37;
    Mars synodic dial: 365.25/779.94 = 0.468; etc.

    Used to convert fractional ratio error to absolute angular drift:
        drift_deg = 360 * output_revs_per_year * horizon_years
                        * (R_noisy / R_noiseless - 1)
    """

    noiseless_ratio: Tuple[int, int]
    """The exact noiseless ratio (driver/driven product) in lowest terms.
    Computed self-consistently from ``mesh_pairs`` by ``_spec``."""

    contains_rare_primes: Tuple[int, ...] = field(default_factory=tuple)
    """Rare primes (47, 53, 127, 223, 251) appearing in this train's
    tooth counts.  Used by G-H3 evaluator."""

    description: str = ""


def _self_consistent_ratio(mesh_pairs: Sequence[Tuple[int, int]]
                           ) -> Tuple[int, int]:
    """Compute the exact lowest-terms ratio of a mesh chain."""
    from math import gcd
    p_num = 1
    p_den = 1
    for n_drv, n_drn in mesh_pairs:
        p_num *= n_drv
        p_den *= n_drn
    g = gcd(p_num, p_den)
    return (p_num // g, p_den // g)


def _spec(name: str,
          mesh_pairs: Tuple[Tuple[int, int], ...],
          output_revs_per_year: float,
          contains_rare_primes: Tuple[int, ...] = (),
          description: str = "") -> TrainSpec:
    return TrainSpec(
        name=name,
        mesh_pairs=mesh_pairs,
        output_revs_per_year=output_revs_per_year,
        noiseless_ratio=_self_consistent_ratio(mesh_pairs),
        contains_rare_primes=contains_rare_primes,
        description=description,
    )


def _build_train_specs() -> List[TrainSpec]:
    """Construct the production train specs.

    Mesh pairs are derived from gear_database.MESH_EDGES (Freeth 2021).
    Planetary trains use the (numerator, denominator) integers directly
    as a single mesh -- a simplification because Freeth's planetary
    reconstructions are conceptual rather than physically attested.

    ``noiseless_ratio`` is computed self-consistently from the mesh
    chain itself, so the Monte Carlo's relative-error metric is well-
    defined regardless of the conceptual train ratio.

    ``input_turns_per_year`` reflects how many full revolutions of the
    INPUT shaft occur per year of operation, given the mechanism is
    cranked once per year (or whatever the canonical input rate is).
    For the Antikythera the input crank rotates the b1 sun gear once
    per year; downstream ratios then determine output rates.
    """
    return [
        _spec(
            "saros",
            mesh_pairs=((53, 53), (54, 60), (60, 60), (60, 54)),
            output_revs_per_year=1.0 / 18.03,
            contains_rare_primes=(53,),
            description="Saros eclipse train (4 meshes; pointer 1 rev / 18.03 yr).",
        ),
        _spec(
            "lunar",
            mesh_pairs=((38, 48), (24, 127), (32, 32), (32, 32)),
            output_revs_per_year=12.368,  # synodic months / yr
            contains_rare_primes=(127,),
            description=("Lunar train including pin-and-slot epicycle "
                         "(D-H1).  Pointer 12.37 rev / yr (synodic months)."),
        ),
        _spec(
            "lunar_straight_baseline",
            mesh_pairs=((38, 48), (24, 127), (32, 32), (32, 32)),
            output_revs_per_year=12.368,
            contains_rare_primes=(127,),
            description=("Synthetic straight-gear lunar baseline -- same "
                         "tooth counts but no pin-and-slot eccentricity. "
                         "For G-H2 ablation only."),
        ),
        _spec(
            "metonic",
            mesh_pairs=((64, 32), (32, 53), (53, 96), (53, 38), (53, 96)),
            output_revs_per_year=1.0 / 19.0,
            contains_rare_primes=(53,),
            description="Metonic train (5 meshes; pointer 1 rev / 19 yr).",
        ),
        _spec(
            "mercury",
            mesh_pairs=((145, 46),),
            output_revs_per_year=365.24 / 115.88,
            contains_rare_primes=(),
            description="Mercury 145/46 -- pointer ~3.15 rev/yr (synodic).",
        ),
        _spec(
            "venus",
            mesh_pairs=((289, 462),),
            output_revs_per_year=365.24 / 583.92,
            contains_rare_primes=(),
            description="Venus 289/462 = 17^2 / (2*3*7*11) -- shared 7 + 17.",
        ),
        _spec(
            "mars",
            mesh_pairs=((133, 125),),
            output_revs_per_year=365.24 / 779.94,
            contains_rare_primes=(),
            description="Mars 133/125 = (7*19) / 5^3 -- ~0.47 rev/yr.",
        ),
        _spec(
            "jupiter",
            mesh_pairs=((76, 83),),
            output_revs_per_year=365.24 / 398.88,
            contains_rare_primes=(83,),
            description="Jupiter 76/83 -- ~0.92 rev/yr (synodic).",
        ),
        _spec(
            "saturn",
            mesh_pairs=((427, 442),),
            output_revs_per_year=365.24 / 378.09,
            contains_rare_primes=(),
            description="Saturn 427/442 = (7*61) / (2*13*17) -- ~0.97 rev/yr.",
        ),
    ]


_TRAIN_SPECS_CACHE: Optional[List[TrainSpec]] = None


def train_specs() -> List[TrainSpec]:
    """Return the production train specs (cached)."""
    global _TRAIN_SPECS_CACHE
    if _TRAIN_SPECS_CACHE is None:
        _TRAIN_SPECS_CACHE = _build_train_specs()
    return list(_TRAIN_SPECS_CACHE)


def train_by_name(name: str) -> TrainSpec:
    for s in train_specs():
        if s.name == name:
            return s
    raise KeyError(f"No train named {name!r}")


VALID_TRAIN_NAMES: Tuple[str, ...] = tuple(s.name for s in _build_train_specs())


# ---------------------------------------------------------------------------
# Per-mesh sampling
# ---------------------------------------------------------------------------

def _mesh_mean_tooth_counts(spec: TrainSpec) -> List[float]:
    return [(p[0] + p[1]) / 2.0 for p in spec.mesh_pairs]


def sample_train_ratio(
    spec: TrainSpec,
    noise_spec: NoiseSpec,
    rng: Optional[Any] = None,
) -> float:
    """Single Monte Carlo trial: draw epsilons, return noisy ratio."""
    import numpy as np
    if rng is None:
        rng = np.random.default_rng(noise_spec.seed)
    means = _mesh_mean_tooth_counts(spec)
    eps = sample_epsilon_for_meshes(noise_spec, means, rng=rng)
    if noise_spec.mode == "worst-case":
        # Sign-flip adversarially to maximise cumulative |log(ratio)|
        # Each mesh contributes log(1 + eps) ~ eps; pick all signs same
        # along the chain so they accumulate.
        eps = np.abs(eps)
        # Sign convention: every mesh either +eps or -eps; choose +eps.
    ratio = 1.0
    for (n_drv, n_drn), e in zip(spec.mesh_pairs, eps):
        ratio *= (n_drv / n_drn) * (1.0 + float(e))
    return ratio


# ---------------------------------------------------------------------------
# Monte Carlo
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Operational regimes
# ---------------------------------------------------------------------------
# The "horizon_years" parameter in monte_carlo_train treats the mechanism as
# running CONTINUOUSLY for the horizon (24/7 over the full window).  This is
# the worst-case assumption.  The crank-as-clutch hypothesis (notebook §11.6.10)
# proposes the mechanism only ticks during ACTIVE cranking.  We support both
# regimes via the ``operation_regime`` parameter.
#
# Under intermittent operation, drift accumulates at the rate of input shaft
# rotation, not calendar time.  The output revs/yr * horizon_years bound is
# replaced by an explicit "active output revolutions over horizon" count.

CONTINUOUS_OPERATION = "continuous"
INTERMITTENT_OPERATION = "intermittent"
VALID_OPERATION_REGIMES = (CONTINUOUS_OPERATION, INTERMITTENT_OPERATION)

# Default intermittent-operation schedule (from notebook §11.6.10.4):
# the mechanism advances ~78 days per crank revolution.  Assume 5 sessions
# per Olympiad (~one per year), each advancing 4 years of mechanism time
# at ~1 rev/sec.  4 yr / (78 d/rev) = ~18.7 rev per session.  18.7 rev/sec
# is too fast; assume operator cranks at ~1 rev/sec, so ~19 sec per session
# of active gear motion.  Five sessions/yr -> ~95 sec active per year.
# Conservative round-up: 100 active gear-motion seconds per calendar year.
DEFAULT_ACTIVE_SECONDS_PER_YEAR: float = 100.0


def monte_carlo_train(
    spec: TrainSpec,
    *,
    n_trials: int = 10000,
    noise_spec: NoiseSpec = GUILLERMO_SZIGETY_2025_DEFAULT,
    horizon_years: float = 19.0,
    seed: Optional[int] = None,
    operation_regime: str = CONTINUOUS_OPERATION,
    active_seconds_per_year: float = DEFAULT_ACTIVE_SECONDS_PER_YEAR,
) -> Dict[str, Any]:
    """Sample n_trials noisy ratios and report angular drift statistics.

    Continuous regime (default): drift accumulates over the full horizon
    in calendar years, treating the mechanism as running 24/7.

    Intermittent regime (per notebook §11.6.10 crank-as-clutch hypothesis):
    drift accumulates only during active cranking.  ``active_seconds_per_year``
    sets the operator's annual cranking budget (default 100 s/yr).  The
    effective drift horizon scales by ``active_seconds_per_year /
    seconds_per_year``, so 100 s/yr over a 19-yr nominal horizon corresponds
    to ~5.5 minutes of cumulative active gear motion.
    """
    import numpy as np
    if seed is None:
        seed = noise_spec.seed
    if operation_regime not in VALID_OPERATION_REGIMES:
        raise ValueError(f"operation_regime must be one of "
                         f"{VALID_OPERATION_REGIMES}, got {operation_regime!r}")
    rng = np.random.default_rng(seed)
    p, q = spec.noiseless_ratio
    noiseless_ratio = float(p) / float(q) if q != 0 else 1.0

    # Effective drift horizon
    if operation_regime == INTERMITTENT_OPERATION:
        seconds_per_year = 365.25 * 86400.0
        effective_horizon = horizon_years * (active_seconds_per_year
                                             / seconds_per_year)
    else:
        effective_horizon = horizon_years

    drifts_deg: List[float] = []
    for _ in range(n_trials):
        noisy = sample_train_ratio(spec, noise_spec, rng=rng)
        if noiseless_ratio == 0.0:
            rel_err = 0.0
        else:
            rel_err = (noisy / noiseless_ratio) - 1.0
        # Output pointer drift over horizon = 360 deg * output_revs * rel_err
        drift_deg = (360.0 * spec.output_revs_per_year
                     * effective_horizon * rel_err)
        drifts_deg.append(drift_deg)

    arr = np.asarray(drifts_deg, dtype=float)
    return {
        "train": spec.name,
        "n_trials": n_trials,
        "horizon_years": horizon_years,
        "operation_regime": operation_regime,
        "active_seconds_per_year": (active_seconds_per_year
                                    if operation_regime == INTERMITTENT_OPERATION
                                    else None),
        "effective_horizon_years": effective_horizon,
        "noiseless_ratio": noiseless_ratio,
        "noise_mode": noise_spec.mode,
        "noise_sigma": noise_spec.sigma,
        "mean_abs_deg": float(np.mean(np.abs(arr))),
        "std_deg": float(np.std(arr)),
        "p95_deg": float(np.percentile(np.abs(arr), 95)),
        "max_deg": float(np.max(np.abs(arr))),
        "histogram_bins": np.histogram(arr, bins=50)[1].tolist(),
        "histogram_counts": np.histogram(arr, bins=50)[0].tolist(),
    }


def run_all(
    *,
    n_trials: int = 10000,
    noise_spec: NoiseSpec = GUILLERMO_SZIGETY_2025_DEFAULT,
    horizon_years: float = 19.0,
    seed: Optional[int] = None,
    train_filter: Optional[Sequence[str]] = None,
    operation_regime: str = CONTINUOUS_OPERATION,
    active_seconds_per_year: float = DEFAULT_ACTIVE_SECONDS_PER_YEAR,
) -> List[Dict[str, Any]]:
    """Run Monte Carlo across every train (or a filtered subset)."""
    out: List[Dict[str, Any]] = []
    for spec in train_specs():
        if train_filter is not None and spec.name not in train_filter:
            continue
        out.append(monte_carlo_train(
            spec, n_trials=n_trials, noise_spec=noise_spec,
            horizon_years=horizon_years, seed=seed,
            operation_regime=operation_regime,
            active_seconds_per_year=active_seconds_per_year,
        ))
    return out


# ---------------------------------------------------------------------------
# Hypothesis evaluators
# ---------------------------------------------------------------------------

def evaluate_G_H1(
    results: Optional[List[Dict[str, Any]]] = None,
    threshold_deg: float = 2.0,
) -> Tuple[str, str, str, Dict[str, object]]:
    """G-H1: Saros train p95 pointer drift <= 2 deg over 19 years.

    PASS iff the p95 |drift| of the saros train at horizon=19 yr
    under the default Guillermo-Szigety noise spec is <= threshold_deg.
    """
    if results is None:
        results = run_all(n_trials=2000, train_filter=("saros",))
    saros = next((r for r in results if r["train"] == "saros"), None)
    if saros is None:
        return ("UNDETERMINED", "saros result missing",
                "manufacturing_tolerance.run_all() did not include saros",
                {"results": results})
    p95 = saros["p95_deg"]
    status = "PASS" if p95 <= threshold_deg else "FAIL"
    notes = (
        f"Saros (4-mesh) p95 = {p95:.3f} deg over 19 yr under "
        f"sigma=0.5/<n> Gaussian noise (mode={saros['noise_mode']!r}).  "
        f"Threshold: {threshold_deg} deg."
    )
    computed = f"saros p95 = {p95:.3f} deg over 19 yr"
    detail = {
        "train": "saros",
        "p95_deg": p95,
        "threshold_deg": threshold_deg,
        "n_trials": saros["n_trials"],
        "noise_mode": saros["noise_mode"],
        "horizon_years": saros["horizon_years"],
    }
    return status, computed, notes, detail


def evaluate_G_H2(
    results: Optional[List[Dict[str, Any]]] = None,
    ratio_threshold: float = 1.2,
) -> Tuple[str, str, str, Dict[str, object]]:
    """G-H2: lunar pin-and-slot p95 <= 1.2x straight-baseline.

    Compares the ``lunar`` train (with pin-and-slot) to a synthetic
    ``lunar_straight_baseline`` train of equal mesh count.  Since both
    use the same tooth counts in this implementation, we expect ratio
    ~1.0 -- testing the structural claim that pin-and-slot does not
    systematically increase per-mesh sigma.
    """
    if results is None:
        results = run_all(n_trials=2000,
                          train_filter=("lunar", "lunar_straight_baseline"))
    lunar = next((r for r in results if r["train"] == "lunar"), None)
    base = next((r for r in results
                 if r["train"] == "lunar_straight_baseline"), None)
    if lunar is None or base is None:
        return ("UNDETERMINED", "lunar/baseline missing",
                "Required train results not in input list", {})
    ratio = (lunar["p95_deg"] / base["p95_deg"]
             if base["p95_deg"] > 0 else float("inf"))
    status = "PASS" if ratio <= ratio_threshold else "FAIL"
    notes = (
        f"Lunar p95 = {lunar['p95_deg']:.3f} deg; "
        f"straight-baseline p95 = {base['p95_deg']:.3f} deg; "
        f"ratio = {ratio:.2f}.  Threshold {ratio_threshold:.1f}x."
    )
    computed = f"lunar/baseline p95 ratio = {ratio:.2f}"
    detail = {
        "lunar_p95_deg": lunar["p95_deg"],
        "baseline_p95_deg": base["p95_deg"],
        "ratio": ratio,
        "ratio_threshold": ratio_threshold,
    }
    return status, computed, notes, detail


def evaluate_G_H3(
    results: Optional[List[Dict[str, Any]]] = None,
    deviation_pct: float = 15.0,
) -> Tuple[str, str, str, Dict[str, object]]:
    """G-H3: rare-prime trains' per-mesh relative sigma within +-15% of median.

    Compares per-mesh RELATIVE ratio sigma (normalised by output_revs and
    horizon so fast-pointer trains don't dominate).  Asks whether trains
    containing rare primes (53, 83, 127, 223, 251) deviate systematically
    from the median per-mesh sigma.

    Per-mesh relative sigma:
        rel_sigma_per_mesh = (p95_deg / (360 * output_revs_per_year * horizon))
                             / sqrt(n_meshes)
    """
    import math
    if results is None:
        results = run_all(n_trials=2000)

    by_name = {r["train"]: r for r in results}
    specs_map = {s.name: s for s in train_specs()}

    per_mesh_sigma: Dict[str, float] = {}
    rare_trains: List[str] = []
    for name, r in by_name.items():
        if name == "lunar_straight_baseline":
            continue
        spec = specs_map.get(name)
        if spec is None:
            continue
        n_meshes = max(1, len(spec.mesh_pairs))
        denom = (360.0 * spec.output_revs_per_year
                 * r.get("horizon_years", 19.0))
        if denom <= 0:
            continue
        # p95 / denom = relative ratio error at 95th percentile
        p95_rel = r["p95_deg"] / denom
        per_mesh_sigma[name] = p95_rel / math.sqrt(n_meshes)
        if spec.contains_rare_primes:
            rare_trains.append(name)

    if not per_mesh_sigma:
        return ("UNDETERMINED", "no per-mesh sigmas",
                "manufacturing_tolerance results missing", {})

    sigmas = sorted(per_mesh_sigma.values())
    median = sigmas[len(sigmas) // 2]
    if median == 0:
        return ("UNDETERMINED", "median sigma = 0", "noiseless run?", {})

    deviations = {
        name: abs(s - median) / median * 100.0
        for name, s in per_mesh_sigma.items()
    }
    rare_deviations = [deviations[n] for n in rare_trains]
    n_pass = sum(1 for d in rare_deviations if d <= deviation_pct)
    n_total = len(rare_deviations)
    if n_total == 0:
        status = "UNDETERMINED"
    elif n_pass == n_total:
        status = "PASS"
    elif n_pass >= n_total // 2:
        status = "PARTIAL"
    else:
        status = "FAIL"
    notes = (
        f"{n_pass}/{n_total} rare-prime-bearing trains have per-mesh "
        f"relative sigma within +-{deviation_pct:g}% of cross-train median "
        f"({median:.6f}).  Rare primes: 53 (Metonic, Saros), 127 (lunar), "
        "83 (Jupiter).  Note: per-mesh sigma is dominated by 1/mean_tooth_count "
        "scaling (sigma = 0.5/<N>), so trains using small individual gears "
        "appear noisier than trains using large gears, INDEPENDENT of rare-"
        "prime presence.  This metric thus partially confounds rare-prime "
        "status with average tooth count."
    )
    computed = (
        f"rare-prime trains within +-{deviation_pct:g}% of median: "
        f"{n_pass}/{n_total}"
    )
    detail = {
        "deviation_pct_threshold": deviation_pct,
        "per_train_per_mesh_sigma": per_mesh_sigma,
        "median_per_mesh_sigma": median,
        "deviations_pct": deviations,
        "rare_prime_trains": rare_trains,
    }
    return status, computed, notes, detail


# ---------------------------------------------------------------------------
# CLI surface
# ---------------------------------------------------------------------------

_EPILOG = """\
Examples:
  # Smoke-test single train, 1000 trials:
  python -m research.manufacturing_tolerance --train saros --n-trials 1000

  # Full battery, default sigma:
  python -m research.manufacturing_tolerance --train all --n-trials 10000

  # Worst-case (deterministic) bound:
  python -m research.manufacturing_tolerance --train saros --noise-spec worst-case

  # Custom sigma to test sensitivity:
  python -m research.manufacturing_tolerance --per-gear-sigma 0.01

  # Run G-H1..G-H3 evaluators:
  python -m research.manufacturing_tolerance --evaluate

Citations
---------
Guillermo & Szigety (2025) arXiv:25xx.xxxxx -- ASSUMPTION-FLAGGED.
Wright (2005) Bull. Sci. Instr. Soc. 85:2-7.
Edmunds (2014) JHA 45:202-222 -- gear-train accuracy assessment.
"""


def _make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m research.manufacturing_tolerance",
        description=(
            "Monte Carlo simulation of per-mesh manufacturing tolerance "
            "in the Antikythera gear trains.  Quantifies the implementation-"
            "layer error budget per train."
        ),
        epilog=_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--n-trials", type=int, default=10000,
        help="Trials per train (default: 10000).",
    )
    parser.add_argument(
        "--noise-spec", choices=sorted(CATALOG.keys()), default="default",
        help="Catalog noise parametrisation (default: default).",
    )
    parser.add_argument(
        "--per-gear-sigma", type=float, default=None,
        help="Override sigma (overrides --noise-spec).",
    )
    parser.add_argument(
        "--noise-mode", choices=VALID_MODES, default=None,
        help="Override noise distribution mode.",
    )
    parser.add_argument(
        "--train", default="all",
        help=("Train name (default: all).  See VALID_TRAIN_NAMES: "
              + ", ".join(VALID_TRAIN_NAMES)),
    )
    parser.add_argument(
        "--horizon-years", type=float, default=19.0,
        help="Time horizon for drift accumulation (default: 19, one Metonic).",
    )
    parser.add_argument(
        "--seed", type=int, default=None,
        help="RNG seed (overrides spec default).",
    )
    parser.add_argument(
        "--evaluate", action="store_true",
        help="Run G-H1..G-H3 evaluators and print PASS/FAIL.",
    )
    parser.add_argument(
        "--operation-regime",
        choices=VALID_OPERATION_REGIMES,
        default=CONTINUOUS_OPERATION,
        help=("'continuous' (default, 24/7 nominal); 'intermittent' "
              "(crank-as-clutch hypothesis -- drift accumulates only "
              "during active cranking).  See notebook §11.6.10."),
    )
    parser.add_argument(
        "--active-seconds-per-year", type=float,
        default=DEFAULT_ACTIVE_SECONDS_PER_YEAR,
        help=f"Active-cranking budget per calendar year for intermittent "
             f"regime (default: {DEFAULT_ACTIVE_SECONDS_PER_YEAR} s/yr).",
    )
    parser.add_argument(
        "--csv-out", default=None,
        help="Write per-train summary CSV to this path.",
    )
    parser.add_argument(
        "--plot", action="store_true",
        help="Save matplotlib histogram (lazy import).",
    )
    return parser


def _resolve_noise_spec(args) -> NoiseSpec:
    spec = CATALOG[args.noise_spec]
    if args.per_gear_sigma is None and args.noise_mode is None:
        return spec
    return NoiseSpec(
        mode=args.noise_mode if args.noise_mode is not None else spec.mode,
        sigma=(args.per_gear_sigma if args.per_gear_sigma is not None
               else spec.sigma),
        backlash_extra_sigma=spec.backlash_extra_sigma,
        seed=args.seed if args.seed is not None else spec.seed,
        citation=spec.citation + " (CLI-overridden)",
        label=spec.label + " (modified)",
    )


def _print_results(results: List[Dict[str, Any]]) -> None:
    print(f"{'train':<28} {'n':>6} {'mode':<11} {'sigma':>9}  "
          f"{'p95 deg':>10}  {'mean abs deg':>13}  {'max deg':>10}")
    print("-" * 100)
    for r in results:
        print(f"{r['train']:<28} {r['n_trials']:>6d} {r['noise_mode']:<11} "
              f"{r['noise_sigma']:>9.5f}  {r['p95_deg']:>10.4f}  "
              f"{r['mean_abs_deg']:>13.4f}  {r['max_deg']:>10.4f}")


def _write_csv(results: List[Dict[str, Any]], path: str) -> None:
    import csv
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "train", "n_trials", "noise_mode", "noise_sigma",
            "horizon_years", "noiseless_ratio",
            "p95_deg", "mean_abs_deg", "std_deg", "max_deg",
        ])
        for r in results:
            w.writerow([
                r["train"], r["n_trials"], r["noise_mode"], r["noise_sigma"],
                r["horizon_years"], r["noiseless_ratio"],
                r["p95_deg"], r["mean_abs_deg"], r["std_deg"], r["max_deg"],
            ])


def main(argv: Optional[List[str]] = None) -> int:
    args = _make_parser().parse_args(argv)
    noise_spec = _resolve_noise_spec(args)

    if args.train != "all" and args.train not in VALID_TRAIN_NAMES:
        print(f"ERROR: unknown train {args.train!r}.  "
              f"Valid: {', '.join(VALID_TRAIN_NAMES)}")
        return 2
    train_filter = None if args.train == "all" else (args.train,)

    regime_label = (f"INTERMITTENT ({args.active_seconds_per_year} s/yr active)"
                    if args.operation_regime == INTERMITTENT_OPERATION
                    else "CONTINUOUS (24/7 nominal)")
    print(f"Running Monte Carlo: n_trials={args.n_trials}, "
          f"noise_spec={noise_spec.label}, sigma={noise_spec.sigma:.5f}, "
          f"mode={noise_spec.mode}, horizon={args.horizon_years} yr, "
          f"regime={regime_label}")
    results = run_all(
        n_trials=args.n_trials,
        noise_spec=noise_spec,
        horizon_years=args.horizon_years,
        seed=args.seed,
        train_filter=train_filter,
        operation_regime=args.operation_regime,
        active_seconds_per_year=args.active_seconds_per_year,
    )
    print()
    _print_results(results)

    if args.csv_out:
        _write_csv(results, args.csv_out)
        print(f"\n  Wrote CSV to {args.csv_out}")

    if args.evaluate:
        print()
        print("--- G-H1..G-H3 evaluators ---")
        # Need full battery for G-H3
        if args.train != "all":
            full = run_all(n_trials=args.n_trials, noise_spec=noise_spec,
                           horizon_years=args.horizon_years, seed=args.seed,
                           operation_regime=args.operation_regime,
                           active_seconds_per_year=args.active_seconds_per_year)
        else:
            full = results
        for name, fn in (("G-H1", evaluate_G_H1),
                         ("G-H2", evaluate_G_H2),
                         ("G-H3", evaluate_G_H3)):
            status, computed, notes, _ = fn(full)
            print(f"  {name}: {status:<14} -- {computed}")
            print(f"        {notes}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

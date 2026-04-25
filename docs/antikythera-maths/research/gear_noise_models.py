"""Gear noise model SSOT — frozen dataclasses + epsilon samplers.

Bronze gears cut by 2nd-century BCE Greek workshops carried fractional-
tooth imprecision.  A single mesh introduces a small multiplicative
ratio error; across a 6-10 mesh planetary train these errors compound.
This module is the SSOT for the noise parametrisations consumed by
``manufacturing_tolerance.py``.

The noise model is **multiplicative** rather than integer-perturbed:
each mesh ``(n_driver, n_driven)`` produces an effective ratio of
``(n_driver / n_driven) * (1 + epsilon)`` where ``epsilon`` is drawn
from a chosen distribution.  Multiplicative noise preserves the
integer abstraction of tooth counts while modelling the *physical*
slop (tooth-pitch eccentricity, axis misalignment, backlash).

Three sampling modes are supported:

    gaussian      epsilon ~ N(0, sigma^2)
    uniform       epsilon ~ U(-sigma*sqrt(3), +sigma*sqrt(3))   (matched variance)
    worst-case    epsilon = +sigma or -sigma deterministically; signs
                  chosen to maximise cumulative error along the chain.

The default ``sigma`` parameter is calibrated to the empirical tolerance
band of bronze gear-cutting: roughly +-0.5 tooth's worth of pitch error
across an N-tooth wheel translates to ``sigma = 0.5 / N``.  The default
``GUILLERMO_SZIGETY_2025_DEFAULT`` uses ``sigma = 0.5/60`` (mid-train
gear count) but ``manufacturing_tolerance.sample_train_ratio`` picks a
per-mesh sigma scaled by the actual mean tooth count of the meshing
pair.

Citation
--------
Szigety, E. & Arenas, G. F. (2025).  The Impact of Triangular-Toothed
    Gears on the Functionality of the Antikythera Mechanism.
    arXiv:2504.00327 [physics.hist-ph].
Edmunds, M. G. (2014).  An initial assessment of the accuracy of the
    gear trains in the Antikythera Mechanism.  J. Hist. Astron. 45:202.

The Szigety & Arenas 2025 paper combines Thorndike's analytical
solution for triangular-tooth non-uniform motion with Edmunds 2014's
manufacturing-error model.  Their headline: under realistic tolerance
the mechanism would jam within ~120 days of operation.  Our G-H1
finding (~13 deg / 19 yr Saros drift under sigma = 0.5/<n>) reads the
same physical situation through the angular-error rather than the
engagement-loss metric.

The ``GUILLERMO_SZIGETY_2025_DEFAULT`` constant name is preserved for
back-compat; the citation now points at the correct paper.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from typing import Any, List, Optional, Tuple


VALID_MODES: Tuple[str, ...] = ("gaussian", "uniform", "worst-case")


@dataclass(frozen=True)
class NoiseSpec:
    """One parametrisation of the per-mesh noise model."""

    mode: str
    """``'gaussian'`` | ``'uniform'`` | ``'worst-case'``."""

    sigma: float
    """Standard deviation of epsilon (relative ratio error per mesh).
    For default bronze tolerance, sigma ~ 0.5 / mean_tooth_count."""

    backlash_extra_sigma: float = 0.0
    """Reserved for future second-order effects (axis misalignment,
    eccentricity-driven harmonic).  Currently a placeholder; manufacturing_
    tolerance.py adds this in quadrature to ``sigma`` if non-zero."""

    seed: int = 42
    """Default RNG seed if the caller does not supply one."""

    citation: str = ""
    """Source for this parameter choice."""

    label: str = ""
    """Human-readable identifier for tables and plots."""


# ---------------------------------------------------------------------------
# Calibrated parametrisations
# ---------------------------------------------------------------------------

GUILLERMO_SZIGETY_2025_DEFAULT: NoiseSpec = NoiseSpec(
    mode="gaussian",
    sigma=0.5 / 60.0,  # ~+-0.5 tooth across mid-size gear
    backlash_extra_sigma=0.0,
    seed=42,
    citation="Szigety & Arenas 2025 (arXiv:2504.00327)",
    label="Guillermo-Szigety 2025 default",
)
"""Working assumption: +-0.5 tooth standard deviation per mesh, scaled
by mean tooth count.  ASSUMPTION-FLAGGED until the paper is read."""


CONSERVATIVE_BRONZE_BOUND: NoiseSpec = NoiseSpec(
    mode="gaussian",
    sigma=0.01,  # 1% per mesh — strict bronze workshop
    backlash_extra_sigma=0.0,
    seed=43,
    citation="Conservative reading of Wright 2005 + Edmunds 2014 wear analysis",
    label="Conservative bronze bound (sigma=0.01)",
)


LIBERAL_BRONZE_BOUND: NoiseSpec = NoiseSpec(
    mode="gaussian",
    sigma=0.05,  # 5% per mesh — degraded / aged mechanism
    backlash_extra_sigma=0.0,
    seed=44,
    citation="Liberal upper-bound for surviving bronze tolerance",
    label="Liberal bronze bound (sigma=0.05)",
)


WORST_CASE_DETERMINISTIC: NoiseSpec = NoiseSpec(
    mode="worst-case",
    sigma=0.5 / 60.0,
    backlash_extra_sigma=0.0,
    seed=0,
    citation="Worst-case deterministic bound (signs chosen adversarially)",
    label="Worst-case deterministic",
)


CATALOG = {
    "default": GUILLERMO_SZIGETY_2025_DEFAULT,
    "conservative": CONSERVATIVE_BRONZE_BOUND,
    "liberal": LIBERAL_BRONZE_BOUND,
    "worst-case": WORST_CASE_DETERMINISTIC,
}


# ---------------------------------------------------------------------------
# Sampling
# ---------------------------------------------------------------------------

def _effective_sigma(spec: NoiseSpec) -> float:
    """Combine ``sigma`` and ``backlash_extra_sigma`` in quadrature."""
    if spec.backlash_extra_sigma == 0.0:
        return spec.sigma
    return float((spec.sigma ** 2 + spec.backlash_extra_sigma ** 2) ** 0.5)


def sample_epsilon(
    spec: NoiseSpec,
    n: int,
    rng: Optional[Any] = None,
) -> Any:
    """Draw ``n`` epsilon samples per ``spec``.

    Returns a numpy array of length ``n``.  ``numpy`` is imported lazily
    so the SSOT module stays fast to import in test contexts that don't
    need the simulator.
    """
    import numpy as np

    if rng is None:
        rng = np.random.default_rng(spec.seed)
    sig = _effective_sigma(spec)
    if spec.mode == "gaussian":
        return rng.normal(loc=0.0, scale=sig, size=n)
    if spec.mode == "uniform":
        # uniform(-a, a) has variance a^2 / 3 -> a = sigma * sqrt(3)
        a = sig * (3.0 ** 0.5)
        return rng.uniform(low=-a, high=a, size=n)
    if spec.mode == "worst-case":
        # +sigma everywhere; manufacturing_tolerance flips signs
        # adversarially per chain to maximise cumulative drift.
        return np.full(n, sig, dtype=float)
    raise ValueError(f"Unknown mode {spec.mode!r}; expected one of {VALID_MODES}")


def sample_epsilon_for_meshes(
    spec: NoiseSpec,
    mean_tooth_counts: Any,
    rng: Optional[Any] = None,
) -> Any:
    """Per-mesh epsilon scaled by 1/mean_tooth_count.

    The default ``spec.sigma`` of ``0.5/60`` is calibrated for a 60-tooth
    gear; for a 224-tooth gear the per-mesh sigma should be smaller
    (smaller relative pitch error).  This helper rescales sigma per
    mesh so each mesh's effective sigma is ``0.5 / mean_tooth_count``.
    """
    import numpy as np

    arr = np.asarray(mean_tooth_counts, dtype=float)
    if rng is None:
        rng = np.random.default_rng(spec.seed)
    sig_per_mesh = 0.5 / arr  # scale rule
    if spec.mode == "gaussian":
        return rng.normal(0.0, sig_per_mesh)
    if spec.mode == "uniform":
        a = sig_per_mesh * (3.0 ** 0.5)
        return rng.uniform(-a, a)
    if spec.mode == "worst-case":
        return sig_per_mesh.copy()
    raise ValueError(f"Unknown mode {spec.mode!r}")


# ---------------------------------------------------------------------------
# CLI surface
# ---------------------------------------------------------------------------

_EPILOG = """\
Examples:
  # Show the catalog of parametrisations:
  python -m research.gear_noise_models --list

  # Sample 5 epsilons from the default Guillermo-Szigety 2025 model:
  python -m research.gear_noise_models --spec default --n 5

  # Sample worst-case sign for a chain of meshes with given mean teeth:
  python -m research.gear_noise_models --spec worst-case \\
        --mean-tooth-counts 224,32,53,96

Citations
---------
Guillermo & Szigety (2025) arXiv:25xx.xxxxx -- ASSUMPTION-FLAGGED
   until paper is read.
Wright (2005) "The Antikythera Mechanism: a new gearing scheme",
   Bull. Sci. Instr. Soc. 85:2-7.
"""


def _make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m research.gear_noise_models",
        description=(
            "Frozen-data SSOT for per-gear manufacturing-tolerance noise "
            "specs.  Inspect the catalog or sample an epsilon vector."
        ),
        epilog=_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--list", action="store_true",
        help="Print the noise-spec catalog.",
    )
    parser.add_argument(
        "--spec", choices=sorted(CATALOG.keys()), default="default",
        help="Which catalog entry to use for sampling.",
    )
    parser.add_argument(
        "--n", type=int, default=5,
        help="Number of epsilon samples to draw (default: 5).",
    )
    parser.add_argument(
        "--mean-tooth-counts", default=None,
        help=("Comma-separated mean tooth counts for per-mesh scaling. "
              "When given, draws one epsilon per mesh."),
    )
    parser.add_argument(
        "--seed", type=int, default=None,
        help="Override the spec's default RNG seed.",
    )
    return parser


def _print_catalog() -> None:
    print(f"{'key':<14} {'mode':<11} {'sigma':>9}  {'label':<35}  citation")
    print("-" * 110)
    for key in sorted(CATALOG.keys()):
        spec = CATALOG[key]
        print(f"{key:<14} {spec.mode:<11} {spec.sigma:>9.5f}  "
              f"{spec.label:<35}  {spec.citation[:50]}")


def main(argv: Optional[List[str]] = None) -> int:
    args = _make_parser().parse_args(argv)

    if args.list:
        _print_catalog()
        return 0

    spec = CATALOG[args.spec]
    if args.seed is not None:
        # NoiseSpec is frozen; reconstitute with new seed
        spec = NoiseSpec(
            mode=spec.mode,
            sigma=spec.sigma,
            backlash_extra_sigma=spec.backlash_extra_sigma,
            seed=args.seed,
            citation=spec.citation,
            label=spec.label,
        )

    if args.mean_tooth_counts:
        try:
            counts = [int(x) for x in args.mean_tooth_counts.split(",")]
        except ValueError as exc:
            print(f"ERROR: --mean-tooth-counts must be comma-separated ints "
                  f"({exc}).")
            return 2
        eps = sample_epsilon_for_meshes(spec, counts)
        print(f"Per-mesh epsilon for spec={args.spec!r} "
              f"(mode={spec.mode}, sigma scaled per mesh):")
        for n, e in zip(counts, eps):
            print(f"  N={n:>4d}  eps={e:+.6f}")
    else:
        eps = sample_epsilon(spec, args.n)
        print(f"Drew {args.n} epsilons from spec={args.spec!r} "
              f"(mode={spec.mode}, sigma={spec.sigma}):")
        for i, e in enumerate(eps):
            print(f"  [{i}] {e:+.6f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Astronomical cycles — the "channel" layout for encode_Ant.

Each row of ``CYCLES`` is one dial (channel) of the mechanism, with:
- ``name``: human / dial identifier.
- ``numerator, denominator``: integer encoding of the commensurability
  the mechanism uses.  E.g. Metonic: (235, 19) = 235 synodic months per
  19 tropical years.
- ``modern_days``: the cycle length in SI days per modern ephemeris
  (for residual checks in Phase 0).
- ``mechanism_days``: the cycle length as the mechanism encodes it
  (either from the numerator/denominator ratio or from an explicit
  astronomical integer like 223 synodic months).
- ``prime_factors_num``, ``prime_factors_den``: precomputed for the
  A-H2 / A-H3 hypotheses.
- ``notes``: provenance.

This file is the SSOT for cycle definitions.  All other research
modules import from here; no cycle length is redefined anywhere else.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import gcd
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Astronomical constants (SI days).  Sources:
# - Synodic month: 29.530588861 d (IAU/modern lunar theory).
# - Tropical year: 365.24219 d.
# - Saros cycle: 6585.3211 d (= 223 synodic months to high precision).
# - Callippic cycle: 27758.78 d (= 76 tropical years - 1 day).
# - Metonic cycle: 6939.688 d.
# - Exeligmos: 19755.96 d (= 3 Saros).
# - Draconic month: 27.21222 d (used for eclipse / node calculations).
# - Anomalistic month: 27.55455 d (used for lunar pin-and-slot).
# - Sidereal month: 27.32166 d.
# ---------------------------------------------------------------------------

SYNODIC_MONTH_DAYS = 29.530588861
TROPICAL_YEAR_DAYS = 365.24219
SAROS_DAYS = 6585.3211
CALLIPPIC_DAYS = 27758.78
METONIC_DAYS = 6939.688
EXELIGMOS_DAYS = 3 * SAROS_DAYS
DRACONIC_MONTH_DAYS = 27.21222
ANOMALISTIC_MONTH_DAYS = 27.55455
SIDEREAL_MONTH_DAYS = 27.32166

# Planetary synodic periods (modern, SI days):
MERCURY_SYNODIC_DAYS = 115.88
VENUS_SYNODIC_DAYS = 583.92
MARS_SYNODIC_DAYS = 779.94
JUPITER_SYNODIC_DAYS = 398.88
SATURN_SYNODIC_DAYS = 378.09


# ---------------------------------------------------------------------------
# Prime factorization — tiny pure-Python (no sympy dep for this helper).
# ---------------------------------------------------------------------------

def prime_factors(n: int) -> List[int]:
    """Ordered list of prime factors (with multiplicity) of n > 0."""
    if n < 1:
        raise ValueError(f"prime_factors requires positive int, got {n}")
    out: List[int] = []
    d = 2
    while d * d <= n:
        while n % d == 0:
            out.append(d)
            n //= d
        d += 1
    if n > 1:
        out.append(n)
    return out


def prime_factor_set(n: int) -> set:
    return set(prime_factors(n)) if n > 0 else set()


# ---------------------------------------------------------------------------
# Cycle dataclass
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Cycle:
    name: str
    numerator: int
    denominator: int
    modern_days: Optional[float]
    mechanism_days: Optional[float]
    notes: str = ""
    tag: str = ""  # free-form category: "lunar", "planetary", "calendar", "eclipse"

    @property
    def num_factors(self) -> List[int]:
        return prime_factors(self.numerator) if self.numerator > 0 else []

    @property
    def den_factors(self) -> List[int]:
        return prime_factors(self.denominator) if self.denominator > 0 else []

    @property
    def reduced(self) -> Tuple[int, int]:
        if self.numerator <= 0 or self.denominator <= 0:
            return (self.numerator, self.denominator)
        g = gcd(self.numerator, self.denominator)
        return (self.numerator // g, self.denominator // g)

    @property
    def residual_days(self) -> Optional[float]:
        """Modern - mechanism (days), if both are populated."""
        if self.modern_days is None or self.mechanism_days is None:
            return None
        return self.modern_days - self.mechanism_days


# ---------------------------------------------------------------------------
# Cycle catalog
# ---------------------------------------------------------------------------
# Each cycle is the mechanism's numerator/denominator encoding, where
# available.  For dials where the mechanism does not encode a ratio
# explicitly (e.g. Mars, where the Greeks lacked equants), we store
# the period-relation Freeth 2021 proposes.

CYCLES: List[Cycle] = [
    Cycle(
        name="Metonic",
        numerator=235,
        denominator=19,
        modern_days=19 * TROPICAL_YEAR_DAYS,
        mechanism_days=235 * SYNODIC_MONTH_DAYS,
        notes="19 tropical years = 235 synodic months.  "
              "Mechanism encodes this exactly via the e-series (53, 96, 53).",
        tag="calendar",
    ),
    Cycle(
        name="Callippic",
        numerator=940,
        denominator=76,
        modern_days=76 * TROPICAL_YEAR_DAYS,
        mechanism_days=940 * SYNODIC_MONTH_DAYS,
        notes="4 Metonic cycles = 76 years.  Improves the Metonic approximation.",
        tag="calendar",
    ),
    Cycle(
        name="Olympic",
        numerator=4,
        denominator=1,
        modern_days=4 * TROPICAL_YEAR_DAYS,
        mechanism_days=4 * TROPICAL_YEAR_DAYS,
        notes="Panhellenic games — 4-year Olympiad dial.",
        tag="calendar",
    ),
    Cycle(
        name="Saros",
        numerator=223,
        denominator=19,   # 223 synodic = 19 eclipse years (approximately)
        modern_days=223 * SYNODIC_MONTH_DAYS,
        mechanism_days=223 * SYNODIC_MONTH_DAYS,
        notes="Eclipse cycle.  223 is prime — genuine celestial-mechanics "
              "fact, not a design choice.",
        tag="eclipse",
    ),
    Cycle(
        name="Exeligmos",
        numerator=669,
        denominator=3,
        modern_days=3 * SAROS_DAYS,
        mechanism_days=669 * SYNODIC_MONTH_DAYS,
        notes="3 Saros = 54 years.  Aligns eclipses to same time of day.",
        tag="eclipse",
    ),
    Cycle(
        name="SiderealMonth",
        numerator=254,
        denominator=19,
        modern_days=19 * TROPICAL_YEAR_DAYS,
        mechanism_days=254 * SIDEREAL_MONTH_DAYS,
        notes="254 sidereal months in 19 tropical years (via 127-tooth gear = 254/2).",
        tag="lunar",
    ),
    Cycle(
        name="DraconicMonth",
        numerator=242,
        denominator=19,
        modern_days=19 * TROPICAL_YEAR_DAYS,
        mechanism_days=242 * DRACONIC_MONTH_DAYS,
        notes="Node-regression cycle; 242 draconic months ~ 19 years.  "
              "Embedded implicitly in Saros eclipse prediction.",
        tag="lunar",
    ),
    Cycle(
        name="LunarAnomaly",
        numerator=251,
        denominator=19,
        modern_days=19 * TROPICAL_YEAR_DAYS,
        mechanism_days=251 * ANOMALISTIC_MONTH_DAYS,
        notes="Anomalistic-month cycle encoded by the pin-and-slot epicycle.  "
              "251 anomalistic ~ 269 synodic months ~ 8.85 years period.",
        tag="lunar",
    ),
    # Planetary — (synodic-return, sidereal-return) period relations.
    # Freeth 2021 proposes these as the factor choices for the lost
    # planetary trains.
    Cycle(
        name="Mercury_synodic_period_relation",
        numerator=145,
        denominator=46,
        modern_days=46 * TROPICAL_YEAR_DAYS,
        mechanism_days=145 * MERCURY_SYNODIC_DAYS,
        notes="Freeth 2021 proposed (145, 46).  145 = 5·29, 46 = 2·23.",
        tag="planetary",
    ),
    Cycle(
        name="Venus_synodic_period_relation",
        numerator=289,
        denominator=462,  # 289 synodic returns in 462 years
        modern_days=462 * TROPICAL_YEAR_DAYS,
        mechanism_days=289 * VENUS_SYNODIC_DAYS,
        notes="Freeth 2021 proposed (289, 462).  289 = 17^2; 462 = 2·3·7·11.  "
              "Shared factor 7 with Mars, shared factor 17 with Saturn.",
        tag="planetary",
    ),
    Cycle(
        name="Mars_synodic_period_relation",
        numerator=133,
        denominator=125,
        modern_days=125 * MARS_SYNODIC_DAYS,
        mechanism_days=133 * MARS_SYNODIC_DAYS,
        notes="Freeth 2021 proposed (133, 125) for Mars.  Here the "
              "denominator 125 is itself 125 Mars-sidereal returns rather than "
              "125 tropical years (the deeply ambiguous case since Greek "
              "Martian theory mixed returns and years).  "
              "133 = 7·19; shared factor 7 with Venus.  "
              "Mars is the 'intentionally wrong' dial — no equant in Greek theory; "
              "the residual here is dominated by the equant-less epicycle model.",
        tag="planetary",
    ),
    Cycle(
        name="Jupiter_synodic_period_relation",
        numerator=76,
        denominator=83,
        modern_days=83 * TROPICAL_YEAR_DAYS,
        mechanism_days=76 * JUPITER_SYNODIC_DAYS,
        notes="Freeth 2021 proposed (76, 83).  76 = 4·19; 83 prime.",
        tag="planetary",
    ),
    Cycle(
        name="Saturn_synodic_period_relation",
        numerator=427,
        denominator=442,
        modern_days=442 * TROPICAL_YEAR_DAYS,
        mechanism_days=427 * SATURN_SYNODIC_DAYS,
        notes="Freeth 2021 proposed (427, 442).  427 = 7·61; 442 = 2·13·17.  "
              "Shared factor 17 with Venus (289 = 17^2).",
        tag="planetary",
    ),
]


def cycle_by_name(name: str) -> Cycle:
    for c in CYCLES:
        if c.name == name:
            return c
    raise KeyError(f"Unknown cycle: {name!r}")


def all_prime_factors() -> List[int]:
    """All prime factors appearing in numerator or denominator, sorted, unique."""
    s: set = set()
    for c in CYCLES:
        s.update(c.num_factors)
        s.update(c.den_factors)
    return sorted(s)


def shared_primes_among_planetary() -> Dict[int, List[str]]:
    """Which primes appear in >1 planetary period-relation?  A-H2 load-bearing."""
    out: Dict[int, List[str]] = {}
    planetary = [c for c in CYCLES if c.tag == "planetary"]
    for c in planetary:
        for p in set(c.num_factors) | set(c.den_factors):
            out.setdefault(p, []).append(c.name)
    return {p: names for p, names in out.items() if len(names) > 1}


_EPILOG = """\
Examples:
  # Default: full per-cycle residuals + shared planetary primes:
  python -m research.astronomical_cycles

  # Filter to one tag:
  python -m research.astronomical_cycles --tag planetary

  # Lookup one cycle by name:
  python -m research.astronomical_cycles --cycle Saros

  # Just the shared-primes histogram:
  python -m research.astronomical_cycles --shared-primes

Citations
---------
Toomer, G. J. (1984). Ptolemy's Almagest. Princeton.
Neugebauer, O. (1975). A History of Ancient Mathematical Astronomy.
    Springer (3 vols).
"""


def _make_parser():
    import argparse
    parser = argparse.ArgumentParser(
        prog="python -m research.astronomical_cycles",
        description=("Astronomical cycle SSOT -- 13 commensurability "
                     "ratios spanning calendar, eclipse, lunar, and "
                     "planetary periods.  Drives the encoder and the "
                     "Pareto / packing analyses."),
        epilog=_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--tag", default=None,
        choices=("calendar", "eclipse", "lunar", "planetary"),
        help="Filter to cycles with the given tag.",
    )
    parser.add_argument(
        "--cycle", default=None,
        help="Print just the cycle with this name and exit.",
    )
    parser.add_argument(
        "--shared-primes", action="store_true",
        help="Print only the planetary shared-primes histogram.",
    )
    return parser


def main(argv=None):
    args = _make_parser().parse_args(argv)

    if args.cycle:
        for c in CYCLES:
            if c.name == args.cycle:
                print(f"{c.name}: {c.numerator}/{c.denominator}  tag={c.tag}")
                if c.modern_days is not None:
                    print(f"  modern_days    = {c.modern_days:.3f}")
                if c.mechanism_days is not None:
                    print(f"  mechanism_days = {c.mechanism_days:.3f}")
                if c.residual_days is not None:
                    print(f"  residual_days  = {c.residual_days:.3f}")
                print(f"  notes: {c.notes}")
                return 0
        print(f"No cycle named {args.cycle!r}")
        return 1

    if args.shared_primes:
        for p, names in sorted(shared_primes_among_planetary().items()):
            print(f"  p = {p}: shared by "
                  f"{', '.join(n.split('_')[0] for n in names)}")
        return 0

    cycles = CYCLES if args.tag is None else [c for c in CYCLES
                                              if c.tag == args.tag]
    print(f"Cycles:            {len(cycles)} "
          f"(tag filter: {args.tag or 'all'})")
    print(f"All prime factors: {all_prime_factors()}")
    print()
    print("Per-cycle residuals (mechanism vs modern, days):")
    print(f"  {'cycle':30s} {'num/den':>14s} {'mech_d':>14s} "
          f"{'mod_d':>14s} {'err_d':>10s}")
    for c in cycles:
        if c.modern_days is not None and c.mechanism_days is not None:
            print(f"  {c.name:30s} {c.numerator:>6d}/{c.denominator:<7d} "
                  f"{c.mechanism_days:14.3f} {c.modern_days:14.3f} "
                  f"{c.residual_days:10.3f}")
    print()
    print("Shared primes across planetary trains (A-H2 load-bearing):")
    for p, names in sorted(shared_primes_among_planetary().items()):
        print(f"  p = {p}: shared by "
              f"{', '.join(n.split('_')[0] for n in names)}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

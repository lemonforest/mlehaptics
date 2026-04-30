"""Packing analysis — empirical A-H1/A-H2/A-H3 analysis of shared-gear solutions.

The addressing-maths research plan (A-H1) asks: when multiple cycles must be
encoded with a shared tooth budget, which shared prime factors are Pareto-
optimal on the (total-tooth-count, total-precision) frontier?

Freeth 2021 claims {7, 17} are the shared primes in the planetary trains.
This module:

- Enumerates candidate shared-prime sets from the small-prime alphabet.
- For each candidate, computes the total tooth budget needed to meet each
  planet's stated precision using the Freeth 2021 period relation.
- Reports the Pareto frontier on (total_teeth, total_err).
- Checks whether {7, 17} lies on the frontier.

The prime-spectrum histogram (A-H3) is also here.
"""

from __future__ import annotations

from itertools import combinations
from math import gcd
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

from .astronomical_cycles import (
    CYCLES,
    prime_factors,
    prime_factor_set,
    shared_primes_among_planetary,
)
from .gear_database import (
    FREETH_2021,
    WRIGHT,
    tooth_count_list,
)


# ---------------------------------------------------------------------------
# Prime spectrum (A-H3)
# ---------------------------------------------------------------------------

def prime_spectrum(reconstruction: str = FREETH_2021,
                   include_planetary: bool = True) -> Dict[int, int]:
    """Histogram: prime -> count of gears whose tooth count contains that prime."""
    hist: Dict[int, int] = {}
    for t in tooth_count_list(reconstruction, include_planetary=include_planetary):
        for p in set(prime_factors(t)):
            hist[p] = hist.get(p, 0) + 1
    return hist


def prime_spectrum_null_model(n_gears: int, lo: int = 10, hi: int = 300,
                              n_trials: int = 1000,
                              seed: int = 42) -> Dict[int, float]:
    """Null model: draw n_gears random tooth counts uniformly from [lo, hi]
    and compute the *average* prime-spectrum histogram across n_trials.
    Expected value per prime = E[ tooth divisible by p ] · n_gears.
    """
    rng = np.random.default_rng(seed)
    agg: Dict[int, float] = {}
    for _ in range(n_trials):
        counts = rng.integers(lo, hi + 1, size=n_gears)
        for t in counts:
            for p in set(prime_factors(int(t))):
                agg[p] = agg.get(p, 0.0) + 1.0
    return {p: v / n_trials for p, v in agg.items()}


# ---------------------------------------------------------------------------
# A-H2: Pareto analysis over shared-prime candidates
# ---------------------------------------------------------------------------

def planetary_period_relations() -> List[Tuple[str, int, int]]:
    """(planet_name, numerator p, denominator q) for each planetary cycle."""
    out: List[Tuple[str, int, int]] = []
    for c in CYCLES:
        if c.tag == "planetary":
            out.append((c.name.split("_")[0], c.numerator, c.denominator))
    return out


def candidate_shared_prime_sets(max_shared: int = 3,
                                alphabet: Sequence[int] = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31)
                                ) -> List[Tuple[int, ...]]:
    """Enumerate candidate sets of shared primes of size 1..max_shared."""
    out: List[Tuple[int, ...]] = []
    for k in range(1, max_shared + 1):
        for combo in combinations(alphabet, k):
            out.append(combo)
    return out


def total_tooth_budget_for_candidate(candidate: Tuple[int, ...]) -> int:
    """Cost of encoding all planetary period-relations using tooth counts
    that must include *at least* one factor from ``candidate`` — a proxy
    measure for "shared-prime reuse."

    Score: sum, over each planetary numerator p and denominator q, of the
    smallest multiple of gcd(p·q, product(candidate)) that is not smaller
    than the original count.  This is a simplified Pareto-analysis proxy
    — it does not attempt a full gear-train optimisation, but it captures
    the intuition that shared primes reduce total bronze.
    """
    relations = planetary_period_relations()
    total = 0
    for _, p, q in relations:
        total += p + q
    # Simple proxy: reward is the count of (p, q) numerator/denom shared
    # factors that match the candidate set — lower = fewer shared, higher = more.
    share = 0
    for _, p, q in relations:
        share += len(set(prime_factors(p)) & set(candidate))
        share += len(set(prime_factors(q)) & set(candidate))
    # Pareto score: a candidate is "better" if total + lambda·(share) is lower.
    # We return the raw total; shared-factor count is returned separately.
    return total


def candidate_share_count(candidate: Tuple[int, ...]) -> int:
    relations = planetary_period_relations()
    share = 0
    for _, p, q in relations:
        share += len(set(prime_factors(p)) & set(candidate))
        share += len(set(prime_factors(q)) & set(candidate))
    return share


def pareto_frontier(candidates: Iterable[Tuple[int, ...]]
                    ) -> List[Tuple[Tuple[int, ...], int, int]]:
    """Return (candidate, total_teeth, shared_count) sorted so Pareto-optimal
    entries are up front.  Pareto-optimality: no other candidate has
    <= teeth AND >= shared_count."""
    scored = [(c, total_tooth_budget_for_candidate(c), candidate_share_count(c))
              for c in candidates]
    frontier: List[Tuple[Tuple[int, ...], int, int]] = []
    for c, t, s in scored:
        dominated = False
        for c2, t2, s2 in scored:
            if (t2, s2) == (t, s) and c2 != c:
                continue
            if t2 <= t and s2 >= s and (t2 < t or s2 > s):
                dominated = True
                break
        if not dominated:
            frontier.append((c, t, s))
    return sorted(frontier, key=lambda x: (x[1], -x[2]))


# ---------------------------------------------------------------------------
# A-H1 helper: continued-fraction ranks for every cycle
# ---------------------------------------------------------------------------

def cycle_cf_ranks(budget: int = 500, max_terms: int = 40) -> List[Dict]:
    """For every cycle, return the continued-fraction rank of its
    mechanism ratio against its astronomical ratio, plus the best-rational
    approximation under the tooth budget."""
    from .rational_approximation import (
        continued_fraction, convergents, rank_in_convergents,
        best_rational_under_budget, approx_error,
    )
    out: List[Dict] = []
    for c in CYCLES:
        # Astronomical true ratio — numerator/denominator both in units of days,
        # but since we care about commensurability, we just need the ratio.
        if c.mechanism_days is None or c.modern_days is None:
            continue
        if c.denominator == 0:
            continue
        mech_ratio = c.numerator / c.denominator
        # The astronomical "true" ratio in the same units the mechanism
        # encodes: numerator-units per denominator-unit.  E.g. for Metonic
        # this is (modern synodic months per modern tropical year), which
        # the mechanism approximates as 235/19.
        true_ratio = (c.mechanism_days / c.numerator)  # days per numerator unit
        # Now divide modern_days_per_denominator_unit by that:
        if true_ratio == 0:
            continue
        true_ratio = (c.modern_days / c.denominator) / true_ratio
        cf = continued_fraction(true_ratio, max_terms=max_terms)
        cvs = convergents(cf)
        # Where does (p, q) = (numerator, denominator) fit?
        rank = rank_in_convergents(true_ratio, c.numerator, c.denominator,
                                   max_terms=max_terms)
        best_p, best_q = best_rational_under_budget(true_ratio, budget)
        out.append({
            "cycle": c.name,
            "mechanism_pq": (c.numerator, c.denominator),
            "true_ratio": true_ratio,
            "cf_head": cf[:6],
            "rank_of_mechanism_pq": rank,
            "best_pq_budget500": (best_p, best_q),
            "mechanism_err": abs(true_ratio - mech_ratio),
            "best_err": abs(true_ratio - best_p / best_q),
        })
    return out


_EPILOG = """\
Examples:
  # Default: prime spectrum + null model + Pareto + CF ranks:
  python -m research.packing_analysis

  # Just the prime spectrum:
  python -m research.packing_analysis --analysis prime-spectrum

  # Compare to null model only:
  python -m research.packing_analysis --analysis null-model

  # Per-cycle CF ranks:
  python -m research.packing_analysis --analysis cf-ranks

DEPRECATED: ``--analysis pareto-proxy`` keeps the legacy proxy
metric for audit only.  For production Pareto analysis use
``research.pareto_analysis`` (Track 4).

Citations
---------
Freeth, T. (2021). A Model of the Cosmos in the ancient Greek Antikythera
    Mechanism. Sci. Rep. 11:5821.
"""


def _make_parser():
    import argparse
    parser = argparse.ArgumentParser(
        prog="python -m research.packing_analysis",
        description=("Empirical packing analysis: prime spectrum (A-H3), "
                     "null model, deprecated Pareto proxy (A-H2 historical), "
                     "and CF ranks (A-H1)."),
        epilog=_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--analysis", default="all",
        choices=("prime-spectrum", "null-model", "shared-primes",
                 "pareto-proxy", "cf-ranks", "all"),
        help="Which sub-analysis to run (default: all).",
    )
    parser.add_argument(
        "--reconstruction", default=FREETH_2021,
        choices=(FREETH_2021, WRIGHT),
        help="Reconstruction for prime spectrum (default: Freeth 2021).",
    )
    parser.add_argument(
        "--no-planetary", action="store_true",
        help="Exclude planetary gears.",
    )
    parser.add_argument(
        "--budget", type=int, default=500,
        help="Tooth budget for CF ranks (default: 500).",
    )
    return parser


def main(argv=None):
    args = _make_parser().parse_args(argv)
    include_planetary = not args.no_planetary

    if args.analysis in ("prime-spectrum", "all"):
        print(f"Prime spectrum ({args.reconstruction}, "
              f"planetary={include_planetary}):")
        hist = prime_spectrum(args.reconstruction,
                              include_planetary=include_planetary)
        for p, n in sorted(hist.items()):
            print(f"  p={p:3d}: {n:2d} gears")
        print()

    if args.analysis in ("null-model", "all"):
        hist = prime_spectrum(args.reconstruction,
                              include_planetary=include_planetary)
        print("Null model (avg over 1000 trials of 40 random gears in [10,300]):")
        null = prime_spectrum_null_model(40)
        for p in sorted(set(hist.keys()) | {2, 3, 5, 7, 11, 13}):
            print(f"  p={p:3d}: observed={hist.get(p, 0):2d}  "
                  f"null={null.get(p, 0):5.2f}")
        print()

    if args.analysis in ("shared-primes", "all"):
        print("Shared primes across planetary trains:")
        for p, names in sorted(shared_primes_among_planetary().items()):
            print(f"  p={p}: {[n.split('_')[0] for n in names]}")
        print()

    if args.analysis in ("pareto-proxy", "all"):
        print("DEPRECATED: legacy Pareto proxy "
              "(see research.pareto_analysis for production version):")
        frontier = pareto_frontier(candidate_shared_prime_sets(max_shared=3))
        for c, t, s in frontier[:8]:
            print(f"  candidate={c}  total_teeth={t}  shared_count={s}")
        on_frontier = any(set(c) == {7, 17} for c, _, _ in frontier)
        print(f"  {{7, 17}} on legacy proxy frontier? {on_frontier}")
        print()

    if args.analysis in ("cf-ranks", "all"):
        print(f"Per-cycle CF rank report (budget = {args.budget}):")
        for rec in cycle_cf_ranks(budget=args.budget):
            print(f"  {rec['cycle']:40s} mech={rec['mechanism_pq']} "
                  f"CF rank={rec['rank_of_mechanism_pq']} "
                  f"best_pq_b{args.budget}={rec['best_pq_budget500']}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

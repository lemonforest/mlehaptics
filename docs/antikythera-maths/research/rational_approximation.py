"""Rational approximation via continued fractions.

The A-H1 hypothesis claims the mechanism's gear ratios are "best rational
approximations under a tooth-count budget."  This module provides the
computational primitives:

- ``continued_fraction(x, max_terms)``: CF expansion of a real number.
- ``convergents(cf)``: list of (p, q) convergents from a CF expansion.
- ``best_rationals_under_budget(x, max_den)``: Stern-Brocot / Farey-mediant
  enumeration of rationals p/q approximating x with q <= max_den.
- ``rank_in_convergents(x, p, q)``: for a hypothesized ratio p/q, at what
  CF-convergent index does it first appear?
- ``tooth_budget_convergents(x, budget)``: convergents with max(p, q) <= budget.

The "budget" parameter is load-bearing for A-H1: the Greeks' practical
ceiling is ~500 teeth (cuttable in bronze).  A claim "the mechanism
used the best approximation under the 500-tooth budget" is specifically
that the convergent the mechanism chose is the smallest-denominator
p/q meeting the precision it did.
"""

from __future__ import annotations

from fractions import Fraction
from math import gcd, isfinite
from typing import List, Optional, Tuple


def continued_fraction(x: float, max_terms: int = 40,
                       tol: float = 1e-14) -> List[int]:
    """Continued-fraction expansion of x, up to ``max_terms`` or until
    the remainder falls below ``tol``."""
    if not isfinite(x):
        raise ValueError(f"x must be finite, got {x}")
    out: List[int] = []
    rem = x
    for _ in range(max_terms):
        a = int(rem // 1)          # floor for non-neg; fine for positive x
        out.append(a)
        frac = rem - a
        if frac < tol:
            break
        rem = 1.0 / frac
    return out


def convergents(cf: List[int]) -> List[Tuple[int, int]]:
    """Convergents (p_k / q_k) of the CF expansion."""
    p_prev2, p_prev1 = 0, 1
    q_prev2, q_prev1 = 1, 0
    out: List[Tuple[int, int]] = []
    for a in cf:
        p = a * p_prev1 + p_prev2
        q = a * q_prev1 + q_prev2
        out.append((p, q))
        p_prev2, p_prev1 = p_prev1, p
        q_prev2, q_prev1 = q_prev1, q
    return out


def tooth_budget_convergents(x: float, budget: int,
                             max_terms: int = 40) -> List[Tuple[int, int]]:
    """Convergents of x with max(p, q) <= budget."""
    cf = continued_fraction(x, max_terms=max_terms)
    out: List[Tuple[int, int]] = []
    for p, q in convergents(cf):
        if max(p, q) > budget:
            break
        out.append((p, q))
    return out


def rank_in_convergents(x: float, p: int, q: int,
                        max_terms: int = 40) -> Optional[int]:
    """0-based index at which p/q first appears as a convergent of x,
    or ``None`` if it does not appear in the first ``max_terms``."""
    g = gcd(p, q)
    p_red, q_red = p // g, q // g
    for idx, (pi, qi) in enumerate(convergents(continued_fraction(x, max_terms))):
        gi = gcd(pi, qi)
        if (pi // gi, qi // gi) == (p_red, q_red):
            return idx
    return None


def semi_convergents(cf: List[int],
                     budget: Optional[int] = None) -> List[Tuple[int, int]]:
    """Semi-convergents — include intermediate (a_k' for a_k' < a_k)
    approximations.  These are the "best rationals" in the Stern-Brocot
    sense.

    If ``budget`` is provided, the inner enumeration over i ∈ [1, a_k]
    stops as soon as max(p, q) exceeds the budget — without this guard,
    a CF term ``a`` near 10^12 (which arises near machine-precision
    convergents of irrational ratios) would attempt to allocate ~10^12
    pairs and OOM.  Callers that filter by budget after the fact MUST
    pass the budget here.
    """
    if not cf:
        return []
    out: List[Tuple[int, int]] = []
    p_prev2, p_prev1 = 0, 1
    q_prev2, q_prev1 = 1, 0
    for k, a in enumerate(cf):
        for i in range(1, a + 1):
            p = i * p_prev1 + p_prev2
            q = i * q_prev1 + q_prev2
            if budget is not None and max(p, q) > budget:
                break
            out.append((p, q))
        p_prev2, p_prev1 = p_prev1, p_prev1 * a + p_prev2
        q_prev2, q_prev1 = q_prev1, q_prev1 * a + q_prev2
        # Once the recurrence itself exceeds budget, no further iteration helps.
        if budget is not None and max(p_prev1, q_prev1) > budget:
            break
    return out


def nearest_convergent(x: float, budget: int,
                       max_terms: int = 40) -> Optional[Tuple[int, int]]:
    """The highest-rank convergent of x that fits the budget."""
    cvs = tooth_budget_convergents(x, budget, max_terms=max_terms)
    return cvs[-1] if cvs else None


def approx_error(x: float, p: int, q: int) -> float:
    """Absolute error |x - p/q|."""
    return abs(x - p / q)


def relative_error(x: float, p: int, q: int) -> float:
    return approx_error(x, p, q) / abs(x) if x != 0 else float("inf")


# ---------------------------------------------------------------------------
# Best-rational search under budget via semi-convergents
# ---------------------------------------------------------------------------

def best_rational_under_budget(x: float, budget: int,
                               max_terms: int = 40) -> Tuple[int, int]:
    """Smallest-denominator p/q with max(p, q) <= budget minimising
    |x - p/q|.  Uses semi-convergents; O(max_terms) with tiny const.
    """
    cf = continued_fraction(x, max_terms=max_terms)
    sc = semi_convergents(cf, budget=budget)
    best: Optional[Tuple[int, int]] = None
    best_err = float("inf")
    for p, q in sc:
        if max(p, q) > budget:
            break
        err = approx_error(x, p, q)
        if err < best_err:
            best_err = err
            best = (p, q)
    if best is None:
        # fall back to floor/ceil
        return (int(round(x)), 1) if abs(x) <= budget else (1, 1)
    return best


_EPILOG = """\
Examples:
  # Default: pi + Metonic demos:
  python -m research.rational_approximation

  # CF expansion + budgeted convergents for an arbitrary target:
  python -m research.rational_approximation --target 3.14159265 --budget 1000

  # Best (p, q) under tooth budget:
  python -m research.rational_approximation --target 12.368266 --budget 500 \\
        --best-only

  # Rank of a candidate (p, q) in the CF series:
  python -m research.rational_approximation --target 12.368266 \\
        --rank-of 235,19

References
----------
Khinchin, A. Y. (1964). Continued Fractions. University of Chicago.
Lang, S. (1995). Introduction to Diophantine Approximations. Springer.
"""


def _make_parser():
    import argparse
    parser = argparse.ArgumentParser(
        prog="python -m research.rational_approximation",
        description=("Continued-fraction primitives.  Computes "
                     "convergents, semi-convergents, and best (p, q) "
                     "approximations under a tooth-count budget -- "
                     "load-bearing for A-H1 (rational approximation) "
                     "and Track 4 (Pareto search)."),
        epilog=_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--target", type=float, default=None,
        help="Real number to approximate.",
    )
    parser.add_argument(
        "--budget", type=int, default=500,
        help="Max(p, q) ceiling (default: 500, Greek bronze limit).",
    )
    parser.add_argument(
        "--max-terms", type=int, default=20,
        help="Max CF terms (default: 20).",
    )
    parser.add_argument(
        "--best-only", action="store_true",
        help="Print only the best (p, q) under budget.",
    )
    parser.add_argument(
        "--rank-of", default=None,
        help="Find the CF rank of comma-separated 'p,q' against --target.",
    )
    return parser


def main(argv=None):
    args = _make_parser().parse_args(argv)

    if args.target is None:
        # Default demo
        import numpy as np
        print("pi CF terms:", continued_fraction(np.pi, 10))
        print("pi convergents:", convergents(continued_fraction(np.pi, 10))[:6])
        print()
        true_ratio = 12.368266
        print("Synodic-months-per-year ratio:", true_ratio)
        print("  CF:", continued_fraction(true_ratio, 10))
        print("  Convergents <= budget 500:",
              tooth_budget_convergents(true_ratio, 500))
        print("  Rank of (235, 19):",
              rank_in_convergents(true_ratio, 235, 19))
        return 0

    if args.rank_of:
        try:
            p_q = [int(x) for x in args.rank_of.split(",")]
        except ValueError:
            print("ERROR: --rank-of expects 'p,q'")
            return 2
        rank = rank_in_convergents(args.target, p_q[0], p_q[1],
                                   max_terms=args.max_terms)
        print(f"rank_in_convergents({args.target}, {p_q[0]}, {p_q[1]}) = {rank}")
        return 0

    if args.best_only:
        p, q = best_rational_under_budget(args.target, args.budget,
                                          max_terms=args.max_terms)
        err = approx_error(args.target, p, q)
        print(f"best (p, q) under budget {args.budget}: ({p}, {q})  "
              f"= {p/q:.10f}  abs_err = {err:.2e}")
        return 0

    # Full report
    cf = continued_fraction(args.target, max_terms=args.max_terms)
    cvs = convergents(cf)
    bsc = tooth_budget_convergents(args.target, args.budget,
                                   max_terms=args.max_terms)
    p, q = best_rational_under_budget(args.target, args.budget,
                                      max_terms=args.max_terms)
    print(f"target = {args.target}")
    print(f"CF terms        : {cf}")
    print(f"convergents     : {cvs}")
    print(f"under budget {args.budget}: {bsc}")
    print(f"best (p, q)     : ({p}, {q})  err = {approx_error(args.target, p, q):.2e}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

"""Production-grade Pareto analysis — A-H2 + A-H4 (Track 4).

The original ``packing_analysis.total_tooth_budget_for_candidate``
proxy is buggy: its return value is the sum of (numerator + denominator)
across all planetary cycles -- a quantity that does NOT depend on the
candidate prime set.  Only ``candidate_share_count`` actually
discriminates candidates, which collapses the supposed 2D Pareto sort
to ranking by share-count alone.  Under this proxy, Freeth 2021's
{7, 17} planetary-shared-prime claim shows up as PARTIAL.  That status
is a metric artefact, not a substantive falsification.

This module replaces the proxy with a rigorous (precision, cost)
Pareto frontier.  Three metric variants are presented as ablations:

    primary       precision = sum |p/q - true_ratio| / true_ratio across
                  the 5 planets, restricted to prime factorisations in
                  candidate U {2, 3, 5}.
                  cost      = max(p, q) across all planets -- the bronze-
                  workshop bottleneck.
    factor-reuse  precision as above; cost = total tooth count summed
                  across the full reconstruction's gears.
    proxy         original metric, preserved for audit.

A-H2 PASS: {7, 17} on the primary frontier AND on at least one ablation.
A-H4 PASS: removing any of the rare large primes {47, 127, 223, 251}
    from the alphabet inflates >= 1 cycle's relative error by > 10x --
    i.e. these primes are FORCED by astronomy, not chosen for cost-share.

References
----------
Freeth, T. (2021).  A Model of the Cosmos in the ancient Greek
    Antikythera Mechanism.  Sci. Rep. 11:5821, "Planetary mechanism".
Wright, M. T. (2005).  The Antikythera Mechanism: a new gearing scheme.
    Bull. Sci. Instr. Soc. 85:2-7.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from itertools import combinations
from typing import Dict, List, Optional, Sequence, Set, Tuple


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ALWAYS_ALLOWED_PRIMES: Tuple[int, ...] = (2, 3, 5)
"""Primes that any Greek bronze workshop can produce trivially.  These
are always allowed; only the candidate set adds beyond {2, 3, 5}."""

CANDIDATE_PRIME_ALPHABET: Tuple[int, ...] = (
    7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53,
)
"""Primes considered as candidates for shared-prime selection.  Capped
at 53; primes beyond are forced by astronomy (Saros 223, lunar 251,
sidereal 127, Mars-related 47), not chosen for cost-share."""

RARE_FORCED_PRIMES: Tuple[int, ...] = (47, 127, 223, 251)
"""Primes appearing exactly once or twice in the mechanism's gear
catalog -- candidates for "forced by astronomy" under A-H4."""

DEFAULT_BUDGET: int = 500
"""Per-gear tooth-count ceiling (Greek bronze-cutting practical limit)."""

VALID_METRICS: Tuple[str, ...] = ("primary", "factor-reuse", "proxy", "all")
VALID_CYCLE_GROUPS: Tuple[str, ...] = ("planetary", "calendrical", "all")


# ---------------------------------------------------------------------------
# Score dataclass
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CandidateScore:
    """Score of one prime-set candidate against the cycles."""

    primes: Tuple[int, ...]
    """The candidate prime set (sorted)."""

    precision_relerr: float
    """Sum of relative errors |p/q - true_ratio| / true_ratio across cycles.
    +inf if no candidate (p, q) satisfies the prime constraint within budget."""

    cost_max_teeth: int
    """max(max(p, q)) across all cycles' chosen approximations -- the bronze-
    workshop bottleneck."""

    cost_total_teeth: int
    """Sum of (p + q) across cycles' chosen approximations -- the factor-
    reuse cost dimension."""

    per_cycle_pq: Dict[str, Tuple[int, int]]
    """Cycle name -> chosen (p, q) under the prime constraint."""


# ---------------------------------------------------------------------------
# Constrained best (p, q) search
# ---------------------------------------------------------------------------

def _factors_in_set(n: int, allowed: Set[int]) -> bool:
    """True iff every prime factor of n is in ``allowed``."""
    from .astronomical_cycles import prime_factor_set
    if n <= 0:
        return False
    return prime_factor_set(n).issubset(allowed)


def best_pq_constrained(
    target_ratio: float,
    allowed_primes: Set[int],
    budget: int = DEFAULT_BUDGET,
    fallback_search: bool = True,
) -> Optional[Tuple[int, int]]:
    """Smallest-denominator (p, q) approximation to ``target_ratio`` whose
    every prime factor of pq is in ``allowed_primes``, with max(p, q) <= budget.

    Strategy
    --------
    1. Compute CF convergents up to budget; filter to those whose p and q
       both factor in allowed_primes.
    2. If no convergent passes, run a bounded Stern-Brocot scan filtered by
       the same prime constraint (fallback only; bounded by budget so we
       never OOM at large CF terms -- per the bug fix in commit 6ba9fe4).

    Returns
    -------
    (p, q) or None if no valid approximation exists within the budget.
    """
    from .rational_approximation import (
        continued_fraction, convergents, semi_convergents,
    )

    cf = continued_fraction(target_ratio, max_terms=40)

    # Pass 1: full convergents
    best: Optional[Tuple[int, int]] = None
    best_err = float("inf")
    for p, q in convergents(cf):
        if max(p, q) > budget:
            break
        if not _factors_in_set(p, allowed_primes):
            continue
        if not _factors_in_set(q, allowed_primes):
            continue
        err = abs(target_ratio - p / q)
        if err < best_err:
            best_err = err
            best = (p, q)
    if best is not None:
        return best

    # Pass 2: semi-convergents (Stern-Brocot mediants), bounded
    if not fallback_search:
        return None
    for p, q in semi_convergents(cf, budget=budget):
        if max(p, q) > budget:
            break
        if not _factors_in_set(p, allowed_primes):
            continue
        if not _factors_in_set(q, allowed_primes):
            continue
        err = abs(target_ratio - p / q)
        if err < best_err:
            best_err = err
            best = (p, q)
    return best


# ---------------------------------------------------------------------------
# Cycle target-ratios
# ---------------------------------------------------------------------------

def _cycle_target_ratio(cycle) -> Optional[float]:
    """Extract a target ratio (numerator / denominator) for the cycle.

    For planetary cycles whose denominator is "years", we prefer the
    integer numerator/denominator ratio recorded by Freeth 2021.  This
    matches the question A-H2 asks: "of all candidate prime sets, which
    are Pareto-optimal at approximating the historically-known integer
    ratio under prime-constrained budget?"  We do NOT attempt to recover
    the modern synodic-period ratio for planetary cycles since the cycle
    record itself blurs (returns, years) vs (synodic, sidereal) per the
    Greek-theory ambiguity noted in astronomical_cycles.py.
    """
    if cycle.numerator <= 0 or cycle.denominator <= 0:
        return None
    return cycle.numerator / cycle.denominator


def _select_cycles(group: str) -> List:
    from .astronomical_cycles import CYCLES
    if group == "planetary":
        return [c for c in CYCLES if c.tag == "planetary"]
    if group == "calendrical":
        return [c for c in CYCLES if c.tag in ("calendar", "eclipse", "lunar")]
    if group == "all":
        return list(CYCLES)
    raise ValueError(f"group must be one of {VALID_CYCLE_GROUPS}, got {group!r}")


# ---------------------------------------------------------------------------
# Scoring + frontier
# ---------------------------------------------------------------------------

def score_candidate(
    primes: Sequence[int],
    cycles=None,
    budget: int = DEFAULT_BUDGET,
) -> CandidateScore:
    """Score one prime-set candidate against a cycle list."""
    if cycles is None:
        cycles = _select_cycles("planetary")
    allowed = set(ALWAYS_ALLOWED_PRIMES) | set(primes)
    sum_relerr = 0.0
    max_teeth = 0
    total_teeth = 0
    per_cycle_pq: Dict[str, Tuple[int, int]] = {}
    for c in cycles:
        target = _cycle_target_ratio(c)
        if target is None:
            continue
        pq = best_pq_constrained(target, allowed, budget=budget)
        if pq is None:
            sum_relerr = float("inf")
            per_cycle_pq[c.name] = (0, 0)
            continue
        p, q = pq
        per_cycle_pq[c.name] = pq
        rel = abs(target - p / q) / target if target != 0 else 0.0
        sum_relerr += rel
        max_teeth = max(max_teeth, max(p, q))
        total_teeth += p + q
    return CandidateScore(
        primes=tuple(sorted(primes)),
        precision_relerr=sum_relerr,
        cost_max_teeth=max_teeth,
        cost_total_teeth=total_teeth,
        per_cycle_pq=per_cycle_pq,
    )


def enumerate_candidates(
    max_set_size: int = 2,
    alphabet: Sequence[int] = CANDIDATE_PRIME_ALPHABET,
) -> List[Tuple[int, ...]]:
    """All prime subsets of size 1..max_set_size from ``alphabet``."""
    out: List[Tuple[int, ...]] = []
    for k in range(1, max_set_size + 1):
        for combo in combinations(alphabet, k):
            out.append(combo)
    return out


def pareto_frontier_2d(
    scores: List[CandidateScore],
    metric: str = "primary",
) -> List[CandidateScore]:
    """Pareto frontier minimising (precision_relerr, cost) for the chosen metric.

    metric:
      ``primary``        cost = cost_max_teeth
      ``factor-reuse``   cost = cost_total_teeth
      ``proxy``          cost = cost_total_teeth, precision = -shared_count
                         (matches the historical proxy direction)
    """
    if metric == "primary":
        cost = lambda s: s.cost_max_teeth
        prec = lambda s: s.precision_relerr
    elif metric == "factor-reuse":
        cost = lambda s: s.cost_total_teeth
        prec = lambda s: s.precision_relerr
    elif metric == "proxy":
        # Map back: precision = -shared_count, cost = total_teeth.
        # Lower is better on both axes.
        from .astronomical_cycles import prime_factor_set
        from .packing_analysis import candidate_share_count
        cost = lambda s: s.cost_total_teeth
        prec = lambda s: -float(candidate_share_count(s.primes))
    else:
        raise ValueError(f"metric must be one of {VALID_METRICS} (excl. 'all')")

    frontier: List[CandidateScore] = []
    for s in scores:
        ps = prec(s)
        cs = cost(s)
        dominated = False
        for s2 in scores:
            if s2 is s:
                continue
            ps2 = prec(s2)
            cs2 = cost(s2)
            if ps2 <= ps and cs2 <= cs and (ps2 < ps or cs2 < cs):
                dominated = True
                break
        if not dominated:
            frontier.append(s)
    return sorted(frontier, key=lambda s: (cost(s), prec(s)))


def is_set_on_frontier(
    target: Set[int],
    frontier: List[CandidateScore],
) -> bool:
    return any(set(s.primes) == set(target) for s in frontier)


# ---------------------------------------------------------------------------
# Forced-prime test (A-H4)
# ---------------------------------------------------------------------------

def forced_prime_test(
    prime: int,
    cycles=None,
    max_relerr_blow_up: float = 10.0,
    budget: int = DEFAULT_BUDGET,
) -> Dict[str, object]:
    """Test whether removing ``prime`` from the alphabet inflates >= 1
    cycle's relative error by more than ``max_relerr_blow_up``.

    A prime "forced by astronomy" survives this test: its absence makes
    the encoding strictly worse on at least one cycle by > 10x.
    """
    if cycles is None:
        cycles = _select_cycles("all")

    full_alphabet = set(ALWAYS_ALLOWED_PRIMES) | set(CANDIDATE_PRIME_ALPHABET) \
        | set(RARE_FORCED_PRIMES)
    reduced = full_alphabet - {prime}

    inflated_cycles: List[Dict[str, object]] = []
    for c in cycles:
        target = _cycle_target_ratio(c)
        if target is None:
            continue
        pq_full = best_pq_constrained(target, full_alphabet, budget=budget)
        pq_reduced = best_pq_constrained(target, reduced, budget=budget)
        if pq_full is None:
            continue
        p_f, q_f = pq_full
        rel_full = abs(target - p_f / q_f) / target if target != 0 else 0.0
        if pq_reduced is None:
            inflated_cycles.append({
                "cycle": c.name,
                "rel_full": rel_full,
                "rel_reduced": float("inf"),
                "ratio": float("inf"),
            })
            continue
        p_r, q_r = pq_reduced
        rel_red = abs(target - p_r / q_r) / target if target != 0 else 0.0
        ratio = (rel_red / rel_full) if rel_full > 0 else (
            float("inf") if rel_red > 0 else 1.0
        )
        if ratio > max_relerr_blow_up:
            inflated_cycles.append({
                "cycle": c.name,
                "rel_full": rel_full,
                "rel_reduced": rel_red,
                "ratio": ratio,
            })
    return {
        "prime": prime,
        "forced": bool(inflated_cycles),
        "inflated_cycles": inflated_cycles,
        "max_blow_up_threshold": max_relerr_blow_up,
    }


# ---------------------------------------------------------------------------
# Hypothesis evaluators (consumed by consolidated_tests)
# ---------------------------------------------------------------------------

def evaluate_A_H2_rigorous(
    max_set_size: int = 2,
    target_set: Sequence[int] = (7, 17),
) -> Tuple[str, str, str, Dict[str, object]]:
    """A-H2: Freeth 2021's {7, 17} planetary shared-prime choice is Pareto-optimal.

    Returns (status, computed_value_str, notes, detail_dict).  Designed
    to be called from consolidated_tests.hypothesis_A_H2.
    """
    cycles = _select_cycles("planetary")
    candidates = enumerate_candidates(max_set_size=max_set_size)
    scores = [score_candidate(c, cycles=cycles) for c in candidates]

    primary = pareto_frontier_2d(scores, metric="primary")
    factor_reuse = pareto_frontier_2d(scores, metric="factor-reuse")
    proxy = pareto_frontier_2d(scores, metric="proxy")

    target = set(target_set)
    on_primary = is_set_on_frontier(target, primary)
    on_fr = is_set_on_frontier(target, factor_reuse)
    on_proxy = is_set_on_frontier(target, proxy)

    n_pass_ablations = sum([on_primary, on_fr, on_proxy])
    # ITER-4 AUDIT-REVERT: the iter-2 threshold relaxation
    # (PASS at >= 2/3 ablations) was flagged by the research audit
    # (research_audit_report.md §A) as the closest-to-p-hacking move
    # in the iteration history -- promoting PARTIAL -> PASS without
    # re-computing.  The PARTIAL is substantively MORE informative:
    # it preserves the finding that {7,17} survives the bronze-cost
    # framing (factor-reuse + proxy) but NOT the workshop-bottleneck
    # framing (primary, cost = max single tooth count).  Reverted
    # to the original PASS = primary AND (>= 1 ablation).
    if on_primary and (on_fr or on_proxy):
        status = "PASS"
    elif on_primary or on_fr or on_proxy:
        status = "PARTIAL"
    else:
        status = "FAIL"

    notes = (
        f"Rigorous (precision, cost) Pareto -- replaces deprecated proxy. "
        f"{{7, 17}} on primary frontier: {on_primary}; on factor-reuse: "
        f"{on_fr}; on legacy proxy: {on_proxy} ({n_pass_ablations}/3 "
        f"ablations).  Primary metric uses cost = max single tooth count "
        "(bronze-workshop bottleneck); factor-reuse uses cost = total "
        "bronze (Freeth's bronze-cost-shared framing).  PASS threshold: "
        "primary frontier + >= 1 ablation (audit-reverted from iter-2's "
        ">= 2/3 ablations relaxation)."
    )
    computed = (
        f"{{7, 17}} on Pareto: primary={on_primary}, "
        f"factor-reuse={on_fr}, proxy={on_proxy}"
    )
    detail = {
        "target_set": sorted(target_set),
        "max_set_size": max_set_size,
        "n_candidates": len(candidates),
        "frontier_size_primary": len(primary),
        "frontier_size_factor_reuse": len(factor_reuse),
        "frontier_size_proxy": len(proxy),
        "on_primary": on_primary,
        "on_factor_reuse": on_fr,
        "on_proxy_legacy": on_proxy,
        "primary_frontier_top10": [
            {
                "primes": list(s.primes),
                "precision_relerr": s.precision_relerr,
                "cost_max_teeth": s.cost_max_teeth,
                "cost_total_teeth": s.cost_total_teeth,
            }
            for s in primary[:10]
        ],
    }
    return status, computed, notes, detail


def evaluate_A_H4(
    primes: Sequence[int] = RARE_FORCED_PRIMES,
    max_relerr_blow_up: float = 10.0,
) -> Tuple[str, str, str, Dict[str, object]]:
    """A-H4: rare primes (47, 127, 223, 251) are forced by astronomy.

    PASS iff every probed prime fails the forced-prime test (i.e. its
    removal inflates >= 1 cycle's relative error by > max_relerr_blow_up).
    """
    cycles = _select_cycles("all")
    results = [
        forced_prime_test(p, cycles=cycles, max_relerr_blow_up=max_relerr_blow_up)
        for p in primes
    ]
    n_forced = sum(1 for r in results if r["forced"])
    n_total = len(results)
    if n_forced == n_total:
        status = "PASS"
    elif n_forced >= n_total // 2:
        status = "PARTIAL"
    else:
        status = "FAIL"
    notes = (
        f"{n_forced}/{n_total} probed primes are FORCED -- removing each "
        "inflates >= 1 cycle's rel-err by > "
        f"{max_relerr_blow_up:g}x.  Tests whether rare primes are dictated "
        "by celestial mechanics rather than chosen for cost-sharing."
    )
    computed = f"forced primes: {n_forced}/{n_total} (probed {list(primes)})"
    detail = {
        "probed_primes": list(primes),
        "max_relerr_blow_up": max_relerr_blow_up,
        "n_forced": n_forced,
        "results": results,
    }
    return status, computed, notes, detail


# ---------------------------------------------------------------------------
# CLI surface
# ---------------------------------------------------------------------------

_EPILOG = """\
Examples:
  # Default Pareto run (planetary cycles, primary metric):
  python -m research.pareto_analysis

  # Did Freeth's {7, 17} make the primary frontier?
  python -m research.pareto_analysis --check-set 7,17

  # All three metrics with frontier dump:
  python -m research.pareto_analysis --metric all --max-set-size 2

  # Forced-prime probe (A-H4): does removing 47 hurt accuracy?
  python -m research.pareto_analysis --forced-prime 47

  # Lift the budget (be careful -- combinatorics expand):
  python -m research.pareto_analysis --max-set-size 3

Notes
-----
- The original packing_analysis.total_tooth_budget_for_candidate
  proxy is preserved as --metric proxy for audit.
- ALWAYS_ALLOWED_PRIMES = {2, 3, 5} are free for any candidate; the
  'candidate set' adds beyond {2, 3, 5}.
- DEFAULT_BUDGET = 500 (Greek bronze-cutting practical ceiling).

Citations
---------
Freeth (2021) Sci. Rep. 11:5821, "Planetary mechanism" section.
Wright (2005) Bull. Sci. Instr. Soc. 85:2-7, gear-cutting limits.
"""


def _make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m research.pareto_analysis",
        description=(
            "Production-grade (precision, cost) Pareto analysis for the "
            "Antikythera planetary trains.  Replaces the buggy proxy in "
            "packing_analysis with a rigorous prime-constrained search."
        ),
        epilog=_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--metric", choices=VALID_METRICS, default="primary",
        help="Pareto metric variant (default: primary).",
    )
    parser.add_argument(
        "--max-set-size", type=int, default=2,
        help="Max candidate prime set size (default: 2; Freeth's claim is "
             "size 2 = {7, 17}).",
    )
    parser.add_argument(
        "--cycles", choices=VALID_CYCLE_GROUPS, default="planetary",
        help="Cycle group to score against (default: planetary).",
    )
    parser.add_argument(
        "--budget", type=int, default=DEFAULT_BUDGET,
        help=f"Per-gear tooth ceiling (default: {DEFAULT_BUDGET}).",
    )
    parser.add_argument(
        "--max-prime", type=int, default=None,
        help=("Cap candidate alphabet at this prime "
              "(use to test A-H4 ablations)."),
    )
    parser.add_argument(
        "--check-set", default=None,
        help="Comma-separated primes -- check whether they're on the frontier.",
    )
    parser.add_argument(
        "--forced-prime", type=int, default=None,
        help="Test whether removing this prime breaks >= 1 cycle's accuracy.",
    )
    parser.add_argument(
        "--top-n", type=int, default=10,
        help="Number of frontier rows to print (default: 10).",
    )
    parser.add_argument(
        "--csv-out", default=None,
        help="Write frontier CSV to this path.",
    )
    return parser


def _print_frontier(frontier: List[CandidateScore], metric: str,
                    top_n: int) -> None:
    print(f"Pareto frontier (metric={metric!r}, {len(frontier)} entries; "
          f"showing top {top_n}):")
    print()
    print(f"{'primes':<24} {'precision':>12} {'max_teeth':>10} "
          f"{'total_teeth':>12}")
    print("-" * 64)
    for s in frontier[:top_n]:
        ps = ", ".join(str(p) for p in s.primes)
        rel = (f"{s.precision_relerr:>12.6f}"
               if s.precision_relerr != float("inf") else "         inf")
        print(f"{('{' + ps + '}'):<24} {rel} {s.cost_max_teeth:>10d} "
              f"{s.cost_total_teeth:>12d}")


def _write_csv(frontier: List[CandidateScore], path: str, metric: str) -> None:
    import csv
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "primes", "precision_relerr",
                         "cost_max_teeth", "cost_total_teeth"])
        for s in frontier:
            writer.writerow([
                metric,
                "+".join(str(p) for p in s.primes),
                s.precision_relerr,
                s.cost_max_teeth,
                s.cost_total_teeth,
            ])


def main(argv: Optional[List[str]] = None) -> int:
    args = _make_parser().parse_args(argv)

    if args.forced_prime is not None:
        cycles = _select_cycles("all")
        result = forced_prime_test(args.forced_prime, cycles=cycles)
        print(f"Forced-prime test: prime={args.forced_prime}")
        print(f"  Forced (>= 1 cycle inflated > 10x): {result['forced']}")
        for entry in result["inflated_cycles"]:
            print(f"  - {entry['cycle']:<40} "
                  f"rel_full={entry['rel_full']:.6g} "
                  f"-> rel_reduced={entry['rel_reduced']:.6g} "
                  f"(x{entry['ratio']:.2f})")
        return 0 if result["forced"] else 1

    cycles = _select_cycles(args.cycles)

    alphabet = CANDIDATE_PRIME_ALPHABET
    if args.max_prime is not None:
        alphabet = tuple(p for p in alphabet if p <= args.max_prime)

    candidates = enumerate_candidates(max_set_size=args.max_set_size,
                                      alphabet=alphabet)
    print(f"Scoring {len(candidates)} candidate prime sets "
          f"(max_set_size={args.max_set_size}, "
          f"alphabet={list(alphabet)})...")
    scores = [score_candidate(c, cycles=cycles, budget=args.budget)
              for c in candidates]

    metrics = ["primary", "factor-reuse", "proxy"] \
        if args.metric == "all" else [args.metric]

    for m in metrics:
        frontier = pareto_frontier_2d(scores, metric=m)
        _print_frontier(frontier, m, args.top_n)
        print()
        if args.csv_out:
            csv_path = (args.csv_out if args.metric != "all"
                        else f"{args.csv_out}.{m}.csv")
            _write_csv(frontier, csv_path, m)
            print(f"  Wrote frontier CSV to {csv_path}")
            print()

    if args.check_set:
        try:
            target = {int(x) for x in args.check_set.split(",")}
        except ValueError as exc:
            print(f"ERROR: --check-set expects comma-separated ints ({exc}).")
            return 2
        print(f"Checking membership of set {{{', '.join(map(str, sorted(target)))}}} "
              "on each frontier:")
        for m in (["primary", "factor-reuse", "proxy"]
                  if args.metric == "all" else [args.metric]):
            frontier = pareto_frontier_2d(scores, metric=m)
            on = is_set_on_frontier(target, frontier)
            print(f"  metric={m:<14}: {'ON FRONTIER' if on else 'dominated'}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

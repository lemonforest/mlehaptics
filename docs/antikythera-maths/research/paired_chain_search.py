"""G-H8 paired-chain enumeration -- Priority 1 of the §12 computability audit.

Tests the setting-mode gear hypothesis (§11.6.15) by enumerating, for each
planetary cycle, alternative rational approximations to the same target
ratio that use DIFFERENT prime factorisations than Freeth 2021's existing
chain.  A "paired chain" candidate exists if at least one alternative:

  - approximates the target within a tight tolerance (synchronisation
    residual < ~1%);
  - uses primes different from the existing chain's primes (otherwise
    the pair is trivially redundant);
  - has total tooth count within Greek bronze-cutting limits (each
    side max 500 teeth per Track 4's DEFAULT_BUDGET).

If for at least one planet such an alternative exists, G-H8's specific
prediction (synchronised-input differentials in the missing planetary
plate) is mechanically constructible and SUPPORTED.  If no alternative
exists for any planet within the constraints, G-H8 is WEAKENED.

Per notebook §11.6.15.9 implementation A: two parallel chains feed a
differential's two sun gears; under normal operation both rotate at
synchronised rates (small differential output -> dial barely moves);
under setting (one input decoupled), the differential output reflects
the operator's manual rotation (dial moves to the set value).

References
----------
Notebook §11.6.15 (G-H8 setting-mode gears) and §11.6.15.9 (the
"moves but doesn't move the dials" mechanical specification).
[figures/hypothesis_computability_audit.md](../figures/hypothesis_computability_audit.md)
priority 1.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Set, Tuple


# Default tolerances per the §12 audit
DEFAULT_RESIDUAL_TOLERANCE_PCT: float = 1.0
"""Synchronisation residual tolerance (percent of target ratio)."""

DEFAULT_BUDGET: int = 500
"""Per-gear tooth budget (matches pareto_analysis.DEFAULT_BUDGET)."""

# Prime alphabets to enumerate alternatives over
ALWAYS_ALLOWED_PRIMES: Tuple[int, ...] = (2, 3, 5)
"""Free primes -- always available."""

CANDIDATE_NON_TRIVIAL_PRIMES: Tuple[int, ...] = (
    7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 61, 67, 71, 73, 79, 83,
)
"""Non-trivial primes considered for alternative chains.  Capped at 83
(Jupiter's 76/83 includes 83); larger primes are not in any planetary
period relation."""


@dataclass(frozen=True)
class ChainCandidate:
    """One rational approximation to a planet's target ratio."""

    p: int
    q: int
    primes: Tuple[int, ...]   # sorted, non-trivial primes only
    target_ratio: float
    relative_error: float     # |p/q - target| / target


@dataclass(frozen=True)
class PairCandidate:
    """A (chain_A, chain_B) pair as a synchronised-input differential candidate."""

    planet: str
    chain_a: ChainCandidate           # Freeth 2021's existing chain
    chain_b: ChainCandidate           # Alternative chain
    sync_residual_abs: float          # |a/q_a - b/q_b|
    sync_residual_pct: float          # sync_residual_abs / target * 100
    bronze_total: int                 # p_a + q_a + p_b + q_b
    primes_disjoint: bool             # do the two chains use disjoint non-trivial primes?
    primes_overlap: Tuple[int, ...]   # if non-disjoint, which primes overlap


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _prime_factors(n: int) -> Set[int]:
    """Set of prime factors of n (deduped)."""
    out: Set[int] = set()
    d = 2
    while d * d <= n:
        while n % d == 0:
            out.add(d)
            n //= d
        d += 1
    if n > 1:
        out.add(n)
    return out


def _factors_in_set(n: int, allowed: Set[int]) -> bool:
    return _prime_factors(n).issubset(allowed)


# ---------------------------------------------------------------------------
# Existing-chain extraction
# ---------------------------------------------------------------------------

def existing_planetary_chains() -> List[ChainCandidate]:
    """Extract Freeth 2021's planetary chains from astronomical_cycles.CYCLES."""
    from .astronomical_cycles import CYCLES
    out: List[ChainCandidate] = []
    for c in CYCLES:
        if c.tag != "planetary":
            continue
        primes = tuple(sorted(_prime_factors(c.numerator) | _prime_factors(c.denominator)))
        non_trivial = tuple(p for p in primes if p not in ALWAYS_ALLOWED_PRIMES)
        target = c.numerator / c.denominator
        out.append(ChainCandidate(
            p=c.numerator, q=c.denominator, primes=non_trivial,
            target_ratio=target, relative_error=0.0,
        ))
    return out


# ---------------------------------------------------------------------------
# Alternative-chain enumeration
# ---------------------------------------------------------------------------

def enumerate_alternatives(
    target_ratio: float,
    excluded_primes: Set[int],
    budget: int = DEFAULT_BUDGET,
    residual_tolerance_pct: float = DEFAULT_RESIDUAL_TOLERANCE_PCT,
    candidate_alphabet: Sequence[int] = CANDIDATE_NON_TRIVIAL_PRIMES,
) -> List[ChainCandidate]:
    """Enumerate alternative (p, q) approximations to ``target_ratio``.

    Constraints:
      - max(p, q) <= budget
      - prime factors of pq lie in (allowed primes ∪ {2, 3, 5})
      - primes outside ``excluded_primes`` (so the alternative differs
        in at least one non-trivial prime from the original chain)
      - relative error <= residual_tolerance_pct / 100
    """
    from .pareto_analysis import best_pq_constrained
    from itertools import combinations

    out: List[ChainCandidate] = []
    seen: Set[Tuple[int, int]] = set()

    # Try each non-trivial-prime subset of size 0..3 (singletons, pairs, triples)
    for k in range(0, 4):
        for combo in combinations(candidate_alphabet, k):
            # Skip if combo overlaps the excluded set entirely
            combo_set = set(combo)
            allowed = set(ALWAYS_ALLOWED_PRIMES) | combo_set
            pq = best_pq_constrained(target_ratio, allowed, budget=budget)
            if pq is None:
                continue
            p, q = pq
            if (p, q) in seen:
                continue
            seen.add((p, q))
            err = abs(p / q - target_ratio) / target_ratio if target_ratio else float("inf")
            if err * 100 > residual_tolerance_pct:
                continue
            chain_primes = sorted(
                (_prime_factors(p) | _prime_factors(q)) - set(ALWAYS_ALLOWED_PRIMES)
            )
            chain_primes_t = tuple(chain_primes)
            # Skip exact same chain as input (this would have empty
            # difference)
            if set(chain_primes) == excluded_primes:
                continue
            out.append(ChainCandidate(
                p=p, q=q, primes=chain_primes_t,
                target_ratio=target_ratio, relative_error=err,
            ))
    # Sort by ascending relative error
    out.sort(key=lambda c: c.relative_error)
    return out


# ---------------------------------------------------------------------------
# Pair scoring
# ---------------------------------------------------------------------------

def score_pair(
    planet: str,
    chain_a: ChainCandidate,
    chain_b: ChainCandidate,
) -> PairCandidate:
    """Score a pair (chain_a, chain_b) as a synchronised-input differential."""
    sync_abs = abs(chain_a.p / chain_a.q - chain_b.p / chain_b.q)
    sync_pct = (sync_abs / chain_a.target_ratio * 100
                if chain_a.target_ratio else float("inf"))
    bronze = chain_a.p + chain_a.q + chain_b.p + chain_b.q
    primes_a = set(chain_a.primes)
    primes_b = set(chain_b.primes)
    overlap = sorted(primes_a & primes_b)
    return PairCandidate(
        planet=planet,
        chain_a=chain_a,
        chain_b=chain_b,
        sync_residual_abs=sync_abs,
        sync_residual_pct=sync_pct,
        bronze_total=bronze,
        primes_disjoint=(len(overlap) == 0),
        primes_overlap=tuple(overlap),
    )


# ---------------------------------------------------------------------------
# Top-level enumeration
# ---------------------------------------------------------------------------

def enumerate_paired_chains(
    budget: int = DEFAULT_BUDGET,
    residual_tolerance_pct: float = DEFAULT_RESIDUAL_TOLERANCE_PCT,
    require_disjoint: bool = False,
    max_alternatives_per_planet: int = 5,
) -> Dict[str, List[PairCandidate]]:
    """For each planet, find paired-chain candidates.

    Returns dict planet -> list of best alternative pairs (sorted by
    sync residual ascending, then bronze cost ascending).
    """
    out: Dict[str, List[PairCandidate]] = {}
    for chain_a in existing_planetary_chains():
        # Extract planet name from cycle name
        from .astronomical_cycles import CYCLES
        planet = "?"
        for c in CYCLES:
            if c.numerator == chain_a.p and c.denominator == chain_a.q and c.tag == "planetary":
                planet = c.name.split("_")[0]
                break
        excluded = set(chain_a.primes)
        alternatives = enumerate_alternatives(
            target_ratio=chain_a.p / chain_a.q,
            excluded_primes=excluded,
            budget=budget,
            residual_tolerance_pct=residual_tolerance_pct,
        )
        pairs: List[PairCandidate] = []
        for alt in alternatives:
            pair = score_pair(planet, chain_a, alt)
            if require_disjoint and not pair.primes_disjoint:
                continue
            pairs.append(pair)
        pairs.sort(key=lambda p: (p.sync_residual_pct, p.bronze_total))
        out[planet] = pairs[:max_alternatives_per_planet]
    return out


# ---------------------------------------------------------------------------
# G-H8 evaluator
# ---------------------------------------------------------------------------

def evaluate_G_H8(
    budget: int = DEFAULT_BUDGET,
    residual_tolerance_pct: float = DEFAULT_RESIDUAL_TOLERANCE_PCT,
) -> Tuple[str, str, str, Dict[str, object]]:
    """G-H8 hypothesis evaluator.

    PASS iff for at least 3 of 5 planets, a viable paired-chain candidate
    exists (different primes than Freeth 2021 chain, sync residual <= 1%,
    bronze cost <= 4 * budget for the pair).

    Returns (status, computed_value_str, notes, detail_dict) -- the
    standard H-battery evaluator signature.
    """
    pairs_by_planet = enumerate_paired_chains(
        budget=budget,
        residual_tolerance_pct=residual_tolerance_pct,
        require_disjoint=False,
    )
    n_with_disjoint: int = 0
    n_with_any: int = 0
    summary: List[Dict[str, object]] = []
    for planet, pairs in pairs_by_planet.items():
        n_pairs = len(pairs)
        n_disjoint = sum(1 for p in pairs if p.primes_disjoint)
        if n_pairs > 0:
            n_with_any += 1
        if n_disjoint > 0:
            n_with_disjoint += 1
        best_disjoint = next((p for p in pairs if p.primes_disjoint), None)
        summary.append({
            "planet": planet,
            "freeth_chain": (pairs[0].chain_a.p, pairs[0].chain_a.q) if pairs else None,
            "n_alternatives": n_pairs,
            "n_disjoint_alternatives": n_disjoint,
            "best_alternative_chain": (
                (best_disjoint.chain_b.p, best_disjoint.chain_b.q)
                if best_disjoint else None
            ),
            "best_alternative_primes": (
                list(best_disjoint.chain_b.primes) if best_disjoint else None
            ),
            "best_sync_residual_pct": (
                best_disjoint.sync_residual_pct if best_disjoint else None
            ),
        })
    # Verdict: PASS if >=3 of 5 planets have a disjoint-prime alternative
    if n_with_disjoint >= 3:
        status = "PASS"
    elif n_with_disjoint >= 1:
        status = "PARTIAL"
    else:
        status = "FAIL"
    notes = (
        f"{n_with_disjoint}/5 planets admit a paired-chain candidate with "
        f"disjoint non-trivial primes (sync residual <= "
        f"{residual_tolerance_pct}%, max(p,q) <= {budget}).  "
        f"{n_with_any}/5 admit any alternative (incl. overlapping primes). "
        "G-H8 prediction: synchronised-input differentials in missing "
        "planetary plate.  PASS if >= 3 disjoint."
    )
    computed = f"{n_with_disjoint}/5 disjoint-prime pairs; {n_with_any}/5 any-prime"
    detail = {
        "budget": budget,
        "residual_tolerance_pct": residual_tolerance_pct,
        "n_planets": len(pairs_by_planet),
        "n_with_disjoint_alternative": n_with_disjoint,
        "n_with_any_alternative": n_with_any,
        "per_planet_summary": summary,
    }
    return status, computed, notes, detail


# ---------------------------------------------------------------------------
# CLI surface
# ---------------------------------------------------------------------------

_EPILOG = """\
Examples:
  # Default G-H8 enumeration (budget 500, tolerance 1.0%):
  python -m research.paired_chain_search

  # Tighter tolerance (sync residual <= 0.1%):
  python -m research.paired_chain_search --tolerance-pct 0.1

  # Larger budget (allow gears up to 1000 teeth -- physically impractical
  # but tests sensitivity):
  python -m research.paired_chain_search --budget 1000

  # JSON output for downstream consumption:
  python -m research.paired_chain_search --json-out results/g_h8_paired_chains.json

References
----------
Notebook §11.6.15 (G-H8 setting-mode gears).
§12 computability audit, Priority 1.
"""


def _make_parser():
    parser = argparse.ArgumentParser(
        prog="python -m research.paired_chain_search",
        description=("G-H8 paired-chain enumeration: for each planet, find "
                     "alternative rational approximations to Freeth 2021's "
                     "chain that use different primes.  Tests the setting-"
                     "mode gear hypothesis (§11.6.15) by computing whether "
                     "synchronised-input differentials in the missing "
                     "planetary plate are mechanically constructible."),
        epilog=_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--budget", type=int, default=DEFAULT_BUDGET,
        help=f"Max(p, q) per chain (default: {DEFAULT_BUDGET}).",
    )
    parser.add_argument(
        "--tolerance-pct", type=float,
        default=DEFAULT_RESIDUAL_TOLERANCE_PCT,
        help=f"Sync residual tolerance in % "
             f"(default: {DEFAULT_RESIDUAL_TOLERANCE_PCT}).",
    )
    parser.add_argument(
        "--require-disjoint", action="store_true",
        help="Only show pairs with disjoint non-trivial primes "
             "(no overlap with Freeth 2021 chain's primes).",
    )
    parser.add_argument(
        "--max-per-planet", type=int, default=5,
        help="Show top N alternatives per planet (default: 5).",
    )
    parser.add_argument(
        "--evaluate", action="store_true",
        help="Run G-H8 evaluator and print PASS/FAIL.",
    )
    parser.add_argument(
        "--json-out", default=None,
        help="Write detailed result JSON to this path.",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = _make_parser().parse_args(argv)
    pairs_by_planet = enumerate_paired_chains(
        budget=args.budget,
        residual_tolerance_pct=args.tolerance_pct,
        require_disjoint=args.require_disjoint,
        max_alternatives_per_planet=args.max_per_planet,
    )

    print("G-H8 paired-chain enumeration")
    print(f"  budget         : {args.budget}")
    print(f"  tolerance      : {args.tolerance_pct} %")
    print(f"  require disjoint: {args.require_disjoint}")
    print()
    for planet, pairs in pairs_by_planet.items():
        if not pairs:
            print(f"  {planet:<10}  no alternatives within constraints")
            continue
        chain_a = pairs[0].chain_a
        print(f"  {planet:<10}  Freeth chain {chain_a.p}/{chain_a.q} "
              f"(primes {list(chain_a.primes)}); "
              f"{len(pairs)} alternative(s):")
        for pair in pairs:
            disj = "DISJOINT" if pair.primes_disjoint else f"overlap={list(pair.primes_overlap)}"
            primes_str = str(list(pair.chain_b.primes))
            print(f"      alt {pair.chain_b.p:>4}/{pair.chain_b.q:<4}  "
                  f"primes={primes_str:<24}  "
                  f"sync_res={pair.sync_residual_pct:>6.3f}%  "
                  f"bronze={pair.bronze_total:>4}  {disj}")
        print()

    if args.evaluate:
        status, computed, notes, detail = evaluate_G_H8(
            budget=args.budget, residual_tolerance_pct=args.tolerance_pct,
        )
        print("--- G-H8 evaluator ---")
        print(f"  status  : {status}")
        print(f"  computed: {computed}")
        print(f"  notes   : {notes}")

    if args.json_out:
        import json
        from pathlib import Path
        all_pairs_dict = {
            planet: [
                {
                    "chain_a_p_q": (p.chain_a.p, p.chain_a.q),
                    "chain_a_primes": list(p.chain_a.primes),
                    "chain_b_p_q": (p.chain_b.p, p.chain_b.q),
                    "chain_b_primes": list(p.chain_b.primes),
                    "sync_residual_pct": p.sync_residual_pct,
                    "bronze_total": p.bronze_total,
                    "primes_disjoint": p.primes_disjoint,
                    "primes_overlap": list(p.primes_overlap),
                }
                for p in pairs
            ]
            for planet, pairs in pairs_by_planet.items()
        }
        Path(args.json_out).parent.mkdir(parents=True, exist_ok=True)
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(all_pairs_dict, f, indent=2, default=str)
        print(f"  wrote {args.json_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

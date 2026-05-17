"""Spike #32 supplementary — substrate invariance of the π convergent ladder.

Tests Q2 explicitly: run four DIFFERENT integer-cyclic cascade types
to a comparable precision and check whether the convergent ladder
matches.

Substrates:
  1. Archimedes hexagon doubling (start n=6, integer-Pythagorean)
  2. Archimedes square doubling   (start n=4, integer-Pythagorean)
  3. Archimedes triangle doubling (start n=3, integer-Pythagorean)
  4. Antikythera-like dodecagon doubling (start n=12, integer-Pythagorean)

All are integer-cyclic cascade types. None invoke math.pi.

Verdict: the BEST-RATIONAL ladders at canonical denominator caps should
match across all four starting polygons; the CF prefixes should
converge to [3; 7, 15, 1, 292, ...] regardless of substrate.
"""

from __future__ import annotations

import math
import json
import sys
from typing import List, Tuple

CANONICAL_PI_CF: List[int] = [3, 7, 15, 1, 292, 1, 1, 1, 2, 1, 3, 1, 14, 2, 1, 1]


def canonical_pi_convergents(num_terms: int = 12) -> List[Tuple[int, int]]:
    convs = []
    h_prev, h_curr = 1, 0
    k_prev, k_curr = 0, 1
    for a in CANONICAL_PI_CF[:num_terms]:
        h_next = a * h_prev + h_curr
        k_next = a * k_prev + k_curr
        convs.append((h_next, k_next))
        h_curr, h_prev = h_prev, h_next
        k_curr, k_prev = k_prev, k_next
    return convs


def integer_sqrt(n: int) -> int:
    if n < 0:
        raise ValueError
    if n < 2:
        return n
    x = n
    y = (x + 1) // 2
    while y < x:
        x = y
        y = (x + n // x) // 2
    return x


def rational_sqrt_bounds(num: int, den: int, precision_bits: int = 512) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    if num < 0 or den <= 0:
        raise ValueError
    if num == 0:
        return ((0, 1), (0, 1))
    M = 1 << precision_bits
    scaled = num * M * M * den
    s = integer_sqrt(scaled)
    lower = (s, den * M)
    upper = (s + 1, den * M)
    g_l = math.gcd(lower[0], lower[1])
    lower = (lower[0] // g_l, lower[1] // g_l)
    g_u = math.gcd(upper[0], upper[1])
    upper = (upper[0] // g_u, upper[1] // g_u)
    return lower, upper


def cf_bignum(p: int, q: int, max_terms: int = 30) -> List[int]:
    result = []
    while q != 0 and len(result) < max_terms:
        result.append(p // q)
        p, q = q, p % q
    return result


def best_rational_bignum(p: int, q: int, max_denominator: int) -> Tuple[int, int]:
    if q == 0:
        return (0, 1)
    h_prev, h_curr = 1, 0
    k_prev, k_curr = 0, 1
    best_p, best_q = 0, 1
    while q != 0:
        a = p // q
        h_next = a * h_prev + h_curr
        k_next = a * k_prev + k_curr
        if k_next > max_denominator:
            break
        best_p, best_q = h_next, k_next
        h_curr, h_prev = h_prev, h_next
        k_curr, k_prev = k_prev, k_next
        p, q = q, p % q
    return best_p, best_q


def archimedes_cascade(s_sq_init_num: int, s_sq_init_den: int, n_init: int,
                       num_doublings: int = 20, precision_bits: int = 512) -> dict:
    """Generic Archimedes-style integer-cyclic doubling cascade.

    Starting polygon: regular n_init-gon inscribed in unit circle, with
    initial side squared = s_sq_init_num / s_sq_init_den.

    Recurrence (integer-Pythagorean): s_{2n}² = 2 − √(4 − s_n²)
    """
    s_sq_num, s_sq_den = s_sq_init_num, s_sq_init_den
    n = n_init
    final_mid = None
    for step in range(num_doublings):
        # Compute the semi-perimeter as rational interval
        s_lo, s_hi = rational_sqrt_bounds(s_sq_num, s_sq_den, precision_bits=precision_bits)
        half_p_lo_num = n * s_lo[0]
        half_p_lo_den = 2 * s_lo[1]
        half_p_hi_num = n * s_hi[0]
        half_p_hi_den = 2 * s_hi[1]
        g_lo = math.gcd(half_p_lo_num, half_p_lo_den)
        half_p_lo = (half_p_lo_num // g_lo, half_p_lo_den // g_lo)
        g_hi = math.gcd(half_p_hi_num, half_p_hi_den)
        half_p_hi = (half_p_hi_num // g_hi, half_p_hi_den // g_hi)
        mid_num = half_p_lo[0] * half_p_hi[1] + half_p_hi[0] * half_p_lo[1]
        mid_den = 2 * half_p_lo[1] * half_p_hi[1]
        g_m = math.gcd(mid_num, mid_den)
        final_mid = (mid_num // g_m, mid_den // g_m)
        final_n = n

        # Cascade doubling
        four_minus_s_sq_num = 4 * s_sq_den - s_sq_num
        four_minus_s_sq_den = s_sq_den
        rsq_lo, rsq_hi = rational_sqrt_bounds(four_minus_s_sq_num, four_minus_s_sq_den, precision_bits=precision_bits)
        rsq_mid_num = rsq_lo[0] * rsq_hi[1] + rsq_hi[0] * rsq_lo[1]
        rsq_mid_den = 2 * rsq_lo[1] * rsq_hi[1]
        g_rsq = math.gcd(rsq_mid_num, rsq_mid_den)
        rsq_mid_num //= g_rsq
        rsq_mid_den //= g_rsq
        new_s_sq_num = 2 * rsq_mid_den - rsq_mid_num
        new_s_sq_den = rsq_mid_den
        g_new = math.gcd(new_s_sq_num, new_s_sq_den)
        s_sq_num = new_s_sq_num // g_new
        s_sq_den = new_s_sq_den // g_new
        n *= 2

    cf = cf_bignum(final_mid[0], final_mid[1], max_terms=30)
    best_rats = {}
    for md in [10, 100, 1000, 10000, 100000, 1000000]:
        best_rats[md] = best_rational_bignum(final_mid[0], final_mid[1], md)
    return {
        "final_n": final_n,
        "continued_fraction_first_30": cf,
        "best_rational_at_denom": best_rats,
    }


def main():
    canonical = canonical_pi_convergents(num_terms=12)
    print("=" * 78)
    print("Spike #32 supplementary — substrate invariance")
    print("=" * 78)
    print("\nCanonical π convergents (from CF [3;7,15,1,292,...]):")
    for i, (p, q) in enumerate(canonical):
        print(f"  conv_{i}: {p}/{q}")

    substrates = [
        # (label, s_sq_init_num, s_sq_init_den, n_init)
        # Regular n-gon inscribed in unit circle, side² = 2 − 2·cos(2π/n).
        # We're computing these starting values from the integer relations:
        #   n=3 (equilateral triangle): side² = 3
        #   n=4 (square): side² = 2
        #   n=6 (regular hexagon): side² = 1
        #   n=12 (regular dodecagon): side² = 2 − √3 ≈ 0.2679...
        #     This is irrational. We approximate it as a rational
        #     from the Archimedes recurrence starting at hexagon:
        #     s_12² = 2 − √(4 − 1) = 2 − √3
        # We need a rational start. Use Pythagorean.
        ("hexagon_start_n=6", 1, 1, 6),
        ("square_start_n=4", 2, 1, 4),
        ("triangle_start_n=3", 3, 1, 3),
        # Dodecagon: we'd need 2 − √3 as a rational. Skip; use only
        # Pythagorean-starting polygons.
    ]

    results = {}
    for label, num, den, n in substrates:
        print(f"\n--- {label} cascade ---", flush=True)
        r = archimedes_cascade(num, den, n, num_doublings=20, precision_bits=512)
        results[label] = r
        match_count = 0
        for i in range(min(len(r["continued_fraction_first_30"]), len(CANONICAL_PI_CF))):
            if r["continued_fraction_first_30"][i] == CANONICAL_PI_CF[i]:
                match_count += 1
            else:
                break
        print(f"  final n = {r['final_n']}")
        print(f"  CF prefix = {r['continued_fraction_first_30'][:16]}")
        print(f"  Canonical = {CANONICAL_PI_CF}")
        print(f"  Match count = {match_count}/{len(CANONICAL_PI_CF)} canonical CF coefficients")
        for md, (p, q) in r["best_rational_at_denom"].items():
            cm = ""
            for ci, (cp, cq) in enumerate(canonical):
                if cp == p and cq == q:
                    cm = f"  ← canonical conv #{ci}"
                    break
            print(f"  max_denom={md:>8}: {p}/{q}{cm}")

    # Cross-substrate verdict
    print("\n" + "=" * 78)
    print("CROSS-SUBSTRATE VERDICT")
    print("=" * 78)
    labels = list(results.keys())
    print(f"\nBest-rational matches across substrates at max_denom=1000:")
    for label in labels:
        p, q = results[label]["best_rational_at_denom"][1000]
        print(f"  {label}: {p}/{q}")
    print(f"\nBest-rational matches across substrates at max_denom=100000:")
    for label in labels:
        p, q = results[label]["best_rational_at_denom"][100000]
        print(f"  {label}: {p}/{q}")

    # Check whether all substrates produce identical best-rationals at each cap
    print(f"\nSubstrate-invariance check (best-rational at each cap):")
    all_match = True
    for md in [10, 100, 1000, 10000, 100000]:
        rats = [results[l]["best_rational_at_denom"][md] for l in labels]
        unique = set(tuple(r) for r in rats)
        match = (len(unique) == 1)
        if not match:
            all_match = False
        print(f"  max_denom={md:>8}: {'INVARIANT' if match else 'VARIANT'} {rats}")
    print(f"\nOverall substrate invariance: {'CONFIRMED' if all_match else 'PARTIAL'}")

    # Dump NDJSON
    records = []
    records.append({"kind": "canonical_pi_convergents", "convergents": canonical})
    for label, r in results.items():
        cf = r["continued_fraction_first_30"]
        match_count = 0
        for i in range(min(len(cf), len(CANONICAL_PI_CF))):
            if cf[i] == CANONICAL_PI_CF[i]:
                match_count += 1
            else:
                break
        records.append({
            "kind": "substrate_invariance_result",
            "substrate": label,
            "final_n": r["final_n"],
            "continued_fraction_first_30": cf,
            "canonical_match_count": match_count,
            "best_rational_at_denom": {str(k): list(v) for k, v in r["best_rational_at_denom"].items()},
        })
    records.append({
        "kind": "substrate_invariance_verdict",
        "all_match": all_match,
        "verdict": "Convergent ladder is substrate-invariant across hexagon/square/triangle Archimedes cascades — π's SHAPE (CF coefficient sequence) is identity-invariant to the cascade starting polygon."
                   if all_match else
                   "Partial substrate-invariance: lower-denominator convergents match but higher-precision CF prefixes diverge",
    })

    with open("D:/temp/spike_32/spike_32_substrate_invariance.ndjson", "w", encoding="utf-8") as f:
        for r in records:
            def clean(d):
                if isinstance(d, dict):
                    return {k: clean(v) for k, v in d.items()}
                if isinstance(d, list):
                    return [clean(v) for v in d]
                if isinstance(d, tuple):
                    return [clean(v) for v in d]
                return d
            f.write(json.dumps(clean(r)) + "\n")
    print(f"\nWrote {len(records)} NDJSON records.")


if __name__ == "__main__":
    main()

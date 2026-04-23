"""Coprime row/column generators for candidate encoder dimensions.

The chess-maths framework (section 9f) uses generators 67 (row) and 7
(column) mod 512 or mod 640, both coprime to the modulus.  For each
candidate fiber rank in Othello the encoder dimension is

    D = (fiber_rank + k_dct) * 64

where k_dct = 10 (number of D4xZ2 irreps) is the full character
channel count.  This module finds the smallest admissible primes p, q
such that gcd(p, D) = gcd(q, D) = 1 and p != q, p not in {2, 5},
q not in {2, 5} (the chess framework avoids 2 and 5 because they are
factors of base-10 and of common binary alignments).  We also report
all 64 phases (r*p + c*q) mod D to confirm they are distinct.
"""

from __future__ import annotations

from math import gcd
from typing import Iterator


FORBIDDEN_PRIMES = (2, 5)


def _primes_from(start: int) -> Iterator[int]:
    n = start
    while True:
        if n < 2:
            n += 1
            continue
        is_prime = True
        k = 2
        while k * k <= n:
            if n % k == 0:
                is_prime = False
                break
            k += 1
        if is_prime:
            yield n
        n += 1


def _admissible_primes(D: int, limit: int = 2000) -> list[int]:
    """Primes in [3, limit] coprime to D and not in FORBIDDEN_PRIMES."""
    out: list[int] = []
    it = _primes_from(3)
    while True:
        p = next(it)
        if p > limit:
            break
        if p in FORBIDDEN_PRIMES:
            continue
        if gcd(p, D) != 1:
            continue
        out.append(p)
    return out


def _phases_distinct(D: int, p: int, q: int) -> bool:
    """True iff the 64 phases (r*p + c*q) mod D are all distinct.

    A collision implies (r1 - r2)*p + (c1 - c2)*q is a multiple of D
    for some nonzero (r1 - r2, c1 - c2) in [-7,7]^2.
    """
    seen = set()
    for r in range(8):
        for c in range(8):
            v = (r * p + c * q) % D
            if v in seen:
                return False
            seen.add(v)
    return True


def find_generators(D: int) -> tuple[int, int]:
    """Return the (p, q) pair with smallest p + q such that p, q are
    admissible primes and all 64 phases (r*p + c*q) mod D are
    distinct.  Chess used (67, 7) for D = 640 (chosen so that 8*67 =
    536 < 640 but 8*7 = 56 << 640 — row stride dominates column
    stride).  The search here is exhaustive over a small prime set.
    """
    primes = _admissible_primes(D)
    best: tuple[int, int] | None = None
    best_sum = float("inf")
    for p in primes:
        for q in primes:
            if p == q:
                continue
            if p + q >= best_sum:
                continue
            if _phases_distinct(D, p, q):
                best = (p, q)
                best_sum = p + q
    if best is None:
        raise RuntimeError(f"no admissible (p, q) found for D = {D}")
    return best


def phase_coverage(D: int, p: int, q: int) -> dict:
    """Compute the 64-point image {(r*p + c*q) mod D : r, c in 0..7}.
    Returns coverage metrics (are all distinct?).
    """
    image = set()
    for r in range(8):
        for c in range(8):
            image.add((r * p + c * q) % D)
    return {
        "modulus": D,
        "row_gen": p,
        "col_gen": q,
        "unique_phases": len(image),
        "all_distinct": len(image) == 64,
    }


def candidates_table(
    fiber_ranks: tuple[int, ...] = (2, 6, 8),
    k_dct: int = 10,
) -> list[dict]:
    rows = []
    for r in fiber_ranks:
        D = (r + k_dct) * 64
        p, q = find_generators(D)
        info = phase_coverage(D, p, q)
        rows.append(
            {
                "fiber_rank": r,
                "k_dct": k_dct,
                "D": D,
                **info,
            }
        )
    return rows


if __name__ == "__main__":
    for row in candidates_table():
        print(row)

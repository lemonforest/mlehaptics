"""4D phase-operator generator search — Phase A of the Chess4D-O&C
phase-operator implementation plan.

Lifts the 2D admissible-primes + image-bijection search from
docs/othello-maths/research/coprime_generators.py to 4 axes on Z_8^4.

Design discipline (per Othello CHESS_NOTEBOOK_PHASE_1C_PATCHES.md
Patch 2): coprimality of each generator with the modulus M is
necessary but *not sufficient* for image bijection on [0,7]^4. The
complete condition is

    g_x · Δx + g_y · Δy + g_z · Δz + g_w · Δw ≢ 0 (mod M)

for every nonzero (Δx, Δy, Δz, Δw) ∈ [-7, 7]^4. We check this
directly via the 4096-point image-set construction — equivalent in
practice and simpler to reason about.

Goal: find the smallest M with admissible 4-tuple (g_x, g_y, g_z, g_w)
satisfying:

    Constraint 1 (coprime):      gcd(g_i, M) = 1  ∀ i
    Constraint 2 (bijection):    |φ([0,7]^4)| = 4096
    Constraint 3 (non-subgroup): φ([0,7]^4) is not a subgroup of Z_M
    Constraint 4 (derived gens distinct): the 8 axis shifts {±g_i},
                                          24 plane-diagonal shifts
                                          {±g_i ± g_j : i<j}, 48 knight
                                          shifts {±2g_i ± g_j : i≠j},
                                          and 80 king shifts {Σ ε_i g_i :
                                          ε ∈ {-1,0,+1}^4 \\ {0}} are
                                          all pairwise distinct mod M.
                                          (Across categories too — no
                                          knight shift equals any king
                                          shift, etc.)

Run: ``python chess4d_phase_design.py``

Prints the chosen tuple and a per-constraint validation table.
"""

from __future__ import annotations

import sys
import time
from itertools import product
from math import gcd
from typing import Iterator

import numpy as np


# Forbidden primes from the 2D framework convention (§9f) — 2 and 5
# are factors of base-10 alignments and are conventionally avoided.
FORBIDDEN_PRIMES = (2, 5)


# ─── prime + admissibility helpers (lifted from coprime_generators.py)


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


def _admissible_primes(M: int, limit: int = 2000) -> list[int]:
    """Primes in [3, limit] coprime to M and not in FORBIDDEN_PRIMES."""
    out: list[int] = []
    it = _primes_from(3)
    while True:
        p = next(it)
        if p > limit:
            break
        if p in FORBIDDEN_PRIMES:
            continue
        if gcd(p, M) != 1:
            continue
        out.append(p)
    return out


# ─── 4D phase image + bijection check


# Pre-compute the [0,7]^4 coordinate matrix once — reused across every
# bijection check. Shape (4096, 4) of int32; column i is the i-th axis.
_COORDS_4D = np.array(
    list(product(range(8), repeat=4)), dtype=np.int64,
)


def phi_image_array(M: int, gx: int, gy: int, gz: int, gw: int) -> np.ndarray:
    """Vectorized φ: returns the (4096,) int64 array of image residues."""
    g = np.array([gx, gy, gz, gw], dtype=np.int64)
    return (_COORDS_4D @ g) % M


def phi_image(M: int, gx: int, gy: int, gz: int, gw: int) -> set[int]:
    return set(phi_image_array(M, gx, gy, gz, gw).tolist())


def is_bijective(M: int, gx: int, gy: int, gz: int, gw: int) -> bool:
    """Constraint 2: image of [0,7]^4 under φ has 4096 distinct values.

    Vectorized: numpy.unique on the image array — much faster than the
    set-based version for use in tight inner loops."""
    img = phi_image_array(M, gx, gy, gz, gw)
    return len(np.unique(img)) == 4096


def is_subgroup(image: set[int], M: int) -> bool:
    """Constraint 3 (negated): the image is closed under addition
    mod M. We expect this to be False for valid designs — the
    boundary-detection mechanism (§11.2.1) requires the off-image
    complement of Z_M to be non-empty under shift-by-generator."""
    image_list = sorted(image)
    # Sample-check: if the image were a subgroup, then 0 ∈ image and
    # for any two elements a, b ∈ image, (a + b) mod M ∈ image. Test
    # 200 random pairs (full O(N²) check is 16M comparisons; sampling
    # is enough — false positives here are negligible for sets of
    # size 4096 in a modulus < 65536).
    if 0 not in image:
        return False
    import random
    rng = random.Random(0)  # deterministic seeding for reproducibility
    for _ in range(200):
        a = rng.choice(image_list)
        b = rng.choice(image_list)
        if (a + b) % M not in image:
            return False
    return True


# ─── derived-generator construction


def derived_generators(
    gx: int, gy: int, gz: int, gw: int, M: int,
) -> dict[str, list[int]]:
    """Construct all derived shift sets per the plan's Constraint 4.

    Returns dict with keys {'axis', 'plane_diag', 'knight', 'king'} →
    lists of shifts mod M (with sign included; e.g. ±g_i is two
    entries). Each list is the per-piece operator's full unobstructed
    shift set on the 4D lattice.
    """
    gens = (gx, gy, gz, gw)

    # 8 axis shifts: ±g_i for each axis.
    axis: list[int] = []
    for g in gens:
        axis.append(g % M)
        axis.append((-g) % M)

    # 24 plane-diagonal shifts: ±g_i ± g_j for i < j (6 pairs × 4
    # sign combos). The "primary" generator per (i,j) plane.
    plane_diag: list[int] = []
    for i in range(4):
        for j in range(i + 1, 4):
            for si in (-1, +1):
                for sj in (-1, +1):
                    plane_diag.append((si * gens[i] + sj * gens[j]) % M)

    # 48 knight shifts: ±2·g_i ± g_j for i ≠ j (12 ordered pairs × 4
    # sign combos).
    knight: list[int] = []
    for i in range(4):
        for j in range(4):
            if i == j:
                continue
            for s2 in (-2, +2):
                for s1 in (-1, +1):
                    knight.append((s2 * gens[i] + s1 * gens[j]) % M)

    # 80 king shifts: Σ ε_i · g_i over ε ∈ {-1,0,+1}^4 \ {0000}.
    king: list[int] = []
    for eps in product((-1, 0, +1), repeat=4):
        if eps == (0, 0, 0, 0):
            continue
        s = sum(e * g for e, g in zip(eps, gens)) % M
        king.append(s)

    return {
        "axis": axis,
        "plane_diag": plane_diag,
        "knight": knight,
        "king": king,
    }


def derived_distinctness(deriv: dict[str, list[int]]) -> dict[str, int | bool]:
    """Constraint 4: per-piece operator destination sets are
    pairwise distinct mod M, AND knight does not alias the
    rook/bishop/king family.

    Important structural note: by construction, the king's 80 shifts
    *contain* both the 8 axis shifts (ε ∈ {-1,0,+1}^4 with weight 1)
    and the 24 plane-diagonal shifts (ε with weight 2). So
    `axis ⊂ king` and `plane_diag ⊂ king` are identities, not
    constraints — checking for cross-category collisions in those
    relationships would trivially fail every design. The 2D supplement
    has the same structure (2D king's 8 shifts = axis ∪ plane-diag).

    The meaningful constraints:
      * Each per-piece set has no internal collision.
      * Knight ∩ (axis ∪ plane_diag ∪ king) = ∅. Knight uses ±2 on one
        axis, which is distinct from the king/axis/plane-diag's ±1
        steps; verify it actually holds at the chosen M.

    Returns a report dict with per-category counts/uniqueness plus
    the knight-disjointness flag.
    """
    report: dict[str, int | bool] = {}
    for name, shifts in deriv.items():
        report[f"{name}_count"] = len(shifts)
        report[f"{name}_unique"] = len(set(shifts)) == len(shifts)
    report["total_shifts"] = sum(len(s) for s in deriv.values())
    report["all_unique_within_categories"] = all(
        report[f"{k}_unique"] for k in deriv  # type: ignore[index]
    )
    # Knight should not alias any single-step (axis/plane-diag/king)
    # shift, since knight uses ±2 multipliers and the others don't.
    knight_set = set(deriv["knight"])
    other_set = set(deriv["axis"]) | set(deriv["plane_diag"]) | set(deriv["king"])
    report["knight_disjoint_from_others"] = len(knight_set & other_set) == 0
    return report


# ─── search


def search_4d_design(
    M_min: int = 4097,           # M=4096 fails C3 trivially (image=Z_M)
    M_max: int = 16384,
    prime_limit: int = 200,
    verbose: bool = True,
) -> list[dict]:
    """Iterate M ascending, return the first M with a valid 4-tuple.

    Strategy:
      * Outer: M ascending.
      * Inner: ascending-prime 4-tuples (gx < gy < gz < gw) ordered
        by sum. Iterate by *sum-rank* so we find the smallest-sum
        tuple first and short-circuit immediately.
      * Per-tuple: cheap-first checks — bijection (numpy), then
        derived-gen distinctness (numpy), then subgroup check.

    Restricting to ascending tuples loses no generality: the operator
    algebra is invariant under axis permutation, so the chosen
    representative covers the whole permutation orbit (24×).
    """
    t0 = time.time()
    last_progress = t0
    for M in range(M_min, M_max + 1):
        primes = _admissible_primes(M, limit=prime_limit)
        if len(primes) < 4:
            continue

        # Build candidate 4-tuples sorted by sum (ascending).
        candidates: list[tuple[int, int, int, int, int]] = []
        for ix, gx in enumerate(primes):
            for iy in range(ix + 1, len(primes)):
                gy = primes[iy]
                for iz in range(iy + 1, len(primes)):
                    gz = primes[iz]
                    for iw in range(iz + 1, len(primes)):
                        gw = primes[iw]
                        candidates.append((gx + gy + gz + gw,
                                           gx, gy, gz, gw))
        candidates.sort()

        for s, gx, gy, gz, gw in candidates:
            if not is_bijective(M, gx, gy, gz, gw):
                continue
            deriv = derived_generators(gx, gy, gz, gw, M)
            report = derived_distinctness(deriv)
            if not (report["all_unique_within_categories"]
                    and report["knight_disjoint_from_others"]):
                continue
            image = phi_image(M, gx, gy, gz, gw)
            if is_subgroup(image, M):
                continue

            # Found the smallest-sum valid tuple at this M.
            elapsed = time.time() - t0
            if verbose:
                print(f"[t={elapsed:.1f}s] FOUND at M={M}: "
                      f"({gx}, {gy}, {gz}, {gw}) sum={s}",
                      flush=True)
            return [{
                "M": M,
                "gx": gx, "gy": gy, "gz": gz, "gw": gw,
                "sum": s,
                "derived": report,
                "elapsed_sec": elapsed,
            }]

        # No tuple worked for this M. Print progress every 5 sec.
        now = time.time()
        if verbose and (now - last_progress) > 5:
            elapsed = now - t0
            print(f"[t={elapsed:.1f}s] M={M}: no valid tuple "
                  f"({len(candidates)} candidates tried)",
                  flush=True)
            last_progress = now
    return []


def report(record: dict) -> None:
    """Pretty-print a search record."""
    g = (record["gx"], record["gy"], record["gz"], record["gw"])
    print(f"M = {record['M']}, generators = {g}, "
          f"sum = {record['sum']}")
    d = record["derived"]
    print(f"  axis shifts:        {d['axis_count']:3d}  unique: {d['axis_unique']}")
    print(f"  plane-diag shifts:  {d['plane_diag_count']:3d}  unique: {d['plane_diag_unique']}")
    print(f"  knight shifts:      {d['knight_count']:3d}  unique: {d['knight_unique']}")
    print(f"  king shifts:        {d['king_count']:3d}  unique: {d['king_unique']}")
    print(f"  total derived:      {d['total_shifts']:3d}  cross-cat unique: "
          f"{d['cross_category_unique']}")


def construct_mixed_radix_tower(
    seed_w: int = 3, ladder_coeff: int = 14,
) -> dict:
    """Directly construct a valid (M, g_x, g_y, g_z, g_w) tuple via
    the mixed-radix tower discipline (the 4D analogue of 2D's
    (67, 7) on Z_640 — see PHASE_OPERATOR_SUPPLEMENT.md §11.2).

    Two ladder coefficients matter:

      * ``ladder_coeff=7``: original Phase A bound. Each generator
        > 7 * (sum of smaller). Sufficient for C2 image bijection on
        [0, 7]^4 (no nonzero Δ ∈ [-7, 7]^4 has Σ Δ·g = 0). **NOT
        SUFFICIENT** for Phase B operator-aliasing-freedom — the
        structural gate caught a 191 = 10·g_w + 7·g_z dependency at
        the original (1523, 191, 23, 3) tuple, with Δ_w = -10 ∈
        [-14, 14] but ∉ [-7, 7].
      * ``ladder_coeff=14``: Phase B refinement. Each generator >
        14 * (sum of smaller). Guarantees no [-14, 14]^4 integer
        dependency (the box that captures cross-piece operator-shift
        differences). Brute-forced verified by
        ``has_dep_in_box(g, 14)``.

    Default is ``ladder_coeff=14`` (the production design). Pass
    ``ladder_coeff=7`` to reproduce the original Phase A construction
    that the test gate forced us to refine.

    Tower bounds:

        g_w = seed_w prime
        g_z >= ladder_coeff*g_w + 1, smallest admissible prime
        g_y >= ladder_coeff*(g_w + g_z) + 1
        g_x >= ladder_coeff*(g_w + g_z + g_y) + 1
        M   >= 7*sum + 7*(g_x + g_y) + 1, smallest prime coprime to
              all four primes (the 7*sum+max_bishop_shift+1 lower
              bound prevents wraparound for any operator shift)
    """
    g_w = seed_w
    if not _is_prime_simple(g_w):
        raise ValueError(f"seed_w={seed_w} must be prime")

    g_z = _next_prime_above(ladder_coeff * g_w + 1)
    g_y = _next_prime_above(ladder_coeff * (g_w + g_z) + 1)
    g_x = _next_prime_above(ladder_coeff * (g_w + g_z + g_y) + 1)
    s = g_w + g_z + g_y + g_x

    # Smallest M > 7*sum + max_bishop_shift that is prime + coprime.
    # max_bishop_shift = 7*(g_x + g_y); M ensures no wraparound for
    # any single-operator shift.
    max_bishop_shift = 7 * (g_x + g_y)
    M = 7 * s + max_bishop_shift + 1
    while True:
        if (_is_prime_simple(M) and
            all(M % p != 0 for p in (g_w, g_z, g_y, g_x))):
            break
        M += 1

    return {
        "M": M,
        "g_x": g_x, "g_y": g_y, "g_z": g_z, "g_w": g_w,
        "sum": s,
        "method": "mixed_radix_tower",
        "seed_w": seed_w,
        "ladder_coeff": ladder_coeff,
    }


def has_dep_in_box(
    g: tuple[int, ...], box_max: int,
) -> tuple[int, ...] | None:
    """Brute-force check: is there a nonzero
    (Δ_0, Δ_1, ..., Δ_{n-1}) ∈ [-box_max, +box_max]^n
    with Σ Δ_i · g_i = 0?

    Returns the smallest such Δ (by sum-of-absolute-values) if found,
    else None. Used as the Phase B verification gate (with box_max=14).
    """
    n = len(g)
    best: tuple[int, ...] | None = None
    best_score = float("inf")
    from itertools import product as _product
    for delta in _product(range(-box_max, box_max + 1), repeat=n):
        if all(d == 0 for d in delta):
            continue
        if sum(d * gi for d, gi in zip(delta, g)) == 0:
            score = sum(abs(d) for d in delta)
            if score < best_score:
                best = delta
                best_score = score
    return best


def _is_prime_simple(n: int) -> bool:
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0:
        return False
    i = 3
    while i * i <= n:
        if n % i == 0:
            return False
        i += 2
    return True


def _next_prime_above(n: int) -> int:
    while not _is_prime_simple(n):
        n += 1
    return n


def report_construction(record: dict) -> None:
    print(f"M = {record['M']}, generators = "
          f"({record['g_x']}, {record['g_y']}, {record['g_z']}, "
          f"{record['g_w']})  [g_x, g_y, g_z, g_w]")
    print(f"  sum                = {record['sum']}")
    print(f"  method             = {record['method']}")
    M = record["M"]
    g_x, g_y = record["g_x"], record["g_y"]
    g_z, g_w = record["g_z"], record["g_w"]
    bij = is_bijective(M, g_x, g_y, g_z, g_w)
    deriv = derived_generators(g_x, g_y, g_z, g_w, M)
    rep = derived_distinctness(deriv)
    img = phi_image(M, g_x, g_y, g_z, g_w)
    sg = is_subgroup(img, M)
    print(f"  C1 (coprime)       = "
          f"{all(_gcd(g, M) == 1 for g in (g_x, g_y, g_z, g_w))}")
    print(f"  C2 (bijection)     = {bij}")
    print(f"  C3 (non-subgroup)  = {not sg}")
    print(f"  C4 axis  unique    = {rep['axis_unique']}  "
          f"(count {rep['axis_count']})")
    print(f"  C4 plane unique    = {rep['plane_diag_unique']}  "
          f"(count {rep['plane_diag_count']})")
    print(f"  C4 knight unique   = {rep['knight_unique']}  "
          f"(count {rep['knight_count']})")
    print(f"  C4 king unique     = {rep['king_unique']}  "
          f"(count {rep['king_count']})")
    print(f"  C4 knight disjoint = {rep['knight_disjoint_from_others']}")
    print(f"  total derived shifts = {rep['total_shifts']}")


def _gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return a


if __name__ == "__main__":
    print("=" * 78)
    print("4D phase-operator design — Phase A")
    print("=" * 78)
    print()
    print("Method 1: directed mixed-radix tower construction "
          "(recommended)")
    print()
    record = construct_mixed_radix_tower(seed_w=3)
    report_construction(record)
    print()
    print(f"Pinned constants for "
          f"chess_spectral/phase_operators_4d/phase_operators_4d.py:")
    print(f"    MODULUS_4D = {record['M']}")
    print(f"    GEN_X = {record['g_x']}")
    print(f"    GEN_Y = {record['g_y']}")
    print(f"    GEN_Z = {record['g_z']}")
    print(f"    GEN_W = {record['g_w']}")

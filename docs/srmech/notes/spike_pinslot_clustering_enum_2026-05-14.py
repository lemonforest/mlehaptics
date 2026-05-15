"""
Priority 1 (Batch C concertmaster) — Pin-and-slot inner/outer planet clustering enumeration.

User-flagged gap: Batch A asked whether the observed Antikythera clustering
({Mercury, Venus} share fixed gear 51; {Mars, Jupiter, Saturn} share fixed gear 56)
is uniquely forced by gear-economy criteria or is one of several near-equivalent
choices the designers picked for non-mathematical reasons.

Ground truth from Freeth 2021 Supp PDF (cached at
docs/antikythera-maths/hoodoos/41598_2021_84310_MOESM4_ESM.pdf):

  - Mercury synodic ratio = 1513/480 = (17 x 89) / (2^5 x 3 x 5)
  - Venus   synodic ratio =  289/462 = (17^2)   / (2 x 3 x 7 x 11)
  - Mars    synodic ratio =  133/284 = (7 x 19) / (2^2 x 71)   *Freeth period*
  - Jupiter synodic ratio =   76/83  = (2^2 x 19) / 83
  - Saturn  synodic ratio =  427/442 = (7 x 61) / (2 x 13 x 17)

The bronze-shared inferior fixed gear of 51 = 3 x 17 exploits the common factor 17.
The bronze-shared superior fixed gear of 56 = 2^3 x 7 exploits the common factor 7
(shared between Mars's 7x19 numerator and Saturn's 7x61 numerator; Jupiter's
numerator (76 = 2^2 x 19) does NOT contain 7, so Jupiter does not share via this
factor — the 56 gear ties Mars/Saturn through the 7).

This script enumerates all 52 partitions of 5 planets into shared-fixed-gear
groups (Bell number B(5) = 52). For each partition, we compute:

  - The required common prime factor in each group's synodic numerator that
    can be incorporated into a single shared fixed gear (≤ 100 teeth);
  - The "gear-cost" estimate: sum over groups of (#planets - 1) gears saved by
    sharing, vs. baseline of one fixed gear per planet (5 baseline).
    A 1-planet group has zero "shared fixed gear" so costs the baseline 1 fixed
    gear; an N-planet group with a viable shared prime costs 1 shared fixed
    gear (saving N-1 over the baseline) PLUS forces every member's period-multiplier
    to be a multiple of (shared_gear / common_prime).
  - The period-fit precision: whether the chosen period ratios on each train
    can hit Freeth's attested values without exceeding tooth-count budgets.

Output: NDJSON one record per partition + a summary record.

No external deps beyond stdlib.
"""

import json
import math
import sys
from itertools import combinations
from pathlib import Path

# -----------------------------------------------------------------------------
# Ground truth from Freeth 2021 main paper (p.4) + Supp S5/S6 (cached PDFs).
# -----------------------------------------------------------------------------

PLANETS = ["Mercury", "Venus", "Mars", "Jupiter", "Saturn"]

# Period relations (synodic, years) — Freeth 2021 final-model choices.
PERIODS = {
    "Mercury": (1513, 480),  # = (17 x 89, 2^5 x 3 x 5)
    "Venus":   ( 289, 462),  # = (17^2, 2 x 3 x 7 x 11)
    "Mars":    ( 133, 284),  # = (7 x 19, 2^2 x 71)
    "Jupiter": (  76,  83),  # = (2^2 x 19, 83)
    "Saturn":  ( 427, 442),  # = (7 x 61, 2 x 13 x 17)
}

# Inferior planets use a different gear-train topology than superior planets.
TOPOLOGY = {
    "Mercury": "inferior",
    "Venus":   "inferior",
    "Mars":    "superior",
    "Jupiter": "superior",
    "Saturn":  "superior",
}

# Observed bronze configuration (the actual Antikythera).
OBSERVED_PARTITION = [("Mercury", "Venus"), ("Mars", "Jupiter", "Saturn")]
OBSERVED_INFERIOR_GEAR = 51   # 3 x 17
OBSERVED_SUPERIOR_GEAR = 56   # 2^3 x 7

# Modulo manufacturing constraints: Freeth notes tooth counts of fixed gears
# must be ≤ 100 (his explicit assertion p.4 and Supp S3 p.20) — gears bigger
# than this won't fit on b1 / CP geometry.
MAX_TOOTH_COUNT = 100

# Min tooth count: too few teeth and the gear mesh is too coarse for the
# pin-and-slot pitch (Freeth notes Saturn's small offset is the binding
# constraint at the small end). 15 teeth is the observed minimum.
MIN_TOOTH_COUNT = 15

# Integer multiplier range for each planet's period (Freeth p.50): 7-10 for
# superior planets; 3 for Mercury, 3 for Venus (Supp S5/S6).
SUP_MULT_RANGE = range(7, 11)
INF_MULT_RANGE = range(3, 6)


# -----------------------------------------------------------------------------
# Number-theory helpers (no external deps).
# -----------------------------------------------------------------------------

def prime_factors(n):
    """Return dict {prime: exponent} for positive int n."""
    out = {}
    if n <= 1:
        return out
    d = 2
    while d * d <= n:
        while n % d == 0:
            out[d] = out.get(d, 0) + 1
            n //= d
        d += 1
    if n > 1:
        out[n] = out.get(n, 0) + 1
    return out


def common_prime_factors(values):
    """Return sorted list of primes that divide every value in `values`."""
    if not values:
        return []
    common = prime_factors(values[0])
    for v in values[1:]:
        pf = prime_factors(v)
        common = {p: min(e, pf.get(p, 0)) for p, e in common.items() if p in pf}
    return sorted(common.keys())


# -----------------------------------------------------------------------------
# Set partitions of {Mercury, Venus, Mars, Jupiter, Saturn} — Bell(5) = 52.
# -----------------------------------------------------------------------------

def set_partitions(s):
    """Yield all set partitions of the list `s` as lists-of-tuples."""
    if len(s) == 0:
        yield []
        return
    if len(s) == 1:
        yield [tuple(s)]
        return
    first = s[0]
    rest = s[1:]
    for sub in set_partitions(rest):
        # Add `first` to each existing group, one variation per group.
        for i, group in enumerate(sub):
            new = list(sub)
            new[i] = tuple(sorted(group + (first,)))
            yield [tuple(sorted(g)) for g in sorted(new)]
        # OR make `first` its own new group.
        new = sub + [(first,)]
        yield [tuple(sorted(g)) for g in sorted(new)]


# -----------------------------------------------------------------------------
# Per-partition evaluator.
# -----------------------------------------------------------------------------

def evaluate_partition(part):
    """Score a partition on (a) shared-gear viability per group and (b) total
    gear count under Freeth's economy criterion (≤100 teeth, ≥15 teeth).

    Returns a record with keys:
        partition (list[list[str]])
        groups (list of group descriptors)
        viable (bool) — every group has at least one viable shared fixed gear
        total_fixed_gears (int) — count of fixed gears in this configuration
        gear_savings (int) — vs. baseline of 5 (one per planet)
        mixed_topology (bool) — any group mixes inferior + superior planets
        matches_observed (bool)
        notes (list[str])
    """
    groups_out = []
    notes = []
    viable_all = True
    mixed = False

    for group in part:
        members = list(group)
        topologies = {TOPOLOGY[p] for p in members}
        is_mixed = len(topologies) > 1
        if is_mixed:
            mixed = True
            notes.append(
                f"group {members} mixes inferior+superior; pin-and-slot topology "
                "differs (Freeth Fig 3c vs 3d), so a shared fixed gear is mechanically "
                "incompatible — both would have to be replaced by a more complex hybrid."
            )

        # The shared fixed gear must divide a common multiple of each member's
        # synodic numerator. We look for the smallest gear g with:
        #   - g divides k_p * synodic_p for every member p (where k_p is the
        #     integer multiplier for that planet's train, in the allowed range);
        #   - g <= MAX_TOOTH_COUNT.
        # For a group of size 1, the fixed gear is just (any) divisor of the
        # synodic numerator (or a small multiplier of it) within tooth-count range.
        if len(members) == 1:
            p = members[0]
            num, _den = PERIODS[p]
            # Find smallest divisor of (k * num) in range
            mult_range = INF_MULT_RANGE if TOPOLOGY[p] == "inferior" else SUP_MULT_RANGE
            smallest = None
            for k in mult_range:
                product = k * num
                for d in range(MIN_TOOTH_COUNT, MAX_TOOTH_COUNT + 1):
                    if product % d == 0:
                        smallest = (d, k)
                        break
                if smallest:
                    break
            if smallest is None:
                viable_all = False
                groups_out.append({
                    "members": members,
                    "common_primes": [],
                    "shared_fixed_gear": None,
                    "k_multipliers": {},
                    "viable": False,
                    "topology": list(topologies),
                })
                continue
            gear, k = smallest
            groups_out.append({
                "members": members,
                "common_primes": sorted(prime_factors(num).keys()),
                "shared_fixed_gear": gear,
                "k_multipliers": {p: k},
                "viable": True,
                "topology": list(topologies),
                "single_planet": True,
            })
            continue

        # Multi-planet group: search for the SMALLEST shared gear g ≤ 100 such
        # that for some choice of multipliers k_p (in each member's range),
        # g divides k_p * synodic_p for every member p.
        # Pseudo-search: enumerate g from MIN_TOOTH_COUNT upward, find feasible
        # k_p per member; if every member has at least one viable k, accept.
        best = None
        best_score = math.inf
        for g in range(MIN_TOOTH_COUNT, MAX_TOOTH_COUNT + 1):
            # For each member, find ANY k in range such that g | k * synodic
            ks = {}
            ok = True
            for p in members:
                num, _ = PERIODS[p]
                mult_range = INF_MULT_RANGE if TOPOLOGY[p] == "inferior" else SUP_MULT_RANGE
                found = None
                for k in mult_range:
                    if (k * num) % g == 0:
                        found = k
                        break
                if found is None:
                    ok = False
                    break
                ks[p] = found
            if ok:
                # Found a viable g. Score by gear size + total tooth counts of
                # multiplied-numerators (lower = more economical).
                score = g + sum(ks[p] * PERIODS[p][0] for p in members) / 1000.0
                if score < best_score:
                    best_score = score
                    best = (g, ks)

        if best is None:
            viable_all = False
            groups_out.append({
                "members": members,
                "common_primes": common_prime_factors([PERIODS[p][0] for p in members]),
                "shared_fixed_gear": None,
                "k_multipliers": {},
                "viable": False,
                "topology": list(topologies),
                "note": "no shared fixed gear ≤100 teeth exists with feasible multipliers",
            })
            continue

        gear, ks = best
        groups_out.append({
            "members": members,
            "common_primes": common_prime_factors([PERIODS[p][0] for p in members]),
            "shared_fixed_gear": gear,
            "k_multipliers": ks,
            "viable": True,
            "topology": list(topologies),
            "single_planet": False,
        })

    # Total fixed gears: one per group.
    total_fixed_gears = len(part)
    # Baseline savings: 5 - total_fixed_gears (lower = more shared).
    gear_savings = 5 - total_fixed_gears

    # Matches observed?
    sorted_part = sorted([tuple(sorted(g)) for g in part])
    sorted_observed = sorted([tuple(sorted(g)) for g in OBSERVED_PARTITION])
    matches_observed = sorted_part == sorted_observed

    return {
        "partition": [list(g) for g in part],
        "groups": groups_out,
        "viable": viable_all,
        "total_fixed_gears": total_fixed_gears,
        "gear_savings_vs_baseline": gear_savings,
        "mixed_topology": mixed,
        "matches_observed": matches_observed,
        "notes": notes,
    }


# -----------------------------------------------------------------------------
# Pareto-front analysis: 2D criterion = (total_fixed_gears, mixed_topology_penalty).
# -----------------------------------------------------------------------------

def pareto_dominates(a, b):
    """a dominates b iff a is ≤ b on every criterion and < on at least one.

    Criteria (lower is better):
      total_fixed_gears, mixed_topology (0/1), viability_violation (0/1)

    Important: viability_violation is a HARD criterion — a non-viable partition
    cannot dominate a viable one regardless of how few fixed gears it has."""
    a_fix = a["total_fixed_gears"]
    a_mix = 1 if a["mixed_topology"] else 0
    a_viol = 0 if a["viable"] else 1
    b_fix = b["total_fixed_gears"]
    b_mix = 1 if b["mixed_topology"] else 0
    b_viol = 0 if b["viable"] else 1
    le = (a_fix <= b_fix) and (a_mix <= b_mix) and (a_viol <= b_viol)
    lt = (a_fix < b_fix) or (a_mix < b_mix) or (a_viol < b_viol)
    return le and lt


def compute_pareto_front(records):
    """Pareto front restricted to viable AND topology-pure partitions.

    Non-viable or topology-mixed partitions are excluded from the front
    because Freeth-style gear economy requires both (mechanically viable
    AND respecting the inferior/superior topology divide imposed by the
    distinct pin-and-follower / pin-and-slot-eccentric devices)."""
    candidates = [r for r in records if r["viable"] and not r["mixed_topology"]]
    front = []
    for r in candidates:
        dominated = False
        for other in candidates:
            if other is r:
                continue
            if pareto_dominates(other, r):
                dominated = True
                break
        if not dominated:
            front.append(r)
    return front


# -----------------------------------------------------------------------------
# Main.
# -----------------------------------------------------------------------------

def main():
    out_path = Path(__file__).with_name(
        "spike_pinslot_clustering_enum_2026-05-14.ndjson"
    )
    records = []
    for i, part in enumerate(set_partitions(PLANETS)):
        rec = evaluate_partition(part)
        rec["partition_id"] = i
        records.append(rec)

    # Pareto front.
    front = compute_pareto_front(records)
    front_ids = {r["partition_id"] for r in front}
    for r in records:
        r["pareto_optimal"] = r["partition_id"] in front_ids

    # Count Bell number check.
    assert len(records) == 52, f"Expected B(5)=52 partitions, got {len(records)}"

    # Find the observed one's rank.
    obs = next(r for r in records if r["matches_observed"])

    # Write NDJSON.
    with open(out_path, "w", encoding="utf-8") as f:
        # Header
        f.write(json.dumps({
            "record_kind": "header",
            "script": "spike_pinslot_clustering_enum_2026-05-14.py",
            "n_partitions": len(records),
            "bell_number_5": 52,
            "max_tooth_count": MAX_TOOTH_COUNT,
            "min_tooth_count": MIN_TOOTH_COUNT,
            "observed_partition": OBSERVED_PARTITION,
            "observed_inferior_fixed_gear": OBSERVED_INFERIOR_GEAR,
            "observed_superior_fixed_gear": OBSERVED_SUPERIOR_GEAR,
            "freeth_2021_period_relations": PERIODS,
        }) + "\n")
        for r in records:
            f.write(json.dumps(r) + "\n")
        # Summary
        n_viable = sum(1 for r in records if r["viable"])
        n_viable_pure = sum(1 for r in records if r["viable"] and not r["mixed_topology"])
        n_pareto = len(front)
        summary = {
            "record_kind": "summary",
            "n_total": len(records),
            "n_viable": n_viable,
            "n_viable_unmixed_topology": n_viable_pure,
            "n_pareto_optimal": n_pareto,
            "observed_partition_pareto_optimal": obs["pareto_optimal"],
            "observed_total_fixed_gears": obs["total_fixed_gears"],
            "observed_viable": obs["viable"],
            "pareto_front_ids": sorted(front_ids),
            "pareto_front_partitions": [r["partition"] for r in front],
        }
        f.write(json.dumps(summary) + "\n")

    print(f"Wrote {out_path}")
    print()
    print(f"Total partitions: {len(records)} (Bell(5) = 52)")
    print(f"Viable (no >100 teeth): {n_viable}")
    print(f"Viable AND topology-pure (no inferior+superior mixing): {n_viable_pure}")
    print(f"Pareto-front partitions: {n_pareto}")
    print()
    print("Observed partition:")
    print(f"  {OBSERVED_PARTITION}")
    print(f"  Total fixed gears = {obs['total_fixed_gears']}")
    print(f"  Viable = {obs['viable']}")
    print(f"  Pareto-optimal = {obs['pareto_optimal']}")
    print(f"  Mixed topology = {obs['mixed_topology']}")
    print()
    print("Other Pareto-optimal partitions (rivals to the observed one):")
    for r in front:
        if not r["matches_observed"]:
            print(f"  {r['partition']}  fixed_gears={r['total_fixed_gears']}, "
                  f"mixed_topo={r['mixed_topology']}, viable={r['viable']}")
    print()
    print("Verdict candidates:")
    if n_pareto == 1 and obs["pareto_optimal"]:
        print("  UNIQUELY economical — observed is the only Pareto-optimal.")
    elif obs["pareto_optimal"]:
        print(f"  Observed is one of {n_pareto} Pareto-optimal partitions.")
        print("  Hypothesis H_economical is NOT uniquely true; H_aesthetic-or-tied has support.")
    else:
        print("  Observed is NOT Pareto-optimal — unexpected; investigate scoring.")


if __name__ == "__main__":
    main()

"""R-RBS-LM-84 — Empirical reorganization of 27-corpus map using 4 foundational
knowledge partitions (Finding 99) instead of educational subject labels.

Per Finding 99: math / communication / structure-and-order / places-and-things
are the foundational knowledge partitions that map onto Spelke core knowledge
systems AND onto A-N 14-class taxonomy (4+3+4+3=14).

Test: does the 4-partition reorganization produce TIGHTER within-class clustering
than the educational-subject grouping in 78-80?

If yes → Finding 99 empirically supported.
If no → 4-partition framework is theoretically useful but doesn't outperform
subject labels empirically (corpus may be too small / mixed to differentiate).

Reuses 80's pairwise alignment data — no recomputation needed.

PARTITION ASSIGNMENT per corpus (primary foundational partition):

  math:
    - openstax_elem_alg, openstax_inter_alg          (math irrep, direct A-N delivery)

  communication:
    - primer, grade1, grade2, grade3, grade4, grade5, grade6  (reading-as-communication ladder)
    - ec_music                                        (notation is communication)
    - ec_drawing                                      (visual communication; too small but assigned)

  structure-and-order:
    - kittredge, kirkham, strunk                      (structural rules of communication)
    - openstax_writing                                 (composition instruction = structure-of-comm)
    - childs_health                                    (body-systems classification = order)
    - ec_games                                         (game rules = explicit structure)
    - ec_baseball                                      (sport rules + statistics = structure-of-action)
    - ec_scouting                                      (instruction = structural transmission)

  places-and-things:
    - home_geography, commercial_geog, how_we_are_fed (geography = places-and-things)
    - astronomy_yf, starland                           (celestial places-and-things)
    - greeks_history                                   (places-and-things in time)
    - ec_perspective                                   (visual representation of places-and-things)
    - ec_cooking                                       (ingredients = things; recipes = procedures
                                                       binding ingredients to outcomes)
"""

import json
from collections import Counter
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
RESULTS_80 = HERE / "R-RBS-LM-80_results.json"


# Primary foundational partition assignment per corpus
PARTITION_ASSIGNMENT = {
    # MATH (A + I + J + N: anchor + cyclic + primes + rational)
    "openstax_elem_alg":   "math",
    "openstax_inter_alg":  "math",

    # COMMUNICATION (B + F + H: TLV-framing + template + introspection)
    "primer":              "communication",
    "grade1":              "communication",
    "grade2":              "communication",
    "grade3":              "communication",
    "grade4":              "communication",
    "grade5":              "communication",
    "grade6":              "communication",
    "ec_music":            "communication",   # notation IS communication
    "ec_drawing":          "communication",   # visual communication

    # STRUCTURE-AND-ORDER (D + E + G + L: pattern + catalog + search + Laplacian)
    "kittredge":           "structure_order",  # grammar instruction
    "kirkham":             "structure_order",
    "strunk":              "structure_order",
    "openstax_writing":    "structure_order",  # composition = structure-of-communication
    "childs_health":       "structure_order",  # body systems classification
    "ec_games":            "structure_order",  # explicit game rules
    "ec_baseball":         "structure_order",  # rules + statistics
    "ec_scouting":         "structure_order",  # structural instruction

    # PLACES-AND-THINGS (C + K + M: chirality + pin-slot + bind)
    "home_geography":      "places_things",
    "commercial_geog":     "places_things",
    "how_we_are_fed":      "places_things",
    "astronomy_yf":        "places_things",   # celestial places
    "starland":            "places_things",   # celestial places (narrative)
    "greeks_history":      "places_things",   # places-and-things in time
    "ec_perspective":      "places_things",   # visual representation of place
    "ec_cooking":          "places_things",   # ingredients (things) + place-of-preparation
}


def main():
    print(f"=== R-RBS-LM-84 — 4-partition reorganization of 27-corpus map ===\n")

    if not RESULTS_80.exists():
        print(f"ERROR: {RESULTS_80} not found. Run R-RBS-LM-80 first.")
        return

    data = json.loads(RESULTS_80.read_text())
    corpora_info = data["corpora"]
    pairwise = data["pairwise_alignments"]

    def get_alignment(a, b):
        return pairwise.get("|".join(sorted([a, b])), 0.0)

    # Verify all corpora are assigned
    missing = set(corpora_info.keys()) - set(PARTITION_ASSIGNMENT.keys())
    extra = set(PARTITION_ASSIGNMENT.keys()) - set(corpora_info.keys())
    if missing or extra:
        print(f"WARNING: missing {missing}; extra {extra}")
        return

    # Group corpora by foundational partition
    partitions = ["math", "communication", "structure_order", "places_things"]
    partition_members = {p: [k for k, v in PARTITION_ASSIGNMENT.items() if v == p] for p in partitions}

    print(f"--- Partition membership ---")
    for p in partitions:
        members = partition_members[p]
        print(f"  {p:<18s} (n={len(members):>2d}): {', '.join(corpora_info[m]['label'] for m in members[:3])}{', ...' if len(members) > 3 else ''}")

    # Compute within/cross ratios per partition
    print(f"\n--- 4-partition within/cross alignment analysis ---\n")
    print(f"  {'partition':<18s} {'n':>3s} {'within':>9s} {'cross':>9s} {'ratio':>7s}")

    partition_stats = {}
    for p in partitions:
        members = partition_members[p]
        if len(members) < 2:
            within_avg = None
        else:
            within = [get_alignment(a, b) for i, a in enumerate(members) for b in members[i+1:]]
            within_avg = float(np.mean(within))
        cross = []
        for a in members:
            for k in corpora_info:
                if k == a or k in members: continue
                cross.append(get_alignment(a, k))
        cross_avg = float(np.mean(cross)) if cross else 0.0
        ratio = within_avg / cross_avg if (within_avg is not None and cross_avg > 0) else None
        wavg_str = f"{within_avg:+.4f}" if within_avg is not None else "  n/a "
        ratio_str = f"{ratio:.2f}" if ratio is not None else " n/a "
        print(f"  {p:<18s} {len(members):>3d} {wavg_str:>9s} {cross_avg:>+9.4f} {ratio_str:>7s}")
        partition_stats[p] = {"n": len(members), "within": within_avg, "cross": cross_avg, "ratio": ratio}

    # Inter-partition mean alignment matrix
    print(f"\n--- 4-partition × 4-partition alignment matrix ---")
    print(f"  {'A \\\\ B':<18s}", end="")
    for p in partitions: print(f"{p[:11]:>13s}", end="")
    print()
    inter_partition = {}
    for pa in partitions:
        print(f"  {pa[:18]:<18s}", end="")
        for pb in partitions:
            members_a = partition_members[pa]
            members_b = partition_members[pb]
            if pa == pb:
                if len(members_a) < 2: print(f"{'-':>13s}", end=""); continue
                pairs = [get_alignment(a, b) for i, a in enumerate(members_a) for b in members_a[i+1:]]
            else:
                pairs = [get_alignment(a, b) for a in members_a for b in members_b]
            m = float(np.mean(pairs)) if pairs else 0.0
            inter_partition[f"{pa}|{pb}"] = m
            print(f"{m:>+13.4f}", end="")
        print()

    # Comparison to 78-80's educational-subject grouping
    print(f"\n--- Comparison to educational-subject grouping (80 baseline) ---")
    # Read subject_stats from 80 results
    subject_stats_80 = data["subject_stats"]
    print(f"  {'old subject':<18s} {'n':>3s} {'within':>9s} {'cross':>9s} {'ratio':>7s}")
    for sj, st in subject_stats_80.items():
        ratio = st.get("ratio")
        wavg = st.get("within_avg")
        cross = st.get("cross_avg")
        wavg_str = f"{wavg:+.4f}" if wavg is not None else "  n/a "
        ratio_str = f"{ratio:.2f}" if ratio is not None else " n/a "
        print(f"  {sj:<18s} {st.get('n_members', 0):>3d} {wavg_str:>9s} {cross if cross is not None else 0:>+9.4f} {ratio_str:>7s}")

    # === Verdict ===
    print(f"\n=== Verdict — does 4-partition reorganization improve clustering? ===\n")

    # Compute aggregate measures
    new_ratios = [s["ratio"] for s in partition_stats.values() if s["ratio"] is not None]
    old_ratios = [s.get("ratio") for s in subject_stats_80.values() if s.get("ratio") is not None]

    new_mean_ratio = float(np.mean(new_ratios)) if new_ratios else 0.0
    old_mean_ratio = float(np.mean(old_ratios)) if old_ratios else 0.0

    new_min = float(min(new_ratios)) if new_ratios else 0.0
    old_min = float(min(old_ratios)) if old_ratios else 0.0

    print(f"  4-partition mean within/cross ratio (multi-corpus only): {new_mean_ratio:.3f}")
    print(f"  Educational-subject mean within/cross ratio (80):        {old_mean_ratio:.3f}")
    print(f"  Difference: {new_mean_ratio - old_mean_ratio:+.3f}")
    print()
    print(f"  4-partition min ratio:    {new_min:.3f}")
    print(f"  Subject min ratio (80):   {old_min:.3f}")
    print(f"  Difference: {new_min - old_min:+.3f}  (higher min = no partition is structurally outlier)")

    # Check if all 4 partitions show ratio > 1.0 (= meaningful within-class clustering)
    all_above_1 = all(r > 1.0 for r in new_ratios)
    print(f"\n  All 4 partitions have within/cross > 1.0? {all_above_1}")

    if all_above_1 and new_min > 1.2:
        verdict = "FINDING 99 SUPPORTED: 4-partition framework produces meaningful within-class clustering for all 4 partitions. The foundational partition taxonomy is empirically validated."
    elif all_above_1:
        verdict = "FINDING 99 PARTIALLY SUPPORTED: all 4 partitions cluster but some weakly. Reorganization is useful but not dramatic improvement."
    elif new_min > 0.9:
        verdict = "FINDING 99 NEUTRAL: 4-partition framework comparable to subject grouping. Theoretical clarity but no empirical tightening."
    else:
        verdict = "FINDING 99 WEAKLY-FALSIFIED: some partitions don't cluster cleanly; assignment may need refinement or corpus may not support 4-partition discrimination."
    print(f"\n  {verdict}")

    out = {
        "partition": "R-RBS-LM-84",
        "n_corpora": len(corpora_info),
        "foundational_partitions": partitions,
        "partition_assignment": PARTITION_ASSIGNMENT,
        "partition_stats": partition_stats,
        "inter_partition_alignment": inter_partition,
        "new_mean_ratio": new_mean_ratio,
        "old_mean_ratio": old_mean_ratio,
        "verdict": verdict,
    }
    out_path = HERE / "R-RBS-LM-84_results.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()

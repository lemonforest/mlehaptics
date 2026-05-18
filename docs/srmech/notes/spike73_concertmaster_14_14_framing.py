"""Spike #73 — '14 CT + 14 FL' framing clarification.

Per Spike #67 F2 fermata. Tests which construction (if any) produces a
14 + 14 clean count from the octonion-triple / Fano structure.

Open-access: Baez 2002 arXiv:math/0105155 (PDF-verified); Spike #58.N
project-internal. NO citation hallucination.

Per [[feedback_no_privileged_primitive_classes]]: any mapping must live
inside 14-class A-N vocabulary; no new class.
"""

import itertools
from collections import Counter
from typing import Tuple, List, Dict, Set, FrozenSet


# Standard 7 Fano lines, project canonical (Spike #58.N + Spike #67):
FANO_LINES = [
    (1, 2, 3),
    (1, 4, 5),
    (1, 7, 6),  # NOTE: ordered (1,7,6) per canonical, but as a SET = {1,6,7}
    (2, 4, 6),
    (2, 5, 7),
    (3, 4, 7),
    (3, 6, 5),  # SET = {3,5,6}
]

# Unordered as sets (for incidence checks):
FANO_SETS = [frozenset(L) for L in FANO_LINES]


# =====================================================================
# Candidate 1: Directed Fano lines (forward + reverse cycles)
# =====================================================================
# Each unordered triple {a,b,c} has TWO cyclic orientations:
#   forward:  a -> b -> c -> a   (induces e_a e_b = +e_c, e_b e_c = +e_a, e_c e_a = +e_b)
#   reverse:  a -> c -> b -> a   (induces e_a e_c = -e_b, e_c e_b = -e_a, e_b e_a = -e_c)
# The two orientations differ by sign in the octonion product.
# So unordered Fano lines = 7; directed (orientation-bearing) = 14.

def candidate_1_directed_fano():
    """Count directed Fano lines: 7 unordered x 2 orientations = 14."""
    directed = []
    for a, b, c in FANO_LINES:
        directed.append(("forward", a, b, c))   # a->b->c
        directed.append(("reverse", a, c, b))   # a->c->b  (= reverse cycle)
    return {
        "count_unordered_lines": 7,
        "count_directed_lines": len(directed),
        "is_14": len(directed) == 14,
        "interpretation": (
            "7 unordered Fano lines x 2 cyclic orientations = 14. "
            "Each orientation is a distinct algebraic structure constant: "
            "forward gives e_a e_b = +e_c; reverse gives e_a e_c = -e_b. "
            "Class-operator support: Class C cascade-orientation provides "
            "the orientation bit; Class I cyclic-group provides the cycle."
        ),
    }


# =====================================================================
# Candidate 2: CT 3-cycle + FL 3-cycle directed (Spike #58.N (1,3,3))
# =====================================================================
# Spike #58.N (1,3,3) decomposition with p = e_1:
#   FIXED line: (2,4,6)            -- polar = e_1
#   FL 3-cycle: (1,2,3),(1,4,5),(1,6,7)   -- lines through p
#   CT 3-cycle: (2,5,7),(3,4,7),(3,5,6)   -- complementary triple
# Each 3-cycle has 3 unordered triples; if each can be oriented two ways,
# 3 * 2 = 6 directed entries per 3-cycle. NOT 14.
# Alternative: total directed = 7 * 2 = 14 = FIXED-direction(1*2) + FL-cycle(3*2) + CT-cycle(3*2) = 2+6+6 = 14.
# So directed-Fano partitions cleanly across the (1,3,3) decomposition.

def candidate_2_partition_within_directed_14():
    """Verify directed 14 partitions across (1,3,3) decomposition."""
    fixed_line = frozenset({2, 4, 6})           # 1 unordered, 2 directed
    fl_lines = [frozenset({1, 2, 3}),
                frozenset({1, 4, 5}),
                frozenset({1, 6, 7})]            # 3 unordered, 6 directed
    ct_lines = [frozenset({2, 5, 7}),
                frozenset({3, 4, 7}),
                frozenset({3, 5, 6})]            # 3 unordered, 6 directed

    # Sanity: are all 7 lines covered?
    all_lines_partition = [fixed_line] + fl_lines + ct_lines
    all_sets = set(all_lines_partition)
    canonical_sets = set(FANO_SETS)
    cover_ok = all_sets == canonical_sets

    fixed_directed = 1 * 2
    fl_directed = 3 * 2
    ct_directed = 3 * 2
    total_directed = fixed_directed + fl_directed + ct_directed
    return {
        "partition_covers_all_7_fano_lines": cover_ok,
        "fixed_unordered": 1, "fixed_directed": fixed_directed,
        "fl_unordered": 3, "fl_directed": fl_directed,
        "ct_unordered": 3, "ct_directed": ct_directed,
        "total_unordered": 7, "total_directed": total_directed,
        "is_14": total_directed == 14,
        "interpretation": (
            "Directed Fano-14 partitions cleanly across Spike #58.N (1,3,3): "
            "FIXED 2 + FL 6 + CT 6 = 14. NOT a 14+14 (CT vs FL) split — "
            "the FL/CT 3-cycles each give 6 directed lines, not 14."
        ),
    }


# =====================================================================
# Candidate 3: CT directed 6 + FL directed 6 + FIXED 2 = 14 (single 14, not 14:14)
# =====================================================================
# Same as Candidate 2 but framed as "is there a way the FL contribution = 14
# and CT contribution = 14"? No: each is only 6 directed lines. 14 only
# appears at the TOTAL directed-Fano level.


# =====================================================================
# Candidate 4: Anticommutator pairs (21) — does not give 14
# =====================================================================
# C(7,2) = 21 imaginary-unit pairs. NOT 14. Ruled out.

def candidate_4_anticomm_pairs():
    return {
        "count": 21,
        "is_14": False,
        "comment": "C(7,2) = 21 pairs, not 14. Ruled out.",
    }


# =====================================================================
# Candidate 5: Non-associative triples among unordered C(7,3) = 28; ordered = 28*2 = 56
# =====================================================================

def candidate_5_nonassoc_directed():
    """28 non-associative unordered. If we orient each: 28 * 2 = 56. Not 14."""
    return {
        "unordered_nonassoc": 28, "directed_nonassoc": 56, "is_14": False,
        "comment": "Non-associative count 28 or 56 != 14.",
    }


# =====================================================================
# Candidate 6: 3x3 FL x CT grid cells = 9; doubled per row = 3 doubled labels (Spike #58.N)
# =====================================================================
# Spike #58.N showed 9 of 9 FL x CT pairs non-empty, each pair shares
# exactly one imaginary unit. Doubled per row count = 3; singleton per
# row count = 3. Total cells = 9; with directed pairing = 18. Not 14.

def candidate_6_fl_ct_grid():
    return {
        "grid_cells": 9, "directed_cells": 18, "is_14": False,
        "comment": "FL x CT 3x3 grid = 9 (unordered) or 18 (directed). != 14.",
    }


# =====================================================================
# Candidate 7: Two disjoint 14s — directed FL-only (?) + directed CT-only (?)
# =====================================================================
# Could "14 CT + 14 FL" refer to TWO INDEPENDENT directed-Fano-graphs,
# one per "side"? In Spike #58.N: FL = {(1,2,3),(1,4,5),(1,6,7)},
# CT = {(2,5,7),(3,4,7),(3,5,6)}. These together cover 6 of 7 lines;
# adding FIXED (2,4,6) gives all 7.
#
# If we directional-tag each of the 3 FL-lines: 3*2 = 6 directed FL.
# Same for CT: 6 directed. Each gives 6, not 14.
#
# Maybe the conductor meant: directed Fano of 7 lines, viewed from each
# side independently. Both sides see the SAME 14 directed lines (just
# rooted differently)? That's two copies of the 14, not 14+14 distinct.

def candidate_7_two_copies_of_14():
    """Two copies of the directed-Fano-14, indexed by orientation choice."""
    forward_total = 7  # 7 forward orientations
    reverse_total = 7  # 7 reverse orientations
    return {
        "forward_orientations": forward_total,
        "reverse_orientations": reverse_total,
        "total": forward_total + reverse_total,
        "is_14": (forward_total + reverse_total) == 14,
        "is_14_plus_14": False,
        "interpretation": (
            "7 forward + 7 reverse = 14 directed Fano lines, total. "
            "NOT 14 + 14 = 28. The 'CT' and 'FL' label-pair would have "
            "to refer to two disjoint sets of 14 each, totalling 28. "
            "No octonion-Fano construction gives that."
        ),
    }


# =====================================================================
# Candidate 8: Cl(0,7) generator-product space — does it give 14?
# =====================================================================
# Cl(0,7) basis: 2^7 = 128 elements. Bivectors L_i L_j (i<j) = C(7,2) = 21. Not 14.
# Trivectors L_i L_j L_k = C(7,3) = 35. Not 14.
# Bivector + trivector = 21 + 35 = 56. Not 14.

def candidate_8_clifford_basis():
    return {
        "bivectors_C72": 21, "trivectors_C73": 35,
        "total": 56, "is_14": False,
        "comment": "Cl(0,7) bivector/trivector counts don't give 14 directly.",
    }


# =====================================================================
# Candidate 9: 4-way sector (Spike #78) x 7 Fano lines = 28; / 2 = 14?
# =====================================================================
# Spike #78 4-way sector decomposition = (gamma_5, i*omega_7) = 2x2 = 4.
# 4 sectors x 7 lines = 28. Not 14.
# 7 lines x 2 orientations (per Candidate 1) = 14 directed. CONSISTENT
# with the 4-way sector if we collapse the gamma_5 axis (4D chirality
# is "downstream", lives in 4D not 7D internal):
#   Internal-only sector axis = i*omega_7 = 2 (orient+/orient-).
#   7 lines x 2 orientations = 14 directed Fano = Class C orientation
#   on top of 7 Class I cyclic-group lines.

def candidate_9_4way_sector_composition():
    """Does 4-way sector x Fano structure naturally give 14?"""
    return {
        "fano_lines": 7,
        "internal_orientation_axis": 2,  # iomega_7 = +/-1
        "directed_fano_lines": 7 * 2,
        "is_14": (7 * 2) == 14,
        "interpretation": (
            "Internal orientation axis (i*omega_7) x 7 Fano lines = 14. "
            "Matches Candidate 1 (directed Fano) via Class L sub-op "
            "(signed-Laplacian / Wick-rotation, dissolved Class O 2026-05-16). "
            "Class C cascade-orientation provides the directionality; "
            "Class I provides the cyclic group; Class L sub-op provides "
            "the signed-metric structure. Composes with Spike #78 4-way "
            "sector by treating gamma_5 as the orthogonal external axis."
        ),
    }


# =====================================================================
# Bit-exact octonion structure-constant computation
# =====================================================================
# Verify that the 14 directed Fano lines correspond bit-exactly to the
# 14 non-zero structure-constants (f_{ijk} where e_i e_j = f_{ijk} e_k) of
# the octonion algebra, modulo identification of the cyclic 3-orbits.

def octonion_structure_constants():
    """For each (i,j) with i,j in 1..7 and i != j, compute e_i e_j = +-e_k.
    Returns the 42 (i,j,k,sign) triples (since 7*6 = 42 ordered pairs).
    Group by unordered {i,j,k}: each Fano line has 6 ordered pairs (forward + reverse).
    """
    # Build multiplication table from canonical FANO_LINES with cyclic orientation.
    table: Dict[Tuple[int, int], Tuple[int, int]] = {}
    # Identity row
    for i in range(8):
        table[(0, i)] = (1, i); table[(i, 0)] = (1, i)
    # e_i * e_i = -1
    for i in range(1, 8):
        table[(i, i)] = (-1, 0)
    # Cyclic Fano lines
    for a, b, c in FANO_LINES:
        table[(a, b)] = (1, c); table[(b, c)] = (1, a); table[(c, a)] = (1, b)
        table[(b, a)] = (-1, c); table[(c, b)] = (-1, a); table[(a, c)] = (-1, b)

    # Collect all signed ordered triples (i, j, k, sign):
    ordered = []
    for i in range(1, 8):
        for j in range(1, 8):
            if i == j: continue
            sign, k = table[(i, j)]
            if k != 0 and sign != 0:
                ordered.append((i, j, k, sign))
    return ordered, table


def candidate_10_signed_structure_constants():
    """Each Fano line contributes 6 ordered pairs (3 forward + 3 reverse).
    Group by sign:
      +1 ordered triples = 21 (forward cycles, 3 per line x 7 lines)
      -1 ordered triples = 21 (reverse cycles, 3 per line x 7 lines)
    So 21 + 21 = 42 ordered, not 14.

    To get 14: collapse the cyclic 3-orbit to "one element per cycle".
    7 forward 3-orbits + 7 reverse 3-orbits = 14 directed-cycle equivalence
    classes. THIS is what 'directed Fano = 14' means.
    """
    ordered, _ = octonion_structure_constants()
    # Group by (sign, frozenset({i,j,k})):
    forward_classes = set()  # set of frozensets (the 7 lines, each appears with cyclic 3-orbit forward)
    reverse_classes = set()
    for i, j, k, s in ordered:
        triple = frozenset({i, j, k})
        if s == +1:
            forward_classes.add(triple)
        else:
            reverse_classes.add(triple)

    # Each Fano line appears in BOTH forward and reverse classes (3-orbits sum same set):
    # forward_classes = reverse_classes = the 7 Fano sets.
    # The 14 directed = (forward) + (reverse) treated as DISTINCT.
    n_directed_cycles = len(forward_classes) + len(reverse_classes)
    return {
        "n_signed_ordered_pairs": len(ordered),  # = 42
        "n_forward_3orbits": len(forward_classes),  # = 7
        "n_reverse_3orbits": len(reverse_classes),  # = 7
        "n_directed_cycles": n_directed_cycles,    # = 14
        "is_14_directed": n_directed_cycles == 14,
        "interpretation": (
            "Bit-exact: 42 signed ordered pairs (7 lines x 6 ordered pairs); "
            "collapsed to cyclic 3-orbits = 7 forward + 7 reverse = 14 "
            "directed Fano cycles. THIS is the canonical 14 reading."
        ),
    }


if __name__ == "__main__":
    import json
    import sys
    sys.stdout.reconfigure(encoding="utf-8")

    print("=" * 70)
    print("Spike #73 — '14 CT + 14 FL' framing clarification")
    print("=" * 70)
    print()

    candidates = [
        ("C1 directed_fano", candidate_1_directed_fano()),
        ("C2 partition_within_14", candidate_2_partition_within_directed_14()),
        ("C4 anticomm_pairs", candidate_4_anticomm_pairs()),
        ("C5 nonassoc_directed", candidate_5_nonassoc_directed()),
        ("C6 fl_ct_grid", candidate_6_fl_ct_grid()),
        ("C7 two_copies_of_14", candidate_7_two_copies_of_14()),
        ("C8 clifford_basis", candidate_8_clifford_basis()),
        ("C9 4way_sector_composition", candidate_9_4way_sector_composition()),
        ("C10 signed_structure_constants", candidate_10_signed_structure_constants()),
    ]

    for label, result in candidates:
        print(f"--- {label} ---")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print()

    print("=" * 70)
    print("Summary verdict")
    print("=" * 70)
    print()
    print("CANDIDATES PRODUCING 14:")
    matches_14 = [(label, r) for label, r in candidates
                  if r.get("is_14") or r.get("is_14_directed")]
    for label, r in matches_14:
        print(f"  - {label}")
    print()
    print("CANDIDATES PRODUCING 14 + 14 (= 28 SPLIT):")
    matches_14_14 = [(label, r) for label, r in candidates if r.get("is_14_plus_14")]
    if not matches_14_14:
        print("  - NONE.")
    print()
    print("Verdict: VOCAB-MATCHES-DIRECTED-FANO-7+7 = 14 (single 14, not 14+14).")
    print("        The conductor's '14 CT + 14 FL' is most consistent with a")
    print("        REDUNDANT-LABEL reading of the SAME 14 directed Fano cycles,")
    print("        where CT and FL are two views of the same partition's")
    print("        directed structure. NO octonion-Fano construction produces")
    print("        14 + 14 = 28 disjoint.")

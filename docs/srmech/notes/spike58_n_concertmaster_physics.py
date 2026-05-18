"""
Spike #58.N: physical-interpretation testing for (1,3,3) canonical structure.

Foundations verified in orbits.py:
- 1 fixed H = line {2,4,6} (polar = e_1)
- Fano-line 3-cycle (FL) = lines through e_1: {(1,2,3),(1,4,5),(1,6,7)}
  Polars {4,2,6} XOR to 0 (the polars LIE ON the fixed line itself)
- Complementary triangle 3-cycle (CT) = lines off e_1, not fixed:
  {(2,5,7),(3,4,7),(3,5,6)}
  Polars {5,3,7} XOR to 1 (= polar of fixed line, the canonical direction)
"""

import itertools
import collections

ct_lines = [frozenset({2,5,7}), frozenset({3,4,7}), frozenset({3,5,6})]
fl_lines = [frozenset({1,2,3}), frozenset({1,4,5}), frozenset({1,6,7})]

print("=" * 70)
print("CANDIDATE A: Three-generation identification")
print("=" * 70)

print("Fano-line 3-cycle pairwise intersections:")
for i, j in itertools.combinations(range(3), 2):
    common = fl_lines[i] & fl_lines[j]
    print(f"  {tuple(sorted(fl_lines[i]))} cap {tuple(sorted(fl_lines[j]))} = {tuple(sorted(common))}")
common_fl = fl_lines[0] & fl_lines[1] & fl_lines[2]
print(f"  triple intersection: {tuple(sorted(common_fl))}")

print("\nComplementary-triangle pairwise intersections:")
for i, j in itertools.combinations(range(3), 2):
    common = ct_lines[i] & ct_lines[j]
    print(f"  {tuple(sorted(ct_lines[i]))} cap {tuple(sorted(ct_lines[j]))} = {tuple(sorted(common))}")
common_ct = ct_lines[0] & ct_lines[1] & ct_lines[2]
print(f"  triple intersection: {tuple(sorted(common_ct))}")

print()
print("READING:")
print("  FL 3-cycle: all three H share C_e1 = R<1, e1>. Three different")
print("    quaternionic extensions of the SAME complex line.")
print("    -> Manogue-Dray three-generation structure: three H-extensions")
print("       of a common C-subalgebra.")
print("  CT 3-cycle: pairwise intersections are DIFFERENT C-subalgebras")
print("    (C_e7, C_e3, C_e5). Triple intersection empty (no shared im unit).")
print("    -> Structurally different; not the three-generation pattern.")

print()
print("=" * 70)
print("CANDIDATE B: SU(3)_c color from XOR closure")
print("=" * 70)

# CT polars 5 XOR 3 XOR 7 = 1
# Three-element constraint summing to a fixed canonical direction =
# discrete shadow of color singlet condition r + g + b -> 1.
# But Z/2^3 != SU(3); promoting to continuous SU(3) needs Spike #58.K Cl(6).

print("  CT polars: 5, 3, 7 -> XOR = 1 = polar(fixed line)")
print("  Reading: discrete Z/2^3 shadow of SU(3)_c r+g+b -> singlet condition.")
print("  Continuous SU(3)_c lives upstairs (Spike #58.K Cl(6) absorption).")
print("  -> CT 3-cycle = COLOR DEGREE OF FREEDOM (one substrate per color slot)")

print()
print("=" * 70)
print("CANDIDATE C: Yukawa triple-vertex / non-associativity")
print("=" * 70)

# Octonion multiplication table
OCTONION_MULT = {}
def build_mult():
    lines = [(1,2,3),(1,4,5),(1,7,6),(2,4,6),(2,5,7),(3,4,7),(3,6,5)]
    for (a,b,c) in lines:
        OCTONION_MULT[(a,b)] = (1, c)
        OCTONION_MULT[(b,c)] = (1, a)
        OCTONION_MULT[(c,a)] = (1, b)
        OCTONION_MULT[(b,a)] = (-1, c)
        OCTONION_MULT[(c,b)] = (-1, a)
        OCTONION_MULT[(a,c)] = (-1, b)
    for i in range(1, 8):
        OCTONION_MULT[(i, i)] = (-1, 0)

build_mult()

def in_common_H(triple):
    all_lines = [frozenset(l) for l in [(1,2,3),(1,4,5),(1,7,6),(2,4,6),(2,5,7),(3,4,7),(3,6,5)]]
    for L in all_lines:
        if all(e in L for e in triple):
            return True
    return False

# CT triples
ct_units = [list({2,5,7}), list({3,4,7}), list({3,5,6})]
fl_units = [list({1,2,3}), list({1,4,5}), list({1,6,7})]

ct_total = 0
ct_assoc_nonzero = 0
for a in ct_units[0]:
    for b in ct_units[1]:
        for c in ct_units[2]:
            if len({a,b,c}) < 3:
                continue
            ct_total += 1
            if not in_common_H({a,b,c}):
                ct_assoc_nonzero += 1
print(f"  CT triples (a from H_CT1, b from H_CT2, c from H_CT3, all distinct):")
print(f"    {ct_assoc_nonzero}/{ct_total} have non-associative product (associator != 0)")

fl_total = 0
fl_assoc_nonzero = 0
for a in fl_units[0]:
    for b in fl_units[1]:
        for c in fl_units[2]:
            if len({a,b,c}) < 3:
                continue
            fl_total += 1
            if not in_common_H({a,b,c}):
                fl_assoc_nonzero += 1
print(f"  FL triples (a from H_FL1, b from H_FL2, c from H_FL3, all distinct):")
print(f"    {fl_assoc_nonzero}/{fl_total} have non-associative product")

print()
print("READING:")
print("  CT triples are MAXIMALLY non-associative (when a/b/c distinct).")
print("  FL triples are LESS non-associative (e_1 shared -> partial closure).")
print("  -> CT 3-cycle produces the non-vanishing associators that")
print("     algebraic SM derivations identify as Yukawa source terms.")

print()
print("=" * 70)
print("CANDIDATE D: Both 3-cycles paired -> 3x3 grid (generations x colors)")
print("=" * 70)

print("3 x 3 grid of intersections (FL row, CT col):")
intersect_grid = collections.defaultdict(list)
print(f"  {'':30}", end='')
for ct_l in ct_lines:
    print(f"{str(tuple(sorted(ct_l))):>15}", end='')
print()
for fl_l in fl_lines:
    print(f"  FL {str(tuple(sorted(fl_l))):<27}", end='')
    for ct_l in ct_lines:
        common = fl_l & ct_l
        cell = str(tuple(sorted(common))) if common else '-'
        print(f"{cell:>15}", end='')
    print()

# Compile the 3x3 intersection table cleanly:
print("\n3x3 pair table (single shared imaginary unit when non-empty):")
for fl_l in fl_lines:
    for ct_l in ct_lines:
        common = fl_l & ct_l
        intersect_grid[(tuple(sorted(fl_l)), tuple(sorted(ct_l)))] = tuple(sorted(common))
        print(f"  FL{tuple(sorted(fl_l))} x CT{tuple(sorted(ct_l))} -> {tuple(sorted(common)) if common else 'empty'}")

# Count distribution: which CT lines pair non-trivially with each FL line?
print("\nPer-FL-line: count of CT lines with NON-EMPTY intersection:")
for fl_l in fl_lines:
    counts = sum(1 for ct_l in ct_lines if (fl_l & ct_l))
    print(f"  FL {tuple(sorted(fl_l))}: {counts} CT lines intersect")

print("\nPer-CT-line: count of FL lines with non-empty intersection:")
for ct_l in ct_lines:
    counts = sum(1 for fl_l in fl_lines if (fl_l & ct_l))
    print(f"  CT {tuple(sorted(ct_l))}: {counts} FL lines intersect")

# Are all 9 pairs non-empty (= a clean 3x3 grid)?
all_pairs = [(fl_l & ct_l) for fl_l in fl_lines for ct_l in ct_lines]
nonempty = sum(1 for p in all_pairs if p)
print(f"\nTotal non-empty FL x CT pairs: {nonempty} / 9")

# Examine which units appear across the grid
all_intersect_units = set()
for fl_l in fl_lines:
    for ct_l in ct_lines:
        all_intersect_units |= (fl_l & ct_l)
print(f"Imaginary units appearing in any FL x CT intersection: {sorted(all_intersect_units)}")
print("(Should be {2,3,4,5,6,7} = all except e_1 (FL hub) and the fixed-line polar)")

PYEOF

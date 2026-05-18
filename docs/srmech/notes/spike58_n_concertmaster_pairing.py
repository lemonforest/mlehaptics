"""
Spike #58.N final test: does the 3x3 FL x CT grid match the SM
(generation x color) structure?

We established:
- 9 of 9 FL x CT pairs are non-empty.
- Each pair (FL_i, CT_j) shares exactly one imaginary unit u_ij in {2,3,4,5,6,7}.
- The unit u_ij is the "label" of that grid cell.

The 3x3 cell labels (using physics convention: row=generation, col=color):
"""

import collections

ct_lines = [frozenset({2,5,7}), frozenset({3,4,7}), frozenset({3,5,6})]
fl_lines = [frozenset({1,2,3}), frozenset({1,4,5}), frozenset({1,6,7})]

# Build the 3x3 label matrix
fl_sorted = [tuple(sorted(l)) for l in fl_lines]
ct_sorted = [tuple(sorted(l)) for l in ct_lines]

label_matrix = []
for fl in fl_lines:
    row = []
    for ct in ct_lines:
        common = fl & ct
        row.append(next(iter(common)) if common else None)
    label_matrix.append(row)

print("3x3 label matrix (rows=FL generations, cols=CT colors):")
print(f"  {'':12}", end='')
for c in ct_sorted:
    print(f"  CT{c}", end='')
print()
for i, fl in enumerate(fl_sorted):
    print(f"  FL{fl}  ", end='')
    for j in range(3):
        print(f"     e_{label_matrix[i][j]}", end='')
    print()

# The matrix:
# Row 1 (FL gen 1, "lightest"):   2  3  3
# Row 2 (FL gen 2, "middle"):     5  4  5
# Row 3 (FL gen 3, "heaviest"):   7  7  6
print()
print("=== Counting cell-label distribution ===")
from collections import Counter
cells = [label_matrix[i][j] for i in range(3) for j in range(3)]
print(f"Cell labels: {cells}")
print(f"Count per label: {Counter(cells)}")

# Each label appears either 1 or 2 times. NOT a clean 3x3 permutation.
# This rules out a 1-to-1 (gen,color) -> imaginary-unit bijection.

# Test ROW STRUCTURE: are the labels in each row the same line?
print()
print("=== Row structure (each FL row's labels) ===")
for i, fl in enumerate(fl_sorted):
    row_labels = set(label_matrix[i])
    print(f"  FL{fl} row labels: {sorted(row_labels)}")
    # Test: is this set a Fano line?
    if frozenset(row_labels) in [frozenset(l) for l in [(1,2,3),(1,4,5),(1,6,7),(2,4,6),(2,5,7),(3,4,7),(3,5,6)]]:
        print(f"    -> IS a Fano line!")

print()
print("=== Column structure (each CT col's labels) ===")
for j, ct in enumerate(ct_sorted):
    col_labels = set(label_matrix[i][j] for i in range(3))
    print(f"  CT{ct} col labels: {sorted(col_labels)}")
    if frozenset(col_labels) in [frozenset(l) for l in [(1,2,3),(1,4,5),(1,6,7),(2,4,6),(2,5,7),(3,4,7),(3,5,6)]]:
        print(f"    -> IS a Fano line!")

print()
print("CRITICAL FINDING:")
print("  Row labels: each FL row's distinct labels = the FL line MINUS {1} = 2 distinct elements")
print("    (because FL line through e_1 has 3 elements, one is e_1, the other 2 fill all 3 CT cols)")
print("  Column labels: each CT col's distinct labels = the CT line itself = 3 distinct elements")
print("  So the row dimension is 'compressed' (one label appears twice per row) and the column")
print("    dimension is faithful.")
print()
print("This breaks ASYMMETRICALLY: FL row 'leaks' label info; CT col is faithful.")
print("If FL = generations and CT = colors, then:")
print("  - The 'color' label is well-defined per row (CT line).")
print("  - The 'generation' label has degeneracy (the doubled e_i per row).")

# Examine the doubled label pattern per row:
print()
print("=== Per-row repeated labels ===")
for i, fl in enumerate(fl_sorted):
    row = label_matrix[i]
    counts = Counter(row)
    doubled = [k for k, v in counts.items() if v == 2]
    singles = [k for k, v in counts.items() if v == 1]
    print(f"  FL{fl}: doubled={doubled}, single={singles}")

print()
print("READING:")
print("  Doubled labels per row = e_3, e_5, e_7 respectively (FL gen 1/2/3).")
print("  These are EXACTLY the polars of the CT 3-cycle (5,3,7).")
print("  So each FL generation 'connects twice' to one specific CT-polar.")
print("  This is a structural ASYMMETRY between the two 3-cycles -- they are")
print("  NOT a clean (generation x color) product.")

# Examine which CT column the doubled label lies in for each row
print()
print("=== Cross-pattern: which CT col carries the doubled label per FL row ===")
for i, fl in enumerate(fl_sorted):
    row = label_matrix[i]
    counts = Counter(row)
    doubled = [k for k, v in counts.items() if v == 2][0]
    # which cols carry the doubled label?
    doubled_cols = [j for j in range(3) if row[j] == doubled]
    single_col = [j for j in range(3) if row[j] != doubled][0]
    print(f"  FL{fl}: doubled e_{doubled} in CT cols {[ct_sorted[c] for c in doubled_cols]},")
    print(f"           single label e_{row[single_col]} in CT col {ct_sorted[single_col]}")

print()
print("=== Verdict on Candidate D (generations x colors paired) ===")
print("  9 = 3x3 cell count matches SM lepton+neutrino+quark family count by generation.")
print("  BUT the grid is NOT a clean tensor product:")
print("    - Each FL row has one doubled label (degeneracy)")
print("    - Each CT col is a complete Fano line (no degeneracy)")
print("  The asymmetry reads as: FL=generations is 'noisy', CT=colors is 'clean'.")
print("  This is consistent with: physics distinguishes colors sharply (gauge SU(3))")
print("    but generations are intermixed (CKM/PMNS mixing).")
print("  So Candidate D has support BUT requires the doubled-label pattern to be")
print("  interpreted as CKM-like mixing, not literal 3x3 product.")


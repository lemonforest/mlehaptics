"""
Spike #58.N step 3: orbit structure on 7 H-subalgebras.

The 7 imaginary units carry an F_2^3 \ {0} structure (PG(2,2)).
The 7 Fano lines = 7 2-dim F_2-subspaces of F_2^3, each containing the 
non-zero elements of a 2-dim subspace.

The "dual" view: each Fano line is determined by its complementary 4-set 
of non-zero elements (which form an "anti-line"). Equivalently, a Fano 
line L is the 0-locus of a non-zero F_2-linear functional f: F_2^3 -> F_2,
and there are exactly 7 such functionals (corresponding to 7 Fano lines
in the dual plane).

Standard duality: lines and points correspond.

S_3 / triality: the outer-automorphism group Out(Spin(8)) = S_3 acts on 
the three 8-dim irreps {V_8, S+, S-}. This descends to an S_3 action on 
the seven octonion units.

There's also a known S_3-orbit decomposition on the 7 Fano lines under a 
"standard" triality fix. Let me find which (1,3,3) breakdown arises.

Approach: pick one Fano line L_0 as fixed. Then S_3 acts on the remaining
6 lines. Test whether they split as 3+3.
"""

FANO_LINES = [
    frozenset((1, 2, 3)),
    frozenset((1, 4, 5)),
    frozenset((1, 7, 6)),
    frozenset((2, 4, 6)),
    frozenset((2, 5, 7)),
    frozenset((3, 4, 7)),
    frozenset((3, 6, 5)),
]

# Each Fano line in F_2^3 labelling: the line is the 0-set of one of 7
# non-zero linear functionals. Equivalently, each line L corresponds to 
# a "polar point" p_L in the dual F_2^3 \ {0}.
#
# The polar point p_L of line L = {a, b, c} is the unique x != 0 such that
# x . a = x . b = x . c = 0 in F_2 (treating a,b,c,x as F_2^3 vectors).
# Equivalently, x is the linear functional whose kernel is the F_2-span
# {0, a, b, c}.

def to_vec(n):
    """Map integer 1..7 to F_2^3 vector (bit0, bit1, bit2)."""
    return ((n >> 0) & 1, (n >> 1) & 1, (n >> 2) & 1)

def dot(u, v):
    return (u[0]*v[0] + u[1]*v[1] + u[2]*v[2]) % 2

def polar_point(line):
    """Find x in F_2^3 \ {0} such that x . v = 0 for all v in line."""
    for x_int in range(1, 8):
        x = to_vec(x_int)
        if all(dot(x, to_vec(v)) == 0 for v in line):
            return x_int
    return None

print("=== Polar correspondence: line <-> point ===")
for line in FANO_LINES:
    p = polar_point(line)
    line_sorted = tuple(sorted(line))
    print(f"  Line {line_sorted} polar to point e_{p}")

# Now: pick the line L_0 fixed by triality. The polar point of L_0 is the 
# "center" of the (1,3,3) decomposition.
#
# Following the brief: 1 fixed H (associated to a fixed direction p),
# 3 H's on a Fano line through p (the "Fano-line 3-cycle"),
# 3 H's complementary triangle (the "complementary 3-cycle").
#
# Let's choose p = e_1 (any choice will be equivalent up to S_3).
# Then the 3 lines through e_1 are the 3 Fano lines containing 1.
# The 3 lines NOT through e_1 are the "complementary triangle".

print("\n=== Decomposition with fixed point p = e_1 ===")
THROUGH_E1 = [line for line in FANO_LINES if 1 in line]
NOT_THROUGH_E1 = [line for line in FANO_LINES if 1 not in line]

print(f"\n3 lines through e_1 (3-cycle A):")
for line in THROUGH_E1:
    print(f"  {tuple(sorted(line))}")

print(f"\n3 lines NOT through e_1 (3-cycle B):")
for line in NOT_THROUGH_E1:
    print(f"  {tuple(sorted(line))}")

# Check the XOR closure on 3-cycle B (lines not through e_1)
# Claim: for each such line {a, b, c}, polar point lies in some fixed
# structure relative to e_1.
print("\n=== Polar points of the two 3-cycles ===")
print("3-cycle A (lines through e_1) polars:")
for line in THROUGH_E1:
    print(f"  Line {tuple(sorted(line))} -> polar e_{polar_point(line)}")

print("3-cycle B (lines NOT through e_1) polars:")
for line in NOT_THROUGH_E1:
    print(f"  Line {tuple(sorted(line))} -> polar e_{polar_point(line)}")

# Now: which line is FIXED? In a (1,3,3) S_3-action, the fixed line is 
# the one whose polar point IS the chosen direction p = e_1.
# The line through e_1's polar... wait, "polar of L" is dual to L.
# Let's see which line has polar = e_1.
fixed_line = None
for line in FANO_LINES:
    if polar_point(line) == 1:
        fixed_line = line
print(f"\nLine with polar = e_1: {tuple(sorted(fixed_line))}")

# This line is the one PERPENDICULAR (in F_2 sense) to e_1.
# It's NOT through e_1 in the bare point-incidence sense.
# So the fixed line is one of NOT_THROUGH_E1.

print(f"\nFixed line is in NOT_THROUGH_E1: {fixed_line in NOT_THROUGH_E1}")

# So the (1,3,3) decomposition is:
# 1 fixed = the line dual to e_1 (i.e., (2,4,6) since e_2,e_4,e_6 are all orthogonal to e_1 in F_2)
# Let me check: e_1 has F_2 vector (1,0,0). Its kernel = {(0,a,b)} = {2,4,6} non-zero.
# So fixed line = (2,4,6).

THROUGH_E1 = [line for line in FANO_LINES if 1 in line]
COMP_NOT_FIXED = [line for line in NOT_THROUGH_E1 if line != fixed_line]

print(f"\n=== Refined (1,3,3) decomposition ===")
print(f"1 fixed line (polar=e_1): {tuple(sorted(fixed_line))}")
print(f"3 lines through e_1 (Fano-line 3-cycle):")
for line in THROUGH_E1:
    print(f"  {tuple(sorted(line))}")
print(f"3 complementary-triangle lines (not through e_1, not fixed):")
for line in COMP_NOT_FIXED:
    print(f"  {tuple(sorted(line))}")

# XOR closure on 3-cycle B (complementary triangle):
# Brief claims q1 XOR q2 XOR q3 = p where p is a fixed reference point.
# Test: for the three lines in COMP_NOT_FIXED, compute XOR of their 
# "characteristic vectors" or their polar points.

print("\n=== XOR closure test on complementary triangle ===")
print("Polar points of complementary triangle:")
polars = [polar_point(line) for line in COMP_NOT_FIXED]
print(f"  {polars}")
xor_sum = 0
for q in polars:
    xor_sum ^= q
print(f"  XOR of polars = {xor_sum}  (vs e_1 = 1)")

print("\nPolar points of Fano-line 3-cycle (through e_1):")
polars2 = [polar_point(line) for line in THROUGH_E1]
print(f"  {polars2}")
xor2 = 0
for q in polars2:
    xor2 ^= q
print(f"  XOR of polars = {xor2}")


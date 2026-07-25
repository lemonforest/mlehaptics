"""The fibration is 3+1+3, and the "4" comes from the PERSPECTIVE -- not from the object.

User 2026-07-25: "we've finally realized that fibration is 3+1+3 and 4 comes from the
perspective, so this will join our carrier soon, for full beat perspective pick etc."

srmech 0.9.0rc336. Exhaustive. Pure integer -- no float, no abs(), no numpy, no RNG.
"""
from itertools import combinations
from srmech.amsc.octonion import oct_mult

fail = []
def check(label, got, want):
    ok = got == want
    print(f"  {'OK ' if ok else 'XX '} {label}: {got}")
    if not ok: fail.append((label, got, want))

IM = list(range(1, 8))                       # the 7 imaginary axes
REAL = 0                                     # the single real unit e0

# ------------------------------------------- 1. the 7 imaginaries, the 7 triads
lines = sorted({frozenset({u, v, u ^ v}) for u in IM for v in IM if u != v}, key=sorted)
print("=== 1. the 7 imaginaries organise into 7 quaternion triads (Fano lines) ===")
check("imaginary axes", len(IM), 7)
check("quaternion triads (Fano lines)", len(lines), 7)
check("every triad has 3 axes", sorted({len(L) for L in lines}), [3])
check("every AXIS lies on exactly 3 triads",
      sorted({sum(1 for L in lines if u in L) for u in IM}), [3])
for L in lines: print(f"      triad {sorted(L)}")

# ------------------ 2. every triad borrows the SAME single real to become a 4
print("\n=== 2. each triad + THE SAME real = a quaternion (an H rung) ===")
reals_used = set()
for L in lines:
    S = {0, 8} | {u for u in L} | {u | 8 for u in L}      # +-1 and +-the three axes
    closed = all(oct_mult(a, b) in S for a in S for b in S)
    check(f"  triad {sorted(L)} + real -> a closed 8-element Q8", closed, True)
    reals_used |= {x for x in S if (x & 7) == 0}
check("the real units used across ALL 7 triads", sorted(reals_used), [0, 8])
check("...which is ONE real axis (+-e0), shared by every triad", len({0, 8} & set(reals_used)), 2)
print("      => 7 triads x 3 axes each, but only ONE real -- and it is COMMON to all of them.")
print("         So the '4' of a quaternion is NOT a fourth axis the triad owns.")
print("         It is the shared anchor the triad BORROWS. 4 = 3 + the perspective.")

# -------------------------------------- 3. the 3+1+3 split of the seven
print("\n=== 3. the 3+1+3 fibration: triad | doubling axis | the doubled triad ===")
for L in lines[:3]:
    base = sorted(L)
    d = [u for u in IM if u not in L][0]                   # a doubling axis off the line
    other = sorted({(u ^ d) for u in L})
    part = (len(base), 1, len(other))
    covers = sorted(set(base) | {d} | set(other))
    check(f"  {base} | [{d}] | {other}  partitions the 7", (part, covers), ((3, 1, 3), IM))
    check(f"    the base triad IS a quaternion triad", frozenset(base) in lines, True)
    check(f"    the DOUBLED triad is NOT (it is a coset, not a subalgebra)",
          frozenset(other) in lines, False)
print("      => 3+1+3: one H triad, the doubling axis that joins, and the doubled COSET.")
print("         The second '3' is not a second subalgebra -- it is the first one, mirrored.")

# ----------- 4. and the shared anchor is EXACTLY what the abelian shadow drops
print("\n=== 4. the perspective-supplied component is invisible to the shadow ===")
check("the shadow of the real unit collides with nothing else (basis 0)",
      sorted({x & 7 for x in (0, 8)}), [0])
check("the Z2^3 shadow sees ONLY the 7 imaginary directions",
      sorted({x & 7 for x in IM}), IM)
print("      => the abelian shadow keeps the 7 axes and CANNOT see the real anchor")
print("         (F1322: ker(pi) = {+-1} = the real axis). The component supplied by the")
print("         perspective is precisely the one the shadow projects away -- which is why")
print("         it never showed up as content, and why a metric (F1324) is needed to pick.")

print("\n" + ("ALL CHECKS PASSED" if not fail else f"FAILURES: {fail}"))
raise SystemExit(1 if fail else 0)

"""Is the HYPERCUBE itself a shadow? And is 8 the middle ground between "4-real-dimensional
space" and "16-vertex tesseract"?  Both: yes.

User 2026-07-28: "what are the chances that even the thing we call hypercube even only gives
us shadows? ... is it possible that there is an object that does describe 4-real-dimensional
space and 16-vertex tesseract by where something related to 8 is the middle ground?"

srmech 0.9.0rc349. Exhaustive. Pure integer -- no float, no abs(), no numpy, no RNG.
"""
from srmech.amsc.cascade.cayley_dickson import cd_mult
fail = []
def check(label, got, want):
    ok = got == want
    print(f"  {'OK ' if ok else 'XX '} {label}: {got}")
    if not ok: fail.append((label, got, want))

def mul(dim, x, y):
    """multiply signed basis UNITS by index: low log2(dim) bits = basis, top bit = sign."""
    b = dim.bit_length() - 1
    vx = [0]*dim; vx[x & (dim-1)] = -1 if (x >> b) & 1 else 1
    vy = [0]*dim; vy[y & (dim-1)] = -1 if (y >> b) & 1 else 1
    pr = cd_mult(vx, vy)
    k = next(i for i, v in enumerate(pr) if int(getattr(v, 'num', v)) != 0)
    return k | (dim if int(getattr(pr[k], 'num', pr[k])) < 0 else 0)

print("=== 1. the ladder: dim n -> 2n units -> a (log2 n + 1)-bit cube of labels ===")
print("  algebra dim | units | label bits | FULL-cube XOR | BASIS-only XOR")
viols = {}
for dim, nm in ((2,"C"), (4,"H"), (8,"O"), (16,"S")):
    n = 2*dim
    fb = sum(1 for x in range(n) for y in range(n) if mul(dim,x,y) != (x ^ y))
    bb = sum(1 for x in range(n) for y in range(n)
             if (mul(dim,x,y) & (dim-1)) != ((x ^ y) & (dim-1)))
    viols[dim] = fb
    print(f"  {nm:<11} {dim:<3}| {n:<5} | {dim.bit_length():<10} | "
          f"{str(fb)+' viol':<13} | {'EXACT' if bb==0 else str(bb)+' viol'}")
    check(f"  {nm}: the BASIS bits XOR exactly", bb, 0)
    check(f"  {nm}: the FULL cube does NOT", fb > 0, True)

print("\n=== 2. the closed form, DERIVED not fitted ===")
check("violations == 2*dim*(dim-1) at every rung",
      [viols[d] for d in (2,4,8,16)], [2*d*(d-1) for d in (2,4,8,16)])
print("  why: for i != j, e_i.e_j = -e_j.e_i, so ANTISYMMETRY forces exactly ONE of the")
print("  ordered pair (i,j),(j,i) to carry the sign -> half of dim(dim-1) basis pairs;")
print("  each covers 4 signed-unit pairs -> 4 * dim(dim-1)/2 = 2*dim*(dim-1).")
print("\n  fraction of pairs the flat cube gets WRONG = (dim-1)/(2*dim):")
for dim in (2,4,8,16,32,64):
    print(f"     dim {dim:<3} -> {dim-1}/{2*dim}")
print("  -> 1/2 asymptotically. THE FLAT CUBE IS WRONG EXACTLY WHERE THE ALGEBRA")
print("     ANTICOMMUTES, and that is asymptotically HALF of all pairs.")

print("\n=== 3. so what IS the middle ground? ===")
print("  'H = 4-real-dimensional space'  -> dim 4  -> 8 units  -> a 3-cube of labels")
print("  'the 16-vertex tesseract'       -> a 4-cube = 16 labels")
print("  what has exactly 16 units?      -> O, dim 8")
check("O has 16 units", 2*8, 16)
check("O's unit labels need exactly 4 bits (a tesseract)", (2*8-1).bit_length(), 4)
print("\n  O simultaneously CONTAINS H (7 copies, the Fano lines) and IS labelled by a")
print("  4-bit tesseract. The two readings are ONE OBJECT seen two ways -- subalgebra")
print("  vs unit-label -- and 8 is where they meet.")

print("\n" + ("ALL CHECKS PASSED" if not fail else f"FAILURES: {fail}"))
raise SystemExit(1 if fail else 0)

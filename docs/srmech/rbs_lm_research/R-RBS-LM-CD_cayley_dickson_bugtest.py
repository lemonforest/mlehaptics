r"""Acceptance/bug test for srmech 0.7.3rc1 cascade.cayley_dickson — full Cayley-Dickson
algebra (exact, Fraction). Tests it against the Hurwitz boundary the framework predicts
(F424 sedenion zero divisors; F442/F449 the algebra breaks at 𝕊; F451 the reversibility
horizon = left_mult_is_invertible ≤𝕆 only). Natively replaces the hand-rolled CD mul/cj
in F442/F449."""
from fractions import Fraction as Fr
import numpy as np
from srmech.amsc.cascade import cayley_dickson as cd

PASS = []; BUGS = []
def ck(name, ok, detail=""):
    PASS.append(ok); print(f"  [{'PASS' if ok else 'FAIL'}] {name}  {detail}")
    if not ok: BUGS.append(name)

def rnd(dim, rng):
    return [Fr(int(v)) for v in rng.integers(-3, 4, size=dim)]

import srmech
print(f"srmech {srmech.__version__} — Cayley-Dickson bug-test\n")

# ---- A. multiply correctness up the ladder ----
print("[A] cd_mult correctness")
i = cd.cd_basis(2, 1)
ck("ℂ: i·i = -1", cd.cd_mult(i, i) == (Fr(-1), Fr(0)), f"-> {tuple(map(str,cd.cd_mult(i,i)))}")
e1, e2 = cd.cd_basis(4, 1), cd.cd_basis(4, 2)
ij, ji = cd.cd_mult(e1, e2), cd.cd_mult(e2, e1)
ck("ℍ: e1·e2 = -(e2·e1) (non-commutative)", ij == tuple(-c for c in ji) and any(ij), f"ij={tuple(map(str,ij))}")
a, b, c2 = cd.cd_basis(8, 1), cd.cd_basis(8, 2), cd.cd_basis(8, 4)
left = cd.cd_mult(cd.cd_mult(a, b), c2); right = cd.cd_mult(a, cd.cd_mult(b, c2))
ck("𝕆: (e1·e2)·e4 ≠ e1·(e2·e4) (non-associative)", left != right)
ck("𝕊: dim-16 multiply runs", len(cd.cd_mult(cd.cd_basis(16, 1), cd.cd_basis(16, 10))) == 16)

# ---- B. conjugate/norm: x·x̄ = N(x)·1 at EVERY rung (incl sedenion) ----
print("\n[B] x·x̄ = N(x)·1 (real, imaginaries 0) at every rung")
rng = np.random.default_rng(3)
for dim in (2, 4, 8, 16):
    x = rnd(dim, rng)
    p = cd.cd_mult(x, cd.cd_conjugate(x)); n = cd.cd_norm_sq(x)
    ok = p[0] == n and all(c == 0 for c in p[1:])
    ck(f"dim {dim}: x·x̄ = N(x)·1", ok, f"N={n}")

# ---- C. composition N(xy)=N(x)N(y): holds ≤𝕆, BREAKS at 𝕊 ----
print("\n[C] composition norm N(xy)=N(x)N(y): holds dims 2/4/8, breaks at 16")
for dim in (2, 4, 8):
    x, y = rnd(dim, rng), rnd(dim, rng)
    ok = cd.cd_norm_sq(cd.cd_mult(x, y)) == cd.cd_norm_sq(x) * cd.cd_norm_sq(y)
    ck(f"dim {dim}: composition holds", ok)
w = cd.sedenion_zero_divisor_witness()
nx, ny = w["x_norm_sq"], w["y_norm_sq"]; nxy = cd.cd_norm_sq(cd.cd_mult(w["x"], w["y"]))
ck("dim 16: composition BREAKS (witness: N(x)N(y)=%s·%s but N(xy)=%s)" % (nx, ny, nxy),
   nxy == 0 and nx * ny != 0, "the zero divisor = extreme composition failure")

# ---- D. the sedenion zero-divisor witness (native F424), verified EXACTLY ----
print("\n[D] sedenion zero-divisor witness — verified with cd_mult (exact)")
prod = cd.cd_mult(w["x"], w["y"])
ck("witness x·y = 0 (recomputed, exact Fraction zeros)", all(c == 0 for c in prod) and all(isinstance(c, Fr) for c in prod),
   f"{w['x_form']} · {w['y_form']}")
ck("witness x, y both NONZERO (norm² = 2, 2)", nx != 0 and ny != 0)
ck("dim == 16 (zero divisors first appear at the sedenion)", w["dim"] == 16)

# ---- E. reversibility horizon (F451): left_mult invertible ≤𝕆, NOT at 𝕊 ----
print("\n[E] reversibility horizon — left_mult_is_invertible (F451 made executable)")
ck("is_division_algebra_dim: True for 1/2/4/8", all(cd.is_division_algebra_dim(d) for d in (1, 2, 4, 8)))
ck("is_division_algebra_dim: False for 16/32", not cd.is_division_algebra_dim(16) and not cd.is_division_algebra_dim(32))
oct_x = rnd(8, rng)
while cd.cd_norm_sq(oct_x) == 0:
    oct_x = rnd(8, rng)
ck("𝕆: a nonzero octonion's left-mult IS invertible (no zero divisor ≤𝕆)", cd.left_mult_is_invertible(oct_x))
ck("𝕊: the witness x's left-mult is NOT invertible (has a kernel)", not cd.left_mult_is_invertible(w["x"]))
ker = cd.left_mult_kernel(w["x"])
ck("𝕊: witness x has a nonempty left-mult kernel (y lives there)", len(ker) > 0, f"kernel dim {len(ker)}")

print(f"\n=== {sum(PASS)}/{len(PASS)} PASS ===")
print("BUGS:", BUGS if BUGS else "NONE")

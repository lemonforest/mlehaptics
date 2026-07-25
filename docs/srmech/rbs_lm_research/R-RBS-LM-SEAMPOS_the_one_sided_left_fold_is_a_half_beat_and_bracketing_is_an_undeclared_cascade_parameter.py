"""Is the cascade's seam at the END, and does that make it half-beat shaped?
Does composition stopping at O mean a correct rotation needs TWO quaternion traversals?
What changes if the rotation happens in the MIDDLE of the cascade instead?

User 2026-07-25: "maybe it has to do with our cascades having the seam at the end, makes
them half beat shaped? ... it takes two full quaternion groups for a correct rotation?
what happens if we change our pattern search parameters to rotation happens in the middle
of cascade ... something to do with the metric field excitations themselves"

The SHIPPED fold (genome_fiber_holonomy / genome_octonion_holonomy) is strictly
LEFT-ASSOCIATED and ONE-SIDED:  acc = ((((1.t0).t1).t2)...)  -- seam at the end.

srmech 0.9.0rc336. Pure integer. No float, no abs(), no numpy, no RNG.
"""
from itertools import permutations
from srmech.amsc.q8 import q8_mult
from srmech.amsc.octonion import oct_mult

fail = []
def check(label, got, want):
    ok = got == want
    print(f"  {'OK ' if ok else 'XX '} {label}: {got}")
    if not ok: fail.append((label, got, want))

def conj_q(a): return a if (a & 3) == 0 else a ^ 4
def conj_o(a): return a if (a & 7) == 0 else a ^ 8
Q8, O16 = list(range(8)), list(range(16))
check("conjugate is the inverse at H", all(q8_mult(a, conj_q(a)) == 0 for a in Q8), True)
check("conjugate is the inverse at O", all(oct_mult(a, conj_o(a)) == 0 for a in O16), True)

def ordr(f, dom):
    m = {x: x for x in dom}; n = 0
    while True:
        m = {x: f(m[x]) for x in dom}; n += 1
        if all(m[x] == x for x in dom): return n

# ================================================== 1. IS IT A HALF BEAT?
print("\n=== 1. ONE-SIDED (seam at the end) vs SANDWICH (seam in the middle) ===")
print("    q      one-sided L_q: x->q.x    sandwich C_q: x->q.x.qbar    ratio")
ratios = []
for q in (1, 2, 3):
    lo = ordr(lambda x, q=q: q8_mult(q, x), Q8)
    co = ordr(lambda x, q=q: q8_mult(q8_mult(q, x), conj_q(q)), Q8)
    ratios.append(lo // co)
    print(f"    H  e{q}        order {lo}                    order {co}                {lo}/{co}")
check("H: the sandwich closes in HALF the steps of the one-sided fold", ratios, [2, 2, 2])
ro = []
for q in (1, 2, 4, 7):
    lo = ordr(lambda x, q=q: oct_mult(q, x), O16)
    co = ordr(lambda x, q=q: oct_mult(oct_mult(q, x), conj_o(q)), O16)
    ro.append((q, lo, co))
    print(f"    O  e{q}        order {lo}                    order {co}                {lo}//{co}")
check("O: same 4-vs-2 double cover", [(l, c) for _, l, c in ro], [(4, 2)] * 4)
print("    => CONFIRMED. A one-sided fold is a HALF BEAT: it takes 2 turns to do what the")
print("       sandwich does in 1. This IS the spinor double cover -- q=exp(u.theta/2)")
print("       carries the HALF-angle, so a one-sided seam reads a spinor, not a rotation.")

# ========================================= 2. TWO QUATERNION GROUPS?
print("\n=== 2. does a correct rotation need TWO quaternion traversals? ===")
H0 = [x for x in O16 if (x & 7) < 4]                    # the base H copy inside O
Hl = [x for x in O16 if (x & 7) >= 4]                   # the doubled copy  H.l
check("O splits as H (+) H.l  -- literally TWO quaternion groups", (len(H0), len(Hl)), (8, 8))
check("the base copy is CLOSED (a group)", all(oct_mult(a, b) in H0 for a in H0 for b in H0), True)
check("the doubled copy is NOT closed (it is a coset, not a group)",
      all(oct_mult(a, b) in Hl for a in Hl for b in Hl), False)
lines = sorted({frozenset({u, v, u ^ v}) for u in range(1, 8) for v in range(1, 8) if u != v})
check("H subalgebras inside O = 2-dim shadow subspaces = FANO LINES", len(lines), 7)
ass = lambda u, v, w: oct_mult(oct_mult(u, v), w) != oct_mult(u, oct_mult(v, w))
inH = [(u, v, w) for L in lines for u in ({0} | set(L)) for v in ({0} | set(L)) for w in ({0} | set(L))]
check("associator INSIDE any single H copy", sum(1 for t in inH if ass(*t)), 0)
check("associator over all triples", sum(1 for u in range(8) for v in range(8)
                                         for w in range(8) if ass(u, v, w)), 168)
print("    => the guess is RIGHT in shape but the count is 7, not 2: O is built by doubling")
print("       ONE H (so '2 copies' is the CD presentation), but it CONTAINS 7 H subalgebras")
print("       -- the 7 Fano lines, the 7 of the 1:3:7. Composition survives inside any ONE")
print("       of them and dies the moment a triple needs two. That IS why it stops at O.")

# ================================ 3. BRACKETING IS AN UNDECLARED PARAMETER
print("\n=== 3. seam position = BRACKETING. Is it content? ===")
def b_left(w):   # ((ab)c)d   -- WHAT WE SHIP
    z = w[0]
    for x in w[1:]: z = oct_mult(z, x)
    return z
def b_right(w):  # a(b(cd))
    z = w[-1]
    for x in reversed(w[:-1]): z = oct_mult(x, z)
    return z
def b_mid(w):    # (ab)(cd)   -- the SEAM IN THE MIDDLE
    h = len(w) // 2
    return oct_mult(b_left(w[:h]), b_left(w[h:]))
def b_l2(w): return oct_mult(oct_mult(w[0], oct_mult(w[1], w[2])), w[3])
def b_r2(w): return oct_mult(w[0], oct_mult(oct_mult(w[1], w[2]), w[3]))
SHAPES = [("left  ((ab)c)d", b_left), ("right a(b(cd))", b_right), ("MID   (ab)(cd)", b_mid),
          ("mixed (a(bc))d", b_l2), ("mixed a((bc)d)", b_r2)]
words = [(a, b, c, d) for a in range(8) for b in range(8) for c in range(8) for d in range(8)]
diff = sum(1 for w in words if len({f(w) for _, f in SHAPES}) > 1)
check("length-4 words where the 5 bracketings DISAGREE", diff > 0, True)
print(f"    {diff} / {len(words)} = {100*diff//len(words)}% of length-4 words give a DIFFERENT")
print("    answer depending on where you put the seam.")
check("all 5 bracketings agree on the SHADOW (basis) always",
      all(len({f(w) & 7 for _, f in SHAPES}) == 1 for w in words), True)
check("H peer: bracketing is IRRELEVANT (associative)",
      sum(1 for a in Q8 for b in Q8 for c in Q8 for d in Q8
          if q8_mult(q8_mult(q8_mult(a, b), c), d) != q8_mult(a, q8_mult(b, q8_mult(c, d)))), 0)
print("    => at H the seam position is free. At O it is CONTENT -- and we ship exactly ONE")
print("       bracketing, undeclared. That is a magic number in the SHAPE, not in a value.")

# ============================ 4. what the MIDDLE seam reads that the END seam cannot
print("\n=== 4. does moving the seam BUY discrimination? (the actionable part) ===")
def classes(keyfns, perms):
    return len({tuple(f(p) for f in keyfns) for p in perms})
from itertools import combinations
tot = gain = 0; hist = {}
for base in combinations(range(1, 8), 4):
    perms = list(permutations(base))
    l = classes([b_left], perms); lm = classes([b_left, b_mid], perms)
    a5 = classes([f for _, f in SHAPES], perms)
    tot += 1; gain += (lm > l); hist[(l, lm, a5)] = hist.get((l, lm, a5), 0) + 1
    if base in ((1, 2, 4, 7), (1, 2, 3, 5)):
        print(f"    word {base}: left={l}  left+MID={lm}  all5={a5}   (of {len(perms)} orderings)")
print(f"    over ALL {tot} 4-subsets of the 7 imaginary axes:")
for k in sorted(hist): print(f"      left={k[0]} left+MID={k[1]} all5={k[2]}  -> {hist[k]} words")
check("left+MID never separates LESS than left alone",
      all(classes([b_left, b_mid], list(permutations(b))) >= classes([b_left], list(permutations(b)))
          for b in combinations(range(1, 8), 4)), True)
check(f"words where the MIDDLE seam separates MORE ({gain}/{tot})", gain, 28)
check("the closed words (XOR of all four == 0) are exactly the ones with NO gain",
      sorted(b for b in combinations(range(1, 8), 4)
             if classes([b_left, b_mid], list(permutations(b))) ==
                classes([b_left], list(permutations(b)))),
      sorted(b for b in combinations(range(1, 8), 4)
             if b[0] ^ b[1] ^ b[2] ^ b[3] == 0))
print("    => the middle seam is not a re-phrasing of the end seam: it separates orderings")
print("       the left fold CONFUSES. Reading k bracketings is a k-bit order read per slot,")
print("       where we currently take 1.")

# ================================================= 5. is any of it gauge?
print("\n=== 5. gauge check -- is the seam read STRUCTURE or convention? ===")
def regauge(m, f, w): return f(tuple(u | (8 if (m >> u) & 1 else 0) for u in w))
base = (1, 2, 4, 7); perms = list(permutations(base))
part = lambda f, m: frozenset(frozenset(i for i, p in enumerate(perms)
                                        if regauge(m, f, p) == v)
                              for v in {regauge(m, f, p) for p in perms})
for nm, f in (("left fold", b_left), ("MID fold", b_mid)):
    p0 = part(f, 0)
    check(f"{nm}: the ORDER partition is gauge-invariant (all 256 gauges)",
          all(part(f, m) == p0 for m in range(256)), True)
check("but the ABSOLUTE value is NOT gauge-invariant",
      len({regauge(m, b_left, base) for m in range(256)}) > 1, True)
print("    => same-multiset comparisons (which orderings differ, which bracketings differ)")
print("       are REAL STRUCTURE; the absolute fold value is convention. So a seam-position")
print("       sweep is a legitimate read, not a re-labelling.")

print("\n" + ("ALL CHECKS PASSED" if not fail else f"FAILURES: {fail}"))
raise SystemExit(1 if fail else 0)

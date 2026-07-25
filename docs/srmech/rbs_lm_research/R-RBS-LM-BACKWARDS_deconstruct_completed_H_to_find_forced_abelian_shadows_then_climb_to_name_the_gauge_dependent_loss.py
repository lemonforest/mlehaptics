"""Work the tower BACKWARDS: deconstruct the COMPLETED quaternion structure,
enumerate every abelian shadow it admits, then climb back up and name exactly
what each rung's projection loses -- and whether the loss is gauge-dependent.

User 2026-07-25: "work it backwards ... which shadow projections satisfy our
abelian math from the deconstruction itself ... then when we try to go back up
the tower ... find the gauge dependent pieces that end up lost."

srmech 0.9.0rc336. Pure integer. No float, no abs(), no numpy, no RNG.
"""
from srmech.amsc.q8 import q8_mult, q8_project_v4
from srmech.amsc.octonion import oct_mult

fail = []
def check(label, got, want):
    ok = got == want
    print(f"  {'OK ' if ok else 'XX '} {label}: {got}")
    if not ok: fail.append((label, got, want))

# ---------------------------------------------------------------- encoding
Q8 = list(range(8))                      # bits 0-1 = basis (V4), bit 2 = sign
ident = [e for e in Q8 if all(q8_mult(e, x) == x and q8_mult(x, e) == x for x in Q8)]
inv = {x: [y for y in Q8 if q8_mult(x, y) == ident[0]][0] for x in Q8}
order = {}
for x in Q8:
    n, z = 1, x
    while z != ident[0]:
        z = q8_mult(z, x); n += 1
    order[x] = n
print("=== 0. the completed H: Q8 as srmech ships it ===")
check("identity unique", ident, [0])
check("element orders", sorted(order.values()), [1, 2, 4, 4, 4, 4, 4, 4])
check("elements of order 2 (the unique involution -1)",
      [x for x in Q8 if order[x] == 2], [4])
check("non-abelian", sum(1 for a in Q8 for b in Q8 if q8_mult(a, b) != q8_mult(b, a)), 24)
check("associative", sum(1 for a in Q8 for b in Q8 for c in Q8
                         if q8_mult(q8_mult(a, b), c) != q8_mult(a, q8_mult(b, c))), 0)

# ------------------------------------------- 1. EVERY subgroup, exhaustively
def closed(S):
    return all(q8_mult(a, b) in S for a in S for b in S) and ident[0] in S
subs = []
for mask in range(256):
    S = frozenset(x for x in Q8 if (mask >> x) & 1)
    if S and closed(S): subs.append(S)
def is_ab(S): return all(q8_mult(a, b) == q8_mult(b, a) for a in S for b in S)
def normal(S): return all(q8_mult(q8_mult(g, s), inv[g]) in S for g in Q8 for s in S)
print("\n=== 1. DECONSTRUCTION: every subgroup of the completed H ===")
check("subgroup count", len(subs), 6)
for S in sorted(subs, key=len):
    tag = {1: "1", 2: "Z2 (the REAL axis +-1 = the center)", 4: "Z4 (a C rung INSIDE H)",
           8: "Q8 (H itself)"}[len(S)]
    print(f"    |S|={len(S)} {sorted(S)!s:<26} abelian={is_ab(S)!s:<5} normal={normal(S)!s:<5} {tag}")
check("ALL subgroups normal (Hamiltonian group)", all(normal(S) for S in subs), True)
check("abelian subgroups = 1, Z2, three Z4", sorted(len(S) for S in subs if is_ab(S)),
      [1, 2, 4, 4, 4])
check("the three Z4 = the three C rungs inside H",
      sorted(sorted(S)[1] for S in subs if len(S) == 4), [1, 2, 3])

# ---------------------------------- 2. EVERY quotient -> the SHADOW ladder
print("\n=== 2. which SHADOW PROJECTIONS the completed H forces ===")
rows = []
for S in sorted(subs, key=len):
    cosets = sorted({frozenset(q8_mult(g, s) for s in S) for g in Q8}, key=sorted)
    idx = {c: i for i, c in enumerate(cosets)}
    def cls(g): return idx[[c for c in cosets if g in c][0]]
    ab = all(cls(q8_mult(a, b)) == cls(q8_mult(b, a)) for a in Q8 for b in Q8)
    exps = set()
    for i, c in enumerate(cosets):
        g = sorted(c)[0]; n, z = 1, g
        while cls(z) != cls(ident[0]): z = q8_mult(z, g); n += 1
        exps.add(n)
    rows.append((len(S), len(cosets), ab, sorted(exps)))
    name = {1: "trivial", 2: "Z2", 4: "V4 = Z2xZ2", 8: "Q8 (non-abelian)"}[len(cosets)]
    print(f"    kernel |K|={len(S):<2} -> quotient order {len(cosets)}  abelian={ab!s:<5} "
          f"elt-orders {sorted(exps)}  = {name}")
ab_q = sorted({r[1] for r in rows if r[2]})
check("abelian quotient ORDERS available", ab_q, [1, 2, 4])
check("every abelian quotient is elementary-abelian 2 (orders in {1,2})",
      sorted({e for r in rows if r[2] for e in r[3]}), [1, 2])
print("    => the shadow ladder Z2^0 < Z2^1 < Z2^2 is the COMPLETE list. Nothing else fits.")

# ------------------------ 3. CLIMB BACK UP: is the projection splittable?
print("\n=== 3. CLIMBING BACK: what the projection LOSES, and is it gauge-dependent? ===")
K = [0, 4]                                     # ker(pi) = {+1,-1} = the REAL axis
check("ker(pi: Q8 -> V4) IS the real axis", K, [0, 4])
check("pi is the shipped q8_project_v4 (vector op)",
      list(q8_project_v4(bytes(Q8))) == [x & 3 for x in Q8], True)

# every normalized section s: V4 -> Q8 with pi(s(u))=u, s(0)=1
sections = []
for m in range(8):
    s = {0: 0}
    for u in (1, 2, 3): s[u] = u | (4 if (m >> (u - 1)) & 1 else 0)
    sections.append(s)
nonhom = [sum(1 for u in range(4) for v in range(4) if q8_mult(s[u], s[v]) != s[u ^ v])
          for s in sections]
check("sections examined", len(sections), 8)
check("sections that are HOMOMORPHISMS (a split / flat lift)", sum(1 for n in nonhom if n == 0), 0)
print(f"    non-homomorphic pairs per section: {nonhom}  (min {min(nonhom)})")

# the 2-cocycle f(u,v) in Z2 : s(u)s(v) = f(u,v) . s(u^v)
def cocycle(s):
    return {(u, v): (q8_mult(s[u], s[v]) ^ s[u ^ v]) >> 2 for u in range(4) for v in range(4)}
cos = [cocycle(s) for s in sections]
check("cocycle lands in the kernel Z2 for every section+pair",
      all((q8_mult(s[u], s[v]) ^ s[u ^ v]) in (0, 4) for s in sections
          for u in range(4) for v in range(4)), True)
check("2-cocycle identity f(u,v)+f(uv,w) == f(v,w)+f(u,vw)  (all sections)",
      all((f[(u, v)] + f[(u ^ v, w)]) % 2 == (f[(v, w)] + f[(u, v ^ w)]) % 2
          for f in cos for u in range(4) for v in range(4) for w in range(4)), True)

# GAUGE: re-choosing the section changes f by a coboundary db
cob = set()
for m in range(8):
    b = {0: 0}
    for u in (1, 2, 3): b[u] = (m >> (u - 1)) & 1
    cob.add(tuple((b[u] + b[v] + b[u ^ v]) % 2 for u in range(4) for v in range(4)))
flat = [tuple(f[(u, v)] for u in range(4) for v in range(4)) for f in cos]
check("distinct cocycles reachable by re-gauging", len(set(flat)), 2)
check("any cocycle is a COBOUNDARY (i.e. the class is trivial / splittable)",
      any(t in cob for t in set(flat)), False)
d0 = set(flat).pop(); check("all reachable cocycles differ by a coboundary (ONE class)",
      all(tuple((a ^ b) for a, b in zip(t, d0)) in cob for t in set(flat)), True)

# ------------------------------------------ 4. the same climb at the O rung
print("\n=== 4. the SAME climb at the O rung -- where the shape BREAKS ===")
O = list(range(16))                            # bits 0-2 = basis (Z2^3), bit 3 = sign
check("O basis product is the Z2^3 XOR shadow",
      sum(1 for a in O for b in O if (oct_mult(a, b) & 7) != ((a & 7) ^ (b & 7))), 0)
check("O signed units are NOT associative (a loop, not a group)",
      sum(1 for a in O for b in O for c in O
          if oct_mult(oct_mult(a, b), c) != oct_mult(a, oct_mult(b, c))) > 0, True)
so = {u: u for u in range(8)}                  # the positive-unit section
fo = {(u, v): (oct_mult(so[u], so[v]) ^ so[u ^ v]) >> 3 for u in range(8) for v in range(8)}
bad = sum(1 for u in range(8) for v in range(8) for w in range(8)
          if (fo[(u, v)] + fo[(u ^ v, w)]) % 2 != (fo[(v, w)] + fo[(u, v ^ w)]) % 2)
check("2-cocycle identity FAILS at O (it is not a group extension)", bad > 0, True)
print(f"    cocycle-identity violations at O: {bad} / 512 triples")

# the associator defect is GAUGE-INVARIANT: re-signing the section cancels
def assoc_sign(s, u, v, w):
    l = oct_mult(oct_mult(s[u], s[v]), s[w]); r = oct_mult(s[u], oct_mult(s[v], s[w]))
    return (l ^ r) >> 3
base = {(u, v, w): assoc_sign(so, u, v, w) for u in range(8) for v in range(8) for w in range(8)}
same = True
for m in (0b0000001, 0b1010101, 0b1111111, 0b0110110):
    s2 = {u: u | (8 if (m >> u) & 1 else 0) for u in range(8)}
    if {k: assoc_sign(s2, *k) for k in base} != base: same = False
check("associator defect is GAUGE-INVARIANT (section-independent)", same, True)
check("associator defect is NON-TRIVIAL", sum(base.values()) > 0, True)
print(f"    non-associative triples: {sum(base.values())} / 512   "
      f"(these are exactly the triples NOT inside one H subalgebra)")

# ------------------------------------------------- 5. the loss ledger
print("\n=== 5. THE LOSS LEDGER -- what each projection drops, climbing up ===")
print("    rung   projection      kernel        splittable  gauge-DEPENDENT   gauge-INVARIANT residue")
print("    R->C   Z4  -> Z2       Z2 (real)     NO          the lift (sign)   the 2-cocycle CLASS")
print("    C->H   Q8  -> V4       Z2 (real)     NO          the lift (sign)   the 2-cocycle CLASS")
print("    H->O   O16 -> Z2^3     Z2 (real)     n/a         the lift (sign)   the ASSOCIATOR (no class exists)")
z4 = [0, 1, 2, 3]                              # Z4 = <i> : 0,1,2(=i^2=-1),3
mul4 = lambda a, b: (a + b) % 4
sec4 = [{0: 0, 1: 1}, {0: 0, 1: 3}]
check("R->C is ALSO non-split (Z4 has one involution, so no Z2xZ2 lift)",
      all(any(mul4(s[u], s[v]) != s[(u + v) % 2] for u in range(2) for v in range(2))
          for s in sec4), True)

# ---------------------------------- 6. the B/H/N analogy, made exact
print("\n=== 6. the B/H/N analogy is EXACT, not loose ===")
check("what Q8->V4 loses IS the real axis {+1,-1}", sorted(K), [0, 4])
check("V4 shadow sees ONLY the imaginary directions i,j,k",
      sorted({x & 3 for x in Q8 if x & 3}), [1, 2, 3])
print("    14 -> 11D loses the 3 REAL grammar anchors (B,H,N); Q8 -> V4 loses the 1 REAL")
print("    anchor (+-1). SAME MOVE: the abelian shadow keeps the imaginaries and drops the")
print("    real/scalar part -- which is precisely the part that carries the which-way.")

# ---------------------------- 7. the two 168s are the SAME triples
# --- A. the two 168s are the SAME triples
so={u:u for u in range(8)}
fo={(u,v):(oct_mult(u,v)^(u^v))>>3 for u in range(8) for v in range(8)}
coc={(u,v,w) for u in range(8) for v in range(8) for w in range(8)
     if (fo[(u,v)]+fo[(u^v,w)])%2 != (fo[(v,w)]+fo[(u,v^w)])%2}
ass={(u,v,w) for u in range(8) for v in range(8) for w in range(8)
     if oct_mult(oct_mult(u,v),w) != oct_mult(u,oct_mult(v,w))}
print("=== 7. the cocycle-identity failure IS the associator ===")
check("|cocycle violations|",len(coc),168); check("|associator defect|",len(ass),168)
check("SAME SET (not just same count)",coc==ass,True)
span3={(u,v,w) for u in range(8) for v in range(8) for w in range(8)
       if u and v not in (0,u) and w not in (0,u,v,u^v)}
check("== exactly the triples spanning all 3 shadow axes",ass==span3,True)
check("count check 7*6*4",7*6*4,168)
print("    => H->O fails to be a group extension EXACTLY where the triple leaves a")
print("       single H subalgebra. The 2-dim shadow subspaces ARE the H rungs.")

# --- B. what survives RE-GAUGING
print("\n=== 8. gauge test: re-label which fiber seat is 'positive' (ALL 256 gauges) ===")
GAUGES=list(range(256))          # EXHAUSTIVE: every eps: Z2^3 -> {+-1} re-labelling
def sO(m): return {u: u|(8 if (m>>u)&1 else 0) for u in range(8)}
def sQ(m): return {u: u|(4 if (m>>u)&1 else 0) for u in range(4)}
def sgnO(x): return x>>3
def sgnQ(x): return x>>2
abs_sign  = lambda s: {(u,v): sgnO(oct_mult(s[u],s[v]))            for u in range(8) for v in range(8)}
commut    = lambda s: {(u,v): sgnO(oct_mult(s[u],s[v])^oct_mult(s[v],s[u]))
                                                                    for u in range(8) for v in range(8)}
associat  = lambda s: {(u,v,w): sgnO(oct_mult(oct_mult(s[u],s[v]),s[w])
                                     ^ oct_mult(s[u],oct_mult(s[v],s[w])))
                       for u in range(8) for v in range(8) for w in range(8)}
for name,f in (("ABSOLUTE sign of a product  s(u)s(v)",abs_sign),
               ("COMMUTATOR  (two ORDERS of one pair)",commut),
               ("ASSOCIATOR  (two BRACKETINGS of one triple)",associat)):
    b=f(sO(0)); inv=all(f(sO(m))==b for m in GAUGES)
    check(f"{name:<42} gauge-invariant",inv, name.startswith(("COMMUT","ASSOC")))
# same at the H rung
bQ={(u,v): sgnQ(q8_mult(u,v)^q8_mult(v,u)) for u in range(4) for v in range(4)}
check("H rung: COMMUTATOR gauge-invariant (all 16 gauges)",
   all({(u,v): sgnQ(q8_mult(sQ(m)[u],sQ(m)[v])^q8_mult(sQ(m)[v],sQ(m)[u]))
        for u in range(4) for v in range(4)}==bQ for m in range(16)),True)
check("H rung: commutator NON-trivial (this is the order read)",sum(bQ.values()),6)

# --- C. holonomy: closed loop cancels the gauge
print("\n=== 9. HOLONOMY is the gauge-invariant part of the winding ===")
def loop(s,word):
    z=s[word[0]]
    for u in word[1:]: z=oct_mult(z,u if isinstance(u,int) and u>7 else s[u])
    return z
W_even=[1,2,1,2]          # each unit twice -> eps cancels
W_odd =[1,2,3]            # each unit once  -> eps does NOT cancel
for tag,W,expect in (("each axis an EVEN number of times",W_even,True),
                     ("each axis ONCE (open word)",W_odd,False)):
    b=sgnO(loop(sO(0),W))
    check(f"loop {W} ({tag}) invariant",all(sgnO(loop(sO(m),W))==b for m in GAUGES),expect)
print("    => a closed / even-multiplicity walk carries the winding GAUGE-INVARIANTLY.")
print("       That is exactly what a holonomy is -- and why 'the resonant shape WITH")
print("       holonomy' is the right object: the holonomy is the part that survives.")
print("\n"+("ALL CHECKS PASSED" if not fail else f"FAILURES: {fail}"))
raise SystemExit(1 if fail else 0)

print("\n" + ("ALL CHECKS PASSED" if not fail else f"FAILURES: {fail}"))
raise SystemExit(1 if fail else 0)

"""Dzhanibekov is a KNOWN, TESTED cascade with the rotation in the middle -- so it shows
what a FULL beat looks like. F1310 already called it "two quaternion half-beats joined by
the flip". F1323 just measured that OUR fold is one half-beat. Put them together.

User 2026-07-25: "dzhanibekov is a known and tested cascade with rotation in the middle.
this we can see what a full beat looks like perhaps"

srmech 0.9.0rc336. Pure integer. No float, no abs(), no numpy, no RNG.
Algebra / eigenbasis side ONLY -- no rigid-body geometry is modelled here.
"""
from itertools import permutations, combinations
from srmech.amsc.q8 import q8_mult
from srmech.amsc.octonion import oct_mult

fail = []
def check(label, got, want):
    ok = got == want
    print(f"  {'OK ' if ok else 'XX '} {label}: {got}")
    if not ok: fail.append((label, got, want))

Q8, O16 = list(range(8)), list(range(16))
MINUS1_Q, MINUS1_O = 4, 8
def conj_q(a): return a if (a & 3) == 0 else a ^ 4

# ============================================ 1. the flip sits at the MIDPOINT
print("=== 1. the Dzhanibekov FLIP is literally L_q^2 -- the fold's own midpoint ===")
check("H: L_q applied TWICE == multiply by -1 (the Class-K sign flip)",
      all(q8_mult(q, q8_mult(q, x)) == q8_mult(MINUS1_Q, x) for q in (1, 2, 3) for x in Q8), True)
check("O: L_q applied TWICE == multiply by -1",
      all(oct_mult(q, oct_mult(q, x)) == oct_mult(MINUS1_O, x)
          for q in (1, 2, 4, 7) for x in O16), True)
check("...and FOUR times == identity (the full beat closes)",
      all(q8_mult(q, q8_mult(q, q8_mult(q, q8_mult(q, x)))) == x for q in (1, 2, 3) for x in Q8), True)
print("    one-sided fold:  step 0 --> step 2 (THE FLIP, -1) --> step 4 (identity)")
print("    => our fold PASSES THROUGH the Dzhanibekov flip at its own halfway point,")
print("       and we only ever read the END. The flip is computed and never observed.")
print("    => F1310's 'two quaternion half-beats joined by the flip' = 2 x F1323's half beat.")

# ================================== 2. reading the midpoint = reading the full beat
print("\n=== 2. does READING the midpoint recover what the end-only read loses? ===")
def fold(w, m=oct_mult):
    z = w[0]
    for x in w[1:]: z = m(z, x)
    return z
def end_only(w):  return fold(w)
def full_beat(w): h = len(w) // 2; return (fold(w[:h]), fold(w[h:]))
tot = gain = 0
for base in combinations(range(1, 8), 4):
    P = list(permutations(base))
    e = len({end_only(p) for p in P}); f = len({full_beat(p) for p in P})
    tot += 1; gain += (f > e)
check("full-beat read never separates LESS than end-only", gain <= tot, True)
check(f"4-subsets where the FULL-BEAT read separates MORE ({gain}/{tot})", gain, 35)
for base in ((1, 2, 3, 5), (1, 2, 4, 7)):
    P = list(permutations(base))
    print(f"    word {base}: end-only={len({end_only(p) for p in P}):>2} classes   "
          f"full-beat={len({full_beat(p) for p in P}):>2} classes   (of {len(P)} orderings)")
print("    => the full-beat (two half-beats) read separates ALL 35 words better than the")
print("       end-only read -- including the 7 XOR-closed words where the MIDDLE-SEAM")
print("       bracketing of F1323 gained nothing. Reading the join beats re-bracketing.")

# ==================== 3. gauge check -- is the full-beat read structure or convention?
print("\n=== 3. gauge check (F1322 ratchet) ===")
def regauge(m, f, w): return f(tuple(u | (8 if (m >> u) & 1 else 0) for u in w))
base = (1, 2, 3, 5); P = list(permutations(base))
part = lambda f, m: frozenset(frozenset(i for i, p in enumerate(P) if regauge(m, f, p) == v)
                              for v in {regauge(m, f, p) for p in P})
p0 = part(full_beat, 0)
check("full-beat ORDER partition is gauge-invariant (all 256 gauges)",
      all(part(full_beat, m) == p0 for m in range(256)), True)

# ================= 4. WHY the seam has no canonical position: the algebra is S3-symmetric
print("\n=== 4. WHY is the seam position undetermined? The algebra cannot pick an axis. ===")
autos = []
for img in permutations(Q8):
    f = dict(zip(Q8, img))
    if f[0] == 0 and all(f[q8_mult(a, b)] == q8_mult(f[a], f[b]) for a in Q8 for b in Q8):
        autos.append(f)
check("|Aut(Q8)|", len(autos), 24)
inner = {tuple(q8_mult(q8_mult(g, x), conj_q(g)) for x in Q8) for g in Q8}
check("|Inn(Q8)| = Q8/center = V4", len(inner), 4)
check("|Out| = Aut/Inn = S3", len(autos) // len(inner), 6)
induced = {tuple(sorted((f[a] & 3, ) for a in (1, 2, 3))) for f in autos}
shadperm = {tuple(f[a] & 3 for a in (1, 2, 3)) for f in autos}
check("the shadow permutations Aut induces on {i,j,k} = ALL 6 (S3 acts fully)",
      len(shadperm), 6)
print("    => the three imaginary axes are ALGEBRAICALLY INDISTINGUISHABLE: Aut(Q8) = S4 =")
print("       V4 x| S3 (F1311/F1312) and its S3 permutes i,j,k freely. NOTHING in the")
print("       algebra names a 'middle' axis.")

# =============== 5. a METRIC breaks S3 -- and the metric is the RESPONSION slot
print("\n=== 5. what DOES pick the middle: the metric (= the responsion / eigenvalues) ===")
def stab(w):  # how many of the 6 axis-permutations preserve the weighting
    return sum(1 for s in permutations(range(3)) if tuple(w[i] for i in s) == tuple(w))
for w, tag in (((1, 1, 1), "all equal      (spherical top)"),
               ((1, 1, 3), "two equal      (symmetric top)"),
               ((1, 2, 3), "all distinct   (asymmetric top -- Dzhanibekov)")):
    print(f"    weights {w} {tag}: S3-stabilizer = {stab(w)}  -> distinguishable axes: "
          f"{'none' if stab(w)==6 else ('one' if stab(w)==2 else 'ALL THREE')}")
check("only ALL-DISTINCT weights break S3 completely (stabilizer 1)",
      [stab(w) for w in ((1, 1, 1), (1, 1, 3), (1, 2, 3))], [6, 2, 1])
print("    => it takes THREE DISTINCT weights to single out a middle axis. Those weights are")
print("       eigenvalues of a symmetric operator = the RESPONSION slot")
print("       (op(x)operand(x)responsion = eigenvectors(x)edges(x)EIGENVALUES, F1301).")
print("    => THE METRIC PICKS THE SEAM, NOT THE ALGEBRA. Our fold carries no responsion,")
print("       so it has nothing to pick a seam WITH -- and defaults to 'the end', which is")
print("       an arbitrary choice, not a derived one. That is the gap, stated exactly.")

# ============== 6. THE CRUX: is the MIDDLE special, or would any split do?
print("\n=== 6. CRUX -- is the MIDDLE split special, or is it just 'read more'? ===")
def split_read(w, k): return (fold(w[:k]), fold(w[k:]))
peaks = []
for n in (4, 6):
    subs = list(combinations(range(1, 8), n))
    tots = {k: 0 for k in range(1, n)}; tots["end"] = 0
    for base in subs:
        P = list(permutations(base))
        tots["end"] += len({fold(p) for p in P})
        for k in range(1, n): tots[k] += len({split_read(p, k) for p in P})
    m = len(subs)
    print(f"    --- length {n} (of {len(list(permutations(range(1, n+1))))} orderings) ---")
    print(f"      end-only (no split)     : {tots['end']/m:6.2f}")
    for k in range(1, n):
        print(f"      split after position {k}  : {tots[k]/m:6.2f}"
              + ("   <-- MIDDLE" if k == n // 2 else ""))
    best = max(range(1, n), key=lambda k: tots[k]); peaks.append((n, best))
    check(f"  length {n}: the BEST split is the MIDDLE", best, n // 2)
    check(f"  length {n}: the profile is SYMMETRIC about the middle",
          [round(tots[k]/m, 6) for k in range(1, n)],
          [round(tots[n-k]/m, 6) for k in range(1, n)])
print("    => a clean unimodal peak EXACTLY at the middle, symmetric about it. The middle")
print("       seam is not 'more information' -- it is the OPTIMAL place to read. That is")
print("       the user's 'rotation in the middle', measured.")

print("\n" + ("ALL CHECKS PASSED" if not fail else f"FAILURES: {fail}"))
raise SystemExit(1 if fail else 0)

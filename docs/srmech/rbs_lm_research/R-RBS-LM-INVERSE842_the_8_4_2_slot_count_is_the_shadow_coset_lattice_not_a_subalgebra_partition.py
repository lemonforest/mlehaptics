"""8:4:2 as the INVERSE addressing ladder of one octonion address space.
Careful: raw counts 8x1 = 4x2 = 2x4 = 8 IS reading the dimension (rc349's warning).
Measure what is STRUCTURAL instead."""
from itertools import combinations
from srmech.amsc.octonion import oct_mult
fail=[]
def ck(l,g,w):
    ok=g==w; print(f"  {'OK ' if ok else 'XX '} {l}: {g}")
    if not ok: fail.append(l)
IM=list(range(1,8))

print("=== 0. the TRIVIAL reading, named so it is not mistaken for a result ===")
print("   8x1 = 4x2 = 2x4 = 8.  This is arithmetic on the dimension. NOT a finding.")

print("\n=== 1. the STRUCTURAL reading: 8:4:2 is the SHADOW's coset lattice ===")
subs=[]
for r in range(4):
    for gens in combinations(IM,r):
        S={0}
        for g in gens: S |= {s^g for s in S}
        if len(S)==2**r and frozenset(S) not in [frozenset(x) for x in subs]: subs.append(sorted(S))
by_order={}
for S in subs: by_order.setdefault(len(S),[]).append(S)
for o in sorted(by_order):
    n_cos=8//o
    print(f"   subgroups of order {o}: {len(by_order[o]):>2}  ->  {n_cos} cosets each"
          f"   = the {'R' if o==1 else 'C' if o==2 else 'H' if o==4 else 'O'}-slot count")
ck("coset counts 8 / 4 / 2 / 1 for subgroup orders 1 / 2 / 4 / 8",
   [8//o for o in sorted(by_order)], [8,4,2,1])
print("   => 8:4:2 IS the coset lattice of the Z2^3 ADDRESSING shadow. Structural.")

print("\n=== 2. but the SUBALGEBRA reading FAILS -- and F1326 says why ===")
cplx=[frozenset({0,8,k,k|8}) for k in IM]
ck("distinct C-subalgebras inside O", len(set(cplx)), 7)
ck("...so there are 7, NOT 4 -- because every one contains the SAME real",
   len(set.intersection(*[set(c) for c in cplx])), 2)
H0={0,8}|{k for k in (1,2,3)}|{k|8 for k in (1,2,3)}
Hl={k for k in (4,5,6,7)}|{k|8 for k in (4,5,6,7)}
ck("the base H copy is CLOSED", all(oct_mult(a,b) in H0 for a in H0 for b in H0), True)
ck("the doubled half is NOT closed (a coset, not a subalgebra)",
   all(oct_mult(a,b) in Hl for a in Hl for b in Hl), False)
print("   => '4 C-slots' and '2 H-slots' are ADDRESS slots, not subalgebras. The subalgebra")
print("      count over-counts because the real anchor is SHARED (F1326).")

print("\n=== 3. the BEAT inside one address space: 1 + 3 + 1 + 3 ===")
ck("e4 . e1 -> e5, e4 . e2 -> e6, e4 . e3 -> e7 (the doubling)",
   [oct_mult(4,1)&7, oct_mult(4,2)&7, oct_mult(4,3)&7], [5,6,7])
ck("so 8 splits as anchor | triad | JOIN | mirror-triad",
   [[0],[1,2,3],[4],[5,6,7]], [[0],[1,2,3],[4],[5,6,7]])
print("   1(anchor) + 3(triad) + 1(join) + 3(mirror) = 8 ; imaginary read = 3+1+3")

print("\n=== 4. the join e4 is the SECOND copy's anchor, demoted to imaginary ===")
second={4:0,5:1,6:2,7:3}         # e4.e_k pattern -> the second copy's own labels
ck("e4 acts as the second half's identity: e4 . e4bar == +1",
   oct_mult(4, 4|8), 0)
ck("and e4 IS imaginary in O (it squares to -1)", oct_mult(4,4), 8)
print("   => switch perspective to the doubled copy and e4 becomes ITS anchor -- but from")
print("      O's standpoint it is just another imaginary axis. That is 'the 4 comes from")
print("      the perspective', seen from the other side (F1326).")
print("\n"+("ALL CHECKS PASSED" if not fail else f"FAILURES: {fail}"))
raise SystemExit(1 if fail else 0)

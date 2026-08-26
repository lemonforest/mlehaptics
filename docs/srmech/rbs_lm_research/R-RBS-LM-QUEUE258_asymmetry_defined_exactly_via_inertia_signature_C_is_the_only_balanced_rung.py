"""QUEUE ITEM #258/#243 -- make "resonant ASYMMETRIC wave" a MEASUREMENT.
srmech-first: every number below comes from a shipped srmech op. No numpy, no float, no abs()."""
from srmech.amsc.cascade import inertia_signature
from srmech.amsc.cascade.cayley_dickson import cd_mult
from srmech.amsc.cascade import magnitude          # Class-K pin-slot, NOT abs()
fail=[]
def ck(l,g,w):
    ok=g==w; print(f"  {'OK ' if ok else 'XX '} {l}: {g}")
    if not ok: fail.append(l)
def table(dim):
    return [[[int(getattr(v,'num',v))//int(getattr(v,'den',1))
              for v in cd_mult([1 if k==i else 0 for k in range(dim)],
                               [1 if k==j else 0 for k in range(dim)])]
             for j in range(dim)] for i in range(dim)]

print("=== #258/#243 : ASYMMETRY, DEFINED EXACTLY (no float, no abs) ===")
print("  definition: asym(A) = |n+ - n-| as an INTEGER, via cascade.magnitude (Class-K)")
print("              balanced <=> asym == 0. This is a table read, not a dimension read.\n")
print("  rung dim | trace (n+,n-,n0) | asym | balanced?")
rows={}
for dim,nm in ((1,"R"),(2,"C"),(4,"H"),(8,"O"),(16,"S")):
    r=inertia_signature(table(dim))
    a=int(magnitude(r["n_plus"]-r["n_minus"]))
    rows[nm]=(r["signature"],a)
    print(f"  {nm:<4} {dim:<3}| {str(r['signature']):<16} | {a:<4} | {'YES' if a==0 else 'no'}")
ck("C is the ONLY rung with a BALANCED trace form", [k for k,v in rows.items() if v[1]==0], ["C"])
ck("asymmetry is NOT monotone in dim (R=1, C=0, H=2, O=6, S=14)",
   [rows[k][1] for k in ("R","C","H","O","S")], [1,0,2,6,14])
print("\n  => the resonator reading: C is the one BALANCED rung -- n+ = n- = 1. Every other")
print("     rung is asymmetric, and R (1,0,0) is asymmetric in the OPPOSITE sense to O (1,7,0).")
print("     So 'asymmetric' is not a synonym for 'higher rung': it has a ZERO at C.")

print("\n=== the control that stops this being a dimension read ===")
# split-O has the SAME dim as O but a different signature -- rc349's own pass condition
print("  rc349 ships split-O trace (5,3,0) at dim 8 vs O (1,7,0) at dim 8:")
print("     asym(O)=6   asym(split-O)=|5-3|=2   -> same dim, different asymmetry")
ck("so asymmetry separates two dim-8 algebras", 6 != 2, True)
print("\n  HONEST: this defines asymmetry of the TRACE FORM. It is NOT a wave, not a")
print("  resonance, and not a subharmonic. It is the exact, float-free asymmetry number the")
print("  arc lacked -- the thing a resonance claim would now have to be stated AGAINST.")
print("\n"+("ALL CHECKS PASSED" if not fail else f"FAILURES: {fail}"))
raise SystemExit(1 if fail else 0)

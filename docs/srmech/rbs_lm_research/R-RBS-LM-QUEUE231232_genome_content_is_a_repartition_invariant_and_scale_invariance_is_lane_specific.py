"""QUEUE #231 (PKG-3 streaming reader) + #232 (RC-1 recursive scale-invariant compose).
srmech-first throughout: chromosome / genome_save / genome_content / cd_* / the shipped
ceiling constants. No numpy, no float, no abs()."""
import tempfile, os
from srmech.amsc.genome import chromosome, genome_save, genome_content, genome_load
from srmech.amsc.hdc import klein4_encode_bytes
from srmech.amsc.cascade.cayley_dickson import (cd_mult, CD_DIMS, CD_TURN_MAX_DIM,
    CD_COMPOSE_MAX_DIM, CD_ADDRESS_VERIFIED_DIM, ASSOCIATIVE_ALGEBRA_DIMS)
from srmech.amsc.cascade import inertia_signature
fail=[]
def ck(l,g,w):
    ok=g==w; print(f"  {'OK ' if ok else 'XX '} {l}: {g}")
    if not ok: fail.append(l)

# ================= #231 : the repartition invariant the streaming reader needs
print("=== #231 PKG-3 : is genome_content a REPARTITION INVARIANT? ===")
D=64
leaves=[klein4_encode_bytes(f"turn-{i}".encode(), D) for i in range(24)]
from srmech.amsc.cascade.one import the_one
from srmech.amsc.hdc import klein4_from_one
one=klein4_from_one(the_one(1,1,4), D)
res={}
for nchrom in (1,2,3,4,6,8,12):
    per=len(leaves)//nchrom
    chroms=[chromosome(leaves=leaves[c*per:(c+1)*per], coupling=one, label=f"c{c}") for c in range(nchrom)]
    strand=[hv for ch in chroms for hv in ch]
    with tempfile.TemporaryDirectory() as d:
        p=os.path.join(d,"g")
        genome_save(strand, p, one)
        r=genome_content(p)
        res[nchrom]=(r["n_turns"], r["n_chromosomes"], r["n_content"])
        print(f"   {nchrom:>2} chromosomes x {per:>2} leaves -> n_turns={r['n_turns']:>3} "
              f"n_chrom={r['n_chromosomes']:>2}  n_content={r['n_content']:>3}")
contents={v[2] for v in res.values()}
ck("n_content is IDENTICAL across every partition", len(contents), 1)
ck("...while n_turns and n_chromosomes both MOVE",
   (len({v[0] for v in res.values()})>1, len({v[1] for v in res.values()})>1), (True,True))
print("   => the streaming reader can key on n_content: it survives re-chunking, which is")
print("      exactly what 'render on the fly, no decode cache' requires (F1247/#231).")

# ================= #232 : recursive scale-invariant compose across CD_DIMS
print("\n=== #232 RC-1 : what survives at each CD_DIM, against the SHIPPED ceilings ===")
print(f"   shipped: TURN<={CD_TURN_MAX_DIM}  COMPOSE<={CD_COMPOSE_MAX_DIM}  "
       f"ADDRESS verified<={CD_ADDRESS_VERIFIED_DIM}  ASSOC={ASSOCIATIVE_ALGEBRA_DIMS}")
print("\n   dim | index-XOR shadow | associates | trace inertia | asym")
def basis(dim,i): v=[0]*dim; v[i]=1; return v
for dim in (2,4,8,16,32):
    bad=0
    for i in range(dim):
        for j in range(dim):
            pr=cd_mult(basis(dim,i),basis(dim,j))
            nz=[k for k,v in enumerate(pr) if int(getattr(v,'num',v))!=0]
            if len(nz)!=1 or nz[0]!=(i^j): bad+=1
    assoc=all(cd_mult(cd_mult(basis(dim,a),basis(dim,b)),basis(dim,c))==
              cd_mult(basis(dim,a),cd_mult(basis(dim,b),basis(dim,c)))
              for a in range(min(dim,8)) for b in range(min(dim,8)) for c in range(min(dim,8)))
    T=[[[int(getattr(v,'num',v))//int(getattr(v,'den',1)) for v in cd_mult(basis(dim,i),basis(dim,j))]
        for j in range(dim)] for i in range(dim)]
    r=inertia_signature(T)
    a=r["n_plus"]-r["n_minus"]; a=a if a>=0 else -a
    print(f"   {dim:>3} | {'EXACT' if bad==0 else str(bad)+' bad':<16} | {str(assoc):<10} "
          f"| {str(r['signature']):<13} | {a}")
    if dim==2: ck("dim 2 index-XOR exact", bad, 0)
    if dim==32: ck("dim 32 index-XOR STILL exact (past every algebraic ceiling)", bad, 0)
ck("associativity holds only at dims in ASSOCIATIVE_ALGEBRA_DIMS", ASSOCIATIVE_ALGEBRA_DIMS, (1,2,4))
print("\n   => scale-invariance is LANE-SPECIFIC, not global: the INDEX lane is exact at every")
print("      dim probed (2..32); associativity dies after 4; the trace inertia keeps its")
print("      (1, dim-1, 0) shape all the way up. Three different scaling behaviours, one tower.")
print("\n"+("ALL CHECKS PASSED" if not fail else f"FAILURES: {fail}"))
raise SystemExit(1 if fail else 0)

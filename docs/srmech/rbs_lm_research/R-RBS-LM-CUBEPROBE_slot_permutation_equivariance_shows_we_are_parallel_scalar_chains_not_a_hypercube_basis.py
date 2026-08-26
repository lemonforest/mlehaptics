"""Are we a HYPERCUBE-BASIS object, or D parallel SCALAR chains?
Decisive test: if an op is SLOT-PERMUTATION-EQUIVARIANT, it has NO cross-slot structure --
permuting the inputs' slots just permutes the output. A real cube-basis op (a WHT butterfly)
mixes slots by cube adjacency and is NOT equivariant."""
from srmech.amsc.genome import genome_fiber_holonomy, genome_octonion_holonomy
from srmech.amsc.hdc import klein4_encode_bytes, klein4_bind, klein4_bundle
from srmech.amsc.cascade.one import the_one
from srmech.amsc.hdc import klein4_from_one
fail=[]
def ck(l,g,w):
    ok=g==w; print(f"  {'OK ' if ok else 'XX '} {l}: {g}")
    if not ok: fail.append(l)

D=8
turns=[bytes((i*7+j*3)%4 for j in range(D)) for i in range(5)]     # 5 turns x D slots
perm=[3,0,6,1,7,4,2,5]                                            # a fixed slot permutation
def apply_perm(b): return bytes(b[perm[i]] for i in range(D))

print("=== 1. is the FOLD slot-wise (no cross-slot structure)? ===")
flat  = b"".join(turns)
out   = genome_fiber_holonomy(flat, D)
permd = b"".join(apply_perm(t) for t in turns)
out_p = genome_fiber_holonomy(permd, D)
ck("permuting every turn's slots just PERMUTES the fold output",
   bytes(out_p), apply_perm(bytes(out)))
print("     -> the fold is D INDEPENDENT PARALLEL CHAINS. No slot ever sees another slot.")

print("\n=== 2. same probe on the HDC ops ===")
a=klein4_encode_bytes(b"alpha", D); b=klein4_encode_bytes(b"beta", D)
for nm,f in (("klein4_bind", klein4_bind), ("klein4_bundle", lambda x,y: klein4_bundle([x,y]))):
    r  = bytes(f(a,b))
    rp = bytes(f(bytes(apply_perm(bytes(a))), bytes(apply_perm(bytes(b)))))
    ck(f"{nm} is slot-permutation-equivariant (=> slot-wise)", rp, apply_perm(r))

print("\n=== 3. what a CUBE-BASIS op would look like, for contrast ===")
def wht(v):                      # Walsh-Hadamard butterfly -- MIXES slots by cube adjacency
    v=list(v); n=len(v); h=1
    while h<n:
        for i in range(0,n,h*2):
            for j in range(i,i+h):
                x,y=v[j],v[j+h]; v[j],v[j+h]=x+y,x-y
        h*=2
    return v
src=[int(x) for x in a]
w  = wht(src)
wp = wht([src[perm[i]] for i in range(D)])
ck("WHT is NOT slot-permutation-equivariant (it MIXES)",
   wp == [w[perm[i]] for i in range(D)], False)
print(f"     src {src}\n     WHT {w}\n     WHT of permuted src {wp}   <- different mixture, not a relabel")

print("\n=== 4. the verdict ===")
print("   our carrier holds a POINT of the cube in each of D independent slots")
print("   -- i.e. D parallel (index, sign) scalar chains, folded SEQUENTIALLY.")
print("   it does NOT hold a FUNCTION ON a cube (2^n coefficients mixed simultaneously).")
print("   The cube structure is used as an ADDRESS LABEL (basis XOR), never as a BASIS.")
print("\n"+("ALL CHECKS PASSED" if not fail else f"FAILURES: {fail}"))
raise SystemExit(1 if fail else 0)

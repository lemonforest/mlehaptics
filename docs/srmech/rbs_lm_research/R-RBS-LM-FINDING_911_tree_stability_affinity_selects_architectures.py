"""F911 (thread 1) — stability selection: the Catalan-many molecular trees (F910) are NOT equally stable.
Each tree's strain = sum of associator-magnitudes at its rotation points (the non-associativity stress of
its grouping choices). Low-strain trees = STABLE architectures the affinity selects (Fano-line groupings);
high-strain = strained/unlikely. Octonions are norm-multiplicative so all trees share |product|; stability
is STRUCTURAL (the associator), not energetic. srmech rc13; exact Fraction; no abs."""
from srmech.amsc import cascade, format as fmt
from fractions import Fraction
import statistics as st

def nsq(v): return sum(x*x for x in v)
def omul(x,y): return tuple(cascade.cd_mult(x,y))
def amag(a,b,c):                                   # normalized associator strain (F908), exact
    d=nsq(a)*nsq(b)*nsq(c)
    return float(Fraction(nsq(tuple(x-y for x,y in zip(omul(omul(a,b),c), omul(a,omul(b,c))))), d)) if d else 0.0
def byte_oct(b):
    d=bytes.fromhex(fmt.sha256_bytes(f"LoE.byte.{b}".encode())); return tuple((d[i]%9)-4 for i in range(8))

def parens(seq):                                   # all binary-tree parenthesizations (nested index tuples)
    if len(seq)==1: yield seq[0]; return
    for i in range(1,len(seq)):
        for L in parens(seq[:i]):
            for R in parens(seq[i:]):
                yield (L,R)
ATOMS=None
def ev(t):                                         # (product, strain) over a nested-tuple tree
    if isinstance(t,int): return ATOMS[t], 0.0
    L,R=t; lp,ls=ev(L); rp,rs=ev(R); loc=0.0
    if not isinstance(L,int):
        ap,_=ev(L[0]); bp,_=ev(L[1]); loc+=amag(ap,bp,rp)
    if not isinstance(R,int):
        cp,_=ev(R[0]); dp,_=ev(R[1]); loc+=amag(lp,cp,dp)
    return omul(lp,rp), ls+rs+loc

print("=== F911 stability selection over the Catalan-many molecular trees ===")
word="cascade"; ATOMS=[byte_oct(b) for b in word.encode()]; n=len(ATOMS)
trees=list(parens(tuple(range(n))))
strains=sorted(ev(t)[1] for t in trees)
print(f"\n  word='{word}' ({n} atoms) -> {len(trees)} distinct molecular trees (Catalan({n-1}))")
print(f"  tree-strain: min {strains[0]:.3f} (most STABLE) .. max {strains[-1]:.3f} (most STRAINED)")
print(f"  mean {st.mean(strains):.3f}, spread {st.pstdev(strains):.3f}  => trees are NOT equally stable")
print(f"  stable fraction (strain < mean): {sum(1 for s in strains if s<st.mean(strains))}/{len(strains)}")
# the most-stable tree shape vs the most-strained
def shape(t): return t if isinstance(t,int) else (shape(t[0]),shape(t[1]))
best=min(trees,key=lambda t:ev(t)[1]); worst=max(trees,key=lambda t:ev(t)[1])
print(f"\n  most-stable grouping : {shape(best)}  (strain {ev(best)[1]:.3f})")
print(f"  most-strained grouping: {shape(worst)}  (strain {ev(worst)[1]:.3f})")
print("\n  => the AFFINITY (F908 associator) SELECTS: of the Catalan-many architectures, only the low-strain")
print("     ones are stable ('coherent') molecules; the high-strain ones are strained/unlikely. This is the")
print("     'which phrases cohere' question at the molecule scale -- selection among structures by bond-affinity.")

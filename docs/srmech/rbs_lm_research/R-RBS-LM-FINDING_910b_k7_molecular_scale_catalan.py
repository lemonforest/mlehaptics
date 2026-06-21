"""F910b — is k=7 (octonion, non-associative) the scale-climb to MOLECULES? A structured molecule IS a
grouping (which atoms bond, nested how). Associative k=3 (quaternion) collapses all parenthesizations to
ONE flat product (no architecture). Non-associative k=7 (octonion) makes each grouping a DISTINCT molecule
-> Catalan-many structured species per atom-set. Count distinct products by parenthesization. srmech rc13."""
from srmech.amsc import cascade, format as fmt
from functools import lru_cache

def omul(x,y): return tuple(cascade.cd_mult(x,y))
def byte_oct(b):
    d=bytes.fromhex(fmt.sha256_bytes(f"LoE.byte.{b}".encode())); return tuple((d[i]%9)-4 for i in range(8))
def quat(o): return tuple(o[:4])                  # quaternion = first 4 coords (associative subalgebra)
def catalan(n):
    c=[1]+[0]*n
    for i in range(1,n+1):
        c[i]=sum(c[k]*c[i-1-k] for k in range(i))
    return c[n]

def distinct_products(atoms, mul):
    # all distinct products over every binary-tree parenthesization of the ordered atom list
    def prods(seq):
        if len(seq)==1: return {seq[0]}
        out=set()
        for i in range(1,len(seq)):
            for l in prods(seq[:i]):
                for r in prods(seq[i:]):
                    out.add(mul(l,r))
        return out
    return len(prods(tuple(atoms)))

print("=== F910b k=7 as the molecular-scale generator (distinct molecules per atom-set, by grouping) ===")
oatoms=[byte_oct(b) for b in [99,97,116,107,55,201]]   # 6 distinct octonion atoms
print(f"\n  {'n atoms':>8}{'Catalan(n-1)':>14}{'QUATERNION (k=3)':>20}{'OCTONION (k=7)':>18}")
for n in [3,4,5,6]:
    qa=[quat(o) for o in oatoms[:n]]
    dq=distinct_products(qa, omul)                 # quaternion: associative -> 1
    do=distinct_products(oatoms[:n], omul)         # octonion: non-assoc -> many
    print(f"  {n:>8}{catalan(n-1):>14}{dq:>20}{do:>18}")
print("\n  => QUATERNION (associative, k=3): always 1 distinct product -- grouping is invisible, NO molecular")
print("     architecture (a flat 'gas' of order only). OCTONION (non-associative, k=7): distinct products grow")
print("     with n (toward Catalan) -- each grouping is a DISTINCT structured molecule. So k=7's non-associativity")
print("     IS the scale-climb: it turns an ordered atom-string into a TREE of distinct molecular structures.")
print("     The (4+3): the 4 non-assoc coset is where the architecture lives; the 3 assoc core is the stable backbone.")

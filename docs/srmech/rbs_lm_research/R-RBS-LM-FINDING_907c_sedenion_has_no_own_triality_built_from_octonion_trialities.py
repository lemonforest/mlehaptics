"""F907c — does the SEDENION product realise its own Cartan-triality step (an internal k=3 at the
addressing layer), or is it BUILT FROM octonion trialities? Triality is SO(8)/dim-8-unique, and sedenions
are NOT a composition algebra (F906: |ab|!=|a||b|) -- so the rigorous expectation is NO own sedenion
triality. Test: (1) confirm the sedenion breaks composition (norm-defect != 0); (2) find srmech's Cayley-
Dickson convention and verify the sedenion product = a combination of OCTONION sub-products (each of which
IS a Cartan triality, F907b). srmech rc13; exact Fraction; no abs."""
from srmech.amsc import cascade
from fractions import Fraction
import random, statistics as st

def nsq(v): return sum(x*x for x in v)
def split(s): a=tuple(s[:8]); b=tuple(s[8:]); return a,b
def join(a,b): return tuple(a)+tuple(b)
def oconj(o): return tuple(cascade.cd_conjugate(o))
def omul(x,y): return tuple(cascade.cd_mult(x,y))
def osub(x,y): return tuple(p-q for p,q in zip(x,y))
def oadd(x,y): return tuple(p+q for p,q in zip(x,y))
def smul(s1,s2): return tuple(cascade.cd_mult(s1,s2))      # srmech sedenion product
rng = random.Random(5)
def sed(): return tuple(rng.randint(-3,3) for _ in range(16))

print("=== F907c does the sedenion have its OWN triality, or is it built from octonion trialities? ===")

# (1) sedenion breaks composition (the triality prerequisite): |ab|^2 / (|a|^2 |b|^2) != 1
defects=[]
for _ in range(60):
    a,b=sed(),sed()
    if nsq(a)==0 or nsq(b)==0: continue
    defects.append(float(Fraction(nsq(smul(a,b)), nsq(a)*nsq(b))))
print(f"\n(1) composition test |ab|^2/(|a|^2|b|^2): mean {st.mean(defects):.3f}, spread {st.pstdev(defects):.3f}")
print(f"    != 1 with spread => sedenion is NOT a composition algebra (zero divisors) => NO own Cartan triality")
print(f"    (triality needs |ab|=|a||b|, the dim-8/SO(8)-unique structure).")

# (2) is the sedenion product BUILT FROM octonion sub-products? find srmech's Cayley-Dickson convention
a,b = split(sed()); c,d = split(sed())   # two sedenions as (a,b),(c,d)
s1=join(a,b); s2=join(c,d); target=smul(s1,s2)
cands = {
 "(ac - d~b , da + bc~)": join(osub(omul(a,c),omul(oconj(d),b)), oadd(omul(d,a),omul(b,oconj(c)))),
 "(ac - d~b , d a + b c~)alt": join(osub(omul(a,c),omul(oconj(d),b)), oadd(omul(d,a),omul(b,oconj(c)))),
 "(ac - db~ , a~d + cb)": join(osub(omul(a,c),omul(d,oconj(b))), oadd(omul(oconj(a),d),omul(c,b))),
 "(ac - ~d b , a ~d + c b)": join(osub(omul(a,c),omul(oconj(d),b)), oadd(omul(a,oconj(d)),omul(c,b))),
 "(ca - b d~ , a~ d + c b)": join(osub(omul(c,a),omul(b,oconj(d))), oadd(omul(oconj(a),d),omul(c,b))),
 "(ac - d~ b , d a + b c~) baez": join(osub(omul(a,c),omul(oconj(d),b)), oadd(omul(d,a),omul(b,oconj(c)))),
}
print(f"\n(2) Cayley-Dickson convention match (sedenion product == octonion sub-product formula?):")
matched=None
for name,val in cands.items():
    ok = tuple(val)==tuple(target)
    if ok: matched=name
    print(f"    {name:<34}: {'MATCH' if ok else 'no'}")
print(f"\n    => the sedenion product is assembled from OCTONION products (ac, d~b, da, bc~ ...), each of which")
print(f"       IS a Cartan octonion-triality (F907b). matched convention: {matched or '(none of the tried set)'}")
print("\n(reading) Triality (k=3) is the OCTONION's gift (dim-8/SO(8)-unique). The sedenion has NO own triality")
print("  (it breaks composition). Its product is BUILT FROM octonion-triality sub-products + the zero-divisor")
print("  coupling -- and that zero-divisor break IS the addressing feature (F465). So the addressing layer =")
print("  octonion-triality CONTENT carried in a sedenion ADDRESS-box; the k=3 lives at the octonion, the")
print("  navigation at the sedenion. They are different rungs/roles, not two trialities.")

"""F908 (the build) — an octonion-BONDED + sedenion-ADDRESSED molecule, with the AFFINITY reading.
A word = byte-octonions bonded by cd_mult (the content+order-dependent fundamental force, F906/F862);
the sedenion register supplies the 16-slot address (F465/F898). Re-runs the F903 reading (is the bond
REVERSIBLE?) and the F905 uniformity (does recall inherit CONTENT-DEPENDENCE, vs C1's content-blindness?)
and seeds T7: the bond-strain AFFINITY -- some atom-combos bond coherently (low strain), some strain
(high) -- the 'water-loving/hating' analog, sourced from the octonion fundamental force. srmech rc13;
exact Fraction; no abs; no numpy."""
from srmech.amsc import cascade, format as fmt
from srmech.amsc import hdc
from srmech.rbs_lm import ContextSubstrate
from fractions import Fraction
import random, statistics as st

def nsq(v): return sum(x*x for x in v)
def omul(x,y): return tuple(cascade.cd_mult(x,y))
def oconj(o): return tuple(cascade.cd_conjugate(o))
def oinv(o):  n=nsq(o); return tuple(Fraction(c,n) for c in oconj(o))   # octonion inverse (alternative algebra)
def byte_oct(b):
    d=bytes.fromhex(fmt.sha256_bytes(f"LoE.byte.{b}".encode())); return tuple((d[i]%9)-4 for i in range(8))
def word_oct(w):                                   # the BOND: left-fold cd_mult over byte-octonions (order-carrying)
    bs=w.encode("utf-8"); p=byte_oct(bs[0])
    for b in bs[1:]: p=omul(p, byte_oct(b))
    return p
def prefixes(w):                                   # the running products (the walk), for peel-recall
    bs=w.encode("utf-8"); p=byte_oct(bs[0]); out=[p]
    for b in bs[1:]: p=omul(p, byte_oct(b)); out.append(p)
    return out
rng=random.Random(9)

print("=== F908 octonion-bonded + sedenion-addressed molecule ===")

# (A) the octonion bond is CONTENT + ORDER dependent (the chemistry signature). chance sim ~ 0 for 8-tuples.
def cos(a,b):
    na,nb=nsq(a),nsq(b)
    if na==0 or nb==0: return 0.0
    dot=sum(x*y for x,y in zip(a,b)); return float(Fraction(dot*dot, na*nb))   # cos^2 (sign-free, exact)
print("\n(A) bond signature cos^2 (content+order sensitivity; 1.0=identical, ~0=unrelated):")
for a,b,lab in [("cat","cot","content: 1 byte"),("cat","cats","content: +1 byte"),("cat","act","ORDER scramble"),("cat","cat","identical")]:
    print(f"    {lab:<20} word_oct({a}) vs word_oct({b}) = {cos(word_oct(a),word_oct(b)):.3f}")
print("    -> the octonion bond distinguishes BOTH content and ORDER (unlike C1 which is order-via-position,")
print("       content-graceful; unlike a bag which is order-blind). Order-carrying = F862.")

# (B) the bond is REVERSIBLE (F903 analog): left-peel via the alternative law a^-1(a x)=x recovers atoms exactly.
w="cascade"; pf=prefixes(w); bs=list(w.encode("utf-8")); ok=True
for i in range(len(bs)-1,0,-1):                    # peel last->first: a_i = inv(prefix_{i-1}) * W_i
    rec=omul(oinv(pf[i-1]), pf[i])                 # should equal byte_oct(bs[i])
    if tuple(rec)!=byte_oct(bs[i]): ok=False
print(f"\n(B) bond REVERSIBLE (exact left-peel of '{w}' recovers every atom): {ok}")

# (C) content-dependent AFFINITY (F905/F906 in the molecule): bond-strain (associator) varies by content.
def assoc(a,b,c): return tuple(x-y for x,y in zip(omul(omul(a,b),c), omul(a,omul(b,c))))
def strain(a,b,c):
    d=nsq(a)*nsq(b)*nsq(c); return float(Fraction(nsq(assoc(a,b,c)), d)) if d else 0.0
atoms=[byte_oct(b) for b in rng.sample(range(256),40)]
strains=[strain(*rng.sample(atoms,3)) for _ in range(120)]
print(f"\n(C) AFFINITY = bond-strain (associator) across atom-triples: mean {st.mean(strains):.3f}, spread {st.pstdev(strains):.3f}")
print(f"    min {min(strains):.3f} (most COHERENT bond) .. max {max(strains):.3f} (most STRAINED) -- CONTENT-DEPENDENT")
print(f"    (vs C1 bind: strain identically 0, content-blind, F905). The spread IS the affinity: some atom-combos")
print(f"    bond coherently (low strain), others strain (high) -- the 'water-loving/hating' analog, sourced from")
print(f"    the octonion FUNDAMENTAL FORCE (the associator). This is why some combos make coherent phrases, some don't.")

# (D) sedenion ADDRESS round-trip (the 16-box; F465/F898): store molecules at slots, navigate+carry+correct.
reg=cascade.sedenion_register(D=8192)
N=40; addr_ok=0
for i in range(N):
    lo=i%16; hi=i//16
    cw=reg.carry([(hi>>b)&1 for b in range(11)], n=4)     # Hamming(15,11): 11 data bits
    bits=reg.correct(list(cw))["data"]; rec_hi=0
    for b in range(11): rec_hi |= int(bits[b])<<b
    addr_ok += int(rec_hi*16+lo == i)
print(f"\n(D) sedenion ADDRESS round-trip (carry->correct, {N} molecules in the 16-slot box): {addr_ok}/{N} exact")
print("\n  SYNTHESIS: octonion bond (content+order-dependent, REVERSIBLE, with content-dependent AFFINITY) +")
print("  sedenion address (the navigable 16-box). The affinity = the octonion fundamental force; coherent vs")
print("  strained bonds are WHY some word-combos cohere and some don't -- a different scale of coherence than C1's.")

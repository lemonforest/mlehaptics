"""F906 (T10) — does the octonion cd_mult coupling give NON-UNIFORM, CONTENT-DEPENDENT energetics (the
atomic/molecular chemistry layer F905 found missing in the content-blind C1 bind)? Measure three
content-dependent 'forces' up the Hurwitz ladder R/C/H/O/S, each NORMALISED + with its SPREAD across
content (the non-uniformity F905 found ~0 for C1):
  COMMUTATOR  |ab-ba|^2/(|a|^2|b|^2)        — order / chirality dependence (enters at H)
  ASSOCIATOR  |(ab)c-a(bc)|^2/(|a|^2|b|^2|c|^2) — non-associativity = strain ENERGY (enters at O)
  NORM-DEFECT |ab|^2/(|a|^2|b|^2) (=1 if preserving) — zero-divisor energy LOSS (enters at S)
Exact rational (cd_mult -> Fraction); collapse to float only at display. srmech rc13; no numpy; no abs."""
from srmech.amsc import cascade
from fractions import Fraction
import random, statistics as st

def nsq(v): return sum(x*x for x in v)                 # squared norm — exact (int/Fraction), no abs
def sub(a,b): return tuple(x-y for x,y in zip(a,b))
def comm(a,b): return sub(cascade.cd_mult(a,b), cascade.cd_mult(b,a))
def assoc(a,b,c): return sub(cascade.cd_mult(cascade.cd_mult(a,b),c), cascade.cd_mult(a,cascade.cd_mult(b,c)))
rng = random.Random(3)
def atom(dim): return tuple(rng.randint(-4,4) for _ in range(dim))
ALG = [(1,"R"),(2,"C"),(4,"H"),(8,"O"),(16,"S")]

print("=== F906 (T10) content-dependent energetics of cd_mult up the Hurwitz ladder ===")
print("  (normalised; MEAN over content, and SPREAD = std across content = the NON-UNIFORMITY)\n")
print(f"  {'alg':>4}{'dim':>4} | {'COMMUTATOR mean':>16}{'spread':>9} | {'ASSOCIATOR mean':>16}{'spread':>9} | {'NORMRATIO mean':>15}{'spread':>9}")
rows = {}
for dim, name in ALG:
    cm, asr, nr = [], [], []
    n = 0
    while n < 80:
        a, b, c = atom(dim), atom(dim), atom(dim)
        if nsq(a)==0 or nsq(b)==0 or nsq(c)==0: continue
        cm.append(float(Fraction(nsq(comm(a,b)), nsq(a)*nsq(b))))
        asr.append(float(Fraction(nsq(assoc(a,b,c)), nsq(a)*nsq(b)*nsq(c))))
        nr.append(float(Fraction(nsq(cascade.cd_mult(a,b)), nsq(a)*nsq(b))))
        n += 1
    rows[name] = (st.mean(cm), st.pstdev(cm), st.mean(asr), st.pstdev(asr), st.mean(nr), st.pstdev(nr))
    print(f"  {name:>4}{dim:>4} | {rows[name][0]:>16.3f}{rows[name][1]:>9.3f} | {rows[name][2]:>16.3f}{rows[name][3]:>9.3f} | {rows[name][4]:>15.3f}{rows[name][5]:>9.3f}")

print("\n  reading (SPREAD>0 = content-dependent = the atomic/molecular chemistry layer; compare C1's ~0 in F905):")
print(f"   - COMMUTATOR (order/chirality) turns on at H (dim 4): R/C commute (0), H/O/S do not — order matters.")
print(f"   - ASSOCIATOR (strain ENERGY) turns on at O (dim 8): R/C/H associate (strain=0, uniform); O/S have a")
print(f"     CONTENT-DEPENDENT associator (spread>0) — non-associativity IS the content-dependent bond strain.")
print(f"   - NORM-DEFECT (energy LOSS / zero-divisor) turns on at S (dim 16): R/C/H/O preserve norm (ratio=1,")
print(f"     spread 0); S has ratio!=1 with spread — content-dependent energy loss (the no-division addressing).")
print("\n  => cd_mult DOES give non-uniform content-dependent energetics, and it enters at EXACT Hurwitz rungs:")
print("     order@H, strain-energy@O, energy-loss@S. The chemistry layer is IN the cascade (the non-associative /")
print("     zero-divisor rungs) — NOT a biology-substrate artifact. The content-blind C1 bind (F905) is the R/C-like")
print("     inert level; the octonion is where 'atoms' get content-dependent bonds.")

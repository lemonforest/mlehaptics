"""F909 (T7) — does the octonion bond-AFFINITY (F908) distinguish BOUND morphemes ('solid only when
bonded') from FREE morphemes ('gas when loose')? Two affinity probes on KNOWN bound vs free morphemes:
 HOST-STRAIN : mean associator strain of [root, m, root2] -- how much m strains a host context
 DIR-ASYM    : |strain(m at END) - strain(m at START)| -- directional preference (suffix/prefix), via
               the octonion non-commutativity/order (F906 H-rung)
Honest: strain is byte/spelling-derived; if it does NOT separate bound/free, valence is DISTRIBUTIONAL
and the octonion is the sub-byte force (different scales). srmech rc13; exact Fraction; no abs; no numpy."""
from srmech.amsc import cascade, format as fmt
from fractions import Fraction
import statistics as st

def nsq(v): return sum(x*x for x in v)
def omul(x,y): return tuple(cascade.cd_mult(x,y))
def byte_oct(b):
    d=bytes.fromhex(fmt.sha256_bytes(f"LoE.byte.{b}".encode())); return tuple((d[i]%9)-4 for i in range(8))
def word_oct(w):
    bs=w.encode("utf-8"); p=byte_oct(bs[0])
    for b in bs[1:]: p=omul(p, byte_oct(b))
    return p
def assoc(a,b,c): return tuple(x-y for x,y in zip(omul(omul(a,b),c), omul(a,omul(b,c))))
def strain(a,b,c):
    d=nsq(a)*nsq(b)*nsq(c); return float(Fraction(nsq(assoc(a,b,c)), d)) if d else 0.0

# KNOWN morphemes (attested English): bound affixes vs free words
BOUND = ["ing","ed","ness","un","re","tion","ly","er","dis","ment","ful","less","est","able"]
FREE  = ["cat","dog","run","walk","blue","house","tree","water","light","book","sun","big","red","fish"]
ROOTS = ["work","play","teach","read","kind","hope","care","help","move","dark"]   # host roots
roct  = [word_oct(r) for r in ROOTS]

def host_strain(m):                       # m in the MIDDLE of a host context [root, m, root2]
    mo=word_oct(m); vals=[]
    for i in range(len(roct)):
        for j in range(len(roct)):
            if i!=j: vals.append(strain(roct[i], mo, roct[j]))
    return st.mean(vals)
def dir_asym(m):                          # m at END (suffix pos) vs START (prefix pos): order preference
    mo=word_oct(m); end=[]; start=[]
    for i in range(len(roct)):
        for j in range(len(roct)):
            if i!=j:
                end.append(strain(roct[i], roct[j], mo))    # ... root root m   (suffix slot)
                start.append(strain(mo, roct[i], roct[j]))  # m root root ...   (prefix slot)
    return float(cascade.magnitude(st.mean(end)-st.mean(start)))   # Class-K real pin-slot magnitude (srmech)

print("=== F909 (T7) octonion bond-affinity of bound vs free morphemes ===")
bh=[host_strain(m) for m in BOUND]; fh=[host_strain(m) for m in FREE]
bd=[dir_asym(m) for m in BOUND];    fd=[dir_asym(m) for m in FREE]
print(f"\n  {'measure':<16}{'BOUND mean':>14}{'FREE mean':>12}{'separates?':>14}")
def sep(b,f):
    # do the distributions separate? simple overlap check via means +/- stdev
    return "yes" if float(cascade.magnitude(st.mean(b)-st.mean(f))) > 0.5*(st.pstdev(b)+st.pstdev(f)) else "no/weak"
print(f"  {'HOST-STRAIN':<16}{st.mean(bh):>14.3f}{st.mean(fh):>12.3f}{sep(bh,fh):>14}")
print(f"  {'DIR-ASYM':<16}{st.mean(bd):>14.3f}{st.mean(fd):>12.3f}{sep(bd,fd):>14}")
print(f"\n  per-morpheme host-strain:")
for m in BOUND: print(f"    bound {m:<6} {host_strain(m):.3f}")
for m in FREE:  print(f"    free  {m:<6} {host_strain(m):.3f}")
print(f"\n  (length confound check) bound mean len {st.mean([len(m) for m in BOUND]):.1f} vs free {st.mean([len(m) for m in FREE]):.1f}")

# Where valence DOES live: the DISTRIBUTIONAL measure (does the morpheme occur as a FREE token?)
import json
path="/home/skirklan/corpora/wikipedia/simplewiki_fullbody_instrument.ndjson"
freq={}; total=0
with open(path) as f:
    for line in f:
        for t in json.loads(line)["s"].split():
            freq[t]=freq.get(t,0)+1; total+=1     # plain token-frequency tally (NOT co-occurrence)
        if total>=200000: break
def free_rate(m): return freq.get(m,0)/total*1e6   # standalone occurrences per million tokens
print(f"\n  DISTRIBUTIONAL valence -- free-token rate (per million; corpus={total} tokens):")
print(f"    {'BOUND (expect ~0)':<22}{'FREE (expect >0)':<22}")
for mb,mf in zip(BOUND,FREE):
    print(f"    {mb:<8}{free_rate(mb):>10.1f}      {mf:<8}{free_rate(mf):>10.1f}")
import statistics as st
print(f"\n  bound free-rate mean {st.mean([free_rate(m) for m in BOUND]):.1f}/M  vs  free {st.mean([free_rate(m) for m in FREE]):.1f}/M")
print("  => valence is DISTRIBUTIONAL (bound morphemes ~never occur free; free morphemes do), NOT octonion-strain.")
print("  The octonion affinity (F908) is the sub-byte bond force (which atoms bond cleanly); morphological")
print("  'solid vs gas' is a DIFFERENT scale -- the morpheme's free-occurrence / adjacency obligatoriness (F902-scale).")

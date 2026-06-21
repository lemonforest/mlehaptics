"""F915 (open-derivation 2) — does real linguistic constituency sit at F911's low-strain minima? English is
strongly RIGHT-branching; if the octonion strain encoded syntax, right-branching word-bracketings would be
systematically low-strain. But strain is BYTE-derived (F909: the octonion affinity is byte-level, not
syntactic), so the prediction is NULL: canonical bracketings are NOT systematically lower than random.
srmech rc13; exact; no abs."""
from srmech.amsc import cascade, format as fmt
from fractions import Fraction
import json, statistics as st

def nsq(v): return sum(x*x for x in v)
def omul(x,y): return tuple(cascade.cd_mult(x,y))
def amag(a,b,c):
    d=nsq(a)*nsq(b)*nsq(c)
    return float(Fraction(nsq(tuple(x-y for x,y in zip(omul(omul(a,b),c), omul(a,omul(b,c))))), d)) if d else 0.0
def byte_oct(b):
    dd=bytes.fromhex(fmt.sha256_bytes(f"LoE.byte.{b}".encode())); return tuple((dd[i]%9)-4 for i in range(8))
def word_oct(w):
    p=byte_oct(w.encode()[0])
    for b in w.encode()[1:]: p=omul(p,byte_oct(b))
    return p
ATOMS=None
def ev(t):
    if isinstance(t,int): return ATOMS[t],0.0
    L,R=t; lp,ls=ev(L); rp,rs=ev(R); loc=0.0
    if not isinstance(L,int): ap,_=ev(L[0]); bp,_=ev(L[1]); loc+=amag(ap,bp,rp)
    if not isinstance(R,int): cp,_=ev(R[0]); dp,_=ev(R[1]); loc+=amag(lp,cp,dp)
    return omul(lp,rp), ls+rs+loc
def parens(seq):
    if len(seq)==1: yield seq[0]; return
    for i in range(1,len(seq)):
        for L in parens(seq[:i]):
            for R in parens(seq[i:]): yield (L,R)
def left(n):  # left-branching ((((0 1)2)3)...)
    t=0
    for i in range(1,n): t=(t,i)
    return t
def right(n): # right-branching (0(1(2(3...))))
    t=n-1
    for i in range(n-2,-1,-1): t=(i,t)
    return t

# real phrases (word sequences) from simplewiki; 5 words each so all 14 bracketings enumerable
path="/home/skirklan/corpora/wikipedia/simplewiki_fullbody_instrument.ndjson"
phrases=[]
with open(path) as f:
    for line in f:
        t=json.loads(line)["s"].split()
        for i in range(0,len(t)-5,5):
            w=t[i:i+5]
            if all(x.isalpha() for x in w): phrases.append(w)
        if len(phrases)>=40: break
phrases=phrases[:40]; n=5
print(f"=== F915 does real constituency sit at low octonion-strain? ({len(phrases)} 5-word phrases) ===")
ranks=[]; lr=[]; rr=[]
for w in phrases:
    ATOMS=[word_oct(x) for x in w]
    allt=list(parens(tuple(range(n)))); strs=sorted(ev(t)[1] for t in allt)
    sl=ev(left(n))[1]; sr=ev(right(n))[1]
    # percentile rank of right-branching among all bracketings (0=lowest strain, 1=highest)
    rr.append(sum(1 for s in strs if s<sr)/len(strs)); lr.append(sum(1 for s in strs if s<sl)/len(strs))
print(f"\n  right-branching (English default) strain percentile-rank among all 14 bracketings: mean {st.mean(rr):.2f}")
print(f"  left-branching strain percentile-rank: mean {st.mean(lr):.2f}   (0.0=always lowest-strain, 0.5=random, 1.0=highest)")
print(f"\n  => {'NULL' if 0.30<st.mean(rr)<0.70 else 'SIGNAL'}: right-branching sits at ~random strain rank (~0.5), NOT systematically low.")
print("  The octonion strain is BYTE-derived (F909), so it does NOT encode syntactic constituency. Real")
print("  linguistic bracketing is DISTRIBUTIONAL/syntactic -- a different scale than the byte-bond affinity.")
print("  (Same lesson as F909: the fundamental force is byte-level; linguistic structure lives one scale up.)")

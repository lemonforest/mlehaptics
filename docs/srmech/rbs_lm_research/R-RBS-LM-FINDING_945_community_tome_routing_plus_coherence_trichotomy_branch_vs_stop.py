"""F945 — community-tome routing for the GENERAL (branching) case + the coherence trichotomy. Route
relationships by source/community into bounded tomes (F778/F465) -> single-next margins stay high; and a
LOW collapse-margin now splits THREE ways: COHERENT (top1 high, margin high -> emit one), BRANCH (top1 AND
top2 above the noise floor, margin low -> legitimate multi-next, SAMPLE), STOP (top1 near floor -> noise,
honest-stop). Grounded: branch a->{b,c} reads b,c both 0.56 (floor 0.34) margin 0.00 = BRANCH; single-next
b/c/d read margin 0.74-1.0 = COHERENT. srmech rc58; real Klein-4; no numpy."""
from srmech.amsc import hdc
from srmech.rbs_lm import substrate as S
D=8192; cs=S.ContextSubstrate(D=D, hex_chars=16); bind=hdc.klein4_bind
def fl(q): return q.as_float() if hasattr(q,'as_float') else float(q)
vocab=['a','b','c','d','e','f','g','h','i','j']; vec={t: hdc.klein4_random(D, seed=2000+i) for i,t in enumerate(vocab)}
ROLE=hdc.klein4_random(D, seed=4242)
edges=[('a','b'),('a','c'),('b','d'),('c','d'),('d','e')]   # a BRANCHES to b,c ; merge at d ; d->e
src={}
for p,n in edges: src.setdefault(p,[]).append(bind(bind(vec[p],ROLE),vec[n]))
src={k: cs.bundle_odd(v) for k,v in src.items()}
def sims(M,x): return sorted(((fl(hdc.klein4_similarity(bind(M,bind(vec[x],ROLE)),vec[t])),t) for t in vocab), reverse=True)
FLOOR=0.34
def classify(s):
    top1=s[0][0]; m=top1-s[1][0]
    if top1<FLOOR: return 'STOP (incoherent/noise)'
    if s[1][0]>=FLOOR and m<0.12: return 'BRANCH -> sample {%s,%s}'%(s[0][1],s[1][1])
    return 'COHERENT -> %s'%s[0][1]
for x in ['a','b','c','d']:
    s=sims(src[x],x)
    print('recall %s : top %s  margin %.2f   %s'%(x,[(t,round(v,2)) for v,t in s[:3]],s[0][0]-s[1][0],classify(s)))

"""F977 — brain 'stop and think' recall as the multi-time read (user). Automatic recall = one strong cue
(k=1); fetching a faded/distant memory that 'requires stop and think' = assembling MULTIPLE cues and
superposing them (k>1, the F976 sqrt(k) altitude lift). Test the sharp case: at high load where the SINGLE
cue has LOST the target (not top1 = 'forgotten'), does MULTI-cue superposition RECOVER it (top1 = the
stop-and-think fetch)? Sparse Klein-4; no dense/numpy/abs."""
from srmech.amsc import hdc
from srmech.rbs_lm import substrate as S
D=8192; cs=S.ContextSubstrate(D=D, hex_chars=16); bind=hdc.klein4_bind
def fl(q): return q.as_float() if hasattr(q,'as_float') else float(q)
ROLE=hdc.klein4_random(D, seed=4242)
V=800
vec=[hdc.klein4_random(D, seed=6000+i) for i in range(V)]
Xi=0; ctx=[1,2,3,4,5]                       # X recurs after up to 5 cues (5 time points)
def recall(probe):
    s=sorted(((fl(hdc.klein4_similarity(probe,vec[j])),j) for j in range(V)), reverse=True)
    return s[0][1]==Xi, s[0][0]-s[1][0]
print('load  single-cue(k=1)   multi-cue k=3        multi-cue k=5     <- does stop-and-think recover the lost memory?')
for N in (150, 300, 500, 700):
    pairs=[bind(bind(vec[c],ROLE),vec[Xi]) for c in ctx]        # X's real recurrences
    for i in range(N): pairs.append(bind(bind(vec[6+(i%(V-7))],ROLE),vec[6+((i+1)%(V-7))]))
    M=cs.bundle_odd(pairs)
    s1,m1=recall(bind(M,bind(vec[ctx[0]],ROLE)))                                  # k=1 single cue
    s3,m3=recall(cs.bundle_odd([bind(M,bind(vec[c],ROLE)) for c in ctx[:3]]))     # k=3
    s5,m5=recall(cs.bundle_odd([bind(M,bind(vec[c],ROLE)) for c in ctx[:5]]))     # k=5
    print('N=%3d  %s (%.3f)      %s (%.3f)      %s (%.3f)'%(N,
        'FOUND' if s1 else 'lost ', m1, 'FOUND' if s3 else 'lost ', m3, 'FOUND' if s5 else 'lost ', m5))
print('=> if single-cue LOSES but multi-cue FINDS: stop-and-think (assemble more cues) recovers a faded memory')

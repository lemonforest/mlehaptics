"""F941 — minimal full-beat recall step (the build). Half-beat (query with the context ALONE = one now)
STALLS (a->a->a); full-beat (bind context WITH the next-relation ROLE = two nows -> composite query)
ADVANCES (a->b->c->d). The cleanup/argmax that resolves the composite to a definite token IS the chirality
collapse (F942). srmech rc58; real Klein-4 (bind/bundle/similarity); no numpy."""
from srmech.amsc import hdc
from srmech.rbs_lm import substrate as S
D=8192; cs=S.ContextSubstrate(D=D, hex_chars=16); bind=hdc.klein4_bind
def fl(q): return q.as_float() if hasattr(q,'as_float') else float(q)
vocab=['a','b','c','d','e','f','g','h']
vec={t: hdc.klein4_random(D, seed=1000+i) for i,t in enumerate(vocab)}
ROLE=hdc.klein4_random(D, seed=4242)
chain=['a','b','c','d','e']; edges=list(zip(chain,chain[1:]))
M=cs.bundle_odd([ bind(bind(vec[p],ROLE),vec[n]) for p,n in edges ])
def cleanup(v): return max(vocab, key=lambda t: fl(hdc.klein4_similarity(v,vec[t])))
def recall_full(x): return cleanup(bind(M, bind(vec[x],ROLE)))   # two nows -> composite
def recall_half(x): return cleanup(bind(M, vec[x]))               # one now
def walk(rec,start,n=5):
    out=[start]; cur=start
    for _ in range(n): cur=rec(cur); out.append(cur)
    return out
print('chain     :', '->'.join(chain))
print('FULL-beat :', '->'.join(walk(recall_full,'a')))
print('HALF-beat :', '->'.join(walk(recall_half,'a')))

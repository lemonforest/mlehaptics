"""F969 — build+run the SHADOW-FORCED encode. Test: does an asymmetric shadow-phase forcing on sequence
position make a SINK (phrase end, no stored next) STOP where the symmetric baseline WANDERS? The forcing =
chirality-flip the position key by the odd shadow-theta sign (F968), so the sequence carries an asymmetric
(odd) mark -> the boundary (where the shadow completes) is detectable as a clean STOP. Metric: margin gap =
(mean margin at real-next nodes) - (margin at the sink). Bigger gap = the phrase stops. srmech rc97; sparse
Klein-4; no dense; no numpy; no abs."""
from srmech.amsc import hdc, unary_theta as U
from srmech.rbs_lm import substrate as S
def fl(q): return q.as_float() if hasattr(q,'as_float') else float(q)
D=8192; cs=S.ContextSubstrate(D=D, hex_chars=16); bind=hdc.klein4_bind
# shadow odd sign per sequence position (F968)
tbl=[0,1,0,0,0,-1,0,-1,0,0,0,1]
qs=U.unary_theta(U.Character(12,tbl),1,1,24,8).q_series(400)
sh=[(1 if c>0 else -1) for c in qs if c!=0]
sh=(sh*8)[:32]                                    # tile for enough positions
vocab=['a','b','c','d','e','f','g','h']; vec={t: hdc.klein4_random(D,seed=1000+i) for i,t in enumerate(vocab)}
ROLE=hdc.klein4_random(D,seed=4242); chain=['a','b','c','d','e']  # sink = e (no stored next)
def poskey(p, forced):
    k=cs.pos_key(p)
    return hdc.klein4_chirality_flip_gamma5(k) if (forced and sh[p]<0) else k
def ctx_enc(seq, forced):                          # position-in-sequence shadow-phased context
    return cs.bundle_odd([bind(poskey(p,forced), vec[t]) for p,t in enumerate(seq)])
def build(forced):                                 # store forward pairs: (prefix-so-far) -> next
    pairs=[bind(ctx_enc(chain[:i+1], forced), vec[chain[i+1]]) for i in range(len(chain)-1)]
    return cs.bundle_odd(pairs)
def margin(M, seq, forced):
    probe=bind(M, ctx_enc(seq, forced))
    s=sorted((fl(hdc.klein4_similarity(probe,vec[t])) for t in vocab), reverse=True)
    return s[0]-s[1]
for forced in (False, True):
    M=build(forced)
    reals=[margin(M, chain[:i+1], forced) for i in range(len(chain)-1)]  # a,ab,abc,abcd -> have a next
    sink=margin(M, chain, forced)                                        # abcde -> sink (no next)
    mr=sum(reals)/len(reals)
    print('%-14s real-next mean margin %.3f  |  SINK margin %.3f  |  gap %.3f'%(
        ('SHADOW-FORCED' if forced else 'symmetric'), mr, sink, mr-sink))
print('=> bigger gap (real advances, sink stops) = the shadow forcing makes the phrase STOP at the boundary')

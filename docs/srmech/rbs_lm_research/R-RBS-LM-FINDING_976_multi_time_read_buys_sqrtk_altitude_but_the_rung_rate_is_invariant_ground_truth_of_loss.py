"""F976 — real-corpus recession (one rung or two?) + the MULTI-TIME read (user): address a target from
several points in time at once, recovering the fundamental memoryless-geometry a single-time read loses
('what is not preserved is lost to time'; the simulation is not limited to one time perspective).
A target X recurs after 3 distinct contexts (3 time points). Load = N random pairs. Compare, vs N:
  single-time margin for X (queried from ONE of its contexts)  vs  multi-time margin (superpose all 3).
Sparse Klein-4; no dense/numpy/abs."""
from fractions import Fraction as Fr
from srmech.amsc import hdc
from srmech.rbs_lm import substrate as S
import json
D=8192; cs=S.ContextSubstrate(D=D, hex_chars=16); bind=hdc.klein4_bind
def fl(q): return q.as_float() if hasattr(q,'as_float') else float(q)
ROLE=hdc.klein4_random(D, seed=4242)
# real content-token vocab (drop function words), for realistic atoms
stop=set('the of in a is and to as for on it was were are that with by an at from or be'.split())
toks=[]
with open('/home/skirklan/corpora/wikipedia/simplewiki_fullbody_instrument.ndjson') as f:
    for line in f:
        toks.extend(json.loads(line)['s'].split())
        if len(toks)>=4000: break
content=[t for t in toks[:4000] if t not in stop]
uniq=list(dict.fromkeys(content))
vec={t: hdc.klein4_random(D, seed=hash(t)%90000+7) for t in uniq}
X=uniq[0]; ctxs=[uniq[1],uniq[2],uniq[3]]          # X recurs after 3 distinct contexts (3 time points)
fillers=uniq[4:]
def margin_for(probe):
    s=sorted(((fl(hdc.klein4_similarity(probe,vec[t])),t) for t in uniq[:80]), reverse=True)
    top=s[0][0]; m=top-s[1][0]; is_X=(s[0][1]==X)
    return m, is_X
def octaves(r):
    r=Fr(r).limit_denominator(10**9) if r>0 else Fr(1,10**9); n=0; x=Fr(1)
    while x>r and n<300: x=x/2; n+=1
    return n
print('real-corpus recession + multi-time read (target X recurs after 3 contexts):')
print(' N     single-margin  X? | multi-margin  X? | single-oct  multi-oct')
for N in (8,16,32,64,128,256):
    pairs=[bind(bind(vec[c],ROLE),vec[X]) for c in ctxs]            # the 3 real recurrences of X
    for i in range(max(0,N-3)): pairs.append(bind(bind(vec[fillers[i%len(fillers)]],ROLE),vec[fillers[(i+1)%len(fillers)]]))
    M=cs.bundle_odd(pairs)
    sm,sx=margin_for(bind(M,bind(vec[ctxs[0]],ROLE)))               # SINGLE time point
    multiprobe=cs.bundle_odd([bind(M,bind(vec[c],ROLE)) for c in ctxs])  # MULTI time points superposed
    mm,mx=margin_for(multiprobe)
    print(' %3d   %.4f  %s | %.4f  %s | %d  %d'%(N, sm,'X' if sx else '.', mm,'X' if mx else '.', octaves(sm),octaves(mm)))
print('=> if multi-time margin recedes SLOWER / keeps X where single loses it: the multi-time read recovers the')
print('   fundamental memoryless-geometry (ground truth) that a single time perspective loses to time.')

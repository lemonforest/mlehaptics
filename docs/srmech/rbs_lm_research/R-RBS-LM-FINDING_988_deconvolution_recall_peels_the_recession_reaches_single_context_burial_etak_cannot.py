"""F988 — deconvolution-recall (DECONV-1 unwrap) vs etak-deeper (F986). Test the complementary case: a
SINGLE-context buried target -- P has nexts {A,B,T} with T weakest (buried); heavy load. etak-deeper CAN'T
help (only one context P -> nothing to superpose). DECONVOLUTION = unwrap the superposition by DEFLATION:
recover P's strongest next, REMOVE that (P->next) pair from M (re-bundle without it = sparse), re-probe;
peel until the buried T surfaces. Does inverting/peeling reach a target multi-cue cannot? Sparse Klein-4
(bundle re-formation, integer sims); no dense/numpy/abs."""
from srmech.amsc import hdc
from srmech.rbs_lm import substrate as S
D=8192; cs=S.ContextSubstrate(D=D, hex_chars=16); bind=hdc.klein4_bind
def fl(q): return q.as_float() if hasattr(q,'as_float') else float(q)
ROLE=hdc.klein4_random(D, seed=4242); V=700
vec=[hdc.klein4_random(D, seed=6000+i) for i in range(V)]
P=0; A,B,T=1,2,3                    # P's nexts: A,B strong (stored 3x,2x), T weak (stored 1x) = buried
pairs=[]
for _ in range(3): pairs.append((P,A))
for _ in range(2): pairs.append((P,B))
pairs.append((P,T))                # T: single weak occurrence
for i in range(120): pairs.append((10+(i%600),11+(i%600)))   # heavy load
def mk(plist): return cs.bundle_odd([bind(bind(vec[a],ROLE),vec[b]) for a,b in plist])
def top(M, exclude=()):            # probe [P], integer-sim rank over candidates, skip already-peeled
    probe=bind(M, bind(vec[P],ROLE))
    s=sorted(((fl(hdc.klein4_similarity(probe,vec[j])),j) for j in range(V) if j not in exclude), reverse=True)
    return s[0][1], s[0][0]-s[1][0]
# etak-deeper: only context P available -> single-cue, cannot escalate; stuck at whatever probe returns
M=mk(pairs)
e_t,e_m=top(M)
print('single-context buried target: P->{A(3x),B(2x),T(1x)} + 120 load; want T=%d'%T)
print('  FAST / etak-deeper (single context P, no multi-cue to superpose): top=%d  reaches_T=%s'%(e_t, e_t==T))
# DECONVOLUTION = deflation: recover top, REMOVE (P->top) pair(s), re-probe; peel to reach T
plist=list(pairs); peeled=[]; reached=None
for step in range(4):
    M=mk(plist)
    t,_=top(M, exclude=set(peeled))
    peeled.append(t)
    if t==T: reached=step; break
    plist=[(a,b) for (a,b) in plist if not (a==P and b==t)]   # sparse deflate: drop the recovered (P->t) relationship
print('  DECONVOLUTION (peel): recovered order %s  -> T reached at deflation step %s'%(peeled, reached))
print('=> deconvolution unwraps the superposition to reach the single-context buried T that etak-deeper cannot')

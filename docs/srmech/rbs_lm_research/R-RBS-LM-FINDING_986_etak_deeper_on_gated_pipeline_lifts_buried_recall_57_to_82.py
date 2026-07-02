"""F986 — add etak-deeper (F978-F981) to the GATED pipeline (F985) for BURIED targets. On doc-freq-gated
community-tomes: FAST-gated single-cue recall; for content targets with multiple in-tome contexts, if FAST
misses (buried), ESCALATE multi-cue (superpose the target's in-tome contexts, gated emission). Measure
FAST-gated vs FAST-gated+etak-deeper accuracy on multi-context buried content targets. srmech rc97; sparse."""
import json, random
from srmech.amsc import hdc, laplacian as Lp
from srmech.rbs_lm import substrate as S
D=8192; cs=S.ContextSubstrate(D=D, hex_chars=16); bind=hdc.klein4_bind
def fl(q): return q.as_float() if hasattr(q,'as_float') else float(q)
ROLE=hdc.klein4_random(D, seed=4242)
arts=[]
with open('/home/skirklan/corpora/wikipedia/simplewiki_fullbody_instrument.ndjson') as f:
    for line in f:
        arts.append(json.loads(line)['s'].split())
        if len(arts)>=40: break
NDOC=len(arts); docf={}
for a in arts:
    for w in set(a): docf[w]=docf.get(w,0)+1
FUNC=int(NDOC*0.6)
def gate(t): d=docf.get(t,1); return 1.0 if d<FUNC else FUNC/d
toks=[w for a in arts[:6] for w in a]; uniq=list(dict.fromkeys(toks)); idx={w:i for i,w in enumerate(uniq)}; n=len(uniq)
vec={w: hdc.klein4_random(D, seed=(hash(w)%80000)+11) for w in uniq}
pairs=[(a,b) for a,b in zip(toks,toks[1:]) if a!=b]
und={}
for a,b in pairs:
    e=(min(idx[a],idx[b]),max(idx[a],idx[b])); und[e]=und.get(e,0)+1
edges=list(und); wg=[float(und[e])*gate(uniq[e[0]])*gate(uniq[e[1]]) for e in edges]
res=Lp.recursive_cut(n, edges, wg, max_tome=90); tmap={}
for ti,t in enumerate(res['tomes']):
    for i in t: tmap[uniq[i]]=ti
# in-tome prev-contexts of each target (same tome), content targets with >=3 contexts = the buried multi-cue set
inctx={}
for a,b in pairs:
    if tmap.get(a)==tmap.get(b) and docf.get(b,1)<FUNC:
        inctx.setdefault(b,{}).setdefault(tmap[b],[]).append(a)
targets=[(b,tid,cx) for b,d in inctx.items() for tid,cx in d.items() if len(set(cx))>=3]
def tome_M(tid):
    ps=[bind(bind(vec[a],ROLE),vec[b]) for a,b in pairs if tmap.get(a)==tid and tmap.get(b)==tid]
    return cs.bundle_odd(ps) if ps else None
def read(M, ctxs, cnt):
    probe=cs.bundle_odd([bind(M,bind(vec[c],ROLE)) for c in ctxs]) if len(ctxs)>1 else bind(M,bind(vec[ctxs[0]],ROLE))
    return max(cnt, key=lambda t: fl(hdc.klein4_similarity(probe,vec[t]))*gate(t))
gr=random.Random(3); samp=gr.sample(targets, min(40,len(targets)))
fast_ok=deep_ok=recovered=0
for T,tid,cx in samp:
    M=tome_M(tid); cnt=[w for w in uniq if tmap.get(w)==tid]; ucx=list(dict.fromkeys(cx))
    f = (read(M,[ucx[0]],cnt)==T)                                  # FAST-gated single cue
    d = f or any(read(M,ucx[:k],cnt)==T for k in (2,3,5) if k<=len(ucx))  # + etak-deeper multi-cue
    fast_ok+=f; deep_ok+=d; recovered += (d and not f)
N=len(samp)
print('etak-deeper on the GATED pipeline (%d gated tomes; %d multi-context buried content targets):'%(res['n_tomes'],N))
print('  FAST-gated (single cue)          : %.0f%% (%d/%d)'%(fast_ok/N*100,fast_ok,N))
print('  FAST-gated + ETAK-DEEPER (multi) : %.0f%% (%d/%d)'%(deep_ok/N*100,deep_ok,N))
print('  buried targets RECOVERED by etak-deeper that FAST missed: %d'%recovered)

"""F993 — Klein-4 CHIRALITY FRAMES as perspectives (#1) + SOFT-consensus (#2) + ASYMMETRIC mock-theta beat
weighting (the ellipse/Ramanujan asymmetric wave) TRANSLATED from the theta ladder into the chirality ladder
(multiple math ladders + translation, user). The 4 frames = {identity, gamma5-flip, iomega7-flip, CPT} read
of the SAME preserved M (the wall is artificial, F992). Reconcile SOFT (sum per-frame evidence). Weight the
4 frames uniformly vs by the asymmetric mock-theta coefficients. Compare to single-frame. Same F992 test set.
Sparse Klein-4; no dense/numpy/abs."""
import json, random
from srmech.amsc import hdc, laplacian as Lp, harmonic_maass as hm, cascade
from srmech.rbs_lm import substrate as S
D=8192; cs=S.ContextSubstrate(D=D, hex_chars=16); bind=hdc.klein4_bind
def fl(q): return q.as_float() if hasattr(q,'as_float') else float(q)
ROLE=hdc.klein4_random(D, seed=4242)
FR=[lambda v:v, hdc.klein4_chirality_flip_gamma5, hdc.klein4_chirality_flip_omega7, hdc.klein4_cpt_mirror]  # 4 chiral frames

# ---- asymmetric weights: TRANSLATE the theta ladder (mock-theta eulerian_f) -> 4 chirality-frame weights ----
def theta_weights():
    try:
        mq=hm.MockQSeries.eulerian_f(); qs=mq.q_series(8)   # q_series(N): truncation depth
        coeffs=[]
        for item in qs:
            try:
                raw=item[1] if isinstance(item,(tuple,list)) else item
                coeffs.append(fl(cascade.magnitude(fl(raw))))   # srmech-allow: cascade.magnitude IS the Class-K pin-slot op (not abs)
            except Exception: pass
        coeffs=[c for c in coeffs if c>0][:4]
        while len(coeffs)<4: coeffs.append(coeffs[-1] if coeffs else 1.0)
        s=sum(coeffs) or 1.0; return [c/s for c in coeffs]
    except Exception as e:
        return None
TW=theta_weights()
print('asymmetric mock-theta frame weights (theta ladder -> chirality ladder):', [round(w,3) for w in TW] if TW else 'FALLBACK-uniform', flush=True)
if TW is None: TW=[0.25]*4

# ---- F992 test set: gated tomes, multi-context targets ----
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
gv={w: hdc.klein4_random(D, seed=(hash(w)%80000)+11) for w in uniq}
pairs=[(a,b) for a,b in zip(toks,toks[1:]) if a!=b]
und={}
for a,b in pairs:
    e=(min(idx[a],idx[b]),max(idx[a],idx[b])); und[e]=und.get(e,0)+1
edges=list(und); wg=[float(und[e])*gate(uniq[e[0]])*gate(uniq[e[1]]) for e in edges]
res=Lp.recursive_cut(n, edges, wg, max_tome=90); tmap={}
for ti,t in enumerate(res['tomes']):
    for i in t: tmap[uniq[i]]=ti
inctx={}
for a,b in pairs:
    if tmap.get(a)==tmap.get(b) and docf.get(b,1)<FUNC:
        inctx.setdefault((b,tmap[b]),[]).append(a)
targets=[(b,tid,list(dict.fromkeys(cx))) for (b,tid),cx in inctx.items() if len(set(cx))>=3]
def M_of(tid):
    ps=[bind(bind(gv[a],ROLE),gv[b]) for a,b in pairs if tmap.get(a)==tid and tmap.get(b)==tid]
    return cs.bundle_odd(ps) if ps else None
def single(M,c,cnt):                                 # identity frame only (F992 baseline)
    probe=bind(M,bind(gv[c],ROLE)); return max(cnt,key=lambda t: fl(hdc.klein4_similarity(probe,gv[t]))*gate(t))
def chiral(M,c,cnt,W):                               # 4 chirality-frame SOFT consensus (sum weighted evidence)
    probe=bind(M,bind(gv[c],ROLE)); views=[fr(probe) for fr in FR]
    def sc(t):
        return gate(t)*sum(W[f]*fl(hdc.klein4_similarity(views[f],gv[t])) for f in range(4))
    return max(cnt,key=sc)
gr=random.Random(5); samp=gr.sample(targets, min(45,len(targets)))
s1=su=sa=0
for T,tid,cx in samp:
    M=M_of(tid); cnt=[w for w in uniq if tmap.get(w)==tid]; c=cx[0]
    s1+=(single(M,c,cnt)==T)
    su+=(chiral(M,c,cnt,[0.25]*4)==T)
    sa+=(chiral(M,c,cnt,TW)==T)
N=len(samp)
print("\nKlein-4 CHIRALITY FRAMES as perspectives (%d targets; same preserved M):"%N, flush=True)
print("  single frame (identity, F992 baseline)      : %.0f%%"%(s1/N*100), flush=True)
print("  4-frame UNIFORM soft-consensus              : %.0f%%"%(su/N*100), flush=True)
print("  4-frame ASYMMETRIC (mock-theta) soft-consensus: %.0f%%"%(sa/N*100), flush=True)

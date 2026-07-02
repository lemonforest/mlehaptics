"""F998d — the PROPOSE->RESOLVE pipeline (F998c architecture, end-to-end). PROPOSE: the sparse Class-M bundle
gives the calibrated distribution (top-5, 92% coverage). RESOLVE: the bounded high-band resonant kernel
re-ranks WITHIN the proposed top-K to the sharp top-1 (its strength). Measure end-to-end top-1 vs bundle-alone
and resonant-alone -- does using each representation for what it's best at beat both? Sparse Klein-4 storage;
bounded Class-L kernel on a small tome; numpy-free bit-exact Jacobi; no abs."""
import json
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
toks=[w for a in arts[:6] for w in a]; uniq=list(dict.fromkeys(toks)); gidx={w:i for i,w in enumerate(uniq)}; NN=len(uniq)
gv={w: hdc.klein4_random(D, seed=(hash(w)%80000)+11) for w in uniq}
pairs=[(a,b) for a,b in zip(toks,toks[1:]) if a!=b]
und={}
for a,b in pairs:
    e=(min(gidx[a],gidx[b]),max(gidx[a],gidx[b])); und[e]=und.get(e,0)+1
edges=list(und); wg=[float(und[e])*gate(uniq[e[0]])*gate(uniq[e[1]]) for e in edges]
res=Lp.recursive_cut(NN, edges, wg, max_tome=80); tmap={}
for ti,t in enumerate(res['tomes']):
    for i in t: tmap[uniq[i]]=ti
_tsz={}
for _v in tmap.values(): _tsz[_v]=_tsz.get(_v,0)+1
tid=max(_tsz, key=_tsz.get)
nodes=[w for w in uniq if tmap[w]==tid]; n=len(nodes); loc={w:i for i,w in enumerate(nodes)}
dcnt={}
for a,b in pairs:
    if tmap.get(a)==tid and tmap.get(b)==tid: dcnt[(loc[a],loc[b])]=dcnt.get((loc[a],loc[b]),0)+1
dedges=list(dcnt); dw=[float(dcnt[e]) for e in dedges]
test=[(a,b) for a,b in pairs if tmap.get(a)==tid and tmap.get(b)==tid and docf.get(b,1)<FUNC]
test=list(dict.fromkeys(test))[:60]
M=cs.bundle_odd([bind(bind(gv[nodes[u]],ROLE), gv[nodes[v]]) for (u,v) in dedges])
Lq=Lp.magnetic_laplacian(n, dedges, dw, q=0.25); evals,evecs=Lp.hermitian_eigendecompose(Lq)
lam=[float(x) for x in evals]; V=[[evecs[i][k] for k in range(n)] for i in range(n)]; HI=range(n-24,n)
def rank_bundle(c):
    probe=bind(M,bind(gv[c],ROLE))
    return [t for _,t in sorted(((fl(hdc.klein4_similarity(probe,gv[t]))*gate(t),t) for t in nodes),reverse=True)]
def res_score(c,b):
    ci,bi=loc[c],loc[b]; s=0.0
    for k in HI: s+=lam[k]*(V[ci][k]*V[bi][k].conjugate()).imag
    return -s*gate(b)
def bundle_top1(c): return rank_bundle(c)[0]
def resonant_top1(c): return max(nodes, key=lambda t: res_score(c,t))
def propose_resolve(c, K=5):
    cand=rank_bundle(c)[:K]                       # PROPOSE (sparse bundle, ~92% coverage)
    return max(cand, key=lambda t: res_score(c,t)) # RESOLVE (resonant re-rank within the proposed set)
N=len(test)
ab=sum(bundle_top1(a)==b for a,b in test)/N
ar=sum(resonant_top1(a)==b for a,b in test)/N
apr=sum(propose_resolve(a)==b for a,b in test)/N
apr3=sum(propose_resolve(a,3)==b for a,b in test)/N
print("PROPOSE->RESOLVE pipeline (n=%d tome, %d content test edges):"%(n,N), flush=True)
print("  bundle-alone       top-1 : %2.0f%%"%(ab*100), flush=True)
print("  resonant-alone     top-1 : %2.0f%%"%(ar*100), flush=True)
print("  PROPOSE(5)->RESOLVE top-1 : %2.0f%%"%(apr*100), flush=True)
print("  PROPOSE(3)->RESOLVE top-1 : %2.0f%%"%(apr3*100), flush=True)
print("=> if propose->resolve > both alone, each representation used for its strength (sparse=coverage, resonant=sharp).", flush=True)

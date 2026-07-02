"""F998c — DISTRIBUTIONAL high-band read to lift F998b's 53% top-1 ceiling. The 53% is argmax-strongest-out-edge;
but c has a DISTRIBUTION of valid nexts and the true b is one of them (not always rank-1). Measure top-K
(K=1/3/5) for the bounded high-band resonant kernel vs the Class-M bundle vs full -- does the resonant store's
DISTRIBUTION recover the target (top-3/5 >> top-1)? + a normalized out-flow distribution read. Sparse Klein-4
storage; bounded Class-L kernel on a small tome; numpy-free bit-exact Jacobi; no abs."""
import json
from srmech.amsc import hdc, laplacian as Lp, cascade
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
lam=[float(x) for x in evals]; V=[[evecs[i][k] for k in range(n)] for i in range(n)]
HI=range(n-24,n)                                   # bounded high band (F998b: K=24 ~ full)
def rank_bundle(c):
    probe=bind(M,bind(gv[c],ROLE))
    return [t for _,t in sorted(((fl(hdc.klein4_similarity(probe,gv[t]))*gate(t),t) for t in nodes),reverse=True)]
def rank_high(c):                                  # resonant high-band out-flow, ranked (the distribution over nexts)
    ci=loc[c]
    def sc(bi):
        s=0.0
        for k in HI: s+=lam[k]*(V[ci][k]*V[bi][k].conjugate()).imag
        return -s*gate(nodes[bi])
    return [nodes[bi] for bi in sorted(range(n), key=sc, reverse=True)]
def topk(rankfn, K): return sum((b in rankfn(a)[:K]) for a,b in test)/len(test)
print("DISTRIBUTIONAL read -- top-K on the largest tome (n=%d, %d content test edges):"%(n,len(test)), flush=True)
print("             top-1   top-3   top-5", flush=True)
print("  Class-M bundle        : %2.0f%%    %2.0f%%    %2.0f%%"%(topk(rank_bundle,1)*100, topk(rank_bundle,3)*100, topk(rank_bundle,5)*100), flush=True)
print("  RESONANT high-band(24): %2.0f%%    %2.0f%%    %2.0f%%"%(topk(rank_high,1)*100, topk(rank_high,3)*100, topk(rank_high,5)*100), flush=True)
print("=> if resonant top-3/5 >> top-1, the store's DISTRIBUTION recovers the target -- the argmax-top-1 (53%,", flush=True)
print("   F998b) undersells it; a distributional read (rank/sample the out-flow) is the honest recall measure.", flush=True)

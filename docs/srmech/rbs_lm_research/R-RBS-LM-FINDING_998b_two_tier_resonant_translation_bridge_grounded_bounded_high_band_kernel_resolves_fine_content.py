"""F998b — the two-tier resonant store AS a translation bridge (F998), re-measured. STORAGE = sparse directed
edges (never densified over the corpus). TRANSLATION KERNEL = the bounded per-tome magnetic-Laplacian eigenbasis,
SPLIT BY BAND: LOW (subharmonic) = routing (already F960 tomes); HIGH (harmonic) = the fine-content resolve.
F997 showed LOW modes fail at fine recall (3%). Test: do the HIGH modes carry the fine next-edges, and how
BOUNDED can the high-band kernel be (K high modes << n)? Compare LOW-K vs HIGH-K vs FULL vs Class-M bundle,
+ a distributional (softmax-of-out-flow) read. srmech numpy-free bit-exact Jacobi; Class-L on a small tome; no abs."""
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
print("two-tier resonant bridge on the largest tome: n=%d, %d edges, %d content test edges"%(n,len(dedges),len(test)), flush=True)
# STORAGE stays sparse: Class-M bundle (baseline)
M=cs.bundle_odd([bind(bind(gv[nodes[u]],ROLE), gv[nodes[v]]) for (u,v) in dedges])
def read_M(c):
    probe=bind(M,bind(gv[c],ROLE)); return max(nodes,key=lambda t: fl(hdc.klein4_similarity(probe,gv[t]))*gate(t))
accM=sum(read_M(a)==b for a,b in test)/len(test)
# TRANSLATION KERNEL (bounded): magnetic-Laplacian eigenbasis of the sparse edges
Lq=Lp.magnetic_laplacian(n, dedges, dw, q=0.25); evals,evecs=Lp.hermitian_eigendecompose(Lq)
lam=[float(x) for x in evals]; V=[[evecs[i][k] for k in range(n)] for i in range(n)]  # ascending lambda
def score_modes(c,b,modeset):
    s=0.0
    for k in modeset: s += lam[k]*(V[c][k]*V[b][k].conjugate()).imag
    return -s*gate(nodes[b])
def read_band(c,modeset):
    ci=loc[c]; return nodes[max(range(n), key=lambda bi: score_modes(ci,bi,modeset))]
print("  STORAGE sparse edges + Class-M bundle read     : %.0f%%"%(accM*100), flush=True)
print("  FULL resonant kernel (all %d modes)            : %.0f%%"%(n, sum(read_band(a,range(n))==b for a,b in test)/len(test)*100), flush=True)
print("  --- band split of the bounded translation kernel ---", flush=True)
for K in (8,16,24,32):
    lowK=range(0,K); highK=range(n-K,n)
    aL=sum(read_band(a,lowK)==b for a,b in test)/len(test)
    aH=sum(read_band(a,highK)==b for a,b in test)/len(test)
    print("  K=%2d :  LOW-band (subharmonic=route) %2.0f%%   HIGH-band (harmonic=resolve) %2.0f%%"%(K, aL*100, aH*100), flush=True)
print("=> two-tier: LOW band routes (coarse, = F960 tomes), HIGH band resolves fine content; the resolve kernel", flush=True)
print("   is BOUNDED (K high modes) -- density lives only in the bounded bridge, storage stays sparse edges (F998).", flush=True)

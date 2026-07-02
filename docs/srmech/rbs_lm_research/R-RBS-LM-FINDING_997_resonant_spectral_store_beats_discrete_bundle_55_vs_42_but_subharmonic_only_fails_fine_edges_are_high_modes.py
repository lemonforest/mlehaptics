"""F997 — store the RBS-SNN in the RESONANT CONTINUOUS SHAPE and re-measure (F996's build). Knowledge = the
directed magnetic-Laplacian LOW eigenmodes (the resonant continuous field = the SUBHARMONIC modes, Class-L on
a SMALL bounded tome = the sanctioned spectral op). Recall = CRANK the low-rank reconstruction (the bit-exact
argmax excites the field, reads which mode/next). Compare to the Class-M discrete HDC bundle we used all arc.
Measure recall + storage. srmech numpy-free Jacobi (bit-exact); no numpy/abs; Class-L on a small graph = sparse-ok."""
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
toks=[w for a in arts[:6] for w in a]; uniq=list(dict.fromkeys(toks)); gidx={w:i for i,w in enumerate(uniq)}; N=len(uniq)
gv={w: hdc.klein4_random(D, seed=(hash(w)%80000)+11) for w in uniq}
pairs=[(a,b) for a,b in zip(toks,toks[1:]) if a!=b]
und={}
for a,b in pairs:
    e=(min(gidx[a],gidx[b]),max(gidx[a],gidx[b])); und[e]=und.get(e,0)+1
edges=list(und); wg=[float(und[e])*gate(uniq[e[0]])*gate(uniq[e[1]]) for e in edges]
res=Lp.recursive_cut(N, edges, wg, max_tome=80); tmap={}
for ti,t in enumerate(res['tomes']):
    for i in t: tmap[uniq[i]]=ti
# pick the LARGEST tome (most nodes) for a meaningful bounded spectral store
_tsz={}                                          # largest-tome pick (tome-size tally, NOT a co-occurrence store)
for _v in tmap.values(): _tsz[_v]=_tsz.get(_v,0)+1
tid=max(_tsz, key=_tsz.get)
nodes=[w for w in uniq if tmap[w]==tid]; n=len(nodes); loc={w:i for i,w in enumerate(nodes)}
# directed co-occurrence edges WITHIN the tome (c->b counts)
dcnt={}
for a,b in pairs:
    if tmap.get(a)==tid and tmap.get(b)==tid: dcnt[(loc[a],loc[b])]=dcnt.get((loc[a],loc[b]),0)+1
dedges=list(dcnt); dw=[float(dcnt[e]) for e in dedges]
# test set: directed content edges c->b (b content = low doc-freq), the recall targets
test=[(a,b) for a,b in pairs if tmap.get(a)==tid and tmap.get(b)==tid and docf.get(b,1)<FUNC]
test=list(dict.fromkeys(test))[:60]
print("resonant store on the LARGEST tome: n=%d nodes, %d directed edges, %d content test edges"%(n,len(dedges),len(test)), flush=True)
# ---- Class-M discrete bundle (baseline, what we did all arc) ----
M=cs.bundle_odd([bind(bind(gv[nodes[u]],ROLE), gv[nodes[v]]) for (u,v) in dedges])
def read_M(c):
    probe=bind(M,bind(gv[c],ROLE)); return max(nodes,key=lambda t: fl(hdc.klein4_similarity(probe,gv[t]))*gate(t))
accM=sum(read_M(a)==b for a,b in test)/len(test)
# ---- Class-L RESONANT store: magnetic-Laplacian low modes; recall by low-rank reconstruction ----
Lq=Lp.magnetic_laplacian(n, dedges, dw, q=0.25)
evals, evecs = Lp.hermitian_eigendecompose(Lq)     # ascending eigenvalues (low = subharmonic modes)
lam=[float(x) for x in evals]
V=[[evecs[i][k] for k in range(n)] for i in range(n)]  # V[node][mode] complex (numpy-free carrier read)
def recon_score(c,b,K):                            # -Im of the K-low-mode reconstruction of L[c][b] = the c->b out-flow
    s=0.0
    for k in range(K): s += lam[k]*(V[c][k]*V[b][k].conjugate()).imag
    return -s*gate(nodes[b])                         # crank: bit-exact argmax reads the resonant field
def read_L(c,K):
    ci=loc[c]; return nodes[max(range(n), key=lambda bi: recon_score(ci,bi,K))]
print("  Class-M discrete bundle (baseline)   : %.0f%%   storage ~ D=%d scalars"%(accM*100, D), flush=True)
for K in (4,8,16,min(32,n),n):
    accL=sum(read_L(a,K)==b for a,b in test)/len(test)
    print("  Class-L RESONANT (low-%2d modes)      : %.0f%%   storage ~ K*n=%d scalars"%(K, accL*100, K*n), flush=True)
print("=> if the resonant low-mode store matches/beats the discrete bundle at K*n << D, the substrate is", flush=True)
print("   continuous-resonant (Class-L), the wall was a Class-M discrete-superposition artifact (F996).", flush=True)

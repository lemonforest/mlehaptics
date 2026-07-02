"""F992 — (A) low-load landmark falsification: does re-anchoring pay off where drift CAN dominate (moderate
base accuracy + long runs)? (B) the reframe (user): the 39% wall is ARTIFICIAL (simulation never loses the
knowledge, it's all in M) -> a landmark is the find-and-ride anchor; the fix = RUNTIME SUPERPOSITION of many
perspectives held DISTINCTLY (geocentric AND epicycle AND orrery) reconciled by CONSENSUS (not merged into
one probe) = chirality-unlocking (F133). Compare single vs etak-MERGE(one probe) vs perspective-CONSENSUS
(N separate reads, vote). Sparse Klein-4; no dense/numpy/abs."""
import json, random
from srmech.amsc import hdc, laplacian as Lp
from srmech.rbs_lm import substrate as S
D=8192; cs=S.ContextSubstrate(D=D, hex_chars=16); bind=hdc.klein4_bind
def fl(q): return q.as_float() if hasattr(q,'as_float') else float(q)
ROLE=hdc.klein4_random(D, seed=4242)

# ---------- PART A: low-load landmark falsification (synthetic: moderate base accuracy, long run) ----------
V=120; vec=[hdc.klein4_random(D,seed=6000+i) for i in range(V)]
chain=list(range(40))                                  # long coherent run 0..39
edges=[]
for _ in range(4): edges += list(zip(chain,chain[1:]))  # strong chain
for i in range(0,38,5): edges += [(chain[i],chain[i]+50)]  # a competing edge every 5th token -> moderate base accuracy, drift risk
for i in range(6): edges.append((90+i,91+i))            # tiny load
M=cs.bundle_odd([bind(bind(vec[x],ROLE),vec[y]) for x,y in edges if y<V])
cnt=list(range(V))
def pred(ctx): return max(cnt,key=lambda t: fl(hdc.klein4_similarity(bind(M,bind(vec[ctx],ROLE)),vec[t])))
def cover(L):
    ok=tt=0; ctx=chain[0]
    for i in range(1,len(chain)):
        p=pred(ctx); ok+=(p==chain[i]); tt+=1
        ctx = chain[i] if (i%L==0) else p
    return ok/tt
base=sum(pred(chain[i])==chain[i+1] for i in range(len(chain)-1))/(len(chain)-1)
print("PART A -- low-load landmark falsification (synthetic long run, base per-step acc=%.0f%%):"%(base*100), flush=True)
print("  free-run (no landmarks): %.0f%%"%(cover(10**9)*100), flush=True)
print("  landmarks every 2      : %.0f%%"%(cover(2)*100), flush=True)
print("  landmarks every 1      : %.0f%% (upper bound)"%(cover(1)*100), flush=True)

# ---------- PART B: perspective CONSENSUS vs single vs etak-MERGE (real corpus, the wall regime) ----------
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
def read1(M,c,cnt): return max(cnt,key=lambda t: fl(hdc.klein4_similarity(bind(M,bind(gv[c],ROLE)),gv[t]))*gate(t))
def read_merge(M,cs_,cnt):                          # etak: MERGE cues into one probe (F986)
    probe=cs.bundle_odd([bind(M,bind(gv[c],ROLE)) for c in cs_])
    return max(cnt,key=lambda t: fl(hdc.klein4_similarity(probe,gv[t]))*gate(t))
def read_consensus(M,cs_,cnt):                      # SUPERPOSITION of perspectives: N SEPARATE reads, vote
    votes={}
    for c in cs_:
        p=read1(M,c,cnt); votes[p]=votes.get(p,0)+1
    return max(votes,key=votes.get)
gr=random.Random(5); samp=gr.sample(targets, min(45,len(targets)))
s1=sm=sc=0
for T,tid,cx in samp:
    M=M_of(tid); cnt=[w for w in uniq if tmap.get(w)==tid]
    s1+=(read1(M,cx[0],cnt)==T)
    sm+=(read_merge(M,cx[:5],cnt)==T)
    sc+=(read_consensus(M,cx[:5],cnt)==T)
N=len(samp)
print("\nPART B -- the wall regime (%d multi-context targets); knowledge PRESERVED in M (wall is artificial):"%N, flush=True)
print("  single perspective (1 anchor)      : %.0f%%"%(s1/N*100), flush=True)
print("  etak-MERGE (cues -> one probe)      : %.0f%%"%(sm/N*100), flush=True)
print("  perspective-CONSENSUS (vote, held)  : %.0f%%"%(sc/N*100), flush=True)

"""F995 — the ASYMMETRIC-FOLD encoder at 1x storage (F994's build). Instead of colliding all of a source's
nexts in one rung (baseline), FOLD each next to a rung by its salience rank via a distinct rung-key (the
fractal/asymmetric fold: strong next -> rung 0, weaker -> higher rungs = the recession, F972). ONE bundle =
1x storage (same pairs, just rung-keyed -- NOT 4x copies, F994). Read by unfolding the rungs. Compare:
baseline collide top-1 vs fold blind soft-consensus vs fold ORACLE-rung (upper bound of the separation).
Does folding the distribution into rungs ADD recall at 1x storage? Sparse Klein-4; no dense/numpy/abs."""
import json, random
from srmech.amsc import hdc, laplacian as Lp
from srmech.rbs_lm import substrate as S
D=8192; cs=S.ContextSubstrate(D=D, hex_chars=16); bind=hdc.klein4_bind
def fl(q): return q.as_float() if hasattr(q,'as_float') else float(q)
ROLE=hdc.klein4_random(D, seed=4242)
NR=6
RK=[hdc.klein4_random(D, seed=71000+r) for r in range(NR)]   # NR distinct rung-keys (the fold ladder)
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
# per-source next salience rank (within tome): rank 0 = strongest next of a
nextcnt={}
for a,b in pairs:
    if tmap.get(a)==tmap.get(b): nextcnt.setdefault(a,{}); nextcnt[a][b]=nextcnt[a].get(b,0)+1
rankof={}
for a,d in nextcnt.items():
    for r,(b,_) in enumerate(sorted(d.items(), key=lambda kv:-kv[1])): rankof[(a,b)]=min(r,NR-1)
inctx={}
for a,b in pairs:
    if tmap.get(a)==tmap.get(b) and docf.get(b,1)<FUNC:
        inctx.setdefault((b,tmap[b]),[]).append(a)
targets=[(b,tid,list(dict.fromkeys(cx))) for (b,tid),cx in inctx.items() if len(set(cx))>=3]
def base_pairs(tid): return [(a,b) for a,b in pairs if tmap.get(a)==tid and tmap.get(b)==tid]
def M_collide(tid):                              # baseline: all nexts collide in one rung
    return cs.bundle_odd([bind(bind(gv[a],ROLE),gv[b]) for a,b in base_pairs(tid)]) or None
def M_fold(tid):                                 # asymmetric fold: each next at its salience-rank rung (1x storage)
    ps=[bind(bind(gv[a],ROLE), bind(RK[rankof.get((a,b),0)], gv[b])) for a,b in base_pairs(tid)]
    return cs.bundle_odd(ps) if ps else None
def read_collide(M,c,cnt): return max(cnt,key=lambda t: fl(hdc.klein4_similarity(bind(M,bind(gv[c],ROLE)),gv[t]))*gate(t))
def read_fold_blind(M,c,cnt):                    # sum evidence across all rungs (don't know the rank)
    probe=bind(M,bind(gv[c],ROLE))
    return max(cnt,key=lambda t: gate(t)*sum(fl(hdc.klein4_similarity(probe,bind(RK[r],gv[t]))) for r in range(NR)))
def read_fold_oracle(M,c,cnt,r):                 # read the TARGET's true rung (upper bound of the separation)
    probe=bind(M,bind(gv[c],ROLE))
    return max(cnt,key=lambda t: fl(hdc.klein4_similarity(probe,bind(RK[r],gv[t])))*gate(t))
gr=random.Random(5); samp=gr.sample(targets, min(45,len(targets)))
sb=sfb=sfo=0
for T,tid,cx in samp:
    cnt=[w for w in uniq if tmap.get(w)==tid]; c=cx[0]; r=rankof.get((c,T),0)
    Mc=M_collide(tid); Mf=M_fold(tid)
    sb +=(read_collide(Mc,c,cnt)==T)
    sfb+=(read_fold_blind(Mf,c,cnt)==T)
    sfo+=(read_fold_oracle(Mf,c,cnt,r)==T)
N=len(samp)
print("ASYMMETRIC-FOLD encoder at 1x storage (%d targets; same pairs, rung-keyed not 4x-copied):"%N, flush=True)
print("  BASELINE collide (top-1)         : %.0f%%"%(sb/N*100), flush=True)
print("  FOLD blind soft-consensus        : %.0f%%"%(sfb/N*100), flush=True)
print("  FOLD ORACLE-rung (separation UB) : %.0f%%  (target read from its own rung)"%(sfo/N*100), flush=True)
print("=> if oracle-rung >> baseline, the fold SEPARATES the distribution at 1x storage (biology-smart); the", flush=True)
print("   gap oracle-vs-blind = the rung-SELECTION problem (which rung to read) left to solve.", flush=True)

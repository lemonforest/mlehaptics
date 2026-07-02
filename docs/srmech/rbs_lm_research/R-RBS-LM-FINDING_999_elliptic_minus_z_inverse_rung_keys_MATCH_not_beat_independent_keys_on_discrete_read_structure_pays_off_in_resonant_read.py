"""F999 (GH #1232) — test the elliptic -z^-1 per-level rung-keys (the EXACT form of the F995 asymmetric fold,
Rosengren theta(pz)=-z^-1 theta(z)) vs F995's INDEPENDENT HV rung-keys. Realized: RK_ell[r] = g5^(r%2)(rot(base
sectors, r*delta)) -- the -1 = chirality flip (g5, orthogonal), the z^-1 = a genuine period-D sector rotation
(NOT the period-2 Klein-4 XOR, which would collapse the ladder = why the fold is inherently elliptic/continuous).
Measure BOTH axes (per F998c): oracle-rung sharpness (F995 metric) AND top-K distribution. Sparse Klein-4; no abs."""
import json, random
from srmech.amsc import hdc, laplacian as Lp
from srmech.rbs_lm import substrate as S
D=8192; cs=S.ContextSubstrate(D=D, hex_chars=16); bind=hdc.klein4_bind
def fl(q): return q.as_float() if hasattr(q,'as_float') else float(q)
ROLE=hdc.klein4_random(D, seed=4242); HV=type(ROLE); g5=hdc.klein4_chirality_flip_gamma5
NR=6
def rot(seq,k): k%=len(seq); return seq[-k:]+seq[:-k]
RK_ind=[hdc.klein4_random(D, seed=71000+r) for r in range(NR)]      # F995: INDEPENDENT random keys
base=hdc.klein4_random(D, seed=99001); bl=base.tolist(); dlt=D//(2*NR)
RK_ell=[(g5(HV.from_sequence(rot(bl, r*dlt))) if r%2 else HV.from_sequence(rot(bl, r*dlt))) for r in range(NR)]  # elliptic (-z^-1)^r
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
def M_fold(tid,RK): return cs.bundle_odd([bind(bind(gv[a],ROLE), bind(RK[rankof.get((a,b),0)], gv[b])) for a,b in base_pairs(tid)]) or None
def rank_oracle(M,c,cnt,RK,r):
    probe=bind(M,bind(gv[c],ROLE)); return [t for _,t in sorted(((fl(hdc.klein4_similarity(probe,bind(RK[r],gv[t])))*gate(t),t) for t in cnt),reverse=True)]
gr=random.Random(5); samp=gr.sample(targets, min(45,len(targets)))
def run(RK,label):
    o1=o3=0
    for T,tid,cx in samp:
        cnt=[w for w in uniq if tmap.get(w)==tid]; c=cx[0]; r=rankof.get((c,T),0); M=M_fold(tid,RK)
        rk=rank_oracle(M,c,cnt,RK,r); o1+=(rk[0]==T); o3+=(T in rk[:3])
    N=len(samp); print("  %-26s oracle-rung top-1 %2.0f%%   top-3 %2.0f%%"%(label, o1/N*100, o3/N*100), flush=True)
print("elliptic -z^-1 rung-keys vs F995 independent HV keys (%d multi-context targets; F995 fold, 1x storage):"%len(samp), flush=True)
run(RK_ind, "F995 INDEPENDENT keys")
run(RK_ell, "elliptic -z^-1 keys")
print("=> does the exact quasi-periodic -z^-1 phase-spacing beat/match F995's independent decorrelated keys?", flush=True)

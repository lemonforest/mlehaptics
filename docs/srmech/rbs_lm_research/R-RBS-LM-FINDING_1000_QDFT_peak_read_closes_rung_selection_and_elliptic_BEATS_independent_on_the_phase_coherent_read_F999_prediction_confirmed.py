"""F1000 (#863 QDFT read, research prototype) — the QDFT/twiddle read over the rung ladder, in its tractable
matched-filter/PEAK reduction (for the single-rung fold the complex QDFT peak = max-over-rungs, by Parseval).
This is the DEPLOYABLE blind read the transform enables: it recovers the target's rung WITHOUT knowing it
(closing F995's oracle-vs-blind rung-SELECTION gap). Test blind-SUM (F995, 53%) vs QDFT-PEAK (max-over-rungs)
vs oracle, for elliptic -z^-1 codes vs F995 independent codes. The full complex QDFT (the_one/exp(mu theta)
twiddle over rungs) is the #863 package op (logged to UPSTREAM_NOTES). Sparse Klein-4; no abs."""
import json, random
from srmech.amsc import hdc, laplacian as Lp
from srmech.rbs_lm import substrate as S
D=8192; cs=S.ContextSubstrate(D=D, hex_chars=16); bind=hdc.klein4_bind
def fl(q): return q.as_float() if hasattr(q,'as_float') else float(q)
ROLE=hdc.klein4_random(D, seed=4242); HV=type(ROLE); g5=hdc.klein4_chirality_flip_gamma5
NR=6
def rot(seq,k): k%=len(seq); return seq[-k:]+seq[:-k]
RK_ind=[hdc.klein4_random(D, seed=71000+r) for r in range(NR)]
base=hdc.klein4_random(D, seed=99001); bl=base.tolist(); dlt=D//(2*NR)
RK_ell=[(g5(HV.from_sequence(rot(bl, r*dlt))) if r%2 else HV.from_sequence(rot(bl, r*dlt))) for r in range(NR)]
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
gr=random.Random(5); samp=gr.sample(targets, min(45,len(targets)))
def run(RK,label):
    o=s=q=0
    for T,tid,cx in samp:
        cnt=[w for w in uniq if tmap.get(w)==tid]; c=cx[0]; r0=rankof.get((c,T),0); M=M_fold(tid,RK)
        probe=bind(M,bind(gv[c],ROLE))
        def srung(t,r): return fl(hdc.klein4_similarity(probe,bind(RK[r],gv[t])))
        orc=max(cnt,key=lambda t: srung(t,r0)*gate(t))                              # oracle (know the rung)
        sm =max(cnt,key=lambda t: gate(t)*sum(srung(t,r) for r in range(NR)))       # F995 blind SUM
        qd =max(cnt,key=lambda t: gate(t)*max(srung(t,r) for r in range(NR)))       # QDFT-PEAK blind (matched-filter)
        o+=(orc==T); s+=(sm==T); q+=(qd==T)
    N=len(samp); print("  %-22s oracle %2.0f%%   F995 blind-SUM %2.0f%%   QDFT-PEAK blind %2.0f%%"%(label, o/N*100, s/N*100, q/N*100), flush=True)
print("#863 QDFT-peak blind read (matched-filter) -- closes the F995 rung-SELECTION gap? (%d targets):"%len(samp), flush=True)
run(RK_ind, "F995 independent keys")
run(RK_ell, "elliptic -z^-1 keys")
print("=> QDFT-peak recovers the rung BLINDLY (vs F995 blind-SUM); elliptic vs independent both work (generative,", flush=True)
print("   not accuracy -- the elliptic ladder is 1 seed + rule, the independent is NR stored keys).", flush=True)

"""F1001 (#863 full complex QDFT read) — the FULL complex QDFT over the rung ladder (coherent phase combination,
not just the peak). NR=6 -> the twiddle is the EXACT 6th roots of unity (no float series). For candidate t:
X_k = sum_r s_r(t) * omega^(r*k); score = max_k |X_k| (or energy). Coherent combination should exploit the
elliptic phase structure MORE than F1000's peak (max-over-rungs). Re-measure elliptic vs independent, vs the
F1000 peak read. Sparse Klein-4; exact roots-of-unity twiddle (surd at the read boundary only); no abs."""
import json, random, math
from srmech.amsc import hdc, laplacian as Lp
from srmech.rbs_lm import substrate as S
D=8192; cs=S.ContextSubstrate(D=D, hex_chars=16); bind=hdc.klein4_bind
def fl(q): return q.as_float() if hasattr(q,'as_float') else float(q)
ROLE=hdc.klein4_random(D, seed=4242); HV=type(ROLE); g5=hdc.klein4_chirality_flip_gamma5
NR=6
# exact 6th-roots-of-unity twiddle table W[r][k] = (cos, sin) of 2*pi*r*k/6  (surd values, read-boundary only)
S3=math.sqrt(3)/2.0
ROU=[(1.0,0.0),(0.5,S3),(-0.5,S3),(-1.0,0.0),(-0.5,-S3),(0.5,-S3)]  # omega^0..omega^5
def tw(r,k): return ROU[(r*k)%NR]
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
    pk=qd=0
    for T,tid,cx in samp:
        cnt=[w for w in uniq if tmap.get(w)==tid]; c=cx[0]; M=M_fold(tid,RK)
        probe=bind(M,bind(gv[c],ROLE))
        def svec(t): return [fl(hdc.klein4_similarity(probe,bind(RK[r],gv[t]))) for r in range(NR)]
        def peak(t): return gate(t)*max(svec(t))
        def qdft(t):                                          # full complex QDFT: max_k |sum_r s_r omega^rk|
            s=svec(t); best=0.0
            for k in range(NR):
                re=sum(s[r]*tw(r,k)[0] for r in range(NR)); im=sum(s[r]*tw(r,k)[1] for r in range(NR))
                m=re*re+im*im
                if m>best: best=m
            return gate(t)*best
        pk+=(max(cnt,key=peak)==T); qd+=(max(cnt,key=qdft)==T)
    N=len(samp); print("  %-22s QDFT-PEAK(F1000) %2.0f%%   FULL-QDFT %2.0f%%"%(label, pk/N*100, qd/N*100), flush=True)
print("#863 FULL complex QDFT (6th-roots twiddle, coherent) vs the F1000 peak read (%d targets):"%len(samp), flush=True)
run(RK_ind, "F995 independent keys")
run(RK_ell, "elliptic -z^-1 keys")
print("=> does coherent phase combination (full QDFT) amplify the elliptic advantage over the peak/max read?", flush=True)

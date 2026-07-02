"""F991c (lean) — 'push R further?' via the CAPACITY lever: R vs tome size, + landmark payoff. Sparse Klein-4."""
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
toks=[w for a in arts[:3] for w in a]; uniq=list(dict.fromkeys(toks)); idx={w:i for i,w in enumerate(uniq)}; n=len(uniq)
vec={w: hdc.klein4_random(D, seed=(hash(w)%80000)+11) for w in uniq}
pairs=[(a,b) for a,b in zip(toks,toks[1:]) if a!=b]
und={}
for a,b in pairs:
    e=(min(idx[a],idx[b]),max(idx[a],idx[b])); und[e]=und.get(e,0)+1
edges=list(und); wg=[float(und[e])*gate(uniq[e[0]])*gate(uniq[e[1]]) for e in edges]
def tomes_at(mt):
    res=Lp.recursive_cut(n, edges, wg, max_tome=mt); tm={}
    for ti,t in enumerate(res['tomes']):
        for i in t: tm[uniq[i]]=ti
    return tm, res['n_tomes']
def build_M(seq):
    ps=[bind(bind(vec[seq[i]],ROLE),vec[seq[i+1]]) for i in range(len(seq)-1)]
    return cs.bundle_odd(ps) if ps else None
def pred1(M,ctx,cnt): return max(cnt,key=lambda t: fl(hdc.klein4_similarity(bind(M,bind(vec[ctx],ROLE)),vec[t]))*gate(t))
def reach(seq,M,cnt,s):
    ctx=seq[s]; r=0
    for i in range(s+1,len(seq)):
        if pred1(M,ctx,cnt)!=seq[i]: break
        r+=1; ctx=seq[i]
    return r
print("'push R further' via the CAPACITY lever (R vs tome size), n=%d vocab:"%n, flush=True)
keep=None
for mt in (15,30,60):
    tm,ng=tomes_at(mt); seqs={}
    for w in toks: seqs.setdefault(tm[w],[]).append(w)
    tot=cn=0; store={}
    for tid,seq in seqs.items():
        if len(seq)<4: continue
        cnt=[w for w in uniq if tm[w]==tid]; M=build_M(seq); store[tid]=(seq,cnt,M)
        for s in range(0,len(seq)-2,6): tot+=reach(seq,M,cnt,s); cn+=1
    R=tot/max(1,cn); print('  max_tome=%2d (%2d tomes): R = %.2f -> 2R spacing = %.1f'%(mt,ng,R,2*R), flush=True)
    if mt==30: keep=(store,R)
store,R=keep; L=max(2,round(2*R))
def cover(Lsp):
    ok=tt=0
    for tid,(seq,cnt,M) in store.items():
        ctx=seq[0]
        for i in range(1,len(seq)):
            p=pred1(M,ctx,cnt); ok+=(p==seq[i]); tt+=1
            ctx = seq[i] if (i%Lsp==0) else p
    return ok/max(1,tt)
print("LANDMARK PAYOFF (max_tome=30):", flush=True)
print('  free-run (no landmarks): %.0f%%'%(cover(10**9)*100), flush=True)
print('  landmarks every 2R=%d  : %.0f%%'%(L, cover(L)*100), flush=True)
print('  landmarks every 1      : %.0f%% (upper bound)'%(cover(1)*100), flush=True)

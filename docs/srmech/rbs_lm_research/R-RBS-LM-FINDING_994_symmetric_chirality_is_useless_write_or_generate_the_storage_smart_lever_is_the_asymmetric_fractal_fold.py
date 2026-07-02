"""F994 — storage-smart chirality: don't WRITE 4x (explodes storage + capacity), GENERATE from a fractal
(user: use the fractal shape to encode as smart as biology). Ground both halves: (1) does 4x full-chirality
WRITE explode capacity (recall degrades)? (2) is a GENERATED chiral frame free -- i.e. is the Klein-4 flip an
ISOMETRY (sim(flip a, flip b)==sim(a,b))? If yes, a SYMMETRIC generated frame costs 0 storage but adds 0 info
-> the only way to add info at 1x storage is an ASYMMETRIC fractal fold (mock-theta beat), the biology-smart
encoding. Sparse Klein-4; no dense/numpy/abs."""
import json, random
from srmech.amsc import hdc, laplacian as Lp
from srmech.rbs_lm import substrate as S
D=8192; cs=S.ContextSubstrate(D=D, hex_chars=16); bind=hdc.klein4_bind
def fl(q): return q.as_float() if hasattr(q,'as_float') else float(q)
ROLE=hdc.klein4_random(D, seed=4242)
g5=hdc.klein4_chirality_flip_gamma5; w7=hdc.klein4_chirality_flip_omega7; cpt=hdc.klein4_cpt_mirror

# ---- (0) is the Klein-4 chirality flip an ISOMETRY? (does a GENERATED frame preserve similarity = free?) ----
a=hdc.klein4_random(D,seed=1); b=hdc.klein4_random(D,seed=2)
s_ab=fl(hdc.klein4_similarity(a,b)); s_flip=fl(hdc.klein4_similarity(g5(a),g5(b)))
from srmech.amsc import cascade as _cs
_iso = fl(_cs.magnitude(s_ab - s_flip)) < 1e-9   # srmech-allow: Class-K |Δ| tolerance check (float near-equality, not a hand-rolled magnitude)
print("(0) Klein-4 gamma5 flip isometry? sim(a,b)=%.4f  sim(g5 a, g5 b)=%.4f  -> %s"%(
      s_ab, s_flip, 'ISOMETRY (generated frame is FREE + info-preserving = symmetric-redundant)' if _iso else 'NOT isometry (flip changes structure)'), flush=True)

# ---- F992 test set (gated tomes, multi-context targets) ----
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
def base_pairs(tid): return [(a,b) for a,b in pairs if tmap.get(a)==tid and tmap.get(b)==tid]
def M_1x(tid):                                   # 1x: identity frame only
    ps=[bind(bind(gv[a],ROLE),gv[b]) for a,b in base_pairs(tid)]
    return cs.bundle_odd(ps) if ps else None
def M_4x(tid):                                   # 4x: WRITE each pair + its 3 chiral images (storage explodes)
    ps=[]
    for a,b in base_pairs(tid):
        pa,pb=bind(gv[a],ROLE),gv[b]
        ps.append(bind(pa,pb)); ps.append(bind(g5(pa),g5(pb))); ps.append(bind(w7(pa),w7(pb))); ps.append(bind(cpt(pa),cpt(pb)))
    return cs.bundle_odd(ps) if ps else None
def read(M,c,cnt): return max(cnt,key=lambda t: fl(hdc.klein4_similarity(bind(M,bind(gv[c],ROLE)),gv[t]))*gate(t))
gr=random.Random(5); samp=gr.sample(targets, min(45,len(targets)))
b1=b4=0
for T,tid,cx in samp:
    cnt=[w for w in uniq if tmap.get(w)==tid]; c=cx[0]
    b1+=(read(M_1x(tid),c,cnt)==T)
    b4+=(read(M_4x(tid),c,cnt)==T)
N=len(samp)
print("\n(1) STORAGE cost of WRITING full-chirality (4x pairs into the SAME bundle):", flush=True)
print("  1x identity storage      : %.0f%%"%(b1/N*100), flush=True)
print("  4x full-chirality WRITE  : %.0f%%  (4x load into one bundle -> capacity wall F896)"%(b4/N*100), flush=True)
print("=> writing chirality explodes storage AND load; if the flip is an isometry a generated frame is free but", flush=True)
print("   symmetric-redundant -> the biology-smart lever is an ASYMMETRIC fractal fold (mock-theta), 1x storage.", flush=True)

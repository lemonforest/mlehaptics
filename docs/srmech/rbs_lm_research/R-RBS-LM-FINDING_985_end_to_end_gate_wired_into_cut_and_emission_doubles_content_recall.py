"""F985 — END-TO-END re-run, doc-freq aboutness-gate (F984) wired into BOTH axes: (1) the community-tome
CUT (edges weighted by the gate so function-word hubs don't drive the partition, F947/F957/F960); (2) the
EMISSION/recall read (sim*gate). FULL memory, nothing dropped (F982). Then FAST -> etak-deeper (F978/F979).
Honest baseline: same pipeline WITHOUT the gate. Metric: recall-accuracy on content prev->next test pairs.
srmech rc97; sparse Klein-4 + sparse recursive_cut; no dense/numpy/abs."""
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
def gate(t): d=docf.get(t,1); return 1.0 if d<FUNC else FUNC/d      # F984 one-sided aboutness-gate
toks=[w for a in arts[:6] for w in a]          # a real multi-article corpus (full, nothing dropped)
uniq=list(dict.fromkeys(toks)); idx={w:i for i,w in enumerate(uniq)}; n=len(uniq)
vec={w: hdc.klein4_random(D, seed=(hash(w)%80000)+11) for w in uniq}
# directed content pairs for the TEST (prev->next where next is a content word = low doc-freq)
pairs=[(a,b) for a,b in zip(toks,toks[1:]) if a!=b]
test=[(a,b) for a,b in pairs if docf.get(b,1)<FUNC]            # targets that are content (the ones we care to recall)
# ---- build community tomes two ways: UNGATED cut vs GATED cut (edge weights) ----
und={}
for a,b in pairs:
    e=(min(idx[a],idx[b]),max(idx[a],idx[b])); und[e]=und.get(e,0)+1
edges=list(und)
w_plain=[float(und[e]) for e in edges]
w_gated=[float(und[e])*gate(uniq[e[0]])*gate(uniq[e[1]]) for e in edges]   # de-lens the CUT: hub edges down-weighted
def tome_of(edges,wts):
    res=Lp.recursive_cut(n, edges, wts, max_tome=60)
    m={}
    for ti,t in enumerate(res['tomes']):
        for i in t: m[uniq[i]]=ti
    return m, res['n_tomes']
tmap_plain,_=tome_of(edges,w_plain); tmap_gated,ng=tome_of(edges,w_gated)
# ---- recall per pipeline: route to prev's tome, build that tome's M, FAST then etak-deeper, gated emission ----
def tome_M(tmap, tid):
    ps=[bind(bind(vec[a],ROLE),vec[b]) for a,b in pairs if tmap.get(a)==tid and tmap.get(b)==tid]
    return cs.bundle_odd(ps) if ps else None
def recall(prev, target, tmap, gated):
    tid=tmap.get(prev)
    M=tome_M(tmap, tid)
    if M is None: return False
    cnt=[w for w in uniq if tmap.get(w)==tid]
    def rd():
        probe=bind(M,bind(vec[prev],ROLE))
        def sc(t):
            s=fl(hdc.klein4_similarity(probe,vec[t])); return s*gate(t) if gated else s
        return max(cnt, key=sc)
    return rd()==target
import random; gr=random.Random(1); sample=gr.sample(test, min(40,len(test)))
def acc(tmap, gated): return sum(recall(a,b,tmap,gated) for a,b in sample)/len(sample)
print('END-TO-END recall on real corpus (%d tokens, %d vocab, %d tomes gated; %d content test pairs):'%(len(toks),n,ng,len(sample)))
print('  BASELINE  (ungated cut + ungated emission): %.0f%%'%(acc(tmap_plain, False)*100))
print('  GATED CUT only                             : %.0f%%'%(acc(tmap_gated, False)*100))
print('  GATED CUT + GATED EMISSION (full F984 wire): %.0f%%'%(acc(tmap_gated, True)*100))

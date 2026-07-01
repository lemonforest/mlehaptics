"""F981 — etak-deeper at HEAVIER real-corpus load with DE-LENSED community-tomes (the F980 next step).
De-lensed content memory (function words dropped, F957/F959); real recurring target T; heavy load. Show:
(1) FAST single-cue fails/branches at heavy load; (2) ETAK-DEEPER multi-cue (T's real contexts, sqrt k)
recovers T; (3) CHUNK to T's community-tome (recursive_cut, F960) makes FAST work directly. Two axes both
recover at real load. Sparse Klein-4; no dense/numpy/abs."""
import json
from srmech.amsc import hdc, laplacian as L
from srmech.rbs_lm import substrate as S
D=8192; cs=S.ContextSubstrate(D=D, hex_chars=16); bind=hdc.klein4_bind
def fl(q): return q.as_float() if hasattr(q,'as_float') else float(q)
ROLE=hdc.klein4_random(D, seed=4242)
stop=set('the of in a is and to as for on it was were are that with by an at from or be this which his her its he she they we you i not no but have has had will would can could s a an'.split())
toks=[]
with open('/home/skirklan/corpora/wikipedia/simplewiki_fullbody_instrument.ndjson') as f:
    for line in f:
        toks.extend(json.loads(line)['s'].split())
        if len(toks)>=5000: break
content=[t for t in toks[:5000] if t not in stop]
uniq=list(dict.fromkeys(content)); vec={t: hdc.klein4_random(D, seed=(hash(t)%80000)+11) for t in uniq}
# real recurrences: prev -> next content bigrams
nexts={}
for a,b in zip(content,content[1:]):
    if a!=b: nexts.setdefault(b,{}).setdefault(a,0); nexts[b][a]+=1
# target T = the content token with the MOST distinct content-prev contexts
T=max(nexts, key=lambda t: len(nexts[t])); prevs=list(nexts[T].keys())
cand=uniq[:120] if T in uniq[:120] else uniq[:119]+[T]
def read(ctxs):
    probe=cs.bundle_odd([bind(bind(vec[c],ROLE),vec) if False else bind(M,bind(vec[c],ROLE)) for c in ctxs]) if len(ctxs)>1 else bind(M,bind(vec[ctxs[0]],ROLE))
    s=sorted(((fl(hdc.klein4_similarity(probe,vec[t])),t) for t in cand), reverse=True)
    return s[0][1], s[0][0]-s[1][0]
# HEAVY de-lensed memory: all content bigrams (heavy load)
allpairs=[(a,b) for a,b in zip(content,content[1:]) if a!=b]
M=cs.bundle_odd([bind(bind(vec[a],ROLE),vec[b]) for a,b in allpairs])
print('target T=%r recurs after %d distinct contexts; HEAVY memory = %d content bigrams, vocab %d'%(T,len(prevs),len(allpairs),len(uniq)))
THINK=0.02
t1,m1=read([prevs[0]])
print('FAST single-cue [%s] -> top=%s margin=%.4f  correct=%s'%(prevs[0],t1,m1,'YES' if t1==T else 'no'))
for kk in (2,3,5,8):
    if kk>len(prevs): break
    tk,mk=read(prevs[:kk])
    print('ETAK-DEEPER k=%d -> top=%s margin=%.4f  correct=%s'%(kk,tk,mk,'YES' if tk==T else 'no'))

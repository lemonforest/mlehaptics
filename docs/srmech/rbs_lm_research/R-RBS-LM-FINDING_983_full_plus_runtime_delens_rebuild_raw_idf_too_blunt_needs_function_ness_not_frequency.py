"""F983 (honest rebuild, F982): a BOUNDED tome (chunk = capacity axis) that keeps EVERY token (nothing
dropped) + RUNTIME de-lens (read-time sim*idf = frequency-prior axis) + etak-deeper. Both axes on the FULL
un-doctored token set. Show: runtime-de-lens recovers a content target where the raw read returns a function
word, the tome is bounded so margins clear, and function words remain in memory (shapes intact)."""
import json
from srmech.amsc import hdc
from srmech.rbs_lm import substrate as S
D=8192; cs=S.ContextSubstrate(D=D, hex_chars=16); bind=hdc.klein4_bind
def fl(q): return q.as_float() if hasattr(q,'as_float') else float(q)
ROLE=hdc.klein4_random(D, seed=4242)
stopish=set('the of in a is and to as for on it was were are that with by an at from or be this'.split())
toks=[]
with open('/home/skirklan/corpora/wikipedia/simplewiki_fullbody_instrument.ndjson') as f:
    for line in f:
        toks.extend(json.loads(line)['s'].split())
        if len(toks)>=250: break
tome=toks[:180]                                    # BOUNDED tome (chunk), ALL tokens kept
uniq=list(dict.fromkeys(tome)); freq={}
for t in toks: freq[t]=freq.get(t,0)+1             # freq from a wider slice for the idf lens
vec={t: hdc.klein4_random(D, seed=(hash(t)%80000)+11) for t in uniq}
nexts={}
for a,b in zip(tome,tome[1:]):
    if a!=b: nexts.setdefault(b,{}).setdefault(a,0); nexts[b][a]+=1
cands=[t for t in nexts if t not in stopish and len(t)>=3 and len(nexts[t])>=2]
T=max(cands, key=lambda t: len(nexts[t])); prevs=list(nexts[T].keys())[:6]
M=cs.bundle_odd([bind(bind(vec[a],ROLE),vec[b]) for a,b in zip(tome,tome[1:]) if a!=b])   # full bounded memory
def read(ctxs, delens):
    probe=cs.bundle_odd([bind(M,bind(vec[c],ROLE)) for c in ctxs]) if len(ctxs)>1 else bind(M,bind(vec[ctxs[0]],ROLE))
    def sc(t):
        s=fl(hdc.klein4_similarity(probe,vec[t])); return s/(freq[t]**0.5) if delens else s
    r=sorted(((sc(t),t) for t in uniq), reverse=True); return r[0][1], r[0][0]-r[1][0]
print('BOUNDED tome: %d tokens, %d vocab, all kept (nothing dropped). Target T=%r (%d contexts)'%(len(tome),len(uniq),T,len(nexts[T])))
t,_=read([prevs[0]], False); print('  raw FAST [%s] -> %s'%(prevs[0],t))
t,m=read([prevs[0]], True);  print('  RUNTIME-delens FAST [%s] -> %s  margin=%.4f  correct=%s'%(prevs[0],t,m,'YES' if t==T else 'no'))
for kk in (2,3):
    if kk>len(prevs): break
    t,m=read(prevs[:kk], True); print('  ETAK-DEEPER runtime-delens k=%d -> %s  margin=%.4f  correct=%s'%(kk,t,m,'YES' if t==T else 'no'))
print('  shapes intact -- function words still in the SAME tome:', [w for w in ('the','of','in','and') if w in vec])

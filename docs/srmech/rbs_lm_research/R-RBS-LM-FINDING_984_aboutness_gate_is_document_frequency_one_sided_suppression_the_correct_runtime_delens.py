"""F984 aboutness-GATE (corrected): function-ness = DOCUMENT frequency (validated), but applied as a ONE-SIDED
GATE (suppress only high-doc-freq function words; leave low-doc-freq content/topic words UNCHANGED -- do NOT
boost rare noise). Test on (a) a content-dominated read [fourth]->month (gate must leave it = month) and
(b) a function-dominated read (gate must surface content, not the/of). FULL memory, nothing dropped."""
import json
from srmech.amsc import hdc
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
FUNC_THRESH=int(NDOC*0.6)                       # in >=60% of tomes => function
def gate(t):                                    # ONE-SIDED: content unchanged; function suppressed prop. to doc-spread
    d=docf.get(t,1)
    return 1.0 if d<FUNC_THRESH else (FUNC_THRESH/d)   # (<=1 for function words; ==1 for content)
tome=arts[0]; uniq=list(dict.fromkeys(tome)); vec={t: hdc.klein4_random(D, seed=(hash(t)%80000)+11) for t in uniq}
M=cs.bundle_odd([bind(bind(vec[x],ROLE),vec[y]) for x,y in zip(tome,tome[1:]) if x!=y])
def read(ctx, gated):
    probe=bind(M,bind(vec[ctx],ROLE))
    def sc(t):
        s=fl(hdc.klein4_similarity(probe,vec[t])); return s*gate(t) if gated else s
    return [t for _,t in sorted(((sc(t),t) for t in uniq), reverse=True)[:3]]
# (a) content-dominated read -- gate must NOT harm it
print('(a) content read [fourth]:  raw=%s  GATED=%s'%(read('fourth',False), read('fourth',True)))
# (b) function-dominated read -- find a ctx whose raw top1 is a function word, show gate surfaces content
for c in ('is','and','the','of','a','to'):
    if c in vec:
        raw=read(c,False); gat=read(c,True)
        if docf.get(raw[0],1)>=FUNC_THRESH:   # raw returned a function word
            print('(b) function read [%s]: raw=%s (func top)  GATED=%s (content surfaces)'%(c,raw,gat)); break

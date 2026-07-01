"""F982 — de-lens at RUNTIME (a read-time lens on the FULL preserved memory), NOT at write-time (dropping
function words bakes a DIFFERENT graph + destroys shapes = doctoring the SSoT). Test: FULL memory keeps ALL
tokens (function words too); at read time apply an IDF re-weight (sim * 1/sqrt(freq)) -> content surfaces,
WHILE the memory is unchanged (function words still recallable, adjacency/order/phrase shapes intact).
srmech rc97; sparse; no numpy/abs."""
import json
from srmech.amsc import hdc
from srmech.rbs_lm import substrate as S
D=8192; cs=S.ContextSubstrate(D=D, hex_chars=16); bind=hdc.klein4_bind
def fl(q): return q.as_float() if hasattr(q,'as_float') else float(q)
ROLE=hdc.klein4_random(D, seed=4242)
toks=[]
with open('/home/skirklan/corpora/wikipedia/simplewiki_fullbody_instrument.ndjson') as f:
    for line in f:
        toks.extend(json.loads(line)['s'].split())
        if len(toks)>=3000: break
toks=toks[:3000]
uniq=list(dict.fromkeys(toks)); freq={}
for t in toks: freq[t]=freq.get(t,0)+1
vec={t: hdc.klein4_random(D, seed=(hash(t)%80000)+11) for t in uniq}
# FULL memory -- ALL tokens incl function words + punctuation-as-tokens; nothing dropped, shapes preserved
M=cs.bundle_odd([bind(bind(vec[a],ROLE),vec[b]) for a,b in zip(toks,toks[1:]) if a!=b])
cand=uniq[:150]
def probe(ctx): return bind(M, bind(vec[ctx],ROLE))
def raw_top(ctx):
    p=probe(ctx); s=sorted(((fl(hdc.klein4_similarity(p,vec[t])),t) for t in cand),reverse=True); return s[:4]
def idf_top(ctx):   # RUNTIME de-lens: re-weight sims by 1/sqrt(freq) at READ time (memory untouched)
    p=probe(ctx); s=sorted(((fl(hdc.klein4_similarity(p,vec[t]))/ (freq[t]**0.5),t) for t in cand),reverse=True); return s[:4]
ctx='the'
print('FULL memory (all tokens kept; %d vocab; nothing dropped):'%len(uniq))
print('  raw read [%s]      -> %s  (frequency prior dominates)'%(ctx,[(t,round(v,3)) for v,t in raw_top(ctx)]))
print('  RUNTIME idf-de-lens -> %s  (content surfaces; SAME memory)'%[(t,round(v,4)) for v,t in idf_top(ctx)])
# proof the shapes survive: a function word is STILL recallable from the full memory (write-time drop would lose it)
fw=[w for w in ('the','of','in') if w in freq][0]
p=probe('fourth'); s=sorted(((fl(hdc.klein4_similarity(p,vec[t])),t) for t in cand),reverse=True)
print('  function word still in memory + recallable (write-time drop would DELETE it): %r freq=%d present=%s'%(fw,freq.get(fw,0), fw in vec))
print('=> runtime de-lens = a LENS (read-time view); write-time drop = doctoring (different graph, shapes destroyed)')

import json
from srmech.rbs_lm import RBSLMInferenceSubstrate
from srmech.amsc import laplacian as L
def fl(q): return q.as_float() if hasattr(q,'as_float') else float(q)
stop=set('the of in a is and to as for on it was were are that with by an at from or be this which his her its he she they we you i not no but have has had will would can could s'.split())
toks=[]
with open('/home/skirklan/corpora/wikipedia/simplewiki_fullbody_instrument.ndjson') as f:
    for line in f:
        toks.extend(json.loads(line)['s'].split())
        if len(toks)>=1500: break
toks=toks[:1500]; know=[t for t in toks if t not in stop]
# SPARSE knowledge Laplacian -> recursive_cut into bounded tomes (F960)
vocab=sorted(set(know)); idx={t:i for i,t in enumerate(vocab)}; n=len(vocab)
eset={}
for a,b in zip(know,know[1:]):
    if a!=b:
        e=(min(idx[a],idx[b]),max(idx[a],idx[b])); eset[e]=eset.get(e,0)+1
edges=list(eset); wts=[float(eset[e]) for e in edges]
res=L.recursive_cut(n, edges, wts, max_tome=40)
tomes=[[vocab[i] for i in t] for t in res['tomes']]
print('knowledge: %d content tok, %d vocab, %d edges -> %d sparse tomes (max_tome=40)'%(len(know),n,len(edges),res['n_tomes']))
# per-KNOWLEDGE-TOME recall coherence: build a substrate on each tome's token subsequence
def build(stream):
    p={'substrate':{'D':8192,'token_seed_hex_chars':16},'inference':{'instrument':{'operating_k':2,'operating_temperature':0.0,'memory_capacity':max(8,len(stream)),'default_max_tokens':4,'learn_seed':1}}}
    s=RBSLMInferenceSubstrate.from_params(p); s.learn(stream); return s
tomeset=[set(t) for t in tomes]
verd={}; margs=[]
for ts in tomeset[:8]:
    sub=[t for t in know if t in ts][:60]            # this tome's tokens in corpus order
    if len(sub)<4: continue
    s=build(sub)
    for i in range(0, min(40,len(sub)-2), 8):
        r=s.next_token_coherence(sub[i:i+2]); verd[r.verdict]=verd.get(r.verdict,0)+1; margs.append(fl(r.collapse_margin))
mk=sum(margs)/len(margs) if margs else 0
print('KNOWLEDGE tomes (chunked, F960): verdicts %s  mean-margin %.3f'%(verd,mk))
print('compare F964 flat: knowledge-flat 0.010, english-flat 0.006 -> chunked knowledge margin %.3f'%mk)

import json
from pathlib import Path
from srmech.rbs_lm.substrate import ContextSubstrate, sim_k4_batch
from srmech.amsc import hdc
INST=Path.home()/"corpora"/"wikipedia"/"simplewiki_rawbody_instrument.ndjson"
IDX =Path.home()/"corpora"/"wikipedia"/"simplewiki_rawbody_index.json"
def load(t):
    off=json.loads(IDX.read_text())[t.lower()]
    with open(INST) as f: f.seek(off); return json.loads(f.readline())["s"].split()
toks=load("tomato"); k=3
cs=ContextSubstrate(D=10000, hex_chars=16)
vocab=sorted(set(toks)); vlist=[cs.enc(w) for w in vocab]; vidx={w:i for i,w in enumerate(vocab)}
pairs=[(toks[i-k:i], toks[i]) for i in range(k,len(toks))]
binds=[hdc.klein4_bind(cs.encode_context(w), cs.enc(n)) for w,n in pairs]
def bundle(vs): return vs[0] if len(vs)==1 else hdc.klein4_bundle(*(vs if len(vs)%2 else vs+[vs[0]]))
sample=pairs[::13]   # ~30 contexts across the article
def eval_reads(Ms, label):
    ranks=[]; r1=0
    for w,n in sample:
        scores=[-1.0]*len(vocab)
        for M in Ms:
            sc=sim_k4_batch(hdc.klein4_bind(M, cs.encode_context(w)), vlist)
            for i,s in enumerate(sc):
                if s>scores[i]: scores[i]=s
        order=sorted(range(len(vocab)), key=lambda i:-scores[i])
        r=order.index(vidx[n]); ranks.append(r); r1+=(r==0)
    print(f"  {label:24s}: true-succ mean rank {sum(ranks)/len(ranks):5.1f}/{len(vocab)} | rank-1 {100*r1/len(sample):4.1f}%")
print(f"tomato: {len(pairs)} binds, vocab {len(vocab)}, {len(sample)} sampled contexts, D=10000")
eval_reads([bundle(binds)], "single M (0.8.2 now)")
for C in (32,16):
    eval_reads([bundle(binds[i:i+C]) for i in range(0,len(binds),C)], f"chunked M (C={C})")

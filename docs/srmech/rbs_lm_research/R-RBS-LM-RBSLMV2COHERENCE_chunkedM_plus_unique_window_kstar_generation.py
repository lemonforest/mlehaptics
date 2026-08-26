import json
from pathlib import Path
from srmech.rbs_lm.substrate import ContextSubstrate, sim_k4_batch
from srmech.amsc import hdc
INST=Path.home()/"corpora"/"wikipedia"/"simplewiki_rawbody_instrument.ndjson"
IDX =Path.home()/"corpora"/"wikipedia"/"simplewiki_rawbody_index.json"
def load(t):
    off=json.loads(IDX.read_text())[t.lower()]
    with open(INST) as f: f.seek(off); r=json.loads(f.readline()); return r["s"].split(), r["k"]
def bundle(vs): return vs[0] if len(vs)==1 else hdc.klein4_bundle(*(vs if len(vs)%2 else vs+[vs[0]]))
CS=ContextSubstrate(D=10000, hex_chars=16)
def gen(toks, C, k, n=44):
    vocab=sorted(set(toks)); vlist=[CS.enc(w) for w in vocab]
    binds=[hdc.klein4_bind(CS.encode_context(toks[i-k:i]), CS.enc(toks[i])) for i in range(k,len(toks))]
    Ms=[bundle(binds)] if C is None else [bundle(binds[i:i+C]) for i in range(0,len(binds),C)]
    out=list(toks[:k])
    for _ in range(n):
        best=[-1.0]*len(vocab)
        for M in Ms:
            sc=sim_k4_batch(hdc.klein4_bind(M, CS.encode_context(out[-k:])), vlist)
            for i,s in enumerate(sc):
                if s>best[i]: best[i]=s
        out.append(vocab[max(range(len(vocab)), key=lambda i:best[i])])
    return out, sum(a==b for a,b in zip(out,toks))/min(len(out),len(toks))
toks,kstar=load("tomato")
print(f"tomato unique-walk k*={kstar}\n")
for C,k,lbl in [(None,kstar,f"single-M, k=k*={kstar}"),(16,kstar,f"chunked C16, k=k*={kstar}")]:
    o,m=gen(toks,C,k); print(f"[{lbl:26s}] {m*100:4.0f}% match: {' '.join(o[:40])}")

import json, time
from srmech.amsc import laplacian as La, qi
def fl(q): return q.as_float() if hasattr(q,"as_float") else float(q)
def arg(z): return fl(qi.Qi.from_complex(z).arg())
path="/home/skirklan/corpora/wikipedia/simplewiki_fullbody_instrument.ndjson"
docs=[]; freq={}
with open(path) as f:
    for line in f:
        toks=[t for t in json.loads(line)["s"].split() if t.isalpha()]
        if len(toks)<4: continue
        docs.append(toks)
        for t in toks: freq[t]=freq.get(t,0)+1
        if len(docs)>=8000: break
vocab=sorted(freq, key=lambda w:-freq[w])[40:160]; idx={w:i for i,w in enumerate(vocab)}; n=len(vocab)
dw={}
for toks in docs:
    for a,b in zip(toks,toks[1:]):
        if a in idx and b in idx and a!=b:
            k=(idx[a],idx[b]); dw[k]=dw.get(k,0)+1
edges=list(dw); weights=[float(dw[e]) for e in edges]
H=La.magnetic_laplacian(n, edges, weights, q=0.25)
print(f"n={n}, {len(edges)} edges; eigendecomposing (complex Hermitian)...", flush=True)
t0=time.monotonic(); evals,evecs=La.hermitian_eigendecompose(H); print(f"  done in {time.monotonic()-t0:.1f}s", flush=True)
def ev_re(j): return evals[j].real if hasattr(evals[j],'real') else fl(evals[j])
order=sorted(range(n), key=ev_re)
k=order[1]
ph={vocab[i]: arg(evecs[i][k]) for i in range(n)}
ranked=sorted(vocab, key=lambda w: ph[w])
print(f"directional embedding (phase of mode {k}); poles of the word-order flow:", flush=True)
print(f"  low-phase  : {', '.join(ranked[:12])}", flush=True)
print(f"  high-phase : {', '.join(ranked[-12:])}", flush=True)

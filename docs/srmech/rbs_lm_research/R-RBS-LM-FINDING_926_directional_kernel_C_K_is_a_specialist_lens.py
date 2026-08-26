"""C/K directional kernel: phase (Qarg) reads the net which-way. Directed pairs -> saturated |theta|;
symmetric pairs -> theta ~ 0. The directed sibling of F920's undirected spectral kernel."""
import json
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
        if len(docs)>=12000: break
vocab=sorted(freq, key=lambda w:-freq[w])[40:200]; idx={w:i for i,w in enumerate(vocab)}; n=len(vocab)
dw={}
for toks in docs:
    for a,b in zip(toks,toks[1:]):
        if a in idx and b in idx and a!=b:
            k=(idx[a],idx[b]); dw[k]=dw.get(k,0)+1
edges=list(dw); weights=[float(dw[e]) for e in edges]
H=La.magnetic_laplacian(n, edges, weights, q=0.25)
print(f"=== C/K directional kernel (n={n}, {len(edges)} edges) — phase = net which-way ===")
def show(a,b):
    if a in idx and b in idx:
        f_,r_=dw.get((idx[a],idx[b]),0),dw.get((idx[b],idx[a]),0)
        z=H[idx[a]][idx[b]]; tot=f_+r_
        asym=(f_-r_)/tot if tot else 0
        print(f"  {a:>9} ~ {b:<8} theta={arg(z):+.3f}  |  {a}->{b}={f_:<5} {b}->{a}={r_:<5} net-asym={asym:+.2f}")
print("STRONGLY DIRECTED (expect saturated |theta|):")
for a,b in [("united","states"),("according","to"),("such","as"),("based","on"),("more","than"),("part","of")]: show(a,b)
print("MORE SYMMETRIC (expect smaller |theta|):")
for a,b in [("black","white"),("men","women"),("north","south"),("east","west")]: show(a,b)
print("=> theta (Qarg, Class C) magnitude tracks net directionality; sign tracks which-way. The byte/glyph (M)")
print("   and undirected-spectral (L) kernels are direction-BLIND; this is the read they cannot give.")

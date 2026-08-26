"""Option C research, on the simplewiki data we already have: the co-occurrence Laplacian eigenvectors as a
RELATIONSHIP-OF-RELATIONSHIPS spectral kernel (Class-L), and the augmentation test -- does the spectral
embedding give USAGE similarity (cat~dog) orthogonal to the byte/glyph SPELLING similarity (cat~cot)?
srmech rc28; cooccurrence_edges -> dense_laplacian -> symmetric_eigendecompose; native eigensolver; no numpy."""
import json
from srmech.amsc import text as T, laplacian as La, hdc
from srmech.rbs_lm import substrate as S
def fl(q): return q.as_float() if hasattr(q,"as_float") else float(q)

# --- load sentences + pick vocab (plain token-frequency dict for vocab selection; NOT co-occurrence) ---
path="/home/skirklan/corpora/wikipedia/simplewiki_fullbody_instrument.ndjson"
docs=[]; freq={}
with open(path) as f:
    for line in f:
        toks=[t for t in json.loads(line)["s"].split() if t.isalpha()]
        if len(toks)<4: continue
        docs.append(toks)
        for t in toks: freq[t]=freq.get(t,0)+1
        if len(docs)>=12000: break
# drop the ~40 highest-frequency hubs (function words; F782 hub-lensing) then take next 360 content words
ranked=sorted(freq, key=lambda w:-freq[w])
vocab=ranked[40:400]; idx={w:i for i,w in enumerate(vocab)}
n=len(vocab)
print(f"=== spectral kernel on simplewiki ({len(docs)} sentences, vocab n={n} content words) ===")

# --- Class-L: co-occurrence graph -> Laplacian -> eigendecompose (the spectral encoding) ---
nn, edges, weights = T.cooccurrence_edges(docs, window=4, vocab=vocab)
L = La.dense_laplacian(nn, edges, weights)
evals, evecs = La.symmetric_eigendecompose(L)
ev=[fl(x) for x in evals]
near0=sum(1 for x in ev if x<1e-6)
print(f"(1) SPECTRUM fingerprint: {nn} nodes, {len(edges)} edges; lowest eigenvalues {[round(x,3) for x in sorted(ev)[:6]]}")
print(f"    near-zero count (connected components / coarse communities, F781): {near0}")

# spectral embedding: word i -> its coords in the low nonzero eigenvectors (the relationship modes)
order=sorted(range(nn), key=lambda j:ev[j])           # ascending eigenvalue
K=[j for j in order if ev[j]>1e-6][:24]               # skip null space, take 24 lowest modes
emb={vocab[i]: [fl(evecs[i][j]) for j in K] for i in range(nn)}
def cos(a,b):
    na=sum(x*x for x in a)**0.5; nb=sum(x*x for x in b)**0.5
    return (sum(x*y for x,y in zip(a,b))/(na*nb)) if na and nb else 0.0
def spectral_nn(w,k=5):
    return sorted([(cos(emb[w],emb[u]),u) for u in vocab if u!=w], reverse=True)[:k]

# byte/glyph (C1) similarity for the SAME query -> spelling neighbors (the contrast)
cs=S.ContextSubstrate(D=8192, hex_chars=16)
wv={w: cs.enc(w) for w in vocab}
def byteglyph_nn(w,k=5):
    return sorted([(fl(hdc.klein4_similarity(wv[w],wv[u])),u) for u in vocab if u!=w], reverse=True)[:k]

print(f"\n(2) RELATIONSHIPS-OF-RELATIONSHIPS (spectral-embedding nearest) vs byte/glyph (spelling nearest):")
for q in ("water","city","king","river","two","made"):
    if q not in idx: continue
    sp=", ".join(f"{u}" for _,u in spectral_nn(q))
    bg=", ".join(f"{u}" for _,u in byteglyph_nn(q))
    print(f"    {q:<7} spectral(usage): {sp}")
    print(f"    {q:<7} byte/glyph(spell): {bg}")

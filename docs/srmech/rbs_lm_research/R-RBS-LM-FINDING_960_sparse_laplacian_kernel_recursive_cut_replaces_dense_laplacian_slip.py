"""F960 — SPARSE Laplacian kernel correction (user: 'ensure our kernel is sparse; dense things creeping in').
Audit: the recall/coherence path was already sparse (Klein-4 HDC integer match-counts, the_one, exact
rationals, native next_token_coherence). The ONE dense slip was F947's dense_laplacian(n,edges) +
symmetric_eigendecompose -- a dense n x n matrix over the corpus token graph. Fix: fiedler_sparse /
recursive_cut (power iteration on the EDGE-LIST, NO dense matrix). Grounded: n=1588 content nodes, 3318 edges
(edge-list only); fiedler_sparse -> Vec (n-unbounded; dense was <=256); recursive_cut -> 54 BALANCED tomes
(~44-48 each, max_tome=48), fixing the F947 hairball {191,29} AND the F955 chunking (bounded < F896 wall) AND
the sparsity directive, in one sparse op. srmech rc79; no numpy; no dense matrix."""
import json
from srmech.amsc import laplacian as L
stop=set('the of in a is and to as for on it was were are that with by an at from or be this which his her its he she they we you i not no but have has had will would can could s'.split())
toks=[]
with open('/home/skirklan/corpora/wikipedia/simplewiki_fullbody_instrument.ndjson') as f:
    for line in f:
        toks.extend(json.loads(line)['s'].split())
        if len(toks)>=6000: break
content=[t for t in toks[:6000] if t not in stop]
vocab=sorted(set(content)); idx={t:i for i,t in enumerate(vocab)}; n=len(vocab)
eset={}
for a,b in zip(content,content[1:]):
    if a!=b:
        e=(min(idx[a],idx[b]),max(idx[a],idx[b])); eset[e]=eset.get(e,0)+1
edges=list(eset.keys()); wts=[float(eset[e]) for e in edges]
print('SPARSE token graph: n=%d nodes, %d edges (edge-list ONLY -- no dense %dx%d = %d-cell matrix)'%(n,len(edges),n,n,n*n))
fied=L.fiedler_sparse(n, edges, wts)
print('fiedler_sparse -> Vec(%d) (sparse power-iteration, n-unbounded; dense was <=256)'%len(fied))
res=L.recursive_cut(n, edges, wts, max_tome=48)
sizes=sorted((len(t) for t in res['tomes']), reverse=True)
print('recursive_cut -> %d BALANCED tomes, sizes %s (vs F947 dense degenerate {191,29})'%(res['n_tomes'], sizes[:10]))

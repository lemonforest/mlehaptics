"""F947 — full spectral community-tome routing on the real corpus. Build the token co-occurrence Laplacian
(Class L), spectrally partition tokens into communities (sign of the 2 lowest non-trivial eigenvectors = 4
Klein-4 spectral quadrants), route each directed bigram relationship into its source-community tome, and
recall via route-to-community + raw-sim trichotomy. Compare context-resolution (does recall return a TRUE
next of the prev, not a frequency-prior function word) for: single bundle vs spectral community-tomes vs
source-routed (the clean F944 baseline). Tests the F946 prediction: chunking helps capacity but the
frequency prior (function words in every community) may still leak. srmech rc58; Class-L Laplacian; no numpy."""
import json, statistics as st
from srmech.amsc import laplacian as Lp, hdc
from srmech.rbs_lm import substrate as S
D=8192; cs=S.ContextSubstrate(D=D, hex_chars=16); bind=hdc.klein4_bind
def fl(q): return q.as_float() if hasattr(q,'as_float') else float(q)

path='/home/skirklan/corpora/wikipedia/simplewiki_fullbody_instrument.ndjson'
toks=[]
with open(path) as f:
    for line in f:
        toks.extend(json.loads(line)['s'].split())
        if len(toks)>=3000: break
toks=toks[:3000]
freq={}
for t in toks: freq[t]=freq.get(t,0)+1
vocab=[t for t,_ in sorted(freq.items(), key=lambda kv:(-kv[1],kv[0]))[:220]]   # top-220 (<=256 Laplacian bound)
idx={t:i for i,t in enumerate(vocab)}; n=len(vocab)
vec={t: hdc.klein4_random(D, seed=3000+i) for i,t in enumerate(vocab)}
ROLE=hdc.klein4_random(D, seed=4242)

nexts={}; und={}; rels=set()
for a,b in zip(toks,toks[1:]):
    if a in idx and b in idx and a!=b:
        nexts.setdefault(a,set()).add(b)
        e=(min(idx[a],idx[b]),max(idx[a],idx[b])); und[e]=und.get(e,0)+1
        rels.add((a,b))
edges=list(und.keys()); rels=list(rels)
print('vocab=%d  undirected edges=%d  directed relationships=%d'%(n,len(edges),len(rels)))

# Class-L spectral partition: Laplacian -> eigenvectors -> 4 communities (sign of 2 lowest non-trivial)
Lap=Lp.dense_laplacian(n, edges)
evals,evecs=Lp.symmetric_eigendecompose(Lap)
ev=[fl(x) for x in evals]
order=sorted(range(n), key=lambda j: ev[j])         # ascending eigenvalue
c1,c2=order[1],order[2]                              # the 2 lowest NON-trivial (skip the ~0 constant mode)
def col(j): return [fl(evecs[i][j]) for i in range(n)]
v1,v2=col(c1),col(c2)
comm={vocab[i]: (1 if v1[i]>=0 else 0)*2 + (1 if v2[i]>=0 else 0) for i in range(n)}  # 0..3 Klein-4 quadrant
sizes={}
for t in vocab: sizes[comm[t]]=sizes.get(comm[t],0)+1
print('4 spectral communities sizes:', sizes)

def bundle(rel_list): return cs.bundle_odd([bind(bind(vec[p],ROLE),vec[nx]) for p,nx in rel_list])
M_single=bundle(rels)
comm_tomes={}
for p,nx in rels: comm_tomes.setdefault(comm[p],[]).append((p,nx))
comm_tomes={cid: bundle(rl) for cid,rl in comm_tomes.items()}
src_tomes={}
for p,nx in rels: src_tomes.setdefault(p,[]).append((p,nx))
src_tomes={p: bundle(rl) for p,rl in src_tomes.items()}

def resolve(M, prev):
    probe=bind(M, bind(vec[prev],ROLE))
    s=sorted(((fl(hdc.klein4_similarity(probe, vec[t])),t) for t in vocab), reverse=True)
    med=st.median([v for v,_ in s])
    return s[0][1], s[0][0]-s[1][0], s[0][0]-med      # (top1_token, margin, top1_above_floor)

# test: content prevs (not the top-12 function words), recall must land on a TRUE next of prev
stop=set(vocab[:12])
test=[p for p in nexts if p not in stop and p in idx][:60]
def score(getM):
    hit=0; mar=[]; flo=[]
    for p in test:
        M=getM(p); t,m,fa=resolve(M,p); mar.append(m); flo.append(fa)
        if t in nexts[p]: hit+=1
    return hit/len(test), st.mean(mar), st.mean(flo)
a0,m0,f0=score(lambda p: M_single)
a1,m1,f1=score(lambda p: comm_tomes[comm[p]])
a2,m2,f2=score(lambda p: src_tomes[p])
print('\n  routing            true-next-acc   mean-margin   mean-top1-above-floor')
print('  single bundle      %5.0f%%          %.3f         %.3f'%(a0*100,m0,f0))
print('  spectral 4-comm    %5.0f%%          %.3f         %.3f'%(a1*100,m1,f1))
print('  source-routed      %5.0f%%          %.3f         %.3f'%(a2*100,m2,f2))
# does the frequency prior still leak in the community tomes? show a few
print('\n  sample recalls (prev -> single | spectral-comm | true-nexts):')
for p in test[:6]:
    ts,_,_=resolve(M_single,p); tc,_,_=resolve(comm_tomes[comm[p]],p)
    print('    %-12s -> %-10s | %-10s | %s'%(p, ts, tc, sorted(list(nexts[p]))[:5]))

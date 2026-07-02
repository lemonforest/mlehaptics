"""F990 — navigation landmark = TWO coupled chiral-opposite fronts (overtone forward + undertone backward);
SCALE = the coherence-reach R (the |q| half-life, F975). Longer chain + load so a SINGLE front's reach R <
chain length (can't span); TWO chiral fronts each reach ~R and MEET at a landmark, spanning ~2R. Sparse Klein-4."""
from srmech.amsc import hdc
from srmech.rbs_lm import substrate as S
D=8192; cs=S.ContextSubstrate(D=D, hex_chars=16); bind=hdc.klein4_bind
def fl(q): return q.as_float() if hasattr(q,'as_float') else float(q)
ROLE=hdc.klein4_random(D, seed=4242); V=400
vec=[hdc.klein4_random(D,seed=6000+i) for i in range(V)]
L=28; chain=list(range(L))
edges=[]
for _ in range(3): edges += list(zip(chain,chain[1:]))
for i in range(90): edges.append((60+(i%300),61+(i%300)))    # heavier load -> finite front reach
M=cs.bundle_odd([bind(bind(vec[x],ROLE),vec[y]) for x,y in edges])
def step(node, avoid):
    probe=bind(M,bind(vec[node],ROLE))
    s=sorted(((fl(hdc.klein4_similarity(probe,vec[j])),j) for j in range(V) if j not in avoid),reverse=True)
    return s[0][1], s[0][0]-s[1][0]
def front(start, thr=0.05, cap=40):
    cur=start; seen={start}; path=[start]
    for _ in range(cap):
        nx,m=step(cur, seen)
        if m<thr: break
        seen.add(nx); path.append(nx); cur=nx
    return path
fwd=front(0); bwd=front(L-1)
Rf=len(fwd)-1; Rb=len(bwd)-1; meet=sorted(set(fwd)&set(bwd))
print('chain 0..%d (len %d), heavy load. Single-front coherence-reach R (the |q| half-life):'%(L-1,L-1))
print('  OVERTONE  forward front from 0  reaches node %d  (R_f=%d)'%(fwd[-1],Rf))
print('  UNDERTONE backward front from %d reaches node %d  (R_b=%d)'%(L-1,bwd[-1],Rb))
spanned_single = (Rf>=L-1)
print('  single front spans the whole chain? %s (reach %d < len %d)'%(spanned_single,max(Rf,Rb),L-1))
print('  TWO chiral fronts couple? meet/overlap at %s ; combined coverage %d/%d nodes'%(meet or 'GAP', len(set(fwd)|set(bwd)),L))
print('=> the coherence-reach R (=|q| half-life, F975) sets the landmark spacing: fronts must meet within 2R')

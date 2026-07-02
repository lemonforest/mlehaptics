"""F989 — concurrent time-front BUBBLES over ONE knowledge, coupled for NAVIGATION not merge (user). Single
bubble at A->{B,C} can't disambiguate locally (both stored strong); a concurrent bubble walks each branch
FORWARD (excluding backtrack to parent A -- F967 direction) and reports cumulative coherence, informing
bubble-1's move. No knowledge merged. Sparse Klein-4; no dense/numpy/abs."""
from srmech.amsc import hdc
from srmech.rbs_lm import substrate as S
D=8192; cs=S.ContextSubstrate(D=D, hex_chars=16); bind=hdc.klein4_bind
def fl(q): return q.as_float() if hasattr(q,'as_float') else float(q)
ROLE=hdc.klein4_random(D, seed=4242); V=200
vec=[hdc.klein4_random(D,seed=6000+i) for i in range(V)]
A,B,C=0,1,2; rich=[C,3,4,5,6]
edges=[]
for _ in range(5): edges += [(A,B),(A,C)] + list(zip(rich,rich[1:]))
for i in range(8): edges.append((50+i,51+i))
M=cs.bundle_odd([bind(bind(vec[x],ROLE),vec[y]) for x,y in edges])
def step(node, avoid):
    probe=bind(M,bind(vec[node],ROLE))
    s=sorted(((fl(hdc.klein4_similarity(probe,vec[j])),j) for j in range(V) if j not in avoid),reverse=True)
    return s[0][1], s[0][0]-s[1][0]
def fwd(start, parent, steps=6):                # forward walk, excluding backtrack (parent + seen) = directed
    cur=start; seen={start,parent}; tot=0.0
    for _ in range(steps):
        nx,m=step(cur, seen)
        if m<0.05: break
        tot+=m; seen.add(nx); cur=nx
    return tot
print('A -> {B=1 (dead), C=2 (rich chain)}, both A-edges stored x5 (LOCAL branch is ambiguous):')
locA=step(A, {A})[0]  # (just to note A's local read is a coin toss between B and C)
cohB=fwd(B, A); cohC=fwd(C, A)
print('  BUBBLE-2 forward-coherence (directed, excl backtrack):  B-front %.3f (dead) | C-front %.3f (rich)'%(cohB,cohC))
pick = C if cohC>cohB else B
print('  CROSS-BUBBLE informed pick: %d  correct(=C=2)=%s'%(pick, pick==C))
print('=> a concurrent bubble on a different front navigates bubble-1; NO knowledge merged -- just a nav hint')

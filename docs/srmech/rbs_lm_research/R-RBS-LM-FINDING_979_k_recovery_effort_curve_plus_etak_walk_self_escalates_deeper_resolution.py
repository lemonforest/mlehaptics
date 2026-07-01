"""F979 — (A) map k->recovery: how many cues to recover a target buried by load N (the effort curve); and
(B) wire the self-escalating multi-cue 'etak deeper' into a recall WALK: at each step FAST(k=1); if margin
low -> escalate cues (etak deeper resolution); emit when resolved, honest-stop when maxed. Sparse Klein-4."""
from srmech.amsc import hdc
from srmech.rbs_lm import substrate as S
D=8192; cs=S.ContextSubstrate(D=D, hex_chars=16); bind=hdc.klein4_bind
def fl(q): return q.as_float() if hasattr(q,'as_float') else float(q)
ROLE=hdc.klein4_random(D, seed=4242); V=1200
vec=[hdc.klein4_random(D, seed=6000+i) for i in range(V)]
THINK=0.02
def read(M, cuelist):
    probe=cs.bundle_odd([bind(M,bind(vec[c],ROLE)) for c in cuelist]) if len(cuelist)>1 else bind(M,bind(vec[cuelist[0]],ROLE))
    s=sorted(((fl(hdc.klein4_similarity(probe,vec[j])),j) for j in range(V)), reverse=True)
    return s[0][1], s[0][0]-s[1][0]

# ---- (A) k -> recovery map: X recurs after up to 12 cues; sweep load; min-k to recover (top1 & margin>=THINK) ----
Xi=0; CUES=list(range(1,13))
print('(A) effort curve -- min cues k to recover a target at load N (deeper load = more cues):')
print('  load N   min-k to recover   (margin at that k)')
for N in (200, 400, 800, 1100):
    pairs=[bind(bind(vec[c],ROLE),vec[Xi]) for c in CUES]
    for i in range(N): pairs.append(bind(bind(vec[13+(i%(V-14))],ROLE),vec[13+((i+1)%(V-14))]))
    M=cs.bundle_odd(pairs)
    got=None
    for k in (1,2,3,5,8,12):
        t,m=read(M, CUES[:k])
        if t==Xi and m>=THINK: got=(k,m); break
    print('  N=%4d   %s'%(N, ('k=%d (margin %.3f)'%got if got else 'not recovered even at k=12 (lost to time)')))

# ---- (B) etak recall walk with self-escalating deeper resolution ----
print()
print('(B) etak recall walk -- FAST(k=1) -> escalate cues (etak deeper) on low margin -> emit / honest-stop:')
chain=[20,21,22,23,24]                       # the walk targets
# each chain link recurs after up to 4 cues (multiple time-anchors), plus load
altcues={t:[t, 100+t, 200+t, 300+t] for t in chain}
def mem(nload):
    pairs=[]
    for i in range(len(chain)-1):
        for c in altcues[chain[i]]: pairs.append(bind(bind(vec[c],ROLE),vec[chain[i+1]]))
    for i in range(nload): pairs.append(bind(bind(vec[500+(i%600)],ROLE),vec[500+((i+1)%600)]))
    return cs.bundle_odd(pairs)
M=mem(700)                                   # heavy load so some steps need to think
def step(prev_t):
    cl=altcues[prev_t]
    for k in (1,2,4):                        # etak: try 1 cue, escalate to 2, then 4
        t,m=read(M, cl[:k])
        if m>=THINK: return t,('FAST' if k==1 else 'ETAK-DEEPER(k=%d)'%k),m,k
    return t,'STOP',m,4
cur=chain[0]
for _ in range(4):
    nxt,mode,m,k=step(cur)
    print('   from %d -> %d  [%s, margin %.3f, cues=%d]'%(cur,nxt,mode,m,k))
    cur=nxt

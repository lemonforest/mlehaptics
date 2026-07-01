from srmech.amsc import hdc
from srmech.rbs_lm import substrate as S
D=8192; cs=S.ContextSubstrate(D=D, hex_chars=16); bind=hdc.klein4_bind
def fl(q): return q.as_float() if hasattr(q,'as_float') else float(q)
ROLE=hdc.klein4_random(D, seed=4242); V=1400
vec=[hdc.klein4_random(D, seed=6000+i) for i in range(V)]
THINK=0.015
chain=[20,21,22,23,24]
altcues={t:[t]+[100*j+t for j in range(1,9)] for t in chain}   # 9 cues available per link
ncues={20:2, 21:9, 22:3, 23:6}                                  # stored cue-richness per link (varies difficulty)
def mem(nload):
    pairs=[]
    for i in range(len(chain)-1):
        for c in altcues[chain[i]][:ncues[chain[i]]]: pairs.append(bind(bind(vec[c],ROLE),vec[chain[i+1]]))
    for i in range(nload): pairs.append(bind(bind(vec[600+(i%700)],ROLE),vec[600+((i+1)%700)]))
    return cs.bundle_odd(pairs)
M=mem(90)
def read(cl):
    probe=cs.bundle_odd([bind(M,bind(vec[c],ROLE)) for c in cl]) if len(cl)>1 else bind(M,bind(vec[cl[0]],ROLE))
    s=sorted(((fl(hdc.klein4_similarity(probe,vec[j])),j) for j in range(V)), reverse=True)
    return s[0][1], s[0][0]-s[1][0]
print('etak recall walk (load=90): FAST(1 cue) -> escalate cues (etak deeper) on low margin -> emit / honest-stop')
for i in range(len(chain)-1):
    cur, want = chain[i], chain[i+1]
    cl=altcues[cur]; res=None
    for k in (1,2,4,8):
        t,m=read(cl[:k])
        if m>=THINK: res=(t,'FAST' if k==1 else 'ETAK-DEEPER(k=%d)'%k,m,k); break
    if res is None: t,m=read(cl[:8]); res=(t,'STOP',m,8)
    t,mode,m,k=res
    print('   %d->%d  stored-cues=%d  %-16s margin %.3f  cues-used=%d  correct=%s'%(cur,want,ncues[cur],mode,m,k,'YES' if t==want else 'no'))
print('=> effort self-selects per step: rich-cue links resolve FAST; sparse-cue links escalate (etak deeper) to recover')

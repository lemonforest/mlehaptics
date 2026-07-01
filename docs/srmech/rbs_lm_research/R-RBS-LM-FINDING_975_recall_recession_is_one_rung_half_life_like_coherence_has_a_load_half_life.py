"""F975 — point the F974 |q|-meter at the RBS-LM recall recession. Measure the collapse-margin as memory
load N grows (the F896 wall), read octaves per N-doubling: CONSTANT = geometric/one-rung (half-life-like,
memoryless); ACCELERATING = factorial/multi-rung. Sparse Klein-4; margin = raw top1-top2 sim; no float mid-
cascade beyond the display octave count; no abs."""
from fractions import Fraction as Fr
from srmech.amsc import hdc
from srmech.rbs_lm import substrate as S
D=8192; cs=S.ContextSubstrate(D=D, hex_chars=16); bind=hdc.klein4_bind
def fl(q): return q.as_float() if hasattr(q,'as_float') else float(q)
ROLE=hdc.klein4_random(D, seed=4242)
def margin_at_load(N):                      # chain of N tokens; store forward pairs; margin at ctx[0]
    vec=[hdc.klein4_random(D, seed=5000+i) for i in range(N)]
    M=cs.bundle_odd([bind(bind(vec[i],ROLE),vec[i+1]) for i in range(N-1)])
    probe=bind(M, bind(vec[0],ROLE))
    s=sorted((fl(hdc.klein4_similarity(probe,vec[j])) for j in range(N)), reverse=True)
    return s[0]-s[1]
def octaves(r):
    r=Fr(r).limit_denominator(10**9) if r>0 else Fr(1,10**9); n=0; x=Fr(1)
    while x>r and n<300: x=x/2; n+=1
    return n
loads=[4,8,16,32,64,128]
ms=[(N, margin_at_load(N)) for N in loads]
print('RBS-LM recall recession -- collapse-margin vs memory load N (the F896 wall):')
for N,m in ms: print('   N=%3d  margin=%.4f  (octaves-below-1 = %d)'%(N,m,octaves(m)))
print('octaves ADDED per N-doubling (constant => geometric/one-rung; growing => accelerating/multi-rung):')
for i in range(len(ms)-1):
    (N1,m1),(N2,m2)=ms[i],ms[i+1]
    do=octaves(m2)-octaves(m1)
    print('   N %3d->%3d: +%d octaves  (1/sqrtN predicts ~ +0.5/doubling = mostly-flat)'%(N1,N2,do))
print('=> read the shape: is the recall recession CONSTANT (one rung, half-life-like) or ACCELERATING (multi-rung)?')

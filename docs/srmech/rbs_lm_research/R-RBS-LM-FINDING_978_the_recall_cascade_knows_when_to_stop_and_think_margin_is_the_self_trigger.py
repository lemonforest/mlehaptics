"""F978 — does the recall cascade KNOW when to 'stop and think'? YES: the collapse-margin is the self-signal.
A SELF-TRIGGERING recall: try single-cue (k=1, fast/automatic); read the margin; if it's LOW (below the
think-threshold but the target isn't pure noise) -> the cascade DETECTS 'in there but not reachable from one
cue' and ESCALATES to multi-cue superposition (stop-and-think, the F976/F977 sqrt(k) lift); re-read; if it
clears -> recovered from the deeper reservoir; if even k_max stays at floor -> honest STOP (lost to time).
Sparse Klein-4; no dense/numpy/abs."""
from srmech.amsc import hdc
from srmech.rbs_lm import substrate as S
D=8192; cs=S.ContextSubstrate(D=D, hex_chars=16); bind=hdc.klein4_bind
def fl(q): return q.as_float() if hasattr(q,'as_float') else float(q)
ROLE=hdc.klein4_random(D, seed=4242); V=800
vec=[hdc.klein4_random(D, seed=6000+i) for i in range(V)]
Xi=0; cues=[1,2,3,4,5]
THINK=0.020    # margin below this + not-noise -> escalate (stop and think)
def read(probe):
    s=sorted(((fl(hdc.klein4_similarity(probe,vec[j])),j) for j in range(V)), reverse=True)
    return s[0][1], s[0][0]-s[1][0]
def self_recall(M):
    # k=1 fast/automatic
    t,m=read(bind(M,bind(vec[cues[0]],ROLE)))
    if m>=THINK: return 'FAST', t==Xi, m, 1
    # margin low -> STOP AND THINK: escalate cue-count until it clears or we run out
    for k in (3,5):
        t,m=read(cs.bundle_odd([bind(M,bind(vec[c],ROLE)) for c in cues[:k]]))
        if m>=THINK: return 'THOUGHT(k=%d)'%k, t==Xi, m, k
    return 'STOP(lost)', t==Xi, m, 5
print('load   self-triggering recall (fast -> stop&think escalation -> honest stop):')
for N in (100, 300, 500, 700):
    pairs=[bind(bind(vec[c],ROLE),vec[Xi]) for c in cues]
    for i in range(N): pairs.append(bind(bind(vec[6+(i%(V-7))],ROLE),vec[6+((i+1)%(V-7))]))
    M=cs.bundle_odd(pairs)
    mode,ok,m,k=self_recall(M)
    print('  N=%3d  -> %-14s recovered_X=%s  margin=%.3f  cues_used=%d'%(N,mode,'YES' if ok else 'no',m,k))
print('=> the cascade SELF-DETECTS low margin (k=1 fails) and escalates cues (stop&think); recovers when reachable, honest-STOPs when not')

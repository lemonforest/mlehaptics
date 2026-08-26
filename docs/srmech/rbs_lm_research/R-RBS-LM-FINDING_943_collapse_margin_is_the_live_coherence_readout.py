"""F943 — the collapse-margin (top1-top2) wired as Siona's live coherence readout. Per step: high margin =
the now collapsed cleanly (coherent); near-zero = the now stayed superposed (incoherent -> stop/flag). It
caught what the F941 argmax masked: only a->b was a confident collapse (0.215); b->c was marginal (0.002,
the F896 crosstalk wall) -> the readout fires. Half-beat: 0.006 from the start (never collapses). This is
the anti-hallucination honest-stop at the recall level (the F934 OPEN residue, F933 coherence order-param)."""
from srmech.amsc import hdc
from srmech.rbs_lm import substrate as S
D=8192; cs=S.ContextSubstrate(D=D, hex_chars=16); bind=hdc.klein4_bind
def fl(q): return q.as_float() if hasattr(q,'as_float') else float(q)
vocab=['a','b','c','d','e','f','g','h']; vec={t: hdc.klein4_random(D, seed=1000+i) for i,t in enumerate(vocab)}
ROLE=hdc.klein4_random(D, seed=4242); chain=['a','b','c','d','e']
M=cs.bundle_odd([ bind(bind(vec[p],ROLE),vec[n]) for p,n in zip(chain,chain[1:]) ])
def resolve(q):
    s=sorted(((fl(hdc.klein4_similarity(q,vec[t])),t) for t in vocab), reverse=True)
    return s[0][1], round(s[0][0]-s[1][0],3)   # (next, collapse-margin)
THRESH=0.10
def walk(qf,start,label,n=6):
    cur=start; print(label)
    for _ in range(n):
        nxt,m=qf(cur); coh = m>=THRESH
        print(f'   {cur}->{nxt}  margin {m:>5}  {\"coherent\" if coh else \"INCOHERENT -> honest-stop (now will not collapse)\"}')
        if not coh: break
        cur=nxt
walk(lambda x: resolve(bind(M,bind(vec[x],ROLE))), 'a', 'FULL-beat + collapse-margin coherence readout:')
walk(lambda x: resolve(bind(M,vec[x])), 'a', 'HALF-beat:')

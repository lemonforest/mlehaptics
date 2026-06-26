"""F942 — the recall-beat IS a chirality collapse, and we know exactly WHEN: at the cleanup/NEXT-resolution.
PAST (anchor) = already collapsed (one-hot, margin 0.74). NOW (full-beat composite, pre-cleanup) = a
SUPERPOSITION (top emerging ~0.47, rest ~0.24 = both hands); cleanup (argmax) = the collapse to one hand.
HALF-beat now = flat = never collapses forward (the F843 stall). Arrow of time: past collapsed, now
collapsing (the front), future superposed. srmech rc58; reuses the F941 chain."""
from srmech.amsc import hdc
from srmech.rbs_lm import substrate as S
D=8192; cs=S.ContextSubstrate(D=D, hex_chars=16); bind=hdc.klein4_bind
def fl(q): return q.as_float() if hasattr(q,'as_float') else float(q)
vocab=['a','b','c','d','e','f','g','h']; vec={t: hdc.klein4_random(D, seed=1000+i) for i,t in enumerate(vocab)}
ROLE=hdc.klein4_random(D, seed=4242); chain=['a','b','c','d','e']
M=cs.bundle_odd([ bind(bind(vec[p],ROLE),vec[n]) for p,n in zip(chain,chain[1:]) ])
def sims(v): return {t: round(fl(hdc.klein4_similarity(v,vec[t])),2) for t in vocab}
def margin(d): s=sorted(d.values(),reverse=True); return round(s[0]-s[1],2)
past=sims(vec['a']); now=sims(bind(M,bind(vec['a'],ROLE))); half=sims(bind(M,vec['a']))
print('PAST  margin', margin(past), '(collapsed, one-hot)  | NOW full margin', margin(now), '(superposition collapsing ->', max(now,key=now.get),') | NOW half margin', margin(half), '(flat = no forward collapse)')

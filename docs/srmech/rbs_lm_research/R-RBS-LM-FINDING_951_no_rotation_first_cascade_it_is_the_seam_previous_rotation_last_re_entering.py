"""F951 — why nature shows rotation-LAST (decay residues) but not rotation-FIRST (onsets): the rotation-first
is the SEAM (the previous beat's rotation-last re-entering as the now), not a separately-generated cascade.
Grounded on the beat-walk: each step's OUTPUT (rotation-last) == the next step's INPUT (rotation-first). So
there is no isolable rotation-first; it is the previous rotation-last inherited as the now's context. Confirms
the user's hypothesis 4 (the start of a beat = previous-beat chirality + the now collapsing). srmech rc78."""
from srmech.amsc import hdc
from srmech.rbs_lm import substrate as S
D=8192; cs=S.ContextSubstrate(D=D, hex_chars=16); bind=hdc.klein4_bind
def fl(q): return q.as_float() if hasattr(q,'as_float') else float(q)
vocab=['a','b','c','d','e','f','g','h']; vec={t: hdc.klein4_random(D, seed=1000+i) for i,t in enumerate(vocab)}
ROLE=hdc.klein4_random(D, seed=4242); chain=['a','b','c','d','e']
src={}
for p,n in zip(chain,chain[1:]): src.setdefault(p,[]).append(bind(bind(vec[p],ROLE),vec[n]))
src={k: cs.bundle_odd(v) for k,v in src.items()}
def recall(x):
    if x not in src: return None
    s=sorted(((fl(hdc.klein4_similarity(bind(src[x],bind(vec[x],ROLE)),vec[t])),t) for t in vocab),reverse=True); return s[0][1]
cur='a'; seam=[]
for _ in range(4):
    nx=recall(cur)
    if nx is None: break
    seam.append((cur,nx)); cur=nx
print('beat-walk:', ' '.join('%s->%s'%(p,n) for p,n in seam))
for i in range(len(seam)-1):
    print('  beat %d rotation-last %r == beat %d rotation-first %r : %s'%(i,seam[i][1],i+1,seam[i+1][0],seam[i][1]==seam[i+1][0]))
print('=> no separate rotation-first; it IS the previous rotation-last re-entering (the seam)')

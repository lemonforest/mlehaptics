"""F956 — per-tome native coherence on REAL English: the routing FAILS because articles share function-word
vocab. Disjoint-vocab synthetic tomes routed cleanly (F955); real simplewiki article-fragment tomes share
is/the/of, so route-to-best (raw context-similarity) picks the WRONG tome -- ['april','apr'] (article-0 =
'april apr is the fourth month...') routed to an ART tome -> 'art~ activities~ activity~ object~', and even
nonsense [zz,yy] did not STOP. = the F946 frequency prior / F947 hairball / F782 hub-lensing at the ROUTING
layer. Fix (handed forward): route by CONTENT (IDF-de-lensed / aboutness-gated context, F768/F782), not raw
similarity. srmech rc79; no numpy."""
import json, random
from srmech.rbs_lm import RBSLMInferenceSubstrate
def fl(q): return q.as_float() if hasattr(q,'as_float') else float(q)
arts=[]
with open('/home/skirklan/corpora/wikipedia/simplewiki_fullbody_instrument.ndjson') as f:
    for line in f:
        t=json.loads(line)['s'].split()[:30]
        if len(t)>=20: arts.append(t)
        if len(arts)>=6: break
def mk(toks):
    p={'substrate':{'D':8192,'token_seed_hex_chars':16},'inference':{'instrument':{'operating_k':2,'operating_temperature':0.0,'memory_capacity':64,'default_max_tokens':12,'learn_seed':1}}}
    s=RBSLMInferenceSubstrate.from_params(p); s.learn(toks); return s
tomes=[mk(a) for a in arts]
def routed(ctx):
    best=None
    for s in tomes:
        r=s.next_token_coherence(ctx)
        if r.verdict!='STOP':
            g=fl(r.top1_floor_gap)
            if best is None or g>best[1]: best=(r,g)
    return best[0] if best else None
def walk(prompt, n=10, seed=0):
    out=list(prompt); gr=random.Random(seed); tr=[]
    for _ in range(n):
        r=routed(out)
        if r is None: tr.append('<STOP>'); break
        nxt=gr.choice(r.branch_candidates) if (r.verdict=='BRANCH' and r.branch_candidates) else r.candidates_topk[0]
        tr.append(nxt+('~' if r.verdict=='BRANCH' else '')); out.append(nxt)
    return tr
print('article-0 actual :', ' '.join(arts[0][:12]))
print('routed walk      :', ' '.join(arts[0][:2]+walk(arts[0][:2])), '  <- routed to WRONG (art) tome')
print('nonsense [zz,yy] :', ' '.join(walk(['zz','yy'])), '  <- no clean STOP (shared vocab)')

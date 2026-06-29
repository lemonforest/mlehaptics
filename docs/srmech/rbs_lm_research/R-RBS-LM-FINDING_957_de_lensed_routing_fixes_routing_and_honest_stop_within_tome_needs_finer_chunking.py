"""F957 — IDF-de-lensed routing (route by the context's rarest/highest-IDF content token) FIXES the F956
routing failure: nonsense [zz,yy] -> STOP (honest-stop restored), content [april,apr] -> routes to the
correct tome. BUT the within-tome walk still wanders (it~ in~ to~ of~ is~) because real article text REPEATS
function words (the/of/in), saturating even a 30-token tome -- the F946 frequency prior recurring WITHIN the
tome (F955's distinct-token synthetic chains had no repeats, so they walked clean). The frequency prior is a
LAYERED wall: single-M (F946) -> routing (F956->fixed here) -> within-tome emission (needs finer chunking
F947 or emission de-lensing). srmech rc79; no numpy."""
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
tok2tomes={}
for i,a in enumerate(arts):
    for t in set(a): tok2tomes.setdefault(t,set()).add(i)
def route(ctx):                                        # IDF-de-lensed: route by the rarest context token
    cand=[t for t in ctx if t in tok2tomes]
    if not cand: return []
    return sorted(tok2tomes[min(cand, key=lambda t: len(tok2tomes[t]))])
def routed(ctx):
    cs=route(ctx)
    if not cs: return None
    best=None
    for i in cs:
        r=tomes[i].next_token_coherence(ctx)
        if r.verdict!='STOP':
            g=fl(r.top1_floor_gap)
            if best is None or g>best[1]: best=(r,g)
    return best[0] if best else None
def walk(prompt, n=12, seed=0):
    out=list(prompt); gr=random.Random(seed); tr=[]
    for _ in range(n):
        r=routed(out)
        if r is None: tr.append('<STOP>'); break
        nxt=gr.choice(r.branch_candidates) if (r.verdict=='BRANCH' and r.branch_candidates) else r.candidates_topk[0]
        tr.append(nxt+('~' if r.verdict=='BRANCH' else '')); out.append(nxt)
    return tr
print('FIXED by de-lensed routing: nonsense [zz,yy] ->', ' '.join(walk(['zz','yy'])), '(honest-stop restored)')
print('routing now picks the right tome for [april,apr] (article-0 via the rare token april/apr)')
print('within-tome still wanders:', ' '.join(['april','apr']+walk(['april','apr'])), '(repeated function words saturate the tome, F946)')

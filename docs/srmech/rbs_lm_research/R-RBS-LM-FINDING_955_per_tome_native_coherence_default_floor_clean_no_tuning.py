"""F955 — per-tome native coherence: chunk into small tomes (one substrate each, M under the F896 wall) +
route each recall step to the best tome's next_token_coherence -> clean COHERENT walks on the DEFAULT floor,
NO per-corpus tuning. Confirms the F954 prediction (F947 chunking spreads margins so the default floor works
on the native method). Small tome margin 0.161 (vs the 13-pair chain 0.072) -> COHERENT; route-to-best sends
a,b->tome1 / p,q->tome2 / m,n->tome3; unknown ctx -> STOP (honest). srmech rc79; no numpy."""
import random
from srmech.rbs_lm import RBSLMInferenceSubstrate
def fl(q): return q.as_float() if hasattr(q,'as_float') else float(q)
def mk(corpus, cap=64):
    p={'substrate':{'D':8192,'token_seed_hex_chars':16},'inference':{'instrument':{'operating_k':2,'operating_temperature':0.0,'memory_capacity':cap,'default_max_tokens':12,'learn_seed':1}}}
    s=RBSLMInferenceSubstrate.from_params(p); s.learn(corpus.split()); return s
tomes=[mk('a b c d e a b c d e'), mk('p q r s t p q r s t'), mk('m n o m n o m n o')]
def routed(context):
    best=None
    for s in tomes:
        r=s.next_token_coherence(context)              # DEFAULT floor, no tuning
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
r=tomes[0].next_token_coherence(['a','b'])
print('small tome ctx[a,b]: verdict=%s margin=%.3f top1_floor_gap=%.3f'%(r.verdict, fl(r.collapse_margin), fl(r.top1_floor_gap)))
for seed in (['a','b'],['p','q'],['m','n'],['zz','yy']):
    print('   from %-7s:'%(','.join(seed)), ' '.join(walk(seed)))

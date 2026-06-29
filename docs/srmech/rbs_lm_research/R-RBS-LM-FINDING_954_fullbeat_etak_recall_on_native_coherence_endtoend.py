"""F954 — the full-beat etak recall now runs END-TO-END on NATIVE next_token_coherence (F953/§78): each step
the verdict drives the action -- COHERENT -> emit top1, BRANCH -> sample branch_candidates, STOP -> honest-
stop. Default floor (0.34 = chance 0.25 + band 0.09) sits below the saturated shadow -> BRANCH-wander; a
TUNED floor (0.42, separating the clean top1=0.468 from the shadow top2=0.395) -> clean COHERENT cyclic walk.
Saturated real corpus (F946 top1~0.40) under the tuned floor -> STOP (honest). Principled no-tune fix =
CHUNKING (F947, margins 0.74 >> any floor). Replaces the F941-F945 recompute-from-M wrapper. srmech rc79."""
import random
from srmech.rbs_lm import RBSLMInferenceSubstrate
from srmech.amsc.q import Q
def walk(sub, prompt, nf=None, max_tokens=12, seed=0):
    out=list(prompt); gr=random.Random(seed); tr=[]
    for _ in range(max_tokens):
        r=sub.next_token_coherence(out, noise_floor=nf) if nf is not None else sub.next_token_coherence(out)
        if r.verdict=='STOP': tr.append('<STOP>'); break
        nxt=gr.choice(r.branch_candidates) if (r.verdict=='BRANCH' and r.branch_candidates) else r.candidates_topk[0]
        tr.append(nxt+('~' if r.verdict=='BRANCH' else '')); out.append(nxt)
    return tr
p={'substrate':{'D':8192,'token_seed_hex_chars':16},'inference':{'instrument':{'operating_k':2,'operating_temperature':0.0,'memory_capacity':256,'default_max_tokens':12,'learn_seed':1}}}
sub=RBSLMInferenceSubstrate.from_params(p); sub.learn('a b c d e a b c d e a b c d e'.split())
print('chain DEFAULT floor 0.34 :', ' '.join(walk(sub,['a','b'])), '  (BRANCH-wander)')
print('chain TUNED   floor 0.42 :', ' '.join(walk(sub,['a','b'], nf=Q(42,100))), '  (clean COHERENT cyclic walk)')

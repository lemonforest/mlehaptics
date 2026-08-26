"""F961 — the n-gram IS dynamic (no srmech fix needed): operating_k = 1/2/3/4 all work, AND more context
SHARPENS the collapse -- k=2 margin 0.072 (BRANCH) -> k=3 0.205 (COHERENT) -> k=4 0.277 (COHERENT). So the
BRANCH-wander (F954/F957) was partly a LOW-k artifact (k=2 default). 'Dynamic n-gram' resolution: typically
k=1/2, ESCALATE to k=3 when the now branches (low margin) -> more context disambiguates -> COHERENT. This is
ORTHOGONAL to the function-word handlings (drop/absorb/down-weight, F959). srmech rc79."""
from srmech.rbs_lm import RBSLMInferenceSubstrate
def fl(q): return q.as_float() if hasattr(q,'as_float') else float(q)
corpus='a b c d e a b c d e a b c d e'.split()
for k in (1,2,3,4):
    p={'substrate':{'D':8192,'token_seed_hex_chars':16},'inference':{'instrument':{'operating_k':k,'operating_temperature':0.0,'memory_capacity':256,'default_max_tokens':6,'learn_seed':1}}}
    s=RBSLMInferenceSubstrate.from_params(p); s.learn(corpus)
    r=s.next_token_coherence(['a','b','c','d'][:k])
    print('operating_k=%d -> top=%s margin=%.3f verdict=%s'%(k, r.candidates_topk[0], fl(r.collapse_margin), r.verdict))
print('=> n-gram dynamic (k=1..4 OK); margin RISES with k (more context = sharper collapse) -> escalate-k disambiguates')

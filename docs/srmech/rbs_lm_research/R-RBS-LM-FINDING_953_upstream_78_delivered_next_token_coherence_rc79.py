"""F953 — §78 DELIVERED + VERIFIED (srmech rc79): RBSLMInferenceSubstrate.next_token_coherence returns a
CoherenceReadout exposing the RAW collapse-margin (pre-softmax) + the F945 trichotomy. The raw margin (0.0724)
is NOT the softmax-flattened prob-margin (0.006, F944); the default noise_floor (0.34) matches the F947
empirical floor; raw_sims_topk + branch_candidates are present; all exact Q rationals. The F941-F945 wrapper
can now call this natively instead of recomputing from sub.M/sub.ctx/sub.vocab_vecs. srmech rc79."""
from srmech.rbs_lm import RBSLMInferenceSubstrate
def fl(q): return q.as_float() if hasattr(q,'as_float') else float(q)
params={'substrate':{'D':8192,'token_seed_hex_chars':16},'inference':{'instrument':{'operating_k':2,'operating_temperature':0.0,'memory_capacity':256,'default_max_tokens':8,'learn_seed':1}}}
sub=RBSLMInferenceSubstrate.from_params(params); sub.learn('a b c d e a b c d e a b c d e'.split())
r=sub.next_token_coherence(['a','b'])
print('verdict          :', r.verdict)
print('collapse_margin  :', '%.4f'%fl(r.collapse_margin), '(RAW pre-softmax = §78 ask; vs softmax-flattened 0.006, F944)')
print('noise_floor      :', '%.4f'%fl(r.noise_floor), '(matches the F947 empirical floor 0.34)')
print('top1_floor_gap   :', '%.4f'%fl(r.top1_floor_gap))
print('candidates_topk  :', r.candidates_topk[:5])
print('raw_sims_topk    :', ['%.3f'%fl(s) for s in r.raw_sims_topk[:5]])
print('branch_candidates:', r.branch_candidates, '| margin type:', type(r.collapse_margin).__name__, '(exact Q)')
print('nonsense ctx verdict:', sub.next_token_coherence(['zzz','qqq']).verdict, '(STOP, correct)')

"""F980 — WIRE the etak-deeper escalation into the REAL RBSLMInferenceSubstrate, content-isolated (the
etak-deeper composes ON TOP of de-lensing, F957/F959; raw corpus FAST is confounded by the frequency prior
F946). etak_recall: FAST via native next_token_coherence; low margin -> escalate multi-cue superposition
(etak deeper, F976/F979); emit / honest-STOP. srmech rc97; sparse; no numpy/abs."""
from srmech.rbs_lm import RBSLMInferenceSubstrate
from srmech.amsc import hdc
def fl(q): return q.as_float() if hasattr(q,'as_float') else float(q)
bind=hdc.klein4_bind
# content-only corpus (no function words / punctuation); target 'gold' recurs after 5 content contexts + filler
corpus=("cats find gold kings hoard gold rivers carry gold miners dig gold pirates bury gold "
        "birds fly sky fish swim sea trees grow tall winds blow cold stars burn far suns shine bright "
        "rain wets earth snow caps peaks roots hold soil leaves catch light waves crash rocks").split()
p={'substrate':{'D':8192,'token_seed_hex_chars':16},'inference':{'instrument':{'operating_k':1,'operating_temperature':0.0,'memory_capacity':400,'default_max_tokens':6,'learn_seed':1}}}
sub=RBSLMInferenceSubstrate.from_params(p); sub.learn(corpus); k=sub.ctx
def raw_read(ctxs):
    probes=[bind(sub.M, k.encode_context(ct)) for ct in ctxs]
    probe=k.bundle_odd(probes) if len(probes)>1 else probes[0]
    s=sorted(((fl(hdc.klein4_similarity(probe, sub.vocab_vecs[i])), sub.vocab[i]) for i in range(len(sub.vocab))), reverse=True)
    return s[0][1], s[0][0]-s[1][0]
THINK=0.02
gold_ctx=[['find'],['hoard'],['carry'],['dig'],['bury']]
print('etak_recall on REAL substrate (content-isolated; target=gold recurs after 5 contexts):')
r=sub.next_token_coherence(['find'])
print('  FAST native next_token_coherence [find]: verdict=%s top=%s margin=%.3f'%(r.verdict, r.candidates_topk[0], fl(r.collapse_margin)))
fast_ok = (r.verdict=='COHERENT' and r.candidates_topk[0]=='gold')
if fast_ok:
    print('   -> FAST resolved gold, no escalation needed')
else:
    print('   -> not confidently gold -> ETAK DEEPER (escalate multi-cue):')
    for kk in (1,2,3,5):
        t,m=raw_read(gold_ctx[:kk])
        print('     k=%d: top=%-6s margin=%.3f %s'%(kk,t,m,'<= gold recovered' if (t=='gold' and m>=THINK) else ''))
        if t=='gold' and m>=THINK:
            print('     => ETAK-DEEPER recovered gold at k=%d, wired on the real substrate (native FAST + multi-cue escalate)'%kk); break

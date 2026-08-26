"""F946 (research note) — at REAL-corpus scale the single-bundle resonator SATURATES to the frequency prior,
and the collapse-margin trichotomy correctly diagnoses it. simplewiki slice (2500 tokens -> 818 vocab, 1500
context->next pairs in ONE bundle): EVERY context -- including nonsense ['xyzzy','qwerty'] -- returns the
same high-frequency FUNCTION WORDS (an/on/in/of) at sim ~0.37, floor ~0.31, margin ~0.00. The bundle is hard
against the F896 wall, so it returns the unigram frequency prior, not the context-conditioned next; the
trichotomy reads top1-barely-above-floor + margin~0 = NOT coherent (it does not falsely emit). srmech rc58."""
import json, statistics as st
from srmech.amsc import hdc
from srmech.rbs_lm import RBSLMInferenceSubstrate
D=8192; bind=hdc.klein4_bind
def fl(q): return q.as_float() if hasattr(q,'as_float') else float(q)
path='/home/skirklan/corpora/wikipedia/simplewiki_fullbody_instrument.ndjson'
toks=[]
with open(path) as f:
    for line in f:
        toks.extend(json.loads(line)['s'].split())
        if len(toks)>=2500: break
toks=toks[:2500]
params={'substrate':{'D':D,'token_seed_hex_chars':16},'inference':{'instrument':{'operating_k':2,'operating_temperature':0.0,'memory_capacity':1500,'default_max_tokens':12,'learn_seed':1}}}
sub=RBSLMInferenceSubstrate.from_params(params); sub.learn(toks); k=2
print('vocab=%d; learned=%d pairs (one bundle)'%(len(sub.vocab), sub.n_learned))
def step(ctx):
    probe=bind(sub.M, sub.ctx.encode_context(ctx[-k:]))
    s=sorted(((fl(hdc.klein4_similarity(probe, sub.vocab_vecs[i])), sub.vocab[i]) for i in range(len(sub.vocab))), reverse=True)
    return s, st.median([v for v,_ in s])
for seed in [['the','fourth'],['is','the'],['between','march'],['xyzzy','qwerty']]:
    s,med=step(seed); print('  ctx %-18s floor=%.2f top %s margin %.2f -> top1 only %.2f above floor = NOT coherent'%(str(seed),med,[(t,round(v,2)) for v,t in s[:3]],s[0][0]-s[1][0],s[0][0]-med))

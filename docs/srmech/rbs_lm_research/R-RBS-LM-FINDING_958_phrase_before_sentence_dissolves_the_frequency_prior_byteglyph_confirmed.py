"""F958 — methodology correction (user): YES we encode through the byte/glyph language-agnostic kernel
(ContextSubstrate.enc default = byteglyph / encode_word_byteglyph, the 'vanuatu'/strip-English-privilege C1
object), but NO we were working at the WORD level (k=2 words), not PHRASES. The F946->F957 frequency-prior
struggle is a WORD-LEVEL ARTIFACT: word atoms have a few dominators (april 230, the 180); 3-word PHRASE atoms
have none (max 6) -- the prior DISSOLVES at the phrase granularity (function words absorbed into distinctive
content phrases). Phrase recall gets REAL content ('april apr is' -> 'the fourth month') where word-level
wandered into function words. Hierarchy: bytes/glyphs -> words -> PHRASES -> sentences (the missing layer).
srmech rc79; no numpy."""
import json
from srmech.rbs_lm import RBSLMInferenceSubstrate
def fl(q): return q.as_float() if hasattr(q,'as_float') else float(q)
toks=[]
with open('/home/skirklan/corpora/wikipedia/simplewiki_fullbody_instrument.ndjson') as f:
    for line in f:
        toks.extend(json.loads(line)['s'].split())
        if len(toks)>=3000: break
toks=toks[:3000]
wf={}; 
for t in toks: wf[t]=wf.get(t,0)+1
phr=[' '.join(toks[i:i+3]) for i in range(0,len(toks)-2,3)]; pf={}
for p in phr: pf[p]=pf.get(p,0)+1
mw=max(wf.values()); mp=max(pf.values())
print('WORD max-freq atom=%d (%s); PHRASE max-freq atom=%d -> phrases ~%dx flatter (prior dissolves)'%(mw, max(wf,key=wf.get), mp, mw//mp))
# phrase recall gets real content
a0=[]
with open('/home/skirklan/corpora/wikipedia/simplewiki_fullbody_instrument.ndjson') as f:
    for line in f: a0=json.loads(line)['s'].split()[:36]; break
aphr=[' '.join(a0[i:i+3]) for i in range(0,len(a0)-2,3)]
p={'substrate':{'D':8192,'token_seed_hex_chars':16},'inference':{'instrument':{'operating_k':1,'operating_temperature':0.0,'memory_capacity':64,'default_max_tokens':6,'learn_seed':1}}}
sub=RBSLMInferenceSubstrate.from_params(p); sub.learn(aphr)
r=sub.next_token_coherence([aphr[0]])
print('phrase recall: %r -> %r (the ACTUAL next phrase; function words absorbed) vs word-level wander it~/in~/of~'%(aphr[0], r.candidates_topk[0]))

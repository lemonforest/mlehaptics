"""F964 (arc opener) — inference-as-translation: force the simplewiki knowledge Laplacian through a stepwise
knowledge->communication hierarchy (bonded knowledge -> ASL-gloss content-dense -> English surface) and test
whether 'inference' is really the translation cascade. First data point: recall coherence of the KNOWLEDGE
layer (content tokens, function words dropped = the bonded relationships) vs the ENGLISH SURFACE (all tokens).
Knowledge mean-margin 0.010 > surface 0.006 -- DIRECTIONAL support (bonded knowledge more coherent than the
surface projection) but WEAK: both saturate at single-M (F946), so this is a lean not a result; the real test
is chunked knowledge tomes (F960) + the 3-layer ASL-middle hierarchy. srmech rc97; sparse; no numpy."""
import json
from srmech.rbs_lm import RBSLMInferenceSubstrate
def fl(q): return q.as_float() if hasattr(q,'as_float') else float(q)
stop=set('the of in a is and to as for on it was were are that with by an at from or be this which his her its he she they we you i not no but have has had will would can could s'.split())
toks=[]
with open('/home/skirklan/corpora/wikipedia/simplewiki_fullbody_instrument.ndjson') as f:
    for line in f:
        toks.extend(json.loads(line)['s'].split())
        if len(toks)>=1200: break
toks=toks[:1200]; know=[t for t in toks if t not in stop]
def build(stream):
    p={'substrate':{'D':8192,'token_seed_hex_chars':16},'inference':{'instrument':{'operating_k':2,'operating_temperature':0.0,'memory_capacity':len(stream),'default_max_tokens':6,'learn_seed':1}}}
    s=RBSLMInferenceSubstrate.from_params(p); s.learn(stream); return s
def coh(sub, stream, n=8):
    v={}; ms=[]
    for i in range(0,n*15,15):
        c=stream[i:i+2]
        if len(c)<2: break
        r=sub.next_token_coherence(c); v[r.verdict]=v.get(r.verdict,0)+1; ms.append(fl(r.collapse_margin))
    return v, sum(ms)/len(ms)
vk,mk=coh(build(know),know); ve,me=coh(build(toks),toks)
print('KNOWLEDGE (content-only): %s mean-margin %.3f'%(vk,mk))
print('ENGLISH  surface (all)  : %s mean-margin %.3f'%(ve,me))
print('knowledge > surface:', mk>me, '(directional; both weak = single-M saturation F946 -> chunk for the real test)')

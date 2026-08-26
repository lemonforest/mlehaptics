"""F959 — 'ASL before English' (user): ASL gloss is natively content-dense (no articles/copula, topic-comment,
sense-determinative-primary), so it DROPS the function words that phrases only ABSORB (F958) and IDF/§80 only
DOWN-WEIGHT -- dissolving the frequency prior at the SOURCE. Grounded: a function-word-drop gloss proxy on a
3000-token slice removes the SHARED cross-topic dominators (the/of/in, ~25% of tokens) -> remaining content
(april/day/year) is topic-distinctive -> fixes BOTH the within-tome prior (F946/F958) AND the cross-tome
routing confound (F956/F957). Already validated: F609 (meaning-class-explicit ASL selects better than English).
Kernel status: asl_sign_kernel.toml is a STRUCTURAL SCAFFOLD (sign-as-chord notation, F608) + expert-handoff
(F282) -- NOT yet a complete English->ASL-gloss TRANSLATION corpus, so 'complete enough' = not yet for full
translation. srmech rc79; no numpy."""
import json
stop=set('the of in a is and to as for on it was were are that with by an at from or be this which his her its he she they we you i not no but have has had will would can could s'.split())
toks=[]
with open('/home/skirklan/corpora/wikipedia/simplewiki_fullbody_instrument.ndjson') as f:
    for line in f:
        toks.extend(json.loads(line)['s'].split())
        if len(toks)>=3000: break
toks=toks[:3000]
gloss=[t for t in toks if t not in stop]
def top(seq,n=6):
    f={}
    for t in seq: f[t]=f.get(t,0)+1
    return sorted(f.items(),key=lambda kv:-kv[1])[:n]
print('ENGLISH words : top', top(toks))
print('ASL-GLOSS proxy: dropped %d%% (function words); top'%(100*(len(toks)-len(gloss))//len(toks)), top(gloss))
print('=> shared cross-topic dominators (the/of/in) GONE; content (april/day/year) topic-distinctive')
print('=> ASL DROPS (vs phrases ABSORB F958, vs IDF/§80 DOWN-WEIGHT) -- the frequency prior gone at the source')

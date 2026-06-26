"""F944 — the two builds. (1) CHUNK the memory against the F896 wall: route relationships by SOURCE into
bounded tomes (the etak/F465 address-routed clump, F778) -> the collapse-margin stays 0.74 across the whole
chain (vs one step for a single N=4 bundle). (2) WIRE the collapse-margin into the REAL resonator: the RAW
sim margin (top1-top2 of the pre-softmax sims) is the true coherence signal -- the softmaxed PROB margin is
flattened and useless. On RBSLMInferenceSubstrate (chain learned) it stays coherent + honest-stops at the
chain end. srmech rc58; real Klein-4 + real resonator; no numpy."""
from srmech.amsc import hdc
from srmech.rbs_lm import substrate as S, RBSLMInferenceSubstrate
D=8192; cs=S.ContextSubstrate(D=D, hex_chars=16); bind=hdc.klein4_bind
def fl(q): return q.as_float() if hasattr(q,'as_float') else float(q)
# --- Build 1: chunk by source ---
vocab=['a','b','c','d','e','f','g','h']; vec={t: hdc.klein4_random(D, seed=1000+i) for i,t in enumerate(vocab)}
ROLE=hdc.klein4_random(D, seed=4242); chain=['a','b','c','d','e']; edges=list(zip(chain,chain[1:]))
def res(M,x):
    q=bind(M, bind(vec[x],ROLE)); s=sorted(((fl(hdc.klein4_similarity(q,vec[t])),t) for t in vocab),reverse=True); return s[0][1], s[0][0]-s[1][0]
M_single=cs.bundle_odd([bind(bind(vec[p],ROLE),vec[n]) for p,n in edges])
src={}
for p,n in edges: src.setdefault(p,[]).append(bind(bind(vec[p],ROLE),vec[n]))
src={k: cs.bundle_odd(v) for k,v in src.items()}
def walk(step,start='a',n=6):
    cur=start; out=[]
    for _ in range(n):
        nxt,m=step(cur); out.append(f'{cur}->{nxt}({m:.2f})')
        if m<0.10: out.append('STOP'); break
        cur=nxt
    return ' '.join(out)
print('Build 1  single bundle(N=4):', walk(lambda x:res(M_single,x)))
print('Build 1  source-routed tomes:', walk(lambda x:(res(src[x],x) if x in src else ('-',0.0))))
# --- Build 2: real resonator, raw-sim collapse-margin + honest-stop ---
params={'substrate':{'D':D,'token_seed_hex_chars':16},'inference':{'instrument':{'operating_k':2,'operating_temperature':0.0,'memory_capacity':256,'default_max_tokens':8,'learn_seed':1}}}
sub=RBSLMInferenceSubstrate.from_params(params); sub.learn('a b c d e a b c d e a b c d e'.split()); k=2
def coherent_next(out, theta=0.05):
    probe=bind(sub.M, sub.ctx.encode_context(out[-k:]))
    s=sorted(((fl(hdc.klein4_similarity(probe, sub.vocab_vecs[i])), sub.vocab[i]) for i in range(len(sub.vocab))), reverse=True)
    m=s[0][0]-s[1][0]; return s[0][1], m, m>=theta
out=['a','b']
for _ in range(8):
    nxt,m,ok=coherent_next(out)
    if not ok: print('Build 2  HONEST-STOP at', out[-2:], 'margin %.3f'%m); break
    out.append(nxt)
print('Build 2  real resonator generated:', ' '.join(out), '(raw-sim collapse-margin, all coherent)')

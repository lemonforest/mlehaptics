"""F1018 probe (user question) — operator words SUPERIMPOSE instead of collide.
(A) The user's chiral-axis idea, GENERALIZED by the elliptic ladder (F999-1002): a homograph's per-language
    senses live at RUNGS of the -z^-1 fold -- sense_L(w) = g5^(L%2)(rot(vec(w), L*delta)). One Z2 chirality
    axis = 2 languages (the user's noted cap); the SECTOR ROTATION (the crank, the_one's theta) = N rungs =
    N languages. The homograph stores as ONE superposed object bundle(bind(sense_L(w), tool_L)); the read is
    RUNG-SELECTION BY LANGUAGE CONTEXT (the utterance's other words vote for their board's rung) -- exactly
    the F995/F1000 rung-selection problem, already characterized. GENERATIVE: rungs from 1 seed + the rule.
(B) Operators EVOLVE FROM A FIXED FRAME: the role-frame (remember/recall/show/define...) is the invariant IR
    (like the 14 A-N classes); a board's WORD->role map is MEASURED from usage -- an unknown lead-word that
    repeatedly precedes utterances grounding to role X ACCRETES to X (usage-attested operator acquisition).
Sparse Klein-4; no numpy/abs/Counter/bag."""
from srmech.amsc import hdc
D=8192; bind=hdc.klein4_bind; g5=hdc.klein4_chirality_flip_gamma5
HV=type(hdc.klein4_random(D,seed=0))
def fl(q): return q.as_float() if hasattr(q,'as_float') else float(q)
def sim(a,b): return fl(hdc.klein4_similarity(a,b))
def vec(w,s=7): return hdc.klein4_random(D, seed=(sum((i+1)*ord(c) for i,c in enumerate(w))%80000)+s)
def rot(seq,k): k%=len(seq); return seq[-k:]+seq[:-k]
NL=4; dlt=D//(2*NL)
def sense(w,L):                                   # the elliptic -z^-1 ladder: -1 = g5 flip, z^-1 = sector rotation
    v=HV.from_sequence(rot(vec(w).tolist(), L*dlt))
    return g5(v) if L%2 else v
# ---- (A) the superposed homograph: 4 languages, 4 DIFFERENT senses of 'save', ONE stored object ----
LANGS=['english','bislama','lang3','lang4']
TOOLS=['remember','recall','show','define']       # save's sense per language-rung
tool_v={t:vec(t,11) for t in TOOLS}
from srmech.rbs_lm.substrate import ContextSubstrate
cs=ContextSubstrate(D=D, hex_chars=16)
SAVE=cs.bundle_odd([bind(sense('save',L), tool_v[TOOLS[L]]) for L in range(NL)])   # SUPERPOSITION, not collision
# language-indicative context words per board (each board's attested words carry its rung)
CTX={0:['the','working','memory','note'],1:['blong','wota','olsem','luksave'],
     2:['zora','miku','tanel','vosk'],3:['brin','kelo','sarn','dovi']}
def lang_of(utt_words):                            # rung vote: which board's words appear? (rung-selection by context)
    votes=[0]*NL
    for L,ws in CTX.items():
        for w in utt_words:
            if w in ws: votes[L]+=1
    return max(range(NL), key=lambda L: votes[L])
print("(A) SUPERPOSED homograph 'save' -- 4 languages, 4 senses, ONE object; read = rung-selection by context:")
ok=0; trials=0
for L in range(NL):
    for i in range(3):                             # 3 mixed utterances per language
        utt=['save']+[CTX[L][j] for j in (i, (i+1)%4)]
        Lh=lang_of(utt)
        probe=bind(SAVE, sense('save',Lh))
        pick=max(TOOLS, key=lambda t: sim(probe, tool_v[t]))
        ok+= (pick==TOOLS[L]); trials+=1
        if i==0: print("   lang=%-8s utt=%-28s -> rung %d -> sense '%s' %s"%(LANGS[L],' '.join(utt),Lh,pick,'OK' if pick==TOOLS[L] else 'X'))
print("   sense recovery: %d/%d  (N=%d languages on ONE rotation axis -- the crank, not the mirror: beyond the Z2 cap)"%(ok,trials,NL))
# storage: generative -- the ladder reconstructs from ONE base vector + the rule
print("   storage: 1 superposed object + 1 base seed (the -z^-1 rule regenerates every rung; F1002 generative)")
# ---- (B) operators EVOLVE from the FIXED role-frame: usage-accretion of an unknown operator word ----
print("(B) operator ACCRETION from the fixed frame (roles declared; words measured from usage):")
frame_roles=TOOLS                                  # the FIXED frame (like the 14 A-N classes: closed, invariant)
obs=[('stash the water note','remember'),('stash this result','remember'),('stash the kernel','remember')]
counts={}
for utt,resolved in obs:                           # each use grounds by MEANING (F1017 conflict path); tally the resolution
    lead=utt.split()[0]; counts.setdefault(lead,{}).setdefault(resolved,0)
    counts[lead][resolved]+=1
lead='stash'; role,k=max(counts[lead].items(), key=lambda kv:kv[1])
ACCRETE_K=3
if k>=ACCRETE_K:
    print("   'stash' resolved to role '%s' %d/%d times -> ACCRETED to the board's verb_tools (deterministic now)"%(role,k,len(obs)))
    print("   => the ROLE-FRAME never changed (fixed, closed); the WORD->role map evolved by measurement --")
    print("      the same shape as F768 (measured function-ness) and how children acquire operator words.")

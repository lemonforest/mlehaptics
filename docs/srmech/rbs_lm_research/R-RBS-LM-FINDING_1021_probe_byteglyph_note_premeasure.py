"""PKG-2 gate: BYTEGLYPH NOTE-ENCODING pre-measurement (the water~wota cross-language content bridge).
The tool-index measurement (F1017) REJECTED byteglyph vectors there (+0.130 Gram cross-talk). The memory-note
surface is different (fewer, longer objects) -- measure it on ITS OWN terms before wiring. Decision rule
(pre-committed): adopt iff (i) distinct-note Gram <= token-baseline + 0.05 AND (ii) the cross-language query
ranks the target note top-1 with same-language controls unhurt. Variants: token-exact (current) / byteglyph /
HYBRID (bundle both). Sparse Klein-4; order-carrying (uni+bigram) in all variants."""
from srmech.amsc import hdc
from srmech.rbs_lm.substrate import ContextSubstrate
D=8192; cs=ContextSubstrate(D=D, hex_chars=16); bind=hdc.klein4_bind
def fl(q): return q.as_float() if hasattr(q,'as_float') else float(q)
def sim(a,b): return fl(hdc.klein4_similarity(a,b))
def toks(s): return [w for w in s.lower().split() if w]
def tvec(w): return hdc.klein4_random(D, seed=(sum((i+1)*ord(c) for i,c in enumerate(w))%80000)+7)
def enc(ws, mode):
    parts=[]
    for w in ws:
        if mode in ('token','hybrid'): parts.append(tvec(w))
        if mode in ('glyph','hybrid'): parts.append(cs.enc(w))
    for a,b in zip(ws,ws[1:]): parts.append(bind(tvec(a),tvec(b)))   # order bigrams (token-keyed, all modes)
    return cs.bundle_odd(parts or [tvec('_')])
NOTES=["wota i boela long 100 selsius","chess is a game of 64 squares","the pope lives in the vatican",
       "gcd result was twelve","kernel fahrenheit is celsius times 9 over 5 plus 32",
       "ol pikinini oli gat raet long edukesen","the fiedler vector splits a graph",
       "sipos yu wantem save moa yu ridim buk"]
QUERIES=[("water boiling","wota i boela long 100 selsius"),          # CROSS-language (eng query, bis note)
         ("education for children","ol pikinini oli gat raet long edukesen"),  # cross (edukesen~education, pikinini~?)
         ("chess game","chess is a game of 64 squares"),             # same-language control
         ("pope vatican","the pope lives in the vatican")]           # same-language control
print("BYTEGLYPH NOTE-ENCODING pre-measurement (decision rule pre-committed):")
for mode in ('token','glyph','hybrid'):
    nv=[(n,enc(toks(n),mode)) for n in NOTES]
    tot=cnt=0.0
    for i in range(len(nv)):
        for j in range(len(nv)):
            if i!=j: tot+=sim(nv[i][1],nv[j][1]); cnt+=1
    gram=tot/cnt
    hits=[]
    for q,want in QUERIES:
        qv=enc(toks(q),mode)
        best=max(nv,key=lambda kv: sim(qv,kv[1]))[0]
        hits.append(best==want)
    cross=sum(hits[:2]); ctrl=sum(hits[2:])
    print("  %-6s: distinct-note Gram %.3f | cross-language %d/2 | same-language controls %d/2"%(mode,gram,cross,ctrl))
print("=> adopt (for NOTE recall only; grounding stays token-exact per F1017) iff a variant meets the rule:")
print("   Gram <= token+0.05 AND cross-language 2/2 AND controls 2/2. Otherwise keep token-exact + record the limit.")

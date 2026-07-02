"""SIONA-INFER-1 (#233) — the intent ROUTER: classify each utterance into {define | tool-call | self-command |
continue} and DISPATCH to the real handler (define -> F1005 depth-read; tool-call -> F1009 drive loop; self-
command -> siona's own memory ops [INFER-4 seed]; continue -> substrate next-token). Design per feedback_
operators_declared_operands_by_meaning: intent markers are OPERATORS (DECLARED closed-class, like reserved
keywords -- distinct from the F768 aboutness-stoplist which was CONTENT and is measured); content routes by
MEANING (grounding sim + operand shape, F1009). Sparse Klein-4; bundle_odd (§82); no numpy/abs/Counter/bag."""
import re, importlib
from srmech.amsc import tool_schema as ts, hdc
from srmech.rbs_lm import substrate as S
D=8192; cs=S.ContextSubstrate(D=D, hex_chars=16); bundle=cs.bundle_odd; bind=hdc.klein4_bind
ROLE=hdc.klein4_random(D, seed=4242)
def fl(q): return q.as_float() if hasattr(q,'as_float') else float(q)
def sim(a,b): return fl(hdc.klein4_similarity(a,b))
def toks(s):
    s=(s or '').lower(); s=re.sub(r'([a-z])([0-9])',r'\1 \2',s); s=re.sub(r'([0-9])([a-z])',r'\1 \2',s)
    return [w for w in re.split(r'[^a-z0-9]+',s) if len(w)>1 or w.isdigit()]
# ---- the INFER-2 grounding index (F1008) ----
tools={t.name:t for t in ts.get_tool_schema().tools}; NT=len(tools)
nm_toks={n:toks(n.split('.')[-1]) for n in tools}; su_toks={n:toks(t.summary) for n,t in tools.items()}
docf={}
for n in tools:
    for w in set(nm_toks[n]+su_toks[n]): docf[w]=docf.get(w,0)+1
FUNC=int(NT*0.35); gate=lambda w: 1.0 if docf.get(w,0)<FUNC else FUNC/docf[w]
gv={}
def vec(w):
    if w not in gv: gv[w]=hdc.klein4_random(D, seed=(sum((i+1)*ord(c) for i,c in enumerate(w))%80000)+7)
    return gv[w]
def bg(ws): return [bind(vec(a),vec(b)) for a,b in zip(ws,ws[1:])]
def enc_tool(n):
    nmw=nm_toks[n]; suw=[w for w in su_toks[n] if gate(w)>=1.0]
    return bundle(([vec(w) for w in nmw]*3 + bg(nmw)*2 + [vec(w) for w in suw] + bg(suw)) or [vec('_')])
def enc_q(u):
    ws=[w for w in toks(u) if gate(w)>=1.0]; return bundle(([vec(w) for w in ws]+bg(ws)) or [vec('_')])
idx=[(n,enc_tool(n)) for n in tools]
def ground(u,k=5): return sorted(((sim(enc_q(u),v),n) for n,v in idx),reverse=True)[:k]
# ---- declared intent OPERATORS (closed-class, by-rule -- reserved keywords, NOT measured content) ----
DEFINE=[('what','is'),('what','are'),('define',),('describe',),('meaning','of'),('tell','me','about'),
        ('who','is'),('who','was'),('explain',)]
SELFV={'remember','recall','forget','ingest','save'}      # siona's own CLI verbs (the INFER-4 surface seed)
ADDR='siona'
DEF_TOKS={w for f in DEFINE for w in f}
def has_define(ws): return any(tuple(ws[:len(f)])==f for f in DEFINE)
def operands(u):
    ints=[int(x) for x in re.findall(r'-?\d+',u)]
    m=re.search(r'(?:bytes|string|text)\s+["\']?([a-z]{2,})["\']?\s*$',u.lower())
    return ints,(m.group(1).encode() if m else None)
IMPV={'list','compute','calculate','run','apply','register','enumerate','build','generate','encode','decode','measure','verify','hash'}  # imperative operators (declared) for the NO-operand tool path
def route(u):
    ws=toks(u)
    if ws and (ws[0]==ADDR or ws[0] in SELFV): return 'self-command'   # ADDRESS/self-verb operator (declared)
    ints,byts=operands(u)
    if has_define(ws) and not (ints or byts): return 'define'          # define-frame w/o operands = depth-read
    if ints or byts: return 'tool-call'                                # operand shape = strong evidence (F1009); define+operands = interrogative tool-call
    if ws and ws[0] in IMPV: return 'tool-call'                        # imperative operator (declared, closed-class)
    return 'continue'                                                  # DEFAULT: no operator frame, no operands
# ---- (A) structural: declared lexicons disjoint + the honest NULL on grounding-threshold routing ----
print("SIONA-INFER-1 -- intent ROUTER {define|tool-call|self-command|continue}:")
print("  (A) declared operator lexicons pairwise DISJOINT: %s  (define∩self=%s; self∩impv=%s; addr unique=%s)"%(
      DEF_TOKS.isdisjoint(SELFV) and DEF_TOKS.isdisjoint(IMPV) and SELFV.isdisjoint(IMPV) and ADDR not in DEF_TOKS|SELFV|IMPV,
      DEF_TOKS&SELFV, SELFV&IMPV, ADDR not in DEF_TOKS|SELFV|IMPV))
mt=[ground(u,1)[0][0] for u in ("list the attested data sources","register an attested catalog root")]
mc=[ground(u,1)[0][0] for u in ("the pope lives in the","april is the fourth month of the","chess is a game of")]
print("      MEASURED + REJECTED: grounding max-sim does NOT separate no-operand tool-asks %s from continues %s"%(
      ['%.2f'%x for x in mt], ['%.2f'%x for x in mc]))
print("      (max over 347 candidates is inflated for short queries -> overlap; router uses DECLARED imperative")
print("       operators + operand shape instead -- no threshold. operators_declared_operands_by_meaning.)")
# ---- (B) routing eval ----
EVAL=[("what is a laplacian","define"),("define chirality","define"),("describe the fiedler vector","define"),
 ("what is prime factorization","define"),("explain the antikythera mechanism","define"),
 ("compute the gcd of 48 and 36","tool-call"),("factor 360 into primes","tool-call"),
 ("sha256 hash of the bytes hello","tool-call"),("what is the gcd of 1071 and 462","tool-call"),
 ("best rational approximation of 355 over 113 with max denominator 100","tool-call"),
 ("list the attested data sources","tool-call"),
 ("siona show your working memory","self-command"),("remember that the pope lives in the vatican","self-command"),
 ("recall what we know about the pope","self-command"),("forget the last note","self-command"),
 ("ingest the note that the elliptic operator is generative","self-command"),
 ("the pope lives in the","continue"),("april is the fourth month of the","continue"),
 ("chess is a game of","continue"),("water flows down the","continue")]
ok=0
print("  (B) routing eval (%d utterances):"%len(EVAL))
for u,want in EVAL:
    got=route(u); hit=got==want; ok+=hit
    print("      %-3s %-58s -> %-12s%s"%('OK' if hit else 'X', u[:58], got, '' if hit else ' (want %s)'%want))
print("  => routing accuracy %d/%d = %.0f%%"%(ok,len(EVAL),100*ok/len(EVAL)))
# ---- (C) DISPATCH: four intents, four REAL handlers, one shared substrate ----
MEM=[]                                                     # never-compacted working memory (INFER-5 seed)
STOP_OPS=DEF_TOKS|SELFV|{'the','a','an','that','your','working','memory','we','know','about','note','last'}
def h_define(u):
    q=' '.join(w for w in toks(u) if w not in STOP_OPS)
    s,n=ground(q,1)[0]; return "%s: %s"%(n.split('.')[-1], (tools[n].summary or '')[:95])
def ptype(p): return p.type.lower().strip()
def h_tool(u):
    ints,byts=operands(u); cands=[n for _,n in ground(u,5)]
    def fit(t):
        reqs=[p for p in t.parameters if p.required]
        if not reqs: return 0.0
        intp=sum(1 for p in reqs if ptype(p)=='int'); bytp=sum(1 for p in reqs if 'bytes' in ptype(p))
        listp=sum(1 for p in reqs if any(k in ptype(p) for k in ('list','sequence','tuple')))
        unsup=len(reqs)-intp-bytp-listp
        if unsup: return 0.0
        if bytp and byts is None: return 0.0
        if listp: return 0.4 if ints else 0.0
        if intp>len(ints): return 0.0
        return 2.0 if (intp==len(ints) and (bytp>0)==(byts is not None)) else 1.0
    scored=sorted(((fit(tools[n]),-cands.index(n),n) for n in cands),reverse=True)
    pick=scored[0][2] if scored[0][0]>0 else cands[0]
    parts=pick.split('.'); fn=None
    for i in range(len(parts),0,-1):
        try:
            obj=importlib.import_module('.'.join(parts[:i]))
            for p in parts[i:]: obj=getattr(obj,p)
            fn=obj; break
        except (ImportError,AttributeError): continue
    args=[]; ii=0
    for p in tools[pick].parameters:
        tp=ptype(p)
        if not p.required and ii>=len(ints): break
        if 'bytes' in tp: args.append(byts)
        elif tp=='int': args.append(ints[ii]); ii+=1
        elif any(k in tp for k in ('list','sequence','tuple')): args.append(ints[ii:]); ii=len(ints)
    try: res=fn(*args)
    except Exception as e: res='ERR %s'%e
    MEM.append('%s%s = %s'%(pick.split('.')[-1],tuple(args),res))
    return "%s%s = %s"%(pick.split('.')[-1], tuple(args), str(res)[:50])
def _mem_M():
    pairs=[]
    for m in MEM:
        ws=[w for w in toks(m) if w not in SELFV and w!='that']
        for i in range(2,len(ws)): pairs.append(bind(cs.encode_context(ws[i-2:i]), vec(ws[i])))  # POSITION-KEYED ctx (F838) -- commutative pair-bind aliased (lives,in)->the to (in,the)->lives = the bag failure mode a 3rd time
    return bundle(pairs) if pairs else None
def h_continue(u):
    M=_mem_M()
    if M is None: return '(no substrate content yet)'
    ws=toks(u); probe=bind(M, cs.encode_context(ws[-2:]))
    vocab=sorted({w for m in MEM for w in toks(m)})
    return max(vocab, key=lambda w: sim(probe,vec(w)))
def h_self(u):
    ws=toks(u); verb=ws[1] if ws and ws[0]==ADDR and len(ws)>1 else (ws[0] if ws else 'show')
    if verb in ('remember','ingest','save'):
        MEM.append(' '.join(w for w in ws if w not in SELFV and w!='that')); return 'noted (%d items in memory)'%len(MEM)
    if verb=='recall':
        q=' '.join(w for w in ws if w not in STOP_OPS)
        if not MEM: return '(memory empty)'
        return 'recall: %s'%max(MEM, key=lambda m: sim(enc_q(q),enc_q(m)))
    if verb=='forget': return 'forgot: %s'%(MEM.pop() if MEM else '(empty)')
    return 'memory (%d): %s'%(len(MEM), ' | '.join(MEM))
H={'define':h_define,'tool-call':h_tool,'self-command':h_self,'continue':h_continue}
print("  (C) DISPATCH -- four intents, four REAL handlers, ONE shared substrate:")
for u in ["remember that the pope lives in the vatican",
          "the pope lives in the",
          "describe the fiedler vector",
          "compute the gcd of 48 and 36",
          "siona show your working memory"]:
    r=route(u); print("      '%s'\n         -> %-12s -> %s"%(u, r, H[r](u)))
print("=> the ROUTER unifies everything built: define->depth-read(F1005) | tool-call->drive(F1009) | self-command->")
print("   siona memory ops (INFER-4 seed) | continue->substrate next-token from the REMEMBERED content. One dispatcher.")

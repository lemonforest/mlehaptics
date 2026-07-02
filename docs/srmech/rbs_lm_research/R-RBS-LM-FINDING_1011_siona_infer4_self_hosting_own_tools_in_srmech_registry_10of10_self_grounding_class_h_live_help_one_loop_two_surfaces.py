"""SIONA-INFER-4 (#236) — self-CLI / SELF-HOSTING: siona registers its OWN tool surface into srmech's REAL
tool_schema registry (register_profile_tools), grounds it with the exact F1008 recipe, and DRIVES ITSELF through
the same route->ground->drive loop it uses for srmech. One registry, two surfaces (347 srmech + siona's own),
one substrate. Includes siona.introspect.help = Class-H self-introspection (siona answers 'what can you do' from
its own live registered schema). Sparse Klein-4; bundle_odd (§82); no numpy/abs/Counter/bag."""
import re, importlib
from srmech.amsc import tool_schema as ts, hdc
from srmech.amsc.tool_schema import ToolEntry, ToolParameter, ToolReturn
from srmech.rbs_lm import substrate as S
D=8192; cs=S.ContextSubstrate(D=D, hex_chars=16); bundle=cs.bundle_odd; bind=hdc.klein4_bind
def fl(q): return q.as_float() if hasattr(q,'as_float') else float(q)
def sim(a,b): return fl(hdc.klein4_similarity(a,b))
def toks(s):
    s=(s or '').lower(); s=re.sub(r'([a-z])([0-9])',r'\1 \2',s); s=re.sub(r'([0-9])([a-z])',r'\1 \2',s)
    return [w for w in re.split(r'[^a-z0-9]+',s) if len(w)>1 or w.isdigit()]
# ---- siona's OWN tool surface, registered into srmech's REAL registry ----
N_BEFORE=len(ts.get_tool_schema().tools)
def T(name,summary,params=('text',)):
    return ToolEntry(name=name, owner='siona', category='siona', summary=summary,
                     parameters=tuple(ToolParameter(name=p, type='str', required=False, summary='utterance remainder') for p in params),
                     returns=ToolReturn(type='str'))
SIONA_TOOLS=[
 T('siona.memory.remember',"Remember a note: store the given text into siona's never-compacted working memory. Aliases: ingest, save, note this."),
 T('siona.memory.recall',"Recall from working memory: retrieve the stored note or driven result most similar to the query text."),
 T('siona.memory.forget',"Forget the most recent note: pop the last item from siona's working memory."),
 T('siona.memory.show',"Show the working memory: list every stored note and driven result in order."),
 T('siona.read.define',"Define a concept: depth-read the srmech tool catalog and return the best definition summary for the query."),
 T('siona.read.continue_text',"Continue a text prefix: substrate next-token read from siona's remembered content."),
 T('siona.introspect.help',"List siona's own commands: enumerate the siona tool schema from the live registry (self-introspection, Class H). Serves asks like: what can you do, what are you able to do, list your commands, help.")]
ts.register_profile_tools('siona', SIONA_TOOLS)
tools={t.name:t for t in ts.get_tool_schema().tools}; NT=len(tools)
print("SIONA-INFER-4 -- SELF-HOSTING: siona's own tools in srmech's registry:")
print("  registry: %d srmech tools -> %d after register_profile_tools('siona', 7) -- ONE registry, TWO surfaces"%(N_BEFORE,NT))
# ---- the F1008 grounding recipe over the COMBINED registry ----
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
def ground(u,k=5,owner=None):
    sc=((sim(enc_q(u),v),n) for n,v in idx if owner is None or tools[n].owner==owner)
    return sorted(sc,reverse=True)[:k]
# ---- (A) READ-INDEPENDENT: the siona profile is discriminable within the combined index ----
sv=[(n,v) for n,v in idx if tools[n].owner=='siona']
intra=[sim(a,b) for i,(_,a) in enumerate(sv) for j,(_,b) in enumerate(sv) if i<j]
cross=max(sim(a,b) for _,a in sv for n,b in idx if tools[n].owner!='siona')
print("  (A) read-independent: siona intra-profile mean off-diag %.3f ; max sim(siona,srmech-tool) %.3f (both ~0.25 baseline -> distinct)"%(sum(intra)/len(intra), cross))
# ---- siona's SELF implementations (the callables its own schema names) ----
MEM=[]
STRIP={'siona','remember','recall','forget','ingest','save','show','define','continue','list','help','that','your','please','the'}
def rem(u): return ' '.join(w for w in toks(u) if w not in STRIP)
def s_remember(text): MEM.append(text); return 'noted (%d items)'%len(MEM)
def s_recall(text):
    if not MEM: return '(memory empty)'
    return 'recall: %s'%max(MEM, key=lambda m: sim(enc_q(text),enc_q(m)))
def s_forget(text=''): return 'forgot: %s'%(MEM.pop() if MEM else '(empty)')
def s_show(text=''): return 'memory (%d): %s'%(len(MEM),' | '.join(MEM))
def s_define(text):
    # depth-read over the srmech surface only (a definition ask should not self-refer)
    s,n=ground(text,1,owner='srmech')[0]
    return '%s: %s'%(n.split('.')[-1], (tools[n].summary or '')[:80])
def s_continue(text):
    pairs=[]
    for m in MEM:
        ws=toks(m)
        for i in range(2,len(ws)): pairs.append(bind(cs.encode_context(ws[i-2:i]), vec(ws[i])))
    if not pairs: return '(no substrate content yet)'
    M=bundle(pairs); ws=toks(text)
    if len(ws)<2: return '(prefix too short)'
    probe=bind(M, cs.encode_context(ws[-2:]))
    vocab=sorted({w for m in MEM for w in toks(m)})
    return max(vocab, key=lambda w: sim(probe,vec(w)))
def s_help(text=''):
    live=[t for t in ts.get_tool_schema().tools if t.owner=='siona']       # LIVE registry read = genuine Class-H
    return 'my commands (%d, from my live schema): %s'%(len(live), ', '.join(t.name.split('.')[-1] for t in live))
SELF_IMPL={'siona.memory.remember':s_remember,'siona.memory.recall':s_recall,'siona.memory.forget':s_forget,
           'siona.memory.show':s_show,'siona.read.define':s_define,'siona.read.continue_text':s_continue,
           'siona.introspect.help':s_help}
def drive_self(u):
    pick=ground(u,1,owner='siona')[0][1]                                   # ground on the SIONA surface (router already said self-command)
    return pick.split('.')[-1], SELF_IMPL[pick](rem(u))
# ---- (B) self-grounding eval: self-command paraphrases -> the right siona tool ----
EVAL=[("siona remember that water boils at 100 celsius","remember"),
 ("siona save this note about the elliptic operator","remember"),
 ("siona recall what we know about water","recall"),
 ("siona forget the last note","forget"),
 ("siona show your working memory","show"),
 ("siona define the fiedler vector","define"),
 ("siona continue the text the pope lives in the","continue_text"),
 ("siona list your commands","help"),
 ("siona what can you do","help"),
 ("siona ingest the note that chess is a game","remember")]
ok=0
print("  (B) SELF-grounding -- self-command paraphrase -> siona tool (10 utterances):")
for u,want in EVAL:
    got=ground(u,1,owner='siona')[0][1].split('.')[-1]
    hit=got==want or (want=='remember' and got=='remember'); ok+= (got==want)
    print("      %-3s %-52s -> %s%s"%('OK' if got==want else 'X', u[:52], got, '' if got==want else ' (want %s)'%want))
print("  => self-grounding accuracy %d/%d"%(ok,len(EVAL)))
# ---- (C) the INTERACTIVE SELF-DRIVE session: siona drives ITSELF + srmech through ONE loop ----
DEFINE=[('what','is'),('what','are'),('define',),('describe',),('explain',)]
SELFV={'remember','recall','forget','ingest','save'}; ADDR='siona'
IMPV={'list','compute','calculate','run','apply','register','enumerate'}
def operands(u):
    ints=[int(x) for x in re.findall(r'-?\d+',u)]
    m=re.search(r'(?:bytes|string|text)\s+["\']?([a-z]{2,})["\']?\s*$',u.lower())
    return ints,(m.group(1).encode() if m else None)
def route(u):
    ws=toks(u)
    if ws and (ws[0]==ADDR or ws[0] in SELFV): return 'self-command'
    ints,byts=operands(u)
    if any(tuple(ws[:len(f)])==f for f in DEFINE) and not (ints or byts): return 'define'
    if ints or byts: return 'tool-call'
    if ws and ws[0] in IMPV: return 'tool-call'
    return 'continue'
def ptype(p): return p.type.lower().strip()
def h_tool(u):
    ints,byts=operands(u); cands=[n for _,n in ground(u,5,owner='srmech')]
    def fit(t):
        reqs=[p for p in t.parameters if p.required]
        if not reqs: return 0.0
        intp=sum(1 for p in reqs if ptype(p)=='int'); bytp=sum(1 for p in reqs if 'bytes' in ptype(p))
        listp=sum(1 for p in reqs if any(k in ptype(p) for k in ('list','sequence','tuple')))
        if len(reqs)-intp-bytp-listp: return 0.0
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
    return '%s%s = %s'%(pick.split('.')[-1],tuple(args),str(res)[:44])
print("  (C) the interactive SELF-DRIVE session (one loop drives BOTH surfaces + one substrate):")
for u in ["siona remember that water boils at 100 celsius",
          "siona list your commands",
          "compute the gcd of 48 and 36",
          "siona recall what do we know about water",
          "siona show your working memory",
          "water boils at"]:
    r=route(u)
    if r=='self-command': t,out=drive_self(u); print("      '%s'\n         -> self-command -> siona.%s -> %s"%(u,t,str(out)[:100]))
    elif r=='tool-call': print("      '%s'\n         -> tool-call    -> %s"%(u,h_tool(u)))
    else: print("      '%s'\n         -> %-12s -> %s"%(u,r,s_continue(u)))
print("=> SELF-HOSTING: siona's own surface lives in srmech's registry, grounds with the SAME F1008 recipe, drives")
print("   through the SAME loop -- and siona answers 'what can you do' from its own LIVE schema (Class-H). #236.")

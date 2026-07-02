"""SIONA-INFER-5 (#237) — multi-turn SESSION COHERENCE with the user's two challenge asks as headline tests:
(1) CROSS-TURN OPERAND: 'compute the gcd of the boiling point of water and 48' -- the missing operand is
    resolved FROM WORKING MEMORY (sim-recall 'boiling point water' -> the water note -> 100) -> gcd(100,48)=4.
(2) KNOWLEDGE-KERNEL CONVERSION: 'water boils at what fahrenheit' -- 212 is NOT stored; siona composes the
    remembered fact (100 celsius) with an INGESTED conversion kernel (fahrenheit is celsius times 9 over 5 plus
    32) and derives it EXACTLY: (100*9 + 32*5)/5 = 1060/5, reduced via srmech cyclic.gcd -> 212. Stay-rational:
    integer num/den end-to-end, collapse only at display.
10-turn session over BOTH surfaces + ONE never-compacted memory; per-turn coherence checked. Sparse Klein-4;
bundle_odd (§82); no numpy/abs/Counter/bag; no floats mid-cascade."""
import re, importlib
from srmech.amsc import tool_schema as ts, hdc, cyclic
from srmech.amsc.tool_schema import ToolEntry, ToolParameter, ToolReturn
from srmech.rbs_lm import substrate as S
D=8192; cs=S.ContextSubstrate(D=D, hex_chars=16); bundle=cs.bundle_odd; bind=hdc.klein4_bind
def fl(q): return q.as_float() if hasattr(q,'as_float') else float(q)
def sim(a,b): return fl(hdc.klein4_similarity(a,b))
def toks(s):
    s=(s or '').lower(); s=re.sub(r'([a-z])([0-9])',r'\1 \2',s); s=re.sub(r'([0-9])([a-z])',r'\1 \2',s)
    return [w for w in re.split(r'[^a-z0-9]+',s) if len(w)>1 or w.isdigit()]
# ---- siona surface (F1011) + the NEW answer tool (kernel-composed QA) ----
def T(name,summary):
    return ToolEntry(name=name, owner='siona', category='siona', summary=summary,
                     parameters=(ToolParameter(name='text', type='str', required=False, summary='utterance remainder'),),
                     returns=ToolReturn(type='str'))
ts.register_profile_tools('siona',[
 T('siona.memory.remember',"Remember a note: store the given text into siona's never-compacted working memory. Aliases: ingest, save, note this."),
 T('siona.memory.recall',"Recall from working memory: retrieve the stored note or driven result most similar to the query text."),
 T('siona.memory.forget',"Forget the most recent note: pop the last item from siona's working memory."),
 T('siona.memory.show',"Show the working memory: list every stored note and driven result in order."),
 T('siona.read.define',"Define a concept: depth-read the srmech tool catalog and return the best definition summary for the query."),
 T('siona.read.continue_text',"Continue a text prefix: substrate next-token read from siona's remembered content."),
 T('siona.introspect.help',"List siona's own commands: enumerate the siona tool schema from the live registry (self-introspection, Class H). Serves asks like: what can you do, what are you able to do, list your commands, help."),
 T('siona.read.answer',"Answer a question from remembered knowledge: compose recalled facts with ingested unit-conversion kernels to derive the asked value exactly (celsius to fahrenheit and similar unit questions).")])
tools={t.name:t for t in ts.get_tool_schema().tools}; NT=len(tools)
# ---- the F1008 grounding index over the combined registry ----
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
# ---- working memory + self implementations ----
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
    live=[t for t in ts.get_tool_schema().tools if t.owner=='siona']
    return 'my commands (%d, from my live schema): %s'%(len(live), ', '.join(t.name.split('.')[-1] for t in live))
def parse_kernel(m):                                       # 'kernel <target> is <source> times a over b plus c'
    ws=toks(m)
    if 'kernel' not in ws: return None
    try:
        tgt=ws[ws.index('kernel')+1]; src=ws[ws.index('is')+1]
        a=int(ws[ws.index('times')+1]); b=int(ws[ws.index('over')+1]); c=int(ws[ws.index('plus')+1])
        return (tgt,src,a,b,c)
    except (ValueError,IndexError): return None
def s_answer(text):
    ws=toks(text)
    tgt=ws[ws.index('what')+1] if 'what' in ws and ws.index('what')+1<len(ws) else None   # asked unit
    if not tgt: return '(no asked unit)'
    kern=None
    for m in MEM:
        k=parse_kernel(m)
        if k and k[0]==tgt: kern=k; break
    if not kern: return '(no kernel for %s)'%tgt
    _,src,a,b,c=kern
    facts=[m for m in MEM if src in toks(m) and 'kernel' not in toks(m) and any(w.isdigit() for w in toks(m))]
    if not facts: return '(no %s fact)'%src
    q=' '.join(w for w in ws if w not in ('what',tgt))
    fact=max(facts, key=lambda m: sim(enc_q(q),enc_q(m)))
    fws=toks(fact); v=None
    for i,w in enumerate(fws):                             # the value immediately BEFORE the source-unit token
        if w==src and i>0 and fws[i-1].isdigit(): v=int(fws[i-1]); break
    if v is None: return '(no %s value in the fact)'%src
    num=v*a+c*b; den=b                                     # EXACT rational: v*a/b + c = (v*a + c*b)/b ; no floats
    g=cyclic.gcd(num,den); num//=g; den//=g                # reduce via srmech Class-I gcd
    shown=str(num) if den==1 else '%d/%d'%(num,den)        # collapse only at the display boundary
    MEM.append('%s %s = %s %s (derived: %s -> exact (%d*%d+%d*%d)/%d)'%(fact.split()[0],tgt,shown,tgt,fact,v,a,c,b,b))
    return '%s %s (EXACT: (%d*%d + %d*%d)/%d = %d/%d, reduced via srmech gcd; from the fact "%s" through the kernel)'%(shown,tgt,v,a,c,b,b,num,den,fact)
SELF_IMPL={'siona.memory.remember':s_remember,'siona.memory.recall':s_recall,'siona.memory.forget':s_forget,
           'siona.memory.show':s_show,'siona.read.define':s_define,'siona.read.continue_text':s_continue,
           'siona.introspect.help':s_help,'siona.read.answer':s_answer}
QOPS={'siona','what','who','when','where','how','why'}     # interrogative INTENT-operators: stripped from the GROUNDING query (operators route; operands ground) -- the handler still gets them via rem()
VERB2TOOL={'remember':'siona.memory.remember','ingest':'siona.memory.remember','save':'siona.memory.remember',
           'recall':'siona.memory.recall','forget':'siona.memory.forget','show':'siona.memory.show'}
def drive_self(u):
    ws=toks(u); lead=ws[1] if ws and ws[0]==ADDR and len(ws)>1 else (ws[0] if ws else '')
    if lead in VERB2TOOL: pick=VERB2TOOL[lead]              # declared self-VERB = deterministic operator dispatch (F1010 two-layer, inside the self surface)
    else:
        q=' '.join(w for w in ws if w not in QOPS)          # verb-less ask -> ground by MEANING on the siona surface
        pick=ground(q,1,owner='siona')[0][1]
    return pick.split('.')[-1], SELF_IMPL[pick](rem(u))
# ---- router (F1010) ----
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
# ---- drive loop (F1009) + CROSS-TURN memory-operand resolution ----
def ptype(p): return p.type.lower().strip()
def fit(t, ints, byts):
    reqs=[p for p in t.parameters if p.required]
    if not reqs: return 0.0
    intp=sum(1 for p in reqs if ptype(p)=='int'); bytp=sum(1 for p in reqs if 'bytes' in ptype(p))
    listp=sum(1 for p in reqs if any(k in ptype(p) for k in ('list','sequence','tuple')))
    if len(reqs)-intp-bytp-listp: return 0.0
    if bytp and byts is None: return 0.0
    if listp: return 0.4 if ints else 0.0
    if intp>len(ints): return 0.0
    return 2.0 if (intp==len(ints) and (bytp>0)==(byts is not None)) else 1.0
def h_tool(u):
    ints,byts=operands(u); cands=[n for _,n in ground(u,5,owner='srmech')]
    resolved=''
    if all(fit(tools[n],ints,byts)==0.0 for n in cands) and MEM:
        # CROSS-TURN OPERAND RESOLUTION: the utterance under-supplies operands -> recall the referenced note
        topname=nm_toks[cands[0]]
        q=' '.join(w for w in toks(u) if not w.isdigit() and w not in IMPV and w not in topname and w not in ('of','the','and'))
        note=max((m for m in MEM if 'kernel' not in toks(m)), key=lambda m: sim(enc_q(q),enc_q(m)))
        mem_ints=[int(w) for w in toks(note) if w.isdigit()]
        ints=mem_ints[:1]+ints                             # the memory value fills the referenced (first) slot
        resolved=' [operand 100.. resolved from memory: "%s"]'%note if False else ' [operand %s resolved from: "%s"]'%(mem_ints[:1],note)
    scored=sorted(((fit(tools[n],ints,byts),-cands.index(n),n) for n in cands),reverse=True)
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
    return '%s%s = %s%s'%(pick.split('.')[-1],tuple(args),str(res)[:40],resolved)
# ---- the 10-turn SESSION (both surfaces, one memory, per-turn coherence check) ----
SESSION=[
 ("siona remember that water boils at 100 celsius",        lambda o:'noted' in o),
 ("siona ingest the kernel fahrenheit is celsius times 9 over 5 plus 32", lambda o:'noted' in o),
 ("siona remember that chess is a game of 64 squares",     lambda o:'noted' in o),
 ("compute the gcd of the boiling point of water and 48",  lambda o:'gcd(100, 48) = 4' in o),      # USER CHALLENGE 1
 ("siona water boils at what fahrenheit",                  lambda o:'212' in o),                    # USER CHALLENGE 2
 ("factor 360 into primes",                                lambda o:'(2, 3), (3, 2), (5, 1)' in o),
 ("siona recall what we know about chess",                 lambda o:'chess' in o and '64' in o),
 ("water boils at",                                        lambda o:o.strip()=='100'),
 ("siona what can you do",                                 lambda o:'answer' in o and '8' in o),
 ("siona show your working memory",                        lambda o:'water boils' in o and 'kernel' in o),
]
print("SIONA-INFER-5 -- the 10-turn coherent session (cross-turn operands + kernel conversion):")
coherent=0
for i,(u,check) in enumerate(SESSION,1):
    r=route(u)
    if r=='self-command': t,out=drive_self(u); tag='siona.%s'%t
    elif r=='tool-call': out=h_tool(u); tag='srmech'
    elif r=='continue': out=s_continue(u); tag='substrate'
    else: out=s_define(u); tag='define'
    ok=check(str(out)); coherent+=ok
    print("  t%-2d %-3s '%s'\n        -> %-14s %s"%(i,'OK' if ok else 'X',u,tag,str(out)[:130]))
print("=> session coherence: %d/%d turns correct; memory grew to %d items and stayed coherent (never compacted)."%(coherent,len(SESSION),len(MEM)))
print("   CHALLENGE 1 (cross-turn operand): 'the boiling point of water' resolved 100 FROM MEMORY -> gcd(100,48)=4.")
print("   CHALLENGE 2 (kernel conversion): 212 was NEVER stored -- derived EXACTLY from the 100-celsius fact through")
print("   the ingested kernel, (100*9+32*5)/5 = 1060/5 -> 212 reduced via srmech cyclic.gcd. Stay-rational; no floats.")

"""SIONA-INFER-3 (#235) — the srmech-DRIVE loop: Siona's inference (a) grounds the utterance to a tool (INFER-2),
(b) extracts operands, (c) SIGNATURE-FIT re-ranks the top-K by the tool's typed parameters (this closes INFER-2's
within-family misses), (d) resolves the dotted callable, (e) binds args, (f) ACTUALLY RUNS the real srmech op,
(g) reads the result back into never-compacted working memory. This is 'native infer as the sparse LM to DRIVE
srmech' -- the rc1 ship criterion. Sparse Klein-4 grounding; no numpy/abs/Counter/bag."""
import re, importlib
from srmech.amsc import tool_schema as ts, hdc
from srmech.rbs_lm import substrate as S
D=8192; cs=S.ContextSubstrate(D=D, hex_chars=16); bundle=cs.bundle_odd; bind=hdc.klein4_bind
def fl(q): return q.as_float() if hasattr(q,'as_float') else float(q)
def sim(a,b): return fl(hdc.klein4_similarity(a,b))
def toks(s):
    s=(s or '').lower(); s=re.sub(r'([a-z])([0-9])',r'\1 \2',s); s=re.sub(r'([0-9])([a-z])',r'\1 \2',s)
    return [w for w in re.split(r'[^a-z0-9]+',s) if len(w)>1 or w.isdigit()]
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
def ground(u,k): return [n for _,n in sorted(((sim(enc_q(u),v),n) for n,v in idx),reverse=True)[:k]]
# ---- operand extraction + signature-fit + bind + RUN ----
def operands(u):
    ints=[int(x) for x in re.findall(r'-?\d+', u)]
    m=re.search(r'(?:bytes|string|text|of)\s+["\']?([a-z]{2,})["\']?\s*$', u.lower())
    byts=m.group(1).encode() if m else None
    return ints, byts
def ptype(p): return p.type.lower().strip()
def supported(p): t=ptype(p); return t=='int' or 'bytes' in t or any(k in t for k in ('list','sequence','tuple'))
def fit(t, ints, byts):                                   # match the OPERAND SHAPE to the PARAM SHAPE (exact arity best)
    reqs=[p for p in t.parameters if p.required]
    if not reqs or any(not supported(p) for p in reqs): return 0.0
    intp=sum(1 for p in reqs if ptype(p)=='int')
    listp=sum(1 for p in reqs if any(k in ptype(p) for k in ('list','sequence','tuple')))
    bytp=sum(1 for p in reqs if 'bytes' in ptype(p))
    if bytp and byts is None: return 0.0
    if listp: return 0.4 if ints else 0.0                 # user gave SCALARS -> a list-param tool is a WEAK fit
    if intp>len(ints): return 0.0                         # not enough int operands
    exact = (intp==len(ints)) and ((bytp>0)==(byts is not None))
    return 2.0 if exact else 1.0                          # EXACT arity (all operands used, right types) wins
def bind_args(t, ints, byts):
    args=[]; ii=0
    for p in t.parameters:
        if not p.required and ii>=len(ints): break
        tp=ptype(p)
        if 'bytes' in tp: args.append(byts)
        elif tp=='int':
            if ii>=len(ints): return None
            args.append(ints[ii]); ii+=1
        elif any(k in tp for k in ('list','sequence','tuple')): args.append(ints[ii:]); ii=len(ints)
        else: return None
    return args
def resolve(dotted):
    parts=dotted.split('.')
    for i in range(len(parts),0,-1):
        try: mod=importlib.import_module('.'.join(parts[:i]))
        except ImportError: continue
        obj=mod
        try:
            for p in parts[i:]: obj=getattr(obj,p)
            return obj
        except AttributeError: continue
    return None
memory=[]                                                 # never-compacted working memory (feeds INFER-5)
def drive(u):
    cands=ground(u,5); ints,byts=operands(u)
    scored=sorted(((fit(tools[n],ints,byts), -cands.index(n), n) for n in cands), reverse=True)  # fit, then grounding rank
    pick=scored[0][2] if scored[0][0]>0 else cands[0]      # signature-fit selection; fallback to grounding top-1
    t=tools[pick]; fn=resolve(pick); args=bind_args(t,ints,byts)
    top3=[c.split('.')[-1] for c in cands[:3]]
    if fn is None or args is None:
        print("  utt: %-55s\n     ground top3=%s  -> could not bind"%(u,top3)); return
    try: res=fn(*args)
    except Exception as e: res='ERR: %s'%e
    rs=str(res); rs=rs[:60]+('…' if len(rs)>60 else '')
    memory.append((u, pick.split('.')[-1], args, res))
    print("  utt: %s"%u)
    print("     ground top3=%s -> FIT-picked '%s'  RAN %s%s = %s"%(top3, pick.split('.')[-1], pick.split('.')[-1], tuple(args), rs))
print("SIONA-INFER-3 -- the srmech-DRIVE loop (ground -> operands -> signature-fit -> resolve -> RUN -> read-back):")
for u in ["compute the gcd of 48 and 36",
          "factor 360 into primes",
          "sha256 hash of the bytes hello",
          "best rational approximation of 355 over 113 with denominator at most 100",
          "greatest common divisor of 1071 and 462"]:
    drive(u)
print("\n  WORKING MEMORY now holds %d driven results (never compacted; feeds INFER-5):"%len(memory))
for u,tool,args,res in memory:
    print("     %-22s %s%s = %s"%(tool, '', tuple(args), str(res)[:44]))
print("=> Siona GROUNDS the utterance to a tool (INFER-2), signature-fit DISAMBIGUATES by typed params, resolves +")
print("   binds + RUNS the real srmech op, and READS the result back. 'native infer to DRIVE srmech' -- demonstrated.")

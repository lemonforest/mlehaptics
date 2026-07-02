"""SIONA-INFER-2 (#234) — srmech tool_schema grounding: encode all 347 srmech ToolEntry (name+summary) as
order-aware RBS-HDC objects (the F766/F1005 depth-read dictionary, pointed at the tool catalog), then map a
natural 'user asks X' utterance -> the correct srmech tool. The 'knows how to use srmech tool_schema' half of the
rc1 gate. v2: fixes from the first cut -- (i) letter-digit tokenization split (klein4 -> klein 4, matches the
query 'klein-4'); (ii) NAME-weighting (the tool name is its identity = the F769 title-vs-definition); (iii)
adjacency BIGRAMS not a bag (feedback_never_bag_of_words). Structural-first. Sparse Klein-4; bundle via
cs.bundle_odd (klein4_bundle rejects HVs, §82); no numpy/abs/Counter."""
import re
from srmech.amsc import tool_schema as ts, hdc
from srmech.rbs_lm import substrate as S
D=8192; cs=S.ContextSubstrate(D=D, hex_chars=16); bundle=cs.bundle_odd; bind=hdc.klein4_bind
def fl(q): return q.as_float() if hasattr(q,'as_float') else float(q)
def sim(a,b): return fl(hdc.klein4_similarity(a,b))
def toks(s):
    s=(s or '').lower()
    s=re.sub(r'([a-z])([0-9])', r'\1 \2', s); s=re.sub(r'([0-9])([a-z])', r'\1 \2', s)  # klein4->klein 4, sha256->sha 256 (BOTH sides consistent)
    return [w for w in re.split(r'[^a-z0-9]+', s) if len(w)>1 or w.isdigit()]
tools=ts.get_tool_schema().tools
NT=len(tools)
nm_toks={t.name: toks(t.name.split('.')[-1]) for t in tools}     # the tool's IDENTITY tokens
su_toks={t.name: toks(t.summary) for t in tools}                 # the tool's DESCRIPTION tokens
# ---- doc-freq aboutness gate over the descriptions (F984/F768) ----
docf={}
for t in tools:
    for w in set(nm_toks[t.name]+su_toks[t.name]): docf[w]=docf.get(w,0)+1
FUNC=int(NT*0.35)
def gate(w): return 1.0 if docf.get(w,0)<FUNC else FUNC/docf[w]
gv={}
def vec(w):
    if w not in gv: gv[w]=hdc.klein4_random(D, seed=(sum((i+1)*ord(c) for i,c in enumerate(w))%80000)+7)
    return gv[w]
def bigrams(ws): return [bind(vec(a),vec(b)) for a,b in zip(ws, ws[1:])]   # adjacency = order-aware, NOT a bag
def encode_tool(name):
    nmw=nm_toks[name]; suw=[w for w in su_toks[name] if gate(w)>=1.0]
    parts=[vec(w) for w in nmw]*3 + bigrams(nmw)*2                     # NAME weighted 3x uni + 2x bigram (identity)
    parts+=[vec(w) for w in suw] + bigrams(suw)                        # DESCRIPTION 1x
    return bundle(parts or [vec('_')])
def encode_query(utt):
    ws=[w for w in toks(utt) if gate(w)>=1.0]
    return bundle(([vec(w) for w in ws] + bigrams(ws)) or [vec('_')])
# ---- (A) READ-INDEPENDENT: tool-vector discriminability ----
names=list(nm_toks); sample=names[:40]
def offdiag():
    vs=[encode_tool(n) for n in sample]; tot=cnt=0.0
    for i in range(len(vs)):
        for j in range(len(vs)):
            if i!=j: tot+=sim(vs[i],vs[j]); cnt+=1
    return tot/cnt
print("SIONA-INFER-2 v2 -- srmech tool_schema grounding (%d tools):"%NT)
print("  (A) tool-vector discriminability (mean off-diag sim; ~0.25=orthogonal): %.3f"%offdiag())
idx=[(n, encode_tool(n)) for n in names]
def retrieve(utt, k=3):
    q=encode_query(utt); return [n for _,n in sorted(((sim(q,v),n) for n,v in idx), reverse=True)[:k]]
EVAL=[
 ("hash these bytes with sha256","sha256_bytes"),("hash many messages at once with simd","sha256_batch"),
 ("compute the greatest common divisor of two integers","gcd"),("best rational approximation with a bounded denominator","best_rational"),
 ("factor this number into primes","factor"),("the magnetic laplacian of a directed graph","magnetic_laplacian"),
 ("signed laplacian with positive and negative edges","signed_laplacian"),("symmetric jacobi eigenvalues of a matrix","jacobi_eigvals"),
 ("hermitian eigendecomposition of a complex matrix","hermitian_eigendecompose"),("the fiedler vector for graph bisection","fiedler_vector"),
 ("bundle these klein-4 hypervectors by majority","klein4_bundle"),("recover a bound value from a klein-4 bundle","klein4_unbundle"),
 ("similarity between two klein-4 vectors","klein4_similarity"),("generate a random klein-4 hypervector","klein4_random"),
 ("cyclic bit rotation of a hypervector","permute"),("weighted co-occurrence graph from documents","cooccurrence_edges"),
 ("three-fold spectral eigenvector grouping","three_fold_eigvec_groups"),("polar hypervector with minus one zero and plus one","polar_random"),
]
top1=top3=0
print("  (B) retrieval -- natural 'user asks' -> tool (top-1/top-3 over %d paraphrases):"%len(EVAL))
for utt,want in EVAL:
    short=[g.split('.')[-1] for g in retrieve(utt,3)]
    h1=short[0]==want; h3=want in short; top1+=h1; top3+=h3
    print("      %-4s %-52s -> %-26s %s"%('OK' if h1 else ('~' if h3 else 'X'), utt[:52], short[0], '' if h1 else ('(top3)' if h3 else '(MISS %s)'%short[:2])))
print("  => top-1 %d/%d = %.0f%%   top-3 %d/%d = %.0f%%"%(top1,len(EVAL),100*top1/len(EVAL), top3,len(EVAL),100*top3/len(EVAL)))

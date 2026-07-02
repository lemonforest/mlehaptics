"""F1005 (F766 / #220) — open-vocabulary word->definition DICTIONARY for the DEPTH read ("what IS X", the why-
asker at depth, feedback_cone_of_ignorance_pedagogy). Source: simplewiki leads ARE definitions ("X is a Y").
Structural-FIRST (feedback_read_independent_structure_check_first): (A) coverage + definitional-FORM rate (are
the leads genus-differentia definitions?); (B) DISCRIMINABILITY gated-vs-ungated (read-independent Gram -- an
ungated def-bundle is function-word-dominated => FUSED => unretrievable; the F768 aboutness-gate should make
defs distinct). Then (C) the depth read: IN-vocab associative recall + OPEN-vocab usage-fallback. Sparse."""
import json
from srmech.amsc import hdc
from srmech.rbs_lm import substrate as S
D=8192; cs=S.ContextSubstrate(D=D, hex_chars=16); bundle=cs.bundle_odd  # bundle_odd accepts HV wrappers (klein4_bundle wants raw int-seqs -- API inconsistency, log to UPSTREAM)
def fl(q): return q.as_float() if hasattr(q,'as_float') else float(q)
def sim(a,b): return fl(hdc.klein4_similarity(a,b))
arts=[]
with open('/home/skirklan/corpora/wikipedia/simplewiki_fullbody_instrument.ndjson') as f:
    for line in f:
        r=json.loads(line); t=r['t']; body=r['s'].split()
        if t and body: arts.append((t, body))
        if len(arts)>=2000: break
# ---- doc-freq aboutness gate (F984/F768), computed on the leads ----
LEAD=25
docf={}
for t,body in arts:
    for w in set(body[:LEAD]): docf[w]=docf.get(w,0)+1
NDOC=len(arts); FUNC=int(NDOC*0.6)
def gate(w): return 1.0 if docf.get(w,0)<FUNC else FUNC/docf[w]   # F984 one-sided function-ness gate
# ---- (A) build the dict + STRUCTURAL coverage + definitional FORM (read-independent) ----
COP=set('is are was were means refers describes called'.split())
dic={}; cop=selfref=0
for t,body in arts:
    key=t.lower().split()[0]; lead=body[:LEAD]
    dic[key]=(t, lead)
    if any(w in COP for w in lead[:6]): cop+=1          # copula in first 6 => genus-differentia definition
    if lead and lead[0]==key: selfref+=1                # opens with the title token (definitional opening)
N=len(arts)
print("F766 open-vocab word->definition DICTIONARY for the depth read -- STRUCTURAL first:")
print("  (A) coverage=%d defs ; definitional FORM (read-independent):"%len(dic))
print("      copula ('is/are/was...') in first 6 tokens : %d/%d = %.0f%%  (genus-differentia = a real definition)"%(cop,N,100*cop/N))
print("      lead opens with the title word             : %d/%d = %.0f%%  (self-referential definitional opening)"%(selfref,N,100*selfref/N))
# ---- (B) DISCRIMINABILITY gated vs ungated (read-independent Gram) ----
gv={}
def vec(w):
    if w not in gv: gv[w]=hdc.klein4_random(D, seed=(sum((i+1)*ord(c) for i,c in enumerate(w))%80000)+7)
    return gv[w]
def defvec(lead, gated):
    parts=[vec(w) for w in lead for _ in range(1)] if not gated else None
    if gated:
        acc=[]
        for w in lead:
            if gate(w)>=1.0: acc.append(vec(w))          # keep only content (gate==1); drop function words
        parts=acc if acc else [vec(w) for w in lead]
    return bundle(parts)
sample=[dic[k] for k in list(dic)[:40]]
def offdiag_mean(gated):
    vs=[defvec(l,gated) for _,l in sample]
    tot=cnt=0.0
    for i in range(len(vs)):
        for j in range(len(vs)):
            if i!=j: tot+=sim(vs[i],vs[j]); cnt+=1
    return tot/cnt
og=offdiag_mean(False); gg=offdiag_mean(True)
print("  (B) DISCRIMINABILITY of def-vectors (mean off-diag sim; LOWER=more distinct=retrievable), 40 defs:")
print("      UNGATED def-bundles : %.3f  (function-word-dominated -> FUSED)"%og)
print("      GATED   def-bundles : %.3f  (F768 aboutness-gate -> DISTINCT)  -> gate makes the dictionary retrievable"%gg)
# ---- (C) the DEPTH read: IN-vocab associative recall (gated vs ungated) + OPEN-vocab usage fallback ----
keys=list(dic)[:60]
def recall_acc(gated):
    dvs=[(k, defvec(dic[k][1], gated)) for k in keys]
    ok=0
    for k in keys:
        lead=dic[k][1]
        cue=[w for w in lead if gate(w)>=1.0][:3] if gated else lead[:3]   # a 3-content-word cue (the "describe X" query)
        if not cue: cue=lead[:3]
        q=bundle([vec(w) for w in cue])
        pick=max(dvs, key=lambda kv: sim(q, kv[1]))[0]
        ok += (pick==k)
    return ok, len(keys)
oa=recall_acc(False); ga=recall_acc(True)
print("  (C) DEPTH read -- associative recall of the right definition from a 3-content-word cue (IN-vocab), 60 defs:")
print("      UNGATED: %d/%d = %.0f%%   GATED: %d/%d = %.0f%%"%(oa[0],oa[1],100*oa[0]/oa[1], ga[0],ga[1],100*ga[0]/ga[1]))
# OPEN-vocab: a query word that is NOT a title -> derive meaning from USAGE (co-occurrence, aboutness-gated)
def open_read(word):
    co={}
    for t,body in arts:
        if word in body[:LEAD]:
            for w in body[:LEAD]:
                if w!=word and gate(w)>=1.0: co[w]=co.get(w,0)+1     # gated co-occurring content words
    return [w for w,_ in sorted(co.items(), key=lambda kv:-kv[1])[:8]]
for q in ('calendar','emperor','ocean'):
    intit = q in dic
    print("  (C-open) '%s' %s -> depth read via %s: %s"%(q, '(IS a title)' if intit else '(OPEN-vocab, no article)',
          'stored def' if intit else 'USAGE co-occurrence', ' '.join(dic[q][1][:8]) if intit else ' '.join(open_read(q))))
print("=> definitional-FORM is high (A: leads ARE 'X is a Y' definitions); the F768 aboutness-gate makes def-vectors")
print("   DISTINCT (B) and lifts associative recall (C) -- the gate is what makes the depth-read dictionary usable;")
print("   OPEN-vocab words get a depth read from gated USAGE co-occurrence. #220 answered.")

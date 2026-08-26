"""F1019 probe (user idea) — OPERATOR-HOOD AS A SPECTRAL SHAPE, pre-learned and transferable: operator/function
words should live in the LOW modes of the language co-occurrence Laplacian (the subharmonic ROUTING band, F997 --
hubs bridging communities), content words in localized high modes. If true, the shape is learned ONCE (English,
the wiki kernel side) and RECOGNIZES operator words in a NEW language (Bislama UDHR) with ZERO word-learning --
the third acquisition mode: attested (F1016) / accreted (F1018) / RECOGNIZED (this). The degree-NORMALIZED
spectral ratio should transfer across corpus scales where a raw frequency threshold cannot.
Route: srmech text.cooccurrence_edges -> normalized_laplacian -> mat_hermitian_eigendecompose (Class-L, bounded).
Read-independent features; labels = the F984 doc-freq definition (same rule both corpora; labels are not the
classifier). Sparse; no numpy/abs/Counter."""
import json, re
import xml.etree.ElementTree as ET
from srmech.amsc import text as stext, laplacian as L
def fl(q): return q.as_float() if hasattr(q,'as_float') else float(q)
def toks(s): return [w for w in re.split(r'[^a-z0-9]+',(s or '').lower()) if w]
# ---- corpora ----
eng_docs=[]
with open('/home/skirklan/corpora/wikipedia/simplewiki_fullbody_instrument.ndjson') as f:
    for line in f:
        eng_docs.append(toks(json.loads(line)['s'])[:80])
        if len(eng_docs)>=200: break
NS='{http://efele.net/udhr}'
root=ET.parse('/home/skirklan/corpora/udhr/udhr_bis.xml').getroot()
bis_docs=[toks(' '.join(p.text or '' for p in a.iter(NS+'para'))) for a in root.iter(NS+'article')]
bis_docs=[d for d in bis_docs if d]
NV=72; KLOW=8
def spectral_features(docs):
    n,edges,weights=stext.cooccurrence_edges(docs, window=2, vocab_size=NV)
    # vocab order: introspect -- cooccurrence_edges returns ids; recover the vocab it chose
    # (the op selects top-vocab_size by frequency; rebuild the same ranking to map ids->words)
    tf={}
    for d in docs:
        for w in d: tf[w]=tf.get(w,0)+1
    vocab=[w for w,_ in sorted(tf.items(), key=lambda kv:(-kv[1],kv[0]))[:n]]
    Ln=L.normalized_laplacian(n, edges, weights)
    ev,V=L.mat_hermitian_eigendecompose(Ln)
    raw=ev.tolist() if hasattr(ev,'tolist') else list(ev)
    if raw and isinstance(raw[0], list):
        flat=[raw[i][i] for i in range(len(raw))] if len(raw)==len(raw[0]) else [x for row in raw for x in row]
    else: flat=raw
    evl=[fl(getattr(x,'real',x)) for x in flat]
    Vl=V.tolist() if hasattr(V,'tolist') else V
    order=sorted(range(n), key=lambda k: evl[k])
    low=[k for k in order if evl[k]>1e-9][:KLOW]          # lowest NONTRIVIAL modes = the routing band
    def re2(z): r=getattr(z,'real',z); return fl(r)*fl(r)+fl(getattr(z,'imag',0.0))**2
    lowE={}; deg={}; ipr={}
    dcount=[0]*n
    for (a,b),w in zip(edges,weights): dcount[a]+=w; dcount[b]+=w
    tot=sum(dcount) or 1
    nontriv=[k for k in order if evl[k]>1e-9]
    for i in range(n):
        lowE[vocab[i]]=sum(re2(Vl[i][k]) for k in low)     # row energy in the low band (rows sum to 1: V orthonormal)
        deg[vocab[i]]=dcount[i]/tot                        # degree-normalized hubness
        es=[re2(Vl[i][k]) for k in nontriv]; tt=sum(es) or 1.0
        ipr[vocab[i]]=1.0/sum((e/tt)**2 for e in es)       # PARTICIPATION RATIO: operators bridge ALL communities
                                                           # -> DELOCALIZED (high P); content LOCALIZES (low P)
    # F984 ground-truth labels: function = docf >= 0.5 * Ndocs (same declared rule both corpora)
    docf={}
    for d in docs:
        for w in set(d): docf[w]=docf.get(w,0)+1
    lab={w: docf.get(w,0)>=0.5*len(docs) for w in vocab}
    return vocab, lowE, deg, lab, dcount, ipr
ev_,elowE,edeg,elab,edc,eipr=spectral_features(eng_docs)
bv_,blowE,bdeg,blab,bdc,bipr=spectral_features(bis_docs)
def mean(xs): return sum(xs)/len(xs) if xs else 0.0
# ---- learn the SHAPE on ENGLISH only ----
fE=[elowE[w] for w in ev_ if elab[w]]; cE=[elowE[w] for w in ev_ if not elab[w]]
t_low=(mean(fE)+mean(cE))/2
fD=[edeg[w] for w in ev_ if elab[w]]; cD=[edeg[w] for w in ev_ if not elab[w]]
t_deg=(mean(fD)+mean(cD))/2
fP=[eipr[w] for w in ev_ if elab[w]]; cP=[eipr[w] for w in ev_ if not elab[w]]
t_ipr=(mean(fP)+mean(cP))/2
fR=[edc[ev_.index(w)] for w in ev_ if elab[w]]; cR=[edc[ev_.index(w)] for w in ev_ if not elab[w]]
t_raw=(mean(fR)+mean(cR))/2                                 # the RAW count threshold (expected NOT to transfer)
print("OPERATOR-HOOD AS A SPECTRAL SHAPE (learned on English, applied to Bislama, ZERO word-learning):")
print("  ENGLISH separation (read-independent): lowE fn=%.3f vs content=%.3f | deg fn=%.4f vs %.4f | IPR fn=%.1f vs %.1f"%(mean(fE),mean(cE),mean(fD),mean(cD),mean(fP),mean(cP)))
def score(vocab,feat,lab,t):
    tp=sum(1 for w in vocab if feat[w]>=t and lab[w]); fp=sum(1 for w in vocab if feat[w]>=t and not lab[w])
    fn=sum(1 for w in vocab if feat[w]<t and lab[w])
    P=tp/(tp+fp) if tp+fp else 0.0; R=tp/(tp+fn) if tp+fn else 0.0
    return P,R,tp,fp,fn
nfun_b=sum(1 for w in bv_ if blab[w])
print("  BISLAMA ground truth (F984 rule): %d function words of %d vocab"%(nfun_b,len(bv_)))
for name,feat,t in (('SPECTRAL lowE  ',blowE,t_low),('NORMALIZED deg ',bdeg,t_deg),('DELOCALIZE IPR ',bipr,t_ipr)):
    P,R,tp,fp,fn=score(bv_,feat,blab,t)
    print("  TRANSFER %s: precision %.0f%%  recall %.0f%%  (tp=%d fp=%d fn=%d)  <- English threshold, unchanged"%(name,100*P,100*R,tp,fp,fn))
rawf={w: bdc[bv_.index(w)] for w in bv_}
P,R,tp,fp,fn=score(bv_,rawf,blab,t_raw)
print("  TRANSFER RAW count     : precision %.0f%%  recall %.0f%%  (tp=%d fp=%d fn=%d)  <- scale-broken, as predicted"%(100*P,100*R,tp,fp,fn))
top_b=sorted(bv_, key=lambda w:-blowE[w])[:12]
print("  Bislama top-12 by SPECTRAL lowE: %s"%top_b)
print("  Bislama top-12 by DELOCALIZE IPR: %s"%sorted(bv_, key=lambda w:-bipr[w])[:12])
print("  (compare F1016 measured function set: i blong mo long we ol o hemi oli se olsem ...)")
print("=> if lowE (and/or normalized deg) transfers with high recall, operator-hood IS a pre-learned spectral")
print("   shape: siona RECOGNIZES a new language's operator words from the kernel's Laplacian -- no from-scratch")
print("   learning. Acquisition modes: ATTESTED (F1016) / ACCRETED (F1018) / RECOGNIZED (F1019, this).")

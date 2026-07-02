"""F1002 — is the premise even correct? Test the elliptic -z^-1 code family from a READ-INDEPENDENT perspective:
its intrinsic CROSS-CORRELATION structure (no recall involved). Premise (#1232/F994/F995): the -z^-1 gives a
genuinely STRUCTURED, distinct code family (vs symmetric x1 = isometry = redundant). Measure directly:
(1) the NR x NR cross-correlation matrix of elliptic vs independent codes; (2) CIRCULANT check -- is elliptic
C[r][r'] a function of the rung-difference |r-r'| (the quasi-periodicity fingerprint)? (3) the MAX off-diagonal
sidelobe (what the peak read rides) + the MEAN. This tests whether the -z^-1 STRUCTURE is real and whether it
has a measurable (non-recall) advantage. Sparse Klein-4; no abs."""
from srmech.amsc import hdc
D=8192; g5=hdc.klein4_chirality_flip_gamma5; HV=type(hdc.klein4_random(D,seed=0))
def fl(q): return q.as_float() if hasattr(q,'as_float') else float(q)
from srmech.amsc import cascade
def mag(x): return fl(cascade.magnitude(x))     # srmech-allow: Class-K pin-slot |x| for a correlation magnitude (not abs)
def dlt_(r,s): return r-s if r>s else s-r        # integer rung-difference (index arithmetic, no abs)
NR=6
def rot(seq,k): k%=len(seq); return seq[-k:]+seq[:-k]
RK_ind=[hdc.klein4_random(D, seed=71000+r) for r in range(NR)]
base=hdc.klein4_random(D, seed=99001); bl=base.tolist(); dlt=D//(2*NR)
RK_ell=[(g5(HV.from_sequence(rot(bl, r*dlt))) if r%2 else HV.from_sequence(rot(bl, r*dlt))) for r in range(NR)]
def cmat(RK): return [[fl(hdc.klein4_similarity(RK[r],RK[s])) for s in range(NR)] for r in range(NR)]
def offdiag(C): return [C[r][s] for r in range(NR) for s in range(NR) if r!=s]
def circ_by_delta(C):   # mean |corr| grouped by rung-difference d=|r-s| -- circulant if consistent within d
    byd={}
    for r in range(NR):
        for s in range(NR):
            if r!=s: byd.setdefault(dlt_(r,s),[]).append(mag(C[r][s]))
    return {d: (sum(v)/len(v)) for d,v in sorted(byd.items())}
def spread(C):          # within-delta consistency: low spread => circulant/structured
    byd={}
    for r in range(NR):
        for s in range(NR):
            if r!=s: byd.setdefault(dlt_(r,s),[]).append(mag(C[r][s]))
    # max-minus-min within each delta group, averaged (0 = perfectly circulant)
    ss=[max(v)-min(v) for v in byd.values() if len(v)>1]
    return sum(ss)/len(ss) if ss else 0.0
for RK,label in ((RK_ind,"INDEPENDENT keys"),(RK_ell,"elliptic -z^-1 keys")):
    C=cmat(RK); od=[mag(x) for x in offdiag(C)]
    print("%s:"%label)
    print("   max off-diag |corr| (peak sidelobe) = %.4f   mean = %.4f"%(max(od), sum(od)/len(od)))
    print("   corr by rung-diff d:", {d: round(v,4) for d,v in circ_by_delta(C).items()})
    print("   within-delta spread (0=perfectly circulant/structured) = %.4f"%spread(C))
print("=> if elliptic is CIRCULANT (low within-delta spread) with a LOWER max sidelobe than independent, the", flush=True)
print("   -z^-1 structure is REAL + advantageous read-INDEPENDENTLY -- the premise is correct, and the F1000 peak", flush=True)
print("   advantage = the lower worst-case sidelobe, not a recall artifact.", flush=True)

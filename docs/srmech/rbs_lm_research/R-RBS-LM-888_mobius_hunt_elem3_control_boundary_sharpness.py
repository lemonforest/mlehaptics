"""F888: three in sequence on the chirality-phase geometry (recoverable-reference bundle).
(1) MOBIUS HUNT: ridge slope for all 3 Klein-4 element pairs (2x1, 2x3, 1x3) -> any denominator-2
    slope = a half-twist; PLUS the_one sigma-vs-theta two-sheet test (does a full theta loop land on
    the sigma=-1 sheet, i.e. a +1/2 offset = Mobius).
(2) elem=3 CONTROL: are 2x3/1x3 also 1:1 (=> the F887 1:1 is structural) or different (=> axis-specific)?
(3) BOUNDARY SHARPNESS: cross-ridge profile -> domain wall (cliff, max-grad >> sinusoid) vs smooth ripple.
srmech-native; Q->float at analysis boundary; sparse Klein-4; no bag.
"""
import json, math, statistics
from srmech.amsc import hdc, cascade, format as fmt, rational
from srmech.rbs_lm import substrate as S

D, K, PMAX = 8192, 2, 24
cs = S.ContextSubstrate(D=D, hex_chars=16)
def _dig(s):
    h = fmt.sha256_bytes(s.encode()); return bytes.fromhex(h) if isinstance(h, str) else h
def byte_k4(b): return hdc.klein4_random(D, seed=b)
def word_k4(w):
    return cs.bundle_odd([hdc.klein4_bind(byte_k4(b), cs.pos_key(i)) for i, b in enumerate(w.encode("utf-8"))])
def byte_oct(b):
    d = _dig(f"LoE.byte.{b}"); return tuple((d[i] % 9) - 4 for i in range(8))
def word_oct(w):
    bs = w.encode("utf-8"); p = byte_oct(bs[0])
    for b in bs[1:]: p = tuple(cascade.cd_mult(p, byte_oct(b)))
    return p
def ctx_key(win):
    p = word_oct(win[0])
    for w in win[1:]: p = tuple(cascade.cd_mult(p, word_oct(w)))
    return hdc.klein4_random(D, seed=int.from_bytes(_dig(",".join(str(x) for x in p))[:8], "big"))
WV = {}
def wv(w):
    if w not in WV: WV[w] = word_k4(w)
    return WV[w]
unbind = getattr(hdc, "klein4_unbind", hdc.klein4_bind)
def fl(q): return q.as_float() if hasattr(q, "as_float") else q

path = "/home/skirklan/corpora/wikipedia/simplewiki_rawbody_instrument_v082.ndjson"
seqs = []
with open(path) as fh:
    for line in fh:
        t = json.loads(line)["s"].split()
        if len(t) >= 12: seqs.append(t[:12]); break
noise = []
toks = seqs[0]; p = ["<s>"]*K + toks + ["<e>"]
for i in range(K, len(p)):
    noise.append(hdc.klein4_bind(hdc.klein4_phase_bind(ctx_key(p[i-K:i]), i/PMAX), wv(p[i])))
REFS = [(["the","first"],"letter"), (["a","small"],"thing"), (["it","is"],"the"), (["of","the"],"world")]
def make(ref_ctx, ref_tok):
    rk = ctx_key(ref_ctx)
    return rk, ref_tok, hdc.klein4_bundle(*(noise + [hdc.klein4_bind(rk, wv(ref_tok))]))

def slope_for(eA, eB, G=36):
    accum=[]
    for ctx,tok in REFS:
        rk,tk,M=make(ctx,tok)
        def res(a,b):
            kk=hdc.klein4_phase_bind(rk,a,elem=eA); kk=hdc.klein4_phase_bind(kk,b,elem=eB)
            return fl(hdc.klein4_similarity(unbind(M,kk), wv(tk)))
        crest=[max(range(G), key=lambda j: res(i/G, j/G)) for i in range(G)]
        disp=0
        for i in range(G):
            d=crest[(i+1)%G]-crest[i]
            if d>G/2: d-=G
            if d<-G/2: d+=G
            disp+=d
        accum.append(disp/G)
    m=statistics.mean(accum); n,dn=rational.best_rational(int(round(m*10000)),10000,12)
    return m, statistics.pstdev(accum), (n,dn)

print("=== (1)+(2) MOBIUS HUNT + elem=3 CONTROL: ridge slope per Klein-4 element pair ===")
print("  pair (elemA x elemB) | mean slope | ratio | sd  (denominator 2 => half-twist/Mobius)")
for eA,eB,name in [(2,1,"gamma5 x iomega7  (F887)"),(2,3,"gamma5 x product "),(1,3,"iomega7 x product")]:
    m,sd,(n,dn)=slope_for(eA,eB)
    flag = "  <-- DENOM-2 (Mobius!)" if dn==2 else ""
    print(f"  {name:24s} | {m:+.3f}   | {n}/{dn}  | {sd:.3f}{flag}")

print("\n=== (1b) the_one sigma-vs-theta two-sheet test (Mobius IFF theta-ridge offsets by ~1/2 on sigma=-1) ===")
flip = hdc.klein4_chirality_flip_gamma5
GT=60
for ctx,tok in REFS[:2]:
    rk,tk,M=make(ctx,tok)
    def res_sig(sig, th):
        kk = rk if sig>0 else flip(rk)
        kk = hdc.klein4_phase_bind(kk, th)
        return fl(hdc.klein4_similarity(unbind(M,kk), wv(tk)))
    thp = max(range(GT), key=lambda j: res_sig(+1, j/GT))/GT
    thm = max(range(GT), key=lambda j: res_sig(-1, j/GT))/GT
    off = (thm-thp) % 1.0
    print(f"  ref {str(ctx):18s}: theta_max(sigma+)= {thp:.3f}  theta_max(sigma-)= {thm:.3f}  offset={off:.3f}"
          f"  {'~1/2 MOBIUS' if 0.4<off<0.6 else ('~0 torus' if off<0.1 or off>0.9 else 'other')}")

print("\n=== (3) BOUNDARY SHARPNESS: cross-ridge profile (domain wall vs smooth ripple) ===")
GS=72
rk,tk,M=make(*REFS[0])
def res(a,b):
    kk=hdc.klein4_phase_bind(rk,a,elem=2); kk=hdc.klein4_phase_bind(kk,b,elem=1)
    return fl(hdc.klein4_similarity(unbind(M,kk), wv(tk)))
# walk ACROSS the ridge along the anti-diagonal (phi_g5 = t, phi_w7 = -t) through the ridge center
prof=[res((0.5+t/GS)%1.0, (0.5-t/GS)%1.0) for t in range(-GS//2, GS//2)]
lo,hi=min(prof),max(prof); amp=hi-lo
grads=[cascade.magnitude(prof[i+1]-prof[i]) for i in range(len(prof)-1)]   # Class-K magnitude of the step
maxg=max(grads); meang=statistics.mean(grads)
# a pure sinusoid of this amplitude over this many samples has max step = amp*pi/len
sin_expect = amp*math.pi/len(prof)
print(f"  cross-ridge amp {amp:.4f} (lo {lo:.4f} hi {hi:.4f}); samples {len(prof)}")
print(f"  max step {maxg:.4f} vs mean step {meang:.4f} (ratio {maxg/meang:.2f}); pure-sinusoid max step ~ {sin_expect:.4f}")
print(f"  -> {'SHARP domain wall (max step >> sinusoid)' if maxg > 1.8*sin_expect else 'SMOOTH ripple (~sinusoidal)'}")
print("\n  Q->float at analysis boundary. Sparse Klein-4; no bag.")

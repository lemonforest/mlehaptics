"""F890: AGN-scale null = gravitational-gradient softening. Scale-invariance (F879) means the knowledge
metric is a 'star system of star systems' (user): the null/boundary structure recurs at every scale,
but the GRADIENT across it scales. Physics anchor: tidal gradient at a BH horizon ~ M/r^3 ~ 1/M^2 ->
a BIGGER null (more mass) has a GENTLER boundary gradient. TEST in our substrate: grow the null
(bundle load = 'mass M') and measure the domain-wall gradient (F888 cross-ridge max-step). Prediction:
the gradient DECREASES with load (bigger null -> gentler boundary). srmech-native; Q->float at display;
sparse Klein-4; no bag.
"""
import json, math, statistics
from srmech.amsc import hdc, cascade, format as fmt
from srmech.rbs_lm import substrate as S

D, K, PMAX, GS = 8192, 2, 24, 72
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
        if len(t) >= 12: seqs.append(t[:12])
        if len(seqs) >= 40: break
# pool of noise binds to grow the null
pool = []
for toks in seqs:
    p = ["<s>"]*K + toks + ["<e>"]
    for i in range(K, len(p)):
        pool.append(hdc.klein4_bind(hdc.klein4_phase_bind(ctx_key(p[i-K:i]), i/PMAX), wv(p[i])))
ref_ctx, ref_tok = ["the","first"], "letter"
rk = ctx_key(ref_ctx); refbind = hdc.klein4_bind(rk, wv(ref_tok))

def boundary_grad(load):                                   # null 'mass' = `load` noise binds + the reference
    M = hdc.klein4_bundle(*(pool[:load] + [refbind]))
    def res(a, b):
        kk = hdc.klein4_phase_bind(rk, a, elem=2); kk = hdc.klein4_phase_bind(kk, b, elem=1)
        return fl(hdc.klein4_similarity(unbind(M, kk), wv(ref_tok)))
    prof = [res((0.5+t/GS) % 1.0, (0.5-t/GS) % 1.0) for t in range(-GS//2, GS//2)]   # across the wall (anti-diag)
    lo, hi = min(prof), max(prof); amp = hi - lo
    steps = [cascade.magnitude(prof[i+1]-prof[i]) for i in range(len(prof)-1)]
    maxg = max(steps); sin_expect = amp*math.pi/len(prof)
    return amp, maxg, (maxg/sin_expect if sin_expect else 0.0)

print("=== F890 AGN-scale: boundary gradient vs null 'mass' (bundle load) ===")
print("  load (mass M) | ridge amp | boundary gradient (max-step) | sharpness (vs sinusoid)")
loads = [1, 5, 13, 30, 70, 150, 300]
rows = []
for L in loads:
    amp, g, sharp = boundary_grad(L)
    rows.append((L, amp, g, sharp))
    print(f"  {L:5d}         |  {amp:.4f}   |   {g:.5f}                  |  {sharp:.2f}x")
# scaling: does the gradient g fall with load? fit log-log slope g ~ M^p
xs = [math.log(L) for L,_,_,_ in rows]; ys = [math.log(g) for _,_,g,_ in rows if g>0]
n=len(xs); sx=sum(xs); sy=sum(ys); sxx=sum(x*x for x in xs); sxy=sum(x*y for x,y in zip(xs,ys))
p = (n*sxy - sx*sy)/(n*sxx - sx*sx)
print(f"\n  gradient ~ M^({p:+.2f})  (negative => bigger null = GENTLER boundary, the AGN tidal-softening 1/M^2 analog)")
print(f"  sharpness trend: {rows[0][3]:.2f}x (small null) -> {rows[-1][3]:.2f}x (big null)")
print("  Q->float at display. Sparse Klein-4; no bag.")

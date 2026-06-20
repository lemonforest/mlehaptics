"""F887: measure the diagonal-ridge slope dphi_omega7/dphi_gamma5 = the gamma5:iomega7 COUPLING RATIO
(the 2-axis Mobius half-twist, F886). Fine 2D chirality-phase sweep on a recoverable reference; trace
the resonance crest column per row; unwrap the periodic winding; fit the slope; express as a small-den
rational (Class N). Averaged over several references for robustness. srmech-native; Q->float at the
analysis boundary; sparse Klein-4; no bag.
"""
import json, statistics
from srmech.amsc import hdc, cascade, format as fmt, rational
from srmech.rbs_lm import substrate as S

D, K, PMAX, G = 8192, 2, 24, 36
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
        if len(seqs) >= 1: break
# one short noise context to keep the reference recoverable (small bundle)
noise = []
toks = seqs[0]; p = ["<s>"]*K + toks + ["<e>"]
for i in range(K, len(p)):
    noise.append(hdc.klein4_bind(hdc.klein4_phase_bind(ctx_key(p[i-K:i]), i/PMAX), wv(p[i])))

REFS = [(["the","first"],"letter"), (["a","small"],"thing"), (["it","is"],"the"), (["of","the"],"world")]
def crest_slope(ref_ctx, ref_tok):
    rk = ctx_key(ref_ctx)
    M = hdc.klein4_bundle(*(noise + [hdc.klein4_bind(rk, wv(ref_tok))]))
    def res(a, b):
        k = hdc.klein4_phase_bind(rk, a, elem=2); k = hdc.klein4_phase_bind(k, b, elem=1)
        return fl(hdc.klein4_similarity(unbind(M, k), wv(ref_tok)))
    crest = []
    for i in range(G):                                  # for each phi_gamma5 row, the crest phi_omega7 column
        a = i/G
        crest.append(max(range(G), key=lambda j: res(a, j/G)))
    # unwrap the periodic winding (shortest-step) and sum total displacement over one full gamma5 loop
    disp = 0; steps = []
    for i in range(G):
        d = crest[(i+1) % G] - crest[i]
        if d > G/2: d -= G
        if d < -G/2: d += G
        disp += d; steps.append(d)
    slope = disp / G                                    # d phi_omega7 / d phi_gamma5 over one loop
    return crest, slope, statistics.pstdev(steps)

print(f"=== F887 ridge-slope = gamma5:iomega7 coupling ratio (G={G} fine grid) ===")
slopes = []
for ctx, tok in REFS:
    crest, slope, sd = crest_slope(ctx, tok)
    num, den = rational.best_rational(int(round(slope*10000)), 10000, 12)
    print(f"  ref {str(ctx):20s}->{tok:8s}: slope {slope:+.3f} ~ {num}/{den}  (crest-step sd {sd:.1f})")
    slopes.append(slope)
ms = statistics.mean(slopes); sd = statistics.pstdev(slopes)
num, den = rational.best_rational(int(round(ms*10000)), 10000, 12)
print(f"\n  mean slope {ms:+.3f} +/- {sd:.3f}  ->  coupling ratio gamma5:iomega7 ~ {num}/{den} (Class-N)")
print(f"  |slope|=1 -> 1:1 lockstep; 1/2 -> Mobius half-twist; 0 -> decoupled (axis-aligned).")
print("  Q->float at analysis boundary. Sparse Klein-4; no bag.")

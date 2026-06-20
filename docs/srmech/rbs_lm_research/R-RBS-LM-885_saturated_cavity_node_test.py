"""F885: the DECISIVE cavity-node test on the KNOWN-NULLS regime (F870 over-stuffed single shared M).
F876 says nulls appear AS information increases; F870 measured that cliff (single M past capacity).
Cavity reading (F884): those geodesic nulls = standing-wave NODES at rational-fraction positions.
TEST: over-stuff ONE shared M (F870 regime, known nulls); measure null-rate per stream position;
do the nulls PEAK at rational fractions (cavity nodes)? Control = chunked-M (F872, holds flat -> no
saturation -> should show NO nodes). srmech-native; Q collapsed only at display; sparse Klein-4; no bag.
"""
import json
from srmech.amsc import hdc, cascade, format as fmt, rational
from srmech.rbs_lm import substrate as S

D, K, PMAX, LEN, NSEQ = 8192, 2, 24, 12, 60
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
def key_at(win, pos): return hdc.klein4_phase_bind(ctx_key(win), pos / PMAX)
WV = {}
def wv(w):
    if w not in WV: WV[w] = word_k4(w)
    return WV[w]

path = "/home/skirklan/corpora/wikipedia/simplewiki_rawbody_instrument_v082.ndjson"
arts = []
with open(path) as f:
    for line in f:
        toks = json.loads(line)["s"].split()
        if len(toks) >= LEN: arts.append(toks[:LEN])
        if len(arts) >= NSEQ: break

# RAW resonance amplitude = similarity(unbind(M_vec, key), true_token). Klein-4 bind is involutive
# (Z2xZ2 XOR) so unbind = bind. Contrast: UNDER-capacity bundle vs OVER-capacity (F870) bundle, same measure.
unbind = getattr(hdc, "klein4_unbind", hdc.klein4_bind)
def build_bundle(seqs):
    binds, probes = [], []
    for toks in seqs:
        p = ["<s>"] * K + toks + ["<e>"]
        for i in range(K, len(p)):
            binds.append(hdc.klein4_bind(key_at(p[i-K:i], i), wv(p[i])))
            probes.append((i - K, p[i-K:i], i, p[i]))
    return hdc.klein4_chunk_bundle(binds, 1)[0], probes, len(binds)   # single bundle vector
over_vec, over_probes, nb_over = build_bundle(arts)          # N=60 -> 780 binds, WAY over the ~24 wall (F870)
under_vec, under_probes, nb_under = build_bundle(arts[:3])   # N=3  -> ~39 binds, near/under the wall

def amp_by_pos(vec, probes):                                 # raw true-token resonance per position
    npos = LEN + 1; acc = [0.0]*npos; cnt = [0]*npos
    for m, ctx, abspos, truetok in probes:
        r = unbind(vec, key_at(ctx, abspos))                 # M ⊛ key⁻¹ ≈ token + noise
        s = hdc.klein4_similarity(r, wv(truetok))
        acc[m] += (s.as_float() if hasattr(s, "as_float") else s); cnt[m] += 1   # collapse at display
    return [acc[i]/cnt[i] if cnt[i] else 0.0 for i in range(npos)]

amp_over = amp_by_pos(over_vec, over_probes)
amp_under = amp_by_pos(under_vec, under_probes)
print(f"=== F885 cavity-node test: raw true-token resonance per position ===")
print(f"  OVER-stuffed bundle ({nb_over} binds, F870 cliff): mean amp {sum(amp_over)/len(amp_over):.4f}")
print(f"  UNDER-capacity bundle ({nb_under} binds, control):  mean amp {sum(amp_under)/len(amp_under):.4f}")
mx = max(amp_over) or 1.0; mn = min(a for a in amp_over if a)
print("\n  pos | OVER-stuffed amplitude (the nulls live here)  | UNDER | fraction")
for i in range(LEN + 1):
    bar = "#" * int(40 * (amp_over[i]-mn) / (mx-mn) if mx > mn else 0)
    num, den = rational.best_rational(i, LEN, 6)
    print(f"  {i:3d} | {amp_over[i]:.4f} {bar:<40s} | {amp_under[i]:.4f} | {num}/{den}")
mean = sum(amp_over)/len(amp_over)
nulls = [i for i in range(1, LEN) if amp_over[i] <= amp_over[i-1] and amp_over[i] <= amp_over[i+1] and amp_over[i] < mean]
print(f"\n  NULL positions (over-stuffed amplitude minima below mean): {nulls}")
for i in nulls:
    num, den = rational.best_rational(i, LEN, 6)
    print(f"    null pos {i} = {num}/{den}  {'SMALL-DEN node (cavity)' if den<=4 else 'not a simple node'}")
print("\n  cavity confirmed IFF over-stuffed nulls sit at small-den fractions (vs flat under-capacity).")
print("  Q->float only at display. Sparse Klein-4; no bag.")

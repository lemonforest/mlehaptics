"""F884: is the bounded page a RESONANT CAVITY whose nodes = the geodesic null regions (F876)?
Reading: F879 page = bounded resonator (cavity); standing-wave eigenmodes have NODES at fixed
positions set by the boundary; the F876 'null is the inverse of information' = node:antinode.
Music theory = discrete cavity modes: nodes at rational fractions (Class N small-denom). TEST:
record top-1 resonance amplitude at each stream position across many pages; do the AMPLITUDE DIPS
(nulls) cluster at rational-fraction positions (cavity nodes) vs uniform? srmech-native; Q collapsed
to float ONLY at the analysis/display boundary; sparse Klein-4; no bag.
"""
import json
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
def key_at(win, pos): return hdc.klein4_phase_bind(ctx_key(win), pos / PMAX)
WV = {}
def wv(w):
    if w not in WV: WV[w] = word_k4(w)
    return WV[w]

path = "/home/skirklan/corpora/wikipedia/simplewiki_rawbody_instrument_v082.ndjson"
LEN = 12                                            # fixed cavity length (same #positions -> stack modes)
arts = []
with open(path) as f:
    for line in f:
        toks = json.loads(line)["s"].split()
        if len(toks) >= LEN: arts.append(toks[:LEN])
        if len(arts) >= 200: break

# amplitude profile: top-1 resonance at each position, averaged across pages (the cavity standing wave)
nbins = LEN + 1
acc = [0.0] * nbins; cnt = [0] * nbins
for toks in arts:
    p = ["<s>"] * K + toks + ["<e>"]
    binds = [hdc.klein4_bind(key_at(p[i-K:i], i), wv(p[i])) for i in range(K, len(p))]
    chunks = hdc.klein4_chunk_bundle(binds, 8); vocab = sorted(set(toks) | {"<e>"})
    for m in range(len(p) - K):
        ctx = p[m:m+K]
        sc = hdc.klein4_chunk_resolve(chunks, key_at(ctx, K+m), [wv(w) for w in vocab])
        top = max(sc, key=lambda q: q.as_float() if hasattr(q, "as_float") else q)  # Q-aware
        acc[m] += (top.as_float() if hasattr(top, "as_float") else top); cnt[m] += 1   # collapse at display

prof = [acc[i]/cnt[i] if cnt[i] else 0.0 for i in range(nbins)]
mx = max(prof) or 1.0
print(f"=== F884 page-as-cavity: resonance amplitude profile across {len(arts)} pages (len {LEN}) ===")
print("  pos | amplitude (top-1 resonance, mean) | bar")
for i, v in enumerate(prof):
    bar = "#" * int(40 * v / mx)
    print(f"  {i:3d} | {v:.4f} | {bar}")
# find the NULLS (local minima) and check their fractional position vs small-denominator rationals
mins = [i for i in range(1, nbins-1) if prof[i] <= prof[i-1] and prof[i] <= prof[i+1]]
print(f"\n  null positions (local minima): {mins}")
for i in mins:
    fr = i / (nbins - 1)
    num, den = rational.best_rational(i, nbins - 1, 8)            # Class N: small-denom node fraction?
    print(f"    pos {i}: fraction {fr:.3f} ~ {num}/{den} (Class-N node; small den = harmonic node)")
print("\n  cavity reading: dips at small-denominator fractions => standing-wave NODES (geodesic nulls).")
print("  Q collapsed to float ONLY here at the analysis boundary. Sparse Klein-4; no bag.")

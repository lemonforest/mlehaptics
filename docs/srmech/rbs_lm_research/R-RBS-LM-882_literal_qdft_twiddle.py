"""F882: the LITERAL exp(mu*theta) QDFT/ODFT twiddle vs the F881 multi-axis SPIRIT.
Literal twiddle = q(pos) = cos(theta) + mu*sin(theta), mu a UNIT pure imaginary in the algebra
(C: 1 axis e1; H: 3 axes e1e2e3; O: 7 axes e1..e7), applied to the octonion-valued context by
Cayley-Dickson multiply, THEN projected (hashed) to the Klein-4 key. This is the genuine
hypercomplex exponential where a hypercomplex value actually lives in our pipeline. Compared
head-to-head with the F881 scalar-phase spirit (composed klein4_phase_bind) and a no-phase baseline.
srmech-native: cos/sin_series_truncate (exact rational), cascade.cd_mult; no math/numpy; sparse Klein-4.
"""
import json
from fractions import Fraction as Fr
from srmech.amsc import hdc, cascade, format as fmt
from srmech import calculus
from srmech.rbs_lm import substrate as S

D, K, PMAX, N, TERMS = 8192, 2, 24, 1000, 12
MULT = (1, 5, 11, 7, 13, 17, 19)
ISQRT = {1: Fr(1), 3: Fr(57735, 100000), 7: Fr(37796, 100000)}   # rational approx of 1/sqrt(k) (unit mu)
cs = S.ContextSubstrate(D=D, hex_chars=16)
def _dig(s):
    h = fmt.sha256_bytes(s.encode()); return bytes.fromhex(h) if isinstance(h, str) else h
def byte_oct(b):
    d = _dig(f"LoE.byte.{b}"); return tuple((d[i] % 9) - 4 for i in range(8))
def word_oct(w):
    bs = w.encode("utf-8"); p = byte_oct(bs[0])
    for b in bs[1:]: p = tuple(cascade.cd_mult(p, byte_oct(b)))
    return p
def ctx_oct(win):
    p = word_oct(win[0])
    for w in win[1:]: p = tuple(cascade.cd_mult(p, word_oct(w)))
    return p
def _hashseed(coords): return int.from_bytes(_dig(",".join(str(x) for x in coords))[:8], "big")

def cossin(pos):                                  # exact-rational cos/sin of theta = pos/PMAX (radians)
    cn, cd = calculus.cos_series_truncate(pos, PMAX, TERMS)
    sn, sd = calculus.sin_series_truncate(pos, PMAX, TERMS)
    return Fr(cn, cd), Fr(sn, sd)

def twiddle_key(win, pos, kaxes):                 # LITERAL exp(mu*theta): rotate ctx octonion by unit hypercomplex
    p = tuple(Fr(x) for x in ctx_oct(win))
    c, s = cossin(pos)
    inv = ISQRT[kaxes]
    q = [c] + [s * inv if a < kaxes else Fr(0) for a in range(7)]   # cos + (1/sqrt k) sin * (e1..ek)
    pr = cascade.cd_mult(tuple(q), p)             # left twiddle in O
    return hdc.klein4_random(D, seed=_hashseed(pr))

def scalar_key(win, pos, axes):                   # F881 SPIRIT: composed scalar klein4_phase_bind
    k = hdc.klein4_random(D, seed=_hashseed(ctx_oct(win)))
    for a in range(axes):
        k = hdc.klein4_phase_bind(k, ((pos * MULT[a]) % PMAX) / PMAX)
    return k

def plain_key(win, pos):                          # no-phase baseline
    return hdc.klein4_random(D, seed=_hashseed(ctx_oct(win)))

WV = {}
def wv(w):
    if w not in WV:
        WV[w] = cs.bundle_odd([hdc.klein4_bind(hdc.klein4_random(D, seed=b), cs.pos_key(i))
                               for i, b in enumerate(w.encode("utf-8"))])
    return WV[w]

path = "/home/skirklan/corpora/wikipedia/simplewiki_rawbody_instrument_v082.ndjson"
arts = []
with open(path) as f:
    for line in f:
        toks = json.loads(line)["s"].split()[:14]
        if len(toks) >= K + 3: arts.append(toks)
        if len(arts) >= N: break
N = len(arts)

def evaluate(keyfn):
    keysets, sigs = [], []
    for toks in arts:
        p = ["<s>"] * K + toks + ["<e>"]
        ks = [keyfn(p[i - K:i], i) for i in range(K, len(p))]
        keysets.append(ks); sigs.append(cs.bundle_odd(ks))
    samples = [(a, keysets[a][len(keysets[a])//2]) for a in range(0, N, max(1, N//60)) if len(keysets[a]) >= 3]
    ok = sum(1 for a, qk in samples if max(range(N), key=lambda b: hdc.klein4_similarity(qk, sigs[b])) == a)
    route = ok / len(samples)
    rep_ok = rep_tot = 0
    for ai in range(0, min(N, 200), 13):
        toks = arts[ai]; p = ["<s>"] * K + toks + ["<e>"]
        binds = [hdc.klein4_bind(keyfn(p[i-K:i], i), wv(p[i])) for i in range(K, len(p))]
        chunks = hdc.klein4_chunk_bundle(binds, 8); vocab = sorted(set(toks) | {"<e>"})
        ctx, out = ["<s>"] * K, []
        for m in range(16):
            sc = hdc.klein4_chunk_resolve(chunks, keyfn(ctx, K+m), [wv(w) for w in vocab])
            nx = vocab[max(range(len(vocab)), key=lambda j: sc[j])]; out.append(nx); ctx = (ctx+[nx])[-K:]
            if nx == "<e>": break
        tgt = toks + ["<e>"]; rep_ok += sum(1 for x, y in zip(out, tgt) if x == y); rep_tot += len(tgt)
    return route, rep_ok / rep_tot

print(f"=== F882 literal exp(mu*theta) QDFT twiddle vs F881 spirit @ N={N} ===")
print("  condition                         | routing | reproduction")
conds = [
    ("no phase (baseline)",                 plain_key),
    ("F881 spirit scalar axes=1 (C)",       lambda w,p: scalar_key(w,p,1)),
    ("F881 spirit scalar axes=3 (H rung)",  lambda w,p: scalar_key(w,p,3)),
    ("LITERAL exp(mu.th) C (1 axis)",       lambda w,p: twiddle_key(w,p,1)),
    ("LITERAL exp(mu.th) H/QDFT (3 axis)",  lambda w,p: twiddle_key(w,p,3)),
    ("LITERAL exp(mu.th) O/ODFT (7 axis)",  lambda w,p: twiddle_key(w,p,7)),
]
for name, fn in conds:
    r, rep = evaluate(fn)
    print(f"  {name:33s} |  {r:.2f}   |   {rep:.3f}")
print("\n  literal twiddle = exp(mu*theta) in O via cd_mult (cos/sin exact-rational series), then project.")
print("  SPARSE Klein-4; no math/numpy; no bag. mu unit via rational 1/sqrt(k).")

"""F883: inverse-coupling rotation sandwich q*p*conj(q) vs the single-sided literal twiddle (F882).
User idea: DFT each piece of the QDFT but couple the two sides as INVERSES -> the genuine rotation
sandwich q.p.q-bar (left q, right conjugate(q) = inverse for unit q), the true SO rotation of the
imaginary part by 2*theta about mu. Does it raise the 0.81 ceiling? Compare C/H/O single-sided vs
sandwich. srmech-native: cos/sin_series_truncate, cd_mult, cd_conjugate; sparse Klein-4; no math/numpy/bag.
"""
import json
from fractions import Fraction as Fr
from srmech.amsc import hdc, cascade, format as fmt
from srmech import calculus
from srmech.rbs_lm import substrate as S

D, K, PMAX, N, TERMS = 8192, 2, 24, 1000, 12
ISQRT = {1: Fr(1), 3: Fr(57735, 100000), 7: Fr(37796, 100000)}
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
def cossin(pos):
    cn, cd = calculus.cos_series_truncate(pos, PMAX, TERMS)
    sn, sd = calculus.sin_series_truncate(pos, PMAX, TERMS)
    return Fr(cn, cd), Fr(sn, sd)
def unit_q(pos, kaxes):
    c, s = cossin(pos); inv = ISQRT[kaxes]
    return tuple([c] + [s * inv if a < kaxes else Fr(0) for a in range(7)])

def single_key(win, pos, kaxes):                  # F882: left twiddle q*p
    p = tuple(Fr(x) for x in ctx_oct(win))
    return hdc.klein4_random(D, seed=_hashseed(cascade.cd_mult(unit_q(pos, kaxes), p)))
def sandwich_key(win, pos, kaxes):                # F883: inverse-coupling rotation q*p*conj(q)
    p = tuple(Fr(x) for x in ctx_oct(win)); q = unit_q(pos, kaxes)
    pr = cascade.cd_mult(cascade.cd_mult(q, p), cascade.cd_conjugate(q))
    return hdc.klein4_random(D, seed=_hashseed(pr))

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

print(f"=== F883 inverse-coupling sandwich q.p.conj(q) vs single-sided literal @ N={N} ===")
print("  condition                              | routing | reproduction")
conds = [
    ("single-sided q.p     C", lambda w,p: single_key(w,p,1)),
    ("single-sided q.p     H", lambda w,p: single_key(w,p,3)),
    ("single-sided q.p     O", lambda w,p: single_key(w,p,7)),
    ("sandwich q.p.conj(q) C", lambda w,p: sandwich_key(w,p,1)),
    ("sandwich q.p.conj(q) H", lambda w,p: sandwich_key(w,p,3)),
    ("sandwich q.p.conj(q) O", lambda w,p: sandwich_key(w,p,7)),
]
for name, fn in conds:
    r, rep = evaluate(fn)
    print(f"  {name:38s} |  {r:.2f}   |   {rep:.3f}")
print("\n  sandwich = genuine SO rotation of imag part by 2theta about mu (inverse coupling = conj on right).")
print("  SPARSE Klein-4; cd_mult/cd_conjugate + exact-rational cos/sin; no math/numpy/bag.")

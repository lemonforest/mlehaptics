"""F889: a sigma<->theta Mobius-aware router vs the F882 flat-torus ODFT ceiling (0.81).
Mobius (F888): sign-flip == half-phase advance. Two ways to exploit it, both on the F882 O-twiddle key:
  (a) mobius-MAX  : route score = max over BOTH sigma-sheets (q and flip(q)) vs flat sigs.
  (b) mobius-PACK : encode position as (sigma sign-bit, theta in [0,1/2)) -> the sign is an extra
                    address bit at double phase-resolution (the Mobius coordinatization).
Baseline = F882 single-sided ODFT, flat routing. Measure routing acc @ N=1000 vs 0.81 + reproduction.
srmech-native; Q-aware compares; sparse Klein-4; no bag.
"""
import json
from fractions import Fraction as Fr
from srmech.amsc import hdc, cascade, format as fmt
from srmech import calculus
from srmech.rbs_lm import substrate as S

D, K, PMAX, N, TERMS = 8192, 2, 24, 1000, 12
ISQRT7 = Fr(37796, 100000)
cs = S.ContextSubstrate(D=D, hex_chars=16)
flip = hdc.klein4_chirality_flip_gamma5
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
def ctx_oct(win):
    p = word_oct(win[0])
    for w in win[1:]: p = tuple(cascade.cd_mult(p, word_oct(w)))
    return p
def _hs(c): return int.from_bytes(_dig(",".join(str(x) for x in c))[:8], "big")
def cossin(num, den):
    cn, cd = calculus.cos_series_truncate(num, den, TERMS); sn, sd = calculus.sin_series_truncate(num, den, TERMS)
    return Fr(cn, cd), Fr(sn, sd)
def odft_key(win, num, den):                      # F882 single-sided O-twiddle, angle = num/den
    p = tuple(Fr(x) for x in ctx_oct(win)); c, s = cossin(num, den)
    q = [c] + [s * ISQRT7]*7
    return hdc.klein4_random(D, seed=_hs(cascade.cd_mult(tuple(q), p)))
def key_base(win, pos): return odft_key(win, pos, PMAX)                 # flat torus (baseline)
def key_pack(win, pos):                                                 # Mobius: hi bit -> sign, lo -> theta in [0,1/2)
    half = PMAX // 2; sigma = (pos // half) % 2; theta_num = (pos % half)
    k = odft_key(win, theta_num, PMAX)            # theta in [0, half/PMAX) = [0,0.5)
    return flip(k) if sigma else k
WV = {}
def wv(w):
    if w not in WV: WV[w] = word_k4(w)
    return WV[w]
sim = hdc.klein4_similarity

path = "/home/skirklan/corpora/wikipedia/simplewiki_rawbody_instrument_v082.ndjson"
arts = []
with open(path) as fh:
    for line in fh:
        t = json.loads(line)["s"].split()[:14]
        if len(t) >= K + 3: arts.append(t)
        if len(arts) >= N: break
N = len(arts)

def build(keyfn):
    keysets, sigs = [], []
    for toks in arts:
        p = ["<s>"]*K + toks + ["<e>"]
        ks = [keyfn(p[i-K:i], i) for i in range(K, len(p))]
        keysets.append(ks); sigs.append(cs.bundle_odd(ks))
    return keysets, sigs
def samples_of(keysets):
    return [(a, keysets[a][len(keysets[a])//2]) for a in range(0, N, max(1, N//60)) if len(keysets[a]) >= 3]

print(f"=== F889 Mobius-aware router vs F882 flat ODFT (0.81) @ N={N} ===")
# baseline (flat torus) + mobius-MAX share the same flat sigs
ks_b, sg_b = build(key_base); samp_b = samples_of(ks_b)
def acc(route): return sum(1 for a,_ in samp_b if route(a)==a)/len(samp_b)
base = acc(lambda a: max(range(N), key=lambda b: sim(samp_b[[s[0] for s in samp_b].index(a)][1], sg_b[b])))
# cleaner: precompute
def route_flat(qk): return max(range(N), key=lambda b: sim(qk, sg_b[b]))
def route_max(qk):
    fqk = flip(qk)
    return max(range(N), key=lambda b: max(sim(qk, sg_b[b]), sim(fqk, sg_b[b])))
base = sum(1 for a,qk in samp_b if route_flat(qk)==a)/len(samp_b)
mmax = sum(1 for a,qk in samp_b if route_max(qk)==a)/len(samp_b)
# mobius-PACK: its own keys/sigs
ks_p, sg_p = build(key_pack); samp_p = samples_of(ks_p)
def route_p(qk): return max(range(N), key=lambda b: sim(qk, sg_p[b]))
pack = sum(1 for a,qk in samp_p if route_p(qk)==a)/len(samp_p)
print(f"  baseline flat ODFT (F882) : {base:.2f}   (target 0.81)")
print(f"  mobius-MAX (both sheets)   : {mmax:.2f}")
print(f"  mobius-PACK (sign=hi-bit)  : {pack:.2f}")
print("\n  Q-aware compares; sparse Klein-4 + O-twiddle; no bag. beats 0.81 IFF a mobius variant > baseline.")

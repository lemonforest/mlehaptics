"""F870: take the composed resonator BEYOND toy scale -- find where it breaks.
Part 1: the fundamental capacity curve -- one stored relationship's match-count as the
        single Klein-4 bundle M fills with N binds. Where does it cross the gate (->break)?
        + does chunked-M (F839, capacity C) hold it flat?
Part 2: reproduction on REAL simplewiki token sequences (v082 's' field) as the corpus
        grows -- does the single-M break on real data, and does chunking fix it?
srmech-native, integer match-counts (no float, F868), no bag.
"""
import json
from srmech.amsc import hdc, cascade, format as fmt
from srmech.rbs_lm import substrate as S

D = 10000
cs = S.ContextSubstrate(D=D, hex_chars=16)
K, WPOS = 2, 100
CHANCE = D // 4
GATE = (CHANCE * 13) // 10

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
def key_sharp(win):
    p = word_oct(win[0])
    for w in win[1:]: p = tuple(cascade.cd_mult(p, word_oct(w)))
    s = ",".join(str(x) for x in p)
    return hdc.klein4_random(D, seed=int.from_bytes(_dig(s)[:8], "big"))
def mcount(a, b): return sum(1 for x, y in zip(a.tolist(), b.tolist()) if x == y)

print("=== Part 1: capacity curve -- one stored relationship's match-count as M fills ===")
print(f"  (chance={CHANCE}, gate={GATE}, clean single bind=D={D})")
key0 = hdc.klein4_random(D, seed=999999); val0 = hdc.klein4_random(D, seed=888888)
target = hdc.klein4_bind(key0, val0)
print("  N binds | single-M count | chunked-M(C=8) count | single>gate?")
for N in [1, 3, 8, 30, 100, 300, 1000, 3000]:
    others = [hdc.klein4_bind(hdc.klein4_random(D, seed=i), hdc.klein4_random(D, seed=100000 + i)) for i in range(N - 1)]
    allb = [target] + others
    single = cs.bundle_odd(allb)
    c_single = mcount(hdc.klein4_unbind(single, key0), val0)
    # chunked: chunks of C=8; target in chunk 0; recall = max over chunks of the match
    C = 8
    chunks = [cs.bundle_odd(allb[i:i + C]) for i in range(0, len(allb), C)]
    c_chunk = max(mcount(hdc.klein4_unbind(ch, key0), val0) for ch in chunks)
    print(f"  {N:6d}  |   {c_single:6d}      |   {c_chunk:6d}            | {c_single >= GATE}")

print("\n=== Part 2: reproduction on REAL simplewiki sequences as the corpus grows ===")
path = "/home/skirklan/corpora/wikipedia/simplewiki_rawbody_instrument_v082.ndjson"
L = 12
arts = []
with open(path) as f:
    for line in f:
        r = json.loads(line)
        toks = r["s"].split()[:L]
        if len(toks) >= K + 2: arts.append(toks)
        if len(arts) >= 300: break
WV = {}
def wv(w):
    if w not in WV: WV[w] = word_k4(w)
    return WV[w]

def build_single(corpus):
    binds = []
    for toks in corpus:
        p = ["<s>"] * K + toks
        for i in range(K, len(p)):
            binds.append(hdc.klein4_bind(key_sharp(p[i - K:i]), wv(p[i])))
    return cs.bundle_odd(binds), len(binds)

import random
def repro_rate(M, corpus, n_probe=40):
    # sample stored (ctx->next) positions; is the correct next the argmax over true+distractors?
    probes, ok, counts = 0, 0, []
    pool = sorted(WV.keys())
    for toks in corpus:
        p = ["<s>"] * K + toks
        for i in range(K, len(p)):
            probe = hdc.klein4_unbind(M, key_sharp(p[i - K:i]))
            true = p[i]; ct = mcount(probe, wv(true)); counts.append(ct)
            distractors = [w for w in pool if w != true][:30]
            win = ct >= max((mcount(probe, wv(w)) for w in distractors), default=0)
            ok += int(win); probes += 1
            if probes >= n_probe: break
        if probes >= n_probe: break
    return ok / probes, sum(counts) // len(counts)

print("  N arts | binds | mean sharp-count | reproduction rate (vs 30 distractors)")
for N in [1, 3, 10, 30, 100, 300]:
    corpus = arts[:N]
    M, nb = build_single(corpus)
    rate, mean_ct = repro_rate(M, corpus)
    flag = "" if mean_ct >= GATE else "  <- below gate"
    print(f"  {N:5d}  | {nb:5d} |   {mean_ct:6d}{flag}        |  {rate:.2f}")
print(f"\n  (gate={GATE}, chance={CHANCE}.)")

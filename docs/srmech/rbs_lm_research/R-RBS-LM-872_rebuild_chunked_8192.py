"""F872: rebuild the scale test as CHUNKED-M at the ATTESTED dim, and confirm
reproduction stays flat where the single bundle cliffed (F870).

DIM DISCIPLINE (F871 -- baked in, do not regress):
  D = 2^13 = 8192. NOT a round decimal (10000 was an unattested magic number).
  - D=2^n is Class-A attested + packs the Klein-4 boolean belly (2 bits/slot -> 4 slots/byte
    once srmech bit-packs; latent today).
  - Capacity is DIMENSION-INDEPENDENT (~24-bind SNR wall, 1/sqrt(N)); you CANNOT grow D past it.
    => CHUNK for capacity (C~8); SIZE D for reliability (~sqrt(D)). 8192 retires 10000.
srmech-native, integer match-counts (no float, F868), no bag (F865).
"""
import json
from srmech.amsc import hdc, cascade, format as fmt
from srmech.rbs_lm import substrate as S

D = 8192                                  # F871: attested 2^13, retires the magic 10000
C = 8                                     # F839 sweet-spot chunk capacity (<= the ~24 SNR wall)
K = 2
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
def key_sharp(win):
    p = word_oct(win[0])
    for w in win[1:]: p = tuple(cascade.cd_mult(p, word_oct(w)))
    return hdc.klein4_random(D, seed=int.from_bytes(_dig(",".join(str(x) for x in p))[:8], "big"))
def mcount(a, b): return sum(1 for x, y in zip(a.tolist(), b.tolist()) if x == y)

path = "/home/skirklan/corpora/wikipedia/simplewiki_rawbody_instrument_v082.ndjson"
L = 12
arts = []
with open(path) as f:
    for line in f:
        toks = json.loads(line)["s"].split()[:L]
        if len(toks) >= K + 2: arts.append(toks)
        if len(arts) >= 300: break
WV = {}
def wv(w):
    if w not in WV: WV[w] = word_k4(w)
    return WV[w]

def binds_of(corpus):
    out = []
    for toks in corpus:
        p = ["<s>"] * K + toks
        for i in range(K, len(p)):
            out.append((key_sharp(p[i - K:i]), wv(p[i]), p[i], p[i - K:i]))
    return out

def repro(corpus, chunked):
    bnd = binds_of(corpus)
    binds_hv = [hdc.klein4_bind(k, v) for k, v, _, _ in bnd]
    if chunked:
        store = [cs.bundle_odd(binds_hv[i:i + C]) for i in range(0, len(binds_hv), C)]
    else:
        store = [cs.bundle_odd(binds_hv)]
    pool = sorted(WV.keys())[:20]         # distractor pool (capped for tractability)
    ok, probes = 0, 0
    for k, v, true, ctx in bnd:
        probes_c = [hdc.klein4_unbind(M, k) for M in store]
        def score(w):                     # MEASUREMENT scoring via native klein4_similarity (fast, ranking-only;
            wvv = wv(w)                    #   the inference path keeps exact integer match-counts, F868)
            return max(hdc.klein4_similarity(pc, wvv) for pc in probes_c)
        st = score(true)
        win = st >= max((score(w) for w in pool if w != true), default=0.0)
        ok += int(win); probes += 1
        if probes >= 30: break
    return ok / probes, len(binds_hv), len(store)

print(f"=== F872 rebuild: single-M vs chunked-M (C={C}) at the attested D={D} ===")
print("  N arts | binds | chunks | single-M repro | chunked-M repro")
for N in [1, 3, 10, 30, 100, 300]:
    corpus = arts[:N]
    r_single, nb, _ = repro(corpus, chunked=False)
    r_chunk, _, nch = repro(corpus, chunked=True)
    print(f"  {N:5d}  | {nb:5d} | {nch:5d}  |     {r_single:.2f}        |     {r_chunk:.2f}")
print(f"\n  (D={D} attested 2^13; C={C}; single-M cliffs as the bundle over-stuffs past the ~24 wall,")
print("   chunked-M should hold flat -- recall = max-over-chunks (cost O(chunks); the sedenion")
print("   register / navigate is the addressing layer that bounds that scan -- F465/F873).")

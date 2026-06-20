"""F881: does a HYPERCOMPLEX (QDFT/ODFT-style) phase fiber help the resolution loss?
Current phase = 2-thing (scalar theta, abelian, F878). Prototype the SPIRIT of QDFT(H, 3 axes)/
ODFT(O, 7 axes): give the position-key several INDEPENDENT phase axes (distinct position-derived
angles) via composed klein4_phase_bind. Test on (a) routing @ N (the live 0.70 loss, F880) and
(b) within-page reproduction (must not break F878's 1.0). This is the multi-axis spirit, NOT the
literal exp(mu*theta) twiddle (that needs srmech #205). SPARSE Klein-4, no bag, no dense, no numpy.
"""
import json
from srmech.amsc import hdc, cascade, format as fmt
from srmech.rbs_lm import substrate as S

D, K, PMAX, N = 8192, 2, 24, 1000
MULT = (1, 5, 11, 7, 13, 17, 19)          # distinct per-axis phase multipliers (coprime-ish to PMAX=24)
cs = S.ContextSubstrate(D=D, hex_chars=16)
def _dig(s):
    h = fmt.sha256_bytes(s.encode()); return bytes.fromhex(h) if isinstance(h, str) else h
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
def key_at(win, pos, axes):               # axes=1 -> F878 scalar phase; 3 -> QDFT-like; 7 -> ODFT-like
    k = ctx_key(win)
    for a in range(axes):
        k = hdc.klein4_phase_bind(k, ((pos * MULT[a]) % PMAX) / PMAX)
    return k
WV = {}
def word_k4(w):
    return cs.bundle_odd([hdc.klein4_bind(hdc.klein4_random(D, seed=b), cs.pos_key(i))
                          for i, b in enumerate(w.encode("utf-8"))])
def wv(w):
    if w not in WV: WV[w] = word_k4(w)
    return WV[w]

path = "/home/skirklan/corpora/wikipedia/simplewiki_rawbody_instrument_v082.ndjson"
arts = []
with open(path) as f:
    for line in f:
        toks = json.loads(line)["s"].split()[:14]
        if len(toks) >= K + 3: arts.append(toks)
        if len(arts) >= N: break
N = len(arts)

def run(axes):
    keysets, sigs = [], []
    for toks in arts:
        p = ["<s>"] * K + toks + ["<e>"]
        ks = [key_at(p[i - K:i], i, axes) for i in range(K, len(p))]
        keysets.append(ks); sigs.append(cs.bundle_odd(ks))
    # routing: a stored mid-context -> its home article
    samples = [(a, keysets[a][len(keysets[a])//2]) for a in range(0, N, max(1, N//60)) if len(keysets[a]) >= 3]
    ok = 0
    for a, qk in samples:
        if max(range(N), key=lambda b: hdc.klein4_similarity(qk, sigs[b])) == a: ok += 1
    route = ok / len(samples)
    # within-page reproduction (must stay high; F878)
    rep_ok = rep_tot = 0
    for ai in range(0, min(N, 200), 13):
        toks = arts[ai]; p = ["<s>"] * K + toks + ["<e>"]
        binds = [hdc.klein4_bind(key_at(p[i-K:i], i, axes), wv(p[i])) for i in range(K, len(p))]
        chunks = hdc.klein4_chunk_bundle(binds, 8); vocab = sorted(set(toks) | {"<e>"})
        ctx, out = ["<s>"] * K, []
        for m in range(16):
            sc = hdc.klein4_chunk_resolve(chunks, key_at(ctx, K+m, axes), [wv(w) for w in vocab])
            nx = vocab[max(range(len(vocab)), key=lambda j: sc[j])]; out.append(nx); ctx = (ctx+[nx])[-K:]
            if nx == "<e>": break
        tgt = toks + ["<e>"]; rep_ok += sum(1 for x, y in zip(out, tgt) if x == y); rep_tot += len(tgt)
    return route, rep_ok / rep_tot

print(f"=== hypercomplex-phase probe @ N={N} (routing = live F880 loss; reproduction = F878) ===")
print("  phase axes | algebra      | routing acc | within-page reproduction")
for axes, name in ((1, "2-thing (C)"), (3, "QDFT-like(H)"), (7, "ODFT-like(O)")):
    r, rep = run(axes)
    print(f"      {axes:2d}     | {name:12s} |    {r:.2f}     |   {rep:.3f}")
print("\n  multi-axis = SPIRIT of QDFT/ODFT (composed klein4_phase_bind); literal exp(mu*theta)")
print("  twiddle = srmech #203-205. SPARSE Klein-4; no bag, no dense, no numpy.")

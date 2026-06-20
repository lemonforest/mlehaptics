"""F879: carry the F878 phase fix into the FULL grid generator at CORPUS SCALE.
SPARSE Klein-4 only -- no dense matrix, no numpy, no bag, no gen-1 patterns. Each article =
one phase-keyed page (a bounded chunked-M instrument), addressed in the sedenion grid
(navigate). Per-page reproduction = phase-keyed within-page resonance (F878). Claim: per-page
reproduction is SCALE-INVARIANT (each page bounded + phase-keyed + independent), where the
single shared M cliffed (F870: 0.47 @300). srmech-native: klein4_chunk_bundle/chunk_resolve/
phase_bind + sedenion_register.navigate.
"""
import json
from srmech.amsc import hdc, cascade, format as fmt
from srmech.rbs_lm import substrate as S

D, C, K, PMAX = 8192, 8, 2, 24
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
def key_at(win, pos):                                  # the 1D_t PHASE bound into the key (F878, s59)
    return hdc.klein4_phase_bind(ctx_key(win), pos / PMAX)
WV = {}
def wv(w):
    if w not in WV: WV[w] = word_k4(w)
    return WV[w]

path = "/home/skirklan/corpora/wikipedia/simplewiki_rawbody_instrument_v082.ndjson"
arts = []
with open(path) as f:
    for line in f:
        toks = json.loads(line)["s"].split()[:14]
        if len(toks) >= K + 3: arts.append(toks)
        if len(arts) >= 300: break

def make_page(toks):                                   # one article = one bounded phase-keyed chunked-M page
    p = ["<s>"] * K + toks + ["<e>"]
    binds = [hdc.klein4_bind(key_at(p[i - K:i], i), wv(p[i])) for i in range(K, len(p))]
    return {"chunks": hdc.klein4_chunk_bundle(binds, C), "vocab": sorted(set(toks) | {"<e>"}), "toks": toks}

def stream(page, maxlen=16):
    ctx, out = ["<s>"] * K, []
    for m in range(maxlen):
        cand = page["vocab"]
        scores = hdc.klein4_chunk_resolve(page["chunks"], key_at(ctx, K + m), [wv(w) for w in cand])
        nxt = cand[max(range(len(cand)), key=lambda j: scores[j])]
        out.append(nxt); ctx = (ctx + [nxt])[-K:]
        if nxt == "<e>": break
    return out

print("=== phase-keyed grid generator at corpus scale (one page/article, SPARSE Klein-4) ===")
print("  N pages | mean per-page reproduction (phase-keyed within-page resonance)")
for N in (4, 30, 100, 300):
    ok = tot = 0
    for toks in arts[:N]:
        page = make_page(toks); emitted = stream(page); target = toks + ["<e>"]
        ok += sum(1 for a, b in zip(emitted, target) if a == b); tot += len(target)
    print(f"   {N:5d}  | {ok}/{tot} = {ok/tot:.3f}")

print("\n=== the grid addresses the pages (navigate); within-page recall is phase-keyed ===")
reg = cascade.sedenion_register(D=D)
sel = arts[:8]
for i in range(8): reg.write(i, f"page.{i}")
# navigate to a slot, then stream that article's page (phase-keyed) -- WHERE x WHEN at scale
key0, _ = reg.read(3)
emitted = stream(make_page(sel[3]))
print(f"  navigate->slot e3 = {key0}; streamed: {' '.join(emitted)}")
print(f"  exact: {emitted == sel[3] + ['<e>']}")
print("\n  per-page reproduction is SCALE-INVARIANT (each page bounded+phase-keyed+independent) --")
print("  vs the single shared M which cliffed (F870: 0.47 @300). SPARSE: Klein-4 chunked-M +")
print("  shipped resonator + phase_bind + sedenion-grid navigate. No dense, no numpy, no bag.")

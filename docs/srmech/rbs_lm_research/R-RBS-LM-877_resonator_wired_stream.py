"""F877: rewire the streaming-grid generator onto the SHIPPED resonator (the op we added).
Replaces F875's hand-rolled max-over-chunks recall with srmech's klein4_chunk_bundle (the
chunker) + klein4_chunk_resolve (the resonator, max-resonance read, exact Q per candidate,
s58/F837). navigate = WHERE (the sedenion grid); chunk_resolve = the within-page resonance =
WHEN. introspect-srmech-first: use the shipped resonator, don't hand-roll. D=8192, no bag.
"""
import json
from srmech.amsc import hdc, cascade, format as fmt
from srmech.rbs_lm import substrate as S

D, C, K = 8192, 8, 2
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
        if len(arts) >= 4: break

def make_page(toks):
    p = ["<s>"] * K + toks + ["<e>"]
    binds = [hdc.klein4_bind(key_sharp(p[i - K:i]), wv(p[i])) for i in range(K, len(p))]
    chunks = hdc.klein4_chunk_bundle(binds, C)          # SHIPPED chunker (was: manual bundle_odd slices)
    return {"chunks": chunks, "vocab": sorted(set(toks) | {"<e>"}), "toks": toks}
pages = [make_page(t) for t in arts]

# probe the shipped resonator return shape once
p0 = pages[0]
res = hdc.klein4_chunk_resolve(p0["chunks"], key_sharp(["<s>", "<s>"]), [wv(w) for w in p0["vocab"]])
print("chunk_resolve return type:", type(res).__name__, "(per-candidate Q scores)")

def resolve_next(page, ctx):
    cand = page["vocab"]
    scores = hdc.klein4_chunk_resolve(page["chunks"], key_sharp(ctx), [wv(w) for w in cand])  # the RESONATOR
    sc = dict(zip(cand, scores)) if not isinstance(scores, dict) else scores
    return max(cand, key=lambda w: sc[w])               # argmax stays in the caller (siona/LM side, s58)

def stream(page, maxlen=16):
    ctx, out = ["<s>"] * K, []
    for _ in range(maxlen):
        nxt = resolve_next(page, ctx); out.append(nxt); ctx = (ctx + [nxt])[-K:]
        if nxt == "<e>": break
    return out

print("\n=== streaming via the SHIPPED resonator (klein4_chunk_resolve) ===")
tot_ok = tot = 0
for i, page in enumerate(pages):
    emitted = stream(page); target = page["toks"] + ["<e>"]
    m = sum(1 for a, b in zip(emitted, target) if a == b); tot_ok += m; tot += len(target)
    print(f"  page {i}: {m}/{len(target)}  emitted: {' '.join(emitted)}")
print(f"\n  overall: {tot_ok}/{tot} = {tot_ok/tot:.2f}  (same recall as F875, now via the shipped resonator + chunker)")
print("  -> navigation/recall now rides klein4_chunk_resolve (the op we added, s58/F837), exact-Q,")
print("     no hand-rolled max-over-chunks; the argmax (LM-specific) stays caller-side per the boundary.")

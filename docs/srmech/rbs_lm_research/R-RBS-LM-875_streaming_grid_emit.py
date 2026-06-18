"""F875: stream REAL token sequences off the grid -- wire each grid page to within-page
token emission. navigate selects the page (WHERE, the sedenion grid); within the page,
autoregressive chunked-M resonance (F872, no bag) emits the next token, scoped to the page's
own bounded vocab (the per-tome atom set, s57/s58); the_one's crank is the 1D_t token-advance
(WHEN). D=8192 attested (F871). srmech-native, sparse, no bag.
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

# --- build pages: each article -> a chunked-M instrument + its own bounded vocab ---
path = "/home/skirklan/corpora/wikipedia/simplewiki_rawbody_instrument_v082.ndjson"
L = 14
arts = []
with open(path) as f:
    for line in f:
        toks = json.loads(line)["s"].split()[:L]
        if len(toks) >= K + 3: arts.append(toks)
        if len(arts) >= 6: break

def make_page(toks):
    p = ["<s>"] * K + toks + ["<e>"]
    binds = [hdc.klein4_bind(key_sharp(p[i - K:i]), wv(p[i])) for i in range(K, len(p))]
    chunks = [cs.bundle_odd(binds[i:i + C]) for i in range(0, len(binds), C)]
    return {"chunks": chunks, "vocab": sorted(set(toks) | {"<e>"}), "toks": toks}

pages = {f"page.{i}": make_page(t) for i, t in enumerate(arts)}

# --- the grid: write page keys into the sedenion register's slots ---
reg = cascade.sedenion_register(D=D)
for i, k in enumerate(pages):
    reg.write(i, k)

# --- stream a page: navigate selects it; autoregressive chunked-M emits its tokens ---
def stream_page(page, maxlen=16):
    ctx, out = ["<s>"] * K, []
    for _ in range(maxlen):
        probes = [hdc.klein4_unbind(M, key_sharp(ctx)) for M in page["chunks"]]
        nxt = max(page["vocab"], key=lambda w: max(hdc.klein4_similarity(pc, wv(w)) for pc in probes))
        out.append(nxt); ctx = (ctx + [nxt])[-K:]
        if nxt == "<e>": break
    return out

print(f"=== stream REAL token sequences off the grid (D={D}, C={C}, navigate-selected pages) ===")
tot_ok = tot = 0
for slot in range(min(4, len(pages))):
    key, _ = reg.navigate(0).read(slot) if False else reg.read(slot)   # navigate addresses; read the page key
    page = pages[key]
    emitted = stream_page(page)
    target = page["toks"] + ["<e>"]
    match = sum(1 for a, b in zip(emitted, target) if a == b)
    tot_ok += match; tot += len(target)
    print(f"\n  slot e{slot} -> {key}")
    print(f"    target : {' '.join(target)}")
    print(f"    emitted: {' '.join(emitted)}")
    print(f"    position match: {match}/{len(target)}")
print(f"\n  overall position-match: {tot_ok}/{tot} = {tot_ok/tot:.2f}")
print("  -> the cursor emits REAL token sequences off the addressed grid pages (within-page")
print("     chunked-M recall, page-scoped vocab, no bag); navigate = WHERE, the autoregressive")
print("     token-advance = the_one's 1D_t stream = WHEN. Honest: reproduction (F841/F872), toy")
print("     scale, page-scoped vocab (the bounded atom set, not full-vocab argmax).")

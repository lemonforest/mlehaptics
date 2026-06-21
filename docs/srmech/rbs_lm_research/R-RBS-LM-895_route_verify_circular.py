"""F895 — push routing past the flat-top1 ceiling: ROUTE -> SHORTLIST (resonance top-K) -> VERIFY
(within-page recall confidence). The flat router saturates (F880: 0.70 @2000) because one argmax
competes vs N distractor bundles. But the address layer is exact+EC (F891/893) -> the router only
needs the right page in a top-K shortlist, then a sharper verify picks it. Verify(page) = how
confidently the query context recalls from that page's chunked-M (F879/F853 coarse-route->fine-verify).
Measure: top-K recall (is the true page in the top-K?) + route-verify accuracy vs flat-top1. Sparse.
"""
import json
from srmech.amsc import hdc, cascade, format as fmt
from srmech.rbs_lm import substrate as S

D, K, PMAX, N = 8192, 2, 24, 2000
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
def fl(q): return q.as_float() if hasattr(q, "as_float") else q

path = "/home/skirklan/corpora/wikipedia/simplewiki_rawbody_instrument_v082.ndjson"
arts = []
with open(path) as f:
    for line in f:
        t = json.loads(line)["s"].split()[:14]
        if len(t) >= K + 3: arts.append(t)
        if len(arts) >= N: break
N = len(arts)
print(f"=== F895 route->shortlist->verify @ N={N} (flat baseline F880 = 0.70) ===")

def make_page(toks):
    p = ["<s>"]*K + toks + ["<e>"]
    binds = [hdc.klein4_bind(key_at(p[i-K:i], i), wv(p[i])) for i in range(K, len(p))]
    return {"chunks": hdc.klein4_chunk_bundle(binds, 8), "vocab": sorted(set(toks) | {"<e>"})}
def page_sig(toks):
    p = ["<s>"]*K + toks + ["<e>"]
    return cs.bundle_odd([key_at(p[i-K:i], i) for i in range(K, len(p))])

sigs, pages = [], []
for toks in arts:
    sigs.append(page_sig(toks)); pages.append(make_page(toks))

samples = []
for a in range(0, N, max(1, N//80)):
    toks = arts[a]; p = ["<s>"]*K + toks + ["<e>"]; mid = K + len(toks)//2
    samples.append((a, key_at(p[mid-K:mid], mid), p[mid-K:mid], mid))

# rank all pages by resonance once per query (the shortlist source)
def ranked(qk): return sorted(range(N), key=lambda b: fl(hdc.klein4_similarity(qk, sigs[b])), reverse=True)
def verify(cand, ctx, pos):              # MARGIN: a confident (bound) recall peaks; noise is flat
    pg = pages[cand]
    sc = sorted((fl(x) for x in hdc.klein4_chunk_resolve(pg["chunks"], key_at(ctx, pos), [wv(w) for w in pg["vocab"]])), reverse=True)
    return (sc[0] - sc[1]) if len(sc) > 1 else sc[0]   # top1 - top2

Ks = [1,3,5,10,20]
topk_hit = {k:0 for k in Ks}; rv_hit = {k:0 for k in Ks}
for a, qk, ctx, pos in samples:
    rk = ranked(qk)
    for k in Ks:
        short = rk[:k]
        topk_hit[k] += int(a in short)
        best = max(short, key=lambda c: verify(c, ctx, pos))
        rv_hit[k] += int(best == a)
n = len(samples)
print("   K  | top-K recall (true page in top-K) | route+verify(MARGIN) accuracy")
for k in Ks:
    print(f"  {k:3d} |        {topk_hit[k]/n:.2f}                  |     {rv_hit[k]/n:.2f}")
print(f"\n  flat top-1 = {topk_hit[1]/n:.2f} (the F880 baseline). route+verify lifts it IFF top-K recall >> top-1")
print("  AND the margin discriminates the shortlist. Sparse Klein-4; resonance + within-page resolve; no bag.")

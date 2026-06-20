"""F880: content-routed navigation + scale-up off toy. SPARSE Klein-4, no bag, no dense, no numpy.
Each article = a page; its routing SIGNATURE = bundle of its phase-keyed CONTEXT-KEYS (the set of
order/phase-aware contexts it knows -- NOT a bag of content words). Route(query-context) = resonate
the query key vs the signatures (the resonator one level up), navigate to the winner, then phase-
keyed within-page stream (F879). Hierarchical group-signatures -> O(sqrt N) instead of O(N).
srmech-native: klein4_random/bind/bundle/similarity/phase_bind/chunk_bundle/chunk_resolve + sedenion grid.
"""
import json
from srmech.amsc import hdc, cascade, format as fmt
from srmech.rbs_lm import substrate as S

D, C, K, PMAX = 8192, 8, 2, 24
N = 2000                                  # scale-up: 6.7x off the 300-article toy (271k = offline batch)
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

path = "/home/skirklan/corpora/wikipedia/simplewiki_rawbody_instrument_v082.ndjson"
arts = []
with open(path) as f:
    for line in f:
        toks = json.loads(line)["s"].split()[:14]
        if len(toks) >= K + 3: arts.append(toks)
        if len(arts) >= N: break
N = len(arts)

def ctx_keys(toks):                       # the page's (phase-keyed) context-keys -- order/phase-aware, NOT a word-bag
    p = ["<s>"] * K + toks + ["<e>"]
    return [(key_at(p[i - K:i], i), p[i - K:i], i) for i in range(K, len(p))]

print(f"=== building {N} page routing-signatures (bundle of phase-keyed context-keys; sparse, no bag) ===")
sigs, keysets = [], []
for toks in arts:
    cks = ctx_keys(toks)
    keysets.append(cks)
    sigs.append(cs.bundle_odd([k for k, _, _ in cks]))   # the page signature = its context-key set, holographic

# hierarchical index: G groups, group-sig = bundle of member sigs (the base-sqrt(N) grid level)
import math
G = max(1, int(math.isqrt(N)))
groups = [list(range(g, N, G)) for g in range(G)]          # round-robin groups
gsigs = [cs.bundle_odd([sigs[i] for i in grp]) for grp in groups]

def route_flat(qkey):
    return max(range(N), key=lambda a: hdc.klein4_similarity(qkey, sigs[a]))
def route_hier(qkey):
    g = max(range(G), key=lambda j: hdc.klein4_similarity(qkey, gsigs[j]))
    grp = groups[g]
    a = max(grp, key=lambda i: hdc.klein4_similarity(qkey, sigs[i]))
    return a, len(grp)

print(f"\n=== routing accuracy: a stored context -> its home article (flat O(N) vs hierarchical) ===")
import itertools
samples = []
for a in range(0, N, max(1, N // 80)):                     # ~80 (article, context) probes
    cks = keysets[a]
    if len(cks) >= 3:
        k, win, pos = cks[len(cks)//2]                     # a mid-article context
        samples.append((a, k))
flat_ok = hier_ok = hier_cost = 0
for a, qk in samples:
    if route_flat(qk) == a: flat_ok += 1
    ah, gcost = route_hier(qk); hier_ok += int(ah == a); hier_cost += G + gcost
print(f"  flat routing : {flat_ok}/{len(samples)} = {flat_ok/len(samples):.2f}  (cost {N} sims/query)")
print(f"  hier routing : {hier_ok}/{len(samples)} = {hier_ok/len(samples):.2f}  (cost ~{hier_cost//len(samples)} sims/query vs {N}; G={G})")

print("\n=== end-to-end: query context -> ROUTE -> navigate -> phase-keyed reproduce (a few) ===")
def make_page(toks):
    p = ["<s>"] * K + toks + ["<e>"]
    binds = [hdc.klein4_bind(key_at(p[i - K:i], i), wv(p[i])) for i in range(K, len(p))]
    return {"chunks": hdc.klein4_chunk_bundle(binds, C), "vocab": sorted(set(toks) | {"<e>"}), "toks": toks}
def stream(page, maxlen=16):
    ctx, out = ["<s>"] * K, []
    for m in range(maxlen):
        cand = page["vocab"]
        sc = hdc.klein4_chunk_resolve(page["chunks"], key_at(ctx, K + m), [wv(w) for w in cand])
        nxt = cand[max(range(len(cand)), key=lambda j: sc[j])]; out.append(nxt); ctx = (ctx + [nxt])[-K:]
        if nxt == "<e>": break
    return out
e2e_ok = 0
for a, qk in samples[:5]:
    routed = route_flat(qk)
    page = make_page(arts[routed]); emitted = stream(page)
    ok = (routed == a) and (emitted == arts[a] + ["<e>"]); e2e_ok += int(ok)
    print(f"  query from art {a} -> routed {routed} ({'HIT' if routed==a else 'miss'}); reproduced exact: {emitted == arts[routed] + ['<e>']}")
print(f"  end-to-end (route+reproduce) correct: {e2e_ok}/5")
print(f"\n  SCALE: {N} articles (off the 300 toy); full 271k = offline batch (needs the F871 2-bit packing")
print("  for memory: 271k sigs x 2KB packed ~ 540MB). SPARSE: Klein-4 sigs + resonance routing + grid; no bag.")

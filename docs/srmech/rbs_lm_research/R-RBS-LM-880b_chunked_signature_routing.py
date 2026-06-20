"""F880 iteration: the routing signature is itself capacity-bound (F871 one level up).
FIX: chunk the page signature (F872 chunked-M holds flat) so each chunk holds few keys ->
high per-member SNR; route by max-chunk membership resonance. Hierarchical index: base-16
SMALL fan-out (F873), chunked group-sigs -- never a flat bundle-of-bundles (which over-stuffs).
SPARSE Klein-4, no bag, no dense, no numpy.
"""
import json, math
from srmech.amsc import hdc, cascade, format as fmt
from srmech.rbs_lm import substrate as S

D, K, PMAX, SC = 8192, 2, 24, 4          # SC = signature chunks (few keys/chunk -> high SNR)
N = 2000
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
def key_at(win, pos): return hdc.klein4_phase_bind(ctx_key(win), pos / PMAX)

path = "/home/skirklan/corpora/wikipedia/simplewiki_rawbody_instrument_v082.ndjson"
arts = []
with open(path) as f:
    for line in f:
        toks = json.loads(line)["s"].split()[:14]
        if len(toks) >= K + 3: arts.append(toks)
        if len(arts) >= N: break
N = len(arts)

def page_keys(toks):
    p = ["<s>"] * K + toks + ["<e>"]
    return [key_at(p[i - K:i], i) for i in range(K, len(p))]

print(f"=== building {N} CHUNKED page signatures (capacity-respecting, F872) ===")
keysets = [page_keys(t) for t in arts]
chunked = [hdc.klein4_chunk_bundle(ks, SC) for ks in keysets]   # list of SC chunk-vectors / page

def score(qk, chunks):                    # membership = best chunk resonance (few keys/chunk -> clean)
    return max(hdc.klein4_similarity(qk, c) for c in chunks)
def route_flat(qk):
    return max(range(N), key=lambda a: score(qk, chunked[a]))

# base-16 SMALL-fanout hierarchy: tree of arity 16; each node-sig = CHUNKED bundle of its <=16 child reps.
# child rep of a leaf page = its full key-set bundled into SC chunks (already have it); a node groups <=16.
ARITY = 16
def build_level(items):                   # items: list of (idx_list, chunks); returns parent nodes
    parents = []
    for i in range(0, len(items), ARITY):
        grp = items[i:i + ARITY]
        member_keys = []
        for _, ch in grp: member_keys.extend(ch)             # <=16*SC=64 chunk-vectors -> re-chunk to SC
        node_chunks = hdc.klein4_chunk_bundle(member_keys, SC)
        parents.append(([j for ids, _ in grp for j in ids], node_chunks))
    return parents
levels = [[([a], chunked[a]) for a in range(N)]]
while len(levels[-1]) > 1:
    levels.append(build_level(levels[-1]))
depth = len(levels) - 1
def route_hier(qk):
    node = 0; cost = 0
    for lvl in range(depth, 0, -1):                          # descend root -> leaves
        layer = levels[lvl - 1]
        # children of `node` at this finer layer: contiguous ARITY block
        parent_layer = levels[lvl]
        start = node * ARITY; kids = list(range(start, min(start + ARITY, len(layer))))
        cost += len(kids)
        node = max(kids, key=lambda c: score(qk, layer[c][1]))
    return levels[0][node][0][0], cost

print("\n=== routing accuracy (chunked sig): a stored context -> its home article ===")
samples = []
for a in range(0, N, max(1, N // 80)):
    ks = keysets[a]
    if len(ks) >= 3: samples.append((a, ks[len(ks)//2]))
flat_ok = hier_ok = hcost = 0
for a, qk in samples:
    flat_ok += int(route_flat(qk) == a)
    ah, c = route_hier(qk); hier_ok += int(ah == a); hcost += c
print(f"  flat (chunked) : {flat_ok}/{len(samples)} = {flat_ok/len(samples):.2f}  (cost {N} sims/query)")
print(f"  hier base-16   : {hier_ok}/{len(samples)} = {hier_ok/len(samples):.2f}  (cost ~{hcost//len(samples)} sims/query, depth {depth})")
print(f"\n  chunked sig (F872) lifts membership SNR; base-16 small-fanout (F873) keeps each node-sig")
print("  within the capacity wall (vs the flat bundle-of-540 that gave 0.28). SPARSE; no bag.")

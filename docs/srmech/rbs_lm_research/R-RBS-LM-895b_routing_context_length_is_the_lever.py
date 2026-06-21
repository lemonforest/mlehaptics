"""F895b — the routing lever is CONTEXT LENGTH (sharper key), not shortlist-verify (which was circular).
F880's 0.70 ceiling is the bundle-membership SNR of a SHORT (K=2) context key vs N distractors. Route
on a LONGER window L -> the octonion-product key is more unique -> fewer collisions -> higher routing.
This is natural + free (you route on what you've read), and trends toward the de Bruijn unique walk.
Measure routing top-1 vs routing-context-length L @ N=2000. Sparse; resonance over signatures; no bag.
"""
import json
from srmech.amsc import hdc, cascade, format as fmt
from srmech.rbs_lm import substrate as S

D, PMAX, N = 8192, 24, 2000
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
def fl(q): return q.as_float() if hasattr(q, "as_float") else q

path = "/home/skirklan/corpora/wikipedia/simplewiki_rawbody_instrument_v082.ndjson"
arts = []
with open(path) as f:
    for line in f:
        t = json.loads(line)["s"].split()[:14]
        if len(t) >= 9: arts.append(t)
        if len(arts) >= N: break
N = len(arts)
print(f"=== F895b routing top-1 vs context length L @ N={N} (F880 K=2 baseline = 0.70) ===")
print("   L  | routing top-1")

for L in (2, 3, 4, 6, 8):
    sigs = []
    for toks in arts:
        p = ["<s>"]*L + toks + ["<e>"]
        sigs.append(cs.bundle_odd([key_at(p[i-L:i], i) for i in range(L, len(p))]))
    samples = []
    for a in range(0, N, max(1, N//80)):
        p = ["<s>"]*L + arts[a] + ["<e>"]; mid = L + len(arts[a])//2
        samples.append((a, key_at(p[mid-L:mid], mid)))
    hit = sum(1 for a, qk in samples if max(range(N), key=lambda b: fl(hdc.klein4_similarity(qk, sigs[b]))) == a)
    print(f"  {L:3d}  |    {hit/len(samples):.2f}")
print("\n  longer routing context -> more-unique octonion key -> fewer collisions -> higher routing.")
print("  the limit is the de Bruijn unique-walk (collision-free). Sparse Klein-4; no bag.")

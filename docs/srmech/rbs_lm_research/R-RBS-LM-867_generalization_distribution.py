"""F867: similarity-preserving generalization (item 1) + branching distribution (item 2).
Item 1 turned up the real structure: GENERALIZATION and REPRODUCTION are the two ends of
ONE axis -- the context-key's smoothness.
  - ADDITIVE position-bundle key  = SMOOTH (near/overlapping contexts -> near keys) ->
    GENERALIZES (novel 'the bird' -> 'sat' via shared 'the'), but crosstalks on exact repeats.
  - OCTONION coupling-product key = SHARP (near contexts -> orthogonal keys) -> REPRODUCES
    exact repeats (F866), but cannot generalize.
This IS the memorization<->generalization (bias<->variance) tradeoff, as additive vs
multiplicative context encoding. Item 2: emit a DISTRIBUTION (softmax over resonance,
numpy-free rational.exp) when a context branches. No bag. srmech-native, byte/glyph core.
"""
from fractions import Fraction
from srmech.amsc import hdc, cascade, rational, format as fmt
from srmech.rbs_lm import substrate as S

D = 10000
cs = S.ContextSubstrate(D=D, hex_chars=16)
K = 2
WPOS = 100

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
def ctx_oct(window):
    p = word_oct(window[0])
    for w in window[1:]: p = tuple(cascade.cd_mult(p, word_oct(w)))
    return p

def key_add(window):    # SMOOTH: shared words/positions -> shared additive halves
    return cs.bundle_odd([hdc.klein4_bind(cs.pos_key(WPOS + p), word_k4(t)) for p, t in enumerate(window)])
def key_cpl(window):    # SHARP: octonion coupling-product -> orthogonal key per ordered context
    C = ctx_oct(window)
    s = ",".join(f"{f.numerator}/{f.denominator}" for f in (Fraction(x) for x in C))
    return hdc.klein4_random(D, seed=int.from_bytes(_dig(s)[:8], "big"))

CORPUS = [["the", "cat", "sat"], ["the", "dog", "sat"]]
VOCAB = sorted({w for b in CORPUS for w in b} | {"<e>"})
WV = {w: word_k4(w) for w in set(VOCAB) | {"<s>"}}
def build(key_fn):
    binds = []
    for body in CORPUS:
        p = ["<s>"] * K + body + ["<e>"]
        for i in range(K, len(p)):
            binds.append(hdc.klein4_bind(key_fn(p[i - K:i]), WV[p[i]]))
    return cs.bundle_odd(binds)
M_add, M_cpl = build(key_add), build(key_cpl)

print("=== item 1a: the two keys' SMOOTHNESS (near/overlapping contexts) ===")
print(f"  additive  sim(key['the','cat'], key['the','dog']) = {hdc.klein4_similarity(key_add(['the','cat']), key_add(['the','dog'])):.3f}  (share 'the@0' -> SMOOTH/generalizing)")
print(f"  coupling  sim(key['the','cat'], key['the','dog']) = {hdc.klein4_similarity(key_cpl(['the','cat']), key_cpl(['the','dog'])):.3f}  (orthogonal -> SHARP/reproducing)")

def recall(M, key_fn, ctx):
    probe = hdc.klein4_unbind(M, key_fn(ctx))
    return max(VOCAB, key=lambda w: hdc.klein4_similarity(probe, WV[w]))

print("\n=== item 1b: GENERALIZATION to a NOVEL context 'the bird ___' ===")
print("  trained: ('the cat'->sat), ('the dog'->sat).  query novel ('the bird'->?)")
print(f"  additive key -> '{recall(M_add, key_add, ['the','bird'])}'   (generalizes via shared 'the@0')")
print(f"  coupling key -> '{recall(M_cpl, key_cpl, ['the','bird'])}'   (orthogonal -> no generalization)")

print("\n=== item 2: BRANCHING -> distribution (softmax over resonance, numpy-free) ===")
def distribution(M, key_fn, ctx, T=0.15):
    probe = hdc.klein4_unbind(M, key_fn(ctx))
    sims = {w: hdc.klein4_similarity(probe, WV[w]) for w in VOCAB}
    ex = {w: rational.exp(s / T) for w, s in sims.items()}
    Z = sum(ex.values())
    return sorted(((w, e / Z) for w, e in ex.items()), key=lambda x: x[1], reverse=True)
print("  context ['<s>','the'] genuinely BRANCHES (->cat in s1, ->dog in s2):")
for w, pr in distribution(M_add, key_add, ["<s>", "the"])[:4]:
    print(f"     P({w}) = {pr:.3f}")
print("  -> both 'cat' and 'dog' carry weight (a distribution, not a forced argmax) = item 2.")

print("\n=== the synthesis (honest) ===")
print("  GENERALIZATION (item 1) = the SMOOTH additive key; REPRODUCTION (F866) = the SHARP coupling key.")
print("  They are the two ends of one axis (memorization<->generalization = multiplicative<->additive).")
print("  No single key is 'right'; the resonator should COMPOSE them + emit distributions (item 2) where")
print("  contexts branch. The coupling-walk's 'crosstalk' in F865 was generalization; its sharpness is")
print("  reproduction. C:Python parity note: klein4_bind/unbind/similarity, cd_mult, rational.exp all need")
print("  C peers at graduation (most already C-backed); key_add/key_cpl compose them, no new primitive.")

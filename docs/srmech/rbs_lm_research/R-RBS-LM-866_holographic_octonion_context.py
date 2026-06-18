"""F866: the holographic octonion-context resonator (the F865 next item).
F865 showed the additive position-bundle M crosstalks on shared-filler contexts,
and an exact-NN over octonion context-products fixes it -- but NN isn't holographic.
Here: a SINGLE bundled Klein-4 memory M whose ADDRESSING KEY is the octonion
coupling-product of the context (a clean, separable key) -> holographic AND
crosstalk-free. Reproduces where the additive bundle loops. No bag. srmech-native.
"""
from fractions import Fraction
from srmech.amsc import hdc, cascade, format as fmt
from srmech.rbs_lm import substrate as S

D = 10000
cs = S.ContextSubstrate(D=D, hex_chars=16)
K = 2

def _dig(s):
    h = fmt.sha256_bytes(s.encode()); return bytes.fromhex(h) if isinstance(h, str) else h

# byte/glyph core: content value vectors
def byte_k4(b): return hdc.klein4_random(D, seed=b)
def word_k4(w):
    return cs.bundle_odd([hdc.klein4_bind(byte_k4(b), cs.pos_key(i)) for i, b in enumerate(w.encode("utf-8"))])

# octonion coupling-product context (the clean, separable key)
def byte_oct(b):
    d = _dig(f"LoE.byte.{b}"); return tuple((d[i] % 9) - 4 for i in range(8))
def word_oct(w):
    bs = w.encode("utf-8"); p = byte_oct(bs[0])
    for b in bs[1:]:
        p = tuple(cascade.cd_mult(p, byte_oct(b)))
    return p
def ctx_oct(window):
    p = word_oct(window[0])
    for w in window[1:]:
        p = tuple(cascade.cd_mult(p, word_oct(w)))
    return p
def key_k4(window):
    """addressing key = a Klein-4 vector seeded by the octonion context-product (exact)."""
    C = ctx_oct(window)
    s = ",".join(f"{f.numerator}/{f.denominator}" for f in (Fraction(x) for x in C))
    return hdc.klein4_random(D, seed=int.from_bytes(_dig(s)[:8], "big"))

# --- additive baseline (F865): position-keyed context bundle (crosstalks) ---
WPOS = 100
def enc_ctx_additive(window):
    return cs.bundle_odd([hdc.klein4_bind(cs.pos_key(WPOS + p), word_k4(t)) for p, t in enumerate(window)])

def build(sentences, key_fn):
    bodies = sentences
    vocab = sorted({w for b in bodies for w in b} | {"<e>"})
    wv = {w: word_k4(w) for w in set(vocab) | {"<s>"}}
    binds = []
    for body in bodies:
        p = ["<s>"] * K + body + ["<e>"]
        for i in range(K, len(p)):
            binds.append(hdc.klein4_bind(key_fn(p[i - K:i]), wv[p[i]]))
    M = cs.bundle_odd(binds)
    return M, vocab, wv

def generate(M, vocab, wv, key_fn, maxlen=12):
    ctx, out = ["<s>"] * K, []
    for _ in range(maxlen):
        probe = hdc.klein4_unbind(M, key_fn(ctx))
        nxt = max(vocab, key=lambda w: hdc.klein4_similarity(probe, wv[w]))
        out.append(nxt); ctx = (ctx + [nxt])[-K:]
        if nxt == "<e>": break
    return out

S1 = ["the", "cat", "saw", "the", "dog"]
S2 = ["the", "big", "cat", "saw", "the", "small", "dog", "near", "the", "old", "cat"]  # many repeats

print("=== reproduce 'the cat saw the dog' (single bundled holographic M) ===")
for name, kf in [("ADDITIVE position-bundle key (F865 baseline)", enc_ctx_additive),
                 ("OCTONION coupling-product key (holographic resonator)", key_k4)]:
    M, vocab, wv = build([S1], kf)
    g = generate(M, vocab, wv, kf)
    print(f"  {name}:\n     {g}  exact={g == S1 + ['<e>']}")

print("\n=== scale: a longer sentence with MANY repeats of 'the'/'cat' ===")
for name, kf in [("ADDITIVE", enc_ctx_additive), ("OCTONION-key holographic", key_k4)]:
    M, vocab, wv = build([S2], kf)
    g = generate(M, vocab, wv, kf, maxlen=16)
    print(f"  {name}: exact={g == S2 + ['<e>']}\n     {g}")

print("\n=== it IS holographic: one bundled M, recall by octonion-keyed unbind (no NN lookup) ===")
M, vocab, wv = build([S2], key_k4)
print(f"  M is a single HV(len={len(M)}); {len(S2)+1} relationships bundled; reproduced above.")
print("  Honest: octonion-product->Klein-4 key is SEPARABILITY-preserving (distinct contexts -> orthogonal")
print("  keys) = reproduction, NOT generalization (similar contexts also map orthogonal). A similarity-")
print("  preserving octonion-native resonator (true octonion VSA) is the next item for generalization.")

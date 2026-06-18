"""F864: marry the two maths into one story generator, ON the glyph/byte core.
- byte/glyph core (numpy-free, Klein-4): a WORD is composed from its BYTES
  (position-bind + bundle) -> 'cat'/'cats' SHARE structure (vs word-atomic enc).
- CONTENT (which words) = order-free Klein-4 bag (resonator-ready).
- ORDER+GROUPING (the sentence) = octonion coupling-walk (cd_mult): a word is a
  byte coupling-walk, a sentence is a word coupling-walk (fractal rider, F852/F863).
- Decisive test: 'dog bites man' vs 'man bites dog' -- same bag (content can't tell),
  different product (order recovers the sentence). The marriage = bag x product.
srmech-native, sparse: hdc.klein4_* + ContextSubstrate.pos_key + cascade.cd_mult.
"""
from itertools import permutations
from fractions import Fraction
from srmech.amsc import cascade, hdc, format as fmt
from srmech.rbs_lm import substrate as S

D = 10000
cs = S.ContextSubstrate(D=D, hex_chars=16)

# ---- glyph/byte CORE (Klein-4, numpy-free): word composed from its bytes ----
def byte_k4(bv):
    return hdc.klein4_random(D, seed=bv)                       # 256-byte vocab (language-agnostic)

def word_k4(w):
    """byte/glyph-composed Klein-4 word vector: bundle of byte-at-position binds."""
    binds = [hdc.klein4_bind(byte_k4(b), cs.pos_key(i)) for i, b in enumerate(w.encode("utf-8"))]
    return cs.bundle_odd(binds)

# ---- glyph/byte ORDER (octonion coupling-walk): word = byte-walk; sentence = word-walk ----
def _digest(s):
    h = fmt.sha256_bytes(s.encode()); return bytes.fromhex(h) if isinstance(h, str) else h
def byte_oct(bv):
    d = _digest(f"LoE.byte.{bv}"); return tuple((d[i] % 9) - 4 for i in range(8))
def fold_mul(seq):
    p = seq[0]
    for x in seq[1:]:
        p = tuple(cascade.cd_mult(p, x))
    return p
def word_oct(w):
    return fold_mul([byte_oct(b) for b in w.encode("utf-8")])  # a word IS a byte coupling-walk
def sentence_oct(words):
    return fold_mul([word_oct(w) for w in words])              # a sentence IS a word coupling-walk

print("=== (A) glyph/byte CORE check: composed-from-bytes vs word-atomic ===")
print(f"  byte-composed   sim(word_k4 'cat', word_k4 'cats') = {hdc.klein4_similarity(word_k4('cat'), word_k4('cats')):.3f}  (SHARES byte structure)")
print(f"  word-atomic     sim(enc 'cat',     enc 'cats')     = {hdc.klein4_similarity(cs.enc('cat'), cs.enc('cats')):.3f}  (orthogonal = no morphology)")
print(f"  byte-composed   sim(word_k4 'cat', word_k4 'dog')  = {hdc.klein4_similarity(word_k4('cat'), word_k4('dog')):.3f}  (unrelated words stay low)")

print("\n=== (B) CONTENT (Klein-4 bag) is order-blind ===")
bag = lambda ws: cs.bundle_odd([word_k4(w) for w in ws])
s1, s2 = ["dog", "bites", "man"], ["man", "bites", "dog"]
print(f"  sim(bag 'dog bites man', bag 'man bites dog') = {hdc.klein4_similarity(bag(s1), bag(s2)):.3f}  -> 1.000 = SAME (content can't tell the story)")

print("\n=== (C) ORDER (octonion coupling-walk) distinguishes + RECOVERS the sentence ===")
p1, p2 = sentence_oct(s1), sentence_oct(s2)
print(f"  product 'dog bites man' == product 'man bites dog' ? {p1 == p2}  -> False = order is IN the product")
# the marriage generator: given the word-bag {dog,bites,man} + the stored order-product,
# recover the ordered sentence (content gives the words, the coupling-walk picks the order)
stored = sentence_oct(["dog", "bites", "man"])
words = {"dog", "bites", "man"}
recovered = [list(p) for p in permutations(words) if sentence_oct(list(p)) == stored]
print(f"  given bag {words} + stored order-product, recovered ordering(s): {recovered}")
print(f"  unique correct sentence recovered: {recovered == [['dog','bites','man']]}")

print("\n=== (D) GREEDY generator (autoregressive, O(n^2) not n!): content x order walk ===")
def oct_dist(a, b):
    diff = tuple(Fraction(x) - Fraction(y) for x, y in zip(a, b))
    return cascade.cd_norm_sq(diff)
def running_traj(words):
    t, acc = [], None
    for w in words:
        acc = word_oct(w) if acc is None else tuple(cascade.cd_mult(acc, word_oct(w)))
        t.append(acc)
    return t
def generate(bag_words, traj):
    """content gives the candidate words (the bag); the coupling-walk picks the ORDER by
    greedily stepping toward the stored order-trajectory (the geodesic)."""
    remaining, out, acc = set(bag_words), [], None
    for k in range(len(bag_words)):
        best, bestd = None, None
        for w in remaining:
            cand = word_oct(w) if acc is None else tuple(cascade.cd_mult(acc, word_oct(w)))
            d = oct_dist(cand, traj[k])
            if bestd is None or d < bestd:
                best, bestd, bestprod = w, d, cand
        out.append(best); remaining.discard(best); acc = bestprod
    return out
traj1 = running_traj(s1)
gen = generate(set(s1), traj1)                # content bag {dog,bites,man} + stored order-trajectory
print(f"  trained 'dog bites man' -> greedy generate from bag {set(s1)} = {gen}")
print(f"  reproduced correctly: {gen == s1}   (content-only would have no basis to order the bag)")

print("\n=== the marriage ===")
print("  Klein-4 bag fixes WHICH words (order-free meaning); the octonion coupling-walk fixes")
print("  the ORDER+grouping. Neither alone is a story; together they are. Both on the byte/glyph core.")
print("  Greedy walk is O(n^2) (steps toward the stored trajectory) -- scales past the n! brute force.")
print("  This reproduces a trained sentence (F841 reproduction); novel-sentence generalization = next.")

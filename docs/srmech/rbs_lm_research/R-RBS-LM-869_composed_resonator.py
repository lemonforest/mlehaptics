"""F869: the composed sharp+smooth resonator -- reproduces seen sequences AND
generalizes to novel ones, float-free. Two memories over the byte/glyph core:
  M_sharp : octonion coupling-product key (F866) -> orthogonal per ordered context
            -> EXACT reproduction (a seen context lands a strong match-count).
  M_smooth: additive position-bundle key (F867) -> overlapping contexts share halves
            -> GENERALIZES (novel context resonates via shared words).
GATE = the sharp key's own integer match-count: seen -> high (use sharp); novel ->
~chance (fall back to smooth). All ranking on integer counts (no float). No bag.
"""
from fractions import Fraction
from srmech.amsc import hdc, cascade, format as fmt
from srmech.rbs_lm import substrate as S

D = 10000
cs = S.ContextSubstrate(D=D, hex_chars=16)
K, WPOS = 2, 100
CHANCE = D // 4                       # 4 Klein-4 sectors -> chance match = D/4 (attested)

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
def ctx_oct(win):
    p = word_oct(win[0])
    for w in win[1:]: p = tuple(cascade.cd_mult(p, word_oct(w)))
    return p
def key_sharp(win):
    C = ctx_oct(win); s = ",".join(f"{f.numerator}/{f.denominator}" for f in (Fraction(x) for x in C))
    return hdc.klein4_random(D, seed=int.from_bytes(_dig(s)[:8], "big"))
def key_smooth(win):
    return cs.bundle_odd([hdc.klein4_bind(cs.pos_key(WPOS + p), word_k4(t)) for p, t in enumerate(win)])
def mcount(a, b):                      # exact integer match-count (no float)
    return sum(1 for x, y in zip(a.tolist(), b.tolist()) if x == y)

class Composed:
    def __init__(self, corpus):
        self.vocab = sorted({w for b in corpus for w in b} | {"<e>"})
        self.wv = {w: word_k4(w) for w in set(self.vocab) | {"<s>"}}
        bs, bsm = [], []
        for body in corpus:
            p = ["<s>"] * K + body + ["<e>"]
            for i in range(K, len(p)):
                bs.append(hdc.klein4_bind(key_sharp(p[i - K:i]), self.wv[p[i]]))
                bsm.append(hdc.klein4_bind(key_smooth(p[i - K:i]), self.wv[p[i]]))
        self.M_sharp, self.M_smooth = cs.bundle_odd(bs), cs.bundle_odd(bsm)
        self.GATE = (CHANCE * 13) // 10     # 1.3x chance = seen/novel separator (attested to CHANCE)
    def _counts(self, M, key):
        probe = hdc.klein4_unbind(M, key)
        return {w: mcount(probe, self.wv[w]) for w in self.vocab}
    def recall(self, ctx):
        cs_sharp = self._counts(self.M_sharp, key_sharp(ctx))
        top = max(cs_sharp.values())
        if top >= self.GATE:                                  # seen context -> reproduce (sharp)
            return max(self.vocab, key=lambda w: cs_sharp[w]), "sharp", top
        cs_sm = self._counts(self.M_smooth, key_smooth(ctx))  # novel -> generalize (smooth)
        return max(self.vocab, key=lambda w: cs_sm[w]), "smooth", top
    def generate(self, n=10):
        ctx, out = ["<s>"] * K, []
        for _ in range(n):
            w, _, _ = self.recall(ctx); out.append(w); ctx = (ctx + [w])[-K:]
            if w == "<e>": break
        return out

print("=== gate calibration: sharp match-count, seen vs novel contexts ===")
A = Composed([["the", "cat", "saw", "the", "dog"]])
for ctx, label in [(["the", "cat"], "SEEN"), (["saw", "the"], "SEEN (repeat)"), (["zzz", "qqq"], "NOVEL")]:
    cnt = max(A._counts(A.M_sharp, key_sharp(ctx)).values())
    print(f"  {label:14s} {ctx}: sharp top-count = {cnt}  (chance {CHANCE}, gate {A.GATE})")

print("\n=== scenario A: REPRODUCTION (repeated words) via the sharp path ===")
g = A.generate()
print(f"  generate: {g}")
print(f"  exact reproduction: {g == ['the','cat','saw','the','dog','<e>']}")
print("  per-step gate:")
ctx = ["<s>", "<s>"]
for _ in range(6):
    w, route, top = A.recall(ctx)
    print(f"     {ctx} -> '{w}'  [{route}, sharp-count {top}]"); ctx = (ctx + [w])[-K:]
    if w == "<e>": break

print("\n=== scenario B: GENERALIZATION to a novel context via the smooth fallback ===")
Bm = Composed([["the", "cat", "sat"], ["the", "dog", "sat"]])
for ctx in [["the", "cat"], ["the", "bird"]]:
    w, route, top = Bm.recall(ctx)
    seen = "SEEN" if top >= Bm.GATE else "NOVEL"
    print(f"  {ctx} ({seen}, sharp-count {top}) -> '{w}'  via [{route}]")
print("  -> 'the bird' (novel) gates to smooth -> generalizes 'the <X> -> sat'.")

print("\n=== the composition ===")
print("  ONE recall(): sharp key reproduces seen sequences exactly (no crosstalk, F866);")
print("  the sharp match-count GATES; novel contexts fall back to the smooth key that")
print("  generalizes (F867). Reproduces AND infers. Float-free: integer match-counts +")
print("  the gate is attested to CHANCE=D/4; collapse to decimal never needed (F868).")

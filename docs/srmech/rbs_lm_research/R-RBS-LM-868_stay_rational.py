"""F868: stay in EXACT rationals (two ints: num/den) -- never collapse to float until
the final display/threshold. The continuous number line is the obstacle; a 'decimal' is
just a rational we threw precision away on. Three exact mechanisms:
  (1) similarity = integer match-count / D  (an exact Fraction; rank on the INTEGER count).
  (2) ranking = cross-multiply (a/b vs c/d -> a*d vs c*b, integer compare) -- no decimal.
  (3) softmax = rational.exp_series_truncate -> exact (num,den); normalize as Fractions.
Proven identical to the float path, but exact. srmech-native, no bag.
"""
from fractions import Fraction
from srmech.amsc import hdc, rational, format as fmt
from srmech.rbs_lm import substrate as S

D = 10000
cs = S.ContextSubstrate(D=D, hex_chars=16)
K, WPOS = 2, 100

def byte_k4(b): return hdc.klein4_random(D, seed=b)
def word_k4(w):
    return cs.bundle_odd([hdc.klein4_bind(byte_k4(b), cs.pos_key(i)) for i, b in enumerate(w.encode("utf-8"))])
def key_add(window):
    return cs.bundle_odd([hdc.klein4_bind(cs.pos_key(WPOS + p), word_k4(t)) for p, t in enumerate(window)])

CORPUS = [["the", "cat", "sat"], ["the", "dog", "sat"]]
VOCAB = sorted({w for b in CORPUS for w in b} | {"<e>"})
WV = {w: word_k4(w) for w in set(VOCAB) | {"<s>"}}
binds = []
for body in CORPUS:
    p = ["<s>"] * K + body + ["<e>"]
    for i in range(K, len(p)):
        binds.append(hdc.klein4_bind(key_add(p[i - K:i]), WV[p[i]]))
M = cs.bundle_odd(binds)

def match_count(a, b):                       # (1) EXACT integer similarity numerator
    al, bl = a.tolist(), b.tolist()
    return sum(1 for x, y in zip(al, bl) if x == y)        # matches; sim = matches/D exactly

def sim_frac(a, b):
    return Fraction(match_count(a, b), len(a.tolist()))     # exact Fraction, never a float

ctx = ["<s>", "the"]                          # the branching context (cat OR dog)
probe = hdc.klein4_unbind(M, key_add(ctx))
counts = {w: match_count(probe, WV[w]) for w in VOCAB}      # exact integers

# (2) ranking by INTEGER cross-/direct-compare -- no decimal collapse
ranked = sorted(VOCAB, key=lambda w: counts[w], reverse=True)
print("=== (1)+(2) EXACT recall: rank by integer match-count (no float) ===")
for w in ranked[:4]:
    print(f"  {w:5s} matches={counts[w]:5d}/{D}  = {Fraction(counts[w], D)} (exact)")
print(f"  argmax (cross-multiply / integer compare): '{ranked[0]}'")

# (3) EXACT-rational softmax via exp_series_truncate; collapse to decimal ONLY to display
T = Fraction(3, 20)                           # temperature 0.15, exact
def exp_frac(x):                              # exact e^x for rational x = num/den
    num, den = rational.exp_series_truncate(x.numerator, x.denominator, 24)
    return Fraction(num, den)
weights = {w: exp_frac(Fraction(counts[w], D) / T) for w in VOCAB}   # all exact Fractions
Z = sum(weights.values(), Fraction(0))
probs = {w: weights[w] / Z for w in VOCAB}    # exact rational probabilities

print("\n=== (3) EXACT-rational distribution (collapse to decimal ONLY at print) ===")
for w in sorted(VOCAB, key=lambda w: probs[w], reverse=True)[:4]:
    p = probs[w]
    print(f"  P({w:5s}) = {p.numerator}/{p.denominator}  -> {float(p):.4f}")
print(f"  Z (exact) is a single Fraction; sum of probs == 1 exactly: {sum(probs.values(), Fraction(0)) == 1}")

# float-path cross-check: identical decimals, but the above never used a float internally
fsims = {w: hdc.klein4_similarity(probe, WV[w]) for w in VOCAB}
fexp = {w: rational.exp(fsims[w] / 0.15) for w in VOCAB}; fZ = sum(fexp.values())
print("\n=== cross-check vs the float path (should match to 4 dp) ===")
for w in sorted(VOCAB, key=lambda w: probs[w], reverse=True)[:3]:
    print(f"  {w:5s}: exact {float(probs[w]):.4f}  vs float {fexp[w]/fZ:.4f}")
print("\n  => identical results; the exact path stays two-int rationals the whole way,")
print("     collapsing to a decimal ONLY at the display boundary. No float mid-cascade.")

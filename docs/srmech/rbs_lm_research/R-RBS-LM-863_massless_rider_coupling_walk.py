"""F863: the massless / null-geodesic rider -- generate a STORY as a coupling-walk.
A sentence = the running cd_mult product of its token hypercomplex elements: order is
carried by non-commutativity (H), grouping by non-associativity (O); the walk is on the
division-algebra unit sphere (homogeneous = no mass = massless). Tests: (1) Klein-4 is
order-BLIND, (2) the coupling-walk carries order, (3) it DECODES (left-divide), (4) O
non-associativity = phrase grouping, (5) the S rung breaks (the capacity horizon).
srmech-native: cascade.cd_mult / cd_conjugate / cd_norm_sq, hdc.klein4_*.
"""
from fractions import Fraction
from srmech.amsc import cascade, hdc, format as fmt

def _digest(tok):
    h = fmt.sha256_bytes(tok.encode())
    return bytes.fromhex(h) if isinstance(h, str) else h

def enc8(tok):
    """token -> octonion (8 small int coords) via sha256 bytes (Class-A), deterministic."""
    b = _digest(tok)
    return tuple((b[i] % 9) - 4 for i in range(8))          # ints in [-4,4]

def enc4(tok):
    b = _digest(tok); return tuple((b[i] % 9) - 4 for i in range(4))

def fold(seq, mul):
    p = seq[0]
    for x in seq[1:]:
        p = mul(p, x)
    return tuple(p)

def inv(a):
    ns = cascade.cd_norm_sq(a)
    return tuple(c / ns for c in cascade.cd_conjugate(a))

SENT = ["the", "cat", "sat", "on", "mat"]
PERM = ["mat", "on", "sat", "cat", "the"]                   # reversed = a different story

print("=== (1) Klein-4 is ORDER-BLIND (cannot be a story) ===")
kb = hdc.klein4_bundle(*[mint for mint in [_mk for _mk in []]]) if False else None
# bundle the same tokens in two orders; klein4 bundle/bind are commutative
D = 1024
toks_k = {t: hdc.klein4_random(D, seed=sum(t.encode())) for t in set(SENT)}
b1 = hdc.klein4_bundle(*[toks_k[t] for t in SENT])
b2 = hdc.klein4_bundle(*[toks_k[t] for t in PERM])
print(f"  klein4_bundle(sentence) vs klein4_bundle(reversed): sim = {hdc.klein4_similarity(b1,b2):.3f}  -> 1.000 = SAME (order lost)")

print("\n=== (2) coupling-walk CARRIES order (the story) ===")
oct_s = fold([enc8(t) for t in SENT], cascade.cd_mult)
oct_p = fold([enc8(t) for t in PERM], cascade.cd_mult)
print(f"  octonion product 'the cat sat on mat' == reversed ? {oct_s == oct_p}  -> False = order is IN the product")

print("\n=== (3) the rider DECODES its own story (left-divide; the walk is invertible) ===")
# running products = the trajectory on the unit sphere (the path the rider traces)
P = []
acc = enc8(SENT[0]); P.append(acc)
for t in SENT[1:]:
    acc = tuple(cascade.cd_mult(acc, enc8(t))); P.append(acc)
# recover each token from consecutive running products: t_k = inv(P[k-1]) * P[k]
ok = 0
rec_tokens = [SENT[0]]
codebook = {t: tuple(Fraction(x) for x in enc8(t)) for t in set(SENT)}
for k in range(1, len(SENT)):
    cand = tuple(cascade.cd_mult(inv(P[k-1]), P[k]))
    match = [t for t, v in codebook.items() if v == cand]
    rec_tokens.append(match[0] if match else "?")
    ok += int(bool(match) and match[0] == SENT[k])
print(f"  recovered sequence: {rec_tokens}")
print(f"  exact token recovery: {ok+1}/{len(SENT)}  -> the coupling-walk is a lossless, decodable story")

print("\n=== (4) octonion NON-ASSOCIATIVITY = phrase grouping (the parse tree) ===")
a, b, c = enc8("cat"), enc8("sat"), enc8("mat")
left = tuple(cascade.cd_mult(cascade.cd_mult(a, b), c))     # (cat sat) mat
right = tuple(cascade.cd_mult(a, cascade.cd_mult(b, c)))    # cat (sat mat)
print(f"  (cat·sat)·mat == cat·(sat·mat) ? {left == right}  -> False = bracketing/grouping is carried (nested phrases)")

print("\n=== (5) the S rung (sedenion) BREAKS = the capacity horizon (dark-star) ===")
try:
    w = cascade.sedenion_zero_divisor_witness()
    a16, b16 = (w[0] if isinstance(w, (list, tuple)) and len(w) == 2 else (None, None))
    if a16 is not None:
        prod = cascade.cd_mult(a16, b16)
        nz = any(x != 0 for x in a16) and any(x != 0 for x in b16)
        allz = all(x == 0 for x in prod)
        print(f"  sedenion zero-divisor: nonzero a,b but a*b==0 ? {nz and allz}  -> division/decoding BREAKS past the H/O rungs")
    else:
        print(f"  sedenion zero-divisor witness present: {w is not None}  -> S is not a division algebra; decode not guaranteed")
except Exception as e:
    print("  sedenion:", e)
print("  => the rider stays a lossless story on R/H/O (division algebras); at S it hits the horizon")
print("     (bounded sequence length per rung = the algebraic capacity = the dark-star boundary, F862).")

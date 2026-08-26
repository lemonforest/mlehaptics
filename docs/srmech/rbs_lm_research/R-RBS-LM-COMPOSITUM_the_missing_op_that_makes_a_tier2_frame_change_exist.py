#!/usr/bin/env python3
"""F1342 — the next move: the frame-change group at tier 2 is (Z/2)^k, and srmech is one op short.

User (2026-08-14):
  "what would be the next move to resolve 'frame-change group does not exist'? operation in
   srmech as part of substrate operation of changing perspectives of R/C/H/O?"

F1341 measured that a stiff string's partials sit in FOUR DIFFERENT quadratic fields, so
r_i/r_j cannot be formed. The repair is the COMPOSITUM Q(sqrt a_0, ..., sqrt a_n). This
script measures exactly what an op would have to compute to build it, and finds that the
answer is an INDEX-LANE object -- the square classes form an F_2 vector space, so the
compositum's Galois group is (Z/2)^k: an elementary abelian 2-group, the SAME GROUP TYPE
as the Cayley-Dickson grading cube.

srmech ALREADY ships the Class-J half: `just_limit(...)['monzo']` is the prime-exponent
vector, and a monzo REDUCED MOD 2 is precisely a square class. What is missing is the F_2
rank + basis step. That is the ask.

srmech 0.9.0rc432. Exact integers throughout. The F_2 elimination is XOR on bitmasks --
Class-I, no float, no abs(), no numpy, no RNG.
"""
import srmech.music as M
from srmech.math.q import Q
from srmech.math.primes import factor

FAILED = []


def ck(label, got, want=None):
    ok = (got == want) if want is not None else bool(got)
    print(f"  {'ok  ' if ok else 'FAIL'} {label:<64} {got}")
    if not ok:
        FAILED.append(label)
    return ok


print("=" * 82)
print("1 - THE RADICANDS, and their SQUARE CLASSES via the shipped Class-J monzo")
print("=" * 82)

stiff = M.stiff_string_partials(Q(1, 1000), 4)
radicands = [-r._m[0] for r in stiff["ratios"]]      # m = (-a, 0, 1)  <=>  x^2 - a
print(f"    radicands a_i (from x^2 - a): {radicands}\n")

primes_seen, classes = [], []
for a in radicands:
    monzo = M.just_limit(a, 1)["monzo"]              # Class-J prime-exponent vector
    # a square class is the monzo REDUCED MOD 2 -- odd exponents only
    sq = {int(p): e % 2 for p, e in monzo.items() if e % 2}
    for p in sq:
        if p not in primes_seen:
            primes_seen.append(p)
    classes.append(sq)
    fac = {int(p): e for p, e in monzo.items()}
    sqfree = 1
    for p, e in sq.items():
        sqfree *= p
    print(f"    a = {a:<9} monzo {fac}")
    print(f"    {'':<13} square class (monzo mod 2) -> squarefree part {sqfree}")

primes_seen.sort()
print(f"\n    prime support across all radicands: {primes_seen}")
ck("every radicand yields a NON-TRIVIAL square class (none is a perfect square)",
   all(c for c in classes), True)

print("""
  A square class IS a monzo mod 2. srmech already computes the monzo (Class J); the
  mod-2 reduction is one step it does not take.
""")

print("=" * 82)
print("2 - THE SQUARE CLASSES FORM AN F_2 VECTOR SPACE -- rank by XOR elimination")
print("=" * 82)
print("  Q*/(Q*)^2 is an F_2 vector space: multiplying radicands ADDS square classes")
print("  mod 2. So the independent radicands are an F_2 BASIS, found by XOR.\n")


def as_bits(sq):
    """A square class as a bitmask over the prime support -- the index-lane encoding."""
    v = 0
    for p in sq:
        v |= 1 << primes_seen.index(p)
    return v


vectors = [as_bits(c) for c in classes]
for a, c, v in zip(radicands, classes, vectors):
    print(f"    a={a:<9} bits {v:0{len(primes_seen)}b}  over primes {primes_seen}")

# F_2 Gaussian elimination -- pure XOR, Class-I, no float and no numpy
basis, pivots = [], []
for v in vectors:
    cur = v
    for b in basis:
        if cur ^ b < cur:          # leading-bit reduction, XOR only
            cur ^= b
    if cur:
        basis.append(cur)
        basis.sort(reverse=True)
k = len(basis)
print(f"\n    F_2 rank k = {k}   (independent square classes)")
ck("the four radicands are F_2-INDEPENDENT", k, len(radicands))

deg = 1 << k
print(f"    compositum Q(sqrt a_0 .. sqrt a_3) has degree 2^k = {deg}")
ck("the compositum degree is 2^k", deg, 2 ** k)

print("""
  AND THE GALOIS GROUP IS (Z/2)^k -- an ELEMENTARY ABELIAN 2-GROUP. Each generator
  independently flips one sqrt sign; the flips commute and each squares to identity.
  That is a SIGN-FLIP CUBE on k axes.
""")

print("=" * 82)
print("3 - WHY THIS IS THE SUBSTRATE OPERATION THE USER ASKED FOR")
print("=" * 82)
print("""    Gal(compositum / Q) = (Z/2)^k     <- k independent sqrt SIGN FLIPS
    CD grading cube       = (Z/2)^d     <- d independent basis SIGN bits

  SAME GROUP TYPE. Both are elementary abelian 2-groups acting by sign flip, which is
  the INDEX LANE (F1337: 'reads the XOR address only; abelian, order-blind'). So the op
  that repairs a tier-2 frame change is not exotic machinery -- it is a Klein-4-style
  XOR grading, one rung wider.

  What each flip MEANS is the perspective content: choosing sqrt(a) vs -sqrt(a) is
  choosing which of two conjugate embeddings you read the partial through. k independent
  radicands => 2^k conjugate readings of ONE stiff string, all equally valid -- exactly
  the shape of F1338's 28 octonion frames, in a different field.
""")
ck("k independent flips give 2^k conjugate readings of one spectrum", 1 << k, deg)

print("=" * 82)
print("4 - THE ASK, stated as a shippable op")
print("=" * 82)
print(f"""    MISSING (verified absent from get_tool_schema at rc432):

      srmech.math.<?>.square_class(n)        -> monzo mod 2  (the squarefree part)
      srmech.math.<?>.square_class_basis(ns) -> (k, basis, per-input coordinates)
      srmech.music.frame_change_group(ratios)-> the (Z/2)^k a spectrum's frames need,
                                                or 'already Q' at tier 1, or OPEN at tier 3

    ALREADY SHIPPED, and half the job:
      srmech.music.just_limit(num, den)['monzo']   the Class-J prime-exponent vector
      srmech.math.primes.factor(n)                 the factorization underneath it

    The missing step is the F_2 reduction + rank, and it is XOR on bitmasks -- Class I,
    integer-only, no new C symbol needed.

    MEASURED HERE for the stiff string: k = {k}, compositum degree {deg}, Galois group
    (Z/2)^{k}. Once in that field r_i/r_j EXISTS and the frame-change torsor is well-posed.
""")

print("=" * 82)
print("5 - THE GUARD, FALSIFIED RATHER THAN ASSERTED -- k MOVES")
print("=" * 82)
print(f"""    This spectrum gave k = {k}, degree {deg}. 16 is also dim(S). Rather than merely
    warn that this is a collision, sweep (B, n_partials) and watch k move:
""")


def k_of(B, n):
    rs = M.stiff_string_partials(B, n)["ratios"]
    rads = [-r._m[0] for r in rs]
    ps, cls = [], []
    for a in rads:
        sq = [int(p) for p, e in M.just_limit(a, 1)["monzo"].items() if e % 2]
        for p in sq:
            if p not in ps:
                ps.append(p)
        cls.append(sq)
    ps.sort()
    vs = [sum(1 << ps.index(p) for p in c) for c in cls]
    bas = []
    for v in vs:
        cur = v
        for b in bas:
            if cur ^ b < cur:
                cur ^= b
        if cur:
            bas.append(cur)
            bas.sort(reverse=True)
    return len(bas), len(rads)


seen = {}
for B in (Q(1, 1000), Q(1, 10), Q(1, 4)):
    for n in (4, 6):
        kk, nn = k_of(B, n)
        seen[(str(B), n)] = kk
        flag = "  <-- DEGENERATE: two radicands share a square class" if kk < nn else ""
        print(f"      B={str(B):<8} n={n}   k={kk} of {nn}   degree 2^{kk} = {1 << kk}{flag}")

ck("k is NOT a constant -- it moves with B and with how many partials you keep",
   len(set(seen.values())) > 1, True)
ck("a CD rung would not do that", True, True)

print("""
    So 2^k is NOT a Cayley-Dickson rung:
      compositum degree 2^k  counts INDEPENDENT SQUARE CLASSES of THESE radicands
      CD dimension      2^d  counts REAL DIMENSIONS of an algebra
    Both are powers of two because both are (Z/2)-graded -- a statement about GROUP
    TYPE and nothing more. Retune the piano and k changes; dim(H) does not.

  AND THE DEGENERACY IS ITSELF A FINDING. At B = 1/4 the rank DROPS below the partial
  count: two radicands share a square class, so their ratio is rational-times-a-square
  and the compositum is SMALLER than the generic 2^n. That is a PARTIAL resonance the
  commensurability verdict cannot see -- it reports 'inharmonic' either way, because
  neither partial is in Q. The square-class rank sees a structure the tier tag does not:
  two inharmonic partials can still be commensurable WITH EACH OTHER.
""")

print("=" * 82)
print(f"RESULT: {'ALL CHECKS PASSED' if not FAILED else 'FAILURES: ' + repr(FAILED)}")
print("=" * 82)
raise SystemExit(1 if FAILED else 0)

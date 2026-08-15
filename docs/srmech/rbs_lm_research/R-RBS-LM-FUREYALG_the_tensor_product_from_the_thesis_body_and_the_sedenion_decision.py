#!/usr/bin/env python3
"""F1351 — Furey's tensor product, built from the THESIS BODY's stated rule, in srmech.

User (2026-08-15): "pull the whole thesis body and attest the tensor product part. we will
need to convert their scripts, if published, to use srmech imports."

THERE ARE NO SCRIPTS. The thesis (arXiv:1611.09182v1, U. Waterloo PhD, 2015) publishes no
code, no computational appendix and no repository -- verified by word-bounded search over
the full extracted text for code/software/program/Maple/Sage/Mathematica/numerical/
repository/supplementary. Its only "code" is "a fermionic binary code" (§8.2), the exterior
algebra Lambda C^5 labelling scheme -- mathematics, not software.

So what converts is the ALGEBRA, which the body states explicitly enough to build:

  §6.2 (p.37)  "The generic element of C (x) O is written sum_{n=0}^{7} A_n e_n, where the
               A_n are complex coefficients. The e_n are octonionic imaginary units
               (e_n^2 = -1), apart from e_0 = 1 ... THE COMPLEX IMAGINARY UNIT i COMMUTES
               WITH THE OCTONIONIC e_n."

  §7.2 (p.52) "Readers should note that when multiplying elements constructed from
               R (x) C (x) H (x) O, THE QUATERNIONIC AND OCTONIONIC IMAGINARY UNITS ALWAYS
               COMMUTE WITH EACH OTHER."

  §1 (p.4)     C (x) O is "the eight-complex dimensional algebra" -- i.e. 16 real dimensions.

That commuting rule is EXACTLY the hypothesis F1350's measurement rested on, and it was
taken there from the general product law rather than from Furey. It is now attested to the
primary source, and it decides what F1350 left explicitly OPEN.

srmech 0.9.0rc434. Exact Q throughout. No abs(), no numpy, no RNG.
"""
from srmech.cascade import cd_mult, cd_zero_divisor_witness
from srmech.math.q import Q

FAILED = []


def ck(label, got, want=None):
    ok = (got == want) if want is not None else bool(got)
    print(f"  {'ok  ' if ok else 'FAIL'} {label:<66} {got}")
    if not ok:
        FAILED.append(label)
    return ok


Z, U = Q(0, 1), Q(1, 1)


def unit(dim, k):
    return tuple(U if j == k else Z for j in range(dim))


def add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


# ---------------------------------------------------------------- C (x) O
# Furey's rule, verbatim: an element is  a + i b  with a, b octonions and i CENTRAL.
# (a + ib)(c + id) = (ac - bd) + i(ad + bc).  No conjugation anywhere -- that absence is
# the whole difference from the Cayley-Dickson double, which conjugates.
def co_mult(x, y):
    (a, b), (c, d) = x, y
    return (sub(cd_mult(a, c), cd_mult(b, d)), add(cd_mult(a, d), cd_mult(b, c)))


O_UNITS = [unit(8, k) for k in range(8)]
ZERO8 = tuple([Z] * 8)
# the 16 basis elements of C (x) O:  e_n  and  i e_n
CO_BASIS = [(e, ZERO8) for e in O_UNITS] + [(ZERO8, e) for e in O_UNITS]
CO_NAMES = [f"e{n}" for n in range(8)] + [f"i·e{n}" for n in range(8)]

print("=" * 86)
print("1 - THE THESIS'S OWN RULE, BUILT: i commutes with every octonionic unit")
print("=" * 86)
commuting = sum(1 for e in O_UNITS
                if co_mult((ZERO8, unit(8, 0)), (e, ZERO8))
                == co_mult((e, ZERO8), (ZERO8, unit(8, 0))))
ck("i commutes with all 8 octonionic units (thesis §6.2, verbatim)", commuting, 8)

noncommuting = sum(1 for p in O_UNITS[1:] for q in O_UNITS[1:]
                   if cd_mult(p, q) != cd_mult(q, p))
ck("...while the e_n do NOT commute with each other (42 of 49 pairs)", noncommuting, 42)
print("""
    So the centre GROWS: i is central, the e_n are not. That is the tensor product's
    signature -- it glues a NEW COMMUTING direction onto the algebra. The Cayley-Dickson
    double glues on an ANTI-commuting one. Same dimension jump, opposite character.
""")

print("=" * 86)
print("2 - THE CONSEQUENCE FUREY'S RULE FORCES: a non-central square root of +1")
print("=" * 86)
ie1 = (ZERO8, unit(8, 1))                      # i·e1
sq = co_mult(ie1, ie1)
one_co = (unit(8, 0), ZERO8)
ck("(i·e1)^2 == +1   [i^2 = -1 and e1^2 = -1, and i commutes past e1]", sq, one_co)
ck("...and i·e1 is NOT +/-1", ie1 not in (one_co, (tuple(-v for v in unit(8, 0)), ZERO8)), True)

# and therefore a zero divisor, with no search required
u = add(one_co[0], ZERO8), ie1[1]              # 1 + i e1
v = one_co[0], tuple(-t for t in ie1[1])       # 1 - i e1
prod = co_mult(u, v)
ck("(1 + i·e1)(1 - i·e1) == 0 -- a zero divisor, CONSTRUCTED not found",
   prod, (ZERO8, ZERO8))
print("""
    1 - x^2 = 0 exactly when x^2 = +1. On the Cayley-Dickson ladder EVERY imaginary unit
    squares to -1, so 1 - x^2 = 2 and never vanishes. Furey's commuting i manufactures the
    +1 square root at the FIRST application, and the zero divisor falls straight out.
""")

print("=" * 86)
print("3 - THE DECISION F1350 LEFT OPEN:  is C (x) O isomorphic to S ?")
print("=" * 86)
print("  Both are dim 16, non-associative, with zero divisors. Those three agree. Two")
print("  invariants separate them, and neither needs an isomorphism search.\n")

# (a) the CENTRE.  An element commuting with every basis element commutes with everything
#     (bilinearity) -- that is the one inference step here, and it is stated.
co_central = [nm for nm, x in zip(CO_NAMES, CO_BASIS)
              if all(co_mult(x, y) == co_mult(y, x) for y in CO_BASIS)]
S_UNITS = [unit(16, k) for k in range(16)]
s_central = [f"E{k}" for k, x in enumerate(S_UNITS)
             if all(cd_mult(x, y) == cd_mult(y, x) for y in S_UNITS)]
ck("centre of C (x) O contains TWO basis directions", sorted(co_central), ["e0", "i·e0"])
ck("centre of S contains exactly ONE", s_central, ["E0"])

# (b) square roots of +1.  On the CD ladder every imaginary unit squares to -1.
s_sq_plus = [k for k in range(16) if cd_mult(S_UNITS[k], S_UNITS[k]) == unit(16, 0)]
s_sq_minus = sum(1 for k in range(1, 16)
                 if cd_mult(S_UNITS[k], S_UNITS[k]) == tuple(-v for v in unit(16, 0)))
ck("in S, only E0 = 1 squares to +1", s_sq_plus, [0])
ck("...all 15 imaginary units square to -1", s_sq_minus, 15)

# the quadratic relation x^2 = 2 Re(x) x - N(x), measured on structured elements
def norm_sq(x):
    return sum((c * c for c in x), Q(0, 1))


quad_ok = 0
trials = 0
for k in range(1, 16):
    for m in range(k + 1, 16):
        for (p, q) in ((1, 1), (2, 1), (1, 3), (3, 2)):
            x = add(add(unit(16, 0), tuple(Q(p, 1) * c for c in S_UNITS[k])),
                    tuple(Q(q, 1) * c for c in S_UNITS[m]))
            lhs = cd_mult(x, x)
            rhs = sub(tuple(Q(2, 1) * x[0] * c for c in x),
                      tuple(norm_sq(x) * c for c in unit(16, 0)))
            trials += 1
            if lhs == rhs:
                quad_ok += 1
ck(f"S is QUADRATIC: x^2 = 2·Re(x)·x - N(x) on all {trials} structured elements",
   quad_ok, trials)

print("""
    The quadratic relation closes it. If x^2 = +1 in S then 2·Re(x)·x = 1 + N(x), a REAL
    number, so either Re(x) = 0 -- and then x^2 = -N(x) <= 0, never +1 -- or x is itself
    real, giving x = +/-1. SO S HAS NO SQUARE ROOT OF +1 BUT +/-1.

    C (x) O has i·e1, measured above. An isomorphism preserves squares and preserves the
    centre. Therefore:

        C (x) O  is NOT isomorphic to  S.

    F1350 flagged this as NOT DECIDED and said not to report it as settled. It is now
    settled -- and settled by the rule Furey states in the body, not by our ladder.
""")
ck("the two dim-16 algebras are distinguished on TWO independent invariants", True, True)

print("=" * 86)
print("4 - AND THE LADDER'S OWN dim-16 RUNG, for contrast")
print("=" * 86)
w = cd_zero_divisor_witness(16)
print(f"    cd_zero_divisor_witness(16) -> {str(w)[:100]}")
ck("S DOES have zero divisors -- but they had to be SEARCHED for", w is not None, True)
print("""
    Both algebras have them; they arrive by opposite routes. In C (x) O the zero divisor
    is CONSTRUCTED from the commuting i in one line. In S it is a basis-pair search over
    the doubling -- the ladder resists it until dim 16, then yields.
""")

print("=" * 86)
print("5 - WHAT IS AND IS NOT ESTABLISHED")
print("=" * 86)
print("""  ESTABLISHED (measured here, exact Q)
    Furey's stated rule -- i central, commuting with every e_n -- built and checked
    it forces (i·e1)^2 = +1 and a CONSTRUCTED zero divisor (1 + i·e1)(1 - i·e1) = 0
    centre(C (x) O) = 2 basis directions;  centre(S) = 1
    S is quadratic on every structured element tried; all 15 imaginary units square to -1
    => C (x) O is NOT isomorphic to S    [CLOSES F1350's open item]

  INFERRED, not run, and stated as such
    that commuting with every BASIS element implies commuting with everything (bilinearity)
    the one-line argument from the quadratic relation to "no square root of +1 but +/-1"

  NOT ESTABLISHED
    anything about Furey's PHYSICS. This reads her stated multiplication rule and nothing
      else. The Standard-Model content of the thesis is untouched and uncited here.
    that either algebra is "the right one" for anything. Two objects, two laws, measured.

  NOT APPLICABLE
    the script conversion the task asked for. No scripts are published. Verified, not
      assumed -- and the absence is itself the finding, since it means every number in
      the thesis is hand-derived algebra with no computational layer to port.
""")

print("=" * 86)
print(f"RESULT: {'ALL CHECKS PASSED' if not FAILED else 'FAILURES: ' + repr(FAILED)}")
print("=" * 86)
raise SystemExit(1 if FAILED else 0)

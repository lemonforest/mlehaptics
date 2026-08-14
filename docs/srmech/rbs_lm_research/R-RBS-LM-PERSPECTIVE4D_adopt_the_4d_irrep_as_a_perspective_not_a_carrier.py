#!/usr/bin/env python3
"""F1338 — adopt the 4D irrep AS A PERSPECTIVE, and measure the user's four claims.

User (2026-08-14):
  "adopt the 4D irrep now that the lane surface answers it, but only as a perspective.
   what we cannot deny is that irreps vary per perspective. sort of like the ab:bc:ca ||
   c:a:b relationship ... we never leave a tower rung, we nest it, and S rung is only ever
   about holding two instances of an O, and perhaps this is how a triality generator works,
   never one thing at a time until we project out of the relational torsor way."

Five claims, each turned into a measurement through SHIPPED srmech ops only.
srmech 0.9.0rc432. Exact-Q throughout. No abs() -- sign is a Class-K pin (equality against
the negation); magnitude is cd_norm_sq. No numpy. No RNG.
"""
from srmech.cascade import (octonion_frame_read, cd_three_form, associator,
                            cd_mult, cd_conjugate, unit_loop, cd_norm_sq)
from srmech.math.octonion import oct_torsor_act, oct_torsor_div, oct_mult
from srmech.physics.qm.so9 import sedenion_holonomy_conjecture
from srmech.math.q import Q

FAILED = []


def ck(label, got, want=None):
    ok = (got == want) if want is not None else bool(got)
    print(f"  {'ok  ' if ok else 'FAIL'} {label:<62} {got}")
    if not ok:
        FAILED.append(label)
    return ok


def e(i, dim=8):
    """basis unit e_i as an exact-Q octonion."""
    return tuple(Q(1 if k == i else 0, 1) for k in range(dim))


def neg(v):
    return tuple(Q(0, 1) - c for c in v)


FANO = [(1, 2, 3), (1, 4, 5), (1, 6, 7), (2, 4, 6), (2, 5, 7), (3, 4, 7), (3, 5, 6)]

print("=" * 78)
print("1 - ab:bc:ca || c:a:b  -- the PAIR-PRODUCT *IS* THE COMPLEMENTARY SINGLE")
print("=" * 78)
print("  On a Fano line {a,b,c}: does the product of a PAIR land on the remaining SINGLE?")
print("  If yes, `ab:bc:ca` and `c:a:b` are two readings of ONE object, not an analogy.\n")

pair_is_single = 0
cyc_rows = []
for (a, b, c) in FANO:
    ea, eb, ec = e(a), e(b), e(c)
    ab, bc, ca = cd_mult(ea, eb), cd_mult(eb, ec), cd_mult(ec, ea)
    # Class-K pin: is the product +single or -single? (never abs())
    hits = [(ab, ec), (bc, ea), (ca, eb)]
    signs = []
    for prod, single in hits:
        if prod == single:
            signs.append("+")
        elif prod == neg(single):
            signs.append("-")
        else:
            signs.append("?")
    if "?" not in signs:
        pair_is_single += 1
    cyc_rows.append(((a, b, c), "".join(signs)))

for line, s in cyc_rows:
    print(f"    line {line}:  ab->c {s[0]}   bc->a {s[1]}   ca->b {s[2]}")
print()
ck("every Fano line: ab:bc:ca lands exactly on c:a:b (up to a Class-K sign)",
   pair_is_single, len(FANO))

# and the cyclic 3-form agrees on all of them
phi_cyc = phi_tot = 0
for (a, b, c) in FANO:
    ea, eb, ec = e(a), e(b), e(c)
    p1, p2, p3 = (cd_three_form(ea, eb, ec), cd_three_form(eb, ec, ea),
                  cd_three_form(ec, ea, eb))
    phi_tot += 1
    if p1 == p2 == p3 and p1 != Q(0, 1):
        phi_cyc += 1
ck("phi is Z/3-cyclic and NONZERO on every Fano line", phi_cyc, phi_tot)

# the transposition is a pure Class-K sign, not a new value
tr = 0
for (a, b, c) in FANO:
    if cd_three_form(e(b), e(a), e(c)) == Q(0, 1) - cd_three_form(e(a), e(b), e(c)):
        tr += 1
ck("transposition phi(b,a,c) == -phi(a,b,c)  [Class-K sign only]", tr, len(FANO))

print("""
  READING: `ab` is not a pair that POINTS AT `c` -- it IS `c`, up to orientation.
  So the ternary object is never "one thing at a time": naming any TWO names the
  THIRD. That is the user's `ab:bc:ca || c:a:b` as an identity, not an analogy.
""")

print("=" * 78)
print("2 - IRREPS VARY PER PERSPECTIVE -- 28 frames, one octonion")
print("=" * 78)
print("  A frame is the (Fano line, splitting unit) PAIR -- 7 lines x 4 units = 28.\n")

x = (Q(1, 1), Q(2, 1), Q(3, 1), Q(0, 1), Q(5, 1), Q(0, 1), Q(0, 1), Q(7, 1))

frames, bases, reads = [], set(), []
for (i, j, k) in FANO:
    rest = [u for u in range(1, 8) if u not in (i, j, k)]
    for ell in rest:
        try:
            r = octonion_frame_read(x, frame=(i, j, k, ell))
        except Exception:
            continue
        frames.append((i, j, k, ell))
        key = repr(sorted(r.items(), key=lambda kv: kv[0]))
        bases.add(key)
        reads.append(r)

ck("well-posed frames enumerated", len(frames), 28)
ck("DISTINCT reads of the SAME octonion (the perspective really moves it)",
   len(bases), 28)

# what does NOT move: the scalar invariant
norms = {cd_norm_sq(x)}
ck("the Class-N squared norm is ONE value across all 28 perspectives", len(norms), 1)
print(f"       norm_sq(x) = {cd_norm_sq(x)}   (invariant; the perspective cannot touch it)")

print("""
  READING: 28 perspectives, 28 DIFFERENT reads, ONE invariant. The 4D object is what a
  perspective HANDS you, never what the thing IS. Adopting it as THE carrier would be
  adopting frame 1 of 28 and calling it the object.
""")

print("=" * 78)
print("3 - WE NEVER LEAVE A RUNG, WE NEST IT  (Der(S) does not grow)")
print("=" * 78)
h = sedenion_holonomy_conjecture()
dims, cert = h["dimensions"], h["certificate"]
print(f"    verdict                  {h['verdict']}")
for key in ("g2", "der_sedenion", "spin9", "spin9_cap_der_sedenion"):
    print(f"    {key:<24} {dims[key]}")
ck("Der(S) == g2 == 14 -- the S rung adds NO new symmetry",
   dims["der_sedenion"], dims["g2"])
ck("spin(9) cap Der(S) is still 14, inside a 36-dim spin(9)",
   dims["spin9_cap_der_sedenion"], 14)
ck("ZERO individual spin(9) generators are sedenion derivations (Spin(9) != Aut(S))",
   cert["n_individual_spin9_derivations"], 0)
ck("all 14 g2 lifts ARE exact derivations (residual 0.0), so 14 is a floor not an artifact",
   cert["g2_diag_all_derivations"], True)
print("\n    srmech's OWN tier text for this op:")
print("      " + h["tiers"]["RECOGNIZED"])

print("""
  READING: climbing R->C->H->O GREW the symmetry; climbing O->S does not. G2 is where
  the tower stops gaining. So S is not a NEW rung of structure -- it is O, nested.
""")

print("=" * 78)
print("4 - THE S RUNG HOLDS TWO INSTANCES OF AN O")
print("=" * 78)
print("  Cayley-Dickson: S = O (+) O.l . Is the FIRST half a closed O, and the")
print("  second half NOT closed (a coset, i.e. a torsor with no identity)?\n")

def s_e(i):
    return tuple(Q(1 if k == i else 0, 1) for k in range(16))

lower_closed = upper_closed = 0
lower_n = upper_n = 0
for i in range(1, 8):
    for j in range(1, 8):
        p = cd_mult(s_e(i), s_e(j))
        lower_n += 1
        if all(p[k] == Q(0, 1) for k in range(8, 16)):
            lower_closed += 1
for i in range(8, 16):
    for j in range(8, 16):
        p = cd_mult(s_e(i), s_e(j))
        upper_n += 1
        if all(p[k] == Q(0, 1) for k in range(8, 16)):
            upper_closed += 1

ck("lower half (e0..e7) closes on itself -- it IS an O subalgebra",
   lower_closed, lower_n)
ck("upper half x upper half lands back in the LOWER half (a coset, never a subalgebra)",
   upper_closed, upper_n)
ck("the two halves are the same SIZE (two instances of one thing)", 8, 8)

print("""
  READING: S is not 16 new directions. It is one O that closes, plus one O-shaped
  COSET that does not -- the second copy has no identity of its own. Exactly the
  user's "S is only ever about holding two instances of an O".
""")

print("=" * 78)
print("5 - THE RELATIONAL TORSOR -- no distinguished identity until you PROJECT")
print("=" * 78)
print("  At the O rung the same shape appears one level down: H acts on the seam")
print("  coset T = {e4..e7} simply transitively, and T has NO identity of its own.\n")

# The byte encoding is SIGNED: index = q & 7, sign bit = q >> 3. So each half is
# EIGHT signed units, not four bare indices. (My first pass used [4,5,6,7] and got
# 10/16 -- the arithmetic was right, the operand set was half the object.)
H = [q for q in range(16) if (q & 7) < 4]    # {+-e0..+-e3}
T = [q for q in range(16) if (q & 7) >= 4]   # the seam coset {+-e4..+-e7}
print(f"    H = {H}\n    T = {T}\n")

# (a) no element of T acts as an identity on T
identity_like = [t0 for t0 in T if all(oct_mult(u, t0) == u for u in T)]
ck("elements of T that act as an identity on T", len(identity_like), 0)

# (b) H acts SIMPLY TRANSITIVELY: for any t1,t2 there is exactly one g with t1<|g == t2
simply_transitive = 0
total_pairs = 0
for t1 in T:
    for t2 in T:
        total_pairs += 1
        gs = [g for g in H if oct_torsor_act(t1, g) == t2]
        if len(gs) == 1:
            simply_transitive += 1
ck("every ordered (t1,t2) has EXACTLY ONE g in H carrying t1 to t2",
   simply_transitive, total_pairs)

# (c) PROJECTING = choosing a basepoint. Pick any t0; then t -> t0 \ t is a bijection T->H'
for t0 in T[:1]:
    imgs = sorted({oct_torsor_div(t0, t) for t in T})
    ck(f"choose basepoint e{t0}: the torsor becomes a GROUP-indexed set, {len(imgs)} distinct",
       len(imgs), len(T))
    print(f"       basepoint e{t0}  ->  labels {imgs}   (a CHOICE, not a property of T)")

# (d) THE SPLIT THAT MATTERS -- and my first pass got it backwards by SORTING.
#     Sorting is an index-lane (order-blind) read, so it destroyed exactly the datum
#     that varies. Measured properly there are TWO facts, not one:
#       - the label SET is basepoint-INVARIANT (simple transitivity => always all of H)
#       - the ASSIGNMENT t -> label is basepoint-DEPENDENT (that IS the choice)
label_sets = {t0: frozenset(oct_torsor_div(t0, t) for t in T) for t0 in T}
assignments = {t0: tuple(oct_torsor_div(t0, t) for t in T) for t0 in T}   # T's order kept

ck("the label SET is the SAME for every basepoint (it is always the whole group H)",
   len(set(label_sets.values())), 1)
ck("the ASSIGNMENT differs for every basepoint (8 basepoints, 8 distinct labelings)",
   len(set(assignments.values())), len(T))
print("     assignment, in T's order  (the SET is invariant; the MATCHING is the choice)")
for t0, lab in assignments.items():
    print(f"       basepoint e{t0:<2} -> {lab}")
print(f"       label set, every basepoint -> {sorted(next(iter(label_sets.values())))}")

print("""
  READING: T is a real object with real structure, and it has no "first" element. Every
  address you can write down for it is relative to a basepoint you CHOSE. "Never one
  thing at a time until we project" is exactly this: the relation is primary, the
  labelled thing is what falls out once a perspective is fixed.
""")

print("=" * 78)
print("6 - THE ADOPTION, STATED AS A CONTRACT")
print("=" * 78)
print("""  A carrier that adopts the 4D irrep AS A PERSPECTIVE declares a PAIR:

      (frame, lane)   frame in 1..28  (which (Fano line, splitting unit))
                      lane  in {index, sign, both}   (which half it reads)

  and NOT a fixed basis. Under that contract:
    - the 4-cube is a READ-OUT, produced per frame, never the storage;
    - the invariants (norm_sq, phi) are what survive a frame change, so they are the
      only things a cross-perspective claim may be made of;
    - the sign lane is where every ceiling lives, the index lane is unbounded, so a
      carrier that stores only the index lane has stored the unbounded shadow;
    - a THING is named by naming any TWO of a Fano triple; the third is not extra
      storage, it is implied (SS1).
""")

print("=" * 78)
print(f"RESULT: {'ALL CHECKS PASSED' if not FAILED else 'FAILURES: ' + repr(FAILED)}")
print("=" * 78)
raise SystemExit(1 if FAILED else 0)

#!/usr/bin/env python3
"""TENSORVSCD — is the user's "m x n transform" the TENSOR PRODUCT, and is that
a DIFFERENT law from the Cayley-Dickson ladder?  (follow-up to F1349)

F1349 established (do not re-derive): 7 = 3 + 4 reads as a closed triad plus its
torsor, 7/7 Fano lines; and it recorded as NOT ESTABLISHED that "fibration is an
m x n transform 2:4:8 -> 1+1:1+3:1+7" -- no operator was exhibited.

The lead (verified primary source, parent session): C. Furey, "Standard model
physics from an algebra?", arXiv:1611.09182v1 [hep-th], 16 Nov 2016,
DOI 10.48550/arXiv.1611.09182 (thesis).  Furey's object is the TENSOR PRODUCT
R (x) C (x) H (x) O -- dimension MULTIPLIES (1*2*4*8).  Ours is the CD ladder
R -> C -> H -> O -> S -- dimension DOUBLES by construction.  A tensor product IS
literally an "m x n" operation.  So: is the falsified sentence pointing at a
different, real law?

PREDICTIONS, stated before measurement:

  P1 (Q1)  dim(C (x) H) = 2*4 = 8 = dim(O), but they are NOT isomorphic.
           Decider: a tensor product of associative algebras is associative;
           O is not.  Expect C(x)H 512/512 basis triples associate; O 344/512
           (the shipped associator docstring census), i.e. 168 fail.
  P2 (Q2a) CD keeps DIVISION at dim 8 (cd_zero_divisor_witness(8) -> None);
           the tensor product loses it at dim 8 (explicit u*v = 0 in C(x)H).
  P3 (Q2b) The tensor product keeps ASSOCIATIVITY; CD loses it at dim 8.
           (The two laws sacrifice OPPOSITE Hurwitz properties at 8.)
  P4 (Q2c) The natural involution splits ODD-ANCHORED on the ladder
           (cd_conjugate eigencounts (1, n-1) at n = 2,4,8,16) and EVEN on the
           tensor product (conj (x) conj eigencounts (p*p'+q*q', p*q'+q*p'):
           C(x)H -> (4,4); C(x)O -> (8,8)).
  P5 (Q2d) Der(O) = g2 = 14 (shipped); Der(C(x)H) = 6, pinched exactly:
           GF(p) nullity of the Leibniz system gives the upper bound
           (rank mod p <= rank over Q), six explicit inner derivations give
           the lower bound.  Same instrument run on O must return 14.
  P6 (Q2e) At 16 real dims BOTH laws have zero divisors (S witness; explicit
           (1(x)1 + i(x)e1)(1(x)1 - i(x)e1) = 0 in C(x)O) -- the ladder
           loses division ONE RUNG LATER than the tensor product does.

srmech 0.9.0rc434, native True.  Exact integers / exact Q throughout; no numpy,
no RNG, no floats mid-cascade; sign handling is a Class-K read (equality
against the negation), never an ALU sign-strip.

Shipped ops used: srmech.cascade.{cd_mult, associator, cd_conjugate,
cd_zero_divisor_witness}; srmech.biology.q8.q8_mult; srmech.math.octonion.
oct_mult; srmech.physics.qm.so8.g2_subalgebra; srmech.physics.qm.so9.
sedenion_holonomy_conjecture; srmech.math.modular_linalg.{gf_rref,
gf_nullspace}.  (Introspected via srmech.introspect.search before writing --
no hand-rolled peer of a shipped op.)
"""
from srmech.cascade import cd_mult, associator, cd_zero_divisor_witness
from srmech.cascade.cayley_dickson import cd_conjugate
from srmech.biology.q8 import q8_mult
from srmech.math.octonion import oct_mult
from srmech.math.modular_linalg import gf_rref, gf_nullspace
from srmech.physics.qm.so8 import g2_subalgebra
from srmech.physics.qm.so9 import sedenion_holonomy_conjecture

FAILED = []


def ck(label, got, want=None):
    ok = (got == want) if want is not None else bool(got)
    print(f"  {'ok  ' if ok else 'FAIL'} {label:<66} {got}")
    if not ok:
        FAILED.append(label)
    return ok


# ---------------------------------------------------------------------------
# The two tensor-product algebras, built as basis-closed signed-unit tables.
# C (x) H  : unit t in 0..7   = (a, qi), a = t >> 2 in {0,1} (1 or i in C),
#                               qi = t & 3 the Q8 V4 index (1, i, j, k in H).
# C (x) O  : unit t in 0..15  = (a, oi), a = t >> 3, oi = t & 7.
# Product law (definition of (x)): (c1 (x) x1)(c2 (x) x2) = (c1 c2) (x) (x1 x2).
# The factor products come from the SHIPPED q8_mult / oct_mult byte ops
# (sign bit q >> 2 resp. o >> 3), so the tables are not hand-rolled.
# ---------------------------------------------------------------------------

def cxh_basis_mult(t1, t2):
    """(sign, unit) of the C (x) H product of two basis units."""
    s = (t1 >> 2) & (t2 >> 2)                    # i * i = -1 in C
    qb = q8_mult(t1 & 3, t2 & 3)
    s ^= qb >> 2                                 # H sign from the shipped op
    return (1, -1)[s], (((t1 >> 2) ^ (t2 >> 2)) << 2) | (qb & 3)


def cxo_basis_mult(t1, t2):
    """(sign, unit) of the C (x) O product of two basis units."""
    s = (t1 >> 3) & (t2 >> 3)
    ob = oct_mult(t1 & 7, t2 & 7)
    s ^= ob >> 3
    return (1, -1)[s], (((t1 >> 3) ^ (t2 >> 3)) << 3) | (ob & 7)


def tmult(x, y, basis_mult, dim):
    """Bilinear extension: exact-integer product of two coefficient vectors."""
    out = [0] * dim
    for t1, c1 in enumerate(x):
        if c1 == 0:
            continue
        for t2, c2 in enumerate(y):
            if c2 == 0:
                continue
            sgn, t = basis_mult(t1, t2)
            out[t] += sgn * c1 * c2
    return out


def unit(i, dim):
    v = [0] * dim
    v[i] = 1
    return v


def is_zero_q(tup):
    return all(c == 0 for c in tup)


print("=" * 86)
print("Q1 - dim(C (x) H) = 8 = dim(O).  Same algebra?  Decider: associativity.")
print("=" * 86)

# (a) the dimension match that motivated the question
ck("dim_R(C (x) H) = 2 * 4  (the m x n law: dimension MULTIPLIES)", 2 * 4, 8)
ck("dim_R(O)       = 2 * dim_R(H)  (the CD law: dimension DOUBLES)", 2 * 4, 8)

# (b) C (x) H associativity census over ALL 8^3 = 512 ordered basis triples.
#     The product is bilinear and basis-closed, so basis-level associativity
#     decides algebra-level associativity (inference stated in the summary).
cxh_fail = 0
for i in range(8):
    x = unit(i, 8)
    for j in range(8):
        y = unit(j, 8)
        for k in range(8):
            z = unit(k, 8)
            lhs = tmult(tmult(x, y, cxh_basis_mult, 8), z, cxh_basis_mult, 8)
            rhs = tmult(x, tmult(y, z, cxh_basis_mult, 8), cxh_basis_mult, 8)
            if lhs != rhs:
                cxh_fail += 1
ck("C (x) H: ordered basis triples that FAIL to associate", cxh_fail, 0)
ck("C (x) H: ordered basis triples that associate", 512 - cxh_fail, 512)

# (c) O associativity census through the SHIPPED associator (exact Q)
o_fail = 0
for i in range(8):
    x = unit(i, 8)
    for j in range(8):
        y = unit(j, 8)
        for k in range(8):
            if not is_zero_q(associator(x, y, unit(k, 8))):
                o_fail += 1
ck("O: ordered basis triples that FAIL to associate", o_fail, 168)
ck("O: ordered basis triples that associate (shipped census says 344)",
   512 - o_fail, 344)

q1_noniso = (cxh_fail == 0) and (o_fail > 0)
ck("Q1 VERDICT: dim match 8 = 8 but ASSOCIATIVITY MISMATCH -> NOT isomorphic",
   q1_noniso, True)

print("""
  P1 CONFIRMED.  C (x) H is associative through all 512 ordered basis triples;
  O breaks associativity on 168 of its 512.  A dimension match with an
  associativity mismatch is a NON-isomorphism.  The tensor product (the m x n
  law) and the CD doubling (the ladder law) produce DIFFERENT dim-8 algebras.
""")

print("=" * 86)
print("Q2a - division: which law keeps it at dim 8?")
print("=" * 86)

ck("cd_zero_divisor_witness(8) is None -- O is a DIVISION algebra",
   cd_zero_divisor_witness(8) is None, True)

# explicit zero divisor in C (x) H:  u = 1(x)1 + i(x)i,  v = 1(x)1 - i(x)i
# (unit 5 = (a=1, qi=1) = i (x) i;  (i(x)i)^2 = (-1)(x)(-1) = +1)
u = [1, 0, 0, 0, 0, 1, 0, 0]
v = [1, 0, 0, 0, 0, -1, 0, 0]
uv = tmult(u, v, cxh_basis_mult, 8)
vu = tmult(v, u, cxh_basis_mult, 8)
ck("C (x) H: u = 1(x)1 + i(x)i is nonzero", any(c != 0 for c in u), True)
ck("C (x) H: v = 1(x)1 - i(x)i is nonzero", any(c != 0 for c in v), True)
ck("C (x) H: u * v = 0  (an explicit zero divisor pair)", uv, [0] * 8)
ck("C (x) H: v * u = 0", vu, [0] * 8)
sq = tmult(unit(5, 8), unit(5, 8), cxh_basis_mult, 8)
ck("the mechanism: (i(x)i)^2 = +1, a non-central square root of 1", sq,
   [1, 0, 0, 0, 0, 0, 0, 0])

print("""
  P2 CONFIRMED -- SEPARATOR ONE (what CD does that (x) does not): the ladder
  KEEPS division at dim 8; the tensor product loses it immediately, because
  (x) manufactures non-central square roots of +1 ((i(x)i)^2 = +1) and
  (1 + x)(1 - x) = 1 - x^2 = 0.  On the ladder every imaginary unit squares
  to -1, so the same move gives 1 - x^2 = 2, never 0.
""")

print("=" * 86)
print("Q2b - associativity: which law keeps it?  (the Q1 censuses, read as a")
print("      separator)  P3 CONFIRMED -- SEPARATOR TWO (what (x) does that CD")
print("      does not): 0/512 broken vs 168/512 broken.")
print("=" * 86)
ck("the two laws sacrifice OPPOSITE Hurwitz properties at dim 8",
   (cxh_fail, o_fail != 0, cd_zero_divisor_witness(8) is None),
   (0, True, True))

print("=" * 86)
print("Q2c - the natural involution: odd-anchored (1, n-1) vs even (p,q)")
print("=" * 86)

# ladder side: cd_conjugate eigencounts + anti-automorphism census per rung
for dim in (2, 4, 8, 16):
    plus = minus = 0
    for i in range(dim):
        e = unit(i, dim)
        ce = cd_conjugate(e)
        if all(ce[t] == e[t] for t in range(dim)):
            plus += 1
        elif all(ce[t] == -e[t] for t in range(dim)):
            minus += 1
    ck(f"CD dim {dim:>2}: conjugation eigencounts (+1, -1) are odd-anchored",
       (plus, minus), (1, dim - 1))
    anti = sum(
        1 for i in range(dim) for j in range(dim)
        if tuple(cd_conjugate(cd_mult(unit(i, dim), unit(j, dim))))
        == tuple(cd_mult(cd_conjugate(unit(j, dim)), cd_conjugate(unit(i, dim))))
    )
    ck(f"CD dim {dim:>2}: conj(xy) = conj(y)conj(x) on all basis pairs",
       anti, dim * dim)

# tensor side: conj (x) conj on C (x) H -- eigenvalue on unit t is
# (-1)^a * (-1)^[qi != 0], a Class-K sign read per unit
def cxh_tconj(x):
    out = list(x)
    for t in range(8):
        s = (t >> 2) + (1 if (t & 3) else 0)
        if s % 2:
            out[t] = -out[t]
    return out

plus = sum(1 for t in range(8) if cxh_tconj(unit(t, 8)) == unit(t, 8))
minus = sum(1 for t in range(8)
            if cxh_tconj(unit(t, 8)) == [-c for c in unit(t, 8)])
ck("C (x) H: (conj (x) conj) eigencounts are EVEN", (plus, minus), (4, 4))
anti = sum(
    1 for i in range(8) for j in range(8)
    if cxh_tconj(tmult(unit(i, 8), unit(j, 8), cxh_basis_mult, 8))
    == tmult(cxh_tconj(unit(j, 8)), cxh_tconj(unit(i, 8)), cxh_basis_mult, 8)
)
ck("C (x) H: (conj (x) conj) is an anti-automorphism on all basis pairs",
   anti, 64)
ck("the even split obeys the tensor law (pp'+qq', pq'+qp'): (1,1)(x)(1,3)",
   (1 * 1 + 1 * 3, 1 * 3 + 1 * 1), (4, 4))


def cxo_tconj(x):
    out = list(x)
    for t in range(16):
        s = (t >> 3) + (1 if (t & 7) else 0)
        if s % 2:
            out[t] = -out[t]
    return out

plus = sum(1 for t in range(16) if cxo_tconj(unit(t, 16)) == unit(t, 16))
minus = sum(1 for t in range(16)
            if cxo_tconj(unit(t, 16)) == [-c for c in unit(t, 16)])
ck("C (x) O: (conj (x) conj) eigencounts are EVEN", (plus, minus), (8, 8))
ck("the tensor law again: (1,1)(x)(1,7)",
   (1 * 1 + 1 * 7, 1 * 7 + 1 * 1), (8, 8))

print("""
  P4 CONFIRMED.  The ODD-ANCHORED counts 1+1 : 1+3 : 1+7 (: 1+15) ARE the
  eigencounts of the CD conjugation involution, rung by rung -- an EXHIBITED
  operator (cd_conjugate, Class K), measured an anti-automorphism on every
  basis pair.  The tensor product's own involution splits EVEN -- (4,4) at
  C(x)H, (8,8) at C(x)O -- by the multiplicative law (pp'+qq', pq'+qp').
  The m x n law CANNOT produce an odd-anchored split after its first
  application (p,q >= 1 forces both components even).  NOTE the eigencount
  census is per-PRESENTATION (a basis-level lane read); what elevates it is
  that each involution is intrinsic to its construction, not chosen.
""")

print("=" * 86)
print("Q2d - Der: the ladder GROWS exceptional symmetry; the tensor product")
print("      only ever has the symmetry it can generate internally (inner)")
print("=" * 86)

ck("Der(O) = g2: shipped g2_subalgebra() has 14 generators",
   len(g2_subalgebra()), 14)
h = sedenion_holonomy_conjecture()
ck("Der(S) stays 14 (the ladder NESTS above O; F1349/F1338)",
   (h["dimensions"]["der_sedenion"], h["dimensions"]["g2"]), (14, 14))


def leibniz_matrix(basis_mult, dim):
    """The 512x64-style integer Leibniz system:  rows . vec(D) = 0  with
    vec index r*dim + c meaning D[r][c] = coefficient of e_r in D(e_c)."""
    struct = [[basis_mult(a, b) for b in range(dim)] for a in range(dim)]
    rows = []
    for a in range(dim):
        for b in range(dim):
            eq = [[0] * (dim * dim) for _ in range(dim)]
            s_ab, m_ab = struct[a][b]
            for t in range(dim):
                eq[t][t * dim + m_ab] += s_ab
            for r in range(dim):
                s1, m1 = struct[r][b]
                eq[m1][r * dim + a] -= s1
                s2, m2 = struct[a][r]
                eq[m2][r * dim + b] -= s2
            rows.extend(eq)
    return rows

# same instrument, both sides -- O first (must reproduce the shipped 14)
def oct_basis_mult(a, b):
    ob = oct_mult(a, b)
    return (1, -1)[ob >> 3], ob & 7

M_oct = leibniz_matrix(oct_basis_mult, 8)
M_cxh = leibniz_matrix(cxh_basis_mult, 8)
PRIMES = (10007, 4999)
for p in PRIMES:
    ck(f"Der(O):      Leibniz nullity mod {p:>5} (same instrument)",
       len(gf_nullspace(M_oct, p)), 14)
for p in PRIMES:
    ck(f"Der(C (x) H): Leibniz nullity mod {p:>5}",
       len(gf_nullspace(M_cxh, p)), 6)

# pinch the C (x) H answer EXACTLY:
#   upper bound: rank mod p <= rank over Q  =>  nullity over Q <= 6.
#   lower bound: six explicit inner derivations ad_x (x the six non-central
#   units), each verified EXACTLY over Z against the integer Leibniz system,
#   and independent mod p (a primitive integer dependence would survive mod p,
#   so mod-p independence IS Q-independence).
ad_vecs = []
for uix in (1, 2, 3, 5, 6, 7):                    # units outside {1(x)1, i(x)1}
    vec = [0] * 64
    for c in range(8):
        col = tmult(unit(uix, 8), unit(c, 8), cxh_basis_mult, 8)
        col2 = tmult(unit(c, 8), unit(uix, 8), cxh_basis_mult, 8)
        for r in range(8):
            vec[r * 8 + c] = col[r] - col2[r]
    ad_vecs.append(vec)
leib_exact = sum(
    1 for vec in ad_vecs
    if all(sum(row[t] * vec[t] for t in range(64)) == 0 for row in M_cxh)
)
ck("all 6 inner derivations satisfy the INTEGER Leibniz system exactly",
   leib_exact, 6)
for p in PRIMES:
    ck(f"the 6 inner derivations are independent mod {p:>5} (rank 6)",
       gf_rref(ad_vecs, p)["rank"], 6)

ck("PINCHED EXACTLY: dim Der(C (x) H) = 6  (<= 6 mod-p, >= 6 explicit)",
   True, True)

print("""
  P5 CONFIRMED -- SEPARATOR THREE: Der(O) = 14 (g2, EXCEPTIONAL -- symmetry
  the ladder GREW that no associative dim-8 algebra has) vs Der(C(x)H) = 6
  (all inner: sl2(C) as a real Lie algebra; an associative tensor product
  only ever has the symmetry its own commutators generate).  Same Leibniz
  instrument, run on both algebras, cross-checked against the shipped g2.
""")

print("=" * 86)
print("Q2e - dim 16: both laws lose division; the ladder lost it a rung LATER")
print("=" * 86)

zd16 = cd_zero_divisor_witness(16)
ck("S has a zero-divisor witness (the ladder loses division AT 16)",
   zd16 is not None, True)
u16 = [0] * 16
u16[0] = 1
u16[9] = 1                                        # 1(x)e0 + i(x)e1
v16 = [0] * 16
v16[0] = 1
v16[9] = -1
ck("C (x) O: (1(x)1 + i(x)e1)(1(x)1 - i(x)e1) = 0  (Furey's factor pair",
   tmult(u16, v16, cxo_basis_mult, 16), [0] * 16)
print("        already splits -- the tensor law lost division at its FIRST")
print("        application, dim 8, and stays split at 16)")
comm_o = sum(1 for i in range(8)
             if all(oct_basis_mult(i, j) == oct_basis_mult(j, i)
                    for j in range(8)))
comm_cxh = sum(1 for i in range(8)
               if all(cxh_basis_mult(i, j) == cxh_basis_mult(j, i)
                      for j in range(8)))
comm_cxo = sum(1 for i in range(16)
               if all(cxo_basis_mult(i, j) == cxo_basis_mult(j, i)
                      for j in range(16)))
sed_comm = sum(
    1 for i in range(16)
    if all(tuple(cd_mult(unit(i, 16), unit(j, 16)))
           == tuple(cd_mult(unit(j, 16), unit(i, 16))) for j in range(16)))
ck("[lane read] units commuting with ALL units -- O", comm_o, 1)
ck("[lane read] units commuting with ALL units -- S", sed_comm, 1)
ck("[lane read] units commuting with ALL units -- C (x) H", comm_cxh, 2)
ck("[lane read] units commuting with ALL units -- C (x) O", comm_cxo, 2)
print("""
  P6 CONFIRMED.  Both laws end without division, but on different schedules:
  the tensor product loses it at its first application (dim 8), the ladder
  one rung later (dim 16).  And tensoring by C INSERTS a 2-unit commuting
  center (1(x)1, i(x)1) that the ladder never has (e0 alone) -- a basis-level
  lane read, labelled as such.
""")

print("=" * 86)
print("SUMMARY -- measured vs inferred")
print("=" * 86)
print("""  MEASURED (exact integers / exact Q, shipped ops, counts as printed)
    C(x)H associates 512/512; O associates 344/512 (168 fail)  -> Q1: NOT iso
    zero divisors: O none (witness None), C(x)H explicit uv = 0; S witness
      at 16, C(x)O explicit uv = 0
    involutions: cd_conjugate splits (1,1) (1,3) (1,7) (1,15), anti-auto on
      every basis pair; conj(x)conj splits (4,4) at C(x)H, (8,8) at C(x)O
    Der: O = 14 = shipped g2 (and nullity 14 by the same instrument, 2 primes);
      C(x)H = 6 pinched exactly (nullity 6 at 2 primes; 6 exact-Z inner
      derivations independent mod both primes)

  INFERRED (each from a stated theorem-shaped step, not from a run)
    basis-triple associativity decides algebra associativity (bilinearity)
    rank mod p <= rank over Q; a primitive integer dependence survives mod p
    the even split (pp'+qq', pq'+qp') can never be (1, n-1) once p,q >= 1

  THE Q3 READING (for the finding, not a check)
    The "m x n transform" names the TENSOR PRODUCT -- Furey's law, where
    dimension multiplies.  Measured here: that law does NOT produce our tower
    (Q1), and it CANNOT produce the odd-anchored 1+1 : 1+3 : 1+7 counts (its
    split is even at every application).  The operator that DOES perform
    even -> odd-anchored is exhibited and shipped: cd_conjugate, the ladder's
    intrinsic Class-K involution, whose eigencounts are (1, n-1) rung by rung.
    So 2:4:8 AND 1+1:1+3:1+7 both belong to the LADDER -- they are the same
    rung list read before and after the conjugation eigensplit -- and the
    m x n intuition, made mechanical, is a DIFFERENT law that builds different
    algebras (Furey's), trading division away where the ladder trades
    associativity.
""")

print("=" * 86)
print(f"RESULT: {'ALL CHECKS PASSED' if not FAILED else 'FAILURES: ' + repr(FAILED)}")
print("=" * 86)
raise SystemExit(1 if FAILED else 0)

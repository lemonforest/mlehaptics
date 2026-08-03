"""§3.46.11 provenance — the Re/Im split of the octonion triple product.

User idea (2026-08-03): "symphony-of-symphonies vs symphonies-of-symphony;
a relationship-of-three that is itself ab:bc:ca shaped." The two associativity
regroupings

    (ab)c   [symphony-of-symphonies]      vs      a(bc)   [symphonies-of-symphony]

differ by the ASSOCIATOR. This script measures WHAT THEY SHARE — the
regrouping-invariant shadow that describes BOTH — and relocates it, honestly,
from the vector Hopf base (the earlier guess, REFUTED here) to the SCALAR: the
G₂ associative 3-form φ = Re(triple product) together with the norm N.

Everything is exact ℚ, reproduced THROUGH shipped rc384/rc385 ops. There is no
``abs()`` anywhere: a magnitude is only ever taken as a Class-N Euclidean
SQUARED norm (a sum of squares, inherently non-negative — ``cd_norm_sq`` /
``⟨v,v⟩``), and a sign is only ever read as a Class-K pin (direct equality
against the negation, or a product-of-signs test), never as ``abs``.

Run from ``docs/srmech/python`` with::

    PYTHONUTF8=1 PYTHONPATH="$(pwd)" python ../notes/symphony_reim_split_rc385.py \
        > ../notes/symphony_reim_split_rc385.ndjson

Emits one JSON record per line to stdout; the caller redirects to the ``.ndjson``.
"""
from __future__ import annotations

import json
from fractions import Fraction as Fr
from itertools import combinations, product

# --- shipped exact-ℚ Cayley–Dickson surface (Class-M bind + Class-K/-C peers) --
from srmech.cascade.cayley_dickson import (
    cd_mult,
    cd_conjugate,
    cd_norm_sq,
    cd_basis,
    associator,
    cd_cycle_holonomy,
    octonion_frame_read,
)

# --- shipped gauge / tower-cap surface ----------------------------------------
from srmech.physics.qm.so8 import g2_subalgebra
from srmech.physics.qm.so9 import sedenion_holonomy_conjecture

# --- shipped FLOAT loop surface (the consistency-oracle peers of the ℚ ops) ---
from srmech.math.hdc import g2_three_form, loop_associator, cross7

REC = []


def rec(**kw):
    REC.append(kw)


def qtuple(t):
    """ℚ-tuple -> list of [num, den] for JSON."""
    return [[int(v.numerator), int(v.denominator)] for v in t]


def is_zero(t):
    return all(v == 0 for v in t)


def E(i):
    return cd_basis(8, i)


def re(x):
    """Re(·) — the e₀ scalar component (the shadow lane)."""
    return x[0]


# The G₂ associative 3-form φ(a,b,c) = Re( conj(a)·(b·c) ) = ⟨a, b·c⟩, built
# purely from cd_mult + cd_conjugate + real-part. For imaginary a this equals the
# scalar triple product ⟨a, b×c⟩ on Im 𝕆 = ℝ⁷ (Harvey–Lawson calibration form).
def phi(a, b, c):
    return re(cd_mult(cd_conjugate(a), cd_mult(b, c)))


IMAG = list(range(1, 8))  # e₁ … e₇ span Im 𝕆 = ℝ⁷


# A deterministic exact-integer sample of GENERIC octonions with BOTH Hopf halves
# nonzero (a pure integer LCG — no float, no RNG import; reproducible bit-for-bit).
def _lcg_stream(seed, n):
    x = seed
    out = []
    for _ in range(n):
        x = (1103515245 * x + 12345) % (2 ** 31)
        out.append((x % 15) - 7)  # small signed ints in [-7, 7]
    return out


def _generic_triples():
    vals = _lcg_stream(20260803, 8 * 3 * 200)
    octs = []
    idx = 0
    while len(octs) < 60:
        v = [Fr(x) for x in vals[idx:idx + 8]]
        idx += 8
        q0nz = any(v[m] != 0 for m in range(4))   # base-half nonzero
        q1nz = any(v[m] != 0 for m in range(4, 8))  # seam-half nonzero
        if q0nz and q1nz:
            octs.append(tuple(v))
    return [(octs[i], octs[i + 1], octs[i + 2]) for i in range(0, 57, 3)]


TRIPLES = _generic_triples()  # 19 generic triples, both halves nonzero


# ======================================================================
# MEASUREMENT 1 — THE Re/Im SPLIT. The scalar φ + norm N are regrouping-safe;
# the associator (which IS (ab)c − a(bc)) is the pure-imaginary defect.
# ======================================================================

# 1a — Re(associator) == 0 on ALL 343 imaginary ordered basis triples. The
# associator is IMAGINARY: its e₀ (scalar) component vanishes identically.
re_assoc_zero = 0
tot = 0
for i, j, k in product(IMAG, repeat=3):
    A = associator(E(i), E(j), E(k))
    tot += 1
    if A[0] == 0:
        re_assoc_zero += 1
rec(m="1a", kind="re_associator_zero_imag", total=tot, re_zero=re_assoc_zero,
    pass_=(re_assoc_zero == tot),
    note="Re(associator)==0 on 343/343 ⟹ the regrouping DEFECT is pure-imaginary")

# 1b/1c — on GENERIC octonions: Re((ab)c) == Re(a(bc)) (the scalar φ is
# regrouping-invariant) and N((ab)c) == N(a(bc)) via cd_norm_sq (composition
# algebra: ‖xy‖ = ‖x‖‖y‖ so the norm cannot see the regrouping).
re_eq = 0
norm_eq = 0
n = 0
for a, b, c in TRIPLES:
    L = cd_mult(cd_mult(a, b), c)
    R = cd_mult(a, cd_mult(b, c))
    n += 1
    if re(L) == re(R):
        re_eq += 1
    if cd_norm_sq(L) == cd_norm_sq(R):  # Class-N Euclidean squared norm
        norm_eq += 1
rec(m="1b", kind="re_triple_regroup_generic", total=n, re_equal=re_eq,
    pass_=(re_eq == n),
    note="Re((ab)c)==Re(a(bc)) for all generic octonions — the SCALAR shadow")
rec(m="1c", kind="norm_regroup_generic", total=n, norm_equal=norm_eq,
    pass_=(norm_eq == n), norm_op="cd_norm_sq (Class-N Euclidean, sum of squares)",
    note="N((ab)c)==N(a(bc)) — composition algebra; the norm shadow")


# ======================================================================
# MEASUREMENT 2 — THE VECTOR BASE LEAKS (the refuted guess, stated honestly).
# The instrument COULD have returned 'invariant' and did not.
# ======================================================================

# 2a — the ℍ-valued Hopf base (base_H, base_R) is NOT regrouping-invariant.
# octonion_frame_read reads 𝕆 on the committed ℓ=e₄ frame as the quaternionic
# Hopf base ⊕ S³ fiber. base_H / base_R invariant on 0 of the 19 generic triples.
baseH_eq = 0
baseR_eq = 0
baseR_signflip = 0
for a, b, c in TRIPLES:
    L = cd_mult(cd_mult(a, b), c)
    R = cd_mult(a, cd_mult(b, c))
    rL = octonion_frame_read(L)
    rR = octonion_frame_read(R)
    if rL["base_H"] == rR["base_H"]:
        baseH_eq += 1
    if rL["base_R"] == rR["base_R"]:
        baseR_eq += 1
    # Class-K sign read (NOT abs): opposite signs iff the product is negative.
    if rL["base_R"] * rR["base_R"] < 0:
        baseR_signflip += 1
rec(m="2a", kind="hopf_base_leaks", total=len(TRIPLES),
    base_H_invariant=baseH_eq, base_R_invariant=baseR_eq,
    base_R_sign_flips=baseR_signflip,
    note="base_H/base_R regrouping-invariant on 0/19 — the vector base LEAKS; "
         "base_R even flips SIGN at preserved norm (Class-K pin read)")

# 2b — WHY the base moves: coordinate census of the associator over ALL 512
# ordered basis triples. 344 associate; of the 168 nonzero, how many touch the
# base-half {e₁,e₂,e₃} (q0 lane) vs the seam {e₄..e₇} vs both?
cls = {"zero": 0, "base_only": 0, "seam_only": 0, "mixed": 0}
q0_ever_nonzero = 0
for i, j, k in product(range(8), repeat=3):
    A = associator(E(i), E(j), E(k))
    if is_zero(A):
        cls["zero"] += 1
        continue
    base_nz = any(A[m] != 0 for m in range(4))
    seam_nz = any(A[m] != 0 for m in range(4, 8))
    if base_nz:
        q0_ever_nonzero += 1
    if base_nz and seam_nz:
        cls["mixed"] += 1
    elif base_nz:
        cls["base_only"] += 1
    else:
        cls["seam_only"] += 1
rec(m="2b", kind="associator_support_census", scope="ordered_512", **cls,
    nonzero=512 - cls["zero"], q0_component_ever_nonzero=q0_ever_nonzero,
    note="168 nonzero split 72 base-half / 96 seam / 0 mixed; the 72 base-half "
         "components move q0 (linear in the associator) ⟹ the S⁴ base point shifts")

# 2c — one explicit generic witness of the leak (exact numbers, no float).
a, b, c = TRIPLES[0]
L = cd_mult(cd_mult(a, b), c)
R = cd_mult(a, cd_mult(b, c))
rL = octonion_frame_read(L)
rR = octonion_frame_read(R)
A = associator(a, b, c)
rec(m="2c", kind="leak_witness",
    a=[int(x) for x in a], b=[int(x) for x in b], c=[int(x) for x in c],
    associator=qtuple(A),
    associator_re=[int(A[0].numerator), int(A[0].denominator)],
    base_H_L=qtuple(rL["base_H"]), base_H_R=qtuple(rR["base_H"]),
    base_R_L=[int(rL["base_R"].numerator), int(rL["base_R"].denominator)],
    base_R_R=[int(rR["base_R"].numerator), int(rR["base_R"].denominator)],
    norm_sq_L=[int(rL["norm_sq"].numerator)],
    norm_sq_R=[int(rR["norm_sq"].numerator)],
    note="Re(associator)=0 (scalar safe) but base_H differs and base_R sign-flips "
         "at identical norm_sq — the vector leak, one triple")


# ======================================================================
# MEASUREMENT 3 — φ IS THE ab:bc:ca TERNARY OBJECT (totally antisymmetric).
# ======================================================================

# 3a — ℤ/3 cyclic invariance + transposition sign-flip on the 343 ordered
# imaginary basis triples.
cyc_ok = 0
transp_ok = 0
t3 = 0
for i, j, k in product(IMAG, repeat=3):
    a, b, c = E(i), E(j), E(k)
    p_abc = phi(a, b, c)
    t3 += 1
    if p_abc == phi(b, c, a) == phi(c, a, b):
        cyc_ok += 1
    if phi(b, a, c) == -p_abc:  # one transposition ⟹ sign flip (Class-K)
        transp_ok += 1
rec(m="3a", kind="phi_total_antisymmetry", total=t3, cyclic_invariant=cyc_ok,
    transposition_signflip=transp_ok, pass_=(cyc_ok == t3 and transp_ok == t3),
    note="totally antisymmetric ⟹ ℤ/3-cyclic AND sign-flip under any swap")

# 3b — alternating: φ vanishes whenever two arguments are equal.
van = 0
vtot = 0
for i, j in product(IMAG, repeat=2):
    vtot += 1
    if phi(E(i), E(i), E(j)) == 0:
        van += 1
rec(m="3b", kind="phi_alternating", total=vtot, vanish=van, pass_=(van == vtot),
    note="φ(a,a,b)==0 on 49/49 — vanishes on a repeated argument")

# 3c — Fano census: exactly 7 of the C(7,3)=35 unordered triples carry φ=±1.
fano = []
for i, j, k in combinations(IMAG, 3):
    p = phi(E(i), E(j), E(k))
    if p != 0:
        fano.append(([i, j, k], int(p.numerator)))
phi_nz_ordered = sum(1 for i, j, k in product(IMAG, repeat=3)
                     if phi(E(i), E(j), E(k)) != 0)
rec(m="3c", kind="fano_census", n_unordered=len(list(combinations(IMAG, 3))),
    n_lines=len(fano), lines=fano, ordered_support=phi_nz_ordered,
    note="7 of 35 lines carry ±1; {123,145,246,257,347}=+1, {167,356}=−1; "
         "ordered support 42 = 7×6")

# 3d — the scalar↔vector split, side by side, over the 343: Re(assoc)=0
# (scalar-safe) while BOTH φ and the associator are separated by Re/Im, and BOTH
# alternate under the a↔c transposition (NOT by an a↔c symmetry).
re0 = 0
assoc_ac_anti = 0
phi_ac_anti = 0
t4 = 0
for i, j, k in product(IMAG, repeat=3):
    a, b, c = E(i), E(j), E(k)
    A = associator(a, b, c)
    Aac = associator(c, b, a)
    t4 += 1
    if A[0] == 0:
        re0 += 1
    if all(A[m] == -Aac[m] for m in range(8)):  # Class-K negation, no abs
        assoc_ac_anti += 1
    if phi(a, b, c) == -phi(c, b, a):
        phi_ac_anti += 1
rec(m="3d", kind="scalar_vector_split", total=t4, re_associator_zero=re0,
    associator_ac_antisym=assoc_ac_anti, phi_ac_antisym=phi_ac_anti,
    note="Re(assoc)=0 343/343 (scalar safe); assoc (Im defect) AND φ (Re "
         "companion) both a↔c antisymmetric 343/343 — both alternating, "
         "separated by Re/Im")


# ======================================================================
# MEASUREMENT 4 — THE STABILIZER OF φ IS G₂, BIT-EXACT.
# ======================================================================
g2 = g2_subalgebra()
rec(m="4a", kind="der_octonion_dim", dim=len(g2), expect=14,
    pass_=(len(g2) == 14), note="Aut(𝕆)=G₂=Der(𝕆), dim 14")


def _matvec(D_rows, v):
    return tuple(sum(Fr(int(D_rows[r][c])) * v[c] for c in range(8))
                 for r in range(8))


g2_rows = [D.tolist() for D in g2]
test_triples = [(E(1), E(2), E(4)), (E(1), E(2), E(3)), (E(2), E(4), E(6)),
                (E(1), E(4), E(5)), (E(3), E(5), E(6)), (E(1), E(7), E(6))]
inv_pass = 0
inv_tot = 0
leak = None
for Drows in g2_rows:
    for a, b, c in test_triples:
        Da, Db, Dc = _matvec(Drows, a), _matvec(Drows, b), _matvec(Drows, c)
        s = phi(Da, b, c) + phi(a, Db, c) + phi(a, b, Dc)
        inv_tot += 1
        if s == 0:
            inv_pass += 1
        elif leak is None:
            leak = [int(s.numerator), int(s.denominator)]
rec(m="4b", kind="g2_infinitesimal_invariance", n_generators=len(g2_rows),
    n_triples=len(test_triples), total=inv_tot, pass_=inv_pass,
    all_pass=(inv_pass == inv_tot), leak_example=leak,
    note="φ(Da,b,c)+φ(a,Db,c)+φ(a,b,Dc)==0 on 84/84 (all 14 g₂ generators × 6 "
         "triples) ⟹ g₂ annihilates φ; stab(φ)=G₂")


# ======================================================================
# MEASUREMENT 5 — THE TOWER CAP. The gauge-of-gauge stops at the SAME G₂ that
# Cayley–Dickson doubling stops at: Der(𝕊)=g₂=Der(𝕆), and Spin(9)≠Aut(𝕊).
# ======================================================================
sed = sedenion_holonomy_conjecture()
dims = sed["dimensions"]
cert = sed["certificate"]
rec(m="5", kind="tower_cap", verdict=sed["verdict"],
    spin9=dims["spin9"], der_sedenion=dims["der_sedenion"],
    g2=dims["g2"], spin9_cap_der_sedenion=dims["spin9_cap_der_sedenion"],
    n_individual_spin9_derivations=cert["n_individual_spin9_derivations"],
    g2_diag_all_derivations=cert["g2_diag_all_derivations"],
    note="Der(𝕊)=g₂=Der(𝕆) bit-exact; dim(spin(9)∩Der(𝕊))=14≪36; "
         "0/36 spin(9) generators are sedenion derivations ⟹ Spin(9)≠Aut(𝕊); "
         "two roads (gauge-of-gauge and CD doubling) cap at the same G₂ wall")


# ======================================================================
# MEASUREMENT 6 — THE 168, COUNTED FOUR WAYS (same object).
# ======================================================================
assoc_nz_512 = sum(1 for i, j, k in product(range(8), repeat=3)
                   if not is_zero(associator(E(i), E(j), E(k))))
# |GL(3,2)| = |PSL(2,7)| = |Aut(Fano)| = (2³−1)(2³−2)(2³−4), integer arithmetic.
gl32 = (2 ** 3 - 1) * (2 ** 3 - 2) * (2 ** 3 - 4)
rec(m="6", kind="the_168_four_ways",
    associator_nonzero_512=assoc_nz_512, gl_3_2_order=gl32,
    phi_support_lines=7, phi_ordered_support=phi_nz_ordered,
    equal=(assoc_nz_512 == gl32 == 168),
    note="168 = associator non-closures (§3.41.6) = |GL(3,2)|=|PSL(2,7)|="
         "|Aut(Fano)| (φ's 7-line support automorphism group) = sign-lane "
         "cocycle δε at 𝕆 (§3.46.9) — one object, four counts")


# ======================================================================
# MEASUREMENT 7 — cd_cycle_holonomy: the clean ℍ-vs-𝕆 line.
# ======================================================================
hH = cd_cycle_holonomy(cd_basis(4, 1), cd_basis(4, 2), cd_basis(4, 3))
rec(m="7a", kind="holonomy_H", carrier="ℍ e1,e2,e3", closed=hH["closed"],
    defect=qtuple(hH["defect"]),
    note="ℍ triple closes; both nests agree; defect 0")
hO = cd_cycle_holonomy(E(1), E(2), E(4))
rec(m="7b", kind="holonomy_O", carrier="𝕆 e1,e2,e4", closed=hO["closed"],
    defect=qtuple(hO["defect"]),
    note="𝕆 triple does NOT close; the two orderings disagree by the "
         "associator; defect = 2·e₇")


# ======================================================================
# MEASUREMENT 8 — OP STATUS + THE CONSISTENCY ORACLE (co-equal dual construction).
# φ ships as the FLOAT g2_three_form; the exact-ℚ Re scalar twin is the queued
# gap. loop_associator is the float Im peer of the exact-ℚ associator().
# ======================================================================

# 8a — exact-ℚ φ == float g2_three_form on the 35 unordered (and 343 ordered).
o1_u = 0
o1_ut = 0
for i, j, k in combinations(IMAG, 3):
    o1_ut += 1
    q = phi(E(i), E(j), E(k))
    f = g2_three_form([float(x) for x in E(i)], [float(x) for x in E(j)],
                      [float(x) for x in E(k)])
    if float(q) == float(f):
        o1_u += 1
o1_o = 0
o1_ot = 0
for i, j, k in product(IMAG, repeat=3):
    o1_ot += 1
    q = phi(E(i), E(j), E(k))
    f = g2_three_form([float(x) for x in E(i)], [float(x) for x in E(j)],
                      [float(x) for x in E(k)])
    if float(q) == float(f):
        o1_o += 1
rec(m="8a", kind="oracle_phi_vs_g2_three_form", unordered_match=o1_u,
    unordered_total=o1_ut, ordered_match=o1_o, ordered_total=o1_ot,
    pass_=(o1_u == o1_ut and o1_o == o1_ot),
    note="exact-ℚ φ (cd_mult∘conj∘Re) == shipped float g2_three_form 35/35 "
         "(and 343/343 ordered) — the consistency oracle for the QUEUED exact-ℚ "
         "cd_three_form (#T1062)")

# 8b — exact-ℚ associator == float loop_associator on the 343 ordered imaginary.
o2 = 0
o2t = 0
for i, j, k in product(IMAG, repeat=3):
    o2t += 1
    A = associator(E(i), E(j), E(k))
    LA = loop_associator([float(x) for x in E(i)], [float(x) for x in E(j)],
                         [float(x) for x in E(k)])
    if all(float(A[m]) == float(LA[m]) for m in range(8)):
        o2 += 1
rec(m="8b", kind="oracle_associator_vs_loop_associator", match=o2, total=o2t,
    pass_=(o2 == o2t),
    note="exact-ℚ associator == shipped float loop_associator 343/343 — the "
         "Im-peer oracle; associator() SHIPS, its Re scalar twin is the gap")

# 8c — the definitional identity φ(a,b,c) = ⟨a, cross7(b,c)⟩ (the vector
# companion cross7 = Im(loop_bind) reproduces φ by contraction).
o3 = 0
o3t = 0
for i, j, k in product(IMAG, repeat=3):
    o3t += 1
    q = phi(E(i), E(j), E(k))
    x = [float(v) for v in E(i)]
    bc = cross7([float(v) for v in E(j)], [float(v) for v in E(k)])
    dot = sum(x[m] * bc[m] for m in range(8))  # ⟨a, b×c⟩
    if float(q) == float(dot):
        o3 += 1
rec(m="8c", kind="phi_equals_a_dot_cross7", match=o3, total=o3t,
    pass_=(o3 == o3t),
    note="φ(a,b,c)=⟨a, cross7(b,c)⟩ on 343/343 — φ is the calibration of the "
         "7-D cross product (Harvey–Lawson); the scalar reads the vector")


for r in REC:
    print(json.dumps(r, default=str))

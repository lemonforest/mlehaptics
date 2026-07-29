#!/usr/bin/env python3
"""LANE 2 — does the shipped HV (Class-M) carrier carry the CD sign cochain?

THE CLAIM UNDER TEST
    "HDC bind IS XOR on labels, which IS the grading group operation of
     (Z/2)^d — so the HV representation natively carries the INDEX lane and
     structurally DROPS the sign cochain epsilon."

Everything measured here is measured with SHIPPED srmech ops as the SUBJECT:

    srmech.amsc.hdc.bind               (Class M, hdc.py:65)      - the BSC bind
    srmech.amsc.hdc.klein4_bind        (hdc.py:1426)             - the (F2)^2 bind
    srmech.amsc.hdc.polar_bind         (hdc.py:442)              - the sign-product bind
    srmech.amsc.hdc.hamming            (hdc.py:279)              - exact int distance
    srmech.amsc.cascade.chiral_flip    (atoms.py:383)            - Class C orientation
    srmech.signal_processing.mint_vector                         - Class A label mint
    cascade.cayley_dickson.cd_basis_product (cayley_dickson.py:560) - the CD cocycle
    srmech.amsc.modular_linalg.gf_rref (modular_linalg.py:173)   - GF(2) RREF

Hand-rolled code appears ONLY as an explicitly LABELLED ORACLE (the `_oracle_*`
functions) and never as the subject of a claim.

Exact integers / exact GF(2) throughout. No float, no numpy, no stdlib
fractions, no abs() (sign handling is an explicit table lookup - Class K pin-slot
+ Class C re-application, per [[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]).
"""
import json
import random

from srmech.amsc import hdc
from srmech.amsc import _native
from srmech.amsc.cascade import chiral_flip
from srmech.amsc.cascade.cayley_dickson import cd_basis_product
from srmech.amsc.modular_linalg import gf_rref
from srmech.signal_processing import mint_vector

OUT = []


def rec(**kw):
    OUT.append(kw)


D_BITS = 8192                       # hypervector width; 1024 bytes
NBYTES = D_BITS // 8
NAME = {1: "R", 2: "C", 4: "H", 8: "O", 16: "S(sedenion)", 32: "T(32)",
        64: "P(64)", 128: "(128)", 256: "(256)"}


# ── labelled ORACLES (never the subject of a claim) ───────────────────────
def _oracle_xor(a, b):
    return bytes(x ^ y for x, y in zip(a, b))


def _oracle_majority(vs):
    out = bytearray(len(vs[0]))
    for k in range(len(vs[0])):
        for bit in range(8):
            ones = sum((v[k] >> bit) & 1 for v in vs)
            if ones * 2 > len(vs):
                out[k] |= (1 << bit)
    return bytes(out)


def _oracle_perm_rotate(a, n):
    return bytes(a[(i + n) % len(a)] for i in range(len(a)))


# ══════════════════════════════════════════════════════════════════════════
# M1 - IS THE SHIPPED bind ACTUALLY XOR?  (if not, the whole claim dies)
# ══════════════════════════════════════════════════════════════════════════
rng = random.Random(20260729)
A = bytes(rng.randrange(256) for _ in range(NBYTES))
B = bytes(rng.randrange(256) for _ in range(NBYTES))
C = bytes(rng.randrange(256) for _ in range(NBYTES))
ZERO = bytes(NBYTES)

shipped_ab = hdc.bind(A, B)
rec(kind="M1_bind_is_xor",
    native_dispatch=bool(_native.HAS_NATIVE),
    equals_xor_oracle=(shipped_ab == _oracle_xor(A, B)),
    commutative=(hdc.bind(A, B) == hdc.bind(B, A)),
    associative=(hdc.bind(A, hdc.bind(B, C)) == hdc.bind(hdc.bind(A, B), C)),
    self_inverse=(hdc.bind(A, hdc.bind(A, B)) == B),
    bind_a_a_is_identity=(hdc.bind(A, A) == ZERO),
    identity_is_all_zero=(hdc.bind(A, ZERO) == A),
    # DISCRIMINATOR: the probe must reject the alternatives it claims to exclude
    differs_from_majority_oracle=(shipped_ab != _oracle_majority([A, B, C])),
    differs_from_rotate_oracle=(shipped_ab != _oracle_perm_rotate(A, 1)),
    differs_from_concat_of_a=(shipped_ab != A),
    note="bind is component-wise XOR: the (Z/2)^(8*nbytes) group operation")

# klein4_bind: the same XOR one rung up on the 2-bit (F2)^2 carrier
k4a = bytes(rng.randrange(4) for _ in range(64))
k4b = bytes(rng.randrange(4) for _ in range(64))
k4 = hdc.klein4_bind(k4a, k4b)
rec(kind="M1b_klein4_bind_is_f2sq_xor",
    equals_xor_oracle=(bytes(k4.tolist()) == _oracle_xor(k4a, k4b)),
    self_inverse=(bytes(hdc.klein4_bind(hdc.klein4_bind(k4a, k4b), k4a).tolist())
                  == k4b),
    alphabet_is_4=(k4.sectors == 4),
    note="klein4 is (F2)^2 per position - the Klein-four grading group")


# ══════════════════════════════════════════════════════════════════════════
# M2 - THE INDEX LANE IN THE HV CARRIER
#      Build labels as a bind-fold over d minted generators.  If bind is the
#      grading group op, then L(i) (+) L(j) == L(i XOR j) EXACTLY.
# ══════════════════════════════════════════════════════════════════════════
def make_labels(dim, tag="CDGEN"):
    d = dim.bit_length() - 1
    gens = [mint_vector(f"{tag}:g{b}", D=D_BITS) for b in range(d)]
    labels = []
    for k in range(dim):
        v = bytes(NBYTES)                     # XOR identity
        for b in range(d):
            if (k >> b) & 1:
                v = hdc.bind(v, gens[b])      # SHIPPED bind
        labels.append(v)
    return labels


LABELS = {}
for dim in (2, 4, 8, 16, 32, 64):
    L = make_labels(dim)
    LABELS[dim] = L
    viol = 0
    for i in range(dim):
        for j in range(dim):
            if hdc.bind(L[i], L[j]) != L[i ^ j]:
                viol += 1
    # injectivity: distinct indices must be distinct vectors (shipped hamming)
    min_sep = min(hdc.hamming(L[i], L[j])
                  for i in range(dim) for j in range(i + 1, dim))
    rec(kind="M2_index_lane_in_hv_carrier", dim=dim, algebra=NAME[dim],
        D_bits=D_BITS, pairs=dim * dim,
        grading_violations=viol,
        grading_exact=(viol == 0),
        min_pairwise_hamming=min_sep,
        labels_distinct=(min_sep > 0),
        note="L(i) bind L(j) == L(i XOR j) - the HV carrier IS (Z/2)^d")


# ══════════════════════════════════════════════════════════════════════════
# M3 - THE CD SIDE (shipped cd_basis_product)
# ══════════════════════════════════════════════════════════════════════════
EPS = {}                       # eps[dim][i][j] in {0,1};  sign = (-1)^eps
for dim in (2, 4, 8, 16, 32, 64):
    tab = [[0] * dim for _ in range(dim)]
    idx_viol = neg = 0
    for i in range(dim):
        for j in range(dim):
            k, s = cd_basis_product(dim, i, j)
            if k != (i ^ j):
                idx_viol += 1
            # Class-K pin-slot: read the orientation, no abs()
            tab[i][j] = 0 if s == 1 else 1
            neg += tab[i][j]
    EPS[dim] = tab
    rec(kind="M3_cd_index_and_sign", dim=dim, algebra=NAME[dim],
        pairs=dim * dim, index_is_xor_violations=idx_viol,
        negative_signs=neg, binom_dim_2=dim * (dim - 1) // 2,
        negatives_equal_binom=(neg == dim * (dim - 1) // 2))


# ══════════════════════════════════════════════════════════════════════════
# M4 - THE DIFFERENTIAL: CD product via the SHIPPED CD op
#      vs the SAME product via the SHIPPED HV bind on labels.
#      Route A: cd_basis_product -> (index, sign)
#      Route B: hdc.bind(L(i), L(j)) -> a vector, decoded against the codebook
# ══════════════════════════════════════════════════════════════════════════
for dim in (2, 4, 8, 16, 32, 64):
    L = LABELS[dim]
    book = {L[k]: k for k in range(dim)}
    idx_agree = idx_total = 0
    sign_lost = 0
    collapsed_pairs = []
    for i in range(dim):
        for j in range(dim):
            a_idx, a_sgn = cd_basis_product(dim, i, j)     # Route A (shipped)
            b_vec = hdc.bind(L[i], L[j])                   # Route B (shipped)
            b_idx = book.get(b_vec, -1)                    # decode
            idx_total += 1
            if b_idx == a_idx:
                idx_agree += 1
            if a_sgn == -1:
                # Route B emits the SAME bytes it would emit for +1: the sign
                # is not represented anywhere in the bound vector.
                sign_lost += 1
                if len(collapsed_pairs) < 4:
                    collapsed_pairs.append([i, j])
    rec(kind="M4_differential_cd_vs_hv_bind", dim=dim, algebra=NAME[dim],
        ordered_pairs=idx_total,
        index_agreements=idx_agree,
        index_lane_exact=(idx_agree == idx_total),
        sign_bits_dropped=sign_lost,
        drop_ratio=f"{sign_lost}/{idx_total}",
        binom_dim_2=dim * (dim - 1) // 2,
        equals_binom=(sign_lost == dim * (dim - 1) // 2),
        example_collapsed_pairs=collapsed_pairs,
        note="HV bind reproduces the index lane exactly and emits byte-identical "
             "output for the +1 and -1 cases - the epsilon support is the loss")


# ══════════════════════════════════════════════════════════════════════════
# M5 - IS THERE ANY SIGN CHANNEL IN THE SHIPPED HV CARRIER?
#      (a) the ANTIPODAL mask (complement) - composes under bind
#      (b) chiral_flip (Class C, atoms.py:383 = sequence reversal) - does NOT
#      (c) polar_bind (sign-product) - a genuine multiplicative sign channel
# ══════════════════════════════════════════════════════════════════════════
NU = bytes([0xFF] * NBYTES)                    # the BSC antipode (all-ones)
rec(kind="M5a_antipodal_channel_composes",
    antipode_is_involution=(hdc.bind(NU, hdc.bind(NU, A)) == A),
    two_antipodes_cancel=(hdc.bind(hdc.bind(A, NU), hdc.bind(B, NU))
                          == hdc.bind(A, B)),
    one_antipode_survives=(hdc.bind(hdc.bind(A, NU), B)
                           == hdc.bind(hdc.bind(A, B), NU)),
    note="XOR with the all-ones vector is a Z/2 that DOES compose under bind - "
         "a sign channel EXISTS in the BSC carrier")

flip_a = bytes(chiral_flip(list(A)))
mismatch = 0
for _ in range(64):
    x = bytes(rng.randrange(256) for _ in range(NBYTES))
    y = bytes(rng.randrange(256) for _ in range(NBYTES))
    lhs = hdc.bind(bytes(chiral_flip(list(x))), y)
    rhs = bytes(chiral_flip(list(hdc.bind(x, y))))
    if lhs != rhs:
        mismatch += 1
rec(kind="M5b_chiral_flip_is_not_a_bind_sign_channel",
    is_involution=(bytes(chiral_flip(list(flip_a))) == A),
    trials=64, non_equivariant_trials=mismatch,
    composes_under_bind=(mismatch == 0),
    note="chiral_flip is sequence REVERSAL (Class C), a permutation - it does "
         "NOT commute past bind, so it cannot act as the multiplicative sign. "
         "CDRegister therefore uses it as a CODEBOOK polarity, resolved by "
         "similarity at read time (cd_register.py:405/516), not as an algebraic "
         "channel that composes")

pa = hdc.polar_random(1024, seed=7)
pb = hdc.polar_random(1024, seed=8)
NEG = hdc.polar_from_real([-1.0] * 1024)       # the polar global-negation vector
rec(kind="M5c_polar_carrier_has_a_true_sign_channel",
    neg_is_all_minus_one=(list(NEG) == [-1] * 1024),
    neg_is_involution=(list(hdc.polar_bind(NEG, hdc.polar_bind(NEG, pa)))
                       == list(pa)),
    sign_pulls_through_bind=(list(hdc.polar_bind(hdc.polar_bind(NEG, pa), pb))
                             == list(hdc.polar_bind(NEG, hdc.polar_bind(pa, pb)))),
    two_signs_cancel=(list(hdc.polar_bind(hdc.polar_bind(NEG, pa),
                                          hdc.polar_bind(NEG, pb)))
                      == list(hdc.polar_bind(pa, pb))),
    note="polar_bind is the element-wise sign-product: a global negation IS a "
         "multiplicative Z/2 that composes. So 'no sign channel' is FALSE.")


# ══════════════════════════════════════════════════════════════════════════
# M6 - THE REAL OBSTRUCTION.  Give the HV carrier the antipodal channel and
#      the full gauge freedom (label e_k by L(k) or its antipode).  Then
#          bind(L'(i), L'(j)) == L'(i^j) (+) eps(i,j)*NU   for all i,j
#      iff  eps == delta t.   Solve THAT with the SHIPPED gf_rref.
# ══════════════════════════════════════════════════════════════════════════
def coboundary_system(dim, eps):
    """Rows = the (dim-1)^2 unital cells (i,j); columns = unknowns t_1..t_{dim-1};
    rhs = eps(i,j).  (delta t)(i,j) = t_i + t_j + t_{i^j} over GF(2)."""
    rows_A, rows_Ab = [], []
    for i in range(1, dim):
        for j in range(1, dim):
            row = [0] * (dim - 1)
            for k in (i, j, i ^ j):
                if k != 0:
                    row[k - 1] ^= 1
            rows_A.append(row)
            rows_Ab.append(row + [eps[i][j]])
    return rows_A, rows_Ab


def is_coboundary(dim, eps):
    """Consistency of delta t = eps, decided by the SHIPPED GF(2) RREF."""
    A_rows, Ab_rows = coboundary_system(dim, eps)
    rk_A = gf_rref(A_rows, 2)["rank"]
    rk_Ab = gf_rref(Ab_rows, 2)["rank"]
    return {"rank_A": rk_A, "rank_Ab": rk_Ab, "consistent": rk_A == rk_Ab}


for dim in (2, 4, 8, 16, 32, 64):
    r = is_coboundary(dim, EPS[dim])
    d = dim.bit_length() - 1
    rec(kind="M6_epsilon_is_not_a_coboundary_gf_rref", dim=dim, algebra=NAME[dim],
        cells=(dim - 1) ** 2, unknowns=dim - 1,
        rank_A=r["rank_A"], rank_Ab=r["rank_Ab"],
        rank_A_predicted=(dim - 1) - d,
        consistent=r["consistent"],
        epsilon_is_a_coboundary=r["consistent"],
        instrument="srmech.amsc.modular_linalg.gf_rref(rows, 2)",
        note="rank([A|b]) > rank(A) => NO assignment of antipodes to the HV "
             "labels can make bind reproduce the CD sign")


# ══════════════════════════════════════════════════════════════════════════
# M7 - THE DISCRIMINATOR.  Same instrument, three inputs:
#      (a) the SHIPPED epsilon        -> must be INCONSISTENT
#      (b) a synthetic pure coboundary -> must be CONSISTENT (and recoverable)
#      (c) the zero cochain            -> must be CONSISTENT
#      (d) a random cochain            -> control
#      An instrument that answers the same for (a) and (b) is not measuring
#      the cohomology class.
# ══════════════════════════════════════════════════════════════════════════
def delta_of(dim, t):
    return [[t[i] ^ t[j] ^ t[i ^ j] for j in range(dim)] for i in range(dim)]


ctrl_rng = random.Random(31415926)
for dim in (2, 4, 8, 16, 32):
    tau = [0] + [ctrl_rng.getrandbits(1) for _ in range(dim - 1)]
    cob = delta_of(dim, tau)
    zero = [[0] * dim for _ in range(dim)]
    rnd = [[0] * dim for _ in range(dim)]
    for i in range(1, dim):
        for j in range(1, dim):
            rnd[i][j] = ctrl_rng.getrandbits(1)
    rec(kind="M7_discriminator", dim=dim, algebra=NAME[dim],
        shipped_epsilon=is_coboundary(dim, EPS[dim]),
        synthetic_coboundary=is_coboundary(dim, cob),
        zero_cochain=is_coboundary(dim, zero),
        random_cochain=is_coboundary(dim, rnd),
        discriminates=(not is_coboundary(dim, EPS[dim])["consistent"]
                       and is_coboundary(dim, cob)["consistent"]
                       and is_coboundary(dim, zero)["consistent"]),
        note="the SAME gf_rref probe separates the shipped epsilon from a "
             "synthetic coboundary - it is measuring the class, not 'are there "
             "signs'")


# ══════════════════════════════════════════════════════════════════════════
# M8 - THE RESIDUAL, MEASURED IN THE ACTUAL HV CARRIER.
#      Exhaustive over all 2^(dim-1) antipodal gauges, every step through the
#      SHIPPED hdc.bind.  Confirms the number the arithmetic route gives.
# ══════════════════════════════════════════════════════════════════════════
def carrier_mismatches(dim, gauge_bits, eps):
    """Count ordered pairs where the SHIPPED bind on antipode-decorated labels
    disagrees with the CD product, decided by exact byte equality."""
    L = LABELS[dim]
    Lp = [hdc.bind(L[k], NU) if ((gauge_bits >> (k - 1)) & 1) else L[k]
          for k in range(1, dim)]
    Lp = [L[0]] + Lp                              # t_0 = 0 forced by unitality
    bad = 0
    for i in range(dim):
        for j in range(dim):
            got = hdc.bind(Lp[i], Lp[j])          # SHIPPED bind
            want = Lp[i ^ j]
            if eps[i][j]:
                want = hdc.bind(want, NU)         # SHIPPED bind for the sign
            if got != want:
                bad += 1
    return bad


for dim in (2, 4, 8):                             # exhaustive in the real carrier
    best, arg = None, None
    for g in range(1 << (dim - 1)):
        m = carrier_mismatches(dim, g, EPS[dim])
        if best is None or m < best:
            best, arg = m, g
    rec(kind="M8_carrier_exhaustive_gauge_search", dim=dim, algebra=NAME[dim],
        gauges_tried=1 << (dim - 1), ordered_pairs=dim * dim,
        min_mismatches=best, argmin_gauge_bits=arg,
        argmin_is_identity=(arg == 0),
        binom_dim_2=dim * (dim - 1) // 2,
        equals_binom=(best == dim * (dim - 1) // 2),
        instrument="srmech.amsc.hdc.bind (native)" if _native.HAS_NATIVE
                   else "srmech.amsc.hdc.bind (pure)",
        note="measured THROUGH the shipped HV carrier, not in arithmetic")

# the same search against a SYNTHETIC coboundary - the carrier MUST reach 0
for dim in (2, 4, 8):
    tau = [0] + [random.Random(1000 + dim).getrandbits(1) for _ in range(dim - 1)]
    cob = delta_of(dim, tau)
    best, arg = None, None
    for g in range(1 << (dim - 1)):
        m = carrier_mismatches(dim, g, cob)
        if best is None or m < best:
            best, arg = m, g
    recovered = [0] + [(arg >> (k - 1)) & 1 for k in range(1, dim)]
    rec(kind="M8b_carrier_control_synthetic_coboundary", dim=dim,
        min_mismatches=best, carrier_absorbs_it=(best == 0),
        recovered_gauge_equals_tau=(recovered == tau),
        note="NEGATIVE CONTROL: when the sign cochain IS a coboundary the HV "
             "carrier carries it perfectly (0 mismatches) and the antipode "
             "pattern recovers tau - so the C(dim,2) residual above is the "
             "COHOMOLOGY CLASS, not a limitation of the carrier")


for r in OUT:
    print(json.dumps(r, sort_keys=True))

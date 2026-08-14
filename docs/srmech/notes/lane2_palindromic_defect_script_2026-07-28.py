"""LANE 2 - RESONANT ASYMMETRIC PALINDROMY: define, then measure.

DEFINITION ADOPTED (and why).

A word is an ordered tuple of BASIS indices w = (i1..in), i_k in [0, dim).
Cayley-Dickson products are MONOMIAL: e_i . e_j = +-e_{i XOR j}. So ANY bracketing
of any word lands on the SAME basis element e_K, K = i1 XOR .. XOR in, and can
differ only in a SIGN. Therefore the palindromic defect cannot be an element and
cannot be a general ratio: it is FORCED to be a sign in {+1,-1}.

Non-associativity means a word needs a bracketing. Two candidate reversals:

  (a) BRACKET-PRESERVING  - leftfold(rev w) vs leftfold(w).       <- ADOPTED
  (b) BRACKET-MIRRORING   - rightfold(rev w) vs leftfold(w).

(b) IS the anti-automorphism: conj(leftfold w) = (-1)^m rightfold(rev w).
So (b) is by construction the conjugation sign and carries no new information.
We MEASURE that rather than assert it, then adopt (a).

  P(w) := s_L(w) * s_L(rev w)   in {+1,-1},  i.e.  leftfold(rev w) = P(w) leftfold(w)

PREDICTED DECOMPOSITION (derived, then tested cell-by-cell):
  P(w) = (-1)^m * eps_K * A(rev w)
    m     = number of IMAGINARY letters (i_k != 0)
    eps_K = +1 if K == 0 else -1                 (conjugation acting on e_K)
    A(u)  = s_L(u) * s_R(u), the ASSOCIATOR DEFECT sign of u -- exactly the
            object shipped genome_octonion_associator reads as a bit.
"""
import json, sys, random
from itertools import product, permutations, combinations, combinations_with_replacement

from srmech.amsc.cascade.cayley_dickson import (
    cd_basis_product, cd_mult, cd_conjugate, algebra_table)

OUT = []
def rec(**kw):
    OUT.append(kw)
    print(json.dumps(kw, sort_keys=True), flush=True)

NAME = {2: "C", 4: "H", 8: "O", 16: "S(sedenion)", 32: "T(trigintaduonion)"}
DIMS = (2, 4, 8, 16, 32)

# Sign table built FROM the shipped cd_basis_product (the subject stays the
# shipped op; this is memoisation, not a reimplementation).
SGN = {d: [[cd_basis_product(d, i, j)[1] for j in range(d)] for i in range(d)]
       for d in DIMS}
# and assert the index lane is XOR for every cell we will ride
_idx_bad = sum(1 for d in DIMS for i in range(d) for j in range(d)
               if cd_basis_product(d, i, j)[0] != (i ^ j))


def leftfold(dim, w):
    """((e_i1 . e_i2) . e_i3) ... -> (K, sign)."""
    t = SGN[dim]
    K, s = 0, 1
    for x in w:
        s *= t[K][x]
        K ^= x
    return K, s


def rightfold(dim, w):
    """e_i1 . (e_i2 . ( ... e_in)) -> (K, sign)."""
    t = SGN[dim]
    K, s = 0, 1
    for x in reversed(w):
        s *= t[x][K]
        K ^= x
    return K, s


def defect(dim, w):
    """The ADOPTED palindromic defect: bracket-preserving reversal."""
    return leftfold(dim, w)[1] * leftfold(dim, tuple(reversed(w)))[1]


def defect_antiauto(dim, w):
    """Convention (b): the anti-automorphism / bracket-mirroring reversal."""
    return leftfold(dim, w)[1] * rightfold(dim, tuple(reversed(w)))[1]


def trivial(dim, w):
    """(-1)^m * eps_K -- the pure conjugation sign."""
    m = sum(1 for x in w if x != 0)
    K = 0
    for x in w:
        K ^= x
    return (1 if m % 2 == 0 else -1) * (1 if K == 0 else -1)


def assoc_defect(dim, w):
    """A(w) = s_L(w)*s_R(w): the shipped associator-defect object, as a sign."""
    return leftfold(dim, w)[1] * rightfold(dim, w)[1]


# ---------------------------------------------------------------- step 0
# Verify the artifact under test: the memoised fold must agree with the real
# exact-Q cd_mult on unit vectors AND with the shipped algebra_table.
def unit(dim, i):
    v = [0] * dim
    v[i] = 1
    return v


mis_mult = mis_tab = n_mult = n_tab = 0
for dim in (2, 4, 8, 16):
    tab = algebra_table(dim)
    words = list(product(range(dim), repeat=3))
    for w in words:
        K, s = leftfold(dim, w)
        Kt, st = 0, 1
        for x in w:
            row = tab[Kt][x]
            nz = [k for k in range(dim) if row[k]]
            assert len(nz) == 1
            Kt, st = nz[0], st * row[nz[0]]
        n_tab += 1
        if (Kt, st) != (K, s):
            mis_tab += 1
    sample = words if dim <= 8 else random.Random(11).sample(words, 300)
    for w in sample:
        K, s = leftfold(dim, w)
        acc = unit(dim, w[0])
        for x in w[1:]:
            acc = cd_mult(acc, unit(dim, x))
        want = [0] * dim
        want[K] = s
        n_mult += 1
        if [int(c) for c in acc] != want:
            mis_mult += 1
rec(kind="artifact_check", vs_cd_mult_words=n_mult, vs_cd_mult_mismatches=mis_mult,
    vs_algebra_table_words=n_tab, vs_algebra_table_mismatches=mis_tab,
    xor_index_violations=_idx_bad,
    note="3-letter left-folded words, dims 2/4/8/16; cd_mult on exact-Q unit "
         "vectors (all words at dim<=8, 300 sampled at dim 16)")


# ---------------------------------------------------------------- step 0b
# Is convention (b) trivially the conjugation sign? (the definitional null)
bad = tot = 0
for dim in DIMS:
    for n in (2, 3, 4):
        for w in product(range(dim), repeat=n):
            tot += 1
            if defect_antiauto(dim, w) != trivial(dim, w):
                bad += 1
rec(kind="antiautomorphism_convention_is_trivial", words=tot,
    disagreements_with_conjugation_sign=bad,
    verdict="convention (b) IS the conjugation sign exactly" if bad == 0
            else "NOT trivial",
    note="all words length 2/3/4 over the FULL basis, dims 2..32; this is why "
         "convention (b) is rejected as the definition")


# ---------------------------------------------------------------- step 1+2
for dim in DIMS:
    for n in (2, 3, 4):
        for pool_name, pool in (("full_basis", list(range(dim))),
                                ("imaginary_only", list(range(1, dim)))):
            plus = minus = triv_mismatch = decomp_mismatch = 0
            for w in product(pool, repeat=n):
                P = defect(dim, w)
                if P == 1:
                    plus += 1
                else:
                    minus += 1
                T = trivial(dim, w)
                if P != T:
                    triv_mismatch += 1
                if P != T * assoc_defect(dim, tuple(reversed(w))):
                    decomp_mismatch += 1
            rec(kind="defect_census", algebra=NAME[dim], dim=dim, length=n,
                pool=pool_name, words=plus + minus, defect_plus=plus,
                defect_minus=minus, asymmetric=(plus != minus),
                words_where_defect_exceeds_conjugation_sign=triv_mismatch,
                decomposition_mismatches=decomp_mismatch,
                note="decomposition P = (-1)^m * eps_K * A(rev w); "
                     "mismatches must be 0")


# ---------------------------------------------------------------- step 1b
# The "4D BEAT": H length-4 imaginary words.
closed = openw = mismatch = 0
for w in product(range(1, 4), repeat=4):
    K, _ = leftfold(4, w)
    P = defect(4, w)
    if K == 0:
        closed += 1
    else:
        openw += 1
    if P != (1 if K == 0 else -1):
        mismatch += 1
rec(kind="H_4beat", algebra="H", dim=4, length=4, pool="imaginary_only",
    words=81, xor_closed_words=closed, xor_open_words=openw,
    defect_equals_xor_closure_mismatches=mismatch,
    note="at n=4 over imaginaries (-1)^m=+1 so P collapses to eps_K: a pure "
         "function of whether the word XOR-closes. Order plays NO role.")

ring = {str(i): [list(leftfold(4, (i,) * k)) for k in range(1, 9)] for i in (1, 2, 3)}
rec(kind="H_ringing_period", algebra="H", dim=4, powers_e1=ring["1"],
    period_4=all(tuple(ring[k][3]) == (0, 1) and tuple(ring[k][7]) == (0, 1)
                 for k in ring),
    note="e_i^4 = +e_0 for every H imaginary -- the measured period-4 ring")


# ---------------------------------------------------------------- step 3
# ORDER-CARRYING, on the SAME 35-set the associator was scored on.
for dim in (4, 8, 16):
    imags = list(range(1, dim))
    for r in (3, 4):
        n_sets = sep_defect = sep_assoc = 0
        for combo in combinations(imags, r):
            n_sets += 1
            perms = list(permutations(combo))
            if len({defect(dim, p) for p in perms}) > 1:
                sep_defect += 1
            if len({assoc_defect(dim, p) for p in perms}) > 1:
                sep_assoc += 1
        rec(kind="order_separation_palindromic", algebra=NAME[dim], dim=dim,
            subset_size=r, n_distinct_subsets=n_sets,
            order_sensitive_by_palindromic_defect=sep_defect,
            order_sensitive_by_associator=sep_assoc,
            palindromic_beats_associator=(sep_defect > sep_assoc),
            note="dim 8 r=3 is exactly #T961's C(7,3)=35 set")


# ---------------------------------------------------------------- step 3b
# Does the defect separate ANY two orderings of ANY multiset, anywhere?
for dim in (4, 8, 16, 32):
    for n in (2, 3, 4, 5):
        pool = list(range(1, dim))
        multisets = list(combinations_with_replacement(pool, n))
        if len(multisets) > 4000:
            multisets = random.Random(7).sample(multisets, 4000)
            exhaustive = False
        else:
            exhaustive = True
        sep = 0
        for w in multisets:
            if len({defect(dim, p) for p in set(permutations(w))}) > 1:
                sep += 1
        rec(kind="order_separation_multisets", algebra=NAME[dim], dim=dim,
            length=n, n_multisets=len(multisets), exhaustive=exhaustive,
            order_sensitive=sep,
            note="every multiset of imaginary letters, all distinct orderings")


# ---------------------------------------------------------------- step 4
# PROMOTION: does the defect survive the CD doubling chain (#T971's claim)?
changed = same = 0
examples = []
for n in (2, 3, 4):
    for w in product(range(4), repeat=n):
        vals = [defect(d, w) for d in (4, 8, 16, 32)]
        if len(set(vals)) == 1:
            same += 1
        else:
            changed += 1
            if len(examples) < 3:
                examples.append({"word": list(w), "defects_4_8_16_32": vals})
rec(kind="promotion_H_into_chain", words=same + changed, invariant=same,
    changed=changed, examples=examples,
    note="H words embedded e_i -> e_i into O, S, T; defect recomputed in each")

for dim in DIMS:
    for n in (3, 4, 5):
        pool = list(range(1, dim))
        allw = product(pool, repeat=n)
        cap = 400000
        tot = nontriv = 0
        exhaustive = (dim - 1) ** n <= cap
        rng = random.Random(3)
        for w in allw:
            if not exhaustive and rng.random() > cap / ((dim - 1) ** n):
                continue
            tot += 1
            if defect(dim, w) != trivial(dim, w):
                nontriv += 1
        rec(kind="nontrivial_content_by_dim", algebra=NAME[dim], dim=dim,
            length=n, words=tot, exhaustive=exhaustive,
            words_beyond_conjugation_sign=nontriv,
            fraction_nontrivial=(0 if tot == 0 else round(nontriv / tot, 6)),
            note="nonzero only where the ASSOCIATOR of the reversed word fires")

with open(sys.argv[1], "w", encoding="utf-8") as fh:
    for r in OUT:
        fh.write(json.dumps(r, sort_keys=True) + "\n")
print("\nwrote", len(OUT), "records", flush=True)

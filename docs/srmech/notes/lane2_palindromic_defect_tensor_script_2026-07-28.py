"""LANE 2 step 4b - does the palindromic defect survive the TENSOR chain?

#T971 is reported to record "palindrome CONFIRMED to survive the tensor chain".
Two readings of "tensor chain"; both are tested here rather than inherited.

  (i)  the CD DOUBLING chain  H -> O -> S -> T   (tested in lane2_palindromy.py)
  (ii) the Furey TENSOR chain R (x) C (x) H (x) O

For (ii): in A (x) B the basis is e_i (x) f_j and
    (e_i (x) f_j)(e_k (x) f_l) = s_A(i,k) s_B(j,l) . e_{i^k} (x) f_{j^l}
so the product is STILL monomial and the defect is STILL a sign. The question
is whether it carries anything the factors did not.
"""
import json, sys
from itertools import product, permutations, combinations

from srmech.amsc.cascade.cayley_dickson import cd_basis_product

OUT = []
def rec(**kw):
    OUT.append(kw)
    print(json.dumps(kw, sort_keys=True), flush=True)

NAME = {1: "R", 2: "C", 4: "H", 8: "O"}
SGN = {d: [[cd_basis_product(d, i, j)[1] for j in range(d)] for i in range(d)]
       for d in (1, 2, 4, 8)}


def fold_factor(dim, letters, right=False):
    t = SGN[dim]
    K, s = 0, 1
    seq = reversed(letters) if right else letters
    for x in seq:
        s *= (t[x][K] if right else t[K][x])
        K ^= x
    return K, s


def tensor_defect(dims, word):
    """word = tuple of tuples, one component per tensor factor."""
    fwd = 1
    rev = 1
    for f, d in enumerate(dims):
        letters = [w[f] for w in word]
        fwd *= fold_factor(d, letters)[1]
        rev *= fold_factor(d, list(reversed(letters)))[1]
    return fwd * rev


def factor_defect(dim, letters):
    return fold_factor(dim, letters)[1] * fold_factor(dim, list(reversed(letters)))[1]


# ---- multiplicativity: P_{A(x)B}(w) = P_A(w_A) * P_B(w_B) ?
for dims in [(2, 4), (4, 8), (2, 4, 8), (1, 2, 4, 8)]:
    bad = tot = 0
    nontriv = 0
    for n in (2, 3):
        pools = [range(d) for d in dims]
        for word in product(product(*pools), repeat=n):
            tot += 1
            got = tensor_defect(dims, word)
            want = 1
            for f, d in enumerate(dims):
                want *= factor_defect(d, [w[f] for w in word])
            if got != want:
                bad += 1
            if got != 1:
                nontriv += 1
    rec(kind="tensor_multiplicativity",
        chain=" (x) ".join(NAME[d] for d in dims), dims=list(dims),
        words=tot, multiplicativity_violations=bad,
        defect_minus_words=nontriv,
        note="P over a tensor product is the PRODUCT of the per-factor defects")


# ---- where does NON-TRIVIAL (beyond-conjugation) content live in the chain?
def trivial_factor(dim, letters):
    m = sum(1 for x in letters if x != 0)
    K = 0
    for x in letters:
        K ^= x
    return (1 if m % 2 == 0 else -1) * (1 if K == 0 else -1)


for dim in (1, 2, 4, 8):
    for n in (3, 4):
        tot = nontriv = 0
        for letters in product(range(dim), repeat=n):
            tot += 1
            if factor_defect(dim, letters) != trivial_factor(dim, letters):
                nontriv += 1
        rec(kind="tensor_chain_factor_content", algebra=NAME[dim], dim=dim,
            length=n, words=tot, words_beyond_conjugation_sign=nontriv,
            note="which FACTOR of R (x) C (x) H (x) O supplies non-trivial "
                 "palindromic content")


# ---- ORDER-carrying inside the full chain: does the tensor defect separate
#      orderings that the per-factor associator cannot?
def assoc_factor(dim, letters):
    return fold_factor(dim, letters)[1] * fold_factor(dim, letters, right=True)[1]


for dims in [(2, 4), (4, 8), (1, 2, 4, 8)]:
    pools = [list(range(1, d)) if d > 1 else [0] for d in dims]
    alphabet = list(product(*pools))
    n_sets = sep_defect = sep_assoc = 0
    for combo in combinations(alphabet, 3):
        n_sets += 1
        perms = list(permutations(combo))
        if len({tensor_defect(dims, p) for p in perms}) > 1:
            sep_defect += 1
        a = set()
        for p in perms:
            v = 1
            for f, d in enumerate(dims):
                v *= assoc_factor(d, [w[f] for w in p])
            a.add(v)
        if len(a) > 1:
            sep_assoc += 1
    rec(kind="tensor_order_separation",
        chain=" (x) ".join(NAME[d] for d in dims), dims=list(dims),
        n_distinct_triples=n_sets,
        order_sensitive_by_palindromic_defect=sep_defect,
        order_sensitive_by_associator=sep_assoc,
        palindromic_beats_associator=(sep_defect > sep_assoc),
        note="triples of imaginary tensor-basis letters, all 6 orderings")

with open(sys.argv[1], "w", encoding="utf-8") as fh:
    for r in OUT:
        fh.write(json.dumps(r, sort_keys=True) + "\n")
print("\nwrote", len(OUT), "records", flush=True)

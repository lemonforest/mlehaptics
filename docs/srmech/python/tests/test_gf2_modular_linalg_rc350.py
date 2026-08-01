"""GF(2) is in domain for ``gf_rref`` — srmech 0.9.0rc350, task `#T1003`.

WHY THIS EXISTS
===============
From rc44 to rc349 ``modular_linalg.gf_rref`` refused ``p = 2``::

    if p <= 2 or p >= _P_CEILING:
        raise ValueError("gf_rref: p must be an odd prime with 2 < p < 2**31")

The word "odd" reads like a scope decision, and it was not one. The rc44 C
kernel inverted a pivot by **Fermat** (a private ``a**(p-2) mod p``), and the C
guard's own comment gave the reason as *"so a*b fits uint64 AND Fermat inversion
is valid"*. rc49 replaced that private power with the extended-Euclidean
``srmech_mod_inv`` — which dissolved the Fermat half of the rationale — and the
bound was simply never revisited. Only the **ceiling** (``p < 2**31``, so ``a*b``
fits one uint64) was ever an arithmetic-domain fact.

Characteristic 2 is the *easy* end of the field range, not an excluded one: the
only nonzero element is 1, so the pivot normalisation is ``1⁻¹ = 1`` (no
division at all) and the elimination row op is XOR.

WHY IT MATTERS — GF(2) IS THE GRADING FIELD OF THE WHOLE CD LADDER
==================================================================
``cascade.cayley_dickson.cd_basis_product`` sends ``e_i · e_j`` to index
``i ⊕ j`` at every rung in ``CD_DIMS``. The index lane of ℂ / ℍ / 𝕆 / 𝕊 / … IS
``(ℤ/2)^d``, so questions about it are GF(2) linear algebra — and srmech's only
finite-field elimination refused the field they live in.

``test_sedenion_zero_divisors_*`` below is the payoff: the sedenion
zero-divisor **support** condition is a single GF(2) affine system, solved
through the shipped ``gf_rref``, after which the sign is *determined* rather
than searched. Zero divisors are measure-zero in 𝕊 — a random sample of 300
dim-16 elements returns 300/300 left-multiplication-invertible (measured in
``test_random_sampling_cannot_find_a_sedenion_zero_divisor``) — so no sampling
op can find them. The GF(2) solve finds **all 168** of them, exactly.

SUBJECT DISCIPLINE
==================
The subject of every test here is the SHIPPED ``srmech.math.modular_linalg
.gf_rref`` (native-dispatched when ``HAS_NATIVE``). The two hand-rolled
reference implementations are named ``*_oracle`` and are never the subject.
"""

from __future__ import annotations

import random
import time

import pytest

from srmech.amsc import _native
from srmech.math import modular_linalg as ml
from srmech.amsc.cyclic import mod_inv
from srmech.amsc.cascade.cayley_dickson import (
    CD_DIMS,
    cd_basis_product,
    cd_mult,
    left_mult_is_invertible,
    sedenion_zero_divisor_witness,
)
from srmech.math.modular_linalg import gf_rref


# ──────────────────────────────────────────────────────────────────────────
# ORACLES — never the subject of a test.
# ──────────────────────────────────────────────────────────────────────────

def _gf2_rref_oracle(rows):
    """ORACLE ONLY — reduced row echelon over GF(2) written the char-2 way:
    bits and XOR, with no modulus, no ``mod_inv``, no ``mod_mul``, and no
    reference to ``p`` at all.

    Deliberately NOT the subject of any test. It shares no code path with
    ``gf_rref`` (which composes the Class-I modular primitives over a general
    ``p``), so agreement between the two is real evidence and not a tautology.
    Returns ``(matrix, pivots, rank)``.
    """
    m = [[v & 1 for v in row] for row in rows]
    n_rows = len(m)
    n_cols = len(m[0]) if n_rows else 0
    pivots = []
    pivot_row = 0
    for col in range(n_cols):
        if pivot_row >= n_rows:
            break
        sel = next((r for r in range(pivot_row, n_rows) if m[r][col]), None)
        if sel is None:
            continue
        m[pivot_row], m[sel] = m[sel], m[pivot_row]
        for r in range(n_rows):
            if r != pivot_row and m[r][col]:
                m[r] = [a ^ b for a, b in zip(m[r], m[pivot_row])]
        pivots.append(col)
        pivot_row += 1
    return m, pivots, pivot_row


def _basis_pair(dim, i, j, k, l, s):
    """Build the element pair ``(e_i + e_j, e_k + s·e_l)`` as plain dim-length
    integer vectors — a shape helper, not an oracle."""
    x = [0] * dim
    y = [0] * dim
    x[i] += 1
    x[j] += 1
    y[k] += 1
    y[l] += s
    return x, y


# ──────────────────────────────────────────────────────────────────────────
# The guard itself.
# ──────────────────────────────────────────────────────────────────────────

def test_gf_rref_accepts_p_equals_2():
    """The rc350 (`#T1003`) widening: GF(2) is in domain. Over GF(2) the matrix
    [[1,1],[1,0]] reduces to the identity — hand-checkable, no oracle needed."""
    out = gf_rref([[1, 1], [1, 0]], 2)
    assert out == {"rref": [[1, 0], [0, 1]], "rank": 2, "pivots": [0, 1]}


@pytest.mark.parametrize("p", [1, 0, -1, -2, 1 << 31, (1 << 31) + 1])
def test_gf_rref_still_rejects_out_of_domain_p(p):
    """Widening the LOWER bound to 2 must not have opened anything else. The
    ceiling (``a*b`` inside one uint64) is untouched, and ``p < 2`` is not a
    field."""
    with pytest.raises(ValueError):
        gf_rref([[1, 0], [0, 1]], p)


def test_gf_rref_rejects_non_int_p():
    for bad in (2.0, "2", True, None):
        with pytest.raises(TypeError):
            gf_rref([[1, 0], [0, 1]], bad)


def test_error_message_no_longer_says_odd():
    """The old message asserted a fact about the field that was never true —
    GF(2) is a field. Guard the corrected wording so it cannot silently
    regress."""
    with pytest.raises(ValueError) as exc:
        gf_rref([[1]], 1)
    text = str(exc.value)
    assert "odd" not in text
    assert "2 <= p < 2**31" in text


# ──────────────────────────────────────────────────────────────────────────
# The odd-`p` hazard audit. Char 2 is SIMPLER than odd p, so the hazards run
# the other way: code written for odd p may assume a != -a, may divide by a
# pivot, or may use (p+1)//2 as the inverse of 2. Each is probed directly.
# ──────────────────────────────────────────────────────────────────────────

def test_hazard_pivot_inverse_is_one_in_char_2():
    """``gf_rref`` normalises a pivot row by ``mod_inv(pivot, p)``. In GF(2) the
    only invertible element is 1 and ``1⁻¹ = 1``, so the shipped Class-I
    primitive must answer 1 — if it raised, the pivot step would be the odd-p
    assumption."""
    assert mod_inv(1, 2) == 1


def test_hazard_a_equals_minus_a_in_char_2():
    """In GF(2) ``a == -a``, so "subtract the pivot row" and "add the pivot row"
    are the same operation. A kernel that distinguished them (e.g. by negating
    into ``[1, p)`` and assuming that range is nonempty for the negation of 1)
    would diverge here. Two identical rows must reduce to one pivot and a zero
    row, not to a doubled row."""
    out = gf_rref([[1, 1, 0], [1, 1, 0]], 2)
    assert out["rank"] == 1
    assert out["rref"] == [[1, 1, 0], [0, 0, 0]]


def test_hazard_two_is_zero_not_a_unit():
    """``(p+1)//2`` is the standard closed form for ``2⁻¹`` at odd ``p`` and is
    nonsense at ``p = 2`` (it yields 1, but 2 ≡ 0 has no inverse). If any such
    idiom were in the path, a matrix whose only entry is 2 would come back
    rank 1 instead of rank 0."""
    assert gf_rref([[2]], 2) == {"rref": [[0]], "rank": 0, "pivots": []}
    assert gf_rref([[2, 4], [6, 8]], 2)["rank"] == 0
    # …and 2 IS a unit at p = 3, so the same matrix is rank 1 there. This is the
    # discriminator: the p=2 answer above is a real char-2 fact, not a stub.
    assert gf_rref([[2]], 3) == {"rref": [[1]], "rank": 1, "pivots": [0]}


def test_hazard_negative_entries_canonicalise_in_char_2():
    """Entries are reduced into ``[0, p)`` first; at ``p = 2`` that maps every
    odd integer (of either sign) to 1 and every even one to 0."""
    out = gf_rref([[-1, -2, -3], [4, -5, 6]], 2)
    assert out["rref"][0][0] == 1
    assert all(v in (0, 1) for row in out["rref"] for v in row)
    oracle, _, _ = _gf2_rref_oracle([[-1, -2, -3], [4, -5, 6]])
    assert out["rref"] == oracle


# ──────────────────────────────────────────────────────────────────────────
# Correctness sweep + native/pure parity at p = 2.
# ──────────────────────────────────────────────────────────────────────────

def test_gf_rref_matches_the_xor_oracle_over_random_matrices_at_p_2():
    """The shipped op vs an independent XOR-only oracle across shapes,
    including rank-deficient and all-even (rank-0 mod 2) matrices."""
    rng = random.Random(1003)
    checked = 0
    for shape in [(1, 1), (2, 2), (3, 3), (3, 5), (5, 3), (4, 7), (6, 6), (8, 4)]:
        n_rows, n_cols = shape
        for _ in range(120):
            rows = [[rng.randint(-6, 6) for _ in range(n_cols)]
                    for _ in range(n_rows)]
            got = gf_rref(rows, 2)
            exp_m, exp_p, exp_r = _gf2_rref_oracle(rows)
            assert got["rref"] == exp_m, rows
            assert got["pivots"] == exp_p, rows
            assert got["rank"] == exp_r, rows
            checked += 1
    assert checked == 960


def test_native_and_pure_are_byte_identical_at_p_2():
    """ADR-0009: the projections are co-equal, so the C peer and the pure body
    must agree at ``p = 2`` exactly as they do at every odd prime. Skipped
    (loudly) when no native library is loaded, rather than passing vacuously."""
    if not _native.has_native_gf_rref():
        pytest.skip("no native srmech_gf_rref loaded — parity untestable here")
    rng = random.Random(350)
    for _ in range(200):
        n_rows = rng.randint(1, 6)
        n_cols = rng.randint(1, 6)
        rows = [[rng.randint(-4, 4) for _ in range(n_cols)]
                for _ in range(n_rows)]
        flat = [v for row in rows for v in row]
        native = ml._gf_rref_c(flat, n_rows, n_cols, 2)
        assert native is not None, "native path refused p = 2"
        n_flat, n_piv, n_rank = native
        n_mat = [n_flat[r * n_cols:(r + 1) * n_cols] for r in range(n_rows)]
        p_mat, p_piv, p_rank = ml._gf_rref_pure(rows, n_rows, n_cols, 2)
        assert (n_mat, n_piv, n_rank) == (p_mat, p_piv, p_rank), rows


def test_odd_prime_behaviour_is_unchanged():
    """The widening must be additive: every ``p`` accepted before is accepted
    now, with identical output."""
    rows = [[2, 4, 6, 1], [3, 5, 7, 0], [0, 0, 11, 13]]
    assert gf_rref(rows, 3)["rank"] == 3
    assert gf_rref(rows, 7)["rref"][0][0] == 1
    assert gf_rref(rows, 2147483647)["rank"] == 3
    for p in (3, 5, 7, 101, 65537, 2147483647):
        out = gf_rref(rows, p)
        assert all(0 <= v < p for row in out["rref"] for v in row)
        assert out["pivots"] == sorted(set(out["pivots"]))


# ──────────────────────────────────────────────────────────────────────────
# WHAT THIS UNLOCKS — the CD index lane is (ℤ/2)^d, so it is gf_rref's domain.
# ──────────────────────────────────────────────────────────────────────────

def _support_solutions_via_gf_rref(d, n_bits):
    """All ``(k, l)`` with ``k ⊕ l = d``, obtained by SOLVING the affine GF(2)
    system ``[I | I | d]`` through the shipped ``gf_rref`` — not by enumerating
    pairs and filtering.

    The unknowns are the ``n_bits`` bits of ``k`` followed by the ``n_bits``
    bits of ``l``; row ``b`` is ``k_b + l_b = d_b (mod 2)``. ``gf_rref``
    returns the RREF, its rank and its pivot columns; the free columns
    parametrise the affine solution set, which is read back by
    back-substitution from that RREF.
    """
    n_unk = 2 * n_bits
    rows = []
    for b in range(n_bits):
        row = [0] * (n_unk + 1)
        row[b] = 1
        row[n_bits + b] = 1
        row[n_unk] = (d >> b) & 1
        rows.append(row)

    out = gf_rref(rows, 2)                       # ← the subject
    rref, pivots, rank = out["rref"], out["pivots"], out["rank"]
    assert rank == n_bits, "k ⊕ l = d is n_bits independent GF(2) equations"

    free = [c for c in range(n_unk) if c not in pivots]
    solutions = []
    for mask in range(1 << len(free)):
        x = [0] * n_unk
        for t, c in enumerate(free):
            x[c] = (mask >> t) & 1
        for row_i, pivot_col in enumerate(pivots):   # back-substitute
            acc = rref[row_i][n_unk]
            for c in free:
                acc ^= rref[row_i][c] & x[c]
            x[pivot_col] = acc
        k = sum(bit << b for b, bit in enumerate(x[:n_bits]))
        l = sum(bit << b for b, bit in enumerate(x[n_bits:]))
        solutions.append((k, l))
    return solutions, rank, len(free)


def _zero_divisor_witnesses_via_gf2(dim):
    """Every basis-pair zero divisor ``(e_i + e_j)·(e_k + s·e_l) = 0`` of the
    Cayley–Dickson algebra of dimension ``dim``, found with NO search over the
    sign and NO search over ``(k, l)``.

    Derivation. ``e_a·e_b = σ(a,b)·e_{a⊕b}``, so the product expands to four
    terms with indices ``i⊕k, i⊕l, j⊕k, j⊕l``. With ``i ≠ j`` and ``k ≠ l`` the
    only pairing that can cancel is ``i⊕k = j⊕l`` together with
    ``i⊕l = j⊕k`` — both are the single GF(2) condition

        i ⊕ j ⊕ k ⊕ l = 0,   i.e.   k ⊕ l = i ⊕ j.

    That is the affine system solved by ``_support_solutions_via_gf_rref``.
    Given a surviving support, the first pair cancels iff
    ``σ(i,k) + s·σ(j,l) = 0``, so ``s = -σ(i,k)·σ(j,l)`` is **determined**; the
    witness is admitted iff the second pair then also cancels.

    Returns ``(witnesses, n_candidates)``.
    """
    n_bits = dim.bit_length() - 1
    witnesses = []
    n_candidates = 0
    for i in range(1, dim):
        for j in range(i + 1, dim):
            supports, _rank, _free = _support_solutions_via_gf_rref(i ^ j, n_bits)
            for (k, l) in supports:
                if k == 0 or l == 0 or k >= l:
                    continue                      # e_0 = 1; (k,l) unordered
                n_candidates += 1
                _, s_ik = cd_basis_product(dim, i, k)
                _, s_jl = cd_basis_product(dim, j, l)
                _, s_il = cd_basis_product(dim, i, l)
                _, s_jk = cd_basis_product(dim, j, k)
                s = -s_ik * s_jl                  # DETERMINED, not searched
                if s * s_il + s_jk == 0:
                    witnesses.append((i, j, k, l, s))
    return witnesses, n_candidates


def test_cd_index_lane_is_gf2_at_every_shipped_rung():
    """The premise of the whole section: ``e_i · e_j`` lands on index ``i ⊕ j``
    at every rung srmech ships, so the CD index lane is ``(ℤ/2)^d``."""
    for dim in CD_DIMS:
        if dim < 2 or dim > 16:                  # exhaustive over the cheap rungs
            continue
        for i in range(dim):
            for j in range(dim):
                idx, sign = cd_basis_product(dim, i, j)
                assert idx == (i ^ j), (dim, i, j, idx)
                assert sign in (1, -1)


def test_support_condition_is_an_affine_gf2_solve():
    """``k ⊕ l = 11`` over ``(ℤ/2)^4``: rank 4, four free variables, and the
    solution set is exactly the 16 pairs with that XOR — read out of the RREF
    ``gf_rref`` returned, never enumerated-and-filtered."""
    sols, rank, n_free = _support_solutions_via_gf_rref(11, 4)
    assert (rank, n_free) == (4, 4)
    assert len(sols) == 16 == len(set(sols))
    assert all((k ^ l) == 11 for k, l in sols)
    assert (4, 15) in sols                       # the shipped witness's support


def test_sedenion_zero_divisors_found_by_gf2_solve_all_annihilate():
    """Every witness the GF(2) criterion emits is a genuine zero divisor under
    the shipped ``cd_mult`` — no false positives."""
    witnesses, n_candidates = _zero_divisor_witnesses_via_gf2(16)
    assert len(witnesses) == 168
    assert n_candidates == 735
    for (i, j, k, l, s) in witnesses:
        x, y = _basis_pair(16, i, j, k, l, s)
        assert any(v != 0 for v in x) and any(v != 0 for v in y)
        assert all(c == 0 for c in cd_mult(x, y)), (i, j, k, l, s)


def test_gf2_criterion_reproduces_the_shipped_hardwired_witness():
    """``sedenion_zero_divisor_witness()`` is hardwired precisely because
    sampling cannot find one. The GF(2) construction must contain it."""
    w = sedenion_zero_divisor_witness()
    assert (w["x_form"], w["y_form"]) == ("e1 + e10", "e4 - e15")
    witnesses, _ = _zero_divisor_witnesses_via_gf2(16)
    assert (1, 10, 4, 15, -1) in set(witnesses)


def test_gf2_criterion_is_exact_against_brute_force_on_a_subset():
    """No false NEGATIVES either. Brute force over a deterministic subset of
    ``(i, j)`` pairs — every ``(k, l, s)`` tested with the shipped ``cd_mult``
    — must return exactly the criterion's answer restricted to that subset.

    (The subset is a runtime bound, not a hedge: the full 22050-product sweep
    was run out-of-band at rc350 and agreed on all 105 pairs, 168 witnesses,
    set-equal. It takes ~27 s versus the criterion's ~0.06 s, which is the
    other half of the point.)
    """
    dim = 16
    subset = [(1, 10), (2, 5), (3, 12), (6, 9), (7, 14), (11, 13)]
    criterion, _ = _zero_divisor_witnesses_via_gf2(dim)
    criterion_subset = {w for w in criterion if (w[0], w[1]) in subset}

    brute = set()
    for (i, j) in subset:
        x = [0] * dim
        x[i] += 1
        x[j] += 1
        for k in range(1, dim):
            for l in range(k + 1, dim):
                for s in (1, -1):
                    y = [0] * dim
                    y[k] += 1
                    y[l] += s
                    if all(c == 0 for c in cd_mult(x, y)):
                        brute.add((i, j, k, l, s))
    assert brute == criterion_subset
    assert len(brute) > 0, "subset must actually contain witnesses"


@pytest.mark.parametrize("dim,expect_candidates", [(4, 3), (8, 63)])
def test_negative_control_division_algebras_yield_no_witnesses(
        dim, expect_candidates):
    """NEGATIVE CONTROL. ℍ and 𝕆 are division algebras, so the identical GF(2)
    criterion — same support solve, same determined sign — must return the
    EMPTY set. The candidate count is pinned so the control cannot pass
    vacuously: the support system IS satisfiable at these rungs (the index lane
    is ``(ℤ/2)^d`` regardless of dimension), and it is the sign condition that
    never closes below dim 16. Without this the dim-16 result would not be
    evidence of anything.

    (ℂ is excluded deliberately, not by oversight: dim 2 has a single imaginary
    unit ``e_1``, so there is no ``e_i + e_j`` at all and the criterion's domain
    is empty — see the companion test below.)"""
    witnesses, n_candidates = _zero_divisor_witnesses_via_gf2(dim)
    assert n_candidates == expect_candidates
    assert witnesses == []


def test_complex_rung_has_no_basis_pair_to_test():
    """ℂ's degeneracy stated outright rather than hidden behind a zero count:
    with one imaginary unit there is no two-term basis element, so the GF(2)
    criterion has nothing to range over at dim 2."""
    witnesses, n_candidates = _zero_divisor_witnesses_via_gf2(2)
    assert (witnesses, n_candidates) == ([], 0)


def test_random_sampling_cannot_find_a_sedenion_zero_divisor():
    """The measured limitation that makes the GF(2) route necessary rather than
    merely faster: zero divisors are measure-zero in 𝕊, so a sampling op finds
    none. 300 random dim-16 elements, all left-multiplication-invertible."""
    rng = random.Random(7)
    invertible = 0
    trials = 300
    for _ in range(trials):
        v = [rng.randint(-9, 9) for _ in range(16)]
        if not any(v):
            v[0] = 1
        if left_mult_is_invertible(v):
            invertible += 1
    assert invertible == trials, (
        f"{trials - invertible}/{trials} random sedenions were singular — if "
        "this ever fires, sampling DOES reach the zero-divisor locus and the "
        "framing above needs revisiting"
    )


def test_gf2_criterion_is_cheaper_than_the_brute_force_it_replaces():
    """The candidate-space collapse, measured rather than asserted: the GF(2)
    solve narrows 22050 (i,j,k,l,s) products to 735 sign-free candidates — a
    30× cut — and finds the same 168 witnesses."""
    _witnesses, n_candidates = _zero_divisor_witnesses_via_gf2(16)
    n_pairs = (15 * 14) // 2                     # unordered (i,j) from e_1..e_15
    brute_force_products = n_pairs * n_pairs * 2  # × (k,l) pairs × the two signs
    assert brute_force_products == 22050
    assert n_candidates == 735
    assert brute_force_products // n_candidates == 30

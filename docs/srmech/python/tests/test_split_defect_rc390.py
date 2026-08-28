"""rc390 (`#T961`) — the ratchet for ``srmech.biology.genome.split_defect``, the
ORDER-carrying octonion associativity read.

This is the FALSE-GREEN CATCHER. ``split_defect == 0`` is AMBIGUOUS — it means
EITHER the re-bracketing preserved the sign (associative) OR the word is too short
at ``k`` to fire. A test that only checked "some word gives 0" would pass on a
broken op that ALWAYS returns 0. So the census below pins BOTH the associative
zeros AND the non-associative nonzeros, the threshold is made visible (a firing
case AND a structurally-cannot-fire case), and split-𝕆 is pinned to prove the op
reads ASSOCIATIVITY, not the division property.

The enumeration reproduced (all EXACT, through the shipped ops):
  ℂ 0/1 · ℍ 0/81 · 𝕆 1008/2401 (all length-4 words, k=2) · 𝕊 18480/32760
  (distinct-letter length-4 words, the non-division rung).

No ``abs()`` (sign is the Class-K pin bit ``b>>3``, re-applied by the Class-C XOR);
no stdlib ``fractions`` (integer byte ops). The test is numpy-free.
"""
from __future__ import annotations

from itertools import product, permutations

import pytest

from srmech import _native
from srmech.biology import genome
from srmech.biology.genome import split_defect
from srmech.math.octonion import oct_mult
from srmech.cascade.cayley_dickson import cd_basis_product, algebra_table
from srmech.introspect.tool_schema import get_tool_schema
from tests._native_gate import require_native


# ── reference folds (through shipped ops) ────────────────────────────────────
def _bp_cd(dim):
    return lambda i, j: cd_basis_product(dim, i, j)


def _bp_table(dim, gammas):
    tbl = algebra_table(dim, gammas)
    def bp(i, j):
        for k, c in enumerate(tbl[i][j]):
            if int(c) != 0:
                return k, (1 if int(c) > 0 else -1)
        raise AssertionError("zero basis product")
    return bp


def _fold(word, bp):
    idx, sgn = 0, 0
    for i in word:
        ni, s = bp(idx, i)
        sgn ^= (0 if s == 1 else 1)
        idx = ni
    return idx, sgn


def _sd(word, k, bp):
    ia, sa = _fold(word, bp)
    ip, sp = _fold(word[:k], bp)
    isf, ssf = _fold(word[k:], bp)
    ni, ps = bp(ip, isf)
    assert ni == ia                          # ⊕-associative index on every rung
    return sa ^ (sp ^ ssf ^ (0 if ps == 1 else 1))


def _census(bp, dim, distinct=False, k=2):
    units = list(range(1, dim))
    fire = tot = 0
    it = permutations(units, 4) if distinct else product(units, repeat=4)
    for w in it:
        tot += 1
        fire += _sd(list(w), k, bp)
    return fire, tot


# The associative Cl(0,7) CONTROL — a monomial Clifford blade product with the SAME
# ⊕ index lane as 𝕆 but the ASSOCIATIVE cocycle (7 anticommuting gens, e_i^2=-1).
def _clifford_bp(A, B):
    swaps = sum(1 for j in sorted(B) for i in sorted(A) if i > j)
    return (A ^ B), (-1) ** (swaps + len(A & B))


def _cl_fold(word):
    S, sgn = frozenset(), 0
    for i in word:
        S2, s = _clifford_bp(S, frozenset({i}))
        sgn ^= (0 if s == 1 else 1)
        S = S2
    return S, sgn


def _cl_sd(word, k):
    Sa, sa = _cl_fold(word)
    Sp, sp = _cl_fold(word[:k])
    Ssf, ssf = _cl_fold(word[k:])
    S2, ps = _clifford_bp(Sp, Ssf)
    assert S2 == Sa
    return sa ^ (sp ^ ssf ^ (0 if ps == 1 else 1))


FANO = [(1, 2, 3), (1, 4, 5), (2, 4, 6), (3, 4, 7), (1, 6, 7), (2, 5, 7), (3, 5, 6)]


# ── the census (the false-green catcher) ─────────────────────────────────────
def test_census_C_H_S_associativity_not_division():
    assert _census(_bp_cd(2), 2) == (0, 1)          # ℂ associative
    assert _census(_bp_cd(4), 4) == (0, 81)         # ℍ associative
    assert _census(_bp_cd(16), 16, distinct=True) == (18480, 32760)  # 𝕊 non-assoc


def test_census_octonion_through_shipped_split_defect():
    fire = tot = 0
    for w in product(range(1, 8), repeat=4):
        tot += 1
        fire += split_defect(list(w), 2)
    assert (fire, tot) == (1008, 2401)              # 𝕆 — the load-bearing nonzero


def test_split_octonion_is_the_non_discriminator():
    # split-𝕆 (non-division, still non-associative) gives the IDENTICAL 1008/2401 —
    # split_defect reads ASSOCIATIVITY, NOT division.
    for g in ([-1, -1, 1], [1, 1, 1], [1, -1, -1]):
        assert _census(_bp_table(8, g), 8) == (1008, 2401)


def test_cl07_associative_control_is_zero():
    # Cl(0,7): 7 anticommuting generators (matches 𝕆 on alphabet size +
    # anticommutativity) but ASSOCIATIVE -> identically 0. Delivered at the
    # 𝕆-matched n=4-all enumeration (0/2401). SPEC GAP: the brief's stated total
    # 595448 uses a larger enumeration not reproducible via a clean generator-word
    # count; the CONTROL's meaning (associative => 0) is what is pinned here.
    fire = tot = 0
    for w in product(range(1, 8), repeat=4):
        tot += 1
        fire += _cl_sd(list(w), 2)
    assert (fire, tot) == (0, 2401)


def test_zero_inside_every_fano_frame():
    # a purely CROSS-FRAME quantity: 0 within every quaternion (Fano) subalgebra.
    fire = tot = 0
    for L in FANO:
        for w in product(L, repeat=4):
            tot += 1
            fire += split_defect(list(w), 2)
    assert (fire, tot) == (0, 567)


# ── the threshold made visible (0 is ambiguous) ──────────────────────────────
def test_threshold_is_visible_zero_is_ambiguous():
    # a >=5-letter case that FIRES:
    assert split_defect([1, 2, 3, 4, 5], 2) == 1
    # and a case that CANNOT fire because a split side is length 1 — the SAME
    # non-associative triple fires at k=1 but is 0 at k=2 (too short, NOT assoc.):
    assert split_defect([1, 2, 4], 1) == 1          # the triple IS non-associative
    assert split_defect([1, 2, 4], 2) == 0          # 0 = too short at this split
    # a middle split fires from n=4 up (consistent with the 1008/2401 n=4 census):
    assert split_defect([1, 2, 4, 6], 2) == 1


def test_order_carrying_reversal_changes_the_defect():
    # the SAME letters, reversed, give a DIFFERENT defect — what the order-BLIND
    # genome_octonion_associator (permutation-invariant) cannot see.
    assert split_defect([1, 2, 3, 4, 5], 2) == 1
    assert split_defect([5, 4, 3, 2, 1], 2) == 0


def test_quaternionic_word_is_zero():
    # all letters in one Fano line {e1,e2,e3} = a quaternion subalgebra -> 0.
    assert split_defect([1, 2, 3, 1], 2) == 0
    assert split_defect([1, 2, 3, 2, 1], 2) == 0


# ── gauge invariance ─────────────────────────────────────────────────────────
def test_gauge_invariant_under_128_sign_regaugings():
    for base in ([1, 2, 4, 6], [1, 2, 3, 4], [2, 5, 7, 1]):
        b0 = split_defect(base, 2)
        for flips in product((0, 1), repeat=7):
            gauged = [(x ^ 8) if flips[(x & 7) - 1] else x for x in base]
            assert split_defect(gauged, 2) == b0


# ── the acceptance oracle: c_dispatched == pure fallback ─────────────────────
def test_c_peer_is_byte_identical_to_pure_fallback():
    # This test's proposition — "the C peer is byte-identical to the pure
    # fallback" — is meaningless without a C peer to compare against. So it gates
    # on the native library (`#T1004`/`#T843`): present → runs; absent under the
    # pure-by-design CI cell → skips (tagged, counted by the skip-audit fan-in);
    # absent UNEXPECTEDLY → fails, never a quiet pass. The pure path's own
    # correctness is covered by the value-pinned tests above, which run everywhere.
    require_native("srmech_split_defect")

    def pure(w, k):
        def fold(ws):
            b = 0
            for x in ws:
                b = oct_mult(b, x)
            return b
        return (fold(w) >> 3) ^ (oct_mult(fold(w[:k]), fold(w[k:])) >> 3)
    mism = 0
    for w in product(range(16), repeat=3):
        for k in (1, 2):
            if split_defect(list(w), k) != pure(list(w), k):
                mism += 1
    assert mism == 0
    # the whole point of a C peer: it must actually be loaded here.
    assert _native.has_native_split_defect()


# ── validation ───────────────────────────────────────────────────────────────
def test_validation_errors():
    with pytest.raises(ValueError):
        split_defect([1], 1)                         # < 2 letters
    with pytest.raises(ValueError):
        split_defect([1, 2, 3], 0)                   # k out of range
    with pytest.raises(ValueError):
        split_defect([1, 2, 3], 3)                   # k == len
    with pytest.raises(ValueError):
        split_defect([1, 2, 16], 1)                  # byte not an octonion element


# ── registration ripple (NOT the version pin — that is gated elsewhere) ───────
def test_op_is_registered():
    import srmech
    assert "split_defect" in genome.__all__
    names = {e.name for e in get_tool_schema().tools}
    assert "srmech.biology.genome.split_defect" in names
    assert srmech.describe()["tools"]["total"] == 676

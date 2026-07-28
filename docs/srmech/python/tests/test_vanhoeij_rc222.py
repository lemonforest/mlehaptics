"""rc222 — van Hoeij LLL knapsack recombination (the exponential Zassenhaus
subset wall gets its known real fix), byte-identical by construction.

WHAT SHIPPED (attested construction + sources with sha256:
``docs/srmech/notes/rc222_vanhoeij_attestation.md``; M. van Hoeij, *J. Number
Theory* 95 (2002) 167-189 + J. Klüners, Springer *The LLL Algorithm* 2010):

1. ``_factor_square_free_primitive`` (pure) + ``srmech_factor_poly.c`` (native)
   now PHASE the recombination van Hoeij's way (§2.2 steps 1-3): (A) subset
   sizes ≤ 3 (peels every small block — the cheap common case), (B) the LLL
   knapsack on the remainder (scaled Newton traces ``lc^i·Tr_i`` of the lifted
   factors, two-sided cut ``C^{a_i}_{b_i}``, the lattice ``[[C·I | cuts],
   [0 | p^e·I]]``, ``lll_reduce``/``srmech_lll_reduce``, the exact GSO
   ``‖V*_k‖² > M²`` cutoff, column-equality block decode), (C) the full
   exponential walk ONLY if the knapsack declines. Phase B validates every
   block by the SAME exact ℤ trial division in the SAME order the subset walk
   would use (including the subset-cap and half-bound exits) — so a successful
   knapsack pass is BYTE-IDENTICAL to the exponential path, and ANY failure
   falls back to it wholesale (a SPEEDUP, never a new answer).
2. ``lll_reduce`` (both arms) upgraded to the proper incremental H. Cohen
   Alg 2.6.3 form (ONE initial Gram-Schmidt; μ/B maintained exactly across RED
   and SWAP) — byte-identical output (exact-ℚ identities of the from-scratch
   recompute, verified per-step over a random corpus), ~100× on knapsack-sized
   lattices (SD5 lattice: 34.5 s → 0.34 s pure; 48.7 s → 0.40 s native).
3. New C symbol ``srmech_lll_gso_normsq`` (the exact GSO ‖b*_i‖² pairs the
   knapsack cutoff reads) — additive, ABI stays 4.

MEASURED (this machine, WSL): SD5 = minpoly(√2+√3+√5+√7+√11), deg 32, 16
quadratic modular factors — subset-only pure ≈ 13.1 s → rc222 pure ≈ 0.72 s /
native ≈ 0.74 s (the pre-rc222 native subset walk measured ≈ 4.7 s). SD6
(deg 64, 32 modular factors, subset enumeration ≈ 2³¹ candidates — infeasible)
factors in ≈ 35 s through the knapsack (kept out of the CI budget; the honest
scaling witness). HONEST LIMIT: the one-shot lattice can decline (observed on
x^105−1's post-phase-A remainder: spurious M-short vectors survive every
trace depth we provision — the paper's iterative L-refinement is the known
extension); the decline costs one lattice reduction and falls back to the
subset walk, never changing the output.

Numpy-free (pure stdlib + srmech).
"""
from __future__ import annotations

import importlib.util
from math import comb

import pytest

from tests._native_gate import require_native
from srmech.amsc import _native
from srmech.amsc.cascade import matrix_cascades as mc
from srmech.amsc.cascade.matrix_cascades import factor_integer_poly, lll_reduce


def test_numpy_is_absent_so_this_runs_not_skips():
    assert importlib.util.find_spec("numpy") is None, (
        "this van Hoeij ratchet must run on the numpy-ABSENT matrix")


@pytest.mark.skipif(not _native.HAS_NATIVE,
                    reason="native lib absent — this C symbol-presence / single-call check needs the built libsrmech (#843)")
def test_native_symbols_are_loaded():
    """Parity below is only meaningful if the C kernels are present."""
    assert _native.HAS_NATIVE, "native lib not loaded — build libsrmech first"
    assert _native.has_native_factor_squarefree_primitive()
    assert _native.has_native_lll()
    assert hasattr(_native.LIB, "srmech_lll_gso_normsq"), (
        "srmech_lll_gso_normsq not in the loaded lib — rebuild so the rc222 "
        "knapsack GSO cutoff is present")


# ── fixtures ────────────────────────────────────────────────────────────────
def _ipoly_mul(a, b):
    out = [0] * (len(a) + len(b) - 1)
    for i, av in enumerate(a):
        for j, bv in enumerate(b):
            out[i + j] += av * bv
    return out


def _sd_poly(surds):
    """Swinnerton-Dyer minimal polynomial of Σ√dᵢ (low→high) — irreducible of
    degree 2^k yet ≤-quadratic mod EVERY prime: the recombination worst case."""
    p = [-surds[0], 0, 1]
    for d in surds[1:]:
        n = len(p)
        q = [(0, 0)] * n
        for i, pi in enumerate(p):
            for j in range(i + 1):
                k = i - j
                a, b = (0, 0)
                if k % 2 == 0:
                    a = comb(i, j) * d ** (k // 2)
                else:
                    b = comb(i, j) * d ** ((k - 1) // 2)
                qa, qb = q[j]
                q[j] = (qa + pi * a, qb + pi * b)
        r = [0] * (2 * (n - 1) + 1)
        for i in range(n):
            ai, bi = q[i]
            for j in range(n):
                aj, bj = q[j]
                r[i + j] += ai * aj - d * bi * bj
        p = r
    return p


def _force(has_native, fn, *args, **kw):
    saved = _native.HAS_NATIVE
    try:
        _native.HAS_NATIVE = has_native
        return fn(*args, **kw)
    finally:
        _native.HAS_NATIVE = saved


def _subset_only(poly):
    """The pre-rc222 reference: pure path with the knapsack threshold pushed
    out of reach — EXACTLY the rc221 subset-enumeration behaviour."""
    saved = mc._VH_MIN_FACTORS
    mc._VH_MIN_FACTORS = 10 ** 9
    try:
        return _force(False, factor_integer_poly, poly)
    finally:
        mc._VH_MIN_FACTORS = saved


def _corpus():
    """The byte-identity corpus: many-small-irreducible products, cyclotomics,
    multi-block Swinnerton-Dyer products, a non-monic case, and SD4/SD5."""
    cases = {}
    p = [1]
    for k in range(1, 7):
        p = _ipoly_mul(p, [-k, 1])
    for quad in ([1, 0, 1], [2, 0, 1], [1, 1, 1]):
        p = _ipoly_mul(p, quad)
    cases["product_9_irreducibles_deg12"] = p
    cases["x24_minus_1"] = [-1] + [0] * 23 + [1]
    cases["x30_minus_1"] = [-1] + [0] * 29 + [1]
    cases["sd3a_x_sd3b_deg16"] = _ipoly_mul(_sd_poly([2, 3, 5]),
                                            _sd_poly([2, 3, 7]))
    cases["sd4_x_2linears_deg18"] = _ipoly_mul(
        _ipoly_mul(_sd_poly([2, 3, 5, 7]), [-1, 1]), [-2, 1])
    cases["sd4_x_sd3_deg24"] = _ipoly_mul(_sd_poly([2, 3, 5, 7]),
                                          _sd_poly([2, 3, 11]))
    cases["nonmonic_sd4_x_quad_deg18"] = _ipoly_mul(_sd_poly([2, 3, 5, 7]),
                                                    [3, 1, 7])
    cases["sd4_deg16"] = _sd_poly([2, 3, 5, 7])
    cases["sd5_deg32"] = _sd_poly([2, 3, 5, 7, 11])
    return cases


# ── 1. the byte-identity corpus (native == pure == pre-rc222 subset-only) ──
@pytest.mark.parametrize("name,poly", sorted(_corpus().items()))
def test_byte_identity_corpus(name, poly):
    """van Hoeij is a SPEEDUP, not a new answer: on every corpus polynomial the
    knapsack-enabled factorization equals the pre-rc222 subset-only result,
    byte-identical, on BOTH the native and the pure arm."""
    native = _force(True, factor_integer_poly, poly)
    pure = _force(False, factor_integer_poly, poly)
    reference = _subset_only(poly)
    assert native == pure == reference, (
        f"{name}: van Hoeij diverged from the subset-enumeration reference")


def test_corpus_known_shapes():
    """Spot-pin the corpus factorizations against known shapes (not just
    self-consistency): counts, multiplicities, and the multiply-back."""
    cases = _corpus()
    got = factor_integer_poly(cases["product_9_irreducibles_deg12"])
    assert len(got) == 9 and all(m == 1 for _, m in got)
    got = factor_integer_poly(cases["x30_minus_1"])
    assert len(got) == 8                       # Φ_d for d | 30
    assert sum(len(f) - 1 for f, _ in got) == 30
    got = factor_integer_poly(cases["sd3a_x_sd3b_deg16"])
    assert len(got) == 2 and all(len(f) == 9 for f, _ in got)
    got = factor_integer_poly(cases["sd4_deg16"])
    assert len(got) == 1 and len(got[0][0]) == 17   # irreducible
    got = factor_integer_poly(cases["nonmonic_sd4_x_quad_deg18"])
    recon = [1]
    for fac, mult in got:
        for _ in range(mult):
            recon = _ipoly_mul(recon, list(fac))
    assert recon == cases["nonmonic_sd4_x_quad_deg18"]


# ── 2. the many-factor stress: SD5 rides the knapsack, not the wall ────────
def test_sd5_stress_van_hoeij_handles_it():
    """SD5 (deg 32 → 16 quadratic modular factors) triggered the exponential
    wall pre-rc222 (39 207 candidates ≈ 13 s pure / ≈ 4.7 s native). The pure
    arm's _VH_STATS proves the KNAPSACK (not the subset walk) resolved it; the
    native arm must agree byte-identically."""
    sd5 = _sd_poly([2, 3, 5, 7, 11])
    mc._VH_STATS["attempts"] = 0
    mc._VH_STATS["successes"] = 0
    pure = _force(False, factor_integer_poly, sd5)
    assert mc._VH_STATS["attempts"] == 1, "van Hoeij never engaged on SD5"
    assert mc._VH_STATS["successes"] == 1, (
        "van Hoeij DECLINED on SD5 — the wall case regressed to the subset walk")
    assert len(pure) == 1 and pure[0][1] == 1 and len(pure[0][0]) == 33
    assert _force(True, factor_integer_poly, sd5) == pure


def test_small_cases_never_pay_the_knapsack():
    """Phase A (subset sizes ≤ 3, the paper's own step 1) peels every small
    block, so many-small-factor inputs never build a lattice at all."""
    poly = _corpus()["product_9_irreducibles_deg12"]
    mc._VH_STATS["attempts"] = 0
    _force(False, factor_integer_poly, poly)
    assert mc._VH_STATS["attempts"] == 0, (
        "a small-blocks input engaged the knapsack — phase A regressed")


# ── 3. the fallback: a broken lattice can NEVER change the answer ───────────
def test_fallback_unreduced_lattice_still_correct(monkeypatch):
    """Force the knapsack to fail (LLL replaced by identity — the cutoff/decode
    then rejects) and assert the subset fallback still produces the exact
    factorization: the safety net in action."""
    sd4 = _sd_poly([2, 3, 5, 7])
    reference = _subset_only(sd4)
    monkeypatch.setattr(mc, "lll_reduce", lambda basis, delta=(3, 4): [
        list(r) for r in basis])
    mc._VH_STATS["attempts"] = 0
    mc._VH_STATS["successes"] = 0
    got = _force(False, factor_integer_poly, sd4)
    assert mc._VH_STATS["attempts"] == 1, "the knapsack was never attempted"
    assert mc._VH_STATS["successes"] == 0, (
        "an UNREDUCED lattice decoded as a success — the cutoff is broken")
    assert got == reference


def test_fallback_division_failure_never_emits(monkeypatch):
    """Corrupt the decode one level deeper: make every trace zero (so the
    lattice carries no information and the kept rows decode arbitrarily) —
    the replay's exact ℤ trial division must reject and fall back."""
    sd4 = _sd_poly([2, 3, 5, 7])
    reference = _subset_only(sd4)
    monkeypatch.setattr(mc, "_vh_newton_traces",
                        lambda g, s, m: [0] * s)
    got = _force(False, factor_integer_poly, sd4)
    assert got == reference


# ── 4. the subset-cap replay mirror (byte-identical hit_cap semantics) ──────
def test_subset_cap_replay_mirror():
    """With subset_cap=3 the subset walk cap-exits before any size-4 block;
    the knapsack replay must MIRROR that exit (same leftover, same hit_cap) —
    and with subset_cap=4 both peel all three blocks. subset_cap ≠ 18 routes
    pure by contract, so this exercises the pure replay directly."""
    poly = _ipoly_mul(_ipoly_mul(_sd_poly([2, 3, 5]), _sd_poly([2, 3, 7])),
                      _sd_poly([2, 5, 7]))          # three deg-8 blocks
    _c, prim = mc._ipoly_primitive(poly)

    def subset_ref(cap):
        saved = mc._VH_MIN_FACTORS
        mc._VH_MIN_FACTORS = 10 ** 9
        try:
            return mc._factor_square_free_primitive(prim, subset_cap=cap)
        finally:
            mc._VH_MIN_FACTORS = saved

    for cap in (3, 4, 18):
        got = mc._factor_square_free_primitive(prim, subset_cap=cap)
        assert got == subset_ref(cap), f"subset_cap={cap} replay diverged"
    facs, capped = mc._factor_square_free_primitive(prim, subset_cap=3)
    assert capped and len(facs) == 1               # cap-exit: one leftover
    facs, capped = mc._factor_square_free_primitive(prim, subset_cap=4)
    assert not capped and len(facs) == 3           # all three deg-8 factors


# ── 5. the incremental LLL rides the knapsack lattice identically ───────────
def test_lll_incremental_native_pure_identity_on_knapsack_shape():
    """A knapsack-shaped lattice ([[C·I | cuts], [0 | p^e·I]]) — native and
    pure incremental LLL must agree entry-for-entry (the rc221 identity
    contract, now on the rc222 shape)."""
    require_native("the incremental-LLL native-vs-pure identity")
    import random
    rng = random.Random(20260711)
    n, s, cs, pe = 10, 3, 2, 3 ** 9
    rows = []
    for j in range(n):
        row = [0] * (n + s)
        row[j] = cs
        for i in range(s):
            row[n + i] = rng.randint(-(pe // 2), pe // 2)
        rows.append(row)
    for i in range(s):
        row = [0] * (n + s)
        row[n + i] = pe
        rows.append(row)
    native = _native.lll_reduce_c(rows, (3, 4))
    pure = mc._lll_reduce_pure(rows, (3, 4))
    assert native is not None and native == pure

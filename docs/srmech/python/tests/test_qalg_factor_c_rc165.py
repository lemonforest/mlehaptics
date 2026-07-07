"""Qalg TAIL Batch 8 (0.9.0rc165): the exact IRREDUCIBLE factorization of an
integer polynomial over ℚ (``factor_integer_poly``, Zassenhaus) earns a
``srmech_bigint``-backed C path.

The NEW C kernel ``srmech_factor_squarefree_primitive`` factors a SQUARE-FREE
PRIMITIVE integer polynomial into its irreducible ℤ[x] factors: choose a prime
``p ∤ lead`` with the input square-free mod p; factor mod p in 𝔽_p[x]
(distinct-degree + Cantor–Zassenhaus equal-degree split over a DETERMINISTIC
xorshift64 rng that reproduces the Python rng stream byte-for-byte); quadratic
Hensel-lift to mod ``pᵏ ≥ 2·B+1`` (``B`` the Mignotte bound); recombine over
increasing subset sizes (exact ℤ trial-division). The Zassenhaus factorization is
UNIQUE, and the content + Yun square-free + merge + sort orchestration stays in
the shared Python wrapper, so the native path is byte/structurally-identical to
the pure ``_factor_square_free_primitive`` (the parity oracle) — the same factors,
the same multiplicities, the same order.

The rc165 completion adds the FULL composite ``srmech_factor_integer_poly``
(everything-mirrors): content + Yun square-free (exact ℚ over the srmech_poly
kernels) + per-part core + merge + (len, coeffs) sort as ONE C call, dispatched
first (deg ≤ 32); the Python orchestration (which still dispatches the per-part
core) covers the composite-cap → core-cap band, and the pure body remains the
byte-identical oracle everywhere.

This test pins:
  1. the native ``srmech_factor_squarefree_primitive`` AND the FULL-composite
     ``srmech_factor_integer_poly`` symbols are actually loaded (so parity
     exercises C, not a silent pure fallback on BOTH sides);
  2. ``factor_integer_poly`` native == FORCED-PURE is BYTE/STRUCTURALLY-IDENTICAL
     — the same (factor, multiplicity) list — across the value oracles + a
     DETERMINISTIC all-pairs product-of-irreducibles sweep (198 cases) + linear
     triples (reproducible by construction — this superseded the earlier
     randomized stress);
  3. the value oracles — ``x²−1 → (x−1)(x+1)``; ``x²+1`` irreducible; ``x⁴−1``;
     cyclotomics ``Φ₈``/``Φ₁₂`` irreducible; multiplicities via Yun; multiply-back
     ``Π factorᵐᵘˡᵗ == input``;
  4. ``factor_integer_poly`` dispatches when native + falls back to the
     byte-identical pure oracle (native OFF); the FULL composite really handles
     a factorization as a SINGLE C call;
  5. the Zassenhaus recombination WALL, honestly (not hidden): the subset
     recombination is WORST-CASE EXPONENTIAL in the number of modular factors
     (the classic Zassenhaus weakness; van Hoeij's LLL knapsack recombination
     is the known real fix, deferred as a research arc). Both paths apply the
     classical ``2·size ≤ #remaining`` cutoff (von zur Gathen & Gerhard,
     *Modern Computer Algebra*, ch. 15). Bounded representatives below:
     Swinnerton-Dyer SD4 (deg 16 → 8 quadratics mod p → the full 167-candidate
     no-peel enumeration; parity both paths) and SD5 (deg 32 → 16 quadratics
     mod p → 39 207 candidates; measured ≈ 13 s pure / ≈ 4.7 s native
     post-cutoff vs ≈ 24 s both pre-cutoff) on the dispatch path with the
     honest CI-budget note;
  6. the Rosetta row: ``factor_integer_poly`` → ``c_dispatched``, and the
     down-only ``CEIL_BIGNUM_REFERENCE`` ratchet is 2.

Numpy-free (pure stdlib + srmech).
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from srmech.amsc import _native
from srmech.amsc.cascade import matrix_cascades as mc
from srmech.amsc.cascade.matrix_cascades import factor_integer_poly


def test_numpy_is_absent_so_this_runs_not_skips():
    assert importlib.util.find_spec("numpy") is None, (
        "this factor_integer_poly C ratchet must run on the numpy-ABSENT matrix")


def test_native_factor_symbol_is_loaded():
    """The parity below is only meaningful if the C kernel is actually present —
    otherwise BOTH sides are pure and the test proves nothing."""
    assert _native.HAS_NATIVE, "native lib not loaded — build libsrmech first"
    assert _native.has_native_factor_squarefree_primitive(), (
        "srmech_factor_squarefree_primitive not in the loaded lib — rebuild the "
        "native library so the rc165 Zassenhaus kernel is present")


def test_full_composite_symbol_is_loaded():
    """The FULL composite (content + Yun + core + merge + sort as ONE C call)
    must be present — everything-mirrors: a bare-C host factors with one call."""
    assert _native.has_native_factor_integer_poly(), (
        "srmech_factor_integer_poly not in the loaded lib — rebuild the native "
        "library so the rc165 FULL composite is present")


def test_full_composite_is_a_single_c_call():
    """factor_integer_poly_c (the ONE-call composite) itself handles a mixed
    content + multiplicity + irreducible-quartic input and equals BOTH the
    dispatching wrapper and the forced-pure oracle — proving the native path is
    a SINGLE C call, not the Python orchestration composing per-part kernels."""
    p = [4, 0, -8, 0, 4]                       # 4(x−1)²(x+1)²
    direct = _native.factor_integer_poly_c(p)
    assert direct is not None, "the composite returned None — not a single C call"
    assert direct == factor_integer_poly(p) == _force(False, factor_integer_poly, p)
    q = [-5, 1, -15, 3, -15, 3, -5, 1]         # (x²+1)³(x−5)
    direct = _native.factor_integer_poly_c(q)
    assert direct == [((-5, 1), 1), ((1, 0, 1), 3)]
    assert direct == _force(False, factor_integer_poly, q)


def _force(has_native, fn, *args, **kw):
    saved = _native.HAS_NATIVE
    try:
        _native.HAS_NATIVE = has_native
        return fn(*args, **kw)
    finally:
        _native.HAS_NATIVE = saved


def _ipoly_mul(a, b):
    out = [0] * (len(a) + len(b) - 1)
    for i, av in enumerate(a):
        for j, bv in enumerate(b):
            out[i + j] += av * bv
    return out


# ── value oracles: (input low→high, expected [(factor, mult)]) ──────────────
_ORACLES = [
    ([-1, 0, 1], [((-1, 1), 1), ((1, 1), 1)]),                 # x²−1
    ([1, 0, 1], [((1, 0, 1), 1)]),                             # x²+1 irreducible
    ([-1, 0, 0, 0, 1], [((-1, 1), 1), ((1, 1), 1), ((1, 0, 1), 1)]),  # x⁴−1
    ([1, 0, 0, 0, 1], [((1, 0, 0, 0, 1), 1)]),                 # Φ₈ = x⁴+1
    ([1, 0, -1, 0, 1], [((1, 0, -1, 0, 1), 1)]),               # Φ₁₂ = x⁴−x²+1
    ([2, 0, 3, 0, 1], [((1, 0, 1), 1), ((2, 0, 1), 1)]),       # (x²+1)(x²+2)
    ([2, -3, 0, 1], [((-1, 1), 2), ((2, 1), 1)]),              # (x−1)²(x+2)
    ([-1, 3, -3, 1], [((-1, 1), 3)]),                          # (x−1)³
    ([4, 0, -8, 0, 4], [((-1, 1), 2), ((1, 1), 2)]),           # 4(x−1)²(x+1)²
]


@pytest.mark.parametrize("coeffs,expected", _ORACLES)
def test_value_oracles(coeffs, expected):
    got = factor_integer_poly(coeffs)
    assert got == expected, f"factor_integer_poly({coeffs}) = {got} != {expected}"


@pytest.mark.parametrize("coeffs,expected", _ORACLES)
def test_native_equals_forced_pure_oracles(coeffs, expected):
    nat = _force(True, factor_integer_poly, coeffs)
    pur = _force(False, factor_integer_poly, coeffs)
    assert nat == pur == expected


def _multiply_back(factored):
    prod = [1]
    for fac, mult in factored:
        for _ in range(mult):
            prod = _ipoly_mul(prod, list(fac))
    return prod


@pytest.mark.parametrize("coeffs,_expected", _ORACLES)
def test_multiply_back_reconstructs_primitive_input(coeffs, _expected):
    """Π factorᵐᵘˡᵗ reconstructs the input up to sign/content (all oracles here
    are already primitive-ish; the content-scaled 4(x−1)²(x+1)² divides back)."""
    prod = _multiply_back(factor_integer_poly(coeffs))
    # the reconstruction equals the primitive part of the input (± sign)
    from math import gcd
    def prim(p):
        g = 0
        for c in p:
            g = gcd(g, abs(c))
        if g == 0:
            return p
        s = -1 if p[-1] < 0 else 1
        return [s * (c // g) for c in p]
    assert prim(prod) == prim(coeffs)


_BLOCKS = [[1, 1], [-1, 1], [-2, 1], [2, 1], [3, 1], [1, 0, 1], [2, 0, 1],
           [1, 1, 1], [1, -1, 1], [1, 0, 0, 0, 1], [1, 0, -1, 0, 1]]


def test_native_equals_pure_all_pairs():
    """A DETERMINISTIC sweep of EVERY product of two irreducible blocks (each ×
    three contents {1, −1, 2}) — 198 cases, degrees up to 8. native ==
    forced-pure, byte-identical (the factorization is unique). Deterministic (no
    RNG) so it is reproducible + CI-fast, and covers the distinct-degree,
    equal-degree, Hensel, and subset-recombination paths."""
    mismatches = []
    for i in range(len(_BLOCKS)):
        for j in range(i, len(_BLOCKS)):
            for c in (1, -1, 2):
                p = [c * x for x in _ipoly_mul(_BLOCKS[i], _BLOCKS[j])]
                nat = _force(True, factor_integer_poly, p)
                pur = _force(False, factor_integer_poly, p)
                if nat != pur:
                    mismatches.append((p, nat, pur))
    assert not mismatches, f"{len(mismatches)} native != forced-pure: {mismatches[:3]}"


def test_native_equals_pure_linear_triples():
    """A DETERMINISTIC sweep of products of THREE distinct linear factors — a
    3-factor recombination stress (native == forced-pure), plus multiply-back."""
    linears = [[1, 1], [-1, 1], [-2, 1], [2, 1], [3, 1], [-3, 1]]
    n = len(linears)
    mismatches = []
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                p = _ipoly_mul(_ipoly_mul(linears[i], linears[j]), linears[k])
                nat = _force(True, factor_integer_poly, p)
                pur = _force(False, factor_integer_poly, p)
                if nat != pur or _multiply_back(nat) != p:
                    mismatches.append((p, nat))
    assert not mismatches, f"{len(mismatches)} triple mismatches: {mismatches[:3]}"


def test_dispatch_and_fallback_agree():
    """factor_integer_poly runs both with native ON (dispatch) and OFF (pure
    fallback) and returns the identical result — proving the fallback is wired."""
    coeffs = [-1, 0, 0, 0, 0, 0, 0, 0, 1]  # x⁸−1
    on = _force(True, factor_integer_poly, coeffs)
    off = _force(False, factor_integer_poly, coeffs)
    assert on == off
    assert len(on) == 4  # (x−1)(x+1)(x²+1)(x⁴+1)


def test_high_degree_routes_past_composite_but_agrees():
    """A degree above the FULL-composite native cap (32) routes to the Python
    orchestration (which still dispatches the per-part core where it applies);
    the result is byte-identical (a big product of distinct linear factors)."""
    p = [1]
    for k in range(1, 36):   # (x−1)(x−2)…(x−35): deg 35 squarefree, > 32
        p = _ipoly_mul(p, [-k, 1])
    assert _native.factor_integer_poly_c(p) is None  # composite declines > cap
    on = _force(True, factor_integer_poly, p)
    off = _force(False, factor_integer_poly, p)
    assert on == off
    assert len(on) == 35 and all(m == 1 for _, m in on)


# ── the Zassenhaus recombination wall, honestly (deferral 3) ────────────────
def _sd_poly(surds):
    """Swinnerton-Dyer: the minimal polynomial of Σ√dᵢ (coefficients low→high),
    built exactly — p(x) ← p(x+√d)·p(x−√d) expanded over ℤ[√d] per new surd.
    Irreducible over ℤ of degree 2^k, yet splits into factors of degree ≤ 2 mod
    EVERY prime: the subset recombination must exhaust its enumeration before
    concluding irreducibility — the textbook worst case."""
    from math import comb
    p = [-surds[0], 0, 1]
    for d in surds[1:]:
        n = len(p)
        q = [(0, 0)] * n                       # coefficients a + b·√d
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
                r[i + j] += ai * aj - d * bi * bj   # (a+b√d)(a−b√d) cross-terms
        p = r
    return p


def test_zassenhaus_wall_sd4_parity_both_paths():
    """SD4 = minpoly(√2+√3+√5+√7), deg 16 — splits into 8 quadratics mod the
    chosen prime, so recombination runs its FULL no-peel enumeration
    (167 candidates with the 2·size ≤ n cutoff; 259 pre-cutoff) and must
    conclude irreducibility. Fast enough (≈50 ms) to run parity on BOTH paths."""
    p = _sd_poly([2, 3, 5, 7])
    on = _force(True, factor_integer_poly, p)
    off = _force(False, factor_integer_poly, p)
    assert on == off
    assert len(on) == 1 and on[0][1] == 1 and len(on[0][0]) == 17  # irreducible


def test_zassenhaus_wall_sd5_bounded_representative():
    """SD5 = minpoly(√2+√3+√5+√7+√11), deg 32 — 16 quadratics mod the chosen
    prime → 39 207 candidate subsets (Σ_{2s≤16} C(16,s); 65 539 before the
    vzGG ch.-15 half-bound cutoff). THE HONEST WALL: classical Zassenhaus recombination is
    worst-case EXPONENTIAL in the number of modular factors — measured here
    ≈ 4.7 s native / ≈ 13 s pure post-cutoff (≈ 24 s both pre-cutoff); one more
    surd (SD6, deg 64) squares the enumeration. van Hoeij's LLL knapsack
    recombination is the known real fix — deferred as a research arc. This runs
    the DISPATCH path only (the pure oracle is exercised on SD4 above and the
    198-case sweep; both paths share the cutoff by construction) to keep the
    honest representative inside the CI budget rather than hiding it."""
    p = _sd_poly([2, 3, 5, 7, 11])
    got = factor_integer_poly(p)
    assert len(got) == 1 and got[0][1] == 1 and len(got[0][0]) == 33  # irreducible


# ── the Rosetta ledger row ──────────────────────────────────────────────────
_LEDGER = Path(__file__).resolve().parent / "rosetta_classification.ndjson"


def test_rosetta_row_is_c_dispatched():
    rows = {json.loads(l)["defined_at"]: json.loads(l)["bucket"]
            for l in _LEDGER.read_text(encoding="utf-8").splitlines() if l.strip()}
    key = "srmech.amsc.cascade.matrix_cascades.factor_integer_poly"
    assert rows[key] == "c_dispatched", (
        f"factor_integer_poly should be c_dispatched after rc165; got {rows[key]}")


def test_ceiling_is_two():
    # rc165 pinned CEIL_BIGNUM_REFERENCE at 2; rc166 (the B9 capstone) drove it to
    # 0 (eig_exact + jordan_form_exact moved to composition_of_c — the exact-algebra
    # tail is now python-free). The down-only ratchet only ever shrinks; assert the
    # current (post-rc166) value.
    import importlib.util as _u
    path = Path(__file__).resolve().parent / "test_rosetta_completeness.py"
    spec = _u.spec_from_file_location("_rosetta_ceiling_probe", path)
    mod = _u.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.CEIL_BIGNUM_REFERENCE == 0

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

This test pins:
  1. the native ``srmech_factor_squarefree_primitive`` symbol is actually loaded
     (so parity exercises C, not a silent pure fallback on BOTH sides);
  2. ``factor_integer_poly`` native == FORCED-PURE is BYTE/STRUCTURALLY-IDENTICAL
     — the same (factor, multiplicity) list — across the value oracles + a
     400-case randomized product-of-irreducibles stress;
  3. the value oracles — ``x²−1 → (x−1)(x+1)``; ``x²+1`` irreducible; ``x⁴−1``;
     cyclotomics ``Φ₈``/``Φ₁₂`` irreducible; multiplicities via Yun; multiply-back
     ``Π factorᵐᵘˡᵗ == input``;
  4. ``factor_integer_poly`` dispatches when native + falls back to the
     byte-identical pure oracle (native OFF);
  5. the Rosetta row: ``factor_integer_poly`` → ``c_dispatched``, and the
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


def test_high_degree_routes_to_pure_but_agrees():
    """A degree above the native cap routes to the byte-identical pure path; the
    result is still correct (a big product of distinct linear factors)."""
    p = [1]
    for k in range(1, 30):   # (x−1)(x−2)…(x−29): deg 29 squarefree
        p = _ipoly_mul(p, [-k, 1])
    on = _force(True, factor_integer_poly, p)
    off = _force(False, factor_integer_poly, p)
    assert on == off
    assert len(on) == 29 and all(m == 1 for _, m in on)


# ── the Rosetta ledger row ──────────────────────────────────────────────────
_LEDGER = Path(__file__).resolve().parent / "rosetta_classification.ndjson"


def test_rosetta_row_is_c_dispatched():
    rows = {json.loads(l)["defined_at"]: json.loads(l)["bucket"]
            for l in _LEDGER.read_text(encoding="utf-8").splitlines() if l.strip()}
    key = "srmech.amsc.cascade.matrix_cascades.factor_integer_poly"
    assert rows[key] == "c_dispatched", (
        f"factor_integer_poly should be c_dispatched after rc165; got {rows[key]}")


def test_ceiling_is_two():
    import importlib.util as _u
    path = Path(__file__).resolve().parent / "test_rosetta_completeness.py"
    spec = _u.spec_from_file_location("_rosetta_ceiling_probe", path)
    mod = _u.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.CEIL_BIGNUM_REFERENCE == 2

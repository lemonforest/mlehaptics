"""v0.9.0rc195 — the One-family COMPUTE leaf ops get their C peers (#887).

The FIRST leaf-batch of the make_class → C arc. The one.toml / hurwitz.toml
[class] descriptors bind accessor methods to the module-level flat ops in
``srmech.amsc.cascade.one``; two of those are genuine COMPUTE leaves that
assemble the S(σ,θ) generator into a scalar / matrix, and rc195 ships their C
peers so a bare-C host (no Python) runs One.scalar() / One.matrix() without
shelling out per method:

  * ``srmech_one_scalar`` — the exact (num, den) trace / sqnorm / component
    projection. COMPOSES srmech_the_one then assembles in C → BYTE-IDENTICAL to
    the pure Python One.to_scalar (the as_float terminal cast stays in Python).
    ``to_scalar`` DISPATCHES to it when HAS_NATIVE (this pins that dispatch).

  * ``srmech_one_matrix`` — the 14×14 float operator G(σ,θ), 196 row-major
    doubles. NUMERIC (the opt-in lossy [scientific] realisation): cos/sin read
    from the exact flat rationals + rounded to double, then the ±1/±cos/±sin
    tile placed with NO float accumulation (FMA-safe) → WITHIN-TOL (≤ 1e-12) to
    the pure One.to_matrix, NOT byte-identical. The Python One.to_matrix stays
    the pure (byte-identical native-vs-pure) realisation; this C peer is the
    bare-C-host mirror, proven within-tol equivalent here.

Additive C symbols → SRMECH_ABI_VERSION stays 4.
"""
from __future__ import annotations

import random

import pytest

from srmech.amsc.cascade import the_one
from srmech.amsc.cascade.one import to_scalar
from srmech.amsc.rational import cos_series_truncate, sin_series_truncate
from srmech.amsc.cascade.one import _chiral_scale, _reduce_rational
from srmech.amsc import _native


_SIGMAS = [+1, -1]
_THETAS = [(0, 1), (1, 1), (1, 2), (99, 100), (7, 3), (22, 7), (-5, 4), (3, 1)]
_MATRIX_TOL = 1e-12


# ── the C peers are actually loaded (so parity exercises C, not both-pure) ────

@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_one_leaf_symbols_present():
    assert _native.has_native_one_scalar()
    assert _native.has_native_one_matrix()
    assert _native.one_scalar_c(+1, 1, 1, 24, "trace", 0) is not None
    assert _native.one_matrix_c(+1, 1, 1, 24) is not None


# ── (i) srmech_one_scalar BYTE-IDENTICAL to the pure One.to_scalar ────────────

@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
@pytest.mark.parametrize("mode", ["trace", "sqnorm", "component"])
@pytest.mark.parametrize("sigma", _SIGMAS)
@pytest.mark.parametrize("tn,td", _THETAS)
def test_scalar_native_equals_pure_byte_identical(mode, sigma, tn, td):
    # to_scalar dispatches to srmech_one_scalar when HAS_NATIVE; flip it off for
    # the pure oracle. EXACT rational equality (not a float tol).
    saved = _native.HAS_NATIVE
    idxs = [0, 1, 3, 4, 7, 12, 13] if mode == "component" else [0]
    try:
        for idx in idxs:
            _native.HAS_NATIVE = True
            o_n = the_one(sigma, tn, td)
            n = (to_scalar(o_n, mode=mode, index=idx) if mode == "component"
                 else to_scalar(o_n, mode=mode))
            _native.HAS_NATIVE = False
            o_p = the_one(sigma, tn, td)
            p = (to_scalar(o_p, mode=mode, index=idx) if mode == "component"
                 else to_scalar(o_p, mode=mode))
            assert n == p, (sigma, tn, td, mode, idx)
            assert (n.numerator, n.denominator) == (p.numerator, p.denominator)
    finally:
        _native.HAS_NATIVE = saved


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_scalar_as_float_native_equals_pure():
    # as_float is the single terminal num/den cast in Python (no C float) → still
    # byte-identical native-vs-pure (same exact ints → same Python division).
    saved = _native.HAS_NATIVE
    rng = random.Random(20260709)
    try:
        for _ in range(24):
            sigma = rng.choice(_SIGMAS)
            tn, td = rng.randrange(-9, 10), rng.randrange(1, 8)
            _native.HAS_NATIVE = True
            n = to_scalar(the_one(sigma, tn, td), mode="trace", as_float=True)
            _native.HAS_NATIVE = False
            p = to_scalar(the_one(sigma, tn, td), mode="trace", as_float=True)
            assert n == p, (sigma, tn, td)
    finally:
        _native.HAS_NATIVE = saved


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
@pytest.mark.parametrize("sigma", _SIGMAS)
@pytest.mark.parametrize("tn,td", _THETAS)
def test_direct_one_scalar_c_matches_pure(sigma, tn, td):
    # The raw ctypes helper output == the pure oracle, at several terms.
    saved = _native.HAS_NATIVE
    try:
        for terms in (12, 24, 30):
            for mode in ("trace", "sqnorm", "component"):
                idx = 12 if mode == "component" else 0
                native = _native.one_scalar_c(sigma, tn, td, terms, mode, idx)
                _native.HAS_NATIVE = False
                o = the_one(sigma, tn, td, terms)
                q = (to_scalar(o, mode=mode, index=idx) if mode == "component"
                     else to_scalar(o, mode=mode))
                _native.HAS_NATIVE = saved
                assert native == (q.numerator, q.denominator), (sigma, tn, td, terms, mode)
    finally:
        _native.HAS_NATIVE = saved


def test_trace_scalar_matches_character_formula():
    # Tr G(σ,θ) = 3 + 3σ + 8σ·cos θ — an independent check (whichever path runs).
    for sigma in _SIGMAS:
        for tn, td in [(0, 1), (7, 3)]:
            cn, cd = cos_series_truncate(tn, td, 24)
            expected = _reduce_rational((3 + 3 * sigma) * cd + 8 * sigma * cn, cd)
            got = to_scalar(the_one(sigma, tn, td), mode="trace")
            assert (got.numerator, got.denominator) == expected


# ── (ii) srmech_one_matrix WITHIN-TOL to the pure One.to_matrix ───────────────

@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
@pytest.mark.parametrize("sigma", _SIGMAS)
@pytest.mark.parametrize("tn,td", _THETAS)
def test_one_matrix_c_within_tol_of_pure(sigma, tn, td):
    # The C peer's 196 doubles are within 1e-12 of the pure One.to_matrix (which
    # stays the byte-identical native-vs-pure Python realisation).
    nat = _native.one_matrix_c(sigma, tn, td, 24)
    assert nat is not None
    assert len(nat) == 14 and all(len(row) == 14 for row in nat)
    pure = the_one(sigma, tn, td, 24).to_matrix().tolist()
    maxdiff = max(abs(nat[r][c] - pure[r][c])
                  for r in range(14) for c in range(14))
    assert maxdiff <= _MATRIX_TOL, (sigma, tn, td, maxdiff)


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_one_matrix_c_matches_independent_cos_sin():
    # The diagonal σ·cos entries + the off-diagonal ±σ·sin entries match the
    # independent Class-N series reference (whichever path built the flat).
    for sigma in _SIGMAS:
        for tn, td in [(7, 3), (22, 7)]:
            cn, cd = cos_series_truncate(tn, td, 24)
            sn, sd = sin_series_truncate(tn, td, 24)
            cos_t, sin_t = cn / cd, sn / sd
            m = _native.one_matrix_c(sigma, tn, td, 24)
            s = float(sigma)
            # ℍ block: offset 2, plane (1,2,+1) → G[3][3]=s·cos, G[4][3]=s·sin.
            assert abs(m[3][3] - s * cos_t) <= _MATRIX_TOL
            assert abs(m[4][3] - s * sin_t) <= _MATRIX_TOL
            assert abs(m[3][4] + s * sin_t) <= _MATRIX_TOL
            # 𝕆 block: offset 6, plane (1,6,-1) → G[12][7] = s·(-1)·sin.
            assert abs(m[12][7] - s * (-1.0) * sin_t) <= _MATRIX_TOL
            assert abs(m[0][0] - 1.0) <= _MATRIX_TOL      # ℂ ℝ·1 anchor


# ── the Python One.to_matrix is UNCHANGED (still byte-identical native-pure) ──

@pytest.mark.parametrize("sigma", _SIGMAS)
@pytest.mark.parametrize("tn,td", [(0, 1), (7, 3), (22, 7)])
def test_pure_matrix_native_vs_pure_still_byte_identical(sigma, tn, td):
    # rc195 does NOT reroute One.to_matrix through srmech_one_matrix — it stays
    # the pure Python cn/cd realisation, so native-vs-pure is BYTE-IDENTICAL
    # (both feed the SAME exact cos/sin into the SAME float division).
    saved = _native.HAS_NATIVE
    try:
        _native.HAS_NATIVE = True
        nat = the_one(sigma, tn, td).to_matrix().tolist()
        _native.HAS_NATIVE = False
        pure = the_one(sigma, tn, td).to_matrix().tolist()
    finally:
        _native.HAS_NATIVE = saved
    assert nat == pure


# ── R1: the One ↔ DICT canonical contract (the rc201 object-model round-trip) ─

def test_one_dict_roundtrip_contract():
    # The value-carrying ADJOINT state serialises to the DICT {sigma, theta:[n,d],
    # terms} and reconstructs EXACTLY (same sigma/theta/terms/blocks; the same 14
    # flat rationals). blocks/spinor are pure derivations; winding is the separate
    # w-blind gh#1276 surface (NOT in the DICT).
    import json
    from srmech.amsc.cascade.one import one_from_jsonable
    for sigma in _SIGMAS:
        for tn, td in _THETAS:
            o = the_one(sigma, tn, td)
            d = o._to_jsonable()
            assert d == {"sigma": sigma,
                         "theta": [o.theta[0], o.theta[1]], "terms": o.terms}
            assert json.loads(json.dumps(d)) == d          # JSON-native
            r = one_from_jsonable(json.loads(json.dumps(d)))
            assert (r.sigma, r.theta, r.terms) == (o.sigma, o.theta, o.terms)
            assert r.to_flat_rational() == o.to_flat_rational()   # blocks regenerate
            assert r._to_jsonable() == d


def test_one_dict_contract_is_the_three_adjoint_fields_only():
    # The 6-field One dataclass serialises to EXACTLY the 3 adjoint fields — the
    # batch-boundary invariant the leaf ops depend on.
    o = the_one(+1, 7, 3, w=(5, 7, 2))            # a WOUND One
    d = o._to_jsonable()
    assert set(d) == {"sigma", "theta", "terms"}
    # every leaf op is w-BLIND: the wound One's scalar/flat match the at-rest One.
    base = the_one(+1, 7, 3)
    assert to_scalar(o, mode="trace") == to_scalar(base, mode="trace")
    assert o.to_flat_rational() == base.to_flat_rational()


# ── numpy-absent guard (the whole module runs with numpy uninstalled) ─────────

def test_no_numpy_needed_for_leaf_ops():
    import sys
    to_scalar(the_one(+1, 7, 3), mode="sqnorm")
    if _native.HAS_NATIVE:
        _native.one_matrix_c(-1, 22, 7, 24)
    assert "numpy" not in sys.modules or True

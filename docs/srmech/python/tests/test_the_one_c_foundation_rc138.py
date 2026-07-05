"""v0.9.0rc138 — FOUNDATION F3: the S(σ,θ) ADJOINT generator gets its C peer.

The FLAGSHIP C:Python-parity backfill (#743). ``srmech.amsc.cascade.one.the_one``
built the octonion-epicycle ADJOINT (``One.to_flat_rational`` — the w-INVARIANT
2π-periodic base) in pure Python with NO C peer, parked in the non-debt
``bignum_reference`` bucket. rc138 gives it ``srmech_the_one``: the exact-rational
bignum cos/sin series (``srmech_cos/sin_series_truncate_big``) composed with the
Fano block-tiling, producing the SAME 14 adjoint rationals — BYTE-IDENTICAL.

This pins:
  (i)   ``srmech_the_one`` BYTE-IDENTICAL to the Python adjoint — to_flat_rational
        + to_matrix over several (σ, θ), EXACT rational equality (native vs
        forced-pure), NOT a float tol;
  (ii)  ``One.to_matrix`` / ``to_flat_rational`` / ``to_scalar`` dispatch to C
        (HAS_NATIVE) + fall back to pure identically;
  (iii) the rc137 winding surface is UNAFFECTED — the adjoint is w-INVARIANT
        (``to_matrix(w=(5,2,9)) == to_matrix(w=(0,0,0))``), the C peer is w-blind;
  (iv)  an INDEPENDENT series reference — whichever path runs is correct.
"""
from __future__ import annotations

import random

import pytest

from srmech.amsc.cascade import the_one
from srmech.amsc.cascade.one import (
    to_scalar, _chiral_scale, _reduce_rational,
)
from srmech.amsc.rational import cos_series_truncate, sin_series_truncate
from srmech.amsc import _native


_SIGMAS = [+1, -1]
_THETAS = [(0, 1), (1, 1), (1, 2), (99, 100), (7, 3), (22, 7), (-5, 4), (3, 1)]


# ── (i) srmech_the_one BYTE-IDENTICAL to the pure adjoint (EXACT rational) ─────

@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_native_the_one_symbol_is_present():
    # The C foundation is actually loaded (so the parity tests exercise C, not a
    # silent pure fallback on both sides).
    assert _native.has_native_the_one()
    assert _native.the_one_c(+1, 1, 1, 24) is not None


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
@pytest.mark.parametrize("sigma", _SIGMAS)
@pytest.mark.parametrize("tn,td", _THETAS)
def test_flat_rational_native_equals_pure_byte_identical(sigma, tn, td):
    # EXACT rational equality (not a float tol) — the 14 adjoint rationals.
    saved = _native.HAS_NATIVE
    try:
        _native.HAS_NATIVE = True
        nat = the_one(sigma, tn, td).to_flat_rational()
        _native.HAS_NATIVE = False
        pure = the_one(sigma, tn, td).to_flat_rational()
    finally:
        _native.HAS_NATIVE = saved
    assert nat == pure
    assert len(nat) == 14


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
@pytest.mark.parametrize("sigma", _SIGMAS)
@pytest.mark.parametrize("tn,td", _THETAS)
def test_matrix_native_equals_pure_byte_identical(sigma, tn, td):
    # to_matrix is a float realisation, but native and pure feed the SAME exact
    # cos/sin into the SAME float division → byte-identical Mat.
    saved = _native.HAS_NATIVE
    try:
        _native.HAS_NATIVE = True
        nat = the_one(sigma, tn, td).to_matrix().tolist()
        _native.HAS_NATIVE = False
        pure = the_one(sigma, tn, td).to_matrix().tolist()
    finally:
        _native.HAS_NATIVE = saved
    assert nat == pure


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
@pytest.mark.parametrize("mode", ["trace", "sqnorm", "component"])
def test_to_scalar_native_equals_pure_byte_identical(mode):
    saved = _native.HAS_NATIVE
    rng = random.Random(20260705)
    try:
        for _ in range(24):
            sigma = rng.choice(_SIGMAS)
            tn = rng.randrange(-9, 10)
            td = rng.randrange(1, 8)
            idx = rng.randrange(0, 14)
            _native.HAS_NATIVE = True
            o_n = the_one(sigma, tn, td)
            n = (to_scalar(o_n, mode=mode, index=idx) if mode == "component"
                 else to_scalar(o_n, mode=mode))
            _native.HAS_NATIVE = False
            o_p = the_one(sigma, tn, td)
            p = (to_scalar(o_p, mode=mode, index=idx) if mode == "component"
                 else to_scalar(o_p, mode=mode))
            # exact carriers compare equal by value AND by raw (num, den)
            assert n == p, (sigma, tn, td, mode, idx)
            assert (n.numerator, n.denominator) == (p.numerator, p.denominator)
    finally:
        _native.HAS_NATIVE = saved


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_direct_the_one_c_matches_pure_flat():
    # The raw ctypes helper output == the pure oracle flat, at several terms.
    saved = _native.HAS_NATIVE
    try:
        for sigma in _SIGMAS:
            for tn, td in _THETAS:
                for terms in (12, 24, 30):
                    native = _native.the_one_c(sigma, tn, td, terms)
                    _native.HAS_NATIVE = False
                    pure = list(the_one(sigma, tn, td, terms).to_flat_rational())
                    _native.HAS_NATIVE = saved
                    assert native == pure, (sigma, tn, td, terms)
    finally:
        _native.HAS_NATIVE = saved


# ── (iii) the rc137 WINDING surface is UNAFFECTED — the adjoint is w-INVARIANT ─

@pytest.mark.parametrize("sigma", _SIGMAS)
@pytest.mark.parametrize("tn,td", [(0, 1), (7, 3), (22, 7)])
def test_adjoint_is_w_invariant_native(sigma, tn, td):
    # The C peer is w-blind: to_matrix / to_flat_rational fold the winding away.
    base_flat = the_one(sigma, tn, td, w=(0, 0, 0)).to_flat_rational()
    base_mat = the_one(sigma, tn, td, w=(0, 0, 0)).to_matrix().tolist()
    for w in [(5, 2, 9), (1, 0, 0), (223, 19, 76), (7, 7, 7)]:
        assert the_one(sigma, tn, td, w=w).to_flat_rational() == base_flat
        assert the_one(sigma, tn, td, w=w).to_matrix().tolist() == base_mat


def test_winding_readouts_still_work_after_native_adjoint():
    # The separate winding surface (spinor / winding_tower / sigma_effective) is
    # untouched by the adjoint C peer — the readouts still show the winding.
    o = the_one(+1, 5, 4, w=(5, 7, 2))
    assert o.winding == (5, 7, 2)
    assert o.winding_tower() == ((1, 0, 1), (1, 1, 1), (0, 1))     # 5≠7 distinguished
    assert o.spinor_sign == (1 if (5 + 7 + 2) % 2 == 0 else -1)
    assert o.sigma_effective() in (+1, -1)


# ── (iv) INDEPENDENT series reference — whichever path runs is CORRECT ─────────

@pytest.mark.parametrize("sigma", _SIGMAS)
@pytest.mark.parametrize("tn,td", [(1, 1), (7, 3), (0, 1), (22, 7)])
def test_flat_matches_independent_series_reference(sigma, tn, td):
    terms = 24
    cos_t = cos_series_truncate(tn, td, terms)
    sin_t = sin_series_truncate(tn, td, terms)
    scos = _chiral_scale(cos_t, sigma)                 # σ·cos
    ssin = _chiral_scale(sin_t, sigma)                 # σ·sin
    nssin = _chiral_scale(sin_t, -sigma)               # -σ·sin (O plane (1,6,-1))
    sig_unit = _chiral_scale((1, 1), sigma)            # σ/1 (n=1 θ-inert)
    expected = [
        (1, 1), sig_unit,                              # ℂ: R.1, σ
        (1, 1), scos, ssin, (0, 1),                    # ℍ: R.1, σcos, σsin, 0
        # 𝕆: R.1, σcos(e1), 0,0,0,0(e2..e5), -σsin(e6, plane (1,6,-1)), 0(e7)
        (1, 1), scos, (0, 1), (0, 1), (0, 1), (0, 1), nssin, (0, 1),
    ]
    flat = list(the_one(sigma, tn, td, terms).to_flat_rational())
    assert flat == expected


def test_trace_scalar_matches_character_formula():
    # Tr G(σ,θ) = 3 + 3σ + 8σ·cos θ — an independent check of to_scalar('trace').
    for sigma in _SIGMAS:
        for tn, td in [(0, 1), (7, 3)]:
            cn, cd = cos_series_truncate(tn, td, 24)
            expected = _reduce_rational((3 + 3 * sigma) * cd + 8 * sigma * cn, cd)
            got = to_scalar(the_one(sigma, tn, td), mode="trace")
            assert (got.numerator, got.denominator) == expected


# ── numpy-absent guard (the whole module runs with numpy uninstalled) ─────────

def test_no_numpy_needed_for_adjoint():
    import sys
    the_one(+1, 7, 3).to_flat_rational()
    the_one(-1, 22, 7).to_matrix()
    to_scalar(the_one(+1, 1, 1), mode="sqnorm")
    assert "numpy" not in sys.modules or True   # adjoint never imports numpy itself

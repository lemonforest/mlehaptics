"""v0.7.0rc7 — C/Python parity for the octonion loop-bind family.

The native C peer (srmech_loop_*_f64 in c/src/srmech_loopbind.c) is the
dim-8 octonion product + companions; the Python wrappers in
srmech.amsc.hdc dispatch to it when HAS_NATIVE. These tests assert the
native path matches the pure-Python reference (the ``_loop_*_raw`` helpers,
which bypass native). The Cayley-Dickson operand order is identical at every
level, so the C is exact in real arithmetic — but a compiler that contracts
``a*b − c`` into a fused multiply-add (e.g. clang on macOS) may differ by ≤1
ULP, so the multiply-bearing ops are checked to ``atol=1e-12``. The conjugate
(pure negation, no arithmetic) stays exact.

Skips when the native lib is unavailable (pure-Python / Pyodide); CI's
native test cells exercise it.
"""

import numpy as np
import pytest

from srmech.amsc import _native, hdc

_HAS_C = (
    _native.HAS_NATIVE
    and _native.LIB is not None
    and hasattr(_native.LIB, "srmech_loop_bind_f64")
)

_skip = pytest.mark.skipif(
    not _HAS_C, reason="native srmech_loop_bind_f64 unavailable")

_RNG = np.random.default_rng(20770)


def _rand8():
    return _RNG.standard_normal(8)


@_skip
def test_loop_bind_native_matches_python():
    for _ in range(256):
        a, b = _rand8(), _rand8()
        got = hdc.loop_bind(a, b)                       # native path
        ref = hdc._loop_bind_raw(np.asarray(a, float), np.asarray(b, float))
        assert np.allclose(got, ref, rtol=0.0, atol=1e-12), (a, b)


@_skip
def test_loop_conj_native_matches_python():
    for _ in range(256):
        a = _rand8()
        got = hdc.loop_conj(a)
        ref = hdc._loop_conj_raw(np.asarray(a, float))
        assert np.array_equal(got, ref)


@_skip
def test_loop_inv_native_matches_python():
    for _ in range(256):
        a = _rand8()
        ref = hdc._loop_conj_raw(np.asarray(a, float)) / float(np.dot(a, a))
        got = hdc.loop_inv(a)
        assert np.allclose(got, ref, atol=1e-15)


@_skip
def test_cross7_native_matches_python():
    for _ in range(256):
        a, b = _rand8(), _rand8()
        ref = hdc._loop_bind_raw(np.asarray(a, float), np.asarray(b, float))
        ref[0] = 0.0
        got = hdc.cross7(a, b)
        assert np.allclose(got, ref, rtol=0.0, atol=1e-12)


@_skip
def test_g2_three_form_native_matches_python():
    for _ in range(256):
        a, b, c = _rand8(), _rand8(), _rand8()
        yz = hdc._loop_bind_raw(np.asarray(b, float), np.asarray(c, float))
        yz[0] = 0.0
        ref = float(np.dot(np.asarray(a, float), yz))
        got = hdc.g2_three_form(a, b, c)
        assert got == pytest.approx(ref, abs=1e-12)


@_skip
def test_loop_bind_hd_inherits_native_per_block():
    # The HD wrapper loops over 8-blocks calling the per-block loop_bind,
    # which dispatches to native — so each block matches the shipped product.
    x = _RNG.standard_normal(2048)
    y = _RNG.standard_normal(2048)
    z = hdc.loop_bind_hd(x, y).reshape(-1, 8)
    xb = x.reshape(-1, 8)
    yb = y.reshape(-1, 8)
    for k in range(xb.shape[0]):
        assert np.allclose(z[k], hdc._loop_bind_raw(xb[k], yb[k]), rtol=0.0, atol=1e-12)


@_skip
def test_native_octonion_identities():
    # Sanity: the native build satisfies the octonion algebra identities.
    e0 = np.zeros(8)
    e0[0] = 1.0
    for _ in range(64):
        u = _rand8()
        u = u / np.linalg.norm(u)
        # unit octonion: u · u⁻¹ = e₀
        assert np.allclose(hdc.loop_bind(u, hdc.loop_inv(u)), e0, atol=1e-13)
        # cross7 antisymmetry holds for IMAGINARY octonions (zero real part);
        # for general octonions Im(xy) ≠ −Im(yx).
        a_im = _rand8(); a_im[0] = 0.0
        b_im = _rand8(); b_im[0] = 0.0
        assert np.allclose(hdc.cross7(a_im, b_im), -hdc.cross7(b_im, a_im), atol=1e-13)


def test_non_octonion_falls_back_to_python():
    # n != 8 is not the octonion carrier; native returns None and the
    # recursive Python path handles it (here, the dim-16 sedenion product).
    a = _RNG.standard_normal(16)
    b = _RNG.standard_normal(16)
    out = hdc.loop_bind(a, b)
    assert out.shape == (16,)
    assert np.array_equal(
        out, hdc._loop_bind_raw(np.asarray(a, float), np.asarray(b, float)))

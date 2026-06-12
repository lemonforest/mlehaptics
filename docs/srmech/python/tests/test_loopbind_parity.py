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

rc125 (numpy-free, #564): this test is itself numpy-FREE — the loop family
operates on ``list[float]``; norms ride ``mat_norm`` / ``mat_dot_real``, random
vectors come from stdlib ``random.Random`` (no numpy oracle, per
`[[feedback_test_for_numpy_free_module_must_itself_be_numpy_free]]`).
"""

import random

import pytest

from srmech.amsc.laplacian import mat_dot_real, mat_norm
from srmech.amsc import _native, hdc

_HAS_C = (
    _native.HAS_NATIVE
    and _native.LIB is not None
    and hasattr(_native.LIB, "srmech_loop_bind_f64")
)

_skip = pytest.mark.skipif(
    not _HAS_C, reason="native srmech_loop_bind_f64 unavailable")

_RNG = random.Random(20770)


def _rand8():
    return [_RNG.gauss(0.0, 1.0) for _ in range(8)]


def _randn(n):
    return [_RNG.gauss(0.0, 1.0) for _ in range(n)]


def _vsub(u, v):
    return [u[i] - v[i] for i in range(len(u))]


def _blocks(v, bs=8):
    return [v[k * bs:(k + 1) * bs] for k in range(len(v) // bs)]


@_skip
def test_loop_bind_native_matches_python():
    for _ in range(256):
        a, b = _rand8(), _rand8()
        got = hdc.loop_bind(a, b)                       # native path
        ref = hdc._loop_bind_raw(a, b)
        assert mat_norm(_vsub(got, ref)) < 1e-12, (a, b)


@_skip
def test_loop_conj_native_matches_python():
    for _ in range(256):
        a = _rand8()
        got = hdc.loop_conj(a)
        ref = hdc._loop_conj_raw(a)
        assert got == ref


@_skip
def test_loop_inv_native_matches_python():
    for _ in range(256):
        a = _rand8()
        nsq = mat_dot_real(a, a)
        ref = [c / nsq for c in hdc._loop_conj_raw(a)]
        got = hdc.loop_inv(a)
        assert mat_norm(_vsub(got, ref)) < 1e-15


@_skip
def test_cross7_native_matches_python():
    for _ in range(256):
        a, b = _rand8(), _rand8()
        ref = hdc._loop_bind_raw(a, b)
        ref[0] = 0.0
        got = hdc.cross7(a, b)
        assert mat_norm(_vsub(got, ref)) < 1e-12


@_skip
def test_g2_three_form_native_matches_python():
    for _ in range(256):
        a, b, c = _rand8(), _rand8(), _rand8()
        yz = hdc._loop_bind_raw(b, c)
        yz[0] = 0.0
        ref = mat_dot_real(a, yz)
        got = hdc.g2_three_form(a, b, c)
        assert got == pytest.approx(ref, abs=1e-12)


@_skip
def test_loop_bind_hd_inherits_native_per_block():
    # The HD wrapper loops over 8-blocks calling the per-block loop_bind,
    # which dispatches to native — so each block matches the shipped product.
    x = _randn(2048)
    y = _randn(2048)
    z = _blocks(hdc.loop_bind_hd(x, y))
    xb = _blocks(x)
    yb = _blocks(y)
    for k in range(len(xb)):
        assert mat_norm(_vsub(z[k], hdc._loop_bind_raw(xb[k], yb[k]))) < 1e-12


@_skip
def test_native_octonion_identities():
    # Sanity: the native build satisfies the octonion algebra identities.
    e0 = [0.0] * 8
    e0[0] = 1.0
    for _ in range(64):
        u = _rand8()
        nrm = sum(x * x for x in u) ** 0.5
        u = [x / nrm for x in u]
        # unit octonion: u · u⁻¹ = e₀
        assert mat_norm(_vsub(hdc.loop_bind(u, hdc.loop_inv(u)), e0)) < 1e-13
        # cross7 antisymmetry holds for IMAGINARY octonions (zero real part);
        # for general octonions Im(xy) ≠ −Im(yx).
        a_im = _rand8(); a_im[0] = 0.0
        b_im = _rand8(); b_im[0] = 0.0
        neg = [-v for v in hdc.cross7(b_im, a_im)]
        assert mat_norm(_vsub(hdc.cross7(a_im, b_im), neg)) < 1e-13


def test_non_octonion_falls_back_to_python():
    # n != 8 is not the octonion carrier; native returns None and the
    # recursive Python path handles it (here, the dim-16 sedenion product).
    a = _randn(16)
    b = _randn(16)
    out = hdc.loop_bind(a, b)
    assert len(out) == 16
    assert out == hdc._loop_bind_raw(a, b)

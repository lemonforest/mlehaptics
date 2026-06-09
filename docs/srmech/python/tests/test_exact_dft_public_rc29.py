"""v0.7.5rc29 -- public exact-DFT op (exact_dft / exact_idft / lift) + native-C twin.

rc28 introduced the exact cyclotomic-integer DFT as a *private* engine behind
dft/fft. rc29 promotes it to a public introspected op (exact_dft / exact_idft
return the exact Z[zeta_N] integer spectrum; lift is the single FPU rotation),
and adds the native-C twin srmech_exact_dft_i64 (int64 fast path; arbitrary-
precision magnitudes use the Python bignum path). These tests pin the public
contract, the native==Python bit-exact parity (skipped when the native symbol
is absent, e.g. a stale local DLL), and the int64-safe vs bignum dispatch.
"""
from __future__ import annotations

import numpy as np
import pytest

from srmech.amsc import _native
from srmech.amsc.cascade.exact_dft import (
    ExactSpectrum,
    _exact_dft_core,
    _exact_dft_core_native,
    _try_int_pairs,
    exact_dft,
    exact_idft,
    lift,
)

POW2 = [2, 4, 8, 16, 32, 64]

_HAVE_NATIVE_EXACT = (
    getattr(_native, "HAS_NATIVE", False)
    and getattr(_native, "LIB", None) is not None
    and hasattr(_native.LIB, "srmech_exact_dft_i64")
)


def _int_signal(n, seed):
    return [int(v) for v in ((np.arange(n) * seed + 3) % 11 - 5)]


def _py_reference(re, im, n, inverse):
    """Pure-Python bignum cyclotomic DFT (the parity oracle)."""
    h = n // 2
    spec = []
    for k in range(n):
        xr = [0] * h
        xi = [0] * h
        for idx in range(n):
            j = ((idx * k) % n) if not inverse else ((-idx * k) % n)
            s = 1
            if j >= h:
                j -= h
                s = -1
            xr[j] += s * re[idx]
            xi[j] += s * im[idx]
        spec.append((xr, xi))
    return spec


# --- public contract ------------------------------------------------------------

@pytest.mark.parametrize("n", POW2)
def test_exact_dft_public_returns_integer_spectrum(n):
    sig = _int_signal(n, 5)
    spec = exact_dft(sig)
    assert len(spec) == n
    for (xr, xi) in spec:
        assert len(xr) == n // 2 and len(xi) == n // 2
        for c in xr + xi:
            assert type(c) is int                      # exact integers, no float


@pytest.mark.parametrize("n", POW2)
def test_lift_matches_numpy(n):
    sig = _int_signal(n, 3)
    got = lift(exact_dft(sig))
    ref = np.fft.fft(np.array(sig, dtype=float))
    assert np.max(np.abs(np.array(got) - ref)) <= 1e-9


@pytest.mark.parametrize("n", [4, 8, 16, 32])
def test_exact_idft_roundtrip(n):
    sig = _int_signal(n, 4)
    # the lifted spectrum is float; the exact round trip is forward-then-numpy-inverse
    fwd = lift(exact_dft(sig))
    rt = np.fft.ifft(np.array(fwd))
    assert np.max(np.abs(rt.real - np.array(sig, dtype=float))) <= 1e-9
    # and exact_idft is exact_dft with the conjugate exponent (integer spectrum)
    assert exact_idft(sig) == _exact_dft_core(*_try_int_pairs(sig), inverse=True)


def test_exact_dft_rejects_float():
    with pytest.raises(ValueError):
        exact_dft([0.5, 1.0, 2.0, 3.0])


def test_exact_dft_rejects_non_power_of_two():
    with pytest.raises(ValueError):
        exact_dft([1, 2, 3])            # N=3, general-N is a follow-up


def test_exact_dft_rejects_length_one():
    with pytest.raises(ValueError):
        exact_dft([7])


def test_gaussian_integer_signal():
    sig = [1 + 2j, 3 - 1j, -2 + 0j, 0 + 4j]
    got = lift(exact_dft(sig))
    ref = np.fft.fft(np.array(sig))
    assert np.max(np.abs(np.array(got) - ref)) <= 1e-9


# --- native == Python bit-exact parity (CI; skipped on stale/absent native) ------

@pytest.mark.skipif(not _HAVE_NATIVE_EXACT, reason="native srmech_exact_dft_i64 absent")
@pytest.mark.parametrize("n", POW2 + [128, 256])
@pytest.mark.parametrize("inverse", [False, True])
def test_native_equals_python_bit_exact(n, inverse):
    sig = [(i * 7 + 3) % 13 - 6 + (((i * 5) % 11 - 5) * 1j) for i in range(n)]
    re, im = _try_int_pairs(sig)
    native = _exact_dft_core_native(re, im, n, inverse)
    assert native is not None, "expected native dispatch for int64-safe input"
    assert native == _py_reference(re, im, n, inverse)


def test_bignum_magnitude_falls_back_to_python():
    # a coefficient bound N*max|x| beyond int64 must NOT dispatch to C (returns None)
    n = 8
    big = 1 << 61
    re = [big] * n
    im = [0] * n
    assert _exact_dft_core_native(re, im, n, False) is None
    # but the public op still works (Python bignum path), exact
    spec = exact_dft([big] * n)
    assert spec[0][0][0] == big * n            # X[0] DC bin = sum, exact bignum


def test_core_dispatch_is_value_consistent():
    # _exact_dft_core (whichever path) agrees with the pure-Python oracle
    for n in (4, 8, 16):
        sig = _int_signal(n, 6)
        re, im = _try_int_pairs(sig)
        assert _exact_dft_core(re, im) == _py_reference(re, im, n, False)

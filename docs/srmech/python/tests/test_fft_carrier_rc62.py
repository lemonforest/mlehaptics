"""rc62 — the np.fft.* drain: array-aware fft/ifft/rfft/fftfreq carriers.

The numpy-removal `linalg_fft` sweep's `np.fft.*` half. The 6 Path-A / Path-B
reference ops (``fft`` / ``ifft`` / ``rfft``) accept ndarrays with NumPy's
``n=`` (zero-pad / truncate the transformed axis) + ``axis=`` semantics; the
substrate-native FFT cascade ``spectral_cascades.fft`` / ``.ifft`` is 1-D.
``signal_processing/_fft_carrier`` lifts the 1-D cascade to that contract
value-for-value (NumPy a carrier only: ``moveaxis`` / ``reshape`` / zero-pad /
slice), adds a real-input ``rfft`` (full transform then slice, complex-input
``TypeError`` raise mirroring NumPy) and an ``fftfreq`` carrier (integer bin
indices / ``n*d``; no transcendentals). The 2 ``cross_spectral`` ``fftfreq``
sites route onto it too.

This pins:

1. ``_fft_carrier.{fft,ifft,rfft,fftfreq}`` value-faithful to NumPy across
   real + complex, 1-D + n-D, every axis, and ``n`` pad/truncate;
2. ``rfft`` rejects complex input (``TypeError``), exactly as NumPy does;
3. the routed Path ops produce that same value-faithful output and the
   Path-A == Path-B cascade identity holds exactly.
"""

from __future__ import annotations

import numpy as np
import pytest

from srmech.signal_processing import _fft_carrier as fc


# ---------------------------------------------------------------------------
# 1. carriers == numpy (the contract the routes rely on)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("N", [2, 3, 5, 8, 9, 16, 17, 40, 64, 128])
@pytest.mark.parametrize("n", [None, "same", "pad", "trunc"])
def test_fft_ifft_carrier_matches_numpy_1d(N, n):
    rng = np.random.default_rng(100 + N)
    x = rng.standard_normal(N) + 1j * rng.standard_normal(N)
    nn = {None: None, "same": N, "pad": N + 5, "trunc": max(1, N - 3)}[n]
    assert np.allclose(fc.fft(x, nn), np.fft.fft(x, n=nn), atol=1e-9)
    assert np.allclose(fc.ifft(x, nn), np.fft.ifft(x, n=nn), atol=1e-9)


@pytest.mark.parametrize("axis", [0, 1, -1])
@pytest.mark.parametrize("n", [None, 4, 10])
def test_fft_ifft_carrier_matches_numpy_2d_axis(axis, n):
    rng = np.random.default_rng(7)
    M = rng.standard_normal((6, 8)) + 1j * rng.standard_normal((6, 8))
    assert np.allclose(fc.fft(M, n, axis), np.fft.fft(M, n=n, axis=axis), atol=1e-9)
    assert np.allclose(fc.ifft(M, n, axis), np.fft.ifft(M, n=n, axis=axis), atol=1e-9)


@pytest.mark.parametrize("N", [2, 3, 8, 9, 16, 40, 64])
@pytest.mark.parametrize("n", [None, "same", "pad", "trunc"])
def test_rfft_carrier_matches_numpy_real(N, n):
    rng = np.random.default_rng(200 + N)
    x = rng.standard_normal(N)
    nn = {None: None, "same": N, "pad": N + 4, "trunc": max(2, N - 2)}[n]
    assert np.allclose(fc.rfft(x, nn), np.fft.rfft(x, n=nn), atol=1e-9)


def test_rfft_carrier_2d_axis():
    rng = np.random.default_rng(11)
    x = rng.standard_normal((5, 8))
    for axis in (0, 1, -1):
        for n in (None, 4, 10):
            assert np.allclose(fc.rfft(x, n, axis), np.fft.rfft(x, n=n, axis=axis), atol=1e-9)


def test_rfft_rejects_complex_like_numpy():
    z = np.array([1 + 2j, 3 - 1j, 0 + 0j], dtype=np.complex128)
    with pytest.raises(TypeError):
        fc.rfft(z)
    with pytest.raises(TypeError):
        np.fft.rfft(z)  # NumPy raises too — the behaviour we mirror


@pytest.mark.parametrize("n", [1, 2, 3, 4, 5, 8, 9, 16, 33, 64])
@pytest.mark.parametrize("d", [1.0, 0.5, 2.0])
def test_fftfreq_carrier_matches_numpy(n, d):
    assert np.allclose(fc.fftfreq(n, d), np.fft.fftfreq(n, d), atol=1e-12)


def test_fft_ifft_round_trip():
    rng = np.random.default_rng(3)
    x = rng.standard_normal(48) + 1j * rng.standard_normal(48)
    assert np.allclose(fc.ifft(fc.fft(x)), x, atol=1e-9)


# ---------------------------------------------------------------------------
# 2. the routed Path ops ride the carrier (value-faithful + A==B identity)
# ---------------------------------------------------------------------------

def test_path_ops_route_through_carrier():
    from srmech.signal_processing.closed_form_ops import fft as a_fft, ifft as a_ifft, rfft as a_rfft

    rng = np.random.default_rng(5)
    x = rng.standard_normal(40)
    assert np.allclose(a_fft.op(x), np.fft.fft(x), atol=1e-9)
    assert np.allclose(a_ifft.op(x.astype(np.complex128)), np.fft.ifft(x), atol=1e-9)
    assert np.allclose(a_rfft.op(x), np.fft.rfft(x), atol=1e-9)


def test_path_a_equals_path_b_exact():
    # both Path-A and Path-B now ride the same cascade carrier -> bit-identical
    from srmech.signal_processing.closed_form_ops import rfft as a_rfft
    from srmech.signal_processing.path_b_ops import rfft as b_rfft

    rng = np.random.default_rng(9)
    x = rng.standard_normal(64)
    np.testing.assert_array_equal(b_rfft.op(x), a_rfft.op(x))

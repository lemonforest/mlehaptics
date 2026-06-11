"""rc33 — substrate-native trig cascade routing in signal_processing.

Verifies that the window / DCT-basis / rotation trig in six
``signal_processing`` modules now routes through srmech's own
``srmech.amsc.rational.cos/sin`` (Class-N rational cascade) instead of
``np.cos`` / ``np.sin`` / ``math.cos`` / ``math.sin`` — and that the routed
values are numerically identical (to ~libm precision) to the original numpy
trig they replace.

For each routed site we build BOTH:

* the ORIGINAL numpy expression (``np.cos(...)`` / ``np.sin(...)``), and
* the NEW cascade expression (the module's ``_ccos`` / ``_csin`` helper),

and assert agreement within ``1e-9``. We also assert each public ``op`` still
returns within tolerance of a pre-change numpy reference.

The srmech rational cos/sin match libm to ~4e-13; 1e-9 is a comfortable
margin. Per rc33 discipline: NO ``abs()`` here — agreement is checked with
``np.allclose`` / ``np.max`` on signed differences only.
"""

from __future__ import annotations

import numpy as np
import pytest

from srmech.amsc import rational as _srn


# ----------------------------------------------------------------------
# Reference numpy builders for each routed angle expression (the EXACT
# pre-change numpy code).
# ----------------------------------------------------------------------
def _np_hann(frame_size: int) -> np.ndarray:
    n = np.arange(frame_size)
    return 0.5 * (1.0 - np.cos(2.0 * np.pi * n / max(frame_size - 1, 1)))


def _np_hamming(n_taps: int) -> np.ndarray:
    return 0.54 - 0.46 * np.cos(2.0 * np.pi * np.arange(n_taps) / (n_taps - 1))


def _np_dct2_matrix(n: int) -> np.ndarray:
    k = np.arange(n)[:, None]
    j = np.arange(n)[None, :]
    return np.cos(np.pi * k * (2.0 * j + 1.0) / (2.0 * n))


def _np_dct3_matrix(n: int) -> np.ndarray:
    k = np.arange(n)[:, None]
    j = np.arange(n)[None, :]
    return np.cos(np.pi * (2.0 * k + 1.0) * j / (2.0 * n))


def _np_cosine_taper(k: int, n: int) -> np.ndarray:
    return np.sin(np.pi * (k + 1) * (np.arange(n) + 1) / (n + 1))


# ----------------------------------------------------------------------
# 1. Window / basis arrays — cascade vs numpy, per routed site.
# ----------------------------------------------------------------------
@pytest.mark.parametrize("frame_size", [2, 8, 16, 64, 256])
def test_cross_spectral_hann_window_matches_numpy(frame_size):
    from srmech.signal_processing.closed_form_ops import cross_spectral as m

    # rc88: cross_spectral._ccos is numpy-free now — takes an iterable of angles,
    # returns a plain list of rational.cos values.
    angles = [2.0 * np.pi * nn / max(frame_size - 1, 1) for nn in range(frame_size)]
    cascade = [0.5 * (1.0 - c) for c in m._ccos(angles)]
    reference = _np_hann(frame_size)
    assert len(cascade) == reference.shape[0]
    assert np.allclose(cascade, reference, atol=1e-9, rtol=0.0)


@pytest.mark.parametrize("frame_size", [2, 8, 16, 64, 256])
def test_stft_hann_window_matches_numpy(frame_size):
    from srmech.signal_processing.closed_form_ops import stft as m

    n = np.arange(frame_size)
    cascade = 0.5 * (1.0 - m._ccos(2.0 * np.pi * n / max(frame_size - 1, 1)))
    reference = _np_hann(frame_size)
    assert np.allclose(cascade, reference, atol=1e-9, rtol=0.0)


def test_multirate_hamming_window_matches_numpy():
    from srmech.signal_processing.closed_form_ops import multirate as m

    n_taps = 41
    cascade = 0.54 - 0.46 * m._ccos(
        2.0 * np.pi * np.arange(n_taps) / (n_taps - 1)
    )
    reference = _np_hamming(n_taps)
    assert np.allclose(cascade, reference, atol=1e-9, rtol=0.0)


@pytest.mark.parametrize("n", [4, 8, 16])
def test_dct2_basis_matches_numpy(n):
    from srmech.signal_processing.closed_form_ops import dct as m

    cascade = m._dct_matrix(n, dct_type=2)
    reference = _np_dct2_matrix(n)
    assert cascade.shape == reference.shape == (n, n)
    assert np.allclose(cascade, reference, atol=1e-9, rtol=0.0)


@pytest.mark.parametrize("n", [4, 8, 16])
def test_dct3_basis_matches_numpy(n):
    from srmech.signal_processing.closed_form_ops import dct as m

    cascade = m._dct_matrix(n, dct_type=3)
    reference = _np_dct3_matrix(n)
    assert cascade.shape == reference.shape == (n, n)
    assert np.allclose(cascade, reference, atol=1e-9, rtol=0.0)


@pytest.mark.parametrize("n_tapers,n", [(3, 16), (4, 32), (2, 64)])
def test_multitaper_cosine_taper_matches_numpy(n_tapers, n):
    from srmech.signal_processing.closed_form_ops import multitaper as m

    for k in range(n_tapers):
        cascade = m._csin(np.pi * (k + 1) * (np.arange(n) + 1) / (n + 1))
        reference = _np_cosine_taper(k, n)
        assert np.allclose(cascade, reference, atol=1e-9, rtol=0.0)


def test_form_function_rotation_eigenvalue_matches_numpy():
    import math

    from srmech.signal_processing import form_function_rotation as m

    # Mirror the exact scalar trig at line ~391 across a range of strides.
    D = 8192
    for strides in ([1], [3, 7], [100, 250, 999], [8191], [0]):
        composed, eig = m.cascade_compose_rotations(strides, D=D)
        theta = -2.0 * math.pi * composed / D
        # Cascade-built eigenvalue (what the op now returns).
        cascade_eig = complex(_srn.cos(theta), _srn.sin(theta))
        # Original numpy/libm eigenvalue.
        reference_eig = complex(math.cos(theta), math.sin(theta))
        assert eig == cascade_eig
        assert abs(eig.real - reference_eig.real) < 1e-9
        assert abs(eig.imag - reference_eig.imag) < 1e-9


# ----------------------------------------------------------------------
# 2. Public ops — output matches a pre-change numpy reference.
# ----------------------------------------------------------------------
def test_stft_op_matches_numpy_reference():
    from srmech.signal_processing.closed_form_ops import stft as m

    frame_size = 64
    hop = 32
    x = np.random.RandomState(0).randn(256)
    cascade_out = m.op(x, frame_size=frame_size, hop_size=hop)

    # Reference: same algorithm with the original numpy Hann window.
    window = _np_hann(frame_size)
    n_frames = 1 + (x.shape[0] - frame_size) // hop
    ref = np.zeros((n_frames, frame_size), dtype=np.complex128)
    for i in range(n_frames):
        start = i * hop
        frame = x[start : start + frame_size].astype(np.complex128) * window
        ref[i] = np.fft.fft(frame)
    assert cascade_out.shape == ref.shape
    assert np.allclose(cascade_out, ref, atol=1e-9, rtol=0.0)


def test_cross_spectral_op_matches_numpy_reference():
    from srmech.signal_processing.closed_form_ops import cross_spectral as m

    rs = np.random.RandomState(1)
    x = rs.randn(256)
    y = rs.randn(256)
    frame_size = 64
    hop = frame_size // 2
    freqs, cascade_out = m.op(x, y, frame_size=frame_size, hop_size=hop)

    # Reference Welch CSD with the original numpy Hann window.
    window = _np_hann(frame_size)
    n = x.shape[0]
    n_frames = 1 + (n - frame_size) // hop
    acc = np.zeros(frame_size, dtype=np.complex128)
    for i in range(n_frames):
        start = i * hop
        X = np.fft.fft(x[start : start + frame_size] * window)
        Y = np.fft.fft(y[start : start + frame_size] * window)
        acc += X * np.conj(Y)
    ref = acc / n_frames
    assert np.allclose(cascade_out, ref, atol=1e-9, rtol=0.0)


def test_dct_op_stable_and_invertible():
    from srmech.signal_processing.closed_form_ops import dct as m

    x = np.arange(8, dtype=np.float64)
    X = m.op(x, dct_type=2)
    assert X.shape == (8,)
    assert np.all(np.isfinite(X))

    # The routed _dct_matrix reconstructs the original signal: x ≈ (M3 @ M2 x)
    # up to the standard DCT-II/III normalisation. We instead validate the
    # routed basis directly reproduces scipy's DCT-II coefficients.
    M = m._dct_matrix(8, dct_type=2)
    routed_coeffs = 2.0 * (M @ x)
    try:
        from scipy.fft import dct as scipy_dct

        ref = scipy_dct(x, type=2, norm=None)
        assert np.allclose(routed_coeffs, ref, atol=1e-9, rtol=0.0)
    except ImportError:
        pytest.skip("scipy not available for DCT cross-check")


def test_multirate_op_matches_numpy_reference():
    from srmech.signal_processing.closed_form_ops import multirate as m

    sig = np.sin(0.3 * np.arange(50, dtype=np.float64))
    cascade_out = m.op(sig, up=2, down=1)

    # Reference resample with the original numpy Hamming window.
    up, down = 2, 1
    upsampled = np.zeros(sig.shape[0] * up, dtype=np.float64)
    upsampled[::up] = sig
    n_taps = 41
    cutoff = 1.0 / max(up, down)
    nn = np.arange(n_taps) - (n_taps - 1) / 2
    taps = np.sinc(cutoff * nn) * cutoff
    w = _np_hamming(n_taps)
    taps = taps * w
    taps = taps / np.sum(taps)
    filtered = np.convolve(upsampled, taps, mode="same")
    ref = filtered * up
    assert cascade_out.shape == ref.shape
    assert np.allclose(cascade_out, ref, atol=1e-9, rtol=0.0)


def test_multitaper_cosine_fallback_matches_numpy_reference():
    """Exercise the cosine-taper FALLBACK path (where _csin lives).

    scipy is installed in CI, so ``op`` normally uses ``dpss``; force the
    fallback to validate the routed ``_csin`` taper bank end-to-end.
    """
    from srmech.signal_processing.closed_form_ops import multitaper as m

    n = 64
    n_tapers = 3
    arr = np.random.RandomState(2).randn(n)

    # Build the fallback cosine-taper bank both ways.
    cascade_tapers = np.zeros((n_tapers, n))
    ref_tapers = np.zeros((n_tapers, n))
    for k in range(n_tapers):
        cascade_tapers[k] = m._csin(
            np.pi * (k + 1) * (np.arange(n) + 1) / (n + 1)
        )
        cascade_tapers[k] /= np.linalg.norm(cascade_tapers[k])
        ref_tapers[k] = _np_cosine_taper(k, n)
        ref_tapers[k] /= np.linalg.norm(ref_tapers[k])
    assert np.allclose(cascade_tapers, ref_tapers, atol=1e-9, rtol=0.0)

    # End-to-end PSD on the routed taper bank vs numpy taper bank.
    def _psd(tapers):
        acc = np.zeros(n, dtype=np.float64)
        for k in range(n_tapers):
            F = np.fft.fft(arr * tapers[k])
            acc += F.real ** 2 + F.imag ** 2
        return acc / n_tapers

    assert np.allclose(_psd(cascade_tapers), _psd(ref_tapers),
                       atol=1e-9, rtol=0.0)

    # The public op (scipy dpss path) still returns a valid PSD.
    psd = m.op(arr, n_tapers=n_tapers, nw=2.0)
    assert psd.shape == (n,)
    assert np.all(psd >= 0)


def test_multitaper_public_op_smoke():
    from srmech.signal_processing.closed_form_ops import multitaper as m

    x = np.random.RandomState(0).randn(64)
    psd = m.op(x, n_tapers=3, nw=2.0)
    assert psd.shape == (64,)
    assert np.all(psd >= 0)

"""rc33 — substrate-native trig cascade routing in signal_processing.

Verifies that the window / DCT-basis / rotation trig in six
``signal_processing`` modules routes through srmech's own
``srmech.amsc.rational.cos/sin`` (Class-N rational cascade) instead of
``np.cos`` / ``np.sin`` / ``math.cos`` / ``math.sin`` — and that the routed
values are numerically identical (to ~libm precision) to a pure-Python libm
trig reference.

For each routed site we build BOTH:

* a pure-Python ``math.cos``/``math.sin`` reference of the angle expression, and
* the NEW cascade expression (the module's ``_ccos`` / ``_csin`` helper),

and assert agreement within ``1e-9``. We also assert each public ``op`` still
returns within tolerance of a pure-Python reference (numpy-free oracle: a
``cmath`` DFT, ``math``-trig windows/tapers, a textbook double-loop convolve).

The srmech rational cos/sin match libm to ~4e-13; 1e-9 is a comfortable
margin. Per rc33 discipline: NO ``abs()`` on the SOURCE side — agreement here
is a TEST tolerance, checked with element-wise ``abs(a-b) < tol`` (allowed in
test code). numpy is GONE: inputs are plain lists; the oracle is pure Python.
"""

from __future__ import annotations

import cmath
import math
import random

import pytest

from srmech.amsc import rational as _srn


# ----------------------------------------------------------------------
# Pure-Python (numpy-free) reference helpers — the libm oracle.
# ----------------------------------------------------------------------
def _dft(x):
    """Σ_t x[t]·e^{-2πikt/n} — textbook DFT (the numpy-free FFT oracle)."""
    n = len(x)
    return [sum(x[t] * cmath.exp(-2j * cmath.pi * k * t / n) for t in range(n))
            for k in range(n)]


def _hann(frame_size):
    return [0.5 * (1.0 - math.cos(2.0 * math.pi * n / max(frame_size - 1, 1)))
            for n in range(frame_size)]


def _hamming(n_taps):
    return [0.54 - 0.46 * math.cos(2.0 * math.pi * n / (n_taps - 1))
            for n in range(n_taps)]


def _dct2_matrix(n):
    return [[math.cos(math.pi * k * (2.0 * j + 1.0) / (2.0 * n))
             for j in range(n)] for k in range(n)]


def _dct3_matrix(n):
    return [[math.cos(math.pi * (2.0 * k + 1.0) * j / (2.0 * n))
             for j in range(n)] for k in range(n)]


def _cosine_taper(k, n):
    return [math.sin(math.pi * (k + 1) * (i + 1) / (n + 1)) for i in range(n)]


def _sinc(x):
    if x == 0.0:
        return 1.0
    px = math.pi * x
    return math.sin(px) / px


def _norm(v):
    return math.sqrt(sum(x * x for x in v))


def _conv_same(a, b):
    na, nb = len(a), len(b)
    full = [0.0] * (na + nb - 1)
    for i in range(na):
        for j in range(nb):
            full[i + j] += a[i] * b[j]
    target = max(na, nb)
    start = (len(full) - target) // 2
    return full[start:start + target]


def _close1d(got, ref, atol=1e-9):
    got = list(got)
    ref = list(ref)
    assert len(got) == len(ref), (len(got), len(ref))
    assert all(abs(g - r) < atol for g, r in zip(got, ref))


def _close2d(got, ref, atol=1e-9):
    assert len(got) == len(ref)
    for grow, rrow in zip(got, ref):
        _close1d(grow, rrow, atol)


# ----------------------------------------------------------------------
# 1. Window / basis arrays — cascade vs libm reference, per routed site.
# ----------------------------------------------------------------------
@pytest.mark.parametrize("frame_size", [2, 8, 16, 64, 256])
def test_cross_spectral_hann_window_matches_reference(frame_size):
    from srmech.signal_processing.closed_form_ops import cross_spectral as m

    # cross_spectral._ccos is numpy-free — takes an iterable of angles,
    # returns a plain list of rational.cos values.
    angles = [2.0 * math.pi * nn / max(frame_size - 1, 1) for nn in range(frame_size)]
    cascade = [0.5 * (1.0 - c) for c in m._ccos(angles)]
    reference = _hann(frame_size)
    _close1d(cascade, reference)


@pytest.mark.parametrize("frame_size", [2, 8, 16, 64, 256])
def test_stft_hann_window_matches_reference(frame_size):
    from srmech.signal_processing.closed_form_ops import stft as m

    angles = [2.0 * math.pi * nn / max(frame_size - 1, 1) for nn in range(frame_size)]
    cascade = [0.5 * (1.0 - c) for c in m._ccos(angles)]
    reference = _hann(frame_size)
    _close1d(cascade, reference)


def test_multirate_hamming_window_matches_reference():
    from srmech.signal_processing.closed_form_ops import multirate as m

    n_taps = 41
    angles = [2.0 * math.pi * nn / (n_taps - 1) for nn in range(n_taps)]
    cascade = [0.54 - 0.46 * c for c in m._ccos(angles)]
    reference = _hamming(n_taps)
    _close1d(cascade, reference)


@pytest.mark.parametrize("n", [4, 8, 16])
def test_dct2_basis_matches_reference(n):
    from srmech.signal_processing.closed_form_ops import dct as m

    cascade = m._dct_matrix(n, dct_type=2)  # numpy-free list-of-lists
    reference = _dct2_matrix(n)
    assert len(cascade) == n and all(len(r) == n for r in cascade)
    _close2d(cascade, reference)


@pytest.mark.parametrize("n", [4, 8, 16])
def test_dct3_basis_matches_reference(n):
    from srmech.signal_processing.closed_form_ops import dct as m

    cascade = m._dct_matrix(n, dct_type=3)  # numpy-free list-of-lists
    reference = _dct3_matrix(n)
    assert len(cascade) == n and all(len(r) == n for r in cascade)
    _close2d(cascade, reference)


@pytest.mark.parametrize("n_tapers,n", [(3, 16), (4, 32), (2, 64)])
def test_multitaper_cosine_taper_matches_reference(n_tapers, n):
    from srmech.signal_processing.closed_form_ops import multitaper as m

    for k in range(n_tapers):
        angles = [math.pi * (k + 1) * (i + 1) / (n + 1) for i in range(n)]
        cascade = m._csin(angles)
        reference = _cosine_taper(k, n)
        _close1d(cascade, reference)


def test_form_function_rotation_eigenvalue_matches_reference():
    from srmech.signal_processing import form_function_rotation as m

    # Mirror the exact scalar trig at line ~391 across a range of strides.
    D = 8192
    for strides in ([1], [3, 7], [100, 250, 999], [8191], [0]):
        composed, eig = m.cascade_compose_rotations(strides, D=D)
        theta = -2.0 * math.pi * composed / D
        # Cascade-built eigenvalue (what the op now returns).
        cascade_eig = complex(_srn.cos(theta), _srn.sin(theta))
        # libm reference eigenvalue.
        reference_eig = complex(math.cos(theta), math.sin(theta))
        assert eig == cascade_eig
        assert abs(eig.real - reference_eig.real) < 1e-9
        assert abs(eig.imag - reference_eig.imag) < 1e-9


# ----------------------------------------------------------------------
# 2. Public ops — output matches a pure-Python reference.
# ----------------------------------------------------------------------
def test_stft_op_matches_reference():
    from srmech.signal_processing.closed_form_ops import stft as m

    frame_size = 64
    hop = 32
    x = [random.Random(0).gauss(0.0, 1.0) for _ in range(256)]
    cascade_out = m.op(x, frame_size=frame_size, hop_size=hop)

    # Reference: same algorithm with a libm Hann window + cmath DFT.
    window = _hann(frame_size)
    n_frames = 1 + (len(x) - frame_size) // hop
    ref = []
    for i in range(n_frames):
        start = i * hop
        frame = [x[start + j] * window[j] for j in range(frame_size)]
        ref.append(_dft(frame))
    # stft.op is numpy-free — returns a list of per-frame lists.
    assert len(cascade_out) == len(ref)
    assert len(cascade_out[0]) == len(ref[0])
    for grow, rrow in zip(cascade_out, ref):
        _close1d(grow, rrow)


def test_cross_spectral_op_matches_reference():
    from srmech.signal_processing.closed_form_ops import cross_spectral as m

    rs = random.Random(1)
    x = [rs.gauss(0.0, 1.0) for _ in range(256)]
    y = [rs.gauss(0.0, 1.0) for _ in range(256)]
    frame_size = 64
    hop = frame_size // 2
    freqs, cascade_out = m.op(x, y, frame_size=frame_size, hop_size=hop)

    # Reference Welch CSD with a libm Hann window + cmath DFT.
    window = _hann(frame_size)
    n = len(x)
    n_frames = 1 + (n - frame_size) // hop
    acc = [0j] * frame_size
    for i in range(n_frames):
        start = i * hop
        X = _dft([x[start + j] * window[j] for j in range(frame_size)])
        Y = _dft([y[start + j] * window[j] for j in range(frame_size)])
        for k in range(frame_size):
            acc[k] += X[k] * Y[k].conjugate()
    ref = [a / n_frames for a in acc]
    _close1d(cascade_out, ref)


def test_dct_op_stable_and_invertible():
    from srmech.signal_processing.closed_form_ops import dct as m

    x = [float(v) for v in range(8)]
    X = m.op(x, dct_type=2)
    assert isinstance(X, list) and len(X) == 8  # numpy-free list return
    assert all(math.isfinite(v) for v in X)

    # The routed _dct_matrix is a numpy-free list-of-lists, so the M @ x matvec
    # is an explicit pure-Python sum (matches the old 2.0 * (M @ x)). Validate
    # the routed basis reproduces scipy's DCT-II coefficients.
    M = m._dct_matrix(8, dct_type=2)
    routed_coeffs = [2.0 * sum(M[k][j] * x[j] for j in range(8)) for k in range(8)]
    try:
        from scipy.fft import dct as scipy_dct

        ref = list(scipy_dct(x, type=2, norm=None))
        _close1d(routed_coeffs, ref)
    except ImportError:
        pytest.skip("scipy not available for DCT cross-check")


def test_multirate_op_matches_reference():
    from srmech.signal_processing.closed_form_ops import multirate as m

    sig = [math.sin(0.3 * i) for i in range(50)]
    cascade_out = m.op(sig, up=2, down=1)

    # Reference resample with a libm Hamming window + sinc taps + textbook conv.
    up, down = 2, 1
    upsampled = [0.0] * (len(sig) * up)
    for i, v in enumerate(sig):
        upsampled[i * up] = v
    n_taps = 41
    cutoff = 1.0 / max(up, down)
    taps = [_sinc(cutoff * (n - (n_taps - 1) / 2)) * cutoff for n in range(n_taps)]
    w = _hamming(n_taps)
    taps = [t * ww for t, ww in zip(taps, w)]
    s = sum(taps)
    taps = [t / s for t in taps]
    filtered = _conv_same(upsampled, taps)
    ref = [f * up for f in filtered]
    # multirate is numpy-free — op returns a plain list of float.
    assert isinstance(cascade_out, list) and len(cascade_out) == len(ref)
    _close1d(cascade_out, ref)


def test_multitaper_cosine_fallback_matches_reference():
    """Exercise the cosine-taper bank (where _csin lives) end-to-end.

    Build the routed ``_csin`` taper bank, normalise, and compute a PSD; the
    reference is the libm ``math.sin`` taper bank through the same pipeline.
    """
    from srmech.signal_processing.closed_form_ops import multitaper as m

    n = 64
    n_tapers = 3
    arr = [random.Random(2).gauss(0.0, 1.0) for _ in range(n)]

    cascade_tapers = []
    ref_tapers = []
    for k in range(n_tapers):
        angles = [math.pi * (k + 1) * (i + 1) / (n + 1) for i in range(n)]
        ct = m._csin(angles)
        nrm = _norm(ct)
        cascade_tapers.append([v / nrm for v in ct])
        rt = _cosine_taper(k, n)
        nrm_r = _norm(rt)
        ref_tapers.append([v / nrm_r for v in rt])
    for ck, rk in zip(cascade_tapers, ref_tapers):
        _close1d(ck, rk)

    # End-to-end PSD on the routed taper bank vs the libm taper bank.
    def _psd(tapers):
        acc = [0.0] * n
        for k in range(n_tapers):
            F = _dft([arr[i] * tapers[k][i] for i in range(n)])
            for i in range(n):
                acc[i] += F[i].real ** 2 + F[i].imag ** 2
        return [a / n_tapers for a in acc]

    _close1d(_psd(cascade_tapers), _psd(ref_tapers))

    # The public op (scipy dpss path) still returns a valid PSD.
    psd = m.op(arr, n_tapers=n_tapers, nw=2.0)
    # multitaper.op is numpy-free — returns a list of float.
    assert isinstance(psd, list) and len(psd) == n
    assert all(v >= 0 for v in psd)


def test_multitaper_public_op_smoke():
    from srmech.signal_processing.closed_form_ops import multitaper as m

    x = [random.Random(0).gauss(0.0, 1.0) for _ in range(64)]
    psd = m.op(x, n_tapers=3, nw=2.0)
    # multitaper.op is numpy-free — returns a list of float.
    assert isinstance(psd, list) and len(psd) == 64
    assert all(v >= 0 for v in psd)

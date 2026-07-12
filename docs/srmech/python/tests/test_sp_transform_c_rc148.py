"""rc148 (BATCH B4a — sp_transform part 1, the FFT-spectral family).

The 5 NUMERIC DSP transform ops — ``dct`` / ``stft`` / ``spectrogram`` /
``cross_spectral`` / ``multitaper`` — move ``python_only_debt →
composition_of_c`` by composing the rc139 c_dispatched numeric FFT foundation
``srmech_fft_c128`` (the 4 windowed/tapered ops, via ``spectral_cascades.fft``)
and the c_dispatched dense matmul ``srmech_dense_matmul_complex`` (``dct``, via
``mat_matvec``). This suite proves:

1. **VALUE oracles** — each op computes the mathematically-correct transform
   (independent of the C-vs-pure question): DCT-II vs a naive cosine sum, the
   DCT-II∘III round-trip identity, per-frame DFT Parseval for STFT /
   spectrogram, auto-coherence ≡ 1 for cross_spectral, and a peak-at-injected-
   frequency + non-negativity check for the multitaper PSD.
2. **WITHIN-TOL native == pure** — each op's C-dispatched path matches its own
   forced-pure fallback (native FFT / matmul monkeypatched OFF) to reldiff ≤
   1e-9. This is a **differential NUMERIC** contract (float DSP), **NOT**
   byte-identity: the FFT-then-window / matmul float accumulations can FMA-fuse
   ~1 ULP on some platforms (macOS clang), so byte-equality is not claimed —
   the SAME classification as the F1 FFT / F2 SVD numeric foundations.

This module is **numpy-free** (a test for a numpy-free surface must itself be
numpy-free) — the reference maths is stdlib ``math`` / ``cmath`` only.
"""

from __future__ import annotations

import cmath
import math
import random

import pytest

from srmech.amsc import _native
from srmech.signal_processing.closed_form_ops import (
    cross_spectral,
    dct,
    multitaper,
    spectrogram,
    stft,
)

# native availability (the differential tests run regardless — with native
# absent, forced-pure == default so reldiff is trivially 0; they still guard
# the pure path is complete + the dispatch wiring does not change the value).
_HAS_FFT = _native.has_native_fft_c128()
_HAS_MATMUL = (
    _native.HAS_NATIVE
    and _native.LIB is not None
    and hasattr(_native.LIB, "srmech_dense_matmul_complex")
)


# ----------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------

def _reldiff(a, b):
    """max|a-b| / max|a| — the relative sup-norm error over complex/real seqs."""
    a = [complex(z) for z in a]
    b = [complex(z) for z in b]
    scale = max((abs(z) for z in a), default=1.0) or 1.0
    worst = max((abs(za - zb) for za, zb in zip(a, b)), default=0.0)
    return worst / scale


def _flat(m):
    """Flatten a list-of-lists (STFT matrix) or list into one complex list."""
    out = []
    for r in m:
        if isinstance(r, (list, tuple)):
            out.extend(complex(z) for z in r)
        else:
            out.append(complex(r))
    return out


def _rand_real(n, seed):
    rng = random.Random(seed)
    return [rng.uniform(-3.0, 3.0) for _ in range(n)]


def _naive_dft(x):
    """Independent O(N^2) forward DFT via stdlib cmath (no FFT, no numpy)."""
    n = len(x)
    return [
        sum(x[j] * cmath.exp(-2j * math.pi * (k * j) / n) for j in range(n))
        for k in range(n)
    ]


# ======================================================================
# DCT — value oracle + round-trip + native==pure
# ======================================================================

def _naive_dct2(x):
    """scipy ``dct(x, type=2, norm=None)`` reference: y_k = 2 Σ_j x_j cos(...)."""
    n = len(x)
    return [
        2.0 * sum(x[j] * math.cos(math.pi * k * (2 * j + 1) / (2 * n))
                  for j in range(n))
        for k in range(n)
    ]


@pytest.mark.parametrize("n", [1, 2, 4, 7, 8, 16, 31])
def test_dct2_value_oracle(n):
    """DCT-II matches an INDEPENDENT naive cosine sum (value correctness)."""
    x = _rand_real(n, seed=100 + n)
    got = dct.op(x, dct_type=2)
    ref = _naive_dct2(x)
    assert _reldiff(ref, got) < 1e-9, f"n={n} dct-II vs naive cosine sum"


@pytest.mark.parametrize("n", [2, 4, 8, 16, 32])
def test_dct_roundtrip_identity(n):
    """DCT-III ∘ DCT-II (norm=None) reconstructs 2N·x — the exact inverse
    relation (the value oracle that pins the DCT-III first-term weight)."""
    x = _rand_real(n, seed=7 * n + 1)
    y = dct.op(x, dct_type=2)
    z = dct.op(y, dct_type=3)
    ref = [2.0 * n * xi for xi in x]
    assert _reldiff(ref, z) < 1e-9, f"n={n} dct3(dct2(x)) != 2N x"


@pytest.mark.parametrize("dct_type", [2, 3])
@pytest.mark.parametrize("n", [4, 8, 16, 31, 32])
def test_dct_native_matches_pure(monkeypatch, dct_type, n):
    """The C-dispatched DCT matvec (srmech_dense_matmul_complex via mat_matvec)
    matches the forced-pure triple-loop within-tol — NOT byte-identical."""
    x = _rand_real(n, seed=2000 + n + dct_type)
    disp = dct.op(x, dct_type=dct_type)
    monkeypatch.setattr(_native, "HAS_NATIVE", False)  # force pure matmul
    pure = dct.op(x, dct_type=dct_type)
    assert _reldiff(pure, disp) < 1e-9, f"n={n} type={dct_type} dct native!=pure"


def test_dct_2d_native_matches_pure(monkeypatch):
    """2-D DCT (per-row + per-column) also dispatches + matches pure within-tol."""
    rng = random.Random(55)
    rows = [[rng.uniform(-2, 2) for _ in range(8)] for _ in range(5)]
    for axis in (-1, 0):
        disp = _flat(dct.op(rows, axis=axis))
        monkeypatch.setattr(_native, "HAS_NATIVE", False)
        pure = _flat(dct.op(rows, axis=axis))
        monkeypatch.undo()
        assert _reldiff(pure, disp) < 1e-9, f"2-D dct axis={axis} native!=pure"


# ======================================================================
# STFT — Parseval value oracle + native==pure
# ======================================================================

def _hann(nn):
    denom = max(nn - 1, 1)
    return [0.5 * (1.0 - math.cos(2.0 * math.pi * i / denom)) for i in range(nn)]


def test_stft_parseval_value_oracle():
    """Per-frame DFT Parseval: Σ_k |STFT[k]|² == N Σ_n |sig_n · w_n|². An
    independent (naive-window) energy identity that pins the STFT values."""
    fs = 16
    sig = _rand_real(64, seed=321)
    mat = stft.op(sig, frame_size=fs)
    win = _hann(fs)
    n_frames = 1 + (len(sig) - fs) // (fs // 2)
    assert len(mat) == n_frames
    for i, frame in enumerate(mat):
        start = i * (fs // 2)
        windowed = [sig[start + k] * win[k] for k in range(fs)]
        lhs = sum(z.real * z.real + z.imag * z.imag for z in frame)
        rhs = fs * sum(v * v for v in windowed)
        assert abs(lhs - rhs) <= 1e-7 * (abs(rhs) + 1.0), f"frame {i} Parseval"


@pytest.mark.parametrize("fs", [8, 16, 32])
def test_stft_native_matches_pure(monkeypatch, fs):
    sig = _rand_real(96, seed=44 + fs)
    disp = _flat(stft.op(sig, frame_size=fs))
    monkeypatch.setattr(_native, "has_native_fft_c128", lambda: False)
    pure = _flat(stft.op(sig, frame_size=fs))
    assert _reldiff(pure, disp) < 1e-9, f"fs={fs} stft native!=pure"


# ======================================================================
# spectrogram — |STFT|² value oracle + native==pure
# ======================================================================

def test_spectrogram_is_stft_magsq():
    """spectrogram == |STFT|² elementwise (the defining identity)."""
    sig = _rand_real(64, seed=99)
    sm = stft.op(sig, frame_size=16)
    sp = spectrogram.op(sig, frame_size=16)
    for row_s, row_p in zip(sm, sp):
        for z, p in zip(row_s, row_p):
            assert abs((z.real * z.real + z.imag * z.imag) - p) <= 1e-9
            assert p >= 0.0


def test_spectrogram_native_matches_pure(monkeypatch):
    sig = _rand_real(80, seed=7)
    disp = _flat(spectrogram.op(sig, frame_size=16))
    monkeypatch.setattr(_native, "has_native_fft_c128", lambda: False)
    pure = _flat(spectrogram.op(sig, frame_size=16))
    assert _reldiff(pure, disp) < 1e-9, "spectrogram native!=pure"


# ======================================================================
# cross_spectral — auto-coherence ≡ 1 value oracle + native==pure
# ======================================================================

def test_cross_spectral_autocoherence_is_one():
    """Coherence of a signal with ITSELF is 1.0 at every bin with power — the
    canonical coherence sanity oracle (Welch/Carter)."""
    sig = _rand_real(96, seed=17)
    freqs, coh = cross_spectral.op(sig, sig, frame_size=16, coherence=True)
    # every finite-power bin should read coherence 1.0 to round-off.
    seen_one = 0
    for c in coh:
        # bins with (near-)zero auto-power read 0 (eps floor); the rest read 1.
        if c > 0.5:
            assert abs(c - 1.0) < 1e-9
            seen_one += 1
    assert seen_one >= len(coh) // 2, "auto-coherence should be ~1 on most bins"


def test_cross_spectral_csd_is_real_nonneg_for_autospectrum():
    """The auto-CSD S_xx = avg(X·conj(X)) is real + non-negative (a periodogram
    is a magnitude-square average) — a value oracle independent of C-vs-pure."""
    sig = _rand_real(96, seed=23)
    _f, s_xx = cross_spectral.op(sig, sig, frame_size=16, coherence=False)
    for z in s_xx:
        z = complex(z)
        assert abs(z.imag) < 1e-9, "auto-CSD imaginary part should vanish"
        assert z.real >= -1e-9, "auto-power should be non-negative"


@pytest.mark.parametrize("fs", [8, 16, 32])
def test_cross_spectral_native_matches_pure(monkeypatch, fs):
    x = _rand_real(96, seed=200 + fs)
    y = _rand_real(96, seed=900 + fs)
    fd, disp = cross_spectral.op(x, y, frame_size=fs)
    monkeypatch.setattr(_native, "has_native_fft_c128", lambda: False)
    fp, pure = cross_spectral.op(x, y, frame_size=fs)
    assert fd == fp, "fftfreq bins should be identical (pure integer cascade)"
    assert _reldiff(pure, disp) < 1e-9, f"fs={fs} cross_spectral native!=pure"


# ======================================================================
# multitaper — spectral-peak value oracle + native==pure
# ======================================================================

def test_multitaper_peak_and_nonneg():
    """The multitaper PSD of a pure cosine at bin k0 peaks near k0 in the lower
    half-spectrum, and every value is a non-negative power — a spectral value
    oracle (Slepian/Thomson)."""
    n = 64
    k0 = 8
    sig = [math.cos(2.0 * math.pi * k0 * i / n) for i in range(n)]
    psd = multitaper.op(sig, n_tapers=4, nw=4.0)
    assert len(psd) == n
    for v in psd:
        assert v >= -1e-12, "PSD must be non-negative"
    half = psd[1: n // 2 + 1]
    peak_bin = 1 + max(range(len(half)), key=lambda i: half[i])
    assert abs(peak_bin - k0) <= 1, f"multitaper peak {peak_bin} not near k0={k0}"


@pytest.mark.parametrize("n", [32, 64, 100])
def test_multitaper_native_matches_pure(monkeypatch, n):
    sig = _rand_real(n, seed=500 + n)
    disp = list(multitaper.op(sig, n_tapers=4, nw=4.0))
    monkeypatch.setattr(_native, "has_native_fft_c128", lambda: False)
    pure = list(multitaper.op(sig, n_tapers=4, nw=4.0))
    assert _reldiff(pure, disp) < 1e-9, f"n={n} multitaper native!=pure"


# ======================================================================
# dispatch presence (informational — the value/parity oracles above are the
# real gate; these just record whether the native path was exercised)
# ======================================================================

def test_native_paths_available_report():
    """Not a hard gate: records which C paths back this batch (fft_c128 for the
    4 windowed ops, dense_matmul for dct). When both are absent the pure path is
    the complete alternative and every test above still passes."""
    assert isinstance(_HAS_FFT, bool)
    assert isinstance(_HAS_MATMUL, bool)

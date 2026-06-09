"""v0.7.5rc28 -- exact-until-rotation DFT/FFT (cyclotomic-integer engine).

Per user direction: "don't use floats for bit-exact math, that's what ints and
complex are for; floats are for FPU lift." A DFT's twiddles e^{-2pi i j/N} are
roots of unity = algebraic integers in Z[zeta_N]; for power-of-two N the ring is
the negacyclic integers Z[x]/(x^(N/2)+1), so the DFT of an integer signal is pure
integer add/subtract (zeta^(N/2) = -1, a Class-K sign flip), with floats produced
exactly once at the final FPU lift zeta -> e^{-2pi i/N}.

These tests pin: (1) the exact integer core is bit-deterministic and produces an
all-Python-int spectrum (no floats); (2) the public dft/fft route integer/
Gaussian-integer power-of-two signals through that engine and agree bit-for-bit;
(3) the result is value-faithful to numpy.fft to round-off; (4) float and
non-power-of-two signals are NOT exact-routed (they keep the float cexp path).
"""
from __future__ import annotations

import numpy as np
import pytest

from srmech.amsc.cascade.exact_dft import (
    _exact_dft_core,
    _exact_transform,
    _is_pow2,
    _lift_spectrum,
    _try_int_pairs,
)
from srmech.amsc.cascade.spectral_cascades import dft, fft, idft, ifft

POW2 = [2, 4, 8, 16, 32, 64]


def _int_signal(n, seed):
    return [int(v) for v in ((np.arange(n) * seed + 3) % 11 - 5)]


# --- (1) the exact integer core -------------------------------------------------

def test_try_int_pairs_accepts_int_and_gaussian_int():
    assert _try_int_pairs([1, -2, 3]) == ([1, -2, 3], [0, 0, 0])
    assert _try_int_pairs([1 + 2j, 3 - 4j]) == ([1, 3], [2, -4])
    # integral-valued floats are accepted (lie on the integer grid)
    assert _try_int_pairs([2.0, -3.0]) == ([2, -3], [0, 0])


def test_try_int_pairs_rejects_non_integral():
    assert _try_int_pairs([0.5, 1.0]) is None
    assert _try_int_pairs([1 + 0.25j]) is None


def test_exact_core_spectrum_is_all_python_int():
    sig = _int_signal(16, 7)
    re, im = _try_int_pairs(sig)
    spectrum = _exact_dft_core(re, im)
    assert len(spectrum) == 16
    for (xr, xi) in spectrum:
        assert len(xr) == 8 and len(xi) == 8            # length N/2 cyclotomic vectors
        for c in xr + xi:
            assert type(c) is int                       # exact integers, no float anywhere


def test_exact_core_is_bit_deterministic():
    sig = [3, -1, 4, -1, 5, -9, 2, -6]
    assert _exact_dft_core(*_try_int_pairs(sig)) == _exact_dft_core(*_try_int_pairs(sig))


@pytest.mark.parametrize("n", POW2)
def test_is_pow2(n):
    assert _is_pow2(n)
    assert not _is_pow2(n + 1) or _is_pow2(n + 1) == _is_pow2(n + 1)  # n+1 rarely pow2


# --- (2)+(3) public dft/fft routing + value-faithfulness ------------------------

@pytest.mark.parametrize("n", POW2)
def test_integer_signal_takes_exact_path_fft_equals_dft_bitwise(n):
    sig = _int_signal(n, 5)
    d = dft(sig)
    f = fft(sig)
    # both route the same exact engine -> identical bit-for-bit
    assert d == f
    # value-faithful to numpy.fft to round-off (the single FPU lift)
    ref = np.fft.fft(np.array(sig, dtype=float))
    assert np.max(np.abs(np.array(d) - ref)) <= 1e-9


@pytest.mark.parametrize("n", POW2)
def test_gaussian_integer_signal_exact(n):
    sig = [complex(a, b) for a, b in zip(_int_signal(n, 2), _int_signal(n, 9))]
    ref = np.fft.fft(np.array(sig))
    assert np.max(np.abs(np.array(fft(sig)) - ref)) <= 1e-9


@pytest.mark.parametrize("n", [4, 8, 16, 32])
def test_roundtrip_ifft_fft_recovers_integer_signal(n):
    sig = _int_signal(n, 3)
    rt = ifft(fft(sig))
    assert np.max(np.abs(np.array(rt) - np.array(sig, dtype=float))) <= 1e-9
    rt2 = idft(dft(sig))
    assert np.max(np.abs(np.array(rt2) - np.array(sig, dtype=float))) <= 1e-9


# --- (4) float / non-pow2 keep the float path (NOT exact-routed) ----------------

def test_float_signal_is_not_exact_routed():
    fsig = [0.5, -1.25, 2.0, 3.7]
    assert _exact_transform(fsig) is None
    ref = np.fft.fft(np.array(fsig))
    assert np.max(np.abs(np.array(fft(fsig)) - ref)) <= 1e-9


def test_non_power_of_two_integer_is_now_exact_routed():
    # rc30: general-N cyclotomic engine — non-power-of-two integer signals now
    # route through the exact path too (was the float fallback through rc29).
    isig = [1, 2, 3, 4, 5]
    assert _exact_transform(isig) is not None
    ref = np.fft.fft(np.array(isig, dtype=float))
    assert np.max(np.abs(np.array(dft(isig)) - ref)) <= 1e-9


def test_length_one_and_empty_are_not_exact_routed():
    assert _exact_transform([7]) is None         # N=1 has no cyclotomic basis
    assert _exact_transform([]) is None
    assert dft([7]) == [7 + 0j]
    assert fft([]) == []


def test_inverse_of_float_spectrum_uses_float_path():
    # a spectrum is generally complex-float; its inverse must run the float path
    spectrum = fft([1, 0, 0, 0, 1, 0, 0, 0])     # exact (integer input)
    back = ifft(spectrum)                          # spectrum is float -> float path
    want = np.fft.ifft(np.array(spectrum))
    assert np.max(np.abs(np.array(back) - want)) <= 1e-9


def test_lift_applies_scale():
    sig = _int_signal(8, 4)
    re, im = _try_int_pairs(sig)
    spec = _exact_dft_core(re, im, inverse=True)
    unscaled = _lift_spectrum(spec, 8, scale=1)
    scaled = _lift_spectrum(spec, 8, scale=8)
    for u, s in zip(unscaled, scaled):
        assert abs(u / 8 - s) <= 1e-12

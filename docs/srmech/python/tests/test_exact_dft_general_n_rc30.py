"""v0.7.5rc30 -- general-N cyclotomic exact DFT (non-power-of-two lengths).

rc28/rc29 handled power-of-two N via the negacyclic ring (zeta^(N/2) = -1). rc30
extends the exact-until-rotation DFT to ANY length N via the full cyclotomic ring
Z[zeta_N] = Z[x]/Phi_N(x): each twiddle zeta^(nk mod N) is reduced to the
length-phi(N) power basis with pure integer arithmetic, and the single FPU lift
evaluates zeta = e^{-2pi i/N}. Python-only arbitrary-precision (no fixed-width C
twin) — the bignum_reference shape. dft/fft now route ALL integer / Gaussian-
integer signals (any N >= 2) through the exact path.

numpy is GONE from srmech — these tests run and pass with numpy NOT installed.
The lift oracle is a pure-cmath DFT-by-definition; the totient uses math.gcd.
"""
from __future__ import annotations

import cmath
import math

import pytest

from srmech.amsc.cascade.exact_dft import (
    _cyclotomic_reduction,
    _exact_transform,
    exact_dft,
    exact_idft,
    lift,
)
from srmech.amsc.cascade.spectral_cascades import dft, fft

GENERAL_N = [3, 5, 6, 7, 9, 10, 11, 12, 14, 15, 18, 24]


def _int_signal(n, seed):
    return [(i * seed + 3) % 11 - 5 for i in range(n)]


def _totient(n):
    return sum(1 for k in range(1, n + 1) if math.gcd(k, n) == 1)


def _dft_ref(x, inverse=False):
    """DFT by definition via cmath: X[k] = Σ_n x[n]·e^{∓2πi·kn/N} (÷N if inverse)."""
    n = len(x)
    sign = 1.0 if inverse else -1.0
    out = []
    for k in range(n):
        acc = 0j
        for idx in range(n):
            acc += complex(x[idx]) * cmath.exp(sign * 2j * math.pi * k * idx / n)
        out.append(acc / n if inverse else acc)
    return out


def _max_abs_diff(got, want):
    return max((abs(complex(g) - complex(w)) for g, w in zip(got, want)), default=0.0)


# --- the cyclotomic machinery ---------------------------------------------------

@pytest.mark.parametrize("n", GENERAL_N + [2, 4, 8, 16])
def test_reduction_degree_is_totient(n):
    _table, deg = _cyclotomic_reduction(n)
    assert deg == _totient(n)


def test_known_cyclotomic_polynomials():
    # The reduction rule zeta^d = -(phi_0 + ... + phi_{d-1} zeta^{d-1}) is the
    # table's first wraparound row (T[d]); check it against textbook Phi_N.
    # Phi_6 = x^2 - x + 1  -> zeta^2 = x - 1 = -1 + zeta  -> T[2] = (-1, 1)
    table6, deg6 = _cyclotomic_reduction(6)
    assert deg6 == 2 and table6[2] == (-1, 1)
    # Phi_12 = x^4 - x^2 + 1 -> zeta^4 = x^2 - 1 -> T[4] = (-1, 0, 1, 0)
    table12, deg12 = _cyclotomic_reduction(12)
    assert deg12 == 4 and table12[4] == (-1, 0, 1, 0)


def test_reduction_table_is_cached_and_deterministic():
    a = _cyclotomic_reduction(15)
    b = _cyclotomic_reduction(15)
    assert a is b                        # lru_cache identity
    assert a[1] == _totient(15)


# --- public exact_dft for general N ---------------------------------------------

@pytest.mark.parametrize("n", GENERAL_N)
def test_exact_dft_general_integer_spectrum(n):
    sig = _int_signal(n, 5)
    spec = exact_dft(sig)
    assert len(spec) == n
    deg = _totient(n)
    for (xr, xi) in spec:
        assert len(xr) == deg and len(xi) == deg
        for c in xr + xi:
            assert type(c) is int        # exact integers, no float
    assert _max_abs_diff(lift(spec), _dft_ref(sig)) <= 1e-9


@pytest.mark.parametrize("n", [6, 9, 10, 12, 15])
def test_exact_dft_general_gaussian_integer(n):
    sig = [complex(a, b) for a, b in zip(_int_signal(n, 2), _int_signal(n, 7))]
    assert _max_abs_diff(lift(exact_dft(sig)), _dft_ref(sig)) <= 1e-9


@pytest.mark.parametrize("n", [6, 9, 12, 15])
def test_exact_dft_general_determinism(n):
    sig = _int_signal(n, 4)
    assert exact_dft(sig) == exact_dft(sig)


@pytest.mark.parametrize("n", [6, 9, 12])
def test_general_n_roundtrip(n):
    sig = _int_signal(n, 3)
    rt = _dft_ref(lift(exact_dft(sig)), inverse=True)
    assert _max_abs_diff([v.real for v in rt], [float(v) for v in sig]) <= 1e-9
    # exact_idft is exact_dft with the conjugate exponent
    assert exact_idft(sig) == exact_dft(sig, inverse=True)


# --- dft/fft now route all integer lengths exact --------------------------------

@pytest.mark.parametrize("n", GENERAL_N)
def test_dft_fft_route_general_integer_exact(n):
    sig = _int_signal(n, 6)
    assert _exact_transform(sig) is not None
    assert _max_abs_diff(dft(sig), _dft_ref(sig)) <= 1e-9
    # fft falls back to dft for non-power-of-2, so they agree
    assert _max_abs_diff(fft(sig), dft(sig)) <= 1e-12


def test_float_general_n_still_float_path():
    fsig = [0.5, 1.5, 2.5, 3.5, 4.5]       # non-integer N=5 -> float path
    assert _exact_transform(fsig) is None
    assert _max_abs_diff(dft(fsig), _dft_ref(fsig)) <= 1e-9


def test_exact_dft_still_rejects_length_one():
    with pytest.raises(ValueError):
        exact_dft([7])
    with pytest.raises(ValueError):
        exact_dft([])

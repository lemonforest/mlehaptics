"""rc62 — the np.fft.* drain: array-aware fft/ifft/rfft/fftfreq carriers.

The numpy-removal `linalg_fft` sweep's `np.fft.*` half. With numpy removed
entirely (#564) the carriers are a numpy-FREE 1-D path:
``signal_processing/_fft_carrier.{fft,ifft,rfft,fftfreq}`` operate on plain
Python sequences and return ``list[complex]`` (``fft`` / ``ifft`` / ``rfft``) or
``list[float]`` (``fftfreq``). The 1-D default-axis cascade is the only shape
supported — an n-D input or a non-default axis now raises ``ValueError``
numpy-free (the old NumPy ``moveaxis`` / ``reshape`` carrier is gone). ``rfft``
rejects complex input with ``TypeError`` (mirroring NumPy's historical
behaviour). The substrate-native FFT cascade ``spectral_cascades.fft`` /
``.ifft`` is what these lift.

This pins (with a hand-rolled DFT-by-definition oracle — NO numpy):

1. ``_fft_carrier.{fft,ifft}`` value-faithful to the DFT/IDFT definition over
   real + complex 1-D inputs, including ``n`` pad/truncate;
2. ``rfft`` == ``fft(x)[:n//2 + 1]`` (the half-spectrum slice it computes);
3. n-D input / non-default axis raise ``ValueError``;
4. ``rfft`` rejects complex input (``TypeError``);
5. ``fftfreq`` == the integer-bin / ``n*d`` formula;
6. the routed Path ops produce that same value-faithful output and the
   Path-A == Path-B cascade identity holds exactly.
"""

from __future__ import annotations

import cmath
import math
import random

import pytest

from srmech.signal_processing import _fft_carrier as fc

_TOL = 1e-9


# ---------------------------------------------------------------------------
# DFT-by-definition oracles (stdlib cmath; X[k] = Σ_n x[n]·e^{-2πi kn/N})
# ---------------------------------------------------------------------------

def _resize(x, n):
    """numpy fft n= semantics: zero-pad or truncate the sequence to length n."""
    if n is None:
        return list(x)
    x = list(x)[:n]
    if len(x) < n:
        x = x + [0.0] * (n - len(x))
    return x


def _dft(x, n=None):
    x = [complex(v) for v in _resize(x, n)]
    N = len(x)
    return [
        sum(x[m] * cmath.exp(-2j * math.pi * k * m / N) for m in range(N))
        for k in range(N)
    ]


def _idft(x, n=None):
    x = [complex(v) for v in _resize(x, n)]
    N = len(x)
    return [
        sum(x[m] * cmath.exp(2j * math.pi * k * m / N) for m in range(N)) / N
        for k in range(N)
    ]


def _rdft(x, n=None):
    """rfft = first n//2 + 1 bins of the full DFT (the half-spectrum)."""
    full = _dft(x, n)
    nn = len(full)
    return full[: nn // 2 + 1]


def _fftfreq(n, d=1.0):
    """numpy fftfreq: [0,1,..,⌈n/2⌉-1, -⌊n/2⌋,..,-1] / (n*d)."""
    val = 1.0 / (n * d)
    out = []
    half = (n - 1) // 2 + 1
    out.extend(i * val for i in range(half))
    out.extend((i - n) * val for i in range(half, n))
    return out


def _close_seq(got, ref, tol=_TOL):
    got = list(got)
    ref = list(ref)
    assert len(got) == len(ref), f"length {len(got)} != {len(ref)}"
    for g, r in zip(got, ref):
        assert abs(complex(g) - complex(r)) < tol, f"{g} != {r}"


def _rand_complex(n, seed):
    rng = random.Random(seed)
    return [complex(rng.gauss(0, 1), rng.gauss(0, 1)) for _ in range(n)]


def _rand_real(n, seed):
    rng = random.Random(seed)
    return [rng.gauss(0, 1) for _ in range(n)]


# ---------------------------------------------------------------------------
# 1. carriers == DFT-by-definition (the contract the routes rely on)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("N", [2, 3, 5, 8, 9, 16, 17, 40, 64])
@pytest.mark.parametrize("n", [None, "same", "pad", "trunc"])
def test_fft_ifft_carrier_matches_dft_1d(N, n):
    x = _rand_complex(N, 100 + N)
    nn = {None: None, "same": N, "pad": N + 5, "trunc": max(1, N - 3)}[n]
    _close_seq(fc.fft(x, nn), _dft(x, nn))
    _close_seq(fc.ifft(x, nn), _idft(x, nn))


@pytest.mark.parametrize("N", [2, 3, 8, 9, 16, 40, 64])
@pytest.mark.parametrize("n", [None, "same", "pad", "trunc"])
def test_rfft_carrier_matches_dft_real(N, n):
    x = _rand_real(N, 200 + N)
    nn = {None: None, "same": N, "pad": N + 4, "trunc": max(2, N - 2)}[n]
    _close_seq(fc.rfft(x, nn), _rdft(x, nn))


def test_nd_input_raises_value_error():
    # numpy removed (#564): only the 1-D default-axis cascade is supported.
    with pytest.raises(ValueError):
        fc.fft([[1.0, 2.0], [3.0, 4.0]], None, 0)
    with pytest.raises(ValueError):
        fc.ifft([[1.0, 2.0], [3.0, 4.0]], None, 0)


def test_non_default_axis_raises_value_error():
    # axis=1 is out of range for a 1-D sequence (only the default last axis is
    # supported numpy-free); axis=0 == axis=-1 for 1-D so it stays valid.
    with pytest.raises(ValueError):
        fc.fft([1.0, 2.0, 3.0, 4.0], None, 1)
    with pytest.raises(ValueError):
        fc.ifft([1.0, 2.0, 3.0, 4.0], None, 1)


def test_rfft_rejects_complex_like_numpy():
    z = [1 + 2j, 3 - 1j, 0 + 0j]
    with pytest.raises(TypeError):
        fc.rfft(z)


@pytest.mark.parametrize("n", [1, 2, 3, 4, 5, 8, 9, 16, 33, 64])
@pytest.mark.parametrize("d", [1.0, 0.5, 2.0])
def test_fftfreq_carrier_matches_formula(n, d):
    _close_seq(fc.fftfreq(n, d), _fftfreq(n, d), tol=1e-12)


def test_fft_ifft_round_trip():
    x = _rand_complex(48, 3)
    _close_seq(fc.ifft(fc.fft(x)), x)


def test_rfft_is_half_of_fft():
    # the half-spectrum identity that makes rfft valid (real input).
    x = _rand_real(64, 7)
    half = fc.rfft(x)
    full = fc.fft(x)
    _close_seq(half, full[: 64 // 2 + 1])


# ---------------------------------------------------------------------------
# 2. the routed Path ops ride the carrier (value-faithful + A==B identity)
# ---------------------------------------------------------------------------

def test_path_ops_route_through_carrier():
    from srmech.signal_processing.closed_form_ops import fft as a_fft, ifft as a_ifft, rfft as a_rfft

    x = _rand_real(40, 5)
    _close_seq(a_fft.op(x), _dft(x))
    _close_seq(a_ifft.op([complex(v) for v in x]), _idft(x))
    _close_seq(a_rfft.op(x), _rdft(x))


def test_path_a_equals_path_b_exact():
    # both Path-A and Path-B now ride the same cascade carrier -> bit-identical
    from srmech.signal_processing.closed_form_ops import rfft as a_rfft
    from srmech.signal_processing.path_b_ops import rfft as b_rfft

    x = _rand_real(64, 9)
    assert list(b_rfft.op(x)) == list(a_rfft.op(x))

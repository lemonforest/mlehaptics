"""rc139 (#743/#747 Foundation F1) — the numeric complex128 FFT C peer.

``srmech_fft_c128`` is the numeric FFT foundation the whole signal_processing
fft-family dispatches to (the C:Python parity backfill: the C surface had only
the exact-integer ``srmech_exact_dft_i64`` + ``srmech_autocorrelation_f64``, no
numeric complex FFT). This suite proves:

1. **Correctness** — the native FFT matches an INDEPENDENT naive O(N^2) DFT
   (stdlib ``cmath``, no numpy) to a tight FPU tolerance across several N,
   including PRIME N (the Bluestein chirp-z path — NOT power-of-2-only).
2. **Round-trip** — ``FFT(IFFT(x)) == x`` to tolerance (the 1/N inverse scale).
3. **Dispatch parity** — the ``spectral_cascades`` + closed_form_ops +
   path_b_ops fft-family ops dispatch to the C peer and match their own pure
   ``cexp`` cascade path (native forced OFF via monkeypatch) to tolerance.

NUMERIC (FPU-tol), not byte-exact — contrast the exact-integer exact_dft twin.
This module is **numpy-free** (a test for a numpy-free surface must itself be
numpy-free) — the reference DFT is stdlib ``cmath`` only.
"""

from __future__ import annotations

import cmath
import math
import random

import pytest

from srmech.amsc import _native
from srmech.amsc.cascade import spectral_cascades as sc

HAS_FFT_C128 = _native.has_native_fft_c128()

_native_only = pytest.mark.skipif(
    not HAS_FFT_C128,
    reason="native srmech_fft_c128 not built (pure-Python cascade is the "
           "complete alternative; the pure-path parity test still runs)",
)

# A spread of lengths: powers of two (radix-2), primes (Bluestein), and
# composite non-powers-of-two (Bluestein) — the full-coverage envelope.
_TEST_NS = [1, 2, 3, 4, 5, 7, 8, 13, 16, 17, 31, 32, 60, 61, 64, 97, 100,
            127, 128, 251, 256, 257]
_PRIMES = [3, 5, 7, 11, 13, 17, 31, 61, 97, 127, 251, 257]


def _naive_dft(x, inverse=False):
    """Independent O(N^2) DFT reference via stdlib cmath (no FFT, no numpy)."""
    n = len(x)
    if n == 0:
        return []
    s = 1.0 if inverse else -1.0
    out = []
    for k in range(n):
        acc = 0j
        for j in range(n):
            acc += x[j] * cmath.exp(s * 2j * math.pi * (k * j) / n)
        out.append(acc / n if inverse else acc)
    return out


def _reldiff(a, b):
    """max|a-b| / max|a| — the relative sup-norm error."""
    scale = max((abs(z) for z in a), default=1.0) or 1.0
    worst = max((abs(za - zb) for za, zb in zip(a, b)), default=0.0)
    return worst / scale


def _rand_complex(n, seed):
    random.seed(seed)
    return [complex(random.uniform(-4.0, 4.0), random.uniform(-4.0, 4.0))
            for _ in range(n)]


# ----------------------------------------------------------------------
# 1. native FFT vs the independent naive DFT reference (incl. prime N)
# ----------------------------------------------------------------------

@_native_only
@pytest.mark.parametrize("n", _TEST_NS)
def test_native_fft_matches_naive_dft(n):
    x = _rand_complex(n, seed=20260705 + n)
    ref = _naive_dft(x, inverse=False)
    got = _native.fft_c128_c(x, inverse=False)
    assert got is not None
    rel = _reldiff(ref, got)
    assert rel < 1e-10, f"n={n} forward reldiff {rel:.3e} vs naive DFT"


@_native_only
@pytest.mark.parametrize("n", _PRIMES)
def test_native_fft_prime_bluestein(n):
    """Explicit PRIME-N correctness — exercises the Bluestein chirp-z path."""
    x = _rand_complex(n, seed=11 + n)
    ref = _naive_dft(x, inverse=False)
    got = _native.fft_c128_c(x, inverse=False)
    assert got is not None
    rel = _reldiff(ref, got)
    assert rel < 1e-10, f"prime n={n} Bluestein reldiff {rel:.3e}"


# ----------------------------------------------------------------------
# 2. round-trip identity FFT(IFFT(x)) == x
# ----------------------------------------------------------------------

@_native_only
@pytest.mark.parametrize("n", _TEST_NS)
def test_native_fft_roundtrip_identity(n):
    x = _rand_complex(n, seed=7 * n + 3)
    fwd = _native.fft_c128_c(x, inverse=False)
    rt = _native.fft_c128_c(fwd, inverse=True)
    assert rt is not None
    rel = _reldiff(x, rt)
    assert rel < 1e-10, f"n={n} roundtrip reldiff {rel:.3e}"


@_native_only
def test_native_ifft_matches_naive(n=13):
    """The inverse transform (with the 1/N scale) matches the naive IDFT."""
    x = _rand_complex(n, seed=42)
    ref = _naive_dft(x, inverse=True)
    got = _native.fft_c128_c(x, inverse=True)
    assert got is not None
    assert _reldiff(ref, got) < 1e-10


@_native_only
def test_empty_signal():
    assert _native.fft_c128_c([], inverse=False) == []


# ----------------------------------------------------------------------
# 3. dispatch parity — the fft-family ops route to C AND match the pure path
# ----------------------------------------------------------------------

@_native_only
@pytest.mark.parametrize("n", [4, 5, 8, 12, 13, 16, 17, 31, 32, 60, 64])
def test_dispatch_matches_pure_path(monkeypatch, n):
    """spectral_cascades.fft/.dft dispatched-to-C == the pure cexp cascade."""
    x = _rand_complex(n, seed=1000 + n)
    disp_fft = sc.fft(list(x))
    disp_dft = sc.dft(list(x))
    # Force the pure path: fft_c128_c returns None when has_native_fft_c128 is
    # False, so spectral_cascades falls through to the pure cexp loop.
    monkeypatch.setattr(_native, "has_native_fft_c128", lambda: False)
    pure_fft = sc.fft(list(x))
    pure_dft = sc.dft(list(x))
    assert _reldiff(pure_fft, disp_fft) < 1e-10, f"n={n} fft dispatch!=pure"
    assert _reldiff(pure_dft, disp_dft) < 1e-10, f"n={n} dft dispatch!=pure"
    # fft and dft compute the same DFT values (fast vs direct)
    assert _reldiff(disp_dft, disp_fft) < 1e-10, f"n={n} fft!=dft"


@_native_only
@pytest.mark.parametrize("n", [8, 13, 16, 17])
def test_fft_family_ops_route_and_match(n):
    """closed_form_ops + path_b_ops fft/ifft/rfft route through the C-dispatched
    spectral_cascades core and match the independent DFT reference."""
    from srmech.signal_processing.closed_form_ops import (
        fft as cf_fft, ifft as cf_ifft, rfft as cf_rfft,
    )
    from srmech.signal_processing.path_b_ops import (
        fft as pb_fft, ifft as pb_ifft,
    )
    x = _rand_complex(n, seed=99 + n)
    ref = _naive_dft(x, inverse=False)
    for opmod in (cf_fft, pb_fft):
        got = list(opmod.op(list(x)))
        assert _reldiff(ref, got) < 1e-10, f"{opmod.__name__} n={n}"
    # inverse family
    spec = _naive_dft(x, inverse=False)
    iref = _naive_dft(spec, inverse=True)
    for opmod in (cf_ifft, pb_ifft):
        igot = list(opmod.op(list(spec)))
        assert _reldiff(iref, igot) < 1e-10, f"{opmod.__name__} inverse n={n}"
    # rfft on a REAL signal — the non-redundant Hermitian half-spectrum
    xr = [random.Random(5 + n).uniform(-3.0, 3.0) for _ in range(n)]
    rref = _naive_dft([complex(v) for v in xr], inverse=False)[: n // 2 + 1]
    rgot = list(cf_rfft.op(list(xr)))
    assert _reldiff(rref, rgot) < 1e-10, f"rfft n={n}"


# ----------------------------------------------------------------------
# 4. the PURE path always runs (native absent OR present) — the parity oracle
# ----------------------------------------------------------------------

@pytest.mark.parametrize("n", [1, 5, 8, 13, 16, 17])
def test_pure_path_matches_naive_dft(monkeypatch, n):
    """The pure-Python cascade (native forced OFF) matches the naive DFT — the
    complete alternative for no-C hosts. Runs regardless of the native lib."""
    monkeypatch.setattr(_native, "has_native_fft_c128", lambda: False)
    x = _rand_complex(n, seed=3 * n + 1)
    ref = _naive_dft(x, inverse=False)
    got = sc.fft(list(x))
    assert _reldiff(ref, got) < 1e-9, f"pure n={n} reldiff vs naive DFT"

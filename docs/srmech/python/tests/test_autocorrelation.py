"""v0.7.0rc8 — the Class-L circular autocorrelation primitive + C parity.

``srmech.amsc.cascade.autocorrelation(x)`` is the circular autocorrelation

    r[k] = Σ_i x[i] · x[(i + k) mod n],   r[0] = Σ x² = energy

— EXACTLY the Wiener-Khinchin spectral object ``r = Re(IFFT(|FFT(x)|²))``
(the circular-convolution theorem; that identity is WHY it is Class L). The
Python wrapper computes it via the fast numpy FFT; the native C peer
(``srmech_autocorrelation_f64`` in c/src/srmech_autocorr.c) computes the
DIRECT O(n²) multiply-add sum — the IDENTICAL object, JPL-clean (no FFT, no
recursion, no transcendentals).

These tests assert:
  * the FFT route equals the naive direct-sum definition (the spectral
    identity holds), to FFT round-off (~1e-12);
  * boundary cases (n == 0 -> []; n == 1 -> [x[0]²]);
  * the energy anchor r[0] == Σ x²;
  * the op is registered + discoverable as a cascade-catalog op;
  * (when HAS_NATIVE) the native direct-sum peer matches the naive
    direct sum to ~1e-12 (a compiler may contract a*b into an FMA, ≤1 ULP),
    and the public dispatch returns that native result.
"""

import math

import numpy as np
import pytest

from srmech.amsc import _native
from srmech.amsc.cascade import autocorrelation
from srmech.amsc.cascade.compose import _try_native_autocorrelation

_RNG = np.random.default_rng(8087)


def _naive_circular_autocorr(x):
    """Reference: the textbook O(n²) circular autocorrelation, pure Python."""
    xs = [float(v) for v in x]
    n = len(xs)
    out = []
    for k in range(n):
        acc = 0.0
        for i in range(n):
            acc += xs[i] * xs[(i + k) % n]
        out.append(acc)
    return out


# ──────────────────────────────────────────────────────────────────────
# The spectral identity: FFT route == direct-sum definition
# ──────────────────────────────────────────────────────────────────────


def test_autocorrelation_matches_direct_definition():
    """The public op (FFT route or native) equals the naive direct sum —
    i.e. r = Re(IFFT(|FFT(x)|²)) IS the lagged product-sum."""
    for n in (2, 3, 5, 8, 13, 32, 64):
        x = _RNG.standard_normal(n)
        got = autocorrelation(x)
        ref = _naive_circular_autocorr(x)
        assert len(got) == n
        assert np.allclose(got, ref, rtol=0.0, atol=1e-9), (n, got, ref)


def test_autocorrelation_returns_list_of_float():
    r = autocorrelation([1.0, 2.0, 3.0, 4.0])
    assert isinstance(r, list)
    assert all(isinstance(v, float) for v in r)


def test_autocorrelation_energy_anchor():
    """r[0] == Σ x² == the signal energy (the F290 §C conservation quantity)."""
    for n in (1, 4, 16, 50):
        x = _RNG.standard_normal(n)
        r = autocorrelation(x)
        assert math.isclose(r[0], float(np.dot(x, x)), rel_tol=0.0, abs_tol=1e-9)


def test_autocorrelation_symmetry():
    """Circular autocorrelation of a real signal is symmetric: r[k] == r[n-k]."""
    n = 11
    x = _RNG.standard_normal(n)
    r = autocorrelation(x)
    for k in range(1, n):
        assert math.isclose(r[k], r[n - k], rel_tol=0.0, abs_tol=1e-9), k


# ──────────────────────────────────────────────────────────────────────
# Boundary cases
# ──────────────────────────────────────────────────────────────────────


def test_autocorrelation_empty():
    assert autocorrelation([]) == []


def test_autocorrelation_singleton():
    """n == 1: the only lag is k=0 -> [x[0]²]."""
    assert autocorrelation([3.0]) == [9.0]


def test_autocorrelation_constant_signal():
    """A constant signal c repeated n times: r[k] = n·c² for every lag."""
    n, c = 6, 2.0
    r = autocorrelation([c] * n)
    for k in range(n):
        assert math.isclose(r[k], n * c * c, rel_tol=0.0, abs_tol=1e-9), k


def test_autocorrelation_coerces_ints():
    """Integer input is coerced to float; result matches the float run."""
    assert np.allclose(autocorrelation([1, 2, 3]),
                       autocorrelation([1.0, 2.0, 3.0]), rtol=0.0, atol=1e-12)


# ──────────────────────────────────────────────────────────────────────
# Catalog discovery
# ──────────────────────────────────────────────────────────────────────


def test_autocorrelation_is_registered_cascade_op():
    from srmech.dsl import list_cascade_ops

    assert "autocorrelation" in list_cascade_ops()


def test_autocorrelation_descriptor_class_is_L():
    from srmech.dsl import get_descriptor

    desc = get_descriptor("autocorrelation")
    assert desc["cascade"]["class_composition"] == "L"


# ──────────────────────────────────────────────────────────────────────
# Native C parity (skipped when the native lib is unavailable)
# ──────────────────────────────────────────────────────────────────────

_HAS_C = (
    _native.HAS_NATIVE
    and _native.LIB is not None
    and hasattr(_native.LIB, "srmech_autocorrelation_f64")
)

_skip = pytest.mark.skipif(
    not _HAS_C, reason="native srmech_autocorrelation_f64 unavailable")


@_skip
def test_native_autocorrelation_matches_direct_sum():
    """The native direct-sum peer matches the naive direct sum to ~1e-12
    (a compiler may contract a*b into an FMA -> <=1 ULP)."""
    for n in (1, 2, 3, 8, 17, 64, 128):
        x = _RNG.standard_normal(n)
        got = _try_native_autocorrelation(x)
        assert got is not None, "native dispatch returned None unexpectedly"
        ref = _naive_circular_autocorr(x)
        assert np.allclose(got, ref, rtol=0.0, atol=1e-12), (n, got, ref)


@_skip
def test_public_autocorrelation_uses_native():
    """When HAS_NATIVE, the public op returns the native direct-sum result
    (so the FFT and direct-sum routes agree to ~1e-12)."""
    for n in (4, 16, 65):
        x = _RNG.standard_normal(n)
        pub = autocorrelation(x)
        nat = _try_native_autocorrelation(x)
        assert np.allclose(pub, nat, rtol=0.0, atol=0.0), (n, pub, nat)

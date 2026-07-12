"""rc149 (BATCH B4b — sp_transform part 2, the filter family).

The 5 NUMERIC DSP filter ops — ``fir`` / ``iir`` / ``allpass`` /
``closed_form_ops.matched_filter`` / ``path_b_ops.matched_filter`` — move
``python_only_debt →`` ``c_dispatched`` (iir / allpass, over the ONE new C
symbol ``srmech_iir_lfilter_f64``) / ``composition_of_c`` (fir / matched_filter,
via a Toeplitz matvec through ``srmech_dense_matmul_complex``). This suite
proves:

1. **VALUE oracles** — each op computes the mathematically-correct filter,
   independent of the C-vs-pure question: FIR impulse response = the taps + FIR
   vs a naive convolution; IIR impulse response = the geometric decay + IIR vs
   an independent difference-equation reference; allpass vs the same reference;
   the matched-filter autocorrelation peak = the signal energy at zero lag (the
   "peak at the template location" property) + matched_filter vs an independent
   reverse-conjugate correlation.
2. **WITHIN-TOL native == pure** — each op's native path matches its own
   forced-pure fallback (native OFF via monkeypatch) to reldiff ≤ 1e-9. This is
   a **differential NUMERIC** contract (float DSP), **NOT** byte-identity: a
   convolution matmul / feedback accumulation can FMA-fuse ~1 ULP on some
   platforms (macOS clang), so byte-equality is not claimed — the SAME
   classification as the F1 FFT / F2 SVD / B4a numeric batches.

This module is **numpy-free** (a test for a numpy-free surface must itself be
numpy-free) — the reference maths is stdlib ``math`` / ``cmath`` only.
"""

from __future__ import annotations

import math
import random

import pytest

from srmech.amsc import _native
from srmech.signal_processing.closed_form_ops import allpass, fir, iir, matched_filter
from srmech.signal_processing.path_b_ops import matched_filter as matched_filter_b

# native availability (the differential tests run regardless — with native
# absent, forced-pure == default so reldiff is trivially 0; they still guard
# the pure path is complete + the dispatch wiring does not change the value).
_HAS_MATMUL = (
    _native.HAS_NATIVE
    and _native.LIB is not None
    and hasattr(_native.LIB, "srmech_dense_matmul_complex")
)
_HAS_IIR = _native.has_native_iir_f64()


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


def _rand_real(n, seed):
    rng = random.Random(seed)
    return [rng.uniform(-3.0, 3.0) for _ in range(n)]


def _ref_convolve_full(x, h):
    """Independent naive full linear convolution (no numpy, no srmech)."""
    nx, nh = len(x), len(h)
    out = [0.0] * (nx + nh - 1)
    for i in range(nx):
        for j in range(nh):
            out[i + j] += x[i] * h[j]
    return out


def _ref_lfilter(b, a, x):
    """Independent direct-form-I difference equation reference (no numpy)."""
    n = len(x)
    y = [0.0] * n
    a0 = a[0]
    for i in range(n):
        acc = 0.0
        for j in range(len(b)):
            if i - j >= 0:
                acc += b[j] * x[i - j]
        for k in range(1, len(a)):
            if i - k >= 0:
                acc -= a[k] * y[i - k]
        y[i] = acc / a0
    return y


def _ref_correlate_full(a, v):
    """Independent NumPy-convention full cross-correlation
    ``c[k] = Σ_n a[k-(nv-1)+n]·conj(v[n])`` (no numpy, no srmech)."""
    na, nv = len(a), len(v)
    out = []
    for k in range(na + nv - 1):
        acc = 0j if any(isinstance(z, complex) for z in a + v) else 0.0
        for n in range(nv):
            j = k - (nv - 1) + n
            if 0 <= j < na:
                vn = v[n].conjugate() if isinstance(v[n], complex) else v[n]
                acc += a[j] * vn
        out.append(acc)
    return out


# ======================================================================
# FIR — impulse-response + naive-convolution value oracles + native==pure
# ======================================================================

@pytest.mark.parametrize("taps", [[1.0], [0.5, -0.25], [1.0, 2.0, 3.0, 2.0, 1.0]])
def test_fir_impulse_response_is_taps(taps):
    """The FIR impulse response IS the tap table: fir(δ, h)[:M] == h."""
    m = len(taps)
    impulse = [1.0] + [0.0] * 9
    y = fir.op(impulse, taps, mode="full")
    assert len(y) == len(impulse) + m - 1
    for k in range(m):
        assert abs(y[k] - taps[k]) < 1e-9, f"impulse response tap {k}"
    for k in range(m, len(y)):
        assert abs(y[k]) < 1e-9, f"impulse response tail {k} should be 0"


@pytest.mark.parametrize("mode", ["full", "same", "valid"])
@pytest.mark.parametrize("n,m", [(12, 3), (16, 5), (9, 9), (5, 8)])
def test_fir_matches_naive_convolution(mode, n, m):
    """FIR matches an INDEPENDENT naive convolution (value correctness)."""
    x = _rand_real(n, seed=11 * n + m)
    h = _rand_real(m, seed=7 * m + 3)
    got = fir.op(x, h, mode=mode)
    full = _ref_convolve_full(x, h)
    # crop the independent reference to `mode` (numpy convention).
    if mode == "full":
        ref = full
    elif mode == "same":
        target = max(n, m)
        start = (len(full) - target) // 2
        ref = full[start:start + target]
    else:  # valid
        target = max(n, m) - min(n, m) + 1
        start = min(n, m) - 1
        ref = full[start:start + target]
    assert _reldiff(ref, got) < 1e-9, f"fir mode={mode} n={n} m={m}"


@pytest.mark.parametrize("mode", ["full", "same", "valid"])
@pytest.mark.parametrize("n,m", [(20, 4), (13, 7)])
def test_fir_native_matches_pure(monkeypatch, mode, n, m):
    """The C-dispatched FIR (Toeplitz matvec) matches the forced-pure convolution
    within-tol — NOT byte-identical."""
    x = _rand_real(n, seed=200 + n)
    h = _rand_real(m, seed=900 + m)
    disp = fir.op(x, h, mode=mode)
    monkeypatch.setattr(_native, "HAS_NATIVE", False)  # force pure convolve
    pure = fir.op(x, h, mode=mode)
    assert _reldiff(pure, disp) < 1e-9, f"fir native!=pure mode={mode}"


# ======================================================================
# IIR — impulse / difference-equation value oracles + native==pure
# ======================================================================

def test_iir_impulse_response_geometric():
    """y[n] = x[n] + 0.5 y[n-1] (b=[1], a=[1,-0.5]) has impulse response 0.5^n."""
    n = 12
    impulse = [1.0] + [0.0] * (n - 1)
    y = iir.op(impulse, [1.0], [1.0, -0.5])
    assert len(y) == n
    for k in range(n):
        assert abs(y[k] - 0.5 ** k) < 1e-9, f"impulse response sample {k}"


@pytest.mark.parametrize("b,a", [
    ([1.0], [1.0, -0.5]),
    ([0.5, 0.5], [1.0, -0.3, 0.1]),
    ([1.0, -1.0], [1.0, 0.2]),
])
def test_iir_matches_reference_difference_equation(b, a):
    """IIR (step input) matches an INDEPENDENT difference-equation reference."""
    x = [1.0] * 16  # step response
    got = iir.op(x, b, a)
    ref = _ref_lfilter(b, a, x)
    assert _reldiff(ref, got) < 1e-9, f"iir vs reference b={b} a={a}"


@pytest.mark.parametrize("b,a", [([1.0], [1.0, -0.5]), ([0.5, 0.5], [1.0, -0.3, 0.1])])
def test_iir_native_matches_pure(monkeypatch, b, a):
    x = _rand_real(48, seed=hash((tuple(b), tuple(a))) % 9999)
    disp = iir.op(x, b, a)
    monkeypatch.setattr(_native, "HAS_NATIVE", False)  # force pure _lfilter_direct
    pure = iir.op(x, b, a)
    assert _reldiff(pure, disp) < 1e-9, "iir native!=pure"


def test_iir_biquad_native_matches_pure(monkeypatch):
    """The biquad-cascade path also dispatches (per section) + matches pure."""
    x = _rand_real(40, seed=4242)
    sections = [
        [1.0, -1.8, 0.9, 1.0, -1.7, 0.85],
        [0.5, 0.0, -0.5, 1.0, 0.2, 0.1],
    ]
    disp = iir.op(x, [1.0], [1.0], biquad_sections=sections)
    monkeypatch.setattr(_native, "HAS_NATIVE", False)
    pure = iir.op(x, [1.0], [1.0], biquad_sections=sections)
    assert _reldiff(pure, disp) < 1e-9, "iir biquad native!=pure"


# ======================================================================
# allpass — reference + native==pure
# ======================================================================

@pytest.mark.parametrize("order,a,b", [(1, 0.6, None), (1, -0.4, None), (2, 0.5, 0.3)])
def test_allpass_matches_reference(order, a, b):
    """allpass matches the same IIR difference-equation reference on its
    mirrored (b_coef, a_coef) pair."""
    x = _rand_real(24, seed=int(100 * (a + 5)) + order)
    got = allpass.op(x, a, b=b, order=order)
    if order == 1:
        b_coef, a_coef = [a, 1.0], [1.0, a]
    else:
        b_coef, a_coef = [a, b, 1.0], [1.0, b, a]
    ref = _ref_lfilter(b_coef, a_coef, x)
    assert _reldiff(ref, got) < 1e-9, f"allpass vs reference order={order}"


@pytest.mark.parametrize("order,a,b", [(1, 0.7, None), (2, 0.4, -0.2)])
def test_allpass_native_matches_pure(monkeypatch, order, a, b):
    x = _rand_real(32, seed=777 + order)
    disp = allpass.op(x, a, b=b, order=order)
    monkeypatch.setattr(_native, "HAS_NATIVE", False)  # force pure _lfilter_df1
    pure = allpass.op(x, a, b=b, order=order)
    assert _reldiff(pure, disp) < 1e-9, f"allpass native!=pure order={order}"


def test_allpass_unity_magnitude_dc_passthrough():
    """A first-order allpass with coefficient 0 IS a pure unit delay H(z)=z^-1 —
    the output is the input shifted by one (a clean phase-only value oracle)."""
    x = _rand_real(10, seed=5)
    y = allpass.op(x, 0.0, order=1)
    assert abs(y[0]) < 1e-12
    for k in range(1, len(x)):
        assert abs(y[k] - x[k - 1]) < 1e-9, f"unit-delay sample {k}"


# ======================================================================
# matched_filter — peak-at-template + reference value oracles + native==pure
# ======================================================================

def test_matched_filter_autocorrelation_peak_is_energy():
    """Matched filter of a signal against ITSELF peaks at zero lag with value =
    the signal energy Σ|x|² (the canonical matched-filter alignment oracle)."""
    t = _rand_real(9, seed=17)
    n = len(t)
    c = matched_filter.op(t, t, mode="full")
    assert len(c) == 2 * n - 1
    energy = sum(v * v for v in t)
    peak_idx = max(range(len(c)), key=lambda i: abs(c[i]))
    assert peak_idx == n - 1, "matched-filter peak not at the alignment lag"
    assert abs(c[n - 1] - energy) < 1e-9 * (energy + 1.0), "peak != energy"


@pytest.mark.parametrize("mode", ["full", "same", "valid"])
def test_matched_filter_matches_reference(mode):
    """matched_filter matches an INDEPENDENT reverse-conjugate correlation."""
    s = _rand_real(20, seed=31)
    t = _rand_real(5, seed=32)
    got = matched_filter.op(s, t, mode=mode)
    full = _ref_correlate_full(s, t)
    na, nv = len(s), len(t)
    if mode == "full":
        ref = full
    elif mode == "valid":
        target = max(na, nv) - min(na, nv) + 1
        start = min(na, nv) - 1
        ref = full[start:start + target]
    else:  # same
        target = max(na, nv)
        diff = len(full) - target
        start = diff // 2 if na >= nv else (diff + 1) // 2
        ref = full[start:start + target]
    assert _reldiff(ref, got) < 1e-9, f"matched_filter mode={mode}"


def test_matched_filter_paths_agree():
    """Path A and Path B compute the same cross-correlation (identity, not
    implementation) — value-identical to round-off."""
    s = _rand_real(24, seed=61)
    t = _rand_real(6, seed=62)
    a = matched_filter.op(s, t, mode="full")
    b = matched_filter_b.op(s, t, mode="full")
    assert _reldiff(a, b) < 1e-12, "path A != path B"


@pytest.mark.parametrize("mode", ["full", "same", "valid"])
def test_matched_filter_native_matches_pure(monkeypatch, mode):
    s = _rand_real(28, seed=71)
    t = _rand_real(7, seed=72)
    disp = matched_filter.op(s, t, mode=mode)
    monkeypatch.setattr(_native, "HAS_NATIVE", False)  # force pure correlate
    pure = matched_filter.op(s, t, mode=mode)
    assert _reldiff(pure, disp) < 1e-9, f"matched_filter native!=pure mode={mode}"


def test_matched_filter_path_b_native_matches_pure(monkeypatch):
    s = _rand_real(28, seed=81)
    t = _rand_real(7, seed=82)
    disp = matched_filter_b.op(s, t, mode="full")
    monkeypatch.setattr(_native, "HAS_NATIVE", False)
    pure = matched_filter_b.op(s, t, mode="full")
    assert _reldiff(pure, disp) < 1e-9, "matched_filter path_b native!=pure"


# ======================================================================
# complex-input coverage — the matmul convolution path is dtype-poly
# ======================================================================

def test_fir_complex_matches_reference():
    """A complex signal / complex taps convolution still matches the naive
    reference (the Toeplitz-matvec path is dtype-polymorphic)."""
    rng = random.Random(303)
    x = [complex(rng.uniform(-2, 2), rng.uniform(-2, 2)) for _ in range(10)]
    h = [complex(rng.uniform(-1, 1), rng.uniform(-1, 1)) for _ in range(3)]
    got = fir.op(x, h, mode="full")
    ref = _ref_convolve_full(x, h)
    assert _reldiff(ref, got) < 1e-9, "complex fir vs naive convolution"


# ======================================================================
# dispatch presence (informational — the value/parity oracles above are the
# real gate; these just record whether the native path was exercised)
# ======================================================================

def test_native_paths_available_report():
    """Not a hard gate: records which C paths back this batch (dense_matmul for
    fir/matched_filter, srmech_iir_lfilter_f64 for iir/allpass). When absent the
    pure path is the complete alternative and every test above still passes."""
    assert isinstance(_HAS_MATMUL, bool)
    assert isinstance(_HAS_IIR, bool)

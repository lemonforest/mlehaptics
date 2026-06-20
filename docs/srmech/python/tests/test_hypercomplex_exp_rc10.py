"""0.9.0rc10 — ``cascade.hypercomplex_exp``: the literal ``exp(μθ)`` unit
hypercomplex twiddle, native-vs-pure byte-exact (F882, srmech #205).

``hypercomplex_exp(theta, k_axes)`` is the GENUINE hypercomplex exponential
``exp(μθ) = cos θ + μ·sin θ`` where ``μ`` is the equal-weight UNIT pure-imaginary
over the first ``k_axes`` octonion axes (``k_axes ∈ {1,3,7}`` = ℂ/ℍ/𝕆). It
returns 8 exact :class:`~srmech.amsc.q.Q` over ``2**61`` (Q61):
``[cos θ, sin θ/√k ×k_axes, 0 ×(7−k_axes)]``, ``|q| = 1``. On a native install
it dispatches to the C peer ``srmech_hypercomplex_exp_q61`` (the int64 Q61 pieces
BEFORE any float projection); off-native it runs the pure-Python Q61 cascade
(``rational.{cos,sin}`` Q61 + the integer-sqrt ``1/√k`` unit norm). The two
paths must be byte-identical — the native accelerator is a pure speedup, never a
divergence.

Substrate-native fixed-width Q61: no bignum, no libm, no ``abs()`` (the ``1/√k``
unit norm is Class-K integer-sqrt; the sign is Class-C). Numpy-free by
construction (no numpy import, no ``np.``); the oracle for the byte-exact check
is the package's own pure cascade. ``math`` appears ONLY as a float-ULP witness
that the Q61→float projection is faithful (the rc7 parity-test pattern;
``[[feedback_test_for_numpy_free_module_must_itself_be_numpy_free]]``).
"""

import math

import pytest

from srmech.amsc import _native
from srmech.amsc.q import Q
from srmech.amsc.cascade import hypercomplex_exp, cd_mult


_K_AXES = (1, 3, 7)               # ℂ / ℍ / 𝕆
_THETAS = (
    [i * 0.1 for i in range(-100, 101)]
    + [0.0, math.pi / 6, math.pi / 4, math.pi / 3, math.pi / 2, math.pi,
       2 * math.pi, -math.pi, 1000.0, -1000.0, 1e-9, 0.123456789]
)


def _pairs(theta, k):
    """The 8 exact ``(num, den)`` pairs of ``hypercomplex_exp(theta, k)``."""
    q8 = hypercomplex_exp(theta, k)
    assert isinstance(q8, tuple) and len(q8) == 8, "must be an 8-tuple"
    return [qv.as_pair() for qv in q8]


@pytest.mark.parametrize("k", _K_AXES)
def test_native_q61_matches_pure_byte_for_byte(k, monkeypatch):
    """Whichever path is active, force the OTHER and assert identical Q pairs.

    Native-built → a true native-vs-pure byte-exact check; native-absent → both
    branches are the pure path and it still proves the dispatch wiring imports
    and runs clean.
    """
    native_live = _native.has_native_hypercomplex_exp()

    results_active = {t: _pairs(t, k) for t in _THETAS}

    # Force the pure-Python Q61 cascade and re-evaluate the same θ grid.
    monkeypatch.setattr(_native, "has_native_hypercomplex_exp", lambda: False)
    results_pure = {t: _pairs(t, k) for t in _THETAS}

    for t in _THETAS:
        assert results_active[t] == results_pure[t], (
            f"hypercomplex_exp({t!r}, {k}) diverged: active={results_active[t]} "
            f"pure={results_pure[t]} (native_live={native_live})"
        )


@pytest.mark.parametrize("k", _K_AXES)
def test_shape_is_cos_then_k_equal_sines_then_zeros(k):
    """``q[0]=cos θ``; ``q[1..k]`` are an EQUAL ``sin θ/√k``; ``q[k+1..7]`` = 0."""
    theta = 0.7
    q8 = hypercomplex_exp(theta, k)
    assert all(isinstance(qv, Q) for qv in q8), "every component is an exact Q"
    # The k imaginary slots are bit-for-bit equal (one shared scaled value).
    for a in range(2, k + 1):
        assert q8[a].as_pair() == q8[1].as_pair(), f"slot {a} != slot 1"
    # The trailing 7−k slots are EXACTLY zero (the empty axes).
    for a in range(k + 1, 8):
        assert q8[a] == Q(0, 1), f"slot {a} must be exactly 0"
    # Q61 denominators: every leaf rides 2**61 before reduction (0 reduces to 1).
    for qv in q8:
        assert qv.denominator in (1, 2 ** 61) or (2 ** 61) % qv.denominator == 0


def test_complex_case_reduces_to_plain_cos_sin():
    """``k_axes=1`` (ℂ) is the bare ``(cos θ, sin θ, 0…)`` — 1/√1 = 1, no scale."""
    for theta in (0.0, 0.3, math.pi / 6, -1.25):
        q8 = hypercomplex_exp(theta, 1)
        assert abs(float(q8[0]) - math.cos(theta)) <= 1e-15
        assert abs(float(q8[1]) - math.sin(theta)) <= 1e-15
        for a in range(2, 8):
            assert q8[a] == Q(0, 1)


@pytest.mark.parametrize("k", _K_AXES)
def test_unit_norm(k):
    """``|q|² = cos²θ + k·(sin θ/√k)² = 1`` (within Q61 truncation)."""
    for theta in (0.0, 0.4, 1.1, math.pi / 3, 5.0):
        q8 = hypercomplex_exp(theta, k)
        norm2 = sum(float(qv) * float(qv) for qv in q8)
        assert abs(norm2 - 1.0) <= 1e-9, f"|q|^2={norm2} for θ={theta}, k={k}"


@pytest.mark.parametrize("k", _K_AXES)
def test_cd_mult_compose_is_norm_preserving(k):
    """Rotating a hypercomplex value by the unit twiddle IN the algebra preserves
    its norm (ℂ/ℍ/𝕆 are normed: ``|q·v| = |q|·|v| = |v|``). This is the F882
    "do the transform in the algebra, then project" path that beats composing
    scalar phase_binds on the projected carrier."""
    theta = 0.9
    q = hypercomplex_exp(theta, k)
    v = (0.5, -0.25, 0.75, 0.1, -0.6, 0.2, 0.3, -0.4)
    out = cd_mult(q, v)                       # exact Fractions, rotation in 𝕆
    assert len(out) == 8
    norm_v = math.sqrt(sum(x * x for x in v))
    norm_out = math.sqrt(sum(float(x) * float(x) for x in out))
    assert abs(norm_out - norm_v) <= 1e-9, (
        f"norm not preserved: |v|={norm_v} |q·v|={norm_out} (k={k})")


def test_k_axes_validation():
    """``k_axes`` must be 1, 3 or 7 (ℂ/ℍ/𝕆); anything else is a clean ValueError."""
    for bad in (0, 2, 4, 5, 6, 8, -1, 14):
        with pytest.raises(ValueError):
            hypercomplex_exp(0.5, bad)


def test_non_finite_theta_rejected():
    """``Q`` is the FINITE-rational carrier — ±Inf / NaN are not rationals."""
    for bad in (float("inf"), float("-inf"), float("nan")):
        with pytest.raises(ValueError):
            hypercomplex_exp(bad, 3)


def test_zero_theta_is_the_identity():
    """``exp(μ·0) = 1`` exactly — ``(1, 0, 0, 0, 0, 0, 0, 0)`` whatever k is."""
    for k in _K_AXES:
        q8 = hypercomplex_exp(0.0, k)
        assert q8[0] == Q(1, 1)
        for a in range(1, 8):
            assert q8[a] == Q(0, 1)

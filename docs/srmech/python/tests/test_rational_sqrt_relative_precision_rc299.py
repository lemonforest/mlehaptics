"""rc299 (`#919`) — the exact-rational √ cascade is RELATIVE-precision, not absolute.

``srmech.math.rational._sqrt_rational`` floors ``√(num/den)`` onto a FIXED
``2^-k`` grid. With the shipped default ``k = 54`` that is an **absolute**
precision, and both public consumers of the exact-rational root — ``hypot``
(always) and ``sqrt`` (on a ``Q`` input) — inherited it:

  * below ``2^-54 ≈ 5.55e-17`` the root floors to **exactly 0.0**, which makes
    the result unsafe as a DIVISOR (`#919`, and one half of the rc285
    ``mat_eigvals`` spectrum bug — the Householder reflector divided by it);
  * and well ABOVE that floor the value is a plausible-looking non-zero that is
    simply wrong — 44% low at 1e-16, 2.4e-4 low at 1e-13. That band is the more
    dangerous one, because nothing about the return value signals it.

rc299 sizes the grid to the radicand (``_sqrt_relative_k``) instead of adding an
epsilon or a guard band. The premise that a rational cascade cannot reach small
magnitudes was false: ``sqrt``'s FLOAT path already decomposed ``x = M·2^e`` and
carried an exact power-of-two scale, so it was relative-precision all along.
``Q`` is an arbitrary-precision integer pair — the floor was the hard-coded
``k``, never the carrier.

The ratchet below is DOWN-ONLY in spirit: it pins ~1-ulp relative accuracy over
220 orders of magnitude, so a future refactor that restores a fixed ``k`` fails
loudly rather than silently reintroducing the zero.

**Proof of redness is in-suite and permanent.** ``_sqrt_rational_pre_rc299``
below is a faithful copy of the shipped pre-rc299 behaviour (the fixed ``k=54``
grid); it is asserted to actually reproduce the exact-zero and the 44% error, so
this file is demonstrably capable of failing. A ratchet never shown to go red is
not a ratchet.

Numpy-free. ``math`` is used ONLY as an independent test ORACLE — never inside a
cascade — which is the same allowance the other kernel-invariant ratchets take.
"""
import math

import pytest

from srmech.amsc.q import Q
from srmech.math.rational import (
    _SQRT_Q_K,
    _sqrt_rational,
    _sqrt_relative_k,
    hypot,
    sqrt,
)
from srmech.math.laplacian import _fhypot


# ── the pre-rc299 behaviour, kept executable so the ratchet can be shown red ──
def _sqrt_rational_pre_rc299(num: int, den: int):
    """The shipped pre-rc299 root: a FIXED ``2^-54`` absolute grid."""
    return _sqrt_rational(num, den, _SQRT_Q_K)


def _hypot_pre_rc299(a: float, b: float):
    """The shipped pre-rc299 ``hypot`` — exact sum-of-squares, fixed-k root."""
    an, ad = float(a).as_integer_ratio()
    bn, bd = float(b).as_integer_ratio()
    num = an * an * bd * bd + bn * bn * ad * ad
    den = ad * ad * bd * bd
    return _sqrt_rational_pre_rc299(num, den)


# ── (1) the raw defect, proven live ──────────────────────────────────────────

def test_pre_rc299_hypot_returns_exactly_zero_in_the_underflow_band():
    """The defect `#919` names: an exact 0.0 magnitude for a non-zero input."""
    for e in (17, 18, 20, 25, 300):
        x = 10.0 ** -e
        got = float(_hypot_pre_rc299(x, 0.0))
        assert got == 0.0, (
            f"expected the pre-rc299 defect (exact 0.0) at 1e-{e}; got {got!r}. "
            "If this fails the faithful-copy oracle has drifted from the "
            "behaviour it is supposed to reproduce."
        )


def test_pre_rc299_hypot_is_inaccurate_well_above_the_zero_floor():
    """The MORE dangerous half: a plausible non-zero that is badly wrong.

    This is the part `#919` does not name and the reason a ``!= 0.0`` guard
    would NOT have been a sufficient fix.
    """
    got = float(_hypot_pre_rc299(1e-16, 0.0))
    assert got != 0.0, "1e-16 sits above the zero floor — precondition"
    rel = (got - 1e-16) / 1e-16
    assert rel < -0.4, (
        f"expected the pre-rc299 value at 1e-16 to be >40% low; rel={rel:+.3e}"
    )


# ── (2) the repair ───────────────────────────────────────────────────────────

_DECADES = list(range(1, 40))


@pytest.mark.parametrize("e", _DECADES)
def test_hypot_is_relative_precision_across_the_former_underflow_band(e):
    """``hypot(x, 0) == |x|`` to ~1 ulp for every decade, including below 1e-17.

    This is the assertion that goes RED if a fixed ``k`` is ever restored.
    """
    x = 10.0 ** -e
    got = float(hypot(x, 0.0))
    assert got != 0.0, (
        f"hypot(1e-{e}, 0.0) returned EXACTLY 0.0 — the `#919` underflow is "
        "back. A zero magnitude is unsafe as a divisor; see _sqrt_relative_k."
    )
    rel = (got - x) / x
    assert math.fabs(rel) < 1e-15, f"hypot(1e-{e}, 0.0) rel error {rel:+.3e}"


@pytest.mark.parametrize("e", [20, 30, 40, 60, 100])
def test_sqrt_of_a_small_Q_keeps_its_significant_bits(e):
    """The ``Q``-input ``sqrt`` path shared the defect — it is fixed with hypot."""
    q = Q(1, 10 ** e)
    got = float(sqrt(q))
    ref = math.sqrt(1.0 / (10.0 ** e))
    assert got != 0.0, f"sqrt(Q(1, 1e{e})) floored to exactly 0.0"
    rel = (got - ref) / ref
    assert math.fabs(rel) < 1e-15, f"sqrt(Q(1,1e{e})) rel error {rel:+.3e}"


def test_fhypot_the_float_projection_carries_the_repair():
    """``laplacian._fhypot`` is the projection the FPU kernels divide by."""
    for e in (16, 17, 18, 25, 40):
        x = 10.0 ** -e
        got = _fhypot(x, 0.0)
        assert got != 0.0, f"_fhypot(1e-{e}, 0.0) == 0.0 — unsafe as a divisor"
        assert math.fabs((got - x) / x) < 1e-15


def test_hypot_matches_libm_over_220_orders_of_magnitude():
    """Differential check against an independent oracle, both components live."""
    worst = 0.0
    worst_at = None
    # A deterministic magnitude sweep — no rng, so a failure is reproducible.
    for ea in range(-160, 61, 11):
        for eb in range(-160, 61, 23):
            a = 1.3 * (2.0 ** ea)
            b = -0.7 * (2.0 ** eb)
            ref = math.hypot(a, b)
            if ref == 0.0 or not math.isfinite(ref):
                continue
            rel = (float(hypot(a, b)) - ref) / ref
            if math.fabs(rel) > math.fabs(worst):
                worst, worst_at = rel, (ea, eb)
    assert math.fabs(worst) < 5e-16, (
        f"worst hypot relative error {worst:+.3e} at 2^{worst_at} — expected ~1 ulp"
    )


# ── (3) backward compatibility: radicands >= 1 are BYTE-identical ─────────────

def test_radicands_at_or_above_one_are_untouched():
    """``_sqrt_relative_k`` returns ``k`` unchanged for a radicand >= 1.

    So every value at or above 1 — including the ``_tool_docs`` example and the
    exact perfect squares — is byte-identical to what shipped before rc299.
    This is what keeps the repair off the doc/registry ripple surface.
    """
    assert hypot(3.0, 4.0) == Q(5, 1)
    assert hypot(1.0, 1.0) == _hypot_pre_rc299(1.0, 1.0)
    assert hypot(5.0, 12.0) == Q(13, 1)
    for a, b in ((1.0, 1.0), (2.0, 3.0), (10.0, 0.25), (1.0, 0.0)):
        assert hypot(a, b) == _hypot_pre_rc299(a, b), (
            f"hypot({a}, {b}) moved; radicands >= 1 must stay byte-identical"
        )


def test_sqrt_relative_k_is_identity_above_one_and_grows_below():
    """The selector's own contract, pinned directly."""
    assert _sqrt_relative_k(4, 1, _SQRT_Q_K) == _SQRT_Q_K       # radicand 4
    assert _sqrt_relative_k(1, 1, _SQRT_Q_K) == _SQRT_Q_K       # radicand 1
    small = _sqrt_relative_k(1, 10 ** 40, _SQRT_Q_K)
    assert small > _SQRT_Q_K, "a tiny radicand must widen the grid"


def test_explicit_precision_bits_is_still_the_literal_absolute_grid():
    """An explicit ``precision=`` keeps its documented ABSOLUTE meaning.

    The relative sizing applies only to the DEFAULT path, so the π cascade and
    any other caller that asks for N fractional bits still gets exactly N.
    (rc318: the knob was renamed ``precision_bits`` → ``precision``.)
    """
    q = hypot(1.0, 1.0, precision=10)
    assert q.as_pair()[1] <= (1 << 10)
    assert hypot(1.0, 1.0, precision=_SQRT_Q_K) == _hypot_pre_rc299(1.0, 1.0)


# ── (4) the divisor contract the repair exists to serve ──────────────────────

def test_phase_from_hypot_is_a_unit_complex_at_every_scale():
    """``x0 / hypot(x0)`` must be a UNIT phase — the property `#919` broke.

    This is the exact consumption that turned the rc285 Householder reduction
    into a non-similarity. It is asserted here at the cascade level so the
    property is pinned independently of any one eigensolver.
    """
    for e in (0, -8, -16, -17, -20, -40, -100):
        for zr, zi in ((3.0, -4.0), (1.0, 0.0), (0.0, 1.0), (-2.0, 5.0)):
            x0 = complex(zr * (2.0 ** e), zi * (2.0 ** e))
            if x0 == 0j:
                continue
            mod = _fhypot(x0.real, x0.imag)
            assert mod > 0.0, f"zero modulus for x0={x0!r} — division would blow up"
            phase = x0 / mod
            unit = math.hypot(phase.real, phase.imag)
            assert math.fabs(unit - 1.0) < 1e-12, (
                f"phase for x0={x0!r} has modulus {unit!r}, not 1.0"
            )

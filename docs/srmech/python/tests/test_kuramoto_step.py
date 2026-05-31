"""Tests for the Kuramoto forward-Euler step (#778 follow-on; MS#20 rc9).

The coupled-oscillator dispatch-clock Euler step the spectral-research arc
hand-rolled in Python (F141/F231/R-95/F234) now has a native C peer
(``srmech_cascade_kuramoto_step_f64``) — closing a C/Python parity gap so
srmech runs it with NO host Python (the full-parity commitment).

Correctness is checked against the closed-form one-step formula; C/Python
parity is to libm-trig **tolerance** (NOT bit-exact across platforms — the
kepler trig discipline). Native tests SKIP cleanly when ``HAS_NATIVE`` is
False (pure-Python wheel / Pyodide / sdist without a toolchain).
"""

from __future__ import annotations

import math

import pytest

from srmech.amsc import _native
from srmech.amsc.cascade import kuramoto_step


def _reference_step(theta, omega, coupling, dt):
    """Closed-form one forward-Euler Kuramoto step (the spec)."""
    n = len(theta)
    inv_n = (coupling / n) if n > 0 else 0.0
    out = []
    for i in range(n):
        s = sum(math.sin(theta[j] - theta[i]) for j in range(n))
        out.append(theta[i] + dt * (omega[i] + inv_n * s))
    return out


# ----------------------------------------------------------------------
# Correctness — the public op matches the closed-form step.
# ----------------------------------------------------------------------


def test_two_oscillator_hand_checked():
    """theta=[0, π/2], omega=[1, 2], K=1, dt=0.1 → [0.15, π/2 + 0.15]."""
    theta = [0.0, math.pi / 2]
    omega = [1.0, 2.0]
    out = kuramoto_step(theta, omega, coupling=1.0, dt=0.1)
    # i=0: Σsin = sin(0)+sin(π/2) = 1 → 0 + 0.1*(1 + 0.5*1) = 0.15
    # i=1: Σsin = sin(-π/2)+sin(0) = -1 → π/2 + 0.1*(2 + 0.5*(-1)) = π/2+0.15
    assert out[0] == pytest.approx(0.15, abs=1e-12)
    assert out[1] == pytest.approx(math.pi / 2 + 0.15, abs=1e-12)


def test_matches_closed_form_reference():
    theta = [0.1, 1.3, -2.0, 4.5, 0.0]
    omega = [0.5, -0.3, 1.1, 0.2, -0.7]
    out = kuramoto_step(theta, omega, coupling=2.5, dt=0.05)
    ref = _reference_step(theta, omega, 2.5, 0.05)
    assert out == pytest.approx(ref, abs=1e-12)


def test_n1_is_pure_drift():
    """n == 1: the coupling sum is sin(0) = 0 ⇒ pure drift θ + dt·ω."""
    out = kuramoto_step([0.7], [3.0], coupling=9.0, dt=0.2)
    assert out == pytest.approx([0.7 + 0.2 * 3.0], abs=1e-12)


def test_zero_coupling_is_pure_drift():
    theta = [0.1, 1.0, 2.0]
    omega = [1.0, -1.0, 0.5]
    out = kuramoto_step(theta, omega, coupling=0.0, dt=0.1)
    assert out == pytest.approx([t + 0.1 * w for t, w in zip(theta, omega)],
                                abs=1e-12)


def test_empty_input_is_empty():
    assert kuramoto_step([], [], coupling=1.0, dt=0.1) == []


def test_length_mismatch_raises():
    with pytest.raises(ValueError):
        kuramoto_step([0.0, 1.0], [1.0], coupling=1.0, dt=0.1)


def test_defaults():
    """coupling defaults to 1.0, dt to 0.01."""
    theta = [0.2, 1.1]
    omega = [0.3, -0.4]
    assert kuramoto_step(theta, omega) == pytest.approx(
        _reference_step(theta, omega, 1.0, 0.01), abs=1e-12)


# ----------------------------------------------------------------------
# C/Python parity (skips without the native symbol).
# ----------------------------------------------------------------------


_HAS_C = (
    _native.HAS_NATIVE
    and _native.LIB is not None
    and hasattr(_native.LIB, "srmech_cascade_kuramoto_step_f64")
)


@pytest.mark.skipif(not _HAS_C, reason="native srmech_cascade_kuramoto_step_f64 unavailable")
def test_c_matches_python_to_tolerance():
    """The native dispatch matches the pure-Python reference to libm-trig
    tolerance for several phase configs (same coupling-sum index order)."""
    cases = [
        ([0.0, math.pi / 2, math.pi], [1.0, 2.0, 3.0], 1.5, 0.1),
        ([0.1, 1.3, -2.0, 4.5, 0.0], [0.5, -0.3, 1.1, 0.2, -0.7], 2.5, 0.05),
        ([-1.0, -0.5, 0.5, 1.0], [0.0, 0.0, 0.0, 0.0], 4.0, 0.2),
    ]
    for theta, omega, k, dt in cases:
        out = kuramoto_step(theta, omega, coupling=k, dt=dt)  # native path
        ref = _reference_step(theta, omega, k, dt)
        assert out == pytest.approx(ref, abs=1e-9), (theta, omega, k, dt)


@pytest.mark.skipif(not _HAS_C, reason="native srmech_cascade_kuramoto_step_f64 unavailable")
def test_native_shim_direct():
    """The _try_native helper returns a value (not None) when the symbol is
    present — confirming the native path is actually exercised."""
    from srmech.amsc.cascade.compose import _try_native_kuramoto_step
    res = _try_native_kuramoto_step([0.0, 1.0], [1.0, 2.0], 1.0, 0.1)
    assert res is not None
    assert res == pytest.approx(_reference_step([0.0, 1.0], [1.0, 2.0], 1.0, 0.1),
                                abs=1e-9)


# ----------------------------------------------------------------------
# The op is a registered ToolEntry in the cascade category.
# ----------------------------------------------------------------------


def test_tool_entry_registered():
    from srmech.amsc import tool_schema

    schema = tool_schema.get_tool_schema()
    name = "srmech.amsc.cascade.kuramoto_step"
    entry = schema.lookup(name)
    assert entry is not None
    assert entry.category == "cascade"
    assert "Kuramoto" in entry.summary

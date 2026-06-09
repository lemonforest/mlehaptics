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


# ----------------------------------------------------------------------
# v0.6.0rc14 (§11.1) — the GENERALISED Kuramoto-Sakaguchi step:
# adjacency matrix + Sakaguchi alpha + per-oscillator pinning. Defaults
# reproduce the plain step exactly. The new co-equal C peer
# (srmech_cascade_kuramoto_step_general_f64) is differential-tested vs the
# Python fallback to libm-trig tolerance (skips on a pre-rc14 / pure lib).
# ----------------------------------------------------------------------

_HAS_C_GENERAL = (
    _native.HAS_NATIVE
    and _native.LIB is not None
    and hasattr(_native.LIB, "srmech_cascade_kuramoto_step_general_f64")
)


def _reference_general(theta, omega, adjacency, coupling, alpha, psi, ps, dt):
    """Closed-form generalised one-step (the spec): the Python fallback path.

    §32 fix: the adjacency weight is SCALED by the global ``coupling`` scalar
    (effective weight = ``K·A_ij``), matching the all-to-all branch
    (``inv_n = K/n``). ``coupling == 0`` zeroes the coupling term.
    """
    n = len(theta)
    inv_n = (coupling / n) if n > 0 else 0.0
    out = []
    for i in range(n):
        s = 0.0
        for j in range(n):
            w = (coupling * adjacency[i][j]) if adjacency is not None else inv_n
            s += w * math.sin(theta[j] - theta[i] - alpha)
        f = omega[i] + s
        if psi is not None:
            f += ps[i] * math.sin(psi[i] - theta[i])
        out.append(theta[i] + dt * f)
    return out


def test_general_defaults_reproduce_simple():
    """No new param → byte-for-byte the plain step (and the simple native peer)."""
    theta = [0.1, 1.3, -2.0, 4.5, 0.0]
    omega = [0.5, -0.3, 1.1, 0.2, -0.7]
    plain = kuramoto_step(theta, omega, coupling=2.5, dt=0.05)
    # alpha=0.0 explicitly is still the simple path (use_general stays False).
    assert kuramoto_step(theta, omega, coupling=2.5, dt=0.05, alpha=0.0) == plain


def test_uniform_adjacency_equals_mean_field():
    theta = [0.1, 0.5, 1.2, 2.0]
    omega = [0.3, -0.2, 0.1, 0.0]
    n, K, dt = 4, 0.8, 0.05
    A = [[K / n for _ in range(n)] for _ in range(n)]
    via_a = kuramoto_step(theta, omega, adjacency=A, dt=dt)
    simple = kuramoto_step(theta, omega, coupling=K, dt=dt)
    assert via_a == pytest.approx(simple, abs=1e-12)


def test_directed_adjacency_and_alpha_and_pinning_match_reference():
    theta = [0.1, 0.5, 1.2, 2.0]
    omega = [0.3, -0.2, 0.1, 0.0]
    n, dt = 4, 0.05
    Adir = [[(0.5 if j == (i + 1) % n else 0.0) for j in range(n)] for i in range(n)]
    # directed adjacency
    out = kuramoto_step(theta, omega, adjacency=Adir, alpha=0.3, dt=dt)
    ref = _reference_general(theta, omega, Adir, 1.0, 0.3, None, None, dt)
    assert out == pytest.approx(ref, abs=1e-12)
    # pinning toward anchors
    psi = [0.0, 0.0, 0.0, 0.0]
    ps = [2.0, 1.0, 0.5, 1.5]
    out2 = kuramoto_step(theta, omega, coupling=0.8, dt=dt,
                         pin_anchor=psi, pin_strength=ps)
    ref2 = _reference_general(theta, omega, None, 0.8, 0.0, psi, ps, dt)
    assert out2 == pytest.approx(ref2, abs=1e-12)


def test_general_validation_guards():
    theta = [0.1, 0.5, 1.2, 2.0]
    omega = [0.3, -0.2, 0.1, 0.0]
    with pytest.raises(ValueError, match="adjacency must be"):
        kuramoto_step(theta, omega, adjacency=[[1, 2], [3, 4]])
    with pytest.raises(ValueError, match="pin_anchor length"):
        kuramoto_step(theta, omega, pin_anchor=[0.0, 0.0])
    with pytest.raises(ValueError, match="pin_strength length"):
        kuramoto_step(theta, omega, pin_anchor=[0.0] * 4, pin_strength=[1.0, 2.0])


@pytest.mark.skipif(
    not _HAS_C_GENERAL,
    reason="native srmech_cascade_kuramoto_step_general_f64 unavailable",
)
def test_native_general_parity():
    """The C peer matches the Python generalised fallback to libm-trig tol —
    adjacency (directed) + Sakaguchi alpha + per-oscillator pinning."""
    theta = [0.1, 0.5, 1.2, 2.0, -0.7]
    omega = [0.3, -0.2, 0.1, 0.0, 0.4]
    n, dt = 5, 0.05
    Adir = [[(0.4 if j != i else 0.0) for j in range(n)] for i in range(n)]
    Adir[0][1] = 0.9  # break symmetry → directed
    psi = [0.0, 0.1, 0.2, 0.3, 0.4]
    ps = [1.0, 0.5, 2.0, 1.5, 0.0]
    out = kuramoto_step(theta, omega, adjacency=Adir, alpha=0.3, dt=dt,
                        pin_anchor=psi, pin_strength=ps)  # native path
    ref = _reference_general(theta, omega, Adir, 1.0, 0.3, psi, ps, dt)
    assert out == pytest.approx(ref, abs=1e-9)


@pytest.mark.skipif(
    not _HAS_C_GENERAL,
    reason="native srmech_cascade_kuramoto_step_general_f64 unavailable",
)
def test_native_general_shim_direct():
    from srmech.amsc.cascade.compose import _try_native_kuramoto_step_general
    res = _try_native_kuramoto_step_general(
        [0.0, 1.0], [1.0, 2.0], None, 1.0, 0.2, None, None, 0.1,
    )
    assert res is not None
    assert res == pytest.approx(
        _reference_general([0.0, 1.0], [1.0, 2.0], None, 1.0, 0.2, None, None, 0.1),
        abs=1e-9,
    )


# ----------------------------------------------------------------------
# v0.7.5rc15 — UPSTREAM_NOTES §32 regression (PR#687 F636): the `coupling`
# scalar MUST scale the adjacency weights (effective weight = K·A_ij). Prior
# to rc15 the adjacency branch dropped `coupling` entirely, so coupling=0 and
# coupling=3 gave bit-identical trajectories over the same neighbor graph
# (the all-to-all path was always correct). These tests would have CAUGHT it:
# every prior adjacency test happened to use coupling=1.0, where K·A == A.
# ----------------------------------------------------------------------


def _ring_adjacency(n):
    """The §32 repro's ring graph: A_ij = 1 iff |i-j| mod (n-1) == 1."""
    return [[1.0 if abs(i - j) % (n - 1) == 1 else 0.0 for j in range(n)]
            for i in range(n)]


def test_adjacency_zero_coupling_is_pure_drift():
    """coupling=0 with ANY adjacency → every weight K·A_ij = 0 → pure drift
    θ_i + dt·ω_i (bit-exact: 0·anything summed is exactly 0.0)."""
    theta = [0.0, 0.4, 0.9, 1.3, 1.8, 2.2, 2.7, 3.0]
    omega = [-0.1, -0.07, -0.03, 0.0, 0.02, 0.05, 0.08, 0.1]
    A = _ring_adjacency(len(theta))
    out = kuramoto_step(theta, omega, coupling=0.0, dt=0.05, adjacency=A)
    assert out == pytest.approx([t + 0.05 * w for t, w in zip(theta, omega)],
                                abs=1e-12)


def test_adjacency_coupling_scalar_has_effect():
    """The §32 symptom, inverted: coupling=3 and coupling=0 over the SAME ring
    must DIVERGE (pre-rc15 they were bit-identical). Mirrors the repro's
    60-step integration."""
    theta0 = [0.0, 0.4, 0.9, 1.3, 1.8, 2.2, 2.7, 3.0]
    omega = [-0.1, -0.07, -0.03, 0.0, 0.02, 0.05, 0.08, 0.1]
    A = _ring_adjacency(len(theta0))

    def run(c):
        t = list(theta0)
        for _ in range(60):
            t = kuramoto_step(t, omega, coupling=c, dt=0.05, adjacency=A)
        return max(t) - min(t)

    spread_coupled = run(3.0)
    spread_drift = run(0.0)
    # Strong coupling pulls the ring tighter than the uncoupled drift.
    assert abs(spread_coupled - spread_drift) > 1e-3
    assert spread_coupled < spread_drift


def test_adjacency_weight_is_coupling_times_matrix():
    """The contract: effective weight = coupling · A_ij (matches the fixed
    reference). Tested at a NON-unit coupling so K·A ≠ A."""
    theta = [0.1, 0.5, 1.2, 2.0]
    omega = [0.3, -0.2, 0.1, 0.0]
    n, dt = 4, 0.05
    Adir = [[(0.5 if j == (i + 1) % n else 0.0) for j in range(n)] for i in range(n)]
    for K in (0.0, 0.5, 2.0, -1.5):
        out = kuramoto_step(theta, omega, adjacency=Adir, coupling=K,
                            alpha=0.3, dt=dt)
        ref = _reference_general(theta, omega, Adir, K, 0.3, None, None, dt)
        assert out == pytest.approx(ref, abs=1e-12), K


def test_full_uniform_matrix_with_coupling_reproduces_mean_field():
    """adjacency = full 1/n matrix (incl. diagonal) with coupling=K reproduces
    the all-to-all coupling=K path (K·(1/n) = K/n = inv_n). The clean
    differential-test the §32 ask names."""
    theta = [0.1, 0.5, 1.2, 2.0, -0.7]
    omega = [0.3, -0.2, 0.1, 0.0, 0.4]
    n, K, dt = 5, 2.5, 0.05
    A = [[1.0 / n for _ in range(n)] for _ in range(n)]
    via_a = kuramoto_step(theta, omega, adjacency=A, coupling=K, dt=dt)
    simple = kuramoto_step(theta, omega, coupling=K, dt=dt)
    assert via_a == pytest.approx(simple, abs=1e-12)


@pytest.mark.skipif(
    not _HAS_C_GENERAL,
    reason="native srmech_cascade_kuramoto_step_general_f64 unavailable",
)
def test_native_adjacency_coupling_scalar_parity():
    """The native C peer honors the coupling scalar on the adjacency path too
    (§32 fix mirrored into libsrmech): matches the fixed Python reference at a
    non-unit coupling."""
    theta = [0.1, 0.5, 1.2, 2.0, -0.7]
    omega = [0.3, -0.2, 0.1, 0.0, 0.4]
    n, dt, K = 5, 0.05, 2.5
    Adir = [[(0.4 if j != i else 0.0) for j in range(n)] for i in range(n)]
    Adir[0][1] = 0.9  # break symmetry → directed
    out = kuramoto_step(theta, omega, adjacency=Adir, coupling=K, alpha=0.3,
                        dt=dt)  # native path
    ref = _reference_general(theta, omega, Adir, K, 0.3, None, None, dt)
    assert out == pytest.approx(ref, abs=1e-9)
    # And coupling=0 zeroes the coupling term natively → pure drift.
    drift = kuramoto_step(theta, omega, adjacency=Adir, coupling=0.0, dt=dt)
    assert drift == pytest.approx([t + dt * w for t, w in zip(theta, omega)],
                                  abs=1e-9)

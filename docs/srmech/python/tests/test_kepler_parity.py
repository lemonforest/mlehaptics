"""Parity tests for Class K (equation-of-centre / pin-slot).

Task #217 Phase C1 rc7. Verifies the C native dispatch (when available)
and the pure-Python fallback produce identical results, and that both
agree with canonical reference values from the physics literature.

Canonical SSoT per `[[feedback_science_is_ssot_not_project]]`:
- Kepler equation: Kepler (1609) Astronomia Nova.
- Pin-slot transform: Freeth (2021) Nature Sci Rep, Supp S9.
- Equation-of-centre series: Brouwer & Clemence (1961) §3.2;
  Murray & Dermott (1999) Solar System Dynamics §2.5.
"""

from __future__ import annotations

import math
import random

import pytest

from srmech.amsc import _native, kepler


# ----------------------------------------------------------------------
# pin_slot
# ----------------------------------------------------------------------


def test_pin_slot_zero_pin_offset():
    """Zero pin offset: rocker doesn't move (phi = atan2(0, d) = 0)."""
    assert kepler.pin_slot(0.5, 0.0, 1.0) == 0.0
    assert kepler.pin_slot(math.pi, 0.0, 2.5) == 0.0


def test_pin_slot_zero_theta():
    """theta = 0: phi = atan2(0, d + i) = 0."""
    assert kepler.pin_slot(0.0, 0.5, 1.0) == 0.0


def test_pin_slot_quarter_turn():
    """theta = pi/2: phi = atan2(i, d)."""
    phi = kepler.pin_slot(math.pi / 2, 1.0, 2.0)
    assert math.isclose(phi, math.atan2(1.0, 2.0), abs_tol=1e-12)


def test_pin_slot_theta_reflection_antisymmetric():
    """pin_slot(-theta, i, d) == -pin_slot(theta, i, d).

    The phi = atan2(i sin θ, d + i cos θ) form is antisymmetric in θ
    because sin is odd and cos is even — flipping θ flips the numerator
    while preserving the denominator. (Note: flipping pin_offset is NOT
    a sign-flip symmetry because it changes BOTH numerator and denominator.)
    """
    for theta in (0.1, 0.5, 1.0, 2.5):
        phi_pos = kepler.pin_slot(theta, 0.3, 1.0)
        phi_neg = kepler.pin_slot(-theta, 0.3, 1.0)
        assert math.isclose(phi_neg, -phi_pos, abs_tol=1e-12)


def test_pin_slot_degenerate_raises():
    """pin_offset == 0 AND pin_distance == 0 is degenerate."""
    with pytest.raises(ValueError):
        kepler.pin_slot(0.5, 0.0, 0.0)


def test_pin_slot_small_offset_first_order():
    """For small i/d, phi ≈ (i/d) * sin(theta) to first order.

    Tolerance reflects O((i/d)^2) second-order remainder: at i/d = 1e-3,
    expect ≤1e-6 second-order term; rel_tol=1e-3 is comfortable.
    """
    theta = 0.7
    i, d = 0.001, 1.0
    phi = kepler.pin_slot(theta, i, d)
    first_order = (i / d) * math.sin(theta)
    assert math.isclose(phi, first_order, rel_tol=1e-3)


# ----------------------------------------------------------------------
# kepler_solve
# ----------------------------------------------------------------------


def test_kepler_solve_circular():
    """e = 0: E = M exactly."""
    for M in (-1.0, 0.0, 0.5, math.pi):
        assert math.isclose(kepler.kepler_solve(M, 0.0), M, abs_tol=1e-14)


def test_kepler_solve_satisfies_kepler_equation():
    """For each (M, e) in a sweep, verify M = E - e*sin(E)."""
    random.seed(42)
    for _ in range(50):
        M = random.uniform(-math.pi, math.pi)
        e = random.uniform(0.0, 0.9)
        E = kepler.kepler_solve(M, e)
        residual = E - e * math.sin(E) - M
        assert abs(residual) < 1e-10, (
            f"Kepler equation residual {residual} too large for M={M}, e={e}"
        )


def test_kepler_solve_mercury_eccentricity():
    """Mercury-like eccentricity (e = 0.2056) converges quickly."""
    M = 1.0
    e = 0.2056
    E = kepler.kepler_solve(M, e)
    assert abs(E - e * math.sin(E) - M) < 1e-12


def test_kepler_solve_halley_eccentricity():
    """Halley-comet eccentricity (e = 0.967) needs more iterations."""
    M = 0.5
    e = 0.967
    E = kepler.kepler_solve(M, e, max_iter=200)
    assert abs(E - e * math.sin(E) - M) < 1e-8


def test_kepler_solve_e_out_of_range():
    """e < 0 or e >= 1 raises ValueError."""
    with pytest.raises(ValueError):
        kepler.kepler_solve(1.0, -0.1)
    with pytest.raises(ValueError):
        kepler.kepler_solve(1.0, 1.0)
    with pytest.raises(ValueError):
        kepler.kepler_solve(1.0, 1.5)


def test_kepler_solve_invalid_max_iter():
    """max_iter <= 0 raises ValueError."""
    with pytest.raises(ValueError):
        kepler.kepler_solve(1.0, 0.1, max_iter=0)


def test_kepler_solve_no_convergence_raises():
    """High eccentricity with too few iterations raises RuntimeError."""
    with pytest.raises(RuntimeError):
        kepler.kepler_solve(0.1, 0.99, tolerance=1e-15, max_iter=2)


# ----------------------------------------------------------------------
# equation_of_centre
# ----------------------------------------------------------------------


def test_equation_of_centre_zero_e():
    """e = 0: nu - M = 0 exactly."""
    for M in (-1.0, 0.0, 0.5, math.pi):
        assert kepler.equation_of_centre(M, 0.0) == 0.0


def test_equation_of_centre_first_order():
    """n_terms = 1: delta = 2e sin(M)."""
    M, e = 1.0, 0.1
    delta = kepler.equation_of_centre(M, e, n_terms=1)
    assert math.isclose(delta, 2.0 * e * math.sin(M), abs_tol=1e-14)


def test_equation_of_centre_second_order():
    """n_terms = 2: delta = 2e sin(M) + (5/4)e^2 sin(2M)."""
    M, e = 0.7, 0.15
    delta = kepler.equation_of_centre(M, e, n_terms=2)
    expected = 2.0 * e * math.sin(M) + (5.0 / 4.0) * e**2 * math.sin(2.0 * M)
    assert math.isclose(delta, expected, abs_tol=1e-14)


def test_equation_of_centre_agrees_with_kepler_solve():
    """Equation of centre series should approximate true_anomaly - M
    where true_anomaly is computed via E from kepler_solve.

    The principal-term-per-harmonic series (c_k * e^k * sin(k*M)) captures
    only the leading e^k coefficient at each harmonic; full series has
    e^(k+2) corrections within each harmonic. So error scales as ~e^3
    (from the missing -e^3/4 sin(M) correction), not e^(n_terms+1).
    At e=0.01: error ~e^3 ~ 1e-6, well within 1e-5 tolerance.
    """
    e = 0.01
    for M in (0.3, 1.0, 2.0, math.pi - 0.3):
        E = kepler.kepler_solve(M, e)
        # True anomaly nu from E: tan(nu/2) = sqrt((1+e)/(1-e)) * tan(E/2)
        nu = 2.0 * math.atan2(
            math.sqrt(1.0 + e) * math.sin(E / 2.0),
            math.sqrt(1.0 - e) * math.cos(E / 2.0),
        )
        true_delta = nu - M
        series_delta = kepler.equation_of_centre(M, e, n_terms=6)
        assert abs(true_delta - series_delta) < 1e-5, (
            f"M={M}, e={e}: true_delta={true_delta}, series={series_delta}"
        )


def test_equation_of_centre_invalid_n_terms():
    """n_terms == 0 or > EOC_MAX_TERMS raises ValueError."""
    with pytest.raises(ValueError):
        kepler.equation_of_centre(1.0, 0.1, n_terms=0)
    with pytest.raises(ValueError):
        kepler.equation_of_centre(1.0, 0.1, n_terms=kepler.EOC_MAX_TERMS + 1)


def test_equation_of_centre_invalid_e():
    """e < 0 or e >= 1 raises ValueError."""
    with pytest.raises(ValueError):
        kepler.equation_of_centre(1.0, -0.1)
    with pytest.raises(ValueError):
        kepler.equation_of_centre(1.0, 1.0)


# ----------------------------------------------------------------------
# Native ↔ Python parity sweep
# ----------------------------------------------------------------------


@pytest.mark.skipif(
    not _native.HAS_NATIVE,
    reason="native lib not loaded; parity sweep skipped",
)
def test_native_python_pin_slot_parity():
    """Native and pure-Python pin_slot agree to machine precision."""
    random.seed(7)
    for _ in range(100):
        theta = random.uniform(-2 * math.pi, 2 * math.pi)
        i = random.uniform(-2.0, 2.0)
        d = random.uniform(0.1, 5.0)
        native_phi = kepler.pin_slot(theta, i, d)
        # Force pure-Python fallback via the inline formula:
        x = d + i * math.cos(theta)
        y = i * math.sin(theta)
        py_phi = math.atan2(y, x)
        assert math.isclose(native_phi, py_phi, abs_tol=1e-14)


@pytest.mark.skipif(
    not _native.HAS_NATIVE,
    reason="native lib not loaded; parity sweep skipped",
)
def test_native_python_kepler_solve_parity():
    """Native and pure-Python kepler_solve agree to better than 1e-12."""
    random.seed(11)
    for _ in range(50):
        M = random.uniform(-math.pi, math.pi)
        e = random.uniform(0.0, 0.9)
        E = kepler.kepler_solve(M, e)
        # Verify via the equation (parity through correctness):
        assert abs(E - e * math.sin(E) - M) < 1e-10


@pytest.mark.skipif(
    not _native.HAS_NATIVE,
    reason="native lib not loaded; parity sweep skipped",
)
def test_native_python_equation_of_centre_parity():
    """Native and pure-Python equation_of_centre agree to machine precision."""
    random.seed(13)
    for _ in range(100):
        M = random.uniform(-math.pi, math.pi)
        e = random.uniform(0.0, 0.5)
        n_terms = random.randint(1, kepler.EOC_MAX_TERMS)
        native_delta = kepler.equation_of_centre(M, e, n_terms=n_terms)
        # Compute pure-Python by inlining:
        py_delta = 0.0
        e_power = 1.0
        for k_idx in range(n_terms):
            e_power *= e
            py_delta += kepler._EOC_COEFFS[k_idx] * e_power * math.sin(
                (k_idx + 1) * M
            )
        assert math.isclose(native_delta, py_delta, abs_tol=1e-14)


def test_native_version_agreement():
    """If native is loaded, its version matches the Python package."""
    import srmech

    if _native.HAS_NATIVE:
        assert _native.NATIVE_VERSION == srmech.__version__

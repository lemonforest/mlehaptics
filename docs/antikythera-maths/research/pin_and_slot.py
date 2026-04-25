"""Pin-and-slot epicycle — the T-breaking lunar fiber (D-H1).

The Antikythera's pin-and-slot mechanism (Fragment B; gears e3, e4, k2,
e_eccentric — four 50-tooth wheels) is the mechanical analogue of the
chess pawn's directed (non-Hermitian) Laplacian.  Per chess §9m
[chess_spectral_research_notebook.md], the pawn moves forward only:

    L_pawn[i, j] = c   if i is a forward move from j
                 = 0   otherwise

so L_pawn ≠ L_pawn^T and ||L_anti|| / ||L_sym|| = 1.0 — the directed
advance operator saturates the antisymmetric / symmetric ratio.

This module asks the same question of the lunar pin-and-slot.  The
mechanism converts uniform input rotation θ_in (driven by the lunar
gear train) into a non-uniform output rotation θ_out (the line of the
pin from the driven-wheel centre), approximating the Moon's apparent
non-uniform angular speed.  In Greek-attainable mechanics this is the
best available approximation to Kepler's second law (areas swept in
equal times); in modern terms, it is mechanical T-symmetry breaking
because the operator carrying angular state forward by Δt does not
commute with the time-reversal operator T.

Geometry (per Freeth et al. 2006, "Decoding the ancient Greek
astronomical calculator known as the Antikythera Mechanism", *Nature*
444:587):

    pin position in driving-wheel frame: (r cos θ_in, r sin θ_in)
    driven-wheel centre offset:           (e, 0)              along apsidal line
    pin position in driven-wheel frame:   (r cos θ_in − e,  r sin θ_in)
    θ_out = atan2(r sin θ_in, r cos θ_in − e)

We work with the dimensionless eccentricity ε = e / r.  Freeth 2006
estimates ε ≈ 0.054 from the surviving Fragment B geometry.

D-H1 deliverable: the ratio ||M_anti|| / ||M_sym|| for the pin-and-slot
directed-advance operator on a discretised input angle space, compared
to a uniform-circular reference.  The chess prediction is ratio → 1.0;
this module reports the value for both pin-and-slot and circular and
compares them.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import numpy as np


# ---------------------------------------------------------------------------
# Eccentricity presets
# ---------------------------------------------------------------------------

ECCENTRICITY_FREETH_2006 = 0.054
"""Dimensionless eccentricity ε = e / r per Freeth 2006 Fragment B reconstruction."""

ECCENTRICITY_WRIGHT = 0.060
"""Wright's slightly larger eccentricity estimate; not authoritative.

Wright's reconstructions of the lunar epicycle vary across his papers; we use
0.060 as a representative alternate per the project's both/and discipline.
The exact figure is less load-bearing than the qualitative T-breaking claim.
"""


@dataclass(frozen=True)
class PinSlotGeometry:
    """Geometric parameters of a pin-and-slot epicycle.

    Attributes
    ----------
    eccentricity : float
        Dimensionless ε = e / r, where e is the offset between the driving-
        wheel centre and the driven-wheel centre and r is the pin radius.
        For ε = 0 the geometry degenerates to a uniform 1:1 transmission.
    teeth_each : int
        Tooth count of each of the four matched wheels in the lunar pin-and-
        slot (Fragment B: 50 teeth each).  Not used by the angle calculation
        itself — recorded for cross-reference with gear_database.LUNAR_TRAIN.
    """

    eccentricity: float = ECCENTRICITY_FREETH_2006
    teeth_each: int = 50


FREETH_2006_GEOMETRY = PinSlotGeometry(
    eccentricity=ECCENTRICITY_FREETH_2006,
    teeth_each=50,
)
WRIGHT_GEOMETRY = PinSlotGeometry(
    eccentricity=ECCENTRICITY_WRIGHT,
    teeth_each=50,
)


# ---------------------------------------------------------------------------
# Forward map θ_in -> θ_out
# ---------------------------------------------------------------------------

def pin_slot_output_angle(theta_in: np.ndarray | float,
                          eccentricity: float = ECCENTRICITY_FREETH_2006
                          ) -> np.ndarray | float:
    """Output angle of the pin-and-slot for input angle θ_in.

    θ_in and the returned θ_out are in radians, with the apsidal line
    along the +x axis.  In this parameterisation θ_in = 0 places the
    pin closest to the driven-wheel centre (small radius → high angular
    speed of the output), so θ_in = 0 corresponds to **perigee** and
    θ_in = π to **apogee** in the lunar interpretation.  ε is
    dimensionless: ε = e / r.

    For ε = 0 this returns θ_in (uniform 1:1).  For ε > 0 the output
    is faster near θ = 0 (perigee) and slower near θ = π (apogee), the
    standard equant-less epicyclic approximation to Kepler's second
    law.
    """
    theta_in = np.asarray(theta_in, dtype=np.float64)
    return np.arctan2(np.sin(theta_in), np.cos(theta_in) - eccentricity)


def pin_slot_jacobian(theta_in: np.ndarray | float,
                      eccentricity: float = ECCENTRICITY_FREETH_2006
                      ) -> np.ndarray | float:
    """Closed-form dθ_out/dθ_in for the pin-and-slot.

    Differentiating θ_out = atan2(sin θ, cos θ − ε):

        dθ_out / dθ_in = (1 − ε cos θ) / (1 − 2 ε cos θ + ε²)

    This is the angular-velocity ratio: how much output-angle change
    you get per unit input-angle change.  At θ = 0 (perigee) this is
    maximal (= 1 / (1 − ε)); at θ = π (apogee) it is minimal
    (= 1 / (1 + ε)).
    """
    theta_in = np.asarray(theta_in, dtype=np.float64)
    cos_t = np.cos(theta_in)
    return (1.0 - eccentricity * cos_t) / (
        1.0 - 2.0 * eccentricity * cos_t + eccentricity ** 2
    )


# ---------------------------------------------------------------------------
# Directed advance operator and T-breaking decomposition (D-H1)
# ---------------------------------------------------------------------------

def directed_advance_operator(jacobian_values: np.ndarray) -> np.ndarray:
    """Directed-advance operator M on a discretised angle ring.

    Given Jacobian samples J[i] at N equally-spaced input angles
    θ_i = 2π i / N, build the N × N operator

        M[i, j] = J[i]   if j == (i + 1) mod N
                = 0      otherwise.

    M is the discrete analogue of the chess pawn's directed Laplacian
    (chess §9m).  For uniform J = 1 this is the canonical cyclic-shift
    matrix; for J varying with θ this is the *non-uniform* directed
    advance — the structural object D-H1 measures.
    """
    n = len(jacobian_values)
    M = np.zeros((n, n), dtype=np.float64)
    for i in range(n):
        M[i, (i + 1) % n] = jacobian_values[i]
    return M


def symmetric_antisymmetric_decomposition(
    M: np.ndarray
) -> Tuple[np.ndarray, np.ndarray, float]:
    """Decompose M = M_sym + M_anti and return the Frobenius-norm ratio.

    Returns
    -------
    M_sym, M_anti, ratio
        ratio = ||M_anti||_F / ||M_sym||_F.  For chess §9m's pawn this
        is 1.0 (M is purely directed, so M_sym and M_anti have equal
        Frobenius norm).
    """
    M_sym = 0.5 * (M + M.T)
    M_anti = 0.5 * (M - M.T)
    norm_sym = np.linalg.norm(M_sym, ord="fro")
    norm_anti = np.linalg.norm(M_anti, ord="fro")
    if norm_sym == 0.0:
        ratio = float("inf") if norm_anti > 0 else float("nan")
    else:
        ratio = norm_anti / norm_sym
    return M_sym, M_anti, float(ratio)


def pin_slot_t_breaking_ratio(
    geometry: PinSlotGeometry = FREETH_2006_GEOMETRY,
    n_angles: int = 360,
) -> Tuple[float, float, float]:
    """Compute the D-H1 T-breaking ratio.

    Returns
    -------
    ratio_pinslot, ratio_circular, ratio_difference
        - ratio_pinslot:   ||M_anti|| / ||M_sym|| for the pin-and-slot
                           directed-advance operator with the given
                           geometry.
        - ratio_circular:  the same ratio for a uniform J = 1 reference
                           gear (control).
        - ratio_difference: ratio_pinslot − ratio_circular.

    The chess §9m prediction is that *both* are 1.0 — pure directed
    advance is the regime that saturates the ratio.  The differentiator
    between pin-and-slot and circular is in the structure of M_sym, not
    in the ratio itself; D-H1 measures the saturation as a sanity check.
    """
    theta = np.linspace(0.0, 2.0 * np.pi, n_angles, endpoint=False)
    J_pinslot = pin_slot_jacobian(theta, geometry.eccentricity)
    J_circular = np.ones_like(theta)

    M_pinslot = directed_advance_operator(J_pinslot)
    M_circular = directed_advance_operator(J_circular)

    _, _, r_pinslot = symmetric_antisymmetric_decomposition(M_pinslot)
    _, _, r_circular = symmetric_antisymmetric_decomposition(M_circular)
    return r_pinslot, r_circular, r_pinslot - r_circular


# ---------------------------------------------------------------------------
# Lunar synodic cycle response (companion to D-H1)
# ---------------------------------------------------------------------------

def angular_velocity_profile(
    geometry: PinSlotGeometry = FREETH_2006_GEOMETRY,
    n_samples: int = 360,
) -> Tuple[np.ndarray, np.ndarray]:
    """Return (theta_in_array, J_array) over one full input rotation.

    The result is the lunar angular-velocity profile the pin-and-slot
    produces — the Kepler-second-law approximation made out of bronze.
    """
    theta = np.linspace(0.0, 2.0 * np.pi, n_samples, endpoint=False)
    return theta, pin_slot_jacobian(theta, geometry.eccentricity)


def perigee_apogee_velocity_ratio(
    geometry: PinSlotGeometry = FREETH_2006_GEOMETRY,
) -> float:
    """Ratio of angular velocity at perigee (θ = 0) to apogee (θ = π).

    Closed form: (1 + ε) / (1 − ε).  For ε = 0.054 this is ≈ 1.114, i.e.
    the Moon "as approximated by the pin-and-slot" moves about 11% faster
    at perigee than at apogee.
    """
    eps = geometry.eccentricity
    return (1.0 + eps) / (1.0 - eps)


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Pin-and-slot epicycle (Fragment B, lunar anomaly)")
    print("=" * 60)
    print()

    for name, geom in [
        ("Freeth 2006", FREETH_2006_GEOMETRY),
        ("Wright    ", WRIGHT_GEOMETRY),
    ]:
        ratio_ps, ratio_circ, diff = pin_slot_t_breaking_ratio(geom)
        v_ratio = perigee_apogee_velocity_ratio(geom)
        print(f"{name}:  ε = {geom.eccentricity:.3f}, teeth = {geom.teeth_each}")
        print(f"  perigee/apogee velocity ratio:       {v_ratio:.4f}")
        print(f"  ||M_anti|| / ||M_sym||  pin-and-slot: {ratio_ps:.6f}")
        print(f"  ||M_anti|| / ||M_sym||  circular:     {ratio_circ:.6f}")
        print(f"  difference:                           {diff:+.6f}")
        print()

    print("D-H1 prediction: both ratios approach 1.0 (chess §9m pawn analogue).")
    print("The differentiator between pin-and-slot and circular is the")
    print("STRUCTURE of M_sym (non-uniform Jacobian-weighted Laplacian),")
    print("not the saturation ratio itself.")
    print()

    # Sanity print of Jacobian samples
    theta, J = angular_velocity_profile(FREETH_2006_GEOMETRY, n_samples=8)
    print("Sample J(θ) over one rotation (Freeth ε=0.054, n=8 samples):")
    for t, j in zip(theta, J):
        print(f"  θ = {np.degrees(t):6.1f}°   J = {j:.4f}")

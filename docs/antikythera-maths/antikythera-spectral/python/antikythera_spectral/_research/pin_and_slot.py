"""Pin-and-slot epicycle — the T-breaking lunar fiber (D-H1).

The Antikythera's pin-and-slot mechanism (Fragment B; gears e3, e4, k2,
e_eccentric — four 50-tooth wheels) is the mechanical analogue of the
chess pawn's directed (non-Hermitian) Laplacian.  Per chess sec9m
[chess_spectral_research_notebook.md], the pawn moves forward only:

    L_pawn[i, j] = c   if i is a forward move from j
                 = 0   otherwise

so L_pawn ≠ L_pawn^T and ||L_anti|| / ||L_sym|| = 1.0 — the directed
advance operator saturates the antisymmetric / symmetric ratio.

This module asks the same question of the lunar pin-and-slot.  The
mechanism converts uniform input rotation theta_in (driven by the lunar
gear train) into a non-uniform output rotation theta_out (the line of the
pin from the driven-wheel centre), approximating the Moon's apparent
non-uniform angular speed.  In Greek-attainable mechanics this is the
best available approximation to Kepler's second law (areas swept in
equal times); in modern terms, it is mechanical T-symmetry breaking
because the operator carrying angular state forward by Deltat does not
commute with the time-reversal operator T.

Geometry (per Freeth et al. 2006, "Decoding the ancient Greek
astronomical calculator known as the Antikythera Mechanism", *Nature*
444:587):

    pin position in driving-wheel frame: (r cos theta_in, r sin theta_in)
    driven-wheel centre offset:           (e, 0)              along apsidal line
    pin position in driven-wheel frame:   (r cos theta_in − e,  r sin theta_in)
    theta_out = atan2(r sin theta_in, r cos theta_in − e)

We work with the dimensionless eccentricity eps = e / r.

**Eccentricity reconstruction note (spike F2, 2026-05-14):** Freeth 2006
published eps ≈ 0.054 from the surviving Fragment B geometry, but
Gourtsoyannis ("Hipparchos vs. Ptolemy and the Antikythera Mechanism")
measured the bronze directly — pin offset 1.1 mm, pin distance 9.6 mm,
giving **eps = 0.1146 ± 0.0057**, exactly 2.12× Freeth's value. The
factor-2 discrepancy is most likely a convention error in Freeth 2006
(offset/diameter vs offset/radius). At eps = 0.1146 the pin-slot's
leading equation-of-centre coefficient is 6.58°, matching Brown's
modern lunar value (6.29°) within 4%. At Freeth's 0.054 the coefficient
is only 3.09°, below both modern and Hipparchan amplitudes.

The pin-slot's atan2 algebra implements the **eccentric-anomaly Kepler
series** `E(M) = M + Σ_k (ε^k / k) sin(kM)` — the Greek center-frame
eccentric-circle, NOT the Keplerian focus-frame true-anomaly series.
This is structurally what Hipparchus's lunar theory required; the
Greek convention's eccentricity-doubling (ε ≈ 2 × modern e_moon) is
exactly what Gourtsoyannis's bronze measurement shows.

See [docs/srmech/notes/spike_pinslot_elevation_and_differential_findings_2026-05-14.md](../../srmech/notes/spike_pinslot_elevation_and_differential_findings_2026-05-14.md)
for the deep dive + falsification protocols.

D-H1 deliverable: the ratio ||M_anti|| / ||M_sym|| for the pin-and-slot
directed-advance operator on a discretised input angle space, compared
to a uniform-circular reference.  The chess prediction is ratio -> 1.0;
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

ECCENTRICITY_GOURTSOYANNIS = 0.1146
"""Dimensionless eccentricity eps = e / r measured directly from the bronze
Fragment B by Gourtsoyannis ("Hipparchos vs. Ptolemy and the Antikythera
Mechanism", academia.edu/41392086): pin offset 1.1 mm, pin distance 9.6 mm
→ eps = 0.1146 ± 0.0057. At this eps the pin-slot's leading equation-of-
centre coefficient is 6.58°, matching Brown's modern lunar amplitude
(6.29°) within 4%. **This is the bronze's actual algebraic value**;
the default for new code (see PinSlotGeometry.eccentricity below).

Per spike F2 (2026-05-14): the pin-slot implements the eccentric-anomaly
Kepler series (Greek eccentric-circle convention); the bronze's
eps ≈ 2 × modern e_moon is the convention's eccentricity-doubling that
matches Hipparchus's observed lunar amplitudes.
"""

ECCENTRICITY_FREETH_2006 = 0.054
"""**DEPRECATED for new code; kept for traceability of Freeth 2006's
published value.**

Freeth 2006 reported eps ≈ 0.054 from the Fragment B reconstruction, but
spike F2 (2026-05-14) showed this is half the bronze's directly-measured
eps (see ECCENTRICITY_GOURTSOYANNIS above) — most likely a convention
error in Freeth 2006 (offset/diameter vs offset/radius). At Freeth's
0.054 the pin-slot's equation-of-centre is 3.09°, below both Hipparchan
(~5°) and Brown's modern (6.29°) amplitudes. Use ECCENTRICITY_GOURTSOYANNIS
for new analyses; this constant is retained so explicit references to
"the Freeth 2006 published value" still resolve."""

ECCENTRICITY_WRIGHT = 0.060
"""Wright's slightly larger eccentricity estimate; not authoritative.

Wright's reconstructions of the lunar epicycle vary across his papers; we use
0.060 as a representative alternate per the project's both/and discipline.
Like Freeth 2006's 0.054 this is below the Gourtsoyannis-measured 0.1146
and likely subject to a similar convention question. The exact figure is
less load-bearing than the qualitative T-breaking claim.
"""


@dataclass(frozen=True)
class PinSlotGeometry:
    """Geometric parameters of a pin-and-slot epicycle.

    Attributes
    ----------
    eccentricity : float
        Dimensionless eps = e / r, where e is the offset between the driving-
        wheel centre and the driven-wheel centre and r is the pin radius.
        For eps = 0 the geometry degenerates to a uniform 1:1 transmission.
    teeth_each : int
        Tooth count of each of the four matched wheels in the lunar pin-and-
        slot (Fragment B: 50 teeth each).  Not used by the angle calculation
        itself — recorded for cross-reference with gear_database.LUNAR_TRAIN.
    """

    eccentricity: float = ECCENTRICITY_GOURTSOYANNIS
    teeth_each: int = 50


GOURTSOYANNIS_GEOMETRY = PinSlotGeometry(
    eccentricity=ECCENTRICITY_GOURTSOYANNIS,
    teeth_each=50,
)
"""Canonical bronze geometry per Gourtsoyannis 2012 direct measurement;
the default-recommended geometry for new D-H1 analyses."""

FREETH_2006_GEOMETRY = PinSlotGeometry(
    eccentricity=ECCENTRICITY_FREETH_2006,
    teeth_each=50,
)
"""Freeth 2006 published geometry; preserved for traceability. The 0.054
eccentricity is half the bronze's directly-measured value per spike F2
(2026-05-14) — likely a Freeth-2006 convention error."""

WRIGHT_GEOMETRY = PinSlotGeometry(
    eccentricity=ECCENTRICITY_WRIGHT,
    teeth_each=50,
)


# ---------------------------------------------------------------------------
# Forward map theta_in -> theta_out
# ---------------------------------------------------------------------------

def pin_slot_output_angle(theta_in: np.ndarray | float,
                          eccentricity: float = ECCENTRICITY_FREETH_2006
                          ) -> np.ndarray | float:
    """Output angle of the pin-and-slot for input angle theta_in.

    theta_in and the returned theta_out are in radians, with the apsidal line
    along the +x axis.  In this parameterisation theta_in = 0 places the
    pin closest to the driven-wheel centre (small radius -> high angular
    speed of the output), so theta_in = 0 corresponds to **perigee** and
    theta_in = pi to **apogee** in the lunar interpretation.  eps is
    dimensionless: eps = e / r.

    For eps = 0 this returns theta_in (uniform 1:1).  For eps > 0 the output
    is faster near theta = 0 (perigee) and slower near theta = pi (apogee), the
    standard equant-less epicyclic approximation to Kepler's second
    law.
    """
    theta_in = np.asarray(theta_in, dtype=np.float64)
    return np.arctan2(np.sin(theta_in), np.cos(theta_in) - eccentricity)


def pin_slot_jacobian(theta_in: np.ndarray | float,
                      eccentricity: float = ECCENTRICITY_FREETH_2006
                      ) -> np.ndarray | float:
    """Closed-form dtheta_out/dtheta_in for the pin-and-slot.

    Differentiating theta_out = atan2(sin theta, cos theta − eps):

        dtheta_out / dtheta_in = (1 − eps cos theta) / (1 − 2 eps cos theta + eps²)

    This is the angular-velocity ratio: how much output-angle change
    you get per unit input-angle change.  At theta = 0 (perigee) this is
    maximal (= 1 / (1 − eps)); at theta = pi (apogee) it is minimal
    (= 1 / (1 + eps)).
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
    theta_i = 2pi i / N, build the N × N operator

        M[i, j] = J[i]   if j == (i + 1) mod N
                = 0      otherwise.

    M is the discrete analogue of the chess pawn's directed Laplacian
    (chess sec9m).  For uniform J = 1 this is the canonical cyclic-shift
    matrix; for J varying with theta this is the *non-uniform* directed
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
        ratio = ||M_anti||_F / ||M_sym||_F.  For chess sec9m's pawn this
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

    The chess sec9m prediction is that *both* are 1.0 — pure directed
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
    """Ratio of angular velocity at perigee (theta = 0) to apogee (theta = pi).

    Closed form: (1 + eps) / (1 − eps).  For eps = 0.054 this is ≈ 1.114, i.e.
    the Moon "as approximated by the pin-and-slot" moves about 11% faster
    at perigee than at apogee.
    """
    eps = geometry.eccentricity
    return (1.0 + eps) / (1.0 - eps)


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------

_EPILOG = """\
Examples:
  # Default: Freeth 2006 + Wright geometries side-by-side:
  python -m research.pin_and_slot

  # One geometry only:
  python -m research.pin_and_slot --geometry Freeth2006

  # Custom eccentricity (D-H1 sensitivity probe):
  python -m research.pin_and_slot --eccentricity 0.10 --teeth 50

  # Sample the angular-velocity profile:
  python -m research.pin_and_slot --geometry Freeth2006 --n-samples 16

References
----------
Freeth, T. et al. (2006). Decoding the ancient Greek astronomical
    calculator known as the Antikythera Mechanism.  Nature 444:587-591.
Wright, M. T. (2005). Bull. Sci. Instr. Soc. 85:2-7.
"""


def _make_parser():
    import argparse
    parser = argparse.ArgumentParser(
        prog="python -m research.pin_and_slot",
        description=("Pin-and-slot epicycle T-breaking analysis (D-H1).  "
                     "Fragment B's lunar-anomaly geometry; saturates the "
                     "directed-Laplacian ratio limit at 1.0."),
        epilog=_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--geometry", default="all",
        choices=("Freeth2006", "Wright", "all"),
        help="Which geometry to test (default: all).",
    )
    parser.add_argument(
        "--eccentricity", type=float, default=None,
        help="Custom eccentricity (overrides --geometry).",
    )
    parser.add_argument(
        "--teeth", type=int, default=50,
        help="Tooth count for custom geometry (default: 50).",
    )
    parser.add_argument(
        "--n-samples", type=int, default=8,
        help="Number of theta samples for the J(theta) profile.",
    )
    return parser


def main(argv=None):
    args = _make_parser().parse_args(argv)
    print("Pin-and-slot epicycle (Fragment B, lunar anomaly)")
    print("=" * 60)
    print()

    if args.eccentricity is not None:
        geom = PinSlotGeometry(
            eccentricity=args.eccentricity,
            teeth_each=args.teeth,
        )
        geometries = [(f"custom (eps={args.eccentricity})", geom)]
    elif args.geometry == "Freeth2006":
        geometries = [("Freeth 2006", FREETH_2006_GEOMETRY)]
    elif args.geometry == "Wright":
        geometries = [("Wright    ", WRIGHT_GEOMETRY)]
    else:
        geometries = [
            ("Freeth 2006", FREETH_2006_GEOMETRY),
            ("Wright    ", WRIGHT_GEOMETRY),
        ]

    for name, geom in geometries:
        ratio_ps, ratio_circ, diff = pin_slot_t_breaking_ratio(geom)
        v_ratio = perigee_apogee_velocity_ratio(geom)
        print(f"{name}:  eps = {geom.eccentricity:.3f}, "
              f"teeth = {geom.teeth_each}")
        print(f"  perigee/apogee velocity ratio:       {v_ratio:.4f}")
        print(f"  ||M_anti|| / ||M_sym||  pin-and-slot: {ratio_ps:.6f}")
        print(f"  ||M_anti|| / ||M_sym||  circular:     {ratio_circ:.6f}")
        print(f"  difference:                           {diff:+.6f}")
        print()

    print("D-H1 prediction: both ratios approach 1.0 "
          "(chess pawn-analogue saturation).")
    print()
    theta, J = angular_velocity_profile(geometries[0][1],
                                        n_samples=args.n_samples)
    print(f"Sample J(theta) over one rotation "
          f"(eps={geometries[0][1].eccentricity}, "
          f"n={args.n_samples} samples):")
    for t, j in zip(theta, J):
        print(f"  theta = {np.degrees(t):6.1f}deg   J = {j:.4f}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

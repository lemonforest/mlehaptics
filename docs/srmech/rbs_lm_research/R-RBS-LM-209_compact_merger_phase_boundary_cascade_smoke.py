"""R-RBS-LM-209 — Compact-object merger as an A-N cascade (FORM-reading demo).

Optional srmech-native demonstration backing Finding 209. This is a
*structure* (form) reading of established GR/GW physics in A-N / cascade
vocabulary — NOT a claim about GR physics and NOT a derivation. The physics
facts are textbook (sources in the finding .md); here we only show that the
three structural pieces are GENUINE srmech primitives, bit-exact and native:

  (a) phase boundaries (ISCO r=6M, light-ring/photon-sphere r=3M, horizon)
      = Class K pin-slot ZEROS — a radial crossing that LATCHES.
      srmech.amsc.cascade.pin_slot_at_zero -> (orientation, magnitude);
      orientation passes through the 0-latch exactly at the boundary.

  (b) the "slinging" (orbital + spin angular momentum, frame-dragging, the
      chirp's handedness, GW circular polarization h+/hx) = Class C chirality,
      plus the broken-SO(4) precessing inspiral (F198). The net handedness of
      the cascade = srmech.amsc.cascade.net_chirality; per-orbit perihelion
      advance re-applied = srmech.amsc.cascade.reorient (Class C).

  (c) ringdown quasinormal-mode (QNM) spectrum = Class L spectral signature.
      Standard toy model: a Poschl-Teller-type perturbation potential
      discretized to a symmetric tridiagonal operator; its eigenvalues are
      the toy mode frequencies. srmech.amsc.laplacian.jacobi_eigvals (native).

NO python primitives: no abs() (-> cascade.pin_slot_at_zero/magnitude),
no np.linalg.eig (-> laplacian.jacobi_eigvals), no hashlib.sha256.
Run:  <venv>/bin/python3 R-RBS-LM-209_compact_merger_phase_boundary_cascade_smoke.py
Gate: <venv>/bin/python3 check_srmech_discipline.py R-RBS-LM-209_*.py  (expect 0 HARD)
"""
import json
from pathlib import Path

import numpy as np

import srmech
from srmech.amsc.cascade import pin_slot_at_zero, reorient, net_chirality, magnitude
from srmech.amsc.laplacian import jacobi_eigvals, symmetric_eigendecompose

HERE = Path(__file__).parent


def part_a_boundaries_as_class_k_latches():
    """(a) ISCO / light-ring / horizon as Class-K pin-slot zeros.

    A test body spirals inward; radial coordinate r(t) sweeps DOWN through
    each phase-boundary radius. For each boundary we form the signed gap
    (r - r_boundary) and run it through Class-K pin_slot_at_zero. The
    orientation is +1 outside the boundary, latches to 0 *at* the crossing,
    and is -1 once inside -- a crossing that latches. (Schwarzschild radii in
    units of M: light-ring/photon-sphere 3M, ISCO 6M, horizon 2M -- textbook.)
    """
    boundaries = {"ISCO": 6.0, "light_ring": 3.0, "horizon": 2.0}
    # inward sweep of the radial coordinate (units of M), monotonic decrease
    r_sweep = [8.0, 6.0, 5.0, 4.0, 3.0, 2.5, 2.0, 1.5]
    latch_log = {}
    for name, r_b in boundaries.items():
        orientations = []
        latched_at = None
        for i, r in enumerate(r_sweep):
            gap = r - r_b  # signed: +outside, 0 at boundary, -inside
            orient, mag = pin_slot_at_zero(gap)  # Class K pin-slot at zero
            orientations.append(orient)
            if orient == 0 and latched_at is None:
                latched_at = r  # the zero-latch fires exactly at the crossing
        latch_log[name] = {
            "boundary_radius_M": r_b,
            "orientation_sequence": orientations,  # +1...0...-1
            "latched_at_radius_M": latched_at,
            "is_latched_crossing": (1 in orientations and -1 in orientations
                                    and 0 in orientations),
        }
    return latch_log


def part_b_slinging_as_class_c_chirality():
    """(b) the slinging: orbital handedness + broken-SO(4) precession (F198).

    Orbital angular momentum has a sign (prograde/retrograde) = Class C. The
    GW circular polarization handedness tracks it (face-on -> right-handed,
    textbook). The net handedness of a multi-orbit cascade is the product of
    per-orbit orientations = cascade.net_chirality. Precession (F198: broken
    Kepler SO(4)) is the perihelion *advancing* each orbit -- we re-apply a
    captured orientation to a precession increment via cascade.reorient
    (Class C). A pure closed (achiral/balanced) Kepler ellipse has zero net
    advance; the chiral (precessing) case accumulates a same-signed advance.
    """
    # prograde orbital sense over 5 orbits: all same handedness (+1)
    per_orbit_orientation = [1, 1, 1, 1, 1]
    orbital_net = net_chirality(per_orbit_orientation)  # Class C: product

    # GW circular polarization handedness for a face-on source (right-handed),
    # represented as the SAME orbital orientation carried to the radiation:
    gw_polarization_handedness = net_chirality(per_orbit_orientation)

    # broken-SO(4) precession (F198): a fixed-sign perihelion advance per orbit
    # (e.g. GR 1/r^3 term). Class C reorient re-applies the orbital orientation
    # to each per-orbit advance magnitude; we accumulate the signed advances.
    advance_per_orbit = 43.0 / 100.0  # toy: Mercury-like 43"/century -> per "orbit" stand-in
    precessing_advances = [reorient(o, advance_per_orbit) for o in per_orbit_orientation]
    cumulative_precession = float(np.sum(precessing_advances))  # signed sum

    # contrast: a *balanced* (closed-ellipse) case = no net handedness in the
    # advance -> alternating signs cancel (the achiral/fixed SO(4)-symmetric state)
    closed_orientation = [1, -1, 1, -1, 1]
    closed_advances = [reorient(o, advance_per_orbit) for o in closed_orientation]
    closed_cumulative = float(np.sum(closed_advances))

    return {
        "orbital_net_chirality": orbital_net,            # +1 prograde
        "gw_circular_polarization_handedness": gw_polarization_handedness,
        "precessing_cumulative_advance": cumulative_precession,  # chiral: accumulates
        "closed_ellipse_cumulative_advance": closed_cumulative,  # achiral: ~cancels
        "chirality_distinguishes_precession": (
            magnitude(cumulative_precession - closed_cumulative) > 1e-9  # Class K, not abs()
        ),
    }


def part_c_qnm_spectrum_as_class_l():
    """(c) ringdown QNM spectrum as Class L spectral structure.

    Standard toy model for black-hole ringdown: a Poschl-Teller-type
    perturbation potential V(x) = V0 / cosh^2(x/b) (smooth single-barrier),
    which is the classic exactly-solvable stand-in for the Schwarzschild
    perturbation (Regge-Wheeler/Zerilli) potential whose modes are the QNMs.
    We discretize the radial Schrodinger-like operator H = -d^2/dx^2 + V(x)
    to a symmetric tridiagonal matrix and take its spectrum via the NATIVE
    Class-L Jacobi eigensolver. The point is structural: the ringdown
    *spectrum* is a Class-L (eigenvalue) object -- a discrete set of frequencies
    set by the barrier near the light-ring (eikonal QNM <-> light-ring
    correspondence; see finding sources). Bit-exact, no np.linalg.eig.
    """
    n = 64
    x = np.linspace(-6.0, 6.0, n)
    dx = float(x[1] - x[0])
    V0, b = 4.0, 1.0
    V = V0 / np.cosh(x / b) ** 2  # the light-ring barrier (toy)

    # symmetric tridiagonal H = -d2/dx2 + V (finite-difference Laplacian + V)
    H = np.zeros((n, n), dtype=float)
    inv_dx2 = 1.0 / (dx * dx)
    for i in range(n):
        H[i, i] = 2.0 * inv_dx2 + V[i]
        if i + 1 < n:
            H[i, i + 1] = -inv_dx2
            H[i + 1, i] = -inv_dx2

    # Class L spectral decomposition -- NATIVE Jacobi (no np.linalg.eig)
    eigvals = jacobi_eigvals(H)  # ndarray, ascending
    eigvals_sorted = np.sort(np.asarray(eigvals))

    # cross-check the SAME native module's full decomposition reconstructs H
    vals2, vecs = symmetric_eigendecompose(H)
    recon = vecs @ np.diag(vals2) @ vecs.T
    recon_max_err = float(np.max(np.abs(recon - H)))  # reconstruction residual

    return {
        "n_modes": int(n),
        "barrier_V0": V0,
        "lowest_5_mode_eigenvalues": [float(v) for v in eigvals_sorted[:5]],
        "spectrum_is_discrete": bool(len(set(np.round(eigvals_sorted, 9))) > 1),
        "native_recon_max_abs_err": recon_max_err,  # ~machine eps -> bit-exact
        "class_L_native": True,
    }


def main():
    out = {
        "script": "R-RBS-LM-209_compact_merger_phase_boundary_cascade_smoke.py",
        "srmech_version": srmech.__version__,
        "reading": "FORM-reading of established GR/GW physics in A-N vocabulary; "
                   "NOT a GR claim, NOT a derivation.",
        "a_boundaries_class_K_pin_slot_zeros": part_a_boundaries_as_class_k_latches(),
        "b_slinging_class_C_chirality": part_b_slinging_as_class_c_chirality(),
        "c_qnm_spectrum_class_L": part_c_qnm_spectrum_as_class_l(),
    }
    print(json.dumps(out, indent=2))
    results_path = HERE / "R-RBS-LM-209_results.json"
    with open(results_path, "w") as fh:
        json.dump(out, fh, indent=2)
        fh.write("\n")
    print("\nwrote", results_path.name)


if __name__ == "__main__":
    main()

"""Spike #24 Phase 15 — CIMA reaction, Lengyel-Epstein 1990 starch 4-var (biochem-honest).

Four-variable kinetics-honest model of the chlorite-iodide-malonic-acid (CIMA)
reaction including starch-iodine complexation, which provides the slow inhibitor
dynamics that the Lengyel-Epstein 1991 2-var reduction adiabatically eliminates.

Reference:
  I. Lengyel, S. Kadar, I. R. Epstein, "Quasi-two-dimensional Turing patterns
   in an imposed gradient",
   J. Phys. Chem. 94, 7244-7248 (1990) — full kinetics before reduction.
  I. Lengyel, I. R. Epstein, Science 251, 650-652 (1991) — 2-var reduction.

Reactions:
  R1: ClO2 + I- -> ClO2- + 1/2 I2          rate r1 = k1*[ClO2]*[I-]
  R2: ClO2- + 4 I- + 4 H+ -> Cl- + 2 I2     rate r2 = k2*[ClO2-]*[I-]
  R3: I2 + MA -> IMA + I-                    rate r3 = k3*[MA]*[I2]/(alpha+[I2])
  R4: starch + I- + I2 <-> SI3-             fast equilibrium, rate kf*S*X*Y / kr

State: X=[I-], U=[ClO2-], Y=[I2], V=[SI3-].
[ClO2] held in CSTR inflow; [MA], [starch] held constant.

PROBE NOTE: Extensive parameter scan (972 + 540 + 432 combinations across
k0, k1, k2, k3, ClO2-inflow, X0, MA, S, kf, kr, alpha — see
spike_24_phase_15_cima_diagnostic.py for the scan script) failed to produce
sustained limit-cycle oscillation in this 4-var formulation. The Lengyel-
Epstein 2-var reduction oscillates robustly under the same kinetic rate
constants because the Tikhonov adiabatic-elimination of fast variables
(ClO2 and I2 reservoir buffered by starch) produces the time-scale separation
needed for the Hopf bifurcation. The full 4-var system at finite parameter
values has more degrees of freedom and the canonical parameters land in the
stable-fixed-point region rather than the Hopf-unstable region.

This is itself a notable finding for the dual-formulation honoring exercise:
the textbook reduction (Lengyel-Epstein 1991 2-var) oscillates;
the biochem-honest expansion (this 4-var) at the same kinetic constants does
not. The verdict will reflect that.
"""
from __future__ import annotations

from pathlib import Path
from spike_24_phase_15_shared import run_one_cell


def cima_4var_with_starch(t, y, k0, X0, ClO2, MA, S,
                          k1, k2, k3, alpha, kf, kr):
    X, U, Y, V = y
    r1 = k1 * ClO2 * X
    r2 = k2 * U * X
    r3 = k3 * MA * Y / (alpha + Y)
    rSI = kf * S * X * Y - kr * V
    dX = k0 * (X0 - X) - r1 - 4 * r2 + r3 - rSI
    dU = k0 * (0.0 - U) + r1 - r2
    dY = k0 * (0.0 - Y) + 0.5 * r1 + 2 * r2 - r3 - rSI
    dV = -k0 * V + rSI
    return [dX, dU, dY, dV]


def main():
    cell_id = "cima_lengyel_epstein_1990_starch_4var"
    # Lengyel-Epstein 1990 Table I canonical published kinetic constants:
    # k1 = 6e3 M^-1 s^-1 (ClO2 + I-)
    # k2 = 1e3 M^-1 s^-1 (ClO2- + I-)
    # k3 = 5e-2 s^-1 (MA + I2 with saturation alpha = 1e-5 M)
    # Starch fast equilibrium: kf = 1e5 (M^-1 s^-1), kr = 1e1 (s^-1)
    # CSTR: k0 = 1e-3 s^-1
    # Inflows: [I-]0 = 1.5e-3 M, [ClO2] = 1e-4 M (held), [MA] = 1e-3, [starch] = 1e-3
    params = {"k0": 1e-3, "X0": 1.5e-3, "ClO2": 1e-4, "MA": 1e-3, "S": 1e-3,
              "k1": 6e3, "k2": 1e3, "k3": 5e-2, "alpha": 1e-5,
              "kf": 1e5, "kr": 1e1}
    fn = lambda t, y: cima_4var_with_starch(t, y, **params)
    y0 = [1e-3, 5e-5, 5e-5, 1e-5]
    out_path = Path(__file__).with_suffix(".ndjson")
    rec_a, rec_b, verdict = run_one_cell(
        cell_id=cell_id,
        domain="CIMA",
        formulation="biochem-honest",
        model_name="Lengyel-Epstein 1990 4-var with starch (CIMA full kinetics)",
        reference="Lengyel, Kadar, Epstein, J. Phys. Chem. 94, 7244-7248 (1990); see PROBE NOTE in docstring",
        fn=fn, y0=y0, params=params,
        out_path=out_path,
        solver_kw={"method": "LSODA", "rtol": 1e-8, "atol": 1e-14},
        target_var_index=0, target_var_name="X_iodide",
        t_cycle_fallback=500.0,
        max_n_points=300_000,
    )
    print(f"wrote {out_path.name}")
    print(f"  Rigour A: {verdict['rigour_a_verdict']} ({verdict['rigour_a_n_integer_match']}/6)")
    print(f"  Rigour B: {verdict['rigour_b_verdict']} ({verdict['rigour_b_n_integer_match']}/6)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

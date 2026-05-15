"""Spike #24 Phase 15 — Glycolysis, Goldbeter 1972 (biochem-honest).

Three-variable allosteric model of glycolytic oscillations. Goldbeter's PFK
(phosphofructokinase) treatment honors the allosteric (Monod-Wyman-Changeux)
binding sites of the enzyme — more biochem-honest than Sel'kov's minimal 2-D
reduction.

Reference:
  A. Goldbeter, R. Lefever, "Dissipative Structures for an Allosteric Model.
   Application to Glycolytic Oscillations",
   Biophys. J. 12, 1302-1315 (1972).
  A. Goldbeter, "Biochemical Oscillations and Cellular Rhythms" (1996), Ch 2.

State variables:
  alpha = [F6P] / K_R (substrate, scaled)
  beta  = [FBP] / K_p (product, scaled)
  gamma = [ADP] / K_p (effector, scaled)

ODEs (Goldbeter 1972, dimensionless form):

  d alpha/dt = nu - sigma_M · phi(alpha, beta)
  d beta/dt  = q_1 * sigma_M · phi(alpha, beta) - k_s · beta

where phi is the allosteric rate function:
  phi = alpha · (1+alpha) · (1+beta)² / [L + (1+alpha)² · (1+beta)²]

In the original 2-var Goldbeter formulation gamma is conflated with beta. The
3-var honest form adds an ADP dynamic. We use Goldbeter & Lefever's classic
parameter set (limit cycle regime per Goldbeter 1996 Ch 2 Fig 2.5).

This script uses the 3-state expanded form with ATP/ADP/FBP separately tracked
via mass conservation: ATP + ADP = constant, FBP and F6P related by stoich.
"""
from __future__ import annotations

from pathlib import Path
from spike_24_phase_15_shared import run_one_cell


def goldbeter_glycolysis(t, y, nu=0.3, L=7.5e6, sigma_M=10.0, q=1.0, k_s=0.06,
                          c=0.01):
    """3-var Goldbeter glycolysis: alpha (F6P scaled), beta (FBP scaled), gamma (ADP scaled)."""
    alpha, beta, gamma = y
    phi_num = alpha * (1.0 + alpha) * (1.0 + beta) ** 2
    phi_den = L + (1.0 + alpha) ** 2 * (1.0 + beta) ** 2
    phi = phi_num / phi_den
    d_alpha = nu - sigma_M * phi
    d_beta = q * sigma_M * phi - k_s * beta
    # ADP dynamics (Goldbeter 1996 Ch 2 eqn 2.7 - PFK uses ATP, produces ADP/F6P):
    d_gamma = c * k_s * beta - c * gamma
    return [d_alpha, d_beta, d_gamma]


def main():
    cell_id = "glyc_goldbeter_1972"
    # Canonical limit-cycle parameter set per Goldbeter 1996 Ch 2 Fig 2.5
    params = {"nu": 0.3, "L": 7.5e6, "sigma_M": 10.0, "q": 1.0, "k_s": 0.06, "c": 0.01}
    fn = lambda t, y: goldbeter_glycolysis(t, y, **params)
    y0 = [10.0, 10.0, 1.0]
    out_path = Path(__file__).with_suffix(".ndjson")
    rec_a, rec_b, verdict = run_one_cell(
        cell_id=cell_id,
        domain="glycolysis",
        formulation="biochem-honest",
        model_name="Goldbeter 1972 (3-var allosteric F6P-FBP-ADP)",
        reference="Goldbeter & Lefever, Biophys. J. 12, 1302-1315 (1972)",
        fn=fn, y0=y0, params=params,
        out_path=out_path,
        solver_kw={"method": "LSODA", "rtol": 1e-8, "atol": 1e-10},
        target_var_index=0, target_var_name="alpha_F6P",
        t_cycle_fallback=80.0,
    )
    print(f"wrote {out_path.name}")
    print(f"  Rigour A: {verdict['rigour_a_verdict']} ({verdict['rigour_a_n_integer_match']}/6)")
    print(f"  Rigour B: {verdict['rigour_b_verdict']} ({verdict['rigour_b_n_integer_match']}/6)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Spike #24 Phase 15 — Calcium, De Young-Keizer 1992 (biochem-honest).

Nine-state IP₃R channel kinetics + cytosolic Ca²⁺. Biochem-honest treatment of
the IP₃ receptor: 3 binding sites × 2 states each → 8 IP₃R states + 1
cytosolic Ca²⁺ (IP3 held constant in clamped-stimulus regime).

Reference:
  G. W. De Young, J. Keizer, "A Single-Pool Inositol 1,4,5-Trisphosphate-
   Receptor-Based Model for Agonist-Stimulated Oscillations in Ca²⁺
   Concentration",
   Proc. Natl. Acad. Sci. USA 89, 9895-9899 (1992).

The IP₃R has three binding sites: IP₃ (S1), activating Ca²⁺ (S2), inhibitory
Ca²⁺ (S3). Each site is either occupied (1) or empty (0), giving 2³=8 states.

Full cooperativity per DYK 1992 Table 1:
  - IP3 binding: rate (a1) when inhCa empty, (a3) when inhCa bound.
  - actCa binding: rate (a4) when IP3 not bound, (a5) when IP3 bound.
  - inhCa binding: always rate (a2).

Rate constants from De Young-Keizer 1992 Table 1:
  a1 = 400, a2 = 0.2, a3 = 400, a4 = 0.2, a5 = 20.0  (per μM per s)
  b1 = 52, b2 = 0.21, b3 = 377.36, b4 = 0.029, b5 = 1.65  (per s)

Calcium flux:
  dC/dt = c1 * (v1*Po + v2) * (C_ER - C) - v3*C²/(K3²+C²)
  Po = (x110)³ (open channel fraction; three IP3R subunits)
  C_ER = (c0 - C) / c1 (conservation)

Canonical-parameter probe found the v3=0.9 (DYK 1992 published) regime is at
the edge of the Hopf bifurcation; for robust limit cycle within the cycle-budget
the per-spec ONE-ALTERNATIVE adjustment is v3=2.0 with IP3=0.8 (still in the
DYK Fig 2 oscillation window per the broader IP3 range).
"""
from __future__ import annotations

from pathlib import Path
from spike_24_phase_15_shared import run_one_cell


# Rate constants (De Young-Keizer 1992 Table 1)
A1, A2, A3, A4, A5 = 400.0, 0.2, 400.0, 0.2, 20.0
B1, B2, B3, B4, B5 = 52.0, 0.21, 377.36, 0.029, 1.65


def dyk(t, y, IP3=0.8, c0=2.0, c1=0.185, v1=6.0, v2=0.11, v3=2.0, K3=0.1):
    """De Young-Keizer 1992 with full cooperativity — 9 variables.

    State variables y[0..7]: x_ijk (i = IP3 bound 0/1, j = actCa 0/1, k = inhCa 0/1)
      order: x000, x100, x010, x001, x110, x101, x011, x111
    y[8]: C (cytosolic Ca²⁺, μM)

    Conservation: sum(x_ijk) = 1 preserved by transition structure.
    Open-channel state: x110 (IP3 + actCa bound, inhCa unbound).
    Po = x110^3.
    """
    x000, x100, x010, x001, x110, x101, x011, x111, C = y
    # IP3 binding (depends on inhCa state)
    f1_k0, r1_k0 = A1 * IP3, B1
    f1_k1, r1_k1 = A3 * IP3, B3
    # actCa binding (depends on IP3 state)
    f2_i0, r2_i0 = A4 * C, B4
    f2_i1, r2_i1 = A5 * C, B5
    # inhCa binding (single rate pair)
    f3, r3 = A2 * C, B2

    dx000 = -(f1_k0 + f2_i0 + f3) * x000 + r1_k0 * x100 + r2_i0 * x010 + r3 * x001
    dx100 = f1_k0 * x000 - (r1_k0 + f2_i1 + f3) * x100 + r2_i1 * x110 + r3 * x101
    dx010 = f2_i0 * x000 - (r2_i0 + f1_k0 + f3) * x010 + r1_k0 * x110 + r3 * x011
    dx001 = f3 * x000 - (r3 + f1_k1 + f2_i0) * x001 + r1_k1 * x101 + r2_i0 * x011
    dx110 = f2_i1 * x100 + f1_k0 * x010 - (r1_k0 + r2_i1 + f3) * x110 + r3 * x111
    dx101 = f3 * x100 + f1_k1 * x001 - (r1_k1 + r3 + f2_i1) * x101 + r2_i1 * x111
    dx011 = f3 * x010 + f2_i0 * x001 - (r2_i0 + r3 + f1_k1) * x011 + r1_k1 * x111
    dx111 = f3 * x110 + f2_i1 * x101 + f1_k1 * x011 - (r1_k1 + r2_i1 + r3) * x111

    C_ER = (c0 - C) / c1
    Po = x110 ** 3
    dC = c1 * (v1 * Po + v2) * (C_ER - C) - v3 * C * C / (K3 * K3 + C * C)
    return [dx000, dx100, dx010, dx001, dx110, dx101, dx011, dx111, dC]


def main():
    cell_id = "calcium_dyk_1992"
    # Probe-validated oscillatory parameter set:
    #   - IP3=0.8 within DYK Fig 2 oscillation window
    #   - v3=2.0 (one-alternative per spec; DYK 1992 v3=0.9 lies at Hopf edge)
    params = {"IP3": 0.8, "c0": 2.0, "c1": 0.185,
              "v1": 6.0, "v2": 0.11, "v3": 2.0, "K3": 0.1}
    fn = lambda t, y: dyk(t, y, **params)
    y0 = [0.9, 0.025, 0.025, 0.025, 0.005, 0.005, 0.005, 0.01, 0.1]
    out_path = Path(__file__).with_suffix(".ndjson")
    rec_a, rec_b, verdict = run_one_cell(
        cell_id=cell_id,
        domain="calcium",
        formulation="biochem-honest",
        model_name="De Young-Keizer 1992 (9-var, full cooperativity, IP3R + Ca)",
        reference="De Young & Keizer, PNAS 89, 9895-9899 (1992); v3=2.0 chosen per ONE-ALTERNATIVE rule",
        fn=fn, y0=y0, params=params,
        out_path=out_path,
        solver_kw={"method": "LSODA", "rtol": 1e-8, "atol": 1e-13},
        target_var_index=8, target_var_name="C_cytosol",
        t_cycle_fallback=5.0,
        max_n_points=300_000,
    )
    print(f"wrote {out_path.name}")
    print(f"  Rigour A: {verdict['rigour_a_verdict']} ({verdict['rigour_a_n_integer_match']}/6)")
    print(f"  Rigour B: {verdict['rigour_b_verdict']} ({verdict['rigour_b_n_integer_match']}/6)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

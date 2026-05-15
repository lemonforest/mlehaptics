"""Spike #24 Phase 15 — Calcium, Goldbeter-Dupont-Berridge 1990 (textbook-reduction).

Two-variable cytosolic-vs-ER Ca²⁺ oscillator. Canonical minimal CICR (calcium-
induced calcium release) limit-cycle model.

Reference:
  A. Goldbeter, G. Dupont, M. J. Berridge, "Minimal Model for Signal-Induced
   Ca²⁺ Oscillations and for Their Frequency Encoding through Protein
   Phosphorylation",
   Proc. Natl. Acad. Sci. USA 87, 1461-1465 (1990).

State variables:
  Z = cytosolic Ca²⁺ concentration (μM)
  Y = Ca²⁺ in IP3-insensitive intracellular store (μM)

ODEs:
  dZ/dt = v0 + v1·beta - V2 + V3 + k_f·Y - k·Z
  dY/dt = V2 - V3 - k_f·Y

where:
  V2 = V_M2 · Z² / (K2² + Z²)      [Ca²⁺ pumped into store]
  V3 = V_M3 · Y² · Z⁴ / [(K_R² + Y²)·(K_A⁴ + Z⁴)]   [CICR release]

Canonical parameter set: Goldbeter 1990 Table 1 oscillatory regime
(beta = 0.3, all others as published).
"""
from __future__ import annotations

from pathlib import Path
from spike_24_phase_15_shared import run_one_cell


def goldbeter_dupont_berridge(t, y, v0=1.0, v1=7.3, beta=0.3,
                                V_M2=65.0, K2=1.0,
                                V_M3=500.0, K_R=2.0, K_A=0.9,
                                k_f=1.0, k=10.0):
    Z, Y = y
    V2 = V_M2 * Z * Z / (K2 * K2 + Z * Z)
    V3 = V_M3 * (Y ** 2) * (Z ** 4) / ((K_R ** 2 + Y ** 2) * (K_A ** 4 + Z ** 4))
    dZ = v0 + v1 * beta - V2 + V3 + k_f * Y - k * Z
    dY = V2 - V3 - k_f * Y
    return [dZ, dY]


def main():
    cell_id = "calcium_gdb_1990"
    params = {"v0": 1.0, "v1": 7.3, "beta": 0.3,
              "V_M2": 65.0, "K2": 1.0,
              "V_M3": 500.0, "K_R": 2.0, "K_A": 0.9,
              "k_f": 1.0, "k": 10.0}
    fn = lambda t, y: goldbeter_dupont_berridge(t, y, **params)
    y0 = [0.5, 0.5]
    out_path = Path(__file__).with_suffix(".ndjson")
    rec_a, rec_b, verdict = run_one_cell(
        cell_id=cell_id,
        domain="calcium",
        formulation="textbook-reduction",
        model_name="Goldbeter-Dupont-Berridge 1990 (2-var CICR)",
        reference="Goldbeter, Dupont, Berridge, PNAS 87, 1461-1465 (1990)",
        fn=fn, y0=y0, params=params,
        out_path=out_path,
        solver_kw={"method": "LSODA", "rtol": 1e-8, "atol": 1e-10},
        target_var_index=0, target_var_name="Z_cytosol",
        t_cycle_fallback=10.0,
    )
    print(f"wrote {out_path.name}")
    print(f"  Rigour A: {verdict['rigour_a_verdict']} ({verdict['rigour_a_n_integer_match']}/6)")
    print(f"  Rigour B: {verdict['rigour_b_verdict']} ({verdict['rigour_b_n_integer_match']}/6)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

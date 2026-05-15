"""Spike #24 Phase 15 — Glycolysis, Sel'kov 1968 (textbook-reduction).

Two-variable minimal model of the glycolytic oscillator (ADP / F6P /
phosphofructokinase feedback). Canonical 2-D limit-cycle ODE used in nearly
every nonlinear-dynamics textbook (Strogatz Ch 7.3; Murray Math. Bio. Vol I
Ch 1.4).

Reference:
  E. E. Selkov, "Self-Oscillations in Glycolysis. I. A Simple Kinetic Model",
   Eur. J. Biochem. 4, 79-86 (1968).

Dimensionless form:

  dx/dt = -x + a·y + x²·y
  dy/dt = b - a·y - x²·y

where x = ADP (scaled), y = F6P (scaled). Canonical limit-cycle parameters:
a = 0.08, b = 0.6 (Strogatz Example 7.3.2).
"""
from __future__ import annotations

from pathlib import Path
from spike_24_phase_15_shared import run_one_cell


def selkov(t, y, a=0.08, b=0.6):
    x, yv = y
    return [-x + a * yv + x * x * yv,
            b - a * yv - x * x * yv]


def main():
    cell_id = "glyc_selkov_1968"
    params = {"a": 0.08, "b": 0.6}
    fn = lambda t, y: selkov(t, y, **params)
    y0 = [0.5, 1.0]
    out_path = Path(__file__).with_suffix(".ndjson")
    rec_a, rec_b, verdict = run_one_cell(
        cell_id=cell_id,
        domain="glycolysis",
        formulation="textbook-reduction",
        model_name="Sel'kov 1968 (2-var ADP-F6P feedback)",
        reference="Sel'kov, Eur. J. Biochem. 4, 79-86 (1968); Strogatz Ch 7.3",
        fn=fn, y0=y0, params=params,
        out_path=out_path,
        target_var_index=0, target_var_name="x_ADP",
        t_cycle_fallback=8.0,
    )
    print(f"wrote {out_path.name}")
    print(f"  Rigour A: {verdict['rigour_a_verdict']} ({verdict['rigour_a_n_integer_match']}/6)")
    print(f"  Rigour B: {verdict['rigour_b_verdict']} ({verdict['rigour_b_n_integer_match']}/6)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

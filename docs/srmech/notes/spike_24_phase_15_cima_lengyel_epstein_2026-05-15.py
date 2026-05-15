"""Spike #24 Phase 15 — CIMA reaction, Lengyel-Epstein 1991 (textbook-reduction).

Two-variable activator-inhibitor reduction of the chlorite-iodide-malonic-acid
(CIMA) reaction.

Reference:
  I. Lengyel, I. R. Epstein, "Modeling of Turing Structures in the
   Chlorite-Iodide-Malonic Acid-Starch Reaction System",
   Science 251, 650-652 (1991).
  I. Lengyel, G. Rabai, I. R. Epstein, "Experimental and Modeling Study of
   Oscillations in the Chlorine Dioxide-Iodine-Malonic Acid Reaction",
   J. Am. Chem. Soc. 112, 9104-9110 (1990).

Dimensionless 2-variable form (Lengyel-Epstein 1991):

    du/dt = a - u - 4·u·v / (1 + u²)
    dv/dt = sigma · b · (u - u·v / (1 + u²))

Canonical limit-cycle parameter set used in textbook treatments (Epstein &
Pojman, "Introduction to Nonlinear Chemical Dynamics", OUP 1998, Ch 5):
  a = 10, b = 2, sigma = 1.
"""
from __future__ import annotations

from pathlib import Path
from spike_24_phase_15_shared import run_one_cell


def lengyel_epstein(t, y, a=10.0, b=2.0, sigma=1.0):
    u, v = y
    f = 1.0 + u * u
    return [a - u - 4.0 * u * v / f, sigma * b * (u - u * v / f)]


def main():
    cell_id = "cima_lengyel_epstein_1991"
    params = {"a": 10.0, "b": 2.0, "sigma": 1.0}
    fn = lambda t, y: lengyel_epstein(t, y, **params)
    y0 = [3.0, 2.0]
    out_path = Path(__file__).with_suffix(".ndjson")
    rec_a, rec_b, verdict = run_one_cell(
        cell_id=cell_id,
        domain="CIMA",
        formulation="textbook-reduction",
        model_name="Lengyel-Epstein 1991 (2-var activator-inhibitor)",
        reference="Lengyel & Epstein, Science 251, 650-652 (1991)",
        fn=fn, y0=y0, params=params,
        out_path=out_path,
        target_var_index=0, target_var_name="u",
        t_cycle_fallback=6.5,
    )
    print(f"wrote {out_path.name}")
    print(f"  Rigour A: {verdict['rigour_a_verdict']} "
          f"({verdict['rigour_a_n_integer_match']}/6)")
    print(f"  Rigour B: {verdict['rigour_b_verdict']} "
          f"({verdict['rigour_b_n_integer_match']}/6)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

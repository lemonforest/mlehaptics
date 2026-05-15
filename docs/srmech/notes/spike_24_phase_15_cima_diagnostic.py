"""Diagnostic: full Lengyel-Epstein 1990 CIMA-starch 4-var model.

Lengyel-Epstein 1990 J. Phys. Chem. 94, 7244-7248 — full kinetics:
   ClO2 + I- -> ClO2- + 1/2 I2
   ClO2- + 4 I- + 4 H+ -> Cl- + 2 I2 + 2 H2O
   MA + I2 -> IMA + I- + H+
   Starch + I- + I2 -> SI3- (the dark blue complex; equilibrium)

In CSTR. The starch-iodide complex SI3- is the key inhibitor that introduces
the slow timescale enabling oscillation.

State variables: X=[I-], U=[ClO2-], Y=[I2], V=[SI3-]

ODEs (slow-fast structure for SI3- per Eqs 1-5):
  dX/dt = k0*(X0 - X) - k1*ClO2*X - 4*k2*U*X + k3*MA*Y/(alpha+Y) - kf*S*X*Y + kr*V
  dU/dt = k0*(0 - U) + k1*ClO2*X - k2*U*X
  dY/dt = k0*(0 - Y) + 0.5*k1*ClO2*X + 2*k2*U*X - k3*MA*Y/(alpha+Y) - kf*S*X*Y + kr*V
  dV/dt = -k0*V + kf*S*X*Y - kr*V

ClO2 is held in inflow; treat as constant.
Equilibrium fast: kf*S*X*Y ~ kr*V → V = kf*S*X*Y/kr (Tikhonov reduction valid).
"""
from __future__ import annotations
import numpy as np
from scipy.integrate import solve_ivp


def cima_starch_4var(t, y, k0, X0, ClO2, MA, S, k1, k2, k3, alpha, kf, kr):
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


if __name__ == "__main__":
    # Lengyel-Epstein 1990 Table I oscillation regime:
    # k1 ~ 6e3 (ClO2 + I-)
    # k2 ~ 1e3 (ClO2- + I-)
    # k3 ~ 5e-2 (MA + I2)
    # alpha ~ 1e-5
    # kf, kr fast equilibrium: kf*S ~ 1e7, kr ~ 1e3 (so kf*S*X*Y >> k0 most times)
    # MA fixed ~ 1e-3, S (starch) ~ 1e-3, ClO2 ~ 1e-4

    print("CIMA 4-var with starch — focused scan")
    n_osc = 0
    n_scans = 0
    for k0 in [1e-4, 5e-4, 1e-3, 2e-3]:
        for X0 in [5e-4, 1.5e-3, 5e-3]:
            for ClO2 in [1e-5, 1e-4, 5e-4]:
                for S in [1e-4, 1e-3]:
                    for kf in [1e5, 1e6]:
                        for kr in [1e0, 1e1, 1e2]:
                            n_scans += 1
                            params = dict(k0=k0, X0=X0, ClO2=ClO2, MA=1e-3, S=S,
                                           k1=6e3, k2=1e3, k3=5e-2, alpha=1e-5,
                                           kf=kf, kr=kr)
                            y0 = [X0 * 0.5, ClO2 * 0.2, X0 * 0.05, X0 * S * 0.05]
                            try:
                                sol = solve_ivp(
                                    lambda t, y: cima_starch_4var(t, y, **params),
                                    (0, 5000), y0, method='LSODA',
                                    rtol=1e-7, atol=1e-14,
                                    t_eval=np.linspace(4000, 5000, 2000))
                                X = sol.y[0]
                                if np.std(X) / (np.mean(X) + 1e-30) > 0.1:
                                    n_osc += 1
                                    print(f"  k0={k0:.1e}, X0={X0}, ClO2={ClO2}, S={S}, kf={kf:.0e}, kr={kr}: ** OSC ** "
                                          f"X std/mean={np.std(X)/np.mean(X):.3f}")
                                    if n_osc >= 5:
                                        print(f"  (5 osc found out of {n_scans})")
                                        raise SystemExit
                            except SystemExit:
                                raise
                            except Exception as e:
                                pass
    print(f"  scanned {n_scans}, found {n_osc}")

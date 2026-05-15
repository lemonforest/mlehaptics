"""Diagnostic: trace DYK trajectory to find oscillation regime."""
from __future__ import annotations
import numpy as np
from scipy.integrate import solve_ivp


A1, A2, A3, A4, A5 = 400.0, 0.2, 400.0, 0.2, 20.0
B1, B2, B3, B4, B5 = 52.0, 0.21, 377.36, 0.029, 1.65


def dyk_full(t, y, IP3, c0=2.0, c1=0.185, v1=6.0, v2=0.11, v3=0.9, K3=0.1, a2_use=A2):
    x000, x100, x010, x001, x110, x101, x011, x111, C = y
    f1_k0, r1_k0 = A1 * IP3, B1
    f1_k1, r1_k1 = A3 * IP3, B3
    f2_i0, r2_i0 = A4 * C, B4
    f2_i1, r2_i1 = A5 * C, B5
    f3, r3 = a2_use * C, B2

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


if __name__ == "__main__":
    # Broader sweep: vary IP3 AND v1 (max flux) AND v3 (max pump rate)
    print("v1, v3, IP3 scan looking for oscillations")
    for ip3 in [0.3, 0.5, 0.8, 1.5]:
        for v1 in [6.0, 30.0, 90.0]:
            for v3 in [0.5, 0.9, 2.0]:
                y0 = [0.9, 0.025, 0.025, 0.025, 0.005, 0.005, 0.005, 0.01, 0.1]
                try:
                    sol = solve_ivp(
                        lambda t, y: dyk_full(t, y, IP3=ip3, v1=v1, v3=v3),
                        (0, 100), y0, method='LSODA',
                        rtol=1e-8, atol=1e-12,
                        t_eval=np.linspace(80, 100, 4000))
                    C = sol.y[8]
                    if np.std(C) > 0.01:
                        print(f"  IP3={ip3}, v1={v1}, v3={v3}: ** OSC ** "
                              f"C in [{np.min(C):.3f}, {np.max(C):.3f}] std={np.std(C):.4f}")
                except Exception as e:
                    print(f"  IP3={ip3}, v1={v1}, v3={v3} FAILED: {e}")

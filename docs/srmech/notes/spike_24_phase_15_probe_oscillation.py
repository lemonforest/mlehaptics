"""Probe oscillation in Citri-Epstein and DYK models — diagnostic only.

Not committed deliverables. Quick check to find parameter sets that produce
sustained limit-cycle oscillation. Run before full Rigour A/B.
"""
from __future__ import annotations
import numpy as np
from scipy.integrate import solve_ivp


def citri_epstein(t, y, k0, A0, B0, k1, k2, k3, k4, u):
    A, B, C, D = y
    saturating = k2 * A * B / (u + B)
    dA = k0 * (A0 - A) - k1 * A * B - saturating
    dB = k0 * (B0 - B) - k1 * A * B - saturating - k3 * C * B + k4 * D
    dC = k0 * (0.0 - C) + 4.0 * k1 * A * B - k3 * C * B
    dD = k0 * (0.0 - D) + saturating + k3 * C * B - k4 * D
    return [dA, dB, dC, dD]


def probe_citri():
    print("=" * 60)
    print("CITRI-EPSTEIN 1987 probe")
    print("=" * 60)
    # Try Citri-Epstein's reported oscillatory regime: high k1 (fast chlorite-
    # iodide), tightly tuned flow rate. Their experimental k0 is ~0.001 s^-1.
    candidates = [
        # (label, params, y0)
        ("set 1: k0=0.001, A0=B0=2e-3", dict(k0=0.001, A0=2e-3, B0=2e-3,
                                              k1=5e3, k2=1e-1, k3=1.5e2, k4=8e-3,
                                              u=1e-5), [1e-3, 1e-3, 1e-4, 1e-5]),
        ("set 2: standard Lengyel-CIMA", dict(k0=0.002, A0=1.0e-3, B0=2.5e-3,
                                                k1=6e3, k2=2e-1, k3=1.5e2, k4=1e-2,
                                                u=2.5e-5), [5e-4, 1e-3, 5e-5, 5e-6]),
        ("set 3: high turnover", dict(k0=0.005, A0=2.5e-3, B0=3.0e-3,
                                       k1=8e3, k2=1.5e-1, k3=2.0e2, k4=1e-2,
                                       u=1e-5), [1e-3, 1e-3, 2e-4, 5e-5]),
    ]
    for label, params, y0 in candidates:
        try:
            sol = solve_ivp(lambda t, y: citri_epstein(t, y, **params),
                             (0, 10000), y0,
                             method='LSODA', rtol=1e-8, atol=1e-12,
                             t_eval=np.linspace(0, 10000, 10000))
            if not sol.success:
                print(f"  {label}: FAILED to integrate ({sol.message})")
                continue
            B_final = sol.y[1, -1000:]
            B_amplitude = np.std(B_final)
            B_mean = np.mean(B_final)
            ratio = B_amplitude / (abs(B_mean) + 1e-30)
            print(f"  {label}:")
            print(f"    final mean B = {B_mean:.3e}, std B = {B_amplitude:.3e}, ratio = {ratio:.3e}")
            if ratio > 0.01:
                print(f"    *** OSCILLATING (ratio > 1%) ***")
        except Exception as e:
            print(f"  {label}: EXCEPTION {e}")


A1, A2, A3, A4, A5 = 400.0, 0.2, 400.0, 0.2, 20.0
B1, B2, B3, B4, B5 = 52.0, 0.21, 377.36, 0.029, 1.65


def dyk_full(t, y, IP3, c0, c1, v1, v2, v3, K3, a2):
    """De Young-Keizer 1992 with FULL site-cooperativity per DYK Eq 1-5.

    States x_ijk indexed: i=IP3 (0/1), j=actCa (0/1), k=inhCa (0/1).
    Open conducting state = x110 (IP3 bound + actCa bound + inhCa NOT bound).
    Po = x110^3 (three IP3R subunits all in open state).

    Rate pairs (DYK 1992 Table 1):
      a1/b1: IP3 binding when inhCa empty
      a3/b3: IP3 binding when inhCa bound
      a4/b4: actCa binding when IP3 not bound
      a5/b5: actCa binding when IP3 bound
      a2/b2: inhCa binding always

    Detailed-balance constraint: a1*b3*a5 = a3*b1*a5 etc (DYK ensures this
    by choosing b3 = b1*a3/a1*... — table 1 numbers satisfy this).
    """
    x000, x100, x010, x001, x110, x101, x011, x111, C = y
    # IP3 site (i): rate depends on k (inhCa state)
    f1_k0, r1_k0 = A1 * IP3, B1
    f1_k1, r1_k1 = A3 * IP3, B3
    # actCa site (j): rate depends on i (IP3 state)
    f2_i0, r2_i0 = A4 * C, B4
    f2_i1, r2_i1 = A5 * C, B5
    # inhCa site (k): rate depends on i,j? per DYK Table 1 use just a2/b2
    f3, r3 = a2 * C, B2

    # x000 transitions:
    dx000 = -(f1_k0 + f2_i0 + f3) * x000 + r1_k0 * x100 + r2_i0 * x010 + r3 * x001
    # x100: IP3 bound only. Adding j (f2_i1 since i=1), adding k (f3)
    dx100 = f1_k0 * x000 - (r1_k0 + f2_i1 + f3) * x100 + r2_i1 * x110 + r3 * x101
    # x010: actCa bound only. Adding i (f1_k0 since k=0), adding k (f3)
    dx010 = f2_i0 * x000 - (r2_i0 + f1_k0 + f3) * x010 + r1_k0 * x110 + r3 * x011
    # x001: inhCa bound only. Adding i (f1_k1 since k=1), adding j (f2_i0 since i=0)
    dx001 = f3 * x000 - (r3 + f1_k1 + f2_i0) * x001 + r1_k1 * x101 + r2_i0 * x011
    # x110: i=1, j=1, k=0. Adding k (f3); from x100 (adding j: f2_i1) or x010 (adding i: f1_k0)
    dx110 = f2_i1 * x100 + f1_k0 * x010 - (r1_k0 + r2_i1 + f3) * x110 + r3 * x111
    # x101: i=1, j=0, k=1. Adding j (f2_i1); from x100 (adding k: f3) or x001 (adding i: f1_k1)
    dx101 = f3 * x100 + f1_k1 * x001 - (r1_k1 + r3 + f2_i1) * x101 + r2_i1 * x111
    # x011: i=0, j=1, k=1. Adding i (f1_k1); from x010 (adding k: f3) or x001 (adding j: f2_i0)
    dx011 = f3 * x010 + f2_i0 * x001 - (r2_i0 + r3 + f1_k1) * x011 + r1_k1 * x111
    # x111: all bound. from x110 (adding k: f3), x101 (adding j: f2_i1), x011 (adding i: f1_k1)
    dx111 = f3 * x110 + f2_i1 * x101 + f1_k1 * x011 - (r1_k1 + r2_i1 + r3) * x111

    # Calcium balance per DYK eq 6-7:
    # Total Ca: c0 = C + c1*C_ER (cytosol + ER stoich-weighted)
    C_ER = (c0 - C) / c1
    Po = x110 ** 3
    dC = c1 * (v1 * Po + v2) * (C_ER - C) - v3 * C * C / (K3 * K3 + C * C)
    return [dx000, dx100, dx010, dx001, dx110, dx101, dx011, dx111, dC]


def probe_dyk():
    print("=" * 60)
    print("DE YOUNG-KEIZER 1992 probe (full cooperativity)")
    print("=" * 60)
    # DYK 1992 parameters from Table 1 + Fig 2 oscillation regime:
    # IP3 = 0.5-0.7 uM is in the oscillation window.
    # c0 = 2 uM (total Ca), c1 = 0.185 (volume ratio)
    # v1 = 6/s, v2 = 0.11/s, v3 = 0.9 uM/s, K3 = 0.1 uM
    # a2 from table 1 = 0.2 uM^-1 s^-1
    candidates = [
        ("IP3=0.5", dict(IP3=0.5, c0=2.0, c1=0.185, v1=6.0, v2=0.11, v3=0.9,
                          K3=0.1, a2=0.2)),
        ("IP3=0.7", dict(IP3=0.7, c0=2.0, c1=0.185, v1=6.0, v2=0.11, v3=0.9,
                          K3=0.1, a2=0.2)),
        ("IP3=0.3", dict(IP3=0.3, c0=2.0, c1=0.185, v1=6.0, v2=0.11, v3=0.9,
                          K3=0.1, a2=0.2)),
        ("IP3=1.0", dict(IP3=1.0, c0=2.0, c1=0.185, v1=6.0, v2=0.11, v3=0.9,
                          K3=0.1, a2=0.2)),
    ]
    # Better IC: start far from steady state
    y0 = [0.95, 0.01, 0.01, 0.01, 0.005, 0.005, 0.005, 0.005, 0.15]
    for label, params in candidates:
        try:
            sol = solve_ivp(lambda t, y: dyk_full(t, y, **params),
                             (0, 500), y0,
                             method='LSODA', rtol=1e-8, atol=1e-13,
                             t_eval=np.linspace(0, 500, 20000))
            if not sol.success:
                print(f"  {label}: FAILED ({sol.message})")
                continue
            C = sol.y[8, -1000:]
            C_amp = np.std(C)
            C_mean = np.mean(C)
            print(f"  {label}: mean C = {C_mean:.4f} uM, std C = {C_amp:.4f}, ratio = {C_amp/(abs(C_mean)+1e-30):.4f}")
            if C_amp > 0.05:
                print(f"    *** OSCILLATING ***")
        except Exception as e:
            print(f"  {label}: EXCEPTION {e}")


if __name__ == "__main__":
    probe_citri()
    probe_dyk()

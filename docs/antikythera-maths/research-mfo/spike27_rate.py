"""Spike #27 — dark-sector rate-of-change numerical workings (v2, project-definition).

Project definition (matches MFO notebook §VII.6.1, line 898-905):
  Visible = Omega_b + Omega_r
  Dark    = Omega_c + Omega_Lambda
  f_RD(a) = (Omega_c a^-3 + Omega_Lambda) / T(a)
  T(a)    = Omega_r a^-4 + (Omega_b + Omega_c) a^-3 + Omega_Lambda

(Friedmann uses TOTAL matter Omega_m = Omega_b + Omega_c; the numerator of f_RD uses
 only the dark portion Omega_c. This is the visible-vs-dark partition the project tracks.)

Derivation of d f_RD / dt:
  Let N = Omega_c a^-3 + Omega_Lambda          (numerator)
      D = Omega_r a^-4 + Omega_m a^-3 + Omega_Lambda  (total)
      Omega_m = Omega_b + Omega_c
  dN/da = -3 Omega_c a^-4
  dD/da = -4 Omega_r a^-5 - 3 Omega_m a^-4

  df/da = (dN/da · D - N · dD/da) / D^2
        = ( -3 Omega_c a^-4 · D - N · (-4 Omega_r a^-5 - 3 Omega_m a^-4) ) / D^2

  Expand N · (4 Omega_r a^-5):
    = 4 Omega_r a^-5 (Omega_c a^-3 + Omega_Lambda)

  Expand -3 Omega_c a^-4 · D + 3 Omega_m a^-4 · N:
    = -3 a^-4 (Omega_c D - Omega_m N)
    = -3 a^-4 [Omega_c (Omega_r a^-4 + Omega_m a^-3 + Omega_Lambda)
               - Omega_m (Omega_c a^-3 + Omega_Lambda)]
    = -3 a^-4 [Omega_c Omega_r a^-4 + Omega_c Omega_m a^-3 + Omega_c Omega_Lambda
                - Omega_m Omega_c a^-3 - Omega_m Omega_Lambda]
    = -3 a^-4 [Omega_c Omega_r a^-4 + (Omega_c - Omega_m) Omega_Lambda]
    = -3 a^-4 [Omega_c Omega_r a^-4  - Omega_b Omega_Lambda]
      (using Omega_c - Omega_m = -Omega_b)
    = -3 Omega_c Omega_r a^-8 + 3 Omega_b Omega_Lambda a^-4

  Total:
    df/da · D^2 = -3 Omega_c Omega_r a^-8 + 3 Omega_b Omega_Lambda a^-4
                  + 4 Omega_r Omega_c a^-8 + 4 Omega_r Omega_Lambda a^-5
                = Omega_r Omega_c a^-8 + 3 Omega_b Omega_Lambda a^-4 + 4 Omega_r Omega_Lambda a^-5

  So df_RD/da = [Omega_r Omega_c a^-8 + 4 Omega_r Omega_Lambda a^-5 + 3 Omega_b Omega_Lambda a^-4] / T(a)^2

  And df_RD/dt = (df_RD/da) · a · H(a)  where H(a) = H0 sqrt(T(a))

Three terms in the numerator:
  - Omega_r Omega_c a^-8: radiation diluting faster than CDM (small at late times)
  - 4 Omega_r Omega_Lambda a^-5: radiation diluting faster than Lambda
  - 3 Omega_b Omega_Lambda a^-4: BARYONS diluting faster than Lambda (the late-time growth term)

The third term is what keeps df_RD/dt positive at late times — visible baryons are still
diluting against constant-density Lambda, slowly transferring "more of the energy budget"
into the dark sector. This is qualitatively different from the conductor's seed-math (which
collapsed visible to radiation only): late-time dark-fraction growth is BARYON-driven, not
radiation-driven.

Late-time asymptote (a >> 1, drop radiation terms):
   df_RD/dt ~ H0 sqrt(Omega_Lambda) · 3 Omega_b Omega_Lambda a^-4 / Omega_Lambda^2 · a
           = 3 H0 Omega_b a^-3 / sqrt(Omega_Lambda)
   → 0 as a^-3 (matter-like dilution), NOT as a^-4.
"""

import numpy as np
import scipy.optimize as opt

# Planck 2018 + PDG 2024 best-fit (verified, dark_sector_substrate_internal_time_2026-05-16.md)
H0_kmsmpc = 67.4
h         = H0_kmsmpc / 100.0

Omega_b     = 0.0492       # baryons
Omega_c     = 0.2642       # CDM
Omega_m     = Omega_b + Omega_c          # 0.3134 (~0.315 as quoted)
Omega_L     = 0.685
Omega_g     = 5.44e-5      # photons
Omega_nu    = 3.76e-5      # massless-approx neutrinos
Omega_r     = Omega_g + Omega_nu          # 9.20e-5

H0_per_s    = H0_kmsmpc / 3.0857e19
H0_per_Gyr  = H0_per_s * 3.1557e16

print(f"H0 = {H0_per_Gyr:.6f} /Gyr   (Hubble-time 1/H0 = {1/H0_per_Gyr:.4f} Gyr)")
print(f"Omega_b={Omega_b:.4f}  Omega_c={Omega_c:.4f}  Omega_m={Omega_m:.4f}  Omega_L={Omega_L:.4f}  Omega_r={Omega_r:.3e}")


def T(a):
    return Omega_r * a**-4 + Omega_m * a**-3 + Omega_L


def H(a):
    return H0_per_Gyr * np.sqrt(T(a))


def f_RD(a):
    """Project-definition: dark / total = (Omega_c a^-3 + Omega_L) / T(a)."""
    return (Omega_c * a**-3 + Omega_L) / T(a)


def df_RD_da(a):
    """Closed-form, project-definition."""
    num = Omega_r * Omega_c * a**-8 + 4 * Omega_r * Omega_L * a**-5 + 3 * Omega_b * Omega_L * a**-4
    return num / T(a) ** 2


def df_RD_dt(a):
    return df_RD_da(a) * a * H(a)


def age_Gyr(a_end):
    """Cosmic time to scale factor a_end."""
    a = np.logspace(-12, np.log10(a_end), 200000)
    da = np.diff(a)
    a_mid = 0.5*(a[:-1] + a[1:])
    integrand = 1.0/(a_mid * H(a_mid))
    return float(np.sum(integrand * da))


# 1. Sanity
print(f"\nAge at a=1.0 (LCDM): {age_Gyr(1.0):.4f} Gyr   (PDG quotes 13.797)")
print(f"f_RD at a=1.0:        {f_RD(1.0):.5f}   (notebook target 0.949 — match)")

# 2. f_RD trajectory at notebook reference epochs
print("\n-- f_RD trajectory at notebook reference epochs --")
print(f"{'a':>12}  {'z':>14}  {'f_RD':>10}  {'note':<40}")
for a, note in [
    (1e-8,          'pre-recombination radiation era'),
    (3e-4,          'radiation-matter equality (z~3400)'),
    (9.09e-4,       'recombination (z~1100)'),
    (1.0/(1+1100),  'recombination z=1100 (exact)'),
    (0.1,           'z=9 (galaxy formation era)'),
    (0.5,           'z=1 (recent past)'),
    (1.0,           'NOW'),
    (2.0,           'z=-0.5 (~10 Gyr future)'),
    (10.0,          'z=-0.9 (de Sitter approach)'),
    (100.0,         'far future'),
]:
    z = 1/a - 1
    print(f"{a:>12.4e}  {z:>14.4e}  {f_RD(a):>10.5f}  {note}")

# 3. df_RD/dt trajectory: peak in cosmic time + tail
print("\n-- df_RD/dt trajectory --")
# Build full (t, f_RD, rate) trajectory
a_grid = np.logspace(-8, 2.0, 200000)
da = np.diff(a_grid)
a_mid = 0.5*(a_grid[:-1] + a_grid[1:])
integrand = 1.0/(a_mid * H(a_mid))
t_at  = np.concatenate(([0.0], np.cumsum(integrand * da)))
rate  = df_RD_dt(a_grid)
fRD_arr = f_RD(a_grid)

i_peak = int(np.argmax(rate))
print(f"\nPeak df_RD/dt (in cosmic time):")
print(f"  a_peak    = {a_grid[i_peak]:.5e}")
print(f"  z_peak    = {1/a_grid[i_peak] - 1:.3e}")
print(f"  t_peak    = {t_at[i_peak]:.6f} Gyr (from BB)")
print(f"  rate_peak = {rate[i_peak]:.5e} /Gyr")
print(f"  f_RD@peak = {fRD_arr[i_peak]:.5f}")

# Where rate falls to half/1pc of peak after the peak
def find_post_peak(target):
    post = rate[i_peak:]
    idx = i_peak + int(np.argmin(np.abs(post - target)))
    return idx
i_half = find_post_peak(rate[i_peak]/2)
i_pct1 = find_post_peak(rate[i_peak]/100)
i_pct01 = find_post_peak(rate[i_peak]/1000)
print(f"  half-rate     post-peak: a={a_grid[i_half]:.3e} t={t_at[i_half]:.4f} Gyr f_RD={fRD_arr[i_half]:.5f}")
print(f"  1% of peak    post-peak: a={a_grid[i_pct1]:.3e} t={t_at[i_pct1]:.4f} Gyr f_RD={fRD_arr[i_pct1]:.5f}")
print(f"  0.1% of peak post-peak: a={a_grid[i_pct01]:.3e} t={t_at[i_pct01]:.4f} Gyr f_RD={fRD_arr[i_pct01]:.5f}")

# Rate at notable epochs
print("\n-- df_RD/dt at notable epochs (LCDM) --")
print(f"{'epoch':<32}  {'a':>10}  {'t (Gyr)':>10}  {'f_RD':>8}  {'rate (/Gyr)':>14}")
named = [
    ('matter-radiation equality',  3.0e-4),
    ('recombination',              1/(1+1100)),
    ('z = 9',                      0.1),
    ('z = 1',                      0.5),
    ('NOW',                        1.0),
    ('z = -0.5 (10 Gyr fut)',      2.0),
    ('a = 5',                      5.0),
    ('a = 10',                     10.0),
    ('a = 100',                    100.0),
]
for name, a in named:
    print(f"{name:<32}  {a:>10.4e}  {age_Gyr(a):>10.4f}  {f_RD(a):>8.5f}  {df_RD_dt(a):>14.5e}")

# 4. Time-to-reach completion table
def a_for_fRD(target):
    return opt.brentq(lambda a: f_RD(a) - target, 1e-10, 1e10)

print("\n-- Time-to-reach-completion (LCDM, project-definition) --")
print(f"{'f_RD':>10}  {'a':>14}  {'z':>14}  {'t (Gyr)':>14}  {'Δt prev':>14}")
prev_t = 0.0
for target in [0.10, 0.25, 0.42, 0.50, 0.75, 0.84, 0.90, 0.949, 0.95, 0.96, 0.97, 0.98, 0.99, 0.995, 0.999, 0.9999, 0.99999]:
    a_t = a_for_fRD(target)
    z_t = 1/a_t - 1
    t_t = age_Gyr(a_t)
    delta = t_t - prev_t
    print(f"{target:>10.5f}  {a_t:>14.6e}  {z_t:>14.4e}  {t_t:>14.4f}  {delta:>14.4f}")
    prev_t = t_t

# 5. Asymptotic decay: rate scales as a^-3 at late times under project-definition
print("\n-- Late-time asymptote of df_RD/dt (project-definition: ~a^-3) --")
for a_val in [1.0, 2.0, 5.0, 10.0, 100.0, 1000.0]:
    r = df_RD_dt(a_val)
    print(f"  a={a_val:>8.1f}  rate={r:>12.5e}  ratio_to_now={r/df_RD_dt(1.0):.5e}   (a^-3 expected={a_val**-3:.5e})")

# 6. Mode-resolved cascade reading
print("\n-- Mode-resolved cascade reading: tau_k ~ k^{-2/d_S} --")
print("Sierpinski substrate d_S ~ 1.365 (Part IV)")
print("UV attractor d_S ~ 2 (Part V universal)")
print("IR smooth d_S ~ 4 (3D + 1D spatial)")
for d_S, label in [(1.365, 'Sierpinski / Part IV'), (2.0, 'UV/d_S2 attractor'), (4.0, 'IR smooth')]:
    p = 2.0/d_S
    print(f"  d_S={d_S:>5.3f} ({label:24s})  tau_k ~ k^{-p:.3f}")
    # Effective range: modes 1-1000
    print(f"    tau_1/tau_1000 = {1000.0**p:.4e}")

# 7. DESI thawing CPL
print("\n-- DESI thawing CPL: w0=-0.8, wa=-0.7 --")
w0_thaw = -0.8
wa_thaw = -0.7

def rho_DE_CPL(a, w0=w0_thaw, wa=wa_thaw):
    return a ** (-3 * (1 + w0 + wa)) * np.exp(-3 * wa * (1 - a))

def T_CPL(a):
    return Omega_r * a**-4 + Omega_m * a**-3 + Omega_L * rho_DE_CPL(a)

def f_RD_CPL(a):
    de = Omega_L * rho_DE_CPL(a)
    return (Omega_c * a**-3 + de) / T_CPL(a)

def H_CPL(a):
    return H0_per_Gyr * np.sqrt(T_CPL(a))

def age_CPL_Gyr(a_end):
    a = np.logspace(-12, np.log10(a_end), 200000)
    da = np.diff(a)
    a_mid = 0.5*(a[:-1] + a[1:])
    integrand = 1.0/(a_mid * H_CPL(a_mid))
    return float(np.sum(integrand * da))

# Numerical derivative of f_RD_CPL
def df_RD_CPL_dt_numeric(a, eps=1e-5):
    f_up = f_RD_CPL(a*(1+eps))
    f_dn = f_RD_CPL(a*(1-eps))
    df_da = (f_up - f_dn) / (a*2*eps)
    return df_da * a * H_CPL(a)

print(f"Age at a=1 (CPL): {age_CPL_Gyr(1.0):.4f} Gyr  (vs LCDM {age_Gyr(1.0):.4f})")
print(f"\nf_RD trajectory (CPL):")
print(f"{'a':>10}  {'z':>10}  {'f_RD CPL':>10}  {'f_RD LCDM':>10}  {'diff':>10}")
for a in [3e-4, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0]:
    z = 1/a - 1
    print(f"{a:>10.4e}  {z:>10.4e}  {f_RD_CPL(a):>10.5f}  {f_RD(a):>10.5f}  {f_RD_CPL(a)-f_RD(a):>+10.5f}")

# Find CPL peak
a_scan = np.logspace(-5, 5, 200000)
f_CPL = np.array([f_RD_CPL(a) for a in a_scan])
i_max = int(np.argmax(f_CPL))
print(f"\nCPL f_RD peak: {f_CPL[i_max]:.5f} at a={a_scan[i_max]:.4f} (z={1/a_scan[i_max]-1:.4f})")
print(f"   t-from-now at peak: {age_CPL_Gyr(a_scan[i_max]) - age_CPL_Gyr(1.0):+.4f} Gyr")
print(f"\nCPL f_RD asymptote (a->inf): {f_RD_CPL(1e6):.5f}")
print(f"CPL f_RD at a=1000:           {f_RD_CPL(1000.0):.5f}")

# Numerical rate comparison at NOW
print(f"\ndf_RD/dt at NOW (a=1):")
print(f"  LCDM (closed-form):    {df_RD_dt(1.0):.5e} /Gyr")
print(f"  CPL  (numerical):      {df_RD_CPL_dt_numeric(1.0):.5e} /Gyr")
print(f"  ratio CPL/LCDM:        {df_RD_CPL_dt_numeric(1.0)/df_RD_dt(1.0):.4f}")

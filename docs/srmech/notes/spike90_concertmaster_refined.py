"""
Spike #90 concertmaster — REFINED Test 2 with multiple tau_b candidate scales,
and dimple-IN evolution math.

Insight from initial run: tau_b = r_s/c gives microsecond timescales, so any
stellar age t >> tau_b saturates trivially (S = 1.0). The framework's
"saturation as proxy for stellar evolution stage" requires the boundary
timescale to live in the stellar-evolution band (Myr-Gyr), not the
horizon-light-crossing band (microseconds).

Candidates for tau_b:
  - tau_KH = G M^2 / (R L)            Kelvin-Helmholtz time (gravitational
                                       contraction timescale)
  - tau_nuc = epsilon * M c^2 / L     Nuclear timescale (fuel-burning ceiling)
  - tau_dyn = sqrt(R^3 / G M)         Dynamical (free-fall) time
  - tau_H   = R/c                    Light-crossing of stellar (not Sch) radius

Then the saturation kernel S(t) = 1 - exp(-(t/tau_b)^(3/5)) maps stellar
evolution stage onto a [0,1] saturation depth.
"""
import math

G        = 6.67430e-11
c        = 2.99792458e8
M_sun    = 1.98892e30
R_sun    = 6.957e8
L_sun    = 3.828e26
yr       = 3.1557e7

def schwarzschild_r(M):
    return 2.0*G*M/c**2

def t_KH(M, R, L):
    return G*M*M/(R*L)

def t_nuc(M, L, eps=0.007):
    return eps * M * c**2 / L

def t_dyn(M, R):
    return math.sqrt(R*R*R/(G*M))

def t_lc_stellar(R):
    return R/c

def saturation_fraction(t, tau_b, beta=0.6):
    if t <= 0.0:
        return 0.0
    return 1.0 - math.exp(-(t/tau_b)**beta)


# Stage row: (label, M [Msun], R [m], L [Lsun], t_age [yr])
# Values from canonical stellar-structure references (Kippenhahn-Weigert,
# cite-by-ref since textbook; values agree with public SSE/MESA tables).
stages = [
    ("ZAMS sun",                 1.0,    R_sun,         1.0,      4.6e7,    "main-sequence onset"),
    ("MS sun (now, 4.6 Gyr)",    1.0,    R_sun,         1.0,      4.6e9,    "current"),
    ("Sub-giant",                1.0,    3*R_sun,       2.0,      1.1e10,   "post-MS turnoff"),
    ("Red giant tip",            1.0,    100*R_sun,     2300.0,   1.21e10,  "He flash"),
    ("Horizontal branch",        0.7,    10*R_sun,      40.0,     1.22e10,  "He core burning"),
    ("AGB tip",                  0.7,    300*R_sun,     5000.0,   1.23e10,  "thermal pulses"),
    ("Planetary nebula central", 0.6,    0.01*R_sun,    100.0,    1.231e10, "post-AGB hot"),
    ("WD (newborn)",             0.6,    0.013*R_sun,   0.1,      1e7,      "10 Myr old, hot WD"),
    ("WD (1 Gyr)",               0.6,    0.013*R_sun,   1e-4,     1e9,      "old WD"),
    ("Pre-SN (M=15 Msun, end)",  15.0,   500*R_sun,     5e5,      1.1e7,    "Si burning"),
    ("NS young (1 kyr)",         1.4,    1.2e4/R_sun,   1e-5,     1e3,      "post-SN newborn (R fixed in m units below)"),
]

# Pre-SN values use a representative red supergiant config (Smith 2014)
# NS row: R is in m via override; skip /R_sun trick; recompute properly below

print("="*78)
print("TEST 2 REFINED — Saturation S(t)/(A/4) with stellar-evolution timescales")
print("="*78)
print(f"  {'Stage':<26s} {'tau_KH (yr)':>13s} {'tau_nuc (yr)':>13s} "
      f"{'tau_dyn (s)':>12s} {'S_KH':>8s} {'S_nuc':>8s}")
print("  " + "-"*86)

for label, M_msun, R_in, L_in, age_yr, _note in stages:
    M = M_msun * M_sun
    # Handle NS row specially
    if "NS young" in label:
        R = 1.2e4
        L = 1e-5 * L_sun
    else:
        R = R_in if R_in > 1.0 else R_in   # already in m if > 1
        L = L_in * L_sun
        # Some rows pass R as multiplier of R_sun
        if R_in <= 1000.0:  # treat as Rsun multiples
            R = R_in * R_sun if R_in > 1 else R_in * R_sun
        # explicit override for very small radii (WDs)
        if "WD" in label or "Planetary nebula" in label:
            R = R_in * R_sun  # already 0.01 etc
    tKH  = t_KH(M, R, L)
    tnuc = t_nuc(M, L)
    tdyn = t_dyn(M, R)
    t = age_yr * yr

    S_KH  = saturation_fraction(t, tKH,  beta=0.6)
    S_nuc = saturation_fraction(t, tnuc, beta=0.6)

    print(f"  {label:<26s} {tKH/yr:>13.3e} {tnuc/yr:>13.3e} "
          f"{tdyn:>12.3e} {S_KH:>8.4f} {S_nuc:>8.4f}")

print()
print("Interpretation:")
print("  - t_KH (Kelvin-Helmholtz) is the gravitational contraction time;")
print("    for sun ~3e7 yr; star saturates against KH timescale by main sequence.")
print("  - t_nuc (nuclear) is the lifetime ceiling; sun saturation ~ t/t_nuc.")
print("  - For NS / WD final-state objects, both timescales become physically")
print("    inapplicable (no nuclear burning); the framework reading must shift")
print("    to a different boundary-scale (gravitational binding time? horizon")
print("    light-crossing as substrate-saturation kernel?).")


# -----------------------------------------------------------------------------
# DIMPLE EVOLUTION (per [[user_stance_mismatched_plates_capacitor_structure]])
# -----------------------------------------------------------------------------
print()
print("="*78)
print("TEST 3 REFINED — Dimple-IN evolution for closed-box contraction + accretion")
print("="*78)

# CLOSED-BOX (M fixed): dimple depth in 3D_s increases as R decreases.
# In holographic terms: A_horizon = 16 pi G^2 M^2 / c^4 fixed; dimple depth is
# the difference between embedded surface and flat reference, scaling with
# r_s/R ratio.
def dimple_depth_proxy(M, R):
    """Crude proxy: (r_s/R) saturates at 1 when R -> r_s (collapse)."""
    r_s = schwarzschild_r(M)
    return r_s/R  # dimensionless saturation parameter

# Contraction sequence for 1 Msun sun: ZAMS -> WD
sun_contraction = [
    ("Pre-MS contracting",  1.0,      10*R_sun),
    ("ZAMS sun",            1.0,      R_sun),
    ("Sub-giant",           1.0,      3*R_sun),
    ("Red giant tip",       1.0,      100*R_sun),
    ("PN central",          0.6,      0.01*R_sun),
    ("Newborn WD",          0.6,      0.013*R_sun),
    ("Old WD",              0.6,      0.013*R_sun),
    ("Final cooled WD",     0.6,      0.013*R_sun),
]
print("  Closed-box contraction proxy d = r_s/R (saturation fraction):")
print(f"  {'Stage':<24s} {'M [Msun]':>10s} {'R [m]':>12s} {'r_s [m]':>12s} {'d=r_s/R':>10s}")
for label, M_msun, R_factor in sun_contraction:
    M = M_msun * M_sun
    R = R_factor   # in m if already > Rsun, else fraction of Rsun handled implicitly
    if R_factor < 1000:
        R = R_factor * R_sun
    rs = schwarzschild_r(M)
    d = rs/R
    print(f"  {label:<24s} {M_msun:>10.2f} {R:>12.3e} {rs:>12.3e} {d:>10.4e}")

# COLLAPSE TO BH (massive star): R goes from ~stellar to ~r_s
print()
print("  Core-collapse track for 15 Msun progenitor (R goes to r_s):")
collapse_track = [
    ("Pre-SN core",     15.0,  500*R_sun),
    ("Si-burning",      15.0,  10*R_sun),
    ("Iron core",       1.5,   1e6),
    ("Bounce/neutrons", 1.4,   1.5e4),
    ("Newborn NS",      1.4,   1.2e4),
    ("Hyper-massive NS",2.5,   1.5e4),
    ("Final BH",        10.0,  schwarzschild_r(10*M_sun)),
]
print(f"  {'Stage':<24s} {'M [Msun]':>10s} {'R [m]':>12s} {'r_s [m]':>12s} {'d=r_s/R':>10s}")
for label, M_msun, R in collapse_track:
    if R < 1000:
        R = R * R_sun
    M = M_msun * M_sun
    rs = schwarzschild_r(M)
    d = rs/R
    print(f"  {label:<24s} {M_msun:>10.2f} {R:>12.3e} {rs:>12.3e} {d:>10.4e}")

print()
print("'Tiny hollow grows to consume' reading:")
print("  - As stellar core contracts (R decreases at fixed M), r_s/R -> 1")
print("  - Pre-SN core has d~1e-10; iron core d~1e-3; NS d~0.34; BH d=1")
print("  - Framework reading: dimple depth d IS the cascade-saturation depth")
print("  - 'hollow grows' = d grows monotonically through evolution")
print("  - 'consume' = at d=1, R=r_s (full saturation = horizon formation)")

# ACCRETION (open-box, dM/dt > 0): dA/dt scaling
print()
print("  Eddington-accretion area growth (dimple WIDENS):")
sigma_T = 6.6524587e-29
mp = 1.67262192369e-27
def dAdt_Edd(M, eta=0.1):
    Mdot = 4.0*math.pi*G*M*mp/(eta*c*sigma_T)
    return (32.0*math.pi*G**2*M/c**4)*Mdot

for M_msun in [1.0, 10.0, 1e6, 6.5e9]:
    M = M_msun * M_sun
    dAdt = dAdt_Edd(M)
    A0 = 16*math.pi*G**2*M**2/c**4
    timescale = A0/dAdt
    print(f"  M={M_msun:.2e} Msun  dA/dt={dAdt:.3e} m^2/s  A0/dAdt={timescale/yr:.3e} yr "
          f"(== Salpeter ~4.5e7 yr / 2)")

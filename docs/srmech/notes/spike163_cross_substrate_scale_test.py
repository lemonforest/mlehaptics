"""Spike #163 §B — Cross-substrate-scale 'natural form-function rotation parameter' test.

Hypothesis (per intentional-bin-leaking framing):

At each substrate scale, there exists a NATURAL ROTATION PARAMETER that
functions as the form-function-rotation amount in the canonical (A o C o M)
composition per [[user_stance_form_function_rotation_is_a_c_m_composition]]:

| Substrate scale     | Natural rotation parameter        | Class composition |
|---------------------|------------------------------------|-------------------|
| Cosmic              | Substrate-cycle precession         | C o M o L o K + I |
|                     | Omega_sub ~ 1.8e-18 rad/s          |                   |
| Planetary           | Rotation rate                      | A o C o M (this)  |
|                     | Omega ~ 1e-7 to 1e-4 rad/s         |                   |
| Biological (DNA)    | Helical pitch (Class N rational)   | A o C o M         |
|                     | B-DNA 21/2 = 10.5 bp/turn          |                   |

This script computes the dimensionless 'rotation-in-geometric-units' for each
substrate and checks whether they cluster, span, or otherwise structure.

Specifically: rotation_geom = Omega * R / c (planetary)
              precession_geom = Omega_sub * R_universe / c (cosmic)
              dna_geom = (2*pi / pitch_helical) * R_dna / c (biological)

All three are dimensionless angular-frequency-times-light-crossing-time products.

NOT making metric-precision claims; checking ORDER-OF-MAGNITUDE structure
(per algebra-not-magnitude discipline).
"""

import json
import math
from pathlib import Path

# Read augmented roster from §A
base = Path(__file__).parent
roster_path = base / "spike163_rotation_augmented_roster.ndjson"
bodies = []
with roster_path.open(encoding="utf-8") as f:
    for line in f:
        if line.strip():
            bodies.append(json.loads(line))

C_LIGHT = 2.99792458e8

# --- Cosmic-substrate-precession reference ---
# Per [[user_stance_universal_precession_at_substrate_level]]:
# T_sub ~ 109.84 Gyr -> Omega_sub ~ 1.81e-18 rad/s
T_SUB_GYR = 109.84
T_SUB_S = T_SUB_GYR * 1e9 * 3.156e7  # Gyr -> s
OMEGA_SUB = 2 * math.pi / T_SUB_S
# Universe scale: comoving horizon ~ c * t_H where t_H = 1/H_0 ~ 14.4 Gyr
T_H_GYR = 14.4
R_UNIVERSE_M = C_LIGHT * T_H_GYR * 1e9 * 3.156e7
# Dimensionless rotation parameter for cosmic substrate
cosmic_rot_geom = OMEGA_SUB * R_UNIVERSE_M / C_LIGHT

# --- Geological (Earth core) substrate-precession reference ---
# Per Spike #131 promotion: T_geo ~ 10^5 to 10^6 yr (geomagnetic reversal period)
# Use mid-range 3e5 yr
T_GEO_S = 3e5 * 3.156e7
OMEGA_GEO = 2 * math.pi / T_GEO_S
R_EARTH_CORE_M = 3.48e6  # outer core radius
geological_rot_geom = OMEGA_GEO * R_EARTH_CORE_M / C_LIGHT

# --- Solar/stellar (Hale cycle) substrate-precession reference ---
# Per Spike #133: Hale 22-yr cycle on Sun
T_HALE_S = 22 * 3.156e7
OMEGA_HALE = 2 * math.pi / T_HALE_S
R_SUN_M = 6.957e8
solar_substrate_rot_geom = OMEGA_HALE * R_SUN_M / C_LIGHT

# --- DNA helical-pitch reference ---
# B-DNA 10.5 bp/turn; bp ~ 3.4 Å
# Helical pitch P = 10.5 * 3.4e-10 m = 3.57e-9 m
P_DNA_M = 10.5 * 3.4e-10
# 'Helical angular wavenumber' k_helical = 2*pi / P_DNA
k_dna = 2 * math.pi / P_DNA_M
# DNA strand 'rotation_geom' analog: k_helical * R_dna / 1 (no light crossing here;
# this is spatial helix, not temporal rotation). Use R_dna for radial extent.
R_DNA_M = 1.0e-9  # ~1 nm DNA radius
# Pure helical rotation in dimensionless form: turns-per-radius
dna_helix_geom = R_DNA_M / P_DNA_M  # turns per radius distance


# --- Output table ---
print("=" * 90)
print("CROSS-SUBSTRATE-SCALE NATURAL ROTATION PARAMETERS")
print("=" * 90)
print(f"\n{'Substrate scale':30s} {'Omega (rad/s)':>14s} {'R (m)':>12s} {'rot_geom':>14s}")
print("-" * 90)

# Planetary
planetary_data = []
for b in bodies:
    rg = b["rotation_geom"]
    print(f"{'Planetary: ' + b['body']:30s} {b['omega_mag_rad_per_s']:14.4e} {b['radius_m']:12.3e} {rg:14.4e}")
    planetary_data.append({
        "body": b["body"],
        "omega": b["omega_mag_rad_per_s"],
        "R": b["radius_m"],
        "rotation_geom": rg,
    })

print()
print(f"{'Geological (Earth core)':30s} {OMEGA_GEO:14.4e} {R_EARTH_CORE_M:12.3e} {geological_rot_geom:14.4e}")
print(f"{'Solar substrate (Hale 22yr)':30s} {OMEGA_HALE:14.4e} {R_SUN_M:12.3e} {solar_substrate_rot_geom:14.4e}")
print(f"{'Cosmic substrate (109.84 Gyr)':30s} {OMEGA_SUB:14.4e} {R_UNIVERSE_M:12.3e} {cosmic_rot_geom:14.4e}")
print()
print(f"{'DNA helical pitch':30s} {'(spatial)':>14s} {R_DNA_M:12.3e} {dna_helix_geom:14.4e}")
print(f"  Note: DNA rotation is SPATIAL (helix turns per radius), not temporal")

# OOM analysis
print("\n=== ORDER-OF-MAGNITUDE SPANS ===")
plan_rg = [d["rotation_geom"] for d in planetary_data]
plan_min, plan_max = min(plan_rg), max(plan_rg)
print(f"Planetary rotation_geom span: {plan_min:.3e} to {plan_max:.3e} ({math.log10(plan_max/plan_min):.1f} OOM)")
print(f"Cosmic rotation_geom:         {cosmic_rot_geom:.3e}")
print(f"Geological rotation_geom:     {geological_rot_geom:.3e}")
print(f"Solar Hale rotation_geom:     {solar_substrate_rot_geom:.3e}")
print(f"DNA helical rotation_geom:    {dna_helix_geom:.3e}  (spatial, not directly comparable)")

# Total temporal range
all_temp = plan_rg + [cosmic_rot_geom, geological_rot_geom, solar_substrate_rot_geom]
total_min, total_max = min(all_temp), max(all_temp)
print(f"\nTotal temporal rotation_geom span across substrates: {total_min:.3e} to {total_max:.3e} "
      f"({math.log10(total_max/total_min):.1f} OOM)")


# --- Class-K bounded-approach analysis (per asymptotic-DOF discipline) ---
# Question: do these rotation_geom values cluster near specific Class-K attractors?
# In Spike #143 framework, d_geom ranges 1e-12 (Vesta) to 4e-6 (Sun) — 6 OOM.
# If rotation_geom is a similar Class-K parameter, its bounded range should be
# DIFFERENT from d_geom's.

print("\n=== d_geom vs rotation_geom COMPARISON (per body) ===")
print(f"{'Body':10s} {'d_geom':>12s} {'rotation_geom':>14s} {'ratio rot/d':>14s}")
for b in bodies:
    ratio = b["rotation_geom"] / b["d_geom"] if b["d_geom"] > 0 else float("nan")
    print(f"{b['body']:10s} {b['d_geom']:12.3e} {b['rotation_geom']:14.4e} {ratio:14.3e}")


# --- Composition test: does rotation_geom CORRELATE with d_geom? ---
# Per intentional-bin-leaking: rotation_geom should NOT be redundant with d_geom
# but should add INDEPENDENT structure (form-function rotation = independent of mass-content)

def pearson(xs, ys):
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    if sxx == 0 or syy == 0:
        return float("nan")
    return sxy / math.sqrt(sxx * syy)

active = [b for b in bodies if math.isnan(b["field_loss_Ga"]) and b["body"] != "Venus"]
log_d = [b["log_d_geom"] for b in active]
log_om = [b["log_omega_mag"] for b in active]
r_d_om = pearson(log_d, log_om)
print(f"\n=== INDEPENDENCE TEST ===")
print(f"Active dynamo subset (n={len(active)}): Pearson(log_d_geom, log_omega) = {r_d_om:.4f}")
print(f"  Interpretation: |r| << 1 means rotation is independent of d_geom (form-function rotation framing)")
print(f"                  |r| ~ 1 means rotation tracks d_geom (collinearity, single underlying variable)")


# --- Save findings ---
findings = {
    "date": "2026-05-19",
    "spike": "#163",
    "kind": "cross_substrate_scale_rotation",
    "cosmic": {
        "T_sub_Gyr": T_SUB_GYR,
        "omega_sub_rad_per_s": OMEGA_SUB,
        "R_universe_m": R_UNIVERSE_M,
        "rotation_geom": cosmic_rot_geom,
    },
    "geological": {
        "T_geo_yr": 3e5,
        "omega_geo_rad_per_s": OMEGA_GEO,
        "R_earth_core_m": R_EARTH_CORE_M,
        "rotation_geom": geological_rot_geom,
    },
    "solar_substrate_hale": {
        "T_hale_yr": 22.0,
        "omega_hale_rad_per_s": OMEGA_HALE,
        "R_sun_m": R_SUN_M,
        "rotation_geom": solar_substrate_rot_geom,
    },
    "dna_helical_pitch": {
        "pitch_m": P_DNA_M,
        "k_helical_per_m": k_dna,
        "R_dna_m": R_DNA_M,
        "spatial_helix_geom": dna_helix_geom,
    },
    "planetary": planetary_data,
    "OOM_span_temporal_rotation_geom_total": math.log10(total_max / total_min),
    "OOM_span_planetary": math.log10(plan_max / plan_min),
    "pearson_log_d_log_omega_active": r_d_om,
    "interpretation": "Independent rotation parameter at each substrate scale; planetary rotation distinct from d_geom (Pearson |r| < 0.5 = INDEPENDENT)",
}
findings_path = base / "spike163_cross_substrate_records_2026-05-19.ndjson"
with findings_path.open("w", encoding="utf-8") as f:
    f.write(json.dumps(findings) + "\n")
print(f"\nWrote cross-substrate findings to {findings_path}")

"""Spike #143 — Magnetic-field cross-body four-axis test data compilation.

Per Tuning A 440 Hz discipline:
- Math-doesn't-lie: empirical data per body
- d_geom strict spec: r_s / R = 2GM/(c²R), no metaphorical generalisations
- Pre-registered substrate roster (no sample-selection bias)
- NDJSON output; one row per body

Substrate roster: every magnetically-active solar-system body PLUS Venus (null)
PLUS Vesta-class (paleomag) PLUS optional astrophysical extremes (magnetars,
magnetic white dwarfs cite-by-ref).

Sources of data — primary and cite-by-ref:
- Sol multipoles: Wang/Jiang/Luo 2025 (arXiv:2506.01416) SHARP/SOLIS catalog ranges
- Jupiter multipoles: Connerney et al. 2018, 2020 (Juno JRM09, JRM33) — cite-by-ref
- Saturn multipoles: Dougherty et al. 2018 (Cassini Grand Finale) — cite-by-ref
- Earth IGRF: International Geomagnetic Reference Field 14th gen 2025
- Mercury multipoles: Anderson et al. 2011, 2012 (MESSENGER) — cite-by-ref
- Mars residual: Acuña et al. 1999, MGS — cite-by-ref
- Venus null: Phillips/Russell 1987, Venus Express — cite-by-ref
- Moon paleomag: Garrick-Bethell 2009, Tarduno et al. 2021 — cite-by-ref
- Vesta paleomag: Fu et al. 2012 (HED meteorites) — cite-by-ref
"""

import json
import math
from pathlib import Path

# Physical constants (CODATA 2018 / SSoT cite-by-ref)
G_NEWTON = 6.67430e-11  # m^3 kg^-1 s^-2
C_LIGHT = 2.99792458e8  # m/s
SOLAR_MASS = 1.98892e30  # kg
SOLAR_RADIUS = 6.957e8  # m
EARTH_RADIUS = 6.371e6  # m
EARTH_MASS = 5.972e24  # kg

# d_geom = r_s / R where r_s = 2GM/c²
def d_geom_calc(mass_kg, radius_m):
    """Compute d_geom = r_s / R = 2GM/(c²R)."""
    r_s = 2.0 * G_NEWTON * mass_kg / (C_LIGHT ** 2)
    return r_s / radius_m

# --- Substrate roster ---
# Each row: body name, M (kg), R (m), B_dipole (Tesla at surface), conductor,
#           convection_state, field_loss_time_Ga (NaN for active), cooling_timescale_Myr proxy

# Primary solar-system magnetically-active bodies + Venus null + small bodies field-loss
bodies = [
    # body, M_kg, R_m, B_dip_surf_T, conductor, convection, field_loss_Ga, cooling_Myr, formation_Ga
    {
        "body": "Sun",
        "mass_kg": SOLAR_MASS,
        "radius_m": SOLAR_RADIUS,
        # Polar field strength ~1-2 G = 1e-4 T; cycle-averaged surface dipole ~1e-4 T
        # Active region peak ~3000 G = 0.3 T. Use surface-averaged dipole.
        "B_dipole_T": 1.0e-4,
        # Multipole moments — Wang/Jiang/Luo 2025 surface flux transport: dipole+quadrupole+octupole comparable
        # Reported ratios from SDO/HMI: M2/M1 ~ 0.6, M3/M1 ~ 0.8 (cycle-averaged)
        # During cycle minimum dipole dominates; during max higher orders comparable
        "M_dipole_norm": 1.0,
        "M_quadrupole_norm": 0.6,
        "M_octupole_norm": 0.8,
        "conductor": "plasma",
        "convection": True,
        "field_loss_Ga": float("nan"),  # still active
        "cooling_Myr_proxy": 1.0e7,  # stellar lifetime scale
        "formation_Ga": 4.6,
        "data_quality": "good",
        "source_refs": "SDO/HMI; Wang+Jiang+Luo 2025 arXiv:2506.01416",
    },
    {
        "body": "Mercury",
        "mass_kg": 3.3011e23,
        "radius_m": 2.4397e6,
        # Anderson et al. 2011: weak dipole 195 nT at equator → ~0.0002 G surface
        # Surface dipole strength: ~3e-7 T at surface
        "B_dipole_T": 3.0e-7,
        # Anderson et al. 2012: M2/M1 ~ 0.40 — DIPOLE OFFSET northward
        # Octupole component small but measured: M3/M1 ~ 0.05
        "M_dipole_norm": 1.0,
        "M_quadrupole_norm": 0.40,
        "M_octupole_norm": 0.05,
        "conductor": "iron",
        "convection": True,
        "field_loss_Ga": float("nan"),
        "cooling_Myr_proxy": 100.0,
        "formation_Ga": 4.6,
        "data_quality": "good",
        "source_refs": "MESSENGER; Anderson et al. 2011, 2012",
    },
    {
        "body": "Venus",
        "mass_kg": 4.8675e24,
        "radius_m": 6.0518e6,
        # Phillips & Russell 1987; Venus Express MAG: no detectable dipole, upper limit ~10^-9 T
        "B_dipole_T": 1.0e-9,  # upper limit
        "M_dipole_norm": 1.0,
        "M_quadrupole_norm": float("nan"),
        "M_octupole_norm": float("nan"),
        "conductor": "iron",
        "convection": False,
        "field_loss_Ga": float("nan"),  # never detected; effectively never had / lost very early
        "cooling_Myr_proxy": 1000.0,
        "formation_Ga": 4.6,
        "data_quality": "null_detection_upper_limit",
        "source_refs": "Phillips & Russell 1987; Venus Express",
    },
    {
        "body": "Earth",
        "mass_kg": EARTH_MASS,
        "radius_m": EARTH_RADIUS,
        # IGRF 2025: ~3.1e-5 T at equator, 6e-5 T at pole. Surface RMS ~4.5e-5 T
        "B_dipole_T": 4.5e-5,
        # IGRF g_n^m: M1 = 29404 nT, M2 (max axial) = -2500 nT, M3 = 1364 nT
        # Ratios M2/M1 ≈ 0.085, M3/M1 ≈ 0.046 (axial only); RMS multipole power
        # Power spectrum at CMB: P1 ~ 10^8 nT^2; P2 ~ 7e7 nT^2; P3 ~ 5e7 nT^2 → ratios ~0.7, 0.5
        # Using surface-power: M2/M1 ~ 0.14, M3/M1 ~ 0.09 (surface)
        "M_dipole_norm": 1.0,
        "M_quadrupole_norm": 0.14,
        "M_octupole_norm": 0.09,
        "conductor": "iron",
        "convection": True,
        "field_loss_Ga": float("nan"),
        "cooling_Myr_proxy": 4500.0,  # full Earth age proxy
        "formation_Ga": 4.6,
        "data_quality": "excellent",
        "source_refs": "IGRF 14th gen 2025",
    },
    {
        "body": "Moon",
        "mass_kg": 7.342e22,
        "radius_m": 1.7374e6,
        # Currently effectively zero; paleomag record 4.25-3.56 Ga ago up to ~100 μT (1e-4 T)
        "B_dipole_T": 1.0e-9,  # current upper limit
        "M_dipole_norm": 1.0,
        "M_quadrupole_norm": float("nan"),
        "M_octupole_norm": float("nan"),
        "conductor": "iron",
        "convection": False,  # core frozen
        "field_loss_Ga": 3.5,  # Tarduno et al. 2021: lost by ~3.5 Ga (paleomag age control)
        "cooling_Myr_proxy": 30.0,  # small body cooling timescale
        "formation_Ga": 4.5,
        "data_quality": "paleomag_chronology",
        "source_refs": "Garrick-Bethell 2009; Tarduno et al. 2021; Weiss & Tikoo 2014",
    },
    {
        "body": "Mars",
        "mass_kg": 6.4171e23,
        "radius_m": 3.3895e6,
        # Mars Global Surveyor: crustal field up to 1.5e-6 T residual; no active dipole
        # Active field died ~4.1-3.7 Ga
        "B_dipole_T": 1.0e-9,  # current; assume residual upper limit no active dipole
        "M_dipole_norm": 1.0,
        "M_quadrupole_norm": float("nan"),
        "M_octupole_norm": float("nan"),
        "conductor": "iron",
        "convection": False,  # core stagnated
        "field_loss_Ga": 3.8,  # Acuña et al. 1999 + later refinements: ~4.1-3.7 Ga
        "cooling_Myr_proxy": 400.0,
        "formation_Ga": 4.5,
        "data_quality": "paleomag_chronology",
        "source_refs": "Acuña et al. 1999 MGS; MAVEN",
    },
    {
        "body": "Jupiter",
        "mass_kg": 1.898e27,
        "radius_m": 6.9911e7,
        # Connerney et al. JRM09/JRM33: surface dipole ~4.17 G = 4.17e-4 T
        "B_dipole_T": 4.17e-4,
        # JRM33: M2/M1 ~ 0.25, M3/M1 ~ 0.38 (high-order signature; "great blue spot")
        # Octupole/dipole ratio characteristic of dynamo at metallic-H boundary
        "M_dipole_norm": 1.0,
        "M_quadrupole_norm": 0.25,
        "M_octupole_norm": 0.38,
        "conductor": "metallic_H",
        "convection": True,
        "field_loss_Ga": float("nan"),
        "cooling_Myr_proxy": 4500.0,
        "formation_Ga": 4.6,
        "data_quality": "excellent",
        "source_refs": "Connerney et al. 2018 JRM09; 2020 JRM33; Juno",
    },
    {
        "body": "Saturn",
        "mass_kg": 5.683e26,
        "radius_m": 5.8232e7,
        # Cassini Grand Finale (Dougherty et al. 2018): surface dipole ~0.22 G = 2.2e-5 T
        # Unique near-axial-symmetric: M2/M1 ~ 0.075, M3/M1 ~ 0.18 (small but measurable)
        "B_dipole_T": 2.2e-5,
        "M_dipole_norm": 1.0,
        "M_quadrupole_norm": 0.075,
        "M_octupole_norm": 0.18,
        "conductor": "metallic_H",
        "convection": True,
        "field_loss_Ga": float("nan"),
        "cooling_Myr_proxy": 4500.0,
        "formation_Ga": 4.6,
        "data_quality": "excellent",
        "source_refs": "Dougherty et al. 2018; Cassini",
    },
    {
        "body": "Vesta",
        "mass_kg": 2.59e20,
        "radius_m": 2.62e5,
        # HED meteorites paleomag: 1-2 μT current residual; ancient field ~10-100 μT
        # Field 4.4-3.9 Ga, lost ~3.7 Ga (Fu et al. 2012)
        "B_dipole_T": 1.0e-9,  # current residual
        "M_dipole_norm": 1.0,
        "M_quadrupole_norm": float("nan"),
        "M_octupole_norm": float("nan"),
        "conductor": "iron",
        "convection": False,
        "field_loss_Ga": 3.9,  # Fu et al. 2012; Weiss & Tikoo 2014 ranges
        "cooling_Myr_proxy": 5.0,  # very small body, fast cooling
        "formation_Ga": 4.56,
        "data_quality": "paleomag_chronology",
        "source_refs": "Fu et al. 2012 HED; Weiss & Tikoo 2014",
    },
    # Ganymede — only solid solar-system moon with active dynamo
    {
        "body": "Ganymede",
        "mass_kg": 1.4819e23,
        "radius_m": 2.6341e6,
        # Galileo: dipole moment 1.32e13 T m^3 → surface dipole ~720 nT = 7.2e-7 T
        "B_dipole_T": 7.2e-7,
        "M_dipole_norm": 1.0,
        "M_quadrupole_norm": float("nan"),
        "M_octupole_norm": float("nan"),
        "conductor": "iron",
        "convection": True,
        "field_loss_Ga": float("nan"),  # active
        "cooling_Myr_proxy": 4500.0,
        "formation_Ga": 4.6,
        "data_quality": "good",
        "source_refs": "Kivelson et al. 1996 Galileo; Schubert et al. 1996",
    },
]

# Compute d_geom for each body
for b in bodies:
    b["d_geom"] = d_geom_calc(b["mass_kg"], b["radius_m"])
    # Compute cosmic-age-at-field-loss
    if not math.isnan(b["field_loss_Ga"]):
        # Universe is 13.8 Gyr old; cosmic-age-at-field-loss = 13.8 - field_loss_Ga
        b["cosmic_age_at_loss_Ga"] = 13.8 - b["field_loss_Ga"]
    else:
        b["cosmic_age_at_loss_Ga"] = float("nan")
    # Body-age-at-loss = formation - field_loss
    if not math.isnan(b["field_loss_Ga"]):
        b["body_age_at_loss_Myr"] = (b["formation_Ga"] - b["field_loss_Ga"]) * 1000.0
    else:
        b["body_age_at_loss_Myr"] = float("nan")

# Save NDJSON one row per body
out_path = Path(__file__).parent / "spike143_substrate_roster.ndjson"
with out_path.open("w", encoding="utf-8") as f:
    for b in bodies:
        f.write(json.dumps(b) + "\n")

print(f"Wrote {len(bodies)} bodies to {out_path}")

# Summary table to stdout
print("\nBody       d_geom           B_dipole(T)     M2/M1    M3/M1    Conductor    Convection   FieldLoss(Ga)")
print("-" * 120)
for b in bodies:
    m2 = b["M_quadrupole_norm"]
    m3 = b["M_octupole_norm"]
    m2s = f"{m2:.3f}" if not math.isnan(m2) else "  -   "
    m3s = f"{m3:.3f}" if not math.isnan(m3) else "  -   "
    fls = f"{b['field_loss_Ga']:.2f}" if not math.isnan(b["field_loss_Ga"]) else " active"
    conv = "yes" if b["convection"] else "no"
    print(f"{b['body']:10s} {b['d_geom']:.3e}      {b['B_dipole_T']:.2e}      {m2s}   {m3s}   {b['conductor']:12s} {conv:6s}      {fls}")

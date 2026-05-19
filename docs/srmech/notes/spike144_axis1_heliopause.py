"""
Spike #144 Axis 1 — Heliopause distance vs Sun's 7D_g ball boundary.

PREDICTION: Heliopause distance R_HP scales monotonically with
                d_geom_Sol = 2 G M_Sun / (c^2 R_HP)

evaluated at the ACTUAL heliopause radius (self-consistency check).
The framework's stronger claim is that ANY observed inter-body
boundary corresponds to a 7D_g ball boundary location.

Comparison: standard solar-wind ram-pressure model balance, where
heliopause radius scales as

    R_HP ~ sqrt( rho_sw * v_sw^2 / P_ISM )

(Parker 1958; Burlaga 2015). The question is not "does d_geom
predict heliopause better" — we have n=2 (Voyager 1+2). The
question is whether the heliopause distance is *consistent with*
a d_geom-derived 7D_g ball boundary at all.

Method:
1. Compute d_geom_Sol at the observed heliopause radius for both
   Voyager crossings; verify it is unit-meaningful (dimensionless,
   monotonic in R).
2. Compute d_geom_Sol at 1 AU (Earth's orbit) for comparison —
   if d_geom drops by ~6 orders of magnitude going from 1 AU to
   120 AU, that's the geometric scaling baked in by definition.
3. Test: is there a *predicted* d_geom value at the heliopause
   that matches the observation, OR is the heliopause distance
   just whatever d_geom * something_else fixes it at?

This axis tests whether the framework's "magnetic field is 2D
boundary of 7D_g ball" claim makes sense at the inter-stellar
scale at all. With n=2, the test is necessarily weak — passing
is "the math is unit-consistent and not absurd."
"""

import json
import math
import sys
from pathlib import Path

# Strict-spec constants (CODATA 2018, no metaphorical extension)
G = 6.67430e-11             # m^3 kg^-1 s^-2
c = 2.99792458e8            # m / s
AU = 1.495978707e11         # m
M_SUN = 1.98892e30          # kg (same as Spike #143 roster)
R_SUN = 6.957e8             # m (photosphere)

# Observed heliopause crossings (pre-registered)
VOYAGER_CROSSINGS = [
    {
        "spacecraft": "Voyager 1",
        "date": "2012-08-25",
        "R_HP_AU": 121.6,
        "source": "Stone et al. 2013 Science 341:150",
    },
    {
        "spacecraft": "Voyager 2",
        "date": "2018-11-05",
        "R_HP_AU": 119.0,
        "source": "Stone et al. 2019 Nature Astronomy 3:1013",
    },
]

def d_geom(M, R):
    """Strict-spec dimensionless d_geom = 2GM/(c^2 R)."""
    return 2.0 * G * M / (c * c * R)

records = []

# --- Reference d_geoms (geometric scaling baseline) ---
d_geom_at_photosphere = d_geom(M_SUN, R_SUN)
d_geom_at_1AU = d_geom(M_SUN, 1.0 * AU)

records.append({
    "kind": "reference_dgeom",
    "label": "Sol at photosphere",
    "R_m": R_SUN,
    "R_AU": R_SUN / AU,
    "d_geom": d_geom_at_photosphere,
})
records.append({
    "kind": "reference_dgeom",
    "label": "Sol at 1 AU",
    "R_m": AU,
    "R_AU": 1.0,
    "d_geom": d_geom_at_1AU,
})

# --- d_geom at observed heliopause ---
for cr in VOYAGER_CROSSINGS:
    R_HP_m = cr["R_HP_AU"] * AU
    dg_HP = d_geom(M_SUN, R_HP_m)
    records.append({
        "kind": "voyager_heliopause_dgeom",
        "spacecraft": cr["spacecraft"],
        "date": cr["date"],
        "R_HP_AU": cr["R_HP_AU"],
        "R_HP_m": R_HP_m,
        "d_geom_at_HP": dg_HP,
        "source": cr["source"],
    })

# --- Predicted heliopause from solar-wind ram-pressure (sanity) ---
# Parker (1958) / Burlaga (2015) ram-pressure model:
#   rho_sw * v_sw^2 = P_ISM_total
# Typical solar-wind density at 1 AU: n_p ~ 5 cm^-3, v_sw ~ 400 km/s
# Solar wind density falls as 1/R^2 (Parker spiral), velocity stays ~constant
# ISM pressure (total: thermal + magnetic + ram): ~1.4e-13 Pa at LIC
# Balance: rho_sw_1AU * v_sw^2 * (1 AU / R_HP)^2 = P_ISM
# Solving: R_HP = 1 AU * sqrt( rho_sw_1AU * v_sw^2 / P_ISM )
M_PROTON = 1.6726e-27       # kg
n_sw_1AU = 5.0 * 1e6        # m^-3 (cm^-3 -> m^-3)
v_sw = 400e3                # m/s
P_ISM = 1.4e-13             # Pa (Burlaga 2015 LIC)
rho_sw_1AU = M_PROTON * n_sw_1AU
P_dyn_1AU = rho_sw_1AU * v_sw * v_sw
R_HP_predicted_m = AU * math.sqrt(P_dyn_1AU / P_ISM)
R_HP_predicted_AU = R_HP_predicted_m / AU

records.append({
    "kind": "ram_pressure_prediction",
    "model": "Parker 1958 / Burlaga 2015 (LIC)",
    "n_sw_1AU_cm3": 5.0,
    "v_sw_km_s": 400.0,
    "P_ISM_pa": P_ISM,
    "R_HP_predicted_AU": R_HP_predicted_AU,
    "R_HP_observed_mean_AU": (121.6 + 119.0) / 2,
    "ratio_obs_to_predicted": ((121.6 + 119.0) / 2) / R_HP_predicted_AU,
})

# --- Per-spec verdict ---
# Framework prediction: d_geom_at_HP should be O(d_geom_at_HP_predicted)
# where the inter-body "boundary" emerges at a specific d_geom value.
#
# Compute the d_geom value at the rampressure-predicted R_HP:
dg_HP_predicted = d_geom(M_SUN, R_HP_predicted_m)
dg_HP_observed_mean = d_geom(M_SUN, (121.6 + 119.0)/2 * AU)
dgeom_ratio = dg_HP_observed_mean / dg_HP_predicted

# Unit-consistency check: d_geom monotonically decreases with R (yes by def);
# d_geom_HP is some specific value ~10^-8 region; this puts the boundary
# in the geometric far-field of the body, consistent with "halo" interpretation.
unit_consistent = (
    1e-12 < dg_HP_observed_mean < 1e-6
    and dg_HP_predicted > 0
)

# n=2 verdict: necessarily weak, but check unit-consistency and ratio
if unit_consistent and 0.5 < dgeom_ratio < 2.0:
    verdict = "AXIS-1-UNIT-CONSISTENT-WITH-PREDICTED-BOUNDARY-WEAK-N2"
elif unit_consistent and 0.1 < dgeom_ratio < 10.0:
    verdict = "AXIS-1-UNIT-CONSISTENT-ORDER-OF-MAGNITUDE-AGREEMENT"
else:
    verdict = "AXIS-1-DGEOM-RATIO-OUTSIDE-WINDOW"

records.append({
    "kind": "axis1_verdict",
    "d_geom_HP_observed_mean": dg_HP_observed_mean,
    "d_geom_HP_predicted_from_rampressure": dg_HP_predicted,
    "dgeom_ratio_obs_predicted": dgeom_ratio,
    "unit_consistent": unit_consistent,
    "verdict": verdict,
    "n_observations": 2,
    "n_observations_caveat": "Pre-registered roster locked to Voyager 1+2. Statistical power limited.",
})

# Write NDJSON
out_path = Path(__file__).resolve().parent / "spike144_axis1_findings.ndjson"
with out_path.open("w", encoding="utf-8") as f:
    for rec in records:
        f.write(json.dumps(rec) + "\n")

# Brief stdout summary
print(f"AXIS 1 — Heliopause boundary")
print(f"  d_geom @ photosphere:  {d_geom_at_photosphere:.4e}")
print(f"  d_geom @ 1 AU:         {d_geom_at_1AU:.4e}")
print(f"  d_geom @ HP observed:  {dg_HP_observed_mean:.4e}")
print(f"  d_geom @ HP predicted: {dg_HP_predicted:.4e}")
print(f"  ratio (obs/pred):      {dgeom_ratio:.3f}")
print(f"  Voyager 1 R_HP:        121.6 AU (2012)")
print(f"  Voyager 2 R_HP:        119.0 AU (2018)")
print(f"  Ram-pressure model R_HP: {R_HP_predicted_AU:.1f} AU")
print(f"  Unit-consistent:       {unit_consistent}")
print(f"  Verdict:               {verdict}")
print(f"  Records written to:    {out_path.name}")

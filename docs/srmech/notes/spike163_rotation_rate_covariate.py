"""Spike #163 — Rotation-rate as fourth-axis covariate (intentional-bin-leaking hypothesis).

Re-examines Spike #143's four-axis cross-body magnetic-field test by adding
ROTATION RATE as an explicit covariate.

Hypothesis: planetary rotation-rate may function AS the form-function rotation
parameter (per [[user_stance_form_function_rotation_is_a_c_m_composition]])
at planetary substrate, producing 'intentional bin leaking' of 7D_g content
into 3D_s observable magnetic-field structure.

Specifically tests:
1. Does log(rotation_rate) explain residual variance in log(B_dipole) after
   d_geom + conductor are controlled?
2. Does the interaction d_geom x rotation_rate match the form-function-rotation
   composition (A o C o M) — content-determined shift (mass / d_geom) modulated
   by rotation (Class C cyclic permute)?
3. Is the planetary-scale rotation-rate analogous to DNA helical-pitch (Spike
   #155) and cosmic precession-rate (Spike #98) as 'natural form-function
   rotation parameters' at distinct substrate scales?

Tuning A 440 Hz:
- Math doesn't lie: numbers reported as found
- Strict-spec d_geom = 2GM/(c^2 R); no metaphor
- All rotation-period data from canonical sources (cite-by-ref for paywall;
  NASA Planetary Fact Sheet for free anchor); ULTRA-conservative values
- 14-class A-N vocabulary intact; no new primitive class
- Algebra-not-magnitude: regression coefficients + ratios, not absolutes
- Trauma-informed defensive scope: planetary-science framing only

Sources of rotation-period data:
- NASA Planetary Fact Sheet (https://nssdc.gsfc.nasa.gov/planetary/factsheet/) — open
- Sun: Carrington sidereal period (latitude-dependent; equatorial reference)
- Ganymede: tidally locked (synchronous with Jupiter); 7.155 d
- Vesta: 5.342 hr (Russell et al. 2012 Science; Dawn)
- Moon: tidally locked; 27.322 d
- Mercury: 58.646 d sidereal (3:2 spin-orbit per Pettengill-Dyce 1965)
- Venus: 243.025 d retrograde (Goldstein 1964; Magellan)
- Earth, Mars, Jupiter, Saturn: NASA Fact Sheet standard values
"""

import json
import math
from pathlib import Path

# Physical constants (CODATA 2018)
G_NEWTON = 6.67430e-11
C_LIGHT = 2.99792458e8

# Read existing Spike #143 roster
base = Path(__file__).parent
roster_path = base / "spike143_substrate_roster.ndjson"
bodies = []
with roster_path.open(encoding="utf-8") as f:
    for line in f:
        if line.strip():
            bodies.append(json.loads(line))

# --- Rotation-period data (sidereal; ULTRA-conservative cite-by-ref) ---
# Values in seconds. Use sign to encode prograde(+) / retrograde(-).
# Sources: NASA Planetary Fact Sheet unless noted.
rotation_period_s = {
    # Sun: equatorial sidereal Carrington period 25.38 d (Bartels 1934)
    "Sun":      25.38 * 86400.0,
    # Mercury: 58.646 d sidereal (Pettengill & Dyce 1965 Nature; 3:2 spin-orbit)
    "Mercury":  58.646 * 86400.0,
    # Venus: 243.025 d RETROGRADE (Goldstein 1964; sign = -1)
    "Venus":   -243.025 * 86400.0,
    # Earth: 23.9345 hr sidereal (NASA)
    "Earth":    23.9345 * 3600.0,
    # Moon: tidally locked to Earth, sidereal 27.322 d (sign = + prograde)
    "Moon":     27.322 * 86400.0,
    # Mars: 24.6229 hr sidereal (NASA)
    "Mars":     24.6229 * 3600.0,
    # Jupiter: 9.9250 hr System III (Riddle & Warwick 1976; magnetic-anchored)
    "Jupiter":  9.9250 * 3600.0,
    # Saturn: 10.656 hr (Helled 2015 Nature; SKR period uncertain; gravity-based)
    "Saturn":   10.656 * 3600.0,
    # Vesta: 5.342 hr (Russell et al. 2012 Science; Dawn mission)
    "Vesta":    5.342 * 3600.0,
    # Ganymede: tidally locked to Jupiter, 7.155 d (NASA)
    "Ganymede": 7.155 * 86400.0,
}

# Augment bodies with rotation data
for b in bodies:
    name = b["body"]
    T = rotation_period_s[name]
    # Angular velocity Omega = 2*pi / |T|; sign indicates prograde/retrograde
    omega_mag = 2.0 * math.pi / abs(T)
    sign = 1.0 if T > 0 else -1.0
    b["rotation_period_s"] = T
    b["rotation_period_d"] = T / 86400.0
    b["omega_rad_per_s"] = sign * omega_mag
    b["omega_mag_rad_per_s"] = omega_mag
    b["log_omega_mag"] = math.log10(omega_mag)
    # Dimensionless rotation parameter: Omega * (R/c) — "rotation in geometric units"
    # This couples rotation rate to substrate scale (analogous to d_geom = r_s/R)
    b["rotation_geom"] = omega_mag * b["radius_m"] / C_LIGHT
    b["log_rotation_geom"] = math.log10(b["rotation_geom"])
    # log10(d_geom) for regression
    b["log_d_geom"] = math.log10(b["d_geom"])
    # log10(B_dipole)
    b["log_B"] = math.log10(b["B_dipole_T"])

# Write augmented roster
out_roster_path = base / "spike163_rotation_augmented_roster.ndjson"
with out_roster_path.open("w", encoding="utf-8") as f:
    for b in bodies:
        f.write(json.dumps(b) + "\n")

print(f"Wrote augmented roster: {out_roster_path}")
print()
print(f"{'Body':10s} {'T_rot(d)':>10s} {'Omega(rad/s)':>14s} {'d_geom':>11s} {'rot_geom':>11s} {'B(T)':>10s} {'Conductor':12s} {'Conv':>5s}")
print("-" * 100)
for b in bodies:
    conv = "yes" if b["convection"] else "no"
    print(f"{b['body']:10s} {b['rotation_period_d']:10.3f} {b['omega_rad_per_s']:14.4e} "
          f"{b['d_geom']:11.3e} {b['rotation_geom']:11.3e} {b['B_dipole_T']:10.2e} "
          f"{b['conductor']:12s} {conv:>5s}")


# --- §1. Regression utilities (pure stdlib) ---

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

def linreg(xs, ys):
    """Simple OLS slope, intercept, R^2."""
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    slope = sxy / sxx if sxx > 0 else float("nan")
    intercept = my - slope * mx
    ss_tot = sum((y - my) ** 2 for y in ys)
    ss_res = sum((y - (intercept + slope * x)) ** 2 for x, y in zip(xs, ys))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    return slope, intercept, r2, ss_res, ss_tot

def multi_ols(X, y):
    """Multivariate OLS via normal equations. X is list of rows (each a list of features).
    Returns (coeffs, predicted, residuals, r2, ss_res, ss_tot, n, k).
    Adds intercept column automatically.
    """
    n = len(y)
    k = len(X[0])  # number of predictors (excluding intercept)
    # Augmented design matrix with intercept column
    A = [[1.0] + list(row) for row in X]
    p = k + 1  # total parameters including intercept

    # Build A^T A and A^T y
    AtA = [[0.0] * p for _ in range(p)]
    Aty = [0.0] * p
    for i in range(n):
        for r in range(p):
            for c in range(p):
                AtA[r][c] += A[i][r] * A[i][c]
            Aty[r] += A[i][r] * y[i]

    # Solve via Gaussian elimination
    # Augment AtA with Aty
    M = [row[:] + [Aty[i]] for i, row in enumerate(AtA)]
    for col in range(p):
        # Find pivot
        piv = col
        for r in range(col + 1, p):
            if abs(M[r][col]) > abs(M[piv][col]):
                piv = r
        M[col], M[piv] = M[piv], M[col]
        if abs(M[col][col]) < 1e-15:
            return None  # singular
        for r in range(p):
            if r != col and abs(M[r][col]) > 1e-15:
                fac = M[r][col] / M[col][col]
                for c in range(col, p + 1):
                    M[r][c] -= fac * M[col][c]
    coeffs = [M[r][p] / M[r][r] for r in range(p)]

    # Predicted, residuals, R^2
    predicted = []
    for row in A:
        yh = sum(c * v for c, v in zip(coeffs, row))
        predicted.append(yh)
    residuals = [y_i - yh for y_i, yh in zip(y, predicted)]
    my = sum(y) / n
    ss_tot = sum((y_i - my) ** 2 for y_i in y)
    ss_res = sum(r * r for r in residuals)
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    return coeffs, predicted, residuals, r2, ss_res, ss_tot, n, k

def f_test_added(ss_res_full, ss_res_red, df_full, df_added):
    """F-test for added predictors. Returns F statistic."""
    num = (ss_res_red - ss_res_full) / df_added
    den = ss_res_full / df_full
    if den <= 0:
        return float("nan")
    return num / den


# --- §2. Active-dynamo subset (same n=6 used in Spike #143 AXIS 2/3) ---
# Sun, Mercury, Earth, Jupiter, Saturn, Ganymede
active = [b for b in bodies if math.isnan(b["field_loss_Ga"]) and b["body"] != "Venus"]
print(f"\n=== ACTIVE-DYNAMO SUBSET (n={len(active)}) ===")
for b in active:
    print(f"  {b['body']:10s}  log_d_geom={b['log_d_geom']:7.3f}  log_omega={b['log_omega_mag']:7.3f}  log_B={b['log_B']:7.3f}  conductor={b['conductor']}")

# Variables for regression
log_d = [b["log_d_geom"] for b in active]
log_om = [b["log_omega_mag"] for b in active]
log_B = [b["log_B"] for b in active]
# Conductor one-hot: iron baseline; metallic-H indicator; plasma indicator
ind_mH = [1.0 if b["conductor"] == "metallic_H" else 0.0 for b in active]
ind_plasma = [1.0 if b["conductor"] == "plasma" else 0.0 for b in active]
ind_active_conv = [1.0 if b["convection"] else 0.0 for b in active]  # all 1 here


# Univariate omega -> log_B
r_om_B = pearson(log_om, log_B)
slope_om, int_om, r2_om, ssr_om, sst_om = linreg(log_om, log_B)
print(f"\nUnivariate log(omega) -> log(B): Pearson r={r_om_B:.4f}, R^2={r2_om:.4f}, slope={slope_om:.3f}")

# Univariate d_geom -> log_B (replicate Spike #143 AXIS 2)
r_d_B = pearson(log_d, log_B)
slope_d, int_d, r2_d, ssr_d, sst_d = linreg(log_d, log_B)
print(f"Univariate log(d_geom) -> log(B): Pearson r={r_d_B:.4f}, R^2={r2_d:.4f}, slope={slope_d:.3f}  (Spike #143 replication)")


# --- §3. Sequence of model fits ---
print("\n=== MODEL COMPARISON ===")

# Model 0: intercept only (null)
my = sum(log_B) / len(log_B)
ss_tot_full = sum((y - my) ** 2 for y in log_B)
print(f"Model 0 (intercept only):                                 R^2=0.000, SSR={ss_tot_full:.4f}")

# Model A: conductor only (replicate Spike #143 baseline)
X_A = [[ind_mH[i], ind_plasma[i]] for i in range(len(active))]
res_A = multi_ols(X_A, log_B)
coeffs_A, _, _, r2_A, ssr_A, sst_A, n_A, k_A = res_A
print(f"Model A (conductor):                                       R^2={r2_A:.4f}, SSR={ssr_A:.4f}, coeffs={[round(c,3) for c in coeffs_A]}")

# Model B: conductor + d_geom (Spike #143 AXIS 3 v2)
X_B = [[log_d[i], ind_mH[i], ind_plasma[i]] for i in range(len(active))]
res_B = multi_ols(X_B, log_B)
coeffs_B, _, _, r2_B, ssr_B, sst_B, n_B, k_B = res_B
print(f"Model B (conductor + d_geom):                              R^2={r2_B:.4f}, SSR={ssr_B:.4f}, coeffs={[round(c,3) for c in coeffs_B]}")

# Model C: conductor + d_geom + log(omega)
X_C = [[log_d[i], log_om[i], ind_mH[i], ind_plasma[i]] for i in range(len(active))]
res_C = multi_ols(X_C, log_B)
coeffs_C, pred_C, resid_C, r2_C, ssr_C, sst_C, n_C, k_C = res_C
print(f"Model C (conductor + d_geom + log(omega)):                 R^2={r2_C:.4f}, SSR={ssr_C:.4f}, coeffs={[round(c,3) for c in coeffs_C]}")

# Model D: d_geom + log(omega) only (no conductor; for parsimony comparison)
X_D = [[log_d[i], log_om[i]] for i in range(len(active))]
res_D = multi_ols(X_D, log_B)
coeffs_D, _, _, r2_D, ssr_D, sst_D, n_D, k_D = res_D
print(f"Model D (d_geom + log(omega), no conductor):               R^2={r2_D:.4f}, SSR={ssr_D:.4f}, coeffs={[round(c,3) for c in coeffs_D]}")

# Model E: d_geom * log(omega) interaction (for form-function-rotation hypothesis)
X_E = [[log_d[i], log_om[i], log_d[i] * log_om[i], ind_mH[i], ind_plasma[i]] for i in range(len(active))]
res_E = multi_ols(X_E, log_B)
if res_E is not None:
    coeffs_E, _, _, r2_E, ssr_E, sst_E, n_E, k_E = res_E
    print(f"Model E (cond + d_geom + log(om) + d*om interact):         R^2={r2_E:.4f}, SSR={ssr_E:.4f}, coeffs={[round(c,3) for c in coeffs_E]}")
else:
    print("Model E: singular (insufficient degrees of freedom)")
    coeffs_E, r2_E, ssr_E = None, float("nan"), float("nan")


# --- §4. F-tests for added rotation-rate ---
print("\n=== F-TESTS (added predictor significance) ===")

# Model B -> Model C: added log(omega) given conductor + d_geom
n = len(active)
df_C = n - (k_C + 1)
F_om_added = f_test_added(ssr_C, ssr_B, df_C, 1)
print(f"Added log(omega) to (conductor + d_geom): F={F_om_added:.3f}, df=({1},{df_C})")
print(f"  Critical F at p<0.05 df=(1,{df_C}): {'19.0 (df=1,1)' if df_C==1 else '18.5 (df=1,2)' if df_C==2 else 'see Fisher table'}")

# Model A -> Model B: added d_geom (replicate Spike #143 AXIS 3 v2)
df_B = n - (k_B + 1)
F_d_added = f_test_added(ssr_B, ssr_A, df_B, 1)
print(f"Added d_geom to (conductor only):         F={F_d_added:.3f}, df=({1},{df_B})  (Spike #143 replication)")

# Improvement from adding rotation
delta_r2_C_B = r2_C - r2_B
print(f"\nR^2 improvement adding log(omega) on top of (conductor + d_geom): +{delta_r2_C_B:.4f}")


# --- §5. Iron-only stratified test (Spike #143 AXIS 2 found r=0.89 for iron) ---
iron_active = [b for b in active if b["conductor"] == "iron"]
print(f"\n=== IRON-ONLY STRATIFIED (n={len(iron_active)}) ===")
log_d_iron = [b["log_d_geom"] for b in iron_active]
log_om_iron = [b["log_omega_mag"] for b in iron_active]
log_B_iron = [b["log_B"] for b in iron_active]
for b in iron_active:
    print(f"  {b['body']:10s}  log_d_geom={b['log_d_geom']:7.3f}  log_omega={b['log_omega_mag']:7.3f}  log_B={b['log_B']:7.3f}")

if len(iron_active) >= 3:
    r_iron_d = pearson(log_d_iron, log_B_iron)
    r_iron_om = pearson(log_om_iron, log_B_iron)
    print(f"Iron-only Pearson r(log_d_geom, log_B): {r_iron_d:.4f}  (Spike #143 reported 0.890)")
    print(f"Iron-only Pearson r(log_omega, log_B):  {r_iron_om:.4f}")
    # Two-predictor model on iron subset (only 3 bodies; just-identified)
    X_iron = [[log_d_iron[i], log_om_iron[i]] for i in range(len(iron_active))]
    res_iron = multi_ols(X_iron, log_B_iron)
    if res_iron is not None:
        co_iron, _, _, r2_iron, ssr_iron, *_ = res_iron
        print(f"Iron 2-predictor (d_geom + omega) coefficients: {[round(c,3) for c in co_iron]}, R^2={r2_iron:.4f}")
    else:
        co_iron, r2_iron = None, float("nan")
else:
    co_iron, r2_iron, r_iron_d, r_iron_om = None, float("nan"), float("nan"), float("nan")


# --- §6. Including Venus (null-detection upper-bound) ---
# Test: does Venus FIT the rotation-rate-modulated framework? Venus rotates retrograde
# 243d (slowest large body) and has null field. Hypothesis: low rotation + no convection
# = no field even though d_geom matches Earth. Already known qualitatively; check fit.
active_plus_venus = [b for b in bodies if math.isnan(b["field_loss_Ga"])]  # includes Venus
print(f"\n=== ACTIVE-DYNAMO + VENUS (n={len(active_plus_venus)}) ===")
log_d_v = [b["log_d_geom"] for b in active_plus_venus]
log_om_v = [b["log_omega_mag"] for b in active_plus_venus]
log_B_v = [b["log_B"] for b in active_plus_venus]
ind_conv_v = [1.0 if b["convection"] else 0.0 for b in active_plus_venus]
ind_mH_v = [1.0 if b["conductor"] == "metallic_H" else 0.0 for b in active_plus_venus]
ind_plasma_v = [1.0 if b["conductor"] == "plasma" else 0.0 for b in active_plus_venus]
for b in active_plus_venus:
    conv = "yes" if b["convection"] else "no"
    print(f"  {b['body']:10s}  log_d_geom={b['log_d_geom']:7.3f}  log_omega={b['log_omega_mag']:7.3f}  log_B={b['log_B']:7.3f}  conv={conv}")
# Including convection indicator
X_F = [[log_d_v[i], log_om_v[i], ind_conv_v[i], ind_mH_v[i], ind_plasma_v[i]] for i in range(len(active_plus_venus))]
res_F = multi_ols(X_F, log_B_v)
if res_F is not None:
    coeffs_F, pred_F, resid_F, r2_F, ssr_F, sst_F, n_F, k_F = res_F
    print(f"\nFull model F (d_geom + log_om + convection + conductor): R^2={r2_F:.4f}, SSR={ssr_F:.4f}")
    names = ["intercept", "log_d_geom", "log_omega", "convection", "metallic_H", "plasma"]
    for name, c in zip(names, coeffs_F):
        print(f"  {name:14s}: {c:+.4f}")
    print(f"\nResiduals:")
    for b, r in zip(active_plus_venus, resid_F):
        print(f"  {b['body']:10s}: residual = {r:+.4f}  (observed - predicted)")
else:
    coeffs_F, r2_F, ssr_F = None, float("nan"), float("nan")


# --- §7. Save findings NDJSON ---
findings = {
    "date": "2026-05-19",
    "spike": "#163",
    "kind": "rotation_rate_covariate_analysis",
    "active_dynamo_subset_n": len(active),
    "active_dynamo_bodies": [b["body"] for b in active],
    "iron_only_n": len(iron_active),
    "iron_only_bodies": [b["body"] for b in iron_active],
    "univariate_pearson": {
        "log_d_geom_vs_log_B": r_d_B,
        "log_omega_vs_log_B": r_om_B,
    },
    "model_R2": {
        "model_0_null": 0.0,
        "model_A_conductor": r2_A,
        "model_B_conductor_plus_d_geom": r2_B,
        "model_C_conductor_plus_d_geom_plus_log_omega": r2_C,
        "model_D_d_geom_plus_log_omega_no_conductor": r2_D,
        "model_E_with_interaction": r2_E,
    },
    "model_SSR": {
        "model_A_conductor": ssr_A,
        "model_B_conductor_plus_d_geom": ssr_B,
        "model_C_conductor_plus_d_geom_plus_log_omega": ssr_C,
        "model_D_d_geom_plus_log_omega_no_conductor": ssr_D,
    },
    "f_test_added_log_omega_to_B": F_om_added,
    "f_test_added_d_geom_to_A": F_d_added,
    "r2_improvement_C_over_B": delta_r2_C_B,
    "model_C_coeffs": {
        "intercept": coeffs_C[0],
        "log_d_geom": coeffs_C[1],
        "log_omega": coeffs_C[2],
        "metallic_H": coeffs_C[3],
        "plasma": coeffs_C[4],
    },
    "iron_only_pearson_log_d_log_B": r_iron_d,
    "iron_only_pearson_log_omega_log_B": r_iron_om,
    "iron_only_2pred_R2": r2_iron,
    "iron_only_coeffs": [round(c, 4) for c in co_iron] if co_iron else None,
    "rotation_periods_d_used": {b["body"]: b["rotation_period_d"] for b in bodies},
    "verdict_added_rotation_significance": "see F-test (df small; effect size primary)",
    "model_F_with_venus_R2": r2_F,
    "model_F_with_venus_coeffs": dict(zip(
        ["intercept", "log_d_geom", "log_omega", "convection", "metallic_H", "plasma"],
        [round(c, 4) for c in coeffs_F]
    )) if coeffs_F else None,
}
findings_path = base / "spike163_records_2026-05-19.ndjson"
with findings_path.open("w", encoding="utf-8") as f:
    f.write(json.dumps(findings) + "\n")
print(f"\nWrote findings to {findings_path}")

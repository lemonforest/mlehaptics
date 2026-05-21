"""Spike #168 — Galactic-scale metallicity-BTFR residual test (LSGF discriminating axis).

Tests Spike #153 Sub-task C recommendation: at galactic scale, does stellar metallicity
function as an algebraically-orthogonal 4th-axis covariate to baryonic mass in the
Baryonic Tully-Fisher Relation (BTFR) / Radial Acceleration Relation (RAR)?

Hypothesis: per [[user_stance_gauge_shadow_components_push_pull_shear_bodies_gravity_is_projection]]:
- Metal-rich galaxies (high stellar metallicity) → enhanced gauge-shadow signature in RAR
- Per [[user_stance_form_function_rotation_is_a_c_m_composition]]: metallicity as
  content-determined shift parameter analogous to planetary rotation rate

Apply Spike #163 methodology (rotation-rate as 4th-axis covariate at planetary substrate)
at galactic substrate with metallicity as the substrate-natural form-function parameter.

Tuning A 440 Hz:
- Math doesn't lie: numbers reported as-found
- Strict-spec: no metaphor; metallicity = stellar [M/H] (Tremonti et al. 2004 calibration)
- 14-class A-N vocabulary intact; no class promotion
- Algebra-not-magnitude: effect-size + (cautious) F-tests; underpower flagged
- Trauma-informed defensive scope: galactic astrophysics framing only
- PDF-verified citations: LMS 2016 (1512.04543, 1606.09251); MLS 2016 (1609.05917);
  Brouwer 2017 (1612.03034); Verlinde 2016 (1611.02269); Tremonti 2004 (astro-ph/0405537)

Methodology source: Spike #163 [docs/srmech/notes/spike163_rotation_rate_covariate.py]
Spike #153 recommendation: galactic-scale metallicity stratification is the proper
discriminating test (Earth-scale was honest-null at 10^27 OOM below detectability).

DATA: representative galaxy roster constructed from published SPARC sample statistics
(LMS 2016 1606.09251 N=175) + mass-metallicity relation (Tremonti 2004 astro-ph/0405537).
Per [[reference_autonomous_validation_tos_landscape]] — arXiv-PDF-cite-by-ref discipline;
no proprietary data extraction.

The Tremonti 2004 stellar-mass metallicity relation (12+log(O/H) vs log M_star):
- Steep slope from log M_star = 8.5 to 10.5
- Flattens (asymptote) above 10.5 (saturation regime)
- Intrinsic scatter ~0.1 dex
- Implies: high-mass galaxies are metal-saturated; low-mass are metal-poor

The BTFR slope ~4 (LMS 2016): M_baryon vs V_flat^4 -> if metallicity is structural
covariate, residuals in BTFR after baryonic-mass-only fit should correlate with
metallicity orthogonal axis.
"""

import json
import math
from pathlib import Path

# CODATA 2018 constants
G_NEWTON = 6.67430e-11
C_LIGHT = 2.99792458e8
H_HUBBLE_SI = 67.4 * 1000.0 / (3.0857e22)  # H_0 ~ 67.4 km/s/Mpc -> SI

# Tremonti 2004 fit (asymptote + powerlaw)
# 12 + log(O/H) ~ 8.83 + 0.020 log(M_star) at high M (saturation)
# Schema below uses dimensionless [M/H] = log(Z/Z_sun)
# Approximation: [M/H] ~ -1.5 at log M_star = 8.5; ~ +0.0 at log M_star = 11.0
# (covers steep regime + saturation per Tremonti Fig 1)

def tremonti_metallicity(log_M_star):
    """Tremonti et al. 2004 (astro-ph/0405537) M-Z relation [M/H] dex.
    Returns stellar [M/H] in dex; saturates at +0.0 above log M = 11.0.

    Schema: piecewise smooth model matching Tremonti Fig 1:
    - At log M = 8.5 -> [M/H] ~ -1.5
    - At log M = 9.5 -> [M/H] ~ -0.6
    - At log M = 10.5 -> [M/H] ~ -0.1
    - At log M = 11.0+ -> [M/H] -> 0.0 (asymptote / saturation)

    Per [[user_stance_asymptotic_dof_sidesteps_infinity]] — saturation at high M
    is consistent with Class K bounded approach.
    """
    if log_M_star >= 11.0:
        return 0.0
    if log_M_star >= 10.5:
        # Saturation regime: gentle slope
        return -0.1 + (log_M_star - 10.5) * 0.2
    if log_M_star >= 8.5:
        # Steep regime: slope ~0.7 dex per dex
        return -1.5 + (log_M_star - 8.5) * 0.7
    # Extrapolation below 8.5 (dwarf regime)
    return -1.5 - (8.5 - log_M_star) * 0.5


# --- §0. Representative SPARC-style galaxy roster ---
# Built from LMS 2016 (1606.09251) Table 1 published sample statistics +
# Tremonti M-Z relation. Each entry is a representative (log_M_baryon, V_flat) bin
# spanning the SPARC sample range (M_b = 1e7 to 1e12 M_sun, V_flat = 20 to 300 km/s).
#
# 12 representative galaxies chosen to span the SPARC dynamical range + cover
# both regimes of the Tremonti M-Z relation (steep dwarf regime + saturation regime).
#
# Galaxy archetypes (representative; cite-by-ref to LMS 2016 sample distribution):
# - Dwarf irregulars (e.g., DDO, IC) - low mass, low V_flat, metal-poor
# - Disk spirals (e.g., NGC 3198) - intermediate
# - High-mass spirals (e.g., NGC 2841, UGC 2885) - massive, fast, metal-rich
# - Low-surface-brightness (LSB) galaxies - extended, metal-poor at fixed mass
# - High-surface-brightness (HSB) spirals - metal-saturated

galaxies = [
    # name, log_M_baryon (M_sun), V_flat (km/s), gas_fraction, surface_brightness_class
    ("DDO_154", 8.5,  47.0, 0.85, "LSB"),
    ("NGC_3741", 8.7,  50.0, 0.75, "LSB"),
    ("IC_2574", 9.0,  77.0, 0.65, "LSB"),
    ("NGC_3109", 9.2,  67.0, 0.70, "LSB"),
    ("NGC_2403", 9.8,  131.0, 0.30, "HSB"),
    ("NGC_3198", 10.3, 150.0, 0.25, "HSB"),
    ("UGC_5005", 10.0, 100.0, 0.50, "LSB"),  # LSB at moderate mass
    ("NGC_6946", 10.6, 180.0, 0.20, "HSB"),
    ("NGC_5055", 10.8, 200.0, 0.15, "HSB"),
    ("NGC_2841", 11.0, 280.0, 0.08, "HSB"),
    ("UGC_2885", 11.3, 300.0, 0.06, "HSB"),
    ("UGC_128",  10.4, 130.0, 0.45, "LSB"),  # LSB at high mass (Malin-1-type)
]

# Augment with derived properties
roster = []
for name, log_M_b, V_flat, f_gas, sb_class in galaxies:
    # Stellar mass: M_star = (1 - f_gas) * M_baryon
    log_M_star = log_M_b + math.log10(max(1.0 - f_gas, 1e-6))
    # Tremonti [M/H]
    M_over_H = tremonti_metallicity(log_M_star)
    # Apply LSB systematic offset: LSB galaxies are metal-poor at fixed M_star
    # (cite-by-ref: Liang et al. 2007 SDSS; LSB ~ 0.3 dex more metal-poor)
    if sb_class == "LSB":
        M_over_H -= 0.3
    # Observed acceleration scale: g_obs ~ V_flat^2 / R_disk
    # Use generic disk scaling R_disk ~ 4 kpc * (M_star / 5e10)^0.3 (Mo+98 cite-by-ref)
    R_disk_kpc = 4.0 * (10**log_M_star / 5e10)**0.3
    R_disk_m = R_disk_kpc * 3.0857e19  # m
    V_flat_m = V_flat * 1000.0  # m/s
    g_obs = V_flat_m**2 / R_disk_m  # m/s^2
    # Predicted baryonic acceleration: g_bar = G*M_baryon / R_disk^2
    M_baryon_kg = 10**log_M_b * 1.989e30
    g_bar = G_NEWTON * M_baryon_kg / R_disk_m**2  # m/s^2
    # RAR residual: log(g_obs / g_bar) — proxy for "dark-acceleration excess"
    log_rar_residual = math.log10(g_obs / g_bar)
    # d_geom-equivalent at galactic scale: r_s / R_disk
    r_s = 2.0 * G_NEWTON * M_baryon_kg / C_LIGHT**2
    d_geom_galactic = r_s / R_disk_m
    # log10 versions for regression
    entry = {
        "galaxy": name,
        "log_M_baryon": log_M_b,
        "log_M_star": log_M_star,
        "V_flat_kms": V_flat,
        "f_gas": f_gas,
        "sb_class": sb_class,
        "M_over_H": M_over_H,
        "R_disk_kpc": R_disk_kpc,
        "g_obs_ms2": g_obs,
        "g_bar_ms2": g_bar,
        "log_g_obs": math.log10(g_obs),
        "log_g_bar": math.log10(g_bar),
        "log_rar_residual": log_rar_residual,
        "d_geom_galactic": d_geom_galactic,
        "log_d_geom": math.log10(d_geom_galactic),
        "log_V_flat": math.log10(V_flat),
    }
    roster.append(entry)

# Write augmented roster
base = Path(__file__).parent
roster_path = base / "spike168_btfr_metallicity_roster.ndjson"
with roster_path.open("w", encoding="utf-8") as f:
    for r in roster:
        f.write(json.dumps(r) + "\n")
print(f"Wrote roster: {roster_path}")
print()

# Print roster table
print(f"{'Galaxy':12s} {'logM_b':>7s} {'V_flat':>7s} {'f_gas':>5s} {'SB':>3s} {'[M/H]':>6s} {'log g_obs':>10s} {'log g_bar':>10s} {'log_rar_res':>12s}")
print("-" * 90)
for r in roster:
    print(f"{r['galaxy']:12s} {r['log_M_baryon']:7.2f} {r['V_flat_kms']:7.1f} {r['f_gas']:5.2f} {r['sb_class']:>3s} "
          f"{r['M_over_H']:6.2f} {r['log_g_obs']:10.3f} {r['log_g_bar']:10.3f} {r['log_rar_residual']:12.3f}")
print()


# --- §1. Statistical utilities (stdlib only; Spike #163 methodology) ---

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
    """Multivariate OLS via Gauss elimination (Spike #163 pattern). Adds intercept."""
    n = len(y)
    k = len(X[0])
    A = [[1.0] + list(row) for row in X]
    p = k + 1
    AtA = [[0.0] * p for _ in range(p)]
    Aty = [0.0] * p
    for i in range(n):
        for r in range(p):
            for c in range(p):
                AtA[r][c] += A[i][r] * A[i][c]
            Aty[r] += A[i][r] * y[i]
    M = [row[:] + [Aty[i]] for i, row in enumerate(AtA)]
    for col in range(p):
        piv = col
        for r in range(col + 1, p):
            if abs(M[r][col]) > abs(M[piv][col]):
                piv = r
        M[col], M[piv] = M[piv], M[col]
        if abs(M[col][col]) < 1e-15:
            return None
        for r in range(p):
            if r != col and abs(M[r][col]) > 1e-15:
                fac = M[r][col] / M[col][col]
                for c in range(col, p + 1):
                    M[r][c] -= fac * M[col][c]
    coeffs = [M[r][p] / M[r][r] for r in range(p)]
    pred = [sum(c * v for c, v in zip(coeffs, row)) for row in A]
    resids = [y_i - yh for y_i, yh in zip(y, pred)]
    my = sum(y) / n
    ss_tot = sum((y_i - my) ** 2 for y_i in y)
    ss_res = sum(r * r for r in resids)
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    return coeffs, pred, resids, r2, ss_res, ss_tot, n, k

def f_test_added(ss_res_full, ss_res_red, df_full, df_added):
    """F-statistic for added variables: F = ((SSR_red - SSR_full) / df_added) / (SSR_full / df_full)."""
    if df_full <= 0 or ss_res_full <= 0:
        return float("nan")
    numer = (ss_res_red - ss_res_full) / df_added
    denom = ss_res_full / df_full
    if denom == 0:
        return float("inf")
    return numer / denom


# --- §2. The 9 effect-size tests (Spike #163 pattern) ---

n = len(roster)
log_M_b = [r["log_M_baryon"] for r in roster]
log_M_star = [r["log_M_star"] for r in roster]
log_V = [r["log_V_flat"] for r in roster]
M_over_H = [r["M_over_H"] for r in roster]
log_g_obs = [r["log_g_obs"] for r in roster]
log_g_bar = [r["log_g_bar"] for r in roster]
log_rar_res = [r["log_rar_residual"] for r in roster]
log_d_geom = [r["log_d_geom"] for r in roster]

records = []

# Test 1: BTFR replication: log V_flat vs log M_baryon (canonical LMS 2016 slope ~4)
slope_btfr, intercept_btfr, r2_btfr, _, _ = linreg(log_V, log_M_b)
records.append({
    "test": "T1_BTFR_replication",
    "x": "log_V_flat",
    "y": "log_M_baryon",
    "n": n,
    "slope": slope_btfr,
    "intercept": intercept_btfr,
    "r2": r2_btfr,
    "pearson": pearson(log_V, log_M_b),
    "lms_2016_expected_slope": 4.0,
    "interpretation": "BTFR slope; expected ~4 per LMS 2016 1512.04543"
})

# Test 2: Univariate metallicity vs RAR-residual (the spike's central question)
r_met_rar = pearson(M_over_H, log_rar_res)
slope_met_rar, _, r2_met_rar, _, _ = linreg(M_over_H, log_rar_res)
records.append({
    "test": "T2_metallicity_vs_RAR_residual",
    "x": "M_over_H",
    "y": "log_rar_residual",
    "n": n,
    "pearson": r_met_rar,
    "slope": slope_met_rar,
    "r2": r2_met_rar,
    "interpretation": "metallicity-driven RAR excess; framework prediction (direction A): high [M/H] -> high residual"
})

# Test 3: Orthogonality of metallicity to baryonic mass (independence check)
r_met_mass = pearson(M_over_H, log_M_b)
records.append({
    "test": "T3_orthogonality_metallicity_vs_M_baryon",
    "x": "M_over_H",
    "y": "log_M_baryon",
    "n": n,
    "pearson": r_met_mass,
    "r2": r_met_mass ** 2,
    "interpretation": "Tremonti M-Z relation: metallicity TRACKS mass; for true 4th-axis orthogonality, need to look at RESIDUALS after M_star-control"
})

# Test 4: Metallicity-residual after M_star control (true 4th-axis test)
# Fit M_over_H ~ log_M_star, take residuals
slope_mhms, int_mhms, _, _, _ = linreg(log_M_star, M_over_H)
M_over_H_resid = [M_over_H[i] - (int_mhms + slope_mhms * log_M_star[i]) for i in range(n)]
r_resmet_rar = pearson(M_over_H_resid, log_rar_res)
records.append({
    "test": "T4_metallicity_residual_vs_RAR_residual",
    "x": "M_over_H_residual_after_Mstar_control",
    "y": "log_rar_residual",
    "n": n,
    "pearson": r_resmet_rar,
    "interpretation": "Metallicity excursion FROM Tremonti relation correlates with RAR residual? (this is the LSB-vs-HSB distinguishing test per [[user_stance_form_function_rotation_is_a_c_m_composition]])"
})

# Test 5: Surface-brightness class effect (LSB vs HSB)
lsb_rar = [log_rar_res[i] for i in range(n) if roster[i]["sb_class"] == "LSB"]
hsb_rar = [log_rar_res[i] for i in range(n) if roster[i]["sb_class"] == "HSB"]
mean_lsb = sum(lsb_rar) / len(lsb_rar)
mean_hsb = sum(hsb_rar) / len(hsb_rar)
records.append({
    "test": "T5_LSB_vs_HSB_RAR_residual_split",
    "n_LSB": len(lsb_rar),
    "n_HSB": len(hsb_rar),
    "mean_log_rar_LSB": mean_lsb,
    "mean_log_rar_HSB": mean_hsb,
    "split_dex": mean_lsb - mean_hsb,
    "interpretation": "LSB galaxies should show enhanced RAR residual per canonical MOND/DM literature (low surface density -> deep MOND regime)"
})

# Test 6: Multivariate fit log_g_obs ~ log_g_bar + M_over_H (canonical RAR + metallicity)
X6 = [[log_g_bar[i], M_over_H[i]] for i in range(n)]
res6 = multi_ols(X6, log_g_obs)
if res6 is not None:
    coeffs6, _, _, r2_6, ss_res_6, ss_tot_6, _, k6 = res6
    # Reduced model: just log_g_bar
    X6r = [[log_g_bar[i]] for i in range(n)]
    res6r = multi_ols(X6r, log_g_obs)
    coeffs6r, _, _, r2_6r, ss_res_6r, _, _, k6r = res6r
    df_full6 = n - (k6 + 1)
    df_added6 = 1
    F6 = f_test_added(ss_res_6, ss_res_6r, df_full6, df_added6)
    records.append({
        "test": "T6_multivariate_metallicity_4th_axis",
        "predictors": ["log_g_bar", "M_over_H"],
        "n": n,
        "k_full": k6,
        "k_reduced": k6r,
        "df_full": df_full6,
        "intercept": coeffs6[0],
        "coef_log_g_bar": coeffs6[1],
        "coef_M_over_H": coeffs6[2],
        "r2_full": r2_6,
        "r2_reduced_log_g_bar_only": r2_6r,
        "delta_r2": r2_6 - r2_6r,
        "F_added_M_over_H": F6,
        "interpretation": "F-test for added metallicity covariate over canonical RAR; effect-size delta_r2 primary"
    })

# Test 7: Multivariate with M_baryon + metallicity (orthogonality test)
X7 = [[log_M_b[i], M_over_H[i]] for i in range(n)]
res7 = multi_ols(X7, log_V)
if res7 is not None:
    coeffs7, _, _, r2_7, ss_res_7, _, _, _ = res7
    X7r = [[log_M_b[i]] for i in range(n)]
    res7r = multi_ols(X7r, log_V)
    coeffs7r, _, _, r2_7r, ss_res_7r, _, _, _ = res7r
    df_full7 = n - 3
    F7 = f_test_added(ss_res_7, ss_res_7r, df_full7, 1)
    records.append({
        "test": "T7_BTFR_plus_metallicity_4th_axis",
        "model": "log_V_flat ~ log_M_baryon + M_over_H",
        "n": n,
        "intercept": coeffs7[0],
        "coef_log_M_baryon": coeffs7[1],
        "coef_M_over_H": coeffs7[2],
        "r2_full": r2_7,
        "r2_reduced": r2_7r,
        "delta_r2": r2_7 - r2_7r,
        "F_added": F7,
        "interpretation": "Does metallicity carry orthogonal information beyond baryonic-mass-only BTFR fit?"
    })

# Test 8: Interaction (metallicity x mass product) — per form-function-rotation algebra
prod_met_mass = [M_over_H[i] * log_M_b[i] for i in range(n)]
r_prod_rar = pearson(prod_met_mass, log_rar_res)
records.append({
    "test": "T8_interaction_metallicity_x_mass_vs_RAR",
    "x": "M_over_H * log_M_baryon",
    "y": "log_rar_residual",
    "n": n,
    "pearson": r_prod_rar,
    "interpretation": "Form-function-rotation A o C o M predicts multiplicative coupling per Spike #163 iron-only finding"
})

# Test 9: Class-K asymptotic-DOF signature (saturation at high mass)
# Test whether RAR-residual correlates with how close mass is to Class-K saturation
# Use log_d_geom_galactic vs log_rar_residual
r_dgeom_rar = pearson(log_d_geom, log_rar_res)
slope_dgeom_rar, _, r2_dgeom_rar, _, _ = linreg(log_d_geom, log_rar_res)
records.append({
    "test": "T9_d_geom_galactic_vs_RAR_residual",
    "x": "log_d_geom_galactic",
    "y": "log_rar_residual",
    "n": n,
    "pearson": r_dgeom_rar,
    "slope": slope_dgeom_rar,
    "r2": r2_dgeom_rar,
    "interpretation": "Galactic-scale d_geom vs RAR residual; tests substrate-coupling magnitude"
})

# Print test results
print("=" * 100)
print("§2. Nine effect-size tests")
print("=" * 100)
for rec in records:
    print(f"\n{rec['test']}")
    for k, v in rec.items():
        if k == "test":
            continue
        if isinstance(v, float):
            print(f"  {k:40s} = {v:+.4f}")
        else:
            print(f"  {k:40s} = {v}")


# --- §3. Both-direction analysis per [[feedback_always_check_both_directions_including_time]] ---

print()
print("=" * 100)
print("§3. Both-direction analysis")
print("=" * 100)

# Direction A: high-metallicity -> LSGF-residual-positive (enhanced gauge content)
high_met = [r for r in roster if r["M_over_H"] > -0.5]
low_met = [r for r in roster if r["M_over_H"] <= -0.5]
high_mean_rar = sum(r["log_rar_residual"] for r in high_met) / len(high_met)
low_mean_rar = sum(r["log_rar_residual"] for r in low_met) / len(low_met)
dirA_split = high_mean_rar - low_mean_rar

# Direction B: low-metallicity -> LSGF-residual-null OR enhanced (form-function-rotation-without-metallicity)
# Operationalize: do low-metallicity galaxies show enhanced (more positive) RAR residual?
# Both predictions need to be tested

direction_record = {
    "test": "B1_both_direction_metallicity_split",
    "n_high_met": len(high_met),
    "n_low_met": len(low_met),
    "mean_log_rar_high_met": high_mean_rar,
    "mean_log_rar_low_met": low_mean_rar,
    "split_high_minus_low": dirA_split,
    "direction_A_prediction": "high_met -> enhanced_RAR_residual (positive split)",
    "direction_B_prediction": "low_met -> enhanced_RAR_residual (negative split)",
    "observed_direction": "A_supported" if dirA_split > 0.05 else ("B_supported" if dirA_split < -0.05 else "NULL_neither")
}
records.append(direction_record)
print(f"\nB1_both_direction_metallicity_split")
for k, v in direction_record.items():
    if k == "test":
        continue
    print(f"  {k:40s} = {v}")


# --- §4. Cross-substrate comparison with Spike #163 ---

print()
print("=" * 100)
print("§4. Cross-substrate comparison with Spike #163")
print("=" * 100)

cross_substrate = {
    "test": "C1_cross_substrate_form_function_rotation",
    "planetary_substrate_spike_163": {
        "form_function_parameter": "rotation_rate (Omega)",
        "primary_observable": "log_B_dipole",
        "covariate_axis": "d_geom",
        "iron_only_pearson_r_FF_obs": 0.929,
        "iron_only_orthogonality": 0.087,
        "delta_r2": 0.052
    },
    "galactic_substrate_spike_168": {
        "form_function_parameter": "stellar_metallicity ([M/H])",
        "primary_observable": "log_rar_residual",
        "covariate_axis": "log_M_baryon",
        "univariate_pearson_r_FF_obs": pearson(M_over_H, log_rar_res),
        "orthogonality_to_baryonic": pearson(M_over_H_resid, log_M_b),
        "delta_r2": records[5]["delta_r2"] if len(records) > 5 and "delta_r2" in records[5] else None
    },
    "interpretation": (
        "Test whether galactic [M/H] is form-function-rotation analog at galactic substrate. "
        "Spike #163 found iron-only |r|=0.929 (Omega vs B); here we test [M/H] vs RAR-residual. "
        "Per [[user_stance_form_function_rotation_is_a_c_m_composition]] A o C o M composition."
    )
}
records.append(cross_substrate)
print(f"\n{cross_substrate['test']}")
print(f"  planetary (Spike #163):")
for k, v in cross_substrate["planetary_substrate_spike_163"].items():
    print(f"    {k:36s} = {v}")
print(f"  galactic (Spike #168):")
for k, v in cross_substrate["galactic_substrate_spike_168"].items():
    if isinstance(v, float):
        print(f"    {k:36s} = {v:+.4f}")
    else:
        print(f"    {k:36s} = {v}")


# --- §5. Class-K asymptotic-DOF signature at high-mass saturation ---

print()
print("=" * 100)
print("§5. Class-K asymptotic-DOF signature (high-mass metallicity saturation)")
print("=" * 100)

# Identify saturation regime: log_M_star >= 10.5 per Tremonti 2004
saturated = [r for r in roster if r["log_M_star"] >= 10.5]
unsaturated = [r for r in roster if r["log_M_star"] < 10.5]
sat_record = {
    "test": "K1_class_K_asymptotic_saturation",
    "n_saturated_log_M_star_ge_10p5": len(saturated),
    "n_unsaturated": len(unsaturated),
    "mean_M_over_H_saturated": (sum(r["M_over_H"] for r in saturated) / len(saturated)) if saturated else None,
    "mean_M_over_H_unsaturated": (sum(r["M_over_H"] for r in unsaturated) / len(unsaturated)) if unsaturated else None,
    "interpretation": (
        "Tremonti 2004 reports M-Z relation flattens above log M_star = 10.5 — this IS the "
        "Class K asymptotic-DOF signature per [[user_stance_asymptotic_dof_sidesteps_infinity]]. "
        "Bounded approach to [M/H] ~ 0 ceiling without ever exceeding it."
    )
}
records.append(sat_record)
print(f"\n{sat_record['test']}")
for k, v in sat_record.items():
    if k == "test":
        continue
    if isinstance(v, float):
        print(f"  {k:40s} = {v:+.4f}")
    else:
        print(f"  {k:40s} = {v}")

# Add gas-fraction analysis: gas_fraction is upstream of metallicity (cite-by-ref:
# closed-box chemical evolution model). For form-function-rotation to operate
# at galactic substrate, gas_fraction should appear orthogonal-ish to baryonic mass
f_gas_list = [r["f_gas"] for r in roster]
r_fgas_rar = pearson(f_gas_list, log_rar_res)
r_fgas_met = pearson(f_gas_list, M_over_H)
records.append({
    "test": "G1_gas_fraction_diagnostic",
    "pearson_f_gas_vs_log_rar": r_fgas_rar,
    "pearson_f_gas_vs_M_over_H": r_fgas_met,
    "interpretation": "Gas fraction is upstream proxy in chemical-evolution closed-box; if metallicity is real form-function parameter, this should track"
})


# --- §6. Write all records to NDJSON ---

out_records = base / "spike168_records_2026-05-19.ndjson"
with out_records.open("w", encoding="utf-8") as f:
    for rec in records:
        f.write(json.dumps(rec, default=str) + "\n")
print()
print(f"Wrote records: {out_records}")
print(f"Total records: {len(records)}")

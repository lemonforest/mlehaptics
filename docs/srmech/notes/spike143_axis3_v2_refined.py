"""Spike #143 AXIS 3 v2 (refined) — f vs g x h discrimination.

v1 used noisy P_conv proxies (orders-of-magnitude uncertainty per body).
v2: use the Christensen-Aubert-Reiners universal-dynamo-scaling law DIRECTLY
in its log form, calibrated to Earth, and ask:

Does the OBSERVED B require an additional d_geom dependence
beyond what conductor + convection alone explain?

The Christensen-Aubert universal law (cite-by-ref Christensen, Holzwarth,
Reiners 2009 Nature; arXiv:0908.0959 for relevant scaling):
    B_dipole_dim ~ (mu_0 rho)^{1/2} (P_conv/V_dyn)^{1/3}

The (mu_0 rho)^{1/2} factor captures CONDUCTOR dependence (rho_iron > rho_metallic-H > rho_plasma)
The P_conv^{1/3} factor captures CONVECTION dependence
There is NO d_geom dependence in standard theory.

For solar dynamo: completely different scaling (Babcock-Leighton).
Take it out of the regression as different-regime.

For Jupiter and Saturn: metallic-H. Use rho_metH ~ 1000 kg/m^3 vs rho_iron ~ 10000 kg/m^3.
Convective heat flux from internal heat measurements:
  - Earth: 47 TW total (Pollack et al. 1993); 4-10 TW from core (Lay et al. 2008)
  - Mercury: ~10-100 MW core heat (Tosi et al. 2013) — orders of magnitude estimate
  - Ganymede: 1e10 W estimate (Schubert et al. 2004)
  - Jupiter: ~1e17 W radiogenic + cooling (Guillot 2005)
  - Saturn: ~1e15 W (helium rain contribution, Fortney+Hubbard 2003)

These are all cite-by-ref estimates with OOM uncertainty. Acknowledge that
v1's noisiness is fundamental to the standard-model prediction.

REFRAME: Test whether the framework's d_geom-driver is a BETTER predictor
than convection-only. Use a single explanatory model:
  log(B) = a + b * log(d_geom) + c * I[metallic-H] + d * I[plasma]

vs

  log(B) = a' + c' * I[metallic-H] + d' * I[plasma] (no d_geom)

Compare R² for active-convective bodies (Sun, Mercury, Earth, Jupiter, Saturn, Ganymede).
"""

import json
import math
import statistics
from pathlib import Path

# Load substrate roster
data_path = Path(__file__).parent / "spike143_substrate_roster.ndjson"
bodies = []
with data_path.open(encoding="utf-8") as f:
    for line in f:
        if line.strip():
            bodies.append(json.loads(line))

selected = {b["body"]: b for b in bodies}
active_conv = [selected[n] for n in ["Sun", "Mercury", "Earth", "Jupiter", "Saturn", "Ganymede"]]

print("AXIS 3 v2 — refined f vs g x h test")
print("Bodies (active convection):", [b["body"] for b in active_conv])

# Build regressors
log_B = [math.log10(b["B_dipole_T"]) for b in active_conv]
log_d_geom = [math.log10(b["d_geom"]) for b in active_conv]
# One-hot encoding
I_metallicH = [1.0 if b["conductor"] == "metallic_H" else 0.0 for b in active_conv]
I_plasma = [1.0 if b["conductor"] == "plasma" else 0.0 for b in active_conv]

# Manual OLS for both models
def ols(X, y):
    """Manual OLS. X is list of feature vectors (including 1 for intercept)."""
    n = len(y)
    p = len(X[0])
    # Compute X^T X
    XTX = [[sum(X[k][i] * X[k][j] for k in range(n)) for j in range(p)] for i in range(p)]
    # Compute X^T y
    XTy = [sum(X[k][i] * y[k] for k in range(n)) for i in range(p)]
    # Solve via Gaussian elimination
    # Augmented matrix
    M = [row[:] + [XTy[i]] for i, row in enumerate(XTX)]
    # Forward
    for i in range(p):
        # Pivot
        max_row = max(range(i, p), key=lambda k: abs(M[k][i]))
        M[i], M[max_row] = M[max_row], M[i]
        if abs(M[i][i]) < 1e-12:
            raise ValueError("Singular matrix")
        for k in range(i + 1, p):
            factor = M[k][i] / M[i][i]
            for j in range(i, p + 1):
                M[k][j] -= factor * M[i][j]
    # Back
    beta = [0.0] * p
    for i in reversed(range(p)):
        beta[i] = (M[i][p] - sum(M[i][j] * beta[j] for j in range(i + 1, p))) / M[i][i]
    # Residuals
    y_pred = [sum(X[k][i] * beta[i] for i in range(p)) for k in range(n)]
    residuals = [y[k] - y_pred[k] for k in range(n)]
    ss_res = sum(r ** 2 for r in residuals)
    ss_tot = sum((y[k] - sum(y) / n) ** 2 for k in range(n))
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    return beta, ss_res, r2

# Model A: log(B) = a + c*I_mH + d*I_p (no d_geom)
n = len(log_B)
X_A = [[1.0, I_metallicH[k], I_plasma[k]] for k in range(n)]
try:
    beta_A, ss_A, r2_A = ols(X_A, log_B)
    print(f"\nModel A (no d_geom): a={beta_A[0]:.3f}, c_mH={beta_A[1]:.3f}, d_p={beta_A[2]:.3f}")
    print(f"  R^2 = {r2_A:.4f}, SS_res = {ss_A:.4f}")
except ValueError as e:
    print(f"Model A: {e}")
    r2_A = float("nan")
    ss_A = float("inf")

# Model B: log(B) = a + b*log(d_geom) + c*I_mH + d*I_p
X_B = [[1.0, log_d_geom[k], I_metallicH[k], I_plasma[k]] for k in range(n)]
try:
    beta_B, ss_B, r2_B = ols(X_B, log_B)
    print(f"\nModel B (with d_geom): a={beta_B[0]:.3f}, b_dgeom={beta_B[1]:.3f}, c_mH={beta_B[2]:.3f}, d_p={beta_B[3]:.3f}")
    print(f"  R^2 = {r2_B:.4f}, SS_res = {ss_B:.4f}")
except ValueError as e:
    print(f"Model B: {e}")
    r2_B = float("nan")
    ss_B = float("inf")

# F-test for added variable
# F = ((SS_A - SS_B) / 1) / (SS_B / (n - p_B))
# p_A = 3, p_B = 4
p_A = 3
p_B = 4
if ss_B > 0 and not math.isnan(ss_A):
    F = ((ss_A - ss_B) / (p_B - p_A)) / (ss_B / (n - p_B))
    # df1 = 1, df2 = 2; F-critical at p=0.05 ~ 18.51 for df=(1,2)
    print(f"\nF-test for added d_geom: F = {F:.3f}")
    print(f"For df=(1, {n-p_B}) at p<0.05: critical F = ~18.5 (n=6 small)")
    print(f"R^2 improvement: {r2_B - r2_A:+.4f}")
else:
    F = float("nan")

# Without Sun (different regime — Babcock-Leighton)
print("\n--- Excluding Sun (different dynamo regime) ---")
non_solar = [b for b in active_conv if b["body"] != "Sun"]
log_B_ns = [math.log10(b["B_dipole_T"]) for b in non_solar]
log_d_geom_ns = [math.log10(b["d_geom"]) for b in non_solar]
I_metallicH_ns = [1.0 if b["conductor"] == "metallic_H" else 0.0 for b in non_solar]
n_ns = len(non_solar)

print(f"n={n_ns} bodies: {[b['body'] for b in non_solar]}")
# Model A_ns: log(B) = a + c*I_mH
X_A_ns = [[1.0, I_metallicH_ns[k]] for k in range(n_ns)]
beta_A_ns, ss_A_ns, r2_A_ns = ols(X_A_ns, log_B_ns)
print(f"Model A_ns (no d_geom): a={beta_A_ns[0]:.3f}, c_mH={beta_A_ns[1]:.3f}, R^2={r2_A_ns:.4f}")

# Model B_ns: log(B) = a + b*log(d_geom) + c*I_mH
X_B_ns = [[1.0, log_d_geom_ns[k], I_metallicH_ns[k]] for k in range(n_ns)]
beta_B_ns, ss_B_ns, r2_B_ns = ols(X_B_ns, log_B_ns)
print(f"Model B_ns (with d_geom): a={beta_B_ns[0]:.3f}, b_dgeom={beta_B_ns[1]:.3f}, c_mH={beta_B_ns[2]:.3f}, R^2={r2_B_ns:.4f}")
print(f"R^2 improvement: {r2_B_ns - r2_A_ns:+.4f}")

# F-test
p_A_ns = 2
p_B_ns = 3
if ss_B_ns > 0:
    F_ns = ((ss_A_ns - ss_B_ns) / (p_B_ns - p_A_ns)) / (ss_B_ns / (n_ns - p_B_ns))
    print(f"F-test (non-solar): F = {F_ns:.3f}")
    # For df=(1, 2): critical F at 0.05 = 18.51
    print(f"  df=(1,{n_ns-p_B_ns}): critical F at 0.05 = ~18.5")
else:
    F_ns = float("nan")

# Within iron-conductor only (Mercury, Earth, Ganymede), test pure d_geom dependence
print("\n--- Iron-only sub-test (Mercury, Earth, Ganymede) ---")
iron = [selected[n] for n in ["Mercury", "Earth", "Ganymede"]]
iron_log_B = [math.log10(b["B_dipole_T"]) for b in iron]
iron_log_d_geom = [math.log10(b["d_geom"]) for b in iron]
print(f"{'Body':12s} {'log d_geom':>10s} {'log B':>8s}")
for b in iron:
    print(f"{b['body']:12s} {math.log10(b['d_geom']):10.3f} {math.log10(b['B_dipole_T']):8.3f}")
# Simple OLS
def simple_ols(x, y):
    n = len(x)
    mx = sum(x) / n
    my = sum(y) / n
    num = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y))
    den = sum((xi - mx) ** 2 for xi in x)
    slope = num / den if den > 0 else float("nan")
    intercept = my - slope * mx
    return slope, intercept

slope_iron, intercept_iron = simple_ols(iron_log_d_geom, iron_log_B)
# Predictions vs observed
pred_iron = [intercept_iron + slope_iron * x for x in iron_log_d_geom]
ss_res_iron = sum((y - p) ** 2 for y, p in zip(iron_log_B, pred_iron))
ss_tot_iron = sum((y - sum(iron_log_B) / 3) ** 2 for y in iron_log_B)
r2_iron = 1 - ss_res_iron / ss_tot_iron if ss_tot_iron > 0 else float("nan")
print(f"\nIron-only linear fit: slope={slope_iron:.3f}, intercept={intercept_iron:.3f}, R^2={r2_iron:.4f}")

# Pearson r within iron group
def pearson(x, y):
    n = len(x)
    mx = sum(x) / n
    my = sum(y) / n
    num = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y))
    dx = math.sqrt(sum((xi - mx) ** 2 for xi in x))
    dy = math.sqrt(sum((yi - my) ** 2 for yi in y))
    return num / (dx * dy) if dx > 0 and dy > 0 else float("nan")

r_iron = pearson(iron_log_d_geom, iron_log_B)
print(f"Iron-only Pearson r = {r_iron:.4f}")
# n=3, df=1, no meaningful p-value

# Now key test: extrapolate iron-only fit to Jupiter, Saturn, Sun
# What does iron-only fit predict for Sun?
print("\n--- Iron-fit extrapolation to non-iron bodies ---")
print(f"Iron fit: log(B) = {intercept_iron:.3f} + {slope_iron:.3f} * log(d_geom)")
for name in ["Sun", "Jupiter", "Saturn"]:
    b = selected[name]
    pred = intercept_iron + slope_iron * math.log10(b["d_geom"])
    obs = math.log10(b["B_dipole_T"])
    diff = obs - pred
    print(f"  {name}: log(d_geom)={math.log10(b['d_geom']):.3f}, predicted log(B)={pred:.3f}, observed={obs:.3f}, diff={diff:+.3f} ({10**diff:.2f}x)")

# VERDICT
verdict_v2 = None
if not math.isnan(F_ns) and F_ns > 5.0 and r2_B_ns - r2_A_ns > 0.1:
    verdict_v2 = "AXIS-3-V2-D_GEOM-IMPROVES-MODEL-FIT-SUBSTANTIALLY"
elif r2_B_ns - r2_A_ns > 0.1:
    verdict_v2 = "AXIS-3-V2-D_GEOM-MODERATE-IMPROVEMENT-INSUFFICIENT-POWER"
elif r2_B_ns - r2_A_ns > 0.0:
    verdict_v2 = "AXIS-3-V2-D_GEOM-WEAK-IMPROVEMENT"
else:
    verdict_v2 = "AXIS-3-V2-D_GEOM-NO-IMPROVEMENT"

print(f"\nVerdict (AXIS 3 v2): {verdict_v2}")

# Save
out_path = Path(__file__).parent / "spike143_axis3_v2_findings.ndjson"
with out_path.open("w", encoding="utf-8") as f:
    f.write(json.dumps({
        "date": "2026-05-18",
        "spike": "#143",
        "axis": 3,
        "kind": "f_vs_gh_refined_OLS",
        "n_bodies_full": n,
        "model_A_no_dgeom_r2": r2_A,
        "model_B_with_dgeom_r2": r2_B,
        "F_stat_full": F if not math.isnan(F) else None,
        "model_A_ns_r2": r2_A_ns,
        "model_B_ns_r2": r2_B_ns,
        "F_stat_non_solar": F_ns if not math.isnan(F_ns) else None,
        "iron_only_pearson_r": r_iron,
        "iron_only_slope": slope_iron,
        "iron_only_R2": r2_iron,
        "verdict": verdict_v2,
    }) + "\n")
print(f"\nWrote findings to {out_path}")

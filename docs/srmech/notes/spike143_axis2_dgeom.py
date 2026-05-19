"""Spike #143 AXIS 2 — d_geom monotone dependence of field strength.

Hypothesis: framework predicts log(|B_dipole|) monotone in log(d_geom)
after controlling for conductor + convection.

Standard geodynamo theory makes NO d_geom prediction. Standard dynamo
scaling laws (Christensen-Aubert 2006; Olson-Christensen 2006) predict
B ~ (ρμ)^{1/2} (F_conv)^{1/3} (rotation-rate dependence) — no d_geom term.

Test: linear regression on log-log scale with conductor + convection
as one-hot controls.

n = 6 bodies with active fields (where standard scaling laws apply meaningfully):
Sun, Mercury, Earth, Jupiter, Saturn, Ganymede (active dynamos)
Plus null cases: Venus (no convection, has iron), Moon/Mars/Vesta (lost field).
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

# Filter to bodies with active dynamos (currently measurable field above noise floor)
# Exclude bodies with field_loss_Ga or no convection — those are not currently field-active
active_bodies = [
    b for b in bodies
    if math.isnan(b["field_loss_Ga"])  # not lost
    and b["convection"]  # has convection
    and b["B_dipole_T"] > 1e-8  # measurable field above null upper limits
]
print(f"AXIS 2 — d_geom dependence regression")
print(f"Active-dynamo bodies: {len(active_bodies)}")
print(f"Bodies: {[b['body'] for b in active_bodies]}")

# Prepare arrays
log_d_geom = [math.log10(b["d_geom"]) for b in active_bodies]
log_B = [math.log10(b["B_dipole_T"]) for b in active_bodies]

print("\n--- log10 values ---")
print(f"{'Body':12s} {'log10(d_geom)':>15s} {'log10(B_T)':>12s} {'Conductor':>12s}")
for b, ld, lb in zip(active_bodies, log_d_geom, log_B):
    print(f"{b['body']:12s} {ld:15.3f} {lb:12.3f} {b['conductor']:>12s}")

# Pearson correlation
def pearson(x, y):
    n = len(x)
    mx = sum(x) / n
    my = sum(y) / n
    num = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y))
    dx = math.sqrt(sum((xi - mx) ** 2 for xi in x))
    dy = math.sqrt(sum((yi - my) ** 2 for yi in y))
    return num / (dx * dy) if dx > 0 and dy > 0 else float("nan")

r_pearson = pearson(log_d_geom, log_B)
n = len(log_d_geom)
# t-stat for correlation: t = r * sqrt((n-2)/(1-r²))
if abs(r_pearson) < 1.0:
    t_corr = r_pearson * math.sqrt((n - 2) / (1 - r_pearson ** 2))
else:
    t_corr = float("inf")

print(f"\n--- Pearson correlation (uncontrolled) ---")
print(f"r = {r_pearson:.4f}")
print(f"t-statistic (n={n}, df={n-2}) = {t_corr:.3f}")
# For df=4: t at p<0.05 two-tailed = 2.78; one-tailed = 2.13
# For df=5: 2.57 / 2.02
crit_2tail = 2.57 if n - 2 == 5 else 2.78
crit_1tail = 2.02 if n - 2 == 5 else 2.13
print(f"Critical t (n-2={n-2}): two-tailed 0.05 = {crit_2tail}, one-tailed = {crit_1tail}")

if abs(t_corr) > crit_2tail:
    sig = "p<0.05 two-tailed"
elif abs(t_corr) > crit_1tail:
    sig = "p<0.05 one-tailed"
else:
    sig = "n.s."
print(f"Uncontrolled correlation significance: {sig}")

# Simple linear regression slope: log(B) = a + b * log(d_geom)
mx = sum(log_d_geom) / n
my = sum(log_B) / n
num = sum((x - mx) * (y - my) for x, y in zip(log_d_geom, log_B))
den = sum((x - mx) ** 2 for x in log_d_geom)
slope = num / den
intercept = my - slope * mx
# Residuals + R²
residuals = [y - (intercept + slope * x) for x, y in zip(log_d_geom, log_B)]
ss_res = sum(r ** 2 for r in residuals)
ss_tot = sum((y - my) ** 2 for y in log_B)
r2 = 1 - ss_res / ss_tot

print(f"\n--- Simple linear regression log(B) ~ log(d_geom) ---")
print(f"slope = {slope:.4f}")
print(f"intercept = {intercept:.4f}")
print(f"R² = {r2:.4f}")

# Standard error of slope
n_eff = n
sx = math.sqrt(den / (n_eff - 1))
se_slope = math.sqrt(ss_res / (n_eff - 2)) / (sx * math.sqrt(n_eff - 1))
t_slope = slope / se_slope if se_slope > 0 else float("inf")
print(f"SE(slope) = {se_slope:.4f}")
print(f"t(slope) = {t_slope:.3f}")

# Now stratify by conductor to see if correlation holds within conductor groups
# But with only 6 bodies + 3 conductor types, the cell counts are tiny.
print("\n--- Conductor stratification ---")
by_cond = {}
for b, ld, lb in zip(active_bodies, log_d_geom, log_B):
    by_cond.setdefault(b["conductor"], []).append((b["body"], ld, lb))
for cond, items in by_cond.items():
    print(f"  {cond}: {len(items)} bodies")
    for it in items:
        print(f"    {it[0]}: log_d_geom={it[1]:.3f}, log_B={it[2]:.3f}")

# Within-conductor analysis: iron group has Mercury + Earth + Ganymede
iron_bodies = [b for b in active_bodies if b["conductor"] == "iron"]
if len(iron_bodies) >= 2:
    iron_ld = [math.log10(b["d_geom"]) for b in iron_bodies]
    iron_lb = [math.log10(b["B_dipole_T"]) for b in iron_bodies]
    r_iron = pearson(iron_ld, iron_lb)
    print(f"\n  Iron group (n={len(iron_bodies)}): pearson r = {r_iron:.4f}")
    print(f"  Bodies: {[(b['body'], math.log10(b['d_geom']), math.log10(b['B_dipole_T'])) for b in iron_bodies]}")

# Within metallic-H: Jupiter + Saturn
mh_bodies = [b for b in active_bodies if b["conductor"] == "metallic_H"]
if len(mh_bodies) >= 2:
    mh_ld = [math.log10(b["d_geom"]) for b in mh_bodies]
    mh_lb = [math.log10(b["B_dipole_T"]) for b in mh_bodies]
    # Only 2 points - slope only
    slope_mh = (mh_lb[1] - mh_lb[0]) / (mh_ld[1] - mh_ld[0])
    print(f"\n  Metallic-H group (n=2): two-point slope = {slope_mh:.4f}")

# VERDICT
if abs(t_corr) > crit_2tail and slope > 0:
    verdict = "AXIS-2-D_GEOM-MONOTONE-CONFIRMED-AT-P<0.05"
elif abs(t_corr) > crit_1tail and slope > 0:
    verdict = "AXIS-2-D_GEOM-WEAK-MONOTONE-AT-P<0.05-ONE-TAIL"
elif slope > 0 and r_pearson > 0.5:
    verdict = "AXIS-2-D_GEOM-EFFECT-SIZE-MODERATE-BUT-N-LIMITED"
else:
    verdict = "AXIS-2-D_GEOM-NO-CORRELATION"

print(f"\nVerdict (AXIS 2, uncontrolled): {verdict}")

# Conductor-controlled: visual inspection of within-conductor monotonicity
# Iron: 3 bodies — Mercury (d_geom=2e-10, B=3e-7), Earth (1.4e-9, 4.5e-5), Ganymede (8.4e-11, 7.2e-7)
# Earth > Ganymede ≈ Mercury in B; Earth's d_geom is HIGHER than Ganymede; Mercury's d_geom > Ganymede
# Ordering by d_geom: Ganymede (smallest) < Mercury < Earth (largest among iron)
# Ordering by B: Mercury ≈ Ganymede ≪ Earth
# Monotone if Mercury (d_geom=2e-10) and Earth (1.4e-9) follow log-log up; Ganymede deviates
# Let's compute explicitly
if len(iron_bodies) >= 2:
    iron_sorted = sorted(iron_bodies, key=lambda b: b["d_geom"])
    print(f"\n  Iron bodies sorted by d_geom:")
    for b in iron_sorted:
        print(f"    {b['body']}: d_geom={b['d_geom']:.3e}, B={b['B_dipole_T']:.3e}")
    # Monotone in B?
    iron_B = [b["B_dipole_T"] for b in iron_sorted]
    monotone_iron = all(iron_B[i+1] >= iron_B[i] for i in range(len(iron_B)-1))
    print(f"  Iron B monotone-increasing with d_geom? {monotone_iron}")

# Save findings
out_path = Path(__file__).parent / "spike143_axis2_findings.ndjson"
with out_path.open("w", encoding="utf-8") as f:
    f.write(json.dumps({
        "date": "2026-05-18",
        "spike": "#143",
        "axis": 2,
        "kind": "d_geom_dependence_regression",
        "n_bodies": n,
        "bodies": [b["body"] for b in active_bodies],
        "log_d_geom": log_d_geom,
        "log_B": log_B,
        "pearson_r": r_pearson,
        "pearson_t": t_corr,
        "slope": slope,
        "intercept": intercept,
        "r_squared": r2,
        "se_slope": se_slope,
        "t_slope": t_slope,
        "verdict": verdict,
        "verdict_significance": sig,
    }) + "\n")
print(f"\nWrote findings to {out_path}")

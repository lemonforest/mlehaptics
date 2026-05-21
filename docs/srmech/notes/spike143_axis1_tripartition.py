"""Spike #143 AXIS 1 — Tripartition-shadow multipole test.

Hypothesis: tripartition-shadow framework predicts preference for k=3 in
multipole-moment ratios across magnetically-active bodies.

Per [[project_space_gauge_time_framework]] k=3 partition: 3D_s + 7D_g + 1D_t.
Tripartition-shadow signature would be octupole (M3) preferentially preserved
relative to quadrupole (M2) and decuple (M4 not measured here).

Test: across bodies with measured multipoles, compute
- (M3/M1) — octupole-to-dipole strength ratio
- (M2/M1) — quadrupole-to-dipole
- (M3/M2) — octupole-to-quadrupole (key ratio for tripartition test)

H0 (null): no k-preference; M2/M1 and M3/M1 statistically equal.
H1 (framework): M3 systematically stronger than M2 (M3/M2 > 1).

Note: this is a 5-body sample; statistical power limited.
Report effect sizes (means + std), not just p-values.
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

# Filter to bodies with measured multipoles
bodies_with_multipoles = [
    b for b in bodies
    if not math.isnan(b["M_quadrupole_norm"]) and not math.isnan(b["M_octupole_norm"])
]

print(f"AXIS 1 — Tripartition-shadow multipole test")
print(f"Bodies with measured multipoles: {len(bodies_with_multipoles)} of {len(bodies)}")
print(f"Bodies: {[b['body'] for b in bodies_with_multipoles]}")

# Compute ratios
ratios_M2_M1 = []
ratios_M3_M1 = []
ratios_M3_M2 = []

for b in bodies_with_multipoles:
    m1 = b["M_dipole_norm"]  # always 1.0 (normalised)
    m2 = b["M_quadrupole_norm"]
    m3 = b["M_octupole_norm"]
    ratios_M2_M1.append(m2 / m1)
    ratios_M3_M1.append(m3 / m1)
    ratios_M3_M2.append(m3 / m2)

print("\n--- Per-body ratios ---")
print(f"{'Body':12s} {'M2/M1':>8s} {'M3/M1':>8s} {'M3/M2':>8s}")
for b, r2, r3, r32 in zip(bodies_with_multipoles, ratios_M2_M1, ratios_M3_M1, ratios_M3_M2):
    print(f"{b['body']:12s} {r2:8.3f} {r3:8.3f} {r32:8.3f}")

# Aggregate statistics
mean_M2_M1 = statistics.mean(ratios_M2_M1)
mean_M3_M1 = statistics.mean(ratios_M3_M1)
mean_M3_M2 = statistics.mean(ratios_M3_M2)

sd_M2_M1 = statistics.stdev(ratios_M2_M1)
sd_M3_M1 = statistics.stdev(ratios_M3_M1)
sd_M3_M2 = statistics.stdev(ratios_M3_M2)

print(f"\n--- Aggregate ratios ---")
print(f"Mean M2/M1 = {mean_M2_M1:.3f} ± {sd_M2_M1:.3f}")
print(f"Mean M3/M1 = {mean_M3_M1:.3f} ± {sd_M3_M1:.3f}")
print(f"Mean M3/M2 = {mean_M3_M2:.3f} ± {sd_M3_M2:.3f}")

# Paired test: is M3/M1 > M2/M1?
# Within-body paired difference (M3/M1 - M2/M1)
paired_diff = [r3 - r2 for r2, r3 in zip(ratios_M2_M1, ratios_M3_M1)]
mean_diff = statistics.mean(paired_diff)
sd_diff = statistics.stdev(paired_diff)
# t-statistic for paired
n = len(paired_diff)
t_stat = mean_diff / (sd_diff / math.sqrt(n))
print(f"\n--- Paired test: H0: M3/M1 = M2/M1 ---")
print(f"Paired diff (M3/M1 - M2/M1) per body: {[f'{d:+.3f}' for d in paired_diff]}")
print(f"Mean paired diff = {mean_diff:+.3f} ± {sd_diff:.3f}")
print(f"t-statistic (n={n}) = {t_stat:.3f}")
# n=5: critical t at p<0.05 two-tailed is 2.78 (df=4); one-tailed 2.13
# Approximate; small sample
print(f"For n={n}, df={n-1}: one-tailed p<0.05 requires |t|>2.13 (cite: Student-t critical)")
if t_stat > 2.13:
    verdict = "AXIS-1-TRIPARTITION-FAVORED-AT-1TAIL-P<0.05"
elif t_stat > 0:
    verdict = "AXIS-1-WEAK-K=3-PREFERENCE-NOT-SIGNIFICANT"
elif t_stat < 0:
    verdict = "AXIS-1-K=3-NOT-FAVORED-(M2-DOMINANT)"
else:
    verdict = "AXIS-1-NULL"

print(f"\nVerdict (AXIS 1): {verdict}")

# Also: count of bodies where M3 > M2
n_M3_dominant = sum(1 for r32 in ratios_M3_M2 if r32 > 1.0)
print(f"\nBodies with M3 > M2: {n_M3_dominant} of {n}")
print(f"Bodies with M3 < M2: {n - n_M3_dominant} of {n}")

# Per-body conductor-dependent analysis
print("\n--- Conductor stratification ---")
by_conductor = {}
for b, r32 in zip(bodies_with_multipoles, ratios_M3_M2):
    by_conductor.setdefault(b["conductor"], []).append((b["body"], r32))
for cond, items in by_conductor.items():
    print(f"  {cond}: {items}")

# Save findings
out_path = Path(__file__).parent / "spike143_axis1_findings.ndjson"
with out_path.open("w", encoding="utf-8") as f:
    f.write(json.dumps({
        "date": "2026-05-18",
        "spike": "#143",
        "axis": 1,
        "kind": "tripartition_shadow_multipole_test",
        "n_bodies": n,
        "bodies": [b["body"] for b in bodies_with_multipoles],
        "mean_M2_M1": mean_M2_M1,
        "sd_M2_M1": sd_M2_M1,
        "mean_M3_M1": mean_M3_M1,
        "sd_M3_M1": sd_M3_M1,
        "mean_M3_M2": mean_M3_M2,
        "sd_M3_M2": sd_M3_M2,
        "paired_mean_diff_M3M1_minus_M2M1": mean_diff,
        "paired_t_stat": t_stat,
        "n_M3_dominant": n_M3_dominant,
        "verdict": verdict,
    }) + "\n")
print(f"\nWrote findings to {out_path}")

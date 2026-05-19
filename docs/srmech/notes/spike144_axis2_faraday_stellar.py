"""
Spike #144 Axis 2 — Galactic Faraday rotation vs stellar density.

PREDICTION: Inter-stellar magnetic field IS the superposition of
stellar 7D_g ball boundaries. RM should correlate with stellar
density MORE than with H I column density or CO molecular gas.

DATA INPUTS (paper-extracted summary statistics; arXiv-sourced
per autonomous-validation TOS):

Oppermann et al. 2012 A&A 542:A93 (arXiv 1111.6186) — NVSS-derived
all-sky RM reconstruction via Wiener filter. Their Figure 3 +
Table 2 report mean |RM| by Galactic latitude bin.

The mean |RM| values in their latitude bins are:
  |b| < 5 deg:    mean |RM| ~ 65 rad/m^2 (with substantial scatter)
  5 < |b| < 10:   mean |RM| ~ 28 rad/m^2
  10 < |b| < 30:  mean |RM| ~ 14 rad/m^2
  |b| > 30:       mean |RM| ~ 7 rad/m^2

Stellar density proxy (visible-matter integrated column):
Gaia DR3 selection function for G < 18 in same bins. From the
all-sky integrated catalog (e.g. Bailer-Jones et al. 2021 AJ 161:147),
stellar density falls as approximately cosh(z/h)^{-2} with scale
height h ~ 300 pc (thin disk). Mean stellar density:
  |b| < 5:       ~7000 stars / sq.deg (G < 18)
  5 < |b| < 10:  ~3200 stars / sq.deg
  10 < |b| < 30: ~1400 stars / sq.deg
  |b| > 30:      ~500 stars / sq.deg

H I column density (HI4PI survey, Bekhti et al. 2016 A&A 594:A116):
  |b| < 5:       ~5.0e21 H atoms / cm^2 (high disk concentration)
  5 < |b| < 10:  ~2.0e21
  10 < |b| < 30: ~5.0e20
  |b| > 30:      ~1.5e20

CO molecular gas (Dame et al. 2001 ApJ 547:792):
  |b| < 5:       ~50 K km/s (W_CO, mean of inner Galaxy)
  5 < |b| < 10:  ~5 K km/s
  10 < |b| < 30: ~1 K km/s
  |b| > 30:      ~0.5 K km/s

Free-electron density (Cordes & Lazio NE2001 model integrated
column out to ~5 kpc, approximate Galactic average):
  |b| < 5:       ~70 cm^-3 pc
  5 < |b| < 10:  ~30 cm^-3 pc
  10 < |b| < 30: ~14 cm^-3 pc
  |b| > 30:      ~7 cm^-3 pc

NOTE: These values are paper-extracted summary statistics. The
analysis tests whether the framework's prediction holds at the
GROSS latitudinal scale; finer-grained pixel-level analysis would
require downloading the full healpix RM map, which would burst
out of spike timebox. The trend test is sufficient at this stage
because:
  - RM should track total integrated column-along-line-of-sight
    of (n_e * B_parallel) per the canonical RM formula
  - If B_parallel comes from STELLAR 7D_g ball superposition,
    then RM should track stellar density not n_e * H_neutral
  - If B_parallel comes from MHD turbulence + neutral gas, then
    RM should track n_e * H I (the canonical model)
"""

import json
import math
from pathlib import Path

# Pre-registered latitude bins
BINS = [
    {"name": "low_lat", "b_range_deg": "|b|<5",   "abs_RM_radm2": 65.0,
     "stellar_density_per_sqdeg": 7000.0, "HI_cm2": 5.0e21, "CO_Kkms": 50.0, "ne_pc_cm3": 70.0},
    {"name": "mid_disk", "b_range_deg": "5<|b|<10", "abs_RM_radm2": 28.0,
     "stellar_density_per_sqdeg": 3200.0, "HI_cm2": 2.0e21, "CO_Kkms": 5.0, "ne_pc_cm3": 30.0},
    {"name": "mid_lat", "b_range_deg": "10<|b|<30", "abs_RM_radm2": 14.0,
     "stellar_density_per_sqdeg": 1400.0, "HI_cm2": 5.0e20, "CO_Kkms": 1.0, "ne_pc_cm3": 14.0},
    {"name": "high_lat", "b_range_deg": "|b|>30",  "abs_RM_radm2": 7.0,
     "stellar_density_per_sqdeg": 500.0,  "HI_cm2": 1.5e20, "CO_Kkms": 0.5, "ne_pc_cm3": 7.0},
]


def pearson_r(xs, ys):
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    sx = sum((x - mx) ** 2 for x in xs)
    sy = sum((y - my) ** 2 for y in ys)
    sxy = sum((xs[i] - mx) * (ys[i] - my) for i in range(n))
    if sx == 0 or sy == 0:
        return 0.0
    return sxy / math.sqrt(sx * sy)


def t_stat_for_r(r, n):
    if abs(r) >= 1.0:
        return float("inf") if r > 0 else float("-inf")
    return r * math.sqrt(n - 2) / math.sqrt(1 - r * r)


# Pearson correlations (log-log to control for orders-of-magnitude)
log_RM = [math.log10(b["abs_RM_radm2"]) for b in BINS]
log_stellar = [math.log10(b["stellar_density_per_sqdeg"]) for b in BINS]
log_HI = [math.log10(b["HI_cm2"]) for b in BINS]
log_CO = [math.log10(b["CO_Kkms"]) for b in BINS]
log_ne = [math.log10(b["ne_pc_cm3"]) for b in BINS]

r_stellar = pearson_r(log_RM, log_stellar)
r_HI = pearson_r(log_RM, log_HI)
r_CO = pearson_r(log_RM, log_CO)
r_ne = pearson_r(log_RM, log_ne)
r_neHI = pearson_r(log_RM, [math.log10(b["HI_cm2"] * b["ne_pc_cm3"]) for b in BINS])

# Standard model predicts RM ~ ne * B_parallel * L; if B_parallel is
# correlated with H I or CO (turbulent ISM source), then ne * HI should
# correlate better than stellar alone.
records = [
    {"kind": "axis2_bin", **b} for b in BINS
]
records.append({
    "kind": "axis2_correlation_results",
    "n_bins": len(BINS),
    "pearson_r_RM_vs_stellar_density": r_stellar,
    "pearson_r_RM_vs_HI": r_HI,
    "pearson_r_RM_vs_CO": r_CO,
    "pearson_r_RM_vs_ne": r_ne,
    "pearson_r_RM_vs_ne_x_HI": r_neHI,
    "t_RM_vs_stellar": t_stat_for_r(r_stellar, len(BINS)),
    "t_RM_vs_HI": t_stat_for_r(r_HI, len(BINS)),
})

# Diagnostic: which proxy correlates BEST with RM?
proxy_results = {
    "stellar_density": r_stellar,
    "HI": r_HI,
    "CO": r_CO,
    "ne_NE2001": r_ne,
    "ne_x_HI": r_neHI,
}
best_proxy = max(proxy_results.items(), key=lambda kv: kv[1])
records.append({
    "kind": "axis2_best_proxy",
    "proxy_correlations": proxy_results,
    "best_proxy": best_proxy[0],
    "best_r": best_proxy[1],
})

# Framework prediction: stellar density should correlate BETTER than H I.
# Falsification condition: H I (or ne*HI) correlates better, framework
# loses.
framework_wins = r_stellar > r_HI and r_stellar > r_CO
stellar_beats_neHI = r_stellar > r_neHI
all_correlations_strong = all(p > 0.95 for p in proxy_results.values())

# Verdict
if all_correlations_strong:
    # All proxies are degenerate at this latitude scale (all drop ~10x)
    # — can't distinguish them at n=4 lat bins
    verdict = "AXIS-2-DEGENERATE-ALL-PROXIES-CORRELATED-AT-LAT-SCALE"
elif framework_wins and stellar_beats_neHI:
    verdict = "AXIS-2-STELLAR-BEATS-CANONICAL-FRAMEWORK-CONSISTENT"
elif framework_wins:
    verdict = "AXIS-2-STELLAR-BEATS-HI-BUT-NEHI-TIES-WEAK-POSITIVE"
else:
    verdict = "AXIS-2-FRAMEWORK-LOSES-CANONICAL-MODEL-FITS-BETTER"

records.append({
    "kind": "axis2_verdict",
    "framework_prediction": "RM correlates better with stellar density than H I / CO",
    "framework_wins_vs_HI": r_stellar > r_HI,
    "framework_wins_vs_CO": r_stellar > r_CO,
    "framework_wins_vs_ne_HI": stellar_beats_neHI,
    "all_proxies_degenerate": all_correlations_strong,
    "verdict": verdict,
    "n_bins": len(BINS),
    "n_bins_caveat": "n=4 at gross latitude scale; degenerate correlation expected. Stronger test requires pixel-level RM map analysis (out of spike timebox).",
    "source_refs": "Oppermann+2012 A&A 542:A93 RM; Bailer-Jones+2021 AJ 161:147 Gaia DR3; Bekhti+2016 A&A 594:A116 HI4PI; Dame+2001 ApJ 547:792 CO; Cordes & Lazio NE2001",
})

out_path = Path(__file__).resolve().parent / "spike144_axis2_findings.ndjson"
with out_path.open("w", encoding="utf-8") as f:
    for rec in records:
        f.write(json.dumps(rec) + "\n")

print("AXIS 2 — Faraday rotation vs stellar density")
print(f"  r(RM, stellar_density): {r_stellar:.4f}")
print(f"  r(RM, H I):             {r_HI:.4f}")
print(f"  r(RM, CO):              {r_CO:.4f}")
print(f"  r(RM, n_e NE2001):      {r_ne:.4f}")
print(f"  r(RM, n_e * H I):       {r_neHI:.4f}")
print(f"  Best proxy:             {best_proxy[0]} (r = {best_proxy[1]:.4f})")
print(f"  All correlations > 0.95: {all_correlations_strong}")
print(f"  Verdict: {verdict}")
print(f"  Output:  spike144_axis2_findings.ndjson")

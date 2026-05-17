"""Spike #42 — quantitative Cauchy-form cascade test on PDG branching ratios.

Tests whether particle-physics decay branching ratios instantiate the
Cauchy-form kernel `c_k = epsilon^k / k` per Spike #41 Kepler-shape-universal
sharpening, with epsilon driven by the QED radiative-correction factor
(predicted alpha/pi = 2.3e-3 for one-loop QED vertex addition).

Substrates tested:
  1. pi0 decay (cleanest hierarchical branching — pure QED radiative cascade)
  2. muon decay (W-mediated, radiative-corrections subdominant)
  3. neutron beta decay (W-mediated, radiative-corrections subdominant)

PDG values: 2024 PDG (pdg.lbl.gov), open canonical.

Methodology: Spike #41 unbiased Cauchy fit — fit on log|c_k * k| (not log|c_k|)
to remove the systematic underestimate-of-epsilon bias documented in Spike #41
Anomaly 2.

Output: NDJSON records per substrate per channel, plus fit summary.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Tuple

OUT_DIR = Path(__file__).resolve().parent

# ---- Physical constants (CODATA / PDG, open canonical) ----
ALPHA_EM = 7.2973525693e-3          # fine-structure constant
ALPHA_OVER_PI = ALPHA_EM / math.pi   # one-loop QED vertex factor (predicted epsilon)
G_F_GEV2 = 1.1663787e-5              # Fermi constant (GeV^-2)
ALPHA_S_MZ = 0.1179                  # strong coupling at M_Z

# ---- PDG branching ratios (open canonical, pdg.lbl.gov, 2024 PDG) ----
# All BRs as fractions of total decay width.

PI0_BRANCHES = {
    "channel_0_2gamma":       0.98823,   # pi0 -> 2 gamma (leading)
    "channel_1_dalitz":       0.01174,   # pi0 -> e+ e- gamma (Dalitz)
    "channel_2_double_dalitz": 3.34e-5,   # pi0 -> e+ e- e+ e- (double Dalitz)
    "channel_3_anomalous":    6.46e-8,   # pi0 -> e+ e-
}

# Muon decay: dominated by mu -> e nu_e nu_mu ; radiative is mu -> e nu nu gamma.
# Mu radiative BR (with E_gamma > 10 MeV): 1.4e-2 per PDG.
# Mu -> e gamma (LFV, SM-suppressed) experimental upper limit: < 4.2e-13 (MEG II).
# We tabulate hierarchically by adding one gamma-vertex per channel:
MUON_BRANCHES = {
    "channel_0_e_nunubar":     1.0 - 1.4e-2 - 4.2e-13,  # leading e nu nubar
    "channel_1_e_nunubar_g":   1.4e-2,                  # radiative (one extra gamma)
    "channel_2_e_g_LFV":       4.2e-13,                 # LFV ceiling (placeholder)
}

# Neutron beta decay: n -> p e- nu_e (essentially 100%).
# Radiative beta decay n -> p e- nu_e gamma: BR ~ 3.13e-3 (Cooper et al. 2010, PDG).
# Inner bremsstrahlung from beta (gamma emission with E_gamma > some MeV cutoff).
# Channel 2 here is bound-state beta decay (rare).
NEUTRON_BRANCHES = {
    "channel_0_p_e_nubar":         1.0 - 3.13e-3,
    "channel_1_p_e_nubar_g":       3.13e-3,    # radiative
    # neutron has no observed double-radiative; we don't fabricate a level here
}


@dataclass
class CauchyFitResult:
    substrate: str
    n_channels: int
    epsilons: List[float]
    c_ratios: List[float]
    epsilon_predicted: float
    epsilon_fit_biased: float       # log|c_k| slope
    epsilon_fit_unbiased: float     # log|c_k * k| slope (Spike #41 methodology)
    r2_biased: float
    r2_unbiased: float
    cauchy_residual_max: float      # max |log(c_k_observed) - log(c_k_predicted)|
    notes: str


def cauchy_fit(c_ratios: List[float]) -> Tuple[float, float, float, float]:
    """Fit c_k = epsilon^k / k. Returns (eps_biased, eps_unbiased, r2_biased, r2_unbiased).

    Biased fit:    log|c_k|      = k log eps - log k    (under-estimates eps)
    Unbiased fit:  log|c_k * k|  = k log eps           (Spike #41 Anomaly 2 fix)
    """
    if not c_ratios:
        return float("nan"), float("nan"), float("nan"), float("nan")
    k_vals = list(range(1, len(c_ratios) + 1))
    if any(c <= 0 for c in c_ratios):
        return float("nan"), float("nan"), float("nan"), float("nan")

    # Biased: regress log|c_k| on k
    log_c = [math.log(abs(c)) for c in c_ratios]
    eps_b, r2_b = _ols_one_var(k_vals, log_c)

    # Unbiased: regress log|c_k * k| on k -> slope = log eps directly
    log_ck = [math.log(abs(c) * k) for c, k in zip(c_ratios, k_vals)]
    eps_u, r2_u = _ols_one_var(k_vals, log_ck)

    return math.exp(eps_b), math.exp(eps_u), r2_b, r2_u


def _ols_one_var(x: List[int], y: List[float]) -> Tuple[float, float]:
    """Ordinary least squares y = slope * x + intercept; returns (slope, R^2)."""
    n = len(x)
    if n < 2:
        # With 1 point, slope = log_c1/1 = log_c1 if x_0=1. r2 = nan for 1-point.
        if n == 1:
            return y[0] / x[0], float("nan")
        return float("nan"), float("nan")
    mean_x = sum(x) / n
    mean_y = sum(y) / n
    sxx = sum((xi - mean_x) ** 2 for xi in x)
    sxy = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
    syy = sum((yi - mean_y) ** 2 for yi in y)
    if sxx == 0 or syy == 0:
        if sxx == 0:
            return float("nan"), float("nan")
        # syy=0 means y is constant; slope = 0; r^2 = 1 in OLS sense
        slope = sxy / sxx
        return slope, 1.0
    slope = sxy / sxx
    intercept = mean_y - slope * mean_x
    ss_res = sum((yi - (slope * xi + intercept)) ** 2 for xi, yi in zip(x, y))
    r2 = 1.0 - ss_res / syy
    return slope, r2


def compute_substrate(substrate: str, branches: dict, eps_predicted: float) -> CauchyFitResult:
    """Compute Cauchy fit + per-channel records for a substrate's branching ratios.

    Channel 0 is the leading channel (denominator); channels 1..N are successive
    additions of suppression factors.
    c_k = BR(channel_k) / BR(channel_0) for k = 1..N
    """
    channel_keys = sorted(branches.keys())  # channel_0..N preserves order
    br_values = [branches[k] for k in channel_keys]
    br_leading = br_values[0]

    c_ratios = []
    for k_idx, br in enumerate(br_values[1:], start=1):
        c_k = br / br_leading
        c_ratios.append(c_k)

    eps_biased, eps_unbiased, r2_b, r2_u = cauchy_fit(c_ratios)

    # Per-channel epsilon estimate from c_k = eps^k / k -> eps_k = (c_k * k)^(1/k)
    epsilons = []
    for k_idx, c_k in enumerate(c_ratios, start=1):
        eps_k = (c_k * k_idx) ** (1.0 / k_idx)
        epsilons.append(eps_k)

    # Residual: how close to Cauchy form is each c_k under predicted eps?
    residuals = []
    for k_idx, c_k in enumerate(c_ratios, start=1):
        c_predicted = (eps_predicted ** k_idx) / k_idx
        if c_k > 0 and c_predicted > 0:
            residuals.append(abs(math.log(c_k) - math.log(c_predicted)))
    cauchy_residual_max = max(residuals) if residuals else float("nan")

    notes = (
        "pi0: epsilon = alpha/pi predicted (one-loop QED vertex). "
        "muon: epsilon ~ alpha (full QED radiative, no /pi). "
        "neutron: only one sub-channel, so r2 ill-defined; report eps_1 only."
    )

    return CauchyFitResult(
        substrate=substrate,
        n_channels=len(c_ratios),
        epsilons=epsilons,
        c_ratios=c_ratios,
        epsilon_predicted=eps_predicted,
        epsilon_fit_biased=eps_biased,
        epsilon_fit_unbiased=eps_unbiased,
        r2_biased=r2_b,
        r2_unbiased=r2_u,
        cauchy_residual_max=cauchy_residual_max,
        notes=notes,
    )


def main():
    """Run Cauchy fit on three substrates, emit NDJSON records."""

    results = []

    # pi0: predicted epsilon = alpha/pi (one-loop QED vertex)
    results.append(compute_substrate("pi0", PI0_BRANCHES, ALPHA_OVER_PI))

    # muon: predicted epsilon ~ alpha (radiative correction; no extra /pi here
    # because radiative BR is alpha not alpha/pi factor compared to leading)
    results.append(compute_substrate("muon", MUON_BRANCHES, ALPHA_EM))

    # neutron: predicted epsilon ~ alpha (similar reasoning)
    results.append(compute_substrate("neutron", NEUTRON_BRANCHES, ALPHA_EM))

    # Print summary
    print("\n=== Spike #42 — Cauchy-form fit on PDG branching ratios ===\n")
    for r in results:
        print(f"\nSubstrate: {r.substrate}")
        print(f"  Channels analyzed: {r.n_channels}")
        print(f"  c_k ratios:    {[f'{c:.3e}' for c in r.c_ratios]}")
        print(f"  per-channel eps_k = (c_k * k)^(1/k):")
        for k_idx, eps in enumerate(r.epsilons, start=1):
            print(f"    k={k_idx}: eps_k = {eps:.4e}")
        print(f"  epsilon predicted (theory):  {r.epsilon_predicted:.4e}")
        print(f"  epsilon fit biased:           {r.epsilon_fit_biased:.4e}")
        print(f"  epsilon fit unbiased:         {r.epsilon_fit_unbiased:.4e}")
        print(f"  r^2 biased / unbiased:        {r.r2_biased:.4f} / {r.r2_unbiased:.4f}")
        print(f"  Cauchy residual max |log c_obs - log c_pred|: {r.cauchy_residual_max:.4f}")
        print(f"  Notes: {r.notes}")

    # Emit per-channel records
    records = []
    for r in results:
        # one record per substrate (summary)
        records.append({
            "kind": "cauchy_fit_summary",
            "substrate": r.substrate,
            "n_channels": r.n_channels,
            "epsilon_predicted": r.epsilon_predicted,
            "epsilon_fit_biased": r.epsilon_fit_biased,
            "epsilon_fit_unbiased": r.epsilon_fit_unbiased,
            "r2_biased": r.r2_biased,
            "r2_unbiased": r.r2_unbiased,
            "cauchy_residual_max": r.cauchy_residual_max,
            "notes": r.notes,
        })
        # one record per channel
        for k_idx, (c_k, eps_k) in enumerate(zip(r.c_ratios, r.epsilons), start=1):
            records.append({
                "kind": "channel_record",
                "substrate": r.substrate,
                "k": k_idx,
                "c_k_observed": c_k,
                "epsilon_k_per_channel": eps_k,
                "epsilon_predicted": r.epsilon_predicted,
                "c_k_predicted": (r.epsilon_predicted ** k_idx) / k_idx,
            })

    out_path = OUT_DIR / "spike_42_branching_ratio_records.ndjson"
    with open(out_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec) + "\n")
    print(f"\nEmitted {len(records)} records to {out_path}")


if __name__ == "__main__":
    main()

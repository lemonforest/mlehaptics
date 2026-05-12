"""
SM 12-fermion log-symmetric spike (2026-05-12).

RESEARCH SPIKE #6 — full SM fermion content in MFO-natural log-m² variable.

Spike #5 truncated to 9 charged fermions. That was a half-test. SM has
12 fermions per generation × {} = 12 total flavours including 3 neutrinos.

If MFO's field-primary ontology has any chiral structure (which the SM
empirically does — left-handed neutrinos but no right-handed neutrinos
in minimal SM), then the log-m² spectrum should reflect that. The
sharpest log-spectrum signature would be SYMMETRY around some scale c:

    For each charged fermion at log-m² = +x, a neutrino partner at
    log-m² = c - x (or symmetric pairing across some center).

This is the qualitative signature of the seesaw mechanism in physics:
m_ν,i × M_R ≈ m_D,i², which translates to:
    log(m_ν,i²) + log(M_R²) = 2 × log(m_D,i²)
i.e., the log-m² values pair across the M_R Majorana scale.

Benchmark neutrino masses (m_lightest free parameter):
  We test 3 benchmarks under Normal Ordering (NO):
    m_lightest = 0.001 eV  (near-degenerate possibility)
    m_lightest = 0.01 eV   (typical)
    m_lightest = 0.05 eV   (close to cosmology upper bound)

Tests:
  T1. Lepton-only log-symmetry: do (e, ν_e), (μ, ν_μ), (τ, ν_τ) pair
      symmetrically around a single center c?
  T2. Full 12-fermion log-symmetry: any natural pairing producing
      symmetric structure around a common center?
  T3. Best-fit center c and residuals; compare to null (random
      shuffling of the 12 values).

Reproduce: `python -X utf8 docs/srmech/notes/sm_12_fermion_log_symmetric_spike_script.py`
"""

import json
import numpy as np
from itertools import permutations
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RNG_SEED = 20260512
OUT_DIR = Path(__file__).parent
RESULTS_FILE = OUT_DIR / "sm-12-fermion-log-symmetric-per-test-2026-05-12.ndjson"

# ── SM masses (MeV; PDG 2024) ───────────────────────────────────────────

SM_MASSES_MEV = {
    "e": 0.511,  "u": 2.16,    "d": 4.67,
    "s": 93.4,   "μ": 105.66,
    "c": 1270.0, "τ": 1776.86,
    "b": 4180.0, "t": 172760.0,
}

# Neutrino oscillation constraints (eV²):
DELTA_M21_SQ_EV2 = 7.4e-5     # solar
DELTA_M31_SQ_EV2 = 2.5e-3     # atmospheric (NO)
EV_PER_MEV = 1e6


def neutrino_masses_eV(m_lightest_eV, ordering="NO"):
    """Compute 3 neutrino masses from m_lightest + oscillation constraints."""
    if ordering == "NO":
        m1 = m_lightest_eV
        m2 = np.sqrt(m1 ** 2 + DELTA_M21_SQ_EV2)
        m3 = np.sqrt(m1 ** 2 + DELTA_M31_SQ_EV2)
    elif ordering == "IO":
        m3 = m_lightest_eV
        m1 = np.sqrt(m3 ** 2 + DELTA_M31_SQ_EV2)
        m2 = np.sqrt(m1 ** 2 + DELTA_M21_SQ_EV2)
    return {"ν_e": m1, "ν_μ": m2, "ν_τ": m3}  # flavor labels (informal)


def full_12_fermion_log_m_sq(m_lightest_eV, ordering="NO"):
    """ln(m²/m_e²) for all 12 SM fermions, sorted by ln value."""
    m_e_eV = SM_MASSES_MEV["e"] * EV_PER_MEV
    log_msq = {}
    for name, mass_MeV in SM_MASSES_MEV.items():
        m_eV = mass_MeV * EV_PER_MEV
        log_msq[name] = 2 * np.log(m_eV / m_e_eV)
    nu_masses = neutrino_masses_eV(m_lightest_eV, ordering)
    for name, m_eV in nu_masses.items():
        log_msq[name] = 2 * np.log(m_eV / m_e_eV)
    return log_msq


# ── Pairing-based log-symmetry tests ────────────────────────────────────

def pairwise_symmetry_residual(pairs, log_msq, return_center=False):
    """
    Given pairs of fermion names, find the center c minimising
        Σ_pairs (log(m²_a) + log(m²_b) − 2c)²
    The optimum c is mean of pair midpoints. Return RMS residual.
    """
    midpoints = [0.5 * (log_msq[a] + log_msq[b]) for a, b in pairs]
    c_star = float(np.mean(midpoints))
    residuals = [m - c_star for m in midpoints]
    rms = float(np.sqrt(np.mean(np.square(residuals))))
    max_dev = float(np.max(np.abs(residuals)))
    if return_center:
        return rms, max_dev, c_star, residuals
    return rms


def null_pairing_residual(log_msq, n_trials=10000, rng=None):
    """
    Random pairings of all 12 values (6 pairs); compute RMS pair-midpoint deviation.
    """
    if rng is None:
        rng = np.random.default_rng(RNG_SEED)
    values = list(log_msq.values())
    n = len(values)
    rms_list = []
    for _ in range(n_trials):
        shuffled = rng.permutation(n)
        pairs = [(shuffled[2 * i], shuffled[2 * i + 1]) for i in range(n // 2)]
        midpts = [0.5 * (values[a] + values[b]) for a, b in pairs]
        c = float(np.mean(midpts))
        rms = float(np.sqrt(np.mean([(m - c) ** 2 for m in midpts])))
        rms_list.append(rms)
    return np.array(rms_list)


def lepton_sector_null(log_msq):
    """
    Proper null for T1: enumerate ALL 15 distinct pairings of the 6 lepton-sector
    fermions {e, μ, τ, ν_e, ν_μ, ν_τ} into 3 pairs, compute RMS for each.
    SM seesaw pairing (e↔ν_e, μ↔ν_μ, τ↔ν_τ) is one of these 15.
    """
    lepton_names = ["e", "μ", "τ", "ν_e", "ν_μ", "ν_τ"]
    lepton_dict = {n: log_msq[n] for n in lepton_names}

    def gen_3_pairings(remaining):
        if not remaining:
            yield []
            return
        first = remaining[0]
        for j in range(1, len(remaining)):
            pair = (first, remaining[j])
            rest = remaining[1:j] + remaining[j + 1:]
            for sub in gen_3_pairings(rest):
                yield [pair] + sub

    all_pairings = list(gen_3_pairings(lepton_names))
    rms_per_pairing = []
    for p in all_pairings:
        rms = pairwise_symmetry_residual(p, lepton_dict)
        rms_per_pairing.append((p, rms))
    return rms_per_pairing


# ── Main ────────────────────────────────────────────────────────────────

def main():
    rng = np.random.default_rng(RNG_SEED)
    records = []

    print("=== SM 12-fermion log-symmetric spike ===\n")

    benchmarks = [
        ("near-massless",  0.001, "NO"),
        ("typical",         0.01,  "NO"),
        ("near-cosmo",      0.05,  "NO"),
    ]

    # The lepton-flavor pairing — natural under seesaw-like mechanisms
    LEPTON_PAIRS = [("e", "ν_e"), ("μ", "ν_μ"), ("τ", "ν_τ")]

    for label, m_lightest, ordering in benchmarks:
        print(f"=== Benchmark: m_lightest = {m_lightest} eV ({ordering}) — '{label}' ===\n")

        log_msq = full_12_fermion_log_m_sq(m_lightest, ordering)
        sorted_log = sorted(log_msq.items(), key=lambda x: x[1])

        print(f"All 12 fermion log(m²/m_e²) values (sorted):")
        for name, v in sorted_log:
            print(f"  {name:>5s} : {v:8.3f}")

        total_span = sorted_log[-1][1] - sorted_log[0][1]
        print(f"\nTotal span: {total_span:.2f}")
        print()

        # T1: Lepton-only log-symmetry (under seesaw-style pairing)
        rms_lep, max_dev_lep, c_lep, resids_lep = pairwise_symmetry_residual(
            LEPTON_PAIRS, log_msq, return_center=True)
        print(f"T1: Lepton (charged ↔ neutrino) seesaw pairing")
        for (a, b), r in zip(LEPTON_PAIRS, resids_lep):
            midpt = 0.5 * (log_msq[a] + log_msq[b])
            print(f"     ({a:>3s}, {b:>4s})  midpoint = {midpt:8.3f}  "
                  f"dev from c = {r:+7.3f}")
        print(f"     Best-fit center c* = {c_lep:.3f}  (corresponds to ~"
              f"{np.exp(c_lep / 2) * SM_MASSES_MEV['e']:.2e} MeV)")
        print(f"     RMS residual = {rms_lep:.3f};  max dev = {max_dev_lep:.3f}")
        print()
        records.append({"test": "T1_lepton_seesaw_pairing",
                          "benchmark": label, "m_lightest_eV": m_lightest,
                          "ordering": ordering,
                          "pairs": [list(p) for p in LEPTON_PAIRS],
                          "center_c": c_lep,
                          "implied_pairing_scale_MeV": float(
                              np.exp(c_lep / 2) * SM_MASSES_MEV['e']),
                          "rms_residual": rms_lep,
                          "max_dev": max_dev_lep})

        # T2: Try best pairing across all 12 (search over allowed pairings)
        # Constraint: 12 values → 6 pairs. Full search over 12!/(2^6 × 6!) = 10395
        # pairings is feasible.
        all_names = [n for n, _ in sorted_log]
        # Brute search would be 10395; use sampling-based search instead
        # Use a heuristic: pair lightest with heaviest, etc., as a baseline
        log_vals = np.array([v for _, v in sorted_log])
        pair_baseline = [(all_names[i], all_names[11 - i]) for i in range(6)]
        rms_base, max_base, c_base, resids_base = pairwise_symmetry_residual(
            pair_baseline, log_msq, return_center=True)
        print(f"T2a: 'Endpoints-paired' (lightest↔heaviest, etc.)")
        for (a, b), r in zip(pair_baseline, resids_base):
            midpt = 0.5 * (log_msq[a] + log_msq[b])
            print(f"     ({a:>4s}, {b:>4s})  midpoint = {midpt:8.3f}  "
                  f"dev = {r:+7.3f}")
        print(f"     c* = {c_base:.3f}  RMS resid = {rms_base:.3f}")
        print()
        records.append({"test": "T2a_endpoint_pairing",
                          "benchmark": label,
                          "pairs": [list(p) for p in pair_baseline],
                          "center_c": c_base, "rms_residual": rms_base})

        # T2b: brute-force best pairing (over all 10395)
        all_pairings = []
        def gen_pairings(remaining):
            if not remaining:
                yield []
                return
            first = remaining[0]
            for j in range(1, len(remaining)):
                pair = (first, remaining[j])
                rest = remaining[1:j] + remaining[j + 1:]
                for sub in gen_pairings(rest):
                    yield [pair] + sub
        best_rms_any = float('inf')
        best_pairing = None
        best_c = None
        for pairing in gen_pairings(all_names):
            rms = pairwise_symmetry_residual(pairing, log_msq)
            if rms < best_rms_any:
                best_rms_any = rms
                best_pairing = pairing
                _, _, best_c, _ = pairwise_symmetry_residual(pairing, log_msq, return_center=True)
        print(f"T2b: best pairing (brute-force search over 10,395 pairings)")
        print(f"     Best pairing: {best_pairing}")
        print(f"     Best RMS residual: {best_rms_any:.4f}")
        print(f"     Best center c*: {best_c:.3f}")
        print()
        records.append({"test": "T2b_best_pairing_brute",
                          "benchmark": label,
                          "best_pairing": [list(p) for p in best_pairing],
                          "rms_residual": float(best_rms_any),
                          "center_c": float(best_c)})

        # PROPER null for T1: enumerate all 15 lepton-sector pairings
        print(f"T3 (CORRECTED): proper null for lepton-sector pairing")
        print(f"     Enumerating ALL 15 possible 3-pairings of {{e, μ, τ, ν_e, ν_μ, ν_τ}}")
        lepton_pairings_rms = lepton_sector_null(log_msq)
        lepton_pairings_rms.sort(key=lambda x: x[1])
        # Find the SM seesaw pairing's rank
        sm_rank = None
        for rank, (p, rms) in enumerate(lepton_pairings_rms):
            # SM seesaw = (e, ν_e), (μ, ν_μ), (τ, ν_τ) (set equality of pairs)
            p_sets = {frozenset(pair) for pair in p}
            sm_sets = {frozenset(pair) for pair in LEPTON_PAIRS}
            if p_sets == sm_sets:
                sm_rank = rank
                break
        print(f"     SM seesaw pairing rank: {sm_rank + 1} / 15 (sorted by RMS, lowest first)")
        print(f"     SM seesaw RMS: {rms_lep:.3f}")
        print(f"     Best of 15: RMS {lepton_pairings_rms[0][1]:.3f}  "
              f"pairs {lepton_pairings_rms[0][0]}")
        print(f"     Worst of 15: RMS {lepton_pairings_rms[-1][1]:.3f}")
        print(f"     Median of 15: RMS {lepton_pairings_rms[7][1]:.3f}")
        sm_percentile = 100.0 * sm_rank / 15
        print(f"     SM is at {sm_percentile:.1f}th percentile of 15 lepton pairings")
        records.append({"test": "T3_lepton_sector_proper_null",
                          "benchmark": label,
                          "sm_rank_out_of_15": sm_rank + 1,
                          "sm_percentile": float(sm_percentile),
                          "sm_rms": float(rms_lep),
                          "best_of_15_rms": float(lepton_pairings_rms[0][1]),
                          "worst_of_15_rms": float(lepton_pairings_rms[-1][1])})

        # Verdict per benchmark — now based on proper test
        if sm_rank == 0:
            verdict = f"STRONG SIGNAL: SM seesaw pairing is THE BEST of 15 possible"
        elif sm_rank <= 2:
            verdict = f"suggestive: SM seesaw pairing in top 3 of 15"
        elif sm_rank <= 7:
            verdict = f"weak: SM seesaw pairing in middle (rank {sm_rank+1}/15)"
        else:
            verdict = f"REFUTED: SM seesaw pairing in BOTTOM half (rank {sm_rank+1}/15)"
        print(f"   → BENCHMARK VERDICT: {verdict}")
        print()
        records.append({"test": "benchmark_verdict",
                          "benchmark": label, "verdict": verdict})

    # Save + plot
    with open(RESULTS_FILE, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    # Plot
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    for ax, (label, m_lightest, ordering) in zip(axes, benchmarks):
        log_msq = full_12_fermion_log_m_sq(m_lightest, ordering)
        sorted_log = sorted(log_msq.items(), key=lambda x: x[1])
        names = [n for n, _ in sorted_log]
        vals = [v for _, v in sorted_log]
        colors = ["red" if "ν" in n else "blue" for n in names]
        ax.scatter(range(12), vals, c=colors, s=80, zorder=5)
        for i, n in enumerate(names):
            ax.annotate(n, (i, vals[i]), textcoords="offset points",
                          xytext=(0, 10), ha="center", fontsize=9)
        ax.axhline(0, ls="--", c="gray", alpha=0.5, label="electron")
        ax.set_xlabel("rank")
        ax.set_ylabel("ln(m²/m_e²)")
        ax.set_title(f"m_lightest = {m_lightest} eV")
        ax.grid(alpha=0.3)
    plt.suptitle("Full 12-fermion log-m² spectrum across neutrino-mass benchmarks (red=neutrino, blue=charged)",
                  y=1.02)
    plt.tight_layout()
    plt.savefig(OUT_DIR / "sm-12-fermion-log-symmetric-2026-05-12.png", dpi=100,
                  bbox_inches="tight")
    plt.close()

    print(f"\nResults: {RESULTS_FILE.name}")
    print(f"Plot:    sm-12-fermion-log-symmetric-2026-05-12.png")

    # Final synthesis
    print("\n=== Final synthesis across benchmarks ===\n")
    verdicts_per_bench = [r for r in records if r["test"] == "benchmark_verdict"]
    for v in verdicts_per_bench:
        print(f"  {v['benchmark']:<15s}: {v['verdict']}")
    print()


if __name__ == "__main__":
    main()

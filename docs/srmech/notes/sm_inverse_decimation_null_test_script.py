"""
SM inverse-decimation NULL TEST (2026-05-12).

RESEARCH SPIKE — companion to sm_inverse_decimation_base_sweep_script.py.

The per-family base-sweep gave stunningly low deviations:
    leptons     dev = 0.0007  (b = 1.8725; k=17, 9)
    up-quarks   dev = 0.0079  (b = 2.667;  k=13, 10)
    down-quarks dev = 0.0168  (b = 1.7212; k=11, 14)

These look like signal — but with one continuous parameter b and only
2 constraint ratios per family, low devs may be Diophantine-approximation
artifact (every real number has rational approximations of arbitrary
quality).

This null test:
    1. Generate N synthetic "fermion families" with 2 random mass² ratios
       drawn from the same log-magnitude distribution as SM (between 1e2
       and 1e6).
    2. For each synthetic family, run the same base-b sweep.
    3. Tabulate the distribution of resulting min-devs.
    4. Compare SM per-family devs to the null distribution. If SM devs
       are typical of the null, the apparent hit was Diophantine luck.

If the SM devs are in the bottom 1% of the null distribution, that's
real signal. Otherwise the "find THE fractal" via base-sweep is
chasing noise.

Reproduce: `python -X utf8 docs/srmech/notes/sm_inverse_decimation_null_test_script.py`
"""

import json
import numpy as np
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT_DIR = Path(__file__).parent
RESULTS_FILE = OUT_DIR / "sm-inverse-decimation-null-test-per-trial-2026-05-12.ndjson"
RNG_SEED = 20260512

# ── SM observed devs (from previous spike) ───────────────────────────────

SM_OBSERVED_DEVS = {
    "leptons":     0.0007,
    "up_quarks":   0.0079,
    "down_quarks": 0.0168,
}

# ── Random ratio generation ─────────────────────────────────────────────

def sample_synthetic_family_ratios(rng, log_min=2.0, log_max=6.0):
    """Two random log-uniform ratios in [10^2, 10^6]."""
    r1 = 10 ** rng.uniform(log_min, log_max)
    r2 = 10 ** rng.uniform(log_min, log_max)
    return r1, r2


def best_b_dev_for_pair(r1, r2, b_grid):
    """Same scoring as sm_inverse_decimation_base_sweep_script.per_family_best_b_score."""
    log_b = np.log(b_grid)
    log_r1 = np.log(r1) / log_b
    log_r2 = np.log(r2) / log_b
    dev_1 = np.abs(log_r1 - np.round(log_r1))
    dev_2 = np.abs(log_r2 - np.round(log_r2))
    mean_dev = 0.5 * (dev_1 + dev_2)
    return float(mean_dev.min())


# ── Main ────────────────────────────────────────────────────────────────

def main():
    rng = np.random.default_rng(RNG_SEED)

    print("=== SM Inverse-Decimation NULL TEST ===\n")
    print("SM observed devs (per-family, base-sweep result):")
    for fam, dev in SM_OBSERVED_DEVS.items():
        print(f"  {fam:<12s} dev = {dev:.4f}")
    print()

    N_TRIALS = 10000
    b_grid = np.geomspace(1.5, 500, 50000)
    print(f"Null trials: {N_TRIALS}; each runs the same b-sweep ({len(b_grid)} grid points)")
    print()

    null_devs = []
    records = []
    for trial in range(N_TRIALS):
        r1, r2 = sample_synthetic_family_ratios(rng)
        dev = best_b_dev_for_pair(r1, r2, b_grid)
        null_devs.append(dev)
        if trial < 200:  # record a sample
            records.append({"test": "null_trial", "trial": trial,
                              "r1": float(r1), "r2": float(r2), "min_dev": dev})
    null_devs = np.array(null_devs)

    print(f"Null distribution of best-b deviations across {N_TRIALS} synthetic families:")
    print(f"  min:    {null_devs.min():.5f}")
    print(f"  1st pct: {np.percentile(null_devs, 1):.5f}")
    print(f"  5th pct: {np.percentile(null_devs, 5):.5f}")
    print(f"  median: {np.median(null_devs):.5f}")
    print(f"  90th pct: {np.percentile(null_devs, 90):.5f}")
    print(f"  max:    {null_devs.max():.5f}")
    print()

    # SM percentiles
    print("SM observed devs vs null distribution:")
    print(f"  {'family':<12s} {'SM dev':>10s} {'null pct':>10s} {'verdict':>20s}")
    print("-" * 60)
    for fam, sm_dev in SM_OBSERVED_DEVS.items():
        pct_below = float(np.mean(null_devs < sm_dev)) * 100
        if pct_below < 1.0:
            verdict = "REAL SIGNAL (< 1%)"
        elif pct_below < 5.0:
            verdict = "suggestive (< 5%)"
        elif pct_below < 20.0:
            verdict = "weak signal (< 20%)"
        else:
            verdict = "DIOPHANTINE NOISE"
        print(f"  {fam:<12s} {sm_dev:>10.4f} {pct_below:>9.2f}% {verdict:>20s}")
        records.append({"test": "sm_vs_null", "family": fam,
                          "sm_dev": float(sm_dev),
                          "null_pct_below": float(pct_below),
                          "verdict": verdict})
    print()

    # Joint probability: how often do random 3-family draws all hit ≤ SM devs?
    n_joint = 0
    JOINT_TRIALS = 5000
    sm_max_dev = max(SM_OBSERVED_DEVS.values())
    sm_mean_dev = np.mean(list(SM_OBSERVED_DEVS.values()))
    print(f"Joint test: probability random 3-family draw produces ALL three devs ≤ SM max ({sm_max_dev:.4f})...")
    for _ in range(JOINT_TRIALS):
        all_below = True
        for sm_dev in SM_OBSERVED_DEVS.values():
            r1, r2 = sample_synthetic_family_ratios(rng)
            d = best_b_dev_for_pair(r1, r2, b_grid)
            if d > sm_dev:  # tighter: each must beat the corresponding SM
                all_below = False
                break
        if all_below:
            n_joint += 1
    joint_pct = 100 * n_joint / JOINT_TRIALS
    print(f"  Joint probability under null: {joint_pct:.2f}% "
          f"({n_joint}/{JOINT_TRIALS} trials)")

    if joint_pct < 1.0:
        joint_verdict = "JOINT signal SIGNIFICANT — SM is < 1% under null"
    elif joint_pct < 5.0:
        joint_verdict = "JOINT signal SUGGESTIVE — SM is < 5% under null"
    else:
        joint_verdict = "JOINT signal NOT SIGNIFICANT — Diophantine noise explanation suffices"
    print(f"\n  {joint_verdict}")
    records.append({"test": "joint_null_test",
                     "joint_trials": JOINT_TRIALS, "n_below": n_joint,
                     "joint_pct": float(joint_pct), "verdict": joint_verdict})

    # Save
    with open(RESULTS_FILE, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    # Plot null distribution with SM markers
    fig, ax = plt.subplots(figsize=(10, 6))
    bins = np.linspace(0, 0.3, 80)
    ax.hist(null_devs, bins=bins, color="lightsteelblue", edgecolor="steelblue",
              alpha=0.7, label=f"Null (N={N_TRIALS})")
    colors = {"leptons": "crimson", "up_quarks": "darkorange", "down_quarks": "forestgreen"}
    for fam, sm_dev in SM_OBSERVED_DEVS.items():
        ax.axvline(sm_dev, color=colors[fam], lw=2.0, ls="--",
                    label=f"SM {fam} (dev = {sm_dev:.4f})")
    ax.axvline(np.percentile(null_devs, 1), color="black", ls=":", alpha=0.5,
                label=f"null 1st pct = {np.percentile(null_devs, 1):.4f}")
    ax.set_xlabel("min mean-integer-dev across base-b sweep")
    ax.set_ylabel(f"count out of {N_TRIALS} null trials")
    ax.set_title("Null distribution of per-family best-b devs (Diophantine baseline)")
    ax.legend(); ax.grid(alpha=0.3)
    ax.set_xlim([0, 0.15])
    plt.tight_layout()
    plt.savefig(OUT_DIR / "sm-inverse-decimation-null-test-2026-05-12.png", dpi=100)
    plt.close()

    print(f"\nResults: {RESULTS_FILE.name}")
    print(f"Plot:    sm-inverse-decimation-null-test-2026-05-12.png")

    print("\n=== Final synthesis ===")
    print(f"  Null 1st-pct dev: {np.percentile(null_devs, 1):.4f}")
    print(f"  SM devs: leptons {SM_OBSERVED_DEVS['leptons']:.4f}, "
          f"up {SM_OBSERVED_DEVS['up_quarks']:.4f}, "
          f"down {SM_OBSERVED_DEVS['down_quarks']:.4f}")
    print(f"  Joint null prob: {joint_pct:.2f}%")
    if joint_pct < 1.0:
        print("\n  → SIGNAL CONFIRMED: SM mass ratios snap to integer log-b levels")
        print("    at rates inconsistent with random Diophantine luck. Continue search:")
        print("    construct fractals with R'(0) ≈ 1.87 (leptons) and check whether they")
        print("    physically exist and have the right number of SM observables.")
    else:
        print("\n  → DIOPHANTINE-NOISE EXPLANATION HOLDS:")
        print("    Per-family low devs are typical of random pairs of large-magnitude")
        print("    ratios under a continuous-b sweep. This does NOT prove §XIII.1 wrong,")
        print("    but the base-sweep diagnostic CANNOT distinguish real fractal structure")
        print("    from chance approximations. Search method itself is degenerate.")
        print()
        print("    Implication: the §XIII.1 'find a fractal whose spectrum reproduces SM'")
        print("    program requires CONSTRAINTS BEYOND eigenvalue matching — e.g. spectral")
        print("    dimension, exceptional-eigenvalue structure, multiplicities matching")
        print("    SM gauge representations. Eigenvalue matching alone is information-poor.")


if __name__ == "__main__":
    main()

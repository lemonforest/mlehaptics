"""
SM inverse-decimation base-b sweep (2026-05-12).

RESEARCH SPIKE — follow-up to sm_inverse_decimation_spike_script.py.

Previous spike refuted Fukushima-Shima SG R(λ) = λ(5 − 4λ); the small-λ
slope R'(0) = 5 cannot fit the SM mass hierarchy on a single decimation
orbit. The natural next test: sweep the small-λ slope b across a wide
range. Two questions:

  Q1. Is there a b for which ALL six SM mass² ratios sit on integer
      log_b values (mean integer-deviation < 0.10)?

  Q2. If not globally, is there a b for which a SINGLE FERMION FAMILY
      (leptons OR up-quarks OR down-quarks) sits cleanly on integer
      log_b levels? This would mean per-family decimation rather than
      universal.

The base b is the small-λ scaling factor; in fractal language, it's
related to (number of contracting maps in IFS) × (some function of
contraction ratio). So scanning b over [1.5, 500] surveys the full
range of fractal IFS configurations.

If even at the best b mean dev stays near random (0.25), the integer-
decimation hypothesis is dead regardless of which R polynomial family.

Reproduce: `python -X utf8 docs/srmech/notes/sm_inverse_decimation_base_sweep_script.py`
"""

import json
import numpy as np
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT_DIR = Path(__file__).parent
RESULTS_FILE = OUT_DIR / "sm-inverse-decimation-base-sweep-per-b-2026-05-12.ndjson"

# ── SM input (PDG 2024) ─────────────────────────────────────────────────

SM_MASS_SQ_RATIOS = {
    "leptons":     {"mid_light":  (105.66 / 0.511) ** 2,        # μ/e
                     "heavy_mid":  (1776.86 / 105.66) ** 2},     # τ/μ
    "up_quarks":   {"mid_light":  (1270.0 / 2.16) ** 2,         # c/u
                     "heavy_mid":  (172760.0 / 1270.0) ** 2},    # t/c
    "down_quarks": {"mid_light":  (93.4 / 4.67) ** 2,           # s/d
                     "heavy_mid":  (4180.0 / 93.4) ** 2},        # b/s
}

ALL_RATIOS = [r for fam in SM_MASS_SQ_RATIOS.values() for r in fam.values()]


# ── Core scoring ────────────────────────────────────────────────────────

def integer_dev(log_value):
    """Distance from log_value to the nearest non-negative integer."""
    return abs(log_value - round(log_value))


def mean_integer_dev_universal(b):
    """Mean integer-deviation of log_b(ratio) over all 6 ratios — universal b."""
    if b <= 1.0:
        return float("inf")
    log_b = np.log(b)
    return float(np.mean([integer_dev(np.log(r) / log_b) for r in ALL_RATIOS]))


def per_family_best_b_score(family_ratios, b_grid):
    """For one family, find b* minimising mean integer-dev over its 2 ratios."""
    log_b = np.log(b_grid)
    r1, r2 = family_ratios["mid_light"], family_ratios["heavy_mid"]
    log_r1_b = np.log(r1) / log_b
    log_r2_b = np.log(r2) / log_b
    nearest_int_1 = np.round(log_r1_b)
    nearest_int_2 = np.round(log_r2_b)
    dev_1 = np.abs(log_r1_b - nearest_int_1)
    dev_2 = np.abs(log_r2_b - nearest_int_2)
    mean_dev = 0.5 * (dev_1 + dev_2)
    idx = np.argmin(mean_dev)
    return {
        "b_star": float(b_grid[idx]),
        "mean_dev": float(mean_dev[idx]),
        "k_mid": int(nearest_int_1[idx]),
        "k_heavy": int(nearest_int_2[idx]),
        "predicted_log_b_ratio_mid": float(log_r1_b[idx]),
        "predicted_log_b_ratio_heavy": float(log_r2_b[idx]),
    }


# ── Q1: universal b sweep ───────────────────────────────────────────────

def sweep_universal_b(b_min=1.5, b_max=500, n=20000):
    b_grid = np.geomspace(b_min, b_max, n)
    scores = np.array([mean_integer_dev_universal(b) for b in b_grid])
    idx = np.argmin(scores)
    return b_grid, scores, idx


# ── Main ────────────────────────────────────────────────────────────────

def main():
    records = []

    print("=== SM Inverse-Decimation Base-b Sweep ===\n")
    print("SM mass² ratios (input):")
    for fam, fam_ratios in SM_MASS_SQ_RATIOS.items():
        print(f"  {fam:<12s} mid/light² = {fam_ratios['mid_light']:.4e}  "
              f"heavy/mid² = {fam_ratios['heavy_mid']:.4e}")
    print()

    # Q1: universal b
    print("=== Q1: Universal-b sweep (one b for all 6 ratios) ===\n")
    b_grid, scores, idx = sweep_universal_b()
    b_star = b_grid[idx]
    score_star = scores[idx]
    print(f"  Best universal b: {b_star:.4f}")
    print(f"  Mean integer-deviation at b*: {score_star:.4f}")
    print(f"  Random baseline: 0.25 (uniform integer-deviation)")
    print(f"  Required for SURVIVAL: < 0.10\n")

    # Detail at b*
    print(f"  Per-ratio detail at b* = {b_star:.4f}:")
    log_b = np.log(b_star)
    print(f"  {'family':<12s} {'ratio':<10s} {'value':>14s} {'log_b*':>9s} {'k_nearest':>10s} {'dev':>7s}")
    print("-" * 70)
    for fam, fam_ratios in SM_MASS_SQ_RATIOS.items():
        for label, r in fam_ratios.items():
            log_val = np.log(r) / log_b
            k = round(log_val)
            dev = abs(log_val - k)
            print(f"  {fam:<12s} {label:<10s} {r:>14.4e} {log_val:>9.3f} {k:>10d} {dev:>7.3f}")
            records.append({"test": "universal_b_per_ratio", "family": fam,
                              "ratio_kind": label, "ratio": r, "b_star": float(b_star),
                              "log_b_value": float(log_val), "k_nearest": int(k),
                              "dev": float(dev)})
    print()

    verdict_q1 = ("SURVIVES" if score_star < 0.10
                   else "WEAK" if score_star < 0.18
                   else "REFUTED — universal-b integer-decimation hypothesis fails")
    print(f"  Q1 VERDICT: {verdict_q1}\n")
    records.append({"test": "q1_verdict", "b_star": float(b_star),
                     "mean_dev": float(score_star), "verdict": verdict_q1})

    # Q2: per-family b
    print("=== Q2: Per-family best-b (each family gets its own decimation) ===\n")
    fine_b_grid = np.geomspace(1.5, 500, 50000)
    per_family_fits = {}
    print(f"  {'family':<12s} {'b*':>10s} {'k_mid':>6s} {'k_heavy':>8s} {'mean_dev':>10s} {'log_b ratios':>30s}")
    print("-" * 80)
    for fam, fam_ratios in SM_MASS_SQ_RATIOS.items():
        fit = per_family_best_b_score(fam_ratios, fine_b_grid)
        per_family_fits[fam] = fit
        print(f"  {fam:<12s} {fit['b_star']:>10.4f} {fit['k_mid']:>6d} {fit['k_heavy']:>8d} "
              f"{fit['mean_dev']:>10.4f}  ({fit['predicted_log_b_ratio_mid']:.3f}, "
              f"{fit['predicted_log_b_ratio_heavy']:.3f})")
        records.append({"test": "per_family_best_b", "family": fam, **fit})
    print()

    # Per-family verdict
    n_survive = sum(1 for f in per_family_fits.values() if f["mean_dev"] < 0.10)
    print(f"  Families with mean_dev < 0.10 (survive): {n_survive} / 3")
    families_b = [f["b_star"] for f in per_family_fits.values()]
    print(f"  Per-family b*: {[round(b, 3) for b in families_b]}")
    if max(families_b) / min(families_b) < 1.05:
        verdict_q2 = "CONVERGENT — families share a near-common b (suggests universal)"
    elif n_survive >= 2:
        verdict_q2 = "PARTIAL — at least 2 families admit clean integer-b fits"
    else:
        verdict_q2 = "REFUTED — per-family integer-decimation also fails"
    print(f"\n  Q2 VERDICT: {verdict_q2}\n")
    records.append({"test": "q2_verdict", "n_survive": n_survive,
                     "families_b": [float(b) for b in families_b],
                     "verdict": verdict_q2})

    # Save
    with open(RESULTS_FILE, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    # Plot
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    axes[0].semilogx(b_grid, scores, c="steelblue", lw=1.3)
    axes[0].axhline(0.25, ls=":", c="gray", label="random baseline (0.25)")
    axes[0].axhline(0.10, ls="--", c="red", label="survival threshold (0.10)")
    axes[0].axvline(b_star, ls=":", c="green", label=f"b* = {b_star:.3f}, dev = {score_star:.3f}")
    axes[0].axvline(5.0, ls=":", c="orange", alpha=0.6, label="SG b = 5 (previous spike)")
    axes[0].set_xlabel("base b (small-λ slope of decimation R(λ))")
    axes[0].set_ylabel("mean integer-deviation across 6 SM ratios")
    axes[0].set_title("Q1: universal-b inverse-decimation sweep")
    axes[0].legend(loc="upper right"); axes[0].grid(alpha=0.3)
    axes[0].set_ylim([0, 0.35])

    # Per-family bars
    fams = list(per_family_fits.keys())
    devs = [per_family_fits[f]["mean_dev"] for f in fams]
    bs = [per_family_fits[f]["b_star"] for f in fams]
    bars = axes[1].bar(fams, devs, color=["steelblue", "coral", "seagreen"])
    axes[1].axhline(0.10, ls="--", c="red", label="survival threshold (0.10)")
    axes[1].axhline(0.25, ls=":", c="gray", label="random baseline (0.25)")
    axes[1].set_ylabel("per-family best-fit mean integer-deviation")
    axes[1].set_title("Q2: per-family best-b deviation")
    for bar, b in zip(bars, bs):
        axes[1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.005,
                      f"b* = {b:.2f}", ha="center", fontsize=9)
    axes[1].legend(); axes[1].grid(alpha=0.3, axis="y")
    axes[1].set_ylim([0, 0.30])
    plt.tight_layout()
    plt.savefig(OUT_DIR / "sm-inverse-decimation-base-sweep-2026-05-12.png", dpi=100)
    plt.close()

    print(f"Results: {RESULTS_FILE.name}")
    print(f"Plot:    sm-inverse-decimation-base-sweep-2026-05-12.png")

    print("\n=== Final synthesis ===")
    print(f"  Universal b: best is b* = {b_star:.4f} with dev = {score_star:.4f}")
    print(f"  Per-family: {n_survive}/3 families admit clean integer-decimation")
    if score_star < 0.10:
        print(f"\n  → STRONG HIT: universal R'(0) = {b_star:.4f} survives. Next step:")
        print(f"    find a fractal IFS with that small-λ slope. Quadratic R(λ) = λ(b − (b-1)λ)")
        print(f"    with b = {b_star:.4f} gives a candidate; needs physical IFS interpretation.")
    elif n_survive >= 2:
        print(f"\n  → PARTIAL HIT: per-family integer-decimation works for {n_survive}/3 families.")
        print(f"    Families may correspond to DIFFERENT FRACTALS. Investigate per-family")
        print(f"    decimation polynomials and look for a unifying parent structure.")
    else:
        print(f"\n  → INTEGER-DECIMATION HYPOTHESIS REFUTED.")
        print(f"    No base b reproduces SM mass hierarchy on integer-decimation orbits.")
        print(f"    This rules out the entire class of self-similar polynomial-decimation")
        print(f"    fractals as SM mass generators. The §XIII.1 'fractal F such that")
        print(f"    spectrum reproduces SM' premise needs to be reconsidered.")


if __name__ == "__main__":
    main()

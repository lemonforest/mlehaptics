"""
SM-mass inverse-decimation spike (2026-05-12).

RESEARCH SPIKE (not on a PR branch).

Question: are the Standard Model charged-fermion mass² values consistent
with a Sierpinski-Gasket-family spectral decimation orbit?

Setup. The Fukushima-Shima SG decimation forward map is
        R(λ) = λ(5 − 4λ),                          λ ∈ [0, 5/4]
with R(0) = 0 (fixed point) and small-λ slope R'(0) = 5. So eigenvalues
at fractal level n+1 satisfy R(λ_{n+1}) = λ_n; iterating R takes deep-IR
(small λ, deep level) to UV (larger λ, shallow level). Successive
decimation levels scale roughly ×5 in eigenvalue at small λ.

Working backwards: if e/μ/τ sit on a single decimation orbit with the
lightest at the deepest level, then there exist integers k_μ > 0 and
k_τ > k_μ and a scale s such that

        R^{k_μ}(m_e² / s) ≈ m_μ² / s
        R^{k_τ}(m_e² / s) ≈ m_τ² / s

Test 1 — single-orbit hypothesis per generation:
    For each fermion family (leptons, up-quarks, down-quarks):
        Sweep scale s; for each (k_μ, k_τ) pair, compute residual
        |R^{k_μ}(m_e²/s) − m_μ²/s| + |R^{k_τ}(m_e²/s) − m_τ²/s|
        Find (s*, k_μ*, k_τ*) minimising residual.

Test 2 — cross-family consistency:
    If SG-family decimation describes flavour, the per-generation
    best-fit (k_μ, k_τ) ought to be similar across families, with
    family-specific scales s. Strong divergence → SG family is wrong R(λ).

Test 3 — orbital-period analysis:
    At small λ, R ≈ ×5 per iteration. So expected k_μ ≈ log₅((m_μ/m_e)²)
    ≈ log₅(4.28e4) ≈ 6.62. Non-integer expected log_5 value already
    signals a problem. Compute log_5 of all SM mass² ratios; see if
    any are even close to integers.

Reproduce: `python -X utf8 docs/srmech/notes/sm_inverse_decimation_spike_script.py`
"""

import json
import numpy as np
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT_DIR = Path(__file__).parent
RESULTS_FILE = OUT_DIR / "sm-inverse-decimation-spike-per-test-2026-05-12.ndjson"


# ── SM input (PDG 2024, MeV) ────────────────────────────────────────────

SM_MASSES_MEV = {
    "leptons":     {"light": ("e", 0.511),  "middle": ("μ", 105.66), "heavy": ("τ", 1776.86)},
    "up_quarks":   {"light": ("u", 2.16),   "middle": ("c", 1270.0),  "heavy": ("t", 172760.0)},
    "down_quarks": {"light": ("d", 4.67),   "middle": ("s", 93.4),    "heavy": ("b", 4180.0)},
}


# ── SG decimation map ───────────────────────────────────────────────────

def R(lam):
    """Fukushima-Shima forward map: R(λ) = λ(5 - 4λ)."""
    return lam * (5.0 - 4.0 * lam)


def R_iter(lam, k):
    """Apply R k times. If we leave [0, 5/4] domain, mark as escaped."""
    x = lam
    for _ in range(k):
        x = R(x)
        if x < 0 or x > 5.0 or not np.isfinite(x):
            return None
    return x


# ── Test 1: per-generation single-orbit fit ─────────────────────────────

def fit_orbit_single_generation(m_light_sq, m_middle_sq, m_heavy_sq,
                                  s_grid_log_min=-8, s_grid_log_max=4,
                                  s_grid_n=400, k_max=20):
    """
    Find (s, k_μ, k_τ) minimising
       |R^{k_μ}(m_light² / s) − m_middle² / s|
       + |R^{k_τ}(m_light² / s) − m_heavy² / s|
    """
    s_grid = np.logspace(s_grid_log_min, s_grid_log_max, s_grid_n)
    best = {"residual": float('inf'), "s": None, "k_mid": None, "k_heavy": None,
            "predicted_middle": None, "predicted_heavy": None}
    for s in s_grid:
        x0 = m_light_sq / s
        if not (0 < x0 < 5.0):
            continue
        # Iterate R; store trajectory
        traj = [x0]
        for _ in range(k_max):
            nxt = R(traj[-1])
            if not (0 <= nxt <= 5.0) or not np.isfinite(nxt):
                break
            traj.append(nxt)
        if len(traj) < 3:
            continue
        target_mid = m_middle_sq / s
        target_heavy = m_heavy_sq / s
        # For each k_mid, find nearest k_heavy > k_mid
        for k_mid in range(1, len(traj)):
            for k_heavy in range(k_mid + 1, len(traj)):
                resid = (abs(traj[k_mid] - target_mid) / target_mid
                         + abs(traj[k_heavy] - target_heavy) / target_heavy)
                if resid < best["residual"]:
                    best.update({
                        "residual": float(resid),
                        "s": float(s),
                        "k_mid": int(k_mid),
                        "k_heavy": int(k_heavy),
                        "predicted_middle": float(traj[k_mid] * s),
                        "predicted_heavy": float(traj[k_heavy] * s),
                    })
    return best


# ── Test 3: log_5 hierarchy check ───────────────────────────────────────

def log5_hierarchy_check():
    """
    At small λ, R(λ) ≈ 5λ, so successive decimation levels scale ×5.
    If SM mass² ratios sit on integer-level decimation orbits, then
    log₅(ratio) should be ≈ integer. Compute log₅ of all six ratios.
    """
    rows = []
    for family, masses in SM_MASSES_MEV.items():
        m_l = masses["light"][1]
        m_m = masses["middle"][1]
        m_h = masses["heavy"][1]
        ratio_mid_light  = (m_m / m_l) ** 2
        ratio_heavy_mid  = (m_h / m_m) ** 2
        log5_mid_light = np.log(ratio_mid_light) / np.log(5)
        log5_heavy_mid = np.log(ratio_heavy_mid) / np.log(5)
        rows.append({
            "family": family,
            "ratio_mid_over_light_sq": float(ratio_mid_light),
            "ratio_heavy_over_mid_sq": float(ratio_heavy_mid),
            "log5_mid_over_light":     float(log5_mid_light),
            "log5_heavy_over_mid":     float(log5_heavy_mid),
            "k_mid_nearest_int":   int(round(log5_mid_light)),
            "k_heavy_nearest_int": int(round(log5_heavy_mid)),
            "log5_mid_int_dev":   float(abs(log5_mid_light - round(log5_mid_light))),
            "log5_heavy_int_dev": float(abs(log5_heavy_mid - round(log5_heavy_mid))),
        })
    return rows


# ── Main ────────────────────────────────────────────────────────────────

def main():
    records = []

    print("=== SM Inverse Decimation Spike ===")
    print(f"SG forward map R(λ) = λ(5 − 4λ); small-λ slope R'(0) = 5\n")

    print("=== Test 3: log₅ hierarchy check (do SM ratios sit on integer-level orbits?) ===\n")
    log5_rows = log5_hierarchy_check()
    print(f"{'family':<12s} {'mid/light²':>14s} {'log₅':>8s} {'k≈':>4s} {'dev':>6s}    "
          f"{'heavy/mid²':>14s} {'log₅':>8s} {'k≈':>4s} {'dev':>6s}")
    print("-" * 100)
    for r in log5_rows:
        print(f"{r['family']:<12s} "
              f"{r['ratio_mid_over_light_sq']:>14.4e} "
              f"{r['log5_mid_over_light']:>8.3f} "
              f"{r['k_mid_nearest_int']:>4d} "
              f"{r['log5_mid_int_dev']:>6.3f}    "
              f"{r['ratio_heavy_over_mid_sq']:>14.4e} "
              f"{r['log5_heavy_over_mid']:>8.3f} "
              f"{r['k_heavy_nearest_int']:>4d} "
              f"{r['log5_heavy_int_dev']:>6.3f}")
        records.append({"test": "log5_hierarchy_per_family", **r})
    print()

    # Interpretation
    avg_dev = np.mean([r["log5_mid_int_dev"] for r in log5_rows]
                      + [r["log5_heavy_int_dev"] for r in log5_rows])
    print(f"  Mean integer-deviation across 6 ratios: {avg_dev:.3f}")
    print(f"  Reference: a random log₅(ratio) has expected integer-deviation 0.25 (uniform)")
    print(f"  → SG-family small-λ approximation gives {'consistent' if avg_dev < 0.10 else 'INCONSISTENT'} integer-level fit\n")

    print("=== Test 1: per-generation full-R orbit fit ===")
    print(f"{'family':<12s} {'scale s':>12s} {'k_μ':>5s} {'k_τ':>5s} {'residual':>10s} "
          f"{'predicted m_mid²':>18s} {'observed m_mid²':>18s} "
          f"{'predicted m_heavy²':>20s} {'observed m_heavy²':>20s}")
    print("-" * 130)
    for family, masses in SM_MASSES_MEV.items():
        m_l_sq = masses["light"][1] ** 2
        m_m_sq = masses["middle"][1] ** 2
        m_h_sq = masses["heavy"][1] ** 2
        fit = fit_orbit_single_generation(m_l_sq, m_m_sq, m_h_sq)
        if fit["s"] is not None:
            print(f"{family:<12s} {fit['s']:>12.3e} {fit['k_mid']:>5d} {fit['k_heavy']:>5d} "
                  f"{fit['residual']:>10.3f} "
                  f"{fit['predicted_middle']:>18.3e} {m_m_sq:>18.3e} "
                  f"{fit['predicted_heavy']:>20.3e} {m_h_sq:>20.3e}")
        else:
            print(f"{family:<12s}  no fit found")
        records.append({"test": "per_family_orbit_fit", "family": family,
                          "m_light_sq_mev2": m_l_sq, "m_middle_sq_mev2": m_m_sq,
                          "m_heavy_sq_mev2": m_h_sq, **fit})
    print()

    print("=== Test 2: cross-family consistency ===")
    # Extract per-family fits
    fits = [r for r in records if r["test"] == "per_family_orbit_fit"]
    k_mids = [f["k_mid"] for f in fits if f["k_mid"] is not None]
    k_heavys = [f["k_heavy"] for f in fits if f["k_heavy"] is not None]
    s_vals = [f["s"] for f in fits if f["s"] is not None]
    print(f"  Best-fit k_μ across families: {k_mids}")
    print(f"  Best-fit k_τ across families: {k_heavys}")
    print(f"  Best-fit scale s across families: {[f'{s:.2e}' for s in s_vals]}")
    print()

    if len(set(k_mids)) == 1 and len(set(k_heavys)) == 1:
        verdict_2 = "CROSS-FAMILY CONSISTENT (same level structure)"
    elif max(k_mids) - min(k_mids) <= 1 and max(k_heavys) - min(k_heavys) <= 1:
        verdict_2 = "approximately cross-family consistent (Δk ≤ 1)"
    else:
        verdict_2 = "CROSS-FAMILY INCONSISTENT — SG family is the wrong R(λ)"
    print(f"  → {verdict_2}")
    records.append({"test": "cross_family_verdict", "verdict": verdict_2,
                      "k_mids": k_mids, "k_heavys": k_heavys, "s_vals": s_vals})

    # Save
    with open(RESULTS_FILE, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    # Plot: log_5 ratios vs nearest integer
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    families = [r["family"] for r in log5_rows]
    log5_mids = [r["log5_mid_over_light"] for r in log5_rows]
    log5_heavys = [r["log5_heavy_over_mid"] for r in log5_rows]
    x = np.arange(len(families))
    axes[0].bar(x - 0.2, log5_mids, 0.4, label="log₅(mid/light)²")
    axes[0].bar(x + 0.2, log5_heavys, 0.4, label="log₅(heavy/mid)²")
    for k in range(0, 12):
        axes[0].axhline(k, ls=":", c="gray", alpha=0.4)
    axes[0].set_xticks(x); axes[0].set_xticklabels(families)
    axes[0].set_ylabel("log₅(mass² ratio)")
    axes[0].set_title("Test 3: SM mass-ratio log₅ vs integer-decimation-levels")
    axes[0].legend(); axes[0].grid(alpha=0.3, axis="y")

    # Plot residuals per family (Test 1)
    residuals = [f["residual"] for f in fits]
    fam_labels = [f["family"] for f in fits]
    axes[1].bar(fam_labels, residuals, color="steelblue")
    axes[1].set_ylabel("relative residual (lower = better SG orbit fit)")
    axes[1].set_title("Test 1: SG-orbit fit residual per fermion family")
    axes[1].grid(alpha=0.3, axis="y")
    plt.tight_layout()
    plt.savefig(OUT_DIR / "sm-inverse-decimation-spike-2026-05-12.png", dpi=100)
    plt.close()

    print(f"\nResults: {RESULTS_FILE.name}")
    print(f"Plot:    sm-inverse-decimation-spike-2026-05-12.png")

    print()
    print("=== Verdict ===")
    print(f"  Test 1 best residual across all families: {min(f['residual'] for f in fits):.3f}")
    print(f"  Test 2: {verdict_2}")
    print(f"  Test 3 mean integer-deviation: {avg_dev:.3f}  ", end="")
    if avg_dev < 0.10:
        print("(integer-decimation hypothesis SURVIVES)")
    else:
        print("(integer-decimation hypothesis REFUTED — SG R(λ) is wrong)")
    print()
    print("INTERPRETATION:")
    print("  If Test 3 fails, the Fukushima-Shima R(λ) = λ(5−4λ) cannot")
    print("  reproduce the SM mass hierarchy. Next research move: find or")
    print("  construct fractals with different decimation polynomials,")
    print("  then re-run inverse-decimation against those R's. Candidates:")
    print("    - Hexagonal-SG (different polynomial degree)")
    print("    - Higher-branching SG variants (3 → 4, 5 branches)")
    print("    - Non-polynomial decimation (transcendental fractals)")


if __name__ == "__main__":
    main()

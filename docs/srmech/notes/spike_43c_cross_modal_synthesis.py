"""
Spike #43c — Cross-modal synthesis.

Find universal-vs-modality-specific signatures of well-spread knowledge.

Hypothesis test:
  H1 (UNIVERSAL): well-spread knowledge has a shared meta-signature across modalities
                  (a SHARED epsilon-tower per c_k = eps^k * K_k(modality))
  H0 (MODALITY-SPECIFIC ONLY): each modality has its own unique shape; no universal beyond
                                modality-specific bindings

Methods:
  1. Per-modality central tendency + spread for each signature (R1 eps, R2 slope, R3
     propagation, R4 callbacks, S7 hapax, S6 cascade-beta)
  2. Cross-modal coefficient of variation (CV = std/mean) — UNIVERSAL signatures have
     LOW CV; modality-specific signatures have HIGH CV
  3. ANOVA-style: between-modality variance vs within-modality variance ratio (analogous
     to F-statistic; we use the ratio directly because we are doing closed-form descriptive
     statistics, not inferential p-values)
  4. K_k shape investigation per modality: fit pure-Zipf (1/k^s) vs Cauchy (1/k) vs
     geometric (1/k decay) on top word frequencies

Output: NDJSON records of:
  - Per-modality central tendency tables
  - Cross-modal CV table
  - K_k shape findings
  - Universal vs modality-specific verdict per signature
  - Iceberg-foresight markers calibrated across modalities (the cross-modal generalisation
    of Spike #43's six iceberg markers)
"""

from __future__ import annotations

import collections
import json
import math
import statistics
from pathlib import Path


OUT_DIR = Path(r"D:\temp\spike_43c")


def load_signatures() -> list[dict]:
    path = OUT_DIR / "spike_43c_signature_records_2026-05-17.ndjson"
    records = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line))
    return records


def per_modality_summary(records: list[dict], signature_key: str, subkey: str) -> dict:
    by_mod: dict[str, list[float]] = collections.defaultdict(list)
    for r in records:
        sig = r.get(signature_key, {})
        if isinstance(sig, dict) and sig.get("valid") and subkey in sig:
            v = sig[subkey]
            if isinstance(v, (int, float)) and not math.isnan(v):
                by_mod[r["modality"]].append(float(v))
    summary = {}
    for mod, vals in by_mod.items():
        if vals:
            summary[mod] = {
                "n": len(vals),
                "mean": statistics.mean(vals),
                "stdev": statistics.stdev(vals) if len(vals) > 1 else 0.0,
                "min": min(vals),
                "max": max(vals),
                "median": statistics.median(vals),
            }
    return summary


def cross_modal_cv(per_mod: dict) -> tuple[float, float, float]:
    """Return (mean_of_means, std_of_means, CV_of_means).

    LOW CV → universal signature (consistent across modalities).
    HIGH CV → modality-specific signature.
    """
    means = [s["mean"] for s in per_mod.values() if s["n"] > 0]
    if not means:
        return float("nan"), float("nan"), float("nan")
    grand_mean = statistics.mean(means)
    grand_std = statistics.stdev(means) if len(means) > 1 else 0.0
    cv = (grand_std / abs(grand_mean)) if grand_mean != 0 else float("inf")
    return grand_mean, grand_std, cv


def anova_ratio(records: list[dict], signature_key: str, subkey: str) -> dict:
    """Between-modality variance / within-modality variance ratio.

    Closed-form descriptive statistic (we don't claim F-distribution p-values).
    """
    by_mod: dict[str, list[float]] = collections.defaultdict(list)
    for r in records:
        sig = r.get(signature_key, {})
        if isinstance(sig, dict) and sig.get("valid") and subkey in sig:
            v = sig[subkey]
            if isinstance(v, (int, float)) and not math.isnan(v):
                by_mod[r["modality"]].append(float(v))
    n_total = sum(len(v) for v in by_mod.values())
    if n_total < 4 or len(by_mod) < 2:
        return {"valid": False}
    all_vals = [v for vs in by_mod.values() for v in vs]
    grand_mean = sum(all_vals) / n_total
    # Between-mod sum of squares
    ss_between = sum(len(vs) * (statistics.mean(vs) - grand_mean) ** 2 for vs in by_mod.values())
    # Within-mod sum of squares
    ss_within = 0.0
    for vs in by_mod.values():
        if len(vs) < 2:
            continue
        m = statistics.mean(vs)
        for v in vs:
            ss_within += (v - m) ** 2
    if ss_within < 1e-12:
        return {
            "valid": True,
            "ss_between": ss_between,
            "ss_within": ss_within,
            "ratio": float("inf") if ss_between > 0 else 0.0,
            "verdict": "ss_within near zero",
        }
    ratio = ss_between / ss_within
    return {
        "valid": True,
        "n_modalities": len(by_mod),
        "n_total": n_total,
        "ss_between": ss_between,
        "ss_within": ss_within,
        "between_over_within": ratio,
        "grand_mean": grand_mean,
        "verdict": (
            "modality-specific (high between-mod variance)" if ratio > 2.0
            else "cross-modal universal" if ratio < 0.5
            else "mixed"
        ),
    }


def investigate_kk_shape(records: list[dict]) -> list[dict]:
    """For each substrate, fit pure-Zipf K_k = 1/k^s vs Cauchy K_k = 1/k vs geometric K_k = 1.

    The K_k_substrate array from R1 is c_k / eps_unbiased^k. Fit the shape over k=1..6.
    """
    out = []
    for r in records:
        r1 = r.get("R1_kladder", {})
        if not r1.get("valid"):
            continue
        K_k = r1.get("K_k_substrate", [])
        if len(K_k) < 4:
            continue
        # K_k vs 1/k^s: log K_k = -s * log(k) + log(K_1)
        # Use k = 1..6
        ks = list(range(1, len(K_k) + 1))
        log_k = [math.log(k) for k in ks]
        log_Kk = [math.log(max(abs(K_k[i]), 1e-12)) for i in range(len(K_k))]
        # Fit log K = a + s * log k  (where Zipf form is K_k = 1/k^|s|, so we expect s near -1)
        n = len(ks)
        mean_x = sum(log_k) / n
        mean_y = sum(log_Kk) / n
        cov = sum((log_k[i] - mean_x) * (log_Kk[i] - mean_y) for i in range(n))
        var = sum((log_k[i] - mean_x) ** 2 for i in range(n))
        s_fit = cov / var if var else 0.0
        intercept = mean_y - s_fit * mean_x
        pred = [intercept + s_fit * log_k[i] for i in range(n)]
        ss_res = sum((log_Kk[i] - pred[i]) ** 2 for i in range(n))
        ss_tot = sum((log_Kk[i] - mean_y) ** 2 for i in range(n))
        r2_zipf = 1.0 - ss_res / ss_tot if ss_tot else 0.0
        # Test Kepler 1/k: K_k = exp(intercept_kepler) / k^1; intercept_kepler = mean(log K + log k)
        intercept_kepler = sum(log_Kk[i] + log_k[i] for i in range(n)) / n
        pred_k = [intercept_kepler - log_k[i] for i in range(n)]
        ss_res_k = sum((log_Kk[i] - pred_k[i]) ** 2 for i in range(n))
        r2_kepler = 1.0 - ss_res_k / ss_tot if ss_tot else 0.0
        # Test geometric K_k ≈ const: intercept only
        intercept_const = sum(log_Kk) / n
        pred_const = [intercept_const for _ in range(n)]
        ss_res_const = sum((log_Kk[i] - pred_const[i]) ** 2 for i in range(n))
        r2_const = 1.0 - ss_res_const / ss_tot if ss_tot else 0.0
        out.append(
            {
                "substrate": r["substrate"],
                "modality": r["modality"],
                "K_k_substrate": K_k,
                "zipf_s_fit": s_fit,
                "zipf_r2": r2_zipf,
                "kepler_r2": r2_kepler,
                "constant_r2": r2_const,
                "best_model": max(
                    [("zipf", r2_zipf), ("kepler", r2_kepler), ("constant", r2_const)],
                    key=lambda p: p[1],
                )[0],
            }
        )
    return out


def cross_modal_iceberg_markers(records: list[dict]) -> dict:
    """The cross-modal extension of Spike #43's six iceberg markers.

    Compute well-spread band (P10..P90) per signature across all modalities;
    out-of-band = candidate iceberg foresight signature.
    """
    sigs = [
        ("R4_callbacks", "callbacks_per_1000_words"),
        ("R3_rare_cascade", "propagation_rate"),
        ("R2_para_pareto", "power_law_slope"),
        ("S7_vocab", "hapax_fraction"),
        ("S7_vocab", "heaps_alpha"),
        ("R1_kladder", "eps_unbiased_fit"),
    ]
    out = {}
    for sig_key, subkey in sigs:
        vals = []
        for r in records:
            sig = r.get(sig_key, {})
            if isinstance(sig, dict) and sig.get("valid") and subkey in sig:
                v = sig[subkey]
                if isinstance(v, (int, float)) and not math.isnan(v):
                    vals.append(float(v))
        if not vals:
            continue
        vals.sort()
        n = len(vals)
        p10 = vals[max(0, n // 10)]
        p25 = vals[max(0, n // 4)]
        p50 = vals[n // 2]
        p75 = vals[min(n - 1, 3 * n // 4)]
        p90 = vals[min(n - 1, 9 * n // 10)]
        out[f"{sig_key}_{subkey}"] = {
            "n": n,
            "min": vals[0],
            "p10": p10,
            "p25": p25,
            "median": p50,
            "p75": p75,
            "p90": p90,
            "max": vals[-1],
            "iceberg_band_p10_to_p90": [p10, p90],
        }
    return out


def per_modality_iceberg_bands(records: list[dict]) -> dict:
    """Per-modality bands for the same signatures — modality-specific K_k binding."""
    sigs = [
        ("R4_callbacks", "callbacks_per_1000_words"),
        ("R3_rare_cascade", "propagation_rate"),
        ("R2_para_pareto", "power_law_slope"),
        ("S7_vocab", "hapax_fraction"),
        ("R1_kladder", "eps_unbiased_fit"),
        ("S7_vocab", "heaps_alpha"),
    ]
    out: dict = collections.defaultdict(dict)
    for sig_key, subkey in sigs:
        by_mod = collections.defaultdict(list)
        for r in records:
            sig = r.get(sig_key, {})
            if isinstance(sig, dict) and sig.get("valid") and subkey in sig:
                v = sig[subkey]
                if isinstance(v, (int, float)) and not math.isnan(v):
                    by_mod[r["modality"]].append(float(v))
        for mod, vals in by_mod.items():
            if len(vals) < 2:
                out[mod][f"{sig_key}_{subkey}"] = {
                    "n": len(vals),
                    "values": vals,
                }
            else:
                vals_sorted = sorted(vals)
                out[mod][f"{sig_key}_{subkey}"] = {
                    "n": len(vals),
                    "min": vals_sorted[0],
                    "median": statistics.median(vals_sorted),
                    "max": vals_sorted[-1],
                    "mean": statistics.mean(vals_sorted),
                    "stdev": statistics.stdev(vals_sorted),
                }
    return dict(out)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    records = load_signatures()
    print(f"  Loaded {len(records)} substrate signature records across modalities")
    print(f"  Modalities present: {sorted(set(r['modality'] for r in records))}")

    synthesis_records = []
    out_lines = []

    # Per-signature cross-modal central tendency
    sigs_to_summarise = [
        ("R1_kladder", "eps_unbiased_fit", "R1 eps (K-ladder unbiased)"),
        ("R2_para_pareto", "power_law_slope", "R2 paragraph-Pareto slope"),
        ("R2_para_pareto", "max_over_median_ratio", "R2 max/median paragraph ratio"),
        ("R3_rare_cascade", "propagation_rate", "R3 rare-word propagation rate"),
        ("R4_callbacks", "callbacks_per_1000_words", "R4 callbacks per 1000 words"),
        ("S3_zipf", "zipf_slope", "S3 Zipf slope"),
        ("S7_vocab", "hapax_fraction", "S7 hapax fraction"),
        ("S7_vocab", "heaps_alpha", "S7 Heaps alpha"),
        ("S6_cascade_beta", "beta_fit", "S6 cascade-beta stretched-exp"),
    ]

    print("\n  === Cross-modal vs within-modal variance ratios ===\n")
    print(f"  {'Signature':<45} {'b/w_ratio':>10} {'verdict':<35}")
    print(f"  {'-'*45} {'-'*10} {'-'*35}")

    for sig_key, subkey, label in sigs_to_summarise:
        per_mod = per_modality_summary(records, sig_key, subkey)
        grand_mean, grand_std, cv = cross_modal_cv(per_mod)
        anova = anova_ratio(records, sig_key, subkey)
        ratio = anova.get("between_over_within", float("nan"))
        verdict = anova.get("verdict", "?")
        print(f"  {label:<45} {ratio:>10.3f} {verdict:<35}")
        synthesis_records.append(
            {
                "date": "2026-05-17",
                "spike": "43c",
                "kind": "cross_modal_summary",
                "signature": f"{sig_key}.{subkey}",
                "label": label,
                "per_modality": per_mod,
                "grand_mean_of_means": grand_mean,
                "grand_std_of_means": grand_std,
                "cv_of_means": cv,
                "anova_between_over_within": ratio,
                "verdict": verdict,
            }
        )

    # K_k shape investigation
    print("\n  === K_k shape investigation per substrate ===\n")
    kk_records = investigate_kk_shape(records)
    print(f"  {'Substrate':<55} {'modality':<14} {'zipf_s':>7} {'zipf_r2':>7} {'kepler_r2':>9} {'best':<10}")
    for kk in kk_records:
        print(
            f"  {kk['substrate']:<55} {kk['modality']:<14} "
            f"{kk['zipf_s_fit']:>7.3f} {kk['zipf_r2']:>7.3f} {kk['kepler_r2']:>9.3f} "
            f"{kk['best_model']:<10}"
        )
        synthesis_records.append(
            {
                "date": "2026-05-17",
                "spike": "43c",
                "kind": "kk_shape",
                **kk,
            }
        )

    # K_k best-model tally per modality
    by_mod_best = collections.defaultdict(collections.Counter)
    for kk in kk_records:
        by_mod_best[kk["modality"]][kk["best_model"]] += 1
    print("\n  === K_k best model tally per modality ===\n")
    for mod, ctr in by_mod_best.items():
        print(f"  {mod:<14} {dict(ctr)}")
        synthesis_records.append(
            {
                "date": "2026-05-17",
                "spike": "43c",
                "kind": "kk_best_model_tally",
                "modality": mod,
                "tally": dict(ctr),
            }
        )

    # Iceberg-foresight markers
    print("\n  === Iceberg-foresight markers (cross-modal P10..P90 well-spread bands) ===\n")
    iceberg = cross_modal_iceberg_markers(records)
    for sig_name, band in iceberg.items():
        print(
            f"  {sig_name:<45} P10={band['p10']:>8.4f}  median={band['median']:>8.4f}  "
            f"P90={band['p90']:>8.4f}"
        )
        synthesis_records.append(
            {
                "date": "2026-05-17",
                "spike": "43c",
                "kind": "iceberg_band_cross_modal",
                "signature": sig_name,
                **band,
            }
        )

    # Per-modality iceberg bands (modality-specific K_k binding)
    per_mod_bands = per_modality_iceberg_bands(records)
    for mod, sigs in per_mod_bands.items():
        synthesis_records.append(
            {
                "date": "2026-05-17",
                "spike": "43c",
                "kind": "iceberg_band_per_modality",
                "modality": mod,
                "bands": sigs,
            }
        )

    # Modality-pairwise distance: do modalities cluster?
    mods = sorted(set(r["modality"] for r in records))
    sig_for_dist = [
        ("R1_kladder", "eps_unbiased_fit"),
        ("R2_para_pareto", "power_law_slope"),
        ("R3_rare_cascade", "propagation_rate"),
        ("R4_callbacks", "callbacks_per_1000_words"),
        ("S7_vocab", "hapax_fraction"),
        ("S7_vocab", "heaps_alpha"),
    ]
    mod_centroids = {}
    for mod in mods:
        cent = []
        for sig_key, subkey in sig_for_dist:
            vals = []
            for r in records:
                if r["modality"] != mod:
                    continue
                sig = r.get(sig_key, {})
                if isinstance(sig, dict) and sig.get("valid") and subkey in sig:
                    v = sig[subkey]
                    if isinstance(v, (int, float)) and not math.isnan(v):
                        vals.append(float(v))
            cent.append(statistics.mean(vals) if vals else 0.0)
        mod_centroids[mod] = cent
    # z-normalise each axis using cross-mod mean+std
    n_axes = len(sig_for_dist)
    means = [statistics.mean([mod_centroids[m][i] for m in mods]) for i in range(n_axes)]
    stds = [statistics.stdev([mod_centroids[m][i] for m in mods]) if len(mods) > 1 else 1.0 for i in range(n_axes)]
    z_centroids = {
        m: [
            (mod_centroids[m][i] - means[i]) / (stds[i] if stds[i] > 0 else 1.0)
            for i in range(n_axes)
        ]
        for m in mods
    }
    distances = {}
    print("\n  === Pairwise modality distance in z-normalised feature space ===\n")
    print(f"  {'mod_a':<15} {'mod_b':<15} {'distance':>10}")
    for i, ma in enumerate(mods):
        for mb in mods[i + 1 :]:
            d = math.sqrt(sum((z_centroids[ma][k] - z_centroids[mb][k]) ** 2 for k in range(n_axes)))
            distances[(ma, mb)] = d
            print(f"  {ma:<15} {mb:<15} {d:>10.3f}")
            synthesis_records.append(
                {
                    "date": "2026-05-17",
                    "spike": "43c",
                    "kind": "modality_pairwise_distance",
                    "mod_a": ma,
                    "mod_b": mb,
                    "distance": d,
                    "axes": [k[0] + "." + k[1] for k in sig_for_dist],
                }
            )

    # Verdict
    print("\n  === SYNTHESIS VERDICT ===\n")
    # Find which signatures are universal (low b/w ratio) vs modality-specific (high b/w)
    universal = []
    modality_specific = []
    mixed = []
    for sig_key, subkey, label in sigs_to_summarise:
        anova = anova_ratio(records, sig_key, subkey)
        if not anova.get("valid"):
            continue
        ratio = anova["between_over_within"]
        if ratio < 0.5:
            universal.append((label, ratio))
        elif ratio > 2.0:
            modality_specific.append((label, ratio))
        else:
            mixed.append((label, ratio))
    print("  UNIVERSAL (b/w < 0.5):")
    for lab, r in universal:
        print(f"    {lab} (b/w={r:.3f})")
    print("  MIXED (0.5 < b/w < 2.0):")
    for lab, r in mixed:
        print(f"    {lab} (b/w={r:.3f})")
    print("  MODALITY-SPECIFIC (b/w > 2.0):")
    for lab, r in modality_specific:
        print(f"    {lab} (b/w={r:.3f})")
    synthesis_records.append(
        {
            "date": "2026-05-17",
            "spike": "43c",
            "kind": "synthesis_verdict",
            "universal_signatures": [{"label": lab, "between_over_within": r} for lab, r in universal],
            "modality_specific_signatures": [{"label": lab, "between_over_within": r} for lab, r in modality_specific],
            "mixed_signatures": [{"label": lab, "between_over_within": r} for lab, r in mixed],
        }
    )

    out_path = OUT_DIR / "spike_43c_synthesis_records_2026-05-17.ndjson"
    with out_path.open("w", encoding="utf-8") as f:
        for rec in synthesis_records:
            f.write(json.dumps(rec, default=str) + "\n")
    print(f"\n  [write] {out_path}  ({len(synthesis_records)} records)")


if __name__ == "__main__":
    main()

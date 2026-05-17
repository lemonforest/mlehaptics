"""
Spike #43c — Anomaly investigation + falsifier verification.

Investigation queue:

A1: K_k universality claim — does the universal Zipf-s ≈ -0.95 hold for negative controls?
    If C5 (LLM-flat), C4 (linear enumeration), C3 (word salad) ALSO have s ≈ -0.95, then
    the "shape" is just Zipf's law and NOT load-bearing for well-spread knowledge.
    If negative controls BREAK the pattern, then the universal IS load-bearing.

A2: Why is M3 LECTURES so far from M6 ORAL despite both being short-form pedagogy?
    Inspect feature contributions to the distance.

A3: Are there modalities where R4 is genuinely zero? Code (M5) is low; oral (M6) is very
    low; what's the cascade-equivalent in those modalities? Investigation: code uses
    cross-function CALLS not natural-language callbacks; oral uses repetition (already
    measured by O1). Check whether O1 + cross-modal-R4-or-equivalent constitutes a unified
    cascade signature.

A4: Books vs Papers: M1 books are at distance 3.6 from M2 papers. Driving features?
"""

from __future__ import annotations

import collections
import json
import math
import statistics
from pathlib import Path
from spike_43c_signature_analysis import (
    r1_word_freq_kladder,
    r2_paragraph_length_pareto,
    r3_rare_word_cascade,
    r4_callback_density,
    s3_zipf,
    s7_vocab_richness,
    s6_concept_intro_rate,
    o1_repetition_density,
    o2_rhyme_regularity,
)


OUT_DIR = Path(r"D:\temp\spike_43c")
CONTROLS_DIR = Path(r"D:\temp\spike_43")


CONTROLS = {
    "C1_paragraph_permute_mfo": CONTROLS_DIR / "C1_paragraph_permute_mfo.md",
    "C2_concatenated_unrelated": CONTROLS_DIR / "C2_concatenated_unrelated.md",
    "C3_word_salad_mfo": CONTROLS_DIR / "C3_word_salad_mfo.md",
    "C4_linear_enumeration": CONTROLS_DIR / "C4_linear_enumeration.md",
    "C5_llm_generated_flat": CONTROLS_DIR / "C5_llm_generated_flat.md",
}


def fit_kk_shape(K_k):
    """Fit log K_k = a + s * log k; return zipf-s + r2."""
    if not K_k or len(K_k) < 4:
        return {"valid": False}
    ks = list(range(1, len(K_k) + 1))
    log_k = [math.log(k) for k in ks]
    log_Kk = [math.log(max(abs(K_k[i]), 1e-12)) for i in range(len(K_k))]
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
    r2 = 1.0 - ss_res / ss_tot if ss_tot else 0.0
    return {"valid": True, "zipf_s_fit": s_fit, "zipf_r2": r2}


def main() -> None:
    records = []

    # ---- A1: K_k universality on negative controls ----
    print("\n  === A1: K_k universality on negative controls ===\n")
    print(f"  {'Substrate':<35} {'eps':>7} {'R1_r2':>7} {'zipf_s':>7} {'zipf_r2':>8} {'r4/1k':>7} {'r3rate':>7} {'hapax':>7}")
    a1_records = []
    for name, path in CONTROLS.items():
        if not path.exists():
            print(f"  [skip] {name} (no file)")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        r1 = r1_word_freq_kladder(text)
        if not r1.get("valid"):
            print(f"  [skip] {name} (R1 invalid)")
            continue
        kk_fit = fit_kk_shape(r1.get("K_k_substrate", []))
        r4 = r4_callback_density(text)
        r3 = r3_rare_word_cascade(text)
        s7 = s7_vocab_richness(text)
        print(
            f"  {name:<35} {r1['eps_unbiased_fit']:>7.4f} {r1['r2']:>7.3f} "
            f"{kk_fit.get('zipf_s_fit', float('nan')):>7.3f} {kk_fit.get('zipf_r2', float('nan')):>8.3f} "
            f"{r4.get('callbacks_per_1000_words', float('nan')):>7.2f} "
            f"{r3.get('propagation_rate', float('nan')):>7.3f} "
            f"{s7.get('hapax_fraction', float('nan')):>7.3f}"
        )
        a1_records.append(
            {
                "kind": "A1_kk_negative_control",
                "control": name,
                "eps_unbiased_fit": r1["eps_unbiased_fit"],
                "K_k_substrate": r1["K_k_substrate"],
                "zipf_s_fit": kk_fit.get("zipf_s_fit"),
                "zipf_r2": kk_fit.get("zipf_r2"),
                "r4_callbacks_per_1000": r4.get("callbacks_per_1000_words"),
                "r3_propagation_rate": r3.get("propagation_rate"),
                "s7_hapax_fraction": s7.get("hapax_fraction"),
            }
        )

    # Compare to well-spread (good) K_k cluster
    sig_path = OUT_DIR / "spike_43c_signature_records_2026-05-17.ndjson"
    good_records = [json.loads(line) for line in sig_path.open("r", encoding="utf-8")]
    good_zipf_s = []
    for r in good_records:
        K_k = r["R1_kladder"].get("K_k_substrate", [])
        kk = fit_kk_shape(K_k)
        if kk.get("valid"):
            good_zipf_s.append(kk["zipf_s_fit"])

    control_zipf_s = [rec["zipf_s_fit"] for rec in a1_records if rec.get("zipf_s_fit") is not None]
    print(f"\n  Well-spread substrates: n={len(good_zipf_s)}  mean zipf_s = {statistics.mean(good_zipf_s):.4f}  "
          f"std = {statistics.stdev(good_zipf_s):.4f}")
    if control_zipf_s:
        print(f"  Negative controls:      n={len(control_zipf_s)}  mean zipf_s = {statistics.mean(control_zipf_s):.4f}  "
              f"std = {statistics.stdev(control_zipf_s):.4f}")
    # Cohen's d-like separation
    if good_zipf_s and control_zipf_s and len(good_zipf_s) > 1 and len(control_zipf_s) > 1:
        good_mean = statistics.mean(good_zipf_s)
        ctrl_mean = statistics.mean(control_zipf_s)
        pooled_std = math.sqrt(
            (statistics.variance(good_zipf_s) + statistics.variance(control_zipf_s)) / 2
        )
        cohen_d = (good_mean - ctrl_mean) / pooled_std if pooled_std else float("inf")
        print(f"  Cohen's d (good vs control on zipf_s):  {cohen_d:.3f}")

    a1_records.append(
        {
            "kind": "A1_kk_summary",
            "good_zipf_s_mean": statistics.mean(good_zipf_s),
            "good_zipf_s_std": statistics.stdev(good_zipf_s) if len(good_zipf_s) > 1 else 0,
            "control_zipf_s_mean": statistics.mean(control_zipf_s) if control_zipf_s else None,
            "control_zipf_s_std": statistics.stdev(control_zipf_s) if len(control_zipf_s) > 1 else 0,
            "good_n": len(good_zipf_s),
            "control_n": len(control_zipf_s),
        }
    )

    # ---- A2: M3 LECTURES vs M6 ORAL distance — driving features ----
    print("\n  === A2: Why is M3 LECTURES so far from M6 ORAL? Feature-contribution analysis ===\n")
    # Compute per-modality feature means + identify which feature drives distance
    sig_keys = [
        ("R1_kladder", "eps_unbiased_fit"),
        ("R2_para_pareto", "power_law_slope"),
        ("R3_rare_cascade", "propagation_rate"),
        ("R4_callbacks", "callbacks_per_1000_words"),
        ("S7_vocab", "hapax_fraction"),
        ("S7_vocab", "heaps_alpha"),
    ]

    def feature_vec(mod: str) -> list[float]:
        v = []
        for sig_key, subkey in sig_keys:
            vals = []
            for r in good_records:
                if r["modality"] != mod:
                    continue
                sig = r.get(sig_key, {})
                if isinstance(sig, dict) and sig.get("valid") and subkey in sig:
                    val = sig[subkey]
                    if isinstance(val, (int, float)) and not math.isnan(val):
                        vals.append(float(val))
            v.append(statistics.mean(vals) if vals else 0.0)
        return v

    m3 = feature_vec("M3_LECTURES")
    m6 = feature_vec("M6_ORAL")
    contribs = []
    for i, (sk, subk) in enumerate(sig_keys):
        delta = m3[i] - m6[i]
        contribs.append((sk + "." + subk, delta, m3[i], m6[i]))
        print(f"    {sk + '.' + subk:<45} M3={m3[i]:>8.4f} M6={m6[i]:>8.4f} delta={delta:>8.4f}")
    records.append(
        {
            "kind": "A2_M3_vs_M6_features",
            "M3_LECTURES_feature_vec": m3,
            "M6_ORAL_feature_vec": m6,
            "feature_axes": [sk + "." + subk for sk, subk in sig_keys],
            "feature_deltas": [d[1] for d in contribs],
        }
    )

    # ---- A3: Cascade-equivalent in code (cross-function calls) and oral (repetition) ----
    print("\n  === A3: Cascade-equivalent across modalities (R4 alternative measures) ===\n")
    # For code substrates, the cross-function call density is the cascade equivalent.
    # For oral substrates, repetition density is the cascade equivalent.
    # Recompute these and report uniformly as "cascade_per_1000_units" where unit is word
    # for text/oral, lines for code.
    cascade_unified = []
    for r in good_records:
        mod = r["modality"]
        r4 = r.get("R4_callbacks", {})
        cascade_text = r4.get("callbacks_per_1000_words") if r4.get("valid") else None
        cascade_code_lines = None
        cascade_oral_rep = None
        if mod == "M5_CODE":
            c2 = r.get("C2_cross_func_calls", {})
            cascade_code_lines = c2.get("callbacks_per_1000_lines") if c2.get("valid") else None
        if mod == "M6_ORAL":
            o1 = r.get("O1_repetition", {})
            cascade_oral_rep = o1.get("repeated_3gram_density_per_1k") if o1.get("valid") else None
        # Unified score: R4 + modality-bonus
        unified = (cascade_text or 0) + (cascade_code_lines or 0) + (cascade_oral_rep or 0)
        cascade_unified.append(
            {
                "substrate": r["substrate"],
                "modality": mod,
                "R4_callbacks_per_1000": cascade_text,
                "C2_cross_func_per_1000": cascade_code_lines,
                "O1_repeated_3gram_per_1k": cascade_oral_rep,
                "unified_cascade_per_1000": unified,
            }
        )
        print(
            f"    {r['substrate']:<55} {mod:<14} "
            f"R4={cascade_text or 0:>6.2f} C2={cascade_code_lines or 0:>7.2f} "
            f"O1={cascade_oral_rep or 0:>7.2f} unified={unified:>7.2f}"
        )
    records.extend(
        [{"kind": "A3_unified_cascade", **r} for r in cascade_unified]
    )

    # ---- A4: Books vs Papers — feature contributions ----
    print("\n  === A4: Books (M1) vs Papers (M2) distance contribution ===\n")
    m1 = feature_vec("M1_BOOKS_PROSE")
    m2 = feature_vec("M2_PAPERS")
    contribs_12 = []
    for i, (sk, subk) in enumerate(sig_keys):
        delta = m1[i] - m2[i]
        contribs_12.append((sk + "." + subk, delta, m1[i], m2[i]))
        print(f"    {sk + '.' + subk:<45} M1={m1[i]:>8.4f} M2={m2[i]:>8.4f} delta={delta:>8.4f}")
    records.append(
        {
            "kind": "A4_M1_vs_M2_features",
            "M1_BOOKS_PROSE_feature_vec": m1,
            "M2_PAPERS_feature_vec": m2,
            "feature_axes": [sk + "." + subk for sk, subk in sig_keys],
            "feature_deltas": [d[1] for d in contribs_12],
        }
    )

    # ---- Write all anomaly records ----
    out_path = OUT_DIR / "spike_43c_anomaly_records_2026-05-17.ndjson"
    all_recs = a1_records + records
    with out_path.open("w", encoding="utf-8") as f:
        for rec in all_recs:
            rec["date"] = "2026-05-17"
            rec["spike"] = "43c"
            f.write(json.dumps(rec, default=str) + "\n")
    print(f"\n  [write] {out_path}  ({len(all_recs)} records)")


if __name__ == "__main__":
    main()

"""
Spike #43c — Cascade universal verification (final falsifier).

Test the cascade hypothesis: well-spread knowledge has substrate-specific cascade
machinery, and the CASCADE is universal even if the mechanism is modality-specific.

For each modality, compute:
  - R4 (callbacks/1k words) for text
  - C2 (cross-function uses per 1k lines) for code
  - O1 (repeated 3-gram density per 1k words) for oral

Negative controls (C3/C4/C5): expect cascade to be LOW (these are flat / random).
Well-spread substrates: expect cascade to be HIGH on the relevant axis.

The cascade-shape universal: well-spread knowledge has a HEAVY-TAILED cascade-event
distribution. Test this on:
  - cascade event rank-frequency Pareto
  - cascade-feature mean
"""

from __future__ import annotations

import collections
import json
import math
import re
import statistics
from pathlib import Path

from spike_43c_signature_analysis import (
    r3_rare_word_cascade,
    r4_callback_density,
    c2_cross_function_call_density,
    o1_repetition_density,
    tokenize_words,
    STOPWORDS,
)


OUT_DIR = Path(r"D:\temp\spike_43c")
CONTROLS_DIR = Path(r"D:\temp\spike_43")
CORPUS_DIR = OUT_DIR / "corpus"


def detect_modality(name: str) -> str:
    if name.startswith("C"):
        return "NEGATIVE_CONTROL"
    return name.split("_")[0] if "_" in name else "UNKNOWN"


def detect_lang_for_code(name: str) -> str:
    if name.endswith("functools"):
        return "PY"
    return "C"


def unified_cascade_score(name: str, text: str) -> dict:
    """Compute the unified cascade score appropriate to the modality."""
    mod_prefix = name.split("_")[0] if "_" in name else name
    r4 = r4_callback_density(text)
    r3 = r3_rare_word_cascade(text)
    cascade_score = r4.get("callbacks_per_1000_words", 0) if r4.get("valid") else 0

    # For code, ALSO add C2 in scaled units (lines vs words)
    c2_score = 0
    if mod_prefix == "M5":
        lang = detect_lang_for_code(name)
        c2 = c2_cross_function_call_density(text, lang)
        c2_score = c2.get("callbacks_per_1000_lines", 0) if c2.get("valid") else 0

    # For oral, add O1 repetition
    o1_score = 0
    if mod_prefix == "M6":
        o1 = o1_repetition_density(text)
        o1_score = o1.get("repeated_3gram_density_per_1k", 0) if o1.get("valid") else 0

    # Universal cascade score = sum of modality-appropriate cascade measures
    return {
        "r4_per_1k_words": cascade_score,
        "r3_propagation_rate": r3.get("propagation_rate", 0) if r3.get("valid") else 0,
        "c2_per_1k_lines": c2_score,
        "o1_3gram_per_1k": o1_score,
        "modality_prefix": mod_prefix,
    }


def cascade_event_pareto(text: str, modality_prefix: str) -> dict:
    """The cascade event distribution: count each rare-word's # of appearances; rank-frequency Pareto fit.

    Hypothesis: well-spread has heavy-tailed cascade-event Pareto (a few rare words used
    many times, most used 2x). Negative controls: flat or absent cascade.
    """
    all_words = [w for w in tokenize_words(text) if w not in STOPWORDS and len(w) >= 5]
    counter = collections.Counter(all_words)
    # Take words appearing 2-100 times (cascade-event candidates)
    cascade_words = {w: c for w, c in counter.items() if 2 <= c <= 100}
    if len(cascade_words) < 20:
        return {"valid": False, "n_cascade_words": len(cascade_words)}
    freqs = sorted(cascade_words.values(), reverse=True)
    n = len(freqs)
    ranks = list(range(1, n + 1))
    log_r = [math.log(r) for r in ranks]
    log_f = [math.log(f) for f in freqs]
    mean_r = sum(log_r) / n
    mean_f = sum(log_f) / n
    cov = sum((log_r[i] - mean_r) * (log_f[i] - mean_f) for i in range(n))
    var = sum((log_r[i] - mean_r) ** 2 for i in range(n))
    slope = cov / var if var else 0.0
    pred = [mean_f + slope * (log_r[i] - mean_r) for i in range(n)]
    ss_res = sum((log_f[i] - pred[i]) ** 2 for i in range(n))
    ss_tot = sum((log_f[i] - mean_f) ** 2 for i in range(n))
    r2 = 1.0 - ss_res / ss_tot if ss_tot else 0.0
    return {
        "valid": True,
        "n_cascade_words": n,
        "cascade_pareto_slope": slope,
        "cascade_pareto_r2": r2,
        "max_freq": freqs[0],
        "median_freq": freqs[n // 2],
    }


def main() -> None:
    print(f"  === Cascade universal verification ===\n")

    # Load well-spread substrates
    sig_path = OUT_DIR / "spike_43c_signature_records_2026-05-17.ndjson"
    well_spread = []
    with sig_path.open("r", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            well_spread.append(r["substrate"])

    # Load text for each well-spread substrate
    cascade_records = []

    print(f"  {'Substrate':<55} {'mod':<15} {'r4/1k':>7} {'r3rate':>7} {'r2_pareto_slope':>16} {'r2_pareto_r2':>13}")
    for name in well_spread:
        text_path = CORPUS_DIR / f"{name}.txt"
        if not text_path.exists():
            continue
        text = text_path.read_text(encoding="utf-8", errors="replace")
        u = unified_cascade_score(name, text)
        p = cascade_event_pareto(text, u["modality_prefix"])
        rec = {
            "substrate": name,
            "modality": u["modality_prefix"],
            "is_well_spread": True,
            **u,
            "cascade_pareto_slope": p.get("cascade_pareto_slope"),
            "cascade_pareto_r2": p.get("cascade_pareto_r2"),
            "cascade_pareto_valid": p.get("valid", False),
        }
        cascade_records.append(rec)
        print(
            f"  {name:<55} {u['modality_prefix']:<15} "
            f"{u['r4_per_1k_words']:>7.2f} {u['r3_propagation_rate']:>7.3f} "
            f"{p.get('cascade_pareto_slope', float('nan')):>16.3f} "
            f"{p.get('cascade_pareto_r2', float('nan')):>13.3f}"
        )

    # Load negative controls
    controls = {
        "C1_paragraph_permute_mfo": CONTROLS_DIR / "C1_paragraph_permute_mfo.md",
        "C2_concatenated_unrelated": CONTROLS_DIR / "C2_concatenated_unrelated.md",
        "C3_word_salad_mfo": CONTROLS_DIR / "C3_word_salad_mfo.md",
        "C4_linear_enumeration": CONTROLS_DIR / "C4_linear_enumeration.md",
        "C5_llm_generated_flat": CONTROLS_DIR / "C5_llm_generated_flat.md",
    }
    print("\n  --- Negative controls ---")
    for name, path in controls.items():
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        u = unified_cascade_score(name, text)
        p = cascade_event_pareto(text, "NEGATIVE_CONTROL")
        rec = {
            "substrate": name,
            "modality": "NEGATIVE_CONTROL",
            "is_well_spread": False,
            **u,
            "cascade_pareto_slope": p.get("cascade_pareto_slope"),
            "cascade_pareto_r2": p.get("cascade_pareto_r2"),
            "cascade_pareto_valid": p.get("valid", False),
        }
        cascade_records.append(rec)
        print(
            f"  {name:<55} {'NEG_CTRL':<15} "
            f"{u['r4_per_1k_words']:>7.2f} {u['r3_propagation_rate']:>7.3f} "
            f"{p.get('cascade_pareto_slope', float('nan')):>16.3f} "
            f"{p.get('cascade_pareto_r2', float('nan')):>13.3f}"
        )

    # Stats: cascade Pareto slope — well-spread vs negative
    well_slopes = [r["cascade_pareto_slope"] for r in cascade_records if r["is_well_spread"] and r.get("cascade_pareto_valid")]
    neg_slopes = [r["cascade_pareto_slope"] for r in cascade_records if not r["is_well_spread"] and r.get("cascade_pareto_valid")]

    print(f"\n  Well-spread cascade-Pareto slope: n={len(well_slopes)}  mean={statistics.mean(well_slopes):.3f}  "
          f"std={statistics.stdev(well_slopes):.3f}")
    if neg_slopes:
        print(f"  Negative-control slope:           n={len(neg_slopes)}  mean={statistics.mean(neg_slopes):.3f}  "
              f"std={statistics.stdev(neg_slopes):.3f}")

    # R3 rare-cascade propagation
    well_r3 = [r["r3_propagation_rate"] for r in cascade_records if r["is_well_spread"]]
    neg_r3 = [r["r3_propagation_rate"] for r in cascade_records if not r["is_well_spread"]]
    print(f"\n  Well-spread R3 propagation: n={len(well_r3)}  mean={statistics.mean(well_r3):.3f}  std={statistics.stdev(well_r3):.3f}")
    if neg_r3:
        print(f"  Negative-control R3:        n={len(neg_r3)}  mean={statistics.mean(neg_r3):.3f}  std={statistics.stdev(neg_r3):.3f}")
        # Cohen's d
        pooled = math.sqrt((statistics.variance(well_r3) + statistics.variance(neg_r3)) / 2)
        d = (statistics.mean(well_r3) - statistics.mean(neg_r3)) / pooled if pooled else float("inf")
        print(f"  Cohen's d (R3 well-spread vs negative): {d:.3f}")

    # Cascade scale by modality (across all positive substrates)
    print("\n  --- Cascade scale per modality (across modality-appropriate measures) ---\n")
    by_mod_max = collections.defaultdict(list)
    for r in cascade_records:
        if not r["is_well_spread"]:
            continue
        mod = r["modality"]
        # Each modality has its own primary cascade measure
        if mod in ("M1", "M2", "M3", "M4", "M7"):
            score = r["r4_per_1k_words"]
        elif mod == "M5":
            score = r["c2_per_1k_lines"]
        elif mod == "M6":
            score = r["o1_3gram_per_1k"]
        else:
            score = 0
        by_mod_max[mod].append(score)
    for mod, scores in sorted(by_mod_max.items()):
        print(f"  {mod}: n={len(scores)}  mean modality-cascade={statistics.mean(scores):.3f}  range=[{min(scores):.3f}, {max(scores):.3f}]")

    # Write
    out_path = OUT_DIR / "spike_43c_cascade_records_2026-05-17.ndjson"
    with out_path.open("w", encoding="utf-8") as f:
        for rec in cascade_records:
            rec["date"] = "2026-05-17"
            rec["spike"] = "43c"
            f.write(json.dumps(rec, default=str) + "\n")
    print(f"\n  [write] {out_path}  ({len(cascade_records)} records)")


if __name__ == "__main__":
    main()

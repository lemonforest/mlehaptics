"""R-RBS-LM-82 — Alignment-entropy test for Finding 96.

Test: are Arts cross-domain coupling cascades (high entropy across
substrate-classes) or irreducible substrate-classes (low entropy
concentrated in one class)?

Method:
  For each corpus, compute Shannon entropy of its alignment-score
  distribution across substrate-classes (excluding self-class).

  H(corpus) = -Σ_class p(class) * log2(p(class))

  where p(class) = normalized alignment of corpus to members of class.

Prediction per Finding 96 (Arts as cross-domain cascade):
  Math:     LOW entropy (concentrate on math)
  Reading:  MODERATE entropy (narrative broadly shared)
  Science:  MODERATE entropy
  Grammar:  MODERATE entropy (instruction kinship spreads)
  Arts:     HIGH entropy (cross-domain coupling)

If Arts entropy > non-arts entropy by significant margin → Finding 96
CONFIRMED.

Reuses the 27-corpus pairwise alignment data from R-RBS-LM-80. Loads
results from R-RBS-LM-80_results.json to avoid recomputation.
"""

import json
import re
from collections import Counter
from pathlib import Path

import numpy as np


HERE = Path(__file__).parent
RESULTS_80 = HERE / "R-RBS-LM-80_results.json"


def main():
    print(f"=== R-RBS-LM-82 — Alignment-entropy test for Finding 96 ===\n")

    if not RESULTS_80.exists():
        print(f"ERROR: {RESULTS_80} not found. Run R-RBS-LM-80 first.")
        return

    data = json.loads(RESULTS_80.read_text())
    corpora_info = data["corpora"]
    pairwise = data["pairwise_alignments"]

    # Lookup helper for pairwise (keys are "a|b" strings with sorted ordering)
    def get_alignment(a, b):
        key = "|".join(sorted([a, b]))
        return pairwise.get(key, 0.0)

    # Group corpora by subject
    keys_by_subject = {}
    subject_of = {}
    for k, info in corpora_info.items():
        sj = info["subject"]
        subject_of[k] = sj
        keys_by_subject.setdefault(sj, []).append(k)

    subjects_list = sorted(keys_by_subject.keys())
    print(f"Subjects: {subjects_list}")
    print(f"Corpora per subject:")
    for sj in subjects_list:
        print(f"  {sj}: {len(keys_by_subject[sj])} ({keys_by_subject[sj]})")

    # Compute per-corpus alignment distribution + entropy
    print(f"\n=== Per-corpus alignment-class distribution + Shannon entropy ===\n")
    print(f"  {'corpus':<28s} | {'subject':<16s} | distribution per class                              | H (bits)")
    print(f"  {'-'*28}-+-{'-'*16}-+-{'-'*52}-+-{'-'*8}")

    entropy_records = []
    for k, info in corpora_info.items():
        own_subject = info["subject"]
        own_label = info["label"]
        # For each subject-class INCLUDING own (excluding only self-pair), compute
        # mean alignment to members of that class. Including own-class is crucial:
        # math should show HIGH concentration to math itself; arts should show
        # SPREAD across many classes.
        class_means = {}
        for sj in subjects_list:
            members = [m for m in keys_by_subject[sj] if m != k]
            if not members: continue
            sims = [get_alignment(k, m) for m in members]
            class_means[sj] = float(np.mean(sims))
        # Normalize to probability distribution
        total = sum(class_means.values())
        if total == 0:
            ent = 0.0; probs = {}
        else:
            probs = {sj: v/total for sj, v in class_means.items()}
            ent = -sum(p * np.log2(p) for p in probs.values() if p > 0)
        # Show top-3 classes
        sorted_classes = sorted(probs.items(), key=lambda x: -x[1])[:3]
        cls_str = ", ".join([f"{sj[:6]}={p:.2f}" for sj, p in sorted_classes])
        marker = "*" if own_subject in ("music","art","scouting","games","sports","cooking") else " "
        print(f"  {own_label:<28s} | {own_subject:<16s} | {cls_str:<52s} | {ent:.3f} {marker}")
        entropy_records.append({"key": k, "label": own_label, "subject": own_subject,
                                  "class_distribution": probs, "entropy": ent})

    # Per-subject entropy averages
    print(f"\n=== Per-subject mean entropy ===\n")
    print(f"  {'subject':<18s} {'n_members':>9s} {'mean entropy':>14s} {'std':>8s} {'min':>8s} {'max':>8s}")
    subject_entropy = {}
    for sj in subjects_list:
        ents = [r["entropy"] for r in entropy_records if r["subject"] == sj]
        if not ents: continue
        mean_h = float(np.mean(ents))
        std_h = float(np.std(ents)) if len(ents) > 1 else 0.0
        min_h = float(min(ents)); max_h = float(max(ents))
        subject_entropy[sj] = {"mean": mean_h, "std": std_h, "n": len(ents)}
        print(f"  {sj:<18s} {len(ents):>9d} {mean_h:>14.4f} {std_h:>8.4f} {min_h:>8.4f} {max_h:>8.4f}")

    # Rank subjects by mean entropy
    print(f"\n=== Subjects ranked by mean alignment-entropy ===\n")
    ranked = sorted(subject_entropy.items(), key=lambda x: -x[1]["mean"])
    print(f"  rank | subject            | n | mean H    | interpretation")
    for rank, (sj, st) in enumerate(ranked, 1):
        marker = "*" if sj in ("music","art","scouting","games","sports","cooking") else " "
        print(f"  {rank:>3d}  | {sj:<18s} | {st['n']:>1d} | {st['mean']:>+8.4f} |{marker}")

    # Hypothesis test: is Arts entropy higher than non-Arts on average?
    print(f"\n=== Finding 96 falsification test ===\n")
    arts_keys = ("music", "art", "scouting", "games", "sports", "cooking")  # extra-curricular subjects (proxy for Arts/cross-domain)
    formal_keys = ("reading", "grammar_hist", "composition_mod", "math", "science", "history", "geography")

    arts_ents = [r["entropy"] for r in entropy_records if r["subject"] in arts_keys]
    formal_ents = [r["entropy"] for r in entropy_records if r["subject"] in formal_keys]

    arts_mean = float(np.mean(arts_ents)) if arts_ents else 0.0
    formal_mean = float(np.mean(formal_ents)) if formal_ents else 0.0

    print(f"  Arts/extracurricular corpora (n={len(arts_ents)}): mean entropy = {arts_mean:.4f}")
    print(f"  Formal-academic corpora    (n={len(formal_ents)}): mean entropy = {formal_mean:.4f}")
    print(f"  Difference (arts - formal): {arts_mean - formal_mean:+.4f}")

    # Specifically check the "art" subject (perspective + drawing)
    art_only_ents = [r["entropy"] for r in entropy_records if r["subject"] == "art"]
    math_ents = [r["entropy"] for r in entropy_records if r["subject"] == "math"]
    reading_ents = [r["entropy"] for r in entropy_records if r["subject"] == "reading"]
    print(f"\n  ART subject (n={len(art_only_ents)}):  mean entropy = {np.mean(art_only_ents):.4f}" if art_only_ents else "")
    print(f"  MATH subject (n={len(math_ents)}): mean entropy = {np.mean(math_ents):.4f}" if math_ents else "")
    print(f"  READING subject (n={len(reading_ents)}): mean entropy = {np.mean(reading_ents):.4f}" if reading_ents else "")

    print(f"\n=== Verdict ===")
    delta = arts_mean - formal_mean
    if delta > 0.20:
        verdict = f"FINDING 96 CONFIRMED: Arts/extra-curricular entropy {delta:+.3f} higher than formal-academic. Cross-domain coupling cascade signature visible."
    elif delta > 0.05:
        verdict = f"FINDING 96 PARTIAL: Arts entropy slightly higher ({delta:+.3f}); trend in expected direction but margin moderate"
    elif delta > -0.05:
        verdict = f"FINDING 96 NEUTRAL: Arts and formal-academic have comparable entropy (Δ={delta:+.3f}). Both compose substrates similarly."
    else:
        verdict = f"FINDING 96 FALSIFIED: Arts entropy LOWER than formal-academic (Δ={delta:+.3f}). Arts may be irrep after all."
    print(f"  {verdict}")

    # Top-3 distributions for art corpora specifically (qualitative inspection)
    print(f"\n=== Glass-box: where does each Arts/extra-curricular corpus distribute? ===")
    for r in entropy_records:
        if r["subject"] not in arts_keys: continue
        sorted_classes = sorted(r["class_distribution"].items(), key=lambda x: -x[1])[:5]
        cls_str = ", ".join([f"{sj}={p:.3f}" for sj, p in sorted_classes])
        print(f"  {r['label']:<28s} ({r['subject']:<8s}, H={r['entropy']:.3f}): {cls_str}")

    out = {
        "partition": "R-RBS-LM-82",
        "entropy_records": entropy_records,
        "subject_entropy": subject_entropy,
        "arts_mean_entropy": arts_mean,
        "formal_mean_entropy": formal_mean,
        "delta": delta,
        "verdict": verdict,
    }
    out_path = HERE / "R-RBS-LM-82_results.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()

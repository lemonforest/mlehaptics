"""
Spike #43 — Iterative refinement (MFO-style)

Iteration log captured here. Each step is a refinement of the methodology
based on what the prior step's data revealed.

Discipline: math doesn't lie. Iterate the test, not the verdict.
"""

from __future__ import annotations

import collections
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from spike_43_literature_spectral_analysis import (  # type: ignore
    tokenize_chapters,
    tokenize_paragraphs,
    tokenize_sentences,
    tokenize_words,
    STOPWORDS,
)


GOOD_PATHS = {
    "mfo_notebook": r"D:\GitHub\mlehaptics\docs\antikythera-maths\mfo_spectral_research_notebook.md",
    "srmech_notebook": r"D:\GitHub\mlehaptics\docs\srmech\srmech_research_notebook.md",
    "spike_38b": r"D:\GitHub\mlehaptics\docs\srmech\notes\spike_38b_caffeine_form_function_remnants_2026-05-17.md",
    "spike_41": r"D:\GitHub\mlehaptics\docs\srmech\notes\spike_41_fibonacci_unity_2026-05-17.md",
    "spike_42": r"D:\GitHub\mlehaptics\docs\srmech\notes\spike_42_imprinting_cascade_entropy_reposture_2026-05-17.md",
}

CONTROL_PATHS = {
    "C1_paragraph_permute_mfo": r"D:\temp\spike_43\C1_paragraph_permute_mfo.md",
    "C2_concatenated_unrelated": r"D:\temp\spike_43\C2_concatenated_unrelated.md",
    "C3_word_salad_mfo": r"D:\temp\spike_43\C3_word_salad_mfo.md",
    "C4_linear_enumeration": r"D:\temp\spike_43\C4_linear_enumeration.md",
    "C5_llm_generated_flat": r"D:\temp\spike_43\C5_llm_generated_flat.md",
}


# ------------------------------------------------------------------------
# Refinement step R1 — K-ladder on word-frequency tail
# ------------------------------------------------------------------------


def r1_word_freq_kladder(text: str, k_max: int = 6) -> dict:
    """K-ladder fit on TOP-(k_max+1) word frequencies (excl. stopwords).

    Rationale: top-frequency content words ARE the cascade — they're the recurring
    threads each chapter relies on. Spike #41's Cauchy-form c_k = eps^k * K_k applies
    here with K_k(text-substrate) as a discovery target.

    For a well-structured text: should fit a c_k = eps^k * K_k decay closely.
    """
    words = [w for w in tokenize_words(text) if w not in STOPWORDS and len(w) >= 4]
    counter = collections.Counter(words)
    most_common = counter.most_common(k_max + 1)
    if len(most_common) < k_max + 1:
        return {"valid": False}
    c0 = most_common[0][1]
    c = [most_common[i][1] / c0 for i in range(1, k_max + 1)]
    log_ck = [math.log(max(abs(c[i]), 1e-12)) for i in range(k_max)]
    log_ck_times_k = [log_ck[i] + math.log(i + 1) for i in range(k_max)]
    # fit log_ck_times_k = k * log(eps), k=1..k_max
    ks = list(range(1, k_max + 1))
    sum_k = sum(ks)
    sum_kk = sum(k * k for k in ks)
    sum_y = sum(log_ck_times_k)
    sum_ky = sum(ks[i] * log_ck_times_k[i] for i in range(k_max))
    log_eps = (k_max * sum_ky - sum_k * sum_y) / (k_max * sum_kk - sum_k * sum_k)
    eps_unbiased = math.exp(log_eps)
    K_k_substrate = [c[i] / (eps_unbiased ** (i + 1)) for i in range(k_max)]
    pred = [k * log_eps for k in ks]
    mean_y = sum(log_ck_times_k) / k_max
    ss_res = sum((log_ck_times_k[i] - pred[i]) ** 2 for i in range(k_max))
    ss_tot = sum((log_ck_times_k[i] - mean_y) ** 2 for i in range(k_max))
    r2 = 1.0 - ss_res / ss_tot if ss_tot else 0.0
    return {
        "valid": True,
        "top_words": [w for w, _ in most_common],
        "freqs": [n for _, n in most_common],
        "c_k": c,
        "eps_unbiased_fit": eps_unbiased,
        "K_k_substrate": K_k_substrate,
        "r2": r2,
        "in_physical_range": 0 < eps_unbiased <= 0.5,
    }


# ------------------------------------------------------------------------
# Refinement step R2 — Pareto / power-law fit on paragraph lengths
# ------------------------------------------------------------------------


def r2_paragraph_length_pareto(text: str) -> dict:
    """Fit Pareto/power-law to paragraph-length distribution.

    Well-structured text: paragraph lengths follow heavy-tail (a few long;
    most short). Power-law slope is the cascade-depth indicator.
    """
    chapters = tokenize_chapters(text)
    lengths = []
    for _, body in chapters:
        for p in tokenize_paragraphs(body):
            wl = len(tokenize_words(p))
            if wl >= 5:
                lengths.append(wl)
    if len(lengths) < 20:
        return {"valid": False, "n": len(lengths)}
    lengths.sort(reverse=True)
    n = len(lengths)
    # rank-frequency: log(length) vs log(rank)
    ranks = list(range(1, n + 1))
    log_r = [math.log(r) for r in ranks]
    log_l = [math.log(l) for l in lengths]
    mean_r = sum(log_r) / n
    mean_l = sum(log_l) / n
    cov = sum((log_r[i] - mean_r) * (log_l[i] - mean_l) for i in range(n))
    var = sum((log_r[i] - mean_r) ** 2 for i in range(n))
    slope = cov / var if var else 0.0
    intercept = mean_l - slope * mean_r
    pred = [intercept + slope * lr for lr in log_r]
    ss_res = sum((log_l[i] - pred[i]) ** 2 for i in range(n))
    ss_tot = sum((log_l[i] - mean_l) ** 2 for i in range(n))
    r2 = 1.0 - ss_res / ss_tot if ss_tot else 0.0
    # also: kurtosis-style measure of how peaked
    mean_l_raw = sum(lengths) / n
    var_l_raw = sum((l - mean_l_raw) ** 2 for l in lengths) / n
    std_l_raw = math.sqrt(var_l_raw)
    skew = sum((l - mean_l_raw) ** 3 for l in lengths) / (n * std_l_raw ** 3) if std_l_raw else 0.0
    return {
        "valid": True,
        "n_paragraphs": n,
        "max_length": lengths[0],
        "median_length": lengths[n // 2],
        "min_length": lengths[-1],
        "power_law_slope": slope,
        "power_law_r2": r2,
        "skew": skew,
        "max_over_median_ratio": lengths[0] / max(1, lengths[n // 2]),
    }


# ------------------------------------------------------------------------
# Refinement step R3 — Bigram cascade: do adjacent paragraphs share rare words?
# ------------------------------------------------------------------------


def r3_rare_word_cascade(text: str) -> dict:
    """How often does a rare-word (frequency-3-or-less) introduced in para N appear in para N+1?

    This is the Class C streaming + Class I cyclic cascade test. Well-written:
    rare technical terms introduced are propagated forward (build-up). Bad:
    rare terms appear orphaned, no follow-up.
    """
    chapters = tokenize_chapters(text)
    paragraphs = []
    for _, body in chapters:
        paragraphs.extend(tokenize_paragraphs(body))
    # global rare-word set
    all_words = [w for w in tokenize_words(text) if w not in STOPWORDS and len(w) >= 5]
    counter = collections.Counter(all_words)
    rare = {w for w, c in counter.items() if 2 <= c <= 5}
    if not rare:
        return {"valid": False, "reason": "no rare words"}
    intro_counts = 0
    propagated_counts = 0
    intro_seen: set[str] = set()
    for i, p in enumerate(paragraphs):
        words = set(tokenize_words(p)) & rare
        new_in_p = words - intro_seen
        for w in new_in_p:
            intro_counts += 1
            # check next 2 paragraphs
            if i + 1 < len(paragraphs):
                w_next1 = set(tokenize_words(paragraphs[i + 1]))
                if w in w_next1:
                    propagated_counts += 1
                    continue
            if i + 2 < len(paragraphs):
                w_next2 = set(tokenize_words(paragraphs[i + 2]))
                if w in w_next2:
                    propagated_counts += 1
        intro_seen |= new_in_p
    return {
        "valid": True,
        "rare_word_count": len(rare),
        "intro_count": intro_counts,
        "propagated_count": propagated_counts,
        "propagation_rate": propagated_counts / max(1, intro_counts),
    }


# ------------------------------------------------------------------------
# Refinement step R4 — Cross-chapter callback density
# ------------------------------------------------------------------------


_CALLBACK_PATTERNS = [
    r"as (?:we |I )?(?:showed|saw|noted|established|argued|stated|defined|introduced)",
    r"recall (?:from|that)",
    r"per (?:Spike|Section|Part|Chapter|§)",
    r"see (?:also |above |below |Spike|Section|Part|Chapter|§)",
    r"\[\[[^\]]+\]\]",  # wiki-style cross-reference
    r"per `\[\[",
    r"per (?:the )?\w+(?:-\w+)+",  # named-stance reference
    r"\(§[\d.]+",  # paren section reference
    r"§\s*[\d.]+",  # bare section reference
    r"PR #\d+|Bug #\d+|Spike #\d+|Task #\d+",  # numbered references
    r"in Chapter \d+",
]

import re as _re


def r4_callback_density(text: str) -> dict:
    """Count cross-reference callbacks per word.

    Well-written cascade-composition text has dense cross-references (each
    chapter cites prior chapters' results). Flat enumeration has near-zero.
    """
    n_words = len(tokenize_words(text))
    if n_words < 200:
        return {"valid": False}
    counts = {}
    total = 0
    for pat in _CALLBACK_PATTERNS:
        m = _re.findall(pat, text, _re.IGNORECASE)
        counts[pat[:30]] = len(m)
        total += len(m)
    return {
        "valid": True,
        "n_words": n_words,
        "callback_count_total": total,
        "callbacks_per_1000_words": (total / n_words) * 1000,
        "per_pattern_counts": counts,
    }


# ------------------------------------------------------------------------
# Refinement step R5 — Class L on PARAGRAPH-level graph (finer than chapter)
# ------------------------------------------------------------------------


def r5_paragraph_laplacian(text: str) -> dict:
    """Build Jaccard graph between paragraphs; Laplacian Fiedler.

    Finer-grained than chapter level. Reveals paragraph-to-paragraph coupling.
    Well-written: paragraphs form connected community; bad-text: scattered.

    For computational tractability, sample at most 100 paragraphs.
    """
    chapters = tokenize_chapters(text)
    paragraphs = []
    for _, body in chapters:
        paragraphs.extend(tokenize_paragraphs(body))
    n = len(paragraphs)
    if n < 10:
        return {"valid": False, "n": n}
    # sample uniformly
    n_sample = min(60, n)
    indices = [int(i * n / n_sample) for i in range(n_sample)]
    sample = [paragraphs[i] for i in indices]
    sets = []
    for p in sample:
        words = [w for w in tokenize_words(p) if w not in STOPWORDS and len(w) >= 4]
        sets.append(set(words))
    from spike_43_literature_spectral_analysis import jaccard, jacobi_eigvals_symmetric  # type: ignore

    ns = len(sets)
    W = [[0.0] * ns for _ in range(ns)]
    for i in range(ns):
        for j in range(i + 1, ns):
            w = jaccard(sets[i], sets[j])
            W[i][j] = w
            W[j][i] = w
    D = [sum(W[i]) for i in range(ns)]
    L = [[(D[i] if i == j else 0.0) - W[i][j] for j in range(ns)] for i in range(ns)]
    eigvals = jacobi_eigvals_symmetric(L, ns, max_iter=200)
    eigvals.sort()
    return {
        "valid": True,
        "n_paragraphs_sampled": ns,
        "lambda_1": eigvals[0],
        "fiedler_lambda_2": eigvals[1],
        "lambda_3": eigvals[2],
        "spectral_gap_2_3": eigvals[2] - eigvals[1],
        "mean_jaccard": sum(W[i][j] for i in range(ns) for j in range(i + 1, ns))
        / max(1, ns * (ns - 1) // 2),
        "n_zero_eigvals_near_zero": sum(1 for e in eigvals if abs(e) < 1e-6),
    }


# ------------------------------------------------------------------------
# Main: run all refinements on good + control substrates
# ------------------------------------------------------------------------


def main(out_dir: str) -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    all_substrates = {**GOOD_PATHS, **CONTROL_PATHS}
    records = []
    iteration_log_records = []
    print("\n  --- iteration step R1: word-frequency K-ladder ---\n")
    for name, path in all_substrates.items():
        if not Path(path).exists():
            print(f"  [skip] {name}")
            continue
        text = Path(path).read_text(encoding="utf-8")
        r1 = r1_word_freq_kladder(text)
        records.append({"date": "2026-05-17", "substrate": name, "step": "R1_word_freq_kladder", "result": r1})
        if r1.get("valid"):
            print(
                f"  {name:<30} eps={r1['eps_unbiased_fit']:.4f}  r2={r1['r2']:.4f}  "
                f"top={r1['top_words'][:5]}"
            )

    iteration_log_records.append(
        {
            "step": "R1",
            "purpose": "K-ladder on top word frequencies; test Cauchy-form c_k = eps^k * K_k(text)",
            "outcome": "see records",
        }
    )

    print("\n  --- iteration step R2: paragraph-length Pareto ---\n")
    for name, path in all_substrates.items():
        if not Path(path).exists():
            continue
        text = Path(path).read_text(encoding="utf-8")
        r2 = r2_paragraph_length_pareto(text)
        records.append({"date": "2026-05-17", "substrate": name, "step": "R2_paragraph_pareto", "result": r2})
        if r2.get("valid"):
            print(
                f"  {name:<30} slope={r2['power_law_slope']:.3f}  r2={r2['power_law_r2']:.4f}  "
                f"skew={r2['skew']:.2f}  max/med={r2['max_over_median_ratio']:.1f}"
            )

    iteration_log_records.append(
        {
            "step": "R2",
            "purpose": "Pareto/power-law fit on paragraph lengths; cascade-depth indicator",
            "outcome": "see records",
        }
    )

    print("\n  --- iteration step R3: rare-word cascade propagation ---\n")
    for name, path in all_substrates.items():
        if not Path(path).exists():
            continue
        text = Path(path).read_text(encoding="utf-8")
        r3 = r3_rare_word_cascade(text)
        records.append({"date": "2026-05-17", "substrate": name, "step": "R3_rare_word_cascade", "result": r3})
        if r3.get("valid"):
            print(
                f"  {name:<30} rare_words={r3['rare_word_count']}  intro={r3['intro_count']}  "
                f"propagation_rate={r3['propagation_rate']:.4f}"
            )

    iteration_log_records.append(
        {
            "step": "R3",
            "purpose": "Rare-word cascade propagation (Class C ∘ I forward weaving)",
            "outcome": "see records",
        }
    )

    print("\n  --- iteration step R4: cross-reference callback density ---\n")
    for name, path in all_substrates.items():
        if not Path(path).exists():
            continue
        text = Path(path).read_text(encoding="utf-8")
        r4 = r4_callback_density(text)
        records.append({"date": "2026-05-17", "substrate": name, "step": "R4_callback_density", "result": r4})
        if r4.get("valid"):
            print(
                f"  {name:<30} total_callbacks={r4['callback_count_total']:>5}  "
                f"per_1k_words={r4['callbacks_per_1000_words']:.2f}"
            )

    iteration_log_records.append(
        {
            "step": "R4",
            "purpose": "Cross-reference callback density (cascade-weave signature; explicit weaving)",
            "outcome": "see records — strongest discriminator candidate",
        }
    )

    print("\n  --- iteration step R5: paragraph-level Laplacian ---\n")
    for name, path in all_substrates.items():
        if not Path(path).exists():
            continue
        text = Path(path).read_text(encoding="utf-8")
        r5 = r5_paragraph_laplacian(text)
        records.append({"date": "2026-05-17", "substrate": name, "step": "R5_paragraph_laplacian", "result": r5})
        if r5.get("valid"):
            print(
                f"  {name:<30} fiedler={r5['fiedler_lambda_2']:.4f}  "
                f"mean_jac={r5['mean_jaccard']:.4f}  "
                f"zero_eigs={r5['n_zero_eigvals_near_zero']}"
            )

    iteration_log_records.append(
        {
            "step": "R5",
            "purpose": "Paragraph-level Class L Laplacian (finer-grained connectivity)",
            "outcome": "see records",
        }
    )

    out_records = out / "spike_43_iteration_records.ndjson"
    with out_records.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, default=float) + "\n")
    print(f"\n  [write] {out_records}")

    out_log = out / "spike_43_iteration_log.ndjson"
    with out_log.open("w", encoding="utf-8") as f:
        for rec in iteration_log_records:
            rec["date"] = "2026-05-17"
            rec["spike"] = 43
            f.write(json.dumps(rec, default=float) + "\n")
    print(f"  [write] {out_log}")


if __name__ == "__main__":
    main(r"D:\temp\spike_43")

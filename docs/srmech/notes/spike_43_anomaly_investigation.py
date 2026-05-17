"""
Spike #43 — Anomaly investigations

Investigate anomalies surfaced by primary analysis + iterative refinement.

Anomaly 1: Zipf slope cluster at -0.67 to -0.75 across good texts (NOT -1).
Anomaly 2: R5 paragraph-level Laplacian Fiedler = 0 on good texts (disconnected components).
Anomaly 3: srmech S6 cascade-beta r2=0.44 (much lower than other good texts).
Anomaly 4: R1 word-frequency K-ladder gives eps > 1 for all texts (unphysical per Spike #41 gate).
"""

from __future__ import annotations

import collections
import json
import math
import re
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


# ------------------------------------------------------------------------
# Anomaly 1: Zipf -0.7 cluster across good texts
# ------------------------------------------------------------------------


def anomaly1_zipf_subset_analysis(text: str) -> dict:
    """Re-check Zipf with different top-N to see if slope varies with N."""
    words = tokenize_words(text)
    counter = collections.Counter(words)
    results = []
    for n in [50, 100, 200, 500]:
        most_common = counter.most_common(n)
        if len(most_common) < 20:
            continue
        ranks = list(range(1, len(most_common) + 1))
        freqs = [c for _, c in most_common]
        log_r = [math.log(r) for r in ranks]
        log_f = [math.log(f) for f in freqs]
        nn = len(log_r)
        mean_r = sum(log_r) / nn
        mean_f = sum(log_f) / nn
        cov = sum((log_r[i] - mean_r) * (log_f[i] - mean_f) for i in range(nn))
        var = sum((log_r[i] - mean_r) ** 2 for i in range(nn))
        slope = cov / var if var else 0.0
        results.append({"top_n": n, "slope": slope})
    return {"valid": True, "results": results}


# ------------------------------------------------------------------------
# Anomaly 2: paragraph graph zero Fiedler (disconnected components)
# ------------------------------------------------------------------------


def anomaly2_paragraph_components(text: str) -> dict:
    """How many connected components does the paragraph graph have?"""
    chapters = tokenize_chapters(text)
    paragraphs = []
    for _, body in chapters:
        paragraphs.extend(tokenize_paragraphs(body))
    n = len(paragraphs)
    if n < 10:
        return {"valid": False}
    # sample at most 60
    n_sample = min(60, n)
    indices = [int(i * n / n_sample) for i in range(n_sample)]
    sample = [paragraphs[i] for i in indices]
    sets = []
    for p in sample:
        words = [w for w in tokenize_words(p) if w not in STOPWORDS and len(w) >= 4]
        sets.append(set(words))
    ns = len(sets)
    # union-find over edges where jaccard >= threshold
    def jaccard(a, b):
        if not a and not b:
            return 0.0
        return len(a & b) / len(a | b)

    thresholds = [0.0, 0.001, 0.05, 0.10, 0.20]
    results = []
    for thr in thresholds:
        parent = list(range(ns))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(a, b):
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb

        for i in range(ns):
            for j in range(i + 1, ns):
                if jaccard(sets[i], sets[j]) > thr:
                    union(i, j)
        roots = {find(i) for i in range(ns)}
        comp_sizes = collections.Counter(find(i) for i in range(ns))
        largest = max(comp_sizes.values())
        results.append(
            {
                "threshold": thr,
                "n_components": len(roots),
                "largest_component_size": largest,
                "isolated_count": sum(1 for s in comp_sizes.values() if s == 1),
            }
        )
    return {"valid": True, "n_paragraphs": ns, "by_threshold": results}


# ------------------------------------------------------------------------
# Anomaly 3: srmech cascade-beta is low
# ------------------------------------------------------------------------


def anomaly3_srmech_concept_intro(text: str) -> dict:
    """Track concept-introduction rate buckets for srmech to see WHERE the low r2 comes from."""
    words = [w for w in tokenize_words(text) if w not in STOPWORDS and len(w) >= 4]
    n = len(words)
    if n < 200:
        return {"valid": False}
    n_buckets = 20
    bucket_size = n // n_buckets
    seen: set[str] = set()
    new_counts = []
    for b in range(n_buckets):
        new_in_bucket = 0
        for i in range(bucket_size):
            idx = b * bucket_size + i
            if idx >= n:
                break
            w = words[idx]
            if w not in seen:
                new_in_bucket += 1
                seen.add(w)
        new_counts.append(new_in_bucket)
    return {"valid": True, "n_buckets": n_buckets, "new_counts": new_counts, "total_unique": len(seen)}


# ------------------------------------------------------------------------
# Anomaly 4: word-frequency K-ladder eps > 1 for ALL texts
# ------------------------------------------------------------------------


def anomaly4_word_freq_decay_shape(text: str) -> dict:
    """Examine ACTUAL decay shape of top-15 word frequencies; not assuming Cauchy form."""
    words = [w for w in tokenize_words(text) if w not in STOPWORDS and len(w) >= 4]
    counter = collections.Counter(words)
    most_common = counter.most_common(15)
    if len(most_common) < 15:
        return {"valid": False}
    c0 = most_common[0][1]
    ratios = [most_common[i][1] / c0 for i in range(1, 15)]
    # try shape 1: c_k = eps^k * 1/k (Spike #41 Kepler Cauchy)
    # try shape 2: c_k = eps^k (pure geometric)
    # try shape 3: c_k = 1 / k^s (pure Zipf power law)
    # Fit each on log scale and report r2

    ks = list(range(1, 15))
    log_c = [math.log(max(r, 1e-12)) for r in ratios]

    # Shape 3: log c_k = -s * log k -> linear regression
    log_k = [math.log(k) for k in ks]
    n = 14
    sx = sum(log_k)
    sy = sum(log_c)
    sxx = sum(x * x for x in log_k)
    sxy = sum(log_k[i] * log_c[i] for i in range(n))
    s_zipf = -(n * sxy - sx * sy) / (n * sxx - sx * sx) if (n * sxx - sx * sx) else 0.0
    intercept_zipf = (sy + s_zipf * sx) / n
    pred_zipf = [intercept_zipf - s_zipf * lk for lk in log_k]
    mean_y = sum(log_c) / n
    ss_res_zipf = sum((log_c[i] - pred_zipf[i]) ** 2 for i in range(n))
    ss_tot = sum((c - mean_y) ** 2 for c in log_c)
    r2_zipf = 1.0 - ss_res_zipf / ss_tot if ss_tot else 0.0

    # Shape 2: log c_k = k log eps -> linear regression on k vs log c_k
    sx2 = sum(ks)
    sxx2 = sum(k * k for k in ks)
    sy2 = sy
    sxy2 = sum(ks[i] * log_c[i] for i in range(n))
    log_eps_geom = (n * sxy2 - sx2 * sy2) / (n * sxx2 - sx2 * sx2)
    intercept_geom = (sy2 - log_eps_geom * sx2) / n
    pred_geom = [intercept_geom + log_eps_geom * k for k in ks]
    ss_res_geom = sum((log_c[i] - pred_geom[i]) ** 2 for i in range(n))
    r2_geom = 1.0 - ss_res_geom / ss_tot if ss_tot else 0.0

    # Shape 1: log c_k = k log eps - log k -> linear regression on k vs (log c_k + log k)
    y_cauchy = [log_c[i] + log_k[i] for i in range(n)]
    sy3 = sum(y_cauchy)
    sxy3 = sum(ks[i] * y_cauchy[i] for i in range(n))
    log_eps_cauchy = (n * sxy3 - sx2 * sy3) / (n * sxx2 - sx2 * sx2)
    intercept_cauchy = (sy3 - log_eps_cauchy * sx2) / n
    pred_cauchy = [intercept_cauchy + log_eps_cauchy * k - log_k[i] for i, k in enumerate(ks)]
    ss_res_cauchy = sum((log_c[i] - pred_cauchy[i]) ** 2 for i in range(n))
    r2_cauchy = 1.0 - ss_res_cauchy / ss_tot if ss_tot else 0.0

    return {
        "valid": True,
        "ratios": ratios,
        "shape_pure_zipf_s": s_zipf,
        "shape_pure_zipf_r2": r2_zipf,
        "shape_geometric_eps": math.exp(log_eps_geom),
        "shape_geometric_r2": r2_geom,
        "shape_cauchy_eps": math.exp(log_eps_cauchy),
        "shape_cauchy_r2": r2_cauchy,
        "best_shape": max(
            [("zipf", r2_zipf), ("geometric", r2_geom), ("cauchy", r2_cauchy)],
            key=lambda x: x[1],
        )[0],
    }


def main(out_dir: str) -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    records = []
    print("\n  --- Anomaly 1: Zipf slope vs top-N ---\n")
    for name, path in GOOD_PATHS.items():
        text = Path(path).read_text(encoding="utf-8")
        a1 = anomaly1_zipf_subset_analysis(text)
        records.append({"date": "2026-05-17", "anomaly": 1, "substrate": name, "result": a1})
        if a1.get("valid"):
            for r in a1["results"]:
                print(f"  {name:<25} top-{r['top_n']:<4} slope={r['slope']:.3f}")
            print()

    print("\n  --- Anomaly 2: paragraph graph components vs jaccard threshold ---\n")
    for name, path in GOOD_PATHS.items():
        text = Path(path).read_text(encoding="utf-8")
        a2 = anomaly2_paragraph_components(text)
        records.append({"date": "2026-05-17", "anomaly": 2, "substrate": name, "result": a2})
        if a2.get("valid"):
            print(f"  {name:<25}")
            for r in a2["by_threshold"]:
                print(
                    f"    thr>{r['threshold']:.2f}: comp={r['n_components']:<3} "
                    f"largest={r['largest_component_size']:<3} isolated={r['isolated_count']}"
                )

    print("\n  --- Anomaly 3: srmech concept-intro rate (bucket-by-bucket) ---\n")
    for name in ["srmech_notebook", "mfo_notebook", "spike_41"]:
        text = Path(GOOD_PATHS[name]).read_text(encoding="utf-8")
        a3 = anomaly3_srmech_concept_intro(text)
        records.append({"date": "2026-05-17", "anomaly": 3, "substrate": name, "result": a3})
        if a3.get("valid"):
            print(f"  {name:<25} new_counts={a3['new_counts']}")

    print("\n  --- Anomaly 4: word-frequency decay shape (Zipf vs geometric vs Cauchy) ---\n")
    for name, path in GOOD_PATHS.items():
        text = Path(path).read_text(encoding="utf-8")
        a4 = anomaly4_word_freq_decay_shape(text)
        records.append({"date": "2026-05-17", "anomaly": 4, "substrate": name, "result": a4})
        if a4.get("valid"):
            print(
                f"  {name:<25} BEST={a4['best_shape']:<10} "
                f"Zipf(s={a4['shape_pure_zipf_s']:.3f}, r2={a4['shape_pure_zipf_r2']:.4f}) "
                f"Cauchy(eps={a4['shape_cauchy_eps']:.4f}, r2={a4['shape_cauchy_r2']:.4f})"
            )

    out_records = out / "spike_43_anomaly_records.ndjson"
    with out_records.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, default=float) + "\n")
    print(f"\n  [write] {out_records}")


if __name__ == "__main__":
    main(r"D:\temp\spike_43")

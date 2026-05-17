"""
Spike #43b — Paragraph-level substructural analysis for SHORT documents.

The within-document units for short material (SE answers, arXiv abstracts,
single OpenStax chapters) are paragraphs, not chapters. Apply the same M1-M6
toolchain at paragraph-graph level.

This is itself a structural finding: short technical material has a
DIFFERENT-SCALE substrate than book-length material. The lock-and-key
question becomes "does this paragraph chain through clearly?"
"""

from __future__ import annotations

import collections
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

sys.path.insert(0, r"D:\temp\spike_43b")
from spike_43b_substructural_analysis import (  # type: ignore
    tokenize_paragraphs, tokenize_words, jaccard, chapter_hv as paragraph_hv,
    cosine, recursive_fiedler_dendrogram, collect_dendrogram_stats,
    greedy_louvain_pass, community_stats, hdc_dendrogram,
    multi_scale_spectral_gaps,
)


def paragraph_word_sets(paragraphs: list[str], top_n: int = 50) -> list[set[str]]:
    out = []
    for p in paragraphs:
        words = tokenize_words(p)
        counter = collections.Counter(words)
        top = {w for w, _ in counter.most_common(top_n) if len(w) >= 4}
        out.append(top)
    return out


def paragraph_similarity_matrix(paragraphs: list[str]) -> np.ndarray:
    word_sets = paragraph_word_sets(paragraphs)
    n = len(word_sets)
    M = np.zeros((n, n), dtype=np.float64)
    for i in range(n):
        for j in range(i, n):
            v = jaccard(word_sets[i], word_sets[j])
            M[i, j] = M[j, i] = v
        M[i, i] = 1.0
    return M


def paragraph_hv_matrix(paragraphs: list[str]) -> np.ndarray:
    n = len(paragraphs)
    hvs = [paragraph_hv(tokenize_words(p)) for p in paragraphs]
    M = np.zeros((n, n), dtype=np.float64)
    for i in range(n):
        for j in range(i, n):
            v = cosine(hvs[i], hvs[j])
            M[i, j] = M[j, i] = v
        M[i, i] = 1.0
    return M


def adjacent_paragraph_cosines(paragraphs: list[str]) -> list[float]:
    n = len(paragraphs)
    if n < 2:
        return []
    hvs = [paragraph_hv(tokenize_words(p)) for p in paragraphs]
    return [cosine(hvs[i], hvs[i + 1]) for i in range(n - 1)]


def analyse_short_doc(name: str, text: str, source_class: str, source_url: str, license_str: str, max_paras: int = 60) -> dict:
    paragraphs = tokenize_paragraphs(text)
    # Strip very short paragraphs (single-line) - they're not structural
    paragraphs = [p for p in paragraphs if len(p) > 50]
    n_para_raw = len(paragraphs)
    # Cap for tractability: if material has more than max_paras paragraphs,
    # we keep them all but rely on the coarsening logic in louvain to handle it.
    n_para = n_para_raw

    if n_para < 3:
        return {
            "substrate": name,
            "substrate_class": source_class,
            "source_url": source_url,
            "license": license_str,
            "n_paragraphs": n_para,
            "valid": False,
            "reason": "too few paragraphs (<3)",
            "n_words": len(tokenize_words(text)),
        }

    W_jac = paragraph_similarity_matrix(paragraphs)
    W_hdc = paragraph_hv_matrix(paragraphs)

    dendro = recursive_fiedler_dendrogram(W_jac)
    dendro_stats = collect_dendrogram_stats(dendro)

    community = greedy_louvain_pass(W_jac)
    comm_stats = community_stats(community)

    hdc_clust = hdc_dendrogram(W_hdc)

    adj_cos = adjacent_paragraph_cosines(paragraphs)
    if adj_cos:
        arr = np.array(adj_cos)
        adj_summary = {
            "n_adjacent_pairs": len(adj_cos),
            "mean_cosine": float(arr.mean()),
            "min_cosine": float(arr.min()),
            "max_cosine": float(arr.max()),
            "std_cosine": float(arr.std()),
        }
    else:
        adj_summary = {"n_adjacent_pairs": 0}

    multi_gaps = multi_scale_spectral_gaps(W_jac)

    # Paragraph-length statistics (Spike #43 R2/S6 analog at this scale)
    para_word_counts = [len(tokenize_words(p)) for p in paragraphs]
    para_arr = np.array(para_word_counts)
    para_stats = {
        "median_words": int(np.median(para_arr)),
        "max_words": int(para_arr.max()),
        "min_words": int(para_arr.min()),
        "ratio_max_to_median": float(para_arr.max() / max(float(np.median(para_arr)), 1.0)),
    }

    return {
        "substrate": name,
        "substrate_class": source_class,
        "source_url": source_url,
        "license": license_str,
        "n_paragraphs": n_para,
        "valid": True,
        "scale": "paragraph_level",
        "n_words": len(tokenize_words(text)),
        "M1_recursive_fiedler": dendro_stats,
        "M2_louvain_modularity": comm_stats,
        "M3_hdc_hierarchical": hdc_clust,
        "M4_adjacent_paragraph_cosines": adj_summary,
        "M6_multi_scale_gaps": multi_gaps,
        "paragraph_length_stats": para_stats,
    }


def main():
    manifest_path = Path(r"D:\temp\spike_43b\spike_43b_real_world_records_2026-05-17.ndjson")
    manifest = [json.loads(l) for l in manifest_path.read_text(encoding="utf-8").splitlines() if l.strip()]

    records = []
    for entry in manifest:
        path = Path(entry["path"])
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        sys.stderr.write(f"[short-doc] {entry['name']} ({len(text)} bytes; class={entry['source_class']})\n")
        rec = analyse_short_doc(
            entry["name"], text, entry["source_class"], entry["source_url"], entry["license"]
        )
        records.append(rec)

    out = Path(r"D:\temp\spike_43b\spike_43b_short_doc_substructural_2026-05-17.ndjson")
    with out.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    sys.stderr.write(f"\nWrote {len(records)} short-doc records to {out}\n")


if __name__ == "__main__":
    main()

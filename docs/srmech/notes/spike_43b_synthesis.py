"""
Spike #43b — Synthesis: sub-structural identification + teachability metric
                      + pathology catalog correlation analysis.

Reads all NDJSON outputs; produces synthesis findings as structured records.
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path


def load_ndjson(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def main():
    substruct = load_ndjson(Path(r"D:\temp\spike_43b\spike_43b_substructural_records_2026-05-17.ndjson"))
    real_world = load_ndjson(Path(r"D:\temp\spike_43b\spike_43b_real_world_substructural_2026-05-17.ndjson"))
    short_doc = load_ndjson(Path(r"D:\temp\spike_43b\spike_43b_short_doc_substructural_2026-05-17.ndjson"))
    teach = load_ndjson(Path(r"D:\temp\spike_43b\spike_43b_teachability_records_2026-05-17.ndjson"))
    patho = load_ndjson(Path(r"D:\temp\spike_43b\spike_43b_pathology_records_2026-05-17.ndjson"))

    findings: list[dict] = []

    # F1 - Sub-structural fingerprint patterns by substrate class
    by_class: dict[str, list[dict]] = {}
    for r in substruct + real_world + short_doc:
        if r.get("valid", True) and "M1_recursive_fiedler" in r:
            cls = r.get("substrate_class", "unknown")
            by_class.setdefault(cls, []).append(r)

    for cls, items in sorted(by_class.items()):
        n = len(items)
        l2_l3 = [r["M6_multi_scale_gaps"].get("ratio_l2_l3", 0)
                 for r in items if r.get("M6_multi_scale_gaps", {}).get("valid")]
        adj_cos = []
        for r in items:
            m4 = r.get("M4_sub_cascade_boundaries") or r.get("M4_adjacent_paragraph_cosines", {})
            if m4.get("mean_cosine") is not None:
                adj_cos.append(m4["mean_cosine"])
        n_comm = [r["M2_louvain_modularity"]["n_communities"] for r in items]
        f_leaf = [r["M1_recursive_fiedler"]["leaf_count"] for r in items]
        coph = [r["M3_hdc_hierarchical"].get("cophenetic_correlation", 0) for r in items]
        findings.append({
            "finding_id": f"F1.{cls}",
            "kind": "substrate_class_fingerprint",
            "substrate_class": cls,
            "n_substrates": n,
            "l2_l3_ratio_mean": statistics.mean(l2_l3) if l2_l3 else None,
            "l2_l3_ratio_stdev": statistics.stdev(l2_l3) if len(l2_l3) > 1 else None,
            "adjacent_cosine_mean": statistics.mean(adj_cos) if adj_cos else None,
            "adjacent_cosine_stdev": statistics.stdev(adj_cos) if len(adj_cos) > 1 else None,
            "n_communities_mean": statistics.mean(n_comm) if n_comm else None,
            "fiedler_leaf_count_mean": statistics.mean(f_leaf) if f_leaf else None,
            "cophenetic_correlation_mean": statistics.mean(coph) if coph else None,
        })

    # F2 - Teachability metric verdict: does T_composite correlate with quality?
    teach_by_cls: dict[str, list[float]] = {}
    for r in teach:
        if not r.get("valid", True):
            continue
        if "T_composite" in r:
            teach_by_cls.setdefault(r["substrate_class"], []).append(r["T_composite"])

    for cls, scores in sorted(teach_by_cls.items()):
        findings.append({
            "finding_id": f"F2.{cls}",
            "kind": "teachability_metric_per_class",
            "substrate_class": cls,
            "n": len(scores),
            "T_composite_mean": statistics.mean(scores),
            "T_composite_stdev": statistics.stdev(scores) if len(scores) > 1 else None,
            "T_composite_max": max(scores),
            "T_composite_min": min(scores),
        })

    # F3 - Pathology catalog: which pathologies hit which classes
    pathology_by_class: dict[str, dict[str, int]] = {}
    pathology_count: dict[str, int] = {}
    severity_by_class: dict[str, list[float]] = {}
    for r in patho:
        if not r.get("valid", True):
            continue
        cls = r.get("substrate_class", "unknown")
        pathology_count[cls] = pathology_count.get(cls, 0) + r["n_pathologies_triggered"]
        severity_by_class.setdefault(cls, []).append(r["severity_total"])
        for p in r.get("pathologies_triggered", {}):
            pathology_by_class.setdefault(cls, {}).setdefault(p, 0)
            pathology_by_class[cls][p] += 1

    for cls, n in sorted(pathology_count.items()):
        sevs = severity_by_class.get(cls, [])
        findings.append({
            "finding_id": f"F3.{cls}",
            "kind": "pathology_per_class",
            "substrate_class": cls,
            "total_pathologies_triggered": n,
            "pathologies_by_kind": pathology_by_class.get(cls, {}),
            "severity_total_mean": statistics.mean(sevs) if sevs else None,
            "severity_total_max": max(sevs) if sevs else 0,
        })

    # F4 - Lock-and-key discrimination: can sub-structural fingerprint predict canonical-good vs others?
    # Compare mean adjacent cosine across canonical-good vs constructed-bad vs wikipedia
    canon_adj = []
    cntrl_adj = []
    wiki_adj = []
    for items, accum in [
        (by_class.get("canonical_good", []), canon_adj),
        (by_class.get("constructed_control", []), cntrl_adj),
        (by_class.get("wikipedia", []), wiki_adj),
    ]:
        for r in items:
            m4 = r.get("M4_sub_cascade_boundaries") or r.get("M4_adjacent_paragraph_cosines", {})
            if m4.get("mean_cosine") is not None:
                accum.append(m4["mean_cosine"])

    findings.append({
        "finding_id": "F4.discrimination",
        "kind": "cross_class_discrimination",
        "canonical_good_adj_cos_mean": statistics.mean(canon_adj) if canon_adj else None,
        "constructed_control_adj_cos_mean": statistics.mean(cntrl_adj) if cntrl_adj else None,
        "wikipedia_adj_cos_mean": statistics.mean(wiki_adj) if wiki_adj else None,
        "canonical_good_n": len(canon_adj),
        "constructed_control_n": len(cntrl_adj),
        "wikipedia_n": len(wiki_adj),
        "note": "Adjacent-section mean cosine: canonical-good lowest (most differentiation); constructed worst usually highest (repetition / flatness); wikipedia tends mid (real-world variation)",
    })

    # F5 - Within-chapter analysis: which substrates have valid within-chapter signal?
    within = []
    for r in substruct + real_world:
        w5 = r.get("M5_within_chapter", {})
        if w5.get("valid"):
            within.append({
                "substrate": r["substrate"],
                "substrate_class": r["substrate_class"],
                "chapter_heading": w5["chapter_heading"],
                "n_paragraphs": w5["n_paragraphs"],
                "lambda_2": w5["lambda_2"],
                "lambda_2_3_gap": w5["lambda_2_3_gap"],
                "n_zero_eigs": w5["n_zero_eigs"],
            })
    findings.append({
        "finding_id": "F5.within_chapter",
        "kind": "within_chapter_largest_analysis",
        "n_substrates_with_valid_within_chapter": len(within),
        "samples": within,
    })

    # Write synthesis NDJSON
    out = Path(r"D:\temp\spike_43b\spike_43b_synthesis_records_2026-05-17.ndjson")
    with out.open("w", encoding="utf-8") as f:
        for r in findings:
            f.write(json.dumps(r) + "\n")
    print(f"Wrote {len(findings)} synthesis records to {out}")

    # Print findings summary
    print("\n--- F1: Sub-structural fingerprint by class ---")
    for f in findings:
        if f["kind"] == "substrate_class_fingerprint":
            print(f"  {f['substrate_class']:25s} n={f['n_substrates']:2d}  "
                  f"adj_cos={f['adjacent_cosine_mean'] or 0:.3f}  "
                  f"l2/l3={f['l2_l3_ratio_mean'] or 0:.3f}  "
                  f"n_comm={f['n_communities_mean'] or 0:.1f}  "
                  f"f_leaf={f['fiedler_leaf_count_mean'] or 0:.1f}")

    print("\n--- F2: Teachability metric T_composite by class ---")
    for f in findings:
        if f["kind"] == "teachability_metric_per_class":
            print(f"  {f['substrate_class']:25s} n={f['n']:2d}  T={f['T_composite_mean']:.3f} "
                  f"[{f['T_composite_min']:.2f}-{f['T_composite_max']:.2f}]")

    print("\n--- F3: Pathology counts by class ---")
    for f in findings:
        if f["kind"] == "pathology_per_class":
            print(f"  {f['substrate_class']:25s} total_triggered={f['total_pathologies_triggered']:3d}  "
                  f"sev_mean={f['severity_total_mean'] or 0:.2f}")
            for pn, n in sorted(f["pathologies_by_kind"].items()):
                print(f"    {pn}: {n}")

    print("\n--- F4: Cross-class discrimination ---")
    for f in findings:
        if f["finding_id"] == "F4.discrimination":
            for k, v in f.items():
                if "adj_cos" in k or k.endswith("_n"):
                    print(f"  {k}: {v}")


if __name__ == "__main__":
    main()

"""
Spike #43b — Sub-structural pathology catalog.

User's "cell walls / lock and key" framing:
  Material that does NOT lock-and-key with a reader's mental structure
  bounces off. We identify SPECIFIC sub-structural pathologies that
  prevent lock-and-key fit.

Each pathology is:
  - operationally defined (a quantitative threshold)
  - empirically calibrated against canonical-good band
  - given an interpretive ("cell wall" framing)
  - cross-referenced to canonical Spike #43 marker if applicable

This catalog operationalises `[[feedback_every_doc_edit_faces_falsification]]`
at the sub-structural level: every doc edit gets a chain-spec; this catalog
becomes the candidate-falsifier surface for "is this sub-structurally healthy?"
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


# Pathologies, each as a function (record -> (triggered: bool, severity: float in [0,1]))


def p1_no_multiscale(r: dict) -> tuple[bool, float, str]:
    """P1: lambda_2/lambda_3 > 0.95 means single-scale partition (one dominant bottleneck).
    Reader's mind expects multi-scale — this triggers monotonic flatness."""
    mg = r.get("M6_multi_scale_gaps", {})
    if not mg.get("valid"):
        return False, 0.0, "n/a"
    ratio = mg.get("ratio_l2_l3", 0.0)
    triggered = ratio > 0.95
    severity = max(0.0, ratio - 0.95) / 0.05
    return triggered, min(1.0, severity), f"l2/l3={ratio:.3f}"


def p2_paragraph_permutation_signature(r: dict) -> tuple[bool, float, str]:
    """P2: High mean adjacent-section cosine (>0.55) signals
    permuted-ordering or concatenated-unrelated structure.
    Reader's mind needs each section to have its own identity AND a thread to the next."""
    m4 = r.get("M4_sub_cascade_boundaries") or r.get("M4_adjacent_paragraph_cosines", {})
    if not m4 or "mean_cosine" not in m4:
        return False, 0.0, "n/a"
    mc = m4["mean_cosine"]
    triggered = mc > 0.55
    severity = (mc - 0.55) / 0.40 if triggered else 0.0
    return triggered, min(1.0, severity), f"mean_cos={mc:.3f}"


def p3_excessive_boundaries(r: dict) -> tuple[bool, float, str]:
    """P3: Too many sub-cascade boundaries (>0.40 per chapter) signals
    topic-shift-without-callback (concatenated-unrelated signature).
    Reader's mind can't build cumulative understanding."""
    n_chap = r.get("n_chapters") or r.get("n_paragraphs", 0)
    m4 = r.get("M4_sub_cascade_boundaries", {})
    if not n_chap or "n_boundaries" not in m4:
        return False, 0.0, "n/a"
    n_bnd = m4["n_boundaries"]
    ratio = n_bnd / max(n_chap, 1)
    triggered = ratio > 0.40
    severity = (ratio - 0.40) / 0.40 if triggered else 0.0
    return triggered, min(1.0, severity), f"bnd_rate={ratio:.3f}"


def p4_unstable_hierarchy(r: dict) -> tuple[bool, float, str]:
    """P4: Recursive Fiedler stable_depth_001 == 0 means the partition collapses
    at the first level (no nested structure stable under spectral gap).
    Reader's mind expects HIERARCHY; flat material is overwhelming."""
    ds = r.get("M1_recursive_fiedler", {})
    sd = ds.get("stable_depth_001", -1)
    md = ds.get("max_depth", 0)
    triggered = sd <= 1 and md >= 2
    severity = 1.0 if triggered else 0.0
    return triggered, severity, f"stable_depth={sd}/{md}"


def p5_too_few_communities(r: dict) -> tuple[bool, float, str]:
    """P5: <4 communities in chapter-similarity graph signals
    monolithic structure (single mega-topic).
    Reader's mind needs distinguishable concept-groups."""
    cs = r.get("M2_louvain_modularity", {})
    nc = cs.get("n_communities", 0)
    triggered = nc < 4
    severity = (4 - nc) / 4.0 if triggered else 0.0
    return triggered, min(1.0, severity), f"n_communities={nc}"


def p6_too_many_communities(r: dict) -> tuple[bool, float, str]:
    """P6: >15 communities signals over-fragmentation
    (each chapter is its own island; nothing holds together).
    Reader's mind exceeds ~10 concept-group working-memory capacity."""
    cs = r.get("M2_louvain_modularity", {})
    nc = cs.get("n_communities", 0)
    triggered = nc > 15
    severity = (nc - 15) / 15.0 if triggered else 0.0
    return triggered, min(1.0, severity), f"n_communities={nc}"


def p7_low_cophenetic(r: dict) -> tuple[bool, float, str]:
    """P7: HDC dendrogram cophenetic correlation < 0.55 means the hierarchy
    you SEE doesn't reflect the distances you FEEL.
    Lock-and-key: the structural signal mismatches the experiential signal."""
    hc = r.get("M3_hdc_hierarchical", {})
    cc = hc.get("cophenetic_correlation", 1.0)
    triggered = cc < 0.55
    severity = (0.55 - cc) / 0.55 if triggered else 0.0
    return triggered, min(1.0, severity), f"coph_corr={cc:.3f}"


def p8_zero_zero_boundary_excess(r: dict) -> tuple[bool, float, str]:
    """P8: Within-chapter LLM-flat signature: lambda_2 of largest chapter > 0.5
    means the chapter is one tight cluster with NO sub-structure (every
    paragraph similar; no internal differentiation).

    REVISED 2026-05-17 after anomaly investigation: Good texts have DISCONNECTED
    paragraph components in their largest chapter (n_zero_eigs > 1 is FEATURE
    not BUG; matches Spike #43 Anomaly 2). The pathology is the OPPOSITE
    direction — single tight cluster with no sub-structure. Cell-wall failure
    inside the chapter is FLATNESS, not disconnection.
    """
    w5 = r.get("M5_within_chapter", {})
    if not w5.get("valid"):
        return False, 0.0, "n/a"
    l2 = w5.get("lambda_2", 0.0)
    triggered = l2 > 0.5
    severity = (l2 - 0.5) / 1.5 if triggered else 0.0
    return triggered, min(1.0, severity), f"within_l2={l2:.3f}"


PATHOLOGIES = {
    "P1_no_multiscale": p1_no_multiscale,
    "P2_paragraph_permutation_signature": p2_paragraph_permutation_signature,
    "P3_excessive_boundaries": p3_excessive_boundaries,
    "P4_unstable_hierarchy": p4_unstable_hierarchy,
    "P5_too_few_communities": p5_too_few_communities,
    "P6_too_many_communities": p6_too_many_communities,
    "P7_low_cophenetic": p7_low_cophenetic,
    "P8_within_chapter_disconnect": p8_zero_zero_boundary_excess,
}


def evaluate(r: dict) -> dict:
    if not r.get("valid", True):
        return {
            "substrate": r["substrate"],
            "substrate_class": r["substrate_class"],
            "valid": False,
            "reason": r.get("reason", ""),
        }
    pathologies_triggered = {}
    severities = {}
    for name, fn in PATHOLOGIES.items():
        triggered, severity, msg = fn(r)
        if triggered:
            pathologies_triggered[name] = msg
        severities[name] = {"triggered": triggered, "severity": severity, "msg": msg}
    return {
        "substrate": r["substrate"],
        "substrate_class": r["substrate_class"],
        "is_canonical_good": r.get("is_canonical_good", False),
        "n_chapters": r.get("n_chapters") or r.get("n_paragraphs", 0),
        "n_pathologies_triggered": len(pathologies_triggered),
        "pathologies_triggered": pathologies_triggered,
        "severity_total": sum(s["severity"] for s in severities.values()),
        "details": severities,
    }


def main():
    inputs = [
        Path(r"D:\temp\spike_43b\spike_43b_substructural_records_2026-05-17.ndjson"),
        Path(r"D:\temp\spike_43b\spike_43b_real_world_substructural_2026-05-17.ndjson"),
        Path(r"D:\temp\spike_43b\spike_43b_short_doc_substructural_2026-05-17.ndjson"),
    ]
    records = []
    for fpath in inputs:
        if not fpath.exists():
            continue
        for line in fpath.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            records.append(evaluate(r))

    out = Path(r"D:\temp\spike_43b\spike_43b_pathology_records_2026-05-17.ndjson")
    with out.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    sys.stderr.write(f"Wrote {len(records)} pathology records to {out}\n")

    print(f"{'substrate':35s} {'class':25s} #patho severity_tot")
    print("-" * 90)
    for r in records:
        if not r.get("valid", True):
            print(f"{r['substrate']:35s} {r['substrate_class']:25s} INVALID ({r.get('reason','')})")
            continue
        print(f"{r['substrate']:35s} {r['substrate_class']:25s} {r['n_pathologies_triggered']:5d}  {r['severity_total']:.3f}")
        for pn, msg in r["pathologies_triggered"].items():
            print(f"    -> {pn}: {msg}")


if __name__ == "__main__":
    main()

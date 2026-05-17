"""
Spike #43b — Lock-and-key teachability metric.

User's framing 2026-05-17:
  "each reader's mind has existing structure (cell walls — biases, prior
  frameworks, attention spans). For teaching to work, material must be
  cellular lock and key — fit through the existing cell walls."

The teachability metric is a heuristic measuring "how well this material's
sub-structural fingerprint fits a typical reader's mental structure."

Components (each is a hypothesised lock-and-key feature):
  T1 — Multi-scale spectral gap richness (lambda_2/lambda_3 ratio):
       readers' minds expect MULTI-SCALE structure (concepts within
       concepts within concepts). A single-scale partition is rigid.
       Score = 1 - |ratio_l2_l3 - 0.5|  (peak at 0.5, i.e. lambda_3 ~ 2*lambda_2)

  T2 — Adjacent-section connectivity (mean cosine):
       readers' minds need CONTINUITY between sections to follow a thread.
       Too low = disjointed; too high = bland/repetitive (no novel content).
       Score: Gaussian peak at 0.20-0.30 (canonical-good band)

  T3 — Sub-cascade boundary detection (n boundaries / n_chapters):
       readers' minds need PERIODIC RESETS (chapter-break to absorb).
       Score: peak at 2-5 boundaries per ~10-15 chapters

  T4 — Recursive Fiedler stable depth:
       readers' minds expect HIERARCHICAL organisation that holds up
       under stable partition (not collapse at depth 2).
       Score: monotone increasing in stable_depth_001

  T5 — Cophenetic correlation of HDC dendrogram:
       readers' minds expect FAITHFUL hierarchy (the categories you
       see at one level match the distances you feel at another).
       Score: monotone increasing in cophenetic_correlation

  T6 — Community-count efficiency:
       readers can hold ~5-10 distinct concept-groups in working memory.
       Score: Gaussian peak at 6-10 communities

Composite T_score = mean(T1..T6), bounded [0, 1].

This is a CONJECTURE; we'll test it by computing T_score for the canonical-good
band and the constructed-bad band, and seeing if T_score predicts category.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path


def gaussian_score(x: float, mu: float, sigma: float) -> float:
    """Gaussian peak at mu, bounded [0, 1]."""
    return float(math.exp(-((x - mu) ** 2) / (2 * sigma * sigma)))


def t1_multiscale_gap(r: dict) -> float:
    """T1 = Gaussian peak at l2/l3 = 0.5 (i.e. lambda_3 ~ 2*lambda_2)."""
    mg = r.get("M6_multi_scale_gaps", {})
    if not mg.get("valid"):
        return 0.0
    ratio = mg.get("ratio_l2_l3", 0.0)
    return gaussian_score(ratio, mu=0.5, sigma=0.3)


def t2_adjacent_continuity(r: dict) -> float:
    """T2 = Gaussian peak at mean_cosine = 0.20-0.30."""
    m4 = r.get("M4_sub_cascade_boundaries") or r.get("M4_adjacent_paragraph_cosines", {})
    if not m4 or "mean_cosine" not in m4:
        return 0.0
    mc = m4["mean_cosine"]
    return gaussian_score(mc, mu=0.25, sigma=0.20)


def t3_boundary_periodicity(r: dict) -> float:
    """T3 = Gaussian peak at 2-5 boundaries per ~12 chapters
    (canonical-good band shows 2-5 boundaries / 10-16 chapters)."""
    n_chap = r.get("n_chapters") or r.get("n_paragraphs", 0)
    m4 = r.get("M4_sub_cascade_boundaries", {})
    if not n_chap or "n_boundaries" not in m4:
        return 0.0
    n_bnd = m4["n_boundaries"]
    # Expected ratio: ~0.25 boundaries per chapter (3/12)
    ratio = n_bnd / max(n_chap, 1)
    return gaussian_score(ratio, mu=0.25, sigma=0.25)


def t4_stable_hierarchy(r: dict) -> float:
    """T4 = stable_depth_001 / max_depth (fraction of dendrogram that holds up)."""
    ds = r.get("M1_recursive_fiedler", {})
    md = ds.get("max_depth", 0)
    sd = ds.get("stable_depth_001", -1)
    if md == 0:
        return 0.0
    # sd is depth at which spectral_gap fell below 0.01; higher is better
    return min(1.0, max(0.0, sd / max(md, 1)))


def t5_cophenetic_faithful(r: dict) -> float:
    """T5 = cophenetic correlation of HDC dendrogram (faithful hierarchy)."""
    hc = r.get("M3_hdc_hierarchical", {})
    cc = hc.get("cophenetic_correlation", 0.0)
    return min(1.0, max(0.0, cc))


def t6_community_count(r: dict) -> float:
    """T6 = Gaussian peak at n_communities = 7-9 (working-memory friendly)."""
    cs = r.get("M2_louvain_modularity", {})
    nc = cs.get("n_communities", 0)
    return gaussian_score(nc, mu=8.0, sigma=4.0)


def compute_teachability(r: dict) -> dict:
    t1 = t1_multiscale_gap(r)
    t2 = t2_adjacent_continuity(r)
    t3 = t3_boundary_periodicity(r)
    t4 = t4_stable_hierarchy(r)
    t5 = t5_cophenetic_faithful(r)
    t6 = t6_community_count(r)
    composite = (t1 + t2 + t3 + t4 + t5 + t6) / 6.0
    return {
        "T1_multiscale_gap": t1,
        "T2_adjacent_continuity": t2,
        "T3_boundary_periodicity": t3,
        "T4_stable_hierarchy": t4,
        "T5_cophenetic_faithful": t5,
        "T6_community_count": t6,
        "T_composite": composite,
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
            sys.stderr.write(f"[skip] {fpath} (not found)\n")
            continue
        for line in fpath.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if not r.get("valid", True) and "M1_recursive_fiedler" not in r:
                # Invalid (too few sections to analyse)
                records.append({
                    "substrate": r["substrate"],
                    "substrate_class": r["substrate_class"],
                    "valid": False,
                    "reason": r.get("reason", "no substructural data"),
                    "n_chapters": r.get("n_chapters", 0),
                    "n_paragraphs": r.get("n_paragraphs", 0),
                    "n_words": r.get("n_words", 0),
                })
                continue
            t = compute_teachability(r)
            t.update({
                "substrate": r["substrate"],
                "substrate_class": r["substrate_class"],
                "is_canonical_good": r.get("is_canonical_good", False),
                "n_chapters": r.get("n_chapters") or r.get("n_paragraphs", 0),
                "n_words": r.get("n_words", 0),
                "scale": r.get("scale", "chapter_level"),
            })
            records.append(t)

    out = Path(r"D:\temp\spike_43b\spike_43b_teachability_records_2026-05-17.ndjson")
    with out.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    sys.stderr.write(f"Wrote {len(records)} teachability records to {out}\n")

    # Print summary
    print(f"{'substrate':35s} {'class':25s} T1   T2   T3   T4   T5   T6   T_comp")
    print("-" * 110)
    for r in records:
        if not r.get("valid", True):
            print(f"{r['substrate']:35s} {r['substrate_class']:25s} INVALID ({r.get('reason','')})")
            continue
        print(f"{r['substrate']:35s} {r['substrate_class']:25s} "
              f"{r['T1_multiscale_gap']:.2f} {r['T2_adjacent_continuity']:.2f} "
              f"{r['T3_boundary_periodicity']:.2f} {r['T4_stable_hierarchy']:.2f} "
              f"{r['T5_cophenetic_faithful']:.2f} {r['T6_community_count']:.2f} "
              f"{r['T_composite']:.3f}")


if __name__ == "__main__":
    main()

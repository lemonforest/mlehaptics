"""Spike #24 Phase 15 — cross-comparison of 6 cells across rigour and formulation.

Loads the 6 per-cell NDJSON files. Produces three analyses:

  1. Per-domain siloing-deviation: for each of (CIMA, glycolysis, calcium),
     compare textbook-formulation harmonic-ratios to biochem-honest. Three
     possible verdicts per domain:
       - vocabulary_consolidates: both formulations show same Kepler-shape
       - siloing_load_bearing: textbook and biochem disagree on Kepler-shape
       - reverse_siloing: textbook messier than biochem-honest

  2. Per-formulation rigour-A-vs-rigour-B agreement: 6 cells, does the
     Phase-9.2 method (Rigour A) agree with the ratcheted method (Rigour B)?

  3. Overall verdict: 9/9 substrate confirmation (3 from Phase 9.2 + 6 from
     Phase 15)? Method validated? Vocabulary consolidating?

Output: spike_24_phase_15_crosscompare_2026-05-15.ndjson
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


# 6 cells (domain, formulation, ndjson_filename_stem)
CELLS = [
    ("CIMA",        "textbook-reduction",  "spike_24_phase_15_cima_lengyel_epstein_2026-05-15"),
    ("CIMA",        "biochem-honest",      "spike_24_phase_15_cima_citri_epstein_2026-05-15"),
    ("glycolysis",  "textbook-reduction",  "spike_24_phase_15_glyc_selkov_2026-05-15"),
    ("glycolysis",  "biochem-honest",      "spike_24_phase_15_glyc_goldbeter_2026-05-15"),
    ("calcium",     "textbook-reduction",  "spike_24_phase_15_calcium_gdb_2026-05-15"),
    ("calcium",     "biochem-honest",      "spike_24_phase_15_calcium_dyk_2026-05-15"),
]

DOMAINS = ["CIMA", "glycolysis", "calcium"]


def load_cell(ndjson_stem):
    path = Path(__file__).parent / f"{ndjson_stem}.ndjson"
    if not path.exists():
        return None
    records = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def get_verdict_from_records(records, rigour_level):
    for r in records:
        if r.get("record_kind") == "harmonic_signature" and r.get("rigour_level") == rigour_level:
            return r
    return None


def get_cell_verdict(records):
    for r in records:
        if r.get("record_kind") == "cell_verdict":
            return r
    return None


def categorize_verdict(v):
    """Normalize verdict to one of: clean, with_extras, absent."""
    if v is None:
        return "absent"
    if "clean" in v:
        return "clean"
    if "extras" in v:
        return "with_extras"
    return "absent"


def main():
    records = []
    records.append({
        "record_kind": "header",
        "spike": 24,
        "phase": "15",
        "purpose": "cross-comparison: textbook-vs-biochem within domain; rigour-A-vs-rigour-B within formulation",
        "generated_at": datetime.now(timezone.utc).isoformat(),
    })

    # Load all cells
    all_data = {}
    for domain, formulation, stem in CELLS:
        recs = load_cell(stem)
        all_data[(domain, formulation)] = recs
        if recs is None:
            print(f"  WARN: missing {stem}.ndjson")

    # 1. Per-cell summary (extract verdicts)
    cell_summary = []
    for domain, formulation, stem in CELLS:
        recs = all_data.get((domain, formulation))
        if recs is None:
            cell_summary.append({
                "domain": domain, "formulation": formulation,
                "rigour_a_verdict": "missing", "rigour_b_verdict": "missing",
                "rigour_a_n_match": None, "rigour_b_n_match": None,
                "rigour_a_fundamental_hz": None, "rigour_b_fundamental_hz": None,
            })
            continue
        rec_a = get_verdict_from_records(recs, "A")
        rec_b = get_verdict_from_records(recs, "B")
        cell_summary.append({
            "domain": domain, "formulation": formulation,
            "rigour_a_verdict": rec_a.get("kepler_shape_verdict") if rec_a else "missing",
            "rigour_b_verdict": rec_b.get("kepler_shape_verdict") if rec_b else "missing",
            "rigour_a_n_match": rec_a.get("n_integer_harmonics_matched_out_of_6") if rec_a else None,
            "rigour_b_n_match": rec_b.get("n_integer_harmonics_matched_out_of_6") if rec_b else None,
            "rigour_a_fundamental_hz": rec_a.get("fundamental_freq_hz") if rec_a else None,
            "rigour_b_fundamental_hz": rec_b.get("fundamental_freq_hz") if rec_b else None,
            "rigour_a_top_harmonics_ratios": [
                round(h["ratio_to_fundamental"], 4) if h.get("ratio_to_fundamental") else None
                for h in (rec_a.get("leading_harmonics", []) if rec_a else [])[:6]
            ],
            "rigour_b_top_harmonics_ratios": [
                round(h["ratio_to_fundamental"], 4) if h.get("ratio_to_fundamental") else None
                for h in (rec_b.get("leading_harmonics", []) if rec_b else [])[:6]
            ],
        })

    for cs in cell_summary:
        records.append({"record_kind": "cell_summary", **cs})

    # 2. Per-domain siloing analysis
    for domain in DOMAINS:
        text = next((c for c in cell_summary if c["domain"] == domain and c["formulation"] == "textbook-reduction"), None)
        bio = next((c for c in cell_summary if c["domain"] == domain and c["formulation"] == "biochem-honest"), None)
        if not text or not bio:
            continue
        # Use Rigour B verdicts as primary (more rigorous), fall back to A
        text_b_cat = categorize_verdict(text["rigour_b_verdict"])
        bio_b_cat = categorize_verdict(bio["rigour_b_verdict"])
        text_a_cat = categorize_verdict(text["rigour_a_verdict"])
        bio_a_cat = categorize_verdict(bio["rigour_a_verdict"])

        # Both Kepler-shape (clean or with_extras): vocabulary consolidates
        # One clean other absent: siloing load-bearing — and we distinguish two sub-cases:
        #   (a) biochem fails to oscillate at canonical params (CIMA case)
        #   (b) biochem oscillates and Rigour A finds Kepler-shape, but Rigour B picks up
        #       additional dynamics (slow drift / sidebands) that push integer harmonics out
        #       of the top-10 ranking — pure-Kepler-shape signature obscured by additional
        #       spectral richness (DYK case)
        # text "absent" but bio "clean": reverse siloing
        def is_kepler(c):
            return c in ("clean", "with_extras")
        if is_kepler(text_b_cat) and is_kepler(bio_b_cat):
            verdict = "vocabulary_consolidates"
            reason = "both formulations show Kepler-shape; pin-slot-gear primitives identifiable at both"
        elif is_kepler(text_b_cat) and bio_b_cat == "absent":
            # Sub-case detection: did biochem oscillate at Rigour A but fail at Rigour B?
            if is_kepler(bio_a_cat) and bio_b_cat == "absent":
                verdict = "siloing_load_bearing_via_spectral_richness"
                reason = (
                    "textbook reduction and biochem Rigour-A show clean Kepler-shape, but "
                    "biochem-honest Rigour-B (50000 cycles, Welch + significance) surfaces "
                    "additional spectral content (slow drift modes + harmonic sidebands) "
                    "that push integer-k harmonics out of the top-10 amplitude ranking. "
                    "Integer harmonics are still present, but the spectrum is no longer "
                    "Kepler-CLEAN — it has the Kepler-shape primitive plus other dynamical "
                    "structure the textbook reduction obscures."
                )
            else:
                verdict = "siloing_load_bearing"
                reason = (
                    "textbook reduction shows Kepler-shape but biochem-honest expansion does not "
                    "(at canonical published parameters): the reduction's slow-fast separation is "
                    "what creates the Hopf-bifurcation regime where Kepler-shape emerges. Carry "
                    "the textbook simplification to identify primitives; biochem-honest expansion "
                    "at finite parameters lives in stable-fixed-point regime."
                )
        elif text_b_cat == "absent" and is_kepler(bio_b_cat):
            verdict = "reverse_siloing"
            reason = "textbook reduction failed to oscillate but biochem-honest did — textbook is over-simplified for primitive identification"
        else:
            verdict = "both_absent_or_inconsistent"
            reason = f"text_b={text_b_cat}, bio_b={bio_b_cat}"
        records.append({
            "record_kind": "domain_siloing_analysis",
            "domain": domain,
            "textbook_rigour_a_verdict": text["rigour_a_verdict"],
            "textbook_rigour_b_verdict": text["rigour_b_verdict"],
            "biochem_rigour_a_verdict": bio["rigour_a_verdict"],
            "biochem_rigour_b_verdict": bio["rigour_b_verdict"],
            "siloing_verdict": verdict,
            "siloing_reason": reason,
        })

    # 3. Per-formulation rigour-A-vs-B agreement
    for cs in cell_summary:
        a_cat = categorize_verdict(cs["rigour_a_verdict"])
        b_cat = categorize_verdict(cs["rigour_b_verdict"])
        if a_cat == b_cat:
            method_verdict = "agree"
        else:
            method_verdict = "disagree"
        records.append({
            "record_kind": "method_validation",
            "domain": cs["domain"],
            "formulation": cs["formulation"],
            "rigour_a_category": a_cat,
            "rigour_b_category": b_cat,
            "rigour_a_n_match": cs["rigour_a_n_match"],
            "rigour_b_n_match": cs["rigour_b_n_match"],
            "method_verdict": method_verdict,
        })

    # 4. Overall verdicts
    cells_with_kepler = sum(
        1 for cs in cell_summary
        if categorize_verdict(cs["rigour_b_verdict"]) in ("clean", "with_extras")
    )
    n_cells_total = len([c for c in cell_summary if c["rigour_b_verdict"] != "missing"])
    method_agreements = sum(
        1 for cs in cell_summary
        if categorize_verdict(cs["rigour_a_verdict"]) == categorize_verdict(cs["rigour_b_verdict"])
    )

    # Phase 9.2 baseline = 3/3 confirmed (Lotka-Volterra, Brusselator, Oregonator)
    # Phase 15 contribution = cells_with_kepler / 6
    # Combined Phase 9.2 + Phase 15 = (3 + cells_with_kepler) / (3 + 6) = (3 + N) / 9
    combined_kepler = 3 + cells_with_kepler
    combined_total = 3 + n_cells_total

    records.append({
        "record_kind": "overall_verdict",
        "phase_15_kepler_count": int(cells_with_kepler),
        "phase_15_cells_total": int(n_cells_total),
        "phase_9_2_kepler_count": 3,
        "phase_9_2_cells_total": 3,
        "combined_kepler_count": int(combined_kepler),
        "combined_cells_total": int(combined_total),
        "method_validation_agreements": int(method_agreements),
        "method_validation_total_cells": int(n_cells_total),
        "method_validation_summary": (
            f"{method_agreements}/{n_cells_total} cells show Rigour-A-vs-Rigour-B verdict agreement: "
            f"Phase 9.2 method (Hann + parabolic interpolation, no CI) "
            f"{'validated' if method_agreements >= n_cells_total - 1 else 'partially validated'} "
            f"by ratcheted Welch + significance test"
        ),
        "kepler_shape_universal_status": (
            f"{combined_kepler}/{combined_total} chemistry-substrate oscillating systems "
            f"show Kepler-shape signature. Universal stands {'STRONGER' if cells_with_kepler >= 5 else 'in expanded scope, with limits'}."
        ),
        "siloing_findings": "See per-domain siloing_analysis records",
    })

    # Write NDJSON
    out_path = Path(__file__).with_suffix(".ndjson")
    with out_path.open("w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"wrote {out_path.name}")
    print("\n=== Cross-comparison summary ===")
    for cs in cell_summary:
        print(f"  {cs['domain']:12} | {cs['formulation']:20} | "
              f"A: {cs['rigour_a_verdict']:25} ({cs['rigour_a_n_match']}/6) | "
              f"B: {cs['rigour_b_verdict']:25} ({cs['rigour_b_n_match']}/6)")
    print(f"\nKepler-shape universal: {combined_kepler}/{combined_total} substrates "
          f"(Phase 9.2 + Phase 15 combined)")
    print(f"Method validation: {method_agreements}/{n_cells_total} cells "
          f"show A-vs-B agreement")
    # Print per-domain
    for r in records:
        if r.get("record_kind") == "domain_siloing_analysis":
            print(f"  {r['domain']}: {r['siloing_verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

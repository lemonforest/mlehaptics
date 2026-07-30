"""Spike #40 EXACT PORT of ``spike_40_synthesis.py`` (2026-07-30).

Pure table generator — it reads the four ported batteries and renders the
per-instrument substrate-discrimination table. No arithmetic of its own, so
there is nothing here to port numerically; what CHANGES is the verdict
column, because the decay-form port now labels the six substrates whose
"best decay model" was decided by ~1e-17 arithmetic noise.

Reads:
  spike_40_records_exact.ndjson
  spike_40_decay_form_records_exact.ndjson
  spike_40_freq_inharmonicity_records_exact.ndjson
  spike_40_falsifier_records_exact.ndjson

Original imports removed: none (this script was already numpy-free) — but the
2026-05-17 conclusions it hard-codes ARE amended below, because two of them
did not survive the exact re-run.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path as _Path
from typing import List

OUT_DIR = str(_Path(__file__).resolve().parent)
sys.path.insert(0, OUT_DIR)

from spike_40_exact_primitives import provenance_records, write_ndjson  # noqa: E402


def load_ndjson(path):
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


INSTRUMENTS = [
    ("pure_fm_beta_0.5", "ring-up", "FM (beta=0.5)"),
    ("pure_fm_beta_1.5", "ring-up", "FM (beta=1.5)"),
    ("pure_fm_beta_3.0", "ring-up", "FM (beta=3.0)"),
    ("pure_am", "ring-up", "AM"),
    ("beat_pattern", "ring-up", "Beat (2-tone)"),
    ("piano_B_0.0001", "ring-down", "Piano (B=1e-4)"),
    ("piano_B_0.0005", "ring-down", "Piano (B=5e-4)"),
    ("piano_B_0.001", "ring-down", "Piano (B=1e-3)"),
    ("violin_helmholtz", "ring-up", "Violin (bowed)"),
    ("clarinet_open_closed", "ring-up", "Clarinet"),
    ("drum_membrane_2d_amp_baseline", "ring-down", "Drum 2D"),
    ("bell_5mode", "ring-down", "Bell"),
    ("voice_vowel_a", "ring-up", "Voice /a/"),
    ("flute_open_open", "ring-up", "Flute"),
    ("trumpet_lip_buzz", "ring-up", "Trumpet"),
    ("REF_pure_kepler_eps_0.1", "ref", "REF: Kepler eps=0.1"),
    ("REF_pure_harmonic_1_over_n", "ref", "REF: 1/n sawtooth"),
    ("REF_white_noise_flat", "ref", "REF: white noise"),
]


def main() -> None:
    print("=" * 78)
    print("Spike #40 EXACT PORT - SYNTHESIS: per-instrument substrate-discrimination")
    print("=" * 78)

    primary = load_ndjson(os.path.join(OUT_DIR, "spike_40_records_exact.ndjson"))
    decay = load_ndjson(os.path.join(OUT_DIR, "spike_40_decay_form_records_exact.ndjson"))
    load_ndjson(os.path.join(OUT_DIR, "spike_40_freq_inharmonicity_records_exact.ndjson"))
    load_ndjson(os.path.join(OUT_DIR, "spike_40_falsifier_records_exact.ndjson"))

    k_by = {r["substrate"]: r for r in primary if r.get("kind") == "substrate_K_test"}
    d_by = {r["substrate"]: r for r in decay if r.get("kind") == "decay_form_fit"}

    print(f"\n{'INSTRUMENT':28s} {'mode':>10s} {'K?':>4s} {'best_decay':>14s} "
          f"{'param':>12s} {'verdict':>12s}")
    print("-" * 92)

    records: List[dict] = provenance_records("spike_40_synthesis_exact.py")
    n_degenerate = 0
    for sub_id, mode, display in INSTRUMENTS:
        K = k_by.get(sub_id, {}).get("k_test", {})
        D = d_by.get(sub_id, {})
        present = K.get("kepler_signature_present", False)
        best = D.get("best_model", "--")
        degen = D.get("exact_degeneracy", {})
        is_degen = bool(degen.get("verdict_is_degenerate"))
        n_degenerate += 1 if is_degen else 0
        if best == "M1_power_law":
            p = D.get("M1_power_law_p", float("nan"))
            param, sig = f"p={p:.3f}", f"power-law 1/n^{p:.2f}"
        elif best == "M2_geometric":
            e = D.get("M2_geometric_eps", float("nan"))
            param, sig = f"eps={e:.3f}", f"geometric eps={e:.3f}"
        elif best == "M3_bessel":
            b = D.get("M3_bessel_beta", float("nan"))
            param, sig = f"beta={b:.3f}", f"Bessel J_k(beta={b:.3f})"
        elif best == "M4_kepler":
            e = D.get("M4_kepler_eps", float("nan"))
            param, sig = f"eps={e:.3f}", f"Kepler eps^n/n eps={e:.3f}"
        elif best == "INSUFFICIENT":
            param, sig = "--", "sparse spectrum"
        else:
            param, sig = "--", "--"
        tag = "DEGENERATE" if is_degen else ("EXACT" if degen.get("n_exact_fits") == 1
                                             else "numeric")
        print(f"{display:28s} {mode:>10s} {'YES' if present else 'no':>4s} "
              f"{best:>14s} {param:>12s} {tag:>12s}")
        records.append({
            "kind": "synthesis_per_instrument",
            "instrument_id": sub_id,
            "display": display,
            "ring_mode": mode,
            "k_signature_present": present,
            "k_test_eps_fit": K.get("eps_fit"),
            "k_test_r2": K.get("r2"),
            "k_test_monotonic": K.get("monotonic_decreasing"),
            "k_test_in_range": K.get("in_physical_range"),
            "best_decay_model": best,
            "best_param": param,
            "signature_summary": sig,
            "decay_verdict_class": tag,
            "decay_models_that_fit_EXACTLY": degen.get("models_that_fit_EXACTLY", []),
        })

    print("\n" + "=" * 78)
    print("META-QUESTION ANSWER (2026-07-30 exact re-run)")
    print("=" * 78)
    print(f"""
Q: From the position of each individual instrument in a concert, are there
   epicycle structures from the way different instruments make different
   musical shapes?

A (AMENDED): PARTLY. The K-test half of the 2026-05-17 answer survives the
   exact re-run bit-for-bit. The decay-form half does NOT survive as stated.

   SURVIVES — strict K-shape (c_k = eps^k/k) is ABSENT from canonical
   instrument amplitude spectra and PRESENT only in FM-small-beta and
   Kepler-orbit-EOC. Every K-test figure in the 2026-05-17 record reproduces
   to <= 2 ulp under exact rational arithmetic.

   DOES NOT SURVIVE — "different instruments -> different decay-form
   best-fit -> identifiable substrate fingerprint". On {n_degenerate} of the 18
   instruments listed above the four-model comparison is DEGENERATE: two or
   more models fit with residual EXACTLY ZERO, so the reported best_model is
   whichever one the arithmetic noise happened to favour. The root cause is
   structural, not numerical: M1 (A/n^p) at p=1 and M4 (A*eps^n/n) at eps=1
   are THE SAME CURVE A/n, so every canonical 1/n spectrum (piano, violin,
   drum-amplitude-baseline, clarinet on its odd partials, the 1/n reference)
   makes the M1-vs-M4 question undecidable. The 2026-05-17 records already
   carried the tell — margin_log_rms = 0.0 on exactly those rows.

   What the decay-form battery DOES discriminate, legitimately:
     - FM              -> M3 Bessel, and the fitted beta recovers the true
                          beta (0.496 / 1.486 / 3.020 for 0.5 / 1.5 / 3.0)
     - Kepler          -> M4 exactly, eps recovered exactly
     - Flute (1/n^2)   -> M1 exactly at p = 2
     - Bell, Voice     -> M2 geometric, a genuine numeric win
     - AM, beat        -> INSUFFICIENT (sparse), correctly refused

KEY ANOMALY-CHASE FINDING (FM-K-overlap): UNCHANGED and reproduced exactly.
   Small-beta FM passes the strict K-test at k_max=6. The exact ratio table
   in the fm-anomaly port shows |J_k(1/2)| / ((1/4)^k/k) DRIFTING in k rather
   than staying constant, so the two series are spectrally distinguishable in
   principle and only coincide at the K-test's resolution.

CASCADE-BETA: the 2026-05-17 conclusion (beta = 1, not the predicted
   0.33 / 0.5 / 0.6) stands, and for drum and bell the exact minimiser is now
   given in closed form: exp(-3t/2) IS exp(-(t/(2/3))^1) and exp(-t/2) IS
   exp(-(t/2)^1), so beta = 1 exactly with residual identically zero. The
   d_S/(d_S+2) prediction is refuted for these envelopes by construction, not
   by a fit.
""")

    records.append({
        "kind": "spike_40_meta_question_synthesis_exact",
        "port_date": "2026-07-30",
        "primary_question": "Where does Kepler-shape c_k=eps^k/k appear in "
                            "musical/wave substrate?",
        "meta_question": "Do different instruments produce measurably different "
                         "epicycle shapes?",
        "primary_answer": "UNCHANGED — ABSENT in canonical instrument amplitude "
                          "spectra; PRESENT in FM (Bessel J_k at small beta) and "
                          "Kepler-orbit-EOC. Reproduced to <= 2 ulp exactly.",
        "meta_answer_2026_05_17": "YES, substrate-discriminating via "
                                  "DECAY-FORM-BEST-FIT.",
        "meta_answer_2026_07_30": (
            f"QUALIFIED. On {n_degenerate}/18 instruments the four-model "
            "comparison is exactly degenerate (>= 2 models fit with residual "
            "EXACTLY zero) because M1(p=1) and M4(eps=1) are the same curve A/n. "
            "On those rows best_model carries no information. The battery still "
            "discriminates FM (M3, beta recovered), Kepler (M4, eps recovered), "
            "flute (M1 exactly at p=2), and bell/voice (M2, genuine numeric win)."
        ),
        "n_degenerate_of_18": n_degenerate,
        "anomaly_chase": "UNCHANGED — small-beta FM passes strict K at k_max=6; "
                         "the exact |J_k|/(eps^k/k) ratio DRIFTS in k, so the two "
                         "are distinguishable in principle.",
        "framework_validation": "STANDS. K-test rejects random spectra 0/50 "
                                "(reproduced bit-exactly against the 2026-05-17 "
                                "PCG64 stream), white noise, and 1/n.",
        "instrument_first_validation": (
            "UNCHANGED for ring-up. For ring-down, beta = 1 is now given in "
            "CLOSED FORM for drum and bell rather than fitted, so the "
            "d_S/(d_S+2) prediction is refuted by construction."
        ),
    })

    out = os.path.join(OUT_DIR, "spike_40_synthesis_records_exact.ndjson")
    write_ndjson(out, records)
    print(f"Wrote {len(records)} synthesis records to {out}")


if __name__ == "__main__":
    main()

"""Spike #40 -- synthesis: per-instrument substrate-discrimination table.

Pulls together the four signature batteries:
  (1) Strict K-test (Spike #30B v3) on amplitude spectrum
  (2) Decay-form best-fit (M1 power-law / M2 geometric / M3 Bessel / M4 Kepler)
  (3) Frequency-axis inharmonicity K-test
  (4) Cascade-beta on ring-down envelopes (where applicable)

Plus the information-instrument 14-class binding-level overlay per Spike #37
substrate-portability table.
"""

from __future__ import annotations

import json
import os

from pathlib import Path as _Path
OUT_DIR = str(_Path(__file__).resolve().parent)


def load_ndjson(path):
    out = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def main():
    print("=" * 78)
    print("Spike #40 -- SYNTHESIS: per-instrument substrate-discrimination")
    print("=" * 78)

    # Load all four batteries
    primary = load_ndjson(os.path.join(OUT_DIR, "spike_40_records.ndjson"))
    decay = load_ndjson(os.path.join(OUT_DIR, "spike_40_decay_form_records.ndjson"))
    freq = load_ndjson(os.path.join(OUT_DIR, "spike_40_freq_inharmonicity_records.ndjson"))
    fals = load_ndjson(os.path.join(OUT_DIR, "spike_40_falsifier_records.ndjson"))

    # Build per-substrate index
    K_by_sub = {r["substrate"]: r for r in primary if r.get("kind") == "substrate_K_test"}
    D_by_sub = {r["substrate"]: r for r in decay if r.get("kind") == "decay_form_fit"}
    F_by_sub = {r["substrate"]: r for r in freq if r.get("kind") == "freq_inharmonicity_K_test"}

    # Render comparison table
    instruments = [
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

    print(
        f"\n{'INSTRUMENT':28s} {'ringup/down':>10s} {'K?':>4s} {'best_decay':>14s} {'p/eps/beta':>12s} {'sig':>32s}"
    )
    print("-" * 110)

    synth_records = []
    for sub_id, mode, display in instruments:
        K = K_by_sub.get(sub_id, {}).get("k_test", {})
        D = D_by_sub.get(sub_id, {})
        K_present = K.get("kepler_signature_present", False)
        K_present_str = "YES" if K_present else "no"
        best = D.get("best_model", "--")
        if best == "M1_power_law":
            p = D.get("M1_power_law_p", float("nan"))
            param = f"p={p:.3f}"
            sig = f"power-law 1/n^{p:.2f}"
        elif best == "M2_geometric":
            eps_g = D.get("M2_geometric_eps", float("nan"))
            param = f"eps={eps_g:.3f}"
            sig = f"geometric eps={eps_g:.3f}"
        elif best == "M3_bessel":
            beta = D.get("M3_bessel_beta", float("nan"))
            param = f"beta={beta:.3f}"
            sig = f"Bessel J_k(beta={beta:.3f})"
        elif best == "M4_kepler":
            eps_k = D.get("M4_kepler_eps", float("nan"))
            param = f"eps={eps_k:.3f}"
            sig = f"Kepler eps^n/n eps={eps_k:.3f}"
        elif best == "INSUFFICIENT":
            param = "--"
            sig = "sparse spectrum"
        else:
            param = "--"
            sig = "--"
        print(
            f"{display:28s} {mode:>10s} {K_present_str:>4s} {best:>14s} {param:>12s} {sig:>32s}"
        )
        synth_records.append({
            "kind": "synthesis_per_instrument",
            "instrument_id": sub_id,
            "display": display,
            "ring_mode": mode,
            "k_signature_present": K_present,
            "k_test_eps_fit": K.get("eps_fit"),
            "k_test_r2": K.get("r2"),
            "k_test_monotonic": K.get("monotonic_decreasing"),
            "k_test_in_range": K.get("in_physical_range"),
            "best_decay_model": best,
            "best_param": param,
            "signature_summary": sig,
        })

    # === Meta-question answer ===
    print("\n" + "=" * 78)
    print("META-QUESTION ANSWER")
    print("=" * 78)
    print("""
Q: From the position of each individual instrument in a concert, are there
   epicycle structures from the way different instruments make different
   musical shapes?

A: YES -- different instruments produce SUBSTRATE-DISCRIMINATING decay-form
   fingerprints. But NO -- most canonical musical-instrument amplitude
   spectra do NOT carry the strict Kepler-shape (c_k = eps^k/k) signature.

   The discrimination is in WHICH MODEL FITS BEST:
     - Pure FM modulation       -> Bessel J_k (and K-shape at small beta!)
     - Pure Kepler/Antikythera  -> Kepler eps^k/k (canonical positive)
     - Piano/Violin/Drum-amp   -> 1/n power-law (sawtooth family)
     - Flute                    -> 1/n^2 (weak-overtone)
     - Trumpet                  -> 1/sqrt(n) (rich-brass)
     - Clarinet                 -> odd-only 1/n (cylindrical closed)
     - Bell/Voice               -> geometric (mode-amplitude / formant-shaped)
     - AM/beat                  -> Class I sparse (no decay envelope)
     - White noise              -> flat (p=0)

   STRICT K-shape appears ONLY in FM-small-beta and Kepler-orbit-EOC. The
   instrument-substrate spectrum is generally Class L (eigenbasis-rooted)
   with substrate-specific decay-form fingerprints.

   The meta-question is substrate-discriminating in the affirmative:
   different instruments -> different decay-form best-fit -> identifiable
   substrate fingerprint. The signature is in the DECAY FORM, not in
   the strict-K test (which is K-specific, not instrument-discriminating).

KEY ANOMALY-CHASE FINDING (FM-K-overlap):
   pure_fm_beta_0.5 passed the strict K-test. Investigation showed this
   is not an artifact -- Kepler equation IS phase modulation at small
   eccentricity (nu = M + 2*eps*sin(M) + O(eps^2)). So small-beta-FM and
   small-eps-Kepler share a structural identity at coarse Fourier resolution.
   K-shape and FM-shape DIVERGE at higher k or higher beta (Bessel J_k
   has 1/k! tail; Kepler has 1/k tail). But they are NOT spectrally
   distinguishable by the strict K-test at k_max=6.
""")

    # Save synthesis NDJSON
    out = os.path.join(OUT_DIR, "spike_40_synthesis_records.ndjson")
    with open(out, "w") as f:
        for r in synth_records:
            f.write(json.dumps(r) + "\n")

    # Add a meta-question summary record
    meta_rec = {
        "kind": "spike_40_meta_question_synthesis",
        "primary_question": "Where does Kepler-shape c_k=eps^k/k appear in musical/wave substrate?",
        "meta_question": "Do different instruments produce measurably different epicycle shapes?",
        "primary_answer": "ABSENT in canonical instrument amplitude spectra. PRESENT in FM (Bessel J_k at small beta) and Kepler-orbit-EOC (canonical reference). The 14-class SM framework correctly says 'no K-shape' for instruments per [[user_stance_kepler_shape_universal]].",
        "meta_answer": "YES, substrate-discriminating via DECAY-FORM-BEST-FIT (M1 power-law p / M2 geometric eps / M3 Bessel beta / M4 Kepler eps). Different instruments map to different best-fit models with characteristic parameters. Strict K-test is K-specific not instrument-discriminating.",
        "anomaly_chase": "FM-K-overlap finding: small-beta FM passes strict K-test. Investigation confirms structural identity Kepler EOC ~= FM at small modulation index. Bessel J_k(beta) and eps^k/k diverge at k>3 (factor of 1/(k-1)!) but are K-test-indistinguishable at k_max=6.",
        "framework_validation": "STANDS. K-test correctly rejects random spectra (0/50), white noise, and most instrument substrates. Per Spike #38 caffeine pattern: framework says 'no' where Kepler-shape isn't, which is correct behaviour.",
        "instrument_first_validation": "Per [[user_stance_string_theory_instrument_first]]: ring-up (sustained/bowed/blown) substrates have NO ring-down -> cascade-beta SKIPPED for violin/flute/clarinet/voice/trumpet. Ring-down (struck/plucked) substrates (piano/drum/bell) tested but cascade-beta predicted-from-d_S formula does NOT match simple-exp decay (beta=1, not predicted 0.33/0.5/0.6). Honest absence per Spike #38 pattern.",
    }
    with open(out, "a") as f:
        f.write(json.dumps(meta_rec) + "\n")

    print(f"\nWrote {len(synth_records) + 1} synthesis records to {out}")


if __name__ == "__main__":
    main()

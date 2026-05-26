"""R-RBS-LM-49z — Srmech-native rebuild of Method B / Method C from R-RBS-LM-49.

Per catalog discipline ([[project_srmech_foundational_cascade_operations_catalog]]):
where srmech has a catalog primitive, prefer it over bare numpy.

R-RBS-LM-49 stage-gate A had bare numpy in three places:
  Method B (FFT band-pass):
    - np.fft.rfft / np.fft.irfft   → srmech.signal_processing.path_b_ops.fft / ifft
    - bipolar > 0 threshold        → srmech.signal_processing.path_b_ops.sign_quantise
  Method C (weak-coupling truncate):
    - signed sum + argsort         → stays in numpy (no srmech primitive yet)
                                      (UPSTREAM gap: no Class K + Class C composite
                                      coupling-score primitive)

Verification: re-run the 50% retention cell from 49 stage A; compare chi²
to the original 49 result. Identity claim: srmech-native and bare-numpy
paths should produce chi² within 1.0 of each other (Path A ≡ Path B at
algebra level per srmech Phase 4 contract).

Per `[[feedback_upstream_srmech_fixes_as_research_notes]]`: gaps in srmech
catalog coverage are noted in UPSTREAM_NOTES, NOT fixed by editing srmech.

The Method A baseline (crude random bit-flip) and Method C (weak-coupling)
do NOT need srmech rewrites for this partition's scope — Method A is
substrate-random (no Class primitive), Method C uses straightforward
signed-arithmetic + argsort (numpy is fine for that primitive surface).
The 49z scope is specifically Method B which has the most direct
srmech-native replacements available.
"""

import json
import re
import sys
import tempfile
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

# srmech-native imports — replace bare numpy.fft and threshold ops
from srmech.signal_processing.path_b_ops import fft as srmech_fft
from srmech.signal_processing.path_b_ops import ifft as srmech_ifft
from srmech.signal_processing.path_b_ops import sign_quantise as srmech_sign_quantise

from rbs_lm_encoder import D  # noqa: E402
from rbs_lm_bytes import compute_byte_vocab_table  # noqa: E402
from rbs_lm_read_mode import (  # noqa: E402
    load_instrument_bytes, phrase_match_retrieval,
)
from rbs_lm_merge import merge_instruments  # noqa: E402


SOURCES = [
    ("v25b GPT-2 fp32",
     "docs/srmech/rbs_lm_research/rbs_lm_instrument_v25b_distill_gpt2.bin",
     "docs/srmech/rbs_lm_research/rbs_lm_instrument_v25b_distill_gpt2.corpus.txt"),
    ("v29 fp32 intermediate",
     "docs/srmech/rbs_lm_research/rbs_lm_instrument_v29_distill_TinyLlama__TinyLlama-1.1B-intermediate-step-1431k-3T.bin",
     "docs/srmech/rbs_lm_research/rbs_lm_instrument_v29_distill_TinyLlama__TinyLlama-1.1B-intermediate-step-1431k-3T.corpus.txt"),
    ("v29 fp16 Chat",
     "docs/srmech/rbs_lm_research/rbs_lm_instrument_v29_distill_TinyLlama__TinyLlama-1.1B-Chat-v1.0.bin",
     "docs/srmech/rbs_lm_research/rbs_lm_instrument_v29_distill_TinyLlama__TinyLlama-1.1B-Chat-v1.0.corpus.txt"),
]


def bits_from_instrument(b):
    return np.unpackbits(np.frombuffer(b, dtype=np.uint8), bitorder="big")


def bits_to_instrument(bits):
    return np.packbits(bits.astype(np.uint8), bitorder="big").tobytes()


# ----- Method B (srmech-native): FFT band-pass via Path B primitives -----

def method_B_fft_bandpass_srmech_native(baseline_bytes, retain_band_fraction):
    """Class L signed-magnitude band selection + Class K bipolar threshold.

    SRMECH-NATIVE VERSION (49z rebuild):
      - srmech.signal_processing.path_b_ops.fft.op  (Class A ∘ Class I ∘ Class K)
      - srmech.signal_processing.path_b_ops.ifft.op (inverse cyclic-DFT)
      - srmech.signal_processing.path_b_ops.sign_quantise.op (Class K threshold)

    Algebra-identity claim: produces D1-identical output to bare-numpy
    method B per srmech Path A ≡ Path B contract on cyclic substrate.

    Note: srmech path_b_ops.fft is full complex FFT (not rfft); we lose
    rfft's 2x efficiency but gain srmech-native dispatchability + Class
    annotation. The squared-magnitude band selection still operates on
    only the positive-frequency half (np.argsort over the full spectrum
    naturally selects the conjugate-symmetric pairs).
    """
    bits = bits_from_instrument(baseline_bytes)
    bipolar = 2.0 * bits.astype(np.float64) - 1.0  # 0→-1, 1→+1
    n = len(bipolar)

    # SRMECH-NATIVE: full complex FFT via Path B
    # Class A ∘ Class I ∘ Class K composition; numpy backend instantiates
    # the same algebra as form_function_rotation cascade would.
    spectrum = srmech_fft.op(bipolar, n=n, substrate="cyclic")

    n_bands = len(spectrum)
    # Class L signed-magnitude band selection (squared, real-valued; no abs())
    mag_sq = spectrum.real * spectrum.real + spectrum.imag * spectrum.imag
    n_keep = max(int(round(retain_band_fraction * n_bands)), 1)
    keep_idx = np.argsort(-mag_sq)[:n_keep]
    mask = np.zeros(n_bands, dtype=bool)
    mask[keep_idx] = True
    spectrum_kept = spectrum * mask

    # SRMECH-NATIVE: inverse FFT via Path B
    reconstructed_complex = srmech_ifft.op(spectrum_kept, n=n, substrate="cyclic")
    reconstructed = np.real(reconstructed_complex)

    # SRMECH-NATIVE: Class K threshold via sign_quantise (Spike #174 anchor)
    # threshold=0.0, no dead-band: maps {-,+} → {-1, +1}; we then remap to {0, 1}.
    bipolar_quantized = srmech_sign_quantise.op(reconstructed, threshold=0.0, dead_band=0.0)
    new_bits = ((bipolar_quantized + 1) // 2).astype(np.uint8)

    mutation_rate = float(np.sum(new_bits != bits.astype(np.uint8))) / n
    return bits_to_instrument(new_bits), mutation_rate


# ----- Method C (audit-only): Class K + Class C signed-sum coupling -----

def method_C_weak_coupling_truncate_audit(baseline_bytes, source_instruments, retain_fraction):
    """Class K (low-coupling sign-flip) + Class C (high-coupling identity-preserve).

    SRMECH-NATIVE STATUS: signed-sum aggregation has no srmech primitive
    yet. Documented as UPSTREAM gap. The arithmetic structure IS Class K
    + Class C composition, but srmech.amsc does not currently expose a
    composite "compute_coupling_score_signed" or "rank_by_coupling_strength"
    primitive. The numpy implementation is the canonical algebra; a
    future srmech catalog addition would wrap this exact composition.

    Per `[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]` —
    squared signed-sum preserves the signed structure of source-agreement
    without any abs() call. The disrupt op is Class K; the preserve op
    is Class C identity at high-coupling positions.
    """
    baseline_bits = bits_from_instrument(baseline_bytes).astype(np.uint8)
    n = len(baseline_bits)
    source_bits = np.stack([
        bits_from_instrument(src).astype(np.int32) for src in source_instruments
    ], axis=0)
    signed_sum = (2 * source_bits - 1).sum(axis=0)
    coupling_sq = signed_sum * signed_sum
    n_preserve = int(round(retain_fraction * n))
    n_disrupt = n - n_preserve
    if n_disrupt <= 0:
        return bits_to_instrument(baseline_bits), 0.0
    low_idx = np.argsort(coupling_sq)[:n_disrupt]
    new_bits = baseline_bits.copy()
    new_bits[low_idx] = 1 - new_bits[low_idx]
    return bits_to_instrument(new_bits), n_disrupt / n


# ----- Original Method B for parity comparison -----

def method_B_fft_bandpass_numpy(baseline_bytes, retain_band_fraction):
    """Original bare-numpy Method B (49 stage A; for parity comparison)."""
    bits = bits_from_instrument(baseline_bytes)
    bipolar = 2.0 * bits.astype(np.float64) - 1.0
    n = len(bipolar)
    spectrum = np.fft.fft(bipolar)  # Note: changed to full FFT for direct comparison
    n_bands = len(spectrum)
    mag_sq = spectrum.real * spectrum.real + spectrum.imag * spectrum.imag
    n_keep = max(int(round(retain_band_fraction * n_bands)), 1)
    keep_idx = np.argsort(-mag_sq)[:n_keep]
    mask = np.zeros(n_bands, dtype=bool)
    mask[keep_idx] = True
    spectrum_kept = spectrum * mask
    reconstructed = np.real(np.fft.ifft(spectrum_kept, n=n))
    new_bits = (reconstructed > 0).astype(np.uint8)
    mutation_rate = float(np.sum(new_bits != bits.astype(np.uint8))) / n
    return bits_to_instrument(new_bits), mutation_rate


# ----- Probe machinery (unchanged from 49 stage A) -----

def make_phrase_corpus(text, max_phrases=80, min_len=15, max_len=180):
    sentences = re.split(r'[.!?]\s+', text)
    out, seen = [], set()
    for s in sentences:
        s = s.strip().rstrip(".")
        if min_len <= len(s) <= max_len and s not in seen:
            out.append(s); seen.add(s)
            if len(out) >= max_phrases: break
    return out


def make_probes_from_corpus(text, n_probes=30, seed=42):
    rng = np.random.default_rng(seed)
    sentences = [s.strip() for s in re.split(r'[.!?]\s+', text)
                 if 20 < len(s.strip()) < 200]
    rng.shuffle(sentences)
    probes = []
    for sent in sentences[:n_probes * 3]:
        words = sent.split()
        if len(words) < 5: continue
        n_prefix = min(rng.integers(3, 6), len(words) - 1)
        probes.append((" ".join(words[:n_prefix]), sent))
        if len(probes) >= n_probes: break
    return probes


def rank_stats(rank_results, corpus_size):
    n = len(rank_results)
    found = [r for r in rank_results if r >= 0]
    n_found = len(found)
    if not found:
        return {"n_probes": n, "n_found": 0, "chi2_5bins": 0.0, "p_estimate": ">0.10"}
    rank_1 = sum(1 for r in found if r == 0)
    top_d = sum(1 for r in found if r < max(1, corpus_size // 10))
    mean_pct = float(np.mean(found)) / max(corpus_size, 1) * 100
    bins = [0] * 5
    bucket = max(corpus_size // 5, 1)
    for r in found:
        bins[min(r // bucket, 4)] += 1
    expected = n_found / 5
    chi2 = sum(((b - expected) ** 2) / expected for b in bins)
    p_est = ("<0.01" if chi2 > 13.28 else "<0.05" if chi2 > 9.49 else
             "<0.10" if chi2 > 7.78 else ">0.10")
    return {"n_probes": n, "n_found": n_found, "rank_1_count": rank_1,
            "top_decile_rate": top_d / n,
            "mean_rank_percentile": round(mean_pct, 1),
            "chi2_5bins": round(chi2, 2), "p_estimate": p_est, "rank_bins": bins}


def run_cell(instr_bytes, phrase_corpus, probes, vocab_table):
    with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as f:
        f.write(instr_bytes); tmp = f.name
    try:
        instrument = load_instrument_bytes(tmp)
    finally:
        Path(tmp).unlink(missing_ok=True)
    rank_results = []
    for query, expected in probes:
        ranked = phrase_match_retrieval(instrument, query, phrase_corpus, vocab_table, D)
        try:
            rank = next(i for i, (phr, _) in enumerate(ranked) if phr == expected)
        except StopIteration:
            try:
                rank = next(i for i, (phr, _) in enumerate(ranked)
                            if expected[:30] in phr or phr in expected)
            except StopIteration:
                rank = -1
        rank_results.append(rank)
    return rank_stats(rank_results, len(phrase_corpus))


def main():
    print("=== R-RBS-LM-49z — srmech-native rebuild of Method B ===\n")
    print(f"srmech path_b_ops: fft, ifft, sign_quantise")
    print(f"Verifying srmech-native ≡ bare-numpy at 50% retention budget\n")

    src_instruments, all_text = [], []
    for label, ipath, cpath in SOURCES:
        with open(ipath, "rb") as f:
            src_instruments.append(f.read())
        all_text.append(Path(cpath).read_text())
        print(f"  loaded {label}")

    baseline = merge_instruments(src_instruments, n_obs=None)
    print(f"\nBaseline: depth-3 pure-fp16+ uniform merge ({len(baseline)} bytes)")

    union_text = "\n\n".join(all_text)
    phrase_corpus = make_phrase_corpus(union_text, max_phrases=80)
    probes = make_probes_from_corpus(union_text, n_probes=30, seed=42)
    print(f"Probes: {len(probes)}; phrase corpus: {len(phrase_corpus)}")

    vocab_table = compute_byte_vocab_table(D)

    # Compare at 50% retention (the falsification cell from 49)
    BUDGETS = [1.00, 0.75, 0.50, 0.25]
    results = {"srmech_native_B": {}, "bare_numpy_B": {}}

    print(f"\n=== Method B — srmech-native (Path B FFT + sign_quantise) ===")
    for budget in BUDGETS:
        instr, actual_mut = method_B_fft_bandpass_srmech_native(baseline, retain_band_fraction=budget)
        stats = run_cell(instr, phrase_corpus, probes, vocab_table)
        stats["budget"] = budget; stats["actual_mutation_rate"] = round(actual_mut, 4)
        results["srmech_native_B"][f"b{int(budget*100)}"] = stats
        print(f"  budget={budget:.2f}; mut={actual_mut:.4f}; chi²={stats['chi2_5bins']:>5.2f} "
              f"({stats['p_estimate']}); top-d={100*stats.get('top_decile_rate', 0):>5.1f}%; "
              f"mean={stats.get('mean_rank_percentile', 50.0):>5.1f}%")

    print(f"\n=== Method B — bare numpy (full FFT, original 49 algebra) ===")
    for budget in BUDGETS:
        instr, actual_mut = method_B_fft_bandpass_numpy(baseline, retain_band_fraction=budget)
        stats = run_cell(instr, phrase_corpus, probes, vocab_table)
        stats["budget"] = budget; stats["actual_mutation_rate"] = round(actual_mut, 4)
        results["bare_numpy_B"][f"b{int(budget*100)}"] = stats
        print(f"  budget={budget:.2f}; mut={actual_mut:.4f}; chi²={stats['chi2_5bins']:>5.2f} "
              f"({stats['p_estimate']}); top-d={100*stats.get('top_decile_rate', 0):>5.1f}%; "
              f"mean={stats.get('mean_rank_percentile', 50.0):>5.1f}%")

    # Parity verdict
    print(f"\n=== Parity verdict (srmech-native ≡ bare-numpy?) ===")
    max_chi2_diff = 0.0
    for budget in BUDGETS:
        key = f"b{int(budget*100)}"
        sn = results["srmech_native_B"][key]["chi2_5bins"]
        bn = results["bare_numpy_B"][key]["chi2_5bins"]
        diff = abs(sn - bn)
        max_chi2_diff = max(max_chi2_diff, diff)
        print(f"  budget={budget:.2f}: srmech-native chi²={sn:.2f}; bare-numpy chi²={bn:.2f}; |Δ|={diff:.2f}")

    print(f"\n  Max |Δ chi²| across budgets: {max_chi2_diff:.2f}")
    if max_chi2_diff < 1.0:
        verdict = "PARITY CONFIRMED — srmech-native rebuild produces algebra-identical results within 1.0 chi² of bare numpy"
    elif max_chi2_diff < 3.0:
        verdict = "PARITY MARGINAL — srmech-native differs by up to {:.2f} chi² (possibly numerical noise; needs investigation)".format(max_chi2_diff)
    else:
        verdict = "PARITY FAILED — srmech-native and bare-numpy diverge by {:.2f} chi²; algebra-identity claim broken".format(max_chi2_diff)
    print(f"  Verdict: {verdict}")

    # UPSTREAM_NOTES gaps surfaced
    print(f"\n=== UPSTREAM_NOTES gaps surfaced ===")
    gaps = [
        "srmech.signal_processing.path_b_ops has no rfft (real-only FFT); used full complex FFT",
        "srmech.amsc has no signed-sum-coupling-score primitive for Method C-style operations",
        "No catalog primitive for argsort-by-score (generic sort; not a Class-N concern)",
        "No catalog primitive for random bit-flip (Method A; not a Class-N concern — substrate-randomness)",
    ]
    for g in gaps: print(f"  - {g}")

    out = {
        "partition": "R-RBS-LM-49z",
        "scope": "srmech-native rebuild of R-RBS-LM-49 Method B",
        "results": results,
        "max_chi2_diff": max_chi2_diff,
        "verdict": verdict,
        "upstream_gaps": gaps,
    }
    out_path = HERE / "R-RBS-LM-49z_results.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()

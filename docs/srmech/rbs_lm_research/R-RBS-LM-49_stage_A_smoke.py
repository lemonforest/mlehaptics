"""R-RBS-LM-49 stage-gate A — chainsaw vs surgical precision reduction.

Per user direction 2026-05-26: each design choice tested as falsifiable
hypothesis; convergence across cells IS the proof. This is stage-gate A
(primary 3x4 matrix). Sub-matrices B-E run only after A confirms the
basic chainsaw-vs-surgical pattern is observable.

Methods (all apply to a 1024-byte / 8192-bit cascade instrument):
  A — crude random bit-flip (Class K sign-flip at random positions)
  B — FFT band-pass (Class L signed-magnitude band selection; Class K
      threshold to bipolar)
  C — weak-coupling truncate (Class K sign-flip at low-coupling
      positions per R-RBS-LM-33; coupling measured via squared-signed-sum
      across sources — NO abs() per [[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]])

Baseline: depth-3 pure-fp16+ uniform merge (R-RBS-LM-46b chi² 32.55).
Budgets (bit retention): 100%, 75%, 50%, 25%.
Probes: same 30 probes as R-RBS-LM-46b (direct comparison).

Pre-registered falsification thresholds at 50% retention:
  - A < 7.78 AND B > 13.28 AND C > 13.28 → CONFIRMED
  - all three < 7.78 → FALSIFIED (precision-of-any-kind destroys)
  - all three > 13.28 → FALSIFIED (need lower budget for any signal)
  - mixed → partial; sub-matrices B-E recommended
"""

import json
import re
import sys
import tempfile
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "python"))
sys.path.insert(0, str(HERE))

from rbs_lm_encoder import D  # noqa: E402
from rbs_lm_bytes import compute_byte_vocab_table  # noqa: E402
from rbs_lm_read_mode import (  # noqa: E402
    load_instrument_bytes, phrase_match_retrieval, baseline_random_phrase_sim,
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


# -------- Method A: Crude random bit-flip (Class K sign-flip; random) --------

def method_A_crude_random(baseline_bytes, mutation_rate, seed=42):
    """Class K (sign-flip at the chosen bit positions; random selection).
    NO abs(). Sign-flip is the canonical Class K phase-boundary operation.
    """
    bits = bits_from_instrument(baseline_bytes).astype(np.uint8)
    n = len(bits)
    rng = np.random.default_rng(seed)
    n_flip = int(round(mutation_rate * n))
    if n_flip == 0:
        return bits_to_instrument(bits), 0.0
    flip_idx = rng.choice(n, size=n_flip, replace=False)
    bits[flip_idx] = 1 - bits[flip_idx]
    return bits_to_instrument(bits), n_flip / n


# -------- Method B: FFT band-pass (Class L band selection + Class K threshold) --------

def method_B_fft_bandpass(baseline_bytes, retain_band_fraction):
    """Class L signed-magnitude band selection + Class K bipolar threshold.

    Bits → bipolar floats (-1, +1) → rFFT → preserve top-K bands by
    squared-magnitude (Class L) → inverse rFFT → Class K sign-flip threshold
    (>0 → +1; ≤0 → -1) → back to bits (0/1).

    Squared-magnitude (not abs()) per
    [[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]: the
    selection criterion is computed as a Class L variant.
    """
    bits = bits_from_instrument(baseline_bytes)
    bipolar = 2.0 * bits.astype(np.float64) - 1.0  # 0→-1, 1→+1
    n = len(bipolar)
    spectrum = np.fft.rfft(bipolar)
    n_bands = len(spectrum)
    # Class L: squared magnitude (signed structure preserved via complex sq-norm)
    mag_sq = spectrum.real * spectrum.real + spectrum.imag * spectrum.imag
    n_keep = int(round(retain_band_fraction * n_bands))
    if n_keep < 1:
        n_keep = 1
    keep_idx = np.argsort(-mag_sq)[:n_keep]
    mask = np.zeros(n_bands, dtype=bool)
    mask[keep_idx] = True
    spectrum_kept = spectrum * mask
    reconstructed = np.fft.irfft(spectrum_kept, n=n)
    # Class K threshold: sign decides bipolar
    new_bits = (reconstructed > 0).astype(np.uint8)
    mutation_rate = float(np.sum(new_bits != bits.astype(np.uint8))) / n
    return bits_to_instrument(new_bits), mutation_rate


# -------- Method C: Weak-coupling truncate (Class K sign-flip at low-coupling positions) --------

def method_C_weak_coupling_truncate(baseline_bytes, source_instruments,
                                     retain_fraction):
    """Per R-RBS-LM-33 weak_coupling_mask. Identify bits where source
    instruments split toward 50/50 (low signed-sum squared); flip those.
    Preserve bits where sources strongly agree (high signed-sum squared).

    NO abs(): coupling strength is the squared signed sum (Class L
    computation), which preserves the signed structure of source-agreement.
    The disrupt operation is Class K sign-flip; the preserve operation is
    Class C chirality-preservation (identity at high-coupling positions).
    """
    baseline_bits = bits_from_instrument(baseline_bytes).astype(np.uint8)
    n = len(baseline_bits)
    source_bits = np.stack([
        bits_from_instrument(src).astype(np.int32) for src in source_instruments
    ], axis=0)  # (n_sources, n_bits)
    signed_sum = (2 * source_bits - 1).sum(axis=0)  # in {-n, ..., +n}
    coupling_sq = signed_sum * signed_sum  # squared; preserves signed structure
    n_preserve = int(round(retain_fraction * n))
    n_disrupt = n - n_preserve
    if n_disrupt <= 0:
        return bits_to_instrument(baseline_bits), 0.0
    # Class K: sign-flip the LOW-coupling bits
    low_idx = np.argsort(coupling_sq)[:n_disrupt]
    new_bits = baseline_bits.copy()
    new_bits[low_idx] = 1 - new_bits[low_idx]
    return bits_to_instrument(new_bits), n_disrupt / n


# -------- Common: probe corpus, rank stats --------

def make_phrase_corpus(text, max_phrases=80, min_len=15, max_len=180):
    sentences = re.split(r'[.!?]\s+', text)
    out, seen = [], set()
    for s in sentences:
        s = s.strip().rstrip(".")
        if min_len <= len(s) <= max_len and s not in seen:
            out.append(s)
            seen.add(s)
            if len(out) >= max_phrases:
                break
    return out


def make_probes_from_corpus(text, n_probes=30, seed=42):
    rng = np.random.default_rng(seed)
    sentences = [s.strip() for s in re.split(r'[.!?]\s+', text)
                 if 20 < len(s.strip()) < 200]
    rng.shuffle(sentences)
    probes = []
    for sent in sentences[:n_probes * 3]:
        words = sent.split()
        if len(words) < 5:
            continue
        n_prefix = min(rng.integers(3, 6), len(words) - 1)
        probe = " ".join(words[:n_prefix])
        probes.append((probe, sent))
        if len(probes) >= n_probes:
            break
    return probes


def rank_stats(rank_results, corpus_size):
    n = len(rank_results)
    found = [r for r in rank_results if r >= 0]
    n_found = len(found)
    if not found:
        return {"n_probes": n, "n_found": 0,
                "chi2_5bins": 0.0, "p_estimate": ">0.10"}
    q_t = max(1, corpus_size // 4)
    d_t = max(1, corpus_size // 10)
    rank_1 = sum(1 for r in found if r == 0)
    top_q = sum(1 for r in found if r < q_t)
    top_d = sum(1 for r in found if r < d_t)
    mean_pct = float(np.mean(found)) / max(corpus_size, 1) * 100
    bins = [0] * 5
    bucket = max(corpus_size // 5, 1)
    for r in found:
        bins[min(r // bucket, 4)] += 1
    expected = n_found / 5
    chi2 = sum(((b - expected) ** 2) / expected for b in bins)
    p_est = ("<0.01" if chi2 > 13.28 else "<0.05" if chi2 > 9.49 else
             "<0.10" if chi2 > 7.78 else ">0.10")
    return {
        "n_probes": n, "n_found": n_found,
        "rank_1_count": rank_1, "rank_1_rate": rank_1 / n,
        "top_quartile_count": top_q, "top_quartile_rate": top_q / n,
        "top_decile_count": top_d, "top_decile_rate": top_d / n,
        "mean_rank_percentile": round(mean_pct, 1),
        "chi2_5bins": round(chi2, 2), "p_estimate": p_est,
        "rank_bins": bins,
    }


def run_cell(instr_bytes, phrase_corpus, probes, vocab_table):
    with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as f:
        f.write(instr_bytes)
        tmp = f.name
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
    print("=== R-RBS-LM-49 stage-gate A — chainsaw-vs-surgical primary 3x4 ===\n")
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
    BUDGETS = [1.00, 0.75, 0.50, 0.25]
    results = {}

    print(f"\n=== Method A: crude random bit-flip ===")
    for budget in BUDGETS:
        mutation_rate = 1.0 - budget
        instr, actual_mut = method_A_crude_random(baseline, mutation_rate, seed=42)
        stats = run_cell(instr, phrase_corpus, probes, vocab_table)
        stats["method"] = "A_crude"
        stats["target_budget"] = budget
        stats["actual_mutation_rate"] = round(actual_mut, 4)
        results[f"A_b{int(budget*100)}"] = stats
        print(f"  budget={budget:.2f}; mut={actual_mut:.4f}; "
              f"chi²={stats['chi2_5bins']:>5.2f} ({stats['p_estimate']}); "
              f"top-d={100*stats.get('top_decile_rate', 0):>5.1f}%; "
              f"mean={stats.get('mean_rank_percentile', 50.0):>5.1f}%")

    print(f"\n=== Method B: FFT band-pass ===")
    for budget in BUDGETS:
        instr, actual_mut = method_B_fft_bandpass(baseline, retain_band_fraction=budget)
        stats = run_cell(instr, phrase_corpus, probes, vocab_table)
        stats["method"] = "B_fft_bandpass"
        stats["target_budget"] = budget
        stats["actual_mutation_rate"] = round(actual_mut, 4)
        results[f"B_b{int(budget*100)}"] = stats
        print(f"  band-budget={budget:.2f}; mut={actual_mut:.4f}; "
              f"chi²={stats['chi2_5bins']:>5.2f} ({stats['p_estimate']}); "
              f"top-d={100*stats.get('top_decile_rate', 0):>5.1f}%; "
              f"mean={stats.get('mean_rank_percentile', 50.0):>5.1f}%")

    print(f"\n=== Method C: weak-coupling truncate (Class K + Class C; no abs()) ===")
    for budget in BUDGETS:
        instr, actual_mut = method_C_weak_coupling_truncate(
            baseline, src_instruments, retain_fraction=budget)
        stats = run_cell(instr, phrase_corpus, probes, vocab_table)
        stats["method"] = "C_weak_coupling"
        stats["target_budget"] = budget
        stats["actual_mutation_rate"] = round(actual_mut, 4)
        results[f"C_b{int(budget*100)}"] = stats
        print(f"  retain={budget:.2f}; mut={actual_mut:.4f}; "
              f"chi²={stats['chi2_5bins']:>5.2f} ({stats['p_estimate']}); "
              f"top-d={100*stats.get('top_decile_rate', 0):>5.1f}%; "
              f"mean={stats.get('mean_rank_percentile', 50.0):>5.1f}%")

    # Summary
    print(f"\n\n{'='*72}\n=== R-RBS-LM-49 stage-gate A SUMMARY\n{'='*72}\n")
    print(f"  {'method':<18s} {'budget':>7s} {'mut_rate':>9s} {'chi²':>7s} "
          f"{'p-est':>7s} {'top-d%':>7s} {'mean%':>7s}")
    print(f"  {'-'*18} {'-'*7} {'-'*9} {'-'*7} {'-'*7} {'-'*7} {'-'*7}")
    for method in ["A_crude", "B_fft_bandpass", "C_weak_coupling"]:
        for budget in BUDGETS:
            key = f"{method[0]}_b{int(budget*100)}"
            r = results[key]
            print(f"  {r['method']:<18s} {r['target_budget']:>6.2f} "
                  f"{r['actual_mutation_rate']:>9.4f} "
                  f"{r['chi2_5bins']:>7.2f} {r.get('p_estimate', '?'):>7s} "
                  f"{100*r.get('top_decile_rate', 0):>6.1f}% "
                  f"{r.get('mean_rank_percentile', 50.0):>6.1f}%")

    # Falsification reading at 50% retention
    print(f"\n=== Pre-registered falsification (at 50% retention) ===")
    b50_A = results["A_b50"]["chi2_5bins"]
    b50_B = results["B_b50"]["chi2_5bins"]
    b50_C = results["C_b50"]["chi2_5bins"]
    print(f"  A (crude): chi² = {b50_A:.2f}")
    print(f"  B (FFT):   chi² = {b50_B:.2f}")
    print(f"  C (weak):  chi² = {b50_C:.2f}")

    if b50_A < 7.78 and b50_B > 13.28 and b50_C > 13.28:
        verdict = "CONFIRMED — A destroys; B and C preserve at 50% budget"
    elif b50_A < 7.78 and b50_B < 7.78 and b50_C < 7.78:
        verdict = "FALSIFIED — precision-reduction-of-any-kind destroys"
    elif b50_A > 13.28 and b50_B > 13.28 and b50_C > 13.28:
        verdict = "FALSIFIED in opposite direction — even crude doesn't destroy at 50%"
    elif b50_B > 13.28 and b50_C < 7.78:
        verdict = "PARTIAL — spectral (B) preserves; coupling-aware (C) fails"
    elif b50_C > 13.28 and b50_B < 7.78:
        verdict = "PARTIAL — coupling-aware (C) preserves; spectral (B) fails"
    else:
        verdict = "MIXED — partial; sub-matrices B-E recommended"

    print(f"\n  Verdict: {verdict}")
    proceed = (b50_A < 7.78) or (b50_B > 13.28 and b50_C > 13.28)
    print(f"  Proceed to sub-matrices B-E: {proceed}")

    out = {
        "stage": "A",
        "baseline": "depth-3 pure-fp16+ uniform merge",
        "n_corpus": len(phrase_corpus),
        "n_probes": len(probes),
        "budgets": BUDGETS,
        "methods": ["A_crude", "B_fft_bandpass", "C_weak_coupling"],
        "thresholds": {"signal_p_010": 7.78, "strong_p_001": 13.28},
        "results": results,
        "verdict": verdict,
        "proceed_to_BCDE": proceed,
    }
    out_path = Path("docs/srmech/rbs_lm_research/R-RBS-LM-49_stage_A_results.json")
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()

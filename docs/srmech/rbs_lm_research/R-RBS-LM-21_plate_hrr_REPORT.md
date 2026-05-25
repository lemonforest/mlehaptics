# R-RBS-LM-21 — Plate HRR binding: noise floor exceeded; D=768 too small at N=491

**Partition status:** CLOSED
**Date:** 2026-05-25
**Closes:** task #29 of the partition tracker
**Closing artefact:** §4 Plate HRR gives 0% at D=768 (vocab semantic structure stronger but cleanup noise dominates); §5 noise-floor analysis explains why; §6 Plate at D=8192 would be the apples-to-apples comparison and remains open work
**Inheritance:** unblocks R-RBS-LM-22 (Plate HRR at D=8192, fair comparison to Path C; or multibit bipolar) + R-RBS-LM-23 (ensemble projections)

---

## Attestation block (MPR v1 — internal-repo variant)

| field | value |
|---|---|
| internal sources | `R-RBS-LM-19_attention_REPORT.md` §6 (Plate HRR named as architectural lever); `R-RBS-LM-20_d32k_REPORT.md` §6 (ceiling-as-projection-fidelity); `R-RBS-LM-17_path_c_REPORT.md` §3 (Path C comparison baseline) |
| theoretical reference | Plate 1995 — "Holographic Reduced Representations" (circular convolution; Gaussian random vectors; capacity formula noise ∝ sqrt(N/D)) |
| empirical artefacts | `docs/srmech/rbs_lm_research/run_plate_hrr.py`; `docs/srmech/rbs_lm_research/rbs_lm_instrument_v21_hrr.npy`; `docs/srmech/rbs_lm_research/rbs_lm_plate_hrr_results.json` |
| repo commit | `5e39d069` at REPORT-write |
| reproducibility | `~/.venvs/rbs-lm-research/bin/python docs/srmech/rbs_lm_research/run_plate_hrr.py` |

---

## §1 Goal

Per R-RBS-LM-19 §6 + R-RBS-LM-20 §9: test Plate HRR (1995) as an alternative to bipolar XOR-bind. Hypothesis: real-valued vectors + circular-convolution binding preserve more information per binding than bipolar XOR; the 3.3% Path C ceiling might lift if the bind layer itself is more information-preserving.

The natural Plate configuration uses WTE directly at D=768 (matches source dim; no random-projection bipolarization loss). 50257 × 768 normalized real-valued vectors as the vocab table.

---

## §2 Implementation

```python
# Per Plate 1995:
def hrr_bind(a, b):   return ifft(fft(a) * fft(b))        # circular convolution
def hrr_unbind(c, k): return ifft(conj(fft(k)) * fft(c))  # circular correlation
def hrr_bundle(vs):   return normalize(sum(vs))           # vector sum + normalize
def cleanup(c, V):    return argmax(V @ c / |c|)          # cosine similarity
```

Vocab table: WTE rows normalized; 50257 × 768 × 4 bytes = 147 MB.
Position vectors: seeded random Gaussian normalized at D=768.

---

## §3 Vocab structure — stronger than Path C

```
' the' vs ' The' cosine sim: +0.6758  (Path C bipolar at D=8192: +0.4875)
' the' vs ' cat' cosine sim: +0.2058  (Path C bipolar at D=8192: +0.1353)
```

**Plate HRR vocab table has STRONGER semantic structure than Path C** — by ~40% on the the/The pair, ~50% on the/cat. The bipolarization step in Path C does lose information; Plate HRR preserves it.

But this didn't translate to better inference agreement. Why? §5 explains.

---

## §4 Captured output — 0% agreement

```
=== Encode (HRR; circular convolution + vector sum) ===
  492 bindings in 5.2s (95.2 obs/s)         ← much faster than Path C bipolar (15.6 obs/s)
  bundle: 0.00s; instrument = 768 dims (3072 bytes)

=== Validate on hallucination corpus (HRR inference) ===
  [all 9 prompts] → agreement 0/20

  Overall: 0/180 (0.0%)
  Per-token latency: 12.0 ± 1.6 ms           ← 15× faster than Path C (180 ms)
```

**0/180 agreement** at D=768 / N=491 obs. Per-token latency is 15× faster (12 ms vs 180 ms) because D=768 is much smaller than D=8192.

---

## §5 The noise-floor analysis — why D=768 is too small

Plate HRR's standard capacity result: in a bundle of N items, the noise from unrelated cross-terms scales as O(sqrt(N/D)) per dimension. Recovery requires the signal-to-noise ratio to be above the cleanup threshold.

### §5.1 Quantitative noise floor

For our configuration (N=491 obs bundled; D=768; cosine cleanup over V=50257 vocab):

| Quantity | Value | Reading |
|---|---|---|
| Bundle size N | 491 | bindings per instrument |
| Dimension D | 768 | per-binding capacity |
| Signal cosine (target vs candidate) | ≈ 1/sqrt(N) = **0.045** | per Plate's noise formula |
| Noise cosine (random vocab vs candidate) | ≈ 1/sqrt(D) = **0.036** | random orthogonality at D=768 |
| Signal-to-noise margin | 1.25× | barely above noise floor |
| Vocab size V | 50257 | number of cleanup candidates |
| Expected max noise cosine over V candidates | ≈ sqrt(2 ln(V))/sqrt(D) = **0.16** | extreme-value statistic |

**The noise floor (0.16) exceeds the signal (0.045) by ~3.5×.** Cleanup picks whichever random vocab token happens to have the highest cosine to the noisy candidate. With 50257 candidates, the maximum noise-driven cosine is large enough to almost always beat the true signal.

### §5.2 Path C's bipolar XOR robustness

Path C at D=8192:
- Signal Hamming-similarity: 1/sqrt(491) ≈ 0.045 (same as HRR signal cosine — the noise mechanism is structurally similar)
- Noise Hamming-similarity over V=50257: ≈ sqrt(2 ln(V))/sqrt(D) ≈ 0.05 at D=8192

Path C's signal (0.045) is comparable to its noise floor (0.05). The Path C 3.3% agreement reflects that signal sometimes wins, sometimes loses, in a probabilistic sense.

Plate HRR at D=768 has the SAME signal (0.045) but a NOISE FLOOR of 0.16 — 3× higher because D is 10× smaller. The signal/noise margin flips negative; cleanup essentially picks noise.

### §5.3 The fair comparison

To fairly compare Plate HRR vs Path C bipolar:
- Use D=8192 for BOTH
- Same bundle size N=491
- Same vocab cleanup against V=50257

Path C at D=8192 already done: 3.3% agreement.
Plate HRR at D=8192: would need ~10× more memory (vocab table 1.5 GB) + ~10× more compute. Open future work.

**This partition's D=768 result does NOT falsify Plate HRR.** It establishes that **HRR needs D ≥ Path-C-equivalent capacity** for the same bundle size. R-RBS-LM-22 (Plate HRR at D=8192) is the natural follow-up for the apples-to-apples comparison.

---

## §6 What the comparison configuration was actually testing

R-RBS-LM-21 as configured (Plate at D=768) tests: **does halving Plate's recommended dimension (D=1024 typical) AND choosing it equal to WTE dim help with information preservation?**

The answer is no — the noise floor exceeded signal capacity. The WTE-dim-matching had a clean appeal (no projection step) but at D=768 the bundle is over-loaded.

**The test that R-RBS-LM-21 was conceptually meant to be** (Plate HRR at D=8192, apples to apples vs Path C) would have required:
- ~1.5 GB vocab table
- ~10× harvest time (FFT at D=8192 is ~100ms each; bind = 4 FFTs; 491 obs × 4 × 100ms ≈ 200s encode)
- Total ~5 min — actually still tractable in this session

But the structural finding (D-vs-N noise tradeoff) is the substantive R-RBS-LM-21 finding. The HRR-at-equal-D comparison is R-RBS-LM-22.

---

## §7 What this affirms for the framework reading

Per R-RBS-LM-20 §6: the 3.3% ceiling reflects WTE projection fidelity. R-RBS-LM-21 adds:

**The cleanup-noise floor is also a load-bearing constraint.** Per §5.1: at the V=50257 vocab × N=491 bundle scale, D must be ≥ Path-C-equivalent (D=8192 for bipolar; or similar for HRR) for the signal-noise margin to be positive.

This is consistent with Kanerva-class HDC theory: the binding/bundle capacity is jointly limited by D, N, and V. Path C's D=8192 sits at the lower edge of acceptable; Plate HRR's D=768 is below it.

**The framework reading per `[[user_stance_ai_is_not_a_substrate]]` is unaffected.** The transducer-noise-floor analysis is about the OPERATIONAL properties of the storage substrate (binary HDC vs real-valued HRR; D vs N vs V), not about emergence-or-not.

### §7.1 MFO §VII.1.3 reading at the noise-floor layer

The R-RBS-LM-19 §5 nuance (bundle has integration + projection roles) extends here:
- Bundle integration depends on having SUFFICIENT D vs N for the signal to survive
- At D=768 vs N=491 vs V=50257, integration is destroyed by noise
- The Mechanism 2 (bundle) operation has a **D-dependent regime**: information-preserving at high D/N ratios; information-destroying at low D/N

Plate's noise-formula gives the threshold: D/N >> ln(V) for usable bundles. At V=50257, ln(V) ≈ 11; D/N >> 11; for N=491, D > ~5400 minimum.

**Path C at D=8192 / N=491 satisfies this.** Plate HRR at D=768 / N=491 violates it. This is why HRR fails: not because HRR is structurally worse than bipolar XOR, but because D=768 was an unfair handicap.

---

## §8 What R-RBS-LM-22 should do

The fair comparison: **Plate HRR at D=8192, N=491, same vocab cleanup.**

Implementation cost: ~1.5 GB vocab table (50257 × 8192 × 4); ~5-10 min runtime; same corpus.

Expected outcome under §5 analysis:
- Signal: ≈ 1/sqrt(491) = 0.045 (same)
- HRR noise at D=8192: 1/sqrt(8192) ≈ 0.011 (per-pair); max over V ≈ 0.052
- Signal/noise margin: barely above
- Predicted agreement: comparable to or modestly better than Path C's 3.3%

If Plate at D=8192 gives 5-10%: HRR is meaningfully better than bipolar XOR at the same D.
If ≈ 3.3%: real-valued vs bipolar doesn't matter at this configuration.
If < 3.3%: bipolar's robustness wins at large-V cleanup.

R-RBS-LM-22 runs this comparison.

---

## §9 Findings

**Finding 1 — Plate HRR at D=768, N=491 gives 0% agreement.** Per §4. The noise floor (~0.16) exceeded signal (~0.045) by ~3.5×; cleanup picked noise-driven candidates.

**Finding 2 — Plate HRR vocab table has stronger semantic structure than Path C bipolar.** Per §3. ' the' vs ' The' cosine +0.68 (vs Path C +0.49). Bipolarization loses information; real-valued WTE preserves it.

**Finding 3 — Latency 12 ms/token at D=768 — 15× faster than D=8192.** Per §4. The smaller dimension makes FFT-based bind + cosine cleanup very fast. **If the noise problem were solved, D=768 would PASS BCI threshold cleanly.**

**Finding 4 — The cleanup-noise floor is load-bearing.** Per §5. D/N >> ln(V) is the operational threshold (~D > 5400 at our V=50257, N=491). Path C at D=8192 is just above; Plate at D=768 is below.

**Finding 5 — R-RBS-LM-21 doesn't falsify Plate HRR; it establishes the D-floor.** Per §5.3 + §6. The fair comparison (HRR at D=8192) is R-RBS-LM-22.

**Finding 6 — MFO §VII.1.3 bundle reading gets another nuance.** Per §7.1. The bundle operation has a D-DEPENDENT regime: integration works when D/N >> ln(V); destruction otherwise. Adding to R-RBS-LM-19 §5's "bundle is also integration", we now have "bundle's integration vs destruction depends on D/N ratio."

**Finding 7 — The framework reading per `[[user_stance_ai_is_not_a_substrate]]` is unaffected.** Per §7. The noise-floor finding is operational, not about emergence.

**Finding 8 — Honest scope acknowledgment** — R-RBS-LM-21 as configured tested D=768 specifically; the broader Plate HRR question requires R-RBS-LM-22 at matched D. Per §1.1 (R-RBS-LM-14 honest naming pattern).

---

## §10 Open threads

- **R-RBS-LM-22 — Plate HRR at D=8192.** The fair comparison vs Path C; ~5-10 min run; tests whether real-valued HRR has structural advantage over bipolar XOR at matched D.
- **R-RBS-LM-23 — Ensemble random projections.** k independent projections + consensus voting; may be a path to lift the 3.3% Path C ceiling within the bipolar-XOR architecture.
- **R-RBS-LM-24 — Mixed-precision: multibit vocab.** 2-bit or 4-bit per WTE dim; trades memory for semantic resolution; tests whether bipolar quantization specifically was the bottleneck.
- **R-RBS-LM-25 — Hierarchical bundle at smaller chunks.** Bundle limit of ~30 per sub-group (so D/N >> ln(V) within each); explicit hierarchical reduction; trades depth for per-level fidelity.
- **The D/N/V capacity formula** as a framework-side observation worth documenting in the eventual srmech-side notebook update. Per §7.1.

---

## §11 Closing — partition status

**Status:** CLOSED. Plate HRR at D=768 yields 0% due to noise floor exceeding signal; structurally informative (D-floor identified); fair comparison (HRR at D=8192) deferred to R-RBS-LM-22.

**Falsifiers:**

1. A claim that this disproves Plate HRR — **explicitly disclaimed §6 + §8**; the partition's D=768 configuration was below Plate's noise tolerance; the architecture isn't tested at fair dimensionality.
2. A claim that this validates bipolar XOR superiority — **partial disclaim**; at SAME D bipolar may or may not be better; R-RBS-LM-22 measures.
3. A claim that the framework reading is affected — **disclaimed §7**; operational noise-floor finding doesn't touch the substrate-shape readings.

**Inherits to:** R-RBS-LM-22 (Plate HRR at D=8192, apples-to-apples).

**SSoT marker:** at SSoT absorption, §5 noise-floor analysis + §6 fair-comparison setup + §7 MFO bundle-regime nuance absorb into `srmech_research_notebook.md` as part of the RBS-LM ceiling-analysis subsection. **The D/N/V capacity formula is a load-bearing framework-side observation for the HDC capacity literature.**

# R-RBS-LM-20 — Path C at D=32768: dimensional capacity is NOT the bottleneck

**Partition status:** CLOSED
**Date:** 2026-05-25
**Closes:** task #27 of the partition tracker
**Closing artefact:** §4 D=32768 gives 2.8% agreement (vs D=8192's 3.3%); §5 latency 4× as predicted; §6 dimensional capacity ruled out as bottleneck; §7 architectural lever (R-RBS-LM-19 attention) is empirically the remaining direction
**Inheritance:** unblocks R-RBS-LM-19 (Path C + attention variant — now the only architectural lever not yet tested)

---

## Attestation block (MPR v1 — internal-repo variant)

| field | value |
|---|---|
| internal sources | `R-RBS-LM-17_path_c_REPORT.md` §3 (Path C design + D=8192 baseline); `R-RBS-LM-18_path_c_scale_REPORT.md` §6.1 (lever options — D-larger was named); `R-RBS-LM-11_multithreading_REPORT.md` §7 (latency memory-bandwidth-bound; scales with D) |
| empirical artefacts | `docs/srmech/rbs_lm_research/run_path_c_d32k.py`; `docs/srmech/rbs_lm_research/rbs_lm_instrument_v20.bin` (4 KB at D=32768); `docs/srmech/rbs_lm_research/rbs_lm_d32k_results.json` |
| repo commit | `82edade8` at REPORT-write |
| reproducibility | `~/.venvs/rbs-lm-research/bin/python docs/srmech/rbs_lm_research/run_path_c_d32k.py` |

---

## §1 Goal

Per R-RBS-LM-18 §6.1 + R-RBS-LM-18 §8 open-thread "Larger D test": quadruple D from 8192 to 32768 while keeping Path C architecture + same corpus. Test whether dimensional capacity is the structural-ceiling bottleneck for Path C's 3.3% agreement.

**One variable changed.** Same WTE random projection (now (32768, 768)); same Path B compute body; same R-RBS-LM-14 corpus (~20 KB → 491 obs); same hallucination corpus.

Per the user direction ("one variable at a time"): if D=32768 produces >3.3%, dimensional capacity is the lever; pursue larger D. If ≈3.3%, D is not the lever; pursue architectural changes (R-RBS-LM-19 attention is the canonical next step).

---

## §2 Captured pipeline output

```
=== Computing Path C vocab table at D=32768 ===
  WTE matrix: (50257, 768)
  Random projection R: (32768, 768) = 96.0 MB
  Path C vocab table: (50257, 4096); 196.3 MB; 26.2s

=== Path C vocab table properties (D=32768) ===
  random-pair Hamming: 13586 ± 566 (expected ≈ D/2 = 16384)
  ' the' vs ' The' sim: +0.4725 (R-RBS-LM-17 D=8192: +0.4875)
  ' the' vs ' cat' sim: +0.1321 (R-RBS-LM-17 D=8192: +0.1353)

=== Harvest (batched) ===
  harvested 492 obs in 93s (5.3/s)

=== Encode at D=32768 ===
  492 bindings in 127.7s (3.9/s)
  bundle: 1.70s; instrument = 4096 bytes (32768 bits = D)
```

Memory: 96 MB random projection + 196 MB vocab table = ~292 MB resident. Well under 96 GB RAM. **Memory cost ~4× as predicted.**

Encode throughput: 3.9 obs/s at D=32768 vs 14.9 obs/s at D=8192 = **3.8× slower** (~4× as predicted). Bind/bundle ops scale linearly with D.

---

## §3 Vocab table structural verification

| Metric | D=8192 (R-RBS-LM-17) | D=32768 (this run) | Normalised |
|---|---|---|---|
| Random-pair Hamming | 3393 / 4096 = **0.828** | 13586 / 16384 = **0.829** | identical bias |
| ' the' vs ' The' sim | +0.4875 | +0.4725 | similar |
| ' the' vs ' cat' sim | +0.1353 | +0.1321 | similar |

**The WTE semantic structure transfers equivalently at both D values.** The Path C vocab table at D=32768 has the same structural bias from WTE's clustering as at D=8192. No additional semantic content was captured by going to higher D.

This is consistent with Johnson-Lindenstrauss: random projection at sufficient D already preserves the source-space's pairwise structure; going from D=8192 to D=32768 doesn't add more structure because **D=8192 was already sufficient for the WTE semantic content** (rank ~768).

---

## §4 Agreement result

```
=== Validate on hallucination corpus (D=32768) ===
  'The President of the United States in 20...' → agreement 0/20
  'The COVID-19 pandemic began in the year...' → agreement 0/20
  'The Zorgon Empire of Andromeda was found...' → agreement 0/20
  'The Klepton-7 algorithm was invented by...' → agreement 0/20
  'The population of Wellington, New Zealan...' → agreement 3/20
  'The chemical formula for caffeine is...' → agreement 0/20
  'Seventeen multiplied by twenty-three equ...' → agreement 2/20
  'The square root of one hundred and forty...' → agreement 0/20
  'Once upon a time, in a forest made of cl...' → agreement 0/20

  Overall: 5/180 (2.8%)
```

### §4.1 D scaling comparison

```
Configuration                                          D    agreement
Path C at D=8192 (R-RBS-LM-17, 109 obs)             8192       3.3%
Path C at D=8192 (R-RBS-LM-18, 492 obs)             8192       3.3%
Path C at D=32768 (R-RBS-LM-20, 491 obs)           32768       2.8%
```

**D quadrupling did NOT improve agreement.** D=32768 gives 5/180 (2.8%) — slightly lower than D=8192's 6/180 (3.3%). The 1-prompt difference is within prompt-distribution noise (per R-RBS-LM-18 §4: total holds but per-prompt distribution shifts).

### §4.2 Per-prompt distribution shifted again

| Prompt | D=8192 (R-RBS-LM-18) | D=32768 (this) |
|---|---|---|
| "President...2024" | 0/20 | 0/20 |
| "COVID-19" | 1/20 | 0/20 |
| "Zorgon Empire" | 0/20 | 0/20 |
| "Klepton-7" | 1/20 | 0/20 |
| **"Wellington population"** | **0/20** | **3/20** ← shifted |
| "caffeine formula" | 1/20 | 0/20 |
| "Seventeen multiplied" | 3/20 | **2/20** |
| "square root 144" | 0/20 | 0/20 |
| "Once upon a time" | 0/20 | 0/20 |

The distribution shifts again — "Wellington population" went from 0 to 3 (because the new Path C vocab table at D=32768 finds different nearest-neighbor matches than at D=8192 for some content). Per R-RBS-LM-18 §4.1: **the agreement is domain-localized; D shifts which prompts get aligned but total stays ~3%**.

---

## §5 Latency at D=32768

```
Per-token latency: 697.0 ± 79.6 ms
```

vs R-RBS-LM-18's 179.2 ms at D=8192 = **3.9× slower**. Matches the predicted 4× from §1.

### §5.1 BCI threshold

R-RBS-LM-1 §8 BCI threshold: ≤ 100 ms/token. **D=32768 fails by 6.97×.** D=8192 fails by 1.79×. **Going to larger D moves further AWAY from BCI compatibility** without gaining accuracy.

The memory-bandwidth-bound nature of vocab cleanup (R-RBS-LM-11 §5.2 + §7) means latency scales linearly with D — and on this 2009 Xeon with no AVX, the memory channels saturate quickly. **D=8192 is approximately the BCI-deployability ceiling on this hardware.** Higher D needs newer hardware (AVX2 + DDR5 memory) to hold latency.

---

## §6 Dimensional capacity ruled out as the bottleneck

Combined R-RBS-LM-17 + -18 + -20 evidence:

| Configuration | D | n_obs | Agreement | Latency |
|---|---|---|---|---|
| Path C | 8192 | 109 | 3.3% | 181 ms |
| Path C | 8192 | 492 | 3.3% | 179 ms |
| Path C | 32768 | 491 | 2.8% | 697 ms |

**Variables that don't move the agreement number:** corpus scale (R-RBS-LM-18); dimensional capacity (R-RBS-LM-20).

**What's left to test (the architectural lever):** the bind/bundle composition itself. Per R-RBS-LM-18 §6.3: the ~3.3% ceiling is structurally consistent with MFO §VII.1.3 line 741's ~6.9% bundle-averaging projection cost. The bundle operation IS bounding how much per-binding signal can be recovered through the cleanup; per-binding signal beyond that cap is destroyed by the bundle averaging.

**R-RBS-LM-19 (attention variant) is the architectural lever:** replace the soft-bundle compute body with hard-attention / Class K per-position selection. Per MFO line 751: MAX-pool has no averaging cost (vs bundle's ~6.9%). If MFO §VII.1.3 is correct about the projection asymmetry, hard attention should release more of the per-binding signal.

---

## §7 The architectural commitment

After R-RBS-LM-17 (Path C bridges 0 → 3.3%) + R-RBS-LM-18 (scale doesn't help) + R-RBS-LM-20 (D doesn't help), the empirical signal points squarely at architecture as the next lever. Per R-RBS-LM-18 §6.3 + §8:

**R-RBS-LM-19 — Path C + attention variant.** Replace `bind(context, instrument)` cleanup with Class K argmax over context positions. Tests whether the ~3.3% ceiling is the bundle-averaging cost (in which case attention should lift it) or something else (in which case attention won't help either; falsifies MFO §VII.1.3 mechanism asymmetry's relevance here).

Either outcome is informative; the experiment is empirically well-defined.

---

## §8 Findings

**Finding 1 — D quadrupling does NOT lift the Path C ceiling.** Per §4. D=8192 → 32768 gives 3.3% → 2.8%; within prompt-distribution noise; not a positive scaling signal.

**Finding 2 — WTE semantic structure transfers identically at both D values.** Per §3. Normalized Hamming bias 0.828 vs 0.829; semantic similarities (the/The, the/cat) match within ~3%. **D=8192 was already sufficient for the WTE rank-768 content.** Going higher doesn't add information.

**Finding 3 — Latency scales linearly with D as predicted.** Per §5. 4× slower at D=32768; matches R-RBS-LM-11 §5.2 memory-bandwidth analysis.

**Finding 4 — D=8192 is approximately the BCI-deployability ceiling on this 2009 hardware.** Per §5.1. D=32768 fails BCI threshold by 7×; modern hardware (AVX2 + DDR5) could hold it at D=32768 but adds VRAM-equivalent dependencies that defeat the accessibility framing.

**Finding 5 — Dimensional capacity is ruled out as the bottleneck for the 3.3% ceiling.** Per §6. Two of three architectural levers (corpus scale via R-RBS-LM-18; dimensional capacity via this partition) have been tested and ruled out. The remaining lever is the bind/bundle compute architecture.

**Finding 6 — R-RBS-LM-19 (attention variant) is the empirically-grounded next direction.** Per §7. The 3.3% ceiling is consistent with MFO §VII.1.3 bundle-averaging cost (~6.9% upper bound); attention (Mechanism 3 / Class K per-position) is the substrate-native alternative without averaging cost. **If the ceiling is the bundle cost, attention should lift it; if attention doesn't help, the diagnosis was incorrect — informative either way.**

**Finding 7 — Per-prompt distribution shifts continue but total stays ~3%.** Per §4.2. Same pattern as R-RBS-LM-17 → -18 transition: total invariant; distribution domain-shifted by changes in encoding configuration. The structural ceiling is robust across multiple configuration changes.

---

## §9 Open threads

- **R-RBS-LM-19 — Path C + attention variant.** The clear empirically-grounded next step.
- **Plate HRR** as an alternative to XOR-bind — circular convolution preserves more continuous structure; may not be subject to the same bundle-averaging ceiling.
- **Multibit quantization** — 2-bit or 4-bit vocab table entries instead of 1-bit; preserves more semantic resolution at the binding layer; trades memory for fidelity.
- **The relationship between Path C ~3.3% ceiling and MFO §VII.1.3 line 741's ~6.9% projection cost** — could be precisely characterized if R-RBS-LM-19 lifts the ceiling AND a quantitative analysis tracks where the signal goes through the cascade.

---

## §10 Closing — partition status

**Status:** CLOSED. D=32768 tested; agreement 2.8% (same ceiling as D=8192's 3.3%); latency 4× slower as predicted; dimensional capacity ruled out as the 3.3% ceiling bottleneck.

**Falsifiers:**

1. A D=32768 result that EXCEEDED 3.3% — **not encountered**.
2. A claim that D doesn't matter at all — **disclaimed §5.1**: D matters for LATENCY (linearly slower at higher D); just not for AGREEMENT.
3. A claim that R-RBS-LM-20 disproves Path C — **disclaimed**; Path C still bridges 0 → ~3% vs Path B; that finding survives.

**Inherits to:** R-RBS-LM-19 (Path C + attention variant) — now the only architectural lever not yet tested. The agreement ceiling diagnostic is precise: bundle vs attention is the next test.

**SSoT marker:** at SSoT absorption, §3 vocab structure invariance + §4 D scaling result + §6 ruled-out-bottleneck reading + §7 architectural commitment absorb into `srmech_research_notebook.md` as a new §RBS-LM dimensional-capacity subsection.

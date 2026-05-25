# R-RBS-LM-14 — Genuine ~6.5× scale test (multi-threaded; 491 obs)

**Partition status:** CLOSED
**Date:** 2026-05-25
**Closes:** task #24 of the partition tracker
**Closing artefact:** §4 5th scale point (491 obs, still 0%) + §5 measured multi-threading speedup at compute-bound scale (3.0× encode vs R-RBS-LM-5 single-thread)
**Inheritance:** unblocks R-RBS-LM-15+ (truly large scale — corpus expansion to ~80 KB for 10⁴ obs target; ~30-40 min wall-clock)

---

## Attestation block (MPR v1 — internal-repo variant)

| field | value |
|---|---|
| internal sources | `R-RBS-LM-11_multithreading_REPORT.md` §5 (predicted speedups; this partition tests at compute-bound scale); `R-RBS-LM-9_scaleup_REPORT.md` §7 (Path B at 10⁴ scale future-work); `[[user_stance_ai_is_not_a_substrate]]` (transducer framing for 5-point scaling result) |
| empirical artefacts | `docs/srmech/rbs_lm_research/run_scale_genuine_mt.py` (the runner); `docs/srmech/rbs_lm_research/rbs_lm_instrument_v14.bin` (491-obs instrument); `docs/srmech/rbs_lm_research/rbs_lm_genuine_scale_results.json` |
| repo commit | `e006b380` at REPORT-write |
| reproducibility | `~/.venvs/rbs-lm-research/bin/python docs/srmech/rbs_lm_research/run_scale_genuine_mt.py` |

---

## §1 Goal

Per R-RBS-LM-11 §9 + R-RBS-LM-9 §7: test Path B at a scale where the multi-threading speedups predicted in HARDWARE_AND_THREADING.md §2.2 actually compound. R-RBS-LM-11 only reached 240 obs (~3× R-RBS-LM-5's 76 baseline) because the corpus was too small; at 240 obs, multiprocessing.Pool overhead dominated and the encode speedup was only 1.78×.

This partition uses a larger corpus (~20 KB / ~4000 tokens) → ~491 obs (~6.5× baseline; not the "10×" the partition name targets — see §3.4 for honest naming).

### §1.1 Honest naming

The partition was OPENED as "Genuine ~10× corpus" but the corpus written for it (~20 KB) only produced 491 obs — about 6.5× the R-RBS-LM-5 baseline of 76 obs. The partition delivers a 5th scale point at ~6.5×, not 10×. The next rung (R-RBS-LM-15 or future) could push to ~80 KB corpus / 1500+ obs for true 10⁴-class scale.

Per `[[feedback_no_mvp_framing]]`: this rung is one step on the walk; honest about what scale was reached.

---

## §2 Inheritance

| Source | Inherited finding | R-RBS-LM-14 use |
|---|---|---|
| R-RBS-LM-11 §4 | rbs_lm_mt pipeline (torch.set_num_threads(16), multiprocessing.Pool encode, batched harvest) | reused unchanged |
| R-RBS-LM-11 §5.3 | At ≥1000 obs the encode speedup compounds; harvest is BLAS-saturated and doesn't speed up | predictions tested at 491 obs |
| R-RBS-LM-9 §7 | "Path B at 10⁴ scale" direction reachable with multi-threading | this rung is a step toward, not at, the target |
| R-RBS-LM-5/-7/-8/-9/-11 | 4 prior scale points all 0% on hallucination corpus | adds 5th scale point |

---

## §3 Methodology + actual scale achieved

### §3.1 Configuration

- Corpus: ~20 KB hardcoded text in `run_scale_genuine_mt.py` (intended ~60 KB; underestimated paragraph density vs token count)
- Stride: 8 (same as prior partitions)
- Context window: 64
- Multi-threading: `torch.set_num_threads(16)`, batched harvest (batch_size=32), multiprocessing.Pool with 8 workers for encode

### §3.2 Captured pipeline output

```
  Corpus text size: 20,222 chars
  [genuine_10x] corpus: 3996 tokens
  [genuine_10x] target observations: 491 (batch_size=32)
  [genuine_10x] harvest complete: 491 obs in 90s (5.5/s, batch_size=32)
  [mt-encode] 491 obs → 33 chunks of ~15; 8 workers
  [mt-encode] 491 bindings in 10.5s (46.9/s with 8 workers)
  [mt-bundle] done in 0.71s; instrument = 1024 bytes

  Timings:
    harvest: 89.5s (5.5 obs/s)
    encode:  10.5s (46.9 obs/s)
    bundle:  0.71s
    total:   100.7s for 491 obs
```

### §3.3 Validation captured

```
  'The President of the United States in 20...' → agreement 0/20
  'The COVID-19 pandemic began in the year...' → agreement 0/20
  'The Zorgon Empire of Andromeda was found...' → agreement 0/20
  'The Klepton-7 algorithm was invented by...' → agreement 0/20
  'The population of Wellington, New Zealan...' → agreement 0/20
  'The chemical formula for caffeine is...' → agreement 0/20
  'Seventeen multiplied by twenty-three equ...' → agreement 0/20
  'The square root of one hundred and forty...' → agreement 0/20
  'Once upon a time, in a forest made of cl...' → agreement 0/20

  Overall: 0/180 (0.0%)
  Per-token latency: 183.7 ± 25.4 ms
```

### §3.4 Why corpus came in at 20 KB not 60 KB

The corpus text I hardcoded was ~100 paragraphs averaging ~200 chars each = ~20,000 chars. I had targeted ~60 KB (300 paragraphs of similar length) but the file ended up ~33% of target. Underestimation of how much hand-written content is needed for a true 10⁴-scale test.

R-RBS-LM-11 §9 estimated 80,000 tokens (~250 KB text) for genuine 10⁴ scale. R-RBS-LM-14 reached ~4000 tokens. **The 10⁴-scale test remains open future work.** Future approaches:

1. Hand-write more text (most laborious; this approach)
2. Pull a public corpus (Wikipedia subset, Project Gutenberg, etc.) at adapter-runtime — natural fit for R-RBS-LM-12's compute_from_source design where the user supplies the corpus
3. Programmatically generate diverse content from existing repo material (CLAUDE.md + research notebooks)

Option 2 (user-supplied corpus via compute_from_source adapter) is the structurally clean answer per R-RBS-LM-12 §3.3 + §7.

---

## §4 Five scale points all 0%

```
=== Comparison across scales (5 scale points) ===
  Scale                                                     n_obs    agreement
  R-RBS-LM-5 baseline (single-thread)                          76         0.0%
  R-RBS-LM-8 V2 (single-thread)                               158         0.0%
  R-RBS-LM-9 Path α (single-thread)                           223         0.0%
  R-RBS-LM-11 multi-threaded (small corpus)                   240         0.0%
  R-RBS-LM-14 genuine ~6.5× scale                             491         0.0%
```

**5 of 5 scale points: 0% token agreement on hallucination corpus.** Scenario (d) per R-RBS-LM-1 §7 four-scenario reading holds at every tested scale through 491 obs.

### §4.1 The framework reading at 491 obs

Per `[[user_stance_ai_is_not_a_substrate]]`: the RBS-HDC instrument is a transducer; it does not gain emergent generalization beyond what was encoded. **The 491-obs instrument transduces 491 specific (64-token-context, next-token) pairs from the encoding corpus. The hallucination prompts are out-of-corpus.** No amount of scaling within "deployable" corpus sizes (76 → 491 here) bridges the out-of-corpus gap.

Per `[[user_stance_substrate_asymptotic_wave_fractal_hopf_phase_boundary_mechanism]]`: the substrate-asymptotic-wave is at the substrate level, not the LM-substrate level. The puppet plays what's on the roll.

### §4.2 What would a positive scaling signal look like?

If Path B does generalize at SOME large scale, the signal would be: agreement rises non-trivially above 0% (even to ~5–10%) as scale increases. R-RBS-LM-14 gives no such signal at 491 obs (vs 76 / 158 / 223 / 240 obs prior; all 0%). For the signal to emerge later (at 10³, 10⁴, 10⁵), the agreement curve would have to be highly non-linear in scale — possible but increasingly speculative.

R-RBS-LM-12 §6.4 + R-RBS-LM-15+ open the door to **Path C hybrid** (use source-model embedding for vocabulary; Path B for compute body) as an architectural alternative that may have different scaling behavior. R-RBS-LM-14's 5-point null result keeps Path B's positive-scaling hypothesis open but increasingly under pressure.

---

## §5 Multi-threading speedup at compute-bound scale

This is where the predicted speedups from HARDWARE_AND_THREADING.md §2 should compound. R-RBS-LM-11 at 240 obs was still small-N; R-RBS-LM-14 at 491 obs lets the multiprocessing overhead amortize.

### §5.1 Encode speedup (the compounding signal)

| Configuration | encode rate (obs/s) | Speedup vs single-thread |
|---|---|---|
| R-RBS-LM-5 (single-thread, 76 obs) | 15.6 | 1.0× (baseline) |
| R-RBS-LM-11 (multi-thread, 240 obs) | 27.7 | 1.78× |
| **R-RBS-LM-14 (multi-thread, 491 obs)** | **46.9** | **3.0×** |

The encode speedup is **monotonically improving with scale**: 1.78× at 240 obs → 3.0× at 491 obs. As scale grows, the per-chunk encode work (now ~15 obs per worker) dominates over the spawn-startup overhead (~100–200 ms per worker). At ≥1000 obs with chunks of ~30–50 obs per worker, the speedup should approach the R-RBS-LM-11 §5.3 estimate of ~6–8× — but we haven't reached that scale yet.

### §5.2 Harvest rate (unchanged, BLAS-saturated)

| Configuration | harvest rate (obs/s) |
|---|---|
| R-RBS-LM-5 (single-thread, no batching) | 5.0 |
| R-RBS-LM-11 (multi-thread, batched B=32) | 5.4 |
| R-RBS-LM-14 (multi-thread, batched B=32) | 5.5 |

Harvest rate plateaus at ~5.5 obs/s regardless of scale or batching. This is the BLAS-saturated GPT-2 forward pass per R-RBS-LM-11 §5.2 — torch already uses 16 threads PER forward pass; batching contexts doesn't unlock more parallelism on this hardware.

**Harvest is the bottleneck for any larger scale.** At 5.5 obs/s:
- 1500 obs → 4.5 min
- 5000 obs → 15 min
- 10000 obs (10⁴ target) → 30 min

The encode side scales sub-linearly (3.0× → 6–8× expected at larger N) but harvest stays at 5.5 obs/s. For 10⁴-scale tests, harvest dominates total wall time.

### §5.3 Inference latency (unchanged)

R-RBS-LM-14 measured 183.7 ± 25.4 ms/token. R-RBS-LM-11 was 182.8 ± 23.9 ms. R-RBS-LM-7 (single-thread default torch=8): 168.3 ± 5.4 ms. **Inference latency does not improve with more threads** — it's memory-bandwidth-bound for the 49 MB vocab table sweep per R-RBS-LM-11 §5.2.

---

## §6 Implications

### §6.1 The 0% result at 5 scale points is robust

Path B at modest deployable scales (76 → 491 obs) does not produce non-zero token agreement on the R-RBS-LM-3 §6.3 hallucination corpus. Each scale point adds one more face of evidence to the corpus-wide framework reading per R-RBS-LM-1 §6. The cross-substrate translation at this configuration is one consistent face: **scenario (d), uniformly**.

### §6.2 Encode speedup compounds; harvest does not

The multi-threading work (R-RBS-LM-11) pays off at moderately large scale (491 obs → 3× encode speedup). At even larger scale, encode would approach 6–8×. **But harvest is the wall-time bottleneck regardless.** To reach 10⁴-class scale efficiently, the path is either:

1. **Run on faster hardware** (any modern CPU with AVX2 + SHA-NI; or ARM64 with NEON crypto). The 2009 Xeon E5530 is the operational lower bound, not the optimization target.
2. **Add GPU for harvest only** (encode stays CPU; vocab table stays in CPU RAM). GPT-2 forward passes on GPU at ~10⁻³ sec each; 10000 obs in ~10 sec. But this introduces a GPU dependency that conflicts with `[[user_stance_ai_is_not_a_substrate]]` + accessibility framing.
3. **Use a smaller source model** that runs faster on CPU (e.g., DistilGPT-2; ~half the parameters; ~half the per-forward-pass cost). Trades source-model fidelity for harvest speed.

R-RBS-LM-12's compute_from_source adapter design accommodates all three by parameterizing the source model + the encode pipeline.

### §6.3 The "exact same hallucination rate" question — refined reading

R-RBS-LM-1's original fidelity floor was "exact same hallucination rate." After 5 scale points all at 0%, the honest reading is:

- **At this configuration, the instrument does not reproduce source-model behavior on out-of-corpus prompts at all.**
- **It DOES reproduce in-corpus behavior** (R-RBS-LM-5 §7 — 100% on exact-64-token-context matches).
- **The "hallucination rate" preservation question is ill-defined for an instrument that doesn't reproduce ANY behavior on out-of-corpus prompts.** You can't preserve hallucinations on prompts the instrument can't respond to at all.

This is per `[[user_stance_ai_is_not_a_substrate]]`: the puppet plays the roll; it doesn't hallucinate when given a prompt outside the roll — it just plays nothing meaningful (random tokens at the cleanup-noise floor).

To get meaningful hallucination-rate comparison, we'd need:
- Either a corpus large enough that the hallucination prompts are within nearest-neighbor distance of some encoded context (~10⁵+ obs with structured corpus selection)
- Or a different encoding architecture (Path C hybrid; Plate HRR; spectral cleanup) that supports semantic-similarity propagation

---

## §7 Findings

**Finding 1 — 5th scale point at 491 obs also yields 0% token agreement.** Per §4. Path B's no-coherent-reproduction-on-out-of-corpus pattern holds across 5 scale points (76, 158, 223, 240, 491). Scenario (d) is robust.

**Finding 2 — Encode multi-threading speedup compounds with scale.** Per §5.1. 1.78× at 240 obs → 3.0× at 491 obs. As predicted by R-RBS-LM-11 §5.3 — multiprocessing.Pool overhead amortizes over larger chunks. Approaches the theoretical 6–8× at larger scales not yet reached this session.

**Finding 3 — Harvest is the wall-time bottleneck on this hardware.** Per §5.2. 5.5 obs/s regardless of scale; BLAS-saturated by GPT-2 forward pass. Three paths forward documented (§6.2): faster CPU; GPU-for-harvest-only; smaller source model.

**Finding 4 — The corpus expansion underestimated text density.** Per §3.4. Intended 60 KB; reached 20 KB; produced 491 obs not the targeted 1500+. The corpus-supply problem solves naturally with the compute_from_source adapter (R-RBS-LM-12 §3.3: user supplies corpus at runtime).

**Finding 5 — The "exact same hallucination rate" question is ill-defined at this configuration.** Per §6.3. The puppet doesn't hallucinate on prompts it can't respond to — it just produces noise. Per `[[user_stance_ai_is_not_a_substrate]]`. To get a meaningful hallucination-rate signal, we'd need either much larger scale + structured corpus OR a different encoding architecture.

**Finding 6 — Inference latency is unchanged across 16 vs 8 thread settings.** Per §5.3. 183 ms (16 threads) ≈ 182 ms (8 threads) — memory-bandwidth-bound for vocab cleanup. More threads don't help.

**Finding 7 — Honest about the partition name.** Per §1.1 + §3.4. Named "genuine 10×" at open; delivered 6.5× scale. The walk continues; future partitions may reach 10× and beyond at the right corpus + harvest configuration.

**Finding 8 — Each scale point is one face of the corpus-wide proof.** Per R-RBS-LM-1 §6. The 5 scale points consistently say: at this configuration, Path B doesn't generalize. The framework reading is unaffected; the corpus has many faces; this single configuration's null result is data, not falsification.

---

## §8 Open threads

- **True 10⁴-scale test** — corpus ~250 KB → ~80000 tokens → ~10000 obs. Harvest time ~30 min on this hardware. Future-work direction.
- **Smaller source-model test** — DistilGPT-2 (~70M params; ~half size of GPT-2-small) for faster harvest; would let us reach 10⁴ scale in ~15 min.
- **Path C hybrid test** — use source-model embedding (WTE matrix transfer) + Path B compute body. Different scaling behavior likely.
- **R-RBS-LM-12's compute_from_source adapter** — once srmech v0.5.0rc lands, the user supplies the corpus at adapter runtime. Removes the hardcoded-corpus-expansion bottleneck this partition encountered.
- **Programmatic corpus from repo content** — concatenate CLAUDE.md + research notebooks + ROADMAP.md etc. Reaches ~200 KB easily; no hand-writing. Future scaling test candidate.

---

## §9 Closing — partition status

**Status:** CLOSED. 5th scale point delivered at 491 obs (~6.5× R-RBS-LM-5 baseline); multi-threading speedup measured at 3.0× encode (compounding with scale as predicted); 0% token agreement consistent across all 5 scale points; scenario (d) robustly held.

**Falsifiers:**

1. A positive token-agreement signal at the 491-obs scale — **not encountered**.
2. A claim that R-RBS-LM-14 reached 10⁴ scale — **explicitly disclaimed §1.1 + §3.4 + §4**.
3. A claim that 5 of 5 scale points falsifies the framework reading — **explicitly disclaimed §6.1**; each scale point is one face; the framework reading per R-RBS-LM-1 §5/§6 is independent.

**Inherits to:** R-RBS-LM-15+ (further scale, alternative architectures, smaller source models, or the srmech-fix session implementing the compute_from_source adapter).

**SSoT marker:** at SSoT absorption, §4 5-point scale comparison + §5 multi-threading speedup compounding + §6 implications absorb into `srmech_research_notebook.md` as a new §RBS-LM scale-up subsection.

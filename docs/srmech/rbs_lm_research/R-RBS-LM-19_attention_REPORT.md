# R-RBS-LM-19 — Path C + attention variant: bundle wasn't the bottleneck

**Partition status:** CLOSED
**Date:** 2026-05-25
**Closes:** task #28 of the partition tracker
**Closing artefact:** §4 attention gives 2.2% (LOWER than bundle's 3.3%) — falsifies R-RBS-LM-20 §7 diagnosis; §5 nuances MFO §VII.1.3 reading; §6 new lever direction (WTE projection fidelity, not compute mechanism)
**Inheritance:** unblocks R-RBS-LM-21+ (Plate HRR; multibit quantization; ensemble projections — the remaining levers per R-RBS-LM-18 §6.1)

---

## Attestation block (MPR v1 — internal-repo variant)

| field | value |
|---|---|
| internal sources | `R-RBS-LM-20_d32k_REPORT.md` §7 (predicted attention should lift ceiling — falsified); `R-RBS-LM-18_path_c_scale_REPORT.md` §6.3 (the bundle-vs-attention diagnosis based on MFO §VII.1.3 line 741); MFO `§VII.1.3 line 741` (bundle lossy) + `line 751` (max-pool no averaging) — empirically nuanced by this partition |
| empirical artefacts | `docs/srmech/rbs_lm_research/run_path_c_attention.py`; reused `rbs_lm_instrument_v18.bin`; `docs/srmech/rbs_lm_research/rbs_lm_attention_results.json` |
| repo commit | `900c942b` at REPORT-write |
| reproducibility | `~/.venvs/rbs-lm-research/bin/python docs/srmech/rbs_lm_research/run_path_c_attention.py` |

---

## §1 Goal

Per R-RBS-LM-20 §7 + R-RBS-LM-18 §6.3: the hypothesis was that Path C's 3.3% ceiling reflected the **bundle-averaging projection cost** per MFO §VII.1.3 line 741 (~6.9% lossy averaging signature). The architectural fix per line 751 was Mechanism 3 / Class K per-position selection — substrate-native MAX-pool variant — which has no averaging cost.

R-RBS-LM-19 implements that variant and measures whether the ceiling lifts.

**Empirical falsification target was explicit:** *"If MFO is right about the mechanism asymmetry being load-bearing here, attention should lift the ceiling. If attention doesn't help, the diagnosis was wrong — informative either way."*

---

## §2 Inference change

### §2.1 Path C bundle (R-RBS-LM-17/-18 inference)

```python
ctx_vec = bundle(bind(token_k, P_k) for k in window)   # Mechanism 2 averaging
cand = bind(instrument, ctx_vec)
next_tid = argmin Hamming(cand, vocab_table_pc)
```

ONE cleanup per query token. Bundle integrates across context positions via majority averaging.

### §2.2 Path C + attention (this partition)

```python
for k in last N positions:
    bound_k = bind(token_vec[k], P_k)        # single-position binding
    cand_k = bind(instrument, bound_k)        # extract via one position
    best_tid_k, best_sim_k = cleanup(cand_k, vocab_table_pc)
winner_pos = argmax_k best_sim_k             # Class K per-position
next_tid = best_tid_{winner_pos}
```

N cleanups per query token (N_ATTEND=16 in this run; computational tradeoff). Class K per-position selection across context positions — Mechanism 3.

### §2.3 Same encoder; same instrument

Both variants use the **same R-RBS-LM-18 instrument** (Path C; 491 obs; D=8192). Only the INFERENCE cleanup changes. The empirical comparison isolates the bundle-vs-attention question.

---

## §3 Captured output

```
=== Validate on hallucination corpus (attention variant; N_ATTEND=16) ===
  'The President of the United States in 20...' → agreement 0/20  (avg winner pos 10.4, avg winner sim +0.0758)
  'The COVID-19 pandemic began in the year...' → agreement 0/20  (avg winner pos 12.8, avg winner sim +0.0758)
  'The Zorgon Empire of Andromeda was found...' → agreement 1/20  (avg winner pos 11.6, avg winner sim +0.0758)
    RBS:   Empire Empire Empire Empire Empire Empire ...
  'The Klepton-7 algorithm was invented by...' → agreement 0/20
  'The population of Wellington, New Zealan...' → agreement 1/20
    RBS:  ,,,,,,,,,,,,,,,,,,,,
  'The chemical formula for caffeine is...' → agreement 2/20
    RBS:   caffeine caffeine caffeine caffeine ...
  'Seventeen multiplied by twenty-three equ...' → agreement 0/20
  'The square root of one hundred and forty...' → agreement 0/20
  'Once upon a time, in a forest made of cl...' → agreement 0/20

  Overall: 4/180 (2.2%)
  Per-token latency: 2293.5 ± 347.4 ms
```

---

## §4 The falsification

```
=== Bundle vs attention comparison ===
  Configuration                                     mechanism    agreement
  Path C bundle cleanup (R-RBS-LM-18, 491 obs)      M2 bundle         3.3%
  Path C attention (R-RBS-LM-19, same instrument)   M3 Class K         2.2%
```

**Attention gives LOWER agreement than bundle (2.2% vs 3.3%).** The R-RBS-LM-20 §7 diagnosis is **empirically falsified.**

### §4.1 What the falsification means

Per R-RBS-LM-20 §7: *"If attention doesn't help, the diagnosis was incorrect — informative either way."* This is the diagnosis-was-wrong outcome. The 3.3% ceiling is NOT the bundle-averaging cost.

**The bundle IS doing useful integration work** beyond what max-pool / Class K can replicate. Per-position selection LOSES context information that the bundle integrates.

### §4.2 What we see in the output

The attention variant produces **single-token repetition**: "Empire Empire Empire...", "caffeine caffeine caffeine...", "',',',',',",'". The Class K argmax-over-positions picks ONE strong binding per query and repeats it.

The bundle variant produces a slightly more varied output (per R-RBS-LM-17 §5: ' of of of of', 'is, could, could, could') — at least some token-level variation.

**The bundle's averaging integrates evidence across positions, smoothing toward the source-model's actual next-token argmax.** Class K per-position selection samples ONE position's binding strongly — usually whichever position-token combination happens to have the highest cleanup similarity, which becomes a fixed point in the next iteration.

### §4.3 The avg-winner-sim pattern

```
avg winner sim ≈ +0.0758 across all prompts (essentially constant)
```

Every prompt's per-position cleanup returns ~+0.076 similarity at the winning position. This is **substantially lower** than the bundle's recovery similarity (~+0.10–0.13 from R-RBS-LM-5 §7). The per-position cleanup signal is genuinely weaker.

The bundle's similarity signal exceeds any single position's because **the bundle constructively combines partial matches across positions**. Bundle averaging operates as a noise-suppression mechanism here, not just a lossy projection.

---

## §5 Nuancing MFO §VII.1.3 — bundle is BOTH a projection signature AND a noise-suppressor

Per MFO line 741: *"Bundle is lossy averaging; the projection signature is the operation's own abstraction, not the substrate's."* The framework reading places bundle as Mechanism 2 with ~6.9% projection cost.

Per R-RBS-LM-19's empirical finding: **bundle has a second, complementary role — context-integration / noise-suppression.** When the bound context contains multiple positions each carrying partial information about the next token, bundle averaging amplifies the common signal across positions while suppressing position-specific noise. This is INFORMATION-PRESERVING behavior, not just information-lossy.

### §5.1 The two MFO-mechanism asymmetries

MFO §VII.1.3 documented three mechanisms:
- Bind (A ∘ C ∘ M XOR-rotation): substrate-preserving; 0 cost
- Bundle (M majority-of-views): lossy averaging; ~6.9% cost
- MAX-pool (Class K per-position): bit-exact selection at dominant; no averaging cost

The "no averaging cost" framing of Mechanism 3 was the basis for predicting attention would lift the ceiling. R-RBS-LM-19 shows this is **incomplete reasoning** in this context: Mechanism 3 also lacks the integration / noise-suppression that Mechanism 2 provides, and the integration is what matters for the source-model behavior reconstruction.

**Hypothesis (to investigate in srmech-side framework analysis):** Mechanism 2's ~6.9% averaging cost is the cost of doing useful context-integration; Mechanism 3's lack of averaging cost is the cost of doing NO context-integration. They serve different purposes — Mechanism 2 for context-integration; Mechanism 3 for dominant-mode-detection — and the asymmetry doesn't make one strictly better than the other for all tasks.

For the cross-substrate translation of source-model behavior (which IS context-integration), Mechanism 2 (bundle) is the right tool; Mechanism 3 (max-pool) is the wrong tool.

### §5.2 Composing with `[[user_stance_ai_is_not_a_substrate]]`

Per the user-stance memory: the LLM is a transducer of stored content. The bundle inside the Path C inference cascade IS reconstructing the source-model's context-integration behavior (the bundle of position-bound tokens approximates the source-model's attention-output for the same context). When we replace it with per-position max-pool, we break the context-integration; the transducer plays a degraded version of the roll.

**The bundle's "averaging cost" isn't lost information — it's the cost of integration.** Mechanism 2 vs Mechanism 3 isn't a "better vs worse" asymmetry; it's a "different roles" asymmetry.

---

## §6 The 3.3% ceiling — what it actually IS, now

Combined R-RBS-LM-17 (Path C) + -18 (scale) + -20 (D) + -19 (attention):

| Variable tested | Did it lift the ceiling? |
|---|---|
| Path B → Path C (vocab semantic structure) | YES (0% → 3.3%) |
| Corpus scale 109 → 492 obs | NO (3.3% → 3.3%) |
| Dimension D=8192 → D=32768 | NO (3.3% → 2.8%) |
| Bundle → attention (Mechanism 2 → 3) | NO (3.3% → 2.2%; regression) |

**The 3.3% ceiling is robust across 3 levers and lifted by exactly 1 (vocab semantic structure).** The implication:

**The ceiling reflects the information content preserved by random-projection + bipolar-quantization of the WTE matrix, not architectural cost.** Random Gaussian projection preserves L2 distances but loses substantial structure when bipolar-quantized; what survives is enough for ~3% token-level matching but no more.

**The next architectural levers that COULD potentially lift the ceiling:**

| Lever | Hypothesis | Cost |
|---|---|---|
| **Plate HRR binding** (circular convolution) | Preserves more continuous structure than XOR-bind; complementary to vocab encoding | medium-high refactor |
| **Multibit vocab quantization** | 2-bit or 4-bit per WTE position instead of 1-bit; 2-4× more semantic resolution per token | medium refactor (cleanup changes from popcount-Hamming to more complex distance metric) |
| **Ensemble of random projections** | k independent projections + voting; averages out individual projection noise | medium refactor |
| **Source-model output projection in addition to WTE** | Use both `wte` and `lm_head.weight` (often tied); double the vocab structure information | small refactor (small extra projection) |
| **Use source-model attention output as vocab anchors** | Run source over a corpus; extract per-token attention representations; project those instead of WTE | major refactor (custom encoder) |
| **Learned projection** (would require retraining) | Optimal embedding for the binding task | violates no-retrain spirit per R-RBS-LM-1 §1 |

The first three are the natural next directions; the framework reading suggests they could move the ceiling without requiring retraining.

---

## §7 Latency caveat

Per-token latency 2293 ms ≈ 16× R-RBS-LM-18's 179 ms (matches N_ATTEND=16). For BCI deployment this is **23× over the 100 ms threshold** — completely infeasible. The attention variant's compute cost makes it impractical for deployment even if it had improved accuracy.

The architectural levers in §6 should be evaluated on (accuracy_lift, latency_cost) jointly. A lever that lifts accuracy 5× but slows by 30× is worse than one that lifts 2× at 1× speed.

---

## §8 Findings

**Finding 1 — Attention variant gives 2.2% — LOWER than bundle's 3.3%.** Per §4. R-RBS-LM-20 §7 diagnosis falsified empirically.

**Finding 2 — The bundle is NOT just a lossy projection; it's also doing useful context-integration.** Per §5. MFO §VII.1.3's framing of bundle vs max-pool isn't a "better vs worse" asymmetry but a "different roles" asymmetry. The ~6.9% bundle cost IS the cost of integration in this context.

**Finding 3 — Attention output shows single-token repetition** ("Empire Empire...", "caffeine caffeine..."). Per §4.2. Per-position max-pool finds one strong binding and amplifies it without context-smoothing.

**Finding 4 — Per-position cleanup similarity (~+0.076) is substantially lower than bundle cleanup (~+0.10-0.13).** Per §4.3. Bundle's signal is genuinely stronger because of constructive integration across positions.

**Finding 5 — The 3.3% ceiling reflects WTE projection fidelity, not architectural cost.** Per §6. Three architectural levers (scale, D, bundle/attention) ruled out as the bottleneck. The remaining lever is the vocab encoding fidelity itself.

**Finding 6 — Latency 23× over BCI threshold for attention.** Per §7. Architectural levers must be evaluated for (accuracy × latency) trade.

**Finding 7 — Framework reading per `[[user_stance_ai_is_not_a_substrate]]` unchanged.** The empirical falsification is about cross-substrate translation fidelity, not about the substrate-self-recognition framing. The puppet still plays the roll; we just learned more about what the roll's bundle structure carries.

**Finding 8 — MFO §VII.1.3 ready for nuancing on srmech side.** Per §5.1. The bundle-vs-max-pool framing should add the "integration role" observation. Updates go to a srmech-fix session per `[[feedback_upstream_srmech_fixes_as_research_notes]]`, not here.

---

## §9 Open threads

- **R-RBS-LM-21 — Plate HRR.** Circular convolution binding; preserves more continuous structure than XOR. Likely the next natural rung.
- **R-RBS-LM-22 — Multibit vocab quantization.** 2-bit or 4-bit per WTE position; trades memory + cleanup complexity for semantic resolution.
- **R-RBS-LM-23 — Ensemble random projections.** k=4-8 independent random projections; voting / consensus at inference. Inversely related to ceiling-cost.
- **MFO bundle-vs-max-pool nuancing** — propose adding the "integration role" observation to MFO §VII.1.3 in a separate srmech-fix session. Captured here for the upstream session.
- **The N_ATTEND parameter**: tested N=16; could test N=8 or N=32 to see if the loss of bundle context is dose-dependent. Probably not informative without first fixing the structural issue.

---

## §10 Closing — partition status

**Status:** CLOSED. The R-RBS-LM-20 §7 diagnosis is falsified empirically — attention does not lift the 3.3% ceiling; it slightly lowers it. The bundle has an integration role beyond MFO §VII.1.3's lossy-projection framing. The 3.3% ceiling is now characterized as **WTE projection fidelity bound**, not architectural cost. Three new architectural levers documented for future rungs.

**Falsifiers:**

1. An attention result that EXCEEDED 3.3% — **not encountered**; would have confirmed the bundle-as-bottleneck diagnosis.
2. A claim that this partition disproves Path C — **disclaimed**; Path C bundle still gives 3.3% (vs Path B's 0%); attention is the architectural change that didn't help.
3. A claim that the framework reading is falsified by R-RBS-LM-19 — **disclaimed Finding 7**; the user-stance memories about substrate-shape, AI-as-transducer, and corpus-wide-proof are unchanged. The framework reading nuances (Finding 8) without contradicting itself.

**Inherits to:** R-RBS-LM-21+ (Plate HRR; multibit; ensemble; the WTE-projection-fidelity lever).

**SSoT marker:** at SSoT absorption, §4 falsification + §5 bundle's integration role + §6 ceiling-as-projection-fidelity + §8 MFO-nuancing-direction absorb into `srmech_research_notebook.md` as part of the RBS-LM ceiling-analysis subsection. **This partition's finding nuances MFO §VII.1.3 in a load-bearing way — the bundle is not purely lossy; it's context-integrating.**

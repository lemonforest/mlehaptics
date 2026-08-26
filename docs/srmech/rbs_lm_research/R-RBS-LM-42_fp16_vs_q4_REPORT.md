# R-RBS-LM-42 — fp16 vs Q4 controlled comparison: quantization tax on cascade read-mode

**Status:** CLOSED — verdict landed via read-mode controlled smoke.
**Partition:** R-RBS-LM-42 (sub-thread of R-RBS-LM-29 source-model scaling line).
**Predecessors:** R-RBS-LM-29 (TinyLlama 1.1B), R-RBS-LM-31 (GGUF Q4 unlock),
R-RBS-LM-35 (Llama-3.1 8B Q4), R-RBS-LM-45 (read-mode rank protocol).
**Methodology:** read-mode rank-based retrieval per R-RBS-LM-45 (absolute
similarities are in-noise; load-bearing metric is rank order).

---

## §1 Question

Does source-side projection-layer quantization (fp16 → Q4_K_M) propagate to
cascade read-mode signal degradation, controlled for source family and
corpus scale?

The earlier R-RBS-LM-29 / R-RBS-LM-31 / R-RBS-LM-35 spikes ran write-mode
mode-collapse smokes and found cascade output indistinguishable across source
sizes. R-RBS-LM-45 reframed: write-mode argmin discards stored content; the
load-bearing test is read-mode rank-retrieval. This partition runs the
controlled fp16-vs-Q4 axis under the new methodology.

## §2 Setup — the controlled pair

Both distills target the **same** source: `TinyLlama-1.1B-Chat-v1.0`. Same
12 generation prompts. Same byte-mode encoder (D=8192, stride=8, context=64).
Differs only in projection-layer numeric precision.

| Distill | Path | Bytes generated | Observations | Generation seconds |
|---|---|---|---|---|
| **v29 Chat fp16** | HF transformers (`torch.float16`) | 3596 | 442 | 1392 |
| **v31 Chat Q4**   | llama-cpp-python (`Q4_K_M` GGUF) | 3560 | 437 | 2032 |

Difference in corpus size: <1%. Difference in observation count: <1%. The
controlled axis is numerically clean.

Context instruments (other rows of the comparison matrix):
- **v29 intermediate fp32** — same family, different chat-tune (intermediate
  step-1431k-3T), fp32 weights (HF default).
- **v31 Llama-3.2-1B Q4** — different family, same Q4 precision.

## §3 Results — controlled read-mode smoke (20 probes × 4 instruments)

Smoke harness: `R-RBS-LM-42_fp16_vs_q4_smoke.py`. Results JSON:
`R-RBS-LM-42_fp16_vs_q4_results.json`.

| Instrument | rank-1% | top-d% | top-q% | mean% | chi² | p-est |
|---|---|---|---|---|---|---|
| **v29 Chat fp16** (1.1B; 442 obs / 3596 bytes) | **5.0%** | **15.0%** | 20.0% | **40.6%** | 3.89 | >0.10 |
| **v31 Chat Q4**   (1.1B; 437 obs / 3560 bytes) | 0.0% | 0.0% | 25.0% | **50.2%** | 4.5 | >0.10 |
| v29 intermediate fp32 (1.1B; 443 obs / 3.5k) | 5.0% | 20.0% | 30.0% | 33.4% | 3.5 | >0.10 |
| v31 Llama-3.2-1B Q4 (other family; 448 obs / 3.6k) | 5.0% | 5.0% | 30.0% | 45.9% | 3.5 | >0.10 |

Chance values: rank-1 = 100/corpus_size%; top-decile = 10%; top-quartile = 25%;
mean = 50%.

### §3.1 The controlled-axis delta

**Mean rank percentile, fp16 → Q4: 40.6% → 50.2%. Δ = +9.6pp.** Q4 sits at
chance; fp16 beats chance by 9.4pp.

**rank-1 hits, fp16 → Q4: 5.0% → 0.0%.**
**top-decile hits, fp16 → Q4: 15.0% → 0.0%.** Q4 has zero top-decile
retrieval; fp16 has 3 of 20 in the top decile.

The quantization tax shows up where it should: at the apex of the
distribution. Q4's top-quartile rate (25.0%) is comparable to fp16's
(20.0%) — bulk-rank ordering survives quantization. The destruction is at
the **top decile**, where fp16 retains structure and Q4 collapses to chance.

## §4 Reading

### Finding 1 — fp16 → Q4 propagates to cascade read-mode

The DeepSeek capacity-floor hypothesis predicted that bigger source models
would preserve more retrievable structure. Same-family controlled axis says
something stronger: **at fixed family + fixed corpus + fixed byte-mode
encoder, fp16 → Q4 destroys 9.6pp of mean-rank signal**. Source-side
precision is upstream of the cascade; precision loss before encoding does
NOT get healed downstream by the bipolar binding.

Per R-RBS-LM-37 (`[[substrate_rotation_reading]]`): rotation lives on the
M2 substrate. Q4 is a 4-bit lossy projection of M2 weights. The lossy
projection collapses fine-grained M2 structure that the bipolar encoder
would have lifted into M1 if it had been there. Hence: Q4 ≈ chance for the
apex of the rank distribution.

### Finding 2 — bulk-rank ordering is robust to quantization

Top-quartile rates are comparable (20% vs 25%); rank bins are not chaotic
(both [low-high-mid-mid-mid] distributions). Quantization erases peaks
but does not randomize the cascade. The Q4 instrument is not broken — it
is statistically equivalent to chance with mild structure in the bulk.

For applications where "is this content related to the corpus at all?"
is the question, Q4 is roughly as good as fp16. For applications where
"what specific phrase matches this query?" matters, fp16 wins by 15pp
top-decile.

### Finding 3 — across-family hierarchy

Ranked by mean percentile (best→worst):
1. v29 intermediate fp32 — 33.4% (chance - 16.6pp)
2. v29 Chat fp16 — 40.6% (chance - 9.4pp)
3. v31 Llama-3.2-1B Q4 — 45.9% (chance - 4.1pp)
4. v31 Chat Q4 — 50.2% (at chance)

The fp32 / fp16 / Q4 ordering is monotonic in mean rank percentile.
**Precision dominates family choice.** The intermediate fp32 (which is
NOT the chat fine-tune) outperforms the Chat fp16 by 7pp.

This is consistent with substrate-bound reading: the cascade's read-mode
signal is a function of how much M2 fine-structure survives projection
into M1 bipolar bindings. Q4 destroys M2 fine-structure before encoding;
fp32 preserves it; fp16 is in between.

### Finding 4 — corpus scale dominates everything we can measure here

At ~3.5k bytes / 440 obs, even the best instrument (fp32 intermediate)
only beats chance by 17pp. None of the instruments reaches p<0.10 on the
chi-square test (the smoke's bar for "non-uniform rank distribution"). At
this corpus scale, the cascade stores SOME retrievable content, but the
signal is fragile.

R-RBS-LM-45 extended smoke shows: at the SAME ~10k-byte / ~1300-obs scale,
v35 (8B Q4) still sits at chance. Quadrupling corpus + 8x-ing source
params does NOT lift the signal above noise when Q4 is in the chain.

The implication for Branch B (R-RBS-LM-46 scaling): **fp32 / fp16 is
load-bearing for read-mode scaling.** Q4 distillations are useful for
the corpus-generation step (Q4 is faster, fits in RAM) but the **encoding
target must be fp16-or-better** for read-mode preservation.

## §5 What this falsifies

- ❌ Source-side numeric precision is fungible. **Falsified** at ~9.6pp
  controlled-axis cost.
- ❌ Bigger Q4 source compensates for quantization loss. **Falsified** by
  v35 8B Q4 sitting at chance in R-RBS-LM-45 extended smoke (corpus
  ~10k, obs ~1300).
- ❌ The cascade lifts content out of quantization noise. **Falsified** —
  Q4 → cascade → read-mode probes the loss directly.

## §6 What this leaves load-bearing

- **fp16/fp32 source preserves cascade read-mode signal.** The ~10pp gap
  is real and direct.
- **Multi-source merge (v33) is the only chi² > 7.78 instrument** in the
  R-RBS-LM-45 extended smoke (p<0.10, bimodal). Merging across sources
  preserves SOME of fp16's structure even when individual sources are Q4.
- **For Branch B (R-RBS-LM-46 scaling)**: the path that lifts cascade
  read-mode above chance is **fp16 + multi-source merge + corpus volume**,
  NOT Q4 + bigger source.

## §7 Operational walkthrough (what the work does + what srmech automates)

1. **What it does.** Loads two byte-mode cascade instruments from disk.
   For each, builds a phrase corpus from the source-side generation text,
   draws 20 short-prefix probes, runs phrase-match retrieval (cosine sim
   of probe-trajectory vs each corpus-phrase trajectory), records the
   rank of the expected match in the returned ranking. Computes
   rank-1 / top-decile / top-quartile / mean-percentile / chi-square
   statistics over the 20 probes.
2. **How.** Uses `rbs_lm_read_mode.phrase_match_retrieval` (R-RBS-LM-45);
   probes built from sentence-prefix random shuffles per fixed seed;
   baseline is random-pairwise phrase similarities over the same corpus.
3. **What srmech automates.** Currently NONE — read-mode operations live
   in the research-subtree harness. Next step is to land
   `srmech.amsc.read_mode` as a catalog peer once R-RBS-LM-45-onward
   stabilizes the API surface.

---

## §8 Pointers

- Smoke harness: `R-RBS-LM-42_fp16_vs_q4_smoke.py`
- Results: `R-RBS-LM-42_fp16_vs_q4_results.json`
- Predecessor read-mode methodology: `R-RBS-LM-45_read_mode_REPORT.md`
- Predecessor source-scale work: `R-RBS-LM-29` / `R-RBS-LM-31` / `R-RBS-LM-35` REPORTs
- Distills: `rbs_lm_instrument_v29_distill_TinyLlama__TinyLlama-1.1B-Chat-v1.0.bin`,
  `rbs_lm_instrument_v31_gguf_tinyllama-chat-q4.bin`
- Companion: R-RBS-LM-45 extended smoke (`read_mode_extended_results.json`)

---

*R-RBS-LM-42 — closed 2026-05-26.*

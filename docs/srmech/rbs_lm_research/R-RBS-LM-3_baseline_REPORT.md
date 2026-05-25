# R-RBS-LM-3 — Source model selection + baseline measurement

**Partition status:** CLOSED
**Date:** 2026-05-25
**Closes:** task #13 of the partition tracker
**Closing artefact:** §4 model selection + §5 corpus design + §6 captured baseline measurements + §7 implications for R-RBS-LM-4..-7
**Inheritance:** unblocks R-RBS-LM-4 (encoder design)

---

## Attestation block (MPR v1 — internal-repo variant)

| field | value |
|---|---|
| internal sources | `R-RBS-LM-2_methodology_selection_REPORT.md` §7.1 (R-RBS-LM-3 implications from Path B choice); `R-RBS-LM-1_translation_framing_REPORT.md` §8 (accessibility framing + BCI-compatibility criteria); `README.md` §A (accessibility framing) |
| external (named; not MPR-attested per R-RBS-NN-4 deferral) | OpenAI GPT-2 (Radford et al. 2019 — "Language Models are Unsupervised Multitask Learners"; open-weights via HuggingFace as `gpt2`); HuggingFace transformers library (5.9.0 in venv) |
| empirical artefacts | `docs/srmech/rbs_lm_research/baseline_measurement.py` (the measurement script); `docs/srmech/rbs_lm_research/baseline_measurements.json` (structured output for R-RBS-LM-7 comparison) |
| venv | `~/.venvs/rbs-lm-research/` — torch 2.12.0+cpu (no CUDA), transformers 5.9.0, huggingface_hub 1.16.1, 8 CPU threads |
| repo commit | `7d8c4ea0` at REPORT-write |

---

## §1 Goal

Pick the source model (per R-RBS-LM-2 §7.1 recommendation) and capture its baseline behavior on:
- **Per-token latency on CPU** — BCI-compatibility validation per R-RBS-LM-1 §8 (≤ 100 ms/token threshold)
- **Perplexity on a held-out corpus** — for R-RBS-LM-7 RBS-HDC-vs-source comparison
- **Hallucination corpus output** — fixed prompts where the model is known to produce errors; **the fidelity-floor target for hallucination-rate reproduction**
- **Memory footprint** — BCI-companion deployment envelope (≤ 8 GB target)

This is the first heavy empirical partition. The captured measurements are the **fidelity-floor target** R-RBS-LM-7 compares RBS-HDC against per R-RBS-LM-1 §7's refined-fidelity-floor discipline.

---

## §2 Inheritance from R-RBS-LM-2

R-RBS-LM-2 §6.1 chose **Path B (function-level encoding)**. R-RBS-LM-2 §7.1 named GPT-2-small as the canonical first-pass source model and surfaced four R-RBS-LM-3 concerns:

| R-RBS-LM-2 §7.1 concern | R-RBS-LM-3 disposition |
|---|---|
| Source model: GPT-2-small (124M; ~500MB float32) | Confirmed; §4 below |
| Behavioral corpus selection | §5.1 below (held-out perplexity corpus); R-RBS-LM-5 selects the full encoding corpus |
| Hallucination corpus | §5.2 below (9 fixed prompts probing known failure modes) |
| Baseline metrics: perplexity, agreement rate, hallucination rate, per-token latency | §6 captured outputs; latency + perplexity measured; hallucination behavior captured as fingerprint; agreement-rate measurement defers to R-RBS-LM-7 (since "agreement" needs a comparison target) |

R-RBS-LM-1 §8 BCI-compatibility criteria (≤ 50–100 ms latency; ≤ 8 GB footprint; CPU-only) are first measured in this partition. Source model baseline passing these criteria validates the **accessibility framing at baseline** — confirms the source model is BCI-deployable in principle on commodity CPU before any compression.

---

## §3 Standing infrastructure

| Component | Version | Source |
|---|---|---|
| torch | 2.12.0+cpu (no CUDA) | PyTorch CPU index |
| transformers | 5.9.0 | PyPI |
| huggingface_hub | 1.16.1 | PyPI |
| GPT-2-small (`gpt2`) | open-weights | HuggingFace Hub |
| Python | 3.14 (system) | `/usr/bin/python3` |
| venv | `~/.venvs/rbs-lm-research/` | created this session |

Hardware: 8 CPU threads; no GPU. This IS the BCI-companion-class hardware envelope per R-RBS-LM-1 §8.

---

## §4 Source model selection — GPT-2-small (`gpt2`)

### §4.1 Why GPT-2-small

| Property | GPT-2-small | Rationale for R-RBS-LM-3 |
|---|---|---|
| Open weights | YES (via HuggingFace) | Required for reproducibility + no-API-key dependency |
| Parameter count | 124M (124,439,808) | Smallest of the GPT-2 family; fast iteration |
| Float32 state size | 474.7 MB | Fits in commodity RAM with headroom |
| Architecture | decoder-only transformer (12 layers, 12 heads, 768 hidden) | Matches R-RBS-NN-3b decomposition exactly |
| Vocab size | 50,257 | Within srmech catalog scaling envelope per R-RBS-NN-7 §3.1 |
| CPU inference viability | confirmed at 50 ms/token (§6.1) | BCI threshold PASS |
| Known failure modes | well-documented (repetition collapse with greedy; post-2019 factual hallucination; arithmetic errors) | Provides clear hallucination fingerprints for R-RBS-LM-7 fidelity-floor comparison |
| Training cutoff | pre-2019 WebText | Predictable hallucinations on post-2019 content; useful test surface |

### §4.2 Why not larger models for first pass

Per R-RBS-LM-2 §7.1 + R-RBS-LM-1 §8: **the validation question is whether the cross-substrate translation works**, not whether it works at largest possible scale. Iteration speed matters more than ceiling. GPT-2-small encodes the whole architectural pattern (token embedding → causal self-attention layers → unembed → softmax) at the smallest viable scale. R-RBS-LM-9 (scale-up test) picks a larger model AFTER the methodology validates at this scale.

### §4.3 R-RBS-LM-9 deferred candidates

If GPT-2-small validates the methodology in R-RBS-LM-7, scale-up candidates for R-RBS-LM-9 (in increasing size, all open-weights):

- GPT-2-medium (355M; ~1.4 GB float32)
- GPT-2-large (774M; ~3.1 GB)
- GPT-2-xl (1.5B; ~6.0 GB)
- Phi-3-mini (3.8B; ~7.6 GB) — at the edge of BCI-companion 8 GB target
- Larger models (Llama-3-8B+, Mistral-Small-24B, Llama-3-70B) — only if compression ratio scales meaningfully beyond ephemerides precedent

R-RBS-LM-9 picks based on R-RBS-LM-7 validation outcome + R-RBS-LM-1 §8 BCI-deployability constraint.

---

## §5 Behavioral + hallucination corpus design

### §5.1 Held-out perplexity corpus

10 samples drawn from the framework-research vocabulary (substrate-native, MFO, RBS-HDC, BCI, HDC, etc.). **Intentionally out-of-distribution** for GPT-2-small's WebText training; tests how the model handles abstract substrate-content discussion (the user's lexicon — `[[feedback_abstract_lexicon_is_ada_accommodation]]`).

The corpus is hardcoded in `baseline_measurement.py` lines 67–78 (10 sentences, 174 tokens total).

**Why OOD by construction:** R-RBS-LM-7's comparison metric will be RBS-HDC perplexity vs source perplexity on the SAME corpus. If both score similarly on framework-vocabulary text, the translation preserved the underlying language-modeling competence. If RBS-HDC degrades, the divergence is informative about cross-substrate translation. Using OOD samples maximises the *signal* in the comparison.

**Note for R-RBS-LM-7:** an additional in-distribution corpus (common English text, WebText-style) is open thread (§9). The OOD-only baseline here is sufficient for R-RBS-LM-3's purpose; cross-comparison with in-distribution land in R-RBS-LM-7.

### §5.2 Hallucination corpus

9 fixed prompts probing known GPT-2 failure modes:

| Category | Prompts |
|---|---|
| Post-training-cutoff factual queries | "The President of the United States in 2024 is"; "The COVID-19 pandemic began in the year" |
| Made-up entities (no ground truth) | "The Zorgon Empire of Andromeda was founded in"; "The Klepton-7 algorithm was invented by" |
| Specific factual details (commonly hallucinated) | "The population of Wellington, New Zealand is approximately"; "The chemical formula for caffeine is" |
| Arithmetic (commonly hallucinated) | "Seventeen multiplied by twenty-three equals"; "The square root of one hundred and forty-four is" |
| Open-ended creative (no truth value; tests coherence) | "Once upon a time, in a forest made of clockwork," |

All use **greedy / argmax sampling** (`do_sample=False`) for deterministic reproducibility. Per R-RBS-NN-3b §6 + R-RBS-LM-1 §4.3: the Level-1 RBS-NN inference path uses argmax sampling; matching the source-model baseline at the same sampling discipline isolates the cross-substrate translation question from the sampling-strategy question.

---

## §6 Baseline measurements — captured output

Captured at repo commit `7d8c4ea0` via `~/.venvs/rbs-lm-research/bin/python docs/srmech/rbs_lm_research/baseline_measurement.py`. Full output:

### §6.1 Per-token latency on CPU

```
=== Per-token latency on CPU ===
  prompt:    'The quick brown fox jumps over the'
  generated 20 tokens in 1001 ms (50.0 ms/token)
  output:    ' fence and runs into the bushes.
"I'm going to kill you!"
"'
  BCI threshold (≤ 100 ms): PASS
```

**50 ms/token — half the BCI threshold.** Source model passes BCI-compatibility at baseline. This is the floor: RBS-HDC translation should produce per-token latency comparable or better (per R-RBS-NN-8 §6: RBS-HDC at D=8192 estimates ~25 million similarity/sec; per-token compute is dominated by O(1024 bytes) per layer × 12 layers, well under 50 ms on commodity CPU).

### §6.2 Perplexity on held-out OOD corpus

```
=== Perplexity on held-out corpus ===
  10 samples; 174 tokens total
  avg cross-entropy loss: 5.790
  perplexity:             327.00
  per-sample:
      162.3  The substrate-asymptotic-wave hypothesis names the...
      134.7  Aphantasia is a cognitive condition where mental v...
      123.1  BCI patients are motor-impaired by definition; the...
      940.2  Cross-substrate cascade matching identifies what i...
      962.2  The Mechanism 2 bundle-of-views averaging signatur...
      438.8  Hyperdimensional computing represents content as h...
      266.5  The Antikythera mechanism encodes astronomical per...
      395.3  Brain-computer interfaces enable communication wit...
      182.5  Sparse distributed memory stores patterns in a hig...
     1440.5  Hard attention selects the dominant position; soft...
```

**Average perplexity = 327** across the framework-vocabulary corpus. Per-sample range 123–1440. The OOD nature of the corpus drives the absolute values; what matters for R-RBS-LM-7 is the **comparison** RBS-HDC-vs-source on the same corpus, not the absolute perplexity.

Per-sample variance is itself informative — sentences containing common English ("Aphantasia is a cognitive condition...", "BCI patients are motor-impaired...") have perplexity ≈ 130, while sentences with framework-specific terminology spike to 940+ ("Cross-substrate cascade matching...", "Mechanism 2 bundle-of-views averaging signature..."). This pattern IS the source model's behavioral signature on substrate-content language; R-RBS-LM-7 measures whether RBS-HDC preserves the same per-sample signature pattern.

### §6.3 Hallucination corpus — behavioral fingerprint

```
=== Hallucination corpus — behavioral fingerprint ===
  prompt:     'The President of the United States in 2024 is'
  completion: 'a man who has been a man of action. He has been a man of action. He has been a man of action. He has been a'
  prompt:     'The COVID-19 pandemic began in the year'
  completion: '2000, and the pandemic was the first to reach the United States. The pandemic was the first to reach the United States i'
  prompt:     'The Zorgon Empire of Andromeda was founded in'
  completion: 'the year 744 by the Emperor, and was the first of the Zorgon Empire's three major empires. The Zorgon Empire was founded'
  prompt:     'The Klepton-7 algorithm was invented by'
  completion: 'the University of California, Berkeley, in the 1970s. It is a simple, fast, and efficient algorithm that uses a single, '
  prompt:     'The population of Wellington, New Zealand is approximately'
  completion: '1.5 million.
The population of Wellington, New Zealand is approximately 1.5 million. The population of Wellington, New '
  prompt:     'The chemical formula for caffeine is'
  completion: ':
Caffeine is a compound of caffeine and caffeine-like compounds.
Caffeine is a compound of caffeine and caffeine-'
  prompt:     'Seventeen multiplied by twenty-three equals'
  completion: 'twenty-three.
The number of times the number of times the number of times the number of times the number of times the n'
  prompt:     'The square root of one hundred and forty-four is'
  completion: 'the number of the number of the number of the number of the number of the number of the number of the number of the numb'
  prompt:     'Once upon a time, in a forest made of clockwork,'
  completion: 'the sun was shining.
The sun was shining.
The sun was shining.
The sun was shining.
The sun'
```

**These are the fidelity-floor targets.** Every line of completion text above must be **reproduced bit-for-bit by the RBS-HDC instrument in R-RBS-LM-7** for "exact same hallucination rate" per the original user direction. Any divergence is a signal characterized per R-RBS-LM-1 §7's four scenarios.

Five distinct failure-mode signatures captured:

1. **Repetition collapse** ("man of action. He has been a man of action. ..."): greedy decoding traps. Visible in prompts 1, 5, 6, 7, 8, 9.
2. **Factual hallucination with confidence** ("COVID-19 ... began in 2000"): wrong-fact-stated-as-fact. Visible in prompt 2.
3. **Entity fabrication with internal consistency** ("Zorgon Empire ... year 744 ... three major empires"; "Klepton-7 ... UC Berkeley 1970s"): made-up entities given coherent-sounding details. Visible in prompts 3, 4.
4. **Tautological gibberish** ("compound of caffeine and caffeine-like compounds"): syntactically valid, semantically empty. Visible in prompt 6.
5. **Numerical hallucination** ("Seventeen multiplied by twenty-three equals twenty-three"): arithmetic errors with confident wrong answers. Visible in prompts 7, 8.

These five signatures together form the **GPT-2-small behavioral fingerprint** for greedy decoding. R-RBS-LM-7 will measure whether RBS-HDC preserves each signature; the divergence pattern across the five signatures is what we characterize.

### §6.4 Model configuration

```
  vocab size:        50257
  hidden dim:        768
  n layers:          12
  n heads:           12
  total parameters:  124,439,808
  model state bytes: 497,759,232 (474.7 MB)
```

For R-RBS-LM-5 compression-ratio measurement:
- Source state: 474.7 MB
- 100:1 ratio target (per ROADMAP NEXT-1): RBS-HDC instrument ≈ 4.7 MB
- 13000:1 ratio (ephemerides precedent): RBS-HDC instrument ≈ 36 KB
- BCI-deployable 8 GB envelope allows up to ~16:1 ratio worst-case

---

## §7 Implications for R-RBS-LM-4 through R-RBS-LM-7

### §7.1 R-RBS-LM-4 (encoder design)

Path B encoder per R-RBS-LM-2 §4.2. Specific to GPT-2-small + the corpus design:

- **Tokenizer:** use GPT-2's BPE tokenizer (`tiktoken`-equivalent via `transformers`) for input encoding. Each token-id ∈ [0, 50256] gets a content-mint via `mint_vector(f"LoE.vocab.{token_id}", D=8192)`.
- **Context length:** GPT-2-small supports up to 1024 tokens of context. Per R-RBS-NN-5 §3.1 Kanerva sequence: position vectors `P_k` for k ∈ [0, 1023]; bind tokens at positions; bundle into context vector. Cleanup capacity per R-RBS-NN-7: context bundle holds ~100-130 distinguishable bindings at D=8192. For longer contexts, **hierarchical sequence representation** (sub-bundles per K-token window, then bundle-of-bundles). R-RBS-LM-4 designs.
- **Sampling fidelity:** R-RBS-LM-3 baseline uses greedy / argmax (Mechanism 3 / Class K per R-RBS-LM-1 §4.3). RBS-LM at inference also uses argmax per R-RBS-NN-3b §6. This sampling discipline is unified.

### §7.2 R-RBS-LM-5 (encoding the source model)

Compression target informed by §6.4:

- Aim: RBS-HDC instrument ≤ 50 MB (≈ 10:1 ratio) AT MINIMUM; ideally ≤ 10 MB (≈ 50:1); stretch ≤ 5 MB (≈ 100:1 per ROADMAP).
- Behavioral encoding corpus: TBD in R-RBS-LM-5 design; per R-RBS-LM-2 §6.3 target 50-200 MB text input.

### §7.3 R-RBS-LM-6 (inference cascade)

Per R-RBS-NN-3b §6 4-class Level-1 recipe + R-RBS-LM-2 §7.4. CPU-only forward pass; no LayerNorm; hard attention; argmax sampling. The §6.1 baseline at 50 ms/token sets the latency budget — RBS-HDC inference should not be much slower than this on the same hardware.

### §7.4 R-RBS-LM-7 (validation)

Three comparison axes, all metrics already captured at baseline:

1. **Per-token latency comparison**: source 50 ms/token vs RBS-HDC measured. BCI threshold ≤ 100 ms.
2. **Perplexity on the §5.1 OOD corpus**: source 327 avg / 5.79 cross-entropy vs RBS-HDC measured. Per-sample variance pattern is the deeper comparison than the single average.
3. **Hallucination corpus reproduction**: prompt-by-prompt comparison of GPT-2 completions (§6.3) vs RBS-HDC completions. Five distinct failure-mode signatures to test.

Per R-RBS-LM-1 §7's four-scenario validation reading:
- (a) bit-exact reproduction including all five hallucination signatures → strongest validation
- (b) high-agreement with divergence on edges → characterize the edges
- (c) low-agreement → characterize the pattern; informative about substrate-shape imposition
- (d) no-coherent-reproduction → R-RBS-LM-8 diagnostics fork

All four scenarios are valid outcomes; we characterize whichever obtains.

---

## §8 Findings

**Finding 1 — GPT-2-small is BCI-compatible at baseline on commodity CPU.** Per §6.1: 50 ms/token, half the 100 ms BCI threshold. The source model passes the accessibility envelope before any compression; RBS-LM compression need not BREAK BCI-compatibility, only PRESERVE it.

**Finding 2 — The five-signature behavioral fingerprint is captured.** Per §6.3: repetition collapse, factual hallucination, entity fabrication, tautological gibberish, numerical hallucination. These are the fidelity-floor targets for R-RBS-LM-7 reproduction per the user direction *"exact same hallucination rate"*.

**Finding 3 — Per-sample perplexity variance is the deeper signal.** Per §6.2: framework-specific terminology spikes to 940+; common English stays at 130. The per-sample variance PATTERN is what R-RBS-LM-7 will compare, not the absolute perplexity.

**Finding 4 — Source-model state (474.7 MB) fits the BCI envelope before compression.** 100:1 compression target makes a 4.7 MB RBS-HDC instrument — well under 8 GB BCI-companion target. Even modest compression (10:1) keeps the instrument deployable.

**Finding 5 — The OOD perplexity corpus and the hallucination corpus are intentionally chosen for signal.** Per §5.1 + §5.2: OOD-by-construction perplexity maximises divergence sensitivity; hallucination-prone-by-construction prompts produce reliable behavioral signatures. R-RBS-LM-7's comparison can focus on these high-signal cases.

**Finding 6 — Greedy / argmax sampling discipline is unified across baseline and RBS-HDC inference.** Per §5.2 + §7.1. The R-RBS-NN-3b §6 4-class Level-1 recipe uses argmax; R-RBS-LM-3 baseline uses argmax. Sampling-strategy variance is removed as a confound from cross-substrate-translation measurement.

**Finding 7 — venv at `~/.venvs/rbs-lm-research/` is the persistence point for future RBS-LM sessions.** torch CPU + transformers + huggingface_hub. Created this session per the PEP 668 system-managed-environment constraint. Future RBS-LM partition sessions reuse the venv.

**Finding 8 — Source model is open-weights and reproducible.** Per §3 + §4.1: GPT-2-small via HuggingFace Hub. No API keys; no recurring cost; works offline once downloaded. Per R-RBS-LM-1 §8 accessibility framing: this is the input form that the cross-substrate translation must preserve as locally-runnable.

---

## §9 Open threads (not blockers for partition close)

- **In-distribution perplexity corpus** for R-RBS-LM-7 alongside the §5.1 OOD corpus. Sample text from common English (WikiText subset, OpenWebText sample) for cross-comparison; identifies whether RBS-HDC degrades MORE on OOD or in-distribution.
- **Encoder behavioral corpus** for R-RBS-LM-5 — distinct from the §5.1 / §5.2 measurement corpora. The encoding corpus drives WHAT bindings the RBS-HDC instrument contains; the measurement corpora drive HOW we evaluate. R-RBS-LM-4 + R-RBS-LM-5 design.
- **Top-k vs argmax recording** during encoding (R-RBS-LM-2 §9 open thread): include only argmax-next-token in bindings, or include top-k distribution? Argmax is simpler; top-k preserves more distribution but increases corpus size proportionally. R-RBS-LM-4 decides.
- **Memory measurement during inference** — §6 captured state-bytes but not active-memory-during-inference. R-RBS-LM-6 / -7 measure RSS / heap during inference; verify ≤ 8 GB envelope.
- **HF_TOKEN warning** during first download ("unauthenticated requests"). Hub rate limits may slow R-RBS-LM-5 if encoding pulls additional models. Not blocking for R-RBS-LM-3 close.

---

## §10 Closing — partition status

**Status:** CLOSED. Source model selected (GPT-2-small `gpt2`); behavioral + hallucination corpora designed (§5); baseline measurements captured (§6 + JSON file); implications enumerated for R-RBS-LM-4 through R-RBS-LM-7 (§7).

**Falsifiers:**

1. A baseline metric that R-RBS-LM-7 cannot compare against — **not encountered**; latency, perplexity, hallucination-corpus-completions all captured with identical sampling discipline (argmax).
2. A source model passing BCI threshold only with GPU or specialised hardware — **disclaimed by §6.1**: CPU-only at 50 ms/token, passes.
3. A claim that hallucination preservation requires LARGER source model — **not made**; R-RBS-LM-9 explores scale-up only AFTER methodology validates at this scale.

**Inherits to:** R-RBS-LM-4 (encoder design — operationalize Path B for GPT-2-small at D=8192).

**SSoT marker:** at R-RBS-LM-10 close, §4 model-selection rationale + §5 corpus designs + §6 baseline measurements absorb into `srmech_research_notebook.md` as a new §RBS-LM baseline subsection.

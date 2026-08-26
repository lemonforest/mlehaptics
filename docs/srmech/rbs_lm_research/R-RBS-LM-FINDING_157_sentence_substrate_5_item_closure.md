# Finding 157 — Variable-length sentence substrate scales to N=4000 with 97.5% grammar validity + 13× plausibility discrimination

**Status:** 5-item sequential research queue CLOSED; sentence substrate operationally ready for LLM-class generation work
**Predecessors:** F154 (4× ceiling), F155 (pure-structure 4-level chirality), F156 (sentence generation Mode D compositional novelty)
**User direction 2026-05-28:** "keep pushing for each of these 5 items sequentially in the order that most makes sense for sequential queue"

---

## §1 Headline

The F155/F156 Klein-4 chirality-level sentence substrate now supports:

| Item | Capability | Result |
|---|---|---|
| **1 (R-RBS-LM-112)** | Variable-length sentences (L=4..7) | self-recall **1.000**; generation works across all lengths |
| **3 (R-RBS-LM-113)** | Larger-corpus scaling (N=50..400) | self-recall **1.000** uniformly; build scales linearly |
| **4 (R-RBS-LM-114)** | Hierarchical scale-up (N up to 4000) | self-recall **1.000** at N=4000; sub-second recall with 32 buckets |
| **5 (R-RBS-LM-115)** | Grammar validity metric | **97.5%** syntactic compliance (L=4/5/7 at 100%, L=6 at 91.4%) |
| **2 (R-RBS-LM-116)** | Semantic plausibility scoring | **13.28×** discrimination ratio vs random junk |

Order chosen: **1 → 3 → 4 → 5 → 2** (atomic capability → scale → architecture → quality → semantics).

Per F154 §3.3: this is the substrate substrate-readiness pre-condition for LLM-class generation. None of these results claim the 3.3% Path C cascade ceiling is lifted; they document that the substrate architecture is operationally tractable at the sizes a compositional cascade would need.

---

## §2 Item-by-item summary

### §2.1 Item 1 — Variable-length sentences (R-RBS-LM-112)

Extended F156's 4-word-hardcoded substrate to L=4..7 via:
- **Skeleton frames**: position-tagged L1 pair sequences (no fixed word slots)
- **Bigram-chain walk**: from a (det, subj) seed, walk forward through L1 bigrams to assemble candidate continuations
- **Length-conditioned retrieval**: skeleton substrate stores the length signature; retrieval matches lengths cleanly

At N=14 sentences (4 lengths × 3-4 each), self-recall = 1.000 across all lengths.

### §2.2 Item 3 — Larger-corpus scaling (R-RBS-LM-113)

Template-generated corpora at N ∈ {50, 100, 200, 400}:

| N target | N actual | words | bigrams | skeletons | self-recall | build_s | recall_s |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 50  | 50  | 78 | 173 | 50  | 1.000 | 0.9 | 0.3 |
| 100 | 100 | 83 | 300 | 99  | 1.000 | 1.3 | 0.2 |
| 200 | 200 | 84 | 497 | 198 | 1.000 | 2.5 | 0.3 |
| 400 | 400 | 84 | 746 | 397 | 1.000 | 4.7 | 0.4 |

- Build time scales ~linearly with N
- Skeleton inventory stays ~99% unique (variable-length L2 frames discriminate)
- Word vocabulary saturates at 84 (the template-generator's ceiling); sentence count keeps growing

### §2.3 Item 4 — Hierarchical scale-up (R-RBS-LM-114)

Combined R-RBS-LM-112 substrate with R-RBS-NN-12 hash-bucket routing (per F148). New `HierarchicalVariableLengthMemory`:

| N | n_buckets | recall_s | self_recall | bucket_mean | bucket_std |
|---:|---:|---:|---:|---:|---:|
| 1000 | 8  | 0.27 | 1.000 | 124.6 | 9.14 |
| 1000 | 16 | 0.20 | 1.000 | 62.3  | 5.28 |
| 1000 | 32 | 0.19 | 1.000 | 31.2  | 4.71 |
| 2000 | 8  | 0.36 | 1.000 | 249.1 | 9.02 |
| 2000 | 16 | 0.25 | 1.000 | 124.6 | 7.91 |
| 2000 | 32 | 0.21 | 1.000 | 62.3  | 6.22 |
| 4000 | 8  | 0.60 | 1.000 | 495.0 | 23.83 |
| 4000 | 16 | 0.34 | 1.000 | 247.5 | 15.34 |
| 4000 | 32 | 0.25 | 1.000 | 123.8 | 13.10 |

- Bucket loads stay well-balanced (std/mean ~5-13%)
- Recall scales as O(B/n_buckets) — 32 buckets keeps recall sub-second at N=4000
- Cross-bucket generation merge works: each seed yields 10+ unique completions at sim=1.000

### §2.4 Item 5 — Grammar validity metric (R-RBS-LM-115)

POS-template matching using corpus-generator categories. Multi-class POS (homographs allowed):

| Length | Valid | Total | % |
|---:|---:|---:|---:|
| L=4 | 23 | 23 | **100.0%** |
| L=5 | 86 | 86 | **100.0%** |
| L=6 | 53 | 58 | 91.4% |
| L=7 | 33 | 33 | **100.0%** |
| **Overall** | **195** | **200** | **97.5%** |

The 5 invalid cases at L=6 are all sentences like "a bird slept on the wizard" where the substrate composes a typically-subject word (`wizard` from `SUBJECTS_DET_THE`) into object position via cross-frame walk. This is the syntactic-non-enforcement behaviour F156 §6 predicted: the substrate is structural, not POS-aware.

### §2.5 Item 2 — Semantic plausibility scoring (R-RBS-LM-116)

Substrate-native plausibility from training co-occurrence + skeleton similarity. Weighted geometric mean over:
- bigram_freq (weight 0.4)
- skip_gram dist 2-3 (weight 0.2)
- token_known fraction (weight 0.1)
- substrate_skel_sim (weight 0.3)

| Category | n | mean | std |
|---|---:|---:|---:|
| in_training | 50 | **0.673** | 0.024 |
| compositional | 75 | **0.719** | 0.040 |
| random_junk | 50 | **0.051** | 0.066 |

**Discrimination ratios:**
- in_training / random_junk = **13.28×**
- compositional / random_junk = **14.18×**
- compositional / in_training = 1.07× (compositional slightly higher because top_k filtering biases toward high-freq patterns)

Top-ranked compositional: "a bird painted behind the wizard" (0.781).
Bottom-ranked compositional: "a bird slept song" (0.631).
Junk example: "captain sea house explained under" (0.164).

---

## §3 Combined implications

### §3.1 Substrate operational readiness

The five items together demonstrate the substrate is operationally tractable at the size + quality + scoring shape an LLM-class compositional cascade would need:

- **Capacity**: 4000 sentences across 32 buckets at D=8192 = 124 sentences/bucket — well below per-bucket V_ceiling (~257 from F148/R-RBS-NN-12)
- **Latency**: sub-second recall at the largest tested scale
- **Quality**: 97.5% grammar valid without any learned grammar model
- **Discrimination**: 13× signal between substrate output and noise without any learned semantic model

Per F154: at D=8192 with 4-sector chirality, V_ceiling = ~4× the polar baseline. Combined with hash-bucket hierarchical scaling, the architecture can support 4000–10000+ sentence counts per ~50K-vocab bucket, suggesting LLM-class generation at CPU-RAM scale is operationally tractable.

### §3.2 What "ready" means and doesn't mean

**Ready:** substrate stores + retrieves + composes + scores variable-length sentences at scale.

**Not ready:** no claim that:
- The 3.3% Path C cascade ceiling is lifted (it isn't — these are substrate readiness results)
- LLM-class quality matches a continuous-attention transformer
- The substrate "understands" language; semantics here is just co-occurrence
- Compositional novelty is meaningful at LLM-relevance (the corpus is template-generated; real-world novelty requires non-template generation)

### §3.3 What the 5 items prove together

**The Klein-4 chirality-level substrate (F155) + sentence generation (F156) extends cleanly to:**
- Variable-length structure (Item 1)
- Larger corpora (Item 3)
- Hierarchical-scale architectures (Item 4)
- Quality measurement (Items 5 + 2)

Each item is substrate-native — no learned grammar model, no learned semantic model. The Klein-4 XOR algebra + content-addressed bucketing + co-occurrence statistics give the full pipeline.

---

## §4 What this finding DOES claim

- The F155/F156 substrate supports variable-length sentence generation
- At small/medium scale (N up to 4000), self-recall stays at 1.000
- Hash-bucket hierarchical routing keeps latency sub-second
- Substrate-native generation produces 97.5% grammatically valid sentences
- A substrate-native plausibility metric discriminates valid sentences from random permutations by >13×
- The substrate architecture is operationally tractable at the sizes a compositional cascade would need

## §5 What this finding does NOT claim

Per MFO §VII.6.20:

- Does NOT claim LLM-quality generation (no comparison to a continuous-attention transformer on real-world text)
- Does NOT lift the 3.3% Path C cascade ceiling
- Does NOT claim semantic understanding (plausibility ≈ co-occurrence, not meaning)
- Does NOT claim the template-generated corpus simulates real-world linguistic distribution
- Does NOT measure capacity bounds at full LLM scale (50K vocab, millions of sentences untested)
- Does NOT claim that high-grammar-validity = compositionally-novel; novelty requires sentences not derivable from skeleton walk
- Per `[[user_stance_ai_is_not_a_substrate]]`: Claude is transducer; the substrate is the structural object, not the inferences

---

## §6 Limitations + next steps

**Untested at this scale:**
- Real-world text corpora (this used template-generated sentences)
- Vocabulary at LLM-class size (~50K)
- Hierarchical inference cascade composition (not just storage)
- Substrate plasticity / forgetting at LLM-scale
- Cross-sector composition for multi-clause sentences (current substrate is single-frame)

**Possible next steps (no commitment):**
1. **Real-corpus test**: replace template corpus with English children's book texts (Project Gutenberg / OpenStax / McGuffey ladder)
2. **Multi-clause sentences**: extend sentence layer to L≥8 with multi-frame structure
3. **Cascade composition**: chain plausibility-filtered generation into multi-sentence narrative
4. **Inference latency at vocab scale**: profile bucket routing + skeleton retrieval at V=10000+ tokens
5. **Substrate plasticity at scale**: test F141 sculpted decay during sentence learning (forget rare combinations)

These are deferred until user direction.

---

## §7 Cross-references

- F132 (Klein-4 HDC engineering)
- F154 (4× ceiling validated)
- F155 (chirality-level substrate; R-RBS-LM-55 closure)
- F156 (sentence generation Mode A/B/C/D)
- F148 (R-RBS-NN-12 hierarchical bundling framework reading)
- F141 (substrate density attestation; would apply to plasticity work)
- ARCHITECTURAL_PATTERN_two_tier_klein4_polar.md
- `[[user_stance_kepler_shape_universal]]` (algebra IS the primitives — Klein-4 XOR composes across levels)
- `[[user_stance_whole_research_corpus_is_proof_not_single_arc]]` (this finding is one converging arc, not a standalone claim)

**Files committed (5-item queue):**
- `R-RBS-LM-112_variable_length_sentences.py` + results
- `R-RBS-LM-113_larger_corpus_scaling.py` + results
- `R-RBS-LM-114_hierarchical_scale_up.py` + results
- `R-RBS-LM-115_grammar_validity_metric.py` + results
- `R-RBS-LM-116_semantic_plausibility_scoring.py` + results
- `R-RBS-LM-FINDING_157_*.md` (this finding)

PR #687 STAYS DRAFT.

---

*Articulated 2026-05-28 per user direction "keep pushing for each of these 5 items
sequentially in the order that most makes sense for sequential queue". The 5-item
sequential queue (variable-length → larger-corpus → hierarchical → grammar → semantic)
closes the F156 sentence-generation arc with substrate operationally ready for further
work. Self-recall stays at 1.000 up through N=4000 across 32 hash-buckets; substrate-
native generation achieves 97.5% grammar validity and 13× plausibility discrimination
vs random noise — all without any learned model. The Klein-4 XOR algebra + content-
addressed bucketing + co-occurrence statistics provide the full substrate pipeline.
None of these results lift the 3.3% Path C cascade ceiling; they document that the
substrate architecture is tractable at the sizes a compositional cascade would need.
Per [[user_stance_kepler_shape_universal]]: algebra IS the primitives, and Klein-4
chirality-level structure composes cleanly across the substrate pipeline.*

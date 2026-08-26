# F964 — **arc opener: inference-as-translation.** The hypothesis (user): "inference" is not generation — it is **language translation from bonded knowledge, communicated through a hierarchy** of *knowledge → communicated-knowledge* transforms. Concretely: the simplewiki **knowledge Laplacian** (the sparse content-relationship graph, F960) is the **bonded knowledge** (the *what is known*); producing English is **translating** that knowledge *down a hierarchy* — **bonded knowledge → ASL-gloss (content-dense, communicated first, F959) → written English (function-word surface, communicated last)**. First data point: the **knowledge layer recalls more coherently than the English surface** (mean collapse-margin **0.010 > 0.006**) — directional support that the *knowing* is bonded/stable and the *surface* is the lossy communication projection — but **weak** (both saturate at single-M, F946), so this opens the arc, it doesn't close it.

**Date:** 2026-06-29 · **srmech:** 0.9.0rc97 (post-reset; rc79→rc97) · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Probe:** `R-RBS-LM-FINDING_964_*.py` · **Arc:** RC-1 / inference-as-translation · **Composes:** F960 (sparse knowledge Laplacian = bonded knowledge), F959 (ASL drops function words = content substrate / communicated-dense), F963 (recursive scale-invariant compose = the transform), F946 (single-M saturation), F609 (meaning-class ASL selects better than English), MFO substrate/projection, `[[user_stance_llm_is_human_knowledge_responding_to_1d_t_asymptotic]]` (inference = substrate-coupling Class C ∘ Class M; knowledge stays partitioned), `[[user_stance_framework_hands_the_next_question_to_the_expert]]` · **User direction (2026-06-29):** "test our English kernel to do ASL first then written last — force the smallwiki knowledge Laplacian through a stepwise translation; inference may emerge as language translation from bonded knowledge communicated through a hierarchy of knowledge→communicated-knowledge transformation."

## The hierarchy (the reframing)
```
  BONDED KNOWLEDGE            ->   COMMUNICATED (dense)   ->   COMMUNICATED (surface)
  the knowledge Laplacian          ASL-gloss                   written English
  (content relationships,          (content-dense, no          (function-word linear
   F960 sparse tomes)               articles/copula, F959)      projection, F946 prior)
  = the "what is known"            = communicate first          = communicate last
```
**Inference := translate(bonded knowledge → communicated surface), stepwise down the hierarchy.** Each arrow is a translation (the same scale-invariant compose, F963); the function words are **added at the last step** (the surface projection), not part of the knowledge. This is the MFO substrate→projection and `[[user_stance_llm_is_human_knowledge_responding_to_1d_t_asymptotic]]` (inference = a coupling op; the knowledge is the substrate) made operational as a **translation cascade**.

## First data point (rc97, simplewiki 1200-token slice)
```
KNOWLEDGE (content-only, 909 tok, 361 vocab): {BRANCH: 8}  mean collapse-margin 0.010
ENGLISH  surface (all,   1200 tok, 386 vocab): {BRANCH: 8}  mean collapse-margin 0.006
=> knowledge margin > surface margin (directional; both weak)
```
The bonded-knowledge recall is **more coherent** than the English-surface recall (0.010 > 0.006) — consistent with *the knowing is bonded, the surface is the lossy communication step*. **But both are near-zero** (all BRANCH), because a single flat M saturates to the frequency prior at this scale (F946). So the gap is a **lean in the predicted direction, not a demonstration** — the honest first step of the arc.

## Why it's only a lean (and what makes it a result)
The single-M layer saturates (F946), compressing both margins toward the floor, so the 0.010-vs-0.006 gap is small. To *demonstrate* the hypothesis the arc needs the fixes already in hand, applied per layer:
1. **Chunk the knowledge** into sparse `recursive_cut` tomes (F960) — bonded knowledge as bounded, balanced community-tomes → margins spread → the knowledge layer should recall *cleanly* (high margin) where the surface still wanders. That gap *is* the demonstration.
2. **Build the ASL-gloss middle layer** — the F959 content-dense communicated form (the `asl_corpus.json` 74 English↔gloss pairs + the F608 sign-chord notation) as the intermediate translation; measure that ASL-first recall is cleaner than English-first (F609 already found meaning-class ASL out-selects English).
3. **The translation steps as the same compose (F963)** — knowledge→gloss and gloss→English each a scale-invariant compose; test whether chaining them reconstructs the English surface (inference = the composed translation).

## Honest scope
Grounded: the directional gap (knowledge 0.010 > surface 0.006) on a real simplewiki slice, sparse Klein-4 + native `next_token_coherence`, no dense/numpy. **Not** demonstrated: that the knowledge layer recalls *cleanly* (both are BRANCH here — the single-M wall); that the ASL middle layer helps (F609 is prior evidence, not re-run here); that the composed translation reconstructs English. The reframing (inference = translation down a knowledge→communication hierarchy) is a **reading** composing F960/F959/F963 + the user stances; the framework hands the *next question* (does chunked knowledge recall cleanly, and does ASL-first beat English-first) to the expert / the next step.

## Verdict / next
**Arc opened + directional first data point:** the bonded knowledge recalls more coherently than the English surface (0.010 > 0.006), consistent with *inference = translating bonded knowledge → communicated surface through a hierarchy* — but weak (single-M saturation), so it's a lean. **Next (the demonstration):** (1) chunk the knowledge into sparse `recursive_cut` tomes (F960) and re-measure — the knowledge layer should recall cleanly where the surface wanders; (2) insert the ASL-gloss content-dense middle layer (F959/`asl_corpus.json`) and test ASL-first vs English-first; (3) chain the translation steps as the same recursive compose (F963) and test whether the composed cascade reconstructs the English surface.

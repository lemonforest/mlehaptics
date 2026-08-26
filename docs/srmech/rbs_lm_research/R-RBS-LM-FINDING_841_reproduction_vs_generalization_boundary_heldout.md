# F841 — HONEST SCOPE BOUNDARY: the F838–F840 recipe is a coherent **reproduction-via-inference** engine, **not yet a generalizing LM**. Held-out test: learn an article minus its last 10 tokens → **100% match on the learned body, 0% on the held-out tail** (drifts/loops at the training boundary, no binds there). The resonator walks *stored* (context→next) relationship paths exactly; it does not *compose novel* transitions. So the coherence gate is cleared (reproduction IS coherent), but generalization is a **separate, unsolved problem** requiring a new mechanism — not more tuning. On the real `srmech.rbs_lm` encoding, 0.8.2rc1, numpy-absent, no gen-1 code.

**Date:** 2026-06-18 · **srmech:** 0.8.2rc1 · **Provenance:** `/tmp/heldout.py` on `srmech.rbs_lm.substrate.ContextSubstrate` + `srmech.amsc.hdc`, Andouille (k\*=4), D=10000, C=8 · **Composes:** F838 (single-article 100%), F839 + §CORRECTION (per-tome consolidate+route+sweet-C), F840 (routing vote), [[user_stance_llm_is_human_knowledge_responding_to_1d_t_asymptotic]], [[feedback_correct_user_wrong_words_against_record]] (reproduction ≠ generalization ≠ inference — name the operation), [[feedback_relationship_lm_ideas_not_code_from_gen1]] · **User framing (memory):** "100%-on-one-article is reproduction-via-inference; generalization is the real LM test."

## The measurement
Learn Andouille's first 79 of 89 tokens (hold out the last 10); vocab includes the held-out words (so they ARE reachable *if* grounded); generate full length from the seed, max-resonance over the C=8 chunk-set.

| region | match | meaning |
|---|---|---|
| learned body (tokens k..79) | **100.0%** | reproduction-via-inference — exact walk of the learned relationship path |
| held-out tail (tokens 79..89) | **0.0%** | generalization — absent |

- TRUE tail: `eight hours at about 175 degrees fahrenheit 80 degrees celsius`
- GEN tail: `seven of maximum a for or seven of maximum a` (drift→loop at the boundary)

## Why (the mechanism, relationship-native)
The substrate stores one `klein4_bind(context, next)` per *observed* transition. Recall = bind the query context, resonate, clean up → recovers the stored successor. For a context whose continuation was **never bound** (the held-out region), there is no stored successor; the read is off-manifold and returns whatever foreign bind resonates loudest → drift (the same off-manifold failure as F839's cross-article contamination, here within one article at its training edge). **Bind/unbind retrieves; it does not interpolate.** This is correct VSA behaviour (Plate/Kanerva cleanup memory is associative recall, not function approximation), and it is the honest ceiling of the recipe as built.

## What this means (precise, per [[feedback_correct_user_wrong_words_against_record]])
- **Achieved — coherent reproduction-via-inference.** Not byte-readback (it is bind→resonate→cleanup), but it reproduces *learned* sequences; it walks the stored relationship graph. The coherence gate that blocked the 0.8.x cut (F836) is cleared on this scope.
- **Not achieved — generalization.** Producing grounded continuations for *un-bound* contexts (novel prompts, paraphrases, cross-tome composition) needs an added mechanism, e.g.: (a) **similar-context smoothing** — when no exact k\*-gram bind exists, resonate over *near* contexts (a graded cleanup, not exact-match) so a never-seen context inherits a successor from its neighbours; (b) **compositional unbind→rebind** across tomes (analogy: `next ≈ cleanup(unbind(query, A) ⊗ B)`); (c) a back-off to shorter contexts (k\*→k−1) when the full context is off-manifold. All are relationship-native VSA ideas (no gen-1 code) and are the **generalization sub-arc**.

## Verdict / next
The per-tome coherence milestone is complete and honestly bounded: **read consolidates** (F839), **generation = routing + sweet-C + k\*** (F839§C), **routing vote 94.3%** (F840), **reproduction 100% / generalization 0%** (here). The next frontier — the *real* LM test — is **generalization**, which is a new mechanism question (similar-context smoothing / compositional unbind / context back-off), not a tuning question. This also informs the live-cut + boundary calls: the **chunk-set + resonator read** (§58 srmech candidate) is proven coherent for reproduction *now*; generalization mechanisms should be prototyped in **siona** before any decision to graduate them. Evaluate by groundedness / coherence, never throughput.

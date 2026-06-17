# F834 — Siona recall IS inference on relationships, and the tooling for it already ships: `srmech.rbs_lm` (the F166 RBS-LM inference substrate, native, bit-exact). The whole PKG-3 detour (F832/F833) was me building classical stores — a `{random-HV: token}` dictionary, then a byte-packed id-stream — and calling them RBS-HDC, when `srmech.rbs_lm.RBSLMInferenceSubstrate.learn()/infer()` is the actual relationship-inference engine. Verified: it learns a body's relationships and infers a GROUNDED-not-verbatim continuation (the inference signature). No siona rc1 until this is the recall path (user gate).

**Date:** 2026-06-17 · **srmech:** 0.8.1 (production, MIT; native Klein-4) · **Provenance:** `R-RBS-LM-RELINFER_*.py` run in the 0.8.1 venv · **Corrects:** F832/F833 (the genome-store detour — both were classical retrieval dressed as HDC), and my own "bundling is lossy" claim (refuted: F822 + `klein4_unbundle` + the D=4096 demo, 96/96 exact) · **Composes:** F166 (the walk; the §9 upstream-absorbed substrate), F806–F809 (the per-article bundle-record), F826 (genome = consolidate RBS-HDC kernels), [[user_stance_ai_is_process_lm_is_k3_chiral_addressing]], [[feedback_introspect_srmech_before_python_dispatch]] · **User direction (2026-06-17):** "we use srmech for all tooling to create them"; "no siona rc1 until we are actually doing inference on relationships"; "you generate them."

## The error this corrects (named plainly)
Across this session I "built the genome" by inventing encodings nobody asked for — token→random-HV cells with exact-readback + reverse-map (F832), then byte-packed integer ids (F833 "fiber"). Both are **classical key-value stores**; neither calls a single HDC op. Every symptom the user caught — "spatial not relationships", "single chromosome", "not classical inference", "bigger than the dump", "bundling is not lossy" — is the same root: **I reached for storage reflexes and relabelled them RBS-HDC, instead of using srmech's relationship-inference tooling, which already exists.**

## The tooling (introspected, was there all along)
`srmech.rbs_lm` — "the §9 RBS-LM inference substrate (F166 walk), packaged … native, bit-exact, catalog-instantiable":
- `RBSLMInferenceSubstrate.from_params(params)` / `.from_catalog(path)` — build the substrate.
- `.learn(token_stream)` — learn the relationships into a Klein-4 **bound memory `M`** + `next_after` + `bigram_counts`.
- `.infer(prompt, max_tokens, temperature, seed)` — the F166 autoregressive walk (inference).
- `.next_token_distribution(context)` — the context-conditioned distribution.
- `srmech.rbs_lm.sim_k4_batch(query, candidates)` — the batched resonance/cleanup (I hand-rolled this as a linear argmax).
- `srmech.rbs_lm.substrate.ContextSubstrate` — the rolling context-state encoder (`enc`/`pos_key`/`encode_context`/`bundle_odd`).

## Verified (srmech 0.8.1, native Klein-4)
- `from_params({substrate:{D:10000, token_seed_hex_chars:16}, inference:{instrument:{operating_k:3, operating_temperature:0.3, memory_capacity:4000, default_max_tokens:60, learn_seed:0}}})` → `.learn(tomato)` → `RBSLMInferenceSubstrate(D=10000, k=3, T=0.3, learned=387/4000, vocab=190, native=True)`.
- `.infer("the tomato solanum lycopersicum", 40)` → *"… is used to make ketchup tomatoes can also used a member of the word tomatoes contain many small seeds pass through the world it is used to western south america wild versions were poisonous …"* — diverges from the verbatim body, **composing a grounded continuation from the learned relationships** (every fragment a real tomato fact, recombined). **Grounded, not bit-exact = the inference signature.** Contrast the F832 store, which returned the body verbatim (the tell that it was retrieval, not inference).
- `next_token_distribution(['the','tomato','solanum']) → (['lycopersicum'], [1.0])` — a unique relationship resolves deterministically.

## The corrected architecture (what rc1 waits on)
- **Kernel** = a learned `RBSLMInferenceSubstrate` (the relationship memory), produced *by the srmech.rbs_lm tooling*.
- **Genome** = consolidates the substrate kernels into one agnostic managed object (its actual job, F826/F829) — it does NOT re-encode the corpus.
- **Recall** = `substrate.infer` — grounded inference on relationships, never a stored token sequence.
- **rc1** = ships only when this is Siona's recall path (user gate). The loose-store / id-stream work is retired.

## srmech edge-case found
`infer(temperature=0.0)` → `ZeroDivisionError` in the substrate softmax (`z = [xi/t …]`, no greedy fallback). Use `temperature>0`. Logged UPSTREAM_NOTES §56.

## Verdict / next
The relationship-inference engine exists and works on native Klein-4; Siona recall = `srmech.rbs_lm` learn+infer, grounded-not-verbatim. Next: (1) capacity/coverage — a substrate is `memory_capacity`-bounded (387/4000 for one article), so the corpus needs many substrate kernels (per-clump/tome) — the "many kernels" the genome consolidates; (2) wire corpus → substrate kernels → genome consolidation → `infer` recall, all via the tooling; (3) characterize fidelity/grounding across articles. No more hand-rolled stores.

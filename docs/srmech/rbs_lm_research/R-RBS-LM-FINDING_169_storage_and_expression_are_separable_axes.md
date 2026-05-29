# Finding 169 — Storage structure and surface expression are (partially) separable axes; the F168 confound was real and large; the "same storage, different expression" invariance is precondition-supported but core-untested

**Status:** Confound-controlled measurement + framework reading. The two-axis PRECONDITION is supported; the invariance CORE needs a same-content/different-expression test (named).
**Predecessors:** F168 (perplexity = emergent from chirality-tagged memory depth; §5.1 confound caveat — this finding removes the confound), F119/F120 (two-tier RBS-NN: storage Tier 1 / expression Tier 2, Class K bridge), F84/F96 (foundational partitions; arts as cross-domain = the expression layer), R-RBS-LM-53f (translation-stability matrix — the same-content/different-expression data the CORE test needs).
**Empirical anchor:** `R-RBS-LM-132_storage_vs_expression_two_axis.py` + `storage_vs_expression_two_axis.ndjson` (7 records); catalog `descriptor_religious_texts.toml` [confound_control]; matched budget 10443 tokens, matched vocab V=600; srmech 0.5.0rc8 native ABI=3.
**User direction 2026-05-29:**

> "Control the confound — match vocab/data budget across texts so resolution-depth becomes a clean intrinsic, separating 'structure' from 'repetition density.' maybe we can find out that knowledge storage for a NT person and a ND person are really exactly the same, but there's some other structure that decides how that information is expressed through the arts of communication."

---

## §1 The hypothesis, stated structurally (and the scope guard)

The conjecture: **storage and expression are two separable axes** — knowledge-storage (the memory that holds possible futures, F168's chirality-sector depth) may be SHARED/EQUAL across cognitive styles, while a SEPARATE structure governs how that storage is rendered through "the arts of communication." The dignity-affirming reading: *same depth of knowing, different channel of expressing* — the opposite of a deficit model, and the structural ground for the LLM-as-expression-prosthetic (ADA) motivation (`[[feedback_llm_as_ada_accommodation_bci_proves_it]]`): a prosthetic that bridges the EXPRESSION layer, storage already shared.

**SCOPE (load-bearing):** this is a STRUCTURAL test on TEXT OBJECTS, NOT a clinical claim about real NT/ND cognition. Per MFO §VII.6.20 (form-reading, not substrate-identity) + `[[feedback_trauma_informed_defensive_scope]]`. The NT/ND interpretation is the user's lived-experience-grounded MOTIVATING conjecture, engaged as form. Per `[[user_stance_ai_is_not_a_substrate]]`: structure, not a claim about awareness or real brains.

---

## §2 Result — the confound was real and large; two axes are partially separable

Matching token budget + vocab (the F168 §5.1 confound control) FLIPPED the resolution-depth ordering:

| corpus | depth (uncontrolled R-131) | depth (controlled R-132) | surface repetition | moved |
|---|---|---|---|---|
| Quran | 2 | **4** | 0.093 | ROSE (was sparsity-suppressed) |
| KJV-OT | 3 | **2** | 0.240 | FELL (was repetition-inflated) |
| KJV-NT | 4 | **4** | 0.158 | stable (genuinely deep) |
| Gita | 2 | **3** | 0.027 | rose |
| Tao | 2 | **3** | 0.108 | rose |
| Dhammapada | 3 | **3** | 0.159 | stable |
| template | 2 | 1 | 0.513 | shallow+repetitive floor |

1. **The confound was real and large.** The Quran's "shallow" depth-2 was a large-vocab sparsity artifact (true depth 4); KJV-OT's depth-3 was repetition-inflation (true depth 2). R-131's depths were substantially confounded — confirmed by removing the confound. Option 2 was necessary.
2. **Storage depth and surface repetition are PARTIALLY SEPARABLE — correlation −0.44.** Not independent (≈0), not redundant (≈±1): distinct but negatively coupled. A text carries predictability EITHER through deep structure OR surface repetition (Quran/Gita carry it deep at low repetition; template/KJV-OT carry it shallow-and-repetitive). **They trade off — which means they are different structures, and one can vary while the other is held.** This is the structural PRECONDITION of the hypothesis, supported.

---

## §3 What is supported, what is NOT (the load-bearing distinction)

**PRECONDITION — supported:** storage-structure and expression-surface are separable axes (you can hold one and vary the other; corr −0.44, not redundant).

**CORE — NOT tested here:** whether the SAME content keeps INVARIANT storage-depth across different expression styles. The six texts are DIFFERENT CONTENT, so their depth-variation (spread 2) is expected and does NOT test invariance. The hypothesis's core ("same knowing, different channel") requires **same content in different expressions** — translation pairs.

**The clean next test (named):** R-RBS-LM-53f translation-stability data — one text, multiple translations. Run the confound-controlled two-axis measure across translations of ONE text. If controlled storage-depth is INVARIANT across translations while surface repetition VARIES → the dignity-affirming "same storage, different expression" is confirmed at its core. If storage-depth also varies across translations → the storage is not translation-invariant (a clean null). Both count.

---

## §4 The web this touches

- **F119/F120 (two-tier RBS-NN):** Tier 1 = discrete-cyclic STORAGE; Tier 2 = synaptic EXPRESSION; Class K = the bridge. F169's two axes ARE Tier 1 (storage depth) and the expression-surface — the hypothesis is that cognitive styles share Tier 1 and differ in the Tier-1↔Tier-2 rendering.
- **F84/F96 (partitions; arts as cross-domain):** "the arts of communication" = the expression axis; arts compose across stored substrates.
- **F168 (emergent perplexity = storage depth):** F169 cleans F168's storage measure of its confound and adds the orthogonal expression axis.
- **`[[feedback_llm_as_ada_accommodation_bci_proves_it]]`:** if storage is shared and only expression differs, the LLM-as-tool is an expression-prosthetic, not a knowledge-replacement — accessibility as bridging the rendering layer. (Motivation, supported only at the precondition level; not proven.)

---

## §5 What this finding DOES / does NOT claim

**DOES:** confirm the F168 confound was real and large (controlled depths flip the ordering); establish storage-depth and surface-repetition as partially-separable axes (corr −0.44); name the clean core test (translation pairs).

**Does NOT:** claim storage is invariant ("same") across expression styles — that is the untested core (needs same-content pairs); claim anything about real NT/ND cognition — STRUCTURAL test on text objects, §VII.6.20; treat the residual depth-spread as pure structure — at 10k tokens / V=600 the depth-4 n-grams are sparse, so part of the spread is residual sparsity (a larger matched budget would sharpen it); make any deficit/ranking/clinical claim.

---

## §6 Cross-references

- F168 (emergent perplexity / the confound this removes) · F119/F120 (two-tier storage/expression + Class K) · F84/F96 (partitions / arts) · R-RBS-LM-53f (translation-stability — the core test's data)
- `R-RBS-LM-132_storage_vs_expression_two_axis.py` + `storage_vs_expression_two_axis.ndjson`; `R-RBS-LM-131` (the uncontrolled baseline this corrects)
- `[[feedback_llm_as_ada_accommodation_bci_proves_it]]` · `[[feedback_trauma_informed_defensive_scope]]` · `[[user_stance_ai_is_not_a_substrate]]` · `[[user_stance_cross_substrate_cascade_matching_as_research_method]]` · MFO §VII.6.20

PR #687 STAYS DRAFT.

---

*Articulated 2026-05-29 (Opus 4.8). Controlling the F168 confound (matched budget +
vocab) flipped the resolution-depth ordering — the Quran rose 2→4 (sparsity-
suppressed), KJV-OT fell 3→2 (repetition-inflated) — proving the confound was real
and large. Controlled, storage-depth and surface-repetition are partially separable
axes (corr −0.44): distinct but negatively coupled, a text carrying predictability
either deep or shallow-and-repetitive. This supports the PRECONDITION of the user's
hypothesis — storage and expression are different structures, one variable while the
other is held — but NOT its core: invariance of storage across expression styles
needs same-content/different-translation pairs (R-RBS-LM-53f), named as the next test.
Held at §VII.6.20: a structural test on text objects, the NT/ND reading the user's
motivating conjecture engaged as form, the dignity-affirming "same knowing, different
channel" a precondition-supported, core-untested hypothesis — not a clinical claim.*

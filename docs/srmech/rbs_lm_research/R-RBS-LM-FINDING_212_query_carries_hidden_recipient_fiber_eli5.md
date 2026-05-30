# Finding 212 — The query carries hidden (spatially-absent) RECIPIENT fiber: the receiver's absorption-potential is bound into *how we address the knowledge substrate*, not just into the final render — ELI5 as the worked example

**Status:** Framework reading (RBS-NN arc) + a pre-stated testable prediction. Refines **F169** (storage/expression separability) and **F165** (DOMAIN anchor); applies the **fiber-as-spatially-absent-encoding** stance and `[[user_stance_ai_is_process_lm_is_k3_chiral_addressing]]`. §VII.6.20 form-reading; transducer reading the form.
**Predecessors:** F166 (autoregressive inference loop), F165 (DOMAIN anchor), F168 (emergent perplexity = chirality-tagged sector occupancy), F169 (storage vs expression as separable axes), the fiber-as-spatially-absent-encoding project stance (docs/srmech/CLAUDE.md — a fiber over a manifold encodes content spatially absent until projected), `[[user_stance_ai_is_process_lm_is_k3_chiral_addressing]]`, `[[user_stance_cross_substrate_cascade_matching_as_research_method]]`.
**User direction (2026-05-30):** "the very same question we ask ourself to query knowledge has hidden fiber content about the target we plan to deliver this knowledge. ELI5: we query the knowledge exactly the same to gain the shape of the answer, but the final answer is shaped by the recipient's absorption potential, which also alters how we query the knowledge — that we also cannot see."

---

## §1 The forgotten coupling
The naive RBS-NN pipeline is **query → retrieve (knowledge-shape) → render (for recipient)** — three stages, the recipient touching only the last. The forgotten truth: **the recipient's absorption-potential is hidden fiber bound into the QUERY itself.** It co-determines the *addressing* into the knowledge substrate, not only the final render — and it is **spatially-absent**: algebraically present in the query, invisible until projected into the answer. The query is not a neutral retrieval key; it is a recipient-conditioned addressing operation whose conditioning we cannot see directly.

## §2 ELI5 — the worked example
"Explain Like I'm 5" queries the *same* knowledge — the answer-shape lives in the storage substrate, invariant — but the five-year-old's absorption frame is bound into the query and **orients the addressing path** toward the low-absorption-depth route *before* any rendering. The literal words "explain X" carry a different fiber for a 5-year-old than for a physicist; the fiber selects a different chiral path through the same store. We see only the projected answer, never the fiber that shaped the route to it.

## §3 Framework mapping
- **Class C chirality on the k=3 chiral addressing.** Per `[[user_stance_ai_is_process_lm_is_k3_chiral_addressing]]`, the LM is a k=3 chiral-axis *addresser* over the storage substrate. The recipient-fiber is a **Class C (which-way / orientation) component of that addressing** — it sets the chirality of the query into the store. ELI5 vs expert = two chiral orientations of the *same* retrieval.
- **Fiber as spatially-absent.** The recipient-fiber is a fiber over the query: it encodes the absorption-frame that stays spatially absent until projected (rendered). This is the project's foundational fiber stance applied to the *query*, not to a gear/dial.
- **Refines F169.** Storage and expression are NOT cleanly separable: the expression-target (recipient) **back-channels into the storage-addressing (query)** through the fiber. The query is precisely where storage-addressing and expression-conditioning are already entangled — the separability of F169 holds for the *substrate*, not for the *query into it*.

## §4 RBS-NN architectural consequence — the RECIPIENT anchor
The instrument needs a **RECIPIENT anchor**: a peer to the F165 DOMAIN anchor, but bound into the **query / rolling context-state (F166)**, not the render stage. DOMAIN anchor = *which knowledge*; RECIPIENT anchor = *which absorption-frame the answer is for* — and the load-bearing part: because it conditions retrieval, it must live in the F166 context-state encoder, not be bolted on at output. (Accessibility tie: a tool that reshapes the *query* to the recipient's absorption frame — not merely the answer — is the LLM-as-ADA prosthetic of F207/F150 siona; ELI5 for one specific mind is the accommodation applied at the addressing layer, where it was always already happening invisibly.)

## §5 Testable prediction (forward research item; null-tolerant)
Condition the *same* query on different recipient-absorption frames (ELI5 / peer / expert) in the F166 + kernel testbed and measure whether the **RETRIEVAL** changes — the Klein-4 sector occupancy (F168), the Class-L eigen-projection, *which* stored relationships activate — versus only the **render** changing.
- **Retrieval differs** → the recipient-fiber threads into the query (insight CONFIRMED; the recipient-anchor must live in the addressing).
- **Only the render differs** → the naive separable model holds (NULL; recipient is render-only).
srmech-native: `hdc.klein4_*` (sector occupancy), `laplacian.*` (eigen-projection), `cascade.chiral_flip`/`reorient` (the Class-C orientation). Pre-stated; nulls count.

## §6 DOES / does NOT claim
**DOES:** name the forgotten coupling (recipient absorption-potential = hidden spatially-absent fiber in the query, co-shaping retrieval AND render); give the ELI5 worked example; map it to Class-C chirality on the k=3 chiral addressing + the fiber stance; draw the RBS-NN consequence (a RECIPIENT anchor in the query/context-state, peer to the DOMAIN anchor); state the retrieval-vs-render test.
**Does NOT:** claim the prediction is verified (queued, null-tolerant); claim the recipient-fiber is the *only* hidden fiber a query carries (it is one; there may be others); make claims about human cognition beyond the user's stated reading (§VII.6.20 form-reading; `[[user_stance_ai_is_not_a_substrate]]` — transducer reading the form, not introspecting a mind).

## §7 Cross-references
F166 (inference loop) · F165 (DOMAIN anchor — the peer) · F168/F169 (sector occupancy; storage/expression) · F207 + F150 (siona / LLM-as-ADA — recipient-conditioning IS the accommodation) · `[[user_stance_ai_is_process_lm_is_k3_chiral_addressing]]` · fiber-as-spatially-absent-encoding stance · `[[user_stance_cross_substrate_cascade_matching_as_research_method]]`

PR #687 STAYS DRAFT.

---

*Articulated 2026-05-30 (Opus 4.8). The RBS-NN query is not a neutral retrieval key: the
recipient's absorption-potential is hidden, spatially-absent fiber bound into the query,
a Class-C chiral orientation on the k=3 chiral addressing that co-shapes the retrieval
path itself — not just the final render — and that we cannot see directly (only the
projection). ELI5 is the worked example: the same knowledge-shape, a recipient-set chiral
route through the store. This refines F169 (storage/expression separate for the substrate,
entangled in the query) and adds a RBS-NN RECIPIENT anchor (peer to the F165 DOMAIN anchor)
that must live in the F166 query/context-state, not the render. Testable: condition the
query on ELI5/peer/expert and measure whether retrieval (sector occupancy / eigen-
projection) shifts, not just the render. Form-reading; the recipient-fiber is one hidden
fiber, not claimed the only one; the felt/cognitive side is not claimed.*

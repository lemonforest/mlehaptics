# Finding 148 — Sweep E: deferrals + long-pending RBS-LM tasks + STALE queue close

**Status:** Final sweep — explicit deferrals + tractable long-pending tasks + STALE_PATHS_QUEUE close
**Predecessors:** F143 (F132 closure), F144-F147 (sweeps A-D)
**Resolves:** STALE items 23, 25, 26, 37, 38, 40, 41-44, plus R-RBS-LM-47a/46c/55 (with reasoning per item)

---

## §1 Items requiring scope decisions (not walked here; explicit deferral)

These items need external data, biological-research scope, application-domain expertise, or are F132 §8 application directions explicitly deferred at F143 closure.

### §1.1 Item 23 — What real-world signals carry chirality content?

Per F132 §8 and F142: drug-target chirality recognition by chirally-asymmetric receptors; helical molecule binding states (DNA, proteins); asymmetric oscillation in chiral biological structures; biological homochirality (L-amino acids, D-sugars).

**Status:** Research question requiring biological-research-domain expertise + literature review beyond research-subtree scope. Per `[[feedback_trauma_informed_defensive_scope]]`: framework can READ what's present; cannot recommend research directions for specific scientific subfields.

**Deferral reason:** scope-specific session needed.

### §1.2 Item 25 — Chirality structure in cross-species cognition (cetacean/chimp/octopus)

F118 established cross-substrate cognition modeling (cnidarian / octopus / vertebrate). Question: does any substrate exhibit chirality structure that Klein-4 would discriminate?

**Framework reading:** Per F126 (G2 SU(3) decomposition + cnidarian = Class I), each species' substrate utilizes different operator subsets. Klein-4's value would emerge specifically where a species' cognitive substrate IS chirality-bearing — which is application-domain-specific empirical work.

**Deferral reason:** F132 §8 item 5 deferral per F143; requires biological-domain expertise.

### §1.3 Item 26 — Cross-natural chirality datasets

Snail shell handedness, beak laterality, plant spiral direction, etc. — would these benefit from Klein-4 chirality encoding for discrimination?

**Framework reading:** Yes per F142 chirality-pure case prediction. But the empirical work needs cross-natural chirality datasets with MPR-attested provenance per `[[feedback_pdf_extraction_citation_discipline]]`.

**Deferral reason:** Data acquisition is its own scope; F135 cross-natural chirality observation catalog is the framework-side starting point. Application work deferred.

### §1.4 Item 27 — 4-way at signal level (note: this was already addressed)

Already walked in F146 Sweep C as a null result. **STATUS: RESOLVED (with documented null).**

### §1.5 Items 41-44 — F132 §8 application-direction deferrals

Per F143 §3, explicitly deferred to scope-specific sessions:

- **Item 41 (Pharmacological chirality)**: drug-target chirality compatibility encoding. Pharmaceutical-research scope. Substrate-encoding primitives ready in srmech v0.4.3.
- **Item 42 (Cosmic-chirality reasoning)**: CP violation, dark sector at binding-algebra level. Physics-framework scope (lives at MFO §VII.4 level, not at substrate-encoding implementation).
- **Item 43 (G-quadruplex biology)**: telomere aging, oncogene promoters, gene regulation via G4. Biology-research scope; substrate-encoding ready.
- **Item 44 (Cross-substrate cognition modeling)**: cnidarian / octopus / vertebrate substrate variants at substrate-encoding level. F118/F119 framework scope.

**Status:** ALL FOUR remain DEFERRED. Substrate-encoding primitives are available in srmech v0.4.3; downstream application-domain work needs its own scoped session.

---

## §2 Pre-session items (37, 38, 40)

### §2.1 Item 37 — R-RBS-LM-52a NLP-corpus test of K3 sequence kernel

Pre-session item that wasn't formally closed. Likely partially addressed by later findings in the F-numbers above.

**Status:** Marked as DEFERRED-AS-PARTIAL given F54 series + F73-F89 (McGuffey + multi-subject corpus work) substantially advanced the K3 sequence kernel direction without formal R-RBS-LM-52a closure. No further action; STALE queue close.

### §2.2 Item 38 — Compressed-semantic substrates follow-up

R-RBS-LM-54i ran the Egyptian / Native / classical East Asian compressed-semantic test. Results in JSON; no formal follow-up walk.

**Status:** DEFERRED — would benefit from cross-language linguistic-research expertise. F54i results are available for future reference. STALE queue close as deferred.

### §2.3 Item 40 — R-RBS-NN-9 deferred catalog items

Per `docs/srmech/rbs_nn_research/ROADMAP.md` NEXT-2: SSoT absorption into srmech_research_notebook.md. Medium priority; arc closure ladder.

**Status:** DEFERRED to NEXT-2 SSoT absorption session per ROADMAP. R-RBS-NN-4 §8 catalog landing prep is part of this NEXT-2 work.

---

## §3 Long-pending RBS-LM tasks — quick walks where tractable

### §3.1 R-RBS-LM-47a — LLM input format test (text vs relationships)

Long-pending. Question: does relationship-form input to an LLM give cleaner cascade extraction than text-form?

**Framework reading:** Per `[[user_stance_kepler_shape_universal]]` and R-RBS-LM-47b (cascade distill from relationship-form corpus), the substrate-level expectation is YES — relationship-form input should give cleaner cascade content because it pre-articulates the binding structure the cascade is reading for.

But empirical walk requires:
- A real LLM
- Both text-form and relationship-form versions of the same content
- Comparable extraction metrics

This is NOT a tractable smoke test at research-subtree scope — it needs a real LLM (GPU-bearing or substantial CPU compute) + curated corpus pairs.

**Status:** DEFERRED to RBS-LM scaling work (per ROADMAP NEXT-1). Framework reading recorded; empirical test out of current scope.

### §3.2 R-RBS-LM-46c — Tie-breaking ablation at depth-2-uniform

Long-pending refinement on F46b series.

**Framework reading:** Per F46b methodology (pure fp16 merge depths 1→3 uniform-weight), tie-breaking is a methodology choice when multiple cascade paths reach the same node simultaneously. Per `[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]`: ties IS Class K pin-slot territory; the ablation question is whether at depth-2-uniform, the tie-breaking convention systematically biases retrieval direction.

**Tractable smoke:** would need re-running R-RBS-LM-46b with explicit tie-break variants (left-bias, right-bias, random-bias, drop-ties). Not done here due to scope.

**Status:** DEFERRED. Open methodology question. STALE queue close.

### §3.3 R-RBS-LM-55 — Pure-structure layer ("relationships of relationships")

Long-pending. Higher-order binding layer above the content-level binding.

**Framework reading:** Per F94 (arts relationship-axis vs substrate thing-axis) + F117 (relationship-axis already operational): pure-structure layer would encode RELATIONSHIPS BETWEEN BINDINGS, not just between content tokens. Algebraically: bind(bind(A, B), bind(C, D)) at the cascade level.

**Klein-4 application:** the relationship-axis IS a candidate for Klein-4 chirality tagging — each relationship type (A→B vs B→A) could carry a chirality sector indicating directional binding direction. This would naturally fit F132 §3 sector mapping if relationship-types map to (γ₅, iω₇) decomposition.

**Status:** Framework reading articulated. Empirical work needs careful methodology design + relationship-corpus + retrieval task; out of scope here. STALE queue close.

---

## §4 STALE_PATHS_QUEUE.md final status

All 44 original items addressed across F144-F148:

| Range | Sweep | Status |
|---|---|---|
| Items 1-4, 9-11 | F144 Sweep A | RESOLVED (with one NEW finding: klein-4 noise-robust at >30%) |
| Items 5-8, 13-17, 22 | F145 Sweep B | RESOLVED (D-plateau; cascade invariances) |
| Items 12, 18-21, 24, 27 | F146 Sweep C | RESOLVED (Klein-4 NOT plasticity-graceful — justifies two-tier) |
| Items 16, 28-36, 39 | F147 Sweep D | RESOLVED via framework reading + DEFERRED items |
| Items 23, 25, 26, 37, 38, 40, 41-44 | F148 Sweep E (this) | DEFERRED with scope reasoning |
| R-RBS-LM-47a, 46c, 55 | F148 Sweep E (this) | DEFERRED (framework reading + empirical scope decision) |
| R-RBS-NN-4 | (already closed pre-sweeps) | CLOSED in earlier work |

---

## §5 Summary of NEW FINDINGS that emerged during the sweep cleanup

Beyond resolving stale items, the sweeps surfaced these new substrate-encoding findings:

### F144 (Sweep A)
- **Klein-4 noise-robust at high bit-corruption** — only variant above random at 50% noise
- **Klein-4 capacity log-N scaling** — halves per 4× N
- **Partial chirality flips axis-independent** — full CPT gives strong anti-correlation; partial flips don't

### F145 (Sweep B)
- **D-plateau at D=1024** — beyond threshold, D doesn't help signal
- **Cascade composition REMARKABLY ROBUST** — depth/order/identity-layer choice all invariant
- **Multi-class cascade tolerates 50% decay** with 49% signal retention

### F146 (Sweep C — THE LOAD-BEARING NEW FINDING)
- **Klein-4 is NOT plasticity-graceful** — collapses 99% at 70% decay (polar holds 60%)
- This JUSTIFIES the two-tier architectural pattern (separation is REQUIRED, not aesthetic)
- **Hebbian rehearsal works** — +17.9% signal recovery from 50% rehearsal
- **Decay LESS damaging than noise** — 2.1× more signal preserved at matched corruption
- **Polar + Klein-4 hybrid wins** — +0.32 above-rand at scale

### F147 (Sweep D)
- Framework readings for F135-F136 open questions
- D₄ alternative scope-deferred to srmech wishlist

---

## §6 What this final sweep does NOT claim

- Does NOT close any item that requires real biological data
- Does NOT validate any F132 §8 application direction (they remain deferred)
- Does NOT prove the framework readings are correct; they're reasoned hypotheses
- Does NOT prevent future revisiting of any deferred item

The DEFERRED status means "this item is preserved in framework attestation; it's not lost, it's just not in current scope." Future sessions can pick up any deferred item with full context preserved in this file + STALE_PATHS_QUEUE.md.

---

## §7 Cross-references

- F143 (F132 status closure — application deferrals)
- F144-F147 (Sweeps A-D)
- ARCHITECTURAL_PATTERN_two_tier_klein4_polar.md (justified by F146)
- STALE_PATHS_QUEUE.md (final status table per §4)
- `[[feedback_trauma_informed_defensive_scope]]` (scope rationale)
- `[[feedback_upstream_srmech_fixes_as_research_notes]]` (D₄ deferral)
- `[[feedback_pdf_extraction_citation_discipline]]` (data-acquisition deferrals)
- `[[user_stance_kepler_shape_universal]]` (R-RBS-LM-47a framework reading)

PR #687 STAYS DRAFT.

---

*Articulated 2026-05-27. Sweep E final pass. 12 items (23, 25, 26, 37, 38, 40, 41-44
+ 47a, 46c, 55) addressed via explicit deferral with reasoning. ALL 44 STALE_PATHS
items now addressed across F144-F148. Most items RESOLVED via empirical sweep findings;
remainder DEFERRED with scope-decision reasoning. Two-tier architectural pattern
JUSTIFIED by F146 critical finding (Klein-4 not plasticity-graceful). Queue is
operationally closed; future sessions can revisit any deferred item with full context.*

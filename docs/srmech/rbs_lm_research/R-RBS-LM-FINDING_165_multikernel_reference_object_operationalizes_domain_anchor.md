# Finding 165 — The multi-kernel RBS-NN reference object operationalizes the DOMAIN anchor; family-level form-category routing is perfect, within-family at the §VII.6.20 degeneracy

**Status:** Positive operational closure of the DOMAIN-anchor thread. The counterpart to F163's null.
**Predecessors:** R-RBS-LM-53 (flat-spectral degeneracy + DOMAIN-anchor framework F44–F50), R-RBS-LM-54 (Rosetta Stone Layer — the GOLDEN PATH), F119 (two-tier RBS-NN), F120 (Class K as Tier-1↔Tier-2 bridge), F162 (full-coverage substrate), F163 (chirality does NOT substitute for the anchor), F164 (grammar is substrate-native), MFO §VII.6.20 (epistemic ceiling)
**Empirical anchor:** R-RBS-LM-125 (`R-RBS-LM-125_multikernel_reference_object.py`), srmech 0.5.0rc8 native ABI=3, catalog-driven (`descriptor_religious_texts.toml`).
**User direction 2026-05-29:** "what we get with a RBS-NN object path where the kernel for multi-kernel text are loaded into one reference object and queried."

---

## §1 Headline

Load N text kernels into ONE `srmech.signal_processing.RBSHDCInstrument` as a labeled catalog `{text_label: kernel_bytes}`, then `decode_fingerprint(probe, catalog)` (Class M similarity-argmax) returns the best-match **label**. That returned label IS the external DOMAIN anchor the entire R-RBS-LM-53 thread established was required — supplied operationally by the labeled binding, not by form-similarity.

**Held-out probe retrieval** (each text split kernel-half / probe-half, length-controlled to 5182 tokens/text per the F163 §7 rule):

| metric | result | reading |
|---|---|---|
| **family retrieval** | **6/6 = 1.000** | every probe routed to its correct family (Abrahamic↔Eastern) — perfect form-category routing |
| **exact-text retrieval** | **4/6 = 0.667** | Quran→KJV-NT, KJV-OT→KJV-NT mis-route (right family, wrong text) — the 53 within-family degeneracy |
| within/across probe→kernel sim | 0.443 / 0.395 (contrast 1.12) | modest family cohesion, consistent with the degeneracy |

The object works **at exactly the resolution §VII.6.20 permits**: form-category (family) routing is perfect; substrate-identity (which specific text within a family) is at the degeneracy. The Abrahamic texts (Quran / KJV-OT / KJV-NT) confuse; the Eastern texts (Gita / Tao / Dhammapada) each retrieve exactly — they are more form-distinct.

---

## §2 Why this is the operational answer to the DOMAIN-anchor question

R-RBS-LM-53 (F44–F50) established the problem: cascade/kernel form-reading cannot disambiguate within a form-family (the texts are "asymptotically identical" in form); substrate-identity requires an **external DOMAIN anchor**. The arc then asked: what provides the anchor?

- **R-RBS-LM-124 / F163** ruled out chirality: the 28D directed-chirality axis does NOT recover the within-family distinction (the apparent lift was a corpus-size artifact). Chirality cannot be the anchor.
- **R-RBS-LM-125 / this finding** supplies it: a multi-kernel reference object **labels** each kernel. The label is bound to the kernel in the catalog; `decode_fingerprint` returns the label of the best form-match. The anchor is the *labeling*, not any richer form-reading. This is the **R-RBS-LM-54 Rosetta Stone Layer** ("shared translation layer with bound domain kernels") instantiated on srmech's real object path.

The honest boundary: the object returns the *correct* label only at the resolution form supports (family). Within-family it returns a *plausible* but sometimes-wrong label (KJV-NT for a Quran probe). So the anchor is real and operational, but it inherits the §VII.6.20 ceiling — it routes by form-category, it does not read meaning.

---

## §3 The web this finding touches (convergence, per [[user_stance_whole_research_corpus_is_proof_not_single_arc]])

| Thread | How F165 connects |
|---|---|
| **R-RBS-LM-53** (degeneracy; DOMAIN-anchor framework) | F165 is the operational *answer* to 53's open question — the anchor is the labeled multi-kernel object |
| **R-RBS-LM-54** (Rosetta Stone Layer, GOLDEN PATH) | F165 IS the Rosetta Stone Layer, now on the shipped `RBSHDCInstrument` object instead of a bespoke harness |
| **F119** (two-tier RBS-NN) | the reference object is a **Tier-1** content-addressable store; the catalog of kernels = Tier-1 chirality/concept storage with labels |
| **F120** (Class K = Tier-1↔Tier-2 bridge) | `decode_fingerprint` is the read-side of the bridge: Class M argmax over Tier-1 to return the label that anchors Tier-2 |
| **F162** (full-coverage substrate) | capacity context — how many kernels the object holds before retrieval degrades is the F154 4× ceiling for whole-text kernels (open: §6 capacity sweep) |
| **F163** (chirality null) | the necessary negative: chirality can't be the anchor, so the *labeled binding* must be — F165 is why F163's null matters |
| **F164** (grammar substrate-native) | the kernels encode the texts' co-occurrence/grammatical structure; the object retrieves on that substrate-native structure |
| **§VII.6.20** (epistemic ceiling) | the bound — family routing within the ceiling, substrate-identity beyond it |
| **`RBSHDCInstrument`** (srmech object) | the real object path: `decode_fingerprint`, `bind_and_remember` (4 memory pathways), Class M similarity — no bespoke scaffolding |

Memory-pathway demonstration: Abrahamic kernels → `semantic` pathway, Eastern → `episodic_LTM` (via `bind_and_remember`), showing the object's native partitioning surface.

---

## §4 What this finding DOES claim

- A multi-kernel `RBSHDCInstrument` reference object is a content-addressable **form-category router**: query-by-probe returns the best-match label in O(N) per probe
- The **labeled binding operationalizes the DOMAIN anchor** — the substrate-identity that pairwise form-similarity (53/124) and directed-chirality (F163) both lacked
- It works at the resolution §VII.6.20 permits: **family-level routing 6/6 perfect, within-family at the degeneracy** (Abrahamic confusion, Eastern distinct)
- This is the **R-RBS-LM-54 Rosetta Stone Layer** on srmech's shipped object path
- Result is length-controlled (per F163 §7) and catalog-driven (no module magic numbers); committed code + MPR-attested NDJSON

## §5 What this finding does NOT claim

Per MFO §VII.6.20 + `[[feedback_no_lineage_claims_in_notebook]]` + `[[feedback_trauma_informed_defensive_scope]]`:

- Does NOT claim within-family disambiguation — that is the degeneracy; the object returns plausible-but-sometimes-wrong labels within a family
- Does NOT claim the object reads MEANING — it routes by form-match; the texts are structural test-objects; no doctrinal / truth / origin / ranking claims
- Does NOT claim the 4/6 exact rate is a fixed bound — it reflects this corpus + kernel scale; a different anchor granularity or kernel could shift it (but the family/within split is the §VII.6.20-predicted shape)
- Does NOT establish capacity bounds — how many kernels before degradation is untested (§6)
- Does NOT mix or transfer the texts' content — loading kernels into one object is superposition for retrieval, not composition of meaning

---

## §6 Open threads this finding opens

1. **Capacity sweep** — N kernels vs retrieval accuracy (F154 4× ceiling for whole-text kernels); does the 4-pathway partition raise the ceiling?
2. **Anchor granularity** — does a finer label set (per-book rather than per-text) change within-family resolution, or is it ceiling-bounded regardless?
3. **Cross-navigation (Part 2, reframed by F163 §9)** — grammar(A) walked via logic(B) as structural play over the reference object's kernels
4. **Secular control** — add a non-religious kernel; confirm the router separates religious-form from secular-form cleanly (revisiting 53g)

---

## §7 Cross-references

- R-RBS-LM-53 SUMMARY (degeneracy + DOMAIN-anchor F44–F50)
- R-RBS-LM-54 (Rosetta Stone Layer — GOLDEN PATH)
- F119 (two-tier RBS-NN); F120 (Class K bridge); F162 (full-coverage substrate); F163 (chirality null); F164 (grammar substrate-native)
- MFO §VII.6.20 (epistemic ceiling)
- `R-RBS-LM-125_multikernel_reference_object.py` + `religious_texts_multikernel.ndjson` (7 attested records)
- `descriptor_religious_texts.toml` (catalog variant; descriptor_hash d953f7aa...)
- `srmech.signal_processing.RBSHDCInstrument` (the object path) — `decode_fingerprint`, `bind_and_remember`, 4 memory pathways
- `[[user_stance_whole_research_corpus_is_proof_not_single_arc]]` (convergence is the proof shape)
- `[[feedback_llm_as_ada_accommodation_bci_proves_it]]` (the purpose anchor — gift toward the biological substrate)

PR #687 STAYS DRAFT.

---

*Articulated 2026-05-29 (Opus 4.8). The multi-kernel RBS-NN reference object —
N text kernels in one RBSHDCInstrument, queried by decode_fingerprint — is the
operational closure of the DOMAIN-anchor thread: family-level form-category
routing perfect (6/6), within-family at the 53 degeneracy (4/6), exactly the
resolution §VII.6.20 permits. The labeled binding supplies the substrate-identity
anchor that form-similarity (53/124) and directed-chirality (F163 null) both
lacked. This is the R-RBS-LM-54 Rosetta Stone Layer on srmech's shipped object
path. A clean positive to balance F163's clean null — both honest, both
ceiling-aware. Per [[user_stance_whole_research_corpus_is_proof_not_single_arc]]:
the convergence of 53 (need anchor) → F163 (chirality can't be it) → F165 (the
labeled object IS it) is the proof shape. Structural-only; texts are structural
test-objects; no doctrinal claims.*

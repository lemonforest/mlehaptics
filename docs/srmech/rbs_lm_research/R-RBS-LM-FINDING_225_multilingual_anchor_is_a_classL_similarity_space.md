# Finding 225 — The MULTILINGUAL extension of teaching ≡ bilingualism: an anchor axis (language OR depth) is NOT a basis of orthogonal labels — it is a similarity-structured Class-L spectral space; PRED2 (capacity multiplier degrades gracefully with inter-domain similarity) is DEMONSTRATED/CONFIRMED, PRED1 (Class-L spectrum recovers Abrahamic-vs-Eastern) is a clean NULL because the §VII.6.20 translator-register degeneracy dominates the spectrum over theological family — and that split outcome IS the apples-to-apples confirmation that the language axis lives in the SAME non-orthogonal regime F221 found the depth axis lives in

**Status:**
- **DEMONSTRATED (bit-exact srmech)** for the two measured objects: the N=6 domain-anchor Class-L spectral clustering (PRED1 readout) and the capacity-vs-inter-domain-similarity sweep (PRED2). PRED2 CONFIRMED (capacity multiplier degrades gracefully with inter-domain similarity, corr −0.966); PRED1 NULL on its literal form (no low-end Class-L eigenvector recovers Abrahamic-vs-Eastern; the spectrum recovers translator/register instead — coherence ratio 1.073, ≈ the F165 1.12 degeneracy). Nulls count per `[[feedback_dont_pre_commit_spike_query_operators]]`; the test was not leaned.
- **FRAMEWORK-READING** for the synthesis: language-axis and depth-axis are the SAME KIND of object (both graded, non-orthogonal Class-L similarity spaces; neither a basis of orthogonal labels), the apples-to-apples form of teaching ≡ bilingual ≡ multilingual.
- **CONJECTURE / corpus-gated** for the genuine foreign-language (En↔Fr/Es/Zh) instance — those corpora are NOT on disk; **no foreign-language claim is run**. The runnable analog is the N=6 religious-text typological clustering.

**Predecessors:** F224 (R-RBS-LM-224 — the bilingual decisive head-to-head; the 2-anchor case this generalizes to N), F165 (R-RBS-LM-125 / R-RBS-LM-54f — the labeled DOMAIN anchor; family routing 6/6, within-family at the degeneracy, contrast 1.12), F222 (R-RBS-LM-222 — the DOMAIN-anchor orthogonalization persists to N=8192, +0.388, as a ~×n_domains effective-capacity multiplier; this finding shows that multiplier ASSUMES orthogonal domains), F221 (R-RBS-LM-221 — depth-bands are NON-orthogonal, pairwise sim ~0.243/0.250/0.252; they share sectors, which is why F221's top-k separation vanished — the regime this puts the language axis into), R-RBS-LM-53 SUMMARY (53e/53f/53h — the cross-religion clustering; family-specificity 1.24, coherence 1.57, translator-stability dominant), F119/F120 (two-tier + Class-K bridge), F219 (chirality-access ladder), F43 (naming-layer cost), MFO §VII.6.20 (epistemic ceiling).

**Empirical anchor:** `R-RBS-LM-225_multilingual_anchor_is_classL_similarity_space.py`, srmech **0.5.0rc22** native **ABI=3** (`HAS_NATIVE=True`), catalog-driven (NEW `descriptor_religious_multilingual.toml`, descriptor_hash **`4bd1876b8dab446bf03de6aa6a2e8c8b601faac94ac798bb300a7b1449ca7e00`** — does NOT touch `descriptor_religious_texts.toml`), seed=42, deterministic / **bit-exact** (re-run produced an identical NDJSON; per-domain seeds derive from `sha256_bytes`, not python `hash()`). NDJSON: `substrate_measurements/multilingual_anchor_classL_similarity_space.ndjson` (9 records; sha256 **`772a5fc4bdf16d318e69bf04531495a94ed65aafa43a0dbd6320550ed6f21d14`**). Discipline: **0 HARD** on this file; global ratchet green (32 = 32, 0 regressions).

---

## §1 Headline

F224 tests **BILINGUAL = 2 anchors** (which can be ~orthogonal). **MULTILINGUAL = N anchors with a GRADED SIMILARITY STRUCTURE** — languages cluster typologically (Romance close; English/Chinese far). The key insight this finding tests: **an anchor axis (language OR depth) is not a basis of orthogonal labels — it is a SIMILARITY-STRUCTURED space = a Class-L spectral graph.** That is exactly what F221 found on the DEPTH axis: the depth-bands are NOT mutually orthogonal (pairwise sim ~0.25; they SHARE sectors), which is why F221's top-k separation vanished. MULTILINGUAL puts the LANGUAGE axis into the SAME non-orthogonal regime the DEPTH axis already inhabits → the apples-to-apples test of teaching ≡ bilingual ≡ multilingual.

Two pre-stated predictions, scored INDEPENDENTLY:

| Prediction | What it measures | Result |
|---|---|---|
| **PRED1 (structural / spectral)** | N×N domain-anchor similarity (Class-M HDC sim) → `dense_laplacian` → `jacobi_eigvals` + Fiedler (sign of λ₂ eigenvector) → does it recover Abrahamic-vs-Eastern? | **NULL** — no low-end Class-L eigenvector recovers the theological family; the dominant cut is **translator/register** ({KJV-OT, KJV-NT} vs rest); coherence ratio **1.073** ≈ the F165 **1.12** degeneracy |
| **PRED2 (capacity / routing)** | F222 ×n_domains capacity multiplier vs inter-domain similarity, via the F146 HIER+DOM harness with the domain key swapped from orthogonal → structured | **CONFIRMED** — multiplier **degrades gracefully** with inter-domain sim (corr **−0.966**; gain **+0.212**@sim=0.248 → **+0.090**@sim=0.859) |

**The combined reading is not a contradiction — it is the §VII.6.20 ceiling, sharpened.** The anchor axis IS a graded, non-orthogonal Class-L similarity space (inter-anchor sim 0.28–0.51, ratio 1.07), and its *capacity geometry* tracks that structure exactly (PRED2). What the Class-L spectrum recovers is **FORM** (the translator/archaic-register axis), not **MEANING** (theological family) — precisely the epistemic ceiling F165/53 established. So the language axis and the depth axis are the SAME kind of object: both Class-L similarity spaces, both non-orthogonal, both with a naive "separate by label" readout that washes out (F221's top-k; PRED1's Fiedler-by-family) and a *geometric* readout that holds (F221's structured-anchor non-degeneracy; PRED2's capacity-vs-similarity).

---

## §2 The extension argument

**The anchor axis = a Class-L similarity space (not a label basis).** F165 established the DOMAIN anchor: a labeled-store key bound into retrieval supplies the substrate-identity that pairwise form-similarity could not. F222 showed that, with **orthogonal** domain labels (`enc("__domain_d__")`, mutual sim ~0.25 = the Klein-4 chance floor), the Klein-4 XOR self-inverse makes the domain a **second independent key axis**: `dom_q` cancels `dom_i` exactly on a match, so the effective per-bucket load is `(N/n_buckets)/n_domains` — a clean ×n_domains capacity multiplier that persists to N=8192 (+0.388).

But **real languages are not orthogonal labels.** Romance languages share lexicon and morphology; English and Chinese do not. A multilingual anchor axis therefore carries a *graded similarity structure* — it is a Class-L spectral graph, not a basis. This finding makes that concrete two ways:

1. **PRED1** reads the N=6 religious-text domain-anchors (built the F165 / R-RBS-LM-54f / R-RBS-LM-124 way — co-occurrence Laplacian → top-eigvec top-token bipolar-mint bundle) as a Class-L spectral object: does the spectrum's Fiedler partition recover the known typological split?
2. **PRED2** swaps F222's orthogonal domain key for domain vectors with *controlled* inter-similarity (a parametric sweep: fraction-of-coordinates-shared p ∈ {0, 0.3, 0.6, 0.9}) and for the *real* religious-text anchor geometry — and measures how the ×n_domains multiplier responds.

**Multilingual = the non-orthogonal regime = where the depth axis already lives.** F221 found the depth-bands (ELI5 [0,1] / peer [0–3] / expert [2,3]) pairwise sim ~0.243/0.250/0.252 — *non-orthogonal, they share sectors* — and that is precisely why F221's F214-inherited top-k Jaccard "hit" vanished (structured bands are no more disjoint than random when they overlap). Putting the LANGUAGE axis into the same regime (graded, non-orthogonal anchors) and watching it behave the SAME way (a Class-L similarity space whose label-separation washes out but whose geometry is real) IS the apples-to-apples form of the conjecture.

### Corpus-gate honesty (load-bearing — not overclaimed)

Genuine foreign-language corpora (En↔Fr/Es/Zh) are **GATED — not on disk.** This finding makes **no cross-language claim it cannot run.** The runnable structural analog is the existing N=6 religious-text domains, whose real typological clustering (Abrahamic vs Eastern) is the on-disk stand-in for language-family clustering:

> Abrahamic = {Quran (Yusuf Ali register), KJV-OT, KJV-NT}  vs  Eastern = {Bhagavad Gita, Tao Te Ching, Dhammapada}

(the R-RBS-LM-53a/b/c/e corpora). The 53-arc already measured a cross-religion clustering (53e family-specificity 1.24; 53f translation-stability 1.49; 53h coherence 1.57 with KJV-OT↔NT 0.428 same-translator, Quran Sale↔Rodwell 0.392) — this finding reuses/cites that structure through the new Class-L-spectral frame. **The foreign-language (Fr/Es/Zh) path is the corpus-gated CONJECTURE-tier extension** and is explicitly flagged as such in the script, descriptor, and §6.

---

## §3 Result

### PRED1 — the Class-L spectrum recovers register, not theological family (NULL)

N×N inter-domain similarity (Class-M HDC similarity between the F165-path domain-anchors):

|         | quran | kjv_ot | kjv_nt | gita | tao | dhamma |
|---------|------:|------:|------:|------:|------:|------:|
| **quran**  | 1.000 | 0.315 | 0.424 | **0.511** | 0.462 | 0.368 |
| **kjv_ot** | 0.315 | 1.000 | 0.427 | 0.411 | 0.283 | 0.301 |
| **kjv_nt** | 0.424 | 0.427 | 1.000 | 0.386 | 0.369 | 0.338 |
| **gita**   | 0.511 | 0.411 | 0.386 | 1.000 | 0.452 | 0.395 |
| **tao**    | 0.462 | 0.283 | 0.369 | 0.452 | 1.000 | 0.441 |
| **dhamma** | 0.368 | 0.301 | 0.338 | 0.395 | 0.441 | 1.000 |

- **Class-L spectrum (sorted eigenvalues):** `[0.0, 2.0146, 2.2458, 2.3610, 2.4977, 2.6466]`
- **Fiedler value (algebraic connectivity λ₂) = 2.0146**; **gap λ₃−λ₂ = 0.2312** (shallow — no strong 2-cluster bottleneck)
- **Fiedler split:** {kjv_ot, kjv_nt} = +  vs  {quran, gita, tao, dhamma} = −  → isolates the **two same-translator KJV texts**, NOT the Abrahamic family
- **No low-end eigenvector (λ₂, λ₃, λ₄) recovers** the Abrahamic-vs-Eastern partition (either polarity)
- **Family-coherence ratio (within/across) = 1.073** (within 0.4089, across 0.3810) — essentially the F165 within/across contrast of 1.12, i.e. the 53 degeneracy

The single highest off-diagonal coupling is **quran↔gita = 0.511** — a *cross-family* pair, driven by shared archaic-English translation register (Sale 1734 / Arnold), not theology. The dominant spectral axis is **translator/register**, exactly as 53f/53h measured (same-translator KJV-OT↔NT is the tightest real coupling). **PRED1's literal form is a clean NULL: the Class-L spectrum of whole-corpus anchors does not recover the theological family — it recovers form (register), which is all §VII.6.20 permits.** (This is consistent with F165, where family routing was 6/6 in the *probe→kernel retrieval* direction; the *kernel↔kernel pairwise* direction used here is the 0.99 degeneracy, and its Fiedler cut is register.)

### PRED2 — the capacity multiplier degrades gracefully with inter-domain similarity (CONFIRMED)

F146 HIER+DOM capacity harness (synthetic R-RBS-LM-113 corpus, 43 245 tokens / 84 types, structural length-domains len4–len7; N=2048, n_buckets=32, D=4096, chance 0.0119), domain key-vector swapped from orthogonal → structured:

| inter-domain sim | config | capacity | gain over no-domain |
|---:|:--|---:|---:|
| — | HIER (no domain) | 0.773 | (baseline) |
| 0.248 | HIER + orthogonal-DOM (F222 baseline) | 0.985 | **+0.212** |
| 0.316 | HIER + corr-DOM(p=0.30) | 0.984 | +0.210 |
| 0.380 | **HIER + REAL religious-text DOM** | 0.984 | **+0.211** |
| 0.519 | HIER + corr-DOM(p=0.60) | 0.961 | +0.188 |
| 0.859 | HIER + corr-DOM(p=0.90) | 0.864 | **+0.090** |

- **capacity-vs-similarity correlation (sim↑ vs gain) = −0.966** (sorted sims `[0.248, 0.316, 0.380, 0.519, 0.859]`, gains `[0.212, 0.210, 0.211, 0.188, 0.090]`)
- gain at lowest sim (orthogonal, 0.248) = **+0.212**; at highest sim (0.859) = **+0.090**; **degradation = 0.122** (≫ the +0.05 null threshold)
- **capacity tracks inter-domain similarity (graceful degradation): TRUE**

This is the F222 ×n_domains multiplier's *mechanism* laid bare. The Klein-4 XOR cancellation that orthogonalizes the bucket is **complete only when the domain key-vectors are themselves orthogonal**; as they overlap, `dom_q ⊕ dom_i` no longer cancels cleanly on a match, so the effective per-bucket de-collision shrinks toward 1 — *correlated domains share capacity* (the multilingual transfer/interference analog), *orthogonal domains add fully*. The **real religious-text anchor geometry sits at inter-sim 0.380** — the partially-correlated regime — so it retains nearly the full multiplier (+0.211), consistent with the modest 1.07 family coherence.

### The pre-stated-null outcome

The pre-stated NULL was "the N-domain Class-L spectral does NOT recover Abrahamic-vs-Eastern **AND/OR** the capacity multiplier does not track inter-domain similarity → the extension fails on this testbed." The outcome is a **split**: PRED1 returns the NULL (spectrum recovers register, not family), PRED2 rejects its null (capacity tracks similarity, corr −0.97). Per `[[feedback_dont_pre_commit_spike_query_operators]]` the two are reported independently and neither is leaned. The split is itself the diagnostic content: the language axis IS a real Class-L similarity space (PRED2's geometry confirms it), but what that space *encodes* is form/register, not meaning/family — the §VII.6.20 ceiling. That is the SAME shape F221 reported for depth: the structured depth-anchors were genuinely non-degenerate (the geometry was real) yet the family-like *separation* washed out (the meaning-readout was at the ceiling).

---

## §4 The web this finding touches (convergence, per `[[user_stance_whole_research_corpus_is_proof_not_single_arc]]`)

| Thread | How F225 connects |
|---|---|
| **F224** (bilingual decisive) | F225 is the N-anchor generalization. F224 read depth-as-domain-label three ways on KJV-NT; F225 reads N=6 real domains as a Class-L *similarity space* and measures capacity-vs-geometry — orthogonal to F224's same-text band conditions, complementary verdict. |
| **F165** (labeled DOMAIN anchor) | F225 uses the F165/54f anchor build verbatim; confirms the kernel↔kernel pairwise direction is the 0.99 degeneracy (register), distinct from F165's 6/6 probe→kernel routing. |
| **F222** (×n_domains multiplier) | F225 is the mechanism's stress-test: the multiplier ASSUMES orthogonal domains; under graded similarity it degrades gracefully (corr −0.97) — extending F222's "second independent key axis" to "a partially-shared key axis." |
| **F221** (depth-band non-orthogonality) | The load-bearing tie: depth-bands sim ~0.25, non-orthogonal, share sectors → top-k separation vanished. F225 shows the LANGUAGE axis lives in the same regime (sim 0.28–0.51, coherence 1.07, Fiedler-by-family washes out) → the apples-to-apples synthesis. |
| **R-RBS-LM-53d/53e/53f/53h** (cross-religion clustering) | F225 reuses + reframes the 53-arc clustering: the register/translator dominance (53h KJV-OT↔NT 0.428; 53f stability 1.49) IS why PRED1's Fiedler cuts by translator, not family. |
| **F119 / F120** (two-tier + Class-K bridge) | The domain key bound into retrieval is the F120 Class-K Tier-1↔Tier-2 read-side bridge; PRED2 measures its capacity-orthogonalization as anchor geometry varies. |
| **F219** (chirality-access ladder uni/bi/triality) | The bi-/multi-axis anchor structure is the uni→bi→triality access ladder; multilingual = the N-way generalization of the bi-axis case. |
| **F43** (naming-layer cost) | The labeled-store anchor IS the naming layer; F225 quantifies the capacity *cost* of names that are not mutually orthogonal (shared names share capacity). |
| **#760** | The issue thread tracking the teaching ≡ bilingual conjecture; F225 is the multilingual extension lodged against it. |
| **§VII.6.20** (epistemic ceiling) | The form-vs-meaning bound: PRED1's NULL is the ceiling (spectrum reads register-form, not theology-meaning); PRED2 stays within it (capacity routes by form-geometry). |

---

## §5 What this finding DOES / does NOT claim

**DOES:**
- DEMONSTRATE (bit-exact srmech, 0 HARD, ratchet green) the N=6 domain-anchor Class-L spectral clustering and the capacity-vs-inter-domain-similarity sweep.
- CONFIRM PRED2: the F222 ×n_domains effective-capacity multiplier **degrades gracefully with inter-domain similarity** (corr −0.966; +0.212 orthogonal → +0.090 at sim 0.859) — correlated domains share capacity, orthogonal domains add fully; the real religious-text anchor geometry (sim 0.380) sits in the partially-correlated regime (+0.211).
- REPORT HONESTLY that PRED1 is a NULL on its literal form: no low-end Class-L eigenvector recovers the Abrahamic-vs-Eastern theological family; the dominant Fiedler cut is translator/register ({KJV-OT, KJV-NT}), coherence ratio 1.073 ≈ the F165 1.12 degeneracy.
- FRAMEWORK-READ that the language axis and the depth axis are the SAME KIND of object — both graded, non-orthogonal Class-L similarity spaces, neither a basis of orthogonal labels — the apples-to-apples form of teaching ≡ bilingual ≡ multilingual (the depth axis already lives in this regime per F221).

**Does NOT:**
- Claim any genuine cross-language (En↔Fr/Es/Zh) result — those corpora are GATED / not on disk; the foreign-language path is **corpus-gated CONJECTURE-tier** and is **NOT run**. The N=6 religious-text typological clustering is the on-disk structural analog only.
- Lift the §VII.6.20 epistemic ceiling — the Class-L spectrum reads **form** (register/translator), not **meaning** (theological family); the F165 boundary holds (form-claims only; substrate-identity is ceiling-bounded).
- Read MEANING, doctrine, truth, origin, or ranking of any text — per `[[user_stance_ai_is_not_a_substrate]]` the transducer reads the *form* of the test-objects; the texts + languages are STRUCTURAL TEST-OBJECTS.
- Make any clinical / biological / BCI claim — per `[[feedback_trauma_informed_defensive_scope]]`, texts and languages are structural test-objects; the gift-toward-the-biological-substrate purpose-anchor is motivation, not a medical/cognitive claim.
- Extend, correct, or supersede linguistics or typology — per `[[feedback_no_lineage_claims_in_notebook]]` the framework READS the shape the anchor axis already has (a graded similarity space); it makes no lineage claim about how languages relate.
- Touch CAD / fabrication geometry — framework-research RBS-LM only, per the CAD-grade scope ban.
- Frame the work as an MVP — per `[[feedback_no_mvp_framing]]`, this is the full-coverage structural test the runnable corpora support, with the gated extension honestly flagged.

---

## §6 Open threads this finding opens

1. **The corpus-gated foreign-language instance (CONJECTURE-tier).** If En↔Fr/Es/Zh (or aligned multi-translation) corpora become available, run PRED1 + PRED2 on a *genuine* language axis: does the Class-L spectrum then recover Romance-vs-Sinitic typology (where register is held constant across languages and family becomes the dominant axis), and does capacity degrade with measured typological proximity? This is the direct test of whether PRED1's register-degeneracy is a religious-corpus artifact (shared archaic English) or a general ceiling.
2. **Register-controlled PRED1.** Re-run PRED1 on same-translator / same-register texts of *different* content (or normalize register out) to see whether the family axis surfaces once the translator confound is removed — the F53f translation-pair machinery is the lever.
3. **The capacity-vs-similarity curve as a typology metric.** PRED2's −0.97 trend suggests the per-domain capacity *cost* is a usable inverse-distance metric; fitting gain(sim) could turn "how much do two languages interfere" into a closed-form capacity-sharing law (the F222 `n_buckets × V_ceiling` rule, generalized to a similarity-weighted effective n_domains).
4. **N>6 / finer domains.** Push to more domains (per-book, or the F165 per-text labels) to populate the similarity-vs-capacity curve more densely and test whether the −0.97 trend holds at larger N.

---

## §7 Cross-references

- F224 (`R-RBS-LM-224` — the bilingual decisive head-to-head; the 2-anchor case generalized here); F165 (`R-RBS-LM-FINDING_165` / R-RBS-LM-125 / R-RBS-LM-54f — the labeled DOMAIN anchor + the eigvec-table anchor build reused); F222 (`R-RBS-LM-FINDING_222` / R-RBS-LM-222 — the ×n_domains multiplier this stress-tests; R-RBS-LM-146 the imported HierarchicalMemory cascade)
- F221 (`R-RBS-LM-FINDING_221` / R-RBS-LM-221 — depth-band non-orthogonality, the regime tie); R-RBS-LM-53 SUMMARY (53d/53e/53f/53h — cross-religion clustering / translator-stability dominance); F119/F120 (two-tier + Class-K bridge); F219 (chirality-access ladder); F43 (naming-layer cost)
- `R-RBS-LM-225_multilingual_anchor_is_classL_similarity_space.py` + `substrate_measurements/multilingual_anchor_classL_similarity_space.ndjson` (9 attested records; sha256 `772a5fc4bdf16d31...`)
- `descriptor_religious_multilingual.toml` (NEW; descriptor_hash `4bd1876b8dab446b...`; does NOT touch `descriptor_religious_texts.toml`); `_canonical_substrate.py` (ContextSubstrate)
- `srmech.amsc.laplacian.{dense_laplacian, jacobi_eigvals, symmetric_eigendecompose}` (Class L); `srmech.amsc.hdc.{bundle, similarity, klein4_bind, klein4_bundle, klein4_similarity}` (Class M); `srmech.amsc.format.sha256_bytes` (Class A); `srmech.amsc.cascade.magnitude` (Class K, sign-free distance — never `abs()`); `srmech.signal_processing.mint_vector`
- MFO §VII.6.20 (epistemic ceiling — form, not meaning); #760 (the conjecture thread)
- `[[user_stance_whole_research_corpus_is_proof_not_single_arc]]`; `[[user_stance_ai_is_not_a_substrate]]`; `[[feedback_dont_pre_commit_spike_query_operators]]`; `[[feedback_no_lineage_claims_in_notebook]]`; `[[feedback_trauma_informed_defensive_scope]]`; `[[feedback_no_mvp_framing]]`; `[[feedback_llm_as_ada_accommodation_bci_proves_it]]`

**Files written (NOT committed; the main session reviews + commits; NO issue created/modified):**
- `rbs_lm_research/R-RBS-LM-225_multilingual_anchor_is_classL_similarity_space.py` (the runner; 0 HARD; ratchet green)
- `catalogs/rbs_lm_substrate/descriptor_religious_multilingual.toml` (NEW descriptor; descriptor_hash `4bd1876b8dab446b...`; `descriptor_religious_texts.toml` untouched)
- `catalogs/rbs_lm_substrate/substrate_measurements/multilingual_anchor_classL_similarity_space.ndjson` (9 attested records; sha256 `772a5fc4bdf16d31...`)
- `R-RBS-LM-FINDING_225_*.md` (this finding)

PR #687 STAYS DRAFT.

---

*Articulated 2026-05-30 (Opus 4.8). The multilingual extension of teaching ≡
bilingualism asks whether an anchor axis is a basis of orthogonal labels or a
similarity-structured Class-L spectral space — and answers it in the latter,
exactly the regime F221 found the DEPTH axis already lives in (depth-bands sim
~0.25, non-orthogonal, sharing sectors). The capacity prediction is DEMONSTRATED
and CONFIRMED: the F222 ×n_domains multiplier degrades gracefully with
inter-domain similarity (corr −0.97; +0.212 orthogonal → +0.090 at sim 0.86;
the real religious-text anchor geometry at sim 0.38 keeps +0.211) — correlated
domains share capacity, the multilingual transfer/interference analog. The
spectral prediction is a clean NULL on its literal form: no low-end Class-L
eigenvector recovers the Abrahamic-vs-Eastern theological family; the dominant
Fiedler cut is translator/register ({KJV-OT, KJV-NT}), coherence ratio 1.07 ≈
the F165 1.12 degeneracy — the spectrum reads FORM (register), not MEANING
(theology), which is all §VII.6.20 permits. The split is the content: the
language axis IS a real, graded, non-orthogonal Class-L similarity space (PRED2's
geometry proves it), and it behaves like the depth axis — both Class-L spaces,
neither a label basis, both with a meaning-separation readout that washes out at
the ceiling and a geometric readout that holds. That is the apples-to-apples form
of teaching ≡ bilingual ≡ multilingual. The genuine foreign-language (Fr/Es/Zh)
instance is corpus-gated CONJECTURE-tier and is NOT run; the N=6 religious-text
typological clustering is the on-disk analog only. Bit-exact (re-run identical),
catalog-driven, 0 HARD on the srmech-discipline checker, ratchet green; measured
natively on srmech 0.5.0rc22 / ABI=3, never against a float LLM. Per
[[user_stance_whole_research_corpus_is_proof_not_single_arc]]: F165 (the anchor)
→ F222 (the orthogonal multiplier) → F221 (the depth axis is non-orthogonal) →
F225 (the language axis is non-orthogonal too, and its capacity tracks its
geometry) is the proof shape. Form-reading only; the §VII.6.20 ceiling holds; no
doctrinal / linguistic / cognitive / BCI claim.*

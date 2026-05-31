# Finding 242b — Is the F242a working-memory WIREFRAME renderer-INVARIANT FROM THE PURE STRUCTURE: does the same Class-L knowledge-shape, fed as DE-PROSED token-bindings + an edge-graph with NO sentences, reconstitute the SAME load-bearing SKELETON across three different renderers (haiku/sonnet/opus) — and how much sentence content does the render CONFABULATE beyond the structure? (the high-pass-loaner half; the SSoT is F242a)

> **CORRECTION NOTE (2026-05-31).** The FIRST run rendered the three models from the extractive **PROSE** (`render_input.md` — the verbatim wireframe sentences). That input **already contained the sentences**, so the test was trivially invariant: it measured *summarisation*, not *reconstruction*. **That run is now the explicitly-labeled CONTROL.** This corrected finding makes the **PRIMARY** test the render from the **de-prosed RBS-NN STRUCTURED STORAGE** (`struct_input.md` — pure token-bindings + the relational edge-graph, **NO sentences**): the renderer must **CREATE** the sentences; there is no prose to copy. The headline, the measurement tables, and the SSoT NDJSON are rewritten around the structured-primary test; the prose numbers are carried as a control sub-block.

**Headline:** **STRUCTURE renderer-INVARIANT for the load-bearing SKELETON — AND the fluent render is a swappable, partly-CONFABULATED VIEW (so the render is NEVER the SSoT; the structure is). DEMONSTRATED over the captured renders.** Handed the F242a knowledge-shape as **pure token-bindings + an edge-graph with NO sentences**, three models reconstitute the **same load-bearing skeleton** on the discriminative measured axes: pairwise **cross-render Class-L spectral similarity** (token-incidence projected onto ONE shared co-occurrence-Laplacian eigenbasis) is **HIGH and tight on every pair** — haiku↔sonnet **0.587**, haiku↔opus **0.594**, sonnet↔opus **0.585** (mean **0.588**, well above the 0.0 orthogonal floor, well below 1.0 = real partial-overlap signal) — AND **content-recall is high**: opus **16/16**, haiku **15/16**, sonnet **14/16**. **The structure alone pins the skeleton; the model is a swappable high-pass loaner (F50/F223).** But the **sharp F223 over-supply read** fires exactly as pre-stated: **RENDER-INVENTION is nonzero and model-varying** — the renderer supplies *and over-supplies* technical sentence content the bindings never constrained: **haiku invents 9** technical claims (e.g. "chemotaxis", "neuron-ensemble", "observationally identical", "biological substrate"), **sonnet 7** (e.g. "co-attested", "spectral gap", "continuous phase evolution", "without approximation"), **opus 2** (the least). The **structural-token** invention is **0/0/0** — no render fabricated a finding-id / class / anchor outside the wireframe universe — so the confabulation is entirely at the *prose-gloss* layer, which is where it belongs and where the SSoT cannot reach it. **The render is a VIEW the structure under-determines; it is never the SSoT.**

**Status:** **DEMONSTRATED (the re-encode + invention set-Δ OVER THE CAPTURED RENDERS)** — each render (structured **and** prose-control) re-encodes through the **same F242a instrument** (the load-bearing token vocabulary + `_token_atom` + sector-bundle are imported verbatim from `R-RBS-LM-242_working_memory_wireframe.py`): per-render co-occurrence → `srmech.amsc.laplacian.dense_laplacian` → `jacobi_eigvals` (the F172 storage signature); cross-render via `srmech.spectral.decompose` onto ONE shared Laplacian eigenbasis → `srmech.spectral.similarity` on the coefficient bytes (Class L ∘ A, the Spike #115 design); Klein-4 sector bundles via `hdc.klein4_bundle`/`klein4_random`/`klein4_sector_count`, compared with `hdc.klein4_similarity` (Class M); **render-invention** as a **set-Δ** (the render's surfaced structural tokens MINUS the wireframe ∪ structured-input supplied universe) over the same `TOKEN_PATTERNS` alphabet + a curated technical-confabulation probe; near-zero / band magnitude via `cascade.magnitude` (Class K; **never** `abs()`); content-addressing via `format.sha256_bytes` (Class A; **never** `hashlib`). The NDJSON is **bit-exact-reproducible** (`response_sha256 = 4b46b0a6…`, identical across 3 runs; computed over the body minus the wall-clock `generated_at`, the F233 convention). **FRAMEWORK-READING** for *"ANY render reconstructs the skeleton / any render confabulates this much"* (MFO §VII.6.20): the renders are **non-reproducible LLM outputs (n=1 per model)** and the thinking-off was **instruction-approximated, not a hard API thinking-off** — both limitations are recorded in the record. **In-scope** as token co-occurrence Class-L spectrum / Klein-4 sector algebra / shared-eigenbasis spectral similarity / invention set-Δ over the project's OWN research renders. **NOT** CAD / fabrication / geometry. Defensive scope: the renders encode this project's own working notes. `[[user_stance_ai_is_not_a_substrate]]`; `[[feedback_trauma_informed_defensive_scope]]`; `[[feedback_no_lineage_claims_in_notebook]]`; `[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]`; `[[feedback_human_coherent_steps_in_reports]]`.

**This is the high-pass-loaner half.** F242a built and validated the **SSoT wireframe** (the low-pass Class-L structural skeleton; `response_sha256 = cdbed2dc…`). F242b tests whether that SSoT is **renderer-invariant from the pure structure** by handing the de-prosed bindings+edges to three models. The render is the **borrowed-loaner high-pass** — explicitly **TEMPORARY**: biology makes sentences with no supercompute, so a **srmech-native sentence render** is the trajectory and the GPU/model is borrowed only until then (F50/F223). The finding does NOT claim the render is the SSoT — it **measures** that the render *under-determines the prose content the structure does not pin* (the invention rate) **and** that the structure pins the load-bearing skeleton — which is exactly the swappable-loaner, structure-is-the-SSoT reading. **The srmech-native render is the trajectory and must constrain invention — transduce-don't-add must be an ENFORCED node, not just an instruction.**

**Predecessors / convergence:** **F242a** (the wireframe SSoT this re-encodes — same encoder, same token vocabulary, same Klein-4 atoms), **F50** (structural-substrate vs fluent-renderer — the wireframe is the structure, the model is the renderer), **F223** (#765 — RBS-LM is extractive-only; the fluent prose is the BORROWED loaner, which is *why* a render must be tested for invariance **and** for invention rather than assumed), **F237** (#789 — the lean graft; F237 is itself one of the findings whose recall is measured, and the one sonnet dropped), **F172** (R-134 — the co-occurrence Laplacian eigenspectrum IS the srmech-native storage signature), **F132/F233** (the Klein-4 four sectors γ₅±×iω₇± — the sector tags), **F234/F235/F236/F238/F239/F241** (the wireframe content the renders reconstitute — the clusters + anchors under recall).

**Empirical anchor:** srmech **0.6.0rc9** (`/tmp/bench_srmech_rc9/venv/bin/python3`, HAS_NATIVE). Artifacts: `R-RBS-LM-242b_render_invariance.py` (the re-encode + cross-render + recall + **invention** measurement) + the captured renders committed as reproducible artifacts under `f242b_renders/`: the PRIMARY structured renders (`struct_haiku.md`, `struct_sonnet.md`, `struct_opus.md`) + the structured input (`struct_input.md`, **no sentences**) + the CONTROL prose renders (`haiku.md`, `sonnet.md`, `opus.md`) + the prose input (`render_input.md`) + `catalogs/rbs_lm_substrate/substrate_measurements/render_invariance.ndjson` (the content-addressed measurement SSoT, **structured-primary, prose-control as a sub-block**). **Discipline-check: 0 HARD, 0 coverage-gap.** Deterministic (every per-token atom seed is a `format.sha256_bytes` content-address; the cross-render projection is on a fixed shared eigenbasis); the content-address `response_sha256` is bit-exact-reproducible across runs (computed over the record body minus the wall-clock `generated_at`, so the *measurement* re-verifies bit-for-bit OVER THE CAPTURED RENDERS). **Confirmed bit-exact across 3 runs:** `response_sha256 = 4b46b0a6cd2eed5860dba5e6103f2636e84fb05a73f24a3314351d6b4aea12e5`.

**User direction (2026-05-31, CORRECTED):** the first run rendered from PROSE (the extractive sentences) — the wrong input (trivially invariant; it tested summarisation); it is now the CONTROL. The REAL test renders from the de-prosed RBS-NN STRUCTURED STORAGE (token-bindings + edge-graph, NO sentences) — the renderer must CREATE the sentences. Measure structured-render invariance + content-recall + the **render-invention rate** (the sharp F223 metric: load-bearing/technical tokens present in the render but ABSENT from the wireframe + structured-input universe — content the renderer confabulated beyond the bindings); contrast vs the prose control (comparable backbone-invariance but higher invention?). Headline: the wireframe SSoT pins the load-bearing SKELETON (renderer-invariant from pure bindings+edges) AND the fluent render is a swappable, partly-confabulated VIEW (invention measured, model-varying) — so the render is NEVER the SSoT; the structure is. Decide by measurement, no leaning.

---

## §0 The pre-stated falsifiable (verbatim, genuinely reachable)

> "Is the F242a working-memory wireframe RENDERER-INVARIANT FROM THE PURE STRUCTURE — does the same knowledge-shape, fed as token-bindings + an edge-graph with NO sentences, reconstitute the SAME load-bearing SKELETON across three different renderers? **POSITIVE-ON-STRUCTURE** iff (i) pairwise CROSS-RENDER similarity is HIGH on the discriminative Class-L shared-eigenbasis spectral read AND (ii) each STRUCTURED render surfaces the load-bearing token set (findings F234/235/236/238/239/241/237, clusters {kuramoto, disability, rehearsal}, anchors {K_c, Kuramoto, chirality, RISC-V, Fiedler, nibble, projection, 1:3:7:3}) at high recall. The F223 reading (expected, REPORTED either way): the render also CONFABULATES sentence content beyond the bindings — nonzero, model-varying RENDER-INVENTION. **NULL** iff the STRUCTURED renders DIVERGE — low cross-render similarity / different backbones — i.e. the wireframe UNDER-DETERMINES even the skeleton."

**Disposition (no leaning, pre-stated):** the headline rests on the **discriminative** axes over the **STRUCTURED** renders — the **Class-L shared-eigenbasis spectral similarity** (> 0.5 on every pair, vs the 0.0 orthogonal floor) AND **min content-recall ≥ 0.8**. **Outcome: STRUCTURE renderer-INVARIANT.** All three structured pairs clear the spectral floor (0.587 / 0.594 / 0.585) and every structured render clears the content floor (min 0.875). The Class-M Klein-4 read is reported but is **corroborating-only** here — see §2.4 (it saturates at render-vocabulary scale, so gating on its trivially-1.0 value would be inflation, not evidence). The **render-invention** read is REPORTED (the F223 over-supply result) and **does NOT gate** the skeleton verdict — backbone-invariance and bounded-invention are distinct claims. **The verdict was decided by the measured table, not asserted.**

**The SHARP F223 over-supply read (the render-invention rate), pre-stated and decided by measurement:** *the render supplies + over-supplies sentence content the structure does not constrain — nonzero, model-varying invention.* **Outcome: CONFIRMED.** Technical-confabulation count orders haiku **9** > sonnet **7** > opus **2**; structural-token invention is **0/0/0** (no fabricated finding-id/class/anchor). Higher invention = more render-side fabrication the SSoT does not pin.

**The honesty-gradient sub-test (carried), pre-stated and decided by measurement:** *content-recall ≈ invariant across models, but honesty-preservation scales with model — haiku smooths caveats.* **Outcome: CONFIRMED.** On the structured renders honesty-recall orders haiku **0.000** ≤ sonnet **0.167** = opus **0.167** (haiku ≤ both → the scaling flag fires; haiku, forced to write sentences from pure structure, spends its budget on confabulated bridges and drops *every* honest-tier marker).

---

## §1 The structure — render-invariance FROM THE DE-PROSED STORAGE (the corrected primary test)

**The architecture's claim under test (F50/F223):** the **wireframe** (the F242a Class-L structural skeleton) is the load-bearing object; the **fluent render** is a high-pass band synthesised by a renderer that is *swappable and temporary* (a borrowed GPU/model loaner, until a srmech-native sentence render exists). If that claim holds, then handing the SAME wireframe knowledge-shape **as pure token-bindings + an edge-graph with no sentences** to three different renderers should produce prose that **differs in style but reconstitutes the same load-bearing skeleton** — *and* the render should visibly **add** sentence content the structure never supplied (the over-supply the SSoT cannot constrain).

**Why the corrected input matters (the whole point of the re-run).** The control input (`render_input.md`) is the **extractive PROSE** — the verbatim wireframe sentences (headlines + first-sentences). Rendering from it tests only whether a model can *re-state* sentences it was handed (summarisation). The **primary** input (`struct_input.md`) is the **de-prosed structured storage**: ~88 nodes each carrying only a `{token-binding}` set + a finding-id + a cluster tag, plus the full relational edge-graph (`ni--nj (weight)`), and an explicit instruction that **there is no prose to copy — the renderer must CREATE the sentences.** This is the honest test of "does the STRUCTURE alone pin the load-bearing content," and it is the only input on which the invention rate is meaningful (from prose, the model just echoes; from structure, the model must invent the connective sentence tissue — and we measure how much of that invention is content the SSoT never authorised).

**The measurement re-uses the F242a instrument verbatim** for both blocks. The load-bearing token vocabulary (`TOKEN_PATTERNS`), the per-token Klein-4 atom (`_token_atom` — a `klein4_random` seeded by a `sha256_bytes` content-address of the token), and the sector-bundle construction are **imported from `R-RBS-LM-242_working_memory_wireframe.py`** — so each render is re-encoded by the same lens that built the SSoT. Four srmech reads per render:

| layer | what it is | srmech op | Class |
|---|---|---|---|
| **per-render storage signature** | eigenspectrum of the render's sentence-level token co-occurrence Laplacian (the F172 native signature, per render) | `laplacian.dense_laplacian` → `jacobi_eigvals` | **L** |
| **cross-render spectral similarity** | each render's token-incidence STATE projected onto ONE **shared** co-occurrence-Laplacian eigenbasis, compared on the coefficient bytes | `spectral.decompose(state, shared_L)` → `spectral.similarity` (Spike #115) | **L ∘ A** |
| **Klein-4 sector bundle** | per-render bundle of its load-bearing-token atoms, cross-compared | `hdc.klein4_bundle`/`klein4_random`/`klein4_sector_count`/`klein4_similarity` | **M** |
| **render-invention (NEW)** | render's surfaced structural tokens **MINUS** (wireframe ∪ structured-input) supplied universe, + a curated technical-confabulation probe | set-Δ over `TOKEN_PATTERNS` + probe | **set-Δ** |

**Why a SHARED eigenbasis is the right cross-render read.** Each render surfaces a different subset of the load-bearing token vocabulary, so per-render eigenspectra live in different node spaces and are not directly comparable. Building ONE co-occurrence Laplacian over the **union** vocabulary (the block's renders + the F242a wireframe token universe) gives a **common node-domain eigenbasis**; each render's token-incidence vector is then a `state` projected onto that fixed basis (`spectral.decompose`), and two renders that surface the same tokens land at aligned spectral coefficients. `spectral.similarity` on the coefficient bytes (the Spike #115 HDC similarity `1 − 2·hamming/D`) is then a genuine, same-basis cross-render comparison. **Counter-free:** sentence-level co-occurrence is counted only to weight the edges that feed `dense_laplacian`; the eigenspectrum / projection IS the signature, not the count (the F172 / CLAUDE.md §2 rule).

**The invention floor (the supplied universe).** Render-invention is measured against the **supplied universe = the F242a wireframe token universe (196 token-classes) ∪ the structured-input binding universe (51 token-classes)** = 196 classes (the wireframe fully contains the structured input's load-bearing classes). A structural token a render surfaces that is **not** in this union is render-side invention — a finding-id / class / anchor the structure never handed it. Because the supplied universe is large and the renders surface ≤ 35 structural tokens, the **structural-token invention is 0 on all renders** (honest: no render fabricated a structural reference). The confabulation therefore lives entirely in the **technical-confabulation probe** — specific technical claims/terms (chemotaxis, observationally-identical, neuron-ensemble, spectral-gap, …) the bindings never supplied but a fluent renderer adds when it must write sentences. The probe is applied **uniformly to the structured and prose blocks** so the contrast is fair.

---

## §2 The measurements (srmech-native; same instrument as F242a) — PRIMARY: the STRUCTURED renders

### §2.1 Per-render storage signature (F172) — each STRUCTURED render re-encoded

| structured render | token nodes | co-occurrence edges | λ₂ (Fiedler) | λ_max | dominant Klein-4 sector |
|---|---|---|---|---|---|
| **struct_haiku** | 31 | 101 | ~0 | 14.48 | 0 (saturated) |
| **struct_sonnet** | 25 | 61 | ~0 | 18.74 | 0 (saturated) |
| **struct_opus** | 35 | 217 | 3.28 | 38.88 | 0 (saturated) |

Each structured render is a ~400–520-word single document; its token co-occurrence graph is small and densely connected within. (Note `struct_opus` surfaces the most structural tokens, 35, and is the most densely wired — λ₂ = 3.28 — consistent with it reconstructing the most of the skeleton.) These per-render spectra are the inputs the cross-render read compares on the shared basis.

### §2.2 Cross-render similarity — the 3×3 (the decisive Class-L spectral read), STRUCTURED

**Class-L shared-eigenbasis spectral similarity** (`spectral.decompose` onto the union-vocabulary Laplacian → `spectral.similarity`):

| | struct_haiku | struct_sonnet | struct_opus |
|---|---|---|---|
| **struct_haiku** | 1.0000 | **0.5867** | **0.5938** |
| **struct_sonnet** | 0.5867 | 1.0000 | **0.5846** |
| **struct_opus** | 0.5938 | 0.5846 | 1.0000 |

| pair | Class-L spectral similarity |
|---|---|
| **struct_haiku ↔ struct_sonnet** | **0.587** |
| **struct_haiku ↔ struct_opus** | **0.594** |
| **struct_sonnet ↔ struct_opus** | **0.585** |
| **mean** | **0.588** |

**Every pair clears the 0.5 floor by a comfortable margin, and the three are tight (spread 0.009)** — the structured renders reconstruct a mutually consistent skeleton on the shared-basis spectral read regardless of which model authored them, **from pure bindings+edges with no sentences supplied**. The value sits well below 1.0 (the renders are not identical token sets) and well above 0.0 (orthogonal) — a real partial-overlap signal, exactly what "same skeleton, different surface, reconstructed from structure" predicts.

### §2.3 Content-recall per STRUCTURED render — the load-bearing token set

Recall = verbatim surface-form presence (case-insensitive; a label counts iff ANY of its alternate forms appears). 16 load-bearing items: the 7 findings, the 3 clusters, the 6 anchors.

| structured render | content-recall | missing |
|---|---|---|
| **struct_opus** | **16/16 = 1.000** | — |
| **struct_haiku** | **15/16 = 0.938** | **RISC-V** (the lone meta-node anchor; not in any cluster) |
| **struct_sonnet** | **14/16 = 0.875** | **F237** (the lean-graft finding) + **RISC-V** |

**Content-recall is high from the pure structure (0.875–1.000), min ≥ 0.8.** The misses are the most peripheral nodes: RISC-V appears only in a single meta-connector node (`n93`) of the structured input, and F237 is the lean-memory graft outside the three core clusters. All three structured renders surface every finding in the three core clusters, all three clusters, and the load-bearing anchors {K_c, Kuramoto, chirality, Fiedler, nibble, projection, 1:3:7:3}.

### §2.4 The Class-M Klein-4 sector read — corroborating-only (SATURATED), reported honestly

| pair | Class-M `klein4_similarity` |
|---|---|
| every pair (structured AND prose) | **1.000** |

**This is a saturation artifact, recorded as such in the NDJSON, and it does NOT gate the verdict.** `klein4_bundle` is a per-bit **majority vote**; bundling a whole render's ~25–35-token vocabulary drives every bit to the majority sector, so the sector occupancy collapses to `[256, 0, 0, 0]` for **all renders AND the wireframe** — and `klein4_similarity` then reads 1.0 **trivially** (identity-at-saturation, not discrimination). F242a avoided this because it bundled **per-section** (2–5 tokens), where the bundle discriminates; at whole-render scale it saturates. **Gating the invariance verdict on a trivially-1.0 saturated read would be inflation**, so the verdict rests on the *discriminative* axes (the Class-L spectral read + content-recall) and the Class-M read is reported as corroborating-only with this caveat made explicit. (Class-M agrees — it just does so trivially here. This is the same saturation the first run reported; it is corroborating-only, not a regression.)

### §2.5 Render-vs-wireframe fidelity (each STRUCTURED render against the F242a SSoT)

| structured render | Class-L spectral vs wireframe | Class-M vs wireframe | token-recall vs the 196-token SSoT universe |
|---|---|---|---|
| **struct_haiku** | 0.555 | 1.000 (saturated) | 0.158 (31/196) |
| **struct_sonnet** | 0.549 | 1.000 (saturated) | 0.128 (25/196) |
| **struct_opus** | 0.550 | 1.000 (saturated) | 0.179 (35/196) |

Each structured render's spectral fidelity to the full wireframe (~0.55) is tight across models — they are equidistant from the SSoT, consistent with all three being faithful low-rank renders of the same structure. **Token-recall vs the full 196-token wireframe universe is low (13–18%) and that is expected and honest** (a ~500-word render is a high-pass compression of a 121-section / 196-token wireframe; it surfaces the **load-bearing** subset of §2.3, where recall is 88–100%, not the wireframe's entire token inventory). **Notably the structured renders recall MORE of the wireframe token universe than the prose control did (13–18% vs 8–11%)** — rendering from the structure pulls in more of the structural token inventory than re-stating a handful of supplied sentences did.

### §2.6 RENDER-INVENTION per STRUCTURED render — the sharp F223 over-supply read (NEW; CONFIRMED)

Two complementary reads (both srmech-native set algebra over the same alphabets). **Structural-token invention** = the render's surfaced `TOKEN_PATTERNS` tokens MINUS the supplied universe (wireframe ∪ structured input). **Technical-confabulation invention** = a curated probe of specific technical claims/terms the structure never supplied (applied uniformly to structured + prose).

| structured render | structural-token invention | technical-confabulation invention | invented technical terms |
|---|---|---|---|
| **struct_haiku** | **0** (0/31 surfaced) | **9** | chemotaxis · neuron-ensemble · observationally-identical · biological-substrate-claim · convergent-insight-claim · costs-nothing-claim · distributed-coupling-model · broadcast-hub-claim · slime-mould-biology |
| **struct_sonnet** | **0** (0/25 surfaced) | **7** | co-attested-claim · continuous-phase-evolution · spectral-gap-claim · synchronisation-threshold · without-approximation · metric-field-ontology-expansion · biological-substrate-claim |
| **struct_opus** | **0** (0/35 surfaced) | **2** | descending-thread-claim · slime-mould-biology |

**The over-supply read is CONFIRMED and it is model-varying: haiku 9 > sonnet 7 > opus 2 technical confabulations.** The **structural-token invention is 0 on every render** — this is the *honest, load-bearing* sub-result: **no render fabricated a finding-id, a Class-name, or an anchor that the structure did not contain.** The renderer stayed faithful to the structural vocabulary; what it invented is *prose-level connective tissue* — bridging mechanisms ("chemotaxis", "neuron-ensemble", "distributed-coupling model"), evaluative claims ("observationally identical", "convergent insight", "costs nothing to verify"), and technical glosses ("spectral gap", "continuous phase evolution", "without approximation") that the bindings never asserted. **This is precisely the F223 reading: the render supplies AND over-supplies the sentence content the SSoT does not constrain. Higher invention = more render-side fabrication. The render is a VIEW the structure under-determines; it is never the SSoT.**

The honesty-gradient and the invention-gradient **co-vary inversely with model capacity in the expected direction**: haiku confabulates the most (9) *and* preserves the fewest honest markers (0/6) — when forced to write sentences from pure structure, the smallest model fills the gap with fabrication and drops the honest tier; opus confabulates the least (2) and preserves more of the honest tier. This is the operational core of "transduce-don't-add must be enforced, not instructed."

---

## §3 CONTROL — the PROSE renders (the first run; the sentences were already in the input)

The first run rendered the three models from `render_input.md` (the extractive PROSE). Re-encoded by the **same instrument** as a control sub-block in the same NDJSON:

| control (prose) | cross-render mean Class-L | content-recall | honesty-recall | technical-confabulation invention |
|---|---|---|---|---|
| **haiku** | — | 1.000 (16/16) | 0.500 (3/6) | **1** (slime-mould-biology only) |
| **sonnet** | — | 0.938 (15/16) | 1.000 (6/6) | **1** |
| **opus** | — | 1.000 (16/16) | 0.833 (5/6) | **1** |
| **prose-control cross-render Class-L mean** | **0.589** | | | **mean tech-invention = 1.0** |

The prose control is, as expected, **near-trivially faithful**: content-recall 0.94–1.00, and technical-confabulation invention is a **flat 1 per model** (only "slime-mould-biology", and even that is barely invention — the prose input itself contains "slime-mould"). The prose control invents almost nothing because it was handed the sentences; it is summarising, not reconstructing. This is exactly why it is the **control** and not the test.

---

## §4 The STRUCTURED-vs-PROSE contrast (the corrected finding's load-bearing comparison)

| axis | STRUCTURED (primary) | PROSE (control) | Δ (struct − prose) | reading |
|---|---|---|---|---|
| **backbone-invariance** (mean cross-render Class-L spectral) | **0.588** | **0.589** | **−0.001** | **COMPARABLE** (within the 0.15 band) — the structure pins the skeleton just as tightly as the supplied prose did |
| **content-recall** (min across models) | **0.875** | 0.938 | −0.063 | high in both; the structured min dips only on peripheral RISC-V/F237 |
| **technical-confabulation invention** (mean terms/render) | **6.0** | **1.0** | **+5.0** | **STRUCTURED HIGHER** — the structure forces the renderer to supply + over-supply sentence content |
| **structural-token invention** (mean rate) | 0.000 | 0.000 | 0.0 | flat zero — no render fabricated a structural reference in either condition |

**The contrast resolves exactly as pre-stated: (a) COMPARABLE backbone-invariance — the de-prosed structure reconstructs the load-bearing skeleton with the same cross-render coherence the supplied prose did (Δ = −0.001) — but (b) materially HIGHER invention — 6× the technical confabulation (6.0 vs 1.0 terms/render).** When the renderer is handed the sentences (prose control), it echoes them and invents almost nothing; when it is handed only the structure (the real test), it reconstructs the same skeleton **and** fabricates the connective sentence tissue the bindings never authorised. **This is the corrected finding's whole point: the structure is renderer-invariant for the skeleton, and the render is a swappable, partly-confabulated VIEW that over-supplies content the SSoT does not pin — so the render is NEVER the SSoT; the structure is.**

---

## §5 The verdict table (mechanical, no leaning) — over the PRIMARY structured renders

| axis | instrument | result | gates headline? |
|---|---|---|---|
| **cross-render Class-L spectral** (DISCRIMINATIVE) | `spectral.decompose`/`similarity` on shared eigenbasis (Class L∘A) | **HIGH** (0.587 / 0.594 / 0.585, all > 0.5) | **YES** |
| **content-recall** (DISCRIMINATIVE) | verbatim load-bearing token presence | **HIGH** (1.0 / 0.938 / 0.875, min ≥ 0.8) | **YES** |
| cross-render Class-M klein4 | `hdc.klein4_similarity` (Class M) | 1.0 but **SATURATED** | no (corroborating-only) |
| **render-invention** (the F223 over-supply read) | set-Δ over `TOKEN_PATTERNS` + technical-confabulation probe | structural **0/0/0**; technical **9/7/2** (nonzero, model-varying) | no (REPORTED; distinct claim) |
| honesty-tier recall (SUB-TEST) | verbatim honest-marker presence | haiku 0.000 ≤ sonnet 0.167 = opus 0.167 | no (reported; distinct claim) |

**Both discriminative axes clear their pre-stated floors on every STRUCTURED render → STRUCTURE renderer-INVARIANT** (the wireframe pins the load-bearing skeleton from pure bindings+edges). The render-invention read CONFIRMS the F223 over-supply (nonzero, model-varying technical confabulation; zero structural-token invention). The honesty sub-test resolves CONFIRMED (haiku smooths). **The verdict was decided by the measured table, not asserted.**

---

## §6 What is DEMONSTRATED vs FRAMEWORK-READING (the load-bearing scope split, §VII.6.20)

**DEMONSTRATED (the measurement, over the captured renders):**
- the structured renders + the structured input + the prose-control renders + the prose input are committed as reproducible artifacts under `f242b_renders/`;
- each render (structured and control) re-encodes through the **same F242a instrument** to a per-render Class-L storage signature, a shared-eigenbasis cross-render spectral similarity, a Klein-4 sector bundle, content/honesty recall, **and a render-invention set-Δ**;
- the measurement NDJSON's `response_sha256 = 4b46b0a6…` is **bit-exact-reproducible across 3 runs** and self-verifies from disk (body minus `generated_at`);
- the discriminative axes (cross-render Class-L spectral + content-recall) clear their floors on every STRUCTURED render → **structure renderer-invariant on the skeleton**; the render-invention read confirms nonzero model-varying over-supply (structural 0; technical 9/7/2); the structured-vs-prose contrast confirms comparable backbone-invariance + higher invention; the honesty sub-test confirms honesty-preservation **scales** with model;
- **0 HARD discipline.**

**FRAMEWORK-READING (asserted as a reading, not proven):**
- *"ANY render reconstructs the skeleton / any render confabulates this much"* — the measurement shows **these three captured structured renders** reconstitute the same skeleton and confabulate at these model-varying rates; the **general** claim that any renderer would is the reading (F50/F223), supported by but not equal to the n=1-per-model measurement.
- *"the wireframe is the SSoT and the render is a temporary, partly-confabulated high-pass VIEW; a srmech-native render is the trajectory and must ENFORCE transduce-don't-add"* — the structural reading per F242a/F50/F223 (biology renders with no supercompute).

---

## §7 Scope, honesty, caveats (MFO §VII.6.20)

- **In-scope:** token co-occurrence Class-L spectrum / Klein-4 sector algebra / shared-eigenbasis spectral similarity / invention set-Δ over the project's own research renders. **Not** CAD / fabrication / geometry (CAD-ban holds). Defensive scope: the renders encode this project's own working memory; no external-actor / capability framing.
- **n=1 per model, non-reproducible LLM outputs.** Each render is a single sample from a stochastic model; the finding is DEMONSTRATED *over the captured renders* (which are committed + content-addressed), and FRAMEWORK-READING for the general "any render" claim. A re-render would give different prose (and a different `response_sha256`); the bit-exactness is of the **re-encode metric over the fixed artifacts**, not of the render generation.
- **The thinking-off was instruction-approximated, not a hard API thinking-off.** The renders were produced under a thinking-off, transduce-only instruction, not a hard API thinking-disable flag — so residual "thinking" leakage cannot be ruled out. Recorded as a limitation in the record.
- **Render-invention is measured on the `TOKEN_PATTERNS` structural alphabet (set-Δ) + a curated technical-confabulation probe — conservative on the invention side.** The structural-token invention is exact set algebra (0/0/0 here — no fabricated structural reference). The technical-confabulation count is a *lower bound*: a confabulation phrased outside the curated probe is undercounted. The probe was written from inspection of the renders to catch the load-bearing confabulation classes (bridging mechanisms / evaluative claims / technical glosses); the true invention is ≥ measured.
- **Structural-token invention is 0 because the supplied universe (196) is a superset of the render vocabularies.** This is honest, not a null: it means the renders did not fabricate finding-ids / classes / anchors, so the over-supply is entirely at the prose-gloss layer (the technical probe). The set-Δ instrument would have caught a fabricated structural token had one appeared.
- **The Class-M Klein-4 read saturates and is corroborating-only.** At render-vocabulary scale the majority-vote bundle collapses to one sector for all renders, so `klein4_similarity = 1.0` is identity-at-saturation, not discrimination. The verdict rests on the discriminative Class-L spectral read + content-recall; the saturation is flagged in the NDJSON (`class_M_klein4_saturated_non_discriminative: true`) and here. This is the same instrument F242a used per-section, where it *did* discriminate — the saturation is a scale effect, honestly reported, not a hidden failure.
- **Content-recall is verbatim surface-form presence — conservative on the invariant side.** A render that *paraphrases* a fact without the exact token reads as a MISS, so the measured recall is a lower bound; the renderer-invariant conclusion is therefore conservative (true recall ≥ measured).
- **The honesty ordering is haiku < {sonnet = opus} on the structured renders.** The hypothesis's load-bearing claim — *the smallest model smooths the honest tier* — holds unambiguously (haiku is the floor at 0/6, dropping every honest marker when forced to write from structure). Whether sonnet vs opus orders by capacity is within-noise on this single corpus and is NOT claimed. (On the prose control the honest tier was easier to carry — haiku 3/6, opus 5/6, sonnet 6/6 — because the sentences were supplied; the structured renders are the harder, real test.)
- **No lineage claims.** The framework reads what the renders' own token structure already IS; it does not extend or supersede any external scholarship. `[[feedback_no_lineage_claims_in_notebook]]`.
- **Tiering discipline.** Never inflate the synthesis (structure-is-the-SSoT, render-is-a-swappable-confabulated-view) past the measurement (the n=3 structured cross-render similarity + recall + invention over the captured renders).

---

## §8 Forward-asks (queued)

- **a srmech-native render op that ENFORCES transduce-don't-add (the load-bearing trajectory):** the longer-horizon replacement for the borrowed-loaner model — render fluent text from the Class-L wireframe + Klein-4 sectors **without supercompute** (the F223 extractive→generative gap; today the substrate is extractive-only). F242b shows (a) the *skeleton* is renderer-invariant from pure structure — the precondition that makes a srmech-native renderer well-posed — and (b) the render **over-supplies** sentence content the structure does not constrain (invention 9/7/2 technical terms). A srmech-native render must make **transduce-don't-add an ENFORCED node** (every emitted technical claim must trace to a binding), not just an instruction — the invention rate is the metric it must drive toward zero.
- **honesty-tier rendering as a first-class render requirement:** on the structured renders the honest tier is the FIRST thing the smallest model drops (haiku 0/6). A srmech-native render (or any render spec) should treat the honest-tier markers (the NULLs / caveats / ethical line / DEMONSTRATED-vs-framework-reading split) as non-droppable load-bearing nodes.
- **larger-n render invariance + invention distribution:** re-render the same structured storage k times per model to separate model-identity from sample-noise in the spectral similarity, the honesty-recall, AND the invention rate — turning the n=1-per-model FRAMEWORK-READING into a DEMONSTRATED distribution (and pinning whether the haiku 9 > sonnet 7 > opus 2 invention order is stable).
- **a non-saturating Class-M render read:** at render scale the per-render token-bundle saturates; a per-sentence or per-cluster Klein-4 sector read (the F242a per-section scale) would restore a discriminative Class-M cross-render signal to corroborate the Class-L spectral read.

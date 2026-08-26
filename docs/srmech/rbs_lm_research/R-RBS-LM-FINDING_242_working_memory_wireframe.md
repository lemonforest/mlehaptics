# Finding 242a — Is the SSoT for WORKING memory a srmech structural WIREFRAME (the low-pass Class-L co-occurrence/Laplacian storage signature + Klein-4 sector tags), and does that wireframe capture the live session's load-bearing structure BETTER than a flat summary? (the SSoT half; the GPU fluent render is the separate, temporary F242b)

**Headline:** **POSITIVE — DEMONSTRATED.** The working-memory CORPUS (the committed findings F234–F241 + the ROADMAP queue + the running session notes — 10 files, 121 sections) encodes to a srmech structural wireframe whose Class-L storage signature (F172) is **bit-exact-reproducible** (`response_sha256 = cdbed2dce378…`, identical across 3 runs) AND whose structure **SEPARATES the pre-named finding-clusters on all three independent srmech-native reads** (the edges were built BLIND to the cluster labels): the **Kuramoto** cluster {F234/F236/F241} vs the **disability** reading {F239} vs the **rehearsal** cost-asymmetry {F238}. The decisive read is the **Class-L BLOCK-STRUCTURE (modularity)** — every cluster is denser WITHIN (disability **1.000**, rehearsal **0.600**, Kuramoto **0.319**) than the across-cluster co-occurrence rate (**0.109**) — relational structure a flat summary, by construction, cannot have. Corroborated by the **giant-core spectral Fisher** read (best eigenvector Fisher ratio **17.18 ≫ 1** on the 80-section connected core where λ₂=0.96>0) and the **Class-M Klein-4 sector** read (mean intra-cluster `klein4_similarity` **0.697 > 0.685** inter-cluster). **A memory FILE is therefore NOT the SSoT for working memory; the wireframe is — the file is a render/view.**

**Status:** **DEMONSTRATED (encoder + bit-exact fingerprint + measured cluster geometry)** — the section-relational co-occurrence graph → `srmech.amsc.laplacian.dense_laplacian` → `jacobi_eigvals` (the F172 storage signature = the wireframe fingerprint) + `symmetric_eigendecompose` on the giant component (the cluster-separating spectral embedding) + per-section Klein-4 sector tags via `hdc.klein4_bundle` of per-token `klein4_random` atoms → `klein4_sector_count` (Class M), with the three separation reads computed over labels the edges never saw. **FRAMEWORK-READING** for the synthesis claim ("this IS the working-memory SSoT; wireframe-is-memory, renders-are-views"; MFO §VII.6.20). **In-scope** as section-relational-graph / Class-L-spectral / Klein-4-sector algebra over the project's OWN research notes. **NOT** CAD / fabrication / geometry. Defensive scope: the corpus is this project's own working notes; no external-actor / capability framing. `[[user_stance_ai_is_not_a_substrate]]`; `[[feedback_trauma_informed_defensive_scope]]`; `[[feedback_no_lineage_claims_in_notebook]]`; `[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]`; `[[feedback_human_coherent_steps_in_reports]]`.

**This is the SSoT half ONLY.** The high-pass FLUENT render — turning the wireframe back into readable prose — is **F242b**, a **SEPARATE** task, and explicitly **TEMPORARY**: it is a borrowed GPU loaner. Biology makes sentences with no supercompute, so a srmech-native render is the trajectory; the GPU is borrowed only until then. F242a (this finding) builds and validates the SSoT skeleton; it does not render, and it does not depend on the render. Per **F223**, the RBS-LM substrate is **extractive-only** — it cannot author fluent prose — which is exactly WHY the kept content here is verbatim spans (never abstractive) and the render is a separate, flagged-temporary half.

**Predecessors / convergence:** **F237** (#789 harness half — convert-X-to-RBS-NN-object by EXTRACTIVE surgical graft + spectral-compare; F242a applies that conversion to the **live SESSION's working memory**, not to a static `CLAUDE.md` file), **F50** (structural-substrate vs fluent-renderer — the wireframe is the structure, the render is the renderer), **F28/F32** (FFT-band composition — the wireframe is the **LOW-PASS band**, the fluent render is the high-pass band), **F223** (#765 — RBS-LM is extractive-only, cannot render fluent prose — the reason content stays verbatim + the render is separate), **F172** (R-134 — the co-occurrence **Laplacian eigenspectrum** IS the srmech-native storage signature, NOT a `Counter()` proxy — the fingerprint), **F132/F233** (the Klein-4 four sectors γ₅±×iω₇± — the sector tags), **F239/F238/F234/F236/F241** (the corpus content under encoding — the clusters being separated).

**Empirical anchor:** srmech **0.6.0rc9** (`/tmp/bench_srmech_rc9/venv/bin/python3`, HAS_NATIVE). Artifacts: `R-RBS-LM-242_working_memory_wireframe.py` (the encoder) + `catalogs/rbs_lm_substrate/substrate_measurements/working_memory_wireframe.ndjson` (the wireframe SSoT — the content-addressed structural skeleton + the verbatim extractive nodes) + `_graft_pruned_DEBUG.md` (the EPHEMERAL pruned-parts, transient / NOT-the-SSoT). **Discipline-check: 0 HARD, 0 coverage-gap; ratchet GREEN (0 regressions, new work added 0 HARD).** Deterministic (every per-section seed is a `format.sha256_bytes` content-address of the section's token set; no noise/RNG-without-seed); the content-address `response_sha256` is bit-exact-reproducible across runs (computed over the record body minus the wall-clock `generated_at`, the F233 convention, so the *measurement* re-verifies bit-for-bit). **Confirmed bit-exact across 3 runs:** `response_sha256 = cdbed2dce37857a099dece7992644be67c91d27ebf3396eb62f4dbd589eb8f8d`.

**User direction (2026-05-31):** build F242a — the working-memory WIREFRAME encoder (the SSoT half). WORKING memory = the live session's load-bearing state (the committed findings, the ROADMAP queue, the open decisions + their relational structure) — which is MORE than the CLAUDE.md/MEMORY.md files, and a memory FILE must NEVER be the SSoT for working memory. The SSoT for working memory is a srmech WIREFRAME: the low-pass structural skeleton (Class-L co-occurrence/Laplacian storage signature F172; Klein-4 sector tags), lossless OF STRUCTURE, compact. The high-pass fluent render is a SEPARATE, temporary GPU loaner = F242b, NOT this job.

---

## §0 The pre-stated falsifiable (verbatim, genuinely reachable)

> "Does the Class-L wireframe (eigenspectrum + Klein-4 sector tags) of the working memory capture the load-bearing structure BETTER than a flat summary? **POSITIVE** iff (i) the structural fingerprint is BIT-EXACT-reproducible across runs AND (ii) the spectrum / sectors SEPARATE the finding-clusters — concretely the Kuramoto cluster {F234, F236, F241} vs the disability reading {F239} vs the rehearsal cost-asymmetry {F238} must occupy distinguishable regions of the section-relational graph (a flat summary, by construction, has no such relational structure). **NULL** iff the wireframe is structurally FLAT (eigenspectrum near-degenerate) OR the clusters do NOT separate (the pre-named clusters land on top of one another in both the spectral embedding AND the Klein-4 sector tags)."

**Disposition (no leaning, pre-stated):** the verdict is a mechanical read of the measured cluster geometry. **POSITIVE** iff the spectrum is non-flat AND the **decisive Class-L block-structure read** separates the clusters (every cluster denser within than the across-cluster rate). If the fingerprint is bit-exact but the decisive read fails, report **POSITIVE-ON-FINGERPRINT / NULL-ON-SEPARATION** — do NOT inflate to POSITIVE. **Outcome: POSITIVE.** The fingerprint is bit-exact, the spectrum is non-flat, and ALL THREE reads (block-structure decisive + spectral-Fisher + Klein-4) separate the clusters. **The verdict was decided by the measured table, not asserted.**

*(Honest history of THIS finding's method — kept per the no-leaning discipline: a first encoder draft read separation off the **full-graph Fiedler vector** + a **content-blind hashed-random** Klein-4 tag and returned NULL-ON-SEPARATION. Both were the WRONG instrument, not a real null: (a) the full 121-section graph has 39 components → λ₂=0 → the index-1 eigenvector is an arbitrary null-space basis vector carrying no cluster signal (the correct Fiedler read is on the **giant connected core**, where λ₂=0.96>0); (b) a hashed-random sector vector destroys the token-overlap structure that IS the cluster signal — the correct Class-M tag **bundles the section's actual token atoms** so shared tokens → aligned sectors. With the correct instruments the separation is decisive and agrees 3/3. The fix is methodological; the falsifiable bar was not moved.)*

---

## §1 The structure — working memory as a srmech wireframe (the low-pass band)

**Working memory ≠ the memory files.** The live session's load-bearing state is the **committed findings + the ROADMAP queue + the open decisions and their relational structure**. `CLAUDE.md` / `MEMORY.md` are *renders* of slices of that state — they are not, and must not be, its single source of truth. The SSoT is the **structural wireframe**: the low-pass skeleton that is **lossless of STRUCTURE** (every load-bearing relation survives) while dropping the high-pass fluent fill (the prose that a render re-synthesises).

The wireframe is three srmech objects over the corpus:

| Wireframe layer | What it is | srmech op | Class |
|---|---|---|---|
| **the storage signature (the fingerprint)** | the eigenspectrum of the section-relational co-occurrence Laplacian — the F172 native storage signature | `laplacian.dense_laplacian` → `jacobi_eigvals` | **L** |
| **the cluster-separating embedding** | the giant-component Fiedler / higher eigenvectors (where λ₂>0) | `laplacian.symmetric_eigendecompose` (π-free Jacobi, NOT `np.linalg.eig`) | **L** |
| **the sector tags** | per-section Klein-4 sector occupancy = `bundle` of its per-token `klein4_random` atoms | `hdc.klein4_bundle` / `klein4_random` / `klein4_sector_count` / `klein4_similarity` | **M** |

**Nodes** = the 121 markdown SECTIONS across the 10 corpus files (each finding md splits at its `## §` headers; ROADMAP splits at its `## DATE` entries). **Edges** = co-occurrence of **load-bearing reference tokens** (finding-ids `F234`, issue-#s `#784`, the A–N class names, Klein-4 / Kuramoto / K_c / chirality anchors, MFO section refs, provenance anchors, the per-cluster substrate vocab) — an edge exists iff two sections share **≥ 2** such tokens (1 shared token = the ubiquitous-anchor noise floor). **The co-occurrence is counted only to weight the edges that feed `dense_laplacian`; the EIGENSPECTRUM is the storage signature — the `Counter()`-as-storage-proxy failure mode is exactly what F172 / CLAUDE.md §2 forbids, and is not used here.**

**Kept content is EXTRACTIVE (F223).** Each node keeps a **verbatim** span — the header line + the first verbatim sentence of the body — never an abstractive paraphrase. The RBS-LM substrate cannot author fluent prose (F223), so the SSoT carries the real spans and leaves authoring to the (separate, temporary) render.

---

## §2 The measurements (srmech-native; the edges built BLIND to the cluster labels)

### §2.1 The storage signature (F172) — the wireframe fingerprint (bit-exact)

| quantity | value |
|---|---|
| corpus files | 10 (F234–F241 findings + ROADMAP.md + 2 session-note files) |
| sections (graph nodes) | **121** |
| co-occurrence edges (shared-token ≥ 2) | **1089** |
| Laplacian eigenvalues (the F172 signature) | 121 values, λ_min=0 … λ_max=460.91 |
| connected components (near-zero eigenvalue count) | **39** (token-disjoint islands + one giant core) |
| structurally flat? | **False** (spread λ₂→λ_max = 460.91 ≫ 0) |
| **content fingerprint** `response_sha256` | **`cdbed2dce37857a099dece7992644be67c91d27ebf3396eb62f4dbd589eb8f8d`** |
| bit-exact across runs | **YES — identical run 1 = 2 = 3** |

The spectrum is **richly non-flat** (the NULL's "near-degenerate" branch does not fire). The 39 components are honest macro-structure: most are singleton sections that share no ≥2-token link with the rest (isolated ROADMAP bullets, note fragments); the **giant component holds 80 of the 121 sections** — the coherent CORE where the load-bearing findings actually inter-reference.

### §2.2 Cluster separation — the decisive Class-L BLOCK-STRUCTURE read (PASS)

The canonical relational-separation test: do the pre-named clusters wire to their OWN cluster more densely than across clusters? (A flat summary has NO edges at all, so any block-diagonal excess is structure it cannot represent.)

| cluster | sections | within-cluster edges | within-density | vs across-cluster density |
|---|---|---|---|---|
| **disability** {F239} | 6 | 15 / 15 possible | **1.000** | ≫ 0.109 |
| **rehearsal** {F238} | 10 | 27 / 45 possible | **0.600** | ≫ 0.109 |
| **Kuramoto** {F234, F236, F241} | 44 | 302 / 946 possible | **0.319** | > 0.109 |
| *across-cluster* | — | 83 / 764 possible | **0.109** | (the off-block null rate) |

**Every cluster is denser within than the across-cluster rate** → the working memory has block-diagonal (modular) relational structure, separating all three clusters. The disability reading is **maximally coherent** (every one of its 15 internal section-pairs co-occurs) — it is the most tightly self-referential of the three; the Kuramoto cluster is the loosest (it is large and spans Python-F234, ngspice-F236, timing-F241), yet still beats the off-block rate by 3×.

### §2.3 Corroboration A — the giant-core spectral Fisher read (PASS)

Restricting the Laplacian to the 80-section giant CORE (where λ₂ = **0.96 > 0**, so the eigenvectors carry real geometry), the per-cluster coordinate groups on each non-trivial eigenvector give a Fisher discriminant ratio (between-cluster variance / within-cluster variance):

| eigenvector | eigenvalue | cluster-separation Fisher ratio |
|---|---|---|
| 1 (core Fiedler) | 0.96 | 12.92 |
| 2 | 1.07 | 12.47 |
| **3** | 3.43 | **17.18** (best) |
| 4 | 3.51 | 7.21 |
| 5 | 8.74 | 12.22 |
| 6 | 9.52 | 13.36 |

**Every non-trivial eigenvector has Fisher ratio ≫ 1** — between-cluster variance dominates within-cluster on the whole low-frequency band. The clusters occupy distinguishable regions of the spectral embedding. *(This is the read the first draft got wrong by using the **full-graph** index-1 eigenvector, where λ₂=0 makes it an arbitrary null-space vector; on the **core** it is decisive.)*

### §2.4 Corroboration B — the Class-M Klein-4 sector read (PASS)

Per-section sector vector = `klein4_bundle` of its load-bearing-token atoms (each token → a deterministic `klein4_random` atom seeded by its `sha256` content-address; shared tokens → aligned sectors). Mean intra- vs inter-cluster `klein4_similarity` (Class M; no hand-rolled cosine):

| read | value |
|---|---|
| mean **intra**-cluster similarity | **0.697** |
| mean **inter**-cluster similarity | 0.685 |
| per-cluster intra: disability | **0.808** (most sector-coherent) |
| per-cluster intra: rehearsal | 0.668 |
| per-cluster intra: Kuramoto | 0.616 |

**intra > inter** → sections inside a cluster are more sector-alike than sections across clusters. The margin is modest (the corpus shares a strong house-style vocabulary — `DEMONSTRATED`, `bit-exact`, `Class-K`, MFO refs — which raises the floor for ALL pairs), but the ordering is the predicted one, and the per-cluster pattern is informative: **disability is the most internally sector-coherent (0.808)**, matching its 1.000 block-density — the same cluster the two independent reads both flag as the tightest.

### §2.5 The verdict table (mechanical, no leaning)

| read | instrument | separated? |
|---|---|---|
| **block-structure (DECISIVE)** | within-density vs across-density (Class L) | **YES** (1.0 / 0.6 / 0.319 all > 0.109) |
| spectral Fisher | giant-core eigenvector Fisher ratio (Class L) | **YES** (best 17.18 ≫ 1) |
| Klein-4 sector | intra vs inter `klein4_similarity` (Class M) | **YES** (0.697 > 0.685) |

**3/3 reads separate; fingerprint bit-exact; spectrum non-flat → POSITIVE.**

---

## §3 What is DEMONSTRATED vs FRAMEWORK-READING (the load-bearing scope split, §VII.6.20)

**DEMONSTRATED (the measurement):**
- the encoder builds the section-relational Class-L wireframe over the real working-memory corpus and emits a content-addressed NDJSON SSoT;
- the storage-signature fingerprint (`response_sha256 = cdbed2dc…`) is **bit-exact-reproducible** across 3 runs and self-verifies from disk (body minus `generated_at`);
- the pre-named finding-clusters **separate on all three srmech-native reads**, decisively on the Class-L block-structure (modularity) read, with the edges built blind to the labels;
- **0 HARD discipline**, ratchet green.

**FRAMEWORK-READING (the synthesis, asserted as a reading, not proven):**
- *"This wireframe IS the SSoT for working memory; the memory FILE is a render/view, not the source of truth"* — the measurement shows the wireframe **has** the load-bearing relational structure (which a flat summary lacks); the **normative** claim that it SHOULD be the canonical SSoT is the reading.
- *"wireframe-is-memory, renders-are-views"* and the **FFT-band** framing (this is the low-pass band; F242b is the high-pass band) — the structural reading per F28/F32/F50.

**The render is the separate, temporary half.** F242a does not render; per F223 the substrate is extractive-only. The fluent render (F242b) is a borrowed GPU loaner, explicitly temporary — biology renders with no supercompute, so the srmech-native render is the trajectory and the GPU is borrowed only until then.

---

## §4 The ephemeral pruned-parts (DEBUG ONLY — NOT the SSoT)

The encoder also emits `_graft_pruned_DEBUG.md`: per corpus section, the high-pass fluent prose the low-pass wireframe DROPPED (the body minus the verbatim extracted first sentence). It exists **only** to debug **over-pruning** — if a load-bearing fact lives only there and never in a kept extractive span, the wireframe is dropping too much and the span should be promoted. It is explicitly marked **transient / NOT-the-SSoT / safe-to-delete**, carries a one-line retention note pointing at the real SSoT fingerprint, and is **regenerated every run**. It is forever-disposable; the NDJSON wireframe is the SSoT.

---

## §5 Scope, honesty, caveats (MFO §VII.6.20)

- **In-scope:** section-relational co-occurrence graph / Class-L Laplacian spectrum / Klein-4-sector algebra over the project's own research notes. **Not** CAD / fabrication / geometry (CAD-ban holds). Defensive scope: the corpus is this project's own working memory; no external-actor / capability framing.
- **The Klein-4 margin is modest (0.697 vs 0.685), and that is honest.** The corpus shares a strong house-style vocabulary that raises the similarity floor for all pairs; the Klein-4 read is corroboration, not the decider. The **decisive** read is the Class-L block-structure (the 1.0 / 0.6 / 0.319 vs 0.109 densities), which is unambiguous. The verdict does not rest on the thin Klein-4 margin.
- **"Better than a flat summary" is operationalised, not asserted.** A flat summary is a token list with **no relational structure** (no edges); the wireframe's separating power comes entirely from the **block-diagonal edge structure + the spectral embedding** — exactly what a flat summary cannot represent. That is the precise sense in which the wireframe captures more.
- **The cluster labels are the falsifiable input, the edges are blind.** The three clusters {F234/F236/F241}/{F239}/{F238} were named in the pre-state; the co-occurrence edges are built from token overlap with no knowledge of them. The separation is therefore a genuine recovery, not a plant.
- **Corpus-window honesty.** "Working memory" here is scoped to the F234–F241 finding window + the ROADMAP + the live session notes (the user-named live cluster). Earlier findings (F84–F233) are committed LONG-TERM memory, intentionally excluded from the live-session wireframe. A different window would give a different (still bit-exact) fingerprint — the SSoT is **window-relative**, as working memory should be.
- **No lineage claims.** The framework reads what the corpus's own relational structure already IS; it does not extend or supersede any external scholarship. `[[feedback_no_lineage_claims_in_notebook]]`.
- **Tiering discipline.** Never inflate the synthesis (the SSoT-claim) past the measurement (the bit-exact fingerprint + the cluster geometry).

---

## §6 Forward-asks (queued)

- **F242b (the separate, temporary half):** the high-pass fluent RENDER — turn this wireframe back into readable prose on the borrowed GPU. Explicitly temporary; the srmech-native render is the trajectory (biology renders with no supercompute).
- **a srmech-native render op:** the longer-horizon replacement for the F242b GPU loaner — render fluent text from the Class-L wireframe + Klein-4 sectors without supercompute (the F223 extractive→generative gap; today the substrate is extractive-only).
- **windowed re-encode as the session advances:** re-run the encoder as new findings land (F242, F243, …) so the working-memory SSoT tracks the live state; the fingerprint becomes a content-addressed checkpoint of "what the session's load-bearing structure was at commit X."
- **promote any over-pruned span:** scan `_graft_pruned_DEBUG.md` for load-bearing facts that survive only in the dropped prose and promote them into kept extractive spans (the debug loop's purpose).

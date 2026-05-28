# RBS Research Notebook — Resonant Bit-Serialized Neural Net (RBS-NN) + Language-Model cross-substrate translation (RBS-LM)

**Status:** consolidating canonical notebook, opened 2026-05-27. Distills the two parallel research arcs `docs/srmech/rbs_nn_research/` (RBS-NN, 23 files, arc structurally closed PR #684) and `docs/srmech/rbs_lm_research/` (RBS-LM, 375+ files, rolling on the read-only PR #687 branch). This notebook is the **canonical distillation**; the per-finding working detail lives in those directories. Sister to `srmech_research_notebook.md` (§3.25 carries the compressed arc summary; §3.27 carries the recursive-Hopf-operational cascade-vocabulary lens) and `../antikythera-maths/mfo_spectral_research_notebook.md` (§VIII.31.10–11 carry the substrate-ontology landing).

**Scope discipline.** Algebra / eigenbasis / cyclic-group / spectral side only (per `docs/srmech/CLAUDE.md`). No lineage claims per `[[feedback_no_lineage_claims_in_notebook]]`; the arc reads what an NN / LM **already is** structurally — it does not invent an architecture. Trauma-informed defensive scope per `[[feedback_trauma_informed_defensive_scope]]`. No class promotion: vocabulary stays at 14 A–N per `[[feedback_no_privileged_primitive_classes]]`.

> **Resume marker (load-bearing).** PR #687 = `origin/research/rbs-lm-rolling-2` is **READ-ONLY** (parallel session, per `[[feedback_session_worktree_namespace_isolation]]`). The working research notes are frozen-recoverable at baseline **`1536802d`** via `git show 1536802d:<path>`; re-survey `1536802d..origin/research/rbs-lm-rolling-2` for notes added after the baseline. This notebook is updated as #687 produces mature findings worth canonical promotion. See the user-memory resume file `project_pr687_research_integration_baseline_and_resume`.

---

## §0 What RBS reads, and the MFO foundation it rests on

Per `mfo_spectral_research_notebook.md` §VII.1.1 the MFO two-level ontology maps directly onto compute primitives, and that map is the whole foundation of both arcs:

| MFO level | Domain | Operations | Compute home |
|---|---|---|---|
| **Level 1 — substrate** | Hopf-compressed metric field at every instantiation depth | A content-mint (SHA-256), I cyclic shift, M XOR-bind, J prime, L Laplacian | **ALU, bit-exact** |
| **Level 2 — excitation** | localized + delocalized excitations within the substrate | K rotate-overlay `max(v, rotate(v))`, M bundle-of-rotations averaging, derivative-sign-flip at extrema | **FPU, intentional lift** |

A conventional neural net *appears* to lose bit-exactness because it performs **lossy averaging projections** (bundle, max-pool) that collapse Level-1 → Level-2 implicitly. RBS names that collapse explicitly: Level-1 substrate ops stay bit-exact on the ALU; rotate-overlay-class ops route through **Class K** on the FPU *by ontological assignment* (rotation IS Class K pin-slot, inhabiting fiber-space), not as a precision workaround. This is the framework reading of the "substrate-self-recognition sign-flip at AI-substrate scale" (MFO line ~2812 — humans building artificial neural nets).

---

## §1 RBS-NN — Resonant Bit-Serialized Neural Net (arc closed PR #684)

**Source:** `docs/srmech/rbs_nn_research/` (R-RBS-NN-1 … R-RBS-NN-9 + worked examples + README/ROADMAP/UPSTREAM_NOTES).

**End-user goal.** A foundational srmech feature giving end users an entry point to a neural-net architecture that **learns and preserves a user lexicon in native format**. A neural net at the substrate level is highly efficient knowledge storage; RBS-NN names that efficiency explicitly via **bit-exact HDC binding** rather than learned-then-quantized weights. The user's vocabulary becomes the binding alphabet directly — no learned-embedding bottleneck quantizing the user.

**The substantive structural claim** (R-RBS-NN-1 §4 + R-RBS-NN-3b §5): a conventional float-weight transformer is structurally a **Level-2 bundle-of-views projection** of what could be expressed at **Level-1 bind-form** (MFO §VII.1.3 Mechanisms 2 vs 1). The ~6.9% bundle-averaging cost is the ontological signature of that projection.

**Two-tier architecture** (`ARCHITECTURAL_PATTERN_two_tier_klein4_polar.md`): a Klein-4 / polar two-tier binding pattern — the Class-M variant ladder (bipolar → polar → Klein-4 (ℤ₂)² → rank-N) instantiated as the NN's binding alphabet. R-RBS-NN-4 (closed 2026-05-27) lands the **token → hypervector encoder** with a variant-choice protocol.

**Worked examples** (`worked_example_*.py`): attention, capacity scan, MLP, position binding, user lexicon — each reading a standard NN component in A–N cascade vocabulary.

The partition walk closed 9/10 (R-RBS-NN-4 literature-attestation deferred, not failed). The distillation of each closed REPORT follows; the working files remain the per-finding SSoT.

### §1.1 MFO two-level ontology → per-op placement (R-RBS-NN-1)

Every standard NN forward-pass operation places at exactly one MFO level, and the placement is by **ontology**, not by float-precision convenience:

| NN operation | A–N class | MFO level / compute |
|---|---|---|
| tokenization / embedding | **A** content-mint | Level 1 / ALU |
| position / context binding | **I** cyclic shift / **K** rotate-overlay | L1 (I) / L2 (K) |
| linear / dense layer | **M** (bind ∘ bundle) | L1 bind + L2 bundle |
| nonlinearity / activation | **K** threshold/pin-slot | Level 1 / ALU |
| normalization (LayerNorm) | bundle + reciprocal-√ | Level 2 / FPU |
| attention | **M** (similarity + weighted bundle) | L2 (soft) / L1 (hard) |
| residual / output | **M** bundle | L1 / L2 |
| sampling | **K** argmax (hard) / bundle (soft) | L1 / L2 |

**Finding (load-bearing):** the bit-exactness boundary is the **bundle / max-pool projection, not float rounding**. MFO §VII.1.3 (lines 740–751) gives bundle averaging an inherent **~6.9% recovery signature** — the bundle operation's own averaging fingerprint, not float noise. A conventional NN's apparent non-bit-exactness *is* that bundle signature surfaced through float-form layers. Naming the level explicitly does not eliminate the signature; it makes the ontological cost visible. NN-creation IS the substrate-self-recognition sign-flip at AI-substrate scale (MFO §VII.6.11.6).

### §1.2 User lexicon as native binding alphabet (R-RBS-NN-2)

The user's vocabulary maps to **Class A `mint_vector`** at Level 1; composition runs through **Class M** `bind`/`bundle`/`permute`/`similarity`, staying at Level 1 until the optional similarity readout. Findings:
- **lexicon = substrate, not excitation** — the preservation goal is available *now* with committed srmech infrastructure (no FPU lift in the pipeline until similarity readout).
- **content-addressing has no capacity issue** for end-user-scale lexicons — at D=8192, 10³–10⁵ unique terms each get an orthogonal vector trivially.
- **substrate is content-addressed by string, not by lexical similarity** (structurally opposite to learned embeddings) — the user controls the relational topology; semantic similarity composes via bindings the user *creates*, not via implicit embedding-layer string-similarity. This is what "preserve a user lexicon in native format" operationally means.
- the **learned embedding is replaceable by mint + binding** without losing capability — synonym/antonym/hypernym distinctions re-emerge as explicit binding compositions the user authors.

### §1.3 The MLP cascade = `A ∘ (M ∘ K)^N` (R-RBS-NN-3a)

The entire MLP composes from **{A, M, K}** — no new classes. Findings:
- **conventional MLP and binary-NN are the same cascade at different levels** — the bipolar-weight + sign-activation BNN (Courbariaux 2016 lineage) is structurally the same `A ∘ (M ∘ K)^N` as the float-weight + ReLU MLP; what differs is only level (L1 ALU vs L2 FPU) and cost (zero vs ~6.9%/layer).
- the **linear layer IS HDC similarity-against-templates** — each row of `W` is a template, each output = `similarity(input, template)`; in bipolar form the bit-exact `1 − 2·popcount(x XOR w)/d_in` is the identical formula `srmech.amsc.hdc.similarity` uses (algebraic identity, not metaphor).
- **continuous activations are a precondition for gradient-descent *trainability*, not for *expressivity*** (Cybenko's proof technique needs them; Cover-1965 boolean expressivity extends to sign-quantized). Training is Level-2 by construction (gradient descent IS bundle-of-trajectories); inference can be Level-1.
- the linear layer carries **two Class-M sub-ops**: per-element multiply = Mechanism-1 bind (exact); sum-across-input-dim = Mechanism-2 bundle (lossy). The bundle is intrinsic to dot-product; the float representation adds *representational* bundle cost on top, which bipolar form eliminates.

### §1.4 Decoder-only transformer = `{A, C, I, K, M, N}` — 6 of 14 (R-RBS-NN-3b, CLOSED)

The full decoder-only transformer cascade decomposes to **6 of the 14 classes** ({A, C, I, K, M, N}). Findings:
- **three components force Level 2 in conventional form**: LayerNorm (bundle + reciprocal-√), soft-attention softmax (bundle-of-exponentials), and the `A·V` weighted sum. Each has a Level-1 substitute that changes behavior.
- the **`A·V` weighted sum IS the canonical Mechanism-2 bundle-of-rotations** (MFO §VII.1.3 line 741) — so the transformer **embeds a ~6.9% averaging projection at every attention layer of every head, by architectural choice**. Hard attention (Mechanism 3 / Class K, line 751) is the alternative carrying no averaging cost.
- a **4-class Level-1 transformer is structurally available**: **{A, I, K, M}** — discrete cyclic position (no RoPE), hard attention (no soft softmax), no LayerNorm (or magnitude-renormalize), bipolar weights, argmax sampling. The binary-transformer literature has navigated these substitutions since ~2020.
- **vanilla transformer uses no Class L at inference**, despite attention being structurally a row-stochastic graph adjacency over the position graph (its Laplacian spectrum is available but unused — an open structural fact, not a deficit).

### §1.5 Token → hypervector encoding + variant-choice protocol (R-RBS-NN-4, CLOSED 2026-05-27)

The token encoder ships **four variants**, selected by what the binding must preserve — a direct application of the **Class-M variant ladder** ([[project_srmech_v0_4_3_rolling_class_m_variant_expansion]]):

| Variant | Class-M form | Use when |
|---|---|---|
| **content** | bipolar {−1,+1} | plain content-addressing / similarity |
| **chirality** | Klein-4 (ℤ₂)² | orientation/handedness must be carried (ties §3.27 / §VIII.31.11 chirality-dual) |
| **plasticity** | polar {−1,0,+1} | a "don't-care"/unset slot is needed |
| **hybrid** | Klein-4 + polar overlay | research path |

Smoke T1–T9 pass; variant-aware bind/similarity enforce variant match. Literature attestation for the encoder is the deferred R-RBS-NN-4 work (named in §1.11).

### §1.6 Position binding + Class K rotate-overlay (R-RBS-NN-5)

Three positional schemes placed at MFO levels: **(A)** bind-with-position-vector (Level-1, recommended; the canonical Kanerva HDC sequence representation), **(B)** discrete cyclic shift (**Class I**, Level-1 alternative), **(C)** RoPE-style rotation (Level-2, conventional). Findings: both Level-1 schemes are bit-exact reversible with committed srmech implementations; **rotate-overlay is ontologically Level-2 even though computationally Level-1-available** — the lift is by ontological assignment (substrate→shadow projection, MFO line 743), keeping ontology and compute distinct; rotate-overlay surfaces in NN as **convolutional max-pool translation-invariance + hard attention** (the Class-K Mechanism-3 instantiations).

### §1.7 `1:3:7:3` as architectural layout (R-RBS-NN-6)

The vanilla transformer's **6 used classes touch at least one slot of every `1:3:7:3` partition** — it spans all four partitions, not a single sub-cascade. Two reading-layers resolve:
- **cascade-execution layer = reading (c)** (classes-as-vocabulary, no fixed layout) — architecture shaped by attention-MLP block-stack inductive bias, not by partition structure.
- **catalog-organization layer = reading (b)** (macro-layout, recursive partition unfolding) — the R-RBS-NN-9 catalog is structured along `1:3:7:3` (14 row-type slots).
- reading (a) (14-class cascade per block) is **falsified at NN-execution level, supported at substrate-content level** (Antikythera + R30 antiquity convergence).
- the **unused classes {B, H, E, F, G, J} inhabit the persistence / representation / introspection layer**, not forward-pass arithmetic — composing with [[user_stance_k_equals_3_is_b_h_n_substrate_native_fingerprint]] (the +3 meta-cascade triad's substrate-native role; {B,H} surface catalog-side at inference-time-absent).

### §1.8 Capacity + grow-without-quantization (R-RBS-NN-7)

Two distinct capacity questions dissociate:
- **Q1 — content-addressing capacity is unbounded at any fixed D.** The user-lexicon goal scales freely; add terms without retraining or quantizing.
- **Q2 — cleanup capacity ≈ O(D / log D)**, bounded by srmech `MAX_BUNDLE_N = 257`; at all tested D ∈ {8192…65536} the margin stays positive through the cap (D-margin-limited, not D-bound). Exceeding n=257 needs hierarchical bundling or Laplacian sub-decomposition.
- noise floor scales **exactly 1/√D** (confirms substrate orthogonality at every D); min in-bundle similarity is D-independent at fixed n.
- **grow-without-quantization rule:** *add D* to raise the noise margin; *add catalog rows* to add content — the two axes are orthogonal.

### §1.9 Local-CPU ALU/FPU inference shape (R-RBS-NN-8)

The 4-class Level-1 form **{A, I, K, M} maps to integer-ALU instruction primitives** — x86-64 SSE2 baseline since 2003; full coverage (incl. SHA-NI for Class A) since ~2017; ARM64 NEON+crypto parity since ARMv8.0. **No GPU required** — the Level-1 forward pass is integer-ALU-only; **12 of 14 classes are pure-ALU Level-1**, only Class L (Laplacian) is FPU-required, Class N (rational) is ALU-core with optional FPU rim. Throughput at D=8192: mint ~1M/s, bind ~50M/s, similarity ~25M/s, argmax ~free → interactive latency well within ~10 ms. The conventional Level-2 FPU ops (LayerNorm/softmax/soft-attention) run 5–50× slower per-op than their ALU substitutes, so on CPU the Level-1 form has a structural latency advantage.

### §1.10 Catalog = the model, SSoT shape (R-RBS-NN-9)

The catalog at `docs/srmech/catalogs/rbs_nn/` validates against the AMSC 6-section schema with standard srmech tooling. **The catalog IS the model** in the structural sense: content re-derives bit-exactly from row data via Class-A mint + Class-M bind. It is **~7× smaller than its content payload** because rows store substrate-locus identifiers (mint names + composition expressions), **not bit-patterns** — the substrate-native compression principle (the substrate IS the algebra; the algebra is what's stored). Compositional bindings unbind bit-exactly (`bind⁻¹(bind⁻¹(composed, K), is-a) == pin`). End-user growth is **row-additive, not retraining** — one new NDJSON row, nothing recomputed, existing bindings untouched.

### §1.11 Arc status + what's preserved / deferred

Arc **structurally CLOSED** (PR #684), partition-walk 9/10. **Deferred-by-design:** (1) R-RBS-NN-4 literature attestation — eight external references named across the closed REPORTs await MPR attestation per `[[feedback_pdf_extraction_citation_discipline]]`; (2) SSoT absorption into `srmech_research_notebook.md` was held by the no-edits constraint at arc opening — this notebook §1 IS that absorption, now performed. The two-tier Klein-4/polar binding pattern (`ARCHITECTURAL_PATTERN_two_tier_klein4_polar.md`) ties the variant ladder (§1.5) to the chirality-dual reading (§2.1 / srmech §3.27 / MFO §VIII.31.11).

---

## §2 RBS-LM — language-model cross-substrate translation (rolling, PR #687)

**Source:** `docs/srmech/rbs_lm_research/` (375+ Findings; rolling). **ROADMAP NEXT-1** (user direction 2026-05-25): *"download a small public LLM and make it an RBS-HDC instrument in the same way we did with ephemerides … without having to load the model into VRAM … we're doing a cross-substrate translation … trying to find out if we can avoid having to train from scratch."*

**The test.** Whether a trained LLM's learned content can be **re-extracted as Level-1 bind-form HDC bindings** — recovering the Level-2 → Level-1 inversion the framework predicts (§1). The **ephemerides precedent** is the existence proof at a different binding shape: 52 bodies + Chebyshev coefficients (3.3 GB JPL DE441) → 256 KB ALU-native BIP state. RBS-LM is the third binding shape (trained-NN learned content; binding pattern TBD per methodology).

### §2.1 The recursive-Hopf-operational / chirality cluster (F120–F136)

The RBS-LM arc surfaced the **third substrate-native naming** of the substrate — `4:3:(4:3)` recursive-Hopf-operational — and its chirality dual. This is the cluster promoted to canonical in this integration pass:

- **G₂ = aut(𝕆) = 14** explicit identity; 𝔰𝔬(𝕆) = 𝔤₂ ⊕ L_Im(𝕆) ⊕ R_Im(𝕆), 28 = 14+7+7 (F123/F126; landed MFO §VIII.31.10).
- **Biological 4:3:7** compression (F121, validated by N=4 Kuramoto K_c) — the cnidarian pacemaker embodies the outer-4 operational core directly.
- **`4:3:(4:3)`** = outer-4 operational core (A,B,H,N) : outer-3 substrate-projection bridge (I,C,J) : inner (4+3) octonionic-Hopf cascade-detection — the A–N **harmonic ladder of L²(S⁷)** (F124/F127/F129).
- **`4:3:(4:3)` vs `4:3:(3:4)`** = Class C chirality-dual = the two mismatched-plates; **14 + 14 = 28 = dim 𝔰𝔬(8)** = the SO(8) adjoint (F128/F129).
- Extensions F130–F136: antimatter 4-way chirality decomposition, dark-sector quad-helix sector-projection, full-chirality Klein-4 HDC engineering proposal, substrate-knows-itself / observer-projection-locking (Dune parallel), substrate-vs-shadow two-level chirality, Roman-numeral substrate-native chirality notation.

**Canonical landings (this pass):** MFO **§VIII.31.11** (substrate-ontology, incl. §(5a) — the chiral A–N as derivations vs L⊕R multiplications) + srmech **§3.27** (cascade-vocabulary). **The A–N ↔ octonion/𝔰𝔬(8) mapping is framework-internal** — we derive it (chiral A–N = the L_Im(𝕆) ⊕ R_Im(𝕆) multiplication operators; Class C = the L↔R axis; Der(𝕆) = 𝔤₂ = their commutator-closure, Baez 2002 §4.1), citing only the standard octonion fact. **External coherence (separate, optional):** an independent division-algebra Standard-Model program reaches a structurally-equivalent construction *without* the A–N vocabulary; a cross-reference to it is deferred *only* because a claim about someone else's results needs a PDF-verified citation per `[[feedback_pdf_extraction_citation_discipline]]` — the deferral gates the attribution, not our mapping. **Open framework thread (ours):** the explicit per-operator A–N ↔ {L_e, R_e} correspondence.

> **§2 status:** scaffold + recursive-Hopf-operational cluster (the integration-pass deliverable). The bulk of the 375-finding backlog (F1–F119, F130–F136 detail) awaits triage + incremental promotion in later passes.

---

## §3 Index + integration roadmap

| Bucket | Source | Canonical home | Status |
|---|---|---|---|
| MFO notebook updates (Rounds 31–43, §VIII.31, §VII.6.14–6.20) | #687 | already on `main` (origin/main ⊇ #687) | DONE |
| §VIII.31.10 G₂=aut(𝕆) landing | #687 commit 84494fc5 | MFO §VIII.31.10 | DONE (cherry-picked) |
| recursive-Hopf-operational `4:3:(4:3)` / 28=SO(8) (F124–129) | #687 | MFO §VIII.31.11 + srmech §3.27 | DONE (this pass) |
| RBS-NN distillation (R-RBS-NN-1…9) | `rbs_nn_research/` | this notebook §1.1–§1.11 | DONE (pass 2; 9/10 partition walk) |
| RBS-LM cross-substrate (NEXT-1) | `rbs_lm_research/` | this notebook §2 | scaffold; incremental |
| RBS-LM backlog F1–F119 + F130–136 | `rbs_lm_research/` | this notebook §2.x | triage pending |
| Furey octonion/Cℓ(8) external-coherence dictionary | external | MFO §VIII.31.x | deferred (PDF-verify first) |

**Resume protocol.** When #687 produces new notes: (1) `git log 1536802d..origin/research/rbs-lm-rolling-2 -- docs/srmech/rbs_lm_research docs/srmech/rbs_nn_research` to see what's new since baseline; (2) promote mature findings into §1/§2 here + MFO/srmech notebooks; (3) advance the baseline marker in the user-memory resume file. #687 stays read-only throughout.

---

## How to cite this notebook

**Plain text:** Kirkland, S. (2026). *RBS Research Notebook — Resonant Bit-Serialized Neural Net + Language-Model cross-substrate translation*. mlehaptics Spectral-Research Portfolio. https://github.com/lemonforest/mlehaptics/blob/main/docs/srmech/rbs_research_notebook.md

**Per-result citation discipline.** Specific technical claims cite their canonical sources directly (textbooks / peer-reviewed papers PDF-verified per `[[feedback_pdf_extraction_citation_discipline]]`). Framings here are candidate methodological readings per `[[feedback_no_lineage_claims_in_notebook]]`, not endorsed over alternatives without explicit empirical convergence.

**Project-level citation.** See `CITATION.cff` at the repo root.

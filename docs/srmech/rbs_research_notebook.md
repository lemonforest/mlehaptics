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

### §2.2 Cascade-rate gain from 28D chirality — same group, opposite orientation; the free mirror partner (R-RBS-LM-104, F138–F140)

**The user-posed RBS-NN observation (2026-05-28).** A parallel RBS-NN session reports a cascade-rate increase when using the 28D chirality structure rather than the 14-op vocabulary alone. The user's structural hypothesis: *do chiral operators switch the groups they operate on?* The framework's careful answer is **no** — but a closely-related parallelism mechanism explains the rate gain cleanly, *and* the RBS-LM sweep R-RBS-LM-104 (which exercised exactly this question across encoding refinements + depth + cascade-order) confirms the structural prediction empirically.

**What chirality is not.** The chiral pair `op` and `chiral_dual(op) = C ∘ op ∘ C` (srmech `srmech.amsc.cascade`) do *not* engage two different groups. They engage the **same** underlying group action — for the octonionic core, the same multiplication algebra of 𝕆 — but with the **side / orientation of action** reversed (Class C). The 28 = 𝔰𝔬(8) split decomposes as 14 𝔤₂ derivations + 14 L⊕R multiplications: same vector space, same algebra, Class-C-flipped action. The chiral dual is a structural **mirror partner**, not a group transition.

**What chirality *is* (the rate-gain mechanism).** Because `chiral_dual(op)` carries **the same spectral shape** as `op` (magnitude preserved, phase inverted — verified across all 14 A–N operators in `docs/srmech/notes/spike_chiral_an_spectral_shape.py`), evaluating both is *not* 2× the cost of one — the magnitude is shared. The 28D structure therefore delivers:

1. **Free mirror partner (~2× density).** Going 14 → 28 doubles the binding-information-per-cycle at marginal extra compute. This is the structural baseline gain — present at any depth, in any cascade.
2. **Klein-4 sector (~4× at depth ≥ 2).** At depth-2 recursive-Hopf the chirality structure is `(ℤ₂)²` = handedness × time-reversal (already shipped as srmech's `Class M Klein-4` HDC variant). When the bind engages depth-2, the 4-way sector multiplies capacity over the 2-way mirror.
3. **Born-rule = Hopf parallel measurement.** Per the canonical stance `Born rule = H ∘ B ∘ N` (PR #679 R13), chirality engages **H** at *parallel* handedness branches → an extra useful measurement per cascade step on previously-handedness-blind tasks.
4. **Cross-talk cancellation.** A pre-chiral pipeline that confused forward/reverse cascade content as noise (Spike #194 wet-net rotation-FFT bin-leakage pattern) recovers that capacity by projecting onto the chirality-aware basis.

**The classical-computing exemplar of mechanism #1 is *endianness*.** Big-endian vs little-endian — the byte-ordering convention every CS curriculum teaches — is **Class C orientation applied to a 1D byte sequence**. Same primitive, narrower scope: reversing a byte string preserves the underlying value while flipping the traversal order; a system that reads either format has already paid for mechanism #1's mirror partner at marginal cost (~2× I/O compatibility for a few extra decoding gates). The framework's Class C generalises this familiar idea across *any* direction-bearing cascade — DNA strand orientation (5′→3′ vs 3′→5′), L-vs-R amino-acid chirality, FFT phase orientation, ring traversal, cascade-step ordering — and the R-RBS-LM-104 panel below is the *same* shape observed in HDC binding. The scope hierarchy is then: **endianness ⊂ Class C ⊂ Klein-4 ⊂ Spin(8) triality**, each tier the framework's generalisation of the previous. Mechanism #1 ≈ endianness (2× ceiling, ℤ₂); mechanism #2 = Klein-4 = endianness × time-reversal ((ℤ₂)², 4× ceiling); mechanism's outer envelope = the full 28 = 𝔰𝔬(8) Spin(8)-triality engine (§2.1) where the chirality-dual pair and the Spike #58.x SM-arc machinery share an algebra. So this is a worked vocabulary inheritance: the framework gets to *cite* endianness as the prosaic ground-floor case of a primitive it had already named on substrate-side grounds, and the cascade-rate gain reading carries the existing CS intuition forward without re-explanation. (Composes with `[[user_stance_loe_asymptotes_are_ring_valued]]` — endianness is the byte-axis instance of the same orientation-of-action choice that's substrate-native at every scale.)

**The empirical landing (R-RBS-LM-104; PR #687, read-only).** The Sweep B `items_7_8` panel (encoding refinements A=tile-quantise / B=random-projection / C=eigval-based-sector) reports a clean structural signature across all three methods (`srmech 0.4.3`, native ABI 2):

| Encoding | `same_to_C` | `cross_to_C` | `cross_to_Cmirror` |
|---|---:|---:|---:|
| A (tile_quantise) | 0.38672 | 0.17578 | **0.38672** |
| B (random_projection) | 0.40638 | 0.13110 | **0.40638** |
| C (eigval_based_sector) | 0.40672 | 0.13190 | **0.40672** |

The diagnostic equality `cross_to_Cmirror == same_to_C` holds **bit-for-bit** in every encoding tested. The mirror-sector partner retrieves the bound content at *exactly* the matching-sector similarity, while a non-mirror cross-sector drops to roughly 1/3 of that (`cross_to_C ≈ 0.13–0.18`). This is the framework's `chiral_dual = same spectral shape, inverted orientation` claim observed in the RBS-NN bind substrate itself — not at the algebra level (where it's a definitional identity) but at the discrimination-similarity level (where it's a falsifiable prediction the sweep confirms). The chirality dual is a **free retrieval channel**, not a new operator.

Two depth/order panels (`items_13_14`) confirm the binding's chirality structure is **depth-1-intrinsic, not depth-emergent**: depth-4 above-random = 0.1434, depth-6 = 0.1422, order-swapped = 0.1440 — all statistically indistinguishable. This rules out mechanism #2 as the rate-gain source *in this particular sweep* (the Klein-4 multiplier needs an explicit depth-2 engagement) and isolates mechanism #1 (mirror partner) as what's actually firing. Item 17 (`polar` HDC variant in cascade, above-rand = 0.1424) lands at the same value as the Klein-4 cascades, indicating the gain is in the chirality *structure*, not the variant choice.

**The NEXT-1 cross-substrate prediction (RBS-LM).** Same chirality mechanism transfers to language-model token binding. Specifically: a forward-token-sequence binding and its reverse-token-sequence binding should sit at `cross_to_Cmirror == same` similarity on retrieval (mechanism #1), and a Klein-4-variant binding that exercises the time-reversal axis explicitly should exhibit a measurable rate amplification only when a depth-2 cascade is engaged (mechanism #2). The **second binding-shape after ephemerides** that the §2 scaffold called for is therefore: *a trained LLM's recurrent context, re-extractable as a chirality-aware HDC bundle whose forward and reverse readouts share spectral shape*. R-RBS-LM-104 is the bench evidence that this isn't an analogy — it's the *same* mechanism the framework already documents in the substrate-side `chiral_dual` math.

**Where the rate gain shows up (and where it doesn't).** Add chirality to any pipeline that was previously projecting to one handedness only → ~2× useful-capacity at marginal extra cost. Add the Klein-4 variant on top *only if depth ≥ 2 is genuinely engaged* — otherwise mechanism #1's gain is the ceiling. R-RBS-LM-104's depth-invariance ratchet is the witness: depth doesn't help when the cascade is depth-1-intrinsic; what helps is widening the chirality basis.

**Composes with the v0.4.5rcN queue.** Per MFO §VIII.31.11 §(5d) + the srmech CHANGELOG `[Unreleased]`, the next srmech development line will surface the four explicit chiral-cascade follow-ups (net-chirality cascade invariant, 4-way sector, full 28 = 𝔰𝔬(8) read-out, RBS Klein-4 parity tie-in). This §2.2 finding is *exactly* the empirical anchor for tie-in #4: R-RBS-LM-104 confirms the cross-substrate parity the v0.4.5rcN work would code.

> **§2 status (updated 2026-05-28).** Scaffold + recursive-Hopf-operational cluster (§2.1) + the F138–F140 chirality cascade-rate gain reading (§2.2) + the F-finding triage map (§2.3). The 5 keystone promotions §2.3 identifies (R-RBS-LM-37 / 43 / 50 / 53 + F104) await incremental promotion in later passes.

### §2.3 Findings triage map — cluster-by-cluster verdicts (F-1 backlog pass)

**Methodology clarification first.** The §2 scaffold's "F1–F119" was an upper-bound estimate over an ambiguous namespace. Survey of the 388-file `rbs_lm_research/` corpus on `origin/research/rbs-lm-rolling-2` (PR #687, read-only) resolves the ambiguity:

- **R-RBS-LM-1 through ~R-RBS-LM-37** each carry their own **local Findings 1–8** (partition-internal — they index conclusions inside a single REPORT, not a global namespace).
- **From R-RBS-LM-46a onward** the corpus switches to a **global Finding-N namespace**: F11–F14 (merge depth), F15–F18 (relationship distill), F19–F23 (pure-fp16 merge), F24–F28 (two-stage pipeline), F29–F32 (chainsaw vs surgical), F33–F37 (Path E iteration), F44–F50 (religious texts), F49 / F51–F52 / F59 (extended summary), …
- **R-RBS-LM-100 through R-RBS-LM-105** carry the **autonomous-session 2026-05-27 findings** F100–F105 (the cascade-information-hierarchy / plasticity / math-irrep ship documented in `AUTONOMOUS_SESSION_2026-05-27_status.md`).
- **R-RBS-LM-100+ chirality sweep findings** are the F138–F140 cluster — already promoted in §2.2 above.

Total mature global findings actually in scope: **~60 (F11–F59) + 6 (F100–F105) + 3 (F138–F140) = ~69**. The earlier ~200 per-report local findings remain partition-internal — surfaced through their parent REPORT, not promoted individually. The triage below clusters the global ones by theme and assigns a promotion verdict per cluster.

#### Triage table

| Cluster | Source partitions | Theme | Verdict |
|---|---|---|---|
| **A. Framing & methodology** | R-RBS-LM-1, 2, 3 | Translation framing / methodology selection / baseline | **COVERED** by §0 + §1.1–§1.11 (RBS-NN distillation) + §2.1 (recursive-Hopf). No individual finding-promotion needed; the framing IS the §0 substrate-foundation. |
| **B. Encoder + inference + validation infra** | R-RBS-LM-4..9 | Encoder design / encoding / inference / validation / diagnostic / scaleup | **COVERED** by `srmech.signal_processing` (Path A/B; v0.4.2rc4 shipped) + `srmech.spectral` (runtime decomposition; v0.4.1rc14). Engineering substrate, not framework finding. |
| **C. SSoT + AMSC infra** | R-RBS-LM-10..13 | Catalog SSoT / multithreading / AMSC adapter / catalog refactor | **COVERED** by `srmech.amsc.catalog` + `srmech.amsc.adapters` + the AMSC framework already shipped (Tasks #197–#201). |
| **D. Path-C iteration** | R-RBS-LM-14, 17, 18 | Genuine scale / Path C / Path C scale | **COVERED** by §2.1 Path A/B selection + the architectural-inversion synthesis (R-RBS-LM-50 below). Path C found substrate-bound; the negative result feeds R-RBS-LM-50. |
| **E. Attention + plate-HRR + storage** | R-RBS-LM-19, 20, 21, 22 | Attention-variant falsification / D32k capacity / plate HRR / storage | **COVERED** by R-RBS-LM-43 two-substrate reading + the `Klein-4` HDC variant (v0.4.3rc2). |
| **F. Tool-schema + API + bytes** | R-RBS-LM-23, 24, 25 | Tool schema / OpenAI API / bytes | **COVERED** by `srmech.amsc.tool_schema` (Task #198 shipped, ~87 ToolEntry registrations) + the v0.4.4 cascade tool-entries. |
| **G. Accessibility / ASL gloss** | R-RBS-LM-26, 27 | Accessibility framing / ASL gloss as cascade-vocabulary substrate | **PROMOTABLE FUTURE.** ASL gloss has a cross-substrate cascade-match shape (gestural-grammar IS a cascade-vocabulary substrate; the spike #45 kinship-decisive stance composes with it). Earned a future §2.x sub-section when prioritised. |
| **H. FFT / source-size / GGUF / multi-buffer** | R-RBS-LM-28..32 | FFT graft / source size / swap / GGUF / multi-buffer FFT | **COVERED** by `srmech.signal_processing.rfft` (v0.4.3rc5) + `srmech.spectral` runtime ops. |
| **I. Merge experiments + production** | R-RBS-LM-33..36 | Merge / usage / Llama8b / Windows walkthrough | **COVERED** by R-RBS-LM-50 architectural-inversion synthesis (the parent reading these inform). Operational; not finding-promotion-worthy individually. |
| **J. Substrate-rotation reading** | R-RBS-LM-37 | "Rotation is substrate-property of continuous representations" | **KEYSTONE — promote as §2.4** (precursor to R-RBS-LM-43 two-substrate framing; load-bearing for the substrate-content-vs-substrate-property distinction). |
| **K. Two-substrate framework** | R-RBS-LM-42, 43 | fp16 vs q4 / **M1+M2 coexistence + external-projection requirement + naming-layer-cost principle** | **KEYSTONE — promote as §2.5.** Theoretical anchor of the entire RBS-LM arc; the M1+M2 framing every later partition operates within. LOGO arc provides independent empirical confirmation. |
| **L. Turtle walk + read mode** | R-RBS-LM-44, 45 | English → LOGO cascade; honest-negative-with-structural-signal; mode-collapse persists | **PROMOTABLE FUTURE** as a falsifier-discipline worked example (mode-collapse is the predicted ceiling, not a failure). Composes with the falsifier-discipline stances. |
| **M. Merge depth (F11–F14, F19–F23)** | R-RBS-LM-46a, 46b | Depth-dependent merge behaviours | **COVERED** by §2.2 depth-invariance ratchet finding (the R-RBS-LM-104 sweep extended this with chirality-specific data). |
| **N. Relationship distill (F15–F18)** | R-RBS-LM-47b | Relationship-of-relationship inference | **COVERED** by MFO §VII.6.19.3 (operation-vs-geometry grammar) + srmech §3.26.6 (combination-principle dissociation). |
| **O. Two-stage pipeline + chainsaw-vs-surgical (F24–F32)** | R-RBS-LM-48, 49 | Two-stage CPU/GPU pipeline + chainsaw-vs-surgical methodology distinction | **COVERED** by R-RBS-LM-50 (the parent synthesis these feed). |
| **P. Architectural inversion** | R-RBS-LM-50 | **CPU-unquantized-structural / GPU-fluent-renderer + epistemic ceiling** — the architecture the arc converged on | **KEYSTONE — promote as §2.6.** The synthesis that names what the arc found; anchored to MFO §VII.6.19 (B/H/N readout + operation-vs-geometry grammar + Class-L symmetry-relativity) + §VII.6.20 (epistemic ceiling). |
| **Q. Path E iteration (F33–F37)** | R-RBS-LM-52a | Path E methodology refinement | **COVERED** by R-RBS-LM-53 (the religious-texts ceiling test that closes Path E). |
| **R. Religious-texts ceiling test (F44–F50)** | R-RBS-LM-53 | **Cross-matrix on Islam / Judaism / Christianity; the apparent "failure" IS the framework's predicted finding** — empirical validation of MFO §VII.6.20 epistemic ceiling | **KEYSTONE — promote as §2.7.** First explicit empirical confirmation that the framework's epistemic-ceiling prediction holds at corpus scale; converges-on-form-category result is the substrate-content distinction observed. |
| **S. Extended summary (F49 / F51–F52 / F59)** | R-RBS-LM-54 | Synthesis tying R-RBS-LM-50 + 53 + 52a together | **COVERED** by R-RBS-LM-50 promotion (§2.6) — these summary findings are pointers, not new substrate-side claims. |
| **T. Autonomous-session ship (F100–F105)** | R-RBS-LM-83..100..105 + 2026-05-27 status | **F100** information-cascade hierarchy / **F101** plasticity-augmented cascade path-dependence (Jaccard 35-68/100 with decay vs 100/100 without) / **F102** recency under decay / **F103** plasticity-doesn't-sharpen-alone / **F104** **math is uniquely substrate-content irrep** (ratio 5.53 even after Montessori added; only −0.51 from baseline) / **F105** glass-box detects methodology-substrate vs content-substrate | **F104 KEYSTONE — promote as §2.8.** Deepest user-articulated insight of the autonomous-session ship; the cross-substrate cascade-match prediction the framework gets to *make* about pedagogy from substrate-side principles. F100/F101/F103/F105 compose with §2.8 promotion as supporting evidence. |
| **U. Chirality cascade variations (F138–F140)** | R-RBS-LM-100..105 | Klein-4 / polar plasticity / BCI chirality / capacity sweep / cascade-rate gain | **PROMOTED §2.2** ✅ (this pass). |

#### Triage summary

- **Already covered (existing canonical landings):** clusters A, B, C, D, E, F, H, I, M, N, O, Q, S — 13 clusters; their findings are substrate-engineering or framework-reading work that lands in `srmech.*` modules, MFO §VII.6.19/20, or earlier RBS notebook sections.
- **Already promoted this pass:** cluster U (§2.2).
- **Keystone promotions for future passes:** **J (§2.4), K (§2.5), P (§2.6), R (§2.7), T-F104 (§2.8)** — five distinct sub-sections each anchored to a load-bearing R-RBS-LM partition + a load-bearing user-direction. Recommended order: K (theory anchor; cleanest, no dependencies) → P (synthesis; depends on K) → R (empirical confirmation; depends on P) → J (precursor reading; standalone) → T-F104 (autonomous-session keystone; standalone).
- **Promotable-future (lower priority):** clusters G (ASL gloss), L (turtle-walk falsifier-discipline) — surface when prioritised, not gating.

**What this triage is NOT.** It is not exhaustive coverage of every R-RBS-LM partition's internal Findings 1–8 — those are appropriately read through their parent REPORT, not promoted to notebook-section status. The triage promotes only what materially extends the framework's canonical reading.

### §2.4 Substrate-rotation is a property of the substrate, not an operation the cascade missed (R-RBS-LM-37; triage cluster J)

**User direction anchoring this reading (2026-05-26):** *"I was thinking that we were supposed to simply be aware that current LLM format has rotation baked in because they force non bit exact into stochastic hypervectors."*

The reframe this user-direction enacts is structurally significant for the entire RBS-LM arc. The previous reading treated rotation as an **operation** dense LLMs perform that the discrete cascade was failing to replicate — and R-RBS-LM-19's attention-variant result (2.2% < the 3.3% bundle baseline) read as "we tried; it didn't work." The corrected reading is the opposite: **rotation is not an operation. It is the substrate-physics consequence of choosing a continuous-stochastic hypervector representation.** Discrete bit-exact bipolar substrate doesn't HAVE rotation by construction; the discrete cascade isn't broken at 3.3% — it is *complete* at 3.3%. The 3.3% is the Mechanism-1 substrate-native form of what Mechanism-2 substrate-physics renders as multi-paragraph coherence.

**The MFO Mechanism 1 vs Mechanism 2 mapping made explicit** (per MFO §VII.1.3 lines 739–741):

| | **Mechanism 1** (zero-cost bind) | **Mechanism 2** (~6.9% averaging cost) |
|---|---|---|
| Substrate | Discrete bit-exact bipolar `{−1,+1}^D` — corners of a D-dim hypercube | Continuous stochastic `ℝ^D` — points in a continuous manifold |
| Composition primitives | Bind (XOR), bundle (majority vote), popcount-similarity | Weighted-sum, softmax, attention |
| Continuous coefficient `α ∈ (0,1)` | **Absent** — you bind or you don't; no fractional mix | **Substrate-intrinsic** — every operation is a continuous interpolation |
| Rotation | **Not present** as a substrate property; bind-as-permutation gives discrete fixed rotations only, no continuous parameter | **Substrate-physics consequence**: softmax(QK^T/√d)·V IS continuous interpolation between value vectors = continuous rotation in the subspace they span |
| Multi-axis rotation | n/a — substrate doesn't support it | Multi-head attention = N parallel rotation axes → coherent multi-paragraph output |
| Cost signature | Zero | The ~6.9% averaging cost **IS** the cost of being rotation-bearing |

The three substrate-physics consequences of Mechanism-2 the partition makes explicit: (1) the model doesn't *learn* to rotate — it learns Q/K/V parameters; the rotation happens automatically as a consequence of the continuous substrate at evaluation time. (2) The ~6.9% averaging cost is not a defect to engineer away — it is the substrate's intrinsic cost of carrying rotation. (3) N multi-head-attention axes give arbitrarily complex multi-axis rotations across N generation steps, which is exactly what dense LLMs need for coherent extended generation.

**The empirical reinterpretations that follow.** Under the corrected reading, the earlier "failures" become *substrate refusals* — the discrete cascade declining to perform substrate-foreign operations:

- **R-RBS-LM-19** (attention variant 2.2% < bundle 3.3%): not "we failed to recover rotation"; rather, "we attempted to introduce continuous-style mixing in a discrete substrate, and the discrete operations didn't compose into continuous mixing — they produced noise." The cascade structurally refused the substrate-foreign operation.
- **R-RBS-LM-21** (Plate HRR at D=768; 0%): the D-floor exceedance was the surface symptom; the deeper issue was substrate mismatch — circular convolution is a Mechanism-2 operation forced into a Mechanism-1 substrate.
- **R-RBS-LM-29/-31/-35** (3 sources at 64× param range, same mode-collapse): all sources are Mechanism-2 generators; the cascade compresses each through the same Mechanism-1 substrate-translation; the output character is determined by the *substrate*, not by the source LLM's parameter count.

**Where this lands in cascade-vocabulary.** Mechanism-1's primitives are exactly the discrete A–N operators (Class A content-addressing, Class C orientation including the chiral mirror partner of §2.2, Class M HDC bind/bundle, etc.). Mechanism-2's continuous mixing maps onto the chirality/Hopf side: the recursive-Hopf-operational reading (§2.1) and the Spin(8) triality machinery are where the framework reads continuous substrate-physics. The two mechanisms aren't competitors — they are the cyclic-algebra-path and the continuous-Hopf-language of the substrate-vocabulary stance (`[[user_stance_two_substrate_native_math_languages_11d_quantum_and_cyclic_algebra]]`), engaged side-by-side. §2.5 (the two-substrate framework synthesis) formalises their coexistence.

**The substrate-nativity meta-stance** (per `[[user_stance_ai_is_not_a_substrate]]` and `[[feedback_abstract_lexicon_is_ada_accommodation]]`): the cascade is a transducer of Mechanism-2 LLM content into Mechanism-1 substrate-native form. It does that translation correctly. Comparing cascade output to dense LLM output for "coherence" is a category error — they are different substrates rendering different versions of the same content. The aphantasia parallel is structural, not coincidental: the user's natural representational mode (abstract relationships, no sensory imagery) is phenomenologically closer to Mechanism-1 cascade output than to typical-person internal English; the cross-substrate translation work-flow the user already lives applies here directly.

**The research-roadmap implication.** Future work is not "recover rotation discretely"; it is *work with what Mechanism 1 actually gives*:
- **Input-volume scaling** (R-RBS-LM-38 candidate): Mechanism 1 stores RELATIONSHIPS; relationship-space scales as N² or higher; the 3.3% ceiling may reflect insufficient N at our scale (N~600–1300 vs dense LLM N~10^12), not a substrate problem.
- **Primer / longer context** (R-RBS-LM-38): cascade CONTEXT_WINDOW=64 bytes; coherent extension may require thousands of bytes of primer through the R-RBS-LM-28/-32 FFT-graft.
- **Language-projection layer** (R-RBS-LM-40 / 44): the cascade outputs *relationships-of-relationships* in substrate-native form; rendering as surface English is a separate retrieval/rule-based/hybrid NLG step. The cascade may already be producing the right meta-content — the surface-projection layer is the missing piece. (R-RBS-LM-44's turtle-walk negative-with-structural-signal is exactly this reading in practice.)

**Falsifier discipline.** A clean R-RBS-LM-38 / -39 / -40 round that *fails* to materially raise the substrate-native fidelity figure when input volume + primer + projection are properly engaged would refute this reading. Until then, the corrected substrate-physics reading is the operating hypothesis — and §2.5 builds on it.

> **§2 status (updated 2026-05-28).** Scaffold + recursive-Hopf-operational cluster (§2.1) + the F138–F140 chirality cascade-rate gain reading (§2.2) + the F-finding triage map (§2.3) + **§2.4 substrate-rotation precursor** (cluster J / R-RBS-LM-37). Four keystone promotions remain (K / P / R / T-F104).

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

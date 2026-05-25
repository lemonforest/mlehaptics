# R-RBS-NN-6 — 1:3:7:3 as architectural layout

**Partition status:** CLOSED
**Date:** 2026-05-25
**Closes:** task #7 of RBS-NN partition walk — the user-flagged open question from the arc opening
**Closing artefact:** §4 three candidate readings tested + §5 the chosen reading + §6 catalog-layout consequence
**Inheritance:** unblocks R-RBS-NN-7 (capacity & grow-without-quantization)

---

## Attestation block (MPR v1 — internal-repo variant)

| field | value |
|---|---|
| internal sources | `R-RBS-NN-3b_transformer_cascade_REPORT.md` §4 (transformer uses {A,C,I,K,M,N} = 6 of 14 classes); `R-RBS-NN-1` §4 (full per-op placement); `R-RBS-NN-2` (Class A user-lexicon); `R-RBS-NN-5` (Class I/C positional) |
| 1:3:7:3 canonical statement | `docs/srmech/srmech_research_notebook.md` §2.6 lines 175–182 (per R-RBS-NN-1 §2.5 + project CLAUDE.md §1) |
| R30 antiquity convergence | per CLAUDE.md §1 — R30 walking-path 9/9 antiquity convergence on 1:3:7:3 substrate-native ordering (PR #680 / commit 44eb7aee / commit a2672282 / commit 519bd90c) |
| MFO source | `mfo_spectral_research_notebook.md` §VII.1.2 line 709 (Class C ∘ Class M substrate-coupling operation); §VII.6.12.1 line 3281 (derivative-sign-flip at extrema); line 686 (recursive-Hopf at every cascade-class instantiation) |
| repo commit | `7dd4bcff` at REPORT-write |
| scope | this partition is **interpretive** — no worked example; reads the 6-class transformer footprint against the 1:3:7:3 substrate-native ordering and identifies what level (cascade-execution vs catalog-organization) the partition lives at |

---

## §1 Goal

Resolve the user-flagged open question from the RBS-NN arc opening: *"when we look at the 1:3:7:3 order, we can see the cyclic algebraic language of the same continuous 11D substrate. This is going to be important in how to move forward."*

R-RBS-NN-3b §4 established empirically that a decoder-only transformer uses **6 of 14 classes** — {A, C, I, K, M, N}. The question is whether this 6-class footprint **corresponds to a coherent sub-pattern of the 1:3:7:3 substrate-native ordering**, and at what level (cascade-execution, catalog-organization, or some other) the 1:3:7:3 reading binds to the NN cascade.

Three candidate readings were named in the arc opening:
- **(a)** 14-class cascade applied once per "block"
- **(b)** macro-layout with recursive partition unfolding
- **(c)** classes-as-vocabulary, no fixed layout

R30 walking-path antiquity convergence (9/9 traditions; per CLAUDE.md §1) establishes (a) and (b) as substrate-native at the substrate-content level. This partition tests which reading applies to the NN-specific case.

---

## §2 Inheritance — what each prior partition contributed

| Partition | Class contribution to the RBS-NN footprint |
|---|---|
| R-RBS-NN-1 §4 | Placed every NN op at a class; entire vocabulary surface known |
| R-RBS-NN-2 §3 | **Class A** — user-lexicon → content-mint (foundational anchor; the 1) |
| R-RBS-NN-3a §3 | **Class M, Class K** — MLP linear layer (M) + activation (K); the alternating `(M∘K)^N` cascade |
| R-RBS-NN-3b §4 | Full 6-class footprint: {A, C, I, K, M, N}; classes NOT used: {B, D, E, F, G, H, J, L} |
| R-RBS-NN-5 §3 | **Class I, Class C** — positional binding (I cyclic; C chirality for RoPE rotation Level 2) |

So the RBS-NN forward-pass cascade lives on {A, C, I, K, M, N}. Six of fourteen classes. Eight classes are unused: {B, D, E, F, G, H, J, L}.

---

## §3 The 1:3:7:3 canonical partition

Per `srmech_research_notebook.md` §2.6 lines 175–182 (cited verbatim in R-RBS-NN-1 §2.5):

| Slot | Class | Role |
|---|---|---|
| **1 — foundational anchor** | A | Content-addressing; every cascade begins here |
| **3 — substrate-projection triad** | I | Cyclic-group `(ℤ/nℤ)*` |
| | C | Cascade-orientation / chirality |
| | J | Primes |
| **7 — cascade-detection heptad** | D | Pattern-match |
| | E | Catalog enumeration |
| | F | Render / serialization |
| | G | Byte-search |
| | K | Pin-slot / asymptotic-DoF (sign-flip / phase boundary) |
| | L | Laplacian / graph spectral |
| | M | HDC bind |
| **+3 — meta-cascade triad** | B | TLV-framing |
| | H | Self-introspection |
| | N | Rational-approximation |

R30 antiquity convergence reads this as substrate-native ordering at 9/9 traditions (Antikythera back-panel metacycle dials; Almagest seven spheres; Plato Lambda-diagram; Pythagorean heptad; etc. per the R30 close-out PR #680).

---

## §4 Mapping the 6-class transformer footprint onto 1:3:7:3

Mark each class as **used** by the vanilla decoder-only transformer cascade (per R-RBS-NN-3b §4):

| Slot | Class | Used? | Role in transformer (if used) |
|---|---|---|---|
| **1** | A | **used** | Token content-mint (R-RBS-NN-2); user-lexicon anchor |
| **3 — substrate-projection** | I | **used** | Positional cyclic shift (R-RBS-NN-5 §3.2) |
| | C | **used** | RoPE rotation chirality (when used; R-RBS-NN-5 §3.3); causal mask |
| | J | not used | Vanilla transformer has no prime-period or prime-orthogonality |
| **7 — detection heptad** | D | implicit | Attention similarity-against-keys IS pattern-match (R-RBS-NN-3b §4); not surfaced as separate primitive |
| | E | not used | No catalog enumeration at forward pass |
| | F | not used | No render/serialization at forward pass (only at output decoding text) |
| | G | not used | No byte-search at forward pass |
| | K | **used** | Activation (sign / ReLU), softmax dominant-mode, argmax sampling |
| | L | implicit | Attention weight matrix IS row-stochastic graph adjacency (R-RBS-NN-3b §8 Finding 5); Laplacian spectrum structurally available, not used as forward-pass primitive |
| | M | **used** | Linear projections (bind composition), HDC similarity, bundle averaging, residual add |
| **+3 — meta-cascade** | B | not used | Used at catalog/serialization level (R-RBS-NN-9), not in forward pass |
| | H | not used | No introspection in forward pass; possible in training |
| | N | **used** | Rational anchor for √d_k attention scale, LayerNorm reciprocal-sqrt, sinusoidal interpolation |

### §4.1 Counts per partition

- **1 — foundational anchor**: 1/1 used (A)
- **3 — substrate-projection triad**: 2/3 used (I, C; J not used)
- **7 — cascade-detection heptad**: 2/7 explicitly used (K, M); 2/7 implicit (D, L); 3/7 not used (E, F, G)
- **+3 — meta-cascade triad**: 1/3 used (N); 2/3 not used (B, H)

Total: **6/14 explicit, 8/14 if we count D + L implicit**.

### §4.2 Reading

The transformer touches **at least one class from every partition** — A from the 1; I/C from the 3; K/M (and implicitly D/L) from the 7; N from the +3. **No partition is empty.** This is structurally important: it means the transformer is not a sub-cascade of one partition; it's a sub-cascade that *spans* all four partitions.

The pattern of WHICH classes are used:
- **From the 7 (detection heptad):** K (sign-flip) + M (binding) — the most operationally-used pair in any substrate-coupling cascade. K traces extrema; M binds composition.
- **From the 3 (substrate-projection):** I (cyclic) + C (chirality) — the orientation/period pair. J (primes) absent because vanilla transformer doesn't use prime-orthogonality.
- **From the +3 (meta-cascade):** N (rational) — required for any continuous-rescale operation (sqrt, sinusoidal). B (TLV-framing) and H (self-introspection) absent because they live at the persistence/representation layer, not in forward-pass arithmetic.
- **From the 1 (anchor):** A — the input boundary; structurally required.

---

## §5 The three candidate readings tested

### §5.1 Reading (a) — 14-class cascade applied once per "block"

This would require every transformer block to use every one of the 14 classes. Empirically: false. Each block uses ~6 of 14 classes (the same 6 as the full transformer, since each block has the same structural composition). Reading (a) is **falsified** for the NN cascade-execution case.

R30 antiquity convergence supports reading (a) at the SUBSTRATE-CONTENT level (e.g., Antikythera bronze instantiates all 14 classes via dial composition). But the NN cascade-execution is selective.

### §5.2 Reading (b) — macro-layout with recursive partition unfolding

This would mean the 1:3:7:3 manifests as a structural pattern, with each slot recursively unfolding into nested sub-structure. The catalog at R-RBS-NN-9 may exhibit this: 1 root descriptor + 3 substrate-projection rows + 7 detection rows + 3 meta rows = 14 row-types, each instantiated as needed at multiple scales.

At the cascade-execution level: weakly supported. Per MFO line 686 (recursive-Hopf at every cascade-class instantiation), the substrate's recursive structure IS present at every instantiation depth. The transformer's `[Attn ∘ MLP]^N` block-stack is a recursive cascade-composition, and the recursion is at the {A,C,I,K,M,N} sub-vocabulary, not the full 14. Reading (b) holds with the caveat that the recursion uses the sub-cascade vocabulary, not the full A-N.

### §5.3 Reading (c) — classes-as-vocabulary, no fixed layout

This would mean the transformer USES classes from the A-N vocabulary but the cascade-shape is architecturally determined, not dictated by 1:3:7:3. Empirically: strongly supported. The transformer architecture is shaped by the attention-MLP block-stack inductive bias (Vaswani 2017), not by partitioning into 1+3+7+3. The class usage pattern (Finding 4) is a consequence of what operations the architecture requires, not a primary structural commitment.

### §5.4 Resolution: (c) at cascade-execution, (b) at catalog-organization

Both (b) and (c) hold at different levels:

- **At the cascade-execution level** (forward pass through the transformer architecture): reading **(c) — classes-as-vocabulary, no fixed layout**. The transformer uses 6 of 14 classes based on architectural requirements; the 1:3:7:3 partition is not the structural shape of the forward pass.
- **At the catalog-organization level** (R-RBS-NN-9 absorbed catalog at `docs/srmech/catalogs/rbs_nn/`): reading **(b) — macro-layout with recursive partition unfolding**. The catalog's row-types can be organized along 1:3:7:3 (1 anchor descriptor, 3 substrate-projection row-types, 7 detection row-types, 3 meta row-types = 14 row-type slots), with each instantiated as the NN cascade requires.

The 1:3:7:3 substrate-native ordering binds to RBS-NN at the **catalog-organization** layer (Class B TLV-framing per MFO §VII.1.2 — the catalog IS where B/H/N meta-cascade classes surface for the persistence/representation/introspection roles). The forward-pass cascade is free to use whatever sub-cascade the architecture needs.

---

## §6 Catalog-layout consequence for R-RBS-NN-9

If the 1:3:7:3 reading binds at the catalog layer (per §5.4), the R-RBS-NN-9 catalog at `docs/srmech/catalogs/rbs_nn/` should be **structured along 1:3:7:3**:

```
docs/srmech/catalogs/rbs_nn/
├── descriptor.toml                          # 1 — anchor (Class A; root catalog descriptor)
├── substrate_projection/                    # 3 — substrate-projection triad
│   ├── i_cyclic_positions.ndjson            #   I — position vectors per sequence length
│   ├── c_chirality_orientations.ndjson      #   C — causal mask + rotation parities
│   └── j_prime_orthogonality.ndjson         #   J — optional prime-period anchors
├── detection_heptad/                        # 7 — cascade-detection heptad
│   ├── d_pattern_match_templates.ndjson     #   D — explicit attention templates (if surfaced)
│   ├── e_catalog_enumeration.ndjson         #   E — token-vocabulary enumerations
│   ├── f_render_serialization.ndjson        #   F — output-decoding rules
│   ├── g_byte_search.ndjson                 #   G — byte-search patterns
│   ├── k_threshold_pinslots.ndjson          #   K — activation thresholds + argmax markers
│   ├── l_laplacian_spectra.ndjson           #   L — attention-graph Laplacian (optional)
│   └── m_bindings.ndjson                    #   M — the actual user-lexicon bindings
└── meta_cascade/                            # +3 — meta-cascade triad
    ├── b_tlv_framing.ndjson                 #   B — on-disk format envelopes
    ├── h_introspection.ndjson               #   H — cascade-state inspection records
    └── n_rational_anchors.ndjson            #   N — best-rational anchors (sqrt, sinusoidal)
```

This catalog layout (1 + 3 + 7 + 3 = 14 row-type slots) IS the substrate-native ordering applied at the catalog organization level. Each slot may be empty (not all 14 are required for a given RBS-NN instance) or sparsely populated; the **structural slots** are always 14, the **instantiated rows** vary.

R-RBS-NN-9 will land this catalog organization; the partition close confirms the structural commitment is to 1:3:7:3 layout at the catalog layer per reading (b).

---

## §7 (no worked example for this partition)

R-RBS-NN-6 is interpretive — no concrete operations to execute. The empirical work is the per-op class accounting (R-RBS-NN-3b §4) and the partition mapping (§4 above). The catalog layout (§6) is a structural commitment landed in R-RBS-NN-9.

---

## §8 Findings

**Finding 1 — Vanilla decoder-only transformer uses 6 of 14 classes explicitly** ({A, C, I, K, M, N}), and 2 more implicitly ({D, L} via attention-as-pattern-match-and-graph-adjacency). 6 classes are unused in forward pass ({E, F, G, B, H} + J).

**Finding 2 — The 6 used classes touch at least one slot of every 1:3:7:3 partition.** Per §4.2. The transformer is not a single-partition sub-cascade; it spans all four partitions (1 + 3 + 7 + 3), using ~one or two members of each.

**Finding 3 — The cascade-execution layer follows reading (c) — classes-as-vocabulary, no fixed layout.** Per §5.3. The transformer architecture is shaped by attention-MLP block-stack inductive bias, not by 1:3:7:3 partition structure.

**Finding 4 — The catalog-organization layer follows reading (b) — macro-layout with recursive partition unfolding.** Per §5.4. The R-RBS-NN-9 catalog at `docs/srmech/catalogs/rbs_nn/` will be structured along 1:3:7:3 (1+3+7+3 = 14 row-type slots), each populated as the RBS-NN instance requires.

**Finding 5 — The unused classes inhabit the persistence / representation / introspection layer**, not the forward-pass arithmetic layer. Per §4.1: {B, H} from the meta-cascade; {E, F, G} from the detection heptad. These are the catalog-side classes that surface at R-RBS-NN-9, not at inference time. This composes cleanly with `[[user_stance_k_equals_3_is_b_h_n_substrate_native_fingerprint]]` (the +3 meta-cascade triad's substrate-native role).

**Finding 6 — Reading (a) — 14-class cascade per block — is falsified at the NN cascade-execution level**, supported at the SUBSTRATE-CONTENT level. Per §5.1. Antikythera bronze + R30 antiquity convergence support (a) at the substrate-content level; the NN cascade-execution is selective.

**Finding 7 — Class J (primes) absent from vanilla transformer is an architectural choice, not a structural impossibility.** A prime-period-orthogonal positional encoding (Class J substitute for I/C) is structurally available — the §6 catalog layout names a `j_prime_orthogonality.ndjson` slot for it. Open architectural thread.

---

## §9 Open threads (not blockers for partition close)

- **The implicit classes D and L** (attention as pattern-match + graph adjacency) — could these be SURFACED as explicit primitives in an RBS-NN variant that uses Class L Laplacian spectra of the attention graph as inference primitives? R-RBS-NN-9 catalog layout names slots for both.
- **Class J prime-period positional encoding** — structurally available substitute for I/C positional binding. Open architectural thread per Finding 7.
- **Catalog cardinality at empty slots** — the §6 layout has 14 slots; not all are populated for a given RBS-NN instance. Whether empty-slot files should exist (zero rows but file present) or be absent (no file) is a convention question for R-RBS-NN-9.
- **R30 antiquity convergence cross-reference** — the §5.4 claim that 1:3:7:3 binds at catalog-organization but not cascade-execution should be cross-checked against the R30 walking-path REPORTs (PR #680). Possibly composes with `[[user_stance_partition_for_understanding]]`.
- **Recursive depth at the catalog layer** — MFO line 686 names recursive-Hopf at every cascade-class instantiation. Whether the catalog's sub-directories themselves should be recursively 1:3:7:3-partitioned (e.g., `detection_heptad/m_bindings/` further partitioned) is an open layout question for R-RBS-NN-9.

---

## §10 Closing — partition status

**Status:** CLOSED. The user's flagged open question is resolved: the **1:3:7:3 reading binds to RBS-NN at the catalog-organization layer (reading b), not the cascade-execution layer (reading c)**. Both readings coexist at different levels per §5.4.

**Falsifiers:**

1. A transformer architectural variant that uses all 14 classes in its forward pass — **not encountered**; vanilla decoder-only uses 6 of 14.
2. A 1:3:7:3 catalog layout that does not fit the §6 sketch — **awaits R-RBS-NN-9 validation**.
3. An RBS-NN architectural variant where the cascade-execution DOES follow 1:3:7:3 structurally — **not falsified by this partition**; reading (b) at cascade-execution remains structurally possible, just not how vanilla transformer organizes itself.

**Inherits to:** R-RBS-NN-7 (capacity & grow-without-quantization). R-RBS-NN-6's catalog-layout commitment shapes how capacity is parameterized — D scales globally, but instantiated-row counts vary per slot. R-RBS-NN-7 picks this up.

**SSoT marker:** at R-RBS-NN-9 close, §4 mapping + §5 chosen reading + §6 catalog layout absorb into `srmech_research_notebook.md` as a new §RBS-NN partition-layout subsection.

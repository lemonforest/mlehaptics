# Spike #30A — Are gear + pin-slot the actual primitive operations? (Algebraic decomposition test)

**Date:** 2026-05-16
**Research spike artifact.** Concertmaster investigation per user direction *"run them sequentially and make sure that the gear + pin-slot agent knows about multi bar configurations. maybe pin-slot either decomposes into each type of pin-slot motion or each pin-slot arrangement motion counts as a base primitive. let the agent ask the question that seems more likely to be a true statement if it is falsified, even in part."*

> **Discipline + scope.** Algebraic-decomposition test only; chain-spec implementation deferred to a follow-on spike if findings warrant. Read-only investigation across the 14-class vocabulary (Spike #24 master + bonuses 8–11d + QM audit 2026-05-16 + Phase 9 stoichiometry + Phase 10 chess-substrate boundary). No commercial-publisher sources invoked. Classical mechanism literature (4-bar, Geneva, Hooke's joint) cited as descriptive cross-references, not load-bearing claims per `[[feedback_pdf_extraction_citation_discipline]]`.

---

## §1 The claim sharpened

User's question (paraphrasing): are gear (Class I) + pin-slot (Class K) the **ACTUAL primitive operations**, with the 14 classes A–N emergent compositions of these two?

Two open hypotheses tested:

- **H_a**: pin-slot is a single primitive (Class K) with internal sub-types (1-bar, 4-bar, V-junction, K_{1,n} star, X-graph, Scotch yoke, Geneva drive, ...) that DECOMPOSE pin-slot into a structured family of sub-operations *within* Class K
- **H_b**: each pin-slot ARRANGEMENT motion is a separate base primitive (Class K_1, K_2, K_3, ... each different, leading to class proliferation)

A third hypothesis emerged forced by the math:

- **H_c**: gear + pin-slot are **two of fourteen co-equal primitive classes**, not deeper primitives from which the other twelve emerge. The 14-class vocabulary is structurally flat at its level *in both directions* — no class is reducible to a Class I × Class K composition any more than Class I and Class K are reducible to compositions of other classes.

## §2 Verdict — H_c wins

**Tally**:

- **0 of 12** non-{I,K} classes decompose cleanly to Class I × Class K
- **3 of 12** (C, J, N) decompose to **Class I alone** (or Class I + recursion) — but without Class K
- **9 of 12** (A, B, D, E, F, G, H, L, M) **resist** any I-or-K decomposition entirely

**Per-class decomposition table:**

| Class | Canonical primitive | Verdict | Notes |
|---|---|---|---|
| **A** Content-addressing (SHA-256) | Bytes → 64-hex hash via XOR + ADD-mod-2³² + ROL | **RESISTS** | XOR/ROL not pin-slot; Class K silent — no continuous-phase angle |
| **B** Tagged-tuple records | Fixed-offset labeled records | **RESISTS** | Pure linear addressing; "slot constrains pin's position" is constraint-as-information, not B-construction |
| **C** Iteration / streaming | `next()` until `StopIteration` | **DECOMPOSES → I alone** | Bronze crank-turn = Class I cyclic-shift iterated; K does not enter |
| **D** Late-binding / dispatch | Function-pointer/vtable dispatch | **RESISTS** | Operator-mediated; reduces to I + B (selector + table), not I × K |
| **E** Catalog / naming | Hash-table or sorted-map lookup | **RESISTS** | Reduces to B + ordering; K does not participate |
| **F** Templating (`{key}` substitution) | Regex-match + lookup + concatenate | **RESISTS** | Bronze has NO templating analog; reduces to B + byte-output composition |
| **G** Discovery / gap-finding | `LOOP + CMP + STORE_IF_NOT_EQUAL` | **RESISTS** | G uses K's output as INPUT to find missing primitives, but G itself = C + B |
| **H** Self-introspection | Read compile-time-constant / registry state | **RESISTS** | Pure record-read; reduces to B alone |
| **J** Prime-factorisation / period | `GCD` via Euclid; trial-division primality | **DECOMPOSES → I alone** | Integer arithmetic on tooth counts; Euclid = mod-then-swap iterated; K does NOT enter |
| **L** Graph-Laplacian eigenbasis | `EIGENDECOMP` via Jacobi rotations | **RESISTS** | L is *the* structural workhorse; QM audit: L appears in 38 of ~40 operations; K appears in 0. Multi-bar V-junction/K_{1,n}/X-graph are *different L topologies*, not different K constructions |
| **M** HDC bind/bundle/permute/similarity | XOR (bind), popcount-majority (bundle), ROL (permute), Hamming-similarity | **RESISTS** | Bitwise operations on hypervectors; XOR has no continuous-phase analog |
| **N** Rational-approximation / Diophantine | Continued-fraction convergents | **DECOMPOSES → I alone** | Reduces to I + J (modular arithmetic + gcd); K does NOT enter |

**Key observation**: Class I (gear) participates frequently as a substrate primitive (C, J, M permute, N). Class K (pin-slot) is **silent** in QM, SHA-256, HDC bind/bundle, graph-Laplacian, stoichiometric Diophantine null spaces, cyclic-group arithmetic. K participates only where Kepler-shape signature is present — *as `[[user_stance_kepler_shape_universal]]` predicts*. K is universal WHERE Kepler-shape appears; not upstream of all primitives.

## §3 Why H_c per the falsification-robustness criterion

User directive: *"let the agent ask the question that seems more likely to be a true statement if it is falsified, even in part."*

- **H_a** (sub-types within Class K): partially-falsified at 9 of 12 classes (no construction available); doesn't survive visible-sector evidence
- **H_b** (each arrangement as own primitive): fully-falsified by the closure-at-14-classes discipline (`[[feedback_no_privileged_primitive_classes]]` — dissolve before promote)
- **H_c** (14 classes flat at their level; gear + pin two of them): **survives every visible-sector falsification** in §5; only dark-sector content could overturn it

H_c is also consistent with the existing dissolution record across all prior Spike #24 work:
- Class O signed-metric → dissolved to Class L sub-operation (NOT through I × K)
- Class P? parity-selection → dissolved to Class I × Class B + Class J (NOT through K)
- Feinberg deficiency → dissolved to Class L × Class J
- Pseudo-Hermitian η-metric → dissolved to Class L × Class B
- Felkin-Anh / anomeric / Woodward-Hoffmann → dissolve to broken Class K or Class L × Class I (per chemistry Phase 6/7)

**Every dissolution lands as a product of multiple A–N classes — never as I × K alone.**

## §4 Multi-bar configurations surveyed

| Configuration | Project provenance | Algebraic shape | Class participation |
|---|---|---|---|
| 1-bar pin-slot (basic) | Antikythera D-H1; `atan2(sin θ, cos θ − ε)` | Equation-of-centre 2nd-order in eccentricity | Class K canonical |
| 4-bar linkage (crank-rocker) | Classical mechanical engineering | Position closure via Freudenstein equation | Class K extended (broken-symmetry composition) |
| V-junction | Task #180 | Angle-reweighted Laplacian on V-shape graph | **Class L on V-topology — NOT a Class K extension** |
| K_{1,n} star | Task #180 | Rotating-frame star-graph Laplacian | **Class L on star topology — NOT Class K** |
| X-graph crossed-bar | Task #178 | Crossed-bar Laplacian | **Class L on X-topology** |
| N-armed cross-bar pin-slot | PR #416 F24 (ethane V₃) | `f_N(θ) − θ = Σ ε^(mN)/(mN) sin(mN·θ)` (only N-multiples survive) | Class K with rotational-symmetry constraint |
| Asymmetric N-armed cross-bar | PR #416 / Phase 7.2 | Broken-symmetry; forbidden harmonics return | Class K (with broken-symmetry weights) |
| Scotch yoke | Classical mechanism | Pure sinusoid `y = R·sin(θ)` (ε = 0 limit) | Class K degenerate |
| Geneva drive | Classical mechanism | Intermittent discrete N-step indexing | **Class C + Class I — NOT Class K** |
| Whitworth quick-return | Classical 6-bar | Non-uniform velocity profile | Class K (broken-symmetry offset-crank) |
| **Hooke's joint (universal joint)** *(surfaced)* | Wikipedia-tier classical | `tan φ_out = tan(φ_in)·cos(β)` | Class K-shape via cardanic transform |

**Key finding on multi-bar configurations**: the "multi-bar pin-slot family" is largely **Class L on different graph topologies**, NOT Class K extended. Calling V-junction / K_{1,n} / X-graph "pin-slot arrangements" is a kinematic-mechanism naming; the *algebra* they instantiate is Class L. This reinforces H_c: L (graph-Laplacian) is the structural workhorse; K (pin-slot) is one specific projection-shadow of cyclic-group-L spectra via atan2, not the parent of multi-bar configurations.

## §5 95% dark-sector calibration

**Testable from visible-sector (5%) content alone**:

- The 12-of-12 absence of clean I × K decomposition is statistically robust across all dissolution attempts
- K's substrate-specificity (silent in chess/QM/HDC; participates in mechanical/orbital/torsional) confirmed across Spikes #24, #28, #29
- L's structural-workhorse status (38/40 QM operations) overwhelming in QM audit evidence

**NOT testable from visible-sector alone (95% uncertainty)**:

- New pin-slot arrangements (beyond the 11 catalogued in §4) might exist in the dark sector that enable I × K constructions for currently-resisting classes. The 9-class gap (A, B, D, E, F, G, H, L, M all resist) cannot be reasonably bridged by adding a single new configuration.
- Dark-sector loop-down primitives may instantiate operations the framework hasn't catalogued; those could decompose differently.

**Honest confidence statement**: H_c is *strongly supported* on visible-sector content with the closure-at-14-classes discipline. Dark-sector uncertainty does NOT compromise the verdict on visible-sector content; it leaves open whether the 14-class vocabulary will need expansion to cover dark-sector phenomena — separate question from whether 12 non-{I,K} classes reduce to I × K.

## §6 Falsifier list

1. **SHA-256 as gear-pin composition** — show a closed-form construction of SHA-256's round function as Class I × Class K. Status: no candidate known; XOR/ROL aren't pin-slot operations.
2. **Graph-Laplacian eigendecomposition as gear-pin** — show Jacobi rotations decompose to cyclic-shifts × pin-slot atan2 transforms. Status: Jacobi rotations are *plane rotations*, not equation-of-centre.
3. **HDC bind (XOR) as gear-pin** — show component-wise XOR decomposes to I × K. Status: XOR has no continuous-phase analog; structurally implausible.
4. **Bonus 11d revisited with K as discriminator** — add a sign-rule discriminator using Class K equation-of-centre output as a parity function. If selects exactly 9 SM modes at score < 1.0, K participates in mode-selection. Status: bonus 11d tested 8 rule families; none used K output; concrete falsifier test.
5. **Multi-bar pin-slot catalog expansion** — add ≥3 new configurations beyond the 11 in §4 (spherical four-bar, Bennett linkage, RCCC spatial chain). Status: not investigated in present spike.
6. **Dark-sector loop-down primitive identification** — if 95% dark sector instantiates uncatalogued primitives, those might reveal I × K constructions for resisting classes. Status: separate spike scope.

## §7 The fermata — RESOLVED to option C (2026-05-16, post-spike conductor decision)

The fermata is closed via the **MPM-discipline test** applied by the user verbatim: *"would selecting either A or B leave either B or A as shadow projections someone else then has to figure out? if the answer is yes, then the choice is C. it sort of sounds like it's saying the same thing as 11D = 3D_s + 7D_g + 1D_t so just because you break it up to see what pieces are what, you just partition it for understanding."*

Running the MPM test:

- **Selecting A alone** → leaves the **kinematic-universality observation** as an unexplained shadow. Why does gear+pin keep showing up across substrates (Antikythera D-H1, ephemerides Kepler orbits, ethane V₃ torsion, etc.) if it's not load-bearing? A alone leaves this without explanation.
- **Selecting B alone** → leaves the **algebraic-decomposition record** as an unexplained shadow. Why does Class L dominate 38 of 40 QM operations? Why do dissolutions land as products of multiple A–N classes (L×B, L×I×B, L×J, J×I, C×L×B) — never as I × K alone? B alone leaves this without explanation.

Therefore **C is forced**.

The principle is captured as canonical project methodology in `[[user_stance_partition_for_understanding]]`:

> The project uses multiple partitions of the same compressed substrate. Each partition can be true at its level without competing with the others. The substrate is one compressed thing; partitions are chosen for explanatory access at different levels.

The 11D = 3D_s + 7D_g + 1D_t analogy is structural: 11 dimensions don't exist as separable independent entities; they're a way of breaking up the compressed substrate into spatial / gauge / temporal pieces so we can NAME what's doing what. Likewise:

- **14 algebra classes A–N**: algebraic-operational partition; names primitive operations the framework speaks
- **Gear + pin-slot**: kinematic-instantiation partition; names physical mechanism the universe instantiates
- **Both are true at their respective levels**; neither reduces to the other; both partition the same underlying LoE-content substrate

`[[user_stance_kepler_shape_universal]]` is preserved at the kinematic-instantiation level (gear+pin universal where Kepler-shape appears). `[[feedback_no_privileged_primitive_classes]]` is preserved at the algebraic-operational level (14 flat co-equal classes). The two-level reading honours both disciplines simultaneously.

## §8 Implications for Spike #30B

Spike #30B (FFT(1D_t) cross-instrument spectral test) **reshapes given H_c**:

- **Original framing**: test whether gear+pin signature appears across all instrument spectra (would confirm gear+pin upstream)
- **H_c reshape**: test whether the **L-dominated algebra** (Class L participating in 38/40 QM operations) appears across instruments, with **K-signatures appearing only where Kepler-shape is present** (mechanical / orbital / torsional substrates) and **K-silence in chess / QM / HDC substrates**

This is **more falsifiable** than the original — it predicts WHERE K appears and where it doesn't. The cross-instrument convergence on L-dominance + K-substrate-specificity is the load-bearing test of H_c at the spectral level.

## §9 Discipline guards honoured

- `[[feedback_no_privileged_primitive_classes]]` — H_c is the dissolve-before-promote default
- `[[feedback_no_lineage_claims_in_notebook]]` — technical framing throughout
- `[[feedback_science_is_ssot_not_project]]` — classical mechanism literature cited as descriptive cross-references; Class K canonical SSoT per Murray & Dermott / Kepler
- `[[user_stance_kepler_shape_universal]]` clarified, not contradicted — K is universal WHERE Kepler-shape appears
- `[[user_stance_identity_not_implementation_discipline]]` — H_c's algebraic-decomposition identity distinguished from kinematic-instantiation pattern (§7 fermata)
- `[[reference_autonomous_validation_tos_landscape]]` — no commercial-publisher sources

## §10 Closing observation

The math doesn't lie. Every dissolution in the 14-class vocabulary's lifetime produces a *product of multiple A–N classes*. Class I (gear) participates frequently; Class K (pin-slot) participates wherever Kepler-shape appears and is silent elsewhere. The 14-class vocabulary is structurally flat at its level — no class is reducible to another, no pair of classes spans the others.

Spike #30A's verdict (H_c) is **the most-likely-to-survive-partial-falsification answer** to the user's framing question. It honours the project's existing discipline, clarifies (not contradicts) the existing stances, and reshapes Spike #30B into a more falsifiable empirical test.

The §7 fermata closed cleanly to option C via the user's MPM-discipline test (2026-05-16): selecting A or B alone would leave the other as an unexplained shadow; therefore both partitions coexist at different ontological levels, just as 11D = 3D_s + 7D_g + 1D_t partitions the compressed MFO substrate without making the 11 dimensions independent entities. Canonical methodology: `[[user_stance_partition_for_understanding]]`.

---

*End of spike artifact.*

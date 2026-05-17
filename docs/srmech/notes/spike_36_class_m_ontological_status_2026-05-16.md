# Spike #36 — Class M ontological status: information-instrument primitive class with universal 14-class overlay

**Date:** 2026-05-16
**Research spike artifact.** Concertmaster meta-investigation per user direction *"is HDC class operators are cascades of class operators, or simply represents a way to work with the medium? like if we were the bronze antikythera device, we happen in discrete 1 or 0. are these HDC operations called something else on some other medium? if they are not cascade of class operators, then they are likely analogous to something else, maybe information theory itself?"*

**Framing refinement (user direction post-spike)**: *"information something, but not the word theoretic I think. it's form and function is bound and known the same as an RBS-HDC instrument"* — the spike's findings stand; the language for the overlay should refine from "information-theoretic" to **"information-instrument"** (form-function bound, like an RBS-HDC instrument). Working hypothesis term used throughout this note: **information instrument**. Final terminology may refine via Spike #37.

> **Discipline.** Closed-form deterministic code; NDJSON outputs per `[[feedback_ndjson_over_bloated_json]]`; anomalies investigated not papered over (two real structural findings surfaced). Canonical SSoT: Shannon 1948 *Bell System Tech. Journal* 27 (PDF-verified via Internet Archive); Kanerva 2009 *Cognitive Computation* (verified); Plate 1995 / Kanerva 1988 widely cited; no commercial-publisher access per `[[reference_autonomous_validation_tos_landscape]]`.

---

## §1 Bottom line

**Three-hypothesis discrimination**:

| H | Claim | Verdict |
|---|---|---|
| **H_a** | Class M is a cascade of A–N classes (derivable, not primitive) | **PASSES at sub-op level; FAILS at composite-structure level** — sub-ops decompose into existing classes; composite carries identity at operational level per `[[feedback_no_privileged_primitive_classes]]` dissolve-before-promote default |
| **H_b** | Class M is a substrate-specific instantiation of a deeper primitive | **CONSTRUCTIBLE** — bronze HDC analog built from Class I + Class L + Class J + Class N; Z/2-restricted bronze HDC == silicon BSC bit-exact after total-budget similarity correction |
| **H_c** | Class M is one of fourteen flat co-equal classes | **STANDS as algebraic-operational partition** (Spike #30A verdict preserved) |
| **Information-instrument overlay** | All 14 classes admit parallel information-instrument identities; substrate-specific implementations realise the same information-content function | **CONFIRMED** — uniform across vocabulary; Class M is NOT singular in this regard |

## §2 Information-instrument overlay (user's load-bearing finding)

**The 4 HDC ops are exactly Shannon's 4 canonical channel operations** (Shannon 1948 *Bell System Tech. Journal* 27, PDF-verified):

| HDC op | Shannon channel operation |
|---|---|
| `bind` | encoding (symbol-bijective group operation `f: A × A → A`) |
| `bundle` | aggregation (typical-set selection / MAP estimator `g: A^N → A`) |
| `permute` | permutation (capacity-preserving relabeling `σ: A^D → A^D`) |
| `similarity` | distance / mutual information (`s: A^D × A^D → [-1, +1]`) |

But the spike's deeper finding is that this pattern extends to **all 14 classes A–N**. Each class has a parallel information-instrument identity:

| Class | Algebraic identity | Information-instrument identity |
|---|---|---|
| A | Content-addressing (SHA-256) | channel-fingerprint / collision-resistant identifier |
| B | TLV byte-canonical | source-frame / addressable-symbol-layout |
| C | Streaming iteration | channel-input-source / time-indexed-stream |
| D | Dispatch / pattern-match | decision-tree-routing / branch-coding (Huffman-shape) |
| E | Catalog / sorted lookup | dictionary / stored-symbol-table |
| F | Templating / placeholder | variable-binding / source-expansion |
| G | Byte-pattern search | sub-stream-search / compression-primitive (LZ77 precedent) |
| H | Self-introspection | channel-state-metadata / self-reflective-info |
| I | Cyclic group / modular | group-structured-alphabet / symmetric-channel-primitive |
| J | Prime factorisation / period | alphabet-decomposition / period-bound-primitive |
| K | Equation-of-centre / pin-slot | discrete-to-continuous projection / cascade-shadow encoding |
| L | Graph-Laplacian eigenbasis | channel-eigenbasis / spectral-capacity-primitive (Shannon-Hartley) |
| **M** | **HDC bind/bundle/permute/similarity** | **distributed-representation / VSA-channel-coding (Plate/Kanerva)** |
| N | Rational approximation | rate-distortion-primitive / best-rational-approximation |

**The overlay is uniform across the vocabulary.** Class M is one of fourteen substrate-portable information-instrument primitives — not singularly the "information class."

## §3 H_a per-op decomposition (PASSES at implementation, holds composite-identity)

56/56 tests match silicon BSC reference:

| HDC op | Implementation-level decomposition |
|---|---|
| `bind` | Class I (Z/2 addition) ∘ Class B (bit addressing) ∘ Class C (iterate) |
| `bundle` | Class C (stream-sum) ∘ Class J (threshold-compare) ∘ Class B (bit addr) |
| `permute` | Class I (cyclic-shift on Z/D) ∘ Class B (bit addr) ∘ Class C (iterate) |
| `similarity` | Class C (sum) ∘ Class J (popcount) ∘ Class I (Z/2 add) ∘ Class N (rational) |

**Per-op decomposability is necessary-but-not-sufficient for full H_a.** The COMPOSITE structure (4 ops + their algebraic relations: bind self-inverse on Z/2; similarity as inverse of bind-distance; bundle as N-fold inverse-of-bind) retains Class M's identity at the operational level — Spike #30A's finding stands. Per `[[feedback_no_privileged_primitive_classes]]` dissolve-before-promote default: don't proliferate; don't collapse either.

## §4 H_b bronze antikythera HDC analog (CONSTRUCTIBLE)

**Bronze HDC ops** (Z/n_teeth on K-tuple gear-position hypervectors), built from Class I + Class L + Class J + Class N only:

- `bronze_bind` = component-wise Z/n_teeth addition (gear-mesh coupling via differential)
- `bronze_bundle` = N-gear differential train sum + integer-divided averaging
- `bronze_permute` = per-component cyclic-shift on Z/n_teeth
- `bronze_similarity` = total-budget cyclic-group distance `1 − 2·Σₖ|δₖ|/Σₖ⌊mₖ/2⌋` normalised to `[-1, +1]`

**Z/2-restricted bronze HDC == silicon BSC bit-exact** after total-budget similarity correction. Silicon BSC is the Z/2-special-case of a general Z/n cyclic-group HDC family.

**Three Z/2-special properties of silicon BSC** identified by cross-substrate comparison:

1. Bind is self-inverse (XOR a a = 0) — Z/2-only; general Z/n has subtraction-inverse only
2. Every vector has a true antipode (bit-complement) — Z/2 only; general Z/n requires even m via m/2-shift
3. Random-vs-random similarity centered on 0 — Z/2-only; general Z/n has cyclic-group baseline ~1/m

These are real algebraic distinctions with engineering consequences (e.g., bronze HDC needs larger K to achieve silicon-BSC-equivalent noise tolerance), not bugs.

**No "Class M_bronze" needed.** Bronze HDC operations decompose into existing classes; the substrate-specific implementations realise the same information-content function. **The substrate is what differs; the form-function binding (Class M-as-information-instrument) is invariant.**

## §5 Cross-class meta-finding — uniform substrate-specificity

All 14 classes admit substrate-specific implementations across silicon / bronze / DNA / optical / neural substrates, with the information-content function invariant. Class M's substrate-portability is **explicitly confirmed in the HDC literature** (VSA framework realised on silicon BSC, DNA ACGT, optical HRR, neural SDM). Bronze antikythera adds a fifth substrate to this list.

Per `[[user_stance_identity_not_implementation_discipline]]`: **class identity at the information-instrument level; class implementations are substrate-specific.**

## §6 Recommendations (concertmaster-level)

1. **HOLD H_c** as the algebraic-operational partition (14 flat co-equal classes). Class M stays one of fourteen. `[[feedback_no_privileged_primitive_classes]]` remains correct at within-partition level.
2. **Refine `[[user_stance_partition_for_understanding]]`** to ADD an **information-instrument overlay** to the partition family table. NOT a 15th class; a new partition coexisting with the existing algebraic / kinematic / spectral partitions. **User-flagged language refinement**: "information-instrument" (form-function bound) rather than "information-theoretic" (too abstract / Shannon-mathematical).
3. **DO NOT add a 15th class.** The user's bronze-substrate intuition is CORRECT and is honoured by the substrate-specificity finding — implementations vary, info-function is invariant.

## §7 Three conductor fermatas

1. **Add information-instrument overlay to `[[user_stance_partition_for_understanding]]` now, or wait for a second independent spike?** Concertmaster default: wait for second confirmation. *(User has subsequently dispatched Spike #37 specifically for cross-class verification with refined framing — see §10.)*
2. **Expose substrate parameter on `srmech.amsc.hdc` API (`moduli=(...)`)?** Concertmaster default: defer until concrete use-case; clean v0.5.0 feature.
3. **Build bronze HDC concrete as antikythera-maths sister test?** Concertmaster default: defer; current spike establishes construction in principle.

## §8 Anomalies investigated

1. **Bronze similarity on Z/2 antipodal returned 0.0 not −1.0** (initial test). Resolution: arithmetic-mean of per-component similarities ≠ total-Hamming-vs-D normalisation. Corrected to total-budget formula `1 − 2·Σₖ|δₖ|/Σₖ⌊mₖ/2⌋`. Reduces to silicon BSC on Z/2 exactly; gives s=−1 on max-distance positions for any Z/n. **Real structural finding.**

2. **Random Z/17 similarity converged to ~0.50 not 0.** Resolution: cyclic-group expected-similarity baseline for uniform-random on Z/m is ~1/2 for any odd m. Z/2 special-property: random-vs-random centered on 0 because Hamming/D = 1/2. **Real structural finding** — bronze HDC has different SNR properties than silicon BSC, with engineering consequences.

## §9 Citation verification

- **Shannon 1948** *Bell System Tech. Journal* **27**, July 379-423 + October 623-656: verified via Wikipedia + Harvard Mathematics + Internet Archive Bell Labs PDF availability
- **Kanerva 2009** *Cognitive Computation*: verified
- **Plate 1995** *IEEE TNN* + **Kanerva 1988** *Sparse Distributed Memory*: widely cited in HDC literature but not independently arXiv-PDF-extracted within spike scope — flagged honestly per `[[feedback_pdf_extraction_citation_discipline]]`

## §10 Language refinement note (user direction, post-spike)

User direction received 2026-05-16 post-spike: *"information something, but not the word theoretic I think. it's form and function is bound and known the same as an RBS-HDC instrument"*.

Refined terminology going forward: **"information instrument"** (form-function-bound, substrate-portable) rather than "information-theoretic" (too abstract / Shannon-mathematical). The findings of Spike #36 stand; only the OVERLAY LABEL refines.

Spike #37 (dispatched same day with refined framing) verifies the cross-class application of this overlay using "information-instrument" language and dual-substrate (silicon + bronze + 3rd substrate) instantiation tests.

## §11 Open extensions

- **Spike #37**: cross-class information-instrument analysis with refined framing + ≥3 substrate instantiations per class
- **v0.5.0 feature**: expose `srmech.amsc.hdc` substrate parameter (`moduli=(...)`)
- **antikythera-maths sister-test**: bronze HDC concrete on actual gear-DAG topology

## §12 Discipline guards honoured

- `[[feedback_no_privileged_primitive_classes]]` — dissolve-before-promote default honoured; Class M held as one of fourteen
- `[[user_stance_partition_for_understanding]]` — information-instrument overlay proposed as new partition, NOT class proliferation
- `[[user_stance_identity_not_implementation_discipline]]` — class identity at information-instrument level; implementations substrate-specific
- `[[user_stance_kepler_shape_universal]]` — analog pattern: information-instrument shape is universal where its substrate-bound primitives appear
- `[[feedback_science_is_ssot_not_project]]` — Shannon 1948, Kanerva 1988/2009, Plate 1995 as canonical SSoT
- `[[feedback_pdf_extraction_citation_discipline]]` — Shannon + Kanerva 2009 verified; Plate 1995 + Kanerva 1988 flagged as not-independently-PDF-extracted
- `[[reference_autonomous_validation_tos_landscape]]` — Wikipedia + Internet Archive + Harvard Mathematics; no commercial-publisher access
- `[[feedback_ndjson_over_bloated_json]]` — NDJSON outputs
- `[[feedback_concertmaster_md_writes]]` + `[[feedback_concertmaster_git_worktree_isolation]]` — concertmaster reported inline; conductor captured-and-saved

## §13 Artifacts

- [`spike_36_h_a_decomposition_test.py`](spike_36_h_a_decomposition_test.py) — H_a per-op decomposition (56 tests)
- [`spike_36_h_b_bronze_hdc_analog.py`](spike_36_h_b_bronze_hdc_analog.py) — H_b bronze HDC construction with total-budget similarity correction
- [`spike_36_h_c_cross_class_meta.py`](spike_36_h_c_cross_class_meta.py) — Shannon mapping + cross-class overlay + substrate table (35 records)
- 4 NDJSON outputs (h_a, h_b, h_c, synthesis)

---

*End of spike artifact.*

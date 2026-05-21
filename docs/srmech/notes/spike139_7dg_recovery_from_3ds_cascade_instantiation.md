# Spike #139 — 7D_g Recovery From 3D_s Cascade Instantiation Cost Asymmetry

**Date**: 2026-05-18
**Branch**: `research/spike-139-7dg-recovery-from-3ds-cascade-instantiation`
**Parent stances**:
- `[[user_stance_identity_not_implementation_discipline]]`
- `[[user_stance_gr_observations_are_7dg_gauge_field_readouts]]`
- `[[user_stance_cascade_composition_is_quantum_algorithm]]`
- `[[user_stance_universal_precession_at_substrate_level]]`
- `[[feedback_no_privileged_primitive_classes]]` (vocabulary stays at 14)
- `[[feedback_no_mvp_framing]]` (full-coverage micro-benchmark)

**Composes with**: Spike #134 (AGN 7D_g↔3D_s coupling, PR #565), Spike #136 (quantum-computing-via-cascade), Spike #128.1 (Bell-CHSH bit-exact), Spike #128.2 (Deutsch-Jozsa MBQC), Spike #138 (proactive cascade exploration, in-flight).

---

## 1. Question

**User verbatim 2026-05-18**: *"launch a spike to see if we can recover knowledge about what happens in 7D_g when we do these operations in 3D_s. something about instantiating a particular cascade has inherent 7D_g content that 3D_s content mixed cascading slower? simply because we instantiate it in 3D_s"*

**Structural reading**: per `[[user_stance_identity_not_implementation_discipline]]`, framework cascades don't *compute* 7D_g content — they ARE 7D_g operations at identity level. When the cascade is instantiated on a classical 3D_s substrate (silicon CPU executing Python), the 3D_s "computation cost" is **substrate-coupling overhead**, not the cascade itself. Pure 7D_g algebra is timeless; 3D_s instantiation has finite cost because electrons must transit gates.

**Hypothesis**: cascades with stronger 7D_g content (Class L gauge-field readout, Class K asymptotic-DOF, Class C cascade-orientation, Class I cyclic-precession) should show characteristic 3D_s instantiation-cost signatures distinguishable from "3D_s-pure" cascades (information-theoretic-only: Class A SHA-256, Class B TLV, Class G byte-search, Class H introspection).

---

## 2. Framing — what is and is not being measured

### What IS being measured

- **3D_s instantiation cost** per class operation on identical-size input on identical hardware: CPU time (ns/op), normalised by output-bit-content where applicable.
- **Per-class cost asymmetry**: does the 14-class vocabulary show a non-uniform cost distribution that aligns with predicted 7D_g-content stratification?
- **Composition cost** (one pair): is composite cost super- vs sub-linear relative to component sum?

### What is NOT being measured

- 7D_g content itself is not directly measurable; we measure 3D_s readout shadows and *infer* substrate-coupling-cost asymmetries from those.
- Wall-clock cost is a **magnitude** (per `[[user_stance_framework_domain_algebra_not_length_or_magnitude]]`); algebraic identity claims live at the algebra level. Cost data is *magnitude shadow*, not algebra confirmation.
- This is NOT a falsification of cascade-IS-quantum-algorithm or identity-not-implementation claims; those are identity-level. This is a separate empirical question about whether magnitude data reveals systematic 7D_g-content correlates.

### Critical methodological cautions

- **Engineering confounds dominate at small scales**: Python interpreter overhead, function-call dispatch, cache locality, branch prediction, GIL effects, JIT (none here — CPython 3.14), allocator behaviour. These can swamp any "framework-significant" signal.
- **HAS_NATIVE = False** in this benchmark run: no `libsrmech` compiled in this worktree. All measurements are pure-Python fallback paths plus NumPy for Class L. This is acknowledged as a **bound on conclusions** — Spike #138 cross-stack signature would be the definitive test of substrate-coupling-cost-as-7D_g-shadow because that's where engineering noise should *not* fully explain class-asymmetry shifts.
- **Negative findings ship honestly** per `[[feedback_every_doc_edit_faces_falsification]]` + `[[feedback_no_mvp_framing]]`: if cost is engineering-mundane, the spike says so.

---

## 3. Predicted stratification (a priori, before data)

Per existing stance vocabulary:

### 3D_s-pure tier (information-theoretic only; predicted LOW per-bit cost)
| Class | Op | Reason it's 3D_s-pure |
|---|---|---|
| A | SHA-256 hash | Pure bit-mixing; no gauge-field algebra; FIPS 180-4 is byte-arithmetic only |
| B | TLV byte-canonical pack | Pure framing/header; no algebraic structure beyond concatenation |
| G | byte-search | Pure search; no group-theoretic content |
| H | introspection (version) | Pure constant return; no operation algebra |

### Mixed tier (some algebraic structure; predicted MIDDLE per-bit cost)
| Class | Op | Reason it's mixed |
|---|---|---|
| D | dispatch / multi-needle match | Pattern-matching = ad-hoc dispatch; mixes G's byte-search with selector logic |
| E | catalog (sorted-key lookup) | Binary search over key-space; some Class L-style ordering structure |
| F | template render | Substitution = limited cascade composition (lookup + concatenate) |
| J | prime factorisation | Pure integer algebra; arithmetic but NOT gauge-field |
| N | rational approximation | Continued-fraction algebra; integer-rational only |
| M | HDC bind/bundle | Tensor-product bind on bit-vectors; combinatorial information but pure XOR/majority |

### 7D_g-engaged tier (substrate-coupling; predicted HIGH per-bit cost)
| Class | Op | Reason it's 7D_g-engaged |
|---|---|---|
| C | cascade-orientation (NDJSON streaming iterator) | Iteration-driver of cascade composition; per Spike #136, Class C composes Gottesman-Knill simulator; gauge-field orientation per `[[user_stance_gauge_field_twist_shear_cascade]]` |
| I | cyclic / modular arithmetic | Universal-precession instantiation per `[[user_stance_universal_precession_at_substrate_level]]`; ℤ/n IS the substrate-cycle algebra |
| K | Kepler equation-of-centre | Asymptotic-DOF instantiation per `[[user_stance_epicycle_via_gear_plus_pin]]`; pin-slot IS Kepler-shape universal |
| L | graph-Laplacian / eigendecomposition | Direct 7D_g gauge-field readout per `[[user_stance_gr_observations_are_7dg_gauge_field_readouts]]` — Class L IS the spectral channel |

### Honest expectation

If the prediction stratification is correct: per-output-bit cost should rank roughly `A,B,G,H < D,E,F,J,M,N < C,I,K,L` (with Class L the highest because eigendecomposition has cubic Jacobi cost regardless).

**BUT**: most of that ranking is also predicted by standard algorithmic-complexity considerations (eigendecomposition is O(n^3), SHA-256 is O(n), Kepler-EoC is a 6-term polynomial). So the ranking *alone* does not discriminate framework-significant 7D_g signature from engineering-mundane complexity.

**The discriminative test**: do classes WITHIN a tier (e.g., all O(n) classes: A vs G vs I-`mod_pow` at small inputs) show systematic differences in cost/bit that align with the predicted tier? If so, framework-suggestive. If not, engineering-explained.

---

## 4. Empirical protocol

### Workload design

- Input sizes calibrated so each class processes ~1 KB equivalent of "work".
- Each operation is run for N=10,000 repetitions (with warmup) to amortise Python dispatch overhead.
- Mean ns/op and median ns/op reported; the spread is a confound indicator.
- Output-bit-content noted per operation (sometimes hash → 32 bytes; sometimes scalar → 8 bytes).

### Hardware / runtime

- Python 3.14.4 / CPython interpreter
- HAS_NATIVE = False (no compiled `libsrmech` available in worktree)
- NumPy 2.x available (Class L uses it for eigendecomposition)
- Single-threaded, no concurrent work
- Run on Windows 10 (the conductor's main development box)

### Falsifier definitions

Falsifier-A (cost-asymmetry-disappears): if standardising by output-bit-content equalises all classes within ±2× factor, **substrate-coupling-cost-is-engineering-mundane** verdict.

Falsifier-B (no-tier-ranking): if predicted-tier-ranking does NOT hold (e.g., Class A cost > Class L cost), **stratification-hypothesis-falsified**.

Falsifier-C (composition-is-linear): if L∘I composition cost equals L+I cost exactly (within 5%), **composition-shows-no-substrate-coupling-friction-or-compression**.

### Verdict possibilities (multi-component)

1. **7DG-CONTENT-SIGNATURE-EMPIRICALLY-DETECTABLE-VIA-COST-ASYMMETRY** — predicted ranking holds AND within-tier-asymmetry exceeds engineering explanation.
2. **COST-ASYMMETRY-EXPLAINED-BY-ENGINEERING-NOT-7DG** — predicted ranking holds but reducible to O() complexity + Python overhead.
3. **PARTIAL-SIGNATURE** — ranking holds for some classes, not others.
4. **FRAMEWORK-AGNOSTIC-AT-CURRENT-INSTRUMENTATION-PRECISION** — noise too high to discriminate.
5. **CROSS-STACK-SIGNATURE-PENDING** — needs Spike #138 triple-stack data (Python+C / Julia / C-native) for definitive answer; this spike provides Python-only single-stack baseline.

---

## 5. Anchored literature (PDF-verified)

1. **Aaronson, S., Gottesman, D. (2004)** — *Improved Simulation of Stabilizer Circuits*, [arXiv:quant-ph/0406196](https://arxiv.org/abs/quant-ph/0406196). Polynomial-time classical simulation of Clifford-only circuits; ParityL-complete. PDF-verified 2026-05-18.

2. **Huang, C., Newman, M., Szegedy, M. (2019)** — *Explicit lower bounds on strong simulation of quantum circuits in terms of T-gate count*, [arXiv:1902.04764](https://arxiv.org/abs/1902.04764). T-count below which classical simulation would beat 3-SAT. PDF-verified 2026-05-18.

3. **Bravyi, S., Browne, D., Calpin, P., Campbell, E., Gosset, D., Howard, M. (2019)** — *Simulation of quantum circuits by low-rank stabilizer decompositions*, [arXiv:1808.00128](https://arxiv.org/abs/1808.00128). Stabilizer-rank classical simulation; chi ~ 2^O(T-count). PDF-verified 2026-05-18.

4. **Xu, X., Benjamin, S., Sun, J., Yuan, X., Zhang, P. (2023)** — *A Herculean task: Classical simulation of quantum computers*, [arXiv:2302.08880](https://arxiv.org/abs/2302.08880). Review of state-vector and tensor-network paradigms. PDF-verified 2026-05-18.

5. **Landauer's principle (canonical)** — minimum thermodynamic cost of irreversible operation is k_B·T·ln(2) per bit-erasure. Practical Nvidia GPU FLOP cost (~10^−11 J) is ~10^8 above Landauer limit (~10^−19 J at 300 K) due to clocking, error correction, parallelism overhead. Cite-by-ref: Landauer 1961 *IBM J. Res. Dev.* 5:183.

### Framework-internal anchors

- Spike #136 (PR shipped 2026-05-18): cascade-IS-Gottesman-Knill at primitive level; T-count is the exponential boundary.
- Spike #134 (PR #565, 2026-05-18): AGN as 7D_g↔3D_s coupling; identity-not-implementation framing.
- Spike #128.1 (`srmech.qm.bell` shipped): Bell-CHSH bit-exact 2√2; 25 tests with timing data.

---

## 6. Methodology limitations

1. **HAS_NATIVE=False**: pure-Python fallback paths only. Per-class native C surfaces (libsrmech) would compress the absolute cost difference between classes; the *ranking* should hold but the *spread* would compress. Spike #138 cross-stack data is needed for the definitive answer.

2. **Single-process measurement**: no statistical aggregation over multiple machines, no temperature-controlled environment, no isolation from OS scheduler. Outlier-medians used to mitigate.

3. **No power measurement**: Landauer-level cost analysis not attempted (no instrumented thermistors, no joule-meters on this development box). Deferred to a future spike if needed.

4. **Workload normalisation is approximate**: "1 KB of work" means different things for an O(n) byte-stream vs an O(n^3) eigendecomposition on a 16×16 matrix vs an O(log p) modular exponentiation. We report multiple normalisations (per-call, per-input-byte, per-output-byte) and let the reader judge.

5. **One composition pair tested** (L∘I): a fuller compose-matrix would multiply combinatorially; out of scope for this spike. The L∘I pair is selected because both classes are predicted 7D_g-engaged.

---

## 7. Expected fermatas

- **Stance-authoring candidate**: if 7D_g-content-signature is detected at clear precision, candidate stance `user_stance_substrate_coupling_cost_is_7dg_shadow.md` becomes credible.
- **Book-chapter framing**: "Substrate-coupling-cost as 7D_g-content shadow" — empirical chapter joining Spike #136 (tractability boundary) and Spike #134 (AGN structural attestation) in the cascade-IS-7D_g triptych.
- **MS #14 BCI cross-link**: substrate-coupling-cost asymmetry at neural-substrate (per `[[user_stance_neural_hebbian_plasticity_substrate_match]]` from Spike #127.4) — if firmware-substrate shows same 7D_g-engaged ordering as silicon-substrate, that's universality evidence.
- **Spike #139.1 follow-up**: cross-stack with HAS_NATIVE=True for the same 14-class workload — composes with Spike #138 deliverables.

---

## 8. Disciplines applied

- No squash-merge per `[[feedback_no_squash_merges]]`
- PDF-extraction citation discipline per `[[feedback_pdf_extraction_citation_discipline]]`
- No lineage claims about external work per `[[feedback_no_lineage_claims_in_notebook]]`
- Algebra-not-magnitude **critical**: separate algebra-level identity claims from magnitude-level cost data
- Identity-not-implementation per `[[user_stance_identity_not_implementation_discipline]]`
- Zero new primitive classes per `[[feedback_no_privileged_primitive_classes]]` — vocabulary stays at 14 A–N
- Trauma-informed defensive scope per `[[feedback_trauma_informed_defensive_scope]]` — CPU-benchmark theoretical work; no defense adjacency
- Math-doesn't-lie: negative findings ship honestly
- Full-coverage shipping per `[[feedback_no_mvp_framing]]` — all 14 classes benchmarked, not a "quick subset"
- NDJSON output per `[[feedback_ndjson_over_bloated_json]]`

---

## 9. Deliverables

- This scoping doc (`spike139_7dg_recovery_from_3ds_cascade_instantiation.md`)
- Empirical benchmark script (`spike139_substrate_coupling_cost_benchmark.py`)
- Findings NDJSON (`spike139_findings_2026-05-18.ndjson`)
- PR returning verdict (per-class table + verdict per component + fermatas)

# srmech changelog

All notable changes to this package will be documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); this package uses semantic versioning.

## [Unreleased]

## [0.4.2rc5] - 2026-05-19

**Cumulative rc5 — TestPyPI verification of README v0.4.2 rewrite + numpy 2.x test compatibility + pyproject description refresh on top of the rc1-rc4 stack** per `[[feedback_rc_stacking_versioning]]` and `[[feedback_always_rc_first_for_downstream_publishes]]`. Graduation to production v0.4.2 is a SEPARATE follow-up PR once rc5 verifies on TestPyPI (fresh-venv install + README rendering check). No new primitive class introduced; 14-class A–N vocabulary intact per `[[feedback_no_privileged_primitive_classes]]`.

### Changed — `README.md` (PyPI long-description)

Full rewrite of the PyPI README for the v0.4.2 surface area. Navigable section structure with `srmech.amsc.*` (14-class primitive vocabulary) + `srmech.qm.*` (canonical QM/QFT/SM operations) + `srmech.spectral` (runtime spectral decomposition incl. MS #14 rcN+1+rcN+2 entries) + `srmech.signal_processing` (dual-path architecture) + AMSC provenance framework all surfaced as load-bearing. Internal project vocabulary scrubbed (cascade-match / substrate-natural / RBS-HDC-LoE / Spike #N anchors moved to the research notebook; public README cites canonical SSoT papers only).

### Fixed — `tests/` numpy 2.x compatibility

`log(0)` domain-check was emitting a `RuntimeWarning` under numpy 2.x (warning-promoted-to-error in pytest config); the test now uses `np.where`-guarded log to skip the zero entries cleanly. Version pin in `test_signal_processing_scaffolding.py` updated to `0.4.2rc5`.

### Changed — `pyproject.toml` / `pyproject-pure.toml` description

Description metadata refreshed to enumerate the five load-bearing surfaces (14-class primitives + canonical QM/QFT/SM + runtime spectral + dual-path signal processing + AMSC provenance). 488 chars, under the PyPI 512-char Summary cap per `[[reference_pypi_512_char_summary_limit]]`. Both pyproject files agree (publish-workflow guard `verify pyproject-pure.toml version + description match main`).

### Discipline

- Cumulative rc stack — rc1-rc4 content unchanged below + this rc5 layer.
- Production graduation v0.4.2 is gated by user direction after rc5 TestPyPI verification (fresh-venv install + README rendering check).

See `[0.4.2rc4]` below for the full Phase 1-4 ship narrative + `srmech.spectral.predict` / `prediction_error` / `truncate_sparse` rcN+2 entries + tool_schema registration.

## [0.4.2rc4] - 2026-05-19

**Phase 4 of the RBS-HDC-LoE dual-path architecture** — Path B per-op MVP. Ships 6 Path B-native signal-processing op modules (`fft`, `ifft`, `sign_quantise`, `matched_filter`, `wiener`, `hdc_truncation`) under `srmech.signal_processing.path_b_ops` per the implementation plan §6 Phase 4. Each op registers BOTH its Path A counterpart (from Phase 2 `closed_form_ops`) and its Path B implementation with `srmech.signal_processing.path_registry` at module-load time, giving the cascade dispatcher dual-path routing for the MVP roster. **No new primitive class introduced**; 14-class A–N vocabulary intact per `[[feedback_no_privileged_primitive_classes]]`. Identity-not-implementation discipline preserved per `[[user_stance_identity_not_implementation_discipline]]` — Path A and Path B IS the same algebra at D1 algebra-content (bit-exact on substrate-natural inputs per `[[feedback_algebra_not_magnitude]]`); D2 substrate-fingerprint divergence is expected per `[[user_stance_substrate_natural_encoding_is_shadow_projection]]`. Trauma-informed defensive scope per `[[feedback_trauma_informed_defensive_scope]]` — methodology-research / educational / civilian-comms framing only.

### Added — `srmech.signal_processing.path_b_ops`

New sub-package containing 6 Path B-native op modules:

- `path_b_ops.fft` — Class A ∘ Class I ∘ Class K cyclic-substrate FFT per Spike #176 H1 anchor (rotation IS Class K pin-slot at machine ε). Wraps the cyclic-DFT algebra with Class K cycle-order verification (Spike #176 T8). Path A counterpart: `closed_form_ops.fft.op` (numpy.fft.fft).
- `path_b_ops.ifft` — Class A ∘ Class I ∘ Class K dual of FFT per Spike #176 T4 anchor (recovery error = 0.0). Path A counterpart: `closed_form_ops.ifft.op` (newly added in this rc as the dual baseline).
- `path_b_ops.sign_quantise` — Class K ∘ Class M threshold/pin-slot projection per Spike #174 anchor (SHA-256 BER preservation at +20 dB SNR; structure-preserving denoising primitive). Path A counterpart: `closed_form_ops.sign_quantise.op`.
- `path_b_ops.matched_filter` — Class A ∘ Class C ∘ Class M form-function cross-correlation per Spike #159 anchor (within-vs-between separation ratio order-of-magnitude). Path A counterpart: `closed_form_ops.matched_filter.op` (numpy.correlate).
- `path_b_ops.wiener` — Class L ∘ Class N ∘ Class M Laplacian-eigenbasis + rational MMSE gain per Kay (1993) §11 SSoT + Chung (1997) §1.4 (cyclic-graph Laplacian eigenbasis IS the FFT basis). Path A counterpart: `closed_form_ops.wiener.op`.
- `path_b_ops.hdc_truncation` — Class K ∘ Class M ∘ Class N asymptotic-DOF sparse-truncate ∘ HDC bundle per Spike #117 anchor + Spike #179 T6 (bit-exact recovery at substrate-natural sparsity rate). Path A counterpart: `closed_form_ops.hdc_truncation.op`.
- `PATH_B_MVP_OPS` — canonical 6-op tuple in alphabetical order.
- Each module exports `OPERATION_NAME`, `CLASS_COMPOSITION` (14 A–N labels only), `PERFORMANCE_HINT`, `SSOT_CITATION` per the Phase 2 metadata schema.
- Each module registers BOTH Path A and Path B with `path_registry` at module-load time; the broader 38-op Path A registration script for Phase 2 remains separately deferred.

### Added — `srmech.signal_processing.closed_form_ops.ifft`

New Phase 2 module added to support the Path B IFFT dual. Closed-form `numpy.fft.ifft` wrapper; SSoT cited to Cooley & Tukey (1965) + Spike #176 T4 round-trip anchor. Listed in `closed_form_ops/__init__.py` alongside the existing 38 modules.

### Added — `tests/test_signal_processing_path_b_mvp.py`

Phase 4 dual-path acceptance suite — 33 tests across 6 ops:

- **6× metadata** — `OPERATION_NAME`, `CLASS_COMPOSITION`, `PERFORMANCE_HINT`, `SSOT_CITATION` present on every Path B module.
- **6× registration** — both Path A and Path B registered with `path_registry`; `has_path` returns True for both.
- **6× dispatcher routing** — `dispatch(op_name, path="B")` and `dispatch(op_name, path="A")` both succeed.
- **6× D1 algebra-identity equivalence** — Path A and Path B produce bit-exact (or machine-ε) equal outputs on substrate-natural inputs per `[[user_stance_identity_not_implementation_discipline]]`.
- **2× aggregate** — all 6 ops registered, CLASS_COMPOSITION restricted to 14 A–N alphabet.
- **4× spike anchors** — Spike #176 T4 round-trip (7 FFT lengths × 3 path combinations), Spike #174 SHA-256 BER preservation (+20 dB SNR), Spike #159 matched-filter separation order-of-magnitude, Spike #117 + Spike #179 T6 sparse-truncate substrate-natural sparsity.
- **2× routing semantics** — default-path-per-class routing (Class K → Path B; Class A → Path A); Phase 4 introduces no new classes.
- **1× ship guard** — Phase 4 ships exactly 6 ops per the plan.

### Phase 4 dispatcher coverage

After Phase 4 the registry holds **11 ops** total — Phase 3's 5 Path B core ops (`rbs_hdc_mint_class_operator`, `rbs_hdc_mint_cascade_composition`, `rbs_hdc_encode_loe_content`, `rbs_hdc_decode_loe_fingerprint`, `form_function_rotate`) plus Phase 4's 6 dual-path MVP ops (`fft`, `ifft`, `sign_quantise`, `matched_filter`, `wiener`, `hdc_truncation`). The 6 MVP ops are the only entries with both Path A and Path B registered; the cascade dispatcher in Phase 5 will exercise full A/B/verify routing across this dual-registered subset.

### Path B coverage notes

- Phase 4 does NOT register the 32 remaining Path A ops from Phase 2's `closed_form_ops` (per the brief: separate / deferred Path A registration script).
- Phase 4 does NOT implement `path="verify"` dual-execution mode — that's Phase 5 (`v0.4.2rc5`) per plan §6.5.
- Phase 4 does NOT add a C surface — C port for Phase 4 ops deferred to v0.4.3rc1 per conductor decision #1.
- Phase 4 does NOT implement Phase 8 profiling/learning — initial seed thresholds remain rule-based per plan §3.1.

### Added — `srmech.spectral` MS #14 rcN+2 entries (`predict` / `prediction_error` / `truncate_sparse`)

Per user direction 2026-05-19, the v0.4.2rc4 ship doubles as the **MS #14 rcN+2 vehicle**: the three runtime spectral operations previously listed as "deferred to rcN+2" in `[0.4.1rc14]` are now shipped in `srmech.spectral`:

- `predict(handle, laplacian, *, steps=1, dt=1.0, encoder_tag="default")` — **Class C ∘ Class L** cascade-extrapolate via per-mode complex-phase evolution `exp(-i·λ_k·steps·dt)` on the eigenbasis coefficients. The closed-form one-shot of a recurrent spectral predictor; matches Spike #113 predictive-coding-cascade anchor. Magnitudes preserved (unitary phase rotation); phase evolves per eigenmode. `steps=0` returns the input handle byte-exactly.
- `prediction_error(predicted, observed, *, threshold=0.0)` — **Class M ∘ Class K** XOR delta between predicted and observed coefficient byte vectors, gated by popcount-density `threshold`. Default `threshold=0.0` per user decision 2026-05-18 (no gating; returns raw delta). When `popcount(delta) / (8·len) <= threshold`, returns all-zero bytes (prediction sufficient).
- `truncate_sparse(handle, *, keep_k=None, threshold=None)` — **Class K** magnitude-band sparse-truncate; keeps top-`keep_k` modes by `|coeff|` OR every mode with `|coeff| >= threshold` (exactly one of the two must be provided), zeros the rest. SSoT: Mallat (2008) §9.2 (best k-term approximation) + Spike #117 anchor.

All three operations compose over the existing 14-class A–N primitive vocabulary per `[[feedback_no_privileged_primitive_classes]]`; **no new primitive class introduced**.

### Added — `tests/test_spectral_rcn_plus_2.py`

27-test acceptance suite covering predict / prediction_error / truncate_sparse:

- **TestPredict (8)**: handle returns, shape + descriptor preservation, `steps=0` identity, unitary magnitude preservation, non-trivial evolution on cycle-graph Laplacian, recompose-of-predicted roundtrip, content_sha corruption detected, descriptor_hash mismatch rejected.
- **TestPredictionError (7)**: `threshold=0.0` equivalent to `delta()`, zero delta on identical handles, threshold-above-density gates to all-zero, threshold-below-density returns raw, out-of-range threshold rejected, raw-bytes input path, predict-then-error roundtrip.
- **TestTruncateSparse (10)**: `keep_k=n` identity, `keep_k=0` zeros all, `keep_k=k` keeps highest-magnitude modes bit-exactly, threshold keeps above-floor, neither/both keyword rejected, out-of-range `keep_k` rejected, negative threshold rejected, corruption detected, recompose-after-truncate yields finite low-rank approximation.
- **TestShipGuard (2)**: all three callables present in `srmech.spectral` namespace; all three registered in tool_schema.

### Added — tool_schema registration for `srmech.spectral.*`

`srmech.amsc.tool_schema._register_spectral_runtime_tools()` (new) registers seven `srmech.spectral.*` callables — the four rcN+1 entries (`decompose` / `delta` / `recompose` / `similarity`) plus the three rcN+2 entries (`predict` / `prediction_error` / `truncate_sparse`). Closes the discipline gap identified by the concertmaster (rcN+2 must register at ship time, not deferred). Tool_schema entries include canonical-SSoT citations per `[[feedback_science_is_ssot_not_project]]` (Mallat 2008 §9.2 for `truncate_sparse`; Spike #113 + #117 anchors).

### Ship

Tag `srmech-v0.4.2rc4` → TestPyPI. Production PyPI publish on clean `srmech-v0.4.2` tag once TestPyPI rc4 verifies. **MS #14 rcN+2 deliverable** — closes Milestone #14 once `srmech-v0.4.2` lands on production PyPI.

## [0.4.2rc3] - 2026-05-19

**Phase 3 of the RBS-HDC-LoE dual-path architecture** — Path B core: `rbs_hdc_instrument.py` + `form_function_rotation.py`. Ports the Spike #170 R1 prototype (LoE-as-RBS-HDC instrument, FEASIBILITY-CONFIRMED at design level with 14/14 mint determinism) + Spike #176 (rotation IS Class K pin-slot, H1 CONFIRMED 6/6 tests at machine ε) + Spike #173 (chess natural-stride substrate, D2 orthogonality + bind-permute commutativity bit-exact) to a stable, composable Path B surface. **No new primitive class introduced**; 14-class A–N vocabulary intact per `[[feedback_no_privileged_primitive_classes]]`. Identity-not-implementation discipline preserved per `[[user_stance_identity_not_implementation_discipline]]` — Path B IS the same algebra as Path A (just substrate-projection differs); bit-exact algebraic identity preserved at D1 algebra-content level per `[[feedback_algebra_not_magnitude]]`. Trauma-informed defensive scope per `[[feedback_trauma_informed_defensive_scope]]` — methodology-research / educational / civilian-comms framing only.

### Added — `srmech.signal_processing.rbs_hdc_instrument`

Path B core: LoE-as-bound-vector RBS-HDC instrument at locked D=8192 (conductor decision #6, 2026-05-19).

- `RBSHDCInstrument` — composed instrument dataclass with `.build(D=...)` classmethod constructor. D defaults to 8192; optional D override accepted (in [D_MIN, D_MAX] multiple of 8).
- `mint_class_operator(class_name, *, D=8192)` — Class A SHA-256 chain mint of one of the 14 A-N class operator vectors. Deterministic: same `class_name` ⇒ same vector (Spike #170 §3 invariant 1: 14/14 bit-exact). Canonical name is `f"LoE.class.{class_letter}.{short_role}"`.
- `mint_cascade_composition(classes, *, D=8192, ordered=False)` — XOR-bundle of class operator vectors. Two modes: algebra-level (commutative bind; cascade-as-identity) and sampling-level (per-position permute by `i * 257`; cascade-shape preserved). Both modes per `[[user_stance_cascade_dual_level_quantum_at_algebra_classical_at_sampling]]`.
- `mint_stance_fingerprint(content_tokens, *, D=8192)` — Bag-HDC XOR-fold of token vectors per Spike #147 holographic-projection.
- `encode_loe_content(content, *, D=8192, substrate="default")` — Full Mode-B encoding pipeline: Class A content-addressed mint → Class C content-determined stride permute → Class M bundle with substrate anchor vector. Same content + same substrate ⇒ same fingerprint; same content + different substrates produces orthogonal D2 fingerprints at noise floor per Spike #173 R3.
- `decode_loe_fingerprint(fingerprint, catalog)` — Reverse-decode via Class M similarity argmax (Spike #170 §3 invariants 6 + 7: 100% reverse-decode accuracy on populated catalog).
- `mint_vector(name, *, D=8192)` — Underlying SHA-256-chain primitive (Class A content-addressing). Used by all higher-level mint operations.
- Module-level dataclasses: `ClassOperator`, `Cascade`, `Stance`, `MemorySlot`, `K3Tripartition`.
- Module-level catalogs: `CLASS_NAMES` (14 A-N), `CLASS_DEFINITIONS` (14 entries), `CANONICAL_CASCADES` (10 cascades including pin-slot-resonate music-box and cyclic-fft-rotation), `SAMPLE_STANCES` (12 stance entries), `MEMORY_PATHWAYS` (4 pathways: procedural / semantic / WM / episodic-LTM), `K3_TRIPARTITION_DEFAULT` (A → 3D_s, M → 7D_g, K → 1D_t).
- Constants: `PERMUTE_ORDER_STRIDE = 257` (coprime to D=8192=2^13 for ordered cascade composition).

### Added — `srmech.signal_processing.form_function_rotation`

Path B core: operational Class A ∘ Class C ∘ Class M rotation per `[[user_stance_form_function_rotation_is_a_c_m_composition]]` + `[[user_stance_rotation_is_class_k_pin_slot]]` (Spike #176).

- `form_function_rotate(content, *, D=8192, stride=None)` — Cyclic permute of `content` by content-determined stride (Class A SHA-256[0:8] little-endian mod D when `stride=None`) or by explicit substrate-natural stride (Class N rational). Supports chess natural strides {5, 7, -8} (Spike #173) and DNA helical pitches {21, 11, -12} (Spike #172).
- `inverse_form_function_rotate(rotated, *, D=8192, stride)` — Bit-exact reverse via `M.permute` with negated stride. Spike #176 T4 anchor: recovery error = 0.0.
- `verify_rotation_class_n_cycle_order(stride, D=8192)` — Class N additive order in Z/D = D / gcd(|stride|, D); cumulative shift `stride * order mod D == 0`. Spike #176 T8 anchor.
- `cascade_compose_rotations(strides, *, D=8192)` — Returns (composed_stride_mod_D, fundamental-mode unit-circle eigenvalue). Per `[[user_stance_cascade_lives_on_circles]]` (Spike #24 bonus 9 + Spike #176 T5): unit-circle identity at machine ε (residual ≤ 2.2e-16).
- `compute_content_stride(content, *, D=8192)` — Class A content-addressing primitive producing rotation stride.

### Path B core dispatcher registration

The two modules register their public operations with `srmech.signal_processing.path_registry` at module-load time (Phase 5 dispatcher reads from registry). Phase 3 registers 5 Path B core ops:

- `rbs_hdc_mint_class_operator` (Path B) — classes ("A", "M")
- `rbs_hdc_mint_cascade_composition` (Path B) — classes ("A", "C", "M")
- `rbs_hdc_encode_loe_content` (Path B) — classes ("A", "C", "M")
- `rbs_hdc_decode_loe_fingerprint` (Path B) — classes ("M",)
- `form_function_rotate` (Path B) — classes ("A", "C", "M")

Path A registration for the 38 closed-form ops from Phase 2 + Path A `form_function_rotate` is deferred to a separate conductor-written registration script per Phase 2's recommendation.

### Added — `tests/test_signal_processing_path_b_core.py`

Phase 3 acceptance suite porting load-bearing invariants from the spike prototypes:

- **T1**: `RBSHDCInstrument` D=8192 default + optional D override (256 / 1024 / 2048 / 16384 tested).
- **T2**: `mint_class_operator` determinism (same input ⇒ same output; 14/14 bit-exact per Spike #170 §3 invariant 1).
- **T3**: Cascade composition bit-exact — XOR-bundle commutativity (algebra-level, 3 orderings equal per Spike #170 §3 invariant 4); ordered mode breaks commutativity (Spike #170 §3 invariant 5).
- **T4**: Form-function rotation bit-exact reverse — Spike #176 T4 recovery error = 0.0 (content-determined stride + chess natural strides {5, 7, -8} + DNA pitches {21, 11, -12}).
- **T5**: Class N rational cycle order = D / gcd(stride, D) per Spike #176 T8; applying rotation `order` times returns to identity bit-exact.
- **T6**: Cascade composition unit-circle eigenvalues at machine ε per Spike #176 T5 (residual ≤ 2.2e-16 across 5 representative cascades).
- **T7**: Bind-permute commutativity at substrate-natural strides — 273 pair cells × 2 substrates (chess + DNA) = 546 bit-exact assertions per Spike #173 T4 + Spike #172 T4.
- **T8**: Z-DNA-style chirality involution — `M.permute(M.permute(v, k), -k) == v` for all 14 class operators at chess + DNA strides (14/14 round-trips per stride per Spike #173 T5).
- **T9**: Cross-substrate D2 orthogonality at noise floor — same content encoded under 5 substrates produces 10 pairs all at |sim| < 5/sqrt(D) ≈ 0.055 per Spike #173 R3.
- **T10**: Full round-trip `encode → rotate → inverse → decode` bit-exact recovery across 5 catalog entries.

Plus supplementary tests:

- Path B core ops registered with path_registry on Path B side.
- Spike #170 §3 invariants (bind self-inverse at D=8192; k=3 tripartition orthogonality).
- 8+ canonical cascade compositions ship (`CANONICAL_CASCADES` has 10 entries).
- `mint_stance_fingerprint` determinism + bag semantics.
- `mint_vector` D-parameter validation.

### Architectural rationale

Per `[[project_rbs_hdc_loe_dual_path_architecture]]`:

- **Path A** — closed-form algebra (Phase 2 baseline; 38 ops). SSoT for primitive definitions.
- **Path B** — RBS-HDC bound-vector instrument at D=8192 (Phase 3 ships core; Phase 4+ ships per-op Path B MVP). Composes from Path A primitive definitions at module-load time per `[[feedback_no_binding_layer_carveout]]`.
- **Path C** — cascade-aware dispatcher (Phase 5 lands routing logic).

Phase 3 delivers the full Path B core surface — the LoE-as-bound-vector instrument + form-function rotation composition — so Phase 4+ per-op Path B MVP can compose from this stable foundation.

### Spike anchors

- Spike #170 — RBS-HDC instrument feasibility (R1 prototype, 14/14 mint determinism; FEASIBILITY-CONFIRMED).
- Spike #172 — DNA helical-pitch substrate (R3 cross-substrate bit-exact closure).
- Spike #173 — chess natural-stride substrate (D2 orthogonality; 25th cross-substrate cascade-match).
- Spike #176 — rotation IS Class K pin-slot (H1 CONFIRMED 6/6 tests at machine ε).
- Spike #177 — pin-slot-resonate music-box mechanism (I + K + C + M∘K).
- Spike #178 — closed-form SP roadmap (Phase 2 Path A baseline citation source).

### Canonical SSoT citations per `[[feedback_science_is_ssot_not_project]]`

- Plate (1995) *Holographic Reduced Representations*, IEEE TNN 6, 623.
- Kanerva (2009) *Hyperdimensional Computing*, Cognitive Computation 1, 139.
- Rachkovskij (2001) *Representation and processing of structures with binary sparse distributed codes*, Neural Comput Appl 9, 322.
- Oppenheim & Schafer (2010) *Discrete-Time Signal Processing* (3rd ed.) — DFT shift theorem.
- Implementation plan: `docs/srmech/notes/rbs_hdc_loe_implementation_plan_2026-05-19.md`.

### Deferred to Phase 4+ (v0.4.2rc4+)

- Path B per-op MVP for the 6-op core (`fft`, `ifft`, `sign_quantise`, `matched_filter`, `wiener`, `hdc_truncation`) — Phase 4.
- Cascade dispatcher full rule-based routing — Phase 5.
- Path B per-op extension to all 38 ops — Phase 6.
- Substrate-natural Class N rational catalogs — Phase 7.
- Learned dispatch table from benchmark suite — Phase 8.
- Notebook §3.8.31 prose — Phase 9.
- C port of Path B core operations — v0.4.3rc1 per conductor decision #1.

## [0.4.2rc1] - 2026-05-19

**Phase 1 scaffolding of the RBS-HDC-LoE dual-path architecture** (Milestone follow-up to Spike #178 closed-form SP roadmap). Ships the `srmech.signal_processing` sub-namespace package skeleton — dispatcher / profiling / registry stubs + locked architectural constants — so Phase 2+ operation modules (Path A closed-form ops Phase 2; Path B RBS-HDC at D=8192 Phase 4; cascade dispatcher Phase 5; cross-substrate verification Phase 7; learned thresholds Phase 8) can land against a stable surface. **No new primitive class introduced**; 14-class A–N vocabulary intact per `[[feedback_no_privileged_primitive_classes]]`. Identity-not-implementation discipline preserved per `[[user_stance_identity_not_implementation_discipline]]` — Path A and Path B both *instantiate* the same class composition. Trauma-informed defensive scope per `[[feedback_trauma_informed_defensive_scope]]` — methodology-research / educational / civilian-comms framing only.

### Added — `srmech.signal_processing` sub-namespace (Phase 1 scaffolding)

- `srmech.signal_processing.__init__` — package entry point + re-exports. Public API stable from Phase 1.
- `srmech.signal_processing._paths` — internal architectural constants:
  - `D_DEFAULT = 8192` (locked per conductor decision #6, 2026-05-19; matches Spike #170/#172/#173/#176/#177 anchors); `D_MIN = 256`; `D_MAX = 65536`.
  - `SUBSTRATES = ("bci", "audio", "rf", "ephemeris")` (Phase 7 cross-substrate coverage per decision #2).
  - `PATH_A`/`PATH_B`/`PATH_VERIFY` discriminators; `VALID_PATHS` tuple.
  - `DISPATCH_TABLE_LOCK_POLICY = "lock-at-release"` (decision #7 — reproducibility).
  - `LEARNED_DISPATCH_TABLE_PATH` — locked NDJSON path (Phase 8 populates).
  - `PROFILING_INPUT_SIZES_DEFAULT` (6) + `PROFILING_CASCADE_DEPTHS_DEFAULT` (4) + `CASCADE_DEPTH_THRESHOLD_FOR_PATH_B = 3` — supports 1920-cell benchmark grid per decision #3.
- `srmech.signal_processing.cascade_dispatcher` — routing API:
  - `begin_cascade(substrate=None, *, D=8192)` — **context-manager** API per decision #5; auto-flush on exception; thread-local stack; nested cascades supported.
  - `end_cascade(ctx=None)` — imperative-form flush for callers who can't structure around `with`.
  - `current_cascade()` — return innermost active `CascadeContext`.
  - `resolve_path(op_name, *, explicit_path=None, input_size=None, substrate=None)` — Phase 1 rule-based routing (override → cascade-hint Path B → class-default → Path A fallback).
  - `dispatch(op_name, *args, path=None, D=8192, **kwargs)` — Phase 1 stub; raises `DispatchError` for ops without registered implementations.
  - `is_dispatch_table_locked()` / `lock_dispatch_table()` / `unlock_dispatch_table()` — lock-state tracking per decision #7.
  - `DEFAULT_PATH_PER_CLASS` — 14 A-N → default path table (Class K/M default Path B; all others default Path A per plan §3.4).
- `srmech.signal_processing.path_registry` — op-name → (Path-A-impl, Path-B-impl) pairing:
  - `register(op_name, *, path, impl, ssot_citation="", classes=())` — idempotent re-registration; `DuplicateRegistrationError` on differing-callable collision.
  - `lookup(op_name) -> OperationEntry` — raises `UnknownOperationError` for unregistered ops.
  - `has_path(op_name, path)` / `registered_ops()` / `clear_registry()`.
  - `OperationEntry` frozen dataclass with `op_name` / `path_a` / `path_b` / `ssot_citation` / `classes` (14 A–N labels).
- `srmech.signal_processing.profiling` — Phase 8 hook API + data structures:
  - `ProfileCellKey` — Cartesian key (op_name, path, input_size, cascade_depth, substrate) supporting decision #3 full granularity.
  - `ProfileRecord` — NDJSON-serialisable timing record (wall + CPU + memory + n_repeats + notes + extra dict).
  - `cell_grid(*, op_names, ...)` — enumerate the full 1920-cell benchmark sweep grid.
  - `record_profile()` / `iter_records()` / `clear_records()` — in-memory record buffer.
  - `profile_op()` / `update_dispatch_table()` — Phase 8 hooks; Phase 1 raises `ProfilingNotImplementedError`.

### Architectural rationale

Per `[[project_rbs_hdc_loe_dual_path_architecture]]`:

- **Path A** — closed-form algebra (composes existing `srmech.amsc.*` 14-class primitive vocabulary). SSoT for primitive definitions.
- **Path B** — RBS-HDC bound-vector instrument at D=8192 (per Spike #170 anchor). Composes from Path A primitive definitions at module-load time per `[[feedback_no_binding_layer_carveout]]`; no duplicate primitive implementations.
- **Path C** — cascade-aware dispatcher (`cascade_dispatcher`); chooses A or B per call based on rule-based (Phase 5) + empirical (Phase 8) routing. Neither path replaces the other.

The 8 accepted conductor decisions (2026-05-19) framing Phase 1:

1. C port deferred to v0.4.3rc1 (no C surface in Phase 1).
2. Cross-substrate coverage stub-level for all 4 substrates.
3. Profiling granularity full per-op × per-cascade-depth × per-substrate (1920 cells).
4. Spike #179 F4 caveat integrates at Phase 9 §3.8.31.
5. `begin_cascade` API as context-manager (Pythonic; auto-flush on exception).
6. D=8192 lock for v0.4.2 baseline; optional `D` param accepted.
7. Dispatch table lock policy: lock-at-release (reproducibility).
8. Notebook §3.8.31 timing: Phase 9 (after Phase 8 learned thresholds).

### Added — `tests/test_signal_processing_scaffolding.py`

Phase 1 scaffolding verification:

- Imports succeed: `from srmech.signal_processing import begin_cascade, dispatch, register, lookup, ...`.
- D=8192 locked default; optional `D` parameter forwarded by dispatcher.
- `begin_cascade(substrate="bci")` context-manager opens/closes cascade; thread-local stack supports nesting; auto-flush on exception.
- `path_registry.register(...)` / `lookup(...)` / `has_path(...)` round-trip; duplicate-registration with differing callable raises `DuplicateRegistrationError`.
- `profiling.cell_grid(...)` enumerates the 1920-cell benchmark grid for a 10-op suite at default sweeps.
- `profile_op()` + `update_dispatch_table()` raise `ProfilingNotImplementedError` (Phase 8 lands runner).
- `dispatch(op_name, path="verify")` raises `DispatcherNotImplementedError` in Phase 1 (verify-mode lands Phase 5).
- Version is `0.4.2rc1` across `srmech.__version__` + `pyproject.toml` + `pyproject-pure.toml` + `c/include/srmech.h`.

### Canonical SSoT citations per `[[feedback_science_is_ssot_not_project]]`

- Plate (1995) *Holographic Reduced Representations*, IEEE TNN 6, 623.
- Kanerva (2009) *Hyperdimensional Computing*, Cognitive Computation 1, 139.
- Chung (1997) *Spectral Graph Theory*, AMS.
- Oppenheim & Schafer (2010) *Discrete-Time Signal Processing* (3rd ed.).
- Implementation plan: `docs/srmech/notes/rbs_hdc_loe_implementation_plan_2026-05-19.md` (committed on this branch).

### Spike anchors

- Spike #170 — RBS-HDC instrument feasibility (14/14 mint determinism at D=8192).
- Spike #172 — DNA helical-pitch substrate.
- Spike #173 — chess natural-stride (D2 orthogonality).
- Spike #175 — knowledge-is-gauge-content.
- Spike #176 — rotation IS Class K (machine ε).
- Spike #177 — pin-slot-resonate music-box mechanism.
- Spike #178 — closed-form SP roadmap (§1 surveys ~40 ops across 8 categories).
- Spike #179 — CFSP-Kalman alternative (in flight; Phase 9 integration per decision #4).

### Not added (deferred to Phase 2+)

- Path A closed-form ops (`closed_form_ops/*`) — Phase 2 (v0.4.2rc2) ships 38 ops re-surfacing `srmech.amsc.*` primitives.
- Path B core (`rbs_hdc_instrument.py`, `form_function_rotation.py`) — Phase 3 (v0.4.2rc3) ports Spike #170 prototype.
- Path B per-op MVP — Phase 4 (v0.4.2rc4).
- Full rule-based cascade dispatcher + `path="verify"` semantics — Phase 5 (v0.4.2rc5).
- 7-op extension + remaining 32 Path B ops — Phase 6 (v0.4.2rc6).
- Substrate-natural Class N rational catalogs + cross-substrate verification — Phase 7 (v0.4.2rc7).
- Benchmark suite + learned dispatch table — Phase 8 (v0.4.2rc8).
- Notebook §3.8.31 prose — Phase 9 (documentation-only commit).
- Production tag v0.4.2 → PyPI — Phase 10.
- C port of Path B operations — v0.4.3rc1 (per conductor decision #1).

## [0.4.1rc14] - 2026-05-18

**rcN+1 of the runtime spectral decomposition surface** (Milestone #13). Ships entries 1/2/3/7 of the 7-entry `srmech.spectral.*` namespace per Spike `#115` two-rc strategy (PR #518): `decompose` (Class L+A), `delta` (Class M; Option B per Spike `#114`), `recompose` (Class L+M), `similarity` (Class M). All composition layer; sub-ops route to existing `srmech.amsc.{laplacian, hdc, format}` C primitives. **No new primitive class introduced**; 14-class A–N vocabulary intact per `[[feedback_no_privileged_primitive_classes]]`. rcN+2 (TBD) ships entries 4/5/6 (`predict` / `prediction_error` / `truncate_sparse`) after Spike `#113` + `#117` C primitive landings.

### Added — `srmech.spectral` runtime namespace

- `srmech.spectral.SpectralHandle` — frozen dataclass pairing `substrate_descriptor_hash` (SHA-256 of Laplacian + encoder tag; `laplacian_kind` folds into the hash per Spike `#115` design 2026-05-18) with `coefficients_bytes`, `content_sha`, `n_modes`.
- `srmech.spectral.decompose(state, laplacian, *, encoder_tag="default") -> SpectralHandle` — Class L Hermitian eigendecomposition (via `srmech.amsc.laplacian.hermitian_eigendecompose`) ∘ Class A SHA-256 content addressing. Projects `state` onto eigenbasis, packs to bytes, returns handle. Eigenbasis cached in module-level LRU (`N_MAX_EIGENBASES=8`).
- `srmech.spectral.delta(ref, current) -> bytes` — Class M (HDC bind / XOR self-inverse) per Spike `#114` Option B (direct on already-encoded coefficient bytes; 1.22× faster than wrapper). Accepts `SpectralHandle` or raw `bytes`. Raises if substrate descriptor hashes mismatch between handles.
- `srmech.spectral.recompose(handle, laplacian, *, encoder_tag="default") -> np.ndarray` — inverse eigendecomposition `V @ coeffs` with `content_sha` integrity check on the handle. Bit-exact roundtrip with `decompose` at machine ε (tested at < 10⁻¹²).
- `srmech.spectral.similarity(a, b) -> float` — Class M HDC similarity `1 − 2·hamming(a,b)/D` ∈ `[−1, 1]`. Accepts `SpectralHandle` or raw `bytes`.
- `srmech.spectral.clear_eigenbasis_cache()` — test-isolation utility.
- `srmech.spectral.N_MAX_EIGENBASES` — module-level LRU bound (8).

### Added — `tests/test_spectral.py` (22 tests, all passing)

Bit-exact verification of:
- `decompose` returns valid `SpectralHandle` with stable descriptor hash (independent of state); shape-rejection paths.
- `delta` self-inverse identity `bind(a, bind(a, b)) = b` per Plate 1995 / Kanerva 2009 BSC algebra; commutativity; handle-substrate mismatch rejection.
- `recompose` roundtrip at machine ε (< 10⁻¹²); content_sha + descriptor_hash mismatch rejection.
- `similarity` self-similarity = +1.0; random near-orthogonal in `[−0.2, +0.2]`.
- Cache LRU bounded at `N_MAX_EIGENBASES`; cleared on `clear_eigenbasis_cache()`.
- End-to-end: `state_b coefficients = bind(h_a.coeffs, bind(h_a.coeffs, h_b.coeffs))` bit-exact byte-equal.

### Canonical SSoT citations per `[[feedback_science_is_ssot_not_project]]`

- Plate (1995) *Holographic Reduced Representations*, IEEE TNN 6, 623.
- Kanerva (2009) *Hyperdimensional Computing*, Cognitive Computation 1, 139.
- Chung (1997) *Spectral Graph Theory*, AMS.
- Golub & Van Loan (2013) *Matrix Computations* (4th ed.), §8.5.

### Spike anchors

- Spike `#112` (PR `#513`) — scoping doc + 7-entry follow-up list.
- Spike `#114` (PR `#514`) — HDC bind delta-encoding identity bit-exact 4/4 substrates; Option B API.
- Spike `#115` (PR `#518`) — 7-entry tool-schema surface design + two-rc strategy.
- Spike `#116` (PR `#516`) — cross-substrate rank-k delta template 3/3 non-chess bit-exact.
- Spike `#117` (PR `#517`) — Class K compression by β band-membership (rcN+2 prereq).
- Spike `#113` (PR `#515`) — predictive-coding cascade Class C∘L (rcN+2 prereq).

### Not added (deferred to rcN+2 — **SHIPPED in v0.4.2rc4**)

The following three operations were originally listed as deferred from rcN+1:

- `srmech.spectral.predict` (Spike `#113` Class C cascade-extrapolate)
- `srmech.spectral.prediction_error` (Class M+K composition; `threshold=0.0` default per user decision 2026-05-18)
- `srmech.spectral.truncate_sparse` (Spike `#117` Class K sparse-truncate + gate-by-threshold)

**Ship status**: All three now shipped in `[0.4.2rc4]` (this document, above) as the MS #14 rcN+2 deliverable per user direction 2026-05-19. Tool-schema entries register at rcN+2 ship time per the original discipline. Implementation is Python-only at v0.4.2rc4; native C ports follow in a later rc per the per-class build-out roadmap.

## [0.4.1rc13] - 2026-05-17

**Task #248 — `pi_cascade_digits` cap expansion (engineering follow-on to PR #468 benchmark).** Per user direction 2026-05-17 ("now I'm curious to know and think we should include in our notes, wall time to return 350 digit pi cascade, partly because it's a weird number on purpose"). The benchmark note in [`docs/srmech/notes/pi_cascade_digits_benchmark_2026-05-17.md`](../notes/pi_cascade_digits_benchmark_2026-05-17.md) surfaced the rc12 hard cap (num_digits ≤ 50 by validation, not by mathematics); rc13 closes that gap with auto-scaled cascade parameters + a 1000-digit ceiling.

### Changed — `pi_cascade_digits` cap raised from 50 to 1000

- `srmech.amsc.rational._PI_CASCADE_MAX_DIGITS`: 50 → 1000.
- `srmech.amsc.rational._PI_CASCADE_MAX_DEPTH`: 90 → 2000.
- New constant `_PI_CASCADE_MAX_PRECISION_BITS = 32768` (was hard-coded 8192 ceiling).
- `pi_cascade_digits(num_digits, *, max_cascade_depth=None, precision_bits=None)` — kwargs default to `None`. When `None`, the function auto-scales via the new `_pi_cascade_auto_params` helper. Existing rc12 callers (no kwargs / explicit defaults of 90 / 512) continue to work unchanged.
- New helper `srmech.amsc.rational._pi_cascade_auto_params(num_digits) -> (depth, precision_bits)` — linear scaling formula derived from the rc12 validated point: `depth = max(90, ceil(num_digits * 90 / 50))`, `precision_bits = max(512, ceil(num_digits * 512 / 50))`. Bit-exact pure-integer arithmetic, AST-clean (no math.pi access).

### Changed — `_integer_sqrt` switched to `math.isqrt` (huge speedup)

- The rc12 implementation used a naive Newton iteration in pure Python. `math.isqrt` (CPython 3.10+) implements an asymptotically-optimal Karatsuba-style integer-floor square root in C; at 20480-bit inputs (D=1000 cascade scale) the speedup is ~2500x.
- `math.isqrt` is NOT a transcendental constant access — the AST gate (which flags `math.pi`, `math.tau`, `numpy.pi`, `np.pi`, `sympy.pi`, `scipy.pi`) is unchanged and still passes. `math.isqrt` is pure-integer arithmetic, fully compatible with `[[user_stance_pi_spectral_shape_scalar_invariant]]` substrate-invariance discipline.
- Without this optimization, num_digits=1000 would take ~24 minutes (extrapolated from naive Newton scaling). With `math.isqrt`, num_digits=1000 takes ~0.7 seconds.

### Added — 6 new rows in `pi_digits/row.ndjson` (12 total)

rc12's catalog at num_digits ∈ {5, 10, 15, 20, 25, 50} extended with rc13 cap-expansion rows at num_digits ∈ {100, 200, 350, 500, 750, 1000}. Each row cross-validated bit-exact against mpmath canonical π reference (the de-facto Python arbitrary-precision π implementation, via Borwein-Borwein 4th-order convergent algorithm). The 350-digit row is the user's "weird number on purpose" probe from PR #468.

Row schema's `num_digits` max widened: 50 → 1000.

### Added — 8 new tests in `tests/test_pi_cascade_primitives.py`

- `test_pi_cascade_digits_350_weird_number_on_purpose` — the deliberate probe value
- `test_pi_cascade_digits_scaling_rc13[num_digits]` — parametrised over {100, 200, 350, 500, 750, 1000}
- `test_pi_cascade_digits_1000_rc13_ceiling` — the new cap ceiling
- `test_pi_cascade_digits_over_rc13_cap_raises` — cap validation
- `test_pi_cascade_digits_auto_params_helper` — pins the auto-scaling formula
- `test_pi_cascade_digits_explicit_kwargs_override_auto` — caller can override
- `test_pi_cascade_digits_ast_no_math_pi_across_rc13_scale` — AST gate survives cap expansion
- Plus `_pi_cascade_auto_params` added to the AST-gate walk in `test_pi_cascade_digits_call_graph_ast_no_math_pi`

New canonical reference `CANONICAL_PI_1000` in both test files (1000 decimal digits, cross-validated against mpmath).

### Added — 3 new tests in `tests/test_pi_digits_catalog.py`

- `test_pi_digits_has_12_rows_rc13` — pins row count at 12 (rc12's 6 + rc13's 6)
- `test_pi_350_digits_canonical_weird_number_probe` — regression-pinned 350-digit row
- `test_pi_1000_digits_canonical_rc13_ceiling` — regression-pinned 1000-digit row
- Existing tests extended: `test_pi_digits_canonical_num_digits_values` widened to all 12 levels, `test_pi_cascade_digits_chain_falsification_all_rows` ratchet bumped from 5 → 12, `test_all_rows_share_canonical_pi_prefix` reference widened from 50 → 1000 digits.

### Wall time (Windows / Python 3.14.4 / fresh-venv)

| num_digits | depth (auto) | prec_bits (auto) | wall time |
|---:|---:|---:|---:|
| 50  | 90   | 512   | ~1 ms   |
| 100 | 180  | 1024  | ~2 ms   |
| 200 | 360  | 2048  | ~10 ms  |
| 350 | 630  | 3584  | **~40 ms** (the user's question) |
| 500 | 900  | 5120  | ~100 ms |
| 750 | 1350 | 7680  | ~310 ms |
| 1000 | 1800 | 10240 | ~700 ms |

The benchmark note's "seconds-range" projection for D=350 was based on the rc12 naive `_integer_sqrt`; the `math.isqrt` switch in rc13 collapses the projection from seconds to milliseconds.

### Test count

- 535 → 549+ passed (full srmech suite; +14 new pi-related tests)
- tool_schema `pi_cascade_digits` ToolEntry summary updated with rc13 cap-expansion note
- JPL Rule 5 audit: no regression (no new C functions; the Python-only cap-expansion + math.isqrt swap don't touch the C surface)
- AST-verification gate: zero `math.pi` invocations across the full call graph including the new `_pi_cascade_auto_params` helper

### C parity

`pi_cascade_digits` stays Python-only per rc12's honest scope decision ([[feedback_no_binding_layer_carveout]]) — the cascade requires bignum integer arithmetic for precision_bits up to 32768 + the long-division step. rc13's expansion of the cap doesn't change that decision; if anything it reinforces it (the precision_bits requirements scale linearly with num_digits, and at 10240 bits the u64 envelope is comfortably exceeded). The Python wrapper around `math.isqrt` IS the C path here — CPython's `math.isqrt` is a C implementation in the interpreter itself.

`continued_fraction_convergents` (the companion Class N primitive shipped in rc12) retains its `srmech_cf_convergents_int64` C surface unchanged.

### Anchored in

- `[[user_stance_pi_spectral_shape_scalar_invariant]]` — the convergent ladder IS π's substrate identity; the decimal expansion is downstream readout. rc13 cap-expansion makes more of the projection visible at the same substrate.
- `[[user_stance_pi_as_projection]]` — π is generated by the cascade-substrate operation
- `[[feedback_every_doc_edit_faces_falsification]]` — discipline this catalog operationalises
- `[[feedback_no_binding_layer_carveout]]` — Python-only by honest scope (bignum-required); not a binding-layer carve-out
- Task #248 (this rc) — engineering follow-on to PR #468 benchmark
- PR #468 benchmark note (2026-05-17) — the engineering finding (rc12 caps at 50 by validation) + the scaling projection
- Spike #32 (PR #460) — empirical confirmation across 3 substrates

## [0.4.1rc12] - 2026-05-16

**Task #245 Milestone #4 — π geometric-cascade primitives (cascade output, no `math.pi`).** Per user direction 2026-05-16 — operationalises `[[user_stance_pi_spectral_shape_scalar_invariant]]` (the convergent ladder IS π's substrate identity; the decimal expansion 3.14159... is downstream readout) via two new Class N primitives + a new chain-falsifiable `pi_digits` AMSC catalog. Confirms Spike #32 / PR #460 substrate-invariance result as on-disk falsification infrastructure (second instance of `[[feedback_every_doc_edit_faces_falsification]]` after `asymptotic_calculus`).

### Added — 2 new Class N π geometric-cascade primitives (Python)

- `srmech.amsc.rational.continued_fraction_convergents(coef_list) -> list[tuple[int, int]]` — produces the convergent ladder `[(h_0, k_0), (h_1, k_1), ...]` from a continued-fraction coefficient list via the standard CF recurrence (`h_k = a_k * h_{k-1} + h_{k-2}`). Canonical π CF `[3; 7, 15, 1, 292, 1, ...]` yields canonical convergents `(3, 1), (22, 7), (333, 106), (355, 113), (103993, 33102), ...` per Hardy & Wright §10.6. Pure-Python bignum-capable; C-standalone for int64-fit ladders via `srmech_cf_convergents_int64`.
- `srmech.amsc.rational.pi_cascade_digits(num_digits) -> str` — streams decimal-digit expansion of π via Archimedes hexagon-doubling cascade. Uses integer Newton-Raphson rational √ at fixed `precision_bits` (default 512) over `max_cascade_depth` doublings (default 90). Produces `"3.14159..."` as string. **AST-verified zero `math.pi` invocations** anywhere in the call graph (discipline gate per `[[user_stance_pi_spectral_shape_scalar_invariant]]`).

Bounded caps: 256 CF coefficients (continued_fraction_convergents); 50 digits / depth 90 / 8192 bits (pi_cascade_digits). Substantially larger than any practical use case; both primitives are pure integer arithmetic throughout the call graph.

### Added — C parity for `continued_fraction_convergents`

- `srmech_cf_convergents_int64(coefs, n, out_nums, out_dens)` in `c/src/srmech_rational.c` + header decl in `srmech.h`. ABI v2 pure-addition (no ABI bump). int64-bound n ≤ 256. Returns `SRMECH_ERR_OVERFLOW` when any convergent exceeds int64; Python wrapper falls through to bignum. Two helper functions (`cf_conv_sadd_i64`, `cf_conv_step`) split per JPL Rule 4 (≤60 LOC) with ≥2 asserts per non-exempt function (Rule 5).

`pi_cascade_digits` stays Python-only — the cascade requires bignum integer arithmetic for `precision_bits` ≥ 512 + the long-division step, neither of which fits the JPL-clean u64 envelope of the C primitive surface. Honest scope decision per `[[feedback_no_binding_layer_carveout]]`: every primitive class earns a C surface; bignum-required cases stay Python.

### Added — `srmech.amsc.attested.pi_digits/` chain-falsifiable catalog

First chain-falsifiable π substrate-invariance catalog. Operationalises Spike #32 / PR #460 result (substrate-invariance across triangle / square / hexagon cascades with AST-verified zero math.pi invocations).

- `descriptor.toml` — single-step `pi_cascade_digits` chain calling the Class N primitive.
- `row.ndjson` — 6 self-validating rows at canonical precision levels: num_digits ∈ {5, 10, 15, 20, 25, 50}. Each row's `expected_pi_string` is the bit-exact canonical decimal expansion of π verifiable against Khinchin *Continued Fractions* §10.
- `row.schema.json` — JSON schema for the row data (enforces `expected_pi_string` starts with `"3."`).

Mathematical anchor: π's substrate identity is the cascade-emergent CF convergent ladder per `[[user_stance_pi_spectral_shape_scalar_invariant]]`; the decimal expansion is a downstream readout under continuous-length-metric projection. Catalog rows are the readable artifact backed by the cascade primitive's substrate computation. Source citations: Khinchin *Continued Fractions* §10 (canonical π CF); Hardy & Wright *Theory of Numbers* §10.6 (best-rational convergent property); Archimedes *Measurement of a Circle* c. 250 BCE (hexagon-doubling cascade algorithm).

### Added — `tests/test_pi_cascade_primitives.py` (27 tests, all green)

- Continued-fraction convergents: canonical π convergents (first 6 + full 16), canonical e convergents cross-check, simple-CF edge cases, bignum ladder, input validation
- pi_cascade_digits: 0/5/10/15/20/25/50 digit canonical values, prefix consistency check, input validation, low-depth divergence behavior, default-kwargs consistency
- **AST-verification gate**: three discipline tests confirming zero `math.pi` / `numpy.pi` / `math.tau` (or equivalent) attribute accesses across `pi_cascade_digits`, its private helpers (`_integer_sqrt`, `_scaled_integer_sqrt`), and `continued_fraction_convergents`
- Substrate-readout consistency: 355/113 convergent agrees with `pi_cascade_digits(6)` first 6 digits

### Added — `tests/test_pi_digits_catalog.py` (9 tests, all green)

- Catalog presence + ≥5 rows
- Canonical num_digits coverage (5, 10, 15, 20, 25, 50)
- Chain falsification (bit-exact comparison row-by-row)
- Canonical regression-pinned values (15-digit IEEE-754 boundary, 50-digit bignum-deep)
- All rows are prefixes of canonical π (substrate-invariance documentation)
- Attestation field presence per descriptor's `[attestation]` block

### Test count

- 499 → 535 passed (full srmech suite; +36 new tests)
- tool_schema ToolEntry coverage bumps by 2 (one per new Class N primitive)
- JPL Rule 5 audit: no regression (new C helpers cf_conv_sadd_i64 + cf_conv_step + srmech_cf_convergents_int64 each have ≥ 2 asserts)
- JPL Rule 4: every new C function ≤ 60 lines (cf_conv_step is 16 LOC; srmech_cf_convergents_int64 is 28 LOC)

### Numbering note

rc12 is Milestone #4 closing Task #245 — the π substrate-output primitive shipping. Predecessor rc11 (Milestone #2 Phase 3B) closed transcendental-Taylor inventory. Following rcs continue Task #234 §11 (forward_difference / riemann_sum), Task #218 Phase C2 work, or new milestones per user direction.

### Anchored in

- `[[user_stance_pi_spectral_shape_scalar_invariant]]` — the convergent ladder IS π's substrate identity (this catalog operationalises this stance)
- `[[user_stance_pi_as_projection]]` — older form; ladder vs. decimal is the projection-shadow boundary
- `[[user_stance_identity_not_implementation_discipline]]` — umbrella discipline (π IS the ladder at substrate level; π HAS a decimal expansion at notation level)
- `[[feedback_every_doc_edit_faces_falsification]]` — discipline this catalog operationalises (second concrete instance)
- `[[feedback_no_binding_layer_carveout]]` — C surface for continued_fraction_convergents (int64 path); Python-only for pi_cascade_digits (bignum required) is honest scope, not binding-layer carve-out
- Spike #32 (PR #460) — empirical confirmation across 3 substrates with AST-verified zero math.pi

## [0.4.1rc11] - 2026-05-16

**Task #234 Phase 3B — trig + log Taylor primitives (Milestone #2 second ship).** Per user direction 2026-05-16 ("number 2 and 3 in the same milestone, do sequentially and test with testpypi first"). Phase 3A shipped `cosmos_validation` catalog as rc10; Phase 3B adds 4 trig/log Taylor partial-sum primitives + chain specs + rows to the `asymptotic_calculus` catalog. Closes Task #234 §11 inventory's transcendental row.

### Added — 4 new Class N Taylor-series primitives (Python)

- `srmech.amsc.rational.sin_series_truncate(num, den, num_terms) -> (out_num, out_den)` — sin(p/q) = Σ (-1)^k (p/q)^(2k+1) / (2k+1)!
- `srmech.amsc.rational.cos_series_truncate(num, den, num_terms) -> (out_num, out_den)` — cos(p/q) = Σ (-1)^k (p/q)^(2k) / (2k)!
- `srmech.amsc.rational.log1p_series_truncate(num, den, num_terms) -> (out_num, out_den)` — log(1+p/q) = Σ_{k=1} (-1)^(k+1) (p/q)^k / k (caller responsibility: |p/q| < 1 for convergence)
- `srmech.amsc.rational.atan_series_truncate(num, den, num_terms) -> (out_num, out_den)` — atan(p/q) = Σ (-1)^k (p/q)^(2k+1) / (2k+1) (caller responsibility: |p/q| ≤ 1)

Pure Python bignum-capable; uses common-denominator integer accumulation with periodic gcd reduction. Bounded `num_terms` (50 for trig; 64 for log/atan) so the per-row time stays acceptable.

### Deferred — C parity for trig primitives (rc12 candidate)

Per `[[feedback_no_binding_layer_carveout]]` every Class N op earns a C surface. rc11 ships Python-only because the 4 trig primitives use bignum-accumulating Taylor series whose intermediates exceed u64 for typical (x, N) inputs; the C path would need either (a) tight num_terms bounds and OVERFLOW returns on most catalog rows, or (b) multi-precision integer infrastructure in C. Honest scope decision: ship Python-only at rc11; add C parity in rc12 with a documented narrow-bound case (matching what `srmech_exp_series_truncate` already does at u64 limits). Tracked as a follow-on task. The rc8 exp_series_truncate C surface remains the canonical example of C-standalone discipline; rc11 adds 4 surfaces to the same C parity work queue.

### Added — `asymptotic_calculus/descriptor.toml` — 4 new chain specs

- `sin_series_truncate` chain — single Class N step
- `cos_series_truncate` chain
- `log1p_series_truncate` chain
- `atan_series_truncate` chain

Each chain takes `(@row.x_num, @row.x_den, @row.num_terms)` and returns `(out_num, out_den)` exact rational. Row schema's `kind` enum widened from `["exp"]` to `["exp", "sin", "cos", "log1p", "atan"]`.

### Added — 16 new self-validating rows in row.ndjson

Per-op rows covering canonical inputs:
- sin: x=0, 1/6 (~30°), 1/4 (~14°), 1 rad
- cos: x=0, 1/6, 1/4, 1 rad
- log1p: x=0, 1/10, 1/4, -1/4
- atan: x=0, 1/4, 1/2, 1 (~π/4)

Each row's `(expected_num, expected_den)` computed bit-exactly by running the new Python op at catalog-author time.

### Test count

- 482 → 484 passed (full srmech suite); `tests/test_asymptotic_calculus_catalog.py::test_exp_series_truncate_chain_falsification_all_rows` expanded to dispatch by `kind` and bit-exact-compare each row across all 5 chain types
- tool_schema ToolEntry coverage ratchet bumps by 4

### Numbering note

This is the second rc in Milestone #2. Phase 3A (cosmos_validation catalog, rc10) shipped first per user direction "do sequentially". rc11 closes the trig-primitive portion of Task #234 §11. Future rc12 ships C parity for the 4 trig primitives + adds calculus operators (forward_difference, riemann_sum) per Task #234 §11 inventory.

### Anchored in

- `[[feedback_every_doc_edit_faces_falsification]]` — discipline
- Task #234 §11 inventory — scope (sin / cos / tan / log / atan / sinh / cosh / Bessel / Γ / ζ / forward_difference / riemann_sum)
- User direction 2026-05-16 Milestone #2 — "do sequentially and test with testpypi first"

## [0.4.1rc10] - 2026-05-16

**Task #234 Phase 3A — `cosmos_validation` catalog ship (Spike #27 / PR #437 Q6.1 falsification infrastructure).** Per user direction 2026-05-16 (Milestone #2: "Task #234 — asymptotic_calculus expansion: cosmos_validation + trig primitives"). First instance of the milestone's pattern: a chain-falsifiable cosmology catalog using only existing Class N rational primitives plus 4 new rational arithmetic ops with Python + C parity.

### Added — Class N rational arithmetic primitives (4 new ops with full C/Python parity)

- `srmech.amsc.rational.rational_add(a, b) -> (num, den)` — add two rationals, reduced.
- `srmech.amsc.rational.rational_mul(a, b) -> (num, den)` — multiply two rationals, reduced.
- `srmech.amsc.rational.rational_div(a, b) -> (num, den)` — divide two rationals, reduced; raises ZeroDivisionError on b_num=0.
- `srmech.amsc.rational.rational_pow_uint(base, exp) -> (num, den)` — raise rational to non-negative integer exponent; exp ≤ 64.

All four take tuple inputs `(p, q)` for clean chain composition via Phase 2 v1 list-resolution in `compose._resolve_args`. C surfaces: `srmech_rational_add` / `srmech_rational_mul` / `srmech_rational_div` / `srmech_rational_pow_uint` in `c/src/srmech_rational.c` + header decls in `srmech.h` + ctypes bindings in `_native.py`. Each Python wrapper dispatches to C when inputs fit u64; falls through to bignum on OVERFLOW or missing-symbol. Per `[[feedback_no_binding_layer_carveout]]` the C library is usable standalone for u64-fit inputs. JPL Power-of-Ten clean: helpers split per Rule 4 (≤60 LOC), ≥2 asserts per function (Rule 5).

### Added — `srmech.amsc.attested.cosmos_validation/` catalog

First chain-falsifiable cosmology catalog. Operationalises Spike #27 / PR #437 Q6.1 dark-sector monotonicity claim (concertmaster's PR #437 audit recommendation 1).

- `descriptor.toml` — 9-step `friedmann_dark_fraction` chain composing rational_pow_uint (1) + rational_mul (3) + rational_add (4) + rational_div (1).
- `row.ndjson` — 11 self-validating rows: Planck-canonical Ω values (Ω_b = 49/1000, Ω_c = 265/1000, Ω_Λ = 685/1000, Ω_r = 1/10000) + scale-factor a across z ∈ [-0.9, ~10⁵]. Each row stores expected `f_dark(a)` rational; CI runs the chain and bit-exact-compares.
- `row.schema.json` — JSON schema for the row data.

Mathematical claim: `f_dark(a) = (Ω_c·a + Ω_Λ·a⁴) / (Ω_b·a + Ω_c·a + Ω_Λ·a⁴ + Ω_r)`. Q6.1 monotonicity: f_dark(a) strictly increases in a — verified bit-exact across the 11 rows (0.026 at a=1/100000 → 0.951 at a=1 → 0.99993 at a=10). Source: Planck Collaboration 2018 VI (Aghanim et al. 2020, A&A 641:A6, doi:10.1051/0004-6361/201833910, arXiv:1807.06209) per `[[feedback_pdf_extraction_citation_discipline]]`.

### Added — `tests/test_cosmos_validation_catalog.py` (9 tests, all green)

- Catalog presence + row count
- Chain bit-exact falsification (all 11 rows)
- **Q6.1 monotonicity test**: sorts rows by a, asserts strict-increase across all consecutive pairs
- Unit tests for each new rational op
- Canonical pin: f_dark(a=1) = 9500/9991

### Added — tool_schema entries for the 4 new rational ops

Coverage ratchet bumps; each op cites Class N's rational-approximation primitive role.

### Numbering note

This rc10 builds on the rc1-rc9 sprint that shipped in `0.4.1rc9` (merged to main via PR #447). It is the first rc in Milestone #2 (Task #234 — asymptotic_calculus expansion). Subsequent rc11 will add sin/cos/log/atan trig primitives (Phase 3B per user direction "do sequentially and test with TestPyPI first").

### Anchored in

- `[[feedback_every_doc_edit_faces_falsification]]` — discipline this catalog operationalises
- `[[feedback_no_binding_layer_carveout]]` — every new Class N op gets a C surface
- `[[user_stance_pi_as_projection]]` + `[[user_stance_kepler_shape_universal]]` + `[[user_stance_asymptotic_dof_sidesteps_infinity]]` + `[[user_stance_epicycle_via_gear_plus_pin]]` — the stance family
- Spike #27 / PR #437 Q6.1 monotonicity claim (concertmaster audit reproduced 9999/9999 positive slopes; this catalog ships the analytic proof as 11 bit-exact rows)

## [0.4.1rc9] - 2026-05-16

**Hotfix: asymptotic_calculus row attestation field.** The rc8 fresh-venv TestPyPI smoke surfaced that `catalog.get_attested_dataset("asymptotic_calculus")` failed at row-parse time because the literature_curated adapter requires every row to carry a `source_published_date` field for per-row attestation. The rc8 row.ndjson had `source_apostol` + `source_bishop` references but not the explicit publication date.

### Fixed
- All 12 rows in `srmech.amsc.attested.asymptotic_calculus/row.ndjson` now carry `source_published_date = "1974-01-01"` (Apostol *Mathematical Analysis* 2nd ed. publication; the citation pinned for the convergence claim per Theorem 12.20).
- `srmech.amsc.attested.asymptotic_calculus/row.schema.json` adds `source_published_date` to its required-fields list + properties (ISO 8601 date format).

### Behaviour impact
- `bridge.get_attested_dataset("asymptotic_calculus", limit=N)` returns rows cleanly.
- `bridge.attestation_audit("asymptotic_calculus")` resolves per-row attestation hashes.
- Python `srmech.amsc.rational.exp_series_truncate(...)` and the C path `srmech_exp_series_truncate(...)` unchanged from rc8.

This is a 12-row + 1-schema-line patch; no C code or Python primitive changes.

## [0.4.1rc8] - 2026-05-16

**Spike #28 ship — asymptotic_calculus catalog + Class N `exp_series_truncate` with C parity (re-versioned from rc6).** Originally drafted as rc6 on PR #447's branch; renumbered to rc8 after PR #439's rc7 chain-spec hotfix merged to main between the two PRs. The underlying ship is identical (asymptotic_calculus catalog, `exp_series_truncate` op, math addendum + chain-spec form + scope inventory) plus the **C parity surface** that was deferred at rc6 ship and now lands on top per `[[feedback_no_binding_layer_carveout]]` — the C library is usable standalone, no Python required.

### Added — Class N op `exp_series_truncate` with full C/Python parity

- **Python** `srmech.amsc.rational.exp_series_truncate(numerator, denominator, num_terms) -> (out_num, out_den)` — computes the exp Taylor partial sum `S_N(p/q) = sum_{k=0..N} (p/q)^k / k!` as an exact rational in lowest terms. Composes:
  - **Class N** rational-approximation: numerator/denominator tracking + gcd reduction
  - **Class J** integer factorial: `k!` as running integer product
  - **Class I** integer arithmetic: power accumulators `p^k`, `q^k`
  - Pure integer arithmetic at every step; arbitrary-precision via Python int for N ≤ 512.
- **C** `srmech_exp_series_truncate(int64_t x_num, uint64_t x_den, uint32_t num_terms, int64_t *out_num, uint64_t *out_den) -> srmech_status_t` — same op as the Python surface, bounded to `num_terms ≤ 20` (factorial fits u64); returns `SRMECH_ERR_OVERFLOW` when intermediate computation would exceed u64 range. The Python wrapper dispatches to C when inputs fit safe bounds, falls back to bignum Python when they don't. **The C library compiles and runs standalone — no Python interpreter required for the catalog-row-shaped inputs (x ∈ {0, ±1/2, ±1, ±2}, N ∈ {5, 10, 15} all fit u64 comfortably).**
- Canonical SSoT: Apostol *Mathematical Analysis* 2nd ed. Theorem 12.20 (Lagrange remainder); Bishop *Foundations of Constructive Analysis* §2 (asymptotic-rate framing). Both cited per `[[feedback_pdf_extraction_citation_discipline]]`.

### Added — `srmech.amsc.attested.asymptotic_calculus/` catalog

First concrete instance of the doc-claim falsification infrastructure (per `[[feedback_every_doc_edit_faces_falsification]]`):

- `descriptor.toml` — single-step Phase 2 v1 chain spec `exp_series_truncate` calling Class N `exp_series_truncate` op with `@row.x_num`, `@row.x_den`, `@row.num_terms` inputs.
- `row.ndjson` — 12 self-validating rows: x in {0, ±1/2, ±1, ±2} at N in {5, 10, 15}; each row carries (x_num, x_den, num_terms) input plus (expected_num, expected_den) bit-exact ground-truth output.
- `row.schema.json` — JSON schema for the row data.

Future rcs (Task #234) expand the catalog to cover sin, cos, tan, log, atan, Bessel, Γ, ζ partial sums + calculus operations (forward-difference, Riemann sum, continued-fraction convergent). Each new operation lands as a new Class N op (Python + C surface) + new chain spec + new row data.

### Added — `tests/test_asymptotic_calculus_catalog.py` (7 tests, all green)

The falsification test runs the chain for every catalog row and bit-exact compares the produced output to the row's stored expected output. Any drift in Class N + Class J primitives surfaces as immediate row-by-row test failure. Includes regression-pinned canonical exemplars: `S_10(1) = 9864101/3628800` (Spike #28 §9 V4 canonical exemplar) + `S_N(0) = 1/1` (trivial-input pin). Plus C/Python parity test (new at rc8): C path matches Python path bit-exact for `num_terms ≤ 20` inputs.

### Added — tool_schema coverage for `exp_series_truncate`

ToolEntry registered in `srmech.amsc.tool_schema` under `category="rational"`; coverage ratchet bumps from previous floor.

### Numbering note

- rc6 — drafted on PR #447's branch (commit `8887368` historical); renumbered to rc8 at rebase time. Not tagged on TestPyPI.
- rc7 — PR #439's chain-spec hotfix (merged to main). Tagged + published; removes 4 Phase 1 worked-example chains from cosmos catalogs (see rc7 entry below).
- rc8 — this rebase carries PR #447's content forward + adds C parity for `exp_series_truncate` per `[[feedback_no_binding_layer_carveout]]`.

### Anchored in

- Spike #28 working note: [`docs/antikythera-maths/research-mfo/asymptotic_vs_infinity_history_2026-05-16.md`](../../../antikythera-maths/research-mfo/asymptotic_vs_infinity_history_2026-05-16.md) — §9 falsification math (V1-V4), §10 canonical chain-spec form, §11 catalog scope inventory
- `[[feedback_every_doc_edit_faces_falsification]]` — discipline this catalog operationalises
- `[[feedback_no_binding_layer_carveout]]` — C-standalone contract honoured by rc8's C surface
- `[[user_stance_pi_as_projection]]` + `[[user_stance_kepler_shape_universal]]` + `[[user_stance_asymptotic_dof_sidesteps_infinity]]` + `[[user_stance_epicycle_via_gear_plus_pin]]` — the upstream stance family this catalog instantiates operationally

## [0.4.1rc7] - 2026-05-16

**Spike #28 ship — falsification-discipline pre-merge hotfix.** Removes the four Phase 1 worked-example chain specs from the cosmos catalogs because they reference primitives that don't yet exist (their chains list cleanly but fail at activate-time when actually run). Per `[[feedback_every_doc_edit_faces_falsification]]` (user direction 2026-05-16: *"our model has not lied to us yet, so I believe the math still"*) we do not ship chain specs whose underlying primitives can't run — chains that cannot execute are claims that cannot falsify. Surfaced via the rc5 fresh-venv TestPyPI smoke (Class D `match_filter`, Class E `sorted_lookup_extract` + `sorted_lookup_batch`, Class L `spherical_harmonic_decompose` + `extract_preferred_axis`, Class I `angular_separation_axes` all missing). Each chain re-lands as its underlying primitive ships — `spherical_harmonic_decompose` is Spike #26 Phase 2 scope (Task #227); `angular_separation_axes` is Task #234 §11 inventory (`cmb_angular_geometry` sister catalog with rc7+ sin/cos). The DSL design pattern lives in `docs/srmech/adr/0002-phase-1-operator-chain-schema.md` for reference.

### Changed — cosmos catalog chain specs removed

- `srmech/amsc/attested/cmb_low_ell_maps/descriptor.toml`: removed `multipole_vector_axis` (LLDA) and `t_vs_e_axis_differential` (LLLLI) chain specs.
- `srmech/amsc/attested/cmb_polarisation_spectra/descriptor.toml`: removed `acoustic_peak_locations` (CDE) chain spec.
- `srmech/amsc/attested/cmb_bispectrum/descriptor.toml`: removed `f_NL_template_combination` (ENA) chain spec.
- All three descriptors retain `[catalog].chain_schema_version = 1` so re-adding chains later does not require reintroducing the `[catalog]` section. Inline deprecation comments document what was removed and which Task # tracks the re-add.

### Behaviour impact

- `srmech.amsc.catalog.list_catalog_chains(<cosmos_catalog>)` now returns `{"ok": True, "source_key": ..., "n_chains": 0, "chains": []}` for each of the three affected catalogs. Pre-rc7 it returned `n_chains=1` or `n_chains=2` but `run_catalog_chain` would then raise `ChainSpecError` at activate time. The rc7 behaviour is strictly more honest: empty chain list reflects empty executable surface.
- All other rc5 functionality intact: cosmos catalog data rows + chain schema infrastructure + composition engine + Class L broadening + tool_schema coverage.
- `cmb_lensing` catalog never had chain specs and is unaffected.

### Test

`test_compose.test_parse_catalog_chains_cosmos_descriptors_have_no_executable_chains` pins `n_chains == 0` across all 3 cosmos catalogs at rc7.

## [0.4.1rc5] - 2026-05-16

**ADR-0002 Phase 2 — Class L broadening + composition engine + notebook updates.** Implements the Phase 1 spike's dissolve-into-Class-L proposal per `[[feedback_no_privileged_primitive_classes]]`. Class L's identity broadens from "graph Laplacian" to "dense-matrix linear algebra including eigendecomposition + matrix-vector multiplication + elementwise operations"; the graph-Laplacian-specific ops become specialisations. Adds the operator-chain composition engine (`srmech.amsc.compose`) implementing schema v1 from the Phase 1 ADR doc, with linear pipeline execution + 4-namespace reference DSL (`@row.* / @input.* / @step[N].output / @catalog.*`) + chain-level and per-step error policy. Engine integration with the catalog bridge: `list_catalog_chains(source_key)` and `run_catalog_chain(source_key, chain_name, row_index, inputs)`. **Vocabulary stays at 14 classes A–N; no Class P promoted.**

### Added — Class L broadening (4 new ops, full C + Python parity)

Each new op cites canonical physics literature per `[[feedback_science_is_ssot_not_project]]`:

- `srmech.amsc.laplacian.hermitian_eigendecompose(H) -> (eigvals, V)` — complex Hermitian generalisation of `jacobi_eigvals`. Returns ascending eigenvalues + unitary eigenvectors. Native C path via `srmech_hermitian_eigendecompose` (complex-Jacobi rotations with algebraic phase factor `e^(iφ) = γ/|γ|`; pi-free, atan2-free, n ≤ 256). Numpy fallback via `np.linalg.eigh`. Canonical SSoT: Golub & Van Loan *Matrix Computations* (4th ed., 2013) §8.5.
- `srmech.amsc.laplacian.dense_matvec_complex(M, v) -> M @ v` — general complex matrix-vector multiplication. Native C path via `srmech_dense_matvec_complex`; numpy fallback. Canonical SSoT: Golub & Van Loan §1.1.
- `srmech.amsc.laplacian.elementwise_multiply_complex(a, b) -> a * b` — vectorised pointwise complex multiply with broadcasting. Native C path; numpy fallback.
- `srmech.amsc.laplacian.elementwise_transcendental(arr, op_name)` for `op_name ∈ {"exp", "cos", "sin", "log", "exp_i"}`. Array-vectorised transcendentals over real input; `exp_i(x) = exp(1j * x)` (TDSE-relevant complex exponential) realised in Python as `cos + i*sin` over the real argument via two C calls. Canonical SSoT: ANSI C99 §7.12 libm.

The `LAPLACIAN_OPS` module-level constant exposes all 8 op names (4 original + 4 new) for the composition-engine registry.

### Added — composition engine (`srmech.amsc.compose`)

- `ChainSpec` dataclass mirroring the TOML `[[catalog.operator_chain]]` schema.
- `StepSpec` dataclass mirroring `[[catalog.operator_chain.steps]]` entries.
- `parse_chain_spec(chain_dict)` — schema-v1 validation; rejects malformed reference syntax, unknown class identifiers, out-of-bounds `@step[N]` references, illegal `on_error` values, empty step lists.
- `parse_catalog_chains(toml_dict)` — parses all chains in a descriptor TOML; requires `[catalog].chain_schema_version = 1`.
- `resolve_chain(spec, registry)` — binds each step's `class.op` against `DEFAULT_CLASS_REGISTRY` (covers all 14 classes A–N); raises `ChainSpecError` on missing op at activation time.
- `run_chain(spec, *, row, inputs, registry)` — top-level executor; linear pipeline; error policy (raise / warn_return_none / skip-NYI-for-single-call).
- 4-namespace reference DSL resolution at runtime: `@row.<path>`, `@input.<name>`, `@step[N].output[.<path>]`, `@catalog.<row_key>.<col>`.

### Added — catalog bridge integration

- `srmech.amsc.catalog.list_catalog_chains(source_key)` returns `{ok, source_key, n_chains, chains}` where each chain has `{name, summary, returns, on_error, n_steps, classes}`. ADR-0002 Phase 2 bridge surface.
- `srmech.amsc.catalog.run_catalog_chain(source_key, chain_name, *, row_index, inputs)` executes the named chain with optional row binding. Phase 1's 4 worked-example chains across 3 cosmos catalogs are now invocable via this bridge.

### Added — C surface

- `srmech_hermitian_eigendecompose(n, H_il, eigvals, V_il)` — complex Hermitian eigendecomposition via complex-Jacobi rotations. Pi-free, atan2-free; complex numbers travel as interleaved-double pairs (re, im, re, im) on the FFI boundary. Bounded by `SRMECH_LAPLACIAN_MAX_NODES` = 256.
- `srmech_dense_matvec_complex(rows, cols, M_il, v_il, out_il)` — complex matvec.
- `srmech_elementwise_multiply_complex(n, a_il, b_il, out_il)` — pointwise complex multiply.
- `srmech_elementwise_transcendental(n, arr, op_id, out)` — real transcendental dispatcher; op_id enum `SRMECH_TRANS_{EXP,COS,SIN,LOG}` in `srmech.h`.

**ABI version stays at v2** — additive symbol additions don't break the wire contract. JPL Power-of-Ten audit clean: each new function ≤ 60 lines, ≥ 2 assertions, no goto, no malloc, no unbounded loops.

### Added — tool-schema entries (10 new entries)

- `srmech.amsc.laplacian.{hermitian_eigendecompose, dense_matvec_complex, elementwise_multiply_complex, elementwise_transcendental}` — Class L broadening.
- `srmech.amsc.catalog.{list_catalog_chains, run_catalog_chain}` — bridge surfaces.
- `srmech.amsc.compose.{parse_chain_spec, parse_catalog_chains, resolve_chain, run_chain}` — engine surfaces.

Tool-schema coverage ratchet (`tests/test_tool_schema_coverage.py`) continues green.

### Added — tests (39 new test cases)

- `tests/test_laplacian_class_l_broadening.py` (18 tests): parity with numpy for all 4 new ops; Hermitian eigendecomposition convergence + unitarity + 2×2 Pauli-Y reference; `LAPLACIAN_OPS` registry coverage; **end-to-end TDSE composition test** (`hermitian_eigendecompose` → `dense_matvec_complex` → `elementwise_transcendental("exp_i")` → `elementwise_multiply_complex` → `dense_matvec_complex`) verified against reference path to 1e-10 with norm preservation.
- `tests/test_compose.py` (21 tests): schema validation; reference DSL namespace resolution; linear pipeline threading; error policy; catalog-level chain parsing including the 4 real Phase 1 cosmos chains end-to-end.

Full suite: **547 passed** (508 pre-Phase-2 + 39 new).

### Documentation

- `docs/srmech/srmech_research_notebook.md` §3.8.3 added — Class L broadening rationale, the 4 new ops with canonical SSoT citations, dissolve-vs-promote framing per `[[feedback_no_privileged_primitive_classes]]`. Cross-references to ADR-0002 Phase 1 schema doc and Phase 1 report.
- `docs/antikythera-maths/mfo_spectral_research_notebook.md` §VIII.6.1 — added "Closure-validation observation #2 — ADR-0002 Phase 1 TDSE spike" paragraph noting the second affirmative closure-validation (after Phase C1's QM/QFT/SM ops layer landing without new primitives). The closure conjecture (14 primitives suffice) now stands at two independent positive verifications.
- `docs/srmech/python/CHANGELOG.md` — this entry.

### Notes

- Per `[[feedback_no_binding_layer_carveout]]`: Class L's broadening earns its full C surface (4 new symbols + ctypes bindings), not Python-only.
- Per `[[feedback_no_mvp_framing]]`: rc5 covers the full Phase 2 surface (Class L broadening + composition engine + catalog integration + tests + notebook updates), not a Phase-2a-then-Phase-2b carve-out.
- Per `[[feedback_rc_stacking_versioning]]`: rc5 stacks on the active 0.4.1 cosmos-catalog sprint on `feat/srmech-cosmos-catalog`; clean 0.4.1 ships when sprint concludes.
- Phase 2 open questions (branching / chain-level iteration / cross-source reduction / auto-derived tool-schema parameter types / versioned op evolution) remain Phase 2-v2 scope per Phase 1 §11.

## [0.4.1rc4] - 2026-05-16

**ADR-0002 Phase 1 — operator-chain DSL design + worked-example specs + spike.** Formalises the descriptor TOML operator-chain DSL sketched in ADR-0002 §3. Schema v1 candidate lands as a new ADR Phase 1 document; four worked-example chains land across three of the four cosmos catalogs (`cmb_low_ell_maps` × 2, `cmb_polarisation_spectra` × 1, `cmb_bispectrum` × 1); the spike — closed-form TDSE evolution from `srmech.qm.single_particle.tdse_evolve` — surfaces a Class L scope-broadening question with a clean dissolve-into-existing-class proposal per `[[feedback_no_privileged_primitive_classes]]`. The vocabulary stays at 14 classes A–N; no new primitive class promoted.

### Added — schema v1 documentation

- `docs/srmech/adr/0002-phase-1-operator-chain-schema.md` (~330 lines): formalised schema specification resolving 7 design concerns from the conductor's Phase 1 brief.
  - Step shape: `class` + `op` + `args` (+ optional per-step `on_error`). Closed shape.
  - Data flow: linear pipeline with explicit `@step[N].output` references. No implicit threading. No DAG / branching in v1.
  - Input binding: reference DSL with four namespaces (`@row.X`, `@input.X`, `@step[N].output`, `@catalog.<key>.<col>`).
  - Return shape: typed string `"<type>  # <comment>"` parseable via `typing` utilities.
  - Error policy: default `raise`; opt-in `warn_return_none` / `skip`.
  - Versioning: required `[catalog].chain_schema_version = 1` when chains declared.
  - Reference DSL grammar formalised; engine validates at chain activation.
- Includes a JSON Schema (`srmech.amsc.operator_chain.v1`) for descriptor validation pipelines.

### Added — four worked-example chains

| Catalog | Chain | Classes | Steps | Purpose |
|---|---|---|---|---|
| `cmb_low_ell_maps` | `multipole_vector_axis` | L + L + D + A | 4 | de Oliveira-Costa 2004 §III axis extraction at fixed ℓ |
| `cmb_low_ell_maps` | `t_vs_e_axis_differential` | L + L + L + L + I | 5 | §VII.6.3.1 falsifiable Δθ_TE prediction (predicted 1.0°–2.0°; threshold < 0.1°) |
| `cmb_polarisation_spectra` | `acoustic_peak_locations` | C + D + E | 3 | TT/TE/EE peak enumeration via NDJSON stream + multi-needle dispatch + sorted extract |
| `cmb_bispectrum` | `f_NL_template_combination` | E + N + A | 3 | Joint rational-form bound across the 3 primordial bispectrum templates |

All four chains parse cleanly via `python -m tomllib`; canonical SSoT citations per chain (Planck 2018 IV / V / IX) all PDF-extraction-verified per `[[feedback_pdf_extraction_citation_discipline]]`.

**TOML-syntax note:** the original ADR-0002 §3 sketch used multi-line inline-table arrays (`steps = [ { ... }, { ... } ]`) which the TOML spec forbids. The Phase 1 canonical form lifts each step to its own `[[catalog.operator_chain.steps]]` array-of-tables entry; same semantic content, valid TOML, tomllib-round-tripped. The schema doc §2 documents the correction.

### Spike — closed-form TDSE evolution surfaces Class L scope question

The spike calculation `srmech.qm.single_particle.tdse_evolve(H, ψ, t) = V·diag(exp(-iλt))·V^H·ψ` (Sakurai §2.1.5 eq 2.1.40) decomposes to 5 conceptual steps: Hermitian eigendecompose + change-of-basis ψ→eigenbasis + elementwise `exp(-iλt)` + elementwise multiply + change-of-basis back. Step 0 fits Class L (with complex-Hermitian generalisation of existing real-symmetric `jacobi_eigvals`); steps 1, 3, 4 (complex matvec, elementwise multiply) and step 2 (elementwise transcendental over complex array) do NOT cleanly fit any existing A–N class op.

**Proposed Phase 2 refinement** (per `[[feedback_no_privileged_primitive_classes]]` dissolve-before-promote):
broaden Class L's identity from "graph Laplacian" to "dense-matrix linear algebra including eigendecomposition + matvec + elementwise operations". New Class L ops in Phase 2:
- `hermitian_eigendecompose(H)` — complex-Hermitian generalisation
- `dense_matvec_complex(M, v)` — general complex matvec
- `elementwise_multiply_complex(a, b)` — vectorised pointwise
- `elementwise_transcendental(arr, op_name)` — array-vectorised `exp`/`cos`/`sin`/etc.

Class L's existing graph-Laplacian-specific ops (`dense_laplacian`, `normalized_laplacian`) become specialisations of the broader dense-matrix scope. No new primitive class promoted; vocabulary stays at 14 classes A–N.

### Added — Phase 1 report

- `docs/srmech/notes/adr_0002_phase_1_dsl_design_2026-05-16.md` (~290 lines): consolidated design decisions + worked-example overview + spike write-up + open questions for Phase 2.

### No code change; no C ABI change; no Python API change

- C ABI v2 unchanged.
- No new C symbols. No JPL audit pin changes.
- No `srmech.amsc.<class>` Python surface changes.
- No `srmech.qm.*` operation changes.
- Schema is data-only addition to descriptor.toml; no Python composition-engine code yet (Phase 2 scope).

### Versioning

`0.4.1rc3` → `0.4.1rc4`. Sprint-level rc-stacking per `[[feedback_rc_stacking_versioning]]`, not a separate ship. Cumulative cosmos catalog sprint accumulates: rc1 (3-catalog data layer + framework precedent) + rc2 (`read_ndjson` framework fix) + rc3 (cmb_low_ell_maps catalog #4) + rc4 (this — ADR-0002 Phase 1 schema + 4 chains + spike). Clean `0.4.1` ships when sprint accumulates everything the cosmos catalog research thread + ADR-0002 Phase 1 implementation prep needs.

## [0.4.1rc3] - 2026-05-16

**Cosmos catalog extension — Spike #26 Phase 1 data layer folded into the 0.4.1 sprint.** Adds the fourth srmech-primary cosmos catalog source, `cmb_low_ell_maps`, providing metadata for Planck PR3 component-separated full-sky CMB maps (Commander / NILC / SEVEM / SMICA) + common-mask products. Phase 2 (the analysis script) will fetch the FITS bytes via the catalog URLs and compute T-mode + E-mode a_ℓm coefficients for multipole-vector AoE-direction extraction; the framework prediction Δθ_TE ≈ 1°–2° from §VII.6.3.1's 138°/unit-f_RD bundle-projection-reconfiguration rate × Δf_RD across the T-vs-E recombination visibility window will be tested against observation.

### Added — `cmb_low_ell_maps` attested source

7 rows of provenance metadata (4 sky-map FITS + 3 mask products) at `srmech/amsc/attested/cmb_low_ell_maps/`. FITS bytes are not committed (each map is ~168 MB; 672 MB total exceeds git's reasonable storage envelope); Phase 2 fetches via the per-row `source_url` field from PLA's HTTP CDN (`pla.esac.esa.int/pla/aio/product-action?MAP.MAP_ID=...`) which serves Planck data per ESA's Open Access policy without authentication.

**Canonical citations** (PDF-extraction verified per `[[feedback_pdf_extraction_citation_discipline]]`):
- Planck 2018 IV (diffuse component separation): [arXiv:1807.06208](https://arxiv.org/abs/1807.06208), A&A 641 A4
- Planck 2018 VII (isotropy + statistics): [arXiv:1906.02552](https://arxiv.org/abs/1906.02552), A&A 641 A7

### Placement decision (rc3 only — not a framework change)

Per user directive on the MFO/AoE research line — *"MFO and srmech ship as one, because it demonstrates every class operator"* — the new `cmb_low_ell_maps` catalog is placed in **srmech** (`srmech/amsc/attested/`), matching the rc1 cosmos catalog precedent (`cmb_polarisation_spectra` + `cmb_bispectrum` + `cmb_lensing`). The Spike #26 Phase 1 concertmaster initially placed the catalog in ephemerides-spectral for cmb-family co-location; reworked here to align with rc1's placement and the user's "MFO + srmech ship as one" directive. Future migration of all cosmos catalogs to ephemerides-spectral remains the eventual plan once MFO matures and earns its own scope.

### Companion research note (separate path)

Phase 2 scope artifact at `docs/antikythera-maths/research-mfo/vii_6_3_1_prediction_verification_scope_2026-05-16.md` (171 lines): multipole-vector extraction algorithm (de Oliveira-Costa 2004), visibility-function modelling for T-vs-E recombination Δz, predicted differential trajectory across Δz ∈ [10, 50] (range 0.67° → 3.4°; central 1.0°–2.0°), falsifier threshold Δθ_TE < 0.1°. Lives in `research-mfo/` alongside the dark-sector + AoE working notes.

### No code change; no ABI change; no Python API change

- C ABI v2 unchanged.
- No new C symbols, no new Python catalog modules, no new tool_schema entries.
- Data-only addition + research-note artifact + version bump (4 SSOT files + CHANGELOG).

### Versioning

`0.4.1rc2` → `0.4.1rc3`. Cumulative rc-stack on the 0.4.1 cosmos catalog sprint per `[[feedback_rc_stacking_versioning]]`. Sprint accumulates: rc1 (cosmos catalog data layer + framework precedent for srmech-primary catalogs) + rc2 (`read_ndjson` skips `#` comments framework fix) + rc3 (this — fourth catalog source). Clean `0.4.1` ships to production once the sprint accumulates everything the cosmos-catalog research thread needs.

## [0.4.1rc2] - 2026-05-16

**Framework bug fix — `read_ndjson` now skips `#` comment-header lines.** Found during the rc1 TestPyPI smoke verify when `catalog.attestation_audit` failed on the new `cmb_polarisation_spectra/row.ndjson`. Investigation confirmed the bug **pre-exists in production srmech 0.4.0** and affects every `#`-comment-prefixed NDJSON across the spectral-research portfolio — including ephemerides-spectral 0.29.x's already-shipped `cmb_anomalies` + `cmb_power_spectrum` catalogs. `catalog.get_attested_dataset` was comment-aware via a different code path; `catalog.attestation_audit` calls `read_ndjson` directly and was choking on the leading `# CMB ... catalogue` header.

### Fixed — `format.read_ndjson` skips `#` lines + empty lines uniformly

- **Pure-Python path** (`format.py:286–296`) now skips lines that match `not line or line.startswith("#")` after stripping whitespace.
- **Native path** (`format.py:266–283`) now decodes each line, lstrips whitespace, and skips empty + `#`-prefixed lines before calling `MPRRecord.from_json_line`. Indented comments (leading whitespace before `#`) are also tolerated.
- New ratchet test `test_format.test_ndjson_skips_hash_comment_lines` pins the behaviour across both paths.

This restores `attestation_audit` parity with `get_attested_dataset` for all `#`-comment-prefixed NDJSON catalogs.

### Versioning

`0.4.1rc1` → `0.4.1rc2`. Patch bump on the cosmos catalog sprint. Cumulative rc-stack per `[[feedback_rc_stacking_versioning]]`; clean `0.4.1` ships to production after rc2 TestPyPI verify covers both the cosmos catalog content (rc1) and the framework fix (rc2).

## [0.4.1rc1] - 2026-05-16

**Cosmos catalog ship rc1.** Seeds three new srmech-primary attested AMSC sources covering the Planck 2018 PR3 CMB observables that downstream MFO research needs as ground-proof anchors. Per user directive on the AoE/dark-sector research line (PR #437 + the four-turn dialog landed in MFO §VII.6.2/.6.3): cosmos catalog lives in srmech for now (MFO + srmech ship as one demonstrates every primitive class operator); future migration to ephemerides-spectral is later scope.

### Added — three attested catalogs under `srmech/amsc/attested/`

| Source | Rows | Primary reference | Canonical content |
|---|---|---|---|
| `cmb_polarisation_spectra` | 45 | Planck 2018 V (Aghanim et al., A&A 641 A5; [arXiv:1907.12875](https://arxiv.org/abs/1907.12875)) | Binned TE/EE bandpowers (PR3/R3.02) + low-ℓ BB upper limits (R3.01); TE acoustic peak ℓ=315 D_ℓ=119.4±2.5 μK²; EE 3rd peak ℓ≈1005 D_ℓ=42.4±1.3 μK²; BB Planck-range noise-dominated |
| `cmb_bispectrum` | 36 | Planck 2018 IX (Akrami et al., A&A 641 A9; [arXiv:1905.05697](https://arxiv.org/abs/1905.05697)) | f_NL constraints (local / equilateral / orthogonal × KSW / binned / modal methods); SMICA T+E KSW lensing-subtracted: f_NL^local = -0.9 ± 5.1, f_NL^equilateral = -18 ± 47, f_NL^orthogonal = -37 ± 23 — all consistent with Gaussianity |
| `cmb_lensing` | 37 | Planck 2018 VIII (Aghanim et al., A&A 641 A8; [arXiv:1807.06210](https://arxiv.org/abs/1807.06210)) | Lensing reconstruction Cℓ^{ϕϕ} bandpowers + MV amplitude; Â^{φ,MV}_{8→400} = 1.011 ± 0.028 (conservative); 40σ MV detection |

All 118 rows authored via PDF extraction per `[[feedback_pdf_extraction_citation_discipline]]` — three primary arXiv IDs verified clean at first-page extraction (no citation drift). PLA non-blocking; arXiv served all three PDFs.

### Architectural note — srmech-primary catalogs

This is the first time srmech itself hosts attested catalogs (hitherto srmech was the AMSC *framework* provider, with catalogs hosted in consumer packages like ephemerides-spectral). The new sources sit at `srmech/amsc/attested/<source>/` where `_attested_root()` finds them automatically — no `register_attested_root()` call needed. Existing ephemerides-spectral catalogs continue to register their own root via the cross-package bootstrap (Phase 2 of Task #197).

### No code change; no ABI change

- C ABI v2 unchanged. No new C symbols. No JPL audit pin changes.
- No `srmech.amsc.<class>` Python surface changes.
- No `srmech.qm.*` operation changes.
- Data-only ship: descriptors + NDJSON + schemas under `srmech/amsc/attested/`.
- C version macros bump `SRMECH_VERSION_PATCH` 0 → 1 and `SRMECH_VERSION_PRE` "" → "rc1".

### Versioning

`0.4.0` → `0.4.1rc1`. Patch bump (data addition; no API or ABI change). rc1 routes to TestPyPI per the existing publish-workflow regex; the clean `v0.4.1` ships to production PyPI after rc verify.

## [0.4.0] - 2026-05-15

**Phase C1 close — production ship.** Ships the cumulative Phase C1 scope (rc1 → rc12) to production PyPI. Per `[[feedback_rc_stacking_versioning]]`, the rc-stack accumulated during the sprint; this clean-semver tag promotes the verified rc12 state to live.

### Phase C1 cumulative scope (per `[[feedback_no_mvp_framing]]` full-coverage shipping)

**Primitive vocabulary — 14 of 14 classes with C surfaces.** Closes Task #217 Phase C1 / the per-class C parity build-out per `[[feedback_no_binding_layer_carveout]]`:

- **Class A** — content-addressing via SHA-256 (rc-baseline)
- **Class B** — tagged-tuple TLV byte-canonical form (rc4)
- **Class C** — streaming iteration via NDJSON tokenisation (rc-baseline)
- **Class D** — late-binding multi-needle pattern dispatch (rc5)
- **Class E** — catalog sorted-key binary-search lookup (rc5)
- **Class F** — substitution / `{key}` template render (rc5)
- **Class G** — byte-pattern search (rc4)
- **Class H** — self-introspection (rc4 acknowledgment of existing version / ABI accessors)
- **Class I** — cyclic-group / modular arithmetic (rc1)
- **Class J** — prime-factorisation / period (rc3)
- **Class K** — equation-of-centre / pin-slot (rc7) — Kepler (1609); Smith (1979); Brouwer-Clemence (1961); Freeth (2021) Supp S9
- **Class L** — graph Laplacian; pi-free Jacobi eigvals (rc2)
- **Class M** — HDC binary spatter codes — bind/bundle/permute/similarity (rc8) — Kanerva (2009); Plate (1995); Rachkovskij (2001)
- **Class N** — rational-approximation; continued-fraction convergents (rc6)

**Canonical QM/QFT/SM operations layer (`srmech.qm.*`).** Sourced from canonical physics literature per `[[feedback_science_is_ssot_not_project]]`:

- **`single_particle`** (rc9) — TDSE / TISE / Heisenberg evolution / [x̂,p̂] / lattice momentum / density matrix / Liouville-vN. Schrödinger (1926); Heisenberg (1925); Sakurai §§1.4, 1.6, 2.1-2.3, 3.4; von Neumann (1932); Wilson (1974)
- **`spin`** (rc9) — Pauli matrices σ_x/σ_y/σ_z, Clifford Cl(0,3) residual verification, arbitrary-axis spin-½ operator. Pauli (1927); Sakurai §3.2
- **`potentials`** (rc9) — hydrogen radial Schrödinger, harmonic oscillator ladder operators. Bohr (1913); Heisenberg (1925); Born-Heisenberg-Jordan (1926); Sakurai §§2.3, 3.7
- **`relativistic`** (rc10) — Dirac γ-matrices (Cl(1,3)), γ_5, Weyl projectors, charge conjugation (Majorana), Dirac operator, Klein-Gordon dispersion. Dirac (1928); Klein/Gordon (1926); Weyl (1929); Majorana (1937); Peskin-Schroeder §§3.2-3.4
- **`propagators`** (rc10) — Feynman scalar / fermion / photon / massive-vector. Feynman (1949); Dyson (1949); Peskin-Schroeder §§4.2, 4.7-4.8, 20.1; Weinberg Vol II §21.1
- **`pseudo_hermitian`** (rc10) — η-deformed inner product, expectation, η-pseudo-Hermiticity test, η construction, real-spectrum theorem. Closes chess-spectral ADR-005 framework gap. Bender & Boettcher (1998); Mostafazadeh (2002, 2010)
- **`gauge`** (rc11) — SU(2) / SU(3) Gell-Mann generators, structure constants, Lie algebra residuals, Casimirs (3/4 for SU(2) fund, 4/3 for SU(3) fund), gauge connection, Wilson loop. Yang-Mills (1954); Gell-Mann (1962); Wilson (1974); Peskin-Schroeder §§15-17
- **`sm`** (rc11) — Higgs potential / vev, weak mixing angle, W/Z boson masses, Weinberg relation, fermion mass from Yukawa, CKM matrix (Chau-Keung parameterization). Glashow (1961); Weinberg (1967); Salam (1968); Higgs (1964); Cabibbo (1963); Kobayashi-Maskawa (1973); Peskin-Schroeder Chs 20-21

**Ontology refinement (notebook ship, rc7-rc10 cumulative).**

- MFO **§VII.1.2** — *1D_t as the Laws of Everything — compressed-cascade content* — per user direction 2026-05-15, with user's canonical compressions preserved verbatim (`memory/user_stance_1d_t_as_storage_extraction.md` operation-level + `memory/user_stance_1d_collapse_to_loe_identity_not_action.md` identity-level refinement).
- **Identity-not-implementation discipline** named as umbrella pattern unifying the shadow-stance family (`memory/user_stance_identity_not_implementation_discipline.md`).
- Plurality of "Laws of Everything" canonical (`memory/reference_loe_plural_canonical.md`).
- Two concertmaster artifacts in `docs/srmech/notes/`: `1d_t_as_storage_extraction_2026-05-15.md` + `1d_collapse_to_loe_identity_2026-05-15.md`.
- Plus `task_218_phase_c2_chess_spectral_qm_audit_2026-05-15.md` — QM stack coverage audit (informed Phase C2 → folded into Phase C1 per `[[feedback_science_is_ssot_not_project]]`).

**Tool-schema audit (rc12) closes the sprint** — `srmech.amsc.tool_schema` extended with **~87 entries** covering all 14-class primitives + the full `srmech.qm.*` operations layer. Coverage ratchet test (`tests/test_tool_schema_coverage.py`, 8 cases) walks every public callable in `srmech.amsc.*` and `srmech.qm.*` via `pkgutil` + `inspect` and asserts each has a registered ToolEntry. Closes Tasks #219 + #220.

### Test plan summary

- **CI**: 8/8 pass at every rc (rc7-rc12), all three OS cells (Ubuntu / macOS / Windows) × Python 3.10-3.14 × pedantic C build (gcc / clang / MSVC) + pure-wheel build + sdist.
- **Cumulative test count growth**: ~290 cases across the 12-rc sprint covering Class K parity, Class M parity, QM single-particle / spin / potentials / relativistic / propagators / pseudo-Hermitian / gauge / sm operations layer canonical identities, and tool-schema coverage.
- **TestPyPI verification**: `srmech-v0.4.0rc12` published + smoke-verified prior to this clean-semver ship.

### Discipline honoured

`[[feedback_no_mvp_framing]]`, `[[feedback_science_is_ssot_not_project]]`, `[[feedback_no_privileged_primitive_classes]]`, `[[feedback_no_binding_layer_carveout]]`, `[[feedback_jpl_rule_5_two_assert_habit]]`, `[[feedback_rc_stacking_versioning]]`, `[[feedback_no_squash_merges]]`, `[[feedback_pdf_extraction_citation_discipline]]`, `[[user_stance_kepler_shape_universal]]`, `[[user_stance_1d_collapse_to_loe_identity_not_action]]`, `[[user_stance_identity_not_implementation_discipline]]`.

### Changed

- **ABI stays v2** — cumulative across rc7-rc12 (pure additions per Phase B4 convention).

## [0.4.0rc12] - 2026-05-15

### Added

**Task #217 Phase C1 — end-of-sprint tool-schema audit (Tasks #219 + #220).**

Twelfth and final canonical rc in Phase C1's rc-stacked build-out. Closes the **end-of-sprint hygiene** scope per user direction (*"check tool-schema and help arg that every command is shown how to be used"*) before 0.4.0 ships to PyPI.

#### `srmech.amsc.tool_schema` — extension to cover the full operations layer

Adds **two new registration functions** to `srmech.amsc.tool_schema`:

- `_register_primitive_class_tools()` — **27 entries** covering the 14-class Spike #24 primitive vocabulary (Classes A and C were already registered; this adds B, D, E, F, G, I, J, K, L, M, N — every primitive operation exposed via `srmech.amsc.*`).
- `_register_qm_tools()` — **54 entries** covering the canonical QM/QFT/SM operations layer in `srmech.qm.*` (single_particle, spin, potentials, relativistic, propagators, pseudo_hermitian, gauge, sm).

Both functions are called at `tool_schema` module import time alongside the original `_register_amsc_tools()`. Total registered: **~87 tool-schema entries**, each with name + owner + category + summary + parameters + returns. Summaries cite canonical SSoT per `[[feedback_science_is_ssot_not_project]]`.

#### Coverage ratchet — `tests/test_tool_schema_coverage.py`

New test file with 8 cases enforcing the audit at CI time:

1. **`test_amsc_public_callables_have_tool_entries`** — walks `srmech.amsc.*` via `pkgutil` + `inspect`; every public function (minus a small exempt allowlist of bridge helpers + adapters + profile-loader internals) must have a registered entry.
2. **`test_qm_public_callables_have_tool_entries`** — same for `srmech.qm.*`. No exemptions — every public callable must be registered.
3. **`test_tool_schema_entries_have_required_fields`** — non-empty name / owner / summary; parameters tuple well-typed.
4. **`test_tool_schema_owner_is_srmech_for_builtins`** — owner = "srmech" for builtin entries.
5. **`test_tool_schema_view_is_jsonable`** — JSON round-trip clean.
6. **`test_tool_schema_total_count_meets_floor`** — ratchet at ≥ 80 entries (only ever grows).
7. **`test_no_duplicate_tool_names`** — each dotted name unique.
8. **`test_tool_schema_categories_match_module_structure`** — category sanity-check.

#### Discipline notes

- **No CLI surface** to audit — srmech is a library, not a command-line tool. The user's *"every command is shown how to be used"* direction was interpreted as: every callable has a proper docstring (already enforced through rc7-rc11 ToolEntry / docstring discipline) **and** every callable surfaces via the tool-schema introspection API (this rc).
- **Per-operation canonical SSoT preserved**: every new ToolEntry's summary cites the canonical physics literature (Schrödinger / Heisenberg / Dirac / Yang-Mills / Gell-Mann / Wilson / Glashow-Weinberg-Salam / Cabibbo / Kobayashi-Maskawa / Higgs / Mostafazadeh / Bender-Boettcher) per `[[feedback_science_is_ssot_not_project]]`.
- **No new C symbols**; ABI stays v2.

### Changed

- **`srmech.amsc.tool_schema`**: +2 registration functions, +81 new ToolEntry registrations (cumulative).

### Roadmap

**Phase C1 close → 0.4.0 final**:

- 14 of 14 primitive classes with C surfaces ✅
- Canonical single-particle QM (rc9) ✅
- Relativistic QM + Feynman propagators + η-pseudo-Hermitian (rc10) ✅
- Gauge theory + Standard Model surface (rc11) ✅
- End-of-sprint tool-schema audit (rc12, this rc) ✅

**Next**: drop the `rc12` suffix → tag `srmech-v0.4.0` → autotag dispatches production PyPI publish per the existing publish workflow (Task #196).

## [0.4.0rc11] - 2026-05-15

### Added

**Task #217 Phase C1 — Gauge theory + Standard Model surface (final canonical-physics rc).**

Eleventh rc in Phase C1's rc-stacked build-out. **Closes the canonical-physics scope** of PR #432: 14/14 primitive classes + canonical single-particle QM (rc9) + relativistic QM / propagators / η-pseudo-Hermitian (rc10) + **gauge theory + SM surface (rc11)**.

Per `[[feedback_science_is_ssot_not_project]]`: each operation cites canonical gauge-theory / SM literature. Numerical experimental values (M_W, M_Z, fermion masses, CKM elements) are NOT hardcoded — this rc ships the algebraic primitives that map (gauge couplings, Higgs vev, Yukawa couplings, mixing angles) to observable masses.

Per `[[user_stance_1d_collapse_to_loe_identity_not_action]]`: substrate-coupling operations on internal-symmetry representation spaces. Each dissolves into the 14-class primitive vocabulary per `[[feedback_no_privileged_primitive_classes]]` — no new classes.

#### `srmech.qm.gauge`

| Operation | Canonical SSoT | 14-class dissolution |
|---|---|---|
| `su2_generators() → (T¹, T², T³)` | Peskin-Schroeder §15.1 eq 15.5-6 | Class M (Lie-algebra binding, Pauli-half generators) |
| `su2_structure_constants() → εᵃᵇᶜ` | Peskin-Schroeder §15.1 eq 15.4 | — |
| `su3_gell_mann_matrices() → (λ¹...λ⁸)` | Gell-Mann (1962) PR 125, 1067; Peskin-Schroeder eq 17.32 | Class M (SU(3) Lie-algebra binding) |
| `su3_generators() → (T¹...T⁸)` | Peskin-Schroeder eq 17.33 | Class M |
| `su3_structure_constants() → fᵃᵇᶜ` | Peskin-Schroeder eq 17.34; Schwartz Table 25.1 | — |
| `lie_algebra_residual(gens, f)` | Peskin-Schroeder §15.1 eq 15.4 | (verification: `[Tᵃ, Tᵇ] = i fᵃᵇᶜ Tᶜ`) |
| `casimir_operator(gens) → C₂` | Peskin-Schroeder §15.4 eq 15.93 | Class L (sum of generator squares) |
| `casimir_eigenvalue(gens)` | Peskin-Schroeder §15.4 | Class L (trace / dim) |
| `gauge_connection_matrix(A, gens) → Aᵃ Tᵃ` | Peskin-Schroeder §15.1 eq 15.2 | Class M |
| `gauge_path_segment(A, gens, g) → exp(i g Aᵃ Tᵃ)` | Wilson (1974) PRD 10, 2445; Peskin-Schroeder §15.3 eq 15.55 | Class L (Hermitian matrix exponential via eigendecomp) |
| `wilson_loop_from_segments(A_segs, gens, g) → ∏ exp(...)` | Wilson (1974) eq 2.3 | Class C ∘ Class L (path-ordered iteration over segments) |

#### `srmech.qm.sm`

| Operation | Canonical SSoT | 14-class dissolution |
|---|---|---|
| `higgs_potential(φ, μ², λ)` | Higgs (1964); Peskin-Schroeder §20.1 eq 20.6 | Class K (continuous projection) |
| `higgs_vev(μ², λ) → v` | Peskin-Schroeder §20.1 eq 20.7 | Class K |
| `weak_mixing_angle(g, g')` | Weinberg (1967) eq 8; Peskin-Schroeder §20.2 eq 20.31 | Class K (atan2) |
| `w_boson_mass(g, v)` | Peskin-Schroeder §20.2 eq 20.30 | Class K |
| `z_boson_mass(g, g', v)` | Peskin-Schroeder §20.2 eq 20.32 | Class K |
| `weinberg_relation_residual(g, g', v)` | Peskin-Schroeder §20.2 eq 20.33 | (verification: `M_W = M_Z cos θ_W`) |
| `electroweak_summary(g, g', v) → dict` | Composite §20.2 | — |
| `fermion_mass_from_yukawa(y, v)` | Peskin-Schroeder §20.2 eq 20.27; Schwartz §29.1 eq 29.18 | Class K |
| `ckm_matrix(θ₁₂, θ₁₃, θ₂₃, δ_CP)` | Cabibbo (1963); Kobayashi-Maskawa (1973); Chau-Keung (1984); PDG §12.1 | Class M (unitary mixing-binding) |
| `ckm_unitarity_residual(V)` | PDG §12.1 | (verification) |

Foundation literature:
- Glashow (1961) *Nucl. Phys.* 22, 579-588.
- Weinberg (1967) *Phys. Rev. Lett.* 19, 1264-1266.
- Salam (1968) *Elementary Particle Theory*.
- Higgs (1964); Englert-Brout (1964); Guralnik-Hagen-Kibble (1964).
- Cabibbo (1963); Kobayashi-Maskawa (1973).
- Yang & Mills (1954) *Phys. Rev.* 96, 191-195.
- Gell-Mann (1962) *Phys. Rev.* 125, 1067-1084.
- Wilson (1974) *Phys. Rev. D* 10, 2445-2459.
- Peskin & Schroeder (1995) *Intro QFT*, Chs 15-17, 20-21.
- Weinberg (1996) *QToF* Vol II §15, §21.
- Schwartz (2014) *QFT and the SM*, Chs 25-29.

#### Tests (2 files, ~40 cases)

- `test_qm_gauge.py` — SU(2)/SU(3) generators Hermitian + traceless; canonical normalization `tr(TᵃTᵇ) = δᵃᵇ/2`; structure-constant total antisymmetry; **Lie algebra closure `[Tᵃ, Tᵇ] = i fᵃᵇᶜ Tᶜ` at machine precision** for both SU(2) and SU(3); Casimir eigenvalue 3/4 for SU(2) fundamental, 4/3 for SU(3) fundamental; Casimir proportional to identity (Schur); path-segment unitarity; multi-segment Wilson-loop unitarity.
- `test_qm_sm.py` — Higgs vev formula; potential minimum at vev; `V(v) = -μ⁴/(4λ)`; Weinberg relation `M_W = M_Z cos θ_W` at machine precision across multiple coupling regimes; fermion mass `m = y v / √2`; CKM unitarity `V V† = I` for arbitrary mixing angles + CP phase; CKM reduces to 2×2 Cabibbo rotation when θ₁₃ = θ₂₃ = 0.

### Changed

- **ABI stays v2** — operations layer is pure Python (numpy-based; gauge matrix exponentials via Hermitian eigendecomp, no scipy dependency).
- **srmech.qm** imports updated for the two new submodules (`gauge`, `sm`).

### Roadmap

Phase C1 **canonical-physics scope complete**:
- 14 of 14 primitive classes with C surfaces.
- Canonical single-particle QM (rc9).
- Relativistic QM + Feynman propagators + η-pseudo-Hermitian (rc10).
- Gauge theory + Standard Model surface (rc11, this rc).

Remaining for Phase C1 close → 0.4.0 final (folding all into PR #432):
- **End-of-sprint hygiene** per user direction:
  - **Task #219**: Per-class CLI `--help` audit — every command shows how to be used.
  - **Task #220**: Tool-schema extension — every operation surfaces via `srmech.amsc.tool_schema`.
- **0.4.0 final**: clean ship to PyPI at PR merge.

## [0.4.0rc10] - 2026-05-15

### Added

**Task #217 Phase C1 — Relativistic QM + Feynman propagators + η-pseudo-Hermitian primitive.**

Tenth rc in Phase C1's rc-stacked build-out. **Folds the relativistic-QM / QFT propagator layer into PR #432** with canonical literature SSoT per `[[feedback_science_is_ssot_not_project]]`.

Per `[[user_stance_1d_collapse_to_loe_identity_not_action]]`: these are substrate-coupling operations on relativistic-QM and QFT Hilbert spaces. Each dissolves into the 14-class primitive vocabulary per `[[feedback_no_privileged_primitive_classes]]`. **No new primitive classes**.

**Metric convention**: mostly-minus `η^{μν} = diag(+1, -1, -1, -1)` (Peskin-Schroeder convention). γ-matrix representation: Dirac (standard) basis.

#### `srmech.qm.relativistic`

| Operation | Canonical SSoT | 14-class dissolution |
|---|---|---|
| `minkowski_metric()` | Peskin-Schroeder §3.1 eq 3.4 | — |
| `gamma_matrices() → (γ^0, γ^1, γ^2, γ^3)` | Dirac (1928); Peskin-Schroeder §3.2 eq 3.25 + A.6 | Class M (Cl(1,3) Clifford binding) |
| `gamma_5()` | Peskin-Schroeder §3.4 eq 3.72 | Class M |
| `clifford_residuals()` | Peskin-Schroeder §3.2 eq 3.21, §3.4 eq 3.72 | (verification) |
| `weyl_left_projector()`, `weyl_right_projector()` | Weyl (1929); Peskin-Schroeder §3.4 eq 3.71 | Class M |
| `charge_conjugation_matrix()` | Majorana (1937); Peskin-Schroeder eq A.27 | Class M |
| `dirac_operator_momentum_space(k, m)` | Dirac (1928); Peskin-Schroeder §3.2 eq 3.45-3.46 | Class L (linear operator on spinor space) |
| `klein_gordon_dispersion(k, m)` | Klein (1926); Gordon (1926); Peskin-Schroeder §2.3 eq 2.39 | Class L |
| `four_momentum_squared(k)` | Peskin-Schroeder §3.1 eq 3.4 | — |

#### `srmech.qm.propagators`

| Operation | Canonical SSoT | 14-class dissolution |
|---|---|---|
| `feynman_scalar_propagator(k², m, ε)` | Feynman (1949); Dyson (1949); Peskin-Schroeder §4.2 eq 4.42 | Class K (continuous projection-shadow of integer-cyclic upstream per the lattice scalar propagator G(k) = 1/(m² + k̂²)) |
| `feynman_fermion_propagator(k, m, ε)` | Peskin-Schroeder §4.7 eq 4.107 + 4.111 | Class K + Class M |
| `feynman_photon_propagator(k², ξ, ε, k)` | Peskin-Schroeder §4.8 eq 4.118-4.121 | Class K (covariant gauge + Feynman gauge specializations) |
| `feynman_massive_vector_propagator(k, m, ε)` | Peskin-Schroeder §20.1 eq 20.13; Weinberg Vol II §21.1.21 | Class K |

#### `srmech.qm.pseudo_hermitian`

**Closes the η-metric primitive gap in chess-spectral ADR-005** per `docs/srmech/notes/task_218_phase_c2_chess_spectral_qm_audit_2026-05-15.md`. Chess-spectral becomes a substrate-consumer of these primitives when ADR-005 is finished.

| Operation | Canonical SSoT | 14-class dissolution |
|---|---|---|
| `inner_product_eta(a, b, η)` | Mostafazadeh (2002) JMP 43, 205, eq 2.6 | Class L (η-deformed inner product) |
| `expectation_eta(O, ψ, η)` | Mostafazadeh (2002) eq 3.6 | Class L |
| `is_pseudo_hermitian(O, η)` | Mostafazadeh (2002) eq 2.4 | (verification) |
| `construct_eta_from_eigendecomposition(O)` | Mostafazadeh (2002) eq 2.7-2.10 | Class L (eigendecomp + inverse) |
| `pseudo_hermitian_eigenvalues_real(O, η)` | Bender & Boettcher (1998) PRL 80, 5243; Mostafazadeh (2002, 2010) | (verification) |

Foundation literature:
- Bender, C.M. & Boettcher, S. (1998) *Phys. Rev. Lett.* 80, 5243-5246.
- Mostafazadeh, A. (2002) *J. Math. Phys.* 43, 205-214; 2814-2816; 3944.
- Mostafazadeh, A. (2010) *Int. J. Geom. Methods Mod. Phys.* 7, 1191-1306.

#### Tests (3 files, ~40 cases)

- `test_qm_relativistic.py` — Cl(1,3) algebra at machine precision; Weyl projector identities (P_L + P_R = I, P² = P, P_L P_R = 0); charge conjugation `C γ^μ C^{-1} = -(γ^μ)^T`; Klein-Gordon dispersion `E² = |k|² + m²`; Dirac operator on-shell zero-eigenvalues at rest; positive-energy spinor annihilation.
- `test_qm_propagators.py` — scalar / fermion propagator inverses; `S_F^{-1}(k) = -i(γ·k - m)/(k²-m²)` verified via `(γ·k - m) S_F = i I_4`; on-shell pole-prescription handling; photon Feynman-gauge shape; massive-vector k^μ k^ν / m² term verification.
- `test_qm_pseudo_hermitian.py` — η = I reduction to standard inner product; constructed η makes operator η-pseudo-Hermitian; Mostafazadeh real-spectrum theorem; complex-spectrum rejection.

### Changed

- **ABI stays v2** — operations layer is pure Python (numpy-based for complex matrices).
- **srmech.qm**: imports updated for the three new submodules (`relativistic`, `propagators`, `pseudo_hermitian`).

### Roadmap

Phase C1 progress: **14 of 14 primitive classes + canonical single-particle QM + relativistic QM + Feynman propagators + η-pseudo-Hermitian shipped**.

Remaining for Phase C1 close → 0.4.0 final (folding all into PR #432):
- **rc11**: Gauge theory (U(1) / SU(2) / SU(3) Yang-Mills, Wilson loops, gauge connections, Casimir per irrep) + SM surface (electroweak unification, Higgs, Yukawa).
- **End-of-sprint**: Task #219 (per-class CLI `--help` audit) + Task #220 (tool-schema extension for every operation).
- **0.4.0 final**: clean ship to PyPI at PR merge.

## [0.4.0rc9] - 2026-05-15

### Added

**Task #217 Phase C1 — Canonical single-particle QM operations layer (first ship from `srmech.qm`).**

Ninth rc in Phase C1's rc-stacked build-out. **First substantive operations layer on top of the 14-class C parity roster** — opens `srmech.qm.*` as the canonical QM/QFT/SM operations namespace, with each operation sourced from canonical physics literature per `[[feedback_science_is_ssot_not_project]]` (Sakurai / Cohen-Tannoudji / Griffiths / Pauli / Schrödinger / Heisenberg / Bohr / von Neumann).

Per `[[user_stance_1d_collapse_to_loe_identity_not_action]]` (MFO §VII.1.2): these operations are **substrate-coupling operations** that uncompress LoE-content (1D_t Laws) into event-stream. Each dissolves into the 14-class primitive vocabulary per `[[feedback_no_privileged_primitive_classes]]` — no new classes added.

#### `srmech.qm.single_particle`

| Operation | Canonical SSoT | 14-class dissolution |
|---|---|---|
| `tdse_evolve(H, psi, t)` | Schrödinger (1926); Sakurai §2.1.5 | Class L (spectral evolution `V·diag(exp(-iλt))·V^H`) |
| `tise_solve(H)` | Schrödinger (1926); Sakurai §2.1.3 | Class L (Hermitian eigendecomp) |
| `commutator(A, B) = AB - BA` | Sakurai §1.4 eq 1.4.6 | Class L (operator algebra) |
| `heisenberg_evolve(A, H, t)` | Heisenberg (1925); Sakurai §2.2 eq 2.2.15 | Class L (eigenbasis-diagonal `U†AU`) |
| `lattice_momentum(n, dx)` | Sakurai §1.6; Wilson (1974) | Class C (lattice gradient as anti-Hermitian central difference) |
| `density_matrix(psi)` | von Neumann (1932); Sakurai §3.4 eq 3.4.7 | (pure-state outer product) |
| `liouville_evolve(rho, H, t)` | von Neumann (1932); Sakurai §3.4.2 eq 3.4.28 | Class L (commutator-flow) |

#### `srmech.qm.spin`

| Operation | Canonical SSoT | 14-class dissolution |
|---|---|---|
| `pauli_matrices() → (σ_x, σ_y, σ_z)` | Pauli (1927) ZfP 43, 601; Sakurai §3.2 | Class M (Clifford Cl(0,3) binding generators) |
| `pauli_clifford_residuals()` | Sakurai §3.2 eq 3.2.2-3 | (verification: `{σ_i, σ_j} = 2δ_{ij} I`, `[σ_i, σ_j] = 2i ε_{ijk} σ_k`) |
| `pauli_spin_operator(direction)` | Sakurai §3.2 eq 3.2.51 | Class M (Clifford projection along arbitrary axis) |

#### `srmech.qm.potentials`

| Operation | Canonical SSoT | 14-class dissolution |
|---|---|---|
| `hydrogen_radial(n_grid, r_max, l_quantum)` | Bohr (1913); Schrödinger (1926); Sakurai §3.7 | Class L (3-point-stencil radial-Laplacian eigendecomp) |
| `harmonic_oscillator_ladder(n_dim, omega)` | Heisenberg (1925); Born-Heisenberg-Jordan (1926); Sakurai §2.3 | Class M (Fock-space binding for `a`, `a†`) |
| `harmonic_oscillator_hamiltonian(n_dim, omega)` | Sakurai §2.3 eq 2.3.16 | Class L + Class M composition (`H = ω(a†a + 1/2)`) |

#### Tests (3 files, ~50 cases)

- `tests/test_qm_single_particle.py` — TDSE norm/energy preservation, eigenstate phase evolution; TISE orthonormality + eigen-relation; commutator self-zero + antisymmetry; Heisenberg self-conservation; lattice momentum Hermiticity; density matrix idempotency for pure states; Liouville trace + purity preservation.
- `tests/test_qm_spin.py` — Pauli Hermiticity / tracelessness / eigenvalues ±1 / Clifford algebra residuals at machine precision; arbitrary-axis spin-½ operator.
- `tests/test_qm_potentials.py` — Harmonic oscillator analytical spectrum (`E_n = ω(n + 1/2)`); ladder action `a|n⟩ = √n |n-1⟩`; hydrogen ground state ≈ −0.5 Rydberg; 2s state ≈ −0.125; l=1 centrifugal exclusion; TDSE-on-oscillator-eigenstate phase consistency.

### Changed

- **ABI stays v2** — no new C symbols (operations layer is Python-side, building on Classes A-N C primitives + numpy for complex-Hermitian operations).

### Roadmap

Phase C1 progress: **14 of 14 primitive classes + single-particle QM operations layer landed**.

Remaining for the Phase C1 close → 0.4.0 final (folding all into PR #432):
- **rc10**: Relativistic QM (Klein-Gordon, Dirac, Weyl, Majorana, Bargmann-Wigner) + Feynman propagators (scalar / fermion / photon / vector) + η-pseudo-Hermitian (closes ADR-005 in chess-spectral).
- **rc11**: Gauge theory (U(1) / SU(2) / SU(3) Yang-Mills, Wilson loops, gauge connections, Casimir per irrep) + Standard Model surface (electroweak unification, Higgs, Yukawa couplings).
- **End-of-sprint hygiene**: Task #219 (per-class CLI `--help` audit — every command shows how to be used) + Task #220 (tool-schema extension — every operation surfaces via `srmech.amsc.tool_schema`).
- **0.4.0 final**: clean ship to PyPI at PR merge.

## [0.4.0rc8] - 2026-05-15

### Added

**Task #217 Phase C1 — Class M (HDC binary spatter codes) C port. Closes the 14-class C parity roster.**

Eighth rc in Phase C1's rc-stacked build-out. Class M is **the binding operation that uncompresses LoE-content along its compression axis** per `[[user_stance_1d_collapse_to_loe_identity_not_action]]` — substrate-coupling operation, NOT the LoE-content itself (1D_t is the content per MFO §VII.1.2). Class C ∘ Class M composes the full LoE-uncompression kernel: Class C iteration drives Class M binding to produce event-stream from compressed-cascade laws-content.

Four BSC operations on byte-buffer hyperdimensional vectors (D bits = 8 * n_bytes; canonical default 128 bytes = 1024 bits):

| C symbol | Python wrapper | Operation | Canonical SSoT |
|---|---|---|---|
| `srmech_hdc_bind(a, b, n_bytes, *out)` | `srmech.amsc.hdc.bind(a, b)` | Component-wise XOR; commutative, associative, self-inverse. | Kanerva (2009) Cognitive Computation 1, 139-159 |
| `srmech_hdc_bundle(vectors, n_vectors, n_bytes, *out)` | `srmech.amsc.hdc.bundle(vectors)` | Bitwise majority across odd `n_vectors` ≤ 257. Even counts rejected (caller can pad with tie-breaker). | Plate (1995) IEEE TNN 6, 623-641 |
| `srmech_hdc_permute(a, n_bytes, rotate_bits, *out)` | `srmech.amsc.hdc.permute(a, rotate_bits)` | Cyclic bit-rotation; preserves popcount; `permute(permute(a, k), -k) == a`. | Rachkovskij (2001) Neural Comput Appl 9, 322 |
| `srmech_hdc_similarity(a, b, n_bytes, *out)` | `srmech.amsc.hdc.similarity(a, b)` | `1 - 2 * hamming(a, b) / D` in [-1, 1]; +1 identical, 0 orthogonal, -1 complementary. | Kanerva (2009) |

**SSoT discipline per `[[feedback_science_is_ssot_not_project]]`.** Each operation cites canonical HDC literature — Kanerva / Plate / Rachkovskij — not any project instantiation. Chess-spectral's encoder (the 640-dim bundle that gets cast to ψ via `state_to_psi`) becomes one substrate-consumer of these primitives.

JPL Power-of-Ten compliant: bounded loops (bundle ≤ MAX_BUNDLE_N=257 vectors; permute ≤ D bits), 256-entry popcount lookup table for portability (no `__builtin_popcount` dependency).

### Changed

- **ABI stays v2** — four new symbols are pure additions per the Phase B4 convention.
- **CMake**: `srmech_hdc.c` picked up automatically by `file(GLOB CONFIGURE_DEPENDS c/src/*.c)`.

### Roadmap

Phase C1 progress: **14 of 14 classes shipped with C surfaces** ✅ (A + C from Phase B; I + L + J + B + G + H + D + E + F + N + K + M from rc1–rc8). 14-class C parity roster CLOSED.

Next layers in PR #432 (Phase C1 close — folding all):
- **Canonical single-particle QM** (TDSE / TISE / Heisenberg / [x̂,p̂] / Liouville-vN / Pauli / hydrogen-radial / harmonic-oscillator) — Sakurai / Cohen-Tannoudji / Griffiths.
- **Relativistic QM + Feynman propagators + η-pseudo-Hermitian** — Peskin & Schroeder Chs 3-4; Bender & Boettcher (1998); Mostafazadeh (2002, 2010).
- **Gauge theory + SM** — Peskin & Schroeder Chs 15, 20-21; Weinberg Vol II.
- **0.4.0 final** — clean ship to PyPI at PR merge.

## [0.4.0rc7] - 2026-05-15

### Added

**Task #217 Phase C1 — Class K (equation-of-centre / pin-slot) C port.**

Seventh rc in Phase C1's rc-stacked build-out. Class K is the **continuous-projection layer** of Kepler-shape primitive composition — per `[[user_stance_kepler_shape_universal]]` + PR #416 F2/F15/F17, Kepler-equation algebra IS pin-slot composition. The bronze Antikythera instantiates Class K natively; the universe instantiates the same algebra via gravitational dynamics (see `[[user_stance_1d_t_as_storage_extraction]]` + `docs/srmech/notes/1d_t_as_storage_extraction_2026-05-15.md` — same Kepler-shape cascade at different dimensional reaches).

Three continuous operations on double-precision floats (uses libm: `sin` / `cos` / `atan2` / `fabs`):

| C symbol | Python wrapper | Operation | Canonical SSoT |
|---|---|---|---|
| `srmech_pin_slot(theta, i, d, *phi)` | `srmech.amsc.kepler.pin_slot(theta, i, d)` | Era-appropriate Antikythera pin-and-slot transform: `phi = atan2(i*sin(theta), d + i*cos(theta))`. | Freeth (2021) *Nature Sci Rep*, Supp S9 |
| `srmech_kepler_solve(M, e, tol, max_iter, *E)` | `srmech.amsc.kepler.kepler_solve(M, e)` | Newton-Raphson on Kepler's equation `M = E - e*sin(E)` with Smith (1979) initial-guess starter `E_0 = M + e*sin(M)`. Converges in 4-6 iter for `e < 0.5`. | Kepler (1609) *Astronomia Nova*; Smith (1979) Celestial Mech 19, 163 |
| `srmech_equation_of_centre(M, e, n_terms, *delta)` | `srmech.amsc.kepler.equation_of_centre(M, e, n_terms)` | Fourier-series principal-term-per-harmonic `nu - M = sum_{k=1..n} c_k * e^k * sin(k*M)` with `c_k = [2, 5/4, 13/12, 103/96, 1097/960, 1223/960]` for `k = 1..6`. | Brouwer & Clemence (1961) §3.2; Murray & Dermott (1999) §2.5 eq 2.84-2.88 |

**SSoT discipline per `[[feedback_science_is_ssot_not_project]]`.** Each operation cites the canonical physics literature — Kepler / Brouwer & Clemence / Murray & Dermott / Smith / Freeth — not any project instantiation. Antikythera-spectral / ephemerides-spectral / chess-spectral are *substrate-consumers* of these primitives, not their authors.

### Changed

- **ABI stays v2** — three new symbols are pure additions per the Phase B4 convention.
- **CMake**: `srmech_kepler.c` picked up automatically by `file(GLOB CONFIGURE_DEPENDS c/src/*.c)`.

### Roadmap

Phase C1 progress: **13 of 14 classes shipped with C surfaces** (A + C from Phase B; I + L + J + B + G + H + D + E + F + N + K from rc1–rc7). Remaining: **M** (HDC bind/bundle/permute — distributed-representation, rc8).

Per `[[feedback_science_is_ssot_not_project]]` reframe: the canonical QM/QFT/SM operations layer is being woven into the Phase C1 close rather than deferred to a separate Phase C2 absorption-from-projects pass. Class M rc8 acquires its operational anchor as **the binding operation that uncompresses LoE-content along its compression axis** per `[[user_stance_1d_collapse_to_loe_identity_not_action]]` (refined from the prior storage/extraction framing — 1D_t IS the Laws of Everything content, identity; Class M is the substrate-coupling operation, not the dimension itself; see `docs/srmech/notes/1d_collapse_to_loe_identity_2026-05-15.md`). Canonical single-particle QM operations (TDSE / TISE / Heisenberg / [x̂,p̂] / Liouville-vN / Pauli / hydrogen-radial / harmonic-oscillator) targeted for rc7 follow-up commits or rc8 alongside Class M; sourced from Sakurai / Cohen-Tannoudji / Griffiths.

## [0.4.0rc6] - 2026-05-16

### Added

**Task #217 Phase C1 — Class N (rational-approximation) C port.**

Sixth rc in Phase C1's rc-stacked build-out. Class N is the third pure-integer primitive (after I — modular arithmetic, J — prime factorisation / period). Two operations, both `uint64_t`, both JPL-clean, both pi-free.

| C symbol | Python wrapper | Operation |
|---|---|---|
| `srmech_continued_fraction(p, q, terms[], max_terms, *out_count)` | `srmech.amsc.rational.continued_fraction(p, q)` | Simple continued-fraction expansion of `p/q` as `[a_0, a_1, ...]` via the Euclidean recurrence. |
| `srmech_best_rational(p, q, max_denom, *out_p, *out_q)` | `srmech.amsc.rational.best_rational(p, q, max_denom)` | Best rational `p'/q'` with `q' ≤ max_denom` approximating `p/q` via continued-fraction convergents (Stern-Brocot path through the mediant tree). Overflow-guarded on the convergent recurrence. |

Loop bound `SRMECH_RATIONAL_EUCLID_CAP = 128` covers Fibonacci-worst-case for uint64 (~91 iterations). Same constant Class I uses for its Euclidean GCD.

### Changed

- **ABI stays v2** — two new symbols are pure additions per the Phase B4 convention.
- **CMake**: `srmech_rational.c` picked up automatically by `file(GLOB CONFIGURE_DEPENDS c/src/*.c)`.

### Roadmap

Phase C1 progress: **12 of 14 classes shipped with C surfaces** (A + C from Phase B; I + L + J + B + G + H + D + E + F + N from rc1–rc6). Remaining: **K + M**.

- **rc7**: K (equation-of-centre / pin-slot — orbital arithmetic)
- **rc8**: M (HDC bind/bundle/permute — distributed-representation)
- **0.4.0 final**: clean ship at Phase C1 close

## [0.4.0rc5] - 2026-05-16

### Added

**Task #217 Phase C1 — Classes D + E + F C ports (real surfaces, not acknowledgment).**

Fifth rc in Phase C1's rc-stacked build-out. Three new C primitive operations, one per class, each parity-tested against a pure-Python fallback. Step 1 of C/Python parity per the architectural commitment: every primitive class earns its C surface.

| Class | C symbol | Python wrapper | Primitive operation |
|---|---|---|---|
| **D** (dispatch) | `srmech_dispatch_match` | `srmech.amsc.dispatch.match` | Given input bytes + ordered (pattern, tag) rules, return tag of first rule whose pattern occurs in input. Multi-needle pattern dispatcher; builds on Class G's `srmech_byte_search` internally. |
| **E** (catalog / naming) | `srmech_catalog_lookup` | `srmech.amsc.naming.lookup` | Binary search over sorted (key, value) catalog. Lex-comparison with length tiebreak. O(log n) lookup, ≤64 iterations cap. |
| **F** (template render) | `srmech_template_render` | `srmech.amsc.template.render` | Render template with `{key}` placeholders, substituting via key→value catalog (uses Class E's `srmech_catalog_lookup` internally). |

Naming note: the new Python primitives are `srmech.amsc.dispatch` / `srmech.amsc.naming` / `srmech.amsc.template` to avoid collision with the existing application-layer modules (`amsc.catalog` is Class E *applied to attested-source registries*, `amsc.descriptor.render_template` is Class F *applied to descriptor cite/purpose templates*). Application modules can later rebuild on the primitive surface for hot-path optimisation.

### Changed

**`CLAUDE.md` operational-scope-clarification rewritten** to remove the "binding-layer concern" framing. Per `[[feedback_no_binding_layer_carveout]]`: every primitive class earns a C surface; "binding-layer" is not a legitimate skip-class directive. Specific scope-bounded helpers (e.g., TOML parsing stays Python per the Phase B5 *vendoring-scope* decision) are framed as their own scope concerns, not as class-skipping carve-outs.

ABI stays v2 — three new symbols are pure additions per the Phase B4 convention. CMake picks up `srmech_dispatch.c` / `srmech_catalog.c` / `srmech_template.c` automatically via `file(GLOB)`.

### Roadmap

Phase C1 progress: **11 of 14 classes shipped with C surfaces** (A + C from Phase B; I + L + J + B + G + H + D + E + F from rc1–rc5). Remaining: **K + M + N**.

- **rc6**: N (rational-approximation — Stern-Brocot continued fractions; pure integer)
- **rc7**: K (equation-of-centre / pin-slot)
- **rc8**: M (HDC bind/bundle/permute)
- **0.4.0 final**: clean ship at Phase C1 close

## [0.4.0rc4] - 2026-05-16

### Added

**Task #217 Phase C1 — Classes B + G + H (the lightweight trio).**

Fourth rc in Phase C1's rc-stacked build-out. Bundles three lightweight classes whose primitive operations each fit a small C surface, freeing up rc cadence for the heavier classes (M, K) later.

- **Class B (tagged-tuple)** — `srmech_tlv_pack(tag, value, value_len, out, capacity, *written)` produces deterministic `[u8 tag][u32 length BE][value]` byte sequences for hashing / fingerprinting typed records. Format is wire-spec ordered (tag-first per the layout); documented as the exception to `[[feedback_struct_field_ordering_big_first]]`. JSON-record parsing stays Python-side per srmech CLAUDE.md operational-scope-clarification.
- **Class G (discovery/search)** — `srmech_byte_search(haystack, h_len, needle, n_len, *out_offset)` finds first occurrence of a byte pattern via naive O(n*m) (fast for srmech's small-haystack cases — descriptor lookups, fingerprint matching). Empty needle matches at offset 0 (matches Python's `bytes.find(b'')`). Catalog dictionary lookups stay Python-side.
- **Class H (self-introspection)** — *already shipped* via `srmech_meta.c`'s `srmech_version()` and `srmech_abi_version()` (Phase B2 baseline). This rc explicitly acknowledges H's mapping to those existing primitives for the cross-substrate-audit roster; no new C symbols added for H.

Public Python surfaces at `srmech.amsc.tlv` and `srmech.amsc.search` with native/fallback dispatch. Parity tests at `tests/test_lightweight_parity.py` cover reference values + Python-equivalence + native↔fallback sweep.

### Changed

- **Class O dissolution** (resolution 2026-05-16). The signed-metric / Wick-rotation operation located by Spike #24 bonus 8 and narrowed by bonus 9 was **dissolved into Class L as a signed-Laplacian-variant sub-operation** per user direction *"nothing else so far has been privileged."* Vocabulary stays at 14 classes A–N; no Class O added. Future Class L rcs will add the signed-Laplacian op when Phase C2 cascade-composition work calls for it. New memory entry `[[feedback_no_privileged_primitive_classes]]` records the design principle: dissolution into existing classes is the default disposition for candidate primitives; promotion requires structural irreducibility. Bonus 11d (Class P sign-rule reduced to existing) is the precedent.
- **ABI stays v2** — two new symbols (tlv_pack, byte_search) are pure additions per the Phase B4 convention.
- **CMake**: `srmech_tlv.c` and `srmech_search.c` picked up automatically by `file(GLOB CONFIGURE_DEPENDS c/src/*.c)`.

### Roadmap

Phase C1 progress: **8 of 14 classes shipped** (A + C from Phase B; I + L + J + B + G + H from Phase C1 rc1–rc4). Remaining: D / E / F / K / M / N. Class D and Class F are likely Python-only-by-design per srmech CLAUDE.md operational-scope-clarification (binding-layer concerns). Heavier classes (M = HDC bind/bundle, K = equation-of-centre/pin-slot) come later as dedicated rcs.

## [0.4.0rc3] - 2026-05-15

### Added

**Task #217 Phase C1 — Class J (prime-factorisation / period) C parity.**

Third per-class C port in Phase C1's rc-stacked build-out. Class J ("J prime-factorisation/period" in Spike #24's cumulative cross-substrate audit) complements Class I (modular arithmetic) with the non-modular integer-structure operations.

Three new C symbols (all `uint64_t`, JPL Power-of-Ten clean, no malloc, pi-free):

- `srmech_is_prime(n, *out)` — trial-division primality test (false for `n < 2`, true for 2 / 3, then test odd `d ≤ sqrt(n)`).
- `srmech_factor(n, primes[], exponents[], max_count, *out_count)` — trial-division prime factorisation returning sorted distinct primes + exponents. Caller-allocated fixed-size buffers; `SRMECH_ERR_OVERFLOW` if distinct-prime count exceeds `max_count`.
- `srmech_cyclic_period(a, n, max_k, *out_period)` — multiplicative order of `a` in `(Z/nZ)*` via trial-period (smallest `k > 0` with `a^k ≡ 1 mod n`). Bounded by `max_k`; `SRMECH_ERR_OVERFLOW` if period exceeds the bound. Requires `gcd(a mod n, n) == 1` (validated by detecting `a mod n == 0`).

Public Python surface at `srmech.amsc.primes` with native/fallback dispatch. Returns ordinary Python types (`bool`, `list[(int, int)]`, `int`) — no numpy dependency at this module level. Parity tests at `tests/test_primes_parity.py` cover reference values + Python-equivalence on random sweeps + native↔fallback parity.

Foundation for Task #218 Phase C2's cascade-period operations (Class J × Class I composition for cyclic-cascade orbital periods).

### Changed

- **ABI stays v2** — three new symbols are pure additions per the Phase B4 convention.
- **CMake**: `srmech_primes.c` picked up automatically by `file(GLOB CONFIGURE_DEPENDS c/src/*.c)`.

## [0.4.0rc2] - 2026-05-15

### Added

**Task #217 Phase C1 — Class L (graph Laplacian) C parity.**

Second per-class C port in Phase C1's rc-stacked build-out. Class L is Spike #24's structural workhorse (instantiated at six of six bonus substrates per the cumulative cross-substrate audit) and the spectral substrate underpinning cascade-composition mass-spectrum reproduction.

Four new C symbols (all `uint32`/`double`, JPL Power-of-Ten clean, pi-free per `[[user_stance_pi_as_projection]]`):

- `srmech_graph_dense_adjacency` — `A` matrix from undirected edge list (self-loops add `2*w` to diagonal per standard convention).
- `srmech_graph_dense_laplacian` — `L = D − A` (combinatorial Laplacian).
- `srmech_graph_normalized_laplacian` — `L_sym = I − D^(−1/2) A D^(−1/2)` (isolated vertices get diagonal 0, not 1).
- `srmech_jacobi_eigvals` — symmetric Jacobi eigendecomposition with algebraic `c, s` computation (no trig calls). In-place on caller-owned matrix.

`N` bound: `SRMECH_LAPLACIAN_MAX_NODES = 256` caps the stack-allocated degree / row-scaling buffers (~2 KB) for embedded-safe execution. Larger graphs return `SRMECH_ERR_OVERFLOW` and the Python wrapper falls back to `numpy.linalg.eigvalsh`.

Public Python surface at `srmech.amsc.laplacian` (`dense_adjacency`, `dense_laplacian`, `normalized_laplacian`, `jacobi_eigvals`) with native/fallback dispatch. Parity tests at `tests/test_laplacian_parity.py` cover reference values, spectral-property invariants (PSD, row-sum=0, normalised eigvals in [0, 2]), and a native↔fallback random sweep.

Pi-free decision: cyclic-graph closed-form spectra (the pi-bearing `2(1−cos(2πk/n))` shortcut) are NOT shipped on the C surface — those are downstream projections of Class I's integer-cyclic upstream. Users computing cyclic-graph spectra compose Class I (modular arithmetic) with Class L's dense build + Jacobi, or use numpy at the Python layer.

### Changed

- **numpy is now a hard runtime dependency** (added to `[project.dependencies]`). Class L (graph Laplacian) and the upcoming Class M (HDC bind/bundle) are fundamentally array-numerical; numpy provides the ergonomic Python surface + fallback path. Pyodide environments install numpy via micropip. `srmech.amsc.cyclic` (Class I, integer-only) does not import numpy.
- **ABI stays v2** — four new symbols are pure additions per the Phase B4 convention.
- **CMake**: `srmech_laplacian.c` picked up automatically by `file(GLOB CONFIGURE_DEPENDS c/src/*.c)` — no CMakeLists edits required. Existing libm linkage covers the `sqrt` calls.

### Roadmap

Phase C1 continues — remaining classes (B/D/E/F/G/H/J/K/M/N + Class O if accepted) ratchet as further rc-stacked additions under `0.4.0rcN`. Class D and Class F likely Python-only-by-design per srmech CLAUDE.md operational-scope-clarification. Phase C1 closes at clean `0.4.0`.

## [0.4.0rc1] - 2026-05-15

### Added

**Task #217 Phase C1 — Class I (cyclic-group / modular arithmetic) C parity.**

First per-class C port in the post-v0.2.0 Phase C1 build-out (Task #217 follows Task #201 Phase B's ratchet). Class I appears in Spike #24's cumulative cross-substrate audit at five of six bonus substrates (tactical / SHA-256 / MFO 3+7+1 / RNG / cascade composition) and is the foundation primitive for Task #218 Phase C2's cascade-composition operations.

Six new C symbols (all uint64_t, JPL Power-of-Ten clean, no malloc, fixed-bound loops, ≥2 asserts per function):

- `srmech_gcd(a, b, *out)` — Euclidean GCD (`gcd(0, 0) = 0`).
- `srmech_lcm(a, b, *out)` — LCM via GCD with `UINT64_MAX` overflow guard.
- `srmech_mod_add(a, b, n, *out)` — `(a + b) mod n`, overflow-safe.
- `srmech_mod_mul(a, b, n, *out)` — `(a * b) mod n` via russian-peasant doubling (portable; no `__int128` / `_umul128`).
- `srmech_mod_pow(a, k, n, *out)` — `a^k mod n` via square-and-multiply.
- `srmech_mod_inv(a, n, *out)` — modular inverse via extended Euclidean (requires `n ≤ INT64_MAX` for int64 intermediate coefficients).

Public Python surface at `srmech.amsc.cyclic` with native/fallback dispatch (parity tests in `tests/test_cyclic_parity.py`).

### Changed

- **ABI stays v2.** Six new symbols are pure additions per the Phase B4 convention; existing ABI-tied wire formats unchanged.
- **CMake**: `srmech_cyclic.c` is picked up automatically by `file(GLOB CONFIGURE_DEPENDS c/src/*.c)` — no CMakeLists.txt edits required.
- **JPL audit**: `srmech_cyclic.c` participates in the pytest ratchet at `tests/test_jpl_audit.py` (Rules 1/3/4/5/8 mechanically detected).

### Roadmap context

This release is the start of Task #217 Phase C1's per-class C-parity build-out. Phase C1 ratchets remaining primitive classes (B/D/E/F/G/H/J/K/L/M/N + Class O if accepted) as rc-stacked additions under `0.4.0rcN` per `[[feedback_rc_stacking_versioning]]`, with the clean `0.4.0` ship at Phase C1 close. Class D and Class F are likely Python-only-by-design (binding-layer per srmech CLAUDE.md operational-scope-clarification); each class gets a per-port decision recorded in CLAUDE.md.

Phases C2 (Task #218 — MFO/SM/QM operations layer), C3 (Task #219 — per-class CLI help-arg discipline), and C4 (Task #220 — tool-schema extension for catalog files) build on Phase C1's foundation.

## [0.3.1] - 2026-05-14

### Production cut bundling rc1 + rc2 (no code change from 0.3.1rc2)

The 0.3.1rc2 → 0.3.1 transition contains only version-string bumps in
the four SSOT locations plus this CHANGELOG header. Bundles both POC
findings from the chess-spectral simple-profile migration ([Task #211](../...)):

- **rc1**: entry-point Form-1 (package-only) support — every
  real-world Python plugin discovery system uses
  `"package_name"` rather than `"package:CONST"`.
- **rc2**: `[profile.tool_schema].extension_file` was parsed at
  validation time but never loaded at activation time, so profile
  tool entries silently went missing from the registry.

Both fixes are backward-compatible additions to the loader; no
v0.3.0 API breakage.

End-to-end verification (Windows / Python 3.14, clean venv, TestPyPI
0.3.1rc2 + chess-spectral 1.19.0 pre-release wheel):

```
srmech version: 0.3.1rc2
=== chess profile activation ===
Profile: chess v1.19.0
=== tool_schema integration ===
chess tools registered: 8
 - chess.encode_2d : Spectral 2D chess encoder...
 - chess.encode_4d : Spectral 4D chess encoder...
 - chess.fen_to_pos : Parse a FEN string into the 2D position dict...
 - chess.channel_energies : Compute per-channel L² energy...
 - chess.encode_2d_pure_phase : Integer-arithmetic 2D chess encoder...
 - chess.phase_only_pseudo_legal_moves : Pure-phase pseudo-legal...
 - chess.encode_2d_bip_hybrid : BIP-hybrid sign × magnitude...
 - chess.decode_2d_bip_hybrid : Inverse of encode_2d_bip_hybrid...
=== bridge call still works ===
encode_2d shape: (640,)
```

Profile pattern (ADR-0001) is now exercised by a real third-party-style
package. ADR §7 Step 1 (chess POC) drives ADR §7 Step 2 (ephemerides
plugin-profile) next.

See [0.3.1rc2] + [0.3.1rc1] below for the full bug + fix narratives.

## [0.3.1rc2] - 2026-05-14

### Fixed — `[profile.tool_schema]` extension file loading

Second issue surfaced by the chess-spectral simple-profile POC (Task #211).
v0.3.0–v0.3.1rc1: the profile loader's `_validate_descriptor` accepted
`[profile.tool_schema]` blocks at parse time, but `Profile.__init__`
never actually loaded the referenced extension TOML at activation
time. Profiles declaring tool-schema extensions activated cleanly but
contributed zero `ToolEntry` records to `srmech.amsc.tool_schema`.

Repro (v0.3.1rc1 against chess-spectral 1.19.0):

```python
>>> import srmech
>>> p = srmech.profile("chess")  # activates cleanly
>>> from srmech.amsc.tool_schema import get_tool_schema
>>> get_tool_schema().by_owner("chess")
[]   # ← should have been 8 entries from chess-spectral's
     # _srmech_tool_schema.toml
```

Fix in `Profile.__init__`: new `_load_tool_schema_extension()` step.
After bridge resolution + catalog registration + native plugin
loading, if `[profile.tool_schema].extension_file` is declared, the
loader resolves it inside the package directory and registers every
`[[tools]]` block via `srmech.amsc.tool_schema.register_profile_tools()`
with `owner = profile.name`.

Verified against chess-spectral's 8-tool extension file
(`_srmech_tool_schema.toml`):

```
chess tools registered: 8
 - chess.encode_2d : Spectral 2D chess encoder...
 - chess.encode_4d : Spectral 4D chess encoder...
 - chess.fen_to_pos : Parse a FEN string into the 2D position dict...
 ...
```

Backward-compatible: profiles without a `[profile.tool_schema]` block
take the no-op path. Profiles with malformed extension files raise
`InvalidProfileError` at activation time, before any bridge surface
is bound — fail-loud-at-boot per ADR-0001 §5.5.

## [0.3.1rc1] - 2026-05-14

### Fixed — entry-point Form-1 (package-only) support for profile loader

v0.3.0's `_resolve_entry_point_toml` only handled `"package:CONST"`
attribute-style entry-point declarations (Form 2). Every real-world
Python plugin discovery system (pytest, flake8, setuptools_scm) uses
the simpler `"package_name"` form — and that's what surfaced
immediately during the **chess-spectral simple-profile POC migration**
([Task #211](https://github.com/lemonforest/mlehaptics/...),
[ADR-0001](../adr/0001-profile-pattern.md) §7 Step 1).

Symptom (v0.3.0 against chess-spectral 1.19.0's declaration):

```python
>>> import srmech
>>> srmech.list_profiles()
{'chess': ProfileStatus(name='chess', ..., status='invalid',
   diagnostic="entry-point 'chess' ('chess_spectral') resolved to
   module; expected Path or str pointing at srmech_profile.toml")}
```

Fix in `srmech/profile_loader.py`:
`_resolve_entry_point_toml` now handles **three** entry-point value
forms:

1. **Package only** (recommended, boilerplate-free):
   `chess = "chess_spectral"`. Loader uses
   `importlib.resources.files(package) / "srmech_profile.toml"`.
2. **Path/str attribute** (explicit, v0.3.0 form):
   `chess = "chess_spectral:_SRMECH_PROFILE_PATH"`. Unchanged.
3. **Callable returning a Path/str** (for descriptors generated at
   import time): `chess = "chess_spectral:_get_path"`. Unchanged in
   intent — was always documented as supported but never wired.

Backward-compatible: every v0.3.0 caller continues to work; Form 1
is purely additive.

ADR-0001 §7 Step 1 explicitly anticipated this kind of finding:
> "Lessons learned go back into the ADR + the §3 schema if needed."

The schema doesn't change; only the loader implementation. The
authoring guide (Task #214) will recommend Form 1 as canonical.

### Tests

- New: `test_entry_point_form_1_package_only` (synthesised package
  on tmp_path; verifies `importlib.resources.files()` resolution).
- New: `test_entry_point_form_2_path_constant` (Form 2 regression).
- New: `test_entry_point_form_2_string_constant` (Form 2 regression).
- New: `test_entry_point_form_3_callable_returning_path`.
- New: `test_entry_point_unknown_type_rejected` (negative case).

### Why a patch bump (not minor)

The fix is purely additive to the loader's accepted inputs.
v0.3.0's documented behaviour (Form 2) continues to work identically.
No new public surface, no API breakage. SemVer patch is correct.

## [0.3.0] - 2026-05-14

### Production cut of the v0.3.0 ship (no code change from 0.3.0rc1)

The 0.3.0rc1 → 0.3.0 transition contains only version-string bumps
in the four SSOT locations (`pyproject.toml`, `pyproject-pure.toml`,
`srmech/version.py`, `c/include/srmech.h`) plus this CHANGELOG header.

TestPyPI verification (clean venv, Windows / Python 3.14):

```
version: 0.3.0rc1
HAS_NATIVE: True ABI: 2
tool_schema_version: 1.0
builtin tools: 6
list_profiles: {}
ProfileNotFoundError works: no profile named 'nonexistent'; enumerated profiles: []
All profile loader exports present: True
```

Native dispatch healthy, builtin AMSC tools self-register at amsc
import time, profile loader API complete. No issues surfaced through
the rc cycle; cutting straight to production.

See [0.3.0rc1] below for the full feature description.

## [0.3.0rc1] - 2026-05-14

### Added — Task #198 (`srmech.amsc.tool_schema`) + Task #199 (profile loader)

First implementation of the **profile pattern** specified in
[ADR-0001](../adr/0001-profile-pattern.md). Ships as v0.3.0rc1 to
TestPyPI for verification before the production v0.3.0 cut.

#### `srmech.amsc.tool_schema` — LLM-friendly introspection (Task #198)

New module that produces a single structured view of every callable
srmech exposes (and, post-profile-pattern, every profile-contributed
callable). API:

- **`get_tool_schema()`** — returns a `ToolSchema` dataclass with
  every registered `ToolEntry`. JSON-serialisable via `.to_jsonable()`.
- **`tool_schema_view()`** — convenience wrapper returning the same
  as a dict.
- **`register_tool(entry)`** — imperative registration; idempotent
  on identical re-registration; raises `ToolSchemaConflictError`
  on name collision with different content.
- **`register_profile_tools(profile_name, entries)`** — batch path
  used by the profile loader; enforces `entry.owner == profile_name`
  so profile-attribution can't drift.
- **`unregister_profile_tools(profile_name)`** — removes every entry
  owned by the named profile (used on profile deactivation).
- **`load_extension_file(path, owner)`** — parses a profile's
  TOML extension file into a list of `ToolEntry` ready for batch
  registration.

srmech's own AMSC functions (sha256_bytes, read_ndjson,
descriptor_hash, list_attested_sources, get_attested_dataset,
register_attested_root) are registered at AMSC import time with
their parameter signatures, return shapes, and smoke-test hints.

#### `srmech.profile_loader` — profile activation API (Task #199)

New module implementing ADR-0001's profile pattern:

- **`srmech.list_profiles()`** — enumerates every installed profile
  via `importlib.metadata.entry_points(group="srmech.profiles")`.
  **Eager at first call** per ADR §5.5 (JPL Rule 2 analog); cached
  for process lifetime.
- **`srmech.profile(name)`** — activation API. Returns a `Profile`
  object exposing bridge surfaces as attributes. On first call for
  a given profile-version:
  - Validates the descriptor against the v1.0 schema (strict).
  - Checks smoke-test cache at
    `~/.cache/srmech/profile_smoke_tests/<name>-<version>.toml`.
  - Cache miss / version bump → re-runs smoke test (bridge surfaces
    importable + callable; catalog roots exist).
  - On smoke-test pass: registers catalog roots into srmech's
    universal bridge; loads native plugin via ctypes if
    `[profile.native]` declared, performs ABI handshake; caches
    result; returns `Profile`.
  - On smoke-test fail: raises `SmokeTestFailedError`; profile not
    activated; cache records the failure (re-runs on next process).
- **`Profile.<bridge_surface>(args)`** — invoke a profile-declared
  bridge function.
- **`Profile.native`** — bound ctypes library (plugin tier only).

Error hierarchy:
`ProfileError` ⊂ `Exception`
  - `ProfileNotFoundError` — unknown profile name
  - `InvalidProfileError` — descriptor failed validation
    - `ProfileSchemaVersionError` — descriptor against unknown schema version
  - `SmokeTestFailedError` — smoke test failed (cache may record)
  - `AbiMismatchError` — plugin's `abi_version()` mismatch

#### JSON Schema for `srmech_profile.toml`

[`docs/srmech/adr/0001-profile-pattern.schema.json`](../adr/0001-profile-pattern.schema.json)
renders ADR §3 into a machine-checkable shape. The loader uses a
pure-Python minimal validator that covers the load-bearing
constraints (required fields, name/version patterns, schema-version
match); the full JSON Schema is the documented source-of-truth for
profile authors and for third-party validation tools.

#### `[profile.interpreted]` is reserved (ADR §5.6)

Profiles declaring an `[profile.interpreted]` block (Julia / R / Lua /
subprocess runtimes) parse cleanly but emit a `FutureWarning` and
the block is ignored. The namespace is reserved in v1.0 of the
schema so adding interpreted-runtime adapters later (a follow-up
ADR) won't be a breaking change.

#### Tests

- **`tests/test_tool_schema.py`** *(NEW)* — 11 tests covering
  imperative + extension-file registration, idempotency, conflict
  detection, owner-tag enforcement, by_owner filter, lookup,
  serialisation round-trip.
- **`tests/test_profile_loader.py`** *(NEW)* — 14 tests covering
  schema validation paths (minimal valid; missing fields; bad
  patterns; full plugin-tier `[profile.native]`; reserved
  `[profile.interpreted]` block warns), public API surface, and
  error-class exports.

All v0.2.0 tests (sha256 parity, NDJSON parity, JPL audit ratchet,
etc.) continue to pass unchanged.

#### Version

This is a **minor bump** (0.2.0 → 0.3.0). Adds new APIs; no breaking
changes to v0.2.0's public surface. C ABI still 2.

## [0.2.0] - 2026-05-14

### Task #201 Phase B7 — production cut to PyPI

First **production PyPI** release of native-C-accelerated srmech.
Content is functionally identical to **`0.2.0rc2`** on TestPyPI;
only the version string changes (rc-suffix stripped) and the
docs lose the rc-cycle commentary. The tag-routing claim in
`srmech-publish.yml` directs a non-rc tag to the production PyPI
trusted-publisher environment.

#### What v0.2.0 ships, headline

The Task #201 build-out (rc3 → rc9 + rc1 → rc2 = 11 TestPyPI
rcs across phases B1 through B7) turned srmech from a pure-Python
AMSC framework (the v0.1.0 ship) into a native-C-accelerated
multi-platform package at peer quality with ephemerides-spectral:

- **Native C library** (`srmech_sha256_hex`, `srmech_ndjson_iter`,
  + version / ABI accessors) shipped under `srmech/_native/`
  inside platform-tagged wheels.
- **15-cell cibuildwheel matrix** — Linux (manylinux_2_28) × macOS
  × Windows × py3.10 / 3.11 / 3.12 / 3.13 / 3.14. Each cell runs
  `test_native_sha256.py` + `test_format.py` to verify the wheel's
  native dispatch + sha256 parity post-build.
- **scikit-build-core + CMake** build backend (Phase B2). Pure-
  Python fallback for Pyodide / WASM lives in `pyproject-pure.toml`
  (hatchling backend, swapped in for the `build-pure-wheel` CI
  job).
- **All `hashlib.sha256` callsites** in `srmech.amsc` route through
  `format.sha256_bytes()` → native dispatch when available;
  hashlib fallback otherwise.
- **JPL Power-of-Ten audit** complete (Phase B6). 10/10 rules
  satisfied modulo one documented Rule 9 callback deviation; ratchet
  enforced by `tests/test_jpl_audit.py` (6 mechanical tests, pinned
  exemption list) + `pedantic-build` CI job (3-cell:
  Linux gcc / macOS clang / Windows MSVC × `-DSRMECH_PEDANTIC=ON`
  → `-Werror` / `/WX`).
- **Description-match guard** between `pyproject.toml` and
  `pyproject-pure.toml` (rc9 post-mortem). Both descriptions
  carry the same 450-char Summary: "*Stored-Relationship
  Mechanism research package: home of the Attested Multi-Source
  Collector/Catalog (AMSC) framework — ...*".
- **AMSC dual-name framing** (rc2). Both *Collector* (at fetch
  time) and *Catalog* (at read time) work; same abbreviation;
  pick whichever fits the lifecycle stage.
- **Development Status classifier** bumped `3 - Alpha` → `4 - Beta`
  (rc9).

#### Cross-package readiness

ephemerides-spectral 0.26.1rc1 (the parallel-session ship) pins
`srmech>=0.1.1rc9` with a TestPyPI `PIP_EXTRA_INDEX_URL` override
to exercise the cibuildwheel matrix against the TestPyPI srmech
rcs. With v0.2.0 now on production PyPI, the next
ephemerides-spectral release will bump that floor to
`srmech>=0.2.0` and drop the TestPyPI override.

#### v0.1.0 status

Still on PyPI as the historical release. `pip install srmech`
without any version constraint now resolves to v0.2.0; users on
older Python paths can still pin `srmech==0.1.0` for the
pure-Python wheel.

#### History

See the rc-by-rc entries below for the full per-phase record:

- `0.2.0rc2` — AMSC "Collector/Catalog" dual-name wording
- `0.2.0rc1` — Phase B7 final TestPyPI gate (no-op version bump
  from rc9)
- `0.1.1rc9` — Metadata drift sweep ("Pure Python." → "Native C
  dispatch"; Dev Status 3-Alpha → 4-Beta; description-match guard)
- `0.1.1rc8` — Phase B6 JPL Power-of-Ten audit + ratchet
- `0.1.1rc7` — Phase B5 sha256 callsites routed through native
- `0.1.1rc6` — Phase B4 NDJSON streaming reader C port
- `0.1.1rc5` — Phase B3 SHA-256 C port + cibuildwheel matrix
- `0.1.1rc4` — Phase B2 scikit-build-core + pyproject-pure
- `0.1.1rc3` — Phase B1 C tree scaffolding
- `0.1.1rc1` / `rc2` — Earlier infrastructure cycles
- `0.1.0` — Initial AMSC-to-srmech refactor (pure-Python)

## [0.2.0rc2] - 2026-05-14

### Added — Task #201 Phase B7: AMSC dual-name wording ("Collector / Catalog")

Documents the dual reading of the **AMSC** abbreviation across
srmech's user-facing surface. **No code, no API, no ABI change**
— pure documentation polish discovered while reviewing the
0.2.0rc1 TestPyPI metadata.

#### The framing

**AMSC** abbreviates both:

- **Attested Multi-Source Collector** — at collection time
  (T1 fetch / T3 live query / re-bake lifecycle stages), the
  framework's adapter classes are *collecting* attested rows
  from upstream archives.
- **Attested Multi-Source Catalog** — after collection, the
  committed NDJSON SSOTs constitute a *catalog* of attested
  data that downstream packages register and query through the
  universal bridge.

Both names are correct; both abbreviate to AMSC; pick whichever
fits the lifecycle stage you're describing. One framework wearing
two hats.

#### Surfaces updated

- **`pyproject.toml` + `pyproject-pure.toml`** `[project].description`
  — "Attested Multi-Source Collector (AMSC)" →
  "Attested Multi-Source Collector/Catalog (AMSC)". 442 chars →
  450 chars (still under both the 480 soft cap and PyPI's 512
  hard cap).
- **`python/README.md`** — package-intro paragraph updated;
  new "Why 'Collector/Catalog'?" subsection explains the dual
  reading with the T1/T3-fetch vs read-time-query lifecycle
  framing.
- **`python/srmech/__init__.py`** docstring — package-level
  framing now leads with the dual name and gives a paragraph on
  the lifecycle-stage interpretation.
- **`python/srmech/amsc/__init__.py`** docstring — same dual-
  name framing at the AMSC subpackage level.
- **`docs/srmech/srmech_research_notebook.md` §0** — three-layer
  architecture's L1 paragraph gains a "Naming aside" note
  introducing both readings, with explicit lifecycle-stage
  cross-references (`list_attested_sources` etc.).
- **`docs/srmech/CLAUDE.md`** state snapshot bumped to reflect
  the rc2 ship.

#### Why TestPyPI rc rather than land-as-unreleased

Initial intent (per maintainer's "leave this as an unreleased
update" guidance) was to land the doc change on `main` without a
new rc; but per the project's TestPyPI-before-PyPI discipline,
any text that goes to production PyPI's Summary metadata should
have been visible on TestPyPI first. PyPI Summary drift (the
"Pure Python." bug at rc8 → rc9) was the specific failure mode
that motivated the description-match guard; landing the dual-name
wording without a TestPyPI round-trip would re-open the same
exposure. So we ship rc2 to TestPyPI and verify there, then v0.2.0
(no rc suffix) cuts to production PyPI carrying the rc2 text.

#### No code change

C ABI still **2**. Python public API surface unchanged. Wheel
content identical to rc1 modulo the description string +
docstrings. Pytest matrix unaffected (the
`test_native_version_and_abi` rc9-bump fix from rc1 keeps working).

## [0.2.0rc1] - 2026-05-13

### Task #201 Phase B7 — final TestPyPI rc before v0.2.0 production cut

No code changes from `0.1.1rc9`. This release exists to validate
the **v0.2.0** version string itself through one more TestPyPI
round-trip before the clean `srmech-v0.2.0` tag goes to
**production PyPI**. Discipline: TestPyPI before PyPI, always —
the rc-suffix auto-routing in `srmech-publish.yml` means a clean
non-rc tag IS the production gate; we want one last sanity
verification on the version string + metadata immediately before
the gate-passing tag.

#### Why a minor bump (0.1.1 → 0.2.0)

The rc3 → rc9 series turned srmech from a pure-Python AMSC
framework into a native-C-accelerated package with cibuildwheel
matrix + JPL Power-of-Ten audit + per-platform parity tests
covering 3 OS × 5 Python versions. That's a real capability
boundary, large enough that consumers of `srmech==0.1.0`
upgrading via `pip install -U srmech` are going on a substantive
ride. Minor bump signals that.

#### Cross-package readiness (parallel session shipped this)

While the srmech rc series was iterating, a parallel Claude
Code session verified srmech rc9 against the sister package
**ephemerides-spectral** (which depends on srmech as its AMSC
substrate per Task #197). The verification result lives at
[`docs/antikythera-maths/ephemerides-spectral/CHANGELOG.md`](../../antikythera-maths/ephemerides-spectral/python/CHANGELOG.md)
under `ephemerides-spectral 0.26.1rc1`. That rc shipped to
TestPyPI with `srmech>=0.1.1rc9` pinned + a
`PIP_EXTRA_INDEX_URL=https://test.pypi.org/simple/` test-env
override (Option B from the verification prompt), confirming
the cibuildwheel test matrix actually exercises against the
TestPyPI srmech rc rather than silently falling back to PyPI's
`srmech==0.1.0`. Cross-package integration confirmed green.

After srmech v0.2.0 ships to production PyPI, ephemerides-spectral
will bump its srmech floor `>=0.1.1rc9` → `>=0.2.0` and drop the
TestPyPI test-env override in its own follow-up release. That's
ephemerides-spectral's ship to plan, not srmech's.

#### Path forward

1. **This rc1** auto-ships to TestPyPI via the rc-suffix routing.
2. Maintainer verifies wheel install + native dispatch + sha256
   parity + ndjson parity end-to-end from a clean venv outside
   the repo tree.
3. If clean, maintainer bumps `0.2.0rc1` → `0.2.0` (drop the
   `rcN` suffix in all four SSOT files), merges that bump, and
   tags `srmech-v0.2.0`. That clean tag auto-routes to
   **production PyPI** via the workflow's environment-name claim.
4. After v0.2.0 lands on PyPI, ephemerides-spectral can bump
   its srmech floor; downstream consumers can upgrade via
   `pip install -U srmech`.

#### No ABI / API / behaviour change

C ABI version unchanged (still 2). Python public surface
unchanged. Wheel content identical to rc9 modulo the version
string. The `SRMECH_VERSION` macro updates in lockstep
(`0.1.1rc9` → `0.2.0rc1`) and the Python `_native.py` reads it
back through `srmech_version()` at load time.

## [0.1.1rc9] - 2026-05-13

### Fixed — PyPI metadata drift after Phase B3 (native code) landed

User-spotted drift on the TestPyPI project page: the Summary still
read "...Pure Python." even though Phase B3 (rc5) shipped native C
dispatch and Phase B4 (rc6) added the second native symbol. Both
`pyproject.toml` and `pyproject-pure.toml` had the stale claim
verbatim because the description text was copy-pasted between them
without revisiting the trailing sentence after each phase.

#### Fixed

- **`pyproject.toml` + `pyproject-pure.toml` `[project].description`**
  — replaced "Pure Python." with "Native C dispatch (SHA-256 +
  NDJSON line reader) with pure-Python fallback for Pyodide / WASM."
  Both files now carry identical 442-char descriptions (well under
  the 480-char soft cap; well under PyPI's 512-char hard limit).
- **`README.md` Status line** — refreshed to reflect the rc3→rc8
  arc and the impending v0.2.0 cut. Adds a one-liner clarifying
  the native-C + pure-Python-fallback architecture in the package
  intro paragraph.
- **`Development Status` classifier** — bumped from
  `3 - Alpha` → `4 - Beta` on both pyproject files. After 6 rc
  iterations including cibuildwheel matrix, JPL Power-of-Ten audit,
  Python/C parity tests, and pedantic-build CI on three platforms,
  "Beta" is the honest label. Same status ephemerides-spectral
  carries.

#### Added — description-match guard (defensive ratchet)

The publish workflow (`srmech-publish.yml`) and CI workflow
(`srmech-ci.yml`) already enforce **version-match** between
`pyproject.toml` and `pyproject-pure.toml`. The same guard pattern
now also asserts **description-match**: any drift between the two
descriptions fails CI with a clear error message including both
char counts. This catches future copy-paste drift before it can
reach a TestPyPI / PyPI upload.

PyPI's Summary metadata is per-project-version (not per-wheel), so
both wheels uploaded under the same version must carry the same
Summary text. The match guard formalises that invariant.

#### Audit scope

Reviewed every user-facing PyPI metadata surface for similar drift:

- ✅ `description` — fixed (both files).
- ✅ `Development Status` classifier — bumped.
- ✅ README Status line — refreshed.
- ✅ `keywords` — accurate (stored-relationship, mechanism, attested,
  provenance, ndjson, ground-proof, research). No change.
- ✅ `Topic :: Scientific/Engineering` classifier — accurate.
- ✅ `Programming Language ::` classifiers — match `requires-python`.
- ✅ `[project.urls]` — Homepage, Repository, Issues, Changelog,
  Notebook. Stable, no drift.
- ✅ Docstrings in `_native.py` / `format.py` / `c/README.md` that
  mention "pure-Python" — all referring to the fallback path
  correctly; no drift.

#### No ABI change

C surface unchanged from rc8. `SRMECH_ABI_VERSION` stays at 2.

## [0.1.1rc8] - 2026-05-13

### Added — Task #201 Phase B6: JPL Power-of-Ten audit

Formal audit of srmech's native C library against
[Holzmann's JPL Power-of-Ten rules](https://web.eecs.umich.edu/~imarkov/10rules.pdf).
Mirrors the pattern ephemerides-spectral applied via Tasks
#105–#110. **All ten rules satisfied** for srmech's C surface,
modulo one documented Rule 9 deviation (callback-based iterator).

#### Audit deliverables (`docs/srmech/c/JPL_AUDIT.md`)

- **Rule-by-rule compliance review** across all 3 C source files
  (`srmech_meta.c`, `srmech_sha256.c`, `srmech_ndjson.c`) + the
  public header `srmech.h`. ~500 LOC total.
- **Per-function line + assertion counts** with explicit exemption
  policy for trivial accessors (`srmech_version`,
  `srmech_abi_version`) and `static inline` arithmetic primitives
  (sha256 bit-rotation helpers).
- **Rule 9 deviation rationale** documented: the `srmech_ndjson_iter`
  callback is the smallest API surface satisfying Rules 3 + 4 simultaneously.

#### Code fix shipped in this audit pass

- **`srmech_ndjson_iter`** at rc6 was **76 lines** (Rule 4 violation:
  > 60 lines). The chunk-byte-loop body extracted into a new
  `static srmech_ndjson_process_chunk` helper along its natural
  state-update seam. Post-refactor: 51-line `iter` + 43-line
  `process_chunk`. Byte semantics identical; 18 ndjson parity
  tests re-ran clean.

#### Tests + CI ratchet

- **`tests/test_jpl_audit.py`** *(NEW)* — 6 mechanically-detectable
  ratchet tests:
  - Rule 1: no `goto` / `setjmp` / `longjmp` anywhere.
  - Rule 3: no `malloc` / `calloc` / `realloc` / `free` / `alloca`.
  - Rule 4: every function ≤ 60 lines (line-count regex + brace-
    depth scanner).
  - Rule 5: every non-exempt function has ≥ 2 assertions.
    Exempt list pinned (8 entries: 2 trivial accessors, 6 inline
    helpers); adding to the exempt list requires documenting
    rationale in JPL_AUDIT.md AND updating the test.
  - Rule 8: no multi-line macros / token-paste / `__VA_ARGS__`.
  - Audit doc present-and-mentions-all-rules sanity check.
- **`.github/workflows/srmech-ci.yml`** gains a **`pedantic-build`
  job** (3-cell matrix: Linux gcc / macOS clang / Windows MSVC)
  that runs `cmake -DSRMECH_PEDANTIC=ON` → builds with `-Werror`
  (POSIX) or `/WX` (MSVC). Any new warning fails CI. Rule 10
  toolchain-side enforcement.
- All 100 existing tests still pass; pytest collects 106 tests +
  the JPL ratchet's 6 = 112 total Python tests.

#### Verification (local)

- ``gcc -std=c11 -Wall -Wextra -Wpedantic -Werror -O2`` builds all
  3 C files clean.
- `pytest tests/test_jpl_audit.py` → 6/6 pass.
- Full pytest suite (rc8 wheel install) → 106 passed + 1 skipped
  (1 native-dispatch skip when run from source tree).

#### Phase plan progress

| B1 | C tree scaffolding (rc3)                          | ✅ |
| B2 | scikit-build-core + pyproject-pure (rc4)          | ✅ |
| B3 | SHA-256 + cibuildwheel matrix (rc5)               | ✅ |
| B4 | NDJSON streaming reader (rc6)                     | ✅ |
| B5 | Route remaining sha256 callsites (rc7)            | ✅ |
| B6 | JPL Power-of-Ten audit (rc8)                      | this ship |
| B7 | v0.2.0rc1 final TestPyPI verify → v0.2.0 to PyPI  | next |

## [0.1.1rc7] - 2026-05-13

### Changed — Task #201 Phase B5: route remaining sha256 callsites through native dispatch

Phase B5's nominal title was "TOML canonical-serialization C port".
The shipped scope is narrower and better-fit: the actual hot work
(SHA-256 over canonicalised bytes) already has a native C path
from Phase B3. **B5 routes the four remaining ``hashlib.sha256``
callsites in srmech through ``sha256_bytes``** so every per-row
attestation hash benefits from the native dispatch.

Vendoring a TOML parser in C — the original phase plan's
implication — was rejected. CPython's ``tomllib`` + ``json.dumps``
canonicalisation is small, fast, and well-tested; replicating it
in C would 3× srmech's native-code surface area for no measurable
gain on the inputs srmech actually processes.

#### Wired callsites

- **`descriptor.descriptor_hash`** — the load-bearing one. Used by
  every adapter's ``attest()`` step to compute
  ``collector_descriptor_hash`` per row.
- **`catalog._file_sha256`** — hashes overlay NDJSON files for T2
  user-runtime-kernel attestation. Small files (< few MB), so
  slurp-and-hash via ``sha256_bytes`` is fine; streaming hashlib
  (which we'd need for huge files) would require a separate
  C-side multi-update API not yet ported.
- **`catalog._kernel_cache_hash`** — cache-key hash over the
  registered T2 overlay summary.
- **`adapters._base.parser_rule_hash`** — per-row attestation field
  documenting the parse-section rules.

#### What stays in Python

- TOML parsing (``tomllib.loads``) — stdlib, already C-accelerated.
- Canonical JSON serialisation (``json.dumps(sort_keys=True, ...)``) —
  stdlib, already C-accelerated.
- Streaming hashlib for the (currently unused) very-large-file case.

#### Tests

- **`tests/test_native_descriptor_hash.py`** *(NEW)* — 7 parity
  tests:
  - 3 descriptor-shape fixtures (minimal, comments + odd-spacing,
    deeply-nested keys) comparing native-routed ``descriptor_hash``
    to a pure-Python hashlib reference computation.
  - ``catalog._file_sha256`` parity vs streaming hashlib.
  - ``adapters._base.parser_rule_hash`` parity vs hashlib.
  - Defensive ratchet asserting all four wired callsites resolve to
    the same native path (catches accidental re-introduction of
    direct ``hashlib.sha256`` calls).
- Full pytest suite (100 tests + 1 skip) all green under native
  wheel install on Windows MSVC + Python 3.14.

#### No ABI change

C surface area unchanged from rc6. SRMECH_ABI_VERSION stays at 2.

## [0.1.1rc6] - 2026-05-13

### Added — Task #201 Phase B4: NDJSON streaming reader C port

Second C/Python parity surface. Native ``srmech_ndjson_iter`` does
file-IO + line tokenisation in C; JSON parsing stays in Python.
Byte-exact line-set agreement pinned by the new pytest parity
suite in ``tests/test_native_ndjson.py`` (18 tests including
chunk-boundary span + max-line-overflow + CRLF / mixed-EOL fixtures).

#### C side (`docs/srmech/c/`)

- **`src/srmech_ndjson.c`** *(NEW)* — streaming line reader.
  Reads 64 KiB chunks via ``fread``; assembles partial lines into a
  static 1 MiB buffer (single-thread contract); invokes the caller's
  callback with ``(line, line_len, lineno, user)`` per non-empty
  line. Empty lines are silently skipped but ``lineno`` still
  advances, so callback-side error messages line up byte-exactly
  with the file (verified by ``test_read_ndjson_malformed_line_lineno_correct``).
  CR-stripping at line boundaries matches Python's
  ``raw.rstrip("\r\n")``.
- **`include/srmech.h`** — callback typedef gains ``size_t lineno``
  parameter; ``SRMECH_ABI_VERSION`` bumped to **2**.
- **`src/srmech_meta.c`** — ``srmech_abi_version()`` now returns the
  macro indirectly so a missed manual bump can't silently lie.

#### Python side (`docs/srmech/python/srmech/amsc/`)

- **`_native.py`** —
  - ``EXPECTED_ABI_VERSION = 2`` (matches C-side bump).
  - ``_NDJSON_LINE_CB`` — ctypes ``CFUNCTYPE`` mirroring the
    4-argument C callback typedef.
  - ``ndjson_lines_c(path) -> list[(lineno, bytes)]`` — Python
    wrapper that runs the native iterator under a ctypes callback
    and collects ``(lineno, line_bytes)`` tuples.
  - ``NativeNDJsonError`` — distinct from ``MPRValidationError``
    because the failure is upstream of JSON parsing (file IO or
    overflow). Translated to ``OSError`` at the ``format.read_ndjson``
    boundary so callers see consistent semantics.
- **`format.py`** — ``read_ndjson()`` dispatches via the native
  iterator when ``HAS_NATIVE`` is True; pure-Python streaming path
  remains unchanged. JSON parsing (``json.loads`` +
  ``MPRRecord.from_json_line``) stays in Python on both paths.

#### Tests

- **`tests/test_native_ndjson.py`** *(NEW)* — 18 parity tests:
  12 fixture inputs (empty file, no-trailing-newline, CRLF / mixed-EOL,
  blank-line patterns, long lines, 100-record stress, etc.) + the
  ``format.read_ndjson`` dispatch test + lineno-fidelity test +
  missing-file ``OSError`` test + 1000-record stress + chunk-
  boundary span test + ``SRMECH_ERR_OVERFLOW`` test (1.25 MiB line
  rejection).
- All 59 existing tests still pass; all 18 native-sha256 tests
  still pass (ABI v2 lift didn't break the v1 surface).

#### Notes on design

- **No JSON parsing in C.** srmech's hot path is the file-IO + line
  tokenisation overhead (Python's text-mode line iteration has
  per-line allocator pressure that adds up across thousand-row
  catalogs). Doing the JSON parse in C would need a vendored JSON
  parser; bytes returned to Python and parsed via
  ``MPRRecord.from_json_line`` is byte-equivalent and avoids that
  surface-area expansion.
- **Static 1 MiB line buffer.** Trade-off: ``srmech_ndjson_iter`` is
  not thread-safe. The two callsites today (Python
  ``format.read_ndjson`` and any future C-side parity test) are
  serial. Phase B6 audit may revisit, but for srmech's data-pipeline
  workload — read a catalog file once, iterate — single-thread is
  the correct model.
- **Eager line collection.** The native path returns a list rather
  than a generator. For the catalog files srmech actually reads
  (small, few KB to a few MB), the eager materialisation is fine.
  If a future use case wants a true generator, the callback can be
  wired to a ``queue.Queue`` + worker thread, but we're not paying
  that complexity until a real need surfaces.

## [0.1.1rc5] - 2026-05-13

### Added — Task #201 Phase B3: SHA-256 C port (first native symbol)

First C/Python parity surface in srmech. Native ``srmech_sha256_hex``
replaces ``hashlib.sha256`` on the hot path used by every adapter's
``attest()`` step. Byte-exact agreement pinned by the new pytest
parity suite in ``tests/test_native_sha256.py`` (18 tests) plus the
C-side smoke tests in ``c/test/test_srmech_sha256.c`` (12 assertions
against FIPS 180-4 fixtures + padding-boundary edge cases).

#### C side (`docs/srmech/c/src/`)

- **`srmech_sha256.c`** — self-contained SHA-256 (FIPS 180-4). No
  OpenSSL / libcrypto dependency. ~200 lines, JPL-Power-of-Ten-
  compatible (bounded loops, no malloc, no goto, ≥2 asserts/fn).
  Public entry: ``srmech_sha256_hex(data, data_len, out_hex)``.
- **`srmech_meta.c`** — ``srmech_version()`` + ``srmech_abi_version()``
  metadata accessors. Called by the Python ctypes shim at load time
  to verify ABI agreement before binding.

The header (`docs/srmech/c/include/srmech.h`) grows
``SRMECH_ABI_VERSION = 1`` and declarations for the three new
symbols.

#### Python side (`docs/srmech/python/srmech/amsc/`)

- **`_native.py`** *(NEW)* — ctypes wrapper mirroring
  ``ephemerides_spectral/_native_bip.py``:
  - ``HAS_NATIVE`` boolean — guards every callsite.
  - ABI-version check at load time; mismatch falls back to Python
    silently (LOAD_ERROR is populated).
  - Three-strategy library discovery: ``srmech.__path__`` walk,
    relative-to-module-file, ``importlib.metadata.files()`` fallback.
    The third strategy is load-bearing for scikit-build-core editable
    installs where the .py files live in the source tree but the
    CMake-installed .so/.dll/.dylib lives in site-packages.
  - ``sha256_hex_c(data) -> str`` — native entry. Handles empty
    bytes correctly (mirrors hashlib.sha256(b"") semantics).
- **`format.py`** — ``sha256_bytes()`` now dispatches to native
  when available, falls back to ``hashlib`` otherwise. The
  user-facing API is unchanged; the implementation is one
  branch deeper.

#### Tests

- **`tests/test_native_sha256.py`** *(NEW)* — 18 parity tests:
  15 fixture inputs (empty, FIPS B.2, B.3, padding boundaries at
  55/56/63/64/65/119/128 bytes, 1 KiB, 64 KiB, 256 KiB),
  ``format.sha256_bytes`` dispatch test, version/ABI lock test,
  200-input randomised parity test. Auto-skipped when
  ``HAS_NATIVE`` is False (pure-Python wheel / Pyodide install).
- **`c/test/test_srmech_sha256.c`** *(NEW)* — 12 C-side asserts
  against FIPS 180-4 vectors + padding edge cases. Exits 0 on
  all-pass.

#### Build

- **`pyproject.toml`** — Phase B2's ``wheel.py-api = "py3"`` +
  ``wheel.platlib = false`` overrides REMOVED. The wheel is now
  legitimately platform-tagged (e.g.
  ``srmech-0.1.1rc5-cp312-cp312-linux_x86_64.whl``) and contains
  ``srmech/_native/libsrmech.{so,dll,dylib}``.
- **`.github/workflows/srmech-publish.yml`** —
  ``build-wheel`` sanity check inverted: rejects py3-none-any
  output (would indicate CMake short-circuited and the .so is
  missing), requires ``srmech/_native/`` to contain a .so / .dll /
  .dylib in the wheel.

#### Phase B7 follow-up

The ``build-wheel`` job still runs on a single Ubuntu cell, so only
the Linux wheel is published at rc5. Mac / Windows users on TestPyPI
get the pure-Python wheel (built by ``build-pure-wheel``) and the
pure-Python ``hashlib`` fallback. Phase B7 adds the cibuildwheel
matrix that produces wheels for all platform/Python combinations.

## [0.1.1rc4] - 2026-05-13

### Infrastructure — Task #201 Phase B2: scikit-build-core + pyproject-pure swap

Switches srmech's build backend from hatchling to **scikit-build-core +
CMake**, mirroring ephemerides-spectral. Adds the
`pyproject-pure.toml` hatchling-fallback file for the Pyodide / WASM
build path. Rewrites `srmech-publish.yml` with the three-job shape
(scikit-build-core wheel + sdist + pure-Python wheel) that mirrors
`ephemerides-spectral-publish.yml`.

**Phase B2 still ships py3-none-any wheels** — until Phase B3 lands
real C code in `docs/srmech/c/src/`, the CMake step short-circuits
to "no library" and the wheel is tagged py3-none-any via the
`wheel.py-api = "py3"` + `wheel.platlib = false` overrides in
pyproject.toml. Both overrides come back OUT at Phase B3 so the
wheel becomes legitimately platform-tagged once the native binary
is real.

#### Added — `pyproject-pure.toml`

Parallel pyproject mirroring `docs/antikythera-maths/ephemerides-spectral/python/pyproject-pure.toml`:

- Uses `hatchling` backend instead of `scikit-build-core`.
- Same `[project]` block (name, version, deps, classifiers, urls) so
  the pure wheel and the platform wheel are interchangeable at
  install time.
- Excludes `srmech/_native/*` from both wheel + sdist so accidental
  rebuild artifacts can't leak in.
- Version-locked to `pyproject.toml`'s version by a workflow guard
  (see "Verify pyproject-pure.toml version matches main" step).

#### Changed — `pyproject.toml`: hatchling → scikit-build-core

- `build-system.requires = ["scikit-build-core>=0.10", "cmake>=3.23"]`
- `build-system.build-backend = "scikit_build_core.build"`
- New `[tool.scikit-build]` block:
  - `cmake.source-dir = ".."` points at `docs/srmech/CMakeLists.txt`
  - `wheel.packages = ["srmech"]`
  - `wheel.py-api = "py3"` + `wheel.platlib = false` — Phase B2 only,
    keeps the wheel py3-none-any while CMake validates the
    infrastructure. Removed at Phase B3.
  - `sdist.include` adds the C tree one directory up (the same
    pattern ephemerides-spectral uses for its CMakeLists.txt + c/).
- `[project.optional-dependencies].dev` gains `scikit-build-core>=0.10`
  and `cmake>=3.23`; retains `hatchling` for the pyproject-pure swap
  build path.

#### Changed — `.github/workflows/srmech-publish.yml`

Replaced the single-`build` job with a three-job pattern mirroring
`ephemerides-spectral-publish.yml`:

- **`build-wheel`** — scikit-build-core wheel via `python -m build
  --wheel` (the `--wheel` flag skips the sdist→wheel detour that
  trips scikit-build-core's `cmake.source-dir=".."` indirection when
  the sdist is unpacked).
- **`build-sdist`** — `python -m build --sdist`, twine-strict-check.
- **`build-pure-wheel`** — swaps in `pyproject-pure.toml` over
  `pyproject.toml` (saved as `.platform`), runs hatchling build,
  restores. Includes the version-match guard + PyPI 512-char
  description guard, copied wholesale from ephemerides-spectral's
  workflow.
- **`publish`** — `needs: [build-wheel, build-sdist, build-pure-wheel]`.
  Same rc-routing logic; `cp -n` dedupe in the artefact-collection
  step handles the case where build-wheel and build-pure-wheel produce
  identically-named wheels at Phase B2 (will not happen at Phase B3+
  when build-wheel becomes platform-tagged).

#### Phase B7 follow-up

`build-wheel` at Phase B7 graduates from a single Ubuntu cell to a
cibuildwheel matrix (Linux / macOS / Windows × py3.10–3.14). The
trigger for that promotion: C/Python parity tests passing in CI
across all three platforms (Phase B5 complete).

## [0.1.1rc3] - 2026-05-13

### Infrastructure — Task #201 Phase B1: srmech C scaffolding

First phase of the **srmech build-out to peer-quality with
ephemerides-spectral** (Task #201). Ships the C tree scaffolding so
Phase B2 can wire scikit-build-core in next. **Pure-Python wheel
contents are byte-identical to rc2** — this release adds files outside
the wheel, no API changes, no behaviour changes.

#### Added — C tree scaffolding (`docs/srmech/c/` + `docs/srmech/CMakeLists.txt`)

Mirrors `docs/antikythera-maths/ephemerides-spectral/c/` layout:

- `c/include/srmech.h` — public C API header. Status enum
  (`srmech_status_t`), version macros, and forward declarations
  for the three planned symbols (`srmech_sha256_hex`,
  `srmech_ndjson_iter`, `srmech_toml_canonical_hash`). No
  definitions yet — those land in Phases B3–B5.
- `c/src/.gitkeep` — empty source directory placeholder.
- `c/test/.gitkeep` — empty test directory placeholder.
- `c/Makefile` — local build/test/parity flow mirroring
  ephemerides-spectral's Makefile. Phase B1 targets noop
  gracefully (no .c files → no .a archive); Phase B3 onward they
  do real work.
- `c/README.md` — phase plan, layout, build instructions.
- `c/JPL_AUDIT.md` — JPL Power-of-Ten audit log placeholder
  (populated in Phase B6).
- `c/.gitignore` — `build/`.
- `c/.pages` — mkdocs nav stub.
- `CMakeLists.txt` (at `docs/srmech/`) — top-level CMake driver,
  mirrors `docs/antikythera-maths/ephemerides-spectral/CMakeLists.txt`.
  At Phase B1 it short-circuits library creation when `c/src/*.c`
  is empty; Phase B2 wires it into pyproject.toml via
  scikit-build-core's `cmake.source-dir = ".."`.

#### Why Phase B1 stops here

The scaffolding is intentionally **inert at rc3**: no .c files means
no library is built, the existing hatchling pyproject.toml backend is
unchanged, and the wheel content is byte-identical to rc2. This
verifies the scaffolding doesn't disturb the existing build before
Phase B2 starts moving the build backend.

#### Phase plan (Task #201 B1–B7)

| Phase | Deliverable                                    | Version    |
| ----- | ---------------------------------------------- | ---------- |
| B1    | C tree scaffolding (this release)              | `0.1.1rc3` |
| B2    | scikit-build-core + CMake + pyproject-pure     | `0.1.1rc4` |
| B3    | `srmech_sha256_hex` — first symbol + parity test | `0.1.1rc5` |
| B4    | `srmech_ndjson_iter` — streaming NDJSON reader | `0.1.1rc6` |
| B5    | `srmech_toml_canonical_hash` — descriptor hash | `0.1.1rc7` |
| B6    | JPL Power-of-Ten audit + JPL_AUDIT.md          | `0.1.1rc8` |
| B7    | cibuildwheel matrix + production v0.2.0 cut    | `0.2.0`    |

Each rc auto-routes to TestPyPI via `srmech-publish.yml`'s rc-suffix
gate; the non-rc `0.2.0` tag is the human-in-loop gate for
production PyPI.

## [0.1.1rc2] - 2026-05-13

### Fixed — hallucination in shipped metadata

- **`pyproject.toml` description, `README.md`, `srmech/__init__.py` docstring**: corrected the package's expanded name from the hallucinated "spectral-resonance mechanism" to the correct **Stored-Relationship Mechanism** (per the srmech research notebook title `# Stored-Relationship Mechanism (srmech) — Research Notebook` and the project memory `project_stored_relationship_mechanism_spike.md`). The error was caught in the TestPyPI verification of v0.1.1rc1 — the wrong text shipped to TestPyPI as srmech-0.1.1rc1's PyPI Summary metadata; rc2 corrects it.
- **`pyproject.toml` keywords**: `"spectral-resonance"` → `"stored-relationship"`.
- **`README.md` Status line** updated to reflect current state (v0.1.0 on PyPI, v0.1.1rcN iterating on TestPyPI toward Task #201 peer-quality cut).

No behaviour or API changes. Wheel + sdist content identical to rc1 except for metadata fields.

## [0.1.1rc1] - 2026-05-13

### Infrastructure — Task #200 Phase A: revert cibuildwheel + add rc-routing

This release reverts the premature cibuildwheel adoption from PR #383
and introduces **rc-suffix auto-routing** in the publish workflow.

#### Reverted (the cibuildwheel mis-application)

- **`.github/workflows/srmech-publish.yml`** restored to the
  single-build-job shape (``python -m build`` produces sdist +
  py3-none-any wheel). cibuildwheel v3.x rejects pure-Python builds
  by design ("Build failed because a pure Python wheel was
  generated") — the matrix that PR #383 introduced was structurally
  incompatible with srmech's current pure-Python state. The
  ``ephemerides-spectral-publish.yml`` template adopted there
  legitimately uses cibuildwheel because that package ships a
  native C library; srmech does not (yet).
- **`docs/srmech/python/pyproject.toml`** ``[tool.cibuildwheel]``
  configuration block removed. Replaced with an explanatory comment
  documenting that cibuildwheel returns once srmech grows the
  C/Python parity surface (Task #201 Phase B).
- The failed ``srmech-v0.1.1`` tag was deleted before any artifact
  reached TestPyPI or PyPI; ``v0.1.0`` remains the current TestPyPI
  release.

#### Added — rc-suffix auto-routing (`srmech-publish.yml`)

- Tag ``srmech-vX.Y.ZrcN`` → publishes to **TestPyPI** (testpypi
  environment) automatically. No manual workflow_dispatch needed.
- Tag ``srmech-vX.Y.Z`` (no rc suffix) → publishes to **PyPI**
  (pypi environment). The act of tagging a non-rc version IS the
  human-in-loop gate for production releases.
- ``workflow_dispatch`` with ``target ∈ {testpypi, pypi}`` retained
  as a manual override path.
- Tag-version regex extended to accept rcN suffix:
  ``r"srmech-v(\d+\.\d+\.\d+(?:rc\d+)?)"``. The version-match
  check now also logs the routing decision so the run page makes
  TestPyPI-vs-PyPI obvious.
- Same rc-routing pattern simultaneously added to
  ``ephemerides-spectral-publish.yml`` for sibling consistency.

#### Version-discipline policy (going forward)

- **Every srmech release between now and peer-quality with
  ephemerides-spectral** ships as an rc on TestPyPI:
  ``0.1.1rc1``, ``0.1.1rc2``, ``0.1.2rc1``, …
- **No non-rc tag pushed** until srmech has Python/C parity, JPL
  Power-of-Ten C standard discipline, scikit-build-core build,
  and cibuildwheel matrix legitimately producing platform wheels.
- Each rc-tagged release is auto-shipped to TestPyPI; the next rc
  iteration is the response to whatever the prior rc-test surfaced.

#### Tests + parity

- All 59 srmech tests pass post-revert (no test changes).
- ephemerides-spectral tests still pass with this srmech version
  (the `srmech>=0.1.0` floor in ephemerides-spectral's
  `pyproject.toml` is satisfied by `0.1.1rc1`; pre-release versions
  resolve normally as PEP 440 allows).

#### History link

Task #200 Phase 1 cibuildwheel adoption (PR #383, merged) → Phase A
revert (this release). The premature cibuildwheel adoption was
caught by the publish workflow's own pure-Python-wheel sanity check
failing under cibuildwheel v3.x's defensive build-time error.

### Notes — Task #197 Phase 4 cleanup (2026-05-13)

Phase 4 is the **final phase** of the AMSC-to-srmech refactor (Task #197). It does
not change the srmech package itself; it cleans up the upstream duplicate copies in
ephemerides-spectral now that Phase 3's import-swap has settled:

- ephemerides-spectral deletes 12 vendored AMSC framework modules (4 top-level +
  8 adapters) from its `_research/` mirror and its `docs/antikythera-maths/research/`
  SSOT. ephemerides-spectral's codegen `_INCLUDED_MODULES` / `_INCLUDED_SUBDIRS`
  are updated to no longer mirror the deleted framework into the wheel.
- ephemerides-spectral's wheel shrinks by ~37 KB (~4.7 %) and its codegen
  `manifest.json` n_files drops from 154 to 142.
- All 5 Phase 1 parity gates remain green at the Phase 4 boundary; srmech
  in-isolation 59/59 tests pass (unchanged from Phase 3); ephemerides-spectral
  pytest is byte-identical to the Phase 3 baseline (2128 passed + 42 skipped
  = 2170 collected).
- `srmech v0.1.0` is now ready for the **first TestPyPI release**. See
  `TESTPYPI_RELEASE_NOTES_v0.1.0.md` in this directory for the release
  procedure (autonomous TestPyPI publish via the `srmech-v0.1.0` tag through
  `.github/workflows/srmech-publish.yml`; PyPI release remains human-in-loop).

## [0.1.0] - 2026-05-13

### Added

- **Initial extract of the AMSC framework from `ephemerides-spectral`** as part of Task #197 (AMSC-to-srmech refactor, Phase 2). The framework lives under `srmech.amsc.*`:
  - `srmech.amsc.format` — Mathematical Provenance Record (MPR) v1 format: `MPRRecord` dataclass, NDJSON streaming IO (`read_ndjson` / `write_ndjson`), `validate_mpr_record`, `sha256_bytes`, schema-version + mandatory-field constants.
  - `srmech.amsc.descriptor` — descriptor TOML loader: `Descriptor`, `load_descriptor`, `discover_descriptors`, `render_template` (deliberately minimal name-substitution + Python format-spec; no Jinja), `descriptor_hash` (canonical-serialised), `DescriptorValidationError`.
  - `srmech.amsc.catalog` — universal bridge surface: `list_attested_sources` (with `adapter_class` filter), `get_attested_dataset` (paginated, T0+T1+T2+T3 tiered), `get_attested_descriptor`, `attestation_audit`, `iter_attested_dataset`, T2 local-kernel overlay (`use_local_kernel` / `clear_local_kernel` / `get_local_kernel_state`).
  - `srmech.amsc.gap_suggester` — schema-gap-driven trigger (`suggest_gap_collections`); the lazy-imported classifier + probe sources are ephemerides-specific and remain in ephemerides-spectral.
  - `srmech.amsc.adapters` — six adapter modules: `html_scraper`, `json_api`, `csv_bulk`, `netcdf_grid` (stub), `geotiff_bbox` (stub), `literature_curated`; plus `_base.py` (`ADAPTERS` registry, `attest`, `parser_rule_hash`, `run` composer).
- **`register_attested_root(path, *, source)`** — the load-bearing cross-package API added in `srmech.amsc.catalog`. Downstream packages whose catalog SSOTs live outside `srmech/amsc/attested/` push their roots at package-import time; subsequent `_descriptors()` calls enumerate the union of srmech's own root + all registered roots in registration order. Conflict policy: first-registered wins with a warning.
- **`list_registered_roots()`** — introspection of currently-registered roots (srmech's own + every external). Used by tests and diagnostic output.
- **`srmech/amsc/attested/`** — empty SSOT subtree reserved for future srmech-primary catalogs (e.g. the `citations_curated` catalog planned for Spike #23).
- **CI workflows** under `.github/workflows/`:
  - `srmech-ci.yml` — pytest on push/PR against `docs/srmech/python/**`, 4-cell matrix (Ubuntu/macOS/Windows × Py3.12 + Ubuntu × Py3.10 floor).
  - `srmech-publish.yml` — build sdist + py3-none-any wheel on `srmech-v*` tag, publish to PyPI via trusted OIDC; manual workflow_dispatch can target TestPyPI.
  - `srmech-autotag.yml` — autotag on `pyproject.toml` version bump.

### Notes

- **Phase 2 is purely additive.** No ephemerides-spectral files are touched. Phase 3 (separate PR, not yet open) will rewire ephemerides-spectral's bridge to import from `srmech.amsc.*`; the byte-identical-wheel parity gate from the Phase 1 scope document applies there, not here.
- **Cross-package gap_suggester deviation.** `srmech.amsc.gap_suggester.suggest_gap_collections()` lazy-imports `.dynamical_regime_catalog` and `.dynamical_regime_probes_data`, which are ephemerides-specific and not shipped by srmech. Calling the function from a context where those modules aren't reachable (e.g. srmech in isolation, no ephemerides installed) will raise `ImportError` at call time. The Phase 1 scope did not flag this; ephemerides-spectral consumers (the only known caller) are unaffected because the relative imports resolve inside ephemerides's `_research/` mirror until Phase 3, then via Phase 3's import-swap.
- **`parser_version` stamp.** Changed from `"ephemerides-spectral X.Y.Z"` to `"srmech X.Y.Z"` in T3 live-fetch attestation blocks: srmech is now the parser. Committed NDJSON files retain whatever `parser_version` was stamped at collection time; only future T3 runs differ. No effect on the Phase 3 wheel parity gate (T3 is runtime, not committed bytes).

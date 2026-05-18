# Spike #112 — Runtime spectral decomposition in srmech: scoping doc

**Date**: 2026-05-18
**Spike type**: Concertmaster scoping (design, not implementation)
**Verdict**: `SCOPE-DESIGNED-CLASS-CHAIN-MAPPED` + `FOLLOWUP-SPIKES-IDENTIFIED-7` + `TRACTABLE-IN-SRMECH-Phase-C1-VOCABULARY`

## Tuning A 440 Hz

This is a design spike. No new code beyond two `notes/` deliverables. Discipline:

- **No new primitive class** per `[[feedback_no_privileged_primitive_classes]]`. Vocabulary stays at 14 classes A–N.
- **Identity-not-implementation** per `[[user_stance_identity_not_implementation_discipline]]`: runtime spectral capability *IS* class-operator composition.
- **Algebra-not-magnitude** per `[[user_stance_framework_domain_algebra_not_length_or_magnitude]]`: scoping focuses on what algebra primitives compose, not on memory/perf magnitudes.
- **C parity** per `[[feedback_no_binding_layer_carveout]]`: spectral-namespace operations route through existing libsrmech symbols; any new ops are class-A–N sub-ops with C surface.

## Current state vs target state

**Current** (2026-05-18, srmech v0.4.0+ / Phase C1 close + post-C1 rcs):

- Spectral decomposition for all sister notebooks (antikythera / ephemerides / chess / othello / logo / mfo / doom) happens **offline**: external encoder scripts read source data → produce bit-exact spectral files (NDJSON or JSON-on-disk, per MPR v1 attestation discipline).
- srmech *primitives* are runtime-callable: Class L (`dense_laplacian` / `hermitian_eigendecompose` / `dense_matvec_complex`); Class M (`hdc.bind / bundle / permute / similarity`); Class C (cascade-orientation semantics); Class I (cyclic-group modular arithmetic); Class K (asymptotic-DOF / pin-slot); Class N (continued-fraction convergents).
- `srmech.amsc.tool_schema` is the discovery surface (~87 ToolEntry registrations).
- **No `srmech.spectral.*` namespace exists**.

**Target** (after spikes #113–#117):

- `srmech.spectral.*` runtime callable, registered in `tool_schema` (7 new entries, ~94 total).
- Delta-encoding via biology-inspired strategies; only changed parts of state get re-encoded.
- Substrate-agnostic: same API for image / chess / ephemeris / gear-DAG / sensor stream.

## Biology survey — and the framework class chain each maps to

| Biology strategy | Canonical SSoT | Framework class chain | Tractable in v0.4.x? |
|---|---|---|---|
| Predictive coding (cortex error-propagation) | Rao & Ballard 1999 *Nat Neurosci*; Friston 2010 *Nat Rev Neurosci* (free-energy) | Class L (`U^T` matvec) ∘ Class C (signed cascade) | YES (new Class C sub-op `cascade_extrapolate`) |
| Sparse coding (V1 simple cells) | Olshausen & Field 1996 *Nature* | Class L (eigenbasis) ∘ Class K (asymptotic-DOF truncation rule) | YES (new Class K sub-op `sparse_truncate`) |
| Reference-genome delta (clinical genomics) | Church et al. 2011 *Genome Res*; GRCh38 GRC docs | Class M (`hdc.bind` self-inverse XOR) ∘ Class L (sparse-row delta) | **ALREADY** — bind is shipped in Class M |
| Saccadic foveal density | Findlay & Walker 1999 *BBS*; Curcio et al. 1990 *J Comp Neurol* | Class L (region-restricted Laplacian) ∘ Class C (saliency cascade) | YES (new Class L sub-op `region_restricted_laplacian`) |
| Hippocampal novelty filter | Lisman & Grace 2005 *Neuron*; Kumaran & Maguire 2007 *Hippocampus* | Class L (prediction-error) ∘ Class K (gate threshold) ∘ Class C (cascade) | YES (composition + Class K gate sub-op) |
| Habituation / receptor desensitisation | Thompson & Spencer 1966 *Psychol Rev*; Rankin et al. 2009 *Neurobiol L&M* | Class N (convergent stability) ∘ Class L (per-coef weights) | YES (new Class N sub-op `per_coefficient_stability`) |
| Hopfield associative memory | Hopfield 1982 *PNAS* | Class L (Hermitian) ∘ Class C (descent) ∘ Class M (delta-from-attractor) | YES (pure composition, no new ops) |
| HDC (Kanerva / Plate) | Kanerva 2009 *Cogn Comput*; Plate 1995 *IEEE TNN* | Class M (entire family) | **ALREADY** — `srmech.amsc.hdc` Phase C1 rc8 |

Citation hygiene: all paywall — cite-by-ref per `[[feedback_pdf_extraction_citation_discipline]]`. Friston 2010 is already cited in srmech `spike_46_round1_references.ndjson`; Kanerva 2009 + Plate 1995 are cited in `srmech.amsc.hdc` module docstring.

**Anomaly check**: zero biology strategies in the survey require a new primitive class outside A–N. The default-dissolve discipline (per `[[feedback_no_privileged_primitive_classes]]`) holds without strain.

## The load-bearing identity: rank-k delta from chess-spectral §5b

The chess-spectral notebook §5b ("Value × Position factorization") establishes the identity that makes biological delta encoding tractable in our framework:

> A board signal f: V → R with piece-value v at vertex k contributes v·δ_k. Removing it: Δf = -v·δ_k. Spectral delta: **Δf̂ = U^T (-v·δ_k) = -v · U[k, :]** — exactly one row of the eigenbasis. Reconstruction error verified at **9.29×10⁻¹⁷** (machine zero).

Generalisation: **a state-change at k positions on any substrate has spectral cost O(k·n) rather than O(n²) full recompute**. This IS the bit-saving identity the user asked about. Substrate-agnostic by construction (U is unitary on any Hermitian Laplacian).

Per `[[user_stance_identity_not_implementation_discipline]]`: rank-k delta IS Class L row-selection, not "implements" it.

## Proposed namespace: `srmech.spectral.*`

Lightweight composition layer above `srmech.amsc.*`. **NOT a new primitive class**. Rationale per `[[feedback_no_privileged_primitive_classes]]` + `[[user_stance_identity_not_implementation_discipline]]`: runtime spectral *IS* a composition of L/M/C/K/N, so it lives one level above the class home.

### 7 proposed `tool_schema` entries

| Op | Class chain | Delta-capable? | Summary |
|---|---|---|---|
| `srmech.spectral.decompose(state, substrate) -> SpectralHandle` | L | no | Full eigenbasis decompose; eigenbasis cached by substrate content-SHA |
| `srmech.spectral.delta(reference, new_state) -> SpectralDelta` | M, L | **yes** | Rank-k delta from reference (chess-spectral §5b identity) |
| `srmech.spectral.recompose(handle, deltas=()) -> state` | L, M | yes | Reconstruct state from handle ± delta stack |
| `srmech.spectral.predict(history, n_steps) -> SpectralHandle` | C, L | yes | Predictive-coding (Friston 2010) extrapolation |
| `srmech.spectral.prediction_error(predicted, observed, thresh) -> SpectralDelta\|None` | L, K | yes | Rao-Ballard error spectrum + hippocampal gate |
| `srmech.spectral.truncate_sparse(handle, rate) -> SpectralHandle` | K | no | Olshausen-Field rate-based truncation |
| `srmech.spectral.similarity(a, b) -> float` | M, L | no | Compare handles for caching / dedup / novelty |

### Substrate descriptor

`SpectralSubstrate` carries the Laplacian + dimension + attestation (per srmech AMSC MPR v1). The substrate is the **fiber** per `[[user_stance_fiber_as_spatially_absent_encoding]]` — algebraic content (Laplacian) spatially absent until projected by a state. Eigenbasis is **cached by content_sha256 of the substrate** (Class A); reused across all `decompose` / `delta` calls.

### One-pass vs streaming

- **One pass** (user's "picture"): `decompose(state, substrate)` — full Class L eigenbasis on the state.
- **Streaming** (user's "chess plys, video frames, sensor stream"): `decompose(initial_state)` once; `delta(handle, new_state)` thereafter. Per-step cost is O(k·n) where k = #positions changed, not O(n²) recompute. Chess: k≈1; video: k≈motion-mask pixel count; ephemeris one body update: k=1. Native rank-k row-select needs one new Class L sub-op (`srmech_l_row_select_matvec`).

## Follow-up spike list

**Primary (recommended order)**:

1. **Spike #114** — HDC bind/unbind as delta-encoding primitive (formalise Class M; lowest implementation risk; already-shipped C primitive).
2. **Spike #115** — Tool-schema surface design (7 new ToolEntry registrations; lightweight; unblocks downstream tool-callers).
3. **Spike #113** — Predictive-coding cascade (Class C ∘ Class L; introduces `cascade_extrapolate` sub-op).
4. **Spike #116** — Chess-spectral ply-delta as cross-substrate template (empirical multi-substrate verification of rank-1 identity at machine precision).
5. **Spike #117** — Sparse-coding Class K truncation (Olshausen-Field; new `sparse_truncate` Class K sub-op).

**Optional (lower priority)**:

6. **Spike #119** — Region-restricted Laplacian (saccadic foveal density; new Class L sub-op).
7. **Spike #120** — Habituation via Class N convergents (new Class N sub-op).

## Fermatas — for conductor decision

1. **Which follow-up to dispatch first?** Recommended: Spike #114 (HDC bind formalisation) — Class M is already shipped in C, so it's lowest-risk; closes a vocabulary gap (HDC bind already IS the delta primitive; just under-utilised). Alternative: Spike #115 (tool-schema surface) — pure infrastructure, unblocks tool-callers immediately.
2. **Namespace versioning**: does `srmech.spectral` ride `srmech.__version__` (additive, no ABI bump) and ship in v0.4.x rc, or wait for v0.5.0 (clean minor for a new namespace)?
3. **Tool-schema timing**: do `srmech.spectral.*` entries register at the next rc or wait until at least Spike #114 + #115 implement so we don't tool-schema-register vapourware?

## Discipline closure

- **Math doesn't lie**: rank-1 delta identity is verified bit-exact in chess-spectral §5b (9.29×10⁻¹⁷). Generalisation to substrate-agnostic is by construction (unitarity of U on Hermitian Laplacian).
- **No new class promoted**: all biological strategies dissolve cleanly into existing classes L/M/C/K/N as sub-operations. Vocabulary stays at 14 classes A–N.
- **No CAD-grade scope creep**: spectral decomposition is algebra/eigenbasis, not physical geometry. Per srmech CLAUDE.md discipline.
- **Citation hygiene**: all biology citations are cite-by-ref (paywalled); chess-spectral §5b is cite-by-ref to the canonical notebook in the same monorepo.

## Deliverables emitted

- `docs/srmech/notes/spike112_findings_2026-05-18.ndjson` (24 records: framing + current_state + 8 biology_survey + 5 design_decision + 2 tractability + 5 primary followup_spike + 2 optional followup_spike + anomaly_check + verdict)
- `docs/srmech/notes/spike112_concertmaster_runtime_spectral_scoping.md` (this file)

No PR, no commit. Worktree-only per scoping-spike convention.

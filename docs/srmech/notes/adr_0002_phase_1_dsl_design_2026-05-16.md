# ADR-0002 Phase 1 — operator-chain DSL design + worked examples + spike

**Date:** 2026-05-16.
**Phase:** ADR-0002 Phase 1 (operator-chain DSL design).
**Author:** Concertmaster (high-effort, cross-cutting dispatch under
`[[feedback_orchestration_metaphor]]`).
**Sprint:** 0.4.1rc4 — folds into the active cosmos-catalog sprint per
`[[feedback_rc_stacking_versioning]]`; clean 0.4.1 ships when sprint accumulates
the full Phase 1+ surface.
**Branch:** `feat/srmech-cosmos-catalog`.

---

## 1. What landed

| Artefact | Path | Lines |
|---|---|---|
| Schema specification | `docs/srmech/adr/0002-phase-1-operator-chain-schema.md` | ~330 |
| Worked chain — `multipole_vector_axis` | `docs/srmech/python/srmech/amsc/attested/cmb_low_ell_maps/descriptor.toml` | +30 (4 steps) |
| Worked chain — `t_vs_e_axis_differential` | `docs/srmech/python/srmech/amsc/attested/cmb_low_ell_maps/descriptor.toml` | +37 (5 steps) |
| Worked chain — `acoustic_peak_locations` | `docs/srmech/python/srmech/amsc/attested/cmb_polarisation_spectra/descriptor.toml` | +25 (3 steps) |
| Worked chain — `f_NL_template_combination` | `docs/srmech/python/srmech/amsc/attested/cmb_bispectrum/descriptor.toml` | +28 (3 steps) |
| This report | `docs/srmech/notes/adr_0002_phase_1_dsl_design_2026-05-16.md` | this file |
| Version bumps (4 SSOT files + CHANGELOG.md) | various | +18 total |

Four chains across three catalogs. All four parse cleanly via Python 3.14
`tomllib.load`. **No new C symbols** — schema v1 is descriptor-shape data
only; the composition engine implementation is Phase 2 scope.

## 2. Schema-design decisions (resolutions to the 7 concerns)

The conductor's brief enumerated 7 schema-design concerns; resolutions:

| Concern | Resolution |
|---|---|
| 1. Step shape | `class` + `op` + `args` (+ optional per-step `on_error`). Three required keys; one optional. Tight closure. |
| 2. Data flow | Linear pipeline. Explicit `@step[N].output` references — no implicit threading. Reductions are linear (multiple `@step[]` refs in one step). No DAG / no branching in v1. |
| 3. Input binding | Reference DSL: `@row.<col>`, `@input.<name>`, `@catalog.<key>.<col>`, `@step[N].output`. Engine resolves at runtime; bridge surface is `bridge.run_operator_chain(catalog_key, chain_name, **inputs)`. |
| 4. Return shape | Typed-string `returns = "<type>  # <comment>"` parseable via `typing` utilities. No structured `return_schema` in v1; Phase 2 may revisit. |
| 5. Error policy | Default `raise`; `warn_return_none` and `skip` opt-in. Per-step override allowed. |
| 6. Versioning | `[catalog].chain_schema_version = 1` required when `operator_chain` declared. Forward-compatible. |
| 7. Reference DSL | Small grammar with four namespaces (`row`, `input`, `step`, `catalog`); dotted-path with optional `[N]` indexers. Validated at chain activation. |

## 3. The four worked-example chains

### 3.1 `cmb_low_ell_maps :: multipole_vector_axis` (4 steps, classes L+L+D+A)

Extracts the AoE preferred axis from a CMB sky map at fixed ℓ. Step 0
decomposes the FITS sky map into spherical harmonic coefficients (Class L,
new op `spherical_harmonic_decompose`). Step 1 extracts the preferred-axis
candidates by maximising Σ|a_ℓm|² cos(2mφ) over rotations (Class L, new op
`extract_preferred_axis`). Step 2 dispatches on the argmax (Class D, new op
`dispatch_on_max_extremum`). Step 3 content-addresses the axis tuple
(Class A, existing `content_address` semantics via `format.sha256_bytes`).

**Canonical SSoT:** de Oliveira-Costa et al. 2004 *Phys.Rev.D* 69:063516 §III.

### 3.2 `cmb_low_ell_maps :: t_vs_e_axis_differential` (5 steps, L+L+L+L+I)

The Spike #26 Phase 2 target. Runs `multipole_vector_axis` independently
on T (temperature) and E (E-mode polarisation) channels of the same
component-separated sky map at ℓ=2, then computes the great-circle angular
separation between the two axes (Class I, new op `angular_separation_axes`
with antipodal-symmetry collapse — axes not vectors so the result lives in
[0°, 90°]).

**Falsifier hook:** §VII.6.3.1 predicts Δθ_TE central range 1.0°–2.0° across
recombination visibility Δz ∈ [10, 50]; threshold for framework falsification
is Δθ_TE < 0.1°. This chain IS the falsifier.

**Canonical SSoT:** de Oliveira-Costa et al. 2004 §III + Planck 2018 IV
diffuse component separation A&A 641 A4 + Planck 2018 V CMB power spectra
A&A 641 A5.

### 3.3 `cmb_polarisation_spectra :: acoustic_peak_locations` (3 steps, C+D+E)

Streams binned bandpower rows (Class C `read_ndjson`), filters by feature
(Class D `match_filter` against a 9-needle peak/trough/lobe needle list),
extracts (ℓ_center, D_ℓ_μK², feature) sorted by ℓ (Class E
`sorted_lookup_extract`). Returns the canonical TT/TE/EE acoustic peak
table for the catalog.

**Canonical SSoT:** Planck 2018 V Aghanim et al. 2020 A&A 641 A5 §3.2,
§3.4 (PR3 R3.02 binned bandpowers).

### 3.4 `cmb_bispectrum :: f_NL_template_combination` (3 steps, E+N+A)

Looks up the SMICA T+E KSW lensing-subtracted f_NL for each of the three
canonical templates (local / equilateral / orthogonal) via Class E batch
sorted-lookup; expresses each (value/error) factor in continued-fraction
rational form via Class N (preserves the cosmos-catalog rational-form
discipline per `[[user_stance_kepler_shape_universal]]`); content-addresses
the joint signature via Class A SHA-256.

**Canonical SSoT:** Planck 2018 IX Akrami et al. 2020 A&A 641 A9 Table 5
(headline KSW lensing-subtracted SMICA T+E entries from Table 6 are
authored verbatim in the cmb_bispectrum row.ndjson).

## 4. The spike — closed-form TDSE evolution doesn't fit cleanly

**Picked candidate:** `srmech.qm.single_particle.tdse_evolve(H, ψ, t)` —
closed-form time-dependent Schrödinger evolution `ψ(t) = V · diag(exp(-iλt)) · V^H · ψ(0)`
where `(λ, V) = numpy.linalg.eigh(H)`. Sakurai *Modern QM* §2.1.5 eq 2.1.40.
Five conceptual steps: eigendecompose, change-of-basis ψ → eigenbasis,
elementwise complex phase factor `exp(-iλt)`, elementwise multiply against
ψ_eig, change-of-basis back.

**Where it fits cleanly:** Step 0 — Hermitian eigendecomposition lives in
Class L (graph-Laplacian today; needs broadening to complex Hermitian).
The eigendecomposition itself is the same operation Class L's existing
`jacobi_eigvals` performs, just with complex Hermitian inputs.

**Where it doesn't fit cleanly:**

1. **General complex matrix-vector multiplication.** Steps 1 and 4
   (change of basis) need to apply a complex unitary to a complex vector.
   No A–N class has an op for "general complex matvec". Class L's existing
   ops are real-symmetric-adjacency-shaped.

2. **Elementwise transcendental over complex arrays.** Step 2 computes
   `exp(-iλt)` over an n-dimensional vector. No A–N class has a
   "transcendental over arrays" op. (Class K's pin_slot uses cos/sin on
   scalars only; Class L's Jacobi uses real c/s computed algebraically
   without transcendental calls.)

3. **Elementwise multiplication of complex arrays.** Step 3 computes
   the diagonal-times-vector product `phase * ψ_eig`. No A–N class has
   a "vectorised elementwise multiply".

**Proposed Phase 2 refinement: broaden Class L scope.**

Per `[[feedback_no_privileged_primitive_classes]]` ("dissolve before
promote"), the safer move is to broaden Class L's identity from
"graph Laplacian" to "dense-matrix linear algebra including
eigendecomposition + matrix-vector multiplication + elementwise
operations on dense arrays". Specifically Phase 2 adds the following
ops to Class L:

- `hermitian_eigendecompose(H) -> (eigvals, V)` — complex Hermitian
  generalisation of `jacobi_eigvals`.
- `dense_matvec_complex(M, v) -> M @ v` — general complex matvec.
- `elementwise_multiply_complex(a, b) -> a * b` — vectorised pointwise.
- `elementwise_transcendental(arr, op_name)` where
  `op_name ∈ {"exp", "cos", "sin", "log", ...}` — array-vectorised
  transcendental.

These extend Class L's surface without introducing a new primitive
class. **Class L's identity** under the broadening becomes "dense-matrix
algebra including eigendecomposition"; graph-Laplacian-specific ops
(`dense_laplacian`, `normalized_laplacian`) become specialisations.
This matches the Phase C1 audit's substance: the operation Class L
already performs (pi-free Jacobi eigendecomposition) is the
mathematical content; "graph Laplacian" was the headline application,
not the identity.

**Alternative considered and rejected: new Class P.** A "Class P =
elementwise transcendental over arrays" candidate could be raised.
Per `[[feedback_no_privileged_primitive_classes]]` the dissolve-first
discipline applies: the structural-irreducibility threshold for new
class promotion is high. Elementwise transcendentals on arrays are
mathematically already inside Class L's eigendecomposition machinery
(Jacobi rotations need elementwise sin/cos under the hood; the
algebraic c/s construction is the project's pi-free trick, but the
mathematical scope of "transcendental functions on real / complex
inputs" is already the same scope as Class L's eigendecomposition).
**Class L gets the new ops, no Class P promoted.**

**Phase 2 implementation note:** the composition engine must support
array-typed `@step[N].output` references. The current eigvecs/eigvals
output of `hermitian_eigendecompose` is a complex `numpy.ndarray`, not
a scalar. The reference DSL handles arbitrary object types fine, but
the validator + tool-schema generator need shape-awareness for
array-typed step outputs (cf. open question 11.5 in the schema doc).

## 5. Validation evidence

```
python -c "
import tomllib
for path in ['srmech/amsc/attested/cmb_low_ell_maps/descriptor.toml',
             'srmech/amsc/attested/cmb_polarisation_spectra/descriptor.toml',
             'srmech/amsc/attested/cmb_bispectrum/descriptor.toml',
             'srmech/amsc/attested/cmb_lensing/descriptor.toml']:
    with open(path, 'rb') as f:
        d = tomllib.load(f)
    chains = d.get('catalog', {}).get('operator_chain', [])
    v = d.get('catalog', {}).get('chain_schema_version', None)
    print(f'{path}: schema_version={v}, n_chains={len(chains)}', [(c['name'], len(c['steps'])) for c in chains])
"

cmb_low_ell_maps/descriptor.toml: schema_version=1, n_chains=2
  [('multipole_vector_axis', 4), ('t_vs_e_axis_differential', 5)]
cmb_polarisation_spectra/descriptor.toml: schema_version=1, n_chains=1
  [('acoustic_peak_locations', 3)]
cmb_bispectrum/descriptor.toml: schema_version=1, n_chains=1
  [('f_NL_template_combination', 3)]
cmb_lensing/descriptor.toml: schema_version=None, n_chains=0 []
```

`cmb_lensing` deliberately not edited — schema v1 is OPTIONAL per
the schema design, and that catalog's derived calculations are
in scope for a separate Phase 2 follow-up (lensing reconstruction
amplitude × power-spectrum normalisation chain). The schema's
optionality means existing catalogs that ship no chains are unaffected.

## 6. Open questions for Phase 2

These are NOT blockers; they're "decide when the case arises" items
documented in the schema doc §11 in more detail.

1. **Branching / conditional chains.** Real consumer code (e.g.
   "if SMICA available use SMICA, else fall back to NILC") needs
   runtime conditionality. v1 punts to "two chains + a Class D
   dispatch step at the boundary".
2. **Class L scope clarification.** §4 of this report's spike
   broadens Class L's identity to "dense-matrix linear algebra".
   Phase 2 formalisation in docstring + JPL audit + C-side surface.
3. **Iteration steps.** Newton iteration / fixed-point solves
   currently encapsulate inside a single class op (Class K's
   `kepler_solve`). Schema needs a chain-level iteration mechanism
   for self-consistent multi-step solves.
4. **Cross-source reduction.** Multi-catalog statistics (e.g. joint
   χ² across observables) — v1 punts to a Python orchestrator
   above the chain layer. Phase 2 may add reduction-step semantics.
5. **Auto-derived tool-schema parameter types.** `@input.<name>`
   references need types. Likely Phase 2 adds an
   `[catalog.operator_chain.inputs]` declaration table.
6. **Versioned op evolution.** When a class-op signature changes
   between srmech minor versions, what's the contract? Likely
   captured by package version pinning, not schema-level.
7. **Plugin acceleration byte-parity.** When a plugin provides an
   accelerated implementation of e.g. `spherical_harmonic_decompose`,
   the byte-parity test discipline (or numerical-tolerance equivalence
   for FP classes) must apply — ADR-0002 §6 Phase 5.

## 7. Cross-references

- `docs/srmech/adr/0002-catalog-as-computation.md` — parent ADR-0002.
- `docs/srmech/adr/0002-phase-1-operator-chain-schema.md` — the schema
  specification this report summarises.
- `docs/srmech/adr/0001-profile-pattern.md` — descriptor TOML schema
  this extends.
- `docs/antikythera-maths/research-mfo/vii_6_3_1_prediction_verification_scope_2026-05-16.md`
  — Spike #26 Phase 2 scope artefact; the `t_vs_e_axis_differential`
  chain IS the implementation surface for this analysis.
- Spike #24 (multiple notes in `docs/srmech/notes/`) — the 14-class
  vocabulary the chains compose over.
- `[[feedback_no_privileged_primitive_classes]]` — class-promotion
  discipline that drove the §4 spike's dissolve-into-Class-L conclusion.
- `[[feedback_no_mvp_framing]]` — full-coverage discipline; schema
  covers the full surface needed by the four cosmos chains + the
  TDSE spike's expansion question.
- `[[feedback_no_binding_layer_carveout]]` — every class op referenced
  by a chain is expected to land its C surface eventually.
- `[[feedback_rc_stacking_versioning]]` — this Phase 1 ship is rc4
  of the active 0.4.1 cosmos catalog sprint.

## 8. Verdict

**Schema v1 candidate ready for Phase 2 implementation.** Four chains
across three catalogs landed cleanly; TOML round-trips; tdse_evolve
spike surfaced a real Class L scope-broadening question that has a
clear dissolve-into-existing-class answer.

The schema is candidate-not-endorsed under
`[[feedback_no_lineage_claims_in_notebook]]`'s humility discipline.
Phase 2 (composition engine implementation) and Phase 3 (auto-derived
tool-schema) will exercise the schema in earnest; revisions land as
cumulative rcs on the active sprint.

No fermata — no conductor input required mid-Phase 1. The seven
schema-design concerns resolved with explicit choices; the spike
landed with a clean refinement proposal; the four worked chains
are real, not synthetic.

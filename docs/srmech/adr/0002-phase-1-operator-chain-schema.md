# ADR-0002 Phase 1: Operator-chain DSL — schema specification

**Status:** Phase 1 candidate (schema v1). Schema is a candidate-not-endorsed under
`[[feedback_no_lineage_claims_in_notebook]]`'s humility discipline; Phase 2 implementation
validation will exercise the shape and surface revisions.
**Date:** 2026-05-16.
**Authors:** Steven Kirkland + Claude Opus 4.7 (concertmaster dispatch).
**Status of parent ADR:** ADR-0002 (catalog-as-computation) Draft.
**Relates to:** ADR-0002 §3 (the sketch this document formalises),
ADR-0001 §3 (descriptor TOML schema this extends).

---

## 1. Scope

ADR-0002 §3 sketched a starting operator-chain DSL. This document promotes the
sketch to a **schema v1 candidate** by resolving the seven open design concerns
the conductor's Phase 1 brief enumerated:

1. Step shape — `class`, `op`, `args` semantics; nesting; literal-vs-reference policy.
2. Data flow between steps — linear vs DAG vs reductions.
3. Input binding — how chains consume catalog data rows.
4. Return shape — annotation discipline.
5. Error policy — raise / skip / warn semantics.
6. Versioning — `chain_schema_version` field placement.
7. Argument-reference DSL — a small reference grammar so step args can point at
   row columns, descriptor fields, prior-step outputs, or runtime inputs.

The schema lands in 3 catalogs as worked examples (`cmb_low_ell_maps`,
`cmb_polarisation_spectra`, `cmb_bispectrum`). The spike is one calculation
that does NOT fit cleanly: closed-form TDSE evolution `ψ(t) = U(t)·ψ(0)` —
documented in §10 below with a proposed Phase 2 refinement.

## 2. Schema v1 in TOML form

The descriptor TOML schema (per ADR-0001 §3) gains a new optional top-level
field plus chain + per-step array-of-table subsections. **TOML inline tables
must be single-line**; the canonical layout uses TOML's nested array-of-tables
syntax (`[[catalog.operator_chain]]` for each chain, `[[catalog.operator_chain.steps]]`
for each step) which permits multi-line per step while keeping `args`
single-line inline:

```toml
[catalog]
chain_schema_version = 1

[[catalog.operator_chain]]
name = "multipole_vector_axis"
summary = "Extract preferred-direction axis at fixed ℓ from a CMB sky map (per de Oliveira-Costa 2004 §III)"
returns = "tuple[float, float]  # (galactic_l_deg, galactic_b_deg)"
on_error = "raise"                  # default; "skip" / "warn_return_none" also legal

[[catalog.operator_chain.steps]]
class = "L"
op = "spherical_harmonic_decompose"
args = { input_bytes = "@input.fits_bytes", channel = "T", healpix_nside = "@row.healpix_nside", ell_max = "@row.ell_max_recommended" }

[[catalog.operator_chain.steps]]
class = "L"
op = "extract_preferred_axis"
args = { alm = "@step[0].output", ell_target = 2, extremum_spectrum = "max_sum_axes" }

[[catalog.operator_chain.steps]]
class = "D"
op = "dispatch_on_max_extremum"
args = { axis_candidates = "@step[1].output", selection_rule = "argmax_sum_alm_sq_cos_2mphi" }

[[catalog.operator_chain.steps]]
class = "A"
op = "content_address"
args = { algo = "sha256", payload = "@step[2].output" }
```

`@row.X` resolves against the current MPR row's `data` block. `@input.X`
is a runtime parameter (e.g. fetched FITS bytes for catalogs that don't
commit large blobs). `@step[N].output` references the output of the
zero-indexed Nth step. `@catalog.X` references a different catalog by key,
with `srmech.amsc.catalog.get_attested_dataset` used under the hood.

**TOML-syntax note (resolved 2026-05-16 at Phase 1 cut):** the original
ADR-0002 §3 sketch used `steps = [ { ... }, { ... } ]` with multi-line inline
tables; this fails `tomllib.load` because TOML's grammar forbids newlines
inside inline tables. The canonical form lifts each step to its own
`[[catalog.operator_chain.steps]]` array-of-tables entry. Same semantic
content; valid TOML; tested via `python -m tomllib` round-trip across
all four worked-example chains.

## 3. Resolved design questions

### 3.1 Step shape (concern 1)

A step is a TOML inline table with **exactly three keys**:

| Key | Type | Semantics |
|---|---|---|
| `class` | string, single letter A–N | Primitive class identifier per Spike #24 + Phase C1. Must resolve to `srmech.amsc.<class>` (lowercase class home: `format`, `tlv`, `dispatch`, `catalog`, `template`, `search`, `cyclic`, `primes`, `kepler`, `laplacian`, `hdc`, `rational`) |
| `op` | string | Operation name within the class. Must be a public callable on the class module. The composition engine validates at activation time |
| `args` | inline table | Free-form key/value. Nesting allowed (TOML inline tables and arrays). Each value is either a **literal** (string / number / bool / array / inline table) or a **reference** (string matching the reference DSL — see §3.7) |

A step MAY add `on_error = "..."` to override the chain-level policy.

**No additional top-level keys per step.** This is the closure: a step is
exactly `class + op + args [+ on_error]`. Steps that need richer semantics
(branching, conditional execution) decompose into multiple steps or — in the
v1 schema's deliberate limitation — extend into a Phase 2 refinement.

### 3.2 Data flow between steps (concern 2)

**Linear pipeline by default.** Each step's `args` may use `@step[N].output`
references; if a step's `args` contains no such references, the previous
step's output is **not** implicitly passed. (No implicit threading. Every
data dependency is explicit.) The decision pushes back on the "magic implicit
piping" pattern that complicates audit; explicit-only matches MPM discipline.

**Reductions are linear.** A step can reference `@step[2].output` AND
`@step[5].output` in its args; the runtime resolves both before invocation.
No new construct needed for reductions — they're a natural use of the args
grammar.

**No DAG / no branching.** The v1 schema is strictly a finite list of steps
in declaration order. A chain that needs runtime branching is either:
- Decomposed into two chains, with a `D` (dispatch) step at the boundary,
- Or surfaces as a Phase 2 schema extension (see open question 11.1).

### 3.3 Input binding (concern 3)

Three references resolve to "outside the chain":

- **`@row.<dotted.field>`** — current row's `data` block (the MPR record). Dotted
  paths drill into nested structures (e.g. `@row.stokes_components_available[0]`).
- **`@catalog.<row_key>.<dotted.field>`** — cross-catalog lookup. Engine calls
  `get_attested_dataset(catalog_key=<via context>, row_key=<row_key>)`; throws if
  ambiguous (no catalog context at registration).
- **`@input.<name>`** — runtime parameter passed via
  `bridge.run_operator_chain(catalog_key, chain_name, **inputs)`. Allows
  catalogs that don't commit large blobs (`cmb_low_ell_maps`, `cmb_lensing`)
  to receive fetched bytes / arrays at runtime without committing them.

The chain's invocation surface (Python) takes the catalog key plus the chain
name plus any `@input.X` references the chain declares:

```python
bridge.run_operator_chain(
    "cmb_low_ell_maps", "multipole_vector_axis",
    row=row_dict, fits_bytes=open(fits_path, "rb").read(),
)
```

### 3.4 Return shape (concern 4)

`returns = "<type>  # <comment>"` — single string with a Python-style type
annotation followed by an optional inline comment after `#`. The annotation
is the canonical machine-readable surface; the comment is the human-readable
gloss for tool-schema generation.

Multi-return types use Python type-annotation syntax:
- Single value: `"float  # radians"`
- Tuple: `"tuple[float, float]  # (l_deg, b_deg)"`
- List: `"list[tuple[int, float, str]]  # (ell, D_ell, peak_type)"`
- Optional: `"Optional[float]  # None if input was masked"`

For tool-schema generation, the engine parses the annotation via `typing`
module utilities (or a lightweight string parser at registration). No
structured `return_schema` subsection in v1 — the typed-string approach is
sufficient for the cosmos catalog chains; Phase 2 may revisit if richer
structured returns surface real needs.

### 3.5 Error policy (concern 5)

Three policies, set at chain-level via `on_error = "..."`:

- **`"raise"`** (default) — exceptions propagate. Calling code catches.
- **`"warn_return_none"`** — log warning + return `None`. Useful for tool-schema
  agents that prefer graceful degradation.
- **`"skip"`** — only valid in batch-execution contexts; skips the current row
  and continues. Not for single-chain calls.

Step-level `on_error` overrides chain-level for that step only.

The default-raise discipline aligns with MPM: errors are signal. Skipping is
opt-in, never default.

### 3.6 Versioning (concern 6)

A new top-level catalog field declares the schema version this catalog uses:

```toml
[catalog]
chain_schema_version = 1
```

The field is **required** for catalogs that ship any `[[catalog.operator_chain]]`
entry. Absence = catalog has no chains (most current catalogs). Forward
compatibility: when v2 ships, the engine reads the field and dispatches to
the appropriate parser; v1 chains keep working without rewrite.

### 3.7 Argument-reference DSL (concern 7 — new)

The args mini-grammar:

```
arg-value     := literal | reference
literal       := <any TOML scalar / array / table — passed verbatim>
reference     := "@" namespace "." path
namespace     := "row" | "input" | "catalog" | "step"
path          := <dotted-path with optional [N] indexers>
                 row:     "<column>" or "<column>.<nested>" or "<column>[N]"
                 input:   "<name>" or "<name>.<nested>"
                 catalog: "<row_key>.<column>"
                 step:    "[N].output" or "[N].<output_field>"
```

Step indexers are zero-based; `@step[0]` is the first step. A reference
that begins with `@` but does not match the grammar raises a validation
error at chain-activation time.

A literal that happens to start with `@` (rare) must be quoted as a TOML
string that the reference parser explicitly rejects; alternatively, escape
via `args = { foo = ["@unparsed", { literal = "@foo" }] }` — but in practice
no current cosmos catalog value starts with `@`, so this is theoretical.

## 4. JSON Schema for the descriptor extension

A machine-readable schema for the new section (drop-in for descriptor
validation pipelines):

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "srmech.amsc.operator_chain.v1",
  "type": "object",
  "properties": {
    "catalog": {
      "type": "object",
      "properties": {
        "chain_schema_version": {
          "type": "integer",
          "enum": [1]
        },
        "operator_chain": {
          "type": "array",
          "items": { "$ref": "#/definitions/chain" }
        }
      }
    }
  },
  "definitions": {
    "chain": {
      "type": "object",
      "required": ["name", "summary", "returns", "steps"],
      "properties": {
        "name": { "type": "string", "pattern": "^[a-z][a-z0-9_]*$" },
        "summary": { "type": "string", "minLength": 1 },
        "returns": { "type": "string", "pattern": ".+" },
        "on_error": {
          "type": "string",
          "enum": ["raise", "warn_return_none", "skip"],
          "default": "raise"
        },
        "steps": {
          "type": "array",
          "minItems": 1,
          "items": { "$ref": "#/definitions/step" }
        }
      },
      "additionalProperties": false
    },
    "step": {
      "type": "object",
      "required": ["class", "op", "args"],
      "properties": {
        "class": {
          "type": "string",
          "pattern": "^[A-N]$"
        },
        "op": { "type": "string", "minLength": 1 },
        "args": { "type": "object" },
        "on_error": {
          "type": "string",
          "enum": ["raise", "warn_return_none", "skip"]
        }
      },
      "additionalProperties": false
    }
  }
}
```

## 5. Class → module mapping (registration-time)

The composition engine maps single-letter class IDs to lowercase
`srmech.amsc.<module>`:

| Class | Module | Public operations (Phase C1 surface) |
|---|---|---|
| A | `srmech.amsc.format` | `sha256_bytes`, `read_ndjson`, `write_ndjson`, `validate_mpr_record` |
| B | `srmech.amsc.tlv` | `tlv_pack` |
| C | `srmech.amsc.format` (`read_ndjson`) | streaming iterator |
| D | `srmech.amsc.dispatch` | `match` |
| E | `srmech.amsc.catalog` | `get_attested_dataset`, `list_attested_sources` |
| F | `srmech.amsc.template` | `render` |
| G | `srmech.amsc.search` | `byte_search` |
| H | `srmech.amsc._native` | `srmech_version`, `srmech_abi_version` |
| I | `srmech.amsc.cyclic` | `gcd`, `lcm`, `mod_add`, `mod_mul`, `mod_pow`, `mod_inv` |
| J | `srmech.amsc.primes` | `is_prime`, `factor`, `cyclic_period` |
| K | `srmech.amsc.kepler` | `pin_slot`, `kepler_solve`, `equation_of_centre` |
| L | `srmech.amsc.laplacian` | `dense_adjacency`, `dense_laplacian`, `normalized_laplacian`, `jacobi_eigvals` |
| M | `srmech.amsc.hdc` | `bind`, `bundle`, `permute`, `similarity` |
| N | `srmech.amsc.rational` | `continued_fraction`, `best_rational` |

**Phase 2 task:** extend Class L with `spherical_harmonic_decompose`,
`extract_preferred_axis`, `eigendecompose`, `signed_laplacian_eigvals`
(the dissolved Class O signed-Laplacian-variant per `[[project_class_o_signed_metric_composition]]`).
Extend Class D with `dispatch_on_max_extremum` and other catalog-specific
dispatch ops. These are new ops on existing classes — no new primitive
class introduced.

## 6. Auto-generated tool-schema entries

Each declared chain produces one tool-schema entry at catalog activation:

```python
ToolEntry(
    name=f"{catalog_key}.{chain.name}",
    summary=chain.summary,
    returns=chain.returns,
    parameters={
        # Synthesised from chain's @input.* references + @row.* requirements
    },
    provenance=[
        f"step[{i}]: {step.class}.{step.op}({redacted_args})"
        for i, step in enumerate(chain.steps)
    ],
    canonical_ssot_citation=catalog.cite_as_template.split(";")[0],
)
```

The catalog's `cite_as_template` provides the canonical-SSoT citation; the
chain's `summary` carries the per-operation context (e.g. "per de Oliveira-Costa
2004 §III"); the per-step `class.op(args)` lines provide audit-trail provenance.

This eliminates the 9 per-source hand-authored ToolEntry registrations the
cosmos catalog rc1 report flagged as a loose end.

## 7. Validation discipline

At catalog activation, the engine validates **before any execution**:

1. **Class identifiers** are A–N.
2. **Module resolution** — `srmech.amsc.<module>` imports cleanly.
3. **Operation existence** — `getattr(module, op)` exists and is callable.
4. **Reference syntax** — every `@`-prefixed string in args matches the grammar.
5. **Step-reference bounds** — every `@step[N]` has `N < current_step_index`.
6. **Return-type parse** — `returns` string parses via `typing.get_type_hints`
   or a lightweight regex-based fallback.
7. **`chain_schema_version` present** when `operator_chain` is declared.

Failures raise `OperatorChainValidationError` at catalog import; no chain
ever executes with an invalid declaration. (Matches the AMSC framework's
attestation-validation-at-load discipline.)

## 8. Tool-schema generation gotcha: `@catalog.X` cross-references

A chain that references `@catalog.<other_catalog_key>.<row_key>.<column>`
creates a **registration-order dependency**: the cross-referenced catalog
must be registered first. The engine handles this two ways:

- **Lazy resolution** at execution time (default). Cross-references resolve
  on each invocation; missing catalog raises clean error.
- **Eager validation** opt-in via `[catalog].validate_cross_refs_at_load = true`.
  Engine checks every `@catalog.X` reference at activation; fails fast if
  the target isn't registered yet.

Most cosmos catalogs are intra-catalog; cross-references are rare. Default
lazy resolution is the right call for v1.

## 9. Worked examples — the three catalogs

See `srmech/amsc/attested/cmb_low_ell_maps/descriptor.toml`,
`cmb_polarisation_spectra/descriptor.toml`, `cmb_bispectrum/descriptor.toml`
for the four chains landed under this Phase 1.

| Catalog | Chain | Class composition | Purpose |
|---|---|---|---|
| `cmb_low_ell_maps` | `multipole_vector_axis` | L + L + D + A | de Oliveira-Costa 2004 axis extraction at ℓ=2 |
| `cmb_low_ell_maps` | `t_vs_e_axis_differential` | L + L + L + I | §VII.6.3.1 falsifiable Δθ_TE prediction |
| `cmb_polarisation_spectra` | `acoustic_peak_locations` | C + D + E | TT/TE/EE peak enumeration |
| `cmb_bispectrum` | `f_NL_template_combination` | E + N + A | f_NL local + equilateral + orthogonal combined-constraint |

Per chain the steps name canonical operations on existing class modules —
no new primitive class invented. Class L gains four ops in Phase 2
(`spherical_harmonic_decompose`, `extract_preferred_axis`, `signed_laplacian_eigvals`,
`eigendecompose` for complex Hermitian) — all extensions of existing-class scope.

## 10. The spike — closed-form TDSE evolution

**Calculation:** `srmech.qm.single_particle.tdse_evolve(H, ψ, t)` solves
`iℏ ∂_t ψ = H ψ` in closed form via `ψ(t) = V · diag(exp(-iλt)) · V^H · ψ(0)`
where `(λ, V) = eigh(H)`. Sakurai *Modern QM* §2.1.5 eq 2.1.40.

**The attempt as a chain (notional — § class identifier means "where does
this op live?" is unresolved):**

```toml
[[catalog.operator_chain]]
name = "tdse_evolve"
summary = "Closed-form TDSE evolution ψ(t) = U(t)·ψ(0) (Sakurai §2.1.5 eq 2.1.40)"
returns = "ndarray  # ψ(t) complex (n,)"

# Step 0: Hermitian eigendecompose — Class L
[[catalog.operator_chain.steps]]
class = "L"
op = "hermitian_eigendecompose"
args = { H = "@input.H" }

# Step 1: change-of-basis ψ → eigenbasis — ??? matvec-complex
[[catalog.operator_chain.steps]]
class = "?"
op = "matrix_vector_complex"
args = { U_dag = "@step[0].V_conj_T", psi = "@input.psi" }

# Step 2: elementwise complex exponential — ??? transcendental-array
[[catalog.operator_chain.steps]]
class = "?"
op = "complex_exp_diag"
args = { eigvals = "@step[0].eigvals", t = "@input.t" }

# Step 3: elementwise product — ??? elementwise-complex
[[catalog.operator_chain.steps]]
class = "?"
op = "elementwise_multiply_complex"
args = { phase = "@step[2].output", psi_eig = "@step[1].output" }

# Step 4: change-of-basis ψ_eig → original — ??? matvec-complex
[[catalog.operator_chain.steps]]
class = "?"
op = "matrix_vector_complex"
args = { U = "@step[0].V", psi_eig = "@step[3].output" }
```

**Where it doesn't fit:**

1. **Step 1, 3, 4 — matrix-vector and elementwise multiplication** over
   complex-valued dense arrays. None of A–N currently has an op for
   "general complex matrix-vector multiply" or "elementwise multiply two
   complex arrays". Class L is graph-Laplacian-scoped (real-symmetric
   adjacency, Jacobi eigvals for real symmetric); it does NOT have a
   "matvec for arbitrary complex matrix" op.

2. **Step 2 — complex elementwise exponential** `exp(-i λ t)`. This is
   transcendental on complex arguments. No class A–N has a "transcendental
   over arrays" op. (Class K's pin_slot uses `cos/sin` on scalars — not
   array-vectorised; Class L's Jacobi uses real `c/s` — not complex.)

**Two candidate refinements:**

**Refinement A — broaden Class L scope.** Add ops to Class L for general
dense-matrix linear-algebra over complex Hermitian inputs:
- `hermitian_eigendecompose(H) -> (eigvals, V)` (today's `jacobi_eigvals`
  plus eigenvectors; complex Hermitian variant)
- `dense_matvec_complex(M, v) -> M@v`
- `elementwise_multiply_complex(a, b)` (or rename to a generic
  `elementwise_op` taking an op-name argument)
- `elementwise_transcendental(arr, op_name)` where `op_name ∈ {"exp", "cos", "sin", "..."}`

These extend Class L's surface but don't introduce a new primitive class.
Class L's current ops (`dense_adjacency` / `dense_laplacian` /
`normalized_laplacian` / `jacobi_eigvals`) are graph-Laplacian-shaped.
Hermitian QM operators are NOT graph Laplacians in general — they're
arbitrary complex Hermitian matrices. **Is the broader Class L still
"the graph-Laplacian class"?** Or does it become "the dense-matrix linear-algebra
class"?

**Refinement B — Class P "elementwise transcendentals over arrays".** Per
`[[feedback_no_privileged_primitive_classes]]` the bias is to dissolve into
existing classes before promoting. Class L is the natural home for
matvec/eigendecompose; elementwise transcendentals over arrays might be
a Class L sub-op or might be a structural-irreducibility-requiring new class.

Verdict to surface at conductor's table: **Refinement A is the safer call**
for Phase 2. Class L's identity is "dense-matrix algebra including
eigendecomposition"; graph-Laplacian-specific ops (`dense_laplacian`,
`normalized_laplacian`) become specialisations of the general dense-matrix
scope, not the class's defining content. The Phase C1 + Phase B audits
named Class L "graph Laplacian" but the underlying mathematical content
is already pi-free Jacobi-style eigendecomposition — eigendecomposition
is the operation. Broadening from real-symmetric to complex-Hermitian
and adding matvec+elementwise transcendental extends the class's reach
without violating its identity. **No new primitive class needed.**

**Phase 2 design implication:** the operator-chain composition engine
must support array-typed @step references (the current eigvecs/eigvals
output of `hermitian_eigendecompose` is a complex `numpy.ndarray`, not a
scalar). The reference DSL handles this fine (arbitrary object types),
but the validator + tool-schema generator need shape-awareness for
array-typed steps. **One concrete Phase 2 follow-up item.**

This is exactly the spike value: tdse_evolve dissolved into an existing
class with an extended scope rather than promoting a new class — the
dissolve-before-promote discipline at work.

## 11. Open questions for Phase 2

1. **Branching / conditional chains.** A real consumer chain (e.g.
   "if SMICA available use SMICA, else fall back to NILC") needs runtime
   conditionality. v1 punts to "two chains + a Class D dispatch step at
   the boundary". Does this hold up under real Phase 2 cosmos analysis
   workloads? If not, an extension keyword like
   `[[catalog.operator_chain.guard]]` may be the v2 addition.

2. **Class L scope clarification.** Per §10's spike, Class L's primary
   identity becomes "dense-matrix linear-algebra (eigendecompose + matvec +
   elementwise)" with graph-Laplacian-specific operations as one
   specialisation. Decision wanted: rename the class identity or formalise
   the broadening in Class L docstring + JPL audit.

3. **Iteration steps.** Newton iteration on Kepler's equation
   (`kepler_solve`, Class K) is iterative; it currently encapsulates
   the loop internally. A chain step that REQUIRES iteration (e.g. a
   self-consistent solve where chain steps iterate until a tolerance
   condition) doesn't fit. Three options: (a) encapsulate inside a single
   class op (today's approach), (b) Phase 2 schema extension with
   `iterate_until` / `max_iter` step modifiers, (c) compose-of-chains
   pattern. Decision wanted.

4. **Cross-source reduction.** A statistic that joins data from
   `cmb_low_ell_maps` + `cmb_polarisation_spectra` + `cmb_lensing`
   (e.g. "joint χ² across observables for cosmological parameter fit")
   needs multi-source binding. The `@catalog.<key>` reference handles
   one cross-source row; what about iteration over multiple rows from a
   different catalog? Use `bridge.list_attested_sources()` + a separate
   Python orchestrator? Phase 2 reduction-step pattern?

5. **Auto-derived tool-schema parameter types.** `@input.<name>` references
   need a type annotation to generate a tool-schema parameter. Today the
   chain says `args = { input = "@input.fits_bytes" }` — the tool-schema
   has no way to know `fits_bytes` is `bytes`. Phase 2 likely adds an
   `[[catalog.operator_chain.inputs]]` table declaring runtime-input
   types:
   ```toml
   [[catalog.operator_chain]]
   name = "multipole_vector_axis"
   ...
   [catalog.operator_chain.inputs]
   fits_bytes = { type = "bytes", required = true,
                  description = "FITS file content (HEALPix sky map; Nside per @row.healpix_nside)" }
   ```

6. **Versioned op evolution.** What happens when Class L's
   `spherical_harmonic_decompose` op changes signature in Phase 3 (e.g.
   adds a `mask` argument)? Catalogs pinning `chain_schema_version = 1`
   should keep working. The class-op contract needs versioning — likely
   captured by `srmech` package version pinning at the consumer side, not
   schema-level. Cross-check Phase 2.

7. **Plugin acceleration boundary.** ADR-0002 §4 says plugins register
   accelerated implementations of class ops via `[profile.native.optimizes]`.
   Phase 2 needs to verify: a chain that references `step[0].V` (an
   eigvec matrix) gets the SAME bytes from the reference path and the
   plugin path (modulo float tolerance). The byte-parity test discipline
   applies — Phase 5 in ADR-0002 §6.

## 12. Discipline references

- `[[feedback_no_mvp_framing]]` — schema covers the full surface needed
  by the four cosmos chains + the tdse_evolve spike; no "MVP carve-out".
- `[[feedback_no_lineage_claims_in_notebook]]` — schema-v1-candidate
  framing; not endorsed final until Phase 2 implementation validation.
- `[[feedback_no_privileged_primitive_classes]]` — TDSE spike dissolves
  into Class L scope expansion; no new primitive class promoted.
- `[[feedback_no_binding_layer_carveout]]` — every class op a chain
  references is expected to land its C surface eventually; chain spec
  agnostic to host language.
- `[[feedback_rc_stacking_versioning]]` — this Phase 1 ship is rc4 of
  the active 0.4.1 cosmos catalog sprint; clean 0.4.1 ships when sprint
  concludes.
- `[[feedback_science_is_ssot_not_project]]` — chains cite canonical
  literature (de Oliveira-Costa 2004; Sakurai §2.1.5; Planck 2018 V)
  rather than internal project framings.
- `[[feedback_ndjson_over_bloated_json]]` — schema artefacts in this
  Phase land as TOML (descriptor-shaped data) per the established
  cosmos catalog precedent.
- `[[user_stance_kepler_shape_universal]]` — chains expressing
  Kepler-shape calculations (precession-fit, equation-of-centre) live
  cleanly within Class K's existing scope; the spike concern is
  iteration-step semantics not class scope.
- ADR-0002 — parent decision; this document is its Phase 1 formalisation.
- ADR-0001 — profile pattern; this schema extends the descriptor TOML
  surface without altering profile-loader machinery.

## 13. Status note

This is **schema v1 candidate**, not v1 final. The four worked-example
chains landed in this Phase 1 exercise the schema across three catalogs;
the tdse_evolve spike surfaces a Class L scope question that Phase 2
implementation work will resolve. Open questions 11.1–11.7 are not
blockers for Phase 2 to start; they're "decide when the case arises"
items. Phase 2 (composition engine implementation) and Phase 3
(auto-derived tool-schema) will exercise the schema in earnest;
revisions land as cumulative rcs on the active sprint per
`[[feedback_rc_stacking_versioning]]`.

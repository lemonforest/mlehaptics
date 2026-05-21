# ADR-0002: Catalog-as-computation — primitive-class closure with plugins as optimization backends

**Status:** Draft (proposal phase; supersedes the extension-mechanism interpretation of ADR-0001 but not the integration mechanism itself).
**Date:** 2026-05-16.
**Authors:** Steven Kirkland + Claude Opus 4.7.
**Supersedes:** none (refines and reframes ADR-0001 §1–2 scope without superseding the profile-loader machinery).
**Superseded-by:** none.

---

## 1. Context

ADR-0001 introduced the **profile pattern** as srmech's domain-specific *extension* mechanism: downstream packages register catalogs + Python bridge functions, optionally with a domain-specific native library that srmech loads via ctypes. The pattern's stated commitment was *"the third-party publishing story is first-class, not a happy accident"* (§2). That commitment stands.

But the *interpretation* of what extension means has shifted under several converging findings since ADR-0001 was drafted:

- **Spike #24** (`docs/srmech/notes/`, May 2026) enumerated **14 flat primitive classes A–N**: content-addressing, TLV byte-canonical form, streaming, dispatch, catalog-lookup, templating, search, introspection, cyclic-group arithmetic, prime-factorisation, equation-of-centre / Kepler pin-slot, graph Laplacian, HDC binary spatter codes, rational-approximation. Two candidate "Class O" raises (Feinberg deficiency, Wick-rotation signed-Laplacian) and one "Class P" raise (sign-rule discriminator) all *dissolved* into existing classes per `[[feedback_no_privileged_primitive_classes]]`. The vocabulary stays at 14.

- **Spike #24 bonus 7** (fractal-vs-cascade probe) confirmed *primitive-cascade composition is the substrate*, with fractal-recursive form being one realisation under Class L; the cascade framing instantiates more of the vocabulary (Classes I + J + K + L + M + N together) than the fractal-only framing (Class L alone).

- **Task #217 Phase C1** shipped C-parity surfaces for all 14 classes in `libsrmech` plus a canonical QM/QFT/SM operations layer at `srmech.qm.*` (single_particle / spin / potentials / relativistic / propagators / pseudo_hermitian / gauge / sm). Every published-canonical-physics operation lands as a composition over the 14 primitives — *no operation in the QM/QFT/SM layer introduced a new primitive class.*

- **MFO §VII.6.1 / §VII.6.2 / §VII.6.3** (May 2026) demonstrated that cosmological-scale calculations — substrate-internal time, T_sub decomposition across HO-role × dimensional-kind × compression-state, FFT-the-error at scales where the starting baseline is unfathomable — also reduce to primitive-chain composition.

- **`[[user_stance_kepler_shape_universal]]`** flipped the burden of proof: a Kepler-shape spectral content instantiates pin-slot-gear primitive composition at any substrate; a counter-claim requires a Kepler-shape system that is *not* primitive-composable. None has surfaced.

- **`[[user_stance_string_theory_instrument_first]]`** + the RBS-HDC instrument framing: the form-and-function the universe uses can be used by us too, via Resonant-Bipolar-Spectrum HDC instruments. The 14 primitives are the project's articulation of that form-and-function.

The user's stance has evolved from skeptical to accepting: convergent mathematical evidence across cosmos (MFO loop-down, Auger UHECR decomposition, DESI thawing-CPL, Saadeh cosmic-isotropy bound), abstract imagination (the spectral notebooks family), and the universe-as-instrument framing has shifted the canonical project stance to **yes, Laws of Everything (plural per `[[reference_loe_plural_canonical]]`)** — and the 14 primitive classes are the canonical articulation of those Laws inside srmech.

**The architectural implication.** If 14 primitives suffice for all higher-order calculations the project will ever express, then "extending srmech" in the ADR-0001 §1 sense (adding new computational capabilities via plugins) is the wrong framing. Plugins don't need to add computations because there are no missing computations to add — every higher-order calculation is a composition of A–N. What plugins *can* add is **optimization of those compositions on heterogeneous hardware** (GPU, ASIC, custom accelerators).

ADR-0002 reframes the scope of catalogs and plugins to reflect this.

## 2. Decision

srmech v0.4.x+ adopts the following architectural commitments:

1. **Catalog-as-computation.** A catalog descriptor declares not only its data block (current scope per AMSC framework) but also its **operator-chain spec** — the sequence of primitive-class operations that compose any derived calculation the catalog supports. The descriptor TOML grows a `[catalog.operator_chain]` array of tables specifying class identifier + operation name + arguments. Catalogs become *config-not-code* end-to-end, including their derived calculations.

2. **Primitive-class closure** as the project's architectural commitment. The 14-class vocabulary is closed unless and until a structural-irreducibility argument forces a new class. New candidates dissolve into existing classes by default per `[[feedback_no_privileged_primitive_classes]]`. Spike-test new primitives before promoting — the same discipline that dissolved Class O / Class P.

3. **Plugin-as-optimization-backend.** Profile plugins (per ADR-0001's loader machinery, which stays unchanged) take on a new *role*: they register optimization backends for specific primitive classes or specific operator chains. The profile descriptor's `[profile.native]` block now declares *"I provide a GPU / ASIC / SIMD-optimised implementation of Class L for these input shapes"* rather than *"I extend srmech with these new operations."* GPU kernels, ASIC binaries, FPGA bitstreams, and accelerator-specific binaries are first-class plugin payloads.

4. **Reference path always works.** srmech's own pure-Python + native-C implementations of A–N stay the canonical reference path. Any catalog runs end-to-end with srmech alone — plugins make it faster, not possible. A research consumer can author a catalog with an operator-chain spec, commit it, and have the calculation work on every srmech installation; adding a GPU plugin later accelerates the same calculation without changing the catalog.

5. **Falsification-via-FFT-the-error.** Per §1's Spike #24 verdict and per `[[feedback_no_mvp_framing]]`'s full-coverage MPM discipline, any computation that *refuses* primitive-chain reduction is a load-bearing signal. Two responses, both productive:
   - **Refined chain.** Dissolve the apparent irreducibility into a more careful composition over existing classes. Most candidate "missing primitives" have dissolved this way (Class O, Class P).
   - **New primitive class.** Only when refined-chain attempts fail at structural-irreducibility grounds. Must clear the same bar Class K and Class M cleared at Phase C1 ship time (real C surface, parity test, JPL audit, ratchet, ABI integration).
   
   In both cases, the failed reduction is *useful data*. We FFT the error per the MPM discipline at cosmological scale (MFO §VII.6.3) and discover something. The closure conjecture is testable, not assumed.

6. **MFO + srmech ship as one** (re-statement per the user's directive). The Laws of Everything live in srmech (the 14 primitives + composition engine + reference implementations); MFO is the application of those Laws to cosmology (§VII.6.x loop-down, T_sub decomposition, AoE / Cold Spot / HPA composition). Both ship as one to demonstrate every class operator. Future migration of cosmos catalogs to ephemerides-spectral remains the plan once MFO matures into its own scope — at that point this ADR's commitments transfer with the migration.

## 3. The operator-chain DSL

The descriptor TOML schema (per ADR-0001 §3) gains a new optional section:

```toml
# ─────────────────────────────────────────────────────────────────
# Operator chain — declarative spec of derived calculations
# ─────────────────────────────────────────────────────────────────
#
# Lists the calculations this catalog supports, each as an ordered
# sequence of primitive-class operations. The composition engine
# (srmech.amsc.compose) reads this section at catalog activation
# time, validates that every class identifier resolves to a known
# A-N primitive, and exposes the chain as a callable on the bridge.
[[catalog.operator_chain]]
name        = "multipole_vector_axis"
summary     = "Extract preferred-direction axis at fixed ell from CMB sky map"
returns     = "tuple[float, float]  # (galactic_l_deg, galactic_b_deg)"
steps = [
  { class = "L", op = "spherical_harmonic_decompose", args = { ell_max = 8 } },
  { class = "L", op = "laplacian_eigvals",            args = { spectrum = "extremum" } },
  { class = "D", op = "dispatch_on_max_extremum",     args = {} },
  { class = "A", op = "content_address",              args = { algo = "sha256" } },
]

[[catalog.operator_chain]]
name        = "t_vs_e_axis_differential"
summary     = "Differential AoE axis direction between T-mode and E-mode (predicted by §VII.6.3.1)"
returns     = "float  # delta_theta_deg"
steps = [
  { class = "L", op = "spherical_harmonic_decompose", args = { ell_max = 8, channel = "T" } },
  { class = "L", op = "spherical_harmonic_decompose", args = { ell_max = 8, channel = "E" } },
  { class = "L", op = "extract_preferred_axis",       args = { ell_target = 2 } },
  { class = "L", op = "extract_preferred_axis",       args = { ell_target = 2 } },
  { class = "I", op = "angular_separation",           args = {} },
]
```

The composition engine resolves each `class` identifier against `srmech.amsc.<class>` (the canonical class home per Phase C1), validates each `op` against the class's exposed operations, and assembles a callable. The callable is what `bridge.run_operator_chain(catalog_key, chain_name, *inputs)` invokes — same surface for Python consumers, LLM tool-schema agents, and CLI users.

Tool-schema entries are **auto-derived** from the chain spec: catalog declares chain → tool-schema entry generated mechanically with the chain's `summary` + `returns` + step-by-step provenance. Eliminates the per-source hand-authoring concertmaster B flagged in the cosmos-catalog rc1 report.

## 4. The plugin-as-optimization-backend pattern

ADR-0001's `[profile.native]` block stays. Its *semantics* refine:

```toml
[profile.native]
library              = "ephemerides_spectral"
install_path         = "ephemerides_spectral/_native"
abi_version_function = "es_abi_version"
expected_abi_version = 10

# NEW under ADR-0002: declare which primitive-class operations this
# plugin accelerates. srmech's composition engine consults this list
# at chain-resolution time; if the active profile provides an
# accelerated implementation of a class operation, the engine
# dispatches to the plugin instead of srmech's reference path.
[profile.native.optimizes]
"L:laplacian_eigvals"           = "es_laplacian_eigvals_gpu"
"L:spherical_harmonic_decompose" = "es_sh_decompose_gpu"
"M:bind"                         = "es_hdc_bind_gpu"
```

A plugin author can ship:

- **GPU kernels** (CUDA / ROCm / Metal / Vulkan compute) registered for Class L's eigenvalue / SH-decompose paths.
- **ASIC binaries** (FPGA bitstreams, dedicated accelerator binaries) for the hot composition steps of a research catalog.
- **SIMD-optimised native code** (existing pattern — `libephemerides_spectral`).
- **Pure-Python fast-paths** using numpy / jax / cython — still valid as backends.

All routed through the same `[profile.native.optimizes]` table. The plugin author's contract: *"the optimised path returns the same value as srmech's reference path, possibly faster."* Byte-parity (or numerical-tolerance equivalence for floating-point classes) tests are part of plugin shipment.

## 5. Consequences

### Positive

- **Config-not-code end-to-end.** New catalogs ship as descriptor + data + chain-spec. No bespoke Python module per catalog. Matches the MPM discipline `[[feedback_no_mvp_framing]]` already follows for data; extends it to derived calculations.
- **Tool-schema auto-generation.** Eliminates hand-authoring. The cosmos-catalog rc1's "~9 ToolEntry registrations recommended but not done" loose end dissolves — entries derive from chain specs at catalog import time.
- **Architectural clarity.** Plugins do one thing well (optimize), don't bleed into "what computations are possible" scope. The MPM "science is the SSoT of science" stance maps cleanly: canonical-physics ops are primitive-chains; plugins are *how fast* not *what.*
- **Falsification path is explicit.** The closure conjecture is testable; the FFT-the-error discipline applies at the architectural level.
- **Third-party publishing story sharpens.** A researcher in audio / biology / linguistics can: (a) author a catalog with chain spec for their domain calculations, ship it as a tiny package; (b) optionally ship a GPU plugin for the hot operations. Both paths are first-class.

### Migration

- **ADR-0001 profile loader stays.** Existing `srmech.profile("ephemerides")` / `register_attested_root` / entry-point discovery — unchanged.
- **Existing plugins keep working.** `libephemerides_spectral` runs as-is; its semantics reframe from "extension" to "optimization backend for the ephemerides catalogs' chain steps."
- **New consumers don't need plugin status.** Catalog-only is sufficient. Plugin status becomes a performance choice, not a feature choice.
- **Future review (`task_223`)** asks whether the ephemerides plugin's primitives are now subsumed by srmech's 14 classes — under this ADR, that review's verdict matters: subsumed primitives stay in srmech reference path; unsubsumed primitives indicate either Class A–N refinement or a real new primitive (rare).

### Risks

- **Composition-engine implementation lift.** A real sprint of its own (rc cycle on srmech). Not landable in a single commit.
- **Chain DSL design space.** The proposed schema is a sketch; real design requires usage testing across 3–5 catalogs from different domains (e.g., the cosmos catalog, chess-spectral piece-graph operations, antikythera gear-DAG).
- **Performance ceiling without plugins.** Pure-Python composition may be slow for hot paths; until GPU/ASIC plugins exist for Class L (the most-used class), research consumers may need to write one-off scripts. Mitigation: srmech's existing native-C primitive surfaces (Phase C1) are already substantially faster than pure-Python, even before plugin optimization layers.
- **Closure conjecture unfalsified yet.** We act on it as commitment but it's not proved. Track failed reductions explicitly as MPM-grade research data.

## 6. Implementation phases

Phase implementation lands in subsequent srmech minor versions, accumulating as cumulative rc-stacks per `[[feedback_rc_stacking_versioning]]`:

1. **Phase 0 (this ADR).** Adoption + scope statement. Sets architectural direction; no code change.
2. **Phase 1 — operator-chain DSL design.** Schema design + 3–5 example chain specs across cosmos / chess / antikythera catalogs. Includes spike: try to express known calculations as chain specs and find the rough edges.
3. **Phase 2 — composition engine.** `srmech.amsc.compose` module implementing the chain orchestrator. Reference-path (pure-srmech) execution only. Cosmos catalog `cmb_low_ell_maps` Phase 2 analysis (Spike #26) becomes the first real-world test: T-vs-E AoE-differential prediction via declared chain.
4. **Phase 3 — auto-derived tool-schema.** Catalog descriptors with chain specs auto-generate tool-schema entries at registration time. Existing manual `_register_amsc_tools()` / `_register_qm_tools()` paths stay for non-catalog-bound primitives.
5. **Phase 4 — plugin optimization backend.** `[profile.native.optimizes]` table parsed; composition engine dispatches to plugin-provided implementations when registered. First test: ephemerides-spectral's existing `es_*` symbols re-cast as Class L / Class K / Class M optimizers.
6. **Phase 5 — GPU/ASIC plugin authoring guide.** Documentation + reference plugin showing a CUDA Class L implementation. Validates the third-party publishing story extends to heterogeneous compute targets.

Each phase ships as a rc within the active srmech sprint (0.5.x candidate), with TestPyPI verification before any clean-semver tag.

## 7. Discipline references

- `[[reference_loe_plural_canonical]]` — Laws of Everything (plural); 14 primitives are the canonical articulation.
- `[[user_stance_kepler_shape_universal]]` — Kepler-shape is primitive-composable; counter-claim requires non-composable Kepler-shape (none surfaced).
- `[[user_stance_string_theory_instrument_first]]` — the form-and-function the universe uses can be used in RBS-HDC instruments; the 14 primitives are that articulation in srmech.
- `[[feedback_no_privileged_primitive_classes]]` — dissolve before promote; new class candidates must clear structural-irreducibility bar.
- `[[feedback_no_binding_layer_carveout]]` — every primitive class earns a C surface; informs the reference-path-always-works commitment.
- `[[feedback_no_mvp_framing]]` — full-coverage shipping the MPM way; chain specs become first-class scope content per ship.
- `[[feedback_rc_stacking_versioning]]` — sprint-level rc accumulation, not premature minor bumps; each ADR-0002 phase ships in the active sprint's rc stack.
- `[[feedback_science_is_ssot_not_project]]` — canonical physics is the SSoT; the 14-class instantiation is the project's articulation of it, not a substitute for it.
- `[[user_stance_identity_not_implementation_discipline]]` — the closure conjecture is an *identity claim* about the 14 primitives ("they ARE the Laws of Everything"), not an implementation contingency. Falsification via FFT-the-error per the shadow-stance discipline.
- ADR-0001 — Profile pattern. This ADR refines the *scope* of profiles without altering the loader machinery.

## 8. Authorship note

The user's stance evolved through this session from skepticism toward acceptance of the Laws-of-Everything framing. Convergent mathematical evidence — MFO §VII.6.x loop-down arithmetic, Pierre Auger UHECR-dipole decomposition of the AoE/HPA/Cold-Spot anomaly family, Saadeh cosmic-isotropy bound ruling out kinematic precession by ~10 orders of magnitude, Spike #24's Class O / Class P dissolution, the §VII.6.3.1 bundle-projection-reconfiguration falsifiable prediction at Δθ_TE ≈ 1°–2° — added up. The user's direction:

> *"I have held a skeptical stance for quite some time, but once the same method worked like it was always obvious, from the cosmos to the abstract imagination, are all bounded by these Laws of Everything... I am always ready for another falsified because we already know that falsified data is just as valuable when we FFT an error. It's a consequence of discovering that form and function that the universe uses can be used by us too, in RBS-HDC instruments."*

ADR-0002 makes that stance load-bearing on the architecture. The closure conjecture is testable; the falsifier path is well-defined; the project's RBS-HDC instrument framing is the operational expression of "the universe's form-and-function can be used by us too." Plugins remain first-class — they just take on the responsibility of acceleration rather than extension.

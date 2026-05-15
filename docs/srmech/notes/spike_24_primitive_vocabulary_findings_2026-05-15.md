# Spike #24 findings — primitive vocabulary inventory + residual analysis

**Status:** Phase 1 landed; Phase 2-5 pending.
**Branch:** `research/spike-24-primitive-vocabulary-2026-05-15`.
**Spec:** [`spike_24_primitive_vocabulary_2026-05-15.md`](spike_24_primitive_vocabulary_2026-05-15.md).

## Phase 1 — Abstraction-layer-only inventory (2026-05-15)

Mechanical-first walk of the srmech python package + C library at HEAD (`fba3065` post PR #416). Identifies each module, function, dataclass that constitutes a *primitive transformation* at the srmech abstraction layer.

Organized by **primitive class** (what algebraic transformation the primitive performs), not by file. Each class lists its srmech-native instances with file references.

### Class A — Content-addressing / fingerprinting

Primitives that map content to fixed-width identifier via cryptographic hash.

- **SHA-256 hashing** — `sha256_bytes(data: bytes) -> str` ([`amsc/format.py:367`](../../srmech/python/srmech/amsc/format.py)) and native `sha256_hex_c` ([`amsc/_native.py:210`](../../srmech/python/srmech/amsc/_native.py), backed by C `srmech_sha256_hex`). Pure function bytes → 64-hex-char hash. Same primitive in both Python and C.
- **Descriptor canonical hash** — `descriptor_hash(path: Path) -> str` ([`amsc/descriptor.py:314`](../../srmech/python/srmech/amsc/descriptor.py)). Re-emits TOML with sorted keys, then SHA-256 over the canonical bytes. Composes Class A with canonical-serialisation.
- **File SHA-256** — `_file_sha256(path)` ([`amsc/catalog.py:450`](../../srmech/python/srmech/amsc/catalog.py)). Path → SHA-256 hash of file content. Same Class A primitive, file-applied.

**Algebraic shape (integer-cyclic):** SHA-256 is composition of XOR + ADD-mod-2³² + ROL on 256-bit accumulators. **CPU analog: exact** — SHA-256 is literally specified in terms of CPU primitives. **No leakage:** the bronze does not have a direct Class A primitive (no hash analog in gear-mesh algebra); content-addressing is a srmech-side / digital-substrate-side primitive without a 1:1 bronze counterpart. Flagged for Table 2B (bronze-standalone, *absent*).

### Class B — Tagged-tuple / labeled-data records

Primitives that pack typed fields into a single addressable unit with a schema-defined shape.

- **MPR record** — `MPRRecord` ([`amsc/format.py:102`](../../srmech/python/srmech/amsc/format.py)). Frozen dataclass with `mpr_version`, `data`, `data_schema_id`, `attestation`, `rendering` fields. The on-disk crystallisation of attested-data per the MPR v1 format.
- **Attestation block** — sub-mapping within MPR record. Schema-defined fields: `source_doi`, `source_url`, `license`, `retrieved_at`, `response_sha256`, `parser_version`, `parser_rule_hash`, `collector_descriptor_path`, `collector_descriptor_hash`. Composed from Class A (response_sha256, parser_rule_hash, descriptor_hash) + scalar metadata.
- **Descriptor** — `Descriptor` ([`amsc/descriptor.py:113`](../../srmech/python/srmech/amsc/descriptor.py)). Frozen dataclass from TOML-parsed `[source]`, `[fetch]`, `[parse]`, `[schema]`, `[rendering]`, `[attestation]`, `[gap_targeting]` sections.
- **Profile** — `Profile` ([`profile_loader.py`](../../srmech/python/srmech/profile_loader.py)). Frozen-ish record carrying `name`, `version`, `schema_version`, `description`, `tool_schema_attestation_path`, `tools` mapping.
- **ToolEntry / ToolSchema** — ([`amsc/tool_schema.py:129,171`](../../srmech/python/srmech/amsc/tool_schema.py)). Tagged-tuple for a profile's exposed tool surface, with `ToolParameter` and `ToolReturn` sub-tuples.

**Algebraic shape:** a tagged-tuple is `(label, value)` pairs at fixed memory offsets. **CPU analog: exact** — STRUCT layout with offset-load (`MOV r, [base+offset]`). **No leakage** for the CPU mapping. **Bronze analog (Table 2B):** the bronze's gear-DAG `Gear` records (in plug-in `gear_database.py`) carry tagged-tuple structure (tooth_count, fragment, mesh_edges) — same Class B primitive instantiated in different substrate. Bronze does NOT have srmech's *attestation* sub-record (no provenance metadata in bronze); that's srmech-side specific.

### Class C — Iterator / streaming primitives

Primitives that produce a sequence of values from an input source, one-at-a-time.

- **NDJSON read** — `read_ndjson(path) -> Iterator[MPRRecord]` ([`amsc/format.py:252`](../../srmech/python/srmech/amsc/format.py)) and native `ndjson_lines_c` ([`amsc/_native.py:261`](../../srmech/python/srmech/amsc/_native.py), backed by C `srmech_ndjson_iter`). Streams one MPR record per line.
- **NDJSON write** — `write_ndjson(path, records, ...)` ([`amsc/format.py:299`](../../srmech/python/srmech/amsc/format.py)). Inverse: iterator of MPR records → NDJSON file with deterministic ordering by `data` natural key (declared per-source in descriptor).
- **Adapter fetch** — `AdapterProtocol.fetch(descriptor) -> Iterator[bytes]` ([`amsc/adapters/_base.py:38`](../../srmech/python/srmech/amsc/adapters/_base.py)). Streams raw bytes from upstream source.
- **Adapter parse** — `AdapterProtocol.parse(raw, descriptor) -> Iterator[dict]` ([`amsc/adapters/_base.py`](../../srmech/python/srmech/amsc/adapters/_base.py)). Streams parsed rows.
- **Adapter run** — `run(descriptor) -> Iterator[MPRRecord]` ([`amsc/adapters/_base.py:183`](../../srmech/python/srmech/amsc/adapters/_base.py)). Composes fetch + parse + attest → iterator of MPR records.
- **Catalog record iteration** — `_iter_records_for_descriptor(descriptor)` ([`amsc/catalog.py:473`](../../srmech/python/srmech/amsc/catalog.py)). Local-kernel-aware streaming for a given source.

**Algebraic shape:** iterator is `next()` repeated until `StopIteration`; under the hood a loop with state-machine. **CPU analog: exact** — `LOOP / LOAD / BRANCH-IF-DONE` is the elementary iteration pattern. **Bronze analog (Table 2B):** the *crank-turn* is the bronze's iteration primitive — each turn advances the gear-train's state by one step. The bronze instantiates Class C natively, but with one critical bronze-side property: **the iteration is bidirectional** (crank can turn either way; per F11 the bronze is in the bidirectionally-coupled regime). CPU iterators are generally forward-only by convention (though `reversed()` exists, the underlying memory access doesn't preserve the algebraic invertibility the bronze has at every step). *Leak:* the CPU mapping elides the bronze's bidirectional symmetry.

### Class D — Late-binding / plugin primitives

Primitives that defer "which implementation runs" until runtime, allowing extension by external modules.

- **Profile loader** — `list_profiles()`, `profile(name) -> Profile` ([`profile_loader.py`](../../srmech/python/srmech/profile_loader.py)). Discovers profiles via Python entry-points; Form 1 (package-only `srmech_profile.toml`), Form 2 (path/str attribute), Form 3 (callable returning a Path). Late-bound profile instantiation at first access; cached thereafter.
- **Adapter registration** — `register(adapter_name, module)` ([`amsc/adapters/_base.py:65`](../../srmech/python/srmech/amsc/adapters/_base.py)). Adapter dispatch via name. Built-ins: `html_scraper`, `json_api`, `csv_bulk`, `netcdf_grid`, `geotiff_bbox`, `literature_curated`.
- **Tool schema registration** — `register_tool(entry)`, `register_profile_tools(profile, attestation_path)` ([`amsc/tool_schema.py:213,233`](../../srmech/python/srmech/amsc/tool_schema.py)). Registers a profile's `ToolEntry`s into the global `ToolSchema` registry.
- **Tool schema extension** — `load_extension_file(profile_name, path)` ([`amsc/tool_schema.py:324`](../../srmech/python/srmech/amsc/tool_schema.py)). Lets a profile add tools via a separate TOML file, loaded at profile activation.
- **Classifier / probe registration** — `register_classifier(module)`, `register_probes(module)` ([`amsc/gap_suggester.py:97,130`](../../srmech/python/srmech/amsc/gap_suggester.py)). Plugin's classification / probe functions registered for gap analysis.

**Algebraic shape:** late-binding is function-pointer / vtable dispatch. **CPU analog: exact** — `CALL via indirect address` (a register holds the function pointer). **Bronze analog (Table 2B):** the bronze has a late-binding analog in the operator's choice of *which crank position* to start from + which calendar-anchor pin to insert — Voulgaris 2024's setting-mode interpretation (§11.6.15 of the antikythera notebook). The bronze's late-binding is *operator-mediated*, not internal; the CPU's late-binding is internal-state-mediated. *Leak:* the CPU mapping elides the operator-as-active-participant role the bronze requires.

### Class E — Catalog / naming primitives

Primitives that map a name (key) to an attested artifact (descriptor + ndjson_path + adapter).

- **Catalog source registration** — `register_attested_root(root_path, ...)` ([`amsc/catalog.py:109`](../../srmech/python/srmech/amsc/catalog.py)). Registers a directory containing attested catalogs at the srmech level.
- **Catalog source listing** — `list_attested_sources()` ([`amsc/catalog.py:653`](../../srmech/python/srmech/amsc/catalog.py)). Iterates registered descriptors, returns rendered metadata per source.
- **Catalog dataset retrieval** — `get_attested_dataset(source_key, limit=, offset=)` ([`amsc/catalog.py:714`](../../srmech/python/srmech/amsc/catalog.py)). Source-key → paginated MPR records.
- **Local-kernel overrides** — `use_local_kernel(path)`, `clear_local_kernel()`, `get_local_kernel_state()` ([`amsc/catalog.py:299,389,395`](../../srmech/python/srmech/amsc/catalog.py)). User-side substitution of an alternative ndjson root for a registered source.
- **Live query** — `_get_attested_dataset_live(...)` ([`amsc/catalog.py:821`](../../srmech/python/srmech/amsc/catalog.py)). Triggers the adapter to fetch fresh data instead of reading the committed mirror; produces a fresh attestation block.

**Algebraic shape:** hash-table or sorted-map lookup. **CPU analog: exact** — `HASH + LOAD-INDIRECT` is the standard catalog pattern. **Bronze analog (Table 2B):** the bronze's catalog is the *dial / pointer / scale registry* — each dial maps a class of celestial observation (lunar phase, planetary longitude, eclipse glyph) to its bronze-side instantiation (specific gear-train + pointer geometry). The bronze instantiates Class E natively for celestial-observation-class → mechanism-instance. *Leak:* CPU catalogs are usually one-shot lookups; the bronze's catalog is *continuously-active* (every crank turn updates all dials simultaneously). The CPU notion of "catalog" elides the bronze's parallel-update property.

### Class F — Substitution / templating primitives

Primitives that produce a string by substituting named placeholders from a context.

- **Template render** — `render_template(template, context)` ([`amsc/descriptor.py:269`](../../srmech/python/srmech/amsc/descriptor.py)). `{key:fmt}` substitution for the descriptor's `cite_as_template` and `purpose_template` fields. Tight scope (no Jinja).

**Algebraic shape:** regex match + lookup + concatenate. **CPU analog: exact** but with multiple-instruction composition (not a single CPU primitive — it's MOV + COMPARE + LOAD-FROM-MAP + STORE in a loop). **Bronze analog (Table 2B):** *absent*. The bronze does not have a templating analog — every gear / dial / pointer is statically inscribed at fabrication time. The bronze's analog of "templating" would be operator-pen-and-ink writing on a paper next to the device. *Genuinely srmech-side / digital-substrate-side specific.*

### Class G — Discovery / search primitives

Primitives that look for what's missing rather than what's present.

- **Gap suggestion** — `suggest_gap_collections(classifier, probes)` ([`amsc/gap_suggester.py:181`](../../srmech/python/srmech/amsc/gap_suggester.py)). Given a classifier + probe set, computes which (regime, collection) combinations are not yet attested. The "schema-gap-driven collector trigger" primitive.
- **Gap classification** — `_classify_gap(...)` ([`amsc/gap_suggester.py:316`](../../srmech/python/srmech/amsc/gap_suggester.py)). Compares discovered regimes against expected regimes per the registered classifier; identifies misses.
- **Descriptor discovery** — `discover_descriptors(...)` ([`amsc/descriptor.py:345`](../../srmech/python/srmech/amsc/descriptor.py)). Walks the attested root for TOML descriptors. Class G + Class C composition.

**Algebraic shape:** loop + compare + accumulate-misses. **CPU analog: exact** — `LOOP + CMP + STORE_IF_NOT_EQUAL` is the elementary search pattern. **Bronze analog (Table 2B):** *partially present.* The bronze's "gap" is what it CAN'T do — Mars retrograde fully resolved per F&J 2012, evection per F15. The bronze surfaces gaps *through residual error* (F12's FFT-inverse method extracts the gap's spec from the residual signature). The bronze's gap-discovery is *passive* (the gap shows up when truth diverges from prediction); srmech's is *active* (the gap-suggester queries the classifier explicitly). *Leak:* the bronze's gap surfacing requires F12-style external analysis to be visible; srmech's is internally introspectable.

### Class H — Self-introspection primitives

Primitives that report on the system itself rather than on external content.

- **Version** — `__version__` ([`srmech/version.py`](../../srmech/python/srmech/version.py)), `srmech_version()` ([`c/include/srmech.h:108`](../../srmech/c/include/srmech.h)). Package identifier as semver string.
- **ABI version** — `srmech_abi_version()` ([`c/include/srmech.h:109`](../../srmech/c/include/srmech.h)). C-binary ABI version integer; matched by `EXPECTED_ABI_VERSION` in `_native.py`.
- **Tool schema view** — `tool_schema_view()` ([`amsc/tool_schema.py:289`](../../srmech/python/srmech/amsc/tool_schema.py)). LLM-friendly serialization of the registered tool surface.
- **Local kernel state** — `get_local_kernel_state()` ([`amsc/catalog.py:395`](../../srmech/python/srmech/amsc/catalog.py)). Reports which sources have local-kernel overrides active.
- **Registered roots list** — `list_registered_roots()` ([`amsc/catalog.py:168`](../../srmech/python/srmech/amsc/catalog.py)). Reports all currently-registered attested roots.

**Algebraic shape:** read compile-time-constant or registry state, return as serializable. **CPU analog: exact** — `CONSTANT LOAD` or `READ REGISTRY VALUE`. **Bronze analog (Table 2B):** the bronze instantiates Class H natively as *inscribed text on the bronze itself* — the Parapegma inscriptions, the back-door instruction inscriptions, the dial markings. The bronze's self-introspection is *static* (inscribed at fabrication and unchanging); srmech's is *dynamic* (registry state can change at runtime). *Leak:* bronze self-introspection is immutable; srmech self-introspection is mutable.

## Phase 1 — what is absent at the srmech abstraction layer

The prediction in the spec held: **srmech as currently shipped is mostly provenance scaffolding primitives, not algebraic scaffolding primitives.**

What is **present** at the srmech abstraction layer:
- Class A (content-addressing / hashing)
- Class B (tagged-tuple / records)
- Class C (iteration / streaming)
- Class D (late-binding / plugins)
- Class E (catalog / naming)
- Class F (templating)
- Class G (discovery / gap-finding)
- Class H (self-introspection)

What is **absent** at the srmech abstraction layer (i.e., currently lives only in plug-ins):
- **Class I — Cyclic-group / modular-arithmetic primitives** — `gcd_many`, `lcm_many`, `is_coprime`, `roll_operator`, `gear_mesh_ratio`, `chain_ratio`, `cyclic_group_element`, `CRTTable` all live in `docs/antikythera-maths/research/cyclic_group_algebra.py` (antikythera-spectral plug-in). Substrate-agnostic algebra; promotion candidate.
- **Class J — Prime-factorization / period-relation primitives** — `prime_factor_set`, `shared_primes_among_planetary`, `shared_prime_planet_pairs`, `shared_prime_planet_triples` live in antikythera-spectral plug-in's `astronomical_cycles.py` + `gear_topology.py`. Substrate-agnostic; promotion candidate (with renaming to drop "planetary" prefix).
- **Class K — Equation-of-centre / pin-slot algebra** — `pin_slot_output_angle`, `pin_slot_jacobian`, `equation_of_centre_unreduced`, `equation_of_centre_series`, `equation_of_centre_n_armed_cross` live in antikythera-spectral's `pin_and_slot.py` + `bronze_planetary_encoder.py`. The Kepler-equation algebra. **Per `[[user_stance_kepler_shape_universal]]`, this is the most important promotion candidate** — Kepler-shape is universal, so the primitive ought to live at the abstraction layer.
- **Class L — Graph-Laplacian eigenbasis primitives** — gear-DAG Laplacian construction, eigendecomposition, Fiedler partition — these live in plug-ins (chess-spectral, ephemerides-spectral's `gateway_graph_laplacian.py`, antikythera-spectral's gear_topology.py). Substrate-agnostic primitive class; multiple plug-ins implement it independently.
- **Class M — HDC (hyperdimensional computing) encoding primitives** — channel basis, bind, bundle, permute, similarity — live in plug-in encoders (antikythera-spectral's `encode_ant.py`; presumably chess-spectral analog). Substrate-agnostic.
- **Class N — Rational-approximation / Diophantine primitives** — continued-fraction convergents, Stern-Brocot tree, best-`p/q` finders — live in antikythera-spectral's `rational_approximation.py` + `pareto_analysis.py`. Substrate-agnostic.

The **size of the absent set is striking**: six full primitive classes (I, J, K, L, M, N) are mathematically substrate-agnostic but currently live only in plug-ins. The "extends" cells in Phase 2's matrix will surface this concretely.

### Phase 1 closing observation

srmech currently is the **provenance scaffolding** (Classes A-H). The **algebraic scaffolding** (Classes I-N) exists across the spectral collection but is *duplicated and unowned at the abstraction layer*. Phase 2's per-plug-in instantiation matrix will:

1. Audit which abstraction-layer primitives (A-H) each plug-in uses.
2. Audit which plug-in-specific primitives (I-N) appear in multiple plug-ins (those are the strongest promotion candidates).
3. Output the bronze→CPU and bronze-standalone tables, populated for the classes that have bronze instances (which is most of B, C, D, E, G, H plus the future-promoted I, J, K).

The Phase 1 finding alone validates the spec's prediction. Phase 2 will quantify it.

## Phase 2 — Per-plug-in instantiation matrix (pending)

[To be filled in next.]

## Phase 3 — Ephemerides residual analysis (pending)

[To be filled in after Phase 2.]

## Phase 4 — Ephemerides handoff packet (pending)

[To be filled in after Phase 3.]

## Phase 5 — srmech_research_notebook.md landing (pending)

[To be filled in after the analysis converges.]

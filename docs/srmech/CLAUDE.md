# `docs/srmech/` — Claude Code session brief

You have been opened into the **srmech** subdirectory of the
`mlehaptics` monorepo. The repo's top-level `CLAUDE.md` is about an
EMDR bilateral-stimulation firmware project (ESP32-C6, Phase 7
pattern playback) — **that's not what you're working on here**.

This subtree is part of a **spectral-research portfolio** of
several Python research packages sharing one mathematical-
provenance discipline. Read this whole file before doing anything
beyond a single-file read.

---

## What srmech IS

**srmech** is short for **Stored-Relationship Mechanism**. It is:

- A Python research package, published as **`srmech`** on PyPI.
  Last graduated release: **`v0.7.4`** (production PyPI). The
  **current dev head is `v0.7.5rc135`** (a long carrier-arc rc run
  on TestPyPI); the most recent rc is the **"carrier
  consolidation"** ship (see the dedicated section below — it
  collapses the numpy-removal duplication debt and removes the
  overdue bus shims; the version-jump decision is the user's, to be
  made before the next live-PyPI cut, so it rides the `0.7.5rcN`
  line for now). Earlier
  graduations — `v0.7.3` / `v0.7.1` / `v0.7.0` (the One `S(σ,θ)` +
  the numpy-optional cascade graduation), `v0.5.0` (bus / DSL /
  MCP / so(8)+triality voxel arc), `v0.4.0` (14-class C-parity
  vocabulary + QM/QFT/SM), `v0.2.0`, `v0.1.0` — remain in PyPI
  history. **numpy is no longer a dependency**: every continuous-math
  op is a cascade of the 14 primitives over the numpy-free
  `Mat` / `Vec` / `HV` carriers (the rc69–rc134 carrier-removal arc;
  see the numpy section below). This top "What srmech IS" narrative is
  kept current under user direction — **this file is NOT hygiene-gated**,
  so update it freely whenever srmech's surface moves.
- The home of the **Attested Multi-Source Collector/Catalog
  (AMSC) framework** — every ground-proof datum carries a mandatory
  attestation block (`source_doi`, `source_url`, `license`,
  `retrieved_at`, `response_sha256`, `parser_version`,
  `parser_rule_hash`, `collector_descriptor_path`,
  `collector_descriptor_hash`). This is the on-disk crystallisation
  of the **Mathematical Provenance Method** (MPM).
- A **native-C-accelerated** Python package shipping the full
  **14-class Spike #24 primitive vocabulary** (Task #201 Phase B
  baseline: Classes A + C — SHA-256 + NDJSON; Task #217 Phase C1
  rc1-rc8: Classes B, D, E, F, G, H, I, J, K, L, M, N). Each class
  has both a native C surface (`libsrmech.{so,dll,dylib}`) and a
  Python wrapper (`srmech.amsc.<class>`); pure-Python fallback for
  Pyodide / WASM environments.
- The **canonical QM/QFT/SM operations layer** at `srmech.physics.qm.*`
  (moved there from `srmech.qm.*` by the ADR-0010 physics slice,
  v0.9.0rc381; the old `srmech.qm.*` path was REMOVED in v0.9.0rc382 —
  a clean break, no alias, per the no-legacy-path discipline — so
  `import srmech.qm` now raises `ModuleNotFoundError`; use
  `srmech.physics.qm.*`)
  (Task #217 Phase C1 rc9-rc11) — single_particle (TDSE/TISE/Heisenberg
  /commutator/density-matrix/Liouville-vN), spin (Pauli + Cl(0,3)),
  potentials (hydrogen radial + harmonic oscillator), relativistic
  (Dirac γ-matrices + Weyl + charge conjugation + Klein-Gordon),
  propagators (Feynman scalar/fermion/photon/massive-vector),
  pseudo_hermitian (η-deformed inner product framework — closes
  chess-spectral ADR-005), gauge (SU(2)/SU(3) Gell-Mann + Casimirs
  + Wilson loops), sm (Higgs + W/Z + Weinberg + Yukawa + CKM). Each
  operation cites canonical physics literature per
  `[[feedback_science_is_ssot_not_project]]`.
- **Tool-schema introspection** at `srmech.amsc.tool_schema` —
  ~87 ToolEntry registrations covering every public callable in
  `srmech.amsc.*` and `srmech.physics.qm.*` with canonical-SSoT-cited
  summaries (Task #217 Phase C1 rc12 / Tasks #219 + #220).
- The dependency surface that downstream spectral-research
  packages (`ephemerides-spectral` today; more later) register
  their catalog SSOTs with via `srmech.amsc.catalog.register_attested_root()`.

**What shipped since v0.4.0 — the v0.5.0 and v0.6.0 arcs:**

> ⚠️ **Paths in this release narrative are AS-SHIPPED-THEN, not as-importable-now.**
> The `qm` subpackage moved to `srmech.physics.qm.*` (ADR-0010, v0.9.0rc381) and
> the old `srmech.qm.*` spelling was REMOVED at v0.9.0rc382 — `import srmech.qm`
> raises `ModuleNotFoundError` today. Five entries below named the dead path with
> nothing marking it dead, and they read as live API; rc406 (`#T1074`) gives each
> one its current spelling inline. Measured cost of leaving it: a session read
> line 86 and repeated `srmech.qm.so8.an_embedding` into a technical answer as a
> live path. This file is loaded as orientation every session and is explicitly
> NOT hygiene-gated, so a stale path here PROPAGATES rather than sitting inert.

- **v0.5.0 (graduated to production PyPI)** — the rc9–rc22 voxel
  arc, srmech recognising its own shape voxel-by-voxel. It adds:
  the **`srmech.bus`** cross-process IPC bus + **Bus-class API**
  (Bio-TOTP wire cipher, Claim 255); the **`srmech.dsl`**
  operator-chain runner that loads the cascade-catalog TOML
  descriptors; the **`srmech-mcp`** Model Context Protocol server
  adapter (for Claude Code) and the **`srmech-agent`** Anthropic
  SDK adapter; the **profile-plugin loader**; a top-level
  **`srmech.native_status()`**; **`an_embedding`** — shipped as
  `srmech.qm.so8.an_embedding`, now **`srmech.physics.qm.so8.an_embedding`**
  (14 = 8 + 3 + 3̄ su(3) branching of g₂ = Der(𝕆)); the full
  **28 = 𝔰𝔬(8) chiral read-out** (then `srmech.qm.so8` / `srmech.qm.triality`,
  now **`srmech.physics.qm.so8`** adjoint +
  **`srmech.physics.qm.triality`** order-3 outer automorphism); and
  **`srmech mcp emit-mcpb`** (emits a Claude Desktop `.mcpb`
  bundle from introspection).
- **v0.6.0 (rc1–rc14 to date; rc14 dev head)** — the lean-ISA arc.
  It adds: the **`cascade.atoms` / `cascade.compose`** two-tier
  lean-ISA split (#751); **`quaternion_subalgebra_stabilizer`** — shipped as
  `srmech.qm.so8.*`, now **`srmech.physics.qm.so8.quaternion_subalgebra_stabilizer`**
  — so(4) = su(2) ⊕ su(2) (#759); **`lean_isa_seventh_primitive`** — shipped as
  `srmech.qm.triality.*`, now
  **`srmech.physics.qm.triality.lean_isa_seventh_primitive`** —
  order-3 triality 7th primitive (#761); `sha256_bytes` docs
  (#738); a **reentrant C core** (#772 — thread-local scratch; note the
  caveat reconciled in rc306 below); the Klein-4 four-sector
  **`cascade.parallel_sector_dispatch`** Python surface (#778) +
  its C peer **`srmech_cascade_parallel_sector_dispatch`** (#771),
  plus the parallel-dispatch slowdown fix; the native Kuramoto
  forward-Euler step **`srmech_cascade_kuramoto_step_f64`** +
  **`cascade.kuramoto_step`** (rc9); the rc10 release-prep
  doc-hygiene sweep; and (rc11) the DSL **`parallel` discriminator**
  (`chain.parallel_sectors` / `parallel_body=`) that slots the
  `parallel_sector_dispatch` 1→N fan-out into the chain contract as a
  first-class special form alongside loop/fold/reduce, with a cascade-op
  **`[cascade].kind`** classification (`stage` vs `combinator`) +
  guided "use the `parallel` discriminator, not `op=`" errors;
  and (rc12) makes the four-sector dispatch **chainable / nestable** —
  a `combine=` recombine (`bundle`/`mean`/`sector0`/`concat`) folds the
  ≤4 sectors into one value (`result["combined"]`) so a sector-dispatched
  cascade is `stream → stream` and the 4-way splay carries THROUGH a
  chained cascade (the rc11 stage was a leaf that crashed when chained);
  `sectorize()` wraps a body for nesting; the DSL `parallel_sectors`
  recombines by default; plus a stale top-help fix (all four
  `status`/`bus`/`dsl`/`mcp` subcommands enumerated); and (rc13) the
  **`klein4_*` HDC ops get a `sectors=`/`parallel=`/`mode=` flag** —
  `mode="chunk"` (default, data-parallel + bit-identical) / `mode=
  "chirality"` (F233 4-sector via klein4's own XOR sector-flips);
  default-on at ≥4 cores; value-preserving; pure-Python (co-equal
  parity — no C-callback; standalone-C sector dispatch is the tracked
  follow-up); and (rc14) the **generalised Kuramoto-Sakaguchi step** —
  `kuramoto_step(…, adjacency=, alpha=, pin_anchor=, pin_strength=)`
  (n×n coupling matrix; non-symmetric → directed; Sakaguchi α frustration;
  per-oscillator pinning) shipped **CO-EQUAL** in Python AND a new
  standalone-C symbol `srmech_cascade_kuramoto_step_general_f64`
  (additive → ABI stays 3; JPL-clean; no Python callback), differential-
  tested. Defaults reproduce the plain step byte-for-byte.

**What shipped after v0.6.0 — the v0.7.x graduations + the numpy-zero carrier arc:**

- **v0.7.0 → v0.7.4 (all graduated to production PyPI)** — the
  octonion / Cayley–Dickson + "the One" `S(σ,θ)` arc, the
  C-transpile of the transcendental cascade, the Hamming/GF(2)
  Rosetta pair, the Schur-complement / Dirichlet-to-Neumann Class-L
  op, `sedenion_register`, and the **numpy→optional capstone**
  (`v0.7.0rc47`): numpy left `install_requires`. Every continuous-math
  op became a cascade of the 14 primitives; `libsrmech` carries no
  `libm`.
- **v0.7.5 (long rc run rc1 → rc134, TestPyPI; current dev head)** —
  the **carrier-removal arc (#564)**. numpy went from *optional* to
  *gone*: a numpy-free **`Mat`** (2-D, `srmech/amsc/mat.py`) + **`Vec`**
  (1-D, `srmech/amsc/vec.py`) + **`HV`** carrier replaced every
  ndarray, with the native dense kernels fed **zero-copy** from the
  `array('d')` interleaved-complex buffers. A down-only
  **`CEIL_NUMPY_CARRIER`** ratchet drove top-level `import numpy`
  to **0**, and the rc129–rc133 "carrier-spirit lockdown" made the
  carriers numpy-idiom-faithful (`m[0]→Vec`, `·`/`@`, slicing,
  elementwise arithmetic, `.conj` as Class-K). rc134 = genome
  several-genes-per-chromosome (`tlv_unpack` + `chromosome(genes=)`).
  See `[[project_carrier_ratchet_to_zero_15rc_roadmap]]` +
  `[[feedback_numpy_removal_must_preserve_carrier_format_mat_vec_not_lists]]`.

### "carrier consolidation" — ships on the `0.7.5rcN` line (rc135)

The carrier-removal arc, done one-rc-per-module, **left a duplication
debt**: it was meant to be *numpy-spirited* (one dtype-transparent
carrier op per operation), but each flip *added* a kernel. The
`srmech.math.laplacian` Class-L surface ended up with the same op in
two-to-four forms. The consolidation hard-removes the redundancy down
to one dtype-polymorphic `mat_*` op each (user 2026-06-13: "we messed
up big time with numpy-removal inflation … fix this pollution"; **hard
removals**, breaking is fine). **Version note:** this is the user's
call to make before the next live-PyPI cut, so the consolidation rides
the `0.7.5rcN` line as **rc135** — do NOT mint a `0.7.6`/`0.8.0` bump
yourself. The full plan also lives in
`[[project_srmech_carrier_consolidation_remove_numpy_removal_duplication]]`.

**Remove 11 redundant ops** (dtype-split `_real`/`_complex` + the
superseded loose-input `dense_*` generation):
`dense_matvec_complex`, `dense_matmul_complex`, `dense_dot_complex`,
`dense_matmul_real`, `dense_matvec_real`, `dense_dot_real`,
`dense_norm`, `dense_outer_complex`, `dense_outer_real`,
`mat_dot_real`, `mat_dot_complex`.

**Keep / add 3 dtype-poly `mat_*` ops** (the canonical carrier surface):
`mat_matmul` (exists, dtype-poly, native-dispatched), `mat_norm`
(exists), `mat_solve`/`mat_lstsq`/`mat_eigvals`/`mat_svd`/
`mat_hermitian_eigendecompose` (exist) — **plus new** `mat_dot`
(unify the 4 dot forms), `mat_matvec` (column-`Mat` over `mat_matmul`),
`mat_outer`. Net public-callable delta: **−11 + 3 = −8**.

VERIFY-FIRST (user requirement): `dense_matmul_complex`/`dense_matvec_complex`
are already thin coercion-shims that ride `mat_matmul`; `dense_*_real`
wrap their `_complex` twins; `mat_dot_real`/`mat_norm` use
`_iter_mat_scalars`. So the unified ops are value-identical — prove it
with a real+complex equivalence check before deleting.

Consumers to repoint (NOT external — internal + tests only):
`mat.py` `__matmul__`/`__rmatmul__` (→ `mat_matmul`/`mat_matvec`),
`vec.py` `__matmul__`/`__rmatmul__` (→ `mat_matvec`/`mat_dot`),
`hdc.py` 3 sites (`mat_dot_real` → `mat_dot`). `_flatten_scalars`
STAYS (elementwise ops use it). Each removal also touches: laplacian
`__all__` (×2: the top list + `LAPLACIAN_OPS`), the `ToolEntry` in
`tool_schema.py`, the `rosetta_classification.ndjson` ledger, the
**#928 down-only Rosetta ratchet**, the `describe()["tools"]["total"]`
count in the duplicated count-tests, and `_native.py`.

⚠️ **This line said "the FIVE duplicated count-tests" until rc362 — that was stale
and it mis-scoped a build brief.** Measured **at rc414, predicate stated**:
`git grep -c "== <total>"` over `tests/` only → **73 lines across 66 test
files**, PLUS `EXPECTED_N` in `tests/test_op_name_set_witness_rc361.py`, which
that predicate cannot match (it is a bare assignment, not a comparison) and
which also needs the manifest rewritten and its sha256 re-pinned in the same
commit. The rc362 figure written here was "61 sites across ~54 files" with no
predicate given — and an unstated predicate is why a re-measurement cannot be
reproduced. "Five" was true around rc135 and
the surface has grown by an order of magnitude since. Do not brief a count-bumping
change as a five-file edit. Re-measure before quoting a number here — this file is
explicitly NOT hygiene-gated, so nothing else will catch it going stale again.
**C/Python 1:1 parity (user directive):** `srmech_dense_matmul_complex`
stays — it still backs `mat_matmul`; but the now-orphaned
`srmech_dense_matvec_complex` kernel is **removed** from the C surface
to keep it 1:1 with Python (matvec is now a composition over
`mat_matmul`, so the dedicated C kernel has no caller). Removed from
`c/include/srmech.h` (prototype + doc), `c/src/srmech_laplacian.c`
(definition + ADR-0002-Phase-2 doc bullet), and the `_native.py`
ctypes binding. Additive/subtractive of a dead symbol does **not**
bump ABI (stays 3; the ctypes shim binds via `hasattr`).

**Also overdue (directive "check other aliases left over"):** the v0.5.0
bus deprecation shims still present at v0.7.5 — HARD-REMOVE
`srmech/bus/_chain.py` ("removed in v0.5.0 final") and the `seed=`
kwarg in `bus/_client.py` + `_server.py` (the `seed→dna` rename;
updates `test_bus_aio.py`).

The package directory layout:

```
docs/srmech/
├── CLAUDE.md                          ← you are here
├── CMakeLists.txt                     ← top-level CMake driver
├── srmech_research_notebook.md        ← canonical notebook
├── notes/                             ← research scratchpads, NDJSON outputs
├── hoodoos/                           ← protein-fold PDB fixtures used by some spikes
├── c/                                 ← native C library
│   ├── include/srmech.h               ← public API: srmech_sha256_hex,
│   │                                    srmech_ndjson_iter, srmech_version,
│   │                                    srmech_abi_version
│   ├── src/srmech_sha256.c            ← FIPS 180-4 SHA-256, JPL-clean
│   ├── src/srmech_ndjson.c            ← streaming NDJSON reader, JPL-clean
│   ├── src/srmech_meta.c              ← version + ABI accessors
│   ├── src/srmech_parallel.c          ← Klein-4 four-sector dispatch (v0.6.0)
│   ├── src/srmech_kuramoto.c          ← native Kuramoto forward-Euler step (v0.6.0)
│   ├── test/                          ← C-side smoke tests
│   ├── Makefile                       ← local build flow
│   ├── README.md
│   └── JPL_AUDIT.md                   ← Power-of-Ten rule-by-rule audit
└── python/
    ├── pyproject.toml                 ← scikit-build-core (primary)
    ├── pyproject-pure.toml            ← hatchling (Pyodide fallback)
    ├── README.md                      ← PyPI long-description
    ├── CHANGELOG.md                   ← per-rc changelog
    ├── srmech/
    │   ├── __init__.py
    │   ├── version.py                 ← SSOT for __version__
    │   ├── amsc/                      ← the AMSC framework
    │   │   ├── format.py              ← MPRRecord, read_ndjson, sha256_bytes
    │   │   ├── descriptor.py          ← TOML descriptor loader, descriptor_hash
    │   │   ├── catalog.py             ← register_attested_root, bridge surfaces
    │   │   ├── _native.py             ← ctypes shim; HAS_NATIVE / sha256_hex_c / ndjson_lines_c
    │   │   ├── gap_suggester.py
    │   │   └── adapters/              ← html / json / csv / netcdf / geotiff / literature_curated
    │   ├── cascade/                    ← ADR-0010's FIRST new top-level namespace (rc364)
    │   │   └── catalogs/               ← the built-in descriptor catalogs, moved out of amsc/_research/
    │   │       ├── class_catalog/      ←  4 [class] TOML descriptors, loaded by srmech.dsl.make_class
    │   │       ├── cascade_catalog/    ← 21 [cascade] TOML descriptors, loaded by srmech.dsl
    │   │       ├── alias_catalog/      ←  2 alias descriptors ([[alias]] + [genome.type_aliases]); NEW rc364
    │   │       └── worked_instances/   ←  1 worked-instance descriptor
    │   └── _native/                   ← (wheel install only) libsrmech.so/.dll/.dylib
    └── tests/                         ← pytest suite
```

The **`srmech.dsl`** operator-chain runner loads the cascade
descriptors under `srmech/cascade/catalogs/cascade_catalog/`.

⚠️ **This line said "10 TOML descriptors" until rc363 — measured on the
rc363 branch: 20.** The 10 named below are the v0.6.0-era set (the 8
lean-ISA atoms/composites `chiral_flip`, `pin_slot_at_zero`, `magnitude`,
`reorient`, `net_chirality`, `cyclic_gcd`, `best_rational_signed`,
`chiral_dual`, plus `parallel_sector_dispatch` and `kuramoto_step`); the
catalog has since doubled. Re-count before quoting a number here — this
file is explicitly NOT hygiene-gated, which is exactly how the sibling
"five duplicated count-tests" line reached a 12× under-scope (ADR-0012
§1.1). ~~**And nothing else can catch it**: ADR-0012 §3.4 (clause C6)
measures that the 20 cascade descriptors have ZERO `describe()`
visibility — `json.dumps(describe())` contains `"cascade_catalog"` 0
times — so this prose sentence is currently the tree's only statement of
how many there are.~~ **SUPERSEDED at rc420 (`#T1114`)**: C6's
cascade_catalog front is CLOSED — `describe()["cascade_catalog"]` now
counts the catalog live (`total` / `executable` / `leaf` + a
per-descriptor status map; 20 = 17 executable + 3 explicit leaves at
rc420), every descriptor declares an executable ADR-0008 chain or an
explicit leaf (`tests/test_cascade_catalog_executable_rc420.py`, no
third state), and `srmech.dsl.run_cascade_chain` runs a declared chain.
This prose is no longer the only statement of how many there are — the
live count is the SSoT and this sentence defers to it. The `[class]`
catalog next door was always counted
(`describe()["classes"]["toml_total"] == 4`); the asymmetry C6 named is
gone on this front (the `[[alias]]` layer's axis is still open).

**Discipline — PREFER config-driven `[class]` TOML over hand-coded
domain classes** (`[[feedback_prefer_config_driven_toml_classes]]`,
user direction 2026-06-13). When a domain object is a
cascade-of-the-14 composition (state + cascade-op-chain methods),
declare it as a `[class]` TOML descriptor consumed by
`srmech.dsl.make_class` / `register_class_dir` (descriptors live
under `srmech/cascade/catalogs/class_catalog/`; the seeds are
`genome.toml` + `hurwitz.toml`). The `Mat`/`Vec`/`HV` carriers,
`srmech.bus`, the `adapters/`, and the `srmech.physics.qm.*` physics
op-families STAY hand-coded Python. **Conversion follows the genome
two-layer pattern** — ship each method as a flat cascade op, then
bind it in the TOML; the `make_class` contract is one-op-per-method
+ a single `appends`/`sets` field, so dict/multi-field-state classes
(e.g. `SedenionRegister`) need a contract extension first, while
immutable accessor-shaped classes (e.g. `One`) are cleaner first
targets. Prove every conversion with a DSL-class-vs-Python
equivalence test.

---

## What srmech IS NOT

**srmech is not a CAD-grade fabrication tool.** It produces
**provenance metadata** about scientific datasets — DOI, retrieval
timestamp, response SHA-256, parser version, descriptor hash. It
does not model physical geometry, mesh contact, axle wobble,
fabrication tolerances, or any of that machinery.

The sister package `docs/antikythera-maths/CLAUDE.md` documents an
explicit **CAD-grade scope ban** for its own subtree (modelling at
the *algebra / eigenbasis* level, projecting to spatial motion,
NOT modelling at the CAD level). **The same ban applies in
srmech**: if a request reads as "model the physical bronze mesh
geometry" or "compute axle wobble" or "fabrication-tolerance
geometry" — push back. CAD-grade fabrication geometry is not
srmech's domain.

**The deeper line (2026-07-23):** "no CAD / GPU" is the *symptom*; the
real line is a **direction of derivation** — FAVOR carrier-native /
metric-field-native ops (the CD / H-genome carrier's own
distributional ⊗ relational ⊗ resonant triality, closed-form on the
ALU); DISFAVOR spacetime-shadow / continuum-projected math (it needs a
GPU *because* the continuum shadow has no closed form). The test is
"does the op emerge FROM the carrier (bottom-up), or is it a cascade
reverse-engineered to approximate a continuous / spacetime target
(top-down)?" — not "is it GPU". See
`[[feedback_metric_field_native_not_spacetime_shadow]]` + the canonical
scope-doc `docs/antikythera-maths/CLAUDE.md`.

**The C native surface, by contrast, intentionally covers every
primitive class srmech exposes** — full C/Python parity is the
architectural commitment per Task #201 and the ephemerides-spectral
precedent that markets microcontroller-readiness on PyPI. As of
2026-05-15, Task #201 Phase B shipped C implementations of
**Class A (content-addressing via SHA-256)** and **Class C
(streaming iterator via NDJSON line tokenisation)**; **Task #217
Phase C1 added Class I (cyclic-group / modular arithmetic) in
v0.4.0rc1, Class L (graph Laplacian; pi-free dense + Jacobi
eigvals, n ≤ 256 native bound) in v0.4.0rc2, Class J (prime-
factorisation / period; trial-division primality + factorisation +
multiplicative order) in v0.4.0rc3, Classes B (TLV byte-canonical
form) + G (byte-pattern search) + H (self-introspection,
acknowledgment of existing srmech_version / srmech_abi_version) in
v0.4.0rc4 as a lightweight-trio bundle, and Classes D (dispatch
multi-needle pattern match) + E (catalog sorted-key lookup) + F
(template `{key}` substitution) in v0.4.0rc5 — each with a real C
primitive surface in `srmech_dispatch.c` / `srmech_catalog.c` /
`srmech_template.c`, parity-tested against Python fallbacks**; the
remaining classes K/M/N ship in subsequent rc additions under
0.4.0rcN per `[[feedback_rc_stacking_versioning]]`, with the clean
`0.4.0` ship at Phase C1 close.

**Class O is NOT a separate class** (resolution 2026-05-16) — the
signed-metric / Wick-rotation operation located by Spike #24
bonus 8 and narrowed by bonus 9 was **dissolved into Class L
as a signed-Laplacian-variant sub-operation** per
`[[feedback_no_privileged_primitive_classes]]`. **The signed-Laplacian
op SHIPPED** — `signed_laplacian` at `srmech/math/laplacian.py:3279`
(real symmetric PSD, Class-K magnitude degree; Kunegis et al. SDM 2010),
with `magnetic_laplacian` at `:3458` as the Hermitian directed / chiral
peer (per-edge `charges=` mode; Lieb & Loss, *Duke Math. J.* **71**
(1993) 337–363, arXiv:cond-mat/9209031; Reff, *LAA* **436** (2012)
3165–3176, arXiv:1110.4554). This passage previously read "future
Class L rcs will add the signed-Laplacian op" and was stale per
`[[feedback_claude_md_orientation_can_lag_notebook_ssot]]` — corrected
2026-07-25. Vocabulary stays at 14 classes A–N.

Each class follows the same ratchet — parity test + JPL Power-of-Ten
audit + cibuildwheel matrix update + TestPyPI rc verification per
`[[feedback_always_rc_first_for_downstream_publishes]]`.

**Hard dependencies (current — numpy is GONE):**

- v0.3.x and earlier: stdlib only (plus `tomli` on Python 3.10).
- **v0.4.0rc2 → v0.7.0rc46**: numpy was a hard dependency (Class L /
  Class M array math). *(historical)*
- **v0.7.0rc47**: numpy moved to an optional `[scientific]` extra.
- **v0.7.5 carrier arc (rc69 → rc134)**: numpy was **removed entirely**.
  There is no `[scientific]` extra and no `import numpy` anywhere in
  `srmech/`. The array carriers are the numpy-free **`Mat`** / **`Vec`**
  / **`HV`** (`array('d')`, row-major, interleaved-`(re,im)` for complex
  = C99 `double _Complex`), fed **zero-copy** to the native dense
  kernels. Install pulls **no numpy**; a fresh numpy-absent venv imports
  + runs the whole package. The C native surface never depended on numpy
  or LAPACK (Jacobi eigvals in C, algebraic c/s, pi-free). **Verify every
  numpy-removal rc in a numpy-ABSENT clean venv** — never reinstall numpy
  to exercise a carrier path (`[[feedback_numpy_is_out_the_door_not_optional]]`).
  A test for a numpy-free module must itself be numpy-free
  (`[[feedback_test_for_numpy_free_module_must_itself_be_numpy_free]]`).

**The current Phase B state (Class A + Class C implemented)** is
Phase B's stopping point and Task #217's starting point. Per
`[[feedback_no_mvp_framing]]` (the MPM way of full-coverage
shipping), the architectural target is full parity for every
primitive class so that srmech runs on a microcontroller without
a host Python or external LAPACK — same target ephemerides-spectral
already markets on PyPI. Adding a class to libsrmech is expected
work per the Task #217 per-class build-out roadmap, with each
class's port following Task #201 Phase B's ratchet (parity test +
JPL Power-of-Ten audit + cibuildwheel matrix update + TestPyPI rc
verification per `[[feedback_always_rc_first_for_downstream_publishes]]`).

**Operational scope clarification — every primitive class earns a
C surface; specific scope-bounded helpers stay Python:**

*Every primitive class A–N has a C primitive operation.* Hash
algorithms, cyclic-group arithmetic, graph-Laplacian operations,
prime factorisation, dispatch (multi-needle pattern match), catalog
lookup (sorted-array binary search), template render (placeholder
substitution), HDC bind/bundle/permute/similarity, equation-of-centre
algebra, rational-approximation — each is shipped as a libsrmech
symbol exported via `srmech.amsc.<class>` Python wrapper. The
architectural commitment per `[[feedback_no_mvp_framing]]` and
`[[feedback_no_binding_layer_carveout]]` is **full C parity for every
primitive class, no exceptions**. "Binding-layer concern" is NOT a
legitimate skip-class directive — it's a recurrence vector for
soft-MVP carve-outs that this project has explicitly rejected.

*Historical Phase-B5 note — SUPERSEDED.* Phase B5 originally kept
TOML/JSON *parsing* in Python (a `tomli` round-trip) as a
**vendoring-scope** decision. That stance was **superseded by the
rc128 full-1:1 C-parity mandate**: srmech's C library now ships its
OWN malloc-free, caller-arena **`srmech_json` parser/canonical writer**
(byte-identical to `json.dumps`, the keystone for the genome
`manifest.json` mirror) and a **`srmech_toml` parser** — because a
C-only / microcontroller host genuinely needs them to read JSON
manifests and TOML descriptors with no Python present. As of the
v0.7.5rc159/rc160 standalone-honor sweep, both carry **no compiled-in
child cap** (the writer's key-sort scratch + the parsers' staging are
caller-arena-backed). So "don't vendor a parser in C" is no longer
the stance. Class F's primitive (template `{key}` substitution) ships
in C as `srmech_template_render`. Frame any future Python-side
decision as **what's the actual scope concern (vendoring? build
complexity? dependency surface?)** rather than as **skip-the-class**.

**srmech is not the EMDR firmware.** The repo root `CLAUDE.md`
describes the EMDR bilateral-stimulation device (`src/`, `test/`,
`platformio.ini`, ESP32-C6, motor PWM). That's a separate project
in the same monorepo. **Do not edit files outside this subtree or
its sister `docs/*-maths/` subtrees** unless the user explicitly
asks.

---

## Sister spectral notebooks (the family srmech belongs to)

srmech is one node in a portfolio of spectral-research Python
packages and notebooks. Each notebook applies the same MPM
discipline to a different domain object:

| Path | Notebook title | What it studies |
|------|----------------|-----------------|
| `../srmech/srmech_research_notebook.md` | **Stored-Relationship Mechanism** | The unifying framework — relationships stored in cyclic-group / spectral representations, projected back to observable behaviour. *Canonical to this directory.* |
| `../antikythera-maths/antikythera_spectral_research_notebook.md` | The Antikythera Mechanism as a Resonant HDC Object | Bronze gear-DAG, cyclic-group algebra, Almagest / Freeth parameter sets |
| `../antikythera-maths/ephemerides_spectral_research_notebook.md` | The Ephemerides Mechanism: High-Precision Resonant HDC Instrument | Sol star system — 52-body roster, geodetic / magnetic / fluid / dynamical catalogs, JPL DE441 anchor. **srmech depends on this one (it consumes AMSC).** |
| `../antikythera-maths/mfo_spectral_research_notebook.md` | MFO Spectral Research Notebook | **Metric Field Ontology** — substrate-vs-excitation framing of the spectral metric field. User's foundational ontology layer (sister to all the others). |
| `../antikythera-maths/doom_spectral_research_notebook.md` | DOOM as a Spectral Lattice System | Map encoding, level topology, gameplay-system spectral analysis |
| `../chess-maths/chess_spectral_research_notebook.md` | Chess as a Spectral Lattice Fermion System | Piece-graph spectra, D_4 / B_4 reps, irrep multiplicities — the original spectral-mechanic spike |
| `../chess-maths/chess_spectral_4d_notebook.md` | 4D Chess Spectral — v1 Validation Notebook | Higher-dimensional chess extension |
| `../logo-maths/logo_research_notebook.md` | LOGO HDC — Research Notebook | LOGO turtle graphics → cyclic-group encoder |
| `../othello-maths/othello_spectral_research_notebook.md` | Othello as a Dynamic Spectral Lattice System | Reversi piece-flip dynamics |

**Discipline shared across all of these**: algebra / eigenbasis /
cyclic-group / spectral side. **Not** CAD / fabrication /
mechanical-engineering side. See
`docs/antikythera-maths/CLAUDE.md` for the canonical scope
statement; it applies to all sister notebooks, srmech included.

---

## The Mathematical Provenance Method (MPM) — srmech's reason for being

Every ground-proof datum srmech ships carries a mandatory
attestation block. The on-disk crystallisation is the
**Mathematical Provenance Record v1** format (`MPR v1`),
implemented in `srmech.amsc.format`:

```python
{
  "mpr_version": "1.0",
  "data": { ... domain payload ... },
  "data_schema_id": "test://schema/example",
  "attestation": {
    "source_doi": "10.0/...",
    "source_url": "https://...",
    "license": "CC0",
    "retrieved_at": "2026-05-13T00:00:00Z",
    "response_sha256": "<64 hex chars>",
    "parser_version": "srmech 0.1.1rcN",
    "parser_rule_hash": "<64 hex chars>",
    "collector_descriptor_path": "...",
    "collector_descriptor_hash": "<64 hex chars>"
  },
  "rendering": { "name": "...", "purpose": "...", "cite_as": "..." }
}
```

Why this matters: the discipline catches the most common LLM-side
error mode — citation hallucination. A citation without
attestation is not real; an attestation that can't be re-verified
is broken. The whole AMSC framework is the project's defence
against citation drift. **Be paranoid about citations.** When a
user asks you to add a paper reference, prefer to extract the
actual PDF and verify authors + title + arXiv ID over trusting
training-data attribution.

---

## Build / release stack — read before touching anything publish-adjacent

### Two-pyproject pattern

- **`pyproject.toml`** — scikit-build-core backend, drives CMake,
  produces **platform wheels** (`cp3XX-cp3XX-{linux,macosx,win}_*`)
  with `srmech/_native/lib*.{so,dll,dylib}` inside.
- **`pyproject-pure.toml`** — hatchling backend, produces **one
  `py3-none-any` wheel** for Pyodide / WASM environments where
  native binaries can't run. Swapped in via `mv` over
  `pyproject.toml` in the `build-pure-wheel` CI job; restored
  afterward.

Both files **MUST** carry identical `version` and `description`
fields. The publish workflow's "Verify pyproject-pure.toml version
+ description match main" step fails CI on any drift. That guard
exists because rc3-rc8 shipped with stale `"Pure Python."` in
both descriptions; the user spotted it on the TestPyPI project
page (rc9 fix). Read [CHANGELOG.md §0.1.1rc9](python/CHANGELOG.md)
for the post-mortem.

### Versioning + tag-push routing

- Version SSOT lives in **FIVE places** that must agree (bump version
  FIRST, then run the suite, or the pin passes spuriously —
  `[[feedback_srmech_version_bump_hits_five_locations_run_suite_after]]`):
  `python/pyproject.toml`, `python/pyproject-pure.toml`,
  `python/srmech/version.py`, `c/include/srmech.h`
  (`SRMECH_VERSION_PRE` / `SRMECH_VERSION`), **and** the hard-pinned
  version-string test in
  `python/tests/test_signal_processing_scaffolding.py`
  (stale name `test_version_is_0_7_0rcN`; asserts the exact current
  version). `grep -rn "X.Y.ZrcN" tests/ srmech/` at every bump.
- **rc tags are pushed MANUALLY** — `srmech-autotag.yml` only auto-tags
  strict-semver (clean) tags; an `rcN` suffix is non-strict-semver and
  is SKIPPED, so push `git tag srmech-vX.Y.ZrcN HEAD && git push origin
  <tag>` by hand. Clean `srmech-vX.Y.Z` tags auto-route to PyPI (the
  human-in-loop production gate) — do NOT hand-push those.
- **rc-suffix auto-routing** in `.github/workflows/srmech-publish.yml`:
  - Tag `srmech-vX.Y.ZrcN` (lowercase `rc`, no separator) →
    **TestPyPI** auto-publish.
  - Tag `srmech-vX.Y.Z` (no `rc` suffix) → **PyPI** auto-publish.
    Tagging without `rc` IS the human-in-loop production gate.
  - The tag-version regex: `r"srmech-v(\d+\.\d+\.\d+(?:rc\d+)?)"`.
- **User discipline (mandatory)**: TestPyPI rc-verification BEFORE
  a clean tag goes to production PyPI. The v0.2.0 ship history
  illustrates: `0.1.1rc3` → `0.1.1rc9` on TestPyPI (the rc series
  for the Task #201 build-out), then `0.2.0rc1` → `0.2.0rc2` on
  TestPyPI (final TestPyPI gate + AMSC dual-name doc fix), then
  the clean `srmech-v0.2.0` tag to production PyPI. Apply the
  same pattern to any future release.

### Tag flow for a new rc

```bash
# 1. Make changes on a feature branch
git checkout -b task-XXX-or-feat-name
# 2. Bump version in 4 SSOT files:
#    python/pyproject.toml         version = "0.1.1rcN"
#    python/pyproject-pure.toml    version = "0.1.1rcN"
#    python/srmech/version.py      __version__ = "0.1.1rcN"
#    c/include/srmech.h            SRMECH_VERSION_PRE + SRMECH_VERSION
# 3. Add CHANGELOG.md entry under [0.1.1rcN] header
# 4. PR → review → MERGE (NOT squash, see "Never squash" below)
git checkout main && git pull
# 5. Tag at the merge commit
git tag srmech-v0.1.1rcN HEAD
git push origin srmech-v0.1.1rcN
# 6. Watch the publish workflow run; verify TestPyPI install
#    in a clean venv (cd outside the repo first; namespace-package
#    shadowing will silently load the source-tree _native.py with
#    no .dll/.so attached and HAS_NATIVE=False).
```

### Native-dispatch architecture

The Python `srmech.amsc._native` module:
- Searches three locations for the shared library:
  1. Each entry in `srmech.__path__` (regular wheel install)
  2. Relative to `_native.py`'s own file (defensive)
  3. `importlib.metadata.files("srmech")` manifest (editable installs)
- Verifies `srmech_abi_version()` matches `EXPECTED_ABI_VERSION`
  at load time; mismatch → `HAS_NATIVE = False`, `LOAD_ERROR`
  populated, pure-Python fallback runs.
- Exposes `sha256_hex_c(bytes) -> str` and
  `ndjson_lines_c(path) -> list[(lineno, bytes)]`.

The dispatching wrappers live in `srmech.amsc.format`:
- `sha256_bytes(data)` → uses native if `HAS_NATIVE`, else hashlib.
- `read_ndjson(path)` → uses native if `HAS_NATIVE`, else stdlib.

Other hot callsites (`catalog._file_sha256`,
`catalog._kernel_cache_hash`, `adapters._base.parser_rule_hash`)
route through `sha256_bytes` so they pick up the native dispatch
transparently. **Do not introduce new `hashlib.sha256(...)` direct
calls** — go through `sha256_bytes` (Phase B5 discipline).

### ABI compatibility

C ABI version is currently **16** (`SRMECH_ABI_VERSION = 16` in
`c/include/srmech.h`; `EXPECTED_ABI_VERSION = 16` in
*(this line said 12 until rc420, 13 until rc425, 14 until rc438 and 15 until
rc439 — one bump behind on each occasion, the exact staleness shape the rc404
note below records; the v13 bump was rc418's, the v14 bump is rc425's
`srmech_mlse` wire-contract change, the v15 bump is rc438's
`srmech_klein4_from_one` winding triad, and the v16 bump is rc439's
`srmech_genome_centromere_of` dicentric refusal — a STATUS reinterpretation,
the v10/v12/v14 shape)*
`python/srmech/_native/__init__.py`). *(These three lines said ABI **9** and
pointed at `python/srmech/amsc/_native.py` until rc404 (`#T1069`) — two stale
facts in three lines: the version was three bumps behind, and ADR-0010 moved
the shim, so the named path had ceased to exist. This file is NOT
hygiene-gated, so nothing but a reader catches that.)* **Bump in lockstep**
whenever
the wire format of any existing exported function changes. Adding
a new symbol does NOT bump ABI (the Python shim just doesn't bind
unknown symbols) — EXCEPT that, by standing precedent, adding a new
**callback typedef** carries a CFUNCTYPE wire-format implication for
the Python ctypes shim, so each new callback typedef bumps. v1 was
Phase B3 (sha256 only); v2 added the `lineno` param to the NDJSON
callback typedef; **v3 (v0.5.0rc2)** added the `srmech_bus_*` C peer
for `srmech.bus` cross-process IPC, including the new
`srmech_bus_handler_callback_t` function-pointer typedef; **v4
(v0.9.0rc180)** added the `srmech.bus` pub/sub C peer + the
`srmech_bus_subscriber_callback_t` delivery-callback typedef; **v5
(v0.9.0rc242)** added the `srmech_progress_cb_t` dispatch-observer
callback (#840) + `srmech_set_progress_cb`; **v6 (v0.9.0rc275)**
added the §101 encode-progress + graceful-abort primitive — the
`srmech_progress_tick_cb_t` per-call/per-iteration heartbeat WITH a
nonzero-return-to-CANCEL channel + the versioned `srmech_progress_ev_t`
struct + the `SRMECH_CANCELLED` status + the two `*_progress` overload
symbols. Each of v2–v6 bumped because a new callback typedef changed
the CFUNCTYPE wire format, even though no existing function signature
changed. (Later APPEND-only growth of `srmech_progress_ev_t` via its
`struct_size` gate will NOT re-bump — that is the whole point of the
versioned struct.) **v7 (v0.9.0rc287)** and **v8 (v0.9.0rc290)** were
the first bumps driven by a symbol REMOVAL (glyph-stream tokenizer;
Klein-4 mint-by-regime) — a removal produces no other symptom than a
version mismatch, so by standing policy a removed export always bumps.
**v9 (v0.9.0rc306, task #899)** is the first bump of the ORDINARY kind —
an existing exported signature changed: `srmech_genome_section_counts`
gained `(void *ws, size_t ws_len)` caller-arena params (removing its
32 MiB static catalog arena / static count table / static window — the
~11k-section corpus cap AND the non-reentrancy), with the paired ctypes
argtypes updated in lockstep. `GENOME_FORMAT_VERSION` stays 15.
**v10 (v0.9.0rc307)** reinterpreted the `fiedler_sparse` family's
`ws_len` UNIT from a count-of-doubles to BYTES — no signature changed shape,
but the CONTRACT of an existing param did. **v11 (v0.9.0rc395, `#T1000`)**
removed `srmech_cd_zero_divisor_witness` (a removal always bumps).
**v12 (v0.9.0rc404, `#T1069`)** is the second bump of the v10 kind: no
signature changed, but `srmech_json_parse` / `srmech_toml_parse` now RETURN a
different status (the new `SRMECH_ERR_LIMIT = 8`) for a class of input that
returned `SRMECH_ERR_OVERFLOW = 4` through rc403. The status block in
`srmech.h` states outright that non-zero values "form part of the wire
contract with the Python ctypes binding", so reinterpreting one is a
wire-contract change. It is load-bearing rather than ceremonial here: rc404
also deletes the rc401 Python pre-scan that existed only because the two
conditions shared a status, and a stale rc403 `.so` reports ABI 11 — so
without the bump it would still LOAD and silently cost ~512 MiB on an
out-of-int64 literal (the answer stays correct; only the cost is wrong).
`GENOME_FORMAT_VERSION` stays 19 throughout v10–v12.

**v14 (v0.9.0rc425, `#T1112`)** is the THIRD bump of the v10 / v12 kind: no
signature changed shape, but an existing parameter's CONTRACT did.
`srmech_mlse`'s `n_states` meant `A^(L-1)` through rc424 and now means `A^L`.
The trellis state must span the whole tap window, because `y_t = Σ_k taps[k]·s_{t-k}`
reads all `L` symbols and a state-emission Viterbi cannot express an emission
that depends on a symbol outside its state. The rc424 kernel held `L-1` and
folded `taps[0]` and `taps[1]` onto the SAME symbol, so it decoded a different
channel — `[h0+h1, h2, …]` with the memory shifted a step — and returned a wrong
sequence **with no error signal**. Measured against an exhaustive
maximum-likelihood search it disagreed on **4 of 9** test channels, returning a
sequence of cost 13.0 where the transmitted one scored exactly 0.0; it agreed
only where the cursor tap dominates, which is precisely the regime in which a
plain slicer is also right, so the error hid wherever the op was not earning its
keep. Fixed in BOTH projections and differential-tested (60 random channels,
zero Python/C divergence). Load-bearing rather than ceremonial: a stale rc424
`.so` would still LOAD into rc425 Python, which now sizes its scratch arena for
`A^L` states, and the stale lib would carve `tup`/`ntup` at the old width against
that larger arena. `GENOME_FORMAT_VERSION` stays 19 — no on-disk format moves.

**v15 (v0.9.0rc438, `#T1140`, gh #1530 §G)** is the THIRD bump of the ORDINARY
kind — v9's and v13's shape, an existing exported signature changed.
`srmech_klein4_from_one` gains `(int64_t w_saros, int64_t w_metonic, int64_t
w_callippic)`: the One's metacycle winding triad, which its wire did not carry
at all. The op's contract calls its output "a DECLARED FUNCTION of the One's
constructor integers" and the winding has been a declared, pinned constructor
parameter since rc408, so the projection was dropping part of its own operand.
**Measured** over `w ∈ [-4,4]³` (729 distinct windings, σ/θ/terms fixed): the
Klein-4 coupling took **1** distinct value out of 729, as did BOTH planes of the
Q₈ coupling composed over it — against controls on the same ops that DO move
(40 θ → 40, 2 σ → 2, 20 `terms` → 20). Post-fix: **729/729** on all three, with
0 native/pure divergences over the same grid. Load-bearing rather than
ceremonial: a stale rc437 `.so` reports ABI 14 and would otherwise load into
rc438 Python, which now pushes nine args at a six-arg wire — and on the REST
path the stale lib still returns CORRECT bytes, so the defect would reappear on
wound Ones only, silently. `GENOME_FORMAT_VERSION` stays 19 — this changes the
function that produces already-stored bytes, not the storage.

**#772 reconciliation (rc306).** The "reentrant C core" claim (#772) rests
on the `SRMECH_THREAD_LOCAL` thread-local-storage scratch. `srmech_genome_section_counts`
was a genuine EXCEPTION to it: rc280 shipped that op with THREE plain
file-scope statics (not thread-local) + a static id counter, so two threads
sharing `libsrmech` would corrupt each other's scan. rc306 removes that
exception by converting the op to the caller-arena pattern (the count table
+ region window are carved from the caller `ws`, the catalog arena is its
tail) — no static scan state remains, so the op is now reentrant on disjoint
`ws` buffers. This does NOT assert the whole C surface is exhaustively
audited for reentrancy; it states precisely that the one documented
section_counts exception is closed. Any op still holding mutable file-scope
scratch remains single-thread-at-a-time until similarly converted.

### JPL Power-of-Ten audit

The C library is clean on **eight** of the 10 Holzmann Power-of-Ten
rules; **Rule 1 is PARTIAL** and Rule 9 carries one deliberate
deviation (see [c/JPL_AUDIT.md](c/JPL_AUDIT.md)).

⚠️ *This line said "passes all 10" until rc441 (`#T1148`), and the
sentence survived because nothing measured the half of Rule 1 it was
asserting: the ratchet grepped `goto|setjmp|longjmp` and never looked
for recursion, which Rule 1 also bans. The first census found **9**
recursion cycles (1 direct + 8 mutual) across 3092 functions. They are
all depth-bounded, so the library is sound — but "sound" and "passes
the rule" are different claims and only one of them was true. Two
sibling blindnesses closed in the same rc: the function scanner counted
braces inside `'{'`/`'}'` char literals, so three functions reported
`lines=1` (Rule 4 could not see them) with assert counts running away
to 458/456/35 (Rule 5 vacuous there too).*

Enforcement:

1. **`tests/test_jpl_audit.py`** — pytest ratchet, mechanically
   detects Rules 1 (no goto **and, since rc441, no new direct/indirect
   recursion — strict on novel cycles, down-only on the seeded
   population of 9**), 3 (no malloc), 4 (≤60-line functions), 5 (≥2
   asserts per non-exempt function), 8 (no multi-line macros).
   **Violations can only go DOWN**, never up. Rules 4 and 5 now scan
   literal-masked text so a brace inside a char literal cannot run the
   counter off the end of the file.
2. **`pedantic-build` CI job** (3-cell: Linux gcc / macOS clang /
   Windows MSVC) — `cmake -DSRMECH_PEDANTIC=ON` enables
   `-Werror` (POSIX) / `/WX` (MSVC). Any new warning fails CI.
   Rule 10 toolchain-side enforcement.
3. **Rule 5 exempt list** in `test_jpl_audit.py` has 8 entries
   (2 trivial accessors + 6 sha256 inline arithmetic helpers).
   Adding to it requires documenting rationale in JPL_AUDIT.md
   AND updating the test. Don't expand silently.

---

## Critical project memories (load-bearing across sessions)

These come from the user's persistent memory directory at the
repo root. They are NOT auto-loaded into this session because the
session's cwd is `docs/srmech/` not the repo root. **Internalise
them anyway** — they're load-bearing for any work in this subtree:

- **Never squash-merge PRs.** Project history depends on per-step
  commits being preserved. Use `gh pr merge --merge` (preferred)
  or `--rebase`; never `--squash`.
- **TestPyPI before PyPI, always.** Every release between now and
  v0.2.0 ships as `vX.Y.ZrcN` to TestPyPI; only clean
  (non-rc) tags route to production PyPI.
- **No MVP framing.** Don't scope ships as "minimum-viable" or
  "quick-tier subsets"; commit to full-coverage per ship version.
- **PDF-extraction citation discipline.** When citing a paper,
  extract the actual PDF and verify authors + title + arXiv ID;
  don't trust prior attributions. Several catches in the
  May 2026 spike series prove this is load-bearing.
- **NDJSON over bloated JSON for results.** New results-style
  outputs should be NDJSON (one record per line), not indented
  JSON. TOML accepted for descriptor-shaped data. (Existing
  bloated JSONs in tree are what they are; the discipline
  applies to NEW outputs.)
- **No lineage claims about external work.** Don't ship "natural
  extension of X" claims about prior researchers' work without
  explicit user direction. Cite specific results technically.
  (The user has explicitly authorised "natural extension" framing
  for *their own* intellectual arc — distinct from academic-
  lineage assertions about others.)
- **WSL smoke before AMSC pushes.** For AMSC-touching PRs, run
  `wsl bash scripts/smoke_local.sh` before push if available;
  Windows-local pytest can't catch libm last-bit divergence
  between platforms. Less critical for srmech (data-pipeline, not
  math-heavy) but watch for it on any C-touching PR.
- **Fiber as spatially-absent encoding.** The user's
  intellectual stance — a fiber over a manifold encodes
  algebraic content that is spatially absent until projected.
  Worked example: a gear's tooth count is `ℤ/n` algebra; the
  spatial dynamics only appear under external rotation. This
  framing applies across all the spectral notebooks (chess
  pieces, gear ratios, Antikythera dials, ephemerides bodies)
  and is the conceptual unifier the project hangs on.
- **Hyper as 3D-spatial-interface.** The user's two-level
  ontology refinement (May 2026): "hyper" denotes 3D-spatial-
  interface, NOT hyperdimensional-algebraic constructions.
  Spherical compression scopes to 3D-spatial-physical phenomena.
  Formalised in MFO §VII.1.1.
- **Trauma-informed defensive scope.** Security/defense-adjacent
  ships are defensive preparedness, NOT offence. Ship physics +
  textbook refs; never targeting / capability-assessment.

---

## If your task is "verify ephemerides-spectral on TestPyPI"

That's the user's stated reason for opening this session. The
ephemerides-spectral package lives at
`../antikythera-maths/ephemerides-spectral/` (sister subtree under
the same monorepo). It depends on `srmech` as a hard runtime
dependency.

Plan:

1. **Check what's on TestPyPI now.** The release index lives at
   <https://test.pypi.org/project/ephemerides-spectral/>. Find
   the most-recent rc version (the publish workflow is
   `.github/workflows/ephemerides-spectral-publish.yml` at the
   repo root).
2. **Create a fresh venv** outside the repo tree (e.g. under
   `/tmp/verify_ephemerides_spectral/`). Source-tree shadowing
   will otherwise import the editable namespace package and
   `HAS_NATIVE` will spuriously read False.
3. **Install via TestPyPI** with PyPI as the fallback index for
   transitive deps:
   ```bash
   pip install --no-cache-dir \
     --index-url https://test.pypi.org/simple/ \
     --extra-index-url https://pypi.org/simple/ \
     "ephemerides-spectral==<rc-version>"
   ```
   Note: this will resolve srmech from PyPI (production
   `v0.2.0` satisfies any reasonable floor downstream packages
   pin). If a downstream package pins srmech against a TestPyPI
   rc explicitly, you'll need `--pre` plus the version pin.
4. **Verify imports, native dispatch, key API surfaces.** Pattern:
   ```python
   import ephemerides_spectral, srmech
   print(ephemerides_spectral.__version__, srmech.__version__)
   # ephemerides-spectral has bridge.* surfaces; the AMSC ones
   # route through srmech.amsc.* after the Task #197 refactor.
   from srmech.amsc import _native
   print("srmech HAS_NATIVE:", _native.HAS_NATIVE, "ABI:", _native.NATIVE_ABI_VERSION)
   from ephemerides_spectral import bridge
   print(bridge.list_attested_sources()["n_sources"])
   ```
5. **Run the ephemerides-spectral tests** if installable that way
   (its publish workflow runs them as part of cibuildwheel
   per-cell — but a post-install end-to-end re-run is a real
   verification).
6. **Report** to the user: what version is on TestPyPI, did it
   install cleanly, are native dispatch + cross-package
   integration working, what's the diff vs. last good release.

The user's broader intent: before they cut **srmech v0.2.0** to
**production PyPI**, they want a parallel session validating that
the latest **ephemerides-spectral on TestPyPI** still works
correctly against the recent srmech rc series. If it does, the
v0.2.0 cut is safe. If it doesn't, debug the breakage before any
production publish.

---

## What NOT to do in this session

- Don't edit anything outside `docs/srmech/`, `docs/antikythera-maths/`,
  `docs/chess-maths/`, `docs/logo-maths/`, `docs/othello-maths/`, or
  the relevant root-level workflow files
  (`.github/workflows/srmech-*.yml`, `.github/workflows/ephemerides-spectral-*.yml`).
  In particular: **don't touch `src/`, `test/`, `platformio.ini`,
  `sdkconfig.*`** — those are the EMDR firmware project at the
  repo root.
- Don't introduce CAD-grade fabrication geometry, mesh-contact,
  axle-precession, lubricant, or related machinery. srmech models
  *data provenance*, not physical artefacts.
- The C library DOES vendor a `srmech_json` + `srmech_toml` parser
  (the old "don't vendor a parser in C" Phase-B5 note is SUPERSEDED by
  the rc128 full-1:1 mandate — a C-only / MCU host needs them to read
  JSON manifests / TOML descriptors with no Python). Both are
  caller-arena-backed with no compiled-in child cap (rc159/rc160).
- Don't introduce a new `hashlib.sha256(...)` direct call;
  route through `format.sha256_bytes(...)`.
- Don't add a new function > 60 lines or remove an assertion
  from an existing non-exempt function — the JPL ratchet fails.
- Don't squash-merge any PR. `gh pr merge --merge` only.
- Don't push to **production PyPI** without a TestPyPI rc
  verification round first. The auto-routing in the publish
  workflow makes a clean (non-rc) tag the production gate;
  treat it as a deliberate human-only action.
- Don't make new citations without verifying the underlying PDF
  (authors + title + arXiv ID).
- Don't write a long planning doc unless the user explicitly
  asks. Work from conversation context.

---

## Quick orientation commands

```bash
# Where am I?
pwd                                            # docs/srmech
ls                                             # CMakeLists.txt c/ notes/ python/ srmech_research_notebook.md ...

# What's the current rc on TestPyPI?
pip index versions srmech \
    --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple/

# What's the current rc on TestPyPI for ephemerides-spectral?
pip index versions ephemerides-spectral \
    --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple/

# Latest commits relevant to srmech
git log --oneline -20 -- 'docs/srmech/' '.github/workflows/srmech-*.yml'

# Latest CHANGELOG entry
head -100 python/CHANGELOG.md
```

---

## Where the parent-session memory + state lives

For deeper context the user might reference in conversation:

- **User's persistent memory** (auto-loaded only at repo root,
  not at this cwd):
  `C:\Users\sckir\.claude\projects\D--GitHub-mlehaptics\memory\MEMORY.md`
  and the per-topic `.md` files alongside it.
- **Repo-root CLAUDE.md** — describes the EMDR firmware
  project. Ignore unless the user explicitly asks about it.
- **Sister scope-doc** — `docs/antikythera-maths/CLAUDE.md`
  states the algebra/eigenbasis-only discipline for that
  subtree. The same discipline applies here.
- **srmech research notebook** — `srmech_research_notebook.md`
  (this directory) is the canonical statement of the
  Stored-Relationship Mechanism concept.

If you need to know what was true *as of this session's open*
without the parent's persistent memory:

- `srmech` is at **`v0.2.0` on production PyPI**. The earlier
  pure-Python `v0.1.0` is still in the PyPI release history but
  no longer the recommended install. TestPyPI rc history covers
  `0.1.1rc3` → `0.1.1rc9` and `0.2.0rc1` → `0.2.0rc2` (the full
  Task #201 build-out and the metadata-drift sweep).
- Task #201 (all 7 phases B1–B7) shipped. See
  `python/CHANGELOG.md` for the per-rc + per-release record.
- The C library is at **ABI v6** (current; this snapshot line
  originally read "v2 with two native symbols" — long superseded).
  The native surface now spans the full 14-class A–N vocabulary
  plus the genome / laplacian / bus / progress peers; see the "ABI
  compatibility" section above for the v1→v6 progression.
- **ephemerides-spectral 0.26.1rc1** (sibling subtree) pins
  `srmech>=0.1.1rc9` for the parallel-session verification round.
  After srmech v0.2.0 lands on production PyPI, ephemerides-
  spectral will bump that floor to `>=0.2.0` in its own follow-up
  release.

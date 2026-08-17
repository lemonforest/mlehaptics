# gh #1653 — PRE-rcN research report: C-projection parity on the config-driven cascade surface

**Measured at srmech 0.9.0rc444, native ABI 17 / expected 17, `has_native=True`, `dispatching=True`, Linux gcc.**
**Status: research + census + design only. ZERO edits to shipped source.**

`git status --porcelain` over `docs/srmech/python/srmech`, `docs/srmech/c/src`, `docs/srmech/c/include`,
`docs/srmech/python/tests` is **empty**. Every artifact is an untracked file under `docs/srmech/notes/`.

This report hands measurement + design to the session that ships the rcN. It does not ship the fix,
does not add ratchets, and does not touch the version SSOT. Section 9 lists exactly what is left to that session.

---

## 0. The single most important structural finding — read before anything else

**The task brief that commissioned this work contained a factual error that would have sent the rcN to the wrong file.**
The brief states that `c/src/srmech_dsl_chain_run.c` is *"the ONLY C chain file."* There are **three**, and
`srmech_dsl_chain_run.c:5` says so in its own words (*"a SIBLING interpreter to srmech_chain_run"*).

There are **two independent step grammars** behind the phrase "the config-driven cascade surface", they share no code,
and **they have opposite parity shapes**:

| | **SURFACE A** — `[[cascade.chain]]` | **SURFACE B** — `[[stage]]` |
|---|---|---|
| Python engine | `srmech/cascade/compose.py` (ADR-0002/0008, schema v1/v2) | `srmech/dsl/_toml_chain.py` + `_chain.py` |
| C peers | `srmech_compose.c` (parse) + `srmech_compose_run.c` (run) | `srmech_dsl_chain_run.c` |
| Population | **the 21 packaged cascade_catalog descriptors** (20 declared chain variants) | `chain().then(...)`, `srmech dsl run`, `[composite]` bodies |
| Step forms in Python | 3 | 6 |
| **Step forms C implements** | **1 of 3** (plain only) | **5 of 6** (`parallel_body` declines by design) |

**gh #1653 is about the config-driven cascade surface = the 21 descriptors = SURFACE A.**
Every implementation recommendation in this report targets `srmech_compose.c` / `srmech_compose_run.c`.

**Consequence for the issue text:** the sentence "C implements 1 of 3 step forms" is *exactly right for Surface A*
and *badly understates C for Surface B*, and the issue does not say which grammar it means. **No single number can
describe both grammars.** Any ratchet the rcN lands must name its surface.

---

## 1. Re-measurement at rc444 (definition-of-done item 1)

Both figures the issue carries are flagged in the issue itself as ~rc435 and requiring re-measurement.
I re-measured both. **One is confirmed; one does not reproduce.**

### 1.1 The headline table

| # | Quantity | Issue's carried figure (~rc435) | **MEASURED at rc444** | Verdict |
|---|---|---|---|---|
| 1 | Surface-A step forms C implements | 1 of 3 | **1 of 3** — plain executes; map `BAD_INPUT=2`; fold `BAD_INPUT=2`, at **both** parse and run | **CONFIRMED** |
| 2 | Surface-B step forms C implements | (not carried) | **5 of 6** execute; `parallel_body` recognised then declined | **NEW — issue silent** |
| 3 | Chains rejected, of 18 executable | **11 of 18 rejected** | **18 of 18 rejected** by `srmech_chain_run` (20 of 20 variants) | **DOES NOT REPRODUCE** |
| 4 | C **parse** accept / reject, of 18 | (not carried) | **11 accept / 7 reject** — 11 is an **ACCEPT** count | **NEW; explains the 11** |
| 5 | C-run-eligible chains, of 20 variants | (not carried) | **0 of 20** | **NEW — worse than the issue says** |
| 6 | Reference namespaces | (not carried) | Python **7** / C parse **4** / C run **3** | **NEW axis** |
| 7 | `chain_schema_version` | (not carried) | Python accepts (1,2); C catalog wrappers hard-require 1; all 20 shipped chains declare **2** | **NEW axis** |
| 8 | Distinct ops used vs C run table | (not carried) | **47 distinct ops used; 47 of 47 outside** the 10-entry table | **NEW** |
| 9 | #T1145 dotted spellings not resolving | 32 of 35 | **35 of 37** (32 data-overqualified + 3 registry-unregistered) | **GAP GREW** |
| 10 | #T1142 `map_op` composite guarantees | "lapses BOTH" | **BOTH lapse** (2/2), `fold_op` control fires 2/2 | **CONFIRMED** |

### 1.2 Figure 3 — "11 of 18 chains rejected". The measurement wins; the issue should be edited.

**MEASURED:** `srmech_chain_run` rejects **18 of 18** executable descriptors / **20 of 20** declared chain variants.
That is **+7 rejections worse** than the carried figure, not better.

The number 11 *is* real at rc444, but it has **opposite polarity on a different axis**: `srmech_chain_spec_parse`
**ACCEPTS 11** of 18 and rejects 7. I swept candidate definitions looking for an "11 rejected" reading and the only
quantity that equals 11 is an accept count:

```
srmech_chain_run REJECTS ................................... 18
srmech_chain_spec_parse REJECTS ............................  7
srmech_chain_spec_parse ACCEPTS ............................ 11   <== the only 11
chains carrying a map or fold step anywhere .................  6
chains whose every step is the plain form ................... 12
descriptor names IN the srmech_dsl_chain_run op tables ......  5
descriptor names NOT in the srmech_dsl_chain_run op tables .. 13
```

**Recommended issue edit.** Replace *"11 of 18 chains rejected"* with the measured pair:

> At rc444 the C run peer (`srmech_chain_run`) declines **20 of 20** declared chain variants (18 of 18 executable
> descriptors), 0 UNATTRIBUTED. The C parse peer (`srmech_chain_spec_parse`) **accepts 11** of 18 and rejects 7.

**Do NOT ship the word "inverted" as a measurement.** Two provenance hypotheses are live and neither is verifiable
without an rc435 build:

- **H1** — the old figure is the parse **accept** count mis-labelled as a reject count, taken when the catalog held
  17 executable descriptors (`klein4_from_one` arrived at rc438), i.e. "11 accepted of 17" → "11 of 18 rejected".
  Fits the polarity; **misses the denominator** (needs 17, issue says 18).
- **H2** — "chains carrying ≥1 `composition_of_c` op" (i.e. not reachable by widening the dispatch table alone)
  is **exactly 11 of 18 at rc444** — matches the denominator precisely. But it falls to 10 of 17 on the
  reconstructed rc435 surface, so it is not a better explanation.

Both are **inference**. The shippable sentence is *"the issue's 11-of-18-rejected figure does not reproduce at rc444;
the measured split is 11 accepted / 7 rejected on parse and 20 of 20 declined on run."*

### 1.3 Two axes the issue does not carry at all

**Reference namespaces.** Python knows **7** (`row|input|step|catalog|idx|bind|op`); C parse
(`co_match_namespace`, `srmech_compose.c:135-149`) knows **4** (`row|input|step|catalog`); the C **run** resolver
(`cr_resolve_ref`, `srmech_compose_run.c:265-289`) knows only **3** — `@catalog` falls through to defer.
In use across the 20 variants: `@idx` in 7, `@bind` in 7, `@op` in 1. **Do not size run-side namespace work off "4".**

**`chain_schema_version`.** Python `SUPPORTED_SCHEMA_VERSIONS == (1, 2)` (verified). The C **catalog-wrapper** sites
hard-require `== 1` (`srmech_compose.c:513`, `:675`; `srmech_compose_run.c:868`), and **all 20 shipped chains declare 2**.
Important scoping correction: this gate lives **only in the catalog wrappers**. `co_chain_head` does not read the field,
so on the **chain-level** entry points — the actual peer of `compose.run_chain` — v2 is **not** a blocker (11 of 20 v2
chains parse OK). Read as "the v2 gate blocks all 20", it would send the rcN to fix the wrong thing.

---

## 2. Per-form census (Surface A and Surface B)

Artifacts: `notes/_1653_step_forms_rc444.py` → `notes/_1653_step_forms_rc444.ndjson` (55 records).
Reproduce: `cd docs/srmech/python && python3 ../notes/_1653_step_forms_rc444.py` (exit 0). **I re-ran it; it reproduces.**

### 2.1 Surface A — the 3 step forms (where "1 of 3" is right)

| form | Python | C parse | C run | verdict |
|---|---|---|---|---|
| plain (`class`+`op`+`args`) | `compose.py:630-659` | `SRMECH_OK` | `SRMECH_OK` | **executes** |
| map (`map_over`+`body`[+`index`,`bind`]) | `compose.py:662-719` | `BAD_INPUT=2` | `BAD_INPUT=2` | **unrecognised** |
| fold (`fold_class`+`fold_op`+`fold_init`+`over`) | `compose.py:722-770` | `BAD_INPUT=2` | `BAD_INPUT=2` | **unrecognised** |

**Attribution.** `co_build_step` (`srmech_compose.c:287-319`) hard-requires `class`+`op`+`args` at `:299-303`; a map or
fold step carries none of the three, so the whole step is `SRMECH_ERR_BAD_INPUT`. The run loop `cr_run_steps`
(`srmech_compose_run.c:713-730`) has the same shape, demanding a STRING `op` at `:722-724`. **There is no map arm and no
fold arm anywhere in either file.**

**Step-form instance counts (measured, including nested map bodies): plain 115, map 14, fold 5 — total 134.**
Top-level steps: 72.

### 2.2 Surface B — the 6 step forms (where "1 of 3" is wrong)

| form | Python | C | verdict |
|---|---|---|---|
| `op` | `_toml_chain.py:248-256` | `:835-839` → `dsl_leaf_dispatch:537-565` | **executes** (7-op table) |
| `loop_n`+`sub_chain` | `:258-286` | `dsl_run_loop:657-678` | **executes** |
| `fold_init`+`fold_op` | `:288-312` | `dsl_run_fold:682-706` | **executes** (`cyclic_gcd` only) |
| `reduce_op` | `:325-333` | `dsl_run_reduce:710-732` | **executes** (`cyclic_gcd` only) |
| `map_op` | `:314-323` | `dsl_run_map_indexed:755-781` | **executes** (`seq_get` body only) |
| `parallel_body` | `:335-365` | recognised `:637-639`, declined `:791-793` | **declines by design** |

**Zero Surface-B forms are unrecognised.** All three negative-shape controls agree (no discriminator / `loop_n` without
`sub_chain` / mixed `op`+`fold_op` → Python rejects, C `NOT_IMPL`).

**FORM parity ≠ OP parity.** Surface B's 5-of-6 is the FORM axis only. Measured kernel coverage: C unary leaf table 7 names,
binary body table 1 (`cyclic_gcd`), map body table 1 (`seq_get`, not a catalog name). **8 of 21 catalog names have any C DSL
kernel; of the 18 executable descriptors, 5 are covered and 13 are not.** A chain over a covered form but an uncovered op
still defers to pure.

---

## 3. Per-chain census (Surface A)

Artifacts: `notes/_1653_chain_census_rc444.py` → `notes/_1653_chain_census_rc444.ndjson` (20 records).
Reproduce: `cd docs/srmech/python && python3 ../notes/_1653_chain_census_rc444.py` (exit 0). **Re-run; reproduces.**

### 3.1 The tally, as the script prints it

```
positive control CTL-1_literal    C parse rc=0  C run rc=0  byte-identical to python=True
positive control CTL-2_input_refs C parse rc=0  C run rc=0  byte-identical to python=True
HARNESS PROVEN (both controls C-accepted + byte-identical): True

step-form instances: {'plain': 115, 'map': 14, 'fold': 5, 'malformed': 0}
namespaces in use: [bind, idx, input, op, step]   C can parse only [row, input, step, catalog]
                                                  C-unknown in use: [bind, idx, op]
python: descriptor-only inputs ok=17/18 ; with the rc420 gate's CASE_DEFAULTS merged ok=18/18
CENSUS: python_ok=17 | C srmech_chain_run ACCEPT=0 REJECT=18
        | C srmech_chain_spec_parse ACCEPT=11 REJECT=7 | byte_identical=0 | UNATTRIBUTED=0
cause classes: {'C_GRAMMAR_GAP': 20}
op-table gap: 47 distinct ops used; 47 outside the C run table (36 dotted, 11 bare)
rosetta buckets: {'c_dispatched': 15, 'composition_of_c': 31, 'non_compute': 1}
blocker frequency over 20 variants: {'ops_outside_c_table': 20, 'step_form_map': 7,
        'ref_namespace_@bind': 7, 'ref_namespace_@idx': 7, 'step_form_fold': 5, 'ref_namespace_@op': 1}
shipped dispatcher: _chain_c_eligible true=0/18 ; _run_chain_native NATIVE_RAN=0/18
srmech_dsl_toml_chain_to_json accepts the descriptor TOML for 16/18
srmech_chain_catalog_parse agrees with srmech_chain_spec_parse on 18/18
```

### 3.2 The 7 rejected descriptors, with blocker sets (the work-sizing that matters)

| rejected descriptor | blockers | note |
|---|---|---|
| **net_chirality** | **fold ×1 — and nothing else** | its ONLY step is a fold; the sole chain whose step[0] is not plain |
| **parallel_sector_dispatch** | **`@op` — and nothing else** | otherwise a pure plain-form chain |
| autocorrelation | map ×2, `@idx`, `@bind` | map-of-map |
| klein4_from_one (×2 variants) | map ×1, `@idx`, `@bind` | |
| kuramoto_step (×2 variants) | map ×2, fold ×1, `@idx`, `@bind` | |
| octonion_dft | map ×3, fold ×1, `@idx`, `@bind` | |
| quaternion_dft | map ×3, fold ×1, `@idx`, `@bind` | |

**`fold` + `@op` alone moves parse rejects 7 → 5**, and those two are the only single-feature descriptors in the set.

### 3.3 The 11 parse-accepting chains — the op-table-only reachable set

`best_rational_signed`, `chiral_dual`, `cyclic_gcd`, `cyclic_mod_add`, `cyclic_mod_inv`, `cyclic_mod_mul`,
`cyclic_mod_mul_wide`, `cyclic_mod_pow`, `encode_loe_content`, `magnitude`, `schur_complement`.

For these, **widening `cr_dispatch`'s op table is the only C-side blocker left** — no new step form, no new namespace.
They need 23 distinct ops, of which **14 already have a C symbol** (`c_dispatched` in the shipped Rosetta ledger).

The measured `_RUN_C_OPS` table (10 entries, all Class-N): `atan_series_truncate`, `cos_series_truncate`,
`exp_series_truncate`, `log1p_series_truncate`, `sin_series_truncate`, `pi_cascade_digits`, `rational_add`,
`rational_div`, `rational_mul`, `rational_pow_uint`.

### 3.4 Attribution of all 20 variant rejections — 0 UNATTRIBUTED

- **19 variants → `op_not_in_c_table`**, rc=5 `SRMECH_ERR_NOT_IMPL` from `cr_dispatch` (`srmech_compose_run.c:616`).
- **1 variant (`net_chirality`) → `step_form_fold`**, rc=2 from `srmech_compose_run.c:723`.
- **0 DESCRIPTOR_DATA, 0 HARNESS_LIMITATION, 0 UNATTRIBUTED** at chain level.

**The fold/map gap is MASKED.** Because the op-table gate fires at step 0 for every chain except `net_chirality`,
19 of 20 variants never reach their map/fold step. The per-variant `c_blockers` field records the full blocker list so
the masking cannot hide work. **Practical consequence for the rcN: widening the op table alone will change the
*attribution* of many rejections without changing the 20, and the map/fold work will then surface.**

### 3.5 The second gate — Python-side, and not in the issue

`compose._chain_c_eligible` (`compose.py:1045-1061`) requires `step.class_id == "N"` **and** `step.op in _RUN_C_OPS`.
Measured: **`_chain_c_eligible` True for 0/18; `_run_chain_native` NATIVE_RAN for 0/18** (all `NATIVE_MISS`).

**So widening the C table alone changes nothing observable.** Both projections must move in the same rc, or the rcN ships
a C capability Python never routes to and the census still reads 0. That is precisely the shape of gap that sits unnoticed.

### 3.6 Two data findings, orthogonal to C

- **`kuramoto_step.general` cannot be run through the public callable at all.** All 5 of its proof cases raise
  `KeyError: 'path element .adjacency not found'` / `.pin_anchor`. It passes CI only because
  `tests/test_cascade_catalog_executable_rc420.py:253-258 CASE_DEFAULTS` merges `{adjacency: None, alpha: 0.0,
  pin_anchor: None, pin_strength: 1.0}` **under** the case — knowledge living in the test file, not the descriptor.
  Measured both ways: **17/18 on descriptor-declared inputs; 18/18 with test-side defaults merged.** A descriptor
  *declaration* gap (TOML cannot spell `None`), and a live inconsistency with the "catalog made callable" claim.
- **A bare-C host cannot even READ 2 of the 18 descriptors.** `srmech_dsl_toml_chain_to_json` accepts 16/18, rc=2 on
  `magnitude.toml` and `best_rational_signed.toml`. Attributed by a 3-document probe: `x = 1.5` → OK; `x = nan` →
  `BAD_INPUT`; `x = inf` → `BAD_INPUT`. Those are exactly the two descriptors carrying `nan`/`inf` proof cases.

### 3.7 The OTHER Surface-A population runs fine

All **7** `[[catalog.operator_chain]]` rows in `srmech/amsc/attested/` are **C-run eligible, 7 of 7**
(5 `*_series_truncate` + `friedmann_dark_fraction` + `pi_cascade_digits`). **`srmech_chain_run` is fully live on the
population it was built for; it is simply aimed at a different descriptor population than the one #1653 is about.**

---

## 4. #T1142 re-measurement — `map_op` missing from `_COMPOSITE_OP_KEYS`

Artifacts: `notes/_1653_t1142_planted_rc444.py` / `.ndjson`, `notes/_1653_t1142_fixprobe_rc444.py` / `.ndjson`,
`notes/_1653_t1142_ADVERSARIAL_rc444.py` / `.ndjson`, fixtures under `notes/_1653_t1142_fixtures/`.
**Re-ran the planted script; reproduces exactly.**

**Verified at rc444:** `_catalog.py:151 _COMPOSITE_OP_KEYS = ('op', 'fold_op', 'reduce_op', 'parallel_body')` —
`map_op` **absent**.

### 4.1 The 2×2, measured by execution

| key | (a) unknown-op | (b) cycle |
|---|---|---|
| **`map_op`** (uncovered) | **LAPSE** — loads clean | **LAPSE** — loads clean |
| **`fold_op`** (CONTROL, covered) | **FIRES** `ValueError` @ `_catalog.py:348` | **FIRES** `ValueError` @ `_catalog.py:330` |

The controls prove this is a **lapse, not an absence**: same planted defects, same descriptor shape, same loader —
only the key differs. **CONFIRMS the issue's claim that both composite load-time guarantees lapse.**

### 4.2 Four additions the issue does not carry

1. **The lapse admits a contract-FORBIDDEN descriptor as a live, running catalog op.** A `[composite]` body with
   `map_op = "srmech.cascade.leaves.seq_get"` (a dotted ref) **loads, resolves and runs** (`[7,8,9] → [7,8,9]`).
   `tests/test_dsl_op_naming_boundaries.py:509` pins the ADR-0008 boundary that a dotted ref inside a `[composite]`
   body is a **load error**. So the hole is not a missing message — it is a path by which a forbidden descriptor
   becomes a listed, executing op with `provenance="user:<sha256>"`.
2. **The two lapses degrade asymmetrically.** (a) becomes a clean `ValueError` at lookup (`_catalog.py:413`);
   (b) becomes **`RecursionError`** (`_catalog.py:466`) — stack exhaustion instead of a named cycle error.
3. **The one-line fix is contract-preserving but leaves `map_op` undeclarable in a `[composite]` body.**
   Measured: **0 of 21** bare catalog ops are usable as a `map_op` body (a map body must be data-first `body(seq, k)`).
   A bare data-first op (a `seq_get` descriptor) must be minted alongside, or the fix will read as "the fix broke map_op".
4. **A second, key-independent hole on the same surface.** `_validate_composite` runs ONLY when `desc.get("composite")`
   is a dict (`_catalog.py:293-295`). A user descriptor whose `[[cascade.chain]]` steps name an unknown op **loads clean**;
   the error appears only at `run_cascade_chain`. **On the `[[cascade.chain]]` axis there is no load-time unknown-op or
   cycle validation for ANY key** — and that is the axis the 18 shipped executable chains live on. The `map_op` one-liner
   does **not** close the load-time-validation gap on the config-driven cascade surface.

### 4.3 Fix probe — 3 passes × 7 cells

**FIX-A** (`_COMPOSITE_OP_KEYS += ("map_op",)`) is **sufficient and contract-preserving**: closes both lapsed cells,
leaves both controls firing, keeps the shipped ratchet's input class rejecting, and the shipped catalog is identical
across all three passes (21/18/3; `run_cascade_chain("magnitude", x=-3.5) == 3.5`).

**FIX-B** (FIX-A + a dotted-ref exemption) is a **contract change, not a fix**: it makes the `tests/test_dsl_op_naming_boundaries.py:509`
input class load, and it weakens guarantee (a) (an unimportable dotted body slips past load, failing only at lookup).

### 4.4 Why nothing caught it — the ratchet gap

Five places enumerate op-naming / discriminator keys. **Four include `map_op`; only the gate does not:**

| location | `map_op`? |
|---|---|
| `srmech/dsl/_catalog.py:151` `_COMPOSITE_OP_KEYS` | **NO** |
| `srmech/dsl/_toml_chain.py:86` `_RESERVED_STAGE_KEYS` | yes |
| `tests/test_dsl_op_naming_boundaries.py:198` `_CHAIN_OP_KEYS` | yes |
| `tests/test_combinator_kernel_closure.py:81` `C_COMBINATOR_KEYS` | yes |
| `c/src/srmech_dsl_chain_run.c:637` `disc[7]` | yes |

`test_combinator_kernel_closure.py` pins Python↔C discriminator parity strictly in both directions and its docstring
anticipates exactly this failure MODE — while the composite-validation mirror stayed open, because that ratchet's key set
is the *combinator* set, not the *composite-validation* set, so it structurally cannot see this gate.

**#T1142 cross-check that inverts the assumed direction:** C's `dsl_stage_is_combinator` (`srmech_dsl_chain_run.c:637-639`)
carries all **7** discriminator keys **including `map_op`**. On this axis **the C projection is COMPLETE and the Python
composite validator is the one behind.**

> **Precision note for a ratchet author.** The census cites that C array as a "6-form" denominator. Hand-read, the array
> holds **SEVEN** strings (`loop_n, sub_chain, fold_init, fold_op, reduce_op, parallel_body, map_op`), because
> `loop_n`/`sub_chain` and `fold_init`/`fold_op` are two spellings each of one form. The **6** is the FORM count and is
> correct (it matches Python's six discriminators at `_toml_chain.py:225-232`), but **a ratchet that counts entries in
> that C array will read 7** and disagree with the census by one.

---

## 5. #T1145 re-measurement — dotted step-op spellings vs `ToolSchema.resolve()`

Artifacts: `notes/_1653_t1145_spellings_rc444.py` / `.ndjson`, `_1653_t1145_executor_probe_rc444.*`,
`_1653_t1145_fix_prototype_rc444.*`, `_1653_t1145_c_api_verify.c`. **Re-ran the primary script; reproduces.**

**MEASURED: 35 of 37 distinct dotted spellings do not `resolve()`** (carried: 32 of 35). Delta **+2 denominator,
+3 numerator**; failure ratio 91.4% → 94.6%. **The gap GREW.** Occurrence-weighted: 89 of 91.

Harvest: 21 descriptors, **121** op-key occurrences (`op` 116, `fold_op` 5, and **`reduce_op` / `parallel_body` /
`map_op` all ZERO**) → 48 distinct spellings (37 dotted, 11 bare). Tool schema carries **663** entries.

### 5.1 The split that decides data-vs-registry — this is the new information, not the size

- **32 of 35 → `data:descriptor-overqualified`.** One single defect: the descriptor addresses the real Python module
  path while both registries (Python **and** C) use a **flat** namespace under `srmech.cascade`. `resolve()` accepts an
  exact name or a unique dotted **suffix**, and the descriptor spelling is *longer*, so it is neither.
  Dropped interior segment: `leaves` 12, `composites` 8, `hypercomplex_dft` 8, `atoms` 3, `parallel` 1.
  **All 32 target names exist in the registry.**
- **3 of 35 → `registry:unregistered`** — genuinely missing, and they import cleanly to real callables:
  `srmech.amsc.descriptor.render_template` (a **peer** of the registered `srmech.math.template.render`, not a duplicate —
  needs its own entry, not an alias), `srmech.signal_processing.rbs_hdc_instrument.mint_vector`,
  `srmech.signal_processing.encode_loe_content`.

**The carried numerator 32 is numerically identical to the data-overqualified bucket**, which suggests the rc435
measurement either used a smaller descriptor set (`klein4_from_one` arrived rc438) or counted only the flat-registry-
shadowed class and excluded the 3 unregistered ops. **Inference, not measurement.**

### 5.2 Attribution — which of three resolvers is broken

| resolver | dotted | bare | total |
|---|---|---|---|
| **R1 EXECUTOR** (`compose.py:1180 _resolve_step_op`) | 38/38 | 11/11 | **49/49** |
| **R2 BUILDER** (`_catalog.py:388 lookup_cascade_op`) | 38/38 | 1/11 | 39/49 |
| **R3 INTROSPECTION** (`ToolSchema.resolve`) | **2/38** | 10/11 | **12/49** |

**The gap is entirely R3.** The names the shipped proofs actually execute are unreachable through the surface meant to
name them. Proven independently: **20 of 20 chain variants resolve at activation and 98 of 98 proof cases run to a value**
(with `CASE_DEFAULTS` merged).

### 5.3 Two secondary deltas the issue does not carry

- **One BARE spelling also fails**: `sha256_raw` — deliberately EXEMPTED at `tests/test_tool_schema_coverage.py:88` as a
  constructor companion. **A documented non-bug; keep it out of any fix ratchet.**
- **1 of the 21 descriptor NAMES is itself unregistered**: `encode_loe_content`. That descriptor is invisible three ways
  over (its name, its top-level op, two of its step ops) — **a sharper one-line statement of the #T1145 complaint than
  the step-op ratio.**

### 5.4 Fix candidate, with safety measured

**Segment-subsequence resolve** (registry-side, one rule): after exact and suffix miss, accept a registry name whose
dotted segments are an ordered subsequence of the query's, leaf matching exactly, only when exactly one entry qualifies.

- **S2 PASS** — all 32 data-class spellings resolve uniquely to the expected flat name.
- **S3 PASS** — the 3 registry-class spellings still resolve to **nothing**. *This is the important one:* a rule that
  "fixed" those three would be inventing a match and **hiding the real registration gap.**
- **S1 is TAUTOLOGICAL and must not be cited as evidence of safety.** The rule only runs after `lookup()` misses AND
  `resolve_all()` returns 0, so it is additive by construction and can only turn `None` into a hit — of the 663 registry
  names used as queries, **zero reach the new tier at all**. The genuine risk is *ambiguity*, which S1 does not probe.
  The verdict stands; the cited evidence for it does not.
- **Bookkeeping error to not carry forward:** the script reports "0 regressions over 711 probes (663 + 48 spellings)".
  The real probe set is 663 + **69** NDJSON rows = **732**. Substance is unharmed (and stronger); **do not ship "711" or
  "48" in a ratchet.**

**Alternative** (safe fallback): rewrite the descriptor strings — 84 edits across 11 files. Cheaper to review, but it
loses the module-path addressing the dotted-import lever was built for. **The subsequence rule is the better shape.**

**C parity: no C change required for the 32.** `c/src/srmech_tool_registry.c` spells all 32 flat names identically.
Verified at **API strength** (not grep strength) with a JPL-clean bare-C driver against
`srmech_tool_registry_count` / `_get` / `_find` (`srmech.h:5802/5805/5809`) — the earlier caveat that "srmech.h exports no
tool-registry enumerator" was **FALSE**; the enumerators exist and the check was run. The 3-op registry gap is
**symmetric across C and Python**, so registering them is a two-sided change.

---

## 6. The implementation path (Surface A)

Design artifacts: `notes/_1653_proto_fold.c`, `notes/_1653_path_measure_rc444.py` / `.ndjson`.

### 6.1 The FOLD arm — prototyped, compiled, and run

`notes/_1653_proto_fold.c` (460 lines, standalone). **I built and ran it myself:**

```
cd docs/srmech/c && cc -std=c99 -Wall -Wextra -Wpedantic -O2 -Iinclude \
  ../notes/_1653_proto_fold.c build/libsrmech.a -o /tmp/proto_fold && /tmp/proto_fold
```

**Zero warnings.** Exit 0. **7 of 7 positive cases MATCH** `net_chirality`'s own shipped proof-case values
(`1, 0, 0, 0, 1, -1, -1`); **5 of 5 negative controls decline at the stated status** (mixed v1+v2 → rc=2;
unknown body op / float `fold_init` / `@bind` in `over` / `fold_args` present → rc=5).

Dispatch points: **PARSE** `co_build_step` (`srmech_compose.c:287-319`) needs a form discriminator ahead of the
required-keys check at `:299-303`; **RUN** `cr_run_steps` (`srmech_compose_run.c:713-730`) needs `switch (form)` in
place of the inline STRING-`op` check at `:722-724`.

Normalized fold node (canonical-sorted): `{"class_id", "fold_op", "on_error", "over", "step_form": "fold"}`, with
`fold_init` / `fold_args` re-attached Python-side from the raw dict by identity — the same trick `args` already uses
(so a `[num, den]` seed keeps its Python type). `_chain_spec_from_native` (`compose.py:378-397`) then dispatches on `step_form`.

**Arena: NO change.** A fold produces one accumulator carrier per element; the existing run term
(`4096*chain_len + 1 MiB`) covers 8192 carriers at the function's own asserted 128-byte bound. **Fold is the one arm that
does not move the arena contract.**

**Body op.** `net_chirality`'s `fold_op` is `srmech.cascade.leaves.orientation_compose` — **no C symbol of that name
exists**. It is a two-line composition over one that does: `orientation == 0 → 0` (absorbing zero, **Class-K pin-slot**)
else `srmech_cascade_reorient_i64(orientation, acc)` (**Class C**). No new math, **no `abs()`**. Match the name with the
`dsl_map_body_is_seq_get` pattern (`srmech_dsl_chain_run.c:738-745`): bare **or** any dotted spelling ending
`.orientation_compose` — necessary, because `cr_dispatch` keys on bare names while **36 of the 47** ops are dotted.

**JPL status — I ran the shipped scanners myself** (`tests/test_jpl_audit.py::_scan_functions`, read-only import):

| rule | `_1653_proto_fold.c` | `_1653_barec_host_rc444.c` |
|---|---|---|
| functions scanned by the ratchet | 13 (+1 invisible, see below) | 30 |
| Rule 4 (≤60 lines) | **CLEAN** — longest `pf_run_fold` 38 | **CLEAN** — longest `a_run_variant` 59 |
| Rule 5 (≥2 asserts) | **CLEAN** | **CLEAN** |
| Rule 1 goto/setjmp/longjmp | 0 | 0 |
| Rule 3 malloc family | 0 | 0 |
| bare `abs(` | 0 | 0 |
| `math.h` | not included | not included |

**Fold is the only arm with no Rule-1 exposure** — a fold has no body step list, so it never re-enters the step runner
and adds **zero** recursion cycles.

> **Scanner limitation I verified first-hand.** `_scan_functions` skips any definition line beginning `static const`, so
> `pf_resolve_ref` (`_1653_proto_fold.c:205`) is **invisible** to it — as are `cr_walk_json` (`srmech_compose_run.c:176`)
> and `cr_find_named_chain` (`:816`) in shipped code. **Rules 4 and 5 are vacuous for every `static const`-returning
> function in the tree.** Do not read a clean Rule 4/5 run as covering those.

### 6.2 The MAP arm — four independent sub-problems

1. **JPL Rule 1 is the binding constraint, and it is STRICT.** A map body is a step list, so the obvious implementation
   is mutual recursion — exactly what `srmech_dsl_chain_run.c` does. **That cycle is one of the 9 SEEDED entries in
   `tests/test_jpl_audit.py:199-231 RULE_1_RECURSION_SEEDED`, and `test_rule_1_no_new_recursion` fails on any cycle not
   in that set — including an existing cycle that gains a member.** So `srmech_dsl_chain_run.c` is prior *art to read,
   not to copy*. The map arm must be an **explicit frame stack**, the remedy the ratchet's own comment names (`:228`).
   Measured shipped bounds: max nesting depth **1** (two levels), max body length **19**, max binds **9** — a frame cap
   of 8 gives 4× headroom.
2. **The carrier has no FLOAT kind, and 13 of 14 maps need one.** `cr_value_t` (`srmech_compose_run.c:91-101`) is
   `{NONE, INT, STR, RATIONAL, LIST}`; `cr_json_scalar` (`:207-220`) returns NULL for `SRMECH_JSON_DOUBLE`.
   **This is what forces the ABI bump.**
3. **The arena formula is LINEAR; a nested map is QUADRATIC.** `autocorrelation`'s map-of-map allocates ≈ `2n² + 3n + 1`
   carriers. Reported crossover at the 128-byte bound: fits through n=128, overflows at n=256. *(This figure is
   INHERITED from the design session — I did not re-run it; see §8.)*
4. **Body ops.** `@idx`/`@bind` must land in **both** `co_match_namespace` (4→6) **and** `cr_resolve_ref` (which knows 3).
   Then the bodies: of 16 distinct map/fold body ops the descriptors name, **only 4 have any C symbol**
   (`srmech_vec_add`, `srmech_vec_scale`, `srmech_mod_add`, `srmech_mod_mul`); 12 have none.

### 6.3 Ordered plan — with a sequencing hazard I measured by execution

**Slice 1 (ABI 17, no bump): `net_chirality` end-to-end in C.** Five coordinated edits; **the ORDER is load-bearing:**

1. `srmech_compose.c` — form discriminator + `co_build_fold_step` + normalized fold node.
2. `srmech_compose_run.c` — `cr_run_fold` + the `orientation_compose` body entry (lift the prototype).
3. `compose.py:1064 _spec_to_chain_dict` — make fold-aware.
4. `compose.py:1002 _run_ints_fit_i64` — make fold-aware.
5. `compose.py:1045 _chain_c_eligible` — **LAST**; and relax `_chain_has_v2_forms` for the fold case.

**Why 5 must be last — measured, not reasoned** (`net_chirality` step[0] is a `FoldStepSpec`):

```
_chain_c_eligible(spec)          -> False        # the isinstance guard, compose.py:1055
_run_ints_fit_i64(spec, None,{}) -> AttributeError: 'FoldStepSpec' object has no attribute 'args'
_spec_to_chain_dict(spec)        -> AttributeError: 'FoldStepSpec' object has no attribute 'class_id'
_chain_has_v2_forms(chain)       -> True
```

`_chain_c_eligible`'s type check is the **only** thing keeping those two helpers unreached, and `_run_chain_native`
calls them immediately after it. **Widen the gate first and the next fold chain `AttributeError`s out of `run_chain`.**

**Slice 2 (ABI 17): the `@op` namespace.** `parallel_sector_dispatch`'s sole blocker; parse-only reach. Rejects 7 → 5.

**Slice 3 (ABI 17 → 18): the map arm.** Explicit frame stack + `CR_FLOAT` + `@idx`/`@bind` on both sides + body-local
`@step[N]` + the arena decision. One bump covers the whole slice.

### 6.4 The two widening traps — both are descriptor LOOKUP, and C has none

`#T1143` (composite op → descriptor's chain, `_catalog.py:418-421`) and `#T1144` (a step referencing a descriptor,
`:411-416`) both need `load_catalog()` — a filesystem scan. **C has no descriptor loader, and the reason is
architectural:** `srmech_catalog_*` (rc172) is explicitly *caller-owned state* — "the registry / kernel state is OWNED BY
THE HOST and passed in per call … No global mutable C state."

The raw ingredients nonetheless exist (`srmech_plat_dir_*`, `srmech_plat_file_read`, `srmech_toml_parse`,
`srmech_plat_has_filesystem()`), so **"impossible" is not an available excuse** — the cost is the real argument.

**Verdict: OUT OF SCOPE for this rcN — file the decline under ADR-0009 §5.** (a) It inverts the caller-owned state model
the whole rc172 catalog surface rests on — an ADR-level decision, not an rc. (b) It is a *name-resolution* capability,
orthogonal to the *step-grammar* capability #1653 is about; bundling them makes the grammar work unshippable.
(c) The cycle semantics it must mirror are **themselves defective today** (a `map_op` cycle reaches `RecursionError` at
`_catalog.py:466`; the C equivalent is a stack overflow, i.e. a crash, not a decline) — mirroring would copy a defect into C.

**The §5 filing is mandatory regardless**, as a ledger row per capability, each naming C as the declining implementation
and `load_catalog()` as the boundary. **Not a source comment** — §5 names that failure mode explicitly.

### 6.5 Surface B `parallel_body` — a FILING task, not a coding one

`srmech_cascade_parallel_sector_dispatch` **already exists** (`srmech.h:956`), already threads, is malloc-free;
`srmech_plat_has_threads()` exists. The real blocker is that **the bump arena is not thread-safe** (four sectors
bump-carving one arena would race); the fix is four disjoint sub-arenas, which the function's own disjoint-slice
contract already models. **ADR-0009 §4 does not exempt this** — the only exemption is host-integration/protocol-adapter
layers, and Klein-4 sector dispatch is not one. Per §5, *"it declines cleanly, the other path works"* is explicitly
**not** a parity argument. So `parallel_body`'s status must become either implemented or a filed §6a ledger row.

---

## 7. Gate spec and bare-C host status

### 7.1 Gate spec

`notes/_1653_gate_spec_rc444.md` (1303 lines, §0–§9, includes a ready-to-lift pytest skeleton as fenced text),
seeded by `notes/_1653_gate_seed_rc444.py` / `.ndjson`, controls in `notes/_1653_gate_controls_rc444.py`.

| gate | shape | seed | fires on |
|---|---|---|---|
| **G1** form closure | INVARIANT, bidirectional | 10 rows (3 forms + 7 namespaces) | a Python widening with no C peer; a stale decline row not deleted |
| **G2** chain-ledger closure | INVARIANT, bidirectional | 20 rows: `op_not_in_c_table` 11, `step_form_map` 7, `step_form_fold` 1, `ref_namespace_v2` 1 | MISSING / STALE / WRONG-REASON, as three distinct messages |
| **G2b** the CEIL | pinned integer, down-only | 20 | the hole G2 cannot see: new descriptor + new ledger row keeps G2 green while the residual GROWS |
| **G3** op-table mirror | INVARIANT, by execution | 10 claimed / 10 confirmed / 0 dead / 5 negatives not live | the Python literal at `compose.py:985` drifting from C unwatched |
| **G4** route coincidence | INVARIANT (**VACUOUS at seed**) | `0 == 0` + a mandatory non-vacuity control | widening `cr_dispatch` without lifting the Class-N restriction |
| **G5** anchor liveness | INVARIANT, meta | 27 claims / 27 verified | the two mis-citations this investigation actually produced |

**I re-ran the controls. All seven planted failures FIRE and the unperturbed predicate set PASSES:**

```
PC-1 FIRES: unledgered: ['form:while']
PC-2 FIRES: ledger says EXECUTES measured UNRECOGNISED
PC-3 FIRES: [MISSING] ['net_chirality.default']
PC-4 FIRES: [STALE] ['synthetic_control.default']
PC-5 FIRES: [WRONG REASON] net_chirality.default: ledger op_not_in_c_table measured step_form_fold
PC-6 FIRES: claimed in-table but cr_dispatch returned NOT_IMPL
PC-7 FIRES: anchor :616 actual 'return SRMECH_ERR_NOT_IMPL; ...'
UNPERTURBED all-predicates: PASS
```

**The missing ratchet is the structural finding.** Measured: `grep -rln "srmech_compose" tests/` → **nothing**;
`grep -rln "_MAP_KEYS\|_FOLD_KEYS" tests/` → **nothing**. **The tree has ZERO Surface-A form-parity ratchet**, while
Surface B has `test_combinator_kernel_closure.py::test_c_discriminator_table_matches_python`, strict both ways, whose
docstring says it exists because *"a Python-side widening (exactly like rc420's `map_op`) would leave the C peer silently
deferring."* **Surface B got that guard; Surface A never did. That asymmetry is the structural reason this gap sat**,
and closing it is worth more than any single arm.

### 7.2 Bare-C host — the ADR-0003 criterion is already met, on the wrong population

`notes/_1653_barec_host_rc444.c` (1078 lines, 30 functions). **I rebuilt and re-ran it:**

```
cc -std=c17 -Wall -Wextra -Wpedantic -Werror -O2 -Ic/include \
   -o /tmp/barec1653 notes/_1653_barec_host_rc444.c c/build/libsrmech.a
```

**Zero warnings under `-Werror`.** `ldd` lists only `linux-vdso`, `libc.so.6`, `ld-linux` — **no libpython, no libm.**

| axis | measured |
|---|---|
| positive control (surface-A path, `rational_add` → 5/6) | **1 of 1** |
| **SURFACE B** `[[catalog.operator_chain]]` — `srmech_chain_catalog_parse` + `srmech_catalog_run_chain` | parse **7/7**, run **7/7**, attested parity **7/7** |
| **SURFACE A** `[[cascade.chain]]` — 21 descriptors, 20 variants | spec-parse **11 ok / 9 rej**, run **0 ok / 20 rej**, HOST_LIMIT **0**, UNATTRIBUTED **0** |

The Surface-B result includes `friedmann_dark_fraction`: **9 steps**, array-of-`@row` args, and a `@step[N].output`
reference chain, returning the exact rational **53000000000000137/2062800000000000137** matching its own attested row.
So a bare-C host already exercises the **reference grammar and multi-step value threading over bignum-ℚ**.

**Therefore #1653's acceptance criterion as literally written ("load the shipped catalog and run a declared chain
end-to-end") already PASSES at rc444.** It must be re-scoped to *"run a `[[cascade.chain]]` descriptor"* or it will be
closed by a proof that does not address the gap.

**Wall 4 — a NEW blocker the issue does not carry.** `cr_json_scalar` (`srmech_compose_run.c:207-220`) accepts
INT / NULL / STRING **only**; a JSON double or bool → NULL → defer. So **widening `cr_dispatch` alone does NOT unblock
the 11 parse-accepting chains**, because 4 of them pass float args (`schur_complement` 9 floats, `chiral_dual` 3,
`best_rational_signed` 2, `magnitude` 1).

**The honest first slice: the 7 chains whose ONLY C-side blocker is the op table** (map 0, fold 0, unknown-ns 0,
float 0, bool 0): `cyclic_gcd`, `cyclic_mod_add`, `cyclic_mod_inv`, `cyclic_mod_mul`, `cyclic_mod_mul_wide`,
`cyclic_mod_pow`, `encode_loe_content`.

**The gap is the table, not the math** — proven in the same binary: `srmech_gcd(12,18)` → 6 and
`srmech_cascade_cyclic_gcd_u64(12,18)` → 6 both return `SRMECH_OK`, in the same process that just declined the
`cyclic_gcd` chain declaring `class=I op=gcd`.

**MCU sizing (a finding in its own right).** `srmech_chain_run_arena_bytes` is dominated by `4096 * chain_len`, so a
**3.5 KB chain demands ~16 MB of arena**: surface-A run arena 2.08 MB (`cyclic_gcd`) → 16.4 MB (`klein4_from_one.wound`).
The host's whole static budget is 104 MB. **An MCU host cannot pay this**, so *"runs without Python"* and *"runs on a
microcontroller"* are **not yet the same claim.**

### 7.3 An anomaly I must report: a one-off, unexplained `B_attested_parity_ok = 2`

**On my very first run of the freshly built host, the summary reported `B_attested_parity_ok: 2` (not 7).** Preserved as
`notes/_1653_barec_ANOMALY_parity2_observed_once.ndjson`.

What I then did, and measured:

- The five chains that reported parity 0 (`exp/sin/cos/log1p/atan_series_truncate`) had **CORRECT C values**. I verified
  independently in Python against the same first-matching attested rows: all 5 match
  (`exp_zero_N5` 1/1, `sin_0_1_N5` 0/1, `cos_0_1_N5` 1/1, `log1p_0_1_N5` 0/1, `atan_0_1_N5` 0/1). **So this was never a
  C parity failure.**
- **35 subsequent runs of the same binary all report 7/7**, as does the shipped artifact
  `notes/_1653_barec_host_rc444.ndjson`. Rebuilt at `-O0/-O1/-O2/-O3`: **7/7 at every level.**
- Instrumented `b_parity` in a scratch copy: it **returns 1 for all seven**.
- **Hypothesis tested and REFUTED:** I suspected arena aliasing in `b_parity` (`d` parsed with the full 16 MB arena,
  `r` into its upper half). Measured `srmech_json_parse`'s footprint: **2934 bytes, nodes at offset 0, independent of the
  workspace size given** (16 MB / 8 MB / 64 KB all identical). **The two parses cannot overlap.** Aliasing is not the mechanism.

**Status: UNEXPLAINED, non-reproducing, observed once in 36 runs.** The one suggestive correlation is that the 5 affected
chains are **exactly the 5 that share a single `row.ndjson`** (`asymptotic_calculus`), while `pi_cascade_digits` and
`friedmann_dark_fraction` each have their own — but I could not turn that into a mechanism.

**Actionable consequence: the design session's recommended ratchet "strict-equality on
`B_attested_parity_ok == B_run_ok == B_targets` (7/7/7)" would have FAILED on my first run.** The rcN must either
determinism-check that counter (run it N times in CI) or not make it a strict-equality gate.

---

## 8. HONEST SCOPE — measured vs inferred vs not attempted

### 8.1 MEASURED — I personally ran these and saw the output in this session

Environment (`0.9.0rc444`, ABI 17/17, `has_native`/`dispatching` True, catalog 21/18/3);
`_1653_step_forms_rc444.py` (exit 0, 55 records); `_1653_chain_census_rc444.py` (exit 0, 20 records);
`_1653_t1142_planted_rc444.py` (the 2×2); `_1653_t1145_spellings_rc444.py` (35 of 37); `_1653_gate_controls_rc444.py`
(PC-1…PC-7 fire, unperturbed passes); the fold prototype (build clean, 7/7 positive, 5/5 negative);
the bare-C host (build `-Werror` clean, `ldd` libc-only, the full tally); the JPL scanner run over both C files;
`_COMPOSITE_OP_KEYS` and `_RUN_C_OPS` contents; `SUPPORTED_SCHEMA_VERSIONS == (1,2)`; the `k="f"` `ValueError`
and the five kinds that do reconstruct; the D1 divergence; the three `FoldStepSpec` sequencing errors;
`SRMECH_ABI_VERSION 17` at `srmech.h:364` and `EXPECTED_ABI_VERSION 17` at `_native/__init__.py:222`;
the 5 version SSOT locations; the `srmech_json_parse` footprint measurement.

### 8.2 INHERITED from the sibling sessions and NOT re-run by me

Stated as findings, flagged as not independently re-measured here:

- **The map-arena `n≥256` overflow cliff** (fits through n=128, overflows at n=256). Arithmetic rests on the arena
  function's **own asserted 128-byte-per-carrier upper bound**, not a measured `sizeof` — the real struct is smaller,
  so **n=256 is a LOWER bound on capacity; the true cliff is further out.** The *shape* (linear arena vs quadratic map)
  is exact regardless.
- The #T1145 executor/builder/introspection 49-row probe (R1 49/49, R2 39/49, R3 12/49) and the `search()` recovery
  numbers (rank-1 19 of 32, top-5 26 of 32).
- The #T1142 fix-probe 3×7 matrix and the adversarial extensions (3-node cycle, self-cycle, sub_chain nesting).
- The 84-edit / 11-file alternative-fix sizing for #T1145.
- The Rosetta bucketing (15 `c_dispatched` / 31 `composition_of_c` / 1 `non_compute`) — printed by the census I re-ran,
  but the bucketing itself resolves BARE ops through `compose.DEFAULT_CLASS_REGISTRY`, which is **inference, not a
  symbol lookup in the `.so`**. All 47 resolved with zero `NOT_IN_LEDGER`, so it did not bite.
- The gate spec's 27 anchor verifications and its 1303-line text.

### 8.3 INFERRED — explicitly not measurement

- **Both provenance hypotheses (H1, H2) for the issue's "11".** Unverifiable without an rc435 build.
- **Wall 4 (float/bool args) is a PREDICTION** read off `cr_json_scalar`'s source, not a measured decline — the op table
  fires first at step 0 and **masks** everything downstream. **The 0-of-20 figure is therefore a FLOOR**, and whether
  widening `cr_dispatch` reveals wall 4 *and only* wall 4 cannot be known until the table is widened.
- The map arm's explicit-frame-stack design: its 60-line / 2-assert feasibility is **reasoned from shipped idioms, not measured.**
- That `#T1143` / `#T1144` denote what this report says they denote — those IDs appear **nowhere in the tree**; the
  reading comes from the brief's one-line descriptions plus the `lookup_cascade_op` code they must mean.

### 8.4 NOT ATTEMPTED

- **No map prototype.** Specified but unbuilt.
- **`srmech_catalog_run_chain` was not driven from Python** (the bare-C host did drive it, 7/7). The Python-side census
  deliberately did not wrap chains for it, because inventing a catalog wrapper would not be the shipped surface.
- **No macOS clang, no Windows MSVC cell.** Everything is Linux gcc, this worktree's `libsrmech.so` / `.a` at ABI 17.
  The bare-C host uses POSIX `dirent.h`, so **it will not compile in the Windows pedantic cell as written.**
- **No test file was run under either #T1142 fix.** FIX-A/FIX-B were prototyped by runtime rebind of `_catalog` globals,
  never by editing shipped source. The shipped ratchet at `test_dsl_op_naming_boundaries.py:509` was *reproduced* as a
  cell, not *executed* under the patch.
- **No ratchet, no test, no CHANGELOG, no version bump, no rc tag** — all left to the srmech session (§9).

### 8.5 UNATTRIBUTED items — the complete list

- **Chain-level rejections: ZERO UNATTRIBUTED.** All 20 variant rejections pin to a named C source line, in **two
  independently written classifiers** (the census's `classify_decline` and the controls file's `_first_gate`) that
  **agree on all 20**. Two separately-written classifiers reaching the same attribution beats one classifier run twice.
- **ONE unattributed item exists, and it is mine:** the one-off `B_attested_parity_ok = 2` (§7.3). Mechanism unknown;
  the leading hypothesis was tested and refuted.

### 8.6 Where our result is WEAKER than it looks — read this before quoting anything

- **`byte_identical = 0` is VACUOUS, not a mismatch count.** C executed no Surface-A chain, so the column had nothing to
  compare. **Never report it as "0 divergences found."**
- **G2 green means "fully attributed", NOT "parity achieved."** All 20 variants are ledgered today, so **G2 is green at
  0-of-20 C coverage.** If release prose says "the C parity gate passes" without that qualifier, it reads as
  "parity achieved" when the measured state is "parity absent, fully attributed."
- **G4 is vacuous at its seed** (`0 == 0`). Its only content is the synthetic control. If that control is dropped as
  redundant, G4 becomes a gate that cannot fail and should be deleted rather than kept as decoration.
- **These gates detect the REGRESSION, never the original.** Every seed is measured pre-repair; re-seeded post-repair a
  gate can only fire on growth. A ceiling seeded at the live population is a claim about the future. **No release prose
  may say they catch the class of defect that caused #1653.**
- **NO gate here covers REJECTION parity.** Divergence **D1 is live through the shipped Python builder** — I re-verified:
  `chain().then("magnitude", bogus=1).run(-3.5)` → **3.5** under native dispatch, while
  `srmech.cascade.magnitude(-3.5, bogus=1)` → **`TypeError`**. Both C parsers are **required-keys** checks, never
  **closed-key-set** checks. G1–G5 measure what C ACCEPTS, never what it should REFUSE. **Widening either C parser
  without a closed-key-set check in the same commit makes this strictly worse**, and G1–G5 stay green throughout.
- **D1 is a REJECTION-parity break, not a wrong-value break.** The value C returns (3.5) equals the correctly-spelled
  call's value. Frame the fix as *"C must decline the unknown key"*, not *"C computes the wrong number."*
- **Surface-A "structure probe" verdicts are GRAMMAR, not per-call.** `magnitude` and `best_rational_signed` still
  decline their `nan`/`inf` proof cases at the JSON parser, upstream of the grammar. Read the structure-probe field.
- **Surface-B "executes" means "for the documented carrier shape."** The C leaves gate on the F1 carrier kind
  (`leaf_magnitude` returns `NOT_IMPL` for a `DV_INT` input at `srmech_dsl_chain_run.c:298`). Not a per-call guarantee.
- **`@idx` / `@bind` are legal in Python ONLY inside a map body** (`compose.py:303-323` raises at ACTIVATION for an
  unbound name). Their `python_accepts=true` verdict is measured **in map scope**; a plain-step probe reports a spurious
  false, which is the unbound-name guard, not a grammar gap.
- **The seeds EXPIRE.** This is an rc444 snapshot of a moving surface: the catalog grew 20 → 21 descriptors between
  rc420 and rc444, **which is very likely how the issue's figures went stale in the first place.** Re-run the scripts;
  do not quote these numbers in a later rc.
- **`CASE_DEFAULTS` is a MIRROR with no protecting assert.** The census mirrors
  `tests/test_cascade_catalog_executable_rc420.py:253-258` read-only. If the ship edits that dict, the
  `python_with_test_defaults` column goes stale silently (unlike the op-table and namespace mirrors, which do assert).

### 8.7 Corrections to carry forward (defects in the sibling censuses, found by cross-checking)

1. **A mis-cited source line.** A census attribution string reads `srmech_compose_run.c:866-876 srmech_json_parse`.
   Lines 866-876 are inside **`srmech_catalog_run_chain`** — a *different function*. `srmech_chain_run`'s own parses are
   at **`:789`** (chain_json) and **`:792`** (ctx_json), and for the non-finite cases it is the **ctx** parse at `:792`
   that fires. **Zero numeric impact** (4 per-case records, 0 structure-probe records), but an attribution naming a line
   in the wrong function is precisely the failure the confound guard exists to prevent. **Fix the string.**
2. **`ref_namespaces_c = 4` is axis-ambiguous** and overstates the RUN axis. 4 is the PARSE count; the run resolver knows
   **3**. No numeric impact, but **do not size run-side namespace work off "4."**
3. **The C discriminator array holds 7 strings, not 6** (§4.4 note). The 6 is the FORM count and is correct; a ratchet
   counting array entries reads 7.
4. **"srmech.h exports no tool-registry enumerator" is FALSE.** Three exist (`srmech.h:5802/5805/5809`). The
   API-strength check was available, and has now been run.
5. **`shipped_descriptors_using_map_op: 0` was a hardcoded literal**, not a measurement
   (`_1653_t1142_fixprobe_rc444.py:294`). I verified the value **is** correct on two independent predicates (0 of 21
   descriptors contain the string `map_op`; 0 of 21 produce a dict-valued `desc['composite']`). **Make it a measurement.**
6. **The "711 probes / 48 spellings" S1 figure is wrong** — the real set is 732 (663 + 69 rows). Safe direction, but
   do not carry "711" or "48."
7. **The brief's "`srmech_dsl_chain_run.c` is the ONLY C chain file" is wrong** — there are three (§0). **A ship that
   follows the brief instead of this report patches the wrong file.**

---

## 9. ABI verdict

`SRMECH_ABI_VERSION` is **17** (`c/include/srmech.h:364`); `EXPECTED_ABI_VERSION: int = 17`
(`python/srmech/_native/__init__.py:222`). Both verified. Policy: **adding a symbol does not bump; changing the wire
format of an existing export does.** Standing precedent (v10 / v12 / v14) bumps for *contract reinterpretations* with no
signature change.

| change | ABI | why, and which direction breaks |
|---|---|---|
| **FOLD arm** (int carrier) + the `orientation_compose` body | **NO BUMP — stays 17** | `net_chirality` returns an int → `{"k":"i","v":"1"}`, a kind Python already reconstructs (verified). Stale .so + new Python → `BAD_INPUT` → pure path → correct. New .so + stale Python → stale `_chain_has_v2_forms` routes v2 chains to pure **before** calling C, so the capability is simply unreached. Neither direction misbehaves. |
| Widening `cr_dispatch`'s op table (10 → more) | **NO BUMP** | Gated both ways by `_RUN_C_OPS` / `_chain_c_eligible`. Worst case a slower pure path, never a wrong answer. |
| **MAP arm** (needs `CR_FLOAT` → `cr_desc` emits `{"k":"f", …}`) | **BUMP 17 → 18, REQUIRED** | **Verified:** `compose._reconstruct_value` accepts `{i,q,s,n,l}` and raises `ValueError: unknown chain-run value descriptor kind 'f'`, and `_run_chain_native` calls it unguarded (`compose.py:1176-1177`), so the exception **escapes the public `run_chain`**. Breaking direction: **new .so + stale Python** — ABI still matches at 17, `has_native` stays true, the .so emits `"f"`, Python raises. **The bump IS the fix**: `_native` disables the library on ABI mismatch, turning a live exception into a clean pure-path fallback. |
| LIST as a final output (`cr_desc` returns NULL for `CR_LIST` today) | **NO BUMP** | `_reconstruct_value({"k":"l","items":[…]})` → `[1]` already works (verified). ⚠️ **Emit the key `items`, not `v`.** Surface A expects `desc["items"]`; the Surface-B F1 carrier uses `{"k":"l","v":[…]}`. Copying the sibling spelling produces a `KeyError`, not a defer. |
| New `@idx` / `@bind` / `@op` namespaces accepted by `srmech_chain_spec_parse` | **BUMP** (fold into 18) | Same class as v12: an existing export returns `OK` + a new normalized shape for input that returned `BAD_INPUT` through rc444. |
| A data-aware `srmech_chain_run_arena_bytes` (map sizing) | **BUMP** — signature change | v9's ordinary kind. Fold into 18. |
| Landing all of it behind NEW symbols (`srmech_chain_run_v2`, …) | **NO BUMP** | The genuine architectural alternative; costs a second run loop to keep in parity forever. |

**Recommendation: ONE bump, not several.** Ship the fold slice and the `@op` namespace at **ABI 17**, then bump **once to
18** when the map slice lands. **This is an architecture call the srmech session owns**, not a measurement.

**Lockstep files on a bump:** `c/include/srmech.h` (`SRMECH_ABI_VERSION`) and
`python/srmech/_native/__init__.py` (`EXPECTED_ABI_VERSION`).

---

## 10. What is explicitly LEFT to the srmech session

**Nothing in this list was done here, and none of it should be inferred as done.**

### 10.1 Shipped-source edits (all forbidden to this session)

- [ ] `docs/srmech/c/src/srmech_compose.c` — form discriminator, `co_build_fold_step`, normalized fold node,
      `co_match_namespace` widening.
- [ ] `docs/srmech/c/src/srmech_compose_run.c` — `cr_run_fold`, the `orientation_compose` body entry,
      `cr_dispatch` table widening, `cr_resolve_ref` namespaces, and (map slice) `CR_FLOAT` + the explicit frame stack.
- [ ] `docs/srmech/c/include/srmech.h` — any new exports; `SRMECH_ABI_VERSION` on the map slice.
- [ ] `docs/srmech/python/srmech/cascade/compose.py` — `_spec_to_chain_dict`, `_run_ints_fit_i64`,
      `_chain_c_eligible`, `_chain_has_v2_forms`, and a **named** error for an unknown carrier kind so the next
      widening cannot reach users as a bare `ValueError`. **Observe the ordering in §6.3 — item 5 LAST.**
- [ ] `docs/srmech/python/srmech/dsl/_catalog.py` — `_COMPOSITE_OP_KEYS += ("map_op",)` (FIX-A), plus the decision on
      minting a bare data-first `seq_get` descriptor.
- [ ] `docs/srmech/python/srmech/introspect/` — the #T1145 subsequence resolve rule, and registering the 3 unregistered
      ops (a **two-sided** change: `c/src/srmech_tool_registry.c` too).

### 10.2 Ratchets and tests (`docs/srmech/python/tests/**` — untouched here)

- [ ] **`test_compose_step_form_parity`** — the missing Surface-A mirror (§7.1). **Highest value item in this report.**
- [ ] **A closed-key-set check, in the SAME COMMIT as any C grammar widening** (§8.6). Non-negotiable.
- [ ] Lift the gate spec's pytest skeleton from `notes/_1653_gate_spec_rc444.md`. **It has never run under pytest** —
      expect fixture/collection friction; keep the module-scope `_VARIANTS_CACHE`.
- [ ] Down-only CEILs: Surface-A parse rejects (**7**), run rejects (**20** variants / **18** descriptors — pick ONE
      granularity and use it consistently in the CHANGELOG), bare-C `A_run_rej` (**20**).
- [ ] Strict-zero: `unattributed` (0), `A_host_limit` (0).
- [ ] **Do NOT adopt strict-equality on `B_attested_parity_ok == 7` without a determinism check** (§7.3).
- [ ] Keep every positive control (2 in the census, 3 in the path measurement, 1 in the bare-C host). They are the whole
      difference between "C declined" and "the harness was wrong", at microsecond cost.
- [ ] Parametrize the two BYO composite guarantee tests over the op-naming keys **by execution**, so a seventh
      combinator cannot land unguarded (§4.4).
- [ ] Exempt `sha256_raw` explicitly, citing `tests/test_tool_schema_coverage.py:88`.
- [ ] Keep #T1145 **S3** as a live assertion: the 3 unregistered ops must resolve to `None` until actually registered,
      so no resolve()-tolerance change can paper over them.
- [ ] If the bare-C host becomes a shipped C test it must be named `test_srmech_*.c` (`Makefile:89` globs that pattern) —
      `cascade_explorer.c` is the standing demonstration of that failure mode — plus a Windows port (POSIX `dirent.h`)
      and a decision on the ~104 MB static arena budget in CI.

### 10.3 ABI, release, and tracker

- [ ] The **ABI 17 → 18** decision and bump (§9), in lockstep across `c/include/srmech.h` and
      `python/srmech/_native/__init__.py`.
- [ ] **CHANGELOG** entry.
- [ ] **Version SSOT — all 5 files must agree** (verified at `0.9.0rc444` today):
      `python/pyproject.toml:25`, `python/pyproject-pure.toml:21`, `python/srmech/version.py:7`,
      `c/include/srmech.h:67` (`SRMECH_VERSION_PRE "rc444"`), `c/include/srmech.h:68` (`SRMECH_VERSION "0.9.0rc444"`).
- [ ] **The rc tag** and the TestPyPI-rc-before-PyPI publish, verified in a clean venv **outside** the source tree
      (source-tree namespace shadowing will silently load `_native.py` and report `HAS_NATIVE=False` spuriously).
- [ ] **Edit gh #1653** to replace the "11 of 18 chains rejected" figure with the measured pair (§1.2), and to name
      **which grammar** its "1 of 3" applies to (§0).
- [ ] **ADR-0009 §5 ledger rows** for the three declines this work produces: C composite-op fallback (#T1143),
      C step→descriptor lookup (#T1144), and Surface-B `parallel_body`. **Where the §6a ledger physically lives is an
      OPEN question** — §6 authorizes it but says it is not implemented, and I found no ledger file in the tree. Either
      the rcN creates it or the declines have nowhere to be filed.
- [ ] Decide whether `orientation_compose` gets its own exported `srmech_cascade_*` symbol (the namespace invariant at
      `srmech.h:767` says every cascade-catalog entry ships one; ABI-additive) or stays inlined in the fold body table.

### 10.4 Open architecture questions this research cannot settle

1. Widen existing exports + one ABI bump, **or** new symbols (`srmech_chain_run_v2`) at ABI 17? (Recommendation: widen + bump once.)
2. The map arena: a data-aware `*_arena_bytes` (signature change, its own bump, caller must know `n`) **or** accept the
   measured defer boundary and file an ADR-0009 §5 row? (Only the second is cheap; only the first is parity.)
3. Is Surface-B `parallel_body` implemented this rcN or filed? (`ADR-0009 §4` does **not** exempt it, so
   "declines by design" is not currently a valid status either way.)
4. Should #1653's acceptance criterion be re-scoped or **split in two**? As written it already passes on 7 of 7 AMSC
   chains (§7.2); closing it on that evidence leaves the actual gap untouched.
5. Which decline codes does the rcN actually DRAIN, and in what order? Cheapest **per variant** is the op table
   (11 variants; 14 of 23 ops already have C symbols); cheapest **absolutely** is `@op` (1 variant, parse-only) — but
   `net_chirality` (fold) is the only chain that goes **end-to-end** in C with no wire-format change at all.

---

## 11. Reproduce everything

```bash
# environment
cd /home/skirklan/GitHub/mlehaptics/.claude/worktrees/srmech-1653-cparity/docs/srmech/python
python3 -c "import sys; sys.path.insert(0,'.'); import srmech; print(srmech.__version__, srmech.native_status())"

# the four Python measurements (each exits 0 and rewrites its own NDJSON)
python3 ../notes/_1653_step_forms_rc444.py            # 55 records; the two grammars
python3 ../notes/_1653_chain_census_rc444.py          # 20 records; the per-chain census
python3 ../notes/_1653_t1142_planted_rc444.py         # the map_op 2x2
python3 ../notes/_1653_t1142_fixprobe_rc444.py        # 3 passes x 7 cells
python3 ../notes/_1653_t1145_spellings_rc444.py       # 35 of 37
python3 ../notes/_1653_t1145_executor_probe_rc444.py  # R1/R2/R3 attribution
python3 ../notes/_1653_t1145_fix_prototype_rc444.py   # S1/S2/S3
python3 ../notes/_1653_gate_seed_rc444.py             # gate seeds
python3 ../notes/_1653_gate_controls_rc444.py         # PC-1..PC-7 must all FIRE

# the fold-arm C prototype
cd ../c && cc -std=c99 -Wall -Wextra -Wpedantic -O2 -Iinclude \
  ../notes/_1653_proto_fold.c build/libsrmech.a -o /tmp/proto_fold && /tmp/proto_fold

# the bare-C host (no Python in the process)
cd .. && cc -std=c17 -Wall -Wextra -Wpedantic -Werror -O2 -Ic/include \
   -o /tmp/barec1653 notes/_1653_barec_host_rc444.c c/build/libsrmech.a
/tmp/barec1653 python/srmech > /tmp/barec.ndjson    # 35 records; tally on stderr
ldd /tmp/barec1653                                  # must show NO libpython, NO libm
cd python && python3 ../notes/_1653_barec_host_verify_rc444.py /tmp/barec.ndjson
```

---

## 12. Artifact index (all under `docs/srmech/notes/`, all untracked)

| artifact | what it is |
|---|---|
| `_1653_PRERCN_REPORT.md` | **this report** |
| `_1653_DRAFT_PR_BODY.md` | the draft-PR body for the srmech session to finish |
| `_1653_step_forms_rc444.py` / `.ndjson` | the two grammars, per-form verdicts (55 records) |
| `_1653_chain_census_rc444.py` / `.ndjson` | per-chain census, 20 variants, 0 unattributed |
| `_1653_path_measure_rc444.py` / `.ndjson` | independent third-session re-measurement of the parse split |
| `_1653_proto_fold.c` | the FOLD arm, JPL-clean, 7/7 positive + 5/5 negative |
| `_1653_barec_host_rc444.c` | the bare-C host (libc only), 1078 lines, 30 functions |
| `_1653_barec_host_rc444.ndjson` | its 35 records (B parity 7/7) |
| `_1653_barec_host_verify_rc444.py` / `.ndjson` | independent Python cross-check, 11/11 spec hashes |
| `_1653_barec_ANOMALY_parity2_observed_once.ndjson` | **the unexplained one-off `B_attested_parity_ok = 2`** (§7.3) |
| `_1653_t1142_planted_rc444.py` / `.ndjson` | the `map_op` 2×2 with `fold_op` controls |
| `_1653_t1142_fixprobe_rc444.py` / `.ndjson` | FIX-A / FIX-B, 3 passes × 7 cells |
| `_1653_t1142_ADVERSARIAL_rc444.py` / `.ndjson` | 3-node cycle, self-cycle, sub_chain nesting |
| `_1653_t1142_fixtures/` | B-tier user descriptors loaded via `SRMECH_CASCADE_PATH` |
| `_1653_t1145_spellings_rc444.py` / `.ndjson` | the 35-of-37 primary measurement |
| `_1653_t1145_executor_probe_rc444.py` / `.ndjson` | R1 / R2 / R3 resolver attribution |
| `_1653_t1145_fix_prototype_rc444.py` / `.ndjson` | subsequence rule, S1 / S2 / S3 |
| `_1653_t1145_c_api_verify.c` | API-strength C tool-registry check |
| `_1653_gate_spec_rc444.md` | the 1303-line gate spec, §0–§9, with pytest skeleton |
| `_1653_gate_seed_rc444.py` / `.ndjson` | gate seeds, measured |
| `_1653_gate_controls_rc444.py` | PC-1…PC-7 planted-failure controls |
| `_1653_adv_*` | adversarial sweeps (the 28-definition "eleven hunt", step-form probes, bare-C verdicts) |

---

*Prepared as PRE-rcN research for gh #1653. No shipped source, tests, ABI constant, CHANGELOG, version SSOT file or
rc tag was modified. Local task IDs are written `#T1142` / `#T1143` / `#T1144` / `#T1145`; the GitHub issue is `#1653`.*

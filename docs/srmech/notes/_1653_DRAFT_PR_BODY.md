# DRAFT PR — srmech #1653 pre-rcN research: C-projection parity on the config-driven cascade surface

> **DRAFT.** This is the research + census + design half of gh #1653. The srmech session finishes it
> with its own ratchets, shipped-source edits, ABI decision, CHANGELOG, version SSOT and rc tag.
>
> **Suggested title:** `srmech #1653 pre-rcN: re-measured C-projection parity on the config-driven cascade surface (research + census + design; no shipped-source edits)`

**Notation discipline used throughout this PR:** `#1653` is the GitHub issue and `#1654` is this PR. `#T1142`,
`#T1143`, `#T1144`, `#T1145`, `#T1146`, `#T1148` are **LOCAL TASK IDs** and are always written with the `T` prefix —
they are **not** GitHub issue numbers and must never appear as bare `#1142` / `#1143` / `#1144` / `#1145` / `#1146` /
`#1148`, which would cross-link unrelated issues.

---

## What this PR delivers

Measurement and design for `#1653`, taken at **srmech 0.9.0rc444, native ABI 17 / expected 17, `has_native=True`,
`dispatching=True`**, Linux gcc. Every number below was produced by a script in this PR and re-run before writing.

- **A re-measurement of both figures `#1653` carries** (the issue flags them as ~rc435 and requiring re-measurement).
  One is confirmed, one does not reproduce. **The measurement wins; the issue text needs an edit.**
- **A per-form census** across *both* step grammars, and **a per-chain census** of all 20 declared chain variants with
  **0 UNATTRIBUTED** rejections — every one pinned to a named C source line, agreed by two independently written classifiers.
- **`#T1142` and `#T1145` re-measurements**, with fix prototypes and measured safety properties.
- **Four compiled, running C prototypes** — the **FOLD arm**, the **MAP arm**, the **op-table wedge harness** and the
  **closed-key-set validator** — all JPL Power-of-Ten measured, plus **a bare-C host that links libc only**.
- **A gate spec** (5 gates + a pinned CEIL) with **7 planted-failure controls that all fire**.
- **An ABI verdict** per change, with the breaking direction named for each.
- **(Round 2)** An **ADR-0009 §5 decline filing** (11 rows + 8 exclusions, probe-backed) and a **README capability
  audit** (24 anchored claims, 6 wrong, all shipping in the wheel).

## What this PR does NOT deliver

**No shipped source is edited.** `git status --porcelain` over `docs/srmech/python/srmech`, `docs/srmech/c/src`,
`docs/srmech/c/include`, `docs/srmech/python/tests` is **empty**. Every file added is untracked under `docs/srmech/notes/`.

Specifically **not** in this PR: any edit to `srmech/**` or `c/src/**` or `c/include/**`; any test or ratchet in `tests/**`;
the ABI 17 → 18 bump; the CHANGELOG entry; any of the 5 version SSOT files; the rc tag; the TestPyPI publish.

**Round 2 built the map arm** (it *was* specified-but-unbuilt after round 1). Every prototype remains a **standalone
file under `notes/` linking `c/build/libsrmech.a`** — none is wired into the shipped runner. The wedge harness in
particular **reimplements the run loop locally with a superset ref resolver**, so "it ran here" sizes the *math*, not
the shipped runner's acceptance.

---

## Headline results

### The structural finding: there are TWO grammars, with opposite parity shapes

**The task framing that commissioned this work named the wrong C file.** There are **three** C chain files, and
`srmech_dsl_chain_run.c:5` says so itself (*"a SIBLING interpreter to srmech_chain_run"*).

| | **SURFACE A** — `[[cascade.chain]]` | **SURFACE B** — `[[stage]]` |
|---|---|---|
| Python | `srmech/cascade/compose.py` | `srmech/dsl/_toml_chain.py` + `_chain.py` |
| C | **`c/src/srmech_compose.c`** + **`c/src/srmech_compose_run.c`** | `c/src/srmech_dsl_chain_run.c` |
| Population | **the 21 packaged cascade_catalog descriptors** (20 declared variants) | `chain().then(...)`, `srmech dsl run`, `[composite]` bodies |
| **C implements** | **1 of 3 step forms** | **5 of 6 step forms** |

`#1653` is about the config-driven cascade surface = the 21 descriptors = **Surface A**. **A ship that patches
`srmech_dsl_chain_run.c` patches the wrong file.** No single number describes both grammars, so **every ratchet must
name its surface.**

### Re-measurement vs the issue's carried figures

| Quantity | Issue (~rc435) | **Measured (rc444)** | Verdict |
|---|---|---|---|
| Surface-A step forms C implements | 1 of 3 | **1 of 3** (plain OK; map + fold `BAD_INPUT=2` at parse *and* run) | **CONFIRMED** |
| Surface-B step forms C implements | — | **5 of 6** (`parallel_body` recognised then declined) | **NEW** |
| Chains rejected, of 18 executable | **11 of 18** | **18 of 18** (20 of 20 variants) by `srmech_chain_run` | **DOES NOT REPRODUCE (+7 worse)** |
| C **parse** accept / reject | — | **11 accept / 7 reject** — 11 is an **ACCEPT** count | **NEW; explains the 11** |
| C-run-eligible variants | — | **0 of 20** | **NEW** |
| Reference namespaces | — | Python **7** / C parse **4** / C run **3** | **NEW axis** |
| Distinct ops used vs C run table | — | **47 used; 47 of 47 outside** the 10-entry table | **NEW** |
| `#T1145` dotted spellings failing `resolve()` | 32 of 35 | **35 of 37** | **GAP GREW** |
| `#T1142` `map_op` composite guarantees | "lapses BOTH" | **BOTH lapse** (2/2); `fold_op` control fires 2/2 | **CONFIRMED** |

**Requested edit to `#1653`.** Replace *"11 of 18 chains rejected"* with the measured pair:

> At rc444 the C run peer (`srmech_chain_run`) declines **20 of 20** declared chain variants (18 of 18 executable
> descriptors), 0 UNATTRIBUTED. The C parse peer (`srmech_chain_spec_parse`) **accepts 11** of 18 and rejects 7.

…and state **which grammar** the "1 of 3" applies to (Surface A).

**Do not ship the word "inverted" as a measurement.** Two provenance hypotheses are live (accept/reject inversion at a
17-descriptor catalog; or "chains with ≥1 `composition_of_c` op", which is exactly 11 of 18 at rc444 and matches the
denominator). Neither is verifiable without an rc435 build. Both are **inference**.

### The 7 rejected descriptors — and the two cheap wins

| descriptor | blockers |
|---|---|
| **net_chirality** | **fold ×1 — and nothing else** (its only step) |
| **parallel_sector_dispatch** | **`@op` — and nothing else** (otherwise pure plain-form) |
| autocorrelation / klein4_from_one ×2 / kuramoto_step ×2 / octonion_dft / quaternion_dft | map (1–3 each), some fold, `@idx`, `@bind` |

**`fold` + `@op` alone moves parse rejects 7 → 5**, and those are the only single-feature descriptors in the set.

### Two things that make the gap bigger than the step-form count suggests

- **A second gate, Python-side, not in the issue.** `compose._chain_c_eligible` requires `class_id == "N"` **and**
  `op in _RUN_C_OPS`. Measured **True for 0/18**, `_run_chain_native` **NATIVE_RAN 0/18**. **Widening the C op table alone
  changes nothing observable** — both projections must move in the same rc.
- **A NEW arg-marshaller wall.** `cr_json_scalar` accepts INT / NULL / STRING only; a JSON double or bool defers. So
  **widening `cr_dispatch` does not unblock the 11 parse-accepting chains** — 4 of them pass floats. The honest first
  slice is the **7 chains whose only blocker is the op table**: `cyclic_gcd`, `cyclic_mod_add`, `cyclic_mod_inv`,
  `cyclic_mod_mul`, `cyclic_mod_mul_wide`, `cyclic_mod_pow`, `encode_loe_content`.

### The missing ratchet — the structural reason this sat

Measured: `grep -rln "srmech_compose" tests/` → **nothing**; `grep -rln "_MAP_KEYS\|_FOLD_KEYS" tests/` → **nothing**.
**The tree has ZERO Surface-A form-parity ratchet**, while Surface B has
`test_combinator_kernel_closure.py::test_c_discriminator_table_matches_python`, strict both ways, whose docstring says it
exists because *"a Python-side widening (exactly like rc420's `map_op`) would leave the C peer silently deferring."*
**Surface B got that guard; Surface A never did.** Closing that asymmetry is worth more than any single arm.

### ABI verdict

| change | ABI |
|---|---|
| **FOLD arm** (int carrier) + `orientation_compose` body | **NO BUMP — stays 17** |
| Widening `cr_dispatch`'s op table | **NO BUMP** |
| **MAP arm** (needs a FLOAT carrier kind → `{"k":"f",…}`) | **BUMP 17 → 18, REQUIRED** |
| LIST as a final output | **NO BUMP** (⚠️ emit key `items`, not `v`) |
| New `@idx` / `@bind` / `@op` namespaces on `srmech_chain_spec_parse` | **BUMP** (fold into 18) |
| Data-aware `srmech_chain_run_arena_bytes` | **BUMP** (signature change; fold into 18) |

**Why the map arm forces it (verified by execution):** `compose._reconstruct_value` accepts `{i,q,s,n,l}` and raises
`ValueError: unknown chain-run value descriptor kind 'f'`, and `_run_chain_native` calls it unguarded, so the exception
**escapes the public `run_chain`**. The breaking direction is **new .so + stale Python**: ABI still matches at 17,
`has_native` stays true, the .so emits `"f"`, Python raises. **The bump IS the fix** — `_native` disables the library on
ABI mismatch, turning a live exception into a clean pure-path fallback.

**Recommendation: ONE bump.** Ship fold + `@op` at ABI 17; bump once to **18** when the map slice lands.

---

## Definition-of-done checklist (1:1 with the 8 items in `#1653`)

> The issue's 8 DoD items are mapped below in the order they appear in `#1653`. Where the item's wording differs from
> the heading used here, the srmech session should re-title but keep the mapping. `[x]` = delivered in this PR;
> `[ ]` = left to the srmech session.

### 1. Re-measure the carried ~rc435 figures at the current rc — `[x] DELIVERED`

Both figures re-measured; one confirmed, one contradicted; delta reported in both directions.
- `docs/srmech/notes/_1653_step_forms_rc444.py` → `_1653_step_forms_rc444.ndjson` (55 records)
- `docs/srmech/notes/_1653_chain_census_rc444.py` → `_1653_chain_census_rc444.ndjson` (20 records)
- `docs/srmech/notes/_1653_path_measure_rc444.py` → `.ndjson` (independent third re-measurement of the parse split)
- Written up in `docs/srmech/notes/_1653_PRERCN_REPORT.md` §1
- `[ ]` **Left to srmech:** editing the issue body itself to replace the stale figure and name the grammar.

### 2. Per-step-form census of the C projection — `[x] DELIVERED`

Surface A: plain **executes**, map **unrecognised**, fold **unrecognised** — attributed to `co_build_step`
(`srmech_compose.c:299-303`) and `cr_run_steps` (`srmech_compose_run.c:722-724`). Surface B: 5 of 6 execute,
`parallel_body` declines at `srmech_dsl_chain_run.c:791-793`. Step instances: **plain 115, map 14, fold 5**.
- `docs/srmech/notes/_1653_step_forms_rc444.py` / `.ndjson`

### 3. Per-chain census with every rejection attributed — `[x] DELIVERED`

20 of 20 variants attributed, **0 UNATTRIBUTED**, by two independently written classifiers that agree on all 20.
2 positive controls prove the harness (C parse rc=0, C run rc=0, byte-identical to pure). Index-preserving per-step
isolation confirms every *plain* step in all 9 rejecting variants parses `rc=0`.
- `docs/srmech/notes/_1653_chain_census_rc444.py` / `.ndjson`
- **Caveat that must survive into the issue:** `byte_identical = 0` is **VACUOUS**, not a mismatch count — C ran no
  Surface-A chain, so there was nothing to compare. Never report it as "0 divergences found."

### 4. `#T1142` — `map_op` missing from `_COMPOSITE_OP_KEYS` — `[x] MEASURED / [ ] FIX LEFT TO SRMECH`

`[x]` Confirmed at rc444 by execution: **both** composite load-time guarantees lapse for `map_op` (unknown-op AND cycle),
while the `fold_op` control fires on the identical planted defects. Plus four findings the issue does not carry:
the lapse admits a **contract-forbidden** dotted-body composite as a live, running op; the cycle lapse degrades to
**`RecursionError`**, not a named error; **0 of 21** bare catalog ops are usable as a `map_op` body, so FIX-A leaves
`map_op` undeclarable until a bare data-first op is minted; and the `[[cascade.chain]]` axis has **no load-time
validation for ANY key**, so the one-liner does not close the gap.
- `docs/srmech/notes/_1653_t1142_planted_rc444.py` / `.ndjson`
- `docs/srmech/notes/_1653_t1142_fixprobe_rc444.py` / `.ndjson` (3 passes × 7 cells; FIX-A sufficient, FIX-B is a contract change)
- `docs/srmech/notes/_1653_t1142_ADVERSARIAL_rc444.py` / `.ndjson`, fixtures in `_1653_t1142_fixtures/`
- `[ ]` **Left to srmech:** the one-line edit to `srmech/dsl/_catalog.py:151`; the seq_get-descriptor decision; the
  by-execution parametrized guarantee ratchet.

### 5. `#T1145` — dotted step-op spellings vs `ToolSchema.resolve()` — `[x] MEASURED / [ ] FIX LEFT TO SRMECH`

`[x]` **35 of 37** (carried: 32 of 35 — the gap grew). The new information is the **split**: **32 are a data problem**
(descriptor over-qualifies with an interior segment the flat registry drops; all 32 targets exist) and **3 are a genuine
registry gap** (`render_template`, `mint_vector`, `encode_loe_content`). Attributed to **R3 (introspection)** alone —
the executor resolves 49/49 and 98 of 98 proof cases run. A segment-subsequence rule closes all 32 (S2) while leaving the
3 unregistered ops resolving to `None` (S3 — the property that prevents papering over the real gap).
- `docs/srmech/notes/_1653_t1145_spellings_rc444.py` / `.ndjson`
- `docs/srmech/notes/_1653_t1145_executor_probe_rc444.py` / `.ndjson`
- `docs/srmech/notes/_1653_t1145_fix_prototype_rc444.py` / `.ndjson`
- `docs/srmech/notes/_1653_t1145_c_api_verify.c` (API-strength C registry check; all 32 flat names present, **no C change
  needed for the data class**)
- **Two corrections to carry:** `sha256_raw` is a **documented exemption**, not a regression
  (`tests/test_tool_schema_coverage.py:88`); and **S1 is tautological** — the rule is additive by construction, so
  "0 regressions" carries no safety information. Do not cite it as evidence. Also: the "711 probes / 48 spellings"
  figure is wrong (real: 732 / 69).
- `[ ]` **Left to srmech:** the resolve-rule edit, registering the 3 ops **on both sides** (`c/src/srmech_tool_registry.c`
  too), and the `distinct_dotted_not_resolving` 35 → 3 ratchet.

### 6. Specify the C implementation path for the missing forms — `[x] DELIVERED (BOTH arms prototyped, compiled and run)`

> **Round 2 advanced this item.** The map arm is no longer "specified only" — it is built, `-Werror`-clean and
> run, and round 1's *"60-line / 2-assert feasibility reasoned, not measured"* admission is **DISCHARGED: the
> claim HOLDS.** See the Round 2 subsection below and report §R2.1.

`[x]` Both arms specified at source-line granularity, with **both arms compiled and run**:
- `docs/srmech/notes/_1653_proto_fold.c` — builds with **zero warnings** under `-Wall -Wextra -Wpedantic`;
  **7 of 7** positive cases match `net_chirality`'s own shipped proof-case values; **5 of 5** negative controls decline
  at the stated status. **JPL clean, verified with the tree's own scanners:** 13 functions scanned, longest 38 lines,
  min 2 asserts, 0 goto, 0 malloc, 0 recursion cycles, no `abs()`, no `math.h`.
- Fold needs **no arena change** and **no ABI bump**. Three pieces to lift are named in the source
  (`pf_step_form`, `pf_fold_body`, `pf_run_fold`).
- `docs/srmech/notes/_1653_proto_map.c` (+ `_1653_proto_map_data.h`) — **the MAP arm, an explicit frame stack with
  no recursion.** Builds with **zero diagnostics** under `-Wall -Wextra -Wpedantic -Werror`; **64 of 64** crumbs of
  `klein4_from_one`'s own 19-step / 8-bind / 64-iteration map step are **bit-identical** to
  `srmech.dsl.run_cascade_chain(…)`, which itself cross-checks `True` against the shipped
  `srmech.math.hdc.klein4_from_one`; **12 of 12** negative probes decline at the stated status.
  **JPL measured with the SHIPPED ratchet's own scanner:** 45 functions, longest **37** lines (cap 60), fewest
  **2** asserts (floor 2), 0 recursion cycles, 0 allocations. Its binding constraint was **JPL Rule 1** — the
  obvious mutual-recursion implementation **fails `test_rule_1_no_new_recursion` outright** — and the explicit
  frame stack clears it with 23 lines of Rule-4 headroom.
- **Ordered plan with a measured sequencing hazard** — `_chain_c_eligible` must be widened **LAST**, because its
  isinstance guard is the only thing keeping two reachable-but-broken helpers unreached:
  `_run_ints_fit_i64` → `AttributeError: 'FoldStepSpec' object has no attribute 'args'`;
  `_spec_to_chain_dict` → `AttributeError: ... 'class_id'`. Widen the gate first and the next fold chain
  `AttributeError`s out of the public `run_chain`.
- `docs/srmech/notes/_1653_path_measure_rc444.py` / `.ndjson`; report §6
- `[ ]` **Left to srmech:** the actual `c/src` + `compose.py` edits, in the order given in report §6.3.

### 7. A gate / ratchet spec that would have caught this — `[x] SPEC DELIVERED / [ ] RATCHETS LEFT TO SRMECH`

`[x]` 5 gates + a pinned down-only CEIL, every seed measured, all 27 source anchors read back and verified, and
**7 planted-failure controls that ALL FIRE** while the unperturbed predicate set passes.
- `docs/srmech/notes/_1653_gate_spec_rc444.md` (1303 lines, §0–§9, includes a ready-to-lift pytest skeleton as fenced text)
- `docs/srmech/notes/_1653_gate_seed_rc444.py` / `.ndjson`
- `docs/srmech/notes/_1653_gate_controls_rc444.py` (PC-1…PC-7 all FIRE; unperturbed PASS)
- **What the gate CANNOT detect, stated plainly** (report §8.6): it detects the **REGRESSION, never the original**;
  **G2 is green at 0-of-20 C coverage** so green means *fully attributed*, not *parity achieved*; **G4 is vacuous at its
  seed** (`0 == 0`); and **NO gate here covers REJECTION parity** — see item 8.
- `[ ]` **Left to srmech:** lifting the skeleton into `tests/` (**it has never run under pytest**), the
  `test_compose_step_form_parity` mirror, and the CEIL/strict-zero ratchets.

### 8. Rejection parity / closed-key-set finding — `[x] DELIVERED (as a REQUIREMENT on the rcN)`

**Both C parsers are required-keys checks, never closed-key-set checks.** Divergence **D1 is live through the shipped
Python builder** — re-verified in this PR:

```
chain().then("magnitude", bogus=1).run(-3.5)   -> 3.5          (native arm ran)
srmech.cascade.magnitude(-3.5, bogus=1)        -> TypeError
chain().then("magnitude", max_denominator=10)  -> 3.5          (typo swallowed)
```

Three further divergences measured (`fold_args` silently dropped in the bare-C host path; a bare `map_op` body name C
accepts and Python rejects; a mixed v1+v2 Surface-A step that C parses **and runs** with the map half silently discarded
while Python raises `ChainSpecError`).

**This is a REJECTION-parity break, not a wrong-value break** — the value C returns equals the correct call's value.
Frame the fix as *"C must decline the unknown key."*

> **⚠️ Hard requirement on the rcN:** a **closed-key-set check must land in the SAME COMMIT** as any C grammar widening.
> Today the only thing preventing the mixed-form hole is `compose._chain_has_v2_forms`; teaching C a new form removes that
> guard's reason to exist. **G1–G5 stay green throughout**, so no gate in this PR will catch it.

**Round 2 turned this requirement into a compiled mechanism.** `docs/srmech/notes/_1653_proto_keyset_validator.c`
(761 lines, 16 functions) compiles clean under `gcc -std=c11 -Werror -Wall -Wextra -Wconversion -Wshadow` **and**
`clang -std=c99 -Werror`, and runs **55/55 probes green**: all **24** round-1 `#T1146` defects now
`REJECT(undeclared key)` at rc=5, **11/11** positive controls still ACCEPT, **20/20** whole-grammar rows match
their measured Python verdict. **The key names need no new artifact** — `srmech_tool_registry_find(name)->params[]`
is generated from `srmech.introspect.tool_schema` and pinned to `inspect.signature` in **both** directions by two
ratchets that both **measured green at rc444**. Cost with the entry pointer already in hand: **~66-71 ns per
validated stage**. A **25th** defect surfaced that round 1's probe set structurally could not find
(`chain().then('magnitude', x=3)` — a *real* param name of the op under test). See report §R2.4.

### Bonus (not a numbered DoD item): the bare-C host / ADR-0003 criterion — `[x] DELIVERED`

`docs/srmech/notes/_1653_barec_host_rc444.c` (1078 lines, 30 functions) builds with **zero warnings under `-Werror`** and
`ldd` shows **only libc** — no libpython, no libm. JPL clean by the tree's own scanners (longest function 59 lines, 0 goto,
0 malloc, no `abs()`, no `math.h`).

- **Surface B:** runs **7 of 7** shipped `[[catalog.operator_chain]]` chains end-to-end, parity **7/7** against each
  descriptor's own attested NDJSON row — including `friedmann_dark_fraction`, **9 steps** with a `@step[N].output`
  reference chain returning the exact rational `53000000000000137/2062800000000000137`.
- **Surface A:** **0 of 20** run. spec-parse 11 ok / 9 rej, **HOST_LIMIT 0, UNATTRIBUTED 0**.
- **Therefore `#1653`'s acceptance criterion as literally written ("load the shipped catalog and run a declared chain
  end-to-end") ALREADY PASSES at rc444.** It must be re-scoped to *"run a `[[cascade.chain]]` descriptor"* or it will be
  closed by a proof that does not address the gap.
- **MCU note:** `srmech_chain_run_arena_bytes` is dominated by `4096 * chain_len`, so a 3.5 KB chain wants ~16 MB
  (2.08 MB for `cyclic_gcd` → 16.4 MB for `klein4_from_one.wound`). *"Runs without Python"* and *"runs on a
  microcontroller"* are **not yet the same claim.**

**⚠️ One honest anomaly, preserved:** on the very first run of the freshly built host the summary reported
`B_attested_parity_ok: 2`, not 7 (`docs/srmech/notes/_1653_barec_ANOMALY_parity2_observed_once.ndjson`). The five affected
chains had **correct C values** (verified independently in Python against the same attested rows), **35 subsequent runs
and all four `-O` levels report 7/7**, instrumented `b_parity` returns 1 for all seven, and the leading hypothesis
(arena aliasing) was **tested and refuted** (`srmech_json_parse`'s footprint is 2934 bytes at offset 0, independent of
workspace size, so the two parses cannot overlap). **Status: UNEXPLAINED, non-reproducing, observed once in 36 runs.**
Consequence: **do not adopt strict-equality on `B_attested_parity_ok == 7` as a ratchet without a determinism check** —
it would have failed on my first run.

---

## Round 2 — the five open gaps, now compiled and run

Round 1 left five gaps. All five now have artifacts that **compiled and ran**. Same worktree, same
**srmech 0.9.0rc444 / ABI 17**, Linux `gcc 15.2.0`. **Still zero shipped-source edits.** Full treatment in
`docs/srmech/notes/_1653_PRERCN_REPORT.md` §R2.

Every round-2 result went through an independent adversarial verification pass. **Six load-bearing claims were
REFUTED; the refutations are what is reported below, not the original claims.**

### The decisive round-2 number

**11 of 11 wedge chains ran end-to-end in a bare-C executable** (no Python, no ctypes, no libm — `ldd` shows
libc only), from the shipped descriptor inputs, with **48 of 52 declared proof cases byte-identical to the
Python projection and 0 divergent**. Of the 23 distinct ops those chains name, **16 dispatch to `srmech_*`
exports that already exist** and **0 new math kernels were written**. The other 4 cases never reached an op —
`srmech_json_parse` rejects their `NaN`/`±Infinity` literals.

**⚠️ But this CORRECTS round 1's claim that those 11 are "blocked ONLY by the op table."** Ablating the
*shipped* `srmech_chain_run` with in-table ops only, one change at a time, three further gates fire
independently: `@step[0].output` → rc=0 but `@step[0].output[0]` → rc=2 (`srmech_compose_run.c:285`); arg
`[1,3]` → rc=0 but `[1.0,3]` → rc=2 (`:215`); and `cr_value_t` (`:92`) has no double / byte-buffer /
dense-matrix kind. **Blocker split: op-table-ONLY 6, wider carrier 5, ref grammar 2, real literal arg 1.**

> **Do not ship a table-only rc and claim the 11. Only 6 land** — the six `cyclic_*` chains, which need six
> dispatch entries over five existing exports plus one bignum composition, and whose 23 proof cases all came
> back byte-identical.

### Round 2 artifacts

| artifact | what it is | compiled | ran |
|---|---|---|---|
| `_1653_proto_map.c` + `_1653_proto_map_data.h` | **the MAP arm** — explicit frame stack, 45 functions, 1316 lines | ✅ `-Wall -Wextra -Wpedantic -Werror`, 0 diagnostics | ✅ exit 0, **64/64** crumbs bit-identical, **12/12** negatives, 0 failures |
| `_1653_wedge_optable_rc444.c` | **the op-table wedge** — bare-C harness, 44 functions, 1293 lines | ✅ 0 diagnostics | ✅ exit 0, **11/11** chains, **48/52** byte-identical, **0** divergent |
| `_1653_proto_keyset_validator.c` | **the closed-key-set gate** — 16 functions, 761 lines | ✅ gcc `-Werror -Wconversion` **and** clang `-Werror` | ✅ exit 0, **55/55** probes green |
| `_1653_adr0009_decline_list.md` + 3 scripts | **the ADR-0009 §5 filing** — 11 decline rows, 8 exclusions, 10 down-only ceilings | n/a | ✅ 3 scripts exit 0, 29 probes / 31 records |
| `_1653_readme_truth_audit.md` + `.py` / `.ndjson` | **the README capability audit** — 24 anchored claims | n/a | ✅ exit 0, deterministic 3/3 byte-identical |
| `_1653_map_frames_rc444` / `_map_groundtruth` / `_map_emit_data` / `_proto_map_jpl` / `_map_arena_law` / `_jpl_scanner_blindspot` | the map arm's six supporting measurements | n/a | ✅ all exit 0 |
| `_1653_wedge_pycheck_rc444.py` + `_1653_wedge_barec/` | the wedge's Python half + 70 fixture files | n/a | ✅ regenerates the fixture dir byte-identically |
| `_1653_adv2_*` / `_1653_adv3_*` | independent verification harnesses (ctypes, ablation probe, forced-pure parity, recounts) | ✅ where C | ✅ |

### The map arm — round 1's "reasoned, not measured" admission is DISCHARGED, and the claim HOLDS

JPL measured with **the shipped ratchet's own scanner** (`test_jpl_audit.py::_scan_functions`), not a
re-implementation: **45 functions, longest 37 lines (cap 60 → 23 lines headroom), fewest 2 asserts (floor 2),
0 recursion cycles, 0 allocations, 0 multi-line macros.** The explicit frame stack — the remedy the ratchet's
own comment names — clears Rule 1 with one function split as the only structural concession.

Positive 1 is a **real shipped map step**: `klein4_from_one.toml`'s variant-`rest` map (index 9), the catalog's
largest at **19 body steps / 8 binds / 64 iterations**, generated from the descriptor with its sha256
`85d3dbc…` baked into the header. The 64/64 match was proven non-tautological by three mutation tests
(corrupt an expected crumb → 63/64 FAIL; change a chain constant → rc=2; in-range bind mutation → 18/64 FAIL).

**Where the map arm stops, measured:** a closed 6-op body table fully covers **2 of the 14** shipped map steps
(both `klein4_from_one` variants). The other 12 each need one of 11 uncovered float-carrying composites — **the
ceiling is the FLOAT carrier kind**. And `compose._chain_has_v2_forms` also declines on any **dotted** op, so
**the map arm alone unlocks 0 of those 2 end-to-end** until the `#T1145` dotted-spelling resolver lands too.

**Three round-1 §6.2 figures corrected:** frame headroom is **2.67×** at a cap of 8, not 4× (3 frames needed;
a cap of 4 sufficed and its boundary declines cleanly); the float need is **12 of 14** maps, not 13, and it is
**data-side** (proof-case inputs) not literal-side; and there are **17** distinct map body ops, of which the
6-op table reaches 6, not "16 of which only 4 have a C symbol".

### ⚠️ The arena figure — round 1 was CLOSER than round 2's first correction

The growth **law** is solid and reproduced: `carrier_bytes ≈ PRODUCT(n_i over nested map levels) × 176`, a
**product** over runtime lengths, so the arena bound **cannot and must not** be a compile-time constant.

But round 2's first pass mis-stated the shipped helper as `128*chain_len + 128*ctx_len + 65536` and reported
shortfalls of 1× / 6× / 19× / **54×**. **That is only the helper's local `parse` term.**
`c/src/srmech_compose_run.c:677-688` returns `parse + run + writer` with `run = 4096*chain_len + 1 MiB`.
Recomputed against the full return value:

| n | full helper | measured need | verdict |
|---|---|---|---|
| 32 | 2 066 704 | 447 216 | **sufficient, 4.62× headroom** |
| 64 | 2 080 528 | 989 936 | **sufficient, 2.10× headroom** |
| 128 | 2 116 448 | 3 156 720 | short **1.49×** |
| 256 | 2 190 176 | 11 815 664 | short **5.39×** |

**Real crossover: fits through n=64, overflows from n=128.** Round 1's inherited "fits through 128, overflows
at 256" was one power of two off; round 2's replacement was four. **Do not quote 54× / 19× / 6× / 1×.** The
structural finding is unchanged — linear helper vs product need, shortfall grows with n, contract breaks on a
nested map.

### The closed-key-set validator's source-of-truth answer

**The key NAMES need no new artifact.** `srmech_tool_registry_find(name)->params[i].{name,required}` is a
`const` table generated from `srmech.introspect.tool_schema`, pinned to `inspect.signature` in **both**
directions by `test_mcp.py::test_schema_signature_alignment_no_drift` and
`test_declared_param_completeness_rc408.py` — **both measured green at rc444.** Superset ∧ subset ⇒ equality.

**⚠️ Two refutations that make the fix CHEAPER than either round claimed:**

1. **A string rule does most of the op-name → registry-name link.** The claim "no string rule derives it, 2/48"
   measured the *identity* rule. Measured over the same 48 names: `"srmech.cascade." + BASENAME` resolves
   **32 of 48**, agreeing with Python callable-identity resolution on all 32, zero disagreements. **Size the
   generated table off the ~16-name residue, not off 48.**
2. **An in-tree pattern DOES exist.** `srmech_invoke.c:1580-1594` `iv_no_extra_keys` is a live closed-key-set
   validator over the **same** generated registry with the **same** defer-on-mismatch semantics — 15 lines,
   2 asserts, JPL-clean, directly copyable. Round 1's narrower claim (none in the C **leaf** surface) stands.

**Ship the pointer-in-hand shape** (~66-71 ns/stage), not the registry-find shape — `dsl_leaf_dispatch` has
already matched the op name by `memcmp` when it would call the gate.

### ⚠️ Bonus: the JPL Rule 4/5 gate has a hole, and it is WORSE than first reported

`_scan_functions` / `_function_bodies` do not see every function in `c/src/`, so Rules 1, 4 and 5 are vacuous
on the ones they miss. Round 2's first pass reported **24 invisible, 0 would-be violations, "library is sound."**
**All four numbers were REFUTED:**

| | reported | measured |
|---|---|---|
| functions invisible to the gate | 24 | **64** |
| Rule-4 violations hiding there | 0 | **12** |
| Rule-5 violations hiding there | 0 | **2** |
| dominant cause | the `static const` skip | **the 10-line look-ahead window** |

Hand-verified with the ratchet's own metric: `srmech_q_zeilberger` **141 lines**, `srmech_q_gosper` **123**,
`srmech_graph_cycle_holonomy` **103 lines and 1 assert**. The `static const` skip is real but minor; the
dominant defect is the 10-line brace look-ahead (`test_jpl_audit.py:614-620`, mirrored at `:258-264`) —
`srmech_q_zeilberger`'s brace sits **22 lines** past its definition line. **Every one of the 12 is a
long-parameter-list function.** This cuts in the rcN's favour, but **"24 / 0 / 0 / sound" must not ship.**

**It matters here:** `srmech_compose_run.c` is the file the map arm edits, and `cr_walk_json` /
`cr_find_named_chain` are already invisible — a new `static const srmech_json_value_t *cr_something(...)`
helper lands **unchecked on all three rules.** Same class as the two blind spots `#T1148` closed at rc441.

**And one live consequence:** `wo_schur` in the wedge harness measures **61 lines** by the shipped ratchet's own
metric — one over the cap. Claim-only today (the ratchet globs `c/src`, never `notes/`), but **the point of the
prototype is that the rcN lifts it into `c/src`, and `wo_schur` cannot be lifted unchanged. Split it first.**

### ⚠️ Two defects in the README audit itself, both making it UNDER-count

1. **A fourth stale literal, in the very file `#1653` names, missed by all four audit passes.**
   `python/README.md:238` says *"**20 descriptors**, loaded at runtime by `srmech.dsl`"*; live
   `describe()["cascade_catalog"]["total"]` is **21** and there are **21** `.toml` files on disk. Present-tense,
   ships in the wheel, wrong — and it rotted from the **same commit** as the audit's own headline finding
   (`klein4_from_one` at rc438 moved total 20→21 and executable 17→18 together). `git log -L 238,238` shows the
   sentence has already rotted three times (10 → 15 → 20). **So `verdict_FALSE: 4` and the 3-site literal fix
   list both under-count.**
2. **"55/55 prose-vs-measurement checks pass" does not mean what it says.** Only **9** of the 55 read the
   document; 46 are NDJSON-vs-NDJSON. A negative control mutating **six** load-bearing prose figures still
   printed `55/55 pass, 0 FAIL`. **The anti-drift guarantee the file advertises about itself does not hold** —
   which is exactly the failure class `#1653` is about.

The audit's central structural finding is unaffected and is a **blocker on the prose fix**:
`describe()["cascade_catalog"]` exposes only `['enumerate','executable','leaf','run','status','total']` — there
is **no live value a corrected README:16 could be keyed to.** The corrected sentence and a new `c_runnable`
field are **one deliverable, not two.**

### The ADR-0009 §5 filing

`_1653_adr0009_decline_list.md` (627 lines) is written to be lifted verbatim, hashed against §5's own body
(`lines 221-237`, `sha256 fb781a79…`) so a later §5 edit **invalidates the filing rather than silently
outdating it**. **11 decline rows + 8 explicit non-decline exclusions + 10 down-only ceilings + 2 strict-zeros**,
each decline row carrying capability / present / missing / boundary (file:line, re-read live) / permanence /
why / what-closes-it / a probe id.

- **The filing has nowhere to live.** Measured over **1,181 files**: `decline_ledger` / `capability_ledger` /
  `parity_ledger` / `declines.ndjson` → **0 hits each.** `c/ROSETTA_LEDGER.md` is the recommended home.
- **`#T1146` is filed as a BUG, never a decline** — nothing declines; C *accepts* what Python *refuses*, so
  §5's predicate is unsatisfied in both directions and **§5 cannot be used to defer it.**
- **Surface-B `parallel_body` is not exempt.** `srmech_plat_has_threads()` returns **1** and the sector-dispatch
  op is public and loadable; the blocker is that the bump arena is **not thread-safe**.
- **D-10 strengthened:** `grep -c srmech_plat_ c/include/srmech.h` == **1**, and that hit is prose in a comment.
  Closing the descriptor-lookup decline means **exporting a new platform surface**, not calling an existing one.

### ABI: round 2 sharpens the verdict, and finds a stale public comment

**Still bump 17 → 18 — but the LIST output does not force it.** `srmech_compose_run.c:19` already documents
**five** kinds (`s`/`q`/`i`/`n`/**`l`**) and `compose.py:1088` already reconstructs `k == "l"` with an `items`
array; only `cr_desc` (`:670`) declines to emit it. Emitting it fills a **declared-but-unexercised branch**.

**⚠️ Fix in the same rc:** `c/include/srmech.h:3336-3338` — the *public* prototype comment on
`srmech_chain_run` — lists only **FOUR** kinds, stale against both the `.c` comment and the Python reader, and
**will mislead the rcN author into minting a bump for the wrong reason.** The same header block also ends
*"ABI-additive → `SRMECH_ABI_VERSION` stays 3"* while ABI is actually 17.

**The bump is load-bearing because of the closed-key-set half, not the map half.** On a well-formed map chain a
stale ABI-17 `.so` returns non-OK → pure path → correct answer, wrong cost. The sharp hazard: if the rcN relaxes
`compose._chain_has_v2_forms` because C can now do v2, **a stale ABI-17 `.so` returns `SRMECH_OK` with a WRONG
value, and "non-OK → defer" cannot catch an OK.** If the rcN leaves that guard untouched, the bump is
**ceremonial** (still bump-worthy by rc404 precedent). Both branches are on the record; round 2 cannot decide it.
`GENOME_FORMAT_VERSION` does not move.

### What round 2 does NOT claim

- **The wedge harness reimplements the run loop LOCALLY** with a ref resolver that is a **superset** of the
  shipped one. "It ran here" is evidence the **math** is present — **not** evidence the shipped runner accepts
  the same chains after a table-only edit. That is the entire point of the ablation.
- **The map prototype resumes `klein4_from_one` at step 9** — steps 0-8 are outside the map arm and their
  measured outputs are injected. **Those five stages are not executed in C.**
- **`PM_JSON` (the borrowed-JSON carrier) is a DESIGN PROPOSAL**, not something `cr_value_t` has; the 176
  bytes/cell constant is the prototype's carrier, not `cr_value_t`'s. **The law transfers; the constant must be
  re-measured.**
- **The triple-nested map is SYNTHETIC** (deepest shipped map is depth 2), and the keyset validator's 20 grammar
  rows are **two measurements joined by a table**, not a Python call from inside the C process.
- **The `chiral_dual` byte parity must not be generalised** — 4 small integral-valued cases; residual risk is
  Neumaier-compensated vs plain accumulation. *(Round 2's first pass attributed it to an FFT-vs-direct-sum
  divergence; **REFUTED** — numpy was removed in the rc69-rc134 carrier arc and `composites.py:606/617-625` is
  direct O(n²) on both routes. The FFT language survives only as stale prose at `srmech.h:1166` and
  `composites.py:548`.)*
- **The wedge's "2 of 2 planted divergences detected" has NO committed generating code.** The verification pass
  rebuilt the control and it holds — but as shipped the number violates
  `[[feedback_computational_provenance_discipline]]`. **Ship the control or drop the number.**
- **`_chain_c_eligible` "False for 0/18" in the decline list is INVERTED** — measured **True for 0/20**, i.e.
  False for 20/20. The conclusion is the one the real measurement supports; the number is backwards.
- **A stale line reference in the keyset design note:** `_chain.py:315-322` for `map_indexed`; the real location
  is **`_chain.py:413`**.
- **6 of the 31 decline records carry no probe id** (all 11 decline rows proper do), and **"0 stale source
  anchors" covers only the 8 anchors the guard re-reads** — the prose cites 21, all hand-checked accurate.
- **No macOS clang / Windows MSVC cell in either round.** Linux gcc/clang at ABI 17 throughout.

---

## Honest scope

Full treatment in `docs/srmech/notes/_1653_PRERCN_REPORT.md` §8. The load-bearing items:

- **Measured in this PR:** every count in the tables above; the fold prototype's build + run; the bare-C host's build,
  `ldd` and tally; the JPL scanner results on both C files; the `k="f"` `ValueError`; the D1 divergence; the three
  `FoldStepSpec` sequencing errors; `_COMPOSITE_OP_KEYS`; `_RUN_C_OPS`; the ABI constants and 5 version SSOT locations.
- **Inherited from sibling sessions, not re-run here:** the map-arena `n≥256` cliff (and its arithmetic rests on the
  arena function's **own asserted 128-byte-per-carrier bound**, so **n=256 is a LOWER bound on capacity**); the
  `#T1145` three-resolver 49-row probe; the `#T1142` fix matrix; the Rosetta bucketing (which resolves bare ops by
  **inference**, not a symbol lookup in the `.so`).
- **Inferred, explicitly not measurement:** both provenance hypotheses for the issue's "11"; **wall 4 (float/bool args)
  is a PREDICTION** read off `cr_json_scalar` — the op table fires first and masks it, so **0-of-20 is a FLOOR**;
  the map frame-stack design's JPL feasibility; and that `#T1143` / `#T1144` denote what this PR says (those IDs appear
  **nowhere in the tree**).
- **Not attempted:** no map prototype; no macOS clang or Windows MSVC cell (the bare-C host uses POSIX `dirent.h` and
  **will not compile in the Windows pedantic cell as written**); no test file run under either `#T1142` fix.
- **UNATTRIBUTED:** **zero** at chain level, in two independent classifiers. **One unattributed item exists and it is
  ours:** the one-off `B_attested_parity_ok = 2` above.
- **The seeds EXPIRE.** The catalog grew 20 → 21 descriptors between rc420 and rc444, which is very likely how the
  issue's figures went stale. **Re-run the scripts against whatever rcN ships; do not quote these numbers later.**

### Corrections this PR makes to earlier work (found by cross-checking)

1. A census attribution cites `srmech_compose_run.c:866-876`, which is inside **`srmech_catalog_run_chain`** — a
   different function. The firing parses are `:789` / `:792`. Zero numeric impact; **fix the string.**
2. `ref_namespaces_c = 4` is the **parse** count; the run resolver knows **3**. Don't size run-side work off 4.
3. The C discriminator array holds **7** strings, not 6 (the 6 is the FORM count and is correct) — a ratchet counting
   array entries reads 7.
4. *"srmech.h exports no tool-registry enumerator"* is **FALSE**; three exist (`srmech.h:5802/5805/5809`), and the
   API-strength check has now been run.
5. `shipped_descriptors_using_map_op: 0` was a **hardcoded literal**, not a measurement. The value is correct (verified
   on two predicates) — **make it a measurement.**
6. The task brief's *"`srmech_dsl_chain_run.c` is the ONLY C chain file"* is wrong — there are three.

---

## Reproduce

```bash
# environment (0.9.0rc444, ABI 17/17, catalog 21/18/3)
cd docs/srmech/python
python3 -c "import sys; sys.path.insert(0,'.'); import srmech; print(srmech.__version__, srmech.native_status())"

# the measurements (each exits 0 and rewrites its own NDJSON)
python3 ../notes/_1653_step_forms_rc444.py            # 55 records; the two grammars
python3 ../notes/_1653_chain_census_rc444.py          # 20 records; per-chain, 0 unattributed
python3 ../notes/_1653_path_measure_rc444.py          # independent parse-split re-measurement
python3 ../notes/_1653_t1142_planted_rc444.py         # the map_op 2x2 + fold_op controls
python3 ../notes/_1653_t1142_fixprobe_rc444.py        # 3 passes x 7 cells
python3 ../notes/_1653_t1145_spellings_rc444.py       # 35 of 37
python3 ../notes/_1653_t1145_executor_probe_rc444.py  # R1/R2/R3 attribution
python3 ../notes/_1653_t1145_fix_prototype_rc444.py   # S1/S2/S3
python3 ../notes/_1653_gate_seed_rc444.py             # gate seeds
python3 ../notes/_1653_gate_controls_rc444.py         # PC-1..PC-7 must ALL fire

# the FOLD-arm C prototype (7/7 positive, 5/5 negative, zero warnings)
cd ../c && cc -std=c99 -Wall -Wextra -Wpedantic -O2 -Iinclude \
  ../notes/_1653_proto_fold.c build/libsrmech.a -o /tmp/proto_fold && /tmp/proto_fold

# the bare-C host (no Python in the process)
cd .. && cc -std=c17 -Wall -Wextra -Wpedantic -Werror -O2 -Ic/include \
   -o /tmp/barec1653 notes/_1653_barec_host_rc444.c c/build/libsrmech.a
/tmp/barec1653 python/srmech > /tmp/barec.ndjson     # 35 records; tally on stderr
ldd /tmp/barec1653                                   # must show NO libpython, NO libm
cd python && python3 ../notes/_1653_barec_host_verify_rc444.py /tmp/barec.ndjson
```

---

## Left to the srmech session

Nothing below is done here. Full detail in report §10 and §R2.

**Round 2 changed the shape of this list in six ways — read these before sizing:**

1. `[ ]` **The wedge is 6 chains, not 11.** Ship the six `cyclic_*` dispatch entries as slice 1; the other five need
   `cr_value_t` widened (double / bytes / dense-matrix), `cr_resolve_ref` extended for `.output[K]`, and
   `cr_json_scalar` to admit a real literal — **three separate, individually-ablated edits.**
2. `[ ]` **The keyset validator's key NAMES need no new artifact** (`params[]` is already generated from
   `inspect.signature` and double-pinned). The new datum is the op-name → registry-name link, and a **basename string
   rule covers 32 of 48** — so the generated table is a **~16-name residue**, not 48. Copy `iv_no_extra_keys`
   (`srmech_invoke.c:1580-1594`), which already does this over the same registry.
3. `[ ]` **Split `wo_schur` before lifting the wedge harness** — it measures **61 lines** by the shipped ratchet's own
   metric, one over `RULE_4_MAX_LINES`.
4. `[ ]` **Fix `c/include/srmech.h:3336-3338`** (public comment lists 4 output kinds; there are 5) **in the same rc as
   the ABI bump**, or the bump gets minted for the wrong reason.
5. `[ ]` **Add `describe()["cascade_catalog"]["c_runnable"]` BEFORE editing README:16** — there is no live value to key
   the corrected prose to, so the field and the sentence are one deliverable. Then fix the **four** stale-literal sites
   (three `17 executable`, one `20 descriptors` at `python/README.md:238`) via the regen path, in one commit with the
   rebuild.
6. `[ ]` **File a separate item for the JPL scanner's 10-line brace look-ahead** (`test_jpl_audit.py:614-620`, mirrored
   at `:258-264`): **64** functions invisible, **12** real Rule-4 and **2** real Rule-5 violations hiding there.
   Same class as `#T1148`. **Do not report it as "24 / 0 / 0 / library is sound."**
7. `[ ]` **Decide `compose._chain_has_v2_forms`** — relaxing it makes the ABI bump load-bearing; leaving it makes the
   bump ceremonial. This research cannot make that call.

**Shipped source** — `[ ]` `c/src/srmech_compose.c` (form discriminator, `co_build_fold_step`, namespaces);
`[ ]` `c/src/srmech_compose_run.c` (`cr_run_fold`, `orientation_compose`, op table, `cr_resolve_ref`, and for map:
`CR_FLOAT` + explicit frame stack); `[ ]` `c/include/srmech.h`; `[ ]` `srmech/cascade/compose.py`
(**item 5 of the 5-edit sequence LAST** — see report §6.3); `[ ]` `srmech/dsl/_catalog.py:151` (`#T1142` FIX-A);
`[ ]` the `#T1145` resolve rule + registering 3 ops on **both** sides.

**Ratchets / `tests/**`** — `[ ]` **`test_compose_step_form_parity`** (the missing Surface-A mirror — highest-value item);
`[ ]` **the closed-key-set check, same commit as any C widening** (non-negotiable);
`[ ]` lift the gate skeleton (never run under pytest); `[ ]` down-only CEILs (parse rejects **7**, run rejects **20**
variants / **18** descriptors — **pick ONE granularity and use it consistently in the CHANGELOG**);
`[ ]` strict-zero on `unattributed` and `A_host_limit`; `[ ]` keep all positive controls;
`[ ]` **no strict-equality on `B_attested_parity_ok` without a determinism check**;
`[ ]` parametrize the BYO composite guarantee tests **by execution**; `[ ]` exempt `sha256_raw` with its citation;
`[ ]` keep `#T1145` **S3** live.

**Release** — `[ ]` the **ABI 17 → 18** decision + bump, lockstep across `c/include/srmech.h` and
`python/srmech/_native/__init__.py`; `[ ]` CHANGELOG; `[ ]` **the 5 version SSOT files**
(`python/pyproject.toml:25`, `python/pyproject-pure.toml:21`, `python/srmech/version.py:7`, `c/include/srmech.h:67`
`SRMECH_VERSION_PRE`, `c/include/srmech.h:68` `SRMECH_VERSION`); `[ ]` the rc tag + TestPyPI-first publish, verified in a
clean venv **outside** the source tree; `[ ]` **edit `#1653`** per items 1 and 8; `[ ]` **ADR-0009 §5 ledger rows** for the
three declines (`#T1143` composite-op fallback, `#T1144` step→descriptor lookup, Surface-B `parallel_body`) — and note
**where that §6a ledger physically lives is OPEN**; no ledger file exists in the tree today.

**Open architecture calls this research cannot settle** — `[ ]` widen exports + one bump vs new `*_v2` symbols;
`[ ]` data-aware arena sizing vs a filed defer boundary; `[ ]` implement or file Surface-B `parallel_body`
(**ADR-0009 §4 does not exempt it**, so "declines by design" is not currently a valid status);
`[ ]` re-scope or split `#1653`'s acceptance criterion; `[ ]` which decline codes to drain, in what order.

---

*Local task IDs: `#T1142` (map_op composite gate), `#T1143` (composite-op → descriptor chain),
`#T1144` (step → descriptor lookup), `#T1145` (dotted spellings vs `resolve()`), `#T1146` (rejection-parity /
closed-key-set), `#T1148` (the rc441 JPL scanner blind spots). GitHub issue: `#1653`. This PR: `#1654`.*

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01KpuzLCPpYag5fRffDfEmAn

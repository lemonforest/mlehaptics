# DRAFT PR — srmech #1653 pre-rcN research: C-projection parity on the config-driven cascade surface

> **DRAFT.** This is the research + census + design half of gh #1653. The srmech session finishes it
> with its own ratchets, shipped-source edits, ABI decision, CHANGELOG, version SSOT and rc tag.
>
> **Suggested title:** `srmech #1653 pre-rcN: re-measured C-projection parity on the config-driven cascade surface (research + census + design; no shipped-source edits)`

**Notation discipline used throughout this PR:** `#1653` is the GitHub issue. `#T1142`, `#T1143`, `#T1144`, `#T1145`
are **LOCAL TASK IDs** and are always written with the `T` prefix — they are **not** GitHub issue numbers and must never
appear as bare `#1142` / `#1143` / `#1144` / `#1145`, which would cross-link unrelated issues.

---

## What this PR delivers

Measurement and design for `#1653`, taken at **srmech 0.9.0rc444, native ABI 17 / expected 17, `has_native=True`,
`dispatching=True`**, Linux gcc. Every number below was produced by a script in this PR and re-run before writing.

- **A re-measurement of both figures `#1653` carries** (the issue flags them as ~rc435 and requiring re-measurement).
  One is confirmed, one does not reproduce. **The measurement wins; the issue text needs an edit.**
- **A per-form census** across *both* step grammars, and **a per-chain census** of all 20 declared chain variants with
  **0 UNATTRIBUTED** rejections — every one pinned to a named C source line, agreed by two independently written classifiers.
- **`#T1142` and `#T1145` re-measurements**, with fix prototypes and measured safety properties.
- **A compiled, running FOLD-arm C prototype** (JPL Power-of-Ten clean) and **a bare-C host that links libc only**.
- **A gate spec** (5 gates + a pinned CEIL) with **7 planted-failure controls that all fire**.
- **An ABI verdict** per change, with the breaking direction named for each.

## What this PR does NOT deliver

**No shipped source is edited.** `git status --porcelain` over `docs/srmech/python/srmech`, `docs/srmech/c/src`,
`docs/srmech/c/include`, `docs/srmech/python/tests` is **empty**. Every file added is untracked under `docs/srmech/notes/`.

Specifically **not** in this PR: any edit to `srmech/**` or `c/src/**` or `c/include/**`; any test or ratchet in `tests/**`;
the ABI 17 → 18 bump; the CHANGELOG entry; any of the 5 version SSOT files; the rc tag; the TestPyPI publish.
There is **no map-arm prototype** — the design is specified but unbuilt.

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

### 6. Specify the C implementation path for the missing forms — `[x] DELIVERED (fold prototyped; map specified only)`

`[x]` Both arms specified at source-line granularity, with the **FOLD arm compiled and run**:
- `docs/srmech/notes/_1653_proto_fold.c` — builds with **zero warnings** under `-Wall -Wextra -Wpedantic`;
  **7 of 7** positive cases match `net_chirality`'s own shipped proof-case values; **5 of 5** negative controls decline
  at the stated status. **JPL clean, verified with the tree's own scanners:** 13 functions scanned, longest 38 lines,
  min 2 asserts, 0 goto, 0 malloc, 0 recursion cycles, no `abs()`, no `math.h`.
- Fold needs **no arena change** and **no ABI bump**. Three pieces to lift are named in the source
  (`pf_step_form`, `pf_fold_body`, `pf_run_fold`).
- **The map arm is specified but NOT prototyped.** Its binding constraint is **JPL Rule 1**: the obvious mutual-recursion
  implementation **fails `test_rule_1_no_new_recursion` outright** (the sibling file's cycle is *seeded*, and the ratchet
  also fires when a seeded cycle gains a member). It must be an **explicit frame stack**.
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

Nothing below is done here. Full detail in report §10.

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
`#T1144` (step → descriptor lookup), `#T1145` (dotted spellings vs `resolve()`). GitHub issue: `#1653`.*

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01KpuzLCPpYag5fRffDfEmAn

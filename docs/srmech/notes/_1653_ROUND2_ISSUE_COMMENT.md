# Round 2 — the gap is a TABLE for the math, and NOT a table for the plumbing

Pre-rcN research round 2, on draft PR #1654. Measured at **srmech 0.9.0rc444, native ABI 17,
`has_native=True`**, Linux `gcc 15.2.0`. **Zero shipped-source edits** — every artifact is an untracked
standalone file under `docs/srmech/notes/` linking `c/build/libsrmech.a`.

Every result below went through an independent adversarial verification pass. **Six load-bearing claims were
refuted; what follows is the refuted-and-corrected version, not the first pass.**

---

## The decisive number: 11 of 11, on symbols that already exist

**All 11 wedge chains ran end-to-end in a bare-C executable** — no Python, no ctypes, **no libm** (`ldd` shows
libc only) — from the shipped descriptor inputs, with:

| | |
|---|---|
| chains that ran | **11 of 11** |
| declared proof cases **byte-identical** to the Python projection | **48 of 52** |
| divergent | **0** |
| cases blocked before any op (`srmech_json_parse` rejects `NaN`/`±Infinity`) | 4 |
| distinct ops those chains name | 23 |
| ops dispatching to `srmech_*` exports **that already exist** | **16** |
| **new math kernels written** | **0** |

The 14 `DIRECT_SYMBOL_EXISTS` figure reproduces the round-1 "14 already `c_dispatched`" count from an
**independent route** (`nm` over the 814-symbol archive vs the shipped Rosetta ledger). The parity is not a
same-kernel echo: forcing `srmech._native.HAS_NATIVE = False` and re-running all 52 cases gives 0 differences
native-vs-pure and 0 mismatches C-vs-pure. `schur_complement` case 1 reproduces a **one-ULP** accumulation
artifact, so this is a bit-level match, not a value match.

### ⚠️ But this CORRECTS round 1: the op table is NOT the only blocker

Round 1 said those 11 are "blocked ONLY by the op table". **Measured too generous.** Ablating the *shipped*
`srmech_chain_run` with chains built from **in-table ops only**, one change at a time (reproduced by an
independent from-scratch probe sharing no code):

| ablation | shipped `srmech_chain_run` |
|---|---|
| arg `@step[0].output` *(control)* | **rc=0** |
| arg `@step[0].output[0]` | **rc=2 BAD_INPUT** |
| arg `b: [1,3]` *(control)* | **rc=0** |
| arg `b: [1.0,3]` | **rc=2 BAD_INPUT** |

Four independent C-side gates, each with its line:

1. **op table** — `srmech_compose_run.c:616` `cr_dispatch` → `NOT_IMPL`
2. **ref grammar** — `srmech_compose_run.c:285`, *"only bare `.output` supported"*
3. **real-number arg** — `srmech_compose_run.c:215`, `cr_json_scalar` returns NULL for a JSON DOUBLE
4. **carrier width** — `srmech_compose_run.c:92`, `cr_value_t` has no double / byte-buffer / dense-matrix kind

**Blocker split over the 11: op-table-ONLY 6 · wider carrier 5 · ref grammar 2 · real literal arg 1.**

> **Do not ship a table-only rc and claim the 11. Only 6 land.** The cheap half is genuinely cheap: the six
> `cyclic_*` chains need six dispatch entries over five existing exports plus one bignum composition — no
> carrier change, no grammar change — and all 23 of their proof cases came back byte-identical.

---

## The MAP arm: built, and the JPL feasibility question is settled

Round 1 shipped the map arm as a specification and admitted its 60-line / 2-assert feasibility was
*"reasoned from shipped idioms, NOT measured."* **That admission is discharged: the claim HOLDS.**

`notes/_1653_proto_map.c` (1316 lines, 45 functions) is an **explicit frame stack** — the remedy the JPL
ratchet's own comment names — with no recursion anywhere. It compiles with **zero diagnostics** under
`-Wall -Wextra -Wpedantic -Werror` and runs to **exit 0**.

**JPL measured with the shipped ratchet's own scanner** (`test_jpl_audit.py::_scan_functions`), not a
re-implementation: **45 functions · longest 37 lines (cap 60) · fewest 2 asserts (floor 2) · 0 recursion
cycles · 0 allocations · 0 multi-line macros.** One function split (`pm_push_map` → `pm_frame_open`) was the
only structural concession Rule 4 forced.

What it computed:

```
POSITIVE 1 — klein4_from_one rest, its OWN map step   rc=0  peak_frames=2   64 / 64 MATCH
POSITIVE 2 — NESTED map depth 2 (autocorrelation's own body)  rc=0  peak_frames=3   16 / 16 MATCH
POSITIVE 3 — TRIPLE-nested (frame-cap boundary, synthetic)    rc=0  peak_frames=4   8 / 8 MATCH
NEGATIVE   — 12 of 12 declined at the stated status
0 failure(s)
```

Positive 1 is the catalog's **largest** map step — `klein4_from_one.toml`'s variant-`rest` map at index 9,
**19 body steps / 8 binds / 64 iterations** — generated from the descriptor (sha256 `85d3dbc…` baked into the
header), not hand-transcribed. All 64 crumbs are bit-identical to `srmech.dsl.run_cascade_chain(…)`, which
itself cross-checks `True` against the shipped `srmech.math.hdc.klein4_from_one`. Three mutation tests prove
it is a real computation: corrupt an expected crumb → 63/64 FAIL; change a chain constant → rc=2; in-range
bind mutation → 18/64 FAIL.

**Where it stops.** A closed 6-op body table fully covers **2 of the 14** shipped map steps (both
`klein4_from_one` variants). The other 12 each need one of 11 uncovered float-carrying composites — **the
ceiling is the FLOAT carrier kind**, as round 1 predicted. And `compose._chain_has_v2_forms` also declines on
any **dotted** op, so **the map arm alone unlocks 0 of those 2 end-to-end** until the `#T1145` dotted-spelling
resolver lands too.

### ⚠️ The arena figure — round 1 was closer than round 2's first correction

The growth **law** is solid: `carrier_bytes ≈ PRODUCT(n_i over nested map levels) × 176 bytes/cell` — a
**product** over runtime lengths, so the bound **cannot and must not** be a compile-time constant.

Round 2's first pass mis-stated the shipped sizing helper as `128*chain_len + 128*ctx_len + 65536` and
reported shortfalls up to **54×**. **That is only the helper's local `parse` term.**
`c/src/srmech_compose_run.c:677-688` returns `parse + run + writer`, with `run = 4096*chain_len + 1 MiB`.
Recomputed against the full return value:

| n | full helper | measured need | verdict |
|---|---|---|---|
| 32 | 2 066 704 | 447 216 | sufficient, **4.62× headroom** |
| 64 | 2 080 528 | 989 936 | sufficient, **2.10× headroom** |
| 128 | 2 116 448 | 3 156 720 | short **1.49×** |
| 256 | 2 190 176 | 11 815 664 | short **5.39×** |

**Real crossover: fits through n=64, overflows from n=128.** Round 1's inherited *"fits through 128, overflows
at 256"* was one power of two off; round 2's replacement was four. **Please do not quote 54× / 19× / 6× / 1×.**
The structural finding is unchanged — linear helper vs product need, shortfall grows with n, the helper's
contract genuinely breaks on a nested map.

---

## The closed-key-set validator, and its source-of-truth answer

`notes/_1653_proto_keyset_validator.c` (761 lines, 16 functions) compiles clean under
`gcc -std=c11 -Werror -Wall -Wextra -Wconversion -Wshadow` **and** `clang -std=c99 -Werror`, and runs
**55/55 probes green**:

- **all 24** round-1 `#T1146` defects now `REJECT(undeclared key)` at rc=5 (`NOT_IMPL` → defer to pure)
- **11/11** positive controls still ACCEPT
- **20/20** whole-grammar rows match their measured Python verdict (6 leaf, 9 fold, 2 reduce, 3 map)
- link health: **663** registry rows, 10 link rows, **0** broken links

A **25th** defect surfaced that round 1's probe set structurally could not find:
`chain().then('magnitude', x=3).run(-3.5)` → Python `TypeError: got multiple values for argument 'x'`, native
returns `3.5`. Round 1 only ever probed *bogus* kwarg names, never a **real param name of the op under test**.
Catching it requires excluding the **piped positionals**, whose count is form-dependent: leaf pipes **1**,
fold / reduce / map_indexed pipe **2**.

### **The key NAMES need no new artifact**

`srmech_tool_registry_find(name)->params[i].{name,required}` is a `const` table **generated** from
`srmech.introspect.tool_schema`, and that declaration is pinned to the live callable signature **in both
directions** by `test_mcp.py::test_schema_signature_alignment_no_drift` (declared ⊆ real) and
`test_declared_param_completeness_rc408.py` (declared ⊇ real). **Both measured green at rc444.** Superset ∧
subset ⇒ equality, so **reading `params[]` in C is reading `inspect.signature`.**

**Two refutations that make the fix CHEAPER than either round claimed:**

1. **A string rule does most of the op-name → registry-name link.** The claim *"no string rule derives it,
   2/48"* measured the *identity* rule. Measured over the same 48 descriptor-referenced op names:
   `"srmech.cascade." + BASENAME` resolves **32 of 48**, agreeing with Python callable-identity resolution on
   all 32 with **zero disagreements** (identity alone reaches 35/48). **Size the generated table off the
   ~16-name residue, not off 48.**
2. **An in-tree pattern DOES exist.** `srmech_invoke.c:1580-1594` `iv_no_extra_keys` is a live closed-key-set
   validator — *"1 iff every key of the arguments object matches a registry param name"* — over the **same**
   generated registry with the **same** defer-on-mismatch semantics. 15 lines, 2 asserts, JPL-clean,
   **directly copyable.** Round 1's narrower claim (none in the C **leaf** surface) still stands.

**Ship the pointer-in-hand shape** (~66-71 ns per validated stage), not the registry-find shape — the leaf
dispatcher has already matched the op name by `memcmp` when it would call the gate.

**Three gaps stay open and should be filed rather than papered over:** 10 of the 48 op names are class-scoped
bare names needing the step's `class` too (a generator must key on the **pair**); **3 names have no
`tool_schema` row at all** (`render_template`, `encode_loe_content`, `mint_vector`); and `fold_args`/`arg_names`
is deliberately deferred because rebinding the positionals makes the piped count data-dependent.

**Generate from what Python accepts, never from what the C matchers accept** — `dsl_map_body_is_seq_get`
matches bare `seq_get` while `lookup_cascade_op('seq_get')` raises. Feeding the generator the C names re-opens
round-1 divergence D3.

---

## ADR-0009 §5 decline filing

`notes/_1653_adr0009_decline_list.md` (627 lines) is written to be lifted verbatim, hashed against §5's own
body (`adr/0009-…md` lines 221-237, `sha256 fb781a79…`) so **a later §5 edit invalidates the filing rather
than silently outdating it**.

**11 decline rows** (9 time-boxed, 2 permanent-ish) + **8 explicit non-decline exclusions** + **10 down-only
ceilings** + 2 strict-zeros. Every decline row carries capability / present / missing / boundary (file:line,
re-read live) / permanence / why / what-closes-it / a probe id.

- **The filing has nowhere to live yet.** Measured over **1,181 files**: `decline_ledger` / `capability_ledger`
  / `parity_ledger` / `declines.ndjson` → **0 hits each.** `c/ROSETTA_LEDGER.md` is the recommended home — it
  is already a down-only debt ledger with two documented-exclusion precedents, and it mentions ADR-0009 zero
  times.
- **`#T1146` is filed as a BUG, never as a decline.** Nothing declines — C *accepts* an input Python *refuses*
  and returns a value, so §5's predicate is unsatisfied in **both** directions and **§5 cannot be used to defer
  it.** A filed decline may persist across rcs; this must not, because it is the only item that can hand a
  caller a wrong outcome instead of an error.
- **Surface-B `parallel_body` is not exempt.** `srmech_plat_has_threads()` returns **1** and the sector-dispatch
  op is public and loadable; the blocker is that the **bump arena is not thread-safe**. "Declines by design" is
  not a valid terminal status under §4.
- **Descriptor lookup is harder than it looked:** `grep -c srmech_plat_ c/include/srmech.h` == **1**, and that
  hit is prose in a comment. Closing it means **exporting a new platform surface**, not calling an existing one.

**A methodological note worth carrying:** four first-pass probes returned a decline for the *wrong reason*
(wrong ctx/carrier shapes) and each looked like a confirming measurement. They were caught only because every
probe was required to carry a **live positive control**. A control-free decline census cannot be trusted.

---

## README capability audit

`notes/_1653_readme_truth_audit.md` — **24 anchored claims: 4 FALSE, 2 MISLEADING, all 6 shipping in the
wheel** (`pyproject.toml:42` makes README.md the dynamic PyPI `long_description`).

- **README:16 carries five claims, not one.** *"a host with no Python present can … run cascades"* is **TRUE of
  Surface B and FALSE of Surface A**, and the sentence names neither grammar. Re-measured live: Surface A is
  **11/20 parse-accept, 0/20 run-accept**, `_chain_c_eligible` True for **0/20**.
- **A number has already rotted into the compiled binary.** The `srmech.dsl.run_cascade_chain` ToolEntry says
  the catalog holds **17 executable**; live is **18**. Three sites — `_tool_docs_curated.py:3834`,
  `_tool_docs.py:294`, and **`c/src/srmech_tool_registry.c`, compiled into `libsrmech`** — confirmed by a
  bare-C host reading the compiled table with no Python in the process. **One edit, one regen, one rebuild —
  not three edits.**
- **A blocker on the prose fix.** `describe()["cascade_catalog"]` exposes only
  `['enumerate','executable','leaf','run','status','total']` — **no `c_runnable`.** There is no live value a
  corrected README:16 could be keyed to, so **the corrected sentence and a new `describe()` field are one
  deliverable, not two**, or the rot simply recurs.

**⚠️ Two defects in the audit itself, both making it under-count:**

1. **A fourth stale literal, in the very file this issue names, missed by all four audit passes.**
   `python/README.md:238` reads *"(**20 descriptors**, loaded at runtime by `srmech.dsl` …)"*; live
   `describe()["cascade_catalog"]["total"]` is **21** and there are **21** `.toml` files on disk. It rotted
   from the **same commit** as the audit's headline finding (`klein4_from_one` at rc438 moved total 20→21 and
   executable 17→18 together) — the audit caught one half of that event and missed the other. `git log -L
   238,238` shows the sentence has already rotted three times (10 → 15 → 20).
2. **"55/55 prose-vs-measurement checks pass" does not mean what it says.** Only **9** of the 55 read the
   document; 46 are NDJSON-vs-NDJSON. A negative control mutating **six** load-bearing prose figures still
   printed `55/55 pass, 0 FAIL`. The anti-drift guarantee that file advertises about itself does not hold —
   which is precisely the failure class this issue is about.

---

## ⚠️ Bonus: the JPL Rule 4/5 gate has a hole, and it is worse than first reported

Found while measuring, not looked for. `_scan_functions` / `_function_bodies` do not see every function in
`c/src/`, so Rules 1, 4 and 5 are **vacuous** on the ones they miss. Round 2's first pass reported 24 invisible
functions, 0 would-be violations, "the library is sound." **All four of those were refuted:**

| | reported | measured |
|---|---|---|
| functions invisible to the gate | 24 | **64** |
| Rule-4 violations hiding there | 0 | **12** |
| Rule-5 violations hiding there | 0 | **2** |
| dominant cause | the `static const` skip | **the 10-line brace look-ahead** |

Hand-verified with the ratchet's own metric (definition line → closing brace, `RULE_4_MAX_LINES = 60`):

```
c/src/srmech_q_zeilberger.c   srmech_q_zeilberger          L293-433 = 141 lines
c/src/srmech_q_gosper.c       srmech_q_gosper              L491-613 = 123 lines
c/src/srmech_laplacian.c      srmech_graph_cycle_holonomy  L857-959 = 103 lines, 1 assert  ← also Rule 5
```

The `static const` skip (`test_jpl_audit.py:258`, `:614`) is real but minor. The dominant defect is the
**10-line look-ahead window** for the opening brace (`:614-620`, mirrored at `:258-264`): any function whose
parameter list pushes the brace more than 10 lines past the definition line is **never registered**.
`srmech_q_zeilberger`'s brace sits **22 lines** past its definition. Every one of the 12 is a
long-parameter-list function.

**This cuts in the rcN's favour, but "24 / 0 / 0 / library is sound" must not ship.** And it is not academic:
`srmech_compose_run.c` is the file the map arm edits, and `cr_walk_json` / `cr_find_named_chain` are already
invisible — a new `static const srmech_json_value_t *cr_something(...)` helper would land **unchecked on all
three rules**. Same class as the two blind spots `#T1148` closed at rc441.

**One live consequence:** `wo_schur` in the wedge harness measures **61 lines** by the shipped ratchet's own
metric, one over the cap. Claim-only today (`_C_SRC_DIR` is `c/src`; the ratchet never globs `notes/`) — but
the point of the prototype is that the rcN lifts it into `c/src`. **Split it first.**

---

## ABI: still bump 17 → 18, but sharpen the reason

**The LIST output does not force it.** `srmech_compose_run.c:19` already documents **five** kinds
(`s`/`q`/`i`/`n`/**`l`**) and `compose.py:1088` already reconstructs `k == "l"` with an `items` array; only
`cr_desc` (`:670`) declines to emit it — *"CR_LIST as a final output is not produced by shipped ops"*. Emitting
it fills a **declared-but-unexercised branch**.

**⚠️ Fix in the same rc:** `c/include/srmech.h:3336-3338` — the *public* prototype comment on
`srmech_chain_run` — lists only **FOUR** kinds, stale against both the `.c` comment and the Python reader, and
**will mislead whoever mints the bump into doing it for the wrong reason.** The same header block also ends
*"ABI-additive → `SRMECH_ABI_VERSION` stays 3"* while ABI is 17.

**The bump is load-bearing because of the closed-key-set half, not the map half.** On a well-formed map chain
a stale ABI-17 `.so` returns non-OK → pure path → correct answer, wrong cost (the rc404 shape). The sharp
hazard: round 1 measured that C's parse **accepts** a step carrying *both* a plain skeleton and map/fold keys
and **silently discards** the v2 half. The only thing preventing that today is `compose._chain_has_v2_forms`,
whose entire reason to exist is that C cannot do v2. **If the rcN relaxes that guard because C now can, a stale
ABI-17 `.so` returns `SRMECH_OK` with a WRONG value — and "non-OK → defer" cannot catch an OK.**

Stated honestly: if the guard stays untouched, no stale lib can produce a wrong answer and the bump is
**ceremonial** (still bump-worthy by rc404 precedent). This research cannot make that call.
`GENOME_FORMAT_VERSION` does not move.

---

## What round 2 does NOT claim

- **The wedge harness reimplements the run loop locally**, with a ref resolver that is a **superset** of the
  shipped one. "It ran here" is evidence the **math** is present — **not** evidence the shipped runner accepts
  the same chains after a table-only edit. That is the entire point of the ablation section.
- **The map prototype resumes `klein4_from_one` at step 9.** Steps 0-8 (`render_template` / `utf8_encode` /
  `sha256_bytes` / `str_concat` / `seq_get`) are outside the map arm; their measured outputs are injected.
  **Those five stages are not executed in C.**
- **`PM_JSON`, the borrowed-JSON carrier that removes both the per-iteration table copy and the only place a
  JSON→carrier conversion would want to recurse, is a DESIGN PROPOSAL** — `cr_value_t` has no such kind. If the
  rcN copies instead of borrowing, the arena numbers are optimistic by a large factor. Likewise the 176
  bytes/cell constant is the prototype's carrier size, not `cr_value_t`'s: **the law transfers, the constant
  must be re-measured.**
- **The triple-nested map is SYNTHETIC** — the deepest shipped map is depth 2.
- **The keyset validator's 20 grammar rows** are two measurements joined by a table, not a Python call from
  inside the C process. That is why the parity ratchet must re-run the `#T1146` census **as a test**, with the
  control cell non-empty so a validator that rejects everything cannot pass it.
- **`chiral_dual`'s byte parity must not be generalised** — 4 small integral-valued cases. *(Round 2's first
  pass attributed the risk to an FFT-vs-direct-sum divergence; **refuted** — numpy left in the rc69-rc134
  carrier arc and both routes are direct O(n²). The FFT language survives only as stale prose at
  `srmech.h:1166` and `composites.py:548`. The advice stands; the mechanism was wrong.)*
- **The wedge's "2 of 2 planted divergences detected" has no committed generating code.** The verification pass
  rebuilt the control and it holds — but as shipped that number is unreproducible from the deliverable. **Ship
  the control or drop the number.**
- **`_chain_c_eligible` "False for 0/18" in the decline list is inverted** — measured **True for 0/20**. The
  conclusion is the one the real measurement supports; the number is backwards.
- **No macOS clang or Windows MSVC cell in either round.** Linux gcc/clang at ABI 17 throughout.
- **Every seed EXPIRES.** This is an rc444 snapshot. The catalog grew 20 → 21 descriptors between rc420 and
  rc444, which is very likely how this issue's own figures went stale. **Re-run the scripts against whatever
  rcN ships.**

---

## Recommended order for the rcN

1. **Add `describe()["cascade_catalog"]["c_runnable"]`** (derivable from the shipped `_chain_c_eligible` gate),
   then correct README:16 keyed to it, then fix the **four** stale-literal sites via the regen path in one
   commit with the rebuild.
2. **Slice 1 — the six `cyclic_*` chains.** Six dispatch entries over five existing exports plus one bignum
   composition. No carrier change, no grammar change, no ABI bump.
3. **The closed-key-set check must land in the SAME COMMIT as any C grammar widening.** Copy
   `iv_no_extra_keys`; ship the pointer-in-hand shape; generate the ~16-name link residue from what **Python**
   accepts. The parity ratchet (re-running the `#T1146` census with a non-empty control) lands with it, not after.
4. **Slice 2 — the fold arm and `@op`** (round 1: prototyped, 7/7 positive, 5/5 negative, no ABI bump), with
   `_chain_c_eligible` widened **LAST** per report §6.3.
5. **Slice 3 — the map arm**, with `CR_FLOAT`, `@idx`/`@bind` on **both** parser and runner, the borrowed-JSON
   carrier, the data-aware arena decision, and the ABI 17 → 18 bump. **Sequenced after `#T1145`**, or it unlocks
   nothing end-to-end.
6. **File separately:** the JPL scanner's 10-line brace look-ahead (64 invisible, 12 + 2 real violations); the
   3 op names with no `tool_schema` row; and the ADR-0009 §5 ledger's physical home.
7. **Then edit this issue** — round 1 already showed the *"11 of 18 chains rejected"* figure does not reproduce
   (measured: **11 accepted / 7 rejected** on parse, **20 of 20 declined** on run), and the *"1 of 3 step
   forms"* figure needs to name **Surface A**.

---

<details>
<summary>Round-2 artifacts (all untracked under <code>docs/srmech/notes/</code>)</summary>

| artifact | compiled | ran |
|---|---|---|
| `_1653_proto_map.c` + `_1653_proto_map_data.h` — the MAP arm, 45 functions | `-Werror -Wpedantic`, 0 diagnostics | exit 0, 64/64, 12/12, 0 failures |
| `_1653_wedge_optable_rc444.c` — the bare-C wedge harness, 44 functions | 0 diagnostics | exit 0, 11/11 chains, 48/52 byte-identical |
| `_1653_proto_keyset_validator.c` — the closed-key-set gate, 16 functions | gcc `-Werror -Wconversion` **and** clang `-Werror` | exit 0, 55/55 |
| `_1653_adr0009_decline_list.md` + `_verify` / `_rows` / `_check` scripts | n/a | 3 scripts exit 0 |
| `_1653_readme_truth_audit.md` / `.py` / `.ndjson` | n/a | exit 0, deterministic 3/3 |
| `_1653_map_frames` / `_map_groundtruth` / `_map_emit_data` / `_proto_map_jpl` / `_map_arena_law` / `_jpl_scanner_blindspot` | n/a | all exit 0 |
| `_1653_wedge_pycheck_rc444.py` + `_1653_wedge_barec/` (70 fixtures) | n/a | regenerates the fixture dir byte-identically |

Full treatment in `docs/srmech/notes/_1653_PRERCN_REPORT.md` §R2 (round 1 is §0-§12, untouched apart from
four one-line pointers where a "not measured" admission is now discharged).

</details>

*Local task IDs are written `#T1142` / `#T1145` / `#T1146` / `#T1148` — they are session task IDs, not GitHub
issue numbers. This is issue #1653; the research PR is #1654.*

---

## ⚠️ Verification addendum — the decisive number was NOT reproducible from the artifacts as first written

Re-run independently after round 2 completed, and this needs to be on the record because it is a defect in the *deliverable*, not in the result:

**Round 2 shipped two halves that never met.** `_1653_wedge_optable_rc444.c` runs and prints `C_VALUE <json>` per case; `_1653_wedge_pycheck_rc444.py` writes the inputs and the NDJSON. **Nothing ever ingested the C harness's stdout.** Consequences, all measured:

- every C-side field in `_1653_wedge_optable_rc444.ndjson` is `null` — `byte_identical: null`, `c_value_spelling: null`
- the Python half prints **`DECISIVE: 0 of 11 wedge chains ran … 0 byte-identical`** on a fresh run
- the run order (`pycheck` → compile → C harness) was undocumented, and the C harness takes its input directory as `argv[1]`, defaulting to `.`

**`_1653_wedge_join_rc444.py` is that missing join**, and with it the number is now measured rather than asserted:

```
TOTALS  cases=52  c_ran=48  BYTE_IDENTICAL=48  DIVERGENT=0  ingest_rejected=4  python_raised=0
chains: total=11  every_case_ran=9  any_case_ran=11
```

**The round-2 claim HOLDS** — all 11 wedge chains run in bare C, and **every one of the 48 cases that ran is byte-identical to the Python projection, with 0 divergent.** The 4 non-runners are rejected by `srmech_json_parse` on a non-finite literal before any op executes.

**Three false divergences were produced by the joiner itself before that number settled**, and they are recorded because each is a trap for whoever writes the real gate:

| apparent divergence | actual cause |
|---|---|
| 7 cases "Python raised" | the *joiner's* serializer, not the projection — `bytes` and `Mat` are not JSON-serializable |
| 4 `encode_loe_content` divergences | **spelling**: C prints lowercase hex, the joiner had normalised `bytes` to a list of ints. `0x32→50`, `0x3a→58` — same bytes |
| 4 `encode_loe_content` divergences, again | **JSON quoting only** — identical 2048-char hex, `equal_ignoring_quotes=True` |

> A parity gate that does not normalise carrier spelling will report false divergences on exactly these three shapes. That is a requirement on the rcN's gate, not a footnote.

**Still not reproducible without manual steps:** the `pycheck → compile → C harness → join` order must be run in sequence, and `_1653_wedge_pycheck_rc444.py`'s own `DECISIVE: 0 of 11` line is misleading when read alone — it reports the state *before* the C half runs. `_1653_wedge_join_rc444.py` supersedes it for the parity claim.

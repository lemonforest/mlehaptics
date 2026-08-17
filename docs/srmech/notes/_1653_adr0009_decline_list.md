# gh #1653 — the ADR-0009 §5 FILED DECLINE LIST

**Definition-of-done item 7.** #1653 states that ADR-0009 §5 forbids an *unfiled* decline, and that
the current state IS an unfiled decline. Item 7 closes when the gap is closed **or** every residual
is a **filed, enumerated** decline with a stated reason.

**This document is that filing.** It is written to be lifted verbatim into ADR-0009 §6a (or into
gh #1653) by the session that ships the rcN.

**Measured at srmech `0.9.0rc444`, native ABI 17 / expected 17, `has_native=True`,
`dispatching=True`, Linux gcc.** Every row carries a probe id whose measurement is in
`notes/_1653_adr0009_decline_verify.ndjson` (31 records, 0 stale source anchors).

```bash
cd docs/srmech/python
python3 ../notes/_1653_adr0009_decline_verify.py   # exit 0 — 31 measured records
python3 ../notes/_1653_adr0009_decline_rows.py     # exit 0 — the rows, machine-readable
python3 ../notes/_1653_adr0009_decline_check.py    # exit 0 — 55/55, prose vs measurement
```

**The prose in this file is checked against its own measurements.**
`_1653_adr0009_decline_check.py` asserts every figure below against the NDJSON that produced it and
fails on drift — **re-run it after any edit to this document**, including edits made while lifting it
into the ADR. A decline list whose numbers have drifted from its measurements is a comment, which is
the exact artifact §5 forbids.

**Zero shipped source was edited to produce this.** Verified: `git status --porcelain` over
`docs/srmech/python/srmech`, `docs/srmech/c/src`, `docs/srmech/c/include`,
`docs/srmech/python/tests` is empty.

---

## 1. The standard — ADR-0009 §5, quoted verbatim

Source: `docs/srmech/adr/0009-multi-implementation-parity-capability-is-the-invariant.md`,
**lines 221–237**, 1145 characters, `sha256 = fb781a7930f1c7f0fcecd1e7cc965114b9f039499805bde24bc6cfec0c448f02`
(probe **P1**; the hash is over the extracted section body so a later edit to §5 invalidates this
filing rather than silently outdating it).

> ## 5. Decision — a clean decline is a correct FAILURE MODE, not parity
>
> An implementation that declines an input the other implementation serves **does not have the
> capability for that domain**. The decline being clean, typed, non-crashing, and well-tested is
> required (ADR-0003 §2.1, ADR-0006 §2.6) and is **never sufficient**.
>
> **Every such decline files a tracked gap** — a ledger row (§6a) recording the capability, the
> declining implementation, and the boundary. "It declines cleanly, the other path works" is a
> statement about the quality of the decline, and is not a parity argument.
>
> This applies **even when the decline is fully and accurately documented**. rc280's
> `section_counts` (§1.2) documents its ceiling, its corpus shortfall, its non-reentrancy, and the
> signature change that would remove it — and the gap is still open, because a changelog entry is
> not a tracked gap. **Disclosure is necessary and is not sufficient.** A build-time lever
> (`SRMECH_GENOME_SC_ARENA_BYTES`) that a caller *could* raise is likewise not parity: parity is a
> property of what the implementation serves as shipped, not of what a recompile could reach.

**The three mandated row fields**, verified present in that text by probe **P1**
(`all_mandated_present = true`):

1. **the capability**,
2. **the declining implementation**,
3. **the boundary**.

Plus four requirements §5 imposes on the *form* of the filing, each also verified present:

| §5 requirement | Consequence for this document |
|---|---|
| "files a tracked gap" | a row, not prose attached to code |
| "a ledger row (§6a)" | a ledger row, **not a source comment** |
| "Disclosure is necessary and is not sufficient" | a CHANGELOG entry does not discharge a row |
| "not of what a recompile could reach" | a build-time lever (arena size, `-D` flag) is not parity |

And the row shape §6a asks for, quoted verbatim (ADR-0009 lines 251–258):

> **(a) A capability-rooted ledger.** Re-key the Rosetta ledger from a Python symbol to a
> **capability**, with a set of implementations present and a set missing:
> `capability → {implementations present} / {missing}`.

---

## 2. Where the rows physically live — an OPEN question the rcN must settle

**§6a authorizes the capability-rooted ledger and explicitly does not implement it, and nothing in
the tree implements it either.** Measured (probe **P2**, **1,181** files scanned across
`python/srmech`, `c/`, `python/tests`):

| token searched | hits |
|---|---|
| `decline_ledger` / `DECLINE_LEDGER` | **0** |
| `capability_ledger` / `CAPABILITY_LEDGER` | **0** |
| `parity_ledger` / `PARITY_LEDGER` | **0** |
| `declines.ndjson` / `decline_rows` | **0** |

Files whose name contains "ledger": `c/ROSETTA_LEDGER.md`, `python/tests/example_args_ledger.ndjson`.

**`c/ROSETTA_LEDGER.md` is the closest in-tree precedent and it is the recommended home.** Measured
properties (P2): it *is* a down-only debt ledger; it is **keyed by Python-op bucket** (the §1.3
mechanism-2 defect ADR-0009 names); it already carries **two documented-exclusion precedents** —
the "adapters IO-exclusion (rc218 — the one deliberate walk exclusion)" and the "Do-not-mirror gate
— known Python bugs" table; and it mentions **ADR-0009 zero times** and the phrase
`declining implementation` **zero times**.

So the rcN has three options and must pick one **in the same commit as any C grammar widening**:

- **(i)** a new `## ADR-0009 §5 filed declines` section in `c/ROSETTA_LEDGER.md`, following the
  do-not-mirror-gate table shape — cheapest, inherits an existing reviewed document, but stays
  prose (nothing asserts it);
- **(ii)** a committed `python/tests/parity_declines.ndjson` + a ratchet that asserts every row's
  boundary still declines and that no *unledgered* decline exists — the only option that makes §5
  mechanical, and the only one that can catch a **stale** row (a decline that was closed but whose
  row was never deleted);
- **(iii)** both: (ii) as the machine-checked SSoT, with (i) as its human-readable rendering.

**Recommendation: (iii).** §5's own diagnosis is that candour without tracking fails; a prose-only
filing reproduces exactly the failure mode ADR-0009 §1.3 mechanism 4 describes.

---

## 3. The rcN baseline this residual is measured against

A residual list is meaningless without stating what closes first. Rows below are tagged with the
slice that closes them, using the ordering measured in `notes/_1653_PRERCN_REPORT.md` §6.3.

| slice | content | ABI | rows it closes |
|---|---|---|---|
| **S1** | Surface-A `fold` arm + the `orientation_compose` body | 17 (no bump) | **D-2** |
| **S2** | the `@op` reference namespace | 17 | part of **D-4** |
| **S3** | Surface-A `map` arm: explicit frame stack + `CR_FLOAT` + `@idx`/`@bind` | **17 → 18** | **D-1**, rest of **D-4**, **D-5** |
| **S4** | widening `cr_dispatch`'s op table | 17 | part of **D-3** |
| **—** | not scheduled | — | **D-6 … D-11** |

**If the rcN ships only S1+S2+S4, rows D-1, D-4(partial), D-5 stay filed and are the largest
residual.** If it ships S3 too, they are struck and the residual is D-3 (the long tail of ops
without a C kernel) plus D-6…D-11. **Strike a row only when its probe flips**, never on intent.

---

## 4. THE FILED DECLINE LIST

Eleven rows. Each is a capability one projection realizes and the other does not, with a measured
boundary. `SC` = scripting-coherency implementation (`python/srmech`); `CC` = compiled-coherency
implementation (`c/src`, `c/include`).

| id | capability | present | **missing** | decline | closes in |
|---|---|---|---|---|---|
| **D-1** | run a Surface-A `map` step (`map_over`/`body`/`index`/`bind`) | SC | **CC** | TIME-BOXED | S3 |
| **D-2** | run a Surface-A `fold` step (`fold_class`/`fold_op`/`fold_init`/`over`) | SC | **CC** | TIME-BOXED | S1 |
| **D-3** | run a step whose op has no C kernel (16 of 20 body ops; 32 of 47 chain ops) | SC | **CC** | TIME-BOXED, per-op | S4+ |
| **D-4** | resolve `@idx` / `@bind` / `@op` references | SC | **CC** | TIME-BOXED | S2, S3 |
| **D-5** | thread a non-integer scalar through a chain step | SC | **CC** | TIME-BOXED | S3 |
| **D-6** | resolve `@catalog` at RUN (C parses it, C run cannot resolve it) | SC | **CC** | TIME-BOXED | unscheduled |
| **D-7** | ingest a `chain_schema_version = 2` **catalog document** | SC | **CC** | TIME-BOXED | unscheduled |
| **D-8** | read a descriptor carrying a non-finite TOML float | SC | **CC** | TIME-BOXED | unscheduled |
| **D-9** | run a chain whose static arena demand exceeds the host budget | SC | **CC** | **PERMANENT-BY-DESIGN**, boundary movable | unscheduled |
| **D-10** | resolve a step or composite op **by descriptor lookup** (`#T1143`, `#T1144`) | SC | **CC** | **PERMANENT PENDING ADR** | requires an ADR |
| **D-11** | run a Surface-B `parallel_body` sector fan-out | SC | **CC** | TIME-BOXED | unscheduled |

---

### D-1 — Surface-A `map` step form

- **Capability.** Execute a `[[cascade.chain.steps]]` step of the MAP form: iterate `map_over`,
  bind each element to `bind`, expose the position as `index`, run the `body` step list per element.
- **Present in:** SC — `python/srmech/cascade/compose.py:662-719`.
- **Missing from:** CC.
- **Boundary (measured, probe P3).** `srmech_chain_spec_parse` → `SRMECH_ERR_BAD_INPUT=2`;
  `srmech_chain_run` → `SRMECH_ERR_BAD_INPUT=2`. Attribution: `co_build_step`
  (`c/src/srmech_compose.c:299`, anchor re-read live) hard-requires `class`+`op`+`args`, none of
  which a map step carries; `cr_run_steps` (`c/src/srmech_compose_run.c:722`) demands a STRING `op`.
  Positive control in the same harness: the plain form parses **and runs** `OK=0` and returns
  `{"d":"6","k":"q","n":"5"}`, so this is the grammar declining, not the harness.
- **Why declined — three coupled technical reasons, not difficulty.**
  1. **JPL Rule 1.** A map body is a step list, so the natural implementation is mutual recursion
     between the step runner and the body runner. `tests/test_jpl_audit.py`'s
     `test_rule_1_no_new_recursion` is strict on any cycle outside `RULE_1_RECURSION_SEEDED` —
     verified to hold exactly **9** cycles, one of which is precisely
     `("dsl_run_combinator", "dsl_run_loop", "dsl_run_stage_array")`, the cycle a map arm modelled
     on the sibling interpreter would join. An existing cycle that *gains a member* fails the same
     test, so `srmech_dsl_chain_run.c` is prior art **to read, not to copy**, and the map arm must
     be an explicit frame stack. Shipped bounds that size it (probe **P16**): max map nesting
     depth **2**, max body length **19**.
  2. **The run carrier has no float kind.** `cr_kind_t` is `{CR_NONE, CR_INT, CR_STR, CR_RATIONAL,
     CR_LIST}` (probe **P5**, `has_float_kind = false`), and the shipped maps need one. Measured
     over the **14** map step instances (predicate stated, because the number moves with it):
     **4 of 14** carry a float *literal inside the map subtree*, and **12 of 14** sit in a variant
     whose *proof-case inputs* carry a float — so on either reading the majority of the map
     population is float-coupled. Adding `CR_FLOAT` makes `cr_desc` emit `{"k":"f",…}`, which the scripting side
     rejects: `compose._reconstruct_value({"k":"f"})` → `ValueError: unknown chain-run value
     descriptor kind 'f'` (measured, P5b). **That is what forces ABI 17 → 18** — the bump converts
     a live exception on a stale-Python/new-`.so` pairing into a clean pure-path fallback.
  3. **Arena shape.** The run arena is linear in the chain-JSON length (`4096*chain_len + 1 MiB`,
     `c/src/srmech_compose_run.c:677-688`); a nested map's carrier count is quadratic in the mapped
     length. *(The quadratic crossover figure in the round-1 report is INHERITED and unmeasured —
     see §8. The linear-vs-quadratic shape is exact regardless, because the formula does not read
     the data.)*
- **PERMANENT or TIME-BOXED:** **TIME-BOXED** — slice S3, one ABI bump.
- **To close:** explicit frame stack (frame cap 8 gives 4× headroom over the measured depth of 2)
  + `CR_FLOAT` + `@idx`/`@bind` in both `co_match_namespace` and `cr_resolve_ref` + `ABI 18` +
  an arena decision (see **D-9**).

### D-2 — Surface-A `fold` step form

- **Capability.** Execute a `[[cascade.chain.steps]]` step of the FOLD form: seed `fold_init`, fold
  `fold_op` over `over`.
- **Present in:** SC — `compose.py:722-770`. **Missing from:** CC.
- **Boundary (probe P3).** parse `BAD_INPUT=2`, run `BAD_INPUT=2`, same two anchors as D-1.
  `net_chirality.default` is the only shipped variant whose step 0 is a fold, so it is the only one
  whose rejection is attributed to the fold gate rather than masked by the op table.
- **Why declined.** Nothing structural — a fold has no body step list, so it adds **zero** recursion
  cycles and does **not** move the arena contract. Its only real cost is that
  `net_chirality`'s `fold_op` is `srmech.cascade.leaves.orientation_compose`, for which no C symbol
  exists; it is a two-line composition over one that does (`orientation == 0 → 0`, the **Class-K
  pin-slot** absorbing zero, else `srmech_cascade_reorient_i64`, **Class C**).
- **PERMANENT or TIME-BOXED:** **TIME-BOXED, first slice.** A standalone prototype
  (`notes/_1653_proto_fold.c`) already exists, and **it was rebuilt and re-run in this pass**:
  `cc -std=c99 -Wall -Wextra -Wpedantic -O2` against `c/build/libsrmech.a` — zero warnings, exit 0,
  **7 of 7** positive cases MATCH `net_chirality`'s own shipped proof-case values, **5 of 5**
  negative controls decline at the stated status (mixed v1+v2 → `rc=2`; unknown body op / float
  `fold_init` / `@bind` in `over` / `fold_args` present → `rc=5`), `0 failure(s)`.
- **To close:** S1 — five coordinated edits in the order given in `_1653_PRERCN_REPORT.md` §6.3
  (`_chain_c_eligible` **last**, because it is the only thing keeping two fold-unaware helpers
  unreached).

### D-3 — steps whose op has no compiled kernel

- **Capability.** Execute the named cascade op inside a chain step, in-process, with no scripting
  runtime.
- **Present in:** SC (all of them). **Missing from:** CC (the subset below).
- **Boundary (measured).**
  - Probe **P10**: `cr_dispatch`'s table holds **10** ops, all Class-N
    (`atan/cos/exp/log1p/sin_series_truncate`, `pi_cascade_digits`,
    `rational_add/div/mul/pow_uint`). The 18 executable descriptors name **47** distinct ops;
    **47 of 47 are outside the table**; **15** of those 47 carry a `c_dispatched` row in
    `python/tests/rosetta_classification.ndjson`, so **32 have no attributable C symbol at all**.
  - Probe **P16**: of the **20** distinct map/fold **body** ops the descriptors name, **4** have a
    plausible C symbol in `c/include/srmech.h` and **16 do not**.
  - Probe **P16** (Surface B): **8 of 21** catalog names appear anywhere in
    `c/src/srmech_dsl_chain_run.c`'s tables; **5 of 18** executable descriptors do.
- **Why declined.** This is a real absence of the kernel, not a grammar gap: each missing op needs
  its own C implementation plus a differential parity test. **This row is the one that must not be
  collapsed into the grammar rows** — widening the op table changes the *attribution* of many
  rejections without changing the count, because the op gate currently fires at step 0 and masks
  every downstream gate.
- **PERMANENT or TIME-BOXED:** **TIME-BOXED, per op.** The 47/20/16 counts are the down-only
  ceilings; each landed kernel decrements one.
- **To close, cheapest first (probe P18).** **7** shipped variants have the op table as their
  **only** C-side blocker — no map, no fold, no unknown namespace, no float:
  `cyclic_gcd`, `cyclic_mod_add`, `cyclic_mod_inv`, `cyclic_mod_mul`, `cyclic_mod_mul_wide`,
  `cyclic_mod_pow`, `encode_loe_content` (all `.default`). **The gap is the table, not the math** —
  re-verified by ctypes in this pass, in the same loaded library that declines the `cyclic_gcd`
  chain: `srmech_gcd(12,18)` → `rc=0, out=6` and `srmech_cascade_cyclic_gcd_u64(12,18)` →
  `rc=0, out=6`.

### D-4 — the `@idx` / `@bind` / `@op` reference namespaces

- **Capability.** Resolve a step-argument reference in those three namespaces.
- **Present in:** SC — `compose._REFERENCE_PATTERN` knows **7**
  (`bind|catalog|idx|input|op|row|step`). **Missing from:** CC.
- **Boundary (probe P4).** `co_match_namespace` (`c/src/srmech_compose.c`) knows **4**
  (`row|input|step|catalog`); `cr_resolve_ref` (`c/src/srmech_compose_run.c:265-289`) knows **3**
  (`@catalog` falls through to defer). Measured, each with `@input` and `@row` as live positive
  controls that parse **and run** `OK=0`:
  | ref | C parse | C run |
  |---|---|---|
  | `@input.a` (control) | `OK=0` | `OK=0` |
  | `@row.x` (control) | `OK=0` | `OK=0` |
  | `@idx.i` | `BAD_INPUT=2` | `BAD_INPUT=2` |
  | `@bind.x` | `BAD_INPUT=2` | `BAD_INPUT=2` |
  | `@op.name` | `BAD_INPUT=2` | `BAD_INPUT=2` |
- **Why declined.** `@idx`/`@bind` are only *legal* in the scripting projection inside a map body
  (`compose.py:303-323` raises at activation for an unbound name), so they cannot land ahead of
  D-1 without inventing a semantics C would own alone. `@op` is independent and is the single
  cheapest row in this document: it is the sole blocker of `parallel_sector_dispatch` and is
  parse-reach only.
- **PERMANENT or TIME-BOXED:** **TIME-BOXED.** `@op` in S2; `@idx`/`@bind` ride S3 with D-1.
- **To close:** both matchers must move — parse 4 → 6/7 **and** run 3 → 5/6. **Do not size the
  run-side work off "4"**; that is the parse count.

### D-5 — a non-integer scalar threaded through a step

- **Capability.** Carry a float or bool step argument through the run loop.
- **Present in:** SC. **Missing from:** CC.
- **Boundary (probe P5, single-scalar attribution).** Isolated on a one-argument in-table op so the
  carrier is separated from the op's own arity:
  | `pi_cascade_digits(num_digits=…)` | C parse | C run |
  |---|---|---|
  | `5` (control) | `OK=0` | **`OK=0`**, value `{"k":"s","v":"3.14159"}` |
  | `5.0` | `OK=0` | `BAD_INPUT=2` |
  | `true` | `OK=0` | `BAD_INPUT=2` |
  | `"5"` | `OK=0` | `BAD_INPUT=2` |
  Attribution: `cr_json_scalar` (`c/src/srmech_compose_run.c:215`, anchor re-read live) returns NULL
  for ARRAY / OBJECT / **DOUBLE** / **BOOL**, so `cr_arg` yields NULL and the op returns
  `BAD_INPUT`. A float arriving through the **ctx** rather than the step literal declines
  identically (`float_via_ctx_ref` → `BAD_INPUT=2`).
- **Sizing (probe P18).** **10** of the 20 shipped variants carry at least one float in their steps
  or proof-case inputs. **4 of the 11 parse-accepting variants** carry one:
  `best_rational_signed.default`, `chiral_dual.default`, `magnitude.default`,
  `schur_complement.default`. **So widening the op table alone does not unblock those four** — this
  row survives S4 and is the reason the round-1 report calls the 0-of-20 run figure a *floor*.
- **Why declined.** Same `CR_FLOAT` / ABI-18 coupling as D-1 reason 2. Landing it without the bump
  puts a live `ValueError` in the public `run_chain` on a new-`.so`/stale-Python pairing.
- **PERMANENT or TIME-BOXED:** **TIME-BOXED**, S3.
- **To close:** `CR_FLOAT` in `cr_kind_t` + `cr_json_scalar` + `cr_desc`, a named error for an
  unknown carrier kind on the Python side, and ABI 17 → 18.

### D-6 — `@catalog` at RUN

- **Capability.** Resolve `@catalog.…` while executing a chain.
- **Present in:** SC (one of its 7 namespaces). **Missing from:** CC — **at run only.**
- **Boundary (probe P4).** `@catalog.row.x` → C **parse `OK=0`**, C **run `BAD_INPUT=2`**.
  `cr_resolve_ref` ends `return NULL;   /* @catalog or unknown → defer */`.
- **Why declined.** This is an **internal inconsistency inside one projection**, and it is the most
  quietly dangerous row here: the compiled parser **accepts and canonicalizes** a chain its own run
  loop cannot execute. No shipped descriptor uses `@catalog`, so nothing exercises it — which is
  precisely why it can sit indefinitely.
- **PERMANENT or TIME-BOXED:** **TIME-BOXED**, unscheduled.
- **To close:** either resolve `@catalog` in `cr_resolve_ref`, or **reject it at parse** so the two
  halves of the compiled projection agree. Rejecting is the cheaper and more honest fix and needs
  no new capability.

### D-7 — a `chain_schema_version = 2` catalog document

- **Capability.** Ingest a catalog-level chain document declaring schema version 2.
- **Present in:** SC — `compose.SUPPORTED_SCHEMA_VERSIONS == (1, 2)` (measured).
  **Missing from:** CC.
- **Boundary (probe P6, by execution).** `srmech_chain_catalog_parse` with `chain_schema_version=1`
  → `OK=0`; with `=2` → `BAD_INPUT=2`. The gate is `ver->u.i != 1` at **three** catalog-wrapper
  sites: `c/src/srmech_compose.c:512`, `c/src/srmech_compose.c:674`,
  `c/src/srmech_compose_run.c:867` (all three anchors re-read live).
  **All 18 executable descriptors declare `chain_schema_version = 2`** (measured, 18/18).
- **Scoping correction that must travel with this row.** The gate lives **only in the catalog
  wrappers**. `co_chain_head` does not read the field, so on the **chain-level** entry points — the
  actual peer of `compose.run_chain` — v2 is **not** a blocker: 11 of 20 v2 variants parse `OK`.
  Read as "the v2 gate blocks all 20", this row sends the rcN to fix the wrong thing.
- **Why declined.** Version acceptance is a policy decision, not a kernel: the compiled wrappers
  would have to declare which v2 *features* they implement, and today the answer is none of them
  (D-1, D-2, D-4). Widening the gate before those land would make the compiled projection accept a
  document class it then declines a step at a time.
- **PERMANENT or TIME-BOXED:** **TIME-BOXED — and deliberately sequenced AFTER D-1/D-2/D-4.**
- **To close:** widen all three sites once the v2 step forms exist, in the same rc.

### D-8 — a descriptor carrying a non-finite TOML float

- **Capability.** A host with no scripting runtime reads a shipped descriptor file.
- **Present in:** SC — Python's `tomllib` reads **21 of 21** descriptors (measured: 0 rejections).
  **Missing from:** CC — for 2 of them.
- **Boundary (probe P7, by execution over the real files plus a 3-document minimal attribution).**
  `srmech_dsl_toml_chain_to_json` accepts **19 of 21** descriptors and returns `BAD_INPUT=2` on
  `magnitude.toml` and `best_rational_signed.toml`. Attribution: `x = 1.5` → `OK=0`; `x = nan` →
  `BAD_INPUT=2`; `x = inf` → `BAD_INPUT=2`. Those two files are exactly the ones carrying
  `nan` / `inf` proof cases.
- **Why declined.** The compiled TOML front end has no representation for a non-finite float, and
  the run carrier has no float kind at all (**D-5**), so accepting the literal would produce a value
  it could not thread. **Flag for the rcN:** whether this is *also* a TOML-1.0 conformance
  shortfall is a spec question this filing does not answer — it must be checked against the
  spec text before anyone calls the decline permanent.
- **PERMANENT or TIME-BOXED:** **TIME-BOXED**, unscheduled, and coupled to D-5.
- **To close:** a non-finite representation in the TOML front end **and** in the run carrier —
  or a decision that `nan`/`inf` proof cases do not belong in a descriptor, which closes it from
  the data side instead.

### D-9 — a chain whose static arena demand exceeds the host budget

- **Capability.** Run a declared chain on a host that must pre-allocate the whole workspace.
- **Present in:** SC (no arena; Python allocates on demand). **Missing from:** CC above a
  host-dependent size.
- **Boundary (probes P11, P17).** `srmech_chain_run_arena_bytes` is dominated by `4096 * chain_len`
  where `chain_len` is the chain-JSON **byte length**. Measured demand over the 20 shipped variants:
  min **2.13 MB** (`cyclic_gcd.default`), max **17.58 MB** (`klein4_from_one.wound`). Over any
  bound the decline is **clean**: with the workspace cut to 1% and 0.1% of the demand,
  `srmech_chain_run` returns `SRMECH_ERR_OVERFLOW=4` with an empty output and no crash — and the
  same control chain still ran correctly at **10%** of the demand, so the formula is a generous
  static over-approximation rather than a measured need.
- **Why declined.** JPL Rule 3 bans malloc and the exported signature carries no data-aware sizing
  hook, so the envelope must be static and therefore conservative. **This is the exact shape of
  ADR-0009 §1.2's rc280 `section_counts` instance** — a bounded arena, an honest `OVERFLOW`, and the
  scripting path running. §5 names it directly: *"a build-time lever that a caller could raise is
  likewise not parity."* So the 17.58 MB figure is a **demand**, not a defect, and it is still a
  filed decline.
- **PERMANENT or TIME-BOXED:** **PERMANENT-BY-DESIGN as a mechanism** (a malloc-free implementation
  must bound something) with a **movable boundary**. Two honest sub-claims must not be conflated:
  *"runs without Python"* is **met** (a bare-C host runs 7 of 7 AMSC operator chains), and
  *"runs on a microcontroller"* is **not** — a 3.5 KB chain demanding ~16 MB is out of reach for an
  MCU budget.
- **To close, or narrow:** a data-aware `srmech_chain_run_arena_bytes` (a signature change, its own
  ABI bump, and the caller must then know the mapped length) — or accept the boundary and keep this
  row filed permanently. Only the first is parity; only the second is cheap.

### D-10 — resolve a step or composite op by DESCRIPTOR LOOKUP (`#T1143`, `#T1144`)

- **Capability, split in two as the issue flags them.**
  - **`#T1143`** — a composite op falling back to a descriptor's own `[[composite.stage]]` chain
    (`python/srmech/dsl/_catalog.py`, `isinstance(desc.get("composite"), dict)` →
    `_make_composite_runner`, verified present).
  - **`#T1144`** — a step referencing a descriptor by name, resolved through
    `catalog = load_catalog()` (verified present).
- **Present in:** SC. **Missing from:** CC.
- **Boundary (probe P9).** **Both require a descriptor-directory load, and the compiled projection
  has none.** Measured: `c/include/srmech.h` declares **zero** descriptor-directory loader symbols;
  the entire `srmech_catalog_*` public surface is 13 symbols
  (`lookup`, `list_chains`, `run_chain`, `registered_roots`, `local_kernel_state`,
  `use_local_kernel`, `attestation_audit`, + their `*_arena_bytes` peers), and the header's own
  state model at `c/include/srmech.h:3178` reads *"STATE MODEL (option a — caller-owned): the
  registry / kernel state is **OWNED BY THE HOST** and passed in per call"* (anchor re-read live).
- **A round-1 claim this filing CORRECTS.** The round-1 report says the raw ingredients exist, so
  *"impossible" is not an available excuse* — citing `srmech_plat_dir_*` / `srmech_plat_file_read` /
  `srmech_plat_has_filesystem`. **Measured (P8): those symbols are in the compiled library but are
  NOT in the public header** — `srmech_plat_*` appears in `c/include/srmech.h` exactly **once**, and
  that one occurrence is prose inside a comment. They are declared only in the internal
  `c/src/srmech_platform.h`. So a bare-C host has **no public API** for directory traversal, and
  closing this row means *exporting a new platform surface*, not just calling an existing one.
  `srmech_toml_parse` **is** public.
- **Why declined — three reasons, and none of them is "hard".**
  1. It **inverts the caller-owned state model** the whole rc172 catalog surface rests on. That is
     an ADR-level architecture decision, not an rc.
  2. It is a **name-resolution** capability, orthogonal to the **step-grammar** capability #1653 is
     about. Bundling them makes the grammar work unshippable.
  3. The cycle semantics it would have to mirror are **themselves defective today**: a `map_op`
     cycle reaches a `RecursionError` in the scripting projection, and the compiled equivalent of
     that is a stack overflow — a **crash, not a decline**. Mirroring would copy a defect into a
     second projection, which `c/ROSETTA_LEDGER.md`'s own "Do-not-mirror gate" already forbids.
- **PERMANENT or TIME-BOXED:** **PERMANENT PENDING AN ADR.** Not permanent-forever — permanent until
  an ADR amendment settles (a) whether the compiled projection may own filesystem-backed registry
  state, and (b) the cycle semantics both projections must share.
- **To close:** an ADR amendment on the state model, a public platform/filesystem surface in
  `srmech.h`, a descriptor loader, **and** a non-crashing cycle policy fixed on the scripting side
  first.

### D-11 — Surface-B `parallel_body`

- **Capability.** Fan a chain body out over Klein-4 sectors and recombine.
- **Present in:** SC — `python/srmech/dsl/_toml_chain.py:335-365`. **Missing from:** CC.
- **Boundary (probe P8, with two live positive controls).**
  | Surface-B stage | status |
  |---|---|
  | `{"op": "magnitude"}` (leaf control) | **`OK=0`** |
  | `{"loop_n": 3, "sub_chain": [{"op": "magnitude"}]}` (combinator control) | **`OK=0`**, value `{"k":"f","v":3.5}` |
  | `{"parallel_body": "chiral_flip", "n_sectors": 4, "combine": "bundle"}` | **`NOT_IMPL=5`** |
  Anchor `c/src/srmech_dsl_chain_run.c:792` re-read live: `return SRMECH_ERR_NOT_IMPL;` inside
  `dsl_run_combinator`, guarded by the `parallel_body` key. It is **recognised** by the
  discriminator array (7 entries) and then declined — a deliberate, typed decline, which is why it
  is a decline and not a bug.
- **Why declined — and the reason is NOT that C cannot thread.** Measured: the C sector-dispatch op
  `srmech_cascade_parallel_sector_dispatch` is in the public header **and** loadable from the
  library, and `srmech_plat_has_threads()` returns **1** on this host. The real blocker is that the
  DSL bump arena is **not thread-safe** — four sectors bump-carving one arena would race — so the
  fix is four disjoint sub-arenas, which the dispatch function's own disjoint-slice contract already
  models.
- **ADR-0009 §4 does NOT exempt this.** §4's only exemption is host-integration and
  protocol-adapter layers (`srmech.mcp` / `srmech.llm` / the `host_glue` rows); Klein-4 sector
  dispatch is neither. Per §5, *"it declines cleanly, the other path works"* is not a parity
  argument, so **"declines by design" is not a valid terminal status** — the status must become
  either *implemented* or *this filed row*.
- **PERMANENT or TIME-BOXED:** **TIME-BOXED** where `srmech_plat_has_threads() == 1`.
  **Platform-conditional and permanent where it returns 0** — a thread-less host cannot serve the
  input at all, and that half of the row can never be closed by code.
- **To close:** four disjoint sub-arenas + the recombine (`bundle`/`mean`/`sector0`/`concat`), with
  the thread-less platform arm remaining filed.

---

## 5. What is NOT a decline — and must not be filed as one

**This section is load-bearing.** A decline is a **clean, typed refusal of an input the peer
serves**. Anything that *accepts* what the peer refuses, or returns a wrong value, or is a routing
choice, is a different thing — and filing it here would grant it §5's shelter, which §5 does not
extend to it.

### 5.1 `#T1146` silent-accept divergence — a **BUG**. Do not launder it into this list.

- **Measured (probe P13, re-confirmed live at rc444).** Through the shipped Python builder,
  `chain().then("magnitude", bogus=1).run(-3.5)` → **`3.5`**, while
  `srmech.cascade.magnitude(-3.5, bogus=1)` → **`TypeError`**. Same for `reorient` and
  `net_chirality`. The round-2 census `notes/_1653_t1146_rejection_parity_rc444.ndjson` puts the
  cell counts at **24 defect probes**, `capability_gap_pure_accepts_native_rejects` **0**,
  `parity_ok_both_reject` **10**, across **5** ops
  (`autocorrelation`, `chiral_flip`, `magnitude`, `net_chirality`, `reorient`).
- **Why it is not a decline.** Nothing declines. The compiled path **accepts** an input the
  scripting path **refuses** and returns a value. §5's predicate — "an implementation that declines
  an input the other implementation serves" — is not satisfied in either direction, so §5 has
  nothing to say about it and cannot be used to defer it.
- **Why the distinction matters practically.** A filed decline is allowed to persist across rcs
  under a tracked row. **This must not.** It is the only item in this investigation that can hand a
  caller a wrong outcome — an accepted mis-specified declaration — rather than an error.
- **Root cause, read from source.** `python/srmech/dsl/_chain.py:111-124` `_then_native_desc` gates
  on **value type** (`_is_c_scalar`) and never on **key name**; `srmech_dsl_chain_run.c:537-565`
  `dsl_leaf_dispatch` has no leaf that validates its own key set. And measured: the two ops that
  *look* clean (`cyclic_gcd`, `pin_slot_at_zero`) reject only **incidentally** — the native stage
  builder declined and Python raised, identical message, `is_python_typeerror = true`. **There is no
  key-set validator anywhere in the C leaf surface**, so the rcN has no in-tree pattern to copy.
- **Consequence for sequencing.** Every C parser on both surfaces is a **required-keys** check, never
  a **closed-key-set** check. **Widening either C parser without a closed-key-set check in the same
  commit makes this strictly worse**, and no gate in the round-1 gate spec (G1–G5) fires on it,
  because all five measure what C *accepts* and none measures what it should *refuse*.

### 5.2 Not-a-decline: everything else, with the reason it is excluded

| item | why it is not a §5 row |
|---|---|
| **The `_chain_c_eligible` routing gate** (`compose.py`; measured P15: class-N gate **and** `_RUN_C_OPS` gate **and** an `isinstance` guard, all three live) | Both projections would have the capability; the **router** declines to use the compiled one. ADR-0009 §3 restricts "native dispatch" to routing language precisely so a routing fact is never read as a capability fact — the inverse holds too. It is a **sequencing hazard** (measured: `_chain_c_eligible` False for 0/18, `_run_chain_native` NATIVE_RAN 0/18, so widening C alone changes nothing observable), and it belongs in the rcN plan, not in the decline ledger. |
| **`seq_get` naming asymmetry** | **Corrected reading, measured P12.** The C map-body recogniser names `seq_get`; the DSL catalog does not (`lookup_cascade_op("seq_get")` → `ValueError: unknown cascade op`). But `srmech.cascade.seq_get` **does exist** in Python (`hasattr` → True). So this is a **registration** asymmetry about whether the NAME is addressable, not a capability either projection lacks. Round-1 framing as a compiled-only capability would have been wrong. |
| **`kuramoto_step.general`'s undeclared inputs** | The capability is absent from **neither** projection and missing from the **descriptor**: all 5 proof cases raise `KeyError: 'path element .adjacency not found'` through the public callable, and it passes CI only because `tests/test_cascade_catalog_executable_rc420.py:253-258 CASE_DEFAULTS` merges `{adjacency: None, alpha: 0.0, pin_anchor: None, pin_strength: 1.0}` under the case. A descriptor-declaration gap (TOML cannot spell `None`), not an implementation parity gap. |
| **`srmech.mcp` / `srmech.llm` / the 21 `host_glue` rows** | **Exempt by ADR-0009 §4** — host-integration and protocol-adapter layers, with no language-independent capability underneath to project. Nothing else is exempt, and a new exemption needs an ADR amendment. |
| **The bare-C host demo's POSIX `dirent.h` dependency** | `notes/_1653_barec_host_rc444.c` is a research artifact under `notes/`, not shipped source. It becomes a real portability row only if the rcN promotes it to `c/test/test_srmech_*.c`. |
| **The 22 `UNVERIFIABLE_CLAIMS` in `srmech/introspect/_c_claims.py`** (measured P14: 271 claim rows, 22 unverifiable — ADR-0009 records 23 of 263 at rc300) | Pre-existing, already tracked under a down-only ceiling, and produced by a different mechanism (static symbol attribution). Named here only so it is not double-filed. |
| **A filesystem-less host (`srmech_plat_has_filesystem() == 0`)** | Symmetric: the scripting projection cannot load descriptors without a filesystem either. No projection has a capability the other lacks. |

---

## 6. The reverse direction — a null result, stated as one

ADR-0009 §2.2 makes the oracle role symmetric, so a one-directional list would be a Python-rooted
filing of exactly the kind §1.3 mechanism 2 describes. **Searched, and found nothing to file**
(probe **P12**): no capability was located that the compiled projection realizes and the scripting
projection does not. The one candidate — `seq_get` — dissolved on measurement into a registration
asymmetry (§5.2).

**This is a null result over a narrow surface, not a clearance.** It covers the two chain grammars
and their op tables only. §6(b)'s C-host capability manifest — the thing that would make this
direction *enumerable* rather than *searched* — still does not exist, so "nothing found" here is
weaker than "nothing exists".

---

## 7. Down-only ceilings the rcN should pin, so the residual cannot grow silently

Every number below is measured at rc444 by the named probe. Without ceilings, a new descriptor can
add a new decline, get a new ledger row, and leave a row-completeness gate green while the residual
**grows** — the hole a per-row invariant cannot see.

| ceiling | rc444 value | probe |
|---|---|---|
| Surface-A chain variants the C run peer declines | **20** of 20 | P18 |
| Surface-A chain variants the C parse peer declines | **9** of 20 | P18 |
| variants whose only C-side blocker is the op table | **7** | P18 |
| parse-accepting variants that also carry a float | **4** | P18 |
| distinct chain ops outside `cr_dispatch`'s table | **47** of 47 | P10 |
| distinct chain ops with no attributable C symbol | **32** of 47 | P10 |
| distinct map/fold body ops with no C symbol | **16** of 20 | P16 |
| catalog names absent from the C DSL tables | **13** of 21 | P16 |
| descriptors the C TOML front end cannot read | **2** of 21 | P7 |
| reference namespaces the C run resolver lacks | **4** of 7 | P4 |
| **strict-zero, not a ceiling:** unledgered declines | **0** | this document |
| **strict-zero, not a ceiling:** `#T1146` silent-accept probes | **24** today → must be **0** | P13 |

Two shapes are needed, not one: a **per-row invariant** (every row's boundary still declines, and
no decline lacks a row — which also catches a **stale** row whose gap was closed) **and** these
**integer ceilings** (the residual only shrinks).

---

## 8. Honest scope — what is measured, what is inherited, what is projected

**MEASURED in this pass** (31 records, `notes/_1653_adr0009_decline_verify.ndjson`, 0 stale
anchors): the ADR §5 extraction + hash; the ledger absence; all three Surface-A step forms at parse
and run with a live plain-form control; all 7 reference namespaces with `@input`/`@row` controls;
the carrier kinds with a single-scalar attribution and an int control that returns π; the schema-
version gate by execution both ways; the TOML front end over all 21 real descriptors plus a
3-document attribution; `parallel_body` with two Surface-B controls and the threading facts; the
absence of a descriptor loader and of a public platform surface; the op-table and body-op coverage;
the arena demand over all 20 variants and its clean `OVERFLOW` under four undersized workspaces; the
`#T1146` divergence live; the per-variant residual matrix. Outside the probe script, also measured
here: `git status --porcelain` over the four shipped-source paths (**empty**); the fold prototype
rebuilt warning-free and re-run (7/7 + 5/5, `0 failure(s)`); `srmech_gcd` and
`srmech_cascade_cyclic_gcd_u64` returning 6 by ctypes; `RULE_1_RECURSION_SEEDED` holding exactly 9
cycles including the `dsl_run_combinator` triple; the `@idx`/`@bind` activation guard at
`compose.py:303-323`; and the 14 map / 5 fold step-instance counts with their float predicates.

**INDEPENDENTLY REPRODUCED from round 1** (same numbers, different script): 11 parse-accept / 9
parse-reject / 0 run-accept at variant level; 7 op-table-only variants and their exact names; 4
parse-accepting variants carrying floats; 47 distinct ops, 47 outside the table; 8 of 21 / 5 of 18
Surface-B coverage; 2 of 21 unreadable descriptors; 18 of 18 descriptors declaring schema version 2.

**INHERITED and NOT re-measured here** — flagged in-row: the map arena's quadratic crossover
(`n=128` fits, `n=256` overflows). It rests on the arena function's own asserted 128-byte
per-carrier upper bound, not a measured `sizeof`, so it is a **lower bound on capacity**. The
linear-vs-quadratic *shape* is exact.

**PROJECTED, not measured:** the map arm's explicit-frame-stack design and its 60-line / 2-assert
feasibility. Reasoned from shipped idioms. **Closing that by building it is the remaining round-2
job on D-1**, and this filing does not claim it.

**CORRECTIONS this pass produced, which the rcN should carry:**

1. **Three round-1 source anchors were off by one** and are now live-verified:
   `chain_schema_version` is at `srmech_compose.c:512` (not `:513`), `srmech_compose.c:674`
   (not `:675`), and `srmech_compose_run.c:867` (not `:868`); `cr_json_scalar`'s STRING gate is at
   `srmech_compose_run.c:215`.
2. **`srmech_plat_*` is NOT in the public header** (D-10). Round 1 implied the ingredients were
   callable; they are internal-only. This makes the D-10 decline *stronger*, not weaker.
3. **`seq_get` is not a compiled-only capability** (§5.2). `srmech.cascade.seq_get` exists.
4. **Body-op count is 20 distinct, 16 without a C symbol** on this pass's predicate (which counts
   `fold_op` at every depth); round 1 reported 16 / 12 on a narrower one. **State the predicate
   whenever this number is quoted.**
5. The arena demand for `klein4_from_one.wound` measures **17.58 MB** here vs **16.4 MB** in round 1
   — the figure moves with the chain-JSON serialization, which is what the formula reads. Quote it
   with the serializer, or quote the formula.
6. **Round 1's "13 of 14 maps need a float" does not reproduce on either predicate.** Measured:
   **4 of 14** map instances carry a float literal in the map subtree; **12 of 14** sit in a variant
   whose proof-case inputs carry one. The conclusion (the map arm is float-coupled, so it forces
   `CR_FLOAT` and the ABI bump) is unchanged and if anything better supported — but the figure must
   travel with its predicate.
7. **`parse_reject` granularity.** 9 rejections at **variant** level = 7 **descriptors**
   (`klein4_from_one` and `kuramoto_step` each declare two variants). The CHANGELOG and any ceiling
   must pick one granularity and hold it; mixing them is how "11 of 18" went stale.

**These seeds EXPIRE.** The catalog grew 20 → 21 descriptors between rc420 and rc444, which is very
likely how #1653's own figures went stale. Re-run the probe script before quoting any number in a
later rc.

---

## 9. Artifacts

All under `docs/srmech/notes/`. Nothing here edits shipped source.

| artifact | what it is |
|---|---|
| `_1653_adr0009_decline_list.md` | **this document** — the filing, written to be lifted verbatim |
| `_1653_adr0009_decline_verify.py` / `.ndjson` | the probe suite behind every row — **29 probe ids / 31 records**, of which 8 are source anchors re-read from disk (**0 stale**), and every C boundary is a real ctypes call on the shipped `libsrmech.so` with a live positive control |
| `_1653_adr0009_decline_rows.py` / `.ndjson` | the same rows **machine-readable** in the §6a shape — 11 decline rows + 8 not-a-decline exclusions + 10 down-only ceilings + 2 strict-zeros (**31 records**). This is the seed for §2 option (ii); the script fails if a row cites a probe the verify NDJSON does not contain |
| `_1653_adr0009_decline_check.py` | the prose-vs-measurement guard, **55/55 pass** |

**Lifting instructions for the srmech session.** §1 is the standard and should not be paraphrased.
§4 rows drop into ADR-0009 §6a (or gh #1653) as-is; strike a row **only when its probe flips**. §5
must travel with §4 — a decline list published without its not-a-decline section is how a bug becomes
a tracked gap. §7's ceilings belong in the ratchet, not the prose.

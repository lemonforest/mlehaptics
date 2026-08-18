# gh #1653 — GATE SPEC for the C-projection parity gap on the config-driven cascade surface

**Status:** DESIGN + MEASURED SEEDS. Nothing here is shipped. `tests/` was not
touched; the pytest skeleton in §5 is text in this file, to be lifted by the
session that owns the rcN.

**Measured on:** srmech `0.9.0rc444`, native ABI 17 (== expected), Linux gcc,
`docs/srmech/python/srmech/_native/libsrmech.so` from this worktree's
`c/build`. **Every number below was produced by execution on this tree**, by
`_1653_gate_seed_rc444.py` → `_1653_gate_seed_rc444.ndjson` (54 records).

**Reproduce:**

```
cd docs/srmech/python && python3 ../notes/_1653_gate_seed_rc444.py
```

Exit 0. Section `[0]` runs the two positive controls and **aborts before
recording anything** if either fails, so no verdict below can be a harness
artefact.

---

## §0 Read this first — the gate covers ONE of two surfaces

"The config-driven cascade surface" names **two grammars that share no code
and have opposite parity shapes.** A single number cannot describe both, and
the issue's carried figures do not say which one they are about. This gate is
scoped to **Surface A**, and every gate name below is prefixed accordingly.

| | **SURFACE A — `[[cascade.chain.steps]]`** | SURFACE B — `[[stage]]` |
|---|---|---|
| Python engine | `srmech/cascade/compose.py` (ADR-0002/0008, schema v1/v2) | `srmech/dsl/_toml_chain.py` + `_chain.py` |
| C peers | `srmech_chain_spec_parse` / `srmech_chain_catalog_parse` (`c/src/srmech_compose.c`); `srmech_chain_run` / `srmech_catalog_run_chain` (`c/src/srmech_compose_run.c`) | `srmech_dsl_chain_run` / `srmech_dsl_toml_chain_to_json` (`c/src/srmech_dsl_chain_run.c`) |
| Population | **the 21 packaged `cascade_catalog` descriptors → 18 executable → 20 declared chain variants** | `chain().then(...)`, `srmech dsl run`, user `[composite]` bodies |
| Step forms | 3 | 6 |
| C implements | **1 of 3** | 5 of 6 |
| Already gated? | **NO — this spec** | YES, `tests/test_combinator_kernel_closure.py` |

**Surface B is already closed and must not be re-gated.**
`test_combinator_kernel_closure.py::test_c_discriminator_table_matches_python`
reads `srmech_dsl_chain_run.c`'s `disc[7]` array and asserts strict
both-direction agreement with the Python combinator keys. That is the exact
gate shape §1 proposes — one surface over. Surface A has no such mirror, which
is why the gap sat.

> **Briefing correction the ship must carry.** The task brief for this research
> said `srmech_dsl_chain_run.c` is "the ONLY C chain file". It is not; there
> are **three** (`srmech_compose.c`, `srmech_compose_run.c`,
> `srmech_dsl_chain_run.c`), and `srmech_dsl_chain_run.c:5` says so in its own
> words ("a SIBLING interpreter to `srmech_chain_run`"). A ship that follows
> the brief instead of this spec will measure and patch the wrong file.

---

## §1 The measured seeds

All five tables are cut from `_1653_gate_seed_rc444.ndjson`.

### 1.1 Step forms — Surface A (`step_forms_python: 3`, `step_forms_c_executes: ["plain"]`)

| form | Python | C parse | C run | verdict |
|---|---|---|---|---|
| plain (`class`+`op`+`args`) | accepts, runs | `SRMECH_OK` | `SRMECH_OK` | **EXECUTES** |
| map (`map_over`+`body`[+`index`,`bind`]) | accepts, runs | `BAD_INPUT` (2) | `BAD_INPUT` (2) | **UNRECOGNISED** |
| fold (`fold_class`+`fold_op`+`fold_init`+`over`[+`fold_args`]) | accepts, runs | `BAD_INPUT` (2) | `BAD_INPUT` (2) | **UNRECOGNISED** |

**The issue's "C implements 1 of 3 step forms" is CONFIRMED for Surface A,
independently, by my own execution.** Not carried — re-measured.

### 1.2 Reference namespaces — the axis the issue does not carry

`_REFERENCE_PATTERN` (`compose.py:151-154`) admits **7**; the C parse
discriminator (`co_match_namespace`, `srmech_compose.c:135-148`) knows **4**;
the C run resolver (`cr_resolve_ref`, `srmech_compose_run.c:265-289`) knows
**3**.

| namespace | C parse | C run | verdict |
|---|---|---|---|
| `@row` | OK | OK | **EXECUTES** |
| `@input` | OK | OK | **EXECUTES** |
| `@step[N].output` | OK | OK | **EXECUTES** |
| `@catalog` | OK | `BAD_INPUT` | **PARSES_REJECTS** (`cr_resolve_ref:288` "@catalog or unknown → defer") |
| `@idx` | `BAD_INPUT` | `BAD_INPUT` | **UNRECOGNISED** |
| `@bind` | `BAD_INPUT` | `BAD_INPUT` | **UNRECOGNISED** |
| `@op` | `BAD_INPUT` | `BAD_INPUT` | **UNRECOGNISED** |

So the honest namespace figure is **4 of 7 at parse, 3 of 7 at run**. This
resolves the census's `ref_namespaces_c = 4`, which its own verify pass
correctly flagged as axis-ambiguous: 4 is the parse count and it overstates
the run side by one.

> **HARNESS ARTEFACT I HIT AND FIXED — do not repeat it.** My first pass gave
> `@row` a **PARSES_REJECTS** verdict. That was wrong and it was my harness:
> the probe ctx carried `row: null`, so `cr_resolve_ref` walked a NULL row and
> failed to resolve a *value*. The grammar was never the problem. Every
> namespace probe now supplies the carrier its reference needs
> (`FORM_PROBES` gained an explicit `row` column). One unfixed instance of
> this would have inflated the C gap by a whole namespace.

### 1.3 The chain ledger — 20 declared variants, 0 C-runnable, 0 unattributed

`declared_chain_variants: 20` · `c_runs: 0` · `c_declined: 20` ·
`c_parse_accept: 11` · `c_parse_reject: 9` · `unattributed: 0`

| primary decline code | count |
|---|---|
| `op_not_in_c_table` | **11** |
| `step_form_map` | **7** |
| `step_form_fold` | **1** |
| `ref_namespace_v2` | **1** |

The primary code is chosen by **the first C gate the control flow reaches**,
not by preference: parse before run, and inside the run loop the step-shape
check (`cr_run_steps`, `srmech_compose_run.c:722`) before the op-table check
(`cr_dispatch`, `:616`).

Note the coincidence and use it: **the 11 `op_not_in_c_table` variants are
exactly the 11 the C parse gate already ACCEPTS.** For those, widening
`cr_dispatch` is the only C-side blocker left — no new step form, no new
namespace.

### 1.4 The op table — 10 claimed, 10 confirmed dispatching, 5 negatives correctly declined

`op_table_claimed: 10` · `op_table_confirmed_dispatching: 10` ·
`op_table_claimed_but_not_dispatching: []` ·
`op_negative_controls_wrongly_dispatching: []`

`compose._RUN_C_OPS` (`compose.py:985-990`) is a Python literal claiming to
describe `cr_dispatch`. Nothing in the tree reads the C side. Measured by
execution here: all 10 dispatch, and 5 plausible non-members
(`rational_sub`, `gcd`, `mod_add`, `magnitude`,
`srmech.math.rational.rational_add` — the dotted spelling of an in-table op)
all return `NOT_IMPL` (5). The mirror is currently accurate and unpinned.

### 1.5 The schema-version axis — NEW, neither sibling census measured it

| declared `chain_schema_version` | `srmech_chain_catalog_parse` |
|---|---|
| 1 | `SRMECH_OK` (0) |
| 2 | `SRMECH_ERR_BAD_INPUT` (2) |

`co_catalog_body` (`srmech_compose.c:513`), `co_list_body` (`:675`) and
`srmech_catalog_run_chain` (`srmech_compose_run.c:868`) each hard-require
`ver->u.i == 1`. **All 20 shipped chain variants declare
`chain_schema_version = 2`.** Both sibling censuses reported
"catalog_parse agrees with spec_parse 18/18" — true, but only because each
minted its **own** wrapper with `chain_schema_version: 1`. On the real
declaration the catalog-wrapper entry points reject 20 of 20. `spec_parse`
and `chain_run` take a bare chain dict and never look at the version, which
is why the 11-accept figure survives on those two.

---

## §2 The gates

Five gates. **Four are INVARIANTS** — statements about agreement between a
declared ledger and measured behaviour, in both directions, which therefore do
not rot as counts move. **One is a pinned integer** (the CEIL) and it exists
for a specific reason stated in §2.2b.

Throughout, `variants()` means the 20 `(descriptor, variant)` pairs from
`cascade_catalog_status()` + `cascade_chain_specs()`, and `c_runs(v)` means
`srmech_chain_run` returned `SRMECH_OK` on the structure probe ctx
`{"row": null, "inputs": {}}` — which isolates the **grammar** verdict from
descriptor data, because the C run loop checks step shape and op-table
membership before resolving a single argument.

---

### G1 — SURFACE-A FORM CLOSURE (invariant, bidirectional)

**Predicate.** For every step form and every reference namespace the *Python*
engine implements, the measured C verdict must equal the verdict declared in
`SURFACE_A_FORM_LEDGER`. Bidirectional: an undeclared feature fails, and a
declared feature whose C verdict has *improved* also fails.

```
for feature in python_forms() | python_namespaces():
    assert feature in SURFACE_A_FORM_LEDGER          # no silent widening
    assert measured_verdict(feature) == SURFACE_A_FORM_LEDGER[feature].verdict
assert set(SURFACE_A_FORM_LEDGER) == python_forms() | python_namespaces()   # no stale rows
```

`python_forms()` is derived from `compose._MAP_KEYS` / `compose._FOLD_KEYS`
plus the plain form; `python_namespaces()` is parsed out of
`compose._REFERENCE_PATTERN.pattern`. **Both are read from the shipped module,
never copied**, so a Python-side widening enters the loop automatically and
fails on the missing ledger row.

`measured_verdict` is **execution**, not a regex over C source: one minimal
complete probe chain per feature, driven through the real
`srmech_chain_spec_parse` and `srmech_chain_run`.

**Seed (10 rows).**

| feature | verdict | reason (the "named, reasoned decline") |
|---|---|---|
| `form:plain` | `EXECUTES` | — |
| `form:map` | `UNRECOGNISED` | `co_build_step` hard-requires `class`+`op`+`args` (`srmech_compose.c:299-306`); a map step carries none of the three. No map arm exists in either C file. |
| `form:fold` | `UNRECOGNISED` | same required-keys check; `cr_run_steps` demands a STRING `op` (`srmech_compose_run.c:722-724`). |
| `ns:row` | `EXECUTES` | — |
| `ns:input` | `EXECUTES` | — |
| `ns:step` | `EXECUTES` | — |
| `ns:catalog` | `PARSES_REJECTS` | recognised by `co_match_namespace:147`, but `cr_resolve_ref` has no catalog arm and defers (`srmech_compose_run.c:288`). |
| `ns:idx` | `UNRECOGNISED` | v2 (rc420); `co_match_namespace:135-148` knows `row\|input\|step\|catalog` only. |
| `ns:bind` | `UNRECOGNISED` | as `ns:idx`. |
| `ns:op` | `UNRECOGNISED` | as `ns:idx`. Blocks `parallel_sector_dispatch`, otherwise an all-plain chain. |

**Failure message.**

```
SURFACE-A form parity moved and the ledger did not.
  feature      : ns:idx
  ledger says  : UNRECOGNISED
  measured     : EXECUTES  (C parse rc=0, C run rc=0)
  anchor       : c/src/srmech_compose.c:135-148 co_match_namespace

If C GAINED this feature, that is good news -- delete the ledger row in this
commit. A stale decline row silently re-opens the room it was meant to close.
If PYTHON gained a new form or namespace, C has no peer for it: either ship
the peer or add a ledger row with a REASON, in this same commit. Do not widen
one projection alone; gh #1653 is what that costs.
```

**Why this cannot rot.** It pins no count. `python_forms()` grows itself; the
C side is re-measured every run; and a decline that gets fixed fails LOUDLY
rather than sitting green. The only maintenance is deleting rows, which is the
direction we want.

---

### G2 — SURFACE-A CHAIN LEDGER CLOSURE (invariant, bidirectional)

**Predicate.** Partition the 20 declared variants into C-runnable and
declined. The declined set must equal `C_DECLINED_CHAINS` **exactly**, and
each entry's declared code must equal the measured first-gate code, and every
code must be a member of the closed `DECLINE_CODES` set.

```
measured_declined = {v for v in variants() if not c_runs(v)}
assert measured_declined == set(C_DECLINED_CHAINS)              # both directions
for v, (code, reason) in C_DECLINED_CHAINS.items():
    assert code in DECLINE_CODES                                # closed set
    assert code == measured_first_gate(v)                       # right reason
    assert reason.strip()                                       # reasoned, not blank
for v in variants() - measured_declined:
    assert c_value(v) == pure_value(v)                          # runs AND agrees
```

The last clause matters: "C-runnable" must mean **byte-identical to the pure
reference**, not merely `rc == 0`. A C path that runs and returns a different
number is worse than one that declines.

**Seed (20 rows, the full ledger, lift verbatim).**

```python
C_DECLINED_CHAINS = {
    # ---- op_not_in_c_table (11) -- C PARSE ALREADY ACCEPTS THESE.
    #      For this whole block, widening cr_dispatch is the ONLY C blocker.
    "best_rational_signed.default":     ("op_not_in_c_table", "..."),
    "chiral_dual.default":              ("op_not_in_c_table", "..."),
    "cyclic_gcd.default":               ("op_not_in_c_table", "op 'gcd'"),
    "cyclic_mod_add.default":           ("op_not_in_c_table", "op 'mod_add'"),
    "cyclic_mod_inv.default":           ("op_not_in_c_table", "op 'mod_inv'"),
    "cyclic_mod_mul.default":           ("op_not_in_c_table", "op 'mod_mul'"),
    "cyclic_mod_mul_wide.default":      ("op_not_in_c_table", "op 'mod_mul_wide'"),
    "cyclic_mod_pow.default":           ("op_not_in_c_table", "op 'mod_pow'"),
    "encode_loe_content.default":       ("op_not_in_c_table", "..."),
    "magnitude.default":                ("op_not_in_c_table", "..."),
    "schur_complement.default":         ("op_not_in_c_table", "op 'schur_complement'"),
    # ---- step_form_map (7)
    "autocorrelation.default":          ("step_form_map",     "steps[1] map"),
    "klein4_from_one.rest":             ("step_form_map",     "steps[9] map"),
    "klein4_from_one.wound":            ("step_form_map",     "steps[9] map"),
    "kuramoto_step.simple":             ("step_form_map",     "steps[2] map (nested)"),
    "kuramoto_step.general":            ("step_form_map",     "steps[2] map (nested)"),
    "octonion_dft.default":             ("step_form_map",     "steps[2], steps[6] map"),
    "quaternion_dft.default":           ("step_form_map",     "steps[1], steps[5] map"),
    # ---- step_form_fold (1)
    "net_chirality.default":            ("step_form_fold",    "steps[0] IS a fold"),
    # ---- ref_namespace_v2 (1)
    "parallel_sector_dispatch.default": ("ref_namespace_v2",  "@op. at steps[0]"),
}

DECLINE_CODES = {
    "step_form_map":          "c/src/srmech_compose.c:299-306 co_build_step; "
                              "c/src/srmech_compose_run.c:722-724 cr_run_steps",
    "step_form_fold":         "c/src/srmech_compose.c:299-306 co_build_step; "
                              "c/src/srmech_compose_run.c:722-724 cr_run_steps",
    "ref_namespace_v2":       "c/src/srmech_compose.c:135-148 co_match_namespace",
    "ref_namespace_run":      "c/src/srmech_compose_run.c:288 cr_resolve_ref",
    "op_not_in_c_table":      "c/src/srmech_compose_run.c:616 cr_dispatch "
                              "-> SRMECH_ERR_NOT_IMPL",
    "chain_schema_version_2": "c/src/srmech_compose.c:513 co_catalog_body / "
                              ":675 co_list_body (hard == 1)",
}
```

`ref_namespace_run` and `chain_schema_version_2` are in the closed set with
**zero seeded members**. That is deliberate — they are real, measured C
declines (§1.2, §1.5) that no *shipped chain variant* reaches today, and
naming them now means a chain that reaches one tomorrow gets an existing code
rather than a rushed new one.

**Failure messages.** Three distinct ones; conflating them is how this stays
unfixed.

```
[MISSING] A chain the C projection cannot run is not in the ledger.
  unledgered : <chain>.<variant>
  measured   : C run rc=<rc> (<STATUS>), first gate <code> at <anchor>
Either make it C-runnable, or add it to C_DECLINED_CHAINS with the code and a
REASON. An unattributed rejection is how a stale figure survived 95 rcs.
```

```
[STALE] A ledgered decline now RUNS in C.
  ledgered   : <chain>.<variant> as <code>
  measured   : C run rc=0, value byte-identical to pure
Delete the row in this commit. Good news must shrink the ledger or the gate
loses its teeth.
```

```
[WRONG REASON] Ledger code disagrees with the measured first C gate.
  chain      : <chain>.<variant>
  ledger     : <declared_code>
  measured   : <measured_code> at <anchor>
The gap is real but the ATTRIBUTION is wrong, and a wrong attribution mis-sizes
the fix. Re-read the C control flow: parse before run; inside cr_run_steps the
step-shape check (:722) fires before cr_dispatch's op table (:616).
```

---

### G2b — THE CEIL (the one pinned integer, and why it is not redundant)

```python
#: Measured at rc444 by _1653_gate_seed_rc444.py. DOWN ONLY.
CEIL_SURFACE_A_C_DECLINED_VARIANTS = 20
```

```
assert len(C_DECLINED_CHAINS) <= CEIL_...        # may not grow
assert len(C_DECLINED_CHAINS) == CEIL_...        # if it fell, lower the constant NOW
```

**It is not redundant with G2, and here is the exact hole it plugs.** G2 is an
exact-set check, so a shipper who adds a new descriptor *and* a matching
ledger row keeps G2 green **while the residual grows**. G2 is the attribution
guard; the CEIL is the growth guard. They fail on different edits.

The `==` half is the rc433 idiom (`test_assert_contract_gate_rc433.py:632`):
a ceiling left above the true population silently re-opens the room it closed.

---

### G3 — OP-TABLE MIRROR (invariant, by execution)

**Predicate.** `compose._RUN_C_OPS` must be exactly the set of op names
`cr_dispatch` dispatches, measured by driving one minimal in-table chain per
name — plus negative controls that must NOT dispatch.

```
for op in compose._RUN_C_OPS:
    assert c_run(one_step_chain(op, MINIMAL_ARGS[op])).rc != NOT_IMPL
for op in NEGATIVE_OPS:
    assert c_run(one_step_chain(op, ...)).rc == NOT_IMPL
```

**Seed.** claimed 10 · confirmed 10 · dead 0 · negatives wrongly live 0.
`MINIMAL_ARGS` must carry an entry per in-table op; a missing entry is an
`assert`, not a skip, so growing `_RUN_C_OPS` forces the probe to grow with it.

**Failure message.**

```
The Python op-table mirror disagrees with the C dispatch table.
  compose._RUN_C_OPS claims : <op>
  C cr_dispatch returned    : SRMECH_ERR_NOT_IMPL (5)
  anchor                    : c/src/srmech_compose_run.c:581-617 cr_dispatch
compose.py:985 is a LITERAL describing C. Widen or shrink BOTH in the same
change -- gh #1653's op axis is exactly this literal drifting unwatched.
```

**Why it earns its place.** `_RUN_C_OPS` is the single gating literal in
`_chain_c_eligible` (`compose.py:1059`). Nothing reads the C side today. When
the rcN widens `cr_dispatch` from 10 toward the 47 ops the shipped chains
name, this is the gate that makes the two halves move together.

---

### G4 — ROUTE COINCIDENCE (set equality + a control that makes it non-vacuous)

**Predicate.** The set of variants the C run loop accepts must equal the set
the Python dispatcher actually routes to C.

```
assert {v : c_runs(v)} == {v : compose._chain_c_eligible(spec(v))}
```

**Seed: `0 == 0`, and that is VACUOUS — say so in the docstring.** This is the
gate the census's finding (b) demands and it is also the gate most likely to
be believed on no evidence. Both sides are empty at rc444:
`_chain_c_eligible` is True for 0 of 20 (it requires `class_id == "N"` *and*
`op in _RUN_C_OPS`), and C runs 0 of 20.

**The non-vacuity control is therefore mandatory, not optional.** A synthetic
one-step Class-N `rational_add` chain must land in **both** sets and agree:

```
measured: _chain_c_eligible = True, C run rc = 0,
          _run_chain_native returned a value (not _NATIVE_MISS), value (5,6)
```

That is `route_control_proves_non_vacuity: true` in the seed NDJSON. Without
it, `0 == 0` would pass forever on a broken instrument — the
`[[feedback_an_instrument_that_cannot_return_otherwise_is_not_a_measurement]]`
failure, and the reason §3.54 exists.

**Failure messages (both directions, and the second is the dangerous one).**

```
[C CAN, PYTHON WON'T] C runs a chain the Python dispatcher never routes to it.
  chain : <chain>.<variant>
This is the shape gh #1653 warns about: widening cr_dispatch without lifting
the Class-N restriction in _chain_c_eligible (compose.py:1052-1061) ships a C
capability Python never calls, and the census still reads 0. Move both.
```

```
[PYTHON WILL, C CAN'T] Python routes a chain C then declines.
  chain : <chain>.<variant>, C run rc=<rc>
_run_chain_native falls back to pure on a miss, so this is not a wrong answer
today -- it is a live wrong-answer RISK the moment a C arm returns rc=0 on a
shape it does not actually implement (see the four D1-D4 divergences: both C
parsers are REQUIRED-KEYS checks, never closed-key-set checks).
```

---

### G5 — ANCHOR LIVENESS (the meta-gate that stops the spec rotting)

**Predicate.** Every `file:line` cited by `DECLINE_CODES` and by
`SURFACE_A_FORM_LEDGER` must, **read back from the real file**, contain the
token claimed for it.

```
for (path, line, token) in ANCHOR_CLAIMS:
    assert token in read_lines(path)[line - 1]
```

**Seed: 27 claims, 27 verified, 0 bad** (measured on this tree; the full list
is the `ANCHOR_CLAIMS` table below).

**Why this gate exists — it has already caught two real errors in this very
investigation.** (1) The chain census attributed a rejection to
`srmech_compose_run.c:866-876 srmech_json_parse`; lines 866-876 are inside
`srmech_catalog_run_chain`, a *different function* — the real anchors are
`:789`/`:792`. (2) The forms census cited `srmech_dsl_chain_run.c:637-639` as
a **6**-entry discriminator table; hand-read, that array holds **7** strings
(`disc[7]`; `loop_n`/`sub_chain` and `fold_init`/`fold_op` are two spellings
each of one form), so a ratchet counting entries there reads 7 and disagrees
with the census by one. Both are attribution defects with zero numeric impact
— which is precisely why nothing else would have caught them.

This is the rc433 falsifier shape, verbatim in intent: *"every line a scanner
reports must, read back from the real file, contain the token claimed for it —
so it cannot rot as the source moves."*

**Seed `ANCHOR_CLAIMS` (all 27 verified at rc444):**

| file | line | token |
|---|---|---|
| `c/src/srmech_compose.c` | 135 | `co_match_namespace` |
| `c/src/srmech_compose.c` | 144 | `"row"` |
| `c/src/srmech_compose.c` | 145 | `"input"` |
| `c/src/srmech_compose.c` | 146 | `"step"` |
| `c/src/srmech_compose.c` | 147 | `"catalog"` |
| `c/src/srmech_compose.c` | 148 | `return 0` |
| `c/src/srmech_compose.c` | 299 | `co_get_string(step, "class"` |
| `c/src/srmech_compose.c` | 301 | `co_get_string(step, "op"` |
| `c/src/srmech_compose.c` | 304 | `"args"` |
| `c/src/srmech_compose.c` | 513 | `u.i != 1` |
| `c/src/srmech_compose.c` | 675 | `u.i != 1` |
| `c/src/srmech_compose_run.c` | 265 | `cr_resolve_ref` |
| `c/src/srmech_compose_run.c` | 288 | `defer` |
| `c/src/srmech_compose_run.c` | 581 | `cr_dispatch` |
| `c/src/srmech_compose_run.c` | 616 | `SRMECH_ERR_NOT_IMPL` |
| `c/src/srmech_compose_run.c` | 691 | `cr_run_steps` |
| `c/src/srmech_compose_run.c` | 722 | `"op"` |
| `c/src/srmech_compose_run.c` | 868 | `u.i != 1` |
| `c/src/srmech_dsl_chain_run.c` | 637 | `disc[7]` |
| `python/srmech/cascade/compose.py` | 124 | `SUPPORTED_SCHEMA_VERSIONS` |
| `python/srmech/cascade/compose.py` | 151 | `_REFERENCE_PATTERN` |
| `python/srmech/cascade/compose.py` | 162 | `_MAP_KEYS` |
| `python/srmech/cascade/compose.py` | 163 | `_FOLD_KEYS` |
| `python/srmech/cascade/compose.py` | 985 | `_RUN_C_OPS` |
| `python/srmech/cascade/compose.py` | 1045 | `_chain_c_eligible` |
| `python/srmech/cascade/compose.py` | 1059 | `_RUN_C_OPS` |
| `python/srmech/dsl/_catalog.py` | 151 | `_COMPOSITE_OP_KEYS` |

**Failure message.**

```
An anchor cited by this gate no longer points at what it claims.
  claim  : c/src/srmech_compose_run.c:616 should contain 'SRMECH_ERR_NOT_IMPL'
  actual : <the line as read today>
The C source moved. Re-anchor the claim on its new line -- do NOT delete the
claim. A gate whose reasons point at the wrong lines is prose, not a gate.
```

---

## §3 WHAT THESE GATES CANNOT DETECT — read this before writing any release prose

This section is not a caveat. It is a requirement, and srmech has been bitten
by prose that omits it (`srmech_research_notebook.md` §3.54, `#T1132`).

**1. They detect the REGRESSION, never the original.** Every seed above was
measured at rc444, i.e. **before** any repair. If the rcN widens the C
grammar, the ledger will be re-seeded post-repair, and from that moment the
gate can only fire on *growth*. **A ceiling seeded at the live population is a
claim about the FUTURE, not a detection of the past.** No prose in the shipping
rc may say these gates "catch the class that caused gh #1653". They cannot.
The repairs produce the result; the gates only pin it, and **the repairs are
strictly stronger than the gates.**

**2. Where the ledger is seeded, it LICENCES the gap.** All 20 variants are in
`C_DECLINED_CHAINS` today, so G2 is green at 0-of-20 C coverage. **G2 green
does not mean the parity gap is closed — it means the gap is fully
attributed.** Those are different claims and only the second one is being
made. The gate's contribution is that the residual is now *named, reasoned and
counted*, so it cannot be silently deferred again; it is not that the residual
is small.

**3. G4 is vacuous at its seed.** `0 == 0`. Its only real content at rc444 is
the synthetic control. Until some real chain is C-runnable, G4 is a promise
about the next rc, not a measurement of this one.

**4. The structure-probe ctx means "grammar", not "per-call".** `c_runs(v)` is
measured with `{"row": null, "inputs": {}}` on purpose, to keep descriptor
data out of the grammar verdict. A chain that passes G2 as C-runnable can
still decline on a *specific* proof case — e.g. `magnitude` and
`best_rational_signed` return rc=2 on their `nan`/`inf` cases, because
`json.dumps` emits `NaN`/`Infinity` and the C `srmech_json` parser correctly
declines them. The gate does not see that and is not trying to.

**5. Rejection parity is NOT covered by any gate here.** The measured D1
divergence is live through the shipped Python builder:
`chain().then("magnitude", bogus=1).run(-3.5)` returns `3.5` under native
dispatch, while `srmech.cascade.magnitude(-3.5, bogus=1)` raises `TypeError`.
The value is right; the *refusal* is missing, because both C parsers are
required-keys checks and never closed-key-set checks. G1–G5 measure what C
ACCEPTS, never what it should REFUSE. **A closed-key-set check is a separate
gate and it should land in the same commit as any C-side grammar widening** —
widening a required-keys parser adds more keys it will silently ignore.

**6. One platform.** Linux gcc, `libsrmech.so` ABI 17 from this worktree. No
macOS clang, no Windows MSVC cell was exercised.

**7. Surface B is out of scope.** These gates say nothing about
`srmech_dsl_chain_run`. Its form axis is already pinned by
`test_combinator_kernel_closure.py`; its **op** axis is not (the C unary leaf
table holds 7 names, the binary-body table 1, the map-body table 1 — so only 5
of the 18 executable descriptor names have any C DSL kernel and 13 have none).
That is a second, separate gap and this gate does not cover it.

**8. The `#T1142` hole is Python-side and orthogonal.** `_catalog.py:151`
`_COMPOSITE_OP_KEYS` still omits `map_op` at rc444 (verified). C's
`dsl_stage_is_combinator` (`srmech_dsl_chain_run.c:637`) carries all seven
discriminators *including* `map_op`, so on that axis the C projection is
COMPLETE and the Python composite validator is the one behind. It inverts the
assumed direction of the gap and no gate in §2 touches it.

---

## §4 Anti-rot properties, stated as design decisions

| decision | why | what it prevents |
|---|---|---|
| Ledger of **reasoned declines**, not a pinned count, as the primary gate | a fixed decline must be *deleted*, which fails loudly | a repair that leaves the gate green and the number stale |
| Both mirrors read **from the shipped module** (`_MAP_KEYS`, `_REFERENCE_PATTERN`, `_RUN_C_OPS`) | a Python widening enters the loop automatically | the `#T1142` shape: a key set copied into one place and not another |
| C side measured **by execution**, never by regex over C source | a refactor that moves code does not change the verdict | the rc433 comment-strip class of bug (line numbers off by 362 with 6 controls green) |
| **Closed** `DECLINE_CODES` set, with two zero-member codes named in advance | a new decline gets an existing code | invention of an ad-hoc reason under ship pressure |
| G5 anchor liveness | every cited line is re-read from the file | exactly the two mis-citations found in this investigation |
| CEIL kept **alongside** the exact-set ledger | different edits break each | new descriptor + new ledger row = residual grows, G2 green |
| Positive controls run **first**, and abort | a harness fault cannot masquerade as a C decline | the confound that inflates the gap |

---

## §5 The pytest skeleton (text only — `tests/` is off-limits to this session)

Lift into `tests/test_cascade_c_parity_gate_rc<N>.py`. Ledger bodies are
elided with `...` where §1/§2 already gives the full literal.

```python
"""SURFACE-A C-projection parity gate for the config-driven cascade surface.

gh #1653.  Seeded from notes/_1653_gate_seed_rc444.ndjson (rc444, ABI 17).

SCOPE -- READ FIRST.  This gate covers SURFACE A only: the
``[[cascade.chain.steps]]`` grammar (``srmech/cascade/compose.py``, C peers
``srmech_compose.c`` / ``srmech_compose_run.c``), which is the grammar the 21
packaged cascade_catalog descriptors actually use.  SURFACE B
(``[[stage]]`` / ``srmech_dsl_chain_run.c``) is a different grammar with an
opposite parity shape and is already pinned by
tests/test_combinator_kernel_closure.py.  Do not merge the two: they share no
code, and one number cannot describe both.

WHAT THIS GATE CANNOT DETECT (do not let release prose overstate it):
  * It detects the REGRESSION, never the original.  Every ledger row is seeded
    at the live population, so it can only fire on GROWTH.  A ceiling seeded
    at the live population is a claim about the future.  See
    srmech_research_notebook.md 3.54.
  * G2 GREEN MEANS "FULLY ATTRIBUTED", NOT "PARITY ACHIEVED".  At the seed,
    20 of 20 chain variants are declined and the gate is green.
  * G4 is VACUOUS at its seed (0 == 0).  Its content is the control.
  * It measures what C ACCEPTS, never what C should REFUSE.  The D1
    rejection-parity divergence (C swallows an unknown kwarg the pure path
    rejects) is invisible here and needs its own gate.
"""
import ctypes
import json

import pytest

from srmech.cascade import compose
from srmech.dsl import _cascade_chain as _cc

NOT_IMPL = 5          # SRMECH_ERR_NOT_IMPL
BAD_INPUT = 2         # SRMECH_ERR_BAD_INPUT

# ══════════════════════════════════════════════════════════════════════
# 0. THE LEDGERS  (seeded rc444 -- see notes/_1653_gate_spec_rc444.md 1)
# ══════════════════════════════════════════════════════════════════════

DECLINE_CODES = {
    "step_form_map":          "c/src/srmech_compose.c:299-306 co_build_step; "
                              "c/src/srmech_compose_run.c:722-724 cr_run_steps",
    "step_form_fold":         "c/src/srmech_compose.c:299-306 co_build_step; "
                              "c/src/srmech_compose_run.c:722-724 cr_run_steps",
    "ref_namespace_v2":       "c/src/srmech_compose.c:135-148 co_match_namespace",
    "ref_namespace_run":      "c/src/srmech_compose_run.c:288 cr_resolve_ref",
    "op_not_in_c_table":      "c/src/srmech_compose_run.c:616 cr_dispatch",
    "chain_schema_version_2": "c/src/srmech_compose.c:513 co_catalog_body",
}

#: verdict per Surface-A grammar feature.  10 rows == 3 forms + 7 namespaces.
SURFACE_A_FORM_LEDGER = {
    "form:plain":  ("EXECUTES", ""),
    "form:map":    ("UNRECOGNISED", "co_build_step requires class+op+args; a "
                                    "map step carries none of the three"),
    "form:fold":   ("UNRECOGNISED", "same required-keys check; cr_run_steps "
                                    "demands a STRING op"),
    "ns:row":      ("EXECUTES", ""),
    "ns:input":    ("EXECUTES", ""),
    "ns:step":     ("EXECUTES", ""),
    "ns:catalog":  ("PARSES_REJECTS", "recognised at co_match_namespace:147 "
                                      "but cr_resolve_ref:288 defers"),
    "ns:idx":      ("UNRECOGNISED", "v2 rc420; C knows row|input|step|catalog"),
    "ns:bind":     ("UNRECOGNISED", "v2 rc420; as ns:idx"),
    "ns:op":       ("UNRECOGNISED", "v2 rc420; blocks parallel_sector_dispatch"),
}

C_DECLINED_CHAINS = {
    "best_rational_signed.default":     ("op_not_in_c_table", "..."),
    # ... 19 more; full literal in notes/_1653_gate_spec_rc444.md 2 (G2) ...
    "parallel_sector_dispatch.default": ("ref_namespace_v2", "@op. at steps[0]"),
}

#: Measured rc444 by notes/_1653_gate_seed_rc444.py.  DOWN ONLY.
#: If it FALLS, lower it in the same commit -- a stale ceiling re-opens the
#: room it was meant to close.
CEIL_SURFACE_A_C_DECLINED_VARIANTS = 20

#: (path-relative-to-docs/srmech, 1-based line, token that MUST be on it)
ANCHOR_CLAIMS = (
    ("c/src/srmech_compose.c", 135, "co_match_namespace"),
    ("c/src/srmech_compose.c", 299, 'co_get_string(step, "class"'),
    ("c/src/srmech_compose_run.c", 616, "SRMECH_ERR_NOT_IMPL"),
    ("c/src/srmech_compose_run.c", 722, '"op"'),
    ("python/srmech/cascade/compose.py", 985, "_RUN_C_OPS"),
    # ... 22 more; full table in notes/_1653_gate_spec_rc444.md 2 (G5) ...
)

#: Minimal in-table args per op, so an in-table name reaches rc=0 rather than
#: failing on arg shape and looking out-of-table.
MINIMAL_ARGS = {
    "rational_add": {"a": [1, 2], "b": [1, 3]},
    "rational_mul": {"a": [1, 2], "b": [1, 3]},
    "rational_div": {"a": [1, 2], "b": [1, 3]},
    "rational_pow_uint": {"base": [2, 3], "n": 2},
    "pi_cascade_digits": {"n_digits": 3},
    "exp_series_truncate": {"numerator": 1, "denominator": 2, "num_terms": 4},
    "sin_series_truncate": {"numerator": 1, "denominator": 2, "num_terms": 4},
    "cos_series_truncate": {"numerator": 1, "denominator": 2, "num_terms": 4},
    "log1p_series_truncate": {"numerator": 1, "denominator": 2, "num_terms": 4},
    "atan_series_truncate": {"numerator": 1, "denominator": 2, "num_terms": 4},
}
NEGATIVE_OPS = ("rational_sub", "gcd", "mod_add", "magnitude",
                "srmech.math.rational.rational_add")

# ══════════════════════════════════════════════════════════════════════
# 1. HARNESS -- calling convention LIFTED from compose._run_chain_native,
#    never re-derived.  A wrong arena must not look like a grammar gap.
# ══════════════════════════════════════════════════════════════════════

STRUCTURE_CTX = {"row": None, "inputs": {}}


def _lib(*syms):
    return compose._compose_lib(*syms)


def _c_call(entry, *json_blobs):
    """Drive one *_arena_bytes / * export pair.  Returns (rc, out_bytes)."""
    lib = _lib(entry, entry + "_arena_bytes")
    if lib is None:
        pytest.skip("native library unavailable -- this gate needs libsrmech")
    blobs = [json.dumps(b, ensure_ascii=False).encode("utf-8")
             for b in json_blobs]
    ws_bytes = int(getattr(lib, entry + "_arena_bytes")(*[len(b) for b in blobs]))
    ws = (ctypes.c_char * ws_bytes)()
    out_cap = max(ws_bytes // 2, 16384)
    out = (ctypes.c_char * out_cap)()
    out_len = ctypes.c_size_t()
    args = []
    for b in blobs:
        args += [b, len(b)]
    rc = int(getattr(lib, entry)(*args, ws, ws_bytes, out, out_cap,
                                ctypes.byref(out_len)))
    return rc, out.raw[:out_len.value]


def _c_parse(chain_dict):
    return _c_call("srmech_chain_spec_parse", chain_dict)[0]


def _c_run(chain_dict, ctx=None):
    return _c_call("srmech_chain_run", chain_dict, ctx or STRUCTURE_CTX)


def _chain(steps, name="gate"):
    return {"name": name, "summary": "", "returns": "", "on_error": "raise",
            "steps": steps}


_VARIANTS_CACHE = {}


def _variants():
    """The declared (descriptor, variant) pairs, from the LIVE catalog.

    Enumerated from ``cascade_catalog_status()`` rather than from a literal
    list, so a descriptor added to the catalog enters the gate automatically.
    That is the property that would have caught this at rc435: the catalog grew
    20 -> 21 descriptors between rc420 and rc444, which is very likely how the
    issue's carried figure went stale.

    Cached at module scope on purpose: every gate below drives real C calls per
    variant, and re-parsing the catalog per test multiplies that by the test
    count for no benefit.
    """
    if not _VARIANTS_CACHE:
        status = _cc.cascade_catalog_status()
        for name in sorted(n for n, s in status.items() if s == "executable"):
            for variant, spec, entry in _cc.cascade_chain_specs(name):
                _VARIANTS_CACHE["%s.%s" % (name, variant)] = (spec, entry)
    return _VARIANTS_CACHE


def _python_forms():
    """The step forms the SHIPPED engine implements -- derived, not copied."""
    forms = {"form:plain"}
    if compose._MAP_KEYS:
        forms.add("form:map")
    if compose._FOLD_KEYS:
        forms.add("form:fold")
    return forms


def _python_namespaces():
    """Parsed out of the SHIPPED _REFERENCE_PATTERN -- never a copy."""
    pat = compose._REFERENCE_PATTERN.pattern
    inner = pat.split("@(", 1)[1].split(")", 1)[0]
    return {"ns:" + n for n in inner.split("|")}


#: The namespaces the C PARSE discriminator knows (co_match_namespace,
#: c/src/srmech_compose.c:144-147).  The RUN resolver knows one fewer -- it
#: has no @catalog arm (cr_resolve_ref, srmech_compose_run.c:288).
C_PARSE_NS = ("row", "input", "step", "catalog")


def _step_form(raw):
    """Classify one raw step by the SAME key sets compose._parse_step uses."""
    if not isinstance(raw, dict):
        return "malformed"
    if any(k in raw for k in compose._MAP_KEYS):
        return "map"
    if any(k in raw for k in compose._FOLD_KEYS):
        return "fold"
    if all(k in raw for k in ("class", "op", "args")):
        return "plain"
    return "malformed"


def _walk_steps(steps, depth=0):
    """Yield (depth, form, raw) over top-level steps AND nested map bodies."""
    for raw in (steps or ()):
        form = _step_form(raw)
        yield depth, form, raw
        if form == "map":
            for t in _walk_steps(raw.get("body") or (), depth + 1):
                yield t


def _collect_refs(obj, out):
    if isinstance(obj, str) and obj.startswith("@"):
        out.append(obj)
    elif isinstance(obj, dict):
        for v in obj.values():
            _collect_refs(v, out)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            _collect_refs(v, out)


def _first_v2_feature(steps):
    """The first C-PARSE-fatal v2 feature, in the C control-flow order.

    Only reached when the parse gate refused but step[0] is plain -- i.e. the
    fatal feature is deeper in the chain, or is a reference namespace rather
    than a step form.
    """
    for _depth, form, raw in _walk_steps(steps):
        if form in ("map", "fold"):
            return "step_form_" + form
        refs = []
        _collect_refs(raw.get("args") if form == "plain" else raw, refs)
        for r in refs:
            ns = r[1:].split(".")[0].split("[")[0]
            if ns not in C_PARSE_NS:
                return "ref_namespace_v2"
    return "UNATTRIBUTED"


# ══════════════════════════════════════════════════════════════════════
# 2. THE POSITIVE CONTROLS -- run first; everything else is void without them
# ══════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("label,args,ctx", [
    ("literal", {"a": [1, 2], "b": [1, 3]}, STRUCTURE_CTX),
    ("input_refs", {"a": "@input.a", "b": "@input.b"},
     {"row": None, "inputs": {"a": [1, 2], "b": [1, 3]}}),
])
def test_harness_is_proven(label, args, ctx):
    """A chain C SHOULD accept must be accepted, through this exact harness.

    Without this, every rejection below could be a wrong arena / wrong JSON
    shape / wrong ctx marshalling, and the gate would report a gap it invented.
    """
    from srmech.math.rational import rational_add
    cd = _chain([{"class": "N", "op": "rational_add", "args": args}])
    assert _c_parse(cd) == 0, "positive control failed at the C PARSE gate"
    rc, out = _c_run(cd, ctx)
    assert rc == 0, "positive control failed at the C RUN gate (rc=%d)" % rc
    got = compose._reconstruct_value(json.loads(out))
    assert tuple(got) == tuple(rational_add((1, 2), (1, 3))), (
        "positive control ran in C but disagreed with pure -- the harness "
        "reads values back wrongly; no verdict in this file is trustworthy")


# ══════════════════════════════════════════════════════════════════════
# 3. G1 -- SURFACE-A FORM CLOSURE
# ══════════════════════════════════════════════════════════════════════

def _form_probe(feature):
    """One minimal COMPLETE chain per grammar feature.  A namespace probe
    supplies the ctx carrier its reference needs -- a null row would fail on
    DATA and be mis-read as a grammar gap (measured harness artefact, rc444).
    """
    plain = {"class": "N", "op": "rational_add", "args": {"a": [1, 2],
                                                          "b": [1, 3]}}
    row, inputs = None, {}
    if feature == "form:plain":
        steps = [dict(plain)]
    elif feature == "form:map":
        steps = [{"map_over": "@input.xs", "index": "k", "body": [dict(plain)]}]
        inputs = {"xs": [1, 2, 3]}
    elif feature == "form:fold":
        steps = [{"fold_class": "N", "fold_op": "rational_add",
                  "fold_init": [0, 1], "over": "@input.xs"}]
        inputs = {"xs": [[1, 2], [1, 3]]}
    elif feature == "ns:step":
        steps = [dict(plain),
                 {"class": "N", "op": "rational_add",
                  "args": {"a": "@step[0].output", "b": [1, 3]}}]
    else:
        ns = feature.split(":", 1)[1]
        ref = {"row": "@row.a", "input": "@input.a", "catalog": "@catalog.a",
               "idx": "@idx.k", "bind": "@bind.s", "op": "@op.srmech"}[ns]
        steps = [{"class": "N", "op": "rational_add",
                  "args": {"a": ref, "b": [1, 3]}}]
        if ns == "row":
            row = {"a": [1, 2]}
        if ns == "input":
            inputs = {"a": [1, 2]}
    return _chain(steps, name=feature), {"row": row, "inputs": inputs}


def measured_verdict(feature):
    cd, ctx = _form_probe(feature)
    p = _c_parse(cd)
    r = _c_run(cd, ctx)[0]
    if p == 0 and r == 0:
        return "EXECUTES"
    return "PARSES_REJECTS" if p == 0 else "UNRECOGNISED"


def test_g1_form_ledger_is_closed_both_ways():
    """Every Python Surface-A grammar feature is ledgered, and no row is stale.

    FALSIFIER (Python side): add a 4th step form or an 8th reference namespace
    and this goes red until the C peer ships or a REASONED decline row lands.
    FALSIFIER (C side): teach co_match_namespace @idx and this goes red until
    the ledger row is DELETED.
    """
    declared = set(SURFACE_A_FORM_LEDGER)
    live = _python_forms() | _python_namespaces()
    assert live <= declared, (
        "SURFACE-A grammar features with no ledger row: %s. Python widened "
        "and C has no peer: ship the peer, or add a row WITH A REASON in this "
        "same commit. Do not widen one projection alone -- gh #1653 is what "
        "that costs." % sorted(live - declared))
    assert declared <= live, (
        "stale ledger rows for features Python no longer implements: %s"
        % sorted(declared - live))


@pytest.mark.parametrize("feature", sorted(SURFACE_A_FORM_LEDGER))
def test_g1_each_form_verdict_matches_measurement(feature):
    want, reason = SURFACE_A_FORM_LEDGER[feature]
    got = measured_verdict(feature)
    assert got == want, (
        "SURFACE-A form parity moved and the ledger did not.\n"
        "  feature     : %s\n  ledger says : %s\n  measured    : %s\n"
        "  reason on file: %s\n"
        "If C GAINED this feature that is good news -- delete/downgrade the "
        "row in THIS commit; a stale decline row silently re-opens the room "
        "it was meant to close. If PYTHON gained it, ship the C peer."
        % (feature, want, got, reason or "(none -- it executes)"))
    if want != "EXECUTES":
        assert reason.strip(), (
            "%s is declared as a DECLINE with no reason. A decline list "
            "without reasons is a deferral list." % feature)


# ══════════════════════════════════════════════════════════════════════
# 4. G2 -- CHAIN LEDGER CLOSURE  (+ G2b the CEIL)
# ══════════════════════════════════════════════════════════════════════

def _first_gate(key, spec, entry):
    """The decline code, chosen by the FIRST C gate the control flow reaches:
    parse before run, and inside cr_run_steps the step-shape check (:722)
    before cr_dispatch's op table (:616)."""
    steps = entry.get("steps", []) or []
    parse_rc = _c_parse(_chain(steps, name=key))
    run_rc = _c_run(_chain(steps, name=key))[0]
    if parse_rc == 0 and run_rc == 0:
        return None
    first = _step_form(steps[0]) if steps else None
    if first in ("map", "fold"):
        return "step_form_" + first
    if parse_rc != 0:
        return _first_v2_feature(steps)      # map / fold / namespace, in order
    return "op_not_in_c_table"


def test_g2_ledger_equals_the_measured_decline_set():
    """Bidirectional.  MISSING and STALE are different failures on purpose."""
    variants = _variants()
    measured = {k for k, (s, e) in variants.items()
                if _c_run(_chain(e.get("steps", []), name=k))[0] != 0}
    missing = measured - set(C_DECLINED_CHAINS)
    stale = set(C_DECLINED_CHAINS) - measured
    assert not missing, (
        "[MISSING] chains the C projection cannot run and the ledger does not "
        "name: %s. Either make them C-runnable, or add each to "
        "C_DECLINED_CHAINS with a code and a REASON. An unattributed "
        "rejection is how a stale figure survived 95 rcs." % sorted(missing))
    assert not stale, (
        "[STALE] ledgered declines that now RUN in C: %s. Delete the rows in "
        "this commit -- good news must SHRINK the ledger or the gate loses "
        "its teeth." % sorted(stale))


@pytest.mark.parametrize("key", sorted(C_DECLINED_CHAINS))
def test_g2_each_decline_has_the_right_reason(key):
    code, reason = C_DECLINED_CHAINS[key]
    assert code in DECLINE_CODES, (
        "%r is not in the CLOSED DECLINE_CODES set. Do not invent a code "
        "under ship pressure; if the C decline is genuinely new, add it to "
        "DECLINE_CODES with its C source anchor." % code)
    assert reason.strip(), "%s is ledgered with no reason" % key
    spec, entry = _variants()[key]
    got = _first_gate(key, spec, entry)
    assert got == code, (
        "[WRONG REASON] %s: ledger says %s, measured first C gate is %s (%s). "
        "The gap is real but the ATTRIBUTION is wrong, and a wrong "
        "attribution mis-sizes the fix."
        % (key, code, got, DECLINE_CODES.get(got, "?")))


def test_g2_c_runnable_chains_agree_BYTE_FOR_BYTE_with_pure():
    """"C-runnable" must mean byte-identical, not merely rc == 0.

    Vacuous at the seed (0 C-runnable) -- and test_g4_control_is_not_vacuous
    is what stops that vacuity from being invisible.
    """
    for key, (spec, entry) in _variants().items():
        if key in C_DECLINED_CHAINS:
            continue
        for case in (entry.get("proof_cases") or []):
            inputs = dict(case.get("inputs") or {})
            rc, out = _c_run(_chain(entry["steps"], name=key),
                             {"row": None, "inputs": inputs})
            assert rc == 0, "%s left the ledger but declines case %r" % (
                key, inputs)
            c_val = compose._reconstruct_value(json.loads(out))
            py_val = compose.run_chain(spec, row=None, inputs=inputs)
            assert repr(c_val) == repr(py_val), (
                "%s runs in C and DISAGREES with pure: C=%r pure=%r. A C path "
                "that returns a different number is worse than one that "
                "declines." % (key, c_val, py_val))


def test_g2b_ceil_only_goes_down():
    n = len(C_DECLINED_CHAINS)
    assert n <= CEIL_SURFACE_A_C_DECLINED_VARIANTS, (
        "SURFACE-A C-declined chain variants rose to %d (ceil %d). G2 is an "
        "exact-set check, so adding a descriptor AND a ledger row keeps it "
        "green while the residual GROWS -- this ceiling is what catches that. "
        "Do not raise it to make a change fit."
        % (n, CEIL_SURFACE_A_C_DECLINED_VARIANTS))
    assert n == CEIL_SURFACE_A_C_DECLINED_VARIANTS, (
        "SURFACE-A C-declined variants FELL to %d (ceil %d) -- good news, but "
        "lower the constant in THIS commit so the ratchet keeps its teeth."
        % (n, CEIL_SURFACE_A_C_DECLINED_VARIANTS))


# ══════════════════════════════════════════════════════════════════════
# 5. G3 -- OP-TABLE MIRROR (by execution)
# ══════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("op", sorted(compose._RUN_C_OPS))
def test_g3_every_claimed_op_really_dispatches_in_c(op):
    assert op in MINIMAL_ARGS, (
        "compose._RUN_C_OPS grew to include %r with no probe args here. Add "
        "the minimal arg shape so this mirror stays a MEASUREMENT rather than "
        "quietly skipping the new op." % op)
    rc = _c_run(_chain([{"class": "N", "op": op, "args": MINIMAL_ARGS[op]}]))[0]
    assert rc != NOT_IMPL, (
        "compose._RUN_C_OPS claims %r but cr_dispatch returned "
        "SRMECH_ERR_NOT_IMPL (c/src/srmech_compose_run.c:581-617). "
        "compose.py:985 is a LITERAL describing C: widen or shrink BOTH in "
        "the same change." % op)


@pytest.mark.parametrize("op", NEGATIVE_OPS)
def test_g3_negative_controls_do_not_dispatch(op):
    """Without these, test_g3 above could pass on an instrument that says OK
    to everything."""
    rc = _c_run(_chain([{"class": "N", "op": op,
                         "args": {"a": [1, 2], "b": [1, 3]}}]))[0]
    assert rc == NOT_IMPL, (
        "%r is NOT in compose._RUN_C_OPS yet C dispatched it (rc=%d). Either "
        "the C table grew without the Python mirror, or this probe no longer "
        "discriminates." % (op, rc))


# ══════════════════════════════════════════════════════════════════════
# 6. G4 -- ROUTE COINCIDENCE (vacuous at seed; the control is the content)
# ══════════════════════════════════════════════════════════════════════

def test_g4_c_acceptance_and_python_routing_are_the_same_set():
    """VACUOUS AT THE SEED: both sides are empty at rc444 (0 == 0).

    Kept anyway because it is the gate the census's finding (b) demands:
    widening cr_dispatch without lifting the Class-N restriction in
    _chain_c_eligible (compose.py:1052-1061) ships a C capability Python never
    routes to, and the census still reads 0.
    """
    variants = _variants()
    c_runs = {k for k, (s, e) in variants.items()
              if _c_run(_chain(e.get("steps", []), name=k))[0] == 0}
    routes = {k for k, (s, e) in variants.items()
              if compose._chain_c_eligible(s)}
    assert c_runs == routes, (
        "[C CAN, PYTHON WON'T] %s\n[PYTHON WILL, C CAN'T] %s\n"
        "Move BOTH projections in the same rc."
        % (sorted(c_runs - routes), sorted(routes - c_runs)))


def test_g4_control_is_not_vacuous():
    """MANDATORY, not optional.  Proves both sides of G4 CAN be non-empty.

    An instrument that cannot return otherwise is not a measurement: with both
    sets empty at the seed, G4 would pass forever on a broken predicate.
    """
    cd = _chain([{"class": "N", "op": "rational_add",
                  "args": {"a": [1, 2], "b": [1, 3]}}])
    spec = compose.parse_chain_spec(cd)
    assert compose._chain_c_eligible(spec) is True, (
        "the synthetic in-table Class-N control is NOT c_eligible -- "
        "_chain_c_eligible has changed and G4 is now untested")
    assert _c_run(cd)[0] == 0, "the control chain does not run in C"
    got = compose._run_chain_native(spec, None, {})
    assert got is not compose._NATIVE_MISS, (
        "the control did not actually take the native arm, so G4's set "
        "equality is comparing two empty sets with no evidence either can "
        "ever be non-empty")
    assert tuple(got) == (5, 6)


# ══════════════════════════════════════════════════════════════════════
# 7. G5 -- ANCHOR LIVENESS (the meta-gate)
# ══════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("path,line,token", ANCHOR_CLAIMS)
def test_g5_every_cited_anchor_still_says_what_we_claim(path, line, token):
    """Stated as an INVARIANT, not a pinned literal, so it cannot rot as the
    source moves.  This gate has already caught two real mis-citations in the
    gh #1653 research (a line inside the wrong function; a disc[7] array
    described as 6 entries)."""
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent.parent      # docs/srmech
    lines = (root / path).read_text(encoding="utf-8").splitlines()
    assert line - 1 < len(lines), "%s:%d is past EOF" % (path, line)
    got = lines[line - 1]
    assert token in got, (
        "An anchor cited by this gate no longer points at what it claims.\n"
        "  claim  : %s:%d should contain %r\n  actual : %s\n"
        "The source moved. RE-ANCHOR the claim; do not delete it. A gate "
        "whose reasons point at the wrong lines is prose, not a gate."
        % (path, line, token, got.strip()))
```

---

## §6 The planted-failure controls — MEASURED to fire, not asserted

A gate never observed to fail is not a measurement. **All seven controls below
were run on this tree and all seven FIRED; the unperturbed predicate set
PASSED in the same run.** The verbatim output is at the bottom of this section.

Artifact: `notes/_1653_gate_controls_rc444.py` (standalone; no pytest, no
`tests/` file). Each control perturbs a **copy** of a ledger and calls the
predicate directly. Nothing monkeypatches shipped module state.

> **Cross-validation worth noting.** That file's `_first_gate` classifier and
> `_1653_gate_seed_rc444.py`'s `classify_decline` were written independently and
> **agree on all 20 variants** (`step_form_map` 7 / `op_not_in_c_table` 11 /
> `step_form_fold` 1 / `ref_namespace_v2` 1). Two separately-written classifiers
> reaching the same attribution is stronger than one classifier run twice.

| # | gate | perturbation | measured outcome | rules out the false green |
|---|---|---|---|---|
| **PC-1** | G1 | add a synthetic `"form:while"` to the live-feature set | **FIRES** — `unledgered: ['form:while']` | the closure check reading an empty diff and passing regardless — i.e. `_python_forms()` returning `{}` |
| **PC-2** | G1 | flip the `ns:idx` ledger row to `EXECUTES` | **FIRES** — `ledger says EXECUTES measured UNRECOGNISED` | `measured_verdict` always returning the ledgered value (a tautology) |
| **PC-3** | G2 | delete `net_chirality.default` from the ledger copy | **FIRES** — `[MISSING] ['net_chirality.default']` | the measured-decline set coming back empty (`_c_run` broken, everything "runs") |
| **PC-4** | G2 | add a synthetic C-runnable chain to the ledger copy | **FIRES** — `[STALE] ['synthetic_control.default']` | a ledger that can only grow. This is the control that proves the **down-only direction is enforced**, and it is the one most likely to be skipped |
| **PC-5** | G2 | relabel `net_chirality.default` as `op_not_in_c_table` | **FIRES** — `[WRONG REASON] ... ledger op_not_in_c_table measured step_form_fold` | attribution accepted on the shipper's word. `net_chirality` is the right subject: it is the **only** chain whose step[0] is not plain, so it is the only one where the fold gap is not MASKED by the op-table gap at step 0 |
| **PC-6** | G3 | probe `"rational_sub"` as if in-table | **FIRES** — `claimed in-table but cr_dispatch returned NOT_IMPL` | the op probe returning rc≠5 for everything (a wrong arg shape passing by accident) |
| **PC-7** | G5 | claim `srmech_compose_run.c:616` contains `"co_match_namespace"` | **FIRES** — prints the real line (`return SRMECH_ERR_NOT_IMPL; …`) | the anchor reader silently passing on a missing file or a short read |

```
PC-1 FIRES: unledgered: ['form:while']
PC-2 FIRES: ledger says EXECUTES measured UNRECOGNISED
PC-3 FIRES: [MISSING] ['net_chirality.default']
PC-4 FIRES: [STALE] ['synthetic_control.default']
PC-5 FIRES: [WRONG REASON] net_chirality.default: ledger op_not_in_c_table measured step_form_fold
PC-6 FIRES: claimed in-table but cr_dispatch returned NOT_IMPL
PC-7 FIRES: anchor :616 actual 'return SRMECH_ERR_NOT_IMPL;   /* op not in the C dispatch table → pure */'
UNPERTURBED all-predicates: PASS
```

**Two of these control CLASSES had already fired for real** before they were
written down, which is the evidence they are worth their runtime:

- **PC-2's class** caught my own `@row` harness artefact (§1.2): the probe's
  ctx carried `row: null`, the verdict came back `PARSES_REJECTS`, and the
  ledger would have recorded a C namespace gap that does not exist.
- **PC-7's class** caught two mis-citations in the sibling censuses — a line
  number inside the wrong function, and a `disc[7]` array described as holding
  six entries.

**One control is deliberately NOT proposed.** There is no planted control for
G4's set equality, because at the seed both sides are empty and any
perturbation that makes one side non-empty is testing the perturbation rather
than the gate. `test_g4_control_is_not_vacuous` is the honest substitute, and
§3 item 3 says plainly that G4 is a promise about the next rc.

---

## §7 Deltas vs the issue's carried figures — the measurement wins

**(1) "C implements 1 of 3 step forms" — CONFIRMED, with a scope qualifier the
issue is missing.** Exactly 1 of 3 on **Surface A** (plain executes; map and
fold both `BAD_INPUT=2` at parse *and* run), re-measured here by execution.
Applied to Surface B the same sentence understates C by a wide margin (5 of 6
execute there). The issue should say **which grammar**.

**(2) "11 of 18 chains rejected" — NOT REPRODUCED.** Measured at rc444:
**20 of 20 declared chain variants are declined by `srmech_chain_run`**
(equivalently 18 of 18 executable descriptors). The number 11 *is* in the
measurement, twice, and both times with the opposite polarity:

- `srmech_chain_spec_parse` **ACCEPTS** 11 of 18 and rejects 7.
- the `op_not_in_c_table` decline class has **exactly 11** members — and it is
  the *same* 11. For that slice, widening `cr_dispatch` is the only C-side
  blocker left.

Two live provenance hypotheses, neither verifiable without the rc435 tree, and
the ship should carry **both** rather than picking one:

- **H1** — the figure is the parse axis with accept/reject inverted, taken
  when the catalog held 17 executable descriptors (`klein4_from_one` arrived
  rc438), i.e. "11 accepted of 17" → "11 of 18 rejected".
- **H2** — "chains carrying ≥1 `composition_of_c` op" (chains *not* reachable
  by widening the dispatch table alone) is **exactly 11 of 18** at rc444,
  matching the issue's denominator precisely, which H1 does not (H1 needs 17).
  It falls to 10 of 17 on the reconstructed rc435 surface, so it is not a
  *better* explanation — but it is a coherent rejection-shaped one.

Either way, **the run-axis figure to carry forward is 20 of 20** (18 of 18
descriptors), and the issue must not ship the word "inverted" as a
*measurement* — that is an inference about what a ~rc435 build reported.

**(3) NEW — the reference-namespace axis, which the issue does not carry at
all.** Python 7 · C parse 4 · C run 3. `@idx` is used by 7 of 20 variants,
`@bind` by 7, `@op` by 1. **`@op` alone is what blocks
`parallel_sector_dispatch`**, a chain that is otherwise pure plain-form — the
cheapest single namespace win on the board. A "3 step forms" framing hides
this whole axis.

**(4) NEW — the schema-version axis, unmeasured by both sibling censuses.**
`chain_schema_version = 2` (declared by all 20 shipped chains) is
`BAD_INPUT` at `srmech_chain_catalog_parse`; v1 is `OK`. Both censuses reported
catalog-parse/spec-parse agreement only because each minted its own v1
wrapper. A bare-C host reading the real descriptors through the catalog
wrapper is blocked before any grammar question — and separately,
`srmech_dsl_toml_chain_to_json` cannot even READ 2 of the 18 (`magnitude`,
`best_rational_signed`) because of their `nan`/`inf` proof-case literals.

**(5) CORRECTION to a sibling census (numeric impact: none).** Its
`ref_namespaces_c = 4` is the **parse** count; the run resolver knows 3. Its
non-finite attribution string cites `srmech_compose_run.c:866-876`, which is
inside `srmech_catalog_run_chain`; the firing parses are at `:789` (chain) and
`:792` (ctx). Both are exactly the class G5 exists to catch.

---

## §8 Sizing the fix, from the ledger

The ledger's own code counts are the work breakdown, cheapest first:

| # | work | unblocks | note |
|---|---|---|---|
| 1 | widen `cr_dispatch` (10 → toward 47) **and lift the Class-N restriction in `_chain_c_eligible` in the same rc** | the 11 `op_not_in_c_table` variants — already parse-accepted | **47** distinct ops sit outside the C table across all 20 variants; the 11-variant slice needs **23** of them (both re-measured from my own ledger, not carried). 14 of those 23 are already `c_dispatched` per `rosetta_classification.ndjson`, so it is largely a dispatch-table edit, not new math. Moving only one side changes nothing observable: G4 exists to make that a red build. |
| 2 | `@op` namespace in `co_match_namespace` + a run-side arm | `parallel_sector_dispatch` (1 variant) | cheapest namespace win; the chain is otherwise all-plain |
| 3 | FOLD step form | `net_chirality` (1 variant, its only step) | `srmech_dsl_chain_run` already implements a seeded fold on its own grammar — prior C art to read, not invent |
| 4 | `@idx` / `@bind` namespaces | prerequisite for most map bodies | 7 of 20 variants each |
| 5 | MAP step form, incl. map-of-map nesting + body-local `@step[N]` scoping | 7 variants | the expensive one. JPL Rule 1 makes nested-map recursion the design question; `srmech_dsl_chain_run` handles its own nesting with a bounded asserted depth guard — follow that pattern |
| 6 | accept `chain_schema_version = 2` on the catalog-wrapper paths | any bare-C host reading the real descriptors | orthogonal to 1-5; three sites (`:513`, `:675`, `srmech_compose_run.c:868`) |

**And in the same commit as ANY of 1-5: the closed-key-set check.** Both C
parsers are required-keys checks today, which is the root of all four measured
Python/C divergences (D1-D4). Widening a required-keys parser adds more keys
it will silently ignore.

---

## §9 Provenance

| file | what it is |
|---|---|
| `notes/_1653_gate_seed_rc444.py` | the seed instrument (54 NDJSON records; positive controls abort on failure) |
| `notes/_1653_gate_seed_rc444.ndjson` | every number in §1, as measured |
| `notes/_1653_gate_controls_rc444.py` | the seven planted-failure controls of §6 — all seven measured FIRING, unperturbed set PASSING; also the independent `_first_gate` classifier that cross-validates the seed's attribution |
| `notes/_1653_chain_census_rc444.{py,ndjson}` | sibling: per-chain C accept/reject census |
| `notes/_1653_step_forms_rc444.{py,ndjson}` | sibling: per-step-form census across both surfaces |
| `notes/_1653_t1142_*.{py,ndjson}` | sibling: the `map_op` composite-validation lapse |
| `notes/_1653_t1145_*.{py,ndjson}` | sibling: the dotted-op `resolve()` census |
| `srmech_research_notebook.md` §3.54 | the "gates detect the regression, never the original" discipline §3 obeys |
| `tests/test_combinator_kernel_closure.py` | the Surface-B peer of this gate; the shape §2 G1 copies |
| `tests/test_assert_contract_gate_rc433.py` | the `<=` + `==` CEIL idiom §2 G2b copies |

Nothing under `srmech/**`, `c/src/**`, `c/include/**` or `tests/**` was
modified by this research. `git status` shows only untracked files under
`docs/srmech/notes/`.

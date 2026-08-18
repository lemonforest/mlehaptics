# rc449 BUILD SPEC — C key-set refusal on both chain interpreters (`#T1158`, gh #1653 residual)

**Base:** `0.9.0rc448`, head `60378dcf5` (merged, tagged, on TestPyPI). **Target:** `0.9.0rc449`.
**Root for every path below:** `D:/GitHub/mlehaptics/docs/srmech/`.
**Status of this document:** design SSoT for rc449. Executable without re-deriving anything. Every
number in it was measured at rc448 head against a library built fresh under WSL2 (138 TUs,
self-reporting `0.9.0rc448 ABI 18`) — never against the stale `build_rc342..rc355` libs on the
Windows host.

---

## §0 THE HEADLINE — what property this rc adds

rc447 closed `#T1146` rejection parity by teaching the **Python IR builder** to defer
(`_then_native_desc` declines a stage whose kwarg the op does not accept). Its own commit says so:
*"CLOSED AT THE IR BUILDER, NOT INSIDE C, because that is where the two projections diverge."*

That is a **divergence-only fix**. It is the exact mirror of the shape issue #1653's DoD warned
against ("a capability-only fix does not satisfy this"): both make the projections agree without
moving C's acceptance behaviour, and they differ only in which side moved. On a bare-C host there is
no Python IR builder, so a malformed declaration is **still silently accepted and computed** — the
silent-wrong-answer class. And rc447 is the same rc that shipped `c/test/test_srmech_chain_run.c`,
the ADR-0003 bare-C proof ("NO PYTHON. NO ctypes."), so it demonstrated that consumers reach exactly
the host where the Python-side fix does not apply.

**rc449's claim is therefore NOT "the projections now agree." It is: C REFUSES what it should, on
the host where Python does not exist.** Those are different properties, and a parity harness that
only compares outputs cannot tell them apart.

**The witness that must flip.** Bare C, `best_rational_signed` on `0.3333333333333333`, rc448 head:

| declaration | rc448 returns | rc449 must return |
|---|---|---|
| `{"op":"best_rational_signed","max_denominator":2}` | `OK`, `(0, 1)` | unchanged — `OK`, `(0, 1)` |
| `{"op":"best_rational_signed","max_denominatr":2}` | `OK`, `(1, 3)` | `SRMECH_ERR_BAD_INPUT` |

One dropped letter. No crash, no decline — the constraint is silently dropped, the default 100 is
used, and a **different number** comes back. Python on the same call raises
`TypeError: best_rational_signed() got an unexpected keyword argument 'max_denominatr'.
Did you mean 'max_denominator'?`

---

## §1 ⚠️ THE TWO ADJUDICATIONS DISAGREE — three disagreements, each resolved here

The design adjudication (Fable #1) and the verification adjudication (Fable #2) agree on the two
hardest calls (status = `BAD_INPUT`; ABI bumps 18 → 19; legal set = `params[1..]` on the DSL
surface). They disagree on three points. **A hidden disagreement between a design and its
instruments is how a wrong design ships with a green gate**, so each is named and settled.

### D1 — SCOPE. Design says six surfaces; verification says two.

- **Fable #1** ships F6 (DSL leaf kwargs) + Surface-A `args` + **F1/F8** (compose `class`-key
  validity and chain-head required keys) + **F5** (DSL multi-discriminator MIXED) + **F2** (genome
  attestation overlay), on the argument that one ABI bump covers all of them and deferring any
  forces ABI 20 later.
- **Fable #2** §0.3 scopes to **unknown op-argument keys on the two chain interpreters only**, and
  explicitly excludes F1, F5, F2, F3, F4, F8, F9.

**RESOLUTION — Fable #2's cut line, with Fable #1's ABI accounting carried forward as a named,
accepted cost.** The discriminator is not "does it ride the same bump" but **"is it the same defect
class, with both sides measured, and is the fix a port of an in-tree construct rather than a new
adjudication?"**

| surface | same class? | Python refusal measured? | verdict |
|---|---|---|---|
| F6 DSL leaf kwargs | yes — the subject | **executed** (TypeError, both spellings) | **IN** |
| Surface-A `args` keys | yes — identical class, `payload(**args)` at `compose.py:1449`; measured 0 of 21 C-run ops carry `**kwargs` | executed on the registry census; read on the raise site | **IN** |
| F1 `class` presence/validity/agreement, F8 chain-head keys | **no** — required-key + enum-validity, not key-set | read only | FILED |
| F5 DSL multi-discriminator MIXED | **no** — discriminator mutual exclusion | read only | FILED |
| F2 genome attestation unknown key | **no** — a different mechanism (5-key overlay across 9 exports), and its Python peer's behaviour on a **non-string value for a known key** is explicitly **unmeasured** | partly read | FILED, elevated |

Two decisive reasons for the narrow line:

1. **Fable #1's own text concedes the unmeasured half.** It writes "**Measure first**: Python's
   behaviour on a non-string *value* for a known key (C currently `continue`s) — mirror exactly, do
   not invent" for F2, and "measure Python first" for combinator-stage keys. A slice whose Python
   side is unmeasured cannot ship in the rc whose entire thesis is that agreeing-by-output is not
   proof. Shipping it would reproduce the adjudicated defect one level up.
2. **The named failure mode "stricter-than-Python green" is invisible to the existing corpus.**
   30 of 45 `*parity*` files have no forced-pure arm; 16 are blind on both axes. Every surface added
   widens an out-refusal risk that nothing in the tree can see. Two surfaces with executed
   measurements is a defensible blast radius; six is not.

**Accepted cost, stated with eyes open:** closing F1/F5/F2/F3/F4/F7/F8 later is another status
reinterpretation on existing exports and therefore forces **ABI 19 → 20** (and possibly 21 if they
split across rcs). That cost is real and is accepted in exchange for not shipping an unmeasured
refusal. Each is FILED with a disposition in §5 — ADR-0009 §5 forbids the unfiled decline, and that
rule is what gh #1653 exists to enforce.

**F2 is flagged as the head item of rc450, not as routine backlog.** It is the highest-stakes
acceptance gap in the sweep: a *wrong provenance record* landing durably on disk inside an
MPR-attested manifest, from the one op whose purpose is provenance honesty. Measured bare-C at
rc448: `srmech_genome_save(..., "{\"source_uri\":\"https://real.example/...\"}", ...)` returns `OK`
and writes srmech's **default** `source_url`. "Ungated surfaces trickle" is exactly what must not
happen to it.

### D2 — key-set SOURCE OF TRUTH. Design decides the registry; verification leaves R-or-S open.

- **Fable #1**: Option **R** — `srmech_tool_registry_find("srmech.cascade." + op)->params[1..]`.
- **Fable #2** §4: Option R **or** Option S (a static `const` table in the C file), "the rc must ship
  exactly one", with a drift gate specified for each.

**RESOLUTION — Option R.** Fable #2 does not contradict Fable #1; it declines to choose. The choice
is forced by the drift argument, which only R satisfies:

- R's names are **already gated set-equal to the Python signatures from both directions** —
  `tests/test_mcp.py::test_schema_signature_alignment_no_drift` (declared ⊆ bindable, rc13) and
  `tests/test_declared_param_completeness_rc408.py` (declared ⊇ live, rc408). Measured at head:
  **660/660 name-sets equal, zero drift**, both gates green (`5 passed`). That two-sided pin is what
  makes the registry a *source of truth* rather than a third copy.
- S mints a **new artifact with no gate until we write one** — and the `#T1146` divergence existed
  *because* two independent notions of "accepted keys" existed. Adding a third is the defect in
  miniature.
- The packaged TOML catalog is eliminated by measurement: it carries `[cascade].name` / `.native` /
  `.delegates_to` and **no param names**. It also needs a filesystem the bare-C host is promised not
  to need (`srmech.h:6392`).
- Cost of R is zero on both JPL axes: the registry is `static const` .rodata (in-tree precedents:
  `disc[7]` at `srmech_dsl_chain_run.c:637-639`; `map_k`/`fold_k`/`plain_k` at
  `srmech_compose_run.c:1309-1312`; `dotted[21]` at `:1331`) — Rule 3 bans malloc, not .rodata — and
  the stage's own key set is already parsed and addressable (`srmech.h:5564`,
  `{ const char **keys; srmech_json_value_t **vals; uint32_t n; }`, keys NUL-terminated, verified by
  execution). **No arena bytes, no new parse, no new exported symbol.** Both linkers already
  co-locate it: `c/Makefile:29` and the root `CMakeLists.txt` GLOB `c/src/*.c`, and `nm` shows
  `srmech_tool_registry_find` and `srmech_dsl_chain_run` both `T` in the same `.a`.

R carries one obligation Fable #2 correctly identified and Fable #1 also accepted: **`params[0]` is
the data carrier, so the rule depends on declaration ORDER, and order is ungated** — 8 of 660
entries are same-set-but-reordered today. The order gate (G4) ships in the same commit. See §3.4.

### D3 — the Python `_op_accepts` param-0 residual: shipped, or hygiene?

- **Fable #1**: ships it, "closes 7/7".
- **Fable #2** §8.7: "recommended hygiene, not required for refusal-set equality — if it does not
  ship, the IR builder still emits a doomed stage, and saying otherwise would be a fourth false
  shipped claim in this arc."

**RESOLUTION — ship it, and state the claim in Fable #2's words.** These are compatible: Fable #2 is
constraining the *claim*, not the *work*. The edit is cheap and makes the IR builder honest instead
of relying on the pure `TypeError` at run time. But the rc must NOT say "the Python residual is what
closes the gap" — front-door end-behaviour converges without it (C refuses → `_NATIVE_MISS` → pure
raises the same `TypeError`). The C refusal is what closes the gap; the Python edit stops the
builder emitting a stage it knows is doomed.

**Measured residual, 7/7 through the public `.then()` surface:** `magnitude x=5` →
`_op_accepts=True`, IR emitted `{'op':'magnitude','x':5}`, pure raises
`TypeError: magnitude() got multiple values for argument 'x'`. Identically for `reorient value=`,
`pin_slot_at_zero x=`, `best_rational_signed x=`, `chiral_flip seq=`, `net_chirality orientations=`,
`autocorrelation x=`.

---

## §2 DECIDED — the three contract questions

### 2.1 Key-set source of truth: the compiled tool registry, `params[1..]` on the DSL surface

`c/src/srmech_tool_registry.c`, already linked. **Nothing needs generating.**
`srmech.h:5726` defines `srmech_tool_param_t {name, type, required, summary}`; `:5740` hangs
`params` + `param_count` off `srmech_tool_entry_t`; `srmech_tool_registry_find(const char *)` at
`c/src/srmech_tool_schema.c:59` is a linear `strcmp` scan. Bare-C probe at rc448:

```
srmech_tool_registry_count() = 655
srmech.cascade.magnitude              param_count=1  keys=x
srmech.cascade.reorient               param_count=2  keys=value,orientation
srmech.cascade.best_rational_signed   param_count=3  keys=x,max_denominator,fine_scale
magnitude                             NOT FOUND      <-- the "srmech.cascade." prefix is required
```

Only **bare** op names reach a leaf (a dotted spelling fails the exact-length `memcmp` in
`dsl_leaf_dispatch` and defers), so `"srmech.cascade." + op` into a **bounded stack buffer with a
length assert** resolves all C-runnable leaf ops. No malloc.

**The two surfaces index the registry DIFFERENTLY, and that asymmetry is deliberate — gate it so
nobody "unifies" it:**

| surface | how the data reaches the op | legal key set |
|---|---|---|
| **B — DSL** (`dsl_leaf_dispatch`) | implicitly, as the chain carrier `in` | `params[1..]` — `params[0]` is the data carrier and is **itself refused** as a stage kwarg |
| **A — compose** (`cr_run_plain` → `cr_dispatch`) | by name, inside `args` | `params[*]` — every declared param is a legal `args` key |

A `params[*]` rule on Surface B reproduces the measured 7/7 residual. A `params[1..]` rule on
Surface A would refuse `gcd{a,b}`. Both directions are gated (§4, G1-B5 and G1-A1).

**Surface A needs one extra artifact:** the bare op names (`gcd`, `mod_add`, `rational_add`, …) do
not live under `srmech.cascade.*`. Ship a **static `const` op-name → registry-full-name index** in
`srmech_compose_run.c`, covering the ≈20 names matched by `cr_op_is` across `cr_dispatch` and
`cr_dispatch_real` (measured 20 at rc448 — recount from the source, do not trust this number). That
is a **name-to-name index, not a second copy of key names**, and it is cross-pinned by G4-A.

### 2.2 Refusal status: `SRMECH_ERR_BAD_INPUT` (= 2). Never `SRMECH_ERR_NOT_IMPL`.

Full enumeration is `c/include/srmech.h:419-470`. The reasoning, once:

- **`BAD_INPUT` (2)** — "malformed input bytes / state". An unknown key IS malformed against the
  grammar. **Chosen.**
- **`NOT_IMPL` (5) is the trap.** In *both* runners it is the **defer-to-pure channel**:
  `srmech_dsl_chain_run.c:534` ("An op NOT here → the caller defers the whole chain to pure"),
  `:564`, `srmech_compose_run.c:1340`, `srmech.h:3360` (rc103 inform-don't-limit). Returning it for
  an unknown key would say *"this projection doesn't do it yet; the other one might"* — false on a
  bare-C host, where nothing will ever implement `max_denominatr`. **It would be rc447's
  divergence-only shape re-implemented inside C**, with only the constants moved.
- **`LIMIT` (8)** is scoped by rc404 to a bound *growing the caller's buffers cannot relieve*.
  Reusing it blurs the exact distinction rc404 was minted to sharpen.
- **`INTERNAL` (6)** blames the library; the library is fine, the *caller's declaration* is
  malformed. Reserved for one case only — see 2.2b.
- `NULL_ARG` / `IO` / `OVERFLOW` / `CANCELLED` are facially wrong.

**The tree already draws this exact line and already pins it.** `srmech_compose_run.c:1446-1452`:
*"NOT_IMPL — a recognised form this projection does not yet run — is deliberately distinct from the
BAD_INPUT that MIXED / NONE earn, which are malformed rather than unimplemented"*, pinned at
`c/test/test_srmech_chain_run.c:188-196` (`MAP` → `NOT_IMPL`, `MIXED` → `BAD_INPUT`). An unknown key
belongs on the MIXED side.

**Shape to copy, disposition NOT to copy:** `c/src/srmech_invoke.c:1580` `iv_no_extra_keys` already
walks `args->u.obj.keys[i]` against `e->params[j].name` and declines. Copy its *walk*. Do **not**
copy its `SRMECH_INVOKE_DEFER` disposition — that is correct only because its sole bare-C consumer
(`srmech_mcp.c:465`, `defer_calls=0`) converts it to an explicit MCP error. On the chain runners,
defer-on-malformed is the defect itself. (Note also: the rc447 commit's claim that there was *"no
in-tree pattern to copy"* is a grep artifact — `iv_no_extra_keys` does not match
`key_set|keyset|unknown_key|validate_keys`.)

**2.2b — registry lookup failure is `SRMECH_ERR_INTERNAL`, never silent acceptance.** If
`srmech_tool_registry_find` returns NULL for an op the dispatch table *does* run, a library
invariant is broken. Falling through to "accept" would let one typo in the Surface-A name index
silently disable the validator for that op forever while every other op's tests stay green. See §6.2.

**2.2c — corollary that binds the tests.** Python collapses every non-OK to `_NATIVE_MISS`
(`python/srmech/dsl/_chain.py:568`; `python/srmech/cascade/compose.py:1253-1254`), so **a gate
asserting only `rc != SRMECH_OK` cannot tell a refusal from a deferral** — the same blindness as the
divergence-only fix. Every bare-C row asserts the **literal status value**; the ctypes gate reads
`rc` *before* the collapse.

### 2.3 ABI: bump `SRMECH_ABI_VERSION` 18 → 19. `SRMECH_GENOME_FORMAT_VERSION` stays 20.

The rule, quoted verbatim from `c/include/srmech.h:70-75`:

> ```
> /* ABI version. Bumped in lockstep with the Python shim's
>  * EXPECTED_ABI_VERSION whenever the wire format of any exported
>  * function changes. Adding a NEW symbol does not bump ABI; changing
>  * an existing signature does; and — stated explicitly since rc287,
>  * because its absence here is what let a removal ship unbumped through
>  * a first review pass — REMOVING an exported symbol ALWAYS bumps.
> ```

No symbol is added, none removed, no signature changes shape. The bump rests entirely on the status
reinterpretation, and the header itself supplies both premises:

- `srmech.h:414-417` — *"Non-zero values are stable across patch releases and **form part of the
  wire contract** with the Python ctypes binding."*
- `srmech.h:219-221` (v12/rc404) — *"The status block below states outright that non-zero values
  'form part of the wire contract with the Python ctypes binding', so reinterpreting one **IS** a
  wire-contract change."*

**A "do NOT bump" reading was raised in cost round 3** on the ground that v12/v14 reinterpreted a
*documented* contract while this refuses input the header never promised to accept. **It is
overruled by the tree's own precedent, read at head.** `srmech.h:307-311`:

> ```
>  *  v16 (v0.9.0rc439, `#T1140`) is the FOURTH bump of the v10 / v12 / v14 kind —
>  *      no signature changed shape, but the STATUS an existing exported function
>  *      returns for a class of input did. Through rc438
>  *      `srmech_genome_centromere_of` returned SRMECH_OK on a strand carrying two
>  *      or more 0x58 centromere caps; it now returns SRMECH_ERR_BAD_INPUT ...
> ```

v16 is precisely a **new refusal on never-promised input**, and it bumped. There is no
counter-precedent: all five "does NOT bump" clauses in the header (`:3071`, `:4352`, `:6585`,
`:7852`, `:7872`) concern *adding a symbol*.

v16's operational argument transfers word for word (`srmech.h:337-341`): *"a stale rc438 `.so`
reports ABI 15 and would otherwise load into rc439 Python. rc439 Python refuses before it dispatches,
so the Python answer would still be right — **but a bare-C host on the stale lib gets the silent
blend with no signal at all, and the projections are co-equal.** Rejecting the stale lib is the only
safe read."* Substitute "rc449 Python defers at `_then_native_desc`" and it is this rc verbatim. The
ABI pin is the **only** mechanism that catches a stale lib here, because Python's `_NATIVE_MISS`
collapse makes the C refusal invisible on the front door.

**`SRMECH_GENOME_FORMAT_VERSION` stays 20**, three ways: `grep -c GENOME_FORMAT
c/src/srmech_dsl_chain_run.c` → **0** (no contact, the DSL runner never touches a strand byte); the
header's own coupling test is *"Only the manifest format_version moves"* when the on-disk body gains
a byte or marker (`:6860-6863`), and nothing here writes a byte; and v16 — a refusal *on a genome
read*, far closer to storage than this — held the format version (`:342-344`).

---

## §3 FILES TO TOUCH — with JPL headroom visible

JPL caps: Rule 4 = **60 lines**, Rule 5 = **≥2 asserts**, Rule 1 = no goto / **no novel recursion
cycle** (`CEIL_RULE_1_RECURSION = 9`, seeded down-only), Rule 3 = no malloc. Counts below are from
the tree's **own** scanner (`python/tests/test_jpl_audit.py::_scan_functions`, literal-masked as of
rc441), cross-checked by line arithmetic; both agree on every target. **None of these functions is
in `RULE_5_EXEMPT_FUNCTIONS`, `RULE_4_SEEDED_OVER_CAP` (12 entries) or `RULE_5_SEEDED_UNDER_MIN`
(2) — all strict, no seeded allowance to hide in.** A NEW helper gets no seed either: ≤60 lines and
≥2 asserts from its first commit.

### 3.1 `c/src/srmech_dsl_chain_run.c` (1064 lines) — Surface B, the subject

| function | span | lines | asserts | R4 headroom |
|---|---|---|---|---|
| `dsl_leaf_dispatch` | `:537-565` | 29 | 2 | **31** |
| `dsl_run_stage_array` | `:814-846` | 33 | 2 | 27 |
| `leaf_reorient` | `:305-330` | 26 | 2 | 34 |
| `leaf_best_rational` | `:362-387` | 26 | 2 | 34 |
| `dsl_run_combinator` | `:785-809` | 25 | 2 | 35 |
| `dsl_stage_is_combinator` | `:635-647` | 13 | 2 | 47 |

**The mechanism to fix, named exactly.** Every leaf reads kwargs by *pull* —
`srmech_json_object_get(stage, "orientation")` at `:308`;
`srmech_json_object_get(stage, "max_denominator")` / `"fine_scale"` at `:366-367`. **Nothing ever
enumerates the stage object's keys**, and there is no code path that "drops" a key — the drop is the
*absence of an iteration*. Worse, **5 of the 7 leaves never receive `stage` at all**:
`leaf_magnitude` (`:292`), `leaf_pin_slot` (`:348`), `leaf_chiral_flip` (`:454`),
`leaf_net_chirality` (`:473`), `leaf_autocorrelation` (`:500`) take `(b, in, out)` only. For those
five, every kwarg is structurally unreachable. **The check therefore MUST live at dispatch, not
inside the leaves.**

**Placement:** a new `static` validator called from `dsl_leaf_dispatch` (31 lines of headroom) after
the op name is known and before the arm is taken. `dsl_leaf_dispatch` already receives `stage`
unchanged (`:839` passes the whole stage object by pointer). **The validator must be a flat key
walk — it must NOT re-enter `dsl_run_stage_array`**: `("dsl_run_combinator", "dsl_run_loop",
"dsl_run_stage_array")` is a **seeded Rule-1 recursion cycle** (`test_jpl_audit.py:207`), down-only
and strict-on-novel, so a validator that re-enters the stage runner mints a new cycle and fails CI.

The stage's legal key set is `{"op"} ∪ params[1..]`. Reserved combinator discriminators are a
separate closed set of 7, already a static array at `:637-639`
(`loop_n`, `sub_chain`, `fold_init`, `fold_op`, `reduce_op`, `parallel_body`, `map_op`) — a stage
that `dsl_stage_is_combinator` claims never reaches `dsl_leaf_dispatch`, so combinator keys are
**out of scope** for this validator (see §5, `combinator-stage-key-sets`).

Whole leaf key vocabulary on Surface B, for reference: **three strings** —
`orientation` (`reorient`), `max_denominator` + `fine_scale` (`best_rational_signed`). Five of seven
leaves accept **zero** kwargs.

### 3.2 `c/src/srmech_compose_run.c` (1609 lines) — Surface A

| function | span | lines | asserts | R4 headroom |
|---|---|---|---|---|
| **`cr_dispatch`** | `:1090-1146` | **57** | 2 | **3** ⚠️ |
| `cr_run_steps` | `:1413-1459` | 47 | 2 | 13 |
| `cr_dispatch_real` | `:1069-1088` | 20 | 2 | 40 |
| `cr_step_form` | `:1307-1324` | 18 | 2 | 42 |
| `cr_run_plain` | `:1400-1410` | **11** | 2 | **49** |
| `cr_arg` | `:395-404` | 10 | 2 | 50 |
| `cr_op_is` | `:1058` | — | — | — |

⚠️ **`cr_dispatch` is at 57/60. NOTHING goes inside it.** It is a 16-arm `if`-chain; a per-op key
check added inline breaks Rule 4 immediately. Note that `cr_dispatch_real` exists *only* because
`cr_dispatch` already had to be split for Rule 4 once (comment at `:978-981`) — this would be the
second time the same function hits the cap. **Place the call in `cr_run_plain` (49 lines of
headroom)**, which already pulls `args` (must be `JSON_OBJECT`) at `:1403-1408` and hands the whole
object to `cr_dispatch` at `:1409`. Validate `args` keys *before* the dispatch call.

Also here: the static op-name → registry-full-name index (§2.1), placed as `static const` .rodata
beside the existing `map_k`/`fold_k`/`plain_k` (`:1309-1312`) and `dotted[21]` (`:1331`).

**Scanner caveat that bites this file.** `_scan_functions` double-reports two-line forward
prototypes (measured: `dv_from_desc` at 22 *and* 37; `dv_to_desc` at 23 *and* 28 — the smaller is
the prototype whose brace look-ahead lands on the next function). No target above is affected, but
**a new two-line forward prototype inherits the artifact** — declare the helper above its first use
instead.

### 3.3 `c/test/test_srmech_chain_run.c` (208 lines, 17 checks) — EXTEND, never replace

The ADR-0003 bare-C proof. Includes are `srmech.h` + `<stdio.h>` + `<string.h>` only (`:17-20`) —
no Python, no ctypes. Assert mechanism is a runtime `check(int cond, const char *desc)` with
`static int g_pass/g_fail` (`:22-29`), so it is a real value check under Release/NDEBUG, which is how
CI builds. Exit contract at `:206-207`. `static unsigned char ws[8u << 20]` at `:44` is the one
file-scope 8 MiB arena (JPL Rule 3).

⚠️ **This file drives `srmech_chain_run` (compose) and touches the D1 surface ZERO times.** Verified:
`srmech_dsl_chain_run` appears in it not at all. Add a **`run_dsl(desc, seed, out, cap)` helper**
beside `run_chain` (`:33-56`), sized by `srmech_dsl_chain_run_arena_bytes` (≈1,242,880 B at
(200,40); the existing 8 MiB `ws` covers it — **reuse it, do not add a second arena**). That helper
is what finally puts the shipped bare-C proof on the surface the finding was filed against.

⚠️ **DO NOT create a new `c/test/test_srmech_*.c` file.** `python/tests/test_c_test_wiring_rc356.py:61`
sets `CEIL_UNWIRED_C_TESTS = 20`, **down-only**; measured now: 38 test files, 18 registered → exactly
**20 unwired, sitting on the ceiling**. A 39th unwired file makes it 21 and turns that gate red. A
new file would have to land with `add_executable` **and** its name in the `foreach` in the same
commit. Extending this file moves nothing and is free.

### 3.4 Python

| file | edit | why |
|---|---|---|
| `python/srmech/dsl/_chain.py` | `_op_accepts` (`:113`) must exclude the **first positional** parameter when judging a *stage kwarg* | closes the 7/7 data-param residual (§1 D3). Keep the existing `**kwargs` / unreadable-signature → `True` behaviour. |
| `python/srmech/cascade/compose.py` | `_chain_c_eligible` (`:1079`) gains the missing key-set check against the op signature | today it gates on `on_error` + membership in `_RUN_C_OPS` (21 ops, `:1000`) and never compares `step.args` keys to the signature — there is **no `_op_accepts` equivalent anywhere on this path**, and `_run_chain_native` is tried FIRST (`:1356`) |
| `python/tests/test_t1146_rejection_parity_rc447.py:32-35` | **rewrite** | it says *"There is NO key-set validator anywhere in the C leaf surface, so there was no in-tree pattern to copy and none is added here"*. That becomes false the moment this rc lands, and it ships in the tree. `[[feedback_fix_falsehoods_when_found_latency_by_surface]]` binds it to the current rc. It was also already wrong about "no in-tree pattern" (§2.2). |
| `python/tests/test_t1158_refusal_set_equality_rc449.py` | **new** | G3, §4 |
| `python/tests/test_t1158_registry_param_order_rc449.py` | **new** | G4, §4 |

### 3.5 Version + ABI ripple — **bump FIRST, then run gates**

**Version SSoT, five files that must agree** (rc448 → rc449): `python/pyproject.toml`,
`python/pyproject-pure.toml`, `python/srmech/version.py`, `c/include/srmech.h` (`SRMECH_VERSION_PRE`
at `:67` + `SRMECH_VERSION` at `:68`), `python/tests/test_signal_processing_scaffolding.py` (the hard
pin). **Plus two gated currency surfaces:** `test_notebook_currency_rc420` (every "Live at rcNNN"
stamp) and `test_readme_currency_rc419` (the worked `native_status()` transcript). Plus a
`python/CHANGELOG.md` entry.

**ABI 18 → 19 ripple: 29 gated/declaration sites across 22 files.** Regenerate the list, do **not**
work from rc447's `notes/ripple_gates.txt` — it is measured to miss two sites and over-count two:

```
grep -rnE "(NATIVE_ABI_VERSION|EXPECTED_ABI_VERSION) *== *18|\"expected_abi\"\] *== *18|SRMECH_ABI_VERSION 18|EXPECTED_ABI_VERSION: *int *= *18|\*\*ABI 18\*\*|'abi_version': *18|'expected_abi': *18|SRMECH_ABI_VERSION\`? is 18|moves \*\*17" \
  --include=*.py --include=*.md --include=*.h . | grep -v '^\./\.claude/' \
  | grep -vE '^\./(python/CHANGELOG\.md|notes/|adr/)'
```

- **Declaration — 2 sites:** `c/include/srmech.h:384`, `python/srmech/_native/__init__.py:222`.
- **Gated test pins — 22 sites / 18 files** (hardcoded literal `18`, all under `python/tests/`):
  `test_bus.py:1020,1063` · `test_bus_cipher_transport_c_rc179.py:63` ·
  `test_bus_pubsub_c_rc180.py:73,78` · `test_cooccurrence_directed_rc248.py:101` ·
  `test_dsl_chain_c_rc181.py:71` · `test_dsl_combinators_c_rc182.py:116` · `test_eulerian_rc250.py:100` ·
  `test_genome_cap_foundation_c_rc196.py:58` · `test_genome_catalog_body_bound_rc337.py:656` ·
  `test_genome_group_v20_rc442.py:76` · `test_genome_multikernel_c_rc198.py:77` ·
  `test_genome_read_bound_global_rc342.py:769` · `test_graph_to_kernel_rc249.py:100` ·
  `test_introspect.py:663` · `test_json_read_selfhost_rc401.py:442` ·
  `test_klein4_regime_split_rc290.py:393,394` · `test_klein4_winding_preimage_rc438.py:358,365` ·
  `test_lightweight_parity.py:125`
- **Gated prose — 5 sites / 2 files:**
  - `python/README.md:162` — `**ABI 18** at this release` (`test_readme_abi_header_matches_the_live_abi`)
  - `python/README.md:164` — `SRMECH_ABI_VERSION moves **17 → 18** at **v0.9.0rc447**`. ⚠️ **This is a
    paragraph rewrite, not a digit edit** — it carries the whole bump rationale and names its own
    release. `test_readme_does_not_contradict_itself_about_abi` asserts `bump.group(2) == header ==
    EXPECTED_ABI_VERSION`.
  - `python/README.md:173-174` — the worked `native_status()` transcript, 2 lines
  - `srmech_research_notebook.md:5460` — ``Live at rc448: **`SRMECH_ABI_VERSION` is 18**``. ⚠️ **NOT in
    rc447's ripple ledger.** The gate that catches it (`test_notebook_currency_rc420.py:958`)
    shipped *in* rc447; its own docstring records that rc447's stamp read "is 17" in the very
    release that bumped 17 → 18.
- **DO NOT touch — historical statements that stay TRUE at 19:**
  `python/srmech/cascade/compose.py:1166` and `python/tests/test_c_real_carrier_rc447.py:12` both say
  `ABI 17 -> 18`. rc447's ledger counted them as ripple; they are not.

**Three ABI claims are ALREADY STALE at head — rc447 bumped and did not carry them. Repair in this
rc:**

1. `docs/srmech/CLAUDE.md:662-663` — *"C ABI version is currently **17**"*. Live is 18. This is the
   narrative ABI SSoT and its own parenthetical enumerates five prior lags (*"said 12 until rc420,
   13 until rc425, 14 until rc438, 15 until rc439 and 16 until rc442 — one bump behind on each
   occasion"*). rc447 made it a **sixth**; leaving it makes rc449 a **seventh**. Ungated.
2. `c/README.md:56` — *"C ABI version is **17**"*. Live is 18. Its own note reads *"No gate covers
   `c/README.md` at all, which is exactly why it drifted the furthest."* rc442 repaired it 3 → 17;
   rc447 re-staled it five rcs later. **Not in rc447's ripple ledger at all.**
3. `python/tests/test_bus.py:1064` — the assertion *message* reads `"EXPECTED_ABI_VERSION should be
   15; got "` beside an assert of `== 18` at `:1063`. rc447 shipped
   `test_pinned_names_carry_no_value_rc447.py` for this defect class, but it parses **function
   names**, not assertion messages.

**Also pull the two ungated ABI-prose lines (1) and (2) under the currency-gate family in this rc.**
Six consecutive lags on `CLAUDE.md` is the textbook "ungated surfaces trickle; gated ones race to
100%" case, and it is cheap to close now.

(Low severity, same family, optional: `python/tests/test_notebook_currency_rc420.py:822` carries the
present-tense rationale string "the ABI is 13 today", stale by five.)

---

## §4 THE GATE SET — five gates, each with a planted-red proof and a discrimination control

> **An instrument that cannot return otherwise is not a measurement.** Every gate below is either
> already red at rc448 (the defect ships — that IS the planted defect) or is made red by a
> run-once-and-revert sabotage arm, recorded in `notes/` per
> `[[feedback_computational_provenance_discipline]]` before the fix commit.

### G1 — the bare-C refusal proof (ADR-0003: no Python, no ctypes in the process)

**Where:** extend `c/test/test_srmech_chain_run.c`. New `run_dsl` helper (§3.3). Update the tally
banner expectation (17 → 17+N).

**Rows — Surface B (DSL). Clean-before-dirty ordering is structural, not cosmetic (see G2.2).**

| # | stage (seed `0.3333333333333333` unless noted) | assert | proves |
|---|---|---|---|
| B1 | `{"op":"best_rational_signed"}` | `OK` ∧ value `(1,3)` | the seed reaches the leaf; baseline |
| B2 | `+ "max_denominator":2` | `OK` ∧ value `(0,1)` | a **legal** extra key is accepted **and USED** — the gate discriminates on key NAME, not key count |
| B3 | `+ "max_denominatr":2` | `== SRMECH_ERR_BAD_INPUT` | the wrong-number witness (rc448: `OK` `(1,3)`) now refuses |
| B4 | `{"op":"magnitude","bogus":1}`, float seed; clean twin first → `OK` 3.5 | `== BAD_INPUT` | zero-kwarg leaves are covered — the check lives at dispatch, not inside leaves that never receive `stage` |
| B5 | `{"op":"magnitude","x":5}` | `== BAD_INPUT` | `params[0]`, the data-carrier name, is NOT stage-legal (§2.1) |
| B6 | `{"op":"pin_slot_at_zero","orientation":-1}` | `== BAD_INPUT` | key sets are **per-op** — `orientation` is legal one leaf over |
| B7 | `{"op":"definitely_not_an_op"}` | `== SRMECH_ERR_NOT_IMPL` | the **defer channel is untouched** — refuse ≠ defer, pinned by value |
| B8 | `{"op":"reorient"}` (no `orientation`) | `== NOT_IMPL` | missing-**required** stays defer; the fix did not reclassify a neighbour |

**Rows — Surface A (compose), into the DECLINES block at `:177`:**

| # | chain | assert | proves |
|---|---|---|---|
| A1 | `gcd{a:@input.a, b:@input.b}`, inputs 12/18 | `OK` ∧ `strstr(out, "\"v\": \"6\"")` | control; also pins `params[*]` on this surface |
| A2 | `gcd{a,b,bogus:99}` | `== BAD_INPUT` | the D1 class on Surface A |
| A3 | `mod_add{a,b,n}` | `OK` | a 3-key declaration accepted where legal… |
| A4 | `gcd{a,b,n:5}` | `== BAD_INPUT` | …and refused where not. Same arity, same key names, different op — **per-op sets, not arity, not a global vocabulary** |
| A5 | existing rows `:177-204` | unchanged | MIXED → `BAD_INPUT`, MAP → `NOT_IMPL`, op-table miss, `NaN` all survive |

**Planted red:** B3/B4/B5/B6/A2/A4 all return `SRMECH_OK` against the rc448 library **today** —
measured, 10/10 malformed Surface-B probes and 5/5 Surface-A probes accepted and computed. Run the
extended test against the unfixed tree, capture the transcript into `notes/`, then fix.

**Sabotage arms (run once, revert, record):**
- point the validator at `params[*]` on Surface B → **B2/A3 go red**. This is the arm that catches
  "a gate that refuses everything scores a perfect zero."
- make the validator refuse unknown **ops** → **B7 goes red**. Proves the defer-channel pin bites.

### G2 — the discrimination controls (embedded in G1; listed so they cannot be dropped)

A refusal test that asserts "declined" passes when an arena overflow, a JSON parse error, an
op-table miss, or the *existing missing-required-key* check fires instead of the new validator. Four
mandatory controls:

1. **Status by VALUE, never `!= SRMECH_OK`.** Op-table miss and missing-required return `NOT_IMPL`;
   arena exhaustion returns `OVERFLOW`; only the validator (and JSON malformation) return
   `BAD_INPUT`.
2. **Minimal-pair attribution.** Every dirty row has a clean twin differing by exactly one key
   (B1/B3, B4's twin, A1/A2). Identical JSON syntax and seed; the twin runs `OK` to the correct
   VALUE **first**. If the twin is not `OK`, the dirty row is vacuous — this is not hypothetical:
   `magnitude` on an INT seed returns `NOT_IMPL` for unrelated carrier reasons, which is exactly why
   `best_rational_signed` is the primary witness and `magnitude` rows use a float seed.
3. **The legal-extra-key control (B2, A3).** Separates "refuses unknown keys" from "refuses keys".
   B2 additionally asserts the legal key was *used* — the value moves `(1,3)` → `(0,1)`, not merely
   "still OK".
4. **The same-arity cross-op pair (A3/A4, B6).** Rules out any arity- or global-vocabulary
   shortcut: `n` is a real key in the tree's vocabulary and legal on `mod_add`; only a per-op set
   refuses it on `gcd`.

⚠️ **Existing refusals that are COINCIDENCES, not checks — do not mistake them for coverage.**
`reorient` without `orientation` declines only because `orientation` is *required* and its absence
trips the pre-existing missing-key path. Every leaf whose keys are *optional* (`magnitude`,
`autocorrelation`, `best_rational_signed`) sails through. **Unknown-key detection and
missing-required-key detection are disjoint defect classes.**

### G3 — refusal-set equality (the property rc447 left unproven)

**New file:** `python/tests/test_t1158_refusal_set_equality_rc449.py`. Skips without `HAS_NATIVE`
(the Windows host is `has_native=False`; CI's native job is authoritative).

**It must drive C via ctypes directly, NOT the Python front door.** `_chain.py:568` and
`compose.py:414/:1227/:1253` collapse every non-OK to `_NATIVE_MISS` → pure. Through the front door
refusal and deferral are indistinguishable, and the instrument would have exactly the blindness it
exists to remove. ctypes is legitimate here: the ADR-0003 claim is carried by G1, not G3.

**Corpus GENERATED, not hand-picked.** D1 was missed by *case selection* —
`python/tests/test_dsl_chain_c_rc181.py` has a real forced-pure arm (`_no_native`) and simply never
fed an invalid chain. Nothing structural stopped it.

- Op sets pinned as literals **and cross-checked against the C source text** (the
  `test_combinator_kernel_closure.py:137-159` pattern): the 7 DSL leaf names from
  `dsl_leaf_dispatch`; the compose ops from `_RUN_C_OPS` (`compose.py:1000`).
- Per op, legal set = `inspect.signature(lookup_cascade_op(name))`, minus param 0 on Surface B.
- Probes per op: (i) clean; (ii) each legal key present-and-correct; (iii) each legal key with its
  last character dropped (the measured witness class); (iv) `+ bogus_t1158`; (v) `+` one key legal
  on a *different* op; (vi) `+` the param-0 name as a kwarg (Surface B only).
- **Verdict equivalence, bidirectional, every probe:** pure-projection call raises `TypeError` ⟺ C
  returns `BAD_INPUT`; pure computes ⟺ C returns `OK`. **Verdicts, NOT values** — pure-vs-C value
  parity for `autocorrelation` diverges in 8 of 9 cases by up to 2.0 and is separately filed
  (ledger row `parity_tests_are_tautological_for_native_dispatched_ops`); importing it here would
  entangle a pre-existing finding with this rc's claim.
- **Every `NOT_IMPL` must be CLASSIFIED.** A C `NOT_IMPL` is legal only if the probe is in an
  explicit, commented defer-allowlist (unknown op; missing required key; carrier shapes C declines).
  An unclassified `NOT_IMPL` **fails** the gate.
- **Anti-vacuity floors:** per-op corpus ≥ 3; total refusal-expected ≥ 20; acceptance-expected ≥
  number-of-ops; and assert that this run actually observed ≥1 `OK` and ≥1 `BAD_INPUT`. An empty or
  degenerate generator goes red, not green.

**Planted red:** every dirty probe is verdict-mismatched at rc448 (C `OK`, pure `TypeError`).
Capture the transcript once. Durable red: the anti-vacuity floors.

### G4 — source-of-truth drift gates

**G4-order** (new, `python/tests/test_t1158_registry_param_order_rc449.py`): for every registry
entry, `params[i].name` equals the i-th parameter of `inspect.signature(...)` in **order**. The
existing rc13 and rc408 gates pin **set** equality only, and `params[0]`-is-the-data-arg is an
**order** assumption.

**Planted red, free:** **8 of 660 entries are same-set-but-reordered today** —
`srmech.biology.genome.chromosome`, `.mint`, `.genome`, `.genome_save`, `.mint_strand`,
`.genome_from_graph`, `srmech.math.hdc.polar_random`, `srmech.cascade.parallel_sector_dispatch`. The
gate is red on first run against the untouched tree. Repair the 8 in the same commit; if any repair
turns out to be load-bearing elsewhere, ship a **down-only ceiling** instead and say so — do not
weaken the gate. None of the 8 is a C leaf *yet*, which is precisely the point: drift here is
demonstrably routine.

**G4-A** (Surface-A name index, in the same new file or beside it): parse the static op-name →
registry-full-name index out of `c/src/srmech_compose_run.c` textually (same
`test_combinator_kernel_closure.py:137-159` pattern), then assert for each entry (a) it resolves in
the registry, and (b) its param name-set equals `inspect.signature` of the op that
`compose._resolve_step_op` actually binds. **Planted red:** misspell one index entry, observe red,
revert. This is the gate that catches §6.2.

### G5 — does it actually run in CI?

**Yes, with three stated conditions. Measured, not assumed.** `#T1036`'s old claim ("ctest finds NO
tests") is **REFUTED at head** — it was true at rc355 and fixed by rc356 (`#T953`).
`docs/srmech/CMakeLists.txt` calls `enable_testing()` inside the `if(SRMECH_PEDANTIC)` block,
registers 18 `add_executable` targets and closes with a `foreach(t ...) add_test(...)`. Verified
empirically: `ctest -N` lists `Test #18: test_srmech_chain_run`, `Total Tests: 18`; built and run on
this host (MSVC 19.31, Release) → `17 passed, 0 failed`, exit 0.

The runner is `.github/workflows/srmech-ci.yml`, job `pedantic-build` (`:877`, name at `:897`,
`timeout-minutes: 12` at `:900`, matrix `[ubuntu-latest, macos-14, windows-latest]`,
`fail-fast: false`):

```yaml
:908  - name: Configure with SRMECH_PEDANTIC=ON
:910    run: cmake -S . -B build -DSRMECH_PEDANTIC=ON -DCMAKE_BUILD_TYPE=Release
:914  - name: Build (warnings = errors)
:925  - name: Run C tests (ctest)
        run: ctest --test-dir build --build-config Release --output-on-failure
```

Conditions, stated honestly so the rc does not over-claim:
1. Extending the existing file → runs everywhere the current proof runs. A new file must be wired in
   the same commit or the 20/20 ceiling goes red (§3.3).
2. **C tests run ONLY under `SRMECH_PEDANTIC=ON`** — never in the wheel builds of
   `srmech-publish.yml`. This is the only job in the repo that runs C tests; grep for
   `make|Makefile|ctest` across the three srmech workflows returns only lines 910/914/923/925.
3. `c/Makefile:89-111` globs all 38 test files, but **no workflow invokes make** — it is the
   local/WSL2 path only. Local verification runs there (numpy-absent, `/mnt` paths); **CI is
   authoritative**.

No `|| true` — pinned by `python/tests/test_c_test_wiring_rc356.py:162-181`, which also asserts
`ctest` appears in the workflow at all.

---

## §5 SCOPE — every item with an ADR-0009 §5 disposition

### IN rc449 — `CLOSED_IN_THIS_RC`

| # | item | disposition |
|---|---|---|
| S1 | **F6** — DSL leaf unknown-kwarg refusal in `dsl_leaf_dispatch`, `{"op"} ∪ params[1..]`, `BAD_INPUT` | CLOSED_IN_THIS_RC |
| S2 | **F-1** — compose `args` unknown-key refusal in `cr_run_plain`, `params[*]`, `BAD_INPUT` + the ≈20-entry name index | CLOSED_IN_THIS_RC |
| S3 | **ABI 18 → 19** + the 29-site ripple + 3 stale-site repairs + gating the 2 ungated ABI-prose lines | CLOSED_IN_THIS_RC |
| S4 | **Registry param-ORDER gate** + repair of the 8 reordered entries | CLOSED_IN_THIS_RC |
| S5 | **`_op_accepts` param-0 residual** (7/7) + the `_chain_c_eligible` key check | CLOSED_IN_THIS_RC (claim scoped per §1 D3) |
| S6 | **Bare-C proof extended** to the D1 surface via `run_dsl` + all G1 rows | CLOSED_IN_THIS_RC |
| S7 | **rc447 confession repair** at `test_t1146_rejection_parity_rc447.py:32-35` | CLOSED_IN_THIS_RC |
| S8 | **Pre-merge blast-radius measurement** (below) | CLOSED_IN_THIS_RC |

**S8 — the pre-merge measurement, currently UNMEASURED and mandatory.** Run every packaged
`cascade_catalog` descriptor (20) and every chain fixture in the suite through both new validators
under WSL2. Expected clean, because they all pass Python's `parse_chain_spec`. **Any refusal is a
shipped-descriptor defect to be fixed in this rc — never a reason to loosen the validator.** This is
the one number nobody has: no census of shipped descriptors against these key sets exists.

### FILED — `FILED_AS_NEW_ITEM`

Each gets a ledger row in `notes/_1653_gap_ledger.ndjson` with its measured bare-C probe attached.

| id | item | reason for deferral | named cost |
|---|---|---|---|
| **F2** | genome attestation overlay accepts unknown keys / non-string values / a non-object root and silently writes srmech's DEFAULT provenance (`srmech_genome.c:726`, 9 exports) | different mechanism; Python's behaviour on a non-string value for a **known** key is unmeasured; mirroring must be exact, not invented | ABI 19 → 20 later. **HEAD ITEM FOR rc450** — highest stakes in the sweep (a durable wrong provenance record from the op whose purpose is provenance honesty). Must not trickle. |
| F1 | compose `class` key never read: not presence, not A-N validity, not op/class agreement (`cr_run_plain`) — while the C **parse** peer `co_build_step:287`/`co_class_valid:300` validates exactly this | different class (required-key + enum), and C's compose parse peer is already *stricter* than Python in the reverse direction (rejects v2 fold/map forms) — untangling that is its own adjudication | rides the same later bump as F2 |
| F8 | chain-head `name`/`summary`/`returns` unchecked in `cr_run_steps:1413` while `co_chain_head:325` checks them | same class as F1; fold into F1's fix | — |
| F5 | DSL multi-discriminator stage silently read as whichever arm tests first (`dsl_stage_is_combinator:635`, `dsl_run_combinator:785`) — `cr_step_form`'s `CR_FORM_MIXED` is the correct sibling and its own comment argues for it | different class (discriminator mutual exclusion); Python peer (`_toml_chain.py:232`) read not executed | — |
| F3 | `mc_build_fields:331` — supplied `[class]` field name not in the declared table is silently discarded | TOML-table mechanism, not JSON-object; refuse-vs-defer semantics unadjudicated on this surface | — |
| F4 | `mc_resolve_binds:350` — non-`binds` args keys silently dropped (literally D1 on the class-method surface); `mc_run_chain` additionally drops static kwargs that CHANGE the answer | as F3; and `mc_run_chain`'s variant is a *capability* gap wearing an acceptance costume | — |
| F7 | `mc_run_method:1747` — state routes tested in fixed order; a descriptor declaring two silently gets one | as F3; three lines beside F3/F4 when that surface is done | — |
| — | combinator-stage key sets (`{"loop_n":…, "sub_chain":…, "bogus":1}`) | **Python side unmeasured.** Measure first; close in C only what Python refuses; if Python also accepts, file as *symmetric laxity*, which is not a divergence | — |
| — | step-level unknown keys on Surface A (outside `args`) | **symmetric laxity** — `_parse_step` accepts them and `cr_step_form` accepts them. Closing only in C would mint the REVERSE divergence, invisible to the whole output-parity corpus | — |
| — | dotted-prefix over-permissive `cr_op_is` match (`totally.different.prefix.chiral_flip` runs) | already filed, deliberately deferred behind `#T1145`'s respelling | — |

### DECLINED — `DECLINED_WITH_REASON`

| item | reason |
|---|---|
| **F9** — `cat_descriptor_kind:670` reads only `[fetch].adapter` of an AMSC descriptor | **The Python peer's refusal is UNVERIFIED**, and the two ops have different contracts (the C op audits a supplied blob rather than registering a source), so it may legitimately not refuse. It cannot be called a divergence until measured. Declined as a *finding*, not as work: promote to FILED the moment the Python peer is measured. |
| **F-4** — `test_input_contracts_rc433.py:109` labels two **Python** functions "CO-EQUAL PROJECTIONS" (`bigq_reduce_c` is Python; no `srmech_bigq_*` symbol exists) | Real, but a docstring/claim repair in a different family. Declined for this rc to keep the change set attributable. |
| **tautological parity corpus** — 30/45 files with no forced-pure arm, 16/45 blind on both axes, 5/6 `test_cascade_*_parity.py` comparing against the test's own re-implementation rather than the shipped pure body | Already ledgered as `parity_tests_are_tautological_for_native_dispatched_ops`. rc449 adds refuse-parity rows for its own two surfaces only; it does not repair the corpus. |
| **`CEIL_UNDECIDED = 25`** reverse-direction divergences (`test_native_contract_parity_rc431.py:72`, sitting exactly on its ceiling; 22 are `genome_*_c` shape-predicate guards) | Under an existing down-only ceiling; unaffected by this rc; adjudicating them is a separate arc. |

---

## §6 ⚠️ HOW THIS RC COULD GO GREEN WHILE BEING WRONG — five named ways

Carried forward from both adjudications. Each has its countermeasure **already in scope**; if a
countermeasure is cut, the corresponding failure mode is live.

**6.1 Wrong index, all green.** A validator reading `params[*]` on Surface B passes every existing
test — well-formed stages never spell the data-param name — and ships the 7/7 data-param residual
still accepted. That is rc447's shape again, under a green gate.
→ **Countermeasure:** G1-B5 (`{"op":"magnitude","x":5}` → `BAD_INPUT`), shown returning `SRMECH_OK`
against the rc448 lib first. Plus the `params[*]` sabotage arm turning B2/A3 red.

**6.2 Registry-miss = silent acceptance.** If `srmech_tool_registry_find` returning NULL falls
through to "accept", one typo in the Surface-A name index silently disables the validator for that
op **forever**, and every test probing other ops stays green.
→ **Countermeasure:** NULL for a *dispatched* op is `SRMECH_ERR_INTERNAL`, never accept (§2.2b);
G4-A asserts every index entry resolves and matches its signature; RED proof = misspell one entry,
observe red, revert.

**6.3 Status-blind parity.** A gate asserting `rc != SRMECH_OK`, or merely that "both projections
refuse", cannot tell `BAD_INPUT` from `NOT_IMPL` — and `NOT_IMPL` would be the divergence-only fix
rebuilt *inside* C, with Python's `_NATIVE_MISS` collapse hiding it completely.
→ **Countermeasure:** literal status-value assertions on every bare-C row (G1-B3/B7/B8 are the
triad); G3 reads `rc` before the collapse and classifies every `NOT_IMPL`.

**6.4 A gate that refuses everything scores a perfect zero.** A validator that declined all stages
would pass every refusal row and would have deleted the C path.
→ **Countermeasure:** every refusal row ships with its control returning `OK` **and the correct
VALUE** (G2.2, G2.3); the `params[*]`/empty-set sabotage arm demonstrates B2/A3 can go red.

**6.5 Stricter-than-Python green.** A validator that closes step-level or combinator keys Python
accepts makes bare-C hosts refuse chains Python users run fine — **invisible to the entire
output-parity corpus** (30/45 files have no forced-pure arm).
→ **Countermeasure:** G3 runs both directions per surface (C refuses ⇔ forced-pure raises); the
combinator-key and step-key questions are explicitly OUT of scope until Python is measured (§5).

**Secondary — the ripple can go tree-green while wrong.** `c/README.md:56` and
`docs/srmech/CLAUDE.md:662-663` are ungated and already stale at 17; the tree passes with them
wrong. Six consecutive lags on the latter is the measured cost of leaving them ungated — this rc
gates them (§3.5). And a new **two-line forward prototype** in either touched C file inherits the
`_scan_functions` double-report artifact, confusing the JPL scanner's line attribution — declare
helpers above first use.

---

## §7 COST PER SLICE — the cut line, visible

Effort is engineer-hours for someone working from this brief. Risk is the chance the slice needs
rework after CI.

| slice | effort | risk | drop it? |
|---|---|---|---|
| **S1** DSL validator + registry lookup helper (`dsl_leaf_dispatch`, 31 lines headroom) | 2–3 h | **low** — pull-model is fully mapped; 3-string vocabulary; no arena, no ABI symbol | **NO — it is the rc** |
| **S6** bare-C `run_dsl` helper + 8 B-rows + 5 A-rows | 2–3 h | **low** — extending an existing wired file; RED already measured | **NO — without it the rc claims nothing provable** |
| **S2** compose `args` validator + ≈20-entry name index + G4-A | 3–4 h | **medium** — `cr_dispatch` at 57/60 forces placement in `cr_run_plain`; the index is a new artifact needing its own cross-pin | **Droppable.** If dropped: rc449 closes Surface B only, the ADR-0003 proof still touches its own surface, and S2 files as FILED_AS_NEW_ITEM riding a later bump. Say so explicitly in the PR body. |
| **S4** param-order gate + 8 repairs | 2 h | **medium** — the 8 repairs may ripple into other name-sensitive gates; fall back to a down-only ceiling | **NO if S1 ships** — `params[1..]` rests on order. Dropping S4 leaves S1's premise ungated. |
| **S5** `_op_accepts` param-0 + `_chain_c_eligible` key check | 1–2 h | low | Droppable (§1 D3) — but then do not claim the residual closed |
| **S3** ABI bump + 29 sites + 3 stale + README paragraph + notebook stamp + gate 2 prose lines | 2–3 h | **medium** — mechanical but wide; rc447's ledger is measured wrong in three ways, so regenerate | **NO — forced by precedent** (§2.3) |
| **G3** refusal-set equality harness (generated corpus, floors, classification) | 3–4 h | **medium** — corpus generation is where vacuity hides; the floors are the defence | **NO — it is the property rc447 lacked** |
| **S7** confession repair | 15 min | none | NO |
| **S8** blast-radius census of 20 shipped descriptors + fixtures | 1 h | **unknown** — the one unmeasured number in the rc | **NO — must run before merge** |
| version bump + CHANGELOG | 30 min | low | NO |

**Total: roughly 17–23 h with S2, 13–18 h without.** The natural cut line is S2 (± S5). Everything
above S2 in the table is load-bearing for the rc's claim.

**Execution order (dependencies are real):**
1. Version bump rc448 → rc449 across the five SSoT files **first**, then the currency stamps — bump
   before running gates or the pin passes spuriously.
2. Run the extended G1 rows against the **unfixed** tree; capture the all-`SRMECH_OK` transcript to
   `notes/`. This is the planted-red record.
3. Run G4-order against the unfixed tree; capture the 8 failures.
4. S4 (order gate + repairs) — S1 depends on it.
5. S1, then S6-B rows. Then S2, then S6-A rows and G4-A.
6. G3.
7. S5, S7.
8. S3 ABI ripple. Re-grep; do not work from `notes/ripple_gates.txt`.
9. S8 blast-radius census.
10. Sabotage arms (6.1, 6.2, 6.4 in §6), each run-once-and-revert, each recorded.
11. WSL2 foreground gate run (numpy-absent, `/mnt` paths). CI is authoritative.

---

## §8 WHAT THIS RC EXPLICITLY DOES **NOT** CLAIM

1. **NOT "C rejection parity is closed."** Closed: the unknown **op-argument-key** class on the two
   chain interpreters. Open and filed: compose `class`-key/op agreement (F1), chain-head keys (F8),
   DSL multi-discriminator MIXED (F5), genome attestation unknown-key overlay (F2), make_class
   fields/args/routes (F3/F4/F7), the dotted-prefix over-permissive match, F9.
2. **NOT "a bare-C host cannot compute a malformed declaration."** Only the key-NAME class is
   closed. Wrong-TYPE values, class/op mismatch, and multi-discriminator stages still compute.
3. **NOT value parity.** The pure-vs-C `autocorrelation` divergence (8/9 cases, up to 2.0 absolute)
   and the 16 doubly-blind parity files are pre-existing, filed, and untouched.
4. **NOT "the parity-harness corpus is fixed."** G3 adds one non-tautological harness for two
   surfaces. The 30-of-45 no-forced-pure-arm census stands.
5. **NOT** the 25 reverse-direction `CEIL_UNDECIDED` divergences — unaffected, still at ceiling.
6. **NOT** CI coverage beyond the `pedantic-build` job. C tests do not run in wheel builds, and no
   workflow invokes `c/Makefile`.
7. **NOT** the `_op_accepts` param-0 residual as the thing that closes the gap. The **C refusal**
   closes it; the Python edit stops the IR builder emitting a stage it knows is doomed. If S5 is
   cut, say the residual is open.
8. **NOT** "the projections now agree" as the headline. The headline is: **C refuses what it should,
   on the host where Python does not exist.** G1 states it; G3 proves both sides state the same
   thing.

---

## §9 HOST NOTES (so a false finding is not reported)

- The Windows host has `has_native=False` and only **stale `build_rc342..rc355`** libraries on disk.
  Any script re-verifying symbols against a live library there reports **every** symbol absent. That
  is the host, not the tree.
- Builds and tests needing the native library run under **WSL2** (`/mnt` paths, `python3`,
  numpy-absent). An ad-hoc probe compile of `srmech_platform.c` needs `-std=gnu11` (`TIME_UTC` is
  undeclared under `-std=c99`) — a probe-flag detail, not a tree defect; the tree's CMake is fine.
- `-DCMAKE_BUILD_TYPE=Release` is ignored by the multi-config MSVC generator (CMake prints
  *"Manually-specified variables were not used"*); `--config Release` on the build/ctest steps is
  what selects it.
- **`git add -A` is UNSAFE in this repo** (~35k untracked non-ignored files). Stage explicit paths.
- **Reference notation binds four surfaces**: file content (including docstrings and `ToolEntry`
  prose, which ship in the wheel), commit messages, the PR body, and **the PR title** (it becomes
  the merge-commit subject). Local task ids are `#T1158`, never bare. `#1653`, `#1654`, `#1658` are
  real GitHub objects and are correct bare.

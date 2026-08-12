# ADR-0012: The introspect surface IS the API contract — autonomous composition, not documentation

**Status:** 🟢 **Implementing** — direction accepted (user direction 2026-07-30, *"mark adr12
accepted"*), execution arc **OPEN**. Everything below is in force; the ADR stays revisable in
place until its shape has settled. (v0.9.0rc415, `#T1098`: the 2026-07-30 header read
`🟢 **ACCEPTED**`, a pair the legend at `README.md` does not define — 🟢 is *Implementing*.
Held at 🟢 by user direction: proceeding with ADR-0013 and the queue may surface more, and the
C5 correction at rc414 plus C6's still-open status are what that reasoning predicted.)

**What acceptance rests on.** The criterion was: *every clause has an instrument that can return
otherwise, proven by injection.* At acceptance — **C1, C3, C4, C5 and C2's param half were recorded as
gated**, each with an injection proof, all three rc363 gates strict-zero with **no CEIL** (possible only
because every residual they found was fixed rather than ceilinged).

> ⚠️ **C5 was NOT gated at acceptance, and this sentence was wrong when written** (corrected
> v0.9.0rc414, `#T1092`). C5 had no instrument at all — §3.3's instrument table lists C2, C3 and the
> prose op-refs, and C5 is absent from it; `grep -rn "C5\b" tests/*.py` matched only an unrelated,
> differently-numbered clause set in `tests/test_codon_read_rc314.py`. The clause was refuted by
> execution on its own marquee exhibit at rc411/rc413. It acquired a real instrument
> (`tests/test_wire_round_trip_rc414.py`) and passed it in rc414; see §3.1 C5 for the reproduction and
> the argument. **Two other sentences in this document repeated the same false claim and are corrected
> in place: §7.3 and §12.** The correction is left visible rather than silently rewritten, because "an
> ADR sentence asserting a clause is gated" turned out to be the only evidence anyone had that it was.

**Two clauses are ACCEPTED AS DECLARED-OPEN, not
as satisfied**: **C2's return half** (no second channel exists; §6.3 declines the only available
surface, and closing it needs a typed element-carrier field this ADR deliberately does not specify) and
**C6** (stated, argued and measured in §3.4; implementation assigned to its own rc by user direction).
Per §3.2 the sin is treating a preference as a clause **silently** — these two are labelled, and a
future rc that closes either should amend this block rather than quietly assume it.

**Why accepted with two open.** The implementation **corrected this draft twice** (§3.3) — the C2
clause as literally written was too noisy to ship, and the C3 baseline had been measured on the very
channel C3 exists to distrust. Both corrections are recorded here rather than silently applied. A
design that survives contact and records where it was wrong is the opposite of the early-botch risk
acceptance was deferred to avoid.

*(The README legend spells this status ✅ Accepted; the 🟢 marker follows ADR-0010's usage. Was 🟡
PROPOSED from 2026-07-30 until the rc363 instruments landed the same day.)*
**Clauses:** audited.
**Date:** 2026-07-30. **Amended 2026-07-30 (rc363)** — see §3.3.
**Implemented before accepted, on purpose.** User direction 2026-07-30: *"adr12 implement as proposed
tell us when to mark accepted. might seem backwards but I don't want follow up adr to fix it if we
botch a design choice early."* v0.9.0rc363 therefore builds the **instruments** for C2, C3 and the
prose op-ref gate while the ADR stays PROPOSED, so every clause is proven enforceable before it becomes
canon. §3.3 records what the build measured — including **two places this draft was wrong**. Nothing
here is in force yet; §3.3 is the evidence for the acceptance decision, not a claim that it has been
made.
**Authors:** Steven Kirkland + Claude Opus 5.
**Supersedes:** none.
**Superseded-by:** none.
**Relates-to:** **ADR-0009** (multi-implementation parity — the generated C registries are introspect
surfaces that ship compiled-in; §7 states how the two compose, and this ADR does not restate 0009) ·
**ADR-0007** §2.3 (the release ripple — §5 measures it and finds it under-enumerated) ·
**ADR-0004** (config-driven surface — the `[[alias]]` layer this ADR finds unreachable) ·
**ADR-0010** (namespace declustering — the introspect root is namespace-agnostic, which is evidence
*for* that arc) · **ADR-0006** (carrier discipline — `carrier_schema` is the operand half of this layer).
**Motivated by:** the rc362 acoustic-domain landing, measured across six introspect surfaces.

---

## 1. Context — a layer everything references and no ADR owns

Measured over the eleven existing ADRs (`grep -ci introspect docs/srmech/adr/0*.md`):

| ADR | mention lines | the layer is… |
|---|---|---|
| ADR-0001 (profile pattern) | 6 | a **dependency** — what a profile plugin must register into |
| ADR-0010 (declustering) | 8 | a **dependency** — a destination namespace, and a thing renames must not desync |
| ADR-0002 (catalog-as-computation) | 1 | a passing reference |
| **every other ADR (0003–0009, 0011)** | **0** | — |

ADR-0007 §2.3 defines the release **ripple** through this layer — six lettered steps, `(a)` through
`(f)` — without naming the layer it ripples through. ADR-0009 §6(b) asks for a C-host capability
manifest, and the bounded first step it records (rc300 `_c_claims.py`, `#T938`) surfaces through
`describe()["c_claims"]` — again, the layer as a delivery mechanism for someone else's decision.

**Referenced by others, owned by none.** That is precisely how a layer drifts with no gate noticing:
every ADR that touches it constrains the *edge* it cares about, and nothing states what the layer as a
whole is for or when it is complete.

### 1.1 The measured cost — a brief that shipped a 12× under-scope

`docs/srmech/CLAUDE.md` described the op-total ripple as *"the FIVE duplicated count-tests"* from
around rc135 until rc362. Measured **at rc414, with the predicate stated**: `git grep -c "== <total>"`
over `tests/` only → **73 lines across 66 files**. (The rc363 text of this paragraph said *"~60
assertion sites across ~54 test files"* without naming a predicate, and by rc414 that had itself gone
stale — inside the very section that exists because the figure went stale once already. Omitting the
predicate is what makes a number un-re-measurable, so it is now given: the literal `== <total>`, in
`tests/`, nowhere else. Note the predicate is not exhaustive by construction — rc414 also found
`tests/test_op_name_set_witness_rc361.py`'s `EXPECTED_N`, a count pin the `== ` form cannot match.)
A build brief was scoped from the stale line as a five-file edit.

That file is explicitly **not** hygiene-gated, so nothing else was positioned to catch it. The number
went stale because *nobody owned the thing it counted*.

### 1.2 The rc362 measurement — what a new domain landing actually exercises

rc362 added nine ops under a **new top-level package** (`srmech.music`), taking the registry from 516
to 525. Six introspect surfaces were surveyed against the autonomous-composition standard, with a
measured baseline over the other 516 ops for every finding. Verdicts: **five PARTIAL, one COVERED**.

The findings split cleanly in two, and the split is the whole reason this ADR exists:

- **Findings a gate selected → closed inside the same rc.** The MCP coercer ratchet
  (`tests/test_mcp.py::test_all_param_types_json_coercible`) went **red** on four music params against a
  strict-zero baseline of 0/1216, and the worked-example gate
  (`tests/test_worked_examples_strict_zero_rc353.py`) went **red** naming all nine ops against a
  baseline of 0/516 on all three of its assertions. Both are **green in the working tree as of
  2026-07-30**: `CURATED` now holds 525 entries with no op missing, `srmech/mcp/_coercion.py` carries
  five `Qalg` references, and the two gates report `6 passed` and `14 passed, 4 skipped`.

- **Findings no gate selected → still open.** `carrier_schema()` still returns **25** carriers with no
  `Qalg` row; `json.dumps(describe())` contains `"Qalg"` **0** times and `"alias"` **0** times. The
  declared param types were tightened in-flight from bare `Sequence` to `Sequence[int | Q]` — an
  improvement that still does not name `Qalg`, so the drift ratchet that exists to force the
  registration still collects no such token and still passes.

**The instrumented half self-corrected within hours. The uninstrumented half did not move.** That is
not a statement about diligence; it is a statement about which properties are gated. This ADR's job is
to name the ungated properties.

## 2. Decision — what the layer IS, and what each surface guarantees TODAY

The introspect layer is **eight surfaces over one SSoT**. Stating them, and stating the guarantee
each actually carries *as measured*, is half the decision — most of the drift above came from assuming
a stronger guarantee than the surface makes.

| # | Surface | Entry point | Guarantees TODAY | Does NOT guarantee |
|---|---|---|---|---|
| 1 | **Tool schema** — the SSoT | `srmech.introspect.tool_schema.get_tool_schema()` | every registered op carries `name` / `owner` / `category` / `summary` / `explanation` / `example` / `returns` / `mcp_callable` (whole-registry, held by a 100% floor) | that any *optional* field is populated. **Measured rc412:** `composes` 9/559 · `preserves` 2/559 · `smoke_test_hint` 21/559 · `reads_lane` 9/559. **Re-measured rc423 (`#T1113`), registry now 605:** `composes` **164/605** (the population pass — §6.1) · `preserves` **13/605** (hold lifted, taxonomy declared and enforced). `smoke_test_hint` and `reads_lane` were **not** re-measured at rc423; their rc412 figures stand on the 559 basis and must not be re-based by arithmetic |
| 2 | **`describe()`** — the root index | `srmech.describe()` (`srmech/introspect/__init__.py:722`) | **counts and shape** over the whole surface, self-warming, entry-path independent | **per-op detail — by design.** 9 of 525 ops are named anywhere in the payload, all inside `lanes.ops`. Its own docstring (`:736-739`): *"It is a ROOT / INDEX: it surfaces the shape, not the detail."* A domain is *covered* here iff **counted**, never iff **named** |
| 3 | **MCP** | `srmech.mcp` · `tool_entries_to_mcp_defs` · `emit-mcpb` | enumeration, dotted-name dispatch, and `mcp_callable` honoured end-to-end — a new op is advertised and invocable with **zero** MCP-side registration (`grep music srmech/mcp/` = 0 hits) | that the published `inputSchema` is **right** — an unknown srmech type-string degrades silently to `{"type":"string"}` (`srmech/mcp/_tools.py:209`); that a return **serialises** rather than repr-terminating; that the advertised **catalog covers the registry** |
| 4 | **Generated C tool registry** | `c/src/srmech_tool_registry.c` | name/identity for every op; count integrity (`srmech_tool_registry_len` is `sizeof`-derived, so it cannot drift from its own table); hash identity against the Python SSoT | **payload quality.** The sha256 ratchet locks in a `{"call": "f(x=<int>) -> dict"}` stencil exactly as happily as a worked example |
| 5 | **Rosetta ledger** | `tests/rosetta_classification.ndjson` + two ratchets | every registered op carries a committed bucket, and the walk genuinely reaches a new package once `tests/rosetta_roots.py` names it — rc362's load-bearing edit | that the bucket was **checked**. Of the four gates that appear to cover a new composite, three carry no information about it (§6.2) |
| 6 | **Carrier schema** — the operand half | `srmech.amsc.carrier_schema.carrier_schema()` | the registry covers every carrier the op surface **DECLARES**, in `parameters[].type` / `returns.type` (25 rows, byte-identical in C) | that it covers every carrier the ops **USE**. The derivation is a token scan over declared type strings; `returns.shape` is never read |
| 7 | **Worked-example gates** | rc353 strict-zero · rc354 execution · rc355 example-input-vs-schema | that examples are real, run, and validate — **for the ops each gate selects** | uniform selection. **Three gates, three different predicates**, and only one is registry-scoped (§4.3) |
| 8 | **`[[alias]]` config vocabulary** (ADR-0004 §4, rc261) | `srmech.dsl.alias` / `load_aliases_toml` | that a declared alias **works** — verified: `names['partials']() == bell_partials()` | anything at introspect. `describe()` has no alias axis, `grep alias srmech/introspect/*.py` = 0 hits, there is no `ALIAS_CATALOG_DIR` peer to `dsl.CLASS_CATALOG_DIR`, and the tree's only `[[alias]]` descriptor lives in `tests/data/` — **outside every wheel** |

**The load-bearing caveat, stated once because the natural reading is the stronger claim and the
stronger claim is false:** surfaces 2 and 6 populate their **capability axes by derivation from
declared type strings**, not from what the ops accept and return. An op that declares a weak type
(`Sequence`, `dict`) is invisible to that derivation even when its body is explicit about the carrier —
and the enforcing ratchet, being driven by the same scan, cannot fire. The guarantee is precisely:
**`describe()` and `carrier_schema()` report the carriers the op surface DECLARES, not the carriers it
USES.** rc362 is the first rc where those two sets differ on a load-bearing axis.

## 3. Decision — the contract is AUTONOMOUS COMPOSITION

**The introspect surface is the API contract, not documentation about it. The bar is: could an agent
holding only introspect output correctly compose these ops? INCOMPLETE IS AS BAD AS FALSE.**

"Incomplete is as bad as false" is not rhetoric here; it has a measured form. An agent reading
`describe()` learns that **25** operands exist, sees `Q` among them, and correctly concludes from the
registry's own scope statement that anything absent is not on the public op surface. Meanwhile
`srmech.music.spectrum_tier` — whose entire job is returning a Tier-1-vs-Tier-2 verdict — emits
`per_partial[i]["carrier"] == "Qalg"` as **runtime data**, and `carrier_schema()["Qalg"]` raises
`KeyError`. The verdict the op exists to produce turns on a distinction the operand registry denies
exists. Nothing here is *false*; the omission alone is sufficient to break the composition.

### 3.1 What "complete" means operationally — six clauses

*(five as drafted; **C6** added 2026-07-30 by user direction — see §3.4. §3.2 below still reads on the original five, and is left as written because its argument is about C2/C3-vs-C4/C5 specifically.)*

Stated so a future rc can be judged against them rather than against a feeling. Each names its rc362
exhibit.

**C1 — NAMED.** The op is registered and appears in every count axis: `tools.total`,
`tools.by_category`, `categories[]`, `mcp_callable`, the C table, the Rosetta ledger, the name-set
witness. *Status: cheap, already gated, and rc362 passed it cleanly on every axis without a single
`describe()`-side edit.*

**C2 — TYPED HONESTLY.** Every declared `parameters[].type` and `returns.type` names the carrier union
the callable actually accepts or produces. **The test is mechanical: does the type string name what the
op's own coercion `raise` text names?** *Exhibit: `srmech/music/_spectra.py:145` raises `"expected Q,
Qalg, int or an (int, int) pair"` while the declared type reads `Sequence[int | Q]`. The op documents
the union in its raise text and in its human-readable `summary` prose, and withholds it from the one
machine-readable field two other surfaces derive from.* **PARAM HALF GATED (rc363); RETURN HALF STILL
OPEN** — the exhibit was closed in rc362 *before any instrument existed*, and rc363 built the
instrument (§3.3).

**C3 — CONSTRUCTIBLE.** Every carrier an op consumes or produces has a `carrier_schema` row with a
description, a measured capability block, and a construction example. The registry's own admission rule
already says this — `srmech/introspect/carrier_schema.py:171-177`, verbatim: *"Internal exact representations
no public op surfaces (`QMat` / `Qalg` / the genus-`RiemannTheta` family) join when an op surfaces them
(the drift ratchet in `tests/test_carrier_schema_rc205.py` forces the addition)."* *Exhibit: rc362 is
the first event in the tree that fires that trigger, and the addition did not happen. Baseline **as
measured on the DECLARED channel** — of the 25 genuine operand-carrier classes the other 516 ops
surface, **24 have a registry row**, the lone precedent being `CarrierSpectrum`, so the tree obeys its
one rule at 96%. ⚠️ **That figure is channel-relative and rc363 found it wrong on the channel that
matters**: derived from what the ops actually consume and produce, the residual is **two**, the second
being `Theta`. §3.3 records the correction. Every carrier count in this ADR should be read with its
channel named — the ambiguity is what produced the error.* **GATED (rc363)** — the exhibit was closed in rc362 *before any
instrument existed*; rc363 built the instrument, which found the 96% baseline was itself measured on
the wrong channel (§3.3).

**C4 — EXECUTABLE.** The op ships a curated example with real argument values, captured output from a
real run, and an explanation clearing the three-perspective bar (WHAT / WHEN-and-what-you-would-wrongly-
hand-roll / SIBLINGS). *Exhibit: rc362 shipped nine signature-echo stencils against a baseline of
**0/516**, with explanations of 58–125 chars against an other-516 **minimum** of 510 — two populations
that do not overlap at any point. The strict-zero gate named all nine, and it was **drained, not
ceilinged**.* **CLOSED in-rc.**

**C5 — CHAINABLE.** A producer's output feeds its designed consumer over **every advertised transport**,
not only in-process. *Exhibit: the rc's marquee case — 12-TET exactly represented and provably
incommensurable with the octave except at the octave — was unreachable over MCP, because
`serialise_native` had a `Q → [num, den]` branch added at rc231 with the comment "never a lossy float,
**NEVER A BARE REPR STRING**" and no algebraic peer. Feeding `equal_temperament_partials`' own `ratios`
back into `spectrum_tier` over the wire returned `isError=True … got str`.*
**GATED in v0.9.0rc414 (`#T1092`). This clause was marked `CLOSED in-rc` and was NOT closed — it was
refuted by execution on the exhibit written into the clause itself.**

> **The refutation, reproduced on the live tree at 0.9.0rc411 and again at rc413** (native dispatching,
> ABI 12):
>
> ```
> invoke_tool("srmech.music.equal_temperament_partials", {"divisions":12,"degrees":[0,7,12]})
> serialise_result(...) -> {"ratios": ["Qalg((-2, 0, …, 1), (Q(1, 1), Q(0, 1), …))", …]}
>
> music.spectrum_tier(loads(wire)["ratios"])
>   -> RAISED: TypeError partial[0]: expected Q, Qalg, int or an (int, int) pair; got str
> music.spectrum_tier(raw["ratios"])["tier"]  -> 2      # in-process: fine
> ```
>
> That is the SAME failure mode the clause records as closed, on the SAME exhibit, one algebra up:
> `Q` got its `[num, den]` branch at rc231 and `Qalg` never got the algebraic peer.

**Why it went green: there was no C5 instrument, and §3.3's instrument table does not list one.**
Every exercise of the exhibit is **in-process** — `tests/test_music_commensurability_rc362.py:231`,
`:244`, `:280` and `:522` all call `music.equal_temperament_partials(...)["ratios"]` directly, never
through `invoke_tool` / `serialise_result`. So the gate that "selected" the new ops tested the one
transport the clause is not about. This is precisely the failure §3.2 names — *"C4 and C5 had gates
that **selected** the new ops"* — and it is the reason a clause needs an instrument that can return
otherwise rather than a gate that merely runs.

**The instrument, as of rc414:** `tests/test_wire_round_trip_rc414.py`. It is the OUTBOUND converse of
the inbound `test_all_param_types_json_coercible` ratchet, and it selects the population C5 is about:
every registered op's declared return type (**549 of 560** are covered by the carrier registry ∪ the
non-carrier class list) plus every carrier in `carrier_schema()` constructed from its own shipped
example. `test_adr0012_c5_marquee_exhibit_chains_over_the_wire` asserts THIS clause's exhibit through
`serialise_result` → `srmech._json.loads` → `deserialise_native` → the consumer, and
`test_no_carrier_crosses_as_a_repr_string` is strict-zero on the defect class. The gate seeds
down-only ceilings for the residual (carriers not round-tripping; declared return types with no
inbound coercer) rather than asserting the surface is finished, because it is not.

**No count appears in this status line.** Restating a measured number in the status line is the
rc407 / rc410 recurrence, twice observed; the numbers live in the gate, where they are inputs to an
assertion.

**C6 — CONFIG-VISIBLE.** *(added 2026-07-30 by user direction; see §3.4 for the argument and the
measurements.)* Every behaviour the package ships **as configuration** is enumerable through the same
introspect surface as the behaviour it ships as Python. A TOML descriptor that changes what srmech can
do is part of the API, and a caller holding only `describe()` must be able to find it. *Exhibit: the
`class_catalog/` 4 descriptors ARE visible (`describe()["classes"]["toml_total"] == 4`); the
`cascade_catalog/` ships **20** descriptors with **zero** visibility, and the `[[alias]]` layer has no
`describe()` axis and no package home at all.* **OPEN — and deliberately NOT implemented in rc363**
(the `describe()` axes are the user's own rc).

> ✅ **The cascade_catalog front CLOSED at v0.9.0rc420** (`#T1114`). `describe()` carries a twelfth
> top-level key `cascade_catalog` — `{total, executable, leaf, status: {descriptor: state}, run,
> enumerate}` — and the state it counts is itself new: every one of the 20 descriptors is
> **executable** (declares an ADR-0008 §2 chain, executed bit-identical to its shipped op by
> `tests/test_cascade_catalog_executable_rc420.py`) or an explicit **leaf**, with the no-third-state
> rule strict-zero. `srmech.dsl.list_catalog_ops` rows carry the per-descriptor `status` column and
> `srmech.dsl.run_cascade_chain` runs a declared chain, so the op → chain half of §3.4's word-problem
> bridge is both countable at the root index and callable. Instrument:
> `tests/test_cascade_catalog_executable_rc420.py::test_no_third_state_strict_zero` +
> the twelve-key pin `tests/test_describe_registry_pointer_rc407.py::test_top_level_key_set_is_untouched`.
> **The alias-layer front remains OPEN** (`"alias"` still occurs 0 times in the payload); the clause
> row below carries that residue, so the closure claims exactly what was closed and no more.

### 3.2 The clause the shape of the failures teaches

C4 and C5 had gates that **selected** the new ops; both were closed within the rc. C2 and C3 had no
gate that selected them; both are open.

**A clause with no instrument that can return otherwise is a DEFECT in this ADR, not a softer kind
of clause.** It is the contract-level form of
`[[feedback_an_instrument_that_cannot_return_otherwise_is_not_a_measurement]]`: an assertion no
apparatus can contradict is not weaker evidence, it is no evidence.

**A defect of this kind has exactly three admissible discharges, and relabelling is not one of them.**

1. **INSTRUMENT it.** Ship a check that fails when the clause is false, proven by injection — the
   mutation is recorded beside the check, not merely described. This is the default.
2. **DATE it.** Record `expiry: rcNNNN` in the clause's own row. The expiry is a promise the tree
   holds: the gate re-fails once the shipped rc passes it, so a deferral cannot go quiet. A deferral
   with no expiry is not a deferral, it is the defect wearing a schedule.
3. **WITHDRAW it.** Delete the clause, or restate it as `**definitional**` / `**not instrumentable**`
   with the reason **in the row** — and accept that the ADR then claims strictly less. §6.3's three
   declined requirements are the worked example: they are recorded as UNSUPPORTED, not softened.

**Rewording the verdict is NOT a fourth discharge.** "GOAL", "standard", "target", "aspiration" and
"preference" all describe a clause with no instrument; none of them changes whether the ADR asserts
something the tree can contradict. If the ADR still means it, discharge 1 or 2 applies. If it does
not, discharge 3 applies. A verdict word is not an exit.

**This clause is self-applying, and its instrument is named.**
`tests/test_adr_clause_instrument_rc417.py:1` reads every live row in every ADR's clause tables and
fails when a cited pytest node id does not resolve — the file must exist **and** declare
`def <name>(`, so deleting the test breaks the ADR, which is the only way a citation is load-bearing
rather than decorative. Measured at rc416, before that gate existed: **0 of 17** clause rows across
the corpus carried a pytest node id at all, and `::test_` occurred exactly **once** corpus-wide, as
prose. That is the population this clause was always about.

*(This paragraph named `tests/test_adr_clause_instrument_rc415.py` from rc415 until rc417 — a file that
has never existed under any rc number. It survived two rcs because the rc415 citation gate is anchored
on the `path:line` form and a **bare path with no line number is outside it**: the ADR named its own
instrument and nothing could tell that the name was empty. The reference now carries `:1` so the
citation gate holds it, which is the smallest possible fix and the one that generalises.)*

> ⚠️ **What this section said until v0.9.0rc415** (`#T1098`), and why it was replaced rather than
> tightened: *"A clause without an instrument that can return otherwise is **not a clause, it is a
> preference**."* That is a **definition**, not a failure condition. Under it an uninstrumented clause
> is not in breach — it has simply been reclassified, so **non-compliance is discharged by
> relabelling**. The corpus already exercised the escape: ADR-0013 §11 writes `**GOAL, not a clause.**
> Adds no instrument and claims nothing`, audits itself as `2 gated · 6 ungated`, and ships anyway —
> all of which was **legal** under the old wording. The three discharges above are what the old
> sentence was reaching for; naming them is what makes the difference between a standard and a
> vocabulary.
>
> **The instrument named above ships in the rc AFTER this rewrite**, which is deliberate and
> is the discipline the rewrite itself demands: a clause and the gate that can refute it are the same
> deliverable, and an instrument built in the same rc as the change it detects has no green baseline,
> so a red is unattributable (ADR-0010 A.5's own ordering constraint). Until it lands, this clause
> carries `expiry: rc417` under discharge 2 — its own rule, applied to itself.
>
> **DISCHARGED at rc417** (`#T1100`). The expiry was written naming rc416 as the landing rc; rc416
> shipped the search tokenizer and the registry-completeness ratchet instead, so the deferral ran one
> rc past its own promise and the expiry is what made that visible rather than quiet. That is the
> mechanism working: a deferral with no expiry is the defect wearing a schedule, and this one came
> due, was noticed because it was dated, and was paid.

### 3.3 Amendment (rc363) — the clauses were IMPLEMENTED before this ADR was accepted

Two of the five clauses had their **exhibits** closed inside rc362, and §3.2's whole point is that this
does not close the **clause**: a clause with no instrument is a preference, and an exhibit closed by
hand is a preference that happened to be honoured once. rc363 therefore builds the instruments. What
the build measured is recorded here because **it corrected this draft twice**.

| clause | exhibit | instrument | status |
|---|---|---|---|
| **C2** (param half) | closed rc362, ungated | `tests/test_declared_type_honesty_rc363.py::test_declared_types_name_every_accepted_and_raise_named_carrier` | **strict-zero, no CEIL** |
| **C2** (return half) | — | none | **still OPEN** (§6.3 declines the only available surface) |
| **C3** | closed rc362, ungated | `tests/test_carrier_use_derivation_rc363.py::test_every_used_carrier_is_registered` | **strict-zero, no CEIL** |
| prose op-refs (`#T1045`) | — | `tests/test_prose_oprefs_resolve_rc363.py::test_no_unresolved_citation_anywhere` | **strict-zero, no CEIL** |
| **C5** *(added rc414, `#T1092`)* | marked `CLOSED in-rc` at rc362 and **refuted by execution** at rc411/rc413 | `tests/test_wire_round_trip_rc414.py::test_no_carrier_crosses_as_a_repr_string` | **strict-zero on the repr-string class; DOWN-ONLY CEILs on the rest** |
| **C6** (cascade_catalog front) *(added rc363 §3.4; closed rc420, `#T1114`)* | 20 descriptors, zero `describe()` visibility through rc419 | `tests/test_cascade_catalog_executable_rc420.py::test_no_third_state_strict_zero` | **GATED — strict-zero (no third state) + the 12-key root pin; the section counts 17 executable / 3 leaf** |
| **C6** (alias front) | `"alias"` occurs 0 times in `json.dumps(describe())` (re-measured rc420) | none | **still OPEN** (the layer has a package home since rc364; the `describe()` axis does not exist yet) |

**⚠️ Amendment (rc417, `#T1100`) — the instrument column now names a NODE ID, and what that does and does not buy.**
Through rc416 every cell above named a **file**. A file-valued instrument is falsifiable in exactly one
way — the file must exist — and stays green when the test inside it is renamed, gutted or deleted, which
is precisely how a clause loses its instrument while this table keeps claiming one. A node id is
falsifiable three ways: the file resolves, the file declares `def <name>(`, and **deleting the test
breaks this ADR**. `tests/test_adr_clause_instrument_rc417.py::test_every_cited_node_id_resolves` is
what makes the third true.

**Say the limit in the same breath.** A derived status does **not** remove typing from this table — it
demotes what is typed from a **VERDICT** to a **POINTER**. A human still writes *"this clause is gated
by X"*, and the `status` column above is still hand-authored prose. The gain is narrower and real: a
pointer is falsifiable, a verdict is not. The rc417 gate is also **static only** — it checks that a
cited node id RESOLVES, not that it PASSES, because a pytest test reading a run manifest reads the
*previous* run and is green-by-staleness on a fresh clone. A cited test that resolves and fails is
invisible to it today; closing that is the deferred pass arm, not a property this row may claim.

**This row's own discharge.** §3.2's `expiry: rc417` is met by the gate landing, and the instrument it
names there is corrected from the never-existent `tests/test_adr_clause_instrument_rc415.py` to the
file that shipped. That mis-citation lived for two rcs and **nothing caught it**: the rc415 citation
gate is anchored on the `path:line` form, and a bare path with no line number is outside it. The
dead-instrument class is now covered for node ids by the gate above; a bare `path` with neither a line
nor a `::` is still not, and that is stated rather than assumed closed.

**C5's absence from this table WAS the finding.** The table above listed C2, C3 and the prose gate, and
three separate sentences elsewhere in this document asserted C5 was gated. Nothing reconciled the two,
because nothing reads an ADR for content — and a clause whose only evidence of being gated is a
sentence saying so is exactly the shape §3.2 warns about. The rc414 row is the first entry here whose
exhibit column records a REFUTATION rather than a closure, and that asymmetry is deliberate: it is
cheaper to keep a wrong verdict visible than to discover a second time that it was never measured.

**The shared instrument (C2 and C3; the prose gate is independent).** The two carrier clauses ride
`tests/coercion_boundary.py`, a **second, independent channel**: it reads what each op's own source
BRANCHES ON — an `isinstance` guard on a value tracked
from the op's own parameters through assignment / iteration / helper calls, imports included — rather
than what a hand-written type string says. §2's load-bearing caveat is exactly that both `describe()`
and `carrier_schema()` derive from the declared strings, and **a single channel cannot disagree with
itself**; that is also why §7.3's parity matrix was green on the same hole.

**Correction 1 — C2's mechanical test, as literally stated, is too noisy to ship.** §3.1 says *"does
the type string name what the op's own coercion `raise` text names?"*. Implemented plainly — carrier
tokens appearing in any raise text in an op's defining module, against that module's declared types —
it flags **16 of the 33 modules it selects** (measured on the rc362 tree, before this rc's fixes), and
inspection of all 16 finds most are not defects:
`amsc.tripoly`'s *constructor* raises on `BiPoly` / `Poly` / `Q` while the registered op takes raw
coefficients; `amsc.op_provenance` raises prose explaining what is NOT provenance-tracked. A gate that
is wrong roughly half the time trains the reader to override it. The shipped form is the **conjunct** —
a carrier is flagged only when the op both ACCEPTS it (dataflow-tracked `isinstance`) and NAMES it in a
raise text on that same path — which selects **27 of 525 ops** and found **8 violations, all genuine**.
This is the same move §6.3 already makes for three other candidate requirements: state the requirement,
decline the undecidable form, ship the decidable subset and say which is which.

**Correction 2 — C3's baseline was measured on the channel C3 exists to distrust.** §3.1 records *"of
the 25 genuine operand-carrier classes the other 516 ops surface, **24** have a registry row — the lone
precedent is `CarrierSpectrum`"*. Derived from what the ops actually consume and produce, the residual
is **two, not one**: `CarrierSpectrum` **and `Theta`** — the elliptic ATOM, accepted directly by five
ops (`elliptic_gosper` / `elliptic_recurrence_8w7` / `elliptic_zeilberger` / `elliptic_wz_certificate` /
`carrier_spectrum`). The draft missed it for precisely the reason the clause exists: those five ops
declared `EllRatio` alone while their own `description` prose read *"an EllMonomial / Theta is
lifted"*. **A baseline is a measurement, and a measurement inherits the blindness of its instrument** —
which is `[[feedback_a_zero_census_is_basis_free_a_nonzero_one_is_gauge]]` applied to §5's own gauge
rule. Both carriers were registered (26 → 28), so C3 ships strict-zero rather than with a CEIL of 2.

**What the C2 instrument found, and what was done with it.** Eight ops declared a narrower type than
they accept; every one was **fixed, not ceilinged**:

| op | withheld | was declared |
|---|---|---|
| `carrier_ladder.qpoly_promote` | `QBiPoly` | `QPoly` |
| `q_gosper.q_gosper` (both params) | `Poly` | `QPoly` |
| `elliptic_gosper` · `elliptic_recurrence_8w7` · `elliptic_zeilberger` · `elliptic_wz_certificate` · `carrier_spectrum` | `EllMonomial` (+ `Theta`) | `EllRatio` |
| `harmonics.classify_chirality_harmonic` | `Q` | `float` |

Five of the eight carried the union in their human-readable prose **in the same tuple** that withheld it
from the machine-readable field. That is C2's failure mode in one line of source, and the reason the
clause is about a *field* rather than about documentation quality. Each widened type string maps to the
**same** MCP coercer the one-carrier key already used (`_to_ellratio` has accepted `EllRatio` /
`EllMonomial` / `Theta` since rc61): the wire behaviour did not change, the declaration caught up.

**Non-vacuity, demonstrated rather than asserted.** Each gate was proven by injecting a real defect into
real content, watching it go red, then restoring byte-identically (sha256-checked). The C3 injection is
the load-bearing one because it is a **differential**: restoring the rc362 pre-state exactly —
`partials` declared bare `Sequence`, `Qalg` unregistered — leaves the existing declared-channel ratchet
`test_every_tool_type_carrier_token_is_registered` **green (1 passed)** while the new use-derivation
gate goes **red, naming all three `srmech.music` ops**. That is §1.2's "findings no gate selected"
turned into a finding a gate selects.

**A second defect, and it is an ADR-0009 one.** `srmech.mcp._tools._TYPE_LEXICON` / `_ENCODING_HINT`
have a hand-maintained C mirror (`c/src/srmech_tool_schema.c`) pinned by
`test_mcp_defs_type_lexicon_and_hint_mapping`. rc362 added `"Q"` and `"Sequence[int | Q | Qalg]"` to the
Python maps and did not mirror them, so a C-emitted `inputSchema` advertised `"string"` for four params
the Python emitter advertises as `"array"` — §4.2's row-4 silent degradation, on the C side, where §7.1
says the generated registry *is the entire introspect layer*. It was invisible on any host whose
`libsrmech` predated the change and surfaced only because rc363 rebuilt the library before running the
suite. All six entries are now mirrored. **This is §7.3 read the other way**: parity certifies mutual
realizability *when both projections are current*, and a stale artifact under test certifies nothing at
all (`[[feedback_verify_the_artifact_under_test_is_the_one_you_think]]`).

**One further defect the work surfaced, outside the clauses.** `tools/gen_carrier_examples_probe.py`
has claimed since rc241 that *"hand-curated construction examples may be added here and are
preserved"*. They were not: `main()` rewrites the whole file from its two dicts, and regenerating for
the two new carriers **silently dropped the rc362 `Qalg` row**, whose `yields` carries the
zero-divisor / irrationality witness a bare `repr` cannot show. Fixed by giving the generator a
`_CURATED` dict so the claim is structurally true. This belongs to §6.1's pattern: a mechanism that
declares a property it does not have, with nothing positioned to notice.

**What remains ungated after rc363** — the acceptance question, answered plainly:

- **C2's return half.** `returns.type` has no second channel. §6.3 already declines `returns.shape` as
  a gate surface (403 unregistered capitalised-token occurrences over 154 distinct tokens), and that
  verdict stands; closing it needs a new typed element-carrier field, which is machinery this ADR
  deliberately does not specify.
- **C6 (the TOML surface), stated in §3.1 and argued in §3.4.** Deliberately NOT implemented here.
- **C1 and C4** were already gated before this rc and are unchanged. **C5 was listed here too, and
  that was false**: it had no instrument, and was refuted by execution on its own exhibit (corrected
  v0.9.0rc414, `#T1092`; see §3.1 C5). It is gated from rc414 by
  `tests/test_wire_round_trip_rc414.py`.
- **The §6.2 uninformative-green list.** Five gates whose green carries no information are recorded,
  not repaired.


### 3.4 C6 in full — introspection derived from Python source cannot see config-driven behaviour

*Added 2026-07-30 by user direction:* **"our TOML surface should even enter describe information. this
is how users and LLM and srmech inference with siona will know what tools do what, with our siona
project goal to actually be able to know what a cascade looks like from a word problem."**

**The structural argument, stated once.** ADR-0004 makes config-driven the PREFERRED way to add
behaviour: a domain object that is a cascade-of-the-14 should ship as a `[class]` TOML descriptor
rather than as hand-coded Python. This ADR makes the introspect surface the API CONTRACT. Those two
standings are in direct tension, because **the introspect layer is derived from Python source** —
`ToolEntry`s are Python literals, `carrier_schema` is a Python dict, the C registries are generated
from both. Behaviour that lives in a TOML file is invisible to every one of those derivations **by
construction**, not by oversight. So the more of the surface that moves to config — which ADR-0004 says
is the right direction — the less of it `describe()` can see. The tension does not resolve itself; it
widens with every descriptor added.

**Measured 2026-07-30 on this branch**, three descriptor layers, three different treatments:

| layer | ships | visible at `describe()` | entry point |
|---|---|---|---|
| `srmech/cascade/catalogs/class_catalog/` | **4** descriptors, inside the wheel | **YES** — `describe()["classes"]["toml_total"] == 4`, plus three `ToolEntry`s | `dsl.CLASS_CATALOG_DIR` · `register_class_dir` |
| `srmech/cascade/catalogs/cascade_catalog/` | **20** descriptors, inside the wheel | **NO** — `json.dumps(describe())` contains `"cascade_catalog"` **0** times, and none of the 20 descriptor names appears anywhere in the payload | `dsl.CATALOG_DIR` · `load_catalog` |
| the `[[alias]]` vocabulary (ADR-0004 §4, rc261) | ~~**0** descriptors in any wheel~~ → **2**, inside the wheel (rc364) | **NO** — `"alias"` occurs **0** times in the payload | ~~`dsl.load_aliases_toml(path)` — a **path**, with no registered directory~~ → `dsl.ALIAS_CATALOG_DIR` · `register_alias_dir` · `list_alias_descriptors` (rc364) |

⚠️ **PATHS UPDATED rc364.** The first two rows read `srmech/amsc/_research/{class,cascade}_catalog/`
until ADR-0010's first execution slice moved the built-in catalogs to the composition layer. The
*measurements* (4 / 20 / visible / not-visible) are unchanged by that move — a directory move does
not change what `describe()` can see, which is itself part of C6's point.

✅ **THE MIDDLE ROW INVERTED AT v0.9.0rc420** (`#T1114`). The table above is the 2026-07-30
measurement and stands as written; re-measured at rc420: `json.dumps(describe())` now contains
`"cascade_catalog"` as a twelfth top-level key whose payload counts the catalog (`total: 20,
executable: 17, leaf: 3`) and carries the per-descriptor status map — and the states it counts are
new facts, not relabels: every descriptor now declares an EXECUTABLE ADR-0008 §2 chain (proven
bit-identical to its shipped op, per proof case, by the rc420 gate) or an explicit LEAF with a
machine-readable reason, no third state. The alias row is unchanged (`"alias"`: still 0 — that
front stays OPEN and is carried as its own clause row in §3.3).

Two of the three are unreachable, and the third proves the reachable shape is already available: the
`[class]` layer has a packaged directory constant, a loader that reads it, a `toml_total` count and
three registered ops. **The asymmetry is the finding** — this is not a missing capability, it is a
capability applied to one of three peers.

**Why the alias layer is the sharpest case.** `srmech/dsl/_alias.py` exposes `load_aliases_toml(path)`
and nothing else: no `ALIAS_CATALOG_DIR` peer to `dsl.CLASS_CATALOG_DIR`, no packaged directory, no
`register_alias_dir`. A layer whose only entry point takes a caller-supplied path has **nowhere to
ship a descriptor**, which is exactly why rc362's first-ever `[[alias]]` descriptor landed in
`tests/data/music_domain_aliases.toml` — outside every wheel (§6.1). The missing `describe()` axis and
the missing package home are the same defect seen from two sides: **a config surface with no packaged
descriptor and no enumeration entry point exists only for readers of the test suite.**

✅ **THE PACKAGE-HOME HALF CLOSED rc364; the `describe()` half is still OPEN.** ADR-0010's first
execution slice built the shape this paragraph says is missing — `ALIAS_CATALOG_DIR`,
`register_alias_dir`, `list_alias_descriptors`, `resolve_alias_descriptor`, and a packaged
`srmech/cascade/catalogs/alias_catalog/` holding both shipped-example descriptors — and moved
rc271's and rc362's descriptors into it. **That is the "two sides" claim being confirmed rather
than merely restated:** giving the layer a home is what made the wheel defect fixable at all, and
the fix was mechanical once the constant existed. What it does NOT do is make the layer countable
at the root index: `"alias"` still occurs **0** times in `json.dumps(describe())`. C6 remains open
on its own terms, and it is now open on a *narrower* front — an enumeration axis over a layer that
finally has something to enumerate.

**Why this matters for Siona specifically, in the user's framing.** The goal is *"to actually be able
to know what a cascade looks like from a word problem"*. That is two lookups, and each one is a
config layer that `describe()` cannot see:

- **domain word → op** is the `[[alias]]` layer. rc362's own descriptor is the worked example: a
  musician says *"partials"*, and `names['partials']()` resolves to `bell_partials`. Verified to WORK;
  undiscoverable.
- **op → chain** is the cascade catalog. 20 descriptors say how the lean-ISA atoms compose into
  `chiral_flip`, `net_chirality`, `parallel_sector_dispatch`, `kuramoto_step` and the rest. Loadable;
  uncountable from the root index.

An agent holding only `describe()` therefore cannot get from a word problem to a cascade — not because
the machinery is missing, but because **neither half of the bridge is enumerable**. §3's bar is
autonomous composition and its standard is INCOMPLETE IS AS BAD AS FALSE; this is the largest measured
instance of incomplete in the layer.

**What C6 does and does not require.** It requires that a shipped config layer be **enumerable** —
countable at the root index and reachable by name — on the same terms the `[class]` layer already is.
It does NOT specify the payload shape, does not require per-descriptor detail in `describe()` (which is
a ROOT/INDEX by its own contract — surface 2), and does not decide whether the alias layer's package
home is a new `_research/alias_catalog/` or something else. Those are implementation decisions for the
rc that closes it. **Decided rc364:** the home is `srmech/cascade/catalogs/alias_catalog/`, beside
`class_catalog/` and `cascade_catalog/` — not under `_research/`, which ADR-0010's first slice
deleted in the same commit. Reasoning recorded as ADR-0010 Amendment B.

**Status: OPEN and deliberately unimplemented in rc363.** The user assigned the `describe()` axes to
their own rc. Recording the clause without building it is the correct move here *only because it is
labelled* — per §3.2 an unimplemented clause is a preference, and this one is named as such rather than
counted as coverage.

**Status update, v0.9.0rc420 (`#T1114`): the cascade_catalog front is CLOSED and gated** (the rc the
user assigned arrived — see the ✅ notes above and the two C6 rows in §3.3's clause table). **The
alias front remains OPEN** on its own row, so this clause now claims exactly the half that shipped.


## 4. Decision — the ripple is the layer's shape, and it is enumerated HERE

ADR-0007 §2.3 lists six lettered steps and is the closest thing the tree has to this enumeration.
Measured at rc362, a new public callable touches **nineteen classes of site**. Enumerating them in the
ADR that owns the layer is the point: no future rc should have to rediscover the list, and no brief
should be scoped from a prose sentence that has gone stale.

| # | Site | When | Kind |
|---|---|---|---|
| 1 | `srmech/introspect/tool_schema.py` — the `ToolEntry` | always | hand |
| 2 | `srmech/introspect/_tool_docs_curated.py` — curated example + explanation | always (C4) | **hand — an INPUT to codegen; no generator rewrites it** |
| 3 | `srmech/mcp/_coercion.py` — a coercer per declared param type | always | hand (strict-zero ratchet) |
| 4 | `srmech/mcp/_tools.py` `_TYPE_LEXICON` — a JSON-schema type | on a new type string | hand (**ungated** — silently degrades to `"string"`) |
| 5 | `srmech/mcp/_coercion.py` `serialise_native` — an outbound branch | on a new returned carrier | hand (**ungated** — silently repr-terminates) |
| 6 | `srmech/introspect/carrier_schema.py` `_CARRIERS` + `_carrier_examples` | on a new surfaced carrier | hand (ratchet is **type-string-scoped**) |
| 7 | `tests/rosetta_classification.ndjson` — a bucket row | always | hand |
| 8 | `tests/rosetta_roots.py` — the walk root | **on a new top-level package** | hand — rc362's load-bearing edit; a root naming a non-existent package is **silently skipped** |
| 9 | `COMPOSES_C_ZERO_REACH_PINNED` + its written justification | `non_compute`/`composes_c` and zero-reach | hand |
| 10 | `srmech/introspect/_c_claims.py` — the op→C-symbol manifest | `c_dispatched` | regenerated |
| 11 | `srmech/_native/__init__.py` — the ctypes binding | `c_dispatched` | hand |
| 12 | `c/include/srmech.h` + `c/src/*.c` — the C implementation | `c_dispatched` (ADR-0009) | hand |
| 13 | `srmech/introspect/_tool_docs.py` | always | regenerated |
| 14 | `c/src/srmech_tool_registry.c` | always | regenerated |
| 15 | `c/src/srmech_carrier_registry.c` | always | regenerated |
| 16 | `c/src/srmech_{class,responsion}_registry.c` | always (usually no-op) | regenerated |
| 17 | `tests/registered_op_names.txt` + `EXPECTED_N` / `EXPECTED_NAME_SET_SHA256` | always | regenerated, **committed in the same commit** |
| 18 | the op-total count pins — **73 lines across 66 test files** (`== <total>` in `tests/`, rc414), **plus `EXPECTED_N` in `tests/test_op_name_set_witness_rc361.py`, which that predicate misses** | always | hand |
| 19 | `tests/worked_examples_result.ndjson` — the execution ledger | iff the example carries a `worked` key | regenerated |

**Two properties of this table are decisions, not observations.**

### 4.1 The hand/regenerated split is where the drift lives

Twelve of the nineteen are hand edits. `_tool_docs_curated.py` is the one most easily missed because it
*looks* generated and sits beside the generated file it feeds — ADR-0010 Amendment A.3 independently
found the same thing from the opposite direction (276 hand edits in it that its own budget had not
costed).

### 4.2 Conditional rows are the ones that go unnoticed

Rows 4, 5, 6 and 8 fire only on a *new* type string, carrier, or package. A domain that reuses existing
vocabulary never exercises them, so they are exercised precisely when a landing is least routine — and
three of the four are ungated or gated on the wrong field.

### 4.3 The worked-example gates select on three different predicates

This is the sharpest structural fact in the layer and it belongs in the ADR verbatim:

| gate | selection predicate | scope |
|---|---|---|
| rc353 strict-zero | `owner == "srmech"` | **registry-scoped — 525/525, cannot be dodged** |
| rc354 execution | `example["worked"]` is truthy | **example-shape-scoped — opt-in** |
| rc355 example-input-vs-schema | `isinstance(example["input"], dict)` | **example-shape-scoped — opt-in** |

Consequence, demonstrated by rc362: a new domain whose examples land in an off-convention shape
**silently exits the scope of two of the three gates and stays green there**, while the third goes red.
Nine ops landed and rc354's collected set did not move — 430 before, 430 after — and its freshness
assertion passed *because* the nine were never collected. Any statement that "the worked-example gates
cover the registry" must be qualified: only the rc353 half is registry-scoped; the other two are
scoped by authoring convention.

## 5. Decision — the gauge rule is part of the contract, not a review habit

**A count of 0 is basis-free. A count of N ≠ 0 is a census of the presentation you chose.** No claim
that a slice "lacks X" is admissible without the measured baseline over the rest of the surface
(`[[feedback_a_zero_census_is_basis_free_a_nonzero_one_is_gauge]]`).

The rc362 survey is the worked example of why this is a contract clause and not advice. Six candidate
findings were raised per surface; measuring the baseline **reclassified most of them**:

| candidate finding | new | baseline | verdict |
|---|---|---|---|
| music examples are signature stencils | 9/9 | **0/516** | **REAL GAP** — drained in-rc |
| music params have no MCP coercer | 4/22 | **0/1216** (a ratchet holds it at zero) | **REAL GAP** — fixed in-rc |
| `Qalg` unregistered as a carrier | 1 of 2 surfaced carriers | **24 of 25** registered | **REAL GAP** — open |
| music ops declare a bare container param | 3/9 | **55/516 (10.7%)** | TREE-WIDE NORM (music 3×, practice not new) |
| music ops absent from the `produces` index | 8/9 | **0/89** other dict-returners indexed | TREE-WIDE NORM — a composition effect, **REFUTED** as music-specific |
| music ops declare no `lane` | 0/9 | 9/516 (1.7%) | **EMPTY** — forced; a declaration would be **uncontradictable**, i.e. a regression |
| no music `[class]` descriptor | 0 | — | **EMPTY** — the ops are stateless functions, not state+method objects |
| `limits.capabilities` has no exactness tier | 0/3 | **3/3 are `cayley_dickson`** | TREE-WIDE NORM — rc362 inherits an empty axis, it did not empty one |
| MCP params degrade to `{"type":"string"}` | 8/22 (36%) | **122/1216 (10%)**, 104 of them required | TREE-WIDE NORM — music is 3.6×, and 104 required params already fail a schema-obedient client |
| example input values are strings, not ints | 2/2 | **72/516** identical mismatch | TREE-WIDE NORM — the generator stringifies by construction |

Half the list dissolved under the gauge. Reporting any of the bottom six as an rc362 regression would
have been a presentation count dressed as a finding, and would have spent the rc's budget on the wrong
work — while `Qalg`, the one that survives against a 96% baseline, went unfixed.

## 6. What is measured and standing-holed

Blunt, with baselines. These are **standing holes in the layer**, not rc362 defects, and this ADR is
where they are recorded so no future rc re-files them as new.

### 6.1 Declared-complete arcs with an empty population — the pattern this ADR exists to name

Two subsystems shipped with a mechanism, a gate, and an ADR or CHANGELOG paragraph declaring the arc
complete, and then the population never arrived:

| subsystem | declared | measured today |
|---|---|---|
| `ToolEntry.composes` / `.preserves` | rc305, *"the Siona compose-a-cascade **CAPSTONE**"* (`#T943`) | **PARTLY DISCHARGED rc412.** As written this row said *"2 of 525 — `genome.genome_from_graph` and `genome.cwf_consistency_mod2`, both landed in the rc that shipped the field. Nothing has been added since."* Two corrections, and the row is worth keeping for both. (a) The landing claim was **false**: `genome_from_graph` landed rc305, `cwf_consistency_mod2` landed rc313, eight rcs later — rc305's own CHANGELOG says *"Only genome_from_graph carries composition data this rc."* (b) The diagnosis was right and the cause was one layer below population: **nothing read either field.** rc412 (`#T1093`) ships `ToolSchema.composition()` — including the REVERSE edge, which had no reader at all — indexes both fields in `search`, closes the vacuity hole below (`cwf`'s declaration was pinned by nothing: deleting it left the rc305 gate fully green), and hand-traces seven more rows under a stated criterion. **`composes` 9/559; `preserves` still 2/559 and deliberately so** — it is a *different* feature (rc305 checks `composes` for registry membership and `preserves` only for non-emptiness), and any floor on it is satisfiable at scale with zero per-op information, so it gets a declared taxonomy before it gets rows. **(c) DISCHARGED for `composes` at rc423 (`#T1113`); HOLD LIFTED for `preserves` at the same rc.** `composes` **16/605 → 164/605** by tier adjudication, not by row-by-row tracing (the tier table is below); `preserves` **13/605** with the taxonomy the hold was waiting for now declared and enforced at strict zero (`tests/test_preserves_taxonomy_rc423.py`). The row's own reasoning is what earned the discharge and is kept verbatim above: the taxonomy came **before** the rows, exactly as this cell demanded. |
| `[[alias]]` config vocabulary | ADR-0004 §4, rc261, with a security contract and a parse path | **ZERO descriptors** anywhere in the tree until rc362 added the first — and that one is `tests/data/music_domain_aliases.toml`, a **test fixture outside every wheel** (`wheel.packages = ["srmech"]`, `tests/**` only under `sdist.include`, no force-include, no `MANIFEST.in`). **FIXED rc364** — 2 descriptors now ship inside `srmech/cascade/catalogs/alias_catalog/`. Note the row's own words survive the fix and are worth keeping: the population was zero-in-the-wheel for **101 rcs** and no gate said so, because there was no directory to count |

**Name the pattern: a field or subsystem whose population is 2 of 525, or 0 of anything, is not
shipped — it is declared.** The mechanism works; the capstone language is what is false. And nothing
goes red, because a strict-zero ratchet over an EMPTY selected set passes — the instrument cannot
return otherwise.

**rc412 (`#T1093`) found the layer BELOW population, and it sharpens this section rather than
retiring it.** The `composes` row above is not merely under-populated — until rc412 **nothing read
it**. `to_jsonable`, the curated merge and the C serialiser were the only consumers, none of them a
question a caller asks. So the honest ordering is **reader first, rows second**: populating a field
nothing reads only moves a hash, and a population drive launched without a reader would have
manufactured exactly the filler this section warns about. The shrinking-set corollary was also
measured live rather than argued: `cwf_consistency_mod2`'s declaration was pinned by nothing, so
deleting it took the declared-edge total from 27 to 25 with the rc305 gate **fully green** — the
same "instrument cannot return otherwise" failure, one direction over.

**And a coverage floor is the wrong repair here, on measurement.** `tool_schema.py` says of
`composes` that empty is *"the correct default"* for a leaf op, and an identity-resolved call graph
puts **231 of 559** rows at zero reachable registered sub-ops even at depth 3. "State the
population" is the obligation this section imposes; "drive the population to the denominator" is
not, and conflating them would turn this section into the defect it diagnoses.

**⚠️ rc423 (`#T1113`) EXTENDS the paragraph above; it retracts nothing in it.** The argument stands as
written, the re-measurement agrees with it — **258 of 605** rows reach zero registered sub-ops at
depth 3, the same finding one registry larger — and **rc423 shipped no coverage floor**. What rc423
adds is the reason a *ceiling* is nevertheless compatible with that reasoning, which the original
paragraph had no occasion to distinguish.

**The distinction is between two sets that the field rendered identical.** A LEAF row is
`composes = ()` **because it composes nothing** — permanently and correctly empty; a floor over it
would be an instruction to invent edges. An UNEXAMINED row is `composes = ()` **because nobody
looked** — and in the field the two were **indistinguishable**, both an empty tuple, with no
instrument able to say which was which. The obligation this section imposes ("state the population")
was therefore unsatisfiable at rc412 for a reason the section did not name: *stating* a population
requires being able to say of each row **why** it is empty.

So rc423 adjudicates every row into a tier and ratchets **only the residue** — registry 605, census
generated by the committed `docs/srmech/notes/_composes_population_census_rc423.py`, per-row verdicts
shipped as `docs/srmech/python/tests/composes_adjudication_rc423.ndjson`:

| tier | count | admission rule |
|---|---|---|
| **DECLARED** | 16 | hand-traced multi-op, pinned in `tests/test_composes_grain_rc412.py::ROSTER` |
| **SINGLE** | 148 | `derived(name, depth=1)` is a SINGLETON — exactly one direct registered call edge, so the ordered tuple is **FORCED** (one element has one ordering) |
| **LEAF** | 258 | `derived(name, depth=3)` is EMPTY — *"composes nothing registered"* as a MEASURED statement |
| **REFUSED** | 1 | tier-eligible and deliberately declined: `srmech.math.covering.covering_catalog` *consults* `spin8_center` rather than being built from it (rc422 read it and said no) |
| **RESIDUAL** | 182 | ≥2 direct call edges — **the ORDER is a human act**, so the row is NOT enumerated |

**Adjudicated 423 of 605.** `composes` population moved **16/605 → 164/605**; `preserves` stayed
**13/605**, deliberately unseeded.

**`CEIL_UNADJUDICATED = 182` is a down-only ceiling over the UNADJUDICATED RESIDUAL — NOT over
"unpopulated rows", and the difference is the whole reason it does not contradict this section.**
Over unpopulated rows it would be the denominator-drive this section forbids, and it would count the
258 leaves as debt they can never discharge. Over the residual it counts only rows where the order is
a human act **and the human act has not happened** — which is the honest remainder of "state the
population", not a coverage target. **Read the two sentences together as the rule this section now
carries:** *never floor a field whose correct value is often empty; do ceiling the set of rows whose
emptiness has not been adjudicated.*

The asymmetry that makes this diagnosable: the `[class]` half of the same config-TOML family is fully
packaged and introspectable — 4 descriptors ship **inside** `srmech/cascade/catalogs/class_catalog/`
(`srmech/amsc/_research/class_catalog/` before rc364), `describe()["classes"]["toml_total"] == 4`, and
three `ToolEntry`s expose them. Two peer descriptor layers, opposite treatment. **A config surface with
no packaged descriptor and no enumeration entry point exists only for readers of the test suite.**

rc364 closed the *packaged-descriptor* half for the alias layer and left the *enumeration* half open,
which splits this sentence into its two conjuncts and shows they are separable: the alias layer now has
a packaged descriptor and still has no enumeration entry point at `describe()`, so it is reachable by
name (`load_aliases_toml("music_domain_aliases")`) but not discoverable without knowing the name.
Half the defect, precisely.

### 6.2 Green gates that carry no information about what they appear to cover

| gate | why its green is uninformative | classification |
|---|---|---|
| `test_no_composition_reaches_nonstandalone_leaf` | its three not-ready buckets hold **0 of 750** ledger rows, so its predicate is unsatisfiable for every leaf. It DOES select the new ops — its green is inert, not unselected. Its own docstring concedes it is a FORWARD-GUARD | **EMPTY** — legitimate as a forward-guard; 0/255 composites have ever been verified by it |
| `test_composes_c_zero_reach_rows_are_pinned` (the rc217 anti-hidden-kernel pin) | it iterates `non_compute` rows only, so it **structurally cannot select** a `composition_of_c` row. Gate coverage 0/7 music **and 0/248 other** | TREE-WIDE NORM — a standing hole, not an rc362 defect |
| `test_every_tool_type_carrier_token_is_registered` (the C3 ratchet) | scans `parameters[].type` + `returns.type` only. Proven by counterfactual: forcing an honest `dict[str, tuple[Qalg, ...]]` return type makes the same scan return `['Qalg']` and the assert **fires**. It passes by not selecting the token | TREE-WIDE NORM — blind for **0/525**; `carrier_spectrum` (rc69) has hidden a genuine unregistered carrier from it since before the gate was written (rc205) |
| the MCP catalog-count assertions | every one asserts `len(...) > 50`; `test_mcpb_emit.py` draws both sides of its equality from the same C-preferring source, so it is self-consistent by construction. The only instrument that can see truncation is `@skipif(not has_native)` — silent on every pure host | TREE-WIDE NORM — a count gate exists for the whole catalog or for none of it |
| `describe()["c_claims"]["consistent"]` on a pure build | `checked_ops = 0`, `checked_symbols = 0` — **0 of 263** claimed ops checked. Green because nothing was checked | **EMPTY**, build-conditional, and the docstring says so. Anyone citing it as evidence must first check `native.has_native` |
| `test_mcp_defs_type_lexicon_and_hint_mapping` — and **every** `@skipif(not has_native)` C-parity gate (added rc363) | it compares the Python table against **the loaded `libsrmech`**, never against the checked-in `.c`. On a host whose library predates the current sources it compares two copies of the OLD table and agrees. Measured: rc362 added `"Q"` and `"Sequence[int \| Q \| Qalg]"` to `_TYPE_LEXICON` / `_ENCODING_HINT` without mirroring them to `c/src/srmech_tool_schema.c`, and the gate was green on every developer host until rc363 rebuilt the library — **the artifact under test was not the artifact under change** (`[[feedback_verify_the_artifact_under_test_is_the_one_you_think]]`) | **BUILD-CONDITIONAL.** Green means "the loaded binary agrees", never "the tree agrees". This is the §7.3 oracle failing one step earlier than §7.3 describes: there, two current projections agreed and were consistently wrong; here, one projection was simply not the one under change. Any citation of a C-parity green must state the library's provenance |

The bell-vs-siblings exhibit is worth preserving because it is internal to a single rc: `bell_partials`
was routed to the bucket that **has** a zero-reach pin, tripped it, and had to carry a written
justification; **five sibling ops in the same two source files** went to the bucket with no such pin and
were asked nothing. Same author, same session — the difference in scrutiny came entirely from which
bucket was chosen.

### 6.3 Nulls this ADR classifies as UNSUPPORTED — no requirement is invented here

Per the survey's instrument discipline, three candidate requirements are **declined** because the
instrument cannot decide them, and saying so is the honest output:

- **Widening the carrier ratchet to `returns.shape` — UNSUPPORTED as framed.** `.shape` is free prose:
  the other 516 ops' shape strings carry **403 unregistered capitalized-token occurrences over 154
  distinct tokens** (`N`, `True`, `Class`, `Hermitian`, `ValueError`, `Rosengren`…). A wider regex
  floods. `ToolParameter` has fields `(name, type, required, summary)` — no shape slot at all. Closing
  C2/C3 mechanically needs either an honest parameterized `.type` (which the schema **already**
  expresses: 37 params use unions today) or a new typed element-carrier field. This ADR states the
  requirement (C2/C3), not the machinery.
- **A music lane declaration — UNSUPPORTED, and adding one would be a REGRESSION.** The lane admission
  rule permits a declaration only when both perturbations apply to the op's input — a Q8-center sign
  flip and an `Aut(V4)=S3` index relabel. Neither is defined on a frequency ratio over `Q`/`Qalg`, so
  `tests/test_op_lane_rc347.py` could never contradict a declaration. That is exactly the vacuous-field
  defect rc343 removed when it retired `turn`'s `bounded_by: "associativity"`. **A coverage number is
  never a reason to mint a declaration nothing can contradict.**
- **A music entry in `limits.capabilities` — admissible but not owed by this ADR.** `srmech.music` does
  ship a genuine three-rung ceiling (`_spectra.py:50`: *"Tier 3 has no exact carrier by construction"*)
  that maps onto the published schema. But all 3 existing entries are `family="cayley_dickson"`; no
  non-CD domain has ever populated the axis. rc362 **inherits** an empty axis. Recorded as a standing
  hole; not a defect.

## 7. C parity — how introspect composes with ADR-0009

ADR-0009 is standing policy and this section adds to it rather than restating it.

### 7.1 The generated C registry is the LAST-RESORT introspect surface

For a bare-C / MCU host, `c/src/srmech_tool_registry.c` **is the entire introspect layer** — no
`describe()`, no docstrings, no `worked_examples_result.ndjson` to fall back on. So the payload
deficit measured in C4 is not a docs backlog: at rc362 a host reading entry 513 got
`spectrum_tier(partials=<Sequence>, open_partials=<Sequence[int]>) -> dict` plus an 86-char restatement
of the summary — the signature it could already read off the header. **Regenerating the C table while
the strict-zero example gate is red compiles a known-deficient contract into the wheel.** The payload
bar is therefore a *precondition* of C regeneration, not a parallel concern.

### 7.2 Verifying a C registry requires DECODING — a textual sweep lies

Three of the generated artifacts store text as **decimal byte arrays**. `tests/c_byte_arrays.py` is the
one shipped decoder and every check must import it. Measured at rc362 for the nine new op names:

| artifact | as-text | **decoded** | a `grep` is… |
|---|---|---|---|
| `srmech_tool_registry.c` | 9 | 0 | sufficient |
| `srmech_carrier_registry.c` | **1** | **8** | **an 8× undercount that inverts the conclusion** |
| `srmech_class_registry.c` | 0 | 0 | sufficient (correctly empty) |
| `srmech_responsion_registry.c` | 0 | 0 | sufficient |

A naive sweep of the carrier registry reports one music op present and seven absent — the exact
opposite of the truth. At tree scale the same sweep reports 385 of 525 ops absent against a true 73.
**The MIXED mode is more dangerous than the invisible one**: a flat `0` invites suspicion, a plausible
number does not (ADR-0010 records the same trap from the rename direction). Every check must also run
`octal_escaped_name_chars()` — a `0` there is what makes the as-text channel provably complete.

### 7.3 Parity certified mutual realizability and could not certify correctness

This is the sharpest thing rc362 says to ADR-0009, and it is a **confirmation of the stance, not a
counterexample**. The C carrier registry reproduces the Python one exactly — 25 == 25, byte-identical
canonical JSON under the sha256 ratchet — **including the missing `Qalg`**, absent from both the as-text
and decoded channels. The two projections agreed, and **agreeing is what let the omission through**,
because both read the same impoverished SSoT: the declared type strings.

> **A green parity matrix bounds implementation drift. It does not bound surface truth, and it must not
> be cited as a completeness claim.** The informative disagreement never occurred because there was
> nothing for the projections to disagree about.

This is `[[user_stance_co_equal_dual_construction_is_a_consistency_oracle]]` measured on a live rc.

### 7.4 The MCP exemption is about C-parity only

ADR-0009 §4 exempts `srmech.mcp` / `srmech.llm` from multi-implementation parity because they bind a
specific host runtime. **That exemption does not license an MCP-side capability gap**, and §5's rule
applies with full force: three of the four rc362 MCP findings were cases where MCP "declines cleanly"
(a typed `TypeError`) while the in-process Python caller is served perfectly — which §5 says is a
correct *failure mode*, never parity, and files a tracked gap. Two were not clean declines at all: the
`Qalg` repr crossed the wire as an `isError=False` **success** carrying corrupted content, and a
truncated catalog is a silent omission with **no error surface whatsoever**. The `.mcpb` manifest
attested 516 tools with an internally consistent `tool_count` and a valid sha256 — the worst failure
shape available, because nothing in the artifact reveals it.

## 8. Consequences

- **The layer has an owner.** A question about `describe()`, the tool schema, the generated registries,
  the Rosetta ledger, `carrier_schema`, the worked-example gates, or the alias descriptors resolves
  here first, and to ADR-0007/0009/0010 for the edges those own.
- **Reviewers have six named clauses.** "Which of C1–C6 does this landing satisfy, and which gate
  selected it?" is answerable by inspection. As of **rc414**: C1 gated; C2 **param half** gated, return
  half open; C3 gated; C4 gated; **C5 gated by `tests/test_wire_round_trip_rc414.py`** (this line read
  "C4 and C5 gated" as of rc363 and was false for C5 — it had no instrument and was refuted on its own
  exhibit; see §3.1 C5); **C6 stated and ungated**. A landing that claims an ungated
  clause claims it on a reading, not on a measurement — and §3.3 records that when C2's and C3's
  exhibits were closed by reading rather than by measurement, the reading was wrong about the
  baseline.
- **The ripple is nineteen classes of site, enumerated in §4, with the hand/regenerated split marked.**
  No brief should again be scoped from a prose sentence. `docs/srmech/CLAUDE.md` is not hygiene-gated;
  §4 is the reference, and §1.1 is the record of what happens when the reference is a stale sentence.
- **"Capstone" language now carries an obligation.** Declaring an arc complete requires stating the
  population. `composes`/`preserves` at 2 of 525 and `[[alias]]` at 0 descriptors-in-wheel are the
  named exhibits; a future declaration that cannot cite a population is not a declaration.
- **A count gate over an empty selected set is not evidence.** Where a gate's green is inert (§6.2), it
  must be recorded as a forward-guard, not cited as coverage. Conversely, an ungated clause must be
  named as ungated rather than assumed satisfied.
- **Decode-before-asserting-absence is mandatory** for any claim about a generated C registry (§7.2),
  and `tests/c_byte_arrays.py` is the single decoder — forking it is the defect the rc361 single-source
  instrument exists to stop.
- **Deriving capability axes from declared type strings is the standing weakness**, and it is now
  written down rather than rediscovered. The honest-type requirement (C2) is stated; the machinery to
  enforce it is deliberately left open (§6.3).
- **~~This ADR closes nothing.~~** True as drafted, and superseded by §3.3: v0.9.0rc363
  implements C2 (param half), C3 and the prose op-ref gate as strict-zero instruments, and registers
  the two carriers the C3 instrument found. The original sentence is kept struck rather than deleted
  because the DATE matters — the measurement it reports (`carrier_schema()` at 25 rows, no `Qalg`, the
  drift ratchet passing) is the pre-instrument state the rc363 injection reproduces on purpose.

## 9. Scope honesty — what this ADR does NOT claim

- **It does not claim the introspect layer is complete.** It defines the standard the open gaps are
  measured against — the same posture ADR-0009 §8 takes toward parity.
- **It does not propose new machinery the survey did not justify.** No new field, no widened ratchet, no
  new gate is specified. Three candidate requirements are explicitly **declined as UNSUPPORTED** (§6.3).
- **It does not re-litigate ADR-0007's ripple, ADR-0009's parity framing, or ADR-0010's move map.** §4
  enumerates what ADR-0007 §2.3 abbreviates; §7 states how introspect composes with 0009 without
  restating it.
- **It does not fault rc362.** Two of the five clauses were breached, both were named by gates the tree
  already owned, and both were drained rather than ceilinged inside the same rc. The two that remain
  open are the two no gate selects, which is a property of the layer, not of the landing.
- **Its measurements are a dated snapshot.** Taken 2026-07-29/30 against `0.9.0rc362` on branch
  `srmech-rc362-acoustic-domain` at `43552be5a` plus in-flight working-tree edits, `HAS_NATIVE=False`
  on the primary host with cross-checks on a native WSL2 host. Several figures moved *during* the
  survey — `CURATED` 516 → 525, the coercer ratchet red → green — and §1.2 records which.
- **It does not assert the §6.2 list of uninformative gates is exhaustive.** Five were found at
  drafting and verified by counterfactual or by census; **rc363 added a sixth** — the
  build-conditional C-parity row — which is itself evidence that the list is not exhaustive.
- **~~It carries no C-side or codegen change.~~** True of the ADR as drafted; **false as of
  rc363**, which implements it. The implementation regenerates `srmech_tool_registry.c` and
  `srmech_carrier_registry.c` (26 → 28 carrier rows), widens eight declared param types, and adds five
  `_PARAM_COERCERS` keys. Recorded here rather than quietly dropped: an ADR that says it changes
  nothing and then changes something is the same shape of stale claim §1.1 is about.
- **⚠️ It did not, until rc415, have an intake path for a defect in an EXISTING op.** C1–C6 all select
  on a LANDING — a new op, a new declared type, a new surfaced carrier. Nothing in this ADR selects on
  an op that shipped correct and has since gone stale, and a layer whose contract only fires at
  registration will drift exactly where nothing is landing. Measured cost of the omission, rc414:
  ADR-0009 §1.2 carries two rows verdicted **"Still open"** whose capabilities closed at rc281 and
  rc306 — `srmech_genome_amplify` (`c/include/srmech.h:8778`) and the caller-arena
  `srmech_genome_section_counts_arena_bytes` (`c/include/srmech.h:8583-8620`) — one of them
  contradicted by ADR-0009's own §8 four paragraphs later; and that §8 lists eight capabilities as
  open, all eight of which now have whole-op C entry points.
  **Intake clause (rc415, `#T1098`): a defect found in an already-shipped op enters through the same
  clause set as a landing.** The rc that finds it either (a) fixes it in that rc, or (b) records it in
  the owning ADR's clause table with an instrument or an `expiry:`, per §3.2. "Found, noted, not
  scheduled" is §3.2's defect wearing a different hat, and it is what produced the two rows above.
  This bullet does not widen a ratchet or add a field — the survey did not justify new machinery
  (§9 bullet 2) — it names the selector the six clauses do not have.

## 10. Sources

`srmech/introspect/__init__.py` (`describe()` at `:722`; the ROOT/INDEX contract at `:736-739`) ·
`srmech/introspect/tool_schema.py` (the SSoT) ·
`srmech/introspect/carrier_schema.py:171-177` (the carrier admission rule this ADR's C3 restates) ·
`tests/test_carrier_schema_rc205.py:310-326` (the drift ratchet, and its type-string scope) ·
`tests/test_worked_examples_strict_zero_rc353.py` (strict-zero by user direction 2026-07-28 — **no
`CEIL_` dict, no per-category allowlist**) ·
`tools/run_worked_examples.py:198` + `tests/test_worked_examples_execute_rc354.py` ·
`tests/test_tool_example_input_schema_rc355.py:137-139` ·
`srmech/mcp/_tools.py:209` (the `"string"` fallback) · `srmech/mcp/_coercion.py` (the inbound
strict-zero ratchet; `serialise_native`'s rc231 comment) ·
`tests/c_byte_arrays.py` (the single byte-array decoder, extracted rc361) ·
**rc363 instruments** — `tests/coercion_boundary.py` (the second, source-derived channel, and the
single source of `NON_CARRIER_CLASSES`) · `tests/test_declared_type_honesty_rc363.py` (C2, param
half) · `tests/test_carrier_use_derivation_rc363.py` (C3) ·
`tests/test_prose_oprefs_resolve_rc363.py` (the prose op-ref gate, `#T1045`) ·
`tests/test_class_catalog_oprefs_resolve_930.py` (the `#T930` model the prose gate extends) ·
`tests/rosetta_roots.py` · `tests/rosetta_classification.ndjson` ·
`srmech/amsc/_tool_docs_curated.py` (the hand-authored codegen input) ·
ADR-0004 §4 (the `[[alias]]` layer) · ADR-0006 (carrier discipline) · ADR-0007 §2.3 (the ripple) ·
ADR-0009 §4–§5 (the exemption rule; a clean decline is a failure mode) · ADR-0010 Amendment A.3–A.4
(the byte-array trap and the cardinality-pin blindness, found independently from the rename direction) ·
`[[project_introspect_surface_is_the_api_contract_not_documentation]]` (the stance this ADR codifies) ·
`[[user_stance_co_equal_dual_construction_is_a_consistency_oracle]]` ·
`[[feedback_a_zero_census_is_basis_free_a_nonzero_one_is_gauge]]` ·
`[[feedback_an_instrument_that_cannot_return_otherwise_is_not_a_measurement]]` ·
`[[feedback_false_green_comments_and_dead_instrumentation_seams]]` ·
`[[feedback_public_callable_ripple_gate_carrier_registry_and_rosetta]]` ·
`[[feedback_dont_ship_partial_unproven_difficulty_is_not_an_excuse]]`

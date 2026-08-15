# ADR-0013: The explanation surface — srmech's self-information layer

**Status:** 🟢 **Implementing** — the fifth lifecycle state, formalised by rc409. Direction accepted;
the surface is **named** and its shape is **measured**; its **encoding is deliberately open**. This is
a *pre-scoped* decision: §11 states which clauses have instruments today and which do not, and the ADR
does **not** claim acceptance for the uninstrumented ones. That is precisely why it ships 🟢 rather
than ✅ — per ADR-0012 §3.2, *a clause without an instrument that can return otherwise is not a
clause, it is a preference*, and a preference labelled as such is honest where one counted as coverage
is not.
**Clauses:** audited.
**Date:** 2026-08-06.
**Authors:** Steven Kirkland + Claude Opus 5.
**Supersedes:** none.
**Superseded-by:** none.
**Amends:** **none.** This ADR **extends ADR-0012, it does not amend it** — nothing in 0012 is revised,
narrowed or contradicted. It occupies a gap 0012 explicitly left open; see §1.6 for the warrant, quoted
verbatim.
**Relates-to:** **ADR-0012** (introspect IS the API contract — this ADR names one of the open gaps that
ADR defines the standard for; C1–C6 are not restated here) · **ADR-0009** (multi-implementation parity
— the explanation surface is compiled into the C registry, so it is parity-bearing, not a Python-side
docs concern; §7) · **ADR-0004** (config-driven surface — the encoding question §9.1 leaves open is
partly an ADR-0004 question) · **ADR-0010** (namespace declustering — `tool_schema` and its two
generated peers now live under `srmech/introspect/`, not `srmech/amsc/`; every path in this ADR is
post-declustering) · **ADR-0007** §2.3 (the release ripple these three files ride).
**Motivated by:** eight retrieval failures in a single agent session working ON this codebase, every
one over capability that had already shipped — and every one a **confident wrong answer supplied by
training**, never a blank (§1.2).

---

## 1. Context — a calculator has no idea what it does

A calculator has no idea what it does. Its knowledge lives somewhere else: in a user manual, and in
the decades of formal education the user brings to the keypad. Press `√` and the machine produces a
number; it holds no account of what a square root *is*, when you would want one, or what you would
otherwise wrongly hand-roll. **A calculator is therefore bounded by the user's domain vocabulary.** It
can only be reached by someone who already knows the name of the thing they want.

srmech's claim is the opposite one, and it is a claim about *identity*, not about polish:

> **The manual, the decades of domain knowledge, and the simulate-and-analyse are a continued
> description of what srmech IS** — not documentation *about* a tool, but part of the tool.

That is the whole reason this layer belongs in **introspect** and not in a `docs/` directory. Prose in
`docs/` is a description of an artifact. Prose on the `ToolEntry` is the artifact describing itself,
and it travels inside the wheel and across the C wire with the callable it describes. A `docs/`
directory cannot be queried by the agent composing a cascade; the introspect surface is exactly the
thing that can.

The consequence, stated once because it is the design pressure behind every decision below: **if
srmech is bounded by the caller's domain vocabulary, it is a calculator.** The surface named in this
ADR is what makes it not one — and §6 measures that today the surface is *authored* but not
*reachable*, which is the same failure wearing better clothes.

### 1.1 The reason the surface must exist — user direction

> *"we must do something different to make 'reach for srmech for all maths' also let you know how to
> reach in the first place. I'd hoped that this would become emergent from usage, but it just keeps
> getting pushed out by static LLM weights for a world made out of only established python libraries."*

This is the ADR's core argument, and the second sentence is the load-bearing one: **emergence was
tried and it lost.** Not to indifference — to a competing signal that is always present, always
confident, and always earlier.

### 1.2 It is a COMPETING-PRIORS problem, not an ignorance problem

**All eight measured failures were confident wrong answers supplied by training, never blanks.** That
distinction decides the whole design. An ignorance problem is solved by adding information. A
competing-priors problem is not — the information was already there, and something else answered
first.

Every row below is a real capability that ships. Verified on this branch by direct lookup:

| the trained reach | what actually ships | verified |
|---|---|---|
| `decimal` for a logarithm | `srmech.math.rational.log` · `…rational.log1p_series_truncate` | both `lookup()` OK |
| `math.gcd` | `srmech.math.cyclic.gcd` | `lookup()` OK |
| filed `mat_rank` as a **GAP** — because numpy has `matrix_rank`, so srmech was assumed not to | **`QMat.rank(self, *, method: str = "auto")`** — `srmech/math/qmat.py:447` | method exists; `resolve_all('rank')` → **`()`** |
| wrote `srmech.math.rational.Q` — "rational" is the *world's* word (`fractions`, `sympy.Rational`) | **`srmech.math.q.Q`** — `srmech/math/q.py:234` | correct module confirmed |
| guessed `all_entries()` / `REGISTRY` / `ENTRIES` — the names *libraries* use | `get_tool_schema()` (`introspect/tool_schema.py:785`) · `tool_schema_view()` (`:809`) | `all_entries` → **no such name** |

**The `mat_rank` row is the sharpest and deserves its own sentence**, because it is not a retrieval
failure at all — it is the index being scoped narrower than the capability surface, and saying so in a
field nobody reads. `describe()["tools"]["covers"]` states verbatim: *"registered module-level ops
only; **carrier/class methods are not indexed here**"*. `rank` is a method. So an agent consulting the
index and concluding "srmech has no rank" **read the index correctly and got a false answer about the
package.** ADR-0012's INCOMPLETE IS AS BAD AS FALSE, instantiated.

### 1.3 The bootstrap is circular — which is why emergence cannot close it

Knowledge accumulates through usage · usage requires reaching · reaching requires knowing what is
there. **Without an index the cycle never closes, and every session restarts from the trained prior.**
Emergence is not slow here; it is structurally blocked. A loop with no entry point does not converge
given more laps.

**The detector works. The referral is missing.** The project's standing rule — *catching yourself
reaching for another math module IS the gap signal* — fired repeatedly and correctly in the session
that produced these eight. But **when it fires there is nowhere to consult**, so the fallback is the
prior anyway. That is the precise shape of the defect: **a working instrument with no referral path.**

The tree already anticipated this exact failure and wrote the counter-instruction into the one organ
that cannot be reached. `srmech.math.cyclic.gcd`'s SIBLINGS clause, verbatim:

> **SIBLINGS — READ THIS BEFORE FILING A GAP.** […] **Do not reach for `math.gcd` inside a cascade:**
> the value is identical, but the stdlib call is invisible to the DSL declarer, the tool schema and
> the introspect writer.

An instruction naming the precise trained reach (`math.gcd`), and an instruction against the precise
error that was in fact committed for another op (filing a gap) — both authored, both shipped, both
unreachable. *(Honest bound: that exact `READ THIS BEFORE FILING A GAP` sentence appears in **1 of
556** explanations. It is one author's note, not a convention — its force here is as an exhibit that
the knowledge existed, not as evidence of a systematic practice.)*

### 1.4 Therefore the acceptance criterion is TEMPORAL, not merely correctness

The standard this surface is measured against is **not** *"can it find gcd?"* It is:

> ### **Does srmech's answer arrive BEFORE the habit fires?**

**An answer that arrives after `import math` has already been written has lost, even when it is
right.** This is what distinguishes the explanation surface from documentation in the ordinary sense:
documentation is judged by whether it is correct and complete when consulted, and this surface is
judged by whether it *wins a race it is currently not entered in*. Every reachability measurement in
§6 should be read against that clock, not against a coverage percentage.

### 1.5 Why the AFFORDANCE organ is load-bearing rather than ornamental

Training knows densely and reliably what a gcd *is*. So **identification competes with training and
loses** — it is the one thing the prior is strongest at, and srmech's version arrives later.

Training cannot supply *"**this project** reaches for gcd when reducing gear-train ratios and dial
realignments"*, because that is **not a fact about mathematics but about this substrate's use of it.**
No corpus contains it. **Identification competes and loses; affordance does not compete at all.**

That is why the WHEN organ is the asset and why its unreachability is the defect. Measured:

| probe | in `summary` | in `explanation` | in `example` | entries touched | `resolve()` |
|---|---|---|---|---|---|
| `gear` | **0 / 556** | 13 | 27 | 36 | `None` |
| `winding` | 12 | 22 | — | **26** | `None` |
| `chirality` | 31 | 49 | — | 65 | `None` |
| `eigen` | 48 | 76 | — | 107 | `None` |

`srmech.math.cyclic.gcd`'s WHEN clause, verbatim from the shipped entry:

> WHEN — reach for it any time two periods, tooth counts or moduli must be reduced to their common
> sub-period: **gear-train ratio reduction, dial realignment**, reducing a `(num, den)` pair before it
> enters a Class-N chain.

**`gear` appears 0 times across all 556 summaries** — the advertised index — while the vocabulary
training could never have supplied was authored 36 entries deep in the unadvertised half. The word was
written down and structurally unreachable. That is not an authoring failure; it is an addressing
failure, and it is the subject of this ADR.

### 1.6 The warrant — ADR-0012 left this gap open on purpose

ADR-0012 is titled *"The introspect surface IS the API contract — autonomous composition, **not
documentation**"*. Its §9 states, verbatim:

> **It does not claim the introspect layer is complete.** It defines the standard the open gaps are
> measured against — the same posture ADR-0009 §8 takes toward parity.

**The explanation surface is exactly such a gap.** ADR-0012 names the *standard* (autonomous
composition; INCOMPLETE IS AS BAD AS FALSE) and enumerates eight surfaces over one SSoT. It does not
name the `explanation` + `example` payload as a surface in its own right, and its surface-1 row treats
those two fields as *fields the SSoT carries* rather than as a layer with its own consumers, its own
organs and its own addressing problem. This ADR names it, without revising a word of 0012.

### 1.7 Three grains — and why the answer is NOT a hand-written usage guide

**User question, 2026-08-06:**

> *"then should we have some general usage guide alongside the srmech notebook that delves into
> everything we've added, beyond architecture?"*

The question is the right one and its answer is a **decision this ADR must record**, because the
obvious response — write a guide — would violate two standing constraints and manufacture a third
drift surface. srmech's self-information is stratified by **grain**, and the three grains are in
radically different states:

| grain | home | state (measured; per-row basis noted — the registry is 559 at rc411, `composes` re-measured at rc412; **both `composes` and `preserves` re-measured at rc423 on a 605-op registry**, §1.7.2) |
|---|---|---|
| **ARCHITECTURE** — the A-N vocabulary, the substrate claims | `srmech_research_notebook.md` (7,373 lines) | **DRIFTING** — highest rcN it mentions is **rc399**; shipped is rc412; **26** `docs/srmech/python` commits landed since it was last touched; **zero** currency gates |
| **PER-OP** — what one op is, means, and demonstrates | `summary` + `explanation` + `example` | **COMPLETE** — 559/559 on all three post-rc411, ~2.05 M chars, floor-enforced (§4) |
| **DECOMPOSITION** — what sub-ops this op is built from | `composes` | **9 / 559** post-rc412 (was 2/559); set derivable, order hand-traced — see §1.7.1. ⚠️ **Superseded by rc423 (`#T1113`): 164 / 605** — the POPULATION pass, adjudicated by tier rather than hand-traced row by row (§1.7.2) |
| **INVARIANT** — what guarantees this op maintains | `preserves` | ~~**2 / 559**, deliberately held pending a taxonomy~~; *not* the same grain as `composes` — see §1.7.1. ⚠️ **The HOLD is LIFTED at rc423 (`#T1113`)**: **13 / 605** rows (the count moved with the registry, not with a population drive), and the taxonomy the hold was waiting for now exists — **10 kinds DERIVED from the shipped rows**, all 21 invariant strings classified with no residue, enforced at **strict zero** by `tests/test_preserves_taxonomy_rc423.py`. The *"not the same grain as `composes`"* half of this row still stands (§1.7.2) |
| **PER-TASK** — which ops go together to do X | `composes`, **lateral branch** | **1 / 559** — `best_rational_signed` only; the branch is declared by the field contract (`tool_schema.py:366`, `:370`) and almost unpopulated. This row read **"NO HOME — does not exist anywhere"** until §1.7.1a retracted it — see §1.7.1 |

#### 1.7.1 ⚠️ CORRECTION (2026-08-07) — this table originally named the wrong home

**As first written, the row above read `PER-TASK … | composes / preserves | EMPTY 2/556`. That was
wrong, and the error mattered, because it implied populating `composes` would close the per-task gap.
It would not.** Corrected on measurement (rc412 design research, run `wf_a0dd4fbf-9b8`, 9 agents with
adversarial verification; the leg that first raised it was itself returned `holds=false`, so the
structural core below is carried as the synthesis pass's own re-derivation, not that leg's claim).

**The contract is the dataclass field comments at `introspect/tool_schema.py:365-383` — the SSoT,
not CHANGELOG prose. Quoted in full, because a truncated quotation of it is what produced the
retracted claim below:**

> *v0.9.0rc305 (`#T943`) — the Siona compose-a-cascade capstone. `describe()` / `example` are PER-OP;
> **a cascade is CROSS-OP. These two fields carry the chaining knowledge** that otherwise lives only
> in CHANGELOG prose Siona cannot read as data.*
>
> *`composes` — the ORDERED sub-ops this op is built from **(or that a declared cascade chains)**.
> Empty for a LEAF op (the correct default); the call-order sequence of registered op names for a
> composite.*

So the field has **two declared branches**, and the contract names them in its own first sentence:
a **DOWNWARD** branch (implementation decomposition — what X is made of) and a **LATERAL** branch
(what a declared cascade chains — which is the per-task question). The per-task grain is therefore
**not homeless; it has a declared home that is nearly unpopulated.**

##### ⚠️ 1.7.1a RETRACTION (2026-08-07, same day) — the paragraph above replaces a false one

As first published, §1.7.1 cited this contract as `tool_schema.py:**317**-331` and quoted it as
*"the ORDERED sub-ops this op is built from **…** Empty for a LEAF op"*. Both are defects, and they
compound:

- **The cited range starts four lines below the sentence that refutes it.** The contiguous `#:`
  block begins at `:313`; `:314` is *"a cascade is CROSS-OP. These two fields carry the chaining
  knowledge"*. Citing `:317` excises it.
- **The ellipsis elided `(or that a declared cascade chains)`** — the parenthetical that states the
  lateral branch outright.

Both excisions land on the lateral branch and nothing else. `grep` for `CROSS-OP` / `declared
cascade` over §1.7.1 as first published returns **zero hits**: the ADR argued the branch does not
exist, from a quotation constructed by removing every sentence that says it does.

**The positive evidence was one sentence at n = 2** — *"Both shipped rows are exactly downward
traces"* — in a paragraph that elsewhere calls their co-population *"an accident of authorship"*.
A two-row census cannot separate *"the field is downward-only"* from *"only the downward branch has
been used yet"*. That is `[[feedback_an_instrument_that_cannot_return_otherwise_is_not_a_measurement]]`
and `[[feedback_a_zero_census_is_basis_free_a_nonzero_one_is_gauge]]`, applied to a field contract
rather than to a number.

**And the lateral branch is already populated, at n = 1.**
`srmech/cascade/catalogs/cascade_catalog/best_rational_signed.toml:41` declares
`operation = "pin_slot_at_zero -> best_rational(...) -> reorient"`, and
`tests/test_composes_grain_rc412.py:146-150` declares `composes` as that identical three-tuple,
verbatim. For a declared cascade the downward decomposition and the lateral chain **are the same
tuple** — which is precisely why every gate stayed green under both readings, and why the
substitution registered as a clarification rather than as a scope deletion. No instrument in the
suite could report a difference.

**Procedural note, recorded because it is the reusable part.** §1.7.1's own commit body disclosed
that *"the leg that first raised this was returned `holds=false`, so the structural core is carried
as the synthesis pass's own re-derivation, not that leg's claim."* The re-derivation's entire
evidentiary base was the n = 2 census above — i.e. the rejected leg's evidence, re-attributed. **A
re-derivation whose only evidence is the refuted leg's evidence is a re-attribution.** When a
`holds=false` verdict is carried forward anyway, the carrying pass must supply its own falsifier and
its own sample size, stated inline; here, asking *"what population would refute this?"* forces
*"is any row using the other branch?"*, and the answer was already in the tree.

**What survives, and what does not.** `composes` and `preserves` being two features rather than one
(next paragraph) **stands** — it rests on the gate asymmetry, not on the citation. The table row is
corrected from **NO HOME** to a declared-but-unpopulated home. §2.3's four readings remain per-op.

**`composes` and `preserves` are TWO FEATURES, not one.** They share a Python type and nothing else.
The asymmetry is already enforced inside the single gate file: `test_composes_preserves_rc305.py:126`
checks every `composes` entry for **registry membership** (referential integrity into the op graph),
while `:147` checks `preserves` only for non-empty strings. `composes` is a typed traversable edge;
`preserves` is unconstrained prose — its six shipped strings already span **five** distinct claim-kinds
(round-trip invariant, cross-op measurement agreement, implementation discipline, precision bound,
honest-null guarantee) under one key with no taxonomy and no checker. That they are co-populated on the
same two rows is an accident of authorship: a leaf op with a real invariant and no composition is legal,
and unrepresented.

⚠️ **rc423 (`#T1113`) amends the second half of that sentence, and STRENGTHENS the first.** *"…with no
taxonomy and no checker"* was true when written and is now false on both counts: `preserves` has a
**10-kind taxonomy** (ALGEBRAIC · ROUND_TRIP · EXACTNESS · HONEST_NULL · PURITY · IDEMPOTENCE ·
IMMUTABILITY · DESIGN_CONTRACT · CROSS_CHECK · IMPLEMENTATION_DISCIPLINE) and a **strict-zero checker**
— an unclassified `preserves` string now fails CI (`tests/test_preserves_taxonomy_rc423.py`). The
five-kinds-under-one-key observation was the right diagnosis; ten kinds is what the same reading finds
at 13 rows / 21 strings instead of at 2 rows / 6 strings. **The TWO-FEATURES point stands and is now
enforced separately on each side**: `composes` is gated on registry membership and, since rc423, on a
tier-adjudicated population census; `preserves` is gated on taxonomic classification. Two features, two
instruments, neither substitutable for the other.

**So §2.3's four readings remain per-op.** What §1.7.1a changes is the per-task row: it has a
**declared home that is almost unpopulated (1/559)**, not no home. The original §1.7 was closer to
right than the "correction" that replaced it — it said `composes` was the home and measured it
empty; the error there was only the *count*, not the *address*.

**One consequence that is code, not prose, and must not be left implicit.**
`tests/test_composes_grain_rc412.py:712` (`test_every_declared_sub_op_is_actually_called`, clause 2)
requires every declared sub-op to be **AST-call-reachable from the parent**. That is correct for the
downward branch and **structurally wrong for the lateral one**: a declared cascade chains ops that
the parent does not call. As written, the next attempt to populate the per-task grain fails CI and
is read as *"the field does not support this"* — hardening the retracted conclusion into a test,
where it would be far harder to see. Either scope clause 2 to rows not sourced from a cascade-catalog
descriptor, or add a second admission path validating a declared-cascade row against its descriptor's
`operation` chain. Tracked as `#T1096`.

✅ **`#T1096` is CLOSED — rc417 (`#T1100`) took the second of the two options above.** Verified against
the file on this branch: `_descriptor_chain(name)` reads the parent's own
`srmech/cascade/catalogs/cascade_catalog/<leaf>.toml` `operation` string, and clause 2 now admits a
sub-op that *either* the call graph reaches *or* the parent's own descriptor chains — so a
declared-cascade row is no longer a red. Two details are worth carrying, because they are what keeps
the fix from being the loophole this paragraph feared: the descriptor lookup is by **exact leaf name,
in that one directory, reading only `operation`** (a parent with no descriptor gets no second path);
and the admissions are **printed, not absorbed** (`test_descriptor_admissions_are_reported`), so a row
that starts leaning on the TOML instead of the call graph is visible the run it happens. **Today every
ROSTER row still passes on the call-graph path alone**, so the second path currently admits nothing —
it was landed before it was needed, precisely so the first lateral row would not arrive as a red
accusing a correct declaration of being wrong.

⚠️ **Two line references in the paragraph above have moved and are kept for the record rather than
rewritten.** `test_every_declared_sub_op_is_actually_called` was at `:516` when this was written; it is
at **`:465`** on this branch, and `_descriptor_chain` is at **`:422`**. The function did not move
*down* as the file grew — it moved *up*, because rc423 lifted the derivation instrument OUT of this
file into `tests/composes_derive.py` (single-sourced there, since two gates now consume it).

**Measured for the record** (identity-resolved AST call-graph over the 559 resolved callables, following
function-local `ImportFrom` aliases through unregistered private helpers) — **this is the rc412-era
measurement, at the 559 registry; it is preserved, not superseded**:

| depth | non-empty | edges | ground truth recovered |
|---|---|---|---|
| 1 | 237 / 559 | 364 | 5 / 7 |
| 3 | 342 / 559 | 643 | **7 / 7** |

**Re-measured at rc423** (`#T1113`) with the same instrument — now single-sourced at
`tests/composes_derive.py` — over the **605**-op registry:

| depth | non-empty | zero-reach | basis |
|---|---|---|---|
| 1 | **256 / 605** | 349 | `derived(name, depth=1)` |
| 3 | **347 / 605** | **258** | `derived(name, depth=3)` |

**The 258 is the load-bearing figure and it is a positive statement, not a shortfall.** Those rows
reach no registered sub-op at depth 3 — *"this op composes nothing registered"* as a MEASURED claim,
which is exactly what `tool_schema.py` calls the correct default for a leaf. They are the reason a
coverage floor over this field would be wrong (ADR-0012 §6.1), and the reason the rc423 ratchet is
scoped to the **unadjudicated residual** instead (§1.7.2).

**The SET is derivable; the ORDER is not.** Lexical first-call order matches **0 of 2** ground-truth
rows, because a native fast-path branch calls `genome_save`/`genome_census` ahead of the pure path a
human traced — and the contract says ORDERED. Any future population is therefore derivation for the
set plus human tracing for the sequence, never derivation alone.

**This finding is why rc423's mechanical tiers stop at ONE sub-op**, and it survives that rc intact. A
`SINGLE`-tier row is admissible precisely because a one-element tuple has exactly one ordering — the
order is *forced*, not derived, so no human tracing is skipped. The moment a row has two direct call
edges the ordering becomes a human act again, and rc423 leaves every such row **unenumerated**
(§1.7.2's RESIDUAL). The rule above is not a constraint rc423 worked around; it is the rule that drew
the tier boundary.

⚠️ **And the field is unread.** `srmech/introspect/search.py::_op_fields` indexes exactly `name`,
`category`, `summary`, `explanation`, `example.*`. **rc411's search surface does not index `composes`
or `preserves`.** Their only consumers are `to_jsonable` (`tool_schema.py:503-505`), the curated merge
(`_apply_docs`, `:578-581`), and the C serialiser. Populating an unread field moves a hash and nothing else — which is
why any rc that populates them must ship a **reader** first.

**Post-rc412 addendum (2026-08-07).** rc412 (`#T1093`) acted on this section and changed two of its
numbers, so read the figures above as current and §1.7.1's body as the rc411-basis correction that
prompted them. It found the cause **one layer below population — nothing READ either field**
(`search.py::_op_fields` indexed neither), and shipped `ToolSchema.composition()` **before** adding
rows: a traversal in **both** directions, because `composes` points downward and the question a caller
actually holds is the reverse edge — *what is built FROM this?* — which previously required walking all
559 rows. `composes` then went **2 → 9** rows (7 → 27 references), hand-traced under a stated criterion,
with a three-clause gate that fires on undeclared population as well as deletion. `preserves` was left
at 2 on purpose. **A measurement worth keeping: indexing `composes` in search wins the `why`
attribution on 0 of 27 references** — a row's own prose almost always already names the ops it composes
— so the index alone would have been a reader that provably reads nothing.

#### 1.7.2 Post-rc423 addendum (`#T1113`) — the POPULATION pass, and the ratchet's exact scope

rc412 shipped the reader and nine hand-traced rows. **rc423 shipped the population**, and it did so by
**adjudication into tiers** rather than by row-by-row tracing, because tracing 605 rows by hand is the
filler ADR-0012 §6.1 warns about wearing a coverage number. Registry = **605** ops. Census generated by
the committed script `docs/srmech/notes/_composes_population_census_rc423.py`; the per-row verdicts ship
as a ledger at `docs/srmech/python/tests/composes_adjudication_rc423.ndjson`.

| tier | count | the rule that admits a row |
|---|---|---|
| **DECLARED** | **16** | hand-traced multi-op, pinned row-by-row in `test_composes_grain_rc412.py::ROSTER` |
| **SINGLE** | **148** | `derived(name, depth=1)` is a **SINGLETON** — the op's own body directly calls exactly one registered op, so the ordered tuple is **FORCED** (one element has one ordering) |
| **LEAF** | **258** | `derived(name, depth=3)` is **EMPTY** — *"composes nothing registered"*, as a MEASURED statement |
| **REFUSED** | **1** | tier-eligible and **deliberately declined**: `srmech.math.covering.covering_catalog`, which rc422 read and judged to *consult* `spin8_center` rather than be *built from* it |
| **RESIDUAL** | **182** | two or more direct call edges — **the ORDER is a human act**, so the row is NOT enumerated |

**Adjudicated 423 of 605.** `composes` population moved **16 / 605 → 164 / 605** (DECLARED + SINGLE).
`preserves` stayed **13 / 605** — deliberately not seeded; see the taxonomy note on §1.7's INVARIANT row.

**The REFUSED tier is one row and it is the most informative one**, because it is the only tier whose
admission rule is *a human said no*. A singleton call edge is mechanically eligible; consulting a
catalog is not the same relation as being built from it, and a tier that could not record that
distinction would have silently converted a judgement into a measurement. One row is enough to prove the
tier can return otherwise.

⚠️ **The ratchet is `CEIL_UNADJUDICATED = 182`, down-only, and its scope is the distinction this whole
section turns on. It is a ceiling over the UNADJUDICATED RESIDUAL — NOT over "unpopulated rows".** Those
are different sets and conflating them would re-file the LEAF tier as debt. A LEAF row is **permanently
and correctly empty**; driving it to a population would be inventing edges. What was genuinely wrong
before rc423 is that **an unexamined row and a measured leaf were indistinguishable in the field** —
both read as `composes = ()`, and no instrument could tell them apart. Only *that* distinction gets a
ceiling, and it drains toward the rows where order is a human act and the human act has not happened.

**Honest status of the `preserves` half: population unblocked, execution owed.** The taxonomy assigns
each of the ten kinds a **VERIFIABILITY class** (EXECUTABLE / STRUCTURAL / PROSE), and **8 of 10 are
EXECUTABLE** — meaning a machine *could* run the op and check the claim. Nothing does yet. That is a
**NEW obligation the taxonomy created**, not a survival of the old hold: the hold asked *"what kinds are
there?"* and has been answered; the open question is now *"does the op actually do what the row says?"*,
which could not even be asked before the kinds existed.

**A hand-authored guide is the wrong instrument, for three separable reasons.**

**(a) It would be a second encoding of content that already exists.** ADR-0011 states verbatim: *"If a
legible view is wanted, derive it on demand through the tool surface; do not persist it."* ~2.05 M
characters of per-op usage prose already ship at 100 % coverage. A guide restating it is precisely the
persisted duplicate 0011 forbids — and the per-op grain is the grain a guide would naturally target,
because it is the grain that already has content to copy.

**(b) It would be a sidecar.** The standing stance is that research notebooks stay monolithic — fold
material *directly in*, never alongside. A companion usage document is the sidecar shape by
construction.

**(c) It would rot, and we have the measurement proving it.** The architecture notebook is the control
experiment: hand-maintained prose about a moving tree, no gate, **11 rcs stale**. A guide restating
2.05 M characters that change every rc would drift faster, because it restates more.

**The real gap the question points at is the PER-TASK grain, and this ADR does not currently cover
it.** §2.3's four readings — identification, contract, affordance, demonstration — are **all four
per-op readings**. Every one answers a question of the form *"what about THIS op?"*. None answers
*"which ops compose to do X?"*. The score metaphor holds and sharpens the point: four readings of one
op's staff is still one staff. A task is a **passage across staves**, and no reading of a single staff
recovers it.

**Decision recorded here (execution tracked as `#T1093`, blocked behind the rc411 index):**

1. **No hand-authored usage guide.** Any usage view is **DERIVED** — generated on demand from
   `summary` + `explanation` + `example` + `composes`, riding the same index the reachability deficit
   (§6) requires. One encoding, no sidecar, no new drift surface.
2. **`composes` / `preserves` are a real gap, but NOT the per-task one** — see §1.7.1. rc305 shipped
   those fields as the composition layer; the *mechanism* landed and the *content* never did
   (**2/559** each, re-measured post-rc411, 0.36 %). What they record is **downward decomposition**;
   ~~the per-task question is lateral, and has no home at all~~.
   ⚠️ **Two amendments, both to this bullet's tail.** The *"no home at all"* clause was retracted by
   §1.7.1a the day after it was written — the lateral branch has a declared home that is nearly
   unpopulated. And the **2/559 each** figure is the rc411 basis: at rc423 it is **`composes` 164/605 ·
   `preserves` 13/605** (§1.7.2). The bullet's *decision* — that these fields are not the per-task
   grain — is unaffected by either.
3. **The per-task grain is named here as OUT of the four-readings decomposition**, not silently folded
   into it. Whether it becomes a fifth reading, a distinct surface, or a derived join over an
   *inverted* `composes` graph is **open** and deliberately not decided by this ADR.

⚠️ **Limits on the numbers above, stated so they are not over-read.** The `composes`/`preserves`
census counts **non-empty, not good** — a one-word value scores identically to a real one, so 2/559 is
a **floor on the gap**, not a quality assessment. *(⚠️ The non-empty-not-good caveat still applies at
rc423's 164/605 — with one narrowing: the 148 `SINGLE` rows are not merely non-empty, they are pinned by
an EQUALITY against the depth-1 call graph, so a wrong or fabricated sub-op on one of them fails CI.
§1.7.2. The `preserves` side gained the peer property: a string is no longer merely non-empty, it must
classify into a declared kind.)* It is measured on the **rc409** registry; rc411
(`#T1079`) took the registry to 559; **re-measured after it landed: still 2/559 each** — rc411 added three rows and populated neither field. And **559/559 population on the
per-op fields is not a claim that the per-op grain is *correct*** — §6 measures that none of it is
reachable, and `#T1092` records a shipped field (`mcp_callable`) that is uniformly populated and
uniformly *wrong* on at least 17 ops. Full population is a coverage fact, never a truth fact.

---

## 2. Decision — what the explanation surface IS

**The explanation surface is the `explanation` + `example` payload carried by every `ToolEntry` and
mirrored on every `srmech_tool_entry_t`, as distinct from `summary`, which is the advertised index.**

Measured on this branch (basis: `list(get_tool_schema().tools)`, `N = 556`; char counts are `len()` of
the string, or `len(json.dumps(v, sort_keys=True))` for the `example` dict):

| field | population | chars | advertised? |
|---|---|---|---|
| `summary` | **556 / 556** | **381,358** | **YES** — the MCP `description`, the only prose any consumer reads |
| `explanation` | **556 / 556** | **743,186** | **NO** |
| `example` | **556 / 556** | **937,042** | **NO** |

The unadvertised half is **1,680,228 chars — 4.4× the advertised index.** Full population on all three
fields; the coverage floors (§4) are why.

### 2.1 The organ decomposition — WHERE WE ARE, not what it is

⚠️ **Read this subsection as a description of the present form, not of the target.** §2.3 states the
goal, which is different in kind: four **readings of one addressed set**, not four authored strings.
The four-field shape below is where the surface stands today, and §2.3 argues it is the wrong shape
for what it is being asked to do.

The payload is not one undifferentiated blob. It has **four organs**, and they answer four different
questions:

| organ | question it answers | population (basis: bare-token `\bWHAT\b` etc. over `explanation`) |
|---|---|---|
| `summary` | **identification** — which op is this? | 556 / 556 |
| `explanation.WHAT` | **contract** — edges, error behaviour, the C peer | 538 / 556 |
| `explanation.WHEN` | **affordance in the reader's domain vocabulary** | 527 / 556 |
| `explanation.SIBLINGS` | **disambiguation** — what you would wrongly re-derive | 550 / 556 |
| `example` | **grounded demonstration** — a real captured run | 556 / 556 |

Co-occurrence: **WHAT ∧ WHEN = 527 / 556 (94.78%)** · WHAT ∧ SIBLINGS = 532 · WHEN ∧ SIBLINGS = 521 ·
**all three = 521 / 556 (93.71%)**.

`example` decomposes further, and its sub-keys are separately populated:

| sub-key | population | what it is |
|---|---|---|
| `output` | **556** | the captured result |
| `why` | **556** | the one line saying what the transcript demonstrates |
| `worked` | **471** | a real REPL transcript with `# ->` captures |
| `input` | **389** | machine-readable argument values |
| `setup` | **97** | preconditions |

**These are not redundant, and flattening them into "docs" is what made them unreachable.** An agent
asking *"which op do I want for a gear train?"* needs WHEN. An agent asking *"will this raise on
zero?"* needs WHAT. An agent asking *"am I about to re-derive `lcm`?"* needs SIBLINGS. One string field
serving all three means no consumer can ask for one without taking all of them, and — §6 — no consumer
asks at all.

### 2.2 ⚠️ The organs are a CONVENTION, not a schema — and that is a finding

The organ markers are real and near-universal, but they are **prose inside one string field**, with no
delimiter contract. Measured over the first non-space character following the `WHAT` token:

| delimiter | count |
|---|---|
| `—` (U+2014 em-dash) | **325** |
| `:` (U+003A colon) | **130** |
| `-` (U+002D hyphen) | **37** |
| *no delimiter* (`WHAT it does…`, `WHAT IT…`) | **46** |
| *no `WHAT` token at all* | **18** |

**Three different delimiters across 492 delimited instances, plus 46 undelimited.** So the four organs
of §2.1 are separately *addressable in principle* and not separately *parseable in practice* without a
heuristic. Any future consumer that wants to select one organ (§5) must either adopt a delimiter
contract or move the organs into distinct fields. **This ADR does not choose between those** (§9.1) —
it records that the choice exists and that today the answer is "neither".

### 2.3 THE GOAL — four readings of one score

**User direction, and it is a decision about what the surface should become:**

> *"our goal is that our introspect surface become four readings of one score, even if it needs
> constructed of discrete subparticles."*

**The target: the organs become four TRAVERSALS of one addressed set, not four authored strings.**
Identification, contract, affordance and demonstration stop being four places prose is written and
become four ways one body of addressed content is read. §2.1's four-field form is the current
approximation to this; it is not the thing itself.

**Why the present form is not merely unpolished but expressively insufficient — measured.**

**(a) An atom may belong to more than one reading, and today you must say it twice or drop it.**
gcd's *"reduces two periods to their common sub-period"* is simultaneously **contract** (it is what
the op computes) and **affordance** (it is when you reach for it). Measured on the shipped entry, the
organs split cleanly at WHAT `[0:357]` / WHEN `[357:717]` / SIBLINGS `[717:1475]`, and:

| probe | WHAT | WHEN | SIBLINGS |
|---|---|---|---|
| `sub-period` | — | ✅ | — |
| `uint64` · `ValueError` | ✅ | — | — |
| **`lcm`** | — | **✅** | **✅** |

Two distinct failures in one entry. **`sub-period` is dropped from a reading**: the characterisation
lives only in WHEN, so a WHAT traversal cannot see the very thing the op computes. **`lcm` is said
twice**: it is authored in WHEN *and* in SIBLINGS, because both readings genuinely need it and the
form gives them no way to share.

At scale — *basis: the **521 of 556** entries whose explanation splits cleanly as WHAT < WHEN <
SIBLINGS; content words are `[A-Za-z_]\w{5,}`, stop-words removed; "shared" = appears in ≥2 organs*:

**513 of 521 entries (98.5%)** carry at least one content word in two or more organs — median **6**
shared tokens per entry, mean 5.9, max 16.

⚠️ **This instrument over-counts and must be read as an upper bound.** Lexical overlap is not proof of
semantic duplication: an op's own name, and common technical vocabulary, recur innocently. What it
establishes is that **cross-organ repetition is the norm rather than the exception**, which is what
the four-field form predicts. The gcd `lcm` case is the hand-verified instance; the 98.5% is the
population shape around it, not 513 proven duplications.

**(b) Sub-field granularity is the load-bearing allowance.** *"even if it needs constructed of
discrete subparticles"* is not a hedge — it is the enabling condition. **Readings are only
non-destructive if the underlying set is finer than any one reading needs.** Were atoms field-sized, a
reading wanting half of one would have to **cut** it — and cutting is construction, not reading. The
whole property depends on the atoms being smaller than the readings.

**(c) It dissolves a wart already recorded here.** §2.2 measures the WHAT/WHEN separation as a *string
convention* — em-dash 325 / colon 130 / hyphen 37 / absent 46. Under an addressed set the separation
is **structural**, and a reading becomes a **frame commitment** rather than a parse. §2.2's finding is
therefore not a defect to patch but evidence for this target.

**(d) The phrase is "address one way, read another" — NOT "build one way".** Addressing and reading
are both non-destructive; **building twice would mean two encodings**, which is exactly what §7
measures as the present cost and exactly what this must not reproduce.

The musical analogy is precise rather than decorative: **retrograde, inversion and transposition are
readings, not rewrites — the marks on the page do not move.** And the formal statement is
**`Lk = Tw + Wr`**: the linking number is what is *there* (invariant); twist and writhe are the
frame-relative decomposition that trades off with how you read. **Building would change `Lk`; reading
cannot.**

✅ **This is carrier-native, not an imported metaphor — srmech ships the theorem.**
`srmech.biology.genome.cwf_consistency_mod2` is the Călugăreanu–White–Fuller check `Lk = Tw + Wr (mod
2)`, with `discrete_writhe` supplying Wr and `quaternion_cycle_holonomy` supplying Lk. Its own shipped
explanation states the design rule that maps **exactly** onto the migration risk below:

> The load-bearing design rule is that **Wr is computed from geometry and NEVER as `Lk - Tw`**; that
> is what gives the check teeth […] A version that back-solved Wr would report True always and detect
> nothing.

**Read that as the constraint on any future decomposition: each reading must be derived from the
addressed atoms independently, never back-solved from the other readings.** A reading defined as
"whatever the other three did not take" is the back-solve, and it detects nothing.

**⚠️ MIGRATION CAUTION — recorded as a RISK, not as a plan.**

**556 ops × 3,022 chars of `explanation` + `example` is not obviously machine-decomposable.**
*(Measured: mean 3,022 chars per op on the `json.dumps` basis for `example`; 2,938 on a concatenated-
values basis; 1,337 for `explanation` alone. The coordinating brief said ~2,850 — my measurement
supersedes it, and the figure is basis-dependent as §6.2 requires.)*

**The content most at risk is the most valuable and the least recoverable: the WHEN clauses' domain
vocabulary.** §1.5 is the argument for why — it is the one organ training cannot regenerate, so a
decomposition that loses it cannot be repaired from any model's prior. And the failure would be
**silent**: a wrong decomposition yields a score that reads correctly in three organs and has quietly
lost the fourth's vocabulary. **Nothing currently gates that** — there is no instrument that would go
red (§11).

**The migration path is the hard part, not the target.** Naming the target does not license attempting
it without an instrument that can detect vocabulary loss first.

---

## 3. Decision — this is SELF-INFORMATION, not documentation

**The explanation surface is in scope for introspect and governed by ADR-0012's standard.** It is not
a docs backlog, not a nice-to-have, and not a candidate for a `docs/` directory.

Three measured facts make this a structural claim rather than a preference:

1. **It crosses the C wire.** `srmech_tool_entry_t` carries `explanation` (`c/include/srmech.h:5522`)
   and `example_json` (`:5520`). The gcd WHEN clause quoted in §1.1 is present in
   `c/src/srmech_tool_registry.c` as shipped text. For a bare-C / MCU host this prose IS the
   introspect layer — ADR-0012 §7.1 makes exactly that point about the generated registry.
2. **It is hash-bearing.** `srmech_tool_schema_to_json` emits bytes byte-identical to the Python
   `json.dumps(..., sort_keys=True, separators=(",", ":"))`, and `sha256(that) == tool_schema_sha256`
   (`srmech.h:5483-5493`). The prose is inside the attestation. Documentation is not usually inside an
   attestation.
3. **It is population-floored.** The coverage gates (§4) hold it at 100%, which is a contract, not a
   docs aspiration.

**A vocabulary correction this ADR makes explicitly.** `c/include/srmech.h:5489` calls `example` /
`smoke_test_hint` the **"documentation-hint fields"**, and `:5522` describes `explanation` as a
**"hint"**. That wording is the calculator framing of §1 written into the wire contract — a *hint* is
something a caller may ignore, and a *documentation* field is something that lives elsewhere by right.
This ADR states the opposite: **the field is self-information, and the wire contract carries it because
it is part of what srmech is.** The header comment is not corrected by this ADR (that is a source
change, and this rc is documentation-only save for the gate bump in §10); it is recorded here as the
next thing a reader will trip over.

---

## 4. Decision — one SSoT, three consumers; today it is three independent authorships

The explanation surface **is one SSoT with three consumers**:

| # | consumer | what it should express |
|---|---|---|
| 1 | **CLI switch help** | the affordance of a subcommand / switch, in the user's vocabulary |
| 2 | **tool schema / MCP** | the advertised index and the machine-readable contract |
| 3 | **WHAT / WHEN / SIBLINGS / example** | the self-information payload |

**Today these are three independent authorships, and that is the gap this ADR names.** Measured by AST
walk over `srmech/cli/*.py`, counting `help=` keyword arguments and classifying each value node:

| call site | count |
|---|---|
| `add_argument(help=…)` — switch help | **41** |
| `add_parser(help=…)` — subcommand help | **16** |
| **total across 6 CLI modules** | **57** |
| of which **plain string literals** (hand-authored) | **57** |
| of which **derived from any registry** | **0** |

Per module: `bus.py` 27 · `dsl.py` 12 · `mcp.py` 6 · `main.py` 5 · `status.py` 4 · `klass.py` 3.

**Not one of the 57 is derived.** And the only mention of `tool_schema` anywhere in `srmech/cli/` is a
docstring — `srmech/cli/mcp.py:7` — which says of the `.mcpb` bundle:

> The bundle's manifest version + tool list are DERIVED from `srmech.__version__` and the advertised
> `tool_schema` surface; **nothing is hand-authored.**

That sentence is true, and it is about the **MCP bundle's tool list**, not about the CLI's own
switches. The file asserting that nothing is hand-authored contains six hand-authored help strings.
The irony is not the finding; the finding is that **the SSoT this ADR names does not exist yet** —
there are three authorships and no source they share.

### 4.1 Coverage floors STAY

The 100% population floors on `explanation` and `example` are a standing requirement and this ADR
does not relax them. They are what keeps §2's population table at 556/556 rather than at the 2/525
shape ADR-0012 §6.1 names as *declared, not shipped*.

`tests/test_tool_docs_coverage_rc240.py` holds them as **two separate emptiness assertions** — one per
field, `assert not missing`, which is a 100% floor in substance (the string "100%" appears only in the
failure message, never as a numeric threshold):

| test | `def` at | assertion at | field |
|---|---|---|---|
| `test_every_srmech_tool_has_explanation` | `:52` | **`:55`** | `explanation` |
| `test_every_srmech_tool_has_example` | `:62` | **`:64`** | `example` |

Two scope facts belong with them, because a floor's *selection predicate* is half of what it
guarantees (ADR-0012 §4.3):

- **The floors select `owner == "srmech"`** (`:42-43`), so profile-owned tools are outside them. This is
  currently a distinction without a difference — all **556/556** entries have `owner == 'srmech'` — but
  it means the floor does not automatically extend to a plugin-contributed surface.
- **A third, non-100% floor sits alongside them:** `_MIN_EXECUTED_EXAMPLES = 90` (`:25`, asserted at
  `:93`) — a down-never ratchet requiring only ~90 ops to carry a *really executed* example rather than
  an honest signature snippet. §2.1 measures `worked` at **471**, far above that floor. The floor is
  not what is holding the population up.

---

## 5. Decision — the organs are distinct, separately addressable, and therefore separately SELECTABLE

Because §2.1's organs answer different questions, **a consumer must be able to ask for one without
taking all of them.** An autonomous or scripted host may legitimately want identification *without*
affordance — a tool picker rendering 556 rows wants `summary` alone; an agent that has already chosen
an op wants WHEN and SIBLINGS and not the index line; a bare-C host with 64 KiB of flash may want
identification only and no prose at all.

This is a decision about **shape**, not about mechanism: the organs are distinct, they are separately
addressable in principle, and any encoding chosen later (§9.1) must preserve that separability rather
than re-flatten it. §2.2 records that today the delimiter is not uniform enough to make the selection
mechanical, which is a constraint on the encoding decision, not a reason to defer the shape decision.

**Selectability is the weak form; §2.3's four readings is the strong form.** Selecting an organ
presupposes each organ is a separable *string*, and §2.3 measures why that presupposition fails: 98.5%
of entries carry content across two or more organs, and gcd's `lcm` is authored twice because the form
offers no way to share. **Under four readings of one addressed set, selection stops being extraction
and becomes traversal** — the same atom can participate in two readings without being written twice,
and no reading has to cut another's content to get what it needs. This section states the requirement
a consumer has today; §2.3 states the shape that satisfies it without forcing duplication.

---

## 6. The measured reachability deficit — the authored half is at 100%, the derived half is at 0%

That one line is the diagnosis. Every number below is a measurement on this branch, with its basis
named.

### 6.1 There is no read path — only an ingress and an egress

Grepped across the whole `srmech/` package for any reference to `.explanation` / `.example` on a
`ToolEntry`. **Two touch points, and neither is an accessor:**

| touch point | file:line | what it does |
|---|---|---|
| **ingress** | `srmech/introspect/tool_schema.py:674-698` (`_apply_docs`) | merges the curated docs onto the entry **at registration** |
| **egress** | `srmech/introspect/tool_schema.py:492-495` (`to_jsonable`) | copies both fields into the JSON blob **on serialisation** |

**Nothing in between ever reads them.** No search, no filter, no render, no selection, no accessor. The
payload goes in at registration and out at serialisation and is never *consulted*. `srmech/introspect/
__init__.py` — the module that owns `describe()` — contains **zero** references to either field.

*(The `example` hit at `introspect/carrier_schema.py:945` is the carrier-construction example, a
different field on a different registry; it is not a consumer of this surface.)*

### 6.2 `resolve` matches whole dotted segments only

`ToolSchema.resolve_all` (`tool_schema.py:586-597`) is, in full:

```python
suffix = "." + name
return tuple(t for t in self.tools if t.name == name or t.name.endswith(suffix))
```

A name resolves iff it is a **whole trailing dotted segment**. Two consequences, measured:

**(a) Compound-leaf sub-tokens.** *Basis: leaf = last dotted segment; a leaf is compound iff it
contains `_`; sub-tokens are its `_`-split parts.* 487 of 556 leaves are compound, yielding **545
distinct sub-tokens**. Of those, **509 (93.39%) return `None` from `resolve()` AND `()` from
`resolve_all()`** — no match by either route. Only 35 resolve, and they do so by coincidence (they
happen to also be whole op names: `bind`, `bundle`, `commutator`, `cos`, `describe`, `eigvals`, …).

**(b) Prose-only tokens.** *Basis: word-tokens drawn from prose, lowercased, that are not a whole
dotted segment of any registered name.* **100.00% are unresolvable — under every basis tested:**

| basis | prose-only tokens | unresolvable |
|---|---|---|
| `explanation` only, `[A-Za-z_]\w{2,}` | 6,286 | **6,286 (100.00%)** |
| `explanation` only, alpha-only len ≥ 4 | 5,125 | **5,125 (100.00%)** |
| `explanation` + `example`, alpha-only len ≥ 4 | 6,455 | **6,455 (100.00%)** |
| `explanation` + `example`, `[A-Za-z_]\w{2,}` | 8,859 | **8,859 (100.00%)** |
| all three fields, `[A-Za-z_]\w{2,}` | 9,796 | **9,796 (100.00%)** |

**This is `[[feedback_a_zero_census_is_basis_free_a_nonzero_one_is_gauge]]` seen from its useful
side.** The *count* is gauge — it moves from 5,125 to 9,796 with the tokeniser, and no single figure
should be quoted without its basis. The *complement is zero under every basis*, and a zero is
basis-free. So the honest claim is not "6,286 tokens are unreachable" but: **no prose token is
reachable, and that holds however you count.**

The worked exhibit: **`resolve('winding')` returns `None` while 26 of 556 entries mention winding.**

### 6.3 MCP is byte-identical with and without the prose

*Basis: build the advertised tool definitions; rewrite `explanation` and `example` on all 556 registry
entries; rebuild; compare `json.dumps(defs, sort_keys=True)` bytes and sha256.*

| | defs | bytes | sha256 (first 16) |
|---|---|---|---|
| with the full prose | 556 | **810,082** | `2d2fc9049040f6b4` |
| with every `explanation`/`example` replaced by `"TAMPERED"` | 556 | **810,082** | `2d2fc9049040f6b4` |

**Byte-identical.** The MCP `description` is assembled at `srmech/mcp/_tools.py:395-402` from
`entry.summary` + `returns` + `[srmech category: …; owner: …]` and nothing else; `_tools.py` contains
**zero** references to either prose field. 1.68 MB of authored self-information reaches an MCP client
as exactly zero bytes.

### 6.4 `describe()` — the root index names almost nothing

*Basis: `json.dumps(srmech.describe())`.*

- **21,293 chars** for 556 ops.
- It names **10 of 556 ops (1.80%)** — all ten inside `lanes`, all `srmech.biology.*` or
  `srmech.physics.qm.quaternion.*`. **`'srmech.math.cyclic.gcd' in json.dumps(describe())` is
  `False`.**
- `"explanation"` and `"example"` each occur **0** times.
- `tools.by_category` maps **76 categories to integer counts** (summing to 556) — **counts, not
  members**.

⚠️ **A correction to the brief this ADR was written from, recorded rather than quietly fixed.** The
brief stated `describe()` "contains ZERO op names". It contains **ten**. The specific probe
(`gcd` absent) holds, and the structural claim (`by_category` is counts-not-members) holds exactly —
but "zero" was an overstatement, and ADR-0012 §2 had already measured the true shape as *"9 of 525
ops are named anywhere in the payload, all inside `lanes.ops`"*. Ten of 556 at rc409 is the same
finding one op larger. A claim of **0** and a claim of **10** are different kinds of claim: the first
is basis-free, the second is a census — and asserting the basis-free version when the true value is
nonzero is the precise error §6.2 exists to avoid.

### 6.5 The staff and the notes — the sharpest structural claim in this ADR

The user's framing, which turns out to be exactly measurable:

> A blank sheet of lines and spaces is the **addressing**. Leave the notes and remove the lines, and
> you have retained **relationship without addressing**.

| surface | what it is | measured |
|---|---|---|
| `describe()` | **lines without notes** | 76 category positions, every value an `int`, **zero members named** |
| `get_tool_schema()` | **notes without lines** | a flat `tuple` of 556 entries; **every row equidistant** |

**Neither is a staff with notes on it.** And the reason is not that the information is missing — every
entry carries `category`, so the membership relation *exists in the data*. It is that **no accessor
exposes it**:

- `ToolSchema` has **no `by_category` accessor** (its full public surface is `by_owner`, `lookup`,
  `resolve`, `resolve_all`, `srmech_version`, `to_json`, `to_jsonable`, `tool_schema_version`,
  `tools`).
- The one grouping accessor that *does* exist, `by_owner`, is **informationally empty**: all 556
  entries have `owner == 'srmech'`, so it partitions 556 rows into **one** bucket.

So the single partition with 76 positions publishes only counts, and the single membership accessor
that exists yields one bucket of everything. The staff and the notes are both present in the data and
joined by nothing.

**An earlier claim that "the ToC is built" was wrong, and the mechanism of the error is worth
recording.** It was believed because `describe()` *self-describes* as a table of contents —
`srmech/introspect/__init__.py:735-736`, verbatim:

> It is a ROOT / **INDEX**: it surfaces the shape, not the detail.

**The docstring was taken for the behaviour.** The sentence is not false — `describe()` is exactly
what it says, and ADR-0012 surface-2 correctly records that a domain is covered there *iff counted,
never iff named*. The error was reading a truthful self-description of an index-of-shapes as evidence
of an index-of-members. This is `[[feedback_false_green_comments_and_dead_instrumentation_seams]]`
in its documentation form: **prose that accurately describes a limitation still reads, to a hurried
reader, as a claim that the job is done.**

---

## 7. Duplication as shipped — and parity today is by COMPILATION

Three files persist this prose.

| file | bytes |
|---|---|
| `srmech/introspect/_tool_docs_curated.py` | **1,751,123** |
| `srmech/introspect/_tool_docs.py` | **1,729,524** |
| `c/src/srmech_tool_registry.c` | **2,664,100** |

The two Python files are **not** byte-identical as files (they differ by 21,599 B of header comment),
but **their payloads are**:

| | `TOOL_DOCS` | `CURATED` |
|---|---|---|
| entries | **556** | **556** |
| keys present in one but not the other | **0** | **0** |
| overlapping payloads that DIFFER | **0** | — |
| payload chars | **1,739,479** | **1,739,479** |

**All 556 keys, all 556 payloads, character-identical.** The two-layer design these files document —
`_tool_docs.py` a docstring-seeded *floor*, `_tool_docs_curated.py` a hand-curated *overlay* merged
over it — has collapsed: the overlay now covers the entire registry, so the floor it overlays is
fully shadowed. **3,480,647 B across the two Python files, both inside the wheel, carrying one
1,739,479-char payload twice.**

The C file is the third copy. `c/tools/gen_tool_registry.py` bakes the prose into the generated table
field by field — `summary` at `:265`, `example` at `:276`, `smoke_test_hint` at `:277`, **`explanation`
at `:278`**.

**The registry's share of the C tree — and why the basis must be stated.** `srmech_tool_registry.c` is
the largest C file in the tree by **5.4×** (next: `srmech_genome.c`, 491,607 B). Its share:

| basis | share |
|---|---|
| **bytes** of `c/src/*.c` (137 files, headers and `test/` excluded) | **36.21%** |
| **lines** of `c/src/*.c` (13,368 of 113,668) | **11.76%** |
| bytes of all `.c` + all `.h` under `c/` (the most conservative) | 30.18% |

⚠️ **The 3× byte-vs-line divergence IS the finding, and quoting only the byte figure would flatter the
claim.** The registry is a table of enormous one-line string literals, so bytes and lines measure
different things about it: by *volume of shipped text* it is a third of the C tree; by *lines of C* it
is an eighth. Both are true. This ADR's argument needs neither to be large — §7's point is that the
prose is compiled in at all — so the honest statement is the one with its basis attached, and the
conservative figure is 30.18%.

*(`tests/test_jpl_audit.py:63-68` lists `srmech_tool_registry.c` as the sole entry in
`GENERATED_DATA_FILES`, with the comment "whose summary strings are the (English) ToolEntry
summaries" — the parenthetical is §9.4's point made in passing by the audit ratchet.)*

**Parity today is by compilation, and that is the fact with consequences.** The prose is not read from
a data file at runtime; it is a `const` table in a translation unit. Two things follow, and both are
recorded as *observations*, not as decisions this ADR makes:

1. A change to one WHEN clause is a **codegen run plus a C rebuild plus an ABI-adjacent artifact
   change**, not an edit.
2. A **language variant is a rebuild**, not a configuration change (§9.4).

---

## 8. Consequences

- **The surface has a name and a definition.** "The explanation surface" denotes the `explanation` +
  `example` payload on `ToolEntry` / `srmech_tool_entry_t`, as distinct from `summary`. A question
  about WHAT/WHEN/SIBLINGS/example resolves here; the introspect layer as a whole still resolves to
  ADR-0012.
- **It is self-information, governed by ADR-0012's standard.** A landing that ships an op with a
  signature-echo explanation is failing C4, and now also failing a named surface rather than an
  unnamed field.
- **"Three consumers, one SSoT" is the target shape; three independent authorships is the measured
  present.** 57 hand-authored CLI help strings, 0 derived, is the baseline any future unification is
  measured against.
- **The organs are separately selectable by design** — and §2.2 records that the current delimiter is
  not uniform enough to make that mechanical, which is a real constraint on the encoding decision.
- **The stated goal is four READINGS of one addressed set (§2.3), and the four-field form is recorded
  as where we are rather than as what it is.** A future rc proposing to keep four authored strings is
  proposing against a stated goal and should say so. The two measured arguments for the change are
  that an atom may belong to more than one reading (gcd's `lcm`, authored twice) and that a reading
  may need content another organ holds (gcd's `sub-period`, dropped from WHAT).
- **The failure mode is CONFIDENT WRONG ANSWERS, not blanks (§1.2), so the bar is temporal (§1.4).**
  A future measurement reporting that the surface "covers" a capability has answered the wrong
  question; the question is whether its answer arrives before the trained reach fires.
- **Any decomposition must derive each reading independently, never back-solve one from the others**
  (§2.3, on the tree's own `cwf_consistency_mod2` rule). And **no decomposition should be attempted
  before an instrument exists that can detect WHEN-vocabulary loss** — that loss is silent, and
  nothing currently goes red on it.
- **Reachability is the gap, not authoring.** The authored half is at 100% on all three fields; the
  derived half — search, selection, addressing — is at 0%. No future rc should re-file "the prose is
  thin" as the problem; measured, the prose is 1.68 MB and unreachable.
- **A number quoted from §6.2 must carry its basis.** The unresolvable *fraction* is 100% and
  basis-free; the *count* ranges 5,125–9,796 and is gauge.
- **`describe()` self-describes accurately and must not be cited as a table of contents.** §6.4/§6.5.
- **Duplication is now measured rather than suspected**, and the collapse of the floor/overlay split
  (§7) is recorded so a future reader does not assume `CURATED` is still a small curated subset.

---

## 9. Scope honesty — what this ADR does NOT decide

This ADR is **pre-scoped on purpose**. It names a surface and measures it. Four questions are
deliberately left open, and each is left open for a stated reason rather than by omission.

### 9.1 The ENCODING is open

**This ADR does not decide how the explanation surface should be stored.** Not TOML, not a baked blob,
not a sidecar data file, not a new field layout, not a delimiter contract for §2.2's organs. Arguments
exist in several directions — ADR-0004 makes config-driven the preferred way to add behaviour, while
ADR-0012 §3.4 (C6) measures that config-driven behaviour is *invisible* to introspect by construction,
so "move it to TOML" trades one reachability problem for another. **Nothing here should be read as
prejudging that trade.**

⚠️ **§2.3's four-readings goal does NOT re-open this question, and must not be read as deciding it.**
"Four readings of one addressed set" is a statement about **shape** — what the content must be able to
do — and it is deliberately silent on what an atom is made of, where atoms live, how they are
serialised, and how they cross the C wire. Several encodings could satisfy it and several could not;
choosing among them is still open, still out of scope here, and still an ADR-0004-adjacent question.
The goal **constrains** the encoding decision (§2.3(b): the atoms must be finer than any reading;
§2.3(d): one encoding, not two) without **making** it.

### 9.2 The genome is explicitly NOT the store — and the reason is principled

The genome is the obvious candidate: it is srmech's own substrate-native storage layer, and storing
srmech's self-description in it has an appealing symmetry.

**This ADR rules it out for now, and not on grounds of readiness.** The genome is known to be
**biologically incorrect** in specific, recorded ways — shortcuts of the *different-cascade-same-result*
kind:

- `#T1005` — a finite group used where biology has the universal cover.
- `#T1033` — `quad_turn` is memoryless where biology is not.

Both produce the right output by a cascade that is not the one biology runs, which is precisely what
`[[feedback_simulate_with_biologys_actual_cascade_not_modified]]` names as the failure mode:
**cascade IDENTITY, not output-match.**

**Storing the self-description in a known-wrong cascade would bake an output-match shortcut into the
one layer whose entire job is to describe what srmech IS.** The layer that answers "what is this
thing?" cannot be the layer that is quietly answering it by a different route than the one it claims.
That is a *principled* exclusion, and it is recorded as such rather than as "not yet" — if the two
defects above are closed, the exclusion should be revisited on its merits, but it should be revisited
as a decision, not assumed lapsed.

### 9.3 The address space is UNSOLVED

§6.5 says `describe()` is lines-without-notes and `get_tool_schema()` is notes-without-lines. It does
**not** say what the staff should be. **A real table of contents is a staff, not a bucket histogram** —
and what the address space *should* be is live research, not a design this ADR is entitled to settle.
The open threads include the Hurwitz-rung structure, lower-rung-addressable-from-higher, and the
2-cochain `quad_turn` "addressing IS the knowledge by choosing frames" line from PR #687.

Adding a `by_category` accessor would be a cheap, real improvement and would **not** be the answer to
this question; it would give 76 buckets a membership list. Recording the difference between *a fix* and
*the answer* is the point of this subsection.

### 9.4 Localization is a CONSEQUENCE, not a decision

**srmech has no human-language localization surface.** Verified over `docs/srmech/python/` by direct
marker census, and the nulls are unambiguous:

| marker | hits |
|---|---|
| `gettext` · `ngettext` · the `_("` marker | **0** |
| `i18n` · `l10n` · `babel` · `setlocale` · `LC_MESSAGES` | **0** |
| `.po` / `.mo` / `.pot` files · `locale/` or `i18n/` directories | **0** |

The 18 `locale` hits are **the opposite of a localization surface** — they are explicit scope
*refusals*, e.g. `srmech/math/text.py:421` *"no case change, no locale tailoring, no
NFKD/compatibility folding"*.

⚠️ **A correction to the brief this ADR was written from.** The brief asserted that the only `translat*`
hits in the tree are *biological* (DNA→protein) and *geometric*. That is **wrong**, and the error is
worth recording because it is the §6.2 gauge mistake in miniature — a token census reported without its
classification. Measured: **278 occurrences across `docs/srmech/python/` + `docs/srmech/c/`**, in at
least **eight** distinct senses. The two largest are neither of the two named:

| sense | occurrences |
|---|---|
| **geometric / group-theoretic** (`sp4_translation`, `left_translations`, half-period translation) | ~55 |
| **C "translation unit"** — *not in the brief's taxonomy* | 16 |
| **biological** ("translation table", the genetic code) | 12 |
| error-code translation (C status → Python exception) | ~11 |
| the framework's own "coherency-translation-layer" (genome Tier-1↔Tier-2) | 10 |
| the framework's own "language-translation operators" (the B/H/N metaphor) | 5 + adjacent |
| "kernel translation layer" (fold↔spectrum) | 4 + adjacent |
| newline translation (text-mode I/O) | 5 |
| **human-language i18n** | **0** |

**The conclusion survives the correction and is in fact strengthened**: the count that matters is the
last row, and it is a zero — which per §6.2 is the one kind of census that is basis-free. Combined with
§7 — compiled-in prose — a language variant is therefore a **rebuild**, not a configuration change.

**This ADR does not decide the fix**, does not propose an i18n mechanism, and does not assert that a
language variant is a requirement. It records the entailment, because "the explanation surface is
compiled into a `const` C table" and "srmech could ship a Spanish-language self-description" are
statements that interact, and the interaction should be visible before an encoding is chosen (§9.1)
rather than discovered afterwards.

---

## 10. Naming — two names this surface must NOT be given

Both were considered and both are rejected on measured grounds.

### 10.1 It is not a `DSL`

**The `DSL` token is already forked in this tree, three ways, and must not absorb a fourth.** Measured:
`grep -rnw DSL` over the worktree returns **500 matching lines across 60+ files**, denoting at least
three distinct objects:

| sense | what it denotes | anchor |
|---|---|---|
| 1 | the **operator-chain / cascade** language — `chain()` + `[cascade]`/`[chain]` TOML | `srmech/dsl/__init__.py:1` (*"srmech.dsl — cascade DSL"*), `c/src/srmech_dsl_chain_run.c` |
| 2 | the **argument-reference** grammar `@row.col` / `@step[0].output`, nested *inside* sense 1 | ADR-0008 §3.7 |
| 3 | the **`[class]` object-model** descriptors — "DSL-declared class" | ADR-0003 `:54`, `srmech.h:6070`, `:6076` |

**ADR-0008 alone applies "DSL" to two different languages in one document**, confirmed by line: sense 1
at `:1` (*"Operator-chain DSL — schema specification"*) and `:18`; sense 2 at `:28`, `:100`, `:199`
(*"Argument-reference DSL"*), `:496`.

And the acronym is **never expanded anywhere in the monorepo**: `grep -rniE "domain[-_ ]?specific[-_
]?language"` returns **0**. All 48 `domain-specific` hits are the bare adjective ("domain-specific
extension", "domain-specific coprime basis") — never once followed by "language". **A token used 500
times, denoting three things, and defined nowhere.**

`DSL` stays with the **execution** chain layer. The explanation surface is not a language, has no
grammar and executes nothing; calling it a DSL would name a *description* layer with a term that
already denotes an *execution* layer in the same package — and would make a three-way fork a four-way
one.

### 10.2 It is not an `affordance`

**`affordance` was considered and rejected.** In this tree the word already carries a specific
technical sense — **a host-language capability that cannot cross a wire** — and it is the single
largest of its ~14 load-bearing uses. Verbatim, `c/include/srmech.h:7247-7248`:

> The §101 `progress=` gate is a **Python-only affordance** (a splice has no meaningful partial;
> **a callable cannot cross the C wire**).

with the near-twin at `srmech.h:7193` — *"predicate stays a **Python-layer** affordance (a callable
cannot cross the C wire)"* — and the JSON-RPC variant at `introspect/tool_schema.py:3750`, *"an
IN-PROCESS Python affordance (a callable cannot cross JSON-RPC)"*.

**The explanation surface does cross the C wire** (§3: `srmech_tool_entry_t.explanation`,
`srmech.h:5522`; the gcd WHEN clause is present in `srmech_tool_registry.c`). Naming it `affordance`
would assert the exact opposite of the measured fact, using the tree's own most established sense of
the word.

The word survives *inside* the surface, in its ordinary sense: §2.1 defines `explanation.WHEN` as **the
affordance in the reader's domain vocabulary**. That is the organ's job description, not the layer's
name.

---

## 11. Instrumentation status — which clauses can return otherwise, and which cannot

Per ADR-0012 §3.2, a clause with no instrument is a preference. Stating which is which is the reason
this ADR is 🟢 Implementing and not ✅ Accepted.

| § | clause | instrument | status |
|---|---|---|---|
| §2 | the surface is named and defined | — | **definitional**; nothing to instrument |
| §4.1 | coverage floors stay (100% `explanation` + `example`) | `tests/test_tool_docs_coverage_rc240.py::test_every_srmech_tool_has_explanation` (§12) | **GATED** — inherited, strict floors |
| §3 | the payload crosses the C wire and is hash-bearing | `tests/test_tool_registry_c_rc184.py::test_hash_ratchet_matches_mcpb_tool_schema_sha256` | **GATED** — inherited |
| §4 | one SSoT, three consumers | **none** | **UNGATED — and currently FALSE** (57 hand-authored, 0 derived). Stated as a target, not as a satisfied property |
| §5 | organs separately selectable | **none** | **UNGATED**; §2.2 shows the delimiter is not uniform enough to make selection mechanical |
| §6.1 | no read path exists | **none** | **UNGATED** — a grep today, not a gate |
| §6.3 | MCP payload is prose-independent | **none** | **UNGATED** — reproducible in three lines (§12), never asserted by CI |
| §6.5 | the address space is unsolved | — | **not instrumentable**; §9.3 declines to specify it |
| §1.4 | the answer arrives before the habit fires | **none** | **UNGATED — and no instrument is even proposed.** Measuring it needs an agent-in-the-loop trial, not a pytest assertion. Stated as the standard, explicitly not as a passing property |
| §2.3 | four readings of one addressed set | **none** | **GOAL, not a clause.** Adds no instrument and claims nothing. The four-field form remains what ships |
| §2.3 | a migration must not silently lose WHEN vocabulary | **none** | **UNGATED — and this is the dangerous one.** The failure is silent by construction; §2.3 records it as a RISK and makes building the detector a precondition of attempting the migration |

**Counted exactly, 11 rows: 2 gated · 6 ungated (one of them a standard) · 1 goal · 1 definitional · 1 not instrumentable.** And **both gated rows are inherited
from earlier rcs — this ADR builds no new instrument.** Of the six ungated, one (§4) is not merely
unenforced but **measurably false today**, and is stated as a target rather than as a property. An
honest reading of the table is: *the surface is named and measured; almost nothing about it is yet
enforced.* That is what 🟢 Implementing means, and it is why acceptance is not claimed.

**The one gate this rc does touch.** `tests/test_adr_status_coherence_rc409.py` pinned
`_EXPECTED_ADR_COUNT = 12` so that a deleted or unparseable ADR fails loudly rather than silently
shrinking the population every other assertion iterates over. Adding this ADR makes it **13**, so the
constant is bumped in the same commit — **the gate is doing exactly its job by forcing the edit**, and
that is the whole reason it was written. The rc409 legend already defines `🟢 Implementing`, so no
legend change is required. §12 records the run and the injection proof.

---

## 12. Verification basis — commands, and one concern filed separately

**Artifact under test.** Every measurement in this ADR was taken with a guard asserting
`srmech.__file__` resolves inside this worktree, after discovering that a bare `import srmech` from
outside the source tree resolves an **empty namespace package** with no `__version__` — the failure
mode `[[feedback_verify_the_artifact_under_test_is_the_one_you_think]]` names. Measured against
**v0.9.0rc409** at `94ed5e914`, `HAS_NATIVE=False`.

**Path note (ADR-0010).** `tool_schema.py`, `_tool_docs.py`, `_tool_docs_curated.py` and
`carrier_schema.py` now live under **`srmech/introspect/`**, not `srmech/amsc/` as ADR-0012 cites them.
Every path in this ADR is the post-declustering one.

**Principal commands.**

```python
# population + char census (N = 556)
rows = list(get_tool_schema().tools)
sum(len(r.summary) for r in rows)                        # 381,358
sum(len(r.explanation) for r in rows)                    # 743,186
sum(len(json.dumps(r.example, sort_keys=True)) for r in rows)   # 937,042

# MCP prose-independence (§6.3) — rebuild after rewriting all 556 entries
json.dumps(list(tool_entries_to_mcp_defs()), sort_keys=True)    # 810,082 B, both ways

# describe() (§6.4)
len(json.dumps(srmech.describe()))                       # 21,293
'srmech.math.cyclic.gcd' in json.dumps(srmech.describe())       # False
```

CLI help was counted by **AST walk** (not grep) over `srmech/cli/*.py`, classifying each `help=`
keyword by call site and by whether its value node is a string literal — a grep cannot distinguish
`add_argument` from `add_parser`, nor a literal from an f-string. (A plain
`grep -c "help=" srmech/cli/*.py` returns the same 57 here, but it cannot produce the 41/16 split or
the literal-vs-derived split, which are the two facts §4 actually rests on.)

**The gate run, and its injection proof.** `tests/test_adr_status_coherence_rc409.py` reports
**`4 passed`** with this ADR's file header and README row in place. Proven non-vacuous rather than
assumed: flipping the README row alone to `⏳ Draft` turns it **red**, naming the defect precisely —

```
AssertionError: 1 ADR(s) disagree between their own header and the README index:
    ADR-0013: file header U+1F7E2 != README index row U+23F3
```

— after which the row was restored and the gate returns `4 passed`. `tests/
test_ref_notation_emitted_rc348.py` also passes (`18 passed`); the only bare `#NNN` in this ADR is
**PR #687**, a real GitHub object, and every local task ID is written `#T…`.

**Corrections this ADR makes to its own brief**, recorded rather than silently applied, because a
draft that survives contact and says where it was wrong is worth more than one that reads clean:

| claim as briefed | measured |
|---|---|
| `describe()` "contains ZERO op names" | **10 of 556**, all inside `lanes` (§6.4) |
| the two `_tool_docs` files are "byte-identical" | **files differ by 21,599 B**; their *payloads* are identical (§7) |
| "39 argparse `help=` strings" | **57** (41 `add_argument` + 16 `add_parser`), all literals (§4) |
| "6901 of 6901 prose-only tokens" | basis-dependent, **5,125–9,796**; the 100% fraction is basis-free (§6.2) |
| coverage floors at `:52` / `:62` | those are the `def` lines; assertions at **`:55`** / **`:64`** (§4.1) |
| the only `translat*` hits are biological + geometric | **eight senses**; the 2nd largest is C "translation unit" (§9.4) |
| `srmech/amsc/tool_schema.py` | moved by ADR-0010 to **`srmech/introspect/tool_schema.py`** |
| `python/tools/gen_tool_registry.py` | the file is at **`c/tools/gen_tool_registry.py`** (line 278 correct) |
| `527/556 = 94%` carry both organ markers | **confirmed** — on the bare-token basis, 94.78% (§2.1) |
| "556 ops × ~2,850 chars" (§2.3 migration scope) | **3,022** mean on the `json.dumps` basis; 2,938 concatenated-values; 1,337 `explanation` alone |

Also verified for §1.2, each by direct lookup: `srmech.math.rational.log` and
`…rational.log1p_series_truncate` both resolve; `QMat.rank(self, *, method="auto")` exists at
`srmech/math/qmat.py:447` while `resolve_all('rank')` returns `()`; `Q` is defined at
`srmech/math/q.py:234` (so `srmech.math.q.Q`, not `…rational.Q`); `tool_schema_view` exists at
`introspect/tool_schema.py:809` and `all_entries` exists nowhere.

Everything else in the brief verified exactly, including the three file sizes, the five `example`
sub-key populations, the three char censuses, `509/545`, `resolve('winding')` with 26 mentions,
`gear` at 0/556 summaries, and the 810,082-byte MCP identity.

### 12.1 A live tamper concern — filed separately, NOT folded in

Demonstrated incidentally while measuring §6.3, and recorded here **only as a cross-reference**:

- **`srmech.introspect.tool_schema._REGISTRY` (`tool_schema.py:662`) is a plain module-level `dict`
  with no write guard** — no `MappingProxyType`, no lock, no freeze. It is not in `__all__`, but it is
  imported by name across modules (`introspect/carrier_schema.py:981`,
  `introspect/responsion_schema.py:406`). A direct `_REGISTRY[name] = tampered` **bypasses
  `register_tool` entirely**, and therefore bypasses its `ToolSchemaConflictError` raise (`:538-556`).
- **`ToolEntry` is a frozen dataclass — but freezing the record is not integrity of the container.**
  Rewriting `explanation` and `example` on **all 556 entries** required only `dataclasses.replace` plus
  dict assignment, and **`owner` still read `'srmech'`** on every rewritten row. This was executed
  while measuring §6.3.
- **The profile loader imports plugin-supplied modules at ENUMERATION time.** `profile_loader.py:361`
  calls `ep.load()` — which imports the third-party module — reached from `_enumerate_profiles()`
  (`:433`, `:464`), which is reached from **`list_profiles()` (`:889`, `:893`)**. So *merely listing
  what profiles exist* executes every installed plugin's module-level code, **before `srmech.profile()`
  is ever called**. `srmech/__init__.py:74` documents the eagerness as deliberate (ADR-0001 §5.5).
- **The attestation then certifies the result.** `mcp/_mcpb.py:80-91` hashes
  `json.dumps(get_tool_schema().to_jsonable(), sort_keys=True, separators=(",", ":"))` — the whole
  registry-derived schema *at the moment of emission* — and `:240` embeds it as
  `"tool_schema_sha256"` in the manifest's `attestation` block. A rewrite landing before `emit-mcpb`
  produces a **valid, internally consistent attestation over tampered content** — ADR-0012 §7.4's
  "worst failure shape available, because nothing in the artifact reveals it".

**This is a separate concern with a separate shape (supply-chain / integrity), and this ADR
deliberately does not fold it in.** It is noted because the explanation surface is the payload such a
rewrite would target, and because §3 establishes that this payload is *inside the attestation*.

---

## 13. Sources

`srmech/introspect/tool_schema.py` — the SSoT (`_REGISTRY` at `:550`; `_apply_docs` ingress at
`:562-586`; `to_jsonable` egress at `:390-393`; `resolve_all` at `:474-485`) ·
`srmech/introspect/__init__.py:735-736` (the ROOT/INDEX self-description §6.5 reads against) ·
`srmech/introspect/_tool_docs.py` + `_tool_docs_curated.py` (the two identical payloads, §7) ·
`srmech/mcp/_tools.py:395-402` (the `description` assembly that omits the prose) ·
`srmech/cli/*.py` (the 57 hand-authored help strings; `cli/mcp.py:7` for the "nothing is
hand-authored" docstring) ·
`c/include/srmech.h:5509-5584` (`srmech_tool_entry_t`; the "documentation-hint fields" wording at
`:5489`; `explanation` at `:5522`; the byte-identity/hash contract at `:5483-5493`) ·
`c/tools/gen_tool_registry.py:265,:276,:277,:278` (where `summary` / `example` / `smoke_test_hint` /
`explanation` are baked into C) ·
`c/src/srmech_tool_registry.c` (the third copy) ·
`tests/test_tool_docs_coverage_rc240.py:55,:64` (the two 100% floors §4.1 preserves; `:42-43` the
`owner == "srmech"` selection; `:25`/`:93` the separate `_MIN_EXECUTED_EXAMPLES = 90` ratchet) ·
`tests/test_jpl_audit.py:63-68` (`GENERATED_DATA_FILES`, and its "(English)" parenthetical) ·
`srmech/profile_loader.py:361,:433,:464,:889,:893` + `srmech/mcp/_mcpb.py:80-91,:240` (§12.1 only) ·
`tests/test_adr_status_coherence_rc409.py` (the gate §11 bumps) ·
**ADR-0012** §9 (the warrant, quoted verbatim in §1.2), §2 (the eight surfaces; surface 2's
counted-not-named contract), §3.2 (a clause without an instrument is a preference), §3.4/C6 (the
config-visibility tension §9.1 must not prejudge), §6.1 (declared-vs-shipped populations), §7.1 (the C
registry as the last-resort introspect surface) ·
**ADR-0009** §4–§5 (parity; the exemption rule) · **ADR-0004** (config-driven surface) ·
**ADR-0010** (the `amsc` → `introspect` move every path here reflects) ·
`[[project_introspect_surface_is_the_api_contract_not_documentation]]` ·
`[[project_srmech_package_is_substrate_self_recognition_apparatus]]` ·
`[[feedback_simulate_with_biologys_actual_cascade_not_modified]]` (the §9.2 exclusion) ·
`[[feedback_a_zero_census_is_basis_free_a_nonzero_one_is_gauge]]` (§6.2) ·
`[[feedback_false_green_comments_and_dead_instrumentation_seams]]` (§6.5) ·
`[[feedback_an_instrument_that_cannot_return_otherwise_is_not_a_measurement]]` (§11) ·
`[[feedback_verify_the_artifact_under_test_is_the_one_you_think]]` (§12) ·
`[[user_stance_resonate_dont_brute_force_asymmetric_resonator]]` (§1's calculator framing)

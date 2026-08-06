# ADR-0013: The explanation surface — srmech's self-information layer

**Status:** 🟢 **Implementing** — the fifth lifecycle state, formalised by rc409. Direction accepted;
the surface is **named** and its shape is **measured**; its **encoding is deliberately open**. This is
a *pre-scoped* decision: §11 states which clauses have instruments today and which do not, and the ADR
does **not** claim acceptance for the uninstrumented ones. That is precisely why it ships 🟢 rather
than ✅ — per ADR-0012 §3.2, *a clause without an instrument that can return otherwise is not a
clause, it is a preference*, and a preference labelled as such is honest where one counted as coverage
is not.
**Date:** 2026-08-06.
**Authors:** Steven Kirkland + Claude Opus 5.
**Supersedes:** none.
**Superseded-by:** none.
**Amends:** **none.** This ADR **extends ADR-0012, it does not amend it** — nothing in 0012 is revised,
narrowed or contradicted. It occupies a gap 0012 explicitly left open; see §1.2 for the warrant, quoted
verbatim.
**Relates-to:** **ADR-0012** (introspect IS the API contract — this ADR names one of the open gaps that
ADR defines the standard for; C1–C6 are not restated here) · **ADR-0009** (multi-implementation parity
— the explanation surface is compiled into the C registry, so it is parity-bearing, not a Python-side
docs concern; §7) · **ADR-0004** (config-driven surface — the encoding question §9.1 leaves open is
partly an ADR-0004 question) · **ADR-0010** (namespace declustering — `tool_schema` and its two
generated peers now live under `srmech/introspect/`, not `srmech/amsc/`; every path in this ADR is
post-declustering) · **ADR-0007** §2.3 (the release ripple these three files ride).
**Motivated by:** eight retrieval failures in a single agent session working ON this codebase, every
one over capability that had already shipped (§1.1).

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

### 1.1 The demonstration — and precisely which half of it is re-derivable

An LLM agent working on this codebase recorded **eight retrieval failures in one session**, every one
over capability that had **already shipped**. Not gaps: authored, tested, wheel-resident capability
that the agent could not find and therefore re-derived or declared missing.

*(The count of eight is reported from the originating session and is not re-derivable here — it is a
property of that transcript, not of the tree. The exhibit below IS re-derived, and it is the sharpest
of the eight.)*

**The sharpest instance.** `srmech.math.cyclic.gcd` carries a WHEN clause naming its affordance in the
reader's own domain vocabulary — verbatim from the shipped entry:

> WHEN — reach for it any time two periods, tooth counts or moduli must be reduced to their common
> sub-period: **gear-train ratio reduction, dial realignment**, reducing a `(num, den)` pair before it
> enters a Class-N chain.

That sentence is exactly what an Antikythera-side reader needs, and it ships. Measured on this branch:

| probe | in `summary` | in `explanation` | in `example` | entries touched | `resolve()` |
|---|---|---|---|---|---|
| `gear` | **0 / 556** | 13 | 27 | 36 | `None` |
| `winding` | 12 | 22 | — | **26** | `None` |
| `chirality` | 31 | 49 | — | 65 | `None` |
| `eigen` | 48 | 76 | — | 107 | `None` |

**`gear` appears 0 times across all 556 summaries** — the advertised index — while the domain
vocabulary was authored 36 entries deep in the unadvertised half. The word was written down and
structurally unreachable. That is not an authoring failure; it is an addressing failure, and it is the
subject of this ADR.

### 1.2 The warrant — ADR-0012 left this gap open on purpose

ADR-0012 is titled *"The introspect surface IS the API contract — autonomous composition, **not
documentation**"*. Its §9 states, verbatim:

> **It does not claim the introspect layer is complete.** It defines the standard the open gaps are
> measured against — the same posture ADR-0009 §8 takes toward parity.

**The explanation surface is exactly such a gap.** ADR-0012 names the *standard* (autonomous
composition; INCOMPLETE IS AS BAD AS FALSE) and enumerates eight surfaces over one SSoT. It does not
name the `explanation` + `example` payload as a surface in its own right, and its surface-1 row treats
those two fields as *fields the SSoT carries* rather than as a layer with its own consumers, its own
organs and its own addressing problem. This ADR names it, without revising a word of 0012.

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

### 2.1 The organ decomposition — this is the load-bearing structure

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

---

## 3. Decision — this is SELF-INFORMATION, not documentation

**The explanation surface is in scope for introspect and governed by ADR-0012's standard.** It is not
a docs backlog, not a nice-to-have, and not a candidate for a `docs/` directory.

Three measured facts make this a structural claim rather than a preference:

1. **It crosses the C wire.** `srmech_tool_entry_t` carries `explanation` (`c/include/srmech.h:5429`)
   and `example_json` (`:5427`). The gcd WHEN clause quoted in §1.1 is present in
   `c/src/srmech_tool_registry.c` as shipped text. For a bare-C / MCU host this prose IS the
   introspect layer — ADR-0012 §7.1 makes exactly that point about the generated registry.
2. **It is hash-bearing.** `srmech_tool_schema_to_json` emits bytes byte-identical to the Python
   `json.dumps(..., sort_keys=True, separators=(",", ":"))`, and `sha256(that) == tool_schema_sha256`
   (`srmech.h:5390-5400`). The prose is inside the attestation. Documentation is not usually inside an
   attestation.
3. **It is population-floored.** The coverage gates (§4) hold it at 100%, which is a contract, not a
   docs aspiration.

**A vocabulary correction this ADR makes explicitly.** `c/include/srmech.h:5396` calls `example` /
`smoke_test_hint` the **"documentation-hint fields"**, and `:5429` describes `explanation` as a
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

---

## 6. The measured reachability deficit — the authored half is at 100%, the derived half is at 0%

That one line is the diagnosis. Every number below is a measurement on this branch, with its basis
named.

### 6.1 There is no read path — only an ingress and an egress

Grepped across the whole `srmech/` package for any reference to `.explanation` / `.example` on a
`ToolEntry`. **Two touch points, and neither is an accessor:**

| touch point | file:line | what it does |
|---|---|---|
| **ingress** | `srmech/introspect/tool_schema.py:515-534` (`_merge_docs`) | merges the curated docs onto the entry **at registration** |
| **egress** | `srmech/introspect/tool_schema.py:390-393` (`to_jsonable`) | copies both fields into the JSON blob **on serialisation** |

**Nothing in between ever reads them.** No search, no filter, no render, no selection, no accessor. The
payload goes in at registration and out at serialisation and is never *consulted*. `srmech/introspect/
__init__.py` — the module that owns `describe()` — contains **zero** references to either field.

*(The `example` hit at `introspect/carrier_schema.py:945` is the carrier-construction example, a
different field on a different registry; it is not a consumer of this surface.)*

### 6.2 `resolve` matches whole dotted segments only

`ToolSchema.resolve_all` (`tool_schema.py:474-485`) is, in full:

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
| 3 | the **`[class]` object-model** descriptors — "DSL-declared class" | ADR-0003 `:54`, `srmech.h:5977`, `:6048` |

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
largest of its ~14 load-bearing uses. Verbatim, `c/include/srmech.h:7154-7155`:

> The §101 `progress=` gate is a **Python-only affordance** (a splice has no meaningful partial;
> **a callable cannot cross the C wire**).

with the near-twin at `srmech.h:7100` — *"predicate stays a **Python-layer** affordance (a callable
cannot cross the C wire)"* — and the JSON-RPC variant at `introspect/tool_schema.py:3698`, *"an
IN-PROCESS Python affordance (a callable cannot cross JSON-RPC)"*.

**The explanation surface does cross the C wire** (§3: `srmech_tool_entry_t.explanation`,
`srmech.h:5429`; the gcd WHEN clause is present in `srmech_tool_registry.c`). Naming it `affordance`
would assert the exact opposite of the measured fact, using the tree's own most established sense of
the word.

The word survives *inside* the surface, in its ordinary sense: §2.1 defines `explanation.WHEN` as **the
affordance in the reader's domain vocabulary**. That is the organ's job description, not the layer's
name.

---

## 11. Instrumentation status — which clauses can return otherwise, and which cannot

Per ADR-0012 §3.2, a clause with no instrument is a preference. Stating which is which is the reason
this ADR is 🟢 Implementing and not ✅ Accepted.

| § | clause | instrument today | status |
|---|---|---|---|
| §2 | the surface is named and defined | — | **definitional**; nothing to instrument |
| §4.1 | coverage floors stay (100% `explanation` + `example`) | `tests/test_tool_docs_coverage_rc240.py` (§12) | **GATED** — inherited, strict floors |
| §3 | the payload crosses the C wire and is hash-bearing | the `tool_schema_sha256` ratchet | **GATED** — inherited |
| §4 | one SSoT, three consumers | **none** | **UNGATED — and currently FALSE** (57 hand-authored, 0 derived). Stated as a target, not as a satisfied property |
| §5 | organs separately selectable | **none** | **UNGATED**; §2.2 shows the delimiter is not uniform enough to make selection mechanical |
| §6.1 | no read path exists | **none** | **UNGATED** — a grep today, not a gate |
| §6.3 | MCP payload is prose-independent | **none** | **UNGATED** — reproducible in three lines (§12), never asserted by CI |
| §6.5 | the address space is unsolved | — | **not instrumentable**; §9.3 declines to specify it |

**Counted exactly: 2 gated · 4 ungated · 2 not instrumentable.** And **both gated rows are inherited
from earlier rcs — this ADR builds no new instrument.** Of the four ungated, one (§4) is not merely
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

Everything else in the brief verified exactly, including the three file sizes, the five `example`
sub-key populations, the three char censuses, `509/545`, `resolve('winding')` with 26 mentions,
`gear` at 0/556 summaries, and the 810,082-byte MCP identity.

### 12.1 A live tamper concern — filed separately, NOT folded in

Demonstrated incidentally while measuring §6.3, and recorded here **only as a cross-reference**:

- **`srmech.introspect.tool_schema._REGISTRY` (`tool_schema.py:498`) is a plain module-level `dict`
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

`srmech/introspect/tool_schema.py` — the SSoT (`_REGISTRY` at `:498`; `_merge_docs` ingress at
`:515-534`; `to_jsonable` egress at `:390-393`; `resolve_all` at `:474-485`) ·
`srmech/introspect/__init__.py:735-736` (the ROOT/INDEX self-description §6.5 reads against) ·
`srmech/introspect/_tool_docs.py` + `_tool_docs_curated.py` (the two identical payloads, §7) ·
`srmech/mcp/_tools.py:395-402` (the `description` assembly that omits the prose) ·
`srmech/cli/*.py` (the 57 hand-authored help strings; `cli/mcp.py:7` for the "nothing is
hand-authored" docstring) ·
`c/include/srmech.h:5378-5437` (`srmech_tool_entry_t`; the "documentation-hint fields" wording at
`:5396`; `explanation` at `:5429`; the byte-identity/hash contract at `:5390-5400`) ·
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

# ADR-0010: srmech namespace declustering — `amsc` is the attestation framework, not the dumping ground

**Status:** 🟢 **ACCEPTED — execution arc OPEN** (`#T1034`). The deferral condition is satisfied: the Class-N precision migration completed (rc318→320) and the class-registry prerequisite landed in rc359. Amendment A (2026-07-29) carries the measured move map, budget and rejected-shorthand record; the arc executes from it. *(Was 🟡 Proposed — target design, deferred behind the precision migration.)*
**Date:** 2026-07-23.
**Authors:** Steven Kirkland + Claude Opus 4.8.
**Supersedes:** none.
**Superseded-by:** none.
**Relates-to:** ADR-0004 (config-driven domain-agnostic surface — the `[class]`/`[cascade]` TOML this ADR re-homes), ADR-0006 (carrier discipline), ADR-0009 (multi-implementation parity — declustering must preserve C/Python parity per module).
**Codifies memory:** `[[project_srmech_module_namespace_needs_declustering]]` · `[[project_class_n_precision_contract_migration_breaking_no_legacy]]` · `[[user_stance_breaking_means_fixing]]`.

---

## Context

`srmech.amsc` was named the **A**ttested **M**ulti-**S**ource **C**ollector/**C**atalog — the provenance/MPR framework. It has since accreted **76 top-level modules + 4 subpackages, 8.7 MB** (measured 2026-07-29; this line read "~70" as an estimate) of which — by the classification test below — **only 4 are attestation**, i.e. **95% of what lives in `amsc` is not `amsc`** (Amendment A.2). The accretion: the whole special-functions galaxy (`rational`, `elliptic_*`, `modular_forms_*`, `thetasum`, `riemann_theta`, `zeilberger`/`gosper`, `jacobi`), the carriers (`q`/`mat`/`vec`/`hv`), the 14 A–N primitives (`format`/`cyclic`/`laplacian`/`hdc`/…), the biology domain (`genome`/`plasmid`/`q8`), and the composition catalogs (`_research/{class,cascade}_catalog/`). The namespace no longer reads as its own map, and `import srmech.amsc.rational` misdescribes what `rational` is. The pressure is real and recurring — rc317 had to move `relative_writhe` out of `srmech.amsc.genome` to dodge the wire-format ratchet; that was the first small instance of this ADR.

## Decision — a domain-and-structure namespace

Top-level namespaces split into **domains** (named by field) and **structure-homes** (named by what they *are*), with `amsc` shrunk back to attestation:

| namespace | kind | holds |
|---|---|---|
| `srmech.math.*` | domain | the 14 A–N primitives + carriers + general math (`rational`, `primes`, `laplacian`, `cyclic`, `poly`) |
| `srmech.physics.*` | domain | the `qm` layer (QM/QFT/SM) |
| `srmech.biology.*` | domain | `genome`/`plasmid`/`q8`/`coupling` |
| `srmech.music.*` | domain | the harmonic/responsion surface |
| **`srmech.<winding>.*`** | **structure** | the special functions — `elliptic_*`, `modular_forms_*`, `thetasum`, `riemann_theta`, `zeilberger`/`gosper` (q-series), `jacobi`. *These are not a domain — they are the mathematics of the winding grade `w` in `S(σ,θ,w)`: elliptic = doubly-periodic (two windings on the torus), modular = the modular group's windings, theta = quasi-periodic, q-series = the nome `q = e^{2πiτ}`.* |
| `srmech.cascade.*` + `srmech.dsl` | structure | `compose`/`atoms`/`the_one`/`cd_register` + `make_class`/`register_class_dir` **and the `[class]`/`[cascade]` TOML catalogs** (moved out of `amsc/_research/`) |
| `srmech.amsc.*` *(reserved, small)* | provenance | `format`(MPR)/`catalog`(register_attested_root)/`descriptor`/`adapters`/`attested/` — **only** the collector/catalog/attestation it was named for |
| `srmech.introspect.*` (or `srmech.tools.*`) | **cross-cutting meta** | `tool_schema` (the op registry), `_tool_docs`, `carrier_schema`, `op_provenance`, `gap_suggester`, `naming`, the `describe()` surface — the tooling/introspection that spans EVERY namespace |
| `srmech.external.*` | — | `profile_loader` + user-registered `[class]`/`[cascade]` dirs — the plugin surface |

**The classification test (the load-bearing rule the audit must apply per module):** ask *"does this module belong to ONE namespace, or does it need to know about ALL of them?"* A module that spans every namespace is **cross-cutting meta**, and it cannot live inside any single namespace — not even `amsc`. `tool_schema` is the exemplar: it registers every op in every domain, so it must sit ABOVE the namespaces (`srmech.introspect`/`srmech.tools`), not inside the provenance framework. The buckets are therefore: **domains** (math/physics/biology/music — bounded field), **structures** (winding/cascade — bounded machinery), **provenance** (amsc — bounded to attestation), and **cross-cutting meta** (introspect/tools — unbounded, knows everything). Every module in today's `amsc` gets re-classified by this test, not left by inertia.

⚠️ **A FIFTH BUCKET, added 2026-07-29 (`#T1034`, user decision): cross-cutting BINDING
INFRASTRUCTURE → top-level private `srmech._native`.** Applying the test above to `_native` (the
1067 KB ctypes shim) gives "knows about ALL of them" — it binds C symbols across math, biology,
winding and cascade — so it cannot live in any single namespace. But it is *not* introspection
either: it reports nothing and registers nothing, it **loads the library**. The four buckets had no
home for that, which was a gap in this ADR rather than an oversight about the module. It becomes
top-level and private: it is the layer every other namespace sits on, it is not a domain, and being
private it carries no public-name obligation. `responsion_schema` goes to **introspect/tools**,
alongside its sibling `carrier_schema`.

### The winding-home name (DECIDED — user, 2026-07-23)
The special-functions home is **`srmech.apokatastasis`** (ἀποκατάστασις, "restoration / return to the original position") — it names the *group's defining property* (the cycle **closes** — wind and **return**), the Great-Year cosmic return, and the Antikythera's mechanical Saros-spiral apokatastasis. It is a **Greek word for a Babylonian–Chaldean idea** (the Stoic cosmic return via Berossus/Chrysippus), so it is cross-tradition, not merely Greek. (Later Christian-theological usage exists; in the astronomical/mathematical sense the term is precise.) The special functions ARE the return-machinery: elliptic = doubly-periodic return, modular = the modular group's return, theta = quasi-periodic return, q-series = the nome's periodicity.
- ~~**Sanity shortening:** ship a terse alias `srmech.apo` and keep the plain-English facade `srmech.winding` re-exporting from it…~~ ⚠️ **STRUCK 2026-07-29 (`#T1034`) — NO SHORTHAND, NO FACADE. `srmech.apokatastasis` stands alone.** A shorthand was designed, measured against every available mechanism, and **REJECTED**; see Amendment A.1 for the measurements. The one-line reason: a second module name cannot be minted without either duplicating objects, duplicating generated rows, or existing only in Python — and the last of those is the parity violation ADR-0009 forbids. The `winding` facade is additionally a legacy-comfort alias, which contradicts this ADR's own **Breaking, no legacy** consequence. Do not re-propose either. If a shorthand is ever wanted it is **its own arc**, and its first task is to give suffix resolution *consumers* (MCP dispatch, the CLI, a C peer) — not to add a name.
- **Distinct from `exeligmos`:** `exeligmos` ("the turning of the wheel," the Antikythera dial) is the specific *winding cycle*; it is the name-of-record for the **winding grade `w`** in `S(σ,θ,w)` if that arg is renamed — see below. `apokatastasis` (the return group) is the *module*; `exeligmos` (the winding) is the *arg*. They are the wind (exeligmos) and its return (apokatastasis).

### `S(σ, θ, w)` winding arg — name-of-record `exeligmos`, symbol stays `w` (or `ω`)
`exeligmos` has no antiquity single-letter glyph (antiquity used no algebraic-variable notation). Keep the symbol **`w`** (already a single letter, means *winding*, unambiguous), documented as *the exeligmos*. If a Greek letter is wanted to match `σ`/`θ`, **`ω` (omega)** is the natural choice — conventionally the winding/rotation symbol, and as the *last* letter it echoes apokatastasis (the return/completion, Α→Ω); caveat: `ω` is overloaded with frequency/angular-velocity elsewhere (F1310's ω-triad). Recommendation: keep `w`. (The `1+3+7+3` construction order of `S` is unchanged per the substrate-frame reasoning — ADR-note only.)

### `make_class` re-homed
`make_class` / `register_class_dir` (the function) are already at `srmech.dsl`, but their `[class]`/`[cascade]` TOML descriptors live under `srmech/amsc/_research/{class_catalog,cascade_catalog,worked_instances}/` — buried in `amsc`. Move the **built-in** catalogs to `srmech.cascade/catalogs/` (the composition layer owns them); the **user-supplied** dirs `register_class_dir` accepts become the `srmech.external.*` extension point.

## Consequences

- **Breaking, no legacy** (`[[user_stance_breaking_means_fixing]]`): ~60 import paths move; every downstream `srmech.amsc.<x>` breaks. The public **facades** (`srmech.calculus` / `trigonometry` / `asymptotic_calculus`) let the *defs* move underneath without breaking the friendly API — they re-export from the new homes.
- **Downstream coordination:** siona (co-name alias) breaks identically and updates in-repo; ephemerides-spectral bumps its floor pin + audits its call sites — a relay, not a unilateral change.
- **Sequencing:** do NOT bundle with the Class-N *precision* migration. That is a *signature* change (bit-identity-critical); this is a *path* change (mechanical, facade-shielded). Bundling would force bisecting a value-drift through pure path churn. Execute this as its own arc **after** rc318→320.
- **Exempt-from-precision is NOT exempt-from-declustering.** The precision migration (rc318→320) exempts the ops whose knob is a first-class *output* parameter, not working-precision — `best_rational` (`max_denominator`; the bignum-lift shipped rc319/`#898`) and the `*_series_truncate` family (`num_terms`). That exemption is about the *signature* contract only. Those same ops still get *re-homed* by this ADR: `best_rational` / `primes` / the 14 A–N primitives move to `srmech.math.*`; the `*_series_truncate` calculus keeps its `srmech.asymptotic_calculus` / `trigonometry` facade (re-exporting from the new `srmech.math` home). Two orthogonal axes — a signature axis (precision) and a path axis (declustering) — and an op can be exempt on one while fully in-scope on the other.
- **Parity (ADR-0009):** every moved module keeps its C/Python parity; the C `srmech_*` symbols are unaffected (Python-side re-homing only), ABI unchanged.
- **Ratchets:** `_WIRE_FORMAT_MODULES`, the count-pins, the rosetta ledger, and the three generated C registries all re-point to the new module paths in the same arc.
- **CLI auto-completion (separate feature, want it either way):** the Python CLI is argparse with NO shell completion today; add **`argcomplete`** (bash/zsh/fish tab-completion over subcommands + module names) so long canonical names like `apokatastasis` are frictionless at the prompt. The C surface is currently a *library* (no CLI `main`); a C host CLI, if/when it lands per ADR-0003, gets a matching completion script (a generated static bash-completion file — no runtime dependency, honoring standalone-C). This does not gate the declustering but makes it ergonomic, and it is worth doing independently.

## Name generation across implementations (compiled C / other locals)

A name that exists only in Python is a parity violation the moment the package is compiled to a bare-C host or bound from Go/Rust (ADR-0009). **Current pipeline:** `srmech.amsc.tool_schema` (the Python `ToolEntry` registry) is the source of truth; four codegen tools — `gen_{tool,carrier,class,responsion}_registry.py` — bake the names into `srmech_{tool,carrier,class,responsion}_registry.c` at build time (each file headed `GENERATED … DO NOT EDIT … Source of truth: srmech.amsc.tool_schema`). So a compiled C host already *carries* the names — but Python is the privileged source, and (tracker `#T930`) a rename that skips one of the four generated tables silently desyncs C dispatch while the pure path keeps answering.

**Target for the declustering (and any future binding):**
1. **The names live in a neutral, implementation-agnostic manifest**, not hardcoded in Python — the module-namespace map (`apokatastasis`; `math`/`physics`/`biology`/`music`) is declared once, and — the substrate-native option — is itself a **genome/attestation record** so any implementation reads the names from the store rather than from Python source.

   ⚠️ **CORRECTED 2026-07-29 (`#T1034`) — the rc261 function-aliasing TOML is NOT the seam.** This
   item previously named it as such. Measured: `srmech/dsl/_alias.py` **rejects module targets
   outright** (`:54-56`; a call on `srmech.amsc.rational` raises `MCPToolError … did not resolve to
   any importable callable`), and even for a *function* target it returns a `functools.wraps`
   **duplicate** rather than the same object (`:71-78`). In its 114 lines it writes neither
   `sys.modules` nor any package attribute, so `import srmech.<alias>` can never be satisfied by it.
   No `[[alias]]` TOML descriptor ships anywhere in the tree. And the rosetta ledger classifies
   `srmech.dsl.alias` as `dev_tooling` — a bucket whose own definition pins it as never-owed-C — so
   it carries **zero** parity by construction. Routing namespace names through it would *reproduce*
   the Python-only shape ADR-0009 forbids, not fix it. The `apo`/`winding` aliases this item listed
   are struck (Amendment A.1).
2. **Every implementation CODEGENS its name registry from that one manifest** at build time — Python's `tool_schema`, the four C registries, and any Go/Rust binding — so the names are byte-identical everywhere and no implementation is primary (ADR-0009).
3. **A rename regenerates ALL name tables in lockstep** — the `#T930` ripple: tool + carrier + class + responsion registries + the count-pins + rosetta.

   ⚠️ **CORRECTED rc359 (`#T1009`) — "gated so a desync fails loudly" was NOT true of all four.** It
   held for the **tool** registry (a hash witness, which caught rc348), for **carrier** and
   **responsion** (byte-identity ratchets at `test_carrier_schema_rc205.py:198-205` and
   `test_responsion_schema_rc225.py:267`), and for `c_dispatched` **ops** (the rc300 op→symbol claim
   manifest). It did **not** hold for the **class** registry, whose only witness asserted that names
   *appeared* — never that the descriptor BODY matched. rc300 was **mis-cited** here: it stops an op
   silently falling back to pure on a stale `.so`, which is a different failure from a registry whose
   *content* has drifted. rc359 shipped the content witness; **35 dotted op refs are now verified
   resolvable in C**.

   ⚠️ **GENERATED ARTIFACTS STORE NAMES AS DECIMAL BYTE ARRAYS, SO A TEXTUAL SWEEP LIES.** The
   `[class]` and carrier descriptors are embedded as decimal byte arrays, so the very prefixes this
   ADR renames do not appear as text at all.

   ⚠️ **CORRECTED 2026-07-29 (`#T1034`) — THIS PARAGRAPH NAMED THE WRONG FILE.** It previously read
   *"the CLASS registry is invisible to grep — this is the one that will bite this arc"*, measured on
   `srmech_class_registry.c` alone (0 as text / 40 decoded). Asking the same question of **every**
   generated artifact — which the next sentence already instructed and which nobody had done —
   finds the class registry is the *smallest* case:

   | generated artifact | `srmech.amsc.` as text | **decoded** | textual sweep sufficient? |
   |---|---|---|---|
   | `srmech_carrier_registry.c` | 191 | **533** | **NO — MIXED, and the largest by 13×** |
   | `srmech_class_registry.c` | 0 | **40** | NO — 100% invisible |
   | `srmech_tool_registry.c` | 1219 | **4** | NO — MIXED, small tail |
   | `srmech_responsion_registry.c` | 72 | 0 | yes |
   | `_tool_docs.py` | 1201 | 0 | yes |
   | `_c_claims.py` | 250 | 0 | yes |
   | `srmech.h` | 176 | 0 | yes |
   | **total** | **3109** | **577** | |

   **577 encoded occurrences, and 533 of them sit in `srmech_carrier_registry.c` — a file this ADR
   never mentioned.** And **MIXED is the more dangerous mode than 100%-invisible**: a textual sweep
   on the carrier registry reports 191 hits, "fixes" them, and *looks like it worked* while 533
   survive. A file that reports a flat **0** at least invites suspicion; a file that reports a
   plausible number does not. **The decode-aware rename check must cover carrier + class + tool** —
   three of the seven, not one.
4. **Locale note:** the Greek canonical names (`apokatastasis`/`exeligmos`) are ASCII-transliterated identifiers (module names are ASCII), so no encoding/locale hazard at the import or C-symbol layer; the Greek glyphs live only in docstrings/prose, which the introspect surface already carries UTF-8.

This makes the declustering's names a **single-source, codegen-to-all-implementations** artifact — the correct shape before any rename lands.

⚠️ **PREREQUISITE — established rc359, and it is an ORDERING constraint, not a checklist item.** The
lockstep gate in (3) must land **and be green in its own rc BEFORE** the rename arc opens — never
inside it. *An instrument built in the same arc as the change it is meant to detect has no green
baseline, so a red is unattributable to either the rename or the instrument.* `#T1009` satisfied this
for the class registry in rc359; ask the same of any table this ADR adds, and of the decode-aware
check above.

## Status of adoption
Design record only. First concrete step (`relative_writhe` → Class-N surface) shipped in rc317.

**Deferral condition SATISFIED (rc359).** This ADR previously read "full execution deferred behind
the precision migration" — that migration is **complete** (the Class-N precision-contract arc shipped
rc318/319/320), and the class-registry prerequisite above landed in rc359. The execution arc is
tracked as `#T1034`. This ADR is the reference for it.

---

## Amendment A — the executable research record (2026-07-29, `#T1034`)

Measured against srmech **0.9.0rc360** at `7b313407b`, **516** registered ops, `SRMECH_ABI_VERSION`
**10**. This amendment exists so the execution arc **rolls out without adjudicating anything**. Where
a number here disagrees with the body above, this amendment is correct and the body has been
annotated in place.

### A.1 The shorthand — DESIGNED, MEASURED, REJECTED

`srmech.apokatastasis` stands alone. No `apo`, no `winding`, no facade, no alias. Each candidate was
measured, and each fails for a *different* reason — which is why the conclusion is a rejection rather
than a preference:

| mechanism | why it fails | evidence |
|---|---|---|
| rc261 `srmech.dsl.alias` | rejects module targets; returns a `wraps` **duplicate** for functions; never touches `sys.modules`; no `[[alias]]` TOML ships; classified `dev_tooling` = never-owed-C ⇒ **zero parity** | `srmech/dsl/_alias.py:54-56`, `:71-78` (114 lines) |
| `sys.modules` package alias | **duplicate** submodule objects, and it *clobbers the canonical* — the original module's `__name__` is overwritten | measured probe |
| PEP-562 facade | cannot serve `import srmech.<alias>.<mod>` (no `__path__`); drifts undetectably | `srmech.calculus` re-exports **24 of 28** (`rational.__all__` = 28); the 4 missing include **`relative_writhe`** — the very op this ADR cites at its own first executed step |
| a second `ToolEntry` | new generated rows at a measured **13 rows per op across 7 files**, plus a bump in every count-pin | the duplication the project hard-removes |
| suffix resolution (`ToolSchema.resolve`) | **reaches ZERO consumers** — see below | `srmech/amsc/tool_schema.py:436-465` |

⚠️ **The suffix-resolution escape is the one worth recording, because it looked like the answer.**
`ToolSchema.resolve()` / `resolve_all()` already ship and mint no name, so they appear to give a
shorthand for free. Traced to the three surfaces a name must reach, they arrive at **none**:

- **Python import** — nothing; a resolution method cannot shorten an `import` statement.
- **C** — `c/src/srmech_tool_schema.c` exports only count/get/find, and `_find` is exact `strcmp`
  (`:59-70`). A resolving peer is a *proposal*, not a path.
- **MCP / introspect** — dispatch is exact `schema.lookup(name)` (`srmech/mcp/_tools.py:507`), and
  `describe()` takes **no arguments** (`srmech/introspect/__init__.py:722`), so it has no
  name-lookup surface to shorten. No `resolve` in `srmech/cli/`.
- **Measured callers of `resolve`/`resolve_all` inside `srmech/`: ZERO.**

So "it duplicates nothing" is an **EMPTY** null — *a mechanism with no consumers cannot duplicate
anything*. It is additionally a **class method**, and the parity ledger structurally cannot see
methods (`_live_ops()` skips classes, `tests/test_rosetta_completeness.py:1060-1062`; 741 live ops,
zero `ToolSchema` entries), so it is not merely exempt from C-parity but **unclassifiable by the only
gate that enforces ADR-0009** — strictly worse than the `dsl.alias` it was meant to beat.

⚠️ **And the property it rested on is FALSE.** "The top-level namespace is never needed to
disambiguate" holds for 495 of 516 names, not all: **21 names are 3-segment**, so their 2-segment
suffix *includes* the first-level package segment this arc renames. `srmech.spectral.similarity`'s
leaf collides with `srmech.amsc.hdc.similarity`, so its **only** unambiguous shorthand is
`spectral.similarity` — a first-level segment. Suffix uniqueness is therefore **not invariant under
this arc**.

**If a shorthand is ever wanted, it is its own arc, and its first task is to give suffix resolution
CONSUMERS** (MCP dispatch, the CLI, a C peer) — not to add a name. It is not part of declustering.

For the record, the ergonomic cost being declined: today's longest registered name is **65** chars
(`srmech.amsc.riemann_theta_multisum.multivariate_riemann_theta_sum`); after the move the longest is
**74** (`srmech.apokatastasis.riemann_theta_multisum.multivariate_riemann_theta_sum`). Nine
characters, in import statements that are authored once in source rather than typed at a prompt.

### A.2 Move map — 73 of 75 classified, both adjudications closed

`srmech/amsc/` holds **76 `.py` modules + 4 subpackages, 8.7 MB**.

| destination | n | note |
|---|---|---|
| `srmech.apokatastasis.*` | **31** | the elliptic / modular / theta / q-series family — 41% |
| `srmech.math.*` | 22 | A–N primitives + carriers + general math |
| `srmech.introspect.*` | 10 | + `responsion_schema` |
| **`srmech.amsc.*` KEEPS** | **4** | `format`, `catalog`, `descriptor`, `gap_suggester` |
| `srmech.biology.*` | 4 | `genome`, `plasmid`, `q8`, `coupling` |
| `srmech.cascade.*` | 1 | `compose` |
| `srmech.music.*` | 1 | `harmonics` |
| `srmech._native` | 1 | the fifth bucket |

**The namespace named for attestation keeps 4 of 75 modules — 5%.** That single number is the
justification for the arc: `amsc` is 95% not-`amsc`.

### A.3 Budget — the body's "~60 import paths" counts PATHS, not sites

**9,897 reference lines across 1,124 files, 125 distinct target names.**

| bucket | lines | files |
|---|---|---|
| **HAND-EDIT** (package 2700 · tests 2210 · tools 84 · C 448) | **5,442** | **751** |
| regenerated — free | 2,166 | 7 |
| rosetta ledger — script | 465 | 1 |
| **DO NOT TOUCH** — `CHANGELOG.md` + `notes/` are dated records; rewriting paths in them **falsifies** them | **1,316** | 196 |
| ADR/prose — adjudicate individually | 215 | 48 |
| **RELAY** — *not only downstream*: includes `.github/workflows/srmech-ci.yml` and the **root `CLAUDE.md`**, plus ephemerides-spectral | 293 | 121 |

⚠️ **A HAND-AUTHORED SURFACE THIS ADR AND THAT BUDGET BOTH MISSED.**
`srmech/amsc/_tool_docs_curated.py` holds **360 full dotted-name keys, 276 of them
`srmech.amsc.*`**. It is an **input** to `tools/gen_tool_docs.py`, so **no codegen rewrites it** —
those are 276 hand edits nobody had costed. The favourable half: its gate **exists and is pure**
(`tests/test_tool_docs_coverage_rc240.py:133-145`, no native gating), so it is a **seventh**
rename-detecting instrument and it will go red with 276 orphans the moment `amsc` moves.

### A.4 The count-pins do NOT gate a rename — and structurally cannot

Their predicate is `len(tool_schema_view()["tools"])`. **It reads no name.** Simulating this ADR's
own example move (`srmech.amsc.rational` → `srmech.math.rational`) relocates **28 of 516** dotted
names while the total stays **516** and every pin stays **GREEN**.

That is an **EMPTY** null about the pin, not a defect: a cardinality assertion measures cardinality,
and does it correctly. It is a **real gap about the arc**. The pin family is **54 test files / 60
assertions** — the obvious grep finds 42, which counts one spelling; twelve more pin the same number
as `len(schema.tools)` / `len(shipped)` / `len(names)`. All 60 are cardinality-only, so the verdict
holds over the whole family.

The instrument that **does** detect a rename on a pure host is
`tests/test_registry_smoke_rc127.py:53` — it importlib-resolves every registered dotted name, with no
hardcoded root list and no native gate. Note that the carrier and responsion byte-identity ratchets
**skip** behind `_needs_native` (`tests/test_carrier_schema_rc205.py:63`), so they are silent
whenever `HAS_NATIVE` is false. CI does build native and runs the asserts-live cell un-skipped
(`.github/workflows/srmech-ci.yml:112` installs `-e ".[dev]"` via scikit-build; the cell asserts
`HAS_NATIVE` before the full suite).

⚠️ **The rosetta gate is HALF-BLINDED, and this bites the arc directly.** Its `_ROOTS` is a
hardcoded 12-tuple containing **none** of this ADR's target namespaces, duplicated in **four** places
(`tests/test_rosetta_completeness.py:104-110`, `tests/conftest.py:551`,
`tests/test_rosetta_transitive_standalone.py:86`, `notes/_rosetta_inventory.py:22`). Moved ops go
invisible to `_live_ops()`, so only the *stale* assertion fires, never the *unclassified* one.

### A.5 Prerequisite rcs — each in its OWN rc, before any rename

Per the ordering constraint above: an instrument built in the same arc as the change it detects has
no green baseline, so a red is unattributable.

1. **A name-SET witness, not a name-COUNT witness** — a committed sorted manifest of all 516 dotted
   names plus its `srmech.amsc.format.sha256_bytes` digest. ⚠️ It **must be hand-committed and
   review-gated, NOT emitted by `tools/codegen_manifest.py`** — if codegen writes it, the rename
   arc's own `python tools/gen_*.py` makes the digest green unconditionally and the witness becomes
   another EMPTY probe, reproducing the exact failure this section indicts.
2. **Single-source the rosetta `_ROOTS`** — collapse the four duplicated copies to one definition,
   so the rename updates one place instead of four. (Widening it to the new namespaces cannot precede
   their existence; de-duplicating it can.)
3. **A decode-aware prefix check** over `srmech_carrier_registry.c` + `srmech_class_registry.c` +
   `srmech_tool_registry.c`, per A.3's table.
4. **Fold `_tool_docs_curated.py`'s 276 hand edits into the plan** before estimating the rename rcs.

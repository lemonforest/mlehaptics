# ADR-0010: srmech namespace declustering — `amsc` is the attestation framework, not the dumping ground

**Status:** 🟢 **ACCEPTED — execution arc OPEN; STRUCTURE slice shipped v0.9.0rc364, FIRST MODULE-MOVING slice shipped v0.9.0rc366** (`#T1034`). The deferral condition is satisfied: the Class-N precision migration completed (rc318→320) and the class-registry prerequisite landed in rc359. Amendment A (2026-07-29) carries the measured move map, budget and rejected-shorthand record; Amendment B (2026-07-30) carries the first executed slice — `srmech.cascade` is real, the built-in catalogs moved out of `amsc/_research/`; Amendment C (2026-07-31) carries the first slice to relocate a module with public callables — `harmonics` → `srmech.music` — which is where the census and op-name-set witness got their first live test. *(Was 🟡 Proposed — target design, deferred behind the precision migration.)*
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

✅ **EXECUTED v0.9.0rc364 — this is the arc's first execution slice.** See Amendment B for the shape it established, the alias-home hole it filled, and what it cost against the estimate.

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
~~Design record only.~~ First concrete step (`relative_writhe` → Class-N surface) shipped in rc317; the
**first execution slice shipped v0.9.0rc364** — `srmech.cascade` created, the built-in
`[class]`/`[cascade]`/worked-instance/alias catalogs moved out of `srmech/amsc/_research/`, and that
subpackage deleted. `srmech/amsc/` is down to **3 subpackages**; its 76 `.py` modules are untouched.
See Amendment B.

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
5. **A module-and-subpackage CENSUS of `srmech/amsc/`** — added rc364 (Amendment B.5). The
   decode-aware prefix check in (3) counts *dotted module paths*, so it is structurally blind to
   anything that is not one; rc364 moved four directories out of `amsc` and both of its channels read
   FLAT. The quantity the arc actually drains, module by module, has no instrument. This one must
   land in its OWN rc with a green baseline before the first MODULE-moving slice — the same ordering
   constraint as the rest of this list, and rc364 deliberately did not mint it inside itself.

   ✅ **DONE — v0.9.0rc365 (`#T1034`).** `tests/test_amsc_module_census_rc365.py` + the hand-committed
   manifest `tests/amsc_module_census.txt` pin the population as a name-SET (75 module stems + 3
   subpackage names) plus a `sha256_bytes` digest, mirroring the rc361 op-name-SET witness. It is
   **down-only** (live ⊆ committed; a module may leave, one appearing is red), it checks departures
   against A.2's move map (removed ⊆ the 71 non-keepers; the four keepers never depart), and its
   non-vacuity is proved by four injections — mapped-departure (digest changes), unmapped-departure
   (move-map red), new-module (down-only red), keeper-departure (keeper red). It ships alone, green,
   and moves no module, satisfying this item's own ordering constraint. **The first module-moving
   slice is unblocked.** Cheapest first real slice measured for the conductor: `compose` →
   `srmech.cascade` (the namespace already exists from rc364) or `harmonics` → `srmech.music`.
   ✅ **`harmonics` → `srmech.music` SHIPPED v0.9.0rc366** — the first module-moving slice; it also
   found and fixed a three-way conflation the census's rc365 mint could not see (Amendment C).

---

## Amendment B — the first execution slice, v0.9.0rc364 (`#T1034`, with `#T1039`)

`srmech.cascade` is real. The built-in `[class]` / `[cascade]` / worked-instance catalogs left
`srmech/amsc/_research/` for `srmech/cascade/catalogs/`, `srmech/amsc/_research/` was deleted, and a
fourth catalog — `alias_catalog/` — was created to fill a hole the move map did not cover. This
amendment records the shape, the two decisions, the measured cost, and the three things the plan got
wrong. Where it disagrees with the body or with Amendment A, **this amendment is the measurement**.

### B.1 The pattern `srmech.cascade` sets — three rules for every later slice

The first namespace to land decides how the rest read, so the rules are written down rather than left
to be inferred from a diff.

1. **A slice relocates a PARENT; it does not rename the LEAF.** `class_catalog` / `cascade_catalog` /
   `worked_instances` kept their directory names verbatim. This was tempting to "fix" — under a
   parent called `catalogs/`, the leaf `cascade_catalog` stutters — and the temptation was declined
   for the same reason this ADR's own prerequisite section gives one level up: *an instrument built
   in the same arc as the change it detects has no green baseline, so a red is unattributable.* A
   slice that moves AND renames makes every red ambiguous between the two. One slice, one variable.
   (The stutter is one path segment, and the constants `CLASS_CATALOG_DIR` / `CATALOG_DIR` already
   read `*_CATALOG`, so the on-disk name matches the API name. A rename, if ever wanted, is its own
   rc.)

   A second, harder reason surfaced while deciding: **`class` is a Python reserved word.** A
   "name the directory after the TOML section it declares" rule breaks on its very first member —
   `catalogs/class/` can never carry an `__init__.py`. `class_catalog` is the name that rule would
   have had to fall back to anyway.

2. **Declarative descriptors go under `catalogs/`; imperative modules go beside it.** When the later
   slices move `compose` / `atoms` / `the_one` / `cd_register` into this namespace they land at
   `srmech/cascade/*.py`, with the TOML still under `srmech/cascade/catalogs/`. The two kinds of
   content stay visually separated at the top of the package.

3. **Every catalog directory carries an `__init__.py`.** Measured first, as instructed:
   `worked_instances/` had NO marker and shipped anyway, because both backends
   (`wheel.packages = ["srmech"]` / `[tool.hatch.build.targets.wheel].packages`) copy the package
   tree wholesale. So the marker is not *required* — it is the difference between inclusion by
   declaration and inclusion by each backend's heuristic. rc364 exists because an adjacent assumption
   of exactly that kind cost two descriptors their place in the wheel (B.3), so all four directories
   now declare themselves, and the marker doubles as where the directory documents itself.

`srmech/cascade/__init__.py` imports nothing and exports nothing: the loaders reach the descriptors by
path, so `import srmech.cascade` stays free. Asserted, not merely intended
(`tests/test_cascade_catalog_home_rc364.py`).

### B.2 The alias home — DECIDED, and why the map had a hole

The move map covers *built-in catalogs* and *user-supplied dirs*. The two shipped-example alias
descriptors are **neither**: `tests/data/genome_type_aliases_legacy.toml` (rc271, a
`[genome.type_aliases]` VALUE alias) and `tests/data/music_domain_aliases.toml` (rc362, the tree's
first `[[alias]]` FUNCTION alias). They are shipped worked examples of a config layer — the same kind
of object as `genome.toml` in `class_catalog/`, not the same kind as a user's own directory.

**Decision: `srmech/cascade/catalogs/alias_catalog/`, a fourth sibling.** Reasoning:

- **Aliasing is composition, so the composition layer owns it.** ADR-0004's ladder is *classes →
  pipelines → names*: `make_class` declares a class, `[chain]` declares a pipeline, `[[alias]]`
  declares a name binding. Three rungs of one ladder; the first two live here.
- **Sibling-of, not child-of.** `alias_catalog/` sits beside `class_catalog/` and `cascade_catalog/`
  rather than inside either, because a name binding is not a `[class]` and not a `[cascade]`. The
  directory is named for the TOML section it declares, which is the rule the other three follow.
- **Not `srmech.external.*`.** That is reserved for *user-supplied* directories. A descriptor srmech
  ships is A-tier by construction; `register_alias_dir` is the B-tier peer, and it now exists.
- **Not a new top-level namespace.** Aliasing mints no op, owes no C parity (`dev_tooling` in the
  rosetta ledger), and has two descriptors. A namespace for it would be a name with nothing under it.

ADR-0012 clause C6 explicitly deferred this ("does not decide whether the alias layer's package home
is a new `_research/alias_catalog/` or something else — implementation decisions for the rc that
closes it"). It is decided here; C6's `describe()` half stays open, and is now open on a narrower
front — an enumeration axis over a layer that finally has something to enumerate.

### B.3 The live wheel defect this slice closed — and how long it had been live

`genome_type_aliases_legacy.toml` is the documented migration path for rc271's **BREAKING**
`stick`→`plasmid` / `minted`→`nuclear` rename. Its own header prints the call to make:

> *"Opt in with ONE call: `genome.load_type_aliases_toml("genome_type_aliases_legacy.toml")`"*

A **bare filename**. The file lived under `tests/data/`; `tests/**` is in `sdist.include` and **not**
in the wheel (`wheel.packages = ["srmech"]`, no force-include, no `MANIFEST.in`). So: install the
wheel, follow the header, get `FileNotFoundError` — for **93 rcs** (rc271 → rc363). The loader shipped
in `genome.__all__` and carried an introspect entry; the thing it loads did not ship at all.

rc362 then landed the tree's first-ever `[[alias]]` descriptor in the same directory, which is the
part worth generalising: **it was not a mistake, it was the absence of an alternative.** There was no
`ALIAS_CATALOG_DIR`, so `tests/data/` was where a descriptor went *by default rather than by
decision*. The fix therefore had to be the directory constant, not the file move.

Both halves are now **executed** in tests rather than described: the documented one-liners are run and
their documented effects checked, and a rule — not a filename pair — forbids the next alias descriptor
from landing in `tests/data/`.

### B.4 The registered alias directory (`#T1039` made concrete)

`srmech/dsl/_alias.py` gained the shape `_class_catalog.py` has had since rc39:

| class layer (rc39) | alias layer (rc364) |
|---|---|
| `CLASS_CATALOG_DIR` | `ALIAS_CATALOG_DIR` |
| `register_class_dir` · `SRMECH_CLASS_PATH` | `register_alias_dir` · `SRMECH_ALIAS_PATH` |
| `list_classes` | `list_alias_descriptors` |
| `load_class_catalog` (path → descriptor) | `resolve_alias_descriptor` (name **or** path → descriptor) |

Resolution is **filesystem-first**, so no existing caller changes meaning; a bare name falls through
to the catalog. Shipped descriptors are A-tier and a user directory may not shadow one, matching
`load_class_catalog`.

**What it enables, concretely: a domain can now SHIP its vocabulary.** An acoustic user `pip install`s
srmech and gets `music_domain_aliases.toml` — *"partials"*, *"bell_tuning"*, *"overtone_series"* — with
no source edit and no recompile, which is the ADR-0004 config-driven stance applied to the one rung
that had an API and no plugin surface. A research group drops its own `*.toml` in a directory and calls
`register_alias_dir`.

Three new rosetta rows, and **the split across them is not the obvious one**:

| op | bucket | why |
|---|---|---|
| `resolve_alias_descriptor` | **host_glue** | descriptor FS *discovery* — a bare-C host must FIND the file before `srmech_toml` can parse it. The `load_catalog` / `load_class_catalog` / `get_descriptor` precedent. |
| `list_alias_descriptors` | **dev_tooling** | *browse*. A C host resolves the one name it was handed; it never enumerates alternatives. Peer of `list_cascade_ops` / `list_classes`. |
| `register_alias_dir` | **dev_tooling** | *configure*. Mutates a process-local search path. Peer of `register_catalog_dir` / `register_class_dir`. |

`composes_c` is **UNMOVED at 138** — none of the three composes a C op; the alias layer's `composes_c`
rows are the rc261 *parse* ops, which route through the C `srmech_toml`, and a resolver that returns a
`Path` parses nothing. host_glue **21 → 22**, dev_tooling **51 → 53**, total **210 → 213**.

⚠️ **The discriminator is NOT "does it touch the filesystem" — all three do.** It is **LOAD/GET vs
BROWSE/CONFIGURE**, and `srmech.dsl` already encodes that split over the *same directory*:
`load_class_catalog` reads it (host_glue) while `list_classes` browses it (dev_tooling). rc364 first
shipped `list_alias_descriptors` as host_glue by reasoning from the *mechanism* (it calls `glob`)
instead of from the *capability*, which made it the only host_glue `list_*` in `srmech.dsl` against
five dev_tooling siblings. CI reported the counts (21→23 / 51→52); **the fix was the classification,
not the pin.** Recorded because the same mechanism-vs-capability slip is available to every later
slice that adds a public callable.

No `ToolEntry`, so no op-count pin moves — `srmech.dsl` functions carry no tool-schema rows, which is
worth knowing before scoping a later slice.

### B.5 ⚠️ THE RATCHET DID NOT MOVE, AND THE PLAN IS WHAT WAS WRONG

`CEIL_AMSC_PREFIX` was expected to FALL. Measured after `tools/regen_all.py`:

| channel | before | after |
|---|---|---|
| as-text | 2957 | **2957** |
| decoded | 577 | **577** |

Flat on every per-artifact pair. The only regen delta in the tree was one line of header COMMENT in
`srmech_class_registry.c`.

**This ratchet counts a DOTTED prefix — a module-path population.** What this slice moved was *data
files*, whose location is only ever written as a filesystem path with slashes, which the prefix does
not match; and the descriptor BODIES are untouched, so a `[class]` descriptor's
`op = "srmech.amsc.genome.chromosome"` still names an op whose module has not moved. All 40 decoded
hits in the class registry survive **by construction**.

The instrument is correct about the population it names. **The wrong belief was this ADR's**: the body
and Amendment A treat "move the catalogs" and "move the modules" as one drain, and only the second
contributes to that counter. *A catalog move is orthogonal to the dotted-prefix ratchet.* Later slices
should not read a flat rc as a failed one, and should not hunt for a pin to lower after a
catalog-shaped slice.

**The quantity this slice DID reduce has no instrument.** `srmech/amsc/` went from **4 subpackages to
3** (`_research/` deleted; `adapters`, `attested`, `cascade` remain) with its 76 `.py` modules
untouched. Nothing in the tree measures that — hence A.5 item 5 above.

### B.6 Cost, measured against the estimate — the number for planning the rest

Amendment A.3 budgets **5,442 hand-edit lines across 751 files** for the whole arc. This slice's share:

| | A.3's expectation | rc364 actual |
|---|---|---|
| catalog-reference sites (`class_catalog` · `cascade_catalog` · `worked_instances`) | 135 + 57 + 14 = **206 lines / 62 files** | **28 live path literals**; the rest are CHANGELOG (DO-NOT-TOUCH), test *filenames*, dated `notes/`, and `srmech.dsl._class_catalog.*` MODULE refs the move does not touch |
| files hand-edited | — | **29** |
| regenerated | — | **1 of 6** artifacts, **1 line** |
| new files | — | 6 (4 `__init__.py`, 1 test module, this amendment) |

**The ratio worth carrying forward is ≈ 7:1 — 206 grep hits, 28 real edits.** A.3's bucket table
already anticipates this shape (its DO-NOT-TOUCH and regenerated rows), but the headline "5,442
hand-edit lines" does not, and a brief scoped from the headline over-scopes by close to an order of
magnitude. **Classify before editing**: code imports vs. path literals vs. prose vs. dated records vs.
generated artifacts each need different handling, and only the first two are mechanical.

**What actually consumed the slice was NOT the move.** In rough order of effort: the alias-home
decision and its two ADR write-ups; the wheel defect and its test; the new `_alias` catalog surface;
the rosetta ripple (3 ledger rows + 2 annex pins + 1 dev-tooling allowlist entry + the root tuple);
and, last and smallest, 28 path edits. **A path change is cheap; the ripple and the adjudication are
not.** Scope the remaining slices by *how many public callables and ledger rows they disturb*, not by
how many paths they rewrite.

### B.7 Two defects found in passing, both fixed here

1. **`srmech.cascade` was appended to the rosetta walk roots** (`tests/rosetta_roots.py`), moving it
   from `_ADR0010_NEW_NAMESPACES` to `_ADR0010_EXISTING_DESTINATIONS` — the one route
   `test_rosetta_roots_single_source_rc361` accepts, and the rule rc362 established for
   `srmech.music`. It adds **zero rows**, because the namespace holds descriptors and no callables.
   That is still the right edit and the distinction matters: a *non-existent* root is silently skipped
   (EMPTY-because-unsupported), an *existing empty* root is a measured zero that goes red the moment a
   later slice moves ops in.

2. **Two guards were unrunnable inside a git worktree.** `test_ref_notation_emitted_rc348.py` and
   `test_rosetta_roots_single_source_rc361.py` both excluded paths by testing
   `"worktrees" in path.parts` on the **absolute** path. Run from a `.claude/worktrees/` checkout —
   which is where this project's build discipline says to work — that matched EVERY file, so the
   ref-notation scan derived an EMPTY task-ID set and both of its strict-zero tests failed on
   *"derived no local task IDs at all - the scan is broken"*. The non-vacuity assert did its job (this
   was loud, not silent), but the gate could not go green in the sanctioned environment. Fixed by
   testing the parts of the path **relative to the scan root**, which preserves the intent exactly:
   `.claude/worktrees/` sits above `docs/`, so nothing below `docs/srmech` can be a worktree.

## Amendment C — the FIRST MODULE-MOVING slice, v0.9.0rc366 (`#T1034`)

rc364 created a *structure* namespace (`srmech.cascade`) and moved directories; B.5 records that **the
ratchet did not move** because no registered op relocated. rc366 is the first slice to move a **module
carrying public callables** out of `amsc` to a domain home: **`srmech/amsc/harmonics.py` →
`srmech/music/harmonics.py`** (the A.2 `srmech.music.* | 1 | harmonics` row). The leaf name `harmonics`
is kept (B.1 rule 1: a slice relocates the parent, never renames the leaf), and `srmech.music` already
existed from rc362, so this was a drop-in, not a new namespace. It is the first live exercise of the
rc365 census and the rc361 op-name-set witness on a real move.

### C.1 The census's rc365 mint conflated three quantities — the first move exposed it, and it is FIXED

The census docstring's "two-edit procedure" (drop the module from the manifest + update the digest) is
**incomplete**, and dropping `harmonics` from the manifest proved it by turning
`test_the_move_map_matches_A2` red — *not* because harmonics was misfiled, but because the rc365 mint
treated three different quantities as one, true only in the snapshot where nothing has moved:

- the **manifest** = the CURRENT amsc population (must shrink so the down-only ceiling drops and a
  re-add is caught);
- `NAMED_DEPARTURES` / `ADR_A2_DESTINATION_COUNTS` = A.2's **fixed plan** (`harmonics → music` is a
  correct classification forever, whether or not it has moved);
- drain **progress** (which modules have actually landed).

At rc365 all three agreed. The move-map test asserted "every named member is still in the manifest",
and the "73 of 75" gap was stated against the live count — both rc365-snapshot truths. The fix
introduces a `LANDED` record and a conservation invariant (`EXPECTED_N_MODULES + len(LANDED) ==
ORIGINAL_N_MODULES`), makes "a named member is REAL when still in amsc OR landed", and states the gap
against a fixed `ORIGINAL_N_MODULES`. The manifest still drops the leaver (the ceiling still falls);
A.2's record is preserved; and a manifest shrink can no longer be booked without saying WHERE the
module went. The census docstring's procedure is rewritten to three coupled edits. **census digest:
`c3c3d174…` → `52a34d12…`; `harmonics` dropped (78 → 77 lines, 75 → 74 modules).**

### C.2 What the prose gate did NOT catch — a real planning input for the bigger buckets

The rc363 prose op-ref gate was expected to fire on the stale citation. **It did not**, and the reason
is worth carrying forward: harmonics' only dotted `srmech.amsc.harmonics.*` strings were the ToolEntry
`name=` fields, which the gate does not scan (it reads `summary` / `explanation` / params / returns),
and its prose cites siblings in **slash-form** `srmech/amsc/harmonics.py:NN`, which the gate excludes as
a filename. So a module whose cross-citations are file-path:line refs is **invisible** to the
dotted-path gate. The slash-form citations were fixed anyway (below the gate's floor, for correctness).
The instrument that actually caught the move was the **rc361 op-name-set witness** (the SET + digest
changed; `EXPECTED_N` stayed 525, a move not an add/remove). The bigger `math` / `apokatastasis`
buckets are more likely to carry genuine dotted cross-citations that WILL trip the prose gate.

### C.3 Cost — a second data point for B.6's ≈7:1 rule

The non-compute split did **not** move: `classify_harmonic` is `non_compute` / `composes_c` and stayed
`composes_c` — a rename preserves the bucket, so all four non-compute counts are unchanged; only the
row's dotted name and the `COMPOSES_C_ZERO_REACH_PINNED` pin moved (amsc → music). Measured ripple:
**2 registered op names, 2 rosetta ledger rows, 1 zero-reach pin, 1 op-name-set digest, 1 census
manifest + digest + the `LANDED`/conservation fix, 2 worked-example ledger rows, 3 regenerated
artifacts (`_tool_docs.py` + 2 C registries), 6 curated-doc fields (2 harmonics + 4 siblings whose
`harmonics.py` citation was repointed), 5 test-file imports.** As B.6 predicted, the path change itself
was trivial; the cost was the **ledger/census ripple and the census-design adjudication**. Scope the
`math` / `apokatastasis` buckets by public-callables-and-ledger-rows disturbed, not path count — and
budget for the census `LANDED` list growing one entry per landed module.

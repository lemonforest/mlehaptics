# ADR-0010: srmech namespace declustering — `amsc` is the attestation framework, not the dumping ground

**Status:** 🟢 **Implementing — execution arc OPEN; STRUCTURE slice shipped v0.9.0rc364, FIRST–FOURTH MODULE-MOVING slices shipped v0.9.0rc366 / rc367 / rc368 / rc369** (`#T1034`). *(rc409: the word was "ACCEPTED" while the README index said 🔄 Proposed — the two surfaces disagreed for the whole rc364→rc408 window. 🟢 is now the DEFINED fifth state "Implementing", which is what this ADR has meant by it all along; the glyph did not change, only the vocabulary caught up.)* The deferral condition is satisfied: the Class-N precision migration completed (rc318→320) and the class-registry prerequisite landed in rc359. Amendment A (2026-07-29) carries the measured move map, budget and rejected-shorthand record; Amendment B (2026-07-30) carries the first executed slice — `srmech.cascade` is real, the built-in catalogs moved out of `amsc/_research/`; Amendment C (2026-07-31) carries the first slice to relocate a module with public callables — `harmonics` → `srmech.music` — which is where the census and op-name-set witness got their first live test; Amendment D (2026-07-31) carries the second — `naming` → `srmech.introspect` — which corrected the module-move instrument set to THREE (the decode-aware prefix ratchet, missed by rc366's first commit) and hit the first C-side entanglement (`srmech_invoke.c` hardcodes the dotted tool name). *(Was 🔄 Proposed — target design, deferred behind the precision migration. v0.9.0rc415, `#T1098`: this narration spelled the earlier state 🟡, a glyph the legend and the lifecycle line both define NOWHERE — the rc409 gate read status glyphs but never narration, so an undefined glyph survived in the same line as a defined one.)*
**Clauses:** unaudited.
**Date:** 2026-07-23.
**Authors:** Steven Kirkland + Claude Opus 4.8.
**Supersedes:** none.
**Superseded-by:** none.
**Relates-to:** ADR-0004 (config-driven domain-agnostic surface — the `[class]`/`[cascade]` TOML this ADR re-homes), ADR-0006 (carrier discipline), ADR-0009 (multi-implementation parity — declustering must preserve C/Python parity per module).
**Codifies memory:** `[[project_srmech_module_namespace_needs_declustering]]` · `[[project_class_n_precision_contract_migration_breaking_no_legacy]]` · `[[user_stance_breaking_means_fixing]]`.

---

## Context

`srmech.amsc` was named the **A**ttested **M**ulti-**S**ource **C**ollector/**C**atalog — the provenance/MPR framework. It has since accreted **76 top-level modules + 4 subpackages, 8.7 MB** (measured 2026-07-29; this line read "~70" as an estimate) of which — by the classification test below — **only 4 are attestation**, i.e. **95% of what lives in `amsc` is not `amsc`** (Amendment A.2). The accretion: the whole special-functions galaxy (`rational`, `elliptic_*`, `modular_forms_*`, `thetasum`, `riemann_theta`, `zeilberger`/`gosper`, `jacobi`), the carriers (`q`/`mat`/`vec`/`hv`), the 14 A–N primitives (`format`/`cyclic`/`laplacian`/`hdc`/…), the biology domain (`genome`/`plasmid`/`q8`), and the composition catalogs (`_research/{class,cascade}_catalog/`). The namespace no longer reads as its own map, and `import srmech.amsc.rational` misdescribes what `rational` is. The pressure is real and recurring — rc317 had to move `relative_writhe` out of `srmech.biology.genome` to dodge the wire-format ratchet; that was the first small instance of this ADR.

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

**MACHINE SOURCE OF TRUTH for what is outstanding (rc381, `#T1052`).** The set of ADR-0010 destination
namespaces that have NOT yet landed is `_ADR0010_NEW_NAMESPACES` in
`python/tests/test_rosetta_roots_single_source_rc361.py`. It is pinned against the fixed full
destination set (the union-pin ratchet, same file), so a name may move NEW → EXISTING but can never
silently disappear, and `len(_ADR0010_NEW_NAMESPACES)` is the tamper-proof **"arc-complete when 0"**
oracle. As of **v0.9.0rc381** — the physics slice, which relocated the whole `qm` subpackage to
`srmech.physics.qm` (the LAST DOMAIN to land) — that set holds exactly one name: **`srmech.external`**
(the structure home). When it drains to zero, ADR-0010 execution is complete. Prose here may lag; that
constant does not.

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
methods (`_live_ops()` skips classes, `tests/test_rosetta_completeness.py:1063-1068`; 839 live ops
measured at rc452, zero `ToolSchema` entries), so it is not merely exempt from C-parity but **unclassifiable by the only
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

   ✅ **DONE — v0.9.0rc361 (`#T1034`).** `tests/test_op_name_set_witness_rc361.py` + the
   hand-committed manifest `tests/registered_op_names.txt`.
2. **Single-source the rosetta `_ROOTS`** — collapse the four duplicated copies to one definition,
   so the rename updates one place instead of four. (Widening it to the new namespaces cannot precede
   their existence; de-duplicating it can.)

   ✅ **DONE — v0.9.0rc361 (`#T1034`).** `tests/rosetta_roots.py` — the one definition; the four
   copies now import it. Its gap-assertion peer is
   `tests/test_rosetta_roots_single_source_rc361.py`.
3. **A decode-aware prefix check** over `srmech_carrier_registry.c` + `srmech_class_registry.c` +
   `srmech_tool_registry.c`, per A.3's table.

   ✅ **DONE — v0.9.0rc361 (`#T1034`).** `tests/test_namespace_prefix_decode_aware_rc361.py`.

   *(v0.9.0rc415, `#T1098`: items 1–3 all landed at rc361 and carried NO completion marker while
   item 5 carried one, so the convention existed and was unevenly applied — an ADR reader could
   not tell a done prerequisite from an outstanding one. The markers above are the remedy; nothing
   in items 1–3 is retracted.)*
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
`op = "srmech.biology.genome.chromosome"` still names an op whose module has not moved. All 40 decoded
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

### C.4 ⚠️ CORRECTION (rc367) — the module-move instrument set is THREE, not two, and rc366's first commit missed the third

C.2 and C.3 named the **census** and the **op-name-set witness** as the instruments a module move trips.
That is **incomplete**. There is a THIRD: the **decode-aware `srmech.amsc.` prefix ratchet**
(`test_namespace_prefix_decode_aware_rc361.py`), and rc366's *move* commit (`6063f25f1`) shipped WITHOUT
re-pinning it — it took a **separate follow-up commit** (`72ca82734`, "record the harmonics drain") to
catch the drain. That gap is the finding, and it must be carried into the bigger-bucket plan:

- **Why it was missed.** rc366's own selection predicate was "files pinning a *ledger/registry-derived
  population*" (the callable-delta set). The census and op-name-set witness both key on the **op/module
  SET**, which a module move visibly changes, so the predicate selected them. The decode-aware ratchet
  keys on **NAMESPACE-MEMBERSHIP** — the count of `srmech.amsc.` *textual + decoded prefix references* in
  the six generated artifacts. A module move adds/removes **no public callable**, so a callable-delta
  predicate does not select it, even though its *reference population* drains by exactly the moved op's
  citations. It is the one instrument in the set whose subject is the dotted-string population rather
  than the op set.
- **The corrected module-move ripple set** (what a `math` / `apokatastasis` slice MUST re-pin, in the
  same commit as the move): **(1)** the census manifest + digest + `LANDED`/conservation; **(2)** the
  op-name-set witness manifest + digest (`EXPECTED_N` holds — a move is not an add/remove); **(3)** the
  decode-aware prefix ratchet — per-file `(as_text, decoded)` pairs for every artifact the move touches,
  plus `TOTAL_AS_TEXT` / `TOTAL_DECODED`, plus the fifth test's hard `amsc` / `music` decoded pins IF the
  move touches the carrier registry's byte arrays (a *carrier* op does; a non-carrier op does not).
  Instruments (1) and (2) go red on the SET; instrument (3) goes red on the POPULATION and is the one a
  callable-delta sweep will walk straight past.

## Amendment D — the SECOND module-moving slice, `naming` → `srmech.introspect`, v0.9.0rc367 (`#T1034`)

rc366 moved `harmonics` (2 pure-compute ops) to `srmech.music`. rc367 moves **`srmech/amsc/naming.py` →
`srmech/introspect/naming.py`** — the Class-E catalog primitive (`lookup` binary-search + `reverse_order`
harmonic-2 chiral mirror), an A.2 `srmech.introspect | 10` member (one of the six the map names). Leaf
name `naming` kept (B.1 rule 1); `srmech.introspect` already existed and is already a rosetta root, so
this is a drop-in. It is the arc's **first `c_dispatched` module move** and its **first C-side
entanglement** — both are departures from the harmonics analog, and both are the data the bigger buckets
need.

### D.1 Two departures from the harmonics analog — say them plainly, they are planning inputs

1. **A hand-authored C-source entanglement (harmonics had NONE).** `naming.lookup` is in the MCP
   `tools/call` DISPATCH SPINE — `c/src/srmech_invoke.c`, which is **hand-authored**, hardcodes the
   dotted tool name `"srmech.amsc.naming.lookup"` in a `strcmp` shape-guard AND in the shape-vtable row
   (`iv_shape_naming_lookup`). Both were repointed to `srmech.introspect.naming.lookup` so the C
   dispatch matches the renamed op. This is a **C-source edit a module move can force**, and the
   decode-aware ratchet does NOT cover `srmech_invoke.c` (not in its six generated artifacts), so nothing
   automated flags it — it must be found by grep. **ABI is unchanged** (an internal dispatch string is
   not wire format), and the C **capability** symbols (`srmech_catalog_lookup` / `srmech_reverse_order`)
   are untouched — only the Python-facing dotted routing string moved. Harmonics' `classify_*` ops are
   not in the invoke vtable, so rc366 never saw this. **Any `math` / `apokatastasis` op that is MCP-C-
   invokable (in the `srmech_invoke.c` shape table) carries this same hidden C edit.**
2. **`_c_claims.py` moved — the first module move to touch it (harmonics did not).** `_c_claims.py` is
   the op→C-symbol CLAIM manifest, keyed ONLY for `c_dispatched` ops. `naming`'s two ops ARE
   `c_dispatched`, so their keys repointed amsc→introspect and the decode-aware `_c_claims.py` pin fell
   250→248. Harmonics' ops are compute, so they never appeared there. **A `c_dispatched` module move
   drains one more artifact than a compute one.**

And one thing that did NOT ripple, for the same reason it did for harmonics but inverted: the **decoded
channel stayed FLAT**. `naming` is not a carrier op, so it has no reference in the carrier registry's
hoisted byte arrays. The harmonics drain was `-9 as-text / -4 decoded` (four carrier byte-array refs);
the naming drain is `-6 as-text / 0 decoded`. The fifth decoded-population test (hard `amsc == 529`,
`music == 13`) is untouched. There is also **no `COMPOSES_C_ZERO_REACH_PINNED` entry to repoint** —
harmonics' `classify_harmonic` was a `composes_c`/zero-reach op and moved in that set; `naming`'s ops are
`c_dispatched` (leaves), so they are not in that set at all.

### D.2 The measured ripple — the corrected THREE-instrument set, all re-pinned in the move commit

- **Census** (`test_amsc_module_census_rc365.py` + manifest): `naming` dropped, **74 → 73 modules**;
  digest **`52a34d12…` → `e4f88591…`**; `LANDED` `{harmonics}` → **`{harmonics, naming}`**; conservation
  **`73 + 2 == 75`** holds.
- **Op-name-set witness** (`test_op_name_set_witness_rc361.py` + manifest): the SET moves two names
  amsc→introspect; digest **`812dc897…` → `eef53539…`**; `EXPECTED_N` **stays 525** (a move, not an
  add/remove).
- **Decode-aware prefix ratchet** (`test_namespace_prefix_decode_aware_rc361.py`) — the instrument
  rc366's first commit missed (C.4): `srmech_tool_registry.c` **(1221, 4) → (1219, 4)**;
  `_tool_docs.py` **(1202, 0) → (1200, 0)**; `_c_claims.py` **(250, 0) → (248, 0)**; carrier / class /
  responsion registries **unchanged**; **`TOTAL_AS_TEXT` 2948 → 2942** (−6 = the two ToolEntry `name=`
  citations × the three doc-carrying artifacts), **`TOTAL_DECODED` 573 → 573** (flat).
- **Rosetta ledger** (`rosetta_classification.ndjson`): two rows repoint `exposed_as` + `defined_at`
  amsc→introspect; **bucket stays `c_dispatched`**; both ops stay rosetta-visible (the walk finds
  `srmech.introspect.naming.{lookup,reverse_order}` under the `srmech.introspect` root, whose `__all__`
  exposes them with `__module__ == srmech.introspect.naming`), and the C symbols they claim are unchanged.
- **Regenerated artifacts** (`tools/regen_all.py`, content-equality + idempotent): `_tool_docs.py`,
  `_c_claims.py`, `srmech_tool_registry.c` (the three that carry naming's dotted name); the other three
  generated outputs unchanged.
- **Source + curated citations**: 2 ToolEntry `name=` (`tool_schema.py`); the moved module's own
  `from . import _native` → `from ..amsc import _native`; two source docstrings (`_handles.py`,
  `compose.py`); the curated docs for `naming`'s 2 ops plus 5 SIBLING ops
  (`dispatch.match` / `dispatch.mirror_pattern` / `search.byte_search` / `search.byte_search_backward` /
  `music.harmonics.classify_harmonic`) whose `srmech/amsc/naming.py:NN` slash-citation repointed; the
  rosetta build note (`notes/_rosetta_build_classification.py`).
- **Consuming tests**: three multi-import splits (`test_def_parity`, `test_chiral_EL_c_parity`,
  `test_harmonics` — `naming` pulled out of `from srmech.amsc import …` into `from srmech.introspect
  import naming`); two invoke-name repoints (`test_mcp`, `test_invoke_tool_clean_batch2_c_rc189`).

### D.3 The prose op-ref gate again did NOT fire — same reason as C.2

As with harmonics, `naming`'s only dotted `srmech.amsc.naming.*` strings were the ToolEntry `name=`
fields (not scanned) and its cross-citations are **slash-form** `srmech/amsc/naming.py:NN` (excluded as
filenames). So the prose op-ref gate stayed green through a real move a second time — the census + the
op-name-set witness + the decode-aware ratchet are what caught it. The `math` / `apokatastasis` buckets
are still the ones expected to carry genuine dotted cross-citations that WILL trip the prose gate; the
two module moves so far are both "slash-form-cited" modules, which is why that gate has yet to fire on a
move.

## Amendment E — the THIRD module-moving slice, `responsion_schema` → `srmech.introspect`, v0.9.0rc368 (`#T1034`)

rc367 moved `naming` (2 ops, `c_dispatched`) and its planning-input headline was "the first C-side
entanglement". rc368 moves **`srmech/amsc/responsion_schema.py` → `srmech/introspect/responsion_schema.py`**
— the RESPONSION (stored-relationship) introspection surface, the k=3 EDGE face binding `tool_schema`
(verbs) and `carrier_schema` (nouns), an A.2 `srmech.introspect | 10` member the census's
`NAMED_DEPARTURES` already named. Leaf name `responsion_schema` kept (B.1 rule 1); `srmech.introspect`
already existed and is already a rosetta root, so it is a drop-in. Op name:
`srmech.amsc.responsion_schema.responsion_schema` → `srmech.introspect.responsion_schema.responsion_schema`.
It is the arc's **first `composes_c` (C-reaching but not `c_dispatched`) module move** and its **first
move to touch the `responsion_registry` decode pin** — both departures from the naming analog, and both
the data the bigger buckets need.

### E.1 The "no C entanglement for a non-`c_dispatched` op" prediction HELD — the inverse of rc367

The build brief predicted, and grep confirmed both before and after the move, that the dotted name does
**not** appear in the hand-authored MCP dispatch spine `c/src/srmech_invoke.c` (zero `responsion` hits
in that file). So, UNLIKE `naming.lookup` (which was hardcoded in a `strcmp` shape-guard AND the
shape-vtable row and needed the amsc→introspect repoint), **`responsion_schema` needed no C
dispatch-string edit**. The reason is its bucket: the op is `non_compute`/`composes_c` — it has C REACH
(it dispatches to the `srmech_responsion_schema` assembler over the compiled-in `srmech_responsion_registry`
const table) but it is **not a `c_dispatched` leaf**, and the MCP `tools/call` vtable routes only the
`c_dispatched` leaves. Two consequences follow, both the mirror image of rc367:

1. **`_c_claims.py` stayed FLAT at (248, 0).** That manifest is keyed only for `c_dispatched` ops, so
   `responsion_schema` never had a key in it. A `c_dispatched` move (naming) drained it 250→248; a
   `composes_c` move does not touch it at all.
2. **No `COMPOSES_C_ZERO_REACH_PINNED` entry to repoint — but for the OPPOSITE reason to naming.** naming
   had none because its ops are `c_dispatched` leaves (not `composes_c`). `responsion_schema` IS
   `composes_c`, so one might expect a zero-reach pin — but it is a `composes_c` op **WITH** C reach (its
   AST walk reaches the `srmech_responsion_schema` dispatch), so it was never in the zero-reach set. The
   rosetta bucket is preserved exactly (`non_compute`/`composes_c`) across the move.

The C **capability** symbol `srmech_responsion_schema` and the `srmech_responsion_registry_table` are
untouched — C symbol names are independent of the Python module path. **Confirmed prediction, stated as a
planning input:** a `composes_c`/C-reaching op with no `c_dispatched` vtable entry moves with NO C dispatch
edit; only its generator + hand-written source-of-truth comments (E.2) follow the Python path.

### E.2 A NEW data point — the first module move to move the `responsion_registry` decode pin

Through harmonics (rc366) and naming (rc367) the decode-aware ratchet's `srmech_responsion_registry.c` row
was a documented CONTROL: "no byte arrays, decoded 0 is a real zero", and untouched by either move. This
slice touches it, because `responsion_schema` **is** the responsion-registry's own schema. Its generator
`c/tools/gen_responsion_registry.py` (a) imports `_pure_responsion_schema` from the module — a LIVE import
that would `ImportError` in `regen_all` if left unrepointed — and (b) emits a `Source of truth:` comment
naming the module path. Both repointed amsc→introspect, so the generated `srmech_responsion_registry.c`
fell **as-text 72 → 71** (decoded stays 0). The 71 residual are the edge-OPERATOR names
(`zeilberger` / `dispatch` / `coupling` / `laplacian` / `cascade` / …), whose modules did **not** move — a
rename of the schema op leaves every `(operator, carrier)` edge intact.

⚠️ **The build brief's "no C source change except the version bump" was WRONG, and this is the general
planning input the bigger buckets need.** What held was the narrower, correct prediction — **no C
DISPATCH entanglement** (`srmech_invoke.c` clean; E.1). But `responsion_schema` has a **dedicated C peer
translation unit** (`srmech_responsion_schema.c`) and a **dedicated generated data table**
(`srmech_responsion_registry.c` + its generator), so its dotted Python path is cited across **FIVE** C
surfaces, every one of which needed the amsc→introspect repoint:

| # | C surface | Kind | How repointed |
|---|-----------|------|---------------|
| 1 | `c/include/srmech.h` | hand-authored doc comment | direct edit (NOT ratcheted; a stale string here passes the pedantic build and ships silently) |
| 2 | `c/src/srmech_responsion_registry.c` | GENERATED data table | via the generator (#5) + `regen_all` |
| 3 | `c/src/srmech_responsion_schema.c` | hand-authored C peer, doc comment (`json.dumps(…_pure_responsion_schema()…)` ~line 13) | direct edit |
| 4 | `c/src/srmech_tool_registry.c` | GENERATED tool table | via `regen_all` |
| 5 | `c/tools/gen_responsion_registry.py` | the GENERATOR that emits #2 (live import + emitted comment) | direct edit of the SOURCE |

Two of the five (#2, #4) are regenerated; three (#1, #3, #5) are hand-edited SOURCE. **The dangerous class
is #1 / #3: a stale dotted name in a C COMMENT does not fail `-Wpedantic -Werror` and is not covered by
the decode-aware ratchet, so it would ship as a silent stale citation in the C distribution.** The only
guard is a grep — verified ZERO `srmech.amsc.responsion_schema` remain anywhere under `docs/srmech/c/`
after the edits + regen. **Every module has a `srmech_<module>.c` peer** (and many have a dedicated
generated table + generator), so the `math` / `apokatastasis` buckets will hit this same 3-to-5-surface C
citation fan-out repeatedly — the module-move checklist must include `git grep srmech.amsc.<module> --
docs/srmech/c/` and a post-regen zero-grep, not only the `srmech_invoke.c` dispatch check.

### E.3 The measured ripple — the THREE-instrument set, all re-pinned in the move commit (per C.4)

- **Census** (`test_amsc_module_census_rc365.py` + manifest): `responsion_schema` dropped, **73 → 72
  modules**; digest **`e4f88591…` → `36c987f0…`**; `LANDED` `{harmonics, naming}` →
  **`{harmonics, naming, responsion_schema}`**; conservation **`72 + 3 == 75`** holds. `NAMED_DEPARTURES
  ["srmech.introspect"]` already listed `responsion_schema`, so the A.2 move map needed no edit.
- **Op-name-set witness** (`test_op_name_set_witness_rc361.py` + manifest): the SET moves ONE name
  amsc→introspect; digest **`eef53539…` → `91ce6e78…`**; `EXPECTED_N` **stays 525**.
- **Decode-aware prefix ratchet** (`test_namespace_prefix_decode_aware_rc361.py`):
  `srmech_tool_registry.c` **(1219, 4) → (1216, 4)**; `_tool_docs.py` **(1200, 0) → (1197, 0)**;
  `srmech_responsion_registry.c` **(72, 0) → (71, 0)** (the new data point); `_c_claims.py` **(248, 0)**
  unchanged; carrier / class registries **unchanged**; **`TOTAL_AS_TEXT` 2942 → 2935** (−7),
  **`TOTAL_DECODED` 573 → 573** (flat); the fifth decoded-population test (`amsc == 529`, `music == 13`)
  untouched. The −3 on each of the two doc-carrying artifacts is the responsion `name=` citation + its
  worked-example import + the `carrier_schema` SIBLINGS-prose ref that named it by dotted path — all
  amsc→introspect; the −1 on the responsion registry is the source-of-truth comment (E.2).
- **Rosetta ledger** (`rosetta_classification.ndjson`): ONE row repoints `exposed_as` + `defined_at`
  amsc→introspect; **bucket stays `non_compute`/`composes_c`**; the op stays rosetta-visible under the
  `srmech.introspect` root and the C reach it composes over is unchanged.
- **Regenerated artifacts** (`tools/regen_all.py --accept-seed-drift`, content-equality + idempotent):
  `_tool_docs.py`, `srmech_tool_registry.c`, `srmech_responsion_registry.c` (the three that carry the
  dotted name); `_c_claims.py` + carrier + class registries verified byte-identical. One worked-example
  ledger row regenerated (`--only-stale`, now `ok` under the introspect import).
- **Source + curated citations**: 1 ToolEntry `name=` (`tool_schema.py`); the moved module's five lazy
  `from .<amsc-sibling>` imports → `from ..amsc.<sibling>` and its own docstring self-path; the curated
  docs for `responsion_schema`'s own entry plus the `carrier_schema` sibling entry whose dotted + slash
  citations repointed; `_native.py`'s source-of-truth comment; the generator + two hand-written C
  comments (E.2).
- **Consuming tests**: three live-import repoints (`test_responsion_schema_rc225`,
  `test_responsion_curvature_rc237`, `test_an_elliptic_jackson_rc227`). The annex / non-compute ratchet
  narrative comments naming the old path are **frozen historical records** (rc366/rc367 precedent) and were
  left; the edge KEYS in `test_responsion_schema_rc225` (`srmech.amsc.laplacian.responsion|Mat`, …) name
  NON-moving operator modules and were correctly NOT touched.

### E.4 The prose op-ref gate again did NOT fire — same reason as C.2 / D.3, third time

`responsion_schema`'s only dotted `srmech.amsc.responsion_schema.*` strings are the ToolEntry `name=` field
(not scanned) and its cross-citations are **slash-form** `srmech/amsc/responsion_schema.py:392` (excluded
as filenames). So the prose op-ref gate stayed green through a real move a third consecutive time — census
+ op-name-set witness + decode-aware ratchet are what caught it. All three module moves to date
(harmonics, naming, responsion_schema) are "slash-form-cited" modules; the `math` / `apokatastasis`
buckets remain the ones expected to carry genuine dotted cross-citations that WILL finally trip the prose
gate.

## Amendment F — the FOURTH module-moving slice, `op_provenance` → `srmech.introspect`, v0.9.0rc369 (`#T1034`)

rc368 moved `responsion_schema` (1 op, `composes_c`) and its headline was "the first `composes_c` move —
`_c_claims.py` stayed flat". rc369 moves **`srmech/amsc/op_provenance.py` →
`srmech/introspect/op_provenance.py`** — the OPERATOR⊗OPERAND-as-one-addressable-object surface (`carry`
the record, `op_provenance_hash` the Class-A canonical hasher, `op_verdict` / `family_verdict` the
one-sided EQUAL/UNKNOWN verdicts, `reproject` the re-verify, `lossy_projection_record`) — an A.2
`srmech.introspect | 10` member the census's `NAMED_DEPARTURES` already named. Leaf name `op_provenance`
kept (B.1 rule 1); `srmech.introspect` already existed and is already a rosetta root, so it is a drop-in.
The SIX `srmech.amsc.op_provenance.*` op names → `srmech.introspect.op_provenance.*`. It is the arc's
**first move with a MIXED rosetta bucket set** (five `composes_c` ops + one `c_dispatched` op in the same
module) and the **largest single doc move so far** (6 ops × the name+worked-example doc pair).

### F.1 ⚠️ The "NOT c_dispatched" prediction was WRONG for one of the six ops — this slice is rc367-shaped

The build brief predicted "NOT c_dispatched, NOT in invoke.c". The **`invoke.c` half held** (grep-verified
zero `op_provenance` hits in `c/src/srmech_invoke.c`, before and after — so NO MCP dispatch-string edit,
unlike `naming.lookup`). The **`c_dispatched` half did not**: `op_provenance_hash` is a genuine
`c_dispatched` leaf. It has a dedicated C peer `srmech_op_provenance.c` (symbols `srmech_op_provenance_hash`
+ `srmech_op_provenance_hash_arena_bytes`), a real ctypes binding in `_native.py`, the `c_dispatched`
bucket in the rosetta ledger, and therefore ONE key in the op→C-symbol claim manifest `_c_claims.py`.
Consequence, the mirror of rc368 and a return to the rc367 shape:

1. **`_c_claims.py` DRAINED (248 → 247).** The single `srmech.amsc.op_provenance.op_provenance_hash` key
   repointed amsc→introspect. A `c_dispatched` move drains this manifest (naming: 250→248; op_provenance:
   248→247); `responsion_schema`'s `composes_c` move left it flat. The five sibling ops
   (`carry` / `op_verdict` / `family_verdict` / `reproject` / `lossy_projection_record`) are
   `non_compute`/`composes_c` and never had a `_c_claims.py` key — so the module drains the manifest by
   exactly ONE despite moving six ops.
2. **The C capability symbols are untouched** — C symbol names are independent of the Python module path.
   The rosetta buckets are preserved exactly across the move: `op_provenance_hash` stays `c_dispatched`,
   the other five stay `non_compute`/`composes_c`.

**Planning input:** the `c_dispatched` predicate must be checked PER-OP, not per-module. A module can carry
a mixed bucket set, and the presence of a `srmech_<module>.c` peer is the tell that at least one op is
likely C-backed — check `_c_claims.py` + the `_native.py` ctypes bindings, not only the module name.

### F.2 The C fan-out — THREE surfaces (lighter than `responsion_schema`'s five): a C-cost data point

`op_provenance` has a dedicated C peer translation unit but — unlike a schema module — NO dedicated
generated registry and NO dedicated generator, so its dotted Python path is cited across **THREE** C
surfaces, every one repointed amsc→introspect:

| # | C surface | Kind | How repointed |
|---|-----------|------|---------------|
| 1 | `c/include/srmech.h` | hand-authored doc comment (×2) | direct edit (NOT ratcheted; a stale string here passes the pedantic build and ships silently) |
| 2 | `c/src/srmech_op_provenance.c` | hand-authored C peer, doc + symbol-map comments (×6) | direct edit |
| 3 | `c/src/srmech_tool_registry.c` | GENERATED tool table | via `regen_all` |

Only one (#3) is regenerated; two (#1, #2) are hand-edited SOURCE. **The dangerous class is again #1 / #2:
a stale dotted name in a C COMMENT does not fail `-Wpedantic -Werror` and is not covered by the
decode-aware ratchet.** Guard: `git grep srmech.amsc.op_provenance -- docs/srmech/c/` verified ZERO remain
after the edits + regen. **The C-cost model, now three data points:** a module with a `srmech_<module>.c`
peer but NO `gen_<module>_registry.py` costs **3** C surfaces (op_provenance); a schema module with a peer
+ a dedicated table + generator costs **5** (responsion_schema); a module with neither costs **0–1**
(harmonics/naming's C surfaces were the generated tool registry alone, plus naming's `srmech_invoke.c`
dispatch spine). The `math` / `apokatastasis` buckets are dominated by peer-carrying non-schema modules, so
the **3-surface** cost is the one to budget by default.

### F.3 The measured ripple — the THREE-instrument set, all re-pinned in the move commit (per C.4)

- **Census** (`test_amsc_module_census_rc365.py` + manifest): `op_provenance` dropped, **72 → 71
  modules**; digest **`36c987f0…` → `ae010cc1…`**; `LANDED` `{harmonics, naming, responsion_schema}` →
  **`{harmonics, naming, responsion_schema, op_provenance}`**; conservation **`71 + 4 == 75`** holds.
  `NAMED_DEPARTURES["srmech.introspect"]` already listed `op_provenance`, so the A.2 move map needed no
  edit.
- **Op-name-set witness** (`test_op_name_set_witness_rc361.py` + manifest): the SET moves SIX names
  amsc→introspect; digest **`91ce6e78…` → `79f1ddfc…`**; `EXPECTED_N` **stays 525**.
- **Decode-aware prefix ratchet** (`test_namespace_prefix_decode_aware_rc361.py`):
  `srmech_tool_registry.c` **(1216, 4) → (1202, 4)**; `_tool_docs.py` **(1197, 0) → (1183, 0)**;
  `_c_claims.py` **(248, 0) → (247, 0)** (the `c_dispatched` drain, F.1); carrier / class / responsion
  registries **unchanged**; **`TOTAL_AS_TEXT` 2935 → 2906** (−29), **`TOTAL_DECODED` 573 → 573** (flat);
  the fifth decoded-population test (`amsc == 529`, `music == 13`) untouched. The −14 on each of the two
  doc-carrying artifacts is the 6 `name=` citations + their worked-example imports + the sibling-prose
  refs (`format.sha256_bytes`, `genome.telomere_tick`, `gene_express`, and the four op_provenance
  cross-references), all amsc→introspect.
- **Rosetta ledger** (`rosetta_classification.ndjson`): SIX rows repoint `exposed_as` + `defined_at`
  amsc→introspect; buckets preserved (`op_provenance_hash` stays `c_dispatched`, the five siblings stay
  `non_compute`/`composes_c`); all six stay rosetta-visible under the `srmech.introspect` root.
- **Regenerated artifacts** (`tools/regen_all.py --accept-seed-drift`, content-equality + idempotent):
  `_tool_docs.py`, `_c_claims.py`, `srmech_tool_registry.c` (the three that carry the dotted name);
  carrier + class + responsion registries verified byte-identical. The worked-example ledger regenerated,
  now `ok` under the introspect imports. (The seed-drift accept was required because the moved module's
  own docstring self-path and the curated sibling refs are docstring/curation seeds that legitimately
  changed — the drift set was exactly the 8 op_provenance-related tools, nothing else.)
- **Source + curated citations**: 6 ToolEntry `name=` (`tool_schema.py`); `coupling.py`'s lazy
  `from . import op_provenance` → `from ..introspect import op_provenance` (a consumer that STAYS in amsc
  and now reaches UP to introspect — the first cross-namespace consumer repoint of the arc); the moved
  module's 15 lazy `from .<amsc-sibling>` imports → `from ..amsc.<sibling>` (`format`, `_native` ×7,
  `laplacian` ×4, `coupling`, `rational` ×2) and its own docstring self-path; the curated docs for the 6
  op_provenance entries + the `format.sha256_bytes` sibling entry; `_native.py`'s two source-of-truth
  comments; `genome.py`'s six sibling-pattern `:func:` refs; the two hand-written C comments (F.2).
- **Consuming tests**: six live-import / prose repoints (`test_op_provenance_rc117`,
  `test_op_provenance_c_rc171`, `test_recoverable_fold_rc125`, `test_fractions_to_q_rc263`,
  `test_declared_type_honesty_rc363`, `test_rosetta_completeness`). Historical CHANGELOG / spike-note refs
  to the old path are **frozen records** (rc366/rc367/rc368 precedent) and were left.

### F.4 A NEW ripple class — the first cross-namespace CONSUMER repoint

Every prior slice moved a module whose amsc-sibling dependencies moved WITH it or were only cited in prose.
op_provenance is the first to expose a **live consumer that stays behind**: `srmech/biology/coupling.py`
(`RecoverableFold.identity`) lazily imports `op_provenance` to compute its chain hash. Its relative
`from . import op_provenance` (which resolved to the amsc sibling) had to become
`from ..introspect import op_provenance` — an amsc module now reaching UP into `srmech.introspect`. This is
the inverse of the moved module's OWN import fixups (which reach DOWN from introspect back into amsc for
`format` / `_native` / `laplacian` / …). **Planning input:** a module-move must grep for BOTH directions —
the moved module's imports of its old siblings, AND its old siblings' imports of it — because a stale
relative import in a STAYING consumer is a runtime `ImportError`, not a silent comment. Verified: the
`coupling → op_provenance` lazy import re-derives the shipped gasket-fold address `f8a09890b9e8…` unchanged
after the move.

## Amendment G — the FIFTH module-moving slice, and the FIRST into a newly-created DOMAIN namespace: `elliptic_partial_fraction` → `srmech.apokatastasis`, v0.9.0rc370 (`#T1034`)

rc366–rc369 all moved modules into namespaces that ALREADY EXISTED (`srmech.music` created at rc362,
`srmech.introspect` a long-standing root). rc370 moves **`srmech/amsc/elliptic_partial_fraction.py` →
`srmech/apokatastasis/elliptic_partial_fraction.py`** — the elliptic partial-fraction expansion (Rosengren
Eq. 1.22, the reduction ENGINE of the multivariable Cₙ elliptic reduction row), a single `c_dispatched` op —
and in doing so **CREATES `srmech.apokatastasis`**, A.2's LARGEST destination (**31 modules, 41 %**: the
elliptic / modular / theta / q-series domain). It is therefore the arc's **first DOMAIN-with-a-registered-op
move** and the template for the remaining 30 members of that bucket. Leaf name `elliptic_partial_fraction`
kept (B.1 rule 1). `describe()["tools"]["total"]` stays **525**; `SRMECH_ABI_VERSION` stays **10**.

The contrast that makes it a distinct milestone: rc364 (`srmech.cascade`) ALSO created a namespace, but that
one carried only TOML descriptors and **zero callables** — a structure-only slice that added zero ledger
rows. rc370 is the first created namespace to arrive **carrying a walked op**, so it exercises every
new-namespace wiring path a structure slice does not.

### G.1 The NEW-NAMESPACE SETUP — three steps beyond a drop-in slice (the template)

A drop-in move into an existing namespace (rc366–rc369) is: move the file, repoint the citations, re-pin the
three instruments. Creating the namespace adds THREE steps, and every remaining slice into a not-yet-created
namespace (`math` 22, `physics`, `biology` 4, `external`) follows them:

1. **Create the package `__init__.py`.** `srmech/apokatastasis/__init__.py` = a domain docstring +
   `__all__ = []`. The op is NOT re-exported at package level — it lives in its submodule
   (`srmech.apokatastasis.elliptic_partial_fraction`) and the Rosetta walk discovers it via
   `pkgutil.walk_packages` reading the SUBMODULE's own `__all__` (the same shape `srmech.music` uses for its
   `harmonics` sibling). The moved module's lazy sibling imports become up-reaches: `from .ellbase` /
   `from .thetasum` / `from . import _native` → `from ..amsc.<sibling>` (the rc369 pattern).
2. **Append the Rosetta walk root** — `srmech.apokatastasis` added to `tests/rosetta_roots.py` AND
   `_EXPECTED_ROOTS` (the two-file edit music/cascade established), plus migrate it NEW→EXISTING in
   `test_rosetta_roots_single_source_rc361.py`'s `_ADR0010_*` tuples.
3. **Name the subset in the census move-map** — `NAMED_DEPARTURES["srmech.apokatastasis"] =
   {"elliptic_partial_fraction"}`, a SUBSET-named bucket (1 of 31, like `srmech.introspect`), with the
   `len(named) <= A.2 count` assertion added. `LANDED <= a2_named` REQUIRES the module be named here before
   it can be recorded landed.

### G.2 ⚠️ The "root already listed — no edit expected" prediction was WRONG

The build brief stated `srmech.apokatastasis` was already in the Rosetta roots tuple and only needed
VERIFYING. It was NOT: line 109 of `test_rosetta_roots_single_source_rc361.py` had it in
`_ADR0010_NEW_NAMESPACES` — the "does-not-exist-yet" list — NOT in `ROSETTA_ROOTS` / `_EXPECTED_ROOTS`. This
is not a nit: a module moving into a namespace makes the package EXIST, and if the root is not added in the
SAME rc, `pkgutil.walk_packages` never reaches the op, `rosetta_live_objects()` drops it, and the ledger
fires its STALE assertion (a classified row whose live op vanished) — the signature of a DELETION, not a
move (the exact hazard `tests/rosetta_roots.py` was single-sourced to prevent). The correct action was the
full music/cascade two-file root edit + NEW→EXISTING migration, done in the move commit. A knock-on: the
`test_a_root_naming_a_nonexistent_package_is_silently_skipped` witness used `srmech.apokatastasis` as its
"nonexistent package" example — now real — so it was switched to `srmech.external` (still in
`_ADR0010_NEW_NAMESPACES`). **Planning input for the remaining new-namespace slices: the root is NEVER
pre-added (rc361's rule), so EVERY first-into-a-namespace slice pays the two-file root edit — treat it as
mandatory setup, not a verify.**

### G.3 The op IS `c_dispatched` (rc367/rc369 shape) + the C fan-out is FOUR surfaces

`elliptic_partial_fraction` is a `c_dispatched` leaf: dedicated C peer `srmech_elliptic_partial_fraction.c`
(symbols `srmech_elliptic_partial_fraction` + `srmech_elliptic_partial_fraction_ws_bound`), a real ctypes
binding, a `c_dispatched` rosetta bucket, one `_c_claims.py` key (repointed amsc→apokatastasis, draining that
pin **247 → 246**). It is **not** in `c/src/srmech_invoke.c` (grep-verified) → no MCP dispatch repoint
(confirming the rc369 lesson that `c_dispatched` and `invoke.c` presence are independent). The dotted path is
cited across **FOUR** C surfaces, all repointed amsc→apokatastasis:

| # | C surface | Kind | How repointed |
|---|-----------|------|---------------|
| 1 | `c/include/srmech.h` | hand-authored doc comment (×1) | direct edit (NOT ratcheted) |
| 2 | `c/src/srmech_elliptic_partial_fraction.c` | hand-authored C peer, doc comment (×1) | direct edit |
| 3 | `c/src/srmech_tool_registry.c` | GENERATED tool table | via `regen_all` |
| 4 | `c/src/srmech_carrier_registry.c` | GENERATED carrier table | via `regen_all` |

This is the **first C-fan-out to include the CARRIER registry (#4)**: `elliptic_partial_fraction` is a carrier
op (named in the `EllMonomial` `consumes` + `ThetaSum` `produces` back-indexes). So the C-cost model gains a
fourth shape — a peer-carrying CARRIER op costs **4** surfaces (peer comment + `srmech.h` + tool registry +
carrier registry). The `apokatastasis` bucket is dominated by carrier ops over the theta algebra, so **4** is
the cost to budget for that bucket by default (vs. 3 for a plain peer-carrying op, 5 for a schema module).

### G.4 The measured ripple — the THREE-instrument set, all re-pinned in the move commit (per C.4)

- **Census**: `elliptic_partial_fraction` dropped, **71 → 70 modules**; digest **`ae010cc1…` →
  `e801322a…`**; `LANDED` gains `elliptic_partial_fraction` (now 5 members); conservation **`70 + 5 == 75`**
  holds; `NAMED_DEPARTURES` gains the `srmech.apokatastasis` subset key + its `<=` assertion.
- **Op-name-set witness**: SET moves ONE name amsc→apokatastasis; digest **`79f1ddfc…` → `02698ab9…`**;
  `EXPECTED_N` **stays 525**. (The name re-sorts from the `amsc.*` block into the `apokatastasis.*` block —
  `registered_op_names.txt` regenerated.)
- **Decode-aware prefix ratchet**: `srmech_carrier_registry.c` **(203, 529) → (201, 529)**;
  `srmech_tool_registry.c` **(1202, 4) → (1201, 4)**; `_tool_docs.py` **(1183, 0) → (1182, 0)**;
  `_c_claims.py` **(247, 0) → (246, 0)**; class / responsion registries **unchanged**; **`TOTAL_AS_TEXT`
  2906 → 2901** (−5), **`TOTAL_DECODED` 573 → 573** (FLAT); the fifth decoded-population test
  (`amsc == 529`, `music == 13`) **untouched**.
  - **⚠️ Finding — a carrier op that does NOT move the decoded (population) channel.** rc366 harmonics was a
    carrier op and its refs lived in the hoisted >4000-byte byte arrays (`cs_lstr_0..3`, the decoded
    channel), so it dropped decoded 533→529. `elliptic_partial_fraction` is ALSO a carrier op, but the
    `EllMonomial` / `ThetaSum` carrier JSON is small enough to sit as an INLINE string literal (the as-text
    channel), NOT in the hoisted arrays — so it drops **2 as-text and 0 decoded** on the carrier registry.
    "Carrier op" therefore does NOT imply "moves the decoded channel"; the discriminator is whether the
    carrier's JSON exceeds the generator's hoist threshold. This is why the fifth-test hard pins are
    unchanged despite this being a carrier move.
- **Rosetta ledger** (`rosetta_classification.ndjson`): 1 row repoints `exposed_as` + `defined_at`
  amsc→apokatastasis; bucket stays `c_dispatched`; the op stays rosetta-visible under the NEW
  `srmech.apokatastasis` root (which is why G.2's root append is load-bearing).
- **Regenerated artifacts** (`tools/regen_all.py --accept-seed-drift`, content-equality + idempotent):
  `_tool_docs.py`, `_c_claims.py`, `srmech_tool_registry.c`, `srmech_carrier_registry.c`; responsion + class
  registries verified byte-identical. (The seed-drift accept was required because the moved module's docstring
  self-path and the curated slash-form sibling refs are curation seeds that legitimately changed — the drift
  set was exactly the 4 elliptic-row tools whose curated text names `elliptic_partial_fraction`.)
- **Source + curated citations**: 1 ToolEntry `name=`; the moved module's own docstring self-path + its 4
  lazy sibling imports (`ellbase` ×2 / `thetasum` / `_native`); the curated docs for `elliptic_partial_
  fraction`'s own entry (dotted key + slash self-ref) + the slash SIBLINGS refs in the three neighbouring
  entries (`elliptic_cauchy_determinant`, `cn_vwp_multisum_lhs`, `an_vwp_multisum_lhs`); `_native.py`'s four
  source-of-truth comments; `elliptic_jackson.py`'s docstring `:func:` ref; the two hand-written C comments
  (G.3). Verified ZERO `srmech.amsc.elliptic_partial_fraction` remain under `docs/srmech/c/` or in
  non-historical Python.
- **Consuming tests**: one live-import repoint (`test_elliptic_partial_fraction_rc95.py`). No
  cross-namespace CONSUMER repoint this slice (unlike rc369's `coupling.py`): nothing outside the module and
  its own test imports the function (grep-verified), so G.2's "grep BOTH directions" check came back clean
  on the consumer side.

## Amendment H — the SIXTH slice, and the LARGEST: the WHOLE `srmech.apokatastasis` family drains in ONE rc (24 modules), v0.9.0rc371 (`#T1034`)

rc370 (Amendment G) opened `srmech.apokatastasis` with a single op. rc371 moves the **entire remaining
elliptic / modular / theta / q-series family — 24 modules in one slice** — completing the domain: `apagodu_
zeilberger`, `eisenstein`, `ellbase`, `elliptic_determinant`, `elliptic_gosper`, `elliptic_jackson`,
`elliptic_jackson_an`, `elliptic_recurrence`, `elliptic_wz_certificate`, `elliptic_zeilberger`, `eta_quotient`,
`gosper`, `harmonic_maass`, `modular_forms_ring`, `q_gosper`, `q_wz_certificate`, `q_zeilberger`,
`quasimodular_forms_ring`, `riemann_theta`, `riemann_theta_multisum`, `thetasum`, `unary_theta`,
`wz_certificate`, `zeilberger`. Leaf names kept (B.1 rule 1); `describe()["tools"]["total"]` stays **525**
(27 op names repoint, a move not an add); `SRMECH_ABI_VERSION` stays **10**.

### H.1 The reusable lesson for a FAMILY-scale move: intra-family imports stay RELATIVE

This is the load-bearing rule that a single-module slice never exercised and the pending `srmech.math` bucket
will need. The 24 modules import each other densely. Because they ALL move together into ONE package, a moved
module's `from .thetasum import …` remains a VALID sibling import and MUST NOT be rewritten to `..amsc.`. The
per-import discriminator is exactly **"did the target move too?"**:

- target is IN the roster (moved) → **keep `from .<sibling>`** (measured this slice: **34** kept relative);
- target STAYS in amsc (a keeper/carrier: `poly` / `q` / `qmat` / `qpoly` / `qbipoly` / `tripoly` / `cyclic` /
  `cascade` / `_native`) → repoint `from .<x>` / `from . import <x>` → **`from ..amsc.<x>`** (measured: **88**
  cross-namespace up-reach imports);
- a STAYS-in-amsc file importing a MOVED module → repoint `from .<roster>` → **`from ..apokatastasis.<roster>`**
  (measured: **16** external-consumer repoints — `amsc/__init__.py` ×6 re-exports, `dispatch.py` ×6,
  `carrier_spectrum.py` ×2, `carrier_ladder.py` ×1, `tripoly.py` ×1).

**And a family move must re-examine EARLIER slices that up-reached into the family.** rc370's
`elliptic_partial_fraction` (already in apokatastasis) reached its carriers via `from ..amsc.ellbase` /
`from ..amsc.thetasum`; both move now, so those two up-reach imports were repointed back DOWN to sibling form
`from .ellbase` / `from .thetasum` (its `from ..amsc import _native` stays). Getting the direction right per
import is the single highest-risk part of a family-scale declustering.

### H.2 The FINDING — A.2's `srmech.apokatastasis` count of 31 OVER-counts the real family by ~6

The real special-functions family is **25** modules (rc370's `elliptic_partial_fraction` + these 24). A.2's
decision table (`ADR_A2_DESTINATION_COUNTS["srmech.apokatastasis"]`) counts **31 (41%)**. The ~6 over-count is
A.2 lumping, by name-similarity, modules that are NOT modular-forms:

- **`modular_linalg`** — GF(p) FINITE-FIELD linear algebra (Gaussian elimination / rank / nullspace over
  𝔽_p), a general math primitive that belongs in the future `srmech.math` bucket, NOT the elliptic/modular-forms
  domain. Its name collides with "modular forms" but the mathematics is unrelated. It deliberately STAYS in
  `amsc` this slice and is explicitly EXCLUDED from the roster.
- **~5 general carriers** (the `q` / `poly` / `qmat` / `qpoly` / `qbipoly` / `tripoly` family and kin) that the
  elliptic ops CONSUME but which are domain-neutral carriers → also the `srmech.math` bucket.

**Decision: `ADR_A2_DESTINATION_COUNTS["srmech.apokatastasis"]` is kept UNCHANGED at 31**, and the census stays
SUBSET-named (`NAMED_DEPARTURES["srmech.apokatastasis"]` = the 25-member family, `25 <= 31`). Reassigning the
~6 to `srmech.math` is the **math bucket's** slice, not this one — doing it here would fabricate a
classification the elliptic slice has no authority over, and would also collide with the still-live
carriers/`modular_linalg` that have not moved. The over-count is recorded here as the finding; it resolves
when the math bucket drains and re-homes those ~6 by name.

### H.3 Measured ripple (all re-pinned in the SAME commit as the move)

- **Census**: **70 → 46** modules; digest `e801322a…` → **`8175d999…`**; `LANDED` gains the 24 (5 → **29**);
  conservation **`46 + 29 == 75`** holds; `NAMED_DEPARTURES["srmech.apokatastasis"]` 1 → **25** members.
- **Op-name-set witness**: SET moves 27 names; digest `02698ab9…` → **`f3373b2c…`**; `EXPECTED_N` stays **525**.
- **Decode-aware ratchet**: carrier `(201,529) → (156,516)`; tool_registry `(1201,4) → (1151,4)`; responsion
  `(71,0) → (41,0)`; `_tool_docs` `(1182,0) → (1133,0)`; `_c_claims` `(246,0) → (218,0)`; **`TOTAL_AS_TEXT`
  2901 → 2699** (−202), **`TOTAL_DECODED` 573 → 560** (−13). **The decoded (population) channel FELL for the
  first time on this bucket, by 13** — this family carries `ellbase` / `thetasum`, whose op references live in
  the four hoisted >4000-byte carrier-registry byte arrays (unlike rc370's inline-as-text single op). The fifth
  test's hard pins re-pin `amsc == 529 → 516`, ADD a conserved receiving-side pin `apokatastasis == 13`
  (−13 amsc = +13 apokatastasis), and hold `music == 13`.
- **C surfaces**: **33** C files repointed (30 hand — `srmech.h`, `srmech_ellbase_internal.h`, and 28
  `srmech_<op>.c` peer comment blocks incl. the cross-cutting `srmech_infer.c` / `srmech_elliptic_lagrange.c` /
  `srmech_an_vwp_multisum_lhs.c` / `srmech_cn_vwp_multisum_lhs.c` / `srmech_q_wz_verify.c` / `srmech_wz.c` /
  `srmech_thetasum_interp.c` — plus the 3 regenerated registries). C symbols capability-named, unchanged; ABI
  stays 10. `srmech_invoke.c` grep-clean (no roster refs) → no dispatch-spine repoint. **ZERO**
  `srmech.amsc.<roster>` remain under `docs/srmech/c/`.
- **Rosetta**: 33 ledger rows repointed (`exposed_as` + `defined_at`, buckets preserved); completeness +
  transitive + roots-single-source all green under the `srmech.apokatastasis` root.
- **Regenerated artifacts** (`tools/regen_all.py --accept-seed-drift`, content-equal + idempotent):
  `_tool_docs.py`, `_c_claims.py`, `srmech_tool_registry.c`, `srmech_carrier_registry.c`,
  `srmech_responsion_registry.c`; class registry byte-identical.

## Amendment I — the FIRST `srmech.math` slice, and the SECOND newly-created DOMAIN namespace: the general-algebra roster `octonion` / `kepler` / `modular_linalg`, v0.9.0rc372 (`#T1034`)

rc370–rc371 drained the whole `srmech.apokatastasis` special-functions domain. rc372 opens A.2's
SECOND-largest destination, **`srmech.math`** (**22 modules**: the 14 A–N primitives + the general
carriers + general math), with its **general-ALGEBRA roster** — the three modules whose mathematics is
domain-neutral algebra rather than a special-functions family:
`srmech/amsc/{octonion,kepler,modular_linalg}.py` → `srmech/math/`. Leaf names kept (B.1 rule 1);
`describe()["tools"]["total"]` stays **525** (10 op names repoint, a move not an add);
`SRMECH_ABI_VERSION` stays **10** (the C peer symbols `srmech_oct_*` / `srmech_kepler_*` /
`srmech_equation_of_centre` / `srmech_pin_slot` / `srmech_gf_rref` / `srmech_crt_reconstruct` are
capability-named, unchanged). The 10 ops: `octonion` 3 (`oct_mult` / `oct_conjugate` / `oct_bind`),
`kepler` 3 (`pin_slot` / `kepler_solve` / `equation_of_centre`), `modular_linalg` 4 (`gf_rref` /
`gf_solve` / `gf_nullspace` / `crt_combine`).

**Deferred to the carriers slice (rc374): `carrier_ladder` / `carrier_spectrum` and the general-carrier
row.** This slice is the general-algebra opener only, not the whole 22-module bucket; the carriers land
in their own slice, exactly as H.2 anticipated for the ~5 general-carrier half of the over-count.

### I.1 `modular_linalg` IS the H.2 apokatastasis over-count reassignment, realised

Amendment H.2 recorded that A.2's `srmech.apokatastasis` count of 31 over-counts the real
special-functions family by ~6, and that **`modular_linalg` (GF(p) finite-field linear algebra —
Gaussian elimination / rank / nullspace over 𝔽_p) is a general math primitive whose name only collides
with "modular forms"**, so it belongs in `srmech.math`, NOT the elliptic/modular-forms domain. H.2
deliberately left it in `amsc` and stated the over-count "resolves when the math bucket drains and
re-homes those ~6 by name". This slice does exactly the `modular_linalg` half of that. The ~5
general-carrier half (`q` / `poly` / `qmat` / … kin) resolves at the carriers slice (rc374). The census
records the resolution: `NAMED_DEPARTURES["srmech.math"] = {octonion, kepler, modular_linalg}`
(subset-named, `3 <= 22`), and `ADR_A2_DESTINATION_COUNTS` is unchanged (math 22, apokatastasis 31 —
apokatastasis stays subset-named at `25 <= 31`).

### I.2 The NEW-NAMESPACE SETUP — the same three steps beyond a drop-in (G.1 template, G.2 rule)

Per G.2's load-bearing planning input — **the root is NEVER pre-added, so every first-into-a-namespace
slice pays the two-file root edit** — this slice performed it as mandatory setup, not a verify:

1. **Created `srmech/math/__init__.py`** (domain docstring + `__all__ = []`); the ops live in their
   submodules, discovered by the Rosetta `walk_packages`, not re-exported. The moved modules' relative
   sibling imports up-reached: `kepler.py` `from . import _native` → `from ..amsc import _native`;
   `modular_linalg.py` `from . import _native` + `from .cyclic import …` → `from ..amsc import _native`
   + `from ..amsc.cyclic import …`. `octonion.py` already used absolute `from srmech.amsc import _native`
   / `from srmech.amsc.hv import HV` (both keepers), so it needed no import rewrite — a case the
   single-module rc370 slice did not exercise.
2. **Appended `srmech.math`** to `tests/rosetta_roots.py` AND `_EXPECTED_ROOTS`, and migrated it
   NEW→EXISTING in `test_rosetta_roots_single_source_rc361.py`'s `_ADR0010_*` tuples. The
   nonexistent-package witness rotated off `srmech.external` (rc370's choice, still valid) onto
   `srmech.physics` — a still-absent member of `_ADR0010_NEW_NAMESPACES`, so the witness does not
   calcify on one name as the arc drains.
3. **Named the subset in the census move-map** — `NAMED_DEPARTURES["srmech.math"]` = the 3-member
   roster, with the `len(named) <= A.2 count` assertion (`3 <= 22`).

### I.3 The ⚠️ SEVEN-form sweep, reaffirmed — a move is NOT a dotted-string sweep

rc371 (residual red-fixes) proved a family move touches SEVEN reference forms, not one. This slice swept
all seven for each of the 3 modules, `srmech.amsc.<m>` → `srmech.math.<m>` (and slash `srmech/amsc/<m>`
→ `srmech/math/<m>`), EXCLUDING history (CHANGELOG, this ADR's own history, `.test_durations`) and the
dated fossil research notes (`notes/*.py` / `*.ndjson` scratchpads and dated `*.md` — historical
records, like ADR-history):

- **(a) dotted** `srmech.amsc.<m>` across live source/tests/C — the bulk.
- **(b) filesystem-path** `os.path.join(…,"amsc","<m>.py")` — **N/A this slice** (no source-reader test
  names these 3 modules by path; measured, not assumed).
- **(c) `from srmech.amsc import <m>`** — incl. the multi-module `from srmech.amsc import _native, kepler`
  in `test_kepler_parity.py`, SPLIT (`_native` stays in amsc, `kepler` → `from srmech.math import
  kepler`) — the case a blanket dotted sweep silently misses.
- **(d) relative / lazy imports in KEEPER modules** — `qmat.py`'s two `from . import modular_linalg`
  (a stays-in-amsc consumer of a MOVED module) → `from ..math import modular_linalg` (H.1 rule 3).
- **(e) worked-examples ledger** — re-captured via `tools/run_worked_examples.py --only-stale` AFTER
  regen (the merge source for `.example` is the GENERATED `_tool_docs.py`, so it MUST be regenerated
  first — running the ledger before regen drops the 3 modules' snippets rather than renaming them; the
  ledger stays `native: false`, `n == 439`, the 10 ops' entries renamed amsc→math with fresh
  `src_sha256`).
- **(f) C comments** — `c/include/srmech.h` carried NO dotted ref to these 3 (measured), so only the
  version bump touches it; the sole hand C-comment site is the non-canonically-named peer
  `c/src/srmech_crt_reconstruct.c` (crt_combine's C peer is NOT `srmech_modular_linalg.c`) — exactly
  the "non-canonically-named peer" hazard rc371 flagged. The generated `srmech_tool_registry.c` /
  `srmech_carrier_registry.c` regenerate.
- **(g) notes prose with reproducible commands** — the live canonical `srmech_research_notebook.md`
  (a table cell + a `from srmech.math.octonion import oct_mult` reproducible line) repointed. Dated
  fossil notes deliberately left as historical record.

**c_dispatched fan-out.** 7 of the 10 ops are `c_dispatched` (all 3 octonion, all 3 kepler,
`modular_linalg.gf_rref`), each with one `_c_claims.py` key; `crt_combine` is a `c_dispatched` op reached
through indirection (in `UNVERIFIABLE_CLAIMS`), so it also has a key — 8 `_c_claims.py` keys repoint
amsc→math. `gf_solve` / `gf_nullspace` are `composition_of_c` (no C claim). **NONE of the 10 is in
`c/src/srmech_invoke.c`** (grep-clean — the only `pin_slot` there is `cascade.pin_slot_at_zero`, a
different op) → no MCP dispatch-spine repoint, confirming again that `c_dispatched` and `invoke.c`
presence are independent.

### I.4 Measured ripple (all re-pinned in the SAME commit as the move)

- **Census**: **46 → 43** modules; digest `8175d999…` → **`8f0361ea…`**; `LANDED` gains the 3 (29 →
  **32**); conservation **`43 + 32 == 75`** holds; `NAMED_DEPARTURES["srmech.math"]` = the 3-member
  subset + its `<=` assertion.
- **Op-name-set witness**: SET moves 10 names amsc→math; digest `f3373b2c…` → **`aa6d1f55…`**;
  `EXPECTED_N` stays **525**.
- **Decode-aware ratchet**: `srmech_carrier_registry.c` **(156, 516) → (156, 500)**;
  `srmech_tool_registry.c` **(1151, 4) → (1111, 4)**; `_tool_docs.py` **(1133, 0) → (1093, 0)**;
  `_c_claims.py` **(218, 0) → (210, 0)**; class / responsion registries **unchanged**; **`TOTAL_AS_TEXT`
  2699 → 2611** (−88), **`TOTAL_DECODED` 560 → 544** (−16). **The decoded (population) channel FELL by
  16** — `octonion` is a genome CARRIER op, so its `oct_mult` / `oct_bind` / `oct_conjugate` back-index
  references live in the four hoisted >4000-byte carrier-registry byte arrays (like rc371's
  ellbase/thetasum, unlike rc370's inline single op). The fifth decoded-population test re-pins
  `amsc == 516 → 500`, ADDS a conserved receiving-side pin `math == 16` (−16 amsc = +16 math), and holds
  `apokatastasis == 13` / `music == 13`.
- **C surfaces**: `srmech.h` (version only — no dotted ref), `srmech_crt_reconstruct.c` (1 hand comment)
  + the 2 regenerated registries. ABI stays 10; `srmech_invoke.c` grep-clean. **ZERO**
  `srmech.amsc.{octonion,kepler,modular_linalg}` remain under `docs/srmech/c/` or in non-historical Python.
- **Rosetta**: 10 ledger rows repointed (`exposed_as` + `defined_at`; buckets preserved — 7
  `c_dispatched` + 3 `composition_of_c`); every moved op rosetta-visible under the NEW `srmech.math`
  root (which is why I.2's root append is load-bearing).
- **Regenerated artifacts** (`tools/regen_all.py --accept-seed-drift`, content-equal + idempotent):
  `_tool_docs.py`, `_c_claims.py`, `srmech_tool_registry.c`, `srmech_carrier_registry.c`; responsion +
  class registries byte-identical.
- **Verification** (numpy-absent WSL): 3/3 `import srmech.math.<m>` succeed, 3/3 `srmech.amsc.<m>` raise
  `ModuleNotFoundError`; whole-suite `pytest --co -q` collects **13034** tests with **0 ImportError**
  (the gate that catches lazy/dynamic misses); census / op-name-set / decode-aware / rosetta
  completeness+transitive+roots-single-source / def_parity / the 3 modules' own tests + the worked-example
  execution gate all green; `regen --check` all six artifacts up to date.

## Amendment J — the EIGHTH slice, the A–N PRIMITIVES batch: ten modules → `srmech.math`, the LARGEST fan-out so far, v0.9.0rc373 (`#T1034`)

rc372 (Amendment I) CREATED `srmech.math` and opened it with the general-algebra roster. rc373 drains
the **bulk of the 14 A–N primitives** into it in one slice — the ten modules
`srmech/amsc/{cyclic,dispatch,hdc,laplacian,primes,rational,search,template,tlv,text}.py` →
`srmech/math/`. Leaf names kept (B.1 rule 1); `describe()["tools"]["total"]` stays **525** (166 op names
repoint amsc→math — a move, not an add); `SRMECH_ABI_VERSION` stays **10** (every `srmech_*` C symbol is
capability-named, unchanged). By op fan-out this is the largest slice of the arc: `laplacian` alone
carries ~56 ops and `hdc` ~57, and the sweep touched **~449 files**.

**Deferred to the carriers slice (rc374): the general carriers** (`q` / `poly` / `qmat` / `qi` /
`qalg` / `qprime` / `qbipoly` / `qpoly` / `tripoly` / `complex128` / `mat` / `vec` / `hv` /
`carrier_ladder` / `carrier_spectrum` and kin). This slice is the A–N-primitives batch, NOT the whole
22-module `srmech.math` bucket. The carriers are the natural next unit because so many of them are the
KEEPER modules the primitives up-reach to (a mover importing a carrier is an up-reach today; when the
carriers move, those become intra-`srmech.math` sibling imports).

### J.1 NO new-namespace setup — this is a PURE module-move slice

Unlike Amendment G (opened `srmech.apokatastasis`) and Amendment I (opened `srmech.math`), rc373 creates
NO namespace: `srmech.math` already exists, its `__init__.py` is already written, and its root is already
in `tests/rosetta_roots.py` + `_EXPECTED_ROOTS` (migrated NEW→EXISTING at rc372). So the G.2 root-setup
cost is ZERO here. The only census-side edit is to **EXTEND** `NAMED_DEPARTURES["srmech.math"]` from the
3-member rc372 subset to **13 members** (adding the 10), holding the `len(named) <= 22` assertion
(`13 <= 22`); `ADR_A2_DESTINATION_COUNTS` is unchanged. This is the shape every remaining slice into an
already-open namespace follows.

### J.2 The mixed-import-direction lesson, generalized — `dispatch.py` is the worst case

A module that moves must have each of its relative imports repointed by the DESTINATION of the target,
not by a blanket rule. `dispatch.py` is the sharpest instance in the arc: of its single-dot relative
imports, **9 up-reached to `..amsc`** (`_native`, `q` ×2, `coupling`, `mat`, `cascade.one`, `poly`,
`qbipoly`, `qpoly` — all amsc KEEPERS), **1 stayed intra-batch relative** (`from . import laplacian` —
`laplacian` is ALSO in this batch, so both land as `srmech.math` siblings and `.` stays correct), and its
**14 `from ..apokatastasis import …` imports were byte-unchanged** (already two-level; `..apokatastasis`
resolves to `srmech.apokatastasis` from `srmech.amsc.dispatch` and `srmech.math.dispatch` identically).
The same three-way discrimination governs every mover and every keeper that imports one:

1. **mover imports an amsc KEEPER** → up-reach: `from . import _native` → `from ..amsc import _native`
   (all 10 movers do this for `_native`; `text` also for `_unicode_*`, `hdc` for `format`/`hv`/`mat`/`q`).
2. **mover imports ANOTHER mover (intra-batch)** → stays relative: `primes.py` `from .cyclic import gcd`,
   `rational.py` `from . import cyclic`, `dispatch.py` `from . import laplacian` — all left untouched.
3. **KEEPER imports a mover** → repoint DOWN-and-OVER by the keeper's depth: `amsc/*.py`
   `from . import <m>` / `from .<m> import` → `from ..math…` (`q` / `qmat` / `coupling` / `mat` / `vec` /
   `poly` / `qi` / `qprime` / `complex128` / `plasmid`); `amsc/cascade/*.py` `from ..<m>` →
   `from ...math.<m>` (`cd_register` / `sedenion_register` / `one` / `cascade.__init__`); sibling
   subpackages `from ..amsc[.<m>]` → `from ..math[.<m>]` (`music` / `spectral` / `introspect` /
   `apokatastasis` / `qm` / `signal_processing` / `rbs_lm`). An already-in-`srmech.math` file that
   imported a NEW mover flips the other way: `math/modular_linalg.py` `from ..amsc.cyclic import …` →
   `from .cyclic import …`.

The reusable lesson: a family move is decided per-import by *where does the OTHER end land*, and a
blanket `amsc`→`math` string sweep gets (2) and (3) wrong. The whole-suite `pytest --co -q` (0 ImportError
over 13034 tests) is the catch-all that proves every one of the four families was resolved, because a
lazy/dynamic import a static grep misses still fails collection.

### J.3 The SEVEN-form sweep across ~449 files

Same seven forms as I.3, at 10× the fan-out, EXCLUDING history (CHANGELOG, this ADR's history,
`.test_durations`, dated `notes/*` fossils and `*.bin`/`*.npy` binaries): (a) dotted `srmech.amsc.<m>` —
the bulk; (b) filesystem-`os.path.join` path — N/A (measured); (c) `from srmech.amsc import <m>` —
including the many MIXED multi-name imports (`compose, coupling, hdc, laplacian`; `_native, rational`;
`cyclic, dispatch, search, _native`; …) each SPLIT keepers-stay / movers-repoint; (d) relative/lazy
imports in KEEPERS and sibling subpackages — the four families of J.2; (e) worked-examples ledger
re-captured AFTER regen (native-absent, so `native: false` is preserved); (f) C comments —
`srmech_loopbind.c` / `srmech_pi.c` / `srmech_pi_archimedes.c` hand comments repointed
`srmech/amsc/{hdc,rational}.py` → `srmech/math/…`; `srmech.h` version-only; generated registries
regenerate; (g) live `srmech_research_notebook.md` reproducible commands. **ZERO**
`srmech.amsc.{the 10}` remain under `docs/srmech/c/` or in non-historical Python.

### J.4 Measured ripple (all re-pinned in the SAME commit)

- **Census**: **43 → 33** modules; digest `8f0361ea…` → **`08c5199f…`**; `LANDED` 32 → **42**;
  conservation **`33 + 42 == 75`** holds; `NAMED_DEPARTURES["srmech.math"]` extended to 13 members
  (`13 <= 22`). The non-vacuity injection's example leaver moved `rational` → `poly` (rational left the
  census).
- **Op-name-set witness**: SET moves **166** names amsc→math (`srmech.math.*` 10 → **176**,
  `srmech.amsc.*` → **181**); digest `aa6d1f55…` → **`10224532…`**; `EXPECTED_N` stays **525**. The
  rename simulation — which the dotted sweep had collapsed into an identity — was repointed onto a live
  prefix (`srmech.math.rational` → the absent `srmech.zzzns.rational`) so it still fires.
- **Decode-aware ratchet** (MEASURED post-regen): `srmech_carrier_registry.c` **(156, 500) → (100, 202)**;
  `srmech_tool_registry.c` **(1111, 4) → (577, 0)**; `_tool_docs.py` **(1093, 0) → (562, 0)**;
  `_c_claims.py` **(210, 0) → (91, 0)**; `srmech_responsion_registry.c` **(41, 0) → (6, 0)**; class
  registry **(0, 40) unchanged**; **`TOTAL_AS_TEXT` 2611 → 1336** (−1275), **`TOTAL_DECODED` 544 → 242**
  (−302). The decoded (POPULATION) channel fell hard: carrier-registry decoded `srmech.amsc.` **500 →
  202** while `srmech.math.` rose **16 → 314** (conserved +298 — the hdc/laplacian/cyclic/rational carrier
  back-index refs in the four hoisted byte arrays), plus 4 tool-registry hoisted refs. `apokatastasis ==
  13` / `music == 13` hold. The `test_the_decoder_sees_what_a_text_grep_cannot` non-vacuity factor
  `car_decoded >= 10 * max(other)` was lowered to **`>= 4 *`** WITH the reason recorded: carrier
  amsc-decoded (202) vs class (40) is now ~5×, no longer a full order of magnitude — the natural
  consequence of draining amsc-referencing ops out of the registry, still leaving carrier the dominant
  amsc-decoded population.
- **C surfaces**: 3 hand C-comment sites repointed (`srmech_loopbind.c`, `srmech_pi.c`,
  `srmech_pi_archimedes.c`); `srmech.h` version-only; `srmech_invoke.c` grep-clean for the movers; ABI
  stays 10. `_c_claims.py` / `_native.py` regenerate — many of the 10 modules carry `c_dispatched` ops
  (`cyclic`, `hdc`, `laplacian`, `primes`, `rational`, `search`, `template`, `tlv`, `text`, `dispatch`),
  all keyed amsc→math; the C SYMBOLS are capability-named and unchanged.
- **Rosetta**: all 166 moved op rows repointed; buckets preserved; every moved op rosetta-visible under
  `srmech.math`; completeness + transitive + roots-single-source green.
- **Regenerated artifacts** (`tools/regen_all.py --accept-seed-drift`, native-absent, content-equal +
  idempotent): `_tool_docs.py`, `_c_claims.py`, `srmech_tool_registry.c`, `srmech_carrier_registry.c`,
  `srmech_responsion_registry.c`; class registry byte-identical.
- **Verification** (numpy-absent WSL): 10/10 `import srmech.math.<m>` succeed, 10/10 `srmech.amsc.<m>`
  raise `ModuleNotFoundError`; `describe` total **525**; whole-suite `pytest --co -q` collects **13034**
  with **0 ImportError**; census / op-name-set / decode-aware / rosetta
  completeness+transitive+roots-single-source / def_parity / no-stdlib-math (the `..math` relative import
  is exempt, guard gates on `node.level == 0`) all green; `regen --check` up to date.

## Amendment K — the NINTH slice, the CARRIERS batch: fifteen modules → `srmech.math`, DRAINING the math bucket, v0.9.0rc374 (`#T1034`)

The math bucket's LAST slice. rc372 opened `srmech.math` (general-algebra), rc373 drained the ten A–N
primitives; this slice moves the fifteen general CARRIERS — `mat` / `vec` / `hv` / `q` / `qmat` / `qi` /
`qalg` / `qprime` / `poly` / `qpoly` / `qbipoly` / `tripoly` / `complex128` / `carrier_ladder` /
`carrier_spectrum` — `srmech/amsc/*.py` → `srmech/math/*.py`. Leaf names kept (B.1 rule 1).
`describe()["tools"]["total"]` stays **525** (10 carrier-family op names repoint amsc→math — a move, not
an add; the bulk of the roster are pure carriers with **no** ToolEntry op); `SRMECH_ABI_VERSION` stays
**10**. `carrier_schema` is NOT in this batch — it is the introspection surface (the noun-side dual of
`tool_schema`) and STAYS in `amsc`. **With this slice the math bucket is FULLY DRAINED**: `srmech.math`
holds all 28 of its A.2 members.

### The H.2 over-count reconciliation, CLOSED IN FULL

A.2 published `srmech.apokatastasis` = 31 and `srmech.math` = 22. Amendment H.2 found the real
special-functions family is only 25 — A.2's 31 OVER-counted it by 6, having lumped in `modular_linalg`
(GF(p) LA, reassigned to `srmech.math` at rc372) plus 5 of the general carriers. This slice realises the
carrier half, so the reconciliation is booked in the census: `ADR_A2_DESTINATION_COUNTS["srmech.math"]`
**22 → 28** and `["srmech.apokatastasis"]` **31 → 25**. The **sum is unchanged** (`28 + 25 == 22 + 31 ==
53`), so `sum(ADR_A2_DESTINATION_COUNTS.values()) == 74` still holds and the "73 of 75" gap is preserved.
Both buckets are now FULLY named (math `28 == 28`, apokatastasis `25 == 25`) — no longer subset-named.

### The mixed-import surgery (every carrier imports several siblings)

Carriers import each other heavily. The three-way discrimination governed every file: **moved files**
(the 15) — `from ..math import <sib>` collapsed to `from .<sib>` (the rc372/rc373 math modules `laplacian`
/ `rational` / `cyclic` / `primes` / `modular_linalg` / `hdc` are now siblings), intra-batch roster
siblings (`from .vec` / `from .q` / `from .poly` / …) stayed relative, `from . import _native` up-reached
to `from ..amsc import _native`, `from ..apokatastasis…` left byte-unchanged. **KEEPERS** — `amsc/__init__.py`
(the `Qalg` / `Qprime` / `QMat` / `Poly` / `TriPoly` re-exports, repointed `from .<m>` → `from ..math.<m>`
so `from srmech.amsc import Qalg` still resolves), `coupling.py`, `carrier_schema.py`, `amsc/cascade/one.py`
(`from ..q` → `from ...math.q`). **Pre-existing math consumers** `dispatch.py` / `hdc.py` / `laplacian.py`
/ `rational.py` `from ..amsc.<m>` → `from .<m>`. **Sibling subpackages** `apokatastasis/*` + `music/harmonics.py`
`from ..amsc.<m>` → `from ..math.<m>`.

### The eleven-form sweep — which forms this batch actually hit

HIT: [1] dotted; [3] `from srmech.amsc import <m>` (6 single-name test imports; no multi-name line mixed a
carrier with a keeper); [4] relative/lazy (above); [5] worked-examples ledger (native-absent recapture
after regen); [6] C comments (`srmech.h` + `ROSETTA_LEDGER.md` + `srmech_poly.c` / `srmech_qmat*.c` /
`srmech_qpoly.c` / `srmech_tripoly.c` / `srmech_carrier_spectrum.c` + two `test_srmech_qmat*.c`); **[9] the
CI workflow YAML** `.github/workflows/srmech-ci.yml` line 693 `from srmech.amsc.mat import Mat` (a
smoke-import step outside `docs/srmech/**` that no repo gate catches); **[11] two pathlib/`os.path.join`
source-readers** (`test_carrier_spectrum_rc69.py`, `test_numpy_carrier_ratchet.py`) → `"math"`. NOT hit
(measured, stated for the record): **[10] dynamic `importlib`** — the audit tests' dynamic tuples name
only `srmech.math.{cyclic,primes,rational}` / `srmech.amsc.format` / `cascade.*`, none a carrier; **[8]
split-string** — the two lines ending `srmech.amsc.` continue with `carrier_schema` / `eisenstein`,
neither a carrier. Forms 9/10/11 are the RUNTIME-ONLY sites — the workflow YAML is outside every gate's
scope, and the dynamic/pathlib sites are invisible to collect-only (they fail only at runtime), which is
why the four audit tests are run explicitly.

### The instrument set (all re-pinned in the SAME commit)

- **Census**: **33 → 18 modules**; digest `08c5199f…` → **`ae5704ea…`**; `LANDED` 42 → **57**; conservation
  **`18 + 57 == 75`**; `NAMED_DEPARTURES["srmech.math"]` 13 → **28** (fully named); over-count
  reconciliation above.
- **Op-name-set witness**: 10 carrier-family op names amsc→math; digest `10224532…` → **`e79b79fb…`**;
  `EXPECTED_N` **stays 525**.
- **Decode-aware** (MEASURED post-regen): `srmech_carrier_registry.c` **(100, 202) → (75, 196)**;
  `srmech_tool_registry.c` **(576, 0) → (440, 0)**; `_tool_docs.py` **(562, 0) → (431, 0)**; `_c_claims.py`
  **(91, 0) → (90, 0)**; `srmech_responsion_registry.c` **(6, 0) UNCHANGED** (no OPERATOR moved — carriers
  are operands, so the responsion edge-operator source-of-truth comments do not move); class **(0, 40)
  unchanged**; **`TOTAL_AS_TEXT` 1335 → 1042**, **`TOTAL_DECODED` 242 → 236**. Decoded population: carrier
  amsc **202 → 196**, `srmech.math.` **314 → 320** (conserved −6/+6 — the 6 carrier-family OP back-index
  refs; the pure carriers `mat`/`vec`/`hv`/`q`/… never entered the back-index). `apokatastasis == 13` /
  `music == 13` hold; the non-vacuity factor stays `>= 4 *` (196 ≥ 160).
- **C surfaces / c_dispatched**: no OPERATOR moved, so `srmech_responsion_registry.c` + `srmech_invoke.c`
  are unchanged; `srmech.h` version-only; ABI stays **10** (every `srmech_*` C symbol capability-named). The
  carrier-family c_dispatched ops (`carrier_spectrum` → `srmech_carrier_spectrum`, the `qmat_*` / `poly_*`
  peers) regenerate their `_c_claims.py` / registry keys amsc→math; the C symbols are unchanged.
- **Rosetta**: all moved carrier-family op rows repointed; buckets preserved; completeness + transitive +
  roots-single-source green.
- **Regenerated artifacts** (`tools/regen_all.py`, native-absent, content-equal + idempotent): `_tool_docs.py`,
  `_c_claims.py`, `srmech_tool_registry.c`, `srmech_carrier_registry.c`; responsion + class registries
  byte-identical; `regen --check` green.
- **Verification** (numpy-absent WSL): 15/15 `import srmech.math.<m>` succeed, 15/15 `srmech.amsc.<m>` raise
  `ModuleNotFoundError`; `describe` total **525**; whole-suite `pytest --co -q` **0 ImportError**; the four
  audit tests (`test_numpy_carrier_ratchet` / `test_cascade_numpy_absent` /
  `test_symmetric_eigh_canon_routing_rc67` / `test_associator_control_gf_solve_rc360`) PASS; census /
  op-name-set / decode-aware / rosetta / def_parity / no-stdlib-math green; `regen --check` up to date.

## Amendment L — the TENTH slice, the BIOLOGY bucket: four modules → `srmech.biology`, the FIFTH new DOMAIN namespace opened AND drained in ONE rc, v0.9.0rc375 (`#T1034`)

rc375 opens A.2's fifth destination, `srmech.biology`, and — the bucket being only four modules — DRAINS
it in the same slice: `genome` / `plasmid` / `q8` / `coupling` all leave `srmech.amsc` for
`srmech.biology`. It is the biological-substrate DOMAIN home (named by field, like `srmech.math` /
`srmech.apokatastasis`; contrast the structure home `srmech.cascade`). `genome` is the **arc's single
largest C surface** — many `c/src/srmech_genome_*.c` files plus extensive `srmech.h` prose — and this is
the first slice to move a heavily-C-backed OPERATOR family.

### L.1 The new-namespace SETUP — the same template (G.1 / I.2), with the census entry already fully named

Three edits beyond a drop-in slice: create `srmech/biology/__init__.py` (domain docstring + `__all__ = []`,
re-exports nothing — the Rosetta walk discovers ops through each submodule's own `__all__`); append
`srmech.biology` to the Rosetta walk roots (`tests/rosetta_roots.py` + the single-source pin
`_EXPECTED_ROOTS`, migrating it out of `_ADR0010_NEW_NAMESPACES` into `_ADR0010_EXISTING_DESTINATIONS`);
and record the roster in the census move-map. `NAMED_DEPARTURES["srmech.biology"]` was ALREADY the fully
named `{coupling, genome, plasmid, q8}` from the census mint (4 == the A.2 count of 4), so that entry needed
only verification, not extension — the four just moved from "named but not landed" to `LANDED`. The
nonexistent-package witness rotates OFF `srmech.biology` (now real) — it points at the still-absent
`srmech.physics`.

### L.2 GENOME OPS MOVE THE DECODED CHANNEL — the finding this slice was watched for

rc374 (Amendment K) moved pure CARRIERS (operands with no ToolEntry op), so its decoded population fell by
only 6. rc375 moves OPERATORS — `genome` / `q8` / `coupling` register ~86 ops, and their carrier back-index
references DO live in the carrier registry's four hoisted >4000-byte byte arrays. **Measured post-regen:
carrier-registry decoded `srmech.amsc.` 196 → 97 (−99), `srmech.biology.` 0 → 99 (+99, conserved); class
registry decoded `srmech.amsc.` 40 → 29 (−11), `srmech.biology.` 11 (the baked `[class] Genome`
descriptor's op refs).** `srmech.math.` / `srmech.apokatastasis.` / `srmech.music.` decoded all held
(320 / 13 / 13) — the biology move touched none of them. A new `assert biology == 99` pins the receiving
side (as `math` / `apokatastasis` / `music` are pinned); the non-vacuity dominance factor drops `4× → 3×`
(carrier 97 vs class 29 ≈ 3.3×, no longer ≥ 4× after the 99-ref drain).

### L.3 The eleven-form sweep — including one this slice HAD to find: the Rosetta ledger is `.ndjson`

HIT: **[1]** dotted `srmech.amsc.{coupling,genome,plasmid,q8}` (742 refs across 154 files) · **[2]**
`os.path.join(…, "amsc", "coupling.py")` (3 coupling source-readers) · **[3]** `from srmech.amsc import <m>`
(115, incl. ONE multi-name `from srmech.amsc import coupling, _native` SPLIT into a biology line + an amsc
line) · **[4]** the moved modules' relative up-reach `from . import _native` → `from ..amsc import _native`
(14 sites in genome/coupling/plasmid; q8 needed none — it imports amsc keepers absolutely; the octonion
precedent) and genome's `from srmech.amsc.q8 import` → relative `from .q8 import` (3); plasmid's intra-biology
`from . import genome` / `from .genome import` STAY relative · **[5]** worked-examples ledger (regenerated
native-absent, `native:false`) · **[6]** C comments (`srmech_genome.c` 33 dotted + 3 slash, `srmech.h`,
`ROSETTA_LEDGER.md`, `JPL_AUDIT.md`) — the `srmech_genome_*` / `srmech_q8_*` / `srmech_coupling_*` C SYMBOLS
are capability-named and DO NOT rename · **[7]** live notes/`srmech_research_notebook.md`/`rbs_lm_research`
prose · **the SLASH descriptor-path form** — genome stamps `"collector_descriptor_path": "srmech/amsc/genome.py"`
in two live attestation sites (→ `srmech/biology/genome.py`), with its `test_genome_attestation_rc304.py`
assertion updated; the FROZEN `genome_v2_fixture/manifest.json` (parser_version rc113) is left as historical
data · **the `.ndjson` Rosetta CLASSIFICATION ledger** (`tests/rosetta_classification.ndjson`, 90 rows × 2
`exposed_as`/`defined_at` fields = 180 refs) — the surprise form: a `srmech.amsc.<m>`-dotted DATA file NOT
in the `.py/.c/.md/.toml` sweep, and the SOURCE `gen_c_claims.py` reads to build `_c_claims.py`; leaving it
stale would have left `_c_claims.py` regenerating amsc-named genome claim keys. NOT HIT (stated for the
record): **[9]** `.github/workflows/srmech-ci.yml` — its only smoke import is `import srmech.qm`; it names
none of the four · **[10]** dynamic `importlib.import_module(f"srmech.amsc.{name}")` — the genome/q8 C-audit
tests DO use `spec_from_file_location`, but they load `test_rosetta_transitive_standalone.py`, NOT the moved
module, so no dynamic module-path names any of the four.

### L.4 The instrument set (all re-pinned in the SAME commit, MEASURED post-regen)

- **Census**: **18 → 14 modules**; digest `ae5704ea…` → **`b7443cd0…`**; `LANDED` 57 → **61**; conservation
  **`14 + 61 == 75`**; `NAMED_DEPARTURES["srmech.biology"]` already `{coupling, genome, plasmid, q8}`
  (verified; 4 == A.2's count of 4). The `test_the_census_can_actually_fail` stand-in leaver rotates
  `genome` → `compose` (genome having actually departed).
- **Op-name-set witness**: **86** op names amsc→biology; digest `e79b79fb…` → **`e52e8d11…`**; `EXPECTED_N`
  **stays 525** (a move, not an add).
- **Decode-aware** (MEASURED post-regen): `srmech_carrier_registry.c` **(75, 196) → (68, 97)**;
  `srmech_class_registry.c` **(0, 40) → (0, 29)**; `srmech_tool_registry.c` **(440, 0) → (282, 0)**;
  `_tool_docs.py` **(431, 0) → (275, 0)**; `_c_claims.py` **(90, 0) → (59, 0)** (31 genome/q8/coupling
  c_dispatched op keys repoint via the Rosetta ledger); `srmech_responsion_registry.c` **(6, 0) → (3, 0)**
  (coupling/genome ARE edge-OPERATOR names here — contrast rc374, where no operator moved so responsion held);
  **`TOTAL_AS_TEXT` 1042 → 687**, **`TOTAL_DECODED` 236 → 126**. Decoded population + the new `biology == 99`
  pin per L.2.
- **C surface / c_dispatched**: `genome` is the arc's largest C surface, yet every `srmech_genome_*` /
  `srmech_q8_*` / `srmech_coupling_*` C SYMBOL is capability-named and UNCHANGED — **ABI stays 10**. The MCP
  dispatch vtable `srmech_invoke.c` holds **NO** dotted Python op names for these (it dispatches by C symbol),
  so it needed no repoint; only the Python-side dotted keys in `_c_claims.py` / the registries moved.
- **Rosetta**: all moved op rows repointed amsc→biology in `rosetta_classification.ndjson`; `srmech.biology`
  added as a walk root; completeness + transitive + roots-single-source green.
- **Regenerated artifacts** (`tools/regen_all.py --accept-seed-drift`, native-absent — the moved genome/q8/
  coupling ops' docstrings and the octonion/rational sibling-cites legitimately drifted): all 6 outputs
  content-equal + idempotent (byte-identical across two passes); `regen --check` green.
- **Verification** (numpy-absent WSL): 4/4 `import srmech.biology.<m>` succeed, 4/4 `srmech.amsc.<m>` raise
  `ModuleNotFoundError`; `describe` total **525**; whole-suite `pytest --co -q` **0 ImportError**; the genome/q8
  audit + dynamic-import tests PASS; census / op-name-set / decode-aware / rosetta / def_parity / no-stdlib-math
  green; `regen --check` up to date.

## Amendment M — the ELEVENTH and FINAL slice, the introspect/native CORE: ten modules leave, `amsc` drains to its four keepers, ADR-0010 execution COMPLETE, v0.9.0rc376 (`#T1034`)

rc376 moves the **last ten non-keeper modules** out of `srmech.amsc` in one slice, taking the live population
to exactly the four attestation keepers (`format` / `catalog` / `descriptor` / `gap_suggester`). **The module
arc is DONE.** The ten split three ways: the six introspection-core modules `tool_schema` / `_tool_docs` /
`_tool_docs_curated` / `_carrier_examples` / `_c_claims` / `carrier_schema` → `srmech.introspect`; the two
Unicode tables `_unicode_fold_tables` / `_unicode_gb_tables` → `srmech.math` (their SOLE consumer is
`srmech/math/text.py`); `compose` → `srmech.cascade`; and `_native` **realized as the `srmech._native`
PACKAGE** (see M.1). It is the arc's largest single fan-out: `_native` alone is imported by ~347 absolute
`from srmech.amsc import _native` sites plus ~24 relative ones, and the whole slice touched **520 files**.

### M.1 The `_native` REALIZATION — `_native.py` → `_native/__init__.py`, shim and `.so` co-located

`srmech/_native/` already existed as a bare directory that the platform build installs `libsrmech.{so,dll,dylib}`
into. rc376 makes it a real package: `git mv srmech/amsc/_native.py srmech/_native/__init__.py`, so the ctypes
shim and the binary it loads now co-locate in one `srmech/_native/` package. The loader (`_find_library`,
strategies 1–3) is UNCHANGED and works from the new location — both projections verified: the numpy-absent
source cell loads `HAS_NATIVE=False` (pure), and a fresh venv with the installed **platform wheel** loads
`HAS_NATIVE=True`, `ABI=10`, `LIB` bound, `describe` total 525, from `.../srmech/_native/__init__.py`.

⚠️ **The MANDATORY packaging fix.** `pyproject-pure.toml` (hatchling) previously excluded the WHOLE
`srmech/_native/*` + `**` tree — correct while the shim lived in `amsc/` and `_native/` held only the binary,
but after the realization that would DROP the shim from the pure wheel and break every pure install. The
excludes are NARROWED to BINARIES ONLY (`*.so` / `*.dll` / `*.dylib` / `*.dll.a` / `*.lib` / `*.pyd`) in both
the wheel and sdist targets, so `srmech/_native/*.py` SHIPS. `pyproject.toml` (scikit-build-core) needed NO
change — `wheel.packages=["srmech"]` copies the new `__init__.py`, CMake installs the `.so` into the same dir.
**Both wheels build-verified:** the pure `py3-none-any` wheel contains `srmech/_native/__init__.py` and ZERO
binaries; the platform `cp310…linux_x86_64` wheel contains BOTH `srmech/_native/__init__.py` AND
`srmech/_native/libsrmech.so`.

### M.2 THE COUNT AMENDMENT — A.2's "73 of 75" classification gap CLOSED to 75/75

Through Amendment L the A.2 destination table summed to 74 against the tree's 75 — A.2's own acknowledged
residual 1. rc376 resolves it: the two Unicode tables A.2 left unclassified belong to `srmech.math` (their sole
consumer is `math/text.py`), so `ADR_A2_DESTINATION_COUNTS` moves `srmech.introspect` **10 → 9** and
`srmech.math` **28 → 30** (net **+1**), the table now sums to **75 == the original tree**, and the census
assertions flip `sum(...)==74 → ==75` and `ORIGINAL_N − sum == 1 → == 0`. The introspect bucket is truly 9,
not 10: its nine members are the six moved this slice (`tool_schema`, `_tool_docs`, `_tool_docs_curated`,
`_carrier_examples`, `_c_claims`, `carrier_schema`) plus the already-landed `naming` / `op_provenance` /
`responsion_schema`. The census comment that read "carrier_schema STAYS in amsc" was a STALE DEFECT — it is the
introspect SURFACE, not a carrier, and introspect (NAMED_DEPARTURES + this ADR) is authoritative; corrected.

### M.3 The `compose` COLLISION pre-emption (stated so it is not rediscovered as a bug)

There are TWO `compose.py`. **This slice moves `srmech/amsc/compose.py`** — the ADR-0002 chain engine
(`run_chain` / `resolve_chain` / `parse_chain_spec` / `parse_catalog_chains`) — to `srmech/cascade/compose.py`
(a clean landing: `srmech/cascade/` had no `compose.py`). **`srmech/amsc/cascade/compose.py` is a DIFFERENT
module** (a separate future slice) and was NOT touched; `amsc/cascade/__init__.py`'s `from . import compose` /
`from .compose import` refer to THAT module and correctly STAY. The dotted-prefix sweeps target
`srmech.amsc.compose` (which never matches `srmech.amsc.cascade.compose`), so the collision cannot be tripped
by a mechanical replace.

### M.4 The sweep — the forms this slice actually hit, and two the move-plan under-specified

HIT: **[1]** dotted `srmech.amsc.<m>` across live source/tests/C/tools/`.github` · **[2]** slash
`amsc/<m>` filesystem paths (incl. the codegen output paths + `load_committed`) · **[3]**
`from srmech.amsc import <m>` **absolute member-imports — 381 of them, 347 being `_native`** — plus six
distinct MULTI-module forms (`from srmech.amsc import _native, cascade`, `… _native, format as …`,
`… ThetaSum, _native`, `… catalog, compose`, …) each SPLIT so the keeper stays in `amsc` and the mover
repoints · **[4]** relative up-reach inside `amsc` keepers/subpackages — `catalog.py` / `format.py`
`from . import _native` → `from .. import _native`, `catalog.py` `from . import compose` →
`from ..cascade import compose`, `cascade/one.py` `from .. import _native` → `from ... import _native`, and the
moved files' own per-new-home imports (`tool_schema`/`carrier_schema` `from . import _native` → `from ..`,
`carrier_schema`'s `.cascade.cayley_dickson` → `..amsc.cascade.cayley_dickson`, `_native`'s `._c_claims` →
`..introspect._c_claims`) · **[5]** worked-examples ledger (regenerated native-absent, `native:false`) ·
**[6]** C comments (`srmech_meta.c` `_native` loader, `srmech_infer.c` `srmech._native.gosper_c`,
`srmech_compose*.c`, `srmech_carrier_schema.c`, `srmech.h`, `README.md`) — the C SYMBOLS are capability-named
and DO NOT rename · **[7]** `.github/workflows/srmech-ci.yml` (both the standalone `from … import _native`
lines AND the three embedded `python -c "…"` one-liners a line-start sweep misses) · the `.ndjson` Rosetta
ledger (13 rows: tool_schema ×7, compose ×5, carrier_schema ×1). NOT explicitly in the move-plan but FOUND and
fixed: the **codegen generator OUTPUT paths** (`codegen_manifest.GENERATORS` `gen_tool_docs` /
`gen_c_claims` outputs, the `gen_curated_probe` / `gen_carrier_examples_probe` / `gen_unicode_*`
`os.path.join(…, "amsc", …)` write paths) — left stale, `regen_all` would have re-emitted the moved files back
into `amsc`. `srmech/__init__.py`'s `warmup_all` import repointed `.amsc.tool_schema` → `.introspect.tool_schema`
and `amsc/__init__.py`'s side-effect `from . import tool_schema` was removed (registration now fires from the
`srmech.__init__` end via `warmup_all()`). The `native_status()` docstring's "srmech.amsc._native (shim) vs
srmech._native (data dir)" contrast INVERTED at the move and was rewritten true.

### M.5 The instrument set (all re-pinned in the SAME commit, MEASURED post-regen)

- **Census**: **14 → 4 modules** (== the four keepers; the module arc is COMPLETE, `KEEPERS ==
  _manifest_modules()`); digest `b7443cd0…` → **`7536f292…`**; `LANDED` 61 → **71**; conservation
  **`4 + 71 == 75`**. `NAMED_DEPARTURES` gains the six introspect-core modules + the two Unicode tables;
  `ADR_A2_DESTINATION_COUNTS` introspect 10→9 / math 28→30 (M.2). The `test_the_census_can_actually_fail`
  stand-in leaver now runs on a HYPOTHETICAL pre-completion population (add `compose` back, then remove it) —
  the manifest holds only keepers, so there is no real non-keeper left to retire as the stand-in.
- **Op-name-set witness**: **5** op names amsc→ (`compose.*` → `srmech.cascade` ×4, `carrier_schema` →
  `srmech.introspect` ×1); digest `e52e8d11…` → **`e85eb71e…`**; `EXPECTED_N` **stays 525** (a rename, not an add).
- **Decode-aware** — **the AS-TEXT channel only; DECODED is FLAT at 126** (no moved op had a back-index ref in
  a hoisted byte array — `compose`/`carrier_schema` are not carrier ops, and the six introspect-core infra
  modules register no ops). `srmech_carrier_registry.c` **(68, 97) → (67, 97)**; `srmech_tool_registry.c`
  **(282, 0) → (257, 0)**; `_tool_docs.py` **(275, 0) → (252, 0)**; `_c_claims.py` **(59, 0) → (58, 0)**;
  class + responsion registries UNCHANGED. **`TOTAL_AS_TEXT` 687 → 637** (−50), **`TOTAL_DECODED` 126 → 126**.
  The pinned population asserts (`amsc 97` / `math 320` / `biology 99` / `apokatastasis 13` / `music 13` /
  class-decoded 29) all HELD — this slice moved no operator whose refs live in the decoded channel.
- **C surface / ABI**: no C SYMBOL renamed (`srmech_compose*` / `srmech_carrier_schema` / the `_native` ctypes
  bindings are all capability-named); only Python-side dotted keys moved. **ABI stays 10.**
- **Rosetta**: the 13 moved op rows repointed amsc→{introspect, cascade} in `rosetta_classification.ndjson`;
  completeness + transitive + roots-single-source green.
- **Regenerated artifacts** (`tools/regen_all.py`, native-absent): `introspect/_tool_docs.py` rewrote (the moved
  op keys); all 6 outputs content-equal + idempotent (byte-identical across two passes); `regen --check` green.
- **Verification** (numpy-absent WSL): all 4 moved-destination imports succeed; 6/6 `srmech.amsc.<m>` raise
  `ModuleNotFoundError`; `describe` total **525** in BOTH the pure cell and the installed-platform-wheel native
  cell (`HAS_NATIVE=True`, ABI 10); whole-suite `pytest --co -q` **13034 tests, 0 ImportError**; the audit /
  dynamic tests (codegen_manifest, tool_schema, carrier_schema, compose, chain-runner, unicode, text, introspect
  / native_status) PASS (283 passed, 39 native-path skips); census / op-name-set / decode-aware / rosetta
  (completeness + transitive + roots-single-source) / def_parity / no-stdlib-math green; `regen --check` up to date.

### M.6 ADR-0010 EXECUTION IS COMPLETE

`srmech.amsc` now holds exactly its four attestation keepers (`format` / `catalog` / `descriptor` /
`gap_suggester`) plus the two attestation subpackages (`adapters` / `attested`) and the `cascade` subpackage
(A.2's separate subpackage row, a distinct future concern). The 71-module drain that A.2 planned is DONE across
eleven slices (rc366 → rc376). The census `test_the_end_state_floor_is_the_four_keepers` now asserts EQUALITY
(`KEEPERS == _manifest_modules()`) rather than strict-superset — the completion condition A.5 documented, now
reached.

## Amendment N — the FINAL slice, the `cascade` SUBPACKAGE: fifteen modules `srmech/amsc/cascade/` → `srmech.cascade`, ADR-0010 execution FULLY COMPLETE (modules AND subpackages), v0.9.0rc377 (`#T1034`)

Amendment M drained the last `srmech/amsc/*.py` MODULES to the four attestation keepers, but left one
loose end it named explicitly: the `cascade` SUBPACKAGE, carried under A.2's separate `srmech.cascade.*`
row (Status-of-adoption "verify"). This slice closes it. All fifteen `srmech/amsc/cascade/*.py` files
`git mv` into the pre-existing top-level `srmech/cascade/` structure-home (created rc364 with its
`catalogs/` subtree + the ADR-0002 chain-engine `compose.py`). `srmech.amsc` is now exactly its four
keeper modules (`format` / `catalog` / `descriptor` / `gap_suggester`) + its two attestation subpackages
(`adapters` / `attested`). ADR-0010 execution is now FULLY COMPLETE — modules AND subpackages.

### N.1 The `compose` → `composites` rename — ADR B.1 rule-1's ONE sanctioned exception

B.1 rule-1 is "a slice relocates a PARENT; it does not rename the LEAF". This slice is its single
deliberate exception, and it is documented AS the exception rather than performed silently. A `compose.py`
already lived in `srmech/cascade/` — the ADR-0002 chain ENGINE (`run_chain` / `parse_chain_spec`). The
incoming `amsc/cascade/compose.py` is the DISJOINT lean-ISA COMPOSITES layer (`cyclic_gcd` /
`best_rational_signed` / `kuramoto_step` / `autocorrelation`), whose own module docstring opens *"Cascade
**composites** — iterative algorithms over the atoms"*. Two disjoint modules cannot share one leaf name,
so the incoming one is renamed to `composites.py` (module `srmech.cascade.composites`). The leaf name is
docstring-DERIVED (not invented), which is what makes it the minimal resolution: the module already called
itself "composites". The incumbent `compose.py` is left untouched. Public surfaces are disjoint
(`run_chain` vs `cyclic_gcd`), so no consumer is ambiguous. The C dispatch strings use FLAT op names
(`srmech.amsc.cascade.cyclic_gcd`, never `...compose.cyclic_gcd`), so they took the plain amsc-drop; only
the `[class]`-descriptor / Rosetta-ledger / `_c_claims` `defined_at` *module-qualifier* fields carry the
`compose`→`composites` rename.

### N.2 The flat-API `__init__` merge

The rc364 top-level `__init__` (catalogs-loader package, deliberately import-free) is UNIONED with the
incoming subpackage `__init__` (the flat op re-exports). This preserves the full flat surface every
`from srmech.cascade import <op>` consumer AND the DSL flat resolver (`dsl/_catalog.py`'s
`getattr(srmech.cascade, op_name)`) rely on. Load-bearing ORDERING is preserved: the `atoms` re-exports
(`chiral_flip` / `hypercomplex_couple` / `magnitude`) precede the `cd_register` / `sedenion_register`
imports, which do `from . import chiral_flip` at import time.

### N.3 The C highest-risk edit — hardcoded `strncmp` length constants

`c/src/srmech_make_class.c`'s vtable keys the moved `one.one_*` and `sedenion_register.sed_*` op families
with `strncmp(op, "<prefix>", N)` on hardcoded prefix-length ints. The dotted prefix shortens by
`len("amsc.") = 5`, so both the strings drop `amsc.` AND the ints DECREMENT by 5:
`"srmech.cascade.one.one_"` **28 → 23**, `"srmech.cascade.sedenion_register.sed_"` **42 → 37** (with the
paired `op + 42` → `op + 37`). A silent miss compiles but mis-dispatches; it is caught only by the native
class-method parity tests, which pass (the platform wheel builds and `test_run_class_method_c_rc202.py` /
`test_make_class_engine_c_rc201.py` are green with `HAS_NATIVE=True`).

### N.4 The instrument set (all re-pinned in the SAME commit, MEASURED post-regen)

- **Census** (`test_amsc_module_census_rc365.py` + manifest): `EXPECTED_N_SUBPACKAGES` **3 → 2**
  (`cascade` dropped from `EXPECTED_SUBPACKAGES`, leaving `adapters` + `attested`); digest
  `7536f292…` → **`91df88e7…`**. Module count stays **4** (the module arc completed at rc376). There is no
  `LANDED_SUBPACKAGES` symbol — a subpackage move needs no LANDED entry.
- **Op-name-set witness**: SET moves **75** op names `srmech.amsc.cascade.*` → `srmech.cascade.*`; digest
  `e85eb71e…` → **`5ce22d65…`**; `EXPECTED_N` **stays 525**.
- **Decode-aware prefix ratchet**: the `srmech.amsc.` population's LARGEST-yet drain, and the one that
  EMPTIES it — cascade ops ARE carriers, so their back-index refs dominated the hoisted byte arrays.
  carrier `(67, 97) → (0, 2)`; class `(0, 29) → (0, 0)`; tool_registry `(257, 0) → (69, 0)`; `_tool_docs`
  `(252, 0) → (66, 0)`; responsion `(3, 0) → (0, 0)`; `_c_claims` `(58, 0) → (6, 0)`; `TOTAL_AS_TEXT`
  **637 → 141**, `TOTAL_DECODED` **126 → 2**. The two non-vacuity proofs PIVOT to `srmech.cascade.` (the
  new decode-only population: 95 carrier + 28 class refs), pinning `cascade == 95` beside `biology 99` /
  `math 320` / `apokatastasis 13` / `music 13`. amsc's decoded population is DRAINED to 2 keeper residuals.
- **Rosetta ledger**: the 75 moved cascade op rows repointed `exposed_as` amsc→cascade and `defined_at`
  `compose`→`composites`; completeness + transitive + roots-single-source green.
- **`test_run_class_method_c_rc202.py`** baked-op-ref scan: regex broadened `srmech\.amsc\.` →
  `srmech\.(?:cascade|biology)\.` — amsc drained, so the amsc-only scan had gone blind.
- **Regenerated** (`tools/regen_all.py --accept-seed-drift`): all 6 outputs content-equal + idempotent;
  `regen --check` green. `SRMECH_ABI_VERSION` stays **10** (every cascade C symbol is capability-named and
  UNCHANGED — a move renames Python paths, never C symbols).

### N.5 ADR-0010 EXECUTION IS FULLY COMPLETE

`srmech.amsc` is now exactly its four attestation keeper modules + its two attestation subpackages
(`adapters` / `attested`). The module drain (71 modules, rc366 → rc376) and the subpackage drain (the
`cascade` subpackage, rc377) are both DONE. ADR-0010 — the namespace declustering of `srmech` into
field-named domains, structure-homes, provenance-only `amsc`, and cross-cutting `introspect` — is
executed in full.

# ADR-0010: srmech namespace declustering — `amsc` is the attestation framework, not the dumping ground

**Status:** 🟡 Proposed — target design; executed as its own breaking arc *after* the Class-N precision migration (rc318→320) completes.
**Date:** 2026-07-23.
**Authors:** Steven Kirkland + Claude Opus 4.8.
**Supersedes:** none.
**Superseded-by:** none.
**Relates-to:** ADR-0004 (config-driven domain-agnostic surface — the `[class]`/`[cascade]` TOML this ADR re-homes), ADR-0006 (carrier discipline), ADR-0009 (multi-implementation parity — declustering must preserve C/Python parity per module).
**Codifies memory:** `[[project_srmech_module_namespace_needs_declustering]]` · `[[project_class_n_precision_contract_migration_breaking_no_legacy]]` · `[[user_stance_breaking_means_fixing]]`.

---

## Context

`srmech.amsc` was named the **A**ttested **M**ulti-**S**ource **C**ollector/**C**atalog — the provenance/MPR framework. It has since accreted **~70 modules** that are not attestation: the whole special-functions galaxy (`rational`, `elliptic_*`, `modular_forms_*`, `thetasum`, `riemann_theta`, `zeilberger`/`gosper`, `jacobi`), the carriers (`q`/`mat`/`vec`/`hv`), the 14 A–N primitives (`format`/`cyclic`/`laplacian`/`hdc`/…), the biology domain (`genome`/`plasmid`/`q8`), and the composition catalogs (`_research/{class,cascade}_catalog/`). The namespace no longer reads as its own map, and `import srmech.amsc.rational` misdescribes what `rational` is. The pressure is real and recurring — rc317 had to move `relative_writhe` out of `srmech.amsc.genome` to dodge the wire-format ratchet; that was the first small instance of this ADR.

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

**The classification test (the load-bearing rule the audit must apply per module):** ask *"does this module belong to ONE namespace, or does it need to know about ALL of them?"* A module that spans every namespace is **cross-cutting meta**, and it cannot live inside any single namespace — not even `amsc`. `tool_schema` is the exemplar: it registers every op in every domain, so it must sit ABOVE the namespaces (`srmech.introspect`/`srmech.tools`), not inside the provenance framework. The four buckets are therefore: **domains** (math/physics/biology/music — bounded field), **structures** (winding/cascade — bounded machinery), **provenance** (amsc — bounded to attestation), and **cross-cutting meta** (introspect/tools — unbounded, knows everything). Every module in today's `amsc` gets re-classified by this test, not left by inertia.

### The winding-home name (DECIDED — user, 2026-07-23)
The special-functions home is **`srmech.apokatastasis`** (ἀποκατάστασις, "restoration / return to the original position") — it names the *group's defining property* (the cycle **closes** — wind and **return**), the Great-Year cosmic return, and the Antikythera's mechanical Saros-spiral apokatastasis. It is a **Greek word for a Babylonian–Chaldean idea** (the Stoic cosmic return via Berossus/Chrysippus), so it is cross-tradition, not merely Greek. (Later Christian-theological usage exists; in the astronomical/mathematical sense the term is precise.) The special functions ARE the return-machinery: elliptic = doubly-periodic return, modular = the modular group's return, theta = quasi-periodic return, q-series = the nome's periodicity.
- **Sanity shortening:** ship a terse alias `srmech.apo` and keep the plain-English facade `srmech.winding` re-exporting from it, so the long canonical never bites; CLI auto-completion (below) makes the length a non-issue at the prompt.
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

A name that exists only in Python is a parity violation the moment the package is compiled to a bare-C host or bound from Go/Rust (ADR-0009). **Current pipeline:** `srmech.amsc.tool_schema` (the Python `ToolEntry` registry) is the source of truth; four codegen tools — `gen_{tool,carrier,class,responsion}_registry.py` — bake the names into `srmech_{tool,carrier,class,responsion}_registry.c` at build time (each file headed `GENERATED … DO NOT EDIT … Source of truth: srmech.amsc.tool_schema`). So a compiled C host already *carries* the names — but Python is the privileged source, and (tracker #930) a rename that skips one of the four generated tables silently desyncs C dispatch while the pure path keeps answering.

**Target for the declustering (and any future binding):**
1. **The names live in a neutral, implementation-agnostic manifest**, not hardcoded in Python — the config-driven naming layer (ADR-0004; the rc261 function-aliasing TOML) is the seam: the module-namespace map (`apokatastasis` + `apo`/`winding` aliases; `math`/`physics`/`biology`/`music`) is declared there, and — the substrate-native option — is itself a **genome/attestation record** so any implementation reads the names from the store rather than from Python source.
2. **Every implementation CODEGENS its name registry from that one manifest** at build time — Python's `tool_schema`, the four C registries, and any Go/Rust binding — so the names are byte-identical everywhere and no implementation is primary (ADR-0009).
3. **A rename regenerates ALL name tables in lockstep** — the #930 ripple: tool + carrier + class + responsion registries + the count-pins + rosetta.

   ⚠️ **CORRECTED rc359 (`#T1009`) — "gated so a desync fails loudly" was NOT true of all four.** It
   held for the **tool** registry (a hash witness, which caught rc348), for **carrier** and
   **responsion** (byte-identity ratchets at `test_carrier_schema_rc205.py:198-205` and
   `test_responsion_schema_rc225.py:267`), and for `c_dispatched` **ops** (the rc300 op→symbol claim
   manifest). It did **not** hold for the **class** registry, whose only witness asserted that names
   *appeared* — never that the descriptor BODY matched. rc300 was **mis-cited** here: it stops an op
   silently falling back to pure on a stale `.so`, which is a different failure from a registry whose
   *content* has drifted. rc359 shipped the content witness; **35 dotted op refs are now verified
   resolvable in C**.

   ⚠️ **AND THE CLASS REGISTRY IS INVISIBLE TO GREP — this is the one that will bite this arc.** Its
   `[class]` descriptors are embedded as **decimal byte arrays**, so the very prefixes this ADR
   renames do not appear as text at all. Measured on `srmech_class_registry.c`:

   | prefix | as text | decoded from the byte arrays |
   |---|---|---|
   | `srmech.amsc.cascade` | **0** | **29** |
   | `srmech.amsc.genome` | **0** | **11** |

   A verification step that greps the generated C for the old prefixes reports **CLEAN** while the
   binary still carries all forty. **Any rename check on this file must DECODE the byte arrays** —
   and the same question must be asked of every generated artifact before trusting a textual sweep
   (rc359 found the identical blindness in `srmech_tool_registry.c`).
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

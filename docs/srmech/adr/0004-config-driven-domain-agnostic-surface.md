# ADR-0004: srmech's user-facing surface is config-driven — the domain-agnostic layer (classes, chains, catalogs, and names in TOML)

**Status:** ✅ Accepted — **standing policy** (governs how domain-specific surfaces are added).
**Date:** 2026-07-16.
**Authors:** Steven Kirkland + Claude Opus 4.8.
**Supersedes:** none.
**Superseded-by:** none.
**Extends:** ADR-0001 (the profile pattern) · ADR-0002 (catalog-as-computation).
**Codifies:** `[[feedback_prefer_config_driven_toml_classes]]` · the rc261 `[[alias]]` addition.

---

## 1. Context — why srmech is config-driven

srmech is a **domain-agnostic substrate**: a fixed vocabulary of 14 primitive classes (A–N) and
a set of exact carriers, over which *any* domain (Antikythera gears, chess spectra, genomes,
cosmology, an LLM's stored relationships) is expressed. For srmech to be genuinely domain-agnostic,
a researcher must be able to declare **their** domain — its objects, its pipelines, its
attested data, and its *vocabulary* — **without editing srmech's source**. If adding a domain
meant forking the library, srmech would be a genome library or a chess library, not a substrate.

So the user-facing surface is **config-driven**: the domain lives in TOML (and the attested
catalogs), the framework is the runtime. This is the load-bearing property that lets one library
serve every sister-package in the spectral-research portfolio.

## 2. The config-driven surfaces (what a user declares in config, not code)

| What a user declares | Config surface | Runtime entry point | Since |
|---|---|---|---|
| **Attested data catalogs** (MPR-attested ground-proof rows) | AMSC descriptor TOML | `srmech.amsc.tool_schema` / `register_attested_root` | ADR-0001/0002 |
| **Domain classes** (state + cascade-op-chain methods = a cascade of the 14) | `[class]` TOML | `srmech.dsl.make_class` | rc39 |
| **Pipelines** (a named cascade of catalog ops) | `[chain]` + `[[stage]]` TOML | `srmech.dsl.build_chain_from_toml` / `run_toml_chain` | rc12 |
| **Names / vocabulary** (bind a user's own name to any srmech function) | `[[alias]]` TOML | `srmech.dsl.alias` / `build_aliases_from_toml_str` | **rc261 (this ADR)** |
| **Extension packages** (a downstream registers catalogs + a native lib) | profile descriptor | the profile loader | ADR-0001 |

Each is *declarative*: the framework reads the config and instantiates; the domain author writes
TOML, not srmech source.

## 3. Decision

**srmech's user-facing surface is config-driven, and the framework's own naming is a DEFAULT, not
a constraint.** Two commitments:

1. **A new domain object is declared in config where a config surface fits it** — a domain class →
   `[class]` TOML (`make_class`), a pipeline → `[chain]` TOML, attested data → an AMSC catalog, a
   name → `[[alias]]` TOML. Hand-coding a srmech domain class when a TOML descriptor would serve is
   the failure (`[[feedback_prefer_config_driven_toml_classes]]`). The framework's own carriers,
   the `srmech.qm.*` physics op-families, `srmech.bus`, and the PAL stay Python (they are the
   substrate, not a domain).

2. **The framework's naming is re-aliasable in config.** srmech names things by its own
   conventions (e.g. the rc260 `genome` = biology-aware umbrella, `plasmid` = all-stick builder).
   A user who prefers different vocabulary — `build`, `stick`, a domain term, another language —
   binds it in a `[[alias]]` TOML with **no code change**. So a framework rename (like rc260's) is
   never a user-layer break: `alias("my_name", "srmech.biology.genome.plasmid")` restores any name.
   This is the property that makes the naming decisions internal — the config layer owns the
   user's vocabulary.

## 4. The rc261 addition — `[[alias]]` function aliasing (`srmech.dsl._alias`)

`srmech.dsl.alias(name, target)` binds `name` to the srmech function at the dotted `target` path
(via `functools.wraps`, preserving the signature/docstring); `build_aliases_from_toml_str(spec)` /
`load_aliases_toml(path)` parse a `[[alias]]` array (`name` + `target`) into a `{name: callable}`
mapping. Parsing reuses the DSL's native (`srmech_toml`) + `tomllib` loader; resolution reuses the
robust dotted-name walk `srmech._resolve.resolve_dotted_callable`.

> **rc413 (`#T1094`) — path corrected, and the scope made explicit.** This sentence read
> `srmech.mcp._tools._resolve_dotted_callable` through rc412. The walker moved to
> `srmech._resolve` (core) because two *core* rungs — this one and
> `srmech._handles.resolve_operator_name` — were importing upward into the ADR-0009 §4 host-glue
> layer, which made `srmech.mcp` non-removable. The claim itself was, and remains, **scoped to the
> `[[alias]]` rung only**. That scoping is worth stating out loud rather than leaving to
> inference: the `[class]` rung next door does **not** share this resolver. It ships its own
> deliberately weaker last-dot-only `srmech.dsl._class_catalog._resolve_op`, so a `[class]` TOML
> `op` may bind `module.function` but **not** `module.Class.method`, while an `[[alias]]` `target`
> may bind either. Measured at rc413 over real `module.Class.method` triples enumerated from the
> shipped package (N = 307): the robust walker resolves all of them, `_resolve_op` raises
> `ModuleNotFoundError` on all of them. Over every population the package actually *ships* the two
> agree exactly (ToolEntry names 0/559 divergent, class-catalog op-refs 0/31, alias targets 0/7),
> so nothing is broken today — but the two rungs are not interchangeable, and unifying them would
> be a **widening of what a user `[class]` descriptor may bind**, i.e. its own decision with its
> own test, not a refactor. rc413 deliberately did not make it.

**Security (load-bearing):** a `target` **MUST** be a dotted `srmech.*` path. The config-driven
naming layer binds names to srmech's *own* surface, **never arbitrary imports** — a config file
cannot be coaxed into importing / calling `os.system`, `subprocess.run`, or any non-srmech module
(rejected with a `ValueError`). Config gives *names*, not *capabilities*.

## 5. Consequences

- Adding a domain surface is a config change first; a source change only when no config surface
  fits (and then the gap in the config surface is itself a candidate build target — that is how
  the `[[alias]]` rung was found: the rename ask exposed that classes + chains were config-driven
  but *names* were not).
- Framework renames are internal decisions; the CHANGELOG documents the default names, the
  `[[alias]]` layer lets any user pin their own.
- The security restriction (srmech.*-only aliasing) is part of the contract — a widening to
  arbitrary targets would turn a naming layer into an execution layer and is out of scope.

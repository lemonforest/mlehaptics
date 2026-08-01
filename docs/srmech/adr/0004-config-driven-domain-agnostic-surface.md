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
robust dotted-name walk `srmech.mcp._tools._resolve_dotted_callable`.

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

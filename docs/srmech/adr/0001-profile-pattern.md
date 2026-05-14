# ADR-0001: The srmech profile pattern — domain-specific extension as configuration

**Status:** Draft (Task #199 design phase; not yet implemented).
**Date:** 2026-05-14.
**Authors:** Steven Kirkland + Claude Opus 4.7.
**Supersedes:** none.
**Superseded-by:** none.

---

## 1. Context

`srmech` v0.2.0 ships the **Attested Multi-Source Collector/Catalog (AMSC) framework** as a domain-agnostic substrate: the MPR v1 attestation format, NDJSON streaming I/O, descriptor TOML loader, six adapter classes (html / json / csv / netcdf / geotiff / literature), a universal catalog bridge with `register_attested_root()` cross-package overlay, and native-C dispatch for the hot paths (SHA-256, NDJSON line tokenisation).

Sister packages in the spectral-research portfolio currently consume srmech as a runtime dependency while shipping their own domain APIs:

- **`ephemerides-spectral`** — Sol star system. 52-body resonance graph, 19 attested catalogs, 11 cross-channel coupling surfaces, native BIP HDC encoder (`libephemerides_spectral`), bridge surfaces (`get_em_state`, `list_em_couplings`, `predict_itn_accessibility`, etc.).
- **`chess-spectral`** — chess piece-graph spectra, D₄/B₄ irrep decomposition, `qm_*.py` kinematics/dynamics modules, channel-decomposition framework.
- **`antikythera-spectral`** — bronze gear-DAG, cyclic-group algebra, Almagest/Freeth parameter sets.

Task #199 names these three as candidates for collapse "into srmech configs, not separate packages." That collapse, naively executed, would:

1. **Reduce maintenance overhead** — one publish workflow, one cibuildwheel matrix, one version cadence across the portfolio.
2. **Centralise the substrate** — research code shares the AMSC framework + native-dispatch infrastructure naturally.
3. **Lose modularity** — users wanting only `chess-spectral` would now pull the whole portfolio.
4. **Lose the third-party publishing story** — a researcher in some unrelated discipline (audio, biology, etc.) who wants to build on srmech's MPM substrate would have no template; they'd either fork srmech or paper over with their own version of `register_attested_root`.

The naive collapse is the wrong target. The **right target** is a *profile pattern* that:

- Lets srmech remain a publishable substrate that **anyone** can build on.
- Lets each domain's code stay coherent under its own name and version.
- Allows the domain code to be distributed either **inside** the mlehaptics monorepo (as srmech learns about it natively) or **outside** as a third-party PyPI package.
- Handles both **simple profiles** (catalogs + Python bridge functions) and **plugin profiles** (catalogs + Python bridge + a domain-specific native library that srmech loads dynamically).

This ADR specifies that pattern.

## 2. Decision

srmech v0.3.0 will introduce a **profile** concept: a unit of domain-specific extension that consists of:

1. A declarative TOML manifest (`srmech_profile.toml`) describing the profile's identity, catalogs, bridge surfaces, and (optionally) native library.
2. A Python entry-point registration (`[project.entry-points."srmech.profiles"]` in the consuming package's `pyproject.toml`) so srmech can discover profiles via `importlib.metadata.entry_points()`.
3. Optionally, a domain-specific native library loaded as a **plugin** through srmech's ctypes infrastructure when the profile declares one.

A srmech installation at runtime can:

- Enumerate registered profiles (`srmech.list_profiles()`).
- Activate a specific profile (`srmech.profile("ephemerides")`), which:
  - Registers the profile's catalog SSOTs via the existing `register_attested_root()` API.
  - Optionally loads the profile's native plugin library and binds the declared symbols.
  - Returns a `Profile` object exposing the profile's bridge surfaces as attributes.
- Compose multiple active profiles in the same process (e.g. cross-domain experiments that need both `chess` and `ephemerides` substrates loaded).

Profiles can be:

- **In-tree**: ship inside srmech itself under `srmech/profiles/<name>/`. Their `srmech_profile.toml` is data, not metadata; they auto-register at srmech import time.
- **Out-of-tree, monorepo**: a sibling package under `docs/*-maths/` declares its profile and entry-point. Discoverable by srmech via the standard entry-point mechanism.
- **Out-of-tree, third-party**: someone in another discipline publishes a Python package that depends on srmech, declares a `srmech_profile.toml` + entry-point, and ships it to PyPI. `pip install their-package` makes their profile visible to any srmech installation.

The third-party publishing story is **first-class**, not a happy accident. Test that constraint at every design step.

## 3. The profile descriptor schema

Each profile ships a `srmech_profile.toml` at a discoverable location (specified by the entry-point — see §4). Schema:

```toml
# ─────────────────────────────────────────────────────────────────
# Required: identity
# ─────────────────────────────────────────────────────────────────
[profile]
name = "ephemerides"                            # profile registry key
version = "0.27.0"                              # profile schema version
summary = "Sol star system spectral instrument"  # one-line description
package = "ephemerides_spectral"                # owning Python package
home = "https://github.com/lemonforest/mlehaptics/tree/main/docs/antikythera-maths/ephemerides-spectral"

# srmech version range this profile is compatible with.
# Mirrors `requires-python` semantics. srmech checks at load time.
srmech_requires = ">=0.3,<0.4"

# ─────────────────────────────────────────────────────────────────
# Optional: catalog SSOTs the profile registers
# ─────────────────────────────────────────────────────────────────
[profile.catalogs]
# Relative to the profile's owning package install root. srmech
# resolves via importlib.resources.files(package).joinpath(path).
attested_root = "_research/attested"

# Optional source-label override; defaults to profile name.
source = "ephemerides-spectral"

# ─────────────────────────────────────────────────────────────────
# Optional: bridge surfaces (Python functions surfaced via the
# Profile object as `srmech.profile("name").FUNCTION_NAME(...)`)
# ─────────────────────────────────────────────────────────────────
[profile.bridge]
get_em_state         = "ephemerides_spectral.bridge:get_em_state"
list_em_couplings    = "ephemerides_spectral.bridge:list_em_couplings"
predict_itn_accessibility = "ephemerides_spectral.bridge:predict_itn_accessibility"
# ... etc; one entry per surface, value is `module:function`

# ─────────────────────────────────────────────────────────────────
# Optional: native plugin library (the "plugin tier")
# Only present when the profile ships a domain-specific
# .so/.dll/.dylib that srmech should load + bind via ctypes.
# ─────────────────────────────────────────────────────────────────
[profile.native]
# Library name pattern (srmech expands to platform-specific filename).
# Example: "ephemerides_spectral" → libephemerides_spectral.so on Linux,
# libephemerides_spectral.dylib on macOS, ephemerides_spectral.dll on Windows.
library = "ephemerides_spectral"

# Install location relative to the owning package, mirroring srmech's
# own _native/ convention. Discovered via importlib.metadata.files().
install_path = "_native"

# Symbols the plugin exports + their ctypes signatures.
# srmech binds these at profile activation time.
[profile.native.symbols.es_encode_state]
argtypes = ["c_double", "POINTER(c_uint32)"]
restype  = "c_int"

[profile.native.symbols.es_find_syzygies]
argtypes = ["c_double", "c_double", "POINTER(es_syzygy_t)", "size_t"]
restype  = "c_size_t"
# ...

# ABI version contract — srmech checks at plugin load time.
abi_version_function = "es_abi_version"
expected_abi_version = 6

# Custom ctypes structs the plugin requires (mirrored from C headers).
[[profile.native.structs]]
name   = "es_syzygy_t"
fields = [
  { name = "body_a",    type = "c_uint8" },
  { name = "body_b",    type = "c_uint8" },
  { name = "jd_tdb",    type = "c_double" },
  { name = "kind",      type = "c_int" },
]
```

The `[profile.native]` block is **optional**. Profiles without it are *simple profiles* (Python + data only). Profiles with it are *plugin profiles* (Python + data + a domain-specific .so/.dll/.dylib).

## 4. Discovery mechanism

A profile is discoverable to srmech when its owning Python package declares:

```toml
# In the consuming package's pyproject.toml:
[project.entry-points."srmech.profiles"]
ephemerides = "ephemerides_spectral:srmech_profile_toml_path"
```

Where `srmech_profile_toml_path` is a module-level constant pointing at the TOML file's path relative to the package root (typically via `importlib.resources.files(__package__) / "srmech_profile.toml"`).

At srmech import time (or on first `srmech.list_profiles()` call — open question, see §10), srmech enumerates `importlib.metadata.entry_points(group="srmech.profiles")` to discover all installed profiles. The TOML is **lazily** parsed; the catalog registration + native-library load only fire when the profile is **activated** via `srmech.profile(name)`.

In-tree profiles (under `srmech/profiles/<name>/`) get auto-registered at srmech import time. They use the same TOML schema but don't need a separate `[project.entry-points]` declaration — srmech walks its own `profiles/` directory.

## 5. The two tiers

### Simple profile tier

Catalogs + Python bridge surfaces; no native code beyond srmech's own. `chess-spectral` is the canonical example. Activation cost: register the catalog root + bind the Python functions. **No ctypes, no .so loading**, no plugin-side ABI version check.

Suitable for any domain whose hot paths are either already covered by srmech's own native dispatch (SHA-256, NDJSON I/O) or aren't hot enough to need C.

### Plugin profile tier

Simple profile **plus** a domain-specific shared library that srmech loads via ctypes and binds against the symbols declared in `[profile.native.symbols]`. `ephemerides-spectral` is the canonical example (libephemerides_spectral with BIP HDC encoder, Fiedler partition, syzygy finder, etc.).

Plugin profiles take a stricter contract:

- **ABI version handshake.** The plugin must export a no-argument `int abi_version(void)` function. srmech compares the return value to `expected_abi_version`; mismatch → plugin not loaded, simple-profile path runs.
- **JPL discipline at the plugin boundary.** Plugins SHOULD follow srmech's own JPL Power-of-Ten audit pattern (bounded loops, no malloc-after-init, ≥2 asserts per function, ≤60-line functions, etc.). srmech does NOT enforce this; the plugin's maintainer does.
- **Single-thread contract per plugin.** srmech's own `srmech_ndjson_iter` uses a static line-assembly buffer; plugins that use similar static state must declare it. srmech does NOT thread-coordinate plugin calls; the calling code is responsible.
- **Library packaging.** Plugin libraries ship inside the plugin's own Python wheel, under the package's `_native/` directory (mirroring srmech's own convention). cibuildwheel matrix on the plugin side produces per-platform wheels. srmech doesn't redistribute plugin binaries; each plugin owns its own publish flow.

The plugin tier is what lets `ephemerides-spectral` keep its native BIP encoder + its own cibuildwheel matrix while still being a profile under srmech. ephemerides-spectral the *package* doesn't disappear; it becomes a srmech profile + plugin that ships its own wheels.

## 6. Third-party publishing story (worked example)

Suppose a researcher building an audio-spectral domain wants to consume srmech's MPM substrate. Their package layout:

```
audio-spectral/
├── pyproject.toml
├── srmech_profile.toml
├── audio_spectral/
│   ├── __init__.py        # exposes the path to the TOML
│   ├── bridge.py          # domain functions
│   ├── _research/
│   │   └── attested/      # NDJSON catalogs (HRTF, ITU-R BS.1770, ...)
│   └── _native/           # (optional, plugin tier)
│       └── libaudio_spectral.so
```

`pyproject.toml`:

```toml
[project]
name = "audio-spectral"
dependencies = ["srmech>=0.3"]

[project.entry-points."srmech.profiles"]
audio = "audio_spectral:SRMECH_PROFILE_TOML"
```

`audio_spectral/__init__.py`:

```python
from importlib.resources import files
SRMECH_PROFILE_TOML = files(__package__) / "srmech_profile.toml"
```

After `pip install audio-spectral`:

```python
import srmech
audio = srmech.profile("audio")          # activates → registers catalogs + (if plugin) loads .so
spectrum = audio.compute_hrtf_spectrum(...)  # bridge surface declared in srmech_profile.toml
```

The audio-spectral researcher never edits anything in srmech's own repo. They never need to be part of the mlehaptics monorepo. They publish their package independently to PyPI. Their profile is fully equal-citizen with ephemerides-spectral inside any srmech installation that has it pip-installed.

This is the third-party-publishable property. The ADR locks it in as a primary requirement, not a secondary nice-to-have.

## 7. Migration plan for existing portfolio packages

### Step 1 — chess-spectral as the simple-profile POC (validates §5 simple tier)

`chess-spectral` is the smallest of the three named in Task #199 and is structurally simpler (smaller native library footprint; fewer cross-channel surfaces). Migration:

1. Add `srmech_profile.toml` at the chess-spectral repo root (or under the package; placement TBD).
2. Add the `[project.entry-points."srmech.profiles"]` declaration to `chess-spectral`'s pyproject.toml.
3. chess-spectral's existing bridge.* functions stay; users can either keep `from chess_spectral import bridge` OR use `srmech.profile("chess")` — both work, both call the same underlying functions.
4. Ship chess-spectral X.Y.Z with the profile declaration; verify on TestPyPI; cut to PyPI.
5. Lessons learned go back into the ADR + the §3 schema if needed.

**Outcome:** The simple-profile tier is validated. No native-library complications. If something in the ADR turns out to need revision, it's caught here cheaply.

### Step 2 — ephemerides-spectral as the plugin-profile POC (validates §5 plugin tier)

Only after Step 1 is solid. Applies the schema to ephemerides-spectral's native library (libephemerides_spectral with BIP encoder, syzygy finder, etc.). Multi-PR:

1. PR-a: declare the simple-profile portion (catalogs + Python bridge). Verify that part works in isolation.
2. PR-b: declare `[profile.native]` for libephemerides_spectral; srmech learns to load it at plugin-profile activation time. Verify ABI handshake + ctypes binding.
3. PR-c: migrate the bridge-surface call sites so a user can do `srmech.profile("ephemerides").es_encode_state(...)` and get exactly what `ephemerides_spectral._native_bip.encode_state(...)` returns today.
4. ephemerides-spectral remains a separate PyPI package; its publish workflow keeps producing platform wheels. The PROFILE pattern is additive to its existing API.

**Outcome:** The plugin-profile tier is validated against the project's most demanding consumer. Any architectural shortcoming surfaces against a real workload before any third party tries to use the pattern.

### Step 3 — antikythera-spectral profile declaration

The smallest residual; mostly catalogs + parameter-set tables. Likely a simple profile (no native code). Quick win after Steps 1 + 2 land.

### Step 4 — Document the third-party publishing flow

After Steps 1-3 land, write a separate guide (probably `docs/srmech/PROFILE_AUTHORING_GUIDE.md` or similar) walking a third-party author through the §6 worked example with copy-pasteable templates. This is what enables the "researcher in another discipline" path.

### What does NOT migrate

- **Research notebooks** stay where they are. `ephemerides_spectral_research_notebook.md` is a research record, not code; it gets cross-referenced from srmech docs but doesn't move.
- **The standalone PyPI packages** stay published. We are *adding* the profile pattern, not *replacing* the package pattern. Users who want `pip install chess-spectral` should still be able to do that. Whether to *yank* a package later is a separate decision (see §10).

## 8. What this ADR does NOT decide

Things explicitly left open for future ADRs or research spikes:

- **In-tree vs out-of-tree placement for chess-spectral, antikythera-spectral, ephemerides-spectral after the profile pattern lands.** They could stay where they are (out-of-tree, sibling-of-srmech subtrees inside the monorepo) or move under `srmech/profiles/` (in-tree). Both work; performance is equivalent; the choice is about monorepo organisation, not about the pattern itself. Pick later; document in a subsequent ADR.
- **The exact srmech version that introduces the profile loader.** Targeting v0.3.0 but the actual cut depends on whether tool_schema (Task #198) lands first as the schema-spec foundation.
- **Conflict resolution when two profiles register the same catalog key or the same bridge-surface name.** Current `register_attested_root()` uses first-wins-with-warning. The profile loader will use the same policy unless a stronger rule is needed; revisit if a real conflict surfaces.
- **Plugin profile sandboxing / security.** A plugin profile is loaded via ctypes; the plugin can do anything the calling process can do. `pip install audio-spectral` is the existing trust boundary (same as any other PyPI package). No additional sandbox is proposed. Document the trust model in the authoring guide.
- **Multi-version coexistence.** Can two installed profiles declare different `srmech_requires` ranges and coexist? Open question. Worst case: srmech refuses to load profiles outside its compatibility range; the user pins srmech to the intersection of the ranges or removes one profile.
- **Lazy vs eager profile discovery.** Walk entry-points at srmech import time (eager, slight cold-start cost) or on first `srmech.list_profiles()` call (lazy, cheaper cold start but slightly less discoverable). Default proposal: lazy on first call. Open for revision.

## 9. Prerequisites — what must land before any of this can ship

1. **Task #198 — `srmech.amsc.tool_schema`** (in queue as pending). Provides the LLM-friendly AMSC introspection layer that the profile schema declares into. Without it the profile descriptor has no formal target.
2. **A draft `srmech_profile.toml` JSON Schema** alongside this ADR — the strawman §3 schema rendered as a formal validator file so profile authors can `jsonschema`-validate their TOML.
3. **Versioning policy for the profile schema itself.** The TOML carries `version = "0.27.0"` (the *profile's* version) but the *schema's* version is implicit. We need a `srmech_profile_schema_version = "1.0"` top-level field so srmech can refuse to load profiles declared against unknown schema versions. Add to §3 before locking.

## 10. Consequences

### Positive

- srmech becomes a true substrate; the third-party publishing path is opened.
- Domain packages keep their own version cadence + cibuildwheel matrices + native libraries. No forced collapse.
- The MPM discipline (citation attestation, NDJSON ground-proof) propagates by inheritance — any profile gets it free.
- LLM-friendly introspection (via Task #198) lets future Claude sessions discover what's installed and what each profile offers without reading every package's docs.

### Negative

- More moving parts. The profile-loader is a new failure surface; ctypes binding mistakes in plugins can crash the host process.
- Schema migration costs. Anything we get wrong in `srmech_profile.toml` v1 has to be migrated (`profile_schema_version` field is the escape hatch).
- Discovery latency. `importlib.metadata.entry_points()` enumeration is fast but not free; lazy-load helps. Measure on Pyodide where filesystem walks are slow.

### Neutral

- The current `register_attested_root()` API remains; it becomes one of several mechanisms (profile loader being the new ergonomic one). No deprecation of existing surface.

## 11. Decision

**Adopt the two-tier profile pattern as the design target for Task #199.** Implement in the order:

1. This ADR + the JSON Schema for `srmech_profile.toml`.
2. Task #198 (`tool_schema`).
3. srmech v0.3.0 with the profile loader + the `srmech.profile()` API + auto-discovery of `srmech.profiles` entry-points (no consumer yet).
4. chess-spectral simple-profile POC.
5. ephemerides-spectral plugin-profile POC.
6. antikythera-spectral simple-profile declaration.
7. Third-party authoring guide.

Skip steps at your peril.

## 12. Roadmap touchpoints beyond this ADR

Things this ADR doesn't directly own but which it makes more
urgent to think about:

- **Task #209 — srmech extracted into its own repository upon
  maturity.** The profile pattern this ADR specifies pushes
  srmech further into the role of *substrate* — a package that
  third-party domain authors (audio-spectral, biology-spectral,
  …) build on. As that role solidifies, hosting srmech inside a
  monorepo whose root identity is the EMDR firmware project
  becomes increasingly awkward for outside contributors and for
  academic citation. The trigger for extraction is profile-pattern
  maturity: ≥1 third-party consumer in the wild, semantic v1.x
  stability, and decoupled CI/CD. Tracked separately so this ADR
  can land independently.

- **A profile authoring guide** (`docs/srmech/PROFILE_AUTHORING_GUIDE.md`)
  becomes the load-bearing onboarding document for third-party
  authors. Written after the chess + ephemerides POCs surface
  the practical sharp edges.

- **CITATION.cff at the srmech level** (currently only at the
  monorepo level per Task #188). Once profiles exist, citing srmech
  vs citing a profile vs citing a profile's plugin needs to be
  cleanly distinguishable. Probably a follow-up ADR after
  Task #188 lands.

## 13. References

- Task #197 — AMSC-to-srmech refactor (the substrate's existing scope).
- Task #198 — srmech.amsc.tool_schema (the prerequisite for this ADR).
- Task #199 — Config-driven srmech profile pattern (this ADR is its design).
- `docs/srmech/srmech_research_notebook.md` §0 — three-layer architecture; profiles live at L1+L2 boundary.
- `docs/srmech/CLAUDE.md` — session-level brief on srmech's current state and conventions.
- ephemerides-spectral's `_native_bip.py` — model of the ctypes binding pattern a plugin profile will follow.

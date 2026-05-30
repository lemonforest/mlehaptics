# srmech bug-fix wishlist — for the maintainer (2026-05-29)

**What this is:** a clean, prioritized, sendable distillation of `UPSTREAM_NOTES.md §10` — every srmech-mcp / package / docs issue the RBS-LM research subtree has surfaced by exercising the surface for real work. Verified against **srmech 0.5.0rc14** (TestPyPI; installed clean outside the source tree; `HAS_NATIVE=True`, ABI = 3).

**Discipline note:** per `[[feedback_upstream_srmech_fixes_as_research_notes]]`, this subtree **never edits the srmech package** — issues are logged here and handed upstream. This file is the hand-off artifact. UPSTREAM_NOTES §10 is the long-form record with full repro context; this is the short list.

**The core surface is correct.** This is a punch-list, not a complaint: `dense_laplacian` → exact D−A; `jacobi_eigvals` → exact eigenvalues; `klein4_similarity` → exact 7/8; the whole `qm.*` layer computed bit-exact (γ₅²=I, Weyl projectors, su(2)/su(3) Casimirs, Weinberg residual all 0.0). The items below are wrapper-drift, schema-gen, naming, and one catalog gap.

| severity | meaning |
|---|---|
| 🔴 **BUG** | tool is uncallable / silently wrong / breaks determinism |
| 🟡 **SCHEMA/NAMING** | callable but the schema or name misleads; trips correct callers |
| 🟢 **ENHANCEMENT** | works as designed; a surface addition would unlock new work |

---

## 🔴 BUGs

### W1 — `naming_lookup` (MCP) is uncallable: wrapper kwarg drift  *(§10.1, OPEN)*
- **Repro:** `mcp__srmech__srmech_amsc_naming_lookup(key=..., entries=[[k,v],...])` → `TypeError: lookup() got an unexpected keyword argument 'entries'`.
- **Root cause (confirmed rc14):** the package fn is `naming.lookup(key, pairs=...)`; the MCP wrapper advertises/forwards `entries=`. The names are out of sync, so the tool **always errors**.
- **Fix:** align the wrapper param to `pairs=`. **And** add a CI parity smoke-test that *every* `tool_schema` entry is callable with its advertised kwargs — this class of drift would have been caught automatically (this ask is cross-cutting; see W7).

### W2 — `*_random` (MCP) cannot be seeded over JSON-RPC → non-reproducible  *(§10.2, FIXED in rc14 package; verify MCP wrapper)*
- **Repro:** two `klein4_random(D=16)` MCP calls returned different vectors; the only randomness param was `rng: numpy.random.Generator`, which **cannot cross JSON-RPC** → no determinism through MCP. This **breaks srmech's own bit-exact / attestation discipline** for any MCP-driven cascade using a `*_random`.
- **Status:** the **package** is fixed — `klein4_random(D, rng=None, seed: int|None=None)` (integer `seed` confirmed in rc14 signature). **Remaining:** confirm the **MCP wrapper** exposes `seed:int` for `klein4_random` *and* the other `*_random` surfaces (`polar_random`, etc.). **Re-confirmed live 2026-05-30 (F182): the `klein4_random` MCP schema STILL exposes only `rng` (a numpy object), no `seed` — it remains non-reproducible via MCP; the wrapper fix has not yet shipped.**

---

## 🟡 SCHEMA / NAMING

### W3 — non-JSON Python types leak into auto-generated MCP schemas  *(§10.3, OPEN)*
- **Symptom:** schema params typed as `numpy.random.Generator` (rng), `bytes`, `SpectralHandle` (e.g. `naming_lookup`, `spectral_similarity`) — none JSON-serializable. Arrays/lists coerce fine; object/bytes params are ambiguous or unusable over JSON-RPC. (This is the root cause shared with W2.)
- **Fix:** the schema generator should map non-serializable params to serializable surrogates — `rng`→`seed:int`; `bytes`→base64 `str` (documented encoding); `SpectralHandle`→opaque handle id — or mark them MCP-excluded.

### W4 — `sha256_bytes` returns a hex STRING, not bytes  *(§10.6.1, OPEN)*
- **Symptom:** `srmech.amsc.format.sha256_bytes(b)` returns a 64-char hex `str` despite the name. Callers expecting `bytes` (`int.from_bytes(...)`) break; must use `int(h[:8], 16)`. Behaviorally fine, but the name says "bytes."
- **Fix:** docstring clarification, or a `sha256_hex` alias / a `sha256_raw`→`bytes` companion.

### W5 — `klein4_bundle` even-count behavior vs prior "odd-only" note  *(§10.6.2, CONFIRM)*
- **Symptom:** in rc14, `srmech.amsc.hdc.klein4_bundle(*vectors)` accepts an **even** count with no odd-count enforcement / no tie-break error. Earlier guidance held that `klein4_bundle` "needs an ODD count (majority tie-break)."
- **Ask:** confirm the intended even-count tie-break semantics and document them. (Bears on a downstream pad-not-drop fix that assumed odd-only; if even is handled natively the pad is unnecessary.)

### W6 — `_native` ABI attribute naming  *(§10.7.3, MINOR — SUPERSEDED in rc18 by the profile-loader; see W12)*
- **Symptom:** `srmech._native` exposes `NATIVE_ABI_VERSION` and `EXPECTED_ABI_VERSION` (both = 3), **not** a top-level `ABI_VERSION`; `_native.ABI_VERSION` raises `AttributeError`.
- **Fix:** add an `ABI_VERSION` alias or document the two names.

### W6b — `weak_mixing_angle` returns radians, not sin²θ_W  *(§10.7.4, DOC-ONLY — not a defect)*
- `srmech.qm.sm.weak_mixing_angle` returns θ_W in **radians** (atan2(g′,g) ≈ 0.50225), not sin²θ_W. Documented behavior; a docstring emphasis would stop callers mis-reading the return as sin² (derive sin²θ_W = sin(θ_W)² ≈ 0.231, PDG).

### W6c — docs reference a non-existent `srmech.cosmos` module  *(§10.7.2, DOC)*
- There is **no `srmech.cosmos`** module in rc14 (`ModuleNotFoundError`); CMB data lives at `srmech.amsc.attested.cmb_*`. (Our own docs named `srmech.cosmos` and are corrected.) If srmech's own README/docs reference `srmech.cosmos`, fix to `srmech.amsc.attested.cmb_*`.

---

## 🟢 ENHANCEMENTS (surface additions)

### W7 — parity smoke-test in CI (cross-cutting; would have caught W1)  *(§10.1/§10.5)*
- A test that asserts every `tool_schema` entry is callable with its advertised kwargs against a trivial fixture. Catches wrapper/signature drift (W1) and serialization mismatches (W3) at build time.

### W8 — pass-by-handle (`SpectralHandle`) MCP surface for array chaining  *(§10.4, DESIGN)*
- Array ops return full JSON (`dense_laplacian` → n×n nested list; `jacobi_eigvals` → list). Chaining (Laplacian→eigvals) round-trips the whole array; bulk per-token work is payload-heavy. A pass-by-reference handle surface would make MCP chaining viable for larger arrays. (Consistent with MCP-as-interactive-surface today; package is the bulk path.)

### W9 — parity-odd CMB catalog (EB/TB) and/or birefringence-β posterior  *(§10.7.1, CATALOG GAP)*
- `srmech.amsc.attested.cmb_*` ships **TE/EE/BB only** (parity-EVEN). There is **no EB/TB** (parity-ODD) observable and **no cosmic-birefringence-β posterior** — the *only* chirality observable at the cosmic band is the one not shipped. This left a parity-odd-cosmology research front unresolvable srmech-native.
- **Ask:** a `cmb_parity_odd_spectra` catalog (EB/TB) and/or an attested birefringence-β posterior, attestable to e.g. Eskilt–Komatsu 2022 (arXiv:2205.13962) / Minami–Komatsu 2020 (arXiv:2011.11254).

### W10 — Spin(8) triality operator (8_v ↔ 8_s ↔ 8_c rep-map)  *(✅ RESOLVED — landed + acceptance-validated bit-exact in 0.5.0rc18; F192 / UPSTREAM §10.8)*
- srmech ships Klein-4 (two Z₂ chirality axes = Class C) and cyclic mod-n (Class I), but **no operator for Spin(8) triality** — the order-3 outer automorphism (S₃; Z₃ cyclic core) that permutes the three inequivalent 8-dim reps (vector 8_v, spinors 8_s/8_c). It is the *defining* structure of D₄ = 𝔰𝔬(8) and is load-bearing for the 28D arc (it underlies three-generation / Higgs-Yukawa octonion-SM models: Boyle arXiv:2006.16265, Todorov arXiv:1911.13124).
- **Ask:** a `triality` op (the S₃ rep-permutation / the cyclic 8_v→8_s→8_c map) under `srmech.qm` or `srmech.amsc.hdc`, so the triality-shadow hypothesis (F182) is testable in-framework rather than only reasoned about.

### W11 — A–N → g₂ embedding / labeling operator  *(NEW — F197; the analogue of W10 for the A–N partition)*
- The triality op (W10) let us compute that the **A–N 14 = G₂ = su(3)[8] ⊕ 3 ⊕ 3̄** (F197), confirming the I/C/J↔B/H/N role-swap at the **triad** level. But the **per-operator A–N → g₂ assignment** (which specific class A…N is which g₂ generator / which 3-vs-3̄ component) is **not shipped**, so the **within-triad** operator pairing (does the chiral flip send I→B, C→H, J→N specifically?) is not yet computable (F197 §4).
- **Ask:** an attested map **A–N class → g₂ generator(s)** (e.g. `srmech.qm.so8.an_embedding()` returning the 14 *named* generators in the su(3)⊕3⊕3̄ basis), so the operator-level chiral-flip swap (F191) becomes a measurement, not a reading.

### W12 — native-status verification recipe for the rc18 profile-loader  *(NEW — F192 / §10.8.3; supersedes W6) — MEDIUM (top-level status-surface gap; native IS verifiable via the AMSC shim — see correction)*
- rc18 replaced the *top-level* `HAS_NATIVE` bool + `_native.NATIVE_ABI_VERSION` surface with a **profile-loader** (`srmech.profile(name)`, `list_profiles()`, `ProfileStatus`, `AbiMismatchError`, `warmup_all()`; ctypes-loaded `_native/libsrmech.so`). **A bare `pip install srmech==0.5.0rc18` shows `list_profiles() == {}`.** **CORRECTION (2026-05-30, issue #733): native status IS still verifiable** — `from srmech.amsc._native import HAS_NATIVE` (= True) and `NATIVE_ABI_VERSION` (= 3) work in rc18 (the AMSC shim kept them). The real gap is narrower than first stated: the *top-level* surface doesn't expose a bare-install status, and the old top-level "verify `HAS_NATIVE=True`" recipe effectively moved down into the AMSC shim.
- **Ask:** (a) document the rc18 native-status check (the working recipe is `from srmech.amsc._native import HAS_NATIVE, NATIVE_ABI_VERSION`; clarify whether `list_profiles()` is also expected to populate); (b) clarify whether a bare install should **auto-register a default native profile** (currently none); (c) ideally surface a one-call top-level status (e.g. `srmech.native_status()`) mirroring the AMSC-shim flag for downstream rc-verification.

### W13 — `srmech mcp emit-mcpb`: a user-invoked CLI that emits a ready-to-install Claude Desktop bundle from introspection  *(NEW — desktop-extension distribution; ENHANCEMENT; user direction 2026-05-30)* — **filed [#749](https://github.com/lemonforest/mlehaptics/issues/749) · milestone MS #19**
- **Context:** Claude Desktop installs MCP servers as **`.mcpb`** bundles (formerly `.dxt`; a ZIP + a root `manifest.json`; spec: `anthropics/mcpb` / `modelcontextprotocol/mcpb`). srmech already holds every value a manifest needs — `tool_schema.get_tool_schema()` (the `mcp_callable` tool set), `__version__`, and the `srmech.mcp._cli` entry point — so the manifest should be **derived by introspection, never hand-authored** (no magic numbers: no frozen tool list, no baked interpreter path, no hardcoded version).
- **Ask:** add a **user-invoked** CLI subcommand — `srmech mcp emit-mcpb [--out .] [--type uv|python] [--manifest-only] [--name srmech]` — that:
  - introspects tool_schema + `__version__` + entry point → writes a spec-valid `manifest.json`;
  - packs a ready-to-install **`srmech.mcpb`** into the **cwd** using stdlib `zipfile` — **NO Node / `@anthropic-ai/mcpb` toolchain required** — and prints the absolute output path so the user can find it trivially;
  - defaults to **`server.type: "uv"`** (declare srmech as the dependency → `uv` fetches the correct platform wheel from PyPI at install; path-/version-agnostic; solves the spec's "Python bundles cannot portably bundle compiled dependencies" limitation — i.e. the `libsrmech` native wheel), with **`server.type: "python"` + `user_config.python_path`** as the documented offline/air-gapped fallback;
  - `--manifest-only` emits just `manifest.json` (+ a `server/` shim) for users who want to edit/repack.
- **Explicitly NOT:** an auto-emit on `pip install` / wheel-build side-effect (it is a deliberate user action), and **NOT** a baked `sys.executable` in `mcp_config.command` (that reintroduces the exact `/tmp`-reboot brittleness we hit with the Claude Code `.mcp.json` — a magic number *and* a portability bug).
- **Provenance fit:** the emitted manifest can carry `__version__` + a `tool_schema` hash as an MPR-style attestation block — bundle provenance, consistent with the AMSC ethos.
- **Gold gate:** the `uv`-type bundle resolves srmech from an index `uv` can reach → **live PyPI**, so the emitted bundle is naturally gold-version-stamped (no rc-as-SoT issue; same principle as `.mcp.json`).
- **Verified now (2026-05-30):** the server end is already healthy — `srmech-mcp` (stdio) does `initialize` + `tools/list`=173 (incl. so8/triality/klein4) + `tools/call` against the 0.5.0rc18 venv. Only the *emit/pack* surface is missing.

---

## Priority for the maintainer (suggested)
1. **W1** (uncallable tool) + **W7** (the CI test that prevents its whole class) — highest leverage.
2. **W12** (native-status recipe) — rc18 moved the native-status surface into the AMSC shim (`srmech.amsc._native.HAS_NATIVE`, still True); the top-level profile-loader just lacks a bare-install status. Verifiable today (correction #733); the ask is to surface/document it at the top level.
3. **W2 / W3** (determinism + schema-gen) — confirm the MCP wrapper exposes the now-landed `seed`; fix the surrogate mapping.
4. **W4 / W5 / W6b / W6c** — cheap docstring/naming/alias fixes (W6 superseded by W12).
5. **W8 / W9 / W11 / W13** — enhancements; schedule with the chaining / parity-cosmology / A–N-embedding work. **W13** (desktop `.mcpb` emit) pairs with the gold cut — its `uv`-type bundle wants srmech on live PyPI.
6. ✅ **W10** (triality op) — **DONE** in rc18 (F192); **W2** seed — **DONE** package-side (confirm MCP wrapper).

---

*Verified env: srmech **0.5.0rc18** (TestPyPI), clean venv outside source tree. Native: `_native/libsrmech.so` ships, but native dispatch is now **profile-gated** (W12) — `list_profiles() == {}` on a bare install, so HAS_NATIVE/ABI can no longer be read the old way. W10 (triality) landed + acceptance-validated bit-exact (F192). Long-form repro + context: `UPSTREAM_NOTES.md §10` (§10.8 = rc18). Compiled from the RBS-LM research subtree per `[[feedback_upstream_srmech_fixes_as_research_notes]]` — no package edits made from here.*

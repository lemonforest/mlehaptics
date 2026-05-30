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

### W6 — `_native` ABI attribute naming  *(§10.7.3, MINOR)*
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

---

## Priority for the maintainer (suggested)
1. **W1** (uncallable tool) + **W7** (the CI test that prevents its whole class) — highest leverage.
2. **W2 / W3** (determinism + schema-gen) — confirm MCP wrapper exposes the now-landed `seed`; fix the surrogate mapping.
3. **W4 / W5 / W6 / W6b / W6c** — cheap docstring/naming/alias fixes; clear a lot of caller friction.
4. **W8 / W9 / W10** — enhancements; schedule when the chaining / parity-cosmology / triality work is prioritized.

---

*Verified env: srmech 0.5.0rc14 (TestPyPI), clean venv outside source tree, `HAS_NATIVE=True`, ABI 3. Long-form repro + context: `UPSTREAM_NOTES.md §10`. Compiled from the RBS-LM research subtree per `[[feedback_upstream_srmech_fixes_as_research_notes]]` — no package edits made from here.*

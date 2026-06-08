# srmech bug-fix wishlist — for the maintainer (2026-05-29)

> **Consolidated GitHub tracker: [#928](https://github.com/lemonforest/mlehaptics/issues/928)** (`srmech` label) — one tracker for all W1–W18 (bugs · schema · enhancements · new ops), built in the separate srmech session. This file is the long-form source; #928 is the at-a-glance status board.

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

### W14 — single-arg `atan_series_truncate` (and `log1p_series_truncate`) silently diverge for |x|>1 — wants argument-reduction or a clean domain error  — ✅ **RESOLVED in 0.7.5rc1** (verified clean venv, cwd outside source tree): both now raise a **clean `ValueError`** past the convergence radius — `atan_series_truncate: |p/q| must be ≤ 1 (Taylor radius…)` and `log1p_series_truncate: p/q must be in (-1, 1] …` — instead of returning a divergent rational (the §15.1/§18 Class-K-style "refuse out-of-domain loudly" option). In-domain values unchanged (`atan(½)`/`log1p(½)` exact). **Perf addendum: PARTIAL** — `atan2`×200 now 756 ms (was ~1095 ms, ~31% faster) but still per-call series; a vectorised/native atan2 remains a *nice-to-have*, NOT a blocker. *(NEW — F540 / circle-shelf work; LOW–MEDIUM; correctness-of-range, not wrong-within-range)*
- **Observed (srmech 0.7.4, clean probe):** `srmech.calculus.atan_series_truncate(num, den, 30)` is accurate for |x|≤½ but is already off at the radius-of-convergence boundary (`atan(1)` 30-term → 0.79346 vs true 0.78540) and **blows up past it** — `atan(2/1)` → ~3.0e16, `atan(5/1)` → ~6.8e40. Same family as the already-hit `log1p_series_truncate(799,…)` blow-up (F526/F528). This is the **naive Taylor series' radius of convergence = 1**, not a coding defect — but the op gives **no warning and no reduction**, so a caller passing |x|>1 gets a huge garbage rational silently.
- **Already-correct sibling:** the **two-arg `srmech.calculus.atan2(y, x, *, terms=40)` is range-safe** (verified full-circle: matches `math.atan2` in all four quadrants, |x|>1 fine) because it reduces by quadrant. So the fix pattern already exists in the module.
- **Perf addendum (F542):** `atan2` is also **slow per call** — 200 scalar calls (40-term series each) took **~1095 ms** in the F542 circle-volume routing (vs **0.47 ms** for the rest of the routing); `np.arctan2` over the same 200 angles is sub-ms. The cost is one-time (cache the angles as kernel metadata) so it does not gate per-query work, but a **vectorised / lower-default-`terms` / native** atan2 would remove a real wall-clock wart from any per-word angular read-out. Pairs with the correctness ask above (one improved series op fixes both).
- **Ask:** give the **single-arg** `atan_series_truncate` standard argument-reduction (`atan(x)=π/2−atan(1/x)` for |x|>1; the `atan(x)=2·atan(x/(1+√(1+x²)))` halving for the slow boundary) and `log1p_series_truncate` a range-split so |x|≥1 is supported — **or**, minimally, raise a clean Class-N domain error past the convergence radius instead of returning a divergent rational (mirror of the §15.1/§18 Class-K contract-error pattern: refuse the out-of-domain input loudly rather than answer it wrongly).
- **Downstream note (no result affected):** the RBS-LM circle-shelf scripts (CIRCLESHELF/MOEHELIX/MULTIMODE, F535/F537/F539) used `np.arctan2` for the full-circle embedding — a srmech-first slip; F540 switched to the range-safe `srmech.calculus.atan2`. Angles are identical to machine precision, so prior findings' numbers stand; this is a tooling-purity correction, logged for completeness.

### W15 — (optional, LOW) a Cayley-loop **closure / orbit / min-generating-set** helper on top of `cayley_dickson`  — ✅ **RESOLVED in 0.7.5rc1** (verified): `cayley_dickson.closure(dim, gens)`, `left_orbit(dim, start, gen)`, `min_generating_set(dim, units)` all shipped + correct — octonion closure 16 / single-gen 4 / min-gen 3; quaternion(dim=4) 8 / 2; complex(dim=2) 1. Semantics are **carrier-strict + documented** ("min k spanning the FULL 2·dim loop"), so it raises a clean `ValueError` on an ill-posed cross-carrier request (e.g. quaternion units against the dim-8 octonion loop) — correct, not a bug. *(NEW — F544/F546 loop-shelf work)*
- **Context (NOT a gap in the core):** the loop algebra is **already srmech-native** — `srmech.amsc.cascade.cayley_dickson` ships `cd_basis_product(dim,i,j)` (the signed basis product), `cd_mult`/`cd_conjugate`/`cd_norm_sq`, `left_mult_matrix`/`left_mult_kernel`, `is_division_algebra_dim`, `sedenion_zero_divisor_witness`. F544/F546 originally hand-rolled an octonion Fano table — a srmech-first slip, now **fixed** to call `cd_basis_product` (verified: identical structural results — single-generator orbit 4, full octonion loop 16, min-generating-set 3 (𝕆) / 2 (ℍ)).
- **The only thin thing missing** (built in ~10 lines on `cd_basis_product` for F544/F546): the *combinatorial* layer over the basis product — **`closure(generators)`** (the sub-loop a generator set spans, by BFS), **`orbit(element, generator)`** (the left-multiplication cycle), and **`min_generating_set(units)`** (the loop's navigation dimensionality). These are the loop analogues of the cyclic-group orbit machinery and would aid any loop-shelf / Cayley-graph traversal work (F541/F544/F546 and successors).
- **Ask (optional):** add `cayley_dickson.closure(dim, generator_idxs) -> set`, `cayley_dickson.left_orbit(dim, start_idx, gen_idx) -> list`, `cayley_dickson.min_generating_set(dim, unit_idxs) -> int`. Low priority — trivially derivable from `cd_basis_product`, logged for completeness so the loop-shelf arc has a named home for it rather than re-deriving each time.

### W16 — (optional, LOW) a `the_one`-trajectory / `the_one`⊗`kuramoto` ergonomic surface  *(NEW — F560 self-driven dynamic wave)*
- **Context (already buildable):** F560 self-generates a substrate-native DYNAMIC driver wave by coupling `cascade.kuramoto_step` (the coupled-oscillator dynamic) to `cascade.the_one` (the wave) — k=7 oscillators evolve, their mean-field phase indexes `the_one`, and `the_one.to_numpy()[4]` is the wave. Works today; no version bump needed.
- **Ask (optional):** a thin convenience `cascade.the_one_trajectory(sigma, theta0, omega, *, steps, coupling, dt, component=4) -> List[float]` that runs the kuramoto→the_one loop in one call (and returns the order-parameter |R| trace) — purely ergonomic, so the "the_one with dynamic waves entirely" pattern has a named home rather than being hand-wired each time. LOW priority; the primitives are all present.

### W17 — (MEDIUM; user-flagged 2026-06-08) a **coupled-wave / quadrature** driver surface — the EM (E,B) full-chirality drive  *(NEW — F577 verb-flip fix)*
- **Context (the finding):** a FLAT scalar driver gates direction by `sign(wave)`, which flips hard at every zero-crossing (2/cycle) — and the VERB is the chiral/relational element, so a flat drive injects "huge verb flips" (a STRUCTURE error). A COUPLED quadrature wave (E = sin, B = cos, 90° apart — exactly EM) rotates monotonically → **0 hard reversals**; the verb-direction is the smooth rotation, not the flipping 1-bit sign. Framework reading (F552 on the driver): flat sign = chirality-COLLAPSED 1-bit (Class-K); coupled (E,B) = FULL-chirality 2D rotation (γ₅/Klein-4 — the 4 quadrants (signE,signB) ARE the 4 sectors). Verified in F577 via `srmech.calculus.{sin,cos}_series_truncate` (degree-mod range reduction, π≈355/113) — works today but hand-wired.
- **Ask:** a first-class coupled-wave op, e.g. `cascade.coupled_wave(theta, *, components=("sin","cos")) -> (E, B, handedness, klein4_quadrant)` — return the quadrature pair + the rotation handedness (stable) + the Klein-4 quadrant — so the full-chirality drive is a named primitive instead of being reconstructed per script. Composes with W16 (the trajectory surface) and the Klein-4 HDC ops. This is "drive with the full chirality, not its collapsed sign."

### W18 — (MEDIUM; user-flagged 2026-06-08, "an efficient way to multi stream for building better sentences") an **efficient multi-stream MULTIPLEX** driver  *(NEW — F573/F577 multi-stream re-aimed at correct structure)*
- **Context (the finding):** driving the Story Teller with N wave INSTANCES (N=3 triad / 7 heptad) and a COVERAGE combiner (MULTIPLEX — wave `t mod N` drives step `t`) reaches more of the manifold; the user's correction (F577): the multi-stream is for **correct sentence STRUCTURE** (clause-role assignment, S-V-O), NOT richness/embellishment. Currently hand-rolled per script (the multiplex loop + the N `the_one`/quadrature instances), which is the inefficient part.
- **Ask:** an efficient multi-stream surface, e.g. `cascade.multiplex_streams(streams, *, mode="roundrobin"|"pickbest"|"superpose", roles=None) -> driver` — run N wave streams and recombine them, with an optional `roles` map binding each stream to a clause role (subject/verb/object) so the N streams BUILD correct structure rather than just covering. Pairs with W17 (each stream a coupled wave) — the verb-stream then carries a stable (non-flipping) chirality. This is the "efficient way to multi-stream for building better sentences."

---

## ⏩ Carried forward to the srmech-build session (user direction 2026-06-08: "we build them in another session")

The maintainer/build session should pull these forward. **Resolved this session:** W14 (atan/log1p domain error + atan2 perf) ✅, W15 (Cayley closure/orbit/min-gen) ✅ — both in 0.7.5rc1. **Still open / new asks, by priority for the sentence-structure arc:**
- **W17** (coupled-wave / EM quadrature driver) — the verb-flip / correct-structure fix (F577). Buildable today via `srmech.calculus` sin/cos; the ask is a named first-class op.
- **W18** (efficient multi-stream multiplex, role-bound) — "an efficient way to multi-stream for building better sentences" (F573/F577). The hand-rolled multiplex is the inefficiency.
- **W16** (the_one-trajectory ergonomic) — LOW; composes with W17/W18.
- W1/W7 (uncallable tool + the CI parity test) and W12 (native-status recipe) remain the highest-leverage non-arc items.

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

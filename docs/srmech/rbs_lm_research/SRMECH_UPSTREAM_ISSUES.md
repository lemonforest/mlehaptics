# srmech — paste-ready upstream issue bodies (2026-05-30)

Generated from `SRMECH_BUGFIX_WISHLIST.md` / `UPSTREAM_NOTES.md §10`. Each block below is a self-contained GitHub issue (title + labels + body) — copy from the heading down to the `═══` divider. **Env baseline:** srmech **0.5.0rc18** (TestPyPI), clean venv outside the source tree, Python 3.14, numpy 2.4.6.

**Verification status:** package-side repros are **verified on rc18**. MCP-side items (W1, W3, and the W2 *wrapper* half) are marked **"last observed — re-verify on rc18 MCP"** because the srmech-mcp server was offline when these were drafted. No package edits were made from the research subtree (`[[feedback_upstream_srmech_fixes_as_research_notes]]`).

═══════════════════════════════════════════════════════════════════════

## W12 — [bug] rc18: native dispatch is unverifiable from a bare install (profile-loader registers no profile)
**Labels:** `bug`, `packaging`, `native`, `priority:high`

### Summary
rc18 replaced the `HAS_NATIVE` bool + `_native.NATIVE_ABI_VERSION` with a profile-loader (`srmech.profile(name)`, `list_profiles()`, `ProfileStatus`, `AbiMismatchError`, `warmup_all()`; ctypes-loaded `_native/libsrmech.so`). A bare `pip install srmech==0.5.0rc18` registers **no profile**, so there is no documented way to confirm the C backend is loaded + ABI-matched + actually dispatching (vs the pure-numpy fallback). The prior rc-verification recipe ("check `HAS_NATIVE=True`") no longer applies — which breaks the downstream TestPyPI-before-PyPI verification discipline.

### Environment
srmech 0.5.0rc18 (verified, this session).

### Reproduction
```python
import srmech
srmech.list_profiles()        # -> {}   (no profile registered on a bare install)
[a for a in dir(srmech) if 'nativ' in a.lower() or 'abi' in a.lower()]   # -> ['AbiMismatchError']  (no HAS_NATIVE)
import srmech.version as V; [a for a in dir(V) if not a.startswith('_')] # -> []
# the .so IS present:  <site-packages>/srmech/_native/libsrmech.so
# but `from srmech import _native; dir(_native)` exposes 0 functions (ctypes-loaded)
```

### Impact
Downstream packages and CI cannot assert "native is active" after install; the wheel ships `libsrmech.so` but dispatch status is opaque.

### Suggested fix
(a) Document the rc18 native-status check (how to confirm `libsrmech.so` is loaded + ABI-matched + dispatching); (b) consider auto-registering a default native profile on import, or document the explicit registration call; (c) ideally restore a one-call status, e.g. `srmech.native_status() -> {loaded, abi, dispatching}`.

═══════════════════════════════════════════════════════════════════════

## W1 — [bug] `naming_lookup` MCP tool is uncallable — wrapper kwarg drift (`entries=` vs `pairs=`)
**Labels:** `bug`, `mcp`

### Summary
The MCP tool `srmech_amsc_naming_lookup` advertises/forwards `entries=`, but the underlying package function is `naming.lookup(key, pairs=...)`. Every MCP call therefore raises `TypeError`.

### Environment
Last observed against the srmech-mcp surface (srmech 0.5.0rc8 / rc14). **Re-verify on the rc18 MCP server.** The package signature (rc18) confirms the correct kwarg is `pairs`.

### Reproduction
```text
# MCP:
srmech_amsc_naming_lookup(key=..., entries=[[k, v], ...])
# -> TypeError: lookup() got an unexpected keyword argument 'entries'
```
```python
# package evidence (rc18):
import inspect, srmech.amsc.naming as n
inspect.signature(n.lookup)   # -> (key, pairs=...)
```

### Suggested fix
Align the MCP wrapper parameter to `pairs=` (or rename). See W7 for the CI test that prevents this class.

═══════════════════════════════════════════════════════════════════════

## W7 — [ci] Add a tool_schema parity smoke-test (every advertised MCP tool callable with its kwargs)
**Labels:** `ci`, `mcp`, `testing`

### Summary
A CI test that asserts every `srmech.amsc.tool_schema` entry is callable with its advertised kwargs (against a trivial fixture) would catch wrapper/signature drift (W1) and JSON-serialization mismatches (W3) at build time.

### Suggested implementation
Iterate the `tool_schema` registry; for each entry, construct a minimal valid call from the advertised parameter schema; assert no `TypeError` and that all advertised params are JSON-serializable.

═══════════════════════════════════════════════════════════════════════

## W3 — [bug] Non-JSON-serializable types leak into auto-generated MCP schemas (`rng`, `bytes`, `SpectralHandle`)
**Labels:** `bug`, `mcp`, `schema`

### Summary
Auto-generated MCP schemas expose Python-native types that can't cross JSON-RPC: `numpy.random.Generator` (`rng`), `bytes`, and `SpectralHandle` (e.g. on `naming_lookup`, `spectral_similarity`). Lists/arrays coerce fine; object/bytes params are unusable over MCP. (Shared root cause with the W2 seed problem.)

### Environment
Last observed (srmech-mcp rc8 / rc14). **Re-verify on the rc18 MCP server.**

### Suggested fix
Map non-serializable params to serializable surrogates in the schema generator: `rng` → `seed:int`; `bytes` → base64 `str` (documented encoding); `SpectralHandle` → opaque handle id — or mark them MCP-excluded.

═══════════════════════════════════════════════════════════════════════

## W2 — [bug] `*_random` MCP determinism: confirm the wrapper exposes `seed:int` (package already fixed)
**Labels:** `bug`, `mcp`

### Summary
The **package** is fixed: `klein4_random(D, rng=None, seed: int | None = None)` (verified rc18). Remaining: confirm the **MCP wrapper** exposes `seed:int`. Last observed, the MCP schema exposed only `rng` (a `numpy.random.Generator`), which can't cross JSON-RPC → non-reproducible via MCP, breaking the framework's bit-exact/attestation discipline. Likely the same for `polar_random` and any other `*_random`.

### Environment
Package: rc18 (seed confirmed). MCP wrapper: last observed pre-rc18 — **re-verify on rc18 MCP.**

### Reproduction
```python
# package (rc18) — FIXED:
import inspect, srmech.amsc.hdc as hdc
inspect.signature(hdc.klein4_random)   # -> (D, rng=None, seed: int | None = None)
```

### Suggested fix
Ensure the MCP wrapper forwards `seed:int` for `klein4_random` and all `*_random` surfaces.

═══════════════════════════════════════════════════════════════════════

## W4 — [docs] `sha256_bytes` returns a hex `str`, not `bytes`
**Labels:** `docs`, `good-first-issue`

### Reproduction (rc18, verified)
```python
from srmech.amsc.format import sha256_bytes
type(sha256_bytes(b"x"))   # -> <class 'str'>  (64 hex chars, not bytes)
```
Callers expecting `bytes` (`int.from_bytes(...)`) must instead use `int(h[:8], 16)`. Behaviorally fine — the **name** says "bytes" but the return is a hex string.

### Suggested fix
Docstring clarification, or a `sha256_hex` alias / a `sha256_raw` → `bytes` companion.

═══════════════════════════════════════════════════════════════════════

## W5 — [docs] Document `klein4_bundle` even-count behavior (accepts even; earlier guidance said odd-only)
**Labels:** `docs`

### Reproduction (rc18, verified)
```python
from srmech.amsc import hdc
hdc.klein4_bundle([0,1,2,3], [0,1,2,3])   # 2 vectors (EVEN) -> returns OK, len 4; no odd-count tie-break error
```
Earlier guidance held that `klein4_bundle` needed an **odd** count (majority tie-break). rc18 accepts even counts with no error.

### Suggested fix
Confirm the intended even-count tie-break semantics and document them in the docstring.

═══════════════════════════════════════════════════════════════════════

## W6b — [docs] `weak_mixing_angle(g, g_prime)` returns radians (θ_W), not sin²θ_W
**Labels:** `docs`

### Note (rc18, verified)
`srmech.qm.sm.weak_mixing_angle(g, g_prime)` returns the Weinberg angle **θ_W in radians**, not sin²θ_W. Callers wanting the PDG value (sin²θ_W ≈ 0.231) must take `sin(θ_W)**2`. Documented behavior — **not a defect** — but a docstring emphasis would prevent mis-reading the return as sin².

═══════════════════════════════════════════════════════════════════════

## W6c — [docs] Remove/redirect any `srmech.cosmos` references (no such module)
**Labels:** `docs`

### Reproduction (rc18, verified)
```python
import srmech.cosmos   # -> ModuleNotFoundError
```
CMB data lives under `srmech.amsc.attested.cmb_*` (TE/EE/BB). If the README or any docstring references `srmech.cosmos`, redirect to `srmech.amsc.attested.cmb_*`.

═══════════════════════════════════════════════════════════════════════

## W8 — [enhancement] Pass-by-handle (`SpectralHandle`) MCP surface for array chaining
**Labels:** `enhancement`, `mcp`, `design`

### Summary
Array ops return full JSON over MCP (`dense_laplacian` → n×n nested list; `jacobi_eigvals` → list), so chaining (Laplacian → eigvals) round-trips the whole array and bulk work is payload-heavy. A pass-by-reference handle (`SpectralHandle`) would make MCP chaining viable for larger arrays. Consistent with MCP being the interactive surface (the package is the bulk path).

═══════════════════════════════════════════════════════════════════════

## W9 — [enhancement] Parity-odd CMB catalog (EB/TB) and/or cosmic-birefringence β posterior
**Labels:** `enhancement`, `catalog`, `cosmology`

### Summary
`srmech.amsc.attested.cmb_*` ships TE/EE/BB (parity-**even**) only. There is no EB/TB (parity-**odd**) observable and no cosmic-birefringence-angle (β) posterior — i.e. the one chirality observable at the cosmic band is the one not shipped, which left a parity-odd-cosmology question unanswerable srmech-native.

### Suggested addition
A `cmb_parity_odd_spectra` catalog (EB/TB) and/or an attested birefringence-β posterior, attestable to e.g. Eskilt–Komatsu 2022 (arXiv:2205.13962) / Minami–Komatsu 2020 (arXiv:2011.11254).

═══════════════════════════════════════════════════════════════════════

## W11 — [enhancement] A–N → g₂ embedding / labeling op (named generators in the su(3) ⊕ 3 ⊕ 3̄ basis)
**Labels:** `enhancement`, `qm`

### Summary
rc18's `srmech.qm.so8` / `triality` ops make it computable that the 14 A–N primitive classes = G₂ = `su(3)[8] ⊕ 3 ⊕ 3̄` (the stabilizer of an imaginary unit is su(3), dim 8; complement = 6). To go from the *triad-level* structure to the *per-operator* structure (which specific A–N class is which g₂ generator / which 3-vs-3̄ component), an attested embedding would help.

### Suggested addition
`srmech.qm.so8.an_embedding()` (or similar) returning the 14 **named** g₂ generators in the `su(3) ⊕ 3 ⊕ 3̄` basis, so the operator-level chirality structure becomes a computation rather than a labeling. (Downstream framework-research use of the A–N vocabulary.)

═══════════════════════════════════════════════════════════════════════

## ✅ W10 — RESOLVED in rc18 (confirmation / thank-you comment, not an open issue)
The Spin(8) **triality operator** landed in 0.5.0rc18 — `srmech.qm.octonion` (incl. `octonion_table_attestation`, an MPR-wrapped `cayley_dickson_from_H` convention), `srmech.qm.so8` (`so8_adjoint_basis`, `g2_subalgebra`), `srmech.qm.triality` (`triality_automorphism`/`swap`/`cycle`/`apply`/`companions`/`relation_residual`). Acceptance tests pass **bit-exact**: τ³ = I (residual 3.7e-15), **dim Fix(τ) = 14 = G₂**, dim Fix(swap) = 21 = 𝔰𝔬(7), so8 = 28, g₂ = 14, octonion `ij = −ji`. Implemented faithfully — thank you. (Closes the W10 wishlist item.)

═══════════════════════════════════════════════════════════════════════

*Compiled from the RBS-LM research subtree. Order/priority and full context: `SRMECH_BUGFIX_WISHLIST.md`; long-form per-item history: `UPSTREAM_NOTES.md §10`.*

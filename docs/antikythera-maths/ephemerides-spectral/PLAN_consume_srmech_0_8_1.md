# PLAN — ephemerides-spectral → srmech 0.8.1 (consume + genome-storage review)

**Date:** 2026-06-17 · **Target version:** `ephemerides-spectral 0.31.0rcN` (minor bump — consumes a major srmech graduation) · **Discipline:** TestPyPI-rc-first, then clean-tag → PyPI (human gate).

---

## Context

- **srmech 0.8.1 is LIVE on production PyPI** (MIT-licensed, numpy-free; carriers `Mat`/`Vec`/`HV` replaced ndarray; `[scientific]` extra gone; tools 310, ABI 3).
- **ephemerides-spectral** is at `0.30.0rc10`, pins **`srmech>=0.7.4`** in three files: `python/pyproject.toml:43`, `python/pyproject-pure.toml:58`, `python/ephemerides_spectral/srmech_profile.toml:40`.
- ephemerides keeps its OWN `numpy>=1.24` dependency (its `_research/laplacian.py` reference impl + `_native_bip.py` ctypes interop). srmech being numpy-free does NOT *force* ephemerides numpy-free — but **user direction 2026-06-17: "this must be numpy free also, we have the tooling in srmech to do it all"** → ephemerides numpy-removal is now a committed arc (Phase N below).

### Version-SSOT reality — there are **8** sites, not 3 (rc1 CI caught this)

The version string lives in EIGHT files that must agree; bumping only the "3 SSOT" the plan first listed left CI red on the floor-bump rc1:

| # | File | Token |
|---|------|-------|
| 1 | `python/pyproject.toml` | `version` |
| 2 | `python/pyproject-pure.toml` | `version` |
| 3 | `python/ephemerides_spectral/version.py` | `__version__` |
| 4 | `python/ephemerides_spectral/srmech_profile.toml` | `[profile].version` |
| 5 | `c/include/ephemerides_spectral.h` | `ES_VERSION_MINOR` + `ES_VERSION_STRING` (test_native_parity rebuilds the wheel from this; `native_version()` reads the compiled `es_version()`) |
| 6 | `python/ephemerides_spectral/_data/manifest.json` | `version` |
| 7 | `python/README.md` | `**Status: vX**` banner (test_readme_freshness) |
| 8 | `python/README.md` | Status-section `**vX** *(current)*` marker (test_readme_freshness) |

Plus the **3 srmech-floor pins** (sites 1, 2, 4 carry a `srmech>=…` / `srmech_requires` line).

## KEY FINDING — empirical introspection settles the "breaking changes" question

Static analysis (subagent) *guessed* the eigen-consumption sites would break (`eigvecs[:, 1]`, `-fiedler_vec`, `V[r][c]`). **Probed against the live srmech 0.8.1 — they DON'T.** The `Mat`/`Vec` carriers are a deliberate numpy-reflex sink and answer every idiom ephemerides uses:

| ephemerides idiom (file) | srmech 0.8.1 result |
|---|---|
| `dense_laplacian(n, edges, weights)` | OK → `Mat` (still takes `weights=None`) |
| `symmetric_eigendecompose(L)` | OK → `(Vec, Mat)` |
| `eigvals[1]` / `eigvals[i]` iterate / `len(eigvals)` | OK (Vec) |
| `V[:, 1]` 2-D **column slice** (hawaii/mars) | OK → `Vec` |
| `V[r][c]` nested / `V[r,c]` tuple index | OK → float |
| `fiedler_vec[i]` / `-fiedler_vec` negate / `len()` | OK (Vec) |
| `rational.log1p_series_truncate` → `(int,int)` ; `exp`/`sqrt`/`sin`/`cos`/`atan2`/`atan` → float | OK (unchanged) |
| `catalog.register_attested_root(path, *, source=)` ; `list_attested_sources()` → `{ok,n_sources,adapter_class,sources}` | OK (unchanged) |

**Conclusion: the core consumption is a near drop-in.** The real risk is only edge idioms the hot-site probe didn't reach — caught by running the FULL suite (Phase 0). The feared big-bang rewrite is mostly absent.

---

## Phase 0 — VERIFY (the real gate; do FIRST)

Install ephemerides (local) + **srmech 0.8.1 (from PyPI)** + numpy; run the **full ephemerides-spectral pytest suite**. Pin srmech to 0.8.1 explicitly. Green = the carrier idioms cover everything; any red = the precise remaining break (fix narrowly). Pay attention to: the 5 catalog consumers (`hawaii_chain`, `mars_tharsis`, `saturn_rings`, `solar_rotation`, `dynamical_regime`), the `_cascade.py` wrappers, and any `np.asarray(srmech_return)` / scipy hand-off.

## Phase 1 — floor bump + annotation honesty

- Bump `srmech>=0.7.4` → **`srmech>=0.8.1`** in all THREE (pyproject.toml, pyproject-pure.toml, srmech_profile.toml). Keep the two pyprojects congruent (CI guard).
- `_research/_cascade.py` return annotations say `Tuple[np.ndarray, np.ndarray]` but now return `(Vec, Mat)` — update to honest types (or a neutral `Tuple[Any, Any]`); cosmetic, not enforced, but keep introspection honest (`[[feedback_numpy_removal_must_preserve_carrier_format...]]` spirit).
- MIT relicense: srmech is now MIT; ephemerides relicenses GPL-3 → MIT under `[[project_srmech_subprojects_mit_monorepo_gpl3]]` (its own GPL→MIT flip across pyprojects + LICENSE + C headers, same as srmech 0.8.1rc1). **Deferred to a follow-up rc** — rc1 stayed honest (floor + version + README hygiene only); do NOT claim MIT in rc1's banner/CHANGELOG.

## Phase 1.5 — README hygiene (user direction 2026-06-17, SHIPPED in rc1)

User: "make sure our plan has pypi facing readme for ephemerides-spectral hygiene. it's quite dated and the first section has a long block in bold." The PyPI-facing README's first section crammed the **entire multi-version landing history into one giant bold `**Status:**` banner** (line 5, ~10 KB). Same pattern srmech hit at 0.8.1: collapse the banner to a single line; the per-version history already lives in the `## Status` section. **Done in rc1** (`_fix_readme_banner.py` one-shot, removed after). Further dated-prose passes (roster counts, shipped-roadmap drift) are a follow-up if a read finds staleness — but the freshness tests only enforce the mechanical markers (banner/current/changelog-completeness/CLI-body-names).

## Phase 2 — version bump + CHANGELOG (across all **8** SSOT)

`0.30.0rc10` → **`0.31.0rc1`** across all 8 SSOT sites in the table above (NOT just 3 — that's the rc1 CI lesson). CHANGELOG entry: "consume srmech 0.8.1 (numpy-free carriers — drop-in; floor `>=0.8.1`) + README hygiene". (MIT relicense lands its own follow-up rc, not rc1.)

## Phase 3 — ship rc1 → TestPyPI + verify

Hand-push `ephemerides-spectral-v0.31.0rc1` (rc → TestPyPI auto) once CI is green + PR merged. Verify in a clean venv: install ephemerides 0.31.0rc1 + srmech (resolve 0.8.1 from PyPI) + numpy; assert `ephemerides_spectral.__version__`, `srmech.__version__==0.8.1`, `srmech HAS_NATIVE`, `bridge.list_attested_sources()["n_sources"]`, and one ITN/cascade op (e.g. `gaussian_eigs_from_pairs` path + `find_itn_chains` / `predict_itn_accessibility`).

---

## Phase R1 — genome native-storage packaging (REVIEW / spike, go-no-go)

srmech `amsc.genome.*` = self-describing strand (`turns.bin`+`manifest.json`), chromosomes/genes, `.chr` bundles, `genome_pack/explode`, `genome_register_attested(chr_dir, amsc_root, *, source)` (one AMSC source per chromosome, composes the catalog).

**Tension (real):** a genome **leaf** is a fixed-width **Klein-4 `HV`** (sector-encoded bytes), `len(the_one)` wide — NOT a float array. ephemerides kernels are variable-width float coefficient sets (gravity SH to degree 2190; dynamical eigenvalue vectors; 6-float secular elements). Embedding raw float coefficients is lossy/awkward; padding to a max `leaf_dim` is wasteful.

**Recommended shape (subagent Option C):** the genome holds **provenance/metadata + references** (per-body chromosome, per-catalog gene; leaf = small descriptor: catalog key, epoch, `n_max`, SHA-256 of the coefficient archive), and `genome_register_attested` surfaces each as an AMSC source — coefficients stay in ephemerides' native tables. The genome becomes a **versioning/provenance checkpoint** ("which kernels were active at epoch T"), not a coefficient store.

**Smallest PoC:** `secular_elements` (51 bodies × 6 floats, fixed width) → one chromosome, `.chr` export, `genome_register_attested` → surfaces in `list_attested_sources`; round-trip equality. **Go-no-go output:** a spike report + decision; only ship a genome surface if it's clean and earns its place. **Likely a SEPARATE rc** (R-line), not rc1.

## Phase R2 — etak ↔ ITN unification (introspection CONFIRMED; class-TOML)

Introspection verdict (subagent): **etak navigation (PR #687 ETAK/BOARD/FLOCK triality, `mfo_spectral_research_notebook.md:6706`) and ephemerides `find_itn_chains` / `predict_itn_accessibility` (gateway-graph Laplacian Fiedler partition, `research/gateway_graph_laplacian.py` + `predict_itn_accessibility.py`) are the SAME structure** — hold an invariant reference frame (Class-C axis / Fiedler eigenbasis), the Class-L manifold's transport structure reveals accessible routes via Fiedler distance; Class-M bind = the k=3 triality. Shared primitives: **L (Laplacian) + C (frame) + M (bind)**.

**Per user direction** ("ephemerides may need its own `[class]` catalog TOML if we find ourselves wanting a new code path just for a different name"): do **NOT** add an `etak_*` code path alongside `find_itn_chains` — they're one cascade. Express the shared navigation cascade ONCE as an ephemerides **`[class]` catalog TOML** (`srmech.dsl.make_class` / `register_class_dir`), with `etak` and `itn` as two named views/methods over it. Prove with a DSL-class-vs-Python equivalence test (`[[feedback_prefer_config_driven_toml_classes]]`).

**= rc2 (user-confirmed 2026-06-17):** *"proceed with rc2 etak/ITN class TOML. where there were hard coded code paths that need deprecated, do not leave as no-op. remove functions that could have been done and will be done with TOML class catalog. this package was retrofit to srmech so there may be many duplicate code paths to clean out."* So rc2 is BOTH the etak/itn `[class]` TOML AND a duplicate-code-path purge. **Hard-remove**, do not no-op. Survey targets (from the Explore sweep):
- **dead `import numpy as np`** in `_research/_cascade.py:28` (unused) — delete.
- **pure-re-export trig wrappers** `_cascade.sqrt/sin/cos/atan2` (lines 59–86) — thin re-exports of `srmech.amsc.rational.*`; collapse callsites onto srmech directly, delete the wrappers.
- **`_best_rational_approx` triplicate** (`_research/itn_window.py:437`, `body_architecture.py`, `predict_itn_accessibility.py:136`) — consolidate; NOTE srmech's `rational.best_rational(num,denom,max_d)` takes an int-pair, NOT a float ratio/max_int, so it's not a blind drop-in — wrap once or adapt the signature deliberately.
- **`np.linalg.eigh` duplication** (`body_architecture.py:146`, `predict_itn_accessibility.py:79`) duplicates `srmech.amsc.laplacian.symmetric_eigendecompose` — route through srmech (CAREFUL: `predict_itn` calibration INTERCEPT/SLOPE were fit against that embedding; assert calibration invariants hold). This is also the first concrete **numpy-removal** step (feeds Phase N).
- ITN public surface to keep working: `bridge.find_itn_chains` (2497), `predict_itn_accessibility` (2723), `em_architecture` (2834).

---

## Phase N — make ephemerides-spectral numpy-FREE (MAJOR arc; user direction 2026-06-17)

**User:** *"this must be numpy free also, we have the tooling in srmech to do it all. thanks!"* The through-line of the 0.31.x rc series (and likely beyond). Mirror srmech's own numpy-removal journey (its rc69–rc134) but leaning on what srmech now ships: every continuous-math op is already a cascade of the 14 A–N classes over the `Mat`/`Vec`/`HV` carriers, all numpy-free. ephemerides routes its OWN math through those, then drops `numpy` from both pyprojects.

**North star:** `pip install ephemerides-spectral` pulls **no numpy**; a fresh numpy-ABSENT venv imports + runs the WHOLE package and the WHOLE test suite green. No `[scientific]`-style escape hatch; no `.to_numpy()` / `np.asarray(...)` bridge (`[[feedback_numpy_free_means_zero_numpy_no_bridges]]`). Flip by **connected component** (`[[feedback_numpy_free_means_zero_numpy_no_bridges]]`), not file-by-file with coercion glue.

**The live numpy surface (to inventory precisely in Phase N-0):**
- `_research/_cascade.py` — dead `import numpy` (rc2 deletes it) + the trig wrappers.
- `_research/laplacian.py` — the numpy reference eigensolver (duplicates `srmech.amsc.laplacian`; route through srmech's numpy-free engine).
- `_research/body_architecture.py`, `predict_itn_accessibility.py`, `itn_window.py` — `np.linalg.eigh`, `_best_rational_approx`, embeddings (rc2 starts these).
- `_native_bip.py` — ctypes interop marshals via numpy buffers in places; srmech already proved numpy-free ctypes marshalling (`array`/`memoryview`), reuse that pattern.
- The per-body catalogs (kinematics/dynamics/geodetic/EM/magnetic/fluid + the v0.24.x dynamical spectra) — sweep each for `np.`.
- The TEST suite — many tests `import numpy` as a differential oracle; rewrite numpy-free (stdlib `cmath`/`fractions`/`struct` or the srmech cascade as reference). A numpy-free module's test must itself be numpy-free (`[[feedback_test_for_numpy_free_module_must_itself_be_numpy_free]]`).

**Sequencing (decisive, batch by component — not dozens of micro-rcs):**
1. **N-0 inventory** — DONE. SHIPPED-package numpy surface (what makes `pip install` need numpy) = the `_research/*` codegen-copied modules + `ephemerides_spectral/{bridge,_native_bip}.py`. NOTE: the canonical `research/` tree has many more numpy files (bit_alu, encode_ant, gateway_graph_laplacian, …) but those are **research-only scaffold, NOT shipped** (not in `_INCLUDED_MODULES`) — they don't affect the installed package's numpy dep. Edit canonical + run codegen (`[[project_ephemerides_research_is_generated_copy_edit_canonical_run_codegen]]`).
2. **rc2** — DONE (0.31.0rc2, TestPyPI-verified). Cleared the ITN component: `_cascade` dead-import + `body_architecture` + `predict_itn_accessibility` → one `navigation_ops` cascade + the `GatewayNavigation` `[class]`. numpy gone from 4 modules.
3. **rc3** — `syzygy_window.py` dead `import numpy` removal (the last TRIVIAL shipped numpy). After rc3 the remaining shipped numpy is ALL ONE component (below).
4. **THE remaining component = the encoder / HD-lift / native-marshalling core** (~145 hits, calibration-sensitive, byte-exact-BIP-gated — its own dedicated effort, NOT a quick flip):
   - `_research/laplacian.py` (25) — complex128 Laplacian build (`np.zeros`/`np.pi`/`np.sqrt`/`np.cos`) + the LTI propagator `get_propagator`/`evolve_state` which uses **`scipy.linalg.expm`** (NO easy numpy-free matrix-exp — DECIDE: drop the LTI baseline as research-only, or implement a numpy-free matrix-exp). Consumed by ↓.
   - `_research/bip_instrument.py` (47) — the BIP integer-ALU encoder; reads the Laplacian diagonal → int64 residues. Its output is byte-exact (the package's core correctness guarantee).
   - `_research/ephemeris_reference_instrument.py` (35) — the reference encoder (breathing path via `get_dynamic_laplacian`).
   - `_research/bip_hd_lift.py` (22) — the complex64 HD lift.
   - `ephemerides_spectral/_native_bip.py` (16) — `encode_state`/`encode_at_jd` return **`np.uint32[N_BODIES]`** (the encoder's primary output type — flipping to `array('I')`/Vec ripples into bridge + tests) + the complex64 ctypes marshalling (`np.frombuffer`/`np.ascontiguousarray` → reuse srmech's numpy-free `array`+`memoryview` ctypes pattern, [[feedback_c_must_be_standalone_complete_no_python_fallback]] sibling).
   - `ephemerides_spectral/bridge.py` (5) — `_interleave_complex` HD wire-format (np complex array → interleaved float32 list).
   - **GATE for this whole component:** the existing BIP byte-parity test (`backend="c"` ≡ `backend="bip"` byte-for-byte) + `test_native_parity` MUST stay green — the `encode_state` residues are bit-exact; ANY drift is a regression. Capture residue ground truth BEFORE flipping, assert byte-identical after. (`tests/` are NOT codegen-copied — edit directly.)
5. **Capstone rc** — once the core is flipped: drop `numpy` from `pyproject.toml` + `pyproject-pure.toml` dependencies; rewrite numpy-oracle TESTS numpy-free; add a permanent "zero numpy" ratchet (no `import numpy` / no executable `np.`); full suite green with numpy UNINSTALLED. Then graduate the 0.31.x line.

**Honesty gate:** never claim a module is numpy-free until `grep -nE "\bnp\.|import numpy" <file>` == 0 AND it runs under numpy-absent. Don't over-claim in CHANGELOG banners (rc1 lesson).

---

## Discipline (load-bearing)

- TestPyPI rc BEFORE any clean tag → PyPI (the clean `ephemerides-spectral-vX.Y.Z` tag is the human gate; rc tags hand-pushed).
- **8 version SSOT must agree** (the table in Context — not 3); 3 srmech-floor sites must agree; pyproject ≡ pyproject-pure (CI guards both). Run `tests/test_readme_freshness.py` + `tests/test_native_parity.py` LOCALLY before pushing any version bump (rc1 lost a CI round to the missed 3).
- `gh pr merge --merge` (never squash). Autotag on clean semver. Scoped `git add`.
- **PREFER config-driven `[class]` TOML over a new bespoke code path whenever the only difference is a name** (`[[feedback_prefer_config_driven_toml_classes]]`).
- ephemerides relicenses GPL-3 → MIT (`[[project_srmech_subprojects_mit_monorepo_gpl3]]`).

## Decisions (RESOLVED by user, 2026-06-17)

1. **Genome packaging** — **Spike first, then decide** (user pick). Phase R1 runs as a standalone go/no-go spike (`secular_elements` PoC); not in the rc-ship line until it earns its place.
2. **etak/ITN class-TOML unification** — **Fold into the rc line as rc2** (user pick), with the duplicate-code-path purge folded in (see Phase R2). Hard-remove, no no-ops.
3. **numpy-free** — **committed** as Phase N (user: "this must be numpy free also"). Through-line of the 0.31.x series; rc2 is its first concrete flip; capstone rc drops numpy from the pyprojects.
4. **README hygiene** — **done in rc1** (Phase 1.5); further dated-prose passes are follow-ups.
5. **MIT relicense** — **its own follow-up rc** (not rc1; rc1 stayed honest).

## Ship order

rc1 (floor + version-8-SSOT + README banner hygiene — SHIPPING) → **rc2** (etak/itn `[class]` TOML + dedup purge, first numpy flip) → rcN… (numpy-removal by component) → numpy-capstone rc (drop numpy dep + zero-numpy ratchet) → MIT-relicense rc → **0.31.0 graduation** to PyPI (human gate). Phase R1 genome spike runs in parallel as a report, ships only if clean.

**Spine that ships regardless:** Phase 0 verify → Phase 1 floor bump → Phase 1.5 README hygiene → Phase 2 version (8 SSOT) → Phase 3 TestPyPI rc1.

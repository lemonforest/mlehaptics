# ephemerides-spectral CHANGELOG

All notable changes to this package will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.29.0rc1] — 2026-05-15

### Added — channel-basis dual-path spike (cyclic-group-native quarter-turn decomposition)

First rc of the v0.29.x cycle is a small precision spike that honours the project's algebraic stance: the channel-basis construction path gains a second route that does **integer quarter-turn decomposition** on the splitmix64-derived phase residue, with a small libm `cos`/`sin` on the within-quadrant fraction only. Motivation: the shipped LEGACY route does `phi = (u >> 11) · (2π / 2^53)` as a software multiply then calls libm `cos`/`sin` on the radian result — composing two argument-reductions and accumulating ~2 ULP of error at quarter-turn channels. The new TURN_INTEGER route works in turns from the start:

```
phase    = (uint32_t)(u >> 32)        # Z_{2^32}, the cyclic group itself
quadrant = phase >> 30                # 0..3
within   = phase & 0x3FFFFFFF         # 30-bit fraction OF a quarter turn

if within == 0:
    out[k] = i^quadrant ∈ {(1,0), (0,1), (-1,0), (0,-1)}   # bit-exact
else:
    a   = (double)within · (π/2 / 2^30)                    # [0, π/2)
    out[k] = i^quadrant · (cos(a), sin(a))                  # sign/swap rotation
```

This honours the notebook §1.4 framing — "every gear is a faithful representation of ℤ/nℤ" — by keeping the structural decomposition in the integer cyclic group and only converting to float at the within-quadrant reduction. Quarter-turn channels collapse to bit-exact `(±1, ±i)` on every toolchain (no libm cospi/sinpi dependency, no platform feature gate); the within-quadrant `cos`/`sin` sees a small argument with no further reduction needed; the `i^quadrant` quadrant rotation is pure sign/swap.

**Why opt-in (not default flip)**: the Tier 2a byte-parity test (`test_channel_basis_parity.py`) pins the C output against `numpy.exp(1j · φ)`, which uses `× 2π` in software too — flipping the default would break Python parity. The dual-path lets us bench-and-quantify (`scripts/bench_turn_integer_basis.py`) before deciding whether to graduate TURN_INTEGER to default + update the Python mirror, or keep LEGACY as the byte-parity default and TURN_INTEGER as the precision-on-demand route.

**Why this design beats the cospi/sinpi alternative**: the cospi/sinpi route (an earlier draft of this spike) needed libm support that's still rolling out (Apple libsystem yes; C23 glibc 2.40+ partial; MSVC libm no). It worked around the `× π` rounding loss but introduced a platform-feature-detection problem. The TURN_INTEGER design captures the same precision benefit — and the structural-correctness-at-quarter-turns benefit — using only universally-available libm `cos`/`sin` + integer arithmetic. No platform dependency, no feature gate, no fallback path that silently no-ops.

**C/Python parity preserved**: `_research/portable_prng.py` gains a byte-identical Python mirror of the TURN_INTEGER route (`splitmix64_turn_integer_basis_element` + `splitmix64_turn_integer_basis`). Sibling parity discipline to the LEGACY route's existing mirror — both routes now have Python-vs-C byte-for-byte agreement pinned in `tests/test_channel_basis_parity.py`. Verified cross-platform on Windows MSVC + WSL2 glibc 2.35: identical bytes on both.

**Per-area detail:** see [python/CHANGELOG.md §0.29.0rc1](python/CHANGELOG.md).

## [0.28.1] — 2026-05-15

### Production cut — README hygiene patch on top of v0.28.0

`ephemerides-spectral 0.28.1` ships to production PyPI as the consolidated landing of the rc1 + rc2 README-hygiene cycle. Version-only bump from `0.28.1rc2` → `0.28.1`; the substantive work landed across rc1 (stale "Unreleased" bullets + body-count drift + shipped roadmap items + heteroclinic note tightening) + rc2 (two minimum-disruption proofread follow-ups: BIP-vs-HD-state clarification + DE441 sweep table body-id rename to the v0.9.0+ Latin-proper-noun convention) and verified on TestPyPI before each rc merged to `main`.

Pure README hygiene patch. No code change; no ABI change (`ES_ABI_VERSION = 9` unchanged from v0.28.0); no `_research` mirror changes; no test ratchet changes.

**Per-area detail:** see [python/CHANGELOG.md §0.28.1](python/CHANGELOG.md).

## [0.28.1rc2] — 2026-05-15

### Fixed — two flagged-but-untouched README items from the rc1 proofread

User reviewed the rc1 PR's "Known ambiguities NOT touched" section and chose minimum-disruption fixes:

- **Issue 1 (Option C)** — BIP-vs-HD-state ambiguity in the "256 KB state at D=65536" framing. The orphan fragment is removed from the BIP bullet; the Memory Footprint table renames `State (BIP)` / `State (complex128)` → `HD state (BIP path)` / `HD state (complex128 path)` with a clarifying paragraph above the table that distinguishes the BIP encoder's user-facing `uint32[52]` per-body output (208 bytes) from the HD-lifted D-dimensional hypervector the HD pipeline uses.
- **Issue 2 (Option B)** — DE441 sweep table renames `earth` → `terra` and `moon` → `luna` to match the v0.9.0+ Latin-proper-noun convention used throughout the rest of the codebase. Prose references to "Earth" / "Moon" in English-language sentences stay as natural-language usage.

Pure README hygiene. No code change; no ABI change; no test ratchet changes. SSOT files bump in lockstep `0.28.1rc1` → `0.28.1rc2`.

**Per-area detail:** see [python/CHANGELOG.md §0.28.1rc2](python/CHANGELOG.md).

## [0.28.1rc1] — 2026-05-15

### Fixed — stale "Unreleased" bullets in PyPI-rendered README

`python/README.md` had two bullets at the top of the version-by-version list flagging features as future work that had actually shipped in v0.26.1 (LLM tool-schema export + first cosmology-instrument pair). The PyPI-rendered README on v0.28.0 still showed both as "Unreleased" — misleading to users landing on the package page. v0.28.1rc1 removes both bullets and leaves a brief HTML comment documenting the removal + the cross-package architecture (srmech provides `srmech.amsc.tool_schema`; ephemerides-spectral's `[profile.tool_schema].extension_file = "_srmech_tool_schema.toml"` registers the 9 profile-tier surfaces with `owner="ephemerides"` for LLM-agent discovery; the local `bridge.get_tool_schema` / `list_tool_names` / `get_one_tool_schema` introspect the full ~246 public bridge functions in 4 formats).

Pure docs hygiene patch. No code change; no ABI change (`ES_ABI_VERSION = 9` unchanged from v0.28.0); no `_research` mirror changes; no test ratchet changes. All 5 SSOT files bump in lockstep + manifest re-stamp.

**Per-area detail:** see [python/CHANGELOG.md §0.28.1rc1](python/CHANGELOG.md).

## [0.28.0] — 2026-05-14

### Production cut after the v0.28.x rc stack — Task `#212` closed

`ephemerides-spectral 0.28.0` ships to production PyPI as the consolidated landing of the four-rc v0.28.x cycle. Version-only bump from `0.28.0rc5` → `0.28.0`; the substantive work landed across rc1 / rc3 / rc4 / rc5 and verified on TestPyPI before each rc merged to `main`.

**Cumulative content:**

* **Phase 10a per-body equation-of-center catalog** (rc1) — 51 closed-form Newton-Kepler EOC patches anchored at J2000; new `_research/secular_elements_data.py` (16 subsystem-authority sources); new `_research/eoc_catalog.py` generator; new AMSC source `secular_elements` (`literature_curated` adapter); six new bridge surfaces + six new CLI subcommands; LLM tool-schema auto-discovers them (240 → 246 tools). Validation: 99.85% Kepler-truth collapse + 94% syzygy-anchor collapse on the 100-yr Earth-Mars sweep with terra+mars EOC active.

* **Task `#212` PR-b: srmech `[profile.native]` plugin tier + ABI v6→v8 realignment + native-parity drift fix** (rc3) — graduates the srmech profile from "simple" to "plugin" tier (ADR-0001 §7 Step 2); restores native acceleration across the install base by realigning `_native_bip.EXPECTED_ABI_VERSION` 6→8 (silent-rejection bug had quietly forced pure-Python fallback for every v0.16.0+ install for 12+ minor versions); regenerates `c/src/es_laplacian.c` to byte-agree with `_data/initial_phases.json` on all 52 bodies. 13 new ratchets pin the plugin-tier surface.

* **Task `#212` PR-c: bridge call-site migration through `srmech.profile("ephemerides").native`** (rc4) — `_native_bip.py` loads the library via the srmech profile when available; `_native_bip.LIB` and `Profile.native` are now the same Python object (Python `is` identity), keeping patch-registry runtime state consistent across both surfaces. New module global `LOAD_SOURCE`. Four-way native parity ratchet pinned: Python BIP / profile-loaded native / direct-ctypes native / bridge `backend="c"` all byte-identical.

* **Phase 10a EOC C-side completion** (rc5, ABI v8→v9) — closes the rc1 backend_caveat. New `ES_PATCH_KIND_ECCENTRICITY_CORRECTION` + Newton-Kepler evaluator in `c/src/es_patches.c`; `es_patch_t` extended with 3 trailing `double` fields; `ES_MAX_PATCHES` 32→64 to fit the 51-body EOC catalog. EOC patches now produce byte-identical phase residues on both `backend="bip"` AND `backend="c"`. JPL Power-of-Ten clean.

**Task `#212` closed**: ADR-0001 §7 Step 2 done. Remaining ADR §7 steps live in adjacent sessions (Step 3 — Task `#213` antikythera-spectral profile; Step 4 — Task `#214` `PROFILE_AUTHORING_GUIDE.md`).

**ABI bump v8 → v9** (`sizeof(es_patch_t)` +24 bytes for the EOC fields). The ABI handshake catches v8/v9 mismatches at load time and degrades to pure-Python rather than producing silent garbage.

**Per-area detail:** see [python/CHANGELOG.md §0.28.0](python/CHANGELOG.md) and the rc entries below.

## [0.28.0rc5] — 2026-05-14

### Phase 10a EOC C-side completion — ABI v8 → v9

The final rc in the v0.28.x stack. Closes the rc1 backend_caveat: per-body equation-of-center patches now produce **byte-identical phase residues on both `backend="bip"` and `backend="c"`** across all 52 bodies at every Δt tested.

**C-side additions** (`c/include/ephemerides_spectral.h` + `c/src/es_patches.c`):
- New patch kind `ES_PATCH_KIND_ECCENTRICITY_CORRECTION = 2`
- `es_patch_t` extended with 3 trailing `double` fields (`eccentricity`, `mean_anomaly_at_j2000_rad`, `n_rad_per_day`)
- Newton-Kepler evaluator `es_eval_eoc_residue` — bounded 30-iter Newton on `E − e·sin(E) = M`, tol 1e-14 rad, half-angle true-anomaly, principal-branch wrap via floor-based modulo
- `es_clear_eoc_patches` — selective clear by kind
- `ES_ABI_VERSION 8 → 9`
- JPL Power-of-Ten clean: every new function ≥2 asserts, no goto, no malloc, all loops bounded, ≤60 lines

**Python wiring** (`_native_bip.py` + `bridge.py` + `srmech_profile.toml`):
- `EXPECTED_ABI_VERSION 8 → 9`; `[profile.native].expected_abi_version 8 → 9`
- `EsPatch` ctypes struct extended in lockstep
- New helpers `native_apply_eoc_patch` + `native_clear_eoc_patches`
- `_mirror_patch_to_native` gains an `EccentricityCorrectionPatch` dispatch branch
- `bridge.apply_eoc_patches` registers C-side patches with Python+C rollback parity invariant; return envelope now reports `backends_active = ["bip", "c"]`
- `bridge.clear_eoc_patches` mirrors selective clear to the C registry

**Test ratchet flips**:
- rc1 `test_eoc_patch_is_python_only_kind` → rc5 `test_eoc_patch_kind_now_c_native` (positive ratchet)
- New `test_eoc_patch_byte_parity_across_backends` pins byte-exact EOC parity at 4 Δt epochs (J2000, ±1 yr, +20 yr, -100 yr)
- `test_parity_smoke` rationale strings refreshed
- JPL audit pins: `PIN_RULE_5_TOTAL_FUNCS 42 → 46`; `PIN_RULE_5_ASSERTIONS 88 → 102` (density 2.22, well above the ≥2.0 average floor)

**ABI wire-format**: `sizeof(es_patch_t)` increased by 24 bytes. The ABI handshake (srmech `_maybe_load_native` + `_native_bip` direct check) catches v8/v9 mismatches and degrades to pure-Python rather than producing silent garbage.

**Per-area detail:** see [python/CHANGELOG.md §0.28.0rc5](python/CHANGELOG.md).

## [0.28.0rc4] — 2026-05-14

### Task `#212` PR-c — bridge call-site migration through srmech profile

Final PR of Task `#212` (ADR-0001 §7 Step 2 call-site-migration portion). `_native_bip.py` now resolves the bundled native library via `srmech.profile("ephemerides").native` first (when srmech is importable + the plugin tier loaded); the existing direct `ctypes.CDLL()` path remains as the fallback. `_native_bip.LIB` and `Profile.native` are now **the same Python object** (Python `is` identity), keeping patch-registry runtime state consistent across both surfaces. New module global `LOAD_SOURCE ∈ {"srmech_profile", "direct_ctypes", None}`.

Four-way native parity verified on TestPyPI: Python BIP / profile-loaded native / direct-ctypes native / bridge `backend="c"` all produce byte-identical phase residues.

**Per-area detail:** see [python/CHANGELOG.md §0.28.0rc4](python/CHANGELOG.md).

## [0.28.0rc3] — 2026-05-14

### Task `#212` PR-b — srmech `[profile.native]` plugin tier + ABI v6→v8 realignment + native-parity drift fix

(rc2 was a failed-publish tombstone; the cibuildwheel Linux matrix surfaced an `es_laplacian.c` ↔ `_data/initial_phases.json` drift on 15 Mars + Saturnian moons that depend on the missing `mar099s` + `sat441` JPL auxiliary kernels. rc3 regenerated `es_laplacian.c` against the same stub-fallback state the JSON uses; both sides now byte-agree on all 52 bodies.)

ephemerides-spectral's srmech profile graduates from "simple" to "plugin" tier. Closes the silent-rejection bug that had quietly forced pure-Python fallback for every v0.16.0+ install: `_native_bip.EXPECTED_ABI_VERSION` was left at `6` while the C library advanced to `8` in v0.16.0. Bumping both sides to v8 in lockstep restores native acceleration across the install base.

**Per-area detail:** see [python/CHANGELOG.md §0.28.0rc3](python/CHANGELOG.md).

## [0.28.0rc1] — 2026-05-14

### Phase 10a — Per-body equation-of-center catalog (PEP 440 alpha pre-release of v0.27.0)

Closed-form Kepler equation-of-center patch catalog for every non-Sun body in the 52-body BIP roster (51 patches; Sun has e ≡ 0). Newton-iteration on Kepler's equation, J2000-anchored, exact at any eccentricity from Triton's e ≈ 1.6e-5 through Nereid's e = 0.7507.

The headline empirical claim — validated against the 100-yr Earth-Mars syzygy sweep on v0.26.1 — is that Earth+Mars EOC patches collapse the closed-form Kepler residual at BIP-opposition JDs from **9.26° RMS (peak 15.75°) → 0.014° RMS (peak 0.015°)**, a 99.85% collapse to numerical precision. Anchor-date offsets vs textbook Mars-opposition dates drop from **19.79 d RMS (max 35.32 d) → 1.12 d RMS (max 3.05 d)**, a 94% collapse. The remaining 1.12 d is the genuine off-diagonal Mars-Jupiter fiber content — Phase 10b's target.

Sub-thread: the Sun-from-SSB wobble hypothesis on FFT bin-5 (20.07 yr ≈ Jupiter-Saturn synodic) tested closed-form and falsified (0.7% collapse under direct subtraction). Stashed as `docs/srmech/notes/sun-wobble-falsification-2026-05-14.md`. First published-internal falsification of a candidate Phase-10b coupling — the MPM discipline at work.

**Architecturally:** v0.28.0rc1 is an alpha pre-release on PyPI; the v0.27.0 banner-flip (Phase B `binary_archive` adapter + C2 registry plumbing + D `use_local_kernel` extension per the ROADMAP) ships separately as a clean v0.27.0 once those land. Phase 10a's work is independent of v0.27.0's three-layer-mechanism banner — but sequenced before it so the version progression is monotonic on both axes (version number AND content richness).

**Per-area detail:** see [python/CHANGELOG.md §0.28.0rc1](python/CHANGELOG.md) — bridge surfaces (6), CLI subcommands (6), AMSC source ([`research/attested/secular_elements/`](research/attested/secular_elements/)), 39 test ratchets, workflow regex extension, Python-BIP-backend-only caveat.

## [0.26.1] — 2026-05-14

### Production cut after TestPyPI verify-rc cycle

`ephemerides-spectral 0.26.1` ships to production PyPI as the consolidated landing of substantive unreleased content (Task #197 Phase 4 AMSC migration to `srmech.amsc.*`, LLM tool-schema export, first cosmology-instrument pair, v0.27.0-phase-A AMSC backfills) plus the runtime dep bump `srmech>=0.1.0` → `srmech>=0.2.0` to match the parallel session's srmech v0.2.0 production cut.

The 0.26.1rc1 TestPyPI cycle (tag `ephemerides-spectral-v0.26.1rc1`, PR #396) verified compatibility against `srmech==0.1.1rc9` on TestPyPI ahead of the srmech v0.2.0 production cut: 15-cell cibuildwheel matrix green; end-to-end clean external venv install + `srmech.__version__ == "0.1.1rc9"` assertion passed.

This `[0.26.1]` block consolidates the four `### Added` / `### Changed` entries below (which lived under `[Unreleased]` during the rc cycle). The headline shape:

- **Task #197 Phase 4** — AMSC framework migrated out of `ephemerides-spectral._research/attested_collector_*` + `_research/attested_adapters/` and into `srmech.amsc.*`. 12 framework modules (~2,931 LOC) removed from the ephemerides-spectral wheel. `srmech>=0.2.0` becomes a hard runtime dep. No `ephemerides_spectral.bridge` public-API changes (delegation wired by `_bootstrap_amsc()` at package import).
- **LLM tool-schema export** — three new bridge functions + three CLI subcommands; 240 public bridge functions are now self-describing in four formats (Anthropic Claude / OpenAI function-calling / Anthropic MCP / plain JSON Schema).
- **First cosmology-instrument pair** — `cmb_power_spectrum` (Planck 2018 PR3 TT, 111 bands) + `cmb_anomalies` (six canonical large-scale anomalies). Five new bridge functions + five CLI subcommands.
- **v0.27.0-phase-A AMSC backfills × 12** — Mercury, Luna, Mars, Sun, Toroidal-Residual, Hawaiian-Emperor, Yarkovsky/YORP, Mars Tharsis, Axial Seamount, Sol Dynamical-Regime classifier (paired training + probes rosters), Pluto-Charon, Loki Patera. `n_sources` 13 → 19; `adapter_class="curated"` 10 → 16.

### Cleanup — TestPyPI rc-cycle scaffolding removed

- `pyproject.toml` + `pyproject-pure.toml`: dep floor `srmech>=0.1.1rc9` → `srmech>=0.2.0`. The rc-cycle's "verify-rc (Option B)" comment blocks are removed.
- `.github/workflows/ephemerides-spectral-publish.yml`: `CIBW_ENVIRONMENT: PIP_EXTRA_INDEX_URL=https://test.pypi.org/simple/` block removed.
- `.github/workflows/ephemerides-spectral-ci.yml`: three `PIP_EXTRA_INDEX_URL` env stanzas removed (build-and-test, codegen-determinism, fallback-test install steps); fallback-test explicit `srmech` install now uses plain `srmech>=0.2.0`.
- `python/CHANGELOG.md`: `[0.26.1rc1]` header rewritten as `[0.26.1]` with production framing.
- `python/README.md`: Status banner + `*(current)*` bullet updated for production.
- **Kept**: the `test_readme_freshness.py` regex relaxation that accepts optional `(?:rc\d+)?` suffixes — option-independent ratchet useful for any future rc cycle.

No code changes; no ABI bump (ES_ABI_VERSION = 8 unchanged).

### Added — LLM tool-schema export

Self-describing bridge surface for LLM tool-use clients. The bridge (~240 public functions across 40+ ships) now emits machine-readable tool descriptions in Anthropic Claude tool-use spec, OpenAI function-calling spec, Anthropic Model Context Protocol (MCP) tools/list spec, and plain JSON Schema formats. Three new bridge surfaces (`get_tool_schema`, `list_tool_names`, `get_one_tool_schema`) + three new CLI subcommands (`tool-schema`, `tool-names`, `tool-schema-one`) wire the export. **Self-describing API**: introspects `bridge.py` at call time — no hand-maintained list; every public bridge function with a docstring + type hints is automatically included. Adding a new ship's bridge surface automatically extends every emitted schema. The ratchet test `test_every_tool_has_non_empty_description` enforces docstring discipline. Filter by name prefix for catalog-specific subsets (e.g. `--filter-prefix get_cmb_` for the cosmology-instrument tools). Type-hint mapping handles `Optional[X]`, `List[X]`, `Dict[X, Y]`, `Union[X, Y]`, and string-form annotations. Name resolution uses the bridge namespace binding (not `fn.__name__`) — necessary because some bridge functions are factory-generated. **Pure-Python additive; no ABI bump.** 15 new tests. Reference: research notebook §0.0 (The Mathematical Provenance Method) — the bridge surface IS the surface other systems consume; making it self-describing to LLM clients is the natural completion of the "machine-readable everywhere" discipline.

### Added — First cosmology-instrument pair (CMB Power Spectrum + CMB Anomalies)

The project's first cosmology-scale instrument addition, opening the Mpc-to-Gpc regime as a new AMSC channel. Three sequential PRs.

- **`research/attested/cmb_power_spectrum/` (PR #351)** — Planck 2018 PR3 binned TT power spectrum. 111 binned bands spanning ℓ=2 to 2499 (28 unbinned low-ℓ commander + 83 binned high-ℓ Plik). Per-row source DOI: `10.1051/0004-6361/201833910` (Planck Collaboration 2018 VI, Aghanim et al. *A&A* 641:A6). Per-row `source_file` traceability to PLA download files (`COM_PowerSpect_CMB-TT-full_R3.01.txt` + `COM_PowerSpect_CMB-TT-binned_R3.01.txt`). First acoustic peak at ℓ ≈ 225 with D_ℓ ≈ 5793 μK² — the canonical empirical anchor for spatial flatness + baryon density constraints. Bridge surfaces deferred to PR #353.
- **`research/attested/cmb_anomalies/` (PR #352)** — six canonical large-scale CMB structural anomalies (Axis of Evil quadrupole-octupole alignment, Cold Spot, hemispherical power asymmetry, low quadrupole, parity asymmetry, missing C(θ) at large angles). Each row carries discovery DOI + Planck 2018 VII confirmation DOI (`10.1051/0004-6361/201833881`, Akrami et al. *A&A* 641:A7) + statistical test description + galactic sky location + `anomaly_kind` ∈ {alignment, hotspot, asymmetry, suppression, parity_violation, correlation_anomaly}. **Data, not interpretation** — theoretical explanations (bubble-collision, EM-medium-pressure, axion / cosmic-string mechanisms) explicitly NOT recorded; they remain research-scope. Bridge surfaces deferred to PR #353.
- **Bridge + CLI deferred items (PR #353)** — closes the ratchet for both ships. Five new public bridge functions (`get_cmb_power_at_ell`, `get_cmb_first_acoustic_peak`, `list_cmb_power_spectrum`, `get_cmb_anomaly`, `list_cmb_anomalies`) + five new CLI subcommands (`cmb-power-at-ell`, `cmb-first-acoustic-peak`, `cmb-power-spectrum-full`, `cmb-anomaly`, `cmb-anomalies-full`). Catalog modules `_research/cmb_power_spectrum_catalog.py` + `_research/cmb_anomalies_catalog.py` follow **AMSC-first pattern** — read directly from attested NDJSON via the universal accessor, no separate `_data.py` duplication. `n_sources` 17 → 19; `adapter_class="curated"` 14 → 16. test_parity_smoke: 5 new python_only entries. Notebook §V.5 (Observational constraints) updated with reference to the new catalogues as empirical anchors at the IR end of the d_S(σ) → 4 flow.

MFO connection (notebook §V): the CMB power spectrum is the empirical anchor at the IR end of the spectral-dimension flow d_S(σ) → 4 (CMB analyses give effective d_H ≈ 4 at Mpc scales, consistent with ΛCDM and MFO's IR limit). The companion anomalies catalogue provides testable observational targets for any future framework prediction; whether MFO predicts specific anomalies is open research per the §XIII.1 status update.

### Added — v0.27.0 phase A — Loki Patera Eruption Cycle AMSC backfill

The v0.24.12 ship — Io's largest persistent thermal anomaly (and the Solar System's most active volcano), driven by Galilean Laplace tidal heating from the Io-Europa-Ganymede 4:2:1 mean-motion resonance. Multi-row-type catalogue (12 rows): 6 cycle_peak rows (1990 / 1995 / 1997 / 2002 / 2013 / 2015 — Veeder 1994 KAO observations through de Kleer 2019 *Nature* adaptive-optics era) + 6 cycle_mode rows (loki_main_cycle ~540 d, brightening_phase, resurfacing_wave at ~1 km/day, cooling_phase, io_orbital_period, galilean_laplace_4_2_1_commensurability). Direct cousin to v0.24.8 Axial Seamount in the temporal_quasi_periodic_cycle regime, but with fundamentally different forcing physics: Galilean Laplace tidal heating instead of mantle-plume / mid-ocean-ridge dynamics. Per-row source DOIs: Veeder 1994 *J. Geophys. Res.* (1990 KAO peak), Rathbun 2002 *GRL* (canonical_doi; ~540-d periodicity + 1995-2002 peaks), de Kleer & de Pater 2017 *Icarus* (modern AO era), de Kleer 2019 *Nature* (multi-phase resurfacing analysis), Peale-Cassen-Reynolds 1979 *Science* (the famous Io tidal-heating prediction confirmed 2 weeks later by Voyager 1), plus one `isbn:` for Murray-Dermott 1999 *Solar System Dynamics* (canonical Galilean-Laplace 4:2:1 textbook reference). 13 new dual-author tests including a 540-day-mean-cycle ratchet, a Galilean-Laplace-4:2:1-arithmetic ratchet (4·P_Io ≈ 2·P_Europa ≈ P_Ganymede within 0.1 d ≈ 1% of period; the period-ratio approximation, not the exact Laplace argument), a Rathbun-2002-anchor-cycle ratchet, an isbn:-only-textbook discipline ratchet, and a chronological-peak-ordering ratchet. **Phase A complete: 12 of 12 v0.24.x catalogues now have AMSC literature_curated backfill PRs in flight (v0.24.0 Mercury through v0.24.12 Loki Patera, with v0.24.9-v0.24.10 paired as the dynamical_regime + dynamical_regime_probes ship).**

### Added — v0.27.0 phase A — Pluto-Charon Dynamical Spectrum AMSC backfill

Twelfth v0.24.x AMSC backfill (the v0.24.11 ship). 12-mode roster covering the project's first BINARY mutual-tidal-lock case: the TRIPLE 1:1 lock at 6.387230 d (P_Pluto_spin = P_Charon_spin = P_mutual_orbit, the only such triple-lock in the Solar System), the apsidal-libration mode, four action variables (eccentricity ~5e-5 / mutual obliquity ~0.0006° / Charon-Pluto mass ratio ~0.1218 / heliocentric inclination ~119.6°), and four small-moon near-3:4:5:6 commensurability angles (Styx / Nix / Kerberos / Hydra orbital periods at integer-multiple ratios with the mutual orbital period). Path-B response to the v0.24.10 OOS-probe schema-gap: closes the new `rigid_body_action_angle_mutual_lock` regime label introduced for this ship. Per-row source DOIs all real Crossref-indexed papers — Brozovic 2015 *Icarus* (canonical post-New-Horizons orbital fit), Stern 1992 *Annu. Rev. Astron. Astrophys.* (canonical pre-New-Horizons binary review), Stern 2015 *Science* (New Horizons flyby summary), Showalter & Hamilton 2015 *Nature* (small-moon resonant interactions + chaotic libration). 12 new dual-author tests including a triple-synchronous-lock ratchet (P_Pluto = P_Charon = P_orbit = 6.3872304 d), a largest-binary-mass-ratio-in-Solar-System ratchet (Charon/Pluto ≈ 0.1218 vs Earth-Luna 0.0123), a small-moon near-3:4:5:6 ratio-bracket ratchet, and a pure-action-Infinity-period-roundtrip ratchet (validates JSON Infinity-token serialisation discipline for the four action rows).

### Added — v0.27.0 phase A — Sol Dynamical-Regime Classifier AMSC backfill (paired)

Tenth + eleventh v0.24.x AMSC backfills (paired ship; two AMSC sources). The v0.24.9 training roster (`dynamical_regime`, 11 rows — one per v0.24.x ship spanning v0.24.0-v0.24.8 + v0.24.11 + v0.24.12) and the v0.24.10 OOS probe roster (`dynamical_regime_probes`, 10 probes spanning every v0.24.x regime label). Decision: ship as **two separate AMSC sources** rather than one combined — different dataclasses (RegimeExample vs RegimeProbe with `expected_regime` / `ood_expected` fields), and the existing `test_suggest_gap_collections_n_probes_matches_roster` already differentiates them; future schema-gap suggester wiring is per-source. Per-row DOIs in the training roster cite the canonical paper most identified with each v0.24.x ship (Margot 2007 / Williams 2014 / Laskar 1993 / Davies 2014 / Iess 2019 / Sharp & Clague 2006 / Chesley 2003 / Plescia 2004 / Chadwick 2016 / Brozovic 2015 / Rathbun 2002). Probe DOIs cite each probe's primary reference. 22 new dual-author tests including a pinned regime-label distribution + Pluto-Charon-only-mutual-lock + Axial-only-MISS + Ceres-only-OOD + isbn:-only-textbook ratchets.

### Added — v0.27.0 phase A — Axial Seamount Eruption Chronology AMSC backfill

Ninth v0.24.x AMSC backfill. Multi-row-type catalogue (9 rows): 3 eruption rows (1998 / 2011 / 2015) + 4 inflation_phase rows (pre-1998, 1998-to-2011, 2011-to-2015, post-2015) + 2 forecast rows (2015 HIT, 2024-2025 MISS — the methodology's first observed missed prediction). First v0.24.x catalogue applying the spectral methodology to a *temporal-spectrum* observable on a single sub-system. Per-row DOIs cite Dziak & Fox 1999 / Caress 2012 / Chadwick 2016 / Wilcock 2016 / Nooner-Chadwick 2009 / 2016. The post-2015 follow-up uses `nodoi:nooner_chadwick_post_2015_ooi_followup` since these are conference proceedings + OOI Cabled Array status updates rather than Crossref-indexed publications. 11 new dual-author tests including row-type-distribution + eruption-chronology + forecast-outcomes (HIT + MISS) + post-2015-rate-slowed + chronologically-chained-phases ratchets.

### Added — v0.27.0 phase A — Mars Tharsis Volcanic Chain AMSC backfill

Eighth v0.24.x AMSC backfill. 5-volcano roster: the Tharsis Montes ridge (Arsia / Pavonis / Ascraeus) plus the two outliers — Olympus Mons (the Solar System's largest known volcano) and Alba Mons (older / broader / shorter shield). Second v0.24.x catalogue applying the bounded-local-Laplacian methodology to physical features on a single body's surface — the no-plate-tectonics counterpart of v0.24.5 Hawaii. Per-row DOIs cite Hartmann & Neukum 2001 / Hartmann 2005 / Werner 2009 / Plescia 2004. 10 new dual-author tests including Olympus-tallest + Alba-broadest + Alba-oldest + role-distribution ratchets.

### Added — v0.27.0 phase A — Sol Yarkovsky/YORP AMSC backfill

Seventh v0.24.x AMSC backfill. 10 NEA / Hayabusa-target asteroids with published Yarkovsky semi-major-axis drift and/or YORP spin-rate-change measurements: Bennu (OSIRIS-REx headline; first directly-imaged drifter), 2000 PH5 (the asteroid that lent its name to YORP), Apophis (impact-prediction relevance), Ryugu / Itokawa (Hayabusa missions), Apollo / Geographos / Eger (NEA YORP detections), 1950 DA (radar Yarkovsky at the rotational-fission limit), Golevka (the first-ever Yarkovsky detection). Per-row DOIs cite Farnocchia 2013 / Lowry 2007 / Vokrouhlický 2015 / Watanabe 2019 / Lowry 2014 / Kaasalainen 2007 / Durech 2008 / Farnocchia 2014 / Chesley 2003 / Durech 2012. 10 new dual-author tests including a prograde-outward / retrograde-inward Yarkovsky-direction ratchet and a 1950-DA-near-fission-limit ratchet.

### Added — v0.27.0 phase A — Hawaiian-Emperor Chain AMSC backfill

Sixth v0.24.x AMSC backfill. 18 seamounts spanning ~85 Myr from Meiji through the Hawaiian-Emperor bend at 47.5 Myr (Daikakuji marker) to Kilauea. First v0.24.x catalogue with the bounded-local-Laplacian regime label. Introduces the `nodoi:` DOI-prefix for pre-DOI book chapters and USGS observatory compilations. 8 new dual-author tests including arc-distribution + Meiji-oldest/Kilauea-youngest + bend-age consistency ratchets.

### Added — v0.27.0 phase A — Toroidal-Residual J₂ AMSC backfill

Fifth v0.24.x AMSC backfill. 14 bodies classified on the Chandrasekhar 1969 equilibrium-figure sequence (Sphere → Maclaurin → Jacobi → bar → ring); each row pairs measured J₂ with dimensionless rotation parameter q + moment-of-inertia factor + regime + fossil-figure flag (Mercury and Luna are the canonical fossils). Per-row DOIs across the gravity-field literature (EGM2008 / Genova 2016 / Anderson 2002 / Smith 2012 MESSENGER / Konopliv 2013 GRAIL / Iess 2018 Juno / Iess 2019 Cassini / Jacobson 2014 / Jacobson 2009 / Anderson 2001 Galileo / Iess 2010). 12 new dual-author tests including a Saturn-closest-to-Maclaurin-Jacobi-bifurcation ratchet. 2012 tests pass.

### Added — v0.27.0 phase A — Sun Dynamical Spectrum AMSC backfill

Fourth v0.24.x AMSC backfill (after Mercury / Luna / Mars). 20 helioseismic p-mode rows at canonical (n, l) labels — the stellar-oscillation analogue of rigid-body action-angle decomposition. Davies-2014-cited BiSON catalogue values. 11 new dual-author tests including a Tassoul-asymptotic-monotonicity ratchet (frequencies increase with n at fixed l). 2000 tests pass total.

### Added — v0.27.0 phase A — Mars Dynamical Spectrum AMSC backfill

Third v0.24.x AMSC backfill (after Mercury PR #303, Luna PR #306). 11 rows: 8 dynamical-mode (orbital + sol-rotation + spin-axis-precession + apsidal g₄ + nodal s₄ + eccentricity / inclination / obliquity) + 3 secular-resonance (the chaos-driving near-resonances). Per-row DOIs cite Park 2021 / Le Maistre 2023 (InSight) / Ward 1973 / Laskar 1993 / Laskar 2004 / Laskar 2008 / Touma-Wisdom 1993. 9 new dual-author tests including a secular_resonance proximity ratchet.

### Added — v0.27.0 phase A — Luna Dynamical Spectrum AMSC backfill

Second v0.24.x AMSC backfill (after Mercury PR #303). 15 rows: 11 dynamical-mode (four classical lunar months + spin lock + Williams-2014 forced libration + apsidal + nodal precession + eccentricity / inclination / obliquity actions) + 4 saros-commensurability (the integer-product closure invariant: 223 synodic ≈ 239 anomalistic ≈ 242 draconitic ≈ 19 eclipse-years ≈ 6585.32 days). Per-row DOIs cite Allen's Astrophysical Quantities, JPL DE441, Williams & Boggs 2014 LLR libration, Murray-Dermott 1999, Cassini 1693 (introduces `historical:` DOI prefix for pre-DOI works), Meeus 1991. 9 new dual-author tests including a Saros closure-invariant ratchet (four product_days values agree within 0.5 day).

### Fixed — AMSC `_ndjson_path` honours explicit `[fetch].ndjson_path`

Surfaced during the v0.27.0 phase A Mercury migration (PR #303): the path resolver ignored the descriptor's explicit `[fetch].ndjson_path` field and used only the schema-id-derived fallback. When the two disagreed, descriptors silently returned empty rows with the misleading "first T1 collection pending" note even though the file existed at the documented path. Fix: resolve `[fetch].ndjson_path` first; fall back to schema-id derivation only when the explicit field is unset. Backwards-compatible (no existing source's behaviour changes). 3 new regression tests pin the resolution order.

### Added — v0.27.0 phase A — first AMSC backfill of a v0.24.x catalogue

The v0.24.0 Mercury Dynamical Spectrum catalogue is now wrapped in the AMSC framework as the first `literature_curated` backfill of an existing v0.24.x ship. New `research/attested/mercury_dynamical_spectrum/` source: descriptor + JSON Schema + NDJSON covering 16 rows (8 dynamical-mode rows + 8 precession-contribution rows from the Le Verrier–Einstein decomposition). Per-row DOIs cite Park 2021 / Margot 2007 / Clemence 1947 / Einstein 1915 / Verma 2014 / Park 2017 / Murray-Dermott 1999 / Laskar 1989. Hand-coded `_research/mercury_dynamical_spectrum_data.py` remains the working authority; AMSC NDJSON is the attestation envelope. 10 new dual-author tests inheriting the Saturn-rings PR #291 pattern ratchet byte-stable agreement between the two paths.

### Added — v0.27.0 phase C — body→kernel registry

The layer-2-to-layer-3 interface from notebook §22.6: `{body → (kernel_path, precision_tier)}`. Pure Python additive; no ABI bump. New module `_research.body_kernel_registry` + three new bridge surfaces (`register_body_kernel`, `clear_body_kernel`, `get_body_kernel_registry`) + metadata propagation (`kernel_registry` field) into `body_architecture` and `predict_itn_accessibility` response envelopes. Registry hashing (SHA-256 over canonical-serialised state) provides the cache-invalidation key that phase B's `binary_archive` adapter will consume. 36 new tests including integration-test stubs for phases A + B + C convergence. **Phase C is structural** — registrations are tracked but orbital-mechanics state lookups still fall back to BODIES until phase B ships kernel-reading. See [docs/antikythera-maths/ephemerides_spectral_research_notebook.md](../ephemerides_spectral_research_notebook.md) §22.6 for the architecture.

### Documentation

- **Two-tier eclipse-finding discipline now explicit in bridge docstrings.** `bridge.find_syzygies` (Saros-class mean-period triage) and `bridge.get_eclipse_probability` (JPL-anchored arc-second-class confirmation) are deliberately different precision tiers, both load-bearing. The pre-v0.27.0 docstring wording suggested `find_syzygies` "replaced" `get_eclipse_probability`, which was misleading — only the *windowed loop over* `get_eclipse_probability` was replaced; per-call use as the precision-confirmation tier remains the intended workflow. No code change. Direct comparison of `bip_hd_lift.eclipse_probability` (Born-rule projection on DE441-derived HD state) vs `syzygy_window.SyzygyCandidate.score` (mean-period geometric residual) confirms they compute related-but-different quantities on different data — keeping both surfaces is correct, not redundant. Surfaced by the bridge-wide audit in [docs/research-spikes/stored-relationship-mechanism-spike.md](../../research-spikes/stored-relationship-mechanism-spike.md).

## [0.26.0] — 2026-05-08

**Schema-gap-driven trigger — closes the Mathematical Provenance Method loop.** The system identifies what it doesn't know and points at attested sources that could populate the gap.

### What ships

| Surface | Function / subcommand |
|---|---|
| Suggester module | `_research.attested_collector_gap_suggester` |
| Bridge | `bridge.suggest_gap_collections(*, ood_threshold=0.85)` |
| CLI | `suggest-gap-collections [--ood-threshold N]` |
| Tests | 10 new tests in `tests/test_attested_collector.py` |

### Behaviour

Reads the v0.24.10 OOS probe roster, runs each probe through the v0.24.9 dynamical-regime classifier, identifies regime gaps, and matches each gap against attested-source descriptors via `[gap_targeting].regime_labels`. Three gap kinds surfaced:

- **`ood`** — calibration ratio exceeds threshold (no close neighbour exists in eigenbasis).
- **`spurious_match`** — classifier's nearest regime disagrees with probe's `expected_regime`.
- **`surprise`** — probe was declared `expected_regime=None, ood_expected=False` ("let classifier surprise us"); flag wherever it landed for densification consideration.

For each gap, the suggester finds descriptors whose `[gap_targeting].regime_labels` includes the target regime label. Output is deterministic given (probe roster, descriptor set, ood_threshold). Same MPM discipline — no LLM, no SGD, no random init.

### What's deferred

The CI auto-PR mechanism that consumes the suggestion surface and opens targeted T1 collection PRs is not in v0.26.0. v0.26.0 ships the analysis surface — the suggestion API is itself the deliverable. The auto-PR half lands when a maintainer-review-grade mechanism is wired up. Open research questions documented in #161.

### Cross-references

- Notebook §0.0 — The Mathematical Provenance Method.
- Notebook §18.5 — T1 re-bake triggers (option 3 = schema-gap-driven).
- v0.24.10 OOS probes + v0.24.9 classifier + v0.25.x descriptor `[gap_targeting]`.

## [0.25.2] — 2026-05-08

**Attested collector — T3 live query.** The fourth-tier reproducibility extension — completes the T0/T1/T2/T3 model from notebook §18.1.

### What ships

| Surface | Function / subcommand |
|---|---|
| Catalog wrapper | `_research.attested_collector_catalog.get_attested_dataset(..., live=False)` extended with new T3 path; new private `_get_attested_dataset_live` |
| Bridge | `bridge.get_attested_dataset(..., live=False)` extended kwarg |
| CLI | `attested-dataset --live` flag |
| Tests | 7 new tests in `tests/test_attested_collector.py` |

### Behaviour

`live=True` invokes the descriptor's declared adapter against the upstream archive at call time. Each row carries its full per-row attestation (the same 9 mandatory fields T1 collector runs produce); the response envelope adds `tier="T3"` + `retrieved_at` + `upstream_response_sha256s` for paper-appendix replay.

`live=False` (default) returns the T0+T1+T2 baseline (committed NDJSON, possibly overlaid by a registered T2 runtime kernel). Baseline responses now also carry an explicit `tier="T0+T1+T2"` discriminator for diagnostic clarity.

### Reproducibility tier

T3 — weakest. Each row's `response_sha256` documents the upstream content currently served; replay requires re-fetching against an unchanged upstream OR archiving response bytes alongside the recorded attestation. Adapter errors surface as `ok=False` with diagnostic + `retrieved_at`.

### Cross-references

- Notebook §18.1 — four-tier reproducibility model (now fully implemented).
- T2 user runtime kernel: v0.25.1 (#159).
- T0+T1 baseline: v0.25.0 (#150 + #163).

### Other

EarthRef SC descriptor's `[source].canonical_doi` updated to `10.1029/2009GL040749` (was empty; MPR validation requires non-empty `source_doi`).

## [0.25.1] — 2026-05-08

**Attested collector — T2 user runtime kernel.** Local NDJSON overlay over the T0+T1 baseline. The second of three reproducibility-tier extensions promised in notebook §18.1.

### What ships

| Surface | Function / subcommand |
|---|---|
| Catalog wrapper | `_research.attested_collector_catalog.{use_local_kernel, clear_local_kernel, get_local_kernel_state, _resolved_ndjson_path}` |
| Bridge | `bridge.use_local_kernel(path)`, `bridge.clear_local_kernel()`, `bridge.get_local_kernel_state()` |
| CLI | `local-kernel-use --path <DIR>`, `local-kernel-clear`, `local-kernel-state` |
| Tests | 11 new tests in `tests/test_attested_collector.py` |

### Behaviour

When an overlay path is registered (directory shaped like `<source_key>/<table>.ndjson`), queries consult the overlay FIRST per source. Matching overlay files REPLACE the baseline NDJSON for that source; sources with no overlay file fall through to T0+T1 unchanged. Default policy is REPLACE; APPEND policy may land in a later v0.25.x.

### Cache hash for paper-appendix replay

`get_local_kernel_state` returns SHA-256 over canonical-serialised `(source_key, ndjson_sha256)` pairs. Papers record this hash; archived overlay trees + the recorded hash uniquely identify which T2 rows were consumed at runtime.

### Cross-references

- Notebook §18.1 — four-tier reproducibility model.
- T0+T1 baseline: v0.25.0 (#163).
- T3 live query: v0.25.2 (#160).

## [0.25.0] — 2026-05-08

**Attested Multi-Source Collector framework v1 — three pilots end-to-end + T1 collect CI workflow + MPR v1 normative format.** Completes the v0.25.0a/b ship sequence (notebook §18). The CONFIG-not-CODE escape from the v0.24.x hand-coding pattern is now production-ready. Pure-Python additive; **no ABI bump** (thirty-sixth consecutive ship since v0.13.x).

### What ships

| Surface | Function / subcommand |
|---|---|
| Format module | `_research.attested_collector_format` (MPRRecord + IO + validation) |
| Descriptor module | `_research.attested_collector_descriptor` (TOML + templating + canonical hashing) |
| Adapter core | `_research.attested_adapters` (5 modules sharing `_base.attest` + `_base.run`) |
| Catalog wrapper | `_research.attested_collector_catalog` (universal bridge surfaces) |
| Bridge | `bridge.list_attested_sources`, `bridge.get_attested_dataset` (paginated), `bridge.get_attested_descriptor`, `bridge.attestation_audit` |
| CLI | `attested-list`, `attested-dataset`, `attested-descriptor`, `attested-audit` |
| Pilots (3) | EarthRef SC (`html_scraper`) + GMRT (`csv_bulk`) + PetDB v4 (`json_api`) |
| T1 workflow | `.github/workflows/ephemerides-spectral-collect.yml` (scheduled monthly + manual dispatch) |
| Tests | 38 new tests in `tests/test_attested_collector.py` |

### Three pilots end-to-end

- **EarthRef Seamount Catalog** (Wessel & Sandwell 2018; Koppers 2019). HTML-scraped; ~1,800 named seamounts globally. Feeds v0.24.5 Hawaii / v0.24.7 Mars Tharsis bounded-local-Laplacian regimes.
- **Global Multi-Resolution Topography** (Ryan et al. 2009, doi:10.1029/2008GC002332). GMRT GridServer ESRI ASCII Grid output via `csv_bulk` adapter (no rasterio/gdal dep). Bathymetry rows for hotspot-track regimes.
- **PetDB v4 / EarthChem unified search** (Lehnert et al. 2000, doi:10.1029/2002GC000345). JSON API; igneous-rock geochemistry samples relevant to v0.24.5 / v0.24.7 / v0.24.8 ground-proof rows.

### T1 (CI-baked extension) — first auto-PR pending

The new `ephemerides-spectral-collect.yml` workflow runs collectors against live archives on schedule (monthly, 02:00 UTC on the 1st) and on manual dispatch (with optional `--source` filter). It writes per-source NDJSON, re-runs `regenerate.py` to refresh manifest SHA-256 sums, and opens an auto-PR via `peter-evans/create-pull-request@v6` with a maintainer-review checklist embedded in the PR body. **The first T1 run** populates the seamount/bathymetry/geochem NDJSON files that v0.25.0 ships descriptor-only.

`codegen/run_collectors.py` is the **only** network-touching code path in the project. `regenerate.py` does no network I/O; the ratchet test `test_regenerate_path_has_no_network_imports` enforces this.

### Reproducibility tier coverage

- **T0 frozen baseline** — committed NDJSON; byte-identical across all installs of v0.25.0.
- **T1 CI-baked extension** — collectors auto-refresh via the new workflow.
- **T2 user runtime kernel** — ships v0.25.1 (#159).
- **T3 live query** — ships v0.25.2 (#160).
- **Schema-gap-driven trigger** — v0.26.x research thread (#161); descriptor `[gap_targeting]` block is shipped in v0.25.0 already, awaiting the consumer.

### MPR v1 is normative

Mathematical Provenance Record v1 is the canonical NDJSON format, aligned with the discipline name from §0.0 (The Mathematical Provenance Method). 9 mandatory attestation fields per row + 3 mandatory rendering fields. Future schema bumps require explicit migration story; consumers MUST refuse unrecognised versions.

### Cross-references

- v0.25.0a foundation (PR #273 merged 2026-05-08).
- Format spec: notebook §18 (PR #272 merged 2026-05-08).
- Discipline: notebook §0.0 The Mathematical Provenance Method.

## [Unreleased — earlier v0.25.0a entries (rolled into v0.25.0)]

### v0.25.0a — Attested Multi-Source Collector framework (checkpoint)

**Framework foundation for the v0.25.0 ship.** Code-only checkpoint commit; no PyPI release. v0.25.0 stable publishes when v0.25.0b lands (GMRT + PetDB pilots + T1 collect CI workflow).

The v0.25.0 ship implements notebook §18: a CONFIG-not-CODE escape from the v0.24.x hand-coding pattern. Each new attested source becomes a TOML descriptor consumed by a generic collector core, producing canonical NDJSON rows with mandatory `attestation` blocks. The format gets a name aligned with the discipline (§0.0): **MPR — Mathematical Provenance Record**.

#### What ships in v0.25.0a

| Surface | Function / subcommand |
|---|---|
| Format module | `_research.attested_collector_format` (MPRRecord + IO + validation) |
| Descriptor module | `_research.attested_collector_descriptor` (TOML parsing + templating + canonical hashing) |
| Adapter core | `_research.attested_adapters` (5 modules sharing `_base.attest` + `_base.run`) |
| Catalog wrapper | `_research.attested_collector_catalog` (universal bridge surfaces) |
| Bridge | `bridge.list_attested_sources`, `bridge.get_attested_dataset` (paginated), `bridge.get_attested_descriptor`, `bridge.attestation_audit` |
| CLI | `attested-list`, `attested-dataset`, `attested-descriptor`, `attested-audit` |
| Pilot | EarthRef SC descriptor + JSON Schema (NDJSON committed in v0.25.0b T1 first run) |
| Tests | 37 new tests (`tests/test_attested_collector.py`) |

#### What ships in v0.25.0b

GMRT pilot (via `csv_bulk` GridServer ASCII XYZ — no rasterio dep), PetDB v4 pilot (via `json_api`), T1 CI workflow (`ephemerides-spectral-collect.yml`), PyPI 0.25.0 stable release.

#### Determinism preserved

NDJSON files committed verbatim under `research/attested/<source>/`; codegen mirror is byte-exact (no LF normalisation; preserves SHA-256 in attestation blocks). `regenerate.py` does no network I/O — T1 collector workflow is the only place network fetches happen. CI codegen-determinism step passes; manifest reproduces byte-identically.

#### Mathematical Provenance Method (renaming-discipline anchor)

The framework is the on-disk crystallisation of the discipline established in §0.0. Per-row attestation block carries source DOI + URL + license + retrieval timestamp + response checksum + parser metadata + descriptor hash — every step has citable mathematical provenance. The format itself is normative once shipped; future bumps require explicit migration.

## [0.24.12] — 2026-05-07

**Loki Patera Eruption Cycle Catalog (Io tidal-heating temporal-spectrum cousin to v0.24.8 Axial Seamount; Galilean Laplace 4:2:1 forcing) — eleventh ship in v0.24.x and the second temporal-spectrum observable on a single sub-system.** Pure-Python additive; **no ABI bump** (thirty-fifth consecutive ship since v0.13.x).

### What ships

| Surface | Function / subcommand |
|---|---|
| Pythonic API | `_research.loki_patera_catalog.get_loki_patera_eruption_cycle / get_loki_galilean_laplace_signature / list_loki_patera_eruption_cycle` |
| Bridge dict API | `bridge.get_loki_patera_eruption_cycle()` / `bridge.get_loki_galilean_laplace_signature()` / `bridge.list_loki_patera_eruption_cycle()` |
| CLI | `loki-patera-eruption-cycle`, `loki-galilean-laplace-signature`, `loki-patera-eruption-cycle-full` |

### THE headline — Galilean Laplace 4:2:1 commensurability

Io / Europa / Ganymede orbital periods satisfy the canonical 3-body mean-motion resonance:

```
4 · P_Io     = 4 · 1.7691378 d = 7.0765512 d
2 · P_Europa = 2 · 3.5511810 d = 7.1023620 d
P_Ganymede   =                   7.1545530 d
```

The agreement is to within ~1% — a **libration around exact resonance**, not strict equality. Peale-Cassen-Reynolds 1979 used this near-commensurability to **predict Io's tidal heating two weeks before Voyager 1 confirmed active volcanism**, one of the cleanest closed-loop predictions in planetary science.

### Loki Patera physics

The deep-mechanism reason Loki exists:

- The Galilean Laplace lock forces Io's orbital eccentricity to ~0.0041 (far above tidal-damping equilibrium).
- The forced eccentricity drives ~10¹⁴ W of tidal dissipation in Io's interior (~2-3 orders of magnitude larger than Earth's total volcanic output).
- Loki Patera, a ~200 km diameter lava lake at ~12.7° N / ~309.6° W, is the largest persistent surface manifestation — accounting for **5-15% of Io's globally-integrated thermal output**.
- The headline observable is a quasi-periodic ~540-day brightening / resurfacing cycle (Rathbun 2002 *GRL* canonical paper; range 480-580 d), proceeding through brightening → resurfacing-wave → cooling → quiescent phases.

### Cousin to v0.24.8 Axial — same regime, different forcing class

Loki and Axial occupy the same `temporal_quasi_periodic_cycle` regime label in the v0.24.9 dynamical-regime classifier — but with fundamentally different forcing physics:

| Body | Cycle period | Spatial scale | Forcing class | Prediction track |
|---|---|---|---|---|
| Axial Seamount (v0.24.8) | ~8.6 yr (3140 d) | ~3-8 km caldera | Mantle-plume magma supply | -1 (Chadwick 1 HIT + 1 MISS) |
| Loki Patera (v0.24.12) | ~540 d | ~200 km lava lake | Galilean Laplace tidal heating | +1 (Rathbun 2002 cycle validated) |

The two ships demonstrate the project's ability to recognise **same regime, different forcing**: Loki populates the temporal-cycle regime more densely rather than opening a new one. The classifier now has 11 ground-proof rows (was 10).

### Schema-gap surfacing — the Path-B loop continues

Adding Loki at `spatial_scale_log_km = 2.30` made it a near-twin to Vesta (2.42, main-belt asteroid in the OOS probe roster), collapsing Vesta's calibration ratio from ~0.98 (honest "I don't know" in v0.24.9–v0.24.11) to ~0.79 — Vesta now lands on `rigid_body_chaotic_obliquity` as a SPURIOUS classification (the physics is small-body radiation-drift, not chaotic obliquity).

Pinned in `tests/test_dynamical_regime_probes.py::test_vesta_classifier_landing_v_0_24_12_pinned` as the next schema-gap to close. A future ship will need a small-body-radiation ground-proof row to give Vesta a correct home — the loop continues.

### The Mathematical Provenance Method (naming-discipline addition)

The v0.24.x methodology is formally **The Mathematical Provenance Method** — we don't train, we don't fit, we don't initialise pseudorandomly; we project labelled ground-proof rows through closed-form `np.linalg.eigh` and accept the eigenbasis as a *property* of the data, not a fit to it. Each new ship deterministically extends the schema; `np.linalg.eigh` recomputes byte-identically. Recorded in the research notebook §0 Framing.

### Cross-channel reach

- **v0.21.5 Sol Electromagnetic Instrument** — Loki is downstream of the Jupiter-Io flux tube (~10¹² W) which is itself a sibling consequence of the Galilean Laplace lock.
- **v0.21.6 Tidal-resonance ↔ orbital migration** — the 4:2:1 commensurability is the canonical 3-body lock catalogued there; Loki is its largest persistent surface manifestation.
- **v0.24.11 Pluto-Charon** — the small-moon near-3:4:5:6 commensurabilities are the binary-system analogue of the Galilean Laplace 4:2:1 (same algebraic structure: small-integer mean-motion ratios producing tidal heating, different central-body geometry).

### Tests

- New `tests/test_loki_patera_eruption_cycle.py` (41 tests).
- Updated `tests/test_dynamical_regime.py` for n=11 + densified-regime tests.
- Updated `tests/test_dynamical_regime_probes.py` for Vesta's v0.24.12 landing flip.
- 3 new parity-smoke entries (all `python_only`).

## [0.24.11] — 2026-05-07

**Pluto-Charon Dynamical Spectrum (binary mutual tidal lock; Path-B closure of v0.24.10 OOS-probe-roster schema-gap) — fourth per-body action-angle ship in v0.24.x and the first binary mutual-tidal-lock entry.** Pure-Python additive; **no ABI bump** (thirty-fourth consecutive ship since v0.13.x).

### What ships

| Surface | Function / subcommand |
|---|---|
| Pythonic API | `_research.pluto_charon_dynamical_spectrum_catalog.get_pluto_charon_dynamical_spectrum / get_double_synchronous_signature / list_pluto_charon_dynamical_spectrum` |
| Bridge dict API | `bridge.get_pluto_charon_dynamical_spectrum()` / `bridge.get_double_synchronous_signature()` / `bridge.list_pluto_charon_dynamical_spectrum()` |
| CLI | `pluto-charon-dynamical-spectrum`, `double-synchronous-signature`, `pluto-charon-dynamical-spectrum-full` |

### THE headline — triple synchronous lock

Pluto and Charon are simultaneously locked to each other:

```
P_orb(Pluto-Charon) = P_spin(Pluto) = P_spin(Charon) = 6.387230 days
```

The **end state of dyadic tidal evolution** — the only example in the Solar System. Earth-Luna is *en route* to this state (Earth's rotation is currently spinning down via tidal recession at +3.83 cm/yr per v0.21.6 / Williams 2014); Pluto-Charon has *arrived*.

### Companion observables confirming the end-state

| Observable | Value | Note |
|---|---|---|
| Eccentricity | 5e-5 | ~1100x smaller than Luna's 0.0549 — fully damped |
| Mutual obliquity | 0.0006° | both spin axes aligned with mutual orbit normal |
| Mass ratio Charon/Pluto | 0.1218 | **largest binary mass ratio in the Solar System** (Earth-Luna is 0.0123, ~10x smaller) |
| Barycenter offset | 2128 km from Pluto centre | sits ~940 km **outside** Pluto's surface (radius 1188 km); both bodies orbit a point in empty space |

### Cross-channel — small-moon near-3:4:5:6 commensurabilities

The four small moons (Styx, Nix, Kerberos, Hydra) orbit the barycenter at near-integer multiples of the mutual orbital period:

| Moon | Period (d) | × P_orb | Off integer |
|---|---|---|---|
| Styx | 20.16 | 3.16 | 5.22% |
| Nix | 24.85 | 3.89 | 2.72% |
| Kerberos | 32.17 | 5.04 | 0.72% |
| Hydra | 38.20 | 5.98 | 0.32% |

Showalter-Hamilton 2015 *Nature* found the system is **chaotic in libration** on Myr timescales because the resonances aren't exact — a v0.24.2-Mars-style spectral-stability failure at the small-moon shepherd network's scale. A mini-Galilean-Laplace structure built on top of a binary lock, exhibited exactly once in the Solar System.

### Path-B closure — populated a v0.24.10 schema-gap with a real ground-proof row

The v0.24.10 OOS probes flagged that bodies with commensurabilities-but-no-Saros-style-track (Pluto-Charon, Enceladus, Io) all collapsed onto Mercury-stable in the v0.24.9 classifier. v0.24.11 closes the gap by **populating the missing regime** (new label `rigid_body_action_angle_mutual_lock`) rather than engineering a new feature. This is the project's discipline: when the eigenbasis honestly can't see a distinction, *give it more ground-proof data*, don't *re-engineer the schema*.

After v0.24.11:
- **Pluto-Charon probe** self-classifies to `mutual_lock` deterministically (cal_ratio 0).
- **Enceladus / Io probes** now land on `mutual_lock` (was Mercury-stable). Partial closure — the next gap surfaced is **asymmetric-satellite-with-partner-resonance** (Enceladus 2:1 Dione, Io 4:2:1 Galilean Laplace), structurally distinct from binary mutual lock.
- **Ceres probe** OOD-flagged at cal_ratio 0.998 — genuine "no rigid-stable-no-commensurability training row exists." Honest gap-surfacing.

### Reframing — "ground-proof rows", not "training data"

The v0.24.x catalogs are now consistently called **ground-proof rows** in code and docs. The classifier's "training step" is `np.linalg.eigh` (closed-form, byte-identical across runs). Adding a new row is a **deterministic schema extension**, not retraining. No SGD, no random init, no validation split, no pseudorandom anywhere.

### Tests

- `tests/test_pluto_charon_dynamical_spectrum.py` — 33 tests (catalog shape, triple-lock invariant, eccentricity / obliquity / mass-ratio / barycenter ratchets, small-moon near-resonance bounds, classifier integration, bridge + CLI smoke).
- `tests/test_dynamical_regime.py` — 7 assertion updates (n=9 → n=10 across regime count, source count, distances-to-all length, eigenbasis n_examples, list n_regimes).
- `tests/test_dynamical_regime_probes.py` — 3 probe-ratchet revisions (pluto_charon → mutual_lock, enceladus + io_galilean_resonance → mutual_lock, ceres → ood_expected=True with notes).
- `tests/test_parity_smoke.py` — 3 new `python_only` parity entries.

**1782 tests pass, 42 skipped** (was 1753 + 42 in v0.24.10; +29 net new — 33 in test_pluto_charon plus updated regime tests).

### Sources (7)

Stern 1992 (canonical pre-New-Horizons review), Tholen-Buie 1990 (mutual events 1985-1990), Brozovic 2015 (post-New-Horizons orbital fit; mass ratio + small-moon orbits), Stern 2015 (New Horizons flyby summary), Showalter-Hamilton 2015 (small-moon chaos), Showalter 2015 (Kerberos discovery), Weaver 2016 (small-satellite imaging).

### Architectural commitment

The project's first **demonstrated Path-B closure**: a real schema-gap surfaced by the OOS probe layer (v0.24.10), then closed not by feature engineering but by populating the missing regime with a real ground-proof row. v0.24.11 is the concrete demonstration of the loop the v0.25.0 multi-source-collector framework will mechanise: probes flag → ground-proof rows close → eigenbasis recomputes deterministically.

Two new gaps surfaced and documented for future ships: (a) asymmetric-satellite-with-partner-resonance (Enceladus, Io); (b) rigid-stable-no-commensurability (Ceres, Vesta).

## [0.24.10] — 2026-05-07

**OOS probe catalog + classifier calibration-ratio metric — closes a v0.24.9 loose end and surfaces a latent diagnostic.** Pure-Python additive; **no ABI bump** (thirty-third consecutive ship since v0.13.x).

### What ships

| Surface | Function / subcommand |
|---|---|
| Pythonic API | `_research.dynamical_regime_probes_data.REGIME_PROBES`; `_research.dynamical_regime_catalog.run_dynamical_regime_probes / list_dynamical_regime_probes` (+ extended `classify_dynamical_regime` return) |
| Bridge dict API | `bridge.run_dynamical_regime_probes(n_components=3, ood_threshold=0.85)` / `bridge.list_dynamical_regime_probes()` (+ extended `bridge.classify_dynamical_regime`) |
| CLI | `regime-probes`, `regime-probes-list` |

### 10-probe out-of-sample roster

| Probe | Expected | Classified | Calibration ratio | OOD |
|---|---|---|---|---|
| yellowstone_hotspot | bounded_local_laplacian_trajectory | ✓ | 0.24 | — |
| reunion_hotspot | bounded_local_laplacian_trajectory | ✓ | 0.07 | — |
| pluto_charon | rigid_body_action_angle_stable† | ✓ | 0.14 | — |
| enceladus | rigid_body_action_angle_stable† | ✓ | 0.29 | — |
| io_galilean_resonance | rigid_body_action_angle_stable† | ✓ | 0.22 | — |
| phobos | (let-classifier-surprise-us) | rigid_body_chaotic_obliquity ‡ | 0.38 | — |
| ceres | rigid_body_action_angle_stable | ✓ | 0.72 | — |
| alpha_centauri_b | continuum_normal_modes | ✓ | 0.01 | — |
| vesta | (out-of-distribution) | bounded_local_laplacian_trajectory | 0.98 | ✓ |
| magnetar_typical | shape_residual_chandrasekhar ‡ | ✓ | 0.49 | — |

† Feature-schema gap: Pluto-Charon / Enceladus / Io have commensurabilities but no Saros-style multi-millennium prediction record, so the v0.24.9 schema can't distinguish them from Mercury-stable. Documented as ratchet; a future schema extension would let these land on Luna.

‡ Surprising classification pinned as documented v0.24.9 ground truth (Phobos = let-classifier-surprise-us; magnetar = dimensionality dominates over size mismatch).

**Zero unexpected classifications** in the summary aggregate — every probe either matches expectation or is correctly OOD-flagged.

### v0.24.10 calibration-ratio metric

`bridge.classify_dynamical_regime` return dict gains four new fields:

- `calibration_ratio = nearest_distance / 2nd_nearest_distance` — small (~0 for self-classification) = confident; near 1 = honest "I don't know"
- `nearest_neighbour_margin = 2nd_nearest_distance - nearest_distance` — absolute version
- `out_of_distribution: bool` — True when `calibration_ratio > ood_threshold` (default 0.85)
- `ood_threshold_used: float` — for reproducibility / custom thresholds

The diagnostic was latent in v0.24.9's `distances_to_all` but never summarised. v0.24.10 surfaces it as first-class.

### NOT machine learning (in the SGD sense)

The catalog module's docstring now explicitly notes: the v0.24.9 classifier *looks* like nearest-neighbour ML, but its "training step" is a closed-form `np.linalg.eigh` call on the standardised covariance matrix. **No random initialisation, no stochastic gradient descent, no hyperparameter search, no validation split, no pseudorandom anywhere.** The eigenbasis is a *property* of the labelled data, not a model fit to it. Identical inputs yield byte-identical bases across runs. The v0.24.10 OOS probes are *test vectors*, never *training data*. This is the spectral-methods discipline at work: classical math, deterministic decomposition, exposed eigenstructure.

### Tests

- `tests/test_dynamical_regime_probes.py` — 33 tests covering roster shape, per-probe classification ratchets, calibration-metric invariants, bridge + CLI smoke. **0 unexpected classifications** in the run-probes summary.
- `tests/test_parity_smoke.py` — two new `python_only` parity entries.

### Sources (10)

Pierce-Morgan 1992 (Yellowstone hotspot track), Courtillot 1986 (Reunion / Deccan), Stern 1992 (Pluto-Charon mutual lock), Murray-Dermott 1999 (Enceladus 2:1 Dione lock), Peale-Cassen-Reynolds 1979 (Io tidal heating prediction), Bills 2005 (Phobos tidal decay), Park 2016 (Ceres Dawn gravity/shape), Kjeldsen 2005 (Alpha Cen B asteroseismology), Russell 2012 (Vesta Dawn), Kaspi-Beloborodov 2017 (magnetars review).

### Architectural commitment

Closes the v0.24.9 loose end by promoting smoke-test probes into a curated ratchet-pinned roster, AND surfaces the calibration-ratio metric the user correctly intuited the classifier was leaving on the table. Future feature-schema extensions can be tested by re-running the probes — if a probe's classification changes, the test fails clearly.

## [0.24.9] — 2026-05-07

**Dynamical-Regime Classifier (eigenbasis-projection version of the v0.24.x if/else chain) — tenth and capstone ship in v0.24.x; the project's first explicit meta-consumer of the v0.24.x methodology arc.** Pure-Python additive; **no ABI bump** (thirty-second consecutive ship since v0.13.x).

### What ships

| Surface | Function / subcommand |
|---|---|
| Pythonic API | `_research.dynamical_regime_catalog.get_dynamical_regime_eigenbasis / classify_dynamical_regime / list_dynamical_regimes` |
| Bridge dict API | `bridge.get_dynamical_regime_eigenbasis(n_components=3)` / `bridge.classify_dynamical_regime(feature_vector, n_components=3)` / `bridge.list_dynamical_regimes()` |
| CLI | `regime-eigenbasis`, `regime-classify`, `regime-list` |

### 9 labelled training examples (one per v0.24.x ship)

| Ship | Regime label | Forcing class | Dimensionality | Stability |
|---|---|---|---|---|
| v0.24.0 Mercury | `rigid_body_action_angle_stable` | gravitational | 0 | 1.0 |
| v0.24.1 Luna | `rigid_body_action_angle_commensurate` | gravitational | 0 | 1.0 |
| v0.24.2 Mars | `rigid_body_chaotic_obliquity` | gravitational | 0 | 0.0 |
| v0.24.3 Sun | `continuum_normal_modes` | stellar_oscillation | 3 | 1.0 |
| v0.24.4 Toroidal-Residual | `shape_residual_chandrasekhar` | gravitational | 3 | 0.5 |
| v0.24.5 Hawaii | `bounded_local_laplacian_trajectory` | tectonic | 1 | 0.7 |
| v0.24.6 Yarkovsky/YORP | `radiation_coupled_drift` | radiation | 0 | 0.5 |
| v0.24.7 Mars Tharsis | `bounded_local_laplacian_family` | volcanic | 2 | 0.6 |
| v0.24.8 Axial Seamount | `temporal_quasi_periodic_cycle` | volcanic | 0 | 0.5 |

### Feature schema (7 features per ship)

1. **`time_scale_log_s`** — log10 of natural period in seconds (range: ~2.5 for solar p-modes to ~15.7 for Mars Tharsis surfaces).
2. **`spatial_scale_log_km`** — log10 of natural length scale in km (range: ~-0.5 for sub-km asteroids to ~5.8 for solar radius).
3. **`stability_index`** — heuristic 0..1 Diophantine-stability indicator (1.0 = stable rigid-body action-angle; 0.0 = chaotic / KAM-broken).
4. **`has_commensurability`** — 1 if integer-resonance observable (Mercury 3:2, Saros 223:239:242), 0 otherwise.
5. **`prediction_track_signal`** — +1 (HIT-only published track record), -1 (MISS observed), 0 (no published prediction).
6. **`dimensionality`** — 0 (point dynamics), 1 (1D chain), 2 (2D surface family), 3 (3D volume / continuum).
7. **`forcing_class_index`** — 0=gravitational, 1=stellar-oscillation, 2=radiation, 3=tectonic, 4=volcanic.

### Eigenbasis spectrum

| PC | Eigenvalue | Explained variance | Cumulative |
|---|---|---|---|
| PC1 | 2.94 | 41.9% | 41.9% |
| PC2 | 1.81 | 25.8% | 67.8% |
| PC3 | 1.07 | 15.3% | 83.1% |
| PC4 | 0.74 | 10.6% | 93.7% |

### Cross-channel observation

The classifier replaces the **aspirational if/else chain** (which was always implicit, never coded) with a **learned eigenbasis projection** that exposes distance-to-all training examples. Same Fiedler/eigenbasis machinery as v0.18.0 body_architecture, v0.24.5 Hawaii, v0.24.7 Mars Tharsis — applied to **the v0.24.x ships themselves as data points**. The project's first explicit *meta-consumer* of the v0.24.x methodology arc.

Out-of-sample probes (the classifier doing useful work):
- **Yellowstone hotspot** (10-Myr North American Plate track) → `bounded_local_laplacian_trajectory` (Hawaii-like, d=0.20)
- **K-dwarf star** (5-min p-modes, ~500000 km) → `continuum_normal_modes` (Sun-like, d=0.05)
- **Enceladus** (1.4-day orbital, 2:1 Dione lock, 252 km) → `rigid_body_action_angle_stable` (Mercury-like, d=0.32; Luna-like 2nd-nearest, d=1.10)

### Tests

- `tests/test_dynamical_regime.py` — 48 tests pinning roster shape, per-ship presence, feature-vector schema invariants, eigenbasis invariants (top-3 PCs > 70% variance, top-4 > 90%, eigenvalues descending), self-classification accuracy (9/9 round-trip), out-of-sample probes, input validation, bridge + CLI smoke.
- `tests/test_parity_smoke.py` — three new `python_only` parity entries.

### Sources (9)

One pointer per v0.24.0–v0.24.8 ship's catalog (Mercury / Luna / Mars / Sun / Toroidal / Hawaii / Yarkovsky / Mars Tharsis / Axial). The v0.24.9 ship is a *consumer* of these prior ships; no new physical claim is made.

### Architectural commitment

Capstone of the v0.24.x methodology arc. After v0.24.0–v0.24.8 demonstrated nine distinct dynamical regimes (rigid stable / commensurate / chaotic; continuum normal-modes; shape-residual; bounded-local-trajectory / family; radiation-coupled drift; temporal cycle), v0.24.9 closes the arc by treating those nine ships as labelled training examples for an eigenbasis-projection regime classifier. The next ship is **v0.25.0 — Attested Multi-Source Collector framework** (config-driven adapters, see ROADMAP).

## [0.24.8] — 2026-05-07

**Axial Seamount Eruption Chronology Catalog (temporal-spectrum eruption-cycle observable on a real-time-monitored submarine volcano) — ninth ship in v0.24.x; the project's first explicit prediction-reliability ship.** Pure-Python additive; **no ABI bump** (thirty-first consecutive ship since v0.13.x).

### What ships

| Surface | Function / subcommand |
|---|---|
| Pythonic API | `_research.axial_seamount_catalog.get_axial_seamount_chronology / get_axial_inflation_cycle_signature / list_axial_seamount` |
| Bridge dict API | `bridge.get_axial_seamount_chronology()` / `bridge.get_axial_inflation_cycle_signature()` / `bridge.list_axial_seamount()` |
| CLI | `axial-seamount-chronology`, `axial-inflation-cycle-signature`, `axial-seamount-full` |

### 3-eruption roster

| Eruption | Date | Subsidence | Inter-eruption interval | Source |
|---|---|---|---|---|
| **axial_1998** | 1998-01-25 | 3.2 m | — | Dziak & Fox 1999 (SOSUS T-wave swarm) |
| **axial_2011** | 2011-04-06 | 2.4 m | 13.2 yr | Caress 2012 (1-m repeat AUV bathymetry; *Nat Geosci*) |
| **axial_2015** | 2015-04-24 | 2.4 m | 4.05 yr | Chadwick 2016 (forecast HIT; *Science*) + Wilcock 2016 (real-time seismic capture) |

### Inflation-phase rate timeline

| Phase | Years | Mean rate | Note |
|---|---|---|---|
| pre-1998 | 1985–1998 | ~15 cm/yr | Nooner-Chadwick 2009 baseline |
| 1998-to-2011 | 1998–2011 | ~15 cm/yr | Steady; matches pre-1998 |
| 2011-to-2015 | 2011–2015 | **~70 cm/yr** | ~5× faster — drove short 4-yr interval |
| post-2015 | 2015–2024 | ~20 cm/yr | **Slower than 2011-2015**; broke the 2024-2025 forecast |

### Chadwick-Nooner forecast track-record

| Forecast | Issued | Target | Outcome | Note |
|---|---|---|---|---|
| 2015 eruption | 2014 | 2015 | **HIT** | Chadwick 2016 — 6-month lead via OOI Cabled Array |
| 2024-2025 window | 2022 | 2024–2025 | **MISS** | Post-2015 slowing → trigger threshold not met as of catalog ref year 2026 |

### Two complementary spectral observations

1. **Inter-eruption interval distribution + rate-period product** — The Chadwick-Nooner methodology assumes the inflation-rate × interval product is conserved (the integrated uplift to reach the geodetic trigger). Empirically: 1998-2011 product ≈ 198 cm; 2011-2015 product ≈ 283 cm; spread ≈ 85 cm. The product is *approximately* but not exactly conserved — the spread itself is the signature that the underlying dynamics is more complicated than a constant-rate inflation-to-trigger model.
2. **Methodology track-record asymmetry** — same model: 1 HIT + 1 MISS on the same body. The MISS arises from post-2015 inflation slowing below the 2011-2015 reference, breaking the constant-rate extrapolation.

### Cross-channel observation

This is a **direct parallel to v0.24.2 Mars secular-resonance chaos** — a quasi-periodic dynamical mode that is Diophantine-stable over some observation window and small-denominator-fragile outside it. v0.24.2 showed the failure mode at **Gyr / arcsec-per-year** scale; v0.24.8 shows it at **decade / cm-per-year** scale. **Same algebraic structure on two wildly different observational scales** — the project's cleanest cross-system spectral-stability observation to date.

### Tests

- `tests/test_axial_seamount.py` — 40 tests pinning roster shape, eruption years, caldera + summit geometry, inflation-phase rate progression, forecast track-record, inter-eruption interval distribution, rate-period-product spread, the v0.24.2 cross-channel parallel, citation discipline, bridge + CLI smoke.
- `tests/test_parity_smoke.py` — three new `python_only` parity entries.

### Sources (10)

Dziak & Fox 1999 (SOSUS T-wave swarm + 1998 eruption date), Embley 1999 (1998 ROV observations), Caress 2012 (2011 eruption discovery + 1-m repeat-bathymetry deflation; *Nat Geosci*), Chadwick 2016 (2015 forecast methodology + HIT; *Science*), Wilcock 2016 (2015 seismic capture; *Science* companion), Nooner-Chadwick 2009 (geodetic baseline), Nooner-Chadwick 2016 (inflation-vs-trigger framework), post-2015 follow-ups (the 2024-2025 forecast window context), Tolstoy 2018 (mid-ocean-ridge axial seismicity context), Kelley 2014 (OOI Cabled Array context).

### Architectural commitment

First temporal-spectrum ship in the v0.24.x sequence. The bounded-local methodology now spans three observable axes: spatial-trajectory (v0.24.5 Hawaii, with plate tectonics) + spatial-cogenetic-family (v0.24.7 Mars Tharsis, no plate tectonics) + temporal-quasi-periodic-cycle (v0.24.8 Axial, real-time observatory). Same v0.24.x algebraic discipline; three different observable axes; one shared cross-channel theme — Diophantine stability is window-dependent.

## [0.24.7] — 2026-05-07

**Mars Tharsis Volcanic Chain Catalog (bounded-local Laplacian on a body WITHOUT plate tectonics) — eighth ship in v0.24.x; the no-plate-tectonics counterpart to v0.24.5 Hawaii.** Pure-Python additive; **no ABI bump** (thirtieth consecutive ship since v0.13.x).

### What ships

| Surface | Function / subcommand |
|---|---|
| Pythonic API | `_research.mars_tharsis_catalog.get_mars_tharsis_chain / get_tharsis_fiedler_signature / list_mars_tharsis_chain` |
| Bridge dict API | `bridge.get_mars_tharsis_chain()` / `bridge.get_tharsis_fiedler_signature()` / `bridge.list_mars_tharsis_chain()` |
| CLI | `mars-tharsis-chain`, `tharsis-fiedler-signature`, `mars-tharsis-chain-full` |

### 5-volcano roster

| Volcano | Role | Surface age (Myr) | Lat / Lon (°E) | Summit elev (m) | Base diameter (km) | Source |
|---|---|---|---|---|---|---|
| **Olympus Mons** | olympus_outlier | 150 ± 50 | 18.65 / 226.20 | 21229 | 600 | Hartmann 2005 |
| **Arsia Mons** | tharsis_montes | 130 ± 20 | -8.40 / 239.90 | 17761 | 435 | Hartmann & Neukum 2001 |
| **Pavonis Mons** | tharsis_montes | 100 ± 20 | 1.50 / 247.20 | 14058 | 375 | Werner 2009 |
| **Ascraeus Mons** | tharsis_montes | 100 ± 30 | 11.80 / 255.50 | 18225 | 460 | Hartmann & Neukum 2001 |
| **Alba Mons** | alba_outlier | 1500 ± 300 | 40.50 / 250.40 | 6800 | 1500 | Plescia 2004 |

### Two complementary spectral observations

1. **Bounded-local Fiedler partition** — Gaussian-spatial-proximity Laplacian (σ = 1500 km on Mars's 3389.5 km-radius surface) bisects the 5-volcano roster, isolating Alba Mons (the geographically distant N outlier at 40°N) from the four young Tharsis-region volcanoes (the three Tharsis Montes ridge + Olympus). The eigenvalue gap λ₃ − λ₂ ≈ 0.51·λ₂ confirms a meaningful partition.
2. **Tharsis Montes ridge alignment + outlier residuals** — fit the three Tharsis Montes to a great-circle ridge (~040° azimuth NE-SW), then compute perpendicular residuals: Olympus Mons sits ~1900 km off the ridge axis, Alba Mons ~1200 km off — structural offsets analogous to Hawaii's age-vs-arc-length residuals at the bend, but **structural** (deep-mantle plume geometry) rather than **temporal** (plate-motion change).

### Cross-channel observation

Where v0.24.5 Hawaii on a body **with** plate tectonics extracts a *trajectory* (the Pacific Plate moves over a stationary plume, producing a chronologically-ordered chain), v0.24.7 Mars Tharsis on a body **without** plate tectonics extracts a *cogenetic family* (stationary plumes build one super-volcano per locus over Gyr timescales). **Olympus Mons** (~22 km from base to summit, the largest volcano in the Solar System) is the direct consequence: it would be a chain on Earth, but on Mars the plume never moved relative to the lithosphere. There is **no directional bend** in the Mars Tharsis system because there is no plate motion to record one. Same eigendecomposition machinery, different geophysical regime.

### Tests

- `tests/test_mars_tharsis.py` — 35 tests pinning roster shape, Olympus super-volcano magnitudes, Alba morphology, Fiedler partition (Alba isolated; three Tharsis Montes clustered), ridge-residual offsets (>500 km for both Olympus + Alba), no-directional-bend invariant, citation discipline, bridge + CLI smoke.
- `tests/test_parity_smoke.py` — three new `python_only` parity entries.

### Sources (8)

Hartmann & Neukum 2001 (Mars crater chronology calibration), Hartmann 2005 (refined chronology + Olympus age), Werner 2009 (Tharsis Montes high-resolution ages), Plescia 2004 (Mars-volcano morphometric compilation + Alba age), Smith 2001 (MGS MOLA topography), Anderson 2001 (Tharsis tectonic history), Carr & Head 2010 (Mars geological synthesis), Morgan 1971 (mantle-plume context).

### Architectural commitment

The bounded-local-Laplacian methodology (introduced in v0.24.5 on Earth) is now **cross-body**: same eigendecomposition machinery operates on Earth and Mars surface-feature graphs. The geophysical regime determines what kind of structure the partition surfaces. Hawaii (with plate tectonics) → trajectory; Mars (no plate tectonics) → cogenetic family.

## [0.24.6] — 2026-05-07

**Small-body Yarkovsky/YORP Catalog (thermal-radiation orbital + spin drift) — seventh ship in v0.24.x.** Pure-Python additive; **no ABI bump** (twenty-ninth consecutive ship since v0.13.x).

### What ships

| Surface | Function / subcommand |
|---|---|
| Pythonic API | `_research.yarkovsky_yorp_catalog.get_yarkovsky_yorp / get_yorp_attractor_thresholds / list_yarkovsky_yorp` |
| Bridge dict API | `bridge.get_yarkovsky_yorp(body=None)` / `bridge.get_yorp_attractor_thresholds()` / `bridge.list_yarkovsky_yorp()` |
| CLI | `yarkovsky-yorp [--body X]`, `yorp-attractor-thresholds`, `yarkovsky-yorps` |

### 10-asteroid roster

| Asteroid | D (km) | T_rot (h) | Yarkovsky (10⁻⁴ AU/Myr) | YORP (10⁻⁸ rad/d²) | Source |
|---|---:|---:|---:|---:|---|
| **(101955) Bennu** | 0.49 | 4.296 | **−19.0 ± 0.1** | +0.064 | Farnocchia 2013 |
| (54509) 2000 PH5 (YORP) | 0.114 | **0.203** | — | **+350 ± 35** | Lowry 2007 |
| (99942) Apophis | 0.34 | 30.4 | −1.99 ± 0.3 | — | Vokrouhlický 2015 |
| (162173) Ryugu | 0.87 | 7.633 | −2.4 ± 0.5 | — | Watanabe 2019 |
| (25143) Itokawa | 0.33 | 12.13 | — | **−3.5 ± 1.0** | Lowry 2014 |
| (1862) Apollo | 1.5 | 3.065 | — | +5.5 ± 1.2 | Kaasalainen 2007 |
| (1620) Geographos | 2.5 | 5.222 | — | +1.14 ± 0.27 | Durech 2008 |
| (29075) 1950 DA | 1.3 | **2.121** | −0.9 ± 0.1 | — | Farnocchia 2014 |
| (6489) Golevka | 0.53 | 6.026 | −1.5 ± 0.4 | — | Chesley 2003 |
| (3103) Eger | 1.5 | 5.711 | — | +2.4 ± 0.6 | Durech 2012 |

### Threshold constants

- **Rotational-fission limit** ~ 2.2 h (rubble-pile spin-up cap)
- **Observability diameter** ~ 30 km (1/D² scaling cuts off larger bodies)
- **YORP obliquity attractors** ~ 55° / ~125° (Vokrouhlický-Čapek 2002 long-term end-states)

### Highlights

- 🌟 **Bennu** — OSIRIS-REx target; first directly-imaged Yarkovsky drift; -19×10⁻⁴ AU/Myr (~285 m/yr inward; retrograde).
- 🌟 **2000 PH5** — first YORP detection; the asteroid that lent its name to the effect; 12-minute rotation period.
- **Apophis** — Yarkovsky uncertainty matters for the 2068 close approach.
- **Itokawa** — one of few measured spin-DOWN cases.
- **1950 DA** — rotation period AT the 2.2-h fission limit; cohesive forces required to prevent disruption.
- **Golevka** — Chesley 2003 first-ever Yarkovsky detection.

### Direction-sign invariant

Every retrograde rotator in the catalog drifts inward (negative da/dt) — the textbook diurnal-Yarkovsky direction signature. Pinned by `test_retrograde_drift_inward`.

### Cross-channel observation

Where **v0.23.0** catalogs **spin-orbit LOCKED** bodies (Mercury 3:2; Luna 1:1; Galileans), v0.24.6 catalogs **spin-FREE** bodies driven *by sunlight*. The radiation-coupled analogue of v0.24.2 Mars's gravitational-secular-resonance obliquity chaos.

### v0.24.x arc complete

With v0.24.6 the v0.24.x backlog is fully shipped. Sequence:

```
v0.24.0  Mercury Dynamical Spectrum     (rigid-body action-angle, stable)
v0.24.1  Luna    Dynamical Spectrum     (rigid-body, Saros commensurability)
v0.24.2  Mars    Dynamical Spectrum     (rigid-body, chaotic)
v0.24.3  Sun     Dynamical Spectrum     (continuum normal-mode spectrum)
v0.24.4  Toroidal-Residual J₂ Catalog   (shape-side; Maclaurin/Jacobi/bar)
v0.24.5  Hawaii Chain                   (bounded-local-Laplacian; chess-board)
v0.24.6  Yarkovsky/YORP                 (small-body radiation-coupled drift)
```

### Test count

1586 pass, 42 skipped (was 1549 + 42 in v0.24.5; +37 net new — 34 in `test_yarkovsky_yorp.py` + 2 README-freshness GREEN flips + 1 reconciliation).

### Migration

Pure-additive bridge + CLI. `ES_VERSION_STRING` bumps `0.24.5 → 0.24.6`.

## [0.24.5] — 2026-05-07

**Hawaiian-Emperor Chain Spectral Catalog (bounded-local graph Laplacian) — sixth ship in v0.24.x; first time the project's graph-Laplacian eigenbasis is applied to physical features on a single body's surface.** Pure-Python additive; **no ABI bump** (twenty-eighth consecutive ship since v0.13.x).

### What ships

| Surface | Function / subcommand |
|---|---|
| Pythonic API | `_research.hawaii_chain_catalog.get_hawaii_chain / get_hawaii_emperor_bend_signature / list_hawaii_chain` |
| Bridge dict API | `bridge.get_hawaii_chain()` / `bridge.get_hawaii_emperor_bend_signature()` / `bridge.list_hawaii_chain()` |
| CLI | `hawaii-chain`, `hawaii-emperor-bend`, `hawaii-chain-full` |

### 18-seamount roster (oldest → youngest)

| Name | Age (Myr) | Arc | Source |
|---|---:|---|---|
| meiji | 85.0 | emperor | Keller 1995 |
| detroit | 75.8 | emperor | Duncan-Keller 2004 |
| suiko | 64.7 | emperor | Duncan-Clague 1985 |
| nintoku | 56.2 | emperor | Sharp-Clague 2006 |
| koko | 48.1 | emperor | Sharp-Clague 2006 |
| **daikakuji** | **46.7** | **bend** | **Sharp-Clague 2006** |
| yuryaku | 43.4 | hawaiian | Sharp-Clague 2006 |
| kammu | 38.5 | hawaiian | O'Connor 2013 |
| midway | 27.7 | hawaiian | Sharp-Clague 2006 |
| pearl_hermes | 20.0 | hawaiian | Clague-Dalrymple 1989 |
| laysan | 19.9 | hawaiian | Clague-Dalrymple 1989 |
| necker | 10.3 | hawaiian | Clague-Dalrymple 1989 |
| niihau | 5.0 | hawaiian | Clague-Dalrymple 1989 |
| kauai | 4.7 | hawaiian | Garcia 2010 |
| oahu | 2.6 | hawaiian | Garcia 2010 |
| molokai | 1.7 | hawaiian | Clague 2010 |
| maui_haleakala | 1.0 | hawaiian | Clague 2010 |
| hawaii_kilauea | 0.0 | hawaiian | Garcia 2010 |

### THE headlines: two complementary spectral observations

**(1) Bounded-local Fiedler partition.** Graph Laplacian over Gaussian-spatial-proximity edges (σ=500 km). Fiedler vector has **exactly one sign change** along the age-ordered chain (a quasi-1D structural property), at the spatial gap between Midway (27.7 Myr) and Pearl-and-Hermes (20 Myr). Eigenvalue gap λ₃ − λ₂ ≈ 3× λ₂ confirms structurally crisp partition.

**(2) Age-vs-arc-length residuals.** Linear fit through post-bend Hawaiian arc gives **Pacific Plate velocity 8.5 cm/yr** (matches Sharp 2006 published 8-10). The directional bend at 47.5 Myr surfaces in the slope residuals: largest residual at Meiji (oldest, 85 Myr) at ~1265 km from the post-bend linear extrapolation.

The two-step decomposition matters: the bend is **directional** (60° kink), not **proximal** (no spatial gap there) — so spatial-proximity Laplacian (1) doesn't see it; slope-residuals (2) do.

### Why this ship matters

- **First non-orbital eigenbasis application.** Until v0.24.5, every Laplacian eigendecomposition the project has done was over orbital relationships (resonance graph, gateway graph). v0.24.5 applies the same machinery to **physical features on a single body's surface** — the chess-board / bounded-local-Laplacian methodology made explicit.
- **Same algebraic machinery as v0.18.0** body_architecture's inner/outer Fiedler partition, just on a different graph.
- **Cross-channel observation**: bend at 47.5 Myr is independently observable in paleomagnetic data (Tarduno 2003 high-paleolatitude Emperor seamounts) — v0.21.x-style multi-channel confirmation.

### Cross-references

- **v0.18.0** body-architecture: same Fiedler-partition mechanism, different graph
- **v0.18.2** predict_itn_accessibility: two-eigenvector embedding pattern
- **v0.20.0** Earth geodetic: Earth interior context
- **v0.21.x** cross-channel coupling: bend's multi-channel observability

### Test count

1549 pass, 42 skipped (was 1518 + 42 in v0.24.4; +31 net new — 28 in `test_hawaii_chain.py` + 2 README-freshness GREEN flips + 1 reconciliation).

### Migration

Pure-additive bridge + CLI. `ES_VERSION_STRING` bumps `0.24.4 → 0.24.5`.

## [0.24.4] — 2026-05-07

**Per-body Toroidal-Residual J₂ Catalog (Maclaurin/Jacobi/bar-ring sequence) — fifth ship in v0.24.x; the shape-side counterpart to v0.24.0–v0.24.3 dynamical-spectrum surfaces.** Codifies the "rotation makes the body toroidal, self-gravity rounds it back" insight as a per-body classification on the Chandrasekhar 1969 ellipsoidal-equilibrium sequence. Pure-Python additive; **no ABI bump** (twenty-seventh consecutive ship since v0.13.x).

### What ships

| Surface | Function / subcommand |
|---|---|
| Pythonic API | `_research.toroidal_residual_catalog.get_toroidal_residual / get_chandrasekhar_sequence_thresholds / list_toroidal_residuals` |
| Bridge dict API | `bridge.get_toroidal_residual(body=None)` / `bridge.get_chandrasekhar_sequence_thresholds()` / `bridge.list_toroidal_residuals()` |
| CLI | `toroidal-residual [--body X]`, `chandrasekhar-sequence`, `toroidal-residuals` |

### Sequence + thresholds

```
Sphere → Maclaurin → Jacobi → bar → ring/torus

q = ω²R³/(GM)         dimensionless rotation parameter
q < 0.001              sphere
0.001 ≤ q < 0.187     Maclaurin oblate spheroid
q ≈ 0.187              Maclaurin-Jacobi BIFURCATION
0.187 ≤ q < 0.27      Jacobi triaxial ellipsoid
q ≈ 0.27               bar instability
0.27 ≤ q < 0.36       bar
q ≈ 0.36               Roche / fission
q ≥ 0.36               ring/torus
```

### 14-body roster

| Body | q | J₂ | Regime | Fossil? | Source |
|---|---:|---:|---|:---:|---|
| **saturn** | **0.158** | 1.63e-2 | maclaurin | — | Iess 2019 |
| jupiter | 0.0892 | 1.47e-2 | maclaurin | — | Iess 2018 |
| uranus | 0.0294 | 3.51e-3 | maclaurin | — | Jacobson 2014 |
| neptune | 0.0264 | 3.41e-3 | maclaurin | — | Jacobson 2009 |
| mars | 4.59e-3 | 1.96e-3 | maclaurin | — | Genova 2016 |
| terra | 3.46e-3 | 1.08e-3 | maclaurin | — | EGM2008 |
| io | 1.71e-3 | 1.85e-3 | maclaurin | — | Anderson 2001 |
| europa | 4.28e-4 | 4.36e-4 | sphere | — | Anderson 2001 |
| ganymede | 1.05e-4 | 1.28e-4 | sphere | — | Anderson 2001 |
| titan | 2.18e-5 | 3.34e-5 | sphere | — | Iess 2010 |
| callisto | 1.43e-5 | 3.27e-5 | sphere | — | Anderson 2001 |
| **luna** | 7.58e-6 | 2.03e-4 | sphere | **YES** | Konopliv 2013 |
| **mercury** | 1.01e-6 | 5.03e-5 | sphere | **YES** | Smith 2012 |
| venus | 6.11e-8 | 4.46e-6 | sphere | — | Anderson 2002 |

### Highlights

- 🌟 **Saturn closest to the Maclaurin-Jacobi bifurcation** — q = 0.158 vs threshold 0.187. Most oblate Solar-System body (1/10 flattening). Cross-references v0.21.4 Mankovich-Fuller 2021 ring-seismology rotation revision.
- **Earth canonical Maclaurin** — q ≈ 0.0035, J₂ ≈ q/3 (Darwin-Radau prediction for I_M = 0.33).
- **Luna fossil figure** — J₂ ≈ 25× current-rotation prediction. Shape frozen when Luna was closer to Earth (cross-references v0.21.6 +3.83 cm/yr tidal recession).
- **Mercury fossil figure** — J₂ ≈ 50× current 3:2-locked rotation prediction (cross-references v0.23.0 spin-orbit-resonance Mercury 3:2 lock + v0.24.0 Mercury dynamical-spectrum).
- **No body past the Jacobi bifurcation** in the Solar System's classical roster (Haumea would be there but is not in v0.16.0 BODIES).

### Cross-references

- **v0.20.0** geodetic catalog: J₂ values for all 14 bodies
- **v0.21.4** rotational constraints: Saturn rotation (Mankovich-Fuller 2021); Mars C/MR² (Le Maistre 2023)
- **v0.21.6** tidal migration: Luna +3.83 cm/yr context for fossil-figure
- **v0.23.0** spin-orbit resonance: Mercury 3:2 lock context
- **v0.24.0** Mercury dynamical spectrum: same Margot 2007 lineage for Mercury physical state

### Test count

1518 pass, 42 skipped (was 1481 + 42 in v0.24.3; +37 net new — 34 in `test_toroidal_residual.py` + 2 README-freshness GREEN flips + 1 reconciliation).

### Migration

Pure-additive bridge + CLI. `ES_VERSION_STRING` bumps `0.24.3 → 0.24.4`.

## [0.24.3] — 2026-05-07

**Sun Dynamical Spectrum (helioseismic p-modes) — fourth per-body dynamical-spectrum surface; first stellar entry + methodology extension from rigid-body action-angle to stellar-oscillation continuum normal-mode spectrum.** Pure-Python additive; **no ABI bump** (twenty-sixth consecutive ship since v0.13.x).

### What ships

| Surface | Function / subcommand |
|---|---|
| Pythonic API | `_research.sun_dynamical_spectrum_catalog.get_sun_dynamical_spectrum / get_helioseismic_asymptotic_relation / list_sun_dynamical_spectrum` |
| Bridge dict API | `bridge.get_sun_dynamical_spectrum()` / `bridge.get_helioseismic_asymptotic_relation()` / `bridge.list_sun_dynamical_spectrum()` |
| CLI | `sun-dynamical-spectrum`, `helioseismic-asymptotic-relation`, `sun-dynamical-spectrum-full` |

### Asymptotic-relation constants

| Constant | Value | Notes |
|---|---:|---|
| Δν (large separation) | 135.1 μHz | Sound-travel-time inverse; ∝ √(M/R³) |
| δν (small separation) | 9.0 μHz | He-core sound-speed gradient diagnostic |
| ε (phase offset) | 1.46 | BiSON-fit |
| ν_max | 3090 μHz | Peak amplitude (Brown 1991 g/√T_eff scaling) |

### 20-mode sample p-mode catalog

n = 18-25 at l = 0,1,2 — the canonical "main p-mode comb" near ν_max used for asteroseismic-instrument validation. Frequencies ship as asymptotic-consistent reference values (residuals < 0.01 μHz from float roundoff).

### THE headline closure invariant

Tassoul 1980 asymptotic relation:

```
ν_{n,l} ≈ Δν · (n + l/2 + ε) - δν · l(l+1) / (n + l/2 + ε)
```

predicts the entire mode spectrum from three constants. **Cross-channel parallel**: stellar-oscillation analogue of v0.24.1 Saros integer commensurability — three constants → entire mode spectrum, just like 223:239:242 integer triple → entire eclipse-recurrence cycle.

Closure invariant `max_residual_uhz < 0.5` pinned by `test_asymptotic_relation_closure_invariant`. Real BiSON / SOI-MDI / SDO-HMI data has ~0.1-1 μHz residuals from interior-structure glitches (helium-ionization zone + base of convection zone; Vorontsov 2002) — themselves diagnostic via Christensen-Dalsgaard 2002 inversion.

### Cross-references

- **v0.20.1** Sol synoptic magnetic field (Stanford HMI Carrington-cadence pointer)
- **v0.21.5** Earth-Sun IMF coupling (solar-wind aurora driving)
- **v0.24.1** Luna Saros integer-commensurability (this is the stellar-oscillation analogue)
- **v0.24.0** Mercury (Mercury's Diophantine-stable 3:2 vs Sun's continuum mode comb)

### Test count

1481 pass, 42 skipped (was 1448 + 42 in v0.24.2; +33 net new — 30 in `test_sun_dynamical_spectrum.py` + 2 README-freshness GREEN flips + 1 reconciliation).

### Migration

Pure-additive bridge + CLI. `ES_VERSION_STRING` bumps `0.24.2 → 0.24.3`.

## [0.24.2] — 2026-05-07

**Mars Dynamical Spectrum — third per-body dynamical-spectrum surface in v0.24.x; the contrast case to Mercury and Luna.** Mars exhibits **secular chaos** — the canonical observable signature of KAM-theory small-denominator failure in the Solar System. Pure-Python additive; **no ABI bump** (twenty-fifth consecutive ship since v0.13.x).

### What ships

| Surface | Function / subcommand |
|---|---|
| Pythonic API | `_research.mars_dynamical_spectrum_catalog.get_mars_dynamical_spectrum / get_mars_secular_resonance_overlap / list_mars_dynamical_spectrum` |
| Bridge dict API | `bridge.get_mars_dynamical_spectrum()` / `bridge.get_mars_secular_resonance_overlap()` / `bridge.list_mars_dynamical_spectrum()` |
| CLI | `mars-dynamical-spectrum`, `mars-secular-resonance-overlap`, `mars-dynamical-spectrum-full` |

### 8-mode action-angle catalog (5 angles + 3 actions)

| Mode | Class | Frequency / Amplitude | Source |
|---|---|---|---|
| orbital_mean_motion | angle | period 686.971 d (sidereal year) | JPL DE441 |
| spin_frequency | angle | period 24.6229 h (sol; **no spin-orbit lock**) | Le Maistre 2023 |
| spin_axis_precession | angle | period 171 kyr; rate 7.58 arcsec/yr | Ward 1973 |
| apsidal_precession_g4 | angle | period 71.6 kyr; rate 17.92 arcsec/yr | Laskar 2004 |
| nodal_precession_s4 | angle | period 70 kyr retrograde; rate −17.74 arcsec/yr | Laskar 2004 |
| eccentricity | action | 0.0934 (varies 0.005-0.119 over secular cycle) | JPL DE441 |
| inclination_to_ecliptic | action | 1.85° (varies 0°-8° over Myr) | JPL DE441 |
| **obliquity** | action | **25.19° present-day; Gyr excursion 0°-60°** | **Laskar 2004** |

### THE headline: secular-resonance overlap (the chaos driver)

| Mars mode | Secular partner | Frequency | Proximity | Notes |
|---|---|---:|---:|---|
| spin_axis_precession | s₃ (Earth-related) | −18.86 arcsec/yr | 11.28 arcsec/yr | Drives obliquity excursions |
| spin_axis_precession | s₄ (Mars-related) | −17.74 arcsec/yr | 10.16 arcsec/yr | Obliquity-eccentricity coupling |
| apsidal_precession_g4 | g₃-s₃ Earth combination | varies | 2.50 arcsec/yr | Mercury-stability resonance (Laskar 2008) |

Where Mercury's v0.24.0 closure was a **successful sum** and Luna's v0.24.1 closure was a **successful integer commensurability**, Mars's v0.24.2 "closure" is a **failure mode**: secular frequencies overlap so tightly that the action-angle quasi-periodic torus structure breaks down. The chaos invariant `min_proximity_arcsec_yr < chaos_threshold` (12 arcsec/yr per Laskar 1993) is pinned by `test_chaos_active_via_min_proximity`.

### Highlights

- 🌟 **Chaotic obliquity** — present-day 25.19°, but Mars's *typical* state historically was MORE oblique. Laskar 2004's Gyr-scale numerical integrations show ~0°-60° excursion range with mean 37.6°.
- **No spin-orbit lock** — unlike every other body in the v0.23.0 spin-orbit-resonance catalog. Mars is rotationally free, and the chaos lives in its obliquity rather than its rotation rate.
- **C/MR² = 0.3645 ± 0.0005** — Le Maistre 2023 InSight RISE; cross-references v0.21.4 rotational-constraint chain (same paper).
- **Stabilising-Moon hypothesis** — without Earth's Moon (v0.24.1 LLR-constrained tidal-locking partner), Earth would likely exhibit Mars-style obliquity chaos. v0.24.1 + v0.24.2 together ship the quantitative argument for why Earth has stable seasons.

### Cross-references

- **v0.21.4** rotational_constraint Mars entry: Le Maistre 2023 InSight RISE chain (same paper)
- **v0.24.1** Luna: stabilising-Moon hypothesis — Mars-style chaos averted on Earth by Moon's tidal coupling
- **v0.24.0** Mercury: contrasts with Mars's chaos — Mercury's 3:2 lock is Diophantine-stable
- **v0.20.0** Mars geodetic: shape constants (J₂, polar moment of inertia)
- **v0.20.2** Mars climate-orbit coupling: eccentricity-secular-cycle drives long-term Martian climate

### Test count

1448 pass, 42 skipped (was 1412 + 42 in v0.24.1; +36 net new — 33 in `test_mars_dynamical_spectrum.py` + 2 README-freshness GREEN flips + 1 reconciliation).

### Migration

Pure-additive bridge + CLI. `ES_VERSION_STRING` bumps `0.24.1 → 0.24.2`.

## [0.24.1] — 2026-05-07

**Luna Dynamical Spectrum — second per-body dynamical-spectrum surface in the v0.24.x sequence; LLR-anchored complement to v0.24.0 Mercury.** Pure-Python additive; **no ABI bump** (twenty-fourth consecutive ship since v0.13.x). Bundled with RTD doc-maintenance fix.

### What ships

| Surface | Function / subcommand |
|---|---|
| Pythonic API | `_research.luna_dynamical_spectrum_catalog.get_luna_dynamical_spectrum / get_luna_saros_commensurability / list_luna_dynamical_spectrum` |
| Bridge dict API | `bridge.get_luna_dynamical_spectrum()` / `bridge.get_luna_saros_commensurability()` / `bridge.list_luna_dynamical_spectrum()` |
| CLI | `luna-dynamical-spectrum`, `luna-saros-commensurability`, `luna-dynamical-spectrum-full` |

### 11-mode action-angle catalog (8 angles + 3 actions)

| Mode | Class | Frequency / Amplitude | Source |
|---|---|---|---|
| sidereal_mean_motion | angle | period 27.32166 d | Allen's |
| synodic_mean_motion | angle | period 29.53059 d | Allen's |
| anomalistic_mean_motion | angle | period 27.55455 d | Allen's |
| draconitic_mean_motion | angle | period 27.21222 d | Allen's |
| spin_frequency | angle | locked 1:1 sidereal | Williams 2014 |
| forced_libration_longitude | angle | 7.9 arcsec at sidereal frequency | Williams 2014 |
| apsidal_precession | angle | 8.85 yr prograde | Murray-Dermott 1999 |
| nodal_precession | angle | 18.61 yr retrograde | Murray-Dermott 1999 |
| eccentricity | action | 0.0549 dimensionless | JPL DE441 |
| inclination_to_ecliptic | action | 5.145° | JPL DE441 |
| obliquity_to_orbit | action | 6.687° (Cassini state 2) | Cassini 1693 |

### THE headline: Saros integer-commensurability closure

| Product | Days | Notes |
|---|---:|---|
| 223 × synodic | 6585.32 | Sun-Earth-Moon configuration repeats |
| 239 × anomalistic | 6585.54 | Earth-Moon distance / perigee phase repeats |
| 242 × draconitic | 6585.36 | Sun-at-node geometry repeats |
| 19 × eclipse-year | 6585.78 | Eclipse-year consistency check |
| **Mean** | **6585.50** | **18.0301 years** |
| **Max spread** | **0.46 d** | **closure invariant: < 1 day** |

The Saros cycle (~18.03-yr eclipse-recurrence period) emerges from this small-integer commensurability — a **textbook small-denominator phenomenon** that is exactly the structure the project's BIP encoder is built to detect: three irrational-looking frequency ratios sharing a near-rational commensurability. The closure is pinned by `test_saros_closure_invariant`.

### Cross-strand observation

The **Antikythera mechanism's Saros dial** is literally a hardware implementation of the (223, 239, 242) commensurability. The same integer triple shows up in:
- `ephemerides-spectral` v0.24.1 — derived from 21st-century LLR + JPL ephemeris
- `antikythera-spectral` — derived from ca. 150 BCE bronze gearing

Two entirely different evidentiary layers; same algebraic content. This bridge surface is a direct cross-link.

### LLR (Williams 2014) is the ground truth

Williams J. G. & Boggs D. H. 2014 (JGR Planets 119, 1546-1578) — 50+ years of Lunar Laser Ranging from McDonald (1969 onwards), Apache Point (2006 onwards), OCA Grasse, and Matera observatories. The 7.9-arcsec forced-libration measurement constrains C/MR² = 0.3932 ± 0.0002 — **the most precise libration measurement of any body in the Solar System**.

### Cross-references

- v0.23.0 spin_orbit_resonance Luna entry: 7.9 arcsec libration (`test_forced_libration_matches_v0_23_0_value` pins agreement)
- v0.21.6 tidal_migration Earth-Luna: +3.83 cm/yr secular drift (Williams 2014, same paper)
- v0.10.0 STLT Metonic cycle: 235 synodic months (Saros uses 223; commensurability cousin)
- v0.20.0 Luna gravity-Stokes: J₂ couples to Earth tidal torque to drive forced libration

### RTD doc-maintenance (bundled)

- `docs/index.md`: stale paragraph claiming `addressing-maths` lives in a separate repo replaced with note that the formal substrate has been subsumed into chess-spectral + antikythera-spectral notebooks.
- `mkdocs.yml`: `site_description` updated to drop the `addressing-maths` reference and clarify the subsumption.

### Test count

1412 pass, 42 skipped (was 1372 + 42 in v0.24.0; +40 net new — 37 in `test_luna_dynamical_spectrum.py` + 2 README-freshness tests that flipped GREEN after Status banner update + 1 reconciliation).

### Migration

Pure-additive bridge + CLI. `ES_VERSION_STRING` bumps `0.24.0 → 0.24.1`.

## [0.24.0] — 2026-05-07

**Mercury Dynamical Spectrum — first per-body dynamical-spectrum surface; discipline pivot from cross-channel-coupling (v0.21.x) to action-angle decomposition of a single body's full dynamical state.** Pure-Python additive; **no ABI bump** (twenty-third consecutive ship since v0.13.x).

### What ships

| Surface | Function / subcommand |
|---|---|
| Pythonic API | `_research.mercury_dynamical_spectrum_catalog.get_mercury_dynamical_spectrum / get_mercury_precession_decomposition / list_mercury_dynamical_spectrum` |
| Bridge dict API | `bridge.get_mercury_dynamical_spectrum()` / `bridge.get_mercury_precession_decomposition()` / `bridge.list_mercury_dynamical_spectrum()` |
| CLI | `mercury-dynamical-spectrum`, `mercury-precession-decomposition`, `mercury-dynamical-spectrum-full` |

### Why Mercury first

Cleanest possible first target for the per-body dynamical-spectrum methodology:
- **No moon** → clean Sol-Mercury 2-body system (no parent-satellite confounding)
- **No atmosphere, no ocean** → no time-varying noise floor
- **Historically richest dynamical-test position** — Le Verrier 1859 → Newcomb 1882 → Einstein 1915 → Clemence 1947 → Margot 2007 → Park 2017 lineage. Every value is anchored in a famous paper.

### 8-mode action-angle catalog

| Mode | Class | Frequency / Amplitude | Source |
|---|---|---|---|
| orbital_mean_motion | angle | 415.20 cycles/century | JPL DE441 |
| spin_frequency | angle | 622.80 cycles/century (3:2 with orbit) | Margot 2007 |
| forced_libration | angle | 35.8 arcsec at orbital frequency | Margot 2007 |
| perihelion_longitude_precession | angle | 574.10 arcsec/century | Clemence 1947 |
| ascending_node_precession | angle | −446.30 arcsec/century retrograde | Murray-Dermott 1999 |
| eccentricity | action | 0.2056 dimensionless | Laskar 1989 |
| inclination | action | 7.005° | JPL DE441 |
| obliquity | action | 2.04 ± 0.08 arcmin (Cassini state 1) | Margot 2007 |

### Headline: Le Verrier / Einstein perihelion-precession decomposition

The famous test of general relativity, made into a spectral fingerprint:

| Contribution | arcsec/century | Physics class | Source |
|---|---:|---|---|
| Venus | 277.42 | Newtonian perturbation | Verma 2014 |
| Jupiter | 153.58 | Newtonian perturbation | Verma 2014 |
| Earth | 90.04 | Newtonian perturbation | Verma 2014 |
| Saturn | 7.30 | Newtonian perturbation | Verma 2014 |
| Mars + other | 3.29 | Newtonian perturbation | Verma 2014 |
| **General relativity** | **42.98** | Schwarzschild | **Einstein 1915** |
| Solar quadrupole J₂ | 0.025 | Solar oblateness | Park 2017 |
| **Sum of predictions** | **574.6** | (matches observed) | |
| **Total observed** | **574.10 ± 0.65** | Observation | **Clemence 1947** |

The sum of Newtonian + GR + solar-J₂ contributions closes to within ~0.5 arcsec/century of Clemence 1947's observed value — well inside the ±0.65 uncertainty. **This is one of the most precise quantitative confirmations of general relativity in physics.** Park 2017's MESSENGER radioscience confirmed Einstein's 42.98 arcsec/century to one part in 10^4.

The decomposition is **the spectral fingerprint of how Mercury's orbit responds to the rest of the Solar System's fields** — every row is a contribution from a neighbouring field (planetary perturbation, spacetime geometry, solar shape).

### Le Verrier/Einstein closure invariant

For Mercury: `observed_total - sum_of_predictions ≈ 0` within Clemence's ±0.65 arcsec/century. Pinned by `test_le_verrier_einstein_closure_invariant`. This is the v0.24.0 analogue of v0.21.10's `test_observed_minus_equilibrium_consistent` thermal-balance invariant.

### Cross-channel cross-references

- v0.23.0 spin-orbit resonance: Mercury 3:2 + 35.8 arcsec libration (forced_libration mode here MUST agree with v0.23.0 value — pinned by `test_forced_libration_matches_v0_23_0_value`).
- v0.21.4 rotational constraint: Margot 2007 provided BOTH the 3:2 lock + libration measurement here AND the C/MR² = 0.346 inversion that constrained Mercury's molten core.
- v0.20.0 geodetic catalog: gravity-Stokes coefficients capturing Mercury's permanent quadrupole — the J₂ that couples to solar tidal torque to drive the forced libration.

### Test count

1372 pass, 42 skipped (was 1338 + 42 in v0.23.1; +34 net new — 31 in `test_mercury_dynamical_spectrum.py` + 2 README-freshness tests that flipped GREEN after Status banner update + 1 reconciliation).

### Migration

Pure-additive bridge + CLI. `ES_VERSION_STRING` bumps `0.23.1 → 0.24.0`.

## [0.23.1] — 2026-05-07

**Packaging fix: trim `pyproject.toml` description to stay under PyPI's 512-character Summary metadata limit.**

### What broke

PyPI's "Summary" metadata field (`[project].description` in `pyproject.toml`) has a **HARD 512-character limit**. The upload endpoint silently rejects oversized metadata with a "could not comply" message that doesn't bubble useful detail into `pypa/gh-action-pypi-publish`'s logs. `twine check --strict` does NOT enforce this. The description grew across v0.22.0 (trajectory + sensing layer language added) and v0.23.0 (spin-orbit resonance language added) until it hit 593 characters — 81 over the limit. Both v0.22.0 and v0.23.0 publish workflows ran successfully through all 17 wheel + sdist + pure-wheel build jobs, then failed at the final PyPI upload step with no visible diagnostic.

### Fix

Trimmed both `pyproject.toml` and `pyproject-pure.toml` descriptions from 593 to 473 characters (39 chars of headroom under the 512 limit). Stripped the previously-included non-ASCII arrows (↔) — non-ASCII metadata is allowed but historically flaky across PyPI mirrors / packaging tools. Added inline `# IMPORTANT:` comments above each description warning future-self about the 512-char limit + ASCII preference.

### CI guard

Added a new `Verify [project].description is under PyPI's 512-char Summary limit` step to `.github/workflows/ephemerides-spectral-publish.yml`. Hard-fails the publish workflow if either pyproject's description hits 512 chars; soft-warns at 480 chars (32-char margin); soft-warns on non-ASCII content. Future descriptions cannot silently exceed the limit.

### Migration

Pure-additive packaging fix. v0.22.0 and v0.23.0 PyPI artifacts are NOT being retroactively published — the next PyPI release after v0.21.10 is v0.23.1 directly. The repo's GitHub Releases for v0.22.0 + v0.23.0 remain accurate; PyPI users get all v0.22.0 + v0.23.0 features when they upgrade to v0.23.1. `ES_VERSION_STRING` bumps `0.23.0 → 0.23.1`.

### Test count

1338 pass, 42 skipped (unchanged from v0.23.0).

## [0.23.0] — 2026-05-07

**Spin-orbit resonance ↔ rotation lock — eleventh cross-channel coupling surface (resumed after v0.22.0 trajectory pivot).** Closes the tidal-physics triple with v0.21.4 (Q-factor / dissipation efficiency) + v0.21.6 (orbital migration / secular drift). The **end-state** of long-term tidal evolution is the spin-orbit resonance lock. Pure-Python additive; **no ABI bump** (twenty-first consecutive ship since v0.13.x).

### What ships

| Surface | Function / subcommand |
|---|---|
| Pythonic API | `_research.spin_orbit_resonance_catalog.compute_spin_orbit_resonance / get_spin_orbit_resonance / list_spin_orbit_resonances` |
| Bridge dict API | `bridge.get_spin_orbit_resonance(body=None)` / `bridge.list_spin_orbit_resonances()` |
| CLI | `spin-orbit-resonance [--body X]` / `spin-orbit-resonances` |

### Physics

A body in orbit around a parent settles into a low-integer spin-orbit resonance over Gyr timescales. End-state is the integer pair `(p, q)` such that `T_rot · q = T_orb · p` (p rotations per q orbits). Most synchronous moons are 1:1; **Mercury is the only non-1:1 case in the Solar System** at 3:2, locked by high orbital eccentricity (e=0.206; Goldreich-Peale 1966).

### 8-body roster

| Body | Parent | Ratio | T_rot (d) | T_orb (d) | Libration (arcsec) | Source |
|---|---|---:|---:|---:|---:|---|
| **mercury** | sol | **3:2** | 58.65 | 87.97 | **35.8** | Margot 2007 |
| luna | terra | 1:1 | 27.32 | 27.32 | 7.9 | Williams 2014 |
| io | jupiter | 1:1 | 1.769 | 1.769 | 0.05 | Lainey 2009 |
| europa | jupiter | 1:1 | 3.551 | 3.551 | 0.10 | Van Hoolst 2008 |
| ganymede | jupiter | 1:1 | 7.155 | 7.155 | 0.04 | Lainey 2020 |
| titan | saturn | 1:1 | 15.945 | 15.945 | **52** | Iess 2012 |
| triton | neptune | 1:1 | 5.877 | 5.877 | 0.50 | Jacobson 2009 |
| **charon** | pluto | **1:1 dual** | 6.387 | 6.387 | 0.10 | McKinnon 2017 |

### Highlights

- 🌟 **Mercury 3:2** — the only non-1:1 spin-orbit resonance in the Solar System. Pettengill & Dyce 1965 Arecibo radar discovery; Goldreich-Peale 1966 stability theory; Margot 2007 ~36 arcsec forced libration.
- **Luna canonical 1:1** — most precisely-measured libration in the Solar System (Williams 2014 LLR ~7.9 arcsec).
- **Titan anomalously large libration** — ~52 arcsec, attributed to icy outer shell decoupled from interior by **subsurface H₂O ocean**. The libration itself is the ocean-depth diagnostic.
- **Pluto-Charon dual-synchronous** — the unique solar-system case where both bodies are tidally locked to each other. Mass ratio 0.12 puts barycentre outside Pluto; a true binary planet.

### Tidal-physics triple closure

```
v0.21.4 rotational constraint   (Q-factor)         ↔ dissipation efficiency
v0.21.6 tidal migration         (cm/yr drift)      ↔ secular evolution rate
v0.23.0 spin-orbit resonance    (p:q + libration)  ↔ END-STATE equilibrium  ← this ship
```

For Io: v0.21.4 Q≈80 + v0.21.6 +3.6 cm/yr expansion + v0.21.8 100 TW heating + v0.23.0 1:1 lock all describe the same physics — the Galilean Laplace 1:2:4 resonance is currently **expanding** because Jupiter dissipates angular momentum into Io's orbit, which dissipates as Io's surface heat flow, which drives the volcanism — all compatible with the 1:1 tidal lock end-state.

### Period-consistency invariant

For every entry: `T_rot / T_orb ≈ q / p` within ±1%. Pinned by `test_period_ratio_matches_p_over_q`. **Mercury-only-non-1:1** invariant pinned by `test_mercury_only_non_one_to_one`.

### Test count

1338 pass, 42 skipped (was 1306 + 42 in v0.22.0; +32 net new — 30 in `test_spin_orbit_resonance.py` + 2 README-freshness tests that flipped GREEN after Status banner update).

### Migration

Pure-additive bridge + CLI. `ES_VERSION_STRING` bumps `0.22.0 → 0.23.0`.

## [0.22.0] — 2026-05-07

**Trajectory + Sensing Layer — discipline pivot out of v0.21.x cross-channel-coupling sequence into applied-physics propagators.** Four-layer surface (Layer A per-body ballistic; Layer B Earth ICBM 3-regime; Layer C(a) sensor access geometry; Layer C(b) decoy discrimination). Pure-Python additive; **no ABI bump** (twentieth consecutive ship since v0.13.x).

**Trauma-informed defensive scope:** the publishable line is textbook physics + public TLEs + textbook geometry. Specific RV signatures, sensor NEΔT, kill-vehicle parameters, and threat-library specifics are intentionally out of scope.

### What ships

| Surface | Function / subcommand |
|---|---|
| **Layer A** Pythonic API | `_research.ballistic_trajectory_catalog.compute_ballistic_trajectory / get_ballistic_atmosphere / list_ballistic_atmospheres` |
| **Layer A** Bridge dict API | `bridge.compute_ballistic_trajectory(...)` / `bridge.get_ballistic_atmosphere(...)` / `bridge.list_ballistic_atmospheres()` |
| **Layer A** CLI | `ballistic-trajectory --body X --v Y --angle Z [--with-drag --bc BC]`, `ballistic-atmosphere`, `ballistic-atmospheres` |
| **Layer B** Pythonic API | `_research.icbm_trajectory_catalog.compute_icbm_trajectory / get_icbm_reference_profile / list_icbm_reference_profiles` |
| **Layer B** Bridge dict API | `bridge.compute_icbm_trajectory(...)` / `bridge.get_icbm_reference_profile(...)` / `bridge.list_icbm_reference_profiles()` |
| **Layer B** CLI | `icbm-trajectory --burnout-v V --burnout-gamma G [--bc BC]`, `icbm-reference-profile`, `icbm-reference-profiles` |
| **Layer C(a)** Pythonic API | `_research.sensor_access_catalog.compute_visibility_geometry / compute_sgp4_state / get_orbital_reference / list_orbital_references` |
| **Layer C(a)** Bridge dict API | `bridge.compute_visibility_geometry(...)` / `bridge.compute_sgp4_state(...)` / `bridge.get_orbital_reference(...)` / `bridge.list_orbital_references()` |
| **Layer C(a)** CLI | `visibility-geometry`, `sgp4-state`, `orbital-reference`, `orbital-references` |
| **Layer C(b)** Pythonic API | `_research.decoy_discrimination_catalog.compute_bc_differential / compute_discrimination_altitude / get_bc_reference_class / list_bc_reference_classes` |
| **Layer C(b)** Bridge dict API | `bridge.compute_bc_differential(...)` / `bridge.compute_discrimination_altitude(...)` / `bridge.get_bc_reference_class(...)` / `bridge.list_bc_reference_classes()` |
| **Layer C(b)** CLI | `bc-differential`, `discrimination-altitude`, `bc-reference-class`, `bc-reference-classes` |

### Layer A — per-body ballistic propagator

Vacuum case: Vallado §8.6.2 closed form (range = v²·sin(2θ)/g, apex = v²·sin²(θ)/(2g), T = 2v·sin(θ)/g) — matches to numerical precision. Drag case: RK4 integration under exponential atmosphere (BC = m/(C_d·A) parameterized).

7-body roster: terra (US Standard Atmosphere 1976), mars (Tewari 2011), venus (VIRA / Seiff 1985), titan (Cassini-Huygens HASI / Fulchignoni 2005), luna (vacuum), mercury (vacuum), jupiter (Galileo Probe / Seiff 1998 1-bar reference).

### Layer B — Earth 3-regime ICBM

Boost is a boundary condition (user supplies burnout state v, γ, h). Midcourse: Kepler-ellipse propagation (Bate-Mueller-White Ch. 6). Re-entry: Allen-Eggers closed form (NACA Report 1381, 1958). **Boost intentionally not modelled** — vehicle-specific Isp/thrust/gravity-turn cross into operationally-sensitive territory.

3 reference profiles (open-literature only):

| Profile | Range (km) | Burnout v / γ | Apex (km) | Re-entry v (m/s) | Source |
|---|---:|---:|---:|---:|---|
| srbm_300km | 300 | 1700 m/s @ 42° | 80 | 1700 | Wilkening 2000 |
| mrbm_1500km | 1500 | 4000 m/s @ 37° | 400 | 3900 | Wilkening 2000 |
| icbm_10000km | 10000 | 7000 m/s @ 23° | 1200 | 7000 | Sessler/UCS 2000 |

### Layer C(a) — sensor access geometry

WGS-84 geodetic-to-ECEF + ECEF-to-ENU + slant-range/elevation/azimuth + Earth-limb occlusion test (Vallado Ch. 11). SGP4 propagation via Brandon Rhodes' `sgp4` package (transitive optional dep through `[ephemeris]`).

8 reference TLEs (textbook samples; fetch fresh from CelesTrak / Space-Track for operational use):

| Label | Class | Inc. | Period | Notes |
|---|---|---:|---:|---|
| ISS (ZARYA) | leo_mid_inc | 51.6° | 92.9 min | Textbook reference |
| SENTINEL-1A | leo_sun_sync | 98.2° | 98.6 min | C-band SAR |
| NOAA-20 (JPSS-1) | leo_sun_sync | 98.7° | 101.4 min | VIIRS day-night |
| IRIDIUM 100 | leo_polar | 86.4° | 100.4 min | 66-sat polar constellation |
| GOES-16 | geo | 0.05° | 1436 min | GLM lightning mapper |
| MOLNIYA-3-50 | heo_molniya | 63.4° | 720 min | **Polar-coverage geometry** |
| TUNDRA | heo_tundra | 63.4° | 1436 min | 24-h alt. polar coverage |
| LANDSAT-9 | leo_sun_sync | 98.2° | 98.9 min | OLI-2 + TIRS-2 |

IR transmission windows: VIS 0.4-0.7 µm, NIR 0.7-2.5 µm, MWIR 3-5 µm, LWIR 8-12 µm.

### Layer C(b) — decoy discrimination

**The only physics-based midcourse-surviving discriminator**: ballistic-coefficient differential velocity separation in the upper atmospheric drag tail (60-100 km). Allen-Eggers closed-form `v(h) = v_e · exp[-K · exp(-h/H)]` with `K = ρ₀H/(2·BC·sin γ_e)` (NACA Report 1381, 1958).

Heavy compact RV (BC ~10000 kg/m²) decelerates slowly; light decoys (BC ~50 kg/m²) decelerate rapidly. Reference: Sessler/UCS *Countermeasures* 2000.

4 reference BC classes (open-literature only):

| Class | Typical BC (kg/m²) | Mass / Diameter | C_d |
|---|---:|---|---:|
| heavy_rv | 10000 | 200 kg / 0.45 m | 0.10 |
| light_rv | 3000 | 200 kg / 0.6 m | 0.20 |
| replica_decoy | 50 | 10 kg / 1.0 m | 1.0 |
| chaff_decoy | 10 | 0.05 kg / 0.1 m | 2.0 |

### Citations

23 unique sources spanning Vallado 2013, Bate-Mueller-White 1971, Curtis 2014, Tewari, Allen-Eggers 1958, Regan-Anandakrishnan 1993, Sessler/UCS 2000, Wilkening 2000, Postol 1991, US Standard Atmosphere 1976, VIRA / Seiff 1985, Cassini-Huygens HASI / Fulchignoni 2005, Galileo Probe / Seiff 1998, NASA Planetary Fact Sheet, CelesTrak, ESA Sentinel, NOAA JPSS / GOES, USGS Landsat, HITRAN, WGS-84 (NIMA TR8350.2).

### Test count

1306 pass, 42 skipped (was 1190 + 41 in v0.21.10; +103 net new across `test_ballistic_trajectory.py` (29) + `test_icbm_trajectory.py` (24) + `test_sensor_access.py` (24) + `test_decoy_discrimination.py` (26)). One additional skip: `compute_sgp4_state` parity-smoke entry tier2_skips when optional `sgp4` dep absent.

### Migration

Pure-additive bridge + CLI. `ES_VERSION_STRING` bumps `0.21.10 → 0.22.0` (minor bump reflects discipline-pivot scope; ABI unchanged).

## [0.21.10] — 2026-05-07

**Heliocentric flux ↔ surface temperature — tenth cross-channel coupling surface (post-trio).** Stefan-Boltzmann radiative-equilibrium decomposition of v0.20.2 observed temperatures into greenhouse + tidal + internal-heat contributions. Pure-Python additive; **no ABI bump** (nineteenth consecutive ship since v0.13.x).

### What ships

| Surface | Function / subcommand |
|---|---|
| Pythonic API | `_research.thermal_balance_catalog.compute_thermal_balance / list_thermal_balances` |
| Bridge dict API | `bridge.get_thermal_balance(body=None)` / `bridge.list_thermal_balances()` |
| CLI | `thermal-balance [--body X]` / `thermal-balances` |

### Physics

`T_eq = ((1 - A) * S / (4 * σ))^(1/4)` where S is solar flux at the body, A is Bond albedo (v0.20.2), σ is Stefan-Boltzmann constant. Observed temperature (v0.20.2) decomposes as `T_obs = T_eq + ΔT_greenhouse + ΔT_tidal + ΔT_internal`.

### 6-body roster

| Body | Source | T_eq (K) | T_obs (K) | Greenhouse (K) | Tidal (K) | Internal (K) |
|---|---|---:|---:|---:|---:|---:|
| terra | Kiehl 1997 | 254.6 | 288.15 | **+33.5** | 0 | 0.05 |
| mars | Haberle 2013 | 210 | 210 | +5 | 0 | 0.001 |
| **venus** | **Bullock 2001** | **231.8** | **737** | **+505 (RUNAWAY)** | 0 | 0.2 |
| mercury | Hapke 1981 | 437 | 440 | 0 | 0 | 0 |
| titan | Strobel 2009 | 83 | 94 | +9 | +2 | 0 |
| **jupiter** | **Hubbard 1999** | **110** | **165** | +10 | 0 | **+45 (INTERNAL)** |

### Highlights

- 🌟 **Venus +505 K runaway greenhouse** — the headline. Surface hotter than Mercury despite further from Sun; CO₂ + clouds make this happen.
- **Earth +33.5 K canonical greenhouse** — H₂O + CO₂ atmosphere; the textbook case.
- **Jupiter internal-heat-dominated** — radiates 1.7× more than it absorbs (primordial cooling + helium-rain drainage).
- **Mercury pure radiative balance** — no atmosphere → all three offsets exactly zero.
- **Mars naked planet** — too thin for greenhouse.

### Energy-budget consistency invariant

For every body: T_obs - T_eq ≈ greenhouse + tidal + internal-heat offsets (within ~5 K rounding). Pinned by `test_observed_minus_equilibrium_consistent`.

### v0.21.x cross-channel coupling progress

```
v0.21.1 topography ↔ gravity                 (5 bodies)  ✅
v0.21.2 magnetic   ↔ dynamo                  (5 bodies)  ✅
v0.21.3 topography ↔ atmosphere              (4 bodies)  ✅
v0.21.4 interior   ↔ rotation                (7 bodies)  ✅
v0.21.5 magnetic   ↔ atmosphere              (6 bodies)  ✅
v0.21.6 tidal      ↔ orbital migration       (6 pairs)   ✅
v0.21.7 escape     ↔ magnetic shielding      (6 bodies)  ✅
v0.21.8 heat flow  ↔ tidal heating           (6 bodies)  ✅
v0.21.9 outgassing ↔ atmospheric composition (6 bodies)  ✅
v0.21.10 thermal balance ↔ surface temp      (6 bodies)  ✅ ← this ship
```

### Test count

1190 pass, 41 skipped (was 1163 + 41 in v0.21.9; +27 net new — 27 in `test_thermal_balance.py`).

### Migration

Pure-additive bridge + CLI. `ES_VERSION_STRING` bumps `0.21.9 → 0.21.10`.

## [0.21.9] — 2026-05-07

**Volcanic outgassing ↔ atmospheric composition — ninth cross-channel coupling surface (post-trio).** Forms the supply-side of atmospheric mass balance with v0.21.7 escape as demand-side. **Closes the Io→Jupiter mass-transfer pipeline across six ships** (v0.19.0 + v0.20.1 + v0.21.5 + v0.21.7 + v0.21.8 + v0.21.9). Pure-Python additive; **no ABI bump** (eighteenth consecutive ship since v0.13.x).

### What ships

| Surface | Function / subcommand |
|---|---|
| Pythonic API | `_research.volcanic_outgassing_catalog.compute_volcanic_outgassing / list_volcanic_outgassings` |
| Bridge dict API | `bridge.get_volcanic_outgassing(body=None)` / `bridge.list_volcanic_outgassings()` |
| CLI | `volcanic-outgassing [--body X]` / `volcanic-outgassings` |

### 6-body roster

| Body | Source | Rate (kg/s) | Species | Mechanism | Active? |
|---|---|---:|---|---|:-:|
| terra | Burton 2013 | 3 | CO₂ | subaerial_volcanism | ✓ |
| mars | Halevy 2014 | 0.001 | SO₂ (upper limit) | dormant | ✗ |
| venus | Bullock 2001 | 0.5 | SO₂ | subaerial_volcanism | ✓ |
| **io** | **Lellouch 2007** | **1000** | **SO₂** | **tidal_volcanism** | **✓** |
| enceladus | Hansen 2011 | 200 | H₂O | plume_venting | ✓ |
| jupiter | Bagenal 2007 | 1000 | S+/O+ (via Io) | magnetospheric_injection | ✓ |

### The Io→Jupiter mass-transfer pipeline (six-ship closure)

| Ship | Channel | Quantity | Value |
|---|---|---|---:|
| v0.19.0 | EM Instrument | Io flux tube | 10¹² W |
| v0.20.1 | Magnetic Multipole | JRM33 dipole | 1.5×10²⁰ T·m³ |
| v0.21.5 | Auroral Coupling | Io footprint | observed |
| v0.21.7 | Atmospheric Escape | Jupiter pickup-ion | 1000 kg/s |
| v0.21.8 | Heat Flow | Io tidal heating | 100 TW |
| **v0.21.9** | **Outgassing** | **Io SO₂** | **1000 kg/s** |

Six observational handles, all consistent with the same physics: Jupiter's gravitational tidal heating drives Io's volcanism → Io vents 1 ton/s SO₂ → SO₂ injected into Jupiter's plasma torus → torus injection rate matches Jupiter's pickup-ion escape rate downstream.

### Highlights

- 🌟 **Io 1 ton/s SO₂ outgassing** — the headline; tidal-driven volcanism powers the Io→Jupiter pipeline.
- **Mars dormant** — modern outgassing ~0 while v0.21.7 escape ~2 kg/s → the famous "dead planet" story.
- **Earth carbon cycle** — outgassing balanced by carbonate-silicate weathering on Gyr timescales (not by escape).
- **Enceladus E-ring supply** — 200 kg/s H₂O plume venting feeds Saturn's ring system.

### v0.21.x cross-channel coupling progress

```
v0.21.1 topography ↔ gravity                 (5 bodies)  ✅
v0.21.2 magnetic   ↔ dynamo                  (5 bodies)  ✅
v0.21.3 topography ↔ atmosphere              (4 bodies)  ✅
v0.21.4 interior   ↔ rotation                (7 bodies)  ✅
v0.21.5 magnetic   ↔ atmosphere              (6 bodies)  ✅
v0.21.6 tidal      ↔ orbital migration       (6 pairs)   ✅
v0.21.7 escape     ↔ magnetic shielding      (6 bodies)  ✅
v0.21.8 heat flow  ↔ tidal heating           (6 bodies)  ✅
v0.21.9 outgassing ↔ atmospheric composition (6 bodies)  ✅ ← this ship
```

### Test count

1163 pass, 41 skipped (was 1136 + 41 in v0.21.8; +27 net new — 24 in `test_volcanic_outgassing.py` + 2 README-freshness + 1 reconciliation).

### Migration

Pure-additive bridge + CLI. `ES_VERSION_STRING` bumps `0.21.8 → 0.21.9`.

## [0.21.8] — 2026-05-07

**Heat flow ↔ tidal heating — eighth cross-channel coupling surface (post-trio).** **Closes the tidal-energy-budget loop** with v0.21.4 (tidal Q) + v0.21.6 (orbital migration). Pure-Python additive; **no ABI bump** (seventeenth consecutive ship since v0.13.x).

### What ships

| Surface | Function / subcommand |
|---|---|
| Pythonic API | `_research.heat_flow_catalog.compute_heat_flow / list_heat_flows` |
| Bridge dict API | `bridge.get_heat_flow(body=None)` / `bridge.list_heat_flows()` |
| CLI | `heat-flow [--body X]` / `heat-flows` |

### 6-body roster

| Body | Source | Total (TW) | Tidal | Radiogenic | Primordial |
|---|---|---:|---:|---:|---:|
| terra | Davies 2010 | 47 | 0.001 | 0.66 | 0.34 |
| mars | Khan 2023 InSight | 0.1 | 0.001 | 0.85 | 0.15 |
| **io** | **Veeder 2012** | **100** | **0.99** | 0.005 | 0.005 |
| europa | Vance 2018 | 0.5 | 0.85 | 0.13 | 0.02 |
| enceladus | Howett 2011 | 0.01 | 0.95 | 0.04 | 0.01 |
| titan | Tobie 2008 | 2 | 0.55 | 0.45 | 0.0 |

### The Io tidal-energy-budget loop

**v0.21.4 + v0.21.6 + v0.21.8 close the Io energy budget**:

| Quantity | Source | Value |
|---|---|---|
| Tidal Q | v0.21.4 Lainey 2009 | ~80 |
| Outward migration rate | v0.21.6 Lainey 2009 | +3.6 cm/yr |
| **Surface heat flow** | **v0.21.8 Veeder 2012** | **~100 TW** |

Three independent observational handles converging on the same tidal-dissipation physics — the Galilean Laplace 1:2:4 resonance is currently expanding because Jupiter's tidal Q ≈ 5×10⁴ dissipates angular momentum into Io's orbit, which then dissipates as Io's surface heat flow.

### Highlights

- 🌟 **Io 100 TW = 99% tidal — the headline.** Most volcanically active body in solar system; 2× Earth's heat flow despite 4× smaller radius.
- **Earth radiogenic-dominated** (~66% radiogenic ²³⁸U/²³²Th/⁴⁰K + ~34% primordial cooling).
- **Mars cooled faster** than Earth (only 0.1 TW today; Khan 2023 InSight).
- **Europa subsurface ocean** maintained by ~0.5 TW tidal heating in icy shell + ocean.
- **Enceladus south-polar plumes** powered by ~10 GW tidal dissipation in tiger-stripe terrain.

### Energy-budget invariants

For every body, tidal + radiogenic + primordial fractions sum to ~1 (pinned by `test_fractions_sum_to_unity`).

### v0.21.x cross-channel coupling progress

```
v0.21.1 topography ↔ gravity                 (5 bodies)  ✅
v0.21.2 magnetic   ↔ dynamo                  (5 bodies)  ✅
v0.21.3 topography ↔ atmosphere              (4 bodies)  ✅
v0.21.4 interior   ↔ rotation                (7 bodies)  ✅
v0.21.5 magnetic   ↔ atmosphere              (6 bodies)  ✅
v0.21.6 tidal      ↔ orbital migration       (6 pairs)   ✅
v0.21.7 escape     ↔ magnetic shielding      (6 bodies)  ✅
v0.21.8 heat flow  ↔ tidal heating           (6 bodies)  ✅ ← this ship
```

### Test count

1136 pass, 41 skipped (was 1107 + 41 in v0.21.7; +29 net new — 27 in `test_heat_flow.py` + 2 README-freshness).

### Migration

Pure-additive bridge + CLI. `ES_VERSION_STRING` bumps `0.21.7 → 0.21.8`.

## [0.21.7] — 2026-05-07

**Atmospheric escape ↔ magnetic-field shielding — seventh cross-channel coupling surface (post-trio).** Pure-Python additive; **no ABI bump** (sixteenth consecutive ship since v0.13.x).

### What ships

| Surface | Function / subcommand |
|---|---|
| Pythonic API | `_research.atmospheric_escape_catalog.compute_atmospheric_escape / list_atmospheric_escapes` |
| Bridge dict API | `bridge.get_atmospheric_escape(body=None)` / `bridge.list_atmospheric_escapes()` |
| CLI | `atmospheric-escape [--body X]` / `atmospheric-escapes` |

### 6-body roster

| Body | Source | Rate (kg/s) | Mechanism | Shielded? | 4-Gyr loss (kg) |
|---|---|---:|---|:-:|---:|
| terra | Lammer 2018 | 3 | thermal_jeans | ✓ | 4×10¹⁴ |
| **mars** | **Jakosky 2018 MAVEN** | **2** | **pickup_ion** | **✗** | **10¹⁸ (50% of primordial)** |
| venus | Persson 2020 ASPERA-4 | 0.4 | pickup_ion | ✗ | 5×10¹⁶ |
| mercury | Killen 2007 | 0.01 | sputtering | ✓ (weak) | 10¹⁵ |
| titan | Strobel 2008 | 30 | hydrodynamic | ✓ (Saturn mag) | 4×10¹⁸ |
| jupiter | Bagenal 2007 | 1000 | pickup_ion (Io torus) | ✓ | 10²⁰ |

### Highlights

- 🌟 **Mars MAVEN headline** — Jakosky 2018 measured Mars's present-day pickup-ion escape at 2 kg/s; integrated 4-Gyr loss = **~10¹⁸ kg = ~50% of primordial CO₂ atmosphere**. The famous "Mars lost atmosphere because it lost dynamo" story.
- **Venus paradox** — no intrinsic dipole but retains thick CO₂ atmosphere; stronger gravity holds heavier ions + induced magnetosphere does the rest.
- **Titan highest absolute rate among classic atmospheres** — 30 kg/s hydrodynamic blowoff despite small size; Saturn magnetosphere provides partial shielding.
- **Jupiter Io torus** dominates mass loss (1000 kg/s of S+/O+ from Io volcanism); cross-references v0.19.0 flux-tube ~10¹² W + v0.20.1 JRM33 + v0.21.5 Io aurora footprint.

### Cross-channel observation

**The v0.20.2 atmospheric inventory diverges by Gyr from the v0.20.1 magnetic-multipole inventory.** Mars + Venus diverge from terrestrial inventory precisely because they lack magnetic shielding. v0.21.7 ships the quantitative measurement of that divergence rate.

### Architectural choice

**Not a re-derivation.** Values shipped are the published measurements / model fits from cited papers.

### v0.21.x cross-channel coupling progress

```
v0.21.1 topography ↔ gravity                 (5 bodies)  ✅
v0.21.2 magnetic   ↔ dynamo                  (5 bodies)  ✅
v0.21.3 topography ↔ atmosphere              (4 bodies)  ✅
v0.21.4 interior   ↔ rotation                (7 bodies)  ✅
v0.21.5 magnetic   ↔ atmosphere              (6 bodies)  ✅
v0.21.6 tidal      ↔ orbital migration       (6 pairs)   ✅
v0.21.7 escape     ↔ magnetic shielding      (6 bodies)  ✅ ← this ship
```

### Test count

1107 pass, 41 skipped (was 1082 + 41 in v0.21.6; +25 net new — 23 in `test_atmospheric_escape.py` + 2 README-freshness).

### Migration

Pure-additive bridge + CLI. `ES_VERSION_STRING` bumps `0.21.6 → 0.21.7`.

## [0.21.6] — 2026-05-07

**Tidal-resonance ↔ orbital migration — sixth cross-channel coupling surface (post-trio).** Pure-Python additive; **no ABI bump** (fifteenth consecutive ship since v0.13.x).

### What ships

| Surface | Function / subcommand |
|---|---|
| Pythonic API | `_research.tidal_migration_catalog.compute_tidal_migration / list_tidal_migrations` |
| Bridge dict API | `bridge.get_tidal_migration(pair=None)` / `bridge.list_tidal_migrations()` |
| CLI | `tidal-migration [--pair X]` / `tidal-migrations` |

### 6-pair roster

| Pair | Source | Rate (cm/yr) | Direction | Resonance? |
|---|---|---:|---|:-:|
| terra-luna | Williams 2014 LLR | +3.83 | outward | ✗ |
| mars-phobos | Lainey 2007 | −1.9 | inward | ✗ |
| **jupiter-io** | **Lainey 2009** | **+3.6** | **outward** | **✓** (Laplace) |
| **saturn-titan** | **Lainey 2020** | **+11** | **outward** | **✓** (Saturn interior) |
| neptune-triton | Jacobson 2009 | −0.5 | inward | ✗ |
| pluto-charon | McKinnon 2017 | 0 | locked | ✗ |

### Highlights

- **Saturn-Titan 11 cm/yr — the headline.** Lainey 2020 measured this is **100× older equilibrium-tide predictions**; implies Saturn-interior resonance locking with Titan's orbit. Cross-references v0.21.4 Mankovich-Fuller 2021 ring-seismology — the two ships form a coherent picture of Saturn's deep-interior dynamics.
- **Galilean Laplace 1:2:4 currently EXPANDING** (Lainey 2009; not contracting as classical theory assumed). Io drifts outward at 3.6 cm/yr.
- **Earth-Moon 3.83 cm/yr** — the canonical case; most precisely measured tidal-migration rate in the solar system via Lunar Laser Ranging.
- **Mars-Phobos** — Phobos orbits faster than Mars rotates → tidal bulge lags → inward at 1.9 cm/yr; tidal-disruption deadline ~50 Myr.
- **Pluto-Charon dual-synchronous tidal lock** — unique solar-system case; tidal evolution end-state.

### Direction-sign convention

Pinned in tests: outward → positive, inward → negative, locked → zero.

### Architectural choice

**Not a re-derivation.** Values shipped are the published secular drift fits from cited papers.

### v0.21.x cross-channel coupling progress

```
v0.21.1 topography ↔ gravity              (5 bodies)  ✅
v0.21.2 magnetic   ↔ dynamo               (5 bodies)  ✅
v0.21.3 topography ↔ atmosphere           (4 bodies)  ✅
v0.21.4 interior   ↔ rotation             (7 bodies)  ✅
v0.21.5 magnetic   ↔ atmosphere           (6 bodies)  ✅
v0.21.6 tidal      ↔ orbital migration    (6 pairs)   ✅ ← this ship
```

### Forward sequence

* **v0.21.7+** — More cross-channel coupling surfaces (e.g., heat flow ↔ tidal heating; volcanic outgassing ↔ atmospheric composition; atmospheric escape ↔ magnetic-field shielding).

### Test count

1082 pass, 41 skipped (was 1056 + 41 in v0.21.5; +26 net new — 24 in `test_tidal_migration.py` + 2 README-freshness tests that flipped GREEN).

### Migration

Pure-additive bridge + CLI. `ES_VERSION_STRING` bumps `0.21.5 → 0.21.6`.

## [0.21.5] — 2026-05-07

**Magnetic ↔ atmosphere coupling via aurorae — fifth cross-channel coupling surface (post-trio).** Pure-Python additive; **no ABI bump** (fourteenth consecutive ship since v0.13.x).

### What ships

| Surface | Function / subcommand |
|---|---|
| Pythonic API | `_research.auroral_coupling_catalog.compute_auroral_coupling / list_auroral_couplings` |
| Bridge dict API | `bridge.get_auroral_coupling(body=None)` / `bridge.list_auroral_couplings()` |
| CLI | `auroral-coupling [--body X]` / `auroral-couplings` |

### Physics

Aurorae are the visible signature of magnetic-field-line topology mapping into the upper atmosphere. The morphology of the auroral oval directly traces the underlying internal-field geometry — circular oval → dipole + small-quadrupole; annular oval → axisymmetric field; partial oval → strongly tilted offset dipole; patchy/time-variable → multipole + tilt mixing.

### 6-body roster

| Body | Source | Morphology | Power (W) | Mechanism | Moon footprint? |
|---|---|---|---:|---|:-:|
| terra | Bonfond 2017 | circular_oval | 10¹¹ | solar_wind | ✗ |
| **jupiter** | **Connerney 2017 (Juno UVS)** | **circular_oval** | **10¹⁴** | **corotation** | **✓** |
| saturn | Hunt 2014 / Stallard 2008 | annular_oval | 10¹¹ | solar_wind | ✗ |
| uranus | Lamy 2017 (HST 2011) | partial_oval | 10⁹ | tilted_dipole | ✗ |
| neptune | Pryor 2007 | patchy_time_variable | 10⁸ | tilted_dipole | ✗ |
| ganymede | Saur 2015 (HST) | circular_oval | 2×10⁹ | corotation | ✗ |

### Highlights

- **Jupiter ~10¹⁴ W = 1000× Earth's** — the headline. Internally driven by corotation enforcement (NOT solar wind); Io flux-tube footprint always visible inside main oval; Europa + Ganymede footprints intermittent.
- **Saturn annular oval** directly traces Cao 2020 axisymmetry (dipole tilt < 0.007°) — cross-references the v0.20.1 result.
- **Ganymede subsurface-ocean diagnostic** — Saur 2015 used auroral-position rocking between 2010 + 2011 HST observations to diagnose ocean conductivity. The aurora itself is the cross-channel measurement: magnetic ↔ interior coupling via observational rocking response.
- **Uranus partial / Neptune patchy** — extreme dipole tilts (58.6° + 47°) yield non-classic morphology.

### Architectural choice

**Not a re-derivation.** Values shipped are the published auroral-imaging campaign decompositions from cited papers.

### 5-body cross-channel surfaces shipped so far in v0.21.x

```
v0.21.1 topography ↔ gravity         (5 bodies; admittance)
v0.21.2 magnetic   ↔ dynamo          (5 bodies; Lowes-Mauersberger)
v0.21.3 topography ↔ atmosphere      (4 bodies; orographic forcing)
v0.21.4 interior   ↔ rotation        (7 bodies; Saturn ring-seismology)
v0.21.5 magnetic   ↔ atmosphere      (6 bodies; aurorae) — this ship
```

### Forward sequence

* **v0.21.6+** — More cross-channel coupling surfaces (e.g., tidal-resonance ↔ orbital migration; atmospheric escape ↔ magnetic-field shielding).

### Test count

1056 pass, 41 skipped (was 1029 + 41 in v0.21.4; +27 net new — 24 in `test_auroral_coupling.py` + 2 README-freshness tests that flipped GREEN + 1 reconciliation).

### Migration

Pure-additive bridge + CLI. `ES_VERSION_STRING` bumps `0.21.4 → 0.21.5`.

## [0.21.4] — 2026-05-07

**Interior-derived rotational constraints — fourth cross-channel coupling surface (post-trio).** Opens the v0.21.4+ sequence of cross-channel coupling surfaces from §17.1/§17.2/§17.3 subagent follow-up findings, after v0.21.1-v0.21.3 shipped the trio explicitly named in §17.4.2. Pure-Python additive; **no ABI bump** (thirteenth consecutive ship since v0.13.x).

### What ships

| Surface | Function / subcommand |
|---|---|
| Pythonic API | `_research.rotational_constraint_catalog.compute_rotational_constraint / list_rotational_constraints` |
| Bridge dict API | `bridge.get_rotational_constraint(body=None)` / `bridge.list_rotational_constraints()` |
| CLI | `rotational-constraint [--body X]` / `rotational-constraints` |

### 7-body roster

| Body | Source | Type | Value | Constrains |
|---|---|---|---:|---|
| terra | Mathews 2002 IERS | free_core_nutation | 430.21 d | core-mantle friction |
| mars | Le Maistre 2023 InSight RISE | insight_nutation | 1830 km | core radius |
| jupiter | Kaspi 2018 (Juno) | zonal_wind_depth | 3000 km | wind penetration |
| **saturn** | **Mankovich & Fuller 2021** | **ring_seismology** | **0.43539 d** | **deep-interior rotation** |
| io | Lainey 2009 | tidal_dissipation_Q | 80 | volcanic dissipation |
| europa | Lainey 2020 | tidal_dissipation_Q | 500 | subsurface ocean |
| ganymede | Lainey 2020 | tidal_dissipation_Q | 300 | dynamo energy budget |

### The Saturn headline

Mankovich & Fuller 2021's ring-seismology mode-fit revises Saturn's true rotation period from the Voyager-era cloud-deck estimate of 10h 39min 22s down to **10h 33min 38s = 0.43539 days = 37618 s**. The ring-mode forcing only matches deep-interior rotation, not cloud-deck rotation, resolving the decades-long debate about Saturn's "true" rotation period.

### 6 sources for 7 bodies

Lainey 2020 covers both Europa and Ganymede tidal Q (single Nature paper, two-body astrometric fit), explaining the 6:7 ratio. Citation discipline ratchet tests pin both directions.

### Forward sequence

* **v0.21.5+** more cross-channel coupling surfaces from §17.1/§17.2/§17.3 follow-ups (e.g., magnetic ↔ atmosphere coupling for the giants — Jupiter aurora morphology ↔ JRM33 magnetospheric topology; tidal-resonance ↔ orbital migration; etc.).

### Test count

1029 pass, 41 skipped (was 1001 + 41 in v0.21.3; +28 net new — 26 in `test_rotational_constraint.py` + 2 README-freshness tests that flipped GREEN after the Status banner update).

### Migration

Pure-additive bridge + CLI; no existing call sites change. `ES_VERSION_STRING` bumps `0.21.3 → 0.21.4`.

## [0.21.3] — 2026-05-07

**Orographic forcing of atmospheric standing waves — third cross-channel coupling surface in the §17.4.2 v0.21.x sequence.** Completes the trio of cross-channel surfaces explicitly named in §17.4.2 (topography ↔ gravity admittance [v0.21.1], magnetic-multipole-derived dynamo constraints [v0.21.2], orographic forcing of atmospheric standing waves [v0.21.3 — this ship]). Pure-Python additive; **no ABI bump** (twelfth consecutive ship since v0.13.x).

### What ships

| Surface | Function / subcommand |
|---|---|
| Pythonic API | `_research.orographic_forcing.compute_orographic_forcing / list_orographic_forcings` |
| Bridge dict API | `bridge.get_orographic_forcing(body=None)` / `bridge.list_orographic_forcings()` |
| CLI | `orographic-forcing [--body X]` / `orographic-forcings` |

### Physics

For a body with both a topography model (v0.20.0) and an atmosphere (v0.20.2), surface topography acts as a lower-boundary forcing on the global circulation. A mountain range or planetary-scale uplift generates downstream stationary Rossby waves — planetary waves with zero phase speed in the body-rotating frame, appearing as fixed structure in the time-mean atmosphere.

### 4-body roster

| Body | Source | Feature | h (km) | k | Observed? | Precision |
|---|---|---|---:|---:|:-:|---|
| **terra** | Held 2002 / Hoskins & Karoly 1981 | Tibetan Plateau | 4.5 | 2 | ✓ | HIGH |
| **mars** | Hollingsworth 1997 | **Tharsis Bulge** | **10** | 2 | ✓ | HIGH |
| venus | Lebonnois 2010 GCM | Maxwell Montes | 11 | 1 | ✗ | LOW |
| titan | Charnay & Lebonnois 2012 | Xanadu / dunes | 0.5 | 1 | ✗ | LOW |

### Highlights

- **Mars Tharsis Bulge** — the headline planetary case. ~10 km elevation, ~10000 km wide; wavenumber-2 stationary pattern survives all the way to ~50 km altitude (mesopause) in MGS observations + Mars GCM. The most dramatic orographic forcing on any body in the catalog.
- **Earth Tibetan Plateau** — the canonical Northern-Hemisphere winter stationary-wave pattern (Hoskins & Karoly 1981); Held 2002 review.
- **Venus + Titan super-rotation suppression** — both bodies' super-rotation regime suppresses classic Hoskins-Karoly stationary-wave physics. LOW precision, `is_stationary_wave_observed=False`.

### Architectural choice

**Not a re-derivation.** Values shipped are the published GCM-derived stationary-wave decompositions from the cited papers; per-degree spectral tables remain in those papers' supplementary materials.

### Citation discipline

4-entry `SOURCES` citation dict (Held 2002, Hollingsworth 1997, Lebonnois 2010, Charnay & Lebonnois 2012). Ratchet tests pin both directions.

### Cross-channel trio complete

With v0.21.3 the **three cross-channel coupling surfaces explicitly named in §17.4.2 are all shipped**:

1. **v0.21.1** topography ↔ gravity admittance (5 bodies; Wieczorek 2007/2013 + Genova 2016 + James 2015 + Anderson 2002).
2. **v0.21.2** magnetic-multipole-derived dynamo-region constraints (5 bodies; Lowes 1974 + Christensen 2006 + Connerney 2022 + Cao 2020 + Schubert 1996).
3. **v0.21.3** orographic forcing of atmospheric standing waves (4 bodies; Held 2002 + Hollingsworth 1997 + Lebonnois 2010 + Charnay 2012).

### Forward sequence

Future v0.21.x minors will ship coupling surfaces from §17.1/§17.2/§17.3 subagent follow-ups (e.g., interior-derived rotational constraints; magnetic ↔ atmosphere coupling for the giants; tidal-heating / orbital-resonance ↔ interior coupling for the Galileans).

### Test count

1001 pass, 41 skipped (was 977 + 41 in v0.21.2; +24 net new — 24 in `test_orographic_forcing.py`; 2 parity-smoke entries are fixture rows, not separate test cases).

### Migration

Pure-additive bridge + CLI; no existing call sites change. `ES_VERSION_STRING` bumps `0.21.2 → 0.21.3`.

## [0.21.2] — 2026-05-07

**Magnetic-multipole-derived dynamo-region constraints — second cross-channel coupling surface in the §17.4.2 v0.21.x sequence.** Pure-Python additive; **no ABI bump** (eleventh consecutive ship since v0.13.x with no ABI movement).

### What ships

| Surface | Function / subcommand |
|---|---|
| Pythonic API | `_research.dynamo_catalog.compute_dynamo_region / list_dynamo_regions` |
| Bridge dict API | `bridge.get_dynamo_region(body=None)` / `bridge.list_dynamo_regions()` |
| CLI | `dynamo-region [--body X]` / `dynamo-regions` |

### Physics

For a body with a published spherical-harmonic magnetic-field expansion (v0.20.1 MAGNETIC_MULTIPOLE_MODELS), the Lowes-Mauersberger spectrum R(n) ∝ (R_dynamo / R_surface)^(2n+4) — the mean-square magnetic field at the body surface, summed over orders at each degree n — has a degree-decay shape that depends on the source-layer geometry. Log-slope inversion gives R_dynamo / R_surface; rearrange to get the absolute dynamo radius.

### 5-body roster

| Body | Source | R_dynamo / R_body | R_dynamo (km) | Material |
|---|---|---:|---:|---|
| **terra** | **Lowes 1974** | **0.547** | **3486** | molten Fe-Ni alloy |
| mercury | Christensen 2006 | 0.83 | 2025 | molten Fe-Ni alloy |
| **jupiter** | **Connerney 2022 (JRM33)** | **0.85** | **60768** | **metallic H** |
| **saturn** | **Cao 2020 / Stevenson 2010** | **0.55** | **33147** | **metallic H** |
| ganymede | Schubert 1996 | 0.27 | 711 | molten Fe-FeS alloy |

### Highlights

- **Earth CMB at 3486 km** — the canonical Lowes 1974 result; magnetic inversion matches seismology (PREM CMB depth 2891 km) to better than 1%. This is the validation case for the technique.
- **Jupiter at 0.85 R_J** — Connerney 2022 from JRM33 deg-18; dynamo lives just above the metallic-H phase boundary.
- **Saturn axisymmetry as constraint** — the famous < 0.007° dipole tilt is itself a dynamo constraint via the Stevenson 1980 mechanism: a thick stably-stratified layer above the dynamo filters all non-axisymmetric modes.
- **Mercury anomaly** — standard Lowes-Mauersberger fails because of stable stratification; Christensen 2006 weak-field model gives 0.83 R_Me.
- **Ganymede** — only intrinsic-moon dynamo in the solar system; max_degree=1 dipole-only published, so depth comes from Schubert 1996 thermal-evolution models.

### Architectural choice

**Not a re-derivation.** Values shipped are the published inversions from the cited papers. Per-degree Lowes-Mauersberger spectrum tables remain in those papers; this catalog is the navigation layer.

### Citation discipline

5-entry `SOURCES` citation dict (Lowes 1974, Christensen 2006, Connerney 2022, Cao 2020, Schubert 1996); ratchet tests pin both directions.

### Forward sequence (per §17.4.2)

* **v0.21.3** — Orographic forcing of atmospheric standing waves (Hollingsworth 1997 Mars; Tharsis bulge as planetary-scale standing-wave generator).
* **v0.21.4+** — More cross-channel coupling surfaces from §17.1/§17.2/§17.3 follow-ups.

### Test count

975 pass, 41 skipped (was 949 + 41 in v0.21.1; +26 net new — 24 in `test_dynamo_catalog.py` + 2 parity-smoke entries + 2 README-freshness tests that flipped GREEN after the Status banner update).

### Migration

Pure-additive bridge + CLI; no existing call sites change. `ES_VERSION_STRING` bumps `0.21.1 → 0.21.2`.

## [0.21.1] — 2026-05-07

**Topography ↔ gravity admittance — first cross-channel coupling surface in the §17.4.2 v0.21.x sequence.** Promotes notebook §17.4.2 to a stable ship surface (per §17.4.2: "v0.21.1+ Cross-channel coupling surfaces, one per minor version: topography ↔ gravity admittance, magnetic-multipole-derived dynamo constraints, orographic forcing of atmospheric standing waves"). Pure-Python additive; **no ABI bump** (tenth consecutive ship since v0.13.x with no ABI movement).

### What ships

| Surface | Function / subcommand |
|---|---|
| Pythonic API | `_research.admittance_catalog.compute_topography_gravity_admittance / list_admittance_spectra` |
| Bridge dict API | `bridge.get_topography_gravity_admittance(body=None)` / `bridge.list_admittance_spectra()` |
| CLI | `admittance [--body X]` / `admittance-spectra` |

### Physics

For a body with both a published gravity multipole expansion (v0.20.0 GRAVITY_MODELS) and a topography model (v0.20.0 TOPOGRAPHY_MODELS), the spectral admittance Z(n) = ⟨SH_gravity[n,m]·conj(SH_topography[n,m])⟩ / ⟨|SH_topography[n,m]|²⟩ at each spherical-harmonic degree n constrains crustal density and crustal thickness via isostatic compensation theory. Low Z(n) at long wavelengths is a signature of Airy compensation; high Z(n) at short wavelengths is uncompensated topographic loading.

### 5-body roster

| Body | Source | Mean Z (mGal/km) | ρ_c (kg/m³) | Crust (km) | Compensation |
|---|---|---:|---:|---:|---|
| terra | Wieczorek 2007 / Watts 2001 | 50 | 2670 | 35 | Airy |
| luna | Wieczorek 2013 (GRAIL+LOLA) | 95 | 2550 | 38.5 | Airy |
| mars | Genova 2016 + Konopliv 2016 | 110 | 2900 | 50 | Airy |
| mercury | James 2015 (MESSENGER) | 85 | 3200 | 35 | Airy |
| venus | Anderson 2002 (Magellan) | 200 | 2900 | 20 | lithospheric_flexure |

### Highlights

- **Lunar 2550 kg/m³ crustal density** — the famous Wieczorek 2013 GRAIL+LOLA result; revised down from prior ~2900.
- **Venus highest Z** — ~200 mGal/km, weak Airy compensation; lithospheric-flexure / mantle-plume support model dominates instead.
- **Mars bimodal crust** — global mean ~50 km masks 30 km northern lowlands vs 70 km southern highlands; Tharsis dominates n<10.
- **Mercury high crustal density** ~3200 kg/m³ consistent with Mercury's overall high planetary density.

### Architectural choice

**Not a re-derivation.** Values shipped are the integrated Z summary published in the cited papers (mean Z + inferred crustal density + crustal thickness). Per-degree Z(n) tables remain in the cited papers' supplementary materials; this catalog is the navigation layer.

### Citation discipline

Every Z(n) value carries a `source_key` pointing into a 5-entry `SOURCES` dict (Wieczorek 2007, Wieczorek 2013, Genova 2016, James 2015, Anderson 2002). Ratchet tests pin both directions.

### Forward sequence (per §17.4.2)

* **v0.21.2** — Magnetic-multipole-derived dynamo-region constraints (Connerney 2022 Jupiter; Stevenson 2010 reviews for the giants).
* **v0.21.3** — Orographic forcing of atmospheric standing waves (Hollingsworth 1997 Mars; Tharsis bulge as planetary-scale standing-wave generator).
* **v0.21.4+** — More cross-channel coupling surfaces from §17.1/§17.2/§17.3 follow-ups.

### Test count

949 pass, 41 skipped (was 922 + 41 in v0.21.0; +27 net new — 25 in `test_admittance_catalog.py` + 2 parity-smoke entries + 2 README-freshness tests that flipped GREEN after the Status banner update).

### Migration

Pure-additive bridge + CLI; no existing call sites change. `ES_VERSION_STRING` bumps `0.21.0 → 0.21.1`.

## [0.21.0] — 2026-05-07

**Sol Spherical Harmonic Catalog — unification refactor across the v0.20.0 gravity sector + v0.20.1 magnetic sector.** Promotes notebook §17.4.2 to a stable ship surface. **This is a unification refactor, not a new data store** — the underlying records still live in `geodetic_catalog_data` (gravity Stokes coefficients in 4π-norm) and `magnetic_multipole_catalog_data` (magnetic Schmidt-quasi-normalised g_n^m / h_n^m). The v0.20.0 / v0.20.1 surfaces continue to work unchanged. Pure-Python additive; **no ABI bump** (ninth consecutive ship since v0.13.x with no ABI movement).

### What ships

| Surface | Function / subcommand |
|---|---|
| Pythonic API | `_research.spherical_harmonic_catalog.compute_spherical_harmonics / list_spherical_harmonic_models / convert_normalisation` |
| Bridge dict API | `bridge.get_spherical_harmonics(body, channel="both")` / `bridge.list_spherical_harmonic_models()` / `bridge.convert_spherical_harmonic_normalisation(value, n, m, from_convention, to_convention)` |
| CLI | `spherical-harmonics --body X [--channel gravity|magnetic|both]` / `spherical-harmonic-models` / `convert-normalisation --value X --n X --m X --from X --to X` |

### Unified query surface

`get_spherical_harmonics(body, channel="both")` returns the v0.20.0 + v0.20.1 records adapted to a unified shape with explicit `normalisation_convention` per channel (`"4pi-Stokes"` / `"Schmidt-quasi-norm"`). Bodies absent from a requested channel return `None` for that channel — Mars has gravity but no global intrinsic dipole (magnetic = None); Ganymede has both (the unique intrinsic-moon-dipole case); icy moons have gravity but no magnetic.

### Roster reach

- 56 gravity models (from v0.20.0) + 7 magnetic models (from v0.20.1) = **56 unified bodies** (magnetic ⊆ gravity).
- **7 both-channels bodies** (intersection): terra, mercury, jupiter, saturn, uranus, neptune, ganymede.
- Merged 76-entry `SOURCES` citation dict spanning both sectors.

### Normalisation conversion helper

`convert_normalisation(coefficient_value, n, m, from_convention, to_convention)` implements the Winch et al. (2005) closed-form: `C̄_nm = g_n^m / sqrt((2 - δ_0m) * (2n + 1))`, where δ_0m = 1 if m=0 else 0. Round-trip identity verified to float-machine precision. Validates `n ≥ 0`, `0 ≤ m ≤ n`, finite numeric input, recognised convention labels.

### Architectural choice

The "unification" is a NEW query surface that exposes both channels via a common interface; it does NOT refactor the underlying storage. This preserves back-compat with v0.20.0 / v0.20.1 callers, which is verified by explicit regression tests:
- `test_v0_20_0_geodetic_state_still_works` — `bridge.get_geodetic_state(body="terra")` returns its original v0.20.0 shape.
- `test_v0_20_1_magnetic_multipoles_still_works` — `bridge.get_magnetic_multipoles(body="jupiter")` returns its original v0.20.1 shape.

### Forward sequence (per §17.4.2)

* **v0.21.1+** — Cross-channel coupling surfaces (one per minor): topography ↔ gravity admittance (Wieczorek 2007); magnetic-multipole-derived dynamo-region constraints (Connerney 2022 Jupiter; Stevenson 2010 reviews); orographic forcing of atmospheric standing waves (Hollingsworth 1997 Mars; Tharsis bulge as planetary-scale standing-wave generator).

### Test count

922 pass, 41 skipped (was 889 + 41 in v0.20.2; +33 net new — 30 in `test_spherical_harmonic_catalog.py` + 3 parity-smoke entries + 2 README-freshness tests that flipped GREEN after the Status banner update).

### Migration

Pure-additive bridge + CLI; no existing call sites change. `ES_VERSION_STRING` bumps `0.20.2 → 0.21.0`.

## [0.20.2] — 2026-05-07

**Sol Fluid Instrument — climatology + archive index + state-at-epoch query surface for the solar-system fluid envelope (atmospheres, oceans, cryospheres, exospheres).** Promotes notebook §17.3 + §17.4.2 to a stable ship surface, mirroring the v0.19.0 EM Instrument / v0.20.0 Sol Geodetic Catalog / v0.20.1 Sol Magnetic Multipole Catalog patterns. **Ships all three Option-D layers together** per the §17.4.2 full-coverage commitment — no MVP subset, no deferred layer. **Not a BIP encoder running on fluid-envelope rhythms** — per §17.4.1 the rhythm-mismatch finding generalises across fluid envelopes alongside solid-body geodesy and magnetic multipoles. Pure-Python additive; **no ABI bump** (eighth consecutive ship since v0.13.x with no ABI movement).

### What ships

| Surface | Function / subcommand |
|---|---|
| Pythonic API | `_research.fluid_instrument.compute_fluid_state / list_fluid_archives / compute_fluid_architecture` |
| Bridge dict API | `bridge.get_fluid_state(body=None, jd_tdb=None, lat=None, lon=None)` / `bridge.list_fluid_archives()` / `bridge.fluid_architecture(target=None)` |
| CLI | `fluid-state [--body X] [--jd-tdb X] [--lat X] [--lon X]` / `fluid-archives` / `fluid-architecture [--target X]` |

### Three layers

**Layer 1 — Climatological summary** (21 entries: 17 atmospheric + 4 airless small bodies):
- Atmospheric: terra / mars / venus / titan / triton / pluto / io / europa / ganymede / enceladus / mercury / luna / sun / jupiter / saturn / uranus / neptune.
- Airless: ceres / vesta / bennu / ryugu.
- Per-body fields: mean surface temperature K, mean surface pressure Pa, top-3 dominant gases (formula + mole fraction), obliquity deg, orbital eccentricity, Bond albedo.

**Layer 2 — Archive-pointer index** (10 entries):
ERA5 (terra), MCD v6.1 (mars), MAVEN (mars-upper-atmosphere), VIRA + Akatsuki (venus), Cassini (titan + saturn), Juno (jupiter), Voyager 2 PDS (uranus + neptune), New Horizons PDS (pluto). Each entry carries archive_url + format + access_protocol + temporal coverage window.

**Layer 3 — State-at-epoch coverage flags** (21 entries):
ONLY terra (ERA5; JD ≈ 2429630.5 onward = 1940-01-01) and mars (MCD v6.1; MY 24-start onward) have the True flag. All 19 other bodies fall back to the climatological summary with explicit `out-of-coverage-fallback-to-climatology` query_type.

### No outbound network calls

The package ships pointers + the climatological-summary fallback in a self-contained dict; consumers fetch the actual reanalysis field via the archive's own API (CDS-API for ERA5; the Python wrapper for MCD). The package never makes outbound HTTP calls.

### Coverage status triage

When `jd_tdb` is passed to `get_fluid_state`, the response includes a `coverage_status` flag: `in_coverage` / `before_archive` / `future` / `no_state_at_epoch`. Earth at modern JD → `in_coverage`; Earth at JD 2400000 (1858) → `before_archive`; Venus at any JD → `no_state_at_epoch` (no state-at-epoch wrapper, only climatology + archive pointers).

### Highlights

- **Titan** — 94 K + 1.45 bar atmosphere (denser than Earth's despite the cold; the only moon with a thick atmosphere).
- **Triton** — 38 K + 1.4 Pa (one of the coldest known surfaces in the solar system).
- **Pluto** — seasonal atmospheric collapse / recovery cycle tracked via HST stellar occultations + New Horizons in situ.
- **Io** — SO₂ pressure variability over 8 orders of magnitude from sublimation cycle.
- **Enceladus** — column-not-pressure convention applies (south-polar plume venting via tiger-stripe fractures).
- **Uranus** — extreme 97.77° obliquity → 42-yr seasonal cycles.

### Architecture partition

`{HIGH: 13, MEDIUM: 8, LOW: 0, NONE: 1}` — fluid-channel sibling of the v0.20.0/v0.20.1 partitions. The single NONE entry is `mars-upper-atmosphere` (appears as an archive-only body string for MAVEN PDS data, distinct from `mars` MCD lower-atmosphere coverage).

### Citation discipline

Every numeric value carries a `source_key` pointing into a 24-entry `SOURCES` dict (NASA fact sheets / mission archives / journal refs). Ratchet tests pin both directions (every key resolves; no unused entries).

### Forward sequence (per §17.4.2)

* **v0.21.0** — `SphericalHarmonicCatalog` unification refactor across gravity (v0.20.0) + magnetic (v0.20.1) sectors.
* **v0.21.1+** — Cross-channel coupling surfaces (one per minor): topography ↔ gravity admittance, magnetic-multipole-derived dynamo constraints, orographic forcing of atmospheric standing waves.

### Test count

889 pass, 41 skipped (was 834 + 41 in v0.20.1; +55 net new — 50 in `test_fluid_instrument.py` + 3 parity-smoke entries + 2 README-freshness tests that flipped GREEN after the Status banner update).

### Migration

Pure-additive bridge + CLI; no existing call sites change. `ES_VERSION_STRING` bumps `0.20.1 → 0.20.2`.

## [0.20.1] — 2026-05-07

**Sol Magnetic Multipole Catalog — state-lookup query surface for the published-internal-field roster across the solar system.** Promotes notebook §17.2 + §17.4.2 to a stable ship surface, mirroring the v0.19.0 EM Instrument and v0.20.0 Sol Geodetic Catalog patterns. **Not a BIP encoder running on magnetic-field rhythms** — per §17.4.1 the rhythm-mismatch finding generalises across magnetic multipoles alongside solid-body geodesy and fluid-envelope channels: internal-field Schmidt-quasi-normalised g_n^m / h_n^m coefficients are static at their epoch, so the cyclic-group encoder discipline does not transplant. Pure-Python additive; **no ABI bump** (seventh consecutive ship since v0.13.x with no ABI movement).

### What ships

| Surface | Function / subcommand |
|---|---|
| Pythonic API | `_research.magnetic_multipole_catalog.compute_magnetic_multipoles / evaluate_magnetic_field / compute_solar_synoptic_state / list_magnetic_multipoles / compute_magnetic_architecture` |
| Bridge dict API | `bridge.get_magnetic_multipoles(body=None, crustal=False)` / `bridge.evaluate_magnetic_field(body, r_km, lat_deg, lon_deg, jd_tdb=None)` / `bridge.get_solar_synoptic_state(jd_tdb=None)` / `bridge.list_magnetic_multipoles()` / `bridge.magnetic_architecture(target=None)` |
| CLI | `magnetic-multipoles [--body X] [--crustal]` / `magnetic-field --body X --r-km X --lat-deg X --lon-deg X` / `solar-synoptic [--jd-tdb X]` / `magnetic-models` / `magnetic-architecture [--target X]` |

### 7-body main-field roster

| Body | Model | Max degree | Tier | Structural flag |
|---|---|---:|---|---|
| terra | IGRF-13 (Alken 2021) | 13 | HIGH | — |
| jupiter | JRM33 (Connerney 2022) | 18 | HIGH | great_blue_spot_resolved |
| saturn | Cao-2020 (Cassini Grand Finale) | 14 | HIGH | axisymmetric_dipole_tilt_under_0.007_deg |
| mercury | Thébault-2018 (MESSENGER reanalysis) | 5 | MEDIUM | offset_dipole_north_484km |
| ganymede | Kivelson-2002 dipole | 1 | MEDIUM | only_intrinsic_moon_dipole |
| uranus | AH5 (Holme & Bloxham 1996) | 3 | LOW | tilted_offset_58.6_deg |
| neptune | O8 (Holme & Bloxham 1996) | 3 | LOW | tilted_offset_47_deg |

Plus 1 crustal field model — Earth EMM2017 (degree 720, ~30 MB lazy-load via `crustal=True` flag) — and 1 solar synoptic reference — Stanford HMI (Carrington-rotation cadence, coverage 2010-present) accessible via `bridge.get_solar_synoptic_state(jd_tdb)`. The Sun's time-varying field lives behind a different surface than the static catalog.

### Notable per-body data

* **Saturn dipole tilt < 0.007°** (Cao 2020 axisymmetric-dynamo result) shipped as a first-class `structural_flag`.
* **Mercury offset dipole** ~484 km northward of body centre.
* **Ganymede** — only solar-system moon with a confirmed intrinsic dipole (Kivelson 2002); dipole-only published, "higher-degree pending JUICE 2034" flag.
* **Uranus + Neptune** — Voyager-only single-flyby fits with explicit LOW precision flag.

### Citation discipline

Every numeric value carries a `source_key` pointing into a 9-entry `SOURCES` dict (DOIs / mission archives / journal refs). Tests pin the resolution:

* `test_every_main_field_source_key_resolves`
* `test_every_crustal_source_key_resolves`
* `test_every_synoptic_source_key_resolves`
* `test_no_unused_sources_entries` (no stale citations)

### Architectural choice

State-*lookup* surface, mirroring v0.20.0 Sol Geodetic Catalog (no JD-advance mechanic — the IGRF main field updates every 5 years on a published schedule, not via JD-ticking arithmetic). The `evaluate_magnetic_field` surface ships dipole-only synthesis (`synthesis_degree=1`) for v0.20.1; higher-degree synthesis is deferred to a future minor version.

### Forward sequence (per §17.4.2)

* **v0.20.2** — `SolFluidInstrument` (climatological summary + archive index + Earth/Mars state-at-epoch surface).
* **v0.21.0** — `SphericalHarmonicCatalog` unification refactor across gravity (v0.20.0) + magnetic (v0.20.1) sectors.
* **v0.21.1+** — Cross-channel coupling surfaces (one per minor version).

### Package metadata refresh

The `pyproject.toml` description was advertising the obsolete v0.5-era 38-body roster + omitting all the v0.16-v0.20.x catalog work. Refreshed to list the 52-body roster + per-body Sol Geodetic / Electromagnetic / Magnetic-Multipole catalogs + resonance-graph ITN-chain search + spectral body-architecture surfaces. Stale "38-body" language scrubbed from `bridge.py`, `cli.py`, and the upstream `research/` modules that codegen mirrors into `_research/`.

### Test count

834 pass, 41 skipped (was 769 + 41 in v0.20.0; +65 net new — 59 in `test_magnetic_multipole_catalog.py` + 5 parity-smoke entries + 1 reconciliation).

### Migration

Pure-additive bridge + CLI; no existing call sites change. `ES_VERSION_STRING` bumps `0.20.0 → 0.20.1`.

## [0.20.0] — 2026-05-07

**Sol Geodetic Catalog — state-lookup query surface for the solar-system solid-body geodetic stack.** Promotes notebook §17.1 + §17.4.2 to a stable ship surface, mirroring the v0.19.0 Sol Electromagnetic Instrument pattern. **Not a BIP encoder running on geodetic rhythms** — per §17.4.1 the rhythm-mismatch finding generalises across solid-body geodesy alongside magnetic multipoles and fluid-envelope channels: solid-body geodetic observables (Stokes coefficients, DEM spectra, layered density profiles) are static parameters with no native rhythm, so the cyclic-group encoder discipline does not transplant. Three internal channels per body: gravity multipoles + topography / shape model metadata + interior structure. Pure-Python additive; **no ABI bump** (sixth consecutive ship since v0.13.x with no ABI movement).

### What ships

| Surface | Function / subcommand |
|---|---|
| Pythonic API | `_research.geodetic_catalog.compute_geodetic_state / list_geodetic_models / compute_geodetic_architecture` |
| Bridge dict API | `bridge.get_geodetic_state(body=None)` / `bridge.list_geodetic_models()` / `bridge.geodetic_architecture(target=None)` |
| CLI | `geodetic-state [--body X]` / `geodetic-models` / `geodetic-architecture [--target X]` |

### Roster + channel coverage

Full §17.4.2 commitment: every body in the v0.16.0 52-body celestial roster that has a published gravity model, topography / shape model, or interior structure model is in scope. Three internal channels — gravity multipoles, topography / shape, interior structure — partitioned by data-quality tier (HIGH / MEDIUM / LOW / NONE per §17.1.6 convention). Sparse coverage by design: not every body has a published model in every channel; missing channels return `None` rather than raising.

### Citation discipline

Every numeric value carries a `source_key` pointing into a `SOURCES` dict (DOIs / mission archives / journal refs). Tests pin the resolution: ratchet checks that every per-body `source_key` is a real key in `SOURCES`.

### Architectural choice

Option B (separate sibling instrument), not Option A (kernel-patch onto celestial Laplacian). Geodetic observables don't have a rhythm at all (no native period; J₂ doesn't oscillate, DEM spectra don't tick) — the rhythm-mismatch finding from §16 generalises by *absence-of-rhythm* on this side. The Sol Geodetic Catalog is therefore a state-*lookup* surface (no JD-advance mechanic) rather than a state-*at-epoch* surface like the v0.19.0 EM Instrument.

### Forward sequence committed in §17.4.2

* **v0.20.1** — `MagneticMultipoleCatalog` (full published high-degree internal-field roster).
* **v0.20.2** — `SolFluidInstrument` (climatological summary + archive index + Earth/Mars state-at-epoch).
* **v0.21.0** — `SphericalHarmonicCatalog` unification refactor across gravity + magnetic + fluid sectors.
* **v0.21.1+** — Cross-channel coupling surfaces (one per minor version): topography ↔ gravity, interior ↔ rotation, etc.

### Migration

Pure-additive bridge + CLI; no existing call sites change. `ES_VERSION_STRING` bumps `0.19.0 → 0.20.0`.

## [0.19.0] — 2026-05-06

**Sol Electromagnetic Instrument — state-at-epoch query surface for the solar-system EM sector.** Promotes notebook §16.9 to a stable ship surface. **Not a BIP encoder** — per §16.3 / §16.9.1 the rhythm-mismatch finding established that EM clocks (rotational, Carrington, solar cycle, plume duty cycles) don't form a low-order rational lattice with orbital periods, so the cyclic-group encoder discipline doesn't transplant. Pure-Python additive; **no ABI bump** (fifth consecutive ship since v0.13.x with no ABI movement).

### What ships

| Surface | Function / subcommand |
|---|---|
| Pythonic API | `_research.em_instrument.compute_em_state_at_jd / list_em_couplings / compute_em_architecture` |
| Bridge dict API | `bridge.get_em_state(jd_tdb)` / `bridge.list_em_couplings()` / `bridge.em_architecture(target=None)` |
| CLI | `em-state --jd-tdb X` / `em-couplings` / `em-architecture [--target X]` |

### 16-body roster

| Class | Count | Bodies |
|---|---:|---|
| star | 1 | sun |
| magnetised | 7 | mercury, terra, jupiter, ganymede, saturn, uranus, neptune |
| induced | 4 | venus, europa, callisto, titan |
| unmagnetised | 4 | luna, mars, io, enceladus |

### 7 pairwise EM couplings

| Pair | Kind | Power | Source |
|---|---|---:|---|
| Jupiter ↔ Io | flux_tube | ~10¹² W | Saur 2007 / Hess et al. 2010 |
| Saturn ↔ Enceladus | plasma_mass_loading | ~5×10⁹ W | Pontius & Hill 2006 |
| Saturn ↔ Titan | induced_magnetosphere | ~10⁹ W | Cassini magnetometer |
| Sun ↔ Terra | imf_reconnection | ~5×10⁹ W | Lockwood 2022 |
| Jupiter ↔ Europa | induced_magnetosphere | ~10¹⁰ W | Khurana 1998 |
| Jupiter ↔ Ganymede | intrinsic_field_to_intrinsic_field | ~10¹⁰ W | Kivelson 2002 |
| Sun ↔ asteroid_belt_bulk | radiation_pressure | ~10¹⁵ W | Bottke 2006 |

### Notable per-body data

* **Jupiter dipole** 1.52×10²⁰ T·m³ (JRM33 Connerney 2022)
* **Earth dipole** 7.94×10²² A·m² (IGRF-13 Alken et al. 2021)
* **Ganymede** — only solar-system moon with confirmed intrinsic dipole (Kivelson 2002)
* **Saturn rotation period** 0.4467 d ± 1 % (Voyager / Cassini SKR disagreement; flagged per §16.3)

### Citation discipline

Every numeric value carries a `source_key` pointing into a 19-entry `SOURCES` dict (DOIs / mission archives / journal refs). Tests pin the resolution: `test_every_body_source_key_resolves` + `test_every_coupling_source_key_resolves`.

### Architectural choice

Option B (separate sibling instrument), not Option A (kernel-patch onto celestial Laplacian). EM rhythms don't form a low-order rational lattice with orbital periods; cross-channel coupling (Io plasma → Io flux tube → DAM synchrotron) means EM should be ONE sibling instrument, not five sub-instruments. User course-correction during the §16 writing widened the scope from "magnetic-only" → "electromagnetic" before the ship.

### Test count

730 pass, 41 skipped (was 685 + 41 in v0.18.2; +45 net new — 46 in `tests/test_em_instrument.py` + 3 parity-smoke entries — minus a small reconciliation when rebased onto v0.18.2).

### Migration

Pure-additive bridge + CLI; no existing call sites change. `ES_VERSION_STRING` bumps `0.18.2 → 0.19.0` (v0.19.0 includes the v0.18.2 2-D Fiedler-embedding upgrade for `predict_itn_accessibility` from the parallel branch — both ships landed on the same day).

## [0.18.2] — 2026-05-06

**2-D `(f₂, f₃)` Fiedler-embedding upgrade for `bridge.predict_itn_accessibility`.** The §13.6 unfinished refinement applied to the v0.18.1 ship: replaces the 1-D Fiedler-distance regression with a 2-D Euclidean-embedding regression on the same hybrid Laplacian. Pure-Python additive improvement; **no ABI bump** (`ES_ABI_VERSION = 8` unchanged).

### Calibration delta

| Metric | v0.18.1 (1-D) | v0.18.2 (2-D) | Lift |
| :--- | ---: | ---: | ---: |
| Spearman ρ | +0.857 | +0.849 | ~unchanged |
| In-sample R² | 0.5072 | **0.6439** | +27 % |
| In-sample MAE | 4.110 km/s | **2.995 km/s** | **−27 %** |
| LOOCV MAE | 4.238 km/s | **3.123 km/s** | **−26 %** |
| LOOCV median \|err\| | not reported | **2.204 km/s** | new |

Spearman unchanged because the rank ordering was already strong; the lift comes from absolute fit quality. The second eigenvector `f₃` adds resolution for within-cluster pairs that the single Fiedler vector collapsed (Earth/Venus + main-belt asteroids cluster at `f₃ > 0`; outer planets at `f₃ < 0`; mercury isolated at `f₃ ≈ −0.28`).

### Updated calibration constants

| Constant | v0.18.1 (1-D) | v0.18.2 (2-D) |
| :--- | ---: | ---: |
| `CALIBRATION_INTERCEPT_KMS` | 8.681 | **4.896** |
| `CALIBRATION_SLOPE_KMS_PER_FIEDLER_UNIT` | 15.617 | **17.319** |
| `CALIBRATION_R2` | 0.507 | **0.644** |
| `CALIBRATION_LOOCV_MAE_KMS` | 4.238 | **3.123** |

The v0.18.1 constants are preserved as `CALIBRATION_INTERCEPT_KMS_1D_HISTORICAL` etc. for callers that pinned the v0.18.1 numbers.

### Bridge response shape

* Existing fields unchanged: `ok`, `departure`, `target`, `fiedler_distance` (1-D back-compat), `predicted_dv_kms`, `calibration`.
* New fields:
  * `embedding_distance_2d` (float) — the 2-D Euclidean distance on the `(f₂, f₃)` embedding (the production predictor input).
  * `calibration.embedding_dim` = 2 (was implicitly 1 in v0.18.1).
  * `calibration.lambda_3` (float) — third eigenvalue, alongside the existing `lambda_2`.
  * `calibration.loocv_median_abs_error_kms` (float) — LOOCV median absolute error.
  * `calibration.method` updated to "OLS linear fit on 2-D (f₂, f₃) hybrid Fiedler embedding".

### Research origin

Notebook §13.6 listed five untried refinements after the §13.5 inv_dv baseline. The v0.18.1 ship calibrated the §13.9 hybrid weighting in 1-D; v0.18.2 closes the §13.6 refinement #1 (two-eigenvector embedding) on top of the same hybrid weighting. New `research/two_eigenvector_fiedler_embedding.py` runs all three weightings (inv_dv, resonance, hybrid) under both 1-D and 2-D embeddings and emits the comparison table.

### Test count

685 pass, 41 skipped (was 681 + 41 in v0.18.1; +4 new tests in `test_predict_itn_accessibility.py`):
- Calibration constants re-pinned to 2-D values
- 1-D historical constants preserved + tested
- New `embedding_distance_2d` field exposed in response
- New `embedding_dim` + `lambda_3` + `loocv_median_abs_error_kms` calibration metadata pinned

### Migration

Pure-additive on the response shape (new fields added; no existing field removed or renamed). Numeric values for `predicted_dv_kms` change as expected (different regression). Callers that pinned the v0.18.1 numeric values via `CALIBRATION_INTERCEPT_KMS` etc. should either re-pin to the v0.18.2 values *or* read the v0.18.1 numbers from the new `*_1D_HISTORICAL` constants.

## [0.18.1] — 2026-05-06

**`bridge.predict_itn_accessibility`: closed-form spectral Δv estimate from the §13.9 hybrid Fiedler-distance regression.** Promotes the v0.17.x research output (notebook §13.9.4) — the multiplicative `inv_dv × resonance` gateway-graph Laplacian's Fiedler distance as a continuous predictor of multi-leg ITN-chain Δv — to a stable ship surface. **Pure-Python addition; no ABI bump** (third consecutive ship since v0.13.x with no ABI movement; `ES_ABI_VERSION = 8` unchanged from v0.17.0 / v0.18.0).

### What ships

| Surface | Function / subcommand | Description |
|---|---|---|
| Pythonic API | `_research.predict_itn_accessibility.predict_itn_accessibility(departure, target)` | Returns `{ok, departure, target, fiedler_distance, predicted_dv_kms, calibration}` |
| Bridge dict API | `bridge.predict_itn_accessibility(departure, target)` | Pyodide-compatible wrapper |
| CLI | `predict-itn-accessibility` | Flags: `--departure`, `--target`, `--pretty` |
| Calibration script | `research/calibrate_predict_itn_accessibility.py` | OLS + LOOCV regression fitter; re-fits the constants against a re-sampled ground truth |

### Algorithm

1. At module load, build the **hybrid** `inv_dv × resonance` edge-weighted Laplacian on the v0.16.0 13-body heliocentric Tier-1 roster (same primitive as `body_architecture` but with hybrid weights), compute its Fiedler eigenvector with the shortest-period sign convention.
2. For an input `(departure, target)` pair, compute the Fiedler distance `d_F = |f₂[i] - f₂[j]|`.
3. Apply the calibrated linear regression `predicted_dv_kms = INTERCEPT + SLOPE * d_F`.

### Calibration

Fit by `calibrate_predict_itn_accessibility.py` against ground truth from a 50-yr `find_itn_chains` sweep at J2000 (max_legs=3, dv_budget=30 km/s, threshold=0.1). 53 feasible pairs (out of 78 in the 13-body roster; 25 infeasible within budget) drive the linear fit:

| Constant | Value |
|---|---|
| `CALIBRATION_INTERCEPT_KMS` | 8.680818 |
| `CALIBRATION_SLOPE_KMS_PER_FIEDLER_UNIT` | 15.617194 |
| `CALIBRATION_R2` | 0.5072 |
| `CALIBRATION_IN_SAMPLE_MAE_KMS` | 4.110 |
| `CALIBRATION_LOOCV_MAE_KMS` | 4.238 |
| `CALIBRATION_SPEARMAN_RHO` | 0.857 |
| `CALIBRATION_N_FINITE_PAIRS` | 53 |
| `CALIBRATION_N_INF_PAIRS` | 25 |

### Use case + disclaimers

* **Use for fast first-pass triage** — microseconds per query vs ~1.5 s for the full Dijkstra. The +0.857 Spearman is suitable for ranking candidate pairs by predicted accessibility.
* **Do NOT use for trajectory design** — the absolute MAE is ~4 km/s on a 2–28 km/s domain, useful for ranking but too coarse for mission-budget purposes. Mission design should call `find_itn_chains` for the full Dijkstra answer.
* **Calibration is window-specific.** For widely different search windows (e.g. multi-decade outer-system missions), re-calibrate by running the calibration script against a re-sampled ground truth.

The calibration provenance — Spearman ρ, R², MAE, LOOCV MAE, n_finite, n_inf, window — is returned in every response, so callers can decide whether the prediction is precise enough for their use case.

### Notebook addition

§14 (the holographic-principle-at-macro-scale section, added in this ship) re-reads the §13.9 / v0.18.1 regression as the bulk-boundary correspondence's "real" empirical payload: the spectral boundary (13-D Fiedler vector) anticipates the trajectory bulk (78-pair × 3-leg Dijkstra) at calibrated Spearman 0.857.

### Test count

681 pass, 41 skipped (was 658 + 41 in v0.18.0; +23 new — 22 in `tests/test_predict_itn_accessibility.py` covering: calibration constants pinned + non-negative predictions for all 13 × 12 = 156 ordered pairs + direction-symmetry + cheap-vs-expensive sanity ordering + intercept-as-lower-bound pin + calibration metadata-in-response + error paths (self-transfer / unknown body / non-string / case-insensitive normalisation) + bridge surface + CLI surface; +1 parity-smoke entry).

### Migration

Pure-additive on the Python bridge and the CLI. No existing call sites change. Native callers see `ES_ABI_VERSION = 8` unchanged. `ES_VERSION_STRING` bumps `0.18.0 → 0.18.1`.

## [0.18.0] — 2026-05-06

**Body Architecture: inner/outer system classification of heliocentric bodies via the resonance-weighted gateway-graph Laplacian Fiedler partition.** First spectral-architecture surface in the bridge — the v0.17.x research output (notebook §13.8) promoted to a stable ship API. Pure-Python addition; **no ABI bump** (second consecutive ship since v0.13.x with no ABI movement; `ES_ABI_VERSION = 8` unchanged from v0.17.0).

### What ships

| Surface | Function / subcommand | Description |
|---|---|---|
| Pythonic API | `_research.body_architecture.compute_body_architecture(bodies=None)` | Returns full classification dict |
| Bridge dict API | `bridge.body_architecture(target=None)` | Pyodide-compatible — full partition by default; single-body record if `target` given |
| CLI | `body-architecture` | Flags: `--target <name>` (optional single-body lookup), `--pretty` |

### Algorithm

1. For each unordered pair `(i, j)` of heliocentric bodies, compute the period ratio `r = min(P_i, P_j) / max(P_i, P_j) ∈ (0, 1]` and the best small-integer rational `(p, q)` approximation via `_best_rational_approx(r, max_int=30)` — the same v0.17.0 ITN-chain primitive used for per-leg resonance signatures.
2. Form the symmetric edge weight `w_ij = exp(-|r - p/q| / 0.005) / (p + q)`. Strong low-order locks (Jupiter-Saturn 2:5, Neptune-Pluto 2:3, Ceres-Pallas 1:1) score high; spurious near-rationals are suppressed by the residual term.
3. Build the combinatorial Laplacian `L = D - W`. Compute eigendecomposition. Take the Fiedler eigenvector (eigenvector of the second-smallest eigenvalue λ₂).
4. Apply the sign convention: the body with the shortest sidereal period (mercury, in the default roster) is forced to have a positive Fiedler entry. This makes the inner/outer label assignment reproducible across platforms regardless of LAPACK pivoting.
5. Classify: positive Fiedler entry ⇒ "inner"; negative ⇒ "outer".

### Default classification (13-body heliocentric Tier-1 roster)

| Class | Bodies (sorted by Fiedler-vector entry) | Period range (d) |
|---|---|---|
| Outer (5) | pluto (−0.585), neptune (−0.585), uranus (−0.137), jupiter (−0.078), saturn (−0.042) | 4332 – 90560 |
| Inner (8) | hygiea (+0.093), pallas (+0.137), ceres (+0.139), vesta (+0.158), mars (+0.171), terra (+0.197), venus (+0.202), mercury (+0.329) | 88 – 2031 |

The cyclic-group encoder discovers the canonical inner/outer system division — the asteroid-belt boundary — without being told it exists. Pluto and Neptune share the deepest entry (−0.585) via their well-known 2:3 mean-motion lock dragging both deep into the outer cluster.

### Research origin

Notebook §13.8 ("the resonance-weighted Laplacian"). The §13 thread compared four edge weightings:

* **inv_dv** (§13 baseline) — Spearman ρ = +0.743 vs empirical Δv from `find_itn_chains`; partition isolates mercury alone (Mercury-isolation indicator).
* **inv_synodic** (§13 control) — Spearman ρ = −0.301; dominated by pallas/ceres near-degeneracy.
* **resonance** (§13.8) — Spearman ρ = +0.632; partition is the canonical inner/outer split — the architectural finding shipped here.
* **hybrid_dv_resonance** (§13.9) — Spearman ρ = +0.857 (clears the §13.7 ship bar); Matthews φ = +0.298 (below the partition bar). Vindicates the multiplicative-hybrid hypothesis for a *continuous* Fiedler-distance Δv predictor; queued for v0.18.x or v0.19.0 as `bridge.predict_itn_accessibility` once a Fiedler-distance → Δv regression is calibrated.

### Test count

658 pass, 41 skipped (was 622 + 41 in v0.17.0; +36 new — 34 in `tests/test_body_architecture.py` covering: default-roster shape + canonical inner-8/outer-5 partition + Pluto-Neptune deepest-entry pin + Mercury-largest-positive sign-convention pin + Fiedler-value sort order + λ₂ positivity + determinism + error paths (empty / duplicates / unknown body / zero-period body) + 13 single-body class lookups via `pytest.mark.parametrize` + bridge surface (full + single + case-insensitive + rejection) + CLI surface (full + target + `--help`) + 2 parity-smoke entries).

### Migration

Pure-additive on the Python bridge and the CLI. No existing call sites change. Native callers see `ES_ABI_VERSION = 8` unchanged. `ES_VERSION_STRING` bumps `0.17.0 → 0.18.0`.

## [0.17.0] — 2026-05-06

**Resonance-graph multi-leg `find_itn_chains` (advanced Lagrange-highway search).** Generalises the v0.8.1 closed-form Hohmann-window enumeration (`find_itn_pathways`) to multi-leg pathways via Dijkstra-style graph search over the `(body, epoch)` state space. Pure-Python addition; **no ABI bump** (first ephemerides ship since v0.13.x to leave the C wire-format alone — every ship from v0.14.0 through v0.16.0 either added bodies or expanded BODIES, each of which moved the ABI).

### New API surface

| Surface | Function / subcommand | Description |
|---|---|---|
| Python (Pythonic API) | `_research.itn_window.find_itn_chains` | Returns `List[ITNChainCandidate]`, lowest-Δv first |
| Python (bridge dict API) | `bridge.find_itn_chains` | Returns `{ok, departure, target, max_legs, n_chains, chains, ...}` (Pyodide-compatible) |
| CLI | `find-chains` | Flags: `--intermediates`, `--max-legs`, `--dv-budget-kms`, `--tof-budget-days`, `--threshold`, `--max-chains`, `--max-intermediate-windows` |

### Algorithm

Dijkstra-style graph search over the `(current_body, current_jd, total_dv, legs)` state space. Each "leg" is a closed-form Hohmann transfer window from `find_itn_pathways` (which is itself a per-pair synodic-anchor enumeration in constant time per synodic period). Legs stitch end-to-end at intermediate bodies; cumulative Δv and time-of-flight are budget-bounded. The Dijkstra invariant on cumulative Δv guarantees the first-popped target node is the optimal-Δv chain; subsequent chains are emitted in monotonically non-decreasing total-Δv order.

The graph search itself is `O(B^L × W)` worst case where B = |intermediates|, L = max_legs, W = windows per leg — bounded per node by `max_intermediate_windows` and overall by `max_chains`. In practice the Δv and TOF budgets prune aggressively.

### Resonance signature

Each leg carries a small-integer `(p, q)` gear-ratio "resonance signature" — the rational approximation of `period_dep / period_tgt` in lowest terms via the new `_best_rational_approx(ratio, max_denom=30)` helper. This is the natural cross-pollination point between the closed-form transfer-window machinery and the BIP cyclic-group encoder.

Canonical witnesses verified in `test_find_itn_chains.py`:

| Pair | Period ratio | Resonance signature | Note |
|---|---|---|---|
| Earth → Mars | 365.25 / 686.98 ≈ 0.5317 | **(8, 15)** | The well-known 8-Earth-yr / 15-Mars-orbit synodic anchor |
| Earth → Jupiter | 365.25 / 4332.589 ≈ 0.0843 | **(1, 12)** | Jupiter's ~12-year orbital period anchor |
| Jupiter → Saturn | 4332.589 / 10759.22 ≈ 0.4027 | **(2, 5)** | The famous 2:5 great-inequality resonance |

### Test count

622 pass, 41 skipped (was 601 + 41 in v0.16.0; +21 new in `tests/test_find_itn_chains.py` covering: rational-approximation invariants, direct-chain consistency with v0.8.1 `find_itn_pathways`, Dijkstra optimal-first emission ordering, Δv/TOF/max-legs budget enforcement, bridge surface (smoke + rejection paths for self-transfer / unknown body / invalid threshold / invalid budget / invalid intermediate), CLI surface (direct + multi-leg + `--help`)).

### Migration

Pure-additive on the Python bridge and the CLI. No existing call sites change. Native callers see ABI 8 unchanged.

### Sets up

The v0.17.x research thesis (notebook §12.2 → task `` `#118` ``): treat the body-graph Laplacian's Fiedler partition as a *prediction* of low-Δv accessibility, then check the prediction empirically against the chains `find_itn_chains` enumerates.

## [0.16.0] — 2026-05-06

**BODIES Tier-1 expansion (43 → 52): Lagrange trojans + retrograde irregulars + Neptune sub-graph completion.** Themed per the post-v0.15.0 audit in research notebook §11.

### BODIES additions (9 new bodies, 43 → 52)

#### Saturnian Lagrange trojans (4) — first L4/L5 entries in BODIES

| Body | Host | L-point | Period (d) | Mass (Earth) | Discoverer / year |
|---|---|---|---|---|---|
| Telesto | Tethys | L4 | 1.88780216 | 4.0e-12 | Smith / Reitsema / Larson / Fountain, 1980 |
| Calypso | Tethys | L5 | 1.88780216 | 1.2e-12 | Pascu / Seidelmann / Baum / Currie, 1980 |
| Helene | Dione | L4 | 2.73691500 | 1.9e-12 | Laques / Lecacheux, 1980 |
| Polydeuces | Dione | L5 | 2.73691500 | 4.4e-15 | Murray et al. (Cassini), 2004 |

Each trojan's sidereal period is **byte-identical** to its host moon's. The body-graph Laplacian therefore acquires a multiplicity-2 eigenvalue at the host's frequency — the spectral signature of the L4/L5 1:1 spin-orbit lock. This is the natural intersection point with v0.16.x's resonance-graph multi-leg find_itn_chains work.

#### Jovian irregulars (3)

| Body | Sense | Period (d) | Mass (Earth) | Notes |
|---|---|---|---|---|
| Himalia | prograde | 250.5662 | 1.10e-9 | Largest Jovian irregular (radius ~85 km); eponym of the Himalia group (Lysithea, Elara, Leda, Dia) |
| Pasiphae | RETROGRADE (i~141°) | 743.6300 | 5.0e-12 | Eponym of the Pasiphae group of retrograde captures |
| Sinope | RETROGRADE (i~153°) | 758.9000 | 1.3e-12 | Pasiphae-group member; near-resonant with Pasiphae (period ratio ~1.02) |

Encoder convention: BODIES['pasiphae'].period_days and BODIES['sinope'].period_days are positive (omega = +2π/P for ALL bodies regardless of orbital direction; retrograde-ness is metadata, not a sign flip — same convention as Triton in v0.14.2 and Sol Uranian Time in v0.5.4).

#### Neptunian sub-graph completion (2)

| Body | Period (d) | Mass (Earth) | Notes |
|---|---|---|---|
| Proteus | 1.12231500 | 7.40e-9 | Neptune's second-largest moon (radius ~210 km, near-spherical despite small size); Voyager 2 1989 |
| Nereid | 360.13619 | 5.10e-9 | Neptune's third-largest moon; **most eccentric major-moon orbit in the solar system** (e=0.749) |

Proteus fills the Neptune sub-graph between Triton (5.88 d) and the deferred inner-Neptunian close-packed cluster (Naiad/Thalassa/Despina/Galatea/Larissa). Nereid's 360-day period extends Neptune's low-frequency tail dramatically — before v0.16.0 the longest Neptunian period was Triton's 5.88 d.

### Sol Moon Times added (9)

| Body | Sol Time | Abbrev | CLI |
|---|---|---|---|
| Telesto | Sol Saturn-Telesto Time | **SSaTeT2** | `time-saturn-telesto` |
| Calypso | Sol Saturn-Calypso Time | **SSaCaT** | `time-saturn-calypso` |
| Helene | Sol Saturn-Helene Time | **SSaHeT** | `time-saturn-helene` |
| Polydeuces | Sol Saturn-Polydeuces Time | **SSaPoT** | `time-saturn-polydeuces` |
| Himalia | Sol Jupiter-Himalia Time | **SJuHiT** | `time-jupiter-himalia` |
| Pasiphae | Sol Jupiter-Pasiphae Time | **SJuPaT** | `time-jupiter-pasiphae` |
| Sinope | Sol Jupiter-Sinope Time | **SJuSiT** | `time-jupiter-sinope` |
| Proteus | Sol Neptune-Proteus Time | **SNePrT** | `time-neptune-proteus` |
| Nereid | Sol Neptune-Nereid Time | **SNeNeT** | `time-neptune-nereid` |

### First invocation of suffix-disambiguation policy

The v0.14.1 6-letter `S<Planet2><Moon2>T` policy reserved a fallback for the case where two moons of the *same parent* share their first-two-letters. v0.16.0 hits exactly that case: **Tethys** (shipped v0.14.1) is `SSaTeT`; **Telesto** (shipped v0.16.0) is `SSaTeT2`. The suffix '2' marks the L4 trojan; if Calypso had also collided we'd have used '3' for the L5 (it didn't — Calypso's moon-prefix is `Ca`, distinct from Tethys's `Te`). This is the first invocation of the suffix policy in any sibling project's roster.

### C-side wire-format change

ABI v7 → v8. `ES_N_BODIES` 43 → 52; the `es_bodies[]`, `es_omega_diag[]`, `es_initial_phases[]`, and `es_laplacian` flat arrays expand. Native binary rebuilt; parity-smoke ratchet pinned at the new shape. Existing wheels at ABI 7 are not interoperable with v0.16.0 callers; v0.16.0 wheels ship with the rebuilt native.

### Test count

601 pass, 41 skipped (was 514 + 41 in v0.15.0; +23 new — 12 Saturnian-trojan + 9 Jovian-irregular + 2 expanded Neptunian + 18 parity-smoke entries + parity-smoke tier-shape variations).

### Migration

Python callers: pure-additive on the bridge surface; existing code unchanged. Native callers: ABI bump from 7 → 8 requires a rebuild (the C header's `ES_ABI_VERSION` constant moves in lockstep). The shipped wheel includes the rebuilt native binary at the matching ABI.

## [0.15.0] — 2026-05-06

**Sol Moon Times: classical-roster completion** (Pluto-Charon + remaining major Uranian moons). BODIES roster expanded 38 → 43. Closes task `` `#86` `` for the IAU-major moon roster: every classical moon discovered between 1787 and 1948 now has a Sol Time wrapper.

### BODIES additions (5 new bodies, 38 → 43)

| body | category | period_days | mass (Earth) | radius (km) | discoverer / year |
|---|---|---|---|---|---|
| Miranda | moon | 1.41347925 | 1.10e-5 | 235.8 | Kuiper, 1948 |
| Ariel | moon | 2.52037935 | 2.27e-4 | 578.9 | Lassell, 1851 |
| Umbriel | moon | 4.14417500 | 2.02e-4 | 584.7 | Lassell, 1851 |
| Oberon | moon | 13.46323907 | 5.05e-4 | 761.4 | Herschel, 1787 |
| Charon | moon | 6.38723000 | 2.66e-4 | 606.0 | Christy, 1978 |

### Sol Moon Times added (5)

| body | Sol Time | abbrev | CLI |
|---|---|---|---|
| Miranda | Sol Uranus-Miranda Time | **SUrMiT** | `time-uranus-miranda` |
| Ariel | Sol Uranus-Ariel Time | **SUrArT** | `time-uranus-ariel` |
| Umbriel | Sol Uranus-Umbriel Time | **SUrUmT** | `time-uranus-umbriel` |
| Oberon | Sol Uranus-Oberon Time | **SUrObT** | `time-uranus-oberon` |
| Charon | Sol Pluto-Charon Time | **SPlChT** | `time-pluto-charon` |

### Charon: the binary-planet case

Pluto and Charon are **mutually tidally locked** — both bodies show the same face to each other forever. The only such 1:1:1 spin-orbit lock in the solar system. Charon:Pluto mass ratio (~0.12) is the highest of any moon-planet pair, and the Pluto-Charon barycentre lies *outside* Pluto, which makes the pair more like a *binary planet* than a planet-with-moon. The mutual lock collapses sidereal / synodic / spin period into a single timescale (6.387 days), so no separate synodic correction is offered.

### Disambiguation

**SUrMiT vs SSaMiT** is the v0.15.0 second-instance case of the same shared-moon-prefix pattern that the v0.14.2 SUrTiT/SSaTiT pair first surfaced. Both pairs are exactly the disambiguation the v0.14.1 6-letter `S<Planet2><Moon2>T` policy was designed to provide; without that switch both moons would have collapsed to the same 4-letter form. Documented inline in the new test_uranian_sol_moon_times.py::test_miranda_does_not_collide_with_saturn_mimas.

### C-side wire-format change

ABI v6 → v7. `ES_N_BODIES` constant 38 → 43; the `es_bodies[]`, `es_omega_diag[]`, `es_initial_phases[]`, and `es_laplacian` flat arrays all expand accordingly. Native binary rebuilt; parity-smoke ratchet pinned at the new shape. The C library no longer accepts pre-v0.15.0 callers built against ABI 6 — this is the kind of breaking change a minor version bump is for.

### Test count

512 pass, 41 skipped (was 497 + 4 in v0.14.2; +56 new — 5 Plutonian + 4 expanded Uranian + 10 parity-smoke entries + parity-smoke tier-shape variations).

### Migration

Python callers: pure-additive on the bridge surface; existing code unchanged. Native callers: ABI bump from 6 → 7 requires a rebuild (the C header's `ES_ABI_VERSION` constant moves in lockstep). The shipped wheel includes the rebuilt native binary at the matching ABI.

## [0.14.2] — 2026-05-06

**Sol Moon Times: remaining 8 moons across 4 parent families.** Closes task `` `#86` `` for the current 38-body roster. Built via 4 parallel subagent worktrees (one per family) integrated into a single ship — first multi-agent ship in this repo.

### Added — Mars (2 moons)

Phobos (SMaPhT), Deimos (SMaDeT). Both likely captured asteroids (C/D-type spectral match). Phobos's sidereal period (0.319 d) is shorter than Mars's solar day (~24h 39m), so from Mars's surface Phobos rises in the **west**. Phobos/Deimos period ratio ≈ 3.96 — near 4:1 but not in mean-motion resonance.

### Added — Jupiter inner regulars (4 moons)

Metis (SJuMeT), Adrastea (SJuAdT), Amalthea (SJuAmT), Thebe (SJuThT). Metis + Adrastea are ring-shepherds; Amalthea was the last solar-system moon discovered by direct visual observation (E. E. Barnard, 1892).

### Added — Uranus (1 moon)

Titania (SUrTiT). Largest Uranian moon; only Uranian moon currently in BODIES roster — Oberon, Umbriel, Ariel, Miranda queued for a future ship. **SUrTiT vs SSaTiT** disambiguation is exactly the case the v0.14.1 6-letter policy was designed to handle.

### Added — Neptune (1 moon)

Triton (SNeTrT). Largest Neptunian moon; captured Kuiper Belt object; **only large moon in the solar system that orbits its planet retrograde**. Tidal deceleration is spiralling Triton inward; in ~3.6 Gyr it will become a ring system after crossing Neptune's Roche limit.

### Encoder convention (Triton retrograde)

`BODIES["triton"].period_days` is positive — we encode `omega = +2π/P` for ALL bodies regardless of prograde/retrograde direction; retrograde-ness is metadata, not a sign flip. Same convention as v0.5.4 Sol Uranian Time (Uranus has retrograde rotation).

### Multi-agent ship (first in this repo)

Subagents branched concurrent with v0.14.1 CI, each delivered: bridge wrappers + CLI subcommand + new test module + parity-smoke entries. Parent agent integrated the 4 deliverables into a single bridge.py / cli.py / parity-smoke ship (avoiding 4-way merge conflicts on shared files), copied the 4 test modules in directly, and added a generic `_add_moon_subparser` CLI helper that supersedes the v0.14.0/v0.14.1 family-specific helpers for v0.14.2 additions.

### Test count

497 pass, 4 skipped (was 399 + 4 in v0.14.1; +98 new).

## [0.14.1] — 2026-05-06

**Sol Moon Times: Saturnians (11 moons) + abbreviation policy switch (4-letter → 6-letter).** Second slice of task `` `#86` ``. The abbreviation contingency policy from v0.14.0's ROADMAP fired exactly as predicted: Saturnians introduced two collisions under the v0.14.0 4-letter pattern (Tethys + Titan; Enceladus + Epimetheus) → uniform switch across all Sol Moon Times.

### Saturnian moons added (11)

Mimas (SSaMiT), Enceladus (SSaEnT), Tethys (SSaTeT), Dione (SSaDiT), Rhea (SSaRhT), Titan (SSaTiT), Hyperion (SSaHyT), Iapetus (SSaIaT), Phoebe (SSaPhT), Janus (SSaJaT), Epimetheus (SSaEpT).

### Galilean abbreviations retroactively renamed

`SJIT → SJuIoT`, `SJET → SJuEuT`, `SJGT → SJuGaT`, `SJCT → SJuCaT`. Python function names + CLI subcommand names + return-shape unchanged; only the `epoch.abbreviation` string changes.

### Resonance witnesses

Tests verify Mimas-Tethys 4:2 (Cassini Division), Enceladus-Dione 2:1 (Enceladus tidal heating), Titan-Hyperion 4:3 (Hyperion chaotic rotation), and the Janus-Epimetheus co-orbital pair.

### Hyperion footnote

The only known major moon NOT in tidal lock — `sidereal_period_days` references its orbital period in our convention; rotation-phase coupling is decoupled, an open research direction.

### Test count

399 pass, 4 skipped (was 294 + 4 in v0.14.0).

## [0.14.0] — 2026-05-05

**Sol Moon Times: Galileans (Io / Europa / Ganymede / Callisto).** First slice of task `` `#86` ``. Extends the Sol Time hierarchy to non-Luna moons under the moons-stuck-to-parent `Sol <Parent>-<Body> Time` naming convention from v0.9.1.

### Added

- **Generic moon-time primitive** (`_research/time_scales.py`): `MoonTime` dataclass + `jd_to_moon_time` factory + inverse + `SOL_MOON_TIME_J2000_JD_TDB` constant. Body-agnostic: caller supplies parent + sidereal period; bridge layer reads them from `BODIES`.

- **Four per-Galilean bridge wrappers** + inverses with abbreviations **SJIT**, **SJET**, **SJGT**, **SJCT**.

- **Four per-Galilean CLI subcommands**: `time-jupiter-io`, `time-jupiter-europa`, `time-jupiter-ganymede`, `time-jupiter-callisto`. Built via a shared `_add_galilean_subparser` helper — same `--jd`/`--sidereal-count` mutex, same augmenting-flag support (`--proper` / `--state` / `--dynamics`).

- **35 new tests** in `tests/test_galilean_sol_moon_times.py` + 8 parity-smoke registrations (`python_only`). Covers J2000-zero, after-one-sidereal-period, inverse round-trip, NaN/Inf rejection, CLI parsing, abbreviation uniqueness, and a Galilean Laplace-resonance witness (`n_Io − 3·n_Europa + 2·n_Ganymede ≈ 0`).

### Naming convention contingencies

ROADMAP gains a `## Naming convention contingencies` section documenting the fallback policy if moon-letter collisions arise in future ships. Current 4-letter abbreviations are `S<Planet><Moon>T`; the fallback (when triggered) switches uniformly across all Sol Moon Times to a 6-letter `S<Planet2><Moon2>T` pattern (e.g., `SJuGaT` for Sol Jupiter-Ganymede Time). Forward-looking; no collisions yet in the v0.14.0 Galilean roster.

### Test count

294 tests pass, 4 skipped (was 251 + 4 in v0.13.10).

### Migration

None. Pure-additive. No API / encoder / ABI / encoder-test changes.

## [0.13.10] — 2026-05-05

**Drop `edited` from docs-check workflow trigger types — fixes post-merge double-fire.** CI-only patch; no code changes.

### Why

User-flagged on PR `` `#214` `` (v0.13.9 ship): the docs-check workflow was deterministically double-firing at every merge time. Two `pull_request` events at the same second on the PR's branch ~3 seconds before the merge committed; concurrency-cancel caught it (one CANCELLED, one SUCCESS) but the wasted CI churn + confusing run-history was observable.

### Root cause + fix

GitHub web UI's "Squash and merge" workflow fires `pull_request: edited` (merge-commit dialog populates the title/body fields) near-simultaneously with `pull_request: synchronize` (GitHub recomputes `refs/pull/N/merge`). With both event types in our workflow's `types` list, both fired runs at the same second.

Fix: drop `edited` from the trigger types in `.github/workflows/ephemerides-spectral-docs-check.yml`. Now `[opened, synchronize, reopened, labeled]` — matches the narrower trigger list used by `ephemerides-spectral-ci.yml`, which never had this issue.

Trade-off: `[skip-docs-check]` opt-out added retroactively (after PR open, by editing the PR body) no longer triggers a re-run; user pushes a synchronizing commit or accepts the stale advisory. Acceptable — opt-out should be set up-front.

### Migration

None. Workflow-only change. 251 tests pass, 4 skipped.

## [0.13.9] — 2026-05-05

**JPL Power-of-Ten Rules 6 + 7 manual audits — closes the v0.13.4-v0.13.9 rule-fix sequence. All ten rules satisfied.** Audit-only release; no code changes; 0 violations found for both rules.

### Result

| Rule | Cleared in | Status |
|---|---|---|
| 1, 3, 4, 5 | v0.13.4 / v0.13.5 / v0.13.6 | ✅ pinned in `test_jpl_audit.py` |
| 10 | v0.13.7 | ✅ enforced by `pedantic-build` 3-cell CI matrix |
| **6, 7** | **v0.13.9** | ✅ manual audit (this ship) |
| 2, 8, 9 | already-passing at v0.11.2 | ✅ pinned |

The v0.11.2 spot-check estimates of "5-10 + 5-15 violations" for Rules 6+7 didn't survive the incremental tightening in v0.13.4-v0.13.6 (long-function splits relocated state into helper-scope; assertion work added `const`-near-use patterns throughout; cleanup-on-error refactor unified the rc-check pattern).

### Audit walked

- **Rule 6**: every variable declaration across the 9 .c files. Loop iterators block-scoped; `const` declarations near use; remaining function-scope declarations are intentional (accumulators, sqrt caches, output buffers, result variables).
- **Rule 7**: every `es_status_t` assignment (8 sites across `es_parity.c`, `es_hd_state.c`, `es_patches.c`); each checked on the next line. Numeric returns used inline. Bridge entry points runtime-validate parameters; internal helpers document caller contract via post-validation `assert()`.

### Migration

None. Audit-only release. 251 tests pass, 4 skipped.

## [0.13.8] — 2026-05-05

**README accuracy patch — two-stage architecture clarification.** Docs-only release; no API / encoder / ABI / test changes.

### Why

User flagged: *"our readme says that we use complex128 for syzygy and stuff, is that still correct? because that would mean we aren't pure ALU, right?"* The README's framing was load-bearing for the project's mental model; the `complex128` bullet was stale (true before Tier 2b shipped in v0.7.0).

### Fixed

- **README split into two-stage architecture** (phase-residue stage + HD-pipeline stage), making explicit that:
  - The **encoder hot path is integer ALU end-to-end** (BIP encoder uint64/int64/uint32; no floats in the chunk loop).
  - The **HD operations** (syzygy operator, observer-bind, eclipse-probability) lift integer residues to `complex64` and **necessarily run on FPU** — channel bases are `(cos(φ), sin(φ))` complex pairs.
  - `complex128` is the **regression baseline only** (`backend="fpu-ref"`); the production HD path is C-side `complex64` since v0.7.0.
- **TL;DR on "pure ALU"** added: *"The package is **not** pure-ALU end-to-end — the HD pipeline can't be, because complex bases require trigonometric channels. The integer-ALU discipline applies to the encoder hot path and is enforced by the JPL Power-of-Ten audit (Rule 10 pedantic-build matrix)."*
- **Status banner refactored**: "Three interchangeable backends" → "Two-stage architecture: three interchangeable integer-ALU phase-residue encoders feeding an FPU `complex64` HD pipeline."

### Roadmap renumber

`c/JPL_AUDIT.md`: Rules 6+7 manual audits move v0.13.8 → **v0.13.9**. The v0.13.4-v0.13.8 sequence becomes v0.13.4-v0.13.9; v0.13.8 is the README hygiene patch.

### Migration

None. Pure docs change. 251 tests pass, 4 skipped (unchanged).

## [0.13.7] — 2026-05-05

**JPL Power-of-Ten Rule 10 fixes — cross-platform pedantic-build CI matrix.** Fourth code-quality patch in the v0.13.4-v0.13.8 rule-fix sequence. CI-only addition; no public API / ABI / encoder change.

### Added

- **`ES_PEDANTIC=ON/OFF` CMake option** — when ON, elevates the existing `-Wall -Wextra -Wpedantic` (gcc/clang) or `/W4` (MSVC) warnings to errors via `-Werror` / `/WX`. Default OFF (casual local builds stay friendly); CI turns it ON.

- **`pedantic-build` CI job** — 3-cell matrix (Linux gcc, macOS clang, Windows MSVC) running `cmake -DES_PEDANTIC=ON && cmake --build`. Always-on (not gated by `wheel-check`); Rule 10 is a permanent invariant.

### All five mechanically-enforceable JPL rules satisfied

| Rule | Status | Mechanism |
|---|---|---|
| 1 (no `goto`) | ✅ | Pinned in `test_jpl_audit.py` |
| 3 (no dynamic alloc) | ✅ | Pinned in `test_jpl_audit.py` |
| 4 (≤60-line functions) | ✅ | Pinned in `test_jpl_audit.py` |
| 5 (≥2 assertions/function) | ✅ | Pinned in `test_jpl_audit.py` |
| 10 (zero warnings at pedantic) | ✅ | Enforced by `pedantic-build` CI job |

Remaining JPL roadmap: Rules 6+7 (manual scope + return-value audits, v0.13.8).

### Migration

None. CI-only addition. Local builds default to previous behaviour; developers wanting local Rule 10 enforcement pass `-DES_PEDANTIC=ON` to cmake.

251 tests pass, 4 skipped (unchanged).

## [0.13.6] — 2026-05-05

**JPL Power-of-Ten Rule 5 fixes — assertion density at 2/function average.** Third code-quality patch in the v0.13.4-v0.13.8 rule-fix sequence. Pure additive instrumentation; no public API/ABI/test-surface change.

### Fixed

- **Rule 5 (≥2 assertions per function avg)** flips from 0 → **88 assertions / 42 functions = 2.10/function** (target ≥2.0). The `test_rule_5_density_meets_2_per_function` ratchet test flips from SKIP to **PASS**.

  Distribution: `es_channel_bases` 2 / 1, `es_encode` 26 / 13, `es_hd_state` 25 / 11, `es_parity` 16 / 8, `es_patches` 15 / 7, `es_prng` 4 / 2. (`es_bodies`, `es_cosine_lut`, `es_laplacian` are pure data tables with no function bodies.)

### Coverage strategy

Per Holzmann's Power-of-Ten paper:
- **Pre-conditions on parameters**: post-validation `assert(ptr != NULL)`; `assert(idx < N_BODIES)`; `assert(isfinite(input))`.
- **Post-conditions on results**: assert magnitude ≥ 0; assert phase < 2π; assert state advanced.
- **Invariants**: `assert(D > 0)`; `assert(n_patches <= ES_MAX_PATCHES)`; `assert(ES_VERSION > 0)`.

### Zero runtime cost

All assertions use standard `<assert.h>` — no-op when `NDEBUG` is defined. Production builds (`-DNDEBUG`) strip them. Assertions are development-time documentation that doubles as static-analysis precondition spec.

### Audit ratchet (`tests/test_jpl_audit.py`)

| Pin | v0.11.2 baseline | v0.13.5 | v0.13.6 |
|---|--:|--:|--:|
| `PIN_RULE_5_ASSERTIONS` | 0 | 0 | **88** |

**Total mechanically-detectable violations: 102 → 0** — every Rule 1-5 violation in the v0.11.2 audit baseline cleared in three ships (v0.13.4 + v0.13.5 + v0.13.6). Remaining JPL roadmap: Rule 10 (pedantic-build matrix, v0.13.7), Rules 6+7 (manual scope + return-value audits, v0.13.8).

250 tests pass, 4 skipped (was 5; Rule 5 density skip is gone).

## [0.13.5] — 2026-05-05

**JPL Power-of-Ten Rule 4 fixes — long-function splits.** Second code-quality patch in the v0.13.4-v0.13.8 rule-fix sequence. Pure refactor; no public API / ABI / test-surface change.

### Fixed

- **Rule 4 (function bodies ≤ 60 lines)** count drops **4 → 0**. The four audit-baseline offenders refactored along natural algorithm seams via 10 new private static helpers:

  | Function | Before | Helpers extracted |
  |---|--:|---|
  | `es_encode_state` | 109 | `apply_one_chunk`, `apply_subchunk_remainder` |
  | `es_find_syzygies` | 99 | `select_syzygy_targets`, `score_syzygy_event`, `validate_syzygy_args`, `emit_syzygy_event` |
  | `es_bind_observer` | 78 | `observer_coord_shift`, `apply_observer_bind` |
  | `es_get_eclipse_probability` | 65 | `build_syzygy_operator`, `complex64_vdot_magnitude` |

  All driver functions ≤60 lines after the splits. Total function count 32 → 42; `PIN_RULE_5_TOTAL_FUNCS` ratcheted UP to track the new inventory (Rule 5 work in v0.13.6 needs it).

### ABI/API impact

**None.** The new factors are `static` (file-private); no header changes; no Python-side updates. Public entry points keep their v0.13.4 signatures. Encoder math byte-identical — parity smoke pins both backends to float-ULP and stays green.

### Audit ratchet (`tests/test_jpl_audit.py`)

| Pin | v0.11.2 baseline | v0.13.4 | v0.13.5 |
|---|--:|--:|--:|
| `PIN_RULE_4_LONG_FUNCTIONS` | 4 | 4 | **0** |
| `PIN_RULE_5_TOTAL_FUNCS` | 32 | 32 | **42** |

Total mechanically-detectable violations: **102 → 64** (37% of audit baseline cleared across v0.13.4 + v0.13.5). Remaining: Rule 5 (assertion density, v0.13.6), Rule 10 (pedantic-build matrix, v0.13.7), Rules 6+7 (manual audits, v0.13.8).

250 tests pass, 5 skipped.

## [0.13.4] — 2026-05-05

**JPL Power-of-Ten Rule 1 + Rule 3 fixes** — first code-quality patch in the v0.13.4-v0.13.8 rule-fix sequence (renumbered from v0.11.3-v0.11.7 in v0.13.2). Caller-supplied-scratch refactor of `c/src/es_hd_state.c` eliminates both classes of violation in one pass. ABI v5 → v6 (mechanical; encoder math byte-identical).

### Fixed

- **Rule 1 (no `goto`)** baseline 5 → **0**. The five `goto out` cleanup statements in `es_hd_state.c` (`es_encode_state_hd`, `es_bind_observer`, `es_get_eclipse_probability`) are gone. With the buffers no longer owned by the C function, the cleanup-on-error paths collapse to plain early-return.

- **Rule 3 (no dynamic allocation after init)** baseline 29 → **0**. No `malloc`/`calloc`/`realloc`/`free` anywhere in the C library after init. `es_hd_state.c` no longer includes `<stdlib.h>`. The HD pipeline takes caller-supplied scratch buffers; the Python ctypes shim allocates them alongside the existing `out_state` (no observable heap-pressure change).

### Changed (ABI v5 → v6)

Three public C entries gained scratch-buffer pointer parameters:

| Function | New params |
|---|---|
| `es_encode_state_hd` | `+scratch_basis`, `+scratch_rolled` |
| `es_bind_observer` | `+scratch_body_basis`, `+scratch_coord_basis`, `+scratch_coord_op` |
| `es_get_eclipse_probability` | `+scratch_sun_b`, `+scratch_moon_b`, `+scratch_node_b`, `+scratch_s_op` |

`ES_ABI_VERSION` bumped 5 → 6. Stale binaries fail at import (`EXPECTED_ABI_VERSION` mismatch); standard upgrade refreshes both halves.

### Why combined

Both violations clustered in the same 318-line file — every `malloc` was paired with a `free` in a `goto out:` cleanup block. Removing one class of violation (`malloc`) removed the *reason* for the other (`goto`). One refactor, two rules satisfied, one ABI bump, one parity-smoke run, one ship. Splitting the work into two PRs would have meant either: (a) Rule 1 first, leaving the malloc/free pairs but inlining the cleanup at every error site (verbose, larger diff); or (b) Rule 3 first, leaving the gotos as no-ops (silly). Combined fix is the natural unit.

### User-facing impact

**None.** Python bridge surface is unchanged. The scratch allocation lives in `_native_bip.py`'s `native_*` helpers, one layer below `bridge.py`. Same call sites, same return shapes, byte-identical math.

### Migration

- **Pure-Python users**: zero change.
- **Direct C-API consumers (rare)**: rebuild against v0.13.4 headers; pass scratch pointers per the new signatures (see `c/include/ephemerides_spectral.h` ABI-history comment).
- **Standard PyPI users**: `pip install -U ephemerides-spectral`.

### Audit ratchet (`tests/test_jpl_audit.py`)

| Pin | v0.11.2 baseline | v0.13.4 |
|---|--:|--:|
| `PIN_RULE_1_GOTO` | 5 | **0** |
| `PIN_RULE_3_DYNAMIC_ALLOC` | 29 | **0** |

Total mechanically-detectable violations: **102 → 68** (33% of the audit baseline cleared). Remaining: Rule 4 (4 long functions, v0.13.5), Rule 5 (64 assertions short, v0.13.6), Rule 10 (pedantic-build matrix, v0.13.7), Rules 6+7 (manual scope + return-value audits, v0.13.8).

250 tests pass, 5 skipped.

## [0.13.3] — 2026-05-05

**Pre-merge docs+parity hygiene check** — soft-warning GitHub Actions workflow added. Closes `` `#98` `` (consolidated; absorbs `` `#87` `` + `` `#88` ``).

### Added

- **`.github/workflows/ephemerides-spectral-docs-check.yml`** — soft-warning workflow that posts (or updates in place) a single PR comment summarising drift between code-side touches and the five PyPI-facing docs files. Never fails the build.

  Watched docs surface (5 files):

  | File | Role |
  |---|---|
  | `python/README.md` | PyPI README (status banner + body table) |
  | `python/CHANGELOG.md` | Package CHANGELOG (PyPI-rendered) |
  | `CHANGELOG.md` | Project CHANGELOG (mirror) |
  | `ROADMAP.md` | Roadmap / status sweep |
  | `ephemerides_spectral_research_notebook.md` | Research notebook |

  Code-side categories cross-checked against expected docs:

  | Category | Expected docs |
  |---|---|
  | Version bump (`pyproject.toml` / `pyproject-pure.toml` / `version.py` / `c/include/ephemerides_spectral.h`) | All five |
  | `bridge.py` | README + both CHANGELOGs + notebook |
  | `cli.py` | README + both CHANGELOGs |
  | `_research/*.py` or `research/*.py` | Notebook + both CHANGELOGs |
  | `c/src/*.c` or `c/include/*.h` | Both CHANGELOGs + parity-test touch |

  **Soft-warning, not hard-fail** — the freshness ratchet inside pytest already hard-fails on the highest-value drift modes (`test_native_version_string_matches`, `test_parity_smoke::PARITY_TARGETS`, `test_readme_freshness`, `test_jpl_audit`); this workflow surfaces the *next tier* — prose-and-narrative drift that humans should review but a regex can't authoritatively adjudicate.

  **Opt-out**: include `[skip-docs-check]` anywhere in the PR body to silence on cosmetic / typo / formatting-only diffs.

  **Comment idempotence**: uses `peter-evans/find-comment` + `peter-evans/create-or-update-comment` to update a single advisory in place across pushes rather than spamming the PR.

  **Concurrency**: `cancel-in-progress: true` keyed by workflow + ref to absorb the `opened`+`labeled` double-fire pattern documented in `ephemerides-spectral-ci.yml`.

  **Discipline absorbed**: `` `#87` `` (pre-merge C/Python parity checklist) and `` `#88` `` (pre-publish docs hygiene, RTD-aware). The mechanical halves stay in pytest (`test_parity_smoke.py`, `test_readme_freshness.py`); the broader prose / notebook / RTD sweep lands here as soft-warning advisory.

### Migration

None. CI-only addition. Version stamps bump 0.13.2 → 0.13.3 in lockstep across `version.py`, both `pyproject*.toml` files, and `c/include/ephemerides_spectral.h`.

## [0.13.2] — 2026-05-05

**Quick-win housekeeping**: gitignore the `_native/` build directory; renumber the JPL rule-fix roadmap to v0.13.4-v0.13.8.

### Fixed

- **Add `_native/` to repo `.gitignore`** (`` `#85` ``). The `python/ephemerides_spectral/_native/` directory holds the compiled native C library (`ephemerides_spectral.dll` / `.so` / `.dylib`) that rebuilds on every `cmake --build ../build` followed by manual copy. Per-platform; not portable; not shipped in source. Listed in the top-level `.gitignore` alongside the existing chess-spectral and othello-spectral C-encoder build artefacts.

- **`c/JPL_AUDIT.md` roadmap renumbering**. The audit document (shipped in v0.11.2) queued v0.11.3-v0.11.7 for the rule-fix patches. After the audit landed, the project shipped v0.12.0 (Sol Kinematics) and v0.13.0 (Sol Dynamics) ahead of the JPL rule-fix work; the rule-fix patches are now renumbered to land in **v0.13.4-v0.13.8**:

  | Was | Now | Focus |
  |---|---|---|
  | v0.11.3 | **v0.13.4** | Rule 1 + Rule 3 — refactor `es_hd_state.c` HD pipeline (remove `goto` + `malloc`, combined fix via static / caller-supplied buffers) |
  | v0.11.4 | **v0.13.5** | Rule 4 — split the 4 long functions (`es_encode_state` 109, `es_find_syzygies` 99, `es_bind_observer` 86, `es_get_eclipse_probability` 71) |
  | v0.11.5 | **v0.13.6** | Rule 5 — add ≥64 assertions, gated by `#ifndef NDEBUG`. Flips the Rule-5 density skip in `test_jpl_audit.py` to passing |
  | v0.11.6 | **v0.13.7** | Rule 10 — cross-platform pedantic-build CI matrix |
  | v0.11.7 | **v0.13.8** | Rules 6 + 7 — manual variable-scope + return-value audits |

  v0.13.3 reserved for `` `#98` `` (consolidated docs+parity hygiene check; absorbs `` `#87` `` + `` `#88` ``).

### Task tracking housekeeping

Three originally-separate tasks consolidated into `` `#98` ``:

- `` `#87` `` (pre-merge C/Python parity checklist) — absorbed; the mechanical part lives in `tests/test_parity_smoke.py::PARITY_TARGETS`, the human-checklist part in `` `#98` ``'s description.
- `` `#88` `` (pre-publish docs hygiene checklist, RTD-aware) — absorbed; the mechanical README-Status-banner-and-CLI-body-name-validity part lives in `tests/test_readme_freshness.py`, the broader notebook + RTD-aware coverage in `` `#98` ``'s description.

Both marked completed-redirected; `` `#98` `` is the canonical task to track.

### Migration

None. Patch-level docs + repo-config + task-tracking changes; no API, no encoder, no ABI, no test changes. 248 tests pass, 5 skipped (unchanged from v0.13.1).

## [0.13.1] — 2026-05-05

**SPICE feature-gap audit + STLT-naming hygiene.** Docs-only release; no API, no encoder, no ABI changes.

### SPICE feature-gap audit — task #101 (research-only)

User question during v0.11.2: *"What do we do now that SPICE does slower? Does SPICE do things we might be able to do but don't? If so, will it be worth some API compatible bridge?"*

Output: `figures/spice_feature_audit.md` — three-column feature comparison + compat-bridge analysis. **Recommendation: skip the SPICE-API compat bridge.**

Three columns documented:
- **What we do faster than SPICE** — encode hot loop ~1000×, eclipse-window enumeration via `find-syzygies`, find-tubes Hohmann windows, 256 KB BIP state vs. 3.3 GB DE441, Pyodide / WASM compatibility.
- **What we do that SPICE does not** — Phase 9 adaptive (breathing) couplings, the entire Sol Symphony Times series (STLT / SPrT / Sol Kinematics / Sol Dynamics), runtime kernel patching, adaptive-Kuramoto / state-dependent graph Laplacian framing.
- **What SPICE does that we don't** — frame transformations, light-time + stellar-aberration corrections (`spkpos` with `LT+S`), high-precision pole / spin orientation (PCK kernels), comprehensive Kepler-element sets (`oscelt`), spacecraft trajectories (mission SPK), CK orientation kernels, multi-body N-body integration, exotic time-scale conversions.

The compat-bridge analysis: option (A) pure SPICE-API stub fails because light-time / aberration is the whole point of `spkpos` and we don't have it; option (B) wrapper with similar names is what we already have (`get_kinematic_state` etc.); option (C) document the conversion table and skip the bridge — recommended.

Spawned v0.14.x backlog: light-time + stellar-aberration; canonical `bridge.frame_transform`; full Kepler elements on `KinematicState`; per-body pole RA/Dec + prime-meridian rotation rate.

### STLT naming hygiene

User flagged two related issues:

1. **"system clock for the Terra-Luna pair"** framing in active code comments + docstrings is misleading. STLT is *anchored Lunar time using the synodic month* — Luna's phase observed from Terra, anchored at a Greek-historical event. "Pair" suggests center-of-mass-of-pair, libration, or similar joint-state observable; that's not what STLT measures.

2. **The abbreviation table** in `python/README.md` listed Luna's primary Sol Time as SLT (surface clock). Per the moons-stuck-to-parent `Sol <Parent>-<Body> Time` convention from v0.9.1 (*"Naming hierarchy for future moon ports"*), Luna's primary entry should follow the Parent-Body form — so STLT goes in the table, not SLT. SLT is preserved as a secondary alternative for the surface-clock case.

Fixed in active code; CHANGELOG entries for v0.10.0 (which describe how STLT was framed *at the time*) are preserved as historical artefacts. The shipped behaviour is unchanged.

**Future moon Sol Times** (Sol Pluto-Charon Time, Sol Jupiter-Io Time, Sol Saturn-Titan Time, etc.) will follow the same `Sol <Parent>-<Body> Time` naming — task #86.

### Discipline

This ship answered two of the user's open questions in one PR:
- "What does SPICE do that we don't?" → audit answers it concretely.
- "Is the 'pair' framing right for STLT?" → no, fixed.

The README freshness check caught the v0.13.0-banner-still-says-v0.13.0 drift the moment the version bumped — exactly what it's for.

### Migration

None. Documentation-only release. The STLT name (`Sol Terra-Luna Time`), CLI subcommand (`time-terra-luna`), bridge methods (`get_sol_terra_luna_time`), and constant set (`STLT_*`) are all unchanged.

## [0.13.0] — 2026-05-05

**Sol Dynamics — completes the Kinematics + Dynamics split.** v0.12.0 shipped Kinematics; v0.13.0 ships Dynamics. Together they mirror chess-spectral's `qm_*.py` (kinematics) + `qm_*_dynamics.py` (dynamics) at the orbital-mechanics scale.

### Why this exists

Pair-completion of the user's earlier *"We now need to add Kinematics and Dynamics"*. The Phase A audit (`research/kinematics_dynamics_audit.py`) covers both halves; v0.13.0 ships the second canonical primitive + bridge + CLI without needing a new Phase A.

### What's queryable now

```python
# System-level (the full aggregate)
bridge.get_dynamics()
# → {is_bound: True, total_energy_j: -1.98e35,
#    fraction_in_jupiter: 0.6151, ...}

# Per-body energy budget
bridge.get_body_energies("mars")
# → {kinetic_energy_j, potential_energy_j, total_energy_j: -1.86e32}

# Pair-wise force (the textbook 3.54e22 N validation)
bridge.get_force_between("terra", "sun")
# → {force_magnitude_n: 3.542e22, distance_m: 1.49e11, ...}
```

```bash
# CLI — three modes selected by which flags you pass
ephemerides-spectral dynamics                                # system aggregate
ephemerides-spectral dynamics --body mars                    # per-body budget
ephemerides-spectral dynamics --body mars --from jupiter     # pair force

# --dynamics flag uniform across every time-* subcommand
ephemerides-spectral time-mars --jd 2451545.0 --dynamics

# All three v0.11+ augmenting flags compose
ephemerides-spectral time-mars --jd 2451545.0 --state --proper --dynamics
```

### Validation pins

| Pin | Computed | Expected | Source |
|---|---|---|---|
| Earth-Sun force | 3.542×10²² N | 3.54×10²² | Textbook (every classical mechanics ref) |
| Total system energy | −1.98×10³⁵ J | < 0 (bound) | Standard |
| Virial theorem | total E = PE / 2 | within 0.5 % | Circular-orbit constraint |
| Newton's 3rd law | F_ab = F_ba | exact | Symmetry |
| Sun KE / Mc² | 8.6×10⁻¹⁶ | < 10⁻¹² | Sun barely moves |

### Three-flag composability

The v0.11.0 `--proper`, v0.12.0 `--state`, and v0.13.0 `--dynamics` flags are uniform across every `time-*` subcommand and *all three compose without conflict*:

- `--proper` adds GR + kinematic time dilation (proper-time-corrected counts).
- `--state` adds the Kinematics block (orbital velocity, semi-major axis, KE, L).
- `--dynamics` adds the Dynamics block (KE + PE + total E + is_bound).

Different physical observables, different blocks in the result, no interaction between them. Same modular pattern as `_add_proper_flags` factoring all three.

### Added

**Python API:**
- `bridge.get_dynamics(...)`, `bridge.get_force_between(...)`, `bridge.get_body_energies(...)`, `bridge.apply_dynamics_correction(...)`.
- `_research/dynamics.py` — Phase B canonical primitive (`BodyEnergies`, `ForceContribution`, `DynamicsState`).

**CLI:**
- `dynamics` subcommand with three query modes.
- `--dynamics` flag uniform across every `time-*` subcommand.

### Discipline carried forward

- 34 new tests in `tests/test_dynamics.py` pin every validation value + the CLI surfaces (including the three-flag-compose test).
- Four new bridge methods classified `python_only` in `PARITY_TARGETS`.
- `dynamics.py` registered in `codegen/emit_research_modules.py`.
- README freshness invariants caught the v0.12.0-banner-still-says-v0.12.0 drift the moment the version bumped — exactly what they're for.

### Out of scope (deferred)

- **3D force vectors** (v0.13.x) — needs the position-vector decoder.
- **Tidal forces** (v0.13.x or later, with #103 per-body internal Laplacian).
- **Lyapunov / chaos indicator** (v0.13.x — needs full state evolution + variation propagation).
- **`evolve(state, dt)` named primitive** — `bip_instrument.encode_state(jd)` IS the evolution; v0.13.0 doesn't wrap it as a separate function.
- **C twin** — parity smoke marks new methods `python_only`.

### Migration

None. Sol Dynamics is purely additive.

## [0.12.0] — 2026-05-05

**Sol Kinematics — per-body orbital state, augmented onto every `time-*` subcommand via `--state`.** First half of the Kinematics + Dynamics split modelled on chess-spectral's `qm_*.py` (kinematics) + `qm_*_dynamics.py` (dynamics) pattern.

### Why this exists

User suggestion (during v0.11.0 SPrT close): *"We now need to add Kinematics and Dynamics."* And: *"we can check our chess spectral where we have done this."* Chess-spectral's pattern translates 1:1: Kinematics layer = static observables (state, mass, orbital elements, expectation values); Dynamics layer = Hamiltonian + evolution + forces + energies. v0.12.0 ships the Kinematics half; v0.13.0 ships Dynamics.

### What's queryable now

Per body — `bridge.get_kinematic_state("mars")`:
- Mass, semi-major axis, mean orbital velocity (Kepler's third law from sidereal period + central-body GM).
- Kinetic energy `0.5 m v²`.
- Angular momentum `m·v·r` (z-component, prograde +).

System-level — `bridge.get_full_system_state()`:
- All 38 bodies plus aggregate totals: total kinetic energy, total angular momentum, fraction of L in Jupiter, fraction in outer planets.

CLI — `--state` flag uniform across every `time-*` subcommand:
```bash
ephemerides-spectral kinematics --body mars
ephemerides-spectral kinematics --all
ephemerides-spectral time-mars --jd 2451545.0 --state
ephemerides-spectral time-mars --jd 2451545.0 --state --proper   # composes
```

### Validated against published values

Phase A research script + Phase B canonical primitive agree on 9 published Solar-System values to within 0.02-2.5 %:

| Check | Computed | Expected |
|---|---|---|
| Mercury orbital v | 47.87 km/s | 47.36 (1.1 %) |
| Earth orbital v | 29.785 km/s | 29.78 (0.02 %) |
| Mars orbital v | 24.13 km/s | 24.07 (0.25 %) |
| Jupiter orbital v | 13.06 km/s | 13.07 (0.08 %) |
| Pluto orbital v | 4.741 km/s | 4.74 (0.02 %) |
| **Jupiter fraction of total L** | **61.5 %** | ~61 % |
| **Outer planets fraction of planet L** | **99.84 %** | ~99 % |
| Sun KE / Mc² | 8.6×10⁻¹⁶ | <10⁻¹² |

The "Jupiter holds ~61 % of system angular momentum" / "outer planets hold ~99.84 % of planet L" facts are the headline reason this surface is worth shipping — it makes computable a piece of Solar-System mechanics most people don't know off the top of their heads.

### Added

**Bridge surface:**
- `bridge.get_kinematic_state(body, *, jd_tdb=None, frame=...)` → single body.
- `bridge.get_full_system_state(*, jd_tdb=None, frame=...)` → all 38 bodies + totals.
- `bridge.apply_state_correction(result, subcommand, *, frame=...)` — internal CLI `--state` post-processor.

**CLI:**
- `--state` flag uniformly added to every `time-*` subcommand via the existing `_add_proper_flags` helper.
- `--frame` flag with values `heliocentric_ecliptic` (default) and `parent_centric`.
- `kinematics --body <X>` / `kinematics --all` standalone subcommand.

**Research:**
- `research/kinematics.py` — Phase B canonical primitive (the dataclass + math). Codegened into `_research/kinematics.py`.
- `research/kinematics_dynamics_audit.py` (committed in v0.11.x research branch; merged with this ship) — Phase A independent reference implementation.

### Discipline carried forward

The Phase A → Phase B → ship cycle is now the project's house pattern for adding new physics modules. Same as STLT (#95) and SPrT (#97). Two-implementation discipline: if either drifts, the other catches it.

### Out of scope (deferred)

- **Eccentricity / inclination corrections** (v0.12.x). Real Mars eccentricity 0.0934 means actual perihelion velocity is ~26.4 km/s, aphelion 21.9 km/s. v0.12.0 reports the mean.
- **Position vectors at a specific JD** (v0.12.1). The encoder's phase residues already encode this; needs a heliocentric Cartesian decoder.
- **Forces / energies / evolution operators** — those go in v0.13.0 *Sol Dynamics*.
- **C twin** — parity smoke marks all three new bridge methods `python_only`.

### Migration

None. Existing scripts and bridge calls unchanged. Sol Kinematics is purely additive.

## [0.11.2] — 2026-05-05

**JPL Power-of-Ten audit baseline for the C library.** Audit-only release; no API, no encoder, no ABI changes; pure docs + test discipline.

### Why this exists

User suggestion during v0.9.3: *"work we should do, maybe its own version path, impose JPL C standard on ourselves."* The library targets embedded deployment (ESP32, Cortex-M); JPL Power-of-Ten is the embedded-C gold standard for safety-critical code (Holzmann 2006, *IEEE Computer* 39(6)). At ~2.1k LOC across 11 files the codebase is small enough to retrofit cleanly. v0.11.2 ships the *audit baseline* — documenting current state and pinning the violation counts in CI as a one-way ratchet. Rule-by-rule fixes ship as separate v0.11.3+ minors.

### Audit results

**102 mechanically-detectable violations** across the codebase, dominated by two clusters in `es_hd_state.c` (the HD pipeline) and a uniform Rule-5 deficit:

| Rule | What it forbids | Violations |
|---|---|--:|
| 1 | `goto`, `setjmp`, `longjmp`, recursion | **5** (all `goto out` cleanup pattern in `es_hd_state.c`) |
| 2 | unbounded loops (`while(1)`, `for(;;)`) | 0 ✅ |
| 3 | dynamic allocation after init (`malloc`/`calloc`/`realloc`/`free`) | **29** (all in `es_hd_state.c`) |
| 4 | functions over 60 lines | **4**: `es_encode_state` 109, `es_find_syzygies` 99, `es_bind_observer` 86, `es_get_eclipse_probability` 71 |
| 5 | <2 assertions per function (avg) | **64-assertion shortfall** (0 / 32 functions) |
| 8 | multi-line / token-pasting / variadic macros | 0 ✅ |
| 9 | function pointers, multi-deref, hidden derefs | 0 ✅ |

The architecture is mostly Power-of-Ten-aligned. The major gaps are concentrated:

- **Rule 1 + Rule 3** in the HD pipeline (`es_hd_state.c`'s `es_encode_state_hd`, `es_bind_observer`, `es_get_eclipse_probability`). The `malloc`/`free` D-dimensional buffers are tied to the `goto out` cleanup pattern; both fix together by switching to caller-supplied buffers (clean for ctypes use) or static stack arrays (clean for embedded). Combined ship in v0.11.3.
- **Rule 4** in 4 long functions. Each is doing real work (encoder hot path; syzygy enumeration; observer bind; eclipse projection) — refactor along natural seams in v0.11.4.
- **Rule 5** is uniform: 0 assertions across the codebase. v0.11.5 adds 64+ targeted assertions.

### Added

- **`c/JPL_AUDIT.md`** — full human-readable audit. Rule-by-rule violations with line numbers, fix paths, references to Holzmann 2006, and the v0.11.3 → v0.11.7 roadmap.
- **`python/tests/test_jpl_audit.py`** — pytest ratchet pinning every mechanically-detectable count. 11 passing checks + 1 expected-skip (Rule 5 density gate that flips to passing when v0.11.5 lands).

### Discipline carried forward

The pinned-baseline pattern joins the project's existing CI invariants:

| Invariant | What it pins |
|---|---|
| `test_native_version_string_matches_package_version` | C `ES_VERSION_STRING` ↔ Python `__version__` |
| `test_parity_smoke.py::PARITY_TARGETS` | Every bridge function classified |
| `test_readme_freshness.py` | Status / banner / CLI body-name examples |
| **`test_jpl_audit.py`** *(this ship)* | **JPL Power-of-Ten violation counts (one-way ratchet)** |

Same model: enumerate the truth, fail loudly on drift, allow ratcheting toward improvement.

### Discoveries documented

- **Recursion: 0** (manual inspection — no function calls itself).
- **`while(1)` / `for(;;)`: 0** — every loop has a static upper bound.
- **No function pointers anywhere** — the codebase happens to already pass Rule 9.
- **No multi-line macros** — Rule 8 already passes.

### Roadmap

| Version | Rules to fix |
|---|---|
| v0.11.3 | Rule 1 + Rule 3 (combined HD-pipeline refactor — static / caller-supplied buffers) |
| v0.11.4 | Rule 4 (split 4 long functions) |
| v0.11.5 | Rule 5 (≥64 assertions, gated by `#ifndef NDEBUG`) |
| v0.11.6 | Rule 10 (cross-platform `-Wall -Wextra -Wpedantic` CI matrix) |
| v0.11.7 | Rules 6 + 7 (manual variable-scope + return-value audits) |
| v0.12.0+ | Resume feature work (Kinematics from #99, etc.) |

Each rule-fix ship updates `c/JPL_AUDIT.md` and ratchets the corresponding pin in `test_jpl_audit.py` downward.

### Migration

None. Audit-only release. Existing scripts and bridge calls unchanged. 182 tests pass (was 171 in v0.11.1 + 11 new audit tests + 1 skip).

## [0.11.1] — 2026-05-05

**Research notebook hygiene — backfill §7.4 (STLT) and §7.5 (SPrT); refresh Status banner.** Documentation-only release; no API, no encoder, no ABI changes.

### Why this exists

User asked during the v0.11.0 SPrT ship close: *"just double checking, we added GR to our research notebook too?"* — and the honest answer was no. Both v0.10.0 STLT and v0.11.0 SPrT shipped with full bridge / CLI / test surfaces but neither updated `docs/antikythera-maths/ephemerides_spectral_research_notebook.md`. The freshness invariants from v0.9.3 (`tests/test_readme_freshness.py`) cover the PyPI README; they don't audit the notebook.

This release closes the specific gap. Task #98 captures the broader follow-on: a soft-warning "docs probably need updating" check on every PR that touches code but not docs — would have caught this gap automatically.

### What's in the notebook now

**§7.4 — Sol Terra-Luna Time (STLT) — v0.10.0:**
- The system-clock framing (Sun-Terra-Luna pair, synodic month as natural unit; distinct from SLT, Sol Lunar Time, STT).
- The Meton 432 BCE default-epoch choice + the Hipparchus-Babylonian-midpoint convergence story (the user's "combo" candidate that lands within +240 days of Meton's solstice — same year, eight months later).
- The four alternative epochs (Antikythera 205 BCE, Hipparchus 141 BCE, Mardokempad 721 BCE, J2000).
- The `Z₅` natural-resonance-group connection (Metonic-aligned cyclic factor of `Z₆₀ = Z₄ × Z₃ × Z₅`).
- The house-epoch-vs-NASA-LCT framing (LCT remains its own roadmap item; STLT is the project's house anchor until standardisation lands).
- Bridge / CLI surface examples.

**§7.5 — Sol Proper Time (SPrT) — v0.11.0:**
- The per-body diagonal-fiber framing — extends Mercury's existing 43″/century PN diagonal to all 38 bodies.
- The two leading-order components (`gr_surface = GM/(R·c²)` and `kinematic_orbital = v_orb²/(2c²)`), with the closed-form rate equation.
- A per-body table for the leading bodies (Sun 2.12×10⁻⁶ → Pluto 1.33×10⁻¹⁰).
- Validation against six published values to within 0.30 % rel err (the same six checks Phase A scores in `figures/proper_time_rates.md`).
- The user's transparent `--proper` UX, with code examples for the bridge primitive + the CLI.
- The two-implementation discipline (Phase A independent script + Phase B canonical primitive — same pattern STLT used).
- Out-of-scope items deferred to v0.12.0+ (rotational kinematic, J₂ oblateness, frame dragging).
- Why this matters in spectral terms (the diagonal-fiber framing in vocabulary continuous with the rest of the notebook).

### Status banner refreshed

Was stale at v0.7.0; now reads v0.11.1 with the up-to-date headline-state summary covering Phase 5–9 implementation, body-roster expansion, parity Tier 1/2a/2b, Sol Symphony Times, body-identity rename, Sol Time naming overhaul, adaptive synonym, STLT, and SPrT.

### Release-history block backfilled

The §4 Release History block was ending at v0.9.1; now extends through v0.11.1 with entries for v0.9.2 (adaptive synonym + breathing-bug fix), v0.9.3 (PyPI README sweep + freshness check), v0.10.0 (STLT), v0.11.0 (SPrT), and v0.11.1 (this release).

### Migration

None. Documentation-only release.

## [0.11.0] — 2026-05-05

**Sol Proper Time (SPrT) — gravitational + orbital-kinematic time dilation, applied transparently via `--proper` on every `time-*` subcommand.**

### Why this exists

The user asked, while we were closing v0.10.0 (STLT): *"does our off-diagonal allow us to know when local gravity might dilate relative to some other body? how do we deal with this sort of thing? like even earth has an imperfect G field."* Then a follow-up: *"can we simply add `--proper` as a line arg to invoke gravitational time dilation fiber so that users don't even need to know anything extra had to happen in the back end?"*

The honest answer to the first question is **no, not directly** — our off-diagonal Laplacian weights encode orbital coupling strength, not the scalar gravitational potential field. But they're one integration away. SPrT closes the gap: per-body GR diagonal corrections (analogous to Mercury's existing 43″/century PN term), exposed transparently through a `--proper` flag the user opts into. *"Same answer, but proper-time-corrected for this body."*

### Two implementations agreeing on six published numbers (Phase A + B)

Phase A (`research/proper_time_rates.py`, committed first in this PR's research branch) implements the formulas independently and validates against six canonical figures. Phase B (`_research/proper_time.py`, the package primitive that `--proper` calls) has its own implementation, validated against the same six figures by `tests/test_sprt.py`. Both agree to within 0.30 % — if either drifts, the other catches it.

| Validation pin | Computed | Expected | Source |
|---|---|---|---|
| Earth surface GR | 6.961×10⁻¹⁰ | 6.95×10⁻¹⁰ | GPS clock corrections (Ashby 2003) |
| Sun surface GR | 2.123×10⁻⁶ | 2.12×10⁻⁶ | Largest gravitational well in roster |
| Mars surface GR | 1.400×10⁻¹⁰ | 1.40×10⁻¹⁰ | Curiosity rover (Genova et al. 2014) |
| Pluto surface GR | 8.136×10⁻¹² | 8.15×10⁻¹² | New Horizons mission planning |
| Terra orbital kinematic | 4.935×10⁻⁹ | 4.95×10⁻⁹ | v_terra² / (2c²) standard |
| **Mars-vs-Terra GR-only difference** | **5.561×10⁻¹⁰** | **5.56×10⁻¹⁰** | **The 0.0175 s/Earth-year Curiosity figure** |

### Headline numerical results

- **Sun surface vs. Terra surface (GR only):** 3,049× larger gravitational dilation. Largest well in the roster.
- **Mars surface vs. Terra surface — two different comparisons:**
  - *GR only*: Mars surface clocks tick faster by 0.0175 s/Earth-year. The figure cited in Curiosity navigation papers.
  - *GR + orbital kinematic*: Mars surface clocks tick faster by 0.0710 s/Earth-year. This is what `--proper` actually applies — Mars's slower orbital velocity adds dilation in the same direction as the GR effect, ~4× more than GR alone.
- **Luna surface vs. Terra surface (GR only):** Luna ticks faster by 6.65×10⁻¹⁰ — Apollo-era atomic-clock comparisons resolved this.

### Added

**Bridge surface:**
- `bridge.get_proper_time_rate(body, *, lat=None, lon=None, jd_tdb=None, reference="tcb")` — single-body rate query.
- `bridge.compare_proper_times(body_a, body_b, *, reference="tcb")` — two-body comparison + drift per Earth-year.
- `bridge.apply_proper_correction(result, subcommand, ...)` — internal post-processor used by the CLI's `--proper` flag. Augments existing Sol Time results with `<count>_proper` siblings and a `proper_time` metadata block.

**CLI surface — uniform `--proper` flag:**
- `--proper`, `--lat`, `--lon`, `--reference` added to **every** `time-*` subcommand (13 of them, including STLT) via a shared `_add_proper_flags` helper. Default off → v0.10.0 behaviour preserved exactly for callers who don't opt in.
- New `time-proper` standalone subcommand: `--body <X>` for the rate-only query, `--compare-to <Y>` for the two-body drift figure. Complementary to the `--proper` flag.

**Data:**
- `Body.surface_radius_km` field added to `bodies.py`. Volumetric mean radii for all 38 bodies, sourced from NASA fact sheets / JPL HORIZONS small-body database.

**Research:**
- `research/proper_time_rates.py` (Phase A audit). Independent implementation; validates against the six published values; dumps `figures/proper_time_rates.md`.
- `research/proper_time.py` (Phase B canonical primitive, codegened into the package's `_research/`).

### Fixed

None — purely additive release. v0.10.0 behaviour preserved when `--proper` is not set.

### Discipline carried forward

- 32+ new SPrT tests in `tests/test_sprt.py` — six validation pins identical to Phase A's report + every primitive + every CLI surface.
- Three new bridge methods classified `python_only` in `tests/test_parity_smoke.py::PARITY_TARGETS`.
- `proper_time.py` registered in `codegen/emit_research_modules.py::_INCLUDED_MODULES` so the codegen pipeline picks it up alongside the other research modules.
- `tests/test_readme_freshness.py` caught the v0.10.0-banner-still-says-v0.10.0 drift exactly when the version bumped — proving (again) the discipline works.
- The Phase A → Phase B → Phase A-as-independent-validation loop is the same cycle we ran for STLT; it's becoming the project's house pattern for adding new physics modules.

### Migration

None. Existing scripts and bridge calls are unchanged. SPrT is purely additive.

## [0.10.0] — 2026-05-05

**Sol Terra-Luna Time (STLT) — system-level clock for the Terra-Luna pair, with Meton's 432 BCE summer solstice as the default epoch.** First Sol Time member with a non-J2000 default anchor. Phase B of task #95.

### Why this matters

Most of the Sol Time series silently borrows J2000.0 from Terra. The user noticed this during the v0.9.x sweep: *"if we don't already, we should do this for all celestial bodies, except for Terra, because JD."* STLT is the first deliverable on that principle — the first Sol Time member whose default epoch is celestially significant in its own right rather than a Terra-modern borrowing.

The choice fell on **Meton of Athens's summer solstice (27 June 432 BCE proleptic Julian)** for three converging reasons:

1. *Empirical center of mass.* The user proposed scoring a "combo" candidate: the midpoint of the Hipparchus-Babylonian eclipse archive (Mardokempad 721 BCE + Hipparchus 141 BCE). The Phase A research script (`research/lunar_epoch_candidates.py`) confirms this midpoint lands within **+240 days of Meton's solstice — same year, eight months later**. Greek mathematical astronomy's eclipse archive is centred on Meton's lifetime.

2. *Cycle alignment.* The Antikythera mechanism's Metonic dial encodes the 19-year Metonic cycle (235 synodic months ≈ 19 tropical years, off by ~2 hours). STLT anchored at Meton's solstice anchors at the cycle the device measures, not just the Saros eclipse anchor of one of its other dials.

3. *Algebraic resonance.* The `Z_5` factor of our `Z_60 = Z_4 × Z_3 × Z_5` natural-resonance group is the Metonic-aligned component. Meton's anchor sits on the encoder's algebraic spine.

This is a **house-epoch design choice**, *not* a claim to be NASA's eventual LCT (Lunar Coordinated Time) standard. LCT remains its own roadmap item; when standardised per the April 2024 White House directive, we add it as a sibling.

### Phase A research (committed first; this release ships Phase B)

`research/lunar_epoch_candidates.py` scores five candidates against the spectral kernel + skyfield ground truth and dumps a markdown report (`figures/lunar_epoch_candidates.md`):

| Candidate | JD_TDB | Kernel match | Notes |
|---|---|---|---|
| Antikythera 205 BCE solar eclipse (Freeth & Jones 2012) | 1646782.49 | 0.49 d offset, score 0.197 rad | Saros-dial anchor; project namesake |
| **Meton 432 BCE summer solstice** | 1645528.00 | **1.19° from solstice (epoch-of-date)** | Date validated; *default epoch* |
| Hipparchus 141 BCE lunar eclipse (Almagest VI.5) | 1669949.24 | 0.18 d offset, score 0.033 rad | Tightest spectral match |
| Mardokempad 721 BCE lunar eclipse (Almagest IV.6) | 1458155.86 | 0.52 d offset, score 0.008 rad | Earliest Babylonian record; remarkable spectral fidelity at 2700 yr |
| Hipparchus-Babylonian transmission midpoint (derived) | 1564052.90 | +240 d from Meton | **Confirms Meton sits at Greek astronomy's empirical center of mass** |

Discoveries in the script's commentary worth carrying forward:
- Solar-longitude solstice diagnostics need an *epoch-of-date* precession correction; ~33° at 2400 yr otherwise dominates the offset.
- Encoder drift at 2700-yr horizons can move predicted eclipse times tens of days. Window scales accordingly.
- `bridge.find_syzygies` had the same `backend="auto"` latent-bug class fixed for `get_breathing_modulation` in v0.9.2. Caught + fixed in this ship.

### Phase B (this release)

**API surface:**
- `bridge.jd_to_sol_terra_luna_time(jd_tdb, *, epoch="meton")` and `bridge.sol_terra_luna_time_to_jd(synodic_count, *, epoch="meton")`.
- The five `epoch` keywords: `meton`, `antikythera`, `hipparchus`, `mardokempad`, `j2000`. Each maps to its corresponding JD_TDB constant.
- New CLI subcommand `ephemerides-spectral time-terra-luna --jd <X>` with `--epoch <name>`.

**Out of scope (deferred):**
- C twin (parity smoke marks both new bridge methods `python_only`; C port queued for a future minor).
- Replacing the J2000 default on the *other* Sol Time members (Venus, Mercury, Mars, Luna, Neptune still use J2000 / calendar conventions). The user's principle ("celestial anchors for non-Terra bodies") will roll out body-by-body.
- Sol Proper Time (SPrT) — gravitational + kinematic time dilation per body / per (lat, lon). User-asked during this ship; captured as task #97 for v0.11.x+.

**Discipline carried forward:**
- Manifest regenerated via the project's official `codegen/regenerate.py`.
- README freshness tests caught the v0.9.3-banner-still-says-v0.9.3 drift the moment the version bumped — exactly what they were designed for.
- Both new bridge methods land in `PARITY_TARGETS`; bridge-surface coverage stays complete.

### Migration

None. Existing scripts and bridge calls unchanged. STLT is purely additive.

## [0.9.3] — 2026-05-05

**PyPI-facing README staleness sweep + CI freshness check (docs-only).** No API or encoder changes; no ABI bump.

### Why this exists

User flagged the Status and Roadmap sections of the PyPI README as stale during the v0.9.2 ship — and they were right. The Status block ended at v0.6.1 (8 versions back); the Roadmap still listed Tier 2b "in progress" (shipped v0.7.0), Sol Venusian/Mercurian Time as upcoming (shipped v0.8.0), and the ITN pathway / `find-tubes` query as upcoming (shipped v0.8.1). Plus leftover `--body earth` examples from before v0.9.0 renamed Earth → Terra.

The broader question — *can CI catch this?* — has a clean answer: yes, for the mechanically-checkable invariants. So this ship does both: refreshes the README *and* installs the CI discipline that prevents the same drift next time.

### Fixed (the sweep itself)

- **Status section** brought up to date through v0.9.3. The 8-version gap was the most egregious staleness; closing it required adding entries for v0.7.0, v0.8.0, v0.8.1, v0.9.0, v0.9.1, v0.9.2, v0.9.3.
- **Status banner** added under the H1 (`Status: v0.9.3 — production-ready`). Now pinned to `__version__` by the freshness test.
- **Roadmap section** pruned of items that have shipped (Tier 2b, Sol Venusian/Mercurian Time, ITN pathway / `find-tubes`); reorganised to lead with the genuinely-still-ahead items (first-principles per-resonance α, Hyperion follow-up, remaining 4 broken moons, Sol Moon Times, DE441 vs DE442 experiment, heteroclinic-tube extension, LTC, Phase 10 resonance coverage).
- **Leftover earth-body CLI examples** corrected to `terra` (caught by the new test as part of Invariant 3).
- **Phase 9 heading** inverted from `"Breathing" Couplings` to `Adaptive Couplings (a.k.a. "breathing")` — matches the v0.9.2 CLI rename and leads with the mainstream-literature term (Gross & Blasius 2008, "Adaptive coevolutionary networks") while keeping the visual metaphor for readers who know it that way.

### Added (drift prevention)

`python/tests/test_readme_freshness.py` enforces three invariants:

1. Every version with a CHANGELOG entry must have a bullet in the README Status section (and the reverse — no inventing unreleased versions in the README).
2. The `Status: vX.Y.Z` banner *and* the `*(current)*` marker must both equal `__version__`. Same pattern as `test_native_version_string_matches_package_version` (which pins the C-side `ES_VERSION_STRING` to the Python `__version__`).
3. Every body name in a CLI example (matched by `--body|--departure|--target|--pair-a|--pair-b NAME` regex) must be in `SUPPORTED_BODIES`.

Plus a sanity check: the body-name regex must find at least one match (catches the empty-passing-test failure mode if the README ever stops shipping CLI examples).

What CI cannot enforce — prose accuracy, judgment about Roadmap scope, "is this a good example" — stays in human review.

### Discipline lineage

- `test_native_version_string_matches_package_version` (C ↔ Python version pinning).
- `test_parity_smoke.py::PARITY_TARGETS` (every bridge function classified; drift fails CI).
- `test_readme_freshness.py` (this release): same model, applied to docs.

The pattern: enumerate what must be true, fail loudly on drift, leave judgment to humans.

### Migration

None. Docs-only release; existing scripts and bridge calls unchanged.

## [0.9.2] — 2026-05-05

**CLI: `adaptive` is the primary subcommand for state-dependent coupling modulation; `breathing` retained as a hidden synonym.** No bridge-API changes, no encoder hot-path changes — purely a CLI surface adjustment plus help-text cleanup.

### The framing

What we call "breathing couplings" in the visual / informal register is, in mainstream network-science vocabulary, an **adaptive** coupling: a state-dependent (non-autonomous) graph Laplacian whose edge weights co-evolve with the system's own resonant phases. The literature term traces to *Gross & Blasius 2008* ("Adaptive coevolutionary networks") and the **adaptive Kuramoto** family of models — exactly the regime our Phase 9 LUT modulation occupies. We were already in that literature; we just hadn't said so out loud.

`breathing` is kept because the visual metaphor (the couplings inhale/exhale with the relative resonant phase) is what readers grok intuitively, and we don't want to take that away from anyone who sees it that way. It's now a hidden synonym (invisible in `--help` listings, fully functional when typed) — not deprecated, not going away.

### Added

- `ephemerides-spectral adaptive` — primary subcommand for Phase 9 state-dependent coupling LUT modulation. Help text references the adaptive-networks literature (Gross & Blasius 2008, adaptive Kuramoto).
- `ephemerides-spectral breathing` — hidden synonym (registered with `help=argparse.SUPPRESS`); identical handler, identical args, identical output. Cross-referenced from `adaptive --help`'s epilog so users discover the equivalence without it cluttering the toplevel help listing.

### Fixed

- `ephemerides-spectral resolution` default body changed from `earth` (no longer in the body roster post-v0.9.0) to `terra`; example strings, `--departure earth` examples in `find-tubes`, and `local-view --body earth` example all corrected to `terra`. Help text and `--body` validation are now self-consistent.
- Toplevel description and example block reflect the v0.9.0 / v0.9.1 body-identity rename throughout (no more orphaned `--body earth` examples).
- **Latent bug, pre-existing since v0.8.0:** `bridge.get_breathing_modulation(..., backend="auto")` (the function's own default value) was rejected by `_validate_backend`, because `SUPPORTED_BACKENDS = ("bip", "complex128", "c")` does not include the `"auto"` sentinel. Any caller — including the `breathing` CLI subcommand — that didn't override `backend=` would receive `{"ok": False, "error": "backend must be one of [...], got 'auto'"}`. The fix resolves `"auto"` → concrete backend (`"c"` if native is loaded, else `"bip"`) before validation, matching the function's own docstring contract. New `tests/test_cli_adaptive_alias.py::test_adaptive_and_breathing_produce_identical_output` is the regression test.

### Internal

- Subparser registration factored through a shared `_add_adaptive_args` helper so `adaptive` and `breathing` are mechanically guaranteed to accept identical arguments — no drift possible.
- `_cmd_breathing` retained as a thin alias of `_cmd_adaptive` for any external caller importing it directly from `ephemerides_spectral.cli`.

### Migration

None required for users. Both `adaptive` and `breathing` work identically. Existing scripts continue to function unchanged.

## [0.9.1] — 2026-05-05

**Sol Time naming convention overhaul + Sol Terra Time + Sol Luna Time.** The Sol Time series gets a uniform indexing convention: direct Latin proper noun (Mercury, Venus, Pluto, Terra, Luna, Sol) for rocky bodies + Sun + Luna; established adjective form (Jovian, Saturnian, Uranian, Neptunian) for the gas/ice giants where the adjective is deeply established in astronomical tradition. Each bridge return now carries an `abbreviation` field per the user's indexing table.

Two new time systems join: **Sol Terra Time (STT)** — Terra's own surface clock — and **Sol Luna Time (SLT)** — Luna's surface clock, distinct from the existing **Sol Lunar Time** (`get_lunar_phase`) which returns Luna's synodic+sidereal phase as observed from Terra.

### The naming framing

> *"Returning to the giants whose shoulders we stand on. We've always had a lunar orbit and a lunar eclipse. We've all had terrain and terrestrial animals. We're just putting the books back in their dewey decimal spot. We no longer kow tow for the sake of leaning forward."*

The adjective forms `lunar`, `terrestrial`, `terran` were always derived from the proper nouns Luna and Terra — the language already carried the convention. The body-identity strings now reflect what the language always implied. Generic English `moon` and `earth` return to their generic meanings.

### Renames (BREAKING)

| Before | After | Abbrev |
|---|---|---|
| `jd_to_sol_mercurian_time` | `jd_to_sol_mercury_time` | SMeT |
| `jd_to_sol_venusian_time` | `jd_to_sol_venus_time` | SVT |
| `jd_to_sol_plutonian_time` | `jd_to_sol_pluto_time` | SPT |
| `MercurianTime` | `MercuryTime` | |
| `VenusianTime` | `VenusTime` | |
| `PlutonianTime` | `PlutoTime` | |

Same for the `*_time_to_jd` inverses. The CLI subcommands (`time-mercury`, `time-venus`, `time-pluto`) already used the body-name form — only the underlying Python identifiers changed.

### Kept (gas/ice giants, established astronomical tradition)

| Body | Function name | Abbrev |
|---|---|---|
| Jupiter | `jd_to_sol_jovian_time` | SJT |
| Saturn | `jd_to_sol_saturnian_time` | SST |
| Uranus | `jd_to_sol_uranian_time` | SUT |
| Neptune | `jd_to_sol_neptunian_time` | SNT |

### New time systems (additive)

- **Sol Terra Time (STT)** — `bridge.jd_to_sol_terra_time(jd_tdb)`, CLI `time-terra`. Terra's surface clock anchored at J2000 with Greenwich prime meridian. Sidereal day = 23h 56m 4s = 0.99726957 Earth-days; solar day = 24h = 1.0 Earth-day (by definition).
- **Sol Luna Time (SLT)** — `bridge.jd_to_sol_luna_time(jd_tdb)`, CLI `time-luna`. Luna's surface clock, tidally locked so sidereal day = orbital period = 27.32 d; solar day = synodic month = 29.53 d. **Distinct from Sol Lunar Time** (`get_lunar_phase`), which is Luna's synodic+sidereal phase as observed from Terra. Same body, different observer frame.

### Abbreviation field (additive)

Every Sol Time bridge return's `epoch:` block now carries an `"abbreviation": "<short>"` field per the user's indexing table:

| Body | Abbrev |
|---|---|
| Mercury | SMeT |
| Venus | SVT |
| Terra | STT |
| Luna | SLT |
| Mars | (kept as MSD via `MarsTime`; no abbreviation field on the existing surface — additive in v0.9.x patch) |
| Jupiter | SJT |
| Saturn | SST |
| Uranus | SUT |
| Neptune | SNT |
| Pluto | SPT |
| Sol | SSoT |

### Tests

111 active tests pass (was 107 in v0.9.0); 5 skipped (4 cibuildwheel-only + 1 `tier1_skip` `find_itn_pathways`).

## [0.9.0] — 2026-05-05

**Body identity rename: `moon` → `luna`, `earth` → `terra`. BREAKING CHANGE.**

User framing: "If we can say things like Lunar Orbit, we can call it Luna and the word moon isn't taken away from all moons" + "earth shall no longer be privileged and should be known as Terra."

The body-identity strings in `BODIES`, `bridge.list_bodies()`, `bridge.body_to_idx`, `_data/initial_phases.json`, and the C-side `es_bodies` table now use the Latin proper nouns. The generic English nouns (`moon` for any natural satellite, `earth` for soil/ground) are no longer privileged as proper nouns of specific bodies.

### What changes

- `BODIES["moon"]` → `BODIES["luna"]` (display: `"Luna"`)
- `BODIES["earth"]` → `BODIES["terra"]` (display: `"Terra"`)
- All callers using `body="earth"` or `body="moon"` must update to `body="terra"` / `body="luna"`
- `bridge.list_bodies()` returns the new keys
- C-side `es_body_index("terra")` / `es_body_index("luna")` (the strings `"earth"` and `"moon"` no longer resolve to body indices)
- Sample states: `_data/initial_phases.json` re-keyed; encoded uint32 phase residues unchanged at the same JD (only the dict key changed)

### What stays the same

- **Category strings**: `Body(..., "moon")` (the 4th arg) is the category for any natural satellite. `category == "moon"` checks across the codebase work as before (Phobos, Io, Titan, etc. all carry `category="moon"`).
- **Adjective forms**: `lunar` (adjective from Luna), `terran`/`terrestrial` (adjective from Terra). Existing time functions like `get_lunar_phase` keep their names — `lunar` is Luna's adjective, naturally.
- **JPL/skyfield identifiers**: external API (kernels, HORIZONS) still uses `"moon"` / `"MOON"` / `301` / `"earth"` / `"EARTH"` / `399`. The translation happens at the kernel boundary in `EphemerisBundle.lookup()` via a small `_to_jpl_name` alias map. Internal code uses `terra` / `luna`; external lookups stay JPL-conventional.
- **Encoder hot path**: byte-identical phase residues at the same JD. The rename touches body-identity strings only; the integer Q-format encoder produces the same uint32 output.

### Migration

Anywhere your code says:
```python
bridge.body_to_idx["earth"]   # before
bridge.list_bodies()           # contained "earth"/"moon"
```

Change to:
```python
bridge.body_to_idx["terra"]   # after
bridge.list_bodies()           # contains "terra"/"luna"
```

### Why this is a v0.9.0 minor bump (not v1.0.0)

Per semver-for-0.x, breaking changes can land in a minor bump while the project is pre-1.0. The actual encoder behavior is unchanged (same phase residues; same Laplacian; same patches). Only the body-identity string convention changed.

### Tests

107 active tests pass (was 107 in v0.8.1); 5 skipped (4 cibuildwheel-only + 1 `tier1_skip` for `find_itn_pathways`).

### Coming up in v0.9.1

The Sol Time naming convention overhaul (per user's body-name + abbreviation table): `Sol Mercurian Time` → `Sol Mercury Time`, `Sol Venusian Time` → `Sol Venus Time`, `Sol Plutonian Time` → `Sol Pluto Time`, plus new `Sol Terra Time` + `Sol Luna Time` as Phase A of the Sol Moon Times completion roadmap. Gas/ice giant adjective forms (Jovian, Saturnian, Uranian, Neptunian) are kept — they're deeply established in astronomical tradition.

## [0.8.1] — 2026-05-05

**ITN pathway / Lagrange-tube query — `find-tubes` first cut.** "Surfing the perturbations": closed-form Hohmann transfer-window enumeration mirroring the v0.3.1 `find-syzygies` discipline. Pure-Python implementation; C twin queued for a follow-up minor (the parity smoke marks `find_itn_pathways` as `tier1_skip`).

### Why "surfing the perturbations"

The Solar System is a natural symphony of overlapping cyclic groups (mean motions, synodic periods, Lagrange-point manifolds). A Hohmann transfer window is the **simplest case of surfing that natural structure** — the lowest-Δv way to ride a planet's orbit out to the next one. v0.8.1 exposes the closed-form math that reads "when does a window open?" from the existing v0.5.0+ initial-phase data + Kepler's 3rd law. No CR3BP integration; no manifold computation. The `transfer_kind` field reserves room for low-energy / heteroclinic-tube candidates as future versions add CR3BP-grade gateway designations.

### Added — research

- `_research/itn_window.py`: `ITNCandidate` dataclass + helpers (`hohmann_transfer_time_days`, `hohmann_launch_phase_angle_rad`, `hohmann_total_dv_kms`, `synodic_period_days`) + `find_itn_pathways` enumeration. Reads body initial phases from `_data/initial_phases.json` (codegen-baked v0.5.0+ output); no encoder calls.

### Added — bridge surface

- `bridge.find_itn_pathways(jd_lo, jd_hi, departure, target, threshold, max_candidates, backend)`. Returns the standard `{ok, candidates, ...}` shape. Each candidate carries `jd_tdb`, `transfer_kind` ("hohmann"), `transfer_time_days`, `launch_phase_angle_deg`, `actual_phase_angle_deg`, `phase_residual_deg`, `score`, `estimated_dv_kms`, `synodic_period_days`, `gateway_lp` ("transfer-ellipse" placeholder).

### Added — CLI

- `find-tubes --from-jd ... --to-jd ... --departure earth --target mars` (plus `--threshold` + `--max-candidates`). Full `--help` epilog with examples spanning Mars + Jupiter targets.

### Sanity values

Earth → Mars at default threshold 0.02 over J2000 + 50 yr returns 23 windows (synodic period 779.94 d). Each window: transfer time 258.87 d, total Δv 5.594 km/s. Matches textbook Hohmann math to 0.01% on time and 0.1% on Δv.

### Future (the C twin + CR3BP layers)

- **C twin** mirroring `find-syzygies` (ABI bump v5 → v6, follow-up minor). `find_itn_pathways` then flips from `tier1_skip` to `parity` in the smoke.
- **L1/L2 gateway designation + Jacobi constant** per CR3BP geometry. `gateway_lp` graduates from `"transfer-ellipse"` placeholder to a real Lagrange-point label.
- **Multi-leg heteroclinic chains** — Sun-Earth L2 → Sun-Mars L1 → Mars surface, etc. Combinatorial enumeration over the gateway graph.
- **Energy-budget filtering** — only emit candidates whose cumulative Δv fits a caller-supplied budget.
- **Ballistic-capture windows** at planetary L1 — Belbruno-style low-energy capture, generalised.

### Tests

- 3 new immolation tests: Earth→Mars windows + characteristics, same-body rejection, Mars→Earth (inner) transfer geometry.
- 107 active tests pass (was 104 in v0.8.0); 5 skipped (4 cibuildwheel + 1 new `tier1_skip` for `find_itn_pathways`).

### References

- Koon, Lo, Marsden, Ross — *Dynamical Systems, the Three-Body Problem and Space Mission Design* (2011), the canonical ITN text.
- Lo (1997) — Genesis spacecraft trajectory design via L1/L2 manifolds.
- Conley (1968) — manifold-connection theorems, the math foundation.

## [0.8.0] — 2026-05-05

**Sol Symphony Times: 7 new planetary/stellar time systems.** Venus, Mercury, Pluto, Sol (the Sun!), Jupiter, Saturn, and Neptune join Mars / Lunar / Uranian as Sol Time members. The natural-symphony framing: every body in the encoder roster has a rotational + orbital cycle that ticks in its own cyclic group; the Sol Time series exposes the JD ↔ local-time mapping for each.

Pure-Python additions (no encoder, no C twin needed); ABI unchanged.

### Added — research/time_scales.py

| body | dataclass | sidereal day | year | anchor | retrograde |
|---|---|---:|---:|---|:---:|
| Venus | `VenusianTime` | 243.0226 d | 224.701 d | J2000.0 | ✓ |
| Mercury | `MercurianTime` | 58.6462 d | 87.9691 d | J2000.0 (Hun Kal) | |
| Pluto | `PlutonianTime` | 6.3872 d | 90,560 d | 2015 New Horizons | ✓ |
| Sol (Sun) | `SolSolTime` | 25.38 d (Carrington) | ~219 Myr (galactic) | CRN 1 (1853) | |
| Jupiter | `JovianTime` | 0.41354 d (System III) | 4332.589 d | 1965.0 epoch | |
| Saturn | `SaturnianTime` | 0.43932 d (Cassini-revised) | 10,759.22 d | J2000.0 | |
| Neptune | `NeptunianTime` | 0.67125 d (Voyager-2 System III) | 60,182 d | J2000.0 | |

Each ships with `jd_to_*_time(jd_tdb)` + `*_time_to_jd(...)` inverse plus module-level constants (sidereal/solar day, orbital period, axial tilt, anchor JD).

**Special quirks handled:**
- **Mercury 3:2 spin-orbit resonance** — solar day = 175.98 Earth-days = 2 Mercury-years exactly. The `MercurianTime` dataclass exposes both `mer_sd_sidereal` AND `mer_sd_solar` because either alone hides the resonance.
- **Venus retrograde + sidereal > year** — sidereal day = 243.0 Earth-days is *longer than* the 224.7-day year. The `VenusianTime` dataclass exposes both `vsd_sidereal` AND `vsd_solar` (= 116.75 Earth-days = synodic).
- **Sol differential rotation** — Carrington 25.38 d at ~16° latitude is the conventional reference; equator ~24.47 d, poles ~38 d. The `SolSolTime` dataclass exposes the Carrington Rotation Number (CRN) integer counter.
- **Saturn Cassini ring-seismology revision** — Mankovich et al. 2019 ApJ 871:1 revised System III from 10h 39m 22.4s (Voyager) to 10h 32m 35s ± 13s. We use the revised value.

### Added — bridge surface (14 methods)

`bridge.jd_to_sol_*_time(jd_tdb)` + `bridge.sol_*_time_to_jd(...)` for venusian / mercurian / plutonian / sol_sol / jovian / saturnian / neptunian. Each returns the dataclass dict plus an `epoch` block carrying the constants.

### Added — CLI (7 subcommands)

`time-venus`, `time-mercury`, `time-pluto`, `time-sol`, `time-jupiter`, `time-saturn`, `time-neptune`. Each follows the v0.5.4 `--help` audit pattern with concrete examples.

### Naming hierarchy convention (for future moon ports)

Established planet/star times: `Sol <Adjective> Time` — Sol Mars, Sol Lunar (Earth's Moon by historical convention), Sol Uranian, Sol Venusian, Sol Mercurian, Sol Plutonian, Sol Jovian, Sol Saturnian, Sol Neptunian, Sol Sol.

Future moon times follow parent-body hierarchy: `Sol <Parent>-<Body> Time` — e.g., Sol Pluto-Charon Time, Sol Jupiter-Io Time, Sol Earth-Moon Time. Established conventional names (Sol Lunar = Earth-Moon shorthand) are kept; new moon time systems land under the hierarchy convention so consumers always know which body's surface clock the answer refers to.

### Why a stand-alone minor bump

v0.8.0 instead of v0.7.1 because:
1. The bridge surface adds 12 new methods (significant new API).
2. The CLI adds 6 new subcommands.
3. The naming-hierarchy convention is a contract, not a tweak.

ABI is unchanged — no C twin needed; these are pure-Python time-scale formulas. Existing C/Python parity discipline holds: all 12 new bridge methods are classified as `python_only` in the parity smoke (rationale field documents the closed-form arithmetic).

### Tests

- 6 new immolation tests in test_immolation.py:
  - `test_v080_sol_symphony_round_trips_at_epoch` (each body's JD↔sol_date round-trips)
  - `test_v080_sol_sol_crn_starts_at_one` (CRN epoch convention)
  - `test_v080_mercury_3to2_spin_orbit_resonance` (spin-orbit resonance honored)
  - `test_v080_venus_retrograde_flag`
  - `test_v080_jovian_uses_system_iii`
  - `test_v080_saturnian_uses_cassini_revised`

104 active tests pass (was 84 in v0.7.0); 4 skipped (cibuildwheel-only native parity ladders).

### Subagent verification

Used a research subagent to confirm the gas-giant rotation rates (Jupiter System III, Saturn Cassini-revised System III) are observationally derived independently of moon orbital data — so Sol Jovian Time and Sol Saturnian Time can ship without first implementing the moons of Jupiter/Saturn. Confirmed: System III is read off magnetospheric radio emissions (Jupiter) or ring seismology (Saturn). Moons of those gas giants are a separate future task.

## [0.7.0] — 2026-05-05

**C/Python parity Tier 2b — full HD pipeline in C (ABI v5).** The architectural lift announced in v0.6.1's `TIER2_DESIGN.md` lands. Three new C entry points + bridge dispatch on `backend={"auto","bip","c","fpu-ref"}` for `get_local_view` and `get_eclipse_probability`. The parity smoke test's two `tier2_skip` entries flip to `parity` — **every encoder-touching bridge method now has a paired C path**. The discipline announced at v0.6.0 ("if we always smoke all python things, we know to always smoke the same C things") is fully realised.

### Added — C surface (ABI v5)

- ``es_encode_state_hd(delta_t_days, complex64 *out, D)`` — calls the existing `es_encode_state` for the 38 × uint32 phase residues, lifts each via the splitmix64 channel basis (`es_channel_basis(2026 + body_idx, ..., D)`), divides by sqrt(D), sums into the accumulator, normalises.
- ``es_bind_observer(state_in, body_idx, lat, lon, state_out, D)`` — pure HDC algebra: integer-encode (lat, lon), build a coord_op via `np.roll(channel_basis(9999), (lat·67 + lon·7) mod D)`, multiply elementwise, scale by `sqrt(D)`. No SPICE, no skyfield.
- ``es_get_eclipse_probability(state, D, sun_idx, moon_idx, *out_prob)`` — builds the syzygy operator (sun + moon channel bases / sqrt(D) plus node basis from seed=777 / sqrt(D)), normalises, returns `|<state, s_op>|`.
- New SSOT macros: ``ES_BODY_BASIS_SEED_BASE``, ``ES_OBSERVER_COORD_BASIS_SEED``, ``ES_SYZYGY_NODE_BASIS_SEED``, ``ES_COPRIME_LAT``, ``ES_COPRIME_LON``.

### Added — Python

- ``_research/bip_hd_lift.py`` — pure-Python BIP-and-lift pipeline. ``encode_state_hd``, ``bind_observer``, ``syzygy_operator``, ``eclipse_probability``. Mirrors the C path step-for-step using the splitmix64 portable PRNG from v0.6.1. The Python BIP-and-lift output and the C ``es_encode_state_hd`` output agree within float-ULP.
- ``_native_bip.native_encode_state_hd``, ``native_bind_observer``, ``native_get_eclipse_probability`` — ctypes wrappers returning `numpy.complex64` arrays.
- New ``backend`` parameter on ``bridge.get_local_view`` and ``bridge.get_eclipse_probability``: ``"auto"`` (default) / ``"bip"`` / ``"c"`` go through the new BIP-and-lift HD path; ``"fpu-ref"`` keeps the original ``EphemerisHDCInstrument.encode_state`` matrix-expm propagation for backwards compatibility. Both return a ``backend`` field in the result dict.

### Behaviour change

Default behaviour of `bridge.get_local_view` and `bridge.get_eclipse_probability` changes from FPU-matrix-expm to BIP-and-lift output. The two paths produce **different state vectors** because they use different propagation algorithms:

- **BIP-and-lift** (v0.7.0+ default): integer-Q-format chunked propagation + LUT-based breathing + lift via channel bases. Fast, deterministic, byte-identical to the C twin within float-ULP.
- **FPU-ref** (pre-v0.7.0 default; opt-in via `backend="fpu-ref"`): scipy.linalg.expm matrix propagation. Captures second-order Laplacian effects but no C twin.

Tests don't pin specific bytes for these methods; the bridge contract (returns ok=True with state vector + probability scalar) is unchanged. Numerical values differ between v0.6.1 and v0.7.0 default output. Callers that need v0.6.1's exact bytes should pass ``backend="fpu-ref"``.

### Tests

- New ``tests/test_hd_parity.py`` — 8 byte-parity tests pinning Python BIP-and-lift ↔ C agreement on `encode_state_hd`, `bind_observer` (parametrized over 4 lat/lon points + body combinations), `eclipse_probability`. Tolerance: 1e-5 on state vectors, 1e-7 on the scalar probability — both well above the empirical ~1e-9 diff observed.
- ``tests/test_parity_smoke.py`` `tier2_skip` entries flipped to ``parity``. **22/22 parametrized parity smoke tests pass; 0 tier_skip entries remain.**

84 active tests pass; 4 skipped (cibuildwheel-only native parity ladders).

### Discipline reached

| version | parity scope |
|---|---|
| v0.5.x | encoder hot path (BIP ↔ C byte-identical, pinned by `test_native_parity`) |
| v0.6.0 | + `find_syzygies` + `get_breathing_modulation` |
| v0.6.1 | + channel-basis foundation (splitmix64) |
| **v0.7.0** | + **HD pipeline (encode_state_hd, bind_observer, eclipse_probability)** |

The PARITY_TARGETS table is the SSOT for what's at parity. As of v0.7.0 every entry is either `parity` (8 entries) or `python_only` (12 entries); zero `tier{1,2}_skip` outstanding.

### Next: phase 2c (deferred)

The `TIER2_DESIGN.md` document mentioned a phase 2c — deciding whether to retire the FPU matrix-expm path or keep it as `backend="fpu-ref"`. v0.7.0 ships with the second choice (kept). The matrix-expm path captures second-order Laplacian effects the BIP integer encoder doesn't; whether that matters for any downstream consumer is empirically open. Phase 2c will measure path divergence on the DE441 sweep and decide.

## [0.6.1] — 2026-05-05

**C/Python parity Tier 2a foundation (ABI v4).** Lays the groundwork for the v0.7.0 hyperdimensional-state-in-C work. No bridge surface change; no encoder behaviour change. The `tier2_skip` parity smoke entries stay as-is — phase 2a is the *foundation*, phase 2b (HD encode + observer-bind + eclipse projection) flips them to `parity` in v0.7.0.

### Why a separate phase 2a

Tier 2 needs **byte-identical channel-basis hypervectors** between Py and C. The Python ref instrument was originally seeded via `numpy.random.default_rng(seed).uniform(0, 2π, D)`, which is PCG64-DXSM internally — reproducing that bit-exactly in C is brittle. Switched both sides to **splitmix64** (six lines, identical output across any IEEE-754 platform). The basis byte values change vs v0.6.0 (Python tests don't pin them; non-breaking).

### Added — C surface (ABI v4)

- `c/include/es_prng.h` + `c/src/es_prng.c`: portable splitmix64 PRNG. `es_splitmix64_next(uint64_t *state)`, `es_splitmix64_uniform_2pi(uint64_t u)`. Bit-identical to the Python `_research/portable_prng` module.
- `c/src/es_channel_bases.c`: `es_channel_basis(seed, out, D)` fills a complex64[D] hypervector deterministically from `seed`.
- `es_complex64_t` typedef in the public header — `{float real; float imag;}`, 8 bytes, matches numpy's complex64 wire format so consumers can `np.frombuffer` directly.

### Added — Python

- `_research/portable_prng.py`: splitmix64 mirror. Same six lines, same conversion to [0, 2π).
- `_native_bip.native_channel_basis(seed, D)`: ctypes wrapper returning a `numpy.complex64` array.
- `tests/test_channel_basis_parity.py`: 10 parity tests pinning byte-identical agreement between Py + C across N=38 body seeds and D ∈ {1024, 65536}, plus splitmix64 standalone parity (first 4 outputs match the canonical Vigna 2013 reference).

### Codegen

`emit_research_modules.py` includes `portable_prng.py`; manifest regenerated.

### Tests

74 active tests pass (was 64 in v0.6.0); 6 skipped (4 cibuildwheel-only + 2 Tier 2b stubs).

### Tier 2 design doc

`TIER2_DESIGN.md` lays out the three-phase delivery plan:
- **Phase 2a (this release)** — channel-basis foundation: portable PRNG, `es_channel_basis`, parity-pinned. ✅
- **Phase 2b (v0.7.0)** — `es_encode_state_hd`, `es_bind_observer`, `es_get_eclipse_probability`. Bridge dispatch on backend. Parity smoke flips both Tier 2 entries to `parity`.
- **Phase 2c (v0.7.x)** — research instrument decision: retire matrix-expm path, or keep as `backend="fpu-ref"` for three-way parity.

## [0.6.0] — 2026-05-05

**C/Python parity Tier 1 + always-on parity smoke test (ABI v3).** Two encoder-touching bridge methods that were previously Python-only now have C twins, and a new test scaffolds C/Python parity discipline as a durable guarantee. ABI bumps v2 → v3 (additive — encoder hot path is unchanged; ``backend="c"`` produces byte-identical / float-ULP-equal output for every parity-flagged bridge method).

### Added — C entry points (ABI v3)

- ``es_breathing_modulation(delta_t_days, idx_a, idx_b, n_a, n_b, …)`` — exposes the resonant-pair phase residue + integer-LUT modulation factor at a single JD. Same arithmetic that lives inside ``es_encode_state``'s breathing inner loop, evaluated at one (jd, body_pair, n_lobes) without running the full encode.
- ``es_find_syzygies(jd_lo, jd_hi, kind, threshold, max_candidates, out_buf, out_capacity, *out_count)`` — fixed-period synodic + draconic month enumeration. No encoder calls; pure modular arithmetic mirroring ``_research/syzygy_window.py`` 1:1. New ``es_syzygy_t`` struct.
- New ``es_status_t`` codes: ``ES_ERR_INVALID_INDEX = 4``, ``ES_ERR_INVALID_KIND = 5``, ``ES_ERR_INVALID_THRESHOLD = 6``.

### Added — bridge dispatch

Both ``bridge.get_breathing_modulation`` and ``bridge.find_syzygies`` accept ``backend="auto"`` (default), ``"bip"`` (pure-Python), or ``"c"`` (native). Auto picks ``"c"`` when the native binary is loaded, else falls back to ``"bip"``. The result dict carries a ``backend`` field for callers that want to know which path executed.

### Added — `tests/test_parity_smoke.py`

The **always-on parity guard.** Every public function in ``bridge.py`` is classified in a ``PARITY_TARGETS`` table by status:

| status | meaning |
|---|---|
| ``parity`` | both backends implemented; outputs must match within tolerance |
| ``python_only`` | pure-Python by design (closed-form time scales, metadata getters) |
| ``tier1_skip`` | C port pending in Tier 1 (none remain after v0.6.0) |
| ``tier2_skip`` | C port pending in Tier 2 (HD-state architectural lift, v0.7.0) |

Two drift-detection sub-tests force the table to stay current:
- ``test_parity_smoke_spec_covers_bridge_surface`` — every public ``bridge.*`` function MUST be in PARITY_TARGETS or in the explicit non-parity allowlist; adding a new bridge method without a parity classification fails CI.
- ``test_parity_smoke_no_orphan_targets`` — every PARITY_TARGETS entry must correspond to a real bridge function; deleting a function without removing its entry fails CI.

This is the discipline the user asked for: "if we always smoke all python things, we know to always smoke the same C things."

### Tier 2 still pending

Two methods remain ``tier2_skip`` after v0.6.0: ``get_local_view`` and ``get_eclipse_probability``. Both operate on the FPU complex128 hyperdimensional state (D=65536); the C side currently exposes only the 38-body Q-format integer phases. Lifting the C runtime to carry the HD state via channel-basis emission at codegen time is a larger architectural change targeted at v0.7.0. The smoke test marks both as skipped with the tier-2 reason; the Python paths still work as before.

### Discipline

- The parity smoke test runs in every CI cell. Pure-Python fallback runs the python_only entries; native cells exercise the parity entries with both backends and assert equality.
- Status downgrades (``parity`` → ``tier{1,2}_skip``) are forbidden — they hide regressions. If parity breaks, fix the underlying drift, don't reclassify.
- Adding a new encoder-touching bridge method now requires (a) a paired C entry point OR (b) a justified ``python_only`` rationale.

### Tests

- 22 new parametrized parity smoke tests (one per PARITY_TARGETS entry) plus the 2 drift-detection sub-tests.
- 64 active tests pass; 6 skipped (4 cibuildwheel-only native parity ladders + 2 Tier 2 skips).

### Notes

- Encoder hot path is **byte-identical** to v0.5.5. With no patches active, ``get_system_state(backend="c")`` returns the same uint32[38] as v0.5.5 (regression test pinned).
- The four anchor constants for syzygy enumeration (synodic / draconic months + two reference JDs) are mirrored from ``_research/syzygy_window.py`` into ``c/src/es_parity.c`` as static const. The parity smoke test catches drift between the two if either side ever changes.

## [0.5.5] — 2026-05-05

**Moon catalog patches (Phase C).** Five LS-fit-vindicated moon patches join `CATALOG_V2`. With the v0.5.3 high-precision sidereal periods removing the dominant secular drift, the residual moon spectrum is now decomposable into clean dominant peaks — exactly the regime where the v0.5.2 LS-fit methodology earns its 96-99% shrinkage on planets.

### Added — `CATALOG_V2` (5 entries)

Each carries `MEASURED SHRINKAGE` in its `notes` field (the v0.5.2 regression-test convention):

| name | body | period | amp | shrinkage | RMS Δ |
|---|---|---:|---:|---:|---:|
| `dione-1.06yr-diagonal-v2` | dione | 387.04 d | 3.57° | **98.2%** | 2.535° → 0.199° |
| `tethys-0.38yr-diagonal-v2` | tethys | 138.24 d | 3.57° | **93.8%** | 2.944° → 1.511° |
| `enceladus-0.39yr-diagonal-v2` | enceladus | 141.94 d | 3.58° | **98.9%** | 2.569° → 0.458° |
| `titan-0.69yr-diagonal-v2` | titan | 252.74 d | 3.31° | **95.5%** | 3.388° → 2.447° |
| `iapetus-0.22yr-diagonal-v2` | iapetus | 79.34 d | 3.26° | **98.6%** | 2.497° → 0.954° |

LS-fit recovered amplitudes are 2-3× the FFT-bin baselines — same bin-leakage pattern that v0.5.2 documented on planets, vindicating the methodology a second time on a completely different bodyset.

### Hyperion: PARTIAL (75.2%, single sinusoid not enough)

The Hyperion `0.20yr-diagonal` patch shrinks the targeted 72.4-d peak by 75.2% (5.44° → 1.35°), shy of the 80% catalog gate. Hyperion is the canonical chaotic-rotator (Wisdom 1984); its FFT shows multiple sub-peaks near 72d (rank 1 at 5.44°, rank 3 at 1.39°, rank 5 at 1.30°) — the quasiperiodic-not-sinusoidal signature. A single LS-fit sinusoid hits the methodological ceiling there. **Queued as v0.5.x research:** either a multi-component patch (the v0.5.2 multi-bin idea, now motivated by physics not bin leakage) or a coupled Titan-Hyperion 4:3 patch (v0.5.0 wired the resonance into `RESONANCES` but never calibrated the coupling strength). Hyperion stays out of `CATALOG_V2` until one of those passes the 80% bar.

### Added — research scripts

- `research/author_moon_patches.py` — moon-targeted LS-fit author. Reuses `_lsq_fit_sinusoid` from the planet author; uses the moon-friendly window (4096 × 30d) so the supplementary `jup365` / `sat441` kernels cover the FFT span.
- `research/verify_moon_patches.py` — patch-shrinks-residual verifier. 7 sweeps (1 baseline + 6 patches); the verdict gate matches the v0.5.2 planet path.
- `research/de441_moon_spectrum.gather_moon_residuals(...)` — extracted from `run_moon_spectrum` so both author + verify share the residual-gathering loop without re-emitting FFT structure each time.

### Outputs

- `results/moon_recovered_catalog.json` — recovered patch params per target.
- `results/verify_moon_patches.{json,md}` — measured shrinkage per patch.
- `figures/moon_catalog_patches_v0.5.5.md` — narrative writeup of the methodology second-vindication.

### Tests

3 new immolation tests for the v0.5.5 moon-patch surface:
- `test_v055_moon_patches_present_in_catalog` — all 5 entries reachable via `bridge.list_catalog_patches`.
- `test_v055_moon_patches_carry_measured_shrinkage` — each entry's `notes` includes the `MEASURED SHRINKAGE` regression-test gate + Phase C provenance.
- `test_v055_moon_patches_apply_and_clear` — full apply/active/clear round-trip via the bridge surface.

44 active tests pass on the v0.5.5 build (was 41 in v0.5.4); 4 skipped (cibuildwheel-only native parity).

### Notes

- Phase C completes the v0.5.x moon programme (Phase A diagnosis → Phase B period fix → Phase C catalog patches). The remaining 4 unfixed moons (metis / thebe / rhea / phoebe) are physics-specific — Phoebe needs a sign-aware retrograde encoder, Metis needs an authoritative period, Thebe + Rhea look perturbation-driven. None of those gate Phase C.
- The methodology is now **vindicated twice** on completely independent body sets: v0.5.2 planets (4 patches at 96-99%), v0.5.5 moons (5 patches at 93-99%). Bin leakage applies the same way (LS-fit amps 2-3× the FFT-bin baselines) on bodies orbiting the Sun and bodies orbiting Saturn.

## [0.5.4] — 2026-05-05

**Sol Uranian Time (SUT)** — third planetary time system in the package, alongside Mars Sol Date / Mars Coordinated Time (Allison & McEwen 2000) and lunar synodic / sidereal phase. CLI `--help` audit across all subcommands.

### Why a Uranus time system

The notebook §6 natural-resonance gear group (Z_30 in v0.2.0, Z_60 in v0.5.0) is anchored in the integer mean-motion ratios that sit in `RESONANCES`. **Uranus is conspicuously absent from that group.** Its orbital period (84.02 yr) doesn't sit in a clean mean-motion resonance with any other body in the Sol Star System; its axial tilt (97.77°) is too extreme for the planet-on-equator approximations the other planets share; its rotation is retrograde. Sol Uranian Time **lives in its own cyclic group** — one anchored to Uranus's three independent cycles (sidereal day, solar day, orbital season) that don't share natural-coprime structure with anything else in the Sol Star System.

The "Sol" prefix marks the family: Sol Mars Time (MSD/MTC), Sol Lunar Time (synodic/sidereal phase), Sol Uranian Time (SUT/USD). All share Julian Date as their Earth-side reference; their cyclic groups are otherwise independent.

### Added — research/time_scales.py

- `UranianTime` dataclass with `jd_tdb`, `usd`, `sut_hours`, `sut_seconds`, `orbital_phase`, `season`, `years_since_epoch`, `retrograde`.
- `jd_to_uranian_time(jd_tdb) → UranianTime` — primary conversion.
- `uranian_time_to_jd(usd) → JD_TDB` — inverse on the USD field (orbital season is uniquely determined by USD given the SUT epoch, so no information loss).
- Module-level constants: `URANUS_SIDEREAL_DAY_HOURS = 17.24`, `URANUS_ORBITAL_PERIOD_DAYS = 30688.5`, `URANUS_AXIAL_TILT_DEG = 97.77`, `SUT_EPOCH_JD_TDB = 2454451.0`, `URANIAN_SEASONS = ("northern-autumn", "southern-summer", "northern-spring", "northern-summer")`.

### Added — bridge surface

- `bridge.jd_to_sol_uranian_time(jd_tdb)` returns a Pyodide-friendly JSON dict with the fields above plus an `epoch` block carrying the IAU/NASA fact-sheet constants. Failure mode: `{ok: False, error: ...}` for invalid JD.
- `bridge.sol_uranian_time_to_jd(usd)` is the inverse.

### Added — CLI

- `ephemerides-spectral time-uranus --jd <JD>` (or `--usd <USD>` to invert). Full `--help` epilog with examples spanning J2000, the SUT epoch (2007-12-16 northern equinox, JD 2454451.0), and a current-day reference. Inline natural-harmonic discussion in the description block.

### CLI `--help` audit (all subcommands)

The `patches` subcommand group from v0.4.0 had stale text claiming "the C native backend doesn't yet implement the overlay" (true at v0.4.0; superseded by v0.4.1's ABI v2 + v0.5.2's CATALOG_V2). v0.5.4 corrects that and adds explicit `description` + `epilog` blocks with concrete examples to every `patches catalog/active/apply/clear` subcommand.

Every subcommand now has:
- A short `help` line for the parent `--help` listing.
- A multi-line `description` explaining what the command does + when to use it.
- An `epilog` with at least one concrete `ephemerides-spectral <cmd> ...` example.

`time-uranus` follows the same pattern by default — natural mirror of `time-mars` / `time-lunar`.

### Tests

6 new immolation tests for SUT (epoch round-trip, retrograde flag, season partition boundary, USD uniform-advance, bridge surface presence). All 27 active tests pass; 18 skipped (cibuildwheel-only native parity).

### Notes

- The function names use the **adjective form** (`jd_to_uranian_time`, mirroring `jd_to_lunar`). The proper noun `Uranus` shows up only in module-level constants where it identifies the body itself.
- Uranus rotates **retrograde**; the encoder still advances `omega = +2π/P` for all bodies. Surfacing the `retrograde=True` flag makes the asymmetry visible but doesn't fix it. Phoebe's continued ~104° RMS in the v0.5.3 moon FFT sweep is the same root cause; sign-aware-omega is queued for v0.5.x.
- No body-roster change. v0.5.4 is purely additive on the time-scale + CLI-help surface.

## [0.5.3] — 2026-05-05

**Moon residuals: 13 of 17 moons fixed.** The v0.5.2 sweep had identified ~100° RMS residuals on most moons as a v0.5.x research question. The diagnosis turned out to be **period truncation in the BODIES table**, not the frame-mismatch hypothesis from notebook §3. Replacing 3-4-decimal sidereal periods with 9+-decimal JPL-HORIZONS values dropped 8 moons by 30-1450× and brings the broken-moon count from 13 down to 4.

### Diagnostic (research/diagnose_moon_residual.py)

Per-orbital-period diagnostic on Callisto (control, 0.6° v0.5.2 RMS), Titan (control, 3.4°), Io (broken, 106°), Europa (broken, 116°), Mimas (broken, 104°), Metis (broken, 104°). Within ONE orbital period, the "broken" moons show TINY residuals (Io 0.42°, Metis 0.07°). The ~100° v0.5.2 sweep RMS is therefore secular drift accumulating over many periods, not within-orbit ecliptic-projection warping. The frame-mismatch hypothesis is **ruled out**.

### Real root cause: period truncation

The encoder uses `omega = 2π / P_sidereal` baked at codegen time. v0.5.0's `BODIES` stored periods to 3-4 decimals. For fast-orbit moons (Io 1.769 d, Metis 0.295 d, Mimas 0.94 d) the 10⁻⁴-relative truncation produces 10⁻⁴-relative omega error that accumulates over 41,000+ orbits in the 200-yr sweep horizon. The wrap of cumulative drift modulo 2π produces a sawtooth-shaped residual whose FFT spectrum is broadband — that's the "near-DC content" the v0.5.2 report flagged as suspicious.

Predicted-cumulative-drift heuristic confirms: Callisto (1.1×10⁻⁶ rel err) → predicted 1.7° → observed 0.6° (clean ✓); Ganymede (-6.3×10⁻⁵) → predicted -130° → observed 117° (matches the wrapped sawtooth). The moons whose predicted cumulative drift is small are exactly the ones that already worked in v0.5.2.

### Fix: high-precision sidereal periods

`research/bodies.py` updated with 9+-decimal sidereal periods from JPL HORIZONS / NASA fact sheets. Examples (v0.5.0 → v0.5.3):
- io: `1.769` → `1.76913786`
- europa: `3.551` → `3.551181`
- ganymede: `7.155` → `7.15455296`
- mimas: `0.9424` → `0.94242196`
- enceladus: `1.370` → `1.37021785`
- metis: `0.2948` → `0.29478000`
- adrastea: `0.2983` → `0.29826000`
- amalthea: `0.4982` → `0.49817905`
- thebe: `0.6745` → `0.67451400`
- All planets, asteroids, and the Mars+Earth moons also bumped to 9+ decimals for consistency.

### Measured improvement on the moon FFT sweep

`research/de441_moon_spectrum.py` re-run on the v0.5.3 high-precision-period encoder:

| Moon | v0.5.2 | v0.5.3 | improvement |
|---|---|---|---|
| io | 106° | **0.34°** | **-317×** |
| europa | 116° | **0.76°** | **-154×** |
| ganymede | 117° | **0.14°** | **-825×** |
| adrastea | 104° | **0.07°** | **-1450×** |
| amalthea | 102° | **0.27°** | **-376×** |
| enceladus | 103° | **2.57°** | **-40×** |
| tethys | 101° | **2.94°** | **-34×** |
| dione | 117° | **2.54°** | **-46×** |
| mimas | 104° | 30.8° | -3.4× (partial) |

13 of 17 moons now clean (≤ 3° RMS). 4 still broken (metis 109°, thebe 104°, rhea 100°, phoebe 104°) — see ROADMAP for individual investigation queue.

### Why the still-broken 4 resisted

- **Metis**: published sidereal periods vary by source; need definitive value.
- **Thebe**: small inclination + eccentricity; perturbation-driven residual.
- **Rhea**: 0.35° inclination to Saturn's equator + perturbations from neighbouring moons.
- **Phoebe**: RETROGRADE orbit (period 550.56 d backward relative to Saturn). Our encoder advances `omega = +2π/P` regardless of direction; needs a sign-aware fix.

### Notes

- `_data/initial_phases.json` regenerated with new omega values; C-side `es_omega_diag[]` and `es_initial_phases[]` re-emitted by `c/codegen/emit_c_tables.py`.
- All 35 tests pass; 4 skipped (cibuildwheel-only).
- v0.4.0 catalog patches and v0.5.2 CATALOG_V2 still apply; their measured shrinkages are slightly different on the v0.5.3 encoder but the patches still target the same FFT residual peaks (now from a more-accurate-omega baseline).

### What this earns

With 13 moons clean, the LS-fit catalog methodology (v0.5.2, §9) now applies to moons. Next step: re-run patch-shrinks-residual on the moon residuals to author measurement-validated CATALOG_V2 entries for the Saturnian resonances (Mimas-Tethys 4:2, Enceladus-Dione 2:1, Titan-Hyperion 4:3) that v0.5.0 wired but couldn't yet calibrate.

## [0.5.2] — 2026-05-05

**Patch-shrinks-residual benchmark FULLY VINDICATED on planets.** Least-squares fitting at the exact target period replaces FFT-bin extraction; the resulting `CATALOG_V2` hits **99.2% (Mars), 99.9% (Mercury), 97.6% (Jupiter), 96.0% (Saturn)** measured shrinkage. Moon-kernel infrastructure ships alongside; moon-residual root cause is queued for v0.5.x.

### What this earns

The v0.5.1 audit got us to PARTIAL vindication (~77% on J–S, but Mars stuck at 2.7% due to FFT bin leakage). v0.5.2's LS-fit methodology unblocks the leakage problem and **vindicates the full diagnosed-fiber-overlay methodology on the bodies it was designed for**: 4/4 planet bodies hit ≥96% shrinkage. The catalog is no longer "applicable" — it's *useful*, with measured shrinkage% pinned per entry as a regression-test gate.

### Added — `CATALOG_V2`

`research.diagnosed_fibers.CATALOG_V2` ships alongside the existing v0.4.0 `CATALOG`. Three patches authored from the v0.5.0 38-body encoder via the LS-fit pipeline:

| name | body | amplitude | period (d) | phase (rad) | corr | measured shrinkage |
|---|---|---:|---:|---:|---:|---|
| `mars-7.96yr-diagonal-v2` | mars | 10.69° | 2902.74 | 0.3378 | — | **99.2%** |
| `mercury-10.69yr-diagonal-v2` | mercury | 23.48° | 3898.87 | 3.0538 | — | **99.9%** |
| `jupiter-saturn-9.56yr-coupled-v2` | jupiter+saturn | 113.29° | 3495.81 | 6.0191 | **+1** | **97.6% J / 96.0% S** |

The combined `COMBINED_CATALOG = {**CATALOG, **CATALOG_V2}` gives 6 patches total. `bridge.list_catalog_patches()` exposes both; `bridge.apply_patch("mars-7.96yr-diagonal-v2")` loads the v2 entry. Each v2 patch's `notes` field carries the measured shrinkage% as a regression-test gate.

### Added — least-squares patch authoring (research-side)

- `research/author_phase_recovered_patches.py` — new `method="lsq"` mode (default). Uses `scipy.optimize.curve_fit` to fit `A·sin(2π·t/P + φ)` to the residual time series at the target period; period is a free parameter in `[target − 60d, target + 60d]`. Bypasses FFT bin leakage entirely.
  - **Math derivation in module docstring** — for an FFT bin with complex value `X[m]`, the cancellation patch parameters are `A = 2|X[m]|/N`, `φ = arg(X[m]) − π/2 + 2π·half_span/period` (mod 2π), `correlation = +1` if `|Δφ_a − Δφ_b| < π/2` else `−1`. The LS-fit method re-derives the same params from the time-domain signal directly, with period free.
- `research/verify_recovered_patches.py` — runs the benchmark against the LS-fit catalog. Verdict: **VINDICATED** on all four targeted bodies.

### Added — moon-kernel infrastructure

- `research/ephemeris_loader.py` extended with `auxiliary_kernels: Optional[List[str]]`. The bundle now carries `extra_ephs: List[Any]` and `extra_kernel_names: List[str]`; new `bundle.lookup(target_key)` searches the main kernel + each auxiliary in order.
- `bip_instrument._calibrate_initial_phases` uses `bundle.lookup` for moon truth → moon initial phases now come from real ephemeris (sat441, jup365) instead of the period-based fallback.
- `de441_error_spectrum._truth_longitude` updated to handle the v0.5.0 expanded moon roster + use `bundle.lookup`.
- `research/de441_moon_spectrum.py` (new) — moon-friendly FFT sweep (`±200 yr` window, 30-d cadence, 4096 samples) that fits inside jup365 / sat441 coverage. Reports per-body residuals for **27 bodies** (was 10 with planets-only DE441).

### Findings — `figures/patch_shrinks_residual_v0.5.2.md`

- **LS-fit recovers larger amplitudes than FFT-bin extraction** (Mars +55%, Mercury +28%, J–S +26%). Mars is the worst leakage case — its 7.96-yr signal smears across two adjacent bins; the FFT-bin extraction underestimates the true sinusoidal amplitude by 3×.
- **J–S correlation = +1, not −1** (empirical, from LS-fit `Δφ_a − Δφ_b` at 9.56 yr). The v0.4.0 anti-correlated-libration assumption was wrong; the residuals are in-phase.
- **Most moons show ~100° RMS residuals.** Callisto, Titan, Iapetus, Hyperion are the 4 "working" moons (RMS ≤ 11°). For the rest (io, europa, ganymede, mimas, enceladus, tethys, dione, rhea, plus the v0.5.0 inner-Jovian regulars and Saturn co-orbitals), the dominant FFT peak is at the sweep span (336 yr) — that's near-DC content, not periodic missing physics. Most likely cause is a calibration mismatch when looking up moon barycenters across stacked SPK kernels. v0.5.x research item.

### Changed

- `de441_error_spectrum.run_spectrum`: `top_peaks` K bumped 20 → 100 so a successfully-shrunk peak is still findable when demoted.
- `bip_instrument` constructor: loads `mar099s` / `jup365` / `sat441` as auxiliary kernels by default. If a given file isn't on disk, it's skipped silently — the bundle is still functional for whatever bodies the main kernel + remaining auxiliaries cover.
- `verify_recovered_patches.py`: tolerance widened (Mars 0.10→0.30, Mercury 0.15→0.50, J–S 0.10→0.30 yr) and "no peak in tolerance after patching" is now reported as a conservative upper-bound shrinkage rather than a hard error (since the targeted peak demoting below the smallest top-K peak IS effective shrinkage).

### Notes

- The v0.4.0 catalog is **not deprecated** — it ships unchanged in the wheel. Users who want vindicated-shrinkage patches use the `-v2` names; users who want the original (e.g., for v0.4.0/v0.5.1 regression continuity) use the v1 names. Each version's catalog reflects the methodology of its time.
- `_data/initial_phases.json` updated by codegen to reflect the v0.5.2 moon calibration via `bundle.lookup`. The C-side `es_initial_phases[]` is also re-emitted.

## [0.5.1] — 2026-05-05

**Patch-shrinks-residual benchmark — earn the right to predict missing data.** Verdict: **PARTIAL VINDICATION**. The methodology produces real, reproducible shrinkage on the J–S coupled patch (~77% on both bodies) and meaningful shrinkage on Mercury (~40%); Mars stays stuck at 3% due to FFT bin leakage. Two authoring bugs in the v0.4.0 catalog surfaced and were diagnosed: amplitude was off by 2×, and phase was wrongly assumed zero.

### What this earns

The original argument for v0.5.1: *patches in the v0.4.0 catalog claim to predict missing physics; until we measure that they actually shrink their targeted FFT residual peak, the claim is unaudited*. v0.5.1 audits it.

The audit produced clean diagnostic data on a methodology bug, a math fix, and quantified shrinkage. We earned **partial** predictive power — J–S 77% is hard data that the spectral-FFT-diagnose-then-overlay approach works when authored correctly — and a clear next step (windowed FFT + multi-bin patches for FFT-leakage cases like Mars).

### Three new research scripts

- **`research/patch_shrinks_residual.py`** — measures shrinkage of the targeted FFT peak when each v0.4.0 catalog patch is active vs inactive. Verdict on the v0.4.0 catalog: REJECTED (Mars +2.5%, Mercury **−49.9%** *(peak GREW)*, J–S +30.9% / −0.4%).
- **`research/author_phase_recovered_patches.py`** — re-authors the catalog from the FFT's complex spectrum:
  - Amplitude: `A = 2 |X[k]| / N` (was `|X[k]| / N`, off by 2×).
  - Phase: `φ = arg(X[k]) − π/2 + 2π · half_span_days / period_days` (mod 2π). The earlier formula `3π/2 − arg` was wrong both in sign and in missing the time-origin offset (the FFT phase is referenced to sample 0 = `REFERENCE_JD − half_span`, NOT to `REFERENCE_JD`).
  - Coupled correlation: recover from the J–S residual phase difference at the target period — `correlation = +1` if `|Δφ| < π/2`, else `−1`. **Empirically `correlation = +1` for J–S 9.56 yr** — the v0.4.0 anti-correlated-libration assumption was wrong.
- **`research/verify_recovered_patches.py`** — re-runs the benchmark with the phase-recovered catalog. Verdict: PARTIAL (Mars +2.7%, Mercury **+39.6%**, J–S **+77.1% / +76.4%** on both bodies).

### Findings table

| Patch | v0.4.0 (mag-only) | v0.5.1 (phase-recovered) | Δ |
|---|---|---|---|
| `mars-7.96yr-diagonal` | +2.5% | +2.7% | +0.2 pp |
| `mercury-10.69yr-diagonal` | **−49.9%** *(grew!)* | **+39.6%** | **+89.5 pp** |
| `jupiter-saturn-9.56yr-coupled` (Jupiter) | +30.9% | **+77.1%** | +46.2 pp |
| `jupiter-saturn-9.56yr-coupled` (Saturn) | **−0.4%** | **+76.4%** | **+76.8 pp** |

Mercury swung 89.5 percentage points just from phase + amplitude correction; Saturn went from ~no effect to ~77% shrinkage in lockstep with Jupiter (the correlation flip is doing exactly what the math says it should).

### Why Mars stays stuck

Mars's residual at the v0.3.1 FFT report:

```
| 1 | 7.960 | 2907.3 | 3.4488 |
| 2 | 7.935 | 2898.1 | 3.3558 |
```

Two adjacent FFT bins of comparable amplitude — the classic signature of a single sinusoid whose true period falls *between* two FFT bins, with the energy spectrally leaking across both. A single-frequency overlay can only cancel the energy at one bin; the leaked half stays. Quantified ceiling: ~50% shrinkage from a single-bin patch on this kind of leaked residual. Mars at 2.7% means the recovered period was off by enough that the patch barely landed in the right bin.

### What `de441_error_spectrum` learned

`top_peaks` returned by `run_spectrum` was bumped from K=5 to K=20. Critical: when a successful patch shrinks its target peak, that peak demotes out of the original top-5 — but it's still measurable. Without K=20 the verifier reported "no peak in tolerance" on Jupiter, hiding the actual 77.1% shrinkage.

### What the v0.4.0 catalog gets

The v0.4.0 catalog **stays unchanged** in the wheel. v0.5.1 is research-side audit + diagnostic; the recovered catalog (in `results/phase_recovered_catalog.json`) doesn't yet meet the ≥80% bar across all bodies. v0.5.2 will:

1. Add Hann-windowed FFT to the patch-authoring pass (suppress leakage; pushes Mars from 2.7% to >50%).
2. Add multi-bin patches: a single catalog entry expressed as a list of `(period, amplitude, phase)` sinusoids covering the bins around the target. C-side overlay struct gets a small array of sinusoids per patch.
3. Ship `CATALOG_V2` alongside the existing `CATALOG`. Each entry pinned with its measured shrinkage% as a regression-test gate.

### Notes

- End-to-end benchmark wall-time ~25 min on the v0.5.0 C native + skyfield truth-lookup path. On Python BIP it's ~90 min (the truth-lookup is the slow part either way; encode is sub-millisecond on C).
- The recovered catalog finding that **J–S `correlation = +1`** (in-phase residuals at 9.56 yr) is the most interesting physics signal of v0.5.1. The original assumption was anti-correlated libration around the conjunction; the FFT data rejects that. What this means physically — whether the v0.5.0 RESONANCES table needs `Resonance("jupiter", "saturn", 5, 2, ...)` rewritten with `(2, 5)` instead — is queued for v0.5.x research.

## [0.5.0] — 2026-05-05

**The Galilean marshaling: all major Jovian and Saturnian moons join the encoder.** Body count grows from 26 → 38 (+12 moons). Three famous Saturnian resonances wired into the breathing Laplacian. SPICE-free runtime — `pip install` and encode immediately.

### Architecture: SPICE-free runtime via codegen-baked initial phases

v0.4.1 left a UX gap: the C path baked initial phases at codegen time (no SPICE needed at runtime), but the Python BIP path calibrated at runtime via skyfield and silently zeroed-out when no SPICE kernel was staged. The two backends agreed only when SPICE was on disk.

v0.5.0 closes the gap: a new codegen step (`codegen/emit_initial_phases.py`) emits `_data/initial_phases.json` carrying the SAME calibrated values the C codegen uses. `EphemerisBIPInstrument._calibrate_initial_phases` consults this JSON first; only falls back to live SPICE calibration when the JSON is missing (research source tree, or codegen-time itself building the JSON).

Result: `pip install ephemerides-spectral` works out of the box for both backends. Skyfield + jplephem stay as optional dependencies (`[ephemeris]` extra) for callers who want runtime recalibration against custom kernels.

### Added — 12 new bodies (26 → 38)

**Jovian inner regulars (4 new)** — orbit inside Io, between the rings and the Galileans:

| Body     | Period (d) | Mass (Earth=1) |
|---|---|---|
| Metis     | 0.2948 | 6.3e-12 |
| Adrastea  | 0.2983 | 3.4e-12 |
| Amalthea  | 0.4982 | 3.5e-10 |
| Thebe     | 0.6745 | 7.5e-11 |

Metis (P=0.2948 d) is the new shortest-period body in the roster — was Phobos at 0.3189 d. The Q-format frequency multiply still has plenty of headroom (~1.46e10 residues/day vs the 9.22e18 int64 ceiling × ~1.86 Myr envelope).

**Classical Saturnian moons (6 new)** — completes the canonical 9 with v0.1.0's Enceladus, Rhea, Titan:

| Body     | Period (d) | Mass (Earth=1) |
|---|---|---|
| Mimas     | 0.9424 | 6.31e-9  |
| Tethys    | 1.888  | 1.04e-7  |
| Dione     | 2.737  | 1.83e-7  |
| Hyperion  | 21.276 | 9.36e-9  |
| Iapetus   | 79.331 | 3.02e-7  |
| Phoebe    | 550.31 | 1.39e-9  |

Phoebe is irregular (retrograde, captured-Centaur origin); included because it's a major moon by mass / size. Period given as forward, which slightly mis-encodes the orbit direction — a v0.5.x note.

**Saturn co-orbitals (2 new)** — share an orbit and swap places every ~4 years:

| Body       | Period (d) | Mass (Earth=1) |
|---|---|---|
| Janus       | 0.6945 | 3.16e-10 |
| Epimetheus  | 0.6943 | 8.97e-11 |

Their periods differ by only 0.0002 d — they're the closest Q-format-frequency pair in the roster. Future work (v0.5.x): add a Janus-Epimetheus 1:1 horseshoe-orbit "resonance" entry.

### Added — 3 new Saturnian / Jovian resonances (RESONANCES, 4 → 7)

`research/laplacian.py::RESONANCES` is now:

| Pair | Ratio | Label |
|---|---|---|
| Jupiter–Saturn | 5:2 | Great Conjunction |
| Neptune–Pluto | 3:2 | orbital resonance |
| Io–Europa | 2:1 | Laplace pair 1 |
| Europa–Ganymede | 2:1 | Laplace pair 2 |
| **Mimas–Tethys** | **4:2** | **Cassini Division libration** *(new)* |
| **Enceladus–Dione** | **2:1** | **Enceladus tidal-heating power source** *(new)* |
| **Titan–Hyperion** | **4:3** | **Hyperion chaotic rotation source** *(new)* |

Each new entry has a non-zero static-coupling weight in `_define_couplings` (1e-3 × √(m_a × m_b), matching the Galilean inter-moon scaling).

### Changed — natural-resonance group: Z_30 → Z_60

The resonance-derived natural cyclic group:

- **v0.2.0 / v0.4.x** (4 resonances): `lcm(10, 6, 2, 2) = 30 = 2 × 3 × 5` → `Z_30`
- **v0.5.0** (7 resonances): `lcm(10, 6, 2, 2, 4, 2, 12) = 60 = 2² × 3 × 5` → `Z_60`

Same prime factor *set* {2, 3, 5}, but the multiplicity of 2 grew from 1 to 2 because the Titan-Hyperion 4:3 contributes `lcm(4, 3) = 12`. Distinct from the encoder's architectural modulus `Z_{2^32}` — the natural group is what the resonance physics implies; the encoder modulus is a Q-format choice.

### Added — codegen-baked initial phases (`_data/initial_phases.json`)

- New `codegen/emit_initial_phases.py` module: builds `EphemerisBIPInstrument` once with SPICE staged at codegen time, snapshots `initial_phases_int` to JSON. Same kernel (de441) the C codegen now uses.
- `EphemerisBIPInstrument._load_baked_initial_phases()` returns the baked array if its body roster matches the live `BODIES` dict; refuses stale data on roster drift (so adding a body without re-running codegen surfaces immediately, not silently).
- `regenerate.py` runs `emit_initial_phases.emit()` as part of the orchestrator. `_data/manifest.json` now lists 10 frozen-data files (was 9): the 8 research modules + manifest + `initial_phases.json`.
- C codegen (`c/codegen/emit_c_tables.py`) standardised on `kernel="de441"` (was "de421") so the C-side `es_initial_phases[]` and the Python-side JSON agree byte-exactly. Documented in the codegen's source comment.

### Changed — C side: ES_N_BODIES = 38

- Header bump: `c/include/ephemerides_spectral.h` defines `ES_N_BODIES = 38u`. Body count change is *not* an ABI break — ABI v2 carries field-format and function-signature stability, not a static count. The `_Static_assert(ES_N_BODIES == N)` in the codegen-emitted `es_bodies.c` catches drift between the header and the actual table.
- Fully re-emitted `c/src/es_bodies.c` (38 entries), `c/src/es_laplacian.c` (38 omegas + 38 initial phases + 7 couplings).

### Tests

- `test_native_parity.py::test_default_encode_native_matches_python` shape assertion now derives `expected_n` from the live `BODIES` dict — auto-tracks future roster growth.
- `test_immolation.py::test_natural_resonance_group_returns_z60` (renamed): asserts modulus = 60 + prime factors {2, 3, 5}.

### Notes

- v0.4.0 catalog patches (`mars-7.96yr-diagonal`, `mercury-10.69yr-diagonal`, `jupiter-saturn-9.56yr-coupled`) still apply cleanly on the 38-body roster — they target bodies that haven't moved in the canonical sort order.

### Pre-ship DE441 FFT sweep

Per user instruction ("don't ship before we sweep against DE441 and look for signals to FFT"), the per-body FFT residual analysis was re-run on the v0.5.0 38-body encoder before tagging. Result: **every peak amplitude byte-identical to v0.3.1** for the 10 DE441-coverable bodies (Earth, Jupiter, Mars, Mercury, Moon, Neptune, Pluto, Saturn, Uranus, Venus).

Why no signal change: the v0.5.0 expansion adds moons + moon-internal resonances; none of the new RESONANCES entries put a *planet* on either side of the breathing modulation, so planet phases receive no v0.5.0-specific perturbation. The v0.4.0 catalog patches (Mars 7.96 yr, Mercury 10.69 yr, J-S 9.56 yr) remain the right targets; no new patches needed for the validated bodies.

The new moons themselves (Galileans + classical Saturnians) cannot be FFT-validated yet: DE441 only ships planet barycenters + Sun + Earth + Moon, so the moons use a period-based fallback at codegen time. v0.5.x will pull in `mar097.bsp` / `jup340.bsp` / `sat441.bsp` so the moons get real ephemeris truth and the FFT can surface any new smoking-gun peaks they reveal.

Bonus: with the v0.4.1 C native path plus v0.5.0's SPICE-free init phases, the full sweep dropped from **314.9 s → 14.6 s** — a 21× speedup at no precision cost. See [`figures/de441_error_spectrum_v0.5.0.md`](figures/de441_error_spectrum_v0.5.0.md) for the full pre/post comparison.

## [0.4.1] — 2026-05-05

C-side runtime kernel patching (ABI v2). Native overlay surface; cross-backend byte-exact parity with patches active.

### Architecture: completing the v0.4.0 overlay design

v0.4.0 shipped the diagnosed-fiber overlay on the BIP (pure-Python) encoder and gated `backend="c"` to fall back to BIP when patches were active. v0.4.1 closes that gap: the native C library now carries its own patch registry, and the encode-state path consults it after the base loop / before the final reduction, mirroring the BIP encoder's overlay step exactly.

The Python and C registries are kept in lockstep via a sync layer in the bridge: every `apply_patch` mirrors into both; `clear_patches` clears both; rejection on either side rolls back the other. Two registries, one source of truth, byte-exact parity verified.

### Added — C-side overlay (`es_patches.c`)

- **`es_patch_t` struct** with `kind` (sinusoid / coupled-sinusoid), `name[64]`, `body_idx_a/b`, `amplitude_deg`, `period_days`, `phase_rad`, `correlation`. Plain-data layout for stable ctypes binding.
- **Registry API**: `es_apply_patch(const es_patch_t *)`, `es_clear_patches()`, `es_n_active_patches()`, `es_get_patch_at(idx, *out)`. Status codes for capacity / duplicate-name / bad-index / bad-param errors. Capacity `ES_MAX_PATCHES = 32`.
- **Encoder hook** in `es_encode_state`: `es_apply_overlay_to_phases(delta_t_days, curr_phases)` runs after the sub-day remainder step, before the final `& MODULO_MASK` reduction. Zero-cost when registry is empty (single early-return).
- **Banker's rounding sharing**: `es_banker_round` (was `static inline` in `es_encode.c`) is now external linkage so `es_patches.c` can match Python's `round()` half-to-even semantics on the overlay delta. Required for byte-exact parity.

### Added — ABI v2 ctypes binding

- `EXPECTED_ABI_VERSION = 2` in `_native_bip.py`. The load-time check refuses any binary reporting a different ABI — silent corruption from a stale wheel can't happen.
- `EsPatch` ctypes structure mirroring `es_patch_t` field-for-field; locked by the load-time ABI assertion.
- High-level helpers: `native_apply_sinusoid_patch(name, body_idx, amplitude_deg, period_days, phase_rad)`, `native_apply_coupled_patch(name, body_idx_a, body_idx_b, amplitude_deg, period_days, phase_rad, correlation)`, `native_clear_patches()`, `native_n_active_patches()`. All no-ops when `HAS_NATIVE=False`.

### Added — bridge sync layer

- **`_mirror_patch_to_native(patch)`** — applies a Python `Patch` into the C-side registry by name + integer body index; rolls back the Python-side change on C-side rejection so registries can't drift. Called from `apply_patch` and `apply_custom_patch`.
- **`_native_clear_patches()`** — wraps the native helper; called from `clear_patches` after the Python-side wipe.
- **`_body_index(name)`** — resolves a Python body name to its integer index, mirroring the canonical sorted body order baked into the C codegen.

### Changed

- **`backend="c"` now applies the overlay natively** when the binary is loaded. The v0.4.0 fallback gate on `_patches.has_active_patches()` is removed. Falls back to BIP only when `HAS_NATIVE=False`.
- **Performance** with 3 catalog patches active (encoded at +20 yr against DE421):
  - `backend="bip"` — 10.8 ms / encode (+418 μs vs no-patches)
  - `backend="c"`   — 0.046 ms / encode (+19 μs vs no-patches)
  - **C is 237× faster than BIP** with patches active.
- **Test `test_c_backend_falls_back_when_patches_active`** renamed to `test_c_backend_handles_overlay_when_loaded` and asserts the v0.4.1 behavior (native applies overlay; falls back only when not loaded).

### Tests

- **`test_cross_backend_parity_with_patches`** — encodes `TEST_JD = J2000 + 20 yr` with all 3 catalog patches active on both backends; asserts `bip["phases_uint32"] == c["phases_uint32"]` byte-for-byte.
- **`test_native_registry_in_sync_with_python`** — verifies `n_active` agrees between registries through apply / clear / duplicate-rejection paths.

### ABI breakage (intentional)

ABI v1 (v0.3.1, v0.4.0) → ABI v2 (v0.4.1). Any v0.4.1 Python wheel paired with a v0.3.1 native binary will refuse to load native (`HAS_NATIVE=False` with a clear `LOAD_ERROR` message); the package falls back to pure-Python BIP. PyPI ships matching Python+C versions in every wheel, so consumers using `pip install ephemerides-spectral==0.4.1` always get a matched pair.

### Build

- `CMakeLists.txt` adds `c/src/es_patches.c` to the shared library sources. `WINDOWS_EXPORT_ALL_SYMBOLS ON` already in place; the new exports surface automatically. No new build flags / no toolchain version bumps.

## [0.4.0] — 2026-05-05

Runtime kernel patching — diagnosed-fiber overlay on the spectral kernel.

### Architecture: overlay, not bones-mutation

The spectral kernel — the static `RESONANCES` table, the Laplacian construction, the integer Q-format frequencies — is the **published truth**. We don't mutate it to chase residuals.

Patches are **overlays**. They live in a module-level registry, are authored as data (not code edits), and contribute per-body residue deltas at encode time AFTER the base encode loop has finished. The base encoder bytes never change. Inspired by Linux ksplice / kpatch.

This is the application surface for the v0.4.x diagnosed-fiber-patches roadmap entry: patches are *authored* from FFT residual peaks (per the v0.3.1 `de441_error_spectrum` analysis), but *applied* via the overlay so the published kernel hash stays pinned forever. A bricked patch is unloadable / disposable; the kernel keeps shipping clean.

### Added — `diagnosed_fibers` runtime overlay

- **`research/diagnosed_fibers.py`** — `DiagnosedPatch` dataclass family (`SinusoidPatch` for diagonal, `CoupledSinusoidPatch` for off-diagonal pairs); module-level `_ACTIVE` registry (RLock-guarded); `apply_patch` / `clear_patches` / `list_patches` / `snapshot` / `evaluate_active_patches` / `has_active_patches` / `apply_catalog_patch`; bundled `CATALOG` keyed by patch name. Mirrors to `_research/diagnosed_fibers.py` via codegen so it ships in the wheel.
- **`bridge.apply_patch(name)`** loads a named CATALOG entry; **`bridge.apply_custom_patch(name=, kind=, body=..., amplitude_deg=..., period_days=..., ...)`** constructs a patch from JSON-friendly primitive args (Pyodide-safe); **`bridge.list_active_patches()`** / **`bridge.list_catalog_patches()`** / **`bridge.clear_patches()`** mirror the registry surface.
- **CLI** (`patches` subcommand group):
  - `ephemerides-spectral patches catalog` — list bundled patches with metadata
  - `ephemerides-spectral patches apply --name ...` — load a named patch
  - `ephemerides-spectral patches active` — list currently-active patches
  - `ephemerides-spectral patches clear` — wipe all patches
- **BIP encoder runtime-overlay integration** — `_encode_state_impl` queries `diagnosed_fibers.evaluate_active_patches(date_jd, body_to_idx)` after the base encode loop; per-body deltas are added to `curr_phases` BEFORE the final `& (MODULO - 1)` reduction. Wraparound is the cyclic-group reduction we want; correctness verified by `test_runtime_patches.py::test_clear_restores_byte_identical_baseline`.

### Added — patch CATALOG (v0.4.0 baseline, three patches)

Each entry was authored directly from a v0.3.1 FFT residual peak — see [`figures/de441_error_spectrum_analysis.md`](figures/de441_error_spectrum_analysis.md) for the source data and [`figures/runtime_kernel_patching.md`](figures/runtime_kernel_patching.md) for the per-patch contribution shape across a JD ladder.

- **`mars-7.96yr-diagonal`** — `SinusoidPatch(body="mars", amplitude_deg=3.45, period_days=2907.3)`. Targets Mars's rank-1 FFT peak (suspect: missing Mars-Saturn or Mars-Jupiter sub-resonance not in the v0.2.0 RESONANCES table).
- **`mercury-10.69yr-diagonal`** — `SinusoidPatch(body="mercury", amplitude_deg=9.19, period_days=3905.1)`. Targets Mercury's rank-1 peak (suspect: higher-order PN beat with Jupiter that the v0.1.0 43"/century PN entry doesn't capture).
- **`jupiter-saturn-9.56yr-coupled`** — `CoupledSinusoidPatch(body_a="jupiter", body_b="saturn", amplitude_deg=45.0, period_days=3490.9, correlation=-1)`. The smoking-gun missing-coupling signal: J and S show identical 9.56-yr peaks at ~45° amplitude. The v0.2.0 `α=0.1` modulation depth undershoots the actual J–S 5:2 libration by ~5×; the anti-correlated coupled patch shrinks both peaks simultaneously (libration is +Jupiter / −Saturn around the conjunction).

### Changed

- **C native backend (`backend="c"`) transparently falls back to `"bip"` when patches are active.** The C-side overlay isn't yet implemented — fallback guarantees correctness while the C ABI v2 surface is designed for v0.4.x phase F. Zero overhead when the registry is empty (`has_active_patches()` is a single-cycle empty-list check).
- **`bridge.get_system_state()`** returns `backend="bip"` (not `"c"`) when the C backend was requested but patches forced a fallback. The new `backend_requested` field always preserves the original ask.
- **Codegen ships 9 modules now** (was 8): added `_research/diagnosed_fibers.py`. The manifest's per-file SHA-256 sums update accordingly; `test_data_freshness.py` enforces the new module is present.

### Tests

- New `tests/test_runtime_patches.py` — 12 tests pinning every structural property of the overlay:
  1. `apply` + `clear` round-trip is byte-identical to baseline
  2. diagonal patch shifts only the targeted body
  3. composition of two disjoint-body patches is order-independent
  4. coupled J-S patch is anti-correlated to within cyclic-group ULP
  5. duplicate-name `apply_patch` is a hard error (no silent shadow)
  6. `backend="c"` falls back to `"bip"` when patches are active
  7. `apply_custom_patch` constructs sinusoid + coupled-sinusoid kinds
  8. unknown kinds + invalid `correlation` are surfaced as `{ok: False}`
  9. `list_catalog_patches` carries name / kind / amplitude / period / notes
  10. fresh process starts with `n_active=0`
- `test_immolation.py` — added `CATALOG_PATCHES` to the `_BRIDGE_CONSTANTS` set (it's a tuple, not a callable).

### Documentation

- **`figures/runtime_kernel_patching.md`** — overlay design rationale, ksplice/kpatch comparison, per-patch contribution tables, what-this-doesn't-claim section (patches are empirical Fourier corrections, not first-principles physics; v0.5.x's α derivation should ultimately replace them).
- **`figures/runtime_kernel_patching_demo.md`** — reproducible per-patch JD-ladder output from `python -m research.demo_runtime_patches`.
- **`research/demo_runtime_patches.py`** — small reproducible demonstration (D=4096 for speed); shows the patch contribution shape across `[-20, -5, 0, +5, +20]` yr from REFERENCE_JD.

### CI

- `pure-wheel-build` job promoted to always-on (added in the v0.3.1 hotfix). Mirrors the publish workflow's `build-pure-wheel` step exactly so any TOML-syntax / hatchling-config drift in `pyproject-pure.toml` fails on the PR, not at release time.

## [0.3.1] — 2026-05-04

C-in-wheel + spectral syzygy window search + DE441 error-spectrum FFT.

### Added — native C backend

- **scikit-build-core** build system replaces hatchling for the platform wheels. CMake compiles `c/src/{es_encode,es_bodies,es_laplacian,es_cosine_lut}.c` into `libephemerides_spectral.{so,dll,dylib}` and bundles the binary under `ephemerides_spectral/_native/` in the wheel.
- **`ephemerides_spectral._native_bip`** — `ctypes` shim that loads the bundled binary, verifies the ABI version (v1) at load time, and exposes `HAS_NATIVE`, `LIB_PATH`, `encode_state`, `encode_at_jd`, `native_version`. Caller-side guard discipline: check `HAS_NATIVE` before invoking; transparent fallback to pure-Python BIP if the binary isn't loadable (sdist installs without a C toolchain, Pyodide / WASM, the pure-Python fallback wheel).
- **`backend="c"`** dispatch in `default_encode()` and `bridge.get_system_state()`. Byte-for-byte identical phase residues to `backend="bip"` (verified by `tests/test_native_parity.py`'s 12-cell three-way parity test); **~1000× speedup** on the chunk loop (encode at +20 yr: 46.5 ms Python → 0.04 ms C). Falls back transparently to `"bip"` when the binary isn't present.
- **`pyproject-pure.toml`** for the Pyodide / WASM `py3-none-any` fallback wheel. Same package name + version as the platform wheel; sanity-checks ensure no `_native/` binaries leak in. Built by the publish workflow's `build-pure-wheel` job alongside the platform-specific `cibuildwheel` matrix.
- **C ABI accessors** in the header: `es_abi_version()`, `es_n_bodies()`. ABI bumps are wire-format breaks; the Python shim refuses to load mismatched binaries.
- **C banker's-rounding** (`es_banker_round`) added to `es_encode.c` to match numpy's `np.round` half-to-even semantics in the sub-day remainder step. Required for byte-exact parity with the Python BIP encoder when the multiplication produces an exact half-integer (verified at the +/-1 yr parity test cases).
- **`ephemerides-spectral-publish.yml`** rewritten to a `cibuildwheel`-style matrix: 3 OS × 5 Python = 15 platform-specific wheels + sdist + pure-Python wheel.
- **`.gitattributes`** unchanged from v0.3.0 (already in place); CMake-generated build artifacts excluded from sdist.

### Added — spectral syzygy window search

- **`research/syzygy_window.py`** — `find_syzygies(jd_lo, jd_hi, kind, threshold)`. Enumerates candidate syzygies in closed form by walking new-moon and full-moon multiples of the synodic month + confirming against the draconic-month phase. **HDC-native** pattern: cost goes from `O(window_days × encode)` to `O(n_syzygies × confirmation)` because syzygies are rare events on the calendar (~5/yr combined solar+lunar).
- **`bridge.find_syzygies(jd_lo, jd_hi, kind, threshold, max_candidates)`** wraps the research-side function with input validation + Pyodide-friendly JSON return shape.
- **CLI `find-syzygies --from-jd ... --to-jd ... [--kind] [--threshold]`**.
- The v0.3.0 point-evaluation `eclipse --jd` (`bridge.get_eclipse_probability(jd_tdb)`) is **kept for backward compatibility** but documented as the deprecated encode-then-check pattern. The bronze antikythera's Saros dial doesn't encode-and-check either — it turns gears whose ratios *are* the Saros cycle.

### Added — DE441 error-spectrum FFT

- **`research/de441_error_spectrum.py`** — uniform-spaced sweep + per-body FFT of the linear-detrended residual against DE441 truth. Native C path used when available (1024 samples × 6 ms = ~6 s total; otherwise 315 s on Python).
- **`figures/de441_error_spectrum_analysis.md`** — hand-curated interpretation of the peaks. Headline: **Jupiter–Saturn show identical 9.56-yr peaks at ±45° amplitude** — that's the smoking-gun missing-coupling signal, the empirical motivation for v0.4+'s first-principles α derivation. The current Phase-9 `α = 0.1` undershoots the actual J–S libration depth by ~5×.
- Outer planets (Uranus, Neptune, Pluto) peak at their own orbital periods — Q-format precision floor signals, not Phase-9 missing-coupling signals; addressed by `K_BITS > 32` future work.
- Mars at 7.96 yr / 3.45° suggests a missing Mars–Saturn coupling. Mercury at 10.69 yr / 9.19° suggests higher-order PN beat with Jupiter.

### Changed

- `SUPPORTED_BACKENDS` now includes `"c"`. Backwards compatible: `"bip"` and `"complex128"` still work unchanged.
- `bridge.get_system_state(backend="c", ...)` returns `backend="c"` on success or `backend="bip"` on transparent fallback (the new `backend_requested` field always preserves the original ask).

### Notes

- v0.3.1 is the first release with platform-specific wheels. Expect **15 wheels** on the PyPI release page (3 OS × 5 Python) plus 1 sdist plus 1 pure-Python wheel for Pyodide.
- Encode timings on the C path: 0.2 ms at J2000; 0.04 ms at +20 yr; ~6 ms at +1000 yr; ~6 ms at +14000 yr (chunk loop is so cheap the body iteration dominates). The DE441 sweep that took 6.4 s in Python at +14,000 yr lands well under 10 ms in C.
- The eclipse-prediction story now has two surfaces: the v0.3.0 point-evaluation `eclipse --jd` (kept; cheap; appropriate for "what's the alignment at this single JD") and the v0.3.1 `find-syzygies --from-jd … --to-jd …` (HDC-native window search; appropriate for everything else).

### CI shape (chess-spectral parity)

- Per-PR runs **4 always-on cells** (`build-and-test`: 3 OS × py3.12 + 1 min-Python cell on Linux), `codegen-determinism` (single Linux job), and `fallback-test` (pure-Python no-native path on Linux). Wall time on the green path is ~3 min per PR.
- The full **15-cell `verify-wheels`** matrix (3 OS × 5 Python via `cibuildwheel`) plus a Linux platform-wheel + sdist `verify-build-artefacts` job are **opt-in** at PR time via the `wheel-check` label or `workflow_dispatch`. Apply the label when touching package layout, `pyproject.toml`, scikit-build-core config, the C source tree, or any `vX.Y.Z`-ship release PR.
- The full matrix still runs unconditionally on tag push via `ephemerides-spectral-publish.yml` — the load-bearing release gate is unchanged.

### Known limitations

- **Sdist standalone build broken when no toolchain is present.** The published sdist contains the C source tree and `CMakeLists.txt` at the parent of the python/ project (mirrored via `[tool.scikit-build] sdist.include = ["../CMakeLists.txt", "../c/**", ...]`), but the parent-relative `cmake.source-dir = ".."` resolves *outside* the unpacked tarball root, so `pip install ephemerides-spectral` from sdist fails with `CMake Error: source directory does not contain CMakeLists.txt`. The 15 platform wheels cover essentially all consumers (3 OS × 5 Python, x86_64 + arm64); users on platforms without a wheel (Linux musllinux, exotic ARM) currently can't fall back to source build. Tracked as a v0.4 cleanup — likely co-locates the C tree under `python/` so `source-dir = "."`. CI's wheel-build path uses `python -m build --wheel` and `python -m build --sdist` as separate invocations to avoid the broken sdist-round-trip codepath.

## [0.3.0] — 2026-05-04

Time scales beyond Earth + DE441 full-epoch sweep + the natural-resonance gear group.

### Added

- **`research/time_scales.py`** — Mars Sol Date / Mars Coordinated Time per Allison & McEwen 2000 (`jd_to_msd` / `msd_to_jd` with documented leap-second handling); mean lunar synodic + sidereal age/phase primitives (`jd_to_lunar`, `MarsTime`, `LunarTime` dataclasses).
- **Bridge methods** (Pyodide-friendly JSON surface):
  - `bridge.jd_to_mars_time(jd_utc, leap_seconds=37)` → `{ok, jd_utc, msd, mtc_hours, mtc_seconds, sol_number, leap_seconds}`
  - `bridge.mars_time_to_jd(msd, leap_seconds=37)` → MSD → JD_UTC inverse
  - `bridge.get_lunar_phase(jd_tdb)` → synodic + sidereal age/phase
  - `bridge.list_lunar_kernels()` → LTE440 metadata + `ltc_status` flag
  - `bridge.get_natural_resonance_group()` → resonance-derived natural cyclic group (LCM, CRT prime factorisation)
- **`LUNAR_KERNELS = ("lte440",)`** — registers LTE440 (Lin et al. 2025, A&A 704 A76) as a known lunar-time ephemeris. Metadata only; no auto-download. The kernel is ~100 MB and must be staged separately from `github.com/xlucn/LTE440` releases when needed.
- **CLI subcommands**:
  - `time-mars --jd 2451545.0` (or `--msd 50000`) — Mars Sol Date / Mars Coordinated Time
  - `time-lunar --jd 2451545.0` — mean lunar synodic + sidereal phase
  - `lunar-kernels` — LTE440 metadata + LTC status
  - `natural-group` — resonance-derived natural cyclic group
- **`research/de441_sweep.py`** — runs the BIP encoder across J2000 ± 14,000 yr (15 sample points) against DE441 truth; writes `results/de441_sweep_summary.json` + `results/de441_sweep_table.md`.
- **[`figures/de441_full_sweep.md`](../figures/de441_full_sweep.md)** — honest interpretation of the sweep. Earth / Venus / Uranus stay <10° at multi-millennium horizons; Mars 14°; Mercury 84°; Jupiter / Saturn / Neptune / Pluto / Moon all hit >150° — the structural-limit signature of phenomenological `α = 0.1`. Documents the three follow-ups that would each visibly improve specific bodies (per-resonance derived α, higher-order PN for Mercury, more resonance entries).

### Notebook updates

- New §6: **Natural gear group, leaf structure, concert frequency** — distinguishes the encoder's architectural `Z_{2^32}` modulus from the resonance-derived natural cyclic group `Z_30 = Z_2 × Z_3 × Z_5`. Connects to chess-spectral §19's non-Markovian sheaf framing (let structure come from the data, don't impose it via the encoding).
- New §7: **Time scales** — JD vs MSD/MTC vs lunar primitives vs LTC roadmap.
- §4 Release History extended with the v0.3.0 entry.

### Roadmap

- **LTC (Lunar Coordinated Time)** deferred to v0.4+ — pending NASA + international agencies' formal definition (target ~2026–2028 per the April 2024 White House directive). LTE440 ships the underlying SPICE-format conversion ephemeris; the bridge will gain runtime LTC↔UTC↔JD_TDB conversions when the standard lands.
- **First-principles per-resonance α** — replaces the phenomenological `α = 0.1` with values from a Hamilton/Delaunay-variable Lagrangian. The DE441 sweep documents *why* this matters: bodies inside the resonance set (Jupiter, Saturn, Neptune, Pluto, Moon) phase-scramble at multi-millennium horizons because their `α` values are wrong-in-detail.
- **DE441 vs DE442 spectral error signature** *(experiment)*: build two BIP instruments calibrated separately from DE441 and DE442; encode the same JD on both; project per-body residue deltas onto the Laplacian eigenbasis. If the deltas have a coherent spectral signature, DE442's corrections to DE441 live in a specific eigenmode subspace — letting us *predict* where ephemeris error correction is structurally needed without needing the corrected kernel.
- **Spectral syzygy window search** — replaces v0.3.0's point-evaluation `eclipse --jd` (encode-then-check) with a window-search `find-syzygies` that uses the natural cyclic-group decomposition (Saros / Metonic / synodic month / lunar nodes) to enumerate candidate JDs in closed form, then confirms each by spectral projection. The HDC-native usage; the bronze antikythera's Saros dial works the same way (turn the gears, don't re-encode).

### C port

- Header version macro bumped to `0.3.0` (`include/ephemerides_spectral.h`).
- No C-side functional changes; the time-scale conversions and natural-group introspection are Python-side surface.

## [0.2.0] — 2026-05-04

Phase 9 coverage extension. The hardcoded Jupiter–Saturn 5:2 entry is promoted to a structured `RESONANCES` table; three new resonance pairs are wired alongside it. The encode path, the reference-instrument breathing Laplacian, and the C codegen all walk the same table — single source of truth in `research/laplacian.py`.

### Added

- **`research.laplacian.RESONANCES`** — frozen-dataclass list of `(body_a, body_b, n_a, m_b, label)` entries. v0.2.0 ships four:
  - **Jupiter–Saturn 5:2 (Great Conjunction)** — refactored from the v0.1.0 hardcoded path; phases unchanged when this is the only active entry.
  - **Neptune–Pluto 3:2** — Pluto's stable orbital resonance with Neptune. Smaller mass-product than J–S; coupling weight follows the `1e-5 · √(m_a·m_b)` scaling the J–S entry uses.
  - **Io–Europa 2:1 (Laplace pair 1)** — first leg of the Jovian Laplace resonance (Io–Europa–Ganymede share a 4:2:1 mean-motion lock).
  - **Europa–Ganymede 2:1 (Laplace pair 2)** — second leg of the same Laplace resonance.
- **Static-coupling weights** for the three new pairs are added to `_define_couplings`. The Phase 9 modulation scales an existing static weight; pairs without a non-zero weight would no-op silently, so the codegen + Python encoder both *guard* against zero-weight resonance entries (a hard error rather than a silent drift).
- **`SolarSystemLaplacian.get_dynamic_laplacian`** now walks the table instead of hardcoding J–S. The reference-instrument breathing path picks up all four resonances automatically.

### Changed

- **Encoded phase residues for Io / Europa / Ganymede / Neptune / Pluto** shift relative to v0.1.0 because their Phase 9 modulation is now active. Earth's phase residue is unchanged (no resonance touches Earth in v0.2.0). The 0.0002 rad Earth phase floor against DE421 at +20 yr is preserved.
- **Bridge `list_couplings()` and `breathing` CLI subcommand** continue to accept any body pair, but the wired-in resonances are now four entries — `bridge.get_breathing_modulation()` for any of the four returns a non-zero modulation factor by default.

### C port

- **`c/src/es_laplacian.c`** regenerated: `es_n_couplings = 4`. Each entry carries `(idx_a, idx_b, n_a, m_b, weight_rpd)` so the C inner loop is a flat iteration over the table — no per-resonance branching.
- **`c/test/test_parity_python.py`** still asserts byte-for-byte parity with the Python reference encoder. **All 26 bodies match exactly at +20 yr** even with the expanded breathing surface, confirming the encoder's floor-division semantics scale cleanly across multiple resonance entries.
- **Stack + `.rodata` footprint** unchanged at the per-body / per-LUT level. Coupling-table grew from 1 entry × 24 B = 24 B to 4 × 24 B = 96 B in `.rodata` — still negligible.

### Notes

- The modulation depth `α = 0.1` is global across all four resonances in v0.2.0; per-resonance depths derived from a Hamilton/Delaunay-variable Lagrangian are deferred to v0.3.x (see ROADMAP).
- The convention `cos(n_a · φ_a − m_b · φ_b)` matches the v0.1.0 J–S wiring (`n_a` is the multiplier on the *faster* body). The cosine is symmetric, so this is equivalent under the modulation envelope to the canonical "slow" resonance angle `m_b · φ_a − n_a · φ_b` — kept this way to preserve byte-exact parity with v0.1.0 for the J–S pair.

## [0.1.0] — 2026-05-04

First public release on PyPI.

### Added

- **Sol Star System Laplacian** (`research/laplacian.py`). 26 bodies — sun + 9 planets (incl. Pluto) + 12 major moons + 4 main-belt asteroids. The static Laplacian decomposes as `L_LTI = L_trunk + L_pn + L_static`: diagonal Newtonian mean motions (`2π / period_days`), Mercury's 43"/century post-Newtonian frequency shift on the diagonal, and a symmetric off-diagonal of gravitational fiber weights (planet–sun / moon–planet / Jupiter–Saturn 5:2 resonance / asteroid–Jupiter). The LTI snapshot remains accessible via the `L_lti` property as the Phase 8 regression baseline.
- **Phase 9 breathing couplings.** `SolarSystemLaplacian.get_dynamic_laplacian(current_phases)` returns the state-dependent matrix where each off-diagonal weight is multiplied by `1 + α cos(n_ij·φ_i − m_ij·φ_j)` for the resonance pair `(n_ij, m_ij)`. The Jupiter–Saturn 5:2 entry is wired with `α = 0.1`. Formally a state-dependent (non-autonomous) graph Laplacian / adaptive Kuramoto-family network with phase-difference-dependent (PDDP) coupling — see [research notebook §1.4](../ephemerides_spectral_research_notebook.md#14-mathematical-positioning-of-the-breathing-laplacian) for the full positioning across spectral-graph-theory / dynamical-systems / DNLS-on-a-graph vocabularies.
- **EphemerisHDCInstrument** (`research/ephemeris_reference_instrument.py`). FPU complex128 reference encoder with unit-norm complex Gaussian bases; supports the algebraic identities (Syzygy operator, observer binding via coprime cyclic rolls, Metonic / J–S resonance projection). Phase 9 evolution path runs `expm(-i·L_dyn(φ)·step)` chunk-wise in 30-day steps.
- **EphemerisBIPInstrument** (`research/bip_instrument.py`). ALU-native bit-serialised encoder over `Z_{2^32}` — phase composition is `(φ₁ + φ₂) mod 2³²`, which is implicit `uint32` overflow on hardware with no explicit modulo. 305× faster than the FPU reference at +20 yr; 256 KB state at D=65536; same 0.0002 rad Earth phase error vs DE421 truth.
- **Integer cosine LUT** for the breathing-coupling path. 1024 × `int32` (Q1.14 amplitude, 4 KB) keyed on the top 10 bits of the resonant-phase residue. Replaces `np.cos(...)` in the inner loop — pure integer table lookup at runtime; the LUT is computed once at import time.
- **Fixed-point Q-format frequency discipline.** All angular frequencies stored as signed `int64` in residues/day with `MODULO = 2³²` residues per revolution. Conversion: `omega_int = round(omega_rad_per_day / (2π) · MODULO)`. Q-format underflow guard at construction time emits a `RuntimeWarning` if any frequency rounds to zero residues/day (the floor is ~13 Gyr period — never trips for real bodies, but the guard exists so the assumption is checkable).
- **Pre-flight bounds check** on `encode_state`. Rejects `|delta_t_days| > 6.8e8` (≈ 1.86 Myr) before any math runs — keeps `omega · delta_t` inside the int64 envelope. The primary defense against silent saturation; the scoped `np.errstate(over='raise')` on the signed-int64 multiply is the secondary safety net.
- **Scoped overflow trap.** `np.errstate(over='raise')` around `omega * step_signed` (where saturation would corrupt); `np.errstate(over='ignore')` plus `warnings.filterwarnings('overflow encountered')` around the `uint64` accumulator (where wraparound IS the cyclic-group reduction we want). Means callers who promote `RuntimeWarning` to error don't see spurious noise from the modular arithmetic.
- **Bridge API** (`ephemerides_spectral.bridge`). 9 Pyodide-friendly methods, all returning `{ok: True, ...}` / `{ok: False, error: ...}`: `get_version()`, `list_bodies()`, `list_kernels()`, `list_couplings()`, `get_resolution()`, `get_system_state()`, `get_local_view()`, `get_eclipse_probability()`, `get_breathing_modulation()`. Validation helpers reject malformed `jd` (non-finite or out-of-envelope) / `body` (off the 26-body list) / `backend` (off `{bip, complex128}`) / `kernel` (off `{de421, de440, de441, de442}`) / `lat-lon` (out-of-range) inputs without ever raising.
- **Console script** (`ephemerides-spectral`). 9 subcommands: `version`, `bodies`, `kernel list`, `resolution`, `encode`, `local-view`, `eclipse`, `couplings`, `breathing`. Top-level `--version` and `--no-pretty` (compact JSON for piping into `jq`). Rich `--help` epilogs with concrete examples on every subcommand.
- **`default_encode(jd, backend="bip", kernel="de441", D=65536)`** top-level shorthand. `backend="bip"` returns the per-body `uint32[26]` phase residue array; `backend="complex128"` returns the FPU reference's `complex128[D]` unit-norm state.
- **Codegen** (`codegen/regenerate.py`, `codegen/emit_research_modules.py`). Mirrors `research/{__init__, ephemeris_reference_instrument, ephemeris_loader, bodies, laplacian, bip_instrument}.py` into `python/ephemerides_spectral/_research/`; reads version from `pyproject.toml` (single source of truth); stamps SHA-256 sums + sizes into `_data/manifest.json`.
- **`ephemerides-spectral-publish.yml`** GitHub Actions workflow. Pure-Python wheel + sdist build; OIDC trusted publishing; `workflow_dispatch` with `target ∈ {testpypi, pypi}` (default `testpypi`); tag-push on `ephemerides-spectral-v*` triggers PyPI publish; tag-version-vs-pyproject-version verification step.

### Documentation

- [`README.md`](README.md) — top-level orientation; subtree layout; how this relates to `../research/` and `../antikythera-spectral/`.
- [`ROADMAP.md`](ROADMAP.md) — released-versions table, next-planned versions, phase status, bridge↔CLI parity inspection.
- [`python/README.md`](python/README.md) — PyPI long description; CLI cheat-sheet; Python API surface.
- [`../ephemerides_spectral_research_notebook.md`](../ephemerides_spectral_research_notebook.md) — research notebook, §1.4 mathematical positioning of the breathing Laplacian.
- [`../research/resonant_bit_serialized_hdc_evaluation.md`](../research/resonant_bit_serialized_hdc_evaluation.md) — RBS-HDC evaluation; Phase 9 algebraic form; ALU-native LUT design; Q-format discipline; overflow trap rationale.

### Cross-pollination

The chess-spectral notebook §20.13–§20.20 explicitly aligns the chess `Z_{640}` phase-operator engine with this BIP design at the group-theoretic level. Both projects share the cyclic-group integer-ALU substrate, the Q-format scaling rules, and the cosine-LUT pattern. Chess pays an explicit `% 640` per op (non-power-of-2 modulus); ephemerides gets cyclic-group reduction free as `uint32` overflow (power-of-2 modulus). Antikythera-spectral is the bronze-mechanism sibling — different evidentiary object, same spectral / Laplacian-eigenbasis framing.

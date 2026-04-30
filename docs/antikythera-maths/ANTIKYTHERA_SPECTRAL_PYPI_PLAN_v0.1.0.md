# `antikythera-spectral` v0.1.0 — PyPI packaging plan

**Status:** PLAN (draft, not yet implemented).
**Owner:** sckirklan@gmail.com
**Date drafted:** 2026-04-29
**Mirrors:** [docs/chess-maths/chess-spectral/](../chess-maths/chess-spectral/) layout, codegen pattern, and publish workflow.

> **Scope note.** This plan folds the originally-planned v0.2 feature set into v0.1.0 per the user's "do v0.1 up to v0.2 in one go" decision. The result is a substantive first release rather than a minimal one. v0.3 candidates remain deferred (§11).

---

## 1. Goal

Package the Antikythera HDC research scaffold (`docs/antikythera-maths/research/`, 25 modules, ~6 200 LOC) as a single PyPI distribution **`antikythera-spectral`** that:

- Installs cleanly with `pip install antikythera-spectral`.
- Runs in **Pyodide / micropip** so a web app can drive a digital Antikythera in-browser without a Python server.
- Exposes a **Bridge API** (~28 methods) for web/UI consumers (mirrors the chess-spectral `qm_4d_bridge.py` pattern: each method returns a Pyodide-JSON-serializable dict with `'ok'`).
- Ships a **CLI** (`antikythera-spectral encode --jd 1684500.0`) symmetric with the chess-spectral CLI.
- Ships **codegen** (`codegen/` directory, mirrors chess-spectral) that emits frozen JSON / NPZ data tables from the research-scaffold sources at build time, with provenance stamping.
- Has a **PyPI publish workflow** triggered by `antikythera-spectral-v*` tags via OIDC trusted publishing.
- Is covered by **CodeQL** with proactive mitigations for the URL-download / clear-text-logging false positives we hit during the v0.2.0 research-scaffold work.

v0.1.0 is **read-only and pure-Python.** No native C binaries (the encoder isn't a hot path; see §A). Single hatchling wheel.

---

## 2. What's IN v0.1.0 (folded scope)

The v0.1.0 release is a feature-complete read-only digital Antikythera. Concretely:

- **HDC encoder + decoder** (round-trip, all three D variants) via facades over `research/`.
- **Date↔JD conversion** in four calendar systems (Gregorian, Julian, Athenian archonships + Attic months, Olympiad years).
- **Visibility & heliacal events** via skyfield (rising / setting / solar elongation per planet).
- **Eclipse search** over arbitrary date bands (sky-driven enumeration; built on `sky_driven_validation.py`).
- **Operator simulation** of the §11.6.16 workflow (re-anchor at heliacal rising, propagate, repeat) — both stateless API and step-walkthrough variant.
- **Reconstruction switcher** — Freeth 2021 vs Wright vs Price 1974 dial readings side-by-side at any date.
- **What-if encoder** — re-encode a dial with arbitrary user-supplied gear ratio (proxy for missing-gear exploration).
- **Archaeological mode** — fragment-keyed inventory of attested vs reconstructed gears.
- **DE-kernel comparator** (DE421 / DE422 / DE441 / DE441_part1 etc.) — body position delta in arcsec, km, AU.
- **Model comparator** — uniform vs Hipparchus epicycle vs Ptolemy equant residuals against ephemeris truth.
- **Babylonian Goal-Year overlay** — given a planet+date, return the prediction a Babylonian astronomer would have made from the N-year cycle (folded from v0.3).
- **Pointer-animation export** — time-series ψ over a date range, exportable as JSON / NPZ / `.spectral`-style file for a viewer.
- **Hypothesis battery** — run all 31 H-rows, return as JSON; per-hypothesis lookup.
- **Frozen reference data** — cycles, gears (3 reconstructions), Hellenistic eclipse anchors, MUL.APIN + Almagest period relations — all as `_data/*.json` with provenance manifest.

## 2.1 What v0.1.0 explicitly does NOT include

- **No native C accelerator.** The encoder is not a hot path; pure Python is fast enough. See §A.
- **No PWA / web frontend.** The Bridge API is the contract a frontend would consume; the frontend itself is a separate project.
- **No bundled ephemeris.** DE441 is ~3 GB; opt-in download only (already implemented in `ephemeris_loader.py`).
- **No mutating global state.** Every bridge method is a pure function. Operator-session "state" is returned to the caller as a plain dict; the caller chooses whether to round-trip it.
- **No live haptic-driver integration.** The `lemonforest/mlehaptics` haptic-firmware project is unrelated.
- **No multi-language bindings.** Pyodide IS the JS surface. We don't ship a TS port.

---

## 3. Repo layout

Mirrors `docs/chess-maths/chess-spectral/` *minus* the C-binary tree. Codegen and bridge sub-trees match exactly:

```
docs/antikythera-maths/antikythera-spectral/
├── README.md                       # GitHub-tree browser landing (project overview, links to subtrees)
├── CHANGELOG.md                    # v0.1.0 entry; future versions append
├── ROADMAP.md                      # status of advertised CLI/Bridge methods (mirrors chess-spectral/ROADMAP.md)
│
├── bridge/                         # standalone bridges (run as scripts, not imported by the wheel)
│   └── ephemeris_bridge.py         # the ONE place that owns URL → BSP-file download
│                                   # (analogue of chess-spectral/bridge/pgn_bridge.py)
│
├── codegen/                        # mirrors chess-spectral/codegen/; emits frozen data into _data/
│   ├── emit_cycles.py              # research.astronomical_cycles → _data/cycles.json
│   ├── emit_gears.py               # research.gear_database → _data/gears.json (3 reconstructions)
│   ├── emit_anchors.py             # research.hellenistic_eclipses → _data/anchors.json
│   ├── emit_periods.py             # research.historical_periods → _data/periods.json
│   ├── emit_basis_vectors.py       # deterministic HDC channel bases → _data/basis_*.npz
│   ├── emit_fragment_inventory.py  # research.gear_database → _data/fragments.json
│   └── regenerate.py               # orchestrator; re-emits everything with source-commit stamping
│
├── docs/
│   ├── bridge_api.md               # Pyodide bridge contract (~28 methods)
│   ├── DELTA_T_MODEL.md            # ΔT discussion; why -200 BCE has ±3 hr uncertainty
│   ├── EPHEMERIS_KERNELS.md        # which kernels exist, sizes, eras, when to use which
│   ├── CALENDAR_SYSTEMS.md         # Gregorian / Julian / Athenian / Olympiad reference + caveats
│   ├── OPERATOR_WORKFLOW.md        # the §11.6.16 re-anchoring loop, with worked example
│   └── adr/
│       ├── 0001-pure-python-only-v0.1.md
│       ├── 0002-bridge-api-shape.md
│       ├── 0003-ephemeris-allowlist-codeql.md
│       ├── 0004-frozen-data-as-json-not-pickle.md
│       ├── 0005-codegen-no-c-yet.md
│       ├── 0006-stateless-bridge-no-server-state.md
│       ├── 0007-athenian-calendar-conversion-fidelity.md
│       ├── 0008-whatif-mode-bounded-input.md
│       ├── 0009-single-branch-rollout.md
│       └── 0010-testpypi-pre-merge-gating.md
│
└── python/
    ├── pyproject.toml              # hatchling, pure-Python wheel; readme = "README.md" → this dir's README
    ├── README.md                   # **PyPI long-description** (this is what shows on pypi.org/project/antikythera-spectral/)
    ├── CHANGELOG.md                # symlinks / mirrors the parent CHANGELOG
    │
    ├── antikythera_spectral/
    │   ├── __init__.py             # version, public API surface, lazy re-exports
    │   ├── cli.py                  # `antikythera-spectral` console script entry
    │   ├── bridge.py               # the Bridge API (§5)
    │   │
    │   ├── encoder.py              # facade over research.encode_ant
    │   ├── decoder.py              # facade over research.dial_decoder
    │   ├── dials.py                # facade over research.astronomical_cycles
    │   ├── render.py               # facade over research.rendering
    │   ├── hypotheses.py           # H-battery runner facade
    │   ├── ephemeris.py            # facade for research.ephemeris_loader
    │   ├── eclipses.py             # frozen-data accessor (Hellenistic anchors)
    │   ├── periods.py              # frozen-data accessor (MUL.APIN + Almagest)
    │   ├── gears.py                # frozen-data accessor (Freeth/Wright/Price)
    │   │
    │   ├── visibility.py           # NEW: heliacal rising/setting + invisibility windows
    │   ├── compare.py              # NEW: DE-kernel comparator + model comparator
    │   ├── dates.py                # NEW: 4-calendar conversion (Gregorian/Julian/Athenian/Olympiad)
    │   ├── eclipses_search.py      # NEW: sky-driven eclipse enumeration over date bands
    │   ├── operator.py             # NEW: §11.6.16 operator-workflow simulation
    │   ├── reconstructions.py      # NEW: side-by-side Freeth/Wright/Price comparator
    │   ├── whatif.py               # NEW: arbitrary-gear-ratio re-encoder
    │   ├── archaeology.py          # NEW: fragment-keyed gear inventory
    │   ├── goalyear.py             # NEW: Babylonian Goal-Year overlay
    │   ├── animation.py            # NEW: time-series ψ export
    │   │
    │   ├── version.py              # __version__ = "0.1.0"
    │   ├── py.typed                # PEP 561 marker
    │   │
    │   └── _data/                  # codegen output, shipped in the wheel
    │       ├── cycles.json
    │       ├── gears.json
    │       ├── anchors.json
    │       ├── periods.json
    │       ├── fragments.json
    │       ├── basis_vectors_d940.npz
    │       ├── basis_vectors_d13440.npz
    │       └── manifest.json       # version, source-commit hash, generation date
    │
    └── tests/
        ├── test_bridge_round_trip.py
        ├── test_encoder_facade.py
        ├── test_visibility.py
        ├── test_compare_kernels.py        # SKIPS if no kernel on disk
        ├── test_compare_models.py
        ├── test_dates.py                  # 4-calendar round-trip
        ├── test_eclipses_search.py        # SKIPS if no kernel
        ├── test_operator_workflow.py      # § 11.6.16 walkthrough golden-output
        ├── test_reconstructions.py
        ├── test_whatif.py
        ├── test_archaeology.py
        ├── test_goalyear.py
        ├── test_animation_export.py
        ├── test_codeql_allowlist.py
        ├── test_pyodide_compat.py         # imports without skyfield/scipy
        └── test_data_freshness.py         # codegen output matches research/ source
```

The package is single-namespace `antikythera_spectral` (chess-spectral has two; we don't need `_4d`).

---

## 4. Dependency surface

```toml
[project]
name = "antikythera-spectral"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = ["numpy>=1.24"]

[project.optional-dependencies]
ephemeris  = ["skyfield>=1.46", "jplephem>=2.21"]
plot       = ["matplotlib>=3.7"]
hypotheses = ["scipy>=1.10"]                       # chi2 for H-H1 cross-reference
all        = ["antikythera-spectral[ephemeris,plot,hypotheses]"]
```

**Pyodide compatibility:** numpy, skyfield, jplephem, matplotlib, scipy all available in Pyodide. The package imports lazily — `import antikythera_spectral` does not pull skyfield, scipy, or matplotlib. Pyodide users install with `micropip.install("antikythera-spectral[ephemeris]")` to get the kernel-backed methods.

**No `requests` / no urllib at import time.** The only network call is `ephemeris_bridge.py` and `compare.py`'s opt-in `download_kernel()`, both gated behind explicit user invocation (§7).

---

## 5. Bridge API (~28 methods)

`antikythera_spectral.bridge` exposes ~28 methods. Each returns `{"ok": True, ...}` on success, `{"ok": False, "error": "..."}` on caller-side input error, raises on unexpected failure. Numpy arrays in return values are real-valued (`Float32` for amplitude payloads) so Pyodide can hand them to JS `Float32Array` without conversion.

### 5.1 State ← date

| Method | Returns |
|---|---|
| `get_dial_state(jd_tdb)` | per-dial residues + total HDC state vector |
| `get_dial_angle(jd_tdb, dial)` | scalar angle ∈ [0, 360) for one dial |
| `get_pointer_xy(jd_tdb, *, layout='dial' \| 'spatial')` | `{dial_name: (x, y)}` for rendering |
| `get_all_dial_metadata()` | list of supported dials + cycles + reconstruction |
| `get_version()` | `{version, build, source_commit, data_manifest}` |

### 5.2 Date ← state

| Method | Returns |
|---|---|
| `decode_dial(state_vec, dial)` | recovered residue (B-H3 round-trip) |
| `decode_to_jd(state_vec)` | best-fit JD given the full state |

### 5.3 Calendar conversion (folded from v0.2)

| Method | Returns |
|---|---|
| `jd_to_gregorian(jd_tdb)` | `{year, month, day, hour, minute, second, era}` |
| `gregorian_to_jd(year, month, day, hour=0, minute=0, second=0, era='CE')` | JD |
| `jd_to_julian_calendar(jd_tdb)` | Julian-calendar date (relevant pre-1582) |
| `jd_to_athenian(jd_tdb, *, archon_table='attic')` | `{archonship, attic_month, day}` (Greek-era format) |
| `jd_to_olympiad(jd_tdb)` | `{olympiad_number, year_in_olympiad}` (Antikythera back-dial format) |

### 5.4 Astronomical observables

| Method | Returns |
|---|---|
| `get_visibility_windows(jd_lo, jd_hi, planet)` | list of (heliacal_rising_jd, heliacal_setting_jd) windows where planet is observable |
| `get_next_heliacal_rising(jd, planet)` | next JD when planet emerges from solar glare |
| `get_solar_elongation(jd, planet)` | scalar degrees |
| `get_eclipse_anchors(era='hellenistic' \| 'modern')` | frozen list of anchors with citations |
| `get_period_relations(source='mulapin' \| 'almagest')` | frozen list of period relations with confidence tags |
| `find_eclipses(jd_lo, jd_hi, *, kind='lunar' \| 'solar' \| 'all')` | list of eclipses with type/JD/peak-magnitude (folded from v0.2) |

### 5.5 Operator workflow (§11.6.16; folded from v0.2)

Stateless: every method takes the prior `OperatorState` dict in and returns a new one out. No server-side mutation.

| Method | Returns |
|---|---|
| `start_operator_session(initial_jd, *, dials='all')` | initial `OperatorState` dict |
| `operator_advance(state, delta_days)` | next `OperatorState` + per-planet visibility flags |
| `operator_observe(state, planet, observed_residue)` | re-anchored `OperatorState` + calibration delta |
| `operator_diagnostics(state)` | per-dial drift since last anchor + time-since-anchor |
| `set_anchor(dial, jd, observed_residue)` | per-dial `CalibrationDelta` (use externally if you want pure-functional re-anchoring) |
| `apply_anchor(state, calibration_delta)` | re-anchored state vector |

### 5.6 Cross-comparators

| Method | Returns |
|---|---|
| `compare_ephemerides(jd, body, kernel_a, kernel_b)` | `{delta_arcsec, delta_km, delta_au}` |
| `compare_models(jd, body, model_a, model_b)` | uniform vs Hipparchus epicycle vs Ptolemy equant residuals |
| `compare_reconstructions(jd, *, dials='all')` | `{Freeth2021: {...}, Wright: {...}, Price1974: {...}}` (folded from v0.2) |

### 5.7 What-if & archaeology (folded from v0.2)

| Method | Returns |
|---|---|
| `encode_with_custom_train(jd, dial, p, q)` | state vector for arbitrary p/q ratio (with sanity gate on tooth budget ≤ 500) |
| `compare_to_ground_truth(jd, dial, p, q)` | residual against ephemeris for an arbitrary ratio |
| `get_fragment_inventory(fragment='A' \| 'B' \| 'C' \| 'D' \| 'all')` | gears attested + reconstructed in that fragment |

### 5.8 Babylonian Goal-Year overlay (folded from v0.3)

| Method | Returns |
|---|---|
| `goalyear_predict(planet, jd, *, source='mulapin' \| 'almagest')` | what a Babylonian astronomer would have predicted from the N-year cycle for that planet/JD |
| `goalyear_compare(planet, jd)` | side-by-side: encoder, Goal-Year prediction, modern truth |

### 5.9 Animation export (folded from v0.2)

| Method | Returns |
|---|---|
| `encode_range(jd_lo, jd_hi, *, step_days=1.0)` | time-series of states, compact format |
| `export_animation(jd_lo, jd_hi, step_days, *, format='json' \| 'npz' \| 'spectral')` | bytes payload for download |

### 5.10 H-battery (read-only)

| Method | Returns |
|---|---|
| `run_hypothesis_battery(*, ephemeris=None)` | the 31-row CSV content as a list of dicts (skips skyfield-dependent rows if `ephemeris=None`) |
| `get_hypothesis(id)` | single-row lookup with full detail blob |

**Total: 28 methods.** Documented in `docs/bridge_api.md` with JSON-schema return types. **Frozen for v0.1.0**; additions are minor-version bumps, breaking changes are major.

---

## 6. CLI surface

`antikythera-spectral` console script (entry point `antikythera_spectral.cli:main`):

```
antikythera-spectral --help
antikythera-spectral version

# Encoding / decoding
antikythera-spectral encode --jd 1684500.0 [--dial all|metonic|saros|...]
antikythera-spectral decode --state state.npy [--dial mars]
antikythera-spectral angle  --jd 1684500.0 --dial mars

# Calendar
antikythera-spectral date jd-to-gregorian 1684500.0
antikythera-spectral date gregorian-to-jd 200 --era BCE
antikythera-spectral date jd-to-athenian 1684500.0
antikythera-spectral date jd-to-olympiad 1684500.0

# Astronomy
antikythera-spectral visibility --planet mars --from-jd 1684500 --to-jd 1685000
antikythera-spectral heliacal   --planet venus --jd 1684500.0
antikythera-spectral eclipses   --from-jd 1684500 --to-jd 1685000 --kind all

# Operator workflow
antikythera-spectral operator step --state session.json --delta-days 30
antikythera-spectral operator observe --state session.json --planet mars --residue 247

# Cross-comparators
antikythera-spectral compare ephemerides --jd 1684500.0 --body mars \
                          --kernel-a de421 --kernel-b de441_part1
antikythera-spectral compare models --jd 1684500.0 --body mars \
                          --model-a uniform --model-b equant
antikythera-spectral compare reconstructions --jd 1684500.0

# What-if & archaeology
antikythera-spectral whatif encode --jd 1684500.0 --dial venus --p 5 --q 8
antikythera-spectral fragment inventory --id A

# Babylonian Goal-Year
antikythera-spectral goalyear predict --planet mars --jd 1684500.0
antikythera-spectral goalyear compare --planet mars --jd 1684500.0

# Animation
antikythera-spectral animate --from-jd 1684500 --to-jd 1685000 \
                          --step-days 1 --format spectral -o out.spectral

# Hypothesis battery
antikythera-spectral hypotheses [--ephemeris de421|de441_part1] [--csv-out -]
antikythera-spectral hypothesis E-H1b --detail

# Kernel management
antikythera-spectral kernel list
antikythera-spectral kernel download de441_part1   # prompts y/N, ~1.5 GB
```

Each subcommand has rich `--help` with a citation-bearing epilog (the v0.2.0 retrofit pattern).

---

## 7. CodeQL strategy — proactive

The v0.2.0 research-scaffold work hit `py/clear-text-logging-sensitive-data` seven times across `ephemeris_loader.py` / `astronomical_ground_truth.py` / `consolidated_tests.py`. The trigger was passing kernel filenames to logging calls; the suppress attempts via `lgtm[...]` did not stick because modern CodeQL Python ignores that legacy syntax. The fix that landed (commit 328f344) was sanitisation-barrier numeric casts.

For v0.1.0 we apply **three layered mitigations**:

### 7.1 An allowlist owns the URL space

`bridge/ephemeris_bridge.py` is the *only* module that constructs JPL URLs. It validates the requested kernel name against a frozen tuple **before** building any URL or filesystem path:

```python
ALLOWED_KERNELS = ("de421", "de422", "de440", "de441", "de441_part1", "de441_part2")

def _kernel_url(name: str) -> str:
    if name not in ALLOWED_KERNELS:           # CodeQL: this branch raises
        raise ValueError(f"unknown kernel {name!r}")
    return f"https://ssd.jpl.nasa.gov/ftp/eph/planets/bsp/{name}.bsp"
```

CodeQL's flow analysis can see the allowlist gate; the user-controlled string never reaches the URL constructor without passing a constant-set membership test.

### 7.2 Logging redacts paths

Anywhere we log a kernel filename or BSP path, we log only the **kernel name** (which is in the allowlist), never the full path:

```python
log.info("loaded kernel %s (size %.1f MB)", kernel_name, size_mb)   # OK
log.info("loaded %s", kernel_path)                                    # NOT OK
```

A unit test `test_codeql_allowlist.py` greps the package source for `log.*kernel_path|log.*\.bsp` and fails the build if any such line appears.

### 7.3 What-if-mode input gates

`encode_with_custom_train(jd, dial, p, q)` requires:

- `dial` ∈ allowlist of supported dials.
- `p, q ∈ [1, 500]` (Greek-bronze cuttability ceiling per A-H1; rejects pathological inputs).
- `gcd(p, q) == 1` (already-reduced ratio).

This is documented in ADR `0008-whatif-mode-bounded-input.md` and enforced in `whatif.py`. Without these gates, a user-controlled `p, q` could trigger pathological enumeration in `pareto_analysis.best_pq_constrained()`.

### 7.4 Workflow paths get the antikythera-spectral tree

`.github/codeql/codeql-config.yml` already lists `docs/antikythera-maths/python/**`. Update both that file and `.github/workflows/codeql.yml`'s `paths:` filter to include:

```yaml
- "docs/antikythera-maths/antikythera-spectral/**"
```

(the existing `docs/antikythera-maths/python/**` line stays as a fallback for the research package.)

### 7.5 What we expect CodeQL to flag (and why we accept it)

- **`py/url-redirection`** — none of the bridge methods take a user-supplied URL.
- **`py/path-injection`** on the BSP-cache path — mitigated by `Path(__file__).parent / "_cache" / sanitized_name` where `sanitized_name` passes a `^[a-z0-9_]+\.bsp$` regex.
- **`py/clear-text-logging-sensitive-data`** — should not fire under §7.2 discipline; if it does, it's a sanitisation-barrier `str(...)` cast or a logger filter, not a `lgtm[...]` suppression.

ADR `0003-ephemeris-allowlist-codeql.md` documents the discipline so a future contributor doesn't accidentally widen the URL space.

---

## 8. PyPI publish workflow

Two workflow files, both new:

### 8.1 `.github/workflows/antikythera-spectral-publish.yml`

Mirrors `chess-spectral-publish.yml` minus cibuildwheel (no native code) and minus the dual `pyproject-pure.toml` step.

**Triggers**:
- `push` on tag `antikythera-spectral-v*` → publishes to **PyPI** (production).
- `workflow_dispatch` with `target` input ∈ `{testpypi, pypi}` → publishes to chosen target. Default: `testpypi` (so accidental hits don't burn a real release).

**Jobs**:
1. **build-wheel** — single ubuntu-latest job; pure Python = `py3-none-any`.
2. **build-sdist** — same job, parallel.
3. **publish** — depends on both. The target environment is selected from the dispatch input or defaults to `pypi` for tag-push events. Uses OIDC trusted publishing.

**Two GitHub environments**:
- `pypi` — production. Trusted publisher on `pypi.org` (✅ done).
- `testpypi` — staging. Trusted publisher on `test.pypi.org` (one-time setup, separate from `pypi`).

**Tag-version check**: parses tag (`antikythera-spectral-vX.Y.Z`) and verifies it matches `python/pyproject.toml`'s `[project].version`. Mismatch → fail.

### 8.2 `.github/workflows/antikythera-spectral-autotag.yml`

Mirror of [`chess-spectral-autotag.yml`](.github/workflows/chess-spectral-autotag.yml). Detects a strict-semver version bump in `python/pyproject.toml` on main and pushes the matching `antikythera-spectral-v*` tag, which fires the publish workflow. Pre-release / dev versions (`0.1.0rc1`, `0.1.0.dev0`, …) do NOT autotag — they're test-only.

### 8.3 The single-PR rollout flow (per user's "test PyPI before merge" decision)

The phased rollout collapses to **one feature branch + one PR + ~18 commits**, validated against TestPyPI before merge:

```
[branch antikythera-spectral-v0.1.0]
   |
   |-- e5acdd2  docs: plan
   |-- ......   phase 1: skeleton + codegen
   |-- ......   phase 2: facade re-exports
   |-- ......   ...
   |-- ......   phase 17: docs + readme
   |
   |  ┌─ workflow_dispatch (target=testpypi) →  publishes 0.1.0rc1 to test.pypi.org
   |  │  pip install --index-url https://test.pypi.org/simple/ antikythera-spectral==0.1.0rc1
   |  │  smoke-test the install in a clean venv + a Pyodide REPL
   |  │  (iterate; bump rcN as needed)
   |  │
   |  └─ once green: bump pyproject version 0.1.0rc1 → 0.1.0, commit, push
   |
[merge to main]
   |
   |-- autotag detects 0.1.0 (strict semver) and pushes tag antikythera-spectral-v0.1.0
   |-- publish workflow fires on tag-push → publishes 0.1.0 to pypi.org
```

The benefit: **zero version-burn on real PyPI during development**. We only push `0.1.0` to `pypi.org` once we've verified the same artifact works under `pip install` from `test.pypi.org`. ADR `0009-single-branch-rollout.md` and `0010-testpypi-pre-merge-gating.md` document this strategy.

---

## 9. Test plan

`python/tests/`:

1. **`test_bridge_round_trip.py`** — every bridge method called with a representative input; assert `result['ok'] is True`, assert payload shapes/types match the documented schema.
2. **`test_encoder_facade.py`** — facade re-exports match `research.encode_ant` (golden-output parity for D=940, D=13440, D=lcm).
3. **`test_visibility.py`** — heliacal-rising windows for Mars / Venus / Mercury at -200 BCE match within ±1 day of NASA Espenak catalogue (skip if skyfield/kernel absent).
4. **`test_compare_kernels.py`** — `compare_ephemerides('de421', 'de421', 2451545.0, 'mars')` returns δ ≈ 0; cross-kernel test runs only if both kernels are on disk.
5. **`test_compare_models.py`** — uniform peak ≥150°, equant peak in [30°, 50°] band, Hipparchus peak ≤10°.
6. **`test_dates.py`** — round-trip Gregorian↔JD, JD↔Athenian, JD↔Olympiad. Cross-check Antikythera back-dial Olympiad readings (per Freeth, Jones, Steele, Bitsakis 2008).
7. **`test_eclipses_search.py`** — skips if no kernel; finds 6 Hellenistic anchor eclipses in their respective JD bands.
8. **`test_operator_workflow.py`** — golden-output walkthrough: start at JD X, advance Y days, observe Mars at heliacal rising, verify re-anchored state.
9. **`test_reconstructions.py`** — Freeth/Wright/Price disagree on the gears with disagreements (e.g. b1 tooth count); agree elsewhere.
10. **`test_whatif.py`** — bounded-input gates reject p > 500, q > 500, p/q non-coprime; valid input encodes successfully.
11. **`test_archaeology.py`** — Fragment A inventory matches Freeth 2021 supplementary table.
12. **`test_goalyear.py`** — Mars 47-year prediction agrees with skyfield within Babylonian-period precision.
13. **`test_animation_export.py`** — `encode_range(jd, jd+10, step=1)` produces 10 states; JSON / NPZ / spectral formats round-trip.
14. **`test_codeql_allowlist.py`** — grep for `log.*kernel_path|log.*\.bsp`; assert zero matches.
15. **`test_pyodide_compat.py`** — `import antikythera_spectral` succeeds with skyfield/scipy/matplotlib monkey-patched to `None`.
16. **`test_data_freshness.py`** — codegen output matches `research/` source.

CI: `.github/workflows/antikythera-spectral-ci.yml` runs the matrix `[ubuntu-latest, macos-14, windows-latest] × [3.10, 3.11, 3.12, 3.13, 3.14]`.

---

## 10. Implementation order

Sequential phases. **Single feature branch (`antikythera-spectral-v0.1.0`), single PR — all phases land as commits on the same branch.** PR opens early; phases land as commits as they're written. Each commit ends with green CI; the branch is always installable. We test against TestPyPI before merging to main (see §8.3). ADR `0009`.

1. **Skeleton** — directory structure (incl. `codegen/`), empty `pyproject.toml`, version stamp, `py.typed`, `__init__.py` with version-only export. CI green.
2. **Codegen** — `codegen/emit_*.py` + `regenerate.py`. Read from `research/*.py`, write to `_data/*.json` + `_data/basis_*.npz`. `manifest.json` carries source-commit hash. `test_data_freshness.py` enforces parity.
3. **Facade re-exports** — `encoder.py`, `decoder.py`, `dials.py`, `render.py`, `hypotheses.py`, `ephemeris.py`, `eclipses.py`, `periods.py`, `gears.py`. Lazy imports. Smoke-test each.
4. **Bridge API §5.1–§5.2** — state↔date methods (the basic encoder bridge). 7 methods.
5. **Calendar conversion** (§5.3) — `dates.py` with 4-system support. ADR `0007` for the Athenian-archonship lookup. 5 bridge methods.
6. **Astronomical observables** (§5.4) — `visibility.py` + `eclipses_search.py`. 6 bridge methods.
7. **Operator workflow** (§5.5) — `operator.py` with stateless API. ADR `0006` for the no-server-state decision. 6 bridge methods.
8. **Cross-comparators** (§5.6) — `compare.py` + `reconstructions.py`. 3 bridge methods.
9. **What-if & archaeology** (§5.7) — `whatif.py` + `archaeology.py`. ADR `0008` for input gates. 3 bridge methods.
10. **Goal-Year overlay** (§5.8) — `goalyear.py`. 2 bridge methods.
11. **Animation export** (§5.9) — `animation.py`. Compact-state-format reuse from chess-spectral's `.spectral` if portable; otherwise project-specific format documented in `docs/SPECTRAL_FILE_FORMAT.md`. 2 bridge methods.
12. **H-battery facade** (§5.10) — wrap `consolidated_tests`. 2 bridge methods.
13. **CLI** — `cli.py` with subcommands matching §6.
14. **CodeQL config update** — paths in `.github/codeql/codeql-config.yml` and `.github/workflows/codeql.yml`. PR; verify CodeQL passes.
15. **PyPI workflow** — `antikythera-spectral-publish.yml` + `antikythera-spectral-ci.yml`. Verify via `workflow_dispatch` dry-run.
16. **Docs** — bridge_api.md, DELTA_T_MODEL.md, EPHEMERIS_KERNELS.md, CALENDAR_SYSTEMS.md, OPERATOR_WORKFLOW.md, 8 ADRs. README.md / CHANGELOG.md / ROADMAP.md.
17. **Docs + READMEs** — both `python/README.md` (PyPI long-description, §16) and the repo-root `docs/antikythera-maths/antikythera-spectral/README.md` (GitHub-tree landing). Bridge API contract, ADRs 0001–0010, CHANGELOG, ROADMAP.
18. **Trusted-publisher PyPI setup** — ✅ **DONE** for `pypi`; **TODO** for `testpypi` environment (one-time human step on test.pypi.org).
19. **TestPyPI dry run** — `workflow_dispatch` the publish workflow with `target=testpypi`, version `0.1.0rc1`. Verify in a clean venv: `pip install --index-url https://test.pypi.org/simple/ antikythera-spectral==0.1.0rc1` + Pyodide REPL smoke. Iterate `rcN` if anything's broken; the PR stays open.
20. **Version bump → merge** — bump `python/pyproject.toml` from `0.1.0rc1` to `0.1.0`, commit on the branch, get final PR review. Merge to main.
21. **Autotag → publish** — autotag workflow detects `0.1.0` on main, pushes tag `antikythera-spectral-v0.1.0`, publish workflow fires on tag-push, real PyPI release lands. Acceptance gate (§15).

All phases ship as commits on a single PR. The scaffold lands as a coherent v0.1.0 release rather than an incremental series — we want a clean first PyPI artifact, not a half-finished one with API gaps. Pre-merge testing happens against TestPyPI per §8.3, so we get the "verify before commit-to-main" signal without burning a real PyPI version slot.

---

## 11. Beyond v0.1.0 — what stays deferred

After folding the original v0.2 set in, the following remain on the backlog:

- **C accelerator** — only if profiling shows a bottleneck for browser bulk-encoding use (>100 ms per frame on a mid-range laptop). Triggers the dual-wheel pattern.
- **DE-kernel cross-validation as a hypothesis row** — H-H3 "The Antikythera era is correctly handled by both DE441 and DE422 within ε₁ arcsec." This needs a research-scaffold update (new H-row), so it's a coordinated minor-version bump on both packages.
- **Parapegma heliacal-event readout** — needs digitisation work on the parapegma inscription (Voulgaris et al. 2022's reading).
- **Drag-and-drop web UI** — out of scope for the package; the chess-spectral viewer PWA is the model for a future companion project.
- **3D rendering of the bronze stack** — geometry data not in our scaffold.
- **Live Szigety-tolerance Monte Carlo in-browser** — the existing Monte Carlo is server-side fine; in-browser would need C-acceleration first.
- **Multi-language bindings (TS / Rust / Go)** — no demand signal.

---

## 12. DE-kernel comparator note

JPL has not released DE442, DE443, or DE444 (as of 2026-04-29). Current sequence: DE438, DE440, DE441 — DE441 (Park et al. 2021) is the long-coverage current best.

`compare_ephemerides(jd, body, kernel_a, kernel_b)` covers any pair of allowlisted kernels. The genuinely useful Hellenistic-era comparison is **DE441 vs DE422** (both reach -200 BCE) or **DE441 vs DE421** (long vs modern-only, to show the modern-only kernel breaks down outside 1899–2053).

The **ΔT discussion** lives in `docs/DELTA_T_MODEL.md`: at -200 BCE the Earth-rotation drift uncertainty is ~3 hours — what makes E-H1b's tolerance ±1 day rather than ±1 minute, and what dominates any apparent kernel-vs-kernel difference at Hellenistic epochs.

---

## 13. Risks & open questions

1. **Frozen-data drift** — `_data/*.json` goes stale if `research/*.py` changes. Mitigation: `test_data_freshness.py` fails build on drift; CHANGELOG entry forced. `codegen/regenerate.py` is a single-command refresh.
2. **Skyfield + Pyodide** — verify before tagging; skyfield's `jplephem` C-extension fallback may not load cleanly in Pyodide. If it fails, document the Pyodide-specific install incantation.
3. **DE441_part1 download size in CI** — 1.5 GB; cannot fetch on every run. Solution: gate kernel-dependent tests behind `ANTIKYTHERA_KERNEL_PATH` env var; CI sets it on a nightly schedule only.
4. **Athenian archon table** — the canonical archon list (Develin 1989, Pritchett & Neugebauer 1947) has gaps and disputed reigns. We default to Develin 1989 for the period -510 to -301 BCE; outside that, raise `UnknownArchonError` rather than guess. ADR `0007`.
5. **Babylonian Goal-Year** — the 47-year Mars cycle, 59-year Saturn cycle, etc. are "implicit" in cuneiform texts; the modern interpretation has confidence levels. We use FIRM + RECONSTRUCTED entries; DISPUTED entries are excluded by default (same discipline as `historical_periods.py`).
6. **Operator-state JSON schema stability** — `OperatorState` dict is part of the v0.1.0 freeze. Adding fields is OK (forward-compatible if consumers ignore unknown keys); removing or renaming fields is a major-version bump.
7. **What-if mode pathological input** — a user could request `encode_with_custom_train(jd, 'venus', p=499, q=499)` and waste enumeration time. Input gates §7.3 + a 5-second timeout in the bridge wrapper guard against this.
8. **Animation file size** — 10 years × 1 day step = 3 650 states × ~30 KB each = ~110 MB JSON. The compact `.spectral`-style format gets this to ~5 MB. Default `step_days=10` for animation export so first-time users don't blow up their browser.

---

## 14. Out of scope (recorded so they don't get forgotten)

- Live haptic rendering. The `lemonforest/mlehaptics` repo houses an EMDR firmware project (CLAUDE.md-level); the antikythera-spectral package is documentation/research code that happens to live in the same monorepo. No firmware integration is contemplated.
- The architectural-mode hypotheses (§11.6.10–§11.6.16) as bridge methods. These are notebook-level discussion; the H-battery surfaces only the *numerical* test outcomes (G-H1, G-H6, G-H7, G-H8). The "rationale" sub-sections like §11.6.16 stay as research narrative + the operator-workflow simulation; they don't become free-standing bridge methods.
- A drag-and-drop web UI. The chess-spectral PWA is the model.

---

## 15. Acceptance gate for v0.1.0 release

Two-tier gate. The TestPyPI tier must be green BEFORE merge to main; the production tier must be green BEFORE we declare the release shipped.

### 15.1 Pre-merge (verified against TestPyPI)

- [ ] `pip install --index-url https://test.pypi.org/simple/ antikythera-spectral==0.1.0rc1` works on a clean Python 3.12 venv.
- [ ] `python -c "import antikythera_spectral; print(antikythera_spectral.__version__)"` prints `0.1.0rc1`.
- [ ] All 28 bridge methods documented in `docs/bridge_api.md` and exercised in `test_bridge_round_trip.py` with 100 % success-path coverage.
- [ ] CodeQL: zero `py/clear-text-logging-sensitive-data` alerts; zero high-severity Python alerts.
- [ ] CI green on Linux / macOS / Windows × Python 3.10–3.14.
- [ ] `python/README.md` renders correctly on TestPyPI (twine check passes, badges resolve, all §16.1 sections present, ≤ 1500 words per §16.2).
- [ ] At least one frontend developer can call 8+ bridge methods from a Pyodide REPL (using the TestPyPI artifact) without hitting an error or a missing dependency.
- [ ] `codegen/regenerate.py` runs in <30 seconds and produces byte-identical output across two runs (deterministic basis-vector seeding).
- [ ] `antikythera-spectral animate --from-jd 1684500 --to-jd 1685000 --step-days 1 --format spectral -o out.spectral` produces a file < 10 MB (run from the TestPyPI install).

When all nine boxes are ticked: bump `python/pyproject.toml` from `0.1.0rc1` to `0.1.0`, commit, get final PR review, merge to main.

### 15.2 Post-merge (verified against PyPI)

- [ ] Autotag workflow pushed `antikythera-spectral-v0.1.0` after the merge commit.
- [ ] Publish workflow on tag-push completed successfully (wheel + sdist on `pypi.org/project/antikythera-spectral/0.1.0/`).
- [ ] `pip install antikythera-spectral` from real PyPI works on a clean venv (we already proved equivalence via TestPyPI; this is the final confirmation).
- [ ] GitHub Release created (autotag's release-creation step) with CHANGELOG entry as the body.

When both tiers are green, v0.1.0 is shipped.

---

## 16. PyPI-facing README (the page on pypi.org)

This is the README PyPI shows on `https://pypi.org/project/antikythera-spectral/`. It lives at `python/README.md` and is referenced via `readme = "README.md"` from the `python/pyproject.toml` in the same directory. The repo-root `README.md` (one level up) is the GitHub-tree landing page; the two are *separate* files because they have different audiences.

The PyPI README is the **first thing** a stranger sees who pip-discovers this package. It must answer four questions in 30 seconds:

1. What is this package?
2. Why would I install it?
3. How do I install it?
4. What does the simplest possible usage look like?

### 16.1 Required structure (sections in order)

```markdown
# antikythera-spectral

One-paragraph elevator pitch.  ~3 sentences.  What it is, what it
encodes, why someone would use it.

## What is the Antikythera mechanism?

A 2-paragraph plain-English primer for users who don't know the
historical context.  ~150 BCE Greek bronze gear-train, recovered 1901,
predicts solar/lunar/planetary positions.  Cite Freeth 2021 for the
authoritative reconstruction.  Link to Wikipedia and the project
notebook for further reading.

## Install

```bash
pip install antikythera-spectral
```

Optional extras table (ephemeris / plot / hypotheses / all).

Pyodide install snippet (`micropip.install("antikythera-spectral[ephemeris]")`).

## Quick start (Python)

A 5-line example: import, encode a date, read the dial state.

```python
>>> from antikythera_spectral import bridge
>>> result = bridge.get_dial_state(jd_tdb=1684500.0)   # ~205 BCE
>>> result['ok']
True
>>> result['dials']['mars']['angle_deg']
247.3
```

## Quick start (CLI)

```bash
antikythera-spectral encode --jd 1684500.0
antikythera-spectral visibility --planet mars --from-jd 1684500 --to-jd 1685000
antikythera-spectral compare ephemerides --jd 1684500 --body mars \
                                          --kernel-a de421 --kernel-b de441_part1
```

## Quick start (Pyodide / browser)

A 5-line snippet showing micropip install + a bridge call from an
in-browser Python REPL.  This is the use case the package is built for.

## What can I do with it?

Bullet list.  ~12 items.  Encode dates, decode states, run hypothesis
battery, visibility windows, eclipse search, calendar conversion,
operator workflow simulation, reconstruction comparison, what-if mode,
archaeological inventory, animation export, Babylonian Goal-Year
overlay.  Each item is a one-line description.

## Bridge API

Pointer to `docs/bridge_api.md` (link to the GitHub blob URL).
Promise: 28 methods, each returns `{"ok": True, ...}` or
`{"ok": False, "error": "..."}`.

## Hypothesis battery

Pointer to the 31-row H-battery, with one or two example rows shown
inline.  Link to `docs/antikythera-maths/antikythera_spectral_research_notebook.md`.

## Documentation

| Doc | Link |
| --- | ---- |
| Research notebook | ../../antikythera_spectral_research_notebook.md |
| Bridge API contract | docs/bridge_api.md |
| Calendar systems | docs/CALENDAR_SYSTEMS.md |
| Ephemeris kernels | docs/EPHEMERIS_KERNELS.md |
| ΔT discussion | docs/DELTA_T_MODEL.md |
| Operator workflow | docs/OPERATOR_WORKFLOW.md |
| ROADMAP | ../ROADMAP.md |
| CHANGELOG | CHANGELOG.md |

## Citing

How to cite the package + the research notebook.  Include a
`@software{}` BibTeX entry.

## License

GPL-3.0-or-later (matches the chess-spectral / haptics-firmware
project licensing).

## See also

Sibling packages in the same monorepo:
- `chess-spectral` (same HDC framing applied to chess)
- (future) `othello-spectral`, `addressing-maths`
```

### 16.2 Word-count budget

- Elevator pitch: ≤ 60 words
- Antikythera primer: ≤ 200 words
- Total README: ≤ 1500 words (so PyPI's render stays scannable; long-form goes in `docs/`)

### 16.3 Image / badge policy

- ✅ PyPI version + license + Python version badges from shields.io.
- ✅ One thumbnail of the gear topology SVG (linked to the full SVG in `docs/antikythera-maths/figures/gear_topology.svg`).
- ❌ No animated GIFs (PyPI's renderer often misbehaves).
- ❌ No locally-hosted images that would 404 if the GitHub repo is renamed.

### 16.4 Verification before tag-push

`twine check --strict dist/*.whl dist/*.tar.gz` is part of the publish workflow (§8). It catches missing description, broken markdown rendering, missing license metadata, etc.

Additionally: a step 16-extra in the implementation order opens the rendered README in a local viewer (`pip install readme-renderer; cat python/README.md | python -m readme_renderer`) and visually confirms the layout before committing.

### 16.5 Maintenance

The PyPI README is **frozen at tag time** for a given version. We do not edit it post-release. If a new feature lands in v0.2.0, the README updates in the v0.2.0 commit, not retroactively. This is the same discipline chess-spectral applies.

---

## Appendix A — Why no C in v0.1.0

Chess-spectral has 21 hand-written `.c` files because encoding a 100-game PGN means tens of thousands of plies × FEN parsing × 640-dim or 45 056-dim vector ops. The pure-Python fallback is **30–60× slower** per the chess-spectral `pyproject-pure.toml` comment. C buys real wall-clock time there.

Antikythera state vectors are tiny (940 to 13 440 dim). A typical query is **one date → one state**. Bulk operations (visibility windows over a year = 365 evaluations; pointer animation over a decade = ~3 650 evaluations) fit comfortably in pure Python — milliseconds, not seconds. The actual compute that matters (skyfield ephemeris evaluation) **already has C inside it** via `jplephem`'s extension; we get that benefit transparently.

If we shipped a C encoder it would be equivalent in user-perceived speed to the pure-Python one, while bringing 5 things we'd rather not have on day one:

1. cibuildwheel matrix (3 OS × 5 Python = 15 cells per release)
2. Dual `pyproject.toml` / `pyproject-pure.toml` pattern
3. `manylinux_2_28` constraints and `--build-mode manual` CodeQL config
4. CMake build prereq for sdist consumers
5. Native-binary storage in the wheel (the `_native/` directory chess-spectral has)

The codegen pattern is valuable independent of C; we adopt it whole-cloth (§3 `codegen/`). Re-evaluate C if a profiling case lands or a non-Python consumer (embedded, pure-WASM, Rust) shows up.

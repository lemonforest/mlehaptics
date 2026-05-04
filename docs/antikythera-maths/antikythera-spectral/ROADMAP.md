# antikythera-spectral roadmap

Status of advertised CLI / Bridge API methods. Mirror of the
[chess-spectral ROADMAP](../../chess-maths/chess-spectral/ROADMAP.md)
discipline: every entry the help text advertises is either ✅ wired
(real implementation behind it) or ⏳ pending (planned for a specific
version).

## Released versions

| Version | Date | Headline |
|---|---|---|
| **v0.3.0** | 2026-05-02 | Mars planetary models + bit-packed HDC ALU. New `mars_models` and `bit_alu` facades; bronze projection + Freeth-reconstruction param sets; `compare.compare_models_at_jd` and `bridge.compare_models` accept `bronze` + `params`; ADR 0012 (algebra/eigenbasis vs CAD scope); Mars 38° gap audit reproduced as `mars_models.fj_38deg_finding()`; bit-ALU benchmark + cycle-alignment investigation. 143 unit tests, 35 immolation. |
| v0.2.1 | 2026-04-30 | PyPI metadata hotfix (project URL `Demo` → kiosk site). |
| v0.2.0 | 2026-04-30 | Self-contained mode: visibility / heliacal / elongation / eclipses all default to algebraic propagation; skyfield optional via `[ephemeris]` extras. ADR 0011. |
| v0.1.0 | 2026-04-30 | First public release on PyPI. 28-method bridge, 9 facade modules, codegen with provenance manifest, 31-row H-battery, CLI console script. |

## Next planned

| Version | Theme |
|---|---|
| v0.4.x | Numpy-fast `bit_alu.permute` + `np.bitwise_count`-backed similarity (close the few remaining bit-ALU operations that still trail the float reference). H-battery rows for the bit-ALU encoder (does it pass the same B-H1 / E-H1 round-trip checks as the complex128 encoder?). |
| later | Apply the #5–#10 Mars-gap framework to Venus / Mercury / Jupiter / Saturn (each has its own theoretical-error figure worth auditing under the same discipline). |

The phase table below is preserved for historical context — most entries shipped during v0.1.0 / v0.2.0 / v0.3.0 even though the inline status says "pending."

## Current release: v0.3.0 (released 2026-05-02)

### Phase status

| Phase | Status | Description |
|-------|--------|-------------|
| 0 — Plan | ✅ shipped | [Planning document](../ANTIKYTHERA_SPECTRAL_PYPI_PLAN_v0.1.0.md) |
| 1 — Skeleton + codegen | ✅ in progress | `pyproject.toml`, version stamp, `codegen/` + `_data/` |
| 2 — Facade re-exports | ⏳ pending | encoder / decoder / dials / render / hypotheses / ephemeris / eclipses / periods / gears |
| 3–11 — Bridge API (28 methods) | ⏳ pending | state↔date, calendar, astronomy, operator, comparators, what-if, archaeology, Goal-Year, animation, H-battery |
| 12 — H-battery facade | ⏳ pending | wraps consolidated_tests |
| 13 — CLI | ⏳ pending | `antikythera-spectral` console script |
| 14 — CodeQL paths | ⏳ pending | update `.github/codeql/codeql-config.yml` |
| 15 — Publish + autotag workflows | ⏳ pending | `antikythera-spectral-publish.yml`, `antikythera-spectral-autotag.yml` |
| 16 — Docs + READMEs | ⏳ pending | bridge_api.md, DELTA_T_MODEL.md, EPHEMERIS_KERNELS.md, CALENDAR_SYSTEMS.md, OPERATOR_WORKFLOW.md, 10 ADRs |
| 17 — TestPyPI dry-run | ⏳ pending | workflow_dispatch with target=testpypi |
| 18 — Pre-merge gate | ⏳ pending | §15.1 of plan, all 9 boxes ticked against TestPyPI |
| 19 — Version bump → merge | ⏳ pending | bump 0.1.0rc1 → 0.1.0, merge PR |
| 20 — Autotag → real PyPI | ⏳ pending | autotag fires, publish workflow lands 0.1.0 on pypi.org |

## Bridge methods (target: 28)

### Read methods (state ← date) — phase 4

| Method | Status |
|--------|--------|
| `get_dial_state(jd_tdb)` | ⏳ pending |
| `get_dial_angle(jd_tdb, dial)` | ⏳ pending |
| `get_pointer_xy(jd_tdb, *, layout)` | ⏳ pending |
| `get_all_dial_metadata()` | ⏳ pending |
| `get_version()` | ⏳ pending |

### Date ← state — phase 4

| Method | Status |
|--------|--------|
| `decode_dial(state_vec, dial)` | ⏳ pending |
| `decode_to_jd(state_vec)` | ⏳ pending |

### Calendar conversion — phase 5

| Method | Status |
|--------|--------|
| `jd_to_gregorian(jd_tdb)` | ⏳ pending |
| `gregorian_to_jd(...)` | ⏳ pending |
| `jd_to_julian_calendar(jd_tdb)` | ⏳ pending |
| `jd_to_athenian(jd_tdb, archon_table)` | ⏳ pending |
| `jd_to_olympiad(jd_tdb)` | ⏳ pending |

### Astronomy — phase 6

| Method | Status |
|--------|--------|
| `get_visibility_windows(jd_lo, jd_hi, planet)` | ⏳ pending |
| `get_next_heliacal_rising(jd, planet)` | ⏳ pending |
| `get_solar_elongation(jd, planet)` | ⏳ pending |
| `get_eclipse_anchors(era)` | ⏳ pending |
| `get_period_relations(source)` | ⏳ pending |
| `find_eclipses(jd_lo, jd_hi, kind)` | ⏳ pending |

### Operator workflow (§11.6.16) — phase 7

| Method | Status |
|--------|--------|
| `start_operator_session(initial_jd, dials)` | ⏳ pending |
| `operator_advance(state, delta_days)` | ⏳ pending |
| `operator_observe(state, planet, observed_residue)` | ⏳ pending |
| `operator_diagnostics(state)` | ⏳ pending |
| `set_anchor(dial, jd, observed_residue)` | ⏳ pending |
| `apply_anchor(state, calibration_delta)` | ⏳ pending |

### Cross-comparators — phase 8

| Method | Status |
|--------|--------|
| `compare_ephemerides(jd, body, kernel_a, kernel_b)` | ⏳ pending |
| `compare_models(jd, body, model_a, model_b)` | ⏳ pending |
| `compare_reconstructions(jd, dials)` | ⏳ pending |

### What-if & archaeology — phase 9

| Method | Status |
|--------|--------|
| `encode_with_custom_train(jd, dial, p, q)` | ⏳ pending |
| `compare_to_ground_truth(jd, dial, p, q)` | ⏳ pending |
| `get_fragment_inventory(fragment)` | ⏳ pending |

### Babylonian Goal-Year — phase 10

| Method | Status |
|--------|--------|
| `goalyear_predict(planet, jd, source)` | ⏳ pending |
| `goalyear_compare(planet, jd)` | ⏳ pending |

### Animation export — phase 11

| Method | Status |
|--------|--------|
| `encode_range(jd_lo, jd_hi, step_days)` | ⏳ pending |
| `export_animation(jd_lo, jd_hi, step_days, format)` | ⏳ pending |

### H-battery — phase 12

| Method | Status |
|--------|--------|
| `run_hypothesis_battery(ephemeris)` | ⏳ pending |
| `get_hypothesis(id)` | ⏳ pending |

## Beyond v0.1.0 (deferred)

- Native C accelerator (only if profiling demands; would trigger dual-wheel pattern from chess-spectral)
- DE-kernel cross-validation as a hypothesis row (H-H3)
- Parapegma heliacal-event readout (needs digitisation work)
- Drag-and-drop web UI (separate frontend project)
- 3D rendering of the bronze stack
- Multi-language bindings (TS / Rust / Go) — Pyodide IS the JS surface

See [`../ANTIKYTHERA_SPECTRAL_PYPI_PLAN_v0.1.0.md`](../ANTIKYTHERA_SPECTRAL_PYPI_PLAN_v0.1.0.md) §11 for the full deferred-features list.

# `antikythera_spectral.bridge` — Pyodide Bridge API

**Version:** v0.1.0 (36 methods).

The bridge is the consumer-facing entry surface — what a Pyodide / web /
CLI consumer calls into. Every method:

- returns a Pyodide-JSON-serializable dict,
- carries an `'ok'` key (`True` for valid input + computation; `False`
  for caller-side input errors with an `error` string explaining why),
- raises only on genuine internal bugs (not user-input issues).

Numpy arrays in return values are real-valued. Complex state vectors
serialize as `Float32` real+imag interleaved of length `2*D` so JS
consumers use `new Float32Array(...)` directly. See ADR 0002.

---

## Method index by group

### §5.1 — State ← date

| Method | Returns |
|---|---|
| `get_dial_state(jd_tdb, *, D=940)` | Per-dial residues + HDC vector (interleaved Float32) |
| `get_dial_angle(jd_tdb, dial)` | Continuous angle (D-independent) |
| `get_pointer_xy(jd_tdb, *, layout='dial' \| 'spatial', D=940)` | Per-dial render coords |
| `get_all_dial_metadata()` | List of supported dials with cycle info |
| `get_version()` | Package version + frozen-data manifest |

### §5.2 — Date ← state

| Method | Returns |
|---|---|
| `decode_dial(state_vec, dial, *, D=940)` | Recovered residue |
| `decode_to_jd(state_vec, *, D=940, reference_jd=REFERENCE_JD)` | Median JD across dials |

### §5.3 — Calendar conversion

| Method | Returns |
|---|---|
| `jd_to_gregorian(jd_tdb)` | Proleptic Gregorian date |
| `gregorian_to_jd(year, month, day, hour=0, minute=0, second=0, era='CE')` | JD |
| `jd_to_julian_calendar(jd_tdb)` | Julian-calendar date (pre-1582) |
| `jd_to_athenian(jd_tdb, *, archon_table='attic')` | Attic month + day; archon=null in v0.1.0 (ADR 0007) |
| `jd_to_olympiad(jd_tdb)` | Olympiad number + year-in-Olympiad |

### §5.4 — Astronomical observables

| Method | Notes |
|---|---|
| `get_visibility_windows(jd_lo, jd_hi, planet, kernel='de421')` | Skyfield required |
| `get_next_heliacal_rising(jd_tdb, planet, kernel='de421')` | Skyfield required |
| `get_solar_elongation(jd_tdb, planet, kernel='de421')` | Skyfield required |
| `get_eclipse_anchors(era='hellenistic' \| 'modern' \| 'all')` | Frozen data |
| `get_period_relations(source='mulapin' \| 'almagest' \| 'all')` | Frozen data |
| `find_eclipses(jd_lo, jd_hi, *, kind='all', kernel='de421')` | Skyfield required |

### §5.5 — Operator workflow (§11.6.16 simulation, ADR 0006)

| Method | Notes |
|---|---|
| `start_operator_session(initial_jd, *, D=940, dials='all')` | Returns OperatorState |
| `operator_advance(state, delta_days)` | Returns new state |
| `operator_observe(state, dial, observed_residue)` | Records anchor |
| `operator_diagnostics(state)` | Per-dial drift |
| `set_anchor(dial, jd_tdb, observed_residue)` | Bare CalibrationDelta |
| `apply_anchor(state, calibration_delta)` | Apply to state |

### §5.6 — Cross-comparators

| Method | Notes |
|---|---|
| `compare_ephemerides(jd_tdb, body, kernel_a, kernel_b)` | DE-kernel delta |
| `compare_models(jd_tdb, body, model_a, model_b, kernel='de421', params='ptolemy')` | Mars-only.  `model_*` ∈ {uniform, epicycle, equant, **bronze**} (bronze added v0.3.0).  `params` ∈ {ptolemy, freeth_2012, freeth_2021} (added v0.3.0; default `'ptolemy'` for backward-compat). |
| `compare_reconstructions(jd_tdb, *, dials='all')` | Freeth/Wright/Price disagreements |

### §5.7 — What-if + archaeology (ADR 0008)

| Method | Notes |
|---|---|
| `encode_with_custom_train(jd_tdb, dial, p, q)` | p,q ∈ [1,500], gcd(p,q)=1 |
| `compare_to_ground_truth(jd_tdb, dial, p, q)` | Custom vs canonical residual |
| `get_fragment_inventory(fragment='all')` | Reads `_data/fragments.json` |

### §5.8 — Babylonian Goal-Year

| Method | Notes |
|---|---|
| `goalyear_predict(planet, jd_tdb, *, source='mulapin')` | Lookup date N years prior |
| `goalyear_compare(planet, jd_tdb)` | Goal-Year + encoder side-by-side |

### §5.9 — Animation export

| Method | Notes |
|---|---|
| `encode_range(jd_lo, jd_hi, *, step_days=1.0, D=940)` | Time-series of states |
| `export_animation(jd_lo, jd_hi, step_days, *, format='json' \| 'npz', D=940)` | Base64-encoded payload |

### §5.10 — Hypothesis battery

| Method | Notes |
|---|---|
| `run_hypothesis_battery(*, ephemeris=None)` | All 31 rows |
| `get_hypothesis(id)` | Single-row lookup |

---

## Common return shape

Success:

```python
{"ok": True, "...": ...}
```

Failure (caller-side input):

```python
{"ok": False, "error": "..."}
```

Internal failures raise; callers should catch broadly only at the JS / Pyodide boundary.

## State vector format

Complex-valued HDC state of dimension D serialised as **real+imag interleaved Float32** of length `2*D`. For cell `k`:

```
state[k] = arr[2*k] + 1j * arr[2*k+1]
```

This matches the chess-spectral `qm_4d_bridge` ComplexArray convention; web consumers cast directly to `Float32Array`.

## Validation patterns

- `jd_tdb` must be finite, in approximately `(-1_000_000, 5_000_000)` (covers any plausible Julian Day).
- `D` must be in `(940, 13440)` (Callippic / packing variants).
- `dial` must be in the frozen list returned by `get_all_dial_metadata`.
- `kernel` must be in `ephemeris.ALLOWED_KERNELS` (frozen tuple).
- `planet` must be in `visibility.SUPPORTED_PLANETS`.
- `layout` must be in `('dial', 'spatial')`.

All validations run before any expensive computation.

## ADR cross-reference

- ADR 0001 — pure-Python only in v0.1.0
- ADR 0002 — bridge API shape (this document is the contract)
- ADR 0003 — ephemeris allowlist (CodeQL discipline)
- ADR 0006 — stateless bridge (no server-side state)
- ADR 0007 — Athenian-calendar fidelity caveats
- ADR 0008 — what-if mode bounded input
- ADR 0009 — single-branch rollout
- ADR 0010 — TestPyPI pre-merge gating

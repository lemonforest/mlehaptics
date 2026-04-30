# ADR 0011: Algebraic default, ephemeris opt-in

**Status:** Accepted (2026-04-30, v0.2.0)

## Context

v0.1.0 shipped four bridge methods that needed a JPL DE-kernel via skyfield to answer:

- `get_solar_elongation(jd, planet)`
- `get_visibility_windows(jd_lo, jd_hi, planet)`
- `get_next_heliacal_rising(jd, planet)`
- `find_eclipses(jd_lo, jd_hi, kind)`

Kiosk-style consumers — the primary motivating use case for the package — generally *do not* want a 16 MB to 1.5 GB ephemeris kernel as a runtime dependency. They want "is Mars currently visible?" to return without `pip install antikythera-spectral[ephemeris]` and a 1.5 GB BSP download.

## Insight

The encoder is the device. Once anchored at design time (`REFERENCE_JD = 1684595.0`), every dial reading is `(jd - REFERENCE_JD) / cycle_period_days % 1`. Pure modular arithmetic on cyclic groups; no ephemeris needed. The ephemeris only enters when we want to *grade* the encoder's predictions against modern best-estimate sky truth.

The same logic applies to the four sky-truth methods above:

- **Heliacal rising / visibility windows / solar elongation** are all functions of *synodic-cycle phase*. Given one observed heliacal rising per planet (an anchor) plus the synodic period, every future event is `anchor + n · synodic`. Closed-form, sub-millisecond, no ephemeris.
- **Eclipse search** is what the Antikythera's Saros pointer does — the device's actual job. Saros-cycle propagation from a frozen anchor catalogue is the right model.

The only method that *inherently* needs an ephemeris is `compare_ephemerides` (it's literally a JPL-kernel diff tool); that one stays ephemeris-only.

## Decision

Each of the four methods grows a `precise` keyword:

- `precise=False` (default): self-contained algebraic mode. Uses per-planet anchors from `_data/visibility_anchors.json` + the existing eclipse anchor catalogue in `_data/anchors.json`. Always succeeds (no kernel required).
- `precise=True`: opt-in skyfield mode. Sub-arcsec accuracy; requires `[ephemeris]` extras + the chosen kernel locally; returns `{"ok": False, ...}` if the kernel is missing.

The CLI mirrors this with a `--precise` flag on the four affected subcommands.

The package's `dependencies` list stays as `["numpy>=1.24"]`. Skyfield + jplephem move to `[ephemeris]` extras only — they're now strictly optional.

`compare_ephemerides` is unchanged (ephemeris-bound by definition; `[ephemeris]` extras required).

## Consequences

- Kiosk install: `pip install antikythera-spectral` works for every method except `compare_ephemerides`. No extras needed.
- Wheel size unchanged (frozen JSON anchors are tiny — <2 KB).
- Precision target: `precise=False` answers are within ~±1 day on heliacal events and ~±5° on elongation. At Hellenistic-era epochs the ΔT-uncertainty floor is 3 hours regardless ([DELTA_T_MODEL.md](../DELTA_T_MODEL.md)), so the algebraic precision is honest for the device's natural use case.
- Research-mode users who want to validate the encoder against modern best-estimate get sub-arcsec precision via `precise=True`. Same surface, opt-in cost.
- `bridge_api.md` updated to document the `precise` keyword on the affected methods. Return shapes gain a `mode: "algebraic" | "ephemeris"` field.

## Anchor provenance

Per-planet anchors in `_data/visibility_anchors.json` were computed once at v0.2.0 design time using skyfield + DE421, searching forward from J2000 (JD 2451545.0) for the first heliacal rising of each planet. Documented inline in the JSON's `anchor_provenance` field. Re-running this computation with a different kernel or epoch is straightforward but should produce equivalent results to within ±1 day; the file is committed and frozen for v0.2.0.

## Alternatives considered

- **Drop the four methods entirely**, force users into [ephemeris]. Rejected: the sky-truth queries are useful in their own right for kiosk display ("is Mars visible tonight?"), and the Antikythera's own job is exactly Saros-cycle eclipse prediction.
- **Make skyfield a runtime dep, ship a small kernel.** Rejected: smallest usable JPL kernel (DE421) is 16 MB and only covers 1899-2053. For Hellenistic-era queries you need DE441_part1 (1.5 GB). Neither is wheel-friendly.
- **Single-mode algebraic only**, drop the skyfield path. Rejected: research users genuinely need the validation surface; we shouldn't take it away from them just because kiosk users don't need it.

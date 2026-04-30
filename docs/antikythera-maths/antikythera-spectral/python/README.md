# antikythera-spectral

> **A hyperdimensional-computing model of the Antikythera mechanism, packaged for Python and the browser.**

Encode any date as a state vector that any of the mechanism's dials can be read from. Decode, compare against modern ephemeris truth, simulate the Hellenistic operator's seasonal-recalibration workflow, and run the project's 31-row hypothesis battery — all from one `pip install`. Pyodide-compatible: the same package runs in a browser via `micropip` so a web app can drive a digital Antikythera with no Python server.

## What is the Antikythera mechanism?

A bronze hand-cranked astronomical calculator built in Hellenistic Greece around 150–60 BCE, recovered in 1901 from a shipwreck off the island of Antikythera. Its surviving 30+ gears predict solar / lunar / planetary positions, eclipses (via the 18-year Saros cycle), and the four-year Olympiad calendar. Freeth et al. 2021 ([*Sci. Rep.* 11:5821](https://www.nature.com/articles/s41598-021-84310-w)) is the current authoritative reconstruction; the device's planetary front face has not survived intact and remains the subject of active research.

The HDC framing this package implements: every gear is a faithful representation of ℤ/nℤ; every mesh is a rational map between cyclic groups; every dial pointer is a hypervector whose components are the phase angles on the various dials. The Greeks built a resonant HDC object before Plate wrote HRR.

## Install

```bash
pip install antikythera-spectral
```

The base install pulls only `numpy` and is **fully self-contained** as of v0.2.0 — every bridge method works out of the box, including visibility windows, heliacal-rising prediction, eclipse search, and solar-elongation queries (using algebraic synodic-cycle propagation; ~±1 day Antikythera-grade precision). No JPL ephemeris kernel required.

Optional extras for sub-arcsec-precision validation against modern ephemerides:

```bash
pip install "antikythera-spectral[ephemeris]"    # adds skyfield + jplephem; pass precise=True
pip install "antikythera-spectral[hypotheses]"   # adds scipy (for chi-square in H-H1)
pip install "antikythera-spectral[plot]"         # adds matplotlib
pip install "antikythera-spectral[all]"          # everything above
```

In algebraic mode (the default), the four sky-truth bridge methods accept `precise=False` (the default) and use frozen per-planet anchors + closed-form propagation. With `precise=True` they switch to skyfield + a JPL DE-kernel for sub-arcsec accuracy. See [ADR 0011](https://github.com/lemonforest/mlehaptics/blob/main/docs/antikythera-maths/antikythera-spectral/docs/adr/0011-algebraic-default-precise-opt-in.md) for the discipline.

### Pyodide / micropip (in-browser)

```python
import micropip
await micropip.install("antikythera-spectral[ephemeris]")
```

The full Bridge API is available from a Pyodide REPL with no server-side Python.

## Quick start (Python)

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
antikythera-spectral hypotheses --csv-out -
```

## What can you do with it?

- **Encode** any Julian date as a state vector across all of the mechanism's dials.
- **Decode** any state vector back to per-dial residues (round-trip is exact for the LCM variant).
- **Convert dates** between Gregorian, Julian, Athenian archonship + Attic months, and Olympiad year — the four calendar systems an ancient Greek astronomer or modern reader might use.
- **Compute visibility windows** for each planet (heliacal rising / setting + solar elongation), the astronomical reality that gates the operator's recalibration workflow.
- **Search for eclipses** in any date band via sky-driven ephemeris enumeration.
- **Simulate the operator workflow** (§11.6.16 of the research notebook): start at a date, advance, observe at heliacal rising, re-anchor, repeat.
- **Compare reconstructions** — Freeth 2021 vs Wright vs Price 1974 dial readings simultaneously at any date.
- **Compare ephemeris kernels** — DE421 vs DE441 vs DE441_part1 deltas at a chosen JD/body in arc-seconds, kilometers, AU.
- **Run the 31-row hypothesis battery** that drives the research notebook, get JSON / CSV output.
- **Override gear ratios** (what-if mode) — re-encode with arbitrary p/q to explore alternative period relations like the canonical Venus 5/8.
- **Inventory by fragment** (archaeological mode) — list which gears are attested in fragments A/B/C/D vs reconstructed by Freeth.
- **Babylonian Goal-Year overlay** — given a planet+date, return what an astronomer using the 47-year Mars cycle (or 59-year Saturn, etc.) would have predicted.
- **Animation export** — emit a time-series of states over a date range for a viewer / animation frontend.

## Bridge API

[`docs/bridge_api.md`](https://github.com/lemonforest/mlehaptics/blob/main/docs/antikythera-maths/antikythera-spectral/docs/bridge_api.md) is the consumer-facing contract. 28 methods grouped by purpose; each returns a Pyodide-JSON-serializable `{"ok": True, ...}` dict. Numpy arrays in return values are real-valued (`Float32` for amplitude payloads) so JS consumers can use `new Float32Array(...)` directly.

## Hypothesis battery

The package ships the same 31-row H-battery the research scaffold runs. Headlines:

- **22 PASS** — encoder round-trips perfectly for all D variants; pin-and-slot encodes T-symmetry breaking; manufacturing tolerance is fine for one Metonic cycle; etc.
- **3 PARTIAL** — the proxy-metric Pareto for {7, 17}; the prime spectrum vs null model; H-H1 chi-square against Almagest periods.
- **3 FAIL** — including E-H2: uniform Mars encoder peak ≥ 150° (this is *expected*; the failure mode is the rationale for the §11.6.16 operator-recalibration framing).
- **3 UNDETERMINED** — open exploration F-series rows, plus skyfield-gated rows when no ephemeris kernel is on disk.

See the [research notebook](https://github.com/lemonforest/mlehaptics/blob/main/docs/antikythera-maths/antikythera_spectral_research_notebook.md) for the full row-by-row narrative.

## Documentation

| Topic | Link |
| --- | --- |
| Research notebook (the project narrative) | [`antikythera_spectral_research_notebook.md`](https://github.com/lemonforest/mlehaptics/blob/main/docs/antikythera-maths/antikythera_spectral_research_notebook.md) |
| Bridge API contract | [`bridge_api.md`](https://github.com/lemonforest/mlehaptics/blob/main/docs/antikythera-maths/antikythera-spectral/docs/bridge_api.md) |
| Calendar systems reference | [`CALENDAR_SYSTEMS.md`](https://github.com/lemonforest/mlehaptics/blob/main/docs/antikythera-maths/antikythera-spectral/docs/CALENDAR_SYSTEMS.md) |
| Ephemeris kernels (DE421 / DE441 / etc.) | [`EPHEMERIS_KERNELS.md`](https://github.com/lemonforest/mlehaptics/blob/main/docs/antikythera-maths/antikythera-spectral/docs/EPHEMERIS_KERNELS.md) |
| ΔT discussion (Earth-rotation drift at -200 BCE) | [`DELTA_T_MODEL.md`](https://github.com/lemonforest/mlehaptics/blob/main/docs/antikythera-maths/antikythera-spectral/docs/DELTA_T_MODEL.md) |
| Operator workflow simulation (§11.6.16) | [`OPERATOR_WORKFLOW.md`](https://github.com/lemonforest/mlehaptics/blob/main/docs/antikythera-maths/antikythera-spectral/docs/OPERATOR_WORKFLOW.md) |
| Roadmap | [`ROADMAP.md`](https://github.com/lemonforest/mlehaptics/blob/main/docs/antikythera-maths/antikythera-spectral/ROADMAP.md) |
| Changelog | [`CHANGELOG.md`](https://github.com/lemonforest/mlehaptics/blob/main/docs/antikythera-maths/antikythera-spectral/python/CHANGELOG.md) |

## Citing

If `antikythera-spectral` contributes to a paper or write-up, please cite both the package and the research notebook:

```bibtex
@software{antikythera_spectral,
  author = {Kirkland, Steven},
  title = {antikythera-spectral: Hyperdimensional-computing model of the Antikythera mechanism},
  year = {2026},
  url = {https://github.com/lemonforest/mlehaptics/tree/main/docs/antikythera-maths/antikythera-spectral},
  version = {0.1.0}
}
```

## License

GPL-3.0-or-later. Matches the license of the parent monorepo.

## See also

Sibling packages in the same monorepo:

- [`chess-spectral`](https://pypi.org/project/chess-spectral/) — the same HDC + cyclic-group-algebra framing applied to chess, with native C accelerator.

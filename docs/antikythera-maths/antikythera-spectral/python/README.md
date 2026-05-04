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
>>> from antikythera_spectral import bridge, default_encode
>>> result = bridge.get_dial_state(jd_tdb=1684500.0)   # ~205 BCE
>>> result['ok']
True
>>> round(result['dials']['Metonic']['angle_deg'], 2)
355.07
>>> result['dials']['Mars_synodic_period_relation']['modulus']
133
>>> result['state']['dtype']        # v0.3.0: bridge default flipped to bit-packed
'uint64'
>>> result['backend']
'bit'

# Top-level shortcut for "encode any date as a hypervector" (v0.3.0):
# default backend is the bit-packed ALU; pass backend="complex128" for the
# legacy reference encoder. See ADR 0012 for the algebra-first rationale.
>>> hv = default_encode(1684500.0)
>>> hv.dtype
dtype('uint64')
>>> hv.shape
(15,)                              # ceil(940/64) packed words = 120 B (vs 15 KB)

# Mars planetary models (v0.3.0): four longitude models × three named
# reconstruction param sets. The `bronze` model is the algebra/eigenbasis
# projection of the gear-ratio cyclic-group representation through the
# pin-and-slot phase-space transform — see ADR 0012.
>>> from antikythera_spectral import mars_models
>>> round(mars_models.mars_longitude_bronze(
...     1721000.0, mars_models.FREETH_2012_MARS_PARAMS
... ), 2)
124.09

# Reproduce F&J 2012 Fig 39's "nearly 38°" Mars peak error from
# the bare deferent + epicycle on the middle 7 retrogrades vs
# JPL DE422 (lazy; needs the kernel cached).
>>> finding = mars_models.fj_38deg_finding()
>>> round(finding["rms_deg"], 2)
38.85

# Bit-packed binary HDC ALU (v0.3.0): every operation reduces to
# integer bit-ops on packed uint64s. 125x smaller than complex128;
# 2-10x faster bind. See figures/bit_alu_findings.md for the benchmark.
>>> from antikythera_spectral import bit_alu
>>> import numpy as np
>>> rng = np.random.default_rng(0)
>>> a = bit_alu.random_hv(940, rng)
>>> b = bit_alu.random_hv(940, rng)
>>> abs(bit_alu.similarity(a, b, 940)) < 0.1   # uncorrelated random pair
True
>>> bit_alu.hamming_distance(bit_alu.bind(a, b), bit_alu.bind(a, b))
0
```

## Quick start (CLI)

```bash
antikythera-spectral encode --jd 1684500.0
antikythera-spectral visibility --planet mars --from-jd 1684500 --to-jd 1685000
antikythera-spectral compare ephemerides --jd 1684500 --body mars \
                                          --kernel-a de421 --kernel-b de441_part1

# v0.3.0: compare Mars models with the new bronze + named param sets
antikythera-spectral compare models --jd 1721000 --body mars \
    --model-a bronze --model-b equant --params freeth_2012 --kernel de422

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
- **Run Hellenistic Mars planetary models** (`antikythera_spectral.mars_models`, v0.3.0): four longitude models (uniform, epicycle-only, equant, **bronze** — the gear-ratio cyclic-group projection through the pin-and-slot phase-space transform) under three named param sets (Ptolemy / Almagest IX-X, Freeth & Jones 2012, Freeth 2021). `mars_models.fj_38deg_finding()` reproduces F&J 2012 Fig 39's "nearly 38°" Mars peak error directly from the bare deferent + epicycle on the middle 7 retrogrades of the 1st century BC vs JPL DE422 (lands at 38.85° within 0.85°). See [ADR 0012](https://github.com/lemonforest/mlehaptics/blob/main/docs/antikythera-maths/antikythera-spectral/docs/adr/0012-algebra-eigenbasis-vs-cad-scope.md) for the algebra-first scope discipline; full audit in [`figures/mars_38deg_gap_findings.md`](https://github.com/lemonforest/mlehaptics/blob/main/docs/antikythera-maths/figures/mars_38deg_gap_findings.md).
- **Use the bit-packed binary HDC ALU** (`antikythera_spectral.bit_alu`, v0.3.0): a second encoder backend where every operation reduces to integer bit-ops (XOR, popcount, shift) on packed `uint64` words — no floating point, no complex multiplies, no matrix work. 125× smaller per hypervector than the `complex128` reference (120 B vs 15 KB at D=940); 2–10× faster `bind` scaling with D. Same algebraic substrate (cyclic-group representation of the dials), pure-bitwise primitives. The cleanest possible incarnation of ADR 0012's algebra-first discipline. Benchmark + cycle-alignment analysis (solar vs sidereal day for `permute = sigma_day` — solar wins) in [`figures/bit_alu_findings.md`](https://github.com/lemonforest/mlehaptics/blob/main/docs/antikythera-maths/figures/bit_alu_findings.md).
- **Encode without picking a backend** (`antikythera_spectral.default_encode`, v0.3.0): one-liner that returns a hypervector under the package's default backend (the bit-packed ALU, per ADR 0012). Pass `backend="complex128"` to recover the legacy reference shape. The bridge's `get_dial_state` / `decode_dial` / `decode_to_jd` likewise default to the bit-packed backend in v0.3.0, with explicit `backend="complex128"` opt-out for v0.2.x consumers.
- **Run the 31-row hypothesis battery** that drives the research notebook, get JSON / CSV output.
- **Override gear ratios** (what-if mode) — re-encode with arbitrary p/q to explore alternative period relations like the canonical Venus 5/8.
- **Inventory by fragment** (archaeological mode) — list which gears are attested in fragments A/B/C/D vs reconstructed by Freeth.
- **Babylonian Goal-Year overlay** — given a planet+date, return what an astronomer using the 47-year Mars cycle (or 59-year Saturn, etc.) would have predicted.
- **Animation export** — emit a time-series of states over a date range for a viewer / animation frontend.

## Bridge API

[`docs/bridge_api.md`](https://github.com/lemonforest/mlehaptics/blob/main/docs/antikythera-maths/antikythera-spectral/docs/bridge_api.md) is the consumer-facing contract. 28 methods grouped by purpose; each returns a Pyodide-JSON-serializable `{"ok": True, ...}` dict. State-vector payloads serialise differently per backend: `backend="bit"` (v0.3.0 default) ships `state.packed_uint64` as a JSON list of integers (each ≤ 2⁶⁴-1; JS consumers can use `BigInt` or split into `uint32` pairs), while `backend="complex128"` ships `state.interleaved_f32` as `[re0, im0, re1, im1, …]` length 2·D so JS can wrap it directly in a `Float32Array`. Per-dial residues / angles are floats / ints either way and fit standard JSON.

v0.3.0 extends `bridge.compare_models` with the `bronze` model name and a new optional `params` argument (`"ptolemy"` / `"freeth_2012"` / `"freeth_2021"`); v0.2.x callers continue to work unchanged. Direct Python access to the new Mars / bit-ALU primitives is via the `antikythera_spectral.mars_models` and `antikythera_spectral.bit_alu` facades — these are not part of the bridge contract (no Pyodide JSON serialization needed; numpy arrays / floats / dicts).

**v0.3.0 default-backend flip.** `bridge.get_dial_state` now returns a bit-packed state by default — the `state` sub-dict has `dtype: "uint64"`, `shape: [n_words]` (= `ceil(D/64)`), `n_bits: D`, and `packed_uint64: list[int]`. `bridge.decode_dial` / `decode_to_jd` auto-detect the backend from the input shape (uint64 array → bit decoder; complex128 / interleaved-Float32 → reference decoder). v0.2.x consumers pass `backend="complex128"` to recover the legacy interleaved-Float32 shape; nothing else changes in the API. The dial residues / angles in the response are backend-independent.

## Two HDC backends, one algebra

The package ships two HDC backends — `complex128` (FHRR-style; the v0.2.x reference) and `bit_alu` (BSC-style; the v0.3.0 default). Both implement the **same algebraic substrate**: a cyclic-group representation of the Antikythera dials. We provide both deliberately because they sit at different points on a structural-fidelity / representation-theoretic-fidelity axis:

- **`bit_alu`** shares two structural properties with the bronze mechanism that `complex128` does not. The state space is finite (`{0,1}^D` vs `ℂ^D`), and the operations (XOR, popcount, bit-rotate) are exact at the representation level rather than floating-point approximations. The bronze realises ℤ/Nℤ literally — a 53-tooth gear has 53 distinguishable rotational positions, full stop — and the binary substrate parallels that discrete substrate one level up the abstraction stack. Hardware-irreducible binary HDC is a real engineering literature (Kanerva 2009 §3 motivates BSC on this basis; Schmuck/Benini/Rahimi 2019 build bit-serial accelerators with no multiplier).

- **`complex128`** is closer to the *representation-theoretic eigenbasis*. Pontryagin duality on a finite cyclic group gives the complex characters `e^{2πi·k/N}` as the natural orthonormal basis; FHRR-style binding via complex multiplication is exactly the convolution-on-characters story. So if you ask "what is the textbook eigenbasis of ℤ/Nℤ?" — that's the complex backend's home.

**Important caveat we want to flag.** Neither backend matches the bronze's actual *tooth count*. Both are holographic abstractions at dimension `D = 940` or `13440`, vastly larger than any single gear's tooth count (max ~250). The bit-ALU's discreteness is a *representation-level* parallel, not a *mechanism-level* identity. We are not claiming the bit ALU is "the" irreducible bit-level translation of the Antikythera mechanism — the mechanism is irreducibly *integer-on-cyclic-groups*, and binary HDC is one of several discrete encodings of that, not a privileged one.

**Why both ship.** The bit ALU is the v0.3.0 default because, in the ADR-0012 algebra-first discipline, "no FPU calls anywhere in the encode/decode path" is a meaningful purity property: floating-point introduces concepts (ULP, gradual underflow, NaN) that have zero counterpart in bronze gearing. The complex128 backend is preserved because the H-battery's algebraic identities (B-H1 round-trip, σ_day unit-operator) are most naturally stated in the FHRR / character-of-cyclic-group language, and because the complex Gaussian basis has cleaner decode behaviour for cross-talk-sensitive H-battery rows.

References for the framing: Kanerva (2009, *Cognitive Computation* 1:139); Plate (1995, *IEEE TNN* 6); Schlegel/Neubert/Protzel (2022, *AI Review* 55:4523, BSC vs FHRR comparison); Schmuck/Benini/Rahimi (2019, *ACM JETC* 15, hardware-binary HDC). For the bronze: Freeth et al. 2006 *Nature* 444:587; Freeth & Jones 2012 *ISAW Papers* 4; Freeth et al. 2021 *Sci. Rep.* 11:5821.

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
| Mars 38° gap audit (10-analysis decomposition) | [`mars_38deg_gap_findings.md`](https://github.com/lemonforest/mlehaptics/blob/main/docs/antikythera-maths/figures/mars_38deg_gap_findings.md) |
| Bit-ALU benchmark + cycle-alignment (v0.3.0) | [`bit_alu_findings.md`](https://github.com/lemonforest/mlehaptics/blob/main/docs/antikythera-maths/figures/bit_alu_findings.md) |
| ADRs (architecture decisions) | [`docs/adr/`](https://github.com/lemonforest/mlehaptics/tree/main/docs/antikythera-maths/antikythera-spectral/docs/adr) — ADR 0011 (algebraic default), ADR 0012 (algebra/eigenbasis vs CAD scope) |
| Roadmap | [`ROADMAP.md`](https://github.com/lemonforest/mlehaptics/blob/main/docs/antikythera-maths/antikythera-spectral/ROADMAP.md) |
| Changelog | [`CHANGELOG.md`](https://github.com/lemonforest/mlehaptics/blob/main/docs/antikythera-maths/antikythera-spectral/CHANGELOG.md) |

## Citing

If `antikythera-spectral` contributes to a paper or write-up, please cite both the package and the research notebook:

```bibtex
@software{antikythera_spectral,
  author = {Kirkland, Steven},
  title = {antikythera-spectral: Hyperdimensional-computing model of the Antikythera mechanism},
  year = {2026},
  url = {https://github.com/lemonforest/mlehaptics/tree/main/docs/antikythera-maths/antikythera-spectral},
  version = {0.3.0}
}
```

## License

GPL-3.0-or-later. Matches the license of the parent monorepo.

## See also

Sibling packages in the same monorepo:

- [`chess-spectral`](https://pypi.org/project/chess-spectral/) — the same HDC + cyclic-group-algebra framing applied to chess, with native C accelerator.

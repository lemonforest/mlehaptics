# ephemerides-spectral roadmap

Status of advertised CLI / Bridge API methods. Mirrors the
[antikythera-spectral ROADMAP](../antikythera-spectral/ROADMAP.md)
discipline: every entry the help text advertises is either ✅ wired
(real implementation behind it) or ⏳ pending (planned for a specific
version).

## Released versions

| Version | Date | Headline |
|---|---|---|
| **v0.2.0** | 2026-05-04 | Phase 9 coverage extension. The hardcoded Jupiter–Saturn 5:2 entry is promoted to a structured `RESONANCES` SSOT table; three new resonances are wired alongside it: Neptune–Pluto 3:2 (orbital), Io–Europa 2:1 + Europa–Ganymede 2:1 (the two legs of the Jovian Laplace resonance). The reference encoder, the BIP encoder, and the C codegen all walk the same table — single source of truth in `research/laplacian.py`. Encoded phase residues for Io / Europa / Ganymede / Neptune / Pluto shift relative to v0.1.0 (their breathing modulation is now active); Earth's phase is unchanged; the 0.0002 rad Earth phase floor at +20 yr against DE421 is preserved. C port: `es_n_couplings` grows from 1 to 4; byte-for-byte parity with Python verified across all 26 bodies. |
| v0.1.0 | 2026-05-04 | First public release on PyPI. 26-body Sol Star System Laplacian (diagonal mean motions + Mercury PN correction + static gravitational fiber couplings); Phase 9 state-dependent (non-autonomous) breathing couplings — Jupiter–Saturn 5:2 resonance modulated via 1024-entry int32 cosine LUT (Q1.14, 4 KB), end-to-end on the integer ALU; ALU-native BIP encoder over `Z_{2^32}` (uint32 cyclic-group binding via free overflow) with 305× speedup vs the FPU reference and 256 KB state at D=65536; FPU `complex128` reference encoder preserved for the algebraic identities (Syzygy operator, observer binding, regression baseline); pre-flight bounds check + scoped `np.errstate(over='raise')` on signed-int64 multiplies; lenient `errstate(over='ignore')` + warning filter on the uint64 accumulator; rich CLI (9 subcommands: `version`, `bodies`, `kernel list`, `resolution`, `encode`, `local-view`, `eclipse`, `couplings`, `breathing`); Pyodide-friendly bridge with input validation and `{ok: True/False}` JSON contract; codegen-stamped frozen-data manifest. |

## Next planned

| Version | Theme |
|---|---|
| v0.2.x | Bug fixes, documentation polish, additional unit-test coverage on top of v0.2.0. CHANGELOG-driven; no API breakage. |
| v0.3.x | **First-principles Phase 9 derivation.** Replace the phenomenological `α = 0.1` modulation depth with values derived from a Hamilton/Delaunay-variable Lagrangian (Lie-series perturbation theory around each resonance). Connects to the adaptive-Kuramoto literature on derived-from-physics PDDP rules. |
| v0.4.x | **CORDIC topocentric rendering.** The cosine LUT is half a CORDIC kernel; the rotation half can subsume the topocentric `lat/lon` observer-bind, taking that path off the FPU. |
| later | **Multi-millennium sweep against DE441.** Re-derive Metonic + Saros anchors against the full 3.3 GB DE441 with breathing couplings active. Propagator drift floor (~0.0002 rad at +20 yr in v0.1.0 against DE421) re-measured at +200 yr / +2000 yr horizons. |

## Phase status (carried over from v0.1.0 plan)

| Phase | Status | Description |
|-------|--------|-------------|
| 0 — Project framing & sibling-folder discipline | ✅ shipped | Sits beside antikythera-spectral; cross-references in both notebooks. |
| 5 — Historical resonance (Metonic / Saros) | ✅ shipped (v0.1.0) | Lunar projection round-trip at +19 yr against DE421. |
| 6 — Interaction fibers (off-diagonal Laplacian) | ✅ shipped (v0.1.0) | Sun-planet / moon-planet / J-S resonance / asteroid-Jupiter coupling table. |
| 7 — Bit-serialised prototype | ✅ shipped (v0.1.0) | 305× speedup vs FPU reference at +20 yr, 0.0002 rad Earth phase floor. |
| 8 — Dimensional expansion | ✅ shipped (v0.1.0) | D = 2^16 .. 2^20 sweep; SNR scales linearly with D. |
| 9 — Breathing Laplacian | ✅ shipped (v0.1.0) | State-dependent off-diagonal weights; integer cosine LUT; PN correction. |
| 10 — Phase 9 coverage extension | ✅ shipped (v0.2.0) | RESONANCES SSOT table; J–S 5:2 + N–P 3:2 + Io–Europa 2:1 + Europa–Ganymede 2:1. |
| 11 — First-principles modulation depths | ⏳ v0.3.x | Replace phenomenological α with Lagrangian-derived values. |
| 12 — CORDIC topocentric | ⏳ v0.4.x | Observer-bind off the FPU. |
| 13 — DE441 multi-millennium sweep | ⏳ later | Re-anchor Metonic + Saros against full 3.3 GB kernel. |
| 14 — C BIP source port | ✅ shipped (alongside v0.1.0) | Embedded-friendly integer-only kernel; byte-exact parity with the Python reference at +20 yr; codegen reads from the same Python research SSOT. Lives at [`c/`](c/). |

## Bridge ↔ CLI parity

Every CLI subcommand maps 1:1 to a bridge method; every bridge method has CLI access. Pinned by inspection at v0.1.0:

| CLI subcommand | Bridge method | Status |
|---|---|---|
| `version` | `bridge.get_version()` | ✅ |
| `bodies` | `bridge.list_bodies()` | ✅ |
| `kernel list` | `bridge.list_kernels()` | ✅ |
| `resolution` | `bridge.get_resolution(body, D)` | ✅ |
| `encode` | `bridge.get_system_state(jd, backend, kernel, force_high_res, D)` | ✅ |
| `local-view` | `bridge.get_local_view(jd, body, lat, lon, kernel)` | ✅ |
| `eclipse` | `bridge.get_eclipse_probability(jd, kernel)` | ✅ |
| `couplings` | `bridge.list_couplings()` | ✅ |
| `breathing` | `bridge.get_breathing_modulation(jd, pair, n_lobes, kernel)` | ✅ |

Future CLI / bridge surface lands here as the corresponding ROADMAP rows ship.

## References

- [Research notebook](../ephemerides_spectral_research_notebook.md) — running design + §1.4 mathematical positioning of the breathing Laplacian
- [RBS-HDC evaluation](../research/resonant_bit_serialized_hdc_evaluation.md) — Q-format discipline, overflow trap, ALU-native LUT design
- [Antikythera-spectral ROADMAP](../antikythera-spectral/ROADMAP.md) — sibling project for cross-pollination patterns
- [Chess-spectral notebook §20.13–§20.20](../../chess-maths/chess_spectral_research_notebook.md) — `Z_{640}` ↔ `Z_{2^32}` algebraic-family alignment

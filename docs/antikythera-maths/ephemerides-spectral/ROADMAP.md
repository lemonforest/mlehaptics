# ephemerides-spectral roadmap

Status of advertised CLI / Bridge API methods. Mirrors the
[antikythera-spectral ROADMAP](../antikythera-spectral/ROADMAP.md)
discipline: every entry the help text advertises is either ✅ wired
(real implementation behind it) or ⏳ pending (planned for a specific
version).

## Released versions

| Version | Date | Headline |
|---|---|---|
| **v0.3.1** | 2026-05-04 | **C-in-wheel + spectral syzygy window search + DE441 error-spectrum FFT.** Native C backend (`backend="c"`) bundled in platform wheels via cibuildwheel; **~1000× speedup** on the encode hot loop; byte-exact parity with the Python BIP encoder. Spectral syzygy window search (`find-syzygies`) replaces v0.3.0's point-evaluation `eclipse --jd` for window queries — `O(n_syzygies × confirmation)` instead of `O(window_days × encode)`, ~1000× faster for multi-decade windows. New `de441_error_spectrum.py` FFTs the per-body residual; **headline finding: Jupiter–Saturn show identical 9.56-yr peaks at ±45° amplitude — the smoking-gun missing-coupling signal motivating v0.4+'s first-principles α derivation**. Pure-Python `py3-none-any` wheel preserved for Pyodide / WASM. |
| v0.3.0 | 2026-05-04 | **Time scales + DE441 sweep + natural-resonance group.** New bridge surface for Mars Sol Date / Mars Coordinated Time (Allison & McEwen 2000) and mean lunar synodic + sidereal phase primitives. LTE440 (Lin et al. 2025) registered as a known lunar-time ephemeris (metadata only; no auto-download). New CLI subcommands `time-mars`, `time-lunar`, `lunar-kernels`, `natural-group`. New `research/de441_sweep.py` runs the BIP encoder across J2000 ± 14,000 yr against DE441 ground truth — see [`figures/de441_full_sweep.md`](../figures/de441_full_sweep.md) for the table (Earth/Venus/Uranus < 10° at multi-millennium horizons; Mars 14°; Mercury 84°; Jupiter/Saturn/Neptune/Pluto/Moon hit >150° — the structural-limit signature of phenomenological α). New `bridge.get_natural_resonance_group()` returns the resonance-derived cyclic group (`Z_30 = Z_2 × Z_3 × Z_5` for the v0.2.0 four-resonance set), distinct from the encoder's architectural `Z_{2^32}`. LTC deferred to v0.4+. |
| v0.2.0 | 2026-05-04 | Phase 9 coverage extension. The hardcoded Jupiter–Saturn 5:2 entry is promoted to a structured `RESONANCES` SSOT table; three new resonances are wired alongside it: Neptune–Pluto 3:2 (orbital), Io–Europa 2:1 + Europa–Ganymede 2:1 (the two legs of the Jovian Laplace resonance). The reference encoder, the BIP encoder, and the C codegen all walk the same table — single source of truth in `research/laplacian.py`. Encoded phase residues for Io / Europa / Ganymede / Neptune / Pluto shift relative to v0.1.0 (their breathing modulation is now active); Earth's phase is unchanged; the 0.0002 rad Earth phase floor at +20 yr against DE421 is preserved. C port: `es_n_couplings` grows from 1 to 4; byte-for-byte parity with Python verified across all 26 bodies. |
| v0.1.0 | 2026-05-04 | First public release on PyPI. 26-body Sol Star System Laplacian (diagonal mean motions + Mercury PN correction + static gravitational fiber couplings); Phase 9 state-dependent (non-autonomous) breathing couplings — Jupiter–Saturn 5:2 resonance modulated via 1024-entry int32 cosine LUT (Q1.14, 4 KB), end-to-end on the integer ALU; ALU-native BIP encoder over `Z_{2^32}` (uint32 cyclic-group binding via free overflow) with 305× speedup vs the FPU reference and 256 KB state at D=65536; FPU `complex128` reference encoder preserved for the algebraic identities (Syzygy operator, observer binding, regression baseline); pre-flight bounds check + scoped `np.errstate(over='raise')` on signed-int64 multiplies; lenient `errstate(over='ignore')` + warning filter on the uint64 accumulator; rich CLI (9 subcommands: `version`, `bodies`, `kernel list`, `resolution`, `encode`, `local-view`, `eclipse`, `couplings`, `breathing`); Pyodide-friendly bridge with input validation and `{ok: True/False}` JSON contract; codegen-stamped frozen-data manifest. |

## Next planned

| Version | Theme |
|---|---|
| v0.3.x | Bug fixes, documentation polish, additional unit-test coverage on top of v0.3.0. CHANGELOG-driven; no API breakage. |
| v0.4.x | **First-principles per-resonance α.** Replace the phenomenological `α = 0.1` modulation depth with values derived from a Hamilton/Delaunay-variable Lagrangian (Lie-series perturbation theory around each resonance). Empirically motivated by the v0.3.0 DE441 sweep, which shows Jupiter/Saturn/Neptune/Pluto/Moon phase-scrambling at multi-millennium horizons under uniform `α`. |
| v0.4.x (research) | **DE441 vs DE442 spectral error signature** *(experiment)*. Build two BIP instruments from scratch — one calibrated only from DE441, one only from DE442. For a sample of JDs across both kernels' overlap, encode the system on both and compute per-body residue deltas: `Δφ_b = (A.phases[b] − B.phases[b]) mod 2^32`. Project the deltas onto the encoder's eigenbasis (Laplacian eigenmodes). Hypothesis: DE442's corrections to DE441 live in a coherent eigenmode subspace — the *spectral signature* of the kernel-update. If true, the signature lets us **predict** where ephemeris error correction is structurally needed without needing the corrected kernel. New `research/de441_vs_de442_signature.py`; figures/ entry with the eigenmode decomposition. |
| v0.4.x | **Spectral kernel + diagnosed-fiber patches.** Architectural reframing motivated by the v0.3.1 FFT analysis: the Laplacian already decomposes as `L_trunk + L_pn + L_static + RESONANCES`; add a fourth layer `L_diagnosed` — *per-fiber* correction terms read off the FFT residual peaks. A patch lives at one of three scopes: (1) **diagonal per-body** (Mars-only mean-motion tweak; affects nothing else; safe); (2) **off-diagonal pair** (Earth–Jupiter coupling correction; affects only those two bodies; safe for unconnected bodies); (3) **resonance-aliased** (e.g., Earth's 5.3-yr peak which is sub-Nyquist-aliased and may share physics with another body's residual; **patching one without the conjugate WILL break the conjugate's accuracy** — multi-body residuals need joint patches respecting the resonance topology). New `research/diagnosed_fibers.py` introducing `DiagnosedPatch` dataclass + `apply_patches(L, patches)`; tests gate on "patching Earth does not change Mars phases beyond ULP" for diagonal patches and on "joint Earth-Jupiter patch self-consistently corrects both" for off-diagonal patches. Empirically, the v0.3.1 FFT analysis tells us *which* patches are safe to author this way (the body-local outer-planet peaks at their own orbital periods are clean diagonal candidates) and which need a coupled-body treatment (Earth's aliased 5.3-yr peak; Mars's 7.96-yr peak that may be shared with Saturn). |
| v0.4.x | **Spectral syzygy window search.** Replace v0.3.0's point-evaluation `eclipse --jd` (encode-then-check) with `find-syzygies --from-jd … --to-jd …`. The current surface is the *least* HDC-native usage: encoding the system and dotting against `S` at a single JD throws away the structure the encoder is built for. The bronze antikythera's Saros dial doesn't encode-and-check either — it turns gears whose ratios *are* the Saros cycle. Implementation: enumerate window-multiples of the slow Saros / Metonic / synodic-month / lunar-node modes in closed form from the Q-format `omega` values; confirm each candidate by spectral projection onto `S`. Cost goes from `O(window_days × encode_cost)` to `O(n_syzygies × confirmation_cost)`. New `bridge.find_syzygies(jd_lo, jd_hi, kind, threshold)` and CLI `find-syzygies`. Keeps `eclipse --jd` for backwards compatibility but documents it as the deprecated point-evaluation pattern. |
| v0.5.x | **CORDIC topocentric rendering.** The cosine LUT is half a CORDIC kernel; the rotation half can subsume the topocentric `lat/lon` observer-bind, taking that path off the FPU. |
| v0.5.x or later | **LTC (Lunar Coordinated Time).** Pending NASA + international space-agency standardisation (target 2026–2028 per April 2024 White House directive). LTE440 (Lin et al. 2025) ships the underlying SPICE-format conversion ephemeris with 0.15 ns accuracy through 2050; ephemerides-spectral gains an `LTC` namespace in the bridge mirroring `MarsTime` once the LTC epoch + day-length convention are formalised. |
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
| 11 — Time scales + DE441 sweep | ✅ shipped (v0.3.0) | MSD/MTC + lunar phase + LTE440 awareness + natural-resonance group + DE441 ±14,000 yr sweep. |
| 12 — C-in-wheel + syzygy window + FFT | ✅ shipped (v0.3.1) | scikit-build-core platform wheels via cibuildwheel; `backend="c"` ~1000× speedup; spectral `find-syzygies` window search; DE441 error-spectrum FFT identifying the J–S 9.56-yr ±45° missing-coupling peak. |
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
| `time-mars` | `bridge.jd_to_mars_time(jd_utc)` / `bridge.mars_time_to_jd(msd)` | ✅ (v0.3.0) |
| `time-lunar` | `bridge.get_lunar_phase(jd_tdb)` | ✅ (v0.3.0) |
| `lunar-kernels` | `bridge.list_lunar_kernels()` | ✅ (v0.3.0) |
| `natural-group` | `bridge.get_natural_resonance_group()` | ✅ (v0.3.0) |
| `find-syzygies` | `bridge.find_syzygies(jd_lo, jd_hi, kind, threshold)` | ✅ (v0.3.1) |

Future CLI / bridge surface lands here as the corresponding ROADMAP rows ship.

## References

- [Research notebook](../ephemerides_spectral_research_notebook.md) — running design + §1.4 mathematical positioning of the breathing Laplacian
- [RBS-HDC evaluation](../research/resonant_bit_serialized_hdc_evaluation.md) — Q-format discipline, overflow trap, ALU-native LUT design
- [Antikythera-spectral ROADMAP](../antikythera-spectral/ROADMAP.md) — sibling project for cross-pollination patterns
- [Chess-spectral notebook §20.13–§20.20](../../chess-maths/chess_spectral_research_notebook.md) — `Z_{640}` ↔ `Z_{2^32}` algebraic-family alignment

# ephemerides-spectral CHANGELOG

Per-version change log for the `ephemerides-spectral` PyPI package.
The full project changelog (with pointers into the research notebook
and cross-pollination notes) lives at
[`../CHANGELOG.md`](../CHANGELOG.md).

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

(no entries yet — next entries land after v0.18.0)

## [0.18.0] — 2026-05-06

**Body Architecture: inner/outer system classification of heliocentric bodies via the resonance-weighted gateway-graph Laplacian Fiedler partition.** Pure-Python addition; **no ABI bump** (`ES_ABI_VERSION = 8` unchanged from v0.17.0).

### Added — Pythonic API

- `_research.body_architecture` — new module containing the resonance-weighted gateway-graph Laplacian Fiedler-partition machinery promoted from research notebook §13.8 to a stable ship surface.
- `_research.body_architecture.HELIOCENTRIC_BODIES` — frozen list of the v0.16.0 13-body Tier-1 heliocentric roster (planets + main-belt asteroids; Sun excluded; moons excluded). The default subset for `compute_body_architecture`.
- `_research.body_architecture.INNER_CLASS = "inner"`, `OUTER_CLASS = "outer"` — class label constants.
- `_research.body_architecture.compute_body_architecture(bodies: Optional[List[str]] = None) -> Dict` — main entry. Returns `{ok, n_bodies, lambda_2, bodies, partitions}` where `bodies` is a list of `{name, class, fiedler_value, period_days}` records (sorted by `fiedler_value` ascending) and `partitions` is `{"inner": [...], "outer": [...]}`. Raises `ValueError` on empty / duplicate / unknown / zero-period inputs.

### Added — bridge dict API (Pyodide-compatible)

- `bridge.body_architecture(target: Optional[str] = None) -> dict` — full partition by default; single-body record if `target` given (lower-cased; must be in the heliocentric roster). Returns `{ok: False, error: ...}` on rejection.

### Added — CLI

- `body-architecture` subcommand — flags: `--target <name>` (optional; if given, returns just that body's record), `--pretty`. Prints the same dict the bridge returns.

### Sign-convention

The Fiedler-vector sign is anchored to the shortest-period body in the input roster being positive. This makes the inner/outer label assignment reproducible across platforms regardless of LAPACK pivoting. For the default 13-body roster this means **mercury is always positive** (largest `+0.329`) and **pluto is always negative** (deepest `−0.585`).

### Default classification

The default 13-body heliocentric roster classifies into:

* **Inner 8** (positive Fiedler entry): mercury, venus, terra, mars, vesta, ceres, pallas, hygiea
* **Outer 5** (negative Fiedler entry): jupiter, saturn, uranus, neptune, pluto

The cyclic-group encoder discovers the canonical asteroid-belt boundary without being told it exists. Pluto and Neptune share the deepest entry (`−0.585`) via their 2:3 mean-motion lock.

### Research origin (notebook §13.8 + §13.9)

The §13 thread tested four edge weightings on the gateway-graph Laplacian:

| Weighting | Spearman ρ vs empirical Δv | Matthews φ | Notes |
| --- | ---: | ---: | --- |
| inv_dv (baseline) | +0.743 | +0.336 | Mercury-isolation predictor |
| inv_synodic (control) | −0.301 | +0.083 | Pallas/Ceres degeneracy null |
| **resonance (this ship)** | +0.632 | +0.207 | Inner/outer architectural partition |
| hybrid_dv_resonance | **+0.857** | +0.298 | Clears continuous Spearman bar; queued |

The **resonance-only Laplacian** is the source of the `body_architecture` surface — its partition is structurally the canonical inner/outer division (the architectural finding). The **hybrid `inv_dv × resonance`** (§13.9) clears the §13.7 0.85 Spearman bar but the partition Matthews φ stays below 0.6, so the hybrid result is queued for v0.18.x or v0.19.0 as a continuous Fiedler-distance → Δv predictor (`bridge.predict_itn_accessibility`) once a regression model lands.

### Tests

- New module `tests/test_body_architecture.py` (34 tests):
  - **Default-roster shape** — 13 bodies, canonical inner-8 / outer-5 partition, partition sizes
  - **Spectral pins** — Pluto + Neptune deepest negative entries (within 0.01 of each other; both below −0.5); Mercury largest positive entry; Fiedler values sorted ascending; λ₂ > 0
  - **Determinism** — repeated calls return byte-identical Fiedler values (LAPACK sign convention nailed)
  - **Error paths** — empty list, duplicates, unknown body name, zero-period body (Sun)
  - **Bridge surface** — full partition, 13 parametrised single-body class lookups, case-insensitive lower-casing, rejection paths (unknown body, non-heliocentric body)
  - **CLI surface** — full partition, `--target`, `--help`
  - **Default-roster contract** — `HELIOCENTRIC_BODIES` is the documented v0.16.0 Tier-1 list
- Parity-smoke spec — `body_architecture` classified as `python_only` (no C twin planned: numpy.linalg.eigh on a 13×13 symmetric matrix is microseconds, well below any threshold where a C twin would be useful).

### Test count

658 pass, 41 skipped (was 622 + 41 in v0.17.0; +36 new).

### Migration

Pure-additive on the Python bridge and the CLI. No existing call sites change. Native callers see `ES_ABI_VERSION = 8` unchanged. `ES_VERSION_STRING` bumps `0.17.0 → 0.18.0`.

## [0.17.0] — 2026-05-06

**Resonance-graph multi-leg `find_itn_chains` (advanced Lagrange-highway search).** Generalises the v0.8.1 closed-form Hohmann-window enumeration to multi-leg pathways via Dijkstra-style graph search over the `(body, epoch)` state space. Pure-Python addition; **no ABI bump** (first ephemerides ship since v0.13.x to leave the C wire-format alone).

### Added — Pythonic API

- `_research.itn_window.ITNChainCandidate` — frozen dataclass carrying `jd_tdb_launch`, `jd_tdb_arrival`, `legs: tuple[ITNCandidate, ...]`, `total_dv_kms`, `total_tof_days`, `resonance_signature: tuple[(int, int), ...]`, `score`.
- `_research.itn_window._best_rational_approx(ratio, max_denom=30) -> (int, int)` — returns the rational approximation of a period ratio in lowest terms; `(0, 0)` sentinel for non-finite or non-positive inputs. Recovers (8, 15) for Earth/Mars, (1, 12) for Earth/Jupiter, (2, 5) for Jupiter/Saturn.
- `_research.itn_window.find_itn_chains(jd_lo, jd_hi, *, departure, target, intermediates=None, max_legs=4, dv_budget_kms=30.0, tof_budget_days=365.25 * 20, threshold=0.05, max_chains=200, max_intermediate_windows=8) -> List[ITNChainCandidate]` — multi-leg ITN chain search via Dijkstra on the `(body, epoch)` state space. Each leg is a closed-form Hohmann window from `find_itn_pathways`. Chains are emitted in monotonically non-decreasing `total_dv_kms` order (Dijkstra invariant); empty if no chain fits the budgets. Default `intermediates=None` ⇒ all heliocentric bodies (planets + dwarf planets + asteroids) minus departure/target; pass `[]` to force a single-leg direct chain.

### Added — bridge dict API (Pyodide-compatible)

- `bridge.find_itn_chains(jd_lo, jd_hi, *, departure, target, intermediates=None, max_legs=4, dv_budget_kms=30.0, tof_budget_days=7305.0, threshold=0.05, max_chains=200, max_intermediate_windows=8) -> dict` — same algorithm, returns `{ok, departure, target, max_legs, n_chains, chains, ...}`. Each chain entry is a JSON-serialisable dict with `jd_tdb_launch`, `jd_tdb_arrival`, `legs` (list of leg dicts mirroring `find_itn_pathways`'s candidate shape), `total_dv_kms`, `total_tof_days`, `resonance_signature` (list of `[p, q]` pairs), `score`.

### Added — CLI

- `find-chains` subcommand — flags: `--from-jd`, `--to-jd`, `--departure`, `--target`, `--intermediates` (comma-separated; empty string = direct), `--max-legs`, `--dv-budget-kms`, `--tof-budget-days`, `--threshold`, `--max-chains`, `--max-intermediate-windows`, `--pretty`. Prints the same dict the bridge returns.

### Algorithm

Dijkstra over the `(current_body, current_jd, total_dv, legs)` state space. Each leg is a closed-form Hohmann transfer window from `find_itn_pathways` (per-pair synodic enumeration; constant time per synodic period). Legs stitch end-to-end at intermediate bodies. Cumulative Δv invariant guarantees first-popped target node is the optimal-Δv chain; subsequent chains emitted in non-decreasing total-Δv order. Worst-case `O(B^L × W)` (B = |intermediates|, L = max_legs, W = windows per leg) but the budgets prune aggressively in practice.

### Resonance signature

Each leg carries a small-integer `(p, q)` gear-ratio resonance signature: the rational approximation of `period_dep / period_tgt` in lowest terms (max denominator 30). The cross-pollination point between the closed-form transfer-window machinery and the BIP cyclic-group encoder.

### Tests

- New module `tests/test_find_itn_chains.py` (21 tests):
  - **Rational-approximation invariants** — Earth/Mars (8, 15), Earth/Jupiter (1, 12), Jupiter/Saturn (2, 5); lowest-terms gcd invariant; non-finite / non-positive sentinel
  - **Direct-chain consistency** — `intermediates=[]` collapses to v0.8.1 `find_itn_pathways` (per-leg jd_tdb byte-identical, modulo Dijkstra-optimal-first vs chronological ordering)
  - **Dijkstra invariant** — chains emitted in monotonically non-decreasing `total_dv_kms` order
  - **Resonance signature shape** — len(`resonance_signature`) == len(`legs`); per-leg `(p, q)` pinned for Earth → Mars
  - **Budget enforcement** — Δv, TOF, max_legs all enforced cumulatively
  - **Bridge surface** — smoke + rejection paths (self-transfer, unknown body, invalid threshold, invalid budget, invalid intermediate)
  - **CLI surface** — direct, multi-leg, `--help`
- Parity-smoke spec — `find_itn_chains` classified as `python_only` (no C twin planned: the priority-queue search is structurally Pythonic and bounded by the same closed-form synodic enumeration as `find_itn_pathways`)

### Test count

622 pass, 41 skipped (was 601 + 41 in v0.16.0; +21 new).

### Migration

Pure-additive on the Python bridge and the CLI. No existing call sites change. Native callers see `ES_ABI_VERSION = 8` unchanged. `ES_VERSION_STRING` bumps `0.16.0 → 0.17.0`.

## [0.16.0] — 2026-05-06

**BODIES Tier-1 expansion (43 → 52): Lagrange trojans + retrograde irregulars + Neptune sub-graph completion.** Themed per the post-v0.15.0 audit (research notebook §11). Adds 9 new bodies + 9 forward + 9 inverse bridge wrappers + 9 CLI subcommands.

### Added — Saturnian Lagrange trojans (4) — first L4/L5 entries in BODIES

| Body | Sol Time | Abbrev | CLI | Host (L4/L5) |
|---|---|---|---|---|
| Telesto | Sol Saturn-Telesto Time | **SSaTeT2** | `time-saturn-telesto` | Tethys L4 |
| Calypso | Sol Saturn-Calypso Time | **SSaCaT** | `time-saturn-calypso` | Tethys L5 |
| Helene | Sol Saturn-Helene Time | **SSaHeT** | `time-saturn-helene` | Dione L4 |
| Polydeuces | Sol Saturn-Polydeuces Time | **SSaPoT** | `time-saturn-polydeuces` | Dione L5 |

Each trojan's sidereal period is **byte-identical** to its host moon's (Tethys: 1.88780216 d; Dione: 2.73691500 d). The body-graph Laplacian acquires a multiplicity-2 eigenvalue at the host's frequency. Natural intersection point with v0.16.x's resonance-graph multi-leg find_itn_chains.

### Added — Jovian irregulars (3)

| Body | Sol Time | Abbrev | CLI | Notes |
|---|---|---|---|---|
| Himalia | Sol Jupiter-Himalia Time | **SJuHiT** | `time-jupiter-himalia` | Largest Jovian irregular (radius ~85 km), prograde, Perrine 1904 |
| Pasiphae | Sol Jupiter-Pasiphae Time | **SJuPaT** | `time-jupiter-pasiphae` | RETROGRADE (i~141°), Melotte 1908 |
| Sinope | Sol Jupiter-Sinope Time | **SJuSiT** | `time-jupiter-sinope` | RETROGRADE (i~153°), Nicholson 1914; near-resonant with Pasiphae |

Pasiphae and Sinope are the second retrograde marker beyond Triton (v0.14.2). Encoder convention: positive period_days; retrograde-ness is metadata.

### Added — Neptune sub-graph completion (2)

| Body | Sol Time | Abbrev | CLI | Notes |
|---|---|---|---|---|
| Proteus | Sol Neptune-Proteus Time | **SNePrT** | `time-neptune-proteus` | Neptune's second-largest moon (~210 km), Voyager 2 1989 |
| Nereid | Sol Neptune-Nereid Time | **SNeNeT** | `time-neptune-nereid` | Most eccentric major-moon orbit in solar system (e=0.749), Kuiper 1949 |

### First invocation of suffix-disambiguation policy

The v0.14.1 6-letter `S<Planet2><Moon2>T` policy reserved a fallback for the case where two moons of the *same parent* share their first-two-letters. v0.16.0 hits exactly that case: **Tethys** (`SSaTeT`, shipped v0.14.1) vs **Telesto** (`SSaTeT2`, shipped v0.16.0). The suffix '2' is the disambiguator. Calypso's moon-prefix (`Ca`) is distinct from Tethys's (`Te`) so no Calypso suffix was needed.

### C-side wire-format change

ABI v7 → v8. `ES_N_BODIES` 43 → 52; native binary rebuilt; parity-smoke ratchet ratcheted. Existing wheels at ABI 7 are not interoperable with v0.16.0 callers; v0.16.0 wheels ship with the rebuilt native.

### Test count

601 pass, 41 skipped (was 514 + 41 in v0.15.0; +23 new — 12 Saturnian-trojan + 9 Jovian-irregular + 2 expanded Neptunian + 18 parity-smoke entries + parity-smoke tier-shape variations).

## [0.15.0] — 2026-05-06

**Sol Moon Times: classical-roster completion** (Pluto-Charon + remaining major Uranian moons). BODIES roster expanded 38 → 43. Closes task `` `#86` `` for the IAU-major moon roster: every classical moon discovered between 1787 and 1948 now has a Sol Time wrapper.

### Added — Uranian classical roster completion (4 moons)

| Body | Sol Time | Abbrev | CLI |
|---|---|---|---|
| Miranda | Sol Uranus-Miranda Time | **SUrMiT** | `time-uranus-miranda` |
| Ariel | Sol Uranus-Ariel Time | **SUrArT** | `time-uranus-ariel` |
| Umbriel | Sol Uranus-Umbriel Time | **SUrUmT** | `time-uranus-umbriel` |
| Oberon | Sol Uranus-Oberon Time | **SUrObT** | `time-uranus-oberon` |

Discovery order: Titania + Oberon (Herschel 1787) → Ariel + Umbriel (Lassell 1851) → Miranda (Kuiper 1948). Voyager 2 (1986) imaged all five. Miranda's Verona Rupes is the tallest known cliff in the solar system (~20 km).

### Added — Plutonian (1 moon)

| Body | Sol Time | Abbrev | CLI |
|---|---|---|---|
| Charon | Sol Pluto-Charon Time | **SPlChT** | `time-pluto-charon` |

Charon (Christy, 1978) is the binary-planet case: mutually tidally locked with Pluto, mass ratio Charon:Pluto ≈ 0.12, barycentre *outside* Pluto. The only 1:1:1 spin-orbit lock in the solar system. Sidereal == synodic == spin period (6.387 d).

### Disambiguation — SUrMiT vs SSaMiT

Second-instance case of the shared-moon-prefix pattern the v0.14.2 SUrTiT/SSaTiT pair first surfaced. Both pairs validate the v0.14.1 6-letter `S<Planet2><Moon2>T` policy — without it both moons would collapse to the same 4-letter form.

### C-side wire-format change

ABI v6 → v7. `ES_N_BODIES` 38 → 43; native binary rebuilt; parity-smoke ratchet ratcheted. Existing wheels at ABI 6 are not interoperable with v0.15.0 callers; v0.15.0 wheels ship with the rebuilt native at the matching ABI.

### Test count

512 pass, 41 skipped (was 497 + 4; +56 new — 5 Plutonian + 4 expanded Uranian + 10 parity-smoke entries + parity-smoke tier-shape variations).

## [0.14.2] — 2026-05-06

**Sol Moon Times: remaining 8 moons across 4 parent families** — closes task `` `#86` `` for the current 38-body roster. Built via four parallel subagent worktrees, integrated into a single ship.

### Added — Mars (2 moons)

| Body | Sol Time name | Abbreviation | CLI |
|---|---|---|---|
| Phobos | Sol Mars-Phobos Time | **SMaPhT** | `time-mars-phobos` |
| Deimos | Sol Mars-Deimos Time | **SMaDeT** | `time-mars-deimos` |

Both likely captured asteroids (C/D-type spectral match). Phobos's sidereal period (0.319 d ≈ 7h 39m) is **shorter** than Mars's solar day (~24h 39m), so from Mars's surface Phobos rises in the **west**. Phobos/Deimos period ratio is ≈ 3.96 — near 4:1 but **not** in 4:1 mean-motion resonance (libration tolerance is parts-per-thousand; 1% off counts as not-locked).

### Added — Jupiter inner regulars (4 moons)

| Body | Sol Time name | Abbreviation | CLI |
|---|---|---|---|
| Metis | Sol Jupiter-Metis Time | **SJuMeT** | `time-jupiter-metis` |
| Adrastea | Sol Jupiter-Adrastea Time | **SJuAdT** | `time-jupiter-adrastea` |
| Amalthea | Sol Jupiter-Amalthea Time | **SJuAmT** | `time-jupiter-amalthea` |
| Thebe | Sol Jupiter-Thebe Time | **SJuThT** | `time-jupiter-thebe` |

Metis + Adrastea are ring-shepherd moons of Jupiter's main ring (both orbit just outside the ring's outer edge). Amalthea is the largest (~84 km radius) and the only one discovered before Voyager (E. E. Barnard, 1892 — the last solar-system moon discovered by direct visual observation). Thebe orbits between Amalthea and Io.

### Added — Uranus (1 moon: Titania)

| Body | Sol Time name | Abbreviation | CLI |
|---|---|---|---|
| Titania | Sol Uranus-Titania Time | **SUrTiT** | `time-uranus-titania` |

Largest Uranian moon (radius ~789 km); discovered by William Herschel 1787. Currently the only Uranian moon in the BODIES roster — Oberon, Umbriel, Ariel, Miranda are queued for a future ship.

**Note**: SUrTiT and SSaTiT (Saturn's Titan) share the `Ti` moon prefix but are globally distinct via the parent prefix (`Ur` vs `Sa`) — exactly the disambiguation the v0.14.1 6-letter abbreviation policy was designed to provide. Without the policy switch, both would have been `STiT` under the old 4-letter form.

### Added — Neptune (1 moon: Triton)

| Body | Sol Time name | Abbreviation | CLI |
|---|---|---|---|
| Triton | Sol Neptune-Triton Time | **SNeTrT** | `time-neptune-triton` |

Largest Neptunian moon (radius ~1353 km — bigger than Pluto). **The only large moon in the solar system that orbits its planet retrograde** — strong evidence Triton is a captured Kuiper Belt object. Tidal deceleration (because of the retrograde orbit) is spiralling Triton inward; in ~3.6 Gyr it will cross Neptune's Roche limit and become a ring system.

**Encoder convention**: `BODIES["triton"].period_days` is positive (we encode `omega = +2π/P` for ALL bodies regardless of prograde/retrograde direction; retrograde-ness is metadata, not a sign flip in the time-scale primitive). Sol Time count proceeds positive-monotonically. Same convention as v0.5.4 Sol Uranian Time (Uranus has retrograde rotation).

### Subagent-driven dispatch

This ship was built via **4 parallel subagent worktrees** (one per family), each:

- branched off main concurrent with v0.14.1 CI
- self-contained: bridge wrappers + CLI subcommand + new test module + parity-smoke entries
- did NOT touch version bumps, CHANGELOGs, README, ROADMAP, notebook (the parent agent integrated those)

Subagents reported clean test runs in their own worktrees. The parent agent integrated the 4 deliverables into a single bridge.py / cli.py / test_parity_smoke.py edit (avoiding 4-way merge conflicts on those shared files), copied the 4 new test modules in directly, and added a generic `_add_moon_subparser` CLI helper that supersedes the v0.14.0/v0.14.1 family-specific helpers for the v0.14.2 additions.

### Sol Moon Times series — current state

23 moons across 6 families (every moon in the BODIES roster except Earth's Luna, which has its own STLT in v0.10.0):

| Family | Count | Examples |
|---|--:|---|
| Galileans (Jupiter) | 4 | Io, Europa, Ganymede, Callisto |
| Saturnians | 11 | Mimas, Enceladus, ..., Titan, ..., Janus, Epimetheus |
| **Martians (v0.14.2)** | **2** | **Phobos, Deimos** |
| **Jovian inner regulars (v0.14.2)** | **4** | **Metis, Adrastea, Amalthea, Thebe** |
| **Uranian (v0.14.2)** | **1** | **Titania** |
| **Neptunian (v0.14.2)** | **1** | **Triton** |
| Total | **23** | |

Plus Sol Terra-Luna Time (STLT) for Earth's Moon = **24 moon time series**. Future BODIES additions (Pluto-Charon, more Uranian moons, etc.) follow the same v0.14.1 6-letter convention.

### Test count

497 pass, 4 skipped (was 399 + 4 in v0.14.1; +98 new — 2 Martian + 4 Jovian-inner + 1 Uranian + 1 Neptunian moon-test modules + parity-smoke entries).

### Migration

None. Pure-additive. No API / encoder / ABI / encoder-test changes.

## [0.14.1] — 2026-05-06

**Sol Moon Times: Saturnians (11 moons) + abbreviation policy switch (4-letter → 6-letter).** Second slice of task `` `#86` ``. The abbreviation collision contingency documented in v0.14.0's ROADMAP fired exactly as predicted: when the 11 Saturnians joined the per-moon abbreviation namespace, two collisions surfaced under the v0.14.0 4-letter `S<Planet><Moon>T` pattern (Tethys + Titan both 'T' → both `SSTT`; Enceladus + Epimetheus both 'E' → both `SSET`). Per the ROADMAP "Naming convention contingencies" policy, the switch applies **uniformly across all Sol Moon Times** — Galileans retroactively renamed too.

### Added — 11 Saturnian Sol Moon Times

| Body | Sol Time name | Abbreviation | CLI |
|---|---|---|---|
| Mimas | Sol Saturn-Mimas Time | **SSaMiT** | `time-saturn-mimas` |
| Enceladus | Sol Saturn-Enceladus Time | **SSaEnT** | `time-saturn-enceladus` |
| Tethys | Sol Saturn-Tethys Time | **SSaTeT** | `time-saturn-tethys` |
| Dione | Sol Saturn-Dione Time | **SSaDiT** | `time-saturn-dione` |
| Rhea | Sol Saturn-Rhea Time | **SSaRhT** | `time-saturn-rhea` |
| Titan | Sol Saturn-Titan Time | **SSaTiT** | `time-saturn-titan` |
| Hyperion | Sol Saturn-Hyperion Time | **SSaHyT** | `time-saturn-hyperion` |
| Iapetus | Sol Saturn-Iapetus Time | **SSaIaT** | `time-saturn-iapetus` |
| Phoebe | Sol Saturn-Phoebe Time | **SSaPhT** | `time-saturn-phoebe` |
| Janus | Sol Saturn-Janus Time | **SSaJaT** | `time-saturn-janus` |
| Epimetheus | Sol Saturn-Epimetheus Time | **SSaEpT** | `time-saturn-epimetheus` |

### Changed — Galilean abbreviations retroactively renamed

| Body | Before (v0.14.0) | After (v0.14.1+) |
|---|---|---|
| Io | `SJIT` | **`SJuIoT`** |
| Europa | `SJET` | **`SJuEuT`** |
| Ganymede | `SJGT` | **`SJuGaT`** |
| Callisto | `SJCT` | **`SJuCaT`** |

The `epoch.abbreviation` field changes; **Python function names, CLI subcommand names, and bridge return-shape are unchanged**. Callers reading the abbreviation as a label (e.g., for display, comparison, or storage) will see the new 6-letter form starting from v0.14.1.

### Why the switch had to be uniform

Mixed conventions across moons (Galileans 4-letter, Saturnians 6-letter) would have been worse than either pure convention — readers would constantly need to remember which family uses which length. The ROADMAP policy was explicit about this: *"When a single collision triggers the policy switch, the change applies uniformly to all Sol Moon Times in the package."*

### Resonance witnesses (in tests, not in dicts)

The Saturnian families have several known mean-motion resonances:

| Resonance | Form | Significance |
|---|---|---|
| Mimas-Tethys 4:2 | `n_Mimas / n_Tethys ≈ 2.0` | Opens the Cassini Division |
| Enceladus-Dione 2:1 | `n_Enc / n_Dione ≈ 2.0` | Powers Enceladus's tidal heating + cryovolcanism |
| Titan-Hyperion 4:3 | `n_Titan / n_Hyp ≈ 1.333` | Drives Hyperion's chaotic rotation |
| Janus-Epimetheus | period ratio ≈ 1.0 | Co-orbital horseshoe orbit (~4-yr swap) |

Each resonance has a witness test in `test_saturnian_sol_moon_times.py`. The per-moon dict carries only `sidereal_count` / `sidereal_phase` — pair-relations stay out of the dict (consistent with the v0.14.0 Galilean Laplace-resonance handling).

### Hyperion footnote

Hyperion's chaotic rotation means rotation period ≠ orbital period (it's the only known major moon NOT in tidal lock). The `sidereal_period_days` field references the orbital period in our convention; the rotation-phase coupling is non-trivially decoupled and an open research direction. This is documented in the bridge docstring, the CLI help text, and the test module.

### Roadmap update

`ROADMAP.md`'s "Naming convention contingencies" section is updated from forward-looking ("if collisions arise") to *triggered* ("v0.14.1 invoked the fallback policy"), with the specific Tethys/Titan and Enceladus/Epimetheus collisions called out as the trigger.

### Test count

399 tests pass, 4 skipped (was 294 + 4 in v0.14.0; +105 new — 99 Saturnian tests + parity-smoke registrations + 6 cross-family abbreviation-uniqueness checks).

### Migration

- **Python function names**: unchanged. `bridge.jd_to_sol_jupiter_io_time(...)` still works the same way.
- **CLI subcommand names**: unchanged. `time-jupiter-io --jd ...` still works the same way.
- **Return-shape**: unchanged. The `epoch.abbreviation` STRING changes from `"SJIT"` to `"SJuIoT"` etc. Callers parsing this field for display / comparison need to update.
- **No API/encoder/ABI changes**.

## [0.14.0] — 2026-05-05

**Sol Moon Times: Galileans (Io / Europa / Ganymede / Callisto).** First slice of task `` `#86` `` — extends the Sol Time hierarchy to non-Luna moons under the moons-stuck-to-parent `Sol <Parent>-<Body> Time` naming convention from v0.9.1.

### Added

- **Generic moon-time primitive** (`_research/time_scales.py`):
  - `MoonTime` dataclass: `body_name`, `parent_name`, `epoch_name`, `epoch_jd_tdb`, `days_since_epoch`, `sidereal_period_days`, `sidereal_count`, `sidereal_phase`.
  - `jd_to_moon_time(body_name, jd_tdb, *, parent_name, sidereal_period_days, ...)`: body-agnostic factory. Caller-supplied parent + sidereal period (looked up at the bridge layer from `BODIES`) keeps this primitive light-weight and free of `BODIES`-table imports — same separation-of-concerns as the rest of `_research/time_scales.py`.
  - `moon_time_to_jd(sidereal_count, *, sidereal_period_days, ...)`: inverse.
  - `SOL_MOON_TIME_J2000_JD_TDB`: shared default epoch (J2000.0).

- **Per-Galilean bridge wrappers** (`bridge.py`):

  | Function | Inverse | Abbrev |
  |---|---|---|
  | `jd_to_sol_jupiter_io_time` | `sol_jupiter_io_time_to_jd` | **SJIT** |
  | `jd_to_sol_jupiter_europa_time` | `sol_jupiter_europa_time_to_jd` | **SJET** |
  | `jd_to_sol_jupiter_ganymede_time` | `sol_jupiter_ganymede_time_to_jd` | **SJGT** |
  | `jd_to_sol_jupiter_callisto_time` | `sol_jupiter_callisto_time_to_jd` | **SJCT** |

  Each returns a dict with `ok`, `jd_tdb`, `body_name`, `parent_name="jupiter"`, `epoch_name="j2000"`, `sidereal_period_days`, `sidereal_count`, `sidereal_phase`, plus an `epoch` block carrying the abbreviation, sol-time-name, parent-body, moon-body, and a per-moon note.

- **Per-Galilean CLI subcommands**: `time-jupiter-io`, `time-jupiter-europa`, `time-jupiter-ganymede`, `time-jupiter-callisto`. Each takes `--jd` or `--sidereal-count` (mutex required), supports `--proper` / `--state` / `--dynamics` augmenting flags via `_add_proper_flags`. The four subparsers share a helper (`_add_galilean_subparser`) so they stay consistent.

- **Test module** (`tests/test_galilean_sol_moon_times.py`): 35 tests covering generic primitive, all four bridge surfaces (J2000-zero, after-one-sidereal-period, inverse round-trip, NaN/Inf rejection), CLI parsing, abbreviation uniqueness, and the Galilean Laplace-resonance witness (canonical form `n_Io − 3·n_Europa + 2·n_Ganymede ≈ 0`; plus the assertion that Callisto is NOT in the resonance).

- **Parity smoke registrations** (`tests/test_parity_smoke.py`): 8 new entries (4 forward + 4 inverse) classified as `python_only` with rationale matching the rest of the Sol Time series.

### Naming convention

Per v0.9.1's moons-stuck-to-parent `Sol <Parent>-<Body> Time`: the production names are *Sol Jupiter-Io Time*, *Sol Jupiter-Europa Time*, *Sol Jupiter-Ganymede Time*, *Sol Jupiter-Callisto Time*. The 4-letter abbreviations follow `S<Planet-initial><Moon-initial>T`. ROADMAP `## Naming convention contingencies` documents the fallback policy if moon-letter collisions arise in future ships (Saturnians, etc.) — switch uniformly to a 6-letter `S<Planet2><Moon2>T` pattern (e.g., `SJuGaT`).

### Why default epoch is J2000

STLT (v0.10.0) used Meton's 432 BCE summer solstice — a Greek-historical anchor that doesn't generalise to non-Luna moons. For Galileans, J2000 is the natural anchor: matches the rest of the Sol Time series, no civilisation has been keeping a Galilean-eclipse archive, and Galileo's own 1610 telescopic discoveries (JD ~2305448) could be a future non-default option but aren't load-bearing for v0.14.0.

### Laplace resonance

The 4:2:1 mean-motion resonance among Io / Europa / Ganymede (canonical form `n_Io − 3·n_Europa + 2·n_Ganymede ≈ 0`) is documented in the test module and in the per-moon docstrings. Callisto is the only Galilean **not** in the resonance — its mean motion is irrationally related to the inner triple. The Sol Time wrappers don't expose resonance metrics in the per-moon dict (the resonance is a pair-relation, not a per-body property); future analysis tooling can compose `sidereal_count` values across the inner triple to recover it.

### Test count

294 tests pass, 4 skipped (was 251 + 4 in v0.13.10 — +43 new: 35 Galilean tests + 8 parity-smoke entries).

### Migration

None. Pure-additive. No API / encoder / ABI / encoder-test surface changes.

## [0.13.10] — 2026-05-05

**Drop `edited` from docs-check workflow trigger types — fixes post-merge double-fire.** CI-only patch; no code / API / encoder / ABI / test changes.

### Why

User flagged on PR `` `#214` `` (v0.13.9 ship): the docs-check workflow was double-firing at merge time. Two `pull_request` events at the same second on the PR's branch ~3 seconds before the merge committed; concurrency-cancel caught it (one CANCELLED, one SUCCESS) but the wasted CI churn + confusing run-history was observable.

### Root cause

GitHub web UI's "Squash and merge" workflow fires `pull_request: edited` (the merge-commit dialog populates / saves the title + body fields) near-simultaneously with `pull_request: synchronize` (GitHub recomputes the `refs/pull/N/merge` preview ref). With both `edited` and `synchronize` in our `types` list, both events triggered runs at the same second → deterministic double-fire at every merge.

### Fix

Drop `edited` from the trigger types in `.github/workflows/ephemerides-spectral-docs-check.yml`:

```yaml
# Before (v0.13.3 → v0.13.9):
types: [opened, synchronize, reopened, edited, labeled]

# After (v0.13.10+):
types: [opened, synchronize, reopened, labeled]
```

Eliminates the source of the double-fire. The CI-side workflow (`ephemerides-spectral-ci.yml`) was already on `[opened, synchronize, reopened, labeled]` and didn't have this issue.

### Trade-off

`[skip-docs-check]` opt-out added retroactively (after PR open, by editing the PR body) no longer triggers a re-run. User must either:
1. Push a synchronizing commit (the natural way), or
2. Accept the stale advisory comment

Acceptable — opt-out should be set up-front in the initial PR description, not retroactively.

### Migration

None. Workflow-only change; CI behaviour now matches the `ephemerides-spectral-ci` workflow's narrower trigger types. 251 tests pass, 4 skipped (unchanged).

## [0.13.9] — 2026-05-05

**JPL Power-of-Ten Rules 6 + 7 manual audits — final patch in the v0.13.4-v0.13.9 rule-fix sequence.** Audit-only release; no code changes; **0 violations found** for both rules.

### Result

**All ten JPL Power-of-Ten rules now satisfied.** The five-ship sequence v0.13.4 → v0.13.5 → v0.13.6 → v0.13.7 → v0.13.9 (with v0.13.8 a docs-hygiene patch in the middle) closes out the v0.11.2 audit baseline:

| Rule | Description | Cleared in | Mechanism |
|---|---|---|---|
| 1 | No `goto` / `setjmp` / `longjmp` / recursion | v0.13.4 | `test_jpl_audit.py` pin |
| 2 | Fixed loop bounds | already-passing at v0.11.2 | `test_jpl_audit.py` pin |
| 3 | No dynamic allocation after init | v0.13.4 | `test_jpl_audit.py` pin |
| 4 | Functions ≤ 60 lines | v0.13.5 | `test_jpl_audit.py` pin |
| 5 | ≥ 2 assertions per function (avg) | v0.13.6 | `test_jpl_audit.py` pin + density test |
| 6 | Smallest possible scope for data | **v0.13.9** | manual audit (this ship) |
| 7 | Check return values, validate parameters | **v0.13.9** | manual audit (this ship) |
| 8 | Limited preprocessor | already-passing at v0.11.2 | `test_jpl_audit.py` pin |
| 9 | Pointer dereference depth ≤ 1; no function pointers | already-passing at v0.11.2 | `test_jpl_audit.py` pin |
| 10 | Compile clean at most-pedantic warning level | v0.13.7 | `pedantic-build` 3-cell CI matrix |

### Rule 6 audit findings

The v0.11.2 spot-check estimate of *"likely 5-10 violations across `es_encode.c` + `es_parity.c`"* did not survive the cleanup work in v0.13.4-v0.13.6. The illustrative snippet in the audit doc was illustrative, not actual code. Real codebase shape:

- **All loop iterators**: `for (size_t i = ...; ...)` block-scoped.
- **All `const` declarations**: at minimal scope near use (the v0.13.6 assertion work added `const double rad = ...; assert(rad >= 0.0)` patterns throughout).
- **Function-scope declarations that remain are intentional**:
  - **Accumulators** (`acc`, `acc_r`, `acc_i`) — must outlive each loop iteration.
  - **Sqrt caches** (`sqrt_D`, `inv_sqrt_D`) — computed once at function entry to avoid recomputation in the inner loop.
  - **Output buffers** (`curr_phases[]`, `trunk_step[]`) — used both before and after the chunk loop.
  - **Result variables** (`rounded` in `es_banker_round`) — set in three branches, returned at function exit.

All within Rule 6 spirit.

### Rule 7 audit findings

The v0.11.2 estimate of *"5-15 sites where `rc` is assigned but not checked"* did not survive scrutiny. Every `es_status_t` return is checked via the uniform pattern:

```c
es_status_t rc = some_call(...);
if (rc != ES_OK) return rc;
```

Audit walked every `es_status_t` assignment in the codebase (8 sites across `es_parity.c`, `es_hd_state.c`, `es_patches.c`); each was checked on the next line. Numeric returns used directly in expressions (no assigned-but-not-used sites). Bridge entry points validate every parameter via runtime checks; internal helpers take pre-validated inputs documented via post-validation `assert()` (Rule 5 work in v0.13.6).

### Migration

None. Audit-only release; no source code changes; no API/ABI/encoder/test surface change. 251 tests pass, 4 skipped (unchanged).

## [0.13.8] — 2026-05-05

**README accuracy patch — two-stage architecture clarification.** Docs-only release; no API / encoder / ABI / test changes.

### Why

User flagged a misunderstanding triggered by the previous README framing: *"our readme says that we use complex128 for syzygy and stuff, is that still correct? because that would mean we aren't pure ALU, right?"*

The README listed three backends (`bip` / `c` / `complex128`) as parallel alternatives, with `complex128` annotated as *"Used for the algebraic identities (Syzygy operator, observer binding) and as a regression baseline."* That bullet was true *before* v0.7.0, when Tier 2b shipped C-side `complex64` implementations of the HD operations. Since then the production HD path is C-side `complex64`; `complex128` is the regression baseline only (`backend="fpu-ref"`).

The framing also implied "three interchangeable backends" all ran the same operation. They don't — they are three encoders for the **phase-residue stage**, plus an FPU HD pipeline that follows. The mental model was off, and the README was the load-bearing source.

### Fixed

- **Two-stage architecture, explicitly described**: phase-residue computation (integer ALU) + HD operations (FPU `complex64` production / `complex128` regression). Phase residues are integer ALU end-to-end; HD operations can't be (channel bases are unit-magnitude complex; `(cos(φ), sin(φ))` requires trigonometric channels).
- **`complex128` reframed**: from "production path for syzygy / observer-bind" to "regression baseline; `backend='fpu-ref'`."
- **"Both backends" → "All three phase-residue encoders"** typo fix (the earlier sentence had been written before `complex128` was added to the list).
- **Status banner updated**: from "Three interchangeable backends (BIP integer ALU, native C, FPU complex128)" to a more accurate "Two-stage architecture: three interchangeable integer-ALU phase-residue encoders feeding an FPU `complex64` HD pipeline."
- **TL;DR callout added** under the new architecture section: *"Phase residues are integer ALU end-to-end (BIP encoder hot path is uint64/int64/uint32, no floats); HD operations (syzygy / observer-bind / eclipse) lift those residues to `complex64` and run on FPU. The package is *not* pure-ALU end-to-end — the HD pipeline can't be."*

### Roadmap renumber

JPL_AUDIT.md: Rules 6+7 manual audits move v0.13.8 → v0.13.9 (last item in the rule-fix sequence; v0.13.8 reserved for this README hygiene patch).

### Migration

None. Pure docs change; no API / encoder / ABI / test surface change. 251 tests pass, 4 skipped.

## [0.13.7] — 2026-05-05

**JPL Power-of-Ten Rule 10 fixes — cross-platform pedantic-build CI matrix.** Fourth code-quality patch in the v0.13.4-v0.13.8 rule-fix sequence. CI-only addition; no public API / ABI / encoder change.

### Added

- **`ES_PEDANTIC` CMake option** (default OFF) elevates the existing pedantic warning flags to errors:

  | Toolchain | Existing flags | With `ES_PEDANTIC=ON` |
  |---|---|---|
  | gcc / clang | `-Wall -Wextra -Wpedantic` | + `-Werror` |
  | MSVC | `/W4` | + `/WX` |

  The casual local build stays friendly (warnings emitted but not fatal); CI turns it on so any new warning fails the build.

- **`pedantic-build` job** in `.github/workflows/ephemerides-spectral-ci.yml` runs a 3-cell matrix:

  | Cell | Toolchain |
  |---|---|
  | `ubuntu-latest` | gcc |
  | `macos-14` | clang |
  | `windows-latest` | MSVC |

  Each cell runs `cmake -DES_PEDANTIC=ON` then `cmake --build`, so any new warning fails CI on every PR.

  **Always-on** (not gated by the `wheel-check` label) — Rule 10 is a permanent invariant, not a per-PR opt-in. Cost ~30s per cell. Cheap protection against signed/unsigned mismatches, unused-variable regressions, missing-prototype drift, etc.

### Why ES_PEDANTIC is opt-in by default

Casual local builds (e.g. `cmake --build` during development for a quick parity check) shouldn't fail on a newly-introduced unused-variable warning the developer is about to fix. `ES_PEDANTIC=OFF` keeps warnings as warnings during development; CI enforces the zero-warnings invariant before merge.

### Holzmann's Rule 10

> *"All code must be compiled, from the first day of development, with all compiler warnings enabled at the compiler's most pedantic setting. All code must compile with these settings without any warnings."*

The 3-cell matrix is the cross-platform implementation: gcc on Linux, clang on macOS, MSVC on Windows. All three see the same source tree; each emits its own warnings (gcc and MSVC notably differ on which patterns warn). The matrix-CI satisfies "without any warnings" across every platform we ship to.

### Audit ratchet

Rule 10 is enforced by CI rather than by `tests/test_jpl_audit.py` (which counts source-side patterns; warnings are toolchain-side and toolchain-version-dependent). The `pedantic-build` job is the ratchet — drop the pin, drop the warning.

**All five mechanically-enforceable JPL rules now satisfied:**

| Rule | Status | Mechanism |
|---|---|---|
| 1 (no `goto`) | ✅ | Pinned in `test_jpl_audit.py` |
| 3 (no dynamic alloc) | ✅ | Pinned in `test_jpl_audit.py` |
| 4 (≤60-line functions) | ✅ | Pinned in `test_jpl_audit.py` |
| 5 (≥2 assertions/function) | ✅ | Pinned in `test_jpl_audit.py` |
| 10 (zero warnings at pedantic) | ✅ | Enforced by `pedantic-build` CI job |

Remaining JPL roadmap: Rules 6+7 (manual scope + return-value audits, v0.13.8).

### Migration

None. CI-only addition. Local builds default to the previous behaviour (warnings as warnings); developers wanting Rule 10 enforcement locally can pass `-DES_PEDANTIC=ON` to cmake.

251 tests pass, 4 skipped (unchanged from v0.13.6).

## [0.13.6] — 2026-05-05

**JPL Power-of-Ten Rule 5 fixes — assertion density at 2/function average.** Third code-quality patch in the v0.13.4-v0.13.8 rule-fix sequence. Pure additive instrumentation: no public API change, no ABI change (still v6), encoder math byte-identical — parity smoke pins both backends to within float-ULP and stays green.

### Fixed

- **Rule 5 (≥2 assertions per function avg)** density flips from 0.0 (audit baseline) to **2.10**. **88 assertions** added across the 42 functions (target ≥2 × 42 = 84). The previously-skipped `test_rule_5_density_meets_2_per_function` ratchet test now **PASSES**.

  Per-file distribution:

  | File | Assertions / Functions | Density |
  |---|--:|--:|
  | `es_channel_bases.c` | 2 / 1 | 2.00 |
  | `es_encode.c` | 26 / 13 | 2.00 |
  | `es_hd_state.c` | 25 / 11 | 2.27 |
  | `es_parity.c` | 16 / 8 | 2.00 |
  | `es_patches.c` | 15 / 7 | 2.14 |
  | `es_prng.c` | 4 / 2 | 2.00 |
  | **Total** | **88 / 42** | **2.10** |

### Coverage strategy

Per Holzmann's original Power-of-Ten paper, assertions document anomalous-condition checks. Three categories applied:

- **Pre-conditions on parameters**: assert pointer non-NULL after runtime `if (ptr == NULL) return ERR;` check (documents post-validation invariant); assert index < N_BODIES; assert input finite.
- **Post-conditions on results**: assert output non-negative for magnitudes/norms; assert output bounded (e.g. `phi < 2π`); assert state advanced exactly once.
- **Invariants**: assert `D > 0`; assert `n_patches ≤ ES_MAX_PATCHES`; assert constants positive.

### Zero runtime cost

All assertions use the standard `<assert.h>` macro, which is a no-op when `NDEBUG` is defined. Production builds (`-DNDEBUG`) strip them entirely. Assertions are a *development-time* documentation tool that doubles as static-analysis-friendly precondition spec — not a runtime check.

### Audit ratchet

`tests/test_jpl_audit.py` pins ratcheted:

| Pin | v0.11.2 baseline | v0.13.5 | v0.13.6 |
|---|--:|--:|--:|
| `PIN_RULE_5_ASSERTIONS` | 0 | 0 | **88** *(ratcheted UP — count must only increase)* |

`test_rule_5_density_meets_2_per_function` flips from SKIP to **PASS**. Total mechanically-detectable violations: **102 → 0** — every Rule 1-5 violation in the v0.11.2 audit baseline now cleared in three ships. Remaining JPL roadmap: Rule 10 (pedantic-build matrix, v0.13.7), Rules 6+7 (manual scope + return-value audits, v0.13.8).

### Migration

None. Pure instrumentation; no API/ABI/test surface change; runtime behaviour unchanged in release builds. 250 tests pass, 4 skipped (was 5; Rule 5 density skip is gone).

## [0.13.5] — 2026-05-05

**JPL Power-of-Ten Rule 4 fixes — long-function splits.** Second code-quality patch in the v0.13.4-v0.13.8 rule-fix sequence. Pure refactor: no public API change, no ABI change (still v6), encoder math byte-identical (parity smoke is the gate).

### Fixed

- **Rule 4 (function bodies ≤ 60 lines)** count drops **4 → 0**. The four offenders identified in the v0.11.2 audit are factored into JPL-compliant sub-functions along natural algorithm seams:

  | File | Function | Before | After (driver) | New static helpers |
  |---|---|--:|--:|---|
  | `es_encode.c` | `es_encode_state` | 109 | ≤60 | `apply_one_chunk` (chunk-loop body), `apply_subchunk_remainder` (banker's-round leftover step) |
  | `es_parity.c` | `es_find_syzygies` | 99 | ≤60 | `select_syzygy_targets` (kind-filter table), `score_syzygy_event` (per-event geometry), `validate_syzygy_args` (input checks), `emit_syzygy_event` (count + cap handling) |
  | `es_hd_state.c` | `es_bind_observer` | 78 | ≤60 | `observer_coord_shift` (lat/lon → roll index), `apply_observer_bind` (complex-mul inner loop) |
  | `es_hd_state.c` | `es_get_eclipse_probability` | 65 | ≤60 | `build_syzygy_operator` (sun+moon+node sum), `complex64_vdot_magnitude` (numpy-`vdot` magnitude) |

  10 new static internal helpers; total function count 32 → 42 (`PIN_RULE_5_TOTAL_FUNCS` ratcheted UP — Rule 5 work in v0.13.6 needs the larger inventory).

### Why static helpers (not public API)

The new factors are private to their .c files — they're internal seams, not new ABI surface. No header changes, no Python-side updates, no parity tests to update. The Python ctypes shim doesn't even know they exist. Public entry points (`es_encode_state`, `es_find_syzygies`, `es_bind_observer`, `es_get_eclipse_probability`) keep their v0.13.4 signatures.

### Audit ratchet

`tests/test_jpl_audit.py` pins ratcheted:

| Pin | v0.11.2 baseline | v0.13.4 | v0.13.5 |
|---|--:|--:|--:|
| `PIN_RULE_4_LONG_FUNCTIONS` | 4 | 4 | **0** |
| `PIN_RULE_5_TOTAL_FUNCS` | 32 | 32 | **42** *(ratcheted UP — Rule 5 needs the new inventory)* |

Total mechanically-detectable violations: **102 → 64** (37% of audit baseline cleared across v0.13.4 + v0.13.5). Remaining: Rule 5 (assertion density, v0.13.6), Rule 10 (pedantic-build matrix, v0.13.7), Rules 6+7 (manual audits, v0.13.8).

### Migration

None. Pure internal refactor; no API/ABI/test surface change. 250 tests pass, 5 skipped.

## [0.13.4] — 2026-05-05

**JPL Power-of-Ten Rule 1 + Rule 3 fixes** — first code-quality patch in the v0.13.4-v0.13.8 rule-fix sequence. Caller-supplied-scratch refactor of the HD pipeline removes both classes of violation in one pass. ABI v5 → v6 (mechanical wire-format change; encoder math byte-identical).

### Fixed

- **Rule 1 (no `goto`)** — 5 occurrences → **0**. The five `goto out` statements in `es_hd_state.c`'s cleanup-on-error pattern (`es_encode_state_hd`, `es_bind_observer`, `es_get_eclipse_probability`) are gone. With the buffers no longer owned by the C function, there's nothing to free on error paths — they collapse to plain early-return.

- **Rule 3 (no dynamic allocation after init)** — 29 occurrences → **0**. The C library no longer calls `malloc`/`calloc`/`realloc`/`free` anywhere after init. `es_hd_state.c` no longer includes `<stdlib.h>`. The HD pipeline's three entry points take caller-supplied scratch buffers as additional pointer parameters; the Python ctypes shim allocates the scratch alongside the existing `out_state` buffer (no observable change in heap pressure — Python was already heap-allocating the output buffer).

### Changed (ABI break — v5 → v6)

Three public C entry points gained scratch-buffer parameters:

| Function | New parameters |
|---|---|
| `es_encode_state_hd` | `+scratch_basis`, `+scratch_rolled` |
| `es_bind_observer` | `+scratch_body_basis`, `+scratch_coord_basis`, `+scratch_coord_op` |
| `es_get_eclipse_probability` | `+scratch_sun_b`, `+scratch_moon_b`, `+scratch_node_b`, `+scratch_s_op` |

Each scratch buffer must have capacity for D `es_complex64_t` entries; contents on entry are ignored, on return are unspecified.

`ES_ABI_VERSION` 5 → 6. The ctypes shim refuses to load any binary with a mismatched ABI, so a stale `_native/ephemerides_spectral.dll` from v0.13.3 will fail loudly at import time rather than silently corrupt memory. Standard `pip install --force-reinstall ephemerides-spectral` (or `cmake --build` for source-tree dev) refreshes the binary.

### User-facing impact

**None.** The Python bridge API (`bridge.py`'s `get_local_view`, `get_eclipse_probability`, `default_encode(..., backend="c")`) is unchanged — the scratch allocation lives in the ctypes shim (`_native_bip.py`'s `native_*` helpers), one layer below the bridge surface. Same call sites, same return shapes, same numpy dtypes, byte-identical math.

### Audit ratchet

`tests/test_jpl_audit.py` pins ratcheted DOWN:

| Pin | v0.11.2 baseline | v0.13.4 |
|---|--:|--:|
| `PIN_RULE_1_GOTO` | 5 | **0** |
| `PIN_RULE_3_DYNAMIC_ALLOC` | 29 | **0** |

Total mechanically-detectable violations: **102 → 68** (-34, 33% of the audit baseline cleared in one ship). Remaining: Rule 4 (4 long functions, queued v0.13.5) + Rule 5 (64 assertions short, queued v0.13.6).

### Migration

- **Pure-Python users (no C extension)**: zero change. Pyodide / WASM / sdist-without-toolchain installs are unaffected.
- **Direct C-API consumers (rare)**: rebuild against v0.13.4 headers; pass scratch pointers per the new signatures. See `c/include/ephemerides_spectral.h` ABI-history comment for the exact field list.
- **Standard PyPI users**: `pip install -U ephemerides-spectral` refreshes the wheel; the bundled native binary matches the bundled Python.

250 tests pass, 5 skipped (unchanged).

## [0.13.3] — 2026-05-05

**Pre-merge docs+parity hygiene check** — soft-warning GitHub Actions workflow that flags PRs whose code-side changes don't move the docs surface in lockstep. Closes `` `#98` `` (consolidated; absorbs `` `#87` `` + `` `#88` ``).

### Added

- **`` `#98` ``** — `.github/workflows/ephemerides-spectral-docs-check.yml` posts (or updates in place) a single PR comment summarising drift between code-side touches and the five documentation files we treat as the PyPI-facing SSOT surface:

  | Watched doc | Role |
  |---|---|
  | `python/README.md` | PyPI README (status banner + body table) |
  | `python/CHANGELOG.md` | Package CHANGELOG (PyPI-rendered) |
  | `CHANGELOG.md` | Project CHANGELOG (mirror) |
  | `ROADMAP.md` | Roadmap / status sweep |
  | `ephemerides_spectral_research_notebook.md` | Research notebook |

  Categories cross-checked against expected docs:

  | Code-side category | Expected docs |
  |---|---|
  | Version bump (`pyproject.toml` / `pyproject-pure.toml` / `version.py` / `c/include/ephemerides_spectral.h`) | All five |
  | `bridge.py` (Python bridge surface) | README + both CHANGELOGs + notebook |
  | `cli.py` (CLI surface) | README + both CHANGELOGs |
  | `_research/*.py` or `research/*.py` (codegen source / mirror) | Notebook + both CHANGELOGs |
  | `c/src/*.c` or `c/include/*.h` (C library) | Both CHANGELOGs + parity-test touch |

  **Soft-warning, not hard-fail.** The freshness ratchet inside pytest already hard-fails on the highest-value drift modes (`test_native_version_string_matches`, `test_parity_smoke::PARITY_TARGETS`, `test_readme_freshness`, `test_jpl_audit`); this workflow surfaces the *next tier* — prose-and-narrative drift that humans should review but a regex can't authoritatively adjudicate. Forcing CHANGELOG bumps on every whitespace diff would burn patience and breed filler bullets.

  **Opt-out**: include `[skip-docs-check]` anywhere in the PR body to silence on cosmetic / typo / formatting-only diffs.

  **Comment idempotence**: uses `peter-evans/find-comment` + `peter-evans/create-or-update-comment` so the same advisory is updated in place across pushes rather than spamming the PR.

  **Concurrency**: matches `ephemerides-spectral-ci.yml`'s `cancel-in-progress: true` group keyed by workflow + ref so the `opened`+`labeled` double-fire pattern documented in that workflow's header doesn't double up here either.

### Migration

None. CI-only addition; no source / API / ABI / encoder / test changes. The four version-stamp files (`version.py`, `pyproject.toml`, `pyproject-pure.toml`, `c/include/ephemerides_spectral.h`) bump from 0.13.2 → 0.13.3 in lockstep as usual.

## [0.13.2] — 2026-05-05

**Quick-win patches**: gitignore the rebuild-every-build `_native/` directory + renumber the JPL rule-fix roadmap.

### Fixed

- **`` `#85` ``** — Added `docs/antikythera-maths/ephemerides-spectral/python/ephemerides_spectral/_native/` to the repo `.gitignore`. The `_native/` directory holds the compiled native C library (`ephemerides_spectral.dll` / `.so` / `.dylib`) that rebuilds on every `cmake --build ../build` followed by `cp ../build/ephemerides_spectral.dll ephemerides_spectral/_native/`. Per-platform; not portable; not shipped in source. Eliminates the friction of `git status` always showing `?? ephemerides_spectral/_native/` and the per-PR ceremony of adding files individually to avoid accidentally committing the binary.

- **`c/JPL_AUDIT.md` roadmap renumbering**. The original v0.11.3-v0.11.7 numbering queued at the v0.11.2 audit ship is obsolete since the project moved past v0.11.x. Rule-fix patches are renumbered:

  | Was | Now | Focus |
  |---|---|---|
  | v0.11.3 | **v0.13.4** | Rule 1 + Rule 3 fixes |
  | v0.11.4 | **v0.13.5** | Rule 4 fixes |
  | v0.11.5 | **v0.13.6** | Rule 5 fixes |
  | v0.11.6 | **v0.13.7** | Rule 10 audit |
  | v0.11.7 | **v0.13.8** | Rules 6 + 7 audits |

  v0.13.3 is reserved for `` `#98` `` (consolidated docs+parity hygiene check; absorbs `` `#87` `` + `` `#88` ``).

### Migration

None. Patch-level docs + repo-config changes only; no API, no encoder, no ABI, no test changes.

## [0.13.1] — 2026-05-05

**SPICE feature-gap audit + STLT-naming hygiene.** Docs-only release.

### SPICE feature-gap audit (#101)

User question (during v0.11.2 ship close): *"What do we do now that SPICE does slower? Does SPICE do things we might be able to do but don't? If so, will it be worth some API compatible bridge?"*

Answer in `figures/spice_feature_audit.md`: three-column comparison of what we do faster, what we do that SPICE doesn't, and what SPICE does that we don't. **Recommendation: skip the SPICE-API compat bridge.** Document the gap (this audit). Re-evaluate when the four high-value gaps land (light-time + stellar aberration; frame transformations; full Kepler elements; per-body pole orientation) — probably still skip, since at that point our surface stands on its own.

Spawned v0.14.x backlog from the audit:
- Light-time + stellar-aberration corrections (high value, moderate cost).
- Canonical frame-transform primitive (medium value, medium cost).
- Full Kepler elements on `KinematicState` (eccentricity, inclination, etc. — high value).
- Per-body pole orientation (PCK-equivalent; small ship).

### STLT naming hygiene

User flagged that the abbreviation table listed Luna's primary Sol Time as **SLT (Sol Luna Time, surface clock)**, but per the moons-stuck-to-parent `Sol <Parent>-<Body> Time` convention from v0.9.1 it should be **STLT (Sol Terra-Luna Time)**. Fixed:

- README abbreviation table: Luna row promoted from `SLT / time-luna` to `STLT / time-terra-luna`. Followed by an explanatory paragraph about the moons-stuck-to-parent convention; SLT is preserved as a secondary alternative for the surface-clock case.
- Active code comments + docstrings (bridge.py / cli.py / time_scales.py / lunar_epoch_candidates.py / test_parity_smoke.py): drop "system clock for the Terra-Luna pair" framing in favour of "anchored Lunar time using the synodic month."
- Notebook §7.4 living description rewritten with the moons-stuck-to-parent framing.
- v0.10.0 CHANGELOG entries preserved as historical artefacts (they describe how STLT was *framed at the time*, not how shipped behaviour was; the shipped API is unchanged).

### Migration

None. Documentation-only release; no API, no encoder, no CLI behaviour change. The STLT name and CLI subcommand (`time-terra-luna`) and bridge methods (`get_sol_terra_luna_time`) are unchanged.

## [0.13.0] — 2026-05-05

**Sol Dynamics — system energy, gravitational forces, per-body energy budgets — augmented onto every `time-*` subcommand via `--dynamics`.**

Counterpart to v0.12.0's Sol Kinematics; mirrors chess-spectral's `qm_*_dynamics.py` *dynamics* layer (Hamiltonian + force / energy queries). The Phase A audit data already covered both halves (`figures/kinematics_dynamics_audit.md`); v0.13.0 ships the second canonical primitive (`_research/dynamics.py`) + bridge + CLI.

### Validated against textbook values

- **Earth-Sun gravitational force = 3.542×10²² N** at 1.000 AU, vs. textbook 3.54×10²² N (0.01 % rel err) — the most-cited validation value in classical mechanics.
- **Total system energy = −1.98×10³⁵ J** (negative ⇒ gravitationally bound) ✓.
- **Virial theorem holds**: total E = PE / 2 to within 0.5 % (circular-orbit constraint).
- **Sun's KE / Mc² = 8.6×10⁻¹⁶**, well below the 1×10⁻¹² noise floor for "Sun barely moves in barycentric frame."
- **Newton's 3rd law**: F_ab = F_ba symmetric to floating-point precision.
- **Inverse-square law**: F = G M m / r² verified explicitly.

### Added

**Bridge:**
- `bridge.get_dynamics(*, jd_tdb=None, frame=...)` — system aggregate (KE, PE, total E, is_bound, L partitions).
- `bridge.get_force_between(body_a, body_b, ...)` — Newtonian pair force.
- `bridge.get_body_energies(body, ...)` — per-body KE + PE + total energy budget.
- `bridge.apply_dynamics_correction(result, subcommand, ...)` — CLI `--dynamics` post-processor.
- `_research/dynamics.py`: `BodyEnergies`, `ForceContribution`, `DynamicsState` dataclasses + Phase B canonical primitives.

**CLI:**
- New `dynamics` subcommand with three query modes:
  - `dynamics` — system aggregate (default)
  - `dynamics --body <X>` — per-body energy budget
  - `dynamics --body <X> --from <Y>` — gravitational force on X from Y
- `--dynamics` flag added uniformly to every `time-*` subcommand.

**Examples:**
```bash
# System totals
ephemerides-spectral dynamics

# Mars's energy budget
ephemerides-spectral dynamics --body mars

# Force on Mars from Jupiter (validates the textbook formula)
ephemerides-spectral dynamics --body mars --from jupiter

# Earth-Sun reference (3.54e22 N at 1 AU)
ephemerides-spectral dynamics --body terra --from sun

# All three augmenting flags compose
ephemerides-spectral time-mars --jd 2451545.0 --state --proper --dynamics
```

### Discipline

- 34 new tests in `tests/test_dynamics.py` pin the validation set + every primitive + the CLI surfaces.
- Four new bridge methods classified `python_only` in `PARITY_TARGETS`.
- `dynamics.py` registered in `codegen/emit_research_modules.py::_INCLUDED_MODULES`.

### Out of scope (deferred)

- **3D force vectors.** v0.13.0 reports magnitudes only; needs the position-vector decoder (queued for v0.13.x).
- **Tidal forces.** Body-extended-by-radius differential pull. v0.13.x with the per-body internal-Laplacian work (#103).
- **Lyapunov / chaos indicator.** Needs full state evolution + variation propagation; v0.13.x.
- **`evolve(state, dt)` named primitive.** The existing `bip_instrument.encode_state(jd_tdb)` IS the evolution; v0.13.0 doesn't wrap it as a separate function.
- **C twin.** Parity smoke marks new methods `python_only`.

### Migration

None. Sol Dynamics is purely additive.

## [0.12.0] — 2026-05-05

**Sol Kinematics — per-body orbital state, transparently augmented onto every `time-*` subcommand via `--state`.**

### The framing

Mirror of chess-spectral's `qm_2d.py` / `qm_4d.py` *kinematics* layer (static observables, no time-evolution). The user pointed at the chess-spectral pattern: *"we can check our chess spectral where we have done this."* Translates 1:1 to ephemerides-spectral as v0.12.0 (Kinematics) + v0.13.0 (Dynamics, coming).

`--state` is opt-in (default off, no behavior change for v0.11.x callers); when set, augments any `time-*` bridge result with a `kinematic_state` block carrying orbital velocity, semi-major axis, kinetic energy, and angular momentum for the subcommand's canonical body.

### Validated against published values

Same 9 pins the Phase A audit script (`research/kinematics_dynamics_audit.py`) verifies — agreeing with `_research/kinematics.py` to within 0.02-2.5 %:

| Check | Computed | Expected | Source |
|---|---|---|---|
| Mercury orbital v | 47.87 km/s | 47.36 | NASA fact sheet |
| Earth orbital v | 29.785 km/s | 29.78 | Standard |
| Mars orbital v | 24.13 km/s | 24.07 | NASA fact sheet |
| Jupiter orbital v | 13.06 km/s | 13.07 | NASA fact sheet |
| Pluto orbital v | 4.741 km/s | 4.74 | NASA fact sheet |
| **Jupiter fraction of total L** | **61.5 %** | ~61 % | Standard tables |
| **Outer planets fraction of planet L** | **99.84 %** | ~99 % | Standard tables |

### Added

- `bridge.get_kinematic_state(body, *, jd_tdb=None, frame=...)` → per-body orbital state.
- `bridge.get_full_system_state(...)` → all 38 bodies + system totals.
- `bridge.apply_state_correction(result, subcommand, ...)` — CLI `--state` post-processor.
- `_research/kinematics.py` — `KinematicState` dataclass + Phase B canonical primitive.
- CLI `--state`/`--frame` flags added to every `time-*` subcommand.
- CLI `kinematics --body <X>` / `kinematics --all` standalone subcommand.

### Out of scope (deferred to v0.12.x or v0.13.0)

- Eccentricity / inclination corrections (v0.12.x).
- Position vectors at a specific JD — phase decoder (v0.12.1).
- Acceleration / forces / energies / evolution — v0.13.0 *Dynamics* counterpart.
- C twin (parity smoke marks new methods `python_only`).

### Migration

None. Sol Kinematics is purely additive.

## [0.11.2] — 2026-05-05

**JPL Power-of-Ten audit baseline for the C library.** Audit-only release — no code changes; documents violations and pins counts in CI as a one-way ratchet.

### Why this exists

User suggestion captured during v0.9.3: *"work we should do, maybe its own version path, impose JPL C standard on ourselves."* The C library is targeted at embedded deployment (ESP32, Cortex-M) per the README's "Microcontroller Compatibility" section; JPL Power-of-Ten is the embedded-C gold standard for safety-critical code (Holzmann 2006). The library is small enough (~2.1k LOC across 11 files) that retrofitting is tractable.

### Audit results

102 mechanically-detectable violations across the codebase:

| Rule | Description | Violations |
|---|---|--:|
| 1 | No goto / setjmp / longjmp / recursion | **5** (all goto in `es_hd_state.c` cleanup pattern) |
| 2 | Fixed loop bounds | 0 ✅ |
| 3 | No dynamic allocation after init | **29** (all in `es_hd_state.c` HD pipeline) |
| 4 | Functions ≤ 60 lines | **4** (`es_encode_state` 109; `es_find_syzygies` 99; `es_bind_observer` 86; `es_get_eclipse_probability` 71) |
| 5 | ≥ 2 assertions per function (avg) | **64-assertion shortfall** (0 across 32 functions) |
| 8 | Limited preprocessor | 0 ✅ |
| 9 | No function pointers | 0 ✅ |

Rules 6, 7, 10 are not mechanically detectable; manual audit deferred to v0.11.3+.

### Added

- **`c/JPL_AUDIT.md`** — full human-readable audit document. Rule-by-rule violation breakdown with line numbers, fix paths, and the v0.11.3+ ship roadmap.
- **`tests/test_jpl_audit.py`** — pytest ratchet pinning all mechanically-detectable counts. 11 passing checks + 1 expected-skip (Rule 5 density gate). Same drift-detection pattern as `test_native_version_string_matches_package_version` and `test_readme_freshness.py`.

### Discipline

- Adding a new violation requires updating the pin upward AND explicit justification in the PR description.
- Removing a violation should drop the pin in the same PR; the test emits a warning if a pin can be ratcheted down.
- The Rule 5 density test is gated as `pytest.skip` until v0.11.5; flipping to passing is the gate that proves the v0.11.5 work landed.

### Roadmap

| Version | Focus |
|---|---|
| v0.11.3 | Rule 1 + Rule 3 fixes — refactor `es_hd_state.c` HD pipeline (combined `goto` + `malloc` removal via static / caller-supplied buffers). |
| v0.11.4 | Rule 4 — split the 4 long functions into <60-line factors. |
| v0.11.5 | Rule 5 — add 64+ assertions across the 32 functions; gate behind `#ifndef NDEBUG`. |
| v0.11.6 | Rule 10 — cross-platform pedantic-build CI matrix. |
| v0.11.7 | Rules 6 + 7 — manual variable-scope and return-value audits. |

### Migration

None. Audit-only release.

## [0.11.1] — 2026-05-05

**Research notebook hygiene: backfill §7.4 (STLT) and §7.5 (SPrT); refresh Status banner.** Documentation-only release.

### Why this exists

User noticed during the v0.11.0 SPrT ship: *"just double checking, we added GR to our research notebook too?"* — and the answer was no. Both v0.10.0 STLT and v0.11.0 SPrT shipped with full bridge / CLI / test surfaces but without their notebook §7.x sections. The existing freshness checks (`tests/test_readme_freshness.py`) cover the README — they don't see the research notebook.

### Fixed

- **Notebook §7.4 added — Sol Terra-Luna Time (STLT).** Covers the system-clock framing, the Meton 432 BCE default-epoch choice, the Hipparchus-Babylonian-midpoint convergence story, the `Z₅` algebraic-spine connection, the available alternative epochs, the house-epoch-vs-NASA-LCT framing, and the bridge / CLI surface.
- **Notebook §7.5 added — Sol Proper Time (SPrT).** Covers the per-body diagonal-fiber framing (extending Mercury's existing 43″/century PN diagonal to all 38 bodies), the two leading-order components (`GM/(R·c²)` + `v_orb²/(2c²)`), the validation table against six published values, the user's transparent `--proper` UX, the two-implementation discipline, and the deferred items (rotational kinematic, J₂ oblateness, frame dragging).
- **Notebook Status banner refreshed.** Was stale at v0.7.0; now reads v0.11.1 with the headline-state summary.
- **Notebook Release History block backfilled** with v0.9.2, v0.9.3, v0.10.0, v0.11.0, and v0.11.1 entries (was ending at v0.9.1).

### Discipline

- New task #98 captured: a soft-warning "docs probably need updating" check on PRs. Would have caught the v0.10.0 / v0.11.0 gaps automatically.

### Migration

None. Documentation-only.

## [0.11.0] — 2026-05-05

**Sol Proper Time (SPrT) — gravitational + orbital-kinematic time dilation, applied transparently via `--proper` on every `time-*` subcommand.**

### The framing

The user asked: *"can we simply add `--proper` as a line arg to invoke gravitational time dilation fiber so that users don't even need to know anything extra had to happen in the back end?"*

That's exactly what shipped. `--proper` is opt-in (default off, no behavior change for v0.10.0 callers); when set, it augments any Sol Time bridge result with proper-time-corrected count fields (`<count>_proper`) plus a `proper_time` metadata block. Same physics as Mercury's existing 43″/century PN diagonal correction; SPrT extends the per-body diagonal-fiber treatment to every body in the roster.

### Validated against published values

Six leading-order checks, all within 0.30 % rel err:

| Check | Computed | Expected | Source |
|---|---|---|---|
| Earth surface GR | 6.961e-10 | 6.95e-10 | Ashby 2003 / GPS clock corrections |
| Sun surface GR | 2.123e-6 | 2.12e-6 | Standard solar physics |
| Mars surface GR | 1.400e-10 | 1.40e-10 | Genova et al. 2014 / Curiosity rover |
| Pluto surface GR | 8.136e-12 | 8.15e-12 | New Horizons mission planning |
| Terra orbital kinematic | 4.935e-9 | 4.95e-9 | v_terra² / (2c²) standard |
| Mars-vs-Terra GR difference | 5.561e-10 | 5.56e-10 | The 0.0175 s/Earth-year Curiosity figure |

### Added

**Python API:**
- `bridge.get_proper_time_rate(body, *, lat=None, lon=None, jd_tdb=None, reference="tcb")` — leading-order rate vs. TCB / TDB. Returns `{components: {gr_surface, kinematic_orbital, j2_oblateness, total}, rate_relative_to_reference, ...}`.
- `bridge.compare_proper_times(body_a, body_b, *, reference="tcb")` — rate ratio + drift per Earth-year between two bodies.
- `bridge.apply_proper_correction(result, subcommand, ...)` — post-processor used by the CLI's `--proper` flag.
- `_research/proper_time.py`: `ProperTimeRate` dataclass + the same primitives at the research-module layer.
- `Body.surface_radius_km` field — volumetric mean radius in km, populated for all 38 bodies in the roster.

**CLI:**
- `--proper`, `--lat`, `--lon`, `--reference` flags added uniformly to **every** `time-*` subcommand via the shared `_add_proper_flags` helper. Default off → v0.10.0 callers see no change.
- `time-proper` standalone subcommand for the rate-only query: `--body <X>` for a single body's rate, `--compare-to <Y>` for the two-body drift figure.

**Examples:**
```bash
# Proper-time-corrected Mars Sol Date
ephemerides-spectral time-mars --jd 2451545.0 --proper

# Proper-time-corrected STLT synodic count
ephemerides-spectral time-terra-luna --jd 2451545.0 --epoch meton --proper

# Standalone rate query — Mars vs. TCB
ephemerides-spectral time-proper --body mars

# Two-body comparison — Mars-Terra clock-rate difference
ephemerides-spectral time-proper --body mars --compare-to terra
```

### Discipline

- 32+ new SPrT tests in `tests/test_sprt.py` pin the validation set + every component + the CLI surfaces.
- Three new bridge methods classified `python_only` in `tests/test_parity_smoke.py::PARITY_TARGETS` (C twin queued).
- Manifest regenerated via `codegen/regenerate.py`.
- `proper_time.py` added to `_INCLUDED_MODULES` in `codegen/emit_research_modules.py` so the package codegen picks it up alongside the other research modules.
- `tests/test_readme_freshness.py` invariants caught the v0.10.0-banner-still-says-v0.10.0 drift the moment the version bumped.

### Out of scope (deferred to v0.12.0+)

- Surface rotational kinematic (`ω × R`) — for most bodies the orbital term dominates; for the Sun, rotational dominates.
- J₂ oblateness corrections (~10⁻¹⁵ scale) — `--lat` / `--lon` already accepted for forward compatibility; v0.11.0 ignores them.
- Frame dragging (Lense-Thirring) — ~10⁻¹⁵ at Earth-Moon scale; skip until needed.

### Migration

None. Existing scripts and bridge calls are unchanged. SPrT is purely additive.

## [0.10.0] — 2026-05-05

**Sol Terra-Luna Time (STLT) — system-level clock for the Terra-Luna pair, with Meton's 432 BCE summer solstice as the default epoch.** First Sol Time member with a non-J2000 default anchor.

### The framing

What we call "STLT" is a *system-level* clock — natural unit is the synodic month (29.530589 days), natural references are eclipse cycles (Saros 18.03 yr) and solar-lunar reconciliation cycles (Metonic 19.00 yr). The existing Sol Time series anchored individual bodies (Sol Mars, Sol Venus, ...); STLT anchors the *pair*.

The default epoch is **Meton of Athens's summer solstice on 27 June 432 BCE proleptic Julian** — the calibration anchor of the Metonic cycle, the lunar-solar reconciliation Greek mathematical astronomy was built on. This choice is independently validated by `research/lunar_epoch_candidates.py`: the Hipparchus-Babylonian eclipse-archive midpoint (Mardokempad 721 BCE + Hipparchus 141 BCE) lands within +240 days of Meton's solstice — *same year*, eight months later. Greek astronomy's eclipse archive is centred on Meton's lifetime; the "combo" candidate test confirms his anchor numerically.

This is a **house-epoch design choice** — not a claim to be NASA's eventual Lunar Coordinated Time (LCT) standard, which is still pending standardisation per the April 2024 White House directive. When LCT lands, we add it as a sibling epoch.

### Added

**Python API:**
- `bridge.jd_to_sol_terra_luna_time(jd_tdb, *, epoch="meton")` → `{epoch_name, epoch_jd_tdb, days_since_epoch, synodic_count, synodic_phase, saros_count, saros_phase, metonic_count, metonic_phase, ...}`. The full epoch metadata block carries the abbreviation `"STLT"`, the cycle constants, and the available-epochs roster.
- `bridge.sol_terra_luna_time_to_jd(synodic_count, *, epoch="meton")` — inverse on the synodic-month count.
- `_research/time_scales.py`: `TerraLunaTime` dataclass, `jd_to_terra_luna_time`, `terra_luna_time_to_jd`, plus the constant set: `STLT_SYNODIC_MONTH_DAYS`, `STLT_SAROS_CYCLE_DAYS`, `STLT_METONIC_CYCLE_DAYS`, `STLT_EPOCH_{METON,ANTIKYTHERA,HIPPARCHUS,MARDOKEMPAD,J2000}_JD_TDB`, `STLT_EPOCHS`, `STLT_DEFAULT_EPOCH`.

**CLI:**
- `ephemerides-spectral time-terra-luna --jd <X>` (canonical) — defaults to Meton's epoch; `--epoch {meton,antikythera,hipparchus,mardokempad,j2000}` switches anchors.
- `--synodic-count <N>` inverts: synodic-month count → JD_TDB.

**Available epochs:**
- `meton` (default) — Meton's summer solstice 432 BCE.
- `antikythera` — solar eclipse 23 Aug 205 BCE; Antikythera mechanism Saros-dial anchor (Freeth & Jones 2012).
- `hipparchus` — Hipparchus's lunar eclipse 25 Jan 141 BCE (Almagest VI.5).
- `mardokempad` — Babylonian lunar eclipse 19 Mar 721 BCE (Almagest IV.6); the foundational Babylonian record Hipparchus calibrated against.
- `j2000` — modern reference, Terra-borrowed.

**Research:**
- `research/lunar_epoch_candidates.py` — the Phase A scoring script. Enumerates all five candidates against the spectral kernel (`find_syzygies`) + skyfield ground truth, dumps a markdown report under `figures/lunar_epoch_candidates.md`. Also handles solstice diagnostics with epoch-of-date precession correction (~33° at 2400 yr) so candidate validation isn't dominated by precession noise.

### Fixed

- `bridge.find_syzygies(backend="auto")` was rejected by `_validate_backend` — same latent bug class fixed for `get_breathing_modulation` in v0.9.2 (`SUPPORTED_BACKENDS` doesn't include the `"auto"` sentinel). Now resolves `"auto"` → concrete backend before validation, matching the docstring contract. Caught while writing the research script; fixed in passing.

### Discipline

- Both new bridge methods classified in `tests/test_parity_smoke.py::PARITY_TARGETS` as `python_only` (pure-Python time-scale formula; C twin queued).
- Manifest regenerated via the project's official `codegen/regenerate.py` — no hand-edited SHAs.
- `tests/test_readme_freshness.py` invariants enforced: Status section + banner + CLI body-name examples.

### Migration

None required. Existing scripts and bridge calls unchanged. STLT is purely additive.

## [0.9.3] — 2026-05-05

**PyPI-facing README staleness sweep + CI freshness check.** Docs-only — no API or encoder changes.

### Why now

User flagged the Status and Roadmap sections of the PyPI-facing README as stale. The Status block ended at v0.6.1 — eight versions back. The Roadmap listed Tier 2b "in progress" (shipped in v0.7.0), Sol Venusian/Mercurian Time as upcoming (shipped in v0.8.0; renamed in v0.9.1), and the ITN pathway / `find-tubes` query as upcoming (shipped in v0.8.1). Plus leftover `--body earth` example strings from before the v0.9.0 body-identity rename.

### Fixed (manual sweep)

- **Status section refreshed** with v0.7.0 → v0.9.3 entries. Current marker moved to v0.9.3.
- **Banner added** under the H1: `**Status: v0.9.3 — production-ready.**` Now pinned to `__version__` by the new freshness test.
- **Roadmap section pruned** of shipped items (Tier 2b, Sol Venusian/Mercurian Time, ITN pathway). Items genuinely still ahead retained and reorganized: first-principles per-resonance α, Hyperion follow-up, remaining 4 broken moons, Sol Moon Times, DE441 vs DE442 spectral error signature, heteroclinic-tube extension to `find-tubes`, LTC, Phase 10 resonance coverage, multi-millennium DE441 sweep, Doxygen, bit-serial hardware port.
- **Leftover earth-body CLI example strings** corrected to `terra` (in the `find-tubes` cheat-sheet and in Key Capabilities prose).
- **Phase 9 heading** inverted from `Phase 9 "Breathing" Couplings` → `Phase 9 Adaptive Couplings (a.k.a. "breathing")` matching the v0.9.2 CLI rename. Also updated the Cosine LUT row in the memory-footprint table.
- **Stale "v0.4+ ROADMAP: window search" comment** in the CLI cheat-sheet removed — `find-syzygies` shipped in v0.3.1.

### Added (drift prevention)

`tests/test_readme_freshness.py` enforces three invariants on every PR:

1. **Status section completeness.** Every released version in the package CHANGELOG must have a corresponding bullet under the README's `## Status` section. Reverse direction also enforced (no inventing unreleased versions in the README).
2. **Current-version stamp accuracy.** The `Status: vX.Y.Z` banner under the H1 *and* the `*(current)*` marker in the Status section must both equal `__version__`. Same pattern as `test_native_version_string_matches_package_version`.
3. **CLI body-name validity.** Every body name appearing after a body-flag in a CLI example (`--body NAME`, `--departure NAME`, `--target NAME`, `--pair-a NAME`, `--pair-b NAME`) must be in `SUPPORTED_BODIES`. Catches the v0.9.0 fallout pattern: examples pointing at body names that have been removed from the roster.

What this does *not* enforce: prose accuracy, Roadmap correctness, whether examples are *good* examples. Those stay in human review. Same modular discipline as `test_parity_smoke.py::PARITY_TARGETS` — enumerate the mechanically-checkable truth, fail loudly on drift.

### Migration

None. Docs-only release; no API surface changes.

## [0.9.2] — 2026-05-05

**CLI: `adaptive` is the primary name for Phase 9 state-dependent coupling modulation; `breathing` retained as a hidden synonym.** No public-API changes, no encoder hot-path changes.

### Added

- `ephemerides-spectral adaptive` — primary subcommand. Matches the adaptive-networks vocabulary (Gross & Blasius 2008; adaptive Kuramoto): a state-dependent graph Laplacian whose edge weights co-evolve with node phases.

### Changed

- `ephemerides-spectral breathing` — now registered with `help=argparse.SUPPRESS`. Invisible in `--help` listings, fully functional when typed. Cross-referenced from `adaptive --help`'s epilog and from the toplevel `--help`.

### Fixed

- `resolution --body` default and example strings updated `earth` → `terra` (consistent with the v0.9.0 body roster). `find-tubes` and `local-view` examples likewise corrected. The CLI help and `--body` validation are now self-consistent.
- **Latent bug since v0.8.0:** `get_breathing_modulation(backend="auto")` (its own default) was rejected by the `_validate_backend` check; any caller that didn't pass an explicit `backend=` got an "ok: false" error. `"auto"` is now resolved to a concrete backend before validation, matching the docstring. The CLI's `breathing` (now `adaptive`) subcommand was the principal victim.

### Internal

- Subparser argument registration factored through a shared helper so `adaptive` and `breathing` cannot drift apart.
- `_cmd_breathing` kept as an alias of `_cmd_adaptive` for external imports.

### Migration

None required. Both `adaptive` and `breathing` work; existing scripts unchanged.

## [0.9.1] — 2026-05-05

**Sol Time naming convention overhaul + Sol Terra Time + Sol Luna Time.**

> *"Returning to the giants whose shoulders we stand on. We've always had a lunar orbit and a lunar eclipse. We've all had terrain and terrestrial animals. We're just putting the books back in their dewey decimal spot."*

### Renames (BREAKING)

`Sol Mercurian/Venusian/Plutonian Time` → `Sol Mercury/Venus/Pluto Time`. Function names, dataclasses, and bridge methods all updated. Gas/ice giants (Jovian, Saturnian, Uranian, Neptunian) keep adjective forms — those are deeply established in astronomical tradition.

### New time systems (additive)

- **Sol Terra Time (STT)** — Terra's own surface clock; `bridge.jd_to_sol_terra_time(jd_tdb)`, CLI `time-terra`.
- **Sol Luna Time (SLT)** — Luna's surface clock; `bridge.jd_to_sol_luna_time(jd_tdb)`, CLI `time-luna`. **Distinct from Sol Lunar Time** (`get_lunar_phase`) which gives Luna's phase as observed from Terra.

### Abbreviation field

Each Sol Time bridge return's `epoch:` block now carries `"abbreviation": "STT"` / `"SLT"` / `"SVT"` / etc. per the user's indexing table.

### Tests

111 active tests pass; 5 skipped (4 cibuildwheel + 1 `tier1_skip`).

## [0.9.0] — 2026-05-05

**Body identity rename: `moon` → `luna`, `earth` → `terra`. BREAKING CHANGE.**

The body-identity strings now use Latin proper nouns. The generic English nouns are no longer privileged — `moon` is the category for any natural satellite, `earth` is the substance/ground.

### Migration

Anywhere your code references body identity by string, change:
```python
bridge.body_to_idx["earth"]    # before
bridge.body_to_idx["moon"]     # before
bridge.list_bodies()            # contained "earth"/"moon"
```
to:
```python
bridge.body_to_idx["terra"]    # after
bridge.body_to_idx["luna"]     # after
bridge.list_bodies()            # contains "terra"/"luna"
```

### What stays the same

- Category strings (`category == "moon"`) — moon is the generic category, not Luna's identity
- Adjective forms (`lunar`, `terran`/`terrestrial`)
- JPL/skyfield kernel identifiers (`"earth"`, `"moon"`, 399, 301)
- Encoded phase residues (uint32 output unchanged at the same JD)

### Tests

107 active tests pass; 5 skipped (4 cibuildwheel + 1 `tier1_skip` `find_itn_pathways`).

## [0.8.1] — 2026-05-05

**ITN pathway / Lagrange-tube query — `find-tubes` first cut.** "Surfing the perturbations": closed-form Hohmann transfer-window enumeration mirroring the v0.3.1 `find-syzygies` discipline. Pure-Python; C twin queued for a follow-up minor.

### Added

- `bridge.find_itn_pathways(jd_lo, jd_hi, departure, target, ...)` — Hohmann window enumeration anchored at body launch geometry (mean longitudes from `_data/initial_phases.json`).
- CLI `find-tubes` subcommand.

### Sanity

Earth → Mars at threshold 0.02 over J2000 + 50 yr returns 23 windows; each carries 258.87-d transfer time and 5.594 km/s total Δv. Matches textbook Hohmann to 0.01% / 0.1%.

### Tests

- 3 new immolation tests; 107 active tests pass; 5 skipped (4 cibuildwheel + 1 `tier1_skip` for `find_itn_pathways` pending the C twin).

## [0.8.0] — 2026-05-05

**Sol Symphony Times: 7 new planetary/stellar time systems** — Venus, Mercury, Pluto, Sol (the Sun), Jupiter, Saturn, Neptune join the Sol Time series.

### Added — bridge surface

14 new methods: `jd_to_sol_<body>_time(jd_tdb)` + `sol_<body>_time_to_jd(...)` for each of venusian, mercurian, plutonian, sol_sol, jovian, saturnian, neptunian.

### Added — CLI

7 new subcommands: `time-venus`, `time-mercury`, `time-pluto`, `time-sol`, `time-jupiter`, `time-saturn`, `time-neptune`. Use `--help` on each for the body's quirks (Mercury 3:2 spin-orbit resonance, Venus retrograde, Cassini-revised Saturn rotation, Neptune Voyager-2 System III, etc.).

### Naming hierarchy

Established: `Sol <Adjective> Time` (Sol Mars, Sol Lunar, Sol Uranian, etc.). Future moon ports: `Sol <Parent>-<Body> Time` (Sol Pluto-Charon, Sol Jupiter-Io, etc.).

### ABI

Unchanged at v5. These are pure-Python time-scale formulas; no C twin needed.

### Tests

104 active tests pass (was 84 in v0.7.0); 4 skipped (cibuildwheel-only).

## [0.7.0] — 2026-05-05

**C/Python parity Tier 2b: HD pipeline in C (ABI v5).** The architectural lift announced in v0.6.1 lands. Three new C entry points (`es_encode_state_hd`, `es_bind_observer`, `es_get_eclipse_probability`) plus bridge dispatch on `backend={"auto","bip","c","fpu-ref"}` for `get_local_view` and `get_eclipse_probability`. Parity smoke flips the two `tier2_skip` entries to `parity` — every encoder-touching bridge method now has a paired C path.

### Added

- `bridge.get_local_view(..., backend="auto"|"bip"|"c"|"fpu-ref", D=4096)` and `bridge.get_eclipse_probability(..., backend=..., D=4096)` accept a `backend` param. Result dicts carry a `backend` field.
- Python `_research/bip_hd_lift` module: `encode_state_hd`, `bind_observer`, `syzygy_operator`, `eclipse_probability`. Pure-Python implementations matching the C entry points.
- Native wrappers: `_native_bip.native_encode_state_hd`, `native_bind_observer`, `native_get_eclipse_probability`.

### Behaviour change

Default behaviour of `get_local_view` and `get_eclipse_probability` changes from FPU matrix-expm output to BIP-and-lift output. Different algorithms; **different state vectors**. The bridge contract (`{ok, state_interleaved_f32, probability, ...}`) is unchanged. Pass `backend="fpu-ref"` to get pre-v0.7.0 behaviour.

### Tests

- New `tests/test_hd_parity.py` — 8 byte-parity tests Python BIP-and-lift ↔ C.
- Parity smoke: 22/22 pass; **zero tier_skip entries remaining**.

84 active tests pass; 4 skipped (cibuildwheel-only).

## [0.6.1] — 2026-05-05

**Tier 2a foundation: portable channel-basis PRNG (ABI v4).** Groundwork for the v0.7.0 hyperdimensional-state-in-C work. No bridge surface change; no encoder behaviour change.

### What's in

- New C entry point `es_channel_basis(seed, out, D)` fills a deterministic complex64[D] channel-basis hypervector. New `es_complex64_t` typedef.
- New `_research/portable_prng.py` module: splitmix64 PRNG, bit-identical to the C `es_splitmix64_next`.
- New `tests/test_channel_basis_parity.py`: 10 parity tests pinning byte-identical agreement between Python + C across body seeds + production D.

### Why splitmix64

Reproducing numpy's PCG64-DXSM + uniform conversion exactly in C is brittle (~200 LOC; numpy bumps could break parity). Splitmix64 is six lines, identical across any IEEE-754 platform. Basis byte values change vs v0.6.0; not breaking (no test pinned them).

### Tier 2b (v0.7.0)

Once the foundation is solid, `es_encode_state_hd` + `es_bind_observer` + `es_get_eclipse_probability` land alongside bridge dispatch on `get_local_view` and `get_eclipse_probability`. Parity smoke flips both `tier2_skip` entries to `parity`. See `TIER2_DESIGN.md` in the source repo for the full plan.

### Tests

74 active tests pass; 6 skipped (4 cibuildwheel-only + 2 Tier 2b stubs).

## [0.6.0] — 2026-05-05

**C/Python parity Tier 1 + always-on parity smoke test (ABI v3).** Two encoder-touching bridge methods now have C twins; a new test pins parity as a durable discipline.

### Added — backend dispatch on existing bridge methods

`bridge.get_breathing_modulation(...)` and `bridge.find_syzygies(...)` both accept `backend={"auto", "bip", "c"}` (default `"auto"` picks C when available). Result dicts carry a `backend` field. C and BIP paths produce byte-identical output for the integer fields and float-ULP-equal output for the modulation factor.

### Added — `tests/test_parity_smoke.py`

The always-on parity guard. Every public `bridge.*` function is classified in a `PARITY_TARGETS` table; adding a new method without a parity classification fails CI. Tier 2 entries (`get_local_view`, `get_eclipse_probability`) are flagged as `tier2_skip` until the v0.7.0 hyperdimensional-state-in-C lift lands.

### ABI

`ES_ABI_VERSION` bumped 2 → 3. Encoder hot path is unchanged. Net-new entry points: `es_breathing_modulation`, `es_find_syzygies` (with `es_syzygy_t` struct).

### Notes

- 64 active tests pass on the v0.6.0 build; 6 skipped (4 cibuildwheel-only + 2 Tier 2 stubs).
- No body roster change. With no patches active, `get_system_state(backend="c")` returns the same uint32[38] as v0.5.5 (regression test pinned).

## [0.5.5] — 2026-05-05

**Moon catalog patches (Phase C).** Five LS-fit-vindicated moon patches join `CATALOG_V2`, completing the v0.5.x moon programme.

### Added — `CATALOG_V2`

| name | body | period | amp | shrinkage |
|---|---|---:|---:|---:|
| `dione-1.06yr-diagonal-v2` | dione | 387.04 d | 3.57° | **98.2%** |
| `tethys-0.38yr-diagonal-v2` | tethys | 138.24 d | 3.57° | **93.8%** |
| `enceladus-0.39yr-diagonal-v2` | enceladus | 141.94 d | 3.58° | **98.9%** |
| `titan-0.69yr-diagonal-v2` | titan | 252.74 d | 3.31° | **95.5%** |
| `iapetus-0.22yr-diagonal-v2` | iapetus | 79.34 d | 3.26° | **98.6%** |

Apply via `bridge.apply_patch("dione-1.06yr-diagonal-v2")` etc. Each entry's `notes` field pins its measured shrinkage% as a regression-test gate (the same convention v0.5.2 established for planet patches).

### Hyperion: PARTIAL (75.2%)

Hyperion's chaotic rotation (Wisdom 1984) shows quasiperiodic-not-sinusoidal residual structure: multiple sub-peaks near 72d. Single LS-fit sinusoid hits the methodological ceiling there. Hyperion stays out of `CATALOG_V2` until a multi-component or coupled Titan-Hyperion 4:3 patch passes the 80% bar.

### Notes

- The methodology is now vindicated **twice** on independent body sets: v0.5.2 planets (4 patches at 96-99%), v0.5.5 moons (5 patches at 93-99%). LS-fit amplitudes consistently 2-3× the FFT-bin baselines on both.
- No body roster change. v0.5.5 is purely additive on `CATALOG_V2`.

## [0.5.4] — 2026-05-05

**Sol Uranian Time (SUT)** — third planetary time system, alongside Mars Sol Date / Mars Coordinated Time and lunar synodic / sidereal phase. Plus a CLI `--help` audit (every subcommand now has examples + epilogs; the `patches` group's stale "C backend doesn't yet implement the overlay" notice from v0.4.0 is replaced with the v0.5.2 catalog-V2 reality).

### Added — Sol Uranian Time

- `research/time_scales.py` gains `UranianTime` dataclass + `jd_to_uranian_time(jd_tdb)` + `uranian_time_to_jd(usd)`. Three independent cycles:
  - **USD (Uranian Sol Date)** — sidereal-day count since the SUT epoch (2007-12-16 northern equinox, JD 2454451.0). 1 USD = 17.24 Earth-hours (retrograde rotation; magnitude is unsigned, the `retrograde=True` flag carries the direction).
  - **SUT (Sol Uranian Time)** — time-of-day at Uranus's prime meridian, 0–24 hours. 1 Uranian hour ≈ 43.1 Earth-minutes.
  - **Orbital phase + season** — Uranus's 84.02-yr orbit partitioned into 4 ~21-yr seasons. Anchored at the 2007 northern equinox. Names per the *northern* hemisphere's experience: northern-autumn (2007–2028), southern-summer (2028–2050), northern-spring (2050–2071), northern-summer (2071–2092).
- `bridge.jd_to_sol_uranian_time(jd_tdb)` and `bridge.sol_uranian_time_to_jd(usd)`. Pyodide-friendly JSON return shape; the result includes an `epoch` block with the IAU/NASA fact-sheet constants (sidereal day 17.24 h, orbital period 84.02 yr, axial tilt 97.77°).
- CLI `ephemerides-spectral time-uranus --jd ...` (or `--usd ...` to invert). Full `--help` epilog with examples.

### Why "Sol" prefix matters

The natural-harmonic framing (notebook §6, §7): Uranus's three independent cycles (sidereal day, solar day, orbital season) don't share clean coprime structure with anything else in the Sol Star System — Uranus doesn't participate in any wired RESONANCES entry, and its orbital period (84 yr) isn't an integer multiple of any nearby body's. **Sol Uranian Time lives in its own cyclic group, separate from the natural-resonance Z₆₀ of v0.5.0**. The "Sol" prefix marks it as one of multiple star-system-anchored planetary time systems (Sol Mars Time = MSD/MTC, Sol Lunar Time = synodic/sidereal phase, Sol Uranian Time = SUT/USD), all sharing JD as their common Earth-side reference.

### CLI `--help` audit

Every subcommand has been touched. Material updates:

- `patches` parent description corrected to reflect v0.4.1 + v0.5.2 (was: "C native backend doesn't yet implement the overlay" — outdated).
- `patches catalog` epilog now lists all 6 catalog entries (3 v0.4.0 magnitude-only + 3 v0.5.2 LS-fit `-v2` with measured shrinkage% per entry).
- `patches active`, `patches apply --name ...`, `patches clear` get explicit `description` + `epilog` blocks with concrete examples.
- New `time-uranus` subcommand naturally has both `description` + `epilog` per the CLI convention.

### Tests

6 new tests in `test_immolation.py`:
- `test_sol_uranus_time_at_epoch_returns_zero_usd` — SUT epoch yields exactly USD=0, SUT=0.0 hr, season=northern-autumn.
- `test_sol_uranus_time_round_trip` — JD → USD → JD round-trips to within ULP.
- `test_sol_uranus_time_carries_retrograde_flag` — `retrograde=True` and the epoch metadata is correct.
- `test_sol_uranus_time_advances_uniformly` — USD advances at exactly 1 USD per `URANUS_SIDEREAL_DAY_DAYS`.
- `test_sol_uranus_time_seasons_partition_orbit_into_four` — boundary at orbital_phase=0.25 transitions from northern-autumn to southern-summer.
- `test_bridge_has_v054_uranus_surface` — the new bridge functions are exported.

27 active tests pass total (was 21 in v0.5.3); 18 skipped (cibuildwheel-only native parity).

### Notes

- The function names follow Python adjective-form convention: `jd_to_uranian_time` (mirrors `jd_to_lunar`), `bridge.jd_to_sol_uranian_time`. The proper-noun `Uranus` shows up only in module-level constants (`URANUS_SIDEREAL_DAY_HOURS` etc.) where it identifies the body itself.
- Uranus rotates **retrograde** (rotation direction is backwards relative to its orbital motion). v0.5.4's encoder still advances `omega = +2π/P` for all bodies regardless of direction; surfacing the `retrograde=True` flag makes this asymmetry visible to consumers but doesn't yet *fix* it. Phoebe's continued ~104° RMS in the v0.5.3 moon FFT sweep is the same retrograde-encoder issue; both are queued for a sign-aware-omega fix in v0.5.x.

See the [project CHANGELOG](../CHANGELOG.md) for the full v0.5.4 entry.

## [0.5.3] — 2026-05-05

**Moon residuals: 13 of 17 moons fixed via high-precision sidereal periods.** The v0.5.2 ~100° RMS residuals on the broken moons turned out to be **period truncation** in the `BODIES` table — fast-orbit moons (Io 1.77 d, Metis 0.29 d, Mimas 0.94 d, etc.) accumulated 10⁻⁴-relative omega errors over the 41,000+ orbits in the 200-yr sweep horizon, wrapping as a sawtooth into the FFT's near-DC content. Replacing the 3-4-decimal periods with 9+-decimal sidereal periods from JPL HORIZONS / NASA fact sheets fixes the 13 most affected moons.

### Diagnosis (research/diagnose_moon_residual.py)

Within ONE orbital period the "broken" moons show TINY residuals (Io: 0.42°, Metis: 0.07°, Europa: 0.81°). The ~100° v0.5.2 sweep RMS is **secular accumulation** over many periods, not within-orbit warping. The frame-mismatch hypothesis from notebook §3 was wrong; the actual cause is period truncation.

### Fix (bodies.py)

All sidereal periods stored to 9+ decimals. Sources: JPL HORIZONS (canonical) + NASA fact sheets (cross-checks). Examples:
- io: `1.769` → `1.76913786`
- europa: `3.551` → `3.551181`
- ganymede: `7.155` → `7.15455296`
- mimas: `0.9424` → `0.94242196`
- enceladus: `1.370` → `1.37021785`

### Measured improvement

| Moon | v0.5.2 RMS | v0.5.3 RMS | improvement |
|---|---|---|---|
| **io** | 106° | **0.34°** | **-317×** |
| **europa** | 116° | **0.76°** | **-154×** |
| **ganymede** | 117° | **0.14°** | **-825×** |
| **adrastea** | 104° | **0.07°** | **-1450×** |
| **amalthea** | 102° | **0.27°** | **-376×** |
| **enceladus** | 103° | **2.57°** | **-40×** |
| **tethys** | 101° | **2.94°** | **-34×** |
| **dione** | 117° | **2.54°** | **-46×** |
| mimas | 104° | 30.8° | -3.4× (partial) |
| metis | 104° | 109° | unchanged |
| thebe | 105° | 104° | unchanged |
| rhea | 98° | 100° | unchanged |
| phoebe | 104° | 104° | unchanged |

**13 of 17 moons** drop into Callisto-class clean territory (≤ 3° RMS; previously only 4 were clean: Callisto, Titan, Iapetus, Hyperion). See [`figures/moon_residual_v0.5.3.md`](../figures/moon_residual_v0.5.3.md) for the full pre/post comparison + the diagnostic methodology.

### Still broken (queued for v0.5.x phase B+)

- **Metis** — published sidereal periods vary across sources (0.2948 d, 0.294778 d, etc.). Needs a definitive authoritative value.
- **Thebe** — non-zero inclination + eccentricity; remaining residual may be perturbation-driven.
- **Rhea** — published period matches to 6 decimals; could be a frame issue (0.35° inclination to Saturn's equator) or perturbation from neighbouring moons.
- **Phoebe** — RETROGRADE; orbits backward relative to Saturn. Our encoder advances `omega = +2π/P` regardless of direction. May need a sign flip or a frame fix specific to retrograde irregulars.

These four are physics-specific investigations queued for individual fixes after v0.5.3 ships.

### What this earns

The LS-fit catalog methodology (v0.5.2, §9) now applies to moons. With 13 moons in clean ≤ 3° RMS, the next step is to author per-moon catalog patches against whatever residual peaks remain — likely surfacing measurement-validated coefficients for the Saturnian resonances (Mimas-Tethys 4:2, Enceladus-Dione 2:1, Titan-Hyperion 4:3) that v0.5.0 wired into `RESONANCES` but couldn't yet calibrate.

See the [project CHANGELOG](../CHANGELOG.md) for the full v0.5.3 entry.

## [0.5.2] — 2026-05-05

**Patch-shrinks-residual benchmark — FULLY VINDICATED on planets** via least-squares fitting at the exact target period (replaces FFT-bin extraction). Mars 99.2%, Mercury 99.9%, Jupiter 97.6%, Saturn 96.0% shrinkage. Moon-kernel infrastructure ships alongside; moon-residual root cause is queued for v0.5.x.

### Added — CATALOG_V2 (LS-fit, vindicated)

- `research.diagnosed_fibers.CATALOG_V2` — three patches with measured ≥96% shrinkage:
  - `mars-7.96yr-diagonal-v2`: `amp=10.69°`, `period=2902.74 d`, `phase=0.34 rad` → **99.2% shrinkage**
  - `mercury-10.69yr-diagonal-v2`: `amp=23.48°`, `period=3898.87 d`, `phase=3.05 rad` → **99.9%**
  - `jupiter-saturn-9.56yr-coupled-v2`: `amp=113.29°`, `period=3495.81 d`, `phase=6.02 rad`, `correlation=+1` → **97.6% J / 96.0% S**
- The original v0.4.0 `CATALOG` stays unchanged for backwards compatibility. `bridge.list_catalog_patches()` now shows 6 patches (3 v1 + 3 v2). Apply v2 entries via the `-v2` suffix.

### Added — research-side LS-fit authoring

- `research/author_phase_recovered_patches.py` gains a `method="lsq"` mode (default). Uses `scipy.optimize.curve_fit` to fit a sinusoid at the target period, with the period as a free parameter constrained to ±60 days. Bypasses FFT bin leakage entirely.
- LS-fit recovers ~25–55% larger amplitudes than the v0.5.1 FFT-bin extraction (Mars 6.90° → 10.69°, +55%; J–S 89.65° → 113.29°, +26%) — the energy that was leaking into adjacent bins.

### Added — moon-kernel infrastructure

- `research/ephemeris_loader.py`: `load_ephemeris(..., auxiliary_kernels=["mar099s", "jup365", "sat441"])`. The bundle now carries `extra_ephs: List[Any]` and a `lookup(target_key)` method that searches the main DE441 + each auxiliary in order.
- `bip_instrument._calibrate_initial_phases` and `de441_error_spectrum._truth_longitude` use `bundle.lookup` so moon truth values come from the supplementary kernels.
- `research/de441_moon_spectrum.py` is a moon-friendly FFT sweep (`±200 yr` around J2000, 30-d cadence, 4096 samples) that fits inside jup365 / sat441 coverage windows.

### Findings

- **J–S correlation = +1, not −1.** v0.4.0's anti-correlated-libration assumption was empirically wrong; LS-fit `Δφ_a − Δφ_b` at 9.56 yr puts the residuals in-phase.
- **LS-fit periods drift ~0.16% from bin-rounded.** Mars: −4.6 d, Mercury: −6.2 d, J–S: +4.9 d. The drift is what makes the catalog work — patches land on the *actual* residual frequency, not the nearest FFT bin.
- **Most v0.5.0 moons show ~100° RMS residuals** dominated by near-DC content (FFT peaks at the sweep span = 336 yr). Callisto, Titan, Iapetus, Hyperion are the 4 "working" moons (RMS ≤ 11°). Root cause for the others is queued for v0.5.x — likely a calibration mismatch when looking up moon barycenters across stacked SPK kernels.

### Tests

- `test_catalog_lists_six_patches_v041_plus_v052` (renamed from `test_catalog_lists_three_v041_patches`) — asserts the combined v1+v2 catalog has the 6 expected patch names.

### Notes

- The v0.4.0 catalog is **not deprecated** — it ships unchanged. Users who want vindicated-shrinkage patches use the `-v2` names; users who want the original catalog (e.g., for backwards-compatibility regression tests) use the v0.4.0 names.
- `de441_error_spectrum.run_spectrum`'s `top_peaks` K parameter bumped 20 → 100 so a successful patch's demoted target peak is still findable in the top-K set.

See the [project CHANGELOG](../CHANGELOG.md) for the full v0.5.2 entry.

## [0.5.1] — 2026-05-05

Patch-shrinks-residual benchmark — earn the right to predict missing
data. Verdict: **PARTIAL** (J–S ~77%, Mercury ~40%, Mars stuck at 3%
due to FFT bin leakage). The v0.4.0 catalog had two authoring bugs
that this audit surfaced: amplitude was off by 2× (used
magnitude-spectrum instead of real-amplitude), and phases were
wrongly assumed to be 0.

### Added — research-side benchmarking

- `research/patch_shrinks_residual.py` — runs the v0.5.0
  `de441_error_spectrum` FFT twice per catalog patch (off vs on),
  measures shrinkage of the targeted FFT peak. Reports verdict per
  patch and overall.
- `research/author_phase_recovered_patches.py` — re-authors each
  catalog patch from the FFT's *complex* spectrum: amplitude is
  `2 |X[k]| / N`, phase is `arg(X[k]) - π/2 + 2π · half_span / period`
  (the second term accounts for the FFT phase being referenced to
  sample 0 = `REFERENCE_JD - half_span`, not REFERENCE_JD itself).
  Coupled patches recover the correlation sign (in-phase = +1,
  anti-phase = −1) from the J–S residual phase difference at the
  target period.
- `research/verify_recovered_patches.py` — re-runs the benchmark
  with the phase-recovered catalog to measure the improvement.

### Findings — `figures/patch_shrinks_residual_v0.5.1.md`

| Patch | v0.4.0 (mag-only) | v0.5.1 (recovered) |
|---|---|---|
| `mars-7.96yr-diagonal` | +2.5% | +2.7% (still stuck) |
| `mercury-10.69yr-diagonal` | **−49.9% (peak GREW)** | **+39.6%** |
| `jupiter-saturn-9.56yr-coupled` | +30.9% J / −0.4% S | **+77.1% J / +76.4% S** |

Mercury swung 138 percentage points; J–S went from one-sided to
balanced ~77% shrinkage on both bodies after the correlation flip
(`−1 → +1`). Mars stays stuck because its 7.96 yr signal smears
across two adjacent FFT bins (rank-1 at 7.960 yr / 3.45° and rank-2
at 7.935 yr / 3.36°) — a single-frequency patch can't cancel
FFT-leaked energy. Windowed FFT authoring + multi-bin patches will
unblock Mars (queued for v0.5.2+).

### Critical methodology bugs surfaced (v0.4.0 catalog)

- **Amplitude off by 2×.** For a real-valued residual, the FFT bin's
  energy is split between `+k` and `-k`; the actual real-sinusoid
  amplitude is `2 |X[k]| / N`, not `|X[k]| / N`.
- **Phase assumed 0.** Magnitude-only authoring discards phase.
  Adding a wrong-phase patch can either partially cancel, have no
  effect, or *reinforce* the residual (Mercury was reinforced by
  ~50% with phase=0).
- **J–S correlation was wrong.** v0.4.0 set `correlation = −1`
  (anti-correlated libration). The recovered phase difference says
  `correlation = +1` (in-phase). The libration-physics intuition was
  empirically wrong at the FFT level.

### Notes

- The v0.4.0 catalog stays unchanged in the wheel — the
  phase-recovered catalog lives in `results/phase_recovered_catalog.json`
  as research output, not yet a shippable replacement (it doesn't
  meet the ≥80% bar across all bodies). v0.5.2 will unblock Mars via
  windowed FFT and ship a `CATALOG_V2`.
- `de441_error_spectrum`'s top-K peaks bumped from 5 to 20 so the
  benchmark can find a target peak even after a successful patch
  demotes it out of the original top-5 (which is what initially
  hid Jupiter's 77.1% shrinkage as "no peak in tolerance").

See the [project CHANGELOG](../CHANGELOG.md) for the full v0.5.1 entry.

## [0.5.0] — 2026-05-05

The Galilean marshaling: all major Jovian and Saturnian moons join the encoder. Body count grows from 26 to **38**. SPICE-free runtime — `pip install ephemerides-spectral` and encode immediately, no kernel staging required.

### Added — 12 new bodies

- **Jovian inner regulars (4)**: Metis, Adrastea, Amalthea, Thebe. Periods 0.30–0.67 d (Metis is the new shortest-period body in the roster — was Phobos at 0.32 d).
- **Classical Saturnian moons (6)**: Mimas, Tethys, Dione, Hyperion, Iapetus, Phoebe. Together with v0.1.0's Enceladus / Rhea / Titan, this completes the canonical 9 Saturnian moons.
- **Saturn co-orbitals (2)**: Janus, Epimetheus (the famous "swap orbits every 4 yr" pair).

### Added — 3 new resonances

- **Mimas–Tethys 4:2** (the libration that maintains the Cassini Division)
- **Enceladus–Dione 2:1** (powers Enceladus's tidal heating + plumes)
- **Titan–Hyperion 4:3** (source of Hyperion's chaotic rotation)

The natural-resonance cyclic group expands from **Z_30** (v0.2.0–v0.4.x: lcm(10, 6, 2, 2)) to **Z_60** (v0.5.0: lcm(10, 6, 2, 2, 4, 2, 12)). Same prime factor set {2, 3, 5}, but the multiplicity of 2 grew from 1 to 2 because the Titan-Hyperion 4:3 contributes lcm(4, 3) = 12.

### Added — SPICE-free BIP runtime

- New codegen step (`codegen/emit_initial_phases.py`) emits `_data/initial_phases.json` containing the calibrated initial phases at REFERENCE_JD = J2000.0. Same SSOT the C codegen uses to bake `es_initial_phases[]` — Python BIP and native C are byte-identical by construction now.
- `EphemerisBIPInstrument._calibrate_initial_phases` now consults `_data/initial_phases.json` first; only falls back to live SPICE calibration when the JSON is missing (research source tree, codegen-time itself). The silent zero-phase fallback when no SPICE was staged is gone.
- `pip install ephemerides-spectral` works out of the box for both backends — no kernel staging required for basic encoding. Skyfield + jplephem are still optional dependencies (`[ephemeris]` extra) for callers who want runtime calibration against custom kernels.

### Changed

- **`ES_N_BODIES = 38`** in the C header (was 26). Fully regenerated `c/src/es_bodies.c`, `c/src/es_laplacian.c`, `_data/initial_phases.json`, `_data/manifest.json`. ABI v2 unchanged (the body count is in the header, not the wire format).
- **C codegen kernel standardised on de441** (was de421); the Python wheel codegen and C-side codegen now use the same kernel so initial phases agree byte-exactly.
- **44 off-diagonal couplings** (was 26) — every new moon adds a planet-moon coupling, plus three new inter-moon resonance couplings.

### Tests

- `test_native_parity.py::test_default_encode_native_matches_python` shape assertion now reads `expected_n` from the live `BODIES` dict instead of hardcoding 26 — automatically tracks future roster growth.
- `test_immolation.py::test_natural_resonance_group_returns_z60` (renamed from `test_natural_resonance_group_returns_z30`): asserts the v0.5.0 resonance set yields modulus 60 with prime factors {2, 3, 5}.

### Notes

- v0.4.0 catalog patches still work — `mars-7.96yr-diagonal`, `mercury-10.69yr-diagonal`, `jupiter-saturn-9.56yr-coupled` apply unchanged on the v0.5.0 38-body roster.
- **Pre-ship FFT validation**: the DE441 error-spectrum sweep was re-run before tagging. Every peak amplitude on the 10 DE441-coverable bodies is byte-identical to the v0.3.1 baseline (the v0.5.0 expansion adds *moon-internal* resonances that don't perturb planet phases). The v0.4.0 catalog patches remain the right targets; no new ones are needed for the validated bodies. Sweep time dropped from 314.9 s → 14.6 s (21× faster) thanks to the v0.4.1 C native + v0.5.0 SPICE-free init phases.
- The new moons themselves cannot be FFT-validated yet — DE441 only carries planet barycenters + Sun + Earth + Moon. Supplementary-kernel codegen (`mar097` / `jup340` / `sat441`) is queued for v0.5.x; once staged the moons get real ephemeris truth at REFERENCE_JD and the FFT can surface any moon-specific residuals.

See the [project CHANGELOG](../CHANGELOG.md) for the full v0.5.0 entry.

## [0.4.1] — 2026-05-05

C-side runtime kernel patching (ABI v2). The native backend now
applies the diagnosed-fiber overlay; `backend="c"` produces
byte-identical phases to `backend="bip"` even with patches active.

### Added

- **C-side patch registry** (`c/src/es_patches.c`): `es_apply_patch`, `es_clear_patches`, `es_n_active_patches`, `es_get_patch_at` plus the `es_patch_t` struct (`kind`, `name[64]`, `body_idx_a/b`, `amplitude_deg`, `period_days`, `phase_rad`, `correlation`). Capacity `ES_MAX_PATCHES = 32`.
- **Encoder hook** in `es_encode_state`: after the base loop + sub-day remainder, before the final cyclic-group reduction, the overlay sums per-body residue deltas matching the Python BIP encoder byte-for-byte. Banker's rounding (`es_banker_round`) shared between encode and overlay paths to match `numpy.round` half-to-even semantics.
- **Python ctypes shim** (`_native_bip.py`): bumped `EXPECTED_ABI_VERSION = 2`; new `EsPatch` ctypes struct + `native_apply_sinusoid_patch`, `native_apply_coupled_patch`, `native_clear_patches`, `native_n_active_patches` helpers.
- **Bridge sync layer** (`_mirror_patch_to_native`): every `apply_patch` / `apply_custom_patch` mirrors into the C registry; failures roll back the Python registry so the two never drift. `clear_patches` clears both.

### Changed

- **`backend="c"` no longer falls back to `"bip"` when patches are active.** With the native binary loaded, the C path applies the overlay natively. Falls back to BIP only when `_native_bip.HAS_NATIVE` is False (sdist install without C toolchain, Pyodide / WASM, pure-Python wheel).
- **Performance**: encoded with 3 patches active, the C path runs at **~46 μs** vs **~10.8 ms** on the BIP path — a **237× speedup**. Patch overhead per encode is **+19 μs** on C (vs +418 μs on BIP); the libm sin call is the only float operation, fired once per active patch outside the hot chunk loop.

### Tests

- New `test_cross_backend_parity_with_patches` — asserts BIP and C produce byte-identical `phases_uint32` for all three catalog patches stacked on a representative JD.
- New `test_native_registry_in_sync_with_python` — `n_active` agrees between Python and C registries through every apply/clear/duplicate-rejection path.
- Updated `test_c_backend_handles_overlay_when_loaded` (was `test_c_backend_falls_back_when_patches_active` in v0.4.0): the v0.4.0 fallback property is replaced by the v0.4.1 native-overlay property; falls back only when no native is loaded.

### Notes

- ABI v2 is a wire-format break vs ABI v1 (v0.3.1). Any consumer holding a v0.3.1 native binary alongside a v0.4.1 Python wheel will see `HAS_NATIVE=False` with `LOAD_ERROR` reporting the version mismatch — no silent corruption.

See the [project CHANGELOG](../CHANGELOG.md) for the full v0.4.1 entry.

## [0.4.0] — 2026-05-05

Runtime kernel patching — diagnosed-fiber overlay on the spectral kernel.

### Added

- **Diagnosed-fiber runtime overlay** — `bridge.apply_patch(name)` / `apply_custom_patch(...)` / `list_active_patches()` / `list_catalog_patches()` / `clear_patches()`. Patches are *data*, summed onto encoded phases at encode time as an overlay on the published kernel — kernel bytes never change. The CLI mirrors 1:1: `ephemerides-spectral patches {catalog,active,apply --name ...,clear}`.
- **Patch catalog** authored from v0.3.1's `de441_error_spectrum` FFT analysis: `mars-7.96yr-diagonal` (3.45° amplitude); `mercury-10.69yr-diagonal` (9.19°); `jupiter-saturn-9.56yr-coupled` (45° anti-correlated, the smoking-gun J–S 5:2 libration depth).
- **Two patch kinds:** `SinusoidPatch` (diagonal, single body) and `CoupledSinusoidPatch` (off-diagonal, two bodies with `correlation ∈ {-1, +1}`).
- **`figures/runtime_kernel_patching.md`** + `research/demo_runtime_patches.py` — pre/post tables showing per-body delta contributions across a JD ladder.

### Changed

- **`backend="c"` falls back to `"bip"` when patches are active.** Correctness over speed; the C-side overlay (ABI v2) lands in v0.4.x phase F.
- **BIP encoder integration:** `_encode_state_impl` queries `diagnosed_fibers.evaluate_active_patches` after the base encode loop; with no patches active the encode is byte-identical to v0.3.1 (pinned by a regression test).
- **Codegen ships `_research/diagnosed_fibers.py`** alongside the existing 8 research modules; the manifest carries 9 frozen-data files now.

### Tests

- `tests/test_runtime_patches.py` — 12 tests pinning the structural overlay properties: clear-restores-byte-identical baseline; diagonal patches don't leak; coupled J-S patches anti-correlated to within ULP; composition is order-independent; duplicate-name `apply_patch` is a hard error; C backend transparently falls back when patches active; `apply_custom_patch` constructs from primitive args.

### Notes

- Patches are **empirical Fourier corrections**, not first-principles physics. They paper over missing coupling entries in `RESONANCES` / `L_static` or missing PN terms. v0.5.x's first-principles α derivation should ultimately replace them.
- The runtime registry is **in-process** — re-apply on each fresh interpreter. Each Python invocation starts with no active patches.

See the [project CHANGELOG](../CHANGELOG.md) for the full v0.4.0 entry.

## [0.3.1] — 2026-05-04

C-in-wheel, spectral syzygy window search, DE441 error-spectrum FFT.

### Added

- **Native C backend** (`backend="c"`) — `libephemerides_spectral.{so,dll,dylib}` ships in the platform wheel under `_native/`; loaded via ctypes. Byte-for-byte parity with `backend="bip"`; **~1000× speedup** on the chunk loop. Transparent fallback to `"bip"` if the binary isn't present.
- **Spectral syzygy window search** — `bridge.find_syzygies(jd_lo, jd_hi, kind, threshold)` + CLI `find-syzygies`. HDC-native enumeration in closed form; replaces the v0.3.0 point-evaluation `eclipse --jd` for window queries.
- **DE441 error-spectrum FFT** — `research/de441_error_spectrum.py`. Empirical bridge to v0.4+'s first-principles α derivation; identifies which couplings empirically dominate the residual. Headline: Jupiter–Saturn ±45° at 9.56 yr (the missing 5:2 libration depth).

### Changed

- Build backend: hatchling → scikit-build-core for the platform wheel; pyproject-pure.toml retained for the Pyodide / WASM pure-Python fallback wheel.
- Wheel inventory: **15 platform wheels** (3 OS × 5 Python) + sdist + pure-Python wheel per release, up from 1 wheel + 1 sdist in v0.3.0.
- CI matrix shape (chess-spectral parity): per-PR runs only 4 always-on cells (3 OS × py3.12 + 1 min-Python cell). The full 15-cell `verify-wheels` matrix is opt-in via the `wheel-check` PR label or `workflow_dispatch`. Tag-push still runs the full matrix via `ephemerides-spectral-publish.yml`.

### Known limitations

- **Sdist standalone build broken when no toolchain is present.** The published sdist contains the C source tree and `CMakeLists.txt` at the parent of the python/ project (mirrored via `[tool.scikit-build] sdist.include = ["../CMakeLists.txt", "../c/**", ...]`), but `cmake.source-dir = ".."` resolves *outside* the unpacked tarball root, so `pip install ephemerides-spectral` from sdist fails with `CMake Error: source directory does not contain CMakeLists.txt`. The 15 platform wheels cover essentially all consumers; users on platforms without a wheel (Linux musllinux, exotic ARM) currently can't fall back to source build. Tracked as a v0.4 cleanup — likely co-locates the C tree under python/ so `source-dir = "."`.

See the [project CHANGELOG](../CHANGELOG.md) for the full v0.3.1 entry.

## [0.3.0] — 2026-05-04

Time scales beyond Earth + DE441 sweep + natural-resonance group.

### Added

- **Mars time** — `bridge.jd_to_mars_time` / `bridge.mars_time_to_jd` using Allison & McEwen 2000 formulas; CLI `time-mars`.
- **Lunar time** — `bridge.get_lunar_phase` returning mean synodic + sidereal age/phase; CLI `time-lunar`.
- **LTE440 awareness** — `bridge.list_lunar_kernels()` + `LUNAR_KERNELS = ("lte440",)` register Lin et al. 2025's Lunar Time Ephemeris on DE440 as a known kernel. Metadata only; no auto-download. CLI `lunar-kernels`.
- **Natural resonance group** — `bridge.get_natural_resonance_group()` returns the cyclic group derived from the Phase 9 resonance pairs themselves (LCM + CRT prime factorisation), distinct from the encoder's architectural `Z_{2^32}` modulus. CLI `natural-group`. On the v0.2.0 four-resonance set: `Z_30 = Z_2 × Z_3 × Z_5`.
- **DE441 full-epoch sweep** — `research/de441_sweep.py` + `figures/de441_full_sweep.md`. Per-body error vs DE441 ground truth across J2000 ± 14,000 yr. Documents the structural-limit signature of phenomenological α at multi-millennium horizons.

### Roadmap

- **LTC (Lunar Coordinated Time)** deferred to v0.4+; awaiting NASA + international-agency standardisation (target 2026–2028).
- **First-principles per-resonance α** stays in v0.4+; the DE441 sweep is the empirical motivation.

### Notes

- C port carries the version bump (`ES_VERSION_STRING = "0.3.0"`) but is otherwise unchanged from v0.2.0; the time-scale + natural-group surface is Python-side only.

See the [project CHANGELOG](../CHANGELOG.md) for the full v0.3.0 entry.

## [0.2.0] — 2026-05-04

Phase 9 coverage extension. The four wired resonances are now Jupiter–Saturn 5:2, Neptune–Pluto 3:2, Io–Europa 2:1 (Laplace pair 1), and Europa–Ganymede 2:1 (Laplace pair 2).

### Added

- **`research.laplacian.RESONANCES`** — single source of truth for the Phase 9 breathing-coupling pairs. The reference encoder, the BIP encoder, and the C codegen all walk this list.
- Three new entries beyond Jupiter–Saturn 5:2: Neptune–Pluto 3:2, Io–Europa 2:1, Europa–Ganymede 2:1.
- Static-coupling weights added for the three new pairs; v0.2.0 explicitly *guards* against zero-weight resonance entries (silent drift would be the failure mode).

### Changed

- Encoded phase residues for Io / Europa / Ganymede / Neptune / Pluto shift relative to v0.1.0 because their breathing modulation is now active. Earth's phase residue is unchanged. 0.0002 rad Earth phase floor at +20 yr against DE421 preserved.
- `bridge.list_couplings()` returns the same set of couplings (the table grew on the Phase 9 side, not the static-Laplacian side); `bridge.get_breathing_modulation()` returns non-zero modulation for any of the four wired pairs by default.

### Notes

- Modulation depth `α = 0.1` is global across all four resonances in v0.2.0; per-resonance depths are deferred to v0.3.x's first-principles derivation.
- C port mirrors the change: `c/src/es_laplacian.c` carries `es_n_couplings = 4`; byte-for-byte parity with the Python encoder verified across all 26 bodies at +20 yr.

See the [project CHANGELOG](../CHANGELOG.md) for the full v0.2.0 entry.

## [0.1.0] — 2026-05-04

First public release.

### Added

- Two encoder backends:
  - **`bip`** *(default)* — bit-serialised integer ALU over `Z_{2^32}`. 305× faster than the FPU reference; 256 KB state at D=65536; 0.0002 rad Earth phase error vs DE421 truth at +20 yr. No FPU in the hot path.
  - **`complex128`** — FPU complex128 reference encoder. Used for the algebraic identities (Syzygy operator, observer binding) and as a regression baseline.
- **Phase 9 breathing couplings.** Off-diagonal Laplacian weights modulate as `1 + α cos(n_a·φ_a − m_b·φ_b)` for the resonance pair `(n_a, m_b)`. Jupiter–Saturn 5:2 entry wired with `α = 0.1`. Implemented end-to-end on the integer ALU via a 1024-entry `int32` cosine LUT (Q1.14 amplitude, 4 KB). Formally a state-dependent (non-autonomous) graph Laplacian / adaptive Kuramoto-family network with phase-difference-dependent coupling; see the [project README](../python/README.md) and the research notebook §1.4 for the full mathematical positioning.
- **Pyodide-friendly bridge** (`ephemerides_spectral.bridge`). 9 methods returning `{ok: True/False}` JSON: `get_version`, `list_bodies`, `list_kernels`, `list_couplings`, `get_resolution`, `get_system_state`, `get_local_view`, `get_eclipse_probability`, `get_breathing_modulation`.
- **Rich CLI** (`ephemerides-spectral` console script). 9 subcommands matching the bridge 1:1; top-level `--version` and `--no-pretty`; per-subcommand `--help` epilogs with concrete examples.
- **`default_encode(jd, backend="bip", kernel="de441", D=65536)`** top-level shorthand for one-line encoding.
- **Q-format frequency discipline.** Angular frequencies stored as signed `int64` in residues/day with `MODULO = 2^32` residues per revolution. Pre-flight bounds check on `|delta_t| > 6.8e8 d` (~1.86 Myr) prevents int64 saturation before any math runs.
- **Scoped overflow trap.** `np.errstate(over='raise')` around the signed-int64 multiplies (where saturation would corrupt); `np.errstate(over='ignore')` plus warning filter around the `uint64` accumulator (where wraparound IS the cyclic-group reduction we want).
- **Codegen-stamped manifest.** `_data/manifest.json` carries SHA-256 sums + sizes for every research module shipped in `_research/`. Bridge `get_version()` returns the manifest so consumers can verify which research-tree commit they're running.

### Notes

- Default kernel is `de441` (3.3 GB). The loader gracefully falls back to `de421` for calibration if `de441` isn't on disk; pass `force_high_res=True` to disable the fallback.
- The integer cosine LUT is computed at import time using float `numpy.cos(...)` — the only float touchpoint in the package. After import, every encode-state path is pure integer arithmetic.
- Bridge & CLI parity is 1:1 — every subcommand has a bridge function and vice versa.

# The Ephemerides Mechanism: A High-Precision Resonant HDC Instrument

**Authors:** Gemini CLI (initial scaffolding); Steven Kirkland & Claude Opus (Phase 9 ALU-native)
**Date:** May 2026 (initial); finalised April 2026
**Status:** v0.13.6 (current). Living modular package. Headline state: 38-body roster (v0.5.0 — Galileans + classical Saturnians + Jovian inner regulars + Janus / Epimetheus); SPICE-free runtime (v0.5.0); **patch-shrinks-residual benchmark VINDICATED on planets** (v0.5.2 — Mars 99.2 %, Mercury 99.9 %, Jupiter 97.6 %, Saturn 96.0 %) and **on moons** (v0.5.5 — 5 of 6 targets 93–99 %); **C/Python parity** Tier 1 + Tier 2a + Tier 2b complete (v0.6.0 / v0.6.1 / v0.7.0 — every encoder-touching bridge method has a paired C path, zero `tier_skip` entries). **Sol Symphony Times** (v0.8.0 — Mercury / Venus / Mars / Jupiter / Saturn / Uranus / Neptune / Pluto / Sol); **ITN pathway find-tubes** (v0.8.1); **body-identity rename** Earth→Terra / Moon→Luna (v0.9.0 BREAKING) and **Sol Time naming overhaul** (v0.9.1 — Latin proper nouns for rocky bodies + Sun + Luna; adjective forms for gas/ice giants); **CLI `adaptive` synonym** for the breathing/Phase-9 LUT (v0.9.2 — matches Gross & Blasius adaptive-networks vocabulary). **STLT — Sol Terra-Luna Time** (v0.10.0 — first Sol Time member with a non-J2000 default epoch; Meton's 432 BCE summer solstice; see §7.4). **SPrT — Sol Proper Time** (v0.11.0 — gravitational + orbital-kinematic time dilation, applied transparently via `--proper` on every `time-*` subcommand; six published validations to 0.30 %; see §7.5). v0.11.1 (this notebook revision) backfills §7.4 and §7.5 + refreshes this Status banner. **JPL Power-of-Ten audit baseline** (v0.11.2 — 102 mechanically-detectable violations pinned in `c/JPL_AUDIT.md`; rule-by-rule fixes queued v0.13.4-v0.13.8). **Sol Kinematics** (v0.12.0 — per-body orbital state augmented onto every `time-*` via `--state`; Jupiter holds 61.5 % of total system L; outer planets hold 99.84 % of planet total L). **Sol Dynamics** (v0.13.0 — Newtonian forces + per-body energies + system aggregate via `--dynamics`; Earth-Sun force 3.54×10²² N validated to 0.01 %; total system energy −1.98×10³⁵ J, virial theorem holds to 0.5 %). **SPICE feature-gap audit** (v0.13.1 — three-column comparison; recommendation: skip the SPICE-API compat bridge; spawned v0.14.x backlog). **Pre-merge docs+parity hygiene check** (v0.13.3 — soft-warning GitHub Actions workflow; the very ratchet that would have caught the v0.10.0 / v0.11.0 notebook gaps as they shipped; closes `` `#98` ``). **JPL Power-of-Ten Rule 1 + Rule 3 fixes** (v0.13.4 — caller-supplied-scratch refactor of the HD pipeline; `goto` 5 → 0, `malloc`/`free` 29 → 0; ABI v5 → v6; user-facing bridge unchanged). **JPL Rule 4 fixes** (v0.13.5 — 4 long functions split via 10 new private static helpers along natural algorithm seams; pure refactor, no public surface change; encoder math byte-identical). **JPL Rule 5 fixes** (v0.13.6 — 88 assertions across 42 functions at 2.10/function avg; gated behind `<assert.h>` NDEBUG so production strips them; `test_rule_5_density_meets_2_per_function` flips SKIP → PASS). **Total mechanically-detectable violations: 102 → 0** — every Rule 1-5 violation in the v0.11.2 audit baseline cleared in three ships. **Live on PyPI**: `pip install ephemerides-spectral`.

> Living document. Sibling to:
> - [./antikythera_spectral_research_notebook.md](./antikythera_spectral_research_notebook.md) — **same-folder sibling.** Where ephemerides-spectral encodes the live JPL DE441 ephemeris, antikythera-spectral encodes the cyclic-group / Laplacian-eigenbasis structure of the ca. 150–60 BCE bronze mechanism. The two projects share the spectral / cyclic-group framing and the Pyodide bridge contract; they sit side-by-side because they are related enough to share the folder, but the bronze and DE441 are separate evidentiary objects so the notebooks are not consolidated.
> - [../chess-maths/chess_spectral_research_notebook.md](../chess-maths/chess_spectral_research_notebook.md) — §20.13–§20.17 explicitly aligns the chess `Z_{640}` phase-operator engine with this BIP design at the group-theoretic level; the cosine LUT pattern transfers between the projects.
> - [../addressing-maths/ADDRESSING_MATHS_RESEARCH_PLAN.md](../addressing-maths/ADDRESSING_MATHS_RESEARCH_PLAN.md) — the formal substrate (cyclic-group / Diophantine / packing).

## 0. Framing

The **Ephemerides Mechanism** (implemented in `ephemerides-spectral`) is the high-precision evolution of the Antikythera HDC paradigm. While the Antikythera mechanism was a masterpiece of bronze-age rational approximation, the Ephemerides Mechanism uses modern JPL ephemeris data to build a resonant HDC state vector ($D=65536$) that natively encodes celestial dynamics and their perturbations.


### 0.1 From Gears to Fibers

The Antikythera mechanism used coprime gear ratios to encode mean motion. In the Ephemeris Mechanism, these unperturbed orbits form the **diagonal content** of our system Laplacian. The real "innovation" of this project is the treatment of **gravitational perturbations** as **off-diagonal fiber couplings**.

Just as a chess capture redistributes field energy across piece-specific movement graphs, the mass of Jupiter dynamically "captures" or perturbs the phase of Mars. In our HDC encoding, these interactions are modeled as interaction hypervectors that fire based on body proximity and resonance, allowing the N-body problem to be computed through vector superposition and correlation.

## 1. Mathematical Architecture

### 1.1 Encoding Primitives
- **Unitary Binding:** We use circular complex bases (magnitude 1 per component) to ensure that all binding operations (observer shifts, temporal advances) are unitary rotations that preserve the total energy (Norm=1.0) of the hypervector.
- **Coprime Roll Binding:** Mirroring the `chess-spectral` (67, 7) pattern, we use coprime cyclic rolls to bind geographic coordinates (lat/lon) to the global system state.

### 1.2 Observer-Agnosticism
The system state $H_{sys}$ is barycentric. A topocentric "Local View" $V_{local}$ is extracted by binding a unitary Observer Operator $O$:
$$V_{local} = H_{sys} \otimes O(Body, \lambda, \phi)$$
This allows for instantaneous state extraction from any position on any supported celestial body.

### 1.3 Syzygy as a Spectral Event
Eclipses and conjunctions are not "searched" in the traditional sense; they are detected as alignment peaks with a pre-calculated **Syzygy Operator** $S$:
$$P_{syzygy} = \langle H_{sys}, S \rangle$$
This treats high-precision astronomical events as primary spectral signatures within the HDC space.

### 1.4 Mathematical positioning of the "breathing Laplacian"

The Phase-9 phrase **"breathing Laplacian"** is a project codename. This subsection names the formal mathematical objects so a reader from spectral graph theory, dynamical systems, or solid-state physics can place the construction in the literature their discipline already proves theorems about.

**The static piece.** The Phase-8 Laplacian is a Hermitian matrix on the body-interaction graph $G = (V, E)$ with $|V| = 26$ bodies:

$$L_{\text{LTI}} = L_{\text{trunk}} + L_{\text{PN}} + L_{\text{static}}$$

where $L_{\text{trunk}}$ is the diagonal of mean motions $\omega_i = 2\pi / P_i$, $L_{\text{PN}}$ is the Mercury post-Newtonian correction, and $L_{\text{static}}$ is the symmetric off-diagonal of gravitational fiber weights. Evolution is the Schrödinger-like flow $\psi(t) = e^{-i L_{\text{LTI}} t} \psi(0)$ on the cyclic-group manifold.

**The dynamic piece.** Phase 9 promotes the off-diagonal weights to functions of the current phase state:

$$W_{ij}(\phi) = W_{ij}^{(0)} \cdot \bigl(1 + \alpha \cos(n_{ij} \phi_i - m_{ij} \phi_j)\bigr)$$

so the Laplacian itself becomes state-dependent: $L = L(\phi(t))$. The flow is no longer a single matrix exponential — it is integrated chunk-wise in 30-day steps with $L$ recomputed each chunk.

**What this is, in three vocabularies.**

* **Spectral graph theory / linear algebra.** A **state-dependent (non-autonomous) graph Laplacian.** The instantaneous spectrum of $L(\phi(t))$ defines the system's normal modes at each instant; the dynamics evolves through these modes as $\phi$ re-organises. This is the "vibrating-lattice" intuition formalised — at every instant we have a bona-fide lattice with bona-fide phonon-like modes; what changes is the Hamiltonian itself.

* **Dynamical systems / synchronisation theory.** An **adaptive Kuramoto-family network with phase-difference-dependent (PDDP) coupling.** Standard Kuramoto fixes $K_{ij}$ and varies $\phi$; we vary both, with $K_{ij}$ a smooth function of $(\phi_i, \phi_j)$. The literature calls this *adaptive coupling* or *plastic coupling*, with a substantial body of synchronisation-resilience results we can lean on (Berner et al. on adaptive phase oscillators; Sakaguchi-style PDDP rules).

* **Physics framing.** A **resonance-modulated coupling** of phase oscillators, structurally analogous to the **Discrete Nonlinear Schrödinger / Gross-Pitaevskii equation on a graph** in the limit where amplitudes are pinned to unit norm and only phases evolve. The coupling kernel $\cos(n\phi_i - m\phi_j)$ is the standard $n{:}m$-resonance lobe; that we model the J–S 5:2 with $\alpha = 0.1$ is a phenomenological choice, not derived from a Lagrangian. A first-principles derivation would route through Hamilton's equations on the Delaunay variables — out of scope for v0.1.0; flagged as future work.

* **Discrete differential geometry / curvature in motion.** The cleanest single-phrase reading is **state-dependent discrete Ricci curvature** — the breathing Laplacian *is* curvature in motion. A weighted graph carries a discrete analog of Ricci curvature (Forman-Ricci $\mathrm{Ric}_F$, Ollivier-Ricci $\kappa_{OR}$, or Bakry-Émery's $\Gamma_2$ / curvature-dimension condition $\mathrm{CD}(\kappa, \infty)$); each is a function of the edge weights $W_{ij}$ and the edge-incidence pattern. When edge weights are state-dependent — $W_{ij}(\phi) = W_{ij}^{(0)}(1 + \alpha \cos(n_a\phi_a - m_b\phi_b))$ — the discrete Ricci curvature on each resonance edge becomes a periodic function of the phase state. The spectral identity is the Bochner-Lichnerowicz analog: the Laplacian's spectrum is *bounded below by curvature* via $\lambda_2 \geq \kappa$ (CD($\kappa$, $\infty$) on a graph yields the same eigenvalue gap inequality as on a Riemannian manifold). What "breathes" in our codename is exactly this curvature: it inhales and exhales over the resonant-phase angle, and the spectral gap $\lambda_2$ tracks it.

  This reading also names the v0.5.x roadmap target precisely. The static $L_{\text{trunk}} + L_{\text{PN}} + L_{\text{static}}$ piece sets a **fixed baseline curvature** — the encoder's "metric." The Phase-9 modulation adds **a curvature flow that is forced, not relaxed**: where Hamilton-style discrete Ricci flow would evolve the metric to flatten the curvature toward a smooth limit, our case is the opposite — the curvature is *forced* to oscillate by the phase-coupling rule. It is "phase-locked Ricci flow" — the geometry doesn't relax but pulses with the natural resonance frequencies of the bronze antikythera's gear ratios. The diagnosed-fiber overlay (§8) and the LS-fit catalog (§9) are then *empirical curvature corrections*: each catalog patch adds a periodic delta to one body's residual that, in the curvature reading, nudges the local Ricci curvature on the patched edge into agreement with what the actual ephemeris demands.

**Why "breathing" is metaphor, not vocabulary.** The codename captures the rhythm — coupling strengths inhale and exhale with the resonant-phase angle — but it does not connect to the literature's existing theorems. **State-dependent graph Laplacian** is the name to grep for in spectral-graph papers; **adaptive Kuramoto network** is the name to grep for in synchronisation papers; **state-dependent discrete Ricci curvature** (or "curvature in motion") is the name to grep for in discrete differential geometry / Bakry-Émery / Ollivier–Ricci papers; **vibrating lattice** captures the right *intuition* (phonon-like instantaneous spectrum) but is a 2nd-order Newtonian framing, whereas our flow is 1st-order phase rotation. We use "breathing" in headings and section labels for project continuity, and the precise vocabulary in prose so future readers can find their way out of our codename and into the canonical literature.

**What about a true vibrating-lattice formulation?** The Phase-8 propagator $e^{-iLt}$ on the cyclic-group manifold is *isomorphic* to the linear-phonon propagator on a 1D ring lattice in the eigenmode basis: each mode rotates at its eigenvalue. The Phase-9 modification then plays the role of *phonon–phonon scattering* (anharmonic coupling). If we ever want to study energy transfer between modes — Fermi-Pasta-Ulam-Tsingou-style equipartition, soliton-on-a-ring, etc. — that is the framing to import. v0.1.0 stops short of any nonlinear-mode bookkeeping; we evolve in the body-index basis, not the eigenmode basis.

## 2. Implementation & Validation

### 2.1 The ephemerides-spectral Package
The project is scaffolded as a standalone PyPI-ready package with:
- `bridge.py`: Pyodide-JSON contract for web frontend integration.
- `_research/`: Deterministic snapshots of the core instrument logic.
- `codegen/`: Automatic manifest and data freezing infrastructure.
### 2.2 Results
The prototype successfully:
- Extracts true ecliptic longitude from JPL kernels.
- Maintains hypervector integrity (Norm=1.0) through frame shifts.
- Detects proximity-based gravitational interaction terms.
- **RBS-HDC Advancement:** Verified a 305× speedup using FPU-less integer arithmetic.
- **Structural Limit Identified:** Confirmed a ~0.0002 rad error floor (Phase 8) due to the static LTI Laplacian assumption and Newtonian mean-motion constraints.
- **Phase 9 Breathing Couplings:** Replaced the static off-diagonal weights with phase-dependent modulation via an integer cosine LUT (1024 × `int32`, Q1.14). The Jupiter–Saturn 5:2 resonance term is now implemented end-to-end without leaving the integer ALU.
- **Fixed-Point Discipline:** All angular frequencies are stored as signed `int64` in residues/day (Q-format with `MODULO = 2^32` residues per revolution); the Q-format underflow guard, pre-flight bounds check, and scoped overflow trap are documented in `resonant_bit_serialized_hdc_evaluation.md` §8.3–§8.4.
- **Cross-pollination:** chess-spectral §20.13–§20.17 explicitly aligns the chess `Z_{640}` phase-operator engine with this BIP design at the group-theoretic level; the cosine LUT pattern transfers between the projects (chess pays an explicit `% 640` per op, ephemerides gets cyclic-group reduction free as `uint32` overflow).

## 3. Future Tracks

### Shipped since this section was first written

- ~~**Download DE441:** Scale the validation suite to the full 3.3 GB JPL kernel.~~ — **shipped v0.3.0**. Full ±14,000 yr sweep against DE441 ground truth ([`figures/de441_full_sweep.md`](figures/de441_full_sweep.md)).
- ~~**Phase 9 Coverage:** Extend breathing couplings beyond the J–S 5:2 term.~~ — **shipped v0.2.0** (Neptune–Pluto 3:2 + Io–Europa 2:1 + Europa–Ganymede 2:1) and **v0.5.0** (Mimas–Tethys 4:2 Cassini Division + Enceladus–Dione 2:1 + Titan–Hyperion 4:3). Seven resonance entries total.
- ~~**Spectral syzygy window search.**~~ — **shipped v0.3.1** as `bridge.find_syzygies` + CLI `find-syzygies`. ~1000× faster than the v0.3.0 point-evaluation `eclipse --jd` for window queries; uses the natural cyclic-group decomposition (synodic + draconic month + Saros) to enumerate candidates in closed form.
- ~~**DE441 error-spectrum FFT diagnostic.**~~ — **shipped v0.3.1** as `research/de441_error_spectrum.py`. Per-body FFT of the DE441-truth residual identifies smoking-gun missing-coupling signals; surfaced the Jupiter–Saturn 9.56 yr ±45° peak that motivates the diagnosed-fiber catalog.
- ~~**Native C backend.**~~ — **shipped v0.3.1** (cibuildwheel platform wheels, `backend="c"`, ~1000× speedup vs Python BIP, byte-exact parity).
- ~~**Diagnosed-fiber runtime overlay (Python side).**~~ — **shipped v0.4.0**. See §8 below for the architecture.
- ~~**C-side overlay (ABI v2).**~~ — **shipped v0.4.1**. Native backend now applies the overlay; cross-backend byte-exact parity with patches active.
- ~~**SPICE-free runtime.**~~ — **shipped v0.5.0**. Codegen bakes initial phases into `_data/initial_phases.json`; `pip install` works out of the box.
- ~~**Patch-shrinks-residual benchmark.**~~ — **shipped v0.5.1 (PARTIAL) → v0.5.2 (VINDICATED)**. See §9 below for the methodology + result.

### Still to come

- **First-Principles Phase-9 Derivation:** v0.1.0's $\alpha = 0.1$ J–S breathing depth is phenomenological. Deriving the modulation depth from a Hamilton/Delaunay-variable Lagrangian (with Lie-series perturbation theory around the 5:2 resonance) would replace the placeholder with a first-principles value. Connects to the adaptive-Kuramoto literature on derived-from-physics PDDP rules (cf. §1.4). v0.5.2's LS-fit catalog (§9) is the *empirical* analog — Fourier-correction patches that first-principles α should ultimately make redundant for the bodies inside the resonance set.
- **DE441 vs DE442 spectral error signature** *(research experiment)*: build two BIP instruments calibrated *separately* from DE441 and DE442; encode the same JD on both; project per-body residue deltas onto the Laplacian eigenbasis. Hypothesis: DE442's corrections to DE441 occupy a coherent eigenmode subspace — the spectral signature of the kernel update. If we can find a correlate, we can **predict** where ephemeris error correction is structurally needed without having the corrected kernel in hand. The natural-coprime decomposition from §6 would be the basis for that prediction.
- **Multi-Millennium Sweep against breathing couplings active:** Re-derive the historical anchors for the Metonic and Saros cycles against the full DE441 sweep (already done at the planet level; multi-millennium re-derivation with the v0.5.x resonance-corrected encoder is the follow-up).
- **CORDIC Topocentric Rendering:** The cosine LUT is the first half of a CORDIC observer-binding pipeline; the rotation half can subsume the topocentric `lat/lon` bind.
- **Resonant Bit-Serialized Hardware:** Port the BIP integer-only evolution to bit-serial hardware simulations (Verilog/SystemC). The cosine LUT becomes block RAM; the `omega * step` multiply becomes a fixed-precision multiplier.
- ~~**Moon residual root-cause investigation** *(v0.5.x)*~~: **shipped v0.5.3 → v0.5.5** as the three-phase moon programme. Phase A (diagnostic) ruled out the frame-mismatch hypothesis. Phase B (v0.5.3) fixed period truncation; 13 of 17 moons dropped 30-1450× in RMS. Phase C (v0.5.5) authored 5 LS-fit catalog patches at 93-99% shrinkage. Four moons remain physics-specific follow-ups (metis / thebe / rhea / phoebe).
- ~~**C/Python parity Tier 1**~~ *(v0.6.0)*: **shipped.** `find_syzygies` + `get_breathing_modulation` now have C twins; ABI v3. The `tests/test_parity_smoke.py` PARITY_TARGETS table is the durable SSOT for what's at parity vs what's pending.
- **C/Python parity Tier 2** *(v0.7.0)*: `get_local_view` and `get_eclipse_probability` still operate on the FPU complex128 hyperdimensional state. Lifting the C runtime to carry HD state via channel-basis emission at codegen time is the architectural change; the parity smoke test's two `tier2_skip` entries flip to `parity` when this lands.
- **LTC (Lunar Coordinated Time)** *(v0.6.x or later)*: Pending NASA + international space-agency standardisation (target 2026–2028 per April 2024 White House directive). LTE440 (Lin et al. 2025) ships the underlying SPICE-format conversion ephemeris with 0.15 ns accuracy through 2050; ephemerides-spectral gains an `LTC` namespace in the bridge mirroring `MarsTime` once the LTC epoch + day-length convention are formalised.
- **Multi-component or coupled-T-H Hyperion patch** *(v0.6.x)*: Hyperion's chaotic rotation produces multi-peak quasiperiodic residual that single-sinusoid LS-fit hits at 75.2% (vs the 80% catalog gate). Two paths: (1) multi-component patch — one entry expressed as a list of `(period, amplitude, phase)` sinusoids; the v0.5.2 multi-bin idea revived for chaos rather than bin leakage. (2) coupled `titan-hyperion-4to3-coupled-v2` patch — v0.5.0 wired the resonance into `RESONANCES` but never calibrated the coupling strength; same v0.5.2 J-S template, different bodies.

## 4. Release History

* **v0.13.6** — 2026-05-05. **JPL Power-of-Ten Rule 5 fixes — assertion density at 2/function average.** Third code-quality patch in the v0.13.4-v0.13.8 rule-fix sequence. **88 assertions added across 42 functions = 2.10/function average** (target ≥2.0). Per Holzmann's Power-of-Ten paper, three categories applied: pre-conditions on parameters (post-validation `assert(ptr != NULL)`, `assert(idx < N_BODIES)`, `assert(isfinite(input))`), post-conditions on results (`assert(magnitude >= 0)`, `assert(phase < 2π)`, `assert(state advanced)`), and invariants (`assert(D > 0)`, `assert(n_patches <= ES_MAX_PATCHES)`, `assert(constants positive)`). All assertions use standard `<assert.h>` and are no-ops under `-DNDEBUG` — assertions are a development-time documentation tool that doubles as static-analysis precondition spec; production builds strip them entirely (zero runtime cost). The previously-skipped `test_rule_5_density_meets_2_per_function` ratchet test now **PASSES**; `PIN_RULE_5_ASSERTIONS` ratcheted UP 0 → 88. **Pure additive instrumentation, no public API/ABI change** — encoder math byte-identical (parity smoke green). **Total mechanically-detectable violations: 102 → 0** — every Rule 1-5 violation in the v0.11.2 audit baseline cleared in three ships (v0.13.4 + v0.13.5 + v0.13.6). Remaining JPL roadmap: Rule 10 (cross-platform pedantic-build matrix, v0.13.7), Rules 6+7 (manual scope + return-value audits, v0.13.8). 250 tests pass, 4 skipped (was 5; Rule 5 density skip is gone). Live: <https://pypi.org/project/ephemerides-spectral/0.13.6/>.
* **v0.13.5** — 2026-05-05. **JPL Power-of-Ten Rule 4 fixes — long-function splits.** Second code-quality patch in the v0.13.4-v0.13.8 rule-fix sequence. The 4 audit-baseline offenders (`es_encode_state` 109, `es_find_syzygies` 99, `es_bind_observer` 78, `es_get_eclipse_probability` 65) split into ≤60-line JPL-compliant drivers via **10 new private static helpers** along natural algorithm seams. Encoder side: `apply_one_chunk` (chunk-loop body) + `apply_subchunk_remainder` (banker's-round leftover step). Parity side: `select_syzygy_targets` + `score_syzygy_event` + `validate_syzygy_args` + `emit_syzygy_event`. HD-pipeline side: `observer_coord_shift` + `apply_observer_bind` + `build_syzygy_operator` + `complex64_vdot_magnitude`. `PIN_RULE_4_LONG_FUNCTIONS` drops 4 → **0**; `PIN_RULE_5_TOTAL_FUNCS` ratchets UP 32 → 42 (Rule 5 in v0.13.6 needs the new inventory). **Pure refactor, no public surface change** — public entry points keep their v0.13.4 signatures; encoder math byte-identical (parity smoke green). **Total mechanically-detectable violations: 102 → 64** (37% of audit baseline cleared across v0.13.4 + v0.13.5). Remaining: Rule 5 (v0.13.6), Rule 10 (v0.13.7), Rules 6+7 (v0.13.8). 250 tests pass, 5 skipped. Live: <https://pypi.org/project/ephemerides-spectral/0.13.5/>.
* **v0.13.4** — 2026-05-05. **JPL Power-of-Ten Rule 1 + Rule 3 fixes — first code-quality patch in the v0.13.4-v0.13.8 rule-fix sequence.** Caller-supplied-scratch refactor of `c/src/es_hd_state.c` eliminates two violation classes in a single pass. `goto` 5 → **0** (Rule 1); `malloc`/`free` 29 → **0** (Rule 3); `<stdlib.h>` no longer included by the C library. The HD pipeline's three entry points (`es_encode_state_hd`, `es_bind_observer`, `es_get_eclipse_probability`) gain caller-supplied scratch-buffer parameters; the Python ctypes shim allocates them alongside the existing `out_state` (no observable heap-pressure change — Python was already heap-allocating the output buffer). **ABI v5 → v6**, mechanical wire-format only — encoder math byte-identical to v0.13.3, verified by `tests/test_parity_smoke.py` pinning both backends to within float-ULP. The combined fix is the natural unit: every `malloc` was paired with a `free` inside a `goto out:` block, so removing one removed the reason for the other. **Total mechanically-detectable violations: 102 → 68** (33% of v0.11.2 audit baseline cleared in one ship). Remaining: Rule 4 long functions (v0.13.5), Rule 5 assertion density (v0.13.6), Rule 10 pedantic-build matrix (v0.13.7), Rules 6+7 manual audits (v0.13.8). **User-facing Python bridge surface unchanged** — same call sites, same return shapes, same numpy dtypes. 250 tests pass, 5 skipped. Live: <https://pypi.org/project/ephemerides-spectral/0.13.4/>.
* **v0.13.3** — 2026-05-05. **Pre-merge docs+parity hygiene check (soft-warning GitHub Actions workflow).** Closes task `` `#98` `` (consolidated; absorbs `` `#87` `` + `` `#88` ``). New `.github/workflows/ephemerides-spectral-docs-check.yml` runs on every PR touching the package; classifies code-side touches (version bumps; `bridge.py`; `cli.py`; `_research/*.py`; `c/src/*.c` / `c/include/*.h`) against the five PyPI-facing docs files (`python/README.md`, `python/CHANGELOG.md`, `CHANGELOG.md`, `ROADMAP.md`, `ephemerides_spectral_research_notebook.md`); posts (or updates in place via `peter-evans/find-comment` + `peter-evans/create-or-update-comment`) one PR comment summarising the gap. **Soft-warning, never fails the build** — the existing pytest freshness ratchet (`test_native_version_string_matches`, `test_parity_smoke::PARITY_TARGETS`, `test_readme_freshness`, `test_jpl_audit`) hard-fails on the highest-value drift modes; this workflow surfaces the *next tier* — prose-and-narrative drift that humans should review but a regex can't authoritatively adjudicate. Forcing CHANGELOG bumps on every whitespace diff would burn patience and breed filler bullets. Opt-out via `[skip-docs-check]` in PR body. Concurrency `cancel-in-progress: true` keyed by workflow + ref absorbs the `opened`+`labeled` double-fire pattern documented in `ephemerides-spectral-ci.yml`. CI-only addition; 250 tests pass, 5 skipped. Live: <https://pypi.org/project/ephemerides-spectral/0.13.3/>.
* **v0.13.2** — 2026-05-05. **Quick-win housekeeping: gitignore `_native/`; renumber JPL rule-fix roadmap to v0.13.4-v0.13.8.** Patch-level repo-config + docs only; no API / encoder / ABI / test changes. Adds `python/ephemerides_spectral/_native/` to the top-level `.gitignore` (`` `#85` ``); `_native/` holds compiled DLL/SO files that rebuild on every `cmake --build` and shouldn't be source-controlled. Patches `c/JPL_AUDIT.md`'s roadmap section: original v0.11.3-v0.11.7 numbering is obsolete since the project moved past v0.11.x; the rule-fix patches are renumbered to **v0.13.4 (Rule 1+3)**, **v0.13.5 (Rule 4)**, **v0.13.6 (Rule 5)**, **v0.13.7 (Rule 10)**, **v0.13.8 (Rules 6+7)**. v0.13.3 reserved for `` `#98` `` (consolidated docs+parity hygiene check; absorbs `` `#87` `` + `` `#88` ``). 248 tests pass, 5 skipped. Live: <https://pypi.org/project/ephemerides-spectral/0.13.2/>.
* **v0.11.1** — 2026-05-05. **Research notebook hygiene: backfill §7.4 (STLT) and §7.5 (SPrT) sections that landed without their notebook coverage in v0.10.0 and v0.11.0; refresh the Status banner; add v0.9.2 → v0.11.1 entries to Release History.** Documentation-only release; no API surface change. Triggered by the user noticing that v0.10.0 and v0.11.0 shipped without their notebook sections — the freshness checks (`tests/test_readme_freshness.py`) cover the README but not the notebook. v0.11.1 closes that specific gap; task #98 captures the broader follow-on (a soft "docs probably need updating" warning on PRs that touch code without touching docs). 171 active tests pass; identical to v0.11.0 (no test changes). Live: <https://pypi.org/project/ephemerides-spectral/0.11.1/>.
* **v0.11.0** — 2026-05-05. **Sol Proper Time (SPrT) — gravitational + orbital-kinematic time dilation, applied transparently via `--proper` on every `time-*` subcommand.** Per-body diagonal-fiber GR correction extending Mercury's existing 43″/century PN diagonal to all 38 bodies. New `bridge.get_proper_time_rate(body, ...)` + `bridge.compare_proper_times(a, b, ...)` primitives + standalone `time-proper` CLI subcommand. Same physics, applied transparently — the user's framing was *"gravitational time dilation fiber so users don't even need to know anything extra had to happen in the back end."* Six published values (Earth GR / Sun GR / Mars GR / Pluto GR / Earth orbital kinematic / Mars-vs-Earth GR-only difference) reproduced to within 0.30 %. **Curiosity rover 0.0175 s/Earth-year Mars-Terra figure verified inline**; combined-effect (GR + orbital kinematic) is 0.0710 s/yr. Two-implementation discipline (Phase A independent script + Phase B canonical primitive, validated against the same six numbers) is the project's house pattern now. New `surface_radius_km` per body in `bodies.py`. **See §7.5.** 171 active tests pass. Live: <https://pypi.org/project/ephemerides-spectral/0.11.0/>.
* **v0.10.0** — 2026-05-05. **Sol Terra-Luna Time (STLT) — system clock for the Terra-Luna pair, with Meton's 432 BCE summer solstice as the default epoch.** First Sol Time member with a non-J2000 default anchor. New `bridge.jd_to_sol_terra_luna_time(jd_tdb, *, epoch="meton")` + inverse; new CLI `time-terra-luna` with `--epoch {meton, antikythera, hipparchus, mardokempad, j2000}`. The "combo" candidate test (the user's suggestion to score the Hipparchus-Babylonian eclipse-archive midpoint as a derived candidate) **independently confirms the choice**: the midpoint lands within +240 days of Meton's solstice — same year, eight months later. Greek mathematical astronomy's eclipse archive is centred on Meton's lifetime. Phase A research script + markdown report at `figures/lunar_epoch_candidates.md`. Latent bug fixed in passing: `find_syzygies(backend="auto")` was rejected by `_validate_backend` (same class as v0.9.2's `get_breathing_modulation` fix). House-epoch design choice; not a claim to be NASA's eventual LCT. **See §7.4.** 143 tests pass. Live: <https://pypi.org/project/ephemerides-spectral/0.10.0/>.
* **v0.9.3** — 2026-05-05. **PyPI-facing README staleness sweep + CI freshness check.** Status section refreshed (8 versions of accumulated drift — block ended at v0.6.1, now runs through v0.9.3). Roadmap section pruned of items that have shipped (Tier 2b, Sol Venusian/Mercurian Time, ITN pathway / `find-tubes`); reorganised to lead with genuinely-still-ahead work. Leftover earth-body CLI examples corrected to `terra`. **Drift-prevention:** new `tests/test_readme_freshness.py` enforces three invariants — every CHANGELOG version must appear in the README Status section; the `Status: vX.Y.Z` banner under the H1 must equal `__version__`; every CLI body-name flag in an example must reference a name in `SUPPORTED_BODIES`. Same modular discipline as `test_native_version_string_matches_package_version` and `test_parity_smoke.py::PARITY_TARGETS` — enumerate the truth, fail on drift. Docs-only release; no API or encoder changes. 124 tests pass. Live: <https://pypi.org/project/ephemerides-spectral/0.9.3/>.
* **v0.9.2** — 2026-05-05. **CLI: `adaptive` is the primary subcommand for state-dependent coupling modulation; `breathing` is preserved as a hidden synonym (`help=argparse.SUPPRESS`).** What we call "breathing couplings" in the visual / informal register is, in mainstream network-science vocabulary, an **adaptive** coupling — a state-dependent (non-autonomous) graph Laplacian whose edge weights co-evolve with the system's own resonant phases (Gross & Blasius 2008, "Adaptive coevolutionary networks"; the adaptive Kuramoto family). Both names work; new users discover `adaptive` via `--help`, visual-metaphor users keep typing `breathing`. Latent bug fixed in passing: `bridge.get_breathing_modulation(backend="auto")` was rejected by `_validate_backend` (the sentinel isn't in `SUPPORTED_BACKENDS`); resolved before validation now, matching the docstring contract. Help-text cleanup: leftover `--body earth` / `--departure earth` examples corrected to `terra` after v0.9.0/v0.9.1. 118 tests pass. Live: <https://pypi.org/project/ephemerides-spectral/0.9.2/>.
* **v0.9.1** — 2026-05-05. **Sol Time naming convention overhaul + Sol Terra Time + Sol Luna Time.** Direct Latin proper noun (Mercury, Venus, Pluto, Terra, Luna, Sol) for rocky bodies + Sun + Luna; established adjective form (Jovian, Saturnian, Uranian, Neptunian) for gas/ice giants. **Renames (BREAKING):** `jd_to_sol_mercurian_time` → `jd_to_sol_mercury_time` (and `MercurianTime` → `MercuryTime`); same for Venus and Pluto. **New (additive):** Sol Terra Time (STT, Terra's surface clock; sidereal 23h 56m 4s, solar 24h) and Sol Luna Time (SLT, Luna's tidally-locked surface clock; sidereal=orbital=27.32 d, solar=synodic=29.53 d). SLT is **distinct from** Sol Lunar Time (`get_lunar_phase`) — same body, different observer frame. Each bridge return's `epoch:` block carries an `abbreviation` field (SMeT, SVT, STT, SLT, SUT, SNT, SJT, SST, SPT, SSoT). The naming framing: *"Returning to the giants whose shoulders we stand on. We've always had a lunar orbit and a lunar eclipse. We've all had terrain and terrestrial animals. We're just putting the books back in their dewey decimal spot."* 111 active tests pass. Live: <https://pypi.org/project/ephemerides-spectral/0.9.1/>.
* **v0.9.0** — 2026-05-05. **Body identity rename: `moon` → `luna`, `earth` → `terra` (BREAKING CHANGE).** Latin proper nouns for the body-identity strings (`BODIES["luna"]`, `BODIES["terra"]`); the generic English words (`moon` for any natural satellite, `earth` for soil/ground) are no longer privileged as the proper noun for specific bodies. JPL/skyfield kernel boundary handled via `EphemerisBundle.lookup()` which translates internal terra/luna → JPL EARTH/MOON. Encoder hot path byte-identical to v0.8.1; only string conventions changed. v0.9.1 ships the matching Sol Time naming overhaul (Sol Mercurian → Sol Mercury, Sol Venusian → Sol Venus, Sol Plutonian → Sol Pluto; new Sol Terra Time + Sol Luna Time; gas/ice giant adjective forms kept). 107 active tests pass; 5 skipped (4 cibuildwheel-only + 1 `tier1_skip` `find_itn_pathways`). Live: <https://pypi.org/project/ephemerides-spectral/0.9.0/>.
* **v0.8.1** — 2026-05-05. **ITN pathway / Lagrange-tube query — `find-tubes` first cut.** "Surfing the perturbations": closed-form Hohmann transfer-window enumeration mirroring v0.3.1's `find-syzygies` discipline. Pure-Python (the C twin lands in a follow-up minor with ABI bump). Earth → Mars sanity at threshold 0.02 over J2000 + 50 yr returns 23 windows; each carries 258.87-d transfer time and 5.594 km/s Δv — matching textbook Hohmann to 0.01% / 0.1%. The `gateway_lp` field is a placeholder for future CR3BP L1/L2 gateway designation; `transfer_kind = "hohmann"` reserves room for low-energy / heteroclinic-tube candidates as future versions add the manifold computation. References: Koon-Lo-Marsden-Ross 2011; Lo's Genesis trajectory work; Conley 1968. Live: <https://pypi.org/project/ephemerides-spectral/0.8.1/>.
* **v0.8.0** — 2026-05-05. **Sol Symphony Times: 7 new planetary/stellar time systems.** Venus, Mercury, Pluto, Sol (the Sun!), Jupiter, Saturn, Neptune join Mars / Lunar / Uranian as Sol Time members. Each ships with sidereal + (where applicable) solar day phase + orbital phase + epoch metadata; quirks honored: **Mercury 3:2 spin-orbit resonance** (solar day = 2 Mercury-years exactly), **Venus retrograde with sidereal day longer than year** (243 vs 224.7 d), **Sol differential rotation** (Carrington Rotation Number; 25.38 d at ~16° latitude), **Saturn Cassini ring-seismology revision** (Mankovich 2019, supersedes Voyager). 12 new bridge methods, 6 new CLI subcommands. Naming hierarchy convention for future moon ports: `Sol <Parent>-<Body> Time` (e.g., Sol Pluto-Charon Time, Sol Jupiter-Io Time, Sol Earth-Moon Time). ABI unchanged — pure-Python time-scale formulas. Subagent confirmed gas-giant rotation periods (Jupiter System III, Saturn ring seismology) are derived independently of moon orbital data, so Sol Jovian and Sol Saturnian Time ship without needing their moons. 102 active tests pass; 4 skipped (cibuildwheel-only). Live: <https://pypi.org/project/ephemerides-spectral/0.8.0/>.
* **v0.7.0** — 2026-05-05. **C/Python parity Tier 2b — full HD pipeline in C (ABI v5).** Three new C entry points: `es_encode_state_hd` (BIP-encode then lift to D-dim hypervector via channel bases), `es_bind_observer` (topocentric HDC algebra; pure HDC, no SPICE), `es_get_eclipse_probability` (syzygy projection). Bridge dispatches `get_local_view` and `get_eclipse_probability` on `backend={"auto","bip","c","fpu-ref"}`. **Parity smoke flips both `tier2_skip` entries to `parity`** — every encoder-touching bridge method has a paired C path; zero `tier_skip` entries remain. New `_research/bip_hd_lift.py` Python helpers + `tests/test_hd_parity.py`. Behaviour change: default `get_local_view`/`get_eclipse_probability` switches from FPU matrix-expm to BIP-and-lift; `backend="fpu-ref"` opts back into pre-v0.7.0 behaviour. 84 active tests pass; 4 skipped (cibuildwheel-only). Live: <https://pypi.org/project/ephemerides-spectral/0.7.0/>.
* **v0.6.1** — 2026-05-05. **C/Python parity Tier 2a foundation (ABI v4).** Channel-basis emission in C with byte-identical agreement to the Python side. New portable splitmix64 PRNG (replaces numpy's PCG64-seeded basis init for cross-language reproducibility); new `es_channel_basis(seed, out, D)` entry point + `es_complex64_t` typedef. The `_research/portable_prng.py` module mirrors the C-side splitmix64 byte-for-byte. New `tests/test_channel_basis_parity.py` pins byte-identical complex64[D] output between Py + C across all 38 body seeds and D ∈ {1024, 65536}. **No bridge surface change; no encoder behaviour change.** This is the foundation for v0.7.0's HD encode + observer-bind + eclipse projection. See `TIER2_DESIGN.md` for the three-phase plan. Live: <https://pypi.org/project/ephemerides-spectral/0.6.1/>.
* **v0.6.0** — 2026-05-05. **C/Python parity Tier 1 + always-on parity smoke test (ABI v3).** Two encoder-touching bridge methods that were previously Python-only now have C twins: `get_breathing_modulation` (resonant-pair phase + integer-LUT modulation factor at one JD) and `find_syzygies` (synodic + draconic month enumeration; pure modular arithmetic, mirrors `_research/syzygy_window.py` 1:1). Both bridge methods accept `backend={"auto","bip","c"}`. **The durable parity discipline:** new `tests/test_parity_smoke.py` enumerates every public `bridge.*` function in a `PARITY_TARGETS` table classified as `parity` / `python_only` / `tier1_skip` / `tier2_skip`. Two drift-detection sub-tests force the table to stay current — adding a new bridge method without a parity classification fails CI. ABI v2 → v3 (additive — encoder hot path byte-identical to v0.5.5). Tier 2 (`get_local_view`, `get_eclipse_probability` over the FPU complex128 D=65536 hyperdimensional state) still pending — flagged as `tier2_skip` in the smoke test, queued for v0.7.0. Live: <https://pypi.org/project/ephemerides-spectral/0.6.0/>.
* **v0.5.5** — 2026-05-05. **Moon catalog patches — Phase C of the v0.5.x moon programme.** Five LS-fit-vindicated moon patches join `CATALOG_V2`: `dione-1.06yr-diagonal-v2` (98.2%), `tethys-0.38yr-diagonal-v2` (93.8%), `enceladus-0.39yr-diagonal-v2` (98.9%), `titan-0.69yr-diagonal-v2` (95.5%), `iapetus-0.22yr-diagonal-v2` (98.6%). The v0.5.2 LS-fit methodology is now vindicated **twice on independent body sets**: planets at 96-99%, moons at 93-99%; same bin-leakage signature both times (LS-fit amps 2-3× the FFT-bin baselines). Hyperion's `0.20yr-diagonal` patch lands at 75.2% — **chaos as the methodological ceiling**: Hyperion's spectrum has multi-peak quasiperiodic structure (rank 1 at 5.44° + rank 3 at 1.39° + rank 5 at 1.30°, all within ~1d of 72.4d) that single-sinusoid LS-fit can't fully capture. Queued as a multi-component or coupled Titan-Hyperion 4:3 follow-up. New scripts: `author_moon_patches.py` + `verify_moon_patches.py`; `de441_moon_spectrum.gather_moon_residuals` factored out for reuse. See [`figures/moon_catalog_patches_v0.5.5.md`](figures/moon_catalog_patches_v0.5.5.md). Live: <https://pypi.org/project/ephemerides-spectral/0.5.5/>.
* **v0.5.4** — 2026-05-05. **Sol Uranian Time (SUT)** — third planetary time system in the package alongside Mars Sol Date / Mars Coordinated Time and lunar synodic / sidereal phase. New `bridge.jd_to_sol_uranian_time(jd_tdb)` returns USD (Uranian Sol Date, sidereal-day count since the 2007 northern equinox), SUT (time-of-day in Uranian hours), orbital phase + season (4 ~21-yr seasons partitioning Uranus's 84.02-yr orbit). Carries `retrograde=True`; the encoder still advances `omega = +2π/P` for all bodies, but surfacing the flag makes the asymmetry visible. CLI `time-uranus --jd ...` (or `--usd ...` to invert). Plus a CLI `--help` audit across every subcommand. See §7.3. Live: <https://pypi.org/project/ephemerides-spectral/0.5.4/>.
* **v0.5.3** — 2026-05-05. **Moon residuals: 13 of 17 moons fixed.** v0.5.2 sweep flagged ~100° RMS residuals on most moons; root cause turned out to be **period truncation** in the BODIES table (10⁻⁴-relative omega error accumulating over 41,000+ orbits across the 200-yr sweep). The hypothesised ecliptic-projection frame mismatch was ruled out by per-orbital-period diagnostic (within one orbit the broken moons show <1° RMS). Fix: full-precision (9+ decimals) sidereal periods from JPL HORIZONS / NASA fact sheets. Result: io 106° → 0.34°, europa 116° → 0.76°, ganymede 117° → 0.14°, adrastea 104° → 0.07°, amalthea 102° → 0.27°, enceladus 103° → 2.57°, tethys 101° → 2.94°, dione 117° → 2.54° — 30-1450× improvements. **13 of 17 moons now clean (was 4)**. Four still broken (metis, thebe, rhea, phoebe) — physics-specific investigation queued. See [`figures/moon_residual_v0.5.3.md`](figures/moon_residual_v0.5.3.md). Live: <https://pypi.org/project/ephemerides-spectral/0.5.3/>.
* **v0.5.2** — 2026-05-05. **Patch-shrinks-residual benchmark VINDICATED on planets** via least-squares fitting at the exact target period. New `CATALOG_V2` with three measured-to-work patches (Mars 99.2%, Mercury 99.9%, J–S 97.6/96.0% shrinkage); ships alongside the original v0.4.0 `CATALOG`. **Empirical finding**: J–S `correlation = +1` (in-phase), not −1 as the v0.4.0 anti-correlated-libration assumption had it. Moon-kernel infrastructure (`auxiliary_kernels` parameter on `load_ephemeris`; new `bundle.lookup`; `de441_moon_spectrum.py` runs a moon-friendly ±200 yr sweep). 4 of 17 moons clean; rest queued as v0.5.x research. See §9. Live: <https://pypi.org/project/ephemerides-spectral/0.5.2/>.
* **v0.5.1** — 2026-05-05. **Patch-shrinks-residual benchmark — PARTIAL vindication; two authoring bugs surfaced.** Three new research scripts: `patch_shrinks_residual.py`, `author_phase_recovered_patches.py`, `verify_recovered_patches.py`. The benchmark measured the v0.4.0 catalog and found Mars +2.5%, Mercury **−49.9% (peak GREW)**, J–S +30.9% / −0.4% — methodology REJECTED. The bugs: amplitude was off by 2× (used FFT magnitude rather than `2|X[k]|/N` real amplitude), and phase was wrongly assumed 0. With phase recovered from the FFT's complex spectrum, Mercury swung 89 percentage points (−49.9% → +39.6%), J–S hit ~77% on both bodies, but Mars stayed stuck at 2.7% due to FFT bin leakage. v0.5.2 fixes the leakage problem with LS-fitting. Live: <https://pypi.org/project/ephemerides-spectral/0.5.1/>.
* **v0.5.0** — 2026-05-05. **38 bodies; SPICE-free runtime; 21× faster sweep.** Body roster grows 26 → 38: Jovian inner regulars (Metis, Adrastea, Amalthea, Thebe), classical Saturnians (Mimas, Tethys, Dione, Hyperion, Iapetus, Phoebe), Saturn co-orbitals (Janus, Epimetheus). Three new famous resonances: **Mimas–Tethys 4:2** (Cassini Division), **Enceladus–Dione 2:1** (powers Enceladus tidal heating), **Titan–Hyperion 4:3** (Hyperion chaotic rotation). Natural-resonance gear group expands $\mathbb{Z}/30 \to \mathbb{Z}/60 = \mathbb{Z}/4 \times \mathbb{Z}/3 \times \mathbb{Z}/5$. New codegen step emits `_data/initial_phases.json`; `pip install` works out of the box without SPICE staging. Pre-ship FFT sweep confirmed zero regressions on the 10 DE441-coverable bodies (every peak amplitude byte-identical to v0.3.1) and 21× faster sweep (314.9 s → 14.6 s) thanks to v0.4.1 native + v0.5.0 SPICE-free init phases. See §10. Live: <https://pypi.org/project/ephemerides-spectral/0.5.0/>.
* **v0.4.1** — 2026-05-05. **C-side overlay (ABI v2).** Native backend now applies the diagnosed-fiber overlay; `backend="c"` produces byte-identical phases to `backend="bip"` even with patches active. New `c/src/es_patches.c`: `es_apply_patch` / `es_clear_patches` / `es_n_active_patches` / `es_get_patch_at`. Capacity 32 patches; encoder hook runs after sub-day remainder, before the final cyclic-group reduction. Banker's rounding shared between encode and overlay paths. **237× speedup** on patched encodes (10.8 ms BIP → 0.046 ms C). ABI v1 → v2; the Python ctypes shim refuses mismatched binaries cleanly. Live: <https://pypi.org/project/ephemerides-spectral/0.4.1/>.
* **v0.4.0** — 2026-05-05. **Runtime kernel patching — diagnosed-fiber overlay (Python side).** Patches sit beside the published spectral kernel as DATA, not code edits, and contribute per-body residue deltas at encode time as an overlay. Inspired by Linux ksplice / kpatch; the kernel's published bytes never change. Two patch kinds: `SinusoidPatch` (diagonal, single body) and `CoupledSinusoidPatch` (off-diagonal pair with `correlation ∈ {-1, +1}`). Three patches in the bundled CATALOG authored from v0.3.1's FFT residual analysis. Bridge: `apply_patch` / `apply_custom_patch` / `list_active_patches` / `list_catalog_patches` / `clear_patches`; CLI `patches catalog/apply/active/clear`. With no patches active the encoder is byte-identical to v0.3.1 (regression test pinned). C native backend transparently falls back to BIP when patches are active (correctness > speed; v0.4.1 brings the C-side overlay). See §8. Live: <https://pypi.org/project/ephemerides-spectral/0.4.0/>.
* **v0.3.1** — 2026-05-04. **Native C backend + spectral syzygy window search + DE441 error-spectrum FFT.** Native C library bundled in 15 platform wheels (3 OS × 5 Python) under `_native/`, loaded via ctypes; **~1000× speedup** on the encode hot loop; byte-exact parity with the Python BIP encoder. Banker's rounding (`es_banker_round`) added to match `numpy.round` half-to-even semantics in the sub-day remainder step. New `bridge.find_syzygies(jd_lo, jd_hi, kind, threshold)` + CLI `find-syzygies` — HDC-native enumeration in closed form; replaces the v0.3.0 point-evaluation `eclipse --jd` for window queries (~1000× faster on multi-decade windows). New `research/de441_error_spectrum.py` FFTs the per-body residual against DE441 truth — **headline finding: Jupiter–Saturn show identical 9.56-yr peaks at ±45° amplitude — the smoking-gun missing-coupling signal motivating v0.4+'s catalog**. Pure-Python `py3-none-any` wheel preserved for Pyodide / WASM. Live: <https://pypi.org/project/ephemerides-spectral/0.3.1/>.
* **v0.3.0** — 2026-05-04. **Time scales + DE441 sweep.** New bridge surface for Mars Sol Date / Mars Coordinated Time (`jd_to_mars_time` / `mars_time_to_jd`, Allison & McEwen 2000 formulas) and mean lunar synodic + sidereal phase primitives (`get_lunar_phase`). LTE440 (Lin et al. 2025, A&A 704 A76) registered in `LUNAR_KERNELS` as a known lunar-time ephemeris; metadata only, no auto-download. CLI: `time-mars`, `time-lunar`, `lunar-kernels` subcommands. New `research/de441_sweep.py` runs the BIP encoder across the full DE441 epoch (J2000 ± 14,000 yr) and reports per-body errors — see [`figures/de441_full_sweep.md`](figures/de441_full_sweep.md) for the honest table (Earth, Venus, Uranus stay <10°; Mars 14°; Mercury 84°; Jupiter / Saturn / Neptune / Pluto / Moon all hit >150° at the multi-millennium extremes — the structural-limit signature of phenomenological `α = 0.1`). LTC (Lunar Coordinated Time) deferred to v0.4+ when NASA + international agencies finalise the standard. Live: <https://pypi.org/project/ephemerides-spectral/0.3.0/>.
* **v0.2.0** — 2026-05-04. **Phase 9 coverage extension.** The hardcoded Jupiter–Saturn 5:2 entry is promoted to a structured `RESONANCES` SSOT table in `research/laplacian.py`. Three new resonance pairs join it: **Neptune–Pluto 3:2** (orbital), **Io–Europa 2:1** + **Europa–Ganymede 2:1** (the two pairwise legs of the Jovian 4:2:1 Laplace resonance). The reference encoder (`get_dynamic_laplacian`), the BIP encoder (`encode_state`), and the C codegen (`emit_c_tables.py`) all walk the same table. Modulation depth `α = 0.1` remains global across all four resonances; per-resonance values from a Hamilton/Delaunay-variable Lagrangian are deferred to v0.3.x. C port: `es_n_couplings` grows 1 → 4; byte-for-byte parity with Python preserved across all 26 bodies at +20 yr. Live: <https://pypi.org/project/ephemerides-spectral/0.2.0/>.
* **v0.1.0** — 2026-05-04. First PyPI release. Phases 5–9 frozen into the wheel: 26-body Sol Star System Laplacian, LTI propagator (Phase 8 baseline), state-dependent breathing couplings (Phase 9), ALU-native BIP encoder (305× speedup, 256 KB state), integer cosine LUT for the off-diagonal modulation, fixed-point Q-format frequency discipline, scoped overflow trap. Two backends: `bip` (default, integer ALU) and `complex128` (FPU reference). Rich CLI (9 subcommands) + Pyodide-friendly bridge. Live: <https://pypi.org/project/ephemerides-spectral/0.1.0/>.
* **v0.1.0rc1** — 2026-05-04. TestPyPI release candidate. Round-tripped clean; published under OIDC trusted publishing. Live: <https://test.pypi.org/project/ephemerides-spectral/0.1.0rc1/>.

## 5. Phase 10: Resonance coverage (v0.2.0)

Phase 9 (v0.1.0) wired exactly one off-diagonal modulation: Jupiter–Saturn 5:2. Phase 10 promotes that single entry to a SSOT table and adds three more pairs.

### 5.1 The RESONANCES table

```python
# research/laplacian.py
RESONANCES: List[Resonance] = [
    Resonance("jupiter", "saturn",   5, 2, "Jupiter-Saturn 5:2 (Great Conjunction)"),
    Resonance("neptune", "pluto",    3, 2, "Neptune-Pluto 3:2 (orbital resonance)"),
    Resonance("io",      "europa",   2, 1, "Io-Europa 2:1 (Laplace pair 1)"),
    Resonance("europa",  "ganymede", 2, 1, "Europa-Ganymede 2:1 (Laplace pair 2)"),
]
```

Each entry parameterises an off-diagonal weight modulation:

$$W_{ab}(\phi) = W_{ab}^{(0)} \cdot \bigl(1 + \alpha \cos(n_a \phi_a - m_b \phi_b)\bigr)$$

with $\alpha = 0.1$ global across all four entries in v0.2.0. The four pairs were chosen because each is a real, named mean-motion resonance in the solar system:

| Resonance | Bodies | Status in solar-system literature |
| :--- | :--- | :--- |
| 5:2 | Jupiter, Saturn | "Great Conjunction"; long-period libration in J–S semi-major axes due to mutual perturbation. |
| 3:2 | Neptune, Pluto | Pluto is in a stable 3:2 resonance with Neptune that prevents close approach despite Pluto's eccentric orbit. |
| 2:1 | Io, Europa | First leg of the Laplace 4:2:1 resonance. Io completes 2 orbits per Europa orbit. |
| 2:1 | Europa, Ganymede | Second leg of the Laplace resonance. Europa completes 2 orbits per Ganymede orbit. |

### 5.2 Modelling discipline (and what v0.2.0 still owes)

The convention $\cos(n_a \phi_a - m_b \phi_b)$ is the **fast** anti-resonant combination, not the canonical slow resonant angle $m_b \phi_a - n_a \phi_b$. The cosine is symmetric, so under modulation the two are equivalent at the envelope level — but the *frequency* of the breathing differs. v0.2.0 keeps the v0.1.0 J–S convention (faster body's multiplier first) so the Jupiter–Saturn modulation is byte-for-byte identical to v0.1.0; the new entries follow the same convention.

A first-principles derivation (v0.3.x) would:

1. Start from the gravitational two-body Hamiltonian, expand around each near-resonance using Lie-series perturbation theory in Delaunay variables.
2. Extract the dominant resonance harmonic — for J–S 5:2 this is the slow combination $2\lambda_J - 5\lambda_S - 3\varpi_S$ (with $\varpi_S$ Saturn's longitude of perihelion).
3. Read off the coefficient (which gives $\alpha$ per resonance, derived not phenomenological).

That programme is documented in the ROADMAP and not in v0.2.0's scope.

### 5.3 Verification

* The 0.0002 rad Earth phase floor at +20 yr against DE421 is preserved (Earth doesn't appear in any of the four resonance entries).
* Encoded phase residues for Io / Europa / Ganymede / Neptune / Pluto shift relative to v0.1.0 because their modulation is now active.
* C port (`c/src/es_laplacian.c`) carries `es_n_couplings = 4`; `make parity` reports byte-for-byte agreement with the Python encoder across all 26 bodies.

## 6. Natural gear group, leaf structure, concert frequency (v0.3.0 framing)

This section formalises an intuition Steven brought to the Phase 9 design: *what is the natural frequency of the concert?*

The intuition: each celestial body is a "gear" with its own intrinsic period; the Laplacian eigenbasis arranges those gears on a tree whose leaves are the bodies themselves; the *aggregate* frequency that emerges from the tree is the concert's natural frequency. Three precise questions hide inside that intuition. We address each.

### 6.1 Two readings of "natural gear group"

There are two different gear groups in play here, and the distinction matters for how we interpret the encoder's structure.

**Reading 1: the architectural gear group (encoder-imposed).** The BIP encoder picks $\mathcal{G}_{\text{enc}} = \mathbb{Z}/2^{32}\mathbb{Z}$ as its phase modulus because that turns modular reduction into free `uint32` overflow. Each body's mean motion gets discretised as $n_b = \lfloor 2^{32} / P_b \rfloor$ residues per day so all bodies share one master cyclic group. **This is human-imposed**: $2^{32}$ is convenient, not physical. Any power of 2 works for the architecture; any non-power-of-2 pays an explicit `% n` per op (cf. chess-spectral §20.13's $\mathbb{Z}/640\mathbb{Z}$).

**Reading 2: the natural gear group (resonance-derived).** The *physical* cyclic structure that the bodies actually live in comes from the integer ratios of their mean motions — the same combinatorial structure the bronze antikythera designers extracted by hand. For each resonance pair $(n_a, m_b)$ in the Phase 9 table, the resonant angle $n_a \phi_a - m_b \phi_b$ closes after $\mathrm{lcm}(n_a, m_b)$ revolutions of the slow combination. The aggregate natural modulus over the whole resonance set is

$$M_{\text{nat}} = \mathrm{lcm}\{\,\mathrm{lcm}(n_a^{(k)}, m_b^{(k)}) : k \in \text{resonances}\,\}.$$

For the v0.2.0 four-resonance table — $(5,2)$, $(3,2)$, $(2,1)$, $(2,1)$ — the per-pair LCMs are $\{10, 6, 2, 2\}$; the aggregate natural modulus is

$$M_{\text{nat}} = \mathrm{lcm}(10, 6, 2, 2) = 30 = 2 \cdot 3 \cdot 5.$$

By the Chinese Remainder Theorem, $\mathbb{Z}/30\mathbb{Z} \cong \mathbb{Z}/2\mathbb{Z} \times \mathbb{Z}/3\mathbb{Z} \times \mathbb{Z}/5\mathbb{Z}$ — three independent prime factors. Those are the **natural coprimes** of the resonance topology: the system has a 2-fold symmetry (Io–Europa, Europa–Ganymede halve), a 3-fold symmetry (Neptune–Pluto thirds), and a 5-fold symmetry (Jupiter–Saturn fifths). A 30-tooth gear divides cleanly into every resonance the model knows about.

This is exactly what the bronze antikythera designers did. Callippic = $19 \times 235 / 4 = 940$ days (4 Metonic cycles ÷ 4) factors as $940 = 2^2 \cdot 5 \cdot 47$; Metonic = 235 lunar months factors as $235 = 5 \cdot 47$. The factor structure is the *natural-coprime fingerprint* of the dial topology.

### 6.2 Connection to the chess non-Markovian sheaf

The chess-spectral notebook §19 ("Multi-Sheeted Riemann Encoding for Non-Markovian Rules") names the same pattern from the chess side: when rules are non-Markovian (castling rights, en-passant, repetition draws), the natural state-space is a **sheaf** over the rule-structure rather than a single global cyclic group. Each rule contributes its own cyclic factor; the natural state space is the *product* of those factors, not the embedding into a single big group.

The DE441 resonance set is the same idea on a different evidence object. Each resonance pair contributes a cyclic factor ($\mathbb{Z}/\mathrm{lcm}(n_a, m_b)\mathbb{Z}$); the natural state space is the product $\prod_k \mathbb{Z}/\mathrm{lcm}(n_a^{(k)}, m_b^{(k)})\mathbb{Z}$ — and CRT collapses that product into a single $\mathbb{Z}/M_{\text{nat}}\mathbb{Z}$ when the factors are coprime, exactly the way the chess sheaf collapses to a $\mathbb{Z}/640\mathbb{Z}$ engine when the rule factors interact cleanly.

The opposite case — when the rule factors *don't* interact cleanly — is what forces the chess project into multi-sheet territory. For ephemerides, the analogue would be: a resonance set whose pair-LCMs are *not* pairwise coprime forces extra structure (drift between two interpretations of the same residue). v0.3.0 happens to be in the clean-CRT regime; future resonance entries may not be.

### 6.3 Practical surface in v0.3.0

`bridge.get_natural_resonance_group()` returns the table, the per-pair LCMs, the aggregate $M_{\text{nat}}$, and the prime decomposition. On the four wired resonances:

```json
{
  "ok": true,
  "resonances": [
    {"a": "jupiter",  "b": "saturn",   "n_a": 5, "m_b": 2, "pair_lcm": 10},
    {"a": "neptune",  "b": "pluto",    "n_a": 3, "m_b": 2, "pair_lcm": 6},
    {"a": "io",       "b": "europa",   "n_a": 2, "m_b": 1, "pair_lcm": 2},
    {"a": "europa",   "b": "ganymede", "n_a": 2, "m_b": 1, "pair_lcm": 2}
  ],
  "natural_modulus": 30,
  "prime_factors": [2, 3, 5],
  "interpretation": "30-tooth natural gear; CRT-isomorphic to Z_2 x Z_3 x Z_5"
}
```

The number `30` is small. The bronze antikythera mechanism has hundreds of teeth across its gears. The reason the bronze numbers are larger is that *the bronze tracks more cycles than just the four Phase-9 resonances* — Saros, Metonic, Callippic, the Olympiad cycle, the Egyptian wandering year, and the planetary synodic periods all contribute their own factors. The Phase-9 model is currently a *minimal* resonance set; as v0.3.x adds resonance entries (Lunar precession, Saros, Earth–Mars approaches, etc.), $M_{\text{nat}}$ grows toward the bronze's hundred-tooth scale by the same combinatorial logic.

**Reading the numerology from the data, not imposing it.** This is the substantive distinction: $\mathbb{Z}/30\mathbb{Z}$ is what the *resonance set itself* demands; $\mathbb{Z}/2^{32}\mathbb{Z}$ is what the *encoder architecture* demands. The encoder happens to embed the natural group cleanly (30 divides $2^{32} - $ wait, no: 30 does *not* divide $2^{32}$; $\gcd(30, 2^{32}) = 2$). Phase residues that hit a $\mathbb{Z}/30\mathbb{Z}$-aligned position drift quasi-periodically against the $\mathbb{Z}/2^{32}\mathbb{Z}$ grid — and that drift IS the structural-limit error the §4 sweep documents. The bridge surface lets future v0.4+ work either re-tile $\mathcal{G}_{\text{enc}}$ to absorb $M_{\text{nat}}$ as a divisor, or split the encoder into a sheaf over the natural prime factors (the chess-style multi-sheet move).

### 6.2 The leaf structure

The interaction graph of the 26 bodies has a specific shape: trunk → branch → leaf.

- **Trunk:** the Sun. All planets couple to it (the planet–sun off-diagonal entries).
- **Primary branches:** each planet, with its mean motion as the natural diagonal frequency.
- **Secondary branches:** the Galilean moons coupled to Jupiter; Titan / Enceladus / Rhea coupled to Saturn; etc.
- **Leaves:** the four main-belt asteroids (Ceres, Vesta, Pallas, Hygiea), each with one connection (to Jupiter) and no further branching.

Operationally, the **periphery rule** named in the antikythera notebook §11.6 ("single-job gears live at the periphery of the mesh DAG; load-bearing multi-output trains live at the heart") is the same observation made about a different evidence object. In the antikythera mechanism, leaf gears are the small ones with one output; in the DE441 encoder, leaf bodies are the asteroids whose dynamics depend on Jupiter but feed nothing back. The *graph topology* is what makes a body a leaf, not its mass or its name.

The Laplacian eigenbasis of this tree has a specific structural property: the smallest non-zero eigenvalue (the *Fiedler value* $\lambda_2$) measures the algebraic connectivity. Heavily-leaved trees have small $\lambda_2$; tightly-coupled clusters have large $\lambda_2$. The Sol Star System sits closer to the heavily-leaved end of the spectrum — most bodies are at depth 2 or 3 from the Sun, only the moons are deeper.

### 6.3 The concert frequency — three readings

"Natural frequency of the concert" admits at least three precise mathematical instantiations. Each gives a different number, all correct in their own framing.

**Reading A: LCM rebound period (the "complete recurrence").**
$$T_{\text{rebound}} = \mathrm{LCM}\{P_b : b \in \text{bodies}\}$$
For real bodies whose periods are irrational, the strict LCM is infinite — the system never exactly repeats. For the *rational approximations* the bronze used (940 days = Callippic, 19 yr = Metonic, etc.), $T_{\text{rebound}}$ is finite and astronomically large. The concert "rebounds" at $T_{\text{rebound}}$ — every body returns to its initial position simultaneously.

**Reading B: Fiedler frequency (the "slowest collective mode").**
$$\omega_{\text{Fiedler}} = \sqrt{\lambda_2(L_{\text{LTI}})}$$
The slowest non-trivial vibration mode of the body-interaction graph, where $\lambda_2$ is the smallest non-zero eigenvalue of the static Laplacian. This is the natural frequency at which the *coupled* system "rings" if perturbed — the analogue of the lowest mode of a vibrating string. For the Sol Laplacian this is dominated by the longest period (Pluto, ~248 yr) modulated by the inter-body coupling weights.

**Reading C: Carrier frequency (the encoder's clock).**
$$\omega_{\text{carrier}} = \frac{2\pi}{2^{32}}\,\text{rad/residue}$$
The *quantum* of the cyclic group $\mathbb{Z}/2^{32}\mathbb{Z}$ — the smallest phase increment the BIP encoder can represent. At Earth's mean motion (~11.76 M residues/day), one residue is ~7.3 ms wall-clock per residue tick. This is the encoder's "sample rate" — the limiting time resolution before quantization noise kicks in.

### 6.4 Which reading matters when

- **For Saros / Metonic / Callippic anchoring** (lining up calendrical events with eclipses): Reading A. The rebound period sets the natural cycle length.
- **For dynamic stability analysis** (does a perturbation amplify or damp?): Reading B. The Fiedler frequency sets the slowest-mode timescale on which perturbations equilibrate.
- **For numerical-precision budgeting** (how short an event can the encoder represent?): Reading C. The carrier frequency sets the floor.

The bronze antikythera was designed for Reading A (it's a calendar-aligning machine). The Phase-9 BIP encoder operates in Reading C (it's a clocked digital instrument). Reading B is the bridge — it tells us *which* of the encoder's residues will drift fastest under unmodelled perturbation, and is the question we want to ask when iterating toward v0.3.x's first-principles α derivation.

### 6.5 Implication for the leaf-and-pinion question

Steven's framing — *the leaf-like structure should give us the concert's natural frequency* — turns out to be Reading B. A pure tree (no resonance edges) has $\lambda_2 \propto 1 / \text{tree depth}$ asymptotically; adding coupling edges (the resonance pairs) raises $\lambda_2$. The Phase 9 breathing modulation, viewed through this lens, is *deliberately* damping the slow modes by injecting state-dependent coupling exactly at the resonance angles where the slow modes would otherwise dominate.

That is a satisfying picture: the breathing Laplacian's role is to keep the concert in tune. The DE441 sweep results (§4 release notes; full data in `figures/de441_full_sweep.md`) confirm the inverse — bodies *outside* the wired resonance set (Earth, Venus, Uranus) drift cleanly under the static Laplacian; bodies *inside* the resonance set (Jupiter, Saturn, the Laplace pair) drift wildly when the phenomenological `α = 0.1` doesn't cancel their slow modes correctly. The natural concert frequency reading B explains *why* phenomenological α drifts at multi-millennium horizons, and the v0.3.x roadmap's Hamilton/Delaunay derivation gives the per-resonance α values that would null-out the slow modes properly.

## 7. Time scales (v0.3.0)

The v0.3.0 release adds non-Earth time-scale conversions alongside JD. The bronze antikythera tracked Greek civil time (lunisolar Athenian calendar + Olympiad year); the DE441 encoder by default speaks JD (TT or TDB). v0.3.0 surfaces three additional time scales:

| Scale | What | Where |
| :--- | :--- | :--- |
| **MSD / MTC** | Mars Sol Date / Mars Coordinated Time, per Allison & McEwen 2000. Reference: 1873-12-29 12:03:36 UTC = MSD 0 = mean solar midnight at Airy-0. | `bridge.jd_to_mars_time(jd_utc)` / `bridge.mars_time_to_jd(msd)` · CLI `time-mars` |
| **Lunar synodic / sidereal** | Mean lunar phase relative to a J2000-anchored reference new moon. Bronze-dial primitives — fixed-period approximations. | `bridge.get_lunar_phase(jd_tdb)` · CLI `time-lunar` |
| **LTE440** | Lunar Time Ephemeris on DE440 (Lin et al. 2025). Listed in `LUNAR_KERNELS`; not auto-downloaded. | `bridge.list_lunar_kernels()` · CLI `lunar-kernels` |

### 7.1 LTC (Lunar Coordinated Time) — roadmap

NASA + the international space-agency consortium are formalising **Lunar Coordinated Time** in the 2026–2028 window per the April 2024 White House directive. The mathematics is well-defined (TCL → TCB → TDB → TT → UTC), and LTE440 ships the underlying SPICE-format conversion ephemeris with 0.15 ns accuracy through 2050. What's pending is the policy decision on the LTC epoch and the day-length convention.

When that policy lands, ephemerides-spectral gains an `LTC` namespace mirroring `MarsTime`:

```python
# Proposed v0.4+ surface
from ephemerides_spectral.bridge import jd_to_ltc, ltc_to_jd

ltc = jd_to_ltc(2451545.0)   # LTC at J2000
print(ltc["ltc_seconds"], ltc["lunar_calendar_day"])
```

Until then the `lunar-kernels` CLI subcommand returns the LTE440 metadata + the explicit `ltc_status: "definition pending"` flag, so downstream consumers can branch on it.

### 7.2 What's *not* in v0.3.0

- **No automatic LTE440 download.** The kernel is ~100 MB; we expect users who care to fetch it from `github.com/xlucn/LTE440` releases and stage it next to `de441.bsp`.
- **No relativistic time-scale conversions** (TT ↔ TDB ↔ TCB ↔ TCG). Skyfield handles these natively when it has the kernel; we don't reimplement.
- **No proleptic calendar conversions** for Mars or Moon. The Mars Sol number is the natural integer Mars-day index; Mars-calendar variants (Darian, Utopian, etc.) are out of scope.

### 7.3 Sol Uranian Time (SUT) — v0.5.4

The third planetary time system in the package. Uranus is conspicuously absent from §6's natural-resonance gear group: its 84.02-yr orbit doesn't sit in a clean integer mean-motion resonance with any other body in the Sol Star System; its 97.77° axial tilt makes it qualitatively different from every other planet (rotates "on its side"); its rotation is *retrograde* relative to its orbital motion. Sol Uranian Time therefore lives in **its own cyclic group**, separate from the Z₆₀ of v0.5.0.

**Three independent cycles**, partitioned by physics:

| Cycle | Magnitude | Earth-equivalent |
| :--- | ---: | :--- |
| Sidereal day (USD unit) | 17.24 h | ~0.71833 d |
| Solar day | ~17.24 h (essentially equal to sidereal at 84-yr orbit) | trivially different |
| Orbital season (one of 4) | 21.005 yr | one quarter of an orbit |
| Orbital year | 84.02 yr | one full orbit |

The "natural harmonic" for Uranus is therefore *not* a single LCM as it is for the resonance set in §6 (Z_60 = lcm of pair-LCMs). Uranus's three cycles are essentially incommensurate — the sidereal day and orbital period give 1 Uranian year ≈ 42,721.81 USD, which doesn't decompose into small integer factors. The "harmonic" instead lives in the **discrete season partition**: the 4 seasons (north-pole-summer, descending equinox, south-pole-summer, ascending equinox) come from the 4-fold geometric symmetry of solstice / equinox configurations, not from any number-theoretic structure.

**Anchor**: 2007-12-16 northern equinox (JD 2454451.0). Sun crossed Uranus's equator going from north-summer (1985) toward south-summer (2028).

**Surface**:

```python
bridge.jd_to_sol_uranian_time(jd_tdb=2454451.0)
# {
#   "ok": True,
#   "jd_tdb": 2454451.0,
#   "usd": 0.0,                     # Uranian Sol Date, sidereal-day count
#   "sut_hours": 0.0,               # time-of-day on Uranus, 0-24
#   "sut_seconds": 0.0,             # SUT in Earth-seconds-since-midnight
#   "orbital_phase": 0.0,           # [0, 1) since SUT epoch
#   "season": "northern-autumn",    # one of 4
#   "years_since_epoch": 0.0,
#   "retrograde": True,             # Uranus rotates backward
#   "epoch": {"jd_tdb": 2454451.0, "sidereal_day_hours": 17.24, ...}
# }

bridge.sol_uranian_time_to_jd(usd=4046.45)   # invert
# {"ok": True, "usd": 4046.45, "jd_tdb": 2457358.55}
```

CLI: `ephemerides-spectral time-uranus --jd 2454451.0` (or `--usd 4046.45` to invert). Full `--help` includes the natural-harmonic discussion + concrete examples spanning J2000, the SUT epoch, and a current-day reference.

**Retrograde flag**. Uranus rotates retrograde — the rotation direction is *backwards* relative to its orbital motion. The v0.5.4 encoder still advances `omega = +2π/P` for all bodies, so the encoded longitude doesn't track Uranus's actual sky position over time the way it does for prograde rotators; the `retrograde=True` flag makes this asymmetry visible to consumers but doesn't *fix* it. Phoebe's continued ~104° RMS in the v0.5.3 moon FFT sweep (also retrograde — it's a captured Centaur) is the same root cause. A sign-aware-omega encoder is queued as a v0.5.x roadmap entry; the SUT surface will benefit automatically.

**Why this matters in spectral terms**. The §1.4 vocabulary names the breathing Laplacian as "state-dependent discrete Ricci curvature." Sol Uranian Time is a clean *external coordinate* against which to measure that curvature for the Uranian sub-system: when v0.5.x adds Titania-vs-Oberon resonance entries (or the four other major Uranian moons — Miranda, Ariel, Umbriel, Oberon), their breathing-coupling dynamics will be parameterised against SUT, not against Earth's UTC or JD. The "Sol Uranian Time" framing is therefore the right *parametric coordinate* for the Uranus-system fragment of the larger Laplacian, the same way MSD/MTC is the right coordinate for the Mars-system fragment.

### 7.4 Sol Terra-Luna Time (STLT) — v0.10.0

**Anchored Lunar time** using the synodic month (29.530589 days) as the natural unit, and the first Sol Time member whose **default epoch is not J2000.0**. The "Terra-Luna" in the name follows the **moons-stuck-to-parent** convention from v0.9.1: every moon's primary Sol Time is named `Sol <Parent>-<Body> Time` to keep the gravitational-binding relationship visible in the time hierarchy. STLT is Luna's primary entry under that convention; future moon ports (Sol Pluto-Charon Time, Sol Jupiter-Io Time, Sol Saturn-Titan Time, ...) follow the same pattern. Saros (18.03 yr eclipse cycle) and Metonic (19.00 yr lunar–solar reconciliation cycle) counts come along for free as multiples of the synodic month.

**Why a *system* clock?** None of the existing Luna-related Sol Times are the right home for a system event like an eclipse:

- **SLT** (Sol Luna Time) is Luna's tidally-locked surface frame.
- **Sol Lunar Time** (`get_lunar_phase`) is Luna's phase as observed from Terra.
- **STT** (Sol Terra Time) is Terra's surface frame.

A solar eclipse is a Sun–Terra–Luna syzygy — a single-parameter event in the Terra–Luna *pair* frame. STLT fills the gap. The naming-hierarchy slot generalises: rocky bodies + Sun + Luna get direct Latin proper nouns; gas/ice giants get adjective forms; **pairs get hyphenated proper nouns** (Sol Terra-Luna; future Sol Pluto-Charon; Sol Jupiter-Io).

**Default epoch: Meton of Athens's summer solstice, 27 June 432 BCE** (proleptic Julian). Meton calibrated his 19-year cycle (235 synodic months ≈ 19 tropical years, off by ~2 hours) against this exact solstice — the foundational Greek lunar–solar-reconciliation observation and the cycle the Antikythera mechanism's Metonic dial encodes.

The choice is empirically validated by `research/lunar_epoch_candidates.py`. The user proposed scoring the **Hipparchus–Babylonian eclipse-archive midpoint** as a "combo" candidate: the arithmetic mean of the JDs of the earliest Babylonian eclipse Hipparchus cited (Mardokempad's first regnal year, 19 March 721 BCE per Almagest IV.6) and Hipparchus's own calibration eclipse (25 January 141 BCE per Almagest VI.5). That midpoint lands within **+240 days of Meton's solstice** — *same year*, eight months later. Greek mathematical astronomy's eclipse archive sits centred on Meton's lifetime; the midpoint test confirms his anchor numerically without circularity.

| Candidate | JD_TDB | Spectral / solstice score | Role |
|---|---|---|---|
| Antikythera Saros anchor (Freeth & Jones 2012) | 1646782.0 | 0.49 d offset, score 0.197 rad | Project-namesake; Saros-dial start |
| **Meton 432 BCE summer solstice** | **1563813.0** | **1.19° from solstice (epoch-of-date)** | **Default; Metonic-dial origin** |
| Hipparchus 141 BCE lunar eclipse | 1669949.5 | 0.18 d offset, score 0.033 rad | Tightest spectral match |
| Mardokempad 721 BCE lunar eclipse | 1458156.4 | 0.52 d offset, score 0.008 rad | Earliest Babylonian record |
| Hipparchus–Babylonian midpoint (derived) | ~1564053 | +240 d from Meton — same year | Independent confirmation |

The four non-default epochs ship as named alternatives (`epoch="antikythera" / "hipparchus" / "mardokempad" / "j2000"`); `j2000` is kept for parity with the rest of the Sol Time series.

**House-epoch framing — *not* NASA LCT**. NASA's Lunar Coordinated Time is still pending standardisation per the April 2024 White House directive (target ~2026–2028). When LCT lands we add it as a sibling epoch keyword. Until then STLT carries the project's own historically-anchored zero.

**Surface**:

```python
bridge.jd_to_sol_terra_luna_time(jd_tdb=2451545.0)
# Default Meton epoch
# {
#   "ok": True,
#   "jd_tdb": 2451545.0,
#   "epoch_name": "meton",
#   "epoch_jd_tdb": 1563813.0,
#   "days_since_epoch": ...,
#   "synodic_count": ...,         # synodic-month count since 432 BCE solstice
#   "synodic_phase": [0, 1),
#   "saros_count": ...,           # Saros cycle (18.03 yr)
#   "saros_phase": [0, 1),
#   "metonic_count": ...,         # Metonic cycle (19.00 yr) — Meton's own cycle
#   "metonic_phase": [0, 1),
#   "epoch": {"description": ..., "abbreviation": "STLT", ...}
# }

bridge.jd_to_sol_terra_luna_time(jd_tdb=2451545.0, epoch="antikythera")
# Switch to the Saros-dial anchor (23 Aug 205 BCE solar eclipse)
```

CLI: `ephemerides-spectral time-terra-luna --jd 2451545.0` (default Meton); `--epoch <name>` to switch anchors. `--synodic-count <N>` inverts.

**Why this matters in spectral terms.** The Metonic cycle is the natural emergent factor in our `Z₆₀ = Z₄ × Z₃ × Z₅` resonance group from §6: `Z₅` is the Metonic-aligned component (5-fold cyclic factor of the lunar–solar reconciliation). Anchoring STLT at Meton's solstice puts the system-clock zero on the encoder's algebraic spine — the moment in time where the `Z₅` component aligns with its modern-conventional reference. Future v0.10.x extensions to other pair times (Sol Pluto-Charon, Sol Jupiter-Io) inherit the same hierarchy: each pair's natural epoch is whatever calibration moment that resonance was anchored at, not J2000 by default.

### 7.5 Sol Proper Time (SPrT) — v0.11.0

A *per-body diagonal fiber* extending the Mercury 43″/century PN correction from §1 to every body in the roster. The user's framing during the v0.10.0 ship: *"can we simply add `--proper` as a line arg to invoke gravitational time dilation fiber so that users don't even need to know anything extra had to happen in the back end?"* That's exactly what shipped — opt-in, transparent, applied uniformly to every `time-*` CLI subcommand.

**Two leading-order components per body**, both positive (clocks tick slower than at infinity / in the barycentric frame):

1. **Surface gravitational time dilation** = `GM/(R·c²)` at the body's surface. The same |Φ|/c² scalar that Mercury's PN diagonal already captures for orbital perihelion precession, reused here for surface clock-rate. Per-body diagonal fiber on the Laplacian.

2. **Mean orbital kinematic time dilation** = `v_orb²/(2c²)` from Kepler's third law. Leading-order Special Relativity dilation due to orbital motion in the barycentric frame.

Total clock rate of a stationary body-surface clock relative to TCB:

$$\text{rate} = 1 - \frac{GM}{Rc^2} - \frac{v_{\text{orb}}^2}{2c^2} + O(c^{-4})$$

The cross-coupled $O(c^{-4})$ terms (general post-Newtonian) and the rotational kinematic ($\omega \times R$) are deferred to v0.12.0+; SPrT v0.11.0 captures the leading two terms exactly.

**Validated against six published numbers** to within 0.30 % rel err — Earth GR (Ashby 2003 / GPS), Sun GR, Mars GR (Genova et al. 2014 / Curiosity rover), Pluto GR, Earth orbital kinematic, and the Mars-vs-Terra GR-only difference (the famous **0.0175 s/Earth-year** Curiosity figure). The combined GR + orbital-kinematic Mars–Terra difference is **0.0710 s/Earth-year** — ~4× larger than GR-alone because Mars's slower 1.524-AU orbital velocity adds dilation in the *same* direction as its weaker gravitational well.

| Body | GR surface | Kinematic orbital | Total | Cite |
|---|---|---|---|---|
| Sun | 2.12×10⁻⁶ | 0 | 2.12×10⁻⁶ | Largest well in roster |
| Jupiter | 2.02×10⁻⁸ | 9.5×10⁻¹⁰ | 2.11×10⁻⁸ | |
| Saturn | 7.25×10⁻⁹ | 5.2×10⁻¹⁰ | 7.76×10⁻⁹ | |
| Terra | 6.96×10⁻¹⁰ | 4.94×10⁻⁹ | 5.63×10⁻⁹ | Ashby 2003 |
| Venus | 5.97×10⁻¹⁰ | 6.82×10⁻⁹ | 7.42×10⁻⁹ | |
| Mars | 1.40×10⁻¹⁰ | 3.24×10⁻⁹ | 3.38×10⁻⁹ | Genova 2014 |
| Mercury | 1.01×10⁻¹⁰ | 1.27×10⁻⁸ | 1.29×10⁻⁸ | Fastest planet |
| Luna | 3.14×10⁻¹¹ | 5.79×10⁻¹² | 3.72×10⁻¹¹ | |
| Pluto | 8.14×10⁻¹² | 1.25×10⁻¹⁰ | 1.33×10⁻¹⁰ | Smallest planet GR |

**The diagonal-fiber framing.** The off-diagonal Laplacian weights of §1 encode *orbital coupling strength* (rate of phase evolution between bodies). They're proportional to `GM_other/r²` — gravitational *acceleration* magnitudes, vector-quantity. SPrT's `gr_surface` is the *scalar potential* at the body's surface — `GM_self/R`, one integration away from the off-diagonal weights but pointing at a different observable: clock rates rather than orbital phases. Both are diagonal fibers (per-body), and adding them to the Laplacian at the same architectural slot keeps the spectral-graph framing coherent.

**Surface — three opt-in surfaces**:

```python
# Standalone "what's the rate" query
bridge.get_proper_time_rate(body="mars")
# {"ok": True, "body": "mars", "rate_relative_to_reference": 0.999...,
#  "components": {"gr_surface": 1.40e-10, "kinematic_orbital": 3.24e-9, ...},
#  "abbreviation": "SPrT"}

# Two-body comparison + drift per Earth-year
bridge.compare_proper_times("mars", "terra")
# {"ok": True, "rate_ratio_a_over_b": ...,
#  "seconds_per_earth_year": -0.0710,    # Mars ticks faster by this
#  "components_a": {...}, "components_b": {...}}

# CLI --proper flag — uniform across every time-* subcommand
# Same answer, but proper-time-corrected:
ephemerides-spectral time-mars --jd 2451545.0 --proper
ephemerides-spectral time-terra-luna --jd 2451545.0 --epoch meton --proper
ephemerides-spectral time-sol --jd 2451545.0 --proper

# CLI standalone rate query
ephemerides-spectral time-proper --body sun                    # 2.12e-6
ephemerides-spectral time-proper --body mars --compare-to terra
```

The `--proper` flag adds `<count>_proper` sibling fields to existing Sol Time results (e.g., `msd_proper` on `time-mars`) plus a `proper_time` metadata block — the user gets the corrected count without learning a new function or thinking about GR.

**Two-implementation discipline.** Phase A (`research/proper_time_rates.py`) implements the formulas independently, validates against the six canonical figures, dumps a markdown report. Phase B (`_research/proper_time.py`, the package primitive `--proper` calls) has its own implementation, validated by `tests/test_sprt.py` against the same six figures. Both agree to within 0.30 %. If either drifts, the other catches it — same "two implementations and a pin" pattern as `test_native_version_string_matches` (C ↔ Python version pinning).

**Out of scope for v0.11.0** (deferred to v0.12.0+):

- **Surface rotational kinematic** (`ω × R` at the body's surface latitude). For most bodies orbital dominates; for the Sun it's the inverse — the Sun barely moves in the barycentric frame but its surface rotates at ~2 km/s. Adding rotational kinematic per body needs an `ω` column in `bodies.py` (already in `time_scales.py` for the bodies with their own Sol Times; cross-referencing is the v0.12.0 work).
- **J₂ oblateness corrections** (~10⁻¹⁵ scale spatial variation on Terra). The `--lat`/`--lon` flags are already accepted for forward compatibility; v0.11.0 ignores them. Adding `J2_oblateness` per body in `bodies.py` lets the (lat, lon)-dependent term kick in for that precision tier.
- **Frame dragging** (Lense-Thirring; ~10⁻¹⁵ at Earth-Moon scale). Skip until needed.

**Why this matters in spectral terms.** Mercury's existing 43″/century PN diagonal is the *only* GR fiber in the v0.10.0 Laplacian — a one-off correction tied to Mercury's perihelion. SPrT generalises: every body gets a diagonal GR fiber for its surface clock rate. The architectural slot (per-body, scalar, additive on the diagonal) is the same; the physical observable (clock rate vs. perihelion advance) is different but co-derived from the same underlying potential. Future work — adding rotational kinematic, J₂ oblateness, frame dragging — extends the same diagonal-fiber slot rather than introducing new architectural layers. The pattern is *"every body's GR contribution to the Laplacian, made queryable."*

## 8. Diagnosed-fiber runtime overlay (v0.4.0+ architecture)

> **Patches as data, not code edits — overlay, not bones-mutation.**

The v0.3.1 DE441 error-spectrum FFT identified Jupiter–Saturn as a smoking-gun missing-coupling signal: both bodies show identical 9.56-yr peaks at ±45° amplitude, and the v0.2.0 phenomenological $\alpha = 0.1$ undershoots the actual J–S 5:2 libration depth by ~5×. The natural question becomes: *can we ship patches against these residuals without mutating the published kernel's bytes?*

v0.4.0 answers yes. The architectural commitment:

> **The published spectral kernel — the static `RESONANCES` table, the Laplacian construction, the integer Q-format frequencies — is immutable truth. We don't fix the kernel by adding empirical Fourier corrections to `RESONANCES`. We layer overlays on top.**

This is the same architectural choice Linux made with [ksplice / kpatch](https://en.wikipedia.org/wiki/Ksplice): ship the immutable kernel, hot-patch at runtime via an overlay registry consulted during execution. In our case, the encoder consults a per-process patch registry at the END of each encode call — between the base chunk loop's last sub-day remainder and the final cyclic-group reduction.

### 8.1 The overlay surface

Two patch kinds, both authored as `dataclasses.dataclass(frozen=True)`:

```python
@dataclass(frozen=True)
class SinusoidPatch:
    name: str
    body: str
    amplitude_deg: float
    period_days: float
    phase_rad: float = 0.0

@dataclass(frozen=True)
class CoupledSinusoidPatch:
    name: str
    body_a: str
    body_b: str
    amplitude_deg: float
    period_days: float
    phase_rad: float = 0.0
    correlation: int = -1   # +1 = same-sign, -1 = opposite-sign
```

The encoder hook evaluates each active patch at the encode JD and adds the per-body delta to the cyclic-group accumulator:

$$\Delta\phi_b(t) = A \cdot \sin\!\left(\frac{2\pi (t - t_0)}{P} + \varphi\right)$$

For coupled patches, $\Delta\phi_{b_a} = +\Delta(t)$ and $\Delta\phi_{b_b} = (\pm 1) \cdot \Delta(t)$ depending on `correlation`. The bridge surface (`bridge.apply_patch` / `apply_custom_patch` / `clear_patches` / `list_active_patches` / `list_catalog_patches`) and the `patches` CLI subcommand expose these to consumers. v0.4.1 mirrors the registry into the C library via `es_apply_patch` (ABI v2); cross-backend byte-exact parity verified.

### 8.2 In curvature-vocabulary terms

A patch is a *periodic perturbation of the discrete Ricci curvature* on one edge (or one pair of edges, for coupled). The published kernel sets the baseline curvature; the catalog patches add small, locally-targeted oscillations to that curvature on the resonance edges where the FFT residuals say the static-`α` baseline curvature is off by a known phase + amplitude. The encoded longitude integrates the resulting state-dependent Laplacian; the patch contribution is the corresponding longitude correction the curvature delta implies.

This makes the patches **falsifiable**: each one claims to cancel a specific FFT residual peak in a specific body. The patch-shrinks-residual benchmark (§9) measures whether they actually do.

### 8.3 What the overlay buys

* **Reproducibility**. The published kernel hashes the same forever. A bricked patch is unloadable / disposable; the kernel keeps shipping clean.
* **Composition**. Sinusoidal patches commute (sum of sins commute on the cyclic group). Multiple patches stack order-independently.
* **Diagnosis-driven authoring**. Each catalog entry carries its FFT-residual provenance in `notes`. Authoring discipline: "I claim this patch cancels Mars's 7.96-yr peak at amplitude 3.45°" — the benchmark says yes or no.
* **First-principles vs empirical separation**. The first-principles α-derivation programme (Hamilton-Delaunay-variable Lagrangian; Lie-series perturbation) lives in `RESONANCES`. The empirical Fourier corrections live in the catalog. The two layers don't collide.

## 9. Patch-shrinks-residual benchmark — earning the right to predict missing data

> *We thought we had three working patches; we measured them and found two were wrong-signed and one had a 2× amplitude error. We fixed the math. Then it worked.*

The v0.4.0 catalog patches **claim** to predict missing physics. v0.5.1 audited the claim; v0.5.2 vindicated the corrected methodology. This section formalises what was learned at each step.

### 9.1 The benchmark

For each catalog patch:
1. Run `de441_error_spectrum` on the encoder with no patches → `baseline_amp_targeted_peak`.
2. Apply the patch via `bridge.apply_patch`.
3. Run `de441_error_spectrum` again → `patched_amp_targeted_peak`.
4. Compute `shrinkage_pct = 100 × (baseline − patched) / baseline`.

If shrinkage_pct ≥ 80% on every targeted peak, the methodology is **vindicated** — the patch's claim is measured.

### 9.2 v0.5.1: REJECTED

| Patch | v0.4.0 (mag-only) |
| :--- | ---: |
| `mars-7.96yr-diagonal` | +2.5% |
| `mercury-10.69yr-diagonal` | **−49.9%** *(peak GREW)* |
| `jupiter-saturn-9.56yr-coupled` | +30.9% J / −0.4% S |

The Mercury patch was actively *reinforcing* its target residual. Three diagnostics:

1. **Amplitude was off by 2×.** The v0.4.0 catalog used $|X[k]| / N$ from the FFT magnitude spectrum. For a real-valued residual, the actual sinusoid amplitude is $2|X[k]| / N$ — the energy is split between bins $+k$ and $-k$.
2. **Phase was assumed 0.** Magnitude-only authoring discards phase. The right phase comes from $\arg(X[k])$ in the *complex* FFT bin, plus a time-origin offset:
   $$\varphi = \arg(X[k]) - \frac{\pi}{2} + \frac{2\pi \cdot \text{half\_span\_days}}{P_{\text{days}}} \pmod{2\pi}$$
   The $-\pi/2$ converts cos to sin; the time-origin term accounts for the FFT phase being referenced to sample 0 = $\text{REFERENCE\_JD} - \text{half\_span}$, not $\text{REFERENCE\_JD}$ itself.
3. **J–S `correlation` was wrong.** v0.4.0 assumed $-1$ (anti-correlated libration around the conjunction). The recovered FFT phase difference at 9.56 yr puts the residuals **in-phase** — `correlation = +1`. Same direction, same magnitude.

With these fixes, v0.5.1 hit Mercury +39.6% and J–S 77% on both bodies — close, but Mars stayed stuck at 2.7% due to **FFT bin leakage**: Mars's 7.96-yr residual smears across two adjacent bins (rank-1 7.960 yr / 3.45° and rank-2 7.935 yr / 3.36°), so the single-bin amplitude underestimates the true sinusoid by ~3×.

### 9.3 v0.5.2: VINDICATED via least-squares fitting

v0.5.2 swaps FFT-bin extraction for time-domain least-squares fitting via `scipy.optimize.curve_fit`:

$$\text{minimise}_{A, P, \varphi, c_0, c_1} \quad \sum_k \Bigl( r(t_k) - A\sin\!\bigl(\tfrac{2\pi t_k}{P} + \varphi\bigr) - c_0 - c_1 t_k \Bigr)^2$$

with $P$ a free parameter constrained to $[P_{\text{target}} - 60\text{ d}, P_{\text{target}} + 60\text{ d}]$. The fitted $(A, P, \varphi)$ are *exact for the targeted period* regardless of FFT bin alignment. Mars's recovered amplitude jumps from 6.90° (FFT-bin) to **10.69°** (LS-fit) — that is the leaked energy v0.5.1 couldn't see.

| Patch | Body | Baseline | Patched | **Shrinkage** |
| :--- | :--- | ---: | ---: | ---: |
| `mars-7.96yr-diagonal-v2` | mars | 3.45° | 0.03° | **99.2%** |
| `mercury-10.69yr-diagonal-v2` | mercury | 9.19° | 0.008° | **99.9%** |
| `jupiter-saturn-9.56yr-coupled-v2` | jupiter | 44.63° | 1.07° | **97.6%** |
| `jupiter-saturn-9.56yr-coupled-v2` | saturn | 45.02° | 1.80° | **96.0%** |

Every targeted body hits ≥96% shrinkage. The methodology has earned the right to predict missing data on the planet bodies.

### 9.4 What this earns mathematically

In curvature-vocabulary terms (cf. §1.4): each catalog-V2 patch is an **empirically-measured local Ricci curvature correction** on one resonance edge. The published kernel sets a baseline curvature; the LS-fit recovers the residual periodic curvature delta the actual ephemeris demands; the catalog patches close ≥96% of that delta. The remaining ~4% is residual not captured by a single sinusoid at the dominant period — usually FFT-leaked second-order content that a multi-bin patch (v0.5.x roadmap) would absorb.

The v0.4.0 → v0.5.2 arc is the *audit-then-vindicate* arc that turns the catalog from a forecast hypothesis into a forecast tool. The v0.5.2 catalog ships with measured shrinkage% pinned in each entry's `notes`; future entries should pin theirs the same way.

### 9.5 What's *not* yet earned

* **Moon residuals.** The v0.5.0 + supplementary-kernel sweep (jup365, sat441) reports residuals for 27 of 38 bodies; 4 moons (Callisto, Titan, Iapetus, Hyperion) show clean ≤11° RMS; the rest show ~100° RMS dominated by near-DC content. Most likely cause is a calibration-frame mismatch in the moon-parent-body lookup chain across stacked SPK kernels. Once fixed, the LS-fit catalog methodology applies directly.
* **First-principles α derivation.** The catalog patches are *empirical Fourier corrections*, not derived physics. They paper over what's missing in `RESONANCES` / `L_static` / $L_{\text{PN}}$. The v0.5.x first-principles α derivation (Hamilton/Delaunay-variable Lagrangian) should produce derived modulation depths that make the catalog patches *unnecessary* for the bodies inside the resonance set. Until that derivation lands, the catalog is the working forecast tool.

## 10. 38-body roster + SPICE-free runtime (v0.5.0)

### 10.1 The Galilean marshaling

v0.1.0–v0.4.x ran on a 26-body roster: Sun + 9 planets + 12 named moons + 4 main-belt asteroids. v0.5.0 expands to **38 bodies** by adding all major Jovian and Saturnian moons:

| Class | Bodies added (v0.5.0) | Reason |
| :--- | :--- | :--- |
| Jovian inner regulars (4) | Metis, Adrastea, Amalthea, Thebe | Inside Io, between the rings and the Galileans |
| Classical Saturnians (6) | Mimas, Tethys, Dione, Hyperion, Iapetus, Phoebe | Completes the canonical 9 with v0.1.0's Enceladus / Rhea / Titan |
| Saturn co-orbitals (2) | Janus, Epimetheus | The "swap orbits every 4 yr" pair |

Three new famous resonances joined `RESONANCES`:

* **Mimas–Tethys 4:2** — the libration responsible for the Cassini Division
* **Enceladus–Dione 2:1** — powers Enceladus's tidal heating + plumes
* **Titan–Hyperion 4:3** — source of Hyperion's chaotic rotation

The natural-resonance gear group (cf. §6) expands $\mathbb{Z}/30 \to \mathbb{Z}/60 = \mathbb{Z}/4 \times \mathbb{Z}/3 \times \mathbb{Z}/5$. Same prime factor *set* {2, 3, 5}, but the multiplicity of 2 grew from 1 to 2 because Titan–Hyperion 4:3 contributes $\mathrm{lcm}(4, 3) = 12$.

### 10.2 SPICE-free runtime

v0.4.1 left a UX gap: the C path baked initial phases into `es_initial_phases[]` at codegen time (no SPICE needed at runtime), but the Python BIP path calibrated at runtime via skyfield and silently zeroed-out when no SPICE kernel was staged. The two backends only agreed when SPICE was on disk.

v0.5.0 closes the gap with `codegen/emit_initial_phases.py`, which emits `_data/initial_phases.json` carrying the SAME calibrated values the C codegen uses for `es_initial_phases[]`. `EphemerisBIPInstrument._calibrate_initial_phases` consults the JSON first; only falls back to live SPICE calibration when the JSON is missing (research source tree, or codegen-time itself building the JSON).

Result: `pip install ephemerides-spectral` works out of the box for both backends. Skyfield + jplephem stay as optional dependencies via the `[ephemeris]` extra for callers who want runtime recalibration against custom kernels.

The pre-ship FFT validation (per user instruction *"don't ship before we sweep against DE441 and look for signals to FFT"*) confirmed every peak amplitude on the 10 DE441-coverable bodies is **byte-identical** to v0.3.1's spectrum — the v0.5.0 expansion adds *moon-internal* resonances; none put a planet on either side of the breathing modulation, so planet phases receive no perturbation. The new bodies need supplementary moon kernels to be FFT-validated against ephemeris truth — that's v0.5.2's work, see §9.5.

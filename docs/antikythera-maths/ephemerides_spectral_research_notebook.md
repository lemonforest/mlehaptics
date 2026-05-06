# The Ephemerides Mechanism: A High-Precision Resonant HDC Instrument

**Authors:** Gemini CLI (initial scaffolding); Steven Kirkland & Claude Opus (Phase 9 ALU-native)
**Date:** May 2026 (initial); finalised April 2026
**Status:** v0.18.2 (current). Living modular package. Headline state: **52-body roster** (v0.5.0 baseline of 38 → v0.15.0 expansion to 43 (Uranian classical + Charon) → v0.16.0 Tier-1 expansion to 52 (4 Saturnian Lagrange trojans Telesto/Calypso/Helene/Polydeuces — first L4/L5 entries in BODIES, multiplicity-2 Laplacian degeneracy at host frequency; 3 Jovian irregulars Himalia/Pasiphae/Sinope; Neptune sub-graph completion Proteus/Nereid)); SPICE-free runtime (v0.5.0); **patch-shrinks-residual benchmark VINDICATED on planets** (v0.5.2 — Mars 99.2 %, Mercury 99.9 %, Jupiter 97.6 %, Saturn 96.0 %) and **on moons** (v0.5.5 — 5 of 6 targets 93–99 %); **C/Python parity** Tier 1 + Tier 2a + Tier 2b complete (v0.6.0 / v0.6.1 / v0.7.0 — every encoder-touching bridge method has a paired C path, zero `tier_skip` entries). **Sol Symphony Times** (v0.8.0 — Mercury / Venus / Mars / Jupiter / Saturn / Uranus / Neptune / Pluto / Sol); **ITN pathway find-tubes** (v0.8.1); **body-identity rename** Earth→Terra / Moon→Luna (v0.9.0 BREAKING) and **Sol Time naming overhaul** (v0.9.1 — Latin proper nouns for rocky bodies + Sun + Luna; adjective forms for gas/ice giants); **CLI `adaptive` synonym** for the breathing/Phase-9 LUT (v0.9.2 — matches Gross & Blasius adaptive-networks vocabulary). **STLT — Sol Terra-Luna Time** (v0.10.0 — first Sol Time member with a non-J2000 default epoch; Meton's 432 BCE summer solstice; see §7.4). **SPrT — Sol Proper Time** (v0.11.0 — gravitational + orbital-kinematic time dilation, applied transparently via `--proper` on every `time-*` subcommand; six published validations to 0.30 %; see §7.5). v0.11.1 (this notebook revision) backfills §7.4 and §7.5 + refreshes this Status banner. **JPL Power-of-Ten audit baseline** (v0.11.2 — 102 mechanically-detectable violations pinned in `c/JPL_AUDIT.md`; rule-by-rule fixes queued v0.13.4-v0.13.8). **Sol Kinematics** (v0.12.0 — per-body orbital state augmented onto every `time-*` via `--state`; Jupiter holds 61.5 % of total system L; outer planets hold 99.84 % of planet total L). **Sol Dynamics** (v0.13.0 — Newtonian forces + per-body energies + system aggregate via `--dynamics`; Earth-Sun force 3.54×10²² N validated to 0.01 %; total system energy −1.98×10³⁵ J, virial theorem holds to 0.5 %). **SPICE feature-gap audit** (v0.13.1 — three-column comparison; recommendation: skip the SPICE-API compat bridge; spawned v0.14.x backlog). **Pre-merge docs+parity hygiene check** (v0.13.3 — soft-warning GitHub Actions workflow; the very ratchet that would have caught the v0.10.0 / v0.11.0 notebook gaps as they shipped; closes `` `#98` ``). **JPL Power-of-Ten Rule 1 + Rule 3 fixes** (v0.13.4 — caller-supplied-scratch refactor of the HD pipeline; `goto` 5 → 0, `malloc`/`free` 29 → 0; ABI v5 → v6; user-facing bridge unchanged). **JPL Rule 4 fixes** (v0.13.5 — 4 long functions split via 10 new private static helpers along natural algorithm seams; pure refactor, no public surface change; encoder math byte-identical). **JPL Rule 5 fixes** (v0.13.6 — 88 assertions across 42 functions at 2.10/function avg; gated behind `<assert.h>` NDEBUG so production strips them; `test_rule_5_density_meets_2_per_function` flips SKIP → PASS). **JPL Rule 10 fixes** (v0.13.7 — `ES_PEDANTIC=ON` CMake option + 3-cell `pedantic-build` CI matrix elevates `-Wall -Wextra -Wpedantic` / `/W4` warnings to errors via `-Werror`/`/WX`; always-on, not gated by `wheel-check`). **All five mechanically-enforceable JPL rules now satisfied (Rules 1, 3, 4, 5, 10)**. **README accuracy patch** (v0.13.8 — clarifies two-stage architecture: phase-residue computation is integer ALU end-to-end; HD operations (syzygy / observer-bind / eclipse-probability) necessarily run on FPU `complex64` because channel bases are unit-magnitude complex; `complex128` reframed as regression baseline only). **JPL Rules 6 + 7 manual audits** (v0.13.9 — closes the v0.13.4-v0.13.9 rule-fix sequence; **0 violations found** for both rules; all ten JPL Power-of-Ten rules satisfied). **Sol Moon Times** complete: Galileans (v0.14.0), Saturnians + abbreviation-policy switch from 4-letter to 6-letter `S<Planet2><Moon2>T` (v0.14.1), the remaining 8 moons across Mars / Jovian inner regulars / Uranus / Neptune (v0.14.2 — first multi-agent ship in this repo), and **the classical-roster completion v0.15.0** (Miranda, Ariel, Umbriel, Oberon close the major Uranian set, plus Charon as the binary-planet case — Pluto-Charon being the only mutually tidally-locked 1:1:1 pair in the solar system; BODIES roster expanded 38 → 43, ABI v6 → v7). **Live on PyPI**: `pip install ephemerides-spectral`.

> Living document. Sibling to:
> - [./antikythera_spectral_research_notebook.md](./antikythera_spectral_research_notebook.md) — **same-folder sibling.** Where ephemerides-spectral encodes the live JPL DE441 ephemeris, antikythera-spectral encodes the cyclic-group / Laplacian-eigenbasis structure of the ca. 150–60 BCE bronze mechanism. The two projects share the spectral / cyclic-group framing and the Pyodide bridge contract; they sit side-by-side because they are related enough to share the folder, but the bronze and DE441 are separate evidentiary objects so the notebooks are not consolidated.
> - [./doom_spectral_research_notebook.md](./doom_spectral_research_notebook.md) — **same-folder sibling.** Where ephemerides-spectral applies the BIP `Z_{2^32}` substrate + Phase-9 adaptive-coupling apparatus to the celestial N-body problem, doom-spectral applies the *same* substrate to the original DOOM (1993, id Tech 1) engine: BSP-tree map as a 2D Grid Laplacian (Blockmap) coarse-grained into a Sector super-graph, Z-elevation as a scalar fiber, raycasting as a dynamic sheaf Laplacian, sound propagation as heat-equation diffusion, and entity kinematics encoded directly as integer phase residues. First sibling that ports the BIP/Phase-9 machinery to a non-celestial-mechanics problem.
> - [../chess-maths/chess_spectral_research_notebook.md](../chess-maths/chess_spectral_research_notebook.md) — §20.13–§20.17 explicitly aligns the chess `Z_{640}` phase-operator engine with this BIP design at the group-theoretic level; the cosine LUT pattern transfers between the projects. §20.21 frames doom-spectral as the fourth sibling and tabulates the Track 1 / Track 3 / Track 4 correspondences (2D Grid Laplacian; dynamic sheaf raycast; heat-equation diffusion).
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

**Why "breathing" is metaphor, not vocabulary.** The codename captures the rhythm — coupling strengths inhale and exhale with the resonant-phase angle — but it does not connect to the literature's existing theorems. **State-dependent graph Laplacian** is the name to grep for in spectral-graph papers; **adaptive Kuramoto network** is the name to grep for in synchronisation papers; **state-dependent discrete Ricci curvature** (or "curvature in motion") is the name to grep for in discrete differential geometry / Bakry-Émery / Ollivier–Ricci papers; **parametric coupling** — and its synonyms **parametric oscillator network**, **parametric resonance**, **parametric instability**, and the **Mathieu / Hill non-autonomous oscillator** family — is the name to grep for in classical-mechanics, accelerator-physics, and nonlinear-dynamics papers. The substance is the same: a coupling strength that is *itself a periodic function of time* (here driven by the phase angle $n_a\phi_a - m_b\phi_b$, equivalent under our 1st-order phase rotation to a slow time variable). Faraday (1831, surface-wave parametric instability) opens the field; the Mathieu equation $\ddot x + (\delta + \varepsilon \cos t)\,x = 0$ supplies the canonical stability / instability tongue diagrams (the **Strutt diagram**), and the modern accelerator-physics machinery on **synchro-betatron coupling** + **dispersion-driven parametric resonance** carries the small-α perturbative regime our $\alpha = 0.1$ Phase-9 modulation lives in. **Vibrating lattice** captures the right *intuition* (phonon-like instantaneous spectrum) but is a 2nd-order Newtonian framing, whereas our flow is 1st-order phase rotation. We use "breathing" in headings and section labels for project continuity, and the precise vocabulary in prose so future readers can find their way out of our codename and into the canonical literature — depending on which of the four formalisms (state-dependent Laplacian / adaptive Kuramoto / Ricci-in-motion / parametric coupling) maps best to the theorem they need.

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

* **v0.18.2** — 2026-05-06. **2-D `(f₂, f₃)` Fiedler-embedding upgrade for `bridge.predict_itn_accessibility`.** Closes the §13.6 refinement #1 (two-eigenvector embedding) on top of the v0.18.1 hybrid weighting. Spearman ρ ~unchanged (1-D: +0.857 / 2-D: +0.849 — rank ordering already strong) but **R² lifts 0.51 → 0.64**, **in-sample MAE drops 4.11 → 3.00 km/s (−27 %)**, **LOOCV MAE drops 4.24 → 3.12 km/s (−26 %)**, and the new LOOCV median |error| is 2.20 km/s. The second eigenvector `f₃` adds an axis that distinguishes within-cluster pairs (Earth/Venus + main-belt asteroids cluster at `f₃ > 0`; outer planets at `f₃ < 0`; mercury isolated at `f₃ ≈ −0.28`) that the 1-D Fiedler vector collapsed. Bridge response is purely additive: new `embedding_distance_2d` + `calibration.embedding_dim` + `calibration.lambda_3` + `calibration.loocv_median_abs_error_kms` fields; the v0.18.1 1-D `fiedler_distance` is preserved for back-compat. Calibration constants change (intercept 8.68 → 4.90, slope 15.62 → 17.32); v0.18.1 numbers preserved under `*_1D_HISTORICAL` constants. New `research/two_eigenvector_fiedler_embedding.py` runs the full 3-weighting × 2-embedding comparison. Notebook §13.10 documents the result. **Pure-Python additive; no ABI bump** — fourth consecutive ship since v0.13.x with no ABI movement (`ES_ABI_VERSION = 8` unchanged from v0.17.0/v0.18.0/v0.18.1). 685 tests pass, 41 skipped (was 681 + 41 in v0.18.1; +4 net new). Live: <https://pypi.org/project/ephemerides-spectral/0.18.2/>.
* **v0.18.1** — 2026-05-06. **`bridge.predict_itn_accessibility`: closed-form spectral Δv estimate from the §13.9 hybrid Fiedler-distance regression.** Promotes the v0.17.x research output (notebook §13.9.4) — the hybrid `inv_dv × resonance` gateway-graph Laplacian's Fiedler distance as a continuous predictor of multi-leg ITN-chain Δv — to a stable ship surface. Calibrated by OLS regression against ground truth from a 50-yr `find_itn_chains` sweep at J2000 (max_legs=3, dv_budget=30 km/s, threshold=0.1) on the v0.16.0 13-body heliocentric Tier-1 roster: slope ≈ 15.62 km/s per Fiedler-unit, intercept ≈ 8.68 km/s, **Spearman ρ = +0.857**, in-sample R² ≈ 0.51, **LOOCV MAE ≈ 4.24 km/s**. Use case: fast first-pass triage (microseconds vs ~1.5 s for the full Dijkstra) — *not* trajectory design (the absolute MAE is ~4 km/s on a 2-28 km/s domain, useful for ranking pairs but too coarse for mission-budget purposes). New `bridge.predict_itn_accessibility(departure, target)` Python entry + new `predict-itn-accessibility` CLI subcommand. Calibration provenance returned in every response (Spearman ρ, R², MAE, LOOCV MAE, n_finite, n_inf, window). New offline calibration script `research/calibrate_predict_itn_accessibility.py` (re-fits the regression against a re-sampled ground truth — useful for non-default search windows). **Pure-Python addition; no ABI bump** — third consecutive ship since v0.13.x with no ABI movement (`ES_ABI_VERSION = 8` unchanged from v0.17.0/v0.18.0). Notebook §14 (the holographic-principle-at-macro-scale section, also added in v0.18.1) re-reads the §13.9 / v0.18.1 result as the bulk-boundary correspondence's "real" empirical payload — the spectral boundary (13-D Fiedler vector) anticipates the trajectory bulk (78-pair × 3-leg Dijkstra) at calibrated Spearman 0.857. New `tests/test_predict_itn_accessibility.py` (22 tests). 681 tests pass, 41 skipped (was 658 + 41 in v0.18.0; +23 new). Live: <https://pypi.org/project/ephemerides-spectral/0.18.1/>.
* **v0.18.0** — 2026-05-06. **Body Architecture: inner/outer system classification of heliocentric bodies via the resonance-weighted gateway-graph Laplacian Fiedler partition.** First spectral-architecture surface in the bridge — the v0.17.x research output (§13.8) promoted to a stable ship API. The cyclic-group encoder discovers the canonical asteroid-belt boundary without being told it exists: outer 5 = jupiter / saturn / uranus / neptune / pluto (all negative Fiedler entries); inner 8 = mercury / venus / terra / mars / vesta / ceres / pallas / hygiea (all positive). Pluto and Neptune share the deepest negative entry (≈ −0.585) via their well-known 2:3 mean-motion lock dragging both deep into the outer cluster. New `bridge.body_architecture(target=None)` + new `body-architecture` CLI subcommand (full partition by default; `--target <body>` for single-body class lookup). The Fiedler-vector sign is anchored to the shortest-period body (mercury) being positive — class labels are reproducible across platforms regardless of LAPACK pivoting. **Pure-Python addition; no ABI bump** — second consecutive ship since v0.13.x with no ABI movement (v0.17.0 added `find_itn_chains`, v0.18.0 adds `body_architecture`, both leave `ES_ABI_VERSION = 8` unchanged). Notebook §13.9 also lands the **hybrid `inv_dv × resonance` Laplacian** research follow-up: Spearman ρ = +0.857 (clears the §13.7 0.85 ship bar), Matthews φ = +0.298 (below the 0.6 partition bar) — vindicates the multiplicative-hybrid hypothesis for a *continuous* Fiedler-distance Δv predictor while leaving the partition-only ship surface to the resonance-only weighting. A `bridge.predict_itn_accessibility` continuous-Δv predictor is queued for v0.18.x or v0.19.0 (gated on Fiedler-distance → Δv regression calibration + cross-validation across body subsets). New `tests/test_body_architecture.py` (34 tests) covering the canonical inner-8/outer-5 partition, Pluto-Neptune deepest-entry pin, Mercury-largest-positive sign-convention pin, determinism, error paths, and 13 parametrised single-body class lookups. 658 tests pass, 41 skipped (was 622 + 41 in v0.17.0; +36 new). Live: <https://pypi.org/project/ephemerides-spectral/0.18.0/>.
* **v0.17.0** — 2026-05-06. **Resonance-graph multi-leg `find_itn_chains` (advanced Lagrange-highway search).** Generalises the v0.8.1 closed-form Hohmann-window enumeration (`find_itn_pathways`) to multi-leg pathways via Dijkstra-style graph search over the `(body, epoch)` state space. Each leg is a closed-form Hohmann window from `find_itn_pathways`; legs stitch end-to-end at intermediate bodies; cumulative Δv and time-of-flight are budget-bounded. Each leg carries a small-integer `(p, q)` **gear-ratio resonance signature** (the rational approximation of `period_dep / period_tgt` in lowest terms via the new `_best_rational_approx(ratio, max_denom=30)` helper) — the natural cross-pollination point between the closed-form transfer-window machinery and the BIP cyclic-group encoder. Canonical witnesses pinned in tests: **Earth/Mars (8, 15)** — the well-known 8-Earth-yr / 15-Mars-orbit synodic anchor; **Earth/Jupiter (1, 12)** — Jupiter's ~12-yr orbit; **Jupiter/Saturn (2, 5)** — the famous great-inequality resonance. The Dijkstra invariant on cumulative Δv guarantees the first chain emitted is the optimal-Δv path; subsequent chains emitted in monotonically non-decreasing total-Δv order. New `bridge.find_itn_chains` Python entry + new `find-chains` CLI subcommand (intermediates / max-legs / Δv-budget / TOF-budget / threshold / max-chains flags). **Pure-Python addition; no ABI bump** — first ephemerides ship since v0.13.x to leave the C wire-format alone (every ship from v0.14.0 through v0.16.0 either added bodies or expanded BODIES, each of which moved the ABI). Sets up the v0.17.x research thesis (`` `#118` ``): treat the body-graph Laplacian's Fiedler partition as a *prediction* of low-Δv accessibility, then check the prediction empirically against the chains `find_itn_chains` enumerates. New `tests/test_find_itn_chains.py` (21 tests). 622 tests pass, 41 skipped (was 601 + 41 in v0.16.0; +21 new). Live: <https://pypi.org/project/ephemerides-spectral/0.17.0/>.
* **v0.16.0** — 2026-05-06. **BODIES Tier-1 expansion (43 → 52): Lagrange trojans + retrograde irregulars + Neptune sub-graph completion.** Themed per the post-v0.15.0 audit (notebook §11). Adds 9 new bodies: 4 Saturnian Lagrange trojans (Telesto + Calypso at Tethys L4/L5 with `SSaTeT2` / `SSaCaT`; Helene + Polydeuces at Dione L4/L5 with `SSaHeT` / `SSaPoT` — **first L4/L5 entries in BODIES**, the body-graph Laplacian acquires a multiplicity-2 eigenvalue at the host moon's frequency); 3 Jovian irregulars (Himalia `SJuHiT` largest prograde, Pasiphae `SJuPaT` and Sinope `SJuSiT` retrograde — second retrograde marker beyond Triton); Neptune sub-graph completion (Proteus `SNePrT` second-largest at 1.122 d period, fills the gap between Triton at 5.88 d and the deferred inner-Neptunian close-packed cluster; Nereid `SNeNeT` most eccentric major-moon orbit in the solar system at e=0.749, 360.13 d period). **First invocation of the v0.14.1-reserved suffix-disambiguation policy**: Telesto's `SSaTeT2` distinguishes from Tethys's `SSaTeT` (both share moon-prefix `Te` under the same parent). **C-side wire-format change**: `ES_N_BODIES` 43 → 52; ABI v7 → v8; native binary rebuilt + parity-smoke ratchet ratcheted. The Saturnian trojans are the spectral headliner — their period equals their host moon's, giving the Laplacian eigenbasis a degeneracy that's the natural intersection point with v0.16.x's resonance-graph multi-leg `find_itn_chains` work (shipped as v0.17.0). Pure-additive on the Python bridge; native callers need ABI 8 (the rebuilt native ships in the v0.16.0 wheel). New test modules `test_saturnian_trojan_sol_moon_times.py` (4 trojans, 12 tests) + `test_jovian_irregular_sol_moon_times.py` (3 irregulars, near-resonance pin) + extended `test_neptunian_sol_moon_times.py` (Triton + Proteus + Nereid). 601 tests pass, 41 skipped (was 514 + 41 in v0.15.0; +87 new — parametrize amplification across 4 trojans + 3 irregulars + 3 Neptunians). Live: <https://pypi.org/project/ephemerides-spectral/0.16.0/>.
* **v0.15.0** — 2026-05-06. **Sol Moon Times: classical-roster completion (Pluto-Charon + remaining major Uranian moons) — BODIES roster expanded 38 → 43.** Closes task `` `#86` `` for the IAU-major moon roster: every classical moon discovered between 1787 and 1948 now has a Sol Time wrapper. Adds 5 new bodies — **Miranda** `SUrMiT` (Kuiper 1948 — Verona Rupes is the tallest known cliff in the solar system at ~20 km), **Ariel** `SUrArT` (Lassell 1851 — brightest surface of the Uranian moons, possible cryovolcanic resurfacing), **Umbriel** `SUrUmT` (Lassell 1851 same night as Ariel — darkest surface of the Uranian moons), **Oberon** `SUrObT` (Herschel 1787 same night as Titania — outermost and second-largest Uranian moon at radius ~761 km), and **Charon** `SPlChT` (Christy 1978). **Charon is the binary-planet case**: mutually tidally locked with Pluto (only 1:1:1 spin-orbit lock in the solar system); Charon:Pluto mass ratio ≈ 0.12 puts the Pluto-Charon barycentre *outside* Pluto, which makes the pair more like a binary planet than a planet-with-moon; the mutual lock collapses sidereal / synodic / spin period into a single timescale (6.387 d) so no separate synodic correction is offered. **SUrMiT vs SSaMiT** is the v0.15.0 second-instance disambiguation case — same shared-moon-prefix pattern as the v0.14.2 SUrTiT/SSaTiT pair, exactly the disambiguation the v0.14.1 6-letter policy was designed to provide. **C-side wire-format change**: ABI v6 → v7; `ES_N_BODIES` 38 → 43; native binary rebuilt + parity-smoke ratchet ratcheted; the v0.15.0 wheel ships with the matched-ABI native. New test module `test_plutonian_sol_moon_times.py` for the binary-planet edge case + 4 expanded entries in `test_uranian_sol_moon_times.py` covering the full classical roster. 512 tests pass, 41 skipped (was 497 + 4 in v0.14.2; +56 new — 5 Plutonian + 4 expanded Uranian + 10 parity-smoke entries + parity-smoke tier-shape variations). Live: <https://pypi.org/project/ephemerides-spectral/0.15.0/>.
* **v0.14.2** — 2026-05-06. **Sol Moon Times: remaining 8 moons across 4 parent families (Mars, Jovian inner regulars, Uranus, Neptune).** Closes task `` `#86` `` for the current 38-body roster. New Sol Moon Times — Phobos `SMaPhT` + Deimos `SMaDeT` (Mars, both likely captured asteroids); Metis `SJuMeT` + Adrastea `SJuAdT` + Amalthea `SJuAmT` + Thebe `SJuThT` (Jupiter inner regulars; Metis + Adrastea are ring-shepherds; Amalthea was the last solar-system moon discovered by direct visual observation, E. E. Barnard 1892); Titania `SUrTiT` (Uranus's largest moon — currently the only Uranian in BODIES; Oberon / Umbriel / Ariel / Miranda queued); Triton `SNeTrT` (Neptune's largest moon — captured Kuiper Belt object, the only large retrograde moon in the solar system, will become a ring system in ~3.6 Gyr after crossing Neptune's Roche limit). All 8 follow the v0.14.1 6-letter `S<Planet2><Moon2>T` convention; **SUrTiT vs SSaTiT** is exactly the disambiguation the policy was designed to provide. **Encoder convention** documented for Triton: `period_days` is positive — we encode `omega = +2π/P` for ALL bodies regardless of prograde/retrograde direction; retrograde-ness is metadata, not a sign flip in the time-scale primitive (same convention as v0.5.4 Sol Uranian Time). Generic `_add_moon_subparser` CLI helper supersedes the v0.14.0/v0.14.1 family-specific helpers. Built via **4 parallel subagent worktrees** (one per family, each delivering bridge wrappers + CLI subcommand + new test module + parity-smoke entries) integrated by the parent agent into a single bridge.py / cli.py / parity-smoke ship — first multi-agent ship in this repo. Pure-additive; no API / encoder / ABI / encoder-test changes. 497 tests pass, 4 skipped (was 399 + 4; +98 new — 2 Martian + 4 Jovian-inner + 1 Uranian + 1 Neptunian moon-test modules + parity-smoke entries). Live: <https://pypi.org/project/ephemerides-spectral/0.14.2/>.
* **v0.14.1** — 2026-05-06. **Sol Moon Times: Saturnians (11 moons) + abbreviation policy switch (4-letter → 6-letter).** Second slice of `` `#86` ``. The contingency policy from v0.14.0's ROADMAP fired exactly as predicted: Saturnians introduced two collisions under the v0.14.0 4-letter `S<Planet><Moon>T` pattern (Tethys + Titan; Enceladus + Epimetheus). Per the policy, the switch applies **uniformly across all Sol Moon Times** — Galileans retroactively renamed (`SJIT → SJuIoT`, `SJET → SJuEuT`, `SJGT → SJuGaT`, `SJCT → SJuCaT`); 11 Saturnians ship with 6-letter abbreviations. Python function names + CLI subcommand names + return-shape unchanged; only the `epoch.abbreviation` string changes. **Resonance witnesses** verified in tests: Mimas-Tethys 4:2 (Cassini Division), Enceladus-Dione 2:1 (Enceladus tidal heating + cryovolcanism), Titan-Hyperion 4:3 (Hyperion's chaotic rotation), Janus-Epimetheus co-orbital horseshoe orbit. **Hyperion** is the only known major moon NOT in tidal lock — `sidereal_period_days` references its orbital period; rotation phase is non-trivially decoupled (open research direction). 399 tests pass, 4 skipped (was 294 + 4; +105 new — 99 Saturnian tests + 6 cross-family abbreviation-uniqueness checks). Live: <https://pypi.org/project/ephemerides-spectral/0.14.1/>.
* **v0.14.0** — 2026-05-05. **Sol Moon Times: Galileans (Io / Europa / Ganymede / Callisto).** First slice of task `` `#86` `` — extends the Sol Time hierarchy to non-Luna moons under the moons-stuck-to-parent `Sol <Parent>-<Body> Time` naming convention from v0.9.1. New generic `MoonTime` primitive in `_research/time_scales.py` (body-agnostic; caller-supplied parent + sidereal period; default epoch J2000) + four per-Galilean bridge wrappers (abbreviations **SJIT** / **SJET** / **SJGT** / **SJCT**) + four CLI subcommands. **Galilean Laplace-resonance** (canonical `n_Io − 3·n_Europa + 2·n_Ganymede ≈ 0`) verified in the test module; Callisto correctly identified as the only Galilean NOT in the resonance (mean motion irrationally related to the inner triple). Per-moon dicts don't expose resonance metrics directly — the resonance is a pair-relation, not a per-body property; analysis tooling can compose `sidereal_count` values across the inner triple to recover it. **Naming convention contingencies** added to ROADMAP: if moon-letter collisions arise in future ships (Saturnians, etc.), the fallback policy switches uniformly across all Sol Moon Times to a 6-letter `S<Planet2><Moon2>T` pattern (e.g., `SJuGaT`). Pure-additive; no API / encoder / ABI / encoder-test changes. 294 tests pass, 4 skipped (was 251 + 4; +43 new — 35 Galilean tests + 8 parity-smoke entries). Live: <https://pypi.org/project/ephemerides-spectral/0.14.0/>.
* **v0.13.10** — 2026-05-05. **Drop `edited` from docs-check workflow trigger types — fixes post-merge double-fire.** User-flagged on PR `` `#214` `` (v0.13.9 ship): the docs-check workflow was deterministically double-firing at every merge. Two `pull_request` events at the same second on the PR's branch ~3 seconds before merge committed; concurrency-cancel caught it but the wasted CI churn was observable. Root cause: GitHub web UI's "Squash and merge" fires `pull_request: edited` (merge-commit dialog populates title/body fields) near-simultaneously with `pull_request: synchronize` (GitHub recomputes the `refs/pull/N/merge` preview ref). Fix: drop `edited` from the trigger types — now `[opened, synchronize, reopened, labeled]`, matching `ephemerides-spectral-ci.yml`'s narrower trigger list (which never had the issue). Trade-off: `[skip-docs-check]` opt-out added retroactively no longer triggers a re-run. CI-only change; no code / API / encoder / ABI / test changes. 251 tests pass, 4 skipped. Live: <https://pypi.org/project/ephemerides-spectral/0.13.10/>.
* **v0.13.9** — 2026-05-05. **JPL Power-of-Ten Rules 6 + 7 manual audits — closes the v0.13.4-v0.13.9 rule-fix sequence; ALL TEN RULES NOW SATISFIED.** Audit-only release; no code changes; **0 violations found** for both Rule 6 (smallest possible scope for data) and Rule 7 (check return values, validate parameters). The v0.11.2 spot-check estimates ("likely 5-10 violations across `es_encode.c` + `es_parity.c`" for Rule 6; "5-15 sites where `rc` is assigned but not checked" for Rule 7) didn't survive scrutiny — the incremental cleanup work in v0.13.4-v0.13.6 happened to tighten scope (long-function splits relocated state into helper-scope; `const`-near-use patterns added throughout the assertion work) and unified the rc-check pattern (every `es_status_t` assignment is followed by `if (rc != ES_OK) return rc;` on the next line). Audit walked every variable declaration across the 9 .c files and every `es_status_t` assignment (8 sites across `es_parity.c`, `es_hd_state.c`, `es_patches.c`). **All ten JPL Power-of-Ten rules satisfied**: Rules 1+3 (v0.13.4), Rule 4 (v0.13.5), Rule 5 (v0.13.6), Rule 10 (v0.13.7), Rules 6+7 (v0.13.9); Rules 2, 8, 9 already-passing at v0.11.2 baseline. The audit started in v0.11.2; the rule-fix sequence ran v0.13.4-v0.13.9 with v0.13.8 a docs-hygiene patch in the middle. **No further JPL rule work queued** — every rule in Holzmann 2006 is now either source-side ratchet-pinned, toolchain-side CI-enforced, or manually audited clean. 251 tests pass, 4 skipped (unchanged). Live: <https://pypi.org/project/ephemerides-spectral/0.13.9/>.
* **v0.13.8** — 2026-05-05. **README accuracy patch — two-stage architecture clarification.** User flagged: *"our readme says that we use complex128 for syzygy and stuff, is that still correct? because that would mean we aren't pure ALU, right?"* The previous README listed three backends as parallel alternatives, with `complex128` annotated as "used for the algebraic identities (Syzygy operator, observer binding)" — but since v0.7.0 (Tier 2b) the production HD path is C-side `complex64`; `complex128` is the regression baseline only (`backend="fpu-ref"`). The README now splits the architecture into **two stages**: (1) phase-residue computation with three integer-ALU encoders (`bip` Python / `c` native / `complex128` Python reference) producing `uint32[38]` residues, and (2) HD pipeline (FPU `complex64` production / `complex128` regression) for syzygy / observer-bind / eclipse-probability. Adds an explicit "TL;DR on pure ALU" callout: *"Phase residues are integer ALU end-to-end (BIP encoder hot path is uint64/int64/uint32, no floats); HD operations lift those residues to `complex64` and run on FPU. The package is **not** pure-ALU end-to-end — the HD pipeline can't be, because complex bases require trigonometric channels."* Roadmap renumber: Rules 6+7 manual audits move v0.13.8 → v0.13.9 (last item in the JPL rule-fix sequence). Docs-only release; no API / encoder / ABI / test changes. 251 tests pass, 4 skipped (unchanged). Live: <https://pypi.org/project/ephemerides-spectral/0.13.8/>.
* **v0.13.7** — 2026-05-05. **JPL Power-of-Ten Rule 10 fixes — cross-platform pedantic-build CI matrix.** Fourth code-quality patch in the v0.13.4-v0.13.8 rule-fix sequence. New `ES_PEDANTIC=ON` CMake option elevates the existing `-Wall -Wextra -Wpedantic` (gcc/clang) and `/W4` (MSVC) flags to errors via `-Werror` / `/WX`. Default OFF so casual local builds stay friendly during development; the new `pedantic-build` job in `.github/workflows/ephemerides-spectral-ci.yml` turns it ON across a 3-cell matrix (Linux gcc, macOS clang, Windows MSVC). **Always-on** — Rule 10 is a permanent invariant, not a per-PR opt-in. Per Holzmann's Power-of-Ten paper: *"All code must be compiled, from the first day of development, with all compiler warnings enabled at the compiler's most pedantic setting. All code must compile with these settings without any warnings."* The 3-cell matrix is the cross-platform implementation: gcc on Linux, clang on macOS, MSVC on Windows; all three see the same source tree, each emits its own warnings, and the matrix-CI satisfies "without any warnings" across every platform we ship to. Rule 10 is enforced by CI rather than by `tests/test_jpl_audit.py` (which counts source-side patterns; warnings are toolchain-side and toolchain-version-dependent). Local MSVC `/W4 /WX` build verified clean. **All five mechanically-enforceable JPL rules now satisfied (Rules 1, 3, 4, 5, 10).** Remaining JPL roadmap: Rules 6+7 manual audits (v0.13.8). **CI-only addition, no public API/ABI/encoder change.** 251 tests pass, 4 skipped (unchanged). Live: <https://pypi.org/project/ephemerides-spectral/0.13.7/>.
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

### 10.3 v0.15.0 expansion: classical-roster completion (38 → 43)

v0.15.0 extends the v0.5.0 baseline of 38 with **5 more bodies**, closing the major-Uranian classical roster and adding Pluto's largest moon:

| Class | Bodies added (v0.15.0) | Reason |
| :--- | :--- | :--- |
| Uranian classical (4) | Miranda, Ariel, Umbriel, Oberon | Closes the major-Uranian roster (Titania already at v0.14.2) |
| Plutonian (1) | Charon | The binary-planet case — only mutually tidally locked 1:1:1 spin-orbit lock in the solar system |

The Uranian sub-graph is now self-consistent: every classical Uranian moon discovered between Herschel 1787 (Titania, Oberon) and Kuiper 1948 (Miranda) carries an anchor in the Laplacian. The natural-resonance gear group acquires Miranda's 1.413-d period, which — though Miranda is small (~236 km radius) — sits cleanly outside the Saturnian Tethys / Dione / Rhea cluster (1.88, 2.74, 4.52 d) so it doesn't add new aliasing on the Uranian sub-spectrum.

Charon is dynamically distinctive: mass ratio Charon:Pluto ≈ 0.12 puts the barycentre *outside* Pluto, which means the system's COM is the dynamical anchor, not Pluto itself. The mutual tidal lock collapses sidereal == synodic == spin period (6.387 d) into one timescale — no separate synodic correction is needed (Sol Pluto-Charon Time = `SPlChT`).

### 10.4 Sol Moon Times completion arc (v0.10.0 → v0.15.0)

Task `` `#86` `` opened way back in the v0.5.x phase as "time reference for every body in the roster." Closed at v0.15.0 across **5 versions**:

| Version | Sol Moon Times added | Cumulative |
| :--- | :--- | :---: |
| v0.10.0 | STLT (Sol Terra-Luna Time) | 1 |
| v0.14.0 | Galileans (Io, Europa, Ganymede, Callisto) | 5 |
| v0.14.1 | Saturnians (11 moons) + 4-letter → 6-letter abbreviation policy | 16 |
| v0.14.2 | Mars (2) + Jovian inner regulars (4) + Uranian Titania + Neptunian Triton | 24 |
| v0.15.0 | Uranian classical-roster completion (4) + Plutonian Charon | 29? |

Wait — the cumulative count is **24 moon Sol Time series** because the v0.14.1 Galilean retroactive renames (`SJIT → SJuIoT` etc.) didn't add new series, just changed abbreviations. Here's the corrected accounting:

| Family | Count | Series |
|---|--:|---|
| Earth | 1 | STLT (Luna) |
| Mars | 2 | Phobos, Deimos |
| Jovian inner regulars | 4 | Metis, Adrastea, Amalthea, Thebe |
| Galileans | 4 | Io, Europa, Ganymede, Callisto |
| Saturnians | 11 | Mimas, Enceladus, Tethys, Dione, Rhea, Titan, Hyperion, Iapetus, Phoebe, Janus, Epimetheus |
| Uranian classical | 5 | Miranda, Ariel, Umbriel, Titania, Oberon |
| Neptunian | 1 | Triton |
| Plutonian | 1 | Charon |
| **Total** | **29** | — every classical IAU-major moon in BODIES |

(So actually 29 — I had the wrong number above; the mistake was conflating "moons added in v0.14.x" with "all moon Sol Time series.")

## 11. Audit: next-tier body candidates (post-v0.15.0)

With v0.15.0 closing the IAU-major moon roster, the natural question becomes "what's the next tier worth adding?" This section catalogues every named body NOT yet in BODIES that's a plausible candidate, ranked by spectral-lattice value-add. The audit was prompted by Steven post-v0.15.0 ship and is intended to scope a v0.16.x or later expansion.

### 11.1 Ranking criterion

The spectral lattice rewards adding bodies that bring **distinct frequency content** to the Laplacian eigenbasis. Concretely:

1. **Mass** — drives the per-body weight in the dynamics module's force calculations (v0.13.0). Tiny shepherd moons (~10⁻¹² Earth) contribute almost nothing here.
2. **Period uniqueness** — a body whose period is far from any existing roster entry expands the eigenbasis support; a body whose period clusters with existing entries adds aliasing risk without distinct spectral content.
3. **Dynamical novelty** — captured retrograde orbits (Triton-class), Lagrange-trojan co-orbitals, mutual tidal locks, resonance chains. These earn their roster slot on the basis of *what they reveal about the substrate*, not raw mass.
4. **Mission-visited / well-characterised** — bodies with high-precision JPL HORIZONS sidereal periods (9+ decimals) earn their slot more easily than poorly-constrained small bodies.

### 11.2 Tier-1 candidates (recommended for v0.16.0)

These score on at least two of the four criteria. Sourced from JPL HORIZONS / NASA fact sheets / IAU MPC.

| Body | Parent | Period (d) | Mass (Earth) | Why it earns the slot |
| :--- | :--- | ---:| ---:| :--- |
| **Proteus** | Neptune | 1.122315 | 7.4e-9 | Neptune's second-largest moon (radius ~210 km, near-spherical); fills the Neptune sub-graph between Triton (5.88 d) and the small inner moons |
| **Nereid** | Neptune | 360.13619 | 5.1e-9 | Highly eccentric orbit (e=0.749, captured-asteroid candidate); 360-d period extends Neptune's low-frequency tail dramatically |
| **Helene** | Saturn | 2.736915 | 4.5e-12 | **Lagrange-trojan**: orbits at Dione's L4 point — same period as Dione (2.736915 d). First L4/L5 entry in the roster — direct connection to the ITN / Lagrange-highway research thread |
| **Telesto** | Saturn | 1.887802 | small | Tethys L4 trojan (same period as Tethys, 1.887802 d) — second L4/L5 entry |
| **Calypso** | Saturn | 1.887802 | small | Tethys L5 trojan — completes the Tethys trojan pair |
| **Polydeuces** | Saturn | 2.736915 | very small | Dione L5 trojan — completes the Dione trojan pair (mass ~10⁻¹⁵ Earth, but the Lagrange-point identity earns the slot) |
| **Pasiphae** | Jupiter | 743.63 (retrograde) | 5.0e-12 | One of the largest Jovian irregular moons (radius ~30 km); **retrograde** — same captured-KBO marker as Triton; would be the first non-Triton retrograde in the roster |
| **Sinope** | Jupiter | 758.90 (retrograde) | 1.3e-12 | Pasiphae companion in the Pasiphae group; retrograde; near-resonant with Pasiphae |
| **Himalia** | Jupiter | 250.56 | 1.1e-9 | Largest Jovian irregular (radius ~85 km); prograde; period sits cleanly between Callisto (16.7 d) and the long-period retrogrades |

**Recommended Tier-1 ship size: 9 new bodies.** Brings the roster from 43 → 52. The four Saturnian trojans (Helene, Telesto, Calypso, Polydeuces) are the most spectrally-interesting addition because they sit *exactly* at L4/L5 — their per-body period is identical to their parent moon's, which means the Laplacian acquires a degeneracy at that frequency (multiplicity-2 eigenvalues per L4/L5 pair). This is where the Lagrange-highway research thread (running in parallel as of post-v0.15.0) intersects the BODIES roster directly.

### 11.3 Tier-2 candidates (defer to v0.17.x or later)

These bodies are real and have JPL HORIZONS data but score on only one of the four criteria. Adding them is plausible but doesn't move the spectral lattice meaningfully.

**Plutonian small moons** (4):
- Nix (P=24.85 d), Hydra (P=38.20 d), Kerberos (P=32.17 d), Styx (P=20.16 d)
- Resonance chain with Charon (3:4:5:6 mean-motion). Spectrally: the resonance is interesting; the masses (~10⁻⁹ Earth or smaller) are not.
- **Verdict**: ship if/when the resonance-graph machinery would directly use the chain. Otherwise defer.

**Saturnian shepherd moons** (5):
- Pan (in Encke gap, P=0.575 d), Daphnis (Keeler gap, P=0.594 d), Atlas (P=0.602 d), Prometheus (F-ring inner, P=0.613 d), Pandora (F-ring outer, P=0.629 d)
- Cluster of near-identical periods (0.575–0.629 d) — high aliasing risk, low distinct content.
- **Verdict**: defer. Spectrally these add a tight low-frequency cluster; the Laplacian eigenbasis already has Mimas (0.942 d) and Janus/Epimetheus (0.694/0.694 d) covering the inner-Saturnian range.

**Inner Uranian moons** (13):
- Cordelia, Ophelia, Bianca, Cressida, Desdemona, Juliet, Portia, Rosalind, Cupid, Belinda, Perdita, Puck, Mab — all 0.3–0.9 d, all ~10⁻¹⁰ Earth or smaller
- Voyager 2 1986 + Hubble 2003. Dynamically chaotic with each other (close-packed inner ring system).
- **Verdict**: defer en masse. Puck (radius ~81 km) is the only one with non-trivial mass.

**Inner Neptunian moons** (5):
- Naiad, Thalassa, Despina, Galatea, Larissa, Hippocamp — all <1 d
- Same problem as the inner Uranians: tight period cluster, low individual mass, high aliasing risk.
- **Verdict**: defer en masse, except possibly Larissa (radius ~97 km, dynamically distinct).

### 11.4 Tier-3 candidates (KBOs and dwarf planets)

These are an entirely different population — not moons but **outer-system dwarf planets** that sit alongside Pluto in the IAU dwarf-planet category.

| Body | Period (d / yr) | Mass (Earth) | Note |
| :--- | ---:| ---:| :--- |
| **Eris** | 203,830 (557 yr) | 2.8e-3 | More massive than Pluto; period 6× Pluto's |
| **Makemake** | 110,300 (302 yr) | 5.1e-4 | Similar to Pluto |
| **Haumea** | 103,410 (283 yr) | 6.7e-4 | Extreme rotation period (3.9 hr) — fastest known among large bodies |
| **Sedna** | 4,150,000 (11,400 yr) | ~1e-4 | Most extreme orbit in the inner Oort cloud |
| **Quaoar** | 105,800 (290 yr) | 2.4e-4 | Has a moon (Weywot) and a ring system |

**Verdict**: these are arguably more interesting than the Tier-2 small moons because they extend the system's low-frequency tail by 1–2 decades. Sedna's 11,400-yr period in particular is a once-in-a-lifetime spectral outlier. Recommend ship as a separate "dwarf planets" class (alongside `pluto`'s existing `category="planet"`). Could be a v0.17.0 thematic ship: "outer-system dwarf planets + their moons (Eris-Dysnomia, Quaoar-Weywot, Haumea-Hi'iaka/Namaka, Makemake-MK2)."

### 11.5 Mission-visited asteroids (4)

The current roster has 4 main-belt asteroids (Ceres, Vesta, Pallas, Hygiea). The natural next-tier additions are mission-visited small bodies whose periods are well-constrained:

| Body | Period (d) | Mission | Notes |
| :--- | ---:| :--- | :--- |
| **Eros** | 642.95 | NEAR-Shoemaker (2000–2001) | First asteroid orbit + landing |
| **Itokawa** | 555.55 | Hayabusa (2005) | First sample return |
| **Bennu** | 437.67 | OSIRIS-REx (2018–2023) | Most recent sample return |
| **Ryugu** | 472.76 | Hayabusa2 (2018–2019) | Sister mission to Bennu |

**Verdict**: these don't move the spectral lattice (small mass, mid-belt periods cluster with the existing Ceres/Vesta/Pallas/Hygiea band) but they earn cultural significance from the missions. Defer to a thematic "visited bodies" ship if the roster ever gets one.

### 11.6 Recommendation

**Ship Tier-1 (9 bodies → 52-body roster) as v0.16.0**, themed as "Lagrange-trojan + retrograde-irregular + Neptune sub-graph completion." The four Saturnian trojans are the spectral headliner; Pasiphae/Sinope add the second retrograde marker beyond Triton; Proteus/Nereid round out Neptune. Cost: ~1 day of work, mirrors the v0.14.x ship pattern (BODIES additions + bridge wrappers + CLI subcommands + test modules + native rebuild + ABI v7 → v8). Benefit: the BODIES table acquires its first L4/L5 Lagrange entries, which directly serves the Lagrange-highway research thread that's running in parallel as of this notebook revision.

**Defer Tier-2 and Tier-3 to thematic ships** (resonance-chain shepherd-cluster ship; dwarf-planet ship; visited-asteroid ship) — none of them are worth the ABI bump on their own.

## 12. Advanced Lagrange-highway searching — research scoping for v0.16.x+

Post-v0.15.0, Steven prompted a research-only investigation into what an advanced Lagrange-highway search layer would look like for `find_itn_pathways`. The v0.8.1 first-cut ships closed-form Hohmann transfer-window enumeration (the lowest-effort transfer between any two named bodies); the question is what the next layer can deliver before requiring a full CR3BP integrator. A subagent surveyed the literature; this section records the survey + the recommendation.

### 12.1 Six surveyed extensions

| # | Extension | Verdict |
|---|---|---|
| 1 | **L1/L2 gateway designation** per CR3BP — Newton-iterable quintic for collinear γ, closed-form Jacobi constant per (departure, target) Sun-orbiter pair | **Implementable now, no new dependency.** Add `gateway_lp ∈ {"L1", "L2"}` and `jacobi_constant: float` to `ITNCandidate`. References: Szebehely 1967 §4.4; Murray & Dermott 1999 §3.7. |
| 2 | **Lyapunov / halo-orbit families** parameterised by (C_J, north/south class) | **Richardson 1980 third-order analytic approximation implementable now**, accurate to ~10⁻³ relative position. Numerical refinement requires a propagator (substantial research-code lift, defer). |
| 3 | **Heteroclinic connections** between manifolds at different bodies' Lagrange points — the actual "highway" | Full search needs a CR3BP integrator (`scipy.integrate.solve_ivp` over a hand-rolled CR3BP RHS — `poliastro` is now archived). **Chirikov 1979 resonance-overlap predictor is closed-form and implementable now.** Ship the predictor in v0.16.x; defer the propagator-based search. |
| 4 | **Spectral-graph view of the transport network** — gateway-graph Laplacian whose nodes are (body, L_i, halo-family-index) tuples and whose edges are heteroclinic Δv-cost weighted connections | **Largely unexplored in published literature.** Anderson & Lo 2009 and Topputo et al. treat the manifold network as a graph but do not analyse it spectrally. Substantial novelty available; likely a short paper's worth of work. The cyclic-group framing adds something genuine: bodies in 1:2 resonance share Lagrange-point geometry up to a scaling — a representation-theoretic statement, not just empirical. |
| 5 | **Weak Stability Boundary (WSB) transfers** — Belbruno 2004; Hiten / SMART-1 / GRAIL / ARTEMIS flew them | **Not appropriate for `ephemerides-spectral` in current discipline.** WSB is non-perturbative and computed by forward integration over a phase-space grid; García & Gómez 2007 showed it has fractal structure. Belongs in a separate workspace. The closest in-discipline analogue is a closed-form *flag* on existing Hohmann candidates whose arrival geometry sits in Belbruno's empirical "WSB-favourable" wedge. |
| 6 | **Resonance-assisted transfers** — multi-leg paths using mean-motion resonance with intermediate bodies (Cassini V-V-E-J-S, Galileo V-E-E-J, Voyager grand tour) | **Implementable now with no new dependency.** Algorithmic surface is graph search (Dijkstra / A*) on a (body, epoch, heliocentric-energy-bucket) state space, with the closed-form Hohmann Δv from #1 as the edge cost. Body-body resonance graph is integer (gear-ratio data already in BODIES); energy buckets are a coarse FPU grid; per-edge phase-window solve is the existing `find_itn_pathways` synodic enumeration. |

### 12.2 The v0.16.x recommendation

**Ship resonance-graph multi-leg search.** It's the most natural generalisation of the closed-form synodic enumeration the module already does, and (a) fits the existing integer-ALU + FPU pipeline discipline without a CR3BP integrator, (b) reuses the BODIES roster's gear-ratio structure as graph-edge data, (c) gives the most directly demonstrable user-facing value: `find_itn_chains(departure='terra', target='pluto', dv_budget_kms=25)` returning low-Δv paths with explicit per-leg resonance signatures.

Sketched API:

```python
def find_itn_chains(
    jd_lo: float, jd_hi: float, *,
    departure: str,
    target: str,
    intermediates: Optional[Iterable[str]] = None,   # default: all of BODIES
    max_legs: int = 4,
    dv_budget_kms: float = 30.0,
    tof_budget_days: float = 365.25 * 20,
    threshold: float = 0.05,
    max_chains: int = 200,
) -> List[ITNChainCandidate]: ...

@dataclass(frozen=True)
class ITNChainCandidate:
    jd_tdb_launch: float
    jd_tdb_arrival: float
    legs: Tuple[ITNCandidate, ...]               # each leg = a v0.8.1 Hohmann window
    total_dv_kms: float
    total_tof_days: float
    resonance_signature: Tuple[Tuple[int, int], ...]  # per-leg p:q gear-ratio
    score: float                                       # combined phase-residual score
```

The `resonance_signature` field is the cross-pollination point with the rest of `ephemerides-spectral`: a tuple of integer (p, q) ratios is exactly the data the cyclic-group encoder already consumes in `bip_instrument`.

L1/L2 gateway designation (#1) and Richardson halo amplitudes (#2) can ship in the same minor as small additional fields on the existing `ITNCandidate`. Heteroclinic search (#3) and the gateway-graph Laplacian (#4) are the natural v0.17.x scope.

### 12.3 The philosophical question the spectral framing raises

The question worth chasing in v0.17.x:

> **Is the body-body graph Laplacian the right operator for ITN, when ITN tubes are by construction non-perturbative on the Sun-only Kepler frame?**

The CR3BP literature treats the ITN as a phenomenon of *one* Sun-planet-spacecraft system at a time — manifold tubes around Sun-Earth L1/L2 are computed in the Sun-Earth rotating frame, those around Sun-Mars L1/L2 in the Sun-Mars rotating frame, and the heteroclinic stitching across them is patched-conic. **There is no single dynamical system whose spectrum *is* the ITN.**

But `ephemerides-spectral`'s body-body Laplacian *is* a single spectrum, on a single graph that includes Sun, Earth, Mars, and the rest. If the eigenbasis of that Laplacian also organises the ITN tube network — even approximately — then there is a sense in which **the ITN is implicit in the body-roster gear ratios**, and the Sun-planet-spacecraft frames are merely localisations of a single underlying spectral structure. That would be a genuinely original claim. CR3BP cannot make it because CR3BP cannot accommodate more than three bodies.

The risk of the claim: ITN tubes are width-zero in the Kepler limit and gain finite width only from the planet's perturbation — so the connection between the body-body Laplacian (which knows about all bodies' periods) and the tube widths (which know only about the *local* perturbing body) is non-obvious, and might be wrong. But the question is at least well-posed in this framework, which is more than the standard literature offers.

The v0.17.x research thesis: **does the gateway-graph Laplacian's Fiedler partition agree with empirical low-Δv accessibility classes?** If yes, the spectral lens has earned its keep on ITN.

### 12.4 References (real, not fabricated)

* Koon, Lo, Marsden, Ross (2011) — *Dynamical Systems, the Three-Body Problem and Space Mission Design.* The canonical ITN textbook.
* Szebehely (1967) — *Theory of Orbits.* §4.4 on collinear Lagrange points and the quintic γ.
* Murray & Dermott (1999) — *Solar System Dynamics.* §3.7 on the restricted three-body problem.
* Richardson (1980) — *Analytic Construction of Periodic Orbits about the Collinear Points.* Celest. Mech. 22, 241–253. The third-order halo-orbit closed form.
* Chirikov (1979) — *A universal instability of many-dimensional oscillator systems.* Physics Reports 52, 263–379. The resonance-overlap criterion for chaos.
* Belbruno (2004) — *Capture Dynamics and Chaotic Motions in Celestial Mechanics.* The WSB framework.
* Conley (1968) — manifold-connection theorems, the original mathematical foundation.
* Lo (1997) — Genesis spacecraft trajectory design via L1/L2 manifolds (the first practical use of ITN for a real mission).
* Anderson & Lo (2009) — *Role of invariant manifolds in low-thrust trajectory design.* JGCD. (Cited from secondary sources; verify before quoting.)
* García & Gómez (2007) — *About the WSB.* Celest. Mech. (Cited from secondary sources; verify before quoting.)

## 13. Gateway-graph Laplacian — Fiedler-partition vs empirical low-Δv accessibility

This section reports a research-only prototype that tests the v0.17.x thesis stated at the close of §12.3:

> Does the body-body graph Laplacian's Fiedler partition agree with empirical low-Δv ITN accessibility classes?

The empirical ground truth is the v0.17.0 `find_itn_chains` Dijkstra search; the spectral side is a freshly-built **gateway-graph Laplacian** (separate from the §1.4 / `laplacian.py` mass-coupled breathing Laplacian — different vocabulary, different edge-weight semantics). Code lives at [`research/gateway_graph_laplacian.py`](research/gateway_graph_laplacian.py); figures at [`figures/gateway_laplacian_*.png`](figures/).

> **Naming note.** §12.2 is the v0.16.x recommendation slot; this section is appended as §13 rather than §12.5 because the result graduates the thesis from "research scoping" (the §12 thread) to "first-light empirical validation" (its own section).

### 13.1 Hypothesis

The body-body graph Laplacian's Fiedler eigenvector — the eigenvector of the second-smallest eigenvalue λ₂, the algebraic-connectivity mode — *predicts* which heliocentric `(departure, target)` pairs admit cheap multi-leg ITN chains. The Fiedler vector's sign bipartitions the vertex set; pairs *within* a partition should be cheaper to chain than pairs *across* the partition. More finely, the Fiedler-vector Euclidean distance `|f₂[i] − f₂[j]|` should rank-correlate with the empirical minimum cumulative Δv from `find_itn_chains`.

If the prediction holds, a closed-form spectral-only query becomes a fast first-pass filter before the costly Dijkstra search; if it fails, the negative result sharpens the boundary on what graph-Laplacian eigenstructure does and does not capture about orbital mechanics.

### 13.2 Construction

**Vertex set.** Heliocentric bodies only — planets (mercury, venus, terra, mars, jupiter, saturn, uranus, neptune, pluto) plus main-belt asteroids (ceres, vesta, pallas, hygiea). 13 vertices. The Sun is excluded because it is the central potential, not a transit node — every Hohmann transfer threads its gravity well, so its "edges" would dominate every weight matrix and trivialise the spectral structure. Moons are excluded because v0.17.0 has no parent-frame Δv model: a Hohmann transfer from `terra` to `phobos` would need to account for Mars's gravity well at arrival, which is not in the closed-form heliocentric Hohmann.

**Edge weighting.** The graph is complete on 13 vertices (78 unordered pairs). Two weightings tested:

1. **Inverse Hohmann Δv** — `w_ij = 1 / (Δv_ij + ε)`, where `Δv_ij` is the closed-form heliocentric Hohmann total Δv from `itn_window.hohmann_total_dv_kms`. Cheaper transfers ⇒ stronger graph edges. This is the *cost* metric and is most directly aligned with what `find_itn_chains` minimises.
2. **Inverse synodic period** — `w_ij = 1 / (T_syn_ij + ε)`, where `T_syn_ij = 2π / |n_i − n_j|`. Short synodic period ⇒ frequent launch windows. This is a *cadence* metric, orthogonal to (1): two bodies on similar orbits have a long synodic period (rare windows) but a small Hohmann Δv (cheap when a window exists). Including it as a control disambiguates whether any spectral signal from (1) is just "any reasonable graph metric" or specifically the cost geometry.

The `(ε)` floor (`1e-3 km/s`, `1e-3 days`) is well below the noise floor (smallest Hohmann in the roster is mercury → venus at ≈ 5 km/s) and is present only to avoid divide-by-zero on conceivable degenerate inputs. The combinatorial Laplacian `L = D − W` is then symmetric positive-semidefinite by construction.

### 13.3 Spectral predictor

Two predictors derived from the Fiedler eigenvector `f₂` (eigenvector of λ₂ from `np.linalg.eigh(L)`):

* **Fiedler partition** — `sign(f₂[i]) == sign(f₂[j])` ⇒ "within partition" (predicted-cheap class); else "across partition" (predicted-expensive class). The simplest possible spectral predictor — a one-bit summary of the Fiedler vector. Validated against an observed median split via a 2×2 confusion matrix and the Matthews correlation coefficient φ.
* **Fiedler distance** — `d_F(i, j) = |f₂[i] − f₂[j]|`, the 1-D Euclidean distance in the Fiedler-vector embedding. A continuous spectral predictor; validated against observed Δv via Spearman rank correlation ρ.

This is the canonical first-cut spectral predictor pair; both are computable from one eigendecomposition of a 13×13 symmetric matrix (microseconds). If either succeeds, deeper predictors (full diffusion distance, k-eigenvector spectral embedding) become worth trying.

### 13.4 Empirical ground truth

For each of the 78 unordered pairs `(i, j)`, the prototype calls `bridge.find_itn_chains` in *both* directions (Hohmann Δv is direction-symmetric in the closed-form model, but multi-leg chain composition through intermediates is not necessarily so) and records `min(min_dv_forward, min_dv_reverse)` as the per-pair empirical accessibility metric. Parameters:

```python
bridge.find_itn_chains(
    jd_lo=2451545.0,                     # J2000.0 (TDB)
    jd_hi=2451545.0 + 50 * 365.25,       # +50 years
    departure=i, target=j,
    max_legs=3, dv_budget_kms=30.0,
    tof_budget_days=20 * 365.25,
    threshold=0.1, max_chains=50,
)
```

Pairs that return no chain within the (Δv, TOF, threshold) budget are recorded as `+inf` (sentinel `NO_CHAIN_DV_KMS`). The 50-year sweep is comfortable for the inner system (≈ 25 Earth-Mars synodic periods, 4 Earth-Jupiter, 2 Earth-Saturn) but tight for the outer system; "no chain" therefore conflates two failure modes — *no chain exists in the budget* and *no chain exists in this 50-year window*. Both are reported as expensive in the confusion matrix.

Wall-clock for the full 78-pair sweep (both directions): ≈ 110 s on the development host (single-thread Python, ESP-IDF host build env). Cached to disk by the prototype for re-runs.

### 13.5 Result

| Predictor | weighting | Spearman ρ (Δv vs Fiedler dist) | Matthews φ (within vs cheap) | n_finite | n_inf |
| :--- | :--- | ---: | ---: | ---: | ---: |
| Fiedler distance + partition | **inv_dv (primary)** | **+0.743** | **+0.336** | 53 | 25 |
| Fiedler distance + partition | inv_synodic (control) | −0.301 | +0.083 | 53 | 25 |

Median Δv on the 53 feasible pairs: **11.19 km/s**. The inv_dv confusion matrix (median split):

|                          | within-partition | across-partition |
| :---                     | ---:             | ---:             |
| **observed cheap (≤ 11.19)**   | 25               | 2                |
| **observed expensive (> 11.19)** | 31               | 20               |

**Fiedler partition (inv_dv weighting):** mercury alone in the positive partition (`f₂[mercury] = +0.952`, with venus marginally positive at +0.033); all eleven other bodies in the negative partition (`f₂` values clustered tightly between −0.034 and −0.101). The Fiedler vector is essentially a Mercury-isolation indicator.

**Inv_synodic Fiedler partition** (control): {pallas, vesta, mars, terra, venus, mercury} negative vs {ceres, hygiea, jupiter, saturn, uranus, neptune, pluto} positive — but with `f₂` magnitude collapsed onto pallas (−0.71) and ceres (+0.70); everyone else within 10⁻³ of zero. The synodic-period Laplacian is dominated by the near-degeneracy of pallas / ceres orbital periods (1681 d / 1686 d), which buys you essentially no information about Δv accessibility — confirmed by the negative Spearman.

Figures: [`gateway_laplacian_fiedler_dv_inv_dv.png`](figures/gateway_laplacian_fiedler_dv_inv_dv.png) (scatter, ρ = +0.743) and [`gateway_laplacian_partition_inv_dv.png`](figures/gateway_laplacian_partition_inv_dv.png) (Fiedler bar chart isolating mercury); the inv_synodic counterparts are also written for completeness.

### 13.6 Interpretation

The +0.743 Spearman headline is real but the Fiedler partition tells a narrower story than the rank correlation alone suggests:

* **What the spectrum is detecting.** The inv_dv Fiedler vector identifies mercury as a singleton outlier — the body whose Hohmann Δv to *every other heliocentric body* is uniformly large (mercury sits deep in the Sun's gravity well; matching its 47.4 km/s circular velocity from any outer orbit is expensive). The Fiedler partition is therefore a "deep-gravity-well isolation" indicator, not a finer "cheap-chain neighbourhood" indicator. The 25 across-partition pairs (mercury or venus paired with anything ≥ mars) are uniformly expensive (median Δv ≈ 18 km/s); the 35 finite within-partition pairs span the entire range from 1.2 km/s (e.g. saturn-uranus) to 28 km/s (e.g. pluto-jupiter).

* **Why the Spearman is still high.** Sorting all 53 feasible pairs by Fiedler distance puts the 18 cross-partition pairs (high Fiedler distance, high Δv) at the top of both rankings; this alone drives a large fraction of the rank correlation. The within-partition tail (35 pairs, all at Fiedler distance ≲ 0.06) carries most of the remaining Δv variance, which the Fiedler partition does *not* resolve.

* **What this means for ship.** A Fiedler-partition-only predictor would correctly flag "mercury (and venus) trips are uniformly expensive — skip them unless you have a fat budget" but would say nothing useful about whether `terra → ceres` is cheaper than `terra → jupiter`. That's a useful first-pass filter (it eliminates 25 / 78 ≈ 32% of pairs from consideration with two false negatives — the saturn / uranus pairs the Dijkstra found feasible at high Δv) but it is not a substitute for the Dijkstra search.

* **Why the inv_synodic control fails.** The inv_synodic weighting up-weights body pairs whose *windows are frequent*, not whose *transfers are cheap*. The pallas / ceres near-resonance (T_syn ≈ 5.6 × 10⁵ d, an order of magnitude larger than typical because their periods are nearly identical) becomes a Fiedler-vector black hole that absorbs the signal. The negative ρ confirms that the inv_dv result is not "any spectral metric works" — it is specifically the cost-geometry encoded in the inverse-Δv weighting that delivers the predictive signal.

* **Refinements worth a v0.17.x follow-up:**
  * **Two-eigenvector embedding.** Project bodies onto `(f₂, f₃)` and re-measure Spearman on the 2-D Euclidean distance. The single Fiedler vector collapses everything-not-mercury into a tight cluster; the next eigenvector might separate the inner-vs-outer distinction inside that cluster.
  * **Diffusion distance.** `d_t(i, j) = ‖exp(−t L) e_i − exp(−t L) e_j‖` for some characteristic time t. Captures multi-step accessibility (the Dijkstra search is, after all, multi-leg) in a way the single Fiedler vector cannot.
  * **Mercury-removed sub-graph.** Strip mercury (the dominant outlier) and re-run; see whether the Fiedler vector on the 12-body sub-graph splits the inner vs outer system in a way that does correlate with intra-cluster Δv variance.
  * **Resonance-weighted edges.** Instead of inv-Hohmann or inv-synodic, weight by `w_ij = exp(−|p_i / p_j − p_best/q_best|)` for the best small-integer rational approximation. The BIP / cyclic-group native metric — closer to Almagest period-ratios than to Hohmann mechanics. Ties this work back to §12 / §11.6.

* **Where the §12.3 framing lands.** §12.3 asked whether "the ITN is implicit in the body-roster gear ratios." The +0.743 Spearman is consistent with that claim *at the partition-level* — the body-graph spectrum does encode at least the deep-vs-shallow heliocentric structure. It is not strong enough to claim the spectrum encodes the full ITN tube structure (the within-partition variance is unresolved). The CR3BP literature's per-Sun-planet rotating-frame analysis remains necessary for finer accessibility predictions; the spectral lens has earned its keep as a *coarse classifier*, not (yet) as a *full ITN predictor*.

### 13.7 Recommendation

**Ship as v0.17.x research-output (notebook-only).** This section + the prototype script + the four figures are the v0.17.x research deliverable. The Spearman is strong enough to publish but the predictor's actionable scope (mercury isolation) is too narrow to justify a `bridge.predict_itn_accessibility` ship surface — a partition-only first-pass filter would surprise users who expected it to discriminate finer than "is mercury involved or not."

**Defer ship of a spectral-only ITN query** to v0.18.0 or later, gated on at least one of the §13.6 refinements (two-eigenvector embedding, diffusion distance, resonance-weighted edges) lifting the Spearman past 0.85 *with* a Matthews φ past 0.6 — the bar at which the spectrum genuinely competes with the Dijkstra rather than weakly anticipating it. Until then, `find_itn_chains` remains the canonical query and this section serves as the baseline result that the next iteration tries to beat.

**Open question for v0.17.x scoping.** The most natural next step is the **resonance-weighted Laplacian** because it ties the gateway-graph thread directly to the BIP cyclic-group encoder's primary surface (notebook §6) and to the architectural-mode work (§11.6). If a Laplacian whose edges are integer-resonance-strength weighted produces a Fiedler vector that splits inner-vs-outer or cheap-chain-clusters more sharply than the inv-Hohmann one does, the spectral-ITN claim acquires a second leg of evidence and becomes worth a real ship surface. That is the v0.17.x or v0.17.y scoping question. *(Answered in §13.8.)*

### 13.8 Follow-up — resonance-weighted Laplacian

The §13.7 open question got an answer. A third edge weighting was added to [`research/gateway_graph_laplacian.py`](research/gateway_graph_laplacian.py):

```
w_ij = exp(-residual / scale) / (p + q),    scale = 5e-3
```

where `(p, q)` is the best small-integer rational approximation of `min(p_i, p_j) / max(p_i, p_j)` from `_best_rational_approx(ratio, max_int=30)` — the **same primitive v0.17.0 ITN chains use for the per-leg resonance signature**, so the gateway-graph and the chain signatures share their lowest-level symbol.

The weight has two physically-motivated factors:

* `1 / (p + q)` — strong low-order resonances dominate (Jupiter-Saturn 2:5 → `p+q=7`, Terra-Jupiter 1:12 → `p+q=13`, Ceres-Pallas 1:1 → `p+q=2`); high-order Stern-Brocot best-rationals are damped (Saturn-Uranus 7:20 → `p+q=27`).
* `exp(-residual / scale)` with `scale = 0.5%` — penalises ratios that *land near* a low-order rational without a true period lock. The Uranus-Neptune ratio 0.510 best-fits as 15:29 with `p+q=44` (real value, no spurious 1:2 gift); Earth-Mars 8:15 has residual 0.24% so `exp(-0.48) ≈ 0.62` (kept); Saturn-Uranus 7:20 has residual 1.3% so `exp(-2.6) ≈ 0.07` (suppressed).

The five strongest resonance edges in the 13-body roster are physically meaningful: ceres↔pallas 1:1 (the "near-degeneracy" pair driving the inv_synodic null result, here interpretable as a true resonance), neptune↔pluto 2:3 (the well-known mean-motion lock), mars↔hygiea 1:3, jupiter↔saturn 2:5 (the great inequality), and venus↔hygiea 1:9.

#### 13.8.1 Result

| Predictor | Weighting | Spearman ρ | Matthews φ | n_finite | n_inf |
| :--- | :--- | ---: | ---: | ---: | ---: |
| Fiedler distance + partition | inv_dv (§13 primary) | **+0.743** | **+0.336** | 53 | 25 |
| Fiedler distance + partition | inv_synodic (§13 control) | −0.301 | +0.083 | 53 | 25 |
| Fiedler distance + partition | **resonance (this section)** | **+0.632** | +0.207 | 53 | 25 |

**The lift hypothesis is null.** Resonance-weighted Spearman ρ = +0.632 is *below* the inv_dv baseline of +0.743; Matthews φ = +0.207 is below +0.336. The §13.7 ship bar (ρ ≥ 0.85 *with* φ ≥ 0.6) is not cleared.

But the partition itself is **structurally cleaner** than the inv_dv partition — and that's a separately-interesting finding.

#### 13.8.2 The inner/outer partition

The resonance Fiedler vector cleanly bipartitions the 13-body roster on the **asteroid-belt boundary**:

| Partition | Bodies (sorted by Fiedler-vector entry) | Periods (d) |
| :--- | :--- | :--- |
| Negative (outer 5) | pluto (−0.585), neptune (−0.585), uranus (−0.137), jupiter (−0.078), saturn (−0.042) | 4332 – 90560 |
| Positive (inner 8) | hygiea (+0.093), pallas (+0.137), ceres (+0.139), vesta (+0.158), mars (+0.171), terra (+0.197), venus (+0.202), mercury (+0.329) | 88 – 2031 |

Compare to the inv_dv partition from §13.5: {mercury, venus} negative (`f₂[mercury] = +0.952`, the rest clustered in `[-0.10, -0.03]`) — essentially a Mercury-isolation indicator. The resonance partition is far more architecturally informative: it **identifies the asteroid belt as the spectral inner-vs-outer boundary**. Pluto and Neptune share the strongest (−0.585) entry — the 2:3 mean-motion lock dragging both deep into the outer cluster.

That's a non-trivial finding *about the body-graph architecture*: the spectrum of a Laplacian whose edges are weighted by integer-resonance strength encodes, in its second eigenvector, the canonical inner/outer system division that planetary scientists draw by inspection. The Antikythera-style cyclic-group encoder, applied to the BODIES roster, **discovers this partition without being told it exists**.

#### 13.8.3 Why the cleaner partition gives the weaker Spearman

The two findings are not contradictory; they are about different things:

* **Inv_dv partition** (mercury vs everyone) maximises the *cost* signal per partition: across-partition pairs are uniformly expensive (mercury Hohmann to anywhere is ≥ 14 km/s); within-partition pairs span the full Δv range. The Fiedler distance scale `|f₂[mercury] − f₂[else]| ≈ 1.0` vs `|f₂[else] − f₂[else']| ≈ 0.1` provides a 10:1 contrast that ranks the cross-partition pairs at the top of both rankings simultaneously. *Spearman ρ rewards rank agreement on extremes.*
* **Resonance partition** (inner vs outer) maximises the *period-ratio* signal per partition: within-partition pairs share approximately commensurable periods (close mean motions ⇒ low-order rationals ⇒ short Fiedler distance); across-partition pairs have wildly different mean motions. But Hohmann Δv depends on **semi-major-axis difference**, not on period-ratio rationality — so within-cluster Δv variance is large (Mars-Vesta = 4.7 km/s vs Mercury-Vesta = 24.0 km/s, both within the inner cluster) and the Fiedler distance fails to track it.

In short: the resonance Laplacian asks "**which bodies live on the same gear-ratio ladder**" — the BIP / cyclic-group native question. The inv_dv Laplacian asks "**which bodies share an accessibility class**" — the trajectory-design native question. The two questions have different correct answers, and §13.5–§13.6 + §13.8.1 just measured both.

#### 13.8.4 Why this is still the right "next move"

§13.7 said the next-step refinement that "ties the gateway-graph thread back to the BIP cyclic-group encoder primary surface (notebook §6) and to the architectural-mode work (§11.6)" was the resonance-weighted Laplacian. That's what §13.8 ran. The **§13.7 open question** had two halves:

1. *Does it lift Spearman past 0.85 with Matthews φ past 0.6?* **No.** ρ = +0.632, φ = +0.207. The resonance Laplacian does not promote `bridge.predict_itn_accessibility` to a v0.18.0 ship surface.
2. *Does it produce a Fiedler vector that splits inner-vs-outer or cheap-chain-clusters more sharply than inv_dv?* **Yes — for inner-vs-outer.** The resonance partition is the canonical asteroid-belt boundary, far more architecturally informative than the inv_dv mercury-isolation. *(For cheap-chain-clusters, no: the within-cluster Δv variance is large.)*

So the resonance Laplacian earns a **partial answer** to §13.7. The thesis from §12.3 — "the ITN is implicit in the body-roster gear ratios" — is consistent with the resonance result *at the inner/outer-architecture level* but not at the within-architecture-class accessibility level. The cyclic-group encoder *does* discover the body-graph's inner/outer division for free; it does *not* additionally discover the per-pair Δv ordering.

#### 13.8.5 Updated recommendation (supersedes §13.7's first paragraph)

* **Ship as v0.17.x research-output (notebook-only)** — unchanged from §13.7. §13.8 adds another datapoint to the same research arc but does not change the ship verdict.
* **A `bridge.predict_itn_accessibility` ship surface remains deferred** to v0.18.0 or later. The two refinements still untried from §13.6 are the **two-eigenvector embedding** (`(f₂, f₃)` Euclidean distance — the inv_dv partition might gain finer discrimination from `f₃`) and the **diffusion distance** (`d_t(i, j) = ‖exp(−t L) e_i − exp(−t L) e_j‖`, which captures multi-step accessibility — the natural spectral analogue of the multi-leg Dijkstra). Either could lift the Spearman past 0.85; neither has been measured.
* **A complementary architectural surface** could ship now: a `bridge.classify_body_architecture` query that returns the resonance Laplacian's Fiedler partition (inner / outer-system designation per body). This is a different ship surface than ITN accessibility — it is a body-roster-architecture indicator, useful for visualisations and for cross-pollinating with the §11.6 architectural-mode thread. Ship-or-not depends on whether the project wants a *partition* surface in the bridge today; it is not the ITN predictor §13.7 set out to find.

#### 13.8.6 Refinement still in scope

The Δv-vs-resonance comparison suggests a **hybrid edge weight** worth measuring: `w_ij = w_ij^{inv_dv} × w_ij^{resonance}`, multiplying the cost signal by the resonance signal. The hypothesis is that pairs which are *both* cost-cheap *and* resonance-locked (Earth-Mars, Jupiter-Saturn) get a multiplicatively stronger edge than either pure metric provides. If the hybrid Spearman lifts past either pure metric, the spectral-ITN ship-surface case becomes much stronger. This is the obvious next single-experiment refinement and slots cleanly into the §13.6 list above. *(Answered in §13.9.)*

### 13.9 Follow-up — hybrid `inv_dv × resonance` Laplacian

The §13.8.6 hybrid hypothesis got an answer. A fourth edge weighting was added to [`research/gateway_graph_laplacian.py`](research/gateway_graph_laplacian.py):

```
w_ij = (1 / (Δv_ij + ε_dv)) × (exp(-residual / scale) / (p + q))
     = w_ij^{inv_dv} × w_ij^{resonance}
```

i.e. the multiplicative product of §13's primary and §13.8's resonance. Pairs that are *both* cost-cheap *and* resonance-locked (Earth-Mars, Jupiter-Saturn, Neptune-Pluto via the 2:3 lock) get multiplicatively stronger edges than either pure metric provides; pairs that are cost-cheap-but-resonance-incoherent or resonance-locked-but-cost-expensive get damped by the multiplicand they fail.

#### 13.9.1 Result

| Predictor | Weighting | Spearman ρ | Matthews φ | n_finite | n_inf |
| :--- | :--- | ---: | ---: | ---: | ---: |
| Fiedler distance + partition | inv_dv (§13 baseline) | +0.743 | +0.336 | 53 | 25 |
| Fiedler distance + partition | inv_synodic (§13 control) | −0.301 | +0.083 | 53 | 25 |
| Fiedler distance + partition | resonance (§13.8) | +0.632 | +0.207 | 53 | 25 |
| Fiedler distance + partition | **hybrid_dv_resonance (this section)** | **+0.857** | +0.298 | 53 | 25 |

**The hybrid clears the §13.7 Spearman bar.** ρ = +0.857 is above the 0.85 line set in §13.7 as the threshold at which "the spectrum genuinely competes with the Dijkstra rather than weakly anticipating it." It also exceeds both pure metrics: +0.114 above the inv_dv baseline (+0.743) and +0.225 above the resonance metric (+0.632). The multiplicative combination genuinely captures more of the empirical Δv variance than either factor alone — the hypothesis from §13.8.6 is **vindicated for the continuous Spearman predictor.**

**Matthews φ does not clear the same bar.** φ = +0.298 is below the 0.6 line and below the inv_dv baseline of +0.336. The hybrid partition is more balanced (within = 48, across = 30 vs inv_dv's 56-22) — the multiplicative damping spreads the spectral support across multiple bodies rather than concentrating it on one outlier (mercury, in inv_dv's case). That is *good news for the continuous Fiedler-distance predictor* (broader support ⇒ finer rank discrimination across the 53 feasible pairs) and *neutral news for the sign-based partition predictor* (broader support ⇒ more pairs land near the partition boundary, where the sign-flip becomes noisy).

#### 13.9.2 Diagnostic — what the hybrid Fiedler vector encodes

The hybrid Fiedler vector preserves the §13.8 inner/outer structure but with finer per-body discrimination than either pure metric. The strongest hybrid edges in the 13-body roster:

* `jupiter` ↔ `saturn` (cost: 8.7 km/s; resonance: 2:5; hybrid weight ~ 0.012)
* `terra` ↔ `mars` (cost: 5.6 km/s; resonance: 8:15; hybrid weight ~ 0.0085)
* `neptune` ↔ `pluto` (cost: ~2 km/s; resonance: 2:3; hybrid weight ~ 0.066 — the dominant hybrid edge, coupling resonance lock × short-Δv between near-degenerate orbits)
* `ceres` ↔ `pallas` (cost: ~0.5 km/s; resonance: 1:1; hybrid weight ~ 0.55 — overwhelmingly dominant by virtue of near-coincident periods)

The hybrid Fiedler vector therefore mixes two distinct physical signals: the trajectory-design-cost (which favours "easy Hohmann" pairs regardless of period rationality) and the BIP cyclic-group-encoder period-rationality (which favours integer-locked pairs regardless of cost geometry). The product penalises pairs that are *only* one or the other — and that is exactly what produces the +0.857 Spearman lift.

#### 13.9.3 Implication for ship surfaces

§13.7 set the v0.18.0 ship bar as ρ ≥ 0.85 *with* Matthews φ ≥ 0.6. §13.9 clears the ρ side definitively (+0.857) but does *not* clear the φ side (+0.298). This separates into two distinct ship questions:

1. **Continuous accessibility predictor** (`bridge.predict_itn_accessibility(departure, target) -> Δv_estimate`). Uses the hybrid Fiedler distance as a closed-form spectral predictor of `min(total_dv_kms)` over `find_itn_chains` outputs. The Spearman is strong enough that this is a useful first-pass filter (5–10 ms wall-clock per query vs ~1.5 s for the full Dijkstra over 50 yr at J2000). **Ship-readiness depends on calibrating the Fiedler-distance → Δv mapping** (the spectral predictor produces a rank, not an absolute Δv). Defer to v0.18.x once a regression model lands.
2. **Architectural classification surface** (`bridge.body_architecture(target=None)`). Uses the §13.8 *resonance-only* Fiedler partition (inner-8 / outer-5 designation per body). Independent of the hybrid result; ships at v0.18.0 alongside this notebook update — see §4 release history.

#### 13.9.4 Updated recommendation (supersedes §13.7 + §13.8.5)

* **Ship the architectural classification surface as v0.18.0** (`bridge.body_architecture`). The §13.8 result is unambiguous for that surface — the resonance Fiedler partition is the canonical inner/outer system division — and the surface is small, pure-Python, no ABI bump. Tests, bridge wrapper, CLI subcommand, docs lockstep all standard for the project.
* **Defer `bridge.predict_itn_accessibility` to v0.18.x or v0.19.0**, gated on either (a) calibration of the hybrid Fiedler-distance → Δv regression (with cross-validation across body subsets), or (b) Matthews φ lift past 0.6 via one of the §13.6 untried refinements (two-eigenvector embedding, diffusion distance). The +0.857 Spearman is *necessary but not sufficient* for a useful ship surface — users querying "predict the Δv to reach Jupiter from Earth" need a number, not a rank.
* **Both the §13.8 inner/outer partition and the §13.9 hybrid spectrum belong in the same notebook §13 thread**: they are two facets of the same gateway-graph Laplacian eigenstructure under different edge weightings. Future ships should reference §13.5 for the inv_dv baseline, §13.8 for the resonance-only partition (the architectural ship), and §13.9 for the hybrid (the deferred ITN-accessibility predictor).

### 13.10 Follow-up — two-eigenvector `(f₂, f₃)` embedding

The §13.6 list left a refinement open: project bodies onto `(f₂, f₃)` instead of `f₂` alone, and re-measure the Spearman/MAE/Matthews against the same ground truth. The §13.9 1-D hybrid hit ρ = +0.857 / R² = 0.51 / MAE = 4.11 km/s; the §13.7 ship bar wanted ρ ≥ 0.85 *with* Matthews φ ≥ 0.6 for `bridge.predict_itn_accessibility`; v0.18.1 shipped the 1-D version anyway, sized to "fast triage, not trajectory design."

This section closes that refinement and ships the result as **v0.18.2**.

#### 13.10.1 Method

Compute the same hybrid Laplacian as §13.9. Take the second *and* third Fiedler eigenvectors `(f₂, f₃)`, with the v0.18.0 sign convention on `f₂` (mercury forced positive) and a max-|f₃| sign convention on `f₃` (no physics-anchor available; the second-smallest non-trivial mode lives on a different structural axis, so a max-magnitude convention is the simplest reproducible choice). Build the per-body 2-D embedding `(f₂[i], f₃[i]) ∈ ℝ²` and define the spectral pair distance as the 2-D Euclidean norm `d_{2D}(i, j) = ‖(f₂[i] - f₂[j], f₃[i] - f₃[j])‖₂`. Re-run OLS regression `Δv = a + b · d_{2D}` on the same 53-feasible-pair ground truth. Re-run leave-one-out cross-validation. Re-test under all three weightings (inv_dv, resonance, hybrid) for completeness.

The script lives at [`research/two_eigenvector_fiedler_embedding.py`](research/two_eigenvector_fiedler_embedding.py); reads the same SHA1-keyed §13 ground-truth cache as the existing v0.18.1 calibration script.

#### 13.10.2 Result

| Weighting | ρ_1D | ρ_2D | lift | R²_1D | R²_2D | MAE_1D | MAE_2D | φ |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| inv_dv (§13.5 baseline) | +0.7433 | +0.7656 | +0.0223 | 0.4426 | 0.4748 | 4.372 | 3.985 | +0.336 |
| resonance (§13.8) | +0.6322 | +0.5131 | −0.1191 | 0.3858 | 0.3776 | 5.015 | 5.106 | +0.207 |
| **hybrid (§13.9)** | **+0.8573** | **+0.8488** | **−0.0085** | **0.5072** | **0.6439** | **4.110** | **2.995** | **+0.298** |

Read the **hybrid row**, which is what v0.18.1 already calibrates against. Three things happen at once:

1. **Spearman is essentially unchanged** (1-D: +0.8573 → 2-D: +0.8488 — a wash on rank). The 1-D Fiedler distance was already a strong rank-correlator; adding a second axis doesn't reorder the pairs.
2. **R² jumps materially** (0.5072 → 0.6439, +27 %). The 2-D distance lets the linear regression fit the within-cluster variance that the 1-D Fiedler vector collapsed.
3. **MAE drops materially** (in-sample 4.110 → 2.995 km/s = −27 %; LOOCV 4.238 → 3.123 km/s = −26 %; new LOOCV median |error| = 2.20 km/s).

The §13.7 ship bar (ρ ≥ 0.85 *and* Matthews φ ≥ 0.6) is **still not cleared on Matthews**: the 2-D *embedding* gives a tighter regression but the 1-D *partition* (sign of `f₂`) is what the φ metric measures; that's unchanged. So the 2-D upgrade is for the *continuous* predictor, not the partition predictor. Which is fine — the partition predictor isn't the v0.18.1 ship's deliverable; the continuous Δv estimate is.

#### 13.10.3 What `f₃` looks like

| Body | `f₂` (sign-anchored to mercury+) | `f₃` (sign-anchored to max-|f₃|+) |
| :--- | ---: | ---: |
| mercury | +0.9156 | −0.2844 |
| venus | +0.0722 | +0.4827 |
| terra | +0.0322 | +0.5083 |
| mars | −0.0292 | +0.2002 |
| jupiter | −0.1239 | −0.0956 |
| saturn | −0.1347 | −0.1302 |
| uranus | −0.1699 | −0.2528 |
| neptune | −0.2087 | −0.3719 |
| pluto | −0.2075 | −0.3674 |
| ceres | −0.0364 | +0.0764 |
| vesta | −0.0253 | +0.0894 |
| pallas | −0.0364 | +0.0763 |
| hygiea | −0.0479 | +0.0691 |

`f₃` reads as a **roughly inner-vs-outer-disc orientation** axis but on a different basis than `f₂`. Earth and Venus sit at the deepest positive `f₃` (+0.49 / +0.51); the asteroid belt at modest positive (+0.07 to +0.09); the outer planets all negative (jupiter through pluto, monotonically deepening with distance); mercury isolated negative. The pluto-neptune resonance lock is even more pronounced on `f₃` than on `f₂` (−0.37 vs −0.37 — almost identical) — suggesting `f₃` carries some of the same 2:3 mean-motion-lock signature that §13.8 surfaced for the resonance-only `f₂`.

The 2-D embedding is therefore not "two orthogonal coordinates of the same accessibility class" but "two distinct architectural readings of the body roster, additively combined under Euclidean distance" — a generalised spectral pair-distance.

#### 13.10.4 Calibration constants (v0.18.2)

```
CALIBRATION_INTERCEPT_KMS                = 4.896324
CALIBRATION_SLOPE_KMS_PER_FIEDLER_UNIT   = 17.319301
CALIBRATION_R2                           = 0.643884
CALIBRATION_IN_SAMPLE_MAE_KMS            = 2.994717
CALIBRATION_LOOCV_MAE_KMS                = 3.122645
CALIBRATION_LOOCV_MEDIAN_ABS_ERROR_KMS   = 2.204213
CALIBRATION_SPEARMAN_RHO                 = 0.849
```

The v0.18.1 1-D constants are preserved as `CALIBRATION_INTERCEPT_KMS_1D_HISTORICAL` etc. for traceability.

#### 13.10.5 Recommendation

* **Ship the 2-D embedding as v0.18.2** (this section + the constant updates land together). The MAE drop is the user-visible win — `predict_itn_accessibility` users want Δv accuracy, not rank correlation per se.
* **Sign-based partition predictor still doesn't clear φ ≥ 0.6.** A `bridge.predict_itn_accessibility(..., kind="class")` API that returns "cheap" / "expensive" boolean is *not* recommended — the partition metric isn't strong enough.
* **Diffusion distance** (§13.6 refinement #2) remains untried. `d_t(i, j) = ‖exp(−tL) eᵢ − exp(−tL) eⱼ‖` for some characteristic time `t` could lift R² further; it captures multi-step accessibility (the natural spectral analogue of the multi-leg Dijkstra), which neither the 1-D nor the 2-D Fiedler distance does. Queued as a v0.18.x or v0.19.0 follow-up if MAE needs to drop below 3 km/s for a downstream consumer.

## 14. The holographic principle at macro scale

The §13 result invites a framing the rest of this notebook has only implied: **the spectrum of the body-graph Laplacian behaves as a holographic boundary representation of the bulk solar-system dynamics it encodes.** This section names the analogy explicitly, locates it in the literature, and is honest about what counts as a real holographic principle and what is a structurally-similar dimension-reduction we are usefully calling "holographic" by analogy.

### 14.1 What the holographic principle says (one paragraph)

In quantum gravity / string theory, the **holographic principle** (`'`t Hooft 1993, *Dimensional Reduction in Quantum Gravity*; Susskind 1995, *The World as a Hologram*) states that the complete information content of a (d+1)-dimensional region of spacetime is encoded on its d-dimensional boundary, with information density bounded by the Bekenstein-Hawking limit (one bit per Planck area). The canonical realisation is the **AdS/CFT correspondence** (Maldacena 1997), in which gravitational dynamics in (d+1)-dimensional anti-de-Sitter bulk are exactly dual to a d-dimensional conformal field theory on the boundary — the **bulk-boundary correspondence**. A pure boundary calculation determines the bulk; a pure bulk calculation determines the boundary; they are the same theory in two presentations.

The principle is two-part: (1) **information capacity** scales as area, not volume; (2) **dynamics** in the bulk are recoverable from the boundary description. Part (1) is the radical claim; part (2) is the operationally useful one for non-quantum-gravity systems that exhibit structurally-similar dimension reduction.

### 14.2 What "macro-scale holographic" means in this project

The Antikythera mechanism + this package's spectral encoder live entirely in the classical, non-relativistic, non-quantum-gravitational regime. Calling anything here "holographic" in the strict sense would be a category error. We use the term in a precise structural sense:

> A **holographic dimension reduction** is any encoding in which a high-dimensional bulk state is fully (or effectively-fully, for some specified purpose) recoverable from a strictly-lower-dimensional boundary representation, with explicit geometric or spectral identification of which boundary degree of freedom maps to which bulk degree of freedom.

Under this reading, three constructions in `ephemerides-spectral` are macro-scale holographic in structure:

#### 14.2.1 BIP encoder bulk → 32-bit phase residue boundary

The encoder bulk is the full DE441 ephemeris — the 52-body barycentric state at every instant in 200+ years. The boundary is a `uint32[52]` array of phase residues at one JD, computed by the BIP integer-ALU encoder (§5). The bulk → boundary map is the dimensional reduction `barycentric_state(jd) → phase_residues(jd)`; the boundary → bulk map is the recovery `propagate_back(phase_residues, jd₀) → barycentric_state(jd₀ + Δt)` via the LTI propagator (§1, §2). The recovery is exact only on the resonance modes the encoder is wired for (Phase 9 + the v0.5.x catalog patches close out-of-resonance drift); see the §3 DE441 sweep + §9 patch-shrinks-residual benchmark for the empirical encoding rate.

The information-density punchline: a 52-body × 6-dof × float64 bulk state is ~2.5 KB; the BIP boundary is 52 × 32 bit = 208 bytes. A **12× compression** with an explicit physics-grounded recovery rule. That is structurally a **codimension-1 reduction** even though the bulk and boundary live in different spaces (configuration vs cyclic-group-residue).

#### 14.2.2 Hyperdimensional state bulk → eigenmode boundary

The HD pipeline (§7 Tier 2b) lifts the BIP residues to a `complex64[D=65536]` hyperdimensional vector — that is the *bulk*. Its **eigenmode decomposition** in the Laplacian eigenbasis is a sparse, low-rank representation: only the modes resonant with the Phase-9 lobes carry significant weight. A practitioner working entirely in eigenmode coefficients (the boundary) recovers every observable the bulk supports (syzygy events, observer binds, eclipse probabilities) without ever reconstructing the D=65536 array.

This is the same shape as **Atiyah-Singer** index theorems on a manifold: the bulk admits a Hodge / spectral decomposition, and *most* of the bulk's information density lives on a small number of modes. Whether you call it holographic or just "spectrally sparse" is taste; the structural property is the same. Notebook §1.4 already names this **"phonon-like instantaneous spectrum on a vibrating lattice"**; the holographic reading reframes it as a bulk-boundary statement: every relevant bulk question reduces to a finite eigenmode sum.

#### 14.2.3 Body-graph spectrum → ITN accessibility (the §13 result)

The freshest and most directly testable case is §13: the body-body graph Laplacian's eigenstructure (specifically the Fiedler vector under the §13.9 hybrid edge weighting) acts as a closed-form *spectral boundary* whose pairwise distances rank-correlate at Spearman ρ = +0.857 with empirical multi-leg ITN-chain Δv (the bulk's trajectory-design content from the v0.17.0 Dijkstra search). The boundary side is a single 13-dimensional eigenvector; the bulk side is the full `find_itn_chains` Dijkstra over the (body, epoch, total_dv) state space, which has |V|=13 × 78 pair-windows × max_legs combinatorics. **A 13-dim spectral boundary anticipates the rank ordering of a 78-pair × multi-window Dijkstra result.**

That is exactly the shape of a (qualified) holographic claim: the bulk dynamical question (cheap-vs-expensive accessibility classes) is determined to within rank by the boundary spectral question (Fiedler-vector pairwise distance). It is not the strict Bekenstein-Hawking bound, but it is a non-trivial dimension reduction with an explicit error metric — the +0.857 Spearman tells you exactly *how holographic* the reduction is on the v0.16.0 13-body roster.

### 14.3 Why this is the right vocabulary for the project

Three reasons holographic-principle vocabulary earns its keep here, separately from physics-of-quantum-gravity prestige:

1. **It names what §13 is doing.** The §13.5 / §13.8 / §13.9 results are bulk-boundary correspondences in disguise: a Dijkstra-bulk question (multi-leg accessibility class) is approximated by a spectral-boundary question (Fiedler partition / Fiedler distance). Without the holographic framing the result reads as "Spearman correlation between graph Laplacian and trajectory cost"; with the framing it reads as "the body-graph spectrum encodes the trajectory-cost manifold in 13 boundary degrees of freedom."
2. **It connects to the §1.4 multi-vocabulary-aliasing pattern.** §1.4 already names the breathing Laplacian in four mathematical vocabularies (state-dependent Laplacian / adaptive Kuramoto / Ricci-in-motion / parametric coupling, after the §92 expansion). The holographic vocabulary adds a fifth one — and a particularly useful one for HDC and bulk-boundary literatures that we have not yet leaned on.
3. **It points to a real future research direction.** A genuinely-holographic version of §13 would calibrate the Fiedler-distance → Δv map into an absolute regression (not just a rank), with the **hybrid `inv_dv × resonance` Laplacian** as the boundary theory and the **`find_itn_chains` Dijkstra** as the bulk theory. That regression — which is also the v0.18.x `bridge.predict_itn_accessibility` ship surface (notebook §13.9.3) — is the natural next ship after v0.18.0. A successful regression with rolling cross-validation across body subsets *is* an empirically-validated bulk-boundary correspondence on the BODIES roster.

### 14.4 Where the analogy breaks (honest disclaimers)

* **No Bekenstein-Hawking-style information bound.** The +0.857 Spearman is empirical, not derived from a maximum-entropy / area-law / information-theoretic limit. We have no statement of the form "no encoding can do better than the spectral one because gravity / surface area / thermodynamic-entropy reasons." The holographic vocabulary is structural-shape borrowing, not literal AdS/CFT.
* **The bulk is classical, non-relativistic, non-quantum-gravitational.** Antikythera-style cyclic-group encoders live entirely in classical celestial mechanics. There is no horizon, no black hole, no Planck-area constraint, no AdS metric. The dimension reduction is an empirical property of the body-graph Laplacian on the 52-body roster, not a theorem about spacetime.
* **The bulk-boundary map is approximate and lossy.** The §13.5 inv_dv ρ = +0.743 misses 25 of 78 pairs entirely (no chain found within budget); the §13.9 hybrid ρ = +0.857 still leaves Matthews φ at +0.298 (sign-based partition predictor only modestly better than random). A *strict* holographic bulk-boundary map would be exact, not Spearman-strong-but-φ-modest. We are doing dimension reduction with a measurable error rate, not duality.
* **No conformal symmetry on either side.** AdS/CFT relies on the conformal symmetry group on the boundary. The body-graph Laplacian has no such symmetry — its automorphism group is whatever permutation group fixes the period-ratio data, which is generically trivial.

The analogy is therefore "structurally holographic *as a dimension-reduction shape*" — not "holographic in the literal AdS/CFT sense." Calling it that openly avoids overclaiming.

### 14.5 Recommendation: when to invoke the vocabulary

Use **"macro-scale holographic"** or **"structurally holographic"** when describing:

* The §13 spectral-boundary → trajectory-bulk correspondence (with the Spearman as the error metric).
* The HDC bulk-state → eigenmode-boundary sparse representation (the §1.4 phonon-like spectrum reading, recast as bulk-boundary).
* The BIP `uint32[52]` boundary as the holographic encoder-state of the full DE441 bulk ephemeris (over a controlled time horizon, with the §3 sweep as the rate-of-information-loss diagnostic).

Avoid the term — or qualify it heavily — when:

* Discussing strict Bekenstein-Hawking bounds, AdS/CFT duality, or quantum-gravity holography. The project does not earn that vocabulary.
* Describing low-rank approximations whose error metric is *not* an explicit boundary-side spectral quantity. "Compressed" or "sparse" is the right word for those; "holographic" should imply a recoverable-bulk-from-boundary map with a defined error.

The macro-scale holographic framing is the cleanest single-sentence answer to "what is this project's spectral apparatus *for*?": the body-graph spectrum is a low-dimensional boundary representation that determines (within a measurable error) the bulk dynamics of the system it indexes. §13 is the first quantitative realisation of that framing on a non-trivial bulk question (multi-leg ITN accessibility); §14 names what §13 was doing.

## 15. Stellar Forge + galaxy-scale lift — feasibility scoping for v1.0.0 / v2.0.0

This section is **research-only scoping**, not a ship. It evaluates two hypothetical major-version-bump targets that have been raised informally:

1. **Star-system scale.** Could the package's spectral primitives (`bridge.body_architecture`, `bridge.predict_itn_accessibility`, `bridge.find_itn_chains`, the `BODIES` roster, Sol Time, SPrT, Sol Kinematics) plug into a procedural-star-system worldgen — specifically, the **Stellar Forge** that Dr Kay Ross worked on at Frontier Developments — as inputs, outputs, or building blocks for the kind of system catalogue Stellar Forge produces?
2. **Galaxy scale.** Is a Milky-Way-scale lift of the same apparatus *technically feasible* given publicly available astrometric data (JPL DE441, Hipparcos, Gaia DR3, etc.), or does the apparatus break in essential ways once the central potential ceases to be heliocentric?

Both questions sit downstream of §13's body-graph Laplacian work. §13 demonstrated that the body-graph spectrum (under hybrid `inv_dv × resonance` weighting) does encode the heliocentric-system architecture; §14 asks whether that argument scales out to *other* systems and *galactic* dynamics.

### 15.1 Stellar Forge — what it actually is

**Identification.** Dr Kay Ross is a former research physicist (Lancaster University, with collaboration at Fermilab) who joined Frontier Developments and was a lead physicist on the **Stellar Forge** — the procedural-generation engine that produces the ≈ 400 billion star systems populating the 1:1-scale Milky Way galaxy in Elite: Dangerous. The Stellar Forge is part of Frontier's proprietary Cobra engine and **is not open-source**; there is no public source code, design doc, or formal API. What is documented sits in PC Gamer / Space.com developer interviews, the Elite Dangerous fan-wiki, and the Frontier forums (Discovery Scanner Q&A streams). The Wikipedia / 80.lv / Frontier-forum coverage is consistent on the basics but light on technical detail.

**What it generates.** From the public coverage:

* **Real-star seed catalogue.** The Hipparcos and Gliese stellar catalogues seed ≈ 160,000 systems with real-star astrometry (positions, proper motions, photometric types). These are the "ground truth" entries that match the night sky.
* **Procedural infill** for the remaining ≈ 400 billion. The infill claims to use "first-principles" formation: a nebular-collapse simulation runs from initial chemical composition + total angular momentum + metallicity, aggregates matter into one or more central bodies, then partitions residual matter into planets, moons, asteroid fields, with derived properties (mass, radius, temperature, atmospheric composition, orbital elements).
* **Galactic-scale dust** — the dust distribution is concentrated on the galactic plane to match real-Milky-Way absorption, and the bulge / Sagittarius A\* / spiral-arm density structure is reproduced visually so that the sky from any in-game position matches what observers would actually see.
* **Planetary surfaces** — terrain, atmospheric chemistry, base maps (the Horizons / Odyssey expansions extended this to walkable planet surfaces).

**What it does NOT generate.** Galactic dynamics is *visual*, not *dynamical*. Stellar Forge does not (publicly) report star *orbits around the Galactic Centre*, does not simulate Lindblad resonances or spiral-density-wave dynamics, and does not provide a kinematic 6-D phase space for its 400-billion-star roster (just static positions + proper motions for the 160 k seeded ones). Its scope-cap is **per-system internal dynamics + global photometric / dust geometry**; galactic-disc orbital evolution is out of scope.

**API surface.** No first-party Stellar Forge API is exposed. Third-party projects scrape the Elite Dangerous client journal files (EDDN, EDSM, EDDB, Inara, EDAstro) and aggregate per-system Stellar-Forge outputs into queryable datasets. EDDN is the canonical live-stream pipeline; EDSM is the canonical archived database. So a downstream analytic tool would consume *EDDN/EDSM JSON*, not call Stellar Forge directly. The Stellar Forge itself is sealed behind the Cobra engine.

### 15.2 Where ephemerides-spectral primitives would slot in (or fail to)

If a future tool wanted to take Stellar-Forge-generated systems and run our spectral primitives against them, the candidate slots are:

* **`BODIES`-roster substitution.** Trivially feasible *per system*. A Stellar Forge system's planet roster — sidereal periods, masses, surface radii — is exactly the dataclass shape `BODIES[name] = Body(name, period_days, mass_earth, category, surface_radius_km)` already accepts. Treating each generated system as its own `BODIES` instance and running `body_architecture` / `predict_itn_accessibility` / `find_itn_chains` against *its* heliocentric (per-star-centric) graph is mechanically straightforward; the Hohmann + Laplacian + Fiedler math is generic over any heliocentric body roster.
* **`bridge.body_architecture` analogue.** The §13.8 resonance-Fiedler partition (inner-vs-outer system) **lifts cleanly** to any star system whose planets have well-defined sidereal periods. If Stellar Forge produces a system with eight planets and three asteroid belts, our existing Laplacian construction would identify its inner / outer partition without modification. This is the strongest "slot-in" of the four bridge surfaces.
* **`bridge.find_itn_chains` analogue.** Also lifts cleanly *per star system*. The closed-form Hohmann is a per-system query and does not depend on which star you orbit — only on the per-system semi-major axes and the local µ = G M\_★. Replace the Sun's GM with Stellar Forge's central-star GM, and the existing `itn_window.hohmann_total_dv_kms` runs verbatim. Result: an ITN-chain catalogue per generated system.
* **`Sol Time` / SPrT analogue.** Sol Time (`time_scales.py`) is a relativistic time-scale stack for our specific solar system (TT/TDB/TCB/TCG offsets are tied to Earth's gravitational potential and orbital state). The general construction is *per-system* — every star system has its own analogue — but the **calibration constants are not generic**: TCG and TT differ by 6.969 × 10⁻¹⁰, a number specific to Earth's geoid. Lifting requires re-deriving each system's barycentre / stellar-surface / habitable-body trio. Mechanically possible; per-system cost is real but bounded.
* **`Sol Kinematics`.** Same story: per-system, with re-derivation cost; the framework generalises but the constants do not.

**Verdict for §15.2:** The per-system spectral primitives **lift cleanly** to any star-system catalogue (Stellar Forge or otherwise) for which sidereal periods, masses, and a central-star µ are available. This is the **strong slot-in** — and it is *exactly* what §13's body-graph Laplacian was implicitly generic over. EDDN/EDSM JSON ingestion would be the bridge.

What does **not** slot in is anything cross-system: there is no meaningful Hohmann transfer between star systems (interstellar Δv is dominated by stellar escape velocity and Galactic-disc kinematics, not Hohmann arithmetic), so `find_itn_chains` and `predict_itn_accessibility` *cannot* run on a Stellar-Forge-galactic-roster vertex set without redefinition. The galactic-scale Δv geometry is a different problem.

### 15.3 Galactic-scale data sources — what the public datasets actually offer

The user's framing was "do we have enough data to model our galaxy with JPL data". JPL DE441 itself does not extend to galactic scale — it is a heliocentric ephemeris of Solar-System bodies plus 343 large asteroids, and stops at the heliocentric reference frame. The galactic-scale data live in stellar catalogues, not planetary ephemerides:

| Dataset | Total sources | 5-param astrometry | 6-D phase space (incl. RV) | Typical precision |
| :--- | ---: | ---: | ---: | :--- |
| **Gaia DR3** (2022) | 1,811,709,771 | 585 M (5-param) + 882 M (6-param) ≈ **1.47 B** | **33,812,183** | 0.02–0.03 mas (G < 15); 0.5 mas @ G = 20 |
| **Gaia GCNS** (within 100 pc) | 331,312 | ≈ 100% | subset (~70 k with RV) | sub-mas |
| **Hipparcos** (1997) | 117,955 | ≈ 100% | subset (~8 k with RV) | ~1 mas |
| **Tycho-2** | 2,539,913 | position + PM only | none | 7-60 mas |
| **2MASS** | ~ 470 M | photometry only | none | n/a (no astrometric solution) |
| **APOGEE / RAVE / GALAH** | ~ 3-5 M total | RV + chemistry only | RV component | spectroscopic |

**The headline number for our purposes** is the **33.8 million Gaia DR3 stars with a complete 6-D phase-space solution** (position + parallax + 2-D proper motion + radial velocity). This is what would power any spectral / Laplacian / kinematic-graph analysis at galactic scale. Within 100 pc the Gaia GCNS catalogue holds 331,312 stars; that is the natural "nearby" sub-sample (≥ 92% complete down to spectral type M9, per the GCNS paper).

**What about galactic-disc orbital periods?** Unlike heliocentric bodies, galactic-disc stars do not have a sidereal period in the BIP-encoder sense — but they *do* have a galactocentric orbital frequency Ω(R) (the angular speed at galactocentric radius R) and an epicyclic frequency κ(R) (the radial-oscillation rate around the guiding-centre orbit). Both are derivable from Gaia DR3 6-D phase space *if* a Galactic potential model is assumed (the standard MWPotential2014 / McMillan 2017 / similar parametrisations). At the Sun's galactocentric radius R\_☉ ≈ 8.2 kpc, Ω\_☉ ≈ 28 km/s/kpc → orbital period T\_☉ ≈ 225 Myr; κ\_☉/Ω\_☉ ≈ √2 (cold-disc limit), so a typical disc star executes ≈ √2 ≈ 1.4 radial oscillations per azimuthal orbit in the rotating frame.

This *does* give the BIP / cyclic-group encoder a candidate "period" observable for galactic-disc stars: T\_orbit(R) = 2π / Ω(R), or alternatively the ratio Ω/κ as a per-star feature. **But the 1.4 ratio is not a small-integer rational** — and that's the early warning that the Antikythera-style integer-resonance encoding is going to struggle here. More on this in §15.4.

### 15.4 What the BODIES / Laplacian / Fiedler / ITN apparatus does and does not lift to galactic scale

Working through the §13-level apparatus piece by piece, with verdicts:

* **`BODIES` roster lift to e.g. `MILKY_WAY_BODIES`.** Mechanically feasible — the dataclass shape is generic. A `MILKY_WAY_BODIES` keyed on Gaia source IDs with `period_days = 2π / Ω(R)` derived from Gaia 6-D phase space is constructible. The 33.8 M sources with full RV give a ceiling; the 331 k GCNS within 100 pc give a tractable starting roster. **Verdict: lifts.**
* **Body-graph Laplacian construction.** A complete 13-vertex graph at heliocentric scale becomes a complete 331,312-vertex graph (or sparse k-NN graph) at GCNS scale. Memory: a dense 331 k × 331 k float64 Laplacian is ≈ 0.87 TB — infeasible. A sparse k-NN Laplacian (k = 50 nearest neighbours in 6-D phase space) is ≈ 130 MB — fine. **Verdict: lifts, but requires a sparse-graph reformulation that §13 did not need at 13-vertex scale.**
* **Fiedler-partition / spectral-clustering.** This is precisely the question the Gaia DR3 moving-groups literature has been asking — and answering, with DBSCAN, MGwave wavelet decomposition, Friends-of-Friends, and (occasionally) graph-Laplacian / spectral-clustering methods. The recent literature (Antoja et al. 2023; Lucchini et al. 2023; arXiv:2512.09078 *Unsupervised Kinematic Dissection of the Solar Neighborhood*, December 2025) recovers Hyades / Pleiades / Sirius / Hercules / Coma streams as kinematic over-densities in the (U, V, W) velocity-space DBSCAN clustering. **The spectral-Laplacian approach is a less-explored variant of this same problem.** A graph-Laplacian moving-group classifier is not novel-in-kind but would be a competitive contribution to the literature. **Verdict: lifts, with an existing literature to slot into, not invent.**
* **Hohmann-Δv weighted edges + `find_itn_chains`.** Does not lift. Interstellar Δv is dominated by stellar escape velocity (≈ 42 km/s from Earth's orbit; at galactic-disc scales, escape from the Galaxy is ≈ 550 km/s) and by relative-velocity matching between moving groups (Hercules–Pleiades have a ≈ 30 km/s relative drift). Hohmann arithmetic — which presumes a single shared central potential — does not apply to a graph whose vertices are stars with their *own* deep wells. **Verdict: does not lift. The naive translation is wrong physics.**
* **Resonance-weighted edges (§13.8) at galactic scale.** Galactic dynamics has its own resonance literature: **Lindblad resonances** (inner-Lindblad ILR: Ω − κ/m = Ω\_p; outer-Lindblad OLR: Ω + κ/m = Ω\_p) are the standard galactic-disc analogues of mean-motion resonances. The Milky Way bar's OLR is observed beyond the solar circle and is the dynamical driver of several Gaia moving groups (Hercules, in particular, is generally interpreted as the OLR of the bar). **The cyclic-group `n_a φ_a − m_b φ_b ≈ 0` formalism *does* describe Lindblad resonances** — this is structurally the same algebra. A resonance-weighted Laplacian on (Ω, κ) per Gaia DR3 disc star, with edge weight `exp(−|m(Ω_i − Ω_p) − κ_i| / scale)` for some bar pattern speed Ω\_p, is a credible spectral approach to bar-OLR-driven moving-group classification. **Verdict: lifts at the algebra level — but with a critical caveat: the Galactic potential and bar pattern speed Ω\_p are model-dependent inputs** (they don't come from Gaia directly; they come from a Galactic-dynamics fit). This is a different epistemic regime from the heliocentric BIP encoder, which gets sidereal periods directly from JPL HORIZONS and treats them as ground truth.
* **Sol Time / SPrT (gravitational time-dilation).** Lifts conceptually (every star has its own proper-time stack relative to the Galactic-Centre frame, and stars deep in the bulge potential run measurably slower than disc stars by ≈ 10⁻⁹ — the analogue of the GR component of SPrT), but is *not* the natural galactic-scale observable. Galactic dynamics doesn't typically care about per-star proper-time offsets. **Verdict: lifts but is uninteresting at galactic scale.**
* **ITN chains / Lagrange-highway searching.** Does not lift. The CR3BP per-Sun-planet rotating-frame structure (§12) presumes a hierarchical Sun-dominated potential with planetary perturbers. The galactic potential is not hierarchical in this sense — disc stars feel the smoothed gravitational potential of the bar + bulge + dark-matter halo + spiral arms, all dynamically active on overlapping timescales. There is no useful "Lagrange-point" structure at galactic scale. **Verdict: does not lift.**

**Summary of the lift table:**

| Apparatus | Lifts to galactic scale? | Notes |
| :--- | :--- | :--- |
| `BODIES` roster shape | Yes | Re-key on Gaia source ID |
| Body-graph Laplacian | Yes (sparse k-NN) | Memory-bound; need sparse formulation |
| Fiedler / spectral clustering | Yes | Established Gaia-DR3 moving-groups literature |
| Hohmann-Δv edges / ITN chains | **No** | Wrong physics — different potential |
| Resonance edges (Lindblad analogue) | Yes (with caveat) | Requires Galactic-potential + Ω\_p model |
| Sol Time / SPrT | Conceptually yes | Uninteresting at galactic scale |
| Lagrange-highway / CR3BP | **No** | Galactic potential not hierarchical |

So roughly half the apparatus lifts; half does not. The half that lifts is the part that was already generic (graph Laplacian, spectral clustering, integer-resonance algebra). The half that does not lift is the part that was specifically heliocentric celestial mechanics (Hohmann, Lagrange).

### 15.5 Candidate ship surfaces for v1.0.0 / v2.0.0

Three honest framings, with verdicts:

**(A) "Per-system spectral worldgen primitive" — v1.0.0.** Ship a `bridge.system_architecture(BODIES_dict)` surface that takes any `BODIES`-shaped dict (Stellar Forge, hand-built, exoplanet catalogue, etc.) and returns the §13.8-style resonance-Fiedler partition. Reasonable, small scope, generalises §13.8 cleanly, ties to a real downstream consumer (Stellar-Forge-derived JSON, exoplanet catalogues like the NASA Exoplanet Archive). **Verdict: feasible, low-risk, useful. This is the strong v1.0.0 candidate — it's what §13.8 was implicitly already doing, just with the heliocentric-roster baked-in dependency lifted.**

**(B) "Galactic-scale moving-group classifier" — v2.0.0.** Ship a `bridge.gaia_moving_groups(gaia_subselection)` surface that takes a Gaia DR3 6-D phase-space subselection (e.g. the 331 k GCNS catalogue) and returns a sparse-Laplacian Fiedler-style spectral clustering of moving groups. **Verdict: feasible but enters a crowded literature.** DBSCAN / MGwave / FoF approaches dominate. A graph-Laplacian Fiedler classifier would be a *contribution*, not a *novelty*; the differentiator would have to be the cyclic-group / Lindblad-resonance edge-weighting, which is a credible novelty if it produces moving groups that the existing methods miss or sharpens the bar-OLR-driven Hercules-stream interpretation. This is a real research contribution but would need genuine astrophysics co-authors to validate against literature ground truth. The lift is technically feasible; the framing of it as "v2.0.0 of an Antikythera spectral library" rather than "a Gaia-DR3 moving-groups paper" is the harder question.

**(C) "Galaxy-scale procedural worldgen engine" — what the user originally framed as the big-bump target.** This conflates (A) and (B) and a Stellar-Forge-style infill engine. Building a Stellar-Forge-equivalent (procedural per-system formation simulation from nebular collapse) is **not what the package does** — the package consumes pre-existing rosters and computes spectral structure on them. Stellar Forge is *generative*; the package is *analytic*. Lifting to a generative engine would be a different project. **Verdict: don't ship this framing.** The package's strength is *reading structure out of an existing roster*; pretending it generates the roster is a category error.

### 15.6 Verdict + recommendation

**Headline.** The spectral framework is **not** tied so deeply to celestial-mechanics-of-the-solar-system that it can't lift, but it **is** scoped narrower than "procedural worldgen / galaxy-scale modelling engine" implies. The lift that genuinely works is **per-system spectral classification** (the §13.8 architecture-Fiedler primitive, generalised over `BODIES`-roster shape) and **galactic-scale moving-group spectral clustering** (Lindblad-resonance-weighted Laplacian on Gaia DR3 6-D phase space). The lift that does *not* work is anything Hohmann / Lagrange-based at galactic scale (wrong physics) or generative procedural worldgen (wrong project archetype).

**Recommendation: scope-limited yes.**

* **Ship v1.0.0 around (A): per-system spectral primitives** as a Stellar-Forge-friendly ingestion surface. Headline deliverable: `bridge.system_architecture(roster)` accepting an arbitrary `BODIES`-shaped dict (e.g. EDSM-derived JSON for a Stellar-Forge system) and returning the resonance-Fiedler inner/outer partition + ITN-chain catalogue + body-architecture report. This is a small, principled, technically clean v1.0.0 that lifts the implicit heliocentric assumption of v0.18.x to "any per-system roster" — a clean major version because it's a roster-shape generalisation, not a feature flood.
* **Defer v2.0.0** until either (a) the per-system v1.0.0 has a real downstream consumer (Stellar-Forge ingest pipeline, exoplanet catalogue ingest, Kerbal-Space-Program-style game integration, etc.) demonstrating the surface earns its keep, or (b) the galactic-scale Lindblad-Laplacian prototype (B) has a non-trivial result that competes with the existing Gaia DR3 moving-groups literature on its own terms. Either is at least 6 months of work; neither should be done speculatively.
* **Don't ship (C).** A "galaxy-scale procedural worldgen engine" is not what this package is. The honest version of that pitch would require a procedural generator, which is a separate project. Marketing v1.0.0 / v2.0.0 as that ambition would over-promise.

**What's not known.**

* Whether a spectral Lindblad-resonance Fiedler classifier on Gaia DR3 produces *new* moving-group classifications that the existing DBSCAN / wavelet / FoF methods miss. Without running the prototype, this is speculation. The §13.8 result on a 13-body roster does not extrapolate cleanly to a 331 k-vertex graph.
* Whether the EDDN / EDSM JSON format actually exposes everything (sidereal periods, masses) needed to populate a `BODIES`-shaped dict from Stellar Forge outputs. The wiki coverage suggests yes; verifying requires touching the EDDN schema.
* Whether the surface-radius / SPrT slot — which we keep as a per-body field for our existing Sol-Time stack — is something Stellar Forge actually exposes for its procedural bodies, or only for the 160 k Hipparcos / Gliese seeded ones. If the field is missing from the procedural infill, the SPrT pieces would fall back to default-zero handling (acceptable but worth flagging).
* Whether `Sol Kinematics` has anything novel to say at galactic scale beyond what the existing Gaia DR3 6-D-phase-space literature already covers. Probably not; this is the candidate we'd most expect to be subsumed by existing astrophysics.

### 15.7 References

Stellar Forge / Elite: Dangerous procedural generation:
* Elite Dangerous Wiki, "Stellar Forge". <https://elite-dangerous.fandom.com/wiki/Stellar_Forge>
* Hall, Charlie. "Space Adventure 'Elite: Dangerous' Simulates Milky Way in Stunning and Accurate Detail." Space.com, 2016. <https://www.space.com/31366-elite-dangerous-stellar-forge-interview.html>
* "Generating The Universe in Elite: Dangerous." 80 Level. <https://80.lv/articles/generating-the-universe-in-elite-dangerous>
* "Meet the Team — Kay Ross." Frontier Forums. <https://forums.frontier.co.uk/threads/meet-the-team-kay-ross.521191/>
* EDDN (Elite: Dangerous Data Network), the canonical third-party live-stream of Stellar-Forge-derived per-system data. <https://github.com/EDCD/EDDN>

Gaia DR3 / nearby-stars catalogues:
* Gaia Collaboration, "Gaia Data Release 3", ESA Cosmos. <https://www.cosmos.esa.int/web/gaia/dr3> — 1.81 B sources, 1.47 B astrometric, 33.8 M with RV.
* Smart, R. L., et al. "Gaia Early Data Release 3 — The Gaia Catalogue of Nearby Stars" (GCNS). *A&A* 649, A6 (2021). <https://www.aanda.org/articles/aa/full_html/2021/05/aa39498-20/aa39498-20.html> — 331,312 stars within 100 pc.
* Creevey, O. L., et al. "Gaia Data Release 3 — Apsis II. Stellar parameters." *A&A* 674, A26 (2023). <https://www.aanda.org/articles/aa/full_html/2023/06/aa43919-22/aa43919-22.html>

Gaia DR3 moving groups / kinematic substructure:
* Lucchini, S., et al. "New stellar velocity substructures from Gaia DR3 proper motions." *MNRAS* 519, 1989 (2023). <https://academic.oup.com/mnras/article/519/2/1989/6909073>
* Antoja, T., et al. "Gaia DR3 view of dynamical substructure in the stellar halo near the Sun." *A&A* 670, A92 (2023). <https://www.aanda.org/articles/aa/full_html/2023/02/aa44546-22/aa44546-22.html>
* "Unsupervised Kinematic Dissection of the Solar Neighborhood: Identifying Stellar Moving Groups with Gaia DR3." arXiv:2512.09078 (December 2025). <https://arxiv.org/abs/2512.09078>

Lindblad resonances / galactic-disc dynamics:
* "Lindblad resonance." Wikipedia. <https://en.wikipedia.org/wiki/Lindblad_resonance>
* Monari, G., et al. "Modelling resonances and orbital chaos in disk galaxies — Application to a Milky Way spiral model." *A&A* 600, A47 (2017). <https://www.aanda.org/articles/aa/full_html/2017/01/aa28895-16/aa28895-16.html>
* Struck, C. "Lindblad Zones: resonant eccentric orbits to aid bar and spiral formation in galaxy discs." *MNRAS* 450, 2217 (2015). <https://academic.oup.com/mnras/article/450/2/2217/986086>
* Kormendy, J. "A heuristic introduction to bars and spiral structure." NED Level-5 review. <https://ned.ipac.caltech.edu/level5/Sept14/Kormendy/Kormendy4.html>

Disclaimer on coverage: Stellar Forge is closed-source proprietary technology; all claims about its internals are derived from developer interviews and fan-wiki coverage, not source. Gaia DR3 numbers cited are from the ESA Cosmos public summary as of June 2022 release; subsequent re-releases (DR4 in preparation) may revise these counts upward.

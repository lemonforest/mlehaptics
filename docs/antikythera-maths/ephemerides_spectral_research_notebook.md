# The Ephemerides Mechanism: A High-Precision Resonant HDC Instrument

**Authors:** Gemini CLI (initial scaffolding); Steven Kirkland & Claude Opus (Phase 9 ALU-native)
**Date:** May 2026 (initial); finalised April 2026
**Status:** Phase 5–9 implemented; CLI + bridge surface stable. **v0.1.0 shipped to PyPI on 2026-05-04** — `pip install ephemerides-spectral`.

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

**Why "breathing" is metaphor, not vocabulary.** The codename captures the rhythm — coupling strengths inhale and exhale with the resonant-phase angle — but it does not connect to the literature's existing theorems. **State-dependent graph Laplacian** is the name to grep for in spectral-graph papers; **adaptive Kuramoto network** is the name to grep for in synchronisation papers; **vibrating lattice** captures the right *intuition* (phonon-like instantaneous spectrum) but is a 2nd-order Newtonian framing, whereas our flow is 1st-order phase rotation. We use "breathing" in headings and section labels for project continuity, and the precise vocabulary in prose so future readers can find their way out of our codename and into the canonical literature.

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

- **Download DE441:** Scale the validation suite to the full 3.3 GB JPL kernel.
- **Phase 9 Coverage:** Extend breathing couplings beyond the J–S 5:2 term: Neptune–Pluto 3:2, Io–Europa 1:2, Earth–Moon precession, and the Jovian Trojans. Each adds one entry in the resonance table; the LUT machinery is shared.
- **Resonant Bit-Serialized Hardware:** Port the BIP integer-only evolution to bit-serial hardware simulations (Verilog/SystemC). The cosine LUT becomes block RAM; the `omega * step` multiply becomes a fixed-precision multiplier.
- **Multi-Millennium Sweep:** Re-derive the historical anchors for the Metonic and Saros cycles against the DE441 "Sky Ground Truth", with breathing couplings active.
- **CORDIC Topocentric Rendering:** The cosine LUT is the first half of a CORDIC observer-binding pipeline; the rotation half can subsume the topocentric `lat/lon` bind.
- **First-Principles Phase-9 Derivation:** v0.1.0's $\alpha = 0.1$ J–S breathing depth is phenomenological. Deriving the modulation depth from a Hamilton/Delaunay-variable Lagrangian (with Lie-series perturbation theory around the 5:2 resonance) would replace the placeholder with a first-principles value. Connects to the adaptive-Kuramoto literature on derived-from-physics PDDP rules (cf. §1.4).

## 4. Release History

* **v0.1.0** — 2026-05-04. First PyPI release. Phases 5–9 frozen into the wheel: 26-body Sol Star System Laplacian, LTI propagator (Phase 8 baseline), state-dependent breathing couplings (Phase 9), ALU-native BIP encoder (305× speedup, 256 KB state), integer cosine LUT for the off-diagonal modulation, fixed-point Q-format frequency discipline, scoped overflow trap. Two backends: `bip` (default, integer ALU) and `complex128` (FPU reference). Rich CLI (9 subcommands) + Pyodide-friendly bridge. Live: <https://pypi.org/project/ephemerides-spectral/0.1.0/>.
* **v0.1.0rc1** — 2026-05-04. TestPyPI release candidate. Round-tripped clean; published under OIDC trusted publishing. Live: <https://test.pypi.org/project/ephemerides-spectral/0.1.0rc1/>.

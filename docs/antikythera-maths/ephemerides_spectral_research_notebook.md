# The Ephemerides Mechanism: A High-Precision Resonant HDC Instrument

**Authors:** Gemini CLI (initial scaffolding); Steven Kirkland & Claude Opus (Phase 9 ALU-native)
**Date:** May 2026 (initial); finalised April 2026
**Status:** Phase 5–9 implemented; CLI + bridge surface stable; v0.1.0 RC published to TestPyPI.

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
- **PyPI Release:** `ephemerides-spectral-publish.yml` ships TestPyPI dispatch + tag-push to PyPI via OIDC trusted publishing; release-candidate builds exercise both wheel and sdist before any public version is cut.

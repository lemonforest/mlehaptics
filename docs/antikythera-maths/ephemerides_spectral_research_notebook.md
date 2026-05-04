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
- **DE441 vs DE442 spectral error signature** *(v0.4+ research experiment)*: build two BIP instruments calibrated *separately* from DE441 and DE442; encode the same JD on both; project per-body residue deltas onto the Laplacian eigenbasis. Hypothesis: DE442's corrections to DE441 occupy a coherent eigenmode subspace — the spectral signature of the kernel update. If we can find a correlate, we can **predict** where ephemeris error correction is structurally needed without having the corrected kernel in hand. The natural-coprime decomposition from §6 would be the basis for that prediction.

## 4. Release History

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

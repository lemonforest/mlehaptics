# Task #218 Phase C2 — Chess-spectral QM Audit (2026-05-15)

**Concertmaster dispatch.** Conductor-initiated audit of chess-spectral's QM stack for equation-level coverage of canonical QM and QFT, scoping srmech's Phase C2 (MFO/SM/QM operations layer on top of the 14-class C-parity primitive vocabulary shipping via Task #217 Phase C1).

> **Provenance note.** Concertmaster delivered findings inline (system-prompt override on writing analysis .md files). Conductor saved this file as the durable artifact since the audit is load-bearing for Phase C2 scoping.

---

## Top-line verdict

**Chess-spectral instantiates roughly the kinematic + free-particle-dynamics quadrant of canonical QM, in spectral / graph-Laplacian form, for a single non-relativistic particle on a finite open 4D lattice. QFT, relativistic QM, gauge theory, and S-matrix machinery are absent.**

| Canonical domain | Instantiated | Adjacent | Absent |
|---|---:|---:|---:|
| Single-particle QM (12 eqs) | 7 (full/partial) | 1 | 4 |
| Relativistic QM (5 eqs) | 0 | 2 (KG + Dirac via notebook citation, no code) | 3 |
| QFT — gauge (7 eqs) | 0 | 2 (Higgs, Yukawa — analogical only) | 5 |
| QFT — propagators/amplitudes (6 eqs) | 0 | 1 (lattice propagator named) | 5 |
| Scattering (5 eqs) | 0 | 0 | 5 |
| Geometric/algebraic adjuncts | **strong** | n/a | n/a |

**Phase C2 implication in one line:** chess-spectral is a thick, ~1.5y-old reference for the canonical kinematic + free-evolution + spectral-measurement layer; srmech-C2 should absorb / cite it as primary substrate and add the relativistic / QFT / gauge layers, not re-implement what's there.

---

## Per-equation table

Files cited relative to `docs/chess-maths/chess-spectral/`. Notable absolute paths:
- `python/chess_spectral/qm_2d.py`
- `python/chess_spectral/qm_2d_dynamics.py`
- `python/chess_spectral/qm_4d.py`
- `python/chess_spectral/qm_4d_dynamics.py`
- `python/chess_spectral/qm_4d_bridge.py`

### Single-particle QM

| Equation | Status | Where | How |
|---|---|---|---|
| TDSE i∂_t ψ = Hψ | **FULL** | `qm_4d_dynamics.py:2575 evolve_under_h0`; `qm_2d_dynamics.py:260` | Closed-form U(t)=exp(-iH₀t) via eigenbasis-diagonal V·diag(exp(-iλt))·V^H (2D); `scipy.expm_multiply` Krylov (4D). H₀ Hermitian; norm + ⟨H⟩ preservation tested. ADR-002. |
| TISE Hψ = Eψ | **FULL** | `qm_4d.py:495 measure_observable_distribution`; `qm_2d_dynamics.py:190 _get_h0_eigenbasis_2d` | `numpy.linalg.eigh` returns (λ, V); 4096 eigenmodes for H₀; per-piece H_piece eigenspectra empirically tabulated (rook [-4,28] integer; bishop, queen, king, knight non-integer). |
| Heisenberg eq. dA/dt = i[H,A] | **ABSENT** | — | Schrödinger picture only. No operator-evolution code path. |
| Density-matrix / Liouville–vN | **PARTIAL** | `qm_4d_bridge.py:960 get_density_matrix_of` | Reduced channel-density ρ = M_local @ M_local^H on 11×11 channel block in a Manhattan-radius cell neighbourhood; Hermitian PSD; purity, rank, eigvals exposed. Marked `isPartial: True` — true η-metric partial trace deferred. |
| Pauli equation (spin-½ in EM) | **ABSENT** | — | No spinor structure, no EM coupling. |
| [x,p] = iℏ canonical commutator | **ABSENT** as algebra | — | No explicit momentum operator object. ∂_a anti-Hermitian gradient is constructed (`qm_4d_bridge.py:1083 _build_lattice_gradient_4d`) and used for probability current, but [x_a, ∂_b] = iδ_ab is never asserted as such. **Adjacent.** |
| Hamiltonian / L² / spin operators | **PARTIAL** | `qm_4d.py:363 build_H_piece_4`; `qm_2d.py:472`; `qm_4d_dynamics.py:2489 _build_h_free_4d` | H₀ = -Δ_{P_8^4}, plus five graph-adjacency-as-Hermitian piece-reach observables. No L² / Lz / S² in the textbook sense — chess uses B_4 hyperoctahedral group (order 384) and D_4 dihedral (order 8) instead of SO(3). **Group is wrong group**: spatial-lattice symmetry, not rotational. |
| Hydrogen-atom radial eq. | **ABSENT** | — | No Coulomb potential, no spherical harmonics. The natural lattice analogue (point-charge potential on Z_8^d) is not built. |
| Harmonic oscillator (ladder ops) | **ABSENT** | — | No a / a†. Free particle on path-graph is the only Hamiltonian. |

### Relativistic QM

| Equation | Status | Where | How |
|---|---|---|---|
| Klein-Gordon (m² + k̂²) | **ADJACENT** | notebook `§1b.5` (theoretical); not coded | Lattice scalar propagator G(k) = 1/(m² + k̂²) is the **named** mathematical substrate for piece value / range. Dybalski 2023 cited. Not instantiated as a function returning a propagator. |
| Dirac equation (γ-matrices) | **ABSENT** as code | notebook `§1b.5`, `§4`, `§1b.1` — framework named, not built | Notebook frames chess as "classical lattice fermion system" with Pauli exclusion (`n_i ∈ {0,1}`). Yumoto & Misumi 2024 cited for graph Laplacian ↔ lattice Dirac operator equivalence + Dirac zero-mode count = sum of Betti numbers. **No γ-matrix code, no spinor space, no Dirac operator built.** Pawn is identified as a **non-Hermitian chiral fermion** in the Hatano-Nelson sense (notebook §1b.1) — that's the closest fragment. |
| Weyl (massless 2-spinor) | **ABSENT** | — | Same as Dirac. No 2-spinor space. |
| Majorana | **ABSENT** | — | — |
| Bargmann-Wigner | **ABSENT** | — | — |

### QFT — gauge theories

| Equation | Status | Where | How |
|---|---|---|---|
| U(1) / QED Lagrangian / Maxwell | **ABSENT** | — | No gauge field, no F_μν. |
| SU(2) / weak / YM | **ABSENT** | — | — |
| SU(3) / strong / QCD YM | **ABSENT** | — | — |
| SU(2)×U(1) electroweak | **ABSENT** | — | — |
| SU(3)×SU(2)×U(1) SM | **ABSENT** | — | — |
| Spontaneous SB / Higgs | **ADJACENT (analogical only)** | notebook `§1b.5` | Pawn → queen promotion called "reverse Higgs mechanism" (gapped → gapless). Explicitly marked ANALOGICAL not mathematical. Fradkin-Shenker 1979 cited. **Not coded.** |
| Yukawa couplings | **ADJACENT** | notebook `§1b.5` "lattice realization of the Yukawa mass-range relationship" | Yukawa form G ~ exp(-mr)/√r is cited as the form of piece-range decay. Not built as a Lagrangian term. |

### QFT — propagators & amplitudes

| Equation | Status | Where | How |
|---|---|---|---|
| Feynman propagators | **ABSENT** as built | notebook §1b.5 names the lattice scalar propagator | Same as Klein-Gordon: named, not instantiated. |
| LSZ reduction | **ABSENT** | — | — |
| Tree-level vertex factors | **ABSENT** | — | — |
| One-loop self-energies | **ABSENT** | — | — |
| RGE / β functions | **ABSENT** | — | — |
| Path-integral measure | **ABSENT** | — | — |

### Scattering

All ABSENT (S-matrix, cross-section, decay width, optical theorem, Cutkosky, crossing, Mandelstam s/t/u). No multi-particle final-state formalism; chess is single-position-state.

### Geometric / algebraic adjuncts (where chess-spectral IS strong)

| Operation | Status | Where | How |
|---|---|---|---|
| Spectral decomposition of H | **FULL** | `qm_2d.py:570`, `qm_4d.py:468 measure_observable_distribution`; `_get_h0_eigenbasis_2d` | Closed-form eigh; (eigvals, Born probs) grouped by distinct eigenvalue. |
| Simultaneous eigenbasis (Δ, B_4 commutant) | **FULL — load-bearing** | `research/spectral_identity_4d_findings.md`; notebook 4D §745 Pre-flight 3 | Verified at machine precision: max ‖Δv-λv‖ = 3.3e-16; every Δ-eigenspace B_4-stable; max ‖[π(g), P_λ]‖ = 1.6e-13. **This is the canonical structural fact under the QM stack.** |
| Irrep-based Casimir | **PARTIAL** | `tables_4d.py` B_4 group action; D_4 irrep channels in `encoder.py` | D_4 / B_4 irrep typing of each channel (A_1 trivial, STD4 standard rep, FA_PAWN antisymmetric, etc.). The Casimir operator per se isn't built as `C_2 = sum_a T^a T^a`, but the irrep-projector decomposition is the same algebraic content. |
| Representation-theoretic mass formulas (GMO) | **ADJACENT** | notebook §1b.4 cites W-E theorem mass-free CG factor | D_4 CG selection rules for piece interactions tabulated; not an explicit GMO-style mass formula. |
| Action-angle decomp | **ABSENT** (chess-side) | — | (Cited from MEMORY as ephemerides feature — not in chess.) |
| Graph Laplacian on config lattice | **FULL** | `qm_4d_dynamics.py:2489 _build_h_free_4d`; `qm_2d_dynamics.py:136 _build_h_free_2d`; notebook §2 | Kron-sum of four (or two) P_8 path-graph Laplacians; integer spectrum; canonical. |
| HDC bind / bundle as QM measurement/superposition | **PARTIAL/IMPLICIT** | `encoder.py` (the 640-dim encoder IS a fixed-basis HDC bundle); `qm_2d.py:122 state_to_psi` casts the HDC bundle to ψ | The state_to_psi map is literally HDC-bundle → ψ; the channel-PVM decomposition acts as a partial-trace-like projection. Not framed in HDC vocabulary, but the algebra is identical. |
| Pseudo-Hermitian / PT-symmetric (Bender-Mostafazadeh) | **PROPOSED, FRAMEWORK STUBBED** | ADR-005; `qm_4d_dynamics.py:1693 _build_m_pawn_white_axis`; `_pawn_observable_decomp` | Pawn observables explicitly identified as candidates for η-pseudo-Hermitian / PT structure (parity = axis flip; time = colour flip). η operator not yet constructed; `H_pawn_*` raises `NotImplementedError` pointing to ADR-005. **This is the single most relevant absent-but-designed piece for srmech-C2.** |
| Probability current j_a = Im(ψ* ∂_a ψ) + continuity eq. ∂_t ρ + ∇·j = 0 | **FULL** | `qm_4d_bridge.py:1148 get_probability_current`; `_build_lattice_gradient_4d` | Anti-Hermitian central-difference ∂_a per axis (reflecting boundary), j = Im(ψ* ∂ ψ) summed over channels; continuity equation explicitly noted; divergence-free property tested. |
| Born-rule measurement + state collapse | **FULL** | `qm_4d_bridge.py:769 measure_at` | Cell-projection collapse + renormalisation; named-observable eigenvalue sampling. |
| Z_2 superselection | **FULL** | Pre-flight 1; `state_to_psi` sign multiplier; ADR-004 | Position dict / Z_2 quotient; 8 fixed-point positions empirically tabulated; canonical mechanism. |

---

## Adjacent-but-not-canonical (chess-spectral operations subsuming canonical content in non-textbook form)

1. **Graph-adjacency-as-Hamiltonian.** The five `H_rook_4`, `H_bishop_4`, … `H_knight_4` are graph adjacency matrices on Z_8^4 lifted to 4096×4096 Hermitians. Their eigenvalues are reach-centrality scores. **This is a Hamiltonian on a single-particle lattice Hilbert space, but the "potential" is not V(x) — it's the piece-specific hopping structure.** The canonical analogue is the tight-binding Hamiltonian H = sum_<ij> t_ij c†_i c_j on a graph; chess-spectral is exactly this in the single-particle sector (no fermionic algebra wrapped on top yet).

2. **The lattice gradient `_build_lattice_gradient_4d`.** Anti-Hermitian central-difference per axis. This **is** the lattice momentum operator p̂_a = -i∂_a (up to factor i). Never named as such. If we set ℏ=1, it gives lattice [x_a, p̂_a] up to boundary corrections. Canonical mom-ops in disguise.

3. **The 11-channel PVM.** A projection-valued measure on the encoded space `C^45056`. Channels carry both semantic (piece type) and irrep (B_4 representation) labels. **Each channel projector is functionally a "quantum number" projector** — a generalised quantum number labelling Hilbert subspaces. This is the categorical apparatus QFT uses to label particle species / charge sectors, just on a chess substrate.

4. **The eigenbasis-diagonal time evolution `V·diag(exp(-iλt))·V^H`** is the textbook canonical solution to TDSE for time-independent H. The 2D module verified ~196× speedup over `expm_multiply` with 1.8e-16 max-abs deviation — closed-form, not approximate.

5. **Pseudo-Hermitian / PT-symmetric pawn framework.** ADR-005 explicitly cites Bender-Boettcher (1998) and Mostafazadeh (2002, 2010). η-inner-product `<a|b>_η := <a|η|b>` named. **This is the canonical non-Hermitian-QM framework**, named precisely; the η-operator construction is stubbed not built. **The single most relevant Phase-C2 surface to absorb-and-finish, not re-invent.**

6. **The simultaneous-eigenbasis identity (Pre-flight 3).** Stated formally: "The encoder's 4096 modes are exactly the simultaneous eigenbasis of (Δ, B_4 commutant)." This is a representation-theoretic theorem (basis-as-irrep-decomposition) verified at machine precision. **In QM-textbook language this is the canonical statement that the eigenspaces of a maximal commuting set of observables (here: Δ + the B_4 commutant generators) form a complete basis.** Not phrased as such; the structural content is identical.

7. **Hatano-Nelson non-Hermitian pawn.** Notebook §1b.1: pawn = H-N model at t_L=0 (max-asymmetric hopping). This is a **canonical non-Hermitian QM model** with imaginary eigenvalues in the antisymmetric part, named, instantiated structurally in the encoder's FA_PAWN channels.

---

## Genuine gaps (real Phase C2 work items)

The following have no chess-spectral surface AND no obvious spectral-form adjacency:

1. **γ-matrices and any spinor space.** Chess-spectral has scalars on `C^4096`; there is no Cl(1,3) or Cl(4,0) construction, no spinor representation of B_4 lifted to a Dirac analogue. Notebook §1b.5 cites Yumoto-Misumi 2024 (graph Laplacian = scalar lattice + Wilson term; Dirac zero-mode count = sum of Betti numbers) but no Dirac operator code.

2. **Gauge connection on lattice.** No U(1) / SU(2) / SU(3) connection variables, no Wilson loop / plaquette construction. The B_4 group acts on the lattice but is not gauged.

3. **Lagrangian formalism.** Chess-spectral is Hamiltonian-only. No action, no path integral, no `S = ∫ d^4x L`.

4. **Multi-particle / Fock-space algebra.** Chess has Pauli exclusion at the position-occupation level (n_i ∈ {0,1}) by lattice geometry, but there is **no creation/annihilation operator algebra**, no antisymmetric multi-particle wavefunction, no Slater determinant, no Grassmann variable. The encoded state is a single 45056-dim ψ with all pieces, not a Fock-space element.

5. **Scattering / S-matrix.** No asymptotic states, no T-matrix, no on-shell condition, no amplitude → cross-section apparatus. Chess has no asymptotic regime.

6. **RGE / β-function / regularisation.** No flow equations, no renormalisation. Single fixed lattice scale; no coarse-graining infrastructure.

7. **Hydrogen atom / Coulomb / spherical harmonics.** Chess uses B_4 / D_4 (lattice point groups), not SO(3). The continuum rotational symmetry is missing by construction. Lattice spherical harmonics (Mädler / cubic harmonics) are not built.

8. **Harmonic oscillator / ladder operators.** No a / a†. Free Hamiltonian is the lattice Laplacian, not a quadratic-potential oscillator.

9. **Klein-Gordon-as-code.** The lattice propagator G(k)=1/(m²+k̂²) is named in §1b.5 but not exposed as a function. **This is a one-screen piece of code** — adding it to chess-spectral would be trivial; not adding it is a real gap.

10. **Heisenberg-picture / commutator algebra.** Schrödinger picture is the only path. No `commutator(A, B)` primitive (despite the natural fit with the integer-ALU preference for HDC binding).

---

## Phase C2 implications (srmech MFO/SM/QM operations layer)

1. **Cite-not-reimplement the kinematic + free-evolution layer.** Chess-spectral's `state_to_psi`, `inner_product`, `expectation`, `is_normalized` / `is_unitary` / `is_hermitian`, `evolve_under_h0`, `measure_observable_distribution`, `get_probability_current`, `measure_at`, `get_density_matrix_of` cover ~7 canonical single-particle QM operations cleanly. srmech-C2 should expose these via the `srmech.profiles["chess"]` path already shipped in v1.19.0. **Do not re-spell.**

2. **Pseudo-Hermitian / PT-symmetric primitive class.** ADR-005's η-metric framework is the cleanest absorption target. srmech-C2 should ship the **η-inner-product primitive** (`inner_product_eta(a, b, eta)`, `expectation_eta(O, psi, eta)`, `is_pseudo_hermitian(O, eta)`) with the chess pawn as the worked instantiation. This unblocks ADR-005's first-class η ship.

3. **Lattice propagator G(k) = 1/(m² + k̂²) as a closed-form operation.** Notebook §1b.5 names it; nothing builds it. srmech-C2 should ship `lattice_scalar_propagator(mass, k_lattice)` as a one-screen function; it cleanly closes the Klein-Gordon gap and matches the project preference for integer-ALU when m and k̂ are integer-encoded.

4. **Lattice gradient ↔ momentum operator naming.** `_build_lattice_gradient_4d` is the lattice p̂. srmech-C2 should expose it as `lattice_momentum(axis, lattice_shape, boundary)` and surface the commutator algebra `[x̂_a, p̂_b] ≈ iδ_ab` (modulo boundary corrections, which are quantifiable for P_8^d). This is canonical QM content currently anonymous.

5. **Casimir operators as group-Laplacian invariants.** The B_4 commutant structure already exists in chess-spectral; srmech-C2 should ship `casimir(group, irrep)` returning the quadratic Casimir value per irrep. This is the canonical SM-side ingredient and connects chess-spectral's irrep decomposition cleanly to SM language (where Casimirs label irreps of SU(N)).

6. **Gauge-connection primitive — flag as out of C2 scope.** Building U(1) / SU(N) connection variables, Wilson loops, plaquettes is a substantial new operation class. Phase C2 should flag this as **Phase C3 / future** and not bundle it.

7. **Dirac operator on the path-graph lattice.** Yumoto-Misumi 2024 (cited in notebook §1b.5) gives a clean recipe: graph Laplacian = scalar lattice + Wilson term, plus an antisymmetrised adjacency matrix; Dirac zero-mode count = sum of Betti numbers. **The chess B_4 commutant decomposition already provides candidate spinor decomposition (FA / FD channels carry the antisymmetric and diagonal content respectively).** srmech-C2 should ship `dirac_lattice(lattice, mass=0)` as a class instantiation using this recipe; it would convert chess's "non-Hermitian chiral pawn" framing into a real instantiated Dirac operator on `C^4096` × spinor.

8. **HDC ↔ QM equivalence operation.** The encoded 640-dim bundle IS the QM state under `state_to_psi`. srmech-C2 should expose this equivalence as an explicit conversion primitive (`hdc_to_psi`, `psi_to_hdc`) rather than burying it in `state_to_psi`. Connects to the integer-ALU preference and the resonant-bit-serialised HDC line.

9. **Born-rule observable distribution as the canonical measurement primitive.** `measure_observable_distribution(H, ψ)` returning (eigvals, probs) grouped by distinct eigenvalue is already the canonical spectral-measurement op; srmech-C2 should expose this verbatim. Add an `apply_born_collapse(H, ψ, sampled_eigval)` op (currently inlined in `measure_at`'s position branch only).

10. **Flag absent surfaces as out-of-scope** for Phase C2 with explicit deferral notes: Lagrangian/path-integral (Phase C3 or later), S-matrix/scattering (no asymptotic regime in chess; likely never relevant), RGE/β-functions (Phase C3+), hydrogen atom / continuum rotation (SO(3) vs B_4 substrate mismatch — Phase D?).

---

## Fermata (conductor input requested)

- The notebook's §1b.5 names lattice propagators / Yukawa form / Hatano-Nelson / Yumoto-Misumi as **cited but not coded** mathematical substrate. Should srmech-C2 ship these as concrete primitives (closing the gap), or stay at the citation layer (deferring to a future SM ops layer)? Items 3, 4, 7 above are the load-bearing instances.
- ADR-005's η-metric pawn observable is "Proposed (Option A; full PT for v1.7+)". srmech-C2's pseudo-Hermitian primitive (item 2 above) could **finish** ADR-005 — should this be co-shipped or kept as a separate chess-spectral PR?

---

## Files of interest (absolute paths)

- `D:\GitHub\mlehaptics\docs\chess-maths\chess-spectral\python\chess_spectral\qm_2d.py`
- `D:\GitHub\mlehaptics\docs\chess-maths\chess-spectral\python\chess_spectral\qm_2d_dynamics.py`
- `D:\GitHub\mlehaptics\docs\chess-maths\chess-spectral\python\chess_spectral\qm_4d.py`
- `D:\GitHub\mlehaptics\docs\chess-maths\chess-spectral\python\chess_spectral\qm_4d_dynamics.py`
- `D:\GitHub\mlehaptics\docs\chess-maths\chess-spectral\python\chess_spectral\qm_4d_bridge.py`
- `D:\GitHub\mlehaptics\docs\chess-maths\chess-spectral\python\chess_spectral\engine\eval\qm.py`
- `D:\GitHub\mlehaptics\docs\chess-maths\chess-spectral\docs\adr\qm_4d\ADR-002-time-evolution-semantics.md`
- `D:\GitHub\mlehaptics\docs\chess-maths\chess-spectral\docs\adr\qm_4d\ADR-005-pawn-pseudo-hermitian-eta-metric.md`
- `D:\GitHub\mlehaptics\docs\chess-maths\chess_spectral_research_notebook.md` (§1b.1, §1b.5, §15, §16)
- `D:\GitHub\mlehaptics\docs\chess-maths\chess_spectral_4d_notebook.md` (qm_4d Pre-flight Findings, §745–§813)
- `D:\GitHub\mlehaptics\docs\chess-maths\chess-spectral\python\research\spectral_identity_4d_findings.md`

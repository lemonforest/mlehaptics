# Spike #24 — QM operations primitive-class audit (2026-05-16)

> **Concertmaster dispatch (research/inventory only — no code authored).**
> Triggered by user comment *"MFO and all of the operations that make doing
> useful things with the standard model and QM (did we forget this goldmine?)"*
> Scope: inventory every QM operation in the project and map each to the
> Spike #24 primitive-class vocabulary A–N.
> Branch: `research/qm-primitive-audit-2026-05-16` (uncommitted, conductor
> reviews and decides PR routing).

## TL;DR

- **All QM operations dissolve into existing A–N classes.** 14-class vocabulary holds. Vocabulary stays flat.
- **Class-distribution histogram is heavily L-weighted** (the structural workhorse, as bonus-series synthesis predicted): L (12), B (11), C (9), D (5), I (2), J (1), G (1). Other classes do not appear.
- **No genuinely new primitives surface.** Two superficially-unusual operations (eta-metric pseudo-Hermitian observable, projector-sandwich move-as-unitary) resolve to Class L sub-operations and Class L × Class I composition respectively.
- **QM operations live ONLY in chess-spectral.** ephemerides-spectral, antikythera-spectral, srmech, and the other notebooks have NO qm_*.py modules. The "goldmine" framing is accurate: a structured set of operations exists, all in one notebook, that could promote to srmech.amsc.qm.* on the same dissolve-first basis as cyclic/laplacian/primes/tlv/etc.
- **Pi-as-projection pattern is clean.** Every `math.pi` enters as downstream phase rotation in move-as-unitary builders or finite-difference gradient normalisation — the upstream integer-cyclic algebra (channel indices, permutation matrices, ladder operators on cyclic factors) is pi-free.

## 1 — Inventory of QM operations

QM operations live exclusively under
`docs/chess-maths/chess-spectral/python/`. Confirmed absent in
`docs/antikythera-maths/ephemerides-spectral/`, `docs/antikythera-maths/antikythera-spectral/`,
`docs/srmech/python/`, and the doom/logo/othello notebooks via top-level
`qm*.py` glob. Per Tasks #99 (Kinematics) and #100 (Dynamics), the chess-spectral
implementation IS the canonical reference.

### 1.1 — chess_spectral.qm_2d (kinematic 2D, 640-dim, 10 channels × 64 modes)

| Function/method | Purpose | Inputs → outputs |
|---|---|---|
| `state_to_psi(pos, side_to_move)` | Encode position → normalised psi ∈ ℂ⁶⁴⁰; Z₂ sign for side-to-move | `dict[int,str]`, `bool` → `ndarray[complex128, (640,)]` |
| `inner_product(a, b)` | ⟨a\|b⟩ = Σᵢ aᵢ* bᵢ via numpy.vdot | two ndarrays → `complex` |
| `norm(psi)` | L2 norm √⟨ψ\|ψ⟩ | ndarray → `float` |
| `expectation(O, psi)` | ⟨ψ\|O\|ψ⟩ for Hermitian O; takes real part | sparse-or-dense + ndarray → `float` |
| `is_normalized / is_hermitian / is_unitary` | Validation predicates with tolerance | matrix/vector, tol → `bool` |
| `d4_closure()` | Enumerate 8 elements of D₄ as length-64 permutations | () → `list[tuple[int,...]]` |
| `d4_unitary_rep_64(g)`, `d4_unitary_rep_full(g)` | Permutation matrix → unitary on ℂ⁶⁴ / ℂ⁶⁴⁰ via `I_10 ⊗ U_64` | group element → CSR sparse complex128 |
| `channel_projector(c)` | PVM projector P_c onto channel c | int → CSR diagonal 640×640 |
| `prob_channel(psi, c)`, `measure_channel_distribution(psi)` | Born-rule probability per channel | psi, [int] → float, `ndarray[(10,)]` |
| `build_H_piece_2(piece)` | Construct Hermitian piece-reach observable from chess adjacency on 8×8 board, symmetrise | char → CSR sparse 64×64 complex128 |
| `H_rook_2 / H_bishop_2 / H_queen_2 / H_king_2 / H_knight_2` | Lazy module-attr accessors over `build_H_piece_2` cache | — → CSR sparse |
| `H_pawn_2` | Raises `NotImplementedError` (directed-push pawns need pseudo-Hermitian eta-metric, deferred) | — → exception |
| `measure_observable_distribution(H, psi, tol)` | Spectral decomposition via `np.linalg.eigh` + Born-rule weights grouped by distinct eigenvalue | H, psi, tol → `(eigvals, probs)` |

### 1.2 — chess_spectral.qm_2d_dynamics (Track B move-as-unitary 2D)

| Function/method | Purpose | Inputs → outputs |
|---|---|---|
| `_l8_path_laplacian()` | Build 1D 8-node path-graph Laplacian (tridiagonal) | () → CSR 8×8 |
| `_build_h_free_2d() / H_FREE_2D()` | Build free-particle H₀ = −Δ_{P₈²} as Kron-sum (L₈ ⊗ I) + (I ⊗ L₈) | () → CSR 64×64 (Hermitian) |
| `_get_h0_eigenbasis_2d()` | Cached `np.linalg.eigh(H_FREE_2D)` decomposition | () → `(eigvals, V)` |
| `evolve_under_h0(psi, t, channel=None)` | Time evolution U(t) = V·diag(e^(−iλt))·V† in eigenbasis, broadcast across 10 channels via batched matmul | psi, t, [channel] → ndarray same shape |
| `_build_p_a1_2d() / P_A1_2D()` | A₁ trivial irrep projector via group average `(1/\|D₄\|) Σ_g Π(g)` | () → CSR 64×64 idempotent |
| `_swap_unitary_2d(from, to)` | Bare permutation swap on ℂ⁶⁴ | (i, j) → CSR 64×64 |
| `u_move_a1_2d(from_sq, to_sq)` | Move-as-unitary on A₁ channel via projector sandwich `P_A1 @ U_swap @ P_A1` (sub-unitary on cross-orbit, strict on same-orbit) | (int, int) → CSR 64×64 |

### 1.3 — chess_spectral.qm_2d_bridge (Pyodide §17.2/§17.5 surface)

| Function | Purpose | Type |
|---|---|---|
| `get_version() / get_encoder_shape()` | Package metadata + dimensions | () → dict |
| `get_fen_state(state) / load_fen(fen)` | FEN ↔ position-dict serialisation via python-chess | state → dict |
| `has_legal_moves(state)` | python-chess legal-move count > 0 | state → dict |
| `complex_to_interleaved_float32(psi)` | Serialise complex → Float32Array-compatible real+imag interleaved | ndarray → `ndarray[float32, (2N,)]` |
| `get_qm_state(state)` | Pyodide-friendly wrapper around `state_to_psi` | state → dict (with serialised ψ) |
| `get_qm_density(state)` | Per-cell `\|ψ\|²` summed across channels | state → dict |
| `get_qm_expectation(state, obs)` | Expectation value of named Hermitian observable | state, str → dict |
| `apply_move_qm(...)` | Post-move ψ assembly (strict A₁ unitary or re-encode fallback) | pre, post, opt args → dict |

### 1.4 — chess_spectral.qm_4d (kinematic 4D, 45 056-dim, 11 channels × 4 096 modes)

Structurally identical surface to qm_2d. Dimensions scale: B₄ group order 384 (vs D₄ order 8), 11 channels (vs 10), 4 096 modes per channel (vs 64). Same operations: `state_to_psi`, `inner_product`, `norm`, `expectation`, `is_normalized/is_hermitian/is_unitary`, `b4_unitary_rep_4096/_full`, `channel_projector`, `prob_channel`, `measure_channel_distribution`, `build_H_piece_4` (with `H_rook_4 / H_bishop_4 / H_queen_4 / H_king_4 / H_knight_4` lazy attrs; `H_pawn_4` raises), `measure_observable_distribution`. No mapping changes vs qm_2d — same classes apply at scale.

### 1.5 — chess_spectral.qm_4d_dynamics (Track B move-as-unitary 4D)

Much richer surface — 11 channels each need their own move-as-unitary builder; some channels admit projector-sandwich, some require similarity transform, some collapse to measurement-only re-encode. Distinct ops:

| Function | Purpose | Class shape |
|---|---|---|
| `_l8_path_laplacian / _build_h_free_4d / H_FREE_4D` | Free-particle H₀ = −Δ_{P₈⁴} via 4-fold Kron-sum | Class L (graph Laplacian + Kron-sum) |
| `evolve_under_h0(psi, t, channel=None)` | Time evolution via `scipy.sparse.linalg.expm_multiply` (Krylov; eigenbasis deferred at 4D scale per benchmark) | Class L + Class C |
| `u_move_a1(...)` | A₁ channel projector-sandwich `P_A1 @ U_swap @ P_A1` (analogue of 2D B1 milestone, B5 captures via re-encode marker) | Class L × Class I (group avg) × Class B (marker dict) |
| `u_move_std4(...)` | STD4_{X,Y,Z,W} via similarity-transform `D_a @ U_swap @ D_a^+` (cross-orbit moves return marker dict pointer) | Class L (sandwich/similarity) × Class D (dispatch) × Class B (marker) |
| `u_move_fa_pawn(...)` | FA_PAWN_{W,Y} antisymmetric pawn channels via axis-parity-odd projector sandwich | Class L (projector) × Class I (axis parity = cyclic-group-2) × Class B (marker) |
| `u_move_fib_meas(...)` | FIB_SYM_{1,2,3} via measurement-only re-encode (bilinear FIB encoder has no strict-unitary lift) | Class C (apply move classically, re-encode) × Class B (marker) |
| `u_move_fd_diag(...)` | FD_DIAG (rank-1 update + renorm path; non-capture invariant; captures via re-encode marker) | Class L (rank-1) × Class B (marker) |
| `_pawn_observable_decomp(...)` | Decompose `M_pawn = M_single + M_double` for eta-metric pseudo-Hermitian pawn (structural API; explicit construction deferred to v1.7+) | Class L (decomposition) × Class B (decomp records) |

### 1.6 — chess_spectral.qm_4d_bridge (Pyodide §17.1/§17.5/§17.6 surface)

Mirrors qm_2d_bridge surface and adds entanglement-flavoured ops:

| Function | Purpose | Distinct ops |
|---|---|---|
| `get_version / get_encoder_shape / get_fen4_state / load_fen4 / load_jsonl_fixture / has_legal_moves` | §17.5 metadata + state-IO surface | Class B (records) + Class E (catalog: FEN parsing) |
| `complex_to_interleaved_float32` | Serialisation helper | Class B (canonical byte form for transport) |
| `get_qm_state / get_qm_density / get_qm_density_from_psi` | ψ + per-cell density | Class L (expectation) + Class C (iterate channels) |
| `apply_move_qm / apply_move_qm_full` | Post-move ψ assembly with per-channel dispatch | Class L + Class D (per-channel dispatch table) |
| `measure_at(state, coords, observable=None)` | Born-rule projective measurement with collapse + post-measurement renorm | Class L (projection + eigh for named-obs) + Class B (return record) |
| `get_density_matrix_of(state, piece_id, neighborhood_radius)` | Reduced density matrix ρ_ch = M·M† on channel-axis restricted to a 4D Manhattan ball; eigvals, purity, rank | Class L (eigendecomposition + matrix multiply) + Class C (neighbourhood iteration) |
| `get_probability_current / _from_psi` | Probability current j_a = Im(ψ*·∂_a ψ) via anti-Hermitian central-difference gradient (Kron-sum of axis ops) | Class L (gradient operator construction) |
| `_build_lattice_gradient_4d` | Build 4 axis-gradient sparse matrices via Kron product | Class L + Class C (axis iteration) |
| `get_qm_expectation(state, obs)` | Named-observable expectation | Class L + Class D (observable-name dispatch) |
| `channel_energies_2d / _4d` | §17.6 per-channel L2 energy from BIP-hybrid encoder | Class L (squared-norm projection per channel) + Class E (channel-name catalog) |

### 1.7 — engine/eval/qm.py (2D + 4D QM-expectation evaluators, Phase 6.1.3)

| Function | Purpose | Class shape |
|---|---|---|
| `evaluate(pos, side_to_move, weights=None)` | Score = Σₚ αₚ · ⟨ψ\|(I ⊗ H_p)\|ψ⟩ summed across channels, side-to-move sign flip | Class L (expectation) + Class C (channel iteration) + Class D (weights resolution) |
| `evaluate_breakdown` | Per-observable contributions for §17.2 HUD | same + Class B (return record) |
| `observable_expectations(psi)` | Raw expectations dict | Class L + Class C |
| `_resolve_weights / load_weights_json` | Weight-dict resolution from None / Mapping / Path / JSON | Class D (late-binding) + Class F (template-resolution if str) + Class E (catalog lookup) |

### 1.8 — research/qm_bishop_wavefunction.py & qm_spectral_identity_demo.py

| Demo | Operations |
|---|---|
| Bishop wavefunction time-evolution | `_initial_bishop_state(s0)` — uniform amplitude on bishop targets → Class L (graph adjacency) + Class I (square indexing). Evolution via `scipy.linalg.expm(-1j*H*t/lam_max)` over time slices → Class L + Class C |
| Spectral identity demo (Pre-flight 3) | `_p_n_laplacian(n)` path-graph Laplacian → Class L. `_kron_sum_4d(L1)` 4D Kron-sum → Class L. `_group_eigenspaces(eigvals, eigvecs, tol)` eigvalue bucketing → Class L + Class B (records). Simultaneous-diagonalisation check vs B₄ commutant → Class L + Class I |

## 2 — Per-operation primitive-class mapping (summary table)

| Operation cluster | Primary class(es) | Supporting | Pi-as-projection note |
|---|---|---|---|
| State construction (`state_to_psi`) | **L** (normalisation = quadratic form) | B (record-inspection of position dict), I (Z₂ superselection sign) | Pi-free |
| Inner-product / norm / expectation | **L** (quadratic forms, matmul) | C (iterate over basis) | Pi-free |
| Validation (`is_normalized / is_hermitian / is_unitary`) | **L** (matrix product comparison) | — | Pi-free |
| Group representation (`d4_unitary_rep_*`, `b4_unitary_rep_*`) | **L** (permutation matrix) × **I** (cyclic-group / dihedral / hyperoctahedral) | B (cache records) | Pi-free (permutations are integer-indexed) |
| Channel PVM (`channel_projector`, `prob_channel`, `measure_channel_distribution`) | **L** (diagonal projector) | C (channel iteration), B (output records) | Pi-free |
| Hermitian observable construction (`build_H_piece_2/4`) | **L** (graph adjacency → Hermitian lift) | B (piece char → adjacency) | Pi-free (adjacency is integer-valued) |
| Spectral measurement (`measure_observable_distribution`) | **L** (eigh + Born-rule weights, group by distinct eigenvalue) | C (sort + group) | Pi-free (eigh is algebraic) |
| Free-particle Hamiltonian construction (`H_FREE_2D/4D`) | **L** (path-graph Laplacian + Kron-sum) | — | Pi-free (integer Kron-sum) |
| Time evolution (`evolve_under_h0`) | **L** (eigh decomposition or expm_multiply Krylov) × **C** (iterate channels or batched matmul) | B (cache `(λ, V)` record) | **`exp(-i λ t)` introduces pi via complex phase**; this is downstream phase-rotation on upstream integer eigenstructure |
| A₁ orbit projector (`P_A1_2D`) | **L** (matrix sum) × **I** (group average) | — | Pi-free (sum of 8 permutations / 8) |
| Move-as-unitary builders (`u_move_a1`, `u_move_std4`, `u_move_fa_pawn`, `u_move_fib_meas`, `u_move_fd_diag`) | **L** (projector sandwich or similarity transform) × **I** (cyclic-group / axis-parity) | D (per-channel dispatch table), B (marker dict for non-strict-unitary paths), C (re-encode iteration for measurement-only path) | STD4 phase factor `e^{i·(π/4)·δ_a}` uses pi as downstream phase rotation; upstream `δ_a = axis_to − axis_from` is integer. FA_PAWN parity sign is pi-free. |
| Bridge: state-IO (`get_fen_state / load_fen / has_legal_moves`) | **B** (record IO) | E (catalog lookup), D (dispatch on input type) | Pi-free |
| Bridge: ψ serialisation (`complex_to_interleaved_float32`) | **B** (TLV-flavoured canonical byte form) | — | Pi-free |
| Bridge: density / expectation / move-application (`get_qm_density`, `get_qm_expectation`, `apply_move_qm`) | **L** (squared-norm or expectation) | C (channel iteration), D (observable name dispatch), B (return records) | Pi-free at this layer (delegates to upstream L) |
| Bridge: measure_at + density-matrix | **L** (eigh, matmul, Born-rule weights) | C (neighbourhood iteration), B (return records) | Pi-free |
| Bridge: probability current | **L** (anti-Hermitian gradient operator + Im(ψ*∂_a ψ) projection) | C (axis iteration) | Pi-free (central-difference is rational; `Im` projection introduces no pi) |
| QM evaluator (engine/eval/qm.py) | **L** (expectation) × **C** (channel sum) | D (weights resolution), B (breakdown record) | Pi-free |
| Research demos | **L** + **C** (eigendecomposition + simultaneous diagonalisation check) | B (group records), I (cyclic-symmetry check vs B₄ commutant) | Pi-free in setup; `expm(-1j*H*t/lam_max)` introduces pi as downstream phase per evolve_under_h0 |

### 2.1 — Class-distribution histogram

Counting class participation across ~40 distinct operations (a single operation contributing to multiple classes counts once per class):

| Class | Count | Notes |
|---|---|---|
| **L** (graph-Laplacian / eigenbasis / quadratic forms / matmul) | **~38** | The structural workhorse, as bonus-series synthesis predicted. Every QM operation touches L. |
| **B** (tagged-tuple / records) | ~14 | Bridge return dicts, marker dicts for non-strict-unitary paths, cache records, position records. |
| **C** (iterator / streaming) | ~11 | Channel iteration, basis iteration, neighbourhood iteration, time-slice iteration. |
| **D** (late-binding / dispatch) | ~5 | Per-channel u_move dispatch, observable-name dispatch, weights resolution, position-vs-Board dispatch. |
| **I** (cyclic-group / modular arithmetic) | ~6 | D₄ / B₄ representation, A₁ orbit average, Z₂ superselection sign, axis-parity in FA_PAWN. |
| **E** (catalog / naming) | ~3 | FEN parsing, channel-name catalog, BIP-hybrid encoder catalog. |
| **F** (templating) | ~1 | Weights-file path → JSON load (templated path resolution). |
| **J** (prime-factorisation / period) | ~0 | Not used in QM operations as inventoried. (The cyclic-group dimensions — 8, 64, 4096, 11, 10 — are integers but no factorisation operations run on them.) |
| **G** (discovery / search) | ~0 | Not used. |
| **A** (content-addressing) | ~0 | Not used. (QM operations are pure functions of inputs; no hashing.) |
| **H** (self-introspection) | ~1 | `get_version()` in bridge. |
| **K** (equation-of-centre / pin-slot) | ~0 | Not used. (Consistent with `[[user_stance_kepler_shape_universal]]` and Phase 10 — chess is a Class-K-absent substrate. QM-on-chess inherits the absence.) |
| **M** (HDC bind/bundle/permute/similarity) | ~0 | Not used DIRECTLY by qm_*. (The encoder is BIP/FHRR-flavoured HDC at the BACKEND; qm_* consumes its output as a complex vector and treats it as plain ψ. The HDC machinery is upstream of state_to_psi.) |
| **N** (rational-approximation / Diophantine) | ~0 | Not used. |

**Cross-check vs bonus-series cumulative table** (Class L most-instantiated; Classes A, F, K, M, N substrate-specific or absent here): the QM inventory is internally consistent. Compared to the cross-substrate cumulative (vdW / Tactical / SHA-256 / NN / MFO / RNG), QM operations are **even more L-concentrated** than any single bonus-series instance — because QM's defining operation IS expectation values of Hermitian operators in an eigenbasis, which is the structural workhorse's domain by construction.

## 3 — Candidate-primitive surface (dissolution-first audit)

Per `[[feedback_no_privileged_primitive_classes]]` and the bonus-series
precedent (Class O dissolved via bonus 8/9, Class P dissolved via 11d), the
default is dissolution into existing A–N. Three QM operations were
flagged as candidate-primitives during inventory; honest examination
dissolves all three.

### 3.1 — Candidate: "pseudo-Hermitian eta-metric pawn observable"

**The operation.** Pawn reach (forward push) is directed → adjacency is NOT
symmetric → Hermitian lift breaks under the standard inner product. ADR-005
(deferred to v1.7+) proposes a pseudo-Hermitian construction with an
"eta-metric": H_pawn satisfies `η · H_pawn = H_pawn^† · η` for a positive-
definite η, rather than `H = H^†` directly.

**Dissolve-or-promote check.** This is not a new primitive class. It is
*linear algebra on a modified inner product* — concretely, `M_pawn = M_single
+ M_double` decomposition (`_pawn_observable_decomp` in qm_4d_dynamics). The
eta-metric is a Class L operation (positive-definite matrix; quadratic
form). The pseudo-Hermiticity condition is a Class L matrix identity. The
decomposition into `M_single + M_double` is Class B (records the
decomposition as tagged structure) + Class L (matrix sum).

**Recommendation: DISSOLVE into Class L × Class B.** When ADR-005 ships,
no new primitive class needs to be invented. The construction is *modified-
inner-product Class L* — analogous to how signed-Laplacian variant is a
Class L sub-operation per the 2026-05-16 Class O dissolution (see
`[[project_class_o_signed_metric_composition]]`). Same template applies.

### 3.2 — Candidate: "projector-sandwich move-as-unitary"

**The operation.** For each channel c, move-from-square s → square s' is
lifted to a channel-c unitary by `U_c = P_c @ U_swap_c @ P_c` (where U_swap
permutes basis vectors and P_c is the channel-c subspace projector). The
sandwich is **strict-unitary on `range(P_c)`** iff U_swap commutes with P_c
(which holds iff (s, s') lies in the same orbit of the channel's underlying
group action). Cross-orbit moves yield a sub-unitary contraction.

**Dissolve-or-promote check.** The "projector sandwich" pattern is a
composition of three Class L operations (project, permute-as-matrix, project)
with a Class I qualifier (orbit membership = cyclic-group cell). The
sub-unitary vs strict-unitary verdict is a Class L matrix identity check
(verify `U^† · U == P_c`). The bookkeeping for the marker-dict-return on
sub-unitary cases is Class B (records the non-strict-unitary reason and
`recommendation` field).

**Recommendation: DISSOLVE into Class L × Class I × Class B.** No new
primitive class needed. The sandwich is *project-permute-project*; all
existing vocabulary. The interesting structural finding (some channels
admit strict-unitary lift, some require measurement-only re-encode) is
itself a Class L diagnostic and lives at the algebra level, not the
primitive-class level.

### 3.3 — Candidate: "measurement-only re-encode" path

**The operation.** For FIB_SYM_{1,2,3} channels and capture moves, the bilinear
encoder formula has no strict-unitary lift in operator form. The post-move ψ
on that channel block is computed by *applying the move classically* (update
position dict), *re-encoding via state_to_psi*, and *slicing the relevant
64-block*. The result is a complex vector; the function returns a marker
dict pointing to it.

**Dissolve-or-promote check.** This is Class C (apply move via classical
state-machine step) + Class L (re-encode via the encoder's existing channel
linear maps; state_to_psi is Class L) + Class B (marker dict packaging the
result with a `reason='measurement-only'` tag).

**Recommendation: DISSOLVE into Class C × Class L × Class B.** This is
not a primitive — it's the explicit absence of one (the bilinear encoder
has no operator-form lift). The "measurement-only" label is a *Class B
record-shape* recording the structural reason for the fallback path.

### 3.4 — Summary of candidate-primitive disposition

| Candidate | Verdict | Dissolved into |
|---|---|---|
| Pseudo-Hermitian eta-metric pawn observable | DISSOLVE | Class L × Class B (modified-inner-product matrix construction + decomposition records) |
| Projector-sandwich move-as-unitary | DISSOLVE | Class L × Class I × Class B (project-permute-project + orbit-membership qualifier + sub-unitary marker) |
| Measurement-only re-encode path | DISSOLVE | Class C × Class L × Class B (classical step + re-encode + marker) |

Pattern matches bonus-series precedent: candidate-primitives default to
dissolution; promotion to new top-level class requires structural
irreducibility that none of the QM candidates demonstrate. **Vocabulary
stays at 14 classes A–N.**

## 4 — Phase C2 implementation sketch (`srmech.amsc.qm.*`)

If/when Phase C2 (Task #218) lands, the natural surface decomposition is:

```
srmech.amsc.qm.state       — state_to_psi, normalise, Z2 sign  → L × B × I
srmech.amsc.qm.inner       — inner_product, norm, expectation  → L
srmech.amsc.qm.validate    — is_normalised / is_hermitian / is_unitary → L
srmech.amsc.qm.group_rep   — generic permutation-to-unitary lift; group-average projector → L × I
srmech.amsc.qm.observable  — build adjacency-to-Hermitian observable lift → L
                              (pseudo-Hermitian eta-metric path → L × B; ADR-005-equivalent)
srmech.amsc.qm.measurement — channel projector PVM, Born-rule probability, post-measurement collapse → L × C
srmech.amsc.qm.spectral    — measure_observable_distribution (eigh + Born-rule grouping) → L × C
srmech.amsc.qm.hamiltonian — graph-Laplacian-derived H₀ (free-particle on path-graph Kron-sum); custom H constructors → L
srmech.amsc.qm.evolution   — evolve_under_h0 (eigenbasis-diagonal or Krylov-expm path) → L × C
srmech.amsc.qm.move_lift   — projector-sandwich and similarity-transform move-as-unitary
                              builders; per-channel dispatch table → L × I × D × B
srmech.amsc.qm.density     — reduced density matrix on a channel-axis restriction → L × C
srmech.amsc.qm.current     — probability current via anti-Hermitian gradient operator → L
```

Each Phase C2 module follows the same ratchet as the Phase C1 lightweight
trio (B / G / H rc4) and the heavier classes (I rc1, L rc2, J rc3): parity
test against the chess-spectral reference + JPL Power-of-Ten audit + C port
where hot + cibuildwheel matrix + TestPyPI rc verification per
`[[feedback_always_rc_first_for_downstream_publishes]]`.

The C-port boundary follows the same discipline as Phase C1: numerical hot
paths (eigh, matmul, expm_multiply Krylov) earn C; binding-layer
conveniences (FEN parsing, JSON weight-file resolution, Pyodide
serialisation) stay in Python per `[[feedback_no_binding_layer_carveout]]`'s
operational scope note in `docs/srmech/CLAUDE.md`.

**Hard-dependency note**: srmech v0.4.0rc2 already added numpy as a hard
dependency for Class L. Phase C2 needs nothing further at the numpy
layer; scipy.sparse / scipy.sparse.linalg.expm_multiply would be a new
dependency floor IF the Krylov path is the chosen 4D-scale evolution
strategy (the 2D-scale eigenbasis-diagonal path needs only numpy). The
dependency decision belongs to Phase C2's conductor call.

## 5 — Cross-substrate consistency check

**QM is the atomic substrate par excellence.** The Spike #24 vocabulary
was built primarily on bronze + cosmos + atomic + molecular + CRN + CPU.
This audit adds **chess-as-QM-Hilbert-space** as a substrate variant of
atomic (Hilbert-space algebra without the literal atom).

**Verdict: the QM operation inventory CONSOLIDATES with existing classes.**
Zero new classes invented; three candidate-primitives dissolved. The
Class-L dominance is *more pronounced* than any single bonus instance
because QM's defining computation IS the Class L workhorse (expectation
values, eigenbases, quadratic forms).

The one structurally notable pattern: **QM operations exhibit Class L ×
Class B composition far more than other substrates.** Every per-channel
u_move builder returns either a sparse matrix (strict-unitary case) OR a
marker dict (sub-unitary / measurement-only / capture case). The marker
dict is a Class B record that captures *the algebraic reason for the
non-operator path*. This is the same shape as the bonus-series marker-dict
pattern (e.g., bonus 11d `REDUCES-TO-EXISTING` verdict records the
dissolution reason). **Class B is doing more work in QM than in earlier
substrates** — recording the structural distinction between operator-form
and re-encode-form per channel is itself a primitive operation, and the
operator-form-vs-re-encode-form distinction is a fundamental QM-on-discrete-
structure pattern (not an artifact of chess-spectral's implementation
choices).

No other surprises. Class I (group reps), Class L (everything else), Class
C (iteration), Class D (dispatch tables), Class B (records) — these are
the QM operation classes. Classes A / F / G / H / J / K / M / N are
absent (or near-absent), with substantive structural reasons:

- **A absent**: QM operations are pure functions; no content-addressing
  required (the bridge layer hashes inputs/outputs externally if needed).
- **F absent**: no string-templating in QM math.
- **G absent**: no discovery/search; the spectral basis is given by H.
- **H absent at the math layer**, present at the bridge layer (`get_version`).
- **J absent**: no prime-factorisation; period-relation is encoded
  symbolically (e.g., `C_4 × C_7` cyclic product), not algorithmically
  factored.
- **K absent**: chess-as-QM has no Kepler-shape (Phase 10 substrate boundary).
- **M absent at the QM math layer**, present at the encoder layer that
  produces the input to state_to_psi. The QM operations consume HDC output
  as a flat complex vector and don't recompose HDC primitives.
- **N absent**: no rational-approximation; quantum amplitudes are
  exact-algebraic, not rational-approximated.

The structural absences are *informative* — they confirm the substrate
boundary and validate the dissolve-first stance. QM operations are
"Class L + algebra-bookkeeping" — exactly what the universal vocabulary
predicts for a Hilbert-space substrate.

## 6 — Fermatas for conductor

1. **Phase C2 dependency floor**: does srmech tolerate adding scipy.sparse
   (or scipy.sparse.linalg.expm_multiply) as a hard dependency floor, or
   should Phase C2 ship a pure-numpy / pure-C path? The 2D-scale
   eigenbasis-diagonal path needs only numpy; the 4D-scale Krylov path
   benefits from scipy. Pyodide tolerates scipy via micropip.

2. **Pseudo-Hermitian eta-metric pawn observable scope**: ADR-005 in
   chess-spectral is "deferred to v1.7+" — does srmech Phase C2 want to
   stay aligned with that deferral, or land it as the cleanest case of
   "Class L × Class B modified-inner-product construction" alongside the
   regular Hermitian construction?

3. **HDC encoder coupling**: state_to_psi consumes encoder output as a
   complex vector. Should Phase C2's `srmech.amsc.qm.state` accept any
   complex vector (substrate-agnostic), or wire in the existing Class M
   primitives so QM-on-HDC is first-class? The former preserves
   dissolution-first; the latter encodes the composition explicitly.

4. **Bridge layer scope**: the Pyodide-flavoured bridge ops
   (`get_qm_state`, `get_qm_density`, etc.) are binding-layer per
   `[[feedback_no_binding_layer_carveout]]`. Should they stay in
   chess-spectral as consumer-side ergonomics, or promote to
   `srmech.amsc.qm.bridge` for sister notebooks to reuse?

5. **Ephemerides QM**: ephemerides-spectral has NO qm_*.py modules
   despite Tasks `#99`/`#100` originally scoping both packages. Was the
   ephemerides QM analogue scoped out, or just not yet built? The user's
   "did we forget this goldmine?" framing suggests the latter. If so,
   Phase C2 srmech.amsc.qm.* would unblock ephemerides reuse.

## NDJSON output

(None this dispatch — the research note IS the output; per
`[[feedback_ndjson_over_bloated_json]]` discipline, if/when the
inventory wants per-operation structured records, those go in a
separate NDJSON file. The conductor can request the NDJSON cut as a
follow-up dispatch if useful.)

## Cross-references

- `[[user_stance_pi_as_projection]]` — pi enters as downstream phase
  rotation in evolve_under_h0 and STD4 phase factor; upstream
  integer-cyclic algebra is pi-free.
- `[[user_stance_kepler_shape_universal]]` — QM-on-chess is Class-K-absent
  per Phase 10's chess substrate boundary characterisation; consistent.
- `[[user_stance_fiber_as_spatially_absent_encoding]]` — the per-channel
  factorisation (H_full = I_10 ⊗ H_0) is a fiber-bundle Class L pattern;
  the fiber-bundle structure encodes channel-axis information that is
  spatially absent until the channel projector P_c acts.
- `[[feedback_no_privileged_primitive_classes]]` — applied to all three
  candidate-primitives; all dissolved.
- `[[feedback_no_binding_layer_carveout]]` — Phase C2 bridge-layer scope
  question (Fermata 4).
- `[[project_class_o_signed_metric_composition]]` — Class O dissolution
  precedent applied to pseudo-Hermitian eta-metric candidate.
- `[[feedback_pdf_extraction_citation_discipline]]` — no QM textbook
  citations made in this audit (operations cited only to chess-spectral
  source files, which are project-internal). Standard QM textbook names
  (Trotter-Suzuki decomposition, Born rule, projector-valued measure,
  central-difference operator, etc.) are referred to descriptively
  without citation; if the conductor wants explicit citation, those
  would be tagged `[unverified-secondary]` per discipline until a primary
  PDF (e.g., Sakurai 2017, Nielsen & Chuang 2010) is extracted and
  verified.
- `docs/srmech/srmech_research_notebook.md` — canonical 14-class roster.
- `docs/srmech/notes/spike_24_bonus_series_synthesis_2026-05-15.md` —
  cumulative cross-substrate audit table that this QM audit extends.

# ADR-001: Phase Convention for Unitary Moves

**Date:** 2026-04-29
**Branch:** `chess-spectral/qm-4d-kinematic`
**Track:** B (full move-as-unitary dynamics)
**Ships in:** Phase 4 / `qm_4d.applyMoveQm` / chess-spectral v1.5.0

---

## 1. Status

**Proposed.** Final acceptance gated on a Phase 3 prototype probe (see §6) that
materializes a sample `applyMoveQm` for the bishop and queen on
`H_bishop_4` / `H_queen_4` and verifies the chosen convention produces
visually-distinguishable trajectories under the M14.3 visualization
acceptance criteria (consumer side).

---

## 2. Context

`applyMoveQm(origin, dest)` is the §17.1 bridge surface method (chess-spectral
v1.5.0) that lifts a chess move to a unitary `U_move` on the QM module's
amplitude space `C^45056`. The §17.1 contract requires `U_move` to (a) be
unitary on the inner product currently in use, (b) act compatibly with the
Z_2 superselection structure (ADR-004), and (c) optionally be returned to the
caller as a sparse complex matrix for animation (M14.3 trajectory replay).

The underlying operation in basis space is a permutation: the indicator on
square `origin` moves to square `dest` (with the captured piece, if any,
removed). Permutation matrices are real orthogonal — therefore unitary over
`C` — so the literal "permute basis vectors" lift gives a real-valued unitary
already. The question is whether it should *stay* real, or pick up a phase
factor that distinguishes Track B's QM dynamics from a relabeling exercise.

**The Aaronson-escape-valve constraint** (Aaronson, *Read the Fine Print*,
2015; cited in 2D notebook §15.6 / §11): a basis-aligned PVM applied to a
basis-aligned state returns classical readouts tautologically. If `applyMoveQm`
produces only real moves and `getQmExpectation` uses only the real Hermitian
piece observables (`H_rook_4`, etc.), the QM module reduces to "classical
chess in different notation." Track B's design must include a path to genuine
quantum interference — the phase convention is where that path opens.

Pre-flight 2 noted explicitly: *"there's no physics-motivated default phase."*
This is the design decision left open. Four candidate conventions are on the
table.

### 2.1 Existing infrastructure that constrains the choice

- **Encoder structure** ([encoder_4d.py](../../../python/chess_spectral/encoder_4d.py)).
  11 channels, 4096 modes each. Each channel carries a B_4 irrep label (see
  ADR-003 for the channel-by-channel breakdown). The chosen phase convention
  must compose cleanly with each channel's existing transformation under a
  move (linear-in-position channels permute the basis; nonlinear channels
  require special handling).

- **B_4 unitary representation** (`b4_unitary_rep_full` in qm_4d.py). The
  module already exposes B_4 group elements as block-diagonal sparse unitaries
  on `C^45056`. Any phase convention must commute with the B_4 action — the
  encoder's symmetry is load-bearing for §15.2's "B_4 equivariance for free"
  claim.

- **Z_2 superselection** (ADR-004). `state_to_psi` already takes the
  side-to-move bit and multiplies ψ by ±1. The phase convention for
  `U_move` must preserve this: a move flips side-to-move, so `U_move` must
  carry the −1 in a way that's consistent with the chosen Z_2 sector
  (ADR-004 fixes this).

---

## 3. Decision

**Adopt Option D: per-channel phase derived from the channel's B_4 irrep
label.**

Concretely, when piece `P` of type `t` moves from coords `o = (x,y,z,w)` to
coords `d = (x',y',z',w')`, the unitary on channel `c` is

```
U_move_c = e^(i * theta_c(o, d, t)) * Pi_c
```

where `Pi_c` is the channel-`c` lift of the basis permutation (described in
ADR-003) and `theta_c(o, d, t)` is the channel-specific phase below.

### 3.1 The channel phase function

The 11 channels group into three irrep classes. Per [encoder_4d.py:115-127](../../../python/chess_spectral/encoder_4d.py#L115-L127):

| # | Channel | Irrep type | Phase formula |
|---|---|---|---|
| 0 | A1            | trivial / A_1                  | `theta_0 = 0`                          |
| 1 | STD4_X        | std-4D coord residual (x-axis) | `theta_1 = (pi/4) * (x' - x)`          |
| 2 | STD4_Y        | std-4D coord residual (y-axis) | `theta_2 = (pi/4) * (y' - y)`          |
| 3 | STD4_Z        | std-4D coord residual (z-axis) | `theta_3 = (pi/4) * (z' - z)`          |
| 4 | STD4_W        | std-4D coord residual (w-axis) | `theta_4 = (pi/4) * (w' - w)`          |
| 5 | FIB_SYM_1     | rank-3 fiber SVD direction 1   | `theta_5 = (2pi/3) * d_path`           |
| 6 | FIB_SYM_2     | rank-3 fiber SVD direction 2   | `theta_6 = (4pi/3) * d_path`           |
| 7 | FIB_SYM_3     | rank-3 fiber SVD direction 3   | `theta_7 = (2pi)   * d_path`           |
| 8 | FA_PAWN_W     | pawn antisymmetric W-axis      | `theta_8 = (pi/2)  * sgn(w' - w)`      |
| 9 | FA_PAWN_Y     | pawn antisymmetric Y-axis      | `theta_9 = (pi/2)  * sgn(y' - y)`      |
| 10| FD_DIAG       | diagonal deviation             | `theta_10 = pi * (1 if diagonal_step else 0)` |

where `d_path` is the Chebyshev path-length of the move (number of single-step
hops the piece traverses; for non-sliders this is the displacement;
for sliders it is the slide length). `sgn(w' - w)` is +1 for white-direction
push, −1 for black-direction.

### 3.2 Why this satisfies the constraints

- **Unitarity:** Each `e^(i * theta_c)` is a global phase on a 4096-block; it
  commutes with `Pi_c` by construction. `U_move = ⊕_c e^(i * theta_c) * Pi_c`
  is therefore unitary on `C^45056` (each block is unitary; the direct sum is
  unitary).
- **Aaronson escape:** Different channels accumulate different phases under
  the same move. A bishop e1 → c3 picks up `theta_1 = pi/2`, `theta_3 = pi/2`
  in STD4 channels but `theta_2 = theta_4 = 0` (no y or w displacement). On
  the FIB channels the phase is `(2pi/3) * 2 = 4pi/3` for `d_path = 2`. A
  superposition input ψ spanning multiple channels accumulates *different*
  phase factors per channel, so `|<phi|U_move ψ>|^2` is no longer just the
  classical permutation overlap — interference arises.
- **B_4 commutativity:** Each B_4 element acts within a channel block (per
  the existing `b4_unitary_rep_full = I_11 ⊗ U_4096(g)` construction). The
  per-channel phase `e^(i * theta_c)` is a scalar on the channel block, so
  it commutes with B_4 on that block. Therefore `U_move` commutes with B_4
  *as long as theta_c does* — and theta_c depends only on the move (its
  channel-irrep type, displacement vector, and path length), not on
  position-of-pieces details that B_4 would scramble. So B_4-equivariance
  is preserved.
- **Z_2 superselection (ADR-004):** A move flips side-to-move; the −1 from
  `state_to_psi` propagates through `U_move` as a global factor and lands
  in the opposite Z_2 sector cleanly. The channel-phase choice is independent
  of the Z_2 grading.

### 3.3 Why these specific phase values

- **A_1 channel (`theta_0 = 0`):** The trivial irrep transforms identically
  under all of B_4. Any nonzero phase would single out a direction in B_4 —
  inconsistent with the irrep label. Zero is the only natural choice.
- **STD4 channels (`theta_a = (pi/4) * delta_a`):** Linear-in-displacement
  phase along the irrep's dedicated axis. The factor `pi/4` is chosen so a
  single-step move accumulates `pi/4` (smallest nonzero phase that survives
  to displacement = 8 without wrapping).
- **FIB_SYM channels (cube roots of unity scaled by `d_path`):** The three
  fiber-SVD directions span a 3D rank space; phases `2pi/3`, `4pi/3`, `2pi`
  encode the three irrep components as 3rd roots of unity. Path-length scaling
  makes longer slides accumulate more phase, capturing "how far the piece
  walked" in the wave function.
- **FA_PAWN channels (`pi/2 * sgn`):** Pawn directionality is the
  *defining* feature of the antisymmetric pawn channel. A `pi/2` phase per
  push captures the directed-push asymmetry as a quarter-turn — half the
  phase of a Berry "out and back" loop, since a pawn cannot reverse.
- **FD_DIAG channel (`pi if diagonal step`):** The diagonal-deviation channel
  measures how far the position is from a pure diagonal lattice. A diagonal
  step (bishop, queen-diag) lands on a `pi` phase (sign flip);
  axis-aligned steps stay on `0`. Captures the channel's geometric character.

### 3.4 What `U_move` returns to the caller

Per the §17.1 contract, `applyMoveQm` may optionally return `U_move` as
`ComplexMatrix`. With the per-channel-phase convention, `U_move` is a sparse
block-diagonal matrix with 11 sparse blocks of shape (4096, 4096), each block
being `e^(i * theta_c) * Pi_c`. Total nnz scales as 4096 × 11 = 45 056 (each
permutation has one nonzero per row). The serialization fits comfortably in
the existing `ComplexArray` real+imag-interleaved Float32 format.

---

## 4. Consequences

### 4.1 What this enables

- **M14.3 visualization differentiability.** The consumer's M14.3 milestone
  requires "visually-distinguishable trajectories" — the phase convention
  produces channel-specific phase rotations during a slide, which colorize
  the M14.2 phase-as-color render. Tested at the prototype stage.
- **Aaronson escape pathway opens.** Channel-distinct phases break the
  classical-relabeling reduction. Whether the resulting interference is
  *useful* (per §15.6's escape valve) is a Phase 6 / 7 empirical question,
  but the structural pathway exists.
- **Chess physics intuition lands.** The path-length-dependent FIB phases
  encode "the piece walked through positions" as accumulated geometric phase,
  matching the user's instrument-and-string framing (notebook §42.1).
- **B_4 equivariance preserved.** Phase factors are channel-block scalars;
  they commute with the existing B_4 action.

### 4.2 What this forecloses

- **No path-history dependence on the phase.** The phase depends only on
  origin, destination, piece type, and channel — not on how the piece's
  ψ-amplitude got to `origin`. This is intentional (keeps `U_move` Markov
  on the QM state) but rules out "true" path-integral phase that integrates
  over all paths the piece *might* have taken. If Phase 6 / 7 finds that
  M14.3 visualizations need path-integral richness, the convention can be
  upgraded in v1.7+ — see §6 below.
- **No piece-type-specific Berry phase beyond the per-channel formulas.**
  Bishop-vs-rook are distinguished by their channel-decomposition profile
  (bishop populates FIB_SYM, FD_DIAG; rook populates STD4 + A1) but not by
  per-piece-type phase coefficients. Option C (sign-parity from piece type)
  is rejected — see §5 below.

### 4.3 LOC implications

`applyMoveQm` total: ~250 LOC including doc strings.
- `_compute_channel_phase(channel_idx, origin, dest, piece_type) -> float`:
  ~80 LOC (one branch per channel, reading from the table in §3.1)
- `_build_channel_permutation(channel_idx, origin, dest)` (decision deferred to
  ADR-003): ~120 LOC — the load-bearing piece for linear channels; nonlinear
  channels add their own LOC budget per ADR-003.
- `applyMoveQm` driver assembling the block-diagonal sparse matrix: ~50 LOC.

### 4.4 Test surface

- **Unitarity:** For a sample of 100 random legal moves on random non-trivial
  positions, assert `is_unitary(U_move, tol=1e-10)` from existing qm_4d.py
  validation helpers. Cost: ~30 LOC test.
- **B_4 commutativity:** For a sample of 50 moves and 20 B_4 elements,
  assert `‖U_move @ B - B @ U_move‖_F < 1e-10` where `B = b4_unitary_rep_full(g)`.
  Cost: ~40 LOC.
- **Z_2 sector flip:** For a sample of moves, assert that
  `state_to_psi(state', NOT side) = U_move @ state_to_psi(state, side)`
  (where `state'` is the post-move state and `side` flips). Cost: ~30 LOC.
- **Per-channel phase formulas:** Direct numeric test of the table in §3.1
  against `_compute_channel_phase`. Cost: ~50 LOC.
- **Aaronson escape demonstration:** A single hand-rolled test showing
  superposition input + nontrivial move produces an output where the channel
  marginals' phases differ. Cost: ~30 LOC.

Total test LOC: ~180.

---

## 5. Alternatives Considered

### 5.1 Option A: Real (+1) only — moves are real orthogonal matrices

**Rejected.** This is the simplest convention: `U_move = ⊕_c Pi_c`, each
block real. Implementing this is ~100 LOC less than Option D (no
`_compute_channel_phase` function, no per-channel branches). However:

- **Aaronson trap.** Pre-flight 2 and 2D notebook §15.6 explicitly call this
  out: real-orthogonal `U_move` + basis-aligned PVM observables = classical
  chess in QM notation. The whole point of Track B is to escape this trap.
- **No interference under M14.x.** The M14.3 trajectory replay would render
  identically to a classical board-state animation, defeating the
  visualization milestone's purpose.
- **Wastes the Pre-flight 3 spectral identity.** The encoder *is* the
  simultaneous eigenbasis of `(Δ, B_4 commutant)`. Real-only moves don't
  exercise this structure beyond the kinematic view in Track A.

### 5.2 Option B: Berry phase from `phi4`

**Rejected for v1.5; revisit for v1.7+.** The proposal: accumulate the
geometric phase along the actual lattice path the piece traverses (e.g.,
sum `phi4(square_k)` for each square `k` on the move's path).

- **Path-dependence ambiguity for non-sliders.** Knights teleport to the
  destination — the "path" is ill-defined. Berry phase as a path integral
  needs a continuous path, which the lattice doesn't have. Defining the
  phase only for sliders introduces piece-type-specific code branches that
  ADR-003 already has to handle for nonlinear channels; we'd be doubling the
  conditional surface.
- **Computation cost.** `phi4` has modulus `MODULUS_4D = 145451`; summing
  over the path produces phases mod `2pi * 145451 / 145451`, which doesn't
  give the simple closed-form `e^(i * theta)` factors that compose cleanly
  in the channel-block structure.
- **Less expressive than per-channel.** A single Berry phase from a path
  doesn't distinguish A_1 from STD4 from FIB_SYM channel evolution. The
  per-channel-irrep convention (Option D) does, which is what the
  visualization-differentiability test requires.

If Phase 6 / 7 finds that Option D's interference structure is too rigid
to capture chess insight, Option B becomes a v1.7+ extension where
sliders accumulate Berry phase *in addition to* the per-channel-irrep base
phase from Option D.

### 5.3 Option C: Sign-parity from piece type

**Rejected.** The proposal: assign each piece type a fixed phase (e.g.,
`e^(i*pi/3)` for knight, `e^(i*pi/2)` for bishop, etc.) accumulated per move.

- **Arbitrary.** No representation-theoretic motivation. The choice of
  which rational multiples of `pi` to assign is unprincipled and would
  introduce a "magic numbers" violation by chess-spectral SSOT discipline.
- **No B_4 equivariance.** Piece-type is a global label, not a B_4 irrep
  component. A `pi/3` phase on knight moves doesn't commute with the B_4
  action on the channel decomposition — the construction would break the
  B_4 commutativity test in §4.4.
- **Less informative than per-channel.** A bishop e1 → c3 and a bishop
  e1 → b4 would carry the same phase under Option C, even though they
  traverse different displacement vectors. The M14.3 visualization
  acceptance criterion explicitly requires "different moves → distinguishable
  trajectories," which Option C only weakly satisfies (different *piece
  types*, yes; different *moves of the same piece type*, no).

### 5.4 Option D variants we considered but didn't pick

- **Real-coefficient per-channel formulas (`theta_c real, no `i`).** Same
  effect as Option A; no interference. Rejected.
- **Per-channel phase from Krawtchouk polynomial values.** The encoder
  basis decomposes via Krawtchouk; using Krawtchouk values at displacement
  argument is mathematically natural. Rejected because the formulas
  produce phases of the form `K_n(d, q) / N_norm`, which is opaque to the
  consumer (no clean intuition about phase-as-rotation). The `pi/4`,
  `2pi/3`, `pi/2`, `pi` rationals in §3.1 are more readable; the
  channel-distinctness property is preserved either way.

---

## 6. Open Questions / Future Work

1. **Phase 3 prototype probe.** Before implementation, build a 50-LOC
   prototype that applies one `U_move` (e.g., bishop e1 → c3) to a
   superposition state and renders the channel-marginal phases. The
   prototype validates that the M14.3 visualization differentiates
   "same-piece different-destination" pairs.

2. **Berry phase v1.7+ extension.** If §16 self-play tournament finds that
   QM-evaluator with Option D underperforms — i.e., chess-relevance is
   *less* than spectral evaluator at the representative depths the
   tournament harness exercises — revisit whether path-integral phase
   (Option B) on sliders adds discriminative signal. This becomes a
   Phase 7 question, not a Phase 4 question.

3. **Phase calibration via tournament.** Phase 7's learned-weight
   experiments (§16.8) could *fit* the rational multipliers in §3.1
   against tournament outcomes. This is "tune the phase convention to
   maximize Elo" — a natural follow-up if Option D has unconstrained
   parameters.

---

## 7. References

- **Notebook §15.6** ([chess_spectral_research_notebook.md, sec 15.6](../../../../chess_spectral_research_notebook.md#156-honest-scope-math-vs-toolkit)) — Aaronson escape valve discussion.
- **Notebook §16** ([chess_spectral_research_notebook.md, sec 16](../../../../chess_spectral_research_notebook.md#16-position-evaluation-search-and-self-play-validation-phase-6-plan)) — Phase 6 evaluator framework where this convention is empirically tested.
- **Notebook §17.1** ([chess_spectral_research_notebook.md, sec 17.1](../../../../chess_spectral_research_notebook.md#171-chess-spectral-15--qm-extension-bridge-surface)) — Bridge contract for `applyMoveQm`.
- **Pre-flight 2** ([chess_spectral_4d_notebook.md, sec qm_4d Pre-flight Findings](../../../../chess_spectral_4d_notebook.md#pre-flight-2--pseudo-hermitian-audit-of-phase_operators_4d)) — "no physics-motivated default phase" finding.
- **Encoder structure** ([encoder_4d.py](../../../python/chess_spectral/encoder_4d.py)) — channel-by-channel construction.
- **B_4 representation** ([qm_4d.py:215-251](../../../python/chess_spectral/qm_4d.py#L215-L251)) — `b4_unitary_rep_full` construction the convention must commute with.
- **ADR-003** — per-channel move derivation (`Pi_c` is built there).
- **ADR-004** — Z_2 superselection (the convention must respect the Z_2 grading).
- **Aaronson, S.** *"Read the Fine Print" (Nature Physics 11, 2015).* Cited
  in 2D notebook §15.6 / §11.

---

## 8. Phase 4 Implementation Pointer

**This is the design we will implement in Phase 4 B[1] (qm_4d phase convention
+ scalar phase tables).** The two helpers `_compute_channel_phase` and the
`channel_phase_table` constant (encoding §3.1's rational multipliers) ship
together; `_build_channel_permutation` (ADR-003) and the `applyMoveQm` driver
ship in subsequent Phase 4 steps. Acceptance: the §4.4 test surface passes,
and a hand-checked bishop-move example produces the §3.1 phases at machine
precision.

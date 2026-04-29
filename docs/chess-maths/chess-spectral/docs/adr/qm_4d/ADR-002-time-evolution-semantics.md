# ADR-002: Time-Evolution Semantics for QM Chess Dynamics

**Date:** 2026-04-29
**Branch:** `chess-spectral/qm-4d-kinematic`
**Track:** B (full move-as-unitary dynamics)
**Ships in:** Phase 4 / `qm_4d.evolve_until` & `applyMoveQm` / chess-spectral v1.5.0

---

## 1. Status

**Proposed (Option A: Zeno-style instantaneous projection).** Stinespring
dilation (Option B) is **deferred to chess-spectral v1.7+** as a natural
follow-up if Phase 6 tournament results suggest captures need first-class
unitary treatment.

---

## 2. Context

Chess is a discrete game on a finite board with non-unitary moves. Two
sources of non-unitarity exist:

1. **Captures remove pieces.** The position state's "piece count" decreases
   by one. Information is irreversibly lost — the captured piece's identity
   and origin square cannot be reconstructed from the post-move position
   alone. (The move history is preserved separately, but the state at any
   given ply is a quotient.)
2. **Pawn promotion / en-passant / castling** are state-changing moves that
   alter the *type* of pieces on the board, not just their positions.

A QM-faithful theory needs unitarity (norm preservation, reversibility) at
the operator level. Track A's kinematic-only path side-stepped this by
declining to define `applyMoveQm` (only `state_to_psi` was exposed). Track B
must define what "evolve the QM state through a move" means.

There is a related but separate question — **what does "time `t`" mean
between moves?** Chess turns are discrete. There is no physical clock that
ticks during a single ply. But the M14.x visualization milestones explicitly
ask for "time-evolution" animations: amplitude flowing across the board
under `H = -Δ` between moves, slowing and re-converging when a move lands.
Without a definition of inter-move time, the M14.x animations have nothing
to render.

### 2.1 The two clean options on the table

**Option A — Zeno-style instantaneous projection.** Declare `H_0 = -Δ` as
the free Hamiltonian (`Δ` is the 4D path-graph Laplacian, already established
as the relevant operator per Pre-flight 3). Between moves, ψ evolves
continuously via `ψ(t) = exp(-i H_0 (t - t_n)) * ψ(t_n)` for `t in [t_n, t_{n+1})`.
At each move boundary (`t = t_{n+1}`), apply `U_move_{n+1}` instantaneously,
producing `ψ(t_{n+1}) = U_move_{n+1} * ψ(t_{n+1}^-)`. ψ is right-continuous;
the move is a discontinuous projective operation on a continuous unitary
flow.

**Option B — Stinespring dilation.** Embed the (in general non-unitary)
chess move into a unitary on a larger space `H ⊕ H_grave`, where `H_grave`
is a "graveyard register" tracking removed pieces. Captures become unitary:
the captured piece's amplitude moves into a graveyard slot rather than
disappearing. The total state is reversible — given the post-capture state
+ graveyard, the pre-capture state can be reconstructed.

Each option has a well-defined inter-move time semantics (continuous unitary
flow under `H_0`) and a well-defined move semantics (projective on H, or
unitary on H ⊕ H_grave). The split is in *what handles capture loss*.

### 2.2 The chess4D-OC consumer's M14.x requirements

The chess4D-OC consumer (the parallel session running the v1.5 visualization
plan) requires:
- **M14.1:** raw amplitude render of `ψ` per cell (`getQmDensity()`)
- **M14.2:** phase-as-color render of `ψ`
- **M14.3:** trajectory replay between moves (animated time-evolution)
- **M14.4:** entanglement visualization (reduced density matrices)
- **M14.5:** Born-rule measurement (`measureAt`)
- **M14.6:** probability current field (`getProbabilityCurrent`)

M14.3 specifically requires *animated* evolution. Both options support this;
the question is what M14.3 *displays* during a capture frame.

---

## 3. Decision

**Adopt Option A: Zeno-style instantaneous projection** for chess-spectral
v1.5.0 (Track B / Phase 4).

### 3.1 Concrete semantics

The QM module's time evolution is described by a triple `(ψ, H_0, U_move_seq)`:

- **ψ ∈ C^45056** — the current QM amplitude (output of `state_to_psi` per
  ADR-004, normalized).
- **H_0 = -Δ_full** — the free Hamiltonian on `C^45056`. Built as
  `H_0 = I_11 ⊗ Δ` where `Δ` is the 4D path-graph Laplacian on `C^4096`
  (already available as `tables_4d.laplacian_4d(...)` lifted to
  `C^4096`). Hermitian, real, sparse.
- **U_move_seq** — the sequence of move unitaries applied at each move
  boundary, per ADR-001 / ADR-003.

Continuous-time evolution between moves:

```
ψ(t) = exp(-i H_0 (t - t_n)) * ψ(t_n)    for t in [t_n, t_{n+1})
```

Move operation (instantaneous, at `t = t_{n+1}`):

```
ψ(t_{n+1}) = N_{n+1} * U_move_{n+1} * ψ(t_{n+1}^-)
```

where `N_{n+1}` is a **renormalization scalar** that restores `‖ψ‖ = 1`
after capture-induced norm loss. Without renormalization, the post-capture
state would have `‖ψ‖ < 1`, breaking the Born-rule probability axioms used
by `measure_channel_distribution` and `getQmExpectation`.

### 3.2 Public API surface

`qm_4d` exposes the following Track B additions:

```python
# Free Hamiltonian (lazy property; cached after first build)
H_free_4d    -> sparse Hermitian on C^45056

# Continuous-time evolution
evolve_until(psi, t_delta) -> psi_evolved
    """Apply exp(-i * H_free_4d * t_delta) to psi.

    Implemented via expm_multiply (scipy.sparse.linalg) on the sparse
    H_free_4d. Works because H_free_4d is sparse and t_delta is small
    (typical M14.3 frames are 16ms).
    """

# Move application (the §17.1 applyMoveQm bridge method)
apply_move_qm(psi, origin, dest, piece_type) -> (psi_post, U_move)
    """Apply U_move_{n+1} to psi, then renormalize. See ADR-001 for
    the phase convention and ADR-003 for per-channel construction.
    """

# Helper: total norm-loss tracking (for diagnostics)
move_norm_loss(psi_pre, psi_post_unnormalized) -> float
    """Returns 1 - ||psi_post_unnormalized||^2; the fraction of
    probability mass lost in the capture. Returns 0.0 for non-capture
    moves.
    """
```

### 3.3 What the M14.3 animation renders

For a single move boundary, the consumer does:

```python
# Step 1: continuous evolution between moves at typical 60 FPS
for t in linspace(t_n, t_{n+1}, n_frames):
    psi_t = evolve_until(psi_n, t - t_n)
    render_frame(psi_t)

# Step 2: at the move boundary, apply U_move and renormalize
psi_n+1, U = apply_move_qm(psi_t_just_before_move, origin, dest, piece_type)
render_frame(psi_n+1)  # discontinuous "jump" in the animation

# Step 3: continuous evolution from psi_n+1 onwards
... repeat
```

The visualization shows ψ "flowing" smoothly between moves and then
"snapping" at each move boundary. The captured piece's amplitude — which
pre-move was localized near the destination square — is renormalized away.
This is visually distinguishable from non-capture moves (where the snap
is just a permutation), satisfying M14.3's differentiability criterion.

### 3.4 The renormalization scalar N

For a non-capture move, `‖U_move @ ψ‖ = ‖ψ‖ = 1` (U_move is unitary on the
full space), so `N = 1`. For a capture move:

- The captured piece's encoded contribution exists across multiple channels
  (e.g., a captured rook contributes to A_1, STD4_*, FIB_SYM, FD_DIAG).
- Per ADR-003, the unitary `U_move_c` on each channel is a *partial* permutation
  that drops the captured piece's contribution from the channel's basis. The
  resulting `U_move` is then a partial-isometry on `C^45056` rather than a
  strict unitary.
- `‖U_move @ ψ‖ < 1` reflects the lost amplitude. `N = 1 / ‖U_move @ ψ‖`
  restores the norm; `ψ_post = N * U_move * ψ_pre`.

This is the **projective** part of the Zeno semantics. We project ψ into the
post-move state-space and renormalize — exactly what a Born-rule measurement
of "is the captured piece present?" does in textbook QM. The non-unitary
character of capture is encapsulated in this single rescaling step.

### 3.5 Inter-move clock

We do **not** introduce a "ply clock" (chess time control) at the QM module
level. The `t_delta` in `evolve_until` is dimensionless (units of `1 / ‖H_0‖`,
which is `O(1/8)` since `Δ` has spectrum `[0, 8]` per Pre-flight 3) and is set
by the consumer's animation timeline. The chess game's actual ply rate is
encoded by *which* `U_move` is applied at each move boundary; the consumer
can replay at any speed.

The `evolve_until` API explicitly supports `t_delta = 0` (no-op) and any
positive `t_delta`. The M14.x renderer is expected to call `evolve_until`
once per animation frame with the elapsed wall-clock time (or any
animation-curve mapping the user prefers).

---

## 4. Consequences

### 4.1 What this enables

- **All M14.x milestones unblocked.** The Zeno semantics gives a clean,
  cheap, and visually-meaningful definition of inter-move time. No
  doubled state space. M14.3 (animated trajectory replay) renders directly.
- **Captures collapse to a single rescale.** The non-unitary part of chess
  is contained in the `N` scalar, which is trivial to compute and explain.
  A reviewer asking "how does QM chess handle captures?" gets a one-line
  answer: "we project and renormalize — the textbook Born-rule operation."
- **Cheap implementation.** `evolve_until` reuses scipy's `expm_multiply`
  on the sparse `H_free_4d`. Memory cost: one extra sparse matrix on
  `C^45056` (~360k nnz; under 10MB). CPU cost: per-frame evaluation in
  the millisecond range for `t_delta < 1.0`.
- **Aligns with Pre-flight 3.** The encoder *is* the simultaneous eigenbasis
  of `(Δ, B_4 commutant)`. `H_0 = -Δ` is therefore diagonal in the encoder
  basis at machine precision. A second-stage optimization could compute
  `evolve_until` via direct diagonal-phase multiplication in the eigenbasis
  (no `expm_multiply` needed at all) — see §6 below.

### 4.2 What this forecloses

- **Information-theoretic conservation.** Stinespring would conserve total
  information (graveyard register tracks captured pieces). Zeno does not.
  If a QM-extension consumer wants to ask "what would the position be
  if we un-captured the rook?" — Zeno cannot answer; Stinespring can.
  This is *intentionally* deferred until empirical evidence (Phase 6+)
  shows the question matters.
- **Capture as unitary.** Some applications (entanglement-based search,
  reversible computing analogies) might want capture to be a unitary
  operation. Zeno chooses simplicity over this; v1.7+ Stinespring opens
  the door if needed.
- **Time as a clock parameter independent of evolution.** Zeno uses a single
  `t_delta` parameter for both "physical time" and "animation time."
  Some applications might want them to differ — e.g., the QM evaluator
  for chess search wants "no time evolution between candidate moves"
  (`t_delta = 0` always), while the M14.x renderer wants ~16ms-equivalent
  evolution per frame. The current `t_delta` parameter handles both,
  but a future split into "game clock" + "render clock" might be useful.

### 4.3 LOC implications

- **`H_free_4d` lazy property:** ~30 LOC (one cached call assembling
  `I_11 ⊗ Δ` from `tables_4d.laplacian_4d`).
- **`evolve_until`:** ~40 LOC (calls `scipy.sparse.linalg.expm_multiply`
  with documented stability bounds and shape checks).
- **Renormalization in `apply_move_qm`:** ~20 LOC (compute norm, divide,
  log a debug message if renormalization scalar exceeds expected range).
- **`move_norm_loss` diagnostic:** ~15 LOC.

Total Zeno-specific LOC: ~110.

### 4.4 Test surface

- **Unitarity of evolution:** For 50 random `t_delta` in `[0, 2.0]`,
  assert `‖evolve_until(ψ, t_delta)‖ = 1.0` within 1e-12 of input
  norm. Cost: ~30 LOC.
- **Norm preservation under non-capture moves:** For 50 random
  non-capture moves, assert `‖U_move @ ψ‖ = ‖ψ‖`. Cost: ~30 LOC.
- **Norm loss under capture:** For 30 hand-picked capture positions,
  assert `‖U_move @ ψ_pre‖ < ‖ψ_pre‖` and `‖N * U_move @ ψ_pre‖ = 1`.
  Document the actual norm losses in a regression file (one per fixture).
  Cost: ~50 LOC.
- **`evolve_until(ψ, 0) == ψ`:** Trivial identity. ~10 LOC.
- **Composability:** `evolve_until(evolve_until(ψ, t1), t2) ≈ evolve_until(ψ, t1+t2)`
  within `expm_multiply`'s precision. ~20 LOC.

Total test LOC: ~140.

### 4.5 Performance

- **`evolve_until(ψ, 0.1)`:** Single `expm_multiply` call on a sparse
  `45056 x 45056` matrix with ~360k nnz. Empirically ~50ms on the dev box;
  fits within a 60 FPS budget if the consumer caches frames.
- **`evolve_until(ψ, t)` for t ≥ 1.0:** Larger Krylov basis needed; cost
  grows linearly with `t * ‖H_0‖`. For typical M14.x frames (`t < 0.2`)
  cost stays under 100ms.
- **Eigenbasis-diagonal optimization (v1.6+):** If `evolve_until` becomes
  a hot path, replace `expm_multiply` with `enc_basis @ exp(-i * eigvals * t) * enc_basis^H @ ψ`,
  reducing per-frame cost to one matvec + one elementwise multiplication.
  ~10x speedup; deferred until profiling justifies the LOC.

---

## 5. Alternatives Considered

### 5.1 Option B: Stinespring dilation (rejected for v1.5; v1.7+ candidate)

**Rejected for v1.5.0.** The proposal: extend the QM space to
`H_total = C^45056 ⊕ C^45056_grave` (or a smaller graveyard space sized
to "max possible captured pieces × encoded dim"). Each capture is a
unitary that moves the captured piece's amplitude into the graveyard.
The total state evolves unitarily.

**Why deferred:**
- **Doubled state space.** Memory cost roughly doubles (to ~720k nnz for
  `H_free`). The consumer's M14.x rendering must handle the graveyard
  (either render it, or choose what to ignore). Visualization design is
  significantly more complex.
- **No empirical motivation yet.** Phase 6's tournament harness measures
  "does QM-evaluator outperform spectral evaluator?" — Stinespring's
  graveyard adds capture-history information that *could* improve the
  evaluator (the evaluator could ask "is the king still threatened by
  the captured queen's last position?"), but no published or in-house
  result suggests this. Building Stinespring before evidence motivates
  it is gold-plating.
- **LOC budget.** Stinespring would add ~600 LOC: graveyard register
  management, unitary capture operations, modified `state_to_psi` to
  handle graveyard, modified `getQmDensity` to support graveyard projection,
  graveyard-aware versions of all 7 §17.1 bridge methods. Track B already
  has a ~2000 LOC budget; doubling that for v1.5.0 risks shipping nothing.
- **Phase 7+ gating.** If Phase 6 results show that capture-history
  matters for evaluator strength (analogous to the §16.8 "bracket
  pseudo-channels" finding from Othello), Stinespring becomes a v1.7+
  feature. The §16.8 finding that pending-capture pseudo-channels lift
  partial ρ by ~+40% is suggestive; we could build Stinespring as the
  unitary-version of pending-capture tracking.

If Stinespring becomes a v1.7+ feature:
- The graveyard register would track per-channel components of captured pieces.
- Captures would be `U_capture = swap_with_graveyard_block` — a unitary on
  `C^45056 ⊕ C^45056_grave` that moves the captured piece's (or, more
  precisely, the encoder-basis components attributed to it) amplitudes into
  graveyard slots.
- Time evolution would extend `H_free` to act on the graveyard via
  `H_total = H_free ⊗ I_grave + I_full ⊗ H_grave` where `H_grave` could be
  zero (frozen graveyard) or non-trivial (graveyard pieces "remember" their
  last position via dispersion).

This is the natural path, but every part of it depends on Phase 6 / 7
empirical evidence.

### 5.2 Option C: Discrete-only (no inter-move time)

**Rejected.** The proposal: skip continuous evolution entirely.
`ψ(n+1) = U_move @ ψ(n)`; M14.3 renders only the move-boundary snap.

- **Breaks M14.3.** The visualization plan explicitly requires
  "smooth trajectory" — without continuous evolution, there's no trajectory
  to render. Position snapshots only.
- **Wastes Pre-flight 3.** `H_0 = -Δ` is the natural, free Hamiltonian
  pre-validated by the spectral identity result. Not using it leaves the
  framework's most physics-airtight result unexploited.
- **No QM-evaluator coherence.** The Phase 6 QM evaluator wants
  `⟨ψ|H_piece|ψ⟩` for the position state. With no inter-move evolution,
  ψ is *exactly* the encoded position (modulo the move U_n), and the
  expectation values reduce to graph-spectral counts — no distinguishing
  signal beyond the spectral evaluator.

### 5.3 Option D: Continuous evolution with non-Hermitian effective Hamiltonian

**Rejected.** The proposal: instead of unitary `H_0 + N * U_move`, use a
single non-Hermitian `H_eff` whose imaginary part encodes the capture
loss. `ψ(t) = exp(-i H_eff t) ψ(0)` evolves continuously through captures.

- **Captures aren't continuous.** A bishop captures on a single ply boundary;
  there's no smooth dissipation. Smearing the capture out into a non-Hermitian
  flow distorts the chess semantics in a way visualizations cannot recover.
- **Recreates Stinespring without its benefits.** A non-Hermitian effective
  H is mathematically equivalent to a unitary embedding (Stinespring's
  theorem); we'd be doing Stinespring anyway, just with worse performance
  and less interpretability.
- **Pseudo-Hermitian conflation with ADR-005.** ADR-005 already introduces
  pseudo-Hermitian / PT-symmetric machinery for *pawn dynamics*. Using a
  non-Hermitian effective H for captures would conflate two distinct
  pseudo-Hermitian phenomena (directed pawn pushing vs. capture-induced
  loss). Better to keep them separate.

---

## 6. Open Questions / Future Work

1. **Eigenbasis-diagonal optimization for `evolve_until`.** Per Pre-flight 3,
   `H_0 = -Δ` is diagonal in the encoder basis. A v1.6+ optimization could
   replace `expm_multiply` with direct phase multiplication. Deferred until
   profiling shows `evolve_until` is a hot path.

2. **Time-dependent `H` for piece-type-aware evolution.** A natural
   extension: `H(t) = -Δ + Σ_p H_piece * occupied(p, t)`. The Hamiltonian
   would change as the position evolves — a Wilson-line-style construction
   where pieces are "perturbations" on the free flow. This is mentioned in
   notebook §4 (Weyl perturbation; pieces as Hamiltonian modifications)
   and is a Phase 7+ candidate. Out of scope for v1.5.0.

3. **Game clock vs. animation clock split.** The current single-`t_delta`
   API may need to split into "game time" and "render time" if the M14.x
   visualization wants to slow down evolution near critical moves
   (e.g., checks). Deferred — the consumer can always rescale `t_delta`
   client-side, so no API split is needed unless server-side time
   semantics become required.

4. **Stinespring promotion criteria.** Define a clean rule for when to
   promote Stinespring from "v1.7+ candidate" to "v1.7 must-have." Working
   proposal: if Phase 6 tournament's QM-evaluator at L8/L16 underperforms
   spectral evaluator, AND Phase 7's preliminary capture-history pseudo-channel
   experiment lifts QM-evaluator above spectral, then Stinespring (the
   unitary version of pending-capture tracking) becomes v1.7's priority
   feature. Otherwise, Zeno remains permanent.

---

## 7. References

- **Notebook §4** ([chess_spectral_research_notebook.md, sec 4](../../../../chess_spectral_research_notebook.md#4-the-lattice-fermion-model)) — Lattice fermion model; Weyl perturbation framing for pieces as Hamiltonian modifications.
- **Notebook §15.2(2)** ([chess_spectral_research_notebook.md, sec 15.2](../../../../chess_spectral_research_notebook.md#152-the-enabling-machinery)) — Spectral identity as design input for `H_0 = -Δ`.
- **Notebook §17.1** ([chess_spectral_research_notebook.md, sec 17.1](../../../../chess_spectral_research_notebook.md#171-chess-spectral-15--qm-extension-bridge-surface)) — Bridge contract for `applyMoveQm` and the M14.x visualization plan.
- **Pre-flight 3** ([chess_spectral_4d_notebook.md, sec qm_4d Pre-flight Findings](../../../../chess_spectral_4d_notebook.md#pre-flight-3--spectral-identity-verification)) — Encoder-as-eigenbasis result; the identity that makes `H_0 = -Δ` natural.
- **Existing kinematic module** ([qm_4d.py](../../../python/chess_spectral/qm_4d.py)) — what Track A ships; Track B extends it.
- **ADR-001** — phase convention for `U_move`; complements this ADR's
  semantics for what happens at move boundaries.
- **ADR-003** — per-channel move construction; defines the partial-isometry
  structure of `U_move` whose norm-loss this ADR's renormalization handles.
- **ADR-005** — pawn pseudo-Hermitian metric; orthogonal to this ADR
  (pawn dynamics within a turn vs. capture loss between turns).
- **Stinespring, W. F.** *"Positive functions on C*-algebras," Proc. Am. Math. Soc.,
  vol. 6, no. 2, pp. 211-216, 1955* — for the v1.7+ extension reference.

---

## 8. Phase 4 Implementation Pointer

**This is the design we will implement in Phase 4 B[2] (qm_4d evolution
semantics).** The `H_free_4d` cached property and `evolve_until` ship
together; `apply_move_qm`'s renormalization is implemented alongside
ADR-003's partial-isometry construction. Acceptance: the §4.4 test surface
passes; the M14.3 prototype renders a smooth-then-snap animation for a
single bishop capture at acceptable frame rates (60 FPS on the dev box).

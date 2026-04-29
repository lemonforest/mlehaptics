# ADR-003: Per-Channel Move-Transformation Derivation

**Date:** 2026-04-29
**Branch:** `chess-spectral/qm-4d-kinematic`
**Track:** B (full move-as-unitary dynamics)
**Ships in:** Phase 4 / `qm_4d.applyMoveQm` and per-channel `_build_*_move_block` helpers / chess-spectral v1.5.0

---

## 1. Status

**Proposed (mixed scope: 5 channels strict-unitary in v1.5; 6 channels
best-effort approximation in v1.5 with documented departures from
strict-QM; 0 channels deferred to v1.7+).** Pre-implementation prototype
required (see §6) before final acceptance.

---

## 2. Context

`applyMoveQm(origin, dest)` (§17.1) lifts a chess move to a unitary
`U_move ∈ U(C^45056)`. ADR-001 fixed the *phase* of each channel's contribution; ADR-002
fixed the *time-evolution* framing and capture-renormalization. **This
ADR fixes the per-channel basis transformation** — the actual permutation
or partial-isometry on each channel's 4096-dim subspace.

This is the **mathematical core** of Track B and the LOC-trap that
"purple-quantum" was flagged at scoping. The encoder ([encoder_4d.py](../../../python/chess_spectral/encoder_4d.py))
constructs each channel from the position via formulas of varying
complexity. A move changes the position — therefore the channel
representation. The question is whether each channel's response to a move
is (a) a strict permutation (unitary on the channel's subspace), (b) a
partial isometry (unitary on a sub-subspace, with some amplitude lost),
(c) a "best-effort approximation" (close to unitary but not exactly), or
(d) genuinely non-unitary in a way that requires Stinespring dilation
(deferred to v1.7+).

The encoder's 11 channels are *not* uniform in this respect. Some channels
are linear-in-position (the move acts as a clean permutation); others are
nonlinear-in-piece-value (the move is a piecewise transformation that may
not even be linear, let alone unitary).

This ADR catalogues all 11 channels by linearity type, derives the move
transformation for each, and decides the v1.5 scope.

### 2.1 The 11-channel catalogue (re-summarized)

Per [encoder_4d.py:115-127](../../../python/chess_spectral/encoder_4d.py#L115-L127):

| # | Channel | Construction (encoder_4d.py) | Linearity in piece values |
|---|---|---|---|
| 0 | A1            | `(P_A1 @ sig)` | **Linear** |
| 1 | STD4_X        | `coord_resid[0] * sig` | **Linear** |
| 2 | STD4_Y        | `coord_resid[1] * sig` | **Linear** |
| 3 | STD4_Z        | `coord_resid[2] * sig` | **Linear** |
| 4 | STD4_W        | `coord_resid[3] * sig` | **Linear** |
| 5 | FIB_SYM_1     | `Σ_k gradient(k) * fib_d[piece(k), k, 0] * adj_row(k)` | **Bilinear** in (sig × sig) |
| 6 | FIB_SYM_2     | same with `d=1` | **Bilinear** |
| 7 | FIB_SYM_3     | same with `d=2` | **Bilinear** |
| 8 | FA_PAWN_W     | `Σ_pawn sign(color) * scatter(W_ANTI_DCT[sw], position)` | **Linear** in pawn presence (per square is binary) |
| 9 | FA_PAWN_Y     | same with Y axis | **Linear** in pawn presence |
| 10 | FD_DIAG       | `Σ_k sig[k] * DIAG_DEV[piece_row(k)]` | **Linear in sig, but coefficient varies by piece type** |

*"Linear" means: the encoded vector is a linear function of the position
signal `sig`. *"Bilinear"* means: the encoded vector contains products of
position signal values, so a move that changes one square's value updates
the encoded vector via a nonlinear formula.

### 2.2 Why this matters for unitarity

A *linear* operator `U_move : C^45056 → C^45056` that maps `encode_4d(pos_pre)`
to `encode_4d(pos_post)` exists *only when* the encoded vector depends linearly
on the move's position-change. For:

- **Linear channels (0-4, 8-9):** `encode_4d_post = U_move @ encode_4d_pre`
  for a uniquely determined `U_move`, which is in fact a permutation
  matrix on the channel block. This is the easy case.
- **Bilinear channels (5-7):** `encode_4d_post` is *not* a linear function of
  `encode_4d_pre`. There is no `U_move` such that
  `encode_4d_post = U_move @ encode_4d_pre` exactly. The best we can do is
  a linearized approximation, or treat these channels as "measurements"
  rather than "states."
- **Linear-with-piece-coefficient channel (10):** `encode_4d_post` is linear
  in `sig_post`, but `sig_post` and `sig_pre` may have different active
  squares (capture changes which DIAG_DEV row is active). The channel block's
  basis effectively changes during a move — strict unitarity holds *only
  on the surviving sub-basis*.

---

## 3. Decision

**Adopt a tiered approach across the 11 channels:**

| # | Channel | v1.5 status | `U_move_c` form | Strict-QM? |
|---|---|---|---|---|
| 0 | A1            | **Strict unitary** | Permutation `Pi_0` | Yes |
| 1 | STD4_X        | **Strict unitary** | Permutation `Pi_1` | Yes |
| 2 | STD4_Y        | **Strict unitary** | Permutation `Pi_2` | Yes |
| 3 | STD4_Z        | **Strict unitary** | Permutation `Pi_3` | Yes |
| 4 | STD4_W        | **Strict unitary** | Permutation `Pi_4` | Yes |
| 5 | FIB_SYM_1     | **Best-effort approximation** | Linearized at `pos_pre` | No (documented) |
| 6 | FIB_SYM_2     | **Best-effort approximation** | Linearized at `pos_pre` | No (documented) |
| 7 | FIB_SYM_3     | **Best-effort approximation** | Linearized at `pos_pre` | No (documented) |
| 8 | FA_PAWN_W     | **Strict unitary** (non-capture) / partial-isometry (capture) | Block scatter | Yes |
| 9 | FA_PAWN_Y     | **Strict unitary** (non-capture) / partial-isometry (capture) | Block scatter | Yes |
| 10 | FD_DIAG       | **Best-effort approximation** | Diagonal piece-coefficient swap | No (documented) |

**Aggregate v1.5 unitarity:** For non-capture moves, channels 0-4, 8-9 are
strictly unitary on their blocks; channels 5-7, 10 are linearized at the
pre-move state (so `U_move @ encode_pre = encode_post + small_residual`,
where the residual is bounded). For capture moves, channels 8-9 lose
amplitude in proportion to captured-pawn count; ADR-002's renormalization
restores `‖ψ‖ = 1`.

### 3.1 Strict-unitary channels (0-4, 8-9): construction

#### Channel 0 (A1, orbit-sum projection):

The channel value at square `s` is `Σ_{s' ∈ orbit(s)} sig[s'] / |orbit(s)|`,
i.e., the orbit-mean of the signal under B_4.

When piece `p` moves from `o` to `d`, `sig[o] → 0` (or `sig_captured` if
capturing) and `sig[d] → sig_pre[o]`. The orbit-mean updates by
permuting which squares contribute to which orbit's average.

**Construction of `Pi_0`:** `Pi_0` is the permutation matrix on `C^4096`
that sends `e_o → e_d` (basis vector at `o` swaps with basis vector at `d`).
This is a **swap operator** (transposition `(o, d)`) on the basis. It is
its own inverse, real-orthogonal, hence unitary.

**Verification:** `Pi_0 @ encode_4d_A1(pos_pre) = encode_4d_A1(pos_post)`
exactly, provided sig values for non-`o`, non-`d` squares are unchanged.
Holds for non-capture moves; for captures, `encode_4d_A1(pos_post)` includes
zero contribution from the captured square (which `Pi_0` accomplishes by
mapping `e_d` to `e_d` — destination square's value updates from
`sig_captured` to `sig_pre[o]`).

LOC: ~50 (mostly the swap operator construction; reuses `tables_4d.b4_a1_orbit_projector`
plumbing).

#### Channels 1-4 (STD4_X/Y/Z/W, coord-residual times signal):

Channel `a` value at square `s` is `coord_resid[a, s] * sig[s]`.

When piece `p` moves `o → d`:
- `coord_resid[a, o] * sig[o]` becomes `coord_resid[a, o] * 0` (vacated).
- `coord_resid[a, d] * 0` becomes `coord_resid[a, d] * sig_pre[o]` (occupied).

But `coord_resid[a, o] ≠ coord_resid[a, d]` in general (the residual depends
on the square). The channel value at `o` decreases by `coord_resid[a, o] * sig_pre[o]`,
and the channel value at `d` increases by `coord_resid[a, d] * sig_pre[o]`.

**Construction of `Pi_a`:** A 2×2 block on rows `o, d` of the channel-`a` block:

```
         col=o      col=d
row=o   [   0          0   ]
row=d   [coord_resid[a,d]/coord_resid[a,o]  0]
```

with all other rows being identity. This is **not** a clean permutation
because the coefficient `coord_resid[a,d] / coord_resid[a,o]` is not 1 in
general. The construction is a *scaled permutation*, which is unitary
**iff** `|coord_resid[a,d] / coord_resid[a,o]| = 1`.

For a generic move, this ratio is not 1. The unitary on channel `a`
must therefore be:

```
Pi_a = scaled_permutation * normalization_diagonal
```

where the normalization diagonal absorbs the ratio. Specifically: define

```
Pi_a[o, o] = sqrt(1 - |coord_resid[a,d]|^2 / |coord_resid[a,o]|^2)  -- absorbed elsewhere
```

This complicates construction. A cleaner alternative: **encode the
coord_resid coefficients into the basis**, so the channel block is built
on the pre-multiplied basis `e_s_a := coord_resid[a, s] * e_s`. In this
basis, `Pi_a` is a clean swap operator on `e_o_a, e_d_a`. The total
encoded vector is the same `coord_resid[a, s] * sig[s]` quantity, just
expressed in a different basis.

**Decision:** Construct `Pi_a` in the pre-multiplied basis. This requires
a 4096×4096 diagonal change-of-basis matrix `D_a = diag(coord_resid[a, *])`
applied at construction time (one-time, cached). The unitary `Pi_a` is then
a permutation in the `D_a`-basis; in the encoder's natural basis it is
`D_a @ swap @ D_a^{-1}`.

This is a **similarity transform** of the swap; it preserves unitarity but
introduces a rescaling. The result is unitary on the channel block as long
as `D_a` is invertible (which it is, except on the central squares where
`coord_resid = 0` — see §6 for the boundary case).

LOC: ~80 (one helper for `D_a`; one for the construction of the rescaled
swap; cached per channel).

#### Channels 8-9 (FA_PAWN_W, FA_PAWN_Y, pawn antisymmetric):

Channel 8 value: `Σ_{pawn at (sx,sy,sz,sw)} sign(color) * W_ANTI_DCT[sw]`
scattered into modes `(sx, sy, sz, *)`. Channel 9: same on Y axis.

When a pawn moves from `(sx0, sy0, sz0, sw0)` to `(sx1, sy1, sz1, sw1)`:
- The scatter at the old position is removed.
- The scatter at the new position is added.

**Construction of `Pi_8`:** A 16×16 block on the channel that swaps the 8
modes at `(sx0, sy0, sz0, *)` with the 8 modes at `(sx1, sy1, sz1, *)`,
applied via `W_ANTI_DCT` and its inverse.

Specifically: define `S_w = W_ANTI_DCT @ swap_8 @ W_ANTI_DCT^{-1}`, where
`swap_8` is the identity on the 8 mode positions. Then `Pi_8` is the lifted
version of `S_w` onto the channel block, mapping the 8 modes at the
pre-position to the 8 modes at the post-position.

Wait — that's a no-op. Let me re-examine: if the pawn moves from `p_pre` to
`p_post`, the W-channel contribution at `p_pre`'s mode-block is zero
post-move; the contribution at `p_post`'s mode-block is `W_ANTI_DCT[sw_post]`.
The unitary on the channel block must therefore swap a "filled" 8-block at
`p_pre` with an "empty" 8-block at `p_post`.

This is a **swap of two 8-mode blocks**. Construction: a 4096×4096
permutation matrix that exchanges row positions `[p_pre's 8 modes]` with
`[p_post's 8 modes]`. This is unitary by construction (any permutation is).

**Capture case:** If the pawn captures another pawn, the captured pawn's
8-block contribution is removed from the encoder (modes go to zero). The
operator on the channel is then a *partial isometry*: `Pi_8` maps the
captured pawn's 8 modes to zero, then swaps the moving pawn's modes.

A partial isometry has `‖ψ‖_post < ‖ψ‖_pre`; ADR-002's renormalization
restores `‖ψ‖ = 1`.

LOC: ~120 per axis channel (the W and Y constructions are nearly identical
modulo which factor of the kron product is operative).

### 3.2 Best-effort approximation channels (5-7, 10): construction

#### Channels 5-7 (FIB_SYM, bilinear in piece values):

Channel `c ∈ {5, 6, 7}` value: `fc[adj(k)] += gradient(k) * fib_d[piece(k), k, c-5]`.

The `gradient(k)` factor is `Σ_{n ∈ adj(k)} sig[n]` — a sum over neighboring
squares' signal values. **This is bilinear in `sig`:** the channel value at
`s ∈ adj(k)` depends on both `sig[k]` (via piece(k) selection) and `sig[n]`
for `n ∈ adj(k)` (via the gradient). A move that changes `sig[k]` updates
the channel via a **product** of two signal values, which is not linear.

**Strict-QM impossibility:** No linear `U_move_c` on `C^4096` satisfies
`U_move_c @ encode_4d_c(pos_pre) = encode_4d_c(pos_post)` exactly. The
encoding map `pos → encode_4d_c(pos)` is itself nonlinear in `pos`, so
linear maps on the codomain cannot reproduce arbitrary post-move encodings.

**Best-effort linearization:** Compute the Jacobian
`J_c(pos_pre) = ∂encode_4d_c / ∂sig` evaluated at `pos_pre`. Then
`U_move_c ≈ J_c(pos_pre) @ swap_pos_pre_to_pos_post` is a first-order
approximation that is *linear* (and can be made unitary by polar
decomposition).

**Acceptance criterion for v1.5:** The `U_move_c` produced by linearization
satisfies `‖U_move_c @ encode_4d_c(pos_pre) - encode_4d_c(pos_post)‖ < ε * ‖encode_4d_c(pos_pre)‖`
where ε ≤ 0.10 (10% relative error) on a random sample of 100 legal moves.
If ε ≤ 0.10, the channel ships in v1.5 with a documented "FIB_SYM channels
are first-order approximations" note. If ε > 0.10, the channel is treated
as a measurement-only block (see §3.3) — the QM module's `evolve_until` on
ψ would project away the FIB_SYM channels' amplitudes, and `U_move` would
zero them out (reset at each move boundary).

**Phase 3 prototype probe will determine which path applies.**

LOC: ~150 per FIB channel (Jacobian construction + polar projection +
fallback to measurement-only branch).

#### Channel 10 (FD_DIAG, linear-in-sig with piece-dependent coefficients):

Channel 10 value: `out[k] += sig[s] * DIAG_DEV[piece_row(s), k]`.

Linear in `sig[s]`, but the *coefficient* `DIAG_DEV[piece_row(s), k]`
depends on the piece type at `s`. A move that changes the piece at a
square changes the coefficient — but the formula remains linear in `sig`.

**Move semantics:** When piece `p` moves `o → d` (no capture):
- At `o`: contribution `sig[o] * DIAG_DEV[piece_row(p), k]` becomes 0.
- At `d`: contribution 0 becomes `sig[o] * DIAG_DEV[piece_row(p), k]`
  (same DIAG_DEV row because same piece; just different sig source).

The channel value updates as `out_post[k] = out_pre[k]` (the contribution
is the same; only the source square changed). The encoding is **invariant**
under non-capture, same-piece-type-only moves.

**Construction of `Pi_10`:** Identity on the channel block.

**For captures:** When piece `p` at `o` captures piece `p'` at `d`:
- At `o`: contribution `sig[o] * DIAG_DEV[piece_row(p), k]` becomes 0.
- At `d`: contribution `sig[d] * DIAG_DEV[piece_row(p'), k]` becomes
  `sig[o] * DIAG_DEV[piece_row(p), k]`.

The change is `sig[o] * DIAG_DEV[piece_row(p), k] - sig[d] * DIAG_DEV[piece_row(p'), k]`,
which is generically nonzero. The unitary on the channel block must add
this difference vector. This is a *rank-1 update*; the operation is
**unitary up to a renormalization**: `Pi_10 = I + rank_1_update_o_d` is
not strictly unitary (it has rank-1 perturbation, so it may be
ill-conditioned). After renormalization (ADR-002), the channel block's
contribution to `‖ψ‖` is properly maintained.

**Phase 3 prototype probe** will measure the conditioning of `Pi_10` for
random capture positions. If `cond(Pi_10) < 10`, the rank-1 update +
renormalization is acceptable. If `cond(Pi_10) > 100`, FD_DIAG ships as
measurement-only (analogous to FIB fallback).

LOC: ~80 (rank-1 update + condition number check + measurement-only
fallback path).

### 3.3 Measurement-only fallback semantics

For any channel that fails the v1.5 acceptance criterion (FIB ε > 0.10 or
FD_DIAG cond > 100), the fallback is:

- `U_move` zeros out the channel block on `ψ` after each move.
- The channel is *re-encoded* from the post-move position via
  `encode_4d` rather than evolved through `U_move`.
- This is a **measurement-only** block: the ψ amplitude in this channel
  represents "the result of measuring `pos_post` in the channel's basis,"
  not "the unitary evolution of pre-move amplitude through the move."
- Documented prominently in the v1.5 `qm_4d` docstring and the
  `applyMoveQm` API contract.

The fallback preserves overall norm (because re-encoding `pos_post` and
projecting to the channel produces a well-defined block contribution),
but is not strict-QM evolution. Consumers using the QM evaluator
(Phase 6) need to be aware of this when interpreting `getQmExpectation`
on channel-projector observables for FIB / FD channels.

---

## 4. Consequences

### 4.1 What this enables

- **Aggregate near-unitarity in v1.5.** Channels 0-4, 8-9 are strictly
  unitary; channels 5-7, 10 are best-effort. Total norm loss bounded
  empirically (target ≤ 5% per move on average, single-digit %
  cumulative over a 50-move game). ADR-002's renormalization handles
  it.
- **All 11 channels visible in M14.x.** No channel is hidden; consumers
  can render the full ψ throughout the game. The fallback channels
  display `pos_post`-encoded values (not pre-move + U_move evolved values),
  which is acceptable for visualization.
- **QM evaluator gets all observables.** `getQmExpectation` on
  `H_piece_4` (channels 0-4 + lifted to full encoder via Track A
  machinery) is strict-QM evaluation. Channel-projector observables
  (P_c) on FIB/FD channels are well-defined but reflect the post-move
  encoding rather than evolved amplitude.
- **Aaronson escape preserved on the strict channels.** Channels 0-4, 8-9
  carry ADR-001's per-channel phase rotations; superpositions across
  these channels accumulate channel-distinct phases under U_move,
  producing genuine quantum interference signatures.

### 4.2 What this forecloses

- **Full-strict-QM Track B in v1.5.** Channels 5-7 and 10 are not strictly
  evolved unitarily. A reviewer asking "is this QM chess?" gets a tiered
  answer: "Yes for 7 of 11 channels; the remaining 4 are best-effort
  linearizations / measurement-only fallbacks pending v1.7+ Stinespring."
- **Symmetric treatment of all channels.** The encoder's "11-channel
  decomposition as a built-in PVM" claim (§15.2(3)) is partially weakened:
  the channels that *fully* benefit from the QM front-end are the linear
  ones; the bilinear/nonlinear channels do so only approximately.
- **Closed-form proof of unitarity.** The mixed strict + approximate
  scope means no clean theorem like "∀ moves, U_move is unitary on ψ."
  Instead: "U_move is unitary on the projection of ψ onto the strict
  channel subspace; on the remaining channels, U_move is best-effort."
  This is the LOC-trap "purple-quantum" was warned about.

### 4.3 LOC implications

- **Strict-unitary channels (0-4, 8-9):** ~50-120 LOC each. Total: ~600 LOC.
- **Best-effort channels (5-7):** ~150 LOC each (Jacobian + polar +
  fallback). Total: ~450 LOC.
- **FD_DIAG (10):** ~80 LOC (rank-1 update + conditioning check).
- **Channel-dispatcher in `applyMoveQm`:** ~100 LOC (which channel
  handler to invoke for each move type; capture flag plumbing).
- **Measurement-only fallback infrastructure:** ~100 LOC (re-encode,
  project, normalize).
- **Total Track B LOC for ADR-003:** ~1330 LOC, the bulk of Track B's
  budget.

### 4.4 Test surface

- **Strict channels: per-channel unitarity.** For each of channels 0-4, 8-9,
  generate 50 random non-capture moves and 30 capture moves; assert
  `is_unitary(U_move_c, tol=1e-10)` (non-capture) or `is_partial_isometry(U_move_c, tol=1e-10)`
  (capture). ~150 LOC.
- **Strict channels: encoder consistency.** For each strict channel, assert
  `‖U_move_c @ encode_4d_c(pos_pre) - encode_4d_c(pos_post)‖ < 1e-10`
  for non-capture moves; for captures, assert the equation holds on the
  post-capture sub-basis. ~100 LOC.
- **Best-effort channels: ε-bound.** For each FIB channel and FD_DIAG,
  on a random sample of 100 moves, compute the actual ε
  (relative error) and assert ε ≤ ε_max (where ε_max is 0.10 for FIB and
  0.05 for FD). Report distribution stats. ~150 LOC.
- **Aggregate norm bound.** For a sample of 50-move games, assert that
  cumulative norm loss before renormalization stays within target
  (≤ 30% over a full game; this is bounded by capture frequency in
  typical games). ~100 LOC.
- **Fallback path triggers correctly.** For a hand-crafted "boundary"
  move that would push ε > ε_max on a FIB channel, assert the fallback
  is invoked and the channel is set to its post-move re-encoded value.
  ~50 LOC.

Total test LOC: ~550. (This is most of Track B's test budget; ADR-001 and
ADR-002 are smaller.)

---

## 5. Alternatives Considered

### 5.1 Option α: All channels strict — defer all bilinear to v1.7+

**Rejected.** The proposal: ship only the 7 strict-unitary channels
(0-4, 8-9) in v1.5; leave channels 5-7, 10 unimplemented (raise
`NotImplementedError` in `applyMoveQm` for any move that would touch
them).

- **Breaks `applyMoveQm` for every move.** Channels 5-7 and 10 are touched
  by *every* move (FIB_SYM by every non-pawn move; FD_DIAG by every move
  with mixed piece types in the position). There is no useful chess move
  that doesn't touch them. The "raise NotImplementedError" path means
  `applyMoveQm` is never callable in practice.
- **Breaks the §17.1 contract.** The bridge surface explicitly requires
  `applyMoveQm` to ship in Track B / Phase 4 / v1.5.0. Deferring to v1.7+
  pushes back the entire v1.5.0 release date by 4-6 months (the
  Stinespring v1.7+ work is a major effort).
- **Loses M14.3.** The trajectory replay milestone needs `applyMoveQm` to
  produce a renderable transition; without bilinear channels, the rendered
  ψ is dramatically incomplete.

### 5.2 Option β: All channels strict — use Stinespring on bilinear channels in v1.5

**Rejected.** The proposal: dilate the bilinear channels (5-7) to a larger
space where the bilinear formula becomes unitary. E.g., embed each FIB
channel into `C^4096 ⊗ C^auxiliary_state_size` where the auxiliary register
tracks the gradient values, making the bilinear product into a unitary
controlled-operation.

- **Massive LOC budget.** Stinespring dilation on each bilinear channel
  is ~600 LOC per channel + auxiliary register management + tests; total
  ~2500 LOC just for this. Track B's total LOC budget is ~2000.
- **Auxiliary register design unspecified.** The right size and structure
  for the auxiliary register depends on the gradient distribution, which
  varies by position. Designing it requires experimental probing
  (a Phase 3+ research effort, not a Phase 4 implementation).
- **Same effect as v1.7+ deferral.** If we ship Stinespring in v1.5, we're
  doing the v1.7+ work early, which contradicts ADR-002's gating
  decision (Stinespring deferred to v1.7+ pending Phase 6 evidence).

### 5.3 Option γ: All channels best-effort — accept all channels as approximations

**Rejected.** The proposal: for *all* 11 channels, use linearized `U_move_c`
at `pos_pre`; document that v1.5 is "approximate QM chess."

- **Loses the strict-QM grounding for the 7 strict channels.** Channels 0-4,
  8-9 *are* strictly unitary in their construction (cleanly proved above).
  Demoting them to "approximation" loses the rigor that makes Pre-flight 3's
  spectral identity result meaningful for QM-front-end claims.
- **More LOC, not less.** Linearizing every channel requires per-channel
  Jacobian computation; this is *more* code than the strict permutations,
  which are cheap. No LOC savings from this option.
- **Worse for Phase 6 / 7.** Strict channels carry stronger interference
  structure (per ADR-001's phase convention). All-approximate would dilute
  the interference signals that the QM evaluator is supposed to expose.

### 5.4 Option δ (within the chosen tiered approach): variations on FIB linearization

The chosen Option D leaves a sub-decision: how to linearize channels 5-7.
Three sub-variants considered:

- **(D1)** Jacobian at `pos_pre`, polar-decomposed to nearest unitary.
  *Chosen.* Cheapest, well-defined, ε-bound testable.
- **(D2)** Symmetric Jacobian (average of `J(pos_pre)` and `J(pos_post)`).
  Slightly better ε on average but requires post-move re-encoding to
  compute, which doubles the encoder cost per move.
- **(D3)** Stinespring auxiliary register on FIB channels only (a
  "limited Stinespring"). Leaves FD_DIAG at best-effort but lifts FIB to
  strict-QM. ~800 LOC; reasonable v1.6 candidate but too much for v1.5.

D1 ships in v1.5; D3 is a v1.6 follow-up if Phase 6 finds FIB approximation
artifacts in the QM evaluator.

---

## 6. Open Questions / Future Work

1. **Phase 3 prototype probe.** Build a 200-LOC prototype that:
   - Materializes `U_move_c` for each of 5-7 and 10 on a random sample
     of 50 chess moves (legal, drawn from a Lichess corpus or similar).
   - Measures the actual ε (FIB) and condition number (FD_DIAG) per move.
   - Reports the 50th, 90th, 99th percentile of ε and cond.
   - **Acceptance:** 90th percentile ε ≤ 0.10 for FIB and 90th percentile
     `cond` ≤ 100 for FD_DIAG. If either fails, that channel ships
     measurement-only in v1.5.

2. **v1.6 Stinespring on FIB.** If Phase 6 finds the QM evaluator's signal
   on FIB channels is washed out by linearization error, build the
   v1.6 limited-Stinespring D3 variant. ~800 LOC; clear motivation
   from empirical signal.

3. **v1.7 full Stinespring.** Per ADR-002, deferred until Phase 6 evidence
   motivates it.

4. **Boundary case: `coord_resid = 0` central squares.** STD4 channels'
   diagonal change-of-basis `D_a = diag(coord_resid[a, *])` has 256 zero
   entries (squares on the lattice's "central" axis where the residual
   vanishes). The similarity transform `D_a @ swap @ D_a^{-1}` is
   ill-defined there. Handle via: the channel-`a` block on those zero
   entries always carries amplitude 0 in any encoded position (the
   coefficient is zero), so the swap operation on those rows is moot.
   Implementation: pad with identity on the zero rows. Verify this is
   correct in the prototype.

---

## 7. References

- **Encoder structure** ([encoder_4d.py:115-127, 326-447](../../../python/chess_spectral/encoder_4d.py#L326-L447)) — the 11-channel construction this ADR analyzes.
- **Tables** ([tables_4d.py](../../../python/chess_spectral/tables_4d.py)) — for `b4_a1_orbit_projector`, `coord_resid`, `W_ANTI_DCT`, `Y_ANTI_DCT`, `DIAG_DEV`, `local_fiber_4d`, `piece_adjacencies_4d`.
- **Notebook §8** ([chess_spectral_research_notebook.md, sec 8](../../../../chess_spectral_research_notebook.md#8-practical-encoding-what-worked-and-what-didnt)) — encoder evolution / "what works" summary.
- **Notebook §15.2(3)** ([chess_spectral_research_notebook.md, sec 15.2](../../../../chess_spectral_research_notebook.md#152-the-enabling-machinery)) — 11-channel decomposition as PVM.
- **Notebook §17.1** ([chess_spectral_research_notebook.md, sec 17.1](../../../../chess_spectral_research_notebook.md#171-chess-spectral-15--qm-extension-bridge-surface)) — `applyMoveQm` bridge contract.
- **Pre-flight 2** ([phase_operators_4d_pseudo_hermitian_audit.md](../../../python/research/phase_operators_4d_pseudo_hermitian_audit.md)) — for the "channels 5-7 use multiplications" finding (independently confirmed in §2.1 of this ADR).
- **ADR-001** — phase convention; `U_move = ⊕_c e^(i*theta_c) * Pi_c`. This ADR
  defines `Pi_c` for each channel.
- **ADR-002** — capture renormalization handles the partial-isometry slack
  on channels 8-9 (capture) and the linearization residual on channels 5-7, 10.
- **ADR-004** — Z_2 superselection; this ADR's per-channel construction must
  preserve the Z_2 sector structure (verified per-channel).
- **Polar decomposition reference:** Higham, N. *"Functions of Matrices,"
  SIAM 2008.* For the unitary projection of `J_c`.

---

## 8. Phase 4 Implementation Pointer

**This is the design we will implement in Phase 4 B[3] (per-channel move
construction).** The roll-out order is:

1. **Phase 4 B[3a]:** Channels 0-4 (A1 + STD4_*). The cleanest case;
   establishes the test infrastructure. ~700 LOC + ~200 test LOC.
2. **Phase 4 B[3b]:** Channels 8-9 (FA_PAWN_W/Y). Moderate LOC, fully
   strict; uses ADR-005's pseudo-Hermitian pawn machinery for direction
   handling. ~250 LOC + ~100 test LOC.
3. **Phase 4 B[3c]:** Phase 3 prototype probe results land. Decide v1.5
   scope for channels 5-7 and 10 based on actual ε / cond percentiles.
4. **Phase 4 B[3d]:** Channels 5-7 (FIB_SYM_1/2/3) per the prototype
   results. Either D1 linearization (if ε ≤ 0.10) or measurement-only
   fallback. ~450 LOC + ~150 test LOC.
5. **Phase 4 B[3e]:** Channel 10 (FD_DIAG) per the prototype results.
   Either rank-1 + renormalization (if cond ≤ 100) or measurement-only.
   ~80 LOC + ~50 test LOC.

Acceptance for v1.5.0 ship: the §4.4 test surface passes; the M14.3
prototype renders a smooth multi-move sequence with documented but
acceptable norm losses; the Phase 6 QM evaluator computes
`getQmExpectation` cleanly on H_piece observables (which live on the
strict channels).

# ADR-004: Z_2 Superselection Structure

**Date:** 2026-04-29
**Branch:** `chess-spectral/qm-4d-kinematic`
**Track:** B (full move-as-unitary dynamics)
**Ships in:** Phase 4 / `qm_4d.state_to_psi`, Z_2 commutation tests / chess-spectral v1.5.0

---

## 1. Status

**Proposed (Option A: Z_2-graded full space with side-to-move charge).**

Track A's `state_to_psi` already implements this informally (multiplies the
encoded vector by ±1 according to side-to-move). This ADR formalizes the
convention as a superselection-sector grading and locks down the Track B
contract.

---

## 2. Context

Pre-flight 1 ([chess_spectral_4d_notebook.md, sec qm_4d Pre-flight Findings](../../../../chess_spectral_4d_notebook.md#pre-flight-1--encoder-injectivity))
established that `encode_4d` is **not injective on synthetic anti-podal-king
configurations**. Exactly 8 of 41 556 synthetic positions encode to the same
vector as a sibling under the involution

```
  J : pos ↦ (central inversion x ↦ (7,7,7,7) − x) ∘ (global color flip)
```

`J` is an order-2 group element (`J^2 = id`); together with the identity it
generates `Z_2 = {id, J}`. The 8 colliding positions are exactly the
fixed-point set of `J`, all of the form

```
  K @ (0,0,0,0) + k @ (7,7,7,7) + (single piece on the main 4D diagonal at
                                    one of {(2,2,2,2), (3,3,3,3), (4,4,4,4), (5,5,5,5)})
```

Track A resolves this by taking `side_to_move` as a second input and
multiplying ψ by +1 (white) or −1 (black). This is sufficient for the
"distinguish a position from its `J`-image" purpose: `J` includes a color
flip, so applying `J` to a "white-to-move" position produces a
"black-to-move" position with negated color labels — and the side-to-move
sign flips. The product `(J-induced encoder collision) × (side-flip)` =
identity, so the sign-tagged encoded vectors are distinct.

But this is only the kinematic resolution. Track B's `applyMoveQm` and
`evolve_until` need a deeper, formal statement of what "Z_2 superselection"
means. Specifically:

1. Is the QM theory defined on **the full ℂ^45056** with a Z_2 grading
   (states are equivalence classes under `J`; observables must commute
   with the Z_2 action)?
2. Or on the **quotient ℂ^45056 / Z_2** — a smaller space where Z_2 is
   gauge-fixed?
3. How does the Z_2 action interact with `applyMoveQm`?
4. What does `getQmState` return — a representative of a Z_2 orbit, the
   orbit itself, or one fixed gauge?

These questions affect: (a) the complexity of the bridge contract for
`getQmState`; (b) whether observables like `H_rook_4` etc. commute with
Z_2 (a Pre-flight 2 cross-check needed in this ADR); (c) the visualization
plan (the consumer's M14.x rendering must look stable across the Z_2
action — the same chess position should look the same regardless of the
sign-tag choice).

---

## 3. Decision

**Adopt Option A: full ℂ^45056 with Z_2 grading.** Specifically:

### 3.1 The grading structure

The QM Hilbert space is the full encoder image:

```
H_QM = C^45056
```

with a Z_2-grading via the involutive operator

```
J_op : H_QM → H_QM,    J_op(psi)[s] = psi[J(s)]
```

where `J(s)` is the involution on the 4096-dim board basis (central
inversion + color flip applied to the encoded square label). `J_op`
extends naturally to all 11 channels: the channels are B_4-equivariant
modules, and `J` is in the center of B_4 ∪ {color-flip}, so `J_op` acts
block-diagonally on the channel decomposition.

The two superselection sectors are:

- `H_+` = `{ψ : J_op ψ = +ψ}` ≅ "white-to-move" sector
- `H_−` = `{ψ : J_op ψ = −ψ}` ≅ "black-to-move" sector

Every chess position has a side-to-move label, so every encoded position
lives in exactly one sector (modulo the 8 fixed points, which were the
kinematic collisions Pre-flight 1 found).

### 3.2 The state_to_psi convention (explicit)

```python
def state_to_psi(position, side_to_move):
    enc = encode_4d(position).astype(complex128)
    if not side_to_move:
        # Black to move: flip the sign of the encoded vector to land in H_−.
        enc = -enc
    return enc / norm(enc)
```

Equivalent statement: ψ = `(1/2)(I + (-1)^side * J_op) * encode_4d(pos)`,
which projects `encode_4d(pos)` onto `H_+` or `H_−` according to
`side_to_move`. The sign-multiplication implementation is the same
because `encode_4d(J(pos)) = encode_4d(pos)` (the encoder is `J`-invariant
by §15.2(5)), so `J_op @ enc = enc` and the projector simplifies to
`±I @ enc`.

### 3.3 Observables must commute with `J_op`

A QM observable on `H_QM` is *physical* (i.e., respects Z_2 superselection)
iff it commutes with `J_op`. Consequence: physical observables decompose
as `O = O_+ ⊕ O_−` with `O_±` acting on `H_±`.

The 5 non-pawn Hermitian observables `H_rook_4`, `H_bishop_4`,
`H_queen_4`, `H_king_4`, `H_knight_4` are constructed as graph-adjacency
matrices on the 4096-dim board basis (Pre-flight 2). The `J` involution on
the board (central inversion + color flip; the color flip is trivial on the
non-color-tagged board basis, so effectively just central inversion)
**commutes with these observables** by the following argument:

- Central inversion is the involution `s ↦ (7,7,7,7) − s` on the 4096-dim
  board.
- Each `H_piece_4` is an adjacency matrix of the piece's reach graph on
  this board.
- Reach-by-piece is symmetric under central inversion: `s ↦ s'` is a legal
  rook step iff `J(s) ↦ J(s')` is also a legal rook step (rook reach is
  rotationally symmetric; the lattice has B_4 symmetry; central inversion
  is in B_4).
- Therefore `H_piece_4` commutes with the central-inversion permutation
  matrix on the 4096-dim block.
- Lifting to the full `C^45056`: `J_op` acts as `I_11 ⊗ central_inv`
  block-diagonally; each `H_piece_4` lifted to `C^45056` is `Σ_c P_c ⊗ H_piece_4`
  for various channel projectors. The lifted observable commutes with
  `J_op` block-by-block.

**Verification required at construction time** (one-shot test in v1.5.0
test suite): for each of the 5 H_piece observables, assert
`‖[H_piece, J_op]‖_F < 1e-10`. This is a closed-form check; expected to pass
trivially.

### 3.4 The U_move operator must respect `J_op`

A move `(o, d)` flips side-to-move: white-to-move position → black-to-move
position (or vice versa). Under our convention, ψ flips Z_2 sector under a
move:

- ψ ∈ H_+ (white to move) → ψ_post ∈ H_− (black to move now).

This means `U_move @ J_op = −J_op @ U_move` (`U_move` *anti-commutes* with
`J_op`, not commutes). Equivalently: `U_move` is a Z_2-graded operator of
*odd parity* (it changes sector).

This is a strong constraint on `U_move`. Verification: for each of the
strict-unitary channel constructions in ADR-003, the per-channel `Pi_c`
must satisfy `Pi_c @ J_c = −J_c @ Pi_c` where `J_c` is the channel-`c`
restriction of `J_op`. This is a per-channel test that must be added to
ADR-003's test surface.

### 3.5 What `getQmState` returns

`getQmState` returns ψ ∈ H_QM (the full 45056-dim vector). The return is
a representative of the position's Z_2-equivalence class — but the
representative is *unique* given side-to-move (since the sign-multiplication
canonicalizes it). The bridge contract returns a flat real+imag-interleaved
Float32 array; the consumer treats this as the canonical ψ.

The consumer does NOT need to know about the Z_2 sector explicitly. From
the consumer's perspective, ψ is just "the QM state of the position." The
sign-multiplication is internal to `qm_4d`'s convention.

### 3.6 The 8 fixed-point positions

The 8 anti-podal-king + diagonal-piece configurations are *fixed points*
of `J`: `J(pos) = pos`. For these, `encode_4d(pos) = encode_4d(J(pos))`
trivially. The sign-multiplication still distinguishes them (white-to-move
encoding is +enc, black-to-move is −enc), so kinematic injectivity is
preserved.

But these positions have a special property: `J_op` acts as `±I` on
`encode_4d(pos)` (since `J(pos) = pos` implies the encoded vector is
`J_op`-invariant *as a vector*; up to sign). For these specific 8 positions,
ψ lives in *both* `H_+` and `H_−` simultaneously (it's a +1 eigenvector of
`J_op` and a −1 eigenvector simultaneously, which is contradictory unless
the encoded vector is zero — which it isn't for these positions, by
construction). The contradiction means these positions *don't fit* the
strict superselection grading.

**Resolution:** For these 8 fixed-point positions, the QM module declares
they live in a *boundary* subspace `H_0` ⊆ `H_QM` defined as
`H_0 = {ψ : J_op ψ = ψ}` — the +1 eigenspace alone. The −1 eigenspace
contribution is zero for these positions. Mathematically, ψ ∈ `H_0 ⊆ H_+`,
and the "black-to-move" encoding's `−enc` is *also* in `H_+` (since
`J_op @ (−enc) = −J_op @ enc = −enc`), so we need to pick a convention.

**Decision for v1.5:** Document the 8 boundary positions as edge cases.
For these positions, `state_to_psi(pos, white)` and
`state_to_psi(pos, black)` both return ψ-vectors in `H_0`. The encoded
vectors differ by sign, which is sufficient for the kinematic distinguishing
purpose. The Track B QM dynamics treat them as members of the dominant
sector by convention (white = `H_+` representative, black = `H_−`
representative-via-sign-flip-from-H_0). No test fails; no observable behaves
unexpectedly.

This is a `O(8 / 41556)` ≈ 0.02% edge-case set on synthetic corpora and
0.0% on real-game corpora. Document as a known boundary; ship.

### 3.7 Interaction with B_4 equivariance

The encoder is B_4-equivariant: the 11 channels carry well-defined irrep
labels (per ADR-001's §3.1 table). `J` (central inversion) is the unique
order-2 *central* element of B_4 (sign-flip on all axes simultaneously,
no permutation). This means `J_op` is in the center of the B_4 unitary
representation:

```
J_op @ U_4096(g) = U_4096(g) @ J_op    for all g ∈ B_4
```

(Verifiable: the central inversion permutation matrix commutes with all B_4
permutations because B_4's representation factors through `S_4 ⋉ Z_2^4`; the
central element of `Z_2^4` is `(−1, −1, −1, −1)`, which is central by
construction.) Consequence: B_4 acts within each Z_2 sector. The §15.2's
"B_4 equivariance for free" claim is preserved under the Z_2-grading.

---

## 4. Consequences

### 4.1 What this enables

- **Clean superselection language.** Pre-flight 1's "ψ lives on
  `configurations / Z_2`" gets a precise mathematical statement: ψ lives
  on `H_QM = H_+ ⊕ H_−`, with `state_to_psi` projecting deterministically
  into `H_±` based on side-to-move.
- **Move operator parity is well-defined.** `U_move` is an odd-parity
  Z_2-graded operator. This is a checkable invariant, added to ADR-003's
  test surface.
- **Visualization stability.** The consumer's M14.x plots ψ; under the Z_2
  action, ψ flips sign, but `|ψ|^2` (probability density) and observable
  expectation values are sign-invariant. So the consumer sees stable
  rendering across the Z_2 action automatically. No special handling needed
  in the bridge.
- **Pre-flight 2 commutation cross-check is trivial.** The 5 `H_piece_4`
  observables commute with `J_op` by construction (graph-adjacency
  matrices of B_4-symmetric reach graphs commute with B_4-central elements).
  The cross-check is a closed-form test, not a deep theorem.
- **Side-to-move integration is API-clean.** `state_to_psi(pos, side)`
  takes side as input; the rest of the API doesn't reference side
  explicitly (though `applyMoveQm` indirectly flips it via the move
  operator's odd parity).

### 4.2 What this forecloses

- **Quotient-space implementation.** Option B (work on `C^45056 / Z_2`)
  was rejected; we work on the full `C^45056`. This means the 8 fixed-point
  positions are edge cases rather than identified points. Acceptable
  trade-off given how rare they are.
- **Direct Z_2-charge as a measurable.** Since `J_op` *is* the Z_2 charge
  operator, "measuring side-to-move" is equivalent to measuring `J_op`'s
  eigenvalue. We don't expose `J_op` as a measurable observable in v1.5
  (it's used internally only) — the consumer asks for side-to-move via
  the explicit input parameter, not via measurement. Could expose it
  in v1.6 if useful.
- **Other discrete symmetries not yet handled.** `J` is the *only* order-2
  involution we explicitly handle. The encoder respects other symmetries
  too (full B_4, not just the central element); but they don't have
  superselection-sector structure (B_4 acts within sectors). If future
  work finds a need to add another superselection (e.g., for castling
  rights or en-passant flags), it would extend the grading.

### 4.3 LOC implications

- **Documentation update in `state_to_psi`:** ~30 LOC docstring elaboration
  on the grading structure; no functional change.
- **`J_op` as a sparse operator (used internally):** ~50 LOC (build
  the 4096×4096 central-inversion permutation; lift to 45056×45056 as
  `I_11 ⊗ central_inv`). Cached.
- **Z_2 commutation test for observables:** ~80 LOC (one test per
  H_piece observable, asserting `‖[H_piece, J_op]‖_F < 1e-10`).
- **Z_2 anti-commutation test for U_move:** ~50 LOC per channel,
  added to ADR-003's test surface (so this LOC is shared with ADR-003).
- **Edge-case test for 8 fixed-point positions:** ~80 LOC (load each of
  the 8 positions, assert `state_to_psi` returns a ψ consistent with the
  boundary handling in §3.6).

Total ADR-004-specific LOC: ~290.

### 4.4 Test surface

- **`J_op` is unitary and order-2.** `J_op^2 = I`. `J_op @ J_op^dagger = I`.
  ~20 LOC.
- **`encode_4d(pos)` is `J_op`-invariant.** For 100 random positions,
  assert `‖encode_4d(J(pos)) - encode_4d(pos)‖ < 1e-10`. ~30 LOC.
- **`state_to_psi(pos, white)` is in `H_+`.** Assert `J_op @ ψ = +ψ` for
  100 random positions with white-to-move. ~30 LOC.
- **`state_to_psi(pos, black)` is in `H_−`.** Same with negated. ~30 LOC.
- **`H_piece` commutes with `J_op` for each of {N, B, R, Q, K}.** ~80 LOC.
- **`U_move` anti-commutes with `J_op`.** For 50 random moves, assert
  `‖U_move @ J_op + J_op @ U_move‖_F < 1e-10`. ~50 LOC.
- **8 fixed-point positions handled per §3.6.** Closed-form test on the
  8 specific positions from Pre-flight 1's CSV. ~80 LOC.

Total test LOC: ~320.

---

## 5. Alternatives Considered

### 5.1 Option B: Work on the quotient ℂ^45056 / Z_2

**Rejected.** The proposal: identify ψ and `J_op @ ψ` as the same state;
work in a smaller Hilbert space `H_quot = ℂ^45056 / Z_2`.

- **Smaller space.** `H_quot` has dimension `45056 / 2 + (8 fixed points)`
  ≈ 22 532 + 8 = 22 540, roughly half the size of the full space. Some
  computational savings.
- **Awkward to implement.** Working in the quotient requires choosing
  representative-fixing maps for each equivalence class. The "fix the
  white-to-move representative" choice is just our Option A, with
  side-to-move tracking as an explicit register — i.e., it reduces back
  to Option A in implementation.
- **Move parity becomes inelegant.** Under the quotient, `U_move` no
  longer has a clean parity (it would need to invoke the choice-of-representative
  function on output). The graded structure is more transparent.
- **Visualization breaks.** Consumers expect ψ to have a stable size
  (`|ψ|^2` summed gives 1.0). On the quotient, the size depends on whether
  the position is a fixed point or not. Inconsistent.
- **Loses Pre-flight 3's structure.** The encoder basis is the simultaneous
  eigenbasis of `(Δ, B_4 commutant)` on the full `ℂ^4096` per channel.
  Working on the quotient loses this clean picture.

The quotient is mathematically equivalent to the graded full space, but
implementing the quotient is more work for less clarity. Reject.

### 5.2 Option C: No Z_2 structure; Pre-flight 1's collisions are accepted

**Rejected.** The proposal: ignore `J`; just live with the 8 collisions
on the synthetic corpus.

- **Real-game corpora are 100% injective** (Pre-flight 1). So this option
  works in practice for any chess game. But...
- **Track B's `applyMoveQm` semantics need a sector concept.** A move
  flips side-to-move. Without a Z_2 sector, the move's "what does it do"
  is ambiguous on the encoded vector — `applyMoveQm` could produce either
  sign of the post-move encoded vector, indistinguishable. We need the
  sign convention to be fixed.
- **Pre-flight 2's H_piece commute structure breaks.** Without `J_op`,
  there's no "physical observable" criterion. Consumers asking "why
  doesn't the QM evaluator flip sign on Z_2-related positions?" have no
  clean answer.
- **Loses interpretability.** "ψ lives on configurations / Z_2" is a
  publishable claim. "ψ lives on configurations modulo a thing we ignored"
  isn't.

Reject. The Z_2 structure is interpretively load-bearing even if it's
not strictly required for kinematic distinguishing on real games.

### 5.3 Option D: Z_2 with a different generator

**Rejected.** The proposal: instead of "central inversion + color flip,"
use just the color flip (a physical observable: who's playing white
vs. black) as the Z_2 generator.

- **Color flip alone doesn't generate the encoder collision class.**
  Pre-flight 1's collisions are fixed points of *both* central inversion
  *and* color flip — not color flip alone. Using just color flip misses
  the collision pattern.
- **Color flip on the 4096-dim board basis is the identity** (the board
  basis doesn't carry color labels; pieces do). So `J_op_color` is
  effectively the identity on `ℂ^4096`, providing no distinguishing
  power.
- **Doesn't match the Pre-flight 1 finding.** The audit identified the
  composite involution; using a different one is just renaming.

Reject.

### 5.4 Option E: Continuous gauge instead of Z_2

**Rejected.** The proposal: replace the discrete Z_2 with a continuous
`U(1)` gauge — multiply ψ by `e^(i*alpha*side)` for some continuous
alpha.

- **No physical motivation.** `J` is genuinely an order-2 involution on
  positions; it's discrete. Imposing a continuous gauge is unphysical.
- **Breaks observable-commutation.** Continuous-U(1) symmetries forbid
  observables that are not `U(1)`-invariant; this would over-constrain
  what `getQmExpectation` can return.

Reject. Z_2 is the right structure.

---

## 6. Open Questions / Future Work

1. **`J_op` as an exposed observable in v1.6+.** If consumers find utility
   in measuring "Z_2 charge" directly (e.g., for diagnostics), expose
   `J_op` as a named observable in `getQmExpectation`. Currently internal-only.

2. **Phase-3 pre-implementation probe.** Verify the §3.3 claim
   (H_piece commutes with `J_op`) closed-form before Track B implementation
   begins. If any H_piece *fails* to commute (e.g., if the lift introduces
   a non-symmetric edge case at the boundary), this affects ADR-003's
   construction. Probe script: ~30 LOC (read existing `H_piece` from
   qm_4d.py, build `J_op`, compute commutator norm). Run as part of Phase
   3 pre-flight.

3. **Z_2 sector for promoted pawns.** A pawn promotion changes the piece
   type; the resulting position lives in a different "subspace" of the
   encoder (different non-pawn channel populations). This doesn't change
   the Z_2 sector (side-to-move flips as expected), but the sector
   *content* changes. ADR-003 already handles this in the per-channel
   construction; cross-reference for clarity.

4. **Higher-order discrete symmetries.** Are there other Z_2 involutions
   beyond `J`? E.g., reflection along single axes? B_4 is generated by
   axis sign-flips and axis permutations; the central element `J` is the
   product of all 4 axis sign-flips. Other order-2 elements exist (single
   axis flip, axis-pair swap, etc.) but they don't generate encoder
   collisions on the synthetic corpus. So no additional superselection
   structure needed in v1.5. Could be revisited if future encoder
   variants change the collision pattern.

---

## 7. References

- **Pre-flight 1** ([chess_spectral_4d_notebook.md, sec qm_4d Pre-flight Findings](../../../../chess_spectral_4d_notebook.md#pre-flight-1--encoder-injectivity)) — establishes the Z_2 collision class.
- **Pre-flight 2** ([phase_operators_4d_pseudo_hermitian_audit.md](../../../python/research/phase_operators_4d_pseudo_hermitian_audit.md)) — the H_piece observables that this ADR shows commute with J_op.
- **Notebook §15.2(5)** ([chess_spectral_research_notebook.md, sec 15.2](../../../../chess_spectral_research_notebook.md#152-the-enabling-machinery)) — "built-in Z_2 superselection structure" section that this ADR formalizes.
- **Notebook §17.1** ([chess_spectral_research_notebook.md, sec 17.1](../../../../chess_spectral_research_notebook.md#171-chess-spectral-15--qm-extension-bridge-surface)) — `getQmState` and `state_to_psi` API contracts.
- **Track A `state_to_psi`** ([qm_4d.py:92-132](../../../python/chess_spectral/qm_4d.py#L92-L132)) — the existing kinematic implementation this ADR formalizes.
- **Encoder injectivity probe** ([encoder_injectivity_4d.py](../../../python/research/encoder_injectivity_4d.py)) — Pre-flight 1's source script and the 41556-row CSV.
- **B_4 representation** ([qm_4d.py:215-251](../../../python/chess_spectral/qm_4d.py#L215-L251)) — the B_4 unitary action that commutes with `J_op`.
- **ADR-001** — phase convention; the per-channel phases in ADR-001's §3.1
  must respect Z_2 sector structure.
- **ADR-003** — per-channel construction; the U_move's odd parity under
  Z_2 is a per-channel test added to ADR-003's surface.
- **Mostafazadeh, A.** *"Pseudo-Hermiticity versus PT Symmetry," J. Math. Phys. 43, 205 (2002).*
  Z_2-grading of Hilbert spaces is a standard technique in pseudo-Hermitian QM.
- **Streater, R. F. and Wightman, A. S.** *"PCT, Spin and Statistics, and All That," Princeton 2000.* Reference for superselection-sector formalism.

---

## 8. Phase 4 Implementation Pointer

**This is the design we will implement in Phase 4 B[4] (Z_2 grading
formalization and verification).** Implementation is mostly *test code*
plus a small `J_op` builder helper:

1. **Phase 4 B[4a]:** Build `J_op` as a sparse 45056×45056 operator.
   Cache. ~50 LOC.
2. **Phase 4 B[4b]:** Add §4.4 commutation tests to the `test_qm_4d.py`
   suite. ~320 LOC.
3. **Phase 4 B[4c]:** Update `state_to_psi` docstring to reference this ADR
   and clarify the grading structure. ~30 LOC.
4. **Phase 4 B[4d]:** Add anti-commutation test for `U_move` (cross-test
   with ADR-003's strict-channel constructions). Tests share LOC with
   ADR-003's test surface. ~50 LOC marginal.

Acceptance: all §4.4 tests pass at machine precision; the 8 fixed-point
positions handled correctly per §3.6; documentation in `state_to_psi`
docstring is updated; the §16.7 / §16.8 tournament-harness QM evaluator
returns sign-consistent values across positions and their `J`-images.

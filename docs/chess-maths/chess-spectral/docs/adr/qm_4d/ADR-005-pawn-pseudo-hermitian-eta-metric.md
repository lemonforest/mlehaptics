# ADR-005: Pawn Pseudo-Hermitian η-Metric

**Date:** 2026-04-29
**Branch:** `chess-spectral/qm-4d-kinematic`
**Track:** B (full move-as-unitary dynamics)
**Ships in:** Phase 4 / `qm_4d.H_pawn_w_4`, `H_pawn_y_4`, `eta_pawn_4` / chess-spectral v1.5.0

---

## 1. Status

**Proposed (best-effort projection onto Hermitian part for v1.5; full
PT-symmetric η for v1.6+ if Phase 6 evidence motivates it).**

This ADR ships v1.5 with a **two-tier delivery**: a "best-effort
Hermitian-part projection" pawn observable that is unitarily exposed as
`H_pawn_w_4_herm` and `H_pawn_y_4_herm`, plus the η-metric framework
**stubbed** so that v1.6+ can promote it to first-class without an API
break. The full pseudo-Hermitian / PT-symmetric machinery is documented
here but ships fully only when motivated.

---

## 2. Context

Pre-flight 2 ([phase_operators_4d_pseudo_hermitian_audit.md](../../../python/research/phase_operators_4d_pseudo_hermitian_audit.md))
established that the 5 non-pawn predicates (`P_rook4`, `P_bishop4`,
`P_queen4`, `P_king4`, `P_knight4`) lift to **real-symmetric Hermitian
matrices** on `C^4096`. The lift commutes with `J_op` (ADR-004) and
admits the trivial metric `η = I`.

The **pawn predicates** (`P_pawn4_white`, `P_pawn4_black`) **break
Hermiticity** because pawn pushes are *directed*:
- White pawns push along `+w` axis (or `+y` axis per Oana & Chiru
  Definition 11; pawns oriented along Y or W axis only).
- Black pawns push along `-w` (or `-y`).
- Captures are diagonal, also directed.

The lifted matrix `M_pawn_white` has `M_pawn_white ≠ M_pawn_white^T`. The
asymmetry sits in the diagonal-capture sub-block and the forward-push
sub-block. A `M_pawn_black` lift would be the transpose / dagger of
`M_pawn_white` on the capture sub-block (black's diagonal captures match
white's diagonal captures with axis flipped).

For Track B's QM evaluator (`getQmExpectation` from §17.1), pawns *must*
be measurable somehow — chess without pawn observables is incomplete.
The question is **what kind of pawn observable** the QM module exposes.

### 2.1 The pseudo-Hermitian / PT-symmetric framework

Mostafazadeh (2002, 2010 reviews) and Bender-Boettcher (1998) introduced
**pseudo-Hermitian operators**: operators `O` on a Hilbert space `H` for
which there exists an invertible Hermitian `η` with

```
O^dagger = η * O * η^{-1}            (η-pseudo-Hermiticity)
```

Equivalently: `O` is Hermitian under the *modified inner product*

```
<a|b>_η := <a|η|b>           (the η-inner-product)
```

This is the natural generalization of "Hermitian" beyond the standard
`η = I` case. **PT-symmetric operators** (Bender-Boettcher) are a
special case where `η = PT` is the parity-time operator. PT-symmetric
operators have **real spectrum** under conditions Bender enumerates
(unbroken PT phase).

The directed-push pawn predicates are **prime candidates** for
PT-symmetric machinery:
- Parity (P): the axis-flip on the pawn's direction (W-axis flip for
  W-axis pawns; Y-axis flip for Y-axis pawns).
- Time-reversal (T): the color flip (white ↔ black).
- The composition PT applied to `M_pawn_white` gives a candidate `η`.

**This is where the "qm_4d earns its keep" framing from notebook §15.2(4)**
points. If the pawn machinery shipped as a pseudo-Hermitian operator under
a meaningful η, that's the structural payoff that distinguishes Track B
from Track A.

### 2.2 The infrastructure problem

Building a usable pseudo-Hermitian / PT-symmetric framework requires:

1. **An η operator.** Compute and verify `M_pawn_white^dagger = η * M_pawn_white * η^{-1}`
   for some explicit η. This is non-trivial: η is determined up to a positive
   scalar by the pseudo-Hermiticity condition, but constructing it
   explicitly requires either a closed-form derivation from PT-symmetry
   (Bender-Boettcher) or a numerical search (eigendecomposition-based).
2. **The η-inner-product machinery.** New helpers `inner_product_eta(a, b, eta)`,
   `expectation_eta(O, psi, eta)`, `is_pseudo_hermitian(O, eta)`. The
   existing qm_4d API uses `vdot` (standard inner product); pseudo-Hermitian
   observables need their own evaluation path.
3. **Spectrum-realness verification.** PT-symmetric operators have real
   spectra in the unbroken phase. We must verify (numerically) that
   `M_pawn_white` (or its η-lifted version) has real spectrum — and
   handle the case where it doesn't (PT phase broken).
4. **Bridge contract integration.** `getQmExpectation('pawn', ...)`
   must specify which evaluation rule applies — standard `<ψ|H|ψ>` or
   η-modified `<ψ|H|ψ>_η`. The 17.1 contract didn't pre-decide this.

### 2.3 The v1.5 LOC budget pressure

Track B's overall LOC budget is ~2000 LOC (notebook §17.1.2 acceptance
criteria + history-dependent budgeting). ADR-001 (phase) is ~250 LOC,
ADR-002 (evolution) is ~110 LOC, ADR-003 (per-channel) is ~1330 LOC,
ADR-004 (Z_2) is ~290 LOC. **Track B's available budget for ADR-005
is ~20 LOC** — far less than what a full η-metric implementation needs.

A full pseudo-Hermitian implementation alone is ~600 LOC:
- η construction + verification: ~150 LOC.
- η-inner-product helpers: ~100 LOC.
- Spectrum-realness machinery: ~150 LOC.
- Pawn observable lift + dispatch: ~100 LOC.
- Tests: ~200 LOC.

This is impossible to ship as a v1.5 deliverable. We must choose between
(a) shipping pawn observables in a reduced form, or (b) deferring pawn
observables entirely (raising NotImplementedError) and shipping the
η-metric in v1.6.

---

## 3. Decision

**Two-tier delivery:**

### 3.1 v1.5 deliverable: best-effort Hermitian-part projection

For v1.5.0, expose pawn observables via the **Hermitian part** of the
lifted pawn matrix:

```
H_pawn_<axis>_4_herm  := (1/2) * (M_pawn_<axis> + M_pawn_<axis>^T)
```

where `<axis>` ∈ {`w`, `y`}. The `_herm` suffix is intentional — the
naming makes the approximation visible in the API.

This is a strictly Hermitian operator on `C^4096`. It loses the
direction-asymmetric information (forward-push vs backward-push are
averaged), but it captures the *symmetric* pawn structure: where pawns
*can* exist regardless of color.

Properties:
- Real-symmetric, Hermitian under `η = I`.
- Real spectrum (Pre-flight 2 already confirmed real-symmetric matrices
  have real spectrum).
- `J_op`-commuting (per ADR-004's general argument for B_4-symmetric
  graph-adjacency lifts; cross-axis pawn directionality cancels under
  `J`'s color-flip).

Exposed as:
- `H_pawn_w_4_herm` (lazy module property)
- `H_pawn_y_4_herm` (lazy module property)

Used by the Phase 6 QM evaluator for pawn-related contributions to
`getQmExpectation`. Documented prominently as "Hermitian projection;
loses directional information" in the `qm_4d` docstring.

### 3.2 v1.5 stub: η-metric framework (zero LOC marginal cost)

Define the *interface* for η-metric pawn observables, but raise
`NotImplementedError` on access in v1.5:

```python
# Module attributes; raise NotImplementedError on access in v1.5.
H_pawn_w_4   # raises NotImplementedError("v1.6+ candidate; see ADR-005")
H_pawn_y_4   # same
eta_pawn_w_4 # same — the η operator itself
eta_pawn_y_4 # same
inner_product_eta(a, b, eta)          # raises in v1.5; reserved name
expectation_eta(O, psi, eta)          # same
is_pseudo_hermitian(O, eta, tol=1e-10) # same
```

These names are reserved in the public API surface so that v1.6 can
promote them to functional implementations without breaking consumers.
LOC cost: ~30 (one stub raising `NotImplementedError` per name).

### 3.3 The η operator design (documented for v1.6+)

When v1.6 implements the η-metric, the η operator is constructed as
follows (this is the design captured here; implementation deferred):

#### 3.3.1 η for W-axis pawns

The white pawn pushes `+w`, captures diagonally `(+w, ±x, ±y, ±z)`.
The black pawn pushes `-w`, captures `(-w, ±x, ±y, ±z)`. The lifted
matrices satisfy:

```
M_pawn_w_white^T = M_pawn_w_black     (push directions reverse)
M_pawn_w_black^T = M_pawn_w_white     (same)
```

So `M_pawn_w_black = M_pawn_w_white^T`. Define:

```
M_pawn_w := M_pawn_w_white + M_pawn_w_black = M_pawn_w_white + M_pawn_w_white^T
```

This is the symmetric part — i.e., exactly `H_pawn_w_4_herm` from §3.1.

For the **antisymmetric / directed** part:

```
A_pawn_w := M_pawn_w_white - M_pawn_w_black = M_pawn_w_white - M_pawn_w_white^T
```

`A_pawn_w` is real anti-symmetric. The full white-pawn operator is
`M_pawn_w_white = (1/2) * (M_pawn_w + A_pawn_w)`.

The η operator that makes `M_pawn_w_white` pseudo-Hermitian is:

```
η_pawn_w := P_w
```

where `P_w` is the W-axis parity flip (the involution `s ↦ s'` with
`w' = 7 − w` and other coords unchanged). This is a 4096×4096
permutation matrix; it commutes with all non-W-axis B_4 elements but
anti-commutes with W-axis sign-flips.

**Verification:**
- `P_w * M_pawn_w_white * P_w^{-1}`: applying P_w to source (sw') and
  P_w to target (sw') of `M_pawn_w_white` permutes the rows and
  columns. The white pawn pushes `+w`; under P_w, `(sw, sw+1)` maps to
  `(7-sw, 7-(sw+1)) = (7-sw, 6-sw)`, which is a `-w` push. So
  `P_w * M_pawn_w_white * P_w^{-1} = M_pawn_w_black = M_pawn_w_white^T`.
- Therefore `M_pawn_w_white^T = P_w * M_pawn_w_white * P_w^{-1}`, which
  is the **pseudo-Hermiticity condition** with η = P_w (since `P_w` is
  Hermitian — it's a permutation matrix and self-inverse, hence
  symmetric).

So `M_pawn_w_white` is **P_w-pseudo-Hermitian**.

**PT-symmetry interpretation:** P_w is parity (axis flip); the time-reversal
T can be identified with the color-flip. PT = P_w * color_flip is then
the involution that takes white-pushing pawns to black-pushing pawns
*and* flips colors. The composition PT commutes with `M_pawn_w_white`
(verifiable closed-form), so `M_pawn_w_white` is **PT-symmetric** in
Bender's sense.

#### 3.3.2 η for Y-axis pawns

By symmetry with the W-axis case: η_pawn_y = P_y (Y-axis parity flip).
Same construction; same verification.

#### 3.3.3 Composite η for combined-axis pawn observables

If consumers want to evaluate "expected pawn presence regardless of axis"
as a single operator, the combined `M_pawn = M_pawn_w + M_pawn_y` is
pseudo-Hermitian under η = P_w * P_y (composed parity flips). Documented
for v1.6+ but not needed for v1.5.

### 3.4 Spectrum-realness check (v1.6 requirement)

Per Bender-Boettcher, the PT-symmetric operator has real spectrum **iff
the PT phase is unbroken**: every eigenvector is also a PT eigenvector.
For the lifted pawn operators, we must verify this empirically:

- Compute the spectrum of `M_pawn_w_white` numerically (4096×4096 dense
  eigendecomposition; ~30 seconds).
- Verify all eigenvalues have `|Im(λ)| < tol`. If yes: PT phase
  unbroken; the η-metric machinery is meaningful.
- If PT phase is broken (some eigenvalues complex): η-metric does not
  produce real expectation values. Document and either (a) project to
  PT-unbroken subspace, or (b) ship Hermitian-part projection only.

**Pre-implementation probe for Phase 3:** Run the spectrum check on
`M_pawn_w_white`; record the result. This is a 30-LOC closed-form check
that *must* run before v1.6 promotion.

If the probe finds PT phase broken, v1.6's design is reduced — possibly
the η-metric is shipped only as a research artifact, with the
Hermitian-projection observables remaining the primary v1.6 deliverable.

### 3.5 v1.5 vs. v1.6 contract

For v1.5.0:
- `getQmExpectation('pawn_w_herm', ψ)` returns `<ψ|H_pawn_w_4_herm|ψ>` —
  a real number computed via the standard inner product. Available.
- `getQmExpectation('pawn_w', ψ)` raises NotImplementedError with a
  pointer to ADR-005 §3.5 (this section). Reserved for v1.6.
- `getQmExpectation('pawn_y_herm', ψ)` available; `pawn_y` reserved.

For v1.6+:
- `getQmExpectation('pawn_w', ψ)` returns `<ψ|H_pawn_w_4|ψ>_η` —
  computed via the η-inner-product, real iff PT phase is unbroken.
- The η operator is exposed as `eta_pawn_w_4` for direct manipulation
  by advanced consumers.

The bridge contract changes are minimal: the same observable name keys,
extended with `_herm` suffix for v1.5; the suffix-less names go live in
v1.6.

---

## 4. Consequences

### 4.1 What this enables

- **Pawn observables ship in v1.5.** The Phase 6 QM evaluator can
  compute pawn contributions via `H_pawn_<axis>_4_herm`. Not strictly
  faithful to the directed-push structure, but captures the symmetric
  pawn skeleton — sufficient for evaluator strength comparisons.
- **API forward-compatibility.** v1.6 promotes the suffix-less names to
  full implementations without breaking v1.5 consumers.
- **Phase 3 prototype probe is well-defined.** §3.4's PT-realness check
  is closed-form; can be run in 30 LOC + ~1 minute of compute.
- **Reviewers see a clean handoff.** "Pawn observable ships as Hermitian
  projection in v1.5; full PT-symmetric construction documented in
  ADR-005 and slated for v1.6 contingent on PT phase verification" is
  a publishable scope.

### 4.2 What this forecloses

- **No first-class directed-push QM dynamics in v1.5.** The
  `M_pawn_white` matrix as written is NOT used in v1.5 — only its
  symmetric part. Consumers who need to distinguish "white pushes
  forward" from "black pushes forward" at the QM level wait for v1.6.
- **No direct coupling between ADR-001's pawn-channel phases and ADR-005's
  pawn observable.** ADR-001 §3.1 sets `theta_8 = (pi/2) * sgn(w'-w)` for
  W-axis push direction. This is a phase encoding of direction. ADR-005's
  v1.5 H_pawn_*_herm doesn't use direction. So a consumer asking "does
  the QM evaluator's pawn observable see the same direction as the
  applyMoveQm phase?" — the answer in v1.5 is *no*; in v1.6+ with full
  η-metric, *yes*.
- **Open thread for §16.5 ablation.** Notebook §16.5 explicitly asks
  "if the pseudo-Hermitian pawn observables (Track B) matter, that
  validates the η-metric machinery." With v1.5 shipping only Hermitian
  projection, this ablation question is *deferred* — Phase 6's tournament
  measures `pawn_w_herm` contribution, not the genuine pseudo-Hermitian
  observable. The ablation as written in §16.5 isn't fully runnable until
  v1.6.

### 4.3 LOC implications

**v1.5 LOC budget:**
- `H_pawn_w_4_herm` lazy attribute: ~30 LOC (build symmetric part of
  M_pawn_white from `_t4.piece_adjacencies_4d` lifted with directionality
  helpers; symmetrize; cache).
- `H_pawn_y_4_herm` lazy attribute: ~30 LOC (same with Y axis).
- Stubs for the full η-metric API: ~30 LOC (NotImplementedError stubs).
- Module-level docstring update: ~30 LOC.

Total v1.5 LOC: ~120.

**v1.6 LOC budget (when promoted):**
- η_pawn_w / η_pawn_y construction: ~100 LOC.
- η-inner-product machinery: ~100 LOC.
- Spectrum-realness verification: ~80 LOC.
- `H_pawn_w_4` / `H_pawn_y_4` (full) lazy attributes: ~80 LOC each.
- Tests: ~200 LOC.

Total v1.6 LOC: ~640.

### 4.4 Test surface

**v1.5 tests:**
- `H_pawn_w_4_herm` is real-symmetric Hermitian: ~30 LOC.
- Spectrum is real for `H_pawn_w_4_herm`: ~30 LOC.
- `H_pawn_w_4_herm` commutes with `J_op`: ~30 LOC (test that this is
  the case; expected to pass per the symmetric-projection argument).
- `H_pawn_y_4_herm` analogous: ~30 LOC each = ~60 LOC total.
- NotImplementedError stubs raise correctly: ~30 LOC.

Total v1.5 test LOC: ~150.

**v1.6 tests (when promoted):**
- η_pawn_<axis> is Hermitian and unitary: ~30 LOC each.
- Pseudo-Hermiticity: `M_pawn_w^T = η_pawn_w * M_pawn_w * η_pawn_w^{-1}`:
  ~30 LOC each.
- PT-realness of spectrum: ~50 LOC.
- η-inner-product produces real expectation values for pseudo-Hermitian
  operators: ~50 LOC.
- Full vs. Hermitian-part projection comparison: ~50 LOC.

Total v1.6 test LOC: ~210.

---

## 5. Alternatives Considered

### 5.1 Option α: Full pseudo-Hermitian / PT-symmetric pawn observables in v1.5

**Rejected.** The proposal: implement the full η-metric machinery in
v1.5.0; ship `H_pawn_w_4` and `H_pawn_y_4` as the genuine pseudo-Hermitian
operators.

- **LOC budget violation.** ~640 LOC for full pseudo-Hermitian work
  exceeds Track B's available budget after ADR-001/002/003/004 take
  ~1980 LOC. Total Track B budget is ~2000 LOC; this option pushes to
  ~2620 LOC. Risk: shipping nothing.
- **PT-realness untested.** The PT phase being unbroken is a *condition*
  to verify. Without the v1.5 Phase 3 probe in §3.4, we don't know if
  the η-metric produces real expectation values. Building infrastructure
  on an unverified condition is fragile.
- **Bridge contract uncertainty.** §17.1 didn't pre-decide whether
  `getQmExpectation` should use η-modified inner products. Locking this
  in v1.5 without consumer testing is premature.

### 5.2 Option β: No pawn observables in v1.5

**Rejected.** The proposal: raise NotImplementedError on all pawn-related
queries in v1.5; punt the entire pawn machinery to v1.6.

- **Breaks Phase 6 evaluator.** Pawns are 8-of-16 starting pieces in
  chess. A QM evaluator that ignores pawns is dramatically incomplete.
  The §16.5 tournament results would be uninterpretable.
- **Wastes Pre-flight 2's groundwork.** Pre-flight 2 already mapped out
  the pseudo-Hermitian / PT structure for pawns. v1.5 having "we know
  but didn't ship" status is anticlimactic.
- **Cleaner is to ship what's shippable.** Hermitian projection is
  technically clean (real-symmetric → Hermitian under η = I), well-defined,
  and produces real expectation values. It's the natural v1.5 deliverable.

### 5.3 Option γ: Ship the directed M_pawn_white as a non-Hermitian operator in v1.5

**Rejected.** The proposal: expose `M_pawn_w_white` directly; let
consumers interpret `<ψ|M_pawn_w_white|ψ>` as a complex number.

- **Bridge contract violation.** §17.1's `getQmExpectation` returns
  `{ ok, value }` where `value` is a real number. A complex-valued
  observable doesn't fit the contract.
- **Confusing semantics.** What does `Im(<ψ|M_pawn_w_white|ψ>)` *mean*
  in a chess context? Without the η-metric machinery to interpret it,
  the imaginary part is just numerical noise from the directed asymmetry.
- **PT-symmetry framework was developed precisely for this.** Bender's
  insight is that directed-flow operators *are* meaningful under the
  η-modified inner product. Ignoring that framework leaves complex
  expectation values uninterpretable.

### 5.4 Option δ: Hermitian projection in v1.5 + η-metric stubs (CHOSEN)

This is the chosen Option D, described in §3 above. The two-tier delivery
balances:
- **Shipping in v1.5:** Hermitian projection is clean, fast, and
  semantically meaningful (loss of direction information is documented).
- **Forward compatibility:** η-metric stubs reserve the API names so v1.6
  can promote without API break.
- **Empirical validation pathway:** The §3.4 Phase 3 probe verifies PT
  realness *before* v1.6 commitment, avoiding the Option α risk.

### 5.5 Sub-decision: which η operator to use

Within Option δ, the choice of η is constrained by the directed-push
structure. The §3.3 derivation `η = P_w` (axis parity flip) is **the
unique** η-operator candidate that:
- Is invertible Hermitian (P_w is a permutation, hence orthogonal, hence
  unitary, hence Hermitian since P_w^2 = I).
- Satisfies the pseudo-Hermiticity condition `M^T = η * M * η^{-1}`
  (verified by the closed-form argument in §3.3.1).
- Has a clean physical interpretation (axis parity ↔ "flip the pawn's
  push direction").

Any other η candidate (e.g., a less symmetric operator) would either
fail to satisfy pseudo-Hermiticity or lack physical interpretability.
P_w is the natural choice.

---

## 6. Open Questions / Future Work

1. **Phase 3 PT-realness probe.** Run the §3.4 spectrum check on
   `M_pawn_w_white` and `M_pawn_y_white` before Track B implementation
   begins. If PT phase is broken (some complex eigenvalues), v1.6's
   design must adapt — likely projecting to the PT-unbroken subspace.

2. **v1.6 promotion criteria.** v1.6 ships full η-metric pawn observables
   if and only if:
   - PT-realness probe passes (real spectrum within tol).
   - Phase 6 tournament results indicate `pawn_w_herm` is signal-bearing
     (consumers actually use it; not zero contribution).
   - LOC budget is available (Track B post-v1.5 has slack).

3. **Multi-axis pawn observables.** If consumers need a unified "all
   pawns regardless of axis" observable, the §3.3.3 composite η = P_w * P_y
   construction handles it. Defer to v1.6+ unless explicitly requested.

4. **Bridge contract clarification.** §17.1 should be amended in the
   v1.5.0 release notes: `getQmExpectation` for pawn observables in
   v1.5 uses the standard inner product (because `_herm` observables are
   actually-Hermitian); v1.6 will introduce η-modified inner product for
   the suffix-less names. Document the migration path.

5. **Castling and en-passant.** These are also asymmetric chess operations.
   Castling is direction-symmetric (kingside / queenside); en-passant is
   direction-asymmetric (only on opposite-color last-move push). They
   may admit similar pseudo-Hermitian treatment but are out of scope for
   ADR-005. Punt to a future ADR (ADR-006 candidate?) if needed.

---

## 7. References

- **Pre-flight 2** ([phase_operators_4d_pseudo_hermitian_audit.md](../../../python/research/phase_operators_4d_pseudo_hermitian_audit.md)) — establishes the directed-pawn / Hermiticity-breaking finding; §3, §6.2 of that audit pre-suggest the η = P_w construction in this ADR.
- **Notebook §15.2(4)** ([chess_spectral_research_notebook.md, sec 15.2](../../../../chess_spectral_research_notebook.md#152-the-enabling-machinery)) — "qm_4d module's pseudo-Hermitian / PT-symmetric machinery earns its keep" framing for the η-metric.
- **Notebook §16.5** ([chess_spectral_research_notebook.md, sec 16.5](../../../../chess_spectral_research_notebook.md#165-what-we-expect-to-learn)) — "if the pseudo-Hermitian pawn observables (Track B) matter, that validates the η-metric machinery beyond aesthetic rigor" — the empirical validation pathway.
- **Notebook §17.1** ([chess_spectral_research_notebook.md, sec 17.1](../../../../chess_spectral_research_notebook.md#171-chess-spectral-15--qm-extension-bridge-surface)) — `getQmExpectation` bridge contract this ADR amends.
- **Track A `qm_4d.build_H_piece_4`** ([qm_4d.py:331-390](../../../python/chess_spectral/qm_4d.py#L331-L390)) — the existing `NotImplementedError` raised for pawns; v1.5 replaces this with the `_herm` variants.
- **Encoder pawn channels** ([encoder_4d.py:387-430](../../../python/chess_spectral/encoder_4d.py#L387-L430)) — channels 8-9 (FA_PAWN_W, FA_PAWN_Y) are encoder-side counterparts; ADR-001 §3.1 set their phase conventions.
- **ADR-001** — phase convention for pawn channels (theta_8, theta_9 use
  direction sign); cross-cuts with v1.6's η-metric in motivating
  direction-sensitive observables.
- **ADR-003** — per-channel `U_move` for FA_PAWN_W/Y; ADR-005's pawn
  observables use the same channel structure.
- **ADR-004** — Z_2 superselection; v1.5's `_herm` observables commute
  with `J_op` per the §3.3 argument.
- **Bender, C. M. and Boettcher, S.** *"Real Spectra in Non-Hermitian
  Hamiltonians Having PT Symmetry," Phys. Rev. Lett. 80, 5243 (1998).*
  Foundational PT-symmetry paper; underwrites the v1.6 η = P_w
  construction.
- **Mostafazadeh, A.** *"Pseudo-Hermiticity versus PT Symmetry,"
  J. Math. Phys. 43, 205 (2002).* Equivalence between PT-symmetry and
  η-pseudo-Hermiticity; underwrites the η-inner-product machinery.
- **Mostafazadeh, A.** *"Pseudo-Hermitian Representation of Quantum
  Mechanics," Int. J. Geom. Methods Mod. Phys. 7, 1191 (2010).* Review
  article for the v1.6 implementation reference.
- **Bender, C. M.** *"Making Sense of Non-Hermitian Hamiltonians,"
  Rep. Prog. Phys. 70, 947 (2007).* Review article for the v1.6
  implementation reference.

---

## 8. Phase 4 Implementation Pointer

**This is the design we will implement in Phase 4 B[5] (pawn observables,
v1.5 tier).** Roll-out:

1. **Phase 4 B[5a]:** Build `H_pawn_w_4_herm` and `H_pawn_y_4_herm` as
   symmetric-projection lifts of the directed pawn predicates.
   ~60 LOC. Test surface ~80 LOC.
2. **Phase 4 B[5b]:** Add NotImplementedError stubs for the suffix-less
   names + `eta_pawn_*` + `inner_product_eta` + `expectation_eta`. ~30 LOC.
3. **Phase 4 B[5c]:** Update `qm_4d` module docstring with the v1.5/v1.6
   contract per §3.5; cross-reference ADR-005. ~30 LOC.
4. **Phase 4 B[5d]:** Update notebook §16.5 ablation question
   parameterization to reference `pawn_<axis>_herm` observables for v1.5.

Acceptance for v1.5.0 ship:
- §4.4 v1.5 test surface passes.
- Phase 3 PT-realness probe is run (deferring v1.6 promotion is
  conditional on its results).
- Tournament ablation in Phase 6 reports `pawn_w_herm` and `pawn_y_herm`
  as separate observables; documented as Hermitian projections.

**Phase 4 B[5e] (optional, deferred to v1.6):** Promote the stubs to
full implementations following the §3.3 design, contingent on Phase 3
PT-realness probe passing.

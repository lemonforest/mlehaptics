# Claude Code: Chess Notebook Phase 1c Propagation Patches

## Status (2026-04-27)

**PARTIAL APPLICATION.** Patch 2's *coprimality is necessary but not
sufficient* discipline was lifted into the chess-maths research
record at
[`chess-maths/PHASE_OPERATOR_SUPPLEMENT_4D.md`](../chess-maths/PHASE_OPERATOR_SUPPLEMENT_4D.md)
§13.1.4 (the Phase B refinement story) and §13.8 (cross-pollination
credits) during the 4D phase-operator landing in
[`chess-spectral/4d-phase-operators` PR #67](https://github.com/lemonforest/mlehaptics/pull/67).
The 4-tuple Diophantine extension (the 4D analogue of the (3, 7) mod
1024 counter-example below) is now codified as constraint **C5** in
[`tests/test_phase_4d_design.py::test_c5_no_integer_dependency_in_minus14_to_14_box`](../chess-maths/chess-spectral/python/tests/test_phase_4d_design.py).

**Still pending propagation into the 2D notebook**
([`chess-maths/chess_spectral_research_notebook.md`](../chess-maths/chess_spectral_research_notebook.md)):
Patches 1, 3, 4, 5, 6 — the §10.4 grid-topology theorem upgrade,
§9f coprimality clarification (the textual edit, not the
discipline), the §10.13 reversi-scripts addendum, and the audit
items on §10.10 / §11.5. Tracking: open a follow-up PR titled
`docs/2D-notebook: apply CHESS_NOTEBOOK_PHASE_1C_PATCHES propagations`
once the 4D phase-operator PR lands.

## Context

The Othello verification pass has yielded findings that propagate back to the chess notebook — some as structural theorems that strengthen existing §10 claims, some as new empirical results from Phase 1c that postdate the current `chess_spectral_research_notebook.md` update, and one as a first-principles audit item that may reveal a latent bug.

This prompt has five patches plus one audit item. Apply the patches in order. The audit item (Patch 6) may or may not produce a code change depending on its outcome — follow the instructions in that section.

Every numerical claim in the patches below has been verified from first principles in the Othello session before being proposed here. The verification is stated inline in the rationale blocks so that the patches can be audited independently by another Claude instance.

---

## PATCH 1 — §10.4 upgrade: B₁/B₂ Frobenius-orthogonality is a grid-topology theorem

**Rationale:** The updated §10.4 currently states the Frobenius-orthogonality of L_{B₁} and L_{B₂} as a "stronger distinctness statement than the original prediction required" — framed as an empirical surprise. But the result follows directly from the disjoint support of the orthogonal-edge and diagonal-edge sets on the 8×8 grid, which makes it a theorem, not just a measured coincidence.

**First-principles verification.** Let `E_ortho` denote the set of grid edges between orthogonal (rook-direction) neighbors and `E_diag` the set of grid edges between diagonal (bishop-direction) neighbors. Any cell pair `(c₁, c₂)` is either an orthogonal neighbor (displacement `(±1, 0)` or `(0, ±1)`), a diagonal neighbor (displacement `(±1, ±1)`), or neither — never both. Hence `E_ortho ∩ E_diag = ∅`. Each undirected ray Laplacian `L_N, L_E, L_S, L_W` has nonzero matrix entries only at positions indexed by `E_ortho`; each of `L_NE, L_SE, L_SW, L_NW` has nonzero entries only at positions indexed by `E_diag`. Any real linear combination of the first group has matrix support ⊆ `E_ortho`; any combination of the second has support ⊆ `E_diag`. Frobenius inner product is a sum of entrywise products over positions; if the supports are disjoint, every entrywise product is zero. Hence `⟨L_{B₁}, L_{B₂}⟩_F = 0` is a theorem of the grid's edge topology. Confirmed computationally: on 8×8, `|E_ortho| = 112`, `|E_diag| = 98`, `|E_ortho ∩ E_diag| = 0` exactly.

OLD:
```
**B₁↔B₂ is the rook/bishop signature, derived from rays alone.** In the chess notebook, the orthogonal-sliding vs diagonal-sliding distinction appears through piece-species analysis (rook adjacency vs bishop adjacency). Here, the same distinction drops out of the ray-set character analysis with no reference to pieces. B₁ carries the orthogonal-orbit anisotropic mode; B₂ carries the diagonal-orbit anisotropic mode. Interchanging orthogonal and diagonal rays — a group-theoretic B₁↔B₂ swap — is the exact signature of the rook/bishop distinction. To this survey's knowledge, this decomposition has not been previously published for Othello. **CONFIRMED 2026-04-22** by character-projection on the 8-dim ray-indicator space: measured multiplicities exactly match `{A₁: 2, A₂: 0, B₁: 1, B₂: 1, E: 2}`; the B₁ and B₂ modes lifted to 64×64 operators land Frobenius-orthogonal (inner product exactly 0), which is a stronger distinctness statement than the original prediction required. See `othello-maths/research/consolidated_tests.py` (H2, H3).
```

NEW:
```
**B₁↔B₂ is the rook/bishop signature, derived from rays alone.** In the chess notebook, the orthogonal-sliding vs diagonal-sliding distinction appears through piece-species analysis (rook adjacency vs bishop adjacency). Here, the same distinction drops out of the ray-set character analysis with no reference to pieces. B₁ carries the orthogonal-orbit anisotropic mode; B₂ carries the diagonal-orbit anisotropic mode. Interchanging orthogonal and diagonal rays — a group-theoretic B₁↔B₂ swap — is the exact signature of the rook/bishop distinction. To this survey's knowledge, this decomposition has not been previously published for Othello. **CONFIRMED 2026-04-22** by character-projection on the 8-dim ray-indicator space: measured multiplicities exactly match `{A₁: 2, A₂: 0, B₁: 1, B₂: 1, E: 2}`; the B₁ and B₂ modes lifted to 64×64 operators land Frobenius-orthogonal (inner product exactly 0). See `othello-maths/research/consolidated_tests.py` (H2, H3).

**The Frobenius-orthogonality is a grid-topology theorem, not an empirical coincidence.** On the 8×8 grid, the orthogonal-neighbor edge set `E_ortho` (112 edges, displacements `(±1, 0)` and `(0, ±1)`) and the diagonal-neighbor edge set `E_diag` (98 edges, displacements `(±1, ±1)`) are disjoint: no cell pair is simultaneously an orthogonal and diagonal neighbor. Each undirected orthogonal ray Laplacian has matrix support ⊆ `E_ortho`; each diagonal ray Laplacian has support ⊆ `E_diag`. Any real linear combination in one orbit therefore has Frobenius inner product identically zero with any combination in the other orbit, independent of the coefficients. The B₁ and B₂ spectral channels are not merely distinct — they live on disjoint subsets of matrix position-space, so the rook/bishop decomposition is a *direct sum* of operator subspaces, not an orthogonal splitting of a shared space. The same theorem applies to chess: the rook adjacency and bishop adjacency have disjoint edge supports, which is why rook+bishop=queen holds exactly at the adjacency-matrix level (§3, §7b). Othello makes the ray-level structure explicit; chess inherits it via piece species.
```

---

## PATCH 2 — §9f clarification: coprimality is necessary but not sufficient

**Rationale:** §9f currently states that 67 and 7 are coprime to 512 and that "All 64 roll offsets are verified distinct." A reader can interpret the second statement as consequence of the first, but it isn't — 64-phase uniqueness is a strictly stronger condition. The Othello work surfaced a concrete counter-example: `(p, q) = (3, 7)` mod 1024, where both generators are coprime to 1024 but `φ(7, 0) = φ(0, 3) = 21`. The Diophantine `p·Δr + q·Δc ≡ 0 (mod D)` must have no nonzero solution with `|Δr|, |Δc| ≤ 7`. Making this distinction explicit here prevents the mistake when generators are chosen for other moduli (Othello's D=768, D=1024, D=1152 cases, plus any future domain).

**First-principles verification.** For generators `(p, q)` and modulus `D`, the phase map `φ(r, c) = (p·r + q·c) mod D` is injective on `[0, 7]² ⊂ ℤ² ` if and only if `p·Δr + q·Δc ≢ 0 (mod D)` for every `(Δr, Δc) ∈ [-7, 7]² \ {(0, 0)}`. Each generator being coprime to `D` prevents only the degenerate failures `Δr = 0, Δc ≠ 0` and `Δr ≠ 0, Δc = 0`. Mixed-sign combinations can still collide. Verified: `(3, 7)` mod 1024 produces 5 collision pairs on 8×8; `(67, 7)` mod 640 (chess) produces 0; `(7, 11)` mod 768 (Othello recommended) produces 0.

OLD:
```
### 9f. Coprime Roll Binding (UTLP S3 → Spatial HDC)

The key architectural connection to UTLP S3: binding is **coprime cyclic roll**, not element-wise multiply.

`bound = np.roll(piece_vec, row * 67 + col * 7 mod 512)`

- 67 and 7 are coprime to 512 (both odd, 512 = 2⁹)
- All 64 roll offsets are verified distinct
- Adjacent squares differ by one coprime stride (67 for vertical, 7 for horizontal)
- Roll is exactly self-inverse: `roll(roll(x, n), -n) = x`
- No bipolar requirement — works with any vector
```

NEW:
```
### 9f. Coprime Roll Binding (UTLP S3 → Spatial HDC)

The key architectural connection to UTLP S3: binding is **coprime cyclic roll**, not element-wise multiply.

`bound = np.roll(piece_vec, row * 67 + col * 7 mod 512)`

- 67 and 7 are coprime to 512 (both odd, 512 = 2⁹)
- All 64 roll offsets are verified distinct
- Adjacent squares differ by one coprime stride (67 for vertical, 7 for horizontal)
- Roll is exactly self-inverse: `roll(roll(x, n), -n) = x`
- No bipolar requirement — works with any vector

**Generator-selection requirement (subtlety discovered by the Othello Phase 1 pass).** Coprimality of each generator with the modulus `D` is necessary but *not* sufficient for 64-phase uniqueness on the 8×8 lattice. The complete condition is that `p · Δr + q · Δc ≢ 0 (mod D)` holds for every nonzero `(Δr, Δc) ∈ [-7, 7]²`. The individual-coprimality condition prevents collisions along the axes only; mixed-sign Diophantine collisions can still occur. Concrete counter-example from the Othello work: `(p, q) = (3, 7)` with `D = 1024` has `gcd(3, 1024) = gcd(7, 1024) = 1`, but `φ(7, 0) = 21 = φ(0, 3)` because `7·3 − 3·7 = 0`. The chess choice `(67, 7)` with `D = 512` and `D = 640` both pass 64-phase uniqueness verification; the "verified distinct" clause above is doing the real work, and coprimality is an insufficient shortcut. For any new modulus `D` (other domains, other dimensions), the correct check is exhaustive verification of 8×8 phase uniqueness, not pairwise `gcd`.
```

---

## PATCH 3 — Add §10.13 Phase 1c addendum

**Rationale:** The Othello session produced a Phase 1c run after the current notebook's §10.12 was finalized. Three results are worth propagating:

1. The OthelloBoard implementation was cross-validated against Takizawa's reference implementation at 2684/2684 agreement. Every downstream claim is now built on a validated engine. Worth stating explicitly.
2. §10.10 test 3 (Shannon information per move) has been partially run and yielded a *conditional* result: globally null, in-book-only significant at ρ = +0.213, p = 2×10⁻⁸ on N ≈ 676. This is a novel structural finding with no direct chess analog.
3. A preliminary edax 50-empty anchor at N = 15 gave ρ = +0.820, p = 1.8×10⁻⁴, below the 20-match threshold for reporting as a result but flagged as a watch item. A 2148-position edax run is currently in flight (multi-hour).

The patch also adds a framework-level observation: the Phase 1c data separates "information as state-richness" (tracks legal-move count, null with winning margin) from "spectrum as strategic structure" (tracks disc density and conditionally tracks move information). These are different axes, and calling them out explicitly is a reusable framework lesson.

**Location:** insert this new subsection immediately after §10.12, before the "Open questions" close-out if one exists, and before §11.

NEW (insert after §10.12):
```
### 10.13. Phase 1c addendum — reversi-scripts integration (2026-04-22)

Run after §10.12 had been finalized. Integrates the GPL-v3 [`eukaryo/reversi-scripts`](https://github.com/eukaryo/reversi-scripts) artefacts that can be used **without** the 20 GB figshare perfect-play table. Full numerics in [`../othello-maths/results/phase1c_*.json`](../othello-maths/results/) and [`../othello-maths/results/session_summary.md`](../othello-maths/results/session_summary.md).

**1c.1 — OthelloBoard engine cross-validation (CONFIRMED).** 2684 positions (2184 from the Barcelona EGP 2026 PGN + 500 synthetic random-play positions) evaluated against Takizawa's vendored `reversi_misc.py::get_moves`. **2684/2684 agreement, zero disagreements.** Every downstream claim in §10.12 / §10.13 inherits this confidence; positions with divergent move sets between Claude's implementation and the reference would have invalidated every correlation in the Othello trajectory work. They don't.

**1c.2 — §10.10 T3 Shannon information per move (CONFIRMED — conditional).** Using the `opening_book_freq.csv.bz2` from reversi-scripts as the empirical P(chosen) dictionary, `I_move = log₂|M(s)| − log₂ P̂(chosen | book)` was computed for 2099 scored plies across 35 tournament games. 32% of plies were in-book (coverage determined by the book's truncation depth).

| Observable | Correlation | p-value | N |
|---|---|---|---|
| I_move vs n_legal_moves (global) | +0.814 | ~0 | 2099 |
| I_move vs A₁⁻ energy (global) | −0.065 | 0.003 | 2099 |
| I_move vs A₁⁻ energy (in-book only) | **+0.213** | **2.1 × 10⁻⁸** | ~676 |
| game-mean I_move vs \|final disc diff\| | +0.109 | 0.53 | 35 |

The global I_move-vs-A₁⁻ correlation is noise (effect size near zero). Out of book, `P̂(chosen | book)` is Laplace-smoothed to uniform-noise baseline, so I_move collapses to `log₂|M(s)|` plus additive noise, which is why the global Spearman is dominated by the `+0.814` legal-move-count correlation. **In-book, where `P̂(chosen | book)` is an informative tournament-frequency distribution, I_move picks up a strategic-weight component, and that component partially aligns with A₁⁻ magnetisation energy at ρ = +0.21.** This is a conditional effect, not a marginal one, and the conditioning variable (in-book / out-of-book) is the structural lever.

The null result at the game level — mean I_move does not predict winning margin (ρ = +0.11, p = 0.53) — distinguishes I_move as a *state-richness* observable rather than a *quality* observable. The spectral channel A₁⁻ (which does partially track disc density at ρ = +0.77 on the same corpus; §10.12 E3 scale-up) carries a different signal. Naming the split explicitly: **Shannon information per move measures state richness (how many options, how evenly distributed); A₁⁻ energy measures strategic structure (how the magnetisation is arranged under the group action).** The two are independent axes of a position description. This is a reusable framework distinction; when the same question is asked of chess (what fraction of I_move-vs-spectral-observable covariance is opening-book-conditional?) the answer may differ because chess's opening-book structure is different, but the conditional framing transfers.

No chess analog for the in-book conditional effect has been measured. Chess §9h′ measures A₁ energy vs Stockfish depth-gap, which is a different observable pairing. Adding a matching in-book I_move experiment to chess is scoped as a §9s follow-up if of interest.

**1c.3 — Edax 50-empty knowledge anchor (PARTIAL, flagged).** 15 of 35 Barcelona 50-empty positions match entries in reversi-scripts' 2587-row `empty50_tasklist_edax_knowledge.csv`. At the default reporting threshold of 20 matches the correlation is suppressed as a result; a peek at N = 15 gives Spearman(A₁⁻ energy, edax_score) = **+0.820, p = 1.8 × 10⁻⁴**. The effect size is the largest in the session. N = 15 is too small to commit to — this is a flag, not a result. A 2148-position edax run at depth 1 vs depth 20 is currently in flight; its result will either vindicate or kill this reading.

**1c.4 — H9 A₁ depth-gap runner scoped (READY).** `research/edax_wrapper.py` + `research/a1_depth_gap_runner.py` land with full OBF-position feeding, depth-1 vs depth-20 gap computation, and partial correlation controlling for `|disc_diff|`. This is the surrogate H9 protocol that uses edax-depth-gap in place of Takizawa perfect-play, mirroring chess §9h′'s use of Stockfish-depth-gap rather than perfect-play. Expected wall time: 1–6 hours at d=20 on the full 2184-position Barcelona corpus. Not yet executed; its result replaces the §10.12 H9 UNDETERMINED status.

**What this does not change.** The §10.12 pass-table is unaffected — H9 and E8 remain UNDETERMINED at the strict (Takizawa-figshare) reading; their surrogate (edax depth-gap) is now runnable and is in flight. The §10.10 T4 (T_eff / D_eff trajectory) and T5 (FK-BC cluster fit) are still scoped to a subsequent pass. Predictive-validation of the Phase 2 sheaf spectrum (following the logo L7b template) is still scoped to the sequel.

**Framework-level observation to carry forward.** The Shannon-information / spectral-observable conditional split is the most novel structural result of the Othello Phase 1c pass. It suggests that position description in the spectral VSA has at least two functionally independent axes — an information-content axis (state richness, tracks |M(s)|, null with outcome) and a spectral-structure axis (strategic configuration, tracks magnetisation arrangement under D₄×Z₂, partially correlates with quality). Whether these two axes also separate cleanly in chess is an open question worth running, especially because chess has a more developed opening-book theory and the in-book / out-of-book regime switch is sharper.
```

---

## PATCH 4 — §10.10 item 3 annotation upgrade

**Rationale:** §10.10 item 3 currently says `opening_book_freq.csv.bz2` makes T3 runnable without the 20 GB download and scopes it to the sequel. T3 has now been partially run. Update the annotation.

OLD:
```
3. **Shannon information per move** vs the Sagawa-Ueda bound ⟨W⟩ ≥ ΔF − k_B T · I. Without the Boltzmann-policy embedding, test the pure Shannon bookkeeping: I_move = log₂ |M(s)| − log₂ P(chosen | policy). Under the embedding with inferred β, test the full generalized-Jarzynski identity. **The `opening_book_freq.csv.bz2` file in the Takizawa reversi-scripts repo provides the empirical P(chosen) dictionary directly** — T3 is runnable without the 20 GB figshare download, scoped to the sequel.
```

NEW:
```
3. **Shannon information per move** vs the Sagawa-Ueda bound ⟨W⟩ ≥ ΔF − k_B T · I. Without the Boltzmann-policy embedding, test the pure Shannon bookkeeping: I_move = log₂ |M(s)| − log₂ P(chosen | policy). Under the embedding with inferred β, test the full generalized-Jarzynski identity. **The `opening_book_freq.csv.bz2` file in the Takizawa reversi-scripts repo provides the empirical P(chosen) dictionary directly** — T3 is runnable without the 20 GB figshare download. **Status: CONFIRMED as a conditional effect (2026-04-22)** — I_move is near-null with A₁⁻ energy globally (ρ = −0.065) but picks up a significant positive correlation on the in-book subset (ρ = +0.213, p = 2 × 10⁻⁸ on N ≈ 676 of 2099 scored plies across 35 Barcelona EGP 2026 games). The in-book / out-of-book conditioning is the structural lever; see §10.13. The generalized-Jarzynski version under the embedding remains open.
```

---

## PATCH 5 — §10.12 sheaf observation: tighten the state-richness framing

**Rationale:** The Phase 1c work makes explicit that the Phase 2 sheaf finding (Spearman(legal_moves, λ₂) = +0.77) belongs to the same "state-richness" axis as the Shannon information finding. The updated notebook currently treats Phase 2 sheaf as a standalone observation. Tightening the cross-reference gives readers the framework-level picture: two independent observables both track legal-move count at high correlation, suggesting a stable state-richness subspace.

This is a small annotation addition to §10.12 rather than a structural rewrite.

OLD (the sheaf headline paragraph in §10.12):
```
**Phase 2 dynamic sheaf headline.** A 60-move random-play game yielded sheaf λ₂ ∈ [0.22, 0.93] with Spearman(legal_moves, λ₂) = +0.765, p = 1.1 × 10⁻¹². The sheaf spectral gap tracks *strategic freedom* (count of legal placements), not disc density. The L7b caveat from the logo notebook applies: this is a snapshot correlation, and predictive power of `spec(L_F(t))` for `t + Δ` has NOT been tested.
```

NEW:
```
**Phase 2 dynamic sheaf headline.** A 60-move random-play game yielded sheaf λ₂ ∈ [0.22, 0.93] with Spearman(legal_moves, λ₂) = +0.765, p = 1.1 × 10⁻¹². The sheaf spectral gap tracks *strategic freedom* (count of legal placements), not disc density. The L7b caveat from the logo notebook applies: this is a snapshot correlation, and predictive power of `spec(L_F(t))` for `t + Δ` has NOT been tested.

Paired with the §10.13 Phase 1c finding that Shannon `I_move` correlates with `n_legal_moves` at ρ = +0.814 on tournament play, the sheaf observable and the information observable are both dominated by the state-richness (count-of-options) axis. Whether they carry independent signal within that axis — i.e. whether `spec(L_F(t))` is informative *conditioning on* `n_legal_moves` — is an open question and the natural next probe for a Phase 1d run.
```

---

## PATCH 6 — AUDIT ITEM: verify chess D₄ character-table class-constancy

**Rationale (this is not a patch, it is an instruction).** The Othello Phase 1 session discovered that lifting the chess convention `B1 = [1, −1, 1, −1, 1, −1, 1, −1]` directly into the D₄ × Z₂ setting failed idempotence because the Othello element numbering puts axis reflections at indices `{4, 5}` and diagonal reflections at `{6, 7}`, and the character must be constant on each conjugacy class. The corrected Othello rows are `B1 = [1, −1, 1, −1, +1, +1, −1, −1]`, `B2 = [1, −1, 1, −1, −1, −1, +1, +1]`.

Whether this is *also* a latent bug in the chess code, or whether the chess code uses a different element indexing under which the naive `[1, −1, 1, −1, 1, −1, 1, −1]` convention happens to be a valid B₁ character, has not been audited.

**Action required:**

1. Open `docs/chess-maths/chess_d4_direct.py` (or wherever `project_irrep` / D₄ character tables live in the chess code).
2. Identify the ordering of the 8 D₄ group elements used in the character table rows.
3. Identify the conjugacy-class partition of those 8 elements *under that specific ordering*.
4. Verify that every character row is constant on each conjugacy class by direct check: for each pair `(g_i, g_j)` that should be conjugate, compute `g_i · g_j · g_i⁻¹` as a permutation and confirm it equals some element `g_k` with `χ(g_k) = χ(g_j)`.
5. Report one of three outcomes:
   - **PASS**: the chess convention is self-consistent under its element ordering. Document the ordering explicitly in the code comment and in §9a so future domain transfers (shogi, go, arimaa) don't repeat the Othello confusion.
   - **FAIL (silent)**: the convention is inconsistent but the bug never triggered because chess's use of `project_irrep` doesn't exercise the axis/diagonal reflections with distinct characters. Document the latent bug, fix the character table, and re-run any downstream `project_irrep` test to confirm no numerical results change (they shouldn't, if the bug was truly silent).
   - **FAIL (actively)**: the convention is inconsistent and some downstream numerical result is affected. Fix the table, re-run the affected tests, document the delta in §9a and in the appropriate CHANGELOG.

**First-principles reference for the audit.** For D₄ under the element ordering `{e, C₄, C₂, C₄³, σ_v, σ_h, σ_d, σ_d'}`:
- Conjugacy classes: `{e}, {C₄, C₄³}, {C₂}, {σ_v, σ_h}, {σ_d, σ_d'}`
- B₁ (transforms as x² − y²): axis reflections fixed (+1), diagonal reflections flipped (−1) → `[1, −1, 1, −1, +1, +1, −1, −1]`
- B₂ (transforms as xy): axis reflections flipped (−1), diagonal reflections fixed (+1) → `[1, −1, 1, −1, −1, −1, +1, +1]`

If chess uses a different ordering (e.g. interleaving rotations and reflections, or treating `C₄³ = C₄⁻¹` as `g₃`), the character rows will have different signs at different positions but the same class-constancy constraint applies.

**Note:** if the audit finds the chess convention is *inconsistent but silently safe*, the correct fix is still to correct the table rather than to leave a latent bug in place. A future contributor will otherwise re-trip on it the first time they try to port the irrep decomposition to a context that does exercise the axis/diagonal distinction — as the Othello work did.

---

## Execution order

1. Apply PATCH 1 through PATCH 5 in order. These are pure documentation patches, no code change.
2. Run the grep sanity checks from each PATCH's OLD/NEW blocks to confirm the edits landed.
3. Execute the PATCH 6 audit. Report outcome (PASS / silent FAIL / active FAIL) inline in the PR description.
4. If the audit lands as active FAIL, include the affected numerical delta table.
5. No CHANGELOG entry required for §10 patches (sibling research project); but IF the audit causes a chess-code change, that does warrant a CHANGELOG entry on the main repo.

Total expected work: ~20 minutes of document editing + 10 minutes of audit. No new experiments; everything needed is already in the Othello results folder.

---

## What this prompt is not

- Not a rewrite of §9f, §10.4, or §10.12. The existing text in all three sections is retained and extended.
- Not a claim that the Othello Phase 1c findings are conclusive — the edax-peek result at N=15 is flagged as a watch item, not a finding, and the 2148-position run is in flight.
- Not a proposal to add new experiments to the chess notebook. The suggestion in PATCH 3's framework-level observation (run the in-book I_move experiment for chess) is noted but out of scope for this pass.

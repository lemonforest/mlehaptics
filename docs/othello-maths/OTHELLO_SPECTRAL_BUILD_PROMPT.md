# Claude Code: Othello Spectral Verification & Discovery Build

## Context

This is a sibling project to `docs/chess-maths/`. You are building the computational substrate for `docs/othello-maths/` — the verification pass of §10 ("Phase-Space Othello") from the chess notebook, plus open exploration of structures that §10 names theoretically but no one has yet computed. A subsequent prompt (sequel to this one) will use the encoder and ray infrastructure built here to construct the Othello phase-operator move engine, mirroring what `PHASE_OPERATOR_SUPPLEMENT.md` does for chess.

### Ground truth documents (read before touching code)

1. `docs/chess-maths/chess_spectral_research_notebook.md` §10 — the "Phase-Space Othello" theoretical scaffold. All of §10.1–§10.10 is the survey you are now verifying.
2. `docs/chess-maths/chess_spectral_research_notebook.md` §9a, §9f, §9h′, §9r — the chess artifacts that transfer (board eigenbasis, coprime roll binding, A₁ depth-gap protocol, polarization framework).
3. `docs/chess-maths/CHESS_SPECTRAL_INSTRUCTIONS.md` — the methodological template.
4. `docs/chess-maths/PHASE_OPERATOR_SUPPLEMENT.md` §11.2 — how the chess phase operators are specified; your output here is the substrate for the Othello analog.
5. `docs/chess-maths/logo_research_notebook.md` §L6–§L7 — the first transfer of the split-object pattern to a non-board domain, which establishes that the pattern generalizes and that honest retractions belong in the notebook.

### Steven's cognitive style & working principles (do not skip)

Steven has aphantasia and reasons through proprioceptive spatial construction. He compresses multiple meanings into single statements, stress-tests ideas through cross-domain analogies, and treats the assistant as a peer-level intellectual collaborator. Informal-sounding intuitions frequently identify real mathematical structure — take them seriously, formalize them, test them computationally before accepting or rejecting.

Every claim in the notebook is tagged: **KNOWN** (published, cited), **NOVEL** (no prior art found), **CONFIRMED** (computationally verified with numbers), **FAILED** (tested and didn't work). Failures are results, not embarrassments. The chess notebook documents several instructive failures; the logo notebook carries an explicit retraction of its L1 reversibility-via-binding claim. Follow that discipline here.

**Discovery principle for this project:** do not commit to a single fiber-rank arrangement in advance. §10.4 names three candidates (rank-2 by orbit count, rank-6 by irrep count, rank-8 by individual rays). Explore all three. The one that ends up most structurally coherent under the empirical tests should fall out — or multiple may coexist as different views of the same object. The goal is open discovery, not rushed convergence.

---

## Phase 0 — Folder scaffold & shared infrastructure

### Folder layout

Create the following. Nothing exists yet at `docs/othello-maths/`:

```
docs/othello-maths/
├── othello_spectral_research_notebook.md     # living notebook (scaffold below)
├── OTHELLO_SPECTRAL_INSTRUCTIONS.md          # Claude Code operating instructions
├── research/                                  # R&D scripts — disorganized OK
│   ├── __init__.py
│   ├── othello_utils.py                       # board, 8 rays, Blume-Capel signal
│   ├── d4_z2.py                               # D4×Z2 irrep projectors (full, exact Z2)
│   ├── ray_laplacians.py                      # 8 ray graphs + diagonalization
│   ├── fiber_rank_study.py                    # rank-2 vs rank-6 vs rank-8 probes
│   ├── static_fiber_bundle.py                 # rook/bishop-from-rays + holonomy
│   ├── blume_capel_encoder.py                 # candidate signal encoders
│   ├── dynamic_sheaf.py                       # time-varying restriction maps
│   ├── coprime_generators.py                  # Othello-side of §9f
│   ├── a1_depth_gap_probe.py                  # §9h′ transfer test
│   ├── wthor_loader.py                        # WTHOR database parser
│   ├── perfect_play_compare.py                # Takizawa 2023 perfect-play correlations
│   ├── empirical_tests.py                     # H10–H14 batch runner
│   └── consolidated_tests.py                  # all-pass sanity battery
├── results/                                   # CSVs, npy (gitignored; regenerate)
│   └── .gitkeep
└── figures/                                   # only if generated
    └── .gitkeep
```

**Production package — do not create yet, but design toward.** The eventual production layout mirrors `chess-spectral/python/chess_spectral/`:

```
othello-spectral/python/othello_spectral/
├── __init__.py
├── board.py
├── rays.py
├── irreps.py
├── encoder.py                 # encode_* — dimension TBD from fiber rank choice
├── tables.py                  # precomputed D4×Z2 projectors, coprime generators
├── phase_operators/           # sequel prompt populates this
│   └── __init__.py
└── utils.py
```

Write research scripts so that functions (not just `__main__` blocks) are importable. When a script graduates to production, the move should be `from research.ray_laplacians import build_ray_laplacians` → `from othello_spectral.rays import build_ray_laplacians`, with no rewrite. That's the refactor budget.

### Shared utilities — build these first, everything else imports them

`research/othello_utils.py`:
- `board_size = 8`
- `N = 64`
- `rc_to_idx(r, c)`, `idx_to_rc(i)`
- `grid_laplacian_8x8()` → returns `L_grid` (64×64), uses the same construction as chess §2. Verify eigenvectors match the 2D DCT basis to machine epsilon — this is a sanity check, not a novel claim.
- `ray_offsets()` → dict with keys `{'N','NE','E','SE','S','SW','W','NW'}` and dr/dc pairs.
- `blume_capel_signal(board_state)` → maps a 64-cell {−1, 0, +1} board state to a real-valued 64-vector.
- `mine_yours_empty_signal(board_state, side_to_move)` → the player-relative variant (Nanda-Lee-Wattenberg 2023 representation).

`research/d4_z2.py`:
- Lift `project_irrep` from `docs/chess-maths/chess_d4_direct.py` but extend the group to D₄×Z₂ (16 elements, 10 irreps). Exact Z₂ means color inversion is an honest symmetry in Othello, unlike chess.
- Provide `project_irrep(signal, irrep_label)` for each of the 10 D₄×Z₂ irreps.
- Provide `character_table_d4z2()` for reference.
- Sanity: character orthogonality should hold to machine epsilon. Report `max |⟨χ_i, χ_j⟩ − δ_ij|` across all irrep pairs.

`research/ray_laplacians.py`:
- For each of 8 ray directions, construct `L_ray_d` on 64 vertices: edges are nearest-neighbor along direction `d` (and its inverse), respecting boundaries.
- Diagonalize each. Report the spectrum.
- Construct the *superposed* `L_rays = Σ_d L_ray_d` and diagonalize.
- Also construct orbit-averaged Laplacians: `L_ortho = L_N + L_E + L_S + L_W`, `L_diag = L_NE + L_SE + L_SW + L_NW`.

All three — utils, irrep projectors, ray Laplacians — are the infrastructure the rest of the prompt depends on. Get them passing sanity checks before moving on.

---

## Phase 1 — Batched hypotheses (the verification pass)

Each hypothesis below is a concrete computation with a pass threshold, a related prior from chess or the literature, and a status field. Run them all, emit a structured CSV/JSON report, and write prose interpretation in the notebook. The point of batching is to let you fan out across all of them and surface surprises together rather than debating each one in isolation.

### H-table format

Emit `results/phase1_hypotheses.csv` with columns:

```
id, statement, computed_value, threshold, status, notes
```

Where `status ∈ {PASS, FAIL, PARTIAL, UNDETERMINED}`. Include narrative expansion in the notebook section §1.X for each.

### Hypotheses — transfer and core structure

**H1 — Board Laplacian eigenbasis transfers.**
- Compute: eigenvectors of `L_grid` vs 2D DCT basis. Max |cos(v_i, dct_i)| over all pairs after Hungarian matching.
- Threshold: > 1 − 1e-12
- Prior: Chess §2 (KNOWN, verified to 5.86×10⁻¹⁶)

**H2 — Full 8-ray representation decomposes as 2A₁ ⊕ B₁ ⊕ B₂ ⊕ 2E under D₄.**
- Compute: apply D₄ character-projection formula to the 8-dim space of ray indicators {N, NE, E, SE, S, SW, W, NW}. Extract multiplicities.
- Threshold: match 2, 0, 1, 1, 2 in the (A₁, A₂, B₁, B₂, E) ordering exactly.
- Prior: §10.4 derivation (NOVEL per §10.4, claimed but not previously verified).

**H3 — B₁ and B₂ ray-modes are numerically distinct.**
- Compute: B₁ basis vector ((N+S) − (E+W))/2 on ray indicators vs B₂ basis ((NE+SW) − (SE+NW))/2. Inner product; Frobenius norm of `L_ray @ (B1 − B2)` vs `L_ray @ (B1 + B2)`.
- Threshold: cos(B₁, B₂) < 0.01; spectral action on the two modes differs by a detectable factor.
- Prior: "rook/bishop signature from rays" (§10.4, NOVEL).

**H4 — Orthogonal vs diagonal ray Laplacians are spectrally distinct.**
- Compute: spec(L_ortho) vs spec(L_diag). Report eigenvalue histograms, top 5 eigenvalue deltas, mean degree, bandwidth.
- Threshold: at least one spectral invariant (λ₂, bandwidth, mean degree) differs by > 5%.
- Prior: chess rook ≠ bishop spectrally (KNOWN); Othello ray analog (NOVEL).

**H5 — Static ray bundle has nontrivial holonomy.**
- Compute: per-square local fiber vectors from the 8 ray Laplacians (following `chess_connection.py`'s approach). Walk a closed loop on the board; measure cos(fiber_start, fiber_end) after parallel transport around the loop.
- Threshold: |cos − 1.0| > 0.01 for at least one loop (any nontrivial holonomy).
- Prior: chess off-diagonal fiber has measured holonomy −0.016 (§8c, NOVEL-CONFIRMED).

**H6 — Fiber rank is one of {2, 6, 8}.**
- Compute: stack all 8 ray Laplacians as a (8, 64, 64) tensor, flatten to (8, 4096), run SVD. Report σ₁…σ₈ and effective rank (σ_i / σ_1 > 1e-6).
- Also compute: (a) stack the two orbit Laplacians L_ortho, L_diag and check rank (expect 2). (b) project each ray Laplacian onto the 6 D₄ irrep channels, check rank after projection (expect 6).
- Threshold: none — this is open exploration. Report all three and let the structure speak.
- Prior: §10.4 names 2/6/8 as candidates (NOVEL, uncommitted).

**H7 — Coprime generators for the Othello modulus exist and are derivable from the fiber rank.**
- Given the fiber rank chosen in H6 (or each candidate), compute the production encoder dimension: `D = (rank + k_dct) × 64` where k_dct is the number of D4×Z2 DCT channels (likely 8 or 10). For each candidate D, find the row and column generators (analog of 67 and 7 for chess's 640): smallest primes coprime to D that are non-2, non-5, and coprime to each other.
- Threshold: existence. Report the generators for each candidate D.
- Prior: §9f coprime roll binding (KNOWN for chess). This is the mechanical analog.

**H8 — D4×Z2 invariance of the Blume-Capel signal encoder.**
- For any one of the candidate encoders (keep simplest: concat the 10 D4×Z2 irrep projections × 64), verify that the A₁ channel is invariant under all 16 D4×Z2 transforms: swap all colors AND rotate/reflect.
- Threshold: ||encode(transform(board)) − encode(board)||_A1 < 1e-10 for all 16 group elements.
- Prior: chess A₁ D4-invariance verified (§9a, CONFIRMED, ||diff|| = 0.00).

**H9 — A₁ depth-gap protocol transfers from chess to Othello.**
- This is the §9h′ transfer test: sample ~500 Othello positions at varying game stages, compute A₁ energy of each, correlate with Takizawa 2023 perfect-play evaluation depth-gap (|eval_deeper − eval_shallow|).
- Threshold: Spearman ρ > 0.3, p < 0.01
- Prior: chess ρ = +0.452, p = 0.0005 (§9h′, CONFIRMED).

### Hypotheses — open exploration (no pre-committed answer)

**E1 — Null tests. What doesn't transfer?**
- Knight exact DCT orthogonality (§1b.3) — no Othello analog because no knight-like move. Confirm absence.
- Pawn antisymmetric fiber (§9m) — should have no Othello analog because Z₂ is exact. Confirm: compute `||A_antisym|| / ||A_sym||` on any Othello ray operator. Should be ≈ 0.
- Rank-5 piece-species fiber — confirm the 5-tuple classification has no Othello counterpart (single particle type).

**E2 — Is there a Pauli-exclusion analog?**
- Chess: two pieces of the same color can't occupy the same square (plus pawn promotion structure). Othello: discs can't overlap, but can flip.
- Compute: the "fermionic" structure of Othello. Is there a Jordan-Wigner-type encoding where the flip is a fermionic sign? The Blume-Capel +1/0/−1 fiber is a three-state system — is there a CP²-sigma-model structure? Explore.

**E3 — Does the monotone disc count give a global KAM-like slow variable?**
- Chess: the pawn sector is the slow variable (§1b.6, KAM grounding).
- Othello: disc count increases monotonically by at least 1 per turn (0 if passing is allowed, rare). Treat ρ_occupied = N_discs / 64 as a slow variable and compute per-phase spectral observables vs ρ. Does the spectrum "see" the three regimes (opening / midgame / endgame) the way the chess pawn sector sees material phases?

**E4 — Compass-model Hamiltonian.**
- §10.5 names the 90° compass model as the closest published structural match. Write the ray-gated compass Hamiltonian `H_compass = −Σ_rays Σ_pairs_in_ray s_i s_j` on the 8×8 lattice. Compute its ground state. Is it a reachable Othello position? If not, how far from any reachable position (Hamming distance)?

**E5 — Fortuin-Kasteleyn / Wolff-cluster statistics on Othello flanks.**
- §10.6 identifies Wolff flanking as the closest stat-mech analog. Compute: across a sample of game positions (from WTHOR or random legal play), measure the distribution of flank cluster sizes. Compare with (a) exponential, (b) power-law, (c) Fortuin-Kasteleyn on Blume-Capel with matched temperature.

**E6 — Dynamic sheaf Laplacian at move k.**
- Following §10.7 and Hansen-Ghrist (2019): build the sheaf Laplacian whose restriction maps encode the current flank-reachable structure from each cell. Compute its spectrum at moves k = 4, 10, 20, 30, 40, 50, 60 across a sample game.
- Open: does the spectral gap track strategic phase transitions (edge-control, stable-region formation, endgame)? Is there an analog of the Otteau-Gryffus "move-40 shift" in Othello tournament literature?
- Prior: §10.7 names this construction (NOVEL, no prior implementation in the literature for any game).

**E7 — Global T-breaking: is disc-count entropy the right quantity?**
- Chess has local T-breaking (pawn, Hatano-Nelson). Othello has global T-breaking (monotone filling). Try to construct the Othello analog of the chess pawn's antisymmetric fiber at the level of the *game trajectory* — i.e., the entropy gradient along the disc-count monotone. Compare forward and reverse move sequences; is the asymmetry detectable spectrally?

**E8 — Takizawa perfect-play correlation with spectral observables.**
- For positions on/near the Takizawa 2023 perfect-play principal variation, compute each candidate spectral observable (A₁ energy, fiber norm, ray balance, dynamic sheaf gap). Which correlates best with (a) optimal evaluation, (b) disc-differential, (c) move-count-to-end? This is the Othello equivalent of the Stockfish depth-gap correlations in chess.

### Emission format for Phase 1

Write to `results/phase1_hypotheses.csv` (one row per hypothesis) and `results/phase1_detail.json` (per-hypothesis detailed numerics). Include a prose section in the research notebook (scaffold §2.X) for each, following the chess notebook's "prediction → experiment → numbers → interpretation" template.

---

## Phase 2 — Dynamic fiber: the sheaf Laplacian instantiation

This is the conceptually novel piece that has no chess analog. §10.7 is framework-level; the instantiation is yours.

### Minimal viable sheaf Laplacian

Before Hansen-Ghrist's full machinery, build the simplest usable form:

1. **Vertex stalks:** 3-state Blume-Capel fiber F(v) = ℝ³ at each cell, carrying (s = −1, s = 0, s = +1) components. Use one-hot encoding as the initial representation.

2. **Edge stalks:** the 8 ray directions. For each directed ray segment from v along direction d of length up to 7, F(e) = ℝ (scalar, or ℝ² for signed).

3. **Restriction maps F_{v⊴e}:** for a ray segment starting at v in direction d, the restriction map is:
   - Zero if v is empty (no ray originates from v)
   - Identity if v matches the flank-starter color
   - Bracket-gated if v is a candidate bracket terminator

4. **Update rule:** after every move, recompute restriction maps on affected rays only. The move changes O(rays × avg_ray_length) = O(~30) restriction entries per move, not all 64 × 8 = 512.

5. **Sheaf Laplacian spectrum:** compute spec(L_F) at each move. Track:
   - Spectral gap λ₂
   - Total spectral entropy H = −Σ p_i log p_i where p_i = λ_i / Σ λ_j
   - Connection to legal-move count: does |λ_0 kernel| correlate with |legal moves|?

### Deliverables from Phase 2

- `research/dynamic_sheaf.py` — working implementation, < 500 lines including sanity checks.
- Notebook §3: spectrum evolution across a sample game (any WTHOR game will do; pick one with good strategic texture).
- Open question to document: is the dynamic sheaf spectrum a useful state summary in its own right? If the spectral gap is flat across legal moves at a given position, the sheaf isn't adding discriminative signal over the static fiber. If it varies meaningfully, it's a new observable.

---

## Phase 3 — Proto-phase operator (sketch only, not full implementation)

This phase is **scoping**, not building. The full phase-operator build is a sequel prompt. Here you answer the preflight questions so that prompt can be written cleanly.

For each of the candidate encoder dimensions D from H7, compute and document:

1. **Placement generators.** The Othello equivalent of chess P_rook/P_bishop. A placement at (r, c) "sees" along 8 rays. What are the 8 generators? Likely some combination of (r × gen_row + c × gen_col) mod D shifts along each of {N, NE, E, SE, S, SW, W, NW} directions at up to 7 steps.

2. **Flip gate.** Unlike chess, the move also flips discs. Is there a phase-arithmetic representation of the flip operator? Options to explore:
   - Flip as a multiplication by −1 in the Blume-Capel signal (sign flip at phase-indexed positions).
   - Flip as a separate Z₂ channel in the encoder.
   - Flip as a composition of placement + Z₂ generator.

3. **State-dependent gating.** Chess bolts occupation-awareness onto static operators (Solutions A/B/C in §11.4). Othello needs this from the start: the placement is legal only if at least one ray brackets opponent-then-same-color. Sketch how this gate is structured in phase space — is it a mask on the generated set, or is it intrinsic to the generator (i.e., the generator only emits phases for rays that currently bracket)?

4. **Ground-truth comparison.** The chess phase-op validation uses `python-chess`. For Othello, use `edax` or a pure-Python Othello engine (there are several on PyPI; `othello_engine` or `reversi` packages). Pick one for the sequel.

Write this as `docs/othello-maths/OTHELLO_PHASE_OP_PREFLIGHT.md` — the input the sequel prompt will absorb.

---

## Phase 4 — WTHOR empirical tests (run if time permits)

These are §10.10 tests 1–5 plus the additional A₁ depth-gap transfer. If Phase 1–3 consume the session budget, leave these as clearly-scoped TODOs in the notebook rather than attempting them partially.

WTHOR database: 61,549 games, French Othello Federation, 2001–2020. Standard format is `.wtb` binary. A Python parser exists in several projects (`wthor-parser` on PyPI, or roll your own ~100-line script).

- **T1. Flip-count distribution** — power law vs exponential. Extract per-move flip count across all games; fit both distributions; report `ln L` ratio and exponents.
- **T2. B₁ vs B₂ population asymmetry** — compute ⟨B₁²⟩ and ⟨B₂²⟩ along game trajectories. If strategic corner/edge control biases the diagonal-orbit modes, B₂ should be elevated vs B₁ in tournament games but not in random-play games.
- **T3. Shannon info per move** — `I_move = log₂ |legal_moves| − log₂ P(chosen | empirical_freq)`. Histogram across game stages.
- **T4. Trajectory in (T_eff, D_eff)** — map each position to a Blume-Capel control-parameter point and ask whether games cluster near the tricritical point at half-filling.
- **T5. Flank cluster size distribution** — per-move cluster sizes compared with Fortuin-Kasteleyn Blume-Capel statistics.

---

## The research notebook scaffold

Create `docs/othello-maths/othello_spectral_research_notebook.md` with the following skeleton. Fill in §1, §2.X, §3 as you go through Phases 0–2. Leave §4–§5 as stubs for Phase 3–4 (or the sequel prompt).

```
# Othello as a Dynamic Spectral Lattice System — Research Notebook

**Authors:** Steven (mlehaptics Project) & Claude (Anthropic)
**Date:** April 2026
**Status:** Active research — §1–§2 computational, §3 open exploration, §4–§5 scaffold.
**Tools:** Python 3, NumPy, SciPy (all runnable standalone).

> Living document. Sibling to
> [../chess-maths/chess_spectral_research_notebook.md](../chess-maths/chess_spectral_research_notebook.md)
> (the chess notebook's §10 is the theoretical survey this notebook
> tests computationally) and
> [../chess-maths/logo_research_notebook.md](../chess-maths/logo_research_notebook.md)
> (the second instance of the split-object-with-fiber-matrix pattern).

## 0. Framing
Why Othello. What transfers from chess, what doesn't. The §10 thesis
in one paragraph, plus the discovery principle: fiber rank unresolved.

## 1. Infrastructure
Board Laplacian (H1). D₄×Z₂ irrep projectors. 8 ray Laplacians.
Blume-Capel signal. Sanity numbers.

## 2. Phase 1 batch — verification & exploration
§2.H1–§2.H9 (transfer hypotheses) and §2.E1–§2.E8 (open exploration).
Each subsection: prediction, experiment, measured numbers,
status tag, interpretation, lesson.

## 3. Dynamic fiber — sheaf Laplacian instantiation
Vertex stalks, edge stalks, restriction maps, update rule.
Spectrum evolution across a sample game. Is this a useful observable?

## 4. Phase-operator preflight  [scaffold only in this pass]
Candidate encoder dimensions D. Placement generators. Flip gate.
State-dependent gating. Ground-truth engine choice.

## 5. WTHOR empirical tests  [scaffold only in this pass]
T1–T5 from §10.10. Shell CSVs. TODOs.

## 6. Vocabulary collisions specific to Othello
"Flip" vs "flank" vs "bracket." "Ray" (direction) vs "line" (segment).
"Fiber" — adopted from chess §7; means the non-spatial rule-coupling
content of the ray structure projected into the grid eigenbasis.

## 7. Appendix: Environment & Reproducibility
Versions, seeds, wall-time targets. Code organization mirrors
chess-spectral; see `research/` directory.
```

---

## Reporting discipline

At the end of the session, emit:

1. `results/phase1_hypotheses.csv` — structured per-hypothesis status table.
2. `results/phase1_detail.json` — per-hypothesis numeric detail.
3. `results/session_summary.md` — a short narrative: what passed, what failed, what surprised, what's scoped-out-for-next-session. ~1 page.
4. Notebook sections §1–§3 filled in with prose + numbers + interpretation.
5. `OTHELLO_PHASE_OP_PREFLIGHT.md` — the handoff document for the sequel prompt.

**Honest-science disciplines:**
- Every claim tagged KNOWN / NOVEL / CONFIRMED / FAILED.
- Failed predictions kept in the notebook with root-cause analysis. Follow the LOGO L1 retraction template — show the wrong number alongside the right one.
- Don't back-rationalize. If H6 reports effective rank = 7.3 instead of 2/6/8, that is the result. Write it down and think about what 7.3 means.
- If an intuition from Steven's framing survives computation, say it survived and in what form. If it didn't survive in the form stated, say what did survive.
- No emoji, no marketing, no "exciting breakthrough" framing. Report numbers, interpret, stop.

---

## Common pitfalls anticipated in advance

1. **Don't duplicate grid Laplacian construction.** Use one source in `othello_utils.py`. Every research script imports from it.

2. **D₄×Z₂ vs D₄.** Chess uses D₄ because Z₂ is approximate (pawn breaks it). Othello uses full D₄×Z₂ because color inversion is exact. The irrep count doubles (5 → 10). Lift the chess `project_irrep` carefully — don't accidentally use D₄ alone and miss the Z₂-odd channels.

3. **Signal choice matters.** Blume-Capel {−1, 0, +1} and mine/yours/empty are structurally identical up to player-relative sign flip. Pick one canonically (recommend: world-frame Blume-Capel for spectral symmetry work; side-to-move frame for probe-style interpretability tests). Document the choice and don't drift between conventions across sections.

4. **Dynamic sheaf is expensive if naive.** Don't rebuild all 512 restriction-map entries each move. Only O(30) entries change; keep a cache.

5. **The "fiber rank" ambiguity is real.** Different questions (bundle rank, irrep count, orbit count) get different right answers. Don't collapse them in prose.

6. **Ground-truth engine for Othello.** `edax` is the gold standard but requires a binary. For Python-only testing use `python-othello` or write a ~200-line legal-move generator — the game is small enough that a from-scratch implementation isn't risky. Pick one, document the choice.

7. **Spectral entropy vs Shannon entropy.** The chess notebook caught this one (§9h′ failed with naive Von Neumann entropy). For Othello, distinguish: entropy of the *game signal* on the board (Shannon on a 3-state field) vs entropy of the *sheaf Laplacian spectrum* (Von Neumann on a density matrix derived from λ_i) vs entropy of the *move distribution* (Shannon on legal moves, weighted by policy). Three different objects; keep them apart.

8. **Pure Python Othello board class.** Write one in `othello_utils.py`. 80 lines max. Tests: starting position has 4 central discs, 4 legal moves; after e6 from start, 3 legal black replies; terminal positions have 0 legal moves for both sides.

---

## Key references (chess-inherited + Othello-specific)

**Inherited from chess-maths** — all apply directly:
- Chung 1997, *Spectral Graph Theory*
- Spielman 2025, *Spectral and Algebraic Graph Theory*
- Merris 1994, Laplacian matrices
- Tinkham 1964; Dresselhaus-Dresselhaus-Jorio 2008 — D₄ irrep tables
- Nakahara 2003, *Geometry, Topology and Physics* — sheaf/bundle construction

**Othello-specific, all named in §10 already**:
- Takizawa 2023, arXiv:2310.19387 — weak solution, draw with perfect play
- Zenodo 10.5281/zenodo.10030906 — complete game-value dataset
- Blume 1966, *Phys. Rev.* 141, 517; Capel 1966, *Physica* 32, 966 — Blume-Capel spin-1
- Blume-Emery-Griffiths 1971, *Phys. Rev. A* 4, 1071 — BEG model, ³He–⁴He analogy
- Hansen & Ghrist 2019, *J. Appl. Comput. Topol.* 3, 315 — spectral sheaf theory
- Bodnar et al. 2022, arXiv:2202.04579 — neural sheaf diffusion
- Nussinov & van den Brink 2015, *Rev. Mod. Phys.* 87, 1 — compass models
- Nussinov-Ortiz 2005, *Phys. Rev. B* 71, 195120 — subsystem symmetries
- Wolff 1989, *Phys. Rev. Lett.* 62, 361 — Wolff cluster flip
- Bouabci-Carneiro 2000, *J. Stat. Phys.* 100, 805 — FK for Blume-Capel
- Sagawa-Ueda 2010, *Phys. Rev. Lett.* 104, 090602 — information thermodynamics
- Horowitz-Esposito 2014, *Phys. Rev. X* 4, 031015 — bipartite information flow
- Li-Hopkins-Bau et al. 2023, arXiv:2210.13382 — Othello-GPT world model
- Nanda-Lee-Wattenberg 2023, arXiv:2309.00941 — mine/yours/empty linearity
- Fraenkel 2000 — two-player cellular automata games
- Ollinger-Theyssier 2019, arXiv:1908.06751 — bounded-change CA

---

## How to run (end state)

```bash
# Phase 0: sanity
python research/othello_utils.py      # grid Laplacian unit test
python research/d4_z2.py              # irrep character orthogonality test
python research/ray_laplacians.py     # 8 ray spectra + H1 check

# Phase 1: batched hypotheses
python research/consolidated_tests.py --phase 1 --emit results/

# Phase 2: dynamic sheaf
python research/dynamic_sheaf.py --sample-game results/sample_game.json

# Phase 3: preflight
python research/phase_op_preflight.py > OTHELLO_PHASE_OP_PREFLIGHT.md

# Phase 4 (optional, if WTHOR available):
python research/wthor_loader.py --db path/to/WTHOR.wtb
python research/empirical_tests.py --phase 4 --emit results/
```

---

## Definition of done for this prompt

- `docs/othello-maths/` exists with the file layout above.
- `research/othello_utils.py`, `research/d4_z2.py`, `research/ray_laplacians.py` — all three pass their sanity checks (H1, character orthogonality, 8-ray spectra well-defined).
- Phase 1 hypotheses H1–H9 have computed numbers. E1–E8 have at least preliminary numbers or a clear statement of what was blocked and why.
- Phase 2 dynamic sheaf implementation runs end-to-end on one sample game and produces a spectrum trajectory.
- Phase 3 preflight document drafted.
- Research notebook §1, §2, §3 have prose + numbers matching the CSV.
- Session summary (`results/session_summary.md`) written: 1 page max, honest about what passed, what failed, what's scoped to the sequel.

Phase 4 is a stretch goal. If you get the first three phases done cleanly, the sequel prompt (phase-operator build) becomes writable. That's the win condition.

---

## What this prompt is not

This prompt does not build the Othello phase-operator move engine. That is the sequel, written against `OTHELLO_PHASE_OP_PREFLIGHT.md` after this pass lands.

This prompt does not commit to a fiber rank. It computes multiple candidates and reports.

This prompt does not duplicate chess-maths work. Every chess artifact it references is importable or re-derivable from the chess notebook; the work here is the Othello-specific verification and extension.

This prompt does not promise success on every hypothesis. Some will fail. Failures are data. Document them in the notebook with the same care given to successes.

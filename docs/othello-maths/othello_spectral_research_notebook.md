# Othello as a Dynamic Spectral Lattice System — Research Notebook

**Authors:** Steven (mlehaptics Project) & Claude (Anthropic)
**Date:** April 2026
**Status:** Active research — §1–§3 computational, §4–§5 scaffold.
**Tools:** Python 3, NumPy, SciPy (all runnable standalone).

> Living document.  Sibling to
> [../chess-maths/chess_spectral_research_notebook.md](../chess-maths/chess_spectral_research_notebook.md)
> (the chess notebook's §10 is the theoretical survey this notebook
> tests computationally) and
> [../logo-maths/logo_research_notebook.md](../logo-maths/logo_research_notebook.md)
> (the second instance of the split-object-with-fiber-matrix pattern,
> including an explicit retraction in L7b that this notebook takes
> as a cautionary template for Phase 2 claims).

Every claim is tagged **KNOWN** (published, cited), **NOVEL** (no
prior art found), **CONFIRMED** (computationally verified in this
session), **FAILED** (tested and didn't work), or **UNDETERMINED**
(requires data not available in this session).

---

## 0. Framing

Othello shares the 8×8 grid with chess and therefore inherits the
board Laplacian eigenbasis (§9b chess), the D₄ symmetry group, and
the 8-generator spectral lattice.  Everything above the board
differs: no movement, no per-piece Laplacians, a single Blume-Capel
3-state fiber at each cell, exact D₄×Z₂ symmetry (Z₂ is approximate
in chess because pawns break it — §1b.1 chess), non-local flanking
updates, monotone disc-count filling as the global T-breaker.

The verification target is §10 of the chess notebook — a
hybrid-framework thesis stitching Blume-Capel spin-1 + D₄×Z₂ + 8-ray
decomposition `2 A1 + B1 + B2 + 2 E` + Wolff-like flanking under
Fraenkel bounded-change CA semantics + Hansen-Ghrist dynamic sheaf +
Sagawa-Ueda thermodynamics under a Boltzmann-policy embedding.

The discovery principle: **do not commit to a single fiber rank in
advance**.  §10.4 names three candidates — rank 2 (orbit count),
rank 6 (irrep count), rank 8 (individual rays) — and this session's
job is to probe all three and report what the structure actually
yields.

---

## 1. Infrastructure

All numbers below come from the consolidated Phase 1 runner at
[research/consolidated_tests.py](research/consolidated_tests.py).
Status tags per hypothesis match
[results/phase1_hypotheses.csv](results/phase1_hypotheses.csv).

### 1.1 Board Laplacian — sanity (H1)

Construction: `research/othello_utils.py::grid_laplacian_8x8` builds
the P₈ □ P₈ graph Laplacian on 64 vertices.  `dct_basis_2d` constructs
the length-8 DCT-II basis and tensors it into the 64-column 2D
basis.  Comparison handles degenerate eigenvalue subspaces by block-
matching `||V V^T − D D^T||` rather than per-vector inner products
(critical: some eigenvalue multiplicities reach 4, so individual
eigenvectors are only defined up to rotations within their degenerate
block).

    subspace_gap = 3.390e-14
    eig_residual = 7.105e-15

**H1 status: PASS** (threshold 1e-12).  **CONFIRMED / KNOWN**:
identical to chess §2 (5.86e-16 there; the slightly worse number
here is the block-subspace metric, not the per-vector cosine).  The
grid Laplacian eigenbasis transfers verbatim.

### 1.2 D₄×Z₂ irrep projectors — sanity (H8 substrate)

[research/d4_z2.py](research/d4_z2.py) implements the full 16-element
group.  Element indexing is linear `2*g + z` with `g ∈ 0..7` (D₄
spatial) and `z ∈ {0, 1}` (Z₂ colour flip).  Bug note: the initial
table had `B1 = [1, −1, 1, −1, 1, −1, 1, −1]` inherited from chess
convention; this broke idempotence by failing to be constant on
conjugacy classes `{g4, g5}` (axis reflections) and `{g6, g7}`
(diagonal reflections) — verified by direct conjugation
`g1 · g4 · g1^-1 = g5` and `g1 · g6 · g1^-1 = g7`.  The corrected
table is `B1 = [1, −1, 1, −1, +1, +1, −1, −1]`,
`B2 = [1, −1, 1, −1, −1, −1, +1, +1]`.

Sanity checks all pass at machine precision:

    character orthogonality: max|<chi_mu,chi_nu>/|G| - delta| = 0.000e+00
    group action identity:   identity_err = 0.000e+00
    (g2)^2 = e:              err = 0.000e+00
    projection idempotence:  max err = 4.441e-16   (over all 10 irreps)
    projection completeness: reconstruction err = 4.441e-16
    Z2 parity split:         Z2-odd on '+' irreps = 0.000e+00
                             Z2-even on '-' irreps = 0.000e+00

**CONFIRMED**: the D₄×Z₂ = D₄ × Z₂ direct-product structure, with
10 irreps labelled `{A1±, A2±, B1±, B2±, E±}`, projects cleanly.

### 1.3 Ray Laplacians (H2, H4)

[research/ray_laplacians.py](research/ray_laplacians.py) builds per-
direction graph Laplacians.  Two constructions:

- **Undirected** (standard graph Laplacian, self-adjoint): `L_d =
  L_{-d}` because graph edges are unordered, so the 8 ray labels
  collapse to 4 distinct operators (N=S, E=W, NE=SW, NW=SE).
- **Directed** (non-symmetric, forward edges only): all 8 operators
  are distinct.

The 8 rays partition into two D₄ orbits of size 4: orthogonal
`{N, E, S, W}` and diagonal `{NE, SE, SW, NW}`.  Orbit-averaged
Laplacians `L_ortho` and `L_diag` capture the orbit-level structure.

Verified mean degrees:

    ortho rays (N, E, S, W):   mean degree 1.750   (path graph length 8 on each row/col)
    diag rays (NE, SE, SW, NW): mean degree 1.531   (diagonal path graphs of varying length)

**H2 — 8-ray D₄ decomposition.**  Applying the character-projection
formula to the 8-dim ray-indicator space yields multiplicities

    measured: {A1: 2, A2: 0, B1: 1, B2: 1, E: 2}
    expected: {A1: 2, A2: 0, B1: 1, B2: 1, E: 2}

**H2 status: PASS.  CONFIRMED** the `Gamma_8 = 2 A1 + B1 + B2 + 2 E`
prediction of §10.4 (NOVEL there; now computationally verified).

**H4 — ortho vs diag spectral distinctness.**

    mean_deg_ortho = 1.7500,  mean_deg_diag = 1.5312  (rel diff 0.125)
    bandwidth_ortho = 7.7200, bandwidth_diag = 6.8284 (rel diff 0.116)
    lambda2_ortho  = 0.1522,  lambda2_diag  = 0.1522  (rel diff 0.000)

**H4 status: PASS** (threshold: max rel diff > 0.05).  **CONFIRMED**:
ortho and diag Laplacians differ at mean-degree and bandwidth level,
though lambda₂ (algebraic connectivity) happens to match — both are
path-graph-like structures with the same connectivity gap.

---

## 2. Phase 1 batch — verification & exploration

### 2.H3 B₁ vs B₂ ray modes are numerically distinct — **CONFIRMED**

    cos(B1, B2) on 8-dim ray indicators = 0.0  (exact)
    L_B1 = weighted sum of (L_N..L_NW) with B1 coefficients
    L_B2 = weighted sum of (L_N..L_NW) with B2 coefficients

    ||L_B1||_F = 14.966
    ||L_B2||_F = 14.966
    Frobenius cos(L_B1, L_B2) = 0.000e+00   (exact)
    max |L_B1 - L_B2| = 1.000
    bandwidth(L_B1) = 6.485, bandwidth(L_B2) = 6.485

Not just distinct — **Frobenius-orthogonal**.  The B₁ mode lives
entirely in the orthogonal-ray edge set; the B₂ mode lives entirely
in the diagonal-ray edge set; the two subspaces share no non-zero
matrix entries, so the lifted 64×64 operators are orthogonal in the
matrix-inner-product sense.  This is *stronger* than the originally
specified "detectable factor" — B₁ and B₂ are orthogonal modes, not
just distinct ones.

The equal Frobenius norms and bandwidths reflect that orthogonal-
ray and diagonal-ray path graphs are isomorphic (both are
unions of disjoint paths on an 8×8 lattice), just embedded along
different axes.

**Literature grounding.**  This realises §10.4's claim that the
B₁↔B₂ swap is the group-theoretic signature of the rook/bishop
distinction, but derived *purely from rays* with no reference to
piece species.

### 2.H5 Static ray bundle has nontrivial holonomy — **CONFIRMED**

Local fiber at site s is the stack of 8 ray-Laplacian rows at s,
flattened to `R^{512}`.  Parallel transport by sign alignment at each
step.  Results on 4 closed loops:

    plaquette (4 cells), centred at (3,3):  cos = +1.000  (trivial)
    3x3 loop, top-left corner:               cos = +1.000  (trivial)
    triangle via (0,0)-(0,7)-(7,0):          cos = +1.000  (trivial, three-step)
    rectangle (0,0)-(0,3)-(1,3)-(1,0)-(0,0): cos = −1.000  (Z_2 holonomy)

**H5 status: PASS** (threshold: at least one loop with
|cos − 1| > 0.01).  One of the four loops returns a full Z₂
holonomy.  This is the direct Othello analog of the chess −0.016
holonomy reported in §8c — here the signal is cleaner (a full sign
reversal) because Z₂ is exact in Othello.

**Open**: the specific loops where holonomy appears are not yet
characterised.  Expected follow-up: enumerate all minimal plaquettes
and record which have trivial vs non-trivial transport, to extract
the connection form's curvature structure.

### 2.H6 Fiber rank candidates — **PARTIAL** (open exploration by design)

Three stackings evaluated.  SVD effective rank at threshold
`sigma_i / sigma_0 > 1e-6`:

    undirected stack (8 Laplacians, pairs coincide):          effective rank 4
    directed stack (8 non-symmetric operators):               effective rank 8
    orbit stack (L_ortho, L_diag):                            effective rank 2
    D4xZ2-projected per-site out-degree signature (8 x 640):   effective rank 8

Singular value spectrum:

    orbit_sv:       [82.08, 29.64]
    undirected_sv:  [41.04, 15.75, 14.82, 14.14, ~0, ~0, ~0, ~0]
    directed_sv:    [20.52, 8.54, 8.54, 7.87, 7.41, 7.41, 6.71, 6.71]
    proj_sv:        [19.19, 4.55, 4.55, 2.45, 1.66, 1.66, 1.11, 0.80]

**Interpretation.**  Rank-2 is confirmed as the orbit-level structure.
Rank-4 is the natural undirected construction (N/S, E/W, NE/SW,
NW/SE pairs).  Rank-8 is the directed construction.  **Rank-6 does
NOT fall out naturally** from any of the four stackings — the
`2 A1 + B1 + B2 + 2 E` count is an irrep multiplicity, not an
operator rank.  Following the polarization reframing (§9r chess) —
which derives Othello as `(theta-class, r=inf, c=0)` — rank-2 is
the most structurally defensible and most directly motivated
candidate.

**Recommendation for downstream work**: adopt rank-2 by default for
the production encoder (D = 768 = (2 + 10) × 64) and keep
rank-8 (D = 1152) as an ablation.  Rank-6 should be treated as a
decomposition of the D₄×Z₂ irrep channels, not a stacked-operator
rank.

### 2.H7 Coprime generators exist — **CONFIRMED**

From [research/coprime_generators.py](research/coprime_generators.py),
exhaustive search over small admissible primes:

| rank | D    | (row_gen, col_gen) | 64 phases unique? |
|------|------|--------------------|-------------------|
| 2    | 768  | (7, 11)            | yes               |
| 6    | 1024 | (3, 11)            | yes               |
| 8    | 1152 | (7, 11)            | yes               |

**H7 status: PASS.  CONFIRMED.**  All three candidate dimensions
admit `(p, q)` generator pairs reproducing the chess §9f structure.
**Caveat**: the first attempt used "smallest primes coprime to D"
which produced `(3, 7)` for D = 1024 — these collide because
`(r₁−r₂) · 3 + (c₁−c₂) · 7 = 0` has non-trivial `(r_diff, c_diff) =
(7, −3)` within the 8×8 range.  The fix is explicit phase-uniqueness
checking over all 64 cells, not just coprimality.

### 2.H8 D₄×Z₂ invariance of the encoder — **CONFIRMED**

Played 10 random moves from the Othello start to get a non-trivial
configuration.  Projected the Blume-Capel signal `s` onto A1−; applied
all 16 `(g, z)` group elements and verified:

    max ||A1-(P_g · s) - A1-(s)||_inf over g in D4  =  0.000e+00   (D4 invariance)
    max ||A1-((g,1) . s) + A1-(s)||_inf             =  0.000e+00   (Z2 sign flip, as expected for Z2-odd signal)
    max ||A1+(P_g · s^2) - A1+(s^2)||_inf           =  0.000e+00   (occupation Z2-even invariant)

**H8 status: PASS** (threshold 1e-10 on all three).  **CONFIRMED**
the D₄×Z₂ projection operates correctly on both Z₂ parities.  For
the raw magnetisation (Z₂-odd under colour flip), A1− is D₄-
invariant and Z₂-odd — its projection picks up the correct sign
under `(g, 1)`.  For the occupation quadrupole s² (Z₂-even),
A1+ is fully D₄×Z₂-invariant at machine precision.

### 2.H9 A₁ depth-gap transfer — **UNDETERMINED**

Requires Takizawa 2023 perfect-play data (Zenodo 10.5281/zenodo.10030906)
and an Othello engine capable of variable-depth evaluation (edax or
equivalent).  Neither is available in-session.

Surrogate: A1− energy of 30 random positions (game stages varying 5–40
moves) has mean 3.64, std 7.84 — non-trivial variance, so the
protocol is at least sensible.  The actual transfer test (Spearman
ρ > 0.3, p < 0.01 vs Takizawa depth-gap) is deferred to the sequel.

### 2.E1 Null tests — **CONFIRMED** (absence)

    sum over directed rays ||A_anti|| / ||A_sym||   = 7.621  (directed case has antisymmetry by construction)
    max undirected ray antisymmetric norm           = 0.000e+00  (undirected ops are self-adjoint)

**CONFIRMED**: undirected ray operators have zero antisymmetric
content — the Z₂-breaking "pawn fiber" of chess has no Othello
analog, consistent with exact Z₂ colour symmetry.  Knight-style DCT
orthogonality and rank-5 piece-species fiber have no Othello
referents by construction (single disc type, no knight move).

### 2.E2 Pauli / CP² fermionic analog — **PARTIAL**

The local Z₂ grading on the 3-state Blume-Capel fiber admits a
parity operator `diag(−1, +1, −1)` in the `(+1, 0, −1)` basis,
decomposing "occupied with sign" vs "empty".  This is the local
structure of a CP² sigma model restricted to occupied cells plus
an empty-state singlet.  A full Jordan-Wigner-style fermionic
encoding would require global ordering and fermion-sign accounting,
which is deferred.

### 2.E3 Disc density as slow variable — **PARTIAL** (but suggestive)

Five random games, 300 positions total:

    Spearman(rho, A1- energy on magnetisation)   = +0.671  (p = 1.5e-40)
    Spearman(rho, D4-only A1 energy on s^2)      = +0.998  (p = 0.000)

The second correlation is near-tautological (occupation integral IS
the disc density), so it is a control.  The first is a substantive
result: **A1− magnetisation energy scales with filling density**
with Spearman +0.67 — not perfectly linear, but strongly monotone.
Disc density `rho` behaves as an effective slow variable gating the
magnetisation-sector spectra, consistent with §10.3's Blume-Emery-
Griffiths structural analog.

### 2.E4 Compass ground state — **PARTIAL**

The 90° compass Hamiltonian `H = -sum_rays sum_pairs s_i s_j` on
`s ∈ {±1}` is minimised by constant boards.  Constant boards ARE
reachable Othello terminal states (64-0 sweeps).  Sample random-play
terminal in this session: 48–16 split (hamming to all-+1 = 16).
The compass ground state is therefore *reachable* as a degenerate
extremum, though not by random play.

### 2.E5 Flank cluster-size distribution — **PARTIAL**

Sampled all legal-move flip-counts across 20 random-play games:

    N = 7216 candidate moves
    mean flip count = 2.28
    std             = 1.81
    max             = 13

Full histogram exported in `results/phase1_detail.json`.  Distribution-
fit comparison (power-law vs exponential vs Fortuin-Kasteleyn-Blume-
Capel) is deferred to the sequel when WTHOR tournament data is
available.  Random play produces an exponential-looking tail; it is
an open question whether tournament play shifts this toward
power-law scaling.

### 2.E6 Dynamic sheaf — see §3.

### 2.E7 Disc-count monotone as global T-breaker — **PARTIAL**

Single random game, A1− energy trajectory.  Forward-increment
positive fraction = 0.52 (essentially symmetric), correlation of
forward and reversed gradients = +0.07 (decorrelated) — no signal
at N = 1 game.  Aggregate statistics over many games are needed
before drawing conclusions; at the level of a single trajectory, the
spectral observable does not cleanly distinguish forward from
reversed play.

### 2.E8 Takizawa perfect-play correlations — **UNDETERMINED**

Blocked on external data, as with H9.  Scoped to the sequel.

---

## 2b. Phase 1b — game-trajectory tests on real PGN

Run `research/game_trajectory_tests.py` on the Barcelona European
Grand Prix 2026 transcript (`dataset/liveothello_Barcelona_EGP_2026.pgn`,
35 games, 2184 position records including auto-inserted passes).
Full aggregate in
[`results/phase1b_game_trajectories.json`](results/phase1b_game_trajectories.json);
per-ply CSV in [`results/phase1b_per_move.csv`](results/phase1b_per_move.csv).

### 2b.T1 Flip-count distribution on real play

    N = 2184 positions
    max flip over entire corpus = 12   (single legal move in a single position)
    median per-position max flip = 4.0
    mean-of-mean flip-per-legal-move over positions = 2.23 +/- 0.70

Comparable in magnitude to the random-play surrogate (E5 mean 2.28,
std 1.81, max 13).  Strategic play does **not** dramatically shift the
single-move flip-count distribution at this sample size.  The §10.10 T1
test — power-law vs exponential — requires larger N and an explicit
distribution fit against FK-Blume-Capel and SOC baselines; that is
still scoped to the sequel.

### 2b.T2 B1 vs B2 population asymmetry — **confirmed direction**

The §10.4 and §10.10 T2 prediction: under *rules alone* the two orbits
are indistinguishable; under *tournament strategy* the diagonal orbit
may register higher because corners are diagonal-reachable first from
the centre and edge/corner control is strategically valued
asymmetrically.

    mean <B1^2> energy over 2184 positions = 3.930
    mean <B2^2> energy over 2184 positions = 4.397
    ratio <B1^2> / <B2^2> = 0.894
    paired diff (B1 - B2) mean = -0.468  (s.d. 4.551)
    B2 > B1 in 1351/2184 positions (61.9%)
    B1 > B2 in  833/2184 positions (38.1%)

**The diagonal orbit (B₂) registers ~12% higher than the orthogonal
orbit (B₁) in tournament play.** The effect is in the predicted
direction.  It is not universal — 38% of positions invert the
ranking — but the population mean is clearly offset.  At this sample
size (N = 35 games, ~2200 plies) we cannot yet compare to
random-play expectation with statistical power sufficient to rule
out finite-sample effects; the random-play baseline is a follow-up
measurement.

### 2b.E3 scale-up — **stronger under real play**

    Spearman(rho, A1- energy) over 2184 tournament positions = +0.772
    p-value essentially 0 (Spearman exact limit)

Phase 1 random-play measurement at N = 300: +0.671.  Real tournament
play scales the correlation UP to +0.772 — structural coupling
between disc density and magnetisation-sector spectra is tighter
under skilled play, consistent with the Blume-Emery-Griffiths
reading of §10.3.

### 2b.E7 aggregate forward asymmetry — **small but consistent**

    mean forward-positive fraction over 35 games = 0.541 (s.d. 0.038)
    fraction of games with forward-positive fraction > 0.5 = 0.857  (30/35)

Small but tight signature — 54.1 ± 3.8% of A₁⁻ ply-to-ply gradients
are positive.  The monotone disc-filling T-breaker of §10.8 leaves a
detectable spectral signature at game level.  The tight standard
deviation (0.038) suggests this is a real population effect rather
than per-game noise.

### 2b.G9 A₁⁻ peak/drop trajectory — **Othello analog of §9h′**

Chess §9h' Experiment 2 found the A₁ energy PEAK ply as the decisive
crisis predictor across 5 masterpieces, with the ΔA₁ drop ply
preceding the peak (the drop detects simplification, the peak
detects residual tactical density).

    mean peak  ply = 57.9  (92.8% of game)
    mean drop  ply = 45.9  (73.7% of game)
    corr(peak_ply, drop_ply) across 35 games = -0.298

**The ordering is reversed relative to chess.**  In chess the drop
*precedes* the peak; in Othello the drop (at ~74% of the game)
precedes the peak (at ~93%), which makes structural sense — A₁⁻
magnetisation energy in Othello grows monotonically with disc count
through most of the game, then plateaus near terminal.  The "drop"
in Othello is a midgame simplification event, which can happen
when a large flanking chain is resolved; the "peak" is the near-
terminal maximum of the magnetisation-weighted structure.  The
chess-style simplification-then-peak reading does not transfer.

The peak/drop correlation across games (ρ = −0.298) is a mildly
negative signal — games where the peak occurs especially late
tend to have earlier drops.  Not sharp enough for significance at
N = 35; worth retesting at WTHOR scale.

### 2b Summary

Phase 1b upgrades five PARTIAL probes to numeric-with-real-games
and lands one new prediction (T2) at the corpus-empirical level.
T3 (Shannon info per move) and H9 (depth-gap vs edax) remain
scoped to further tooling — T3 needs the reversi-scripts
`opening_book_freq.csv`; H9 needs a compiled edax binary from the
same repo.

---

## 2c. Phase 1c — reversi-scripts integration

Runs the corpus-level probes that need artefacts from
[`eukaryo/reversi-scripts`](https://github.com/eukaryo/reversi-scripts)
but NOT the 20 GB figshare perfect-play table.  All four sub-phases
of the Phase 1c plan ([`PHASE_1C_PLAN.md`](PHASE_1C_PLAN.md)) land.

### 2c.1 OthelloBoard cross-validated — **CONFIRMED**

Agreement rate against Takizawa's reference bitboard implementation
(vendored in `research/third_party/reversi_misc.py`, GPL v3):

    positions compared:    2684
    positions in agreement: 2684
    agreement rate:         100.000 %

2184 Barcelona corpus positions plus 500 synthetic random-play
positions; zero disagreements.  `OthelloBoard.legal_moves()` is
independently validated; every probe downstream of legal-move
enumeration inherits that confidence.

### 2c.2 §10.10 T3 Shannon information per move — **CONFIRMED**

Opening book `opening_book_freq.csv.bz2` (24 MB, 2.57M rows,
D4-canonical position → WTHOR tournament frequency).  For every
played ply in the Barcelona corpus compute

    I_move = log_2 |M(s)| - log_2 P(chosen | WTHOR empirical,
                                            Laplace alpha=1)

Coverage by game phase (fraction of corpus positions in the book):

    empties 60-53 : 100 %
    empties 52    : 97 %
    empties 51    : 91 %
    empties 50    : 86 %
    empties 49    : 80 %
    empties 30-21 : 14 % down to 3 %
    empties <= 20 :  0 %

Overall in-book fraction: 32.2 % of played moves have at least one
successor position in the WTHOR book.  The 2/3 out-of-book tail is
midgame / endgame where Barcelona 2026 has diverged from any
2001-2020 WTHOR precedent.

Headlines (N = 2099 played plies, 35 games):

    mean I_move (all plies)        = 5.087 bits  (s.d. 2.025)
    mean I_move (in-book only)     = 4.403 bits
    mean I_move (out-of-book only) = 5.412 bits

    Spearman(I_move, n_legal_moves)      = +0.814, p << 1e-10
    Spearman(I_move, A1- energy)         = -0.065, p = 3e-3
    Spearman(I_move, A1- energy) in-book = +0.213, p = 2e-8
    Spearman(game mean I_move, |disc_diff|) = +0.109, p = 0.53

The dominant correlation is with `n_legal_moves` as expected (the
`log_2 |M|` term is leading order).  **The novel finding is the
in-book-only positive correlation between I_move and A1- energy:
ρ = +0.213, p = 2 × 10⁻⁸** (N ≈ 676 in-book plies).  In book-
covered positions — where we have a real empirical-policy
reference — the spectral A1- observable tracks how much a chosen
move diverges from the most-common tournament line.  This is the
first direct connection between the D₄×Z₂ spectral decomposition
and the §10.10 information-theoretic bookkeeping.

The null on `game mean I_move vs |disc_diff|` (ρ = +0.109,
p = 0.53) says that at the GAME level, information-rich games are
not necessarily decisive games.  Consistent with tournament play
containing both forced-sequence blowouts and balanced fights.

### 2c.3 Edax 50-empty knowledge anchor — **PARTIAL / striking but underpowered**

Cross-reference against `empty50_tasklist_edax_knowledge.csv`
(2587 D4-canonical 50-empty positions with edax's predicted
score).  Match count:

    50-empty positions in Barcelona corpus:    35  (one per game)
    canonical matches against 2587-row list:   15  (42.9 %)

Below the `--min-matches = 20` threshold from the Phase 1c plan.
The default runner therefore reports "deferred".  Peek at
`--min-matches = 10`:

    Spearman(A1- energy, edax_score) at matching positions
        = +0.820, p = 1.8 × 10⁻⁴  (N = 15)

**Large effect size with tight p-value** — but N = 15 is below
conventional power thresholds; this is a preliminary anchor, not
a confirmed result.  The direction is intuitive: edax's score is
signed with "good for side-to-move"; at 50-empties only 14 discs
are down, and large A1- magnetisation at that stage typically
reflects one player having flipped more stones overall, which
edax rightly evaluates as an advantage.  **Worth retesting at
WTHOR scale** — a 2000-match corpus would either replicate the
effect or surface selection bias.

### 2c.4 H9 surrogate (A1- energy vs edax d=1 / d=20 gap) — **CONFIRMED (disc-count-mediated)**

Run against the Takizawa-delivered edax 4.5.5 binary
(`wEdax-x86-64.exe`) at depth 1 and depth 20 across the full
Barcelona corpus.

    n_positions_evaluated: 2180 / 2184  (99.8% — 4 parse failures
                                         on rare edax output edge cases)
    Spearman(A1- energy, |d1 - d20|)              = +0.151, p = 1.6 x 10^-12
    Partial Spearman controlling for |disc_diff|  = +0.058, p = 0.007

**Direction matches chess §9h'** (which reported +0.452 at N = 55
Stockfish d=1 vs d=20).  Effect size is roughly a third of chess;
p-value is much tighter because N is ~40x larger.  The chess
§9h' partial-with-piece-count was essentially identical to the
raw Spearman (+0.456 vs +0.452), meaning piece count did NOT
mediate the effect.  **In Othello, the partial collapses from
+0.151 to +0.058** — the signal is mostly a disc-count artifact,
not a pure spectral signal.

**Interpretation.**  Othello's A₁⁻ channel is the Z₂-odd
magnetisation projection; it is strongly coupled to disc density
(§10.12 E3 scale-up: Spearman(ρ, A₁⁻) = +0.772).  Chess's A₁
channel is the full-D₄-invariant component including magnitudes,
which does not reduce to a piece-count proxy.  So the natural
chess/Othello analog is *not* identical — the Othello A₁⁻ is
closer to the chess *signed-sum* A₁ than to the chess *energy* A₁,
and chess §9h' itself shows that A₁ signed sum collapses to a
material-counting proxy (§9h' partial controlling material =
−0.057 vs raw +0.527).  **Our Othello H9 result is the direct
analog of the chess A₁-signed-sum observation, not the
A₁-energy observation**, and the +0.058 partial is the
spectral-beyond-counting residual.

A cleaner chess→Othello transfer would use the Z₂-even
`D4-only A1` projection of `s²` (the occupation magnitude, which
does not reduce to disc count because it sums a Z₂-invariant
quantity).  That probe is scoped as a Phase 1d item.

**H9 status: CONFIRMED as a disc-count-mediated effect with a
small residual spectral signal.**  Re-reading §9h' chess
against this Othello finding, the distinction between the
A₁-energy and A₁-signed-sum channels may be load-bearing for
the cross-game transfer of the complexity-vs-depth-gap
correlation.  The single-number headline (chess +0.452 vs
Othello +0.151) is misleading without this breakdown.

### 2c Summary

All four Phase 1c sub-phases land numeric results.  The headlines:

1. **1c.1 CONFIRMED** — OthelloBoard 100% agrees with Takizawa's
   reference bitboard engine across 2684 positions.
2. **1c.2 CONFIRMED (conditional)** — Shannon I_move vs A₁⁻
   energy is null globally (ρ = −0.065) but significantly
   positive on the in-book subset (ρ = +0.213, p = 2 × 10⁻⁸,
   N ≈ 676).  Novel: first direct connection between §10.10
   information-theoretic bookkeeping and §10.4 spectral
   decomposition, no direct chess analog.
3. **1c.3 PARTIAL (flagged)** — edax 50-empty anchor at N = 15
   matches shows ρ = +0.820, p = 1.8 × 10⁻⁴.  Large effect,
   small N; worth retesting at WTHOR scale.
4. **1c.4 CONFIRMED (disc-count-mediated)** — A₁⁻ energy vs
   |edax d=1 − d=20| Spearman = +0.151 (p = 1.6 × 10⁻¹²) on
   N = 2180.  Partial controlling for |disc_diff| collapses to
   +0.058 (p = 0.007).  Direction matches chess §9h' but the
   signal is mostly a disc-count artifact; chess §9h' partial
   did NOT collapse (chess A₁ *energy* is not a piece-count
   proxy, Othello A₁⁻ *magnetisation* largely is).  The cleaner
   chess-transfer analog uses the D₄-only A₁ projection of s²
   (occupation) — scoped as Phase 1d.

Remaining §10.10 tests (T4 T_eff / D_eff trajectory, T5 FK-BC
cluster fit) stay scoped to the sequel / external-data-dependent
work.  **Strict H9 / E8 are now runnable** following the arrival
of Takizawa's figshare knowledge archive — see §2d.

**Framework lesson carried forward.**  The "state richness vs
strategic structure" axis split (§10.13 in the chess notebook)
is the most reusable observation: Shannon I_move and sheaf λ₂
both track `n_legal_moves` at ~+0.77 to +0.81; A₁⁻ energy tracks
ρ_disc at +0.77.  Two independent axes of position description,
each with its own natural observable.  Chess counterpart
experiment has not been run; would benefit from a Phase 1d pass.

---

## 2d. Phase 1d — strict H9 / E8 against Takizawa perfect-play archive

The Takizawa figshare download (17 GB compressed → 171 GB decompressed
at a local drive path, outside repo) provides per-50-empty-position
knowledge files.  Each of 2587 canonical 50-empty positions has an
associated `knowledge_<OBF>.csv` containing every 36-empty sub-problem
reached from it under optimal play, with exact game-theoretic bound
pairs `(score_lb, score_ub)` and accuracy codes (100 = exact, 99 =
single-point acceptable).

The 2587-row small CSV `empty50_tasklist_edax_knowledge.csv` (already
committed under `dataset/reversi_scripts/` since Phase 1c) has the
pre-proof edax `score` prediction for each 50-empty position plus its
WTHOR frequency count.

### 2d.a Tasklist-scale correlation (N = 2587) — **CONFIRMED the predicted transfer channel**

Run: `python research/h9_strict_runner.py`.  Computes the D4-only A₁
projection of `s²` (the Z₂-invariant occupation observable that
Phase 1c.4 identified as the "cleaner chess-transfer analog" of A₁
energy), plus A₁⁻ magnetisation and the B₁/B₂/E channels, for every
2587 tasklist position.  Correlates with edax's predicted score.
Full per-position CSV in
[`results/phase1d_spectral_vs_perfectplay.csv`](results/phase1d_spectral_vs_perfectplay.csv);
aggregate JSON at
[`results/phase1d_correlations.json`](results/phase1d_correlations.json).

Headline correlations (N = 2587):

    raw:
      D4-only A1(s^2)     vs edax_score      = -0.349  p = 7.4e-75
      A1-                 vs edax_score      = +0.181  p = 1.5e-20
      B1, B2, E           vs edax_score      |rho| < 0.07, mixed significance
      D4-only A1(s^2)     vs |edax_score|    = -0.320  p = 1.7e-62

    partial (controlling |disc_diff|):
      D4-only A1(s^2)     vs edax_score      = -0.279  p = 2.3e-47   SURVIVES
      A1-                 vs edax_score      = -0.054  p = 6e-3      collapses
      E                   vs edax_score      = +0.075  p = 1.3e-4

**The predicted D₄×Z₂ Z₂-invariant channel carries robust spectral-
beyond-counting signal** (ρ = −0.279 partial, p = 2 × 10⁻⁴⁷, N =
2587).  This confirms the §2c.4 conjecture that the cleaner chess-
transfer analog uses the occupation projection rather than the
magnetisation projection.  The A₁⁻ magnetisation channel, consistent
with the Phase 1c.4 finding, collapses under the partial (ρ = −0.054)
— its raw correlation is a disc-count artifact.

**Direction.** Negative ρ means: positions with higher D4-symmetric
occupation structure tend to have lower edax predicted score (worse
for side-to-move).  At 50-empties (14 discs placed), this suggests
that tournament strategy prefers asymmetric configurations over
D4-symmetric ones, and edax's evaluator encodes that preference.

### 2d.b Strict augmentation via archive bounds — **CONFIRMED, stronger than 1d.a**

Archive scan completed: **2587 / 2587 knowledge files**, ~80-minute
walltime on the N:\\ mount, zero parse errors.  Per-parent aggregates
(mean / median / min / max of each file's 36-empty child
`score_lb` and `score_ub`) joined with the per-position spectral
observables; full summary in
[`results/phase1d_archive_summary.csv`](results/phase1d_archive_summary.csv).
Each 50-empty parent's file contained between ~300 k and ~600 k
36-empty children under Takizawa's proof tree — proved values
aggregated across that many positions per parent.

**Headline: the D₄-only A₁(s²) channel is a STRONGER predictor of
Takizawa's proved game-theoretic bound than of edax's pre-proof
predicted score**, and the effect survives the disc-count partial
control MORE robustly than the prediction version.

Raw Spearman correlations (N = 2587):

    D4-A1(s^2)  vs  edax_score            = -0.349   p = 7.4e-75
    D4-A1(s^2)  vs  archive_mean_lb       = -0.498   p = 1.7e-162   <== strongest
    D4-A1(s^2)  vs  archive_mean_ub       = -0.064   p = 1.1e-3
    D4-A1(s^2)  vs  archive_median_lb     = -0.405   p ~ 5e-100
    D4-A1(s^2)  vs  archive_median_ub     = -0.318   p ~ 1e-61

Partial Spearman controlling for |disc_diff|:

    D4-A1(s^2)  vs  edax_score            = -0.279   p = 2.3e-47
    D4-A1(s^2)  vs  archive_mean_lb       = -0.319   p = 4.4e-62    <== survives, stronger
    D4-A1(s^2)  vs  archive_mean_ub       = -0.163   p = 6.2e-17
    D4-A1(s^2)  vs  archive_median_lb     = -0.268   p = 6.3e-44

**Interpretation.**  The Z₂-invariant occupation projection captures
structural information about a 50-empty position that is more
aligned with its *true* game-theoretic value (as proved by
Takizawa's algorithm) than with edax's pre-proof heuristic guess.
Improvement from ρ = −0.349 (vs edax) to ρ = −0.498 (vs proved
lower-bound aggregate) is a 43 % relative gain in Spearman
magnitude; the partial version goes from ρ = −0.279 to ρ = −0.319
(14 % gain), confirming the signal is not a disc-count artefact.

The asymmetric behavior between `archive_mean_lb` (very strong)
and `archive_mean_ub` (much weaker) is structurally interpretable:
the lower bound aggregate represents the "worst case under optimal
play" for the side-to-move — a position's *defensive floor* — while
the upper bound aggregate is the "best case if opponent mistakes"
(often saturated at 64 for any reachable chain).  The spectral
observable tracks the defensive floor much better, suggesting it
encodes something like "how much optimal-play value this position
contains" rather than "how much tactical upside exists."

A₁⁻ magnetisation also shows modest negative partial correlations
with archive bounds (ρ ≈ −0.07 to −0.08), ~4× weaker than the
D₄-A₁(s²) signal.  B₁, B₂, E channels: near-zero, consistent with
the 1d.a finding.

**This is the strict H9 / E8 result that §2c.4's Phase 1c.4 caveat
predicted: an occupation-based (Z₂-invariant) observable needed to
find the chess-style A₁-energy-vs-depth-gap analog in Othello.  It
lands at N = 2587 and p ~ 10⁻¹⁶² — the largest-N and lowest-p
spectral-to-ground-truth correlation in this notebook or any of its
siblings.**

Open items for a Phase 1e or sequel:

- Does the effect generalise to other child-aggregate functions
  (variance, per-child correlation)?  Preliminary: mean is
  strongest, median survives the partial, min/max saturate at
  ±64 and are uninformative.
- Does the correlation transfer to earlier game phases (55- or
  60-empty positions) when larger corpora become available?  The
  Takizawa archive only covers 50-empty and 36-empty levels.
- Is there a cleaner chess-side analog experiment?  Chess lacks a
  weak-solution table, but the §9h′ fishtest corpus could be
  re-run with a Z₂-invariant D₄-only A₁(|signal|) projection
  paired with the Stockfish depth-20-vs-depth-12 gap; prediction is
  that the chess partial ρ against Stockfish would rise above the
  +0.456 A₁-energy baseline if the Othello structural finding
  transfers.
- Does the result hold for Takizawa's own accuracy-weighted scoring
  (weighting children by `accuracy = 100` vs `99`)?  The current
  aggregate includes both equally; an exact-only restriction would
  reduce N per parent but tighten the signal.

---

## 3. Dynamic fiber — sheaf Laplacian instantiation

[research/dynamic_sheaf.py](research/dynamic_sheaf.py) builds a
minimal Hansen-Ghrist sheaf Laplacian whose vertex stalks are the
3-state Blume-Capel fiber F(v) = R^3 carrying (empty, black, white)
one-hot components.  Edge stalks are R^3; restriction maps depend
on the cell state at the edge's endpoints (empty -> project onto
empty coordinate; friendly -> identity on that player's component;
opponent -> half weight, modelling an in-progress bracket).

The map is a crude surrogate — a more faithful construction would
make restrictions depend on the full bracket validity of the
segment, not just its endpoints.  We proceed with the crude
version to get a working spectral trajectory and leave faithful
implementation as sequel work.

### 3.1 Sample game trajectory

Random play from the starting position; 60 moves to terminal.
Per-move spectra:

    trajectory length: 60 moves
    rho range:         0.062 to 0.984  (monotonically increasing, as expected)
    sheaf lambda_2:    min = 0.223, max = 0.934, mean = 0.571
    sheaf entropy:     min = 3.881, max = 4.029
    kernel dim:        constant at 128 (2/3 of total dimension 192)
    legal-move count:  min = 1, max = 18

### 3.2 Correlations

    Spearman(rho, lambda_2)           = -0.008  (p = 0.95, uncorrelated)
    Spearman(legal_moves, lambda_2)   = +0.765  (p = 1.1e-12, strongly positive)

**The headline**: the sheaf spectral gap tracks **legal-move count**,
not disc density.  This is consistent with λ₂ measuring structural
connectivity of the flank graph — positions with many legal
placements have more "connected" flank structure, producing a wider
spectral gap.

**L7b caveat.**  The logo notebook's L7b retraction established that
a snapshot fiber does not necessarily extrapolate forward in time.
The sheaf spectrum reported here is a *per-move snapshot*; we have
NOT tested whether it predicts the spectrum 5 or 10 moves into the
future.  The correlation with legal-move count tells us the
spectrum varies with game state in a structured way; it does NOT
tell us the spectrum is a predictive summary of future state.  Any
sequel that uses the sheaf spectrum as a game-state summary must
test predictive power explicitly, following the L7b template.

### 3.3 What the sheaf-spectrum observable is good for

Based on the 60-move trajectory:

- **Positive**: discriminates "many-option" (midgame) from "few-option"
  (opening / endgame) positions at Spearman +0.77.
- **Null**: does not track disc-count filling independently of
  legal-move count.
- **Unknown**: whether the spectrum is a USEFUL observable depends
  on the sequel's validation tests.  If `spec(L_F(t))` is flat across
  legal moves at a given position, the sheaf adds no discriminative
  signal over the static fiber; if it varies meaningfully across
  positions with the same disc count, it does.

Preliminary indication: the spectrum varies more than flatly within
a 60-move trajectory (range `[0.22, 0.93]`), so the observable is
not trivially degenerate.

### 3.4 Kernel dimension

The kernel dim is constant at 128 across the trajectory.  This is an
artefact of the simplified restriction maps: empty cells project
onto a single coordinate, leaving two kernel directions per cell.
A faithful bracket-aware restriction should reduce the kernel at
positions with many contested rays.  Sequel work.

---

## 4. Phase-operator preflight — scaffold only

See [OTHELLO_PHASE_OP_PREFLIGHT.md](OTHELLO_PHASE_OP_PREFLIGHT.md)
for the full handoff document.  Candidate encoder dimensions,
placement generators, flip gate options, state-dependent gating
mechanisms, and ground-truth engine selection are documented there.

Recommended default: D = 768 with generators (7, 11), rank-2 fiber
motivated by the §9r polarization collapse.

---

## 5. WTHOR empirical tests — scaffold only

§10.10 tests 1–5 plus the A1 depth-gap transfer.  All require
external data not available in-session:

- T1 Flip-count distribution (power law vs exponential).
- T2 B1 vs B2 population asymmetry along game trajectories.
- T3 Shannon information per move.
- T4 Trajectory in (T_eff, D_eff) plane.
- T5 Flank-cluster size distribution vs FK-BC.

Preparation: `research/wthor_loader.py` is scoped but not yet
implemented; `research/perfect_play_compare.py` is similarly scoped.
Both are single-session tasks once the WTHOR .wtb file is
downloaded and the Takizawa Zenodo dataset is available.

---

## 6. Vocabulary collisions specific to Othello

- **"Flip"** — sign change on an opponent disc (`s -> -s`).  Distinct
  from **"flank"** (the geometric structure of the bracket) and
  **"bracket"** (the ray segment `same — opposite^+ — same`).
- **"Ray"** (direction, one of 8) vs **"line"** (a segment, possibly
  long, possibly empty).  The Laplacians in §1 are per-ray; the
  sheaf edges in §3 are per-segment.
- **"Fiber"** — adopted from chess §7; here means the non-spatial
  rule-coupling content of the 8-ray structure projected into the
  grid eigenbasis.  Unlike chess, the fiber is *dynamic*: its
  restriction maps evolve with the board state.
- **"Polarization"** — adopted from chess §9r.  In Othello the
  polarization reduces to `(theta-class, r = infinity, c = 0)` —
  a single excitation with 8 angle classes, infinite range (flip
  propagates until bracket close), zero chirality (Z₂ exact).

---

## 7. Appendix: Environment and reproducibility

- Python 3.12 (tested), NumPy, SciPy.
- Deterministic: all random-draw tests use `np.random.default_rng`
  with explicit seeds.  See individual functions in
  `research/consolidated_tests.py`, `research/dynamic_sheaf.py`.
- Wall time (this session, all tests run back to back on laptop):
  `consolidated_tests.py` ~3 s, `dynamic_sheaf.py` ~15 s.
- Reproduce Phase 0–2 with:

        cd docs/othello-maths/research
        python othello_utils.py
        python d4_z2.py
        python ray_laplacians.py
        python consolidated_tests.py
        python dynamic_sheaf.py

- Results land in `docs/othello-maths/results/`.  Notebook + preflight
  + instructions live at `docs/othello-maths/`.

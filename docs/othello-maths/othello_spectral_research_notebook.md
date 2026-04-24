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

**Interpretation — the 43 % gain, two readings.**  The raw Spearman
magnitude goes from |ρ| = 0.349 (spectral vs edax's pre-proof
heuristic score) to |ρ| = 0.498 (spectral vs Takizawa's proof-
grounded `archive_mean_lb`), a ~43 % relative gain (0.498 / 0.349
≈ 1.43).  The partial version goes from 0.279 → 0.319 (14 % gain),
confirming the signal is not a disc-count artefact.  Two possible
mechanisms contribute to the gain; they are NOT mutually exclusive
and a follow-up experiment is needed to disentangle them:

  - **Reading A — aggregation / noise-reduction.**  `archive_mean_lb`
    averages over 300 k – 600 k proof-grounded 36-empty child
    bounds per 50-empty parent.  Heavy averaging produces a smoother
    target than `edax_score`, which is a single pre-proof heuristic
    integer.  Spearman against a smoother target is naturally
    tighter.  Some fraction of the 43 % gain is a noise-floor
    effect on the y-variable, not a substantive property of the
    spectral observable.

  - **Reading B — alignment / substantive.**  The D₄-A₁(s²)
    projection is a simple linear functional of the occupation
    pattern with no search or heuristic content.  If it correlates
    with the *proved* game-theoretic value more tightly than with
    a strong engine's pre-proof *prediction* of that value, the
    spectral observable is genuinely picking up structural content
    aligned with ground truth that the engine's heuristic does not
    fully capture.  That would be a substantive statement about
    the D₄-A₁(s²) channel's informational content.

**How to separate the two readings (not yet run).**  Run edax at
matched deep search depth (e.g. d = 20, roughly comparable to the
effort of Takizawa's individual sub-problem solves) on the same
2587 positions and take that as a third target, `edax_d20_score`.

  - If ρ(spectral, edax_d20) ≈ ρ(spectral, archive_mean_lb), the
    43 % gain is mostly Reading A (aggregation / smoother target).
    The spectral observable agrees with ANY strong evaluator,
    pre- or post-proof, once noise is averaged down.

  - If ρ(spectral, edax_d20) is noticeably weaker than
    ρ(spectral, archive_mean_lb), Reading B is load-bearing: the
    spectral channel carries ground-truth-aligned content that
    even a strong deep-search engine doesn't fully capture.

At the time of this writing, only the pre-proof `edax_score` and
the proof-grounded `archive_mean_lb` are computed.  The deep-search
comparison is scoped as Phase 1e.1 (edax wrapper + runner are
already in place from Phase 1c.4 — `a1_depth_gap_runner.py`).

The earlier phrasing in an interim commit that the spectral channel
"knows more about the TRUE game-theoretic value than edax's
heuristic eval" was too strong — it conflated Reading B with the
narrower Reading-A-or-B ambiguity the data actually supports.  The
two-reading framing is the accurate one until the deep-search edax
comparison lands.

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

### 2d.c Deep channel analysis — the full D₄ battery on s² (post PATCH 6 audit)

The 1d.a and 1d.b passes reported A₁(s²) as the headline and
mentioned that B₁/B₂ on magnetisation came back null.  A follow-up
pass extended the observable battery to all FIVE D₄ irreps projected
onto the occupation s² signal (Z₂-invariant probes), plus all five
D₄×Z₂ '−' irreps on the magnetisation s signal (Z₂-odd probes).
Motivated explicitly by the question "after the PATCH 6 B₁/B₂
character-table fix, did we re-evaluate B₁/B₂ or just assume they
stayed null?"  Answer: on magnetisation they are null, but on
occupation the full D₄ battery contains a second strong signal we
had not reported.

**Complete post-fix channel table, raw Spearman vs `archive_mean_lb`
(N = 2587):**

| Channel | raw ρ | raw p | partial ρ | partial p |
|---|---|---|---|---|
| Magnetisation (Z₂-odd) |  |  |  |  |
| A₁⁻ | +0.187 | 8.6×10⁻²² | −0.069 | 4.4×10⁻⁴ |
| A₂⁻ | −0.006 | 0.76 | +0.000 | 1.00 |
| B₁⁻ | −0.015 | 0.45 | +0.004 | 0.86 |
| B₂⁻ | −0.041 | 0.04 | +0.009 | 0.65 |
| E⁻ | +0.073 | 2.1×10⁻⁴ | +0.102 | 1.8×10⁻⁷ |
| Occupation (Z₂-even) |  |  |  |  |
| **D₄-A₁(s²)** | **−0.498** | **1.7×10⁻¹⁶²** | **−0.319** | **4.4×10⁻⁶²** |
| D₄-A₂(s²) | +0.151 | 1.4×10⁻¹⁴ | +0.133 | 1.1×10⁻¹¹ |
| D₄-B₁(s²) | +0.148 | 3.5×10⁻¹⁴ | +0.074 | 1.6×10⁻⁴ |
| D₄-B₂(s²) | +0.034 | 0.08 | −0.007 | 0.73 |
| **D₄-E(s²)** | **+0.484** | **5.9×10⁻¹⁵²** | **+0.310** | **9.3×10⁻⁵⁹** |

**Two headline findings, not one.**  The raw-correlation
magnitudes sort into a striking pattern:

    Strong (|rho| > 0.3):   A1(s^2)  -0.498,   E(s^2)  +0.484
    Moderate (0.1-0.2):     A2(s^2)  +0.151,   B1(s^2) +0.148
    Null (|rho| < 0.05):    B2(s^2)  +0.034

Under the disc-count partial:

    Strong:     A1(s^2) -0.319,  E(s^2) +0.310
    Moderate:   A2(s^2) +0.133
    Weak:       B1(s^2) +0.074
    Null:       B2(s^2) -0.007

**D₄-E(s²) is the near-mirror of D₄-A₁(s²).**  Opposite sign,
magnitudes within 3 % of each other raw and within 3 % partial.
These are the two channels that carry essentially all of the
"spectral-beyond-counting" signal in the D₄ decomposition of the
occupation pattern, and they pull in opposite directions.

**Interpretation.**  The A₁ projection picks out the D₄-invariant
(fully symmetric) component of the occupation pattern — "how evenly
distributed the 14 discs are under all 8 spatial symmetries."  The
E projection picks out the D₄-covariant 2-dim (x, y)-transforming
component — "how much oriented anisotropy the occupation carries."
The mirror relationship is intuitive: positions with LESS uniform
fill (smaller A₁, worse for side-to-move) tend to have MORE oriented
fill (larger E, also worse for side-to-move), and vice versa.
Because D₄-A₁ + D₄-A₂ + D₄-B₁ + D₄-B₂ + D₄-E sums to the full
occupation norm (Plancherel), a decrease in one channel must be
compensated by an increase elsewhere; the A₁/E pair soaks up the
dominant trade-off.

**Multivariate implication.**  If A₁(s²) and E(s²) partially
cancel each other, their DIFFERENCE `D4-A1 - D4-E` (or any rotation
in the 2-D span) might be a sharper univariate predictor.  Both
channels individually explain ~10 % of the variance in
`archive_mean_lb` (partial R² ≈ 0.32² ≈ 0.10 each); combined they
might explain 25–30 %.  A multivariate regression on these two
alone is scoped as a Phase 1e item.

**B₁(s²) / B₂(s²) asymmetry revisited.**  In chess, the PATCH 6
reprocess of [`archive/chess_a1_followup.py`](../chess-maths/archive/chess_a1_followup.py)
on 2026-04-23 (55-position hand-picked depth-gap corpus, Stockfish
d=1 vs d=20) gave B₂ partial ρ = +0.490 against |depth_gap| — the
single strongest complexity predictor in THAT sample, beating A₁ at
+0.456 (chess §9h′ Table 1).  In Othello B₁/B₂ on either signal
(magnetisation or occupation) at N = 2587 vs Takizawa proved bounds
are essentially null.

**Scope caveat.**  The chess "B₂ is the best predictor" claim is
based on a single 55-position corpus, not on a broader Stockfish-
matched post-PATCH-6 corpus.  A chess-side batch is in flight
(see `docs/chess-maths/results/sweep_chain_lichess_ashchess_2026-04-21_N50/`)
re-encoding a 50-game lichess sample on post-fix characters; the
corpus-level aggregates (`corpus_index.csv`) and per-ply Stockfish
correlations have not been regenerated from the re-encoded spectralz
at the time of this notebook edit.  **A structural sanity scan on
the 20-game post-fix spectralz subset did confirm:**

- 1953 plies scanned, **99.7 % show B₁ ≠ B₂** (the correct post-fix
  signature; bug would pin the ratio near 100 % equal).
- Mean channel energies in that subset: A₁ = 18.94, B₁ = 12.65,
  **B₂ = 32.66** (B₂ is the largest channel by mean), consistent
  with B₂ being an active complexity channel at chess-corpus scale
  — but **not yet confirmed as the strongest Stockfish predictor**
  at that scale.

So the chess vs Othello structural-divergence claim ("chess B₂
carries piece-species content; Othello has one disc type so the
B₁↔B₂ swap has no modulation") is defensible on theory plus the
55-position empirical anchor; confirmation at broader corpus scale
is pending the chess-side re-correlation batch.

**Structural interpretation of the divergence (theory-side).**  The
chess B₂ signal captures diagonal-sliding vs orthogonal-sliding
structure across piece species — rook-like adjacency in the ortho
orbit vs bishop-like in the diag orbit, with the "which-orbit"
distinction carrying strategic content about pawn structure and
piece mobility.  Othello has a single disc type, so the B₁↔B₂
swap has no piece-species content to modulate.  The orthogonal-vs-
diagonal RAY structure still exists (it sits in the H2 8-ray
decomposition `2 A₁ + B₁ + B₂ + 2 E`), but a single 50-empty
configuration of 14 indistinguishable discs projects into B₁(s²)
and B₂(s²) as close to random-signal noise once disc count is
controlled — no structural lever amplifies the anisotropy.

This is the structural interpretation of the §10.4 rank-6 irrep
count not showing up as an operator rank: B₁ and B₂ are real
geometric modes of the 8×8 grid, but they need piece-species or
directional-movement content to carry strategic signal.  Othello
provides neither.

**B₁(s²) moderate partial (ρ = +0.074) as a ghost signal.**  It
is not null — raw +0.148, partial +0.074 with p = 1.6×10⁻⁴ — but
it is ~4× weaker than A₁(s²) and E(s²).  Most likely explanation:
B₁ picks up edge/corner vs centre occupation asymmetry on the 8×8
grid (transforms as x² − y²), and tournament play at 50-empties
has a mild systematic bias toward centre-filled configurations.
Not a headline, but worth noting as a weak corroborating signal
alongside A₁ and E.

### 2d.d A₂(s²) — a third meaningful channel (weaker than A₁/E)

The D₄-A₂(s²) channel transforms as R_z (rotation about the board
normal) and is invariant under rotations but sign-flips under
reflections.  Partial ρ = +0.133, p = 1.1×10⁻¹¹ at N = 2587.  Not
as strong as A₁ or E but clearly above noise and with a tight
p-value.  Combined with A₁/E, the 2d battery on occupation has three
channels with meaningful signal.  The full channel-energy vector
(A₁, A₂, B₁, B₂, E) on s² could be a 5-D encoding of "structural
content of occupation" worth testing in a downstream classifier.

### 2d.e Chess vs Othello cross-game comparison (post-PATCH-6, both sides)

Cross-game comparison is now meaningful — PR #57 landed chess §9c′
(corpus-level post-fix B₁/B₂ analysis, 23 games across 4 lichess
corpora) on main on 2026-04-23, with the chess `manifest.json` /
`corpus_index.csv` / `corpus_summary.md` all regenerated from post-
fix spectralz.  The matched-Stockfish per-ply chess correlation is
still a pending batch item (referenced in chess §9c′ but not yet
computed against the re-encoded spectralz), but the structural
channel-level numbers are available on both sides.  Static
structural comparison only; game-theoretic-value correlation
comparison deferred until chess Stockfish re-correlation lands.

#### Similarities — universal grid-topology properties

Both chess (static §9c′ 23-game sample) and Othello (N = 2587
Takizawa 50-empty positions) show:

1. **B₂ > B₁ in mean energy**, at a consistent ratio:
   - Chess B₂/B₁ ≈ 1.4–1.7× across all four corpora (nykt 1.69,
     ash 1.68, hf 1.52, single 1.35; chess §9c′.2).
   - Othello B₂⁻/B₁⁻ = **2.01** (magnetisation), D₄-B₂(s²)/D₄-B₁(s²)
     = **1.82** (occupation).
   - Structural interpretation: the diagonal-orbit vs orthogonal-
     orbit asymmetry of the 8×8 grid under standard occupation
     patterns (initial position, tournament fills) favours B₂.
     Independent of piece-species / single-species structure.

2. **B₁ and B₂ projections are exactly orthogonal per-ply.**  Chess
   §9c′.1 measures Frobenius cos(B₁, B₂) = 0.0000 over 2112 plies.
   Othello H3 shows the same via direct grid-topology argument
   (`E_ortho ∩ E_diag = ∅`).  Identical structural fact on both
   games.

3. **E is the largest D₄ channel by mean energy.**  Chess E mean
   11–14 across corpora vs A₁ mean 3.9–4.9 and B₂ mean 4.9–5.9.
   Othello E⁻ mean 7.2 vs A₁⁻ mean 2.7 vs B₂⁻ mean 2.3.  E/A₁
   ≈ 2.7× and E/B₂ ≈ 2–3× on both sides.

4. **A₁ and E anti-correlate** in both games, but magnitude differs:
   - Chess corr(A₁, E) = **−0.293** (moderate; §9c′.4).
   - Othello corr(A₁⁻, E⁻) = **−0.532** (on magnetisation).
   - Othello corr(A₁(s²), E(s²)) = **−0.834** (on occupation — the
     near-mirror we flagged in §2d.c).
   - Interpretation: A₁ and E decompose the full D₄ occupation
     energy into "fully symmetric" vs "2D (x, y)-oriented"
     components and trade off under Plancherel.  Chess's signal
     carries additional content from the fiber channels
     (FS1, FS2, FS3, FA, FD) that dilutes the A₁/E anticorrelation;
     Othello's single-disc-type signal concentrates the trade-off
     into exactly two D₄ channels, producing the tighter −0.83
     mirror.

#### Divergences — piece-species content as the amplifier

Chess B₁/B₂ and Othello B₁/B₂ behave very differently once we
look beyond mean energy into cross-channel structure and strategic
content:

1. **Cross-channel correlation structure is opposite-signed on
   (A₁, B₁).**

   | Pair | Chess ρ (§9c′.4, raw signal) | Othello ρ (D₄/s² channels) |
   |---|---|---|
   | (A₁, B₁) | **+0.575** | **−0.299** |
   | (A₁, B₂) | +0.221 | −0.230 |
   | (A₂, B₂) | +0.358 | −0.003 |
   | (A₁, E)  | −0.293 | −0.834 |

   **Chess B₁ co-moves with A₁** ("symmetric-fiber-aligned" per
   §9c′.4), while **Othello B₁(s²) anti-correlates with A₁(s²)**.
   The sign flip on the (A₁, B₁) pair is the sharpest structural
   divergence.  It reflects the Plancherel accounting: in chess
   the signal has many channels (5 D₄ irreps + 5 fiber channels =
   10 total, 640 dims) and A₁/B₁ can co-move without exhausting
   the norm budget; in Othello the 5 D₄ occupation channels alone
   account for most of the norm, so A₁(s²) and B₁(s²) compete for
   the same budget and anti-correlate.

2. **Strategic content on B₂ is chess-specific.**  Chess §9h′ Table
   1 (55-position hand-picked depth-gap corpus, post-PATCH-6) puts
   B₂ partial ρ = +0.490 against |depth_gap|, the strongest
   single-channel complexity predictor there.  Chess §9c′.5
   decomposes this by move type: rooks and kings excite B₂
   preferentially (×1.28 and ×1.53), **castling produces a ×2.05
   B₂ spike** — castling is the archetype of σᵥ-symmetry breaking
   and B₂ is the σᵥ-antisymmetric channel.  Othello has no castling,
   no piece species, no rook/king asymmetry.  Its D₄-B₂(s²) partial
   ρ = −0.007 (p = 0.73) against Takizawa's archive_mean_lb is
   genuinely null.  **The structural ray geometry is shared, but
   the strategic amplification requires piece-species or
   directional-movement content to show up.**

3. **The "useful" headline spectral channel differs.**
   - Chess (narrow §9h′ sample): B₂ on raw piece-value signal;
     partial ρ = +0.490 vs |depth_gap|.
   - Othello (Takizawa-strict N = 2587): D₄-A₁(s²) and D₄-E(s²)
     on occupation; partial ρ = −0.319 and +0.310 vs archive_mean_lb.
   - Both findings are "spectral beyond counting" — they survive
     the disc-count / piece-count partial control.  They just
     live on different (signal, irrep) coordinates.

#### Framework reading

The cross-game picture is:

- **Static D₄ grid geometry is universal**: B₂ > B₁, A₁/E
  anti-correlate, B₁ ⊥ B₂.  Both games inherit this from the
  8×8 grid topology, no piece-species amplification needed.
- **Strategic signal on the B-irreps is piece-species-dependent**:
  chess B₂ carries rook-vs-king / castling-vs-plain content that
  Othello's single-disc-type play has no analog for, so chess B₂
  becomes the complexity headline while Othello B₂ is inert.
- **Strategic signal on the A₁/E axis transfers**: chess A₁ energy
  (§9h′ +0.452 partial vs depth_gap) and Othello A₁(s²) energy
  (−0.319 partial vs archive_mean_lb) are both "fully-symmetric"
  invariants of their respective occupation signals, and both
  predict ground-truth-aligned quantities.
- **The E channel's partial ρ matches A₁'s in magnitude with
  opposite sign on the Othello side** (+0.310 vs −0.319).  Chess
  §9c′ does not yet have an E/depth-gap partial; the corpus-scale
  Stockfish re-correlation batch (in flight) may find a symmetric
  A₁/E twin result if the Othello framing transfers.

Pending confirmation items (each requires the chess Stockfish
re-correlation batch to land):

- Chess post-fix B₂ partial ρ at corpus scale vs |depth_gap| /
  |eval_change| — does the §9h′ +0.490 hold at ~2000 plies, or
  was that a hand-picked-corpus artefact?
- Chess post-fix E partial ρ vs |depth_gap| — does the Othello
  A₁/E mirror have a chess analog?
- Chess post-fix A₁/E cross-channel Pearson at corpus scale —
  does the Othello −0.83 have a chess analog, or is the tight
  mirror an Othello-specific consequence of single-species signal?

None of these are blockers for the §2d.c A₁/E-twin claim; they
add a chess-side symmetry check if the framework transfers.

### 2d summary (updated after deep channel analysis)

1. **D₄-A₁(s²) and D₄-E(s²) are the twin headline channels**,
   opposite signs, ~0.32 partial ρ magnitude each against Takizawa
   proved bounds, p values of 10⁻⁶² to 10⁻⁵⁹.  Together they carry
   the bulk of the Z₂-invariant spectral-beyond-counting signal.
2. **D₄-A₂(s²) is a supporting third channel** at partial
   ρ = +0.13.
3. **D₄-B₁(s²) is a weak fourth channel** at partial ρ = +0.07.
4. **D₄-B₂(s²) is genuinely null** in Othello, in contrast to
   chess B₂ on the 55-position §9h′ hand-picked depth-gap corpus
   where partial ρ = +0.49 against |d1−d20| beats A₁ (+0.456).
   The chess claim is narrow to that corpus; broader post-fix
   chess-side re-correlation (50-game lichess sweep) is in
   flight and its corpus_index / Stockfish tables had not been
   regenerated from post-fix spectralz at the time of this edit.
   Structural reading: chess B₂ needs piece-species content to
   carry signal, Othello's single disc type kills that modulation.
5. **All magnetisation-side projections collapse under the
   disc-count partial control**, consistent with the Phase 1c.4
   finding that Othello A₁⁻ is a disc-count proxy.

Revised framework statement: **the useful spectral observables for
Othello perfect-play correlation live in the D₄-only projection of
the Z₂-invariant occupation signal s², not in the D₄×Z₂ projection
of the magnetisation signal s.**  This cleanly separates Othello
from chess, where magnetisation-based A₁ energy remains the
complexity headline.  The chess-style "A₁ energy" and Othello-style
"D₄-A₁(s²)" are structurally analogous — both are the fully-
symmetric irrep on the Z₂-invariant aggregate — but they live on
different Z₂ parities of the underlying signal because Othello's
piece content is Z₂-invariant (single particle type) while chess's
is not (piece-species polarizes the signal).

---

## 2e. Phase 1e — follow-ups, encoder, C-parity, sheaf-as-reference

Phase 1e extends 1d in five parallel tracks.  Full per-item detail
in the running doc
[PHASE_1E_FINDINGS.md](PHASE_1E_FINDINGS.md); this section is the
notebook-level summary with status tags.

### 2e.1 Multivariate A₁(s²) + E(s²) — **CONFIRMED** the Plancherel pair

[phase1e_multivariate.py](research/phase1e_multivariate.py).
Joint OLS at N=2587: (A₁, E) gives R² partial 0.100; full D₄
5-channel adds only +0.012.  The A₁ − E rotated direction at 135°
lands partial ρ = +0.337, marginally stronger than A₁ alone.  The
A₁ + E (45°) direction is near-null (−0.038), confirming the
§2d.c mirror.

### 2e.2 edax d=20 on the 2587 tasklist — **Reading B CONFIRMED**

[phase1e_edax_d20_tasklist.py](research/phase1e_edax_d20_tasklist.py),
[phase1e_edax_d20_correlations.py](research/phase1e_edax_d20_correlations.py).
Spearman(D₄-A₁(s²), edax_d20) = −0.342 — essentially identical to
pre-proof edax_score (−0.349, gap of 0.007).  Both are ~35 % short
of the archive_mean_lb correlation (−0.498).  **The 43 % gain in
§2d.b is not a search-depth artifact** — deep-search edax doesn't
bridge the gap.  Reading B (the spectral channel sees structural
content beyond deep-search heuristics) is load-bearing.

### 2e.3 Shannon info × D₄-A₁(s²) — **retraction via Simpson**

[phase1e_shannon_observables.py](research/phase1e_shannon_observables.py),
[phase1e_signflip_decomposition.py](research/phase1e_signflip_decomposition.py).
Initial §2c.2 headline Spearman(I_move, A₁⁻) = +0.213 doubles to
+0.465 when the D₄-A₁(s²) observable replaces A₁⁻.  §1e.6
decomposition by n_empties bucket then shows both aggregates are
**Simpson's paradox** artifacts of game-phase structure — within
any single phase bucket, A₁⁻ correlates NEGATIVELY with I_move
(opening in-book −0.274, late-midgame in-book −0.419).  The
"A₁⁻ tracks strategic divergence" framing in §2c.2 is retracted.

### 2e.4 Predictive sheaf (§3 L7b caveat) — **target-specific trajectory memory**

[phase1e_predictive_sheaf.py](research/phase2_predictive_sheaf.py),
[phase1e_predictive_sheaf_pgn.py](research/phase1e_predictive_sheaf_pgn.py),
[phase1e_predictive_sheaf_faithful.py](research/phase1e_predictive_sheaf_faithful.py),
[phase1e_faithful_gain_investigation.py](research/phase1e_faithful_gain_investigation.py).

The sheaf spectrum carries FORWARD-PREDICTIVE content — contra
logo §L7b.5.  On 30-seed random-play trajectories, sheaf λ₂ at
time t predicts `n_legal_moves(t+10)` with R² = 0.56, matching
sheaf λ₂ at t+10.  Gain vs persistence baseline grows from +0.24
(Δ=1) to **+0.49 (Δ=10)**.  On the 2178-game 2025 tournament
corpus the pattern replicates, but at scale the picture sharpens:
**trajectory memory is target-specific.**

  target                        Δ=10 gain_vs_snap (2025)
  d4_e_occupation_energy        **+0.159**
  d4_a1_occupation_energy       +0.070  (grows to +0.150 @ Δ=20)
  rho                           +0.079  (grows to +0.154 @ Δ=20)
  n_legal_moves                 +0.012  (near-zero)
  a1_minus_energy               **−0.041**  (snapshot wins)

Train/test split (1089 train, 1089 test) confirms the signature
is not overfit (OOS gain LARGER than in-sample on most targets).
Per-feature ablation shows the effect is **joint feature
decorrelation**: at time t the 8 sheaf features (λ₂/entropy/
kerdim/λmax × owner) encode diverse trajectory-relevant info;
at t+Δ they collapse to redundant current-state summaries.

### 2e.5 Faithful sheaf restriction maps — **bracket-aware**

[faithful_sheaf.py](research/faithful_sheaf.py).  Replaces §3's
endpoint-only crude restriction with an R1/R2/R3/R4 bracket
classifier: edges exist only across active flanks (R2 stable,
R3 pending).  **Breaks §3.4's constant-128 kernel artifact** —
faithful kernel dim is position-dependent (141–188 on seed=123).
λ₂ differs from crude by mean +0.29.  The per-cell R3_PENDING
count, projected through D₄, becomes the headline observable in
2e.6.

### 2e.6 Sheaf-derived D₄ channels beat occupation by 40 % — **NEW HEADLINE**

[phase1e_sheaf_vs_archive.py](research/phase1e_sheaf_vs_archive.py)
at N=2587.  Against Takizawa's `archive_mean_lb`:

  channel                                  raw ρ    partial ρ
  D₄-A₁(s²)      §2d.b baseline            −0.498   −0.319
  D₄-E(s²)       §2d.b baseline            +0.484   +0.310
  **E_pending_white_A1**   sheaf-derived   −0.621   **−0.447**
  E_degree_white_E         sheaf-derived   +0.638   +0.429
  E_pending_black_A1       sheaf-derived   +0.224   +0.370
  E_pending_black_E        sheaf-derived   +0.565   +0.362

The per-cell **pending white** bracket count, projected through
D₄-A₁, lifts the partial ρ magnitude from 0.319 to **0.447** — a
40 % improvement.  Sign interpretation: many white-side pending
flanks ⇒ bad news for side-to-move (BLACK on the tasklist) ⇒
lower `archive_mean_lb`.

Consequence: sheaf-derived channels are promoted to the encoder's
reference fiber layout (v0.3.0).  Channels 10-11 of the 768-dim
encoding are now `sheaf_pending_black` and `sheaf_pending_white`
instead of `L_ortho @ s` / `L_diag @ s`.  The legacy rank-2
(orbit-Laplacian) fiber remains available via
`encode_768(state, fiber_mode="rank2")` — and is what the C
reference encoder supports until the bracket walker is ported
(2e.7).

### 2e.7 C encoder + bit-identical engine dispatch

[othello_spectral/c_encoder/](research/othello_spectral/c_encoder/),
[othello_spectral/codegen/emit_c_tables.py](research/othello_spectral/codegen/emit_c_tables.py),
[othello_spectral/runtime.py](research/othello_spectral/runtime.py).

ANSI C17 reference encoder with `clang -Wall` clean build.
Python-side ctypes path (v0.3.0): loads `othello_spectral.dll`,
direct-calls `othello_spectral_encode_768` — no subprocess
overhead.  Benchmarks (APR 2026, 25 447 states):

  path                encode  wall
  python              3.0 s   18.4 s
  c (ctypes DLL)      3.1 s   17.8 s
  c (subprocess exe)  7.6 s   21.7 s

All three paths are bit-identical on rank-2 fiber.  Parity test
[tests/test_c_py_parity.py](research/othello_spectral/tests/test_c_py_parity.py)
compares 9 states at float32 precision (subprocess) and float64
(ctypes).  Sheaf-fiber C port is a future item (the bracket
walker in `faithful_sheaf.py` is Python-only).

Engine dispatch: `--engine {py, c, auto}`, env vars
`OTHELLO_SPECTRAL_BIN` / `OTHELLO_SPECTRAL_DLL` /
`OTHELLO_SPECTRAL_ENGINE`; `auto` mode verifies the C binary
against Python (version + smoke test) before selecting, silent
fallback on any failure.  When `--fiber sheaf` is active the C
path is skipped (rank2-only).

### 2e.8 T1 flip-count + T5 chain-size — **exponential at corpus scale**

[phase1e_flipcount_distribution.py](research/phase1e_flipcount_distribution.py),
[phase1e_t5_cluster_distribution.py](research/phase1e_t5_cluster_distribution.py).

Both §10.10 T1 (per-move flip count) and T5 (per-chain same-colour
run length) **reject the power-law** prediction across all four
committed PGN corpora (WC 2005, Barcelona 2026, APR 2026, 2025
all — 23 to 2178 games each).

  T1 (flip-count):       all 4 corpora prefer exponential by
                         ΔAIC 3 k to 346 k;  λ ≈ 0.548;  mean 2.37
  T5 (chain length):     all 4 corpora prefer exponential by
                         ΔAIC 3 k to 221 k;  τ ≈ 2.68 (close to
                         FK-BC critical τ ≈ 2.05 but exp wins);
                         mean 2.94, max 8

Remarkably stable across a 20-year span and 3 orders of magnitude
of N.  Strategic play does not shift these distributions from
random-play expectation (§2.E5 mean 2.28).

### 2e.9 T4 thermodynamic trajectory — **negative T_eff robust**

[phase1e_t4_thermodynamic_trajectory.py](research/phase1e_t4_thermodynamic_trajectory.py),
[phase1e_t4_robust.py](research/phase1e_t4_robust.py),
[phase1e_t4_logtransform.py](research/phase1e_t4_logtransform.py).

Per-ply T_eff = dE_tot / dS_eff heavy-tailed (median −11 k, mean
+70 k on Barcelona).  Windowed OLS on high-R² windows: median
−22 k with IQR [−35 k, −14 k].  Log-transform log(E_tot) vs S_eff:
median slope −6.04 with IQR [−8.48, −4.28] — robust negative
signal, interpretable as "1 unit increase in Shannon entropy
corresponds to factor exp(−6.04) ≈ 0.002 change in E_tot."

Structurally consistent with §2d.c's A₁ / E mirror: as spectral
energy grows with disc count, the channel-energy distribution
concentrates (Shannon entropy shrinks).

### 2e.10 Holonomy structural map — **Z₂ holonomy exclusive to lj_rect_W×1, W≥3**

[phase1e_holonomy_plaquettes.py](research/phase1e_holonomy_plaquettes.py).
Enumerated 1192 loops across 7 shape families on the 8×8 static
fiber bundle.  Exactly **105 / 1192 loops carry Z₂ holonomy
(cos = −1)**, and they are ALL of shape `lj_rect_Wx1` with W ≥ 3
(long-jump rectangles of height 1).  All other 1087 loops are
trivial.  The effect is path-orientation-dependent, not homotopy
invariant: lj_rect_1×H (transpose) is trivial.

Generalises §2.H5's single-loop finding (the 0,0→0,3→1,3→1,0
rectangle, one of the 35 lj_rect_3×1 instances) to the full
curvature map.

### 2e.11 Chess vs Othello A₁ / E — **Simpson's paradox mechanism**

[phase1e_chess_a1_e_pair.py](research/phase1e_chess_a1_e_pair.py),
[phase1e_chess_a1_e_bootstrap.py](research/phase1e_chess_a1_e_bootstrap.py),
[phase1e_simpson_mechanism.py](research/phase1e_simpson_mechanism.py),
[phase1e_othello_a1_e_per_game.py](research/phase1e_othello_a1_e_per_game.py).

§2d.e deferred the chess A₁/E correlation check pending
Stockfish re-correlation.  Completed here via direct chess-
spectral spectralz extraction at N=10 729 plies.

  species            pooled   within   between
  chess/ashchess     +0.011   −0.117   **+0.667**
  chess/drnyk        −0.201   −0.315   **+0.605**
  chess/hf           +0.116   +0.022   **+0.663**
  othello/2025 magn  +0.330   +0.385   **−0.479**
  othello/2025 occ   −0.072   −0.051   **−0.592**

Between-game Pearson of game-means is the dominant contribution
and has OPPOSITE sign between the two species:

  - Chess: between +0.60 to +0.67 — games with high mean A1 also
    have high mean E.  Pooled ≈ 0 because positive between and
    slight negative within partially cancel.

  - Othello magnetisation: between −0.48 — games with high mean
    A1⁻ have LOW mean E⁻.  Pooled positive because within-game
    co-correlation (+0.39) outweighs.

  - Othello occupation: between −0.59, within −0.05.  Driven by
    between-game baseline structure.

The Othello §2d.c 50-empty static Pearson of −0.834 is a
**phase-specific 14-disc configuration** property, not a general
trajectory signature.  Per-game trajectory-level A₁/E is
game-species-specific.  The Plancherel-budget reading (fewer
channels in Othello ⇒ tighter mirror) only holds at the static
50-empty cross-section.

### 2e.12 Sheaf-phased encoder v0.3.0 benchmark — **sheaf is new reference**

Pulls together 2e.5 + 2e.6 + 2e.7: the faithful-sheaf pending-
bracket channels replace the v0.2.0 orbit-Laplacian fiber.
Default encoder now v0.3.0 sheaf-default; rank-2 mode survives
as `fiber_mode="rank2"` for C parity.

  fiber mode      partial ρ vs archive_mean_lb (A1 channel)
  rank2 (v0.2)    D4-A1(s^2)           −0.319
  sheaf (v0.3)    D4-A1(pending_white) **−0.447**   (40 % gain)

### 2e.13 C sheaf port — bit-identical v0.3.0/0.3.1 parity + 25× speedup

[othello_spectral/c_encoder/src/othello_spectral.c](research/othello_spectral/c_encoder/src/othello_spectral.c)
gains `classify_ray` + `sheaf_pending_counts` (~80 lines,
direct port of `faithful_sheaf.classify_ray`).  New public
API `othello_spectral_encode_768_v2(state, fiber_mode, out)`
with `fiber_mode ∈ {FIBER_RANK2, FIBER_SHEAF}`; legacy
`encode_768` retained as alias for rank-2.  CLI + ctypes
wrappers thread `--fiber {rank2, sheaf}` through.  Tests at
v0.3.1 verify **36 bit-identical py/c comparisons** (2 fiber
modes × 2 C paths × 9 states) at float32 (subprocess) and
float64 (ctypes).

End-to-end on 35-game Barcelona corpus:

  path                        encode   wall
  py (fiber=sheaf)            5.0 s    7.0 s
  c ctypes DLL (fiber=sheaf)  0.2 s    2.4 s     **25× encode speedup**

Byte-identical .spectralz SHA256 = `461bd1219357041a`.

### 2e.14 s-vs-s² asymmetry mechanism — three-regime structural explanation

[phase1e_s_vs_s2_asymmetry.py](research/phase1e_s_vs_s2_asymmetry.py)
runs four per-game diagnostics on 2178 games of 2025 corpus:
volatility, lag-1 autocorrelation, Pearson with disc-count,
monotone fraction.

  target                  volatility  autocorr1  r_disc   mono_frac
  a1_minus_energy            +0.236    +0.842    +0.755    0.550
  d4_a1_occupation_energy    +0.051    +0.9996   +0.991    1.000
  d4_e_occupation_energy     +0.277    +0.961    +0.083    0.500
  rho                        +0.056    +1.0000   +1.000    1.000
  empty_count                +0.056    +1.0000   −1.000    1.000

Three regimes fully account for the §1e.7.4b trajectory-memory
gain pattern:

  1. **Game-clock monotone** (ρ, empty_count, d4_a1_occ) —
     trivially predictable.  The sheaf "predictive gain" for
     these is a disc-count correlation artefact.

  2. **Non-monotone structural** (d4_e_occ, r_disc = +0.083).
     **Genuine trajectory memory.**  The sheaf's pending-bracket
     count predicts how oriented occupation anisotropy evolves
     because active flanks drive directional shifts.

  3. **Turn-order-coupled** (a1_minus).  The sheaf captures
     WHAT happens structurally (brackets) but not WHO places/
     flips the disc.  Sign of A1⁻ depends on turn order; the
     bracket classifier doesn't encode that → snapshot wins.

Z₂ representation theory doesn't explain it; the distinction
is target's coupling to (disc count, turn order), not Z₂ parity.

### 2e.15 Sheaf-phased operator — **12 % additional gain over §2e.6**

[othello_spectral/phase_operator.py](research/othello_spectral/phase_operator.py).
The first concrete instantiation of a §4-style phase operator
for Othello.  Applies a state-dependent diagonal scaling D(f(state))
to the encoding vector, where f maps sheaf spectrum features
(λ₂, λ_max, entropy, kerdim per owner) to channel weights.

Four modes provided (v0.3.1):

  - `identity`               no-op baseline
  - `scale_fiber_by_owner_lambda2`   weight fiber channels by 1/(1+λ₂^{owner})
  - `scale_all_by_kernel_dim`        weight all channels by ⟨kerdim⟩/192
  - `rotate_E_by_entropy`            cos(entropy_B) damping of E channels

Benchmark on 2587 tasklist against archive_mean_lb:

  mode                            fiber_pw through D4-A1 partial ρ
  identity (baseline Exp 1)                  **−0.447**
  scale_fiber_by_owner_lambda2               **−0.503**   (+12 % gain)
  scale_all_by_kernel_dim                    −0.449
  rotate_E_by_entropy                        −0.447

`scale_fiber_by_owner_lambda2` lifts the partial ρ magnitude
from 0.447 to **0.503** — another 12 % on top of the 40 % gain
sheaf fiber gave over occupation in §2e.6.  Total improvement
over the §1d.b baseline D₄-A₁(s²) (ρ = −0.319):
**0.503 / 0.319 ≈ 58 % cumulative gain.**

Interpretation: λ₂ of each owner's faithful sheaf Laplacian
measures the algebraic connectivity of that owner's bracket
graph.  Dividing the per-cell bracket counts by 1 + λ₂ normalises
for "how busy" the bracket network is, letting per-cell
structure drive the correlation rather than total activity.

Framework is minimal — diagonal scaling only.  Phase operators
with off-diagonal coupling (SO(2) rotations within the E
subspace, state-dependent mixing between channels) are future
work.  The current module is pure Python; C port would need
sheaf eigendecomposition (scipy eigh; not bit-identical across
LAPACK versions, so the operator is platform-reproducible but
not bit-portable at v0.3.1).

Open items (updated after this pass):
  - Port faithful_sheaf.classify_ray to C — **CLOSED** (2e.13)
  - Z₂-cancellation Exp 2 on Barcelona — **CLOSED** (2e.14)
  - Sheaf as phase-operator coupling — **CLOSED** (2e.15)

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

# Othello Phase-Operator Preflight

**Status:** scaffold / handoff document.  Produced at the end of the
Phase 0–2 Othello verification session (branch
`othello-spectral-foundations-v0.1.0`).  The next prompt in this
chain — the Othello analog of `chess-maths/PHASE_OPERATOR_SUPPLEMENT.md`
§11.2 — absorbs this document and builds the phase-operator move
engine.

The point of this doc is to answer the preflight questions so the
sequel can be written cleanly.  It is *not* a specification of the
phase operators themselves; it is a decision log about the parameters
the sequel will commit to.

---

## 1. Candidate encoder dimensions

From `research/coprime_generators.py` (verified Phase 1, §2.H7).
`k_dct = 10` channels for D₄×Z₂ irrep projections.  `D = (rank + 10) × 64`.

| Fiber rank | D    | (row_gen, col_gen) | 64 phases distinct? |
|------------|------|--------------------|---------------------|
| 2 (orbit count: ortho vs diag)       | 768  | (7, 11)  | yes |
| 6 (irrep count: 2 A1 + B1 + B2 + 2 E) | 1024 | (3, 11)  | yes |
| 8 (individual ray directions)        | 1152 | (7, 11)  | yes |

Generators chosen by exhaustive search over small primes coprime to `D`
and to the forbidden set {2, 5}, minimising `row_gen + col_gen` subject
to the 64-phase-uniqueness constraint.  All three candidates admit
valid generators.

**Recommendation for the sequel.**  The rank-2 candidate (D = 768) is
the simplest and most directly motivated by the polarization
reframing of §9r — Othello reduces to `(theta-class, r = infty, c = 0)`
with only the `theta-class` degree of freedom populated, and the
natural split of `theta-class` into orthogonal-orbit vs diagonal-orbit
gives two fiber channels.  Build the sequel's default encoder at
D = 768 and keep D = 1024 and D = 1152 available as ablations.

The H6 empirical readout (`results/phase1_detail.json`):
- Undirected ray-Laplacian stack: effective rank 4 (pairs coincide
  because L_d = L_{-d} for undirected graph Laplacians).
- Directed ray-Laplacian stack: effective rank 8 (all 8 ray
  directions distinct as non-symmetric operators).
- Orbit-Laplacian stack (L_ortho, L_diag): rank 2, as predicted.
- D₄×Z₂-projected per-site degree signatures: rank 8.

Rank 6 did not fall out naturally from any of these four
constructions — the `2 A1 + B1 + B2 + 2 E` decomposition is an irrep
COUNT, not an operator rank.  The sequel should treat rank-6 as a
decomposition parameter of the encoder's irrep channels rather than
a stacked-operator rank.

---

## 2. Placement generators

A placement at `(r, c)` sees 8 rays.  Following the chess §11.2
structure, the Othello phase-space origin is

    phi(r, c) = (r * row_gen + c * col_gen) mod D

and each ray contributes a characteristic phase shift along up to 7
lattice steps.  For D = 768 with generators (row_gen = 7, col_gen = 11):

| Ray  | Offset per step (dr, dc) | Phase shift per step mod 768 |
|------|--------------------------|-------------------------------|
| N    | (-1,  0)  | −7           |
| E    | ( 0,  1)  | +11          |
| S    | ( 1,  0)  | +7           |
| W    | ( 0, −1)  | −11          |
| NE   | (-1,  1)  | −7 + 11 = +4 |
| SE   | ( 1,  1)  | +7 + 11 = +18 |
| SW   | ( 1, −1)  | +7 − 11 = −4 |
| NW   | (-1, −1)  | −7 − 11 = −18 |

The phase shifts along the 4 ortho directions form the set {±7, ±11};
along the 4 diagonal directions they are {±4, ±18}.  Unlike chess,
there is no knight-style `(±1, ±2)` combination — the knight's θ
class has no Othello referent (E1 verified).

**Phase-operator candidates (unobstructed reach).**

- P_ray_N(phi)   = { phi + k · (−7)  mod D  : k ∈ 1..7 }, and
                   analogously for {E, S, W, NE, SE, SW, NW}.
- P_placement(phi) = union of all 8 P_ray_d(phi).

The unobstructed reach size from a central square is at most 8 × 7 =
56 phases, but truncation at board boundaries typically gives ≤ 28
(≈ queen's reach from e4 in chess — deliberately analogous).

---

## 3. Flip gate

Unlike chess, an Othello placement is inseparable from the flip
operation on bracketed opponent discs.  The sequel must decide how
the flip is represented in phase space.  Three candidates:

### Option A: sign flip on Blume-Capel signal in place

Flip along ray d is the multiplication of `s_j` by `-1` for every
bracketed site j.  In phase space this is a scalar `-1` applied to the
encoded site values at the bracketed phase positions.  Simple; but
requires the occupation-aware gating of §4 before it can be
applied.

### Option B: Z₂ channel in the encoder

Treat the flip as an explicit Z₂ charge in a separate encoder
channel.  Each disc has an associated Z₂ bit; the flip toggles it.
The D₄×Z₂ irrep decomposition naturally splits the encoder into
'+' and '-' halves (§10.4), so this choice aligns with the
symmetry structure.

### Option C: composition of placement + Z₂ generator

Define a Z₂ phase generator `g_flip` such that `g_flip . phi = phi + D/2`
(antipodal shift in the coprime phase space).  The flip is then the
composition `P_placement ∘ g_flip` along bracketed rays.

**Recommendation.** Option B is the most structurally defensible: it
matches the D₄×Z₂ irrep split (exact in Othello, approximate in chess)
that already grounds the encoder.  Option A is simpler for small-board
validation.  The sequel should implement both and verify they produce
equivalent legal-move sets on the validation engine before committing.

---

## 4. State-dependent gating

Chess phase operators (§11.2) are state-INDEPENDENT — a rook at e4
generates the same phase-space reach whether the board is empty or
crowded.  The occupation-aware phase operators (§11.4) were bolted
on via Solutions A/B/C.  Othello does not permit this design:
placement is legal ONLY if at least one ray brackets.  The gate must
be intrinsic to the generator.

Three design candidates for the intrinsic gate:

1. **Mask construction.**  Precompute, for each `(phi_origin, state)`
   pair, the subset of P_placement(phi_origin) that corresponds to
   legal placements.  Store as a sparse mask.  Legal-move generation
   = query the mask at the current state.  Memory: up to 2^64 states,
   so must be computed online from the current state, not
   precomputed.

2. **Generator filtering.**  P_ray_d emits phase shifts ONLY along
   rays that currently bracket.  The generator reads the state, walks
   each ray to the first same-colour terminator, and only emits
   phases for rays where a bracket exists.  This is essentially a
   re-expression of the geometric move generator in phase-tuple
   language — correct but not a reduction.

3. **Aliasing-horizon gating.**  The CRT aliasing horizon from UTLP
   S4 (chess §11.6) could be re-purposed as a spatial partition
   detector: a phase-shift is admitted iff its target phase is within
   the aliasing horizon of a current-colour disc along the same ray
   direction.  This is the most structurally interesting candidate
   and the one most worth testing empirically.

**Recommendation.**  Start with Option 2 (generator filtering) for
correctness validation, then implement Option 3 (aliasing-horizon
gating) and compare — they should produce identical legal-move sets
if the aliasing horizon is chosen correctly.  Equivalence (or not)
is a falsifiable prediction of the phase-operator framework.

---

## 5. Ground-truth engine

For the chess phase-operator validation, `python-chess` was the
reference.  For Othello the sequel needs a Python-importable legal
move generator.  Candidates:

| Engine              | Language | Strength vs perfect play | Notes |
|---------------------|----------|--------------------------|-------|
| edax                | C binary | gold-standard            | External process; requires wrapping |
| python-othello      | Pure Py  | legal-move generator only | pip-installable |
| reversi (on PyPI)   | Pure Py  | weak player              | Works; less common |
| our OthelloBoard    | Pure Py  | legal-move only (this code) | 80 lines; verified |

**Recommendation.**  Use `research/othello_utils.py::OthelloBoard`
as the primary reference for legal-move generation (verified against
the standard Othello opening: 4 starting legal moves, 3 replies after
first move).  For evaluation-quality ground truth (depth-gap studies
against H9 / E8), add `edax` as an optional dependency, invoked via
subprocess with a documented setup step.  This mirrors how chess used
`stockfish` as an optional binary.

---

## 6. What the sequel should cover

1. **Experiment 1 — Empty-board equivalence** (chess §11.3 analog).
   Phase-operator reachable set vs geometric set for every single
   disc on an empty board, across all 8 rays.  Target: 100%
   equivalence for the unobstructed reach.
2. **Experiment 2 — Occupation-aware** (chess §11.4 analog).  Three
   gating solutions (§4 above); measure convergence.  Target:
   100% equivalence of the filtered reach with the ground-truth
   legal-move set over a position-generator corpus.
3. **Experiment 3 — Flip closure.**  Unique to Othello.  Verify
   that phase-space representation of the flip is well-defined and
   invertible (where possible) and that its composition with
   P_placement gives the correct post-move state.
4. **Experiment 4 — Aliasing horizon.**  If Option 3 from §4 above
   is adopted, test whether the horizon produces the exact
   legal-move set or a strict sub/superset.

Each experiment should emit a structured CSV of
`(position_hash, phase_ops_set, engine_set, match)` for later
statistical analysis.

---

## 7. Open questions the sequel must answer

1. Does the minimum admissible D fall out naturally from Othello
   structure (the way D = 640 emerged for chess from the
   rank-5 fiber × 5 D₄ irreps × 64)?
2. Is there a "polarization state" analog for Othello's single
   disc type?  The §9r reframing collapses to
   `(theta-class, r = infinity, c = 0)` — does this mean a single
   lattice excitation with 8 polarization directions, analogous to
   the chess king's 8 directions at r = 1?
3. Does the dynamic sheaf spectrum from Phase 2 reproduce the legal-
   move-count correlation we observed (Spearman +0.765, p = 1.1e-12),
   at production-size corpus volumes?
4. Is the CRT aliasing horizon computable from the current board
   state in O(ray_length × ray_count) = O(56) operations per move?
   If so, Option 3 is the production implementation.

---

## 8. Artefacts the sequel will need

- `research/othello_utils.py` — board + signals (ready).
- `research/d4_z2.py` — 16-element group, 10 irreps, projectors
  (ready, sanity-verified).
- `research/ray_laplacians.py` — 8 ray Laplacians and orbit
  aggregates (ready).
- `research/coprime_generators.py` — (p, q) table for candidate D's
  (ready).
- `research/dynamic_sheaf.py` — Phase 2 minimal sheaf
  (ready, spectrum trajectory in `results/phase2_sheaf_trajectory.json`).
- `results/phase1_hypotheses.csv`, `results/phase1_detail.json` —
  verification numerics (ready).

Everything above is importable from the `research/` package, and the
file layout mirrors the intended production package
`othello-spectral/python/othello_spectral/` so promotion-when-ready is
a `mv`, not a rewrite.

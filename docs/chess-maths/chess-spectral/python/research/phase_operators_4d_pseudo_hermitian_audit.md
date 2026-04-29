# `phase_operators_4d` — pseudo-Hermitian / PT-symmetry pre-flight audit

**Pre-flight check #2** for the planned `chess_spectral.qm_4d` module.
**Date:** 2026-04-29.
**Repo:** `C:\AI_PROJECTS\EMDR_PULSER_SONNET4\docs\chess-maths\chess-spectral`.
**Audited code:** `python/chess_spectral/phase_operators_4d/` (~976 LOC across 5 files).

The previous quantum-lens audit suspected the package's "operators" are
phase-encoded mask functions / set-valued reach predicates rather than
linear operators on a Hilbert space. This document records the
categorisation, a materialised-matrix probe, and a renaming
recommendation.

---

## 1. Background — what would qualify as a "pseudo-Hermitian operator"

An operator `O` on a Hilbert space `H` is **pseudo-Hermitian**
(Mostafazadeh) if there exists an invertible Hermitian `eta` with

```
O^dagger = eta . O . eta^{-1}
```

A *necessary* (not sufficient) condition is that `spec(O)` is real or
comes in complex-conjugate pairs. **PT-symmetric** operators (Bender)
are a subset where `eta` is the parity-time operator. To even ask the
question, `O` must be a linear map between vector spaces.

The package defines `MODULUS_4D = 145451`, `phi4 : [0,7]^4 -> Z_M`,
and a family of "piece operators" `P_rook4`, `P_bishop4`, …,
`P_pawn4_*`. The natural Hilbert space for the problem is
`H = C^4096`, indexed by board phases (the image of `phi4`); a
secondary candidate is `C^145451`, the full ring `Z_M`.

---

## 2. Symbol categorisation

Legend: **(L)** linear operator on a defined vector space.
**(P)** predicate / set function returning `bool` or `frozenset[int]`
— *not* an operator. **(C)** composition that is structurally an
operator but currently implemented as set arithmetic and would need
lifting to qualify.

### `phase_operators_4d.py`

| Symbol | Class | Notes |
|---|---|---|
| `MODULUS_4D`, `GEN_X`, `GEN_Y`, `GEN_Z`, `GEN_W`, `AXIS_GENS` | const | scalars / tuples |
| `AXIS_SHIFTS`, `PLANE_DIAG_SHIFTS`, `KNIGHT_SHIFTS`, `KING_SHIFTS` | const | shift tables |
| `phi4(x,y,z,w) -> int` | const | scalar coordinate-to-phase map; not an operator |
| `_pawn_axis_gen`, `_pawn_capture_phases` | private helper | predicate-set helpers |
| `PawnAxis` | type alias | — |
| `P_rook4(origin_phi) -> frozenset[int]` | **(P)** lifts to **(L)** | reach predicate; lifts to a real-symmetric matrix |
| `P_bishop4(origin_phi) -> frozenset[int]` | **(P)** lifts to **(L)** | same |
| `P_queen4(origin_phi) -> frozenset[int]` | **(P)** lifts to **(L)** | same |
| `P_king4(origin_phi) -> frozenset[int]` | **(P)** lifts to **(L)** | same |
| `P_knight4(origin_phi) -> frozenset[int]` | **(P)** lifts to **(L)** | same |
| `P_pawn4_white(origin, *, axis, on_starting_rank, include_captures)` | **(P)** | parametric reach predicate; not symmetric (push direction is not reversible at the same speed); lift would be **non-Hermitian** |
| `P_pawn4_black(...)` | **(P)** | same; would be the dagger of the white form on the captures sub-block |

### `phase_to_coords_4d.py`

| Symbol | Class | Notes |
|---|---|---|
| `Coord4D` | type alias | — |
| `_build_lookup_tables`, `PHI_TO_XYZW`, `XYZW_TO_PHI` | const | injective dictionaries — lattice basis enumeration |
| `invert(phi) -> Optional[Coord4D]` | **(P)** | partial inverse / membership predicate |
| `phase_set_to_board(phases) -> frozenset[Coord4D]` | **(P)** | boundary-clipping projector at the *set* level (would lift to the diagonal projector `Pi_board` on `C^M`) |

### `occupation_aware_a_4d.py`

| Symbol | Class | Notes |
|---|---|---|
| `_PHASE_OP_BY_PIECE_TYPE_NAME` | const | dispatch table |
| `_phase_dests_for(piece_type, origin)` | **(P)** | predicate dispatcher |
| `_phase_dests_for_pawn(...)` | **(P)** | predicate dispatcher |
| `occupation_aware_moves_a_4d(state, origin, piece) -> frozenset[Coord4D]` | **(C)** | structurally `phase_op intersect oracle`. Would lift to `Pi_oracle . M_piece`, with `M_piece` Hermitian and `Pi_oracle` a state-dependent diagonal projector — the composition is **not Hermitian in general** (Hermitian times projector lifts a Hermitian to a non-Hermitian operator on the active subspace, but is pseudo-Hermitian under `eta = Pi_oracle`). |

### `phase_check_detection_4d.py`

| Symbol | Class | Notes |
|---|---|---|
| `_pawn_threat_phases_on_king(...)` | **(P)** | predicate |
| `phasecast_is_check_4d_no_pawns(state, color) -> bool` | **(P)** | reduces to a non-empty intersection of `M_piece . |kings>` with enemy-occupation indicators; *the outer return value is a bool*, but the structure is "operator times indicator vector, non-empty intersection" — i.e. predicate over an operator |
| `phasecast_is_check_4d(state, color) -> bool` | **(P)** | same |
| `_slider_ray_hits_king(...)` | **(P)** | step-by-step ray walk; an explicit unrolled `(I + d + d^2 + ...) |king>` truncated by the first occupant; a (C)-class candidate but currently a procedural set-walk |
| `move_leaves_king_in_check_4d_no_pawns(state, move) -> bool` | **(P)** | composition `phasecast . push(move)` returning a bool |
| `move_leaves_king_in_check_4d(state, move) -> bool` | **(P)** | same |

### Total

Public symbols (excluding constants and type aliases):

| Class | Count | Symbols |
|---|---|---|
| **(L)** | **0** | none — *no symbol is currently a linear operator in code* |
| **(L)-liftable from (P)** | **5** | `P_rook4`, `P_bishop4`, `P_queen4`, `P_king4`, `P_knight4` (all chess-symmetric reach predicates) |
| **(P)** | **9** | `P_pawn4_white`, `P_pawn4_black`, `invert`, `phase_set_to_board`, `phasecast_is_check_4d_no_pawns`, `phasecast_is_check_4d`, `move_leaves_king_in_check_4d_no_pawns`, `move_leaves_king_in_check_4d`, `_pawn_threat_phases_on_king` |
| **(C)** | **2** | `occupation_aware_moves_a_4d`, `_slider_ray_hits_king` |

Headline tally: **0 L-class, 9 P-class, 2 C-class** (with 5 P-class
symbols liftable to (L) at small extra cost). The `phi4` map and the
shift tables are constants, not operators.

---

## 3. Materialised-matrix probe

To validate the lift claim, `P_rook4` was materialised on the
4096-dimensional board image: `M[i, j] = 1` iff
`basis[i] in P_rook4(basis[j])` and `basis[i] is on-board`. Probe
script: `research/_probe_p_rook4_hermiticity.py`.

```
=== P_rook4 materialisation probe ===
basis size n         = 4096
nnz                  = 114688
is real symmetric?   = True
#(M - M^T) != 0      = 0
max |M_ij - M_ji|    = 0.0
max |Im(eig)|        = 4.69e-15
all eigs real (1e-9)? = True
Re(eig) range        = (-4.0, 28.0)         <- exactly {-4, ..., 28}
first 8 eigs         = 27.99..., 19.99..., 19.99..., 19.99...,
                       11.99..., 11.99..., 11.99..., 11.99...
one-sided offdiag    = 0
diagonal metric admissible? = True (trivially: eta = I works)
```

A second probe on `P_knight4` (`research/_probe_p_knight4_hermiticity.py`)
gave the same shape: real-symmetric, max |Im eig| ≈ 2.4e-15,
spectrum in `[-36.06, 36.06]` (irrational because the 48-leaper
adjacency graph is not vertex-transitive after boundary clipping).

### Verdict for the `P_*4` reach predicates

When lifted, they are **real-symmetric matrices on `C^4096`** —
i.e., **Hermitian** in the strongest sense (Hermitian implies
pseudo-Hermitian with `eta = I`).

This is not magic. Chess piece reach is a *symmetric relation*
(every legal axis-step is reversible by the same axis-step in the
opposite direction), and the boundary clipping is symmetric on
the active basis (off-board destinations drop on both sides). The
operators are graph adjacency matrices of vertex-symmetric (mostly
— the boundary breaks transitivity but not symmetry) reach graphs.
Such adjacency matrices are always Hermitian.

### Where pseudo-Hermiticity becomes nontrivial

The pawn predicates (`P_pawn4_white`, `P_pawn4_black`) **break
Hermiticity** because pawn pushes are directed (white pushes
+axis, black pushes -axis; double-push from starting rank only).
The lift `M_white_pawn` would have `M^T != M`. The natural metric
candidate would be a parity flip on the pawn-axis coordinate —
this is the actual **PT-symmetric** structure if it exists, and
it deserves its own probe in `qm_4d`.

The `occupation_aware_moves_a_4d` composition lifts to
`Pi_oracle . M_piece`, which is non-Hermitian on `C^M` but
*pseudo-Hermitian* under `eta = Pi_oracle` if we restrict to the
active subspace — that is the genuinely interesting piece for
`qm_4d` and worth a follow-up probe.

---

## 4. Renaming recommendation

**Equivocal — leaning toward "phase reach predicates" as the
canonical name, with `phase_operators` retained as a domain-of-
discourse alias.** Rationale:

1. **The strict reading favours renaming.** As shipped, every
   public symbol returns `frozenset[int]` or `bool`, not a vector
   in `C^4096`. Calling them "operators" in the Mostafazadeh /
   Bender sense is a category error. A reviewer who reads
   `P_rook4(origin_phi) -> frozenset[int]` and sees the word
   "operator" in the package name will reasonably object.

2. **The chess-spectral house style is forgiving here.** The 2D
   sibling package is also called `phase_operators`, and the
   broader research record (`PHASE_OPERATOR_SUPPLEMENT_4D.md`)
   has used the term consistently for ~12 months. The term is a
   *load-bearing identifier* in the documentation graph.

3. **The probe shows the lift is clean.** When `P_rook4` is
   materialised, it *is* a Hermitian operator. So the symbols
   are not phase operators *as written*, but they are
   phase-operator generators / kernels. Calling the package
   `phase_operators_4d` is technically defensible if the docstrings
   are amended to clarify "predicate-form representations of
   linear operators on the board image."

**Proposed compromise (recommended):**

- **Do not rename the package** (`phase_operators_4d` stays).
- **Rename the public symbols' docstring vocabulary** from
  "operator" to "reach predicate" / "phase reach predicate",
  with a one-paragraph note in `__init__.py` explaining: "These
  symbols are predicate-form generators of Hermitian operators
  on `C^4096`. The `chess_spectral.qm_4d` module materialises
  them as matrices and explores the pseudo-Hermitian /
  PT-symmetric structure of the directed pawn variants."
- **Add a stub `chess_spectral.qm_4d` module** that *does* expose
  honest linear operators, and reserve the word "operator" in
  the function-level vocabulary for that module.

This way no API breaks, no test renames, no cross-document
churn — but the audit-trail concern (Bender / Mostafazadeh
literature is unforgiving) is addressed where it matters.

---

## 5. Files affected if a hard rename were chosen

If the maintainers decide on a hard rename (`phase_operators` →
`phase_predicates` or similar) the following 14 files reference the
identifier and would all need updating:

- `python/chess_spectral/phase_operators_4d/__init__.py` (4 occ.)
- `python/chess_spectral/phase_operators_4d/phase_operators_4d.py` (1 occ.)
- `python/chess_spectral/phase_operators_4d/phase_check_detection_4d.py` (3 occ.)
- `python/chess_spectral/phase_operators_4d/occupation_aware_a_4d.py` (5 occ.)
- `python/chess_spectral/phase_operators_4d/phase_to_coords_4d.py` (4 occ.)
- `python/tests/test_phase_4d_design.py` (3 occ.)
- `python/tests/test_phase_4d_unobstructed.py` (5 occ.)
- `python/tests/test_phase_4d_occupation_aware.py` (1 occ.)
- `python/tests/test_phase_4d_check_detection.py` (2 occ.)
- `python/tests/test_smoke_e2e.py` (25 occ.)
- `python/research/chess4d_phase_design.py` (2 occ.)
- `python/research/bench_phase_vs_spatial.py` (6 occ.)
- `python/CHANGELOG.md` (22 occ.)
- `python/README.md` (7 occ.)

Total `phase_operators_4d` occurrences: ~90 (excluding the 2D
sibling package, which would also need the same treatment for
consistency — another ~33 occurrences across 11 more files).

**Three files most likely to hurt** if a rename is chosen:

1. `python/chess_spectral/phase_operators_4d/__init__.py` — the
   public re-export list and `__all__`. Every downstream import
   path threads through this file.
2. `python/tests/test_smoke_e2e.py` — 25 occurrences. End-to-end
   test goes red on every rename pass and is the canary for the
   global migration.
3. `python/CHANGELOG.md` — 22 occurrences. Historical entries
   reference the old name; rewriting them silently rewrites
   history. Better policy: leave CHANGELOG entries as-is and
   add a clarifying entry to the next version.

---

## 6. Recommended next steps for `qm_4d`

1. **Confirm the lift design.** `qm_4d.materialise(P_rook4)` →
   `(M, basis_phases)` where `M` is real-symmetric on `C^4096`.
   Provide a small adjoint-shape probe and a unit test that asserts
   `is_real_symmetric == True` for all 5 chess-symmetric `P_*4`
   predicates.
2. **Investigate pawn pseudo-Hermiticity properly.** Materialise
   `P_pawn4_white` + `P_pawn4_black` on the W- and Y-axis pawn
   subspaces; search for a parity-time `eta` of the form
   `eta_W = T_W . P_axis` where `T_W` flips the W coordinate and
   `P_axis` is the axis-permutation. *This* is the genuine PT
   probe.
3. **Document occupation_aware_a_4d as a (C)-class symbol** with
   a non-trivial state-dependent diagonal metric `eta = Pi_oracle`.
   This is a reasonable test bed for the Mostafazadeh framework
   and would justify the `qm_4d` name properly.
4. **Adopt the compromise rename** in §4: leave the package name,
   amend the docstrings, reserve `qm_4d` for the honest linear-
   operator forms.

---

## 7. Probe scripts

- `python/research/_probe_p_rook4_hermiticity.py` — full materialisation + spectrum + diagonal-metric admissibility for `P_rook4`. Runtime ≈ 1 minute.
- `python/research/_probe_p_knight4_hermiticity.py` — cross-check probe for `P_knight4`. Runtime ≈ 1 minute.

Both run from the `python/` working directory:

```sh
cd python/
python research/_probe_p_rook4_hermiticity.py
python research/_probe_p_knight4_hermiticity.py
```

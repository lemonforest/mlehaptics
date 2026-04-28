# Phase-Operator Move Engine (4D / Oana-Chiru): Notebook Supplement

**Status:** working supplement — occupies the §13 slot in [chess_spectral_4d_notebook.md](chess_spectral_4d_notebook.md). Companion to the 2D supplement at [PHASE_OPERATOR_SUPPLEMENT.md](PHASE_OPERATOR_SUPPLEMENT.md).

**Framing:** lifts the 2D phase-operator hypothesis (§11) to the 4D Oana-Chiru lattice on Z_8^4. Where 2D validated against `python-chess`, 4D validates against the spatial movegen we already shipped in [`tables_4d.py`](chess-spectral/python/chess_spectral/tables_4d.py) — `rook4_targets`, `bishop4_targets`, `knight4_targets`, `king4_targets`, `queen4_targets`, `white_pawn4_targets`, `white_pawn4_y_targets` — which directly encodes Oana & Chiru, "On a Four-Dimensional Chess Model," AppliedMath 6(3):48 2026 §3.

**Language discipline:** as in the 2D supplement, movement is "phase transition," pieces are "polarization states," the board is "the lattice domain" or "the coprime cyclic phase space." Specific chess terminology (rook, bishop, etc.) is retained where it references the spatial validation oracle.

**Connection to 2D §11.** The four constraints below are the 4D Diophantine generalization of 2D §11.2.1's coprime+distinct construction. The Othello Phase 1c work surfaced a critical correction — coprimality is necessary but **not sufficient** for image bijection (see [`docs/othello-maths/CHESS_NOTEBOOK_PHASE_1C_PATCHES.md`](../othello-maths/CHESS_NOTEBOOK_PHASE_1C_PATCHES.md) Patch 2 for the 2D counter-example `(p,q) = (3,7) mod 1024`). §13.1 below makes this discipline explicit for 4D where the constraint count grows from `15² - 1 = 224` to `15⁴ - 1 = 50,624`.

---

## §13.1. The φ_4d encoding

### §13.1.1 Statement

Define the 4D phase map

    φ(x, y, z, w) = (x · g_x + y · g_y + z · g_z + w · g_w) mod M

with axis generators `(g_x, g_y, g_z, g_w)` each coprime to M. The image of `[0,7]^4` under φ must be a 4096-element subset of Z_M that is **not** a subgroup.

### §13.1.2 Design constraints

| #  | Name                   | Statement                                                                 |
|----|------------------------|---------------------------------------------------------------------------|
| C1 | Coprime (necessary)    | gcd(g_i, M) = 1 for each axis i ∈ {x, y, z, w}                            |
| C2 | Image bijection        | \|{(x·g_x + y·g_y + z·g_z + w·g_w) mod M : (x,y,z,w) ∈ [0,7]⁴}\| = 4096   |
| C3 | Subgroup non-closure   | The image is **not** closed under addition mod M                          |
| C4 | Derived-gen distinct.  | Each per-piece shift set (axis 8, plane-diag 24, knight 48, king 80) has no internal collision mod M. Knight is disjoint from axis ∪ plane-diag ∪ king (since knight uses ±2 multipliers and the others use ±1 only). |

C1 is necessary but not sufficient for C2. The complete bijection condition is the Diophantine

    g_x · Δx + g_y · Δy + g_z · Δz + g_w · Δw ≢ 0 (mod M)

for every nonzero `(Δx, Δy, Δz, Δw) ∈ [-7, 7]^4` — `15⁴ - 1 = 50,624` inequalities. C2 (image-size check) is the operationally equivalent statement: the image has size 4096 iff no two distinct origin tuples produce the same residue iff the Diophantine has no nonzero solution in the bounded box.

C3 is the boundary-detection mechanism inherited from 2D §11.2.1: phase-shifts that carry an origin off the board land in the off-image complement of Z_M, where Phase B's `invert` function returns None.

C4 keeps each per-piece operator's destination set unambiguous and ensures the knight (which uses ±2 multipliers) cannot be confused with any single-step piece (rook/bishop/king, all using ±1). Importantly, the king's 80 shifts contain the 8 axis shifts (ε weight 1) and 24 plane-diagonal shifts (ε weight 2) by construction — `axis ⊂ king` and `plane_diag ⊂ king` are identities derived from `ε ∈ {-1,0,+1}⁴`, not violations. The same structure holds in 2D: the 2D king's 8 shifts equal `axis ∪ plane_diag` exactly. C4's cross-category check is therefore narrowed to the meaningful question — does the knight family alias any single-step family?

### §13.1.3 The chosen tuple

```
(M, g_x, g_y, g_z, g_w) = (145451, 9719, 647, 43, 3)
```

Constructed via the **mixed-radix tower with ladder coefficient 14** in [`research/chess4d_phase_design.py`](chess-spectral/python/research/chess4d_phase_design.py):

```
g_w = 3                              # smallest admissible prime
g_z = next_prime(14·g_w + 1)         = next_prime(43)   = 43
g_y = next_prime(14·(g_w + g_z) + 1) = next_prime(645)  = 647
g_x = next_prime(14·sum_lower + 1)   = next_prime(9703) = 9719
sum = 10412
M   = next prime > 7·sum + 7·(g_x + g_y) coprime to all = 145451
```

The construction is the 4D analogue of the 2D pattern `(M, p, q) = (640, 67, 7)` with `8·7 = 56 < 67`. Each generator dominates `14·` (sum-of-smaller), and by integer linear independence of distinct primes, no nonzero `Δ ∈ [-14,14]^4` satisfies `Σ Δ_i · g_i = 0`. Combined with `|Σ Δ_i · g_i| ≤ 14·sum = 145768`, the choice `M = 145451 ≥ 7·sum + 7·(g_x + g_y) + 1 = 145451` ensures no operator-shift wraparound for any single-piece phase shift.

### §13.1.4 The Phase B refinement (why ladder_coeff = 14, not 7)

The original Phase A construction used **ladder_coeff = 7** — the bound for `[-7, 7]^4` origin-bijection. That tuple `(M=12181, g_x=1523, g_y=191, g_z=23, g_w=3)` passed all four Phase A constraints (C1–C4) but failed Phase B's structural gate (4096 origins × 9 piece configs against `tables_4d.X_targets`) at every single piece config.

**Root cause.** Operator shifts have components in `[-7, 7]` per axis; the difference between two operator shifts spans `[-14, 14]^4`. An integer linear dependency `Σ Δ·g = 0` with `Δ ∈ [-14, 14]^4 \ {0}` manifests as cross-piece destination aliasing. The original tuple had `g_y = 10·g_w + 7·g_z` (literally `191 = 30 + 161`), giving `Δ = (0, +1, -7, -10)` with `Σ Δ·g = 0` and `Δ_w = -10 ∈ [-14, 14]` (but `∉ [-7, 7]`).

**Concrete failure.** A rook `+7·g_w` shift (intended `+7` along the w-axis) from origin `(0, 0, 7, 3)` inverted to `(0, 1, 0, 0)` — a non-rook destination — because `phi(0, 0, 7, 3) + 7·g_w = phi(0, 1, 0, 0)` exactly by the dependency above. The rook operator was claiming bishop-plane-diagonal squares as legal destinations.

**The fix.** Widen the ladder coefficient from 7 to 14 in `construct_mixed_radix_tower()`, then verify by brute-force enumeration over `(2·14+1)⁴ = 707281` candidates that no nonzero `Δ ∈ [-14, 14]^4` has `Σ Δ·g = 0`. The new tuple `(M=145451, g_x=9719, g_y=647, g_z=43, g_w=3)` is dep-free in `[-14, 14]^4` (and trivially in `[-7, 7]^4`).

**The lesson.** C1–C4 (Phase A) ensure origin uniqueness. Phase B's structural gate adds a fifth constraint — call it **C5: operator-aliasing freedom** — that requires `[-14, 14]^4` dep-freedom. C5 is now codified in `test_phase_4d_design.test_c5_no_integer_dependency_in_minus14_to_14_box` so any future re-derivation that violates it fails loudly.

The 2D supplement's `(67, 7) on Z_640` design satisfies `8·7 = 56 < 67`, which is the same structural bound at a smaller scale — operator shifts in 2D are 2-axis, not 4-axis, so the `[-N, N]^2` box is naturally narrower. Both designs are the same construction; the 4D version needs the wider ladder to handle 4-axis cross-mixing.

### §13.1.5 Per-constraint verification (post-refinement)

Output of `python research/chess4d_phase_design.py`:

| Constraint                                | Result                                  |
|-------------------------------------------|-----------------------------------------|
| C1 (coprime g_i to M)                     | ✓ all four                              |
| C2 (image bijection)                      | ✓ 4096 distinct phases mod 145451       |
| C3 (image not a subgroup)                 | ✓ random-pair-sum escape detected       |
| C4 axis shifts (8 distinct)               | ✓                                       |
| C4 plane-diag shifts (24)                 | ✓                                       |
| C4 knight shifts (48)                     | ✓                                       |
| C4 king shifts (80)                       | ✓                                       |
| C4 knight ∩ {axis ∪ pd ∪ king}            | ∅ (knight uses ±2; others ±1)           |
| **C5 ([-14, 14]^4 integer-dep-freedom)**  | **✓ brute-forced 707k candidates**      |

Constants pinned in [`chess_spectral/phase_operators_4d/phase_operators_4d.py`](chess-spectral/python/chess_spectral/phase_operators_4d/phase_operators_4d.py) as `MODULUS_4D = 145451`, `GEN_X = 9719`, `GEN_Y = 647`, `GEN_Z = 43`, `GEN_W = 3`. Validated by [`tests/test_phase_4d_design.py`](chess-spectral/python/tests/test_phase_4d_design.py) (15 tests including C5) and [`tests/test_phase_4d_unobstructed.py`](chess-spectral/python/tests/test_phase_4d_unobstructed.py) (20 tests including the 4096-origin × 9-piece-config structural gate).

### §13.1.4 What this hypothesis would establish if confirmed

If P_p (Phase B) reproduces `tables_4d.X_targets` set-equal at every origin (Phase B gate = 4096 origins × 9 piece configs), then the O&C piece geometry on Z_8^4 is fully captured by the φ_4d coprime cyclic structure with no reference to (x,y,z,w) coordinates. The 4D lattice is redundant representation; the encoder's tensor-DCT structure (chess_spectral_4d_notebook.md Phase 2) plus the φ_4d phase shifts together encode the complete piece-movement structure of Oana-Chiru chess.

### §13.1.5 What this hypothesis would not establish

(Same caveat as 2D §11.1.3.) Nothing about whether 4D phase-space computation is faster, more accurate, or more revealing than 4D coordinate-space computation. Nothing about fog-of-war, partial observation, or 4D similarity structure. These are downstream experiments.

---

## §13.2. Phase Operator Specifications

Implemented in [`chess_spectral.phase_operators_4d.phase_operators_4d`](chess-spectral/python/chess_spectral/phase_operators_4d/phase_operators_4d.py). All operators return `frozenset[int]` of phase residues mod `MODULUS_4D = 145451`. Boundary clipping is handled by [`phase_to_coords_4d.phase_set_to_board`](chess-spectral/python/chess_spectral/phase_operators_4d/phase_to_coords_4d.py) which inverts via the precomputed `PHI_TO_XYZW` lookup.

| Operator | Shift count | Construction |
|---|---|---|
| `P_rook4(φ)` | up to 56 (interior 28) | `±k·g_axis` for k=1..7 on each of 4 axes |
| `P_bishop4(φ)` | up to 168 | `±k·(±g_i ± g_j)` for k=1..7 over 6 plane pairs × 4 sign combos |
| `P_queen4(φ)` | up to 224 | `P_rook4 ∪ P_bishop4` (disjoint by construction) |
| `P_king4(φ)` | 80 (interior) | `Σ ε_i · g_i` for `ε ∈ {-1,0,+1}^4 \ {0}` |
| `P_knight4(φ)` | 48 (interior) | `±2·g_i ± g_j` for 12 ordered axis pairs × 4 sign combos |
| `P_pawn4_white(φ, axis, on_starting_rank, include_captures)` | 1 or 2 | `+g_axis` (single) or `+g_axis + 2·g_axis` (double from start rank); `axis ∈ {'w', 'y'}` per O&C Def 11 |
| `P_pawn4_black(φ, ...)` | 1 or 2 | mirror with `−g_axis` |

What's included and what's not:

- **Included:** unobstructed reach for each piece from any origin. The mathematics is pure phase arithmetic mod `MODULUS_4D`.
- **Not included:** occupation-aware ray truncation (Phase C), check / checkmate (Phase D), pawn diagonal captures (Phase E — `include_captures=True` raises `NotImplementedError` so the failure is loud, not silent).

---

## §13.3. Experiment 1: Equivalence on Empty Board (Phase B structural gate)

For each piece p ∈ {R, B, Q, N, K, P_w_white, P_w_black, P_y_white, P_y_black} and every origin (x, y, z, w) ∈ [0, 7]⁴ (4096 squares), the φ_4d-derived destination set equals `tables_4d.X_targets(x, y, z, w)`. Total cell tests: **4096 × 9 = 36,864 set-equality assertions, all pass**.

The test is parametrized in [`tests/test_phase_4d_unobstructed.py`](chess-spectral/python/tests/test_phase_4d_unobstructed.py)::`test_phase_op_matches_spatial_oracle_on_all_4096_origins[piece]`, with one parametrization per piece. On failure, the test reports the first three mismatched `(origin, missing_in_phase, extra_in_phase)` triples — actionable.

**The §13.3 gate is the structural pass/fail gate for the whole construction.** It confirmed (after the refinement story above) that the 4D O&C piece geometry is fully captured by the φ_4d coprime cyclic phase structure. The supporting derivation tests:

| Test | Status | What it confirms |
|---|---|---|
| `test_rook_interior_mobility_is_28` | ✓ | O&C section 3 rook degree |
| `test_king_interior_mobility_is_80` | ✓ | O&C section 3 king degree (3⁴ - 1) |
| `test_knight_interior_mobility_is_48` | ✓ | O&C section 3 knight degree |
| `test_bishop_two_components_via_parity` | ✓ | O&C section 3 bishop parity partition (matches `tables_4d.bishop4_targets`) |
| `test_queen_equals_rook_union_bishop` | ✓ | A_queen = A_rook + A_bishop (disjoint edge support) |
| `test_w_pawn_white_double_push_from_starting_rank` | ✓ | (3,3,3,1) → {(3,3,3,2), (3,3,3,3)} on +w axis |
| `test_y_pawn_white_double_push_from_starting_rank` | ✓ | (3,1,3,3) → {(3,2,3,3), (3,3,3,3)} on +y axis |
| `test_pawn_capture_geometry_is_phase_e_punt` | ✓ | `include_captures=True` raises `NotImplementedError` (loud failure for the unimplemented surface) |
| `test_pawn_axis_z_is_rejected` | ✓ | `axis='z'` raises `ValueError` per O&C Def 11 |

---

## §13.4. Experiment 2: Occupation-Aware Moves (Phase C gate)

> Will be populated by Phase C. Expected:
>
> 100 seeded sparse pos4 fixtures from `_seeded_self_play_4d` × every occupied origin. Phase-op A's destination set must equal the spatial oracle's `legal_pseudo_dests`. Pass count: X / Y.

---

## §13.5. Experiment 3: Check Detection (Phase D gate)

> Will be populated by Phase D. Expected:
>
> Reverse-cast `phasecast_is_check_4d` agrees with naive `is_check_naive_4d` on Phase C's 100-pos4 corpus. Pass count: X / Y. Reverse-cast timing vs naive: ratio Z.

---

## §13.6. Pawn Axis Handling (Phase E)

Per O&C §3.10 Def 11, pawns are W- or Y-oriented (never Z). Per Def 13, captures are restricted to the **2-plane spanned by the x-axis and the pawn's forward axis** — XZ, YZ, ZW captures are not legal.

### §13.6.1 Phase shifts

For each (color, axis) pair the capture phase shifts are:

| Color | Axis | Forward shift | Capture shifts                                       |
|-------|------|---------------|------------------------------------------------------|
| WHITE | W    | `+g_w`        | `(+g_x + g_w) mod M`, `(-g_x + g_w) mod M`           |
| WHITE | Y    | `+g_y`        | `(+g_x + g_y) mod M`, `(-g_x + g_y) mod M`           |
| BLACK | W    | `-g_w`        | `(+g_x - g_w) mod M`, `(-g_x - g_w) mod M`           |
| BLACK | Y    | `-g_y`        | `(+g_x - g_y) mod M`, `(-g_x - g_y) mod M`           |

These are a strict subset of the bishop's 24 plane-diagonal shifts (specifically the four xw and four xy diagonals). The phase op emits all geometric capture targets; off-board candidates are dropped by `phase_set_to_board`. Up to 2 captures per pawn (left- and right-x diagonals on the forward-axis side).

### §13.6.2 Where the rule comes from

Lifted directly from `chess4d.geometry.PAWN_CAPTURES` (the python-chess4d-oana-chiru reference implementation), which itself encodes O&C §3.10 Def 13. Both `P_pawn4_white(include_captures=True)` and the corresponding chess4d generator are tested against each other in `test_phase_4d_occupation_aware.py` and `test_phase_4d_unobstructed.py`.

### §13.6.3 Reverse-cast in is_check

`phasecast_is_check_4d` extends the Phase D `_no_pawns` form by computing the inverse pawn-capture phase set from each king. For a white king at `φ_k`:
- Black W-pawns capturing INTO `φ_k` originate at `(φ_k + g_x + g_w)` and `(φ_k - g_x + g_w)` (i.e., one square +w and ±1 in x).
- Black Y-pawns originate at `(φ_k + g_x + g_y)` and `(φ_k - g_x + g_y)`.

Black king mirrors with the W/Y signs flipped. The threat set is 4 phases per king (2 axes × 2 x-sides), intersected with the set of opposite-color pawn occupations.

### §13.6.4 What v1 covers

- Forward push (single + double from starting rank).
- Diagonal capture with axis-aware target plane.
- Color sign (white +, black −).

### §13.6.5 What v1 does NOT cover

- **En passant.** Per O&C §3.10 Def 15 it requires the ep-target state from the previous move; deferred to a future phase, mirroring the 2D supplement's deferral. The chess4d `pawn_moves` likewise excludes ep (its `legal_moves` includes ep via a separate path).
- **Promotion.** A move-level concern (the move metadata changes), not a phase-shift concern. The phase op produces forward/capture destinations regardless of whether the target rank is the promotion rank; the legality pipeline is responsible for tagging the move with the resulting promotion piece.

These are documented gaps — not silent ones. The `_no_pawns` variants of `phasecast_is_check_4d` and `move_leaves_king_in_check_4d` remain available for ablations or contexts where pawn detection isn't desired.

---

## §13.7. Discussion — what transferred from 2D, what's new at 4D

### §13.7.1 What transferred cleanly

- **The coprime cyclic phase encoding lifts cleanly from Z_640 to Z_145451.** Constraint catalog is identical in form (C1–C4), only the ladder coefficient widens (7 → 14) to handle 4-axis cross-mixing.
- **The Solution A discipline (phase op ∩ oracle) lifts directly.** Where 2D used `python-chess`, 4D uses [`python-chess4d-oana-chiru`](https://pypi.org/project/python-chess4d-oana-chiru/) — same shape, different oracle.
- **Multi-king reverse-cast** matches the 2D `phase_check_detection` shape; the only addition is iterating over all of mover's kings (per O&C §3.4 Def 3) rather than the unique king of 2D chess.
- **Pawn-axis as Z_2 tag** mirrors the encoder's W/Y antisym channel split. Phase E's capture geometry (xw / xy plane) is the natural lift of the encoder's structure.

### §13.7.2 What's genuinely new at 4D

- **C5: operator-aliasing freedom on `[-14, 14]^4`.** This constraint doesn't exist in the 2D supplement because 2D has only 2 axes; bounded integer dependencies are rare with two distinct coprime primes. In 4D the 4-prime mixing makes them common and easy to miss — Phase A's first attempt hit one. Codified in `test_phase_4d_design.py::test_c5_no_integer_dependency_in_minus14_to_14_box` so the regression cannot recur.
- **No external oracle.** 2D `python-chess` is C-accelerated bitboards. 4D `python-chess4d-oana-chiru` is pure Python — same language as our phase op. This makes 4D wall-clock comparisons more meaningful (both paths face the same CPython cost model) but doesn't help us evaluate the phase-vs-bitboard tradeoff at all.

### §13.7.3 Wall-clock benchmark (per-position move generation)

Measured by [`research/bench_phase_vs_spatial.py`](chess-spectral/python/research/bench_phase_vs_spatial.py) at the standard initial position, ~32 pieces in 2D / ~896 in 4D. Median of 20 runs after warmup; CPython 3.12 on Windows. **Lower is better.**

| Configuration                                             | Median (µs) | Ratio vs oracle |
|-----------------------------------------------------------|------------:|-----------------|
| 2D: `python-chess.Board.legal_moves` (full)               |       143   | 1.00× (oracle)  |
| 2D: phase op Solution A, no castling                      |     3,692   | **25.8× slower** |
| 2D: phase op Solution A + castling king-safety walk       |     4,479   | **31.3× slower** |
| 4D: `chess4d` per-piece pseudo-legal (no check filter)    |    14,508   | 1.00× (oracle)  |
| 4D: `chess4d.GameState.legal_moves` (full + check filter) |   216,758   | 14.9× slower    |
| 4D: phase op Solution A, no castling                      |    49,888   | **3.4× slower** |

**Reading the numbers.**

- **2D is dominated by the bitboard / pure-Python gap.** `python-chess` is C-accelerated; the phase op is pure-Python set arithmetic. The 26–31× gap is the constant-factor cost of CPython, not an algorithmic loss for phase math.
- **2D castling adds ~22% to the phase op** (3,692 → 4,479 µs). The king-safety walk per castle right is the visible cost — every transit square requires a phase-cast attack check.
- **4D phase op is 3.4× slower than chess4d's per-piece pseudo-legal** generators. This is the cleanest apples-to-apples comparison (both pure Python, neither has check filtering). The phase op pays for double work: phase generation + oracle filter (Solution A is intentionally wasteful by design — it's a *correctness* tool). A phase-native truncation (Solution B / C — see §11.4 in the 2D supplement for the original discussion) might close some of that gap, but Solution A is what landed in v1.3.0.
- **chess4d's full `legal_moves` is 15× slower than its own pseudo-legal** because of the multi-king check filter — 28 kings × per-move check verification adds up fast. This is intrinsic to O&C 4D chess, not a chess4d implementation issue.

**The castling extrapolation Steven asked about.**

The 2D phase op's castling overhead is ~22% (king-safety walk × 1 king × O(transit) attack checks). In 4D, **multi-king semantics multiply that cost by ~28**: every safety check during castling must verify *all* of the mover's kings remain safe (paper §3.4 Def 3 — "no king of the moving side is attacked afterwards"). So if 4D phase op castling were implemented, it would likely add **~28 × 22% ≈ 6× overhead** to the un-castled phase op time per position (admittedly with castling itself being a small fraction of total moves, but the per-castle-decision cost is large).

### §13.7.4 Was "phased maths faster than spatial maths" right?

**No, not in pure Python.** In 4D where both paths are pure Python, phase math is 3.4× *slower* than spatial math at the per-position level, because Solution A pays for both the phase candidates and the oracle filter. Even if Solutions B / C were implemented (phase-native truncation, no oracle), the constant factors of modular arithmetic + dict lookups are roughly comparable to the constant factors of ray-walking + bound checks. There's no obvious algorithmic win.

**Where phase math could plausibly win.**

1. **C / SIMD implementation with 64-bit modular ops.** Phase math sits naturally in 64-bit ints; bitboards in 4D would need 4096-bit operations (no native SIMD support on most CPUs). A future C 4D move generator might find phase math the easier path to vectorize.
2. **Vectorized over many positions** (e.g., a batch of game-tree leaves). The phase op's lookup table is a single flat dict; a numpy-style batched rewrite might amortize the per-call Python overhead. Spatial generators have more position-dependent control flow.
3. **As a representation for similarity / coordinate-free reasoning**, which is the *original* §11 motivation — not for raw move-gen speed.

**The right framing.** Phase math is a **correctness and structural-claim** tool: it lets us say "the 4D O&C piece geometry is fully captured by the φ_4d coprime cyclic phase structure" with a 36,864-assertion proof (the Phase B structural gate). For raw move-generation speed in 4D, the path forward is a C bitboard-style implementation, not an optimized phase op. Phase math validates the bitboard's correctness; bitboards run the searches.

Steven's "I might be losing that bet with myself" — yes, in pure Python; and the path to "actually faster" is C, not algorithmic refinement of the Python phase op.

---

## §13.8. Cross-Pollination Credits

The Othello Phase 1c work ([`docs/othello-maths/`](../othello-maths/)) produced two findings that propagate into this 4D pass:

1. **Patch 2 of [`CHESS_NOTEBOOK_PHASE_1C_PATCHES.md`](../othello-maths/CHESS_NOTEBOOK_PHASE_1C_PATCHES.md):** coprimality of axis generators with the modulus is necessary but not sufficient for image bijection. The 4D analogue of the Othello 2D counter-example `(p,q) = (3,7) mod 1024` would be a 4-tuple where each `g_i` is coprime to M but `g_x · Δx + g_y · Δy + g_z · Δz + g_w · Δw ≡ 0 (mod M)` admits a nonzero `Δ ∈ [-7,7]^4`. C2 above explicitly checks the image-bijection condition rather than relying on pairwise gcd.

2. **§3 Option B of [`OTHELLO_PHASE_OP_PREFLIGHT.md`](../othello-maths/OTHELLO_PHASE_OP_PREFLIGHT.md):** treat polarization-state attributes (Othello: Z₂ flip; 4D chess: pawn axis W/Y) as Z₂ channels in the encoder, aligned with the irrep decomposition's natural ± split. The 4D encoder's pawn-anti channel pair (W-axis, Y-axis) is exactly this construction; Phase E's pawn operator inherits it.

These findings originate in the Othello research record. **All six patches from `CHESS_NOTEBOOK_PHASE_1C_PATCHES.md` are also present in the 2D notebook** ([`chess_spectral_research_notebook.md`](chess_spectral_research_notebook.md)) — verified during PR #67 closure. Patches 1–5 sit at the documented locations (§9f line 1498, §10.4 line 2174, §10.10 line 2274, §10.12 line 2337, §10.13 line 2369), and Patch 6's audit (D₄ character-table class-constancy) was applied with the corrected `B₁ = [1,-1,1,-1,1,1,-1,-1]` and `B₂ = [1,-1,1,-1,-1,-1,1,1]` rows in [`chess_d4_direct.py`](chess-spectral/python/chess_d4_direct.py) and [`chess_spectral/tables.py`](chess-spectral/python/chess_spectral/tables.py); the §9a audit note (lines 1219–1284) documents the bug, the fix, and the downstream re-runs (most notably the previously-null "combined breaking" hypothesis, now confirmed at ρ = -0.310, p = 0.022). The Othello orphan-data loop is closed; PR #67 updated [`CHESS_NOTEBOOK_PHASE_1C_PATCHES.md`'s status header](../othello-maths/CHESS_NOTEBOOK_PHASE_1C_PATCHES.md) to **FULLY APPLIED** with citations.

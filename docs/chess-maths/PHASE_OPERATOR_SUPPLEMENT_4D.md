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
(M, g_x, g_y, g_z, g_w) = (12181, 1523, 191, 23, 3)
```

Constructed via the **mixed-radix tower discipline** in [`research/chess4d_phase_design.py`](chess-spectral/python/research/chess4d_phase_design.py):

```
g_w = 3                          # smallest admissible prime
g_z = next_prime(7·g_w + 1)      = next_prime(22) = 23
g_y = next_prime(7·(g_w+g_z)+1)  = next_prime(183) = 191
g_x = next_prime(7·sum_lower+1)  = next_prime(1520) = 1523
sum = 1740
M   = next coprime above 7·sum+1 = next coprime above 12181 = 12181
      (12181 = 13·937; coprime to 3, 23, 191, 1523)
```

The construction is the 4D analogue of the 2D pattern `(M, p, q) = (640, 67, 7)` with `7·8 + 7 = 63 < 67 < 640`, which mirrors the (recursive) tower bound here. By integer linear independence of distinct primes, no nonzero `Δ ∈ [-7,7]^4` satisfies `Σ Δ_i · g_i = 0`; combined with `|Σ Δ_i · g_i| ≤ 7·sum = 12180 < M`, modular reduction is a no-op and C2 is automatic.

**Brute-force fallback search.** The repo's [`research/chess4d_phase_design.py`](chess-spectral/python/research/chess4d_phase_design.py) also retains a numpy-vectorized brute-force search over M ∈ [4097, 16384] with `prime_limit=200`. That search finds nothing — *not because no design exists*, but because every valid 4-tuple has at least one prime > 200 (the tower's `g_x = 1523` exceeds the search ceiling). The search is kept as a verification tool: extending `prime_limit` to 2000 and running it would re-discover the tower's tuple. The directed mixed-radix construction is the canonical answer.

**Per-constraint verification** (output of `python research/chess4d_phase_design.py`):

| Constraint                    | Result                              |
|-------------------------------|-------------------------------------|
| C1 (coprime g_i to M)         | ✓ all four                          |
| C2 (image bijection)          | ✓ 4096 distinct phases mod 12181    |
| C3 (image not a subgroup)     | ✓ random-pair-sum escape detected   |
| C4 axis shifts (8 distinct)   | ✓                                   |
| C4 plane-diag shifts (24)     | ✓                                   |
| C4 knight shifts (48)         | ✓                                   |
| C4 king shifts (80)           | ✓                                   |
| C4 knight ∩ {axis ∪ pd ∪ king}| ∅ (knight uses ±2; others ±1)       |
| Total derived shifts          | 160 (axis ⊂ king and pd ⊂ king by  |
|                               | construction; 80 + 48 distinct = 128|
|                               | plus knight-to-king disjointness)   |

Constants pinned in [`chess_spectral/phase_operators_4d/phase_operators_4d.py`](chess-spectral/python/chess_spectral/phase_operators_4d/phase_operators_4d.py) as `MODULUS_4D = 12181`, `GEN_X = 1523`, `GEN_Y = 191`, `GEN_Z = 23`, `GEN_W = 3`. Validated by [`tests/test_phase_4d_design.py`](chess-spectral/python/tests/test_phase_4d_design.py) — 14 tests, all pass.

### §13.1.4 What this hypothesis would establish if confirmed

If P_p (Phase B) reproduces `tables_4d.X_targets` set-equal at every origin (Phase B gate = 4096 origins × 9 piece configs), then the O&C piece geometry on Z_8^4 is fully captured by the φ_4d coprime cyclic structure with no reference to (x,y,z,w) coordinates. The 4D lattice is redundant representation; the encoder's tensor-DCT structure (chess_spectral_4d_notebook.md Phase 2) plus the φ_4d phase shifts together encode the complete piece-movement structure of Oana-Chiru chess.

### §13.1.5 What this hypothesis would not establish

(Same caveat as 2D §11.1.3.) Nothing about whether 4D phase-space computation is faster, more accurate, or more revealing than 4D coordinate-space computation. Nothing about fog-of-war, partial observation, or 4D similarity structure. These are downstream experiments.

---

## §13.2. Phase Operator Specifications

> Will be populated by Phase B. Expected structure mirrors 2D §11.2:

- §13.2.1 Coordinate conventions (φ_4d as defined in §13.1).
- §13.2.2 P_rook4 — 8 axis generators, k ∈ ±{1..7}, 28 destinations interior.
- §13.2.3 P_bishop4 — 24 plane-diagonal generators, 6 plane choices × 4 sign combos × 7 distances; 2 connected components by parity (matches `tables_4d.bishop4_targets` connectivity).
- §13.2.4 P_queen4 = P_rook4 ∪ P_bishop4.
- §13.2.5 P_king4 — 80 shifts (3⁴ - 1 ternary sign vectors).
- §13.2.6 P_knight4 — 48 shifts (12 ordered axis pairs × 4 sign combos).
- §13.2.7 P_pawn4_white/black, parameterized by axis ∈ {'w', 'y'} per O&C Definition 11.
- §13.2.8 What's included and what's not.

---

## §13.3. Experiment 1: Equivalence on Empty Board (Phase B gate)

> Will be populated by Phase B. Expected:
>
> For each piece p ∈ {R, B, Q, K, N, P_w_white, P_w_black, P_y_white, P_y_black} and every origin (x,y,z,w) ∈ [0,7]^4, the φ_4d-derived destination set equals `tables_4d.X_targets(x,y,z,w)`.
>
> 4096 origins × 9 piece configs = 36 864 cell tests. Pass count:
> X / 36 864.

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

> Will be populated by Phase E. Expected:
>
> Per O&C Definition 11, pawns are oriented along Y or W axis only (never Z). The phase op's pawn capture geometry on the (axis, perpendicular-axis) plane, resolved against either the source paper or a documented best-fit consistent with the 2D capture pattern.

---

## §13.7. Discussion — what transferred from 2D, what's new at 4D

> Will be populated alongside §13.6. Expected highlights:
>
> - The coprime cyclic phase encoding lifts cleanly from 2D's Z_640 to 4D's Z_M. Constraint catalog is identical in form, only the dimension grows.
> - The validation oracle differs: 2D used `python-chess` legal moves; 4D uses our own `tables_4d.X_targets` + a 4D occupancy-aware spatial movegen. The 4D phase op is therefore validated against an in-repo reference, not an external one.
> - The pawn axis (W vs Y) is a Z₂ tag on the pawn polarization state. The 2D pawn has only a color tag (one Z₂); the 4D pawn has color × axis (two Z₂s). The encoder already uses this — channels 8 (W-axis antisym) and 9 (Y-axis antisym) are the two Z₂ sub-channels. The phase op inherits the structure.

---

## §13.8. Cross-Pollination Credits

The Othello Phase 1c work ([`docs/othello-maths/`](../othello-maths/)) produced two findings that propagate into this 4D pass:

1. **Patch 2 of [`CHESS_NOTEBOOK_PHASE_1C_PATCHES.md`](../othello-maths/CHESS_NOTEBOOK_PHASE_1C_PATCHES.md):** coprimality of axis generators with the modulus is necessary but not sufficient for image bijection. The 4D analogue of the Othello 2D counter-example `(p,q) = (3,7) mod 1024` would be a 4-tuple where each `g_i` is coprime to M but `g_x · Δx + g_y · Δy + g_z · Δz + g_w · Δw ≡ 0 (mod M)` admits a nonzero `Δ ∈ [-7,7]^4`. C2 above explicitly checks the image-bijection condition rather than relying on pairwise gcd.

2. **§3 Option B of [`OTHELLO_PHASE_OP_PREFLIGHT.md`](../othello-maths/OTHELLO_PHASE_OP_PREFLIGHT.md):** treat polarization-state attributes (Othello: Z₂ flip; 4D chess: pawn axis W/Y) as Z₂ channels in the encoder, aligned with the irrep decomposition's natural ± split. The 4D encoder's pawn-anti channel pair (W-axis, Y-axis) is exactly this construction; Phase E's pawn operator inherits it.

These findings originate in the Othello research record. Phase F of this work also propagates them back into the 2D notebook ([`chess_spectral_research_notebook.md`](chess_spectral_research_notebook.md) §10.4 + §9f patches, §10.13 reversi-scripts addendum).

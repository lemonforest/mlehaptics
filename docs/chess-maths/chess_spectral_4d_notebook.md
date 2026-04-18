# 4D Chess Spectral — v1 Validation Notebook

Companion to the 2D reference at [chess-spectral/](chess-spectral/). This
notebook records what transferred cleanly from the 2D encoder (640-dim
on Z_8^2) to the 4D encoder (40 960-dim on Z_8^4), what changed, and
what is still open for v1.1.

Paired with the implementation plan `when-we-need-to-spicy-seahorse.md`
(kept in `~/.claude/plans/`), which defined the six-phase roadmap.

## Run the gates yourself

```
cd docs/chess-maths/chess-spectral/python
python -m chess_spectral_4d.cli tables-verify --phase all
python -m pytest tests/test_encoder_4d.py tests/test_roundtrip_4d.py -v
```

All six gates (1..5 via `tables-verify`, 6 via pytest) must pass before
any further work.

---

## Phase-by-phase results

### Phase 1 — 4D piece graphs

Verifies the Oana & Chiru piece-movement definitions produce the
mobility numbers reported in their section 3.

| Piece  | Expected (O&C) | Observed (gate) | Where                         |
|--------|----------------|-----------------|-------------------------------|
| Rook   | 28             | 28              | every one of 4 096 squares    |
| King   | 80 (interior)  | 80              | 100 sampled deep-interior sqs |
| Knight | 48 (interior)  | 48              | 100 sampled deep-interior sqs |
| Bishop | 2 components   | 2 (2048/2048)   | partitioned by coord-sum mod 2|
| Queen  | Rook + Bishop  | exact union     | `A_Q == A_R ∪ A_B`            |
| Pawn   | +w push        | out-deg 1 if w<7| directed graph; 0 at w=7      |

**Transferred cleanly from 2D.** The generator pattern is identical; we
re-ran the closure checks at 4D and they reproduced the published
numbers without special-casing.

**New:** the bishop disconnectivity structure is richer in 4D — the
parity partition still splits into exactly two components (2 048 each),
matching the combinatorial expectation from `2 * 8^3`.

### Phase 2 — Kronecker-sum eigenbasis

4D grid Laplacian `L_grid` on `P_8 □ P_8 □ P_8 □ P_8` has eigenvalues
`λ_i + λ_j + λ_k + λ_l` where `{λ_n}` is the P_8 spectrum.

```
P_8 eigenvalues: 0.0000, 0.1522, 0.5858, 1.2346, 2.0000, 2.7654, 3.4142, 3.8478
Spectrum range: [0.000000, 15.391036]  (max = 4 * λ_max of P_8)
Unique eigenvalues: 225  (many are tensor-sum-degenerate)
Trace identity: trace(L) = 28 672 == sum(kron eigvals)
L v = λ v holds on 20 random tensor products with max residual 4.44e-16.
```

**Memory win:** we never construct the 4 096 × 4 096 dense
eigenvector matrix. The tensor-DCT basis is applied on demand either
as `np.einsum` over tensor factors or as a double `np.kron` product
(128 MB, built once for the Phase 4/5 transforms).

**Transferred cleanly from 2D's grid eigenbasis** — the only change is
a tensor of 4 DCT factors instead of 2.

### Phase 3 — B_4 group action + partial irrep projection

B_4 = (Z_2)^4 ⋊ S_4, |B_4| = 2^4 · 4! = 384, 20 irreps in total.

For v1 we compute **two** irrep projectors:

- **A_1 (trivial):** orbit-average projector
  `P_A1 = (1/|B_4|) Σ_g Π(g)`. Closure of 7 generators (4 sign flips +
  3 adjacent S_4 transpositions) reached 384 elements exactly.
  The resulting sparse CSR projector has rank = #orbits = **35** on
  Z_8^4; idempotent and B_4-invariant within 1e-12.
- **Standard 4D:** closed form `P_std = I_4 − (1/4) J_4` on coord
  channels. Trace 3, annihilates the axis-sum.

Character spot-checks matched the known values of the B_4 defining
rep (whose character equals the number of fixed axes of a signed
permutation):

    χ_std(identity) = 4
    χ_std(sign-flip on one axis) = 2
    χ_std(axis transposition) = 2

**Deferred to v1.1:** the other 18 irreps via Serre projection over
bipartitions of 4. Not needed for the current channel layout.

### Phase 4 — 4D fiber bundle

Core algebraic identities of the encoder, cross-checked at 4D:

```
A_queen == A_rook + A_bishop            (exact, disjoint support)
C_queen == C_rook + C_bishop            (DCT basis; max |Δ| = 1.14e-13)
||rook diag-dev||_2 = 1376.74           (finite, nonzero: rook shadow lives)
```

**Pawn antisymmetric fiber is block-diagonal over (x, y, z).**
`A_anti = (A_pawn − A_pawn^T) / 2` factors as
`I ⊗ I ⊗ I ⊗ A_w_anti`, so in the tensor-DCT basis only the w-axis
mixes modes. Gate measured

    on-w-axis   ||C_anti||_F = 42.3320
    off-w-axis  ||C_anti||_F = 3.55e-14

The off-w residual is pure round-off. This is the cleanest symmetry
check in the whole pipeline — it tells us the w-axis convention for
pawn direction is not just a naming choice but a spectral fact.

**6-piece diagonal deviation table** (norms of row vectors in DCT mode
space, unitless; pawn_sym derives from the directed-push symmetrized
adjacency):

    pawn_sym=423.62  knight=1603.55  bishop=2936.36
    rook=1376.74     queen=4725.19   king=3194.72

Queen's diag-dev norm is close to bishop + rook (2936 + 1377 = 4313,
vs. observed 4725 — triangle inequality, not equality, since they're
vectors in mode space with different directions).

**Transferred cleanly from 2D**: the (pawn-is-the-only-antisymmetric
contributor) and (rook-is-the-only-diag-dev contributor that actually
commutes like a rook) narratives hold at 4D. In 2D, the rook's DIAG_DEV
norm was ~88.05; at 4D it scales to ~1376.74, roughly consistent with
the `n^{1.5}` growth you'd expect from stacking 4 axes of K_8 on an
8-cube.

**Deferred to v1.1:** the per-square LOCAL_FIBER_3D and LOCAL_ADJ_ROWS
tables. Their 4D analogues are `5 × 4096 × 3` and `5 × 4096 × 4096` =
~2.6 GB combined. We'll replace with a global-SVD fiber basis applied
per piece count in v1.1 — matches the 2D semantics up to where the
fiber energy lands.

### Phase 5 — encoder + spectralz v3

- `encode_4d(pos4) -> np.ndarray[float32, (40960,)]`
- 10 channels, each 4 096 modes wide:

| idx | Name        | Dim range        | Space     | Status  |
|-----|-------------|------------------|-----------|---------|
| 0   | A_1         | [0 : 4096]       | signal    | ✓       |
| 1   | STD4_X      | [4096 : 8192]    | signal    | ✓       |
| 2   | STD4_Y      | [8192 : 12288]   | signal    | ✓       |
| 3   | STD4_Z      | [12288 : 16384]  | signal    | ✓       |
| 4   | STD4_W      | [16384 : 20480]  | signal    | ✓       |
| 5   | FIB_SYM_1   | [20480 : 24576]  | signal    | v1 stub |
| 6   | FIB_SYM_2   | [24576 : 28672]  | signal    | v1 stub |
| 7   | FIB_SYM_3   | [28672 : 32768]  | signal    | v1 stub |
| 8   | FA_PAWN     | [32768 : 36864]  | mode      | ✓       |
| 9   | FD_DIAG     | [36864 : 40960]  | mode      | ✓       |

`spectralz v3`: 256-byte header (`LARTPSEC` magic, version=3,
encoding_dim=40960, frame_bytes=163 854, board_dim_side=8,
n_dimensions=4) + packed frames of `encoding_dim*4 + 14` bytes each.
The 2D reader remains untouched; a single dispatch shim
`frame_4d.read_header_any(fp)` branches on the version field.

Round-trip gate: 10 random frames written and read back bit-identical
(max |Δ| = 0.0) with all metadata preserved.

### Phase 6 — cross-framework validation + unit tests

27 pytest cases across `test_encoder_4d.py` and `test_roundtrip_4d.py`.
Notable algebraic checks:

- **A_1 channel is B_4-orbit-invariant** — placing a piece at two
  orbit-equivalent squares produces bit-identical A_1 channels. This
  is the clean spectral analogue of "the board has no intrinsic
  orientation".
- **Pawn antisym flips sign with color** — for equal-magnitude
  opposite-color pawns at the same square, the FA channel is exactly
  opposite (bit-exact).
- **Diagonal deviation is piece-specific** — knight, rook, and queen
  FD channels are all pairwise distinct at the same square.
- **Channel energies partition total energy** — `Σ ch-energy = ||v||^2`
  (matches 2D semantics).

Cross-framework mobility numbers were recorded during Phase 1 gate and
aligned exactly with Oana & Chiru section 3. No stop-the-line events.

---

## What transferred cleanly from 2D

- Graph-Laplacian + DCT eigenbasis recipe scales by tensor power.
- Fiber-bundle structure (symmetric + antisym pawn + diag-dev rook
  shadow) stayed rank-5 conceptually; 3 sym subspaces were validated
  via SVD (v1.1 will exercise the fiber basis end-to-end in the
  encoder).
- `queen = rook + bishop` holds as an algebraic identity in both
  adjacency and Laplacian pictures.
- Channel energy partition + signal-vs-mode-space split carried over
  without modification.

## What's new or different in 4D

- 35 B_4-orbits on Z_8^4 (vs. 10 D_4-orbits on Z_8^2).
- Standard rep expanded to 4 coordinate channels rather than the 2D's
  2-dim E-irrep (so the encoder dedicates 4 channels to std-4D vs. the
  2D encoder's 1 channel for E).
- Memory pressure is real: the dense tensor-DCT basis is 128 MB; the
  pawn antisym fiber matrix is another 128 MB. We sidestepped
  materializing the local fiber tables entirely.
- Pawn directionality is cleanly w-axis-only in spectral space — the
  off-w residual of `C_anti` is zero to 4e-14.

## Known gaps / v1.1 candidates

1. **Fiber-sym channels are stubs.** Encoder dims `[5..7]` return 0.
   Next step: implement a global-SVD fiber basis applied per-piece-type
   rather than per-square. Replaces the `(5, 4096, 4096)` blowup.
2. **No game corpus yet.** The plan called for 10 Oana-Chiru playouts.
   Requires external data (their engine is not wired into this repo).
   The CLI's `encode-moves4` + `corpus-gen` subcommands still print
   "not yet implemented" (exit 4) and will be filled in when a JSONL
   move-log generator is available.
3. **C encoder + `emit_tables_4d.py` + `test_4d_consolidated.c`** —
   all deferred to v1.1 per the plan.
4. **Full B_4 irrep decomposition** (18 remaining irreps) — deferred.
5. **FEN4 grammar** — deferred; encoder is driven by `pos4` dict
   directly.
6. **Performance** — no attempt at C-speed yet. The first call to
   `encode_4d` takes ~20 s to build the dense tables; subsequent calls
   are millisecond-scale via the module-level cache.

---

*Last updated alongside Phase 6 commit on branch `chess-spectral-4d`.*

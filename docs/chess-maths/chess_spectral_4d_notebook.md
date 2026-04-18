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

**Shipped in v1.1:** per-square fiber coordinates on the rank-3
cross-piece SVD basis. Instead of materializing the 2.6 GB `(5, 4096,
4096)` local adjacency tables of the naive 2D analogue, we build one
signal-space fiber matrix per direction — `K_d = U F_d U^T`, where
`F_d` reconstructs the d-th cross-piece SVD fiber direction as a
symmetric zero-diagonal `(4096, 4096)` matrix — and accumulate
`fib_d(p, s) = Σ_{t ∈ adj_p(s)} K_d[s, t]` per piece/square/direction.
Resulting table: `FIBER_LOCAL[5, 4096, 3]` float32 = 240 KB runtime.
Peak build memory: ~200 MB (U + one K_d).

Rook is dropped from the SVD and its `FIBER_LOCAL` row is held at
zero — rook's global off-diag is identically zero, so any non-zero
per-square `fib_d(rook, s)` would be an artifact of the local
decomposition, not a genuine fiber participation. The rook-only-zero
test encodes this discipline.

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
| 5   | FIB_SYM_1   | [20480 : 24576]  | signal    | ✓ (v1.1) |
| 6   | FIB_SYM_2   | [24576 : 28672]  | signal    | ✓ (v1.1) |
| 7   | FIB_SYM_3   | [28672 : 32768]  | signal    | ✓ (v1.1) |
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

1. **No game corpus yet.** The plan called for 10 Oana-Chiru playouts.
   Requires external data (their engine is not wired into this repo).
   The CLI's `encode-moves4` + `corpus-gen` subcommands still print
   "not yet implemented" (exit 4) and will be filled in when a JSONL
   move-log generator is available.
2. **C encoder + `emit_tables_4d.py` + `test_4d_consolidated.c`** —
   all deferred to v1.1 per the plan.
3. **Full B_4 irrep decomposition** (18 remaining irreps) — deferred.
4. **FEN4 grammar** — deferred; encoder is driven by `pos4` dict
   directly.
5. **Performance** — no attempt at C-speed yet. The first call to
   `encode_4d` takes ~60 s to build the dense tables (U tensor +
   pawn-antisym + diag-dev + 3 K_d fiber matrices); subsequent calls
   are millisecond-scale via the module-level cache.

---

## v1.1 investigation: empirical fiber rank

Follow-up to the v1 stub decision in Phase 4. Two analysis scripts
produced the input numbers:

- `chess-spectral/python/analyze_fiber_rank_4d.py` — cross-piece SVD
  on `Z_8^4`
- `chess-spectral/python/direct_orthogonality.py` +
  `chess-spectral/python/staged_cosine.py` — localize which matrix
  representation the rank-3 result actually lives in (answer: the
  `off-diag(U^T L U)` representation specifically; see the two-claim
  section below for the sharper reading)

### Cross-piece SVD singular values (grid-DCT basis, off-diagonal)

Normalized flattened upper-triangles of `C_p = U^T L_p U` stacked as
rows; rook dropped because its off-diagonal vanishes identically (see
below). Thin SVD on the 4-row matrix.

|                | leading σ | σ₂     | σ₃     | σ₄     | rank @ 10% | rank @ 1% |
|----------------|-----------|--------|--------|--------|------------|-----------|
| 2D (Z_8²)      | 1.70      | 0.82   | 0.65   | 0.00   | **3**      | 3         |
| 4D (Z_8⁴)      | 1.83      | 0.65   | 0.49   | 0.00   | **3**      | 3         |

**Fiber rank = 3 in both dimensions.** The σ₄ zero is algebraic (queen
≡ bishop in fiber space, see below), not numerical. Leading σ grew
slightly in 4D; σ₂ and σ₃ shrank — 4D fiber couplings concentrate more
energy in the leading direction than 2D.

### Two structural facts that force rank < #pieces

**(i) Rook fiber vanishes identically.** The K_8 Laplacian has spectrum
`{0, 8, 8, …, 8}`; the DC P_8 eigenvector is the K_8 nullvector and
every non-DC P_8 DCT column lies in the 8-eigenspace (it is orthogonal
to the 1-vector). So `U_P8^T L_K8 U_P8 = diag(0, 8, 8, 8, 8, 8, 8, 8)`
— diagonal. The 4D rook Laplacian is a Kronecker sum of four K_8
Laplacians, diagonal in the tensor-DCT basis, and so has
`C_rook_off ≡ 0` exactly.

Measured:
- 2D: `||C_rook_off||_F = 3.78e-13` (round-off at dim 64)
- 4D: `||C_rook_off||_F = 2.8e-13` (round-off at dim 4096)

This is **not** a 4D-specific property — the 2D rook also vanishes
identically in the DCT basis. The original 2D
`chess_spectral/tables.py` code already omits rook from its cross-piece
SVD (it iterates `['Knight', 'King', 'Bishop', 'Queen']`), which
implicitly encoded this fact without ever naming it.

**(ii) Queen ≡ Bishop in fiber space.** `A_queen = A_rook + A_bishop`,
so `C_queen = C_rook + C_bishop`. With `C_rook` diagonal,
`C_queen_off = C_bishop_off` exactly. Verified bit-identical:

- 2D: `||C_bishop_off||_F = ||C_queen_off||_F = 14.83435`
- 4D: `||C_bishop_off||_F = ||C_queen_off||_F = 370.6751`

So the five piece Laplacians collapse to three independent fiber
directions (knight, bishop/queen, king) in both dimensions.

### Staged cosine progression — where does rank-3 emerge?

The rank-3 result is a property of a specific matrix representation. To
locate *which* representation gives it, compute Frobenius cosines
between piece pairs at four successive stages (see
`staged_cosine.py`):

```
stage 1 — raw Laplacian         L = D - A
stage 2 — raw adjacency         A
stage 3 — centered adjacency    A - mean(A) · J/N²
stage 4 — DCT off-diagonal      off-diag(U^T L U)
```

Each stage strips one layer. Numbers:

**2D (Z_8²):**

| pair           | raw L  | raw A  | cent. A | DCT off |
|----------------|--------|--------|---------|---------|
| knight-rook    | 0.8381 | 0.0000 | -0.1582 | -0.02*  |
| knight-bishop  | 0.8638 | 0.0000 | -0.1190 |  0.4657 |
| knight-queen   | 0.8698 | 0.0000 | -0.2220 |  0.4657 |
| knight-king    | 0.8495 | 0.0000 | -0.1010 |  0.5089 |
| bishop-rook    | 0.8973 | 0.0000 | -0.2106 | -0.02*  |
| bishop-queen   | 0.9616 | 0.6202 |  0.5359 |  1.0000 |
| rook-queen     | 0.9840 | 0.7845 |  0.7125 | -0.02*  |

**4D (Z_8⁴):**

| pair           | raw L  | raw A  | cent. A | DCT off |
|----------------|--------|--------|---------|---------|
| knight-rook    | 0.9371 | 0.0000 | -0.0073 |  0.15*  |
| knight-bishop  | 0.9682 | 0.0000 | -0.0100 |  0.7168 |
| knight-queen   | 0.9652 | 0.0000 | -0.0125 |  0.7168 |
| knight-king    | 0.9639 | 0.0000 | -0.0104 |  0.7603 |
| bishop-rook    | 0.9645 | 0.0000 | -0.0095 |  0.10*  |
| bishop-queen   | 0.9957 | 0.8076 |  0.8048 |  1.0000 |
| rook-queen     | 0.9848 | 0.5898 |  0.5859 |  0.10*  |

`*` rook-involving cosines at stage 4 are numerically undefined (rook
off-diag norm is 1e-13). The printed values are noise / noise.

**What we learn at each stage:**

- **Stage 1 (raw L):** every piece-pair cosine is 0.83–0.99. Dominated
  by the degree matrices on the diagonal. No discriminative
  information.
- **Stage 2 (raw A):** every distinct-support pair is **exactly zero**.
  Knight edges are not rook edges, rook edges are not bishop edges,
  etc. The nonzero pairs are those where one piece's edge set contains
  the other (queen ⊃ bishop, queen ⊃ rook). This orthogonality is
  trivial — it reflects disjoint edge support, not any spectral
  property.
- **Stage 3 (centered A):** removing the scalar mean barely changes
  anything (cosines shift by ~0.01–0.2). The DC-DC correction is small
  because piece adjacencies are already sparse.
- **Stage 4 (DCT off-diag):** the picture flips. Knight-bishop,
  knight-queen, knight-king become strongly positive (0.47–0.76).
  Bishop-queen collapses to exactly 1.0 (degeneracy). Everything
  involving rook vanishes (rook fiber identically zero). This is where
  the rank-3 cross-piece SVD lives.

### Interpretation

The Stage 2 → Stage 4 flip is the key finding. In the raw adjacency
representation, pieces with disjoint edge support are trivially
orthogonal — but that orthogonality gives **rank 4 (knight + bishop +
rook + king)**, not rank 3. Queen is a linear combination, rook is
not. Five pieces → rank 4 trivial independence.

The DCT projection discards one more dimension — rook — by diagonalizing
the K_8 Kronecker sum. Queen then equals bishop. Five pieces → rank 3
*structural* independence.

So the rank-3 claim has a specific content:

- It is **not** a property of the raw graph Laplacians or their
  adjacency matrices (both of those give rank 4 after normalization).
- It **is** a property of the piece Laplacians viewed in the grid
  (tensor-)DCT basis, after removing the basis's diagonal component.
- The rank value (3 rather than 4) is forced by **rook's
  Kronecker-sum structure**: `L_rook` is a sum of K_8 Laplacians along
  each axis, each of which commutes with the DC/non-DC split of the
  DCT basis.
- The rank holding at **3 across both 2D and 4D** is therefore a claim
  about the grid-DCT representation being uniform-across-dimensions
  for this piece set, not a claim about intrinsic graph invariants.

For the v1.1 encoder this means the rank-3 basis is the right thing to
ship — it captures the non-trivial shared structure. The narrative to
put in prose, though, is "rank-3 in the grid-DCT off-diagonal
representation" not "rank-3 graph invariant".

---

## Two claims about piece-graph structure

The v1.1 investigation produced **two distinct structural claims**
about chess piece graphs. They live on different objects and are
easily confused. The test suite pins each of them to its own gate.

### Claim 1 — Edge-support orthogonality (graph-theoretic, basis-free)

**Statement.** The binary adjacency matrices `A_knight`, `A_bishop`,
`A_rook` share no edges pairwise, and the knight is edge-disjoint from
the king:

    <A_p, A_q>_F = Σ_{i,j} A_p[i,j] · A_q[i,j] = 0  exactly (integer)

for `(p, q)` in `{(knight, bishop), (knight, rook), (bishop, rook),
(knight, king)}` in both `Z_8^2` and `Z_8^4`.

**Basis independence.** The Frobenius inner product of two binary
matrices is an integer edge-overlap count. It does not care about any
eigenbasis; it is invariant under any orthogonal change of basis on
either vertex set only up to the reindexing of edges. Orthogonality
here means literally "no shared edges", not any spectral claim.

**Gate.** `tests/test_edge_support_orthogonality.py` (20 tests,
integer-typed assertions). All pass on `int64` dtype — zero is exactly
zero, not 1e-13.

### Claim 2 — Grid-spectral rank-3 (basis-dependent, representation-specific)

**Statement.** When each piece's graph Laplacian is pushed into the
tensor-DCT basis of the grid and the diagonal is zeroed, the resulting
`C_off_p = off-diag(U^T L_p U)` vectors for `p ∈ {knight, bishop,
rook, queen, king}` span a rank-3 subspace (σ₄ ≈ 0 is algebraic, not
numerical).

**Basis dependence, explicit.** The number 3 here is a property of
(a) the grid-DCT basis `U`, (b) the off-diagonal projection, (c) the
specific piece set. Change any of these and the rank changes. In
particular:

- In the raw adjacency basis the five pieces already drop to rank 4
  by `A_queen = A_bishop + A_rook` (Claim 1's trivial queen partition
  lifted to a linear identity).
- In the raw Laplacian basis the five pieces are all pairwise cosine
  ≈ 0.9 and look full-rank at any tolerance — the degree diagonal
  dominates.

The rank-3 claim is therefore "in this representation, with this
diagonal-strip convention, rook is algebraically zero and queen
collapses onto bishop". It is the right thing to encode into the
fiber-sym channels because it captures the shared-structure directions
that the `off-diag(U^T L U)` recipe can see. It is **not** an intrinsic
graph property and should not be described as "basis-independent".

### What v1.1 tooling does not claim

Earlier drafts of this notebook used language like "intrinsic
geometry" and "basis-independent rank-3 result" for the cross-piece
SVD finding. Those readings are wrong. Claim 2 is a representation-
specific fact about a specific spectral basis; Claim 1 is a trivial
graph-theoretic fact about disjoint edge supports. Conflating them
obscures what is being measured.

---

## Primitives-plus-sums decomposition

Claim 1 refines into a cleaner structural statement that classifies
the piece set into primitives and their compositions. This language
generalizes to 4D with a sharp dimension-sensitive twist.

### Primitives and sums in 2D

**Primitives** (pairwise edge-disjoint): `knight`, `bishop`, `rook`.

**Queen as an edge sum.** `A_queen = A_bishop + A_rook` exactly as
sets. Equivalently `<A_B, A_Q> + <A_R, A_Q> = <A_Q, A_Q>`.

**King as an edge sum (2D only).** Every king edge is either a
distance-1 diagonal (one-step bishop) or a distance-1 orthogonal
(one-step rook). So `<A_B, A_K> + <A_R, A_K> = <A_K, A_K>` exactly.
The 2D king's move set is fully generated by the one-step primitives.

**Knight does not participate.** Knight is edge-disjoint from every
other piece: its (2,1)-leap never coincides with any one-step or
slider edge. Knight is the only piece whose movement is not expressible
as any sum of one-step primitive components.

### Dimension-sensitive king in 4D

The 4D king's move set is Chebyshev-1 in the full 4-dimensional sense:
any cell reachable by changing 1, 2, 3, or 4 coordinates by ±1
simultaneously. This decomposes by Hamming distance of the move
displacement:

| HD class | displacement                  | count (interior) | matches...            |
|----------|-------------------------------|------------------|-----------------------|
| HD = 1   | ±1 on one axis                | `C(4,1) · 2 = 8` | one-step rook         |
| HD = 2   | ±1 on two axes                | `C(4,2) · 4 = 24`| one-step bishop       |
| HD = 3   | ±1 on three axes              | `C(4,3) · 8 = 32`| **none** (un-named)   |
| HD = 4   | ±1 on all four axes           | `C(4,4) · 16= 16`| **none** (un-named)   |
| **total**|                               | **80**           | Oana & Chiru interior |

In 4D the one-step bishop + one-step rook strictly under-counts the
king: `<A_B, A_K> + <A_R, A_K> < <A_K, A_K>`, and the deficit splits
exactly into the HD=3 and HD=4 subgraphs of the king. The test file
`test_4d_king_hd_partition_exact` asserts the full four-way partition.

### Candidate pieces for the 4D HD=3 and HD=4 residuals (research note)

The 4D king includes move classes that have no independently named
piece in the codebase:

- **Trihedral stepper (HD = 3 one-step).** Displacement = `(±1, ±1,
  ±1, 0)` and permutations. 32 interior moves. Geometrically: "corner
  of a 3-cube inside a 4-cell move along three coordinate axes at once".
- **Tetrahedral stepper (HD = 4 one-step).** Displacement = `(±1, ±1,
  ±1, ±1)`. 16 interior moves. Geometrically: "corner of the
  4-hypercube along all four axes at once".

These are well-defined graph primitives — their adjacencies would
integrate cleanly into the primitives-plus-sums decomposition. The
framework is agnostic to whether Oana & Chiru or any downstream
ruleset names them. What the spectral machinery surfaces is that the
**named** piece vocabulary `{pawn, knight, bishop, rook, queen, king}`
under-specifies the 4D geometric primitives by exactly two classes.
This is the kind of finding a purely top-down axiomatic ruleset is
unlikely to notice.

**This is a dimension-sensitive fact.** In 2D, HD ∈ {1, 2} is exhaustive
for Chebyshev-1 and the named pieces cover the ground. In 4D, HD can
reach 3 or 4 and the named pieces miss those classes. The spectral
framework is dimension-blind (the recipe doesn't change); the piece
vocabulary happens to be two-dimensional by default.

### Knight as sui generis: a speculative link to Claim 2

Knight is the only piece that is edge-disjoint from every other named
piece, including from the king (whose closure covers HD 1–4 one-step).
It cannot be written as a sum of any other piece's edges at any
distance. The (2,1)-leap is topologically isolated from one-step motion.

Does this graph-level isolation explain why, in Claim 2, the knight
contributes an independent direction in the grid-DCT off-diagonal
subspace distinct from the bishop+queen direction and the king
direction?

The conjecture is: an edge set that lies in no other piece's closure
cannot be a linear combination of them in `off-diag(U^T L U)` either,
so it must add a spectral direction. The converse (pieces in one
another's closures collapse) holds trivially: `queen = bishop + rook`
at the edge level forces `C_off_queen = C_off_bishop + C_off_rook` at
the spectral level.

This is **speculative**. The implication from edge-disjointness to
spectral independence is only one-way obvious (edge-disjoint pieces
have orthogonal raw adjacencies, but that is Claim 1, not Claim 2).
The claim that they also span independent directions *after* the DCT
projection and off-diagonal strip requires more work to make rigorous.
Logged here as a bridge between the two claims rather than a proof.

---

*Last updated with v1.1 fiber wiring, edge-support orthogonality gate,
and two-claim / primitives-plus-sums reframing on branch
`chess-spectral-4d`.*

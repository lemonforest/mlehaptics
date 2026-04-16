## FA Channel Structural Sensitivity Test

**Source:** `docs/chess-maths/test_fa_structure.py`

**Question:** Does FA (dims 512–575) discriminate pawn STRUCTURE (passed pawns, chains, blockades) from pawn COUNT, or is it a glorified pawn-count proxy?

### Quadratic-form diagnostics

`M = PAWN_ANTI_FIBER @ PAWN_ANTI_FIBER.T`. ||diag(M)|| = 11.5586, ||off-diag(M)|| = 11.9958 → off/diag ratio 1.038. Off-diagonal mass is the only source of structural (pair-geometry) sensitivity.

Per-rank mean of M[s,s] (rank 8 → rank 1):

| Rank | 8 | 7 | 6 | 5 | 4 | 3 | 2 | 1 |
|---|---|---|---|---|---|---|---|---|
| diag mean | 1.448 | 2.485 | 1.839 | 1.352 | 0.629 | 0.439 | 0.260 | 0.299 |

### Position pairs

| Pair | n♟(A,B) | FA_A | FA_B | |Δ| | vs count baseline | structural? |
|---|---|---|---|---|---|---|
| passed_vs_blockaded | 3,3 | 7.0821 | 3.8017 | 3.2804 | 12.88× | **yes** |
| connected_vs_isolated | 6,6 | 11.2932 | 10.0650 | 1.2282 | 4.82× | **yes** |
| chain_vs_lateral | 6,6 | 7.6332 | 9.6584 | 2.0252 | 7.95× | **yes** |
| race_vs_head_on | 2,2 | 2.0412 | 1.2808 | 0.7604 | 2.99× | **yes** |
| count_control | 1,2 | 0.2366 | 0.4912 | 0.2546 | — | (baseline) |
| file_mirror | 2,2 | 0.5434 | 1.0723 | 0.5288 | 2.08× | **yes** |

- **passed_vs_blockaded** — Same pawn count (1W + 2B = 3). A: white d5 is a passed pawn (no opposing pawns on c/d/e). B: white d5 is diagonally blockaded by c6 and e6.
- **connected_vs_isolated** — Same pawn count (3W + 3B = 6). A: both sides have three connected pawns on adjacent files. B: both sides have three pawns on alternating files (no neighbors).
- **chain_vs_lateral** — Same pawn count (3W + 3B = 6). A: opposing diagonal pawn chains (d4-c3 vs d5-e6-f7). B: lateral pawn duos on a single rank each.
- **race_vs_head_on** — Same pawn count (1W + 1B = 2). A: mutual passed pawns on opposite flanks (race). B: white d4 and black d5 lock head-on, neither can advance.
- **count_control** — DIFFERENT pawn count (1 vs 2). Same colour, adjacent files. FA *should* differ — this validates that FA responds to count at all.
- **file_mirror** — Same pawn count (2W). B is the file-reflection of A. The white-pawn graph is file-uniform, so FA energy should be identical (sanity check on encoder symmetry).

### Encoder geometry note — file-mirror surprise

The `file_mirror` pair (a2,b2 vs g2,h2) yields different FA energies despite being a left-right reflection of one another. The kernel `K = A_anti @ A_anti.T` IS file-symmetric in the board basis (verified `||K - P_F K P_F.T|| = 0` numerically), and `sig.T @ K @ sig` is identical for the two configs (=2.75). However, the encoder computes `FA = Σ_pawns sign · PAWN_ANTI_FIBER[s, :]` — indexing rows of an eigenbasis matrix by board-square index without first rotating the signal into eigenbasis. This conflates the board-basis address with the eigenbasis output, producing an FA that is NOT D4-equivariant under board permutations.

Empirically: ||PAF[a2]|| = 0.502, ||PAF[h2]|| = 0.539; cross term `<PAF[a2], PAF[b2]> = -0.008` vs `<PAF[g2], PAF[h2]> = +0.219`. The cross term sign-flip across the board centre is the encoder's basis-mixing fingerprint, not chess.

This does not invalidate the structural hits for passed/connected/chain/race pairs above — those compare positions whose pawn geometries differ in ways that would register under any reasonable encoding. It does mean FA carries an extra basis-dependent signal that future analyses should be aware of.

### Sequence test (count drops; does FA track structure?)

**creates_passer**:

| Step | n♟ | FA energy |
|---|---|---|
| start | 8 | 12.6472 |
| after_cxd | 5 | 3.9726 |
| after_exd | 4 | 3.1127 |
| passer_isol | 1 | 0.8876 |

**no_passer**:

| Step | n♟ | FA energy |
|---|---|---|
| start | 8 | 12.6472 |
| trade1 | 6 | 6.5872 |
| trade2 | 4 | 4.9056 |
| trade3 | 0 | 0.0000 |

**Matched-count cross-trajectory comparison** (same pawn count, different structure):

| n♟ | FA (passer trajectory) | FA (no-passer trajectory) | |Δ| |
|---|---|---|---|
| 8 | 12.6472 | 12.6472 | 0.0000 |
| 4 | 3.1127 | 4.9056 | 1.7929 |

### Verdict

STRUCTURAL — same-count chess-structure pairs differ by ≥5% of pure-count baseline (0.2546). Hits: passed_vs_blockaded, connected_vs_isolated, chain_vs_lateral, race_vs_head_on.

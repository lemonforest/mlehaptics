# Chess channel rationale + hyper-wrap parallel-ops — findings (2026-05-11)

**Spike:** User question 2026-05-11: "have them look at chess2d and chess4d to find out why flat board with x,y coords is 10 channel dims and chess4d with w,x,y,z is 11 channel dims. what if we somehow had a reason to wrap it inside a hyper object such that we could perform parallel operations?" Two sub-questions: (A) what does the EXTRA 11th channel in 4D encode? (B) could a hyper-wrap of the channel dim enable parallel ops?

**Method:** Concertmaster role, MPM-discipline. Read encoder source code (qm_2d.py, qm_4d.py, encoder.py, encoder_4d.py, qm_2d_dynamics.py, qm_4d_dynamics.py). Build synthetic chess-scale Laplacian benchmarks comparing three propagator paths.

**Dispatch:** Conductor → concertmaster, 2026-05-11. Single dispatch.

**Bottom line:** **(A)** Chess-2D's 10 channels are NOT one-per-piece — they are **5 D₄ irrep projections + 3 symmetric-fiber + FA-pawn + FD-diagonal**. Chess-4D's 11 channels are **1 A₁ orbit + 4 STD4-axis residuals (X/Y/Z/W) + 3 symmetric-fiber + 2 FA-pawn-axis (W/Y per Oana-Chiru) + 1 FD-diagonal**. **The "extra" 11th channel arises from two independent splits**: STD4 expands the 2D's three non-trivial 1D irreps (A₂, B₁, B₂) into four axis-residual channels (one per spatial axis of the 4D base), AND FA splits into two axis-specific pawn channels per Oana-Chiru Definition 11 (pawns oriented on Y or W axis, never Z). Net: 2D has +5 base-irreps - 4 STD4 = 1 fewer channel from the irrep side, +1 from the pawn-axis split, +0 from fiber-sym (both 3) and FD (both 1). Math reconciles. **(B)** The chess H₀ free-particle propagator is **strictly block-diagonal across channels with bit-identical blocks** (`H_full = I_{N_CHANNELS} ⊗ H₀`, off-block nnz = 0, max block-diff = 0.0 at machine precision in both 2D and 4D). The "hyper-wrap" for parallel ops is real: a single batched-einsum eigenbasis propagator gives **~196× speedup at chess-2D scale** (10.4 ms → 0.053 ms per call). At chess-4D scale **the speedup VANISHES** — the 4096-dim dense eigendecomposition costs 124 seconds one-shot and per-call is 722 ms (12× SLOWER than the current sparse path); amortization breakeven is infinite. Honest finding: math-doesn't-lie. Per-channel SIMD via einsum is a 2D-scale win, not a 4D-scale win.

Reproducible: `python docs/srmech/notes/chess-channels-and-hyper-parallel-script.py`. Runtime ~3 min on commodity workstation (the 4D eigendecomposition dominates). Deterministic seed `20260511`.

---

## 1 — Channel rationale: 10-vs-11 decoded

### 1.1 — chess-2D — 10 channels × 64 dims = 640 total

Source: [`encoder.py:91-95`](../../chess-maths/chess-spectral/python/chess_spectral/encoder.py), [`qm_2d.py:38-41`](../../chess-maths/chess-spectral/python/chess_spectral/qm_2d.py).

| Channel | Slice | Semantic role | Group-theoretic anchor |
|---|---|---|---|
| **A1** | 0:64 | D₄ trivial irrep (totally symmetric signal) | 1-dim D₄ irrep |
| **A2** | 64:128 | D₄ sign-of-rotation irrep | 1-dim D₄ irrep |
| **B1** | 128:192 | D₄ diagonal-flip irrep | 1-dim D₄ irrep |
| **B2** | 192:256 | D₄ anti-diagonal-flip irrep | 1-dim D₄ irrep |
| **E** | 256:320 | D₄ 2-dim standard irrep | 2-dim D₄ irrep |
| **F1, F2, F3** | 320:512 | Symmetric-fiber: per-piece local Laplacians projected onto 3D fiber basis (knight, bishop=queen, king contribute 3 independent directions) | Cross-piece SVD rank-3 basis |
| **FA** | 512:576 | Antisymmetric pawn fiber: `(A_white_pawn - A_white_pawn.T)/2` in grid eigenbasis | Antisymmetric / pawn-direction |
| **FD** | 576:640 | Diagonal deviation: `diag(EVECS.T @ L_piece @ EVECS) - EVALS_GRID`, signed-piece-weighted | Rook-shadow / per-piece eigenvalue split |

**5 D₄ irreps + 3 fiber-sym + 1 FA + 1 FD = 10.** The channels are **NOT one-per-piece** — they are spectral / group-theoretic projections of the signed-piece-value scalar field over the 8×8 base. Piece identity enters only through the fiber-sym (3 directions of cross-piece SVD), the FA (pawns only), and the FD (per-piece-type DIAG_DEV row).

### 1.2 — chess-4D — 11 channels × 4096 dims = 45 056 total

Source: [`encoder_4d.py:3-14, 115-127`](../../chess-maths/chess-spectral/python/chess_spectral/encoder_4d.py), [`qm_4d.py:38-41`](../../chess-maths/chess-spectral/python/chess_spectral/qm_4d.py).

| Channel | Slice | Semantic role | Group-theoretic anchor |
|---|---|---|---|
| **A1** | 0:4096 | B₄ trivial irrep (`P_A1 @ sig`) | 1-dim B₄ irrep |
| **STD4_X** | 4096:8192 | Centered x-coord residual × signal | std-4D rep, axis 0 |
| **STD4_Y** | 8192:12288 | Centered y-coord residual × signal | std-4D rep, axis 1 |
| **STD4_Z** | 12288:16384 | Centered z-coord residual × signal | std-4D rep, axis 2 |
| **STD4_W** | 16384:20480 | Centered w-coord residual × signal | std-4D rep, axis 3 |
| **FIB_SYM_1/2/3** | 20480:32768 | Symmetric fiber (cross-piece SVD basis, knight/bishop=queen/king, 4D rook drops out) | Cross-piece SVD rank-3 |
| **FA_PAWN_W** | 32768:36864 | Antisymmetric pawn fiber on W-axis (`I⊗I⊗I⊗W_ANTI_DCT`) | Oana-Chiru Def. 11 |
| **FA_PAWN_Y** | 36864:40960 | Antisymmetric pawn fiber on Y-axis (`I⊗Y_ANTI_DCT⊗I⊗I`) | Oana-Chiru Def. 11 |
| **FD_DIAG** | 40960:45056 | Diagonal deviation, rook-shadow, all pieces | Per-piece DIAG_DEV row |

### 1.3 — Reconciliation: why 11 not 10

Two independent splits convert 2D's 10 into 4D's 11:

- **D₄ irreps (2D, 5) → STD4 axis residuals (4D, 4 + 1 = 5).** The 2D code uses 5 character-table-projected channels (A1, A2, B1, B2, E). The 4D code keeps just **one** B₄-orbit projector (A1, the trivial irrep) and replaces the other four with **four axis residual channels** STD4_{X,Y,Z,W}. Net: **5 ↔ 5** (no change in count, but a deep semantic reframing — irrep projection → per-axis residual; consistent with the std-4D rep being 4-dimensional vs D₄'s {A2, B1, B2, E} totaling 4 non-trivial-irrep dimensions).
- **FA pawn (2D, 1) → FA_PAWN axis-split (4D, 2).** The 2D code has one antisymmetric pawn channel. The 4D code splits it into FA_PAWN_W and FA_PAWN_Y per Oana-Chiru Definition 11 (4D pawns are anchored on the Y or W axis, never Z; vendored at [`hoodoos/rinaldi-unciuleanu-chiru-2026.xml`](../hoodoos/rinaldi-unciuleanu-chiru-2026.xml)). Net: **1 → 2** (+1 channel).
- **Fiber-sym (2D, 3) → Fiber-sym (4D, 3).** No change.
- **FD (2D, 1) → FD_DIAG (4D, 1).** No change.

**Tally: 5 + 1 + 3 + 1 = 10 (2D); 5 + 2 + 3 + 1 = 11 (4D).** The +1 channel in 4D is from the pawn-axis split mandated by the chess4D-OC ruleset, NOT from the dimensional bump per se. (One might have naively expected +6 or +8 channels from B₄'s richer irrep structure; the encoder design instead uses the 4D coordinate frame as the natural splitter and keeps only one B₄ orbit projector.)

This is a **load-bearing design choice** — the 4D encoder bypasses B₄'s 20-irrep table in favor of the natural-rep coordinate axes for channels 1-4. A future encoder revision could expand the B₄ irrep coverage (analogue of D₄'s {A2, B1, B2, E}) at the cost of more channels.

---

## 2 — Hyper-wrap for parallel operations: structural check

### 2.1 — H₀ block-diagonal structure

Both [`qm_2d_dynamics.py:159-172, 261-271`](../../chess-maths/chess-spectral/python/chess_spectral/qm_2d_dynamics.py) and [`qm_4d_dynamics.py:2598-2604`](../../chess-maths/chess-spectral/python/chess_spectral/qm_4d_dynamics.py) document: `H_full = I_{N_CHANNELS} ⊗ H₀`. The current code path is already a per-channel loop:

```python
for ch in range(N_CHANNELS):
    out[start:end] = expm_multiply((-1j*t)*H_0, psi[start:end])
```

**Direct measurement (synthetic chess-scale Laplacian):**

| Scale | Off-block coupling nnz | Strictly block-diagonal? | Max block-vs-block diff | Blocks identical? |
|---|---|---|---|---|
| chess-2D (`I_10 ⊗ H_0`) | **0** | **YES** | **0.0** (machine-exact) | **YES** |
| chess-4D (`I_11 ⊗ H_0`) | **0** | **YES** | **0.0** (machine-exact) | **YES** |

The structure is exactly what the code claims. The "hyper-wrap" representation already exists implicitly; the question is whether materializing it (as a single big propagator) or batching the per-channel calls more aggressively gives a speedup.

### 2.2 — Three propagator paths benchmarked

Three implementations, same numerical result (validated):

1. **Per-channel sparse loop** — current code: `N_CHANNELS` separate `expm_multiply` calls, each on a single `(H₀, ψ_block)` pair.
2. **Eigenbasis + einsum batched** — pre-compute `eigh(H₀_dense)` once, then per call apply `V_T @ diag(exp(-iλt)) @ V^H @ ψ` to all `N_CHANNELS` blocks at once via `(N_CHANNELS, n) @ (n, n)` einsum. This is the **literal "hyper-wrap for parallel ops"** interpretation.
3. **Full-dim sparse** — materialize `I_N ⊗ H₀` and call `expm_multiply` once on the `N·n`-dim state. The "naive hyper" form.

| Scale | Per-channel sparse | Eig + einsum batched | Full-dim sparse | Eig speedup vs per-channel | Cross-check max_abs |
|---|---|---|---|---|---|
| **chess-2D (10×64=640)** | 10.4 ms | **0.053 ms** | 1.22 ms | **~196×** | 1.8e-16 (machine-exact) |
| **chess-4D (11×4096=45056)** | 61.3 ms | 722 ms (post-decomp; 124s decomp) | 69.0 ms | **0.085× (SLOWER)** | 1.3e-16 (machine-exact) |

### 2.3 — Math-doesn't-lie verdict

**The hyper-wrap-for-parallel-ops idea is a real 2D-scale win and a real 4D-scale loss.** Honest accounting:

- **chess-2D: 196× speedup is genuine.** Eigenbasis diagonalization of the 64×64 H₀ costs ~0.5 ms one-shot; subsequent per-call cost is 0.053 ms vs 10.4 ms for the current sparse loop. **Recommendation: ship as ADR-002 §6.1 optimization for the 2D side.** Eigendecomp is amortized across move boundaries during M14.x animation; per-frame cost drops by ~196×.
- **chess-4D: 12× slowdown plus prohibitive setup cost.** Eigendecomp of the 4096×4096 dense H₀ costs **124 seconds** one-shot, and per-call eigenbasis-batched is 722 ms (vs 61 ms sparse). Amortization breakeven is **infinite** — the per-call cost is already higher, so no number of subsequent calls recoups the upfront cost. **Recommendation: do NOT pursue eigenbasis optimization for 4D side.** The 4096×4096 dense matmul (V^H @ ψ across 11 channels) is fundamentally slower than `scipy.sparse.linalg.expm_multiply`'s Krylov subspace iteration on the sparse H₀ (32 768 nnz).
- **The full-dim sparse path (interpretation 3) is fastest at 2D scale (1.22 ms vs 10.4 ms per-channel loop) and roughly tied at 4D scale (69 ms vs 61 ms).** This is because `scipy.sparse.linalg.expm_multiply` has per-call overhead that dominates at small `n`; one big call beats 10 small calls. **Anomaly-chase**: the current per-channel loop in `qm_2d_dynamics.evolve_under_h0` is suboptimal at 2D scale by ~8× even without going to eigenbasis. Materializing `I_10 ⊗ H₀` (once, cached) and calling `expm_multiply` once on the full 640-dim state is **strictly better** than the per-channel loop on every metric tested.

### 2.4 — Connection to "hyper" terminology

The user's question proposed a fourth potential sense of "hyper" — channel-parallelization. **Recommendation: do NOT add a fourth sense to the canon.** What we measured is just structured numpy broadcasting (`einsum('cij,cj->ci', ...)` or `psi.reshape(N, n) @ V`), well within the existing **algebraic-hyperdimensional** (§3.5.1) sense — HDC-style batched-vector operations on a fiber-bundle structure. The fiber-bundle operator algebra (§3.5.4) already documents `total = base × fiber` (tensor product) and says explicitly "the graph-Laplacian + eigenphase-torus lift applies to the **base** factor; HDC bind/bundle operations apply to the **fiber** factor". What this spike confirms is that **operators that respect the fiber structure (factor as `I_fiber ⊗ O_base`) admit per-fiber batched evaluation** — this is structural, not new terminology.

### 2.5 — Anomaly chase: the chess-4D `94 ms` from `project-workflow-a2a-quickbench`

The project-workflow-A2A quick-bench measured chess qm_4d_dynamics at **94 ms** per evolve_under_h0 call. Our synthetic measurement is **61 ms** — within 1.5× and consistent with the quick-bench's "within constant factors of the real subsystem" caveat. (The quick-bench used N_TRIALS=10 at the full scale, and the synthetic Laplacian has ~32 768 nnz vs the real 4D H₀ which has the same structure.) This is **convergence** — our measurement validates the prior quick-bench. The bigger anomaly is that **the project-internal 4D dynamics call is already near-optimal**: the per-channel loop and full-dim sparse paths are tied at 4D scale, and eigenbasis would slow it down. There is no further speedup to chase at the 4D scale via channel-parallelization.

---

## 3 — Three concrete recommendations to the conductor

1. **chess-2D dynamics: enable ADR-002 §6.1 eigenbasis-diagonal optimization.** A 196× speedup at zero numerical cost (max_abs deviation 1.8e-16) is a real M14.x animation win at the 2D scale. The 64×64 H₀ eigendecomp is trivial (<1 ms). Implementation is ~10 lines in `qm_2d_dynamics.evolve_under_h0`.
2. **chess-4D dynamics: do NOT pursue eigenbasis optimization.** Honest negative result. Document the breakeven calculation in ADR-002 §6.1 so the deferral has a measured justification (not just "deferred").
3. **chess-2D dynamics: alternative — drop the per-channel sparse loop in favor of pre-cached `I_10 ⊗ H₀`.** 8× speedup with no math change, no eigendecomposition. If the eigenbasis path is judged too invasive, this is the lower-risk floor improvement.

**Channel rationale**: the chess-spectral notebook should gain a §16.1 (or similar) **channel rationale** subsection explaining the 10 vs 11 split. The current `qm_2d.py` and `encoder_4d.py` docstrings document the layouts independently; no shared narrative explains the +1 (it's the pawn-axis split per Oana-Chiru, not the dimensional bump per se).

**§3.5.4 fiber-bundle row update (srmech notebook)**: add a sub-property after the existing operator-orthogonality paragraph: *"Operators of the form `I_fiber ⊗ O_base` (free-particle Hamiltonian H₀, channel-independent observables, group-action lifts U_g) factor naturally as per-fiber batched evaluations. The chess-spectral H₀ is the load-bearing project instance: synthetic measurement at chess-2D scale shows a 196× speedup from per-channel sparse `expm_multiply` to batched eigenbasis-diagonal einsum; at chess-4D scale the dense-eigendecomposition cost is prohibitive (124 s) and the speedup inverts to 12× slowdown."*

---

## Files

- `chess-channels-and-hyper-parallel-2026-05-11.md` — this findings markdown
- `chess-channels-and-hyper-parallel-per-finding-2026-05-11.ndjson` — structural-check + bench records, one per line
- `chess-channels-and-hyper-parallel-script.py` — reproducible benchmark, deterministic seed `20260511`

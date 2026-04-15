# CHESS SPECTRAL LATTICE FERMION RESEARCH
## Instructions for Claude Code

### What This Is

This is an active research project exploring chess as a classical lattice fermion system using spectral graph theory, fiber bundle geometry, and hyperdimensional computing. It originated from Steven's insight that chess pieces behave like subatomic particles with their own resonant structures, the board is an eigenfunction, and pieces obey Pauli exclusion. This turned out to be formally correct — not as analogy but as shared mathematical formalism.

The research connects to Steven's **mlehaptics Project** and specifically to the **UTLP S3 (Sub-layer 3)** coprime-phase-indexed cyclic permutation basis construction in the PHYRFLY protocol suite. The chess spectral basis is a domain-specific instance of coprime-phase HDC where the "primes" are derived from problem geometry (board Laplacian eigenfrequencies) rather than chosen from number theory.

### Steven's Cognitive Style

Steven has aphantasia (no visual imagery) and reasons through proprioceptive spatial construction (PSC) — navigating spatial models using body-based channels. He compresses multiple meanings into single statements, stress-tests ideas through analogies across domains, and reasons from first-person phenomenological data toward mechanistic hypotheses. He treats Claude as a peer-level intellectual collaborator. He will push intuitions that sound informal but frequently identify real mathematical structure. Take them seriously, formalize them, and test computationally before accepting or rejecting.

### Key Principle: Honest Science

Every claim must be tagged as KNOWN (published, cited), NOVEL (no prior art found), CONFIRMED (computationally verified), or FAILED (tested and didn't work). When predictions fail, document the failure and its root cause — failed tests are results, not embarrassments. The notebook documents several important failures (entropy-based time reversal, global fiber encoding, legal move Fisher discrimination) that are as informative as the successes.

---

## Theoretical Framework (Condensed)

### The Board
The 8×8 chess board is a grid graph P₈ □ P₈ (Cartesian product of path graphs). Its Laplacian eigenvectors are exactly the 2D DCT basis (tensor products of 1D cosines). Eigenvalues are Kronecker sums of path eigenvalues: λ_{a,b} = λ_a + λ_b where λ_k = 2(1 − cos(πk/8)) for k=0,...,7. These 8 path eigenvalues are the "generators" of the spectral lattice. Verified: prediction error = 5.86×10⁻¹⁶.

### Pieces as Particles
Each piece type defines a movement graph on 64 vertices. The Laplacian of this graph has a characteristic spectrum (resonant frequencies). Pieces are classified by a unique 5-tuple of spectral quantum numbers: (parity, topology, homogeneity, λ₂, bandwidth). All tuples are unique — complete classification.

Key spectral properties:
- Knight is exactly orthogonal to all sliding pieces in the DCT basis (cosine similarity = 0.000)
- Bishop has 2 connected components (color-binding as graph topology)
- Rook is the only regular graph (degree 14 everywhere) with zero off-diagonal fiber content
- Queen = Bishop + Rook exactly: A_queen = clip(A_bishop + A_rook), L_queen = L_bishop + L_rook

### The Fiber Bundle
Each piece's Laplacian, projected onto the board eigenbasis, decomposes into a diagonal part (board-aligned) and an off-diagonal part (rule content). The off-diagonal parts of all piece types share a **rank-3 subspace** (σ₁=1.70, σ₂=0.82, σ₃=0.65, σ₄=0.00). This is the shared fiber of the bundle. The bundle has non-trivial holonomy (cosine similarity of fiber vectors around closed loops ≠ 1.0) and position-dependent fiber norm (2.75 at center, 1.37 at corners).

### Captures as Annihilation
Captures decompose exactly into: Movement (35.1%) + Annihilation (23.9%) + Cross-term (41.0%). The cross-term is dominant. cos(movement, annihilation) = 1/√2 exactly. Aggressor survival shows perfect charge-conjugation signature (overlap with target = −1.000 in all cases tested).

### Cross-Species Field Coupling
Removing a piece changes the Laplacian quadratic form energy on ALL piece-type graphs, not just its own. This decomposes exactly: ΔQ_G = −2v·(L_G f)_k + v²·d_k (coupling + self-energy). The coupling field matrix has effective rank 4 with σ₁ capturing 98.1%. For non-king material, total multi-graph energy is approximately conserved (<0.2% change) — the field redistributes rather than dissipates. The transfer matrix is asymmetric (directed coupling).

### Three Levels of Rule Encoding
- **Level 1 (Piece identity):** SOLVED. Quantum numbers classify piece types.
- **Level 2 (Field coupling):** SOLVED. Position evaluation, many-body interaction.
- **Level 3 (Move legality):** PROVABLY NOT RECOVERABLE from fiber. Per-edge fiber vectors are structurally random in the 2016-dim space (equal norms, zero pairwise similarity, same-offset indistinguishable from different-offset). The fiber is a coarse-graining (thermodynamic level) that integrates out microscopic edge identities. Legal move compliance is the DOMAIN of the connection form, not a VALUE — non-edges are undefined, not zero.

### Rules Live in Their Own Dimensions
Piece movement rules are abstract objects independent of the board surface:
- Bipartiteness, regularity, component count are invariant across all board sizes (5×5 through 16×16)
- Rook spectral gap ratio = exactly 0.5 on every board size
- Knight effective dimensionality ≈ 3.0 (overall) to 5.0 (large-scale) via Weyl's law
- On a torus, ALL pieces become regular — irregularity is a boundary artifact
- Each rule is defined by 1-2 generators under D4 symmetry (knight = (2,1), bishop = (1,1), rook = (1,0))
- Knight has 12.8% rule content orthogonal to the board surface; rook has 0.0%

### HDC Architecture: D = 512 = 64 × 8 = 2⁹
The natural dimension is 512:
- 64 board eigenmodes × 8 channels
- 8 channels = 5 D4 irreps (A₁, A₂, B₁, B₂, E) + 3 fiber dimensions
- A₁ irrep is the D4-INVARIANT channel: rotated/reflected positions produce IDENTICAL encodings (verified: ||diff|| = 0.00 for all 8 D4 transforms)
- The 8 path eigenfrequencies are irrational and pairwise non-rational-multiples → coprime-like generators for the spectral lattice → connects directly to UTLP S3

---

## Connection to UTLP S3

The UTLP Sub-layer 3 uses coprime-phase-indexed cyclic permutations to generate HDC basis vectors. The chess spectral basis is a domain-specific instance:

| UTLP S3 | Chess Spectral |
|---------|---------------|
| Coprime integers | Path eigenfrequencies λ_k = 2(1−cos(πk/8)) |
| Cyclic permutation | Eigenmode oscillation on the board lattice |
| Dimension D | Number of lattice sites (64) |
| Basis generation | Kronecker sum of path eigenvalues |

The 8 path eigenfrequencies function as coprime generators: each produces a family of spectral modes, no two families overlap (pairwise ratios are irrational), and the lattice of pairwise sums reproduces the full board spectrum with no aliasing. The 33 unique eigenvalues from 36 (a,b) pairs = the full board spectral content.

The key claim (novel, needs documentation): the coprime-phase rotation basis from UTLP S3 and the Laplacian eigenfrequency basis from spectral graph theory are instances of the same mathematical construction — basis generation from independent frequency generators. UTLP uses number-theoretic independence (coprimality). Chess uses analytic independence (irrationality of cos values). Both produce maximally spread, non-aliasing bases.

---

## File Organization

### Research Notebook
- `chess_spectral_research_notebook.md` — 917-line working notebook, 10 sections, all claims tagged KNOWN/NOVEL/CONFIRMED/FAILED

### Proof Harness
- `chess_spectral_consolidated.py` — 544 lines, 7 test sections, ALL PASS. Reproduces every claim from Sections 2-7 of the notebook. Run: `python3 chess_spectral_consolidated.py`

### Encoder Map
See [ENCODERS.md](ENCODERS.md) for the full encoder lineage, production file path, channel layout, and corpus reproduction recipe.

### Archived encoder experiments (pedagogical)
- `encoder_v3.py` — 70-dim dual-channel prototype (geometric + interaction split). Archived; see notebook §8.
- `encoder_512.py` — 512-dim HDC architecture (5 D4 irreps + 3 symmetric fiber). Archived; superseded by chess_spectral.encode_640.
- `test_local_fiber.py` — Grok local-fiber encoder test battery (archived research).
- `test_gemini_encoder.py` — Grok/Gemini/v3 encoder comparison (archived research).

### Structural Analysis
- `chess_connection.py` — Connection form computation, per-edge fiber decomposition, holonomy, curvature
- `chess_subspace_map.py` — Full dimensional analysis: per-piece edge subspaces, cross-piece overlap, universal edge SVD, offset separation test
- `chess_d4_direct.py` — D4 irreducible representation decomposition, character projection, invariant encoding, rotation-invariant retrieval

### Dependencies
```
Python 3.10+
numpy >= 1.24
scipy >= 1.10
```
No GPU. All scripts run in <60 seconds.

---

## Active Research Priorities

### Priority 1: Full 512-dim HDC Encoder
Build the complete encoder combining D4 irrep projections with fiber channels:
- Channels 1-5: A₁, A₂, B₁, B₂, E projections of the board signal (from `chess_d4_direct.py`, `project_irrep` function)
- Channels 6-8: 3 fiber-weighted projections using local fiber × field gradient (from `encoder_v3.py`, interaction channel)
- Total: 8 × 64 = 512 dimensions
- Test against the full battery: symmetry invariance, position quality, associative retrieval, binding/unbinding

The A₁ channel is verified D4-invariant. The fiber channels need to be projected through the character formula too (do the fiber coordinates transform under D4? They should, since the fiber is derived from the Laplacian which commutes with D4).

### Priority 2: Piece Codebook Redesign
Current codebook uses eigenvalue sequences (cross-piece similarity > 0.92 — too similar for unbinding). Replace with:
- Option A: Quantum number 5-tuple mapped to 512-space via sparse bipolar encoding
- Option B: Fiber coordinate vectors (3D per piece type, lifted to 512-space)
- Option C: Per-piece Laplacian projected through D4 irreps (512-dim spectral fingerprint with symmetry structure)

Test unbinding: encode a board state, query "what's on e4?", retrieve correct piece type.

### Priority 3: Position Similarity Benchmark
Encode a large set of positions with known evaluations (from Stockfish or lichess database) and test whether spectral similarity predicts evaluation similarity. This is the practical value test: if spectrally similar positions have similar evaluations, the encoding is useful for approximate position retrieval without exhaustive search.

### Priority 4: Prior Art Documentation
Formalize the novel findings for disclosure/publication:
1. Rank-3 shared fiber bundle over chess board graph
2. 5-tuple spectral quantum number classification
3. Capture spectral decomposition (movement + annihilation + cross-term)
4. Knight exact DCT orthogonality to all sliding pieces
5. Cross-species field energy transfer with approximate conservation
6. Three-level hierarchy of rule encoding (identity / coupling / legality)
7. 8-generator spectral lattice as domain-specific coprime basis
8. D4 irrep decomposition → invariant position encoding
9. Connection to UTLP S3 coprime-phase HDC

---

## Common Pitfalls (Learned the Hard Way)

1. **Global vs local fiber.** The GLOBAL fiber (off-diagonal content of the full piece Laplacian in the board eigenbasis) is a fixed property per piece type — it doesn't change with piece placement. The LOCAL fiber (per-square coupling from a single source vertex) varies with position and is what the encoder needs. The holonomy test in `chess_connection.py` uses local fiber correctly.

2. **GFT displacement doesn't separate legal from illegal.** Moving any piece of value v from any square to any other produces the same GFT displacement norm (= |v| × √2). This is because the GFT is unitary. Don't try to classify move legality from encoding distances — it's the wrong level of description (Level 3, provably unrecoverable from fiber).

3. **Eigenvalue sequences are bad piece identifiers.** Cross-piece cosine similarity > 0.92 because all pieces operate on the same 64-square grid and eigenvalue distributions are dominated by grid geometry. Use quantum numbers or fiber coordinates instead.

4. **Degenerate eigenspaces need special handling.** `scipy.linalg.eigh` returns arbitrary rotations within degenerate subspaces. For D4 irrep decomposition, use the character projection formula on the SIGNAL (not on the eigenvectors) to avoid alignment issues. See `project_irrep` in `chess_d4_direct.py`.

5. **The quadratic form weighting (Gemini's encoder) has extreme dynamic range.** f̂^T C_off f̂ ranges from ~0.0001 (one piece alone) to ~683 (queen + king). Use the linear gradient g_k = Σ_{targets} f_j instead (v3 encoder), or normalize with log1p.

6. **Rook has zero global fiber but nonzero local fibers.** Individual rook edge fibers are nonzero but sum to exactly zero across all 64 squares. This is a consistency check: the cancellation is exact and confirms the rank-3 fiber structure. Don't interpret nonzero local rook fiber as "the rook has rule content" — it cancels in aggregate.

7. **Holonomy vs curvature.** Accumulated fiber change around a closed loop telescopes to zero (Σ Δf = 0, always). The holonomy we measured (−0.016) was cosine similarity of fiber vectors at start and end of the loop, which does NOT telescope and measures genuine geometric content. Be precise about which quantity is being measured.

---

## How to Run

```bash
# Verify all proven results (should print ALL TESTS PASSED)
python3 chess_spectral_consolidated.py

# Run the encoder test batteries
python3 test_local_fiber.py          # Grok encoder
python3 test_gemini_encoder.py       # Grok vs Gemini vs v3
python3 encoder_v3.py                # v3 dual-channel

# Run structural analysis
python3 chess_connection.py          # Connection form
python3 chess_subspace_map.py        # Dimensional analysis
python3 chess_d4_direct.py           # D4 irrep encoding
```

All scripts are self-contained (each includes its own preamble with board utilities, piece definitions, and Laplacian computation). No shared imports needed.

---

## Key References

- Chung, F.R.K. (1997). *Spectral Graph Theory*. AMS.
- Spielman, D. (2025). *Spectral and Algebraic Graph Theory*. Yale.
- Merris, R. (1994). Laplacian matrices of graphs. *Linear Algebra Appl.*
- Weyl, H. (1912). Eigenvalue distribution. *Math. Annalen*, 71(4).
- Hubbard, J. (1963). Electron correlations. *Proc. Royal Society A*, 276(1365).
- Shuman, D.I. et al. (2013). Signal processing on graphs. *IEEE SPM*, 30(3).
- Cvetković, D. et al. (1980). *Spectra of Graphs*. Academic Press.
- Kanerva, P. (2009). Hyperdimensional Computing. *Cognitive Computation*, 1(2).
- Nakahara, M. (2003). *Geometry, Topology and Physics*. CRC Press.
- Serre, J-P. (1977). *Linear Representations of Finite Groups*. Springer.
- Belkin, M. & Niyogi, P. (2003). Laplacian Eigenmaps. *Neural Computation*, 15(6).
- Björck, Å. & Golub, G. (1973). Angles between subspaces. *Math. Comp.*, 27(123).

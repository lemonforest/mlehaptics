# Spectral Identity Verification (Pre-Flight #3 for `chess_spectral.qm_4d`)

**Date:** 2026-04-29
**Run:** `python research/spectral_identity_4d_verification.py` (FULL_4D and FULL_4D_ALL)
**Verdict:** **HOLDS** at machine precision, with one important wording correction.

---

## Wording correction (Z_8 vs P_8)

The original statement of the claim mentions the "Z_8^4 graph Laplacian." The
encoder's actual graph is **P_8 [box] P_8 [box] P_8 [box] P_8** (Cartesian
product of four open 8-vertex paths), **not** the 8-cycle Cayley graph of Z_8.
This is an important factual point because:

* The 8-cycle Z_8 has _4 distinct_ eigenvalues with high multiplicity from the
  abelian Pontryagin dual; the encoder eigenbasis would be Fourier modes
  (DFT-II), and B_4 acts only by axis permutations + cyclic shift sign-flips.
* The path P_8 has _8 distinct_ eigenvalues, eigenbasis is DCT-II, and B_4
  acts as signed permutations through the symmetric reflection s -> 7-s on
  flipped axes (this is exactly what `tables_4d.b4_permutation_matrix` does).

So the **strictly correct claim** for the encoder is:

> The 4096 eigenmodes used by `chess_spectral.encoder_4d` are the simultaneous
> eigenbasis of (a) the **P_8^4 Cartesian-product** graph Laplacian Delta and
> (b) the centralizer of the B_4 (signed-permutation) representation.

The script tests this exact statement.

## Numerical evidence

### 2D pilot (P_8^2 = 64-dim, B_2 group order 8)

* 33 distinct eigenvalues, multiplicities {1: 9, 2: 23, 7: 1}.
* Every Delta-eigenspace is B_2-stable: max `||[pi(g), P_lambda]||_inf = 3.5e-15`.
* Encoder columns are exact L-eigenvectors: `max ||L v - lambda v|| = 1.1e-15`.

### Full 4D (P_8^4 = 4096-dim, B_4 group order 384)

* `Delta` build (sparse Kronecker sum): 0.81s.
* Diagonalize (`np.linalg.eigh`, dense): 48.1s.
* **225 distinct eigenvalues**, total dim = 4096 (matches by trace).
* Maximum multiplicity = 127 at lambda = 8.0 (the spectral midpoint, as
  expected from convolution-of-eight P_8 spectra).
* P_8 1D spectrum: `[0, 0.15224, 0.58579, 1.23463, 2.0, 2.76537, 3.41421,
  3.84776]` (the standard `2 - 2 cos((k+0.5) pi / 8)` is **not** what P_8
  gives; this is the open-boundary `2 sin^2(k pi / 16)` spectrum that
  `tables_4d.eig_p8` returns).
* Multiplicity histogram (via `kron_sum4_eigvals` cross-check, identical to
  the diagonalization output):

```
  mult     1:    7 eigenvalues   ( 7  vectors, fully axis-symmetric corners)
  mult     4:   43 eigenvalues   (172 vectors)
  mult     6:   18 eigenvalues   (108 vectors)
  mult    12:   96 eigenvalues   (1152 vectors  - dominant interior class)
  mult    24:   28 eigenvalues   (672 vectors)
  mult    34:    6 eigenvalues   (204 vectors)
  mult    42:    1 eigenvalue    ( 42 vectors)
  mult    60:   12 eigenvalues   (720 vectors)
  mult    64:    6 eigenvalues   (384 vectors)
  mult    72:    6 eigenvalues   (432 vectors)
  mult    76:    1 eigenvalue    ( 76 vectors)
  mult   127:    1 eigenvalue    (127 vectors  - lambda = 8.0 spectral midpoint)
                                  -----
                                  4096
```

#### Bottom-line metrics

| Quantity | Value |
| --- | --- |
| `eigenvalue_match_4d` (encoder lambdas == Delta lambdas, with mults) | **True** |
| `encoder_basis_residual_4d` (max ||L v - lambda v||) | `3.3e-16` |
| `all_stable_4d` (all 225 eigenspaces B_4-stable) | **True** |
| `max_commutator_err_4d` (max ||[pi(g), P_lambda]||) | `1.6e-13` |
| `encoder_alignment_residual_4d` (max ||(I - P_lambda) v_enc||) | `6.2e-14` |

All four diagnostics are at floating-point noise. The claim holds at
1e-13 tolerance everywhere, ~3 orders of magnitude better than the 1e-10
target the project uses for C-Python parity.

### Isotypic spot-check (B_4 trivial-irrep multiplicity)

Burnside-style character projection on the lowest-10 eigenspaces:

```
lam=-0.00000  dim=  1   trivial-irrep mult ~ 1
lam= 0.15224  dim=  4   trivial-irrep mult ~ 0
lam= 0.30448  dim=  6   trivial-irrep mult ~ 0
lam= 0.45672  dim=  4   trivial-irrep mult ~ 0
lam= 0.58579  dim=  4   trivial-irrep mult ~ 1
lam= 0.60896  dim=  1   trivial-irrep mult ~ 0
lam= 0.73803  dim= 12   trivial-irrep mult ~ 0
lam= 0.89027  dim= 12   trivial-irrep mult ~ 0
lam= 1.04251  dim=  4   trivial-irrep mult ~ 0
lam= 1.17157  dim=  6   trivial-irrep mult ~ 1
```

`lambda = 0` (constant), `lambda = 0.58579` (totally symmetric tensor of the
first non-zero P_8 mode on each of 4 axes) and `lambda = 1.17157` are the
first three eigenspaces with a B_4-invariant component. The dim-1 eigenspace
at `lambda = 0.60896` (the "antisymmetric" eigenvalue `lambda_3 + lambda_3 +
lambda_3 + lambda_3` minus exchange) carries no trivial irrep — consistent
with the encoder's A_1 channel being non-zero only when the signal projects
onto these B_4-invariant subspaces.

## Interpretation

The encoder's tensor-DCT basis `e_i (x) e_j (x) e_k (x) e_l` is _canonical_:
it diagonalizes `Delta` (Kronecker-sum eigenvalues) **and** every P_lambda
commutes with every `pi(g)` (B_4-action). The choice of basis _within_ each
multidimensional eigenspace is therefore not arbitrary engineering — it is
determined by the simultaneous spectral decomposition of the operator
algebra `< Delta, pi(B_4) >`. Whatever further refinement we make on a
specific eigenspace (e.g., breaking it into B_4-irrep components for the
QM extension's "energy basis" / "angular-momentum basis" analogy) is a
sub-decomposition _within_ a B_4-stable subspace, not a re-choice of basis.

The encoder basis is therefore representation-theoretically clean:

* **Delta-eigenvalue** = "energy quantum number" (kinetic level).
* **B_4-irrep label** within each E_lambda = "angular-momentum-like quantum
  number" (point-group sector).
* **(i, j, k, l) tuple** = a specific simultaneous-eigenvector of Delta and
  of the four commuting axis-position operators (which together form a
  maximal abelian subalgebra in the B_4 commutant once we restrict to
  the abelian (Z_2)^4 subgroup of B_4).

This is exactly the "complete set of commuting observables" picture that
QM uses for any single-particle problem with a discrete symmetry group —
the encoder happens to be exactly that, in disguise.

## Recommendation

**Ship "experiment 1" of the QM module as the spectral-identity statement.**
The result is:

* Numerically airtight (4 independent diagnostics all at 1e-13 or better).
* Conceptually clean (representation theory + graph Laplacian; no chess
  semantics needed for the proof).
* Already proven via existing `tables_4d` primitives — the QM module just
  needs to expose the eigendecomposition, the per-eigenspace projector
  `P_lambda`, and the irrep-projection convenience function (which can be
  added incrementally and is independently testable).

Do **not** fall back to the bishop-wavefunction experiment as the lead
result. That experiment is good and complementary, but it relies on a
specific piece-Laplacian commutation property which the rook violates
(see `diag_dev_4d` discussion in `tables_4d.py:894`). The spectral
identity is _piece-agnostic_ and therefore the cleaner foundation.

### What "experiment 1" should contain

1. The 225-eigenvalue spectrum table (one figure / one CSV).
2. Per-eigenspace B_4-stability ledger (already produced by this script).
3. A worked example of "complete set of commuting observables":
   pick `lambda = 0.58579` (dim 4), show how the four basis vectors are
   exactly the four 1D eigenvectors permuted by S_4 on the axis index,
   so they are simultaneous eigenvectors of Delta and the four
   axis-direction projectors.
4. The trivial-irrep multiplicity table for at least the bottom 50
   eigenspaces (should sum to the total number of B_4-orbits on Z_8^4 =
   trace(P_A1), which `tables_4d.b4_a1_orbit_projector` already computes).
5. A short remark that this generalizes the "lattice momentum + crystal
   point group" decomposition standard in solid-state physics
   (Bouckaert-Smoluchowski-Wigner 1936; the usual reference for the
   diamond-cubic group but the construction is identical here).

### Single caveat to flag in the QM module docs

**The graph is P_8, not C_8.** A reader expecting a translation-invariant
plane-wave basis (C_8 / Pontryagin / Bloch) will be surprised. P_8 has
sine-cosine Dirichlet/Neumann modes, not exponentials, and the symmetry
group is the dihedral D_2 (not Z_8). In 4D this means B_4 acts by signed
permutations of the centered coords, and reflections through the box
center, not by translations.

If a future "infinite-board" or "torus chess" extension changes to C_8,
the entire spectral picture changes (eigenvalues degenerate to 4 distinct
values, B_4 grows to W(B_4) ⋊ (Z_8)^4, etc.). The spectral identity in
its present form is specific to the open-boundary 4D chess board.

## Files added

* `python/research/spectral_identity_4d_verification.py` (verification script)
* `python/research/spectral_identity_4d_findings.md` (this note)

No shipped source files were modified.

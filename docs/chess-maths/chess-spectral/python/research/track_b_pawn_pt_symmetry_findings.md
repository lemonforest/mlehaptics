# ADR-005 Pawn Pseudo-Hermitian PT-Symmetry Probe — Findings

**Verdict: PARTIAL**

## Summary (Primary Variant — full operator: double-push + captures)

M_pawn_w_white nnz: 10,368; asymmetric entries: 20,736 (non-zero confirms the pawn operator is non-Hermitian as expected).

Duality check P_w * M_white * P_w == M_black: residual 0.000e+00
M_white^T == M_black residual: 3.200e+01

## Pseudo-Hermiticity Residuals Across All Variants

### Variant: double_push=True, captures=True

| eta candidate | residual | passes (<1e-10) |
|---|---|---|
| P_w | 3.200000e+01 | no |
| P_y | 1.440000e+02 | no |
| J_op | 3.200000e+01 | no |
| I | 1.440000e+02 | no |

  Spectrum: max |Im(lambda)| = 0.000e+00; range [0.000e+00, 0.000e+00]. Real within 1e-10: YES
  Duality P_w M_white P_w = M_black residual: 0.000e+00
  M_white^T = M_black residual: 3.200e+01

### Variant: double_push=False, captures=True

| eta candidate | residual | passes (<1e-10) |
|---|---|---|
| P_w | 0.000000e+00 | YES |
| P_y | 1.403994e+02 | no |
| J_op | 0.000000e+00 | YES |
| I | 1.403994e+02 | no |

  Spectrum: max |Im(lambda)| = 0.000e+00; range [0.000e+00, 0.000e+00]. Real within 1e-10: YES
  Duality P_w M_white P_w = M_black residual: 0.000e+00
  M_white^T = M_black residual: 0.000e+00

### Variant: double_push=False, captures=False

| eta candidate | residual | passes (<1e-10) |
|---|---|---|
| P_w | 0.000000e+00 | YES |
| P_y | 8.466404e+01 | no |
| J_op | 0.000000e+00 | YES |
| I | 8.466404e+01 | no |

  Spectrum: max |Im(lambda)| = 0.000e+00; range [0.000e+00, 0.000e+00]. Real within 1e-10: YES
  Duality P_w M_white P_w = M_black residual: 0.000e+00
  M_white^T = M_black residual: 0.000e+00

**Best overall:** variant `double_push=False, captures=True` with eta = `P_w` (residual 0.000e+00).

## Recommendation for ADR-005

**PARTIAL — REVISE eta DERIVATION.** 
Spectrum is real (max |Im(lambda)| = 0.000e+00, well below 1e-10), so a similarity transform to a Hermitian matrix exists (M is similar to a real matrix). However, eta = P_w fails the strict pseudo-Hermiticity condition M^T = eta M eta^-1 with residual 3.200e+01.

Root cause: the actual M_pawn_w_white satisfies `P_w M_white P_w = M_black` (verified to 0e+00 residual) but `M_white^T != M_black` because of the starting-rank double-push asymmetry (white pushes 2 squares from rank 1; black pushes 2 from rank 6; transpose reverses these but the as-built operator does not). ADR-005 §3.3.1's claim `M_pawn_w_white^T = M_pawn_w_black` holds ONLY in the no-double-push idealization.

**Empirically: in the no-double-push variant, eta = P_w DOES satisfy strict pseudo-Hermiticity** (residual 0.000e+00). This validates the underlying ADR-005 derivation modulo the double-push asymmetry.

**Recommended revision to ADR-005:**

1. Acknowledge in §3.3.1 that the as-shipped P_pawn4_white includes double-push and is *not* strictly pseudo-Hermitian under eta = P_w.
2. Decompose M_pawn_w_white = M_single_push + M_double_push, and apply the η-metric only to M_single_push (which IS P_w-pseudo-Hermitian).
3. Treat double-push as a separate, non-pseudo-Hermitian rank-deficient operator (it is non-iterable: a pawn that double-pushed cannot double-push again from the new rank, so the structure is rank-1 per pawn position).
4. The spectrum is fully real because M is nilpotent (all eigenvalues = 0); pawn pushes are non-iterable on a finite board. ADR-005's PT-realness gate is trivially satisfied.

**Spectrum is fully zero (nilpotent operator):** max |lambda| = 0.000e+00. This is expected — pawn pushes are non-reversible and the matrix iterated 8 times produces zero (8-rank board limit). The ADR-005 'real spectrum' acceptance criterion is trivially passed; the more interesting question is whether the operator is diagonalizable (it is NOT — Jordan blocks of size > 1).
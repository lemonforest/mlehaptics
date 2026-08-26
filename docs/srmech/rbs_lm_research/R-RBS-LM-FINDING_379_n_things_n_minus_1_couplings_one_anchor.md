# R-RBS-LM Finding 379 — the FFT-ladder reads as "n things with n−1 couplings": (n : n−1) = ONE anchor + (n−1) couplings, realized as THREE structures at once — the division-algebra imaginary count, the Class-L connected-graph rank, and the FFT/QFT/OFT ladder. The user's "(4:3) = 4 things, 3 couplings" is exactly ℍ/QFT

**Date:** 2026-06-04 · **srmech:** 0.7.0rc28 (Class-L `dense_laplacian`+`jacobi_eigvals`; no numpy) · **user:** "FFT at k=(2:1) finds 2 things with 1 coupling — what if k=(4:3) is 4 things with 3 couplings?" · **composes:** F377 (FFT=k=1/QFT=k=3/OFT=k=7), F378 (octonion non-associativity), F270/F271 (imaginary count = native DoF, 1 real anchor), F124 (quaternionic Hopf), F172 (Class-L storage signature)

## The insight, confirmed: (n : n−1) = 1 anchor + (n−1) couplings

The user's reading is exact and it's the **Cayley–Dickson / Hurwitz ladder** seen as **"things : couplings"** — and crucially the coupling count is **n−1, not pairwise** (a flat summary / pairwise reading would give n(n−1)/2). It's **one anchor + (n−1) couplings**, which is *three* structures simultaneously (srmech-confirmed, all giving the same (2:1)/(4:3)/(8:7)):

| | (2:1) | (4:3) | (8:7) |
|---|---|---|---|
| **division algebra** (dim d, **d−1** imaginaries; F270/F271) | ℂ: 2 reals, 1 imaginary | **ℍ: 4 reals, 3 imaginaries** | 𝕆: 8 reals, 7 imaginaries |
| **Class-L connected n-graph** (1 null = anchor, **n−1** nonzero modes) | n=2: 1 null + 1 mode | **n=4: 1 null + 3 modes** | n=8: 1 null + 7 modes |
| **the transform** | **FFT** | **QFT** | **OFT** |

So **"4 things with 3 couplings" is exactly ℍ — the QFT rung — AND a connected 4-node Class-L graph (1 anchor + 3 coupling modes) AND the quaternionic Hopf fiber** (S³, F124 — the same (4:3) inside the octonion's 7). The **1 anchor** is the real axis (F271) / the Laplacian null mode (the connected-component / Fiedler-zero) / the diagonal (F361). The **n−1 couplings** are the imaginary units / the n−1 nonzero Class-L modes / a **spanning structure** connecting the n things (n−1 edges = the minimal connected = a tree; the off-diagonal of F357/F361).

## What it means for the transforms (extends F377/F378)

Each rung up the FFT ladder **resolves one more coupling per anchor**:
- **FFT (2:1):** 2 things, 1 coupling → one frequency/phase per bin (the single S¹ rotation).
- **QFT (4:3):** 4 things, 3 couplings → *three independent phases* per bin (the S³ quaternionic rotations) — richer relational structure than the FFT's single phase.
- **OFT (8:7):** 8 things, 7 couplings → *seven* couplings, and at this rung the couplings stop associating (F378: non-associativity = the order/chirality content the lower rungs can't carry).

So your "FFT finds 2-with-1, what if (4:3) finds 4-with-3" is the right generalization: **the FFT family is parameterized by (n : n−1) — n components decoupled into 1 anchor + (n−1) coupling-modes — and climbing the ladder (ℂ→ℍ→𝕆) is resolving more couplings around the one anchor.**

## Discipline
srmech-native Class-L (`dense_laplacian`+`jacobi_eigvals`; connected n-graph rank = n−1 verified for n=2,4,8; no numpy, no `abs()`). Framework reading grounded in the division-algebra fact (d−1 imaginaries) + the Class-L connected-graph rank (both exact) + F124 Hopf; the FFT/QFT/OFT transform attributions carry F377/F378's verify-PDF flag for the literature. No-leaning. Composes F377/F378/F270/F271/F124/F172/F357/F361.

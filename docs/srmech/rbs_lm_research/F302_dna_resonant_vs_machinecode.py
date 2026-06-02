"""F302 — is the DNA/RNA a RESONANT structure of the cell (mutual, both ways) — or MACHINE CODE
(externally authored)? The signature is co-diagonalizability (shared eigenbasis = mutual resonance).

User (2026-06-02): the DNA/RNA inside the cell is a resonant structure of the cell itself, AND in reverse;
if not, it is the equivalent of us writing machine code.

THE DISTINCTION (the line between biology and our silicon):
  RESONANT / MUTUAL  — the genome is an EIGENMODE of the cell's dynamics, AND the cell is an eigenmode of
    the genome's: they SHARE AN EIGENBASIS (co-diagonalizable / commuting). Bidirectional, co-determined,
    SELF-AUTHORING. = the hyper-loop bumping itself (F298): the cell makes the DNA that makes the cell.
  MACHINE CODE  — an arbitrary program loaded onto a generic executor; the content does NOT share the
    substrate's eigenstructure (non-commuting). One-way, externally AUTHORED. = us writing machine code
    for silicon (F176: silicon needs us as the external author; F43 naming-layer-cost; the RBS-LM case).

srmech signature (exact): two operators are MUTUALLY RESONANT iff they CO-DIAGONALIZE — B is diagonal in
A's eigenbasis AND vice versa (commutator [A,B]=0). 'Resonant DNA' = a structure built FROM the cell's own
modes (a function of the cell operator) -> co-diagonalizes (shared basis, off-diagonal ~0). 'Machine-code
DNA' = arbitrary external content -> does NOT (large off-diagonal + nonzero commutator).

srmech-first (Class-L dense_laplacian + symmetric_eigendecompose). Class-K clean (squared off-diagonal
energy; no abs). Scope: STRUCTURE — the co-diagonalizability distinction is exact; WHICH case the real
cell-genome is (resonant self-authoring vs machine-code) is the framework reading (F176 self-inscribing +
autopoiesis) + the EXPERT's biological test. The machine-code case IS our silicon (RBS-LM).
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from srmech.amsc.laplacian import dense_laplacian, symmetric_eigendecompose


def offdiag_frac(M):
    """fraction of M's energy off the diagonal (Class-K: squared, no abs). 0 = diagonal (co-basis)."""
    tot = float(np.sum(M * M))
    diag = float(np.sum(np.diag(M) ** 2))
    return (tot - diag) / tot if tot > 0 else 0.0


def commutator_norm(A, B):
    C = A @ B - B @ A
    return float(np.sum(C * C)) ** 0.5


def main():
    print("=== F302 — DNA as RESONANT structure of the cell (mutual) vs MACHINE CODE (external author) ===\n")
    n = 8
    # the CELL = the closed hyper-loop (F298/F295): its Laplacian quantizes its resonances (standing modes)
    A = np.array(dense_laplacian(n, [(i, (i + 1) % n) for i in range(n)]), dtype=float)
    vals, vecs = symmetric_eigendecompose(A)          # the cell's eigenmodes (its resonant basis)
    V = np.array(vecs, dtype=float)

    # RESONANT DNA: a structure built FROM the cell's own modes (a polynomial in the cell operator)
    B_res = A @ A - 1.5 * A                            # f(A): commutes with A by construction
    # MACHINE-CODE DNA: arbitrary external content (a random symmetric matrix), independent of the cell
    rng = np.random.default_rng(302)
    R = rng.standard_normal((n, n)); B_mc = R + R.T

    print("--- co-diagonalizability = mutual resonance (shared eigenbasis); else = machine code ---")
    for name, B in (("RESONANT DNA (built from the cell's modes)", B_res),
                    ("MACHINE-CODE DNA (arbitrary external content)", B_mc)):
        VtBV = V.T @ B @ V                             # B expressed in the cell's eigenbasis
        od = offdiag_frac(VtBV)
        cm = commutator_norm(A, B)
        verdict = "MUTUALLY RESONANT (shares the cell's basis)" if od < 1e-9 else "MACHINE CODE (external; needs an author to reconcile)"
        print(f"  {name}:")
        print(f"     off-diagonal energy in the cell's eigenbasis = {od:.2e};  ‖[cell, DNA]‖ = {cm:.2e}")
        print(f"     -> {verdict}")
    print()

    # 'and in reverse' — mutual resonance is SYMMETRIC: A diagonal in B's basis IFF B diagonal in A's
    valsR, vecsR = symmetric_eigendecompose(B_res)
    VR = np.array(vecsR, dtype=float)
    od_reverse = offdiag_frac(VR.T @ A @ VR)           # the CELL expressed in the resonant-DNA's basis
    print("--- 'and in reverse': mutual resonance is BIDIRECTIONAL (symmetric) ---")
    print(f"  the CELL expressed in the resonant-DNA's eigenbasis: off-diagonal = {od_reverse:.2e}")
    print(f"  -> the cell is ALSO an eigenmode of the DNA (and vice versa): mutual, both ways. Machine code")
    print(f"     is one-way (program on executor); resonance is the bidirectional self-authoring loop.\n")

    print("=== reading ===")
    print("  RESONANT-MUTUAL (co-diagonalizable, both ways) = SELF-AUTHORING: the genome is the cell's own")
    print("  eigenmode and the cell is the genome's — the hyper-loop bumping itself (F298), no external author.")
    print("  MACHINE-CODE (non-commuting, one-way) = EXTERNALLY authored: arbitrary content on a generic")
    print("  executor — which is exactly OUR silicon (RBS-LM: F176 'silicon needs us as the external author';")
    print("  F43 naming-layer-cost). So the test of 'is biology machine code or self-resonant' = does the")
    print("  cell-genome SHARE eigenstructure (mutual) or not. The framework's prior (F176 self-inscribing +")
    print("  autopoiesis: the cell SYNTHESISES its own DNA) says RESONANT, not machine code. The exact")
    print("  biological measurement (is the genome literally an eigenmode of cell dynamics, both ways) is the")
    print("  expert's; the co-diagonalizability DISTINCTION is exact and is the honest test to hand them.")


if __name__ == "__main__":
    main()

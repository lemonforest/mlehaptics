"""F295 — the amoeba unifies it: SELF-PARTITION (closing the boundary) is the topological precondition
for the DIRECTED rotating k=3 corrector; + the two F294 follow-ups.

Grabs Spike #254 (social-amoeba self-partition, cloud branch claude/insect-colony-distributed-body) and
joins it to F293/F294 (k=2 detect substrate; k=3 directed-cycle corrector) + F235 (slime-mould on the
chiral Fiedler axis). The slug's TWO phases ARE our two layers:
  - aggregation = rotating cAMP SPIRAL waves  -> a DIRECTED / chiral rotating signal = the F294 corrector
  - slug = self-secreted slime SHEATH         -> CLOSES the boundary (Spike #254 open-path -> closed-cycle)

PART A (follow-up #1, deepened): the directed (chiral) cycle = the k=3 corrector, and CLOSING the loop
(self-partition, Class B) is its precondition:
  A1 open PATH P_n (env-partition, ant-like): srmech real spectrum -> NO rotating mode (can't host a wave)
  A2 undirected CYCLE C_n (closed but symmetric): srmech real spectrum -> closing lifts connectivity
     (Spike #254 lambda2) but symmetric still carries NO phase
  A3 directed (chiral) CYCLE: eigenvalues = n-th roots of unity (COMPLEX) -> carries the rotating phase;
     reverse direction = conjugate spectrum = the winding sign (spiral handedness = chirality)
  -> SELF-PARTITION (close the loop, Class B / Spike #254) is the PRECONDITION for the directed corrector;
     the amoeba does BOTH (sheath closes it; cAMP spirals are the directed rotation).

PART B (follow-up #2): the 3x7 static ℤ₃ on the 21 sense+stop classes — FALSIFIED. A FREE (no-fixed-point,
the distributed-anchor requirement) ℤ₃ code-automorphism needs the 21 classes to split into 7 EQUAL-
degeneracy triples -> every degeneracy multiplicity must be divisible by 3. The standard code's
degeneracy multiset forbids it -> 3|21 is cardinality-only; the static code carries NO ℤ₃ (reinforces F294).

srmech-first (Class-L dense_adjacency/dense_laplacian/jacobi_eigvals). Class-K clean (moduli via re^2+im^2;
no abs in cascades). Attested standard genetic code (NCBI table 1). Scope: STRUCTURE only; no biology
mechanism/clinical claim; cAMP-spiral fact is cite-by-reference (textbook), PDF-extraction-pending.
"""
import os
import sys
import itertools

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from srmech.amsc import laplacian  # noqa: E402  Class-L

# ---- attested standard genetic code (NCBI table 1); T for U; bases T,C,A,G ----
BASES = "TCAG"
_AA = {"T": {"T": "FFLL", "C": "SSSS", "A": "YY**", "G": "CC*W"},
       "C": {"T": "LLLL", "C": "PPPP", "A": "HHQQ", "G": "RRRR"},
       "A": {"T": "IIIM", "C": "TTTT", "A": "NNKK", "G": "SSRR"},
       "G": {"T": "VVVV", "C": "AAAA", "A": "DDEE", "G": "GGGG"}}
CODE = {b1 + b2 + b3: _AA[b1][b2][k] for b1 in BASES for b2 in BASES for k, b3 in enumerate(BASES)}


def path_edges(n):
    return [(i, i + 1) for i in range(n - 1)]


def cycle_edges(n):
    return [(i, (i + 1) % n) for i in range(n)]


def roots_of_unity(n):
    return [np.exp(2j * np.pi * k / n) for k in range(n)]


def part_a():
    print("=== PART A — self-partition (close the loop) is the precondition for the directed corrector ===\n")
    n = 3
    # A1 — open path P_n (environment-partition, ant-like): srmech symmetric adjacency -> REAL
    Ap = laplacian.dense_adjacency(n, path_edges(n))
    evp = sorted(round(float(x), 3) for x in laplacian.jacobi_eigvals(Ap))
    print(f"[A1] open PATH P_{n} adjacency eigenvalues (srmech): {evp}  -> REAL, no rotating mode")
    print(f"     (an open chain that leaks into the environment cannot host a sustained rotating wave)")
    # A2 — undirected cycle C_n (closed but symmetric): srmech -> REAL; connectivity lifts (Spike #254)
    Ac = laplacian.dense_adjacency(n, cycle_edges(n))
    evc = sorted(round(float(x), 3) for x in laplacian.jacobi_eigvals(Ac))
    l2_path = sorted(float(x) for x in laplacian.jacobi_eigvals(laplacian.dense_laplacian(n, path_edges(n))))[1]
    l2_cyc = sorted(float(x) for x in laplacian.jacobi_eigvals(laplacian.dense_laplacian(n, cycle_edges(n))))[1]
    print(f"[A2] undirected CYCLE C_{n} adjacency eigenvalues (srmech): {evc}  -> REAL (symmetric ⇒ no phase)")
    print(f"     closing lifts algebraic connectivity λ2: path {l2_path:.3f} -> cycle {l2_cyc:.3f} "
          f"(×{l2_cyc / l2_path:.2f})  [Spike #254 open→closed self-partition]")
    # A3 — directed (chiral) cycle: roots of unity (COMPLEX); reverse = conjugate (winding sign)
    fwd = roots_of_unity(n)
    rev = [np.conj(z) for z in fwd]                       # reverse direction = mirror = conjugate spectrum
    s = sum(fwd); mod2 = float(s.real) ** 2 + float(s.imag) ** 2
    nonreal = float(fwd[1].imag) ** 2
    print(f"[A3] directed (chiral) CYCLE C_{n} eigenvalues = cube roots of unity: "
          f"{[complex(round(z.real, 3), round(z.imag, 3)) for z in fwd]}  -> COMPLEX (carries the rotating phase)")
    print(f"     trivial mode λ=1 = the CONSERVED all-ones anchor (distributed); rotating modes ω,ω² = the phase/correction")
    print(f"     reverse direction = {[complex(round(z.real, 3), round(z.imag, 3)) for z in rev]} = CONJUGATE = the winding sign (spiral handedness = chirality)")
    print(f"     |1+ω+ω²|²={mod2:.1e}; chiral (non-real) content={nonreal:.3f}")
    print(f"\n  READING: open→closed (self-partition, Class B / Spike #254) is the PRECONDITION; DIRECTION")
    print(f"  (chirality) is the corrector (F294). The social amoeba does BOTH — the slime SHEATH closes the")
    print(f"  loop, the cAMP SPIRAL waves are the directed rotation (winding number = the chirality). The")
    print(f"  distributed body must CLOSE its own boundary to host the k=3 rotating corrector.\n")


def part_b():
    print("=== PART B — follow-up #2: the 3×7 static ℤ₃ on the 21 sense+stop classes ===\n")
    from collections import Counter
    deg = Counter(CODE.values())                          # degeneracy of each of the 21 classes
    mult = Counter(deg.values())                          # how many classes have each degeneracy
    print(f"  21 classes, degeneracy multiset (degeneracy -> #classes): {dict(sorted(mult.items()))}")
    print(f"    e.g. 6-fold: {[a for a,d in deg.items() if d==6]}; 4-fold: {[a for a,d in deg.items() if d==4]}; "
          f"3-fold: {[a for a,d in deg.items() if d==3]}; 1-fold: {[a for a,d in deg.items() if d==1]}")
    # A FREE ℤ₃ code-automorphism partitions the 21 classes into 7 orbits of 3, each orbit EQUAL-degeneracy
    # (an automorphism preserves synonymy-class size). So each degeneracy multiplicity must be divisible by 3.
    blockers = {d: m for d, m in mult.items() if m % 3 != 0}
    free_z3_possible = (len(blockers) == 0)
    print(f"\n  a FREE ℤ₃ (no fixed point = distributed-anchor) code-automorphism needs every degeneracy")
    print(f"  multiplicity divisible by 3 (7 equal-degeneracy triples). Blockers (mult not ÷3): {blockers}")
    print(f"  -> free ℤ₃ on the 21 classes possible? {free_z3_possible}")
    print(f"  -> FALSIFIED: 3 | 21 = 3×7 is CARDINALITY-only; the code's degeneracy structure FORBIDS a free ℤ₃.")
    print(f"     (the synonymy-internal ℤ₃ — a 3-cycle within a ≥3-fold box — is VACUOUS: identity on the classes.)")
    print(f"  -> REINFORCES F294: the static code has NO error-correcting ℤ₃; the corrector is the DYNAMIC")
    print(f"     directed cycle (Part A), not the static codon table.\n")
    return free_z3_possible


def main():
    print("=== F295 — amoeba self-partition × directed corrector; + the 3×7 static-ℤ₃ null ===\n")
    part_a()
    r_b = part_b()
    print("=== synthesis ===")
    print("  Spike #254 (self-partition, Class B) + F293/F294 (k=3 directed corrector) UNIFY: a distributed")
    print("  body must CLOSE its boundary (self-partition) to host the directed rotating corrector. The")
    print("  amoeba is the biological instance (sheath + cAMP spirals). Follow-up #2 null (no static ℤ₃)")
    print("  confirms the corrector is dynamic. Static codon code = order-2 DETECT substrate; dynamic")
    print(f"  directed-closed-cycle = k=3 CORRECT. (3×7 free static ℤ₃ exists: {r_b}.)")


if __name__ == "__main__":
    main()

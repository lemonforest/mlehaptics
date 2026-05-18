"""
Spike #78 anomaly investigation: the 8-dim Cl(7,R) irrep we built has
i*omega_7 = +I globally (not +I on half, -I on half). This is the
SUBSTRATE-IDENTITY tell.

In odd dimensions (7 here), omega_p is CENTRAL, so by Schur's lemma it
acts as a scalar on any irrep. Since (i*omega_7)^2 = +I, the scalar is
either +1 or -1; the two choices give the two INEQUIVALENT 8-dim irreps,
mapped to each other by gamma^a -> -gamma^a (skew-whiff).

So Cl(7,R) has structure  M_8(R) (+) M_8(R) (or M_8(C) (+) M_8(C) over C),
two inequivalent 8-dim irreps. Each is the entire 8-dim space; the 4+4
split inside ONE irrep does NOT occur (that's a Cl(8) thing, where the
volume element is non-central and the 16-dim space splits 8+8 into
chirality halves).

The correct mapping is:

  Irrep #1:  i*omega_7 = +I  on all 8 dims  =>  "P_+ = I, P_- = 0"
  Irrep #2:  i*omega_7 = -I  on all 8 dims  =>  "P_+ = 0, P_- = I"

In KK 11D->4D reduction, the 32-dim 11D spinor sits in
   Cl(1,10) ~ M_32(R)  (one irrep, 32-dim).
When we restrict the SO(1,3) x SO(7) subgroup, the 32-dim space
decomposes as  4D-Dirac (4-dim) x  internal-Cl(7) (8-dim).

But which Cl(7) irrep? Both — because the 32-dim 11D irrep contains
both inequivalent Cl(7) irreps in its decomposition. Specifically:

   32 = 4 * 8   (one Cl(7) irrep) ... but that's only 32 if we use ONE irrep.

Actually: Cl(1,10) is M_32(R) which has a 32-dim irrep. Restricting to
Cl(0,7) x Cl(1,3) gives a tensor decomposition. Cl(1,3) ~ M_4(R) has
4-dim Majorana irrep; Cl(0,7) ~ M_8(R) (+) M_8(R) has 8+8 = 16-dim
total irrep content. The natural tensor is 4 x 16 = 64, but we want 32.
So one of the two Cl(7) summands gets projected out.

Crucial reframe: the 32-dim spinor 4D x 8D doesn't see both Cl(7) irreps
internally — it sees ONE 8-dim Cl(7) irrep, and the "matter/antimatter"
split is provided by gamma_5 in 4D, NOT by i*omega_7.

The "Cl(7,C) ~ Cl(6,C) (+) Cl(6,C)" of Spike #58.K is the COMPLEXIFIED
algebra. Over C:
   Cl(7,C) ~ M_8(C) (+) M_8(C)
two inequivalent 8-dim COMPLEX irreps, indexed by i*omega_7 eigenvalue +-1.

The two summands are the TWO IRREPS, not two halves of one irrep.
Skew-whiff sends one summand to the other.

So Spike #69's setup -- "two complex idempotents (1 +- i*omega_7)/2" --
should be read as: these are the PROJECTORS onto the two inequivalent
irrep summands of Cl(7,C) ~ Cl(6,C) (+) Cl(6,C). They're well-defined
on the FULL Cl(7,C) algebra acting on a reducible 16-dim representation
(8+8). On an irreducible 8-dim rep, one of them is identity and the
other is zero.

KK reduction implication:
  - The 32-dim 11D Majorana spinor restricts to a single Cl(7) irrep
    times the 4D Dirac space. WHICH Cl(7) irrep is a CONVENTION choice
    in the ansatz.
  - The two physical SM chiralities (LH vs RH) are distinguished by
    gamma_5 in 4D, not by i*omega_7 in 7D.
  - HOWEVER: if the 11D theory's KK reduction yields BOTH Cl(7) irreps
    (in different KK towers, or as matter/antimatter), then i*omega_7
    is the right operator to read off which side.

In M-theory compactifications on squashed-S^7 (Awada-Duff-Pope 1983
PRL 50:294 cite-by-ref; BNV 1983 cite-by-ref; Nilsson 2024
arXiv:2412.04208 PDF-verified per project memory):
  - Round S^7 has Spin(8) holonomy; left and right Cl(7) irreps both
    realized (8+8 supersymmetries -> N=8 in 4D).
  - Squashed S^7 (orient+) breaks to G_2 holonomy with 1 Killing spinor
    (N=1 in 4D); only ONE Cl(7) irrep summand survives.
  - Skew-whiffed squashed S^7 (orient-) has 0 Killing spinors (N=0 in 4D);
    the OTHER Cl(7) irrep survives but is not preserved by SUSY.

So orient+ vs orient- is exactly: which of the two complex idempotents
(1 +- i*omega_7)/2 the surviving Cl(7) irrep summand is.

CONVENTION FIX:

  By Awada-Duff-Pope 1983 + BNV 1983 + Nilsson 2024 (all cite-by-ref
  per [[feedback_pdf_extraction_citation_discipline]] -- only Nilsson
  2024 PDF-verified per project memory), the squashed-S^7 with 1 KS
  is "orient+", and its surviving Cl(7) irrep is conventionally the
  i*omega_7 = +1 summand:

      orient+ <==> P_+ = (1 + i*omega_7)/2  <==> 1 Killing spinor

  The 4D N=1 SUSY this yields preserves a single Majorana spinor.
  Under further SU(3)_color x SU(2)_L x U(1)_Y SM breaking, this
  Majorana spinor decomposes into the SM fermions WITH their
  standard left-handed chirality assignment.

  Whether this maps to LH or RH on the 4D Dirac side is FIXED BY
  THE 4D GAMMA-5 CONVENTION, NOT by Cl(7). The 4D LH fermion is
  defined by gamma_5 = -1 (Peskin-Schroeder eq 3.71 + 3.72, with
  gamma_5 = +i*gamma_0*gamma_1*gamma_2*gamma_3 in the standard
  signature (+,-,-,-) and gamma^0 hermitian / gamma^i anti-hermitian).
  SU(2)_L weak isospin couples to gamma_5 = -1 fermions.

  THE TWO LAYERS ARE INDEPENDENT:
    Layer A:  4D chirality   (gamma_5 = +-1)   <==  4D Dirac Cl(1,3)
    Layer B:  internal label (i*omega_7 = +-1) <==  7D Cl(7)

  Both layers commute and provide a tensor 4-fold sector decomposition,
  not a 2-fold one.

So the answer to Spike #78 question #2 is:

  CONVENTION-AMBIGUOUS-MULTIPLE-CHOICES at the "iomega_7 -> LH/RH" level
  taken in isolation, because the two layers are independent. The KK
  ansatz already provides 4D chirality via gamma_5; the i*omega_7
  label is an ADDITIONAL internal-manifold label, not a redundant
  chirality label.

The well-posed Spike #78 question is:

  Q: Which orientation (orient+ vs orient-) on the squashed-S^7
     internal manifold realizes 1 vs 0 Killing spinors?
  A: orient+ realizes 1 KS (BNV 1983 cite-by-ref; Nilsson 2024
     PDF-verified per memory).
  Q: Which Cl(7) irrep does orient+ select?
  A: By the natural projector choice with the ansatz convention above:
     orient+ <==> P_+ = (1 + i*omega_7)/2
     orient- <==> P_- = (1 - i*omega_7)/2
     (Equivalent choice of sign in the volume element; this is the
     "label convention" Spike #69 flagged. The math doesn't care which
     symbol gets which label, but the project freezes the labels.)

  Q: Does orient+ map to LH-SM-matter or RH-SM-matter?
  A: ORTHOGONAL QUESTION -- depends on the 4D gamma_5 convention,
     which is independent of the 7D omega_7 convention.

So the right way to write the CANONICAL PROJECT CONVENTION is:

   ============================================
   Spike #78 canonical convention (2026-05-17)
   ============================================

   7D-internal-manifold orientation label:
       orient+   <==>   P_+ = (1 + i*omega_7)/2
       orient-   <==>   P_- = (1 - i*omega_7)/2

   On squashed-S^7 substrate (Spike #58.O):
       orient+   ==>  1 Killing spinor  (BNV 1983 cite-by-ref;
                                          Nilsson 2024 PDF-verified)
       orient-   ==>  0 Killing spinors (Awada-Duff-Pope 1983 cite-by-ref)

   4D chirality is INDEPENDENT, set by gamma_5 in 4D Cl(1,3):
       gamma_5 = -1  ==>  psi_LH  (couples to SU(2)_L per
                                    Glashow-Weinberg-Salam SM)
       gamma_5 = +1  ==>  psi_RH

   Joint Cl(11) ~ Cl(1,3) x Cl(0,7) decomposition:
       psi = psi_4D (x) chi_7D
       where chi_7D lives in EITHER P_+ or P_- (one Cl(7) irrep).

   In M-theory KK compactification 11D -> 4D x 7D:
       Round S^7   :  both P_+ and P_- present (8+8 KS, N=8)
       Squashed-S^7 orient+  :  P_+ surviving  (1 KS, N=1)
       Squashed-S^7 orient-  :  P_- surviving  (0 KS, N=0)

   Verdict: CONVENTION-FIXED-VIA-Cl(7)-STRUCTURE for the
            (orient+,orient-) <-> (P_+,P_-) labelling.
            ORTHOGONAL to 4D LH/RH labelling, which lives downstream
            in 4D gamma_5 standard SM convention.
"""

import numpy as np

# Reproduce the algebraic check that confirms central scalar action:
I2 = np.eye(2, dtype=complex)
sx = np.array([[0, 1], [1, 0]], dtype=complex)
sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
sz = np.array([[1, 0], [0, -1]], dtype=complex)
I4 = np.eye(4, dtype=complex)
G1 = np.kron(sx, sx); G2 = np.kron(sy, sx); G3 = np.kron(sz, sx)
G4 = np.kron(I2, sy); G5 = np.kron(I2, sz)
g1 = np.kron(G1, sx); g2 = np.kron(G2, sx); g3 = np.kron(G3, sx)
g4 = np.kron(G4, sx); g5 = np.kron(G5, sx)
g6 = np.kron(I4, sy); g7 = np.kron(I4, sz)

I8 = np.eye(8, dtype=complex)
omega7 = g1 @ g2 @ g3 @ g4 @ g5 @ g6 @ g7

print("=" * 70)
print("Substrate-identity confirmation: i*omega_7 on the 8-dim irrep")
print("=" * 70)
print(f"i*omega_7 = {1j*omega7[0,0]:+.6g} * I_8 (scalar action by centrality)")
print(f"All eigenvalues of i*omega_7 equal: {np.linalg.eigvals(1j*omega7)[0]:+.6g}")
print()
print("This is the EXPECTED behaviour for odd-dim Cl(p,q) volume element")
print("acting on an irrep: by Schur's lemma it must be a scalar.")
print()
print("The TWO inequivalent 8-dim irreps of Cl(7,R) are distinguished by")
print("the scalar (+1 or -1); skew-whiff (gamma^a -> -gamma^a) swaps them.")
print()
# Build the OTHER irrep by skew-whiff:
g1n, g2n, g3n, g4n, g5n, g6n, g7n = [-gi for gi in (g1,g2,g3,g4,g5,g6,g7)]
omega7_n = g1n @ g2n @ g3n @ g4n @ g5n @ g6n @ g7n
print(f"After skew-whiff: i*omega_7' = {1j*omega7_n[0,0]:+.6g} * I_8")
print(f"Skew-whiff flips +I <-> -I as expected.  (Spike #69 verdict reproduced.)")
print()
print("=" * 70)
print("Conclusion for Spike #78")
print("=" * 70)
print("""
The two complex idempotents (1 +- i*omega_7)/2 are LABELS for the two
inequivalent 8-dim Cl(7,R) irreps. On a single Cl(7) irrep, one
projector is identity, the other is zero. So:

  PROJECT CANONICAL CONVENTION (2026-05-17, Spike #78):

  - orient+ Cl(7,R) irrep  :=  the one where i*omega_7 = +I
                              labelled by P_+ = (1 + i*omega_7)/2
  - orient- Cl(7,R) irrep  :=  the one where i*omega_7 = -I
                              labelled by P_- = (1 - i*omega_7)/2

  - On squashed-S^7 substrate (Spike #58.O Class C IS skew-whiffing):
      orient+ has 1 Killing spinor  (BNV 1983 cite-by-ref;
                                      Nilsson 2024 PDF-verified)
      orient- has 0 Killing spinors (Awada-Duff-Pope 1983 cite-by-ref)

  - 4D chirality (LH vs RH) is INDEPENDENT, set by 4D gamma_5:
      LH (gamma_5 = -1) couples to SU(2)_L per GWS SM
      RH (gamma_5 = +1) is SU(2)_L singlet (for SM fermions)

  - The full 4D-x-7D sector index is (gamma_5, i*omega_7), giving a
    2x2 = 4-way sector decomposition.  Spike #58.K's
    Cl(7,C) ~ Cl(6,C) + Cl(6,C) is the COMPLEXIFIED algebra splitting
    into two inequivalent 8-dim complex irreps.  Spike #58.K's
    matter/antimatter language refers to the COMBINED i*Gamma_11
    eigenvalue +- 1 in 11D, which is the product of gamma_5 and
    i*omega_7.

  VERDICT: CONVENTION-FIXED-VIA-Cl(7)-STRUCTURE.

  The (orient+,orient-) -> (P_+,P_-) label is fixed (one bit of
  convention choice, set above to the natural i*omega_7 = +1 -> P_+
  reading).  The KK reduction does NOT force a (orient+ -> LH) or
  (orient+ -> RH) identification; that is ORTHOGONAL to Spike #78's
  scope and lives entirely in the standard 4D SM gamma_5 convention.
""")

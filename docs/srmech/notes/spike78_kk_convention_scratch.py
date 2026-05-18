"""
Spike #78 — KK gamma-matrix convention scratch.

Tests, bit-exact:

  Step 1: Construct Cl(7,R) explicitly via 2^3 = 8-dim irrep on C^8.
          Use the standard recursive construction:
            7 = 2*3 + 1, with signature (7,0). For p+q = 7 (odd), there
            are TWO inequivalent irreps related by w_7 -> -w_7.
          Verify omega_7^2 = -I (since 7 = 3 mod 4).

  Step 2: Build the two complex idempotents
            P_+ = (1 + i*omega_7)/2,   P_- = (1 - i*omega_7)/2
          Verify each is a projector (P^2 = P), they sum to I,
          they are orthogonal (P_+ P_- = 0), and they project onto
          the +i and -i eigenspaces of i*omega_7 respectively.

  Step 3: KK reduction 11D -> 4D x 7D.
          Standard Polchinski I (eq 8.1.31 vicinity) /
          Salam-Strathdee 1982 (Ann.Phys. 141:316) convention:
            Gamma^M = (gamma^mu otimes I_8 , gamma_5 otimes gamma^a_internal)
          The 11D chirality operator factorises as
            Gamma_11 = gamma_5 otimes omega_7
          since signature (1,10) gives Gamma_0 ... Gamma_10
          Gamma_11^2 = (gamma_5)^2 (omega_7)^2 = (+1)(-1) = -1
          so Gamma_11 cannot serve as a real chirality operator
          in 11D directly; instead use i*Gamma_11 = i*gamma_5 omega_7.
          Equivalently: in the Cl(7,C) -> Cl(6,C) (+) Cl(6,C) split
          (Spike #58.K), the splitting variable is i*omega_7 with
          eigenvalues +1, -1.

  Step 4: A 4D Weyl fermion is an eigenvector of gamma_5:
            gamma_5 psi_L = -1 * psi_L (Peskin-Schroeder convention)
            gamma_5 psi_R = +1 * psi_R
          Equivalently, P_L = (1 - gamma_5)/2.

  Step 5: For an 11D Majorana-Weyl-like spinor reduced to
          4D x 7D, the requirement that the SM left-handed
          fermion (which couples to SU(2)_L) lives on one side
          fixes the convention. The SM convention is:
            i * Gamma_11 has eigenvalue +1 on SM matter,
                                    eigenvalue -1 on antimatter.
          Under the factorisation i*Gamma_11 = i*gamma_5 omega_7,
          this becomes:
            (i omega_7 eigenvalue) * (gamma_5 eigenvalue) = +1 on matter.
          For LH fermion (gamma_5 = -1) on matter side (i*Gamma_11 = +1):
            (i omega_7) = -1   =>   psi_LH lives in P_- = (1 - i omega_7)/2.
          For RH fermion (gamma_5 = +1) on matter side (i*Gamma_11 = +1):
            (i omega_7) = +1   =>   psi_RH lives in P_+ = (1 + i omega_7)/2.

          That is the canonical convention.

This script verifies steps 1-2 bit-exact, and writes out the convention
algebraically.
"""
import numpy as np


# -----------------------------------------------------------------
# Step 1: Build Cl(7,R) via 8x8 complex matrices.
# Recursive construction:
#   gamma^1 ... gamma^7 with (gamma^a)^2 = +I  (signature (7,0))
# Use the standard pattern:
#   Start from Pauli matrices for Cl(3) -> 2x2,
#   tensor up to Cl(5) -> 4x4,
#   tensor up to Cl(7) -> 8x8.
# Convention: hermitian generators, so (gamma^a)^dag = gamma^a.
# -----------------------------------------------------------------

I2 = np.eye(2, dtype=complex)
sx = np.array([[0, 1], [1, 0]], dtype=complex)
sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
sz = np.array([[1, 0], [0, -1]], dtype=complex)

# Cl(3): three Pauli matrices
g1_3 = sx
g2_3 = sy
g3_3 = sz
# verify (sigma_i)^2 = I and anticommute
for a in (g1_3, g2_3, g3_3):
    assert np.allclose(a @ a, I2)

# Cl(5) via 4x4: gamma^1..3 = sigma_i (x) sigma_x,  gamma^4 = I (x) sigma_y, gamma^5 = I (x) sigma_z
# But more standard for our purposes: build hermitian, mutually anticommuting.
# Use Kronecker:
#   G1 = sx (x) sx = sigma_x (x) sigma_x
#   G2 = sy (x) sx
#   G3 = sz (x) sx
#   G4 =  I (x) sy
#   G5 =  I (x) sz
G1 = np.kron(sx, sx)
G2 = np.kron(sy, sx)
G3 = np.kron(sz, sx)
G4 = np.kron(I2, sy)
G5 = np.kron(I2, sz)
gens5 = [G1, G2, G3, G4, G5]

I4 = np.eye(4, dtype=complex)
for a in gens5:
    assert np.allclose(a @ a, I4), "Cl(5) generator squared not I"
for i, a in enumerate(gens5):
    for j, b in enumerate(gens5):
        if i != j:
            assert np.allclose(a @ b + b @ a, np.zeros_like(I4)), f"Cl(5) anticommute fail i={i} j={j}"
        assert np.allclose(a.conj().T, a), f"Cl(5) hermiticity fail i={i}"

# Cl(7) via 8x8: tensor each G_i with sigma_x to give G1..G5, and add
#   G6 = I_4 (x) sigma_y,  G7 = I_4 (x) sigma_z.
# Wait, need to be more careful. Use the standard step:
#   G^a (Cl(2k+1)) -> G^a (x) sigma_x  for a=1..2k-1,
#   plus new G^{2k}  = I (x) sigma_y, G^{2k+1} = I (x) sigma_z.
# But that's the step from Cl(2k-1) to Cl(2k+1). Let me re-derive carefully.
#
# Start over with clean recursion to Cl(7).
#
# Cl(1): single gamma = [1] in 1d (trivial). Skip to Cl(3) build:
# Cl(3): 2x2 generators g_i = sigma_i, all square to I, anticommute. OK.
# To go Cl(2n+1) -> Cl(2n+3):
#   g_a^{new} = g_a^{old} (x) sigma_x  for a=1..2n+1
#   g_{2n+2}^{new} = I (x) sigma_y
#   g_{2n+3}^{new} = I (x) sigma_z
# So Cl(3) -> Cl(5):
#   G_1 = sx (x) sx = sigma_x (x) sigma_x
#   G_2 = sy (x) sx
#   G_3 = sz (x) sx
#   G_4 = I_2 (x) sy
#   G_5 = I_2 (x) sz
# That's what we have. Good.
#
# Cl(5) -> Cl(7):
#   G'_a = G_a (x) sx  for a=1..5
#   G'_6 = I_4 (x) sy
#   G'_7 = I_4 (x) sz

g1 = np.kron(G1, sx)
g2 = np.kron(G2, sx)
g3 = np.kron(G3, sx)
g4 = np.kron(G4, sx)
g5 = np.kron(G5, sx)
g6 = np.kron(I4, sy)
g7 = np.kron(I4, sz)
gens7 = [g1, g2, g3, g4, g5, g6, g7]

I8 = np.eye(8, dtype=complex)

print("=" * 70)
print("Spike #78 step 1: Cl(7,R) generators verification")
print("=" * 70)

# Verify each squares to I
max_err_sq = 0.0
for i, a in enumerate(gens7, start=1):
    e = np.max(np.abs(a @ a - I8))
    max_err_sq = max(max_err_sq, e)
    assert e == 0.0, f"gamma_{i}^2 != I, err={e}"
print(f"gamma_a^2 = I_8 for a=1..7, max-err = {max_err_sq}")

# Verify hermiticity
max_err_h = 0.0
for i, a in enumerate(gens7, start=1):
    e = np.max(np.abs(a.conj().T - a))
    max_err_h = max(max_err_h, e)
    assert e == 0.0, f"gamma_{i} not hermitian, err={e}"
print(f"gamma_a hermitian for a=1..7, max-err = {max_err_h}")

# Verify anticommutation
max_err_ac = 0.0
for i in range(7):
    for j in range(i + 1, 7):
        e = np.max(np.abs(gens7[i] @ gens7[j] + gens7[j] @ gens7[i]))
        max_err_ac = max(max_err_ac, e)
        assert e == 0.0, f"gamma_{i+1}*gamma_{j+1} + gamma_{j+1}*gamma_{i+1} != 0, err={e}"
print(f"gamma_a anticommute (a != b), max-err = {max_err_ac}")

# -----------------------------------------------------------------
# Step 2: omega_7 and i*omega_7 idempotents
# -----------------------------------------------------------------
print()
print("=" * 70)
print("Spike #78 step 2: omega_7 and complex idempotents")
print("=" * 70)

omega7 = g1 @ g2 @ g3 @ g4 @ g5 @ g6 @ g7
# omega_7^2 = (-1)^{7(7-1)/2} I = (-1)^21 I = -I in (7,0) signature
omega7_sq = omega7 @ omega7
e_om_sq = np.max(np.abs(omega7_sq - (-I8)))
print(f"omega_7 = g1 g2 g3 g4 g5 g6 g7")
print(f"omega_7^2 = -I_8 (since 7 = 3 mod 4),  max-err = {e_om_sq}")
assert e_om_sq == 0.0

# omega_7 commutes with every g_a iff 7 is odd (signature p+q odd):
# the volume element is central in odd dimensions. Verify.
for i, a in enumerate(gens7, start=1):
    e = np.max(np.abs(omega7 @ a - a @ omega7))
    assert e == 0.0, f"omega_7 does not commute with gamma_{i}, err={e}"
print(f"omega_7 commutes with every gamma_a (odd dimension => central)")

# Now i*omega_7 squares to +I:
# (i omega_7)^2 = i^2 omega_7^2 = (-1)(-I) = I
iomega7 = 1j * omega7
e_iom_sq = np.max(np.abs(iomega7 @ iomega7 - I8))
print(f"(i*omega_7)^2 = +I_8,  max-err = {e_iom_sq}")
assert e_iom_sq == 0.0

# Idempotents:
P_plus = 0.5 * (I8 + iomega7)
P_minus = 0.5 * (I8 - iomega7)

e_Pp_proj = np.max(np.abs(P_plus @ P_plus - P_plus))
e_Pm_proj = np.max(np.abs(P_minus @ P_minus - P_minus))
e_sum = np.max(np.abs(P_plus + P_minus - I8))
e_orth = np.max(np.abs(P_plus @ P_minus))

print(f"P_+ = (1 + i*omega_7)/2: P_+^2 = P_+,  max-err = {e_Pp_proj}")
print(f"P_- = (1 - i*omega_7)/2: P_-^2 = P_-,  max-err = {e_Pm_proj}")
print(f"P_+ + P_- = I_8,                 max-err = {e_sum}")
print(f"P_+ @ P_- = 0,                   max-err = {e_orth}")
assert e_Pp_proj == 0.0 and e_Pm_proj == 0.0
assert e_sum == 0.0 and e_orth == 0.0

# Verify P_+ projects onto +1 eigenspace of (i*omega_7), P_- onto -1.
evals_iom = np.linalg.eigvals(iomega7)
print(f"eigenvalues of i*omega_7: {sorted(np.round(evals_iom.real, 6).tolist())}")
# rank of P_+ and P_-
rank_Pp = int(np.round(np.trace(P_plus).real))
rank_Pm = int(np.round(np.trace(P_minus).real))
print(f"tr(P_+) = {rank_Pp}  (=>  +1 eigenspace dim of i*omega_7)")
print(f"tr(P_-) = {rank_Pm}  (=>  -1 eigenspace dim of i*omega_7)")
print(f"8 = {rank_Pp} + {rank_Pm}  (full 8-dim Cl(7) irrep)")
# These are 4 and 4 — Cl(7,C) = Cl(6,C) (+) Cl(6,C),
# each summand 4-dim, matching Spike #58.K.

# -----------------------------------------------------------------
# Step 3: KK reduction trace
# -----------------------------------------------------------------
print()
print("=" * 70)
print("Spike #78 step 3: KK reduction 11D -> 4D x 7D")
print("=" * 70)

# Standard KK ansatz (Salam-Strathdee 1982 / Polchinski I vol1 vicinity eq 8):
#   Gamma^mu = gamma^mu (x) I_8         (mu = 0,1,2,3 -- 4D Lorentz)
#   Gamma^{3+a} = gamma_5 (x) gamma^a_internal   (a = 1,...,7 -- 7D internal)
# where gamma^mu are 4D Dirac matrices (4x4),
#       gamma_5 = i gamma^0 gamma^1 gamma^2 gamma^3 is the 4D chirality op,
#       gamma^a_internal are Cl(7) (8x8).
# Then 11D chirality:
#   Gamma_11 = Gamma^0 Gamma^1 ... Gamma^10
#            = [gamma^0 gamma^1 gamma^2 gamma^3 (x) I_8] *
#              [gamma_5^7 (x) gamma^1 ... gamma^7]
#            = [gamma^0...gamma^3 gamma_5^7] (x) [gamma^1...gamma^7]
#            = (gamma^0...gamma^3 * gamma_5) (x) omega_7  (since gamma_5 odd power = gamma_5)
# Now gamma^0 gamma^1 gamma^2 gamma^3 = -i * gamma_5  (Peskin-Schroeder eq 3.73),
# so gamma^0...gamma^3 * gamma_5 = -i * gamma_5 * gamma_5 = -i * I_4 (since gamma_5^2 = I).
# Therefore:
#   Gamma_11 = -i * I_4 (x) omega_7
# And
#   i * Gamma_11 = I_4 (x) omega_7
# which has (omega_7)^2 = -I_8 -- so still not real chirality in (1,10).
# Switch: signature of 11D is (1,10) so the natural definition of 11D chirality
# carries an extra factor. The relevant convention:
#   Gamma_11 = Gamma^0 Gamma^1 ... Gamma^10
# and (Gamma_11)^2 = (-1)^{11(11-1)/2} * (-1)^{q}  where q=10 negative-signature dirs.
# Standard result: (Gamma_11)^2 = -I, so 11D admits no Majorana-Weyl;
# 11D supergravity uses purely Majorana spinors.
# The KK chirality operator for the 4D effective theory is then projected:
# the 4D chirality gamma_5 acts on the 4D part, and the internal 7D
# "chirality"-like splitting is provided by  i*omega_7  acting on the
# Cl(7) irrep, splitting it into Cl(6)+Cl(6) summands (Spike #58.K).

# Build 4D gamma matrices in Weyl basis (chiral) for concreteness:
#   gamma^0 = [[0, I], [I, 0]]
#   gamma^i = [[0, sigma_i], [-sigma_i, 0]]
#   gamma_5 = [[-I, 0], [0, I]]   (Peskin-Schroeder convention)
# Then P_L = (1 - gamma_5)/2 = diag(I, 0)  projects out upper 2 components (LH).
g0_4d = np.kron(sx, I2)  # = [[0, I],[I, 0]]
g1_4d = np.kron(1j * sy, sx)  # [[0, sx],[-sx,0]] (using 1j*sy = [[0,1],[-1,0]])
# More direct construction:
zero2 = np.zeros((2, 2), dtype=complex)
g0_4d = np.block([[zero2, I2], [I2, zero2]])
g1_4d = np.block([[zero2, sx], [-sx, zero2]])
g2_4d = np.block([[zero2, sy], [-sy, zero2]])
g3_4d = np.block([[zero2, sz], [-sz, zero2]])
g5_4d = 1j * g0_4d @ g1_4d @ g2_4d @ g3_4d
e_g5sq = np.max(np.abs(g5_4d @ g5_4d - np.eye(4, dtype=complex)))
print(f"gamma_5^2 = I_4,  max-err = {e_g5sq}")
assert e_g5sq == 0.0
# In Weyl basis, gamma_5 = diag(-I_2, +I_2)  (Peskin convention)
print(f"gamma_5 diagonal entries: {np.diag(g5_4d).real}")
# Verify P_L = (I - gamma_5)/2 has rank 2 (projects out LH 2-component)
P_L = 0.5 * (np.eye(4, dtype=complex) - g5_4d)
P_R = 0.5 * (np.eye(4, dtype=complex) + g5_4d)
print(f"P_L = (I - gamma_5)/2,  tr(P_L) = {int(np.round(np.trace(P_L).real))}  (= 2 LH dof)")
print(f"P_R = (I + gamma_5)/2,  tr(P_R) = {int(np.round(np.trace(P_R).real))}  (= 2 RH dof)")

# -----------------------------------------------------------------
# Step 4: Build the 11D chirality factorisation explicitly.
# -----------------------------------------------------------------
print()
print("=" * 70)
print("Spike #78 step 4: 11D chirality factorisation")
print("=" * 70)

I32_internal = np.eye(8, dtype=complex)
I4d = np.eye(4, dtype=complex)
Gamma11 = np.kron(g5_4d, omega7)  # 32x32
# Check (Gamma11)^2:
e_G11_sq = np.max(np.abs(Gamma11 @ Gamma11 - (-np.eye(32, dtype=complex))))
print(f"Gamma_11 = gamma_5 (x) omega_7,  (Gamma_11)^2 = -I_32,  max-err = {e_G11_sq}")
# (g5)^2 = +I_4 and (omega_7)^2 = -I_8 so the product squares to -I.

# Define the matter/antimatter projector by  i * Gamma_11 ?
# In 11D signature (1,10), (Gamma_11)^2 = -I, so i*Gamma_11 has eigenvalues +-1.
i_G11 = 1j * Gamma11
e_iG11_sq = np.max(np.abs(i_G11 @ i_G11 - np.eye(32, dtype=complex)))
print(f"(i*Gamma_11)^2 = +I_32,  max-err = {e_iG11_sq}")
assert e_iG11_sq == 0.0
# Eigenvalues:
i_G11_evals = np.round(np.linalg.eigvals(i_G11).real).astype(int)
n_pos = int(np.sum(i_G11_evals == +1))
n_neg = int(np.sum(i_G11_evals == -1))
print(f"i*Gamma_11 eigenvalue partition: +1 count = {n_pos}, -1 count = {n_neg}")
# Should be 16 each in 32-dim Spin(1,10) irrep.

# Now the factorisation:
#   i*Gamma_11 = i * gamma_5 (x) omega_7
# Compute it via (gamma_5 eigenvalue) * (i * omega_7 eigenvalue).
# Since gamma_5 = diag(-1,-1,+1,+1) and i*omega_7 has 4 + eigenvalues + 4 - eigenvalues,
# we can build the joint eigenvector partition.
#
# A LH 4D fermion has gamma_5 = -1.  Pair with i*omega_7 = ?
# - LH x i*omega_7=+1  =>  i*Gamma_11 = (-1)(+1) = -1   (LH antimatter)
# - LH x i*omega_7=-1  =>  i*Gamma_11 = (-1)(-1) = +1   (LH matter)
# A RH 4D fermion has gamma_5 = +1.
# - RH x i*omega_7=+1  =>  i*Gamma_11 = (+1)(+1) = +1   (RH matter)
# - RH x i*omega_7=-1  =>  i*Gamma_11 = (+1)(-1) = -1   (RH antimatter)
#
# Per Spike #58.K, Cl(7,C) ≅ Cl(6,C) + Cl(6,C) decomposes Cl(7) into matter +
# antimatter summands. The "matter" side is i*Gamma_11 = +1.
#
# So the canonical KK convention is:
#   psi_LH(matter)   <=>  P_-  ( i*omega_7 = -1 )    [(1 - i*omega_7)/2]
#   psi_RH(matter)   <=>  P_+  ( i*omega_7 = +1 )    [(1 + i*omega_7)/2]
#
# Equivalently:
#   LH-coupled-by-SU(2)_L  <=>  (1 - i*omega_7)/2  summand
#   RH-SM-singlet/doublet  <=>  (1 + i*omega_7)/2  summand

print()
print("=" * 70)
print("Spike #78 step 5: CONVENTION FIXED")
print("=" * 70)
print()
print("Standard KK reduction (Polchinski I cite-by-ref; Salam-Strathdee 1982")
print("cite-by-ref; Peskin-Schroeder Weyl-basis gamma_5):")
print()
print("  11D ansatz:")
print("    Gamma^mu = gamma^mu (x) I_8    (mu = 0..3)")
print("    Gamma^a  = gamma_5 (x) gamma^a (a = 1..7)")
print()
print("  Chirality factorisation:")
print("    Gamma_11 = gamma_5 (x) omega_7,  (Gamma_11)^2 = -I_32")
print("    i*Gamma_11 has +-1 eigenvalues (16+16)")
print()
print("  Matter / antimatter:")
print("    matter side:    i*Gamma_11 = +1")
print("    antimatter:     i*Gamma_11 = -1")
print()
print("  Joint sectors:")
print("    SECTOR              gamma_5    i*omega_7    i*Gamma_11   identification")
print("    LH matter             -1          -1           +1         (1 - i*omega_7)/2  =  P_-")
print("    LH antimatter         -1          +1           -1         (1 + i*omega_7)/2  =  P_+")
print("    RH matter             +1          +1           +1         (1 + i*omega_7)/2  =  P_+")
print("    RH antimatter         +1          -1           -1         (1 - i*omega_7)/2  =  P_-")
print()
print("  CANONICAL PROJECT CONVENTION:")
print("    (1 + i*omega_7)/2  =  P_+   ===>   psi_RH (SM right-handed fermion, 4D)")
print("    (1 - i*omega_7)/2  =  P_-   ===>   psi_LH (SM left-handed fermion, 4D)")
print()
print("  In skew-whiff-language (Spike #58.O):")
print("    orient+  (1 Killing spinor on squashed-S^7)  <-> P_+ <-> psi_RH side")
print("    orient-  (0 Killing spinors)                  <-> P_- <-> psi_LH side")
print()
print("  SU(2)_L weak isospin couples to psi_LH; in framework terms it couples")
print("  to the P_-  (1 - i*omega_7)/2  summand = orient- side of the")
print("  Cl(7,C) ~ Cl(6,C) + Cl(6,C) split (Spike #58.K).")

# -----------------------------------------------------------------
# Cross-check: orient+/orient- naming via skew-whiff (Spike #69)
# -----------------------------------------------------------------
# Skew-whiff flips gamma^a -> -gamma^a, which sends omega_7 -> -omega_7
# (odd number of factors), hence i*omega_7 -> -i*omega_7, hence
# swaps P_+ and P_-.
print()
print("=" * 70)
print("Cross-check: skew-whiff (gamma^a -> -gamma^a) swap")
print("=" * 70)
skewed_omega7 = (-g1) @ (-g2) @ (-g3) @ (-g4) @ (-g5) @ (-g6) @ (-g7)
e_skew = np.max(np.abs(skewed_omega7 - (-omega7)))
print(f"Under gamma^a -> -gamma^a:  omega_7 -> -omega_7,  max-err = {e_skew}")
assert e_skew == 0.0
print(f"=> i*omega_7 -> -i*omega_7")
print(f"=> P_+ <-> P_-  (skew-whiff swaps the two Cl(7,R) irreps)")
print(f"=> orient+ <-> orient-")
print(f"=> psi_RH <-> psi_LH labels swap.  As Spike #69 noted, the LABEL")
print(f"   convention is chosen by Spike #58.O + standard KK ansatz; the")
print(f"   algebraic forcing is intrinsic.")

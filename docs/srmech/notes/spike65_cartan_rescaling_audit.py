"""
Spike #65 — Overall sqrt(3/5) GUT-norm rescaling: convention or derivable?

Setup per Spike #58 thread:
- Lohitsiri-Tong + Euler/Fermat fix the U(1)_Y *group structure* (no other
  Y assignments cancel anomalies on the SM matter content).
- Stoica 1702.04336 §7 eq. 94-95 derives sin^2(theta_W,N) = (1/2)(N-2)/(N-1)
  from a U(2)_ew -> SU(N) embedding via inner-product matching, yielding
  3/8 at N=5 (SU(5) bare GUT value).
- The Cl(6,C) ASM at N=3 yields the SAME closed form -> 1/4 (different SM ref
  scheme, equally bit-exact at the algebra level).

The remaining open question: is there a privileged overall scale
sqrt(3/5) (i.e. r_5/r_3 ratio, or equivalently the Cartan-subalgebra
normalization scale) that the substrate FORCES, or is r_N a free constant
("up to a constant r" per Stoica below eq.91) that physics conventions fix
externally?

This script tests four things bit-exact:

(I)   sin^2 theta_W is INVARIANT under any overall rescaling r_N -> lambda r_N.
      This is the formal statement of the "ratio is fixed, scale is open" picture.

(II)  The Killing form on so(n) is K(X,Y) = (n-2) Trace(XY) (Helgason convention).
      For Cl(6,C) bivectors so(6,C), n=6 gives K = 4 Tr(XY). Is the Killing form
      a privileged Cartan normalization that fixes r_6 (and via the embedding,
      r_N for relevant N)?

(III) The standard SU(5) GUT-norm rescaling sqrt(3/5) of Y comes from demanding
      that ALL Cartan generators of SU(5) have equal trace-normalization
      Tr(T_a^2) = 1/2 in the fundamental rep. Check this bit-exact: does
      embedding Y_SM in SU(5) Cartan equal Tr(T_a^2) = 1/2 give Y' = sqrt(3/5) Y?

(IV)  Does the Cl(6,C) bivector inner product, restricted to the U(1)_Y
      direction and the SU(2)_L Cartan T_3, give the same sqrt(3/5) or a
      DIFFERENT factor? If different, the rescaling is substrate-specific,
      not universally derivable.

Verdict scale per brief:
- CONVENTION-NOT-DERIVABLE: r_N freely chosen; sqrt(3/5) is convention attached
  to SU(5), not forced by any deeper algebra.
- DERIVABLE-FROM-CARTAN: Killing-form on so(N) or fundamental-rep equal-trace
  normalization forces a specific r_N, and that r_N reproduces sqrt(3/5).
- DERIVABLE-FROM-OTHER: some other algebraic constraint (anomaly, mass-fit,
  Witt-pair count) forces it.
- UNKNOWN: investigation inconclusive.
"""

from fractions import Fraction
import numpy as np

# ---------------------------------------------------------------
# (I) Scale-invariance of sin^2 theta_W under r_N -> lambda r_N
# ---------------------------------------------------------------
# From Stoica eq. 93b solution:
#     g^2  = N r_N / (2 r^2)
#     g'^2 = g^2 + N r_N / ((N-2) r^2)
# Both g^2 and g'^2 scale linearly with r_N; their RATIO does not.
# sin^2 theta_W = g^2 / (g^2 + g'^2). Let's confirm bit-exact.

def sin2_W_general(N, r_N, r_sq):
    g_sq = Fraction(N) * r_N / (2 * r_sq)
    g_prime_sq = g_sq + Fraction(N, N - 2) * (r_N / r_sq)
    return g_sq / (g_sq + g_prime_sq)

print("=" * 70)
print("(I) Scale-invariance of sin^2 theta_W under r_N -> lambda r_N")
print("=" * 70)
for (r_N, r_sq) in [(Fraction(1), Fraction(1)),
                    (Fraction(2), Fraction(1)),
                    (Fraction(7, 11), Fraction(5, 3)),
                    (Fraction(1000), Fraction(1, 17))]:
    rows = []
    for N in [3, 4, 5, 6]:
        s = sin2_W_general(N, r_N, r_sq)
        rows.append((N, str(s), float(s)))
    print(f"  r_N={r_N!s:>8} r^2={r_sq!s:>8}  ", end="")
    print(", ".join(f"N={N}:{s_str}" for (N, s_str, _) in rows))

# Closed-form check: sin^2 theta_W reduces to (1/2)(N-2)/(N-1) regardless
# of r_N or r^2. -> Stoica's claim "up to a constant r" is bit-exact.
print()
print("  -> sin^2 theta_W is INDEPENDENT of (r_N, r^2). Math doesn't lie.")
print("     The overall scale r_N is NOT fixed by the inner-product matching.")
print()

# ---------------------------------------------------------------
# (II) Killing form on so(6,C) and its relation to r_6
# ---------------------------------------------------------------
# Helgason / Knapp: for so(n,C), the Killing form on the Lie algebra is
# K(X,Y) = (n-2) Trace(XY) in the defining (vector) rep.
# (Derivation: K(X,Y) = sum_a c^a_b^d c^d_a^b ; for so(n) this collapses to
#  (n-2) Tr(XY) in the n-dim rep. See e.g. Fuchs-Schweigert §6.2.)
#
# For Cl(6,C), bivectors span so(6,C), and the natural rep is 6-dimensional
# (the Witt-vector space of the Cl(6,C) ASM, complex dim 6).
#
# But Stoica's eq. 91 is on su(N) with rep DIM_N = N, not so(2N).
# The Cl(6,C) ASM uses su(3) (N=3, dim 3) as the color group acting on the
# 3-dim Witt subspace -> r_3 in this case.

# Killing form normalization for su(N): K_su(N)(X,Y) = 2N Tr(XY) in the fundamental.
# So if we demand "Killing form = inner product", we fix the prefactor:
#     -N r_N Tr(AB) = K(A,B) = 2N Tr(AB)
#     -> r_N = -2 (negative because Stoica's metric is anti-Hermitian-skew)
# Up to sign, r_N = 2 for ALL N.

print("=" * 70)
print("(II) Killing-form prescription r_N = 2 (Helgason) -> sin^2 still 1/4")
print("=" * 70)
for N in [3, 4, 5, 6]:
    s_killing = sin2_W_general(N, Fraction(2), Fraction(1))
    s_unit    = sin2_W_general(N, Fraction(1), Fraction(1))
    same = s_killing == s_unit
    print(f"  N={N}: Killing r_N=2 -> {s_killing} ; unit r_N=1 -> {s_unit} ; same: {same}")
print()
print("  -> Even pinning r_N to the Killing form gives the SAME sin^2 theta_W.")
print("     The Killing form does not break the scale-invariance: the ratio")
print("     g^2/(g^2+g'^2) cancels every overall factor.")
print()

# ---------------------------------------------------------------
# (III) SU(5) sqrt(3/5) rescaling: bit-exact derivation
# ---------------------------------------------------------------
# In SU(5) GUT, the embedding decomposes as 5 -> (3,1)_{-1/3} + (1,2)_{1/2}
# (this is the SM decomposition of the fundamental of SU(5)).
# The hypercharge generator inside SU(5) is, in the fundamental:
#   Y_SU5 = diag(-1/3, -1/3, -1/3, 1/2, 1/2)
# Normalization in SU(5): Tr(T_a T_b) = (1/2) delta_ab in the fundamental.
# So the "normalized" hypercharge generator Y' must satisfy Tr(Y'^2) = 1/2.

Y_SU5_diag = np.array([-1/3, -1/3, -1/3, 1/2, 1/2])
Tr_Y_SU5_sq = np.sum(Y_SU5_diag**2)
print("=" * 70)
print("(III) sqrt(3/5) from SU(5) Cartan-equal-trace normalization")
print("=" * 70)
print(f"  Y_SU5 = diag(-1/3, -1/3, -1/3, +1/2, +1/2)")
print(f"  Tr(Y_SU5^2) = 3*(1/9) + 2*(1/4) = 1/3 + 1/2 = {Fraction(1,3)+Fraction(1,2)} = {Tr_Y_SU5_sq:.10f}")
# Required for SU(5) Cartan normalization Tr(Y'^2) = 1/2: rescale by lambda
# such that lambda^2 * Tr(Y_SU5^2) = 1/2.
# lambda^2 = (1/2) / (5/6) = 3/5. lambda = sqrt(3/5).
lambda_sq = Fraction(1, 2) / (Fraction(1, 3) + Fraction(1, 2))
print(f"  Demand Tr((lambda*Y_SU5)^2) = 1/2 -> lambda^2 = (1/2)/(5/6) = {lambda_sq}")
print(f"  -> lambda = sqrt({lambda_sq}) = sqrt(3/5)  EXACT")
print(f"  -> This is the standard origin of the GUT-norm sqrt(3/5).")
print(f"     It comes from Cartan-equal-trace in the FUNDAMENTAL of SU(5).")
print(f"     It is a STATEMENT ABOUT SU(5), not about SU(3) or Cl(6,C).")
print()

# ---------------------------------------------------------------
# (IV) Cl(6,C) bivector inner product: what is the analogous rescaling?
# ---------------------------------------------------------------
# Build Cl(6,C) bivectors corresponding to T_3 (SU(2)_L Cartan) and Y (U(1)_Y),
# compute trace inner products in the 8-dim fundamental rep (M_8(C)) and
# in the 3-dim Witt-vector rep so(6,C) -> su(3).
#
# Construction per spike58_p_normalization_audit conclusion:
#   In Cl(6,C) ASM, T_3 is a bivector pair like (gamma_3 gamma_4 - gamma_5 gamma_6),
#   Y is a different bivector pair, identified per Stoica eq. (15).
#
# But the KEY point: in Cl(6,C), the bivector "inner product" Tr(B1 B2) on M_8(C)
# is FIXED by the dimension of the rep (8). There is NO free parameter analogous
# to r_N once the rep is chosen.
#
# Build explicit Cl(6,C) gamma matrices via Witt-pair construction and check.

# Cl(6,C) gamma matrices (8x8 complex)
# Use the construction: a_k = (gamma_{2k-1} + i gamma_{2k})/2, b_k = (gamma_{2k-1} - i gamma_{2k})/2
# for k=1,2,3, with {a_i, b_j} = delta_ij, {a_i, a_j} = {b_i, b_j} = 0
# Standard Fock-like representation on C^8 = Lambda^* C^3.

dim = 8
sigma_x = np.array([[0,1],[1,0]], dtype=complex)
sigma_y = np.array([[0,-1j],[1j,0]], dtype=complex)
sigma_z = np.array([[1,0],[0,-1]], dtype=complex)
I2 = np.eye(2, dtype=complex)

def kron3(A, B, C):
    return np.kron(np.kron(A, B), C)

# Build gamma_1..gamma_6 (6 matrices, anticommuting)
gamma = [None] * 7  # 1-indexed
gamma[1] = kron3(sigma_x, I2, I2)
gamma[2] = kron3(sigma_y, I2, I2)
gamma[3] = kron3(sigma_z, sigma_x, I2)
gamma[4] = kron3(sigma_z, sigma_y, I2)
gamma[5] = kron3(sigma_z, sigma_z, sigma_x)
gamma[6] = kron3(sigma_z, sigma_z, sigma_y)

# Verify Clifford algebra: {gamma_i, gamma_j} = 2 delta_ij I_8
err = 0
for i in range(1, 7):
    for j in range(1, 7):
        anti = gamma[i] @ gamma[j] + gamma[j] @ gamma[i]
        expected = (2 if i == j else 0) * np.eye(8, dtype=complex)
        err += np.linalg.norm(anti - expected)
print("=" * 70)
print("(IV) Cl(6,C) bivector inner products vs sqrt(3/5)")
print("=" * 70)
print(f"  Cl(6,C) anticommutator check: max error = {err:.2e}")

# Build T_3 (SU(2)_L Cartan) and Y (U(1)_Y) as bivectors
# Per Trayling-Baylis (1996, in CL6 form via isomorphism C7 ~ M_8(C) ~ C6):
#   T_3 ~ (1/4)(gamma_5 gamma_4 + gamma_7 gamma_6) -> in CL6: gamma_5 gamma_4 - gamma_3 gamma_4
# We need the SU(2)_L and U(1)_Y bivectors that act on the Witt-vector u/d doublet.
#
# In Cl(6,C) ASM: Ww = span_C(u, d) where u = a_1, d = a_2 b_3 (or similar).
# T_3 = (1/2)(N_2 - N_3) where N_k = a_k b_k is the k-th number operator.
# Y = (1/3)(N_1 + N_2 + N_3) - 1/2 (Stoica eq.15, choice of Y for ASM).

# Build a_k, b_k as 8x8 matrices via the Witt isomorphism
def witt_pair(k):
    """Return a_k, b_k = (gamma_{2k-1} +/- i gamma_{2k})/2."""
    return ((gamma[2*k-1] + 1j*gamma[2*k]) / 2,
            (gamma[2*k-1] - 1j*gamma[2*k]) / 2)

a = [None] * 4
b = [None] * 4
for k in range(1, 4):
    a[k], b[k] = witt_pair(k)

# Number operators N_k = a_k b_k
N = [None] * 4
for k in range(1, 4):
    N[k] = a[k] @ b[k]

# SU(2)_L T_3 and U(1)_Y as in the Cl(6,C) ASM (Stoica eq. 14-15)
T3 = (N[2] - N[3]) / 2
Y  = (N[1] + N[2] + N[3]) / 3 - np.eye(8, dtype=complex) / 2

# Verify hypercharges on the 8 basis states span the SM expectations
# Basis states of M_8(C) = Lambda^* C^3: ordered as |0>, a_1|0>, a_2|0>, a_3|0>,
# a_1 a_2|0>, a_1 a_3|0>, a_2 a_3|0>, a_1 a_2 a_3|0>.
# Eigenvalues of N_k: 0/1 depending on presence of a_k.
# Compute Y eigenvalues bit-exact:
Y_diag = np.diag(Y).real  # Y should be diagonal in this basis
T3_diag = np.diag(T3).real
print(f"  Y diagonal values: {Y_diag}")
print(f"  T_3 diagonal values: {T3_diag}")

# Compute Tr(T_3^2) and Tr(Y^2) on the FULL 8-dim rep
tr_T3_sq = np.trace(T3 @ T3).real
tr_Y_sq  = np.trace(Y @ Y).real
print(f"  Tr(T_3^2)_M8 = {tr_T3_sq}")
print(f"  Tr(Y^2)_M8   = {tr_Y_sq}")
print(f"  Ratio Tr(Y^2)/Tr(T_3^2) = {Fraction(int(round(tr_Y_sq*36)),36) / Fraction(int(round(tr_T3_sq*36)),36)}")
ratio = tr_Y_sq / tr_T3_sq
print(f"  Numeric ratio = {ratio}")

# In SU(5): Y' = sqrt(3/5) Y means (Y')^2 = (3/5) Y^2.
# For SU(5) to give 3/8: with the rescaling, Tr((Y')^2)/Tr(T_3^2) = 3/5 (one chiral gen).
# That is: ratio_GUT_norm = (3/5) * ratio_SM_norm, and 3/8 emerges from the trace ratio.

# In Cl(6,C) at full M_8(C), what is the "natural" rescaling implied by the
# bivector inner product? The Cl(6,C) bivector Killing form on so(6,C) is
#   K(B1, B2) = (6-2) Tr_so6(B1 B2) = 4 Tr_so6(B1 B2)
# on the 6-dim defining rep (Witt-vector space). But our T_3, Y are written
# on the 8-dim spinor rep M_8(C). The spinor and vector reps relate by:
#   Tr_spinor(B^2) = (dim_spinor / dim_vector) * (B-dependent factor)
# specifically for so(6,C): dim_spinor = 8, dim_vector = 6, and for a bivector
# B = (1/2) sum w_ab gamma^a gamma^b in the spinor rep,
#   Tr_spinor(B B) = 2^{n/2} * (- (1/4) sum w_ab^2)  [n=6, 2^3 = 8]
#   Tr_vector(B B) = -2 sum w_ab^2 (rep-dependent, signs depending on convention).
# Both reps give the SAME bivector inner product UP TO an overall positive factor
# determined by the rep dimension. Neither rep introduces a new free parameter,
# but the choice of rep does set an overall normalization.

# Test: does ANY rescaling of Y in Cl(6,C) give 3/8 (the SU(5) value)?
# (3/8 = ratio when sin^2 theta_W = 3/8.)
# In Stoica's framework: sin^2 theta_W is FIXED by (N-2)/(2(N-1)) for the embedding,
# NOT by the trace ratio. The trace ratio computed above is a SEPARATE quantity
# (the formal "trace of generators squared in the spinor rep").

# Conclusion check: try to find a rescaling lambda such that
#   lambda^2 * Tr_M8(Y^2) / Tr_M8(T_3^2) gives "3/5" (the SU(5)-style ratio)
# vs lambda^2 such that the ratio gives "1/3" (the Cl(6,C) ASM 1/4 condition).

# For sin^2 = g'^2/(g^2+g'^2) = 1/4 with the convention sin^2 = (lambda^2 * tr Y^2)/(lambda^2 tr Y^2 + tr T_3^2):
# need lambda^2 * tr Y^2 = (1/3) * tr T_3^2
# -> lambda^2 = (1/3) * tr T_3^2 / tr Y^2 = (1/3) / ratio
lambda_sq_quarter = Fraction(1, 3) / Fraction(int(round(tr_Y_sq*3)), int(round(tr_T3_sq*3)))
print(f"  For ratio = 1/4 (Stoica/ASM): lambda^2 = (1/3)/ratio = {lambda_sq_quarter} = {float(lambda_sq_quarter)}")
# For sin^2 = 3/8: need lambda^2 * tr Y^2 = (3/5) * tr T_3^2 (matching SU(5) Cartan-equal-trace)
lambda_sq_threeeighths = Fraction(3, 5) / Fraction(int(round(tr_Y_sq*3)), int(round(tr_T3_sq*3)))
print(f"  For ratio = 3/8 (SU(5) GUT): lambda^2 = (3/5)/ratio = {lambda_sq_threeeighths} = {float(lambda_sq_threeeighths)}")
# Compute the ratio of these: gives the relative rescaling between
# the SU(5) GUT scheme and the Cl(6,C) ASM scheme
rel = lambda_sq_threeeighths / lambda_sq_quarter
print(f"  Relative SU(5)/ASM Cartan rescaling^2 = (3/5)/(1/3) = {Fraction(3,5)/Fraction(1,3)} = 9/5")
print(f"  -> lambda_SU5/lambda_ASM = sqrt(9/5) = 3/sqrt(5)")
print()
print(f"  Note: this is NOT the canonical sqrt(3/5). It is the RATIO of two")
print(f"  different conventions, each derivable from its own Cartan-equal-trace")
print(f"  prescription, but each LIVES in a different substrate (SU(5) vs Cl(6,C)).")
print()

# ---------------------------------------------------------------
# Final verdict synthesis
# ---------------------------------------------------------------
print("=" * 70)
print("VERDICT SYNTHESIS")
print("=" * 70)
print("""
(I)  sin^2 theta_W from Stoica eq.94 is BIT-EXACT INVARIANT under r_N -> lambda r_N.
     The overall scale r_N is therefore NOT fixed by the inner-product
     matching that derives the Weinberg angle.

(II) The Killing form is a privileged Lie-algebra-invariant choice
     (r_N = 2 by Helgason), but the *ratio* sin^2 theta_W cancels every r_N
     anyway. Killing-form normalization does not break the scale freedom of
     the matching.

(III) The standard sqrt(3/5) GUT-norm rescaling is DERIVABLE inside SU(5):
     it is what Cartan-equal-trace Tr(T_a^2) = 1/2 on the fundamental
     enforces when comparing Y_SM to the other SU(5) Cartan generators.
     This derivation IS Cartan-internal, and bit-exact: lambda^2 = (1/2) /
     (1/3 + 1/2) = 3/5.

(IV) The Cl(6,C) ASM yields sin^2 theta_W = 1/4 via the SAME closed form at
     N=3 (not from any new free parameter). The rescaling implied by the
     Cl(6,C) bivector inner product on M_8(C), normalized to match Stoica's
     1/4 trace ratio, is DIFFERENT from sqrt(3/5):
         lambda_ASM^2 = (1/3) / (Tr Y^2 / Tr T_3^2)_M8 = 1/2
         lambda_SU5^2 = (3/5) / (Tr Y^2 / Tr T_3^2)_M8 (in same rep) = 9/10
     The RATIO sqrt(9/5) = 3/sqrt(5) is what would relate SU(5) and ASM
     conventions on a common basis -- not a unique privileged value.

KEY DISTINCTION:
     - "sqrt(3/5)" as a STATEMENT ABOUT SU(5) (Cartan-equal-trace in the
       fundamental rep) is DERIVABLE-FROM-CARTAN, bit-exact rational 3/5.
     - "sqrt(3/5)" as an UNIVERSAL OVERALL RESCALING for any GUT-norm-to-SM-norm
       comparison is NOT DERIVABLE. It is specifically the SU(5)-rep
       prescription. Different substrates (Cl(6,C), Spin(10), Pati-Salam,
       trinification) each induce DIFFERENT Cartan rescalings.

VERDICT: PARTIAL-DERIVABLE-FROM-CARTAN
     - Derivable WITHIN SU(5) from Cartan-equal-trace in the fundamental.
     - NOT universally fixed -- different substrates give different rescalings.
     - The remaining choice between (3/5)-style and (1/2)-style is a
       substrate-selection step, not a free convention but also not algebra-
       free derivation. Substrate-identity question (Spike #51, R2-alpha)
       feeds directly into which Cartan prescription is canonical.
""")

"""Computational-provenance oracle for the rc233 (#824) riemann_theta.transform
ζ₈-multiplier fix.

This is a THROWAWAY NUMERIC verification (float/cmath — NOT shipped package code; it
lives under docs/, outside the numpy/math-free srmech package tree).  It establishes,
from first principles, the exact-integer ζ₈ exponent that the shipped exact-integer
``RiemannTheta{,G3,G4}._kappa_exp8`` / ``srmech_riemann_theta_*_char`` must reproduce.

Law (DLMF §21.5.9; Igusa, *Theta Functions*, Springer Grundlehren 194, 1972, Ch. V):
    θ[γ·m]((CΩ+D)⁻ᵀz | γ·Ω)
        = κ₀(γ)·e^{2πi φ_m(γ)}·det(CΩ+D)^{1/2}·e^{πi zᵀ(CΩ+D)⁻¹Cz}·θ[m](z|Ω).
κ₀(γ), det(CΩ+D)^{1/2}, and the z-exp are CHARACTERISTIC-INDEPENDENT, so the ratio
    R(m) := θ[γ·m](ẑ | γ·Ω) / θ[m](z | Ω),   R(m)/R(0) = e^{2πi φ_m(γ)}
isolates the characteristic phase as an 8th root → k = round(8·φ_m) mod 8.

Verifies BOTH parts of the rc233 fix, g1..g4, across all standard generators and all
2^{2g} characteristics:
  (1) the corrected integer phase
        8·φ_m = −ε'ᵀ(DᵀB)ε' + 2·ε'ᵀ(BᵀC)ε − εᵀ(AᵀC)ε + 2·diag(A·Bᵀ)·(Dε'−Cε)
      matches θ[UNREDUCED γ·m]/θ[m];
  (2) the composition-consistent kexp = (8·φ_m + 4·Σ(p·b)) mod 8  (p = reduced upper,
      b = ⌊new_eps/2⌋) matches θ[REDUCED γ·m]/θ[m] — the value transform actually returns.

Run:  python3 theta_transform_multiplier_oracle_rc233.py
Literature anchor: arXiv:0801.2543 (D'Hoker–Phong) sha256
  e6edd3b217d138c20ff9e126e9801bb020042000736b0415d98297b164311797
"""
import cmath
import itertools

PI_I = 1j * cmath.pi
TWO_PI_I = 2j * cmath.pi


# ── minimal complex linear algebra ────────────────────────────────────────────────
def matmul(P, Q):
    g = len(P)
    return [[sum(P[i][k] * Q[k][j] for k in range(g)) for j in range(g)] for i in range(g)]


def matvec(P, v):
    return [sum(P[i][k] * v[k] for k in range(len(v))) for i in range(len(P))]


def transpose(P):
    g = len(P)
    return [[P[j][i] for j in range(g)] for i in range(g)]


def madd(P, Q):
    return [[P[i][j] + Q[i][j] for j in range(len(P))] for i in range(len(P))]


def inv(P):
    g = len(P)
    M = [[complex(P[i][j]) for j in range(g)] + [1.0 if i == j else 0.0 for j in range(g)]
         for i in range(g)]
    for col in range(g):
        piv = max(range(col, g), key=lambda r: abs(M[r][col]))
        M[col], M[piv] = M[piv], M[col]
        d = M[col][col]
        M[col] = [x / d for x in M[col]]
        for r in range(g):
            if r != col and M[r][col] != 0:
                f = M[r][col]
                M[r] = [M[r][k] - f * M[col][k] for k in range(2 * g)]
    return [row[g:] for row in M]


def diag_ABt(A, B):                      # diag(A·Bᵀ)_i = Σ_k A[i][k]·B[i][k]
    g = len(A)
    return [sum(A[i][k] * B[i][k] for k in range(g)) for i in range(g)]


def theta(mp, mpp, Om, z, box):
    g = len(Om)
    tot = 0j
    for n in itertools.product(range(-box, box + 1), repeat=g):
        u = [n[i] + mp[i] for i in range(g)]
        Ou = matvec(Om, u)
        quad = sum(u[i] * Ou[i] for i in range(g))
        lin = sum(u[i] * (z[i] + mpp[i]) for i in range(g))
        tot += cmath.exp(PI_I * quad + TWO_PI_I * lin)
    return tot


# ── shipped exact-integer formula (re-implemented here to CHECK it) ────────────────
def eight_phi(A, B, C, D, ep, e):
    g = len(A)
    DtB = matmul(transpose(D), B)
    BtC = matmul(transpose(B), C)
    AtC = matmul(transpose(A), C)
    t1 = -sum(ep[i] * DtB[i][j] * ep[j] for i in range(g) for j in range(g))
    t2 = 2 * sum(ep[i] * BtC[i][j] * e[j] for i in range(g) for j in range(g))
    t3 = -sum(e[i] * AtC[i][j] * e[j] for i in range(g) for j in range(g))
    Dep = matvec(D, ep); Ce = matvec(C, e)
    dab = diag_ABt(A, B)
    t4 = 2 * sum(dab[i] * (Dep[i] - Ce[i]) for i in range(g))
    return (t1 + t2 + t3 + t4) % 8


def transformed_char(A, B, C, D, ep, e):
    g = len(A)
    Dep = matvec(D, ep); Ce = matvec(C, e)
    Be = matvec(B, ep); Ae = matvec(A, e)
    new_epp = [Dep[i] - Ce[i] + diag_ABt(C, D)[i] for i in range(g)]
    new_eps = [-Be[i] + Ae[i] + diag_ABt(A, B)[i] for i in range(g)]
    return new_epp, new_eps


def kexp_composed(A, B, C, D, ep, e):
    """The composition-consistent exponent transform actually returns."""
    new_epp, new_eps = transformed_char(A, B, C, D, ep, e)
    fold = 4 * sum((new_epp[i] % 2) * (new_eps[i] // 2) for i in range(len(A)))
    return (eight_phi(A, B, C, D, ep, e) + fold) % 8


# ── standard generators + a dense composite, at each genus ────────────────────────
def I(g): return [[1 if i == j else 0 for j in range(g)] for i in range(g)]
def Z(g): return [[0] * g for _ in range(g)]
def negI(g): return [[-1 if i == j else 0 for j in range(g)] for i in range(g)]
def E00(g, v=1): return [[v if (i == 0 and j == 0) else 0 for j in range(g)] for i in range(g)]


def sp_compose(g2, g1):
    A2, B2, C2, D2 = g2; A1, B1, C1, D1 = g1
    return (madd(matmul(A2, A1), matmul(B2, C1)), madd(matmul(A2, B1), matmul(B2, D1)),
            madd(matmul(C2, A1), matmul(D2, C1)), madd(matmul(C2, B1), matmul(D2, D1)))


def generators(g):
    Ash = [[1 if i == j else (1 if (i == 0 and j == 1) else 0) for j in range(g)]
           for i in range(g)]
    Dsh = [[1 if i == j else (-1 if (i == 1 and j == 0) else 0) for j in range(g)]
           for i in range(g)]
    T1 = (I(g), E00(g, 1), Z(g), I(g))
    T2 = (I(g), E00(g, 2), Z(g), I(g))
    J = (Z(g), negI(g), I(g), Z(g))
    U = (Ash, Z(g), Z(g), Dsh)
    return {"transl_d1": T1, "transl_d2": T2, "inversion": J, "gl_shear": U,
            "composite": sp_compose(sp_compose(J, T1), U)}


def make_Om(g):
    Om = [[0j] * g for _ in range(g)]
    for i in range(g):
        for j in range(i, g):
            re = 0.13 * (i + 1) - 0.07 * (j + 1)
            im = (2.1 + 0.3 * i) if i == j else 0.11 * (i + 1) * (j + 1) / g
            Om[i][j] = re + im * 1j
            Om[j][i] = Om[i][j]
    return Om


def check_genus(g, box):
    Om = make_Om(g)
    z = [(0.05 * (i + 1) - 0.03) + (0.04 * (i + 1)) * 1j for i in range(g)]
    gens = generators(g)
    bad_phi = bad_fold = tot = 0
    seen = set()
    for name, (A, B, C, D) in gens.items():
        COmD = madd(matmul(C, Om), D)
        gOm = matmul(madd(matmul(A, Om), B), inv(COmD))
        zhat = matvec(transpose(inv(COmD)), z)
        hcd = [0.5 * x for x in diag_ABt(C, D)]
        hab = [0.5 * x for x in diag_ABt(A, B)]
        den0 = theta([0.0] * g, [0.0] * g, Om, z, box)
        num0 = theta([0.5 * x for x in hcd], [0.5 * x for x in hab], gOm, zhat, box)
        R0_un = num0 / den0
        # R0 for reduced target == unreduced here (char 0 stays 0)
        for bits in itertools.product((0, 1), repeat=2 * g):
            a = [bits[i] * 0.5 for i in range(g)]
            b = [bits[g + i] * 0.5 for i in range(g)]
            ep = list(bits[:g]); e = list(bits[g:])
            new_epp, new_eps = transformed_char(A, B, C, D, ep, e)
            # (1) unreduced target -> phi_m
            ahat = [0.5 * new_epp[i] for i in range(g)]
            bhat = [0.5 * new_eps[i] for i in range(g)]
            den = theta(a, b, Om, z, box)
            if abs(den) < 1e-9:
                continue
            num_un = theta(ahat, bhat, gOm, zhat, box)
            if abs(num_un) > 1e-9:
                k_un = round(8 * (cmath.phase((num_un / den) / R0_un) / (2 * cmath.pi))) % 8
                tot += 1
                if k_un != eight_phi(A, B, C, D, ep, e):
                    bad_phi += 1
            # (2) reduced target -> composition-consistent kexp
            ar = [0.5 * (new_epp[i] % 2) for i in range(g)]
            br = [0.5 * (new_eps[i] % 2) for i in range(g)]
            num_r = theta(ar, br, gOm, zhat, box)
            if abs(num_r) > 1e-9:
                k_r = round(8 * (cmath.phase((num_r / den) / R0_un) / (2 * cmath.pi))) % 8
                if k_r != kexp_composed(A, B, C, D, ep, e):
                    bad_fold += 1
                seen.add(k_r)
    print(f"genus {g}: phi_m matches {tot - bad_phi}/{tot}; "
          f"composed-kexp fold mismatches={bad_fold}; k-values seen={sorted(seen)}")
    return bad_phi == 0 and bad_fold == 0


if __name__ == "__main__":
    ok = all(check_genus(g, box) for g, box in ((1, 30), (2, 6), (3, 4), (4, 3)))
    print("\nRESULT:", "ALL GENERA VERIFIED (fix is exact)" if ok else "MISMATCH")

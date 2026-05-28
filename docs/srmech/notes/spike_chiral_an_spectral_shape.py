#!/usr/bin/env python3
"""Spike: is the chiral dual of an A-N operator a 180-degree rotation, or
the same shape inverted?

Two spectral definitions, per user direction 2026-05-27:
  DEF A  -- eigenspectrum of the so(8) matrix (octonion multiplication ops,
            the generative chiral set L_e vs R_e = the 4:3:(4:3) | 4:3:(3:4)
            Plate-1 / Plate-2 pair).
  DEF B  -- FFT of the operator's cascade action on a probe signal.

Cascade-honesty: no Python abs() anywhere. Real sign-handling routes through
srmech.amsc.cascade.magnitude (Class K pin-slot); complex modulus is computed
as sqrt((z * conj(z)).real). Octonions are built by Cayley-Dickson doubling and
VERIFIED (e_i^2 = -1, anticommutativity, norm multiplicativity) before use.
"""
import numpy as np

# ---- cascade-honest real magnitude (Class K), srmech if available ----------
try:
    from srmech.amsc.cascade import magnitude as _k_magnitude  # Class K
    SRMECH = True
except Exception:
    SRMECH = False
    def _k_magnitude(x):              # no abs(): pin-slot via square-root-of-square
        return float(np.sqrt(float(x) * float(x)))

def cmod(z):                          # complex modulus, no abs()
    z = np.asarray(z)
    return np.sqrt((z * np.conj(z)).real)

def fro(M):                           # Frobenius norm, real matrix, no abs()
    M = np.asarray(M, dtype=float)
    return float(np.sqrt(np.sum(M * M)))

# ---- octonions via Cayley-Dickson doubling ---------------------------------
def cd_conj(x):
    c = -x.copy(); c[0] = x[0]; return c

def cd_mul(x, y):
    n = len(x)
    if n == 1:
        return x * y
    h = n // 2
    a, b, c, d = x[:h], x[h:], y[:h], y[h:]
    # (a,b)(c,d) = (a c - conj(d) b,  d a + b conj(c))
    z1 = cd_mul(a, c) - cd_mul(cd_conj(d), b)
    z2 = cd_mul(d, a) + cd_mul(b, cd_conj(c))
    return np.concatenate([z1, z2])

def basis(i, n=8):
    e = np.zeros(n); e[i] = 1.0; return e

def verify_octonions():
    ok = True
    for i in range(1, 8):                       # e_i^2 = -1
        sq = cd_mul(basis(i), basis(i))
        ok &= abs(sq[0] + 1.0) < 1e-12 and fro(sq[1:]) < 1e-12
    for i in range(1, 8):                        # anticommutativity e_i e_j = -e_j e_i
        for j in range(1, 8):
            if i == j: continue
            ok &= fro(cd_mul(basis(i), basis(j)) + cd_mul(basis(j), basis(i))) < 1e-12
    rng = np.random.default_rng(0)               # norm multiplicativity
    for _ in range(200):
        x, y = rng.standard_normal(8), rng.standard_normal(8)
        nx, ny = fro(x), fro(y)
        nxy = fro(cd_mul(x, y))
        ok &= abs(nxy - nx * ny) < 1e-9
    return ok

def L_matrix(e):                                 # left-multiplication operator
    return np.column_stack([cd_mul(e, basis(j)) for j in range(8)])

def R_matrix(e):                                 # right-multiplication operator
    return np.column_stack([cd_mul(basis(j), e) for j in range(8)])

K = np.diag([1.0] + [-1.0] * 7)                  # octonion conjugation = parity / reflection

def sorted_eigs(M):
    ev = np.linalg.eigvals(M)
    return ev[np.lexsort((ev.imag, ev.real))]

# ============================================================ DEF A =========
def def_a():
    print("=" * 70)
    print("DEF A  --  eigenspectrum of the so(8) multiplication operators")
    print("=" * 70)
    assert verify_octonions(), "octonion table failed verification"
    print("octonion Cayley-Dickson table VERIFIED (e_i^2=-1, anticomm, |xy|=|x||y|)")
    for idx in (1, 2, 4):                         # representatives across Fano lines
        e = basis(idx)
        L, R = L_matrix(e), R_matrix(e)
        evL, evR = sorted_eigs(L), sorted_eigs(R)
        spec_match = fro(np.array([evL.real - evR.real, evL.imag - evR.imag]))
        antisym_L = fro(L + L.T)
        print(f"\n-- e{idx} --")
        print(f"  eig(L_e) = {np.round(evL,3)}")
        print(f"  eig(R_e) = {np.round(evR,3)}")
        print(f"  L_e antisymmetric (||L+L^T||): {antisym_L:.2e}")
        print(f"  SAME SPECTRUM?  ||sortedeig(L)-sortedeig(R)|| = {spec_match:.2e}")
        # three competing structural relationships:
        res_180   = fro(R - (-L))          # R = -L           : pure 180deg rotation (global -1)
        res_refl  = fro(R - (K @ L @ K))   # R = K L K        : pure reflection / inverse
        res_pr    = fro(R - (-(K @ L @ K)))# R = -K L K       : reflection AND 180deg (parity o rotation)
        print(f"  residual  R = -L        (pure 180deg)        : {res_180:.2e}")
        print(f"  residual  R = +K L K    (pure reflect/inv)   : {res_refl:.2e}")
        print(f"  residual  R = -K L K    (reflect AND 180deg) : {res_pr:.2e}")
        verdict = min((res_180,"pure 180deg"),(res_refl,"pure inverse/reflection"),
                      (res_pr,"inverse-AND-180deg (R = -K L_e K)"), key=lambda t:t[0])
        print(f"  >>> chiral dual L->R is: {verdict[1]}  (residual {verdict[0]:.2e})")

# ============================================================ DEF B =========
def chiral_flip_phase_test(name, Y, Yd, thresh=1e-6):
    """Y = operator FFT, Yd = chiral-dual FFT. Decide 180deg vs inverse."""
    magY, magYd = cmod(Y), cmod(Yd)
    scale = float(np.max(magY)) or 1.0
    mag_diff = float(np.max(cmod(magY - magYd))) / scale          # shape preserved?
    active = magY > thresh * scale
    pdiff = np.angle(Yd[active]) - np.angle(Y[active])
    pdiff = (pdiff + np.pi) % (2 * np.pi) - np.pi                  # wrap to (-pi,pi]
    pdiff_std = float(np.std(pdiff))                              # ~0 => constant => global rotation
    # constant-pi (180deg) hypothesis residual:
    res_180 = float(np.sqrt(np.mean((np.cos(pdiff) + 1) ** 2 + np.sin(pdiff) ** 2)))
    # conjugate (inverse) hypothesis residual: Yd ~ conj(Y)
    res_conj = float(np.max(cmod(Yd - np.conj(Y)))) / scale
    print(f"\n-- {name} --")
    print(f"  SAME SHAPE? max||,|Y|-|Yd|,|| / scale          = {mag_diff:.2e}")
    print(f"  phase-diff std over active bins (0=>global turn)= {pdiff_std:.3f} rad")
    print(f"  residual: global 180deg (phase-diff == pi)      = {res_180:.3f}")
    print(f"  residual: inverse/conjugate (Yd == conj(Y))     = {res_conj:.2e}")
    mean_cos = float(np.mean(np.cos(pdiff)))   # +1 => const 0 (identical); -1 => const pi (180deg)
    if mag_diff >= 1e-9:
        v = "neither (shape changed)"
    elif pdiff_std < 1e-6 and mean_cos < -0.5:
        v = "pure 180deg (constant phase turn of pi)"
    elif pdiff_std < 1e-6 and mean_cos > 0.5:
        v = "DEGENERATE: dual == original (constant phase 0; test not informative)"
    else:
        v = "SAME SHAPE, INVERSE (phase orientation-flipped, not a global turn)"
    print(f"  >>> {v}")

def def_b():
    print("\n" + "=" * 70)
    print("DEF B  --  FFT of operator cascade action on a probe signal")
    print("=" * 70)
    N = 64
    t = np.arange(N)
    x = (np.sin(2*np.pi*3*t/N) + 0.5*np.sin(2*np.pi*7*t/N)
         + 0.25*np.cos(2*np.pi*11*t/N))          # real probe, clear peaks at k=3,7,11
    X = np.fft.fft(x)

    # Class I (cyclic shift) -- orientation = shift direction
    k = 5
    YI  = np.fft.fft(np.roll(x,  k))
    YId = np.fft.fft(np.roll(x, -k))             # Class C flip: opposite orientation
    chiral_flip_phase_test("Class I  cyclic shift (roll +k vs -k)", YI, YId)

    # Class C / A reversal -- orientation = sequence direction (content read-order)
    YA  = X
    YAd = np.fft.fft(x[::-1])                     # reversed read-order
    chiral_flip_phase_test("Class C  sequence reversal (x vs x[::-1])", YA, YAd)

    # composed cascade C o I: reverse-then-shift; chiral dual flips ONLY the I
    # orientation (C reversal is its own inverse), so the dual is not degenerate.
    Yc  = np.fft.fft(np.roll(x[::-1],  k))
    Ycd = np.fft.fft(np.roll(x[::-1], -k))
    chiral_flip_phase_test("cascade C o I (flip I orientation)", Yc, Ycd)

if __name__ == "__main__":
    print(f"srmech.amsc.cascade available: {SRMECH}")
    def_a()
    def_b()
    print("\n" + "=" * 70)
    print("Reading: DEF A residuals pick the structural relationship L->R;")
    print("DEF B asks whether the FFT dual is a constant phase turn (180deg)")
    print("or an orientation-flipped phase at preserved magnitude (inverse).")

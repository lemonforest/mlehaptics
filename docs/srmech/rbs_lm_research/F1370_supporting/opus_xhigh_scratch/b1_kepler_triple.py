"""B1 - Kepler E(M) read through distributional x relational x responsion; rates per index direction.

srmech ops: srmech.math.qmat.QMat (exact integer matrix powers on the harmonic graph),
srmech.music.bessel_j_fixed (Kapteyn radii), srmech.math.kepler.kepler_solve (truth),
srmech.calculus sin/exp/sqrt (Q61 exact rationals, read as float), srmech.amsc.format.sha256_bytes.
HAND-ROLLED (disclosed): the Kapteyn ascending-series lattice c_{p,k} in Fraction (validated against
bessel_j_fixed in part 0, exactly as opus_scratch/s1_lattice.py did); the 64-point M grid and sup-norm;
bisection for the Laplace limit; ratio-based rate estimators.
"""
import sys, math, time
from fractions import Fraction as F
sys.path.insert(0, "D:/GitHub/mlehaptics/docs/srmech/python")
import srmech
from srmech import _native
from srmech.amsc.format import sha256_bytes
from srmech.math.qmat import QMat
from srmech.music import bessel_j_fixed
from srmech.math import kepler
from srmech.math import rational as R
from srmech import calculus as C

HERE = "C:/Users/sckir/AppData/Local/Temp/claude/D--GitHub-mlehaptics/623ea061-948c-4282-968d-ca4179875bf2/scratchpad/infinity_research/followup/opus_xhigh_scratch/"
print("srmech", srmech.__version__, srmech.__file__, "HAS_NATIVE", _native.HAS_NATIVE)
print("preregistration sha256:", sha256_bytes(open(HERE + "b0_preregistration.txt", "rb").read()))


def kapteyn(p, k):
    """coefficient of e^p sin(kM) in E - M; zero off the support."""
    if k < 1 or k > p or (p - k) % 2:
        return F(0)
    m = (p - k) // 2
    return F((-1) ** m * 2 * k ** (2 * m + k),
             k * 2 ** (2 * m + k) * math.factorial(m) * math.factorial(m + k))


def qf(x):
    return F(x.numerator, x.denominator)


# ---- part 0: instrument check ------------------------------------------------------------
print("\n(0) lattice column sums vs srmech bessel_j_fixed at e = 3/5 (p <= 300)")
for k in range(1, 7):
    col = sum(kapteyn(p, k) * F(3, 5) ** p for p in range(k, 301))
    num, den = bessel_j_fixed(k, 3 * k, 5)
    print(f"  k={k} |lattice - (2/k)J_k(ke)| = {float(abs(col - F(2, k) * F(num, den))):.1e}")

# ---- part 1: the lattice factorises as signed walk count x eigenvalue power ---------------
P = 16
N = 2 * P + 1
Hrows = [[0] * N for _ in range(N)]
Arows = [[0] * N for _ in range(N)]
Drows = [[0] * N for _ in range(N)]
for j in range(N):
    Drows[j][j] = j - P
    if j + 1 < N:
        Hrows[j + 1][j] = 1          # S : harmonic j -> j+1
        Arows[j + 1][j] = 1
    if j - 1 >= 0:
        Hrows[j - 1][j] = -1         # -S^{-1}
        Arows[j - 1][j] = 1
H = QMat.from_rows(Hrows)
A = QMat.from_rows(Arows)
D = QMat.from_rows(Drows)
print("\n(1) hop operator H = S - S^-1 and unsigned adjacency A = S + S^-1 on harmonics -16..16 (QMat exact)")
Hp, Ap = QMat.identity(N), QMat.identity(N)
mism = supp_bad = checked = 0
for p in range(1, P + 1):
    Hp = Hp @ H
    Ap = Ap @ A
    Hl, Al = Hp.to_lists(), Ap.to_lists()
    for k in range(0, P + 1):
        w = qf(Hl[k + P][P])
        a = qf(Al[k + P][P])
        lat = kapteyn(p, k)
        rhs = w * F(k) ** (p - 1) / (2 ** (p - 1) * math.factorial(p)) if k >= 1 else F(0)
        checked += 1
        if lat != rhs:
            mism += 1
        in_cone = (k <= p) and ((p - k) % 2 == 0)
        if (a != 0) != in_cone:
            supp_bad += 1
print(f"  cells checked (1<=p<={P}, 0<=k<={P}): {checked}")
print(f"  c(p,k) == [H^p]_(k,0) * k^(p-1) / (2^(p-1) p!) : mismatches = {mism}")
print(f"  support of [A^p]_(k,0) == cone {{k<=p, k=p mod 2}} : disagreements = {supp_bad}")
print("  k = 0 column: walk count nonzero for even p, lattice zero; the factor k^(p-1) = 0 removes it (p >= 2)")
comm = (D @ H) - (H @ D) if hasattr(QMat, '__sub__') else None
if comm is None:
    DH, HD = (D @ H).to_lists(), (H @ D).to_lists()
    comm_l = [[qf(DH[i][j]) - qf(HD[i][j]) for j in range(N)] for i in range(N)]
else:
    comm_l = [[qf(x) for x in row] for row in comm.to_lists()]
Al1 = [[F(x) for x in row] for row in Arows]
print("  commutator [D, H] == A (D = diag(harmonic index)):", comm_l == Al1,
      "  -> D and H do not commute, so they have no common eigenbasis")

# ---- part 3: rates per index direction ---------------------------------------------------
pi_s = R.pi_chudnovsky_digits(30)
PI = float(F(int(pi_s.replace('.', '')), 10 ** len(pi_s.split('.')[1])))


def sinf(x):
    return float(C.sin(x))


def expf(x):
    return float(C.exp(x))


def sqrtf(x):
    return float(C.sqrt(x))


# Laplace limit by bisection on g(x) = x exp(sqrt(1+x^2)) - (1 + sqrt(1+x^2))
lo, hi = 0.5, 0.8
for _ in range(60):
    mid = (lo + hi) / 2
    s = sqrtf(1 + mid * mid)
    if mid * expf(s) - (1 + s) > 0:
        hi = mid
    else:
        lo = mid
rL = (lo + hi) / 2
print(f"\n(3) Laplace limit r_L (bisection, srmech exp/sqrt) = {rL:.12f}   1/r_L = {1 / rL:.9f}")

# e-order coefficients at M = pi/2, where sin(k pi/2) is exact
print("  root test |a_p|^(1/p) at M = pi/2 (a_p = sum_k c(p,k) sin(k pi/2), exact Fractions):")
ap = {}
for p in range(1, 202, 2):
    ap[p] = sum(kapteyn(p, k) * (1 if (k - 1) % 4 == 0 else -1) for k in range(1, p + 1, 2))
for p in (21, 51, 101, 151, 201):
    lg = (math.log(abs(ap[p].numerator)) - math.log(ap[p].denominator)) / p
    print(f"    p={p:3d}: |a_p|^(1/p) = {math.exp(lg):.6f}")

grid = [(j + 0.5) * PI / 64 for j in range(64)]


def depth_rate(e, nmax):
    truth = [kepler.kepler_solve(M, e, tolerance=1e-15, max_iter=200) for M in grid]
    res = max(abs(t - e * sinf(t) - M) for t, M in zip(truth, grid))
    E = list(grid)
    errs = []
    for n in range(1, nmax + 1):
        E = [M + e * sinf(x) for x, M in zip(E, grid)]
        errs.append(max(abs(x - t) for x, t in zip(E, truth)))
    use = [i for i in range(1, len(errs)) if errs[i] > 1e-11 and errs[i - 1] > 1e-11]
    tail = use[-8:]
    rate = sum(errs[i] / errs[i - 1] for i in tail) / len(tail)
    return rate, res, errs


def mode_ratio(e, ks):
    num, den = e.numerator, e.denominator
    out = {}
    for k in ks:
        a = F(*bessel_j_fixed(k, k * num, den)) * F(2, k)
        b = F(*bessel_j_fixed(k + 1, (k + 1) * num, den)) * F(2, k + 1)
        out[k] = float(b / a)
    return out


def eorder_rate(e, pmax):
    Et = kepler.kepler_solve(PI / 2, float(e), tolerance=1e-15, max_iter=200)
    S = F(0)
    errs = {}
    for p in range(1, pmax + 1, 2):
        S += ap[p] * e ** p
        errs[p] = abs(PI / 2 + float(S) - Et)
    return errs


rows = []
for e in (F(1, 10), F(3, 10), F(1, 2), F(3, 5), F(7, 10), F(9, 10)):
    t0 = time.time()
    ef = float(e)
    nmax = {0.1: 20, 0.3: 30, 0.5: 45, 0.6: 60, 0.7: 80, 0.9: 260}[ef]
    dr, res, derr = depth_rate(ef, nmax)
    mr = mode_ratio(e, (10, 20, 40, 60))
    s = sqrtf(1 - ef * ef)
    rho = ef * expf(s) / (1 + s)
    eo = eorder_rate(e, 61)
    ps = sorted(eo)
    ratios = [(eo[ps[i]] / eo[ps[i - 1]]) ** 0.5 for i in range(len(ps) - 6, len(ps)) if eo[ps[i - 1]] > 1e-13 and eo[ps[i]] > 1e-13]
    eor = sum(ratios) / len(ratios) if ratios else float('nan')
    rows.append((ef, dr, mr[60], rho, eor, ef / rL))
    print(f"\n  e = {e}: truth residual max {res:.1e}")
    print(f"    depth (sup over 64-point M grid): measured step ratio {dr:.6f}   [DERIVED e = {ef}]   err@n={nmax}: {derr[-1]:.2e}")
    print(f"    modes: r(k+1)/r(k) at k=10,20,40,60: " + " ".join(f"{mr[k]:.6f}" for k in (10, 20, 40, 60)) + f"   [rho(e) = {rho:.6f}]")
    print(f"    e-order at M=pi/2: per-order ratio (err(p)/err(p-2))^(1/2), last window: {eor:.6f}   [e/r_L = {ef / rL:.6f}]"
          f"   err@p=61: {eo[61]:.2e}   ({time.time() - t0:.0f}s)")

print("\n(4) direction table: rate per index step; log-ratios (float, so UNDECIDED as verdicts)")
print("    e     depth   modes(rho)  e-order(e/r_L)  log(depth)/log(rho)  log(depth)/log(e/r_L)")
for ef, dr, m60, rho, eor, er in rows:
    lr2 = math.log(ef) / math.log(er) if er < 1 else float('nan')
    print(f"   {ef:.2f}  {dr:.4f}   {rho:.4f}      {er:.4f}{'(DIV)' if er >= 1 else '     '}      {math.log(ef) / math.log(rho):.6f}            {lr2:.6f}")
print("\n    exact cells after a budget B: depth B -> #{(p,k): k<=p<=B, parity} ; modes B -> every p (unbounded)")
for B in (4, 8, 16):
    print(f"      B={B}: depth exact cells {sum((p + 1) // 2 for p in range(1, B + 1))}; modes exact cells: all p >= 1 in columns k<=B")

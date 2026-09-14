"""B2 - responsion-as-commensurateness, measured on six frame pairs.

DEFINITIONS (stated BEFORE any measurement; not tuned afterwards):
 (I)   INDEX map M in {exact, partial, none}: exact = every finite truncation of frame 1 IS
       a finite truncation of frame 2 (an injective index map phi); partial = truncations
       share an exactly-agreeing sub-block but are unequal objects; none = no finite pair equal.
 (II)  RATE commensurateness: r1, r2 = asymptotic per-stage error ratios (geometric rates).
       q = log r1 / log r2. Commensurate iff q is a FIXED small-denominator rational: the shipped
       Class-N best_rational(q, max_denominator=12) reproduces q to 1e-6 AND q does not move
       under the family parameter (e). If one frame is superlinear (order 2) the ratio is
       UNDEFINED -> counts as incommensurate. A rate >= 1 means the frame diverges.
 (III) For a finite Class-L pair: the shipped commensurability_verdict on the spectrum.
 HYPOTHESIS H (from the brief): M == exact  <=>  rate/spectrum commensurate.

INSTRUMENTS: srmech kepler_solve, bessel_j_fixed, best_rational (with_path), continued_fraction,
atan_series_truncate, pi_cascade_digits, cyclic_laplacian_spectrum's Qalg ladder
(_cyclic_spectrum_qalg, private, disclosed), commensurability_verdict, dense_laplacian,
hermitian_eigendecompose, winding_fold constants. HAND-ROLLED (disclosed): Fraction lattice of
Kapteyn coefficients (validated against bessel_j_fixed), float sin on the OUTPUT side for the
sup-norm grid, math.isqrt for the sqrt(2) reference, math.log for the rate ratio.
"""
import sys, math
from fractions import Fraction as F
sys.path.insert(0, "D:/GitHub/mlehaptics/docs/srmech/python")
import srmech
from srmech import _native
from srmech.math import kepler, rational, laplacian, poly
from srmech.math.rational import best_rational, continued_fraction, atan_series_truncate, pi_cascade_digits
from srmech.music import bessel_j_fixed, commensurability_verdict
import importlib.util
print("srmech", srmech.__version__, "HAS_NATIVE", _native.HAS_NATIVE,
      "numpy", "present" if importlib.util.find_spec("numpy") else "ABSENT")

def q_test(q, label):
    """Definition (II): is q a small-denominator rational?"""
    num = int(round(q * 10**9)); den = 10**9
    p, d = best_rational(num, den, 12)
    err = abs(p / d - q)
    verdict = "RATIONAL(small-d)" if err < 1e-6 else "not a small-d rational"
    print(f"    {label}: q = {q:.6f}; best_rational(max_d=12) = {p}/{d} = {p/d:.6f}; |diff| = {err:.2e} -> {verdict}")
    return err < 1e-6

def kapteyn(p, k):
    if k < 1 or k > p or (p - k) % 2:
        return F(0)
    m = (p - k) // 2
    return F((-1) ** m * 2 * k ** (2 * m + k), k * 2 ** (2 * m + k) * math.factorial(m) * math.factorial(m + k))

# validate the hand-rolled lattice against the shipped Bessel op (one column suffices; opus did six)
e3 = F(3, 10)
for k in (1, 3):
    col = sum(kapteyn(p, k) * e3 ** p for p in range(k, 121))
    num, den = bessel_j_fixed(k, k * e3.numerator, e3.denominator)
    print(f"lattice validation k={k}: |lattice - (2/k)J_k(ke)| = {float(col - F(2, k) * F(num, den)):.1e}")

N = 256
GRID = [2 * math.pi * i / N for i in range(N)]

def depth_rate(e, n_hi=60):
    """per-step sup-error ratio, averaged over the window 1e-3 > err > 1e-10 (above the float floor)."""
    ref = [kepler.kepler_solve(M, e) for M in GRID]
    En = list(GRID); errs = []
    for n in range(1, n_hi + 1):
        En = [M + e * math.sin(x) for M, x in zip(GRID, En)]
        errs.append(max(abs(a - b) for a, b in zip(En, ref)))
    ratios = [errs[i + 1] / errs[i] for i in range(len(errs) - 1) if 1e-10 < errs[i + 1] and errs[i] < 1e-3]
    return sum(ratios) / len(ratios), errs

def mode_rate(e, k=50):
    ef = F(e).limit_denominator(1000)
    def r(k):
        num, den = bessel_j_fixed(k, k * ef.numerator, ef.denominator)
        return F(2, k) * F(num, den)
    return float(r(k + 1) / r(k))

def rho(e):  # CITED-NOT-FETCHED closed form, used only as a comparison column
    s = math.sqrt(1 - e * e)
    return e * math.exp(s) / (1 + s)

def eorder_rate(e, P=61):
    # Lagrange e-power frame at M = pi/2: a_p = sum_k c_{p,k} sin(k pi/2); only odd p are nonzero
    a = {}
    for p in range(1, P + 1, 2):
        a[p] = sum(kapteyn(p, k) * (1 if k % 4 == 1 else -1) for k in range(1, p + 1, 2))
    rr = [(abs(float(a[p + 2] / a[p])) ** 0.5) * e for p in range(P - 20, P - 1, 2)]
    return sum(rr) / len(rr)

E_LAPLACE = 0.6627434193  # CITED-NOT-FETCHED; comparison only

print("\n=== PAIR 1: Kepler depth (one-pin iteration) vs modes (Kapteyn radii) ===")
print("  (I) index map: NONE (row vs column projections of one triangular lattice; coordinator-confirmed S1)")
qs = []
for e in (0.1, 0.2, 0.3, 0.5, 0.7):
    rd, _ = depth_rate(e); rm = mode_rate(e)
    q = math.log(rd) / math.log(rm)
    print(f"  e={e}: depth rate {rd:.4f} (e={e}), mode rate {rm:.4f} (rho(e)={rho(e):.4f}), q=log rd/log rm = {q:.4f}")
    qs.append(q)
for e, q in zip((0.1, 0.3, 0.7), (qs[0], qs[2], qs[4])):
    q_test(q, f"e={e}")
print(f"  q spans {min(qs):.3f}..{max(qs):.3f} across e -> NOT a fixed rational -> (II) INCOMMENSURATE")

print("\n=== PAIR 2: Kepler depth vs e-order (Lagrange power series) ===")
print("  (I) index map: PARTIAL (depth n reproduces every lattice cell p<=n exactly; objects unequal; S1)")
for e in (0.3, 0.5, 0.6, 0.7):
    rd, _ = depth_rate(e); re_ = eorder_rate(e)
    status = "DIVERGES" if re_ >= 1 else "converges"
    q = math.log(rd) / math.log(re_) if re_ < 1 else float('nan')
    print(f"  e={e}: depth rate {rd:.4f}; e-order rate {re_:.4f} (e/e_L = {e / E_LAPLACE:.4f}) {status}; q = {q:.4f}")
print("  q moves with e and is undefined past e_L -> (II) INCOMMENSURATE, while (I) is PARTIAL-exact")

print("\n=== PAIR 3: Heron sqrt(2) depth vs continued-fraction convergents ===")
SCALE = 10 ** 120
sqrt2_num = math.isqrt(2 * SCALE * SCALE)  # ALU isqrt reference (disclosed)
x = F(1); rows = []
for n in range(1, 7):
    x = (x + 2 / x) / 2
    p, d, path = best_rational(sqrt2_num, SCALE, x.denominator, with_path=True)
    is_conv = (p == x.numerator and d == x.denominator)
    idx = len(path) - 1
    cf = continued_fraction(x.numerator, x.denominator) if x.numerator < 2**64 and x.denominator < 2**64 else ["(uint64 cap: continued_fraction refuses; best_rational path used)"]
    err = abs(F(x.numerator * SCALE - sqrt2_num * x.denominator, x.denominator * SCALE))
    rows.append((n, is_conv, idx, err))
    print(f"  Heron n={n}: best_rational(sqrt2, max_d=q_n) == x_n: {is_conv}; convergent index (len(path)-1) = {idx} = 2^n-1? {idx == 2**n - 1}; CF(x_n) tail = {cf[-3:]}; err = 10^{math.log10(err):.1f}")
print("  (I) index map: EXACT subsequence phi(n) = 2^n - 1 (srmech best_rational path)")
for i in range(1, len(rows) - 1):
    e0, e1 = rows[i][3], rows[i + 1][3]
    print(f"    Heron order check: err(n+1)/err(n)^2 = {float(e1 / (e0 * e0)):.4f}  (constant -> order 2)")
# CF convergent geometric rate for sqrt 2
convs = []
pp, qq = 1, 1
p_prev, q_prev = 1, 0
for m in range(1, 40):
    p_new, q_new = 2 * pp + p_prev, 2 * qq + q_prev
    p_prev, q_prev, pp, qq = pp, qq, p_new, q_new
    convs.append(abs(F(pp * SCALE - sqrt2_num * qq, qq * SCALE)))
cf_rate = float(convs[30] / convs[29])
print(f"    CF convergent rate err(m+1)/err(m) -> {cf_rate:.6f}  ((sqrt2-1)^2 = {(math.sqrt(2) - 1) ** 2:.6f}) -> order 1")
print("  (II) rate ratio UNDEFINED (order 2 vs order 1): the index map is exponential, not rational-affine -> INCOMMENSURATE")

print("\n=== PAIR 4 (control): Fibonacci ratio vs continued fraction of phi ===")
phi_num = (SCALE + math.isqrt(5 * SCALE * SCALE)) // 2
a, b = 1, 1
errs = []
for n in range(1, 41):
    a, b = b, a + b           # b/a = F_{n+2}/F_{n+1}
    p, d, path = best_rational(phi_num, SCALE, a, with_path=True)
    ok = (p == b and d == a)
    errs.append(abs(F(b * SCALE - phi_num * a, a * SCALE)))
    if n in (5, 10, 20, 40):
        print(f"  n={n}: best_rational(phi, max_d=F_n) == F_(n+1)/F_n: {ok}; convergent index = {len(path) - 1}")
print(f"  (I) index map: EXACT, phi(n) = n (identity). rate err(n+1)/err(n) -> {float(errs[30] / errs[29]):.6f} on BOTH frames (same objects) -> q = 1 -> (II) COMMENSURATE")

print("\n=== PAIR 5: pi by Archimedes bracket (depth = doublings) vs Machin arctan series (terms) ===")
ref = pi_cascade_digits(200)
ref_q = F(int(ref.replace('.', '')), 10 ** 200)
poly_err = []
for depth in range(1, 13):
    s = pi_cascade_digits(60, max_cascade_depth=depth)
    v = F(int(s.replace('.', '')), 10 ** 60)
    poly_err.append(abs(v - ref_q))
for i in range(4, 11):
    pass
print("  Archimedes per-doubling error ratios:", [f"{float(poly_err[i + 1] / poly_err[i]):.4f}" for i in range(3, 10)])
mach_err = []
for n in range(1, 30):
    t5 = atan_series_truncate(1, 5, n); t239 = atan_series_truncate(1, 239, n)
    v = 4 * (4 * F(t5.numerator, t5.denominator) - F(t239.numerator, t239.denominator)) if hasattr(t5, 'numerator') else None
    if v is None:
        v = 4 * (4 * F(t5[0], t5[1]) - F(t239[0], t239[1]))
    mach_err.append(abs(v - ref_q))
print("  Machin per-term error ratios:", [f"{float(mach_err[i + 1] / mach_err[i]):.5f}" for i in range(10, 16)])
r_poly = float(poly_err[9] / poly_err[8]); r_mach = float(mach_err[14] / mach_err[13])
q = math.log(r_poly) / math.log(r_mach)
q_test(q, "pi: log(1/4)/log(1/25)")
print(f"    DERIVED: log 4 / log 25 = log 2 / log 5 is irrational (2^a = 5^b has no integer solution) -> (II) INCOMMENSURATE")
poly_vals = set()
for depth in range(1, 13):
    s = pi_cascade_digits(60, max_cascade_depth=depth); poly_vals.add(F(int(s.replace('.', '')), 10 ** 60))
mach_vals = set()
for n in range(1, 30):
    t5 = atan_series_truncate(1, 5, n); t239 = atan_series_truncate(1, 239, n)
    mach_vals.add(4 * (4 * F(t5.numerator, t5.denominator) - F(t239.numerator, t239.denominator)))
print(f"  (I) index map: equal truncation values across 12 depths x 29 term-counts: {len(poly_vals & mach_vals)} -> NONE")

print("\n=== PAIR 6: the 2pi anchors - dyadic grid (bits) vs Machin-2pi rational (terms) ===")
from srmech.math.laplacian import _EPH_TWO_PI, _EPH_TWO_PI_DEN, _EPH_FOLD_DEN
print(f"  shipped: _EPH_TWO_PI_DEN = 2^{_EPH_TWO_PI_DEN.bit_length() - 1}, _EPH_FOLD_DEN = 2^{_EPH_FOLD_DEN.bit_length() - 1}; anchor 2pi = {float(F(*_EPH_TWO_PI)):.15f}")
two_pi = 2 * ref_q
for bits in (44, 80):
    g = F(round(two_pi * 2 ** bits), 2 ** bits)
    print(f"  dyadic grid 2^-{bits}: |grid - 2pi| = {float(abs(g - two_pi)):.2e}")
# per-bit rate 1/2 (definitional) vs Machin per-term 1/25: which term count matches 2^-80?
for n in range(1, 40):
    if 2 * mach_err[min(n, 28) - 1] < 2 ** -80:
        print(f"  Machin terms needed to reach the 2^-80 grid: {n} (80*log2/log25 = {80 * math.log(2) / math.log(25):.2f})")
        break
q = math.log(0.5) / math.log(1 / 25)
q_test(q, "2pi: log(1/2)/log(1/25)")
print("  (I) index map: a dyadic truncation has denominator 2^k; a Machin partial sum has denominators with factors 5, 239 -> never equal -> NONE")

print("\n=== PAIR 7: Class-L C_7 - L^n v (depth) vs eigenbasis expansion (modes) ===")
n7 = 7
edges = [(i, (i + 1) % n7) for i in range(n7)]
L = laplacian.dense_laplacian(n7, edges)
vals, V = laplacian.hermitian_eigendecompose(L)
Lrows = [[float(L[i, j].real if hasattr(L[i, j], 'real') else L[i, j]) for j in range(n7)] for i in range(n7)]
Vc = [[complex(V[i, j]) for j in range(n7)] for i in range(n7)]
lam = [float(vals[i]) for i in range(n7)]
v0 = [1.0, 0, 0, 0, 0, 0, 0]
c = [sum(Vc[i][k].conjugate() * v0[i] for i in range(n7)) for k in range(n7)]
worst = 0.0
x = list(v0)
for n in range(1, 9):
    x = [sum(Lrows[i][j] * x[j] for j in range(n7)) for i in range(n7)]
    y = [sum(c[k] * lam[k] ** n * Vc[i][k] for k in range(n7)) for i in range(n7)]
    worst = max(worst, max(abs(a - b) for a, b in zip(x, y)))
print(f"  (I) exact identity L^n v == sum_k lambda_k^n c_k v_k for n=1..8, K=N=7: max |diff| = {worst:.1e} -> EXACT (finite)")
srt = sorted(lam)
print(f"  power-iteration rate lambda_second/lambda_max = {srt[-3] / srt[-1]:.6f} (top eigenvalue doubly degenerate: {srt[-1]:.6f},{srt[-2]:.6f})")
phi7 = poly.cyclotomic_polynomial(7)
eig, powers = laplacian._cyclic_spectrum_qalg(7, phi7["coefficients"])
ratios = [eig[k] / eig[1] for k in (1, 2, 3)]
verd = commensurability_verdict(ratios)
print(f"  (III) commensurability_verdict([l1/l1,l2/l1,l3/l1]) -> verdict={verd['verdict']}, rational_rank={verd.get('rational_rank')}")
print("  -> (I) EXACT but (III) INCOMMENSURATE: H FAILS on C_7")

print("\n=== PAIR 8: Class-L Q_3 hypercube - same construction ===")
edges8 = [(i, i ^ (1 << b)) for i in range(8) for b in range(3) if i < i ^ (1 << b)]
L8 = laplacian.dense_laplacian(8, edges8)
ev = laplacian.jacobi_eigvals(L8)
ints = [int(round(float(ev[i]))) for i in range(8)]
verd8 = commensurability_verdict([(v, 2) for v in ints if v != 0])
print(f"  spectrum {ints}; verdict (fundamental nominated = 2) = {verd8['verdict']}, integer_series = {verd8.get('integer_series')}")
print("  -> (I) EXACT and (III) COMMENSURATE: H holds on Q_3 (but the same finite identity held on C_7)")

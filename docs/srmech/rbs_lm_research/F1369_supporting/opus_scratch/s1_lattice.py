"""S1 - exact (e-order p, harmonic k) coefficient lattice of Kepler's E(M)-M.

INSTRUMENT (hand-rolled, disclosed): truncated bivariate series in e whose coefficients are
trig polynomials in M, Fraction arithmetic throughout. Reference lattice = Kapteyn/Bessel
ascending series (formula disclosed below; VALIDATED here against srmech.music.bessel_j_fixed).
Kepler reference values = srmech.math.kepler.kepler_solve (pure cell).
"""
import sys, math
from fractions import Fraction as F
sys.path.insert(0, "D:/GitHub/mlehaptics/docs/srmech/python")
import srmech
from srmech import _native
from srmech.math import kepler
from srmech.music import bessel_j_fixed
print("srmech", srmech.__version__, "HAS_NATIVE", _native.HAS_NATIVE)

def kapteyn(p, k):
    """coefficient of e^p sin(kM) in E-M = sum_k (2/k) J_k(ke) sin kM,
    J_k(x) = sum_m (-1)^m (x/2)^(2m+k) / (m! (m+k)!)   (ascending series)."""
    if k < 1 or k > p or (p - k) % 2:
        return F(0)
    m = (p - k) // 2
    return F((-1) ** m * 2 * k ** (2 * m + k),
             k * 2 ** (2 * m + k) * math.factorial(m) * math.factorial(m + k))

# --- (0) validate the lattice against srmech's own Bessel op -------------------------
print("\n(0) lattice column sums vs srmech bessel_j_fixed, e = 3/10")
e = F(3, 10)
for k in range(1, 7):
    col = sum(kapteyn(p, k) * e ** p for p in range(k, 121))
    num, den = bessel_j_fixed(k, k * e.numerator, e.denominator)
    r = F(2, k) * F(num, den)
    print(f"  k={k}  lattice(p<=120)={float(col):.15e}  srmech={float(r):.15e}  diff={float(col - r):.1e}")

# --- (1) depth-n cascade jets vs the exact lattice -----------------------------------
P = 9
def norm(p, kind, k, v, out):
    if kind == 's':
        if k == 0:
            return
        if k < 0:
            k, v = -k, -v
    elif k < 0:
        k = -k
    out[(p, kind, k)] = out.get((p, kind, k), 0) + v

def clean(d):
    return {key: v for key, v in d.items() if v != 0}

def add(a, b):
    r = dict(a)
    for key, v in b.items():
        r[key] = r.get(key, 0) + v
    return clean(r)

def mul(a, b):
    out = {}
    for (p1, t1, k1), v1 in a.items():
        for (p2, t2, k2), v2 in b.items():
            p = p1 + p2
            if p > P:
                continue
            h = v1 * v2 / 2
            if t1 == 'c' and t2 == 'c':
                norm(p, 'c', k1 - k2, h, out); norm(p, 'c', k1 + k2, h, out)
            elif t1 == 's' and t2 == 's':
                norm(p, 'c', k1 - k2, h, out); norm(p, 'c', k1 + k2, -h, out)
            elif t1 == 's':
                norm(p, 's', k1 + k2, h, out); norm(p, 's', k1 - k2, h, out)
            else:
                norm(p, 's', k1 + k2, h, out); norm(p, 's', k1 - k2, -h, out)
    return clean(out)

ONE = {(0, 'c', 0): F(1)}
SINM = {(0, 's', 1): F(1)}
COSM = {(0, 'c', 1): F(1)}

def sin_of_M_plus(d):
    powd, cosd, sind = ONE, dict(ONE), {}
    for j in range(1, P + 1):
        powd = mul(powd, d)
        if not powd:
            break
        c = F((-1) ** (j // 2), math.factorial(j))
        term = {key: v * c for key, v in powd.items()}
        if j % 2:
            sind = add(sind, term)
        else:
            cosd = add(cosd, term)
    return add(mul(SINM, cosd), mul(COSM, sind))

print(f"\n(1) depth-n one-pin cascade E_(n+1) = M + e sin E_n, exact jets to e^{P}, vs Kapteyn lattice")
delta = {}
for n in range(1, P + 1):
    s = sin_of_M_plus(delta)
    delta = clean({(p + 1, t, k): v for (p, t, k), v in s.items() if p + 1 <= P})
    cos_terms = [key for key in delta if key[1] == 'c']
    bad = []
    for p in range(1, P + 1):
        for k in range(0, P + 1):
            got = delta.get((p, 's', k), F(0))
            if got != kapteyn(p, k):
                bad.append((p, k, got, kapteyn(p, k)))
    agree_through = (min(b[0] for b in bad) - 1) if bad else P
    first = sorted(bad)[:3]
    ks_beyond = sorted({k for (p, t, k) in delta if p > n})
    print(f"  depth {n}: all lattice cells with p <= {agree_through} EXACT; cos-terms {len(cos_terms)};"
          f" first mismatches {[(b[0], b[1], str(b[2]), str(b[3])) for b in first]}; harmonics present at orders > n: {ks_beyond}")

# --- (2) Laplace-limit check: the e-power (jet) frame at M = pi/2 --------------------
print("\n(2) e-power frame at M = pi/2: a_p = sum_k c_{p,k} sin(k pi/2); root test and partial sums")
PMAX = 121
a = {}
b = {}
for p in range(1, PMAX + 1):
    a[p] = sum(kapteyn(p, k) * (0 if k % 2 == 0 else (1 if k % 4 == 1 else -1)) for k in range(1, p + 1))
    b[p] = sum((kapteyn(p, k) if kapteyn(p, k) >= 0 else -kapteyn(p, k)) for k in range(1, p + 1))
for p in (21, 41, 61, 81, 101, 121):
    ap = a[p] if a[p] >= 0 else -a[p]
    print(f"  p={p:3d}  |a_p|^(-1/p) = {float(ap) ** (-1.0 / p):.6f}   (sum_k|c_pk|)^(-1/p) = {float(b[p]) ** (-1.0 / p):.6f}")
def lap(x):
    s = math.sqrt(1 + x * x)
    return x * math.exp(s) / (1 + s) - 1
lo, hi = 0.5, 0.8
for _ in range(80):
    mid = (lo + hi) / 2
    lo, hi = (mid, hi) if lap(mid) < 0 else (lo, mid)
print(f"  root of x*exp(sqrt(1+x^2))/(1+sqrt(1+x^2)) = 1 (CITED-NOT-FETCHED Laplace-limit formula): {lo:.10f}")
for ef in (F(3, 5), F(13, 20), F(7, 10)):
    ref = kepler.kepler_solve(math.pi / 2, float(ef)) - math.pi / 2
    row = []
    for PP in (25, 51, 81, 121):
        sp = sum(a[p] * ef ** p for p in range(1, PP + 1))
        row.append(f"P={PP}: {float(sp) - ref:+.2e}")
    print(f"  e={float(ef):.2f}  kepler_solve ref E-M = {ref:.12f}   partial-sum error  " + "  ".join(row))

"""D1 dictionary check on srmech's own Class-L ops (main checkout, pure cell): under repeated application L^n
the eigenvectors (op slot) are invariant, the eigenvalues (responsion slot) run lambda -> lambda^n, the
support (operand reach) widens 1-hop -> n-hop. Also: the Kepler cascade's frame-invariant (winding) across
both truncation frames. Hand-rolled: matrix power + row support count (plain Python lists)."""
import sys, math
sys.path.insert(0, r"D:/GitHub/mlehaptics/docs/srmech/python")
from srmech.math import laplacian as L, kepler
from srmech import _native
print("HAS_NATIVE", _native.HAS_NATIVE)
n = 7
edges = [(i, (i + 1) % n) for i in range(n)]
Lm = L.dense_laplacian(n, edges)
ev = L.jacobi_eigvals(Lm)
print("C7 dense_laplacian eigvals:", [round(float(x), 6) for x in ev])
rows = [[float(Lm[i, j]) for j in range(n)] for i in range(n)]
def matmul(A, B):
    return [[sum(A[i][k] * B[k][j] for k in range(n)) for j in range(n)] for i in range(n)]
P = rows
lam = max(float(x) for x in ev)
for p in (1, 2, 3, 4):
    if p > 1: P = matmul(P, rows)
    support = sum(1 for j in range(n) if abs(P[0][j]) > 1e-12)
    # eigenvector invariance: the all-ones vector is the lambda=0 eigenvector of every power; a k=1 Fourier vector too
    v = [math.cos(2 * math.pi * j / n) for j in range(n)]
    Pv = [sum(P[i][j] * v[j] for j in range(n)) for i in range(n)]
    lam1 = 2 - 2 * math.cos(2 * math.pi / n)
    resid = max(abs(Pv[i] - (lam1 ** p) * v[i]) for i in range(n))
    print(f"  L^{p}: row-0 support {support}/{n} (operand reach)   lambda_max^p={lam**p:.4f} (responsion)   |L^p v1 - lam1^p v1|={resid:.2e} (op invariant)")
print("\nKepler cascade frame-invariant: net winding of E(M) over one period, both truncation frames, e=0.3")
N = 128; grid = [2 * math.pi * j / N for j in range(N)]
def stage(M, e, depth):
    x = M
    for _ in range(depth): x = M + e * float(kepler._rsin(x))
    return x
for depth in (1, 3, 10):
    vals = [stage(M, 0.3, depth) for M in grid] + [stage(2 * math.pi, 0.3, depth)]
    print(f"  depth {depth}: E(2pi)-E(0) = {(vals[-1]-vals[0])/(2*math.pi):.6f} turns")
from fractions import Fraction
from srmech.music import bessel_j_fixed
radii = []
for k in range(1, 9):
    num, den = bessel_j_fixed(k, k * 3, 10); radii.append(float(Fraction(2, k) * Fraction(num, den)))
for K in (1, 4, 8):
    f = lambda M: M + sum(radii[k] * math.sin((k + 1) * M) for k in range(K))
    print(f"  {K} modes: E(2pi)-E(0) = {(f(2*math.pi)-f(0))/(2*math.pi):.6f} turns")
print("\nShipped docstring claim check: kepler.pin_slot 'IS the Kepler equation of centre to second order in eccentricity' — pin_slot(theta, 2e, 1) vs nu-M at e=0.0167")
e = 0.0167
def nu_from_E(E):
    return 2.0 * math.atan2(math.sqrt(1 + e) * math.sin(E / 2), math.sqrt(1 - e) * math.cos(E / 2))
def coeffs(vals): return [2.0 / N * sum(v * math.sin(k * t) for v, t in zip(vals, grid)) for k in range(1, 4)]
def wrap(d):
    while d > math.pi: d -= 2*math.pi
    while d < -math.pi: d += 2*math.pi
    return d
ps = coeffs([kepler.pin_slot(th, 2 * e, 1.0) for th in grid])
kv = coeffs([wrap(nu_from_E(kepler.kepler_solve(M, e)) - M) for M in grid])
for k in range(3):
    print(f"  k={k+1}: pin_slot(2e) {ps[k]:+.4e}   Kepler nu-M {kv[k]:+.4e}   ratio {ps[k]/kv[k]:+.3f}")

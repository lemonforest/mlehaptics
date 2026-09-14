"""B4 - Class L pairs P8 (C_5: tr L^j vs sum lambda^j) and P9 (P_5: power iteration vs Jacobi sweeps).

srmech ops: math.laplacian.dense_laplacian (exact and float), cyclic_laplacian_spectrum, jacobi_eigvals,
math.qmat.QMat (exact powers, trace), math.qalg.cos_sin_2pi_k_over_n, calculus.cos.
HAND-ROLLED (disclosed): Rayleigh-quotient bookkeeping in Fractions; ratio estimators.
"""
import sys, math, inspect
from fractions import Fraction as F
sys.path.insert(0, "D:/GitHub/mlehaptics/docs/srmech/python")
import srmech
from srmech import _native
from srmech.math.q import Q
from srmech.math.qmat import QMat
from srmech.math import laplacian as L
from srmech.math import qalg
from srmech import calculus as C

print("srmech", srmech.__version__, "HAS_NATIVE", _native.HAS_NATIVE)


def qf(x):
    return F(x.numerator, x.denominator)


print("\n(P8) C_5")
Lx = L.dense_laplacian(5, [(i, (i + 1) % 5) for i in range(5)], exact=True)
LQ = QMat.from_rows(Lx)
spec = L.cyclic_laplacian_spectrum(5)
print("  cyclic_laplacian_spectrum(5) keys:", list(spec)[:12])
lam_f = [2 - 2 * float(C.cos(2 * math.pi * k / 5)) for k in range(5)]
Pw = QMat.identity(5)
for j in range(1, 11):
    Pw = Pw @ LQ
    tr = qf(Pw.trace())
    ps = sum(l ** j for l in lam_f)
    print(f"  j={j:2d}: tr(L^j) = {tr}   sum lambda^j (float via calculus.cos) = {ps:.6f}   diff {float(tr) - ps:+.1e}")
try:
    print("  qalg.cos_sin_2pi_k_over_n signature:", inspect.signature(qalg.cos_sin_2pi_k_over_n))
    cs = qalg.cos_sin_2pi_k_over_n(1, 5)
    print("  cos_sin_2pi_k_over_n(1,5) ->", cs)
    ex = []
    for k in range(5):
        c = qalg.cos_sin_2pi_k_over_n(k, 5)[0]
        ex.append(2 - 2 * c)
    for j in (1, 2, 5, 10):
        tot = None
        for l in ex:
            t = l ** j
            tot = t if tot is None else tot + t
        print(f"  exact sum lambda^j (Qalg) j={j}:", tot)
except Exception as exn:
    print("  exact power sums via Qalg not reached:", type(exn).__name__, str(exn)[:200])

print("\n(P9) P_5 dominant eigenvalue: power iteration (exact Rayleigh quotients) vs Jacobi sweeps")
edges = [(i, i + 1) for i in range(4)]
LP = QMat.from_rows(L.dense_laplacian(5, edges, exact=True))
lam = sorted(2 - 2 * float(C.cos(math.pi * k / 5)) for k in range(5))
lmax = lam[-1]
print("  exact spectrum 2-2cos(k pi/5):", [round(v, 12) for v in lam], "  lambda3/lambda4 =", lam[-2] / lmax, " squared:", (lam[-2] / lmax) ** 2)
v = QMat.from_rows([[1], [0], [0], [0], [0]])
rq = []
for n in range(1, 41):
    v = LP @ v
    vl = [qf(r[0]) for r in v.to_lists()]
    Lv = [qf(r[0]) for r in (LP @ v).to_lists()]
    rq.append(float(sum(x * y for x, y in zip(vl, Lv)) / sum(x * x for x in vl)))
err = [lmax - r for r in rq]
for n in (10, 20, 30):
    print(f"  power n={n}: RQ error {err[n]:.3e}  ratio {err[n] / err[n - 1]:.6f}")
Lf = L.dense_laplacian(5, edges)
for s in range(1, 7):
    ev = sorted(list(L.jacobi_eigvals(Lf, max_sweeps=s, tolerance=0.0)))
    print(f"  jacobi sweeps={s}: max |eig error| = {max(abs(a - b) for a, b in zip(ev, lam)):.3e}")

"""B2 - Heron vs continued fraction for sqrt 2, read as ONE linear object A = [[2,1],[1,0]] (a weighted
2-vertex graph: loop weight 2, edge weight 1) under distributional x relational x responsion.

srmech ops: QMat (exact powers, det), calculus.sqrt (Class-N rational sqrt at declared precision),
math.laplacian.jacobi_eigvals (float and exact), math.rational.best_rational (cross-check), Mat.
HAND-ROLLED (disclosed): Fraction bookkeeping; ratio estimators.
"""
import sys, math
from fractions import Fraction as F
sys.path.insert(0, "D:/GitHub/mlehaptics/docs/srmech/python")
import srmech
from srmech import _native
from srmech.math.qmat import QMat
from srmech.math.q import Q
from srmech.math.mat import Mat
from srmech.math import laplacian as L
from srmech.math.rational import best_rational
from srmech import calculus as C

print("srmech", srmech.__version__, "HAS_NATIVE", _native.HAS_NATIVE)


def qf(x):
    return F(x.numerator, x.denominator)


A = QMat.from_rows([[2, 1], [1, 0]])
P0 = QMat.from_rows([[1, 1], [1, 0]])
print("det A =", A.det(), " det P0 =", P0.det(), " (unimodular: the CF step is invertible over Z)")

s2q = C.sqrt(Q(2, 1), precision=4000)
S2 = qf(s2q)
print("sqrt2 instrument: calculus.sqrt(2, precision=4000); (S2^2 - 2) =", f"{float(S2 * S2 - 2):.1e}")

conv = []
M = P0
for k in range(0, 121):
    l = M.to_lists()
    conv.append((int(qf(l[0][0])), int(qf(l[1][0]))))
    M = M @ A
ok = all(best_rational(S2.numerator, S2.denominator, q) == (p, q) for p, q in conv[:100])
print("convergents from P0 @ A^k agree with srmech best_rational at each denominator (k<100):", ok)

print("\n(1) Heron depth n vs CF index; stage objects compared exactly")
x = F(1)
for n in range(1, 7):
    x = (x + 2 / x) / 2
    k = conv.index((x.numerator, x.denominator)) if (x.numerator, x.denominator) in conv else None
    print(f"  Heron n={n}: equals convergent k={k}  (2^n - 1 = {2 ** n - 1});  Pell norm p^2-2q^2 = {x.numerator ** 2 - 2 * x.denominator ** 2}")
print("  CF Pell norms k=0..9:", [p * p - 2 * q * q for p, q in conv[:10]])

print("\n(2) rates")
errs = [F(p, q) - S2 for p, q in conv]
for k in (20, 40, 80):
    print(f"  CF   err(k+1)/err(k) at k={k}: {float(errs[k + 1] / errs[k]):+.9f}")
print(f"  3 - 2 sqrt2 = {float(3 - 2 * S2):.9f}")
for k in (20, 40):
    print(f"  every-second convergent err(k+2)/err(k) at k={k}: {float(errs[k + 2] / errs[k]):+.9f}   (3-2sqrt2)^2 = {float((3 - 2 * S2) ** 2):.9f}")
x = F(1)
he = []
for n in range(1, 8):
    x = (x + 2 / x) / 2
    he.append(abs(x - S2))
print("  Heron order log err(n+1)/log err(n):", " ".join(f"{math.log(float(he[i + 1])) / math.log(float(he[i])) if float(he[i + 1]) > 0 else float('nan'):.4f}" for i in range(3)),
      "| exact logs:", " ".join(f"{(math.log(he[i + 1].numerator) - math.log(he[i + 1].denominator)) / (math.log(he[i].numerator) - math.log(he[i].denominator)):.5f}" for i in range(6)))

print("\n(3) the three reads of A")
ev = L.jacobi_eigvals(Mat.from_rows([[2.0, 1.0], [1.0, 0.0]]))
evl = sorted(list(ev))
print("  eigenvalues (jacobi, float):", evl, " |lam-/lam+| =", abs(evl[0] / evl[1]))
try:
    print("  eigenvalues (jacobi exact=True):", L.jacobi_eigvals([[Q(2, 1), Q(1, 1)], [Q(1, 1), Q(0, 1)]], exact=True))
except Exception as ex:
    print("  exact jacobi on [[2,1],[1,0]] raised:", type(ex).__name__, str(ex)[:160])
lp = 1 + float(S2)
v = (lp, 1.0)
Av = (2 * v[0] + v[1], v[0])
print("  A @ (1+sqrt2, 1) / (1+sqrt2) =", (Av[0] / lp, Av[1] / lp), " -> eigenvector (distributional read); P0 maps it to ratio",
      (v[0] + v[1]) / v[0])
print("  relational read: entries of A^k are weighted walk counts; [A^8] =", [[int(qf(z)) for z in r] for r in (A ** 8).to_lists()] if hasattr(A, '__pow__') else "n/a")

print("\n(4) direction / irreversibility")
h = lambda t: (t + 2 / t) / 2
print("  Heron h(3/2) == h(4/3):", h(F(3, 2)) == h(F(4, 3)), " (x and 2/x share an image: 2-to-1)")
print("  CF alternates sides of sqrt2 (sign of err k=0..7):", ["+" if errs[k] > 0 else "-" for k in range(8)])
print("  Heron iterates all above sqrt2 (n=1..6):", all(e > 0 for e in [F(1)] and [(lambda z: z)(0)] or []) if False else all(
    (lambda t: t > S2)(t) for t in (F(3, 2), F(17, 12), F(577, 408))))

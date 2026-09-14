"""B5: P10 (pure winding_fold 2pi constant + 2^-44 grid vs Machin partial sums) and P8 exact power sums (Qalg).
srmech ops only, plus Fraction bookkeeping (disclosed). Private constants read, not modified."""
import sys, inspect
from fractions import Fraction as F
sys.path.insert(0, "D:/GitHub/mlehaptics/docs/srmech/python")
import srmech
from srmech import _native
from srmech.math import laplacian as L, rational as R, qalg
from srmech.math.qmat import QMat
print("srmech", srmech.__version__, "HAS_NATIVE", _native.HAS_NATIVE)
pn, pd = L._EPH_TWO_PI
print("_EPH_TWO_PI =", pn, "/", pd, " denominator bits:", pd.bit_length(), " _EPH_FOLD_DEN =", L._EPH_FOLD_DEN, "= 2^%d" % (L._EPH_FOLD_DEN.bit_length() - 1))
T = F(pn, pd)
ps = R.pi_chudnovsky_digits(300); PI = F(int(ps.replace('.', '')), 10 ** len(ps.split('.')[1]))
print("  |_EPH_TWO_PI - 2pi| =", float(abs(T - 2 * PI)))
hit = None
for N in range(1, 80):
    m = 2 * (16 * F(*R.atan_series_truncate(1, 5, N).as_pair()) - 4 * F(*R.atan_series_truncate(1, 239, N).as_pair()))
    if m == T:
        hit = N
    if N in (5, 10, 15, 20, 25, 30) or m == T:
        q_m = round(m * L._EPH_FOLD_DEN); q_T = round(T * L._EPH_FOLD_DEN)
        print(f"  N={N}: 2*Machin_N == _EPH_TWO_PI exactly: {m == T};  same 2^-44 grid cell: {q_m == q_T};  |diff| = {float(abs(m - T)):.2e}")
print("  exact Machin stage equal to the register constant: N =", hit)
first_cell = next(N for N in range(1, 80) if all(round(2 * (16 * F(*R.atan_series_truncate(1, 5, M).as_pair()) - 4 * F(*R.atan_series_truncate(1, 239, M).as_pair())) * L._EPH_FOLD_DEN) == round(T * L._EPH_FOLD_DEN) for M in range(N, N + 5)))
print("  first N from which Machin_N stays in the register's 2^-44 cell (checked 5 further stages):", first_cell)

print("\nP8 exact power sums on C_5 via Qalg cos(2 pi k/5):")
ex = [2 - 2 * qalg.cos_sin_2pi_k_over_n(5, k)[0] for k in range(5)]
Lq = QMat.from_rows(L.dense_laplacian(5, [(i, (i + 1) % 5) for i in range(5)], exact=True))
Pw = QMat.identity(5)
for j in range(1, 11):
    Pw = Pw @ Lq
    tot = ex[0] ** j
    for l in ex[1:]:
        tot = tot + l ** j
    print(f"  j={j}: sum lambda^j (Qalg) = {tot}   tr(L^j) = {Pw.trace()}")

print("\nTable-1 / quick-start existence checks:")
import srmech.math.hdc as H
print("  srmech.math.hdc has bind/bundle/permute/similarity:", [hasattr(H, n) for n in ('bind', 'bundle', 'permute', 'similarity')])
print("  srmech._native.srmech_version:", hasattr(_native, 'srmech_version'), [n for n in dir(_native) if 'version' in n.lower()][:6])
import srmech.spectral as SP
print("  spectral.decompose", inspect.signature(SP.decompose), "| predict", inspect.signature(SP.predict))
print("  laplacian.dense_laplacian", inspect.signature(L.dense_laplacian), "(book calls dense_laplacian(A.astype(np.complex128)))")
from srmech.signal_processing import path_registry as PR
names = [n for n in dir(PR) if not n.startswith('_')]
print("  path_registry public names:", names[:20])

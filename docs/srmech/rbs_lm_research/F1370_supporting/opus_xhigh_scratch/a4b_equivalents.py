"""A4b: remaining functional-equivalent runs (shifted circle, fft, Hopf) + a second instrument on the Hubble figure."""
import sys, math
from fractions import Fraction as F
sys.path.insert(0, "D:/GitHub/mlehaptics/docs/srmech/python")
import srmech
from srmech import _native
print("srmech", srmech.__version__, "HAS_NATIVE", _native.HAS_NATIVE)
from srmech.math.q import Q
from srmech import calculus as C
from srmech.math import rational as R, laplacian as L
from srmech.math.mat import Mat
from srmech.cascade import spectral_cascades as SC, cayley_dickson as CD, cayley_plane as CP

print("\n[p.48/184/195] shifted-circle eigenvalues: mat_eigvals(I + P_n):")
for n in (4, 6):
    rows = [[complex((1 if i == j else 0) + (1 if (i - j) % n == 1 else 0)) for j in range(n)] for i in range(n)]
    ev = L.mat_eigvals(Mat.from_rows(rows))
    print(f"   n={n}:", [complex(round(z.real, 12), round(z.imag, 12)) for z in ev], " max ||lam-1|-1| =", f"{max(abs(abs(z - 1) - 1) for z in ev):.1e}")

print("\n[p.49/197] fft on N=8 (spectral_cascades.fft), value only:")
print("   ", [complex(round(z.real, 9), round(z.imag, 9)) for z in SC.fft([complex(k, 0) for k in range(8)])])
try:
    from srmech.cascade import exact_dft
    print("   exact_dft._radix2_ring_op_count(8) =", exact_dft._radix2_ring_op_count(8))
except Exception as ex:
    print("   op count not reached:", type(ex).__name__, str(ex)[:100])

s = 2 ** -0.5
print("\n[p.23 Ex.2.5] complex Hopf at (1/sqrt2,1/sqrt2) via octonion_hopf_base on a, b in C (16-vector):")
hb = CP.octonion_hopf_base([s] + [0.0] * 7 + [s] + [0.0] * 7)
for k in hb:
    print("   ", k, "=", hb[k])
print("\n[p.24 Ex.2.8] quaternionic Hopf base at (q1,q2) = (1/sqrt2, 1/sqrt2) via octonion_frame_read:")
fr = CD.octonion_frame_read([s, 0, 0, 0, s, 0, 0, 0])
for k in fr:
    print("   ", k, "=", str(fr[k])[:160])
u = [0.5, 0.5, 0.5, 0.5]  # unit quaternion, right-multiplied into both halves: fibre direction
def qmul(a, b):
    a0, a1, a2, a3 = a; b0, b1, b2, b3 = b
    return [a0*b0 - a1*b1 - a2*b2 - a3*b3, a0*b1 + a1*b0 + a2*b3 - a3*b2, a0*b2 - a1*b3 + a2*b0 + a3*b1, a0*b3 + a1*b2 - a2*b1 + a3*b0]
x2 = qmul([s, 0, 0, 0], u) + qmul([s, 0, 0, 0], u)
fr2 = CD.octonion_frame_read(x2)
print("   after right-multiplying both halves by a unit quaternion (hand-rolled qmul, disclosed), keys equal:",
      {k: (str(fr[k]) == str(fr2[k])) for k in fr})

print("\n[p.154] Hubble figure, two instruments:")
ps = R.pi_chudnovsky_digits(60)
PI = F(int(ps.replace('.', '')), 10 ** len(ps.split('.')[1]))
x = PI * F(13787, 1000) / F(10984, 100)
print("   srmech calculus.cos (Q61):", 1 - float(C.cos(float(x))))
print("   exact cos Taylor (Fraction, 30 terms, hand-rolled):", float(1 - sum(F((-1) ** j) * x ** (2 * j) / math.factorial(2 * j) for j in range(30))))
print("   math.cos:", 1 - math.cos(float(x)))
for t0, T in ((13.787, 109.84), (13.8, 109.84), (13.787, 109.0), (13.797, 109.84)):
    print(f"   variant t0={t0}, T={T}: {1 - math.cos(math.pi * t0 / T):.6f}")

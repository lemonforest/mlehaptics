"""A4: run shipped functional equivalents on the book's own examples, where cheap.
All srmech ops, main checkout, pure cell. Float instruments named inline."""
import sys, math
sys.path.insert(0, "D:/GitHub/mlehaptics/docs/srmech/python")
import srmech
from srmech import _native
print("srmech", srmech.__version__, "HAS_NATIVE", _native.HAS_NATIVE)
from srmech.math.q import Q
from srmech import calculus as C
from srmech.math import rational as R, kepler, laplacian as L
from srmech.math.mat import Mat
from srmech.physics.qm import bell
from srmech.cascade import spectral_cascades as SC, cayley_dickson as CD, cayley_plane as CP

print("\n[p.184/223] Tsirelson: chsh_operator_norm() =", bell.chsh_operator_norm(), " 2*sqrt2 =", 2*float(C.sqrt(2.0)), " verify_chsh:", bell.verify_chsh())

print("\n[p.69 Ex.8.4] kepler_solve(pi/4, 0.3) =", kepler.kepler_solve(math.pi/4, 0.3, tolerance=1e-15), "(book prints E2~0.99622)")
E = kepler.kepler_solve(math.pi/4, 0.3, tolerance=1e-15)
print("   residual E - 0.3 sin E - pi/4 at book value 0.99622:", 0.99622 - 0.3*float(C.sin(0.99622)) - math.pi/4, " at solver value:", E - 0.3*float(C.sin(E)) - math.pi/4)
# book's own Newton steps redone (float instrument, srmech sin/cos)
En = math.pi/4
for i in range(4):
    En = En - (En - 0.3*float(C.sin(En)) - math.pi/4)/(1 - 0.3*float(C.cos(En)))
    print(f"   Newton E{i+1} = {En:.6f}")

print("\n[p.152/184] Schwarzschild ISCO 1 - sqrt(8/9):", 1 - float(C.sqrt(Q(8,9), precision=200)), "(book 0.0571909584)")
print("            Kerr extremal 1 - 1/sqrt(3):", 1 - 1/float(C.sqrt(Q(3,1), precision=200)), "(book 0.4226497308)")

pi_s = R.pi_chudnovsky_digits(40)
from fractions import Fraction as F
PI = F(int(pi_s.replace('.', '')), 10**(len(pi_s.split('.')[1])))
om = 2*PI/(F(10984,100)*10**9 * F(31557,10000)*10**7)
print("\n[p.94/211] Omega_sub = 2pi/(109.84e9 * 3.1557e7 s) =", float(om), "(book 1.813e-18)")

x = PI*F(13787,1000)/F(10984,100)
c = C.cos(float(x))
print("\n[p.154] Hubble: 1 - cos(pi*13.787/109.84) =", 1-float(c), " argument", float(x), "(book: 1-0.9231 = 7.69%; notebooks :2143/:1284 print 0.07686)")

print("\n[p.60/200] toy_modulation_time closed form T = (1/c)(1/eps - 1/gap) [alpha=2], (1/2c)(1/eps^2 - 1/gap^2) [alpha=3], exact Q:")
eps, gap, cc = Q(1,1000), Q(1,1), Q(1,1)
T2 = (Q(1,1)/cc)*(Q(1,1)/eps - Q(1,1)/gap); T3 = (Q(1,1)/(Q(2,1)*cc))*(Q(1,1)/(eps*eps) - Q(1,1)/(gap*gap))
print("   alpha=2:", T2, "  alpha=3:", T3, "(book 999 / 499999.5)")

print("\n[p.87/218] Cauchy kernel K_k=1/k!: exp_series_truncate(1,2,N):")
for N in (4, 8, 16):
    s = R.exp_series_truncate(1, 2, N); m = R.exp_series_truncate(-1, 2, N)
    print(f"   N={N}: f(0.5)={float(s):.12f}  f(0.5)*f(-0.5)={float(s*m):.15f}")
print("   K_k=1 geometric partial sums (exact Q) at x=1/2 and x=2:")
for x_, lab in ((Q(1,2),'1/2'), (Q(2,1),'2')):
    acc, term, out = Q(0,1), Q(1,1), []
    for k in range(12):
        acc = acc + term; term = term*x_; out.append(float(acc))
    print(f"   x={lab}: {[round(v,4) for v in out]}")

print("\n[p.48/184/195] shifted-circle eigenvalues: mat_eigvals(I + P_n):")
for n in (4, 6):
    rows = [[complex(1 if i == j else 0) + complex(1 if (i - j) % n == 1 else 0) for j in range(n)] for i in range(n)]
    ev = L.mat_eigvals(Mat(rows))
    print(f"   n={n}: eigvals", [complex(round(z.real,12), round(z.imag,12)) for z in ev], " max ||lam-1|-1| =", max(abs(abs(z-1)-1) for z in ev))

print("\n[p.49/197] fft on N=8 (spectral_cascades.fft) — value only; no cascade-class trace op exists:")
xs = [complex(k,0) for k in range(8)]
print("   fft([0..7]) =", [complex(round(z.real,9), round(z.imag,9)) for z in SC.fft(xs)])

print("\n[p.23 Ex.2.5] complex Hopf at (1/sqrt2, 1/sqrt2), via octonion_hopf_base restricted to C^2 (a=(s,0..), b=(s,0..)):")
s = 2**-0.5
xv = [s]+[0.0]*7+[s]+[0.0]*7
hb = CP.octonion_hopf_base(xv)
print("   ", {k: hb[k] for k in hb if k in ('base_O','base_R','norm_sq','on_sphere')} if isinstance(hb, dict) else hb)
print("[p.24 Ex.2.8] quaternionic Hopf (book calls it octonionic) at (q1,q2)=(1/sqrt2,1/sqrt2) via octonion_frame_read:")
fr = CD.octonion_frame_read([s,0,0,0,s,0,0,0])
print("   keys:", list(fr)[:12])
for k in list(fr)[:6]: print("   ", k, "=", fr[k])

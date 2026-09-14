"""Cheap srmech check (pure cell, main checkout) of the 2026-09-07 assistant sense of
"resonance is anisotropic": 'the spectrum isn't a scalar, each eigenvector carries its own
eigenvalue. Direction-dependent in both domains.'

Three questions, each answered by a shipped op:
 Q1  does each eigenvector carry its OWN eigenvalue?  (C_7 exact spectrum: chirality_paired;
     Q_3 spectrum: multiplicities)
 Q2  does the SPECTRUM depend on DIRECTION (edge orientation)?  magnetic_laplacian on a
     directed 3-cycle and its reversal: Hermitian spectra compared; cycle_holonomy compared.
 Q3  where does the tree's measured asymmetry sit?  kuramoto_step with Sakaguchi alpha = -0.3/0/+0.3
     (the MFO §VIII.31.21 instrument), collective drift sign.
"""
import sys, io, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import srmech
from srmech import _native
import srmech.math.laplacian as L
from srmech.cascade import kuramoto_step
print("srmech", srmech.__version__, "HAS_NATIVE", getattr(_native, "HAS_NATIVE", None), srmech.__file__)

# Q1
s7 = L.cyclic_laplacian_spectrum(7)
print("Q1a C_7 exact spectrum keys:", sorted(k for k in s7.keys()))
print("    chirality_paired =", s7.get("chirality_paired"), "| field_degree =", s7.get("field_degree"),
      "| all_rational =", s7.get("all_rational"))
q3_edges = [(0,1),(0,2),(0,4),(1,3),(1,5),(2,3),(2,6),(3,7),(4,5),(4,6),(5,7),(6,7)]
M = L.dense_laplacian(8, q3_edges)
ev = L.jacobi_eigvals(M)
ev = [round(float(x), 9) for x in ev]
from collections import Counter
print("Q1b Q_3 spectrum:", ev, "| multiplicities:", dict(Counter(ev)))

# Q2
fwd = [(0,1),(1,2),(2,0)]
rev = [(1,0),(2,1),(0,2)]
try:
    from srmech.math.laplacian import hermitian_eigendecompose
except Exception:
    hermitian_eigendecompose = None
for name, edges in (("forward", fwd), ("reversed", rev)):
    Mq = L.magnetic_laplacian(3, edges, q=0.25)
    try:
        vals = hermitian_eigendecompose(Mq)
        if isinstance(vals, dict):
            vals = vals.get("eigenvalues", vals)
        elif isinstance(vals, tuple):
            vals = vals[0]
        vals = [round(float(v), 9) for v in vals]
    except Exception as e:
        vals = f"eig error: {e}"
    hol = L.cycle_holonomy(edges, n=3)
    print(f"Q2 {name:8s} magnetic spectrum(q=1/4) = {vals} | cycle_holonomy = {hol}")

# Q3
def drift(alpha, steps=4000, dt=0.01, K=4.0):
    th = [0.0, 0.1, 0.2, 0.3]; om = [1.0, 2.0, 3.0, 4.0]
    for _ in range(steps):
        th = kuramoto_step(th, om, coupling=K, dt=dt, alpha=alpha)
    mean_omega = sum(om) / len(om)
    coll = sum(th) / len(th)
    return coll - mean_omega * steps * dt
for a in (-0.3, 0.0, 0.3):
    print(f"Q3 alpha={a:+.1f}: collective drift beyond mean-omega = {drift(a):+.6f}")

"""Investigate: Jupiter + Galilean-moon coupling system as a gravity/forces-of-forces encode.
Reads: (1) the orbital resonance via Qprime (the dark/stored ratio structure), (2) the coupling-Laplacian
SPECTRUM = the stored tensions (the 'dark composition' before any pluck/excitation), (3) L^2 = forces-of-
forces = the tidal/biharmonic concentration + dispersive curvature evolution. Watching for the common
cascade -> a srmech primitive (like the_one). srmech rc33; small graph; spectral READING not a simulator.
Body data illustrative (JPL fact-sheet order of magnitude); a real run sources the ephemerides catalog."""
from srmech.amsc import laplacian as La, rational, primes
from srmech.amsc.qprime import Qprime
from srmech.amsc.mat import Mat
def fl(q): return q.as_float() if hasattr(q,"as_float") else float(q)
# bodies: a = semi-major axis (10^3 km), m = mass (10^22 kg)  [Jupiter central]
B=["Jupiter","Io","Europa","Ganymede","Callisto"]
a=[0.0, 421.7, 671.0, 1070.4, 1882.7]
m=[189800.0, 8.93, 4.80, 14.82, 10.76]
n=len(B)

# (1) RESONANCE: mean motion ~ a^-1.5 (Kepler 3rd); read the ratios via Qprime (J) + best_rational (N)
mm=[(a[i]**-1.5 if a[i] else 0.0) for i in range(n)]
print("=== (1) orbital resonance (mean-motion ratios, the stored/dark ratio structure) ===")
for i in (1,2,3):  # Io, Europa, Ganymede
    r=mm[1]/mm[i]; num,den=rational.best_rational(round(r*1_000_000),1_000_000,64)
    qp=Qprime.from_vec(dict(primes.factor(den)) if den>1 else {})
    print(f"  n_Io/n_{B[i]:<8} = {r:.3f}  best_rational={num}/{den}  den prime-coords={qp.coords}")
print("  Io:Europa:Ganymede mean-motion ratio ~ 4:2:1 (the Laplace lock) -> 2-adic ladder (Class J).")

# (2) COUPLING LAPLACIAN = the gravity coupling; its SPECTRUM = the stored tensions (the 'dark' composition)
edges=[]; weights=[]
for i in range(n):
    for j in range(i+1,n):
        r=a[j] if i==0 else (a[j]-a[i])          # Jupiter-moon: moon's axis; moon-moon: gap
        if r>0:
            w=m[i]*m[j]/(r*r)                         # gravity-like coupling weight
            edges.append((i,j)); weights.append(w)
L=La.dense_laplacian(n, edges, weights)
evals,evecs=La.symmetric_eigendecompose(L)
ev=sorted(fl(x) for x in evals)
print("\n=== (2) coupling-Laplacian spectrum = stored TENSIONS (dark composition, no excitation yet) ===")
print(f"  eigenvalues (tensions): {[f'{x:.3g}' for x in ev]}")
print(f"  near-zero modes (free/bulk): {sum(1 for x in ev if x<ev[-1]*1e-9)} ; top tension/bottom = {ev[-1]/max(ev[1],1e-30):.2g}x spread")

# (3) FORCES OF FORCES: L^2 = biharmonic (tidal/turbulence). Compare diagonal (self-coupling) of L vs L^2.
L2=L @ L
def diag(M,i): return fl(M[i][i])
print("\n=== (3) forces-of-forces (L^2 = biharmonic tidal/turbulence): diagonal concentration ===")
print(f"  {'body':<9}{'L (force)':>14}{'L^2 (force-of-force)':>22}{'ratio L2/L':>12}")
for i in range(n):
    d1,d2=diag(L,i),diag(L2,i); print(f"  {B[i]:<9}{d1:>14.3g}{d2:>22.4g}{(d2/d1 if d1 else 0):>12.3g}")
print("  L^2 over-weights the strongest-coupled near pair (the tidal flux) -- forces-of-forces concentrate where gravity does.")
print("  spectrum of L^2 = (spectrum of L)^2 -> curvature evolves DISPERSIVELY (4th-order), not like 2nd-order matter curvature.")

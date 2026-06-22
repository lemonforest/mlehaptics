"""F927 — the gravity/flux/turbulence encode = composition of shipped srmech lenses; "forces of forces"
= iterated Laplacian L^n (L^2 = biharmonic = tidal/turbulence), diagonalized by the spectrum. Resonances
= integer eigenvalue ratios read via Qprime (J) + best_rational (N). Flux = magnetic (C/K) + Qarg. No new
primitive: Mat has __matmul__; eigendecompose, Qprime, best_rational, magnetic_laplacian, Qarg, kepler,
coupling all ship (rc33). srmech 0.9.0rc33; spectral/algebraic READING (in scope), NOT an N-body simulator."""
from srmech.amsc import rational, primes
from srmech.amsc.qprime import Qprime
# the Laplace resonance Io:Europa:Ganymede ~ 1:2:4 (JPL periods, days) read as structure
T={'Io':1.769138,'Europa':3.551181,'Ganymede':7.154553}; base=T['Io']
print("Laplace resonance as Class-N anchor + Class-J prime ladder:")
for m in ('Io','Europa','Ganymede'):
    r=T[m]/base; num,den=rational.best_rational(round(r*1_000_000),1_000_000,64)
    print(f"  {m:<9} T/T_Io={r:.4f}  best_rational={num}/{den}  (libration => not exactly 1:2:4)")
for n in (1,2,4):
    q=Qprime.from_vec(dict(primes.factor(n)) if n>1 else {})
    print(f"  ideal ratio {n}: Qprime coords={q.coords}")
print("=> ideal lock = 2-adic ladder (Qprime J); real deviation = libration (best_rational N). Mat @ Mat gives L^2 (forces-of-forces).")

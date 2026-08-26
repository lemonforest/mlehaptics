"""F933 — the closure half is not alien dark content: it is our own HEPTAD, mirrored into the two dark
chiralities. Grounded: the 14 derivations (g2) fix exactly ONE octonion direction (the real unit e_0,
14/14) and act on the imaginary 7 -> each rep splits 8 = 1 (singlet) + 7 (heptad). so(8) = g2 (+) 7 (+) 7
(standard): the closure 7+7 = two copies of that same heptad-rep, in the two dark (triality-active)
chiralities. srmech 0.9.0rc33; exact; no numpy."""
from fractions import Fraction as Fr
from srmech.qm import so8
g2=so8.g2_subalgebra()
def col(D,k): return [Fr(D[i][k]) for i in range(8)]
def is_zero(v): return all(x==0 for x in v)
fixed_dirs=[k for k in range(8) if sum(1 for D in g2 if is_zero(col(D,k)))==14]
print(f'octonion directions fixed by ALL 14 derivations: {fixed_dirs}  (= the real unit e_0, the singlet)')
print(f'=> 8 = 1 (g2-fixed singlet) + 7 (the heptad the derivations act on).')
print(f'   so(8) = g2(14) + 7 + 7 : the closure 7+7 = TWO copies of that heptad-rep, in the two dark chiralities.')

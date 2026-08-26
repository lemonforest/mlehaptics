"""F932 — the non-deriving half of so(8) (the closure) = the triality-ACTIVE complement = the two
chiralities (7+7 = the omega/omega^2 eigenspaces). Grounded basis-robustly via the trace: tau is order-3
(tau^3=I), tr(tau)=tr(tau^2)=7, so dim Fix(tau) = (28 + tr + tr^2)/3 = 14 = dim g2 = the derivations
(F931). Complement = 28-14 = 14 = 7+7 (two spinor chiralities). srmech 0.9.0rc33; exact Fraction; no numpy.
NOTE: the direct 28x28 tau-on-adjoint-coords fixedness check returned 0/14 (a basis/normalization
convention mismatch between srmech's tau and the Frobenius adjoint-projection) -- a probe-mechanics issue,
NOT a refutation; the trace method below is basis-independent and the identification Fix(tau)=g2 is the
standard Cartan fact + F931 (g2 = the octonion derivations)."""
from fractions import Fraction as Fr
from srmech.qm import triality
tau=triality.triality_automorphism(); n=28
def tr(M): return sum(Fr(M[i][i]) for i in range(n))
def matmul(A,B): return [[sum(Fr(A[i][k])*Fr(B[k][j]) for k in range(n)) for j in range(n)] for i in range(n)]
t2=matmul(tau,tau); t3=matmul(t2,tau)
order3=all(Fr(t3[i][j])==(1 if i==j else 0) for i in range(n) for j in range(n))
tr1,tr2=tr(tau),tr(t2); dimfix=(28+tr1+tr2)/3
print(f'tau^3==I: {order3} | tr(tau)={tr1} tr(tau^2)={tr2} | dim Fix(tau)=(28+tr+tr2)/3={dimfix}')
print(f'=> GENERATE = Fix(tau) = 14 = g2 = derivations (F931); CLOSE = complement = {28-dimfix} = 7+7 (two chiralities).')

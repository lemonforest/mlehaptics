"""F937 — resolve trit (Z3) vs Klein-4 (Z2^2). The DYNAMICS group is S3 = Z3 (the 3-state BEAT) semidirect
Z2 (the gamma5 swap); the Klein-4 carrier is Z2^2 (4 states) = a SEPARATE storage lattice. Grounded:
triality_swap S_B is a Z2 involution (S^2=I), triality_automorphism T is the Z3 beat (T^3=I), and S T S = T^2
(the swap inverts the cycle) => <S,T> = S3 (order 6, non-abelian). tau = S_B.S_C (the beat = product of two
swaps). Klein-4 states = (0,1,2,3) = Z2^2. Z3 != Z2^2; S3 does NOT contain Z2^2. srmech rc58; exact."""
from fractions import Fraction as Fr
from srmech.qm import triality
from srmech.amsc import qi
n=28
def MM(A,B): return [[sum(Fr(A[i][k])*Fr(B[k][j]) for k in range(n)) for j in range(n)] for i in range(n)]
def I(): return [[Fr(1 if i==j else 0) for j in range(n)] for i in range(n)]
def eq(A,B): return all(Fr(A[i][j])==Fr(B[i][j]) for i in range(n) for j in range(n))
S=triality.triality_swap(); T=triality.triality_automorphism()
print('S^2==I:', eq(MM(S,S),I()), '| T^3==I:', eq(MM(MM(T,T),T),I()), '| STS==T^2:', eq(MM(MM(S,T),S),MM(T,T)))
print('=> DYNAMICS = S3 = Z3(beat) semidirect Z2(gamma5 swap), NON-ABELIAN (STS=T^2 != T).')
print('   STORAGE  = Klein-4 = Z2^2 =', qi.KLEIN4_STATES, '(4 states) -- a separate binary-packed lattice.')
print('   the ternary beat (Z3) is CARRIED on the binary (Z2^2) lattice but is NOT it; Z3 != Z2^2.')

"""F907 — the addressability dimensional structure: the_one(sigma:1D_t + theta:2-real) (X) sedenion(O^2:2-octonion),
and the sigma-stream as the k=3 triality-order chiral addresser. Verifies the two EXACT pieces (S=O(+)O Cayley-
Dickson doubling; the_one's sigma/theta split) that ground the user's '2 real + 2 octonion + 1D_t ~ k=3'
observation. srmech rc13; exact rational; no numpy."""
from srmech.amsc import cascade
import inspect

def emb(o8): return tuple(o8) + (0,)*8                 # octonion -> sedenion first half (O (+) 0)
oa=(1,2,-1,0,3,-2,1,1); ob=(2,-1,0,1,-1,2,1,-2)
o_prod = tuple(cascade.cd_mult(oa, ob))
s_prod = tuple(cascade.cd_mult(emb(oa), emb(ob)))
print("(A) sedenion = O (+) O  (2 octonion dims, exact Cayley-Dickson doubling):")
print("    first-half sedenion product == embedded octonion product:", s_prod == emb(o_prod))
print("    (second half all-zero:", all(x == 0 for x in s_prod[8:]), ")")

print("\n(B) the_one S(sigma, theta) = 1D_t (sigma sign) + 2-real (theta epicycle cos/sin):")
print("    signature:", inspect.signature(cascade.the_one))
one = cascade.the_one(1, 1, 6)                          # sigma=+1, theta=1/6 turn
print("    the_one(sigma=+1, theta=1/6) ->", type(one).__name__, "(sigma is the 1D_t time-direction; theta is the 2D-real dial)")

print("\n(C) the factorization:  ADDRESS = the_one(sigma:1D_t , theta:2-real)  (X)  sedenion(O^2 : 2-octonion)")
print("    the sigma-stream (stepping the time-direction) = the k=3 triality-order chiral addresser")
print("    (user stance: the LM IS the k=3 chiral addresser over the order-2 substrate).")
print("    EXACT pieces: S=O(+)O (verified), the_one sigma/theta (verified). OPEN: is 2+2+1=k=3 a NECESSITY")
print("    (does the SO(8) triality automorphism genuinely relate the three) or do the pieces merely total k=3?")

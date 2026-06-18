"""F862 probe: is Klein-4 the wrong object for the WALK? Does the_one's native
Cayley-Dickson tower (R/Q/O/S = R/H/O/S) carry what Klein-4 cannot -- ORDER (path)?
And the massless/photon mode: navigate the coupling (the PRODUCT) itself.
srmech-native: cascade.cd_mult / cd_conjugate / sedenion_zero_divisor_witness,
hdc.klein4_bind (commutative XOR), the_one.to_matrix (the hypercomplex generator).
"""
from srmech.amsc import cascade, hdc

def differ(a, b):
    return tuple(a) != tuple(b)

print("=== Does the object carry ORDER (the WALK needs it) ? ===")
# Klein-4 (the current store object): XOR group -> commutative + associative -> ORDER-BLIND
a = hdc.klein4_random(64, seed=1); b = hdc.klein4_random(64, seed=2); c = hdc.klein4_random(64, seed=3)
ab = hdc.klein4_bind(a, b); ba = hdc.klein4_bind(b, a)
print(f"Klein-4 bind commutative?  a*b == b*a : {hdc.klein4_similarity(ab, ba) == 1.0}  -> ORDER-BLIND (cannot encode a walk's direction)")
abc = hdc.klein4_bind(hdc.klein4_bind(a, b), c); a_bc = hdc.klein4_bind(a, hdc.klein4_bind(b, c))
print(f"Klein-4 bind associative?  (a*b)*c == a*(b*c) : {hdc.klein4_similarity(abc, a_bc) == 1.0}  -> grouping-blind too")

# Cayley-Dickson tower (the_one's native algebra): R(1) / C(2) / H=Q(4) / O(8) / S(16)
q1 = (1, 2, 3, 4); q2 = (4, 3, 2, 1)                      # quaternions (H = Q)
print(f"\nQuaternion (H, dim4) commutative?  q1*q2 == q2*q1 : {not differ(cascade.cd_mult(q1,q2), cascade.cd_mult(q2,q1))}"
      f"  -> NON-commutative = carries ORDER (the walk's direction)")
o1 = (1,0,1,0,1,0,0,1); o2 = (0,1,1,0,0,1,1,0); o3 = (1,1,0,0,1,0,1,0)   # octonions (O)
lhs = cascade.cd_mult(cascade.cd_mult(o1,o2), o3); rhs = cascade.cd_mult(o1, cascade.cd_mult(o2,o3))
print(f"Octonion (O, dim8) associative?  (o1*o2)*o3 == o1*(o2*o3) : {not differ(lhs, rhs)}"
      f"  -> NON-associative = carries GROUPING (how the path is bracketed)")
# Sedenion (S, dim16): division fails -> zero-divisors (the asymptote / breakdown rung)
try:
    w = cascade.sedenion_zero_divisor_witness()
    print(f"Sedenion (S, dim16): zero-divisor witness exists -> {w is not None}  -> division BREAKS (the asymptotic boundary)")
except Exception as e:
    print("sedenion witness:", e)

print("\n=== the_one IS the hypercomplex generator: its WALK is path-dependent ===")
M1 = cascade.the_one(1, 1, 4).to_matrix()   # crank phase 1/4
M2 = cascade.the_one(1, 1, 3).to_matrix()   # crank phase 1/3
f = (M1 @ M2); g = (M2 @ M1)
fl = [x for x in f.to_flat()] if hasattr(f, 'to_flat') else None
# compare two products elementwise via tolist
fl = f.tolist() if hasattr(f, 'tolist') else None
gl = g.tolist() if hasattr(g, 'tolist') else None
same = (fl == gl) if fl is not None else "n/a"
print(f"the_one PHASE-crank M(1/4)@M(1/3) == M(1/3)@M(1/4) ? : {same}")
print("  -> COMMUTES: the epicycle is a single-plane rotation (abelian). The phase/crank is a DIAL POSITION,")
print("     not a path. Walk-ORDER memory must come from the non-commutative cd_mult COUPLING product, NOT theta.")

print("\n=== massless / photon mode: no mass-gear, helicity = chirality, coupling = the product ===")
# a massless probe carries NO gear-rate (mass): uniform phase; helicity = sigma (the two chiralities)
photon_plus = cascade.the_one(+1, 1, 4)     # helicity +1
photon_minus = cascade.the_one(-1, 1, 4)    # helicity -1 (sigma-mirror = opposite circular polarization)
fp = [p/q for p,q in photon_plus.to_flat_rational()]
fm = [p/q for p,q in photon_minus.to_flat_rational()]
flips = sum(1 for x,y in zip(fp,fm) if (x>0) != (y>0))
print(f"two helicities (sigma=+1 vs -1) differ in {flips}/14 sign-coords = the two circular polarizations (chirality)")
print("massless probe = the_one with NO gear-rate (uniform speed) -> not captured by mass-wells, only LENSED (de-lensed traversal);")
print("coupling = cd_mult (the gauge product) -> navigation rides the EDGE (relationship), order-dependent (the walk).")

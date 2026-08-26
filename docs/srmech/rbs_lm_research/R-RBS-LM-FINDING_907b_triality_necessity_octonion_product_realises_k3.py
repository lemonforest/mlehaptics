"""F907b — necessity test: does SO(8) triality genuinely relate the (2+1)=2D_oct+1D_t as one order-3
orbit, or is '(2+1)=k=3' a coincidence of count? Decisive: (1) the rep-cycle is order-3 (8v->8s->8c->8v);
(2) Cartan's relation g_v(x*y)=g_s(x)*g_c(y) holds (residual~0) => the OCTONION PRODUCT realises the
three reps {x, y, x*y}; (3) so the time-stream, IF it is the cd_mult coupling (F862/F906), turns the two
stored octonions into the third rep = a genuine triality per step. Honest about (a) vs (b). srmech rc13."""
from srmech.qm import so8, triality

print("=== F907b triality-necessity test for the addressability (2+1) ===")

# (1) order-3 rep cycle
f0 = triality.triality_cycle("8v"); f = f0; cyc=[f0]
for _ in range(3): f = triality.triality_cycle(f); cyc.append(f)
print(f"\n(1) rep cycle: {' -> '.join(cyc)}  | order-3: {cyc[0]==cyc[3]}")

# (2) Cartan's relation residual for several so(8) generators (g_v + its companions)
basis = so8.so8_adjoint_basis()                 # 28 generators: 14 g2 + 7 L + 7 R
print(f"\n(2) Cartan g_v(x*y)=g_s(x)*g_c(y) residual (0 => octonion product realises the 3-rep triality):")
import itertools
idxs = [0, 14, 15, 21, 22, 27]                  # sample across g2 / L / R blocks
for i in idxs:
    g_v = basis[i]
    try:
        g_s, g_c = triality.triality_companions(g_v)
        r = triality.triality_relation_residual(g_v, g_s, g_c)
        rf = r.as_float() if hasattr(r,"as_float") else float(r)
        print(f"    generator[{i:>2}] (block {'g2' if i<14 else 'L' if i<21 else 'R'}): residual = {rf:.3e}")
    except Exception as e:
        print(f"    generator[{i:>2}]: {type(e).__name__}: {e}")

# (3) order-3 of the 28x28 automorphism tau (tau^3 == I ?)
try:
    tau = triality.triality_automorphism()
    t2 = so8.mat_matmul(tau, tau); t3 = so8.mat_matmul(t2, tau)
    # deviation of tau^3 from identity: compare to tau^0 by Frobenius of (t3 - I) via list diff
    import itertools
    n = 28
    dev = 0.0
    for r in range(n):
        for c in range(n):
            v = t3[r][c]; v = v.as_float() if hasattr(v,"as_float") else float(v)
            dev += (v - (1.0 if r==c else 0.0))**2
    print(f"\n(3) automorphism order-3: ||tau^3 - I||_F^2 = {dev:.3e}  (0 => tau is exactly order-3)")
except Exception as e:
    print(f"\n(3) tau order-3: {type(e).__name__}: {e}")

print("\n(reading) If (1)-(3) hold: the octonion PRODUCT genuinely realises the order-3 triality {x, y, x*y}")
print("  -> the addressing's two stored octonions (2D_oct) + the cd_mult time-stream that produces their")
print("  product = ONE triality per step. So (2+1)=k=3 is NOT a coincidence of count -- it is the Cartan")
print("  triality of the octonion multiply. HONEST nuance: this maps F907 IFF the 1D_t stream IS the")
print("  cd_mult coupling (F862 walk-order) -- the time is the MULTIPLY that makes the 3rd rep, not a 3rd stored dim.")

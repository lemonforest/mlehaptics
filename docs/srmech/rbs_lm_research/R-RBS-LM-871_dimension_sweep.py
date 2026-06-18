"""F871: don't pick a random dim. Measure capacity vs dimension across POWERS-OF-2 and
nearby NON-powers, and learn WHY -- no assumption that 2^n wins. D=10000 is an unattested
round decimal; the substrate is Klein-4 (Z2xZ2 = 2 bits/slot -> 'boolean belly'); CLAUDE.md
attests D=2^n (Class A). Question: does 2^n give better CAPACITY (binds before the stored-
item match-count crosses the gate), or is capacity just ~D (size), with 2^n winning only on
packing/attestation? Measure: capacity N*, N*/D, the chance baseline + its variance, speed.
srmech-native, integer match-counts (no float).
"""
import time
from srmech.amsc import hdc

def mcount(a, b): return sum(1 for x, y in zip(a.tolist(), b.tolist()) if x == y)

def capacity(D, Ngrid):
    """largest N with the target's match-count >= gate (1.3 x chance). Measured by scan."""
    chance = D // 4
    gate = (chance * 13) // 10
    key0 = hdc.klein4_random(D, seed=7); val0 = hdc.klein4_random(D, seed=9)
    target = hdc.klein4_bind(key0, val0)
    Nstar, counts = 0, {}
    for N in Ngrid:
        others = [hdc.klein4_bind(hdc.klein4_random(D, seed=1000 + i),
                                  hdc.klein4_random(D, seed=50000 + i)) for i in range(N - 1)]
        M = hdc.klein4_bundle(target, *others) if (N % 2 == 1) else hdc.klein4_bundle(
            target, *others, hdc.klein4_random(D, seed=424242))   # odd count for majority
        c = mcount(hdc.klein4_unbind(M, key0), val0)
        counts[N] = c
        if c >= gate: Nstar = N
    return chance, gate, Nstar, counts

def is_pow2(n): return (n & (n - 1)) == 0

DIMS = [1024, 4096, 8192, 16384,        # powers of 2
        1000, 5000, 10000, 12000]       # nearby non-powers (incl. the old magic 10000)
NGRID = [4, 8, 16, 24, 32, 48, 64, 96, 128]

print("=== capacity vs dimension (does 2^n win, or is it ~size?) ===")
print("  D      2^n? | chance | gate  | N* (binds<=gate) | N*/D x1000 | ms/bind")
rows = []
for D in sorted(DIMS):
    t0 = time.process_time()
    chance, gate, Nstar, counts = capacity(D, NGRID)
    dt = (time.process_time() - t0) * 1000 / sum(NGRID)
    rows.append((D, is_pow2(D), Nstar, Nstar / D * 1000, dt))
    print(f"  {D:6d}  {str(is_pow2(D)):5s}| {chance:6d} | {gate:5d} | {Nstar:6d}          | {Nstar/D*1000:8.3f}   | {dt:6.3f}")

print("\n=== capacity-per-dimension: is N*/D constant (capacity ~ D, size) or higher at 2^n? ===")
p2 = [r[3] for r in rows if r[1]]; np2 = [r[3] for r in rows if not r[1]]
print(f"  mean N*/D x1000  -- powers of 2: {sum(p2)/len(p2):.3f}   non-powers: {sum(np2)/len(np2):.3f}")

print("\n=== chance baseline + variance check (theory: chance=D/4, std=sqrt(3D/16)) ===")
import math
for D in [4096, 10000, 16384]:
    a = hdc.klein4_random(D, seed=11); b = hdc.klein4_random(D, seed=22)
    obs = mcount(a, b)
    print(f"  D={D:6d}: random-pair count {obs} vs chance {D//4} (excess {obs - D//4:+d}); pred std {math.sqrt(3*D/16):.1f}")
print("\n  (Reading the result, not assuming it, in the response.)")

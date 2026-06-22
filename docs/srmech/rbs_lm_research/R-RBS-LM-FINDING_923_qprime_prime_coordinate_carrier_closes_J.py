"""Class-J prime-coordinate carrier prototype (Qprime / PrimeVec).

srmech 0.9.0rc28, native, numpy-free. Exact-rational throughout.
Carrier = prime-exponent vector {prime: exponent}.
"""
from fractions import Fraction
import random

import srmech.amsc.primes as P
import srmech.amsc.cyclic as C
from srmech.amsc.cascade import magnitude


# ---------- carrier construction ----------
def to_vec(n):
    """Prime-exponent vector of positive int n as dict {p: e}. n>=1."""
    if n < 1:
        raise ValueError("Qprime carrier requires n >= 1")
    return {p: e for (p, e) in P.factor(n)}  # factor -> List[Tuple[int,int]]


def as_int(vec):
    """Reconstruct the int from a prime-exponent vector."""
    out = 1
    for p, e in vec.items():
        out *= p ** e
    return out


# ---------- exact carrier arithmetic ----------
def vec_multiply(a, b):
    """Class-J multiply = ADD exponents elementwise."""
    out = dict(a)
    for p, e in b.items():
        out[p] = out.get(p, 0) + e
    return out


def vec_gcd(a, b):
    """gcd = elementwise MIN over shared primes (others -> exponent 0, dropped)."""
    out = {}
    for p in a.keys() & b.keys():
        m = min(a[p], b[p])
        if m > 0:
            out[p] = m
    return out


def vec_lcm(a, b):
    """lcm = elementwise MAX over union of primes."""
    out = dict(a)
    for p, e in b.items():
        if e > out.get(p, 0):
            out[p] = e
    return out


def vec_similarity(a, b):
    """Shared-factor overlap as EXACT Fraction; collapse to float only at display.

    Cosine-style on exponent vectors over the union of primes:
        dot(a,b) / (||a|| * ||b||), all integer-exact under the radical.
    Returns Fraction(dot^2, na_sq * nb_sq) so the value is exact-rational
    (the similarity SQUARED); the displayed score takes a real sqrt at the
    human boundary only. 0 for coprime (empty shared support).
    """
    shared = a.keys() & b.keys()
    if not shared:
        return Fraction(0)
    dot = sum(a[p] * b[p] for p in shared)
    na_sq = sum(e * e for e in a.values())
    nb_sq = sum(e * e for e in b.values())
    return Fraction(dot * dot, na_sq * nb_sq)  # similarity^2, exact


def vec_overlap_minexp(a, b):
    """Alt similarity: normalized sum-of-min-exponents (Jaccard-ish), EXACT.

    sum_{shared} min(ea,eb) / sum_{union} max(ea,eb).
    """
    shared = a.keys() & b.keys()
    union = a.keys() | b.keys()
    num = sum(min(a[p], b[p]) for p in shared)
    den = sum(max(a.get(p, 0), b.get(p, 0)) for p in union)
    if den == 0:
        return Fraction(0)
    return Fraction(num, den)


# ============================================================
# VERIFICATION
# ============================================================
random.seed(20260622)

def run_verification(n_pairs=200, lo=2, hi=10_000):
    mul_ok = gcd_ok = lcm_ok = 0
    mul_round = 0
    for _ in range(n_pairs):
        a = random.randint(lo, hi)
        b = random.randint(lo, hi)
        va, vb = to_vec(a), to_vec(b)

        # round-trip carrier
        if as_int(va) == a and as_int(vb) == b:
            mul_round += 1

        # multiply: factor(a*b) == add-exponents(factor a, factor b)
        prod_vec = vec_multiply(va, vb)
        if prod_vec == to_vec(a * b):
            mul_ok += 1

        # gcd: elementwise-min == cyclic.gcd (NOT math.gcd)
        if as_int(vec_gcd(va, vb)) == C.gcd(a, b):
            gcd_ok += 1

        # lcm: elementwise-max == cyclic.lcm
        if as_int(vec_lcm(va, vb)) == C.lcm(a, b):
            lcm_ok += 1

    print(f"round-trip as_int(to_vec(n))==n : {mul_round}/{n_pairs}")
    print(f"multiply (add-exp == factor(ab)): {mul_ok}/{n_pairs}")
    print(f"gcd (min-exp == cyclic.gcd)     : {gcd_ok}/{n_pairs}")
    print(f"lcm (max-exp == cyclic.lcm)     : {lcm_ok}/{n_pairs}")
    return mul_ok, gcd_ok, lcm_ok


print("=== (2) VERIFIED ARITHMETIC ===")
run_verification(200)

# also cross-check lcm fallback a*b//gcd via cyclic.gcd matches cyclic.lcm
print()
xok = 0
for _ in range(100):
    a = random.randint(2, 5000); b = random.randint(2, 5000)
    fallback = a * b // C.gcd(a, b)
    if fallback == C.lcm(a, b):
        xok += 1
print(f"cyclic.lcm == a*b//cyclic.gcd   : {xok}/100")


# ============================================================
# (3) THE LENS
# ============================================================
print()
print("=== (3) LENS DEMO ===")

def show_sim(a, b):
    va, vb = to_vec(a), to_vec(b)
    sq = vec_similarity(va, vb)          # exact similarity^2
    jac = vec_overlap_minexp(va, vb)      # exact min/max overlap
    # collapse to float ONLY here, at display:
    cos = magnitude(float(sq)) ** Fraction(1, 2) if sq != 0 else 0.0
    cos = float(cos)
    print(f"  {a:>4}={dict(va)}  vs  {b:>4}={dict(vb)}")
    print(f"      shared primes: {sorted(va.keys() & vb.keys())}")
    print(f"      cosine sim   = {cos:.4f}   (exact sim^2 = {sq})")
    print(f"      min/max ovlp = {float(jac):.4f}   (exact = {jac})")

print("(i) shared-factor relatedness (12, 18 share {2,3}; 25 is coprime to both):")
show_sim(12, 18)   # 2^2*3 vs 2*3^2  -> related
show_sim(12, 25)   # 2^2*3 vs 5^2    -> coprime -> 0
show_sim(18, 25)   # 2*3^2 vs 5^2    -> coprime -> 0

print()
print("(ii) cyclic_period reading a recurrence/period as a relationship feature:")
# multiplicative order: 'how long until a self-repeats mod n'
# decimal expansion of 1/7 has period = order of 10 mod 7
for a, n in [(10, 7), (10, 13), (2, 11), (3, 7)]:
    if C.gcd(a % n, n) == 1:
        k = P.cyclic_period(a, n)
        print(f"  ord_{n}({a}) = {k}   (a^{k} ≡ 1 mod {n}; e.g. 1/7 decimal period = ord_7(10))")
    else:
        print(f"  ord_{n}({a}) undefined (gcd!=1)")
# concrete: 1/7 = 0.(142857), period 6 == ord_7(10)
print("  -> 1/7 = 0.142857142857...  repeating block length 6 == ord_7(10)=6")

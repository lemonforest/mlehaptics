#!/usr/bin/env python3
"""F424 — the Hurwitz/division cap at 𝕆 is a MAGNITUDE-layer phenomenon ONLY.

F423 split the octonion product three ways (SECTOR / CHIRALITY / MAGNITUDE) and
pre-stated this falsification rung: at the sedenion boundary (k=15→16) the SECTOR
(XOR index) and CHIRALITY (antisymmetric sign) should SURVIVE, but the MAGNITUDE
layer (norm multiplicativity) should BREAK (zero divisors appear).

Generic Cayley-Dickson doubling on 2^n integer tuples — exact, no FPU. Tested at
𝕆 (N=8) and 𝕊 (N=16). Result (asserted below): the three-part split localizes the
Hurwitz cap to exactly the MAGNITUDE layer — the sector/chirality structure is
indifferent to the division-algebra boundary.

Run:  <clean-venv>/bin/python R-RBS-LM-F424_sedenion_boundary_is_magnitude_layer_provenance.py
Self-contained exact integer; no srmech import required (pure algebra).
Anchor: F423 (the three-part split) · F404 (2^n / Mersenne; 𝕆 boundary) · F410 (Hopf
ladder terminates at 𝕆) · F389 (sedenion 16:15 has no division).
"""

def add(x, y): return tuple(a + b for a, b in zip(x, y))
def sub(x, y): return tuple(a - b for a, b in zip(x, y))
def neg(x): return tuple(-t for t in x)
def norm2(x): return sum(t * t for t in x)


def cd_conj(x):
    n = len(x)
    if n == 1:
        return x
    h = n // 2
    return cd_conj(x[:h]) + tuple(-t for t in x[h:])


def cd_mul(x, y):                       # (a,b)(c,d) = (a c − d* b , d a + b c*)
    n = len(x)
    if n == 1:
        return (x[0] * y[0],)
    h = n // 2
    a, b, c, d = x[:h], x[h:], y[:h], y[h:]
    return sub(cd_mul(a, c), cd_mul(cd_conj(d), b)) + add(cd_mul(d, a), cd_mul(b, cd_conj(c)))


def unit(i, N):
    v = [0] * N
    v[i] = 1
    return tuple(v)


def layers(N):
    E = [unit(i, N) for i in range(N)]
    im = range(1, N)
    sq = all(cd_mul(E[i], E[i]) == neg(E[0]) for i in im)
    anti = all(cd_mul(E[i], E[j]) == neg(cd_mul(E[j], E[i])) for i in im for j in im if i != j)

    def tgt(o):
        nz = [k for k in range(N) if o[k] != 0]
        return nz[0] if len(nz) == 1 else None
    sector = all(tgt(cd_mul(E[i], E[j])) == (i ^ j) for i in im for j in im if i != j)

    def mk(s): return tuple(((s * 7 + k * 3) % 5) - 2 for k in range(N))
    norm_ok = all(norm2(cd_mul(mk(s), mk(s + 11))) == norm2(mk(s)) * norm2(mk(s + 11)) for s in range(8))
    return E, sq, anti, sector, norm_ok


def main():
    ok = {}
    for N, name in [(8, "octonion"), (16, "sedenion")]:
        E, sq, anti, sector, norm_ok = layers(N)
        print(f"\n{name} (N={N}):")
        print(f"  e_i^2 = -1                          : {sq}")
        print(f"  CHIRALITY  ε(i,j) = -ε(j,i)          : {anti}")
        print(f"  SECTOR     σ(i,j) = i XOR j          : {sector}")
        print(f"  MAGNITUDE  |xy|^2 = |x|^2 |y|^2      : {norm_ok}")
        if N == 8:
            ok['𝕆: sector ✓ chirality ✓ magnitude ✓ (division algebra)'] = sq and anti and sector and norm_ok
        if N == 16:
            x = add(E[1], E[10]); y = add(E[5], E[14]); p = cd_mul(x, y)
            zd = all(c == 0 for c in p) and norm2(x) > 0 and norm2(y) > 0
            print(f"  ZERO DIVISOR (e1+e10)(e5+e14)=0     : {zd}  (both factors nonzero)")
            # the BOUNDARY: sector + chirality SURVIVE, magnitude BREAKS
            ok['𝕊: sector ✓ chirality ✓ (SURVIVE past 𝕆)'] = sq and anti and sector
            ok['𝕊: magnitude ✗ (BREAKS — norm non-mult + zero divisor)'] = (not norm_ok) and zd

    print("\n=== F424: the Hurwitz cap at 𝕆 is a MAGNITUDE-layer phenomenon ONLY ===")
    for k, v in ok.items():
        print(f"  [{'PASS' if v else 'FAIL'}] {k}")
    allok = all(ok.values())
    print("\n  ⇒ SECTOR (XOR) + CHIRALITY (antisymmetric sign) are indifferent to the")
    print("    division-algebra boundary; only MAGNITUDE (norm multiplicativity) caps at 𝕆.")
    print("\nVERDICT:", "ALL PASS ✓" if allok else "FAILURE ✗")
    return 0 if allok else 1


if __name__ == "__main__":
    raise SystemExit(main())

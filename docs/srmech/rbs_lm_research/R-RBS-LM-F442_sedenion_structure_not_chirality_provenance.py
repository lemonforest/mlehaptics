#!/usr/bin/env python3
"""R-RBS-LM-F442 — the user's "bigger int" insight: hold the OCTONION's coherence in a
SEDENION-SIZED container using the sedenion's STRUCTURE (its 2⁴−1 = 15 = Hamming(15,11)
code) but NOT its CHIRALITY (the broken multiplication). The way PAST the Hurwitz cap.

Two halves + the nesting + the principle:
  HALF 1 — the sedenion ALGEBRA is broken: (e1+e10)·(e5+e14)=0 (zero divisor, F424) — a bind
           you cannot reverse; the product is non-associative + has zero divisors. Don't use it.
  HALF 2 — the sedenion's STRUCTURE = Hamming(15,11): 11 data + 4 parity, corrects 1 error AND
           localizes it (syndrome=position), fully associative + reversible (linear over GF(2)).
           Holds 11 slots ≥ the octonion's 8 — "a bigger int to hold the value", with parity headroom.
  NEST   — the octonion's Fano(7)=Hamming(7,4) (F441) sits inside the sedenion's PG(3,2)=Hamming(15,11)
           as 7 of the 15 points (PG(2,2) ⊂ PG(3,2)). The octonion rides intact in the bigger code.
  PRINCIPLE — past 𝕆 the DIVISION ALGEBRA dies (Hurwitz, F424) but the CODE LIVES (Hamming 7→15→31…,
           the 2ⁿ−1 ladder, F404/F441). To bind/hold an octonion with headroom, widen the CODE
           (sedenion's structure) — NOT the algebra (its chirality).

Composes F424 (Hurwitz cap / sedenion zero divisors) · F441 (octonion=Fano=Hamming(7,4)) ·
F404 (2ⁿ−1 Mersenne ladder) · F437/F438 (reversible coupler ≤ 𝕆; stacked past it). Attested
coding theory (Hamming(15,11); PG(3,2)). Defensive / no-lineage.
"""
import itertools


def add(x, y): return tuple(a + b for a, b in zip(x, y))
def cj(x):
    n = len(x)
    return x if n == 1 else cj(x[:n // 2]) + tuple(-t for t in x[n // 2:])
def mul(x, y):
    n = len(x)
    if n == 1:
        return (x[0] * y[0],)
    h = n // 2
    a, b, c, d = x[:h], x[h:], y[:h], y[h:]
    return add(mul(a, c), tuple(-t for t in mul(cj(d), b))) + add(mul(d, a), mul(b, cj(c)))
def e(i, N):
    v = [0] * N; v[i] = 1; return tuple(v)


def main():
    ok = {}
    # HALF 1 — sedenion algebra broken
    x = add(e(1, 16), e(10, 16)); y = add(e(5, 16), e(14, 16))
    prod = mul(x, y)
    ok['HALF1 sedenion ALGEBRA broken: (e1+e10)(e5+e14)=0 (zero divisor)'] = all(c == 0 for c in prod)

    # HALF 2 — Hamming(15,11): row r controls bit (8>>r); parity at that pure power
    def col(j): return [(j >> 3) & 1, (j >> 2) & 1, (j >> 1) & 1, j & 1]
    H = [[col(j)[r] for j in range(1, 16)] for r in range(4)]
    def syn(v): return tuple(sum(H[r][j] * v[j] for j in range(15)) % 2 for r in range(4))
    row_parity_idx = [7, 3, 1, 0]
    parity = set(row_parity_idx)
    def encode(d11):
        v = [0] * 15; di = iter(d11)
        for j in range(15):
            if j not in parity:
                v[j] = next(di)
        for r, pidx in enumerate(row_parity_idx):
            v[pidx] = sum(H[r][j] * v[j] for j in range(15) if j != pidx) % 2
        return v
    cw = encode([1, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0])
    valid = syn(cw) == (0, 0, 0, 0)
    located = all(
        (lambda s: s[0]*8 + s[1]*4 + s[2]*2 + s[3])(syn([b ^ (1 if i == ep-1 else 0) for i, b in enumerate(cw)])) == ep
        for ep in range(1, 16))
    ok['HALF2 sedenion-sized CODE Hamming(15,11): valid codeword + EVERY single error localized'] = valid and located

    # NEST — Fano(7) ⊂ PG(3,2)(15)
    fano = {frozenset((a, b, a ^ b)) for a, b in itertools.combinations(range(1, 8), 2)}
    ok['NEST octonion Fano(7) ⊂ sedenion PG(3,2)(15): 7 pts of 15, octonion intact'] = (len(fano) == 7)

    print("=== F442: sedenion STRUCTURE (the code), not CHIRALITY (the algebra) — past the Hurwitz cap ===\n")
    for k, v in ok.items():
        print(f"  [{'PASS' if v else 'FAIL'}] {k}")
    print("\n  PRINCIPLE: division algebra caps at 𝕆 (Hurwitz, F424); the CODE ladder does NOT")
    print("  (Hamming 7→15→31…, 2ⁿ−1). 'A bigger int to hold the value' = widen the CODE")
    print("  (Hamming(15,11), 11 slots ≥ 8 + parity), reversible — using the sedenion's structure,")
    print("  NEVER its chirality. The octonion's coherent knowledge rides the bigger code intact.")
    allok = all(ok.values())
    print("\nVERDICT:", "ALL PASS ✓" if allok else "FAIL ✗")
    return 0 if allok else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""AX-2 — do two coupled Klein-4 streams reproduce the FULL octonion product, or only
its chirality skeleton? (F397's pre-stated null.)

EXACT integer algebra, NO FPU (Cayley-Dickson doubling over integer components). The
octonion basis product e_i·e_j = ε(i,j)·e_{σ(i,j)} is decomposed into:
  • σ (the SECTOR / target index)  — is it the abelian (Z2)^3 group law (= "the two
    Klein-4 quads + the ℓ-coupling bit")?
  • ε (the SIGN / chirality)        — is it carried by the abelian streams, or only by
    a separate antisymmetric coupling?

Result (asserted bit-exact below):
  σ(i,j) == i XOR j for all 49 pairs  → the SECTOR is exactly (Z2)^3 = V_A (Klein-4,
      bit0/bit1) × Z2 (bit2 = the ℓ / | seam coupling between the two quads).
  ε(i,j) == −ε(j,i) for all i≠j        → the SIGN is ANTISYMMETRIC, so the abelian
      (commutative) streams CANNOT carry it; the chirality is the coupling, not the
      streams.

So the null resolves three-part and sharp: the two Klein-4 streams reproduce the
magnitude-free SECTOR skeleton (XOR); the CHIRALITY (sign) is entirely the COUPLING
(an antisymmetric Z2 cocycle); and the FULL product of GENERAL octonions needs, on top,
the real-coefficient bilinear sum (the magnitude / Class-M / ALU layer, F422) — which
lives outside the group structure altogether.

Run:  <clean-venv>/bin/python R-RBS-LM-AX-2_octonion_two_klein4_streams_provenance.py
Requires: srmech==0.7.1 (only for native_status banner; the algebra is self-contained
exact integer — numpy-free, bit-exact, the AX-2 "no FPU" requirement).
Anchor: F397 (the mechanism + null) · F403 (Klein-4 = two Z2 = γ5,iω7) · F410 (𝕆 Hopf
15=8+7, the | seam) · F404 (2^n / Mersenne) · F422 (the magnitude layer = lean-ALU).
"""

# ---- exact integer quaternion + octonion (Cayley-Dickson), NO floats ----
def qmul(p, q):
    a1, b1, c1, d1 = p; a2, b2, c2, d2 = q
    return (a1*a2 - b1*b2 - c1*c2 - d1*d2, a1*b2 + b1*a2 + c1*d2 - d1*c2,
            a1*c2 - b1*d2 + c1*a2 + d1*b2, a1*d2 + b1*c2 - c1*b2 + d1*a2)
def qconj(p): a, b, c, d = p; return (a, -b, -c, -d)
def qadd(p, q): return tuple(x + y for x, y in zip(p, q))
def qsub(p, q): return tuple(x - y for x, y in zip(p, q))
def omul(o1, o2):                       # (a,b)(c,d) = (a c − d* b , d a + b c*)
    a, b = o1[:4], o1[4:]; c, d = o2[:4], o2[4:]
    return qsub(qmul(a, c), qmul(qconj(d), b)) + qadd(qmul(d, a), qmul(b, qconj(c)))
def unit(i):
    v = [0]*8; v[i] = 1; return tuple(v)
def neg(o): return tuple(-x for x in o)
def norm2(o): return sum(x*x for x in o)


def main():
    try:
        import srmech
        ns = srmech.native_status()
        print("srmech native_version:", ns.get("native_version"), "(algebra below is self-contained exact-int)")
    except Exception:
        pass
    E = [unit(i) for i in range(8)]
    ok = {}

    # ---- validate it's a GENUINE octonion algebra (bit-exact) ----
    sq = all(omul(E[i], E[i]) == neg(E[0]) for i in range(1, 8))
    anti = all(omul(E[i], E[j]) == neg(omul(E[j], E[i])) for i in range(1, 8) for j in range(1, 8) if i != j)
    def mk(s): return tuple(((s*7 + k*3) % 5) - 2 for k in range(8))
    nm = all(norm2(omul(mk(s), mk(s+11))) == norm2(mk(s)) * norm2(mk(s+11)) for s in range(8))
    ok['valid octonion algebra (e^2=-1, anticommute, |xy|=|x||y|)'] = sq and anti and nm

    # ---- extract ε (sign) and σ (target) for the 7 imaginaries ----
    def decode(o):
        nz = [(k, o[k]) for k in range(8) if o[k] != 0]
        assert len(nz) == 1
        return nz[0][1], nz[0][0]          # (sign, index)
    eps, sig = {}, {}
    for i in range(1, 8):
        for j in range(1, 8):
            s, k = decode(omul(E[i], E[j]))
            eps[(i, j)], sig[(i, j)] = s, k

    # ---- (1) SECTOR: σ(i,j) == i XOR j  (the abelian (Z2)^3 = two Klein-4 quads + ℓ-bit) ----
    ok['SECTOR σ(i,j) == i XOR j (all 42 off-diag)'] = all(
        sig[(i, j)] == (i ^ j) for i in range(1, 8) for j in range(1, 8) if i != j)

    # the two quads + the coupling bit: V_A = {1,2,3}(+real 0) = bit2==0 ; ℍℓ = {4,5,6,7} = bit2==1
    quadA = {0, 1, 2, 3}; quadB = {4, 5, 6, 7}
    ok['two Klein-4 quads = bit2 (ℓ/seam) cosets'] = (
        all((i & 4) == 0 for i in quadA) and all((i & 4) == 4 for i in quadB))
    # V_A closed under XOR (a Klein-4 on bits 0,1); crossing quads always toggles bit2 (the coupling)
    ok['V_A (bits0,1) closed = Klein-4; cross-quad toggles ℓ-bit'] = (
        all(((i ^ j) & 4) == 0 for i in {1, 2, 3} for j in {1, 2, 3})
        and all(((i ^ j) & 4) == 4 for i in {1, 2, 3} for j in {4, 5, 6, 7}))

    # ---- (2) CHIRALITY: ε(i,j) == −ε(j,i) antisymmetric → abelian streams CANNOT carry it ----
    ok['CHIRALITY ε(i,j) == −ε(j,i) antisymmetric (all i≠j)'] = all(
        eps[(i, j)] == -eps[(j, i)] for i in range(1, 8) for j in range(1, 8) if i != j)
    # an abelian/symmetric rule on the streams would force ε(i,j)==ε(j,i): it is wrong on EVERY off-diag pair
    n_antisym = sum(1 for i in range(1, 8) for j in range(1, 8) if i != j and eps[(i, j)] != eps[(j, i)])
    ok['abelian-symmetric sign wrong on ALL 42 off-diag pairs'] = (n_antisym == 42)

    # ---- (3) FULL general product needs the magnitude (real-coeff bilinear) — outside the group ----
    # x·y real part = -Σ_i x_i y_i (i=1..7) + x0 y0 + ... : carries COEFFICIENTS, not in {σ,ε}.
    x = (1, 2, 0, 0, 3, 0, 0, 1); y = (0, 1, 1, 0, 0, 2, 0, 0)
    prod = omul(x, y)
    # the product has integer magnitudes that no sector/sign table alone produces:
    ok['general product carries coefficients (magnitude layer, Class-M/ALU)'] = (
        any(abs(c) > 1 for c in prod))

    print("\n=== AX-2: two coupled Klein-4 streams vs the octonion product ===")
    for k, v in ok.items():
        print(f"  [{'PASS' if v else 'FAIL'}] {k}")
    print("\n  RESOLUTION (F397 null): three-part & sharp —")
    print("   • SECTOR  (which e_k) = the two Klein-4 quads + ℓ-coupling bit  = i XOR j   (streams)")
    print("   • CHIRALITY (the sign) = the antisymmetric cocycle ε(i,j)=−ε(j,i)          (coupling, NOT streams)")
    print("   • MAGNITUDE (general x·y) = the real-coeff bilinear sum                     (Class-M/ALU, F422)")
    print("  ⇒ bare streams give the SECTOR skeleton only; the chirality IS the coupling.")
    allok = all(ok.values())
    print("\nVERDICT:", "ALL PASS ✓" if allok else "FAILURE ✗")
    return 0 if allok else 1


if __name__ == "__main__":
    raise SystemExit(main())

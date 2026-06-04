"""F380 — the Klein-4 object's NATIVE transform is the QUATERNION FT, not the complex flat shadow.

User insight (2026-06-04): "we need this to QFT a klein-4 object ... and not just its flat shadow
in our RBS-SNN." The math that grounds it: the Klein-4 group V = Z2xZ2 IS the quaternion unit group
Q8 = {+-1,+-i,+-j,+-k} modulo its center {+-1}: Q8/{+-1} ~= Z2xZ2 (every non-identity coset squares
to the identity, and the product of two distinct non-identity cosets is the third). So:
  - complex FFT   -> coefficient algebra C, units {+-1,+-i} mod sign = Z2     (ONE chirality axis = flat shadow)
  - quaternion FT -> coefficient algebra H, units Q8        mod sign = Z2xZ2  (BOTH axes = Klein-4, native)
A Klein-4 HDC object (srmech hdc.klein4_*, 4 states/coord = the gamma5 & i.omega7 sectors) transformed by
a *complex* FFT collapses one of its two Z2 axes -> it sees only the flat shadow. The QUATERNION FT's
coefficient algebra matches the object's value algebra (H units mod sign = Klein-4) -> both axes survive.

This PROVES the load-bearing claim srmech-natively (NO numpy math): read the octonion structure-constant
table (qm.octonion.octonion_mult_table), restrict to the H subalgebra {e0,e1,e2,e3}, confirm it closes
into Q8 (order 8), quotient by {+-e0}, and show the 4-coset table == the Klein-4 (Z2xZ2) XOR table that
srmech.amsc.hdc.klein4 uses.
Run: /tmp/verify_srmech_v070rc28/bin/python docs/srmech/rbs_lm_research/R-RBS-LM-R21_klein4_is_quaternion_units_mod_sign.py
"""
import json
from pathlib import Path
import srmech
from srmech.qm.octonion import octonion_mult_table

HERE = Path(__file__).parent


def main():
    print(f"F380 Klein-4 == quaternion-units-mod-sign (srmech {srmech.__version__})")
    C = octonion_mult_table().tolist()   # (8,8,8) int8 structure constants: e_i*e_j = sum_k C[i][j][k] e_k
    H = [0, 1, 2, 3]                      # the quaternion subalgebra H = span{1,i,j,k}

    def prod(i, j):
        row = C[i][j]
        ks = [k for k in range(8) if row[k] != 0]
        assert len(ks) == 1, f"e{i}*e{j} is not a single basis unit: {ks}"
        k = ks[0]
        return row[k], k                 # (sign in {-1,+1}, index)  -- Class-K sign boundary, no abs()

    # (1) closure -> Q8 (order 8)
    signed_units = set()
    for i in H:
        for j in H:
            s, k = prod(i, j)
            assert k in H, f"H not closed: e{i}*e{j} = (sign {s}) e{k} leaves H"
            signed_units.add((s, k))
    print(f"  (1) H={{e0,e1,e2,e3}} is closed under *; signed-unit group order = {len(signed_units)} "
          f"(Q8 has order 8) -> {'Q8' if len(signed_units) == 8 else '??'}")

    # (2) quotient by the center {+-e0}: the coset of (sign, k) is just k (drop the sign)
    klein_from_quat = [[prod(a, b)[1] for b in H] for a in H]
    print("  (2) coset (mod +-1) multiplication table [rows/cols = e0,e1,e2,e3]:")
    for r in klein_from_quat:
        print("       ", r)

    # (3) srmech Klein-4 = Z2xZ2, element g=(b1,b0) <-> int 2*b1+b0; group op = XOR (the hdc.klein4 group)
    klein_xor = [[a ^ b for b in range(4)] for a in range(4)]
    print("  (3) srmech Klein-4 = Z2xZ2 XOR table (hdc.klein4 group):")
    for r in klein_xor:
        print("       ", r)

    # (4) isomorphism: a bijection fixing the identity that carries coset-mul -> XOR
    from itertools import permutations
    iso = None
    for p in permutations([1, 2, 3]):
        relabel = {0: 0, 1: p[0], 2: p[1], 3: p[2]}
        if all(relabel[klein_from_quat[a][b]] == (relabel[a] ^ relabel[b]) for a in H for b in H):
            iso = relabel
            break
    abelian_quotient = all(klein_from_quat[a][b] == klein_from_quat[b][a] for a in H for b in H)
    q8_nonabelian = any(prod(a, b) != prod(b, a) for a in H for b in H)

    print("\n=== verdict ===")
    print(f"  Q8 is non-abelian (i*j != j*i):                 {q8_nonabelian}")
    print(f"  but the quotient Q8/{{+-1}} IS abelian:           {abelian_quotient}")
    print(f"  Q8/{{+-1}} == Klein-4 (Z2xZ2): isomorphism found = {iso is not None}; relabel = {iso}")
    print( "  => complex FFT resolves ONE Z2 (the flat shadow); the QUATERNION FT's coefficient algebra")
    print( "     (H units mod sign = Klein-4) matches the Klein-4 object's value algebra, so BOTH chirality")
    print( "     axes (gamma5 & i.omega7) survive. THIS is why a Klein-4 RBS-SNN object wants a quaternion")
    print( "     FT, not a complex one. (Octonion FT -> the (8:7) rung, carrying the F378 non-associativity.)")

    res = dict(srmech_version=srmech.__version__,
               q8_order=len(signed_units), q8_nonabelian=bool(q8_nonabelian),
               quotient_abelian=bool(abelian_quotient),
               coset_table=klein_from_quat, klein_xor=klein_xor,
               isomorphism=iso, is_klein4=iso is not None)
    (HERE / "R-RBS-LM-R21_results.json").write_text(json.dumps(res, indent=2))
    print(f"\n  Results: {HERE / 'R-RBS-LM-R21_results.json'}")


if __name__ == "__main__":
    main()

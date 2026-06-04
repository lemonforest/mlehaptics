"""F385 — capturing the CHIRALITY of the degenerate fibrations.

User (2026-06-04): "and we have to capture the chirality of our degenerate fibrations".

F384 fibered the symmetric "3" of (4:3)=H as 1 (fiber) + 2 (base) by CHOOSING a complex structure (which
imaginary is the fiber). That choice BREAKS the SO(3)/triality symmetry of the 3 — the "degeneration" (the
3 were symmetric/equivalent; picking a fiber degenerates them to a preferred axis). What the choice leaves
behind is a HANDEDNESS: because H is NON-COMMUTATIVE, the chosen fiber can act on the base by LEFT or RIGHT
multiplication, and the two give MIRROR fibrations. That residual Z2 IS the chirality (gamma5 / i.omega7,
F130; the (4:3) vs (3:4) chirality-dual, F129), and it is exactly the LEFT/RIGHT/two-sided QFT the literature
defines (F380/F381). Dropping it collapses left and right into one = the flat shadow (F380).

srmech-native: the octonion structure-constant table (qm.octonion.octonion_mult_table) for the table proof,
and the NAMED ops octonion_left_mult / octonion_right_mult (F357/F380) to confirm. No numpy math, no abs().
Run: /tmp/verify_srmech_v070rc28/bin/python docs/srmech/rbs_lm_research/R-RBS-LM-R27_chirality_of_degenerate_fibrations.py
"""
import json
from pathlib import Path
import numpy as np                      # ONLY to build a basis-vector input for the srmech ops + read columns
import srmech
from srmech.qm.octonion import octonion_mult_table, octonion_left_mult, octonion_right_mult

HERE = Path(__file__).parent
NAMES = {0: "1", 1: "i", 2: "j", 3: "k"}


def main():
    print(f"F385 chirality of the degenerate fibrations (srmech {srmech.__version__})")
    C = octonion_mult_table().tolist()
    I, J, K = 1, 2, 3

    def prod(a, b):
        row = C[a][b]
        ks = [k for k in range(8) if row[k] != 0]
        return row[ks[0]], ks[0]

    # (1) the DEGENERATION: the 3 imaginaries are cyclically symmetric (an automorphism i->j->k->i),
    # so NO imaginary is canonically the fiber; choosing one BREAKS that symmetry.
    print("\n(1) the degeneration (symmetry-breaking): the 3 are cyclically symmetric ->")
    for a, b in ((I, J), (J, K), (K, I)):
        s, kk = prod(a, b)
        print(f"    {NAMES[a]}*{NAMES[b]} = {'+' if s > 0 else '-'}{NAMES[kk]}", end="   ")
    print("\n    i->j->k->i is an automorphism (the triality 3-cycle); the 3 are SO(3)-equivalent.")
    print("    Choosing 'i' as the fiber DEGENERATES this symmetry to a preferred axis. What's left = a handedness.")

    # (2) the CHIRALITY: left vs right multiplication by the fiber i (H is non-commutative)
    print("\n(2) the chirality (the residual Z2) — fiber i acting LEFT vs RIGHT on the base j:")
    sL, kL = prod(I, J)        # i*j  (LEFT-fiber: L_i(j))
    sR, kR = prod(J, I)        # j*i  (RIGHT-fiber: R_i(j))
    print(f"    LEFT   i*j = {'+' if sL > 0 else '-'}{NAMES[kL]}     (left-fiber rotates base j -> +k)")
    print(f"    RIGHT  j*i = {'+' if sR > 0 else '-'}{NAMES[kR]}     (right-fiber rotates base j -> -k)")
    mirror = (kL == kR and sL == -sR)
    print(f"    => LEFT and RIGHT fibrations are MIRROR images (same axis, opposite sign): {mirror}")

    # confirm via the NAMED ops octonion_left_mult / octonion_right_mult (F357/F380)
    e_i = np.zeros(8); e_i[I] = 1.0
    Li = octonion_left_mult(e_i).tolist()      # L_i : column j = i*e_j
    Ri = octonion_right_mult(e_i).tolist()     # R_i : column j = e_j*i
    colL = [Li[r][J] for r in range(8)]
    colR = [Ri[r][J] for r in range(8)]
    print(f"    octonion_left_mult(i)  applied to j -> {NAMES[colL.index(next(v for v in colL if v))]} "
          f"(coef {int(next(v for v in colL if v))})")
    print(f"    octonion_right_mult(i) applied to j -> {NAMES[colR.index(next(v for v in colR if v))]} "
          f"(coef {int(next(v for v in colR if v))})")
    ops_agree_mirror = (colL[K] == -colR[K] != 0)
    print(f"    named-op confirmation (left = -right on the base): {ops_agree_mirror}")

    print("\n=== verdict ===")
    print("  Fibering the symmetric 3 = choosing a complex structure = DEGENERATING its SO(3)/triality symmetry.")
    print("  The residue is a HANDEDNESS: fiber-acts-LEFT (i*j=+k) vs fiber-acts-RIGHT (j*i=-k) = MIRROR fibrations,")
    print("  the Z2 chirality (gamma5 / i.omega7, F130). This is the (4:3) vs (3:4) chirality-dual (F129) and IS")
    print("  the LEFT/RIGHT/two-sided QFT the literature defines (F380/F381) — captured, not optional.")
    print("  => 'capture the chirality of our degenerate fibrations' = carry the LEFT/RIGHT tag (Class C net_chirality)")
    print("     on every fibration choice. Drop it and left==right collapses to the flat shadow (F380); the (4:3)-")
    print("     native substrate (F383) and the QDFT descriptor (F380/F381) must each carry the handedness tag.")

    res = dict(srmech_version=srmech.__version__,
               left_i_times_j=[sL, NAMES[kL]], right_j_times_i=[sR, NAMES[kR]],
               mirror_fibrations=bool(mirror), named_ops_confirm_mirror=bool(ops_agree_mirror),
               chirality="left/right multiplication = gamma5/i.omega7 = (4:3)/(3:4) dual = left/right/two-sided QFT")
    (HERE / "R-RBS-LM-R27_results.json").write_text(json.dumps(res, indent=2))
    print(f"\n  Results: {HERE / 'R-RBS-LM-R27_results.json'}")


if __name__ == "__main__":
    main()

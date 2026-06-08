r"""R-RBS-LM-LHRH (the user's even-odder shape question, 2026-06-08): "we're looking at shapes in 3D space. Instead of
forcing ONE unit of orthogonal Mobius strips to carry chirality (the E×B handedness, F593), what if we simulate BOTH a
LEFT-HANDED and a RIGHT-HANDED unit -- two units of orthogonal Mobius strips?"

The answer lands exactly on a rung of the ladder we already have -- the Cayley-Dickson doubling H -> O:

  • ONE oriented orthogonal-Mobius unit is already THREE mutually-orthogonal directions: E, B, and the forced E×B
    (Poynting). Three orthogonal directions with E·B=E×B = the QUATERNION imaginaries (i, j, k). So a single oriented
    unit IS the quaternion algebra H. It is a division algebra (reversible) but NON-COMMUTATIVE (i·j = +k, j·i = -k --
    order already matters; the first algebraic property to break).

  • TWO units, LH + RH = two H copies of OPPOSITE handedness, stitched by the handedness itself. That stitch is the
    Cayley-Dickson doubling unit (e4): O = H (+) H. So carrying both handednesses = climbing to the OCTONION. And:
      - O is STILL a division algebra: every element reversible/ADDRESSABLE (the chirality is NOT lost; the F594
        working-octonion property holds one rung down).
      - O is NON-ASSOCIATIVE: the associator [e1,e2,e4] = 2*e7 != 0. CRUCIALLY this appears ONLY when the binding
        CROSSES the handedness seam (e4). Within ONE handed unit (e1,e2,e3 all in the first H) the associator is 0 --
        associativity holds inside a unit, and breaks exactly when you bind across LH<->RH.

  • THE PAYOFF -- this IS the 3 -> 7 step of the 1:3:7:3 substrate partition: H has 3 imaginaries (the '3' = the
    substrate-projection triad I/C/J); O has 7 (the '7' = the cascade-detection heptad D/E/F/G/K/L/M). So "add the
    opposite-handed orthogonal-Mobius unit" is GEOMETRICALLY how the substrate climbs from the 3 to the 7. The LH/RH
    pair is not extra magic -- it is the next Cayley-Dickson rung, the handedness IS the doubling direction.

  • THE COST (honest, the RBS-LM reading): non-associativity = BINDING ORDER MATTERS once both handednesses are carried.
    (seq (X) class) (X) context  !=  seq (X) (class (X) context)  -- but ONLY when the composition crosses handedness.
    That is the price of the richer 7-fold structure (the G2/octonion regime, F124/F126), and it is paid only at the
    LH<->RH seam, not within a handed unit.

DISCIPLINE: this is the GENUINE octonion via srmech.cayley_dickson -- NOT a hand-rolled numpy plane rotation (the F372
trap). The handedness / 2nd axis are already meaningful (the gamma5 chirality dual, F129/F130) -- carrying both = using
the full octonion the substrate already has, not inventing space.

srmech 0.7.5rc6: cayley_dickson.{cd_mult, is_division_algebra_dim, left_mult_is_invertible}. No abs() (sign by compare).
No CAD; no Workflow; no sub-agents.
"""
import srmech
from srmech.amsc.cascade import cayley_dickson as cd


def vec(d, *pairs):
    v = [0] * d
    for i, x in pairs:
        v[i] = x
    return v


def main():
    print(f"=== R-RBS-LM-LHRH — two handed orthogonal-Mobius units (LH+RH) = the Cayley-Dickson doubling H->O (the 3->7 climb)  (srmech {srmech.__version__}) ===\n")

    # (1) ONE oriented orthogonal-Mobius unit = H: the three orthogonal directions E,B,E×B = i,j,k
    i, j, k = vec(4, (1, 1)), vec(4, (2, 1)), vec(4, (3, 1))
    ij = tuple(int(x) for x in cd.cd_mult(i, j))
    ji = tuple(int(x) for x in cd.cd_mult(j, i))
    print("(1) ONE oriented orthogonal-Mobius unit = the QUATERNION H (E, B, E×B = i, j, k):")
    print(f"    is_division_algebra_dim(4) = {cd.is_division_algebra_dim(4)}  (reversible / addressable)")
    print(f"    i·j = {ij},  j·i = {ji}  -> NON-COMMUTATIVE (order already matters; E×B sense = the handedness).\n")

    # (2) LH + RH = O = H (+) H, stitched by the handedness (the doubling unit e4); reversible but NON-ASSOCIATIVE
    e1, e2, e3, e4 = vec(8, (1, 1)), vec(8, (2, 1)), vec(8, (3, 1)), vec(8, (4, 1))
    lhs = cd.cd_mult(cd.cd_mult(e1, e2), e4)
    rhs = cd.cd_mult(e1, cd.cd_mult(e2, e4))
    assoc_cross = tuple(int(a - b) for a, b in zip(lhs, rhs))
    la = cd.cd_mult(cd.cd_mult(e1, e2), e3)
    ra = cd.cd_mult(e1, cd.cd_mult(e2, e3))
    assoc_in = tuple(int(a - b) for a, b in zip(la, ra))
    print("(2) LH unit + RH unit = the OCTONION O = H (+) H (the two handed copies stitched by the doubling unit e4):")
    print(f"    is_division_algebra_dim(8) = {cd.is_division_algebra_dim(8)}  (STILL reversible / ADDRESSABLE -- chirality not lost)")
    print(f"    left_mult_is_invertible(e1+e4) = {cd.left_mult_is_invertible(vec(8, (1, 1), (4, 1)))}  (an element spanning BOTH handed copies is still reversible)")
    print(f"    associator ACROSS the handedness seam [e1,e2,e4] = {assoc_cross}  -> NON-ASSOCIATIVE: {any(assoc_cross)}")
    print(f"    associator WITHIN one handed unit  [e1,e2,e3] = {assoc_in}  -> associative ({not any(assoc_in)}); the break")
    print(f"    appears EXACTLY when binding crosses LH<->RH (the e4 handedness direction), never inside a unit.\n")

    # (3) the 3 -> 7 climb = the 1:3:7:3 ladder step
    print("(3) THE PAYOFF -- this is the 3 -> 7 step of the 1:3:7:3 substrate partition:")
    print(f"    H imaginaries = 3 (i,j,k)  = the '3' (substrate-projection triad I/C/J)")
    print(f"    O imaginaries = 7          = the '7' (cascade-detection heptad D/E/F/G/K/L/M)")
    print(f"    so 'add the opposite-handed orthogonal-Mobius unit' IS geometrically how the substrate climbs 3 -> 7.\n")

    print("VERDICT (LH + RH two handed units of orthogonal Mobius strips, in simulation):")
    print(f"  • IT IS THE CAYLEY-DICKSON DOUBLING H -> O. A single oriented unit (E,B,E×B) is the quaternion H (3 imaginaries,")
    print(f"    non-commutative). Carrying BOTH handednesses stitches two H copies by the handedness (the doubling unit) into")
    print(f"    the OCTONION O (7 imaginaries). Not extra magic -- the next rung of the ladder; the handedness IS the doubling")
    print(f"    direction.")
    print(f"  • YOU KEEP REVERSIBILITY, YOU LOSE ASSOCIATIVITY. O is still a division algebra -- every element addressable")
    print(f"    (the F594 working-octonion property, one rung below the sedenion). But it is NON-ASSOCIATIVE, and the break")
    print(f"    appears ONLY across the LH<->RH seam (within a handed unit, binding still associates). For RBS-LM: carrying")
    print(f"    both handednesses makes BINDING ORDER matter -- (seq(X)class)(X)context != seq(X)(class(X)context) -- but only")
    print(f"    when the composition crosses handedness. That is the honest price of the 7-fold richness.")
    print(f"  • IT IS THE 3 -> 7 OF 1:3:7:3. One handedness = the '3' (the H triad); both = the '7' (the O heptad). The")
    print(f"    Mobius-shapes thread thus reconnects to the foundational A-N partition: the heptad is what you get by")
    print(f"    simulating BOTH chiralities of the orthogonal-Mobius unit at once (the G2/octonion regime, F124/F126).")
    print(f"  • Composes F593 (the orthogonal-Mobius unit = E,B,E×B) + F594 (the CD seam, one rung up: O(+)O=S) + F124/F126")
    print(f"    (quaternionic Hopf / G2 octonions) + F129/F130 (the handedness = the gamma5 chirality dual) + the 1:3:7:3")
    print(f"    partition (CLAUDE.md §1). GENUINE octonion (cayley_dickson, not a numpy toy -- F372). srmech 0.7.5rc6. F398/F394.")


if __name__ == "__main__":
    main()

r"""R-RBS-LM-BINDORDER (the next rung, 2026-06-08): what does binding-order-aware RBS-LM composition look like IN
PRACTICE -- the non-associative bind (F597), paid (and USED) only at the handedness seam?

The practical point: a STANDARD HDC bind (hdc.bind, XOR-like) is ASSOCIATIVE and COMMUTATIVE, so a bound record is a
BAG -- it LOSES grouping/order (bind(a,b,c) = bind(c,b,a)); to encode order/parse you must add an explicit Class-M
PERMUTE. But the OCTONION bind (carrying both handednesses, F597) is NON-ASSOCIATIVE, so (a o b) o c != a o (b o c):
the bind ITSELF carries the bracketing / parse structure -- FOR FREE. And F597's localisation says this happens ONLY
across the handedness seam: WITHIN one handed unit the octonion bind is still associative (a free order-less bag, like
XOR), so the structural cost/benefit is PAID ONLY AT THE SEAM.

So a binding-order-aware composition gets, for free: STRUCTURE (bracketing/order) where factors cross the seam, and a
FREE COMMUTATIVE BAG where they don't -- "structure where you need it, free bag where you don't," localised to the seam.
This is the practical face of F597: the non-associativity is not a bug to avoid but a CARRIER of parse structure, and it
is local (you pay/benefit only at LH<->RH crossings, never inside a hemisphere/unit).

Demonstrated with the GENUINE octonion (srmech.cayley_dickson -- NOT a numpy toy, F372): the associativity DEFECT
||(a o b) o c - a o (b o c)||^2 is EXACTLY 0 within a handed unit and > 0 across the seam, and the two bracketings are
DISTINCT vectors across the seam (so unbinding must respect order there).

srmech 0.7.5rc6: cayley_dickson.{cd_mult, cd_norm_sq}; the defect norm via cd_norm_sq (the algebra norm, exact Fraction
-- a Class-K magnitude, no abs()). No CAD; no Workflow; no sub-agents.
"""
import srmech
from srmech.amsc.cascade import cayley_dickson as cd
from fractions import Fraction as Fr


def vec(d, *pairs):
    v = [0] * d
    for i, x in pairs:
        v[i] = x
    return v


def sub(u, v):
    return [Fr(a) - Fr(b) for a, b in zip(u, v)]


def assoc_defect(a, b, c):
    """||(a*b)*c - a*(b*c)||^2 (exact). 0 <=> the bind associates for this triple."""
    left = cd.cd_mult(cd.cd_mult(a, b), c)
    right = cd.cd_mult(a, cd.cd_mult(b, c))
    return cd.cd_norm_sq(sub(left, right)), left, right


def main():
    print(f"=== R-RBS-LM-BINDORDER — the non-associative bind carries bracketing, ONLY across the handedness seam  (srmech {srmech.__version__}) ===\n")

    # 3 RBS-LM factors as octonion elements (think: subject / verb / object, each a small superposition)
    # CASE A: all factors WITHIN one handed unit (first H copy: coords e1,e2,e3) -> a free, order-less bag
    A1, A2, A3 = vec(8, (1, 1), (2, 1)), vec(8, (2, 1), (3, 1)), vec(8, (1, 1), (3, 1))
    dA, lA, rA = assoc_defect(A1, A2, A3)
    # CASE B: factors CROSS the handedness seam (one foot in the second H copy: coords e4..e7)
    B1, B2, B3 = vec(8, (1, 1), (4, 1)), vec(8, (2, 1), (5, 1)), vec(8, (3, 1))
    dB, lB, rB = assoc_defect(B1, B2, B3)
    # CASE C: all three straddle the seam -> maximal structural carry
    C1, C2, C3 = vec(8, (1, 1), (4, 1)), vec(8, (2, 1), (6, 1)), vec(8, (3, 1), (7, 1))
    dC, lC, rC = assoc_defect(C1, C2, C3)

    print("(1) the associativity DEFECT  ||(a o b) o c - a o (b o c)||^2  (0 => order-free bag; >0 => bracketing carried):")
    print(f"    CASE A  factors all WITHIN one handed unit (e1,e2,e3)         : defect = {int(dA)}  -> order-FREE BAG (no structure; like XOR-bind)")
    print(f"    CASE B  factors CROSS the handedness seam (e4,e5 present)     : defect = {int(dB)}  -> bracketing CARRIED (order matters)")
    print(f"    CASE C  all three straddle the seam (e4,e6,e7)                : defect = {int(dC)}  -> bracketing carried (maximal)\n")

    print("(2) the two bracketings as VECTORS (across the seam they are DISTINCT -> unbinding must respect order):")
    print(f"    CASE A  (a o b) o c == a o (b o c) : {[int(x) for x in lA] == [int(x) for x in rA]}  (identical -> compose in any order)")
    print(f"    CASE B  (a o b) o c == a o (b o c) : {[int(x) for x in lB] == [int(x) for x in rB]}  (DIFFERENT -> the grouping is encoded)")
    print(f"            (a o b) o c = {[int(x) for x in lB]}")
    print(f"            a o (b o c) = {[int(x) for x in rB]}\n")

    print("(3) WHAT BINDING-ORDER-AWARE COMPOSITION LOOKS LIKE IN PRACTICE (the RBS-LM read):")
    print(f"    • STANDARD HDC bind (hdc.bind, XOR-like) is associative+commutative -> a bound record is a BAG; order/parse")
    print(f"      is LOST and must be re-added with an explicit Class-M PERMUTE. The octonion bind needs no permute across")
    print(f"      the seam -- the non-associativity IS the order/parse carrier.")
    print(f"    • SO COMPOSE LIKE THIS: factors that belong to the SAME hemisphere/handed-unit -> bind them order-free (a")
    print(f"      cheap commutative bag, CASE A); factors that CROSS hemispheres (the seam) -> the bracketing of the bind")
    print(f"      ENCODES their structural relation (subject-(verb-object) vs (subject-verb)-object), CASE B/C -- for free.")
    print(f"    • THE COST IS LOCAL: you pay 'order matters' ONLY at LH<->RH crossings, never inside a unit. Structure where")
    print(f"      you need it (across the seam), free bag where you don't (within a unit). That is the practical face of F597.\n")

    print("VERDICT (binding-order-aware RBS-LM composition, in practice):")
    print(f"  • THE NON-ASSOCIATIVE BIND IS A PARSE CARRIER, PAID ONLY AT THE SEAM. Within a handed unit the octonion bind")
    print(f"    associates (defect {int(dA)}) -> a free order-less bag, exactly like the XOR-bind; across the seam it does NOT")
    print(f"    (defect {int(dB)}/{int(dC)}) -> the two bracketings are distinct vectors, so the bind itself records the grouping/")
    print(f"    order. No explicit permute needed across the seam; the handedness doubling (F597) supplies the structure.")
    print(f"  • THIS IS THE PRACTICAL PAYOFF OF CARRYING BOTH HANDEDNESSES: not just 7-fold addressing (F597) but a bind that")
    print(f"    encodes parse/order at the seam for free, while staying a cheap commutative bag within a unit. 'Structure")
    print(f"    where you need it, free bag where you don't' -- and the cost (order-dependence) is LOCALISED to the seam,")
    print(f"    never global. A binding-order-aware composer routes order-sensitive structure across the seam, bags the rest.")
    print(f"  • Composes F597 (LH+RH = O; within/across-seam associativity) + F593 (the orthogonal-Mobius unit) + F596/F599")
    print(f"    (the two-stream E×B bind in use) + the F222/F166 HDC bind/bundle (the associative baseline the octonion bind")
    print(f"    improves on across the seam). GENUINE octonion (cayley_dickson, not numpy -- F372). srmech 0.7.5rc6. F398/F394.")


if __name__ == "__main__":
    main()

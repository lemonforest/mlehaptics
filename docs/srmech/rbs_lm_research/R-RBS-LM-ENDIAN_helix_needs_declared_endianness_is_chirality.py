r"""R-RBS-LM-ENDIAN (the user's refinement 2026-06-07): the helix bookshelf needs a DECLARED ENDIANNESS. The helix
(F533) is an ordered shelf of sedenion tomes, but ORDER ALONE does not say WHICH WAY to read it — start->tip or
tip->start, slot 0->6 or 6->0. Without a declared endianness, the SAME tomes reconstruct the history OR its mirror.

The framework point: ENDIANNESS = a CHIRALITY declaration (Class C, which-way). The two endiannesses ARE the two
chiral hands (sigma=+1 big-endian forward, sigma=-1 little-endian reverse, F514/F528). So the helix's reading
direction is a Class-C flag, carried on the Class-A START anchor (F533): the start says WHERE to begin, the
endianness says WHICH WAY to read. Together = complete, unambiguous addressing. The OTHER endianness is the
chiral-DUAL read (the history backward = the conjugate, F486) — valid, but not the declared canonical one.

srmech 0.7.4; SedenionRegister tomes; endianness = a declared sigma (Class C). No abs(); no CAD; no sub-agents.
"""
import srmech
from srmech.amsc.cascade import SedenionRegister

K = 7


def write_history(reg, history):
    """write the recorded history (in order) into helix tomes, 7 complexes each, forward (the writer's order)."""
    return [reg.couple_working(history[m * K:(m + 1) * K]) for m in range(len(history) // K)]


def read_helix(reg, tomes, endian):
    """read the helix with a declared ENDIANNESS (sigma): +1 = big-endian (tome 0->M, slot 0->6);
    -1 = little-endian (tome M->0, slot 6->0). Order alone is silent on this — the endianness declares it."""
    out = []
    tome_order = range(len(tomes)) if endian == +1 else range(len(tomes) - 1, -1, -1)
    for m in tome_order:
        vals = reg.uncouple_working(tomes[m])
        slots = range(K) if endian == +1 else range(K - 1, -1, -1)
        out += [round(vals[s]) for s in slots]
    return out


def main():
    print(f"=== R-RBS-LM-ENDIAN — the helix needs a DECLARED ENDIANNESS (= a Class-C chirality, the reading hand)  (srmech {srmech.__version__}) ===\n")
    reg = SedenionRegister()
    history = [i + 1 for i in range(K * 3)]                      # the recorded history, in the writer's order: 1,2,3,...,21
    tomes = write_history(reg, [float(x) for x in history])

    big = read_helix(reg, tomes, +1)                            # sigma=+1: big-endian (forward)
    little = read_helix(reg, tomes, -1)                         # sigma=-1: little-endian (reverse) = the chiral dual

    print("(1) ORDER ALONE IS AMBIGUOUS — the same tomes read two ways:")
    print(f"    writer's history (intended): {history[:7]} ... {history[-3:]}")
    print(f"    read big-endian   (sigma=+1): {big[:7]} ... {big[-3:]}   matches writer: {big == history}")
    print(f"    read little-endian(sigma=-1): {little[:7]} ... {little[-3:]}   = the history MIRRORED: {little == history[::-1]}")
    print(f"    -> without a declared endianness, a reader could reconstruct the history OR its mirror.\n")

    print("(2) THE DECLARED ENDIANNESS RESOLVES IT (carried on the Class-A START anchor):")
    declared = +1                                               # the writer DECLARES sigma=+1 on the start anchor
    recovered = read_helix(reg, tomes, declared)
    print(f"    start anchor declares endianness sigma={declared:+d} (big-endian). Reader uses it ->")
    print(f"    recovered == writer's history: {recovered == history}.  Unambiguous.\n")

    print("(3) THE TWO ENDIANNESSES ARE THE TWO CHIRAL HANDS:")
    print(f"    sigma=+1 (big-endian) and sigma=-1 (little-endian) read the SAME shelf in mirror directions —")
    print(f"    the two hands (F514/F528). The non-declared one is the chiral-DUAL read (the history backward,")
    print(f"    the conjugate F486): valid, but not the canonical history. Endianness PICKS the hand.\n")

    print("VERDICT:")
    print(f"  • THE HELIX NEEDS A DECLARED ENDIANNESS: order alone is silent on direction, so the same tomes give the")
    print(f"    history (big-endian, matches: {big == history}) OR its mirror (little-endian, matches reversed: {little == history[::-1]}).")
    print(f"    A declared endianness removes the ambiguity (recovered == writer: {recovered == history}).")
    print(f"  • ENDIANNESS = CHIRALITY (Class C, which-way): the two endiannesses ARE the two chiral hands (sigma=+-1,")
    print(f"    F514/F528). It is carried on the Class-A START anchor (F533): START says WHERE to begin, ENDIANNESS")
    print(f"    says WHICH WAY to read — together, complete unambiguous addressing of a recorded history.")
    print(f"  • The OTHER endianness is the chiral-dual (the history read backward = the conjugate, F486) — a valid")
    print(f"    mirror read, not the canonical one. So a helix is declared by (start-anchor, endianness) = (Class A, Class C).")


if __name__ == "__main__":
    main()

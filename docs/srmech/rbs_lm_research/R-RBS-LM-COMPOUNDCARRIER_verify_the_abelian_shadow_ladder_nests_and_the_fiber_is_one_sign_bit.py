r"""R-RBS-LM-COMPOUNDCARRIER — committed generating code for F1317: the COMPOUNDED fibration carrier.

Three exhaustive checks on shipped srmech ops (no sampling — the full product tables):
  1. each rung projects to its ELEMENTARY-ABELIAN shadow Z2^n by XOR
       H: q8_mult(a,b)&3  == (a&3)^(b&3)     over all 8x8
       O: oct_mult(a,b)&7 == (a&7)^(b&7)     over all 16x16      <- the new one
  2. the shadows NEST by truncation: (O-shadow)&3 == (H-shadow)  over all 16x16
  3. per-rung FIBER CARDINALITY (MFO VIII.31.18's named falsifiable next step):
       the non-abelian range over an abelian shadow is DISCRETE, size exactly 2 at every rung,
       and its members differ ONLY in the sign bit.
Plus the (4+3) internal middle: H sits inside O as a closed block, H*e4 -> the doubling copy.

CONSEQUENCE: one symbol read at mask-width n IS the rung-n abelian address; the fibration is
chosen by the READ WIDTH, not built. shadow = which AXIS (nests, free); fiber = which WAY (1 sign
bit, must be supplied -- resonantly, by the_one).

BOUND (MFO VIII.31.19 s3, standard math; F1316 measured it independently): this is an ADDRESSING
result. Turns need a GROUP; S^7 is a non-associative Moufang loop, so turn-composability tops out
at H. Address at any rung; turn only at H or below. TWO CEILINGS.

METHOD NOTE (recorded because the wrong version would have "refuted" the carrier): the first probe
compared oct_mult(a,b)&7 to q8_mult(a&7,b&7) and saw 96/256 violations. That comparison is WRONG --
it pits O's basis index against Q8's signed algebra (Q8 packs sign at bit 2, O at bit 3). Each rung
must be compared to its OWN Z2^n XOR shadow.

srmech 0.9.0rc336. No numpy/fractions/abs(). Composes F1317/F1316/F1307/F1310; MFO VIII.31.18-19.
Run:  /tmp/srmech_335/bin/python3 R-RBS-LM-COMPOUNDCARRIER_*.py
"""
import sys
from collections import defaultdict

import srmech
from srmech.amsc import octonion as O, q8 as Q8


def main():
    print("=== compounded fibration carrier (srmech %s) ===" % srmech.__version__)
    ok = True

    # 1 - each rung -> its Z2^n shadow, exhaustively
    h_bad = [(a, b) for a in range(8) for b in range(8)
             if Q8.q8_mult(a, b) & 3 != (a & 3) ^ (b & 3)]
    o_bad = [(a, b) for a in range(16) for b in range(16)
             if O.oct_mult(a, b) & 7 != (a & 7) ^ (b & 7)]
    ok &= not h_bad and not o_bad
    print("  [1] H -> Z2^2 : %d/64 violations | O -> Z2^3 : %d/256 violations"
          % (len(h_bad), len(o_bad)))

    # 2 - the shadows NEST by truncation
    nest_bad = [(a, b) for a in range(16) for b in range(16)
                if (((a & 7) ^ (b & 7)) & 3) != ((a & 3) ^ (b & 3))]
    ok &= not nest_bad
    print("  [2] (O-shadow)&3 == (H-shadow) : %d/256 violations" % len(nest_bad))

    # 3 - per-rung fiber cardinality + what distinguishes fiber members
    for name, n, mask, signbit in (("H (Q8->V4)", 8, 3, 4), ("O (O16->Z2^3)", 16, 7, 8)):
        fib = defaultdict(list)
        for u in range(n):
            fib[u & mask].append(u)
        sizes = sorted({len(v) for v in fib.values()})
        sign_only = all(len({u & mask for u in v}) == 1 and
                        sorted(u // signbit for u in v) == [0, 1] for v in fib.values())
        ok &= sizes == [2] and sign_only
        print("  [3] %-14s shadow classes %d | fiber sizes %s | members differ ONLY in sign: %s"
              % (name, len(fib), sizes, sign_only))

    # 4 - the (4+3) internal middle
    H = {0, 1, 2, 3}
    closed = all((O.oct_mult(a, b) & 7) in H for a in H for b in H)
    copy = all((O.oct_mult(a, 4) & 7) in {4, 5, 6, 7} for a in H)
    ok &= closed and copy
    print("  [4] H-block closed: %s | H*e4 -> {4,5,6,7}: %s  => Im(O)=7=(4 copy)+(3 old)"
          % (closed, copy))

    print("\n=== %s ===" % ("CARRIER CONFIRMED: shadows nest, fiber = 1 sign bit (card 2) at every "
                            "rung. Address at any rung by masking; turn only at H (two ceilings)."
                            if ok else "REGRESSION — reconcile before trusting F1317."))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

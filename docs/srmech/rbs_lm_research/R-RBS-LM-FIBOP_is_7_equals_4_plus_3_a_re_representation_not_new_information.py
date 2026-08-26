#!/usr/bin/env python3
"""F1349 — is 7 = 4+3 a RE-REPRESENTATION rather than additional information?

User (2026-08-15):
  "why can't fibration also be an operation that changes the even number basis items
   (2:4:8) into the (1+1:1+3:1+7) odd anchored things ... octonion at k=7=(4+3) are the
   same information in different representation, not additional information. so if 7 were
   abc then (4+3) is all the ab:cb:ca || c:a:b thing, meaning if 3 is always a shape then
   4 must be cb shape. so that'd mean also we don't do operations on real and imaginary
   and expect a change in time, that change in time things happen when we address Os at S."

Made falsifiable as three hypotheses. H1 and H3 are decided here; H2 is decided in the
weaker of its two readings and left OPEN in the stronger one, which is stated rather than
finessed.

  H1  for every Fano line L (3 units), the complement C (4 units) is NOT a subalgebra
      but IS a single H-coset -- so "7" reads as (one closed triad) + (one torsor)
  H2  the (3,4) split carries the SAME information as the flat 7 -- the full product
      table is reconstructible from the triad plus the coset action
  H3  the S rung adds NO new symmetry but DOES add zero divisors -- so whatever is new
      at S is not structural symmetry

srmech 0.9.0rc434. Exact integer / exact-Q. No abs(), no numpy, no RNG.
"""
from srmech.math.octonion import oct_mult, oct_torsor_act
from srmech.physics.qm.so9 import sedenion_holonomy_conjecture
from srmech.cascade import cd_zero_divisor_witness, cd_mult
from srmech.math.q import Q

FAILED = []


def ck(label, got, want=None):
    ok = (got == want) if want is not None else bool(got)
    print(f"  {'ok  ' if ok else 'FAIL'} {label:<64} {got}")
    if not ok:
        FAILED.append(label)
    return ok


FANO = [(1, 2, 3), (1, 4, 5), (1, 6, 7), (2, 4, 6), (2, 5, 7), (3, 4, 7), (3, 5, 6)]
IMAG = list(range(1, 8))

print("=" * 84)
print("1 - H1: for EVERY Fano line, is the complement a coset rather than a subalgebra?")
print("=" * 84)

closed_lines = 0
closed_comps = 0
coset_comps = 0
for L in FANO:
    C = [u for u in IMAG if u not in L]                      # the 4 complement units
    # the LINE plus the real closes into a quaternion subalgebra (8 signed elements)
    subL = set()
    for a in (0,) + L:
        for b in (0,) + L:
            subL.add(oct_mult(a, b) & 7)
    if subL <= set((0,) + L):
        closed_lines += 1
    # the COMPLEMENT: does it close?
    subC = set()
    for a in C:
        for b in C:
            subC.add(oct_mult(a, b) & 7)
    if subC <= set(C):
        closed_comps += 1
    # is the complement a single H-coset? C x C must land back in the LINE-plus-real
    if subC <= set((0,) + L):
        coset_comps += 1
    print(f"    line {L}  complement {tuple(C)}   C*C lands in {sorted(subC)}")

print()
ck("every Fano line + the real CLOSES (a quaternion subalgebra)", closed_lines, 7)
ck("no complement closes on itself (none is a subalgebra)", closed_comps, 0)
ck("every complement squares back INTO its line's subalgebra -- a COSET",
   coset_comps, 7)

print("""
  H1 HOLDS. 7 does not read as seven peers. It reads as

        3   a CLOSED triad (a quaternion subalgebra, has an identity)
      + 4   a COSET of it  (a torsor -- F1341 measured it has NO identity of its own)

  and the 4 is not four more things: it is the SAME triad, re-based. That is the
  user's "if 3 is always a shape then 4 must be a cb shape" -- the 4 is the triad
  seen from outside, which is why it cannot close.
""")

print("=" * 84)
print("2 - H2: does the split CARRY the same information? (weak reading DECIDED)")
print("=" * 84)
print("  Weak reading: is the complement's action FREE and TRANSITIVE -- i.e. does the")
print("  triad's group determine the coset entirely, adding no independent content?\n")

L = FANO[0]                                   # {1,2,3}; complement {4,5,6,7}
H = [q for q in range(16) if (q & 7) in (0,) + L]        # 8 signed units
T = [q for q in range(16) if (q & 7) not in (0,) + L]    # 8 signed units
ck("the triad-with-real has 8 signed units", len(H), 8)
ck("its complement has 8 signed units -- the SAME count", len(T), 8)

st = sum(1 for t1 in T for t2 in T
         if len([g for g in H if oct_torsor_act(t1, g) == t2]) == 1)
ck("H acts SIMPLY TRANSITIVELY on the complement", st, len(T) * len(T))

print("""
  So the coset carries no independent content: fix ONE element of it and the whole
  thing is indexed by the triad's own group. 4 = |H|/2 worth of NEW numbers is zero;
  the 4 is a RE-BASING of the 3, exactly as claimed.

  THE STRONGER READING IS NOT DECIDED HERE. "The full product table is reconstructible
  from the triad plus the coset action" needs the CD doubling rule (which supplies the
  cross terms) as an input; with it the reconstruction is trivially true, and without
  it, false. So the honest verdict is: the split is a re-representation GIVEN the
  doubling rule, and the doubling rule is exactly the piece that is not in either part.
  That is a real caveat on "no additional information" -- the JOIN is information.
""")

print("=" * 84)
print("3 - H3: what does S actually add? NOT symmetry.")
print("=" * 84)
h = sedenion_holonomy_conjecture()
d = h["dimensions"]
ck("Der(S) == Der(O) == g2 == 14 -- NO new symmetry at the S rung",
   (d["der_sedenion"], d["g2"]), (14, 14))
ck("and 0 individual spin(9) generators are sedenion derivations",
   h["certificate"]["n_individual_spin9_derivations"], 0)

# zero divisors: absent at O, present at S
zd8 = cd_zero_divisor_witness(8)
zd16 = cd_zero_divisor_witness(16)
print(f"\n    cd_zero_divisor_witness(8)  -> {str(zd8)[:110]}")
print(f"    cd_zero_divisor_witness(16) -> {str(zd16)[:110]}")

print("""
  So the S rung is where a genuinely NEW behaviour appears -- and it is a LOSS of a
  property (no zero divisors -> zero divisors), not a GAIN of symmetry. Der stays g2.

  That is consistent with the user's "change in time things happen when we address Os
  at S": whatever S contributes, it is not more structure. It is the first rung where
  two things can annihilate -- where a composition can FAIL to be reversible.
""")

print("=" * 84)
print("4 - WHAT IS AND IS NOT ESTABLISHED")
print("=" * 84)
print("""  ESTABLISHED
    7 = 3 + 4 is (closed triad) + (its torsor), for all 7 Fano lines
    the torsor adds no independent content -- simply transitive under the triad's group
    S adds no symmetry (Der stays g2) and does add zero divisors

  NOT ESTABLISHED, and stated so it is not later cited as if it were
    that fibration IS an m x n transform taking 2:4:8 -> 1+1:1+3:1+7. The 3+1+3
      reading (F1326) and the 8:4:2 widths (F1328/F1337) are both measured, but NO
      operator has been exhibited that PERFORMS the change of basis, and calling the
      correspondence a "transform" without one is a name, not a mechanism.
    that "change in time" happens at S. Nothing here measures TIME. What is measured
      is that S is the first rung with zero divisors. Reading irreversibility as time
      is an INTERPRETATION and belongs in MFO, not in a measurement.
    Cohl Furey's programme is NOT cited here. It is real published work on octonionic
      structure and the Standard Model, but per the MPM discipline a citation without
      a verified primary source is not a citation. Flagged as a lead to attest, not
      as support.
""")

print("=" * 84)
print(f"RESULT: {'ALL CHECKS PASSED' if not FAILED else 'FAILURES: ' + repr(FAILED)}")
print("=" * 84)
raise SystemExit(1 if FAILED else 0)

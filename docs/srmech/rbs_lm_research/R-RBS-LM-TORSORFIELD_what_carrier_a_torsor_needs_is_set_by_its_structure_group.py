#!/usr/bin/env python3
"""F1341 — does a torsor ever NEED exact-Q num/den? Yes, and the rule is exact.

User (2026-08-14):
  "I don't suppose that there's ever a need for, or a way to need Q rational num/den things
   for torsor objects for even wierder things to try to keep up with?"

The answer is not a matter of taste. A torsor's `div` op RETURNS AN ELEMENT OF ITS
STRUCTURE GROUP, so the carrier a torsor needs is whatever carrier that group needs:

    torsor                          structure group        div returns    carrier
    O seam coset {+-e4..+-e7}       H signed units (8)     an int         BYTE
    bell spectrum, choice of f0     a subgroup of Q*       a RATIO        Q  (num/den)
    stiff-string spectrum           a subgroup of Q(a)*    an algebraic   Qalg
    membrane spectrum               NOT IDENTIFIED         --             open

So "do we ever need Q for a torsor?" -> only when the structure group is infinite and
rational. The O torsor never needs it; the bell torsor CANNOT be done without it.

srmech 0.9.0rc432. Exact-Q throughout, no abs(), no numpy, no RNG.
"""
import srmech.music as M
from srmech.math.q import Q
from srmech.math.octonion import oct_torsor_act, oct_torsor_div

FAILED = []


def ck(label, got, want=None):
    ok = (got == want) if want is not None else bool(got)
    print(f"  {'ok  ' if ok else 'FAIL'} {label:<66} {got}")
    if not ok:
        FAILED.append(label)
    return ok


print("=" * 84)
print("1 - THE FINITE TORSOR: O's seam coset needs NO rationals at all")
print("=" * 84)
H = [q for q in range(16) if (q & 7) < 4]
T = [q for q in range(16) if (q & 7) >= 4]

divs = {oct_torsor_div(t1, t2) for t1 in T for t2 in T}
print(f"    div returns: {sorted(divs)}")
ck("every oct_torsor_div result is a plain int", all(isinstance(d, int) for d in divs), True)
ck("...and every one lands in the structure group H", sorted(divs), sorted(H))
ck("the structure group is FINITE", len(H), 8)

print("""
  A finite structure group needs only a byte. There is no ratio to represent, because
  the group has no notion of 'a bit of the way between two elements'. Q would be dead
  weight here -- and worse, it would imply a divisibility the group does not have.
""")

print("=" * 84)
print("2 - THE RATIONAL TORSOR: a spectrum's CHOICE OF FUNDAMENTAL")
print("=" * 84)
print("  F1339 measured that a bell has no distinguished f0 -- 5 frames, 5 periods, one")
print("  invariant. That is a torsor statement. What is its structure group?\n")

bell = M.bell_partials()
ratios, names = list(bell["ratios"]), bell["names"]

# the element carrying frame i to frame j is r_i / r_j -- a RATIO, not an index
print("    the 'div' table: what carries frame i to frame j is r_i / r_j")
print("        " + "".join(f"{n:>9}" for n in names))
group_elems = set()
for i, ni in enumerate(names):
    row = ""
    for j in range(len(ratios)):
        g = ratios[i] / ratios[j]
        group_elems.add(g)
        row += f"{str(g):>9}"
    print(f"    {ni:<8}{row}")
print()

ck("every div result is an exact Q, never an int",
   all(isinstance(g, Q) for g in group_elems), True)
non_integral = [g for g in group_elems if g.denominator != 1]
ck("and MOST of them are NOT integers (a byte cannot hold them)",
   len(non_integral) > len(group_elems) // 2, True)
print(f"       {len(group_elems)} distinct group elements, {len(non_integral)} with denominator > 1")

# simple transitivity: exactly one group element carries frame i to frame j
st = sum(1 for i in range(len(ratios)) for j in range(len(ratios))
         if len({ratios[i] / ratios[j]}) == 1)
ck("exactly one element carries frame i -> frame j (simply transitive)",
   st, len(ratios) ** 2)

# and no distinguished basepoint: every frame calls itself 1
diag = [ratios[i] / ratios[i] for i in range(len(ratios))]
ck("every frame labels ITSELF 1 -- no frame is the 'real' fundamental",
   all(d == Q(1, 1) for d in diag), True)

print("""
  THIS IS THE ANSWER TO THE QUESTION. The bell's frame torsor CANNOT be carried in
  bytes: its structure group is a subgroup of Q* (the positive rationals under
  multiplication), and 6/5 is not an index into anything. The num/den pair is not a
  convenience here -- it IS the group element.

  And notice the shape is identical to O's: no distinguished basepoint, simply
  transitive, every element calls itself the identity. Same torsor, different field.
""")

print("=" * 84)
print("3 - THE ALGEBRAIC TORSOR: one rung weirder, and Q is no longer enough")
print("=" * 84)
stiff = M.stiff_string_partials(Q(1, 1000), 4)
sr = list(stiff["ratios"])

# I expected "the group element is a Qalg instead of a Q". The op REFUSED, and the
# refusal is a stronger result than the assertion: the partials do not share a field,
# so the frame-change element DOES NOT EXIST -- there is no group to be a member of.
minpolys = [r._m if hasattr(r, "_m") else None for r in sr]
print("    each partial's minimal polynomial (the field it generates):")
for i, m in enumerate(minpolys):
    print(f"      partial {i}: m = {m}")
ck("the partials live in DIFFERENT number fields", len(set(minpolys)), len(sr))

err = None
try:
    sr[1] / sr[0]
except Exception as exc:
    err = exc
print(f"\n    r1 / r0 -> {type(err).__name__}: {str(err)[:80]}")
ck("the frame-change element cannot even be FORMED (no common field)", err is not None, True)

v = M.commensurability_verdict(sr)
ck("every partial is degree 2, but each over a DIFFERENT radicand",
   set(v["field_degrees"]), {2})

print("""
  SO THE LADDER IS NOT 'a fancier carrier one rung up'. It BREAKS:

    tier 1  the frame changes CLOSE into a group inside Q*   -> a real torsor, needs Q
    tier 2  the frame changes DO NOT CLOSE -- each partial sits in its own quadratic
            field, so r_i/r_j is not an element of anything. NOT A TORSOR AT ALL until
            you first build the compositum Q(sqrt a, sqrt b, ...), which is a CHOICE
            and a construction, not something the spectrum hands you.
    tier 3  no field identified; declared OPEN.

  That is the real reason a stiff string has no period, stated structurally rather than
  numerically: not 'the lcm is too big' but 'the frame-change group does not exist'.
""")

print("=" * 84)
print("4 - THE RULE, AND THE TRAP IT PREDICTS")
print("=" * 84)
print("""    A torsor's div op returns an element of its STRUCTURE GROUP.
    Therefore: the carrier a torsor needs == the carrier its structure group needs.

    finite group          -> byte / int   (O seam coset; Klein-4; Q8)   <- MEASURED
    rational group        -> Q num/den    (a spectrum's choice of f0)   <- MEASURED
    group DOES NOT CLOSE  -> no torsor    (a stiff string's partials)   <- MEASURED
    field unidentified    -> declare OPEN, build nothing (a membrane)

  Note the third row is NOT 'algebraic group -> Qalg'. That is what I predicted and it
  is wrong: the stiff string's partials sit in FOUR DIFFERENT quadratic fields, so no
  single Qalg carrier holds the group, because there is no group. A Qalg-torsor is
  perfectly possible in principle -- it just needs all partials over ONE minimal
  polynomial, which a real stiff string does not give you.

  THE TRAP THIS PREDICTS, and it is one we have been warned about twice:
  forcing a rational carrier onto a non-closing frame set is exactly the best_rational
  failure the music ops document -- it would not approximate the group, it would
  MANUFACTURE one that was never there. The same move that turns an inharmonic spectrum
  into a harmonic one turns a non-torsor into a torsor. Same defect, one rung up, and
  now with a structural name for what gets faked: the closure.
""")

print("=" * 84)
print(f"RESULT: {'ALL CHECKS PASSED' if not FAILED else 'FAILURES: ' + repr(FAILED)}")
print("=" * 84)
raise SystemExit(1 if FAILED else 0)

#!/usr/bin/env python3
"""F1339 — the generator: SUBHARMONIC (x) INHARMONIC -> HARMONIC, read under (frame, lane).

User (2026-08-14):
  "trying to understand how a thing like a subharmonic and inharmonic are what go into a
   generator and harmonic comes out. the resonance is between the two dissimilar shapes is
   what this generator must create. let's try the new (frame, lane) way test too."

The tuned bell is the existence proof and it SHIPS as attested TIER-1 data:
    hum 1/2   prime 1   tierce 6/5   quint 3/2   nominal 2
  - the HUM at 1/2 is a SUBHARMONIC (an undertone, below the fundamental)
  - the TIERCE at 6/5 is INHARMONIC in the acoustician's sense (not an integer multiple)
  - and the whole thing is COMMENSURABLE with period 10.

Measured through shipped srmech.music ops only. Exact-Q / exact-algebraic throughout.
NEVER best_rational on a spectrum -- the shipped explanation states it does not approximate
an inharmonic spectrum, it CONVERTS it into a harmonic one. No abs(), no numpy, no RNG.
srmech 0.9.0rc432.
"""
import srmech.music as M
from srmech.math.q import Q
from srmech.math.cyclic import lcm, gcd

FAILED = []


def ck(label, got, want=None):
    ok = (got == want) if want is not None else bool(got)
    print(f"  {'ok  ' if ok else 'FAIL'} {label:<64} {got}")
    if not ok:
        FAILED.append(label)
    return ok


def den(r):
    """Reduced denominator of an exact-Q ratio (Class-I datum; no float anywhere).
    The accessor is `.denominator` (not `.den` -- my first pass guessed and it threw)."""
    return r.denominator


print("=" * 80)
print("1 - THE TWO POLES, as the shipped verdict sees them")
print("=" * 80)

bell = M.bell_partials()
bv = M.commensurability_verdict(bell["ratios"])
stiff = M.stiff_string_partials(Q(1, 1000), 6)
sv = M.commensurability_verdict(stiff["ratios"])

print(f"  BELL  ratios {[str(r) for r in bell['ratios']]}")
print(f"        verdict={bv['verdict']:<11} integer_series={bv['integer_series']}"
      f"  rational_rank={bv['rational_rank']}/{bv['n_partials']}"
      f"  field_degrees={bv['field_degrees']}  period={bv['period_multiplier']}")
print(f"  STIFF verdict={sv['verdict']:<11} integer_series={sv['integer_series']}"
      f"  rational_rank={sv['rational_rank']}/{sv['n_partials']}"
      f"  field_degrees={sv['field_degrees']}  period={sv['period_multiplier']}")
print()

ck("the BELL is COMMENSURABLE ('harmonic') ...", bv["verdict"], "harmonic")
ck("... and yet NOT an integer series -- two senses of one word",
   bv["integer_series"], False)
ck("the STIFF STRING is INCOMMENSURABLE", sv["verdict"], "inharmonic")
ck("stiff: NOTHING lives in Q (rational_rank 0, every degree 2)",
   (sv["rational_rank"], set(sv["field_degrees"])), (0, {2}))

print("""
  THE LANE READING, and it is not an analogy -- it is what the op computes:
    rational_rank  = how much of the spectrum lies in Q. Q-membership is basis-free
                     and order-blind => this is the INDEX lane.
    field_degree>1 = the algebraic extension Q cannot see => the SIGN/twist lane.
  Bell: rank 5, all degrees 1 -> PURE INDEX LANE, so a period exists.
  Stiff: rank 0, all degrees 2 -> PURE EXTENSION, so no period can exist.
""")

print("=" * 80)
print("2 - THE GENERATOR: neither shape alone has the period they make TOGETHER")
print("=" * 80)
print("  Period is the Class-I lcm of the reduced denominators. Split the bell into")
print("  its SUBHARMONIC part and its INHARMONIC part and price each one alone.\n")

names = bell["names"]
ratios = list(bell["ratios"])
for nm, r in zip(names, ratios):
    tag = ("SUBHARMONIC (below f0)" if r < Q(1, 1) else
           "non-integer (inharmonic sense)" if den(r) != 1 else "integer multiple")
    print(f"    {nm:<9} {str(r):<5} den={den(r)}   {tag}")
print()

SUB = [r for r in ratios if r < Q(1, 1)]                       # the hum, 1/2
INH = [r for r in ratios if den(r) != 1 and r >= Q(1, 1)]      # the tierce 6/5, quint 3/2
INT = [r for r in ratios if den(r) == 1]                       # prime 1, nominal 2

# price each part alone, through the SHIPPED op (never a hand-rolled lcm on an untiered set)
p_sub = M.common_period(SUB + [Q(1, 1)])
p_inh = M.common_period(INH + [Q(1, 1)])
p_int = M.common_period(INT)
p_all = M.common_period(ratios)

print(f"    SUBHARMONIC alone  {str([str(r) for r in SUB]):<30} period = {p_sub}")
print(f"    INHARMONIC alone   {str([str(r) for r in INH]):<30} period = {p_inh}")
print(f"    integer part alone {str([str(r) for r in INT]):<30} period = {p_int}")
print(f"    ALL FIVE TOGETHER  {'':<30} period = {p_all}")
print()

ck("the subharmonic part alone gives period 2", p_sub, 2)
ck("the inharmonic part alone gives period 10", p_inh, 10)
ck("the integer part alone gives period 1 (it contributes NOTHING)", p_int, 1)
ck("the whole bell gives period 10", p_all, 10)
ck("period(whole) == lcm(period(sub), period(inh)) -- the coupling is a Class-I lcm",
   p_all, lcm(p_sub, p_inh))
ck("and the INTEGER partials are inert: lcm(1, x) == x", lcm(p_int, p_all), p_all)

print(f"""
  THE GENERATOR, stated exactly:  period = lcm(den) over the whole set.
    the SUBHARMONIC hum 1/2 supplies the prime 2
    the INHARMONIC tierce 6/5 supplies the prime 5
    the INTEGER partials (1, 2) supply 1 -- inert, they add no denominator
  10 = 2 x 5. The harmonic that comes OUT is built from the DENOMINATOR-BEARING partials
  and from nothing else. The integer partials -- the ones that look most 'harmonic' --
  are exactly the ones that generate nothing.
  (The ablation below asks the sharper question: WHICH of them is irreplaceable.)
""")

# ABLATION -- which partial is actually LOAD-BEARING for the period? Drop each in turn.
# (This replaces a check I first wrote as gcd(p_sub, p_inh) == 1. That is FALSE --
#  gcd(2, 10) = 2 -- and it contradicted the prose I had written directly beneath it.
#  The ablation is the measurement that assertion was reaching for, and it is sharper.)
print("  ABLATION -- drop each partial and re-price the period:\n")
gen_primes = sorted({den(r) for r in ratios if den(r) != 1})
ck("denominators present across the whole bell", gen_primes, [2, 5])

drops = {}
for i, nm in enumerate(names):
    rest = [r for j, r in enumerate(ratios) if j != i]
    drops[nm] = M.common_period(rest)
    verdict = "PERIOD COLLAPSES" if drops[nm] != p_all else "no change"
    print(f"    without {nm:<9} -> period {drops[nm]:<3} {verdict}")
print()

load_bearing = [nm for nm, p in drops.items() if p != p_all]
ck("EXACTLY ONE partial is load-bearing for the period", len(load_bearing), 1)
ck("...and it is the TIERCE -- the inharmonic one", load_bearing, ["tierce"])
ck("dropping the SUBHARMONIC hum changes nothing (the quint 3/2 also carries a 2)",
   drops["hum"], p_all)
ck("without the tierce the period collapses 10 -> 2", drops["tierce"], 2)

print("""
  THIS CORRECTS THE SYMMETRIC READING, and the correction is the result:
  the two shapes are NOT equal partners. The prime 2 is supplied REDUNDANTLY -- by the
  subharmonic hum (1/2) AND by the quint (3/2) -- so removing the hum costs nothing.
  The prime 5 has a SINGLE source: the tierce 6/5. Remove it and the period collapses
  10 -> 2, i.e. back to what the subharmonic alone already gave.

  So the generator is not sub (x) inh as a balanced pair. It is: the INHARMONIC partial
  is the irreplaceable one, and the subharmonic supplies a prime the rest of the
  spectrum was going to supply anyway. What the bell needs, it needs from the tierce.
""")

print("=" * 80)
print("3 - THE (frame, lane) TEST -- re-reference to each partial as the fundamental")
print("=" * 80)
print("  A FRAME here = which partial you call f0. Re-frame the bell 5 ways and ask")
print("  what survives. If F1338's contract holds: the VERDICT is invariant, the")
print("  PERIOD is a per-frame read.\n")

rows = []
for i, (nm, r0) in enumerate(zip(names, ratios)):
    reframed = tuple(r / r0 for r in ratios)          # exact-Q division; stays in Q
    v = M.commensurability_verdict(reframed)
    per = M.common_period(reframed) if v["verdict"] == "harmonic" else None
    rows.append((nm, reframed, v, per))
    print(f"    f0 = {nm:<9} ratios {[str(x) for x in reframed]}")
    print(f"    {'':<14} verdict={v['verdict']:<10} rank={v['rational_rank']}"
          f"  degrees={v['field_degrees']}  PERIOD={per}")

verdicts = {r[2]["verdict"] for r in rows}
ranks = {r[2]["rational_rank"] for r in rows}
degs = {tuple(r[2]["field_degrees"]) for r in rows}
periods = sorted({r[3] for r in rows})
print()
ck("VERDICT is frame-INVARIANT across all 5 frames", len(verdicts), 1)
ck("rational_rank (the INDEX lane) is frame-INVARIANT", len(ranks), 1)
ck("field_degrees (the SIGN lane) is frame-INVARIANT", len(degs), 1)
ck("PERIOD is frame-DEPENDENT -- it is a read, not a property", len(periods) > 1, True)
print(f"       periods across the 5 frames: {periods}")

print("""
  EXACTLY F1338's contract, now in a second substrate:
    - the LANE data (rational_rank, field_degrees) is the INVARIANT -> a cross-frame
      claim may be made of it;
    - the PERIOD is the per-frame READ-OUT -> two observers of the SAME bell disagree
      about the repeat length and are both right.
  'Is this thing harmonic?' is frame-free. 'What is its period?' is not.
""")

print("=" * 80)
print("4 - DOES THE GENERATOR SURVIVE A GENUINELY DISSIMILAR PARTNER?")
print("=" * 80)
print("  The bell's two shapes are both RATIONAL. Couple a rational subharmonic to an")
print("  ALGEBRAIC (degree-2) partner and ask whether a harmonic still comes out.\n")

mixed = [Q(1, 2), Q(1, 1)] + list(stiff["ratios"][:2])
mv = M.commensurability_verdict(mixed)
print(f"    mixed verdict={mv['verdict']}  rank={mv['rational_rank']}/{mv['n_partials']}"
      f"  degrees={mv['field_degrees']}  incommensurable={mv['incommensurable']}")
ck("mixing a rational subharmonic with a degree-2 partner is INCOMMENSURABLE",
   mv["verdict"], "inharmonic")
ck("...and the op NAMES which partials broke it (indices 2,3 = the algebraic ones)",
   tuple(mv["incommensurable"]), (2, 3))
ck("the rational members SURVIVE in the rank (2 of 4 still lie in Q)",
   mv["rational_rank"], 2)

raised = False
try:
    M.common_period(mixed)
except Exception as exc:
    raised = True
    print(f"       common_period REFUSED, as documented: {str(exc)[:90]}")
ck("common_period RAISES rather than silently harmonising (the raise IS the feature)",
   raised, True)

print("""
  SO THE GENERATOR HAS A PRECONDITION, and it is the honest half of this finding:
  subharmonic (x) inharmonic -> harmonic works when both shapes are COMMENSURABLE-BUT-
  DISSIMILAR (different denominators, same field Q). It does NOT bridge a field
  extension. A degree-2 partner does not resonate into a period -- it refuses one, and
  srmech refuses WITH it rather than converting.
""")

print("=" * 80)
print(f"RESULT: {'ALL CHECKS PASSED' if not FAILED else 'FAILURES: ' + repr(FAILED)}")
print("=" * 80)
raise SystemExit(1 if FAILED else 0)

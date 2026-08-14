#!/usr/bin/env python3
"""F1340 — the SAME ablation across three substrates: 1-D stiff string, 2-D membrane, 3-D bell.

User (2026-08-14):
  "now try the same ablation on membrane and stiff string partials. can't forget that these
   are instances of the same process on varying substrate and perspective, so the thing we're
   looking for needs to describe from string to 3D asymmetric and tuned box ... on up to this
   hypercomplex object, that when fibrated downward still describes the 2d string and 3d
   box/body resonators of strings, pianos, bells, and gongs."

F1339's ablation was written on the PERIOD. The period only exists for a commensurable
spectrum, so on a stiff string or a membrane it RAISES. That obstacle is the finding: the
ablation must be taken on the INVARIANT (rational_rank / field_degrees / verdict), which
exists at every tier, and never on the READ (the period), which does not.

Measured through shipped srmech.music ops. Exact-Q / exact-algebraic. NEVER best_rational
on a spectrum. No abs(), no numpy, no RNG. srmech 0.9.0rc432.
"""
import srmech.music as M
from srmech.math.q import Q

FAILED = []


def ck(label, got, want=None):
    ok = (got == want) if want is not None else bool(got)
    print(f"  {'ok  ' if ok else 'FAIL'} {label:<66} {got}")
    if not ok:
        FAILED.append(label)
    return ok


def verdict_of(ratios, open_partials=()):
    return M.commensurability_verdict(ratios, open_partials=open_partials)


def invariant(v):
    """The (frame, lane) INVARIANT triple -- what a perspective may not change.

    SIZE-NORMALISED, and that correction is load-bearing. My first pass used the raw
    (verdict, rational_rank, field_degrees) tuple, which carries CARDINALITY: dropping
    any partial takes rank 5/5 -> 4/4 and a 5-tuple of degrees -> a 4-tuple, so it moves
    trivially for every partial of every substrate. I had built a size-DEPENDENT quantity
    and called it an invariant, then ablated it -- guaranteeing a meaningless 'everything
    matters'. The KIND of a spectrum is (verdict, is-it-full-rank, WHICH degrees occur),
    none of which should care how many partials you kept.
    """
    return (v["verdict"],
            v["rational_rank"] == v["n_partials"],     # full-rank? (a ratio, not a count)
            frozenset(v["field_degrees"]))             # which degrees OCCUR, not how many


# ---------------------------------------------------------------- the three substrates
bell = M.bell_partials()
stiff = M.stiff_string_partials(Q(1, 1000), 6)
mem = M.membrane_partials(3, 3)

SUBSTRATES = [
    ("BELL      3-D cast metal, TUNED", bell["ratios"], (), 3),
    ("STIFF STR 1-D wire + stiffness ", stiff["ratios"], (), 1),
    ("MEMBRANE  2-D drumhead         ", mem["ratios"], mem["open_partials"], 2),
]

print("=" * 84)
print("1 - ONE PROCESS, THREE SUBSTRATES -- the invariant triple side by side")
print("=" * 84)
for name, ratios, openp, dim in SUBSTRATES:
    v = verdict_of(ratios, openp)
    print(f"  {name}  dim={dim}D  tier={v['tier']} ({v['tier_name']})")
    print(f"      verdict={v['verdict']:<11} rank={v['rational_rank']}/{v['n_partials']}"
          f"  degrees={tuple(v['field_degrees'])}")
print()

ck("bell is TIER 1 rational", verdict_of(bell["ratios"])["tier"], 1)
ck("stiff string is TIER 2 algebraic", verdict_of(stiff["ratios"])["tier"], 2)
ck("membrane is TIER 3 open",
   verdict_of(mem["ratios"], mem["open_partials"])["tier"], 3)

print("""
  DIMENSION DOES NOT SET THE TIER.  1-D -> tier 2.  2-D -> tier 3.  3-D -> tier 1.
  Non-monotone in both directions. The most geometrically complex object here (a cast
  bell) has the SIMPLEST spectrum, because a founder TUNED it back into Q. What sets the
  tier is whether something forced commensurability -- not how many dimensions vibrate.
""")

print("=" * 84)
print("2 - THE ABLATION, GENERALISED -- taken on the INVARIANT, never on the period")
print("=" * 84)
print("  Drop each partial in turn; report whether the INVARIANT triple moves.\n")

ladder = {}
for name, ratios, openp, dim in SUBSTRATES:
    base = invariant(verdict_of(ratios, openp))
    movers = []
    for i in range(len(ratios)):
        rest = tuple(r for j, r in enumerate(ratios) if j != i)
        rest_open = tuple(k - (1 if k > i else 0) for k in openp if k != i)
        if invariant(verdict_of(rest, rest_open)) != base:
            movers.append(i)
    # the PERIOD ablation, for contrast -- only defined when commensurable
    try:
        p_all = M.common_period(ratios, open_partials=openp)
        p_movers = [i for i in range(len(ratios))
                    if M.common_period(tuple(r for j, r in enumerate(ratios) if j != i),
                                       open_partials=tuple(k - (1 if k > i else 0)
                                                           for k in openp if k != i)) != p_all]
        period_note = f"period={p_all}, load-bearing {p_movers}"
    except Exception as exc:
        period_note = f"period UNDEFINED ({type(exc).__name__})"
    ladder[name.split()[0]] = (len(movers), period_note)
    print(f"  {name}")
    print(f"      invariant-ablation : partials that MOVE the invariant -> {movers or 'NONE'}")
    print(f"      period-ablation    : {period_note}")

print()
ck("BELL: the invariant ablation is FLAT (0 movers) even though the PERIOD one is not",
   ladder["BELL"][0], 0)
ck("STIFF: no partial is load-bearing for the invariant", ladder["STIFF"][0], 0)
ck("MEMBRANE: no partial is load-bearing for the invariant", ladder["MEMBRANE"][0], 0)

print("""
  AND THIS IS THE RESULT, not a null: the invariant ablation is FLAT ON ALL THREE.
  Removing a partial never changes what KIND of spectrum it is. The bell's dramatic
  10 -> 2 collapse from F1339 is entirely a PERIOD effect, and the period is the
  frame-dependent READ. So F1339's 'the inharmonic partial is irreplaceable' is TRUE
  and is a statement about a READ-OUT, not about the object's identity.

  That sharpens the (frame, lane) contract with a rule it did not have:
     an ABLATION inherits the frame-dependence of whatever it ablates.
  Ablate a read -> you learn about the frame. Ablate an invariant -> you learn about
  the object. Both are useful; conflating them is how a frame artifact gets published.
""")

print("=" * 84)
print("3 - CONTINUOUS SUBSTRATE, DISCRETE INVARIANT -- the stiffness sweep")
print("=" * 84)
print("  B is the physical inharmonicity of a real wire. Sweep it toward zero.\n")

sweep = []
for B in (Q(1, 10), Q(1, 100), Q(1, 1000), Q(1, 10**6), Q(1, 10**12), Q(0, 1)):
    v = verdict_of(M.stiff_string_partials(B, 4)["ratios"])
    sweep.append((B, v["verdict"], v["rational_rank"], tuple(v["field_degrees"])))
    print(f"    B = {str(B):<12} verdict={v['verdict']:<11} rank={v['rational_rank']}/4"
          f"  degrees={tuple(v['field_degrees'])}")
print()

nonzero = [s for s in sweep if s[0] != Q(0, 1)]
zero = [s for s in sweep if s[0] == Q(0, 1)][0]
ck("every NONZERO stiffness gives the same verdict (inharmonic)",
   len({s[1] for s in nonzero}), 1)
ck("every NONZERO stiffness gives rank 0 and degree 2 -- no gradient at all",
   len({(s[2], s[3]) for s in nonzero}), 1)
ck("B = 0 EXACTLY flips to harmonic, rank 4, degree 1", (zero[1], zero[2], zero[3]),
   ("harmonic", 4, (1, 1, 1, 1)))

print("""
  A STEP FUNCTION, not a slope. B = 1e-12 is as inharmonic as B = 1/10: rank 0, degree 2.
  Only B = 0 EXACTLY is in Q. The physical parameter is continuous; the invariant it
  controls is DISCRETE. You are in the field or you are not, and 'nearly in Q' is not a
  state the invariant can occupy.

  This is the substrate/shadow split in one measurement: the continuous knob is the
  SUBSTRATE, the discrete verdict is what survives projection.
""")

print("=" * 84)
print("4 - THE TRAP -- what a precision-truncated irrational looks like")
print("=" * 84)
print("  The membrane ships fixed-point ratios at a DECLARED precision, so every one of")
print("  them is LITERALLY a rational. Ask the verdict WITHOUT the open declaration:\n")

honest = verdict_of(mem["ratios"], mem["open_partials"])
naive = verdict_of(mem["ratios"])
print(f"    WITH  open_partials= : verdict={honest['verdict']:<10} rank={honest['rational_rank']}/9")
print(f"    WITHOUT              : verdict={naive['verdict']:<10} rank={naive['rational_rank']}/9   <-- FALSE")
ck("the honest call returns 'open'", honest["verdict"], "open")
ck("the naive call returns a FALSE 'harmonic' with full rank",
   (naive["verdict"], naive["rational_rank"]), ("harmonic", 9))

print(f"\n    but the lie does not survive to a period:")
print(f"      period_unavailable: {str(naive['period_unavailable'])[:130]}")
raised = False
try:
    M.common_period(mem["ratios"])
except Exception as exc:
    raised = True
ck("common_period still REFUSES -- the 39-digit denominator is the tell", raised, True)

print("""
  TWO LAYERS OF HONESTY, and only the second is automatic. The tier DECLARATION is what
  makes the verdict truthful; without it the op is confidently wrong. What catches the
  lie downstream is the SIZE of the denominator -- a genuine rational has a small one, a
  truncated irrational has a 39-digit one. So 'is the denominator absurd?' is a usable
  smell test when a tier tag is missing, and it is NOT a substitute for the tag.
""")

print("=" * 84)
print("5 - WHAT FIBRATES DOWNWARD, AND WHAT DOES NOT")
print("=" * 84)
print("""  The one description that spans wire -> drumhead -> bell is the INVARIANT TRIPLE
  (verdict, rational_rank, field_degrees) -- the tier ladder Q / algebraic / open. It is
  substrate-blind: it never asks how many dimensions vibrate, only which field the RATIOS
  live in. That is why it reads a 1-D wire and a 3-D casting on the same axis.

  ⚠ GUARD, and it is the same collision srmech's own describe() warns about:
     the TIER ladder      1 / 2 / 3        is FIELD-EXTENSION DEGREE of the ratios
     the CD/Hurwitz ladder R / C / H / O   is REAL DIMENSION of an algebra
  These are DIFFERENT ladders that both count small integers upward. Nothing measured
  here identifies them, and this finding does not claim tier-3 'is' the octonion rung.
  What IS shared is the CONTRACT shape: an invariant that survives a perspective, and a
  read that does not.
""")

print("=" * 84)
print(f"RESULT: {'ALL CHECKS PASSED' if not FAILED else 'FAILURES: ' + repr(FAILED)}")
print("=" * 84)
raise SystemExit(1 if FAILED else 0)

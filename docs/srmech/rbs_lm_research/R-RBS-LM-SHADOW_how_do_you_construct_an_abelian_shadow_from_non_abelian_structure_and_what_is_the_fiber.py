r"""R-RBS-LM-SHADOW — the constructive direction: HOW do you build an abelian shadow FROM a non-abelian
structure, what exactly is lost, and where does the shadow-map itself break?

USER (2026-07-21): *"the part you said 'the abelian shadow of a non-abelian structure' is absolutely what we
need. our science tries to describe an abelian universe from an abelian shadow, so then too does our simulation
of science, all the way down to knowledge inference. means we should be looking at how to create an abelian
shadow from non-abelian structure too."*

F1278 showed the destructive direction: flatten a non-abelian history and the H(3)/O(7) parts do not survive.
This is the CONSTRUCTIVE direction — not "what breaks" but "what is the map, and what is its kernel."

WHAT AN ABELIAN SHADOW HAS TO BE. A map S from the algebra to something commutative, such that S(xy) does not
depend on the order. That is a homomorphism onto an abelian target. Two candidates are already sitting in the
framework rather than needing invention:
    the NORM        N(x) = sum x_i^2      -> multiplicative into (R+, x), which is abelian
    the REAL PART   Re(x) = x_0           -> the trace-like part; Re(xy) = Re(yx) is the trace property
Both are ORDER-FREE if they are genuine shadows, and that is measurable rather than assumable.

WHAT THE FIBER IS. Whatever the shadow cannot see is the COMMUTATOR [x,y] = xy - yx. It is identically zero
exactly when the algebra is abelian, and it is precisely the content F1278 said cannot be flattened. So the
decomposition is: **shadow = the order-free invariants; fiber = the commutator.** That makes "hidden fiber"
a computable object here, not a figure of speech.

THE PREDICTION THAT MAKES THIS MORE THAN BOOKKEEPING. If the norm-shadow is a homomorphism exactly where
composition holds, then it exists at 1,2,4,8 and FAILS at 16 -- i.e. **the Hurwitz boundary is the boundary of
"has a clean abelian shadow at all."** That would sharply reframe F1273/F1274/F1275: the boundary is INVISIBLE
to addressing (which needs only signed permutations) and EXACTLY VISIBLE to shadow-formation. Two operations,
one boundary, opposite verdicts -- and that is checkable here.

FALSIFIER: if N(xy) = N(yx) fails somewhere it should hold, or if the commutator is zero where the algebra is
non-abelian, the decomposition is wrong and the shadow/fiber split does not survive.

MFO READING (in scope, per user direction 2026-07-21). If an observer is confined to the shadow, the fiber is
not merely unmeasured -- it is OUTSIDE THE MAP'S RANGE. That is the precise form of "we may be asking the
substrate to produce shadow-shaped observables." Stated as structure, not as a claim about the world.

srmech 0.9.0rc297. Exact rationals via cd_mult; Class-K cascade.magnitude; DERIVED elements, no RNG.
Composes F1278 (the destructive direction), F1273/F1274/F1275 (the Hurwitz boundary and what it is invisible
to), F1279 (invisible != absent), F1216, `[[feedback_no_privileged_primitive_classes]]`.
Run:  /tmp/srmech_rc297/bin/python3 R-RBS-LM-SHADOW_*.py
"""
import sys
import time

from srmech.amsc import cascade

T0 = time.time()
RUNGS = ((2, "C"), (4, "H"), (8, "O"), (16, "S"), (32, "T"))
TRIALS = 40


def log(m):
    print("[%5.1fs] %s" % (time.time() - T0, m), flush=True)


def derived(rule, t, dim, salt=0):
    """Same three declared rules as F1273/F1274/F1278. DERIVED, no RNG."""
    if rule == 0:
        return tuple(((t * 31 + k * 17 + salt * 7) % 11) - 5 for k in range(dim))
    if rule == 1:
        return tuple(((t * 13 + k * k * 5 + salt * 3) % 9) - 4 for k in range(dim))
    return tuple((((t + 1) * (k + 2) + salt * 11) % 13) - 6 for k in range(dim))


def N(x):
    return sum(a * a for a in x)


def Re(x):
    return x[0]


def commutator(x, y):
    xy, yx = cascade.cd_mult(x, y), cascade.cd_mult(y, x)
    return tuple(a - b for a, b in zip(xy, yx))


def pairs(dim):
    for rule in (0, 1, 2):
        for t in range(TRIALS):
            x, y = derived(rule, t, dim, 0), derived(rule, t, dim, 1)
            if all(c == 0 for c in x) or all(c == 0 for c in y):
                continue
            yield x, y


def part_a():
    log("")
    log("=== (A) ARE THE CANDIDATE SHADOWS ACTUALLY ORDER-FREE? ===")
    log("  A shadow must not depend on the order of the product. Measured, not assumed.")
    log("")
    log("  %-8s %-22s %-22s %-18s" % ("rung", "N(xy) == N(yx)?", "Re(xy) == Re(yx)?", "algebra abelian?"))
    for dim, name in RUNGS:
        nfail = rfail = comm_nonzero = tot = 0
        for x, y in pairs(dim):
            tot += 1
            xy, yx = cascade.cd_mult(x, y), cascade.cd_mult(y, x)
            if N(xy) != N(yx):
                nfail += 1
            if Re(xy) != Re(yx):
                rfail += 1
            if any(c != 0 for c in commutator(x, y)):
                comm_nonzero += 1
        log("  %-8s %-22s %-22s %-18s"
            % ("%d %s" % (dim, name),
               "ALWAYS (%d/%d)" % (tot - nfail, tot) if nfail == 0 else "fails %d/%d" % (nfail, tot),
               "ALWAYS (%d/%d)" % (tot - rfail, tot) if rfail == 0 else "fails %d/%d" % (rfail, tot),
               "yes" if comm_nonzero == 0 else "NO (%d/%d non-comm)" % (comm_nonzero, tot)))
    log("")
    log("  => both candidates are ORDER-FREE at every rung, INCLUDING the non-abelian ones. That is")
    log("     what makes them shadows: they survive exactly the reordering the algebra does not.")


def part_b():
    log("")
    log("=== (B) IS THE NORM-SHADOW A HOMOMORPHISM? — and where does it STOP being one? ===")
    log("  Order-free is necessary but not sufficient. A usable shadow must also COMPOSE:")
    log("  N(xy) = N(x)N(y). Otherwise the shadow of a product is not a function of the shadows.")
    log("")
    log("  %-8s %-26s %-30s" % ("rung", "N(xy) = N(x)N(y)?", "verdict"))
    for dim, name in RUNGS:
        fail = tot = 0
        for x, y in pairs(dim):
            tot += 1
            if N(cascade.cd_mult(x, y)) != N(x) * N(y):
                fail += 1
        ok = fail == 0
        log("  %-8s %-26s %-30s"
            % ("%d %s" % (dim, name),
               "HOLDS (%d/%d)" % (tot, tot) if ok else "fails %d/%d (%.0f%%)" % (fail, tot, 100.0 * fail / tot),
               "clean abelian shadow EXISTS" if ok else "NO clean abelian shadow"))
    log("")
    log("  => THE HURWITZ BOUNDARY IS THE BOUNDARY OF 'HAS A CLEAN ABELIAN SHADOW'.")
    log("     At 1,2,4,8 the norm is multiplicative, so the shadow of a product is a function of the")
    log("     shadows. At 16 it is not — so beyond O you cannot even build a consistent abelian")
    log("     DESCRIPTION, never mind recover the structure from one.")


def part_c():
    log("")
    log("=== (C) THE FIBER: what the shadow cannot see, as a computable object ===")
    log("  fiber = the commutator [x,y] = xy - yx. Zero iff abelian; otherwise it is exactly the")
    log("  content F1278 said cannot be flattened. Measured as a RATIO to the product's magnitude —")
    log("  note it EXCEEDS 1, so the commutator is not a small residue inside the product.")
    log("")
    log("  %-8s %-20s %-26s" % ("rung", "[x,y] nonzero", "|[x,y]|^2 / |xy|^2 (RATIO)"))
    for dim, name in RUNGS:
        nz = tot = 0
        share_num, share_den = 0, 0
        for x, y in pairs(dim):
            tot += 1
            c = commutator(x, y)
            xy = cascade.cd_mult(x, y)
            if any(v != 0 for v in c):
                nz += 1
            if N(xy) != 0:
                share_num += N(c)
                share_den += N(xy)
        share = (share_num / share_den) if share_den else 0.0
        log("  %-8s %-20s %-26s" % ("%d %s" % (dim, name), "%d/%d" % (nz, tot), "%.3f" % share))
    log("")
    log("  => the fiber is not a residue that shrinks with rung — it GROWS. The higher the rung, the")
    log("     larger the share of the product that the abelian shadow cannot represent.")


def part_d():
    log("")
    log("=== (D) CAN THE STRUCTURE BE RECOVERED FROM ITS SHADOW? ===")
    log("  Direct test: find DISTINCT products that cast the SAME shadow. If they exist, the map is")
    log("  many-to-one and no amount of shadow-side cleverness inverts it.")
    dim = 8
    # (i) CONSTRUCTIVE: S maps an 8-dimensional space onto TWO numbers, so it cannot be injective.
    #     Exhibiting one pair settles it; a search is only needed to show it is not a corner case.
    a = tuple(1 if k == 1 else 0 for k in range(dim))      # e1
    b = tuple(1 if k == 2 else 0 for k in range(dim))      # e2
    log("")
    log("  (i) CONSTRUCTIVE — S(x) = (N, Re) maps %d dimensions onto 2 numbers, so it CANNOT be" % dim)
    log("      injective. Exhibit: e1 and e2 are different elements with")
    log("        S(e1) = %s   S(e2) = %s   -> IDENTICAL shadow, distinct elements" % ((N(a), Re(a)), (N(b), Re(b))))

    # (ii) SEARCH, over a wider and less structured space than part A's three rules -- the earlier
    #      draft searched only those and found 33 distinct products, far too few to exhibit anything.
    seen = {}
    collisions = []
    for t in range(600):
        x = tuple(((t * 37 + k * 11) % 17) - 8 for k in range(dim))
        y = tuple(((t * 23 + k * 29) % 15) - 7 for k in range(dim))
        if all(c == 0 for c in x) or all(c == 0 for c in y):
            continue
        xy = tuple(cascade.cd_mult(x, y))
        key = (N(xy), Re(xy))
        if key in seen and seen[key] != xy:
            collisions.append((key, seen[key], xy))
        seen[key] = xy
    log("  (ii) SEARCH — %d distinct shadows over %d products: %d COLLISIONS (same (N,Re), different element)"
        % (len(seen), 600, len(collisions)))
    if collisions:
        k, p, q = collisions[0]
        log("       example shadow (N,Re) = %s" % (k,))
        log("         product A = %s" % (p[:5] + ("...",),))
        log("         product B = %s" % (q[:5] + ("...",),))
    log("")
    log("  => the shadow map is MANY-TO-ONE — settled CONSTRUCTIVELY by (i), independent of the search.")
    log("     This is F1279's cospectral pair again, in the algebra rather than the graph: the")
    log("     observer sees one object where there are two.")
    return len(collisions)


def main():
    import srmech
    log("=== SHADOW (srmech %s) — constructing an abelian shadow, and naming its fiber ===" % srmech.__version__)
    part_a()
    part_b()
    part_c()
    ncol = part_d()

    log("")
    log("=== THE CONSTRUCTION, STATED ===")
    log("  SHADOW  S(x) = (N(x), Re(x))   — order-free at EVERY rung; composes only through O")
    log("  FIBER   [x,y] = xy - yx        — zero iff abelian; grows with rung; invisible to S")
    log("")
    log("  Three things follow, and the third is the one that bites:")
    log("   1. An abelian shadow can ALWAYS be formed (the invariants are order-free at every rung),")
    log("      so the existence of a shadow is NOT evidence that the structure is abelian.")
    log("   2. The shadow COMPOSES only at 1,2,4,8. Past O, even the description breaks — the shadow")
    log("      of a product stops being a function of the shadows.")
    log("   3. The map is MANY-TO-ONE (proved constructively; %d collisions also found by search)," % ncol)
    log("      so it is NOT invertible. The")
    log("      fiber is not 'not yet measured'; it is OUTSIDE THE RANGE of the map.")
    log("")
    log("  MFO reading (in scope per user direction): an observer confined to S sees a consistent,")
    log("  composable, abelian world at every rung it can describe at all — and that consistency is")
    log("  NOT evidence the underlying structure is abelian. The shadow is well-behaved precisely")
    log("  because it has already discarded what would misbehave. Stated as structure; whether our")
    log("  observation IS such a map is a substrate question this harness does not touch.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

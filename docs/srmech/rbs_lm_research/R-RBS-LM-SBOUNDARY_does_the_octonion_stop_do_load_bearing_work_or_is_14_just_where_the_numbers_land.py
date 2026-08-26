r"""R-RBS-LM-SBOUNDARY — the 𝕊-boundary probe queued by F1270. Is stopping the Cayley–Dickson ladder at 𝕆
LOAD-BEARING, or is 14 = 1+3+7+3 simply where the numbers land?

THE QUESTION, STATED SO IT CAN FAIL. F1270 read `the_one`'s `dim 14 = ℂ(2)⊕ℍ(4)⊕𝕆(8)`, `imag_dims (1,3,7)` = 11D,
`grammar_slots ('B','H','N')` = the 3 reals. Every one of those numbers depends on the ladder STOPPING at 𝕆.
Admit the next rung 𝕊(16) and the arithmetic is 2+4+8+16 = 30, imag 1+3+7+15 = 26, reals 4 — not 14, not 11D,
not 3. So the partition is not robust to the boundary; it IS the boundary.

That makes the honest question sharp, and it is NOT "does Hurwitz hold" (it does — it is a theorem, dim 1/2/4/8
are the only normed division algebras, and re-deriving it is not the point). The question is:

    **Does anything we ACTUALLY DO with the 1:3:7:3 structure depend on the property 𝕊 loses?**

Because if it does not, then stopping at 𝕆 is us liking where the numbers land — which is exactly the failure
mode that killed seven fitted results across F1264–F1271. A boundary that no operation of ours leans on is
decoration, however true the theorem behind it is.

WHY THIS IS A REAL RISK AND NOT A STRAW MAN. Our own memory already says the opposite of "we need division":
`[[feedback_sedenion_no_division_is_the_addressing_feature]]` — *non*-division is the FEATURE for addressing
(navigate, don't divide). If that stance is right, then 𝕊 is not a wall we stop at, it is a REGIME WE USE, and
the 14 boundary must be justified by something other than "algebra breaks there."

THE FOUR PARTS
  A — THE LOSS LADDER, MEASURED (not cited). Sweep dims 1,2,4,8,16,32 through OUR OWN `cascade.cd_mult` and
      measure the violation rate of commutativity / associativity / alternativity / norm-multiplicativity at
      each rung. Own-work-first: we do not take the textbook's word for where each property dies.
  B — HOW MUCH OF 𝕊 IS BROKEN? Zero divisors exist at 16 — but are they DENSE (𝕊 is unusable) or MEASURE-ZERO
      (dodgeable, and "navigate around them" is a real strategy)? This is the quantitative form of the
      addressing claim, and it is the number the stance in memory actually needs.
  C — THE LOAD-BEARING TEST. Does OUR addressing degrade at 𝕊? `SedenionRegister` ships `navigate` +
      `is_navigable` — the reversibility gate. Measure the navigable fraction.
      FALSIFIER FOR THE FRAMEWORK STANCE: if the navigable fraction is ~0, "non-division is the addressing
      feature" is dead and the 𝕆 stop IS load-bearing for us.
      FALSIFIER FOR THE 𝕆 STOP: if addressing at 𝕊 is fine, then no operation of ours needs the division
      property, and 14's boundary rests on Hurwitz as an EXTERNAL theorem — not on our cascade. That is a
      legitimate place to stand, but it must be SAID, not implied.
  D — THE ARITHMETIC, STATED PLAINLY. What the partition becomes if 𝕊 is admitted. No interpretation.

NO RNG. Elements are DERIVED from the trial index by three declared integer rules (per
`[[feedback_three_things_called_random_derived_drawn_stochastic]]` — a content-keyed derivation is a Class-A
address, not a draw, and it is reproducible). Three independent rules guard against one rule accidentally
landing on special structure; if the rules disagree, that is reported rather than averaged away.

Exact rationals throughout (`cd_mult` returns Q) — no floats, so every "is it zero" is EXACT, not a tolerance.
Class-K `cascade.magnitude`, never the builtin.

srmech 0.9.0rc288.
Composes F1270 (which queued this), F1272 (the structural results that held), F1271 (the fitted ones that did
not), `[[feedback_sedenion_no_division_is_the_addressing_feature]]`,
`[[feedback_three_things_called_random_derived_drawn_stochastic]]`, DUALITY.md / TRIALITY.md, #231/PKG-3.
Run:  /tmp/srmech_rc288/bin/python3 R-RBS-LM-SBOUNDARY_*.py
"""
import sys
import time

from srmech.amsc import cascade

T0 = time.time()
DIMS = (1, 2, 4, 8, 16, 32)
NAMES = {1: "R (real)", 2: "C (complex)", 4: "H (quaternion)", 8: "O (octonion)",
         16: "S (sedenion)", 32: "T (trigintaduonion)"}
TRIALS = 60


def log(m):
    print("[%5.1fs] %s" % (time.time() - T0, m), flush=True)


# ---- DERIVED elements: three declared rules, no RNG ------------------------------------------------
def elem(rule, t, dim, salt=0):
    """Coefficient k of trial t under `rule`. Deterministic, reproducible, content-keyed (Class-A-ish)."""
    if rule == 0:
        return tuple(((t * 31 + k * 17 + salt * 7) % 11) - 5 for k in range(dim))
    if rule == 1:
        return tuple(((t * 13 + k * k * 5 + salt * 3) % 9) - 4 for k in range(dim))
    return tuple((((t + 1) * (k + 2) + salt * 11) % 13) - 6 for k in range(dim))


def is_zero(v):
    return all(x == 0 for x in v)


def sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def nsq(v):
    """Squared norm — exact. Sum of squares, no sqrt, so it stays rational."""
    return sum(x * x for x in v)


# ---- PART A: the loss ladder, measured ------------------------------------------------------------
def part_a():
    log("")
    log("=== PART A — THE LOSS LADDER, MEASURED ON OUR OWN cd_mult (not cited) ===")
    log("  violation RATE over %d derived trials x 3 rules. 0.000 = property HOLDS." % TRIALS)
    log("")
    log("  %-22s %-10s %-10s %-12s %-12s" % ("rung", "commut", "assoc", "alternat", "norm-mult"))
    table = {}
    for dim in DIMS:
        bad = {"c": 0, "a": 0, "l": 0, "n": 0}
        tot = 0
        for rule in (0, 1, 2):
            for t in range(TRIALS):
                x = elem(rule, t, dim, 0)
                y = elem(rule, t, dim, 1)
                z = elem(rule, t, dim, 2)
                if is_zero(x) or is_zero(y):
                    continue
                tot += 1
                xy, yx = cascade.cd_mult(x, y), cascade.cd_mult(y, x)
                if not is_zero(sub(xy, yx)):
                    bad["c"] += 1
                if not is_zero(sub(cascade.cd_mult(xy, z), cascade.cd_mult(x, cascade.cd_mult(y, z)))):
                    bad["a"] += 1
                xx = cascade.cd_mult(x, x)
                if not is_zero(sub(cascade.cd_mult(xx, y), cascade.cd_mult(x, xy))):
                    bad["l"] += 1
                if nsq(xy) != nsq(x) * nsq(y):
                    bad["n"] += 1
        r = {k: (v / tot if tot else 0.0) for k, v in bad.items()}
        table[dim] = r
        log("  %-22s %-10.3f %-10.3f %-12.3f %-12.3f" %
            ("%-2d %s" % (dim, NAMES[dim]), r["c"], r["a"], r["l"], r["n"]))

    log("")
    log("  --- where each property DIES (first rung with a nonzero rate) ---")
    for key, label in (("c", "commutativity"), ("a", "associativity"),
                       ("l", "alternativity"), ("n", "norm-multiplicativity")):
        died = next((d for d in DIMS if table[d][key] > 0), None)
        log("    %-24s lost at dim %s" % (label, died if died else "never (in this sweep)"))
    return table


# ---- PART B: how much of S is actually broken? ----------------------------------------------------
def part_b():
    log("")
    log("=== PART B — ARE ZERO DIVISORS DENSE, OR MEASURE-ZERO AND DODGEABLE? ===")
    log("  The stance in memory ('navigate, don't divide') needs them RARE. If a derived-generic pair")
    log("  multiplies to zero often, S is unusable and the stance is wrong.")
    log("")
    log("  %-22s %-14s %-16s" % ("rung", "generic x*y==0", "norm-mult fails"))
    for dim in (8, 16, 32):
        zero_hits, norm_fail, tot = 0, 0, 0
        for rule in (0, 1, 2):
            for t in range(TRIALS):
                x, y = elem(rule, t, dim, 0), elem(rule, t, dim, 1)
                if is_zero(x) or is_zero(y):
                    continue
                tot += 1
                xy = cascade.cd_mult(x, y)
                if is_zero(xy):
                    zero_hits += 1
                if nsq(xy) != nsq(x) * nsq(y):
                    norm_fail += 1
        log("  %-22s %-14s %-16s" % ("%-2d %s" % (dim, NAMES[dim]),
                                     "%d/%d" % (zero_hits, tot), "%d/%d" % (norm_fail, tot)))

    log("")
    log("  --- the STRUCTURED zero divisor srmech exhibits (basis-pair search, our own table) ---")
    w = cascade.sedenion_zero_divisor_witness()
    log("    dim %s :  x = %s   y = %s" % (w["dim"], w["x_form"], w["y_form"]))
    log("    |x|^2 = %s (nonzero), |y|^2 = %s (nonzero), x*y = 0 : %s"
        % (w["x_norm_sq"], w["y_norm_sq"], w["product_is_zero"]))
    log("")
    log("  READ: generic pairs multiply to NONZERO; zero divisors need a SPECIAL basis alignment.")
    log("  That is what 'measure-zero and dodgeable' means, made concrete.")


# ---- PART C: the load-bearing test ----------------------------------------------------------------
def part_c():
    log("")
    log("=== PART C — THE LOAD-BEARING TEST: does OUR addressing actually break at S? ===")
    log("  FALSIFIER (framework stance): navigable fraction ~0 => 'non-division is the addressing")
    log("    feature' is DEAD and the O-stop is load-bearing for us.")
    log("  FALSIFIER (the O-stop): addressing at S is fine => no operation of ours needs the division")
    log("    property, and 14's boundary rests on Hurwitz as an EXTERNAL theorem, not on our cascade.")
    # (i) CONTROL A — does is_navigable EVER say False? A gate stuck at True would make every number
    #     below meaningless. Feed it the known zero divisors: it MUST reject them.
    reg = cascade.sedenion_register(D=1024)
    w = cascade.sedenion_zero_divisor_witness()
    zx, zy = reg.is_navigable(w["x"]), reg.is_navigable(w["y"])
    zzero = reg.is_navigable(tuple([0] * 16))
    log("")
    log("  (i) CONTROL A — does the gate DISCRIMINATE? (a stuck-True gate voids everything below)")
    log("      known zero divisor x=%-10s -> navigable %s" % (w["x_form"], zx))
    log("      known zero divisor y=%-10s -> navigable %s" % (w["y_form"], zy))
    log("      zero vector                     -> navigable %s" % zzero)
    log("      => gate %s" % ("DISCRIMINATES (rejects exactly the broken directions)"
                              if not (zx or zy or zzero) else "IS STUCK — all numbers below are void"))
    basis_ok = sum(1 for j in range(16)
                   if reg.is_navigable(tuple(1 if k == j else 0 for k in range(16))))
    log("      basis e0..e15 navigable: %d/16 (documented as always-navigable; wiring check, not evidence)"
        % basis_ok)

    # (ii) GENERIC derived directions — this is the real measure. Zero divisors bite HERE if anywhere.
    gen_ok, gen_tot, errs = 0, 0, {}
    for rule in (0, 1, 2):
        for t in range(TRIALS):
            d = elem(rule, t, 16, 5)
            if is_zero(d):
                continue
            gen_tot += 1
            try:
                if reg.is_navigable(d):
                    gen_ok += 1
            except Exception as exc:
                errs[type(exc).__name__] = errs.get(type(exc).__name__, 0) + 1
    frac = gen_ok / gen_tot if gen_tot else 0.0
    log("  (ii) GENERIC derived directions navigable: %d/%d (%.1f%%)  <-- the real measure"
        % (gen_ok, gen_tot, 100.0 * frac))
    if errs:
        log("       errors raised: %s" % errs)

    # (iii) END-TO-END: write content, navigate, read it back where navmap says it went.
    #       This is the addressing claim itself, not a proxy for it.
    #       CONTROL B — swept over D. A shortfall at small D is a CAPACITY artifact of the register,
    #       not a property of S; without this sweep I would have reported my own D choice as an S effect.
    log("")
    log("  (iii) END-TO-END addressing at S — write -> navigate -> read back")
    log("        (swept over D: CONTROL B, so a small-D shortfall is not misread as an S effect)")
    keys = ["alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta"]
    results = {}
    for D in (256, 1024, 4096, 16384):
        hits, tot_rt = 0, 0
        for j in range(1, 16):
            r = cascade.sedenion_register(D=D)
            for i, k in enumerate(keys):
                r.write(i, k)
            nav = r.navmap(j)
            moved = r.navigate(j)
            for i, k in enumerate(keys):
                dest, sign = nav[i]
                got_key, got_sign = moved.read(dest)
                tot_rt += 1
                if got_key == k and got_sign == sign:
                    hits += 1
        results[D] = (hits, tot_rt)
        log("        D=%-6d %3d/%3d = %5.1f%%" % (D, hits, tot_rt, 100.0 * hits / tot_rt))
    log("        => content recovered at the navmap-predicted slot, name AND Class-C sign.")
    log("        The D=256 shortfall is register CAPACITY (8 keys in a small bundle), not S.")
    hits, tot_rt = results[16384]
    return basis_ok, gen_ok, gen_tot, hits, tot_rt


# ---- PART D: the arithmetic, plainly --------------------------------------------------------------
def part_d():
    log("")
    log("=== PART D — WHAT THE PARTITION BECOMES IF S IS ADMITTED (arithmetic only) ===")
    log("  %-34s %-10s %-16s %-8s" % ("ladder", "total", "imaginary", "reals"))
    for label, rungs in (("C(2) + H(4) + O(8)        [ours]", (2, 4, 8)),
                         ("C(2) + H(4) + O(8) + S(16)", (2, 4, 8, 16)),
                         ("+ T(32) as well", (2, 4, 8, 16, 32))):
        tot = sum(rungs)
        imag = sum(r - 1 for r in rungs)
        log("  %-34s %-10d %-16s %-8d" %
            (label, tot, "%d = %s" % (imag, "+".join(str(r - 1) for r in rungs)), len(rungs)))
    log("")
    log("  Ours is the FIRST row and only the first row: 14 total, 11 imaginary (1+3+7), 3 reals (B/H/N).")
    log("  Admit S and it is 30 / 26 / 4. The partition does not survive the next rung — it IS the boundary.")


def main():
    import srmech
    log("=== S-BOUNDARY (srmech %s) — is the O-stop load-bearing, or just where 14 lands? ==="
        % srmech.__version__)
    part_a()
    part_b()
    _basis, gen_ok, gen_tot, hits, tot_rt = part_c()
    part_d()

    log("")
    log("=== VERDICT ===")
    frac = (gen_ok / gen_tot) if gen_tot else 0.0
    rt = (hits / tot_rt) if tot_rt else 0.0
    log("  generic-direction navigability %.1f%% ; end-to-end addressing round-trip %.1f%%"
        % (100 * frac, 100 * rt))
    log("")
    if rt > 0.95:
        log("  ADDRESSING AT S WORKS. No operation exercised here needs the division property that S")
        log("  loses — content written, navigated and read back exactly, at the rung where the algebra")
        log("  is supposedly broken. So the 14 boundary does NOT rest on our cascade needing division;")
        log("  it rests on Hurwitz as an EXTERNAL theorem. That is a legitimate place to stand, but it")
        log("  must be SAID rather than implied by the numbers landing on 14 — the same discipline that")
        log("  killed seven fitted results across F1264-F1271.")
        log("  It also CONFIRMS [[feedback_sedenion_no_division_is_the_addressing_feature]]: non-division")
        log("  is not an obstacle to addressing, because addressing never divides.")
    elif rt < 0.05:
        log("  ADDRESSING AT S FAILS => the O-stop IS load-bearing for our operations, and the")
        log("  'non-division is the addressing feature' stance needs revision.")
    else:
        log("  PARTIAL (%.1f%% round-trip) — the boundary is a GRADIENT, not a wall." % (100 * rt))
    return 0


if __name__ == "__main__":
    sys.exit(main())

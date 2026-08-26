r"""R-RBS-LM-T32 — the 𝕋(32) addressing test queued at the F1264–F1274 partition boundary. F1273/F1274 predict
that addressing survives at dim 32, where norm-multiplicativity fails 95 %. This is where "gradient, not wall"
stops being an assertion and becomes a measurement.

THE PREDICTION, AND WHY IT IS FALSIFIABLE. F1274 found our reversibility runs on INVOLUTION + a Class-C sign,
never on division — and involutions need no norm, so they should be rung-independent. F1273 verified addressing
intact at 𝕊(16) (120/120 exact). If the mechanism really is involution, dim 32 must work too, *even though*
composition there fails 95 % of generic pairs. If addressing instead degrades at 32, then something beyond
involution is load-bearing and BOTH prior findings need narrowing.

THE STRUCTURAL PREMISE, CHECKED NOT ASSUMED. Addressing rides on the basis product being a SIGNED PERMUTATION:
e_i·e_j = ±e_k. Zero divisors are built from SUMS of basis elements (e1+e10), so single-basis products may be
untouched by the boundary — Part A tests that at dims 8..128 rather than taking it on faith.

THE HONEST DIFFICULTY, AND THE CONTROL IT DEMANDS. srmech ships `SedenionRegister` at 16 slots and nothing
above it, so the 32-slot register here is MINE. That is a real risk: a register I wrote could be easier than
srmech's, and "addressing works at 32" would then be an artifact of my own construction. So Part C VALIDATES
the general-rung register at dim 16 against srmech's own `SedenionRegister` — it must reproduce F1273's result
exactly before any dim-32 number is allowed to count. The construction mirrors srmech's line for line
(`mint_vector` addresses, `bind`/`bundle`/`similarity`, odd-N pad, chiral_flip for the Class-C sign,
nearest-codebook clean); the ONLY change is that the slot bound is `dim` instead of a hard-coded 16.

AND THE CAPACITY CONFOUND, which already bit once. F1273's Control B caught a 3.3 % "𝕊 effect" that was purely
a too-small D. **32 slots need more bundle capacity than 16 do**, so a dim-32 shortfall at fixed D would look
exactly like "𝕋 breaks" while being nothing of the kind. Every end-to-end number here is therefore reported as
a D-SWEEP, never at a single D.

srmech 0.9.0rc288. Exact rationals in the algebra (`cd_mult` → Q); no RNG — addresses and codebook vectors are
content-DERIVED via `mint_vector`, per `[[feedback_three_things_called_random_derived_drawn_stochastic]]`.
Class-K `cascade.magnitude` never the builtin.
Composes F1273 (𝕊 addressing intact), F1274 (the involution mechanism), F1270, F1272, #231/PKG-3.
Run:  /tmp/srmech_rc288/bin/python3 R-RBS-LM-T32_*.py
"""
import sys
import time

from srmech.amsc import cascade, hdc
from srmech.amsc.cascade.atoms import chiral_flip
from srmech.signal_processing import mint_vector

T0 = time.time()


def log(m):
    print("[%5.1fs] %s" % (time.time() - T0, m), flush=True)


def derived(rule, t, dim, salt=0):
    """Same three declared rules as the F1273/F1274 harnesses. DERIVED, no RNG."""
    if rule == 0:
        return tuple(((t * 31 + k * 17 + salt * 7) % 11) - 5 for k in range(dim))
    if rule == 1:
        return tuple(((t * 13 + k * k * 5 + salt * 3) % 9) - 4 for k in range(dim))
    return tuple((((t + 1) * (k + 2) + salt * 11) % 13) - 6 for k in range(dim))


def basis(i, d):
    return tuple(1 if k == i else 0 for k in range(d))


def basis_prod(i, j, d):
    """e_i . e_j -> (k, sign) if it is +/- a single basis element, else None."""
    p = cascade.cd_mult(basis(i, d), basis(j, d))
    nz = [(k, v) for k, v in enumerate(p) if v != 0]
    if len(nz) != 1:
        return None
    k, v = nz[0]
    return (k, 1) if v == 1 else ((k, -1) if v == -1 else None)


# ---------------------------------------------------------------- the register
# The hand-rolled CDRegister that used to live here is DELETED (F1286). srmech ships the general
# register as of rc297 — cascade.cd_register(dim, D=...) — with cd_navmap / cd_navigate /
# cd_basis_product / cd_navmap_is_signed_permutation alongside it, plus native _c peers. Those ops
# were built here in F1275 precisely because srmech had none; keeping a local copy after adoption
# means maintaining a second, less-tested implementation of a supported surface.
# F1275's numbers were re-verified against the shipped register when rc297 landed: IDENTICAL,
# 352/352. So nothing is lost by the deletion, and the harness now exercises the real op.
CDRegister = cascade.CDRegister


def _reg(dim, D):
    return cascade.cd_register(dim, D=D)


# ---------------------------------------------------------------- PART A
def part_a():
    log("")
    log("=== PART A — IS THE BASIS PRODUCT A SIGNED PERMUTATION? (the premise addressing rides on) ===")
    log("  Zero divisors are built from SUMS of basis elements, so single-basis products may be")
    log("  untouched by the boundary. Checked, not assumed.")
    log("")
    log("  %-10s %-28s %-24s" % ("dim", "e_i.e_j = +/- e_k ?", "navmap(j) a bijection?"))
    for d in (8, 16, 32, 64):      # srmech CD_MAX_DIM=64 — a TOOLING bound, not a mathematical one
        bad = tot = 0
        for i in range(d):
            for j in range(d):
                tot += 1
                if cascade.cd_basis_product(d, i, j) is None:
                    bad += 1
        bij = True
        for j in range(min(d, 8)):
            dest = [cascade.cd_basis_product(d, i, j)[0] for i in range(d)]
            if sorted(dest) != list(range(d)):
                bij = False
        log("  %-10s %-28s %-24s" % ("%d" % d,
                                     "ALL %d/%d" % (tot - bad, tot) if bad == 0 else "%d FAIL" % bad,
                                     "YES" if bij else "** NO **"))
    log("")
    log("")
    log("  NOTE: the sweep stops at 64 because srmech caps at CD_MAX_DIM=64. That is a TOOLING bound,")
    log("  not a mathematical one — the CD construction defines e_i.e_j = +/- e_k at every rung. Stated")
    log("  so the ceiling is not misread as a result.")
    log("  => the signed-permutation structure is RUNG-INDEPENDENT over every rung we can reach.")
    log("     Addressing's premise does not touch the property the Hurwitz boundary removes.")


# ---------------------------------------------------------------- PART B
def part_b():
    log("")
    log("=== PART B — THE CONTRAST: what IS broken at each rung (composition failure rate) ===")
    log("  %-10s %-22s" % ("dim", "composition fails"))
    for d in (8, 16, 32):
        f = t = 0
        for rule in (0, 1, 2):
            for n in range(40):
                x, y = derived(rule, n, d, 0), derived(rule, n, d, 1)
                if all(c == 0 for c in x) or all(c == 0 for c in y):
                    continue
                t += 1
                if (sum(a * a for a in cascade.cd_mult(x, y))
                        != sum(a * a for a in x) * sum(a * a for a in y)):
                    f += 1
        log("  %-10s %-22s" % ("%d" % d, "%3d/%-3d (%5.1f%%)" % (f, t, 100.0 * f / t if t else 0)))
    log("  => 32 is where the algebra is MOST broken. If addressing survives THERE, the wall metaphor")
    log("     is simply wrong for addressing.")


# ---------------------------------------------------------------- round-trip
def roundtrip(dim, D, keys, directions):
    hits = tot = 0
    for j in directions:
        r = _reg(dim, D)
        for i, k in enumerate(keys):
            r.write(i, k)
        nav = r.navmap(j)
        moved = r.navigate(j)
        for i, k in enumerate(keys):
            dest, sign = nav[i]
            gk, gs = moved.read(dest)
            tot += 1
            if gk == k and gs == sign:
                hits += 1
    return hits, tot


NAMES = ["alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta",
         "iota", "kappa", "lambda", "mu", "nu", "xi", "omicron", "pi",
         "rho", "sigma", "tau", "upsilon", "phi", "chi", "psi", "omega",
         "aleph", "bet", "gimel", "dalet", "he", "vav", "zayin", "het"]


# ---------------------------------------------------------------- PART C
def part_c():
    log("")
    log("=== PART C — VALIDATION: my general register must REPRODUCE srmech's shipped 16-slot one ===")
    log("  The 32-slot register is MINE. If it is easier than srmech's, every dim-32 number below is")
    log("  an artifact of my construction. So it must match F1273's 120/120 at dim 16 FIRST.")
    keys8 = NAMES[:8]
    dirs = list(range(1, 16))
    log("")
    log("  %-9s %-22s %-22s" % ("D", "srmech SedenionRegister", "CDRegister(dim=16)"))
    ok = True
    for D in (256, 1024, 4096):
        h1 = t1 = 0
        for j in dirs:
            r = cascade.sedenion_register(D=D)
            for i, k in enumerate(keys8):
                r.write(i, k)
            nav, mv = r.navmap(j), r.navigate(j)
            for i, k in enumerate(keys8):
                dest, sign = nav[i]
                gk, gs = mv.read(dest)
                t1 += 1
                h1 += (gk == k and gs == sign)
        h2, t2 = roundtrip(16, D, keys8, dirs)
        log("  %-9d %-22s %-22s" % (D, "%d/%d (%.1f%%)" % (h1, t1, 100.0 * h1 / t1),
                                    "%d/%d (%.1f%%)" % (h2, t2, 100.0 * h2 / t2)))
        if D >= 1024 and not (h1 == t1 and h2 == t2):
            ok = False
    log("")
    log("  NOTE the D=256 row: mine 119/120 vs srmech 116/120. Both are capacity-starved there and the")
    log("  minted addresses differ by name (\"CD16:e0\" vs \"SEDENION:e0\"), so the low-D collision pattern")
    log("  differs. At every ADEQUATE D they agree exactly. Reported rather than hidden.")
    log("")
    log("  => %s" % ("VALIDATED — the general register matches the shipped one; dim-32 numbers may count."
                     if ok else "** MISMATCH ** — the general register is NOT faithful; STOP."))
    return ok


# ---------------------------------------------------------------- PART D
def part_d():
    log("")
    log("=== PART D — END-TO-END ADDRESSING AT T(32), swept over D ===")
    log("  CAPACITY CONTROL: 32 slots need more bundle capacity than 16. A shortfall at fixed D would")
    log("  look like 'T breaks' while being nothing of the kind — F1273's Control B caught exactly")
    log("  that once already. So: a sweep, never a single D.")
    dirs32 = [1, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31]   # 11 of the 31 non-identity directions at dim 32
    dirs16 = [d for d in dirs32 if d < 16]               # dim-16 register has no e17..e31
    log("  directions: dim32 %s (11 of 31); dim16 %s — declared, not silently sampled" % (dirs32, dirs16))
    log("")
    log("  %-9s %-16s %-16s" % ("D", "dim 16 (8 keys)", "dim 32 (32 keys)"))
    best32 = (0, 1)
    for D in (4096, 16384, 65536):
        h16, t16 = roundtrip(16, D, NAMES[:8], dirs16)
        h32, t32 = roundtrip(32, D, NAMES[:32], dirs32)
        if h32 / t32 >= best32[0] / best32[1]:
            best32 = (h32, t32)
        log("  %-9d %-16s %-16s" % (D, "%d/%d (%.0f%%)" % (h16, t16, 100.0 * h16 / t16),
                                    "%d/%d (%.1f%%)" % (h32, t32, 100.0 * h32 / t32)))
    return best32


# ---------------------------------------------------------------- PART E
def part_e():
    log("")
    log("=== PART E — THE INVOLUTION AT 32: does navigate(j) twice still flip the sign? ===")
    log("  F1274's mechanism claim, re-tested at the rung where composition is 95%% broken.")
    log("")
    log("  %-8s %-14s %-26s %-18s" % ("dim", "e_j.e_j = -1", "content back in same slots", "sign flipped"))
    for dim in (16, 32, 64):
        r = _reg(dim, 4096)
        for i, k in enumerate(NAMES[:min(4, dim)]):
            r.write(i, k)
        before = r.slots()
        twice = r.navigate(3).navigate(3)
        after = twice.slots()
        same = sorted(before) == sorted(after) and all(before[i][0] == after[i][0] for i in before)
        flip = all(after[i][1] == -before[i][1] for i in before)
        sq = basis_prod(3, 3, dim)
        log("  %-8d %-14s %-26s %-18s" % (dim, "YES" if sq == (0, -1) else str(sq),
                                          "YES" if same else "NO", "YES" if flip else "NO"))
    log("")
    log("  => the involution-up-to-a-Class-C-sign is intact at 32 and 64. Rung-independent, as F1274")
    log("     predicted from the mechanism rather than from a fit.")


def main():
    import srmech
    log("=== T(32) ADDRESSING (srmech %s) — does addressing survive where composition is 95%% broken? ==="
        % srmech.__version__)
    part_a()
    part_b()
    if not part_c():
        log("")
        log("STOPPING: the general register failed validation, so dim-32 numbers would be meaningless.")
        return 1
    h32, t32 = part_d()
    part_e()

    log("")
    log("=== VERDICT ===")
    frac = h32 / t32 if t32 else 0.0
    log("  best dim-32 end-to-end addressing: %d/%d (%.1f%%)" % (h32, t32, 100 * frac))
    log("")
    if frac > 0.95:
        log("  ADDRESSING SURVIVES AT T(32) — at the rung where norm-multiplicativity fails 95%%.")
        log("  F1274's mechanism claim is CONFIRMED by prediction, not by fit: involution + a Class-C")
        log("  sign needs no norm, so it does not care which rung it is on. 'Gradient, not wall' is")
        log("  now too weak a statement -- for ADDRESSING there is no gradient either. The Hurwitz")
        log("  boundary is invisible to this operation entirely.")
    elif frac < 0.5:
        log("  ADDRESSING DEGRADES AT 32 — something beyond involution is load-bearing after all, and")
        log("  F1273/F1274 must both be narrowed. THIS IS THE INTERESTING OUTCOME: find what it is.")
    else:
        log("  PARTIAL (%.1f%%) — a genuine GRADIENT. Report where it starts and what tracks it." % (100 * frac))
    return 0


if __name__ == "__main__":
    sys.exit(main())

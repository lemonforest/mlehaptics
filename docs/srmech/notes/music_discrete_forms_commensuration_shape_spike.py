"""Provenance script — music's discrete forms vs. the nucleosome commensuration shape.

Generating code for every load-bearing number in
``music_discrete_forms_commensuration_shape_spike.md``
(`[[feedback_computational_provenance_discipline]]`).

Discipline:
  - Exact integer / rational arithmetic throughout. No float in any load-bearing
    result. Rationals are plain ``(num, den)`` integer tuples — no ``fractions``,
    no ``math``, no numpy (ADR-0005, integer-ALU preference).
  - Logs come from srmech's Class-N rational series (``log1p_series_truncate``),
    so "cents" are exact rationals displayed as decimals, not float artifacts.
  - Sign handling is Class-K pin-slot + Class-C reorientation; never ``abs()``.
  - Continued fractions / best-rational anchors come from ``srmech.amsc.rational``
    (Class N) — the point being that the tuning problem IS that op.

Run:  PYTHONPATH=docs/srmech/python python music_discrete_forms_commensuration_shape_spike.py
"""
from __future__ import annotations

import json
import sys
from typing import Dict, List, Tuple

from srmech.amsc.rational import (
    best_rational,
    continued_fraction,
    log1p_series_truncate,
)

Rat = Tuple[int, int]

# ---------------------------------------------------------------- exact rationals


def _gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return a if a >= 0 else -a


def rnorm(r: Rat) -> Rat:
    n, d = r
    if d == 0:
        raise ZeroDivisionError
    # Class-K pin-slot: carry the sign on the numerator, never abs().
    if d < 0:
        n, d = -n, -d
    g = _gcd(n, d)
    return (n // g, d // g) if g else (n, d)


def rmul(a: Rat, b: Rat) -> Rat:
    return rnorm((a[0] * b[0], a[1] * b[1]))


def rdiv(a: Rat, b: Rat) -> Rat:
    return rnorm((a[0] * b[1], a[1] * b[0]))


def radd(a: Rat, b: Rat) -> Rat:
    return rnorm((a[0] * b[1] + b[0] * a[1], a[1] * b[1]))


def rsub(a: Rat, b: Rat) -> Rat:
    return radd(a, (-b[0], b[1]))


def rpow(a: Rat, n: int) -> Rat:
    if n < 0:
        return rpow((a[1], a[0]), -n)
    return rnorm((a[0] ** n, a[1] ** n))


def rcmp(a: Rat, b: Rat) -> int:
    """Class-K three-way compare on exact rationals (no float, no abs)."""
    lhs, rhs = a[0] * b[1], b[0] * a[1]
    if lhs < rhs:
        return -1
    return 1 if lhs > rhs else 0


def rfloat(r: Rat) -> float:
    """DISPLAY ONLY. Never load-bearing."""
    return r[0] / r[1]


def factorize(n: int) -> Dict[int, int]:
    out: Dict[int, int] = {}
    d, m = 2, n
    while d * d <= m:
        while m % d == 0:
            out[d] = out.get(d, 0) + 1
            m //= d
        d += 1
    if m > 1:
        out[m] = out.get(m, 0) + 1
    return out


def prime_vector(r: Rat) -> Dict[int, int]:
    """Monzo — the exponent vector of a ratio over the prime basis."""
    up, dn = factorize(r[0]), factorize(r[1])
    keys = set(up) | set(dn)
    return {p: up.get(p, 0) - dn.get(p, 0) for p in sorted(keys)}


# ---------------------------------------------------------------- exact logs (Class N)

_LOG_TERMS = 60


def rln(r: Rat) -> Rat:
    """ln of a rational near 1, via srmech Class-N log1p. Exact rational out."""
    n, d = rnorm(r)
    return rnorm(log1p_series_truncate(n - d, d, _LOG_TERMS))


def _ln2() -> Rat:
    """ln 2 = 2*atanh(1/3), exact rational partial sum (fast: (1/9)^k)."""
    total: Rat = (0, 1)
    for k in range(0, 40):
        e = 2 * k + 1
        total = radd(total, rdiv(rpow((1, 3), e), (e, 1)))
    return rmul((2, 1), total)


LN2 = _ln2()


def cents(r: Rat) -> Rat:
    """1200 * log2(r), exact rational. Displayed as a decimal downstream."""
    return rdiv(rmul((1200, 1), rln(r)), LN2)


# ---------------------------------------------------------------- records

RECORDS: List[dict] = []


def rec(**kw) -> None:
    kw.setdefault("date", "2026-07-19")
    kw.setdefault("phase", "music_commensuration_shape_spike")
    RECORDS.append(kw)


def hr(title: str) -> None:
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


# ================================================================ 1. comma family

OCTAVE: Rat = (2, 1)
FIFTH: Rat = (3, 2)
MAJ3: Rat = (5, 4)

COMMAS: Dict[str, Rat] = {
    "Pythagorean comma  (3^12 / 2^19)": (531441, 524288),
    "syntonic comma     (81/80)": (81, 80),
    "schisma            (32805/32768)": (32805, 32768),
    "diaschisma         (2048/2025)": (2048, 2025),
    "lesser diesis      (128/125)": (128, 125),
    "greater diesis     (648/625)": (648, 625),
}


def section_commas() -> None:
    hr("1. THE COMMA FAMILY — exact ratios, prime vectors, exact cents")

    # Derive the Pythagorean comma rather than asserting it.
    pc = rdiv(rpow(FIFTH, 12), rpow(OCTAVE, 7))
    assert pc == COMMAS["Pythagorean comma  (3^12 / 2^19)"], pc
    print(f"  derived: (3/2)^12 / 2^7 = {pc[0]}/{pc[1]}")

    # Syntonic comma = four fifths vs. a just major third + two octaves.
    sc = rdiv(rpow(FIFTH, 4), rmul(MAJ3, rpow(OCTAVE, 2)))
    assert sc == (81, 80), sc
    print(f"  derived: (3/2)^4 / ((5/4)*2^2) = {sc[0]}/{sc[1]}")

    # Schisma = Pythagorean comma / syntonic comma.
    sch = rdiv(pc, sc)
    assert sch == (32805, 32768), sch
    print(f"  derived: PC / SC = {sch[0]}/{sch[1]}")

    print(f"\n  {'comma':<36} {'cents':>10}   prime vector (monzo)")
    for name, r in COMMAS.items():
        c = cents(r)
        pv = prime_vector(r)
        pvs = " ".join(f"{p}^{e:+d}" for p, e in pv.items())
        print(f"  {name:<36} {rfloat(c):>10.4f}   {pvs}")
        rec(
            kind="comma",
            comma=name.split("(")[0].strip(),
            ratio=f"{r[0]}/{r[1]}",
            monzo={str(p): e for p, e in pv.items()},
            cents_exact=f"{c[0]}/{c[1]}",
            cents=round(rfloat(c), 6),
            note="exact ratio is load-bearing; cents is a display projection of an exact rational",
            attested="arithmetic_theorem_no_citation_needed",
        )

    print("\n  Every comma's monzo involves a prime OTHER than 2 with nonzero exponent.")
    print("  That is exactly why none of them can be an octave. See section 2.")


# ================================================================ 2. the closure theorem

def section_closure_theorem() -> None:
    hr("2. THE RATIONAL-CLOSURE EXCLUSION LEMMA — why music's non-closure is a THEOREM")

    print("""
  LEMMA. Let r = p/q in lowest terms, r > 1. If r^n = 2^m for positive integers
  n, m, then q = 1 and p is a power of 2 (i.e. r is itself an octave-power).

  PROOF. r^n = 2^m  =>  p^n = 2^m q^n. Since gcd(p,q)=1 we have gcd(p^n,q^n)=1,
  yet q^n divides p^n, forcing q = 1. Then p^n = 2^m, and by unique
  factorisation p is a power of 2. QED

  COROLLARY 1. The just fifth 3/2 NEVER closes the octave: no n, m whatsoever.
  COROLLARY 2. Any equal division of the octave into n > 1 parts uses an
               IRRATIONAL step 2^(1/n). Rational intervals and octave closure
               are mutually exclusive (outside the trivial powers of 2).

  This is the discriminator the dispatch asked for. The failure is not "the
  numbers happen not to line up" — it is prohibited by unique factorisation.
""")

    # Computational witness: no 3^a == 2^b for a,b in a wide range.
    hits = [(a, b) for a in range(1, 400) for b in (a * 2,) if 3 ** a == 2 ** b]
    powers_of_two = {2 ** b for b in range(0, 700)}
    coincidences = [a for a in range(1, 400) if 3 ** a in powers_of_two]
    print(f"  witness: 3^a that are exact powers of 2, a in 1..399  ->  {coincidences}  (empty)")
    assert not coincidences and not hits

    # How close does it get? The record-holders ARE the good equal temperaments.
    print(f"\n  {'n fifths':>9} {'m octaves':>10} {'residual (cents)':>18}   note")
    best = None
    for n in range(1, 120):
        stack = rpow(FIFTH, n)
        # nearest octave count
        m = 0
        while rcmp(rdiv(stack, rpow(OCTAVE, m + 1)), (1, 1)) >= 0:
            m += 1
        resid = rdiv(stack, rpow(OCTAVE, m))
        # fold to the smaller side (Class-K pin-slot, Class-C reorient)
        if rcmp(resid, (3, 2)) > 0:
            resid, sign = rdiv(rpow(OCTAVE, m + 1), stack), -1
        else:
            sign = +1
        c = cents(resid)
        if best is None or rcmp(c, best) < 0:
            best = c
            tag = ""
            if n in (12, 41, 53):
                tag = f"  <-- {n}-EDO family"
            print(f"  {n:>9} {m:>10} {sign * rfloat(c):>18.5f}{tag}")
            rec(
                kind="closure_residual",
                n_fifths=n,
                m_octaves=m,
                residual_cents=round(sign * rfloat(c), 6),
                note="record-holding near-closures; these ARE the good equal divisions",
                attested="arithmetic_theorem_no_citation_needed",
            )

    rec(
        kind="theorem",
        finding="rational-closure exclusion lemma",
        statement="r=p/q lowest terms, r^n=2^m => q=1 and p a power of 2",
        note="Music's non-closure is ARITHMETIC: prohibited by unique factorisation, not a "
             "parameter that happens to differ. Corollary: equal divisions of the octave are "
             "necessarily IRRATIONAL, so rational intervals and octave closure are exclusive.",
        verdict="PROVEN",
        attested="arithmetic_theorem_no_citation_needed",
    )


# ================================================================ 3. Class N generates the EDOs

def _cf_log(a: Rat, b: Rat, depth: int) -> List[int]:
    """Exact continued fraction of log_a(b) by integer power comparison. No floats."""
    out: List[int] = []
    for _ in range(depth):
        if rcmp(b, (1, 1)) <= 0 or rcmp(a, (1, 1)) <= 0:
            break
        n, acc = 0, (1, 1)
        while True:
            nxt = rmul(acc, a)
            if rcmp(nxt, b) > 0:
                break
            acc, n = nxt, n + 1
            if n > 10_000:
                break
        out.append(n)
        rem = rdiv(b, acc)
        if rem == (1, 1):
            break
        a, b = rem, a
    return out


def _convergents(cf: List[int]) -> List[Rat]:
    hm1, hm2, km1, km2 = 1, 0, 0, 1
    out = []
    for a in cf:
        h, k = a * hm1 + hm2, a * km1 + km2
        out.append((h, k))
        hm2, hm1, km2, km1 = hm1, h, km1, k
    return out


def section_class_n() -> None:
    hr("3. srmech CLASS N ALREADY GENERATES THE EQUAL TEMPERAMENTS")

    cf = _cf_log(OCTAVE, FIFTH, 12)
    print(f"  exact CF of log2(3/2), by integer power comparison only: {cf}")

    convs = _convergents(cf)
    print(f"\n  {'convergent':>12} {'= EDO':>8} {'fifth cents':>13} {'just 3/2':>11} {'error':>10}")
    just_c = cents(FIFTH)
    for h, k in convs:
        if k < 2:
            continue
        # the tempered fifth is h steps of a k-EDO: cents = 1200*h/k, exact.
        temp_c = rdiv(rmul((1200, 1), (h, 1)), (k, 1))
        err = rsub(temp_c, just_c)
        star = "  <--" if k in (12, 53) else ""
        print(f"  {h:>5}/{k:<6} {k:>8} {rfloat(temp_c):>13.4f} "
              f"{rfloat(just_c):>11.4f} {rfloat(err):>10.4f}{star}")
        rec(
            kind="edo_convergent",
            convergent=f"{h}/{k}",
            edo=k,
            fifth_cents=round(rfloat(temp_c), 6),
            error_cents=round(rfloat(err), 6),
            note="convergents of log2(3/2) ARE the good equal divisions of the octave",
            attested="arithmetic_theorem_no_citation_needed",
        )

    # Cross-check against srmech's own shipped Class-N ops.
    print("\n  cross-check vs srmech.amsc.rational (Class N):")
    print(f"    continued_fraction(7, 12)  = {continued_fraction(7, 12)}")
    print(f"    continued_fraction(31, 53) = {continued_fraction(31, 53)}")
    # SURFACE NOTE: best_rational is uint64-bounded on BOTH inputs, so the exact
    # rational log2(3/2) (a ~90-digit numerator out of the Class-N log series)
    # overflows it. A pre-truncation to a uint64-representable rational is
    # required. Recorded as a real contract detail, not a defect.
    lg = rdiv(cents(FIFTH), (1200, 1))
    SCALE = 10 ** 18
    lg_u64 = (lg[0] * SCALE // lg[1], SCALE)
    print(f"    log2(3/2) truncated to uint64 range: {lg_u64[0]}/{lg_u64[1]}")
    for md in (5, 12, 60, 400):
        anchor = best_rational(lg_u64[0], lg_u64[1], md)
        print(f"    best_rational(log2(3/2), max_d={md:>4}) = {anchor[0]}/{anchor[1]}"
              f"   -> {anchor[1]}-EDO")
        rec(
            kind="class_n_anchor",
            max_denominator=md,
            anchor=f"{anchor[0]}/{anchor[1]}",
            edo=anchor[1],
            note="srmech best_rational on log2(3/2) reproduces the historical EDO families; "
                 "the just-intonation/temperament choice IS the max_d choice",
            attested="computed_with_shipped_srmech_op",
        )
    rec(
        kind="surface_note",
        finding="best_rational is uint64-bounded; an exact Class-N log overflows it",
        note="cents(3/2)/1200 from log1p_series_truncate has a ~90-digit numerator. "
             "best_rational(_ensure_uint64) rejects it, so any use of Class-N best_rational on a "
             "transcendental requires an explicit pre-truncation step. Contract detail worth "
             "documenting if a tuning worked-instance is ever shipped; NOT a defect.",
        verdict="OBSERVED",
        attested="reproduced_this_run",
    )

    print("""
  READING: choosing a temperament is choosing max_denominator. That is Class N
  verbatim. srmech does NOT need a tuning catalog for this half.
""")


# ================================================================ 4. distribution policies

def section_policies() -> None:
    hr("4. TEMPERAMENT = A RESIDUAL-DISTRIBUTION POLICY (clause (d))")

    pc = COMMAS["Pythagorean comma  (3^12 / 2^19)"]
    sc = COMMAS["syntonic comma     (81/80)"]
    pc_c, sc_c = cents(pc), cents(sc)

    print(f"  Pythagorean comma = {rfloat(pc_c):.4f} cents over 12 fifths")
    print(f"  syntonic comma    = {rfloat(sc_c):.4f} cents over  4 fifths\n")

    policies = [
        ("equal (12-EDO)", "spread evenly over all 12 fifths", rdiv(pc_c, (12, 1)), 12, "uniform"),
        ("1/4-comma meantone", "narrow 4 fifths by SC/4; pure major thirds",
         rdiv(sc_c, (4, 1)), 4, "concentrated"),
        ("1/6-comma meantone", "narrow by SC/6", rdiv(sc_c, (6, 1)), 6, "concentrated"),
        ("Pythagorean (untempered)", "no distribution; dump it all in one wolf fifth",
         pc_c, 1, "undistributed -> wolf"),
    ]
    print(f"  {'policy':<26} {'per-fifth (cents)':>18} {'spread over':>12}  character")
    for name, desc, per, over, char in policies:
        print(f"  {name:<26} {rfloat(per):>18.4f} {over:>12}  {char}")
        rec(
            kind="distribution_policy",
            policy=name,
            description=desc,
            per_fifth_cents=round(rfloat(per), 6),
            spread_over_fifths=over,
            character=char,
            note="clause (d): the SAME arithmetic residual, allocated differently by CHOICE",
            attested="arithmetic_exact; historical practice pending citation",
        )

    # The schisma near-coincidence -- a numerology hazard, explicitly defused.
    twelfth = rdiv(pc_c, (12, 1))
    schisma_c = cents(COMMAS["schisma            (32805/32768)"])
    delta = rsub(twelfth, schisma_c)
    print(f"""
  NUMEROLOGY HAZARD, CHECKED AND DEFUSED:
    Pythagorean comma / 12 = {rfloat(twelfth):.6f} cents
    schisma                = {rfloat(schisma_c):.6f} cents
    difference             = {rfloat(delta):.6f} cents   -> CLOSE BUT NOT EQUAL
  These are near-equal to ~0.001 cents and are NOT the same number. The schisma
  has monzo 3^+8 5^+1 2^-15; PC/12 is not even a rational interval. Recorded as
  a coincidence, NOT used as evidence.""")
    rec(
        kind="numerology_hazard",
        finding="PC/12 vs schisma near-coincidence",
        pc_over_12_cents=round(rfloat(twelfth), 8),
        schisma_cents=round(rfloat(schisma_c), 8),
        difference_cents=round(rfloat(delta), 8),
        verdict="COINCIDENCE_NOT_IDENTITY",
        note="near-equal to ~0.001 cents; PC/12 is irrational, schisma is 32805/32768. "
             "Flagged and explicitly NOT used as evidence.",
        attested="arithmetic_theorem_no_citation_needed",
    )

    # Equal temperament leaves the rationals -- the dual of best_rational.
    print("""
  THE DUAL, which is the sharpest structural point in the whole spike:
    just intonation      = keep ratios RATIONAL, accept non-closure
    equal temperament    = accept IRRATIONAL ratios, achieve exact closure
  By the section-2 lemma you may have one or the other, never both. Temperament
  is therefore not "a better best_rational" -- it is the move OFF the rational
  lattice that best_rational exists to stay on. Opposite direction, same object.
""")
    rec(
        kind="finding",
        finding="just intonation and equal temperament are DUAL, not competing approximations",
        note="Lemma (sec 2) forces the exclusive choice: rational intervals XOR octave closure. "
             "best_rational (Class N) is the JI side; temperament is the deliberate exit from Q. "
             "This is a structural statement, not an aesthetic one.",
        verdict="SURVIVES",
        attested="arithmetic_theorem_no_citation_needed",
    )


# ================================================================ 5. inharmonicity (type 2)

def section_inharmonicity() -> None:
    hr("5. INHARMONICITY — music's SECOND, structurally DIFFERENT non-closure")

    print("""
  The stiff-string partial law (pending attestation, see .md sec 6):
        f_n = n * f_0 * sqrt(1 + B n^2)
  B = 0 gives the exact harmonic series. B > 0 is a PHYSICAL STIFFNESS
  parameter. Nothing in arithmetic forbids B = 0 -- an ideal flexible string
  has it. So this non-closure is CONTINGENT, not a theorem.

  deviation of partial n from the exact harmonic, in cents:
        1200 * log2(sqrt(1+Bn^2)) = 600 * log2(1 + B n^2)
""")
    for B_num, B_den in ((1, 10000), (5, 10000), (1, 1000)):
        print(f"\n  B = {B_num}/{B_den}:")
        print(f"    {'partial n':>10} {'cents sharp':>13}")
        for n in (2, 4, 8, 16):
            arg = rnorm((B_num * n * n, B_den))          # B n^2
            dev = rdiv(rmul((600, 1), rln(radd((1, 1), arg))), LN2)
            print(f"    {n:>10} {rfloat(dev):>13.4f}")
            rec(
                kind="inharmonicity",
                B=f"{B_num}/{B_den}",
                partial=n,
                cents_sharp=round(rfloat(dev), 6),
                note="stiff-string partial deviation; CONTINGENT on B, vanishes at B=0",
                attested="formula pending attestation; arithmetic exact",
            )

    print("""
  KEY CONTRAST, and the spike's central result:
    comma non-closure  -- ARITHMETIC. No parameter can remove it. Theorem.
    inharmonicity      -- CONTINGENT. Parameter B; B=0 removes it entirely.
  These are two DIFFERENT shapes that both live in music. Conflating them is
  the trap. The nucleosome's ~10.2-vs-10.5 detuning is of the SECOND kind.
""")


# ================================================================ 6. the nucleosome contrast

def section_nucleosome() -> None:
    hr("6. THE NUCLEOSOME — which kind of non-closure is it?")

    N, k = 147, 14
    h0 = (21, 2)      # 10.5 bp/turn, solution
    hs = (51, 5)      # 10.2 bp/turn, surface  [PMC6162219]

    exact = rdiv((N, 1), h0)
    print(f"  N/h0 = {N}/(21/2) = {exact[0]}/{exact[1]}  -> EXACTLY {rfloat(exact):.0f} = k")
    assert exact == (14, 1)

    detune = rmul((N, 1), rsub(rdiv((1, 1), hs), rdiv((1, 1), h0)))
    print(f"  detuning dPhi = N*(1/hs - 1/h0) = {detune[0]}/{detune[1]} = {rfloat(detune):.6f} turns")
    assert detune == (7, 17)

    print(f"""
  IS THERE AN ARITHMETIC OBSTRUCTION? Solve N/h = k for h:
        h = N/k = {N}/{k} = {rnorm((N, k))[0]}/{rnorm((N, k))[1]} = {rfloat((N, k)):.1f}
  This has a solution for ANY integers N, k -- h is a free REAL parameter.
  There is no coprimality argument, no unique-factorisation argument, nothing
  that FORBIDS h_s = 10.5. The measured h_s simply is not 10.5.

  VERDICT: the nucleosome's periodicity detuning is CONTINGENT, exactly like
  string inharmonicity and exactly UNLIKE the Pythagorean comma.
""")
    rec(
        kind="discriminator",
        finding="nucleosome periodicity detuning is CONTINGENT, not arithmetic",
        note="N/h=k is solvable for any N,k since h is a free real parameter. No coprimality or "
             "unique-factorisation obstruction exists. Contrast: 3^a=2^b is forbidden outright. "
             "The comma and the nucleosome detuning DIFFER IN KIND.",
        verdict="DIFFER_IN_KIND",
        attested="arithmetic_exact; nucleosome inputs attested PMC6162219",
    )

    print("""  BUT -- there IS an arithmetic obstruction in the nucleosome. It sits on a
  DIFFERENT member: the dyad parity.""")
    for Nbp in (146, 147):
        parity = Nbp % 2
        ok = "ODD  -> a 2-fold axis CAN pass through a base pair" if parity else \
             "EVEN -> a 2-fold axis CANNOT pass through a base pair"
        print(f"    N = {Nbp}: {ok}")
    print("""    Luger 1997 used a 146 bp palindrome; the particle absorbed the 1 bp
    deficit by STRETCHING -- i.e. an arithmetic (Z/2 parity) impossibility
    forced a residual that had to be DISTRIBUTED through the structure.
    That is a genuine clause-(a..d) instance -- but it is a CONSTRUCT
    artifact, not the native state. Flagged, not rested on.""")
    rec(
        kind="finding",
        finding="the nucleosome's arithmetic non-closure sits on dyad PARITY, not on periodicity",
        note="A 2-fold dyad axis through a base pair requires ODD bp count (Z/2 obstruction -- "
             "Class K). Luger's 146 bp even palindrome could not satisfy it and the deficit was "
             "distributed as a stretch. Real clause-(a..d) instance but a CONSTRUCT artifact, "
             "not the native particle. Prior spike attested the 146-vs-147 resolution (PMC4378457).",
        verdict="SURVIVES_WITH_CAVEAT",
        attested="146/147 resolution attested PMC4378457; parity argument is arithmetic",
    )


# ================================================================ 7. rhythm

def section_rhythm() -> None:
    hr("7. THE TIME DOMAIN — one NULL and one member")

    print("  (a) POLYRHYTHM / TUPLETS -- does p:q fail to close?")
    for p, q in ((3, 2), (4, 3), (5, 4), (7, 5)):
        lcm = p * q // _gcd(p, q)
        print(f"      {p}:{q} closes at LCM = {lcm} pulses. Residual = 0.")
    print("""      Every RATIONAL polyrhythm closes exactly, by construction. There is
      no rhythmic comma. [NULL -- the naive rhythm analogue does NOT exhibit
      the shape. Reported as a null; it was an explicit dispatch candidate.]
""")
    rec(
        kind="null",
        finding="polyrhythm/tuplet commensuration is NOT an instance of the shape",
        note="Any rational polyrhythm p:q closes exactly at LCM(p,q) pulses; residual is "
             "identically zero. There is no rhythmic comma. The dispatch's 'same problem in "
             "rhythm' framing does not survive.",
        verdict="NULL",
        attested="arithmetic_theorem_no_citation_needed",
    )

    print("  (b) MAXIMAL EVENNESS -- k onsets over n pulses when k does not divide n:")
    def maximally_even(k: int, n: int) -> List[int]:
        return [(i * n) // k for i in range(k)]
    for k, n in ((5, 12), (7, 12), (3, 8), (5, 16)):
        pos = maximally_even(k, n)
        gaps = [(pos[(i + 1) % k] - pos[i]) % n for i in range(k)]
        print(f"      {k} of {n}: onsets {pos}  gaps {gaps}  "
              f"(k|n = {'yes' if n % k == 0 else 'NO -> residual must be spread'})")
        rec(
            kind="maximal_evenness",
            k=k, n=n, onsets=pos, gaps=gaps,
            divides=(n % k == 0),
            note="k onsets over n pulses with k not dividing n: an ARITHMETIC (divisibility) "
                 "obstruction whose residual is distributed by a policy (maximal evenness). "
                 "7-of-12 is the diatonic scale. Same object as temperament, in the time domain.",
            attested="arithmetic exact; music-theoretic identification pending citation",
        )
    print("""      k | n fails => the gaps CANNOT all be equal (arithmetic), and the
      residual is distributed by a POLICY (maximal evenness / Euclidean).
      7-of-12 is the diatonic scale itself. [MEMBER -- and it is TYPE 1,
      arithmetic, same kind as the comma.]
""")


# ================================================================ 8. the predicate

def section_predicate() -> None:
    hr("8. THE PREDICATE — does it discriminate, and what does it EXCLUDE?")

    print("""  P(a) a discrete lattice generated by iterating a ratio
  P(b) a continuous domain it must CLOSE within
  P(c) an irreducible residual (closure fails)
  P(d) the residual must be ALLOCATED by a policy underdetermined by (a)-(c)
""")
    rows = [
        ("Pythagorean/syntonic comma", 1, 1, 1, 1, "MEMBER  (c) arithmetic"),
        ("maximal evenness / Euclidean rhythm", 1, 1, 1, 1, "MEMBER  (c) arithmetic"),
        ("calendar leap-year rules", 1, 1, 1, 1, "MEMBER  (c) contingent"),
        ("Antikythera gear-train ratios", 1, 1, 1, 1, "MEMBER  (c) contingent"),
        ("floating-point rounding modes", 1, 1, 1, 1, "MEMBER  (c) arithmetic"),
        ("string inharmonicity / Railsback", 1, 1, 1, 1, "MEMBER  (c) contingent"),
        ("coupled asymmetric pair (directed)", 1, 1, 1, 1, "MEMBER  (c) contingent -- MEASURED, K5"),
        ("nucleosome periodicity detuning", 1, 1, 1, "?", "PARTIAL (c) contingent, (d) weak-only"),
        ("nucleosome dyad parity (146 bp)", 1, 1, 1, 1, "MEMBER  (c) arithmetic, construct-only"),
        ("polyrhythm / tuplets", 1, 1, 0, 0, "EXCLUDED at (c) -- closes exactly"),
        ("UNCOUPLED two-oscillator beat / moire", 1, 1, 1, 0, "EXCLUDED at (d) -- nothing to allocate"),
        ("bell / drum inharmonic spectrum", 0, 1, 1, 0, "EXCLUDED at (a) -- no ratio-lattice ideal"),
        ("thermal equilibration", 0, 1, 1, 0, "EXCLUDED at (d) -- allocation is determined"),
        ("statistical variance across particle classes", 0, 0, 0, 0, "EXCLUDED -- not a residual at all"),
        ("MFO subharmonic comb (period-doubling)", 0, 1, 0, 0, "EXCLUDED at (a),(c) -- bifurcation"),
    ]
    print(f"  {'system':<44} {'a':>2} {'b':>2} {'c':>2} {'d':>2}  verdict")
    for name, a, b, c, d, v in rows:
        print(f"  {name:<44} {a:>2} {b:>2} {c:>2} {str(d):>2}  {v}")
        rec(
            kind="predicate_test",
            system=name,
            clause_a=a, clause_b=b, clause_c=c, clause_d=d,
            verdict=v,
            note="predicate P(a-d): ratio-generated lattice / closure requirement / irreducible "
                 "residual / policy-allocated residual",
            attested="structural classification; individual empirical inputs cited in the .md",
        )

    print("""
  THE PREDICATE IS DISCRIMINATING, NOT VACUOUS. It excludes 6 of 15 tested
  systems, and it excludes them at four DIFFERENT clauses -- which is the
  sign of a predicate doing real work rather than one clause carrying it.
  (Was 6 of 14; the beat row SPLIT in two under the measured K5 amendment --
  exclusions unchanged, members +1.)

  Clause (d) is load-bearing: it is what kills "any system with two
  periodicities" -- but the boundary sits ONE LEVEL IN. An UNCOUPLED pair has
  a residual and nothing to ALLOCATE; a COUPLED (directed) pair has a locked
  state whose allocation the closure does NOT fix -- measured, phi* identical
  to five decimals while the allocation runs 0.05 -> 0.95 (K5, attributed to
  open_experiments_kuramoto_hexasome_spike.md sec 2.4, NOT tested here).
  Coupling is what creates something to allocate.
  Clause (a) is second: it kills bells and drums, whose inharmonic spectra
  are NOT perturbations of any ratio-generated ideal.

  BUT the predicate does NOT single out music+DNA. Calendars, gear-trains and
  floating-point rounding are full members. The shape is a general
  commensuration-under-closure shape, NOT a signature of anything cosmic.
""")


# ================================================================ 9. verdict

def section_verdict() -> None:
    hr("9. VERDICT")
    print("""
  Q2 (the central test) -- ARITHMETIC vs CONTINGENT:
    Pythagorean comma        : ARITHMETIC. Theorem (sec 2 lemma).
    nucleosome ~10.2 vs 10.5 : CONTINGENT. Free real parameter, no obstruction.
    => The comma <-> nucleosome analogy FAILS. They differ IN KIND.

  BUT the dispatch pointed at the wrong member of music. Music contains a
  SECOND non-closure -- string inharmonicity -- which is contingent in
  exactly the nucleosome's way: an exact integer ideal (harmonic series /
  14-fold commensuration), a physical stiffness-like parameter detuning it
  (B / surface-vs-solution periodicity), and a deviation that is MEASURED
  AND DISTRIBUTED rather than removed (Railsback stretch / the wrap
  distribution). That match survives.

    comma            <-> nucleosome detuning : FAILS  (arithmetic vs contingent)
    inharmonicity    <-> nucleosome detuning : SURVIVES (both contingent)
    comma            <-> dyad parity         : SURVIVES (both arithmetic, but
                                               the DNA instance is a construct
                                               artifact, not the native state)
""")


def main() -> int:
    section_commas()
    section_closure_theorem()
    section_class_n()
    section_policies()
    section_inharmonicity()
    section_nucleosome()
    section_rhythm()
    section_predicate()
    section_verdict()

    out = "music_discrete_forms_commensuration_shape_spike.ndjson"
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        for r in RECORDS:
            fh.write(json.dumps(r, ensure_ascii=True) + "\n")
        for s in STATIC_RECORDS:
            fh.write(s.strip() + "\n")
    total = len(RECORDS) + len(STATIC_RECORDS)
    print(f"\n[wrote {len(RECORDS)} computed + {len(STATIC_RECORDS)} static "
          f"= {total} NDJSON records -> {out}]")
    return 0



# ---------------------------------------------------------------- static records
# Attestation / verdict / anomaly / fermata rows. Not computed — carried here so that
# re-running this script regenerates the COMPLETE ndjson instead of truncating it to
# the computed rows. Sources and verbatim quotes live in the .md attestation ledger.
STATIC_RECORDS = [
    r"""{"date": "2026-07-19", "phase": "music_commensuration_shape_spike", "kind": "amendment", "q": "Q1", "finding": "clause-(d) exclusion of two-oscillator beats was TOO BROAD - the row splits", "note": "First pass excluded 'generic two-oscillator beat / moire' wholesale at clause (d). Corrected on a MEASURED result, not a preference. UNCOUPLED pair: still EXCLUDED at (d) - a residual exists but there is nothing to allocate, the original reasoning stands. COUPLED ASYMMETRIC pair (directed / non-reciprocal): MEMBER, satisfying (d) in the STRONG sense. Coupling is what creates something to allocate: an uncoupled pair has two independent phases and no shared ledger; a coupled pair has one shared locked state whose allocation between the members is a free direction. Mechanism is DIRECTED coupling specifically - the source records the effect arriving via non-reciprocity, NOT via the Sakaguchi alpha frustration parameter.", "verdict": "ROW_SPLIT", "attributed_to": "open_experiments_kuramoto_hexasome_spike.md section 2.4 (K5) + its committed provenance script; run on srmech cascade.kuramoto_step. NOT tested in this spike.", "attested": "in-tree measured result, verified against that note's section 2.4 body and data table before citing"}""",
    r"""{"date": "2026-07-19", "phase": "music_commensuration_shape_spike", "kind": "measurement_cited", "q": "Q1", "finding": "K5 - the lock threshold is BLIND to the allocation", "note": "Directed coupling at alpha=0, holding the sum A12+A21 fixed at 2.0 and varying only the ratio: locked phase offset phi* = 0.25268 IDENTICAL TO FIVE DECIMALS across every row while the allocation runs 0.05 -> 0.95, tracking A12/(A12+A21) exactly. Closed form: threshold depends only on the SUM, split only on the RATIO. That is clause (d) verbatim - the residual is real, it closes a ledger, and how it splits between the two members is not determined by the closure.", "verdict": "CLAUSE_D_SATISFIED_STRONG", "attributed_to": "open_experiments_kuramoto_hexasome_spike.md section 2.4 (K5)", "attested": true}""",
    r"""{"date": "2026-07-19", "phase": "music_commensuration_shape_spike", "kind": "recount", "q": "Q1", "finding": "predicate count updated 14/6 -> 15/6", "note": "15 systems tested, 6 excluded, still at FOUR different clauses - (a), (c), (d), and all-clauses. The beat row split in two: exclusion count UNCHANGED, member count +1. HEADLINE VERDICT STANDS UNCHANGED - the predicate is discriminating but NOT special. Calendars, gear-trains and floating-point rounding remain full members; adding coupled asymmetric pairs makes the class LARGER, not more exclusive. This is generic commensuration-under-closure WITH A MECHANISM ATTACHED, not a signature.", "verdict": "DISCRIMINATING_BUT_NOT_SPECIAL", "attested": true}""",
    r"""{"date": "2026-07-19", "phase": "music_commensuration_shape_spike", "kind": "convergence", "q": "Q2", "finding": "the instrument's REACH LIMIT independently reproduces the arithmetic-vs-contingent split", "note": "Sinusoidal Kuramoto has exactly ONE resonance - 1:1 - with no higher-order p:q Arnold tongue at any coupling, because higher tongues need harmonics the model does not carry (open_experiments spike section 2.6 / N4). The nucleosome's commensuration IS 1:1 (one helical turn per contact, N/h0 = 14 turns over 14 contacts) so it sits INSIDE the model's reach; music's comma is 12:7 and sits OUTSIDE it. So a reach limit derived from the model's harmonic content lands on EXACTLY the same boundary as the section 2.1 unique-factorisation argument. TWO INDEPENDENT ROUTES TO ONE SPLIT. Stated with its limit: this is a CONVERGENCE, not a proof - a sinusoidal model's reach is a fact about the model and the p:q structure of the comma is a fact about the integers; that they partition the same way is corroboration that the partition is real, not a second derivation of it.", "verdict": "CONVERGENCE", "attributed_to": "open_experiments_kuramoto_hexasome_spike.md section 2.6 / N4", "attested": true}""",
    r"""{"date": "2026-07-19", "phase": "music_commensuration_shape_spike", "kind": "guard_rail", "q": "scope", "finding": "the amendment does NOT touch the headline or the central verdict", "note": "Explicitly preserved under the amendment: (1) the predicate is DISCRIMINATING BUT NOT SPECIAL - adding coupled asymmetric pairs enlarges the member class rather than narrowing it; (2) the comma <-> nucleosome verdict is UNTOUCHED - still decorative, still differ-in-kind; (3) the string-inharmonicity <-> nucleosome match remains THE surviving one. No inflation.", "verdict": "UNCHANGED", "attested": true}""",
    r"""{"date": "2026-07-19", "phase": "music_commensuration_shape_spike", "kind": "source_note", "q": "method", "finding": "the cited source's own summary row reads ambiguously out of context - body used instead", "note": "open_experiments_kuramoto_hexasome_spike.md line 43 states K5's HYPOTHESIS in the negative ('the allocation is fixed by the closure condition => Kuramoto is the generic beat the music spike already excluded at clause (d)') with verdict 'survives, but NOT via alpha', which out of context could be read as confirming the EXCLUSION. Its section 2.4 body plus data table is unambiguous the other way: phi* constant across allocation, 'That is clause (d) verbatim', 'K5 survives -- via directed coupling, not via alpha'. Cited the BODY, not the summary row. Minor wording ambiguity in the source, flagged not corrected - that note's authors own it.", "verdict": "RESOLVED_BY_READING_BODY", "attested": true}""",
    r"""{"date": "2026-07-19", "phase": "music_commensuration_shape_spike", "kind": "attestation", "q": "A", "finding": "stiff-string inharmonicity law ATTESTED", "note": "Gracia & Sanz-Perela, 'The wave equation for stiff strings and piano tuning', arXiv:1603.05516v2 (UPC; Reports@SCM 3, 2017). Verbatim: 'the frequency spectrum is no longer harmonic, but of the form fn = n f sqrt(1 + Bn^2) (n>=1), where B is a constant depending on the physical parameters of the string'; 'For piano strings the value of the inharmonicity parameter B is about 10-3'; 'this explains why the tuning of the piano is actually stretched, with octaves slightly larger than should'. Corroborated Roy, Edinburgh Student J Sci, DOI 10.2218/esjs.9815 (OA 2024).", "verdict": "ATTESTED", "attested": true}""",
    r"""{"date": "2026-07-19", "phase": "music_commensuration_shape_spike", "kind": "attestation", "q": "B", "finding": "Railsback curve PARTIALLY attested - curve yes, magnitude NO", "note": "Hinrichsen, 'Entropy-based Tuning of Musical Instruments', arXiv:1203.5101v1. Verbatim: 'first explained by O. L. Railsback in 1938, who showed that this perception is caused by inharmonic corrections in the overtone spectrum. Professional aural tuners compensate this inharmonicity by small deviations, a technique known as stretching.' ATTESTED: name, 1938, the practice, and the CAUSAL link to inharmonicity. NOT attested: the magnitude in cents.", "verdict": "ATTESTED_PARTIAL", "attested": true}""",
    r"""{"date": "2026-07-19", "phase": "music_commensuration_shape_spike", "kind": "attestation", "q": "C", "finding": "temperament as residual-distribution practice ATTESTED", "note": "Scholtz, 'Algorithms for Mapping Diatonic Keyboard Tunings and Temperaments', Music Theory Online 4.4 (1998), peer-reviewed OA musicology. Verbatim: 'Equal temperament flattens the fifths (and sharpens the fourths) by 1/12 of a Pythagorean comma'; 'equally dividing the syntonic comma over the four links of each major third'; 'The more that the commas were divided and dispersed, the more that well temperament approached equal temperament.' CAVEAT: says CONSONANT major thirds, not PURE; and 'key colour' does NOT appear anywhere.", "verdict": "ATTESTED", "attested": true}""",
    r"""{"date": "2026-07-19", "phase": "music_commensuration_shape_spike", "kind": "attestation", "q": "D", "finding": "maximal evenness / Euclidean rhythm ATTESTED incl. the 7-of-12 diatonic identity", "note": "Toussaint, 'The Euclidean Algorithm Generates Traditional Musical Rhythms', BRIDGES 2005 extended version, McGill-hosted author copy. Verbatim: 'If k divides evenly (without remainder) into n, then the solution is obvious... The solution is less obvious when k and n are relatively prime numbers'; 'it is the same pattern as the pitch pattern of the major diatonic scale'; Bjorklund's algorithm 'has the same structure as the Euclidean algorithm'. CAVEAT: Clough & Douthett 1991 is reference-only INSIDE Toussaint (JMT paywalled) - do NOT quote their words.", "verdict": "ATTESTED", "attested": true}""",
    r"""{"date": "2026-07-19", "phase": "music_commensuration_shape_spike", "kind": "attestation", "q": "E", "finding": "non-closure of fifths ATTESTED - but as a PARITY argument, not UFD", "note": "Scholtz, MTO 4.4 (1998) endnote 8. Verbatim: '(3/2)^(n), which can never be an exact multiple of 2 since every power of 3 is an odd number'. This is a PARITY argument covering the fifth only; Scholtz falls back on an 'intuitive musical proof' for fourths. The UFD/coprimality framing and the generalisation to arbitrary p/q with two corollaries are OURS - flagged so the lemma is not mistaken for a cited result. No number-theory-grade OA source located.", "verdict": "ATTESTED_FACT_OUR_FRAMING", "attested": true}""",
    r"""{"date": "2026-07-19", "phase": "music_commensuration_shape_spike", "kind": "anomaly", "q": "method", "finding": "A3 - the Railsback stretch MAGNITUDE has no attestable source", "note": "The most-quoted number in this area ('~30 cents at the extremes') traces to a Wikipedia image file. Hinrichsen's own Fig.1 credit line is literally 'Figure taken from: http://en.wikipedia.org/wiki/File:Railsback2.png'. JASA 1938 primary is paywalled; the 2015 JASA explanatory paper returned HTTP 403.", "investigation": "direct fetch of every candidate source; no OA document states the magnitude", "verdict": "CONFIRMED - apparently well-sourced quantity with no attestable origin. SECOND independent instance of the prior spike's A3 vector, in an unrelated literature.", "next": "the Railsback CURVE may be cited; its MAGNITUDE may not. Methodology exhibit candidate."}""",
    r"""{"date": "2026-07-19", "phase": "music_commensuration_shape_spike", "kind": "anomaly", "q": "method", "finding": "A4 - three 'standard' domain phrases failed attestation", "note": "'key colour', 'pure thirds in meantone', 'treble sharp / bass flat' all read as textbook; none is in any fetched OA source, and 'pure' is actively contradicted by Scholtz ('consonant'). All three were in this note's FIRST DRAFT and were removed before ship.", "investigation": "grep of the full fetched texts for each phrase", "verdict": "REAL - failure mode is FLUENT-DOMAIN-VOCABULARY, distinct from citation hallucination: plausible register rather than invented fact, therefore harder to catch", "next": "logged as a pattern; no action required"}""",
    r"""{"date": "2026-07-19", "phase": "music_commensuration_shape_spike", "kind": "anomaly", "q": "A", "finding": "attested-source CONFLICT on the treble inharmonicity coefficient", "note": "Gracia gives typical piano B ~ 10^-3 and computes with B in [0.0004, 0.002]. Hinrichsen states B ranges 'between 0.0002 for bass strings up to 0.4 for treble strings' - but his own figure axis tops out at 10^-1, BELOW his quoted 0.4. Two OA sources disagree by orders of magnitude at the treble end.", "investigation": "both texts extracted and compared against their own figures", "verdict": "UNRESOLVED - treat 0.4 as suspect; do not cite it. Script brackets B in {1e-4, 5e-4, 1e-3}, consistent with Gracia.", "next": "a measurement paper with a numeric table would settle it; Roy's values are locked in a figure"}""",
    r"""{"date": "2026-07-19", "phase": "music_commensuration_shape_spike", "kind": "verdict", "q": "Q2", "finding": "CENTRAL TEST - arithmetic vs contingent: the two non-closures DIFFER IN KIND", "note": "Pythagorean comma: ARITHMETIC. Lemma - r=p/q lowest terms, r^n=2^m forces q=1 and p a power of 2; so 3/2 never closes the octave for ANY n, and every equal division of the octave is irrational. Nucleosome: CONTINGENT. N/h=k solves as h=N/k for any integers N,k because h is a free real parameter; nothing forbids h_s=10.5, the measured value simply is not 10.5. The comma <-> nucleosome analogy is DECORATIVE.", "verdict": "DIFFER_IN_KIND", "attested": "lemma exact; fact attested Scholtz MTO 4.4 endnote 8; nucleosome inputs PMC6162219"}""",
    r"""{"date": "2026-07-19", "phase": "music_commensuration_shape_spike", "kind": "verdict", "q": "Q2b", "finding": "the dispatch pointed at the WRONG MEMBER of music - a different match survives", "note": "Music has TWO structurally different non-closures. (1) comma = arithmetic. (2) string inharmonicity = contingent, parameterised by stiffness B, removed entirely at B=0. The nucleosome detuning is of the SECOND kind: an exact integer ideal (147/10.5 = 14 exactly), a physical parameter detuning it (10.2 vs 10.5), and a deviation MEASURED AND DISTRIBUTED rather than removed (Railsback stretch <-> the wrap distribution). comma<->nucleosome FAILS; inharmonicity<->nucleosome SURVIVES.", "verdict": "SURVIVES", "attested": "inharmonicity law attested arXiv:1603.05516; Railsback practice attested arXiv:1203.5101"}""",
    r"""{"date": "2026-07-19", "phase": "music_commensuration_shape_spike", "kind": "verdict", "q": "Q1", "finding": "the predicate is DISCRIMINATING, not vacuous - but it does NOT single out music+DNA", "note": "14 systems tested, 6 excluded, at FOUR DIFFERENT clauses - the sign of a predicate doing real work rather than one clause carrying it. Clause (d) (residual ALLOCATED by an underdetermined policy) is load-bearing: it kills 'any system with two periodicities', since a generic beat has a residual but nothing to allocate. Clause (a) kills bells/drums (no ratio-lattice ideal). BUT calendars, gear-trains and floating-point rounding are FULL MEMBERS - the shape is generic commensuration-under-closure, NOT a signature of anything cosmic. Clause (d) was sharpened from 'an agent chooses' (anthropocentric, excludes DNA by definition) to ALLOCATION-UNDERDETERMINATION.", "verdict": "DISCRIMINATING_BUT_NOT_SPECIAL", "attested": "structural classification"}""",
    r"""{"date": "2026-07-19", "phase": "music_commensuration_shape_spike", "kind": "finding", "q": "Q1", "finding": "EQUIVOCATION CAUGHT on the word 'distribution'", "note": "The nucleosome spike's 'the honest object is a DISTRIBUTION, not a constant' uses distribution in the STATISTICAL sense (variance across particle classes). Predicate clause (d) uses it in the ALLOCATION sense (spreading one residual over several slots). Different objects; the word bridges them illegitimately. Statistical variance is excluded by the predicate at EVERY clause. The two senses must not be traded on.", "verdict": "HAZARD_CLEARED", "attested": true}""",
    r"""{"date": "2026-07-19", "phase": "music_commensuration_shape_spike", "kind": "verdict", "q": "Q4", "finding": "the MFO tie does NOT triangulate - it is two-way plus a homonym", "note": "MFO's actual claim (notebook head + XIV.8): matter/force are 'inharmonic and subharmonic excitations of a single metric field. An asymmetric resonator', exemplar a CYMBAL/BELL. Three findings against the bridge. (1) MFO ALREADY decoupled the words itself - XIV.8's honest correction: 'the comb comes from nonlinearity, not from spatial asymmetry'. (2) MFO's MEASURED signature is a period-doubling bifurcation cascade with Feigenbaum delta ~4.669 - NOT a commensuration residual; fails clauses (a) and (c). (3) MFO's exemplar is PRECISELY what the predicate excludes: a bell is inharmonic in the NO-NEARBY-INTEGER-IDEAL sense, while a piano string and the nucleosome are detuned in the SMALL-PERTURBATION-OFF-AN-EXACT-INTEGER-IDEAL sense - opposite ends of one word. In-tree corroboration: Spike #40 measured bell as geometric-decay and drum as Bessel-zero frequencies, neither a perturbation of N*f0. This does NOT refute MFO; it says the proposed bridge does not go through by this route.", "verdict": "NULL_AS_TRIANGULATION", "attested": "MFO in-tree; bell/drum spectra in-tree Spike #40"}""",
    r"""{"date": "2026-07-19", "phase": "music_commensuration_shape_spike", "kind": "fermata_answer", "q": "F-g", "finding": "ADJUDICATES the open fermata F-g", "note": "F-g logged the user framing (DNA as physical instantiation of MFO's asymmetric universal resonator) MFO-side, recorded but NOT adjudicated, with two guard-rails: must not retro-justify S1/S2, does not soften anomaly A1. This spike adjudicates: the reading does NOT go through by commensuration. Both guard-rails observed - nothing here retro-justifies S1/S2, and A1 is untouched and if anything reinforced, since the detuning is shown to be a free parameter.", "verdict": "ADJUDICATED_NEGATIVE", "attested": true}""",
    r"""{"date": "2026-07-19", "phase": "music_commensuration_shape_spike", "kind": "verdict", "q": "Q3", "finding": "srmech should NOT grow a tuning/temperament op-family", "note": "The JI half is REDUNDANT: best_rational + continued_fraction ARE the just-intonation problem. Demonstrated - best_rational(log2(3/2), max_d=12) = 7/12 (12-EDO), max_d=60 -> 31/53 (53-EDO), max_d=400 -> 179/306. Choosing a temperament IS choosing max_denominator; that is Class N verbatim. The temperament half is genuinely ABSENT but is NOT music: tempering out a comma = quotienting the prime-exponent lattice Z^k by the sublattice generated by the comma vectors, then choosing a section - integer linear algebra (Smith normal form / kernel), adjacent to Class L. If it ships it should ship as the GENERAL lattice-quotient + residual-allocation op with music as ONE worked instance; shipping it as 'tuning' would privilege a substrate against feedback_no_privileged_primitive_classes.", "verdict": "DO_NOT_SHIP_AS_MUSIC", "attested": "computed with shipped srmech ops"}""",
    r"""{"date": "2026-07-19", "phase": "music_commensuration_shape_spike", "kind": "finding", "q": "Q3", "finding": "just intonation and equal temperament are DUAL, not competing approximations", "note": "By the closure lemma you may have rational intervals OR octave closure, never both (outside powers of 2). JI keeps ratios rational and accepts non-closure; ET accepts irrational ratios and achieves exact closure. Temperament is therefore NOT 'a better best_rational' - it is the deliberate move OFF the rational lattice that best_rational exists to stay ON. Same object, opposite direction. Theorem, not a reading.", "verdict": "SURVIVES", "attested": "arithmetic_theorem"}""",
    r"""{"date": "2026-07-19", "phase": "music_commensuration_shape_spike", "kind": "anomaly", "q": "Q2b", "finding": "A1 - the surviving match is with the member music theory treats as an ERROR", "note": "Temperament (the comma side) is the celebrated, theorised, notated part of music's commensuration problem. Inharmonicity is treated as a DEFECT of real strings. Yet it is inharmonicity, not temperament, that shares the nucleosome's shape.", "investigation": "the closure lemma vs the free-parameter argument, both exact", "verdict": "REAL - and it INVERTS the dispatch's expected mapping", "next": "if the framework wants a DNA<->music reading it must be built on the Railsback/inharmonicity member and explicitly NOT on the comma - the opposite of the intuitive route"}""",
    r"""{"date": "2026-07-19", "phase": "music_commensuration_shape_spike", "kind": "anomaly", "q": "Q2c", "finding": "A2 - the nucleosome's arithmetic non-closure survives only in an ARTIFICIAL construct", "note": "The one genuinely arithmetic obstruction on the DNA side is Z/2 dyad parity (a 2-fold axis through a base pair requires ODD bp) - canonically Class K. It manifests as a distributed residual ONLY in Luger's 146 bp even palindrome, a crystallographer's construct, where the deficit was absorbed by stretching. The native 147 bp particle satisfies parity exactly and has NO residual to distribute.", "investigation": "parity arithmetic plus the attested 146/147 resolution (PMC4378457)", "verdict": "REAL - the type-1 match is with an experimental artifact, not with biology", "next": "conductor decision on whether an artifact-only match may be cited at all"}""",
    r"""{"date": "2026-07-19", "phase": "music_commensuration_shape_spike", "kind": "fermata", "q": "conductor", "finding": "five open decisions", "note": "F-i: ship a GENERAL lattice-quotient + residual-allocation op (integer Smith normal form over a prime-exponent lattice) with tuning as one worked instance, or park? Also document the best_rational uint64 bound? F-ii: notebook placement - section 5 is MFO-side ontology, sections 2-4 srmech-side math; split per the notebook split rule, or hold pending the still-open F-d? F-iii: may an artifact-only (146 bp construct) match be cited in framework prose, or record 'arithmetic non-closure on the DNA side' as NATIVE-ABSENT? F-iv: A1 says the DNA<->music reading must be built on inharmonicity and NOT the comma - worth a follow-up spike on the Railsback member specifically? F-v: the nucleosome spike's F-c (Kuramoto/Arnold-tongue, untested) is now MORE motivated, since two-periodicity detuning is shown to be the contingent-class mechanism shared by strings and nucleosomes.", "verdict": "OPEN", "attested": false}""",
]

if __name__ == "__main__":
    sys.exit(main())

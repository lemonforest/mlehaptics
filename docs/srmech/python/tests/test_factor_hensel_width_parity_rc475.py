"""rc475 (`#T1188`) — the Zassenhaus core must TERMINATE, SERVE, and agree with
the pure oracle on the inputs that overran its bignum pool buffers.

THE DEFECT THIS GUARDS. ``bp_buf`` spaced the 30 bignum poly buffers
``cw = deg+1`` apart, while a quadratic Hensel step against ``F`` (degree ``n``)
with ``g``/``h`` of degrees ``a``/``b`` forms products of length up to
``n + max(a,b) - 1`` — longer than ``deg+1`` whenever a non-last mod-p split has
``max(a,b) >= 3`` — and none of the four ``bp_*`` kernels checked its output
against a width. The product ran into the NEXT pool buffer, which is live Hensel
state.

THE THREE SYMPTOMS, MEASURED over 84 polynomials at rc474: **34 did not return,
6 returned a WRONG VALUE, 3 DECLINED, 41 agreed.**

⚠️ WHY THIS FILE ASSERTS *SERVED* AND *SHAPE*, NOT ONLY EQUALITY. Two instrument
defects were measured while this gate was being designed, and each one would
have made a green run meaningless:

1. **A DECLINE HIDES BEHIND A DIGEST MATCH.** ``factor_integer_poly_c`` and
   ``factor_squarefree_primitive_c`` returned ``None`` for every non-OK status,
   and ``factor_integer_poly`` then answered from the pure body. So a test that
   compares "the answer" to "the pure answer" compares pure to pure and passes
   on a corrupted library. That is not hypothetical: it happened on 3 of 84 rows
   at rc474 and nobody had recorded the class. Every row below therefore asserts
   the DIRECT wrapper result ``is not None`` before comparing anything.
2. **THE RETURN SHAPE.** ``factor_integer_poly`` returns a LIST of
   ``((coeffs...), multiplicity)`` pairs, not a ``(factors, hit_cap)`` 2-tuple.
   A lane that unpacked it as a pair raised on every row with != 2 factors and
   "succeeded" only on the 2-factor subset — 31 of 48 rows reported as errors,
   in all three lanes, which is what exposed it. So the shape is asserted
   explicitly rather than assumed by destructuring.

⚠️ THE NATIVE CALLS RUN OUT OF PROCESS. A non-returning ctypes call cannot be
interrupted from Python, so an in-process loop over this corpus would hang the
whole pytest session on the very defect the file exists to detect, and report it
as a CI timeout rather than as a failure. Each batch runs in a subprocess under a
wall-clock guard.

⚠️ THE CORE'S FACTOR ORDER IS COMPARED AS A MULTISET, DELIBERATELY. rc475's other
half replaces the Cantor–Zassenhaus equal-degree split with deterministic
Berlekamp, whose canonical ``(len, coeffs)`` mod-p order is a DIFFERENT order —
measured: ``srmech_factor_squarefree_primitive``'s list is reordered on 14 of 46
served rows and is an identical multiset on 46/46. That is forced (any
deterministic replacement moves it), so pinning it here would pin a value this
rc deliberately changed. The COMPOSITE is compared WITH order, because it sorts
and was measured identical 48/48 with order.

WHAT THIS DOES NOT PROVE. That the C is right where pure is wrong: pure is the
oracle here. Its own correctness is checked two ways rather than assumed — the
reconstruction identity (:func:`test_the_pure_oracle_reconstructs_every_input`)
and an independent per-factor irreducibility CERTIFICATE
(:mod:`_irreducibility_cert`, exercised by
:func:`test_every_served_factor_is_certified_irreducible`). Numpy-free.
"""
from __future__ import annotations

import json
import random
import subprocess
import sys
import textwrap

import pytest

from srmech import _native
from srmech.cascade.matrix_cascades import (
    _ipoly_content, _ipoly_mul, _ipoly_primitive, _ipoly_trim, char_poly,
    factor_integer_poly,
)

from tests._irreducibility_cert import certify

#: The fixed build answers the whole corpus in well under a second; rc474 never
#: returned on 34 of 84 rows. 120 s is ~100x the measured need and still a bound.
GUARD_S = 120

pytestmark = pytest.mark.skipif(
    not _native.has_native_factor_integer_poly(),
    reason="needs the native factor_integer_poly composite",
)


def _force_pure(fn, *a):
    saved = _native.HAS_NATIVE
    _native.HAS_NATIVE = False
    try:
        return fn(*a)
    finally:
        _native.HAS_NATIVE = saved


def _poly_mul(a, b):
    out = [0] * (len(a) + len(b) - 1)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            out[i + j] += x * y
    return out


#: The five rc474 witnesses, by symptom. Rows 0/3/4 DID NOT RETURN; row 1
#: returned a WRONG VALUE (and its product still equalled the input, so the
#: composite's own multiply-back self-check passed — a reducible degree-9 factor
#: served as irreducible); row 2 DECLINED with a non-OK status and was answered
#: from the pure oracle with nobody seeing.
WITNESSES = [
    [-8464, 0, 2516, 0, -152, 0, 1],
    [14, 50, 61, -149, -259, 47, 209, 106, -76, -4, 1],
    [49, 0, -84, 0, -314, 0, -164, 0, 33, 0, -1],
    [169, 0, -315, 0, 299, 0, -432, 0, 163, 0, -102, 0, 1],
    [-3, 0, -10, 0, -25, 0, -24, 0, 12, 0, 1, 0, 1],
]


def _corpus():
    """The parity corpus, generated deterministically from one seed.

    Generated rather than shipped as a data file so the generator IS the
    provenance (`[[feedback_computational_provenance_discipline]]`): anyone can
    re-derive the exact rows from this function. Five families, and the third is
    the one that matters — the first diagnosis of this defect tied the failures
    to EVEN structure (``g(x)g(-x)``, ``m(x^2)``) and measured 0 failures on
    "products of degree 1-4 factors", which is why the trigger was restated: it
    is the mod-p factor-DEGREE profile, and a generic non-even product hits it
    (4 hangs + 1 wrong value out of 16 on the restating sample).

    Every row is kept at degree <= 32 on purpose: that is
    ``_FACTOR_FULL_NATIVE_MAX_DEG``, so the composite SERVES every row and a
    decline cannot be excused as "above the cap".
    """
    rows = list(WITNESSES)
    rng = random.Random(475118820)
    for dg in (3, 4, 5, 6):                      # g(x)*g(-x)
        for _ in range(10):
            g = [rng.randint(-9, 9) for _ in range(dg)] + [1]
            gm = [c if i % 2 == 0 else -c for i, c in enumerate(g)]
            rows.append(_poly_mul(g, gm))
    for dm in (3, 4, 5):                         # m(x^2)
        for _ in range(8):
            m = [rng.randint(-8, 8) for _ in range(dm)] + [1]
            sq = []
            for c in m:
                sq += [c, 0]
            rows.append(sq[:-1])
    for da in (3, 4, 5):                         # generic g*h, NOT even
        for db in (3, 4, 5):
            for _ in range(6):
                a = [rng.randint(-7, 7) for _ in range(da)] + [1]
                b = [rng.randint(-7, 7) for _ in range(db)] + [1]
                rows.append(_poly_mul(a, b))
    for n in (12, 15, 16, 18, 21, 24, 30, 32):   # x^n - 1: abelian Galois
        rows.append([-1] + [0] * (n - 1) + [1])
    # char polys of small integer matrices and of their Gram matrices — the
    # route eig_exact / singular_values_exact actually take into the core.
    for shape in ((2, 2), (3, 3), (4, 4), (5, 5), (4, 3), (5, 3)):
        for _ in range(8):
            A = [[rng.randint(-6, 6) for _ in range(shape[1])]
                 for _ in range(shape[0])]
            m, n = len(A), len(A[0])
            G = [[sum(A[r][i] * A[r][j] for r in range(m)) for j in range(n)]
                 for i in range(n)]
            rows.append([int(x) for x in reversed(char_poly(G))])
            if m == n:
                rows.append([int(x) for x in reversed(char_poly(A))])
    out, seen = [], set()
    for r in rows:
        r = _ipoly_trim(list(r))
        if len(r) < 2 or len(r) - 1 > 32:
            continue
        key = tuple(r)
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out


CORPUS = _corpus()


def test_the_corpus_is_not_vacuous():
    """A corpus that shrank to nothing makes every row-wise test below pass.

    Also pins that the WITNESSES are members, because a generator change that
    silently dropped them would leave a large green corpus with the one defect
    it was built for absent from it.
    """
    assert len(CORPUS) > 200, f"corpus is {len(CORPUS)} rows; > 200 expected"
    for w in WITNESSES:
        assert _ipoly_trim(list(w)) in CORPUS, f"witness {w} left the corpus"
    assert max(len(r) - 1 for r in CORPUS) <= 32, (
        "a row exceeds _FACTOR_FULL_NATIVE_MAX_DEG, so a composite decline on "
        "it would be legitimate and the served-count assertion would be wrong"
    )


def _native_batch(rows):
    """``[{comp, core}]`` from a SUBPROCESS, one entry per row.

    Out of process because a non-returning ctypes call cannot be interrupted
    in-process: an in-process loop would hang pytest on precisely the defect
    being measured. ``RuntimeError`` is caught per row and returned as a marker
    rather than killing the batch, because rc475 makes
    ``SRMECH_ERR_INTERNAL`` RAISE — and an INTERNAL is a finding this gate must
    report by row, not an infrastructure failure.
    """
    code = textwrap.dedent("""
        import json, sys
        from srmech import _native as N
        rows = json.loads(sys.stdin.read())
        out = []
        for r in rows:
            rec = {}
            try:
                rec["comp"] = N.factor_integer_poly_c(r)
            except RuntimeError as exc:
                rec["comp"] = None
                rec["comp_raised"] = str(exc)[:200]
            try:
                rec["core"] = N.factor_squarefree_primitive_c(r)
            except RuntimeError as exc:
                rec["core"] = None
                rec["core_raised"] = str(exc)[:200]
            out.append(rec)
        print(json.dumps(out))
    """)
    proc = subprocess.run(
        [sys.executable, "-c", code], input=json.dumps(rows),
        capture_output=True, text=True, timeout=GUARD_S,
    )
    assert proc.returncode == 0, (
        f"the native batch subprocess exited {proc.returncode}: "
        f"{proc.stderr[-800:]}"
    )
    return json.loads(proc.stdout)


NATIVE = None


def _native_once():
    global NATIVE
    if NATIVE is None:
        NATIVE = _native_batch(CORPUS)
    return NATIVE


def test_no_row_fails_to_return():
    """The 34/84 symptom. If any row hangs, the subprocess guard fires and
    :func:`_native_batch`'s own assertion reports it, so this test is the one
    that names the guard rather than letting a CI timeout stand in for it."""
    got = _native_once()
    assert len(got) == len(CORPUS), (
        f"{len(got)} results for {len(CORPUS)} rows — the batch did not "
        f"complete, which through rc474 is exactly what a hang looked like"
    )


def test_every_row_is_SERVED_by_the_composite():
    """The 3/84 DECLINE symptom — the class nobody had recorded.

    ``is not None`` is the whole point: a decline is answered by the pure oracle
    and is INVISIBLE to a value comparison.
    """
    got = _native_once()
    declined = [(i, CORPUS[i], g.get("comp_raised"))
                for i, g in enumerate(got) if g["comp"] is None]
    assert not declined, (
        f"{len(declined)} of {len(CORPUS)} rows DECLINED (or raised) in the "
        f"native composite. A decline is answered from the pure oracle with no "
        f"other signal, which is how the rc474 corruption stayed invisible. "
        f"First three: {declined[:3]}"
    )


def test_every_row_is_SERVED_by_the_core():
    """Same claim on ``srmech_factor_squarefree_primitive``.

    Rows that are not square-free are EXCLUDED by name rather than tolerated:
    the core documents a square-free primitive precondition, so a decline there
    is the contract and not a finding — but it has to be identified as such, or
    "declined because not square-free" and "declined because corrupted" read
    the same.
    """
    got = _native_once()
    declined = []
    for i, g in enumerate(got):
        if g["core"] is not None:
            continue
        mults = [m for _f, m in _force_pure(factor_integer_poly, CORPUS[i])]
        if max(mults) > 1:
            continue                      # not square-free: the documented precondition
        declined.append((i, CORPUS[i], g.get("core_raised")))
    assert not declined, (
        f"{len(declined)} SQUARE-FREE rows declined in the native core: "
        f"{declined[:3]}"
    )


def test_the_composite_shape_and_value_match_the_pure_oracle():
    """Shape FIRST, then value, WITH order.

    The shape assertion is here because a lane that destructured the result as a
    ``(factors, hit_cap)`` pair raised on 31 of 48 rows and read as a partial
    pass. The order assertion is safe on the composite and only on the
    composite: it sorts by ``(len, coeffs)``.
    """
    got = _native_once()
    bad_shape, mismatch = [], []
    for i, g in enumerate(got):
        comp = g["comp"]
        if not isinstance(comp, list):
            bad_shape.append((i, type(comp).__name__))
            continue
        for entry in comp:
            if not (isinstance(entry, list) and len(entry) == 2
                    and isinstance(entry[0], list) and isinstance(entry[1], int)):
                bad_shape.append((i, entry))
                break
        pure = _force_pure(factor_integer_poly, CORPUS[i])
        if [(tuple(f), m) for f, m in comp] != pure:
            mismatch.append((i, CORPUS[i], comp, pure))
    assert not bad_shape, (
        f"the composite returned an unexpected SHAPE on {len(bad_shape)} rows; "
        f"it must be a list of (coeffs, multiplicity) pairs: {bad_shape[:3]}"
    )
    assert not mismatch, (
        f"{len(mismatch)} of {len(CORPUS)} composite rows disagree with the "
        f"pure oracle (order included): {mismatch[:2]}"
    )


def test_the_core_matches_the_pure_oracle_as_a_MULTISET():
    """The core's peel ORDER moved at rc475 and its CONTENT did not.

    Compared as a multiset for the reason in the module docstring. ``hit_cap``
    is compared too — it is a function of the same mod-p order, so a change
    there would be a served-value change hiding behind an order-blind compare.
    """
    got = _native_once()
    mismatch, cap = [], []
    for i, g in enumerate(got):
        core = g["core"]
        if core is None:
            continue
        assert isinstance(core, list) and len(core) == 2, (
            f"row {i}: the CORE returns a (factors, hit_cap) 2-tuple; got {core!r}"
        )
        facs, hit = core
        pure = _force_pure(factor_integer_poly, CORPUS[i])
        if max(m for _f, m in pure) > 1:
            continue                      # not square-free: core precondition
        want = sorted(tuple(f) for f, _m in pure)
        if sorted(tuple(f) for f in facs) != want:
            mismatch.append((i, CORPUS[i], facs, want))
        if hit:
            cap.append((i, CORPUS[i]))
    assert not mismatch, (
        f"{len(mismatch)} core rows disagree with the pure oracle even as a "
        f"MULTISET, which is a value change and not an order change: "
        f"{mismatch[:2]}"
    )
    assert not cap, f"unexpected recombination-cap hits: {cap[:3]}"


def test_the_pure_oracle_reconstructs_every_input():
    """The oracle is checked, not assumed: ``primitive(prod factor^mult)`` must
    equal ``+/- primitive(input)``.

    Run through srmech's own ``_ipoly_mul`` / ``_ipoly_primitive`` /
    ``_ipoly_trim`` rather than a hand-rolled content division — a private
    reimplementation of the content is a second thing that can be wrong, and it
    would be wrong in the same direction as the code it is checking.
    """
    bad = []
    for r in CORPUS:
        prod = [1]
        for f, m in _force_pure(factor_integer_poly, r):
            for _ in range(m):
                prod = _ipoly_mul(prod, list(f))
        _c_in, prim_in = _ipoly_primitive(_ipoly_trim(list(r)))
        _c_pr, prim_pr = _ipoly_primitive(_ipoly_trim(prod))
        if prim_pr != prim_in and prim_pr != [-c for c in prim_in]:
            bad.append((r, prim_in, prim_pr))
    assert not bad, f"the pure oracle does not reconstruct {len(bad)} inputs: {bad[:2]}"
    assert _ipoly_content([6, 9, 12]) == 3, (
        "control: _ipoly_content must actually compute a content, or the "
        "reconstruction check above is comparing two identically-wrong things"
    )


def test_every_served_factor_is_certified_irreducible():
    """⚠️ THE ORACLE'S IRREDUCIBILITY IS CERTIFIED, NOT ASSERTED BY AGREEMENT.

    This test replaces the claim "irreducibility of factors of degree >= 4 rests
    on agreement between two implementations". Agreement between two
    implementations of the SAME algorithm is a consistency check, not a proof of
    irreducibility, and it is exactly the kind of claim that reads as evidence
    while resting on none.

    :mod:`_irreducibility_cert` searches, per factor, a certificate that can be
    verified in exact integers by code that shares nothing with the factorizer:
    degree 1; a non-square discriminant at degree 2; a complete elementary
    criterion for a monic even quartic; the cyclotomic identity; a prime at
    which the factor is irreducible mod p; or a set of primes whose mod-p degree
    patterns admit no common proper factor degree. Two of those tiers (A2, E)
    are COMPLETE criteria, so a served REDUCIBLE quadratic or even quartic is
    detected outright rather than merely left uncertified.

    A factor the checker cannot certify does not pass silently — it is listed by
    name and counted, and the count is pinned at zero. If a future corpus row
    introduces a genuinely hard Galois group (a degree-8 factor with
    ``Gal = C_2^3`` has no certifying prime and survives the degree sieve), the
    honest move is to raise that pin WITH the factor named, not to delete the
    test.
    """
    tally, residual, reducible = {}, [], []
    for i, r in enumerate(CORPUS):
        for f, _m in _force_pure(factor_integer_poly, r):
            g = list(f)
            if len(g) - 1 < 1:
                continue
            cert = certify(g)
            tally[cert["tier"]] = tally.get(cert["tier"], 0) + 1
            if cert["tier"] == "RESIDUAL":
                residual.append((i, g, cert.get("surviving_degrees")))
            if cert.get("reducible"):
                reducible.append((i, g, cert["cert"]))
    total = sum(tally.values())
    assert total > 300, (
        f"only {total} factors certified; the corpus yields ~350, so the "
        f"checker or the corpus collapsed"
    )
    assert not reducible, (
        f"a REDUCIBLE factor was served as irreducible — tiers A2 and E are "
        f"COMPLETE criteria, so this is a correctness finding and not an "
        f"uncertified one: {reducible[:3]}"
    )
    assert not residual, (
        f"{len(residual)} of {total} factors could not be certified by the "
        f"independent checker, so for those the gate can claim only "
        f"two-implementation agreement. They are named here rather than passing "
        f"quietly: {residual[:5]}. Tally: {tally}"
    )
    # The tally is printed into the failure message of the vacuity check above
    # rather than pinned per tier: which tier certifies a given factor depends
    # on the prime search, and pinning that would make the gate brittle about
    # something it does not claim.
    assert tally.get("A", 0) + tally.get("A2", 0) < total, (
        "every factor certified by degree alone means no factor of degree >= 3 "
        "reached the real checker, which is the claim this test exists to make"
    )


def test_the_certificate_checker_can_fail():
    """The instrument's own controls — an instrument that cannot return
    otherwise is not a measurement.

    Four cases, each with a KNOWN answer: a reducible even quartic must be
    caught by a COMPLETE criterion, an irreducible quintic must certify by a
    prime, a cyclotomic must certify by identity, and a product of two
    irreducibles of coprime degrees must be reported REDUCIBLE or RESIDUAL —
    never certified irreducible.
    """
    # (x^2+1)(x^2+2) = x^4 + 3x^2 + 2 — an even quartic, REDUCIBLE, and tier E
    # is a COMPLETE criterion, so the checker must say so rather than shrug.
    red = certify([2, 0, 3, 0, 1])
    assert red["tier"] == "E" and red.get("reducible") is True, red
    # x^4 + 1 = Phi_8 — also an even quartic, and IRREDUCIBLE. Same tier, other
    # verdict: without this row, "E always says reducible" would read green.
    irr4 = certify([1, 0, 0, 0, 1])
    assert irr4["tier"] == "E" and irr4.get("reducible") is False, irr4
    # x^2 - 1 — the two-sided degree-2 criterion, on the reducible side.
    disc = certify([-1, 0, 1])
    assert disc["tier"] == "A2" and disc.get("reducible") is True, disc
    # x^2 + 1 — the same criterion, irreducible.
    disc2 = certify([1, 0, 1])
    assert disc2["tier"] == "A2" and disc2.get("reducible") is False, disc2
    # x^5 - x - 1 — irreducible, certified by a PRIME (tier B).
    assert certify([-1, -1, 0, 0, 0, 1])["tier"] == "B"
    # Phi_7 = x^6 + ... + 1 — certified by the cyclotomic IDENTITY (tier D),
    # and it has to be: its Galois group is cyclic, so no prime certifies it and
    # the degree sieve survives forever.
    phi7 = certify([1, 1, 1, 1, 1, 1, 1])
    assert phi7["tier"] == "D" and phi7["cert"] == ("Phi", 7), phi7
    # (x^2+x+1)(x^3+x+1) = x^5 + x^4 + 2x^3 + 2x^2 + 2x + 1 — REDUCIBLE at a
    # degree where no tier is two-sided, so the only honest answers are
    # RESIDUAL or a sieve that has not closed. It must NEVER come back B or D.
    comp = certify([1, 2, 2, 2, 1, 1])
    assert comp["tier"] in ("RESIDUAL", "C"), comp
    assert not comp.get("reducible"), "no two-sided tier applies at degree 5"
    assert certify([1, 1])["tier"] == "A"
    # And the DDF pattern itself must be able to see a split: a control on the
    # instrument under the instrument.
    from tests._irreducibility_cert import ddf_pattern
    assert ddf_pattern([-1, 0, 1], 7) == [1, 1], "x^2-1 splits mod 7"
    assert ddf_pattern([1, 0, 1], 7) == [2], "x^2+1 is irreducible mod 7"


def test_the_even_reduction_tier_certifies_and_declines_correctly():
    """⚠️ TIER F IS THE ONE TIER THIS RC ADDED, so it gets its own controls.

    Three rows, and the two DECLINES matter more than the certification —
    a tier that certified everything would silently convert this whole gate
    into a rubber stamp.

    1. ``x^8 + 3x^6 - 6x^2 + 4`` — the factor this gate's own corpus could not
       certify any other way. It must come back F, and the certificate must
       carry BOTH halves of the theorem's refutation: the recursive verdict on
       ``m = y^4 + 3y^3 - 6y + 4`` and the odd-multiplicity prime.
    2. ``(x^4+x^3+1)(x^4-x^3+1) = x^8 - x^6 + 2x^4 + 1`` — genuinely
       ``A(x)*A(-x)``, i.e. exactly branch (ii). By the theorem EVERY prime's
       pattern has all-even multiplicities here, so tier F has no refutation
       and MUST decline. If it certified this, the theorem's second half would
       be implemented backwards.
    3. ``(x^4+1)(x^4+2) = x^8 + 3x^4 + 2`` — branch (i): ``m = (y^2+1)(y^2+2)``
       is reducible, so the recursive call cannot refute it and tier F must
       decline. This is the half that a "just take one odd prime" shortcut
       would get wrong.
    """
    f_ok = certify([4, 0, -6, 0, 0, 0, 3, 0, 1])
    assert f_ok["tier"] == "F", f_ok
    assert f_ok["cert"]["odd_multiplicity_prime"] is not None, f_ok
    assert f_ok["cert"]["m_tier"] not in ("RESIDUAL", None), f_ok

    mirror = certify([1, 0, 0, 0, 2, 0, -1, 0, 1])       # A(x)*A(-x)
    assert mirror["tier"] != "F", (
        "tier F certified an A(x)*A(-x) product as irreducible — branch (ii) "
        f"of the theorem is implemented backwards: {mirror}"
    )
    assert mirror["tier"] == "RESIDUAL", mirror

    m_red = certify([2, 0, 0, 0, 3, 0, 0, 0, 1])         # (x^4+1)(x^4+2)
    assert m_red["tier"] != "F", (
        "tier F certified a factor whose m is REDUCIBLE — branch (i) of the "
        f"theorem is not being checked: {m_red}"
    )

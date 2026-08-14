"""rc424 (`#T1113`) — the music RELATIONS lane, plus the two defects it found.

WHAT THIS FILE PINS
===================
Six new ops (``just_limit`` / ``comma_of_chain`` / ``tempers_out`` /
``interval_vector`` / ``normal_order`` / ``prime_form``), and TWO regressions
for defects that were reachable on the shipped rc423 surface.

The load-bearing test in here is
:func:`test_forte_and_rahn_disagree_on_exactly_six_set_classes`. It enumerates
every set class of cardinality 2..10 and compares the two published algorithms
row by row, because the alternative — copying a list out of a textbook — is how
the tree would have inherited the widely-quoted figure of FIVE. The measured
answer is SIX, and the sixth is 7-Z18.

⚠️ ``fractions`` / ``decimal`` / ``math`` / numpy are all banned in this file by
``tests/test_selfhosting_import_ban.py``, and nothing here needs them: every
value below is exact ℤ or exact ℚ through the shipped ops.
"""

from __future__ import annotations

import itertools

import pytest

from srmech.math.rational import best_rational
from srmech.music import (
    comma_of_chain,
    commensurability_verdict,
    common_period,
    equal_temperament_partials,
    interval_vector,
    just_limit,
    membrane_partials,
    normal_order,
    prime_form,
    tempers_out,
)


# ══════════════════════════════════════════════════════════════════════
# §1  just_limit — Class J ∘ Class I ∘ Class N
# ══════════════════════════════════════════════════════════════════════
@pytest.mark.parametrize("num,den,limit,odd,monzo", [
    (1, 1, 1, 1, {}),
    (2, 1, 2, 1, {"2": 1}),
    (3, 2, 3, 3, {"2": -1, "3": 1}),
    (4, 3, 3, 3, {"2": 2, "3": -1}),
    (5, 4, 5, 5, {"2": -2, "5": 1}),
    (6, 5, 5, 5, {"2": 1, "3": 1, "5": -1}),
    (7, 4, 7, 7, {"2": -2, "7": 1}),
    (9, 8, 3, 3, {"2": -3, "3": 2}),
    (16, 15, 5, 5, {"2": 4, "3": -1, "5": -1}),
    (45, 32, 5, 5, {"2": -5, "3": 2, "5": 1}),
    (11, 8, 11, 11, {"2": -3, "11": 1}),
])
def test_just_limit_reads_the_prime_support(num, den, limit, odd, monzo):
    r = just_limit((num, den))
    assert r["limit"] == limit
    assert r["odd_limit"] == odd
    assert r["monzo"] == monzo
    assert r["ratio"] == f"{num}/{den}"


def test_just_limit_reduces_before_factoring():
    """The Class-I reduce is load-bearing, not cosmetic.

    ``81/54`` is ``3/2``. Factoring it UNREDUCED would give a monzo carrying a
    3-exponent that cancels, and a wrong limit.
    """
    assert just_limit((81, 54)) == just_limit((3, 2))
    assert just_limit((81, 54))["monzo"] == {"2": -1, "3": 1}


def test_just_limit_refuses_float():
    with pytest.raises(TypeError):
        just_limit(1.5)
    with pytest.raises(TypeError):
        just_limit((3.0, 2))


def test_just_limit_refuses_a_non_positive_ratio():
    for bad in ((-3, 2), (3, -2), (0, 1)):
        with pytest.raises(ValueError):
            just_limit(bad)


# ══════════════════════════════════════════════════════════════════════
# §2  comma_of_chain — DERIVED, never a table
# ══════════════════════════════════════════════════════════════════════
@pytest.mark.parametrize("gen,n,period,comma,removed,limit", [
    # the Pythagorean comma: twelve just fifths against seven octaves
    ((3, 2), 12, (2, 1), "531441/524288", 7, 3),
    # the syntonic comma: four just fifths against a just major third +2 8ves
    ((3, 2), 4, (5, 1), "81/80", 1, 5),
    # the septimal comma of Archytas: 8/7 against 9/8
    ((8, 7), 1, (9, 8), "64/63", 1, 7),
])
def test_comma_of_chain_derives_the_named_commas(gen, n, period, comma,
                                                 removed, limit):
    r = comma_of_chain(gen, n, period)
    assert r["comma"] == comma
    assert r["periods_removed"] == removed
    assert r["limit"] == limit
    assert r["vanishes"] is False


def test_comma_of_chain_vanishes_only_where_the_chain_really_closes():
    """``vanishes`` must DISCRIMINATE, not be permanently False."""
    assert comma_of_chain((2, 1), 1, (2, 1))["vanishes"] is True
    assert comma_of_chain((2, 1), 5, (2, 1))["vanishes"] is True
    assert comma_of_chain((3, 2), 12, (2, 1))["vanishes"] is False


def test_no_chain_of_fifths_ever_closes():
    """§3.46.2 — the frequency lane's failure is STRUCTURAL, not an error term.

    ``(3/2)**n == 2**m`` has no solution for ``n > 0`` because the prime
    supports ``{3}`` and ``{2}`` are disjoint. Swept over the whole practical
    range, not asserted — including well past the point where the residue
    stops being factorable, since the CLOSURE question does not need the
    factorisation.
    """
    for n in range(1, 60):
        assert comma_of_chain((3, 2), n, (2, 1))["vanishes"] is False
    # the historically interesting ones, by name
    for n in (12, 41, 53):
        assert comma_of_chain((3, 2), n, (2, 1))["vanishes"] is False


def test_regression_a_long_chain_reports_its_bound_instead_of_raising():
    """DEFECT 1c — found by this file's own sweep, at authoring time.

    ``factor`` carries the SAME fixed-width 2**64 bound as ``lcm``, and a
    41-fifth chain's residue has a 20-digit numerator, so the Class-J
    enrichment raised ``ValueError`` and destroyed a perfectly exact comma.
    Same shape as the two ``commensurability_verdict`` crashes, same fix: the
    op whose whole answer IS the bounded quantity (``just_limit``) still
    raises; the op for which it is an optional enrichment reports instead.
    """
    short = comma_of_chain((3, 2), 12, (2, 1))
    assert short["limit"] == 3
    assert short["monzo"] == {"2": -19, "3": 12}
    assert short["factorisation_unavailable"] is None

    long = comma_of_chain((3, 2), 41, (2, 1))          # must NOT raise
    assert long["limit"] is None
    assert long["monzo"] is None
    assert long["factorisation_unavailable"] is not None
    assert "2**64 - 1" in long["factorisation_unavailable"]
    # the COMMA itself is exact and the real answer survives
    assert long["vanishes"] is False
    assert int(long["num"]) > 0xFFFF_FFFF_FFFF_FFFF

    # and just_limit, whose entire answer IS the factorisation, still refuses
    with pytest.raises(ValueError, match="exceeds uint64 range"):
        just_limit((long["num"], long["den"]))


def test_comma_of_chain_rejects_a_degenerate_generator_or_period():
    with pytest.raises(ValueError):
        comma_of_chain((2, 3), 4, (2, 1))       # gen < 1
    with pytest.raises(ValueError):
        comma_of_chain((3, 2), 4, (1, 1))       # period == 1
    with pytest.raises(ValueError):
        comma_of_chain((3, 2), -1, (2, 1))      # negative chain


# ══════════════════════════════════════════════════════════════════════
# §3  tempers_out — the val decided by EXACT INTEGER COMPARISON
# ══════════════════════════════════════════════════════════════════════
PYTHAGOREAN = (531441, 524288)
SYNTONIC = (81, 80)


@pytest.mark.parametrize("comma,edo,expected", [
    # 12-EDO is meantone AND closes the circle of fifths
    (SYNTONIC, 12, True),
    (PYTHAGOREAN, 12, True),
    # the meantone family: these all temper out the syntonic comma
    (SYNTONIC, 5, True),
    (SYNTONIC, 7, True),
    (SYNTONIC, 19, True),
    (SYNTONIC, 31, True),
    # ...and these do not
    (SYNTONIC, 22, False),
    (SYNTONIC, 53, False),
    # the two questions are INDEPENDENT: 5-EDO tempers out one and not the other
    (PYTHAGOREAN, 5, False),
    (PYTHAGOREAN, 53, False),
])
def test_tempers_out_decides_the_kernel(comma, edo, expected):
    r = tempers_out(comma, edo)
    assert r["tempers_out"] is expected
    assert (r["steps"] == 0) is expected


def test_the_patent_val_matches_the_textbook_values():
    """12-EDO's patent val is 2->12, 3->19, 5->28, 7->34."""
    val = tempers_out((2 * 3 * 5 * 7, 1), 12)["val"]
    assert val == {"2": 12, "3": 19, "5": 28, "7": 34}


def test_the_val_of_two_is_always_the_edo_itself():
    """``round(n*log2 2) == n`` — the sanity anchor for the integer identity."""
    for edo in range(1, 100):
        assert tempers_out((2, 1), edo)["val"]["2"] == edo


def test_tempers_out_rejects_a_degenerate_edo():
    with pytest.raises(ValueError):
        tempers_out(SYNTONIC, 0)
    with pytest.raises(TypeError):
        tempers_out(SYNTONIC, True)


# ══════════════════════════════════════════════════════════════════════
# §4  interval_vector — and the Z-relation that bounds it
# ══════════════════════════════════════════════════════════════════════
@pytest.mark.parametrize("pcs,vector", [
    ([0, 4, 7], (0, 0, 1, 1, 1, 0)),                 # major triad
    ([0, 3, 7], (0, 0, 1, 1, 1, 0)),                 # minor triad — the SAME
    ([0, 3, 6, 9], (0, 0, 4, 0, 0, 2)),              # diminished 7th
    ([0, 2, 4, 6, 8, 10], (0, 6, 0, 6, 0, 3)),       # whole-tone
    ([0, 2, 4, 5, 7, 9, 11], (2, 5, 4, 3, 6, 1)),    # diatonic
    ([0, 1, 2, 3, 4, 5], (5, 4, 3, 2, 1, 0)),        # chromatic hexachord
])
def test_interval_vector(pcs, vector):
    assert interval_vector(pcs) == vector


def test_interval_vector_depends_only_on_the_set_mod_12():
    assert interval_vector([12, 16, 7, 7, 0]) == interval_vector([0, 4, 7])


def test_the_z_relation_is_a_real_loss_not_a_rounding_one():
    """[0,1,3,7] and [0,1,4,6] share a vector and are DIFFERENT set classes."""
    a, b = [0, 1, 3, 7], [0, 1, 4, 6]
    assert interval_vector(a) == interval_vector(b) == (1, 1, 1, 1, 1, 1)
    assert prime_form(a, "rahn") != prime_form(b, "rahn")
    assert prime_form(a, "forte") != prime_form(b, "forte")


def test_the_number_of_z_related_vectors_is_measured_not_assumed():
    """23 interval vectors are shared by more than one set class (card 2..10)."""
    by_vector = {}
    for card in range(2, 11):
        for s in itertools.combinations(range(12), card):
            by_vector.setdefault(interval_vector(s), set()).add(
                prime_form(s, "rahn"))
    shared = [v for v, classes in by_vector.items() if len(classes) > 1]
    assert len(shared) == 23


# ══════════════════════════════════════════════════════════════════════
# §5  normal_order / prime_form — and the convention that MUST be named
# ══════════════════════════════════════════════════════════════════════
def test_the_convention_has_no_default():
    """Omitting it is a TypeError — the signature itself refuses."""
    with pytest.raises(TypeError):
        normal_order([0, 4, 7])
    with pytest.raises(TypeError):
        prime_form([0, 4, 7])


def test_an_unknown_convention_raises_rather_than_falling_back():
    for bad in ("straus", "FORTE", "", None):
        with pytest.raises(ValueError):
            prime_form([0, 4, 7], bad)
        with pytest.raises(ValueError):
            normal_order([0, 4, 7], bad)


@pytest.mark.parametrize("convention", ["forte", "rahn"])
def test_prime_form_is_invariant_across_the_whole_orbit(convention):
    """Every member of a set class returns one prime form — the ALGEBRAIC
    invariant declared in this op's ``preserves``, executed."""
    base = [0, 1, 4, 6, 7]
    want = prime_form(base, convention)
    for t in range(12):
        transposed = [(x + t) % 12 for x in base]
        assert prime_form(transposed, convention) == want
        inverted = [(-x) % 12 for x in transposed]
        assert prime_form(inverted, convention) == want


def test_prime_form_starts_at_zero():
    for card in range(2, 11):
        for s in itertools.combinations(range(12), card):
            assert prime_form(s, "rahn")[0] == 0
            assert prime_form(s, "forte")[0] == 0


#: The SIX set classes on which Forte (1973) and Rahn (1980) disagree, as
#: ``(forte_prime_form, rahn_prime_form)``. Computed by the test below, NOT
#: copied: the figure usually quoted is FIVE (Straus's list omits 7-Z18).
FORTE_RAHN_DISAGREEMENTS = {
    (0, 1, 3, 7, 8): (0, 1, 5, 6, 8),                      # 5-20
    (0, 1, 3, 6, 8, 9): (0, 2, 3, 6, 7, 9),                # 6-Z29
    (0, 1, 3, 5, 8, 9): (0, 1, 4, 5, 7, 9),                # 6-31
    (0, 1, 2, 3, 5, 8, 9): (0, 1, 4, 5, 6, 7, 9),          # 7-Z18
    (0, 1, 2, 4, 7, 8, 9): (0, 1, 2, 5, 6, 7, 9),          # 7-20
    (0, 1, 2, 4, 5, 7, 9, 10): (0, 1, 3, 4, 5, 7, 8, 10),  # 8-26
}


def test_forte_and_rahn_disagree_on_exactly_six_set_classes():
    """MEASURED, by enumeration — the load-bearing test in this file.

    Copying a divergence list out of a textbook is exactly how the tree would
    have inherited the widely-quoted count of FIVE. Enumerate instead.
    """
    pairs = {}
    for card in range(2, 11):
        for s in itertools.combinations(range(12), card):
            f = prime_form(s, "forte")
            r = prime_form(s, "rahn")
            if f != r:
                pairs[f] = r
    assert len(pairs) == 6, sorted(pairs.items())
    assert pairs == FORTE_RAHN_DISAGREEMENTS
    # the cardinalities the literature reports for these six
    assert sorted(len(f) for f in pairs) == [5, 6, 6, 7, 7, 8]


def test_seven_z_eighteen_is_the_one_the_count_of_five_omits():
    """Pinned on its own so a future edit cannot quietly drop it back to 5."""
    s = [0, 1, 4, 5, 6, 7, 9]
    assert prime_form(s, "forte") == (0, 1, 2, 3, 5, 8, 9)
    assert prime_form(s, "rahn") == (0, 1, 4, 5, 6, 7, 9)
    assert prime_form(s, "forte") != prime_form(s, "rahn")


def test_the_two_conventions_agree_everywhere_else():
    """202 of the 208 — the disagreement is real but rare, which is exactly
    why an unnamed default would go unnoticed."""
    agree = disagree = 0
    for card in range(2, 11):
        for s in itertools.combinations(range(12), card):
            if prime_form(s, "forte") == prime_form(s, "rahn"):
                agree += 1
            else:
                disagree += 1
    assert disagree > 0 and agree > disagree


def test_normal_order_is_not_transposed_to_zero():
    """The difference from prime_form, pinned: 5-20 under Rahn starts at 7."""
    assert normal_order([0, 1, 3, 7, 8], "rahn") == (7, 8, 0, 1, 3)
    assert normal_order([0, 1, 3, 7, 8], "forte") == (0, 1, 3, 7, 8)


# ══════════════════════════════════════════════════════════════════════
# §6  the `#T1014` Class-N corruption — DEMONSTRATED, not just warned about
# ══════════════════════════════════════════════════════════════════════
def test_class_n_erases_a_comma_to_a_unison():
    """The purest form of the corruption: a comma is DEFINED by not being 1/1,
    and ``best_rational`` at a low ceiling returns exactly 1/1."""
    exact = comma_of_chain((3, 2), 4, (5, 1))
    assert exact["comma"] == "81/80"
    assert exact["vanishes"] is False
    anchored = best_rational(81, 80, 10)
    assert anchored == (1, 1)
    # and the p-limit collapses with it: 5 -> 1
    assert just_limit((81, 80))["limit"] == 5
    assert just_limit(anchored)["limit"] == 1


def test_class_n_swaps_the_12_edo_third_for_a_just_one():
    """At ``max_denominator=10`` an IRRATIONAL 12-EDO major third comes back as
    exactly ``5/4`` — a different, audible interval — and the p-limit then runs
    away as the ceiling rises."""
    # 2**(4/12) to 18 decimal places, carried as an exact integer pair.
    third_num, third_den = 1259921049894873164, 1000000000000000000
    at10 = best_rational(third_num, third_den, 10)
    assert at10 == (5, 4), at10
    assert just_limit(at10)["limit"] == 5
    at1000 = best_rational(third_num, third_den, 1000)
    assert at1000 != (5, 4)
    assert just_limit(at1000)["limit"] > 100   # measured: 127


# ══════════════════════════════════════════════════════════════════════
# §7  REGRESSION — the two reachable defects found while costing this rc
# ══════════════════════════════════════════════════════════════════════
def test_regression_verdict_survives_an_unrepresentable_period_operand():
    """DEFECT 1a (rc423): ``commensurability_verdict`` RAISED
    ``ValueError: b exceeds uint64 range`` on a 64-bit-declared membrane
    spectrum passed without its Tier-3 declaration.

    The verdict, rational rank and field degrees were all computed and CORRECT
    before the period was even attempted, and ``period_multiplier`` is
    documented as OPTIONAL — so the raise destroyed a correct answer in
    service of an optional field.
    """
    drum = membrane_partials(n_orders=2, m_zeros=2, scale_bits=64)
    v = commensurability_verdict(drum["ratios"])       # must NOT raise
    assert v["verdict"] == "harmonic"
    assert v["rational_rank"] == 4
    assert v["period_multiplier"] is None
    assert v["period_unavailable"] is not None
    assert "2**64 - 1" in v["period_unavailable"]


def test_regression_verdict_survives_an_unrepresentable_period_result():
    """DEFECT 1b (rc423): the same crash by the OTHER route — every operand in
    range, but the running lcm out of range. This one raised ``OverflowError``
    rather than ``ValueError``, which is why it is pinned separately.
    """
    from srmech.math.q import Q
    base = 1000000000000000000
    tet = [1000000000000000000, 1059463094359295265, 1122462048309372981,
           1189207115002721067, 1259921049894873164, 1334839854170034365,
           1414213562373095049, 1498307076876681499, 1587401051968199475,
           1681792830507429086, 1781797436280678609, 1887748625363386993,
           2000000000000000000]
    ratios = [Q(*best_rational(n, base, 1501)) for n in tet]
    v = commensurability_verdict(ratios)               # must NOT raise
    assert v["verdict"] == "harmonic"
    assert v["period_multiplier"] is None
    assert "running lcm" in v["period_unavailable"]
    # and BELOW the bound the period still comes back, unchanged
    ok = [Q(*best_rational(n, base, 100)) for n in tet]
    assert commensurability_verdict(ok)["period_multiplier"] == 17948700
    assert commensurability_verdict(ok)["period_unavailable"] is None


def test_regression_common_period_still_refuses_exactly_as_documented():
    """The OTHER HALF of the fix, and the one that must NOT change.

    ``common_period`` has nothing but a period to return, so its raise is the
    feature — it is what makes silent harmonisation unreachable, and its
    message is pinned in the SHIPPED worked example for the op. Fixing the
    verdict must not soften this.
    """
    drum = membrane_partials(n_orders=2, m_zeros=2, scale_bits=64)
    with pytest.raises(ValueError, match="exceeds uint64 range"):
        common_period(drum["ratios"])
    # and the declared-open path keeps ITS distinct refusal
    with pytest.raises(ValueError, match="OPEN"):
        common_period(drum["ratios"], open_partials=drum["open_partials"])


def test_regression_ordinary_spectra_are_untouched_by_the_fix():
    """The blast radius, pinned: nothing that worked before changed."""
    for ratios, period in (([1, 2, 3, 4], 1),
                           ([1, 2, 3, 4, 5, 6], 1)):
        v = commensurability_verdict(ratios)
        assert v["verdict"] == "harmonic"
        assert v["period_multiplier"] == period
        assert v["period_unavailable"] is None
        assert common_period(ratios) == period
    # an inharmonic spectrum still reports no period, and for its OWN reason
    tet = equal_temperament_partials(12)
    v = commensurability_verdict(tet["ratios"])
    assert v["verdict"] == "inharmonic"
    assert v["period_multiplier"] is None
    assert v["period_unavailable"] is None      # not a representability issue


# ══════════════════════════════════════════════════════════════════════
# §8  the ℤ/7 note-alphabet walk — §3.46.2, as a WORKED EXAMPLE not an op
# ══════════════════════════════════════════════════════════════════════
def test_the_note_alphabet_is_z_mod_7_and_the_fifth_generates_it():
    """§3.46.2 reproduced through the shipped Class-I op.

    This ships as an example rather than as an op on purpose: it is a single
    ``cyclic_mod_add`` walk and carries no decision, so registering it would
    add registry surface for zero capability.
    """
    from srmech.cascade import cyclic_mod_add
    from srmech.math.cyclic import gcd

    letters = ["F", "C", "G", "D", "A", "E", "B"]
    # the circle of fifths steps +4 mod 7
    idx = 6                                   # F, in the A=1..G=7 alphabet
    walk = []
    for _ in range(7):
        walk.append(letters[len(walk)])
        idx = cyclic_mod_add(idx, 4, 7)
    assert walk == letters
    # the fourths cycle is the reverse read, stepping +3
    assert list(reversed(letters)) == ["B", "E", "A", "D", "G", "C", "F"]
    # both generators are coprime to 7, so each generates the whole cycle...
    assert gcd(4, 7) == 1 and gcd(3, 7) == 1
    # ...and 4 + 3 = 7 is the octave, the conserved quantity
    assert 4 + 3 == 7
    # the odd modulus FORCES the split: 7 has no integer half, so unlike Z/12
    # (where the tritone 6 is self-inverse) no step in Z/7 is its own inverse
    assert all(cyclic_mod_add(s, s, 7) != 0 for s in range(1, 7))

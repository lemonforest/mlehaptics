"""rc354 (F1336) — two introspection repairs, both about NOT over-reading a row.

PART A — the UNIT-LABEL cube. rc353's ``collision_note`` separated three senses
of a small power of two and was TRUE BUT INCOMPLETE. An accurate-but-incomplete
note is as serious as a false one the moment a planner acts on the gap: the
missing sense is that an algebra of real dim ``n`` has ``2n`` SIGNED units
needing ``log2(n)+1`` bits, so the 16-vertex tesseract is ALSO 𝕆's unit-label
cube and not only 𝕊's grading cube. Two different 16s.

PART B — the DOMAIN-WORD gap. A four-word MAGNITUDE / PHASE / ORIENTATION /
PATH vocabulary was proposed for picking a carrier. The published capability
row determines it for **3 of 25**, and this pins that the shipped surface says
so rather than asserting a word beside data that does not determine it.

Both halves assert the MEASUREMENT, never the prose. Generating code for Part A
is ``docs/srmech/notes/unit_label_cube_rc354.py``.
"""

from __future__ import annotations

from itertools import combinations

import pytest

import srmech
from srmech.amsc.carrier_schema import (
    DOMAIN_WORD_VERDICTS, _domain_word, _domain_word_gap)
from srmech.amsc.cascade.cayley_dickson import cd_basis_product


# ── PART A: the unit-label cube ───────────────────────────────────────────

RUNGS = (2, 4, 8, 16, 32, 64)


@pytest.mark.parametrize("dim", RUNGS)
def test_index_lane_xors_exactly_at_every_rung(dim: int) -> None:
    """The low log2(n) label bits ARE the XOR — zero violations, every rung."""
    bad = [(i, j) for i in range(dim) for j in range(dim)
           if cd_basis_product(dim, i, j)[0] != (i ^ j)]
    assert bad == [], f"dim {dim}: index lane is not XOR at {bad[:4]}"


@pytest.mark.parametrize("dim", RUNGS)
def test_sign_bit_violations_match_the_closed_form(dim: int) -> None:
    """``2*dim*(dim-1)`` ordered signed pairs break the flat-hypercube XOR.

    Each violating INDEX pair lifts to 4 SIGNED pairs because the cocycle sign
    does not depend on the input signs.
    """
    minus = sum(1 for i in range(dim) for j in range(dim)
                if cd_basis_product(dim, i, j)[1] < 0)   # Class-K pin-slot read
    assert 4 * minus == 2 * dim * (dim - 1)


def test_the_fraction_wrong_is_exact_and_climbs_toward_one_half():
    """``(dim-1)/(2*dim)`` — asserted as exact integer pairs, never as floats."""
    expect = {2: (1, 4), 4: (3, 8), 8: (7, 16),
              16: (15, 32), 32: (31, 64), 64: (63, 128)}
    for dim, (num, den) in expect.items():
        assert (dim - 1, 2 * dim) == (num, den)
        # strictly increasing toward 1/2, never reaching it: 2*num < den always.
        assert 2 * num < den
    fracs = [(dim - 1) * 128 // (2 * dim) for dim in RUNGS]
    assert fracs == sorted(fracs) and fracs == sorted(set(fracs))


def test_octonion_contains_h_seven_times():
    """The other half of the middle-ground argument, verified not asserted."""
    lines = [t for t in combinations(range(1, 8), 3) if t[0] ^ t[1] == t[2]]
    assert len(lines) == 7
    for a, b, c in lines:
        sub = {0, a, b, c}
        assert all(cd_basis_product(8, i, j)[0] in sub for i in sub for j in sub)


def test_collision_note_carries_the_fourth_sense_and_its_bounds():
    """The note must publish the sense AND refuse to let it be over-read."""
    gran = srmech.describe()["lanes"]["granularity"]
    note = gran["collision_note"]
    assert "signed" in note.lower() and "log2(n)+1" in note
    assert "UNIT-LABEL" in note or "unit-label" in note.lower()

    cube = gran["unit_label_cube"]
    two = cube["the_two_sixteens"]
    # the whole point: same 16, different objects.
    assert two["S_grading_cube"]["vertices"] == two["O_unit_label_cube"]["vertices"] == 16
    assert two["S_grading_cube"]["real_dim"] == 16
    assert two["O_unit_label_cube"]["real_dim"] == 8
    assert two["S_grading_cube"]["counts"] != two["O_unit_label_cube"]["counts"]

    # the shipped numbers are the measured ones.
    assert cube["shadow"]["violations_by_dim"] == {
        "2": 4, "4": 24, "8": 112, "16": 480, "32": 1984, "64": 8064}

    # THE BOUNDS ARE LOAD-BEARING. Ship the claim without them and it becomes
    # a theorem about all n, a carrier measurement, and an error rate — three
    # things it is not.
    bounds = " ".join(cube["bounds"]).lower()
    assert "not proved for all n" in bounds
    assert "design argument" in bounds and "not a measurement" in bounds
    assert "basis-pair products" in bounds and "error budget" in bounds


# ── PART B: the domain-word gap ───────────────────────────────────────────

def test_the_row_determines_the_word_for_only_three_carriers():
    """⚠️ ``of`` IS A LIVE DENOMINATOR, NOT A CONSTANT — it is ``len(_CARRIERS)``.

    v0.9.0rc362 registered ``Qalg`` and this went 25 → 26. The number was
    RAISED rather than the new carrier being excluded, and the reasoning
    matters more than the digit:

    * ``_domain_word_gap`` is derived live and its docstring says so —
      "Recomputed live, never authored, so it cannot drift from the rows it
      describes". Excluding a registered carrier would need a hand-maintained
      exclusion list, i.e. exactly the drift that design forbids.
    * The gap is a claim ABOUT THE REGISTRY: "of the N carriers srmech
      publishes, the row determines a word for only 3". ``Qalg`` is published,
      it has a capability row, so the question is meaningful for it — and it
      HAS an answer.
    * That answer is ``none_of_the_four``, a SUBSTANTIVE verdict, not a
      ``not_applicable`` skip. It joins ``Vec``, and for the same derivable
      reason: commutative (so not ORIENTATION/PATH) with zero divisors (so not
      orderable, hence not MAGNITUDE; and a commutative zero-divisor product is
      not a cycle, hence not PHASE).
    * Excluding it would WEAKEN the finding. The deliverable here is that the
      four-word vocabulary fails to cover srmech's carrier surface; a carrier it
      also fails to label makes the gap better evidenced, not worse. Suppressing
      that is the papering-over the sibling test below exists to forbid.

    So: raise this with the carrier count, and never exclude a carrier to hold
    the number still.

    v0.9.0rc363 registered ``Theta`` and ``CarrierSpectrum`` and this went
    26 → 28, by the identical rule. Those two differ from ``Qalg`` in WHERE
    they land: both have no closed binary product, so both are
    ``not_applicable`` — the skip, not a verdict. So rc363 moved the
    denominator and nothing else, and
    :func:`test_the_rc363_registrations_moved_only_the_denominator` asserts
    exactly that, including that the two content-bearing buckets below are
    untouched.
    """
    gap = _domain_word_gap()
    assert gap["verdict"].startswith("NOT DERIVABLE")
    assert gap["of"] == 28
    assert gap["determined_unambiguous"] == 3
    assert gap["unambiguous"] == ["Mat", "octonion", "quaternion"]
    assert gap["word_returned_but_qualified"] == [
        "CDRegister", "HV", "SedenionRegister", "sedenion"]
    assert len(gap["by_verdict"]["undecidable"]) == 13
    # rc362: pinned because this is the bucket Qalg MOVED, and it was the one
    # bucket with no assertion — so the registration changed a published
    # verdict set and only the denominator noticed. Vec was alone here; the
    # block comment in carrier_schema.py calls it "a genuine fifth thing", and
    # that sentence is now about two carriers.
    assert gap["by_verdict"]["none_of_the_four"] == ["Qalg", "Vec"]
    # ...and the worst-case set, for the same reason: Qalg publishes a
    # varies_with, so its word is a worst case over the minimal polynomial.
    assert gap["word_is_worst_case_only_for"] == ["CDRegister", "HV", "Qalg"]


def test_magnitude_and_phase_are_never_asserted_anywhere():
    """The refusal IS the deliverable. If either word ever appears attached to
    a carrier, the gap has been papered over and this must go red."""
    gap = _domain_word_gap()
    assert "MAGNITUDE" not in gap["by_verdict"]
    assert "PHASE" not in gap["by_verdict"]
    assert set(gap["by_verdict"]) == set(DOMAIN_WORD_VERDICTS)
    caps = srmech.describe()["carriers"]["capabilities"]
    for name, cap in caps.items():
        assert "MAGNITUDE" not in str(cap) and "PHASE" not in str(cap), name


def test_float_and_complex_are_the_decisive_measurement():
    """They differ in exactly ONE published field, and it is not a capability.

    This is the measurement the whole null rests on. If a future rc adds the
    ``order`` field, THIS is the test that goes red and tells you the gap is
    closeable — so it is a live probe, not a monument.
    """
    caps = srmech.describe()["carriers"]["capabilities"]
    f, c = caps["float"], caps["complex"]
    differing = sorted(k for k in set(f) | set(c) if f.get(k) != c.get(k))
    assert differing == ["max_dim"], differing
    assert (f["max_dim"], c["max_dim"]) == (1, 2)
    assert _domain_word(f) == _domain_word(c) == "undecidable"
    # and the two columns that could have separated them carry no entropy where
    # it is needed: `address` is constant over ALL carriers, and `turn` is
    # constant over every commutative one.
    assert len({v["address"] for v in caps.values()}) == 1
    commutative = [v for v in caps.values() if v.get("commutative") is True]
    assert len({v["turn"] for v in commutative}) == 1


def test_vec_fits_none_of_the_four_and_that_is_derivable():
    caps = srmech.describe()["carriers"]["capabilities"]
    vec = caps["Vec"]
    assert vec["commutative"] is True and vec["compose"] == "zero_divisors"
    # commutative -> not ORIENTATION/PATH; zero divisors -> an ordered ring is
    # an integral domain, so not orderable, so not MAGNITUDE; and it is no cycle.
    assert _domain_word(vec) == "none_of_the_four"


def test_the_verdict_space_is_a_lattice_not_a_chain():
    """Mat and octonion are incomparable, so no 4-word CHAIN labels this."""
    caps = srmech.describe()["carriers"]["capabilities"]
    mat, octo = caps["Mat"], caps["octonion"]
    assert (mat["compose"], mat["turn"]) == ("zero_divisors", "non_commuting")
    assert (octo["compose"], octo["turn"]) == ("full", "abelian_only")
    # Mat is worse on compose, better on turn — neither dominates.
    assert mat["compose"] != octo["compose"] and mat["turn"] != octo["turn"]


def test_the_gap_is_visible_from_describe_not_only_from_the_module():
    """A planner who never opens carrier_schema.py is the reader at risk."""
    gap = srmech.describe()["carriers"]["domain_word_gap"]
    assert gap["missing_field"]["name"] == "order"
    assert "formally real" in gap["missing_field"]["witness"]
    assert "rc339" in gap["not_shipped"]

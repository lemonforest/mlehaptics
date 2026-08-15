"""``octonion_associator_support`` — v0.9.0rc436 (local task T1141).

WHAT IS ACTUALLY NEW, AND WHAT IS NOT
=====================================
The number **168** is NOT new and this file does not treat it as a finding. It
was already pinned at five sites before the op existed:

* ``associator``'s own per-rung census — ``512 − 344 = 168`` at dim 8,
* ``cd_cycle_holonomy`` — ``168 / 512`` non-closing basis triangles,
* ``oct_mult`` — ``168 of 343`` associator-violating imaginary triples,
* ``octonion_frame_read`` — "ALL 168 of 𝕆's nonzero associators (of 512) CROSS
  the doubling seam",
* ``group_algebra_table`` — the labelled tautology, ``512 − 344 = 168``.

What shipped NOWHERE is the **SET** those five count, and a **closed form** for
membership. That is what the op adds, and it is what this file gates.

THE PREDICATE, GATED AS A SET
=============================
    nonzero associator ⟺ distinct imaginary indices, not all on one Fano line

    7·6·5 − 7·3! = 210 − 42 = 168

``test_the_fano_predicate_reproduces_the_support_as_a_set`` asserts SET
equality, not cardinality. That distinction is the whole point: two different
rules can agree on a count and disagree on membership, and a count-only check
would call that a derivation. The perturbation control below proves this test
can tell the difference.

THE THREE DENOMINATORS ARE ONE SET
==================================
𝕆 is ALTERNATIVE, so its associator is alternating: it vanishes on any repeated
argument and on ``e₀``. Hence the support over all 512 ordered basis triples,
over the 343 imaginary ones with repeats, and over the 210 distinct imaginary
ones is literally the same set — measured here, so "168 of 512" and "168 of 210"
are two readings of one object rather than two results that happen to agree.

THE COLLISION IS GATED TOO
==========================
``cd_zero_divisor_witnesses(16)`` is also 168, at a different rung, counting a
different phenomenon, and ``inertia_signature``'s docstring uses THAT sense. The
op ships a ``collision_note``; this file pins that the note keeps naming both,
because a warning that quietly loses half its subject is worse than none.
"""
from __future__ import annotations

import itertools

from srmech.cascade import (associator, cd_basis, cd_zero_divisor_witnesses,
                            octonion_associator_support)
from srmech.cascade.cayley_dickson import _octonion_fano_lines

BASIS8 = [cd_basis(8, i) for i in range(8)]


def _nonzero(i, j, k):
    return any(v != 0 for v in associator(BASIS8[i], BASIS8[j], BASIS8[k]))


def test_the_shape_and_the_arithmetic():
    s = octonion_associator_support()
    assert s["dim"] == 8
    assert s["count"] == 168
    assert s["ordered_distinct_imaginary"] == 210
    assert len(s["triples"]) == 168
    assert len(s["associating"]) == 42
    assert len(s["triples"]) + len(s["associating"]) == 210
    assert len(s["fano_lines"]) == 7
    assert 7 * 6 * 5 - 7 * 6 == 168


def test_the_support_is_the_MEASURED_support_not_a_stored_table():
    """Re-derive it independently, through ``associator`` directly."""
    measured = {t for t in itertools.permutations(range(1, 8), 3)
                if _nonzero(*t)}
    assert set(octonion_associator_support()["triples"]) == measured


def test_the_fano_predicate_reproduces_the_support_as_a_set():
    """SET equality — the load-bearing assertion of the whole op."""
    lines = {frozenset(l) for l in _octonion_fano_lines()}
    predicted = {t for t in itertools.permutations(range(1, 8), 3)
                 if frozenset(t) not in lines}
    s = octonion_associator_support()
    assert set(s["triples"]) == predicted
    assert s["line_membership_reproduces_support"] is True
    # and the complement is exactly the Fano orderings
    assert set(s["associating"]) == {
        t for t in itertools.permutations(range(1, 8), 3)
        if frozenset(t) in lines}


def test_control_a_perturbed_predicate_STOPS_reproducing_the_support():
    """PROOF THIS FILE CAN FAIL.

    Drop ONE Fano line from the rule. The predicted set then differs from the
    measured support by exactly the 6 orderings of that line — the count moves
    168 → 174, and the SET moves too. If set equality above were vacuous (an
    empty set compared to an empty set, or a cardinality check in disguise) this
    control would still pass; it does not.
    """
    lines = [frozenset(l) for l in _octonion_fano_lines()]
    crippled = set(lines[1:])                       # one line withheld
    predicted = {t for t in itertools.permutations(range(1, 8), 3)
                 if frozenset(t) not in crippled}
    measured = set(octonion_associator_support()["triples"])
    assert predicted != measured, (
        "the control did not perturb anything — the predicate test above "
        "proves nothing")
    assert len(predicted) == 174
    assert len(predicted - measured) == 6


def test_alternativity_makes_512_343_and_210_the_same_set():
    """The reason the published denominators disagree and the answer does not."""
    over512 = {t for t in itertools.product(range(8), repeat=3) if _nonzero(*t)}
    over343 = {t for t in itertools.product(range(1, 8), repeat=3)
               if _nonzero(*t)}
    over210 = set(octonion_associator_support()["triples"])
    assert over512 == over343 == over210
    assert len(over512) == 168


def test_the_content_address_is_stable_and_over_the_set():
    """Class A: same set ⇒ same digest, and the digest tracks the SET."""
    from srmech.amsc.format import sha256_bytes
    a = octonion_associator_support()
    b = octonion_associator_support()
    assert a["sha256"] == b["sha256"]
    assert len(a["sha256"]) == 64

    expect = sha256_bytes(
        ";".join("%d,%d,%d" % t for t in a["triples"]).encode("ascii"))
    assert a["sha256"] == expect

    # a DIFFERENT set must not share the address
    perturbed = tuple(sorted(set(a["triples"]) - {a["triples"][0]}))
    assert sha256_bytes(
        ";".join("%d,%d,%d" % t for t in perturbed).encode("ascii")) != a["sha256"]


def test_the_collision_note_names_BOTH_senses():
    """The warning must keep both halves, and the second half must stay true."""
    note = octonion_associator_support()["collision_note"]
    assert "cd_zero_divisor_witnesses(16)" in note
    assert "inertia_signature" in note
    assert "Aut(Fano)" in note
    # the colliding value is still 168 at the OTHER rung — measured, not quoted
    assert len(cd_zero_divisor_witnesses(16)) == 168
    # ...and the two censuses are at different rungs, which is the whole point
    assert octonion_associator_support()["dim"] == 8


def test_every_triple_is_a_genuine_distinct_imaginary_ordered_triple():
    s = octonion_associator_support()
    for t in s["triples"]:
        assert len(t) == 3
        assert len(set(t)) == 3, t
        assert all(1 <= i <= 7 for i in t), t

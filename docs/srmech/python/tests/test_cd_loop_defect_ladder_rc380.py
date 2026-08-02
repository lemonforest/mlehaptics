"""rc380 (`#T1055`) — the Cayley–Dickson loop-defect LADDER: two ops, staggered.

WHAT LANDED
===========
* ``cascade.cd_commutator(x, y, table=None)``   — the k=2 square-loop defect
  ``x·y − y·x`` (non-commutativity).
* ``cascade.cd_cycle_holonomy(x, y, z, table=None)`` — the general-dim, any-rung
  3-cycle edge-holonomy (the k=3 triangle loop over CD edge-gains), whose
  ``defect`` is the associator carried as a loop.

They are the first two rungs of the property-loss ladder, each turning ON one
rung later than the last, with the pre-existing ``associator`` as the k=3 rung's
bare-tuple form:

    commutator  turns on at ℍ (dim 4)   — associator still 0 there
    associator  turns on at 𝕆 (dim 8)   — commutator already firing

WHY EACH CHECK BELOW IS A DIFFERENTIAL AND NOT A TAUTOLOGY
==========================================================
A test that recomputes the subject with the subject proves nothing. Each block
reaches its number by a genuinely different route:

* the commutator noncommuting census is compared against the CLOSED FORM
  ``(dim−1)(dim−2)`` — derived from the anticommutation structure, not from the
  op — so a bug in either fails;
* the commutator equals the hand-rolled ``cd_mult(x,y) − cd_mult(y,x)`` it
  replaces, computed inline (a second route through the same product);
* the cycle-holonomy's two walks are checked against ``cd_mult`` bracketed by
  hand, and ``closed`` against ``left == right``;
* the cycle-holonomy ``defect`` is asserted to EQUAL ``associator`` — stated as
  the identity it is (the k=3 content is the associator wearing a holonomy hat),
  in the one place it cannot be mistaken for a measurement.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from srmech.cascade import (algebra_table, associator, cd_basis, cd_commutator,
                                 cd_cycle_holonomy, cd_mult)


# ══════════════════════════════════════════════════════════════════════
# cd_commutator — the k=2 square-loop defect
# ══════════════════════════════════════════════════════════════════════

def _noncommuting(dim: int, table=None) -> int:
    b = [cd_basis(dim, i) for i in range(dim)]
    return sum(1 for i in range(dim) for j in range(dim)
               if any(v != 0 for v in cd_commutator(b[i], b[j], table=table)))


def test_commutator_census_matches_the_closed_form():
    """The per-rung noncommuting ordered-basis-pair count IS ``(dim−1)(dim−2)``
    — MEASURED through the op against a closed form derived independently from
    the anticommutation structure (e₀ commutes with all; each unit with itself;
    every other distinct imaginary pair anticommutes)."""
    for dim in (1, 2, 4, 8, 16):
        assert _noncommuting(dim) == (dim - 1) * (dim - 2), dim


def test_commutator_turns_on_at_H_one_rung_below_the_associator():
    """⚠️ THE LADDER CLAIM. The commutator is nonzero from ℍ up; the associator
    is still identically zero at ℍ and only turns on at 𝕆. The stagger is the
    whole point — the two are not restatements of one defect."""
    # commutator: 0 through ℂ, nonzero from ℍ.
    assert _noncommuting(1) == 0 and _noncommuting(2) == 0
    assert _noncommuting(4) == 6
    # associator: 0 through ℍ, nonzero only from 𝕆.
    for dim in (1, 2, 4):
        b = [cd_basis(dim, i) for i in range(dim)]
        assert all(all(v == 0 for v in associator(b[i], b[j], b[k]))
                   for i in range(dim) for j in range(dim) for k in range(dim)), dim
    b8 = [cd_basis(8, i) for i in range(8)]
    nonassoc8 = sum(1 for i in range(8) for j in range(8) for k in range(8)
                    if any(v != 0 for v in associator(b8[i], b8[j], b8[k])))
    assert nonassoc8 == 168


def test_commutator_is_the_hand_rolled_difference():
    """It equals ``cd_mult(x, y) − cd_mult(y, x)`` — the expression measurements
    used to write inline, which is the whole reason it ships as an op."""
    for dim in (4, 8):
        for i in range(dim):
            for j in range(dim):
                x, y = cd_basis(dim, i), cd_basis(dim, j)
                left, right = cd_mult(x, y), cd_mult(y, x)
                assert (cd_commutator(x, y)
                        == tuple(a - b for a, b in zip(left, right)))


def test_commutator_ij_is_2k_in_H():
    """A concrete ℍ value: i·j − j·i = 2k (e1·e2 = e3)."""
    assert [int(q) for q in cd_commutator(cd_basis(4, 1), cd_basis(4, 2))] == \
        [0, 0, 0, 2]


def test_commutator_reaches_split_octonion_through_table():
    """table= sends it onto a split γ-twist — a DIFFERENT algebra — and it still
    counts 42 noncommuting pairs at dim 8 (anticommutation survives the twist)."""
    split = algebra_table(8, [1, -1, -1])
    assert _noncommuting(8, table=split) == 42


def test_commutator_rejects_mismatched_operands():
    with pytest.raises(ValueError, match="share dimension"):
        cd_commutator([1, 0], [1, 0, 0, 0])
    with pytest.raises(ValueError, match="power-of-two"):
        cd_commutator([1, 0, 0], [1, 0, 0])
    with pytest.raises(ValueError, match="the table is dim"):
        cd_commutator([1, 0], [1, 0], table=algebra_table(4))


# ══════════════════════════════════════════════════════════════════════
# cd_cycle_holonomy — the k=3 triangle loop over CD edges
# ══════════════════════════════════════════════════════════════════════

def _open_triangles(dim: int, table=None) -> int:
    b = [cd_basis(dim, i) for i in range(dim)]
    return sum(1 for i in range(dim) for j in range(dim) for k in range(dim)
               if not cd_cycle_holonomy(b[i], b[j], b[k], table=table)["closed"])


def test_holonomy_closes_on_associative_rungs_and_opens_at_octonion():
    """⚠️ THE TURN-ON. ``closed`` is a property of the RUNG: every basis triangle
    closes on ℝ / ℂ / ℍ, and at 𝕆 they fail to close on exactly the 168/512
    non-associating triples."""
    for dim in (1, 2, 4):
        assert _open_triangles(dim) == 0, dim
    assert _open_triangles(8) == 168


def test_holonomy_walks_are_the_two_bracketings():
    """``holonomy_left`` / ``holonomy_right`` ARE the two nestings of the loop
    product, checked against ``cd_mult`` bracketed by hand; ``closed`` is exactly
    ``left == right``."""
    for dim in (4, 8):
        b = [cd_basis(dim, i) for i in range(dim)]
        for i in range(dim):
            for j in range(dim):
                x, y, z = b[i], b[j], b[(i + j) % dim]
                h = cd_cycle_holonomy(x, y, z)
                left = cd_mult(cd_mult(x, y), z)
                right = cd_mult(x, cd_mult(y, z))
                assert h["holonomy_left"] == left
                assert h["holonomy_right"] == right
                assert h["closed"] == (left == right)
                assert h["dim"] == dim


def test_holonomy_defect_IS_the_associator():
    """The k=3 content the loop carries is the associator — stated as the
    identity it is, over all 512 dim-8 basis triangles, in the one place it
    cannot be mistaken for a measurement."""
    b = [cd_basis(8, i) for i in range(8)]
    for i in range(8):
        for j in range(8):
            for k in range(8):
                assert (cd_cycle_holonomy(b[i], b[j], b[k])["defect"]
                        == associator(b[i], b[j], b[k]))


def test_holonomy_reaches_split_octonion_through_table():
    """table= runs the loop on a split γ-twist: still a division-free non-
    associative rung, and its open count differs from the definite 𝕆 (the twist
    reaches a genuinely second algebra, exactly as the associator sees it)."""
    split = algebra_table(8, [1, -1, -1])
    b = [cd_basis(8, i) for i in range(8)]
    differ = sum(1 for i in range(8) for j in range(8) for k in range(8)
                 if cd_cycle_holonomy(b[i], b[j], b[k])["defect"]
                 != cd_cycle_holonomy(b[i], b[j], b[k], table=split)["defect"])
    assert differ == 96


def test_holonomy_rejects_mismatched_operands():
    with pytest.raises(ValueError, match="share dimension"):
        cd_cycle_holonomy([1, 0], [1, 0], [1, 0, 0, 0])
    with pytest.raises(ValueError, match="power-of-two"):
        cd_cycle_holonomy([1, 0, 0], [1, 0, 0], [1, 0, 0])
    with pytest.raises(ValueError, match="the table is dim"):
        cd_cycle_holonomy([1, 0], [1, 0], [1, 0], table=algebra_table(4))


# ══════════════════════════════════════════════════════════════════════
# both ops are exported AND classified (the __all__ / Rosetta trap)
# ══════════════════════════════════════════════════════════════════════

def test_new_ops_are_exported_and_classified():
    """A new public name is invisible to the ledger walk unless it is exported
    AND carries a Rosetta bucket. Both ops compose the c_dispatched products, so
    both are ``composition_of_c`` — never a new C symbol."""
    import srmech.cascade as cascade
    assert "cd_commutator" in cascade.__all__
    assert "cd_cycle_holonomy" in cascade.__all__
    ledger = (Path(__file__).resolve().parent
              / "rosetta_classification.ndjson").read_text(encoding="utf-8")
    for name in ("srmech.cascade.cayley_dickson.cd_commutator",
                 "srmech.cascade.cayley_dickson.cd_cycle_holonomy"):
        assert f'"{name}"' in ledger, f"{name} has no Rosetta bucket"
        # and it is the composition_of_c bucket (no new C symbol owed).
        row = next(l for l in ledger.splitlines() if f'"{name}"' in l)
        assert '"bucket": "composition_of_c"' in row, row
